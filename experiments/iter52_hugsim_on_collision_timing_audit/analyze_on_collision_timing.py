#!/usr/bin/env python3
"""Iteration 52 HUGSIM ON-collision timing audit.

Offline post-result audit over committed iteration-48/49 HUGSIM proof artifacts.
Implements HYPOTHESIS.md exactly:

- ON collision = min(top-level nc, details.*.nc) < 1.0.
- Timing bins use first ON collision time and first ON brake time.
- TTC/CPA surface proxy uses the frozen NeuroNCAP thresholds, but is not the full firing
  predicate.
- No GPU, no gcloud, no box reads, no retuning, no new safety claim.
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

PRIMARY_NC_BAR = 1.0
MATERIAL_HD_BAR = 0.03
TTC_THRESH = 2.5
CPA_MARGIN = 1.5
SHORT_LEAD_SECONDS = 1.0
EXPECTED_PAIRS_PER_DATASET = 52

TIMING_BINS = (
    "unknown_collision_time",
    "no_brake_no_surface_proxy",
    "no_brake_surface_proxy_present",
    "post_collision_first_brake",
    "short_lead_brake",
    "long_lead_brake",
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
    out = []
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


def read_decisions(path: Path) -> dict:
    monitor_frames = 0
    fired_frames = 0
    brake_frames = 0
    release_frames = 0
    surface_proxy_rows = 0
    first_brake_ts = None
    first_fire_ts = None
    first_surface_proxy_ts = None
    min_ttc = None
    min_cpa = None
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "trace_error" in row:
            continue
        monitor_frames += 1
        ts = _numeric(row.get("ts", row.get("frame_index", 0)), "ts")
        fired = bool(row.get("fired"))
        brake = bool(row.get("brake"))
        fired_frames += int(fired)
        brake_frames += int(brake)
        release_frames += int(bool(row.get("release")))
        if fired and first_fire_ts is None:
            first_fire_ts = ts
        if brake and first_brake_ts is None:
            first_brake_ts = ts
        row_ttc = row.get("min_ttc")
        row_cpa = row.get("min_cpa")
        if isinstance(row_ttc, (int, float)) and not isinstance(row_ttc, bool):
            min_ttc = float(row_ttc) if min_ttc is None else min(min_ttc, float(row_ttc))
        if isinstance(row_cpa, (int, float)) and not isinstance(row_cpa, bool):
            min_cpa = float(row_cpa) if min_cpa is None else min(min_cpa, float(row_cpa))
        if (
            isinstance(row_ttc, (int, float))
            and not isinstance(row_ttc, bool)
            and isinstance(row_cpa, (int, float))
            and not isinstance(row_cpa, bool)
            and float(row_ttc) <= TTC_THRESH
            and float(row_cpa) <= CPA_MARGIN
        ):
            surface_proxy_rows += 1
            if first_surface_proxy_ts is None:
                first_surface_proxy_ts = ts
    if monitor_frames == 0:
        raise ValueError("empty-decision-log")
    return {
        "monitor_frames": monitor_frames,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "release_frames": release_frames,
        "surface_proxy_rows": surface_proxy_rows,
        "first_brake_ts": first_brake_ts,
        "first_fire_ts": first_fire_ts,
        "first_surface_proxy_ts": first_surface_proxy_ts,
        "min_monitor_ttc": min_ttc,
        "min_monitor_cpa": min_cpa,
    }


def scenario_tier(scenario: str) -> str:
    match = TIER_RE.search(scenario)
    return match.group(1) if match else "unknown"


def is_attackplanner_scenario(scenario: str) -> bool:
    return "-extreme-" in scenario or scenario in ATTACKPLANNER_HARD_SCENARIOS


def assign_timing_bin(row: dict) -> str:
    if not row["on_collision"]:
        return "excluded_no_on_collision"
    if row["first_on_nc_time"] is None:
        return "unknown_collision_time"
    if row["brake_frames"] == 0:
        if row["surface_proxy_rows"] == 0:
            return "no_brake_no_surface_proxy"
        return "no_brake_surface_proxy_present"
    first_brake = row["first_brake_ts"]
    if first_brake is None:
        raise ValueError("brake_frames_positive_without_first_brake_ts")
    if first_brake > row["first_on_nc_time"]:
        return "post_collision_first_brake"
    lead = row["first_on_nc_time"] - first_brake
    if 0.0 <= lead <= SHORT_LEAD_SECONDS:
        return "short_lead_brake"
    if lead > SHORT_LEAD_SECONDS:
        return "long_lead_brake"
    raise ValueError(f"negative-lead:{lead}")


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
            row["lead_time"] = (
                row["first_on_nc_time"] - row["first_brake_ts"]
                if row["on_collision"]
                and row["first_on_nc_time"] is not None
                and row["first_brake_ts"] is not None
                else None
            )
            row["timing_bin"] = assign_timing_bin(row)
            row["material_gain"] = row["delta_hd"] > MATERIAL_HD_BAR
            row["material_loss"] = row["delta_hd"] < -MATERIAL_HD_BAR
            rows.append(row)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            problems.append(f"{dataset}:{scenario}:r{run}:{exc}")
    if len(rows) != EXPECTED_PAIRS_PER_DATASET:
        problems.append(f"{dataset}:pair-count:{len(rows)}!={EXPECTED_PAIRS_PER_DATASET}")
    return rows


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize(rows: list[dict]) -> dict:
    on_rows = [r for r in rows if r["on_collision"]]
    counts = Counter(r["timing_bin"] for r in on_rows)
    absent_or_post = (
        counts["no_brake_no_surface_proxy"]
        + counts["no_brake_surface_proxy_present"]
        + counts["post_collision_first_brake"]
    )
    pre_collision = counts["short_lead_brake"] + counts["long_lead_brake"]
    by_bin = {}
    for timing_bin in TIMING_BINS:
        sub = [r for r in on_rows if r["timing_bin"] == timing_bin]
        by_bin[timing_bin] = {
            "count": len(sub),
            "mean_delta_hd": _mean([r["delta_hd"] for r in sub]),
            "median_delta_hd": _median([r["delta_hd"] for r in sub]),
            "material_gain_pairs": sum(r["material_gain"] for r in sub),
            "material_loss_pairs": sum(r["material_loss"] for r in sub),
            "median_lead_time": _median([
                r["lead_time"] for r in sub if r["lead_time"] is not None
            ]),
            "mean_brake_frames": _mean([float(r["brake_frames"]) for r in sub]),
        }
    return {
        "pairs": len(rows),
        "on_collision_pairs": len(on_rows),
        "excluded_no_on_collision": len(rows) - len(on_rows),
        "timing_bin_counts": {name: counts.get(name, 0) for name in TIMING_BINS},
        "absent_or_post_collision_brake_family": absent_or_post,
        "pre_collision_brake_family": pre_collision,
        "material_gain_pairs": sum(r["material_gain"] for r in on_rows),
        "material_loss_pairs": sum(r["material_loss"] for r in on_rows),
        "bin_stats": by_bin,
    }


def grouped_summaries(rows: list[dict]) -> dict:
    by_dataset = {
        dataset: summarize([r for r in rows if r["dataset"] == dataset])
        for dataset in sorted({r["dataset"] for r in rows})
    }
    iter49 = [r for r in rows if r["dataset"] == "iter49_hard_extreme"]
    return {
        "combined": summarize(rows),
        "by_dataset": by_dataset,
        "iter49_attackplanner": {
            "attackplanner": summarize([r for r in iter49 if r["attackplanner"]]),
            "non_attackplanner": summarize([r for r in iter49 if not r["attackplanner"]]),
        },
    }


def check_iter51_cross_report(rows: list[dict], iter51_report: Path, problems: list[str]) -> dict:
    try:
        report = json.loads(iter51_report.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"bad-iter51-report:{exc}")
        return {}
    iter51_pairs = report.get("pairs", [])
    expected_pairs = len(iter51_pairs)
    expected_on_collisions = sum(bool(r.get("on_primary_collision")) for r in iter51_pairs)
    observed_on_collisions = sum(r["on_collision"] for r in rows)
    if expected_pairs != len(rows):
        problems.append(f"iter51-pair-count:{expected_pairs}!={len(rows)}")
    if expected_on_collisions != observed_on_collisions:
        problems.append(
            f"iter51-on-collision-count:{expected_on_collisions}!={observed_on_collisions}"
        )
    return {
        "iter51_pairs": expected_pairs,
        "timing_pairs": len(rows),
        "iter51_on_collision_pairs": expected_on_collisions,
        "timing_on_collision_pairs": observed_on_collisions,
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
    cross = check_iter51_cross_report(rows, Path(args.iter51_report), problems)
    return {
        "verdict": "TIMING_AUDIT_INFRASTRUCTURE_NULL" if problems else "TIMING_AUDIT_COMPLETE",
        "process_disclosure": {
            "prototype_probe_disclosed_in_hypothesis": True,
            "no_inferential_surprise_claim": True,
        },
        "constants": {
            "primary_nc_bar": PRIMARY_NC_BAR,
            "material_hd_bar": MATERIAL_HD_BAR,
            "ttc_thresh": TTC_THRESH,
            "cpa_margin": CPA_MARGIN,
            "short_lead_seconds": SHORT_LEAD_SECONDS,
        },
        "infrastructure_problems": problems,
        "iter51_cross_check": cross,
        "summaries": grouped_summaries(rows) if not problems else {},
        "pairs": rows if not problems else [],
    }


def _fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def render_markdown(report: dict) -> str:
    lines = [
        "| dataset | scenario | run | tier | attackplanner | timing bin | "
        "HD off | HD on | delta | on nc min | first ON NC t | first brake t | "
        "lead | brake frames | surface proxy rows |",
        "|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report.get("pairs", []):
        lines.append(
            f"| {row['dataset']} | {row['scenario']} | {row['run']} | {row['tier']} | "
            f"{str(row['attackplanner']).lower()} | {row['timing_bin']} | "
            f"{row['hd_off']:.4f} | {row['hd_on']:.4f} | {row['delta_hd']:+.4f} | "
            f"{row['on_nc_min']:.4f} | {_fmt(row['first_on_nc_time'])} | "
            f"{_fmt(row['first_brake_ts'])} | {_fmt(row['lead_time'])} | "
            f"{row['brake_frames']} | {row['surface_proxy_rows']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter48-episodes", required=True)
    parser.add_argument("--iter49-episodes", required=True)
    parser.add_argument("--iter51-report", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown-out", required=True)
    args = parser.parse_args()
    report = run_analysis(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(args.markdown_out).write_text(render_markdown(report) + "\n")
    print(f"iter52 timing audit verdict: {report['verdict']}")
    if report["infrastructure_problems"]:
        print(f"infrastructure problems: {report['infrastructure_problems']}")
    else:
        combined = report["summaries"]["combined"]
        print(f"combined timing bins: {combined['timing_bin_counts']}")
        print("families: "
              f"absent/post={combined['absent_or_post_collision_brake_family']} "
              f"pre={combined['pre_collision_brake_family']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
