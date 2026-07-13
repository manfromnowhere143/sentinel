#!/usr/bin/env python3
"""Iteration 82 HUGSIM support-object surface/provenance co-occurrence audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER81_VERDICT = "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE"
FIXED_SUPPORT_OBJECTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "support_object_id": 9,
        "iter81_label": "support_object_ever_active",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "support_object_id": 10,
        "iter81_label": "support_object_visible_never_surface",
    },
)
SUPPORTED_BANDS = {"match", "ambiguous"}


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER81 = _load_module(
    "experiments/iter81_hugsim_support_object_temporal_surface/analyze_support_object_temporal_surface.py",
    "iter81_support_temporal",
)
SWITCH = ITER81.SWITCH
surface_margin = ITER81.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def object_index(rows: Any, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append("iter81-objects-not-list")
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("iter81-object-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        if not isinstance(audit_id, str) or not isinstance(scenario, str):
            problems.append(f"iter81-object-key-missing:{row}")
            continue
        key = (audit_id, scenario)
        if key in index:
            problems.append(f"duplicate-iter81-object:{key}")
        index[key] = row
    return index


def bridge_frame(
    decision_row: dict[str, Any],
    event_ts: float,
    obj: dict[str, Any],
    foregrounds: list[dict[str, Any]],
    problems: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    variants: list[dict[str, Any]] = []
    for foreground in foregrounds:
        try:
            variants.extend(SWITCH.bridge_variants(decision_row, event_ts, obj, "support", foreground))
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"support-object-bridge-failed:{obj.get('id')}:{event_ts}:{exc}")
    return variants, SWITCH.best_variant(variants)


def compact_frame(frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if frame is None:
        return None
    keys = (
        "frame_index",
        "ts",
        "state",
        "min_cpa",
        "ttc",
        "cpa_rank",
        "ttc_rank",
        "bridge_band",
        "best_bridge_distance_m",
        "fired",
        "brake",
    )
    compact = {key: frame.get(key) for key in keys}
    compact["best_bridge_variant"] = frame.get("best_bridge_variant")
    return compact


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter81_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter81_report.get("verdict") != ITER81_VERDICT:
        problems.append(f"iter81-verdict-not-{ITER81_VERDICT}")
    if iter81_report.get("infra_problems"):
        problems.append(f"iter81-infra-problems:{iter81_report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter81_index = object_index(iter81_report.get("objects"), problems)
    if len(iter81_index) != len(FIXED_SUPPORT_OBJECTS):
        problems.append(f"iter81-object-count-mismatch:{len(iter81_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_SUPPORT_OBJECTS:
        key = (target["audit_id"], target["scenario"])
        row59 = iter59_index.get(key)
        row81 = iter81_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row81 is None:
            problems.append(f"missing-iter81-object:{key}")
            continue
        if row81.get("problems"):
            problems.append(f"iter81-object-problems:{key}:{row81.get('problems')}")
        if not same_object_id(row81.get("support_object_id"), target["support_object_id"]):
            problems.append(f"iter81-support-object-mismatch:{key}:{row81.get('support_object_id')}")
        if row81.get("row_label") != target["iter81_label"]:
            problems.append(f"iter81-label-mismatch:{key}:{row81.get('row_label')}")
        selected.append({"target": target, "iter59": row59, "iter81": row81})
    if len(selected) != len(FIXED_SUPPORT_OBJECTS):
        problems.append(f"fixed-object-count-mismatch:{len(selected)}")
    return selected, problems


def classify(
    problems: list[str],
    present_frames: list[dict[str, Any]],
    active_supported: list[dict[str, Any]],
    active_match: list[dict[str, Any]],
    active_ambiguous: list[dict[str, Any]],
    borderline_supported: list[dict[str, Any]],
    bridge_supported: list[dict[str, Any]],
    surface_frames: list[dict[str, Any]],
) -> str:
    if problems or not present_frames:
        return "support_surface_bridge_cooccurrence_insufficient"
    if active_match:
        return "support_surface_bridge_active_match"
    if active_ambiguous:
        return "support_surface_bridge_active_ambiguous"
    if borderline_supported and not active_supported:
        return "support_surface_bridge_borderline_only"
    if bridge_supported and surface_frames:
        return "support_bridge_surface_temporally_split"
    if bridge_supported:
        return "support_bridge_never_surface"
    if surface_frames:
        return "support_surface_never_bridge"
    return "support_no_bridge_no_surface"


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row59 = item["iter59"]
    row81 = item["iter81"]
    object_id = target["support_object_id"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
        foregrounds: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        foregrounds, foreground_problems = SWITCH.load_foregrounds(ep_dir / "eval.json")
        problems.extend(row_problems + foreground_problems)

    frames: list[dict[str, Any]] = []
    for idx, decision_row in enumerate(decision_rows):
        ts = surface_margin.number(decision_row.get("ts", decision_row.get("frame_index")), f"decision.ts:{idx}", problems)
        if ts is None:
            continue
        metric = ITER81.metric_for_object(decision_row, object_id, problems)
        if metric is None:
            continue
        obj = SWITCH.select_object(decision_row, object_id, "support", problems)
        variants: list[dict[str, Any]] = []
        best_variant: dict[str, Any] | None = None
        if obj is not None:
            variants, best_variant = bridge_frame(decision_row, ts, obj, foregrounds, problems)
        distance = best_variant["distance_m"] if best_variant is not None else None
        frame = {
            "frame_index": decision_row.get("frame_index", idx),
            "ts": ts,
            "state": metric.get("state"),
            "min_cpa": metric.get("min_cpa"),
            "ttc": metric.get("ttc"),
            "cpa_rank": metric.get("cpa_rank"),
            "ttc_rank": metric.get("ttc_rank"),
            "fired": bool(decision_row.get("fired")),
            "brake": bool(decision_row.get("brake")),
            "evaluated_variant_count": len(variants),
            "best_bridge_distance_m": distance,
            "bridge_band": SWITCH.distance_band(distance),
            "best_bridge_variant": SWITCH.compact_variant(best_variant),
        }
        frames.append(frame)

    bridge_supported = [frame for frame in frames if frame.get("bridge_band") in SUPPORTED_BANDS]
    surface_frames = [frame for frame in frames if frame.get("state") in {"active", "borderline"}]
    active_supported = [
        frame for frame in bridge_supported if frame.get("state") == "active"
    ]
    active_match = [
        frame for frame in active_supported if frame.get("bridge_band") == "match"
    ]
    active_ambiguous = [
        frame for frame in active_supported if frame.get("bridge_band") == "ambiguous"
    ]
    borderline_supported = [
        frame for frame in bridge_supported if frame.get("state") == "borderline"
    ]
    numeric_bridge = [frame for frame in frames if finite_number(frame.get("best_bridge_distance_m"))]
    numeric_surface_bridge = [
        frame for frame in surface_frames if finite_number(frame.get("best_bridge_distance_m"))
    ]
    finite_ttc = [frame["ttc"] for frame in frames if finite_number(frame.get("ttc"))]
    label = classify(
        problems,
        frames,
        active_supported,
        active_match,
        active_ambiguous,
        borderline_supported,
        bridge_supported,
        surface_frames,
    )
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "support_object_id": object_id,
        "iter81_row_label": row81.get("row_label"),
        "foreground_count": len(foregrounds),
        "present_frame_count": len(frames),
        "bridge_supported_frame_count": len(bridge_supported),
        "active_bridge_supported_frame_count": len(active_supported),
        "borderline_bridge_supported_frame_count": len(borderline_supported),
        "surface_frame_count": len(surface_frames),
        "first_bridge_supported_ts": bridge_supported[0]["ts"] if bridge_supported else None,
        "first_surface_bridge_supported_ts": (
            (active_supported or borderline_supported)[0]["ts"] if active_supported or borderline_supported else None
        ),
        "best_bridge_frame": compact_frame(
            min(numeric_bridge, key=lambda frame: frame["best_bridge_distance_m"]) if numeric_bridge else None
        ),
        "best_surface_bridge_frame": compact_frame(
            min(numeric_surface_bridge, key=lambda frame: frame["best_bridge_distance_m"])
            if numeric_surface_bridge
            else None
        ),
        "min_cpa": min((frame["min_cpa"] for frame in frames if finite_number(frame.get("min_cpa"))), default=None),
        "min_finite_ttc": min(finite_ttc) if finite_ttc else None,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_SUPPORT_OBJECTS)
        or any(row.get("problems") for row in rows)
        or "support_surface_bridge_cooccurrence_insufficient" in labels
    ):
        return "HUGSIM_SUPPORT_SURFACE_BRIDGE_BLOCKED"
    if "support_surface_bridge_active_match" in labels:
        return "HUGSIM_SUPPORT_SURFACE_BRIDGE_ACTIVE_MATCH_COMPLETE"
    if "support_surface_bridge_active_ambiguous" in labels:
        return "HUGSIM_SUPPORT_SURFACE_BRIDGE_ACTIVE_AMBIGUOUS_COMPLETE"
    if "support_surface_bridge_borderline_only" in labels:
        return "HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE"
    no_cooccurrence_labels = {
        "support_bridge_surface_temporally_split",
        "support_bridge_never_surface",
        "support_surface_never_bridge",
        "support_no_bridge_no_surface",
    }
    if all(label in no_cooccurrence_labels for label in labels):
        return "HUGSIM_SUPPORT_SURFACE_BRIDGE_TEMPORAL_SPLIT_COMPLETE"
    return "HUGSIM_SUPPORT_SURFACE_BRIDGE_MIXED_COMPLETE"


def build_report(iter59_report_path: Path, iter81_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter81_report, problems81 = surface_margin.load_report(iter81_report_path, "iter81-report")
    infra_problems.extend(problems59 + problems81)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter81_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 82,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter81_report": str(iter81_report_path),
        },
        "fixed_support_objects": list(FIXED_SUPPORT_OBJECTS),
        "infra_problems": infra_problems,
        "objects": rows,
        "summary": {
            "target_objects": len(selected),
            "evaluated_objects": sum(not row.get("problems") for row in rows),
            "object_label_counts": dict(sorted(label_counts.items())),
            "objects_with_bridge_support": sum(row.get("bridge_supported_frame_count", 0) > 0 for row in rows),
            "objects_with_surface_bridge_cooccurrence": sum(
                row.get("active_bridge_supported_frame_count", 0) > 0
                or row.get("borderline_bridge_supported_frame_count", 0) > 0
                for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-object descriptive surface/provenance co-occurrence audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 82 - HUGSIM support-object surface/provenance co-occurrence audit",
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
        "| audit id | support id | label | present | bridge-supported | active+bridge | borderline+bridge | first bridge | first surface+bridge | best bridge m | best surface bridge m | problems |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["objects"]:
        best_bridge = row.get("best_bridge_frame") or {}
        best_surface = row.get("best_surface_bridge_frame") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['support_object_id']}` | `{row['row_label']}` | "
            f"`{row['present_frame_count']}` | `{row['bridge_supported_frame_count']}` | "
            f"`{row['active_bridge_supported_frame_count']}` | "
            f"`{row['borderline_bridge_supported_frame_count']}` | "
            f"`{row.get('first_bridge_supported_ts')}` | "
            f"`{row.get('first_surface_bridge_supported_ts')}` | "
            f"`{best_bridge.get('best_bridge_distance_m')}` | "
            f"`{best_surface.get('best_bridge_distance_m')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter81_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter81_report)
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
        "--iter81-report",
        type=Path,
        default=Path("experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/temporal_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/"
            "cooccurrence_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/cooccurrence.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter81_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
