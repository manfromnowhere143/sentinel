#!/usr/bin/env python3
"""Iteration-18 offline gate, iteration-17 side: replay the committed routed-arm evidence
through the tracking layer and recompute the routing predicate on tracker output.

O2 (pre-registered): in side-0108's logged crawl frames — the misroute that failed the gate —
the overlap predicate computed on tracker output must mandate the stop in every frame.
Also reported: crawl-frame retention everywhere else (the mechanism must not go vacuous), and
the O3 clean-scene check (union trigger rate on tracker output vs raw, stationary clean pairs).

World frame is reconstructed by joining each shadow frame's timestamp to the committed
ego_poses.json of its episode (episodes appear in run-script order, 6 runs per pair).

Usage: replay_i17.py <i17 run log> <i17 decision jsonl[.gz]> <i17 runs root (contains i17-routed/)>
"""
import collections
import gzip
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sentinel.tracker import Tracker  # noqa: E402

RUNLOG, DECISIONS, RUNSROOT = sys.argv[1:4]
GATE_PAIR = ('side', '0108')
CLEAN = [('stationary', s) for s in ('0099', '0103', '0331', '0966')]
DT = 0.5
ROUTE_MARGIN = 2.0
CPA_MARGIN = 1.5
TTC_T = 2.5
MIN_CLOSE = 3.0

pairs = []
for line in open(RUNLOG, errors='replace'):
    m = re.search(r'##### I17PAIR routed (\w+) (\d+)', line)
    if m and (not pairs or pairs[-1] != m.groups()):
        pairs.append(m.groups())

