#!/usr/bin/env python3
"""Pool the OFF and union arms across iterations 8/9/10 (same config, independent seeds) and put a
drive-clustered bootstrap CI on the union's safe-progress advantage. This is the statistical
confirmation of the campaign's headline: is safe-progress(union) > safe-progress(OFF) real, or noise?"""
import collections
import json
import math
import os
import random
import re

random.seed(20260701)  # fixed; Date.now/random-at-import are unavailable, so pin explicitly

OUT = '/opt/sentinel-stack/NeuroNCAP/outoutput'
ITERS = [('i8', 'union'), ('i9', 'union'), ('i10', 'union')]
LOGS = {'i8': '/var/log/sentinel-i8.log', 'i9': '/var/log/sentinel-i9.log', 'i10': '/var/log/sentinel-i10.log'}
PAIRPAT = {'i8': 'I8PAIR', 'i9': 'I9PAIR', 'i10': 'I10PAIR'}
SCENES = ['stationary-0103', 'frontal-0103', 'side-0103']


def pl(P):
    return sum(math.hypot(P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]) for i in range(len(P)-1))


def scores_from_log(tag):
    sc = collections.defaultdict(list); arm = scene = None
    pat = PAIRPAT[tag]
    for line in open(LOGS[tag]):
        m = re.search(pat + r' (\w+) (\w+) (\d+)', line)
        if m:
            arm = m.group(1); scene = m.group(2)+'-'+m.group(3); continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scene)].append((float(m.group(1)), float(m.group(2))))
    return sc


def egos(tag, arm, scene):
    d = os.path.join(OUT, f'{tag}-{arm}', scene)
    out = []
    if os.path.isdir(d):
        for r in sorted(os.listdir(d), key=lambda x: int(x.split('_')[1]) if x.startswith('run_') else 0):
            try:
                e = json.load(open(os.path.join(d, r, 'ego_poses.json')))
                out.append(pl([[m[0][3], m[1][3]] for _, m in sorted(e.items())]))
            except Exception:
                pass
    return out


# collect per-scene pooled runs: (score, ego) for OFF and union across all 3 iters
pool = {'off': collections.defaultdict(list), 'union': collections.defaultdict(list)}
for tag, _ in ITERS:
    sc = scores_from_log(tag)
    for arm in ['off', 'union']:
        for scene in SCENES:
            S = sc.get((arm, scene), []); E = egos(tag, arm, scene)
            for i in range(min(len(S), len(E))):
                pool[arm][scene].append((S[i][0], E[i]))

# OFF mean ego per scene = normal-driving reference for the progress ratio
off_mean_ego = {s: (sum(e for _, e in pool['off'][s]) / len(pool['off'][s]) if pool['off'][s] else 1.0)
                for s in SCENES}


def safe_progress(arm_pool, resample=False):
    per_scene = []
    for s in SCENES:
        runs = arm_pool[s]
        if not runs:
            continue
        if resample:
            runs = [random.choice(runs) for _ in runs]  # within-scene (drive-clustered) resample
        base = off_mean_ego[s] or 1.0
        vals = [sc * min(1.0, eg / base) for sc, eg in runs]
        per_scene.append(sum(vals) / len(vals))
    return sum(per_scene) / len(per_scene) if per_scene else 0.0


print('pooled n per scene (OFF / union):')
for s in SCENES:
    print(f'  {s:16s} {len(pool["off"][s])} / {len(pool["union"][s])}')

off_sp = safe_progress(pool['off'])
un_sp = safe_progress(pool['union'])
d_obs = un_sp - off_sp
boots = sorted(safe_progress(pool['union'], True) - safe_progress(pool['off'], True) for _ in range(5000))
lo, hi = boots[int(0.025*5000)], boots[int(0.975*5000)]
print(f'\npooled safe-progress:  OFF {off_sp:.3f}   union {un_sp:.3f}')
print(f'union - OFF delta = {d_obs:+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]')
print(f'CI excludes 0 (net-positive confirmed): {lo > 0}')

print('\nper-scene mean score / collision% (pooled):')
sc_all = {tag: scores_from_log(tag) for tag, _ in ITERS}
for arm in ['off', 'union']:
    for s in SCENES:
        allS = []
        for tag, _ in ITERS:
            allS += sc_all[tag].get((arm, s), [])
        n = len(allS) or 1
        ms = sum(x[0] for x in allS)/n
        co = sum(1 for x in allS if x[1] > 0)/n*100
        print(f'  {arm:6s} {s:16s} score={ms:.2f} coll%={co:3.0f} n={len(allS)}')
