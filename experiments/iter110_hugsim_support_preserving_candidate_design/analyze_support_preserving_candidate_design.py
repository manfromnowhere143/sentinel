#!/usr/bin/env python3
"""Iteration 110 HUGSIM support-preserving candidate design."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER52_VERDICT = "TIMING_AUDIT_COMPLETE"
ITER54_VERDICT = "PROVENANCE_SUPPORT_NULL"
ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER104_VERDICT = "HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_SUPPORT_NULL"
ITER109_VERDICT = "HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE"

INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_INFRA_NULL"
THIRTEEN_SLOT_COMPLETE_VERDICT = "HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_13_SLOT_COMPLETE"
CORE_COMPLETE_VERDICT = "HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE"
SUPPORT_NULL_VERDICT = "HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_SUPPORT_NULL"

EXPECTED_PAIR_COUNT = 104
EXPECTED_ITER59_EPISODES = 8
EXPECTED_BATCH_EPISODES = 13
MIN_CORE_FLOOR = 4
TARGET_SLOT_COUNT = 13
TIMING_LABELS = ("long_lead_fire", "short_lead_fire")
CHANNELS = ("ttc_only", "cpa_only")
PROVENANCE_LABELS = ("unique_ttc_object", "unique_cpa_object")
TIMING_BIN_BY_LABEL = {
    "long_lead_fire": "long_lead_brake",
    "short_lead_fire": "short_lead_brake",
}
SUPPORT_PRESERVING_LABELS = {
    "exact_ttc_classifiable_anchor",
    "ttc_classifiable_scenario_analogue",
}
LABEL_PRIORITY = {
    "exact_ttc_classifiable_anchor": 0,
    "ttc_classifiable_scenario_analogue": 1,
    "ttc_residual_risk_probe": 2,
    "cpa_residual_risk_fallback": 3,
    "ineligible_or_schema_gap": 4,
}
TIMING_PRIORITY = {"short_lead_fire": 0, "long_lead_fire": 1}


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
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def row_key(row: dict[str, Any]) -> tuple[str, int]:
    scenario = row.get("scenario")
    run = row.get("run")
    return (str(scenario), int(run) if isinstance(run, int) else 999)


def source_list(report: dict[str, Any], key: str, label: str, problems: list[str]) -> list[dict[str, Any]]:
    rows = report.get(key)
    if not isinstance(rows, list):
        problems.append(f"{label}-{key}-not-list")
        return []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    if len(dict_rows) != len(rows):
        problems.append(f"{label}-{key}-contains-nondict")
    return dict_rows


def source_checks(
    iter52_report: dict[str, Any],
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter104_report: dict[str, Any],
    iter109_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    require_equal(problems, "iter52-verdict", iter52_report.get("verdict"), ITER52_VERDICT)
    require_equal(problems, "iter54-verdict", iter54_report.get("verdict"), ITER54_VERDICT)
    require_equal(problems, "iter59-verdict", iter59_report.get("verdict"), ITER59_VERDICT)
    require_equal(problems, "iter104-verdict", iter104_report.get("verdict"), ITER104_VERDICT)
    require_equal(problems, "iter109-verdict", iter109_report.get("verdict"), ITER109_VERDICT)

    if iter54_report.get("infrastructure_problems"):
        problems.append(f"iter54-infrastructure-problems:{iter54_report.get('infrastructure_problems')}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter104_report.get("infra_problems"):
        problems.append(f"iter104-infra-problems:{iter104_report.get('infra_problems')}")
    if iter109_report.get("infra_problems"):
        problems.append(f"iter109-infra-problems:{iter109_report.get('infra_problems')}")

    pairs52 = source_list(iter52_report, "pairs", "iter52", problems)
    pairs54 = source_list(iter54_report, "pairs", "iter54", problems)
    episodes59 = source_list(iter59_report, "episodes", "iter59", problems)
    episodes104 = source_list(iter104_report, "episodes", "iter104", problems)
    slots109 = source_list(iter109_report, "slots", "iter109", problems)

    require_equal(problems, "iter52-pair-count", len(pairs52), EXPECTED_PAIR_COUNT)
    require_equal(problems, "iter54-pair-count", len(pairs54), EXPECTED_PAIR_COUNT)
    require_equal(problems, "iter59-episode-count", len(episodes59), EXPECTED_ITER59_EPISODES)
    require_equal(problems, "iter104-episode-count", len(episodes104), EXPECTED_BATCH_EPISODES)
    require_equal(problems, "iter109-slot-count", len(slots109), EXPECTED_BATCH_EPISODES)

    summary104 = iter104_report.get("summary")
    if isinstance(summary104, dict):
        require_equal(problems, "iter104-min-classifiable-bar", summary104.get("min_classifiable_bar"), MIN_CORE_FLOOR)
    else:
        problems.append("iter104-summary-not-dict")
    summary109 = iter109_report.get("summary")
    if isinstance(summary109, dict):
        require_equal(problems, "iter109-classifiable-success", summary109.get("classifiable_success"), 2)
    else:
        problems.append("iter109-summary-not-dict")
    return pairs52, pairs54, episodes59, episodes104, slots109, problems


def timing_eligible(row: dict[str, Any]) -> bool:
    lead = finite_number(row.get("first_fire_lead_time"))
    return (
        row.get("on_collision") is True
        and row.get("fire_timing_label") in TIMING_LABELS
        and lead is not None
        and lead >= 0.0
        and row.get("first_fire_channel") in CHANNELS
        and row.get("monitor_provenance_label") in PROVENANCE_LABELS
    )


def crosscheck_timing_rows(
    eligible_rows: list[dict[str, Any]],
    pairs52: list[dict[str, Any]],
) -> list[str]:
    problems: list[str] = []
    timing_by_key = {
        row_key(row): row
        for row in pairs52
        if isinstance(row.get("scenario"), str) and isinstance(row.get("run"), int)
    }
    for row in eligible_rows:
        key = row_key(row)
        timing_row = timing_by_key.get(key)
        if timing_row is None:
            problems.append(f"timing-row-missing:{key}")
            continue
        expected_bin = TIMING_BIN_BY_LABEL.get(str(row.get("fire_timing_label")))
        if timing_row.get("timing_bin") != expected_bin:
            problems.append(f"timing-bin-mismatch:{key}:{timing_row.get('timing_bin')}!={expected_bin}")
        for field in ("first_on_nc_time", "first_fire_ts"):
            if timing_row.get(field) != row.get(field):
                problems.append(f"timing-{field}-mismatch:{key}:{timing_row.get(field)}!={row.get(field)}")
        if timing_row.get("lead_time") != row.get("first_fire_lead_time"):
            problems.append(f"timing-lead-time-mismatch:{key}:{timing_row.get('lead_time')}!={row.get('first_fire_lead_time')}")
    return problems


def evidence_source(source: str, support_label: Any, bridge_label: Any = None) -> str:
    if bridge_label:
        return f"{source}:{support_label}:{bridge_label}"
    return f"{source}:{support_label}"


def build_prior_evidence(
    episodes59: list[dict[str, Any]],
    episodes104: list[dict[str, Any]],
    slots109: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_positive: dict[tuple[str, int], list[str]] = defaultdict(list)
    exact_nonclassifiable: dict[tuple[str, int], list[str]] = defaultdict(list)
    scenario_positive: dict[str, list[str]] = defaultdict(list)
    scenario_nonclassifiable: dict[str, list[str]] = defaultdict(list)

    def add_scenario(row: dict[str, Any], source: str, positive: bool, support_label: Any, bridge_label: Any = None) -> None:
        scenario = row.get("scenario")
        if not isinstance(scenario, str):
            return
        target = scenario_positive if positive else scenario_nonclassifiable
        target[scenario].append(evidence_source(source, support_label, bridge_label))

    def add_exact(row: dict[str, Any], source: str, positive: bool, support_label: Any, bridge_label: Any = None) -> None:
        if not isinstance(row.get("scenario"), str) or not isinstance(row.get("run"), int):
            return
        key = row_key(row)
        target = exact_positive if positive else exact_nonclassifiable
        target[key].append(evidence_source(source, support_label, bridge_label))

    for row in episodes59:
        support_label = row.get("support_label")
        positive = support_label == "classifiable_foreground"
        add_scenario(row, "iter59", positive, support_label, row.get("bridge_label"))
    for row in episodes104:
        support_label = row.get("support_label")
        positive = support_label == "classifiable_foreground"
        add_scenario(row, "iter104", positive, support_label, row.get("bridge_label"))
        add_exact(row, "iter104", positive, support_label, row.get("bridge_label"))
    for row in slots109:
        residual_label = row.get("residual_label")
        support_label = row.get("observed_support_label")
        positive = residual_label == "classifiable_success" or support_label == "classifiable_foreground"
        label = residual_label if residual_label is not None else support_label
        add_scenario(row, "iter109", positive, label, row.get("observed_bridge_label"))
        add_exact(row, "iter109", positive, label, row.get("observed_bridge_label"))

    prior_scenarios = set(scenario_positive) | set(scenario_nonclassifiable)
    return {
        "exact_positive": {key: sorted(value) for key, value in exact_positive.items()},
        "exact_nonclassifiable": {key: sorted(value) for key, value in exact_nonclassifiable.items()},
        "scenario_positive": {key: sorted(value) for key, value in scenario_positive.items()},
        "scenario_nonclassifiable": {key: sorted(value) for key, value in scenario_nonclassifiable.items()},
        "prior_scenarios": sorted(prior_scenarios),
    }


def design_label(row: dict[str, Any], evidence: dict[str, Any]) -> str:
    channel = row.get("first_fire_channel")
    key = row_key(row)
    scenario = str(row.get("scenario"))
    if channel == "cpa_only":
        return "cpa_residual_risk_fallback"
    if channel != "ttc_only":
        return "ineligible_or_schema_gap"
    exact_positive = key in evidence["exact_positive"]
    exact_nonclassifiable = key in evidence["exact_nonclassifiable"]
    scenario_positive = scenario in evidence["scenario_positive"]
    if exact_positive and not exact_nonclassifiable:
        return "exact_ttc_classifiable_anchor"
    if scenario_positive and not exact_nonclassifiable:
        return "ttc_classifiable_scenario_analogue"
    return "ttc_residual_risk_probe"


def compact_row(row: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    key = row_key(row)
    scenario = str(row.get("scenario"))
    fields = (
        "dataset",
        "scenario",
        "run",
        "tier",
        "monitor_provenance_label",
        "first_fire_channel",
        "fire_timing_label",
        "first_on_nc_time",
        "first_fire_ts",
        "first_fire_lead_time",
        "fired_frames",
        "brake_frames",
    )
    compact = {field: row.get(field) for field in fields}
    compact["design_label"] = design_label(row, evidence)
    compact["exact_positive_sources"] = evidence["exact_positive"].get(key, [])
    compact["exact_nonclassifiable_sources"] = evidence["exact_nonclassifiable"].get(key, [])
    compact["scenario_positive_sources"] = evidence["scenario_positive"].get(scenario, [])
    compact["scenario_nonclassifiable_sources"] = evidence["scenario_nonclassifiable"].get(scenario, [])
    return compact


def sort_key(row: dict[str, Any]) -> tuple[int, int, float, str, int]:
    lead = finite_number(row.get("first_fire_lead_time"))
    return (
        LABEL_PRIORITY.get(str(row.get("design_label")), 99),
        TIMING_PRIORITY.get(str(row.get("fire_timing_label")), 99),
        -(lead if lead is not None else -999.0),
        str(row.get("scenario")),
        int(row.get("run")) if isinstance(row.get("run"), int) else 999,
    )


def cap_two_per_scenario(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    capped: list[dict[str, Any]] = []
    scenario_counts: Counter[str] = Counter()
    for row in sorted(rows, key=sort_key):
        scenario = str(row.get("scenario"))
        if scenario_counts[scenario] >= 2:
            continue
        capped.append(row)
        scenario_counts[scenario] += 1
    return capped


def select_design_rows(eligible_rows: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    labeled_rows = [compact_row(row, evidence) for row in eligible_rows]
    unsupported_labels = sorted(
        {str(row.get("design_label")) for row in labeled_rows if row.get("design_label") not in LABEL_PRIORITY}
    )
    core_pool = [row for row in labeled_rows if row.get("design_label") in SUPPORT_PRESERVING_LABELS]
    core_rows = cap_two_per_scenario(core_pool)
    fallback_rows = sorted(
        [row for row in labeled_rows if row.get("design_label") not in SUPPORT_PRESERVING_LABELS],
        key=sort_key,
    )
    prior_scenarios = set(evidence["prior_scenarios"])
    fresh_primary_rows = sorted(
        [row for row in labeled_rows if row.get("scenario") not in prior_scenarios],
        key=sort_key,
    )
    return {
        "timing_eligible_rows": sorted(labeled_rows, key=sort_key),
        "support_preserving_core_rows": core_rows,
        "fallback_pressure_rows": fallback_rows,
        "fresh_primary_rows": fresh_primary_rows,
        "unsupported_labels": unsupported_labels,
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def build_summary(
    selected: dict[str, Any],
    evidence: dict[str, Any],
    infra_problems: list[str],
) -> dict[str, Any]:
    rows = selected["timing_eligible_rows"]
    core_rows = selected["support_preserving_core_rows"]
    fallback_rows = selected["fallback_pressure_rows"]
    fresh_rows = selected["fresh_primary_rows"]
    return {
        "target_slot_count": TARGET_SLOT_COUNT,
        "min_core_floor": MIN_CORE_FLOOR,
        "timing_eligible_count": len(rows),
        "design_label_counts": count_by(rows, "design_label"),
        "support_preserving_core_count": len(core_rows),
        "exact_ttc_classifiable_anchor_count": sum(
            row.get("design_label") == "exact_ttc_classifiable_anchor" for row in core_rows
        ),
        "ttc_classifiable_scenario_analogue_count": sum(
            row.get("design_label") == "ttc_classifiable_scenario_analogue" for row in core_rows
        ),
        "core_channel_counts": count_by(core_rows, "first_fire_channel"),
        "core_timing_counts": count_by(core_rows, "fire_timing_label"),
        "fallback_pressure_count": len(fallback_rows),
        "fallback_label_counts": count_by(fallback_rows, "design_label"),
        "fresh_primary_count": len(fresh_rows),
        "fresh_primary_channel_counts": count_by(fresh_rows, "first_fire_channel"),
        "prior_support_scenario_count": len(evidence["prior_scenarios"]),
        "full_13_support_preserving_available": len(core_rows) >= TARGET_SLOT_COUNT,
        "infra_problem_count": len(infra_problems),
    }


def choose_verdict(core_count: int, infra_problems: list[str], unsupported_labels: list[str]) -> str:
    if infra_problems or unsupported_labels:
        return INFRA_NULL_VERDICT
    if core_count >= TARGET_SLOT_COUNT:
        return THIRTEEN_SLOT_COMPLETE_VERDICT
    if core_count >= MIN_CORE_FLOOR:
        return CORE_COMPLETE_VERDICT
    return SUPPORT_NULL_VERDICT


def build_report_from_reports(
    iter52_report: dict[str, Any],
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter104_report: dict[str, Any],
    iter109_report: dict[str, Any],
    inputs: dict[str, str],
    initial_problems: list[str] | None = None,
) -> dict[str, Any]:
    infra_problems: list[str] = list(initial_problems or [])
    selected = {
        "timing_eligible_rows": [],
        "support_preserving_core_rows": [],
        "fallback_pressure_rows": [],
        "fresh_primary_rows": [],
        "unsupported_labels": [],
    }
    evidence = {
        "exact_positive": {},
        "exact_nonclassifiable": {},
        "scenario_positive": {},
        "scenario_nonclassifiable": {},
        "prior_scenarios": [],
    }
    if not infra_problems:
        pairs52, pairs54, episodes59, episodes104, slots109, source_problems = source_checks(
            iter52_report,
            iter54_report,
            iter59_report,
            iter104_report,
            iter109_report,
        )
        infra_problems.extend(source_problems)
    else:
        pairs52, pairs54, episodes59, episodes104, slots109 = [], [], [], [], []
    if not infra_problems:
        eligible_rows = [row for row in pairs54 if timing_eligible(row)]
        infra_problems.extend(crosscheck_timing_rows(eligible_rows, pairs52))
        evidence = build_prior_evidence(episodes59, episodes104, slots109)
        selected = select_design_rows(eligible_rows, evidence)
        if selected["unsupported_labels"]:
            infra_problems.append(f"unsupported-design-labels:{selected['unsupported_labels']}")
    summary = build_summary(selected, evidence, infra_problems)
    return {
        "iteration": 110,
        "inputs": inputs,
        "infra_problems": infra_problems,
        "prior_evidence_summary": {
            "exact_positive_count": len(evidence["exact_positive"]),
            "exact_nonclassifiable_count": len(evidence["exact_nonclassifiable"]),
            "scenario_positive_count": len(evidence["scenario_positive"]),
            "scenario_nonclassifiable_count": len(evidence["scenario_nonclassifiable"]),
            "prior_scenario_count": len(evidence["prior_scenarios"]),
        },
        "event": {"measurements": selected},
        "summary": summary,
        "verdict": choose_verdict(
            len(selected["support_preserving_core_rows"]),
            infra_problems,
            selected["unsupported_labels"],
        ),
        "claim_boundary": (
            "offline support-preserving candidate design only; no actor-causality, actor-match "
            "support upgrade, repair, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, commercial, schedule-selection, "
            "launch-manifest, or GPU-approval claim"
        ),
    }


def build_report(
    iter52_report_path: Path,
    iter54_report_path: Path,
    iter59_report_path: Path,
    iter104_report_path: Path,
    iter109_report_path: Path,
) -> dict[str, Any]:
    iter52_report, problems52 = load_json(iter52_report_path, "iter52-report")
    iter54_report, problems54 = load_json(iter54_report_path, "iter54-report")
    iter59_report, problems59 = load_json(iter59_report_path, "iter59-report")
    iter104_report, problems104 = load_json(iter104_report_path, "iter104-report")
    iter109_report, problems109 = load_json(iter109_report_path, "iter109-report")
    return build_report_from_reports(
        iter52_report,
        iter54_report,
        iter59_report,
        iter104_report,
        iter109_report,
        {
            "iter52_report": str(iter52_report_path),
            "iter54_report": str(iter54_report_path),
            "iter59_report": str(iter59_report_path),
            "iter104_report": str(iter104_report_path),
            "iter109_report": str(iter109_report_path),
        },
        problems52 + problems54 + problems59 + problems104 + problems109,
    )


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 110 - HUGSIM support-preserving candidate design",
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
    measurements = report["event"]["measurements"]
    lines.extend(
        [
            "",
            "## Support-Preserving Core",
            "",
            "| role | scenario | run | dataset | tier | timing | lead s | positive evidence | nonclass evidence |",
            "|---|---|---:|---|---|---|---:|---|---|",
        ]
    )
    for row in measurements.get("support_preserving_core_rows", []):
        positive = row.get("exact_positive_sources") or row.get("scenario_positive_sources")
        nonclass = row.get("exact_nonclassifiable_sources") or []
        lines.append(
            f"| `{row.get('design_label')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('dataset')}` | `{row.get('tier')}` | `{row.get('fire_timing_label')}` | "
            f"`{row.get('first_fire_lead_time')}` | `{positive}` | `{nonclass}` |"
        )
    lines.extend(
        [
            "",
            "## Fallback Pressure",
            "",
            "| role | scenario | run | channel | timing | lead s | scenario nonclass evidence |",
            "|---|---|---:|---|---|---:|---|",
        ]
    )
    for row in measurements.get("fallback_pressure_rows", []):
        lines.append(
            f"| `{row.get('design_label')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('first_fire_channel')}` | `{row.get('fire_timing_label')}` | "
            f"`{row.get('first_fire_lead_time')}` | `{row.get('scenario_nonclassifiable_sources')}` |"
        )
    lines.extend(
        [
            "",
            "## Fresh Primary Rows",
            "",
            "| role | scenario | run | channel | timing | lead s |",
            "|---|---|---:|---|---|---:|",
        ]
    )
    for row in measurements.get("fresh_primary_rows", []):
        lines.append(
            f"| `{row.get('design_label')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('first_fire_channel')}` | `{row.get('fire_timing_label')}` | "
            f"`{row.get('first_fire_lead_time')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter52_report: Path,
    iter54_report: Path,
    iter59_report: Path,
    iter104_report: Path,
    iter109_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter52_report, iter54_report, iter59_report, iter104_report, iter109_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter52-report",
        type=Path,
        default=Path("experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json"),
    )
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
        "--iter104-report",
        type=Path,
        default=Path(
            "experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/"
            "provenance_batch_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--iter109-report",
        type=Path,
        default=Path(
            "experiments/iter109_hugsim_timing_aware_support_yield_decomposition/proof-decomposition/"
            "timing_aware_support_yield_decomposition_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter110_hugsim_support_preserving_candidate_design/proof-design/"
            "support_preserving_candidate_design_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter110_hugsim_support_preserving_candidate_design/proof-design/"
            "support_preserving_candidate_design.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter52_report,
        args.iter54_report,
        args.iter59_report,
        args.iter104_report,
        args.iter109_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
