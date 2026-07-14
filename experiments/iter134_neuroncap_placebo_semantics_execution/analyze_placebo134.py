#!/usr/bin/env python3
"""Iteration 134 analyzer: does the released union's NeuroNCAP gain need its risk semantics?

Frozen and hash-bound in the launch manifest BEFORE the first episode runs. One pass, over
committed artifacts only. Methodology is reused from experiments/full14_power/analyze_power14.py:
NCAP score is the mean of the three class means; safe-progress is the score scaled by
min(1, ego_path_len / this-run OFF-arm mean ego_path_len for that pair).

Gates first, then the verdict. The verdict function implements the four classes frozen by
iteration 133 and restated in HYPOTHESIS.md.

Usage:
  analyze_placebo134.py <i134 log> <i134 runs root> <committed p14 merged log>
                        <donor_schedules.json> <placebo decision log> <out report.json>
"""
import collections
import json
import math
import os
import random
import re
import sys

CLASSES = ["stationary", "frontal", "side"]
NRUNS = 20
ARMS = ["off", "union", "placebo"]
BOOT_DRAWS = 10000
BOOT_SEED = 134


def parse_log(path, marker):
    sc = collections.defaultdict(list)
    arm = scen = seq = None
    for line in open(path, errors="replace"):
        m = re.search(r"^##### " + marker + r" (\w+) (\w+) (\d+)", line)
        if m:
            arm, scen, seq = m.groups()
            continue
        m = re.search(r"ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)", line)
        if m and arm:
            sc[(arm, scen, seq)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def egos(root, tag, scen, seq):
    d = os.path.join(root, tag, f"{scen}-{seq}")
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, "ego_poses.json")
            if r.startswith("run_") and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split("_")[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


def realized_brakes(path):
    """(pair, run) -> realized brake frame count, from the placebo decision log."""
    out = collections.Counter()
    frames = collections.Counter()
    if not path or not os.path.exists(path):
        return out, frames
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        pair = row.get("pair")
        run = row.get("run")
        if pair is None or run is None:
            continue
        if row.get("brake"):
            out[(pair, run)] += 1
        elif row.get("frame"):
            frames[(pair, run)] += 1
    return out, frames


def main():
    (I134LOG, I134OUT, P14LOG, SCHEDJSON, PLACEBOLOG, OUTJSON) = sys.argv[1:7]
    random.seed(BOOT_SEED)
    SP = parse_log(I134LOG, "I134PAIR")
    P14 = parse_log(P14LOG, "P14PAIR")
    sched = json.load(open(SCHEDJSON))
    pairs = sorted({(scen, seq) for (a, scen, seq) in SP if a == "off"})

    problems = []
    report = {"schema": "iter134.placebo_semantics_execution.v1"}

    # ---- G4 completion -------------------------------------------------------------------
    counts = {arm: {f"{s}/{q}": len(SP.get((arm, s, q), [])) for s, q in pairs} for arm in ARMS}
    for arm in ARMS:
        total = sum(counts[arm].values())
        planned = len(pairs) * NRUNS
        report[f"{arm}_episodes"] = total
        if planned and total / planned < 0.95:
            problems.append(f"completion:{arm}:{total}/{planned}")
    if len(pairs) != 20:
        problems.append(f"pair-count:{len(pairs)}")

    # ---- G2 exact-reproduction drift gate ------------------------------------------------
    # committed p14 arm names: off, best. our carried arms: off, union.
    g2_mismatch = []
    for scen, seq in pairs:
        for arm, refarm in [("off", "off"), ("union", "best")]:
            new = [x[0] for x in SP.get((arm, scen, seq), [])]
            old = [x[0] for x in P14.get((refarm, scen, seq), [])]
            n = min(len(new), len(old))
            if n == 0:
                g2_mismatch.append(f"{arm}:{scen}-{seq}:no-overlap")
                continue
            if new[:n] != old[:n]:
                first = next((k for k in range(n) if new[k] != old[k]), None)
                g2_mismatch.append(f"{arm}:{scen}-{seq}:run{first}:new={new[first]}!=committed={old[first]}")
    report["g2_mismatch_count"] = len(g2_mismatch)
    report["g2_mismatches"] = g2_mismatch[:40]
    if g2_mismatch:
        problems.append(f"g2-drift:{len(g2_mismatch)}")

    # ---- data assembly -------------------------------------------------------------------
    data = {}
    for arm, tag in [("off", "i134-off"), ("union", "i134-union"), ("placebo", "i134-placebo")]:
        for scen, seq in pairs:
            runs = SP.get((arm, scen, seq), [])
            eg = egos(I134OUT, tag, scen, seq)
            data[(arm, scen, seq)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]

    off_ego_mean = {}
    for scen, seq in pairs:
        e = [x[2] for x in data[("off", scen, seq)] if x[2] is not None]
        off_ego_mean[(scen, seq)] = (sum(e) / len(e)) if e else 1.0

    def pooled(arm, pair_draw=None, idxs=None):
        use_pairs = pair_draw if pair_draw is not None else pairs
        class_score = {}
        pair_sp = []
        for scen in CLASSES:
            vals = []
            for s2, seq in use_pairs:
                if s2 != scen:
                    continue
                d = data[(arm, s2, seq)]
                if not d:
                    continue
                use = d if idxs is None else [d[i % len(d)] for i in idxs]
                vals += [x[0] for x in use]
                base = off_ego_mean[(s2, seq)] or 1.0
                sp = [x[0] * min(1.0, (x[2] or 0.0) / base) for x in use if x[2] is not None]
                if sp:
                    pair_sp.append(sum(sp) / len(sp))
            class_score[scen] = (sum(vals) / len(vals)) if vals else 0.0
        return (sum(class_score[s] for s in CLASSES) / 3,
                (sum(pair_sp) / len(pair_sp)) if pair_sp else 0.0)

    base_vals = {arm: pooled(arm) for arm in ARMS}
    for arm in ARMS:
        report[f"{arm}_ncap"] = round(base_vals[arm][0], 4)
        report[f"{arm}_safe_progress"] = round(base_vals[arm][1], 4)
        v = [x for (a, s2, q), d in data.items() if a == arm for x in d]
        report[f"{arm}_collision_rate"] = round(sum(1 for x in v if x[1] > 0) / max(len(v), 1), 4)

    def ci(deltas):
        s = sorted(deltas)
        lo = s[int(0.025 * len(s))]
        hi = s[int(0.975 * len(s)) - 1]
        return round(lo, 4), round(hi, 4)

    # PRIMARY: pair-clustered bootstrap (resample the 20 pairs with replacement), per HYPOTHESIS
    def clustered(a, b):
        d_nc = base_vals[a][0] - base_vals[b][0]
        d_sp = base_vals[a][1] - base_vals[b][1]
        bn, bs = [], []
        for _ in range(BOOT_DRAWS):
            draw = [pairs[random.randrange(len(pairs))] for _ in range(len(pairs))]
            pa, pb = pooled(a, pair_draw=draw), pooled(b, pair_draw=draw)
            bn.append(pa[0] - pb[0])
            bs.append(pa[1] - pb[1])
        return {"delta_ncap": round(d_nc, 4), "ci_ncap": ci(bn),
                "delta_safe_progress": round(d_sp, 4), "ci_safe_progress": ci(bs)}

    # COMPARABILITY: run-index resampling, the method behind the committed +0.783 headline
    def runidx(a, b):
        bn = []
        for _ in range(3000):
            idxs = [random.randrange(NRUNS) for _ in range(NRUNS)]
            bn.append(pooled(a, idxs=idxs)[0] - pooled(b, idxs=idxs)[0])
        return {"delta_ncap": round(base_vals[a][0] - base_vals[b][0], 4), "ci_ncap": ci(bn)}

    report["primary_union_minus_placebo"] = clustered("union", "placebo")
    report["secondary_placebo_minus_off"] = clustered("placebo", "off")
    report["secondary_union_minus_off"] = clustered("union", "off")
    report["comparability_runidx_union_minus_off"] = runidx("union", "off")
    report["comparability_runidx_union_minus_placebo"] = runidx("union", "placebo")

    # ---- realized vs scheduled budget (disclosure, not a gate) ---------------------------
    rb, rf = realized_brakes(PLACEBOLOG)
    scheduled_total = sched.get("scheduled_total_brake_frames")
    realized_total = sum(rb.values())
    report["placebo_scheduled_brake_frames"] = scheduled_total
    report["placebo_realized_brake_frames"] = realized_total
    report["placebo_realized_frames"] = sum(rf.values())
    if scheduled_total:
        report["placebo_budget_realization"] = round(realized_total / scheduled_total, 4)

    # ---- verdict -------------------------------------------------------------------------
    report["problem_count"] = len(problems)
    report["problems"] = problems
    up = report["primary_union_minus_placebo"]
    po = report["secondary_placebo_minus_off"]
    up_excl = up["ci_ncap"][0] > 0 or up["ci_ncap"][1] < 0
    po_excl = po["ci_ncap"][0] > 0 or po["ci_ncap"][1] < 0
    if problems:
        verdict = "PLACEBO_CONTROL_INFRA_NULL"
    elif up["delta_ncap"] > 0 and up_excl:
        verdict = "SEMANTIC_VALUE_CONFIRMED"
    elif po["delta_ncap"] > 0 and po_excl:
        verdict = "PLACEBO_EXPLAINS_GAIN"
    else:
        verdict = "PLACEBO_HARM_OR_NULL"
    report["verdict"] = verdict
    report["union_minus_placebo_ci_excludes_zero"] = up_excl
    report["placebo_minus_off_ci_excludes_zero"] = po_excl

    with open(OUTJSON, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)

    print(f"=== iteration 134 verdict: {verdict} ===")
    print(f"  G2 drift mismatches : {len(g2_mismatch)}")
    print("  episodes            : " + "  ".join(f"{a}={report[f'{a}_episodes']}" for a in ARMS))
    for a in ARMS:
        print(f"  {a:8s} NCAP {report[f'{a}_ncap']:.3f}  safe-prog {report[f'{a}_safe_progress']:.3f}"
              f"  coll {report[f'{a}_collision_rate'] * 100:.0f}%")
    print(f"  PRIMARY union-placebo {up['delta_ncap']:+.3f} CI {up['ci_ncap']} excl0={up_excl}")
    print(f"  placebo-off           {po['delta_ncap']:+.3f} CI {po['ci_ncap']} excl0={po_excl}")
    print(f"  union-off             {report['secondary_union_minus_off']['delta_ncap']:+.3f} "
          f"CI {report['secondary_union_minus_off']['ci_ncap']}")
    print(f"  placebo budget realized {realized_total}/{scheduled_total}")
    for p in problems[:10]:
        print("  problem:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
