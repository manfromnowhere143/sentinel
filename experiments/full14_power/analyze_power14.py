#!/usr/bin/env python3
"""The power run — OFF vs best configuration at 20 runs/pair on the full 14-scene set.

First runs the H-P0 validity gate: run indices 0-5 of each arm must reproduce the committed
RUNS=6 evidence exactly (deterministic episodes). Then the full14 analysis at n=20: per-pair and
per-class tables, pooled NCAP score and safe-progress (normalized to this run's OFF arm), and
the seed-paired within-pair bootstrap CI on the deltas.

Usage: analyze_power14.py <p14 log> <p14 runs root> <f14 log> <best comparator log>
                          <best comparator marker: I15PAIR|I16PAIR> <best comparator arm name>
"""
import collections
import json
import math
import os
import random
import re
import sys

random.seed(20260705)
P14LOG, P14OUT, F14LOG, BESTLOG, BESTMARKER, BESTARM = sys.argv[1:7]
CLASSES = ['stationary', 'frontal', 'side']


def parse_log(path, marker):
    sc = collections.defaultdict(list)
    arm = scen = seq = None
    for line in open(path, errors='replace'):
        m = re.search(r'^##### ' + marker + r' (\w+) (\w+) (\d+)', line)
        if m:
            arm, scen, seq = m.groups()
            continue
        m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
        if m and arm:
            sc[(arm, scen, seq)].append((float(m.group(1)), float(m.group(2))))
    return sc


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def egos(root, tag, scen, seq):
    d = os.path.join(root, tag, f'{scen}-{seq}')
    out = {}
    if os.path.isdir(d):
        for r in os.listdir(d):
            p = os.path.join(d, r, 'ego_poses.json')
            if r.startswith('run_') and os.path.exists(p):
                e = json.load(open(p))
                out[int(r.split('_')[1])] = path_len([[m[0][3], m[1][3]] for _, m in sorted(e.items())])
    return out


SP = parse_log(P14LOG, 'P14PAIR')
S14 = parse_log(F14LOG, 'F14PAIR')
SB = parse_log(BESTLOG, BESTMARKER)
pairs = sorted({(scen, seq) for (a, scen, seq) in SP if a == 'off'})

print('=== H-P0 validity gate: run indices 0-5 reproduce the committed RUNS=6 evidence ===')
gate_ok = True
for scen, seq in pairs:
    for arm, ref, refarm in [('off', S14, 'off'), ('best', SB, BESTARM)]:
        new = [x[0] for x in SP.get((arm, scen, seq), [])][:6]
        old = [x[0] for x in ref.get((refarm, scen, seq), [])][:6]
        if len(new) < 6 or new != old:
            gate_ok = False
            print(f'  MISMATCH {arm} {scen}-{seq}: new[:6]={new} committed={old}')
print(f'  H-P0: {"PASS — first-6 exact on all pairs, both arms" if gate_ok else "FAIL (apparatus drift — no result claims below are valid)"}')

data = {}
NRUNS = 20
for arm, tag in [('off', 'p14-off'), ('best', 'p14-best')]:
    for scen, seq in pairs:
        runs = SP.get((arm, scen, seq), [])
        eg = egos(P14OUT, tag, scen, seq)
        data[(arm, scen, seq)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]

print('\n=== per-pair (score/coll%/ego m): OFF | best ===')
for scen in CLASSES:
    for s2, seq in pairs:
        if s2 != scen:
            continue
        cells = []
        for arm in ('off', 'best'):
            d = data[(arm, scen, seq)]
            n = len(d) or 1
            ms = sum(x[0] for x in d) / n
            co = sum(1 for x in d if x[1] > 0) / n * 100
            egm = [x[2] for x in d if x[2] is not None]
            cells.append(f'{ms:4.2f}/{co:3.0f}/{(sum(egm) / max(len(egm), 1)):5.1f}')
        print(f'  {scen:10s} {seq}   {cells[0]} | {cells[1]}   (n={len(data[("off", scen, seq)])}/{len(data[("best", scen, seq)])})')

print('\n=== per-class pooled ===')
for scen in CLASSES:
    row = []
    for arm in ('off', 'best'):
        v = [x for (a, s2, _), d in data.items() if a == arm and s2 == scen for x in d]
        row.append(f'{arm} {sum(x[0] for x in v) / len(v):4.2f}/{sum(1 for x in v if x[1] > 0) / len(v) * 100:3.0f}%')
    print(f'  {scen:10s} ' + '   '.join(row))

off_ego_mean = {}
for scen, seq in pairs:
    e = [x[2] for x in data[('off', scen, seq)] if x[2] is not None]
    off_ego_mean[(scen, seq)] = sum(e) / len(e) if e else 1.0


def pooled(arm, idxs=None):
    class_score = {}
    pair_sp = []
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
                pair_sp.append(sum(sp) / len(sp))
        class_score[scen] = sum(vals) / len(vals)
    return sum(class_score[s] for s in CLASSES) / 3, sum(pair_sp) / len(pair_sp)


print('\n=== pooled NCAP score and safe-progress (n=20/pair) ===')
base_vals = {arm: pooled(arm) for arm in ('off', 'best')}
for arm, (nc, sp) in base_vals.items():
    print(f'  {arm:5s} NCAP {nc:.2f}   safe-progress {sp:.3f}')

d_nc = base_vals['best'][0] - base_vals['off'][0]
d_sp = base_vals['best'][1] - base_vals['off'][1]
boots = []
for _ in range(3000):
    idxs = [random.randrange(NRUNS) for _ in range(NRUNS)]
    a = pooled('best', idxs)
    b = pooled('off', idxs)
    boots.append((a[0] - b[0], a[1] - b[1]))
bn = sorted(x[0] for x in boots)
bs = sorted(x[1] for x in boots)
print('\nbest - off:')
print(f'  NCAP delta {d_nc:+.3f}  CI [{bn[75]:+.3f}, {bn[2924]:+.3f}]  excludes 0: {bn[75] > 0 or bn[2924] < 0}')
print(f'  safe-prog  {d_sp:+.3f}  CI [{bs[75]:+.3f}, {bs[2924]:+.3f}]  excludes 0: {bs[75] > 0 or bs[2924] < 0}')
