#!/usr/bin/env python3
"""Iteration 48 offline paired analyzer — HUGSIM Stage-2 OFF vs released-union transfer gate.

Runs ONCE, offline, over the committed proof artifacts (episodes collected from the box-side
iter48_runs root plus receipts.json). Applies EXACTLY the frozen design of HYPOTHESIS.md:

- F1 first (retuning void): the receipts' echoed parameter block AND every decision-log
  params row must equal the seven NeuroNCAP-frozen values; any mismatch -> VOID_RETUNED,
  no transfer verdict.
- K1/K2 completion bars: all 104 scheduled episodes complete with finite hdscore after at
  most one retry, per-step logs present; ON episodes must carry the patch load marker and
  per-frame decision lines. Failure -> completion null, NOT a transfer verdict.
- Primary bar: 95% scenario-clustered bootstrap CI (26 clusters, 10,000 draws, seed 48) on
  the MEAN paired HD-Score delta (ON - OFF) over the 52 within-launch pairs.
- Heavy-tail treatment: MEDIAN paired delta with the same bootstrap draws, reported
  alongside; sign disagreement is a reported caveat, the mean stays primary.
- Secondaries (descriptive, NOT bars): paired deltas of nc/dac/ttc/comfort and rc; ON-arm
  firing statistics from the decision logs.
- Falsifiers: F2 (pooled ON brake frames > 80% of frames, or 0 fired frames over all 52 ON
  episodes -> transfer-boundary null), F3 (mean paired RC delta < -0.30 -> named finding),
  F4 (dual-failure episodes -> completion null), F5 (fresh OFF-OFF median |dHD| > 0.15 ->
  pairing finding; CI still reported, flagged noise-dominated).

Bars never move after data; no claim logic lives here beyond the registered bars.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

import numpy as np

SCENARIOS26: list[str] = [
    "scene-0013-easy-00", "scene-0013-medium-00",
    "scene-0038-easy-00", "scene-0038-medium-00", "scene-0038-medium-01",
    "scene-0041-easy-00", "scene-0041-medium-00", "scene-0041-medium-01",
    "scene-0051-easy-00", "scene-0051-medium-00", "scene-0051-medium-01",
    "scene-0062-easy-00", "scene-0062-medium-00", "scene-0062-medium-01",
    "scene-0064-easy-00", "scene-0064-medium-00", "scene-0064-medium-01",
    "scene-0071-easy-00", "scene-0071-medium-00", "scene-0071-medium-01",
    "scene-0138-easy-00", "scene-0138-medium-00", "scene-0138-medium-01",
    "scene-0166-easy-00", "scene-0166-medium-00", "scene-0166-medium-01",
]
RUNS = (1, 2)
ARMS = ("off", "on")

FROZEN_PARAMS = {
    "cpa_margin": 1.5,
    "ttc_thresh": 2.5,
    "min_closing": 3.0,
    "max_gap": 30.0,
    "min_score": 0.3,
    "release_k": 4,
    "dt": 0.5,
}
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 48
F2_BRAKE_FRAC_BAR = 0.80
F3_RC_DELTA_BAR = -0.30
F5_PAIRING_BAR = 0.15
TERMS = ("nc", "dac", "ttc", "c", "rc")


def load_episode(episodes_root: Path, scenario: str, arm: str, run_idx: int) -> dict:
    rec: dict = {"scenario": scenario, "arm": arm, "run": run_idx}
    ep_dir = episodes_root / f"{scenario}__{arm}_r{run_idx}"
    failed_dir = episodes_root / f"{scenario}__{arm}_r{run_idx}__failed"
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
        rec["hdscore"] = hd if isinstance(hd, (int, float)) else None
        rec["terms"] = {t: ev.get(t) for t in TERMS}
    except Exception:
        problems.append("eval-json-unreadable")
    try:
        meta = json.loads((ep_dir / "episode_meta.json").read_text())
        rec["steps"] = int(meta.get("steps", 0))
        rec["attempts"] = int(meta.get("attempt", 1))
        if meta.get("failed"):
            problems.append("meta-marked-failed")
        if rec["steps"] <= 0:
            problems.append("no-step-log")
    except Exception:
        problems.append("meta-unreadable")
    out_txt = ep_dir / "output.txt"
    if not out_txt.is_file():
        problems.append("output-txt-missing")
    else:
        text = out_txt.read_text(errors="replace")
        want = f"SENTINEL_I48_UNION_PATCH_LOADED enabled={1 if arm == 'on' else 0}"
        if want not in text:
            problems.append("patch-marker-missing")
        if arm == "on" and "SENTINEL_I48_DECISION frame=" not in text:
            problems.append("decision-lines-missing")
    if arm == "on":
        dec_path = ep_dir / "sentinel_iter48_decisions.jsonl"
        if not dec_path.is_file():
            problems.append("decision-jsonl-missing")
        else:
            rows = []
            for line in dec_path.read_text().splitlines():
                if line.strip():
                    rows.append(json.loads(line))
            rec["decisions"] = rows
            if not rows:
                problems.append("decision-jsonl-empty")
    rec["complete"] = not problems
    if problems:
        rec["reason"] = ",".join(problems)
    return rec


def params_match_frozen(params: dict) -> bool:
    if set(params.keys()) != set(FROZEN_PARAMS.keys()):
        return False
    return all(
        math.isclose(float(params[k]), float(v), rel_tol=0, abs_tol=1e-12)
        for k, v in FROZEN_PARAMS.items()
    )


def check_f1(receipts: dict, episodes: list[dict]) -> dict:
    problems = []
    rp = receipts.get("monitor_params")
    if not isinstance(rp, dict) or not params_match_frozen(rp):
        problems.append("receipts-params-mismatch")
    for e in episodes:
        if e["arm"] != "on":
            continue
        for row in e.get("decisions", []):
            if "trace_error" in row:
                continue
            if not params_match_frozen(row.get("params", {})):
                problems.append(
                    f"decision-params-mismatch:{e['scenario']}__on_r{e['run']}"
                    f":frame{row.get('frame_index')}"
                )
                break
    return {"fired": bool(problems), "problems": problems}


def clustered_bootstrap(deltas_by_cluster: list[list[float]]) -> dict:
    """Resample the scenario clusters with replacement; mean and median per draw."""
    n_clusters = len(deltas_by_cluster)
    arr = np.array(deltas_by_cluster, dtype=float)  # (clusters, pairs_per_cluster)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, n_clusters, size=(BOOTSTRAP_DRAWS, n_clusters))
    draws = arr[idx].reshape(BOOTSTRAP_DRAWS, -1)  # (draws, 52)
    means = draws.mean(axis=1)
    medians = np.median(draws, axis=1)
    flat = arr.reshape(-1)
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "clusters": n_clusters,
        "pairs": int(flat.size),
        "point_mean": float(flat.mean()),
        "point_median": float(np.median(flat)),
        "mean_ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "median_ci95": [float(np.percentile(medians, 2.5)),
                        float(np.percentile(medians, 97.5))],
    }


def firing_statistics(episodes: list[dict]) -> dict:
    total = fired = brake = releases = 0
    intervention_episodes = 0
    error_rows = 0
    for e in episodes:
        if e["arm"] != "on":
            continue
        ep_brake = 0
        for row in e.get("decisions", []):
            if "trace_error" in row:
                error_rows += 1
                continue
            total += 1
            fired += int(bool(row.get("fired")))
            b = int(bool(row.get("brake")))
            brake += b
            ep_brake += b
            releases += int(bool(row.get("release")))
        if ep_brake > 0:
            intervention_episodes += 1
    return {
        "monitor_frames": total,
        "fired_frames": fired,
        "brake_frames": brake,
        "releases": releases,
        "intervention_episodes": intervention_episodes,
        "trace_error_rows": error_rows,
        "brake_frame_fraction": (brake / total) if total else None,
    }


def analyze(episodes_root: Path, receipts_path: Path) -> dict:
    receipts = json.loads(receipts_path.read_text()) if receipts_path.is_file() else {}
    episodes = [
        load_episode(episodes_root, s, a, r)
        for s in SCENARIOS26 for r in RUNS for a in ARMS
    ]
    report: dict = {
        "design": {
            "scenarios": len(SCENARIOS26),
            "scheduled_episodes": len(episodes),
            "frozen_params": FROZEN_PARAMS,
            "primary": "mean paired HD delta (ON - OFF), scenario-clustered bootstrap CI",
        },
        "receipts": {k: receipts.get(k) for k in
                     ("monitor_params", "monitor_patch_sha", "e2e_py_patched_sha",
                      "e2e_sh_patched_sha", "carried_d0_verdict")},
    }

    # F1 — retuning void (checked before any bar).
    f1 = check_f1(receipts, episodes)
    report["falsifiers"] = {"F1_retuned": f1}
    if f1["fired"]:
        report["verdict"] = "VOID_RETUNED"
        return report

    # K1/K2 completion bars.
    incomplete = [e for e in episodes if not e["complete"]]
    dual_failures = [e for e in incomplete if e.get("reason") == "failed-both-attempts"]
    k1 = len(incomplete) == 0
    k2 = k1  # per-episode K2 substrate checks are folded into load_episode problems
    report["completion"] = {
        "scheduled": len(episodes),
        "complete": len(episodes) - len(incomplete),
        "incomplete": [
            {"scenario": e["scenario"], "arm": e["arm"], "run": e["run"],
             "reason": e.get("reason")} for e in incomplete
        ],
        "retried_episodes": sum(1 for e in episodes if e.get("attempts", 1) > 1),
    }
    report["falsifiers"]["F4_crash_loop"] = {
        "dual_failure_episodes": len(dual_failures),
        "fired": bool(dual_failures),
    }
    report["bars"] = {"K1_all_episodes_complete": k1, "K2_per_step_and_decision_logs": k2}
    if not (k1 and k2):
        report["verdict"] = "NULL_COMPLETION_BAR_FAILED"
        return report

    by_key = {(e["scenario"], e["arm"], e["run"]): e for e in episodes}

    # Paired HD deltas: 52 pairs in 26 scenario clusters.
    deltas_by_cluster: list[list[float]] = []
    pair_rows = []
    term_deltas: dict[str, list[float]] = {t: [] for t in TERMS}
    for s in SCENARIOS26:
        cluster = []
        for r in RUNS:
            off = by_key[(s, "off", r)]
            on = by_key[(s, "on", r)]
            d = float(on["hdscore"]) - float(off["hdscore"])
            cluster.append(d)
            pair_rows.append({
                "scenario": s, "run": r,
                "hd_off": float(off["hdscore"]), "hd_on": float(on["hdscore"]),
                "delta": d,
            })
            for t in TERMS:
                ov, nv = off["terms"].get(t), on["terms"].get(t)
                if isinstance(ov, (int, float)) and isinstance(nv, (int, float)):
                    term_deltas[t].append(float(nv) - float(ov))
        deltas_by_cluster.append(cluster)
    report["pairs"] = pair_rows

    boot = clustered_bootstrap(deltas_by_cluster)
    report["primary"] = boot
    lo, hi = boot["mean_ci95"]
    if lo > 0:
        primary_verdict = "PASS_TRANSFER_POSITIVE"
    elif hi < 0:
        primary_verdict = "TRANSFER_NEGATIVE"
    else:
        primary_verdict = "TRANSFER_NULL"
    mlo, mhi = boot["median_ci95"]
    mean_sign = 0 if lo <= 0 <= hi else (1 if lo > 0 else -1)
    median_sign = 0 if mlo <= 0 <= mhi else (1 if mlo > 0 else -1)
    report["heavy_tail_caveat"] = {
        "mean_median_ci_sign_disagreement": mean_sign != median_sign,
        "note": "verdict follows the pre-registered primary (mean); disagreement reported",
    }

    # Secondaries (descriptive, NOT bars).
    report["secondary_term_deltas"] = {
        t: {
            "mean": statistics.mean(v) if v else None,
            "median": statistics.median(v) if v else None,
            "n": len(v),
        } for t, v in term_deltas.items()
    }
    stats = firing_statistics(episodes)
    report["firing_statistics"] = stats

    # F2 — trigger mistuned for splat tracking noise (either direction, frozen detection).
    frac = stats["brake_frame_fraction"]
    f2_overfire = frac is not None and frac > F2_BRAKE_FRAC_BAR
    f2_neverfire = stats["fired_frames"] == 0
    report["falsifiers"]["F2_splat_noise_mistuned"] = {
        "brake_frame_fraction": frac,
        "over_fire_bar": F2_BRAKE_FRAC_BAR,
        "over_fire": f2_overfire,
        "never_fire": f2_neverfire,
        "fired": f2_overfire or f2_neverfire,
    }

    # F3 — over-braking (RC collapse); named finding, does not replace the primary verdict.
    rc_deltas = term_deltas["rc"]
    rc_mean = statistics.mean(rc_deltas) if rc_deltas else None
    report["falsifiers"]["F3_rc_collapse"] = {
        "mean_paired_rc_delta": rc_mean,
        "bar": F3_RC_DELTA_BAR,
        "fired": rc_mean is not None and rc_mean < F3_RC_DELTA_BAR,
    }

    # F5 — pairing infeasibility re-check on this run's fresh OFF-OFF pairs.
    off_off = []
    for s in SCENARIOS26:
        off_off.append(abs(float(by_key[(s, "off", 1)]["hdscore"])
                           - float(by_key[(s, "off", 2)]["hdscore"])))
    f5_med = statistics.median(off_off)
    f5_fired = f5_med > F5_PAIRING_BAR
    report["falsifiers"]["F5_pairing_infeasibility"] = {
        "median_abs_off_off_delta": f5_med,
        "bar": F5_PAIRING_BAR,
        "fired": f5_fired,
        "pairs_measured": len(off_off),
    }
    report["noise_dominated_flag"] = f5_fired

    if report["falsifiers"]["F2_splat_noise_mistuned"]["fired"]:
        mech = "OVER_FIRE" if f2_overfire else "NEVER_FIRE"
        report["verdict"] = f"TRANSFER_BOUNDARY_NULL_F2_{mech}"
        report["primary_ci_verdict_for_record"] = primary_verdict
    else:
        report["verdict"] = primary_verdict
    return report


def render_markdown(report: dict) -> str:
    lines = [
        "| scenario | run | HD off | HD on | delta (ON - OFF) |",
        "|---|---|---|---|---|",
    ]
    for p in report.get("pairs", []):
        lines.append(
            f"| {p['scenario']} | {p['run']} | {p['hd_off']:.4f} | "
            f"{p['hd_on']:.4f} | {p['delta']:+.4f} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", required=True,
                    help="directory containing the <scenario>__<arm>_r<n> episode dirs")
    ap.add_argument("--receipts", required=True, help="collected receipts.json")
    ap.add_argument("--out", required=True, help="JSON report output path")
    ap.add_argument("--markdown-out", help="optional per-pair markdown table")
    args = ap.parse_args()
    report = analyze(Path(args.episodes), Path(args.receipts))
    Path(args.out).write_text(json.dumps(report, indent=2, default=str) + "\n")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(report) + "\n")
    print(f"iter48 analyzer verdict: {report['verdict']}")
    print(f"bars: {report.get('bars')}")
    if "primary" in report:
        print(f"primary mean-delta CI95: {report['primary']['mean_ci95']} "
              f"(point {report['primary']['point_mean']:+.4f})")
        print(f"median-delta CI95: {report['primary']['median_ci95']} "
              f"(point {report['primary']['point_median']:+.4f})")
    if "firing_statistics" in report:
        print(f"firing: {report['firing_statistics']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
