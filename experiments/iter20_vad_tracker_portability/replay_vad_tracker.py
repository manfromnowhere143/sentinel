#!/usr/bin/env python3
"""Iteration-20 offline gate: replay VAD-union logs with tracker output.

Usage:
  replay_vad_tracker.py <sentinel-vad20.log> <sentinel_vad20_union.jsonl[.gz]> <vad20-runs.tar.gz>
"""
import collections
import gzip
import json
import math
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sentinel.tracker import Tracker  # noqa: E402

RUNLOG, DECISIONS, RUNS_TAR = sys.argv[1:4]

RUNS_PER_PAIR = 20
DT = 0.5
CPA_MARGIN = 1.5
TTC_T = 2.5
MIN_CLOSE = 3.0
MIN_SCORE = 0.3
MAX_GAP = 30.0
RAW_ID_GATE = 3.0
TRACKER_DEFAULTS = {'gate': 3.0, 'alpha': 0.5, 'max_missed': 3}
SAFETY_SCENES = {'stationary-0103', 'side-0103'}
FRONTAL_SCENE = 'frontal-0103'


def union_pairs(path):
    pairs = []
    for line in open(path, errors='replace'):
        match = re.search(r'VAD20PAIR (\w+) (\w+) (\d+)', line)
        if match and match.group(1) == 'union':
            pairs.append((match.group(2), match.group(3)))
    if not pairs:
        raise SystemExit('no VAD20PAIR union entries found')
    return pairs


def open_jsonl(path):
    return gzip.open(path, 'rt') if path.endswith('.gz') else open(path)


def load_ego_poses(tf, scene, run):
    name = f'vad20-union/{scene}/run_{run}/ego_poses.json'
    try:
        member = tf.getmember(name)
    except KeyError as exc:
        raise SystemExit(f'missing {name} in {RUNS_TAR}') from exc
    with tf.extractfile(member) as handle:
        return {int(ts): mat for ts, mat in json.load(handle).items()}


def to_world(ego, x, y):
    return (
        ego[0][0] * x + ego[0][1] * y + ego[0][3],
        ego[1][0] * x + ego[1][1] * y + ego[1][3],
    )


def raw_assign_ids(state, points):
    ids = [-1] * len(points)
    used = set()
    for i, (cx, cy) in enumerate(points):
        best = -1
        best_dist = RAW_ID_GATE
        for j, (px, py) in enumerate(state['pts']):
            if j in used:
                continue
            dist = math.hypot(cx - px, cy - py)
            if dist < best_dist:
                best = j
                best_dist = dist
        if best >= 0:
            ids[i] = state['ids'][best]
            used.add(best)
        else:
            ids[i] = state['next']
            state['next'] += 1
    state['pts'] = list(points)
    state['ids'] = ids
    return ids


def raw_tracks(raw_id_state, raw_velocity_state, detections, ts):
    ids = raw_assign_ids(raw_id_state, detections)
    out = []
    new_state = {}
    for oid, (wx, wy) in zip(ids, detections):
        vx = vy = 0.0
        if oid in raw_velocity_state:
            px, py, pts = raw_velocity_state[oid]
            dt = max((ts - pts) / 1e6, 1e-6)
            vx = (wx - px) / dt
            vy = (wy - py) / dt
        out.append((wx, wy, vx, vy, oid))
        new_state[oid] = (wx, wy, ts)
    raw_velocity_state.clear()
    raw_velocity_state.update(new_state)
    return out