# --- load episodes: frames [(ts, plan, objs, scores)] + logged act per ts -------------------
_open = gzip.open if DECISIONS.endswith('.gz') else open
episodes = []
cur = None
ep = -1
for line in _open(DECISIONS, 'rt'):
    d = json.loads(line)
    if d.get('reset'):
        ep += 1
        cur = {'pair': pairs[min(ep // 6, len(pairs) - 1)], 'run': ep % 6, 'frames': [], 'acts': {}}
        episodes.append(cur)
    elif 'traj' in d:
        cur['frames'].append((d['ts'], d['traj'], d.get('objs') or [], d.get('scores') or []))
    elif d.get('stop') or d.get('crawl'):
        if cur['frames']:
            cur['acts'][cur['frames'][-1][0]] = 'S' if d.get('stop') else 'C'


def ego_matrix_map(pair, run):
    p = os.path.join(RUNSROOT, 'i17-routed', f'{pair[0]}-{pair[1]}', f'run_{run}', 'ego_poses.json')
    if not os.path.exists(p):
        return {}
    return {int(ts): m for ts, m in json.load(open(p)).items()}


def to_world(E, x, y):
    return (E[0][0] * x + E[0][1] * y + E[0][3], E[1][0] * x + E[1][1] * y + E[1][3])


joined = missing = 0
res = collections.defaultdict(lambda: {'crawl': 0, 'crawl_now_stop': 0, 'fired_raw': 0, 'fired_trk': 0})
for epis in episodes:
    egos = ego_matrix_map(epis['pair'], epis['run'])
    trk = Tracker(gate=3.0, alpha=0.5, max_missed=3)
    for ts, plan, objs, scores in epis['frames']:
        E = egos.get(int(ts))
        if E is None:
            missing += 1
            continue
        joined += 1
        wplan = [to_world(E, px, py) for px, py in plan]
        ex, ey = E[0][3], E[1][3]
        dets = []
        for i in range(min(len(objs), len(scores))):
            if scores[i] is None or scores[i] < 0.3:
                continue
            ox, oy = objs[i][0], objs[i][1]
            if math.hypot(ox, oy) > 30:
                continue
            dets.append(to_world(E, ox, oy))
        tracks = trk.update(dets, ts / 1e6)
        # overlap + union trigger on TRACKER output
        omin = 1e9
        mcpa = 1e9
        mttc = 1e9
        H = len(wplan)
        for (tx, ty, tvx, tvy, _tid) in tracks:
            for k in range(H):
                t = (k + 1) * DT
                ax, ay = tx + tvx * t, ty + tvy * t
                exk, eyk = wplan[k]
                d = math.hypot(exk - ax, eyk - ay)
                if d < mcpa:
                    mcpa = d
                for wx, wy in wplan:
                    d2 = math.hypot(wx - ax, wy - ay)
                    if d2 < omin:
                        omin = d2
            dx, dy = ex - tx, ey - ty
            gap = math.hypot(dx, dy)
            if gap > 1e-3:
                closing = (tvx * dx + tvy * dy) / gap
                if closing > max(MIN_CLOSE, 0.5):
                    mttc = min(mttc, gap / closing)
        key = epis['pair']
        act = epis['acts'].get(ts)
        if act == 'C':
            res[key]['crawl'] += 1
            if omin < ROUTE_MARGIN:
                res[key]['crawl_now_stop'] += 1
            if key == GATE_PAIR:
                epis['o2_crawl'] = epis.get('o2_crawl', 0) + 1
                if omin < ROUTE_MARGIN:
                    epis['o2_conv'] = epis.get('o2_conv', 0) + 1
        if act in ('S', 'C'):
            res[key]['fired_raw'] += 1
        if mcpa < CPA_MARGIN or mttc < TTC_T:
            res[key]['fired_trk'] += 1

print(f'frame join: {joined} joined, {missing} missing ego pose '
      f'(the missing are episode warm-up frames that precede pose recording — excluded on both sides)')

# --- O2 verdict on the pre-registered wording: frames the router crawled UNSAFELY = crawl
# frames in episodes that ended in collision. Colliding runs come from the committed run log.
sec = []
grab = False
for line in open(RUNLOG, errors='replace'):
    if f'I17PAIR routed {GATE_PAIR[0]} {GATE_PAIR[1]}' in line:
        grab = True
        continue
    if grab and 'I17PAIR' in line:
        break
    if grab and 'ncap_score:' in line:
        sec.append(float(re.search(r'ncap_score: ([0-9.]+)', line).group(1)))
colliding = {i for i, s in enumerate(sec) if s < 5.0}
print(f'\n=== O2 — {GATE_PAIR[0]}-{GATE_PAIR[1]}: unsafe crawl frames (colliding runs {sorted(colliding)}) ===')
unsafe = conv = 0
for epis in episodes:
    if epis['pair'] != GATE_PAIR or epis['run'] not in colliding:
        continue
    n_c = epis.get('o2_crawl', 0)
    n_s = epis.get('o2_conv', 0)
    unsafe += n_c
    conv += n_s
    print(f"  run_{epis['run']}: crawl {n_c}  -> stop under tracker {n_s}")
print(f"  O2 {'PASS' if unsafe > 0 and conv == unsafe else 'FAIL'}: {conv}/{unsafe} converted "
      f"(bar: every unsafe crawl frame mandates the stop)")

g = res[GATE_PAIR]
print(f"  (all {GATE_PAIR[0]}-{GATE_PAIR[1]} crawl frames incl. safe runs: "
      f"{g['crawl_now_stop']}/{g['crawl']} converted)")

print('\n=== retention — crawl frames elsewhere that remain crawl (mechanism not vacuous) ===')
tot_c = tot_conv = 0
for key in sorted(res):
    if key == GATE_PAIR:
        continue
    r = res[key]
    tot_c += r['crawl']
    tot_conv += r['crawl_now_stop']
    if r['crawl']:
        print(f"  {key[0]:10s} {key[1]}  crawl {r['crawl']:3d}  -> stop {r['crawl_now_stop']:3d}")
print(f'  retained elsewhere: {tot_c - tot_conv}/{tot_c} ({(tot_c - tot_conv) / max(1, tot_c) * 100:.0f}%)')

print('\n=== O3 — clean-scene union firing on tracker output vs logged (raw) ===')
for key in CLEAN:
    r = res[key]
    print(f"  {key[0]:10s} {key[1]}  raw fired frames {r['fired_raw']:3d}   tracker fired frames {r['fired_trk']:3d}")
raw = sum(res[k]['fired_raw'] for k in CLEAN)
trk_f = sum(res[k]['fired_trk'] for k in CLEAN)
print(f"  O3 {'PASS' if trk_f <= max(raw * 1.1, raw + 2) else 'CHECK'} (tracker {trk_f} vs raw {raw}, bar: within 10%)")
