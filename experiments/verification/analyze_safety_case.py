#!/usr/bin/env python3
"""Safety-engineering view of the union monitor, from committed decision logs alone.

AV safety cases are written in interventions-per-distance, detection lead time, and severity
reduction — not benchmark scores. This derives all three for the iteration-8 union arm:

- false-intervention rate: brake decisions on the benign scene, per km driven;
- detection lead time: episodes are deterministic until the monitor intervenes, so the OFF arm's
  contact time on the same run index is the counterfactual impact moment; lead time =
  t_contact(OFF) - t_first_brake(union). Contact time comes from the scorer's ground-truth actor
  pose (`metrics.json` recall_info.target_actor_in_ego): the actor's planar distance to the ego
  origin, linearly interpolated to the 2.0 m contact plane. Ground truth is used ONLY for this
  offline timing analysis — the monitor itself never sees it;
- severity: impact speed OFF vs union on the same run indices (from the run logs).

Scene assignment follows the run-script order (stationary, frontal, side), 8 episodes each.

Usage: python3 analyze_safety_case.py
"""
import gzip
import json
import math
import os
import re
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, 'evidence')
SCENES = ['stationary-0103', 'frontal-0103', 'side-0103']
CONTACT_M = 2.0


def episodes(jsonl_path):
    """Split a decision log into episodes, keeping file order; scene = block of 8 resets."""
    eps = []
    cur = None
    for line in gzip.open(jsonl_path, 'rt'):
        d = json.loads(line)
        if d.get('reset'):
            cur = {'frames': [], 'brakes': []}
            eps.append(cur)
        elif cur is not None:
            if 'brake' in d:
                d['after_frame'] = len(cur['frames']) - 1
                cur['brakes'].append(d)
            elif 'ts' in d:
                cur['frames'].append(d)
    return eps


