#!/usr/bin/env python3
"""Iteration 50 - offline collision-opportunity audit over committed evidence only.

Registered in HYPOTHESIS.md; run ONCE. Zero GPU, zero gcloud, zero box reads.

- Integrity gates first (iteration-40 frozen full14/power facts; HUGSIM set sizes and
  field presence). Any failure -> OPPORTUNITY_AUDIT_INFRASTRUCTURE_NULL, no A1/A2
  interpretation.
- A1 (NeuroNCAP): Spearman rho over the 20 full14/power pairs between OFF-arm collision
  rate (metrics.json `any_collide@0.0s`) and per-pair benefit (mean best - mean OFF
  ncap_score from the merged log); 10,000 pair-resampling bootstrap draws, Python
  `random` seeded 50; bars A1_CONFIRMED / A1_INVERTED / A1_ABSENT; stratified means at
  OFF collision rate >= 0.5 (support, no bar).
- A2 (HUGSIM easy+medium): primary opportunity per OFF episode = nc_min < 1.0 from that
  episode's eval.json (top-level `nc` and every `details.<t>.nc`); secondary near-miss
  proxy = not primary and ttc_min < 1.0 (descriptive only). Classifying set = iteration
  48's 52 OFF episodes; corroboration set = the iteration-46/47 52-episode baseline.
  Frozen bar: fraction < 0.25 -> OPPORTUNITY_SCARCE else OPPORTUNITY_PRESENT_NULL. The
  classification does not upgrade iteration 48's TRANSFER_NULL.
- Circularity guard: opportunity labels are computed from OFF-arm artifacts only; the
  opportunity reader refuses any path containing an ON-arm marker.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
from pathlib import Path

import numpy as np

BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 50
OPPORTUNITY_FRACTION_BAR = 0.25
A1_RHO_BAR = 0.5
STRATUM_SPLIT = 0.5
OFF_EXCEPTION = ("off", "side", "0921")  # n=19, carried iteration-40 frozen fact

PAIR_MARKER = re.compile(r"^##### P14PAIR (\w+) (\w+) (\d+)")
SCORE_LINE = re.compile(r"ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)")
METRICS_MEMBER = re.compile(r"^p14-(off|best)/([a-z]+)-(\d+)/run_(\d+)/metrics\.json$")


# ---------------------------------------------------------------------------
# HUGSIM opportunity (OFF arms only)
# ---------------------------------------------------------------------------

def _min_metric(ev: dict, field: str) -> float:
    """Min of the top-level field and every details.<t>.<field> value; raises on absence."""
    vals = [ev[field]]
    for step in ev.get("details", {}).values():
        vals.append(step[field])
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        raise ValueError(f"non-numeric {field}")
    return min(float(v) for v in vals)


def read_off_opportunity(eval_path: Path) -> dict:
    """Frozen opportunity labels for ONE OFF episode. Circularity guard enforced here."""
    if "__on_" in eval_path.as_posix():
        raise ValueError(f"circularity guard: ON-arm path passed to opportunity reader: {eval_path}")
    ev = json.loads(eval_path.read_text())
    nc_min = _min_metric(ev, "nc")
    ttc_min = _min_metric(ev, "ttc")
    primary = nc_min < 1.0
    return {
        "nc_min": nc_min,
        "ttc_min": ttc_min,
        "primary_opportunity": primary,
        "secondary_near_miss": (not primary) and ttc_min < 1.0,
        "hdscore": float(ev["hdscore"]),
    }


def episode_tier(scenario: str) -> str:
    m = re.search(r"-(easy|medium|hard|extreme)-", scenario)
    return m.group(1) if m else "unknown"


def collect_hugsim_set(entries: list[tuple[str, Path]], problems: list[str]) -> list[dict]:
    """entries: (episode_label, eval.json path). Returns per-episode opportunity rows."""
    rows = []
    for label, path in entries:
        if not path.exists():
            problems.append(f"missing-eval:{label}")
            continue
        try:
            rec = read_off_opportunity(path)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            problems.append(f"bad-eval:{label}:{exc}")
            continue
        scenario = label.split("__")[0]
        rows.append({"episode": label, "scenario": scenario, "tier": episode_tier(scenario), **rec})
    return rows


def summarize_set(rows: list[dict]) -> dict:
    n = len(rows)
    prim = sum(r["primary_opportunity"] for r in rows)
    sec = sum(r["secondary_near_miss"] for r in rows)
    tiers = {}
    for t in sorted({r["tier"] for r in rows}):
        sub = [r for r in rows if r["tier"] == t]
        tiers[t] = {
            "episodes": len(sub),
            "primary_opportunity": sum(r["primary_opportunity"] for r in sub),
            "secondary_near_miss": sum(r["secondary_near_miss"] for r in sub),
        }
    return {
        "episodes": n,
        "primary_opportunity_count": prim,
        "primary_opportunity_fraction": (prim / n) if n else None,
        "secondary_near_miss_count": sec,
        "per_tier": tiers,
    }


# ---------------------------------------------------------------------------
# NeuroNCAP side (full14/power committed evidence)
# ---------------------------------------------------------------------------

def read_tar_collisions(tar_path: Path, problems: list[str]) -> tuple[dict, dict]:
    """Return ({(scen, seq): [bool per OFF episode]}, counts) from p14-runs.tar.gz."""
    off: dict[tuple[str, str], list[bool]] = {}
    counts = {"off": 0, "best": 0}
    with tarfile.open(tar_path, "r:gz") as tf:
        for member in tf:
            m = METRICS_MEMBER.match(member.name)
            if not m:
                continue
            arm, scen, seq, _run = m.groups()
            counts[arm] += 1
            if arm != "off":
                continue
            try:
                metrics = json.load(tf.extractfile(member))
                off.setdefault((scen, seq), []).append(bool(metrics["any_collide@0.0s"]))
            except (KeyError, json.JSONDecodeError) as exc:
                problems.append(f"bad-metrics:{member.name}:{exc}")
    return off, counts


def parse_p14_log(path: Path) -> dict:
    """{(arm, scen, seq): [ncap_score, ...]} from the merged full14/power log."""
    scores: dict[tuple[str, str, str], list[float]] = {}
    arm = scen = seq = None
    for line in open(path, errors="replace"):
        m = PAIR_MARKER.search(line)
        if m:
            arm, scen, seq = m.groups()
            continue
        m = SCORE_LINE.search(line)
        if m and arm is not None:
            scores.setdefault((arm, scen, seq), []).append(float(m.group(1)))
    return scores


def _avg_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rho with average ranks; 0.0 on zero variance in either ranked vector."""
    rx, ry = _avg_ranks(x), _avg_ranks(y)
    ax, ay = np.array(rx), np.array(ry)
    sx, sy = ax.std(), ay.std()
    if sx == 0.0 or sy == 0.0:
        return 0.0
    return float(np.corrcoef(ax, ay)[0, 1])


