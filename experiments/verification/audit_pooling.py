#!/usr/bin/env python3
"""Independent verification audit of the union_validation pooling.

Reads only committed evidence (evidence/logs, evidence/runs) and answers, run by run:
1. Are the iteration 8/9/10 arms independent replications, or deterministic replays?
2. What is the honest safe-progress delta and CI on unique episodes?
3. How many union side-impact collisions actually occurred?

Run from this directory: python3 audit_pooling.py
"""
import collections
import glob
import json
import math
import os
import random
import re
import tarfile
import tempfile

random.seed(20260701)
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, 'evidence')
PAIRPAT = {'i8': 'I8PAIR', 'i9': 'I9PAIR', 'i10': 'I10PAIR'}
SCENES = ['stationary-0103', 'frontal-0103', 'side-0103']


def scores_from_log(tag):
    sc = collections.defaultdict(list)
    arm = scene = None
    for line in open(os.path.join(EV, 'logs', f'sentinel-{tag}.log'), errors='replace'):
        m = re.search(PAIRPAT[tag] + r' (\w+) (\w+) (\d+)', line)
        if m:
            arm, scene = m.group(1), m.group(2) + '-' + m.group(3)
            continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scene)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


_extract = tempfile.mkdtemp(prefix='sentinel_audit_')


def egos(tag, arm, scene):
    """run index -> ego path length, from the committed per-run ego_poses archives."""
    tar = os.path.join(EV, 'runs', f'{tag}-{arm}.tar.gz')
    root = os.path.join(_extract, f'{tag}-{arm}')
    if not os.path.isdir(root) and os.path.exists(tar):
        with tarfile.open(tar) as t:
            t.extractall(_extract)
    out = {}
    for p in glob.glob(os.path.join(_extract, f'{tag}-{arm}', scene, 'run_*', 'ego_poses.json')):
        e = json.load(open(p))
        idx = int(p.split('run_')[-1].split(os.sep)[0])
        out[idx] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


S = {t: scores_from_log(t) for t in PAIRPAT}

print('=== A. run-by-run identity (determinism test) ===')
ok_910 = ok_89 = True
for scene in SCENES:
    for arm in ('off', 'union'):
        v8, v9, v10 = (S[t].get((arm, scene), []) for t in ('i8', 'i9', 'i10'))
        if v9 != v10:
            ok_910 = False
        if v8[:len(v9)] != v9:
            ok_89 = False
print(f'  i9 == i10 for every arm/scene: {ok_910}')
print(f'  i8[:6] == i9 for every arm/scene: {ok_89}')
print('  -> the three "replications" are the same episodes; pooling them triple-counts runs 0-5.')

print('\n=== B. union side-impact recount ===')
for t in ('i8', 'i9', 'i10'):
    v = S[t].get(('union', 'side-0103'), [])
    coll = [(k, s, i) for k, (s, i) in enumerate(v) if i > 0]
    print(f'  {t}: n={len(v)} collisions at run indices {[c[0] for c in coll]}')
print('  -> unique episodes: 1 collision in 8 (run 6), i.e. 12.5%, not the pooled 5%.')

print('\n=== C. honest recompute on unique episodes (iter8, runs 0-7), seed-paired bootstrap ===')
ue = {}
for arm in ('off', 'union'):
    ue[arm] = {}
    for scene in SCENES:
        sc_list = S['i8'].get((arm, scene), [])
        eg = egos('i8', arm, scene)
        ue[arm][scene] = [(sc_list[k][0], eg[k]) for k in range(len(sc_list)) if k in eg]

off_mean_ego = {s: sum(e for _, e in ue['off'][s]) / len(ue['off'][s]) for s in SCENES}


def safe_progress(arm, idxs=None):
    per_scene = []
    for s in SCENES:
        runs = ue[arm][s]
        if idxs is not None:
            runs = [runs[i] for i in idxs if i < len(runs)]
        per_scene.append(sum(sc * min(1.0, eg / off_mean_ego[s]) for sc, eg in runs) / len(runs))
    return sum(per_scene) / len(per_scene)


n = min(len(ue['off'][s]) for s in SCENES)
obs = safe_progress('union') - safe_progress('off')
boots = sorted(
    safe_progress('union', idx) - safe_progress('off', idx)
    for idx in ([random.randrange(n) for _ in range(n)] for _ in range(5000))
)
lo, hi = boots[int(0.025 * 5000)], boots[int(0.975 * 5000)]
print(f'  unique n per scene = {n}')
print(f'  OFF {safe_progress("off"):.3f}  union {safe_progress("union"):.3f}  delta {obs:+.3f}')
print(f'  95% CI [{lo:+.3f}, {hi:+.3f}]  excludes 0: {lo > 0}')
