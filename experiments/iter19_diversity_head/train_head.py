#!/usr/bin/env python3
"""Iteration-19 diversity head training (runs inside the uniad container on the box).

Per the frozen pre-registration: K=8 candidates over the 6-step horizon, winner-takes-all
imitation plus inter-candidate repulsion, <=5M parameters, planner frozen (this trains on the
extracted conditioning corpus only). Scene-level split within the 60 disjoint train scenes for
early stopping; the iteration-12 corpus is never touched here (evaluation-only, per the data
discipline whose violation voids the result).

Fixed choices (logged, not swept): last decoder layer of sdc_traj_query + sdc_track_query +
kinematics + command one-hot as input; hidden 512x512; Adam 1e-3; batch 256; WTA L2 +
lambda_rep * hinge(margin - min pairwise endpoint distance), margin 1.0 m, lambda_rep 0.1;
seed 20260706; early stop on val WTA (patience 20, max 300 epochs).
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
MARGIN = 1.0
LAMBDA_REP = 0.1


def load_corpus(xpath, gpath):
    op = gzip.open if xpath.endswith('.gz') else open
    xs = {}
    for line in op(xpath, 'rt'):
        d = json.loads(line)
        if 'sdc_traj_query' in d:
            xs[d['ts']] = d
    gt = {}
    op = gzip.open if gpath.endswith('.gz') else open
    for line in op(gpath, 'rt'):
        d = json.loads(line)
        gt[d['ts']] = d
    rows = []
    for ts, d in xs.items():
        g = gt.get(ts)
        if not g or len(g['gt_future']) != H:
            continue
        tq = np.array(d['sdc_traj_query'], dtype=np.float32).reshape(d['sdc_traj_query_shape'])
        last = tq[-1].reshape(-1)  # last decoder layer: (1,6,256) -> 1536
        trk = np.array(d['sdc_track_query'], dtype=np.float32).reshape(-1)  # 256
        kin = np.array([g['speed'], g['yaw_rate'], g['accel']], dtype=np.float32)
        cmd = np.zeros(3, dtype=np.float32)
        cmd[int(d['command'])] = 1.0
        x = np.concatenate([last, trk, kin, cmd])
        y = np.array(g['gt_future'], dtype=np.float32)  # (6,2)
        rows.append((g['scene'], x, y))
    return rows


class Head(nn.Module):
    def __init__(self, din):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(din, 512), nn.ReLU(),
            nn.Linear(512, 512), nn.ReLU(),
            nn.Linear(512, K * H * 2),
        )

    def forward(self, x):
        return self.net(x).view(-1, K, H, 2)


def loss_fn(pred, y):
    # WTA: best-of-K L2 to the logged future
    d = ((pred - y[:, None]) ** 2).sum(-1).sqrt().mean(-1)  # (B,K) mean waypoint dist
    wta = d.min(dim=1).values.mean()
    # repulsion on endpoints: hinge on min pairwise distance
    ends = pred[:, :, -1, :]  # (B,K,2)
    pd = torch.cdist(ends, ends)  # (B,K,K)
    eye = torch.eye(K, device=pred.device, dtype=torch.bool)
    pd = pd.masked_fill(eye[None], float('inf'))
    minpd = pd.min(dim=-1).values  # (B,K)
    rep = torch.relu(MARGIN - minpd).mean()
    return wta + LAMBDA_REP * rep, wta.item(), rep.item()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract', default='/model/sentinel_extract.jsonl')
    ap.add_argument('--gt', default='/model/sentinel_extract_gt.jsonl')
    ap.add_argument('--out', default='/model/diversity_head.pt')
    args = ap.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    rows = load_corpus(args.extract, args.gt)
    scenes = sorted({r[0] for r in rows})
    val_scenes = set(scenes[-10:])
    tr = [(x, y) for s, x, y in rows if s not in val_scenes]
    va = [(x, y) for s, x, y in rows if s in val_scenes]
    print(f'corpus rows: {len(rows)}  train: {len(tr)}  val: {len(va)}  scenes: {len(scenes)}', flush=True)

    Xtr = np.stack([x for x, _ in tr])
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'

    def to_t(pairs):
        X = torch.tensor((np.stack([x for x, _ in pairs]) - mu) / sd, dtype=torch.float32, device=dev)
        Y = torch.tensor(np.stack([y for _, y in pairs]), dtype=torch.float32, device=dev)
        return X, Y

    Xtr_t, Ytr_t = to_t(tr)
    Xva_t, Yva_t = to_t(va)
    model = Head(Xtr_t.shape[1]).to(dev)
    nparam = sum(p.numel() for p in model.parameters())
    print(f'params: {nparam} (<=5M: {nparam <= 5_000_000})', flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    best = float('inf')
    patience = 0
    for epoch in range(300):
        model.train()
        perm = torch.randperm(len(Xtr_t), device=dev)
        tot = 0.0
        for i in range(0, len(perm), 256):
            idx = perm[i:i + 256]
            opt.zero_grad()
            loss, wta, rep = loss_fn(model(Xtr_t[idx]), Ytr_t[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        model.eval()
        with torch.no_grad():
            _, vwta, vrep = loss_fn(model(Xva_t), Yva_t)
        if epoch % 10 == 0:
            print(f'epoch {epoch}  train {tot / len(Xtr_t):.3f}  val_wta {vwta:.3f}  val_rep {vrep:.3f}', flush=True)
        if vwta < best - 1e-4:
            best = vwta
            patience = 0
            torch.save({'state': model.state_dict(), 'mu': mu, 'sd': sd,
                        'din': Xtr_t.shape[1], 'K': K, 'H': H, 'seed': SEED,
                        'val_wta': best, 'params': nparam}, args.out)
        else:
            patience += 1
            if patience >= 20:
                break
    print(f'TRAIN_DONE best_val_wta {best:.3f} -> {args.out}', flush=True)


if __name__ == '__main__':
    main()
