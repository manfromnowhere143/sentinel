#!/usr/bin/env python3
"""Iteration 53 HUGSIM first-fire channel audit.

Offline post-result audit over committed iteration-48/49 HUGSIM proof artifacts.
Classifies the released union's first fired row as TTC-only, CPA-only, both, or no-fire,
then crosses that with ON-collision timing and iteration-52 timing bins.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PRIMARY_NC_BAR = 1.0
MATERIAL_HD_BAR = 0.03
TTC_THRESH = 2.5
CPA_MARGIN = 1.5
SHORT_LEAD_SECONDS = 1.0
EXPECTED_PAIRS_PER_DATASET = 52

CHANNELS = (
    "ttc_only",
    "cpa_only",
    "both",
    "no_fire",
    "fired_channel_unreconstructable",
)
FIRE_TIMING_LABELS = (
    "no_on_collision",
    "unknown_collision_time",
    "no_fire",
    "post_collision_fire",
    "short_lead_fire",
    "long_lead_fire",
)
ITER52_TIMING_BINS = (
    "unknown_collision_time",
    "no_brake_no_surface_proxy",
    "no_brake_surface_proxy_present",
    "post_collision_first_brake",
    "short_lead_brake",
    "long_lead_brake",
    "excluded_no_on_collision",
)
PAIR_RE = re.compile(r"^(?P<scenario>.+)__on_r(?P<run>[12])$")
TIER_RE = re.compile(r"-(easy|medium|hard|extreme)-")
ATTACKPLANNER_HARD_SCENARIOS = {"scene-0041-hard-00", "scene-0411-hard-00"}


def _numeric(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"non-numeric {field}")
    return float(value)


def _details_items(ev: dict) -> list[tuple[float, dict]]:
    details = ev.get("details", {})
    if not isinstance(details, dict):
        raise ValueError("details-not-dict")
    out: list[tuple[float, dict]] = []
    for key, row in details.items():
        try:
            t = float(key)
        except ValueError as exc:
            raise ValueError(f"bad-details-time:{key}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"details-row-not-dict:{key}")
        out.append((t, row))
    return sorted(out, key=lambda item: item[0])


def read_eval(path: Path) -> dict:
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
        "collision": nc_min < PRIMARY_NC_BAR,
        "first_nc_time": first_nc_time,
        "first_nc_source": first_nc_source,
    }


def first_fire_channel(row: dict) -> str:
    ttc = _numeric(row.get("min_ttc"), "min_ttc")
    cpa = _numeric(row.get("min_cpa"), "min_cpa")
    ttc_cross = ttc < TTC_THRESH
    cpa_cross = cpa < CPA_MARGIN
    if ttc_cross and cpa_cross:
        return "both"
    if ttc_cross:
        return "ttc_only"
    if cpa_cross:
        return "cpa_only"
    return "fired_channel_unreconstructable"


def read_decisions(path: Path) -> dict:
    monitor_frames = 0
    fired_frames = 0
    brake_frames = 0
    release_frames = 0
    first_fire = None
    first_brake_ts = None
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "trace_error" in row:
            continue
        monitor_frames += 1
        fired = bool(row.get("fired"))
        brake = bool(row.get("brake"))
        fired_frames += int(fired)
        brake_frames += int(brake)
        release_frames += int(bool(row.get("release")))
        ts = _numeric(row.get("ts", row.get("frame_index", 0)), "ts")
        if fired and first_fire is None:
            first_fire = {
                "first_fire_ts": ts,
                "first_fire_channel": first_fire_channel(row),
                "first_fire_min_ttc": _numeric(row.get("min_ttc"), "min_ttc"),
                "first_fire_min_cpa": _numeric(row.get("min_cpa"), "min_cpa"),
                "first_fire_frame_index": int(row.get("frame_index", -1)),
                "first_fire_pre_braking": bool(row.get("pre_braking")),
            }
        if brake and first_brake_ts is None:
            first_brake_ts = ts
    if monitor_frames == 0:
        raise ValueError("empty-decision-log")
    if first_fire is None:
        first_fire = {
            "first_fire_ts": None,
            "first_fire_channel": "no_fire",
            "first_fire_min_ttc": None,
            "first_fire_min_cpa": None,
            "first_fire_frame_index": None,
            "first_fire_pre_braking": None,
        }
    return {
        "monitor_frames": monitor_frames,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "release_frames": release_frames,
        "first_brake_ts": first_brake_ts,
        **first_fire,
    }


def fire_timing_label(row: dict) -> str:
    if not row["on_collision"]:
        return "no_on_collision"
    if row["first_on_nc_time"] is None:
        return "unknown_collision_time"
    if row["first_fire_channel"] == "no_fire":
        return "no_fire"
    first_fire = row["first_fire_ts"]
    if first_fire is None:
        raise ValueError("fire-channel-without-time")
    if first_fire > row["first_on_nc_time"]:
        return "post_collision_fire"
    lead = row["first_on_nc_time"] - first_fire
    if 0.0 <= lead <= SHORT_LEAD_SECONDS:
        return "short_lead_fire"
    if lead > SHORT_LEAD_SECONDS:
        return "long_lead_fire"
    raise ValueError(f"negative-lead:{lead}")


def iter52_timing_bin_from_current(row: dict) -> str:
    if not row["on_collision"]:
        return "excluded_no_on_collision"
    if row["first_on_nc_time"] is None:
        return "unknown_collision_time"
    if row["brake_frames"] == 0:
        return "no_brake_no_surface_proxy"
    first_brake = row["first_brake_ts"]
    if first_brake is None:
        raise ValueError("brake-frames-without-first-brake-ts")
    if first_brake > row["first_on_nc_time"]:
        return "post_collision_first_brake"
    lead = row["first_on_nc_time"] - first_brake
    if 0.0 <= lead <= SHORT_LEAD_SECONDS:
        return "short_lead_brake"
    if lead > SHORT_LEAD_SECONDS:
        return "long_lead_brake"
    raise ValueError(f"negative-brake-lead:{lead}")


def scenario_tier(scenario: str) -> str:
    match = TIER_RE.search(scenario)
    return match.group(1) if match else "unknown"


def is_attackplanner_scenario(scenario: str) -> bool:
    return "-extreme-" in scenario or scenario in ATTACKPLANNER_HARD_SCENARIOS


def collect_dataset(dataset: str, episodes_root: Path, problems: list[str]) -> list[dict]:
    rows = []
    for on_dir in sorted(episodes_root.iterdir()):
        if not on_dir.is_dir() or "__on_r" not in on_dir.name:
            continue
        match = PAIR_RE.match(on_dir.name)
        if not match:
            problems.append(f"{dataset}:bad-on-dir-name:{on_dir.name}")
            continue
        scenario = match.group("scenario")
        run = int(match.group("run"))
        off_dir = episodes_root / f"{scenario}__off_r{run}"
        try:
            on_eval = read_eval(on_dir / "eval.json")
            off_eval = read_eval(off_dir / "eval.json")
            decisions = read_decisions(on_dir / "sentinel_iter48_decisions.jsonl")
            row = {
                "dataset": dataset,
                "scenario": scenario,
                "run": run,
                "tier": scenario_tier(scenario),
                "attackplanner": is_attackplanner_scenario(scenario),
                "hd_off": off_eval["hdscore"],
                "hd_on": on_eval["hdscore"],
                "delta_hd": on_eval["hdscore"] - off_eval["hdscore"],
                "on_nc_min": on_eval["nc_min"],
                "on_collision": on_eval["collision"],
                "first_on_nc_time": on_eval["first_nc_time"],
                "first_on_nc_source": on_eval["first_nc_source"],
                **decisions,
            }
            row["first_fire_lead_time"] = (
                row["first_on_nc_time"] - row["first_fire_ts"]
                if row["on_collision"]
                and row["first_on_nc_time"] is not None
                and row["first_fire_ts"] is not None
                else None
            )
            row["fire_timing_label"] = fire_timing_label(row)
            row["iter52_timing_bin_recomputed"] = iter52_timing_bin_from_current(row)
            row["material_gain"] = row["delta_hd"] > MATERIAL_HD_BAR
            row["material_loss"] = row["delta_hd"] < -MATERIAL_HD_BAR
            rows.append(row)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            problems.append(f"{dataset}:{scenario}:r{run}:{exc}")
    if len(rows) != EXPECTED_PAIRS_PER_DATASET:
        problems.append(f"{dataset}:pair-count:{len(rows)}!={EXPECTED_PAIRS_PER_DATASET}")
    return rows


def key_for(row: dict) -> str:
    return f"{row['dataset']}::{row['scenario']}::r{row['run']}"


def check_iter52(rows: list[dict], iter52_report: Path, problems: list[str]) -> dict:
    try:
        report = json.loads(iter52_report.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"bad-iter52-report:{exc}")
        return {}
    iter52_pairs = report.get("pairs", [])
    expected = {key_for(row): row for row in iter52_pairs}
    observed = {key_for(row): row for row in rows}
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    if missing:
        problems.append(f"iter52-missing-keys:{missing[:5]}")
    if extra:
        problems.append(f"iter52-extra-keys:{extra[:5]}")
    mismatches = []
    for key in sorted(set(expected) & set(observed)):
        want = expected[key].get("timing_bin")
        got = observed[key].get("iter52_timing_bin_recomputed")
        if want != got:
            mismatches.append(f"{key}:{want}!={got}")
    if mismatches:
        problems.append(f"iter52-timing-bin-mismatches:{mismatches[:5]}")
    return {
        "iter52_pairs": len(iter52_pairs),
        "channel_pairs": len(rows),
        "timing_bin_mismatches": len(mismatches),
    }


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _counter_dict(counter: Counter, names: tuple[str, ...]) -> dict:
    return {name: counter.get(name, 0) for name in names}


def summarize(rows: list[dict]) -> dict:
    channel_counts = Counter(row["first_fire_channel"] for row in rows)
    on_rows = [row for row in rows if row["on_collision"]]
    on_channel_counts = Counter(row["first_fire_channel"] for row in on_rows)
    timing_counts = Counter(row["fire_timing_label"] for row in rows)
    pre_fire = [
        row for row in on_rows
        if row["fire_timing_label"] in ("short_lead_fire", "long_lead_fire")
    ]
    by_channel = {}
    for channel in CHANNELS:
        sub = [row for row in on_rows if row["first_fire_channel"] == channel]
        by_channel[channel] = {
            "on_collision_count": len(sub),
            "mean_delta_hd": _mean([row["delta_hd"] for row in sub]),
            "median_delta_hd": _median([row["delta_hd"] for row in sub]),
            "material_gain_pairs": sum(row["material_gain"] for row in sub),
            "material_loss_pairs": sum(row["material_loss"] for row in sub),
            "median_first_fire_lead_time": _median([
                row["first_fire_lead_time"] for row in sub
                if row["first_fire_lead_time"] is not None
            ]),
        }
    iter52_cross: dict[str, dict[str, int]] = {}
    by_bin: defaultdict[str, Counter] = defaultdict(Counter)
    for row in rows:
        by_bin[row["iter52_timing_bin_recomputed"]][row["first_fire_channel"]] += 1
    for timing_bin in ITER52_TIMING_BINS:
        iter52_cross[timing_bin] = _counter_dict(by_bin[timing_bin], CHANNELS)
    return {
        "pairs": len(rows),
        "on_collision_pairs": len(on_rows),
        "channel_counts_all_pairs": _counter_dict(channel_counts, CHANNELS),
        "channel_counts_on_collisions": _counter_dict(on_channel_counts, CHANNELS),
        "fire_timing_counts": _counter_dict(timing_counts, FIRE_TIMING_LABELS),
        "pre_collision_fire_pairs": len(pre_fire),
        "pre_collision_fire_channel_counts": _counter_dict(
            Counter(row["first_fire_channel"] for row in pre_fire), CHANNELS,
        ),
        "channel_delta_stats": by_channel,
        "iter52_timing_bin_x_first_fire_channel": iter52_cross,
    }


def grouped_summaries(rows: list[dict]) -> dict:
    by_dataset = {
        dataset: summarize([row for row in rows if row["dataset"] == dataset])
        for dataset in sorted({row["dataset"] for row in rows})
    }
    iter49 = [row for row in rows if row["dataset"] == "iter49_hard_extreme"]
    return {
        "combined": summarize(rows),
        "by_dataset": by_dataset,
        "iter49_attackplanner": {
            "attackplanner": summarize([row for row in iter49 if row["attackplanner"]]),
            "non_attackplanner": summarize([row for row in iter49 if not row["attackplanner"]]),
        },
    }


def run_analysis(args: argparse.Namespace) -> dict:
    problems: list[str] = []
    rows = []
    rows.extend(collect_dataset(
        "iter48_easy_medium", Path(args.iter48_episodes), problems,
    ))
    rows.extend(collect_dataset(
        "iter49_hard_extreme", Path(args.iter49_episodes), problems,
    ))
    iter52_cross = check_iter52(rows, Path(args.iter52_report), problems)
    return {
        "verdict": (
            "FIRST_FIRE_CHANNEL_INFRASTRUCTURE_NULL"
            if problems else "FIRST_FIRE_CHANNEL_COMPLETE"
        ),
        "process_disclosure": {
            "patch_inspection_disclosed_in_hypothesis": True,
            "prototype_probe_disclosed_in_hypothesis": True,
            "no_inferential_surprise_claim": True,
        },
        "constants": {
            "ttc_thresh": TTC_THRESH,
            "cpa_margin": CPA_MARGIN,
            "primary_nc_bar": PRIMARY_NC_BAR,
            "material_hd_bar": MATERIAL_HD_BAR,
            "short_lead_seconds": SHORT_LEAD_SECONDS,
        },
        "infrastructure_problems": problems,
        "iter52_cross_check": iter52_cross,
        "summaries": grouped_summaries(rows) if not problems else {},
        "pairs": rows if not problems else [],
    }


def _fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def render_markdown(report: dict) -> str:
    lines = [
        "| dataset | scenario | run | tier | attackplanner | iter52 timing bin | "
        "fire timing | first-fire channel | HD off | HD on | delta | first ON NC t | "
        "first fire t | fire lead | first min TTC | first min CPA | fired frames | brake frames |",
        "|---|---|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report.get("pairs", []):
        lines.append(
            f"| {row['dataset']} | {row['scenario']} | {row['run']} | {row['tier']} | "
            f"{str(row['attackplanner']).lower()} | {row['iter52_timing_bin_recomputed']} | "
            f"{row['fire_timing_label']} | {row['first_fire_channel']} | "
            f"{row['hd_off']:.4f} | {row['hd_on']:.4f} | {row['delta_hd']:+.4f} | "
            f"{_fmt(row['first_on_nc_time'])} | {_fmt(row['first_fire_ts'])} | "
            f"{_fmt(row['first_fire_lead_time'])} | {_fmt(row['first_fire_min_ttc'])} | "
            f"{_fmt(row['first_fire_min_cpa'])} | {row['fired_frames']} | {row['brake_frames']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter48-episodes", required=True)
    parser.add_argument("--iter49-episodes", required=True)
    parser.add_argument("--iter52-report", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown-out", required=True)
    args = parser.parse_args()
    report = run_analysis(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(args.markdown_out).write_text(render_markdown(report) + "\n")
    print(f"iter53 first-fire audit verdict: {report['verdict']}")
    if report["infrastructure_problems"]:
        print(f"infrastructure problems: {report['infrastructure_problems']}")
    else:
        combined = report["summaries"]["combined"]
        print(f"on-collision first-fire channels: "
              f"{combined['channel_counts_on_collisions']}")
        print(f"pre-collision fire channels: "
              f"{combined['pre_collision_fire_channel_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
