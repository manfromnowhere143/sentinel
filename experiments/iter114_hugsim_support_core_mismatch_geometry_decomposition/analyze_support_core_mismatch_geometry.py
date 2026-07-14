#!/usr/bin/env python3
"""Iteration 114 HUGSIM support-core mismatch-geometry decomposition."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER113_VERDICT = "HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
FAR_M = 6.0


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


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


def vec2(value: Any, field: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError(f"{field}-not-vec2")
    if not numeric(value[0]) or not numeric(value[1]):
        raise ValueError(f"{field}-nonnumeric")
    return float(value[0]), float(value[1])


def forward_relation(delta_forward_m: float) -> str:
    if delta_forward_m > FAR_M:
        return "monitor_far_ahead"
    if delta_forward_m < -FAR_M:
        return "monitor_far_behind"
    return "monitor_forward_near"


def lateral_relation(delta_lateral_m: float) -> str:
    if delta_lateral_m > FAR_M:
        return "monitor_far_left"
    if delta_lateral_m < -FAR_M:
        return "monitor_far_right"
    return "monitor_lateral_near"


def dominant_component(abs_forward_delta_m: float, abs_lateral_delta_m: float) -> str:
    if abs_forward_delta_m > abs_lateral_delta_m:
        return "forward_dominant"
    if abs_lateral_delta_m > abs_forward_delta_m:
        return "lateral_dominant"
    return "balanced"


def combined_geometry(forward_label: str, lateral_label: str) -> str:
    lateral_far = lateral_label in {"monitor_far_left", "monitor_far_right"}
    if forward_label == "monitor_far_behind" and lateral_label == "monitor_lateral_near":
        return "far_behind_lateral_near"
    if forward_label == "monitor_far_ahead" and lateral_label == "monitor_lateral_near":
        return "far_ahead_lateral_near"
    if forward_label == "monitor_forward_near" and lateral_far:
        return "forward_near_lateral_far"
    if forward_label == "monitor_far_behind" and lateral_far:
        return "far_behind_lateral_far"
    if forward_label == "monitor_far_ahead" and lateral_far:
        return "far_ahead_lateral_far"
    return "diagonal_near_components"


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    if row.get("support_label") != "classifiable_foreground":
        problems.append(f"support-label-not-classifiable:{row.get('support_label')!r}")
    if row.get("bridge_label") != "actor_mismatch":
        problems.append(f"bridge-label-not-mismatch:{row.get('bridge_label')!r}")
    distance = row.get("bridge_distance_m")
    if not numeric(distance):
        problems.append("bridge-distance-nonnumeric")
        distance_f = math.nan
    else:
        distance_f = float(distance)
        if distance_f <= FAR_M:
            problems.append(f"bridge-distance-not-mismatch:{distance_f}")
    try:
        monitor_forward, monitor_lateral = vec2(row.get("monitor_forward_lateral"), "monitor_forward_lateral")
        hugsim_forward, hugsim_lateral = vec2(row.get("hugsim_forward_lateral"), "hugsim_forward_lateral")
    except ValueError as exc:
        problems.append(str(exc))
        monitor_forward = monitor_lateral = hugsim_forward = hugsim_lateral = math.nan

    if problems:
        return {
            "slot_index": row.get("slot_index"),
            "slot_id": row.get("slot_id"),
            "scenario": row.get("scenario"),
            "run": row.get("run"),
            "design_label": row.get("design_label"),
            "problems": problems,
        }

    delta_forward = monitor_forward - hugsim_forward
    delta_lateral = monitor_lateral - hugsim_lateral
    abs_forward = abs(delta_forward)
    abs_lateral = abs(delta_lateral)
    f_label = forward_relation(delta_forward)
    l_label = lateral_relation(delta_lateral)
    d_label = dominant_component(abs_forward, abs_lateral)
    g_label = combined_geometry(f_label, l_label)
    return {
        "slot_index": row.get("slot_index"),
        "slot_id": row.get("slot_id"),
        "scenario": row.get("scenario"),
        "run": row.get("run"),
        "design_label": row.get("design_label"),
        "fire_timing_label": row.get("fire_timing_label"),
        "monitor_object_id": row.get("monitor_object_id"),
        "first_foreground_obs_name": row.get("first_foreground_obs_name"),
        "bridge_distance_m": distance_f,
        "monitor_forward_m": monitor_forward,
        "monitor_lateral_m": monitor_lateral,
        "hugsim_forward_m": hugsim_forward,
        "hugsim_lateral_m": hugsim_lateral,
        "delta_forward_m": delta_forward,
        "delta_lateral_m": delta_lateral,
        "abs_forward_delta_m": abs_forward,
        "abs_lateral_delta_m": abs_lateral,
        "forward_relation": f_label,
        "lateral_relation": l_label,
        "dominant_component": d_label,
        "geometry_label": g_label,
        "problems": [],
    }


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _minmax(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(row[key]) for row in rows if numeric(row.get(key))]
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("geometry_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter113_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter113_report, report_problems = load_json(iter113_report_path, "iter113-report")
    infra_problems.extend(report_problems)
    source_rows: list[dict[str, Any]] = []
    geometry_rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter113-verdict", iter113_report.get("verdict"), ITER113_VERDICT)
        episodes = iter113_report.get("episodes")
        if not isinstance(episodes, list):
            infra_problems.append("iter113-episodes-not-list")
        else:
            require_equal(infra_problems, "iter113-episode-count", len(episodes), EXPECTED_ROW_COUNT)
            source_rows = [row for row in episodes if isinstance(row, dict)]
            require_equal(infra_problems, "iter113-dict-episode-count", len(source_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        geometry_rows = [classify_row(row) for row in source_rows]

    geometry_counts = Counter(row.get("geometry_label") for row in geometry_rows if not row.get("problems"))
    forward_counts = Counter(row.get("forward_relation") for row in geometry_rows if not row.get("problems"))
    lateral_counts = Counter(row.get("lateral_relation") for row in geometry_rows if not row.get("problems"))
    dominant_counts = Counter(row.get("dominant_component") for row in geometry_rows if not row.get("problems"))
    summary = {
        "row_count": len(geometry_rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in geometry_rows),
        "geometry_label_counts": _dict_counts(geometry_counts),
        "forward_relation_counts": _dict_counts(forward_counts),
        "lateral_relation_counts": _dict_counts(lateral_counts),
        "dominant_component_counts": _dict_counts(dominant_counts),
        "bridge_distance_m": _minmax(geometry_rows, "bridge_distance_m"),
        "abs_forward_delta_m": _minmax(geometry_rows, "abs_forward_delta_m"),
        "abs_lateral_delta_m": _minmax(geometry_rows, "abs_lateral_delta_m"),
    }
    verdict = choose_verdict(infra_problems, geometry_rows, summary)
    return {
        "iteration": 114,
        "inputs": {
            "iter113_report": str(iter113_report_path),
        },
        "infra_problems": infra_problems,
        "geometry_rows": geometry_rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive geometry decomposition of eight committed support-core mismatch vectors only; "
            "no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 114 - HUGSIM support-core mismatch-geometry decomposition",
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
            "## Rows",
            "",
            "| slot | scenario | run | geometry | forward | lateral | dominant | d_forward | d_lateral | distance |",
            "|---:|---|---:|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in report["geometry_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('geometry_label')}` | `{row.get('forward_relation')}` | "
            f"`{row.get('lateral_relation')}` | `{row.get('dominant_component')}` | "
            f"`{row.get('delta_forward_m')}` | `{row.get('delta_lateral_m')}` | "
            f"`{row.get('bridge_distance_m')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter113_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter113_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter113-report",
        type=Path,
        default=Path(
            "experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/"
            "support_core_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition/proof-geometry/"
            "support_core_mismatch_geometry_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition/proof-geometry/"
            "support_core_mismatch_geometry.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter113_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