def bootstrap_rho(x: list[float], y: list[float]) -> dict:
    import random

    rng = random.Random(BOOTSTRAP_SEED)
    n = len(x)
    rhos = []
    for _ in range(BOOTSTRAP_DRAWS):
        idx = [rng.randrange(n) for _ in range(n)]
        rhos.append(spearman([x[i] for i in idx], [y[i] for i in idx]))
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "point_rho": spearman(x, y),
        "rho_ci95": [float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))],
    }


def a1_verdict(point_rho: float, ci: list[float]) -> str:
    if point_rho >= A1_RHO_BAR and ci[0] > 0.0:
        return "A1_CONFIRMED"
    if ci[1] < 0.0:
        return "A1_INVERTED"
    return "A1_ABSENT"


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------

def hugsim_entries_iter48_off(root: Path) -> list[tuple[str, Path]]:
    return [(d.name, d / "eval.json") for d in sorted(root.iterdir())
            if d.is_dir() and "__off_r" in d.name]


def hugsim_entries_baseline(iter46_root: Path, iter47_root: Path) -> list[tuple[str, Path]]:
    entries = [(d.name, d / "eval.json") for d in sorted(iter46_root.iterdir())
               if d.is_dir() and not d.name.endswith("__failed")]
    entries += [(d.name, d / "eval.json") for d in sorted(iter47_root.iterdir()) if d.is_dir()]
    return entries


def paired_deltas_iter48(root: Path, off_rows: list[dict], problems: list[str]) -> list[dict]:
    """52 paired HD deltas stratified by the OFF episode's primary-opportunity label.

    ON-arm eval.json enters ONLY as the outcome side of the delta; opportunity labels come
    from the already-computed OFF rows.
    """
    by_episode = {r["episode"]: r for r in off_rows}
    out = []
    for off_label, off_row in sorted(by_episode.items()):
        on_label = off_label.replace("__off_r", "__on_r")
        on_path = root / on_label / "eval.json"
        if not on_path.exists():
            problems.append(f"missing-on-eval:{on_label}")
            continue
        on_hd = float(json.loads(on_path.read_text())["hdscore"])
        out.append({
            "pair": off_label.replace("__off_", "__"),
            "delta_hd": on_hd - off_row["hdscore"],
            "off_primary_opportunity": off_row["primary_opportunity"],
        })
    return out


