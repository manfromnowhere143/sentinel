#!/usr/bin/env python3
"""Iteration 16 — four-way verdict: OFF vs union vs released vs crawl on the full 14-scene set.

OFF and union come from the committed full14 evidence, released from the committed iter15
evidence (identical deterministic episodes); crawl is the new arm. Reports per-pair and
per-class tables, pooled NCAP score and safe-progress with within-pair seed-paired bootstrap
CIs (crawl vs OFF, vs union, vs released), the H16 criteria, and the pre-registered
falsifier checks from the decision log (oscillation; crawl-frame accounting).

Usage: analyze_iter16.py <f14 log> <f14 runs root> <i15 log> <i15 runs root>
                         <i16 log> <i16 runs root> <i16 decision jsonl>
"""
import collections
import gzip
import json
import math
import os
import random
import re
import sys

random.seed(20260703)
F14LOG, F14OUT, I15LOG, I15OUT, I16LOG, I16OUT, DECISIONS = sys.argv[1:8]
CLASSES = ['stationary', 'frontal', 'side']
ARMS = ('off', 'union', 'released', 'crawl')


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


S14 = parse_log(F14LOG, 'F14PAIR')
S15 = parse_log(I15LOG, 'I15PAIR')
S16 = parse_log(I16LOG, 'I16PAIR')
pairs = sorted({(scen, seq) for (_, scen, seq) in S14})
data = {}
for arm, S, root, tag in [('off', S14, F14OUT, 'f14-off'), ('union', S14, F14OUT, 'f14-union'),
                          ('released', S15, I15OUT, 'i15-released'), ('crawl', S16, I16OUT, 'i16-crawl')]:
    for scen, seq in pairs:
        runs = S.get((arm, scen, seq), [])
        eg = egos(root, tag, scen, seq)
        data[(arm, scen, seq)] = [(runs[k][0], runs[k][1], eg.get(k)) for k in range(len(runs))]

print('=== per-pair (score/coll%/ego m): OFF | union | released | crawl ===')
for scen in CLASSES:
    for s2, seq in pairs:
        if s2 != scen:
            continue
        cells = []
        for arm in ARMS:
            d = data[(arm, scen, seq)]
            n = len(d) or 1
            ms = sum(x[0] for x in d) / n
            co = sum(1 for x in d if x[1] > 0) / n * 100
            egm = [x[2] for x in d if x[2] is not None]
            cells.append(f'{ms:4.2f}/{co:3.0f}/{(sum(egm) / max(len(egm), 1)):5.1f}')
        print(f'  {scen:10s} {seq}   ' + ' | '.join(cells))

print('\n=== per-class pooled ===')
for scen in CLASSES:
    row = []
    for arm in ARMS:
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


print('\n=== pooled NCAP score and safe-progress ===')
base_vals = {arm: pooled(arm) for arm in ARMS}
for arm, (nc, sp) in base_vals.items():
    print(f'  {arm:9s} NCAP {nc:.2f}   safe-progress {sp:.3f}')

for ref in ('off', 'union', 'released'):
    d_nc = base_vals['crawl'][0] - base_vals[ref][0]
    d_sp = base_vals['crawl'][1] - base_vals[ref][1]
    boots = []
    for _ in range(3000):
        idxs = [random.randrange(6) for _ in range(6)]
        a = pooled('crawl', idxs)
        b = pooled(ref, idxs)
        boots.append((a[0] - b[0], a[1] - b[1]))
    bn = sorted(x[0] for x in boots)
    bs = sorted(x[1] for x in boots)
    print(f'\ncrawl - {ref}:')
    print(f'  NCAP delta {d_nc:+.3f}  CI [{bn[75]:+.3f}, {bn[2924]:+.3f}]  excludes 0: {bn[75] > 0 or bn[2924] < 0}')
    print(f'  safe-prog  {d_sp:+.3f}  CI [{bs[75]:+.3f}, {bs[2924]:+.3f}]  excludes 0: {bs[75] > 0 or bs[2924] < 0}')

print('\n=== falsifier checks (decision log) ===')
_open = gzip.open if DECISIONS.endswith('.gz') else open
episodes = []
cur = None
for line in _open(DECISIONS, 'rt'):
    d = json.loads(line)
    if d.get('reset'):
        cur = {'events': [], 'crawl_frames': 0}
        episodes.append(cur)
    elif cur is not None:
        if d.get('crawl'):
            cur['events'].append('C')
            cur['crawl_frames'] += 1
        elif d.get('release'):
            cur['events'].append('R')
osc = 0
rel_eps = 0
fired = 0
latched_end = 0
total_crawl = 0
for ep in episodes:
    s = ''.join(ep['events'])
    total_crawl += ep['crawl_frames']
    if 'C' in s:
        fired += 1
    if 'R' in s:
        rel_eps += 1
    if s.count('RC') >= 2:
        osc += 1
latched_end = sum(1 for ep in episodes if ep['events'] and ep['events'][-1] == 'C')
print(f'  episodes: {len(episodes)}  fired: {fired}  with >=1 release: {rel_eps}')
print(f'  ended still latched (crawling): {latched_end}  total crawl frames: {total_crawl}')
print(f'  episodes with >=2 release->re-latch cycles (oscillation): {osc}')
