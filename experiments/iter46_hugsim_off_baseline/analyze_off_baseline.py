#!/usr/bin/env python3
"""Iteration 46 offline analyzer — HUGSIM Stage-1 monitor-OFF baseline completion gate.

Runs ONCE, offline, over the collected run artifacts (the box-side collection root copied
into proof-off/). Checks the frozen completion bars C1/C2 and the registered falsifiers from
HYPOTHESIS.md, and emits the aggregate HD-Score table used by the plausibility note (context,
NOT a bar). It consumes only JSON/text artifacts (eval.json, output-step counts recorded in
episode_meta.json, d0_comparison.json); the heavy pickles stay on the box behind the SHA
manifest. No claim logic lives here beyond the registered bars.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

# Frozen scenario subset (lexicographic; mirrors HYPOTHESIS.md exactly).
SCENARIOS: list[str] = [
    "scene-0013-easy-00", "scene-0013-medium-00",
    "scene-0038-easy-00", "scene-0038-medium-00", "scene-0038-medium-01",
    "scene-0041-easy-00", "scene-0041-medium-00", "scene-0041-medium-01",
    "scene-0051-easy-00", "scene-0051-medium-00", "scene-0051-medium-01",
    "scene-0062-easy-00", "scene-0062-medium-00", "scene-0062-medium-01",
    "scene-0064-easy-00", "scene-0064-medium-00", "scene-0064-medium-01",
    "scene-0071-easy-00", "scene-0071-medium-00", "scene-0071-medium-01",
    "scene-0138-easy-00", "scene-0138-medium-00", "scene-0138-medium-01",
    "scene-0166-easy-00", "scene-0166-medium-00", "scene-0166-medium-01",
    "scene-0167-easy-00", "scene-0167-medium-00", "scene-0167-medium-01",
    "scene-0254-easy-00", "scene-0254-medium-00", "scene-0254-medium-01",
    "scene-0383-easy-00", "scene-0383-medium-00", "scene-0383-medium-01",
    "scene-0411-easy-00", "scene-0411-medium-00", "scene-0411-medium-01",
    "scene-0418-easy-00", "scene-0418-medium-00", "scene-0418-medium-01",
    "scene-0528-easy-00", "scene-0528-medium-00", "scene-0528-medium-01",
    "scene-0661-easy-00", "scene-0661-medium-00", "scene-0661-medium-01",
    "scene-0920-easy-00", "scene-0920-medium-00",
    "scene-0930-easy-00", "scene-0930-medium-00", "scene-0930-medium-01",
]
STOCHASTIC_SUBSET = SCENARIOS[:26]
PAIRING_DELTA_BAR = 0.15  # frozen falsifier bar: median within-scenario |dHD| (stochastic)


def scenario_tier(name: str) -> str:
    return "easy" if "-easy-" in name else "medium"


def scheduled_episodes(verdict: str) -> list[tuple[str, int]]:
    """The frozen schedule for a D0 branch: (scenario, run_idx) pairs."""
    if verdict == "deterministic":
        return [(s, 1) for s in SCENARIOS]
    return [(s, r) for s in STOCHASTIC_SUBSET for r in (1, 2)]


def load_episode(runs_root: Path, scenario: str, run_idx: int) -> dict:
    """Read one collected episode; returns a record with completion checks applied."""
    rec: dict = {"scenario": scenario, "run": run_idx, "tier": scenario_tier(scenario)}
    ep_dir = runs_root / f"{scenario}__r{run_idx}"
    failed_dir = runs_root / f"{scenario}__r{run_idx}__failed"
    if not ep_dir.is_dir():
        rec["complete"] = False
        rec["reason"] = "failed-both-attempts" if failed_dir.is_dir() else "missing"
        return rec
    problems = []
    try:
        ev = json.loads((ep_dir / "eval.json").read_text())
        hd = ev.get("hdscore")
        if not (isinstance(hd, (int, float)) and math.isfinite(hd)):
            problems.append("hdscore-not-finite")
        rec["eval"] = ev
        rec["hdscore"] = hd if isinstance(hd, (int, float)) else None
    except Exception:
        problems.append("eval-json-unreadable")
    try:
        meta = json.loads((ep_dir / "episode_meta.json").read_text())
        rec["meta"] = meta
        rec["steps"] = int(meta.get("steps", 0))
        rec["attempts"] = int(meta.get("attempt", 1))
        if rec["steps"] <= 0:
            problems.append("no-step-log")  # C2: per-step pairing substrate must exist
    except Exception:
        problems.append("meta-unreadable")
    if not (ep_dir / "output.txt").is_file():
        problems.append("output-txt-missing")  # C2
    rec["complete"] = not problems
    if problems:
        rec["reason"] = ",".join(problems)
    return rec


def analyze(runs_root: Path) -> dict:
    d0_path = runs_root / "d0_comparison.json"
    d0 = json.loads(d0_path.read_text()) if d0_path.is_file() else {"verdict": "missing"}
    verdict = d0.get("verdict", "missing")
    report: dict = {"d0": d0, "branch": verdict}
    if verdict not in ("deterministic", "stochastic"):
        report["bars"] = {"C1_all_episodes_complete": False, "C2_per_step_logs": False}
        report["verdict"] = "NULL_D0_MISSING"
        return report

    episodes = [load_episode(runs_root, s, r) for s, r in scheduled_episodes(verdict)]
    report["episodes"] = episodes
    incomplete = [e for e in episodes if not e["complete"]]
    c1 = len(incomplete) == 0
    c2 = all(e.get("steps", 0) > 0 and "output-txt-missing" not in e.get("reason", "")
             for e in episodes if e["complete"]) and c1
    retried = [e for e in episodes if e.get("attempts", 1) > 1]
    report["completion"] = {
        "scheduled": len(episodes),
        "complete": len(episodes) - len(incomplete),
        "incomplete": [
            {"scenario": e["scenario"], "run": e["run"], "reason": e.get("reason")}
            for e in incomplete
        ],
        "retried_episodes": len(retried),
    }

    scored = [e for e in episodes if e["complete"] and e.get("hdscore") is not None]
    if scored:
        by_tier: dict[str, list[float]] = {"easy": [], "medium": []}
        for e in scored:
            by_tier[e["tier"]].append(float(e["hdscore"]))
        all_scores = [float(e["hdscore"]) for e in scored]
        report["hdscore"] = {
            "mean": statistics.mean(all_scores),
            "median": statistics.median(all_scores),
            "per_tier_mean": {
                t: (statistics.mean(v) if v else None) for t, v in by_tier.items()
            },
            "n": len(all_scores),
            "plausibility_note": (
                "context only, NOT a bar: published RealADSim closed-loop anchors "
                "~0.30-0.42 HD-Score; scene sets/tiers/clients differ"
            ),
        }

    falsifiers: dict = {}
    if verdict == "stochastic":
        deltas = []
        for s in STOCHASTIC_SUBSET:
            pair = [e for e in scored if e["scenario"] == s]
            if len(pair) == 2:
                deltas.append(abs(float(pair[0]["hdscore"]) - float(pair[1]["hdscore"])))
        med = statistics.median(deltas) if deltas else None
        falsifiers["pairing_infeasibility"] = {
            "median_abs_delta_hd": med,
            "bar": PAIRING_DELTA_BAR,
            "fired": med is not None and med > PAIRING_DELTA_BAR,
            "pairs_measured": len(deltas),
        }
    falsifiers["crash_loop_dual_failures"] = {
        "count": sum(1 for e in incomplete if e.get("reason") == "failed-both-attempts"),
        "fired": any(e.get("reason") == "failed-both-attempts" for e in incomplete),
    }
    report["falsifiers"] = falsifiers

    bars = {"C1_all_episodes_complete": c1, "C2_per_step_logs": c2}
    report["bars"] = bars
    fired = [k for k, v in falsifiers.items() if v.get("fired")]
    if all(bars.values()) and not fired:
        report["verdict"] = "PASS_BARS_MET"
    else:
        report["verdict"] = "NULL_" + (
            "FALSIFIER_" + "_".join(fired).upper() if fired else "COMPLETION_BAR_FAILED"
        )
    return report


def render_markdown(report: dict) -> str:
    lines = ["| scenario | run | tier | hdscore | steps | complete |", "|---|---|---|---|---|---|"]
    for e in report.get("episodes", []):
        hd = e.get("hdscore")
        lines.append(
            f"| {e['scenario']} | {e['run']} | {e['tier']} | "
            f"{hd if hd is not None else '-'} | {e.get('steps', '-')} | "
            f"{'yes' if e['complete'] else 'NO: ' + str(e.get('reason'))} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--out", required=True, help="JSON report output path")
    ap.add_argument("--markdown-out", help="optional per-episode markdown table")
    args = ap.parse_args()
    report = analyze(Path(args.runs_root))
    Path(args.out).write_text(json.dumps(report, indent=2, default=str) + "\n")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(report) + "\n")
    print(f"iter46 analyzer verdict: {report['verdict']}")
    print(f"bars: {report.get('bars')}")
    if "hdscore" in report:
        print(f"hdscore aggregate: {report['hdscore']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
