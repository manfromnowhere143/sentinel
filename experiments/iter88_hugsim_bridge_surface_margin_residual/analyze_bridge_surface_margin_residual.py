#!/usr/bin/env python3
"""Iteration 88 HUGSIM bridge/surface margin residual decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER85_VERDICT = "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE"
ITER87_VERDICT = "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
SUPPORTED_BANDS = {"match", "ambiguous"}
CPA_FAR_MARGIN_M = 6.0
FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "support_object_id": 9,
        "support_bridge_band": "ambiguous",
        "replay_ts": 5.5,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "support_object_id": 10,
        "support_bridge_band": "match",
        "replay_ts": 4.0,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "support_object_id": 10,
        "support_bridge_band": "match",
        "replay_ts": 5.75,
        "alignment": "nearest_before_bridge_ts",
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


ITER87 = _load_module(
    "experiments/iter87_hugsim_interval_bridge_time_surface_replay/"
    "analyze_interval_bridge_time_surface_replay.py",
    "iter87_interval_bridge_time_surface_replay",
)
surface_margin = ITER87.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER87.event_index(rows, label, problems)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def compact_residual(row85: dict[str, Any], row87: dict[str, Any]) -> dict[str, Any]:
    bridge = row85.get("support_bridge") or {}
    replay_metric = row87.get("replay_metric") or {}
    selection = row87.get("selection") or {}
    return {
        "support_bridge_band": bridge.get("distance_band"),
        "support_bridge_best_distance_m": bridge.get("best_distance_m"),
        "replay_alignment": selection.get("alignment"),
        "replay_ts": selection.get("replay_ts"),
        "replay_state": replay_metric.get("state"),
        "replay_min_cpa": replay_metric.get("min_cpa"),
        "replay_active_cpa_margin_m": replay_metric.get("active_cpa_margin_m"),
        "replay_ttc": replay_metric.get("ttc"),
        "replay_active_ttc_margin_s": replay_metric.get("active_ttc_margin_s"),
        "replay_cpa_active_logged_threshold": replay_metric.get("cpa_active_logged_threshold"),
        "replay_ttc_active_logged_threshold": replay_metric.get("ttc_active_logged_threshold"),
        "replay_cpa_borderline_registered": replay_metric.get("cpa_borderline_registered"),
        "replay_ttc_borderline_registered": replay_metric.get("ttc_borderline_registered"),
        "replay_cpa_rank": replay_metric.get("cpa_rank"),
        "replay_ttc_rank": replay_metric.get("ttc_rank"),
    }


def classify_residual(residual: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "bridge_surface_margin_residual_insufficient"
    if residual.get("support_bridge_band") not in SUPPORTED_BANDS:
        return "bridge_surface_margin_residual_insufficient"
    state = residual.get("replay_state")
    active_cpa_margin = residual.get("replay_active_cpa_margin_m")
    active_ttc_margin = residual.get("replay_active_ttc_margin_s")
    if state == "active":
        return "bridge_surface_active"
    if (
        state == "borderline"
        and finite_number(residual.get("replay_ttc"))
        and residual.get("replay_ttc_borderline_registered") is True
        and finite_number(active_ttc_margin)
        and float(active_ttc_margin) > 0.0
        and finite_number(active_cpa_margin)
        and float(active_cpa_margin) >= CPA_FAR_MARGIN_M
        and residual.get("replay_cpa_active_logged_threshold") is False
    ):
        return "bridge_surface_ttc_borderline_cpa_far"
    if (
        state == "subthreshold"
        and not finite_number(residual.get("replay_ttc"))
        and finite_number(active_cpa_margin)
        and float(active_cpa_margin) >= CPA_FAR_MARGIN_M
        and residual.get("replay_cpa_active_logged_threshold") is False
    ):
        return "bridge_surface_no_finite_ttc_cpa_far"
    if state in {"borderline", "subthreshold"}:
        return "bridge_surface_other_residual"
    return "bridge_surface_margin_residual_insufficient"


def crosscheck_sources(
    iter85_report: dict[str, Any],
    iter87_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter85_report.get("verdict") != ITER85_VERDICT:
        problems.append(f"iter85-verdict-not-{ITER85_VERDICT}")
    if iter85_report.get("infra_problems"):
        problems.append(f"iter85-infra-problems:{iter85_report.get('infra_problems')}")
    if iter87_report.get("verdict") != ITER87_VERDICT:
        problems.append(f"iter87-verdict-not-{ITER87_VERDICT}")
    if iter87_report.get("infra_problems"):
        problems.append(f"iter87-infra-problems:{iter87_report.get('infra_problems')}")

    iter85_index = event_index(iter85_report.get("events"), "iter85", problems)
    iter87_index = event_index(iter87_report.get("events"), "iter87", problems)
    if len(iter85_index) != len(FIXED_ROWS):
        problems.append(f"iter85-event-count-mismatch:{len(iter85_index)}")
    if len(iter87_index) != len(FIXED_ROWS):
        problems.append(f"iter87-event-count-mismatch:{len(iter87_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row85 = iter85_index.get(event_key)
        row87 = iter87_index.get(event_key)
        if row85 is None:
            problems.append(f"missing-iter85-event:{event_key}")
            continue
        if row87 is None:
            problems.append(f"missing-iter87-event:{event_key}")
            continue
        if row85.get("problems"):
            problems.append(f"iter85-event-problems:{event_key}:{row85.get('problems')}")
        if row87.get("problems"):
            problems.append(f"iter87-event-problems:{event_key}:{row87.get('problems')}")
        for row_label, row in (("iter85", row85), ("iter87", row87)):
            if not same_object_id(row.get("support_object_id"), target["support_object_id"]):
                problems.append(f"{row_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}")
        if bridge_supported(row85.get("selected_bridge") or {}):
            problems.append(f"iter85-selected-bridge-supported:{event_key}")
        support_bridge = row85.get("support_bridge")
        if not isinstance(support_bridge, dict):
            problems.append(f"iter85-support-bridge-not-dict:{event_key}")
        elif not bridge_supported(support_bridge):
            problems.append(f"iter85-support-bridge-not-supported:{event_key}:{support_bridge.get('distance_band')}")
        elif support_bridge.get("distance_band") != target["support_bridge_band"]:
            problems.append(f"iter85-support-bridge-band-mismatch:{event_key}:{support_bridge.get('distance_band')}")
        selection = row87.get("selection")
        if not isinstance(selection, dict):
            problems.append(f"iter87-selection-not-dict:{event_key}")
        else:
            replay_ts = surface_margin.number(selection.get("replay_ts"), f"iter87.replay_ts:{event_key}", problems)
            if replay_ts is not None and not math.isclose(replay_ts, float(target["replay_ts"]), abs_tol=1e-6):
                problems.append(f"iter87-replay-ts-mismatch:{event_key}:{replay_ts}")
            if selection.get("alignment") != target["alignment"]:
                problems.append(f"iter87-alignment-mismatch:{event_key}:{selection.get('alignment')}")
        if row87.get("row_label") not in {"interval_support_surface_arrival", "interval_support_surface_miss"}:
            problems.append(f"iter87-label-mismatch:{event_key}:{row87.get('row_label')}")
        selected.append({"target": target, "iter85": row85, "iter87": row87})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    problems: list[str] = []
    residual = compact_residual(item["iter85"], item["iter87"])
    label = classify_residual(residual, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "support_object_id": target["support_object_id"],
        "residual": residual,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "bridge_surface_margin_residual_insufficient" in labels
    ):
        return "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_BLOCKED"
    if "bridge_surface_active" in labels:
        return "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_ACTIVE_COMPLETE"
    if (
        all(
            label in {"bridge_surface_ttc_borderline_cpa_far", "bridge_surface_no_finite_ttc_cpa_far"}
            for label in labels
        )
        and "bridge_surface_ttc_borderline_cpa_far" in labels
        and "bridge_surface_no_finite_ttc_cpa_far" in labels
    ):
        return "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE"
    return "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_OTHER_COMPLETE"


def build_report(iter85_report_path: Path, iter87_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter85_report, problems85 = surface_margin.load_report(iter85_report_path, "iter85-report")
    iter87_report, problems87 = surface_margin.load_report(iter87_report_path, "iter87-report")
    infra_problems.extend(problems85 + problems87)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter85_report, iter87_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    bridge_band_counts = Counter((row.get("residual") or {}).get("support_bridge_band") for row in rows)
    replay_state_counts = Counter((row.get("residual") or {}).get("replay_state") for row in rows)
    return {
        "iteration": 88,
        "inputs": {
            "iter85_report": str(iter85_report_path),
            "iter87_report": str(iter87_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "support_bridge_band_counts": {
                str(key): value for key, value in sorted(bridge_band_counts.items()) if key is not None
            },
            "replay_state_counts": {
                str(key): value for key, value in sorted(replay_state_counts.items()) if key is not None
            },
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive bridge/surface margin residual decomposition only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 88 - HUGSIM bridge/surface margin residual decomposition",
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
        "| audit id | event | support id | bridge band | bridge distance | replay state | CPA margin | TTC | TTC margin | label | problems |",
        "|---|---|---:|---|---:|---|---:|---:|---:|---|---|",
    ])
    for row in report["events"]:
        residual = row.get("residual") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['support_object_id']}` | "
            f"`{residual.get('support_bridge_band')}` | `{residual.get('support_bridge_best_distance_m')}` | "
            f"`{residual.get('replay_state')}` | `{residual.get('replay_active_cpa_margin_m')}` | "
            f"`{residual.get('replay_ttc')}` | `{residual.get('replay_active_ttc_margin_s')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter85_report: Path, iter87_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter85_report, iter87_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter85-report",
        type=Path,
        default=Path(
            "experiments/iter85_hugsim_path_horizon_bridge_timing/proof-timing/"
            "path_horizon_bridge_timing_report.json"
        ),
    )
    parser.add_argument(
        "--iter87-report",
        type=Path,
        default=Path(
            "experiments/iter87_hugsim_interval_bridge_time_surface_replay/proof-interval/"
            "interval_bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter88_hugsim_bridge_surface_margin_residual/proof-residual/"
            "bridge_surface_margin_residual_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter88_hugsim_bridge_surface_margin_residual/proof-residual/"
            "bridge_surface_margin_residual.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter85_report, args.iter87_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