def scene_of(i):
    return SCENES[i // 8]


_tmp = tempfile.mkdtemp(prefix='safety_case_')
with tarfile.open(os.path.join(EV, 'runs', 'i8-off.tar.gz')) as t:
    t.extractall(_tmp)


def _interp_xy(ts_list, xy_list, t):
    """Linear interpolation of a timestamped 2D track (timestamps ascending, microseconds)."""
    if t <= ts_list[0]:
        return xy_list[0]
    for (t0, p0), (t1, p1) in zip(zip(ts_list, xy_list), zip(ts_list[1:], xy_list[1:])):
        if t0 <= t <= t1:
            s = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return (p0[0] + (p1[0] - p0[0]) * s, p0[1] + (p1[1] - p0[1]) * s)
    return xy_list[-1]


def contact_ts_gt(scene, run):
    """First time the adversarial actor's world-frame distance to the ego crosses CONTACT_M.

    Uses the simulator's own actor trajectories (actors.json) and the driven ego trajectory
    (ego_poses.json) on the OFF arm — both world-frame — sampled at 10 Hz with linear
    interpolation. The adversary is the actor with the smallest closest-approach to the ego.
    """
    base = os.path.join(_tmp, 'i8-off', scene, f'run_{run}')
    pa, pe = os.path.join(base, 'actors.json'), os.path.join(base, 'ego_poses.json')
    if not (os.path.exists(pa) and os.path.exists(pe)):
        return None
    ego = json.load(open(pe))
    ets = sorted(int(t) for t in ego)
    exy = [(ego[str(t)][0][3], ego[str(t)][1][3]) for t in ets]
    best = (float('inf'), None)
    for actor in json.load(open(pa)):
        ats, aps = actor['timestamps'], actor['poses']
        if len(ats) < 2:
            continue
        axy = [(p[0][3], p[1][3]) for p in aps]
        lo, hi = max(ats[0], ets[0]), min(ats[-1], ets[-1])
        if hi <= lo:
            continue
        t = lo
        first_contact = None
        dmin = float('inf')
        while t <= hi:
            ax, ay = _interp_xy(ats, axy, t)
            ex, ey = _interp_xy(ets, exy, t)
            d = math.hypot(ax - ex, ay - ey)
            dmin = min(dmin, d)
            if d < CONTACT_M and first_contact is None:
                first_contact = t
            t += 100_000  # 10 Hz
        if dmin < best[0]:
            best = (dmin, first_contact)
    return best[1]


off = episodes(os.path.join(EV, 'jsonl', 'sentinel_i8_off.jsonl.gz'))
un = episodes(os.path.join(EV, 'jsonl', 'sentinel_i8_union.jsonl.gz'))
assert len(off) == 24 and len(un) == 24, (len(off), len(un))

print('=== detection lead time (frontal + side episodes that collide under OFF) ===')
leads = []
for i in range(24):
    u = un[i]
    contact_ts = contact_ts_gt(scene_of(i), i % 8)
    if contact_ts is None or not u['brakes']:
        continue
    fi = max(u['brakes'][0]['after_frame'], 0)
    if fi >= len(u['frames']):
        continue
    brake_ts = u['frames'][fi]['ts']
    lead = (contact_ts - brake_ts) / 1e6
    leads.append((scene_of(i), i % 8, lead))
    print(f'  {scene_of(i):16s} run {i % 8}: first brake {lead:+.1f} s before OFF-arm contact')
if leads:
    ls = sorted(x[2] for x in leads)
    print(f'  median lead time: {ls[len(ls)//2]:.1f} s  (n={len(ls)}, min {ls[0]:.1f}, max {ls[-1]:.1f})')
    print('  coverage note: lead time requires the strict 2.0 m center-distance contact crossing '
          'on the OFF arm; episodes whose contact geometry keeps box centers above it are excluded '
          'rather than approximated.')

print('\n=== intervention budget ===')


def ego_km(arm, scene):
    tar = os.path.join(EV, 'runs', f'i8-{arm}.tar.gz')
    with tarfile.open(tar) as t:
        t.extractall(_tmp)
    total = 0.0
    root = os.path.join(_tmp, f'i8-{arm}', scene)
    for r in os.listdir(root):
        p = os.path.join(root, r, 'ego_poses.json')
        if os.path.exists(p):
            e = json.load(open(p))
            P = [[m[0][3], m[1][3]] for _, m in sorted(e.items())]
            total += sum(math.hypot(P[k + 1][0] - P[k][0], P[k + 1][1] - P[k][1])
                         for k in range(len(P) - 1))
    return total / 1000.0


for si, scene in enumerate(SCENES):
    n_brake_eps = sum(1 for i in range(si * 8, si * 8 + 8) if un[i]['brakes'])
    n_events = sum(len(un[i]['brakes']) for i in range(si * 8, si * 8 + 8))
    km = ego_km('union', scene)
    print(f'  {scene:16s} episodes-with-intervention {n_brake_eps}/8   brake frames {n_events}   '
          f'ego {km * 1000:.0f} m')
clean_brakes = sum(len(un[i]['brakes']) for i in range(0, 8))
print(f'  benign-scene false-intervention rate: {clean_brakes} brake frames over '
      f'{ego_km("union", SCENES[0]) * 1000:.0f} m driven')

print('\n=== severity (impact speed, same run indices, from the committed run log) ===')
sc = {}
arm = scene = None
for line in open(os.path.join(EV, 'logs', 'sentinel-i8.log'), errors='replace'):
    m = re.search(r'I8PAIR (\w+) (\w+) (\d+)', line)
    if m:
        arm, scene = m.group(1), m.group(2) + '-' + m.group(3)
        continue
    m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
    if m and arm:
        sc.setdefault((arm, scene), []).append(float(m.group(2)))
for scene in SCENES[1:]:
    o, u = sc[('off', scene)], sc[('union', scene)]
    om = [x for x in o if x > 0]
    um = [x for x in u if x > 0]
    print(f'  {scene:16s} OFF collides {len(om)}/8 mean impact {sum(om) / max(len(om), 1):.1f} m/s   '
          f'union collides {len(um)}/8 mean impact {sum(um) / max(len(um), 1):.1f} m/s')
