#!/usr/bin/env python3
"""Iteration-21 BEV-conditioned diversity head training.

Runs inside the UniAD container on the GPU box after Stage-1 extraction completes.
The iteration-12 evaluation corpus is not read here.
"""
import argparse
import gzip
import json
import random

import numpy as np
import torch
import torch.nn as nn

SEED = 20260706
K = 8
H = 6
DT = 0.5
MARGIN = 1.0
LAMBDA_REP = 0.1
LAMBDA_FEAS = 0.05
CURV_MAX = 0.2
ACC_MAX = 4.0


def open_jsonl(path):
    return gzip.open(path, 'rt') if path.endswith('.gz') else open(path)


def load_corpus(xpath, gpath):
    xs = {}
    for line in open_jsonl(xpath):
        d = json.loads(line)
        if 'bev_pool' in d and d.get('bev_pool_shape') == [8, 8, 256]:
            xs[d['ts']] = d
    gt = {}
    for line in open_jsonl(gpath):
        d = json.loads(line)
        gt[d['ts']] = d
    rows = []
    for ts, d in xs.items():
        g = gt.get(ts)
        if not g or len(g.get('gt_future', [])) != H:
            continue
        bev = np.array(d['bev_pool'], dtype=np.float32).reshape(8, 8, 256)
        bev = np.transpose(bev, (2, 0, 1))  # C,H,W
        kin = np.array([g['speed'], g['yaw_rate'], g['accel']], dtype=np.float32)
        cmd = np.zeros(3, dtype=np.float32)
        cmd[int(d['command'])] = 1.0
        y = np.array(g['gt_future'], dtype=np.float32)
        rows.append((g['scene'], bev, kin, cmd, y))
    return rows


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
            nn.Linear(512, K * H * 2),
        )

    def forward(self, bev, kin_cmd):
        z = torch.cat([self.bev(bev), self.kin(kin_cmd)], dim=1)
        return self.out(z).view(-1, K, H, 2)


def feasibility_penalty(pred, speed):
    zeros = torch.zeros(pred.shape[0], K, 1, 2, device=pred.device, dtype=pred.dtype)
    pts = torch.cat([zeros, pred], dim=2)
    seg = pts[:, :, 1:] - pts[:, :, :-1]
    ds = torch.linalg.norm(seg, dim=-1).clamp_min(1e-4)
    sp = ds / DT
    first = torch.relu(torch.abs(sp[:, :, 0] - speed[:, None]) - (ACC_MAX * DT + 1.0)).mean()
    acc = torch.diff(sp, dim=2) / DT
    acc_pen = torch.relu(torch.abs(acc) - ACC_MAX).mean()
    a = seg[:, :, :-1]
    b = seg[:, :, 1:]
    cross = a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    dot = (a * b).sum(-1)
    dtheta = torch.atan2(cross, dot)
    curv = torch.abs(dtheta) / ds[:, :, :-1]
    curv_pen = torch.relu(curv - CURV_MAX).mean()
    return first + acc_pen + curv_pen


def loss_fn(pred, y, speed):
    d = ((pred - y[:, None]) ** 2).sum(-1).sqrt().mean(-1)
    wta = d.min(dim=1).values.mean()
    ends = pred[:, :, -1, :].contiguous()
    pd = torch.cdist(ends, ends)
    eye = torch.eye(K, device=pred.device, dtype=torch.bool)
    pd = pd.masked_fill(eye[None], float('inf'))
    rep = torch.relu(MARGIN - pd.min(dim=-1).values).mean()
    feas = feasibility_penalty(pred, speed)
    return wta + LAMBDA_REP * rep + LAMBDA_FEAS * feas, wta.item(), rep.item(), feas.item()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract', default='/model/sentinel_bev_extract.jsonl.gz')
    ap.add_argument('--gt', default='/model/sentinel_bev_extract_gt.jsonl.gz')
    ap.add_argument('--out', default='/model/bev_diversity_head.pt')
    args = ap.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    rows = load_corpus(args.extract, args.gt)
    scenes = sorted({r[0] for r in rows})
    val_scenes = set(scenes[-10:])
    tr = [r[1:] for r in rows if r[0] not in val_scenes]
    va = [r[1:] for r in rows if r[0] in val_scenes]
    print(f'corpus rows: {len(rows)}  train: {len(tr)}  val: {len(va)}  scenes: {len(scenes)}',
          flush=True)
    assert tr and va, 'empty train/val split'

    xtr = np.stack([r[0] for r in tr])
    mu = xtr.mean(axis=(0, 2, 3), keepdims=True)
    sd = xtr.std(axis=(0, 2, 3), keepdims=True) + 1e-6
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'

    def to_t(rows_):
        bev = torch.tensor((np.stack([r[0] for r in rows_]) - mu) / sd,
                           dtype=torch.float32, device=dev)
        kin_cmd = torch.tensor(np.stack([np.concatenate([r[1], r[2]]) for r in rows_]),
                               dtype=torch.float32, device=dev)
        y = torch.tensor(np.stack([r[3] for r in rows_]), dtype=torch.float32, device=dev)
        speed = kin_cmd[:, 0]
        return bev, kin_cmd, y, speed

    btr, ktr, ytr, str_ = to_t(tr)
    bva, kva, yva, sva = to_t(va)
    model = BevHead(btr.shape[1]).to(dev)
    nparam = sum(p.numel() for p in model.parameters())
    print(f'params: {nparam} (<=15M: {nparam <= 15_000_000})', flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    best = float('inf')
    patience = 0
    for epoch in range(300):
        model.train()
        perm = torch.randperm(len(btr), device=dev)
        tot = 0.0
        for i in range(0, len(perm), 128):
            idx = perm[i:i + 128]
            opt.zero_grad()
            loss, _wta, _rep, _feas = loss_fn(model(btr[idx], ktr[idx]), ytr[idx], str_[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        model.eval()
        with torch.no_grad():
            _vloss, vwta, vrep, vfeas = loss_fn(model(bva, kva), yva, sva)
        if epoch % 10 == 0:
            print(
                f'epoch {epoch} train {tot / len(btr):.3f} '
                f'val_wta {vwta:.3f} val_rep {vrep:.3f} val_feas {vfeas:.3f}',
                flush=True,
            )
        if vwta < best - 1e-4:
            best = vwta
            patience = 0
            torch.save({
                'state': model.state_dict(),
                'mu': mu,
                'sd': sd,
                'channels': btr.shape[1],
                'K': K,
                'H': H,
                'seed': SEED,
                'val_wta': best,
                'params': nparam,
                'model': 'bev8x8_cnn_mlp',
            }, args.out)
        else:
            patience += 1
            if patience >= 20:
                break
    print(f'TRAIN_DONE best_val_wta {best:.3f} -> {args.out}', flush=True)


if __name__ == '__main__':
    main()
