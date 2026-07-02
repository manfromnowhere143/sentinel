#!/usr/bin/env python3
"""Iteration 13 — the RSS-style formal envelope vs the union, on the same 20 unique episodes.

Parses the RSS arm's run log + per-run ego_poses and compares against the committed v20 OFF and
union arms (same run indices — seed-paired by determinism). Metrics per H13: per-scene score /
collision% / ego progress; pooled safe-progress (normalized to the v20 OFF means); within-scene
bootstrap CI on (union - RSS).

Usage: analyze_rss.py <sentinel-rss.log> <rss-runs-root> <v20-log> <v20-runs-root>
"""
import collections
import json
import math
import os
import random
import re
import sys

random.seed(20260702)
RSSLOG, RSSOUT, V20LOG, V20OUT = sys.argv[1:5]
SCENES = ['stationary-0103', 'frontal-0103', 'side-0103']


def scores_from_log(path, pairpat):
    sc = collections.defaultdict(list)
    arm = scene = None
    for line in open(path, errors='replace'):
        m = re.search(pairpat + r' (\w+) (\w+) (\d+)', line)
        if m:
            arm, scene = m.group(1), m.group(2) + '-' + m.group(3)
            continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scene)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def egos(root, tag, scene):
    d = os.path.join(root, tag, scene)
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, 'ego_poses.json')
            if r.startswith('run_') and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split('_')[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


S_rss = scores_from_log(RSSLOG, 'RSSPAIR')
S_v20 = scores_from_log(V20LOG, 'V20PAIR')

data = {}
for arm, S, root, tag in [('rss', S_rss, RSSOUT, 'rss-arm'),
                          ('off', S_v20, V20OUT, 'v20-off'),
                          ('union', S_v20, V20OUT, 'v20-union')]:
    for scene in SCENES:
        runs = S.get((arm if arm != 'rss' else 'rss', scene), [])
        eg = egos(root, tag, scene)
        data[(arm, scene)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]

print('=== per-arm, per-scene (n, mean score, collision%, mean ego m) ===')
for arm in ('off', 'union', 'rss'):
    for scene in SCENES:
        d = data[(arm, scene)]
        n = len(d) or 1
        ms = sum(x[0] for x in d) / n
        co = sum(1 for x in d if x[1] > 0) / n * 100
        egm = [x[2] for x in d if x[2] is not None]
        print(f'  {arm:6s} {scene:16s} n={len(d):2d} score={ms:.2f} coll%={co:3.0f} '
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


n = min(len(data[(a, s)]) for a in ('off', 'union', 'rss') for s in SCENES)
print(f'\n=== pooled safe-progress (n={n}/scene, normalized to v20 OFF) ===')
for arm in ('off', 'union', 'rss'):
    print(f'  {arm:6s} {sp(arm):.3f}')
obs = sp('union') - sp('rss')
boots = sorted(
    sp('union', idx) - sp('rss', idx)
    for idx in ([random.randrange(n) for _ in range(n)] for _ in range(5000))
)
lo, hi = boots[int(0.025 * 5000)], boots[int(0.975 * 5000)]
print(f'\nunion - RSS delta = {obs:+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]   excludes 0: {lo > 0 or hi < 0}')