def union_terms(plan, ego_xy, tracks):
    min_cpa = 1e9
    min_ttc = 1e9
    ego_x, ego_y = ego_xy
    for tx, ty, tvx, tvy, _tid in tracks:
        for k, (px, py) in enumerate(plan):
            t = (k + 1) * DT
            ax = tx + tvx * t
            ay = ty + tvy * t
            min_cpa = min(min_cpa, math.hypot(px - ax, py - ay))
        dx = ego_x - tx
        dy = ego_y - ty
        gap = math.hypot(dx, dy)
        if gap > 1e-3:
            closing = (tvx * dx + tvy * dy) / gap
            if closing > max(MIN_CLOSE, 0.5):
                min_ttc = min(min_ttc, gap / closing)
    return {
        'cpa': min_cpa,
        'ttc': min_ttc,
        'cpa_fire': min_cpa < CPA_MARGIN,
        'ttc_fire': min_ttc < TTC_T,
        'fire': min_cpa < CPA_MARGIN or min_ttc < TTC_T,
    }


def frame_geometry(record, ego):
    plan = [to_world(ego, px, py) for px, py in record['traj']]
    detections = []
    objs = record.get('objs') or []
    scores = record.get('scores') or []
    for i in range(min(len(objs), len(scores))):
        if scores[i] is None or scores[i] < MIN_SCORE:
            continue
        ox = float(objs[i][0])
        oy = float(objs[i][1])
        if math.hypot(ox, oy) > MAX_GAP:
            continue
        detections.append(to_world(ego, ox, oy))
    return plan, (ego[0][3], ego[1][3]), detections


def pct(numer, denom):
    if denom == 0:
        return 0.0
    return numer / denom * 100.0


