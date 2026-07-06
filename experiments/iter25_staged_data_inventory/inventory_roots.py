#!/usr/bin/env python3
"""Inventory frozen local nuScenes roots for iter25.

This script is metadata/file-existence only. It inspects the pre-registered root list, applies the
known-data firewall, and writes token-free inventory artifacts. It does not import UniAD, start
Docker, call /infer, compute labels, fit probes, or read image bytes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT = "iter25_staged_data_inventory"
HYPOTHESIS = "experiments/iter25_staged_data_inventory/HYPOTHESIS.md"
MIN_ELIGIBLE_SCENES = 48
MIN_SCENE_KEYFRAMES = 24
MIN_TOTAL_KEYFRAMES = 1200
MIN_HELDOUT_KEYFRAMES = 300

FROZEN_ROOTS = (
    "/datasets/nuscenes",
    "/datasets/nuscenes-full",
    "/opt/sentinel-stack/data/nuscenes",
    "/opt/sentinel-stack/UniAD/data/nuscenes",
    "/data/nuscenes",
)

CAMS = (
    "CAM_FRONT",
    "CAM_FRONT_RIGHT",
    "CAM_FRONT_LEFT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
)

NEURO_NCAP_OFFICIAL_SCENE_IDS = (
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
)
NEURO_NCAP_OFFICIAL_SCENES = tuple(f"scene-{sid}" for sid in NEURO_NCAP_OFFICIAL_SCENE_IDS)
ITER12_EVALUATION_SCENES = ("scene-0103",)

KNOWN_DATA_MANIFESTS = (
    Path("experiments/iter22_causal_planner_interpretability/split_manifest.json"),
    Path("experiments/iter23_s0_hardened_causal_localization/availability_manifest.json"),
    Path("experiments/iter24_risk_support_atlas/availability_manifest.json"),
)
KNOWN_DATA_JSONL_GZ = (
    Path(
        "experiments/iter22_causal_planner_interpretability/"
        "proof-extract/sentinel_e22_stage1_gt.jsonl.gz"
    ),
    Path(
        "experiments/iter23_s0_hardened_causal_localization/"
        "proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz"
    ),
)
KNOWN_DATA_TEXTS = (
    Path("experiments/iter24_risk_support_atlas/availability_manifest.exclusions.txt"),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def write_json(path: Path, obj: Any) -> None:
    assert_no_nuscenes_identifier_fields(obj)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def scene_names_in_obj(obj: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(obj, dict):
        for key in ("name", "scene"):
            value = obj.get(key)
            if isinstance(value, str) and value.startswith("scene-"):
                names.add(value)
        for value in obj.values():
            names.update(scene_names_in_obj(value))
    elif isinstance(obj, list):
        for value in obj:
            names.update(scene_names_in_obj(value))
    return names


def scene_names_in_jsonl_gz(path: Path) -> set[str]:
    names: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            scene = row.get("scene")
            if isinstance(scene, str) and scene.startswith("scene-"):
                names.add(scene)
    return names


def scene_names_in_text(path: Path) -> set[str]:
    names: set[str] = set()
    for part in path.read_text().replace(",", " ").split():
        cleaned = part.strip()
        if cleaned.startswith("scene-") and len(cleaned) == len("scene-0000"):
            names.add(cleaned)
    return names


def collect_known_data_firewall() -> dict[str, Any]:
    sources: dict[str, list[str]] = {}
    all_names: set[str] = set()
    for path in KNOWN_DATA_MANIFESTS:
        if not path.exists():
            raise SystemExit(f"missing known-data manifest for firewall: {path}")
        names = scene_names_in_obj(read_json(path))
        sources[str(path)] = sorted(names)
        all_names.update(names)
    for path in KNOWN_DATA_JSONL_GZ:
        if not path.exists():
            raise SystemExit(f"missing known-data sidecar for firewall: {path}")
        names = scene_names_in_jsonl_gz(path)
        sources[str(path)] = sorted(names)
        all_names.update(names)
    for path in KNOWN_DATA_TEXTS:
        if not path.exists():
            raise SystemExit(f"missing known-data text artifact for firewall: {path}")
        names = scene_names_in_text(path)
        sources[str(path)] = sorted(names)
        all_names.update(names)
    return {"scene_names": sorted(all_names), "sources": sources}


def read_train_scenes(path: Path) -> list[str]:
    scenes = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(scenes) != 700:
        raise SystemExit(f"expected 700 official train scenes, found {len(scenes)} in {path}")
    if len(set(scenes)) != len(scenes):
        raise SystemExit(f"duplicate scene names in {path}")
    bad = [scene for scene in scenes if not scene.startswith("scene-")]
    if bad:
        raise SystemExit(f"non-scene entries in {path}: {bad[:5]}")
    return scenes


def table_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {row[key]: row for row in rows}


def keyframe_index(
    sample_data: list[dict[str, Any]],
    calibrated_sensor: list[dict[str, Any]],
    sensor: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    calib = table_by_key(calibrated_sensor, "token")
    sensor_channel = {row["token"]: row["channel"] for row in sensor}
    by_sample_channel = {}
    for row in sample_data:
        if not row.get("is_key_frame"):
            continue
        sensor_token = calib[row["calibrated_sensor_token"]]["sensor_token"]
        channel = sensor_channel[sensor_token]
        if channel in CAMS:
            by_sample_channel[(row["sample_token"], channel)] = row
    return by_sample_channel


def scene_chain(scene: dict[str, Any], samples: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    chain = []
    sample_key = scene["first_sample_token"]
    while sample_key:
        sample = samples[sample_key]
        chain.append(sample)
        sample_key = sample["next"]
    return chain


def split_hash(root_id: str, scene_name: str) -> str:
    return hashlib.sha256(f"iter25:{root_id}:{scene_name}".encode()).hexdigest()


def split_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    fit_n = (len(records) * 50) // 100
    calibration_n = (len(records) * 25) // 100
    return {
        "fit": records[:fit_n],
        "calibration": records[fit_n : fit_n + calibration_n],
        "heldout": records[fit_n + calibration_n :],
    }


def summarize_splits(splits: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    return {
        split: {
            "scene_count": len(records),
            "keyframe_count": sum(int(record["available_keyframes"]) for record in records),
        }
        for split, records in splits.items()
    }


def assert_no_nuscenes_identifier_fields(obj: Any) -> None:
    bad_keys: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_path = f"{path}.{key}" if path else key
                if key == "token" or key.endswith("_token"):
                    bad_keys.append(key_path)
                visit(child, key_path)
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                visit(child, f"{path}[{idx}]")

    visit(obj, "")
    if bad_keys:
        preview = ", ".join(bad_keys[:10])
        raise SystemExit(f"refusing to write nuScenes token fields: {preview}")


def camera_file_info(root: Path, relative_name: str) -> dict[str, Any] | None:
    path = root / relative_name
    if not path.is_file():
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size <= 0:
        return None
    return {"path": relative_name, "size_bytes": int(size)}


def availability_record(
    scene: dict[str, Any],
    samples: dict[str, dict[str, Any]],
    sample_channel: dict[tuple[str, str], dict[str, Any]],
    root: Path,
    root_id: str,
) -> tuple[dict[str, Any], dict[str, Any], Counter[str]]:
    frames = []
    reasons: Counter[str] = Counter()
    total_camera_bytes = 0
    for sample_index, sample in enumerate(scene_chain(scene, samples)):
        camera_files = {}
        missing = False
        for channel in CAMS:
            row = sample_channel.get((sample["token"], channel))
            if row is None:
                reasons[f"missing_metadata_{channel}"] += 1
                missing = True
                continue
            info = camera_file_info(root, row["filename"])
            if info is None:
                reasons[f"missing_file_{channel}"] += 1
                missing = True
                continue
            camera_files[channel] = info
            total_camera_bytes += int(info["size_bytes"])
        if not missing:
            frames.append(
                {
                    "camera_files": camera_files,
                    "sample_index": sample_index,
                    "timestamp_us": int(sample["timestamp"]),
                }
            )

    summary = {
        "available_keyframes": len(frames),
        "first_timestamp_us": frames[0]["timestamp_us"] if frames else None,
        "last_timestamp_us": frames[-1]["timestamp_us"] if frames else None,
        "name": scene["name"],
        "nbr_samples": int(scene["nbr_samples"]),
        "split_hash": split_hash(root_id, scene["name"]),
        "total_camera_bytes": int(total_camera_bytes),
    }
    manifest_record = {**summary, "frames": frames}
    return summary, manifest_record, reasons


def metadata_paths(root: Path) -> dict[str, Path]:
    meta = root / "v1.0-trainval"
    return {
        "calibrated_sensor": meta / "calibrated_sensor.json",
        "sample": meta / "sample.json",
        "sample_data": meta / "sample_data.json",
        "scene": meta / "scene.json",
        "sensor": meta / "sensor.json",
    }


def inspect_root(
    root_name: str,
    train_scenes: list[str],
    excluded_scene_names: set[str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    root = Path(root_name)
    root_id = root_name
    report: dict[str, Any] = {
        "availability_gate": {
            "min_eligible_scenes": MIN_ELIGIBLE_SCENES,
            "min_heldout_keyframes": MIN_HELDOUT_KEYFRAMES,
            "min_scene_keyframes": MIN_SCENE_KEYFRAMES,
            "min_total_keyframes": MIN_TOTAL_KEYFRAMES,
            "pass": False,
        },
        "counts": {
            "candidate_scene_count_after_exclusions": 0,
            "eligible_scene_count": 0,
            "heldout_keyframe_count": 0,
            "known_data_contamination_count": 0,
            "mixed_root_keyframe_count": 0,
            "metadata_identifier_field_count": 0,
            "total_keyframe_count": 0,
        },
        "root": root_name,
        "root_exists": root.exists(),
        "root_id": root_id,
        "status": "not_started",
    }
    if not root.exists():
        report["status"] = "missing_root"
        return report, None

    table_paths = metadata_paths(root)
    missing_tables = [name for name, path in table_paths.items() if not path.exists()]
    report["metadata_dir"] = str(root / "v1.0-trainval")
    report["missing_tables"] = missing_tables
    if missing_tables:
        report["status"] = "missing_metadata_tables"
        return report, None

    try:
        scene_rows = read_json(table_paths["scene"])
        sample_rows = read_json(table_paths["sample"])
        sample_data_rows = read_json(table_paths["sample_data"])
        calibrated_sensor_rows = read_json(table_paths["calibrated_sensor"])
        sensor_rows = read_json(table_paths["sensor"])
    except (json.JSONDecodeError, OSError) as exc:
        report["status"] = "metadata_read_error"
        report["error"] = str(exc)
        return report, None

    scenes_by_name = table_by_key(scene_rows, "name")
    samples = table_by_key(sample_rows, "token")
    sample_channel = keyframe_index(sample_data_rows, calibrated_sensor_rows, sensor_rows)
    table_sha = {name: sha256_file(path) for name, path in table_paths.items()}

    candidate_names = [name for name in train_scenes if name not in excluded_scene_names]
    missing_from_scene_json = sorted(set(candidate_names) - set(scenes_by_name))
    candidate_names = [name for name in candidate_names if name in scenes_by_name]

    eligible_summaries = []
    eligible_manifest_records = []
    ineligible_summaries = []
    reason_counts: Counter[str] = Counter()
    for name in candidate_names:
        summary, manifest_record, reasons = availability_record(
            scenes_by_name[name], samples, sample_channel, root, root_id
        )
        reason_counts.update(reasons)
        if int(summary["available_keyframes"]) >= MIN_SCENE_KEYFRAMES:
            eligible_summaries.append(summary)
            eligible_manifest_records.append(manifest_record)
        else:
            ineligible_summaries.append(
                {
                    "available_keyframes": summary["available_keyframes"],
                    "name": name,
                    "nbr_samples": summary["nbr_samples"],
                    "reason_counts": dict(sorted(reasons.items())),
                }
            )

    eligible_pairs = sorted(
        zip(eligible_summaries, eligible_manifest_records, strict=True),
        key=lambda pair: (pair[0]["split_hash"], pair[0]["name"]),
    )
    eligible_summaries = [pair[0] for pair in eligible_pairs]
    eligible_manifest_records = [pair[1] for pair in eligible_pairs]
    summary_splits = split_records(eligible_summaries)
    manifest_splits = split_records(eligible_manifest_records)
    total_keyframes = sum(int(record["available_keyframes"]) for record in eligible_summaries)
    heldout_keyframes = sum(
        int(record["available_keyframes"]) for record in summary_splits["heldout"]
    )
    contamination = len({record["name"] for record in eligible_summaries} & excluded_scene_names)
    availability_pass = (
        len(eligible_summaries) >= MIN_ELIGIBLE_SCENES
        and total_keyframes >= MIN_TOTAL_KEYFRAMES
        and heldout_keyframes >= MIN_HELDOUT_KEYFRAMES
        and contamination == 0
    )

    report.update(
        {
            "availability_reason_counts": dict(sorted(reason_counts.items())),
            "counts": {
                "candidate_scene_count_after_exclusions": len(candidate_names),
                "eligible_scene_count": len(eligible_summaries),
                "heldout_keyframe_count": heldout_keyframes,
                "ineligible_scene_count": len(ineligible_summaries)
                + len(missing_from_scene_json),
                "known_data_contamination_count": contamination,
                "missing_from_scene_json_count": len(missing_from_scene_json),
                "mixed_root_keyframe_count": 0,
                "metadata_identifier_field_count": 0,
                "scene_json_scene_count": len(scene_rows),
                "total_keyframe_count": total_keyframes,
            },
            "eligible_scene_names": [record["name"] for record in eligible_summaries],
            "ineligible_scene_sample": ineligible_summaries[:25],
            "missing_from_scene_json_sample": missing_from_scene_json[:25],
            "source": {
                "data_root": root_name,
                "metadata_dir": str(root / "v1.0-trainval"),
                "table_sha256": table_sha,
            },
            "split_summary": summarize_splits(summary_splits),
            "status": "pass" if availability_pass else "insufficient_availability",
        }
    )
    report["availability_gate"]["pass"] = availability_pass

    selected_manifest = None
    if availability_pass:
        selected_manifest = {
            "availability_gate": report["availability_gate"],
            "counts": report["counts"],
            "experiment": EXPERIMENT,
            "hypothesis": HYPOTHESIS,
            "join_key": ["scene", "sample_index", "timestamp_us"],
            "root": root_name,
            "root_id": root_id,
            "selection_rule": (
                "Exclude NeuroNCAP/iteration-12 and iter22/iter23/iter24 known-data scene names; "
                "require at least 24 six-camera keyframes under one root; sort eligible scenes by "
                "SHA256('iter25:<root_id>:<scene_name>'); assign first 50% fit, next 25% "
                "calibration, remainder heldout."
            ),
            "source": report["source"],
            "splits": manifest_splits,
            "stage": "selected_root_availability_manifest",
        }
    return report, selected_manifest


def exclusion_report_text(
    known_data_firewall: dict[str, Any],
    excluded_scene_names: set[str],
    excluded_train_scene_names: set[str],
) -> str:
    lines = [
        "iter25 staged-data inventory exclusion report",
        "neuro_ncap_official_scene_names: " + " ".join(NEURO_NCAP_OFFICIAL_SCENES),
        "iteration12_evaluation_scene_names: " + " ".join(ITER12_EVALUATION_SCENES),
        "known_data_scene_count: " + str(len(known_data_firewall["scene_names"])),
        "known_data_scene_names: " + " ".join(known_data_firewall["scene_names"]),
        "excluded_scene_count: " + str(len(excluded_scene_names)),
        "excluded_scene_names: " + " ".join(sorted(excluded_scene_names)),
        "excluded_train_scene_count: " + str(len(excluded_train_scene_names)),
        "excluded_train_scene_names: " + " ".join(sorted(excluded_train_scene_names)),
    ]
    for source, names in sorted(known_data_firewall["sources"].items()):
        lines.append(f"source {source}: {len(names)} scenes")
    return "\n".join(lines) + "\n"


def choose_selected_root(
    reports: list[dict[str, Any]],
    manifests: dict[str, dict[str, Any]],
) -> str | None:
    passing = [report for report in reports if report["availability_gate"]["pass"]]
    if not passing:
        return None
    passing.sort(
        key=lambda report: (
            -int(report["counts"]["total_keyframe_count"]),
            str(report["root"]),
        )
    )
    selected = str(passing[0]["root"])
    if selected not in manifests:
        raise SystemExit(f"internal error: selected passing root lacks manifest: {selected}")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train-scenes",
        default="experiments/iter22_causal_planner_interpretability/official_train_scenes.txt",
        help="official nuscenes.utils.splits.train scene-name list",
    )
    parser.add_argument(
        "--out-dir",
        default="experiments/iter25_staged_data_inventory",
        help="directory for root inventory artifacts",
    )
    args = parser.parse_args()

    train_scenes_path = Path(args.train_scenes)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_scenes = read_train_scenes(train_scenes_path)
    known_data_firewall = collect_known_data_firewall()
    excluded_scene_names = set(NEURO_NCAP_OFFICIAL_SCENES)
    excluded_scene_names.update(ITER12_EVALUATION_SCENES)
    excluded_scene_names.update(known_data_firewall["scene_names"])
    excluded_train_scene_names = set(train_scenes) & excluded_scene_names

    reports = []
    selected_manifests: dict[str, dict[str, Any]] = {}
    for root in FROZEN_ROOTS:
        report, selected_manifest = inspect_root(root, train_scenes, excluded_scene_names)
        reports.append(report)
        if selected_manifest is not None:
            selected_manifests[root] = selected_manifest

    selected_root = choose_selected_root(reports, selected_manifests)
    inventory = {
        "availability_bars": {
            "min_eligible_scenes": MIN_ELIGIBLE_SCENES,
            "min_heldout_keyframes": MIN_HELDOUT_KEYFRAMES,
            "min_scene_keyframes": MIN_SCENE_KEYFRAMES,
            "min_total_keyframes": MIN_TOTAL_KEYFRAMES,
        },
        "command": shlex.join([sys.executable, *sys.argv]),
        "experiment": EXPERIMENT,
        "frozen_roots": list(FROZEN_ROOTS),
        "hypothesis": HYPOTHESIS,
        "known_data_firewall": known_data_firewall,
        "official_train_scenes": {
            "count": len(train_scenes),
            "path": str(train_scenes_path),
            "sha256": sha256_file(train_scenes_path),
        },
        "overall_pass": selected_root is not None,
        "selected_root": selected_root,
        "selection_rule": (
            "Inspect only the frozen root list; choose the passing root with the most eligible "
            "post-firewall keyframes; break ties lexicographically by root path."
        ),
        "stage": "root_inventory",
        "root_reports": reports,
    }

    inventory_path = out_dir / "root_inventory.json"
    write_json(inventory_path, inventory)
    write_text(out_dir / "root_inventory.sha256", f"{sha256_file(inventory_path)}  root_inventory.json")
    write_text(out_dir / "root_inventory.command.txt", shlex.join([sys.executable, *sys.argv]))
    write_text(
        out_dir / "root_inventory.exclusions.txt",
        exclusion_report_text(
            known_data_firewall,
            excluded_scene_names,
            excluded_train_scene_names,
        ),
    )

    if selected_root is not None:
        manifest_path = out_dir / "selected_availability_manifest.json"
        write_json(manifest_path, selected_manifests[selected_root])
        write_text(
            out_dir / "selected_availability_manifest.sha256",
            f"{sha256_file(manifest_path)}  selected_availability_manifest.json",
        )

    print(
        "iter25 inventory "
        f"overall_pass={selected_root is not None} "
        f"selected_root={selected_root or 'NONE'} "
        f"inventory_sha256={sha256_file(inventory_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
