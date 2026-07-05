"""Lightweight association-and-filter tracking layer (iteration 18).

Motivated by two committed findings: VAD's geometric nearest-neighbor IDs manufacture closing
speed through identity jitter (iteration 14), and the router's overlap projection flickers
through velocity dropouts across identity switches (iteration 17). This layer sits between raw
per-frame detections and the monitor, producing a track stream whose velocity survives short
identity breaks and occlusions.

Pure stdlib; world-frame inputs (the caller ego-compensates positions, as the monitor already
does). The interface mirrors what the monitor consumes: position, velocity, stable id.
"""
import math


class Track:
    __slots__ = ('tid', 'x', 'y', 'vx', 'vy', 'ts', 'missed', 'age')

    def __init__(self, tid, x, y, ts):
        self.tid = tid
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.ts = ts
        self.missed = 0
        self.age = 0


class Tracker:
    """Gated greedy nearest-neighbor association with a constant-velocity filter.

    gate: association radius (m) around each track's predicted position.
    alpha: exponential smoothing weight for velocity updates (higher = more responsive).
    max_missed: frames a track coasts (velocity persisted) before it is dropped.
    """

    def __init__(self, gate=3.0, alpha=0.5, max_missed=3):
        self.gate = gate
        self.alpha = alpha
        self.max_missed = max_missed
        self.tracks = []
        self._next = 0

    def reset(self):
        self.tracks = []
        self._next = 0

    def update(self, detections, ts):
        """detections: [(x, y)] world frame; ts: seconds. Returns [(x, y, vx, vy, tid)]."""
        preds = []
        for t in self.tracks:
            dt = max(ts - t.ts, 1e-6)
            preds.append((t.x + t.vx * dt, t.y + t.vy * dt))

        cands = []
        for i, t in enumerate(self.tracks):
            px, py = preds[i]
            for j, (dx, dy) in enumerate(detections):
                d = math.hypot(px - dx, py - dy)
                if d <= self.gate:
                    cands.append((d, i, j))
        cands.sort()

        used_t = set()
        used_d = set()
        for d, i, j in cands:
            if i in used_t or j in used_d:
                continue
            used_t.add(i)
            used_d.add(j)
            t = self.tracks[i]
            dt = max(ts - t.ts, 1e-6)
            mvx = (detections[j][0] - t.x) / dt
            mvy = (detections[j][1] - t.y) / dt
            if t.age == 0:
                t.vx, t.vy = mvx, mvy
            else:
                t.vx = (1 - self.alpha) * t.vx + self.alpha * mvx
                t.vy = (1 - self.alpha) * t.vy + self.alpha * mvy
            t.x, t.y = detections[j]
            t.ts = ts
            t.missed = 0
            t.age += 1

        kept = []
        for i, t in enumerate(self.tracks):
            if i in used_t:
                kept.append(t)
                continue
            t.missed += 1
            if t.missed <= self.max_missed:
                dt = max(ts - t.ts, 1e-6)
                t.x += t.vx * dt
                t.y += t.vy * dt
                t.ts = ts
                kept.append(t)
        self.tracks = kept

        for j, (dx, dy) in enumerate(detections):
            if j in used_d:
                continue
            tr = Track(self._next, dx, dy, ts)
            self._next += 1
            self.tracks.append(tr)

        return [(t.x, t.y, t.vx, t.vy, t.tid) for t in self.tracks]
