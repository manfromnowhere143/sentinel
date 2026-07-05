#!/usr/bin/env python3
"""Iteration-21 offline gate B0-B4 for the BEV-conditioned diversity head.

Usage:
  analyze_bev_gate.py <iter12 cand jsonl[.gz]> <bev evalextract jsonl[.gz]> <bev_head.pt>
"""
import gzip
import json
import math
import sys
from types import SimpleNamespace

import numpy as np
import torch
import torch.nn as nn

CAND, EXTR, CKPT = sys.argv[1:4]
DANGER_GAP = 3.5
ESCAPE_GAP = 5.0
H_IMM = 3
B1_N = 12
B2_VALID = 0.90
B3_BAR = 0.780
B4_BAR = 0.75
CURV_MAX = 0.2
ACC_MAX = 4.0
DT = 0.5
CPA_MARGIN = 1.5
TTC_T = 2.5
MIN_CLOSE = 3.0


def load(path):
    op = gzip.open if path.endswith('.gz') else open
    return [json.loads(x) for x in op(path, 'rt') if x.strip()]


def episodes_of(records, is_reset, is_frame):
    eps = []
    cur = None
    for rec in records:
        if is_reset(rec):
            cur = []
            eps.append(cur)
        elif cur is not None and is_frame(rec):
            cur.append(rec)
    return [e for e in eps if e]


