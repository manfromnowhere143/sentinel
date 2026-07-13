#!/usr/bin/env python3
"""Iteration 79 HUGSIM selected-object surface decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER75_VERDICT = "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
ITER77_VERDICT = "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE"
ITER78_VERDICT = "HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE"
FIXED_EVENTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "event_ts": 5.0,
        "selected_object_id": 5,
        "support_object_id": 9,
        "support_band": "ambiguous",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "event_ts": 2.5,
        "selected_object_id": 6,
        "support_object_id": 10,
        "support_band": "match",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "event_ts": 5.0,
        "selected_object_id": 24,
        "support_object_id": 10,
        "support_band": "match",
    },
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


ITER78 = _load_module(
    "experiments/iter78_hugsim_support_object_ranking/analyze_support_object_ranking.py",
    "iter78_support_object_ranking",
)
SWITCH = ITER78.SWITCH
ITER62 = ITER78.ITER62
surface_margin = ITER78.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def event_index(rows: Any, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append("iter78-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("iter78-event-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        role = row.get("event_role")
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(role, str):
            problems.append(f"iter78-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, role)
        if key in index:
            problems.append(f"duplicate-iter78-event:{key}")
        index[key] = row
    return index


def selected_object_id(row75: dict[str, Any], role: str, problems: list[str]) -> Any:
    event_objects = row75.get(f"{role}_objects")
    if not isinstance(event_objects, dict) or not isinstance(event_objects.get("object_ids"), list):
        problems.append(f"{role}-selected-objects-missing")
        return None
    object_ids = event_objects["object_ids"]
    if len(object_ids) != 1:
        problems.append(f"{role}-selected-object-count:{object_ids}")
        return None
    return object_ids[0]


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter75_report: dict[str, Any],
    iter77_report: dict[str, Any],
    iter78_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter75": (iter75_report, ITER75_VERDICT),
        "iter77": (iter77_report, ITER77_VERDICT),
        "iter78": (iter78_report, ITER78_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter75_index = surface_margin.index_rows(iter75_report.get("episodes"), "iter75", problems)
    iter77_index = surface_margin.index_rows(iter77_report.get("episodes"), "iter77", problems)
    iter78_index = event_index(iter78_report.get("events"), problems)
    if len(iter78_index) != len(FIXED_EVENTS):
        problems.append(f"iter78-event-count-mismatch:{len(iter78_index)}")

    selected: list[dict[str, Any]] = []
    for event in FIXED_EVENTS:
        row_key = (event["audit_id"], event["scenario"])
        event_key = (event["audit_id"], event["scenario"], event["role"])
        row59 = iter59_index.get(row_key)
        row75 = iter75_index.get(row_key)
        row77 = iter77_index.get(row_key)
        row78 = iter78_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row75 is None:
            problems.append(f"missing-iter75-row:{row_key}")
            continue
        if row77 is None:
            problems.append(f"missing-iter77-row:{row_key}")
            continue
        if row78 is None:
            problems.append(f"missing-iter78-event:{event_key}")
            continue

        selected_id = selected_object_id(row75, str(event["role"]), problems)
        if not same_object_id(selected_id, event["selected_object_id"]):
            problems.append(f"iter75-selected-object-mismatch:{event_key}:{selected_id}")
        if row78.get("row_label") != "support_object_nonselected_subthreshold":
            problems.append(f"iter78-row-label-mismatch:{event_key}:{row78.get('row_label')}")
        if row78.get("problems"):
            problems.append(f"iter78-event-problems:{event_key}:{row78.get('problems')}")
        if not same_object_id(row78.get("selected_object_id"), event["selected_object_id"]):
            problems.append(f"iter78-selected-object-mismatch:{event_key}:{row78.get('selected_object_id')}")
        if not same_object_id(row78.get("support_object_id"), event["support_object_id"]):
            problems.append(f"iter78-support-object-mismatch:{event_key}:{row78.get('support_object_id')}")
        if row78.get("support_band") != event["support_band"]:
            problems.append(f"iter78-support-band-mismatch:{event_key}:{row78.get('support_band')}")
        event_ts = surface_margin.number(row78.get("event_ts"), "iter78.event_ts", problems)
        if event_ts is not None and not math.isclose(event_ts, float(event["event_ts"]), abs_tol=1e-6):
            problems.append(f"iter78-event-ts-mismatch:{event_key}:{event_ts}")

        event_set = row77.get(f"{event['role']}_event_set")
        if not isinstance(event_set, dict):
            problems.append(f"iter77-event-set-missing:{event_key}")
        else:
            best = event_set.get("best_variant")
            if not isinstance(best, dict):
                problems.append(f"iter77-best-variant-missing:{event_key}")
            elif not same_object_id(best.get("object_id"), event["support_object_id"]):
                problems.append(f"iter77-support-object-mismatch:{event_key}:{best.get('object_id')}")
            if event_set.get("distance_band") != event["support_band"]:
                problems.append(f"iter77-support-band-mismatch:{event_key}:{event_set.get('distance_band')}")

        selected.append({"event": event, "iter59": row59, "iter75": row75, "iter78": row78})
    if len(selected) != len(FIXED_EVENTS):
        problems.append(f"fixed-event-count-mismatch:{len(selected)}")
    return selected, problems


def metric_for_object(object_metrics: list[dict[str, Any]], object_id: Any, label: str, problems: list[str]) -> dict[str, Any] | None:
    matches = [row for row in object_metrics if same_object_id(row.get("object_id"), object_id)]
    if len(matches) != 1:
        problems.append(f"{label}-object-count-{len(matches)}:{object_id}")
        return None
    return matches[0]


def augment_metric(
    metric: dict[str, Any] | None,
    cpa_margin: float | None,
    ttc_thresh: float | None,
) -> tuple[dict[str, Any] | None, str | None]:
    if metric is None or cpa_margin is None or ttc_thresh is None:
        return metric, None
    min_cpa = metric.get("min_cpa")
    ttc = metric.get("ttc")
    cpa_active = isinstance(min_cpa, (int, float)) and not isinstance(min_cpa, bool) and min_cpa <= cpa_margin
    ttc_active = (
        isinstance(ttc, (int, float))
        and not isinstance(ttc, bool)
        and math.isfinite(ttc)
        and ttc <= ttc_thresh
    )
    cpa_borderline = (
        isinstance(min_cpa, (int, float))
        and not isinstance(min_cpa, bool)
        and not cpa_active
        and min_cpa <= ITER78.CPA_BORDERLINE_M
    )
    ttc_borderline = (
        isinstance(ttc, (int, float))
        and not isinstance(ttc, bool)
        and math.isfinite(ttc)
        and not ttc_active
        and ttc <= ITER78.TTC_BORDERLINE_S
    )
    augmented = metric | {
        "cpa_active_logged_threshold": cpa_active,
        "ttc_active_logged_threshold": ttc_active,
        "cpa_borderline_registered": cpa_borderline,
        "ttc_borderline_registered": ttc_borderline,
    }
    if cpa_active or ttc_active:
        return augmented, "active"
    if cpa_borderline or ttc_borderline:
        return augmented, "borderline"
    return augmented, "subthreshold"


def classify(selected_state: str | None, support_state: str | None, problems: list[str]) -> str:
    if problems:
        return "selected_surface_decomposition_insufficient"
    if selected_state == "active" and support_state == "subthreshold":
        return "selected_active_support_subthreshold"
    if selected_state == "borderline" and support_state == "subthreshold":
        return "selected_borderline_support_subthreshold"
    if selected_state == "subthreshold" and support_state == "subthreshold":
        return "selected_subthreshold_support_subthreshold"
    if selected_state is not None and support_state is not None:
        return "selected_support_surface_mixed"
    return "selected_surface_decomposition_insufficient"


def analyze_event(item: dict[str, Any]) -> dict[str, Any]:
    event = item["event"]
    row59 = item["iter59"]
    row78 = item["iter78"]
    role = str(event["role"])
    problems: list[str] = []
    event_ts = surface_margin.number(row78.get("event_ts"), "event_ts", problems)
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        rows: list[dict[str, Any]] = []
    else:
        rows, row_problems = SWITCH.load_decision_rows(Path(episode_dir) / "sentinel_iter48_decisions.jsonl")
        problems.extend(row_problems)
    event_row = SWITCH.find_decision_row(rows, event_ts, role, problems) if event_ts is not None else None
    object_metrics: list[dict[str, Any]] = []
    selected_metric: dict[str, Any] | None = None
    support_metric: dict[str, Any] | None = None
    selected_state: str | None = None
    support_state: str | None = None
    if event_row is not None:
        cpa_margin, ttc_thresh = ITER78.channel_thresholds(event_row, problems)
        try:
            object_metrics = ITER62.object_metrics(event_row)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"object-metrics-failed:{exc}")
        selected_metric = metric_for_object(object_metrics, event["selected_object_id"], "selected", problems)
        support_metric = metric_for_object(object_metrics, event["support_object_id"], "support", problems)
        selected_metric, selected_state = augment_metric(selected_metric, cpa_margin, ttc_thresh)
        support_metric, support_state = augment_metric(support_metric, cpa_margin, ttc_thresh)
    row_label = classify(selected_state, support_state, problems)
    return {
        "audit_id": event["audit_id"],
        "scenario": event["scenario"],
        "event_role": role,
        "event_ts": event_ts,
        "selected_object_id": event["selected_object_id"],
        "support_object_id": event["support_object_id"],
        "support_band": event["support_band"],
        "object_count": len(object_metrics),
        "selected_metric": selected_metric,
        "support_metric": support_metric,
        "selected_state": selected_state,
        "support_state": support_state,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_EVENTS)
        or any(row.get("problems") for row in rows)
        or "selected_surface_decomposition_insufficient" in labels
    ):
        return "HUGSIM_SELECTED_SURFACE_DECOMPOSITION_BLOCKED"
    if "selected_active_support_subthreshold" in labels:
        return "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"
    if "selected_borderline_support_subthreshold" in labels:
        return "HUGSIM_SELECTED_BORDERLINE_SUPPORT_SUBTHRESHOLD_COMPLETE"
    if all(label == "selected_subthreshold_support_subthreshold" for label in labels):
        return "HUGSIM_SELECTED_AND_SUPPORT_SUBTHRESHOLD_COMPLETE"
    return "HUGSIM_SELECTED_SURFACE_DECOMPOSITION_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter75_report_path: Path,
    iter77_report_path: Path,
    iter78_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter75_report, problems75 = surface_margin.load_report(iter75_report_path, "iter75-report")
    iter77_report, problems77 = surface_margin.load_report(iter77_report_path, "iter77-report")
    iter78_report, problems78 = surface_margin.load_report(iter78_report_path, "iter78-report")
    infra_problems.extend(problems59 + problems75 + problems77 + problems78)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(
            iter59_report,
            iter75_report,
            iter77_report,
            iter78_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_event(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 79,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter75_report": str(iter75_report_path),
            "iter77_report": str(iter77_report_path),
            "iter78_report": str(iter78_report_path),
        },
        "fixed_events": list(FIXED_EVENTS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_events": len(selected),
            "evaluated_events": sum(not row.get("problems") for row in rows),
            "event_label_counts": dict(sorted(label_counts.items())),
            "selected_active_events": sum(
                row.get("row_label") == "selected_active_support_subthreshold" for row in rows
            ),
            "selected_borderline_events": sum(
                row.get("row_label") == "selected_borderline_support_subthreshold" for row in rows
            ),
            "selected_subthreshold_events": sum(
                row.get("row_label") == "selected_subthreshold_support_subthreshold" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-event descriptive selected-vs-support surface audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population, HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 79 - HUGSIM selected-object surface decomposition",
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
        "## Events",
        "",
        "| audit id | event | selected id | selected state | selected cpa rank | selected min cpa | selected ttc | support id | support state | support cpa rank | support min cpa | support ttc | label | problems |",
        "|---|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---|---|",
    ])
    for row in report["events"]:
        selected_metric = row.get("selected_metric") or {}
        support_metric = row.get("support_metric") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['selected_object_id']}` | "
            f"`{row.get('selected_state')}` | `{selected_metric.get('cpa_rank')}` | "
            f"`{selected_metric.get('min_cpa')}` | `{selected_metric.get('ttc')}` | "
            f"`{row['support_object_id']}` | `{row.get('support_state')}` | "
            f"`{support_metric.get('cpa_rank')}` | `{support_metric.get('min_cpa')}` | "
            f"`{support_metric.get('ttc')}` | `{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter75_report: Path,
    iter77_report: Path,
    iter78_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(
        iter59_report,
        iter75_report,
        iter77_report,
        iter78_report,
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
        "--iter75-report",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff_report.json"),
    )
    parser.add_argument(
        "--iter77-report",
        type=Path,
        default=Path("experiments/iter77_hugsim_event_object_set_bridge/proof-set/set_report.json"),
    )
    parser.add_argument(
        "--iter78-report",
        type=Path,
        default=Path("experiments/iter78_hugsim_support_object_ranking/proof-ranking/ranking_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter79_hugsim_selected_surface_decomposition/proof-selected/selected_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter79_hugsim_selected_surface_decomposition/proof-selected/selected.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter75_report,
        args.iter77_report,
        args.iter78_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
