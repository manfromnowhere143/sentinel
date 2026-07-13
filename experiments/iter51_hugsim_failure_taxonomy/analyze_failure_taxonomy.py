#!/usr/bin/env python3
"""Iteration 51 HUGSIM transfer-failure taxonomy.

Runs ONCE, offline, over committed iteration-48/49 HUGSIM proof artifacts.
The analyzer implements the frozen taxonomy in HYPOTHESIS.md:

- OFF/ON primary collision = min(top-level nc, details.*.nc) < 1.0.
- ON intervention timing = first decision row with brake == true.
- Material HD deadband = 0.03, descriptive only.
- Mutually exclusive category order is fixed in HYPOTHESIS.md.

No GPU, no gcloud, no box reads, no external data, no retuning, no safety claim.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

MATERIAL_HD_BAR = 0.03
DOMINANCE_BAR = 0.40
PRIMARY_NC_BAR = 1.0
EXPECTED_PAIRS_PER_DATASET = 52

CATEGORY_ORDER = (
    "induced_collision",
    "clean_no_off_opportunity",
    "converted_collision_material_gain",
    "converted_collision_no_material_gain",
    "persistent_collision_no_brake",
    "persistent_collision_late_by_proxy",
    "persistent_collision_early_by_proxy",
)

PAIR_RE = re.compile(r"^(?P<scenario>.+)__off_r(?P<run>[12])$")
TIER_RE = re.compile(r"-(easy|medium|hard|extreme)-")
ATTACKPLANNER_HARD_SCENARIOS = {"scene-0041-hard-00", "scene-0411-hard-00"}


def _numeric(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"non-numeric {field}")
    return float(value)


def _details_items(ev: dict) -> list[tuple[float, dict]]:
    out: list[tuple[float, dict]] = []
    details = ev.get("details", {})
    if not isinstance(details, dict):
        raise ValueError("details-not-dict")
    for key, row in details.items():
        try:
            t = float(key)
        except ValueError as exc:
            raise ValueError(f"bad-details-time:{key}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"details-row-not-dict:{key}")
        out.append((t, row))
    return sorted(out, key=lambda item: item[0])


def read_eval_metrics(path: Path) -> dict:
    """Read frozen HUGSIM metric fields from one eval.json."""
    ev = json.loads(path.read_text())
    hdscore = _numeric(ev["hdscore"], "hdscore")
    nc_values = [_numeric(ev["nc"], "nc")]
    first_nc_time = None
    first_nc_source = None
    for t, row in _details_items(ev):
        nc = _numeric(row["nc"], f"details.{t}.nc")
        nc_values.append(nc)
        if first_nc_time is None and nc < PRIMARY_NC_BAR:
            first_nc_time = t
            first_nc_source = "details"
    nc_min = min(nc_values)
    if nc_min < PRIMARY_NC_BAR and first_nc_time is None:
        first_nc_source = "top_level_only"
    return {
        "hdscore": hdscore,
        "nc_min": nc_min,
        "primary_collision": nc_min < PRIMARY_NC_BAR,
        "first_nc_time": first_nc_time,
        "first_nc_source": first_nc_source,
    }


def read_decision_summary(path: Path) -> dict:
    """Summarize ON-arm decision rows; rows with trace_error do not count as monitor frames."""
    if not path.exists():
        raise FileNotFoundError(path)
    monitor_frames = 0
    fired_frames = 0
    brake_frames = 0
    release_frames = 0
    first_fire_ts = None
    first_brake_ts = None
    min_ttc = None
    min_cpa = None
    object_rows = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "trace_error" in row:
            continue
        monitor_frames += 1
        fired = bool(row.get("fired"))
        brake = bool(row.get("brake"))
        release = bool(row.get("release"))
        fired_frames += int(fired)
        brake_frames += int(brake)
        release_frames += int(release)
        ts_raw = row.get("ts")
        ts = _numeric(ts_raw, "ts") if ts_raw is not None else float(row.get("frame_index", 0))
        if fired and first_fire_ts is None:
            first_fire_ts = ts
        if brake and first_brake_ts is None:
            first_brake_ts = ts
        if isinstance(row.get("min_ttc"), (int, float)) and not isinstance(row.get("min_ttc"), bool):
            val = float(row["min_ttc"])
            min_ttc = val if min_ttc is None else min(min_ttc, val)
        if isinstance(row.get("min_cpa"), (int, float)) and not isinstance(row.get("min_cpa"), bool):
            val = float(row["min_cpa"])
            min_cpa = val if min_cpa is None else min(min_cpa, val)
        objs = row.get("objs")
        if isinstance(objs, list) and objs:
            object_rows += 1
    if monitor_frames == 0:
        raise ValueError("empty-decision-log")
    return {
        "monitor_frames": monitor_frames,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "release_frames": release_frames,
        "first_fire_ts": first_fire_ts,
        "first_brake_ts": first_brake_ts,
        "brake_fraction": brake_frames / monitor_frames,
        "min_monitor_ttc": min_ttc,
        "min_monitor_cpa": min_cpa,
        "object_rows": object_rows,
    }


def scenario_tier(scenario: str) -> str:
    match = TIER_RE.search(scenario)
    return match.group(1) if match else "unknown"


def is_attackplanner_scenario(scenario: str) -> bool:
    return "-extreme-" in scenario or scenario in ATTACKPLANNER_HARD_SCENARIOS


def assign_category(pair: dict) -> str:
    off_collision = pair["off_primary_collision"]
    on_collision = pair["on_primary_collision"]
    if not off_collision:
        return "induced_collision" if on_collision else "clean_no_off_opportunity"
    if not on_collision:
        if pair["delta_hd"] > MATERIAL_HD_BAR:
            return "converted_collision_material_gain"
        return "converted_collision_no_material_gain"
    if pair["brake_frames"] == 0:
        return "persistent_collision_no_brake"
    first_brake = pair["first_brake_ts"]
    first_nc = pair["off_first_nc_time"]
    if first_brake is None or first_nc is None or first_brake > first_nc:
        return "persistent_collision_late_by_proxy"
    return "persistent_collision_early_by_proxy"


def enrich_pair(pair: dict) -> dict:
    category = assign_category(pair)
    pair = dict(pair)
    pair["category"] = category
    pair["material_gain"] = pair["delta_hd"] > MATERIAL_HD_BAR
    pair["material_loss"] = pair["delta_hd"] < -MATERIAL_HD_BAR
    pair["score_loss_under_brake"] = pair["brake_frames"] > 0 and pair["material_loss"]
    pair["converted_collision"] = (
        pair["off_primary_collision"] and not pair["on_primary_collision"]
    )
    pair["persistent_collision"] = (
        pair["off_primary_collision"] and pair["on_primary_collision"]
    )
    pair["late_by_proxy"] = (
        pair["off_primary_collision"]
        and pair["brake_frames"] > 0
        and (
            pair["first_brake_ts"] is None
            or pair["off_first_nc_time"] is None
            or pair["first_brake_ts"] > pair["off_first_nc_time"]
        )
    )
    return pair


def collect_dataset(dataset: str, episodes_root: Path, transfer_report_path: Path,
                    problems: list[str]) -> list[dict]:
    pairs = []
    for off_dir in sorted(episodes_root.iterdir()):
        if not off_dir.is_dir() or "__off_r" not in off_dir.name:
            continue
        match = PAIR_RE.match(off_dir.name)
        if not match:
            problems.append(f"{dataset}:bad-off-dir-name:{off_dir.name}")
            continue
        scenario = match.group("scenario")
        run = int(match.group("run"))
        on_dir = episodes_root / f"{scenario}__on_r{run}"
        try:
            off_eval = read_eval_metrics(off_dir / "eval.json")
            on_eval = read_eval_metrics(on_dir / "eval.json")
            decisions = read_decision_summary(on_dir / "sentinel_iter48_decisions.jsonl")
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            problems.append(f"{dataset}:{scenario}:r{run}:{exc}")
            continue
        pair = {
            "dataset": dataset,
            "scenario": scenario,
            "run": run,
            "tier": scenario_tier(scenario),
            "attackplanner": is_attackplanner_scenario(scenario),
            "hd_off": off_eval["hdscore"],
            "hd_on": on_eval["hdscore"],
            "delta_hd": on_eval["hdscore"] - off_eval["hdscore"],
            "off_nc_min": off_eval["nc_min"],
            "on_nc_min": on_eval["nc_min"],
            "off_primary_collision": off_eval["primary_collision"],
            "on_primary_collision": on_eval["primary_collision"],
            "off_first_nc_time": off_eval["first_nc_time"],
            "off_first_nc_source": off_eval["first_nc_source"],
            "on_first_nc_time": on_eval["first_nc_time"],
            "on_first_nc_source": on_eval["first_nc_source"],
            **decisions,
        }
        pairs.append(enrich_pair(pair))
    if len(pairs) != EXPECTED_PAIRS_PER_DATASET:
        problems.append(f"{dataset}:pair-count:{len(pairs)}!={EXPECTED_PAIRS_PER_DATASET}")
    _check_transfer_report(dataset, transfer_report_path, pairs, problems)
    return pairs


def _check_transfer_report(dataset: str, path: Path, pairs: list[dict], problems: list[str]) -> None:
    try:
        report = json.loads(path.read_text())
        expected_pairs = int(report["primary"]["pairs"])
        expected_mean = float(report["primary"]["point_mean"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        problems.append(f"{dataset}:bad-transfer-report:{exc}")
        return
    if expected_pairs != len(pairs):
        problems.append(f"{dataset}:transfer-pair-count:{expected_pairs}!={len(pairs)}")
        return
    point_mean = statistics.mean(p["delta_hd"] for p in pairs)
    if abs(point_mean - expected_mean) > 1e-9:
        problems.append(
            f"{dataset}:transfer-mean-mismatch:{point_mean:.12f}!={expected_mean:.12f}"
        )


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize_pairs(pairs: list[dict]) -> dict:
    counts = Counter(p["category"] for p in pairs)
    off_opp = [p for p in pairs if p["off_primary_collision"]]
    off_counts = Counter(p["category"] for p in off_opp)
    dominant_category = "mixed_taxonomy"
    dominant_fraction = None
    if off_opp:
        category, count = max(off_counts.items(), key=lambda item: (item[1], item[0]))
        dominant_fraction = count / len(off_opp)
        if dominant_fraction >= DOMINANCE_BAR:
            dominant_category = category
    category_stats = {}
    for category in CATEGORY_ORDER:
        sub = [p for p in pairs if p["category"] == category]
        deltas = [p["delta_hd"] for p in sub]
        category_stats[category] = {
            "count": len(sub),
            "mean_delta_hd": _mean(deltas),
            "median_delta_hd": _median(deltas),
        }
    return {
        "pairs": len(pairs),
        "category_counts": {category: counts.get(category, 0) for category in CATEGORY_ORDER},
        "off_opportunity_pairs": len(off_opp),
        "off_opportunity_category_counts": {
            category: off_counts.get(category, 0) for category in CATEGORY_ORDER
        },
        "dominance_bar": DOMINANCE_BAR,
        "dominant_category": dominant_category,
        "dominant_category_fraction": dominant_fraction,
        "mean_delta_hd": _mean([p["delta_hd"] for p in pairs]),
        "median_delta_hd": _median([p["delta_hd"] for p in pairs]),
        "material_gain_pairs": sum(p["material_gain"] for p in pairs),
        "material_loss_pairs": sum(p["material_loss"] for p in pairs),
        "score_loss_under_brake_pairs": sum(p["score_loss_under_brake"] for p in pairs),
        "converted_collision_pairs": sum(p["converted_collision"] for p in pairs),
        "persistent_collision_pairs": sum(p["persistent_collision"] for p in pairs),
        "late_by_proxy_pairs": sum(p["late_by_proxy"] for p in pairs),
        "category_delta_stats": category_stats,
    }


def grouped_summaries(pairs: list[dict]) -> dict:
    by_dataset = {
        dataset: summarize_pairs([p for p in pairs if p["dataset"] == dataset])
        for dataset in sorted({p["dataset"] for p in pairs})
    }
    iter49_pairs = [p for p in pairs if p["dataset"] == "iter49_hard_extreme"]
    return {
        "combined": summarize_pairs(pairs),
        "by_dataset": by_dataset,
        "iter49_attackplanner": {
            "attackplanner": summarize_pairs([p for p in iter49_pairs if p["attackplanner"]]),
            "non_attackplanner": summarize_pairs([
                p for p in iter49_pairs if not p["attackplanner"]
            ]),
        },
    }


def _check_p1_cross_report(pairs: list[dict], p1_path: Path, problems: list[str]) -> dict:
    try:
        p1 = json.loads(p1_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"bad-p1-report:{exc}")
        return {}
    iter49_count = sum(
        p["off_primary_collision"] for p in pairs if p["dataset"] == "iter49_hard_extreme"
    )
    if p1.get("primary_opportunity_count") != iter49_count:
        problems.append(
            "p1-cross-check-count:"
            f"{p1.get('primary_opportunity_count')}!={iter49_count}"
        )
    return {
        "published_p1_count": p1.get("primary_opportunity_count"),
        "taxonomy_recomputed_count": iter49_count,
        "published_p1_branch": p1.get("p1_branch_given_iter49_verdict"),
    }


def run_analysis(args: argparse.Namespace) -> dict:
    problems: list[str] = []
    pairs = []
    pairs.extend(collect_dataset(
        "iter48_easy_medium",
        Path(args.iter48_episodes),
        Path(args.iter48_transfer_report),
        problems,
    ))
    pairs.extend(collect_dataset(
        "iter49_hard_extreme",
        Path(args.iter49_episodes),
        Path(args.iter49_transfer_report),
        problems,
    ))
    p1_cross_check = _check_p1_cross_report(pairs, Path(args.iter49_p1_report), problems)
    report = {
        "verdict": "TAXONOMY_INFRASTRUCTURE_NULL" if problems else "TAXONOMY_COMPLETE",
        "material_hd_bar": MATERIAL_HD_BAR,
        "dominance_bar": DOMINANCE_BAR,
        "category_order": list(CATEGORY_ORDER),
        "infrastructure_problems": problems,
        "p1_cross_check": p1_cross_check,
        "summaries": grouped_summaries(pairs) if not problems else {},
        "pairs": pairs if not problems else [],
    }
    return report


def render_pairs_markdown(report: dict) -> str:
    lines = [
        "| dataset | scenario | run | tier | attackplanner | category | "
        "HD off | HD on | delta | off nc min | on nc min | brake frames | "
        "first off NC t | first brake t |",
        "|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in report.get("pairs", []):
        lines.append(
            f"| {p['dataset']} | {p['scenario']} | {p['run']} | {p['tier']} | "
            f"{str(p['attackplanner']).lower()} | {p['category']} | "
            f"{p['hd_off']:.4f} | {p['hd_on']:.4f} | {p['delta_hd']:+.4f} | "
            f"{p['off_nc_min']:.4f} | {p['on_nc_min']:.4f} | {p['brake_frames']} | "
            f"{_fmt_optional(p['off_first_nc_time'])} | {_fmt_optional(p['first_brake_ts'])} |"
        )
    return "\n".join(lines)


def _fmt_optional(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter48-episodes", required=True)
    parser.add_argument("--iter48-transfer-report", required=True)
    parser.add_argument("--iter49-episodes", required=True)
    parser.add_argument("--iter49-transfer-report", required=True)
    parser.add_argument("--iter49-p1-report", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown-out", required=True)
    args = parser.parse_args()

    report = run_analysis(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(args.markdown_out).write_text(render_pairs_markdown(report) + "\n")

    print(f"iter51 taxonomy verdict: {report['verdict']}")
    if report["infrastructure_problems"]:
        print(f"infrastructure problems: {report['infrastructure_problems']}")
    else:
        combined = report["summaries"]["combined"]
        print(f"combined dominant category: {combined['dominant_category']} "
              f"({combined['dominant_category_fraction']:.3f})")
        print(f"category counts: {combined['category_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
