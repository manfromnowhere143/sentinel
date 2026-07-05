#!/usr/bin/env python3
"""Iteration-19 extraction feeder: drives the patched /infer server with real nuScenes
keyframes from the 60 disjoint train scenes, replicating the orchestrator's exact dialect
(base64 torch-saved image tensors; 16-dim emulated canbus from consecutive poses; per-frame
calibration). Runs INSIDE the model container (torch available; /datasets mounted).

Dumps its own ground-truth sidecar (ts -> ego kinematics + future waypoints in current ego
frame + derived command) to merge with the server's conditioning dump by timestamp.

Command convention (nuScenes/UniAD): 0=RIGHT, 1=LEFT, 2=FORWARD, derived from the +3 s
ego-frame lateral displacement (y > +2 m -> LEFT, y < -2 m -> RIGHT). The raw displacement is
also dumped so the mapping can be re-derived offline if the convention is ever questioned.
"""
import argparse
import base64
import io
import json
import math
import time
import urllib.request

import numpy as np
import torch
from PIL import Image
from pyquaternion import Quaternion

CAMS = ['CAM_FRONT', 'CAM_FRONT_RIGHT', 'CAM_FRONT_LEFT', 'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT']


def mat_from(translation, rotation):
    m = np.eye(4)
    m[:3, :3] = Quaternion(rotation).rotation_matrix
    m[:3, 3] = translation
    return m


def quaternion_yaw(q: Quaternion) -> float:
    v = np.dot(q.rotation_matrix, np.array([1, 0, 0]))
    return float(np.arctan2(v[1], v[0]))


def emulate_canbus(prev_pose, prev_speed, current_pose, delta_t):
    """Port of neuro_ncap.components.nuscenes_api.emulate_nuscenes_canbus_signals."""
    def nusc_quat(rot):
        yaw = quaternion_yaw(Quaternion(matrix=rot[:3, :3]))
        return Quaternion(axis=[0, 0, 1], radians=yaw)

    can = np.zeros(16)
    can[:3] = current_pose[:3, 3]
    rotation = nusc_quat(current_pose)
    can[3:7] = rotation.elements
    delta_yaw = quaternion_yaw(rotation) - quaternion_yaw(nusc_quat(prev_pose))
    delta_yaw = (delta_yaw + math.pi) % (2 * math.pi) - math.pi
    yaw_rate = delta_yaw / delta_t
    delta = np.linalg.inv(prev_pose[:3, :3]) @ (current_pose[:3, 3] - prev_pose[:3, 3])
    speed = float(delta[0]) / delta_t
    accel = (speed - prev_speed) / delta_t
    can[7] = accel
    can[9] = 9.81
    can[12] = yaw_rate
    can[13] = speed
    return can, speed


def b64_tensor(img_path):
    arr = np.array(Image.open(img_path).convert('RGB'), dtype=np.uint8)
    buf = io.BytesIO()
    torch.save(torch.from_numpy(arr), buf)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenes', default='/tmp/train_scenes.txt')
    ap.add_argument('--meta', default='/datasets/nuscenes/v1.0-trainval')
    ap.add_argument('--data', default='/datasets/nuscenes')
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--out', default='/model/sentinel_extract_gt.jsonl')
    args = ap.parse_args()

    names = set(open(args.scenes).read().split())
    print('loading metadata...', flush=True)
    J = {k: json.load(open(f'{args.meta}/{k}.json'))
         for k in ('scene', 'sample', 'sample_data', 'ego_pose', 'calibrated_sensor', 'sensor')}
    scenes = [s for s in J['scene'] if s['name'] in names]
    samples = {s['token']: s for s in J['sample']}
    ego_pose = {p['token']: p for p in J['ego_pose']}
    calib = {c['token']: c for c in J['calibrated_sensor']}
    sensor_ch = {s['token']: s['channel'] for s in J['sensor']}
    # keyframe sample_data by (sample_token, channel)
    sd_by = {}
    for sd in J['sample_data']:
        if not sd['is_key_frame']:
            continue
        ch = sensor_ch[calib[sd['calibrated_sensor_token']]['sensor_token']]
        sd_by[(sd['sample_token'], ch)] = sd
    print(f'scenes matched: {len(scenes)}', flush=True)

    base = f'http://127.0.0.1:{args.port}'
    outf = open(args.out, 'a')
    done_frames = 0
    for sc in scenes:
        chain = []
        tok = sc['first_sample_token']
        while tok:
            chain.append(samples[tok])
            tok = samples[tok]['next']
        # world poses per sample from LIDAR_TOP
        poses = []
        for smp in chain:
            sdl = sd_by.get((smp['token'], 'LIDAR_TOP'))
            if sdl is None:
                poses.append(None)
                continue
            ep = ego_pose[sdl['ego_pose_token']]
            poses.append(mat_from(ep['translation'], ep['rotation']))
        post(f'{base}/reset', {})
        prev_pose = None
        prev_speed = 0.0
        for i, smp in enumerate(chain):
            if poses[i] is None:
                continue
            cams_ok = all((smp['token'], c) in sd_by for c in CAMS)
            if not cams_ok:
                continue
            cur = poses[i]
            can, speed = emulate_canbus(prev_pose if prev_pose is not None else cur,
                                        prev_speed, cur, 0.5)
            prev_pose, prev_speed = cur, speed
            sdl = sd_by[(smp['token'], 'LIDAR_TOP')]
            lidar2ego = mat_from(calib[sdl['calibrated_sensor_token']]['translation'],
                                 calib[sdl['calibrated_sensor_token']]['rotation'])
            images = {}
            cam2ego = {}
            cam2img = {}
            skip = False
            for c in CAMS:
                sd = sd_by[(smp['token'], c)]
                path = f"{args.data}/{sd['filename']}"
                try:
                    images[c] = b64_tensor(path)
                except Exception:
                    skip = True
                    break
                cc = calib[sd['calibrated_sensor_token']]
                cam2ego[c] = mat_from(cc['translation'], cc['rotation']).tolist()
                cam2img[c] = np.array(cc['camera_intrinsic']).tolist()
            if skip:
                continue
            # GT future: next 6 keyframes' positions in current ego frame
            fut = []
            inv = np.linalg.inv(cur)
            for k in range(1, 7):
                if i + k < len(chain) and poses[i + k] is not None:
                    p = inv @ np.append(poses[i + k][:3, 3], 1.0)
                    fut.append([float(p[0]), float(p[1])])
            lat = fut[-1][1] if len(fut) == 6 else 0.0
            command = 1 if lat > 2.0 else (0 if lat < -2.0 else 2)
            payload = {
                'images': images,
                'ego2world': cur.tolist(),
                'canbus': can.tolist(),
                'timestamp': int(smp['timestamp']),
                'command': command,
                'calibration': {'lidar2ego': lidar2ego.tolist(),
                                'camera2ego': cam2ego, 'camera2image': cam2img},
            }
            t0 = time.time()
            post(f'{base}/infer', payload)
            outf.write(json.dumps({'ts': int(smp['timestamp']), 'scene': sc['name'],
                                   'speed': speed, 'yaw_rate': can[12], 'accel': can[7],
                                   'gt_future': fut, 'lat_3s': lat, 'command': command}) + '\n')
            outf.flush()
            done_frames += 1
            if done_frames % 50 == 0:
                print(f'frames {done_frames} (last infer {time.time() - t0:.2f}s)', flush=True)
    print(f'FEEDER_DONE frames={done_frames}', flush=True)


if __name__ == '__main__':
    main()
