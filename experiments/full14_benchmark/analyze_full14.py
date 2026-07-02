#!/usr/bin/env python3
"""Full 14-scene benchmark analysis — the pre-registered H14 hypotheses.

Parses the run log (F14PAIR arm scenario seq markers) and per-run ego_poses, and reports:
- per-pair and per-class tables (score / collision%) for both arms;
- H14-1: OFF pooled NCAP score (mean of the three class means, the published protocol) vs 1.84;
- H14-2: union - OFF on pooled NCAP score AND on safe-progress, each with a within-pair
  (seed-paired) bootstrap CI;
- H14-3: per-class structure;
- the 0103 cross-metadata drift check against the committed v20 values.

Usage: analyze_full14.py <sentinel-full14.log> <runs-root with f14-off/ f14-union/>
"""
import collections
import json
import math
import os
import random
import re
import sys

random.seed(20260703)
LOG, OUT = sys.argv[1], sys.argv[2]
CLASSES = ['stationary', 'frontal', 'side']


def parse_log():
    sc = collections.defaultdict(list)
    arm = scen = seq = None
    for line in open(LOG, errors='replace'):
        m = re.search(r'^##### F14PAIR (\w+) (\w+) (\d+)', line)
        if m:
            arm, scen, seq = m.groups()
            continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scen, seq)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def egos(arm, scen, seq):
    d = os.path.join(OUT, f'f14-{arm}', f'{scen}-{seq}')
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, 'ego_poses.json')
            if r.startswith('run_') and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split('_')[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


S = parse_log()
pairs = sorted({(scen, seq) for (_, scen, seq) in S})
data = {}
for arm in ('off', 'union'):
    for scen, seq in pairs:
        runs = S.get((arm, scen, seq), [])
        eg = egos(arm, scen, seq)
        data[(arm, scen, seq)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]

print('=== per-pair (score / coll% / ego m), OFF vs union ===')
for scen in CLASSES:
    for s2, seq in pairs:
        if s2 != scen:
            continue
        row = []
        for arm in ('off', 'union'):
            d = data[(arm, scen, seq)]
            n = len(d) or 1
            ms = sum(x[0] for x in d) / n
            co = sum(1 for x in d if x[1] > 0) / n * 100
            egm = [x[2] for x in d if x[2] is not None]
            row.append(f'{ms:4.2f}/{co:3.0f}/{(sum(egm) / max(len(egm), 1)):5.1f}')
        print(f'  {scen:10s} {seq}   OFF {row[0]}   union {row[1]}')


def class_stats(arm):
    out = {}
    for scen in CLASSES:
        v = [x for (a, s2, _), d in data.items() if a == arm and s2 == scen for x in d]
        ms = sum(x[0] for x in v) / len(v)
        co = sum(1 for x in v if x[1] > 0) / len(v) * 100
        out[scen] = (ms, co, len(v))
    return out


print('\n=== per-class pooled (H14-3) ===')
cs = {arm: class_stats(arm) for arm in ('off', 'union')}
for scen in CLASSES:
    o, u = cs['off'][scen], cs['union'][scen]
    print(f'  {scen:10s} OFF {o[0]:.2f}/{o[1]:.0f}% (n={o[2]})   union {u[0]:.2f}/{u[1]:.0f}% (n={u[2]})')

off_pooled = sum(cs['off'][s][0] for s in CLASSES) / 3
un_pooled = sum(cs['union'][s][0] for s in CLASSES) / 3
print(f'\nH14-1: OFF pooled NCAP score = {off_pooled:.2f}   (published UniAD 1.84; pre-registered tolerance ±0.4)')
print(f'H14-2: union pooled NCAP score = {un_pooled:.2f}   delta = {un_pooled - off_pooled:+.2f}')

# bootstrap CIs: resample run indices within every pair (seed-paired), recompute pooled deltas
off_ego_mean = {}
for scen, seq in pairs:
    e = [x[2] for x in data[('off', scen, seq)] if x[2] is not None]
    off_ego_mean[(scen, seq)] = sum(e) / len(e) if e else 1.0


def pooled_metrics(idxs=None):
    """Return (pooled NCAP delta, pooled safe-progress delta) for a run-index resample."""
    class_score = {arm: {} for arm in ('off', 'union')}
    pair_sp = {arm: [] for arm in ('off', 'union')}
    for arm in ('off', 'union'):
        for scen in CLASSES:
            vals = []
            for s2, seq in pairs:
                if s2 != scen:
                    continue
                d = data[(arm, scen, seq)]
                use = d if idxs is None else [d[i % len(d)] for i in idxs]
                vals += [x[0] for x in use]
                base = off_ego_mean[(scen, seq)] or 1.0
                sp = [x[0] * min(1.0, (x[2] or 0.0) / base) for x in use if x[2] is not None]
                if sp:
                    pair_sp[arm].append(sum(sp) / len(sp))
            class_score[arm][scen] = sum(vals) / len(vals)
    ncap = {a: sum(class_score[a][s] for s in CLASSES) / 3 for a in ('off', 'union')}
    spd = {a: sum(pair_sp[a]) / len(pair_sp[a]) for a in ('off', 'union')}
    return ncap['union'] - ncap['off'], spd['union'] - spd['off']


d_ncap, d_sp = pooled_metrics()
boots = [pooled_metrics([random.randrange(6) for _ in range(6)]) for _ in range(3000)]
bn = sorted(b[0] for b in boots)
bs = sorted(b[1] for b in boots)
print('\nH14-2 CIs (within-pair seed-paired bootstrap, 3000 samples):')
print(f'  NCAP-score delta   {d_ncap:+.3f}   95% CI [{bn[75]:+.3f}, {bn[2924]:+.3f}]   excludes 0: {bn[75] > 0}')
print(f'  safe-progress delta {d_sp:+.3f}   95% CI [{bs[75]:+.3f}, {bs[2924]:+.3f}]   excludes 0: {bs[75] > 0}')

print('\n=== 0103 cross-metadata drift check (vs committed v20, mini metadata) ===')
V20 = {('stationary', '0103'): (4.51, 10), ('frontal', '0103'): (0.84, 85), ('side', '0103'): (0.52, 100)}
for (scen, seq), (v20s, v20c) in V20.items():
    d = data[('off', scen, seq)]
    ms = sum(x[0] for x in d) / len(d)
    co = sum(1 for x in d if x[1] > 0) / len(d) * 100
    print(f'  off {scen:10s} 0103: f14 {ms:.2f}/{co:.0f}% (n=6) vs v20 {v20s:.2f}/{v20c}% (n=20) — '
          f'first-6 determinism check in text')
