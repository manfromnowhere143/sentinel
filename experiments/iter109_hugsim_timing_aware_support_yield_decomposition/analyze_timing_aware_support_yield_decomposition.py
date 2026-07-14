#!/usr/bin/env python3
"""Iteration 109 HUGSIM timing-aware support-yield decomposition."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER105_VERDICT = "HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE"
ITER107_VERDICT = "HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE"
ITER108_ALLOWED_VERDICTS = {
    "HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL",
    "HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_AUDIT_COMPLETE",
}
COMPLETE_VERDICT = "HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_INFRA_NULL"
EXPECTED_SLOT_COUNT = 13


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def finite_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return None


def load_design_rows(design_report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    require_equal(problems, "iter105-verdict", design_report.get("verdict"), ITER105_VERDICT)
    measurements = design_report.get("event", {}).get("measurements")
    if not isinstance(measurements, dict):
        problems.append("iter105-measurements-missing")
        return []
    rows = measurements.get("selected_rows")
    if not isinstance(rows, list):
        problems.append("iter105-selected-rows-not-list")
        return []
    require_equal(problems, "iter105-selected-count", len(rows), EXPECTED_SLOT_COUNT)
    require_equal(
        problems,
        "iter105-selected-indexes",
        [row.get("slot_index") for row in rows if isinstance(row, dict)],
        list(range(1, EXPECTED_SLOT_COUNT + 1)),
    )
    return [row for row in rows if isinstance(row, dict)]


def load_manifest_slots(manifest: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    slots = manifest.get("slots")
    policy = manifest.get("duplicate_slot_policy")
    if not isinstance(slots, list):
        problems.append("manifest-slots-not-list")
        return []
    if not isinstance(policy, dict):
        problems.append("manifest-duplicate-policy-missing")
    else:
        require_equal(problems, "manifest-primary-key", policy.get("primary_execution_key"), "slot_id")
        require_equal(problems, "manifest-scenario-dedup", policy.get("scenario_deduplication_allowed"), False)
    require_equal(problems, "manifest-slot-count", len(slots), EXPECTED_SLOT_COUNT)
    require_equal(
        problems,
        "manifest-slot-indexes",
        [slot.get("slot_index") for slot in slots if isinstance(slot, dict)],
        list(range(1, EXPECTED_SLOT_COUNT + 1)),
    )
    return [slot for slot in slots if isinstance(slot, dict)]


def load_iter107_slots(iter107_report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    require_equal(problems, "iter107-verdict", iter107_report.get("verdict"), ITER107_VERDICT)
    summary = iter107_report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter107-summary-missing")
        summary = {}
    require_equal(problems, "iter107-completed-slot-count", summary.get("completed_slot_count"), EXPECTED_SLOT_COUNT)
    require_equal(problems, "iter107-provenance-key-count", summary.get("collision_provenance_key_count"), 13)
    rows = iter107_report.get("slots")
    if not isinstance(rows, list):
        problems.append("iter107-slots-not-list")
        return []
    require_equal(problems, "iter107-slot-count", len(rows), EXPECTED_SLOT_COUNT)
    return [row for row in rows if isinstance(row, dict)]


def load_iter108_rows(iter108_report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    verdict = iter108_report.get("verdict")
    if verdict not in ITER108_ALLOWED_VERDICTS:
        problems.append(f"iter108-verdict-mismatch:{verdict!r}!={sorted(ITER108_ALLOWED_VERDICTS)!r}")
    rows = iter108_report.get("episodes")
    if not isinstance(rows, list):
        problems.append("iter108-episodes-not-list")
        return []
    require_equal(problems, "iter108-episode-count", len(rows), EXPECTED_SLOT_COUNT)
    summary = iter108_report.get("summary")
    if isinstance(summary, dict):
        require_equal(problems, "iter108-completed-rows", summary.get("completed_rows"), EXPECTED_SLOT_COUNT)
    else:
        problems.append("iter108-summary-missing")
    return [row for row in rows if isinstance(row, dict)]


def crosscheck_slot_lineage(
    design_rows: list[dict[str, Any]],
    manifest_slots: list[dict[str, Any]],
    iter107_slots: list[dict[str, Any]],
    iter108_rows: list[dict[str, Any]],
    problems: list[str],
) -> None:
    manifest_ids = [slot.get("slot_id") for slot in manifest_slots]
    iter107_ids = [slot.get("slot_id") for slot in iter107_slots]
    iter108_ids = [row.get("slot_id") for row in iter108_rows]
    require_equal(problems, "iter107-slot-ids", iter107_ids, manifest_ids)
    require_equal(problems, "iter108-slot-ids", iter108_ids, manifest_ids)

    design_ids = [row.get("slot_id") for row in design_rows]
    manifest_source_ids = [slot.get("source_slot_id") for slot in manifest_slots]
    require_equal(problems, "iter105-to-iter106-source-slot-ids", manifest_source_ids, design_ids)
    for idx, (design, slot) in enumerate(zip(design_rows, manifest_slots, strict=False), start=1):
        for key in ("scenario", "run", "dataset", "tier", "first_fire_channel", "fire_timing_label"):
            require_equal(problems, f"lineage-{idx}-{key}", slot.get(key), design.get(key))


def residual_label(row: dict[str, Any]) -> str:
    if row.get("problems"):
        return "observed_infra_or_schema_gap"
    support = row.get("support_label")
    if support == "classifiable_foreground":
        return "classifiable_success"
    if support == "background_collision_only":
        return "observed_background_only"
    if support == "no_collision_provenance":
        return "observed_empty_collision_provenance"
    if support == "post_collision_fire":
        return "observed_post_collision_fire"
    if support == "no_monitor_fire":
        return "observed_no_monitor_fire"
    return "observed_infra_or_schema_gap"


def delta(a: Any, b: Any) -> float | None:
    left = finite_number(a)
    right = finite_number(b)
    if left is None or right is None:
        return None
    return left - right


def build_rows(
    design_rows: list[dict[str, Any]],
    manifest_slots: list[dict[str, Any]],
    iter107_slots: list[dict[str, Any]],
    iter108_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for design, slot, execution, observed in zip(design_rows, manifest_slots, iter107_slots, iter108_rows, strict=True):
        obs_fire = finite_number(observed.get("first_fire_ts"))
        obs_foreground = finite_number(observed.get("first_foreground_ts"))
        row = {
            "slot_index": slot.get("slot_index"),
            "slot_id": slot.get("slot_id"),
            "source_slot_id": slot.get("source_slot_id"),
            "scenario": slot.get("scenario"),
            "run": slot.get("run"),
            "dataset": slot.get("dataset"),
            "tier": slot.get("tier"),
            "first_fire_channel": slot.get("first_fire_channel"),
            "fire_timing_label": slot.get("fire_timing_label"),
            "selection_reason": slot.get("selection_reason"),
            "manifest_first_fire_ts": slot.get("first_fire_ts"),
            "manifest_first_on_nc_time": slot.get("first_on_nc_time"),
            "manifest_first_fire_lead_time": slot.get("first_fire_lead_time"),
            "design_first_fire_lead_time": design.get("first_fire_lead_time"),
            "observed_first_fire_ts": observed.get("first_fire_ts"),
            "observed_first_foreground_ts": observed.get("first_foreground_ts"),
            "observed_fire_lead_s": None if obs_fire is None or obs_foreground is None else obs_foreground - obs_fire,
            "observed_first_fire_minus_manifest_first_fire_s": delta(
                observed.get("first_fire_ts"), slot.get("first_fire_ts")
            ),
            "observed_first_foreground_minus_manifest_first_on_nc_s": delta(
                observed.get("first_foreground_ts"), slot.get("first_on_nc_time")
            ),
            "observed_support_label": observed.get("support_label"),
            "observed_bridge_label": observed.get("bridge_label"),
            "observed_bridge_distance_m": observed.get("bridge_distance_m"),
            "observed_foreground_count": observed.get("foreground_count"),
            "observed_provenance_count": observed.get("provenance_count"),
            "observed_monitor_object_id": observed.get("monitor_object_id"),
            "execution_hdscore": execution.get("hdscore"),
            "execution_steps": execution.get("steps"),
            "residual_label": residual_label(observed),
        }
        rows.append(row)
    return rows


def nested_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        counts[str(row.get(outer_key))][str(row.get(inner_key))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(counts.items())}


def build_summary(rows: list[dict[str, Any]], infra_problems: list[str]) -> dict[str, Any]:
    residual_counts = Counter(row.get("residual_label") for row in rows)
    support_counts = Counter(row.get("observed_support_label") for row in rows)
    observed_leads = [
        row["observed_fire_lead_s"]
        for row in rows
        if isinstance(row.get("observed_fire_lead_s"), (int, float))
    ]
    return {
        "slot_count": len(rows),
        "residual_counts": dict(sorted(residual_counts.items())),
        "support_counts": dict(sorted(support_counts.items())),
        "classifiable_success": residual_counts.get("classifiable_success", 0),
        "unclassifiable_count": len(rows) - residual_counts.get("classifiable_success", 0),
        "foreground_absent_or_empty_count": residual_counts.get("observed_background_only", 0)
        + residual_counts.get("observed_empty_collision_provenance", 0),
        "observed_post_collision_fire_count": residual_counts.get("observed_post_collision_fire", 0),
        "timing_inversion_count": sum(
            1
            for row in rows
            if row.get("residual_label") == "observed_post_collision_fire"
            and finite_number(row.get("manifest_first_fire_lead_time")) is not None
            and finite_number(row.get("observed_fire_lead_s")) is not None
            and float(row["manifest_first_fire_lead_time"]) > 0
            and float(row["observed_fire_lead_s"]) < 0
        ),
        "observed_fire_lead_min_s": min(observed_leads) if observed_leads else None,
        "observed_fire_lead_max_s": max(observed_leads) if observed_leads else None,
        "residual_by_timing": nested_counts(rows, "fire_timing_label", "residual_label"),
        "residual_by_channel": nested_counts(rows, "first_fire_channel", "residual_label"),
        "residual_by_dataset": nested_counts(rows, "dataset", "residual_label"),
        "infra_problem_count": len(infra_problems),
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems:
        return INFRA_NULL_VERDICT
    if len(rows) != EXPECTED_SLOT_COUNT:
        return INFRA_NULL_VERDICT
    residual_counts = Counter(row.get("residual_label") for row in rows)
    if sum(residual_counts.values()) != EXPECTED_SLOT_COUNT or None in residual_counts:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    design_report_path: Path,
    manifest_path: Path,
    iter107_report_path: Path,
    iter108_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    design_report, design_problems = load_json(design_report_path, "iter105-design-report")
    manifest, manifest_problems = load_json(manifest_path, "iter106-manifest")
    iter107_report, iter107_problems = load_json(iter107_report_path, "iter107-report")
    iter108_report, iter108_problems = load_json(iter108_report_path, "iter108-report")
    infra_problems.extend(design_problems + manifest_problems + iter107_problems + iter108_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        design_rows = load_design_rows(design_report, infra_problems)
        manifest_slots = load_manifest_slots(manifest, infra_problems)
        iter107_slots = load_iter107_slots(iter107_report, infra_problems)
        iter108_rows = load_iter108_rows(iter108_report, infra_problems)
        if not infra_problems:
            crosscheck_slot_lineage(design_rows, manifest_slots, iter107_slots, iter108_rows, infra_problems)
        if not infra_problems:
            rows = build_rows(design_rows, manifest_slots, iter107_slots, iter108_rows)
    summary = build_summary(rows, infra_problems)
    return {
        "iteration": 109,
        "inputs": {
            "iter105_design_report": str(design_report_path),
            "iter106_manifest": str(manifest_path),
            "iter107_report": str(iter107_report_path),
            "iter108_report": str(iter108_report_path),
        },
        "infra_problems": infra_problems,
        "summary": summary,
        "slots": rows,
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "offline timing-aware support-yield decomposition only; no actor-causality, "
            "actor-match support upgrade, repair, threshold-value, transfer, safety, deployment, "
            "robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, "
            "first-responder behavior, acquisition-value, retuning, production, commercial, "
            "schedule-selection, or GPU-approval claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 109 - HUGSIM timing-aware support-yield decomposition",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if report["infra_problems"]:
        lines.extend(["", "## Infrastructure Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["infra_problems"])
    lines.extend(
        [
            "",
            "## Slots",
            "",
            "| slot | scenario | run | design lead s | observed lead s | support | residual | fire delta s | foreground delta s |",
            "|---:|---|---:|---:|---:|---|---|---:|---:|",
        ]
    )
    for row in report["slots"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('manifest_first_fire_lead_time')}` | `{row.get('observed_fire_lead_s')}` | "
            f"`{row.get('observed_support_label')}` | `{row.get('residual_label')}` | "
            f"`{row.get('observed_first_fire_minus_manifest_first_fire_s')}` | "
            f"`{row.get('observed_first_foreground_minus_manifest_first_on_nc_s')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    design_report: Path,
    manifest: Path,
    iter107_report: Path,
    iter108_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(design_report, manifest, iter107_report, iter108_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--design-report",
        type=Path,
        default=Path(
            "experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/"
            "timing_aware_provenance_batch_design_report.json"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "experiments/iter106_hugsim_timing_aware_launch_manifest/proof-launch-manifest/"
            "timing_aware_launch_manifest.json"
        ),
    )
    parser.add_argument(
        "--iter107-report",
        type=Path,
        default=Path(
            "experiments/iter107_hugsim_timing_aware_batch_execution/proof-execution/"
            "timing_aware_batch_execution_report.json"
        ),
    )
    parser.add_argument(
        "--iter108-report",
        type=Path,
        default=Path(
            "experiments/iter108_hugsim_timing_aware_batch_actor_match_audit/proof-actor-match/"
            "timing_aware_batch_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter109_hugsim_timing_aware_support_yield_decomposition/proof-decomposition/"
            "timing_aware_support_yield_decomposition_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter109_hugsim_timing_aware_support_yield_decomposition/proof-decomposition/"
            "timing_aware_support_yield_decomposition.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.design_report,
        args.manifest,
        args.iter107_report,
        args.iter108_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
