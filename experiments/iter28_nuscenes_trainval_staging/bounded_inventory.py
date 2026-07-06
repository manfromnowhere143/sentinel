#!/usr/bin/env python3
"""Run the iter28 post-staging availability inventory for /datasets/nuscenes-full only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shlex
import sys
from pathlib import Path
from typing import Any


ITER25_SCRIPT = Path("experiments/iter25_staged_data_inventory/inventory_roots.py")
DEST_ROOT = "/datasets/nuscenes-full"
OUT_DIR = Path("experiments/iter28_nuscenes_trainval_staging/proof-inventory")


def load_iter25_module() -> Any:
    spec = importlib.util.spec_from_file_location("iter25_inventory_roots", ITER25_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ITER25_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEST_ROOT)
    parser.add_argument(
        "--train-scenes",
        default="experiments/iter22_causal_planner_interpretability/official_train_scenes.txt",
    )
    parser.add_argument("--out-dir", default=str(OUT_DIR), type=Path)
    args = parser.parse_args()

    if args.root != DEST_ROOT:
        raise SystemExit(f"iter28 may inspect only {DEST_ROOT}, got {args.root}")

    inv = load_iter25_module()
    inv.EXPERIMENT = "iter28_nuscenes_trainval_staging"
    inv.HYPOTHESIS = "experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md"
    inv.split_hash = lambda root_id, scene_name: hashlib.sha256(
        f"iter28:{root_id}:{scene_name}".encode()
    ).hexdigest()

    train_scenes_path = Path(args.train_scenes)
    train_scenes = inv.read_train_scenes(train_scenes_path)
    known_data_firewall = inv.collect_known_data_firewall()
    excluded_scene_names = set(inv.NEURO_NCAP_OFFICIAL_SCENES)
    excluded_scene_names.update(inv.ITER12_EVALUATION_SCENES)
    excluded_scene_names.update(known_data_firewall["scene_names"])
    excluded_train_scene_names = set(train_scenes) & excluded_scene_names

    report, selected_manifest = inv.inspect_root(args.root, train_scenes, excluded_scene_names)
    inventory = {
        "availability_bars": {
            "min_eligible_scenes": inv.MIN_ELIGIBLE_SCENES,
            "min_heldout_keyframes": inv.MIN_HELDOUT_KEYFRAMES,
            "min_scene_keyframes": inv.MIN_SCENE_KEYFRAMES,
            "min_total_keyframes": inv.MIN_TOTAL_KEYFRAMES,
        },
        "command": shlex.join([sys.executable, *sys.argv]),
        "experiment": "iter28_nuscenes_trainval_staging",
        "frozen_root": DEST_ROOT,
        "hypothesis": "experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md",
        "known_data_firewall": known_data_firewall,
        "official_train_scenes": {
            "count": len(train_scenes),
            "path": str(train_scenes_path),
            "sha256": sha256_file(train_scenes_path),
        },
        "overall_pass": bool(report["availability_gate"]["pass"]),
        "root_report": report,
        "selection_rule": (
            "Inspect only /datasets/nuscenes-full; sort eligible scenes by "
            "SHA256('iter28:/datasets/nuscenes-full:<scene_name>'); assign first 50% fit, "
            "next 25% calibration, remainder heldout."
        ),
        "stage": "iter28_bounded_post_staging_inventory",
    }
    inv.assert_no_nuscenes_identifier_fields(inventory)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = args.out_dir / "availability_inventory.json"
    write_json(inventory_path, inventory)
    write_text(
        args.out_dir / "availability_inventory.sha256",
        f"{sha256_file(inventory_path)}  availability_inventory.json",
    )
    write_text(args.out_dir / "availability_inventory.command.txt", shlex.join([sys.executable, *sys.argv]))
    write_text(
        args.out_dir / "availability_inventory.exclusions.txt",
        inv.exclusion_report_text(
            known_data_firewall,
            excluded_scene_names,
            excluded_train_scene_names,
        ),
    )
    if selected_manifest is not None:
        inv.assert_no_nuscenes_identifier_fields(selected_manifest)
        manifest_path = args.out_dir / "selected_availability_manifest.json"
        write_json(manifest_path, selected_manifest)
        write_text(
            args.out_dir / "selected_availability_manifest.sha256",
            f"{sha256_file(manifest_path)}  selected_availability_manifest.json",
        )
    print(
        "iter28 inventory "
        f"overall_pass={report['availability_gate']['pass']} "
        f"eligible_scenes={report['counts']['eligible_scene_count']} "
        f"heldout_keyframes={report['counts']['heldout_keyframe_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
