#!/usr/bin/env python3
"""Build the iter23 availability and split manifest.

This script is metadata/file-existence only. It reads official nuScenes train scene names,
nuScenes metadata tables, and local staged sample files. It writes scene names, sample indices,
timestamps, counts, and hashes; it never writes nuScenes scene/sample tokens.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT = "iter23_s0_hardened_causal_localization"
MIN_ELIGIBLE_SCENES = 36
MIN_SCENE_KEYFRAMES = 24
MIN_HELDOUT_KEYFRAMES = 200
CAMS = ("CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_FRONT_LEFT", "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT")
REQUIRED_CHANNELS = (*CAMS, "LIDAR_TOP")

NEURO_NCAP_OFFICIAL_SCENE_IDS = [
    "0099",
    "0101",
    "0103",
    "0106",
    "0108",
    "0110",
    "0278",
    "0331",
    "0346",
    "0783",
    "0796",
    "0921",
    "0923",
    "0966",
]
NEURO_NCAP_OFFICIAL_SCENES = [f"scene-{sid}" for sid in NEURO_NCAP_OFFICIAL_SCENE_IDS]
ITER12_EVALUATION_SCENES = ["scene-0103"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def read_train_scenes(path: Path) -> list[str]:
    scenes = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(scenes) != 700:
        raise SystemExit(f"expected 700 official train scenes, found {len(scenes)} in {path}")
    if len(set(scenes)) != len(scenes):
        raise SystemExit(f"duplicate scene names in {path}")
    bad = [s for s in scenes if not s.startswith("scene-")]
    if bad:
        raise SystemExit(f"non-scene entries in {path}: {bad[:5]}")
    return scenes


def table_by_token(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["token"]: row for row in rows}


def keyframe_index(
    sample_data: list[dict[str, Any]],
    calibrated_sensor: list[dict[str, Any]],
    sensor: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    calib = table_by_token(calibrated_sensor)
    sensor_channel = {row["token"]: row["channel"] for row in sensor}
    by_sample_channel = {}
    for row in sample_data:
        if not row.get("is_key_frame"):
            continue
        sensor_token = calib[row["calibrated_sensor_token"]]["sensor_token"]
        channel = sensor_channel[sensor_token]
        by_sample_channel[(row["sample_token"], channel)] = row
    return by_sample_channel


def scene_chain(scene: dict[str, Any], samples: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chain = []
    token = scene["first_sample_token"]
    while token:
        sample = samples[token]
        chain.append(sample)
        token = sample["next"]
    return chain


def split_hash(scene_name: str) -> str:
    return hashlib.sha256(f"iter23:{scene_name}".encode()).hexdigest()


def split_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    fit_n = (len(records) * 60) // 100
    calibration_n = (len(records) * 20) // 100
    return {
        "fit": records[:fit_n],
        "calibration": records[fit_n : fit_n + calibration_n],
        "heldout": records[fit_n + calibration_n :],
    }


def availability_record(
    scene: dict[str, Any],
    samples: dict[str, dict[str, Any]],
    sample_channel: dict[tuple[str, str], dict[str, Any]],
    data_root: Path,
) -> tuple[dict[str, Any], Counter[str]]:
    frames = []
    reasons: Counter[str] = Counter()
    chain = scene_chain(scene, samples)
    for sample_index, sample in enumerate(chain):
        missing_channel = False
        missing_file = False
        for channel in REQUIRED_CHANNELS:
            row = sample_channel.get((sample["token"], channel))
            if row is None:
                reasons[f"missing_{channel}"] += 1
                missing_channel = True
                continue
            if channel in CAMS and not (data_root / row["filename"]).exists():
                reasons[f"missing_file_{channel}"] += 1
                missing_file = True
        if not missing_channel and not missing_file:
            frames.append(
                {
                    "sample_index": sample_index,
                    "timestamp_us": int(sample["timestamp"]),
                }
            )
    record = {
        "name": scene["name"],
        "nbr_samples": int(scene["nbr_samples"]),
        "available_keyframes": len(frames),
        "split_hash": split_hash(scene["name"]),
        "first_timestamp_us": frames[0]["timestamp_us"] if frames else None,
        "last_timestamp_us": frames[-1]["timestamp_us"] if frames else None,
        "frames": frames,
    }
    return record, reasons


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--meta",
        default=".evidence-staging/nuscenes-mine/v1.0-trainval",
        help="nuScenes v1.0-trainval metadata directory",
    )
    parser.add_argument(
        "--data-root",
        default=".evidence-staging/nuscenes-mine",
        help="nuScenes data root containing samples/",
    )
    parser.add_argument(
        "--train-scenes",
        default="experiments/iter22_causal_planner_interpretability/official_train_scenes.txt",
        help="official nuscenes.utils.splits.train scene-name list",
    )
    parser.add_argument(
        "--out-dir",
        default="experiments/iter23_s0_hardened_causal_localization",
        help="directory for availability_manifest.json and audit sidecars",
    )
    args = parser.parse_args()

    meta = Path(args.meta)
    data_root = Path(args.data_root)
    train_scenes_path = Path(args.train_scenes)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    table_paths = {
        "scene": meta / "scene.json",
        "sample": meta / "sample.json",
        "sample_data": meta / "sample_data.json",
        "calibrated_sensor": meta / "calibrated_sensor.json",
        "sensor": meta / "sensor.json",
    }
    for name, path in table_paths.items():
        if not path.exists():
            raise SystemExit(f"missing {name} table: {path}")
    if not data_root.exists():
        raise SystemExit(f"missing data root: {data_root}")

    train_scenes = read_train_scenes(train_scenes_path)
    scene_rows = read_json(table_paths["scene"])
    sample_rows = read_json(table_paths["sample"])
    sample_data_rows = read_json(table_paths["sample_data"])
    calibrated_sensor_rows = read_json(table_paths["calibrated_sensor"])
    sensor_rows = read_json(table_paths["sensor"])

    scenes_by_name = {row["name"]: row for row in scene_rows}
    samples = table_by_token(sample_rows)
    sample_channel = keyframe_index(sample_data_rows, calibrated_sensor_rows, sensor_rows)

    missing_from_scene_json = sorted(set(train_scenes) - set(scenes_by_name))
    if missing_from_scene_json:
        raise SystemExit(
            "train scenes missing from scene.json: " + ", ".join(missing_from_scene_json[:10])
        )

    excluded = sorted(set(NEURO_NCAP_OFFICIAL_SCENES) | set(ITER12_EVALUATION_SCENES))
    excluded_train = sorted(set(train_scenes) & set(excluded))
    candidate_names = [name for name in train_scenes if name not in set(excluded)]

    ineligible = []
    eligible = []
    reason_counts: Counter[str] = Counter()
    for name in candidate_names:
        record, reasons = availability_record(scenes_by_name[name], samples, sample_channel, data_root)
        reason_counts.update(reasons)
        if record["available_keyframes"] >= MIN_SCENE_KEYFRAMES:
            eligible.append(record)
        else:
            ineligible.append(
                {
                    "name": name,
                    "nbr_samples": record["nbr_samples"],
                    "available_keyframes": record["available_keyframes"],
                    "reason_counts": dict(reasons),
                }
            )

    eligible_sorted = sorted(eligible, key=lambda r: (r["split_hash"], r["name"]))
    splits = split_records(eligible_sorted)
    heldout_keyframes = sum(int(r["available_keyframes"]) for r in splits["heldout"])
    availability_pass = len(eligible_sorted) >= MIN_ELIGIBLE_SCENES and heldout_keyframes >= MIN_HELDOUT_KEYFRAMES

    manifest = {
        "experiment": EXPERIMENT,
        "hypothesis": "experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md",
        "stage": "availability_and_split_manifest",
        "join_key": ["scene", "sample_index", "timestamp_us"],
        "source": {
            "meta": str(meta),
            "data_root": str(data_root),
            "official_train_scenes": str(train_scenes_path),
            "official_train_scenes_sha256": sha256_file(train_scenes_path),
            "table_sha256": {name: sha256_file(path) for name, path in table_paths.items()},
        },
        "availability_gate": {
            "min_eligible_scenes": MIN_ELIGIBLE_SCENES,
            "min_scene_keyframes": MIN_SCENE_KEYFRAMES,
            "min_heldout_keyframes": MIN_HELDOUT_KEYFRAMES,
            "pass": availability_pass,
        },
        "exclusions": {
            "neuro_ncap_official_scene_ids": NEURO_NCAP_OFFICIAL_SCENE_IDS,
            "neuro_ncap_official_scene_names": NEURO_NCAP_OFFICIAL_SCENES,
            "iteration12_evaluation_scene_names": ITER12_EVALUATION_SCENES,
            "excluded_train_scene_names": excluded_train,
        },
        "selection_rule": (
            "Exclude NeuroNCAP/iteration-12 scene names; require local keyframe availability; "
            "sort eligible scenes by SHA256('iter23:<scene_name>'); assign first 60% fit, "
            "next 20% calibration, remainder heldout."
        ),
        "counts": {
            "official_train_scene_count": len(train_scenes),
            "scene_json_scene_count": len(scene_rows),
            "candidate_scene_count_after_exclusions": len(candidate_names),
            "excluded_scene_count": len(excluded),
            "excluded_train_scene_count": len(excluded_train),
            "eligible_scene_count": len(eligible_sorted),
            "ineligible_scene_count": len(ineligible),
            "fit_scene_count": len(splits["fit"]),
            "calibration_scene_count": len(splits["calibration"]),
            "heldout_scene_count": len(splits["heldout"]),
            "fit_keyframe_count": sum(int(r["available_keyframes"]) for r in splits["fit"]),
            "calibration_keyframe_count": sum(
                int(r["available_keyframes"]) for r in splits["calibration"]
            ),
            "heldout_keyframe_count": heldout_keyframes,
            "availability_reason_counts": dict(sorted(reason_counts.items())),
        },
        "splits": splits,
        "ineligible_preview": ineligible[:50],
    }

    manifest_path = out_dir / "availability_manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(manifest_text)
    manifest_sha = hashlib.sha256(manifest_text.encode()).hexdigest()

    write_text(out_dir / "availability_manifest.sha256", f"{manifest_sha}  availability_manifest.json")
    command = "python3 " + shlex.join([sys.argv[0], *sys.argv[1:]])
    write_text(out_dir / "availability_manifest.command.txt", command)
    report = [
        "iter23 S0-hardened availability manifest report",
        f"availability_pass: {availability_pass}",
        f"official_train_scene_count: {len(train_scenes)}",
        f"candidate_scene_count_after_exclusions: {len(candidate_names)}",
        f"excluded_scene_names: {' '.join(excluded)}",
        f"excluded_train_scene_names: {' '.join(excluded_train) if excluded_train else '(none)'}",
        f"eligible_scene_count: {len(eligible_sorted)}",
        f"ineligible_scene_count: {len(ineligible)}",
        f"fit_scene_count: {len(splits['fit'])}",
        f"calibration_scene_count: {len(splits['calibration'])}",
        f"heldout_scene_count: {len(splits['heldout'])}",
        f"heldout_keyframe_count: {heldout_keyframes}",
        "fit: " + " ".join(r["name"] for r in splits["fit"]),
        "calibration: " + " ".join(r["name"] for r in splits["calibration"]),
        "heldout: " + " ".join(r["name"] for r in splits["heldout"]),
    ]
    write_text(out_dir / "availability_manifest.exclusions.txt", "\n".join(report))

    print(f"wrote {manifest_path}")
    print(f"sha256 {manifest_sha}")
    print(
        "counts "
        f"eligible={len(eligible_sorted)} ineligible={len(ineligible)} "
        f"fit={len(splits['fit'])} calibration={len(splits['calibration'])} "
        f"heldout={len(splits['heldout'])} heldout_keyframes={heldout_keyframes} "
        f"availability_pass={availability_pass}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
