#!/usr/bin/env python3
"""Iteration 105 HUGSIM timing-aware provenance batch design."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER52_VERDICT = "TIMING_AUDIT_COMPLETE"
ITER54_VERDICT = "PROVENANCE_SUPPORT_NULL"
ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER104_VERDICT = "HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_SUPPORT_NULL"

INFRA_NULL_VERDICT = "HUGSIM_TIMING_AWARE_BATCH_DESIGN_INFRA_NULL"
SUPPORT_NULL_VERDICT = "HUGSIM_TIMING_AWARE_BATCH_DESIGN_SUPPORT_NULL"
COMPLETE_VERDICT = "HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE"

TARGET_SLOT_COUNT = 13
MIN_UNIQUE_SCENARIOS = 8
DATASETS = ("iter48_easy_medium", "iter49_hard_extreme")
CHANNELS = ("cpa_only", "ttc_only")
TIERS = ("easy", "medium", "hard", "extreme")
TIMING_LABELS = ("long_lead_fire", "short_lead_fire")
TIMING_BIN_BY_LABEL = {
    "long_lead_fire": "long_lead_brake",
    "short_lead_fire": "short_lead_brake",
}


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


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def row_key(row: dict[str, Any]) -> tuple[str, int]:
    scenario = row.get("scenario")
    run = row.get("run")
    return (str(scenario), int(run) if isinstance(run, int) else 999)


def priority_key(row: dict[str, Any]) -> tuple[float, int, int, str, int]:
    lead = row.get("first_fire_lead_time")
    brake_frames = row.get("brake_frames")
    fired_frames = row.get("fired_frames")
    scenario, run = row_key(row)
    return (
        -float(lead) if is_number(lead) else 0.0,
        -int(brake_frames) if isinstance(brake_frames, int) else 0,
        -int(fired_frames) if isinstance(fired_frames, int) else 0,
        scenario,
        run,
    )


def compact_row(row: dict[str, Any], slot_index: int | None, reason: str) -> dict[str, Any]:
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
    compact["selection_reason"] = reason
    if slot_index is not None:
        compact["slot_index"] = slot_index
        compact["slot_id"] = f"i105_slot_{slot_index:02d}"
    return compact


def report_list(report: dict[str, Any], key: str, label: str, problems: list[str]) -> list[dict[str, Any]]:
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
) -> list[str]:
    problems: list[str] = []
    if iter52_report.get("verdict") != ITER52_VERDICT:
        problems.append(f"iter52-verdict-not-{ITER52_VERDICT}")
    if iter54_report.get("verdict") != ITER54_VERDICT:
        problems.append(f"iter54-verdict-not-{ITER54_VERDICT}")
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter104_report.get("verdict") != ITER104_VERDICT:
        problems.append(f"iter104-verdict-not-{ITER104_VERDICT}")
    if iter54_report.get("infrastructure_problems"):
        problems.append(f"iter54-infrastructure-problems:{iter54_report.get('infrastructure_problems')}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter104_report.get("infra_problems"):
        problems.append(f"iter104-infra-problems:{iter104_report.get('infra_problems')}")
    pairs54 = report_list(iter54_report, "pairs", "iter54", problems)
    pairs52 = report_list(iter52_report, "pairs", "iter52", problems)
    if len(pairs54) != 104:
        problems.append(f"iter54-pair-count:{len(pairs54)}!=104")
    if len(pairs52) != 104:
        problems.append(f"iter52-pair-count:{len(pairs52)}!=104")
    summary104 = iter104_report.get("summary")
    if not isinstance(summary104, dict):
        problems.append("iter104-summary-not-dict")
    else:
        if summary104.get("classifiable_foreground") != 1:
            problems.append("iter104-classifiable-foreground-not-1")
        if summary104.get("min_classifiable_bar") != 4:
            problems.append("iter104-min-classifiable-bar-not-4")
    return problems


def existing_scenarios(iter59_report: dict[str, Any], iter104_report: dict[str, Any]) -> set[str]:
    scenarios: set[str] = set()
    for report in (iter59_report, iter104_report):
        episodes = report.get("episodes")
        if isinstance(episodes, list):
            scenarios.update(
                str(row["scenario"])
                for row in episodes
                if isinstance(row, dict) and isinstance(row.get("scenario"), str)
            )
    return scenarios


def is_timing_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("on_collision") is True
        and row.get("fire_timing_label") in TIMING_LABELS
        and is_number(row.get("first_fire_lead_time"))
        and float(row["first_fire_lead_time"]) >= 0.0
        and row.get("first_fire_channel") in CHANNELS
        and row.get("monitor_provenance_label") in ("unique_cpa_object", "unique_ttc_object")
    )


def choose_row(
    pool: list[dict[str, Any]],
    selected_keys: set[tuple[str, int]],
    scenario_counts: Counter[str],
    predicate: Any,
) -> dict[str, Any] | None:
    for row in sorted(pool, key=priority_key):
        scenario, _run = row_key(row)
        if row_key(row) in selected_keys:
            continue
        if scenario_counts[scenario] >= 2:
            continue
        if predicate(row):
            return row
    return None


def select_schedule(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[tuple[dict[str, Any], str]] = []
    selected_keys: set[tuple[str, int]] = set()
    scenario_counts: Counter[str] = Counter()

    def add(row: dict[str, Any] | None, reason: str) -> None:
        if row is None:
            return
        key = row_key(row)
        scenario, _run = key
        selected.append((row, reason))
        selected_keys.add(key)
        scenario_counts[scenario] += 1

    for dataset in DATASETS:
        add(
            choose_row(pool, selected_keys, scenario_counts, lambda row, dataset=dataset: row.get("dataset") == dataset),
            f"coverage_dataset_{dataset}",
        )
    for channel in CHANNELS:
        add(
            choose_row(
                pool,
                selected_keys,
                scenario_counts,
                lambda row, channel=channel: row.get("first_fire_channel") == channel,
            ),
            f"coverage_channel_{channel}",
        )
    for tier in TIERS:
        if any(row.get("tier") == tier for row in pool):
            add(
                choose_row(pool, selected_keys, scenario_counts, lambda row, tier=tier: row.get("tier") == tier),
                f"coverage_tier_{tier}",
            )
    for timing_label in TIMING_LABELS:
        if any(row.get("fire_timing_label") == timing_label for row in pool):
            add(
                choose_row(
                    pool,
                    selected_keys,
                    scenario_counts,
                    lambda row, timing_label=timing_label: row.get("fire_timing_label") == timing_label,
                ),
                f"coverage_timing_{timing_label}",
            )

    while len(selected) < TARGET_SLOT_COUNT:
        row = choose_row(pool, selected_keys, scenario_counts, lambda _row: True)
        if row is None:
            break
        add(row, "priority_fill")

    return [compact_row(row, slot_index + 1, reason) for slot_index, (row, reason) in enumerate(selected)]


def cross_check_selected_with_iter52(
    selected_rows: list[dict[str, Any]],
    iter52_report: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    pairs52 = iter52_report.get("pairs")
    if not isinstance(pairs52, list):
        return ["iter52-pairs-not-list-for-cross-check"]
    by_key = {
        row_key(row): row
        for row in pairs52
        if isinstance(row, dict) and isinstance(row.get("scenario"), str) and isinstance(row.get("run"), int)
    }
    for row in selected_rows:
        key = row_key(row)
        timing_row = by_key.get(key)
        if not timing_row:
            problems.append(f"selected-row-missing-in-iter52:{key}")
            continue
        expected_bin = TIMING_BIN_BY_LABEL.get(str(row.get("fire_timing_label")))
        if timing_row.get("timing_bin") != expected_bin:
            problems.append(f"iter52-timing-bin-mismatch:{key}:{timing_row.get('timing_bin')}!={expected_bin}")
        for field in ("first_on_nc_time", "first_fire_ts"):
            if timing_row.get(field) != row.get(field):
                problems.append(f"iter52-{field}-mismatch:{key}:{timing_row.get(field)}!={row.get(field)}")
        if timing_row.get("lead_time") != row.get("first_fire_lead_time"):
            problems.append(
                f"iter52-lead-time-mismatch:{key}:{timing_row.get('lead_time')}!={row.get('first_fire_lead_time')}"
            )
    return problems


def policy_problems(report: dict[str, Any]) -> list[str]:
    selected = report["event"]["measurements"].get("selected_rows", [])
    primary_pool_count = report["summary"]["primary_eligible_count"]
    selected_count = report["summary"]["selected_slot_count"]
    unique_scenarios = report["summary"]["selected_unique_scenario_count"]
    datasets = set(report["summary"]["selected_dataset_counts"])
    channels = set(report["summary"]["selected_channel_counts"])
    tiers = set(report["summary"]["selected_tier_counts"])
    timings = set(report["summary"]["selected_timing_counts"])
    primary_timings = set(report["summary"]["primary_timing_counts"])
    problems: list[str] = []
    if primary_pool_count < TARGET_SLOT_COUNT:
        problems.append(f"primary-pool-too-small:{primary_pool_count}<{TARGET_SLOT_COUNT}")
    if selected_count != TARGET_SLOT_COUNT:
        problems.append(f"selected-slot-count:{selected_count}!={TARGET_SLOT_COUNT}")
    if unique_scenarios < MIN_UNIQUE_SCENARIOS:
        problems.append(f"selected-unique-scenarios:{unique_scenarios}<{MIN_UNIQUE_SCENARIOS}")
    if not set(DATASETS).issubset(datasets):
        problems.append("selected-datasets-do-not-cover-both")
    if not set(CHANNELS).issubset(channels):
        problems.append("selected-channels-do-not-cover-both")
    if len(tiers) < 3:
        problems.append(f"selected-tier-count:{len(tiers)}<3")
    if "short_lead_fire" in primary_timings and "short_lead_fire" not in timings:
        problems.append("primary-short-lead-exists-but-selection-has-none")
    scenario_counts = Counter(row.get("scenario") for row in selected)
    too_many = sorted(str(scenario) for scenario, count in scenario_counts.items() if count > 2)
    if too_many:
        problems.append(f"scenario-selected-more-than-twice:{too_many}")
    return problems


def choose_verdict(infra_problems: list[str], support_problems: list[str]) -> str:
    if infra_problems:
        return INFRA_NULL_VERDICT
    if support_problems:
        return SUPPORT_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report_from_reports(
    iter52_report: dict[str, Any],
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter104_report: dict[str, Any],
    inputs: dict[str, str],
    initial_problems: list[str] | None = None,
) -> dict[str, Any]:
    infra_problems: list[str] = list(initial_problems or [])
    measurements: dict[str, Any] = {
        "existing_instrumented_scenarios": [],
        "primary_eligible_rows": [],
        "excluded_eligible_rows": [],
        "selected_rows": [],
    }
    if not infra_problems:
        infra_problems.extend(source_checks(iter52_report, iter54_report, iter59_report, iter104_report))
    if not infra_problems:
        pairs54 = report_list(iter54_report, "pairs", "iter54", infra_problems)
        existing = existing_scenarios(iter59_report, iter104_report)
        eligible_rows = [row for row in pairs54 if is_timing_eligible(row)]
        primary_pool = [row for row in eligible_rows if str(row.get("scenario")) not in existing]
        excluded_pool = [row for row in eligible_rows if str(row.get("scenario")) in existing]
        selected_rows = select_schedule(primary_pool if len(primary_pool) >= TARGET_SLOT_COUNT else eligible_rows)
        measurements = {
            "existing_instrumented_scenarios": sorted(existing),
            "primary_eligible_rows": [compact_row(row, None, "primary_pool") for row in sorted(primary_pool, key=priority_key)],
            "excluded_eligible_rows": [compact_row(row, None, "excluded_existing") for row in sorted(excluded_pool, key=priority_key)],
            "selected_rows": selected_rows,
        }
        infra_problems.extend(cross_check_selected_with_iter52(selected_rows, iter52_report))

    selected_rows = measurements.get("selected_rows", [])
    primary_rows = measurements.get("primary_eligible_rows", [])
    excluded_rows = measurements.get("excluded_eligible_rows", [])
    summary = {
        "target_slot_count": TARGET_SLOT_COUNT,
        "primary_eligible_count": len(primary_rows),
        "excluded_eligible_count": len(excluded_rows),
        "selected_slot_count": len(selected_rows),
        "selected_unique_scenario_count": len({row.get("scenario") for row in selected_rows}),
        "selected_dataset_counts": dict(sorted(Counter(row.get("dataset") for row in selected_rows).items())),
        "selected_channel_counts": dict(sorted(Counter(row.get("first_fire_channel") for row in selected_rows).items())),
        "selected_tier_counts": dict(sorted(Counter(row.get("tier") for row in selected_rows).items())),
        "selected_timing_counts": dict(sorted(Counter(row.get("fire_timing_label") for row in selected_rows).items())),
        "primary_timing_counts": dict(sorted(Counter(row.get("fire_timing_label") for row in primary_rows).items())),
    }
    report = {
        "iteration": 105,
        "inputs": inputs,
        "infra_problems": infra_problems,
        "support_problems": [],
        "event": {"measurements": measurements},
        "summary": summary,
        "verdict": SUPPORT_NULL_VERDICT,
        "claim_boundary": (
            "offline timing-aware candidate-schedule design only; no GPU approval, launch authorization, "
            "actor-causality, actor-match result, repair, threshold-value, transfer, safety, deployment, "
            "robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, "
            "first-responder behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }
    support_problems = [] if infra_problems else policy_problems(report)
    report["support_problems"] = support_problems
    report["verdict"] = choose_verdict(infra_problems, support_problems)
    return report


def build_report(
    iter52_report_path: Path,
    iter54_report_path: Path,
    iter59_report_path: Path,
    iter104_report_path: Path,
) -> dict[str, Any]:
    iter52_report, problems52 = load_report(iter52_report_path, "iter52-report")
    iter54_report, problems54 = load_report(iter54_report_path, "iter54-report")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter104_report, problems104 = load_report(iter104_report_path, "iter104-report")
    return build_report_from_reports(
        iter52_report,
        iter54_report,
        iter59_report,
        iter104_report,
        {
            "iter52_report": str(iter52_report_path),
            "iter54_report": str(iter54_report_path),
            "iter59_report": str(iter59_report_path),
            "iter104_report": str(iter104_report_path),
        },
        problems52 + problems54 + problems59 + problems104,
    )


def build_report_from_data_for_test(
    iter52_report: dict[str, Any],
    iter54_report: dict[str, Any],
    iter59_report: dict[str, Any],
    iter104_report: dict[str, Any],
) -> dict[str, Any]:
    return build_report_from_reports(
        iter52_report,
        iter54_report,
        iter59_report,
        iter104_report,
        {
            "iter52_report": "<test>",
            "iter54_report": "<test>",
            "iter59_report": "<test>",
            "iter104_report": "<test>",
        },
    )


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 105 - HUGSIM timing-aware provenance batch design",
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
    if report["support_problems"]:
        lines.extend(["", "## Support Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["support_problems"])
    lines.extend(
        [
            "",
            "## Selected Future Slots",
            "",
            "| slot | scenario | run | dataset | tier | channel | timing | lead s | brake frames | reason |",
            "|---:|---|---:|---|---|---|---|---:|---:|---|",
        ]
    )
    for row in report["event"]["measurements"].get("selected_rows", []):
        lines.append(
            f"| `{row['slot_index']}` | `{row['scenario']}` | `{row['run']}` | `{row['dataset']}` | "
            f"`{row['tier']}` | `{row['first_fire_channel']}` | `{row['fire_timing_label']}` | "
            f"`{row['first_fire_lead_time']}` | `{row['brake_frames']}` | `{row['selection_reason']}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter52_report: Path,
    iter54_report: Path,
    iter59_report: Path,
    iter104_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter52_report, iter54_report, iter59_report, iter104_report)
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
        "--out",
        type=Path,
        default=Path(
            "experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/"
            "timing_aware_provenance_batch_design_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/"
            "timing_aware_provenance_batch_design.md"
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
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
