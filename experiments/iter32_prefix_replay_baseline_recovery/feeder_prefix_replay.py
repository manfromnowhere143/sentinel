#!/usr/bin/env python3
"""Prefix-replay feeder for iteration-32 baseline recovery."""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import time
import urllib.request
from collections import OrderedDict

import numpy as np
import torch
from PIL import Image
from pyquaternion import Quaternion


CAMS = [
    "CAM_FRONT",
    "CAM_FRONT_RIGHT",
    "CAM_FRONT_LEFT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
]


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
    arr = np.array(Image.open(img_path).convert("RGB"), dtype=np.uint8)
    buf = io.BytesIO()
    torch.save(torch.from_numpy(arr), buf)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def load_prefix_manifest(path):
    rows = json.load(open(path))
    grouped = OrderedDict()
    for row in rows:
        scene = row["scene"]
        grouped.setdefault(scene, OrderedDict())
        sample_index = int(row["sample_index"])
        if sample_index in grouped[scene]:
            raise SystemExit(f"duplicate prefix row {scene}[{sample_index}]")
        grouped[scene][sample_index] = row
    return grouped


def load_tables(meta):
    return {
        k: json.load(open(f"{meta}/{k}.json"))
        for k in ("scene", "sample", "sample_data", "ego_pose", "calibrated_sensor", "sensor")
    }


def keyframe_index(tables):
    calib = {c["token"]: c for c in tables["calibrated_sensor"]}
    sensor_ch = {s["token"]: s["channel"] for s in tables["sensor"]}
    sd_by = {}
    for sd in tables["sample_data"]:
        if not sd["is_key_frame"]:
            continue
        ch = sensor_ch[calib[sd["calibrated_sensor_token"]]["sensor_token"]]
        sd_by[(sd["sample_token"], ch)] = sd
    return sd_by, calib


def scene_chain(scene, samples):
    chain = []
    tok = scene["first_sample_token"]
    while tok:
        chain.append(samples[tok])
        tok = samples[tok]["next"]
    return chain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix-manifest", default="/model/prefix_manifest.json")
    ap.add_argument("--meta", default="/datasets/nuscenes-full/v1.0-trainval")
    ap.add_argument("--data", default="/datasets/nuscenes-full")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out", default="/model/sentinel_e32_prefix_gt.jsonl")
    args = ap.parse_args()

    grouped = load_prefix_manifest(args.prefix_manifest)
    requested_scenes = set(grouped)

    print("loading metadata...", flush=True)
    tables = load_tables(args.meta)
    samples = {s["token"]: s for s in tables["sample"]}
    ego_pose = {p["token"]: p for p in tables["ego_pose"]}
    sd_by, calib = keyframe_index(tables)
    scenes_by_name = {s["name"]: s for s in tables["scene"] if s["name"] in requested_scenes}
    missing = sorted(requested_scenes - set(scenes_by_name))
    if missing:
        raise SystemExit(f"missing scenes in metadata: {missing[:5]} total={len(missing)}")
    ordered_scenes = [scenes_by_name[name] for name in grouped]
    print(f"manifest scenes requested: {len(grouped)} matched: {len(ordered_scenes)}", flush=True)

    base = f"http://127.0.0.1:{args.port}"
    outf = open(args.out, "a")
    done_frames = 0
    target_frames = 0
    for sc in ordered_scenes:
        wanted = grouped[sc["name"]]
        chain = scene_chain(sc, samples)
        poses = []
        for smp in chain:
            sdl = sd_by.get((smp["token"], "LIDAR_TOP"))
            if sdl is None:
                poses.append(None)
                continue
            ep = ego_pose[sdl["ego_pose_token"]]
            poses.append(mat_from(ep["translation"], ep["rotation"]))
        post(f"{base}/reset", {})
        prev_pose = None
        prev_speed = 0.0
        scene_frames = 0
        scene_targets = 0
        for sample_index, smp in enumerate(chain):
            if sample_index not in wanted:
                continue
            rec = wanted[sample_index]
            timestamp_us = int(smp["timestamp"])
            if rec.get("target_row") and timestamp_us != int(rec["timestamp_us"]):
                raise SystemExit(
                    f"timestamp mismatch {sc['name']}[{sample_index}]: "
                    f"manifest={rec['timestamp_us']} metadata={timestamp_us}"
                )
            if poses[sample_index] is None:
                raise SystemExit(f"missing LIDAR pose for {sc['name']}[{sample_index}]")
            if not all((smp["token"], cam) in sd_by for cam in CAMS):
                raise SystemExit(f"missing camera keyframe for {sc['name']}[{sample_index}]")
            cur = poses[sample_index]
            can, speed = emulate_canbus(prev_pose if prev_pose is not None else cur, prev_speed, cur, 0.5)
            prev_pose, prev_speed = cur, speed
            sdl = sd_by[(smp["token"], "LIDAR_TOP")]
            lidar2ego = mat_from(
                calib[sdl["calibrated_sensor_token"]]["translation"],
                calib[sdl["calibrated_sensor_token"]]["rotation"],
            )
            images = {}
            cam2ego = {}
            cam2img = {}
            for cam in CAMS:
                sd = sd_by[(smp["token"], cam)]
                images[cam] = b64_tensor(f"{args.data}/{sd['filename']}")
                cc = calib[sd["calibrated_sensor_token"]]
                cam2ego[cam] = mat_from(cc["translation"], cc["rotation"]).tolist()
                cam2img[cam] = np.array(cc["camera_intrinsic"]).tolist()
            fut = []
            inv = np.linalg.inv(cur)
            for k in range(1, 7):
                j = sample_index + k
                if j < len(chain) and poses[j] is not None:
                    p = inv @ np.append(poses[j][:3, 3], 1.0)
                    fut.append([float(p[0]), float(p[1])])
            lat = fut[-1][1] if len(fut) == 6 else 0.0
            command = 1 if lat > 2.0 else (0 if lat < -2.0 else 2)
            target_row = bool(rec.get("target_row", False))
            context = {
                "scene": sc["name"],
                "split": rec.get("source_split", "prefix_context"),
                "sample_index": sample_index,
                "timestamp_us": timestamp_us,
                "target_row": target_row,
                "source_label": rec.get("source_label"),
                "source_label_name": rec.get("source_label_name", ""),
            }
            payload = {
                "images": images,
                "ego2world": cur.tolist(),
                "canbus": can.tolist(),
                "timestamp": timestamp_us,
                "command": command,
                "calibration": {
                    "lidar2ego": lidar2ego.tolist(),
                    "camera2ego": cam2ego,
                    "camera2image": cam2img,
                },
            }
            t0 = time.time()
            post(f"{base}/sentinel_e32_context", context)
            post(f"{base}/infer", payload)
            row = {
                **context,
                "speed": speed,
                "yaw_rate": can[12],
                "accel": can[7],
                "gt_future": fut,
                "lat_3s": lat,
                "command": command,
            }
            outf.write(json.dumps(row, sort_keys=True) + "\n")
            outf.flush()
            done_frames += 1
            target_frames += int(target_row)
            scene_frames += 1
            scene_targets += int(target_row)
            if done_frames % 25 == 0:
                print(f"frames {done_frames} (last infer {time.time() - t0:.2f}s)", flush=True)
        print(
            f"SCENE_DONE {sc['name']} frames={scene_frames} targets={scene_targets}",
            flush=True,
        )
    print(
        f"FEEDER_DONE rows={done_frames} target_rows={target_frames} scenes={len(ordered_scenes)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
