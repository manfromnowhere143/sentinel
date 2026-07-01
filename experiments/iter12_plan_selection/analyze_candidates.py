#!/usr/bin/env python3
"""Checkpoint D — does a safer command-conditioned plan exist when the default plan is dangerous?

Reads the per-frame candidate log written by patch_candidate_logging.py and, for every frame,
computes the G1-validated risk term for each of the three candidate plans: the closest predicted
approach between the candidate ego trajectory and every agent's own forecast displacement
(mode 0, the planner's most-likely mode), in ego coordinates, over the imminent horizon.

The pre-condition of the plan-selection thesis is answered per dangerous frame:
  danger  = the executed plan's closest predicted gap < DANGER_GAP
  escape  = some other command's plan has closest gap > ESCAPE_GAP (and > executed's)
If dangerous frames consistently have an escape candidate, re-ranking can prevent the collision;
if the three candidates collapse to the same trajectory under threat, that is the (reportable)
negative answer and the effort pivots to VAD's native modes.

Usage: analyze_candidates.py <sentinel_cand.jsonl> [danger_gap] [escape_gap] [horizon_steps]
"""
import json
import math
import sys

CMD = {0: 'right', 1: 'left', 2: 'straight'}
path = sys.argv[1]
DANGER_GAP = float(sys.argv[2]) if len(sys.argv) > 2 else 3.5
ESCAPE_GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
H = int(sys.argv[4]) if len(sys.argv) > 4 else 3  # plan steps at 0.5 s -> 1.5 s imminent window


def closest_gap(plan, objs, futs):
    """Min distance between the plan and each agent's forecast displacement path (mode 0)."""
    best = float('inf')
    for o, fut in zip(objs, futs):
        ox, oy = o[0], o[1]
        m = fut[0]  # most-likely mode: 12 x 2 displacements from the agent position
        for k in range(min(H, len(plan))):
            px, py = plan[k]
            ax = ox + (m[k][0] if k < len(m) else m[-1][0])
            ay = oy + (m[k][1] if k < len(m) else m[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


frames = [json.loads(x) for x in open(path) if x.strip()]
print(f'frames: {len(frames)}')

danger_frames = 0
escape_frames = 0
divergence = []  # max pairwise endpoint distance between candidates, per frame
per_cmd_gap_when_danger = {0: [], 1: [], 2: []}

for fr in frames:
    cands, objs, futs = fr['cands'], fr['objs'], fr['futs']
    if not objs:
        continue
    gaps = {c: closest_gap(cands[c], objs, futs) for c in (0, 1, 2)}
    exe = fr['exe_cmd']
    d = max(
        math.hypot(cands[a][-1][0] - cands[b][-1][0], cands[a][-1][1] - cands[b][-1][1])
        for a in (0, 1, 2) for b in (0, 1, 2)
    )
    divergence.append(d)
    if gaps[exe] < DANGER_GAP:
        danger_frames += 1
        for c in (0, 1, 2):
            per_cmd_gap_when_danger[c].append(gaps[c])
        alt = max((g for c, g in gaps.items() if c != exe), default=0.0)
        if alt > ESCAPE_GAP and alt > gaps[exe]:
            escape_frames += 1

print(f'candidate divergence (max endpoint distance between the 3 plans): '
      f'median={sorted(divergence)[len(divergence)//2]:.2f} m  max={max(divergence):.2f} m')
print(f'dangerous frames (executed-plan closest gap < {DANGER_GAP} m): {danger_frames}')
if danger_frames:
    for c in (0, 1, 2):
        g = per_cmd_gap_when_danger[c]
        print(f'  command {c} ({CMD[c]:8s}): mean gap in danger {sum(g)/len(g):.2f} m')
    print(f'ESCAPE EXISTS (alt gap > {ESCAPE_GAP} m and better than executed): '
          f'{escape_frames}/{danger_frames} = {escape_frames/danger_frames*100:.0f}%')
print('\nVERDICT: ' + (
    'a low-risk alternative command exists in a meaningful share of dangerous frames -> '
    'the re-ranker has room to prevent.' if danger_frames and escape_frames / danger_frames > 0.3
    else 'the command-conditioned candidates collapse under threat -> pivot to VAD native modes.'
) if danger_frames else 'VERDICT: no dangerous frames in this log — run on the collision scenes.')
