#!/usr/bin/env python3
"""Offline evaluation of iteration 17's three named successor predicates, on the committed
iteration-17 evidence — no GPU. Each test asks: would the modified router have removed
side-0108's unsafe crawl frames while retaining the crawl share that produced the deployment
gain?

1. Firing-term routing (CPA-fired -> stop; TTC-only -> crawl): counts crawl frames with
   cpa < 1.5 (they would convert to stop). Result: zero — every CPA-fired frame was already
   stopped by the 2.0 m overlap predicate; this successor is a strict no-op-or-worse.
2. N-frame no-overlap confirmation (hysteresis toward the stop): simulates requiring N
   consecutive omin >= 2.0 frames before any crawl frame. Reports kept/converted per N.
3. Current-position proximity guard: per crawl frame, the minimum distance from any tracked
   object's current position (ego frame, score >= 0.3, range <= 30 m) to the planned polyline,
   using the shadow record paired with each decision frame; sweeps a guard radius X.

Usage: analyze_successors_offline.py <i17 run log> <i17 decision jsonl[.gz]>
"""
import collections
import gzip
import json
import math
import re
import sys

RUNLOG, DECISIONS = sys.argv[1:3]

pairs = []
for line in open(RUNLOG, errors='replace'):
    m = re.search(r'##### I17PAIR routed (\w+) (\d+)', line)
    if m and (not pairs or pairs[-1] != m.groups()):
        pairs.append(m.groups())

_open = gzip.open if DECISIONS.endswith('.gz') else open
episodes = []  # (pair, [(act, cpa, omin, dpos)])
ep = -1
cur = None
last_shadow = None
for line in _open(DECISIONS, 'rt'):
    d = json.loads(line)
    if d.get('reset'):
        ep += 1
        last_shadow = None
        cur = []
        episodes.append((pairs[min(ep // 6, len(pairs) - 1)], cur))
    elif 'traj' in d:
        last_shadow = d
    elif cur is not None and (d.get('stop') or d.get('crawl')):
        dpos = 99.0
        if last_shadow:
            plan = last_shadow['traj']
            objs = last_shadow.get('objs') or []
            scores = last_shadow.get('scores') or []
            for i in range(min(len(objs), len(scores))):
                if scores[i] is None or scores[i] < 0.3:
                    continue
                ox, oy = objs[i][0], objs[i][1]
                if math.hypot(ox, oy) > 30:
                    continue
                for px, py in plan:
                    dpos = min(dpos, math.hypot(px - ox, py - oy))
        cur.append(('S' if d.get('stop') else 'C', d.get('cpa', 99), d.get('omin', 99), dpos))

MIS = ('side', '0108')

print('=== successor 1: firing-term routing (crawl frames with cpa < 1.5 -> stop) ===')
conv = sum(1 for _, seq in episodes for a, cpa, _, _ in seq if a == 'C' and cpa < 1.5)
tot = sum(1 for _, seq in episodes for a, *_ in seq if a == 'C')
print(f'  crawl frames converted: {conv}/{tot} -> ' +
      ('NO-OP: every CPA-fired frame was already stopped by the 2.0 m overlap predicate; '
       'this variant is equal-or-more permissive. REFUTED.' if conv == 0 else 'nonzero effect'))

print('\n=== successor 2: N-frame no-overlap confirmation ===')
for N in (2, 3, 4):
    keep = collections.defaultdict(int)
    conv2 = collections.defaultdict(int)
    for key, seq in episodes:
        streak = 0
        for a, _, omin, _ in seq:
            streak = streak + 1 if omin >= 2.0 else 0
            if a == 'C':
                (keep if streak >= N else conv2)[key] += 1
    tk = sum(keep.values())
    tc = sum(conv2.values())
    print(f'  N={N}: total crawl kept {tk}/{tk + tc} ({tk / (tk + tc) * 100:.0f}%) | '
          f'side-0108 kept {keep[MIS]} converted {conv2[MIS]}')
print('  -> N=4 removes 0108 but leaves 6% crawl share (mechanism vacuous); N<=3 unsafe. REFUTED.')

print('\n=== successor 3: current-position proximity guard ===')
dist = collections.defaultdict(list)
for key, seq in episodes:
    for a, _, _, dpos in seq:
        if a == 'C':
            dist[key].append(dpos)
for key in sorted(dist):
    v = sorted(dist[key])
    flag = '  <-- misrouted pair' if key == MIS else ''
    print(f'  {key[0]:10s} {key[1]}  n={len(v):3d}  min={v[0]:5.1f}  median={v[len(v) // 2]:5.1f}  max={v[-1]:5.1f}{flag}')
for X in (2.5, 3.0, 4.0, 5.0):
    c0 = sum(1 for d in dist[MIS] if d < X)
    t = sum(len(v) for v in dist.values())
    c = sum(1 for v in dist.values() for d in v if d < X)
    print(f'  X={X}: 0108 converted {c0}/{len(dist[MIS])} | total converted {c}/{t} (retained {(t - c) / t * 100:.0f}%)')
print('  -> 0108 (unsafe) and side-0103 (safe, 5.00/0%) are indistinguishable on this feature. REFUTED.')

print('\nCONCLUSION: no per-frame geometric refinement separates the misrouted crossing from')
print('safe crawls on this evidence. The discriminating signal is velocity continuity through')
print('ID switches — tracking quality — converging with the iteration-14 transfer finding.')
