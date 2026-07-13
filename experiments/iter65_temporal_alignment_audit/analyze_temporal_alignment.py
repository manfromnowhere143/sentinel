#!/usr/bin/env python3
"""Iteration 65 matched pre-contact temporal alignment audit analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
ITER64_VERDICT = "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
EXPECTED_ROWS = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("cpa_medium_b", "scene-0166-medium-00"),
)
ACTIVE_LABEL = "matched_object_active_hazard"
SUBTHRESHOLD_LABEL = "matched_object_subthreshold"
MISSING_LABEL = "matched_object_missing"
TIME_TOL = 1e-9


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = _load_module(
    "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
    "iter59_actor_match",
)
ITER62 = _load_module(
    "experiments/iter62_nontrigger_ranking_audit/analyze_nontrigger_ranking.py",
    "iter62_nontrigger_ranking",
)


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"parse-{label}-failed:{exc}"]
    if not isinstance(report, dict):
        return {}, [f"{label}-not-dict"]
    return report, []


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def crosscheck_reports(
    iter59_report: dict[str, Any],
    iter61_report: dict[str, Any],
    iter64_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    if iter64_report.get("verdict") != ITER64_VERDICT:
        problems.append(f"iter64-verdict-not-{ITER64_VERDICT}")

    episodes61 = iter61_report.get("episodes")
    if not isinstance(episodes61, list):
        problems.append("iter61-episodes-not-list")
    else:
        rows61 = [
            row for row in episodes61
            if isinstance(row, dict) and row.get("row_label") == "no_monitor_object_support"
        ]
        identities61 = [row_identity(row) for row in rows61]
        if identities61 != list(EXPECTED_ROWS):
            problems.append(f"iter61-no-support-identity-mismatch:{identities61}")

    episodes64 = iter64_report.get("episodes")
    if not isinstance(episodes64, list):
        problems.append("iter64-episodes-not-list")
        return [], problems
    rows64 = [row for row in episodes64 if isinstance(row, dict)]
    identities64 = [row_identity(row) for row in rows64]
    if identities64 != list(EXPECTED_ROWS):
        problems.append(f"iter64-identity-mismatch:{identities64}")
    for row in rows64:
        if row.get("row_label") != "pre_contact_object_match":
            problems.append(f"iter64-row-not-match:{row_identity(row)}:{row.get('row_label')}")
        variant = row.get("best_variant")
        if not isinstance(variant, dict):
            problems.append(f"iter64-best-variant-missing:{row_identity(row)}")
            continue
        for field in ("decision_ts", "object_id", "foreground_timestamp"):
            if field not in variant:
                problems.append(f"iter64-best-variant-missing-{field}:{row_identity(row)}")
    return rows64, problems


def episode_decisions_path(proof_root: Path, audit_id: str, scenario: str) -> Path:
    return proof_root / "episodes" / f"{audit_id}__{scenario}__on" / "sentinel_iter48_decisions.jsonl"


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    return rows


def find_decision_row(rows: list[dict[str, Any]], decision_ts: float) -> dict[str, Any] | None:
    for row in rows:
        try:
            ts = require_float(row.get("ts", row.get("frame_index")), "decision.ts")
        except ValueError:
            continue
        if abs(ts - decision_ts) <= TIME_TOL:
            return row
    return None


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def classify_matched_object(
    decision_row: dict[str, Any],
    matched_object_id: Any,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    objects = ITER62.object_metrics(decision_row)
    matched = [row for row in objects if same_object_id(row.get("object_id"), matched_object_id)]
    if len(matched) != 1:
        return None, objects, MISSING_LABEL
    matched_object = matched[0]
    if matched_object.get("cpa_cross") or matched_object.get("ttc_cross"):
        return matched_object, objects, ACTIVE_LABEL
    return matched_object, objects, SUBTHRESHOLD_LABEL


def summarize_first_fire(path: Path, matched_object_id: Any) -> tuple[dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    try:
        decisions = ITER59.read_decisions(path)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return None, [f"first-fire-read-failed:{exc}"]
    summary = {
        "first_fire_ts": decisions.get("first_fire_ts"),
        "first_fire_channel": decisions.get("first_fire_channel"),
        "monitor_provenance_label": decisions.get("monitor_provenance_label"),
        "first_fire_object_id": decisions.get("monitor_object_id"),
        "matched_object_is_first_fire_object": same_object_id(
            decisions.get("monitor_object_id"),
            matched_object_id,
        ),
        "monitor_frames": decisions.get("monitor_frames"),
        "fired_frames": decisions.get("fired_frames"),
        "brake_frames": decisions.get("brake_frames"),
    }
    if summary["first_fire_ts"] is None or summary["first_fire_channel"] in {None, "no_fire"}:
        problems.append("first-fire-summary-missing")
    return summary, problems


def analyze_row(proof_root: Path, iter64_row: dict[str, Any]) -> dict[str, Any]:
    audit_id, scenario = row_identity(iter64_row)
    result: dict[str, Any] = {"audit_id": audit_id, "scenario": scenario, "problems": []}
    variant = iter64_row.get("best_variant")
    if not isinstance(variant, dict):
        result["problems"].append("best-variant-missing")
        result["row_label"] = MISSING_LABEL
        return result
    decision_ts = require_float(variant.get("decision_ts"), "best_variant.decision_ts")
    matched_object_id = variant.get("object_id")
    foreground_ts = require_float(variant.get("foreground_timestamp"), "best_variant.foreground_timestamp")
    decisions_path = episode_decisions_path(proof_root, audit_id, scenario)
    result.update({
        "matched_decision_ts": decision_ts,
        "matched_object_id": matched_object_id,
        "matched_foreground_ts": foreground_ts,
        "matched_bridge_variant": {
            key: variant.get(key)
            for key in (
                "distance_m",
                "temporal_source",
                "axis_order",
                "forward_sign",
                "lateral_sign",
                "lead_time_s",
            )
        },
    })
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        result["problems"].append("missing-decisions")
        result["row_label"] = MISSING_LABEL
        return result

    first_fire_summary, first_fire_problems = summarize_first_fire(decisions_path, matched_object_id)
    result["first_fire"] = first_fire_summary
    result["problems"].extend(first_fire_problems)
    try:
        decision_rows = read_decision_rows(decisions_path)
        decision_row = find_decision_row(decision_rows, decision_ts)
        if decision_row is None:
            result["row_label"] = MISSING_LABEL
            result["matched_object"] = None
            result["object_count_at_matched_ts"] = 0
            return result
        matched_object, objects, label = classify_matched_object(decision_row, matched_object_id)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        result["row_label"] = MISSING_LABEL
        return result

    for obj in objects:
        obj["is_matched_object"] = same_object_id(obj.get("object_id"), matched_object_id)
        obj["is_first_fire_object"] = bool(
            first_fire_summary
            and same_object_id(obj.get("object_id"), first_fire_summary.get("first_fire_object_id"))
        )
    result.update({
        "row_label": label,
        "object_count_at_matched_ts": len(objects),
        "matched_object": matched_object,
        "objects_at_matched_ts": sorted(objects, key=lambda row: str(row.get("object_id"))),
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 2 or any(row.get("problems") for row in rows):
        return "TEMPORAL_ALIGNMENT_AUDIT_BLOCKED"
    labels = [row.get("row_label") for row in rows]
    if labels == [ACTIVE_LABEL, ACTIVE_LABEL]:
        return "TEMPORAL_ALIGNMENT_ACTIVE_HAZARD_COMPLETE"
    if labels == [SUBTHRESHOLD_LABEL, SUBTHRESHOLD_LABEL]:
        return "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE"
    if all(label in {ACTIVE_LABEL, SUBTHRESHOLD_LABEL, MISSING_LABEL} for label in labels):
        return "TEMPORAL_ALIGNMENT_MIXED_COMPLETE"
    return "TEMPORAL_ALIGNMENT_AUDIT_BLOCKED"


def build_report(
    proof_root: Path,
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter64_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    iter64_report, problems64 = load_report(iter64_report_path, "iter64-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    infra_problems.extend(problems64)
    iter64_rows: list[dict[str, Any]] = []
    if not problems59 and not problems61 and not problems64:
        iter64_rows, crosscheck_problems = crosscheck_reports(iter59_report, iter61_report, iter64_report)
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in iter64_rows]
    label_counts = Counter(row.get("row_label") for row in rows if row.get("row_label"))
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 65,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
            "iter64_report": str(iter64_report_path),
        },
        "expected_rows": [
            {"audit_id": audit_id, "scenario": scenario}
            for audit_id, scenario in EXPECTED_ROWS
        ],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(iter64_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "matched_object_ids": [
                row.get("matched_object_id")
                for row in rows
                if not row.get("problems")
            ],
            "matched_objects_equal_first_fire_objects": sum(
                bool(row.get("first_fire", {}).get("matched_object_is_first_fire_object"))
                for row in rows
                if not row.get("problems")
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-row temporal/provenance alignment audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 65 - matched pre-contact temporal alignment audit",
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
    lines.extend(["", "## Rows", ""])
    for row in report["episodes"]:
        matched = row.get("matched_object")
        if not isinstance(matched, dict):
            matched = {}
        first_fire = row.get("first_fire")
        if not isinstance(first_fire, dict):
            first_fire = {}
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}`: label `{row.get('row_label')}`, "
            f"matched object `{row.get('matched_object_id')}`, decision `{row.get('matched_decision_ts')}`, "
            f"min_cpa `{matched.get('min_cpa')}`, ttc `{matched.get('ttc')}`, "
            f"cpa_cross `{matched.get('cpa_cross')}`, ttc_cross `{matched.get('ttc_cross')}`, "
            f"first_fire `{first_fire.get('first_fire_channel')}` object "
            f"`{first_fire.get('first_fire_object_id')}`, problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    proof_root: Path,
    iter59_report: Path,
    iter61_report: Path,
    iter64_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter61_report, iter64_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-proof-root",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match"),
    )
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter61-report",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"),
    )
    parser.add_argument(
        "--iter64-report",
        type=Path,
        default=Path(
            "experiments/iter64_unsupported_temporal_surface_audit/proof-unsupported-temporal/"
            "unsupported_temporal_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter65_temporal_alignment_audit/proof-alignment/temporal_alignment_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter65_temporal_alignment_audit/proof-alignment/temporal_alignment.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_proof_root,
        args.iter59_report,
        args.iter61_report,
        args.iter64_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
