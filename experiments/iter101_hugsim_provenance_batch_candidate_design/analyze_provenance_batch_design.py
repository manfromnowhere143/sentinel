#!/usr/bin/env python3
"""Iteration 101 HUGSIM provenance batch candidate design."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER54_VERDICT = "PROVENANCE_SUPPORT_NULL"
ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER100_VERDICT = "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL"

NON_SINGLETON_STRATA = (
    ("iter48_easy_medium", "no_fire"),
    ("iter48_easy_medium", "unique_cpa_object"),
    ("iter48_easy_medium", "unique_ttc_object"),
    ("iter49_hard_extreme", "no_fire"),
    ("iter49_hard_extreme", "unique_cpa_object"),
    ("iter49_hard_extreme", "unique_ttc_object"),
)
SINGLETON_STRATUM = ("iter49_hard_extreme", "both_distinct_objects")
ALL_STRATA = (*NON_SINGLETON_STRATA, SINGLETON_STRATUM)


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
    iter100_report: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    if iter54_report.get("verdict") != ITER54_VERDICT:
        problems.append(f"iter54-verdict-not-{ITER54_VERDICT}")
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter100_report.get("verdict") != ITER100_VERDICT:
        problems.append(f"iter100-verdict-not-{ITER100_VERDICT}")
    if iter54_report.get("infrastructure_problems"):
        problems.append(f"iter54-infrastructure-problems:{iter54_report.get('infrastructure_problems')}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter100_report.get("infra_problems"):
        problems.append(f"iter100-infra-problems:{iter100_report.get('infra_problems')}")

    combined54 = nested_get(iter54_report, ("summaries", "combined"))
    if not isinstance(combined54, dict):
        problems.append("iter54-combined-summary-missing")
        combined54 = {}
    require_equal(problems, "iter54-pairs", combined54.get("pairs"), 104)
    require_equal(problems, "iter54-on_collision_pairs", combined54.get("on_collision_pairs"), 92)
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
        "iter54-collision_actor_supported",
        nested_get(combined54, ("collision_actor_support_counts", "collision_actor_supported")),
        0,
    )

    episodes59 = iter59_report.get("episodes")
    if not isinstance(episodes59, list):
        problems.append("iter59-episodes-not-list")
    else:
        require_equal(problems, "iter59-completed-row-count", len(episodes59), 8)
        for row in episodes59:
            if not isinstance(row, dict) or not isinstance(row.get("scenario"), str):
                problems.append(f"iter59-scenario-missing:{row}")

    summary100 = iter100_report.get("summary")
    if not isinstance(summary100, dict):
        problems.append("iter100-summary-missing")
        summary100 = {}
    require_equal(problems, "iter100-larger_committed_pool_exists", summary100.get("larger_committed_pool_exists"), True)
    require_equal(problems, "iter100-can_expand_from_committed_reports", summary100.get("can_expand_from_committed_reports"), False)
    require_equal(
        problems,
        "iter100-new_instrumentation_required_for_larger_structural_bridge",
        summary100.get("new_instrumentation_required_for_larger_structural_bridge"),
        True,
    )
    return problems


def existing_scenarios(iter59_report: dict[str, Any]) -> set[str]:
    episodes = iter59_report.get("episodes")
    if not isinstance(episodes, list):
        return set()
    return {row["scenario"] for row in episodes if isinstance(row, dict) and isinstance(row.get("scenario"), str)}


def row_sort_key(row: dict[str, Any]) -> tuple[str, int]:
    scenario = row.get("scenario")
    run = row.get("run")
    return (str(scenario), int(run) if isinstance(run, int) else 999)


def compact_row(row: dict[str, Any], selection_role: str) -> dict[str, Any]:
    fields = (
        "dataset",
        "scenario",
        "run",
        "tier",
        "attackplanner",
        "monitor_provenance_label",
        "first_fire_channel",
        "fire_timing_label",
        "first_on_nc_time",
        "first_fire_ts",
        "first_fire_lead_time",
        "monitor_frames",
        "fired_frames",
        "brake_frames",
    )
    compact = {field: row.get(field) for field in fields}
    compact["selection_role"] = selection_role
    compact["stratum"] = [row.get("dataset"), row.get("monitor_provenance_label")]
    return compact


def select_schedule(iter54_report: dict[str, Any], existing: set[str], problems: list[str]) -> dict[str, Any]:
    pairs = iter54_report.get("pairs")
    if not isinstance(pairs, list):
        problems.append("iter54-pairs-not-list")
        return {
            "strata": {},
            "selected_rows": [],
            "selected_new_rows": [],
            "carried_singleton_rows": [],
        }
    strata_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        if not isinstance(row, dict):
            problems.append(f"iter54-pair-not-dict:{row}")
            continue
        if row.get("on_collision") is not True:
            continue
        key = (str(row.get("dataset")), str(row.get("monitor_provenance_label")))
        if key in ALL_STRATA:
            strata_rows[key].append(row)
    strata_report: dict[str, dict[str, Any]] = {}
    selected_new: list[dict[str, Any]] = []
    carried: list[dict[str, Any]] = []
    for key in NON_SINGLETON_STRATA:
        rows = sorted(strata_rows.get(key, []), key=row_sort_key)
        eligible = [row for row in rows if row.get("scenario") not in existing]
        chosen = eligible[:2]
        strata_report[" / ".join(key)] = {
            "source_count": len(rows),
            "eligible_after_existing_scenario_exclusion": len(eligible),
            "selected_count": len(chosen),
            "selected_role": "new_candidate",
            "selected": [compact_row(row, "new_candidate") for row in chosen],
        }
        selected_new.extend(chosen)
    singleton_rows = sorted(strata_rows.get(SINGLETON_STRATUM, []), key=row_sort_key)
    singleton_chosen = singleton_rows[:1]
    strata_report[" / ".join(SINGLETON_STRATUM)] = {
        "source_count": len(singleton_rows),
        "eligible_after_existing_scenario_exclusion": len(
            [row for row in singleton_rows if row.get("scenario") not in existing]
        ),
        "selected_count": len(singleton_chosen),
        "selected_role": "carried_existing_singleton",
        "selected": [compact_row(row, "carried_existing_singleton") for row in singleton_chosen],
    }
    carried.extend(singleton_chosen)
    return {
        "strata": strata_report,
        "selected_rows": [compact_row(row, "new_candidate") for row in selected_new]
        + [compact_row(row, "carried_existing_singleton") for row in carried],
        "selected_new_rows": [compact_row(row, "new_candidate") for row in selected_new],
        "carried_singleton_rows": [compact_row(row, "carried_existing_singleton") for row in carried],
    }


def classify(measurements: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "provenance_batch_design_insufficient"
    stratum_values = measurements["strata"].values()
    non_singleton_ok = all(
        item["selected_count"] == 2
        for key, item in measurements["strata"].items()
        if key != " / ".join(SINGLETON_STRATUM)
    )
    singleton_ok = measurements["strata"][" / ".join(SINGLETON_STRATUM)]["selected_count"] == 1
    covers_all = len(list(stratum_values)) == len(ALL_STRATA)
    if (
        non_singleton_ok
        and singleton_ok
        and covers_all
        and measurements["selected_new_count"] == 12
        and measurements["carried_singleton_count"] == 1
    ):
        return "provenance_batch_design_balanced_with_carried_singleton"
    return "provenance_batch_design_partial"


def choose_verdict(label: str, infra_problems: list[str]) -> str:
    if infra_problems or label == "provenance_batch_design_insufficient":
        return "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_BLOCKED"
    if label == "provenance_batch_design_balanced_with_carried_singleton":
        return "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE"
    return "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_PARTIAL_COMPLETE"


def build_report(iter54_report_path: Path, iter59_report_path: Path, iter100_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter54_report, problems54 = load_report(iter54_report_path, "iter54-report")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter100_report, problems100 = load_report(iter100_report_path, "iter100-report")
    infra_problems.extend(problems54 + problems59 + problems100)
    measurements: dict[str, Any] = {}
    label = "provenance_batch_design_insufficient"
    if not infra_problems:
        infra_problems.extend(source_checks(iter54_report, iter59_report, iter100_report))
        existing = existing_scenarios(iter59_report)
        selection = select_schedule(iter54_report, existing, infra_problems)
        stratum_counts = Counter(
            (row.get("dataset"), row.get("monitor_provenance_label"))
            for row in iter54_report.get("pairs", [])
            if isinstance(row, dict) and row.get("on_collision") is True
        )
        measurements = {
            "existing_instrumented_scenarios": sorted(existing),
            "on_collision_stratum_counts": {f"{dataset} / {label_}": count for (dataset, label_), count in sorted(stratum_counts.items())},
            "strata": selection["strata"],
            "selected_rows": selection["selected_rows"],
            "selected_new_rows": selection["selected_new_rows"],
            "carried_singleton_rows": selection["carried_singleton_rows"],
            "selected_total_count": len(selection["selected_rows"]),
            "selected_new_count": len(selection["selected_new_rows"]),
            "carried_singleton_count": len(selection["carried_singleton_rows"]),
            "all_strata_covered": len(selection["strata"]) == len(ALL_STRATA),
        }
        label = classify(measurements, infra_problems)
    return {
        "iteration": 101,
        "inputs": {
            "iter54_report": str(iter54_report_path),
            "iter59_report": str(iter59_report_path),
            "iter100_report": str(iter100_report_path),
        },
        "infra_problems": infra_problems,
        "event": {
            "row_label": label,
            "measurements": measurements,
            "problems": [] if not infra_problems else infra_problems,
        },
        "summary": {
            "selected_total_count": measurements.get("selected_total_count", 0),
            "selected_new_count": measurements.get("selected_new_count", 0),
            "carried_singleton_count": measurements.get("carried_singleton_count", 0),
            "all_strata_covered": measurements.get("all_strata_covered", False),
            "existing_instrumented_scenario_count": len(measurements.get("existing_instrumented_scenarios", [])),
        },
        "verdict": choose_verdict(label, infra_problems),
        "claim_boundary": (
            "offline candidate-schedule design only; no actor-causality, repair, threshold-value, "
            "transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, "
            "commercial-value, real-world behavior, first-responder behavior, retuning, GPU approval, "
            "or approval-to-run claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 101 - HUGSIM provenance batch candidate design",
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
    measurements = report["event"].get("measurements") or {}
    lines.extend(
        [
            "",
            "## Selected Rows",
            "",
            "| role | dataset | stratum | scenario | run | tier | timing | first fire | first collision |",
            "|---|---|---|---|---:|---|---|---:|---:|",
        ]
    )
    for row in measurements.get("selected_rows", []):
        lines.append(
            f"| `{row['selection_role']}` | `{row['dataset']}` | "
            f"`{row['monitor_provenance_label']}` | `{row['scenario']}` | `{row['run']}` | "
            f"`{row['tier']}` | `{row['fire_timing_label']}` | "
            f"`{row['first_fire_ts']}` | `{row['first_on_nc_time']}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter54_report: Path, iter59_report: Path, iter100_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter54_report, iter59_report, iter100_report)
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
        "--iter100-report",
        type=Path,
        default=Path(
            "experiments/iter100_hugsim_structural_expansion_support_audit/proof-expansion/"
            "structural_expansion_support_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter101_hugsim_provenance_batch_candidate_design/proof-design/"
            "provenance_batch_candidate_design_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter101_hugsim_provenance_batch_candidate_design/proof-design/"
            "provenance_batch_candidate_design.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter54_report, args.iter59_report, args.iter100_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
