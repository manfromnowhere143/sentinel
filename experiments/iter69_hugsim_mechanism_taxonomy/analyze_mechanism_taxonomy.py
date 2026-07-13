#!/usr/bin/env python3
"""Iteration 69 HUGSIM mechanism taxonomy synthesis.

This analyzer runs offline over committed iteration-59/61/63/64/65/66/67/68
reports. It does not read the GPU box, create episodes, change thresholds, or
retune Sentinel.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
ITER63_VERDICT = "TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE"
ITER64_VERDICT = "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
ITER65_VERDICT = "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE"
ITER66_VERDICT = "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE"
ITER67_VERDICT = "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE"
ITER68_VERDICT = "FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE"

EXPECTED_ITER59_ROWS = (
    {
        "audit_id": "ttc_extreme_short",
        "scenario": "scene-0038-extreme-00",
        "support_label": "classifiable_foreground",
    },
    {
        "audit_id": "mixed_extreme",
        "scenario": "scene-0062-extreme-00",
        "support_label": "no_monitor_fire",
    },
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "support_label": "post_collision_fire",
    },
    {
        "audit_id": "nofire_hard_control",
        "scenario": "scene-0041-hard-00",
        "support_label": "no_monitor_fire",
    },
    {
        "audit_id": "cpa_medium_a",
        "scenario": "scene-0071-medium-00",
        "support_label": "background_collision_only",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "support_label": "post_collision_fire",
    },
    {
        "audit_id": "cpa_medium_b",
        "scenario": "scene-0166-medium-00",
        "support_label": "classifiable_foreground",
    },
    {
        "audit_id": "ttc_extreme_b",
        "scenario": "scene-0383-extreme-00",
        "support_label": "classifiable_foreground",
    },
)

ITER61_EXPECTED_KEYS = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("cpa_medium_b", "scene-0166-medium-00"),
    ("ttc_extreme_b", "scene-0383-extreme-00"),
)
TWO_ROW_KEYS = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("cpa_medium_b", "scene-0166-medium-00"),
)
STRUCTURAL_LABELS = {
    "no_monitor_fire",
    "post_collision_fire",
    "background_collision_only",
}
CLASSIFIABLE_LABEL = "classifiable_foreground"


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


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


def report_problem_list(report: dict[str, Any], key: str) -> list[Any]:
    value = report.get(key)
    return value if isinstance(value, list) else []


def index_episodes(report: dict[str, Any], label: str, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    episodes = report.get("episodes")
    if not isinstance(episodes, list):
        problems.append(f"{label}-episodes-not-list")
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in episodes:
        if not isinstance(row, dict):
            problems.append(f"{label}-episode-not-dict")
            continue
        key = row_key(row)
        if key in index:
            problems.append(f"{label}-duplicate-row:{key}")
            continue
        index[key] = row
    return index


def iter59_actual_schedule(episodes: list[Any]) -> list[dict[str, str]]:
    out = []
    for row in episodes:
        if isinstance(row, dict):
            out.append({
                "audit_id": str(row.get("audit_id")),
                "scenario": str(row.get("scenario")),
                "support_label": str(row.get("support_label")),
            })
    return out


def check_expected_keys(
    index: dict[tuple[str, str], dict[str, Any]],
    expected: tuple[tuple[str, str], ...],
    label: str,
    problems: list[str],
) -> None:
    actual = list(index)
    if actual != list(expected):
        problems.append(f"{label}-identity-mismatch:{actual}")


def check_report_problem_lists(reports: dict[str, dict[str, Any]], problems: list[str]) -> None:
    for label, report in reports.items():
        infra = report_problem_list(report, "infra_problems")
        if infra:
            problems.append(f"{label}-infra-problems:{infra}")
        row_problems = report_problem_list(report, "row_problems")
        if row_problems:
            problems.append(f"{label}-row-problems:{row_problems}")


def crosscheck_reports(reports: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": ITER59_VERDICT,
        "iter61": ITER61_VERDICT,
        "iter63": ITER63_VERDICT,
        "iter64": ITER64_VERDICT,
        "iter65": ITER65_VERDICT,
        "iter66": ITER66_VERDICT,
        "iter67": ITER67_VERDICT,
        "iter68": ITER68_VERDICT,
    }
    for label, expected in expected_verdicts.items():
        if reports[label].get("verdict") != expected:
            problems.append(f"{label}-verdict-not-{expected}")
    check_report_problem_lists(reports, problems)

    iter59_episodes = reports["iter59"].get("episodes")
    if not isinstance(iter59_episodes, list):
        problems.append("iter59-episodes-not-list")
        iter59_rows: list[dict[str, Any]] = []
    else:
        actual = iter59_actual_schedule(iter59_episodes)
        if actual != list(EXPECTED_ITER59_ROWS):
            problems.append(f"iter59-schedule-mismatch:{actual}")
        iter59_rows = [row for row in iter59_episodes if isinstance(row, dict)]

    iter61_index = index_episodes(reports["iter61"], "iter61", problems)
    check_expected_keys(iter61_index, ITER61_EXPECTED_KEYS, "iter61", problems)

    iter63_target = reports["iter63"].get("target")
    if not isinstance(iter63_target, dict):
        problems.append("iter63-target-not-dict")
    elif row_key(iter63_target) != ("ttc_extreme_b", "scene-0383-extreme-00"):
        problems.append(f"iter63-target-mismatch:{row_key(iter63_target)}")

    indexes: dict[str, dict[tuple[str, str], dict[str, Any]]] = {"iter61": iter61_index}
    for label in ("iter64", "iter65", "iter66", "iter67", "iter68"):
        index = index_episodes(reports[label], label, problems)
        check_expected_keys(index, TWO_ROW_KEYS, label, problems)
        indexes[label] = index

    return {
        "iter59_rows": iter59_rows,
        "indexes": indexes,
        "iter63_target": iter63_target if isinstance(iter63_target, dict) else {},
        "iter63_summary": reports["iter63"].get("summary")
        if isinstance(reports["iter63"].get("summary"), dict)
        else {},
    }, problems


def label_from(index: dict[tuple[str, str], dict[str, Any]], key: tuple[str, str]) -> str | None:
    row = index.get(key)
    value = row.get("row_label") if isinstance(row, dict) else None
    return str(value) if value is not None else None


def source_labels_for_classifiable(
    key: tuple[str, str],
    sources: dict[str, Any],
) -> dict[str, str | None]:
    indexes: dict[str, dict[tuple[str, str], dict[str, Any]]] = sources["indexes"]
    labels: dict[str, str | None] = {
        "iter61": label_from(indexes["iter61"], key),
    }
    if key == ("ttc_extreme_b", "scene-0383-extreme-00"):
        summary = sources["iter63_summary"]
        labels["iter63"] = str(summary.get("row_label")) if summary.get("row_label") else None
        return labels
    for label in ("iter64", "iter65", "iter66", "iter67", "iter68"):
        labels[label] = label_from(indexes[label], key)
    return labels


def evidence_row(
    audit_id: str,
    source_labels: dict[str, str | None],
) -> tuple[str, list[str], list[str]]:
    required: dict[str, str]
    if audit_id == "ttc_extreme_b":
        required = {
            "iter61": "nontrigger_object_match",
            "iter63": "visible_never_hazard",
        }
        label = "nontrigger_visible_never_hazard"
    elif audit_id == "ttc_extreme_short":
        required = {
            "iter61": "no_monitor_object_support",
            "iter64": "pre_contact_object_match",
            "iter65": "matched_object_subthreshold",
            "iter66": "target_object_ever_active_hazard",
            "iter67": "same_object_target_trigger_match",
            "iter68": "fire_gap_best_before_fire",
        }
        label = "same_object_late_fire_after_best_bridge"
    elif audit_id == "cpa_medium_b":
        required = {
            "iter61": "no_monitor_object_support",
            "iter64": "pre_contact_object_match",
            "iter65": "matched_object_subthreshold",
            "iter66": "target_object_visible_never_active",
            "iter67": "split_target_match_trigger_match",
            "iter68": "fire_gap_best_after_fire",
        }
        label = "split_object_visible_never_active_fire_before_best_bridge"
    else:
        return "classifiable_actor_mismatch_unrefined", [], ["unknown-classifiable-row"]

    met = []
    missing = []
    for source, expected in required.items():
        actual = source_labels.get(source)
        if actual == expected:
            met.append(f"{source}:{expected}")
        else:
            missing.append(f"{source}:{expected}!={actual}")
    if missing:
        return "classifiable_actor_mismatch_unrefined", met, missing
    return label, met, []


def object_details_for_classifiable(
    key: tuple[str, str],
    sources: dict[str, Any],
) -> dict[str, Any]:
    indexes: dict[str, dict[tuple[str, str], dict[str, Any]]] = sources["indexes"]
    details: dict[str, Any] = {}
    iter61_row = indexes["iter61"].get(key)
    if isinstance(iter61_row, dict):
        details["iter61_trigger_object_id"] = iter61_row.get("trigger_object_id")
        best_nontrigger = iter61_row.get("best_nontrigger_variant")
        if isinstance(best_nontrigger, dict):
            details["iter61_best_nontrigger_object_id"] = best_nontrigger.get("object_id")
            details["iter61_best_nontrigger_distance_m"] = best_nontrigger.get("distance_m")
    for label in ("iter66", "iter67", "iter68"):
        row = indexes.get(label, {}).get(key)
        if not isinstance(row, dict):
            continue
        for field in ("target_object_id", "trigger_object_id", "first_fire_ts"):
            if field in row:
                details[f"{label}_{field}"] = row.get(field)
    if key == ("ttc_extreme_b", "scene-0383-extreme-00"):
        target = sources["iter63_target"]
        details["iter63_object_id"] = target.get("object_id")
        details["iter63_trigger_object_id"] = target.get("trigger_object_id")
    return details


def classify_row(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    audit_id = str(row.get("audit_id"))
    scenario = str(row.get("scenario"))
    support_label = str(row.get("support_label"))
    out: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "iter59_support_label": support_label,
        "first_fire_channel": row.get("first_fire_channel"),
        "first_fire_ts": row.get("first_fire_ts"),
        "monitor_object_id": row.get("monitor_object_id"),
        "source_labels": {"iter59": support_label},
        "object_details": {},
        "refined_by_downstream": False,
        "refinement_evidence": [f"iter59:{support_label}"],
        "unmet_refinement_evidence": [],
    }
    if support_label in STRUCTURAL_LABELS:
        out["mechanism_label"] = support_label
        return out
    if support_label != CLASSIFIABLE_LABEL:
        out["mechanism_label"] = "classifiable_actor_mismatch_unrefined"
        out["unmet_refinement_evidence"] = [f"unexpected-iter59-support:{support_label}"]
        return out

    key = (audit_id, scenario)
    source_labels = source_labels_for_classifiable(key, sources)
    mechanism_label, met, missing = evidence_row(audit_id, source_labels)
    out["source_labels"].update(source_labels)
    out["object_details"] = object_details_for_classifiable(key, sources)
    out["mechanism_label"] = mechanism_label
    out["refined_by_downstream"] = not missing
    out["refinement_evidence"] = met
    out["unmet_refinement_evidence"] = missing
    return out


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != len(EXPECTED_ITER59_ROWS):
        return "HUGSIM_MECHANISM_TAXONOMY_BLOCKED"
    classifiable_rows = [
        row for row in rows
        if row.get("iter59_support_label") == CLASSIFIABLE_LABEL
    ]
    refined = [row for row in classifiable_rows if row.get("refined_by_downstream")]
    if len(classifiable_rows) == 3 and len(refined) == 3:
        return "HUGSIM_MECHANISM_TAXONOMY_COMPLETE"
    return "HUGSIM_MECHANISM_TAXONOMY_PARTIAL"


def build_report(
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter63_report_path: Path,
    iter64_report_path: Path,
    iter65_report_path: Path,
    iter66_report_path: Path,
    iter67_report_path: Path,
    iter68_report_path: Path,
) -> dict[str, Any]:
    path_map = {
        "iter59": iter59_report_path,
        "iter61": iter61_report_path,
        "iter63": iter63_report_path,
        "iter64": iter64_report_path,
        "iter65": iter65_report_path,
        "iter66": iter66_report_path,
        "iter67": iter67_report_path,
        "iter68": iter68_report_path,
    }
    reports: dict[str, dict[str, Any]] = {}
    infra_problems: list[str] = []
    for label, path in path_map.items():
        report, problems = load_report(path, f"{label}-report")
        reports[label] = report
        infra_problems.extend(problems)

    sources: dict[str, Any] = {"iter59_rows": [], "indexes": {}, "iter63_summary": {}}
    if not infra_problems:
        sources, crosscheck_problems = crosscheck_reports(reports)
        infra_problems.extend(crosscheck_problems)

    rows = []
    if not infra_problems:
        rows = [classify_row(row, sources) for row in sources["iter59_rows"]]

    mechanism_counts = Counter(row.get("mechanism_label") for row in rows)
    classifiable_rows = [
        row for row in rows
        if row.get("iter59_support_label") == CLASSIFIABLE_LABEL
    ]
    refined_rows = [row for row in classifiable_rows if row.get("refined_by_downstream")]
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 69,
        "inputs": {label: str(path) for label, path in path_map.items()},
        "expected_rows": list(EXPECTED_ITER59_ROWS),
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "total_rows": len(rows),
            "structural_rows": sum(
                row.get("iter59_support_label") in STRUCTURAL_LABELS for row in rows
            ),
            "classifiable_rows": len(classifiable_rows),
            "refined_classifiable_rows": len(refined_rows),
            "unrefined_classifiable_rows": len(classifiable_rows) - len(refined_rows),
            "mechanism_counts": dict(sorted(mechanism_counts.items())),
        },
        "verdict": verdict,
        "claim_boundary": (
            "eight-row evidence synthesis over committed HUGSIM audit reports only; no "
            "actor-causality, repair, transfer, safety, deployment, robustness, benchmark, "
            "population, HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 69 - HUGSIM mechanism taxonomy synthesis",
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
    lines.extend([
        "",
        "## Taxonomy",
        "",
        "| audit id | scenario | iteration-59 support | mechanism | refined | evidence |",
        "|---|---|---|---|---:|---|",
    ])
    for row in report["episodes"]:
        evidence = ", ".join(row.get("refinement_evidence", []))
        if row.get("unmet_refinement_evidence"):
            evidence = evidence + " / unmet: " + ", ".join(row["unmet_refinement_evidence"])
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | "
            f"`{row['iter59_support_label']}` | `{row['mechanism_label']}` | "
            f"`{row['refined_by_downstream']}` | {evidence} |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter61_report: Path,
    iter63_report: Path,
    iter64_report: Path,
    iter65_report: Path,
    iter66_report: Path,
    iter67_report: Path,
    iter68_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(
        iter59_report,
        iter61_report,
        iter63_report,
        iter64_report,
        iter65_report,
        iter66_report,
        iter67_report,
        iter68_report,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter61-report",
        type=Path,
        default=Path(
            "experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"
        ),
    )
    parser.add_argument(
        "--iter63-report",
        type=Path,
        default=Path(
            "experiments/iter63_temporal_emergence_audit/proof-temporal/temporal_emergence_report.json"
        ),
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
        "--iter65-report",
        type=Path,
        default=Path("experiments/iter65_temporal_alignment_audit/proof-alignment/temporal_alignment_report.json"),
    )
    parser.add_argument(
        "--iter66-report",
        type=Path,
        default=Path("experiments/iter66_matched_object_timeline_audit/proof-timeline/timeline_report.json"),
    )
    parser.add_argument(
        "--iter67-report",
        type=Path,
        default=Path("experiments/iter67_trigger_target_bridge_audit/proof-trigger-target/trigger_target_report.json"),
    )
    parser.add_argument(
        "--iter68-report",
        type=Path,
        default=Path("experiments/iter68_fire_time_bridge_decomposition/proof-fire-time/fire_time_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter69_hugsim_mechanism_taxonomy/proof-taxonomy/taxonomy_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter69_hugsim_mechanism_taxonomy/proof-taxonomy/taxonomy.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter61_report,
        args.iter63_report,
        args.iter64_report,
        args.iter65_report,
        args.iter66_report,
        args.iter67_report,
        args.iter68_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
