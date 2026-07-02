#!/usr/bin/env python3
"""H-VAD-1 — does the union transfer to a frozen VAD? OFF vs union, 20 unique episodes/scene.

VAD's OFF arm is its own baseline (a planner with a built-in collision optimizer — a *defended*
baseline, per the pre-registration). Per-scene score / collision% / ego progress; pooled
safe-progress normalized to VAD-OFF means; within-scene bootstrap CI on (union - OFF).

Usage: analyze_vad.py <sentinel-vad20.log> <vad20-runs-root>
"""
import collections
import json
import math
import os
import random
import re
import sys

random.seed(20260702)
LOG, OUT = sys.argv[1], sys.argv[2]
SCENES = ['stationary-0103', 'frontal-0103', 'side-0103']


def scores_from_log():
    sc = collections.defaultdict(list)
    arm = scene = None
    for line in open(LOG, errors='replace'):
        m = re.search(r'VAD20PAIR (\w+) (\w+) (\d+)', line)
        if m:
            arm, scene = m.group(1), m.group(2) + '-' + m.group(3)
            continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scene)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def egos(arm, scene):
    d = os.path.join(OUT, f'vad20-{arm}', scene)
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, 'ego_poses.json')
            if r.startswith('run_') and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split('_')[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


S = scores_from_log()
data = {}
print('=== per-arm, per-scene (n, mean score, collision%, mean ego m) ===')
for arm in ('off', 'union'):
    for scene in SCENES:
        runs = S.get((arm, scene), [])
        eg = egos(arm, scene)
        data[(arm, scene)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]
        n = len(runs) or 1
        ms = sum(r[0] for r in runs) / n
        co = sum(1 for r in runs if r[1] > 0) / n * 100
        egm = [e for e in (eg.get(k) for k in range(len(runs))) if e is not None]
        print(f'  {arm:6s} {scene:16s} n={len(runs):2d} score={ms:.2f} coll%={co:3.0f} '
              f'ego={sum(egm) / max(len(egm), 1):.1f}')

off_mean = {s: sum(x[2] for x in data[('off', s)] if x[2]) / max(len([x for x in data[('off', s)] if x[2]]), 1)
            for s in SCENES}


def sp(arm, idxs=None):
    per = []
    for s in SCENES:
        runs = [(x[0], x[2]) for x in data[(arm, s)] if x[2] is not None]
        if idxs is not None:
            runs = [runs[i % len(runs)] for i in idxs]
        per.append(sum(sc * min(1.0, eg / off_mean[s]) for sc, eg in runs) / len(runs))
    return sum(per) / len(per)


n = min(len(data[(a, s)]) for a in ('off', 'union') for s in SCENES)
obs = sp('union') - sp('off')
boots = sorted(
    sp('union', idx) - sp('off', idx)
    for idx in ([random.randrange(n) for _ in range(n)] for _ in range(5000))
)
lo, hi = boots[int(0.025 * 5000)], boots[int(0.975 * 5000)]
print(f'\n=== pooled safe-progress (n={n}/scene, normalized to VAD-OFF) ===')
print(f'  OFF {sp("off"):.3f}   union {sp("union"):.3f}   delta {obs:+.3f}')
print(f'  95% CI [{lo:+.3f}, {hi:+.3f}]   excludes 0: {lo > 0 or hi < 0}')
