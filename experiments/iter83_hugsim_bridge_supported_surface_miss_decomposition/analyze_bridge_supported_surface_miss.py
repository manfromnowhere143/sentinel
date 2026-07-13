#!/usr/bin/env python3
"""Iteration 83 HUGSIM bridge-supported surface-miss decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER82_VERDICT = "HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE"
FIXED_SUPPORT_OBJECTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "support_object_id": 9,
        "iter82_label": "support_surface_bridge_borderline_only",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "support_object_id": 10,
        "iter82_label": "support_bridge_never_surface",
    },
)
SUPPORTED_BANDS = {"match", "ambiguous"}
BORDERLINE_CPA_M = 3.0
BORDERLINE_TTC_S = 5.0


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER82 = _load_module(
    "experiments/iter82_hugsim_support_surface_bridge_cooccurrence/"
    "analyze_support_surface_bridge_cooccurrence.py",
    "iter82_support_cooccurrence",
)
ITER81 = ITER82.ITER81
SWITCH = ITER82.SWITCH
surface_margin = ITER82.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def object_index(rows: Any, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append("iter82-objects-not-list")
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("iter82-object-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        if not isinstance(audit_id, str) or not isinstance(scenario, str):
            problems.append(f"iter82-object-key-missing:{row}")
            continue
        key = (audit_id, scenario)
        if key in index:
            problems.append(f"duplicate-iter82-object:{key}")
        index[key] = row
    return index


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter82_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter82_report.get("verdict") != ITER82_VERDICT:
        problems.append(f"iter82-verdict-not-{ITER82_VERDICT}")
    if iter82_report.get("infra_problems"):
        problems.append(f"iter82-infra-problems:{iter82_report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter82_index = object_index(iter82_report.get("objects"), problems)
    if len(iter82_index) != len(FIXED_SUPPORT_OBJECTS):
        problems.append(f"iter82-object-count-mismatch:{len(iter82_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_SUPPORT_OBJECTS:
        key = (target["audit_id"], target["scenario"])
        row59 = iter59_index.get(key)
        row82 = iter82_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row82 is None:
            problems.append(f"missing-iter82-object:{key}")
            continue
        if row82.get("problems"):
            problems.append(f"iter82-object-problems:{key}:{row82.get('problems')}")
        if not same_object_id(row82.get("support_object_id"), target["support_object_id"]):
            problems.append(f"iter82-support-object-mismatch:{key}:{row82.get('support_object_id')}")
        if row82.get("row_label") != target["iter82_label"]:
            problems.append(f"iter82-label-mismatch:{key}:{row82.get('row_label')}")
        selected.append({"target": target, "iter59": row59, "iter82": row82})
    if len(selected) != len(FIXED_SUPPORT_OBJECTS):
        problems.append(f"fixed-object-count-mismatch:{len(selected)}")
    return selected, problems


def compact_frame(frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if frame is None:
        return None
    keys = (
        "frame_index",
        "ts",
        "bridge_band",
        "best_bridge_distance_m",
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
    return {key: frame.get(key) for key in keys}


def metric_with_margins(
    decision_row: dict[str, Any],
    object_id: Any,
    problems: list[str],
) -> dict[str, Any] | None:
    metric = ITER81.metric_for_object(decision_row, object_id, problems)
    if metric is None:
        return None
    cpa_margin, ttc_thresh = ITER81.ITER78.channel_thresholds(decision_row, problems)
    min_cpa = metric.get("min_cpa")
    ttc = metric.get("ttc")
    if finite_number(min_cpa) and cpa_margin is not None:
        metric["active_cpa_margin_m"] = float(min_cpa) - float(cpa_margin)
        metric["borderline_cpa_margin_m"] = float(min_cpa) - BORDERLINE_CPA_M
    else:
        metric["active_cpa_margin_m"] = None
        metric["borderline_cpa_margin_m"] = None
    if finite_number(ttc) and ttc_thresh is not None:
        metric["active_ttc_margin_s"] = float(ttc) - float(ttc_thresh)
        metric["borderline_ttc_margin_s"] = float(ttc) - BORDERLINE_TTC_S
    else:
        metric["active_ttc_margin_s"] = None
        metric["borderline_ttc_margin_s"] = None
    return metric


def bridge_supported_frames(item: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], int]:
    target = item["target"]
    row59 = item["iter59"]
    object_id = target["support_object_id"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        return [], ["episode-dir-missing"], 0

    ep_dir = Path(episode_dir)
    decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
    foregrounds, foreground_problems = SWITCH.load_foregrounds(ep_dir / "eval.json")
    problems.extend(row_problems + foreground_problems)

    frames: list[dict[str, Any]] = []
    for idx, decision_row in enumerate(decision_rows):
        ts = surface_margin.number(decision_row.get("ts", decision_row.get("frame_index")), f"decision.ts:{idx}", problems)
        if ts is None:
            continue
        metric = metric_with_margins(decision_row, object_id, problems)
        if metric is None:
            continue
        obj = SWITCH.select_object(decision_row, object_id, "support", problems)
        if obj is None:
            continue
        variants, best_variant = ITER82.bridge_frame(decision_row, ts, obj, foregrounds, problems)
        distance = best_variant["distance_m"] if best_variant is not None else None
        bridge_band = SWITCH.distance_band(distance)
        if bridge_band not in SUPPORTED_BANDS:
            continue
        frame = {
            "frame_index": decision_row.get("frame_index", idx),
            "ts": ts,
            "bridge_band": bridge_band,
            "evaluated_variant_count": len(variants),
            "best_bridge_distance_m": distance,
            "best_bridge_variant": SWITCH.compact_variant(best_variant),
        }
        frame.update(metric)
        frames.append(frame)
    return frames, problems, len(foregrounds)


def best_by(frames: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    numeric = [frame for frame in frames if finite_number(frame.get(field))]
    if not numeric:
        return None
    return min(numeric, key=lambda frame: frame[field])


def classify(frames: list[dict[str, Any]], problems: list[str]) -> str:
    if problems or not frames:
        return "bridge_supported_surface_miss_insufficient"
    active = [frame for frame in frames if frame.get("state") == "active"]
    if active:
        return "bridge_supported_active_surface_present"
    cpa_borderline = [frame for frame in frames if frame.get("cpa_borderline_registered")]
    ttc_borderline = [frame for frame in frames if frame.get("ttc_borderline_registered")]
    if cpa_borderline and ttc_borderline:
        return "bridge_supported_borderline_mixed"
    if ttc_borderline:
        return "bridge_supported_borderline_ttc_only"
    if cpa_borderline:
        return "bridge_supported_borderline_cpa_only"
    finite_ttc = [frame for frame in frames if finite_number(frame.get("ttc"))]
    if not finite_ttc:
        return "bridge_supported_subthreshold_no_finite_ttc"
    return "bridge_supported_subthreshold_finite_ttc_far"


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row82 = item["iter82"]
    frames, problems, foreground_count = bridge_supported_frames(item)
    active = [frame for frame in frames if frame.get("state") == "active"]
    borderline = [frame for frame in frames if frame.get("state") == "borderline"]
    subthreshold = [frame for frame in frames if frame.get("state") == "subthreshold"]
    finite_ttc = [frame for frame in frames if finite_number(frame.get("ttc"))]
    label = classify(frames, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "support_object_id": target["support_object_id"],
        "iter82_row_label": row82.get("row_label"),
        "foreground_count": foreground_count,
        "bridge_supported_frame_count": len(frames),
        "active_bridge_supported_frame_count": len(active),
        "borderline_bridge_supported_frame_count": len(borderline),
        "subthreshold_bridge_supported_frame_count": len(subthreshold),
        "finite_ttc_bridge_supported_frame_count": len(finite_ttc),
        "min_active_cpa_margin_m": (
            min(frame["active_cpa_margin_m"] for frame in frames if finite_number(frame.get("active_cpa_margin_m")))
            if frames
            else None
        ),
        "min_active_ttc_margin_s": (
            min(frame["active_ttc_margin_s"] for frame in frames if finite_number(frame.get("active_ttc_margin_s")))
            if finite_ttc
            else None
        ),
        "min_borderline_cpa_margin_m": (
            min(
                frame["borderline_cpa_margin_m"]
                for frame in frames
                if finite_number(frame.get("borderline_cpa_margin_m"))
            )
            if frames
            else None
        ),
        "min_borderline_ttc_margin_s": (
            min(
                frame["borderline_ttc_margin_s"]
                for frame in frames
                if finite_number(frame.get("borderline_ttc_margin_s"))
            )
            if finite_ttc
            else None
        ),
        "best_bridge_frame": compact_frame(best_by(frames, "best_bridge_distance_m")),
        "best_active_cpa_margin_frame": compact_frame(best_by(frames, "active_cpa_margin_m")),
        "best_active_ttc_margin_frame": compact_frame(best_by(frames, "active_ttc_margin_s")),
        "best_borderline_cpa_margin_frame": compact_frame(best_by(frames, "borderline_cpa_margin_m")),
        "best_borderline_ttc_margin_frame": compact_frame(best_by(frames, "borderline_ttc_margin_s")),
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_SUPPORT_OBJECTS)
        or any(row.get("problems") for row in rows)
        or "bridge_supported_surface_miss_insufficient" in labels
    ):
        return "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_BLOCKED"
    if "bridge_supported_active_surface_present" in labels:
        return "HUGSIM_BRIDGE_SUPPORTED_ACTIVE_SURFACE_PRESENT_COMPLETE"
    if len(set(labels)) >= 2:
        return "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE"
    if all(label == "bridge_supported_borderline_ttc_only" for label in labels):
        return "HUGSIM_BRIDGE_SUPPORTED_BORDERLINE_TTC_ONLY_COMPLETE"
    if all(label == "bridge_supported_borderline_cpa_only" for label in labels):
        return "HUGSIM_BRIDGE_SUPPORTED_BORDERLINE_CPA_ONLY_COMPLETE"
    if all(label == "bridge_supported_subthreshold_no_finite_ttc" for label in labels):
        return "HUGSIM_BRIDGE_SUPPORTED_SUBTHRESHOLD_NO_TTC_COMPLETE"
    if all(label == "bridge_supported_subthreshold_finite_ttc_far" for label in labels):
        return "HUGSIM_BRIDGE_SUPPORTED_SUBTHRESHOLD_FINITE_TTC_COMPLETE"
    return "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE"


def build_report(iter59_report_path: Path, iter82_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter82_report, problems82 = surface_margin.load_report(iter82_report_path, "iter82-report")
    infra_problems.extend(problems59 + problems82)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter82_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 83,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter82_report": str(iter82_report_path),
        },
        "fixed_support_objects": list(FIXED_SUPPORT_OBJECTS),
        "infra_problems": infra_problems,
        "objects": rows,
        "summary": {
            "target_objects": len(selected),
            "evaluated_objects": sum(not row.get("problems") for row in rows),
            "object_label_counts": dict(sorted(label_counts.items())),
            "bridge_supported_frames": sum(row.get("bridge_supported_frame_count", 0) for row in rows),
            "active_bridge_supported_frames": sum(row.get("active_bridge_supported_frame_count", 0) for row in rows),
            "borderline_bridge_supported_frames": sum(
                row.get("borderline_bridge_supported_frame_count", 0) for row in rows
            ),
            "finite_ttc_bridge_supported_frames": sum(
                row.get("finite_ttc_bridge_supported_frame_count", 0) for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-object descriptive bridge-supported surface-miss decomposition only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 83 - HUGSIM bridge-supported surface-miss decomposition",
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
        "## Objects",
        "",
        "| audit id | support id | label | bridge frames | active | borderline | subthreshold | finite ttc | min active cpa margin | min active ttc margin | min borderline ttc margin | problems |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["objects"]:
        lines.append(
            f"| `{row['audit_id']}` | `{row['support_object_id']}` | `{row['row_label']}` | "
            f"`{row['bridge_supported_frame_count']}` | `{row['active_bridge_supported_frame_count']}` | "
            f"`{row['borderline_bridge_supported_frame_count']}` | "
            f"`{row['subthreshold_bridge_supported_frame_count']}` | "
            f"`{row['finite_ttc_bridge_supported_frame_count']}` | "
            f"`{row.get('min_active_cpa_margin_m')}` | `{row.get('min_active_ttc_margin_s')}` | "
            f"`{row.get('min_borderline_ttc_margin_s')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter82_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter82_report)
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
        "--iter82-report",
        type=Path,
        default=Path(
            "experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/"
            "cooccurrence_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/"
            "surface_miss_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/"
            "surface_miss.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter82_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