def run_audit(args: argparse.Namespace) -> dict:
    problems: list[str] = []

    # --- HUGSIM sets ---
    h48_rows = collect_hugsim_set(hugsim_entries_iter48_off(Path(args.iter48_episodes)), problems)
    hbase_rows = collect_hugsim_set(
        hugsim_entries_baseline(Path(args.iter46_episodes), Path(args.iter47_episodes)), problems)
    if len(h48_rows) != 52:
        problems.append(f"h48-off-count:{len(h48_rows)}!=52")
    if len(hbase_rows) != 52:
        problems.append(f"hbase-count:{len(hbase_rows)}!=52")

    # --- full14/power ---
    analysis_txt = Path(args.p14_analysis).read_text(errors="replace")
    if "H-P0: PASS" not in analysis_txt:
        problems.append("p14-hp0-not-pass")
    off_coll, tar_counts = read_tar_collisions(Path(args.p14_tar), problems)
    if tar_counts != {"off": 399, "best": 400}:
        problems.append(f"p14-tar-counts:{tar_counts}!=off399/best400")
    if len(off_coll) != 20:
        problems.append(f"p14-off-pairs:{len(off_coll)}!=20")
    scores = parse_p14_log(Path(args.p14_log))
    pairs = sorted({(s, q) for (a, s, q) in scores if a == "off"})
    if len(pairs) != 20:
        problems.append(f"p14-log-pairs:{len(pairs)}!=20")
    for (scen, seq) in pairs:
        for arm in ("off", "best"):
            n = len(scores.get((arm, scen, seq), []))
            expected = 19 if (arm, scen, seq) == OFF_EXCEPTION else 20
            if n != expected:
                problems.append(f"p14-episode-count:{arm}:{scen}-{seq}:{n}!={expected}")
        n_coll = len(off_coll.get((scen, seq), []))
        expected = 19 if ("off", scen, seq) == OFF_EXCEPTION else 20
        if n_coll != expected:
            problems.append(f"p14-metrics-count:{scen}-{seq}:{n_coll}!={expected}")

    # --- iter48 published-mean cross-check + paired deltas ---
    pair_deltas = paired_deltas_iter48(Path(args.iter48_episodes), h48_rows, problems)
    if len(pair_deltas) != 52:
        problems.append(f"iter48-paired-deltas:{len(pair_deltas)}!=52")
    published = json.load(open(args.iter48_report))["primary"]["point_mean"]
    if pair_deltas:
        recomputed = float(np.mean([p["delta_hd"] for p in pair_deltas]))
        if abs(recomputed - published) > 1e-9:
            problems.append(f"iter48-mean-mismatch:{recomputed}!={published}")

    report: dict = {
        "iteration": 50,
        "frozen": {
            "opportunity_fraction_bar": OPPORTUNITY_FRACTION_BAR,
            "a1_rho_bar": A1_RHO_BAR,
            "stratum_split": STRATUM_SPLIT,
            "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED},
            "primary_definition": "OFF eval.json nc_min < 1.0 (top-level nc and all details.<t>.nc)",
            "secondary_definition": "not primary and ttc_min < 1.0 (descriptive only)",
            "neuroncap_definition": "OFF metrics.json any_collide@0.0s per-pair fraction",
        },
        "integrity": {"problems": problems, "p14_tar_counts": tar_counts},
    }
    if problems:
        report["verdict"] = "OPPORTUNITY_AUDIT_INFRASTRUCTURE_NULL"
        return report

    # --- A1 ---
    xs, ys, pair_table = [], [], []
    for (scen, seq) in pairs:
        colls = off_coll[(scen, seq)]
        rate = sum(colls) / len(colls)
        benefit = (float(np.mean(scores[("best", scen, seq)]))
                   - float(np.mean(scores[("off", scen, seq)])))
        xs.append(rate)
        ys.append(benefit)
        pair_table.append({"pair": f"{scen}-{seq}", "off_collision_rate": rate,
                           "off_n": len(colls), "benefit": benefit})
    boot = bootstrap_rho(xs, ys)
    hi = [p["benefit"] for p in pair_table if p["off_collision_rate"] >= STRATUM_SPLIT]
    lo = [p["benefit"] for p in pair_table if p["off_collision_rate"] < STRATUM_SPLIT]
    report["a1"] = {
        **boot,
        "verdict": a1_verdict(boot["point_rho"], boot["rho_ci95"]),
        "pairs": pair_table,
        "strata": {
            "high_opportunity": {"n": len(hi), "mean_benefit": float(np.mean(hi)) if hi else None},
            "low_opportunity": {"n": len(lo), "mean_benefit": float(np.mean(lo)) if lo else None},
            "difference": (float(np.mean(hi) - np.mean(lo)) if hi and lo else None),
        },
    }

    # --- A2 ---
    h48 = summarize_set(h48_rows)
    classification = ("OPPORTUNITY_SCARCE"
                      if h48["primary_opportunity_fraction"] < OPPORTUNITY_FRACTION_BAR
                      else "OPPORTUNITY_PRESENT_NULL")
    with_opp = [p["delta_hd"] for p in pair_deltas if p["off_primary_opportunity"]]
    without = [p["delta_hd"] for p in pair_deltas if not p["off_primary_opportunity"]]
    report["a2"] = {
        "h48_off": h48,
        "hbase": summarize_set(hbase_rows),
        "iter48_null_classification": classification,
        "classification_note": ("explanation of the null's domain, not an excuse; "
                                "iteration 48's TRANSFER_NULL stands as published"),
        "delta_stratification_descriptive": {
            "with_opportunity": {"n": len(with_opp),
                                 "mean_delta": float(np.mean(with_opp)) if with_opp else None,
                                 "median_delta": float(np.median(with_opp)) if with_opp else None},
            "without_opportunity": {"n": len(without),
                                    "mean_delta": float(np.mean(without)) if without else None,
                                    "median_delta": float(np.median(without)) if without else None},
        },
        "episodes_h48_off": h48_rows,
        "episodes_hbase": hbase_rows,
        "iter48_pair_deltas": pair_deltas,
    }
    report["verdict"] = "OPPORTUNITY_AUDIT_COMPLETE"
    return report


