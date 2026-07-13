#!/usr/bin/env python3
"""Iteration 84 HUGSIM selected/support path-arbitration decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER79_VERDICT = "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"
ITER80_VERDICT = "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE"
ITER83_VERDICT = "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE"
SUPPORTED_BANDS = {"match", "ambiguous"}
FIXED_EVENTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "event_ts": 5.0,
        "selected_object_id": 5,
        "support_object_id": 9,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "event_ts": 2.5,
        "selected_object_id": 6,
        "support_object_id": 10,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "event_ts": 5.0,
        "selected_object_id": 24,
        "support_object_id": 10,
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


ITER80 = _load_module(
    "experiments/iter80_hugsim_selected_all_provenance_bridge/"
    "analyze_selected_all_provenance_bridge.py",
    "iter80_selected_all_provenance",
)
ITER83 = _load_module(
    "experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/"
    "analyze_bridge_supported_surface_miss.py",
    "iter83_surface_miss",
)
SWITCH = ITER80.SWITCH
surface_margin = ITER80.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-event-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        role = row.get("event_role")
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(role, str):
            problems.append(f"{label}-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, role)
        if key in index:
            problems.append(f"duplicate-{label}-event:{key}")
        index[key] = row
    return index


def object_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-objects-not-list")
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-object-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        if not isinstance(audit_id, str) or not isinstance(scenario, str):
            problems.append(f"{label}-object-key-missing:{row}")
            continue
        key = (audit_id, scenario)
        if key in index:
            problems.append(f"duplicate-{label}-object:{key}")
        index[key] = row
    return index


def compact_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    if metric is None:
        return None
    keys = (
        "object_id",
        "state",
        "min_cpa",
        "ttc",
        "cpa_rank",
        "ttc_rank",
        "active_cpa_margin_m",
        "active_ttc_margin_s",
        "borderline_cpa_margin_m",
        "borderline_ttc_margin_s",
        "cpa_active_logged_threshold",
        "ttc_active_logged_threshold",
        "cpa_borderline_registered",
        "ttc_borderline_registered",
        "gap",
        "closing",
        "score",
    )
    return {key: metric.get(key) for key in keys}


def compact_bridge(bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "distance_band": bridge.get("distance_band"),
        "best_distance_m": bridge.get("best_distance_m"),
        "evaluated_variant_count": bridge.get("evaluated_variant_count"),
        "provenance_count": bridge.get("provenance_count"),
        "provenance_type_counts": bridge.get("provenance_type_counts"),
        "best_variant": bridge.get("best_variant"),
    }


def object_bridge(
    event_row: dict[str, Any],
    event_ts: float,
    obj: dict[str, Any],
    role: str,
    provenance_rows: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    variants: list[dict[str, Any]] = []
    for idx, provenance in enumerate(provenance_rows):
        try:
            for variant in SWITCH.bridge_variants(event_row, event_ts, obj, role, provenance):
                variants.append(
                    variant
                    | {
                        "collision_type": provenance.get("collision_type"),
                        "provenance_index": idx,
                    }
                )
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{role}-bridge-failed:{obj.get('id')}:{exc}")
    best = SWITCH.best_variant(variants)
    distance = best["distance_m"] if best is not None else None
    type_counts = Counter(str(row.get("collision_type")) for row in provenance_rows)
    return {
        "role": role,
        "object_id": obj.get("id"),
        "event_ts": event_ts,
        "provenance_count": len(provenance_rows),
        "provenance_type_counts": dict(sorted(type_counts.items())),
        "evaluated_variant_count": len(variants),
        "best_variant": ITER80.compact_variant(best),
        "best_distance_m": distance,
        "distance_band": SWITCH.distance_band(distance),
    }


def rank_better(left: Any, right: Any) -> bool:
    return finite_number(left) and finite_number(right) and float(left) < float(right)


def hazard_advantages(selected_metric: dict[str, Any], support_metric: dict[str, Any]) -> dict[str, bool]:
    selected_ttc = selected_metric.get("ttc")
    support_ttc = support_metric.get("ttc")
    return {
        "selected_lower_cpa": rank_better(selected_metric.get("min_cpa"), support_metric.get("min_cpa")),
        "selected_better_cpa_rank": rank_better(selected_metric.get("cpa_rank"), support_metric.get("cpa_rank")),
        "selected_finite_ttc_support_missing": finite_number(selected_ttc) and not finite_number(support_ttc),
        "selected_lower_ttc": rank_better(selected_ttc, support_ttc),
        "selected_better_ttc_rank": rank_better(selected_metric.get("ttc_rank"), support_metric.get("ttc_rank")),
    }


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def bridge_rank(bridge: dict[str, Any]) -> int:
    return {"missing": -1, "no_support": 0, "ambiguous": 1, "match": 2}.get(str(bridge.get("distance_band")), -1)


def classify_row(
    selected_state: str | None,
    support_state: str | None,
    selected_bridge: dict[str, Any],
    support_bridge: dict[str, Any],
    advantages: dict[str, bool],
    problems: list[str],
) -> str:
    if problems:
        return "selected_support_arbitration_insufficient"
    selected_supported = bridge_supported(selected_bridge)
    support_supported = bridge_supported(support_bridge)
    if selected_supported and support_supported:
        return "selected_and_support_both_bridge_supported"
    if selected_state == "subthreshold" or support_state in {"active", "borderline"}:
        return "support_surface_or_selected_subthreshold"
    if selected_state in {"active", "borderline"} and support_state == "subthreshold" and support_supported:
        if not selected_supported and any(advantages.values()):
            return "selected_surface_support_bridge_split"
        if not selected_supported:
            return "selected_surface_support_bridge_no_hazard_advantage"
    return "selected_support_arbitration_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter79_report: dict[str, Any],
    iter80_report: dict[str, Any],
    iter83_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter79": (iter79_report, ITER79_VERDICT),
        "iter80": (iter80_report, ITER80_VERDICT),
        "iter83": (iter83_report, ITER83_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter79_index = event_index(iter79_report.get("events"), "iter79", problems)
    iter80_index = event_index(iter80_report.get("events"), "iter80", problems)
    iter83_index = object_index(iter83_report.get("objects"), "iter83", problems)
    if len(iter79_index) != len(FIXED_EVENTS):
        problems.append(f"iter79-event-count-mismatch:{len(iter79_index)}")
    if len(iter80_index) != len(FIXED_EVENTS):
        problems.append(f"iter80-event-count-mismatch:{len(iter80_index)}")
    if len(iter83_index) != 2:
        problems.append(f"iter83-object-count-mismatch:{len(iter83_index)}")

    selected: list[dict[str, Any]] = []
    for event in FIXED_EVENTS:
        row_key = (event["audit_id"], event["scenario"])
        event_key = (event["audit_id"], event["scenario"], event["role"])
        row59 = iter59_index.get(row_key)
        row79 = iter79_index.get(event_key)
        row80 = iter80_index.get(event_key)
        row83 = iter83_index.get(row_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row79 is None:
            problems.append(f"missing-iter79-event:{event_key}")
            continue
        if row80 is None:
            problems.append(f"missing-iter80-event:{event_key}")
            continue
        if row83 is None:
            problems.append(f"missing-iter83-object:{row_key}")
            continue

        if row79.get("problems"):
            problems.append(f"iter79-event-problems:{event_key}:{row79.get('problems')}")
        if row80.get("problems"):
            problems.append(f"iter80-event-problems:{event_key}:{row80.get('problems')}")
        if row83.get("problems"):
            problems.append(f"iter83-object-problems:{row_key}:{row83.get('problems')}")
        if row79.get("selected_state") not in {"active", "borderline"}:
            problems.append(f"iter79-selected-state-not-surface:{event_key}:{row79.get('selected_state')}")
        if row79.get("support_state") != "subthreshold":
            problems.append(f"iter79-support-state-not-subthreshold:{event_key}:{row79.get('support_state')}")
        if row80.get("row_label") != "selected_all_provenance_no_support":
            problems.append(f"iter80-selected-provenance-label-mismatch:{event_key}:{row80.get('row_label')}")
        for row_label, row in (("iter79", row79), ("iter80", row80)):
            if not same_object_id(row.get("selected_object_id"), event["selected_object_id"]):
                problems.append(f"{row_label}-selected-object-mismatch:{event_key}:{row.get('selected_object_id')}")
            if not same_object_id(row.get("support_object_id"), event["support_object_id"]):
                problems.append(f"{row_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}")
            event_ts = surface_margin.number(row.get("event_ts"), f"{row_label}.event_ts", problems)
            if event_ts is not None and not math.isclose(event_ts, float(event["event_ts"]), abs_tol=1e-6):
                problems.append(f"{row_label}-event-ts-mismatch:{event_key}:{event_ts}")
        if not same_object_id(row83.get("support_object_id"), event["support_object_id"]):
            problems.append(f"iter83-support-object-mismatch:{row_key}:{row83.get('support_object_id')}")
        selected.append({"event": event, "iter59": row59, "iter79": row79, "iter80": row80, "iter83": row83})
    if len(selected) != len(FIXED_EVENTS):
        problems.append(f"fixed-event-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_event(item: dict[str, Any]) -> dict[str, Any]:
    event = item["event"]
    row59 = item["iter59"]
    role = str(event["role"])
    problems: list[str] = []
    event_ts = surface_margin.number(event.get("event_ts"), "event.event_ts", problems)
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
        provenance_rows: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        provenance_rows = ITER80.load_all_provenance(ep_dir / "eval.json", problems)
        problems.extend(row_problems)

    event_row = SWITCH.find_decision_row(decision_rows, event_ts, role, problems) if event_ts is not None else None
    selected_metric: dict[str, Any] | None = None
    support_metric: dict[str, Any] | None = None
    selected_bridge: dict[str, Any] = {"distance_band": "missing"}
    support_bridge: dict[str, Any] = {"distance_band": "missing"}
    advantages: dict[str, bool] = {}
    selected_state: str | None = None
    support_state: str | None = None
    if event_row is not None and event_ts is not None:
        selected_metric = ITER83.metric_with_margins(event_row, event["selected_object_id"], problems)
        support_metric = ITER83.metric_with_margins(event_row, event["support_object_id"], problems)
        selected_obj = SWITCH.select_object(event_row, event["selected_object_id"], "selected", problems)
        support_obj = SWITCH.select_object(event_row, event["support_object_id"], "support", problems)
        if selected_metric is not None:
            selected_state = selected_metric.get("state")
        if support_metric is not None:
            support_state = support_metric.get("state")
        if selected_obj is not None:
            selected_bridge = object_bridge(event_row, event_ts, selected_obj, "selected", provenance_rows, problems)
        if support_obj is not None:
            support_bridge = object_bridge(event_row, event_ts, support_obj, "support", provenance_rows, problems)
        if selected_metric is not None and support_metric is not None:
            advantages = hazard_advantages(selected_metric, support_metric)

    support_better_bridge = bridge_rank(support_bridge) > bridge_rank(selected_bridge)
    row_label = classify_row(selected_state, support_state, selected_bridge, support_bridge, advantages, problems)
    return {
        "audit_id": event["audit_id"],
        "scenario": event["scenario"],
        "event_role": role,
        "event_ts": event_ts,
        "selected_object_id": event["selected_object_id"],
        "support_object_id": event["support_object_id"],
        "selected_state": selected_state,
        "support_state": support_state,
        "selected_metric": compact_metric(selected_metric),
        "support_metric": compact_metric(support_metric),
        "selected_bridge": compact_bridge(selected_bridge),
        "support_bridge": compact_bridge(support_bridge),
        "hazard_advantages": advantages,
        "support_better_bridge": support_better_bridge,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_EVENTS)
        or any(row.get("problems") for row in rows)
        or "selected_support_arbitration_insufficient" in labels
    ):
        return "HUGSIM_SELECTED_SUPPORT_ARBITRATION_BLOCKED"
    if all(label == "selected_surface_support_bridge_split" for label in labels):
        return "HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE"
    if (
        "selected_surface_support_bridge_no_hazard_advantage" in labels
        and "selected_surface_support_bridge_split" not in labels
    ):
        return "HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_NO_ADVANTAGE_COMPLETE"
    return "HUGSIM_SELECTED_SUPPORT_ARBITRATION_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter79_report_path: Path,
    iter80_report_path: Path,
    iter83_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter79_report, problems79 = surface_margin.load_report(iter79_report_path, "iter79-report")
    iter80_report, problems80 = surface_margin.load_report(iter80_report_path, "iter80-report")
    iter83_report, problems83 = surface_margin.load_report(iter83_report_path, "iter83-report")
    infra_problems.extend(problems59 + problems79 + problems80 + problems83)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter79_report, iter80_report, iter83_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_event(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    advantage_counts: Counter[str] = Counter()
    for row in rows:
        for key, value in (row.get("hazard_advantages") or {}).items():
            if value:
                advantage_counts[key] += 1
    return {
        "iteration": 84,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter79_report": str(iter79_report_path),
            "iter80_report": str(iter80_report_path),
            "iter83_report": str(iter83_report_path),
        },
        "fixed_events": list(FIXED_EVENTS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_events": len(selected),
            "evaluated_events": sum(not row.get("problems") for row in rows),
            "event_label_counts": dict(sorted(label_counts.items())),
            "support_better_bridge_events": sum(bool(row.get("support_better_bridge")) for row in rows),
            "selected_bridge_supported_events": sum(bridge_supported(row.get("selected_bridge") or {}) for row in rows),
            "support_bridge_supported_events": sum(bridge_supported(row.get("support_bridge") or {}) for row in rows),
            "hazard_advantage_counts": dict(sorted(advantage_counts.items())),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive selected/support arbitration decomposition only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 84 - HUGSIM selected/support path-arbitration decomposition",
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
        "| audit id | event | selected id | selected state | selected cpa | selected ttc | selected bridge | support id | support state | support cpa | support ttc | support bridge | advantages | label | problems |",
        "|---|---|---:|---|---:|---:|---|---:|---|---:|---:|---|---|---|---|",
    ])
    for row in report["events"]:
        selected_metric = row.get("selected_metric") or {}
        support_metric = row.get("support_metric") or {}
        selected_bridge = row.get("selected_bridge") or {}
        support_bridge = row.get("support_bridge") or {}
        advantages = [key for key, value in (row.get("hazard_advantages") or {}).items() if value]
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['selected_object_id']}` | "
            f"`{row.get('selected_state')}` | `{selected_metric.get('min_cpa')}` | "
            f"`{selected_metric.get('ttc')}` | `{selected_bridge.get('distance_band')}` | "
            f"`{row['support_object_id']}` | `{row.get('support_state')}` | "
            f"`{support_metric.get('min_cpa')}` | `{support_metric.get('ttc')}` | "
            f"`{support_bridge.get('distance_band')}` | `{advantages}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter79_report: Path,
    iter80_report: Path,
    iter83_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter79_report, iter80_report, iter83_report)
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
        "--iter79-report",
        type=Path,
        default=Path("experiments/iter79_hugsim_selected_surface_decomposition/proof-selected/selected_report.json"),
    )
    parser.add_argument(
        "--iter80-report",
        type=Path,
        default=Path(
            "experiments/iter80_hugsim_selected_all_provenance_bridge/proof-all-provenance/"
            "all_provenance_report.json"
        ),
    )
    parser.add_argument(
        "--iter83-report",
        type=Path,
        default=Path(
            "experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/"
            "surface_miss_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter84_hugsim_selected_support_arbitration/proof-arbitration/"
            "arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter84_hugsim_selected_support_arbitration/proof-arbitration/"
            "arbitration.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter79_report,
        args.iter80_report,
        args.iter83_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
