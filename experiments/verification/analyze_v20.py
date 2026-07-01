#!/usr/bin/env python3
"""Verification §4 — fresh OFF vs union at 20 unique episodes, plus the iter11 evade null re-check.

Parses the v20 run log + per-run ego_poses, verifies determinism against the committed iteration-8
evidence (run indices 0-7 must match exactly), and computes the honest n=20 statistics:
per-scene score/collision, safe-progress, and a drive-clustered (within-scene) bootstrap CI.

Usage: python3 analyze_v20.py <sentinel-v20.log> <outoutput-root>
where <outoutput-root> holds v20-off/ v20-union/ v20-evade/ scene dirs with run_*/ego_poses.json.
"""
import collections
import contextlib
import io
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
        m = re.search(r'V20PAIR (\w+) (\w+) (\d+)', line)
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
    d = os.path.join(OUT, f'v20-{arm}', scene)
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, 'ego_poses.json')
            if r.startswith('run_') and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split('_')[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


S = scores_from_log()

print('=== per-arm, per-scene (n, mean score, collision%, mean ego m) ===')
data = {}
for arm in ('off', 'union', 'evade'):
    for scene in SCENES:
        runs = S.get((arm, scene), [])
        if not runs:
            continue
        eg = egos(arm, scene)
        data[(arm, scene)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]
        n = len(runs)
        ms = sum(r[0] for r in runs) / n
        co = sum(1 for r in runs if r[1] > 0) / n * 100
        egm = [e for e in (eg.get(k) for k in range(n)) if e is not None]
        egs = sum(egm) / len(egm) if egm else float('nan')
        print(f'  {arm:6s} {scene:16s} n={n:2d} score={ms:.2f} coll%={co:3.0f} ego={egs:.1f}')

print('\n=== determinism cross-check: v20 runs 0-7 vs committed iteration-8 evidence ===')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import audit_pooling  # noqa: E402  (reuses its committed-evidence parsers; silence its report)
match = True
for arm in ('off', 'union'):
    for scene in SCENES:
        v20 = [(s, i) for s, i, _ in data.get((arm, scene), [])][:8]
        i8 = audit_pooling.S['i8'].get((arm, scene), [])
        if v20 != i8:
            match = False
            print(f'  MISMATCH {arm} {scene}:\n    v20[:8] {v20}\n    i8      {i8}')
print(f'  v20[:8] == iteration-8 evidence everywhere: {match}')

print('\n=== honest n=20 statistics (safe-progress, within-scene bootstrap) ===')
ue = {arm: {s: [(sc, eg) for sc, _, eg in data[(arm, s)] if eg is not None] for s in SCENES}
      for arm in ('off', 'union')}
off_mean = {s: sum(e for _, e in ue['off'][s]) / len(ue['off'][s]) for s in SCENES}


def sp(arm, idxs=None):
    per = []
    for s in SCENES:
        runs = ue[arm][s]
        if idxs is not None:
            runs = [runs[i % len(runs)] for i in idxs]
        per.append(sum(sc * min(1.0, eg / off_mean[s]) for sc, eg in runs) / len(runs))
    return sum(per) / len(per)


n = min(len(ue['off'][s]) for s in SCENES)
obs = sp('union') - sp('off')
boots = sorted(
    sp('union', idx) - sp('off', idx)
    for idx in ([random.randrange(n) for _ in range(n)] for _ in range(5000))
)
lo, hi = boots[int(0.025 * 5000)], boots[int(0.975 * 5000)]
print(f'  n per scene = {n}')
print(f'  OFF {sp("off"):.3f}   union {sp("union"):.3f}   delta {obs:+.3f}')
print(f'  95% CI [{lo:+.3f}, {hi:+.3f}]   excludes 0: {lo > 0}')
