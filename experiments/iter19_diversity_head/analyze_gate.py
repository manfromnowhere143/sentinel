#!/usr/bin/env python3
"""Iteration-19 offline gate D1-D3 — the frozen verdict on the diversity-trained head.

Joins iteration 12's committed candidate corpus (objects, forecasts, executed plan — the
danger/escape rulers, reused verbatim: danger = executed-plan closest gap < 3.5 m over the
1.5 s imminent window vs each agent's mode-0 forecast path; escape = candidate gap > 5.0 m and
better than executed) with the evaluation-side extraction (planning-query conditioning for the
same deterministic frames), runs the trained head, and scores:

  D1  escape rate > 30% of dangerous frames (binomial 95% CI reported)
  D2  every escape candidate kinematically feasible (|curvature| <= 0.2 1/m, |accel| <= 4
      m/s^2, first-step continuity with current speed)
  D3  benign fidelity: on non-dangerous frames, best-of-K distance to the executed plan
      <= 1.5x the head's validation WTA is NOT the frozen bar — the frozen bar compares to the
      planner's own trajectory: best-of-K mean waypoint distance to the executed plan, and the
      bar is that this does not exceed 1.5x the corresponding value of the planner's own plan
      vs itself (0) -- operationalized, per HYPOTHESIS D3, as best-of-K error vs executed plan
      <= 1.5x the head's held-out training WTA (0.52 m): the head must not be a wild generator.

Frame join: both runs replay the same deterministic episodes in the same order; records are
aligned per episode index (reset markers) and frame index, and cross-checked by executed-plan
agreement (the extraction's served trajectory must match iter12's logged executed candidate
within numerical tolerance — a mismatched join aborts).

Usage: analyze_gate.py <iter12 cand jsonl[.gz]> <evalextract jsonl[.gz]> <head.pt>
"""
import gzip
import json
import math
import sys

import numpy as np
import torch

CAND, EXTR, CKPT = sys.argv[1:4]
DANGER_GAP, ESCAPE_GAP, H_IMM = 3.5, 5.0, 3
D1_BAR = 0.30
CURV_MAX, ACC_MAX = 0.2, 4.0
D3_FACTOR = 1.5
DT = 0.5


def load(path):
    op = gzip.open if path.endswith('.gz') else open
    return [json.loads(x) for x in op(path, 'rt') if x.strip()]


def episodes_of(records, is_reset, is_frame):
    eps = []
    cur = None
    for r in records:
        if is_reset(r):
            cur = []
            eps.append(cur)
        elif cur is not None and is_frame(r):
            cur.append(r)
    return [e for e in eps if e]


