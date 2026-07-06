#!/usr/bin/env python3
"""Build the iter22 Stage 1 split manifest.

This script is metadata-only. It reads the official nuScenes train split scene names and the
nuScenes scene table, excludes every NeuroNCAP/iteration-12 evaluation scene, then applies the
pre-registered lexicographic 60/15/15 split rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path


EXPERIMENT = "iter22_causal_planner_interpretability"

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


def read_scene_table(path: Path) -> dict[str, dict[str, object]]:
    rows = json.loads(path.read_text())
    by_name = {}
    for row in rows:
        name = row["name"]
        by_name[name] = {
            "name": name,
            "token": row["token"],
            "nbr_samples": row["nbr_samples"],
            "description": row.get("description", ""),
        }
    return by_name


def split_records(records: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    return {
        "fit": records[:60],
        "calibration": records[60:75],
        "heldout": records[75:90],
    }


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scene-json",
        default=".evidence-staging/nuscenes-mine/v1.0-trainval/scene.json",
        help="nuScenes v1.0-trainval scene.json path",
    )
    parser.add_argument(
        "--train-scenes",
        default="experiments/iter22_causal_planner_interpretability/official_train_scenes.txt",
        help="official nuscenes.utils.splits.train scene-name list",
    )
    parser.add_argument(
        "--out-dir",
        default="experiments/iter22_causal_planner_interpretability",
        help="directory for split_manifest.json and audit sidecars",
    )
    args = parser.parse_args()

    scene_json = Path(args.scene_json)
    train_scenes_path = Path(args.train_scenes)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_scenes = read_train_scenes(train_scenes_path)
    scene_table = read_scene_table(scene_json)

    missing_from_scene_json = sorted(set(train_scenes) - set(scene_table))
    if missing_from_scene_json:
        raise SystemExit(
            "train scenes missing from scene.json: " + ", ".join(missing_from_scene_json[:10])
        )

    excluded = sorted(set(NEURO_NCAP_OFFICIAL_SCENES) | set(ITER12_EVALUATION_SCENES))
    excluded_train = sorted(set(train_scenes) & set(excluded))
    eligible = sorted(s for s in train_scenes if s not in set(excluded))
    if len(eligible) < 90:
        raise SystemExit(f"only {len(eligible)} eligible scenes remain; pre-registration needs 90")

    selected_names = eligible[:90]
    selected_records = [scene_table[name] for name in selected_names]
    splits = split_records(selected_records)

    manifest = {
        "experiment": EXPERIMENT,
        "hypothesis": "experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md",
        "stage": "stage1_non_evaluation_manifest",
        "source": {
            "scene_json": str(scene_json),
            "scene_json_sha256": sha256_file(scene_json),
            "official_train_scenes": str(train_scenes_path),
            "official_train_scenes_sha256": sha256_file(train_scenes_path),
            "official_train_scenes_source": (
                "Extracted on sentinel-gpu from UniAD runtime with "
                "`from nuscenes.utils import splits; splits.train`; 700 lines."
            ),
        },
        "exclusions": {
            "neuro_ncap_official_scene_ids": NEURO_NCAP_OFFICIAL_SCENE_IDS,
            "neuro_ncap_official_scene_names": NEURO_NCAP_OFFICIAL_SCENES,
            "iteration12_evaluation_scene_names": ITER12_EVALUATION_SCENES,
            "excluded_train_scene_names": excluded_train,
        },
        "selection_rule": (
            "Sort official train scene names lexicographically after exclusions; take the first "
            "90 eligible scenes; assign 1-60 fit, 61-75 calibration, 76-90 heldout."
        ),
        "counts": {
            "official_train_scene_count": len(train_scenes),
            "scene_json_scene_count": len(scene_table),
            "excluded_scene_count": len(excluded),
            "excluded_train_scene_count": len(excluded_train),
            "eligible_scene_count": len(eligible),
            "selected_scene_count": len(selected_names),
            "fit_scene_count": len(splits["fit"]),
            "calibration_scene_count": len(splits["calibration"]),
            "heldout_scene_count": len(splits["heldout"]),
        },
        "splits": splits,
    }

    manifest_path = out_dir / "split_manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(manifest_text)
    manifest_sha = hashlib.sha256(manifest_text.encode()).hexdigest()

    write_text(out_dir / "split_manifest.sha256", f"{manifest_sha}  split_manifest.json")
    command = "python3 " + shlex.join([sys.argv[0], *sys.argv[1:]])
    write_text(out_dir / "split_manifest.command.txt", command)
    report = [
        "iter22 Stage 1 split manifest exclusion report",
        f"official_train_scene_count: {len(train_scenes)}",
        f"scene_json_scene_count: {len(scene_table)}",
        f"excluded_scene_names: {' '.join(excluded)}",
        f"excluded_train_scene_names: {' '.join(excluded_train) if excluded_train else '(none)'}",
        f"eligible_scene_count: {len(eligible)}",
        "fit: " + " ".join(r["name"] for r in splits["fit"]),
        "calibration: " + " ".join(r["name"] for r in splits["calibration"]),
        "heldout: " + " ".join(r["name"] for r in splits["heldout"]),
    ]
    write_text(out_dir / "split_manifest.exclusions.txt", "\n".join(report))

    print(f"wrote {manifest_path}")
    print(f"sha256 {manifest_sha}")
    print(
        "counts "
        f"train={len(train_scenes)} eligible={len(eligible)} selected={len(selected_names)} "
        f"fit={len(splits['fit'])} calibration={len(splits['calibration'])} "
        f"heldout={len(splits['heldout'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
