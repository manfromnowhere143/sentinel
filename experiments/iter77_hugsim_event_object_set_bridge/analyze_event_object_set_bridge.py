#!/usr/bin/env python3
"""Iteration 77 HUGSIM event object-set foreground bridge audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER72_VERDICT = "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"
ITER73_VERDICT = "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"
ITER74_VERDICT = "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE"
ITER75_VERDICT = "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
ITER76_VERDICT = "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE"
FIXED_ROWS = (
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
)


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SWITCH = _load_module(
    "experiments/iter76_hugsim_switch_foreground_bridge/analyze_switch_foreground_bridge.py",
    "iter76_switch_foreground_bridge",
)
surface_margin = SWITCH.surface_margin


def event_set_bridge(
    event_row: dict[str, Any],
    event_ts: float,
    role: str,
    foregrounds: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    objs = event_row.get("objs")
    if not isinstance(objs, list):
        problems.append(f"{role}-objs-not-list")
        objs = []
    objects = [obj for obj in objs if isinstance(obj, dict) and "id" in obj]
    if not objects:
        problems.append(f"{role}-object-set-empty")
    variants: list[dict[str, Any]] = []
    for obj in objects:
        try:
            for foreground in foregrounds:
                variants.extend(SWITCH.bridge_variants(event_row, event_ts, obj, role, foreground))
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{role}-object-{obj.get('id')}-bridge-failed:{exc}")
    best = SWITCH.best_variant(variants)
    distance = best["distance_m"] if best is not None else None
    return {
        "role": role,
        "event_ts": event_ts,
        "object_count": len(objects),
        "object_ids": [obj.get("id") for obj in objects],
        "evaluated_variant_count": len(variants),
        "best_variant": SWITCH.compact_variant(best),
        "best_distance_m": distance,
        "distance_band": SWITCH.distance_band(distance),
    }


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter72_report: dict[str, Any],
    iter73_report: dict[str, Any],
    iter74_report: dict[str, Any],
    iter75_report: dict[str, Any],
    iter76_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
        "iter73": (iter73_report, ITER73_VERDICT),
        "iter74": (iter74_report, ITER74_VERDICT),
        "iter75": (iter75_report, ITER75_VERDICT),
        "iter76": (iter76_report, ITER76_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = surface_margin.index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter72_index = surface_margin.index_rows(iter72_report.get("episodes"), "iter72", problems)
    iter73_index = surface_margin.index_rows(iter73_report.get("episodes"), "iter73", problems)
    iter74_index = surface_margin.index_rows(iter74_report.get("episodes"), "iter74", problems)
    iter75_index = surface_margin.index_rows(iter75_report.get("episodes"), "iter75", problems)
    iter76_index = surface_margin.index_rows(iter76_report.get("episodes"), "iter76", problems)

    selected: list[dict[str, Any]] = []
    for key in FIXED_ROWS:
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        row72 = iter72_index.get(key)
        row73 = iter73_index.get(key)
        row74 = iter74_index.get(key)
        row75 = iter75_index.get(key)
        row76 = iter76_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None or row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-late-fire-missing:{key}")
        if row72 is None or row72.get("row_label") not in {
            "late_fire_prefire_near_ttc_margin",
            "late_fire_prefire_near_cpa_margin",
        }:
            problems.append(f"iter72-near-row-missing:{key}")
        if row73 is None or row73.get("row_label") != "late_prefire_near_postcontact_active":
            problems.append(f"iter73-late-transition-missing:{key}")
        if row74 is None or row74.get("row_label") != "cross_channel_late_activation":
            problems.append(f"iter74-cross-channel-row-missing:{key}")
        if row75 is None or row75.get("row_label") != "object_switch_cross_channel_handoff":
            problems.append(f"iter75-object-switch-row-missing:{key}")
        if row76 is None or row76.get("row_label") != "no_foreground_bridge_support":
            problems.append(f"iter76-no-support-row-missing:{key}")
            continue
        selected.append({"iter59": row59, "iter75": row75, "iter76": row76})

    actual = [SWITCH.row_identity(item["iter59"]) for item in selected]
    if actual != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual}")
    return selected, problems


def classify(pre_band: str, active_band: str, problems: list[str]) -> str:
    if problems or pre_band == "missing" or active_band == "missing":
        return "event_object_set_bridge_insufficient"
    if pre_band == "match" and active_band == "match":
        return "both_sets_foreground_match"
    if active_band == "match":
        return "active_set_foreground_match"
    if pre_band == "match":
        return "pre_set_foreground_match"
    if pre_band == "ambiguous" and active_band == "ambiguous":
        return "both_sets_foreground_ambiguous"
    if active_band == "ambiguous" and pre_band == "no_support":
        return "active_set_foreground_ambiguous"
    if pre_band == "ambiguous" and active_band == "no_support":
        return "pre_set_foreground_ambiguous"
    if pre_band == "no_support" and active_band == "no_support":
        return "event_object_sets_no_foreground_support"
    return "event_object_set_bridge_insufficient"


def analyze_row(item: dict[str, Any]) -> dict[str, Any]:
    row59 = item["iter59"]
    row75 = item["iter75"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        rows: list[dict[str, Any]] = []
        foregrounds: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        foregrounds, foreground_problems = SWITCH.load_foregrounds(ep_dir / "eval.json")
        problems.extend(row_problems + foreground_problems)
    pre_ts = surface_margin.number(row75.get("pre_ts"), "pre_ts", problems)
    active_ts = surface_margin.number(row75.get("active_ts"), "active_ts", problems)
    pre_row = SWITCH.find_decision_row(rows, pre_ts, "pre", problems) if pre_ts is not None else None
    active_row = SWITCH.find_decision_row(rows, active_ts, "active", problems) if active_ts is not None else None
    pre_event: dict[str, Any] = {}
    active_event: dict[str, Any] = {}
    if pre_row is not None and pre_ts is not None:
        pre_event = event_set_bridge(pre_row, pre_ts, "pre", foregrounds, problems)
    if active_row is not None and active_ts is not None:
        active_event = event_set_bridge(active_row, active_ts, "active", foregrounds, problems)
    pre_band = str(pre_event.get("distance_band", "missing"))
    active_band = str(active_event.get("distance_band", "missing"))
    row_label = classify(pre_band, active_band, problems)
    pre_distance = pre_event.get("best_distance_m")
    active_distance = active_event.get("best_distance_m")
    distance_delta = None
    if isinstance(pre_distance, (int, float)) and isinstance(active_distance, (int, float)):
        distance_delta = float(active_distance) - float(pre_distance)
    return {
        "audit_id": row59.get("audit_id"),
        "scenario": row59.get("scenario"),
        "foreground_count": len(foregrounds),
        "pre_event_set": pre_event,
        "active_event_set": active_event,
        "active_minus_pre_distance_m": distance_delta,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "event_object_set_bridge_insufficient" in labels
    ):
        return "HUGSIM_EVENT_SET_FOREGROUND_BRIDGE_BLOCKED"
    if "active_set_foreground_match" in labels:
        return "HUGSIM_EVENT_SET_FOREGROUND_ACTIVE_MATCH_COMPLETE"
    if "pre_set_foreground_match" in labels:
        return "HUGSIM_EVENT_SET_FOREGROUND_PRE_MATCH_COMPLETE"
    return "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter72_report_path: Path,
    iter73_report_path: Path,
    iter74_report_path: Path,
    iter75_report_path: Path,
    iter76_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    iter73_report, problems73 = surface_margin.load_report(iter73_report_path, "iter73-report")
    iter74_report, problems74 = surface_margin.load_report(iter74_report_path, "iter74-report")
    iter75_report, problems75 = surface_margin.load_report(iter75_report_path, "iter75-report")
    iter76_report, problems76 = surface_margin.load_report(iter76_report_path, "iter76-report")
    infra_problems.extend(
        problems59 + problems70 + problems72 + problems73 + problems74 + problems75 + problems76
    )
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter72_report,
            iter73_report,
            iter74_report,
            iter75_report,
            iter76_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 77,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter72_report": str(iter72_report_path),
            "iter73_report": str(iter73_report_path),
            "iter74_report": str(iter74_report_path),
            "iter75_report": str(iter75_report_path),
            "iter76_report": str(iter76_report_path),
        },
        "fixed_rows": [{"audit_id": audit_id, "scenario": scenario} for audit_id, scenario in FIXED_ROWS],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "active_set_match_rows": sum(row.get("row_label") == "active_set_foreground_match" for row in rows),
            "pre_set_match_rows": sum(row.get("row_label") == "pre_set_foreground_match" for row in rows),
            "no_support_rows": sum(
                row.get("row_label") == "event_object_sets_no_foreground_support" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive event-object-set foreground-bridge audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 77 - HUGSIM event object-set foreground bridge audit",
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
        "## Rows",
        "",
        "| audit id | scenario | label | pre best object | pre distance | active best object | active distance | delta active-pre | problems |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        pre = row.get("pre_event_set", {})
        active = row.get("active_event_set", {})
        pre_best = pre.get("best_variant") or {}
        active_best = active.get("best_variant") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{pre_best.get('object_id')}` | `{pre.get('best_distance_m')}` | "
            f"`{active_best.get('object_id')}` | `{active.get('best_distance_m')}` | "
            f"`{row.get('active_minus_pre_distance_m')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter70_report: Path,
    iter72_report: Path,
    iter73_report: Path,
    iter74_report: Path,
    iter75_report: Path,
    iter76_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(
        iter59_report,
        iter70_report,
        iter72_report,
        iter73_report,
        iter74_report,
        iter75_report,
        iter76_report,
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
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--iter72-report",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire_report.json"),
    )
    parser.add_argument(
        "--iter73-report",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json"),
    )
    parser.add_argument(
        "--iter74-report",
        type=Path,
        default=Path("experiments/iter74_hugsim_late_fire_delay_barrier/proof-delay/delay_report.json"),
    )
    parser.add_argument(
        "--iter75-report",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff_report.json"),
    )
    parser.add_argument(
        "--iter76-report",
        type=Path,
        default=Path("experiments/iter76_hugsim_switch_foreground_bridge/proof-bridge/bridge_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter77_hugsim_event_object_set_bridge/proof-set/set_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter77_hugsim_event_object_set_bridge/proof-set/set.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter70_report,
        args.iter72_report,
        args.iter73_report,
        args.iter74_report,
        args.iter75_report,
        args.iter76_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
