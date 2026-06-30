#!/usr/bin/env python3
"""Iteration 3 — deployment metric: route progress (distance driven) alongside collision safety.

progress = ego distance traveled this episode, normalized to the OFF arm's mean for the same scene
(OFF normal driving = 1.0). Episodes are short windows of a longer scene, so absolute ego distance --
not ego/full-reference -- is the honest 'did the car drive' measure. always-brake freezes (~0); a
selective monitor drives the clean scene like OFF and only brakes under threat. safe-progress =
NCAP safety score x progress separates the selective monitor from a trivial always-brake.
"""
import collections
import json
import math
import os
import re
import sys

OUT = '/opt/sentinel-stack/NeuroNCAP/outoutput'
LOG = '/var/log/sentinel-i3.log'
ARMS = ['off', 'always', 'ttc']


def path_len(P):
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


# NCAP scores from the log, in order per (arm, scene)
scores = collections.defaultdict(list)
arm = scene = None
for line in open(LOG):
    m = re.search(r'I3_ARM_START (\w+)', line)
    if m:
        arm = m.group(1); continue
    m = re.search(r'I3PAIR (\w+) (\w+) (\d+)', line)
    if m:
        arm = m.group(1); scene = m.group(2) + '-' + m.group(3); continue
    m = re.search(r'ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+)', line)
    if m and arm and scene:
        scores[(arm, scene)].append((float(m.group(1)), float(m.group(2))))

rows = []
for a in ARMS:
    base = os.path.join(OUT, f'i3-{a}')
    if not os.path.isdir(base):
        continue
    for scene in sorted(os.listdir(base)):
        sdir = os.path.join(base, scene)
        if not os.path.isdir(sdir):
            continue
        runs = sorted([r for r in os.listdir(sdir) if r.startswith('run_')],
                      key=lambda x: int(x.split('_')[1]))
        sc = scores.get((a, scene), [])
        for i, r in enumerate(runs):
            rd = os.path.join(sdir, r)
            try:
                ego = json.load(open(os.path.join(rd, 'ego_poses.json')))
                ep = [[m[0][3], m[1][3]] for _, m in sorted(ego.items())]
                ed = path_len(ep)
                met = json.load(open(os.path.join(rd, 'metrics.json')))
                collide = 1 if met.get('any_collide@0.0s') else 0
                score, impact = (sc[i] if i < len(sc) else (float('nan'), float('nan')))
                rows.append([a, scene, i, score, impact, collide, ed])
            except Exception as e:
                sys.stderr.write(f'{a} {scene} {r}: {e}\n')

# OFF mean ego distance per scene = the normal-driving reference
off_ego = collections.defaultdict(list)
for a, scene, i, s, im, c, ed in rows:
    if a == 'off':
        off_ego[scene].append(ed)
off_mean = {k: (sum(v) / len(v) if v else 1.0) for k, v in off_ego.items()}

for row in rows:
    a, scene, i, s, im, c, ed = row
    base = off_mean.get(scene, 1.0) or 1.0
    row.append(min(1.0, ed / base))  # progress ratio vs OFF normal driving, capped at 1

print('arm\tscene\trun\tscore\timpact\tcollide\tego_m\tprogress')
for a, scene, i, s, im, c, ed, pr in rows:
    print(f'{a}\t{scene}\t{i}\t{s:.3f}\t{im:.2f}\t{c}\t{ed:.1f}\t{pr:.3f}')

print('\n=== per arm (pooled over scenes) ===')
print(f'{"arm":8s} {"score":>6s} {"progress":>9s} {"collision%":>10s} {"ego_m":>7s} {"safe-prog":>9s}')
for a in ARMS:
    rs = [r for r in rows if r[0] == a]
    if not rs:
        continue
    n = len(rs)
    print(f'{a:8s} {sum(r[3] for r in rs)/n:6.2f} {sum(r[7] for r in rs)/n:9.2f} '
          f'{sum(r[5] for r in rs)/n*100:10.0f} {sum(r[6] for r in rs)/n:7.1f} '
          f'{sum(r[3]*r[7] for r in rs)/n:9.2f}')

print('\n=== CLEAN scene (stationary-0103) — the selectivity test ===')
print(f'{"arm":8s} {"score":>6s} {"progress":>9s} {"ego_m":>7s}')
for a in ARMS:
    rs = [r for r in rows if r[0] == a and r[1] == 'stationary-0103']
    if not rs:
        continue
    n = len(rs)
    print(f'{a:8s} {sum(r[3] for r in rs)/n:6.2f} {sum(r[7] for r in rs)/n:9.2f} {sum(r[6] for r in rs)/n:7.1f}')