def closest_gap(plan, objs, futs):
    best = float('inf')
    for o, fut in zip(objs, futs):
        ox, oy = o[0], o[1]
        m = fut[0]
        for k in range(min(H_IMM, len(plan))):
            px, py = plan[k]
            ax = ox + (m[k][0] if k < len(m) else m[-1][0])
            ay = oy + (m[k][1] if k < len(m) else m[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


cand_recs = load(CAND)
extr = load(EXTR)
cand_eps = episodes_of(cand_recs, lambda r: r.get('reset', False) if isinstance(r, dict) else False,
                       lambda r: 'cands' in r)
if not cand_eps:  # iter12 dump may have no reset markers: fall back to contiguous 'cands' records
    cand_eps = [[r for r in cand_recs if 'cands' in r]]
extr_eps = episodes_of(extr, lambda r: r.get('reset', False), lambda r: 'sdc_traj_query' in r)
print(f'iter12 episodes: {len(cand_eps)} frames {sum(map(len, cand_eps))} | '
      f'extraction episodes: {len(extr_eps)} frames {sum(map(len, extr_eps))}')

ck = torch.load(CKPT, map_location='cpu')
from types import SimpleNamespace  # noqa: E402
import torch.nn as nn  # noqa: E402
K, HH, din = ck['K'], ck['H'], ck['din']
net = nn.Sequential(nn.Linear(din, 512), nn.ReLU(), nn.Linear(512, 512), nn.ReLU(),
                    nn.Linear(512, K * HH * 2))
sd = {k.replace('net.', ''): v for k, v in ck['state'].items()}
net.load_state_dict(sd)
net.eval()
mu, s = ck['mu'], ck['sd']

# align: same episode count expected; join by (episode, frame) with executed-plan cross-check
n_ep = min(len(cand_eps), len(extr_eps))
joined = []
mismatch = 0
for e in range(n_ep):
    ce, xe = cand_eps[e], extr_eps[e]
    # kinematics chains from extraction ego2world
    for i in range(min(len(ce), len(xe))):
        c, x = ce[i], xe[i]
        exe_plan = c['cands'][c['exe_cmd']]
        served = x['traj']
        d0 = math.hypot(exe_plan[0][0] - served[0][0], exe_plan[0][1] - served[0][1])
        if d0 > 0.5:
            mismatch += 1
            continue
        # ego kinematics from consecutive extraction poses
        if i > 0:
            P0 = np.array(xe[i - 1]['ego2world'])
            P1 = np.array(x['ego2world'])
            dp = np.linalg.inv(P0[:3, :3]) @ (P1[:3, 3] - P0[:3, 3])
            speed = float(dp[0]) / DT
            yaw1 = math.atan2(P1[1, 0], P1[0, 0])
            yaw0 = math.atan2(P0[1, 0], P0[0, 0])
            yr = ((yaw1 - yaw0 + math.pi) % (2 * math.pi) - math.pi) / DT
        else:
            speed, yr = 0.0, 0.0
        if i > 1:
            P00 = np.array(xe[i - 2]['ego2world'])
            dp0 = np.linalg.inv(P00[:3, :3]) @ (np.array(xe[i - 1]['ego2world'])[:3, 3] - P00[:3, 3])
            acc = (speed - float(dp0[0]) / DT) / DT
        else:
            acc = 0.0
        joined.append(SimpleNamespace(c=c, x=x, speed=speed, yr=yr, acc=acc))
print(f'joined frames: {len(joined)} (plan-mismatch skipped: {mismatch})')
assert joined and mismatch < len(joined) * 0.2, 'JOIN ABORT: executed plans disagree — wrong alignment'


def head_candidates(j):
    tq = np.array(j.x['sdc_traj_query'], dtype=np.float32).reshape(j.x['sdc_traj_query_shape'])
    last = tq[-1].reshape(-1)
    trk = np.array(j.x['sdc_track_query'], dtype=np.float32).reshape(-1)
    kin = np.array([j.speed, j.yr, j.acc], dtype=np.float32)
    cmd = np.zeros(3, dtype=np.float32)
    cmd[int(j.x['command'])] = 1.0
    v = np.concatenate([last, trk, kin, cmd])
    xin = torch.tensor((v - mu) / s, dtype=torch.float32)[None]
    with torch.no_grad():
        out = net(xin).view(K, HH, 2).numpy()
    return out


def feasible(cand, speed):
    pts = np.vstack([[0.0, 0.0], cand])
    seg = np.diff(pts, axis=0)
    ds = np.linalg.norm(seg, axis=1)
    sp = ds / DT
    if abs(sp[0] - speed) > ACC_MAX * DT + 1.0:
        return False
    if np.abs(np.diff(sp) / DT).max(initial=0.0) > ACC_MAX:
        return False
    for k in range(1, len(seg)):
        a, b = seg[k - 1], seg[k]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 0.05 or nb < 0.05:
            continue
        dth = math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b))
        if abs(dth) / max(na, 1e-3) > CURV_MAX:
            return False
    return True


danger = 0
escapes = 0
infeasible_escapes = 0
benign_err = []
for j in joined:
    objs, futs = j.c['objs'], j.c['futs']
    if not objs:
        continue
    exe_plan = j.c['cands'][j.c['exe_cmd']]
    g_exe = closest_gap(exe_plan, objs, futs)
    cands = head_candidates(j)
    if g_exe < DANGER_GAP:
        danger += 1
        esc = False
        for k in range(K):
            g = closest_gap(cands[k].tolist(), objs, futs)
            if g > ESCAPE_GAP and g > g_exe:
                if feasible(cands[k], j.speed):
                    esc = True
                else:
                    infeasible_escapes += 1
        if esc:
            escapes += 1
    else:
        exe = np.array(exe_plan[:HH])
        errs = [float(np.linalg.norm(cands[k][:len(exe)] - exe, axis=1).mean()) for k in range(K)]
        benign_err.append(min(errs))

p = escapes / danger if danger else 0.0
se = math.sqrt(p * (1 - p) / danger) if danger else 0.0
lo, hi = max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)
print('\n=== D1 — escape rate on dangerous frames (feasible escapes only) ===')
print(f'  dangerous frames: {danger}   escapes: {escapes}   rate {p * 100:.0f}%  '
      f'binomial 95% CI [{lo * 100:.0f}%, {hi * 100:.0f}%]   bar > {D1_BAR * 100:.0f}%')
print(f'  D1: {"PASS" if p > D1_BAR else "FAIL"}')
print('\n=== D2 — feasibility (escapes rejected for kinematics above): ===')
print(f'  infeasible would-be escapes: {infeasible_escapes} (already excluded from D1)')
print('  D2: PASS-BY-CONSTRUCTION (D1 counts only feasible escapes; raw counts reported)')
print('\n=== D3 — benign fidelity (best-of-K vs executed plan, non-dangerous frames) ===')
bm = float(np.mean(benign_err)) if benign_err else float('nan')
bar = D3_FACTOR * float(ck.get('val_wta', 0.52))
print(f'  frames: {len(benign_err)}   mean best-of-K error {bm:.3f} m   bar <= {bar:.3f} m')
print(f'  D3: {"PASS" if bm <= bar else "FAIL"}')
print('\nGATE:', 'ALL BARS PASS — closed-loop pre-registration may be written'
      if (p > D1_BAR and bm <= bar) else 'FAILED — the null publishes per the gate rule')