def closest_gap(plan, objs, futs):
    best = float('inf')
    for obj, fut in zip(objs, futs):
        ox, oy = obj[0], obj[1]
        mode = fut[0]
        for k in range(min(H_IMM, len(plan))):
            px, py = plan[k]
            ax = ox + (mode[k][0] if k < len(mode) else mode[-1][0])
            ay = oy + (mode[k][1] if k < len(mode) else mode[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


def union_risk_score(plan, objs, futs):
    min_cpa = closest_gap(plan, objs, futs)
    min_ttc = float('inf')
    for obj, fut in zip(objs, futs):
        mode = fut[0]
        if not mode:
            continue
        ox, oy = obj[0], obj[1]
        vx = mode[0][0] / DT
        vy = mode[0][1] / DT
        gap = math.hypot(ox, oy)
        if gap > 1e-3:
            closing = -(vx * ox + vy * oy) / gap
            if closing > max(MIN_CLOSE, 0.5):
                min_ttc = min(min_ttc, gap / closing)
    return max(0.0, CPA_MARGIN - min_cpa) + max(0.0, TTC_T - min_ttc)


class BevHead(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.bev = nn.Sequential(
            nn.Conv2d(channels, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 8 * 8, 1024),
            nn.ReLU(),
        )
        self.kin = nn.Sequential(nn.Linear(6, 64), nn.ReLU())
        self.out = nn.Sequential(
            nn.Linear(1024 + 64, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 8 * 6 * 2),
        )

    def forward(self, bev, kin_cmd):
        z = torch.cat([self.bev(bev), self.kin(kin_cmd)], dim=1)
        return self.out(z).view(-1, 8, 6, 2)


def kinematics(extr_flat, idx, episode_starts):
    if idx > 0 and idx not in episode_starts:
        p0 = np.array(extr_flat[idx - 1]['ego2world'])
        p1 = np.array(extr_flat[idx]['ego2world'])
        dp = np.linalg.inv(p0[:3, :3]) @ (p1[:3, 3] - p0[:3, 3])
        speed = float(dp[0]) / DT
        yaw1 = math.atan2(p1[1, 0], p1[0, 0])
        yaw0 = math.atan2(p0[1, 0], p0[0, 0])
        yaw_rate = ((yaw1 - yaw0 + math.pi) % (2 * math.pi) - math.pi) / DT
    else:
        speed, yaw_rate = 0.0, 0.0
    if idx > 1 and idx not in episode_starts and (idx - 1) not in episode_starts:
        p00 = np.array(extr_flat[idx - 2]['ego2world'])
        p0 = np.array(extr_flat[idx - 1]['ego2world'])
        dp0 = np.linalg.inv(p00[:3, :3]) @ (p0[:3, 3] - p00[:3, 3])
        acc = (speed - float(dp0[0]) / DT) / DT
    else:
        acc = 0.0
    return speed, yaw_rate, acc


def feasible(cand, speed):
    pts = np.vstack([[0.0, 0.0], cand])
    seg = np.diff(pts, axis=0)
    ds = np.linalg.norm(seg, axis=1)
    sp = ds / DT
    if abs(sp[0] - speed) > ACC_MAX * DT + 1.0:
        return False
    if len(sp) > 1 and np.abs(np.diff(sp) / DT).max() > ACC_MAX:
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


def main():
    cand_recs = load(CAND)
    extr_recs = load(EXTR)
    cand_eps = episodes_of(cand_recs, lambda r: r.get('reset', False), lambda r: 'cands' in r)
    if not cand_eps:
        cand_eps = [[r for r in cand_recs if 'cands' in r]]
    extr_eps = episodes_of(extr_recs, lambda r: r.get('reset', False), lambda r: 'bev_pool' in r)
    flat_c = [r for e in cand_eps for r in e]
    flat_x = [r for e in extr_eps for r in e]
    print(f'iter12 frames: {len(flat_c)} | bev extraction frames: {len(flat_x)}')

    ck = torch.load(CKPT, map_location='cpu', weights_only=False)
    model = BevHead(int(ck['channels']))
    model.load_state_dict(ck['state'])
    model.eval()
    mu, sd = ck['mu'], ck['sd']

    episode_starts = set()
    offset = 0
    for episode in extr_eps:
        episode_starts.add(offset)
        offset += len(episode)

    joined = []
    mismatches = []
    for i in range(min(len(flat_c), len(flat_x))):
        c, x = flat_c[i], flat_x[i]
        exe_plan = c['cands'][c['exe_cmd']]
        served = x['traj']
        d0 = math.hypot(exe_plan[0][0] - served[0][0], exe_plan[0][1] - served[0][1])
        if d0 > 0.5:
            mismatches.append((i, d0))
            continue
        speed, yaw_rate, acc = kinematics(flat_x, i, episode_starts)
        joined.append(SimpleNamespace(c=c, x=x, speed=speed, yaw_rate=yaw_rate, acc=acc))

    b0 = len(flat_c) == len(flat_x) == len(joined) and not mismatches
    print('\n=== B0 - extraction integrity ===')
    print(f'  joined {len(joined)} / iter12 {len(flat_c)} / extraction {len(flat_x)}')
    print(f'  executed-plan mismatches: {len(mismatches)}')
    print(f"  B0 {'PASS' if b0 else 'FAIL'}")

    def head_candidates(j):
        bev = np.array(j.x['bev_pool'], dtype=np.float32).reshape(8, 8, 256)
        bev = np.transpose(bev, (2, 0, 1))
        bev = (bev[None] - mu) / sd
        kin = np.array([j.speed, j.yaw_rate, j.acc], dtype=np.float32)
        cmd = np.zeros(3, dtype=np.float32)
        cmd[int(j.x['command'])] = 1.0
        kin_cmd = np.concatenate([kin, cmd])[None]
        with torch.no_grad():
            return model(
                torch.tensor(bev, dtype=torch.float32),
                torch.tensor(kin_cmd, dtype=torch.float32),
            )[0].numpy()

    danger = 0
    escapes = 0
    selector_ok = 0
    selector_total = 0
    valid = 0
    total = 0
    benign_err = []
    infeasible_would_be = 0
    for j in joined:
        objs, futs = j.c['objs'], j.c['futs']
        if not objs:
            continue
        exe_plan = j.c['cands'][j.c['exe_cmd']]
        exe_gap = closest_gap(exe_plan, objs, futs)
        exe_risk = union_risk_score(exe_plan, objs, futs)
        cands = head_candidates(j)
        cand_valid = [feasible(cands[k], j.speed) for k in range(cands.shape[0])]
        valid += sum(cand_valid)
        total += len(cand_valid)
        if exe_gap < DANGER_GAP:
            danger += 1
            frame_escape = False
            frame_selector_ok = False
            for k in range(cands.shape[0]):
                gap = closest_gap(cands[k].tolist(), objs, futs)
                if gap > ESCAPE_GAP and gap > exe_gap:
                    if cand_valid[k]:
                        frame_escape = True
                        if union_risk_score(cands[k].tolist(), objs, futs) < exe_risk:
                            frame_selector_ok = True
                    else:
                        infeasible_would_be += 1
            if frame_escape:
                escapes += 1
                selector_total += 1
                selector_ok += int(frame_selector_ok)
        else:
            exe = np.array(exe_plan[:6])
            errs = [float(np.linalg.norm(cands[k][:len(exe)] - exe, axis=1).mean())
                    for k in range(cands.shape[0])]
            benign_err.append(min(errs))

    esc_rate = escapes / danger if danger else 0.0
    valid_rate = valid / total if total else 0.0
    benign = float(np.mean(benign_err)) if benign_err else float('nan')
    sel_rate = selector_ok / selector_total if selector_total else 0.0
    print('\n=== B1 - feasible escape rate ===')
    print(f'  dangerous frames: {danger}  feasible escapes: {escapes}  rate {esc_rate * 100:.1f}%')
    print(f"  B1 {'PASS' if escapes >= B1_N else 'FAIL'} (bar: at least {B1_N}/37)")
    print('\n=== B2 - candidate feasibility ===')
    print(f'  all-candidate validity: {valid}/{total} = {valid_rate * 100:.1f}%')
    print(f'  infeasible would-be escapes: {infeasible_would_be}')
    print(f"  B2 {'PASS' if valid_rate >= B2_VALID else 'FAIL'} (bar: >= {B2_VALID * 100:.0f}%)")
    print('\n=== B3 - benign fidelity ===')
    print(f'  benign frames: {len(benign_err)}  mean best-of-K error: {benign:.3f} m')
    print(f"  B3 {'PASS' if benign <= B3_BAR else 'FAIL'} (bar: <= {B3_BAR:.3f} m)")
    print('\n=== B4 - selector compatibility ===')
    print(f'  selector-compatible escapes: {selector_ok}/{selector_total} = {sel_rate * 100:.1f}%')
    print(f"  B4 {'PASS' if selector_total and sel_rate >= B4_BAR else 'FAIL'} "
          f"(bar: >= {B4_BAR * 100:.0f}%)")

    gate = b0 and escapes >= B1_N and valid_rate >= B2_VALID and benign <= B3_BAR
    gate = gate and selector_total > 0 and sel_rate >= B4_BAR
    print('\nGATE:', 'PASS - closed-loop pre-registration may be written' if gate else 'FAIL')
    if not gate:
        print('Per HYPOTHESIS.md, no closed-loop run is allowed.')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main()