def main():
    pairs = union_pairs(RUNLOG)
    stats = collections.defaultdict(lambda: collections.Counter())
    episodes = {}
    joined = 0
    missing = 0
    ep = -1
    scene = run = None
    ego_poses = {}
    raw_id_state = {'pts': [], 'ids': [], 'next': 0}
    raw_velocity_state = {}
    tracker = Tracker(**TRACKER_DEFAULTS)

    with tarfile.open(RUNS_TAR) as tf, open_jsonl(DECISIONS) as lines:
        for line in lines:
            record = json.loads(line)
            if record.get('reset'):
                ep += 1
                pair = pairs[min(ep // RUNS_PER_PAIR, len(pairs) - 1)]
                scene = f'{pair[0]}-{pair[1]}'
                run = ep % RUNS_PER_PAIR
                ego_poses = load_ego_poses(tf, scene, run)
                raw_id_state = {'pts': [], 'ids': [], 'next': 0}
                raw_velocity_state = {}
                tracker = Tracker(**TRACKER_DEFAULTS)
                episodes[(scene, run)] = {'raw': False, 'trk': False}
                continue
            if 'traj' not in record:
                continue
            if scene is None:
                raise SystemExit('trajectory frame before reset')
            ts = int(record['ts'])
            ego = ego_poses.get(ts)
            if ego is None:
                missing += 1
                continue
            joined += 1
            plan, ego_xy, detections = frame_geometry(record, ego)
            raw = union_terms(plan, ego_xy, raw_tracks(raw_id_state, raw_velocity_state, detections, ts))
            trk = union_terms(plan, ego_xy, tracker.update(detections, ts / 1e6))
            row = stats[scene]
            row['frames'] += 1
            row['raw_fire_frames'] += int(raw['fire'])
            row['raw_ttc_frames'] += int(raw['ttc_fire'])
            row['raw_cpa_frames'] += int(raw['cpa_fire'])
            row['tracker_fire_frames'] += int(trk['fire'])
            row['tracker_ttc_frames'] += int(trk['ttc_fire'])
            row['tracker_cpa_frames'] += int(trk['cpa_fire'])
            row['raw_ttc_removed_frames'] += int(raw['ttc_fire'] and not trk['fire'])
            if raw['fire']:
                episodes[(scene, run)]['raw'] = True
            if trk['fire']:
                episodes[(scene, run)]['trk'] = True

    print(f'frame join: {joined} joined, {missing} missing ego pose')
    print(f'tracker defaults: {TRACKER_DEFAULTS}')
    print('\n=== per-scene instantaneous replay ===')
    for key in sorted(stats):
        row = stats[key]
        print(
            f"  {key:15s} frames={row['frames']:4d} "
            f"raw_fire={row['raw_fire_frames']:4d} "
            f"raw_ttc={row['raw_ttc_frames']:4d} "
            f"raw_cpa={row['raw_cpa_frames']:4d} "
            f"tracker_fire={row['tracker_fire_frames']:4d} "
            f"tracker_ttc={row['tracker_ttc_frames']:4d} "
            f"tracker_cpa={row['tracker_cpa_frames']:4d} "
            f"raw_ttc_removed={row['raw_ttc_removed_frames']:4d}"
        )

    total_raw_ttc = sum(row['raw_ttc_frames'] for row in stats.values())
    total_removed = sum(row['raw_ttc_removed_frames'] for row in stats.values())
    v1_rate = total_removed / max(1, total_raw_ttc)
    v1_pass = total_raw_ttc > 0 and v1_rate >= 0.80
    print('\n=== V1 — false-closing reduction ===')
    print(
        f'  raw TTC frames removed by tracker-union replay: {total_removed}/{total_raw_ttc} '
        f'({v1_rate * 100:.1f}%; bar >= 80%)'
    )
    print(f"  V1 {'PASS' if v1_pass else 'FAIL'}")

    print('\n=== V2 — safety-scene firing-episode retention ===')
    v2_pass = True
    for safety in sorted(SAFETY_SCENES):
        raw_eps = sum(1 for (sc, _run), e in episodes.items() if sc == safety and e['raw'])
        kept_eps = sum(1 for (sc, _run), e in episodes.items() if sc == safety and e['raw'] and e['trk'])
        retention = kept_eps / max(1, raw_eps)
        ok = raw_eps > 0 and retention >= 0.90
        v2_pass = v2_pass and ok
        print(
            f"  {safety:15s} retained {kept_eps}/{raw_eps} raw firing episodes "
            f"({retention * 100:.1f}%; bar >= 90%) — {'PASS' if ok else 'FAIL'}"
        )

    print('\n=== V3 — frontal selectivity ===')
    frontal = stats[FRONTAL_SCENE]
    raw_frames = frontal['raw_fire_frames']
    trk_frames = frontal['tracker_fire_frames']
    frame_reduction = (raw_frames - trk_frames) / max(1, raw_frames)
    raw_eps = sum(1 for (sc, _run), e in episodes.items() if sc == FRONTAL_SCENE and e['raw'])
    trk_eps = sum(1 for (sc, _run), e in episodes.items() if sc == FRONTAL_SCENE and e['trk'])
    episode_reduction = (raw_eps - trk_eps) / max(1, raw_eps)
    v3_pass = (
        raw_frames > 0
        and raw_eps > 0
        and frame_reduction >= 0.50
        and episode_reduction >= 0.50
    )
    print(
        f'  firing frames raw={raw_frames} tracker={trk_frames} '
        f'reduction={frame_reduction * 100:.1f}% (bar >= 50%)'
    )
    print(
        f'  firing episodes raw={raw_eps} tracker={trk_eps} '
        f'reduction={episode_reduction * 100:.1f}% (bar >= 50%)'
    )
    print(f"  V3 {'PASS' if v3_pass else 'FAIL'}")

    v4_pass = TRACKER_DEFAULTS == {'gate': 3.0, 'alpha': 0.5, 'max_missed': 3}
    print('\n=== V4 — no threshold fit ===')
    print(f"  V4 {'PASS' if v4_pass else 'FAIL'}: defaults used with no sweep")

    gate_pass = v1_pass and v2_pass and v3_pass and v4_pass
    print('\n=== offline gate ===')
    print(f"  ITER20 {'PASS' if gate_pass else 'FAIL'}")
    if not gate_pass:
        print('  Per HYPOTHESIS.md, no VAD closed-loop run is allowed from this iteration.')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main()