def write_markdown(report: dict, episodes_md: Path, pairs_md: Path) -> None:
    if report["verdict"] == "OPPORTUNITY_AUDIT_INFRASTRUCTURE_NULL":
        return
    lines = ["# Iteration 50 - HUGSIM OFF-episode opportunity (frozen primary: nc_min < 1.0)", ""]
    for name, key in [("H48-OFF (iteration-48 OFF arm)", "episodes_h48_off"),
                      ("HBASE (iteration-46/47 baseline)", "episodes_hbase")]:
        lines += [f"## {name}", "", "| episode | tier | nc_min | ttc_min | primary | near-miss |",
                  "|---|---|---:|---:|---|---|"]
        for r in report["a2"][key]:
            lines.append(f"| {r['episode']} | {r['tier']} | {r['nc_min']:.4f} | "
                         f"{r['ttc_min']:.4f} | {'YES' if r['primary_opportunity'] else 'no'} | "
                         f"{'yes' if r['secondary_near_miss'] else 'no'} |")
        lines.append("")
    episodes_md.write_text("\n".join(lines))

    lines = ["# Iteration 50 - full14/power per-pair OFF collision rate vs benefit", "",
             "| pair | OFF collision rate | OFF n | benefit (best - OFF) |", "|---|---:|---:|---:|"]
    for p in report["a1"]["pairs"]:
        lines.append(f"| {p['pair']} | {p['off_collision_rate']:.2f} | {p['off_n']} | "
                     f"{p['benefit']:+.3f} |")
    pairs_md.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p14-tar", default="experiments/full14_power/proof/p14-runs.tar.gz")
    ap.add_argument("--p14-log", default="experiments/full14_power/proof/sentinel-power14-merged.log")
    ap.add_argument("--p14-analysis", default="experiments/full14_power/proof/analysis_output.txt")
    ap.add_argument("--iter46-episodes",
                    default="experiments/iter46_hugsim_off_baseline/proof-off/episodes")
    ap.add_argument("--iter47-episodes",
                    default="experiments/iter47_map_staging_and_off_completion/proof-completion/episodes")
    ap.add_argument("--iter48-episodes",
                    default="experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes")
    ap.add_argument("--iter48-report",
                    default="experiments/iter48_hugsim_transfer_gate/proof-stage2/transfer_report.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--episodes-md-out", required=True)
    ap.add_argument("--pairs-md-out", required=True)
    args = ap.parse_args()

    report = run_audit(args)
    Path(args.out).write_text(json.dumps(report, indent=1))
    write_markdown(report, Path(args.episodes_md_out), Path(args.pairs_md_out))
    print(f"verdict: {report['verdict']}")
    if report["verdict"] == "OPPORTUNITY_AUDIT_COMPLETE":
        print(f"A1: {report['a1']['verdict']} rho={report['a1']['point_rho']:.4f} "
              f"ci={report['a1']['rho_ci95']}")
        h48 = report["a2"]["h48_off"]
        print(f"A2: {report['a2']['iter48_null_classification']} "
              f"({h48['primary_opportunity_count']}/{h48['episodes']} primary)")
    else:
        for p in report["integrity"]["problems"]:
            print(f"  problem: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
