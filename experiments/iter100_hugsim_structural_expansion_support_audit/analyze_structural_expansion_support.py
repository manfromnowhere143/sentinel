#!/usr/bin/env python3
"""Iteration 100 HUGSIM structural expansion support audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ITER54_VERDICT = "PROVENANCE_SUPPORT_NULL"
ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER99_VERDICT = "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE"


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    cursor: Any = data
    for key in path:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def source_checks(
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter99_report: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    if iter54_report.get("verdict") != ITER54_VERDICT:
        problems.append(f"iter54-verdict-not-{ITER54_VERDICT}")
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter99_report.get("verdict") != ITER99_VERDICT:
        problems.append(f"iter99-verdict-not-{ITER99_VERDICT}")
    if iter54_report.get("infrastructure_problems"):
        problems.append(f"iter54-infrastructure-problems:{iter54_report.get('infrastructure_problems')}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter99_report.get("infra_problems"):
        problems.append(f"iter99-infra-problems:{iter99_report.get('infra_problems')}")

    combined54 = nested_get(iter54_report, ("summaries", "combined"))
    summary59 = iter59_report.get("summary")
    summary99 = iter99_report.get("summary")
    if not isinstance(combined54, dict):
        problems.append("iter54-combined-summary-missing")
        combined54 = {}
    if not isinstance(summary59, dict):
        problems.append("iter59-summary-missing")
        summary59 = {}
    if not isinstance(summary99, dict):
        problems.append("iter99-summary-missing")
        summary99 = {}

    require_equal(problems, "iter54-pairs", combined54.get("pairs"), 104)
    require_equal(problems, "iter54-on_collision_pairs", combined54.get("on_collision_pairs"), 92)
    require_equal(
        problems,
        "iter54-collision_actor_supported",
        nested_get(combined54, ("collision_actor_support_counts", "collision_actor_supported")),
        0,
    )
    require_equal(
        problems,
        "iter54-collision_actor_not_logged",
        nested_get(combined54, ("collision_actor_support_counts", "collision_actor_not_logged")),
        104,
    )
    require_equal(
        problems,
        "iter54-on_collision_collision_actor_supported",
        nested_get(combined54, ("collision_actor_support_on_collision_counts", "collision_actor_supported")),
        0,
    )
    require_equal(
        problems,
        "iter54-on_collision_collision_actor_not_logged",
        nested_get(combined54, ("collision_actor_support_on_collision_counts", "collision_actor_not_logged")),
        92,
    )
    require_equal(
        problems,
        "iter54-monitor_unique_ttc_object",
        nested_get(combined54, ("monitor_provenance_counts", "unique_ttc_object")),
        40,
    )
    require_equal(
        problems,
        "iter54-monitor_unique_cpa_object",
        nested_get(combined54, ("monitor_provenance_counts", "unique_cpa_object")),
        36,
    )
    require_equal(
        problems,
        "iter54-monitor_both_distinct_objects",
        nested_get(combined54, ("monitor_provenance_counts", "both_distinct_objects")),
        1,
    )
    require_equal(
        problems,
        "iter54-monitor_no_fire",
        nested_get(combined54, ("monitor_provenance_counts", "no_fire")),
        27,
    )
    require_equal(
        problems,
        "iter54-monitor_argmin_reconstruction_failed",
        nested_get(combined54, ("monitor_provenance_counts", "argmin_reconstruction_failed")),
        0,
    )
    require_equal(
        problems,
        "iter54-monitor_schema_unsupported",
        nested_get(combined54, ("monitor_provenance_counts", "schema_unsupported")),
        0,
    )
    require_equal(problems, "iter54-collision_actor_identity_fields", combined54.get("collision_actor_identity_fields"), [])

    require_equal(problems, "iter59-completed_rows", summary59.get("completed_rows"), 8)
    require_equal(
        problems,
        "iter59-classifiable_foreground",
        nested_get(summary59, ("support_counts", "classifiable_foreground")),
        3,
    )
    require_equal(problems, "iter59-no_monitor_fire", nested_get(summary59, ("support_counts", "no_monitor_fire")), 2)
    require_equal(problems, "iter59-post_collision_fire", nested_get(summary59, ("support_counts", "post_collision_fire")), 2)
    require_equal(
        problems,
        "iter59-background_collision_only",
        nested_get(summary59, ("support_counts", "background_collision_only")),
        1,
    )

    require_equal(problems, "iter99-target_rows", summary99.get("target_rows"), 5)
    require_equal(problems, "iter99-covered_rows", summary99.get("covered_rows"), 5)
    require_equal(problems, "iter99-compatible_rows", summary99.get("compatible_rows"), 5)
    require_equal(problems, "iter99-uncovered_rows", summary99.get("uncovered_rows"), 0)
    require_equal(
        problems,
        "iter99-duplicate_or_incompatible_rows",
        summary99.get("duplicate_or_incompatible_rows"),
        0,
    )
    return problems


def build_measurements(
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter99_report: dict[str, Any],
) -> dict[str, Any]:
    combined54 = nested_get(iter54_report, ("summaries", "combined"))
    if not isinstance(combined54, dict):
        combined54 = {}
    summary59 = iter59_report.get("summary")
    if not isinstance(summary59, dict):
        summary59 = {}
    support59 = summary59.get("support_counts") if isinstance(summary59.get("support_counts"), dict) else {}
    summary99 = iter99_report.get("summary")
    if not isinstance(summary99, dict):
        summary99 = {}
    monitor_counts = combined54.get("monitor_provenance_counts") if isinstance(combined54.get("monitor_provenance_counts"), dict) else {}
    collision_counts = (
        combined54.get("collision_actor_support_counts")
        if isinstance(combined54.get("collision_actor_support_counts"), dict)
        else {}
    )
    on_collision_collision_counts = (
        combined54.get("collision_actor_support_on_collision_counts")
        if isinstance(combined54.get("collision_actor_support_on_collision_counts"), dict)
        else {}
    )
    monitor_side_supported = sum(
        int(monitor_counts.get(key, 0))
        for key in ("unique_ttc_object", "unique_cpa_object", "both_distinct_objects", "unique_both_same_object")
    )
    structural_rows59 = sum(
        int(support59.get(key, 0))
        for key in ("no_monitor_fire", "post_collision_fire", "background_collision_only")
    )
    collision_actor_supported = int(collision_counts.get("collision_actor_supported", 0))
    broad_pairs = int(combined54.get("pairs", 0))
    current_structural_covered = int(summary99.get("covered_rows", 0))
    larger_committed_pool_exists = broad_pairs > int(summary59.get("completed_rows", 0))
    can_expand_from_committed_reports = collision_actor_supported > current_structural_covered
    return {
        "broad_committed_transfer_pairs": broad_pairs,
        "broad_on_collision_pairs": combined54.get("on_collision_pairs"),
        "monitor_side_supported_pairs": monitor_side_supported,
        "monitor_provenance_counts": monitor_counts,
        "collision_actor_supported_pairs": collision_actor_supported,
        "collision_actor_not_logged_pairs": collision_counts.get("collision_actor_not_logged"),
        "on_collision_collision_actor_supported_pairs": on_collision_collision_counts.get("collision_actor_supported"),
        "on_collision_collision_actor_not_logged_pairs": on_collision_collision_counts.get("collision_actor_not_logged"),
        "collision_actor_identity_fields": combined54.get("collision_actor_identity_fields"),
        "actor_match_audit_rows": summary59.get("completed_rows"),
        "actor_match_classifiable_foreground_rows": support59.get("classifiable_foreground"),
        "actor_match_structural_rows": structural_rows59,
        "structural_bridge_covered_rows": current_structural_covered,
        "structural_bridge_compatible_rows": summary99.get("compatible_rows"),
        "larger_committed_pool_exists": larger_committed_pool_exists,
        "can_expand_from_committed_reports": can_expand_from_committed_reports,
        "new_instrumentation_required_for_larger_structural_bridge": larger_committed_pool_exists
        and not can_expand_from_committed_reports,
    }


def classify(measurements: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "expansion_support_insufficient"
    if (
        measurements["larger_committed_pool_exists"] is True
        and measurements["monitor_side_supported_pairs"] > 0
        and measurements["collision_actor_supported_pairs"] == 0
        and measurements["structural_bridge_covered_rows"] == 5
    ):
        return "expansion_boundary_no_collision_actor_support"
    if measurements["collision_actor_supported_pairs"] > measurements["structural_bridge_covered_rows"]:
        return "expansion_candidate_committed_actor_support_present"
    return "expansion_support_mixed"


def choose_verdict(label: str, infra_problems: list[str]) -> str:
    if infra_problems or label == "expansion_support_insufficient":
        return "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BLOCKED"
    if label == "expansion_boundary_no_collision_actor_support":
        return "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL"
    if label == "expansion_candidate_committed_actor_support_present":
        return "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_CANDIDATE_PRESENT"
    return "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_MIXED_COMPLETE"


def build_report(iter54_report_path: Path, iter59_report_path: Path, iter99_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter54_report, problems54 = load_report(iter54_report_path, "iter54-report")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter99_report, problems99 = load_report(iter99_report_path, "iter99-report")
    infra_problems.extend(problems54 + problems59 + problems99)
    measurements: dict[str, Any] = {}
    label = "expansion_support_insufficient"
    if not infra_problems:
        infra_problems.extend(source_checks(iter54_report, iter59_report, iter99_report))
        measurements = build_measurements(iter54_report, iter59_report, iter99_report)
        label = classify(measurements, infra_problems)
    return {
        "iteration": 100,
        "inputs": {
            "iter54_report": str(iter54_report_path),
            "iter59_report": str(iter59_report_path),
            "iter99_report": str(iter99_report_path),
        },
        "infra_problems": infra_problems,
        "event": {
            "row_label": label,
            "measurements": measurements,
            "problems": [] if not infra_problems else infra_problems,
        },
        "summary": {
            "broad_committed_transfer_pairs": measurements.get("broad_committed_transfer_pairs", 0),
            "broad_on_collision_pairs": measurements.get("broad_on_collision_pairs", 0),
            "monitor_side_supported_pairs": measurements.get("monitor_side_supported_pairs", 0),
            "collision_actor_supported_pairs": measurements.get("collision_actor_supported_pairs", 0),
            "collision_actor_not_logged_pairs": measurements.get("collision_actor_not_logged_pairs", 0),
            "actor_match_audit_rows": measurements.get("actor_match_audit_rows", 0),
            "actor_match_structural_rows": measurements.get("actor_match_structural_rows", 0),
            "structural_bridge_covered_rows": measurements.get("structural_bridge_covered_rows", 0),
            "larger_committed_pool_exists": measurements.get("larger_committed_pool_exists", False),
            "can_expand_from_committed_reports": measurements.get("can_expand_from_committed_reports", False),
            "new_instrumentation_required_for_larger_structural_bridge": measurements.get(
                "new_instrumentation_required_for_larger_structural_bridge",
                False,
            ),
        },
        "verdict": choose_verdict(label, infra_problems),
        "claim_boundary": (
            "report-level expansion-support boundary only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, "
            "HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, "
            "retuning, or approval-to-run claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 100 - HUGSIM structural expansion support audit",
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
    event = report["event"]
    lines.extend(
        [
            "",
            "## Event",
            "",
            f"- `row_label`: `{event['row_label']}`",
            f"- `measurements`: `{event['measurements']}`",
            "",
            "## Boundary",
            "",
            report["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter54_report: Path, iter59_report: Path, iter99_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter54_report, iter59_report, iter99_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter54-report",
        type=Path,
        default=Path("experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json"),
    )
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter99-report",
        type=Path,
        default=Path(
            "experiments/iter99_hugsim_structural_bridge_coverage_audit/proof-coverage/"
            "structural_bridge_coverage_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter100_hugsim_structural_expansion_support_audit/proof-expansion/"
            "structural_expansion_support_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter100_hugsim_structural_expansion_support_audit/proof-expansion/"
            "structural_expansion_support.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter54_report, args.iter59_report, args.iter99_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
