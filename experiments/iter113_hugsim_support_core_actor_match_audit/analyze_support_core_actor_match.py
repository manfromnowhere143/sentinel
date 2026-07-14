#!/usr/bin/env python3
"""Iteration 113 HUGSIM support-core actor-match support audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER112_VERDICT = "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE"
SUPPORT_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_ACTOR_MATCH_SUPPORT_NULL"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_ACTOR_MATCH_INFRA_NULL"
MIN_CLASSIFIABLE = 4
ITER108_CLASSIFIABLE_BASELINE = 2
EXPECTED_SLOT_COUNT = 8
EXPECTED_DUPLICATE_GROUPS = 3


def load_iter59_module() -> Any:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "iter59_hugsim_actor_match_audit"
        / "analyze_actor_match.py"
    )
    spec = importlib.util.spec_from_file_location("iter59_actor_match", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-iter59-analyzer:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = load_iter59_module()


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


def crosscheck_iter112(iter112_report: dict[str, Any], slots: list[dict[str, Any]], problems: list[str]) -> None:
    require_equal(problems, "iter112-verdict", iter112_report.get("verdict"), ITER112_VERDICT)
    summary = iter112_report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter112-summary-missing")
        summary = {}
    require_equal(problems, "iter112-completed-slot-count", summary.get("completed_slot_count"), EXPECTED_SLOT_COUNT)
    require_equal(
        problems,
        "iter112-artifact-count",
        summary.get("slot_proof_artifact_complete_count"),
        EXPECTED_SLOT_COUNT,
    )
    require_equal(
        problems,
        "iter112-provenance-key-count",
        summary.get("collision_provenance_key_count"),
        EXPECTED_SLOT_COUNT,
    )
    require_equal(problems, "iter112-slot-order", summary.get("collected_slot_ids_match_manifest"), True)
    require_equal(
        problems,
        "iter112-duplicate-groups",
        summary.get("duplicate_scenario_group_count"),
        EXPECTED_DUPLICATE_GROUPS,
    )
    iter112_slots = iter112_report.get("slots")
    if not isinstance(iter112_slots, list):
        problems.append("iter112-slots-not-list")
        return
    manifest_ids = [slot.get("slot_id") for slot in slots]
    iter112_ids = [slot.get("slot_id") for slot in iter112_slots if isinstance(slot, dict)]
    require_equal(problems, "iter112-manifest-slot-ids", iter112_ids, manifest_ids)


def slot_dir(proof_root: Path, slot: dict[str, Any]) -> Path:
    return proof_root / f"{slot['slot_id']}__{slot['scenario']}__on"


def classify_slots(slots: list[dict[str, Any]], proof_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot in slots:
        row = ITER59.classify_episode(slot_dir(proof_root, slot), str(slot["slot_id"]), str(slot["scenario"]))
        row.update(
            {
                "slot_index": slot.get("slot_index"),
                "slot_id": slot.get("slot_id"),
                "run": slot.get("run"),
                "dataset": slot.get("dataset"),
                "tier": slot.get("tier"),
                "design_label": slot.get("design_label"),
                "first_fire_channel": slot.get("first_fire_channel"),
                "fire_timing_label": slot.get("fire_timing_label"),
                "first_fire_lead_time": slot.get("first_fire_lead_time"),
                "exact_positive_sources": slot.get("exact_positive_sources", []),
                "scenario_positive_sources": slot.get("scenario_positive_sources", []),
            }
        )
        rows.append(row)
    return rows


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    classifiable = sum(row.get("support_label") == "classifiable_foreground" for row in rows)
    if classifiable < MIN_CLASSIFIABLE:
        return SUPPORT_NULL_VERDICT
    return COMPLETE_VERDICT


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def build_report(manifest_path: Path, iter112_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    manifest, manifest_problems = load_json(manifest_path, "iter111-manifest")
    iter112_report, iter112_problems = load_json(iter112_report_path, "iter112-report")
    infra_problems.extend(manifest_problems + iter112_problems)
    slots: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        slots = load_manifest_slots(manifest, infra_problems)
        crosscheck_iter112(iter112_report, slots, infra_problems)
        rows = classify_slots(slots, proof_root)
    support_counts = Counter(row.get("support_label") for row in rows)
    bridge_counts = Counter(
        row.get("bridge_label")
        for row in rows
        if row.get("support_label") == "classifiable_foreground"
    )
    design_counts = Counter(row.get("design_label") for row in rows)
    design_classifiable_counts = Counter(
        row.get("design_label")
        for row in rows
        if row.get("support_label") == "classifiable_foreground"
    )
    classifiable = support_counts.get("classifiable_foreground", 0)
    verdict = choose_verdict(rows, infra_problems)
    summary = {
        "slot_count": len(rows),
        "completed_rows": sum(not row.get("problems") for row in rows),
        "classifiable_foreground": classifiable,
        "support_counts": _dict_counts(support_counts),
        "bridge_counts": _dict_counts(bridge_counts),
        "design_counts": _dict_counts(design_counts),
        "design_classifiable_counts": _dict_counts(design_classifiable_counts),
        "actor_match": bridge_counts.get("actor_match", 0),
        "actor_mismatch": bridge_counts.get("actor_mismatch", 0),
        "actor_ambiguous": bridge_counts.get("actor_ambiguous", 0),
        "min_classifiable_bar": MIN_CLASSIFIABLE,
        "iter108_classifiable_baseline": ITER108_CLASSIFIABLE_BASELINE,
        "classifiable_delta_vs_iter108": classifiable - ITER108_CLASSIFIABLE_BASELINE,
    }
    return {
        "iteration": 113,
        "inputs": {
            "manifest": str(manifest_path),
            "iter112_report": str(iter112_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": str(
                Path("experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py")
            ),
        },
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "bounded 8-slot support-core actor-match support audit only; no repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 113 - HUGSIM support-core actor-match support audit",
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
            "| slot | scenario | run | design | timing | support | bridge | distance m | monitor object | foreground |",
            "|---:|---|---:|---|---|---|---|---:|---|---|",
        ]
    )
    for row in report["episodes"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('design_label')}` | `{row.get('fire_timing_label')}` | "
            f"`{row.get('support_label')}` | `{row.get('bridge_label')}` | "
            f"`{row.get('bridge_distance_m')}` | `{row.get('monitor_object_id')}` | "
            f"`{row.get('first_foreground_obs_name')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    manifest: Path,
    iter112_report: Path,
    proof_root: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(manifest, iter112_report, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "experiments/iter111_hugsim_support_core_launch_manifest/proof-launch-manifest/"
            "support_core_launch_manifest.json"
        ),
    )
    parser.add_argument(
        "--iter112-report",
        type=Path,
        default=Path(
            "experiments/iter112_hugsim_support_core_batch_execution/proof-execution/"
            "support_core_batch_execution_report.json"
        ),
    )
    parser.add_argument(
        "--proof-root",
        type=Path,
        default=Path("experiments/iter112_hugsim_support_core_batch_execution/proof-execution"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/"
            "support_core_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/"
            "support_core_actor_match.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.manifest,
        args.iter112_report,
        args.proof_root,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
