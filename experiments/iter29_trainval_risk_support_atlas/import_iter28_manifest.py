#!/usr/bin/env python3
"""Import and validate the iter28 availability manifest for iter29.

This is the S0a gate. It does not inspect model outputs, fit probes, touch
iteration-12 evidence, or run GPU work. It copies only the committed token-free
iter28 manifest into the iter29 experiment after validating the frozen counts
and digest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any


ITER28_MANIFEST = Path(
    "experiments/iter28_nuscenes_trainval_staging/proof-inventory/"
    "selected_availability_manifest.json"
)
ITER28_SHA = Path(
    "experiments/iter28_nuscenes_trainval_staging/proof-inventory/"
    "selected_availability_manifest.sha256"
)
OUT_DIR = Path("experiments/iter29_trainval_risk_support_atlas")
OUT_MANIFEST = "availability_manifest.json"
OUT_REPORT = "manifest_import_report.json"

EXPECTED_ROOT = "/datasets/nuscenes-full"
EXPECTED_SPLIT_SCENES = {"fit": 266, "calibration": 133, "heldout": 133}
EXPECTED_SPLIT_KEYFRAMES = {"fit": 10726, "calibration": 5375, "heldout": 5360}
EXPECTED_TOTAL_KEYFRAMES = 21461
SPLITS = ("fit", "calibration", "heldout")
FORBIDDEN_KEY_PARTS = ("token",)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_expected_sha(path: Path) -> str:
    text = path.read_text().strip()
    if not text:
        raise SystemExit(f"empty SHA sidecar: {path}")
    return text.split()[0]


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def count_identifier_fields(obj: Any) -> int:
    if isinstance(obj, dict):
        total = 0
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                total += 1
            total += count_identifier_fields(value)
        return total
    if isinstance(obj, list):
        return sum(count_identifier_fields(value) for value in obj)
    return 0


def split_counts(manifest: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]]:
    scene_counts: dict[str, int] = {}
    keyframe_counts: dict[str, int] = {}
    splits = manifest.get("splits", {})
    for split in SPLITS:
        records = splits.get(split)
        if not isinstance(records, list):
            raise SystemExit(f"missing split list: {split}")
        scene_counts[split] = len(records)
        keyframe_counts[split] = sum(len(record.get("frames", [])) for record in records)
    return scene_counts, keyframe_counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, default=ITER28_MANIFEST)
    parser.add_argument("--source-sha", type=Path, default=ITER28_SHA)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    actual_sha = sha256_file(args.source_manifest)
    expected_sha = read_expected_sha(args.source_sha)
    if actual_sha != expected_sha:
        raise SystemExit(
            f"source manifest SHA mismatch: actual={actual_sha} expected={expected_sha}"
        )

    manifest = json.loads(args.source_manifest.read_text())
    scene_counts, keyframe_counts = split_counts(manifest)
    total_keyframes = sum(keyframe_counts.values())
    identifier_field_count = count_identifier_fields(manifest)
    counts = manifest.get("counts", {})

    report = {
        "command": shlex.join([sys.executable, *sys.argv]),
        "experiment": "iter29_trainval_risk_support_atlas",
        "source_manifest": str(args.source_manifest),
        "source_sha_sidecar": str(args.source_sha),
        "source_sha256": actual_sha,
        "expected_source_sha256": expected_sha,
        "root": manifest.get("root"),
        "root_id": manifest.get("root_id"),
        "split_scene_counts": scene_counts,
        "split_keyframe_counts": keyframe_counts,
        "total_keyframes": total_keyframes,
        "expected_split_scene_counts": EXPECTED_SPLIT_SCENES,
        "expected_split_keyframe_counts": EXPECTED_SPLIT_KEYFRAMES,
        "expected_total_keyframes": EXPECTED_TOTAL_KEYFRAMES,
        "known_data_contamination_count": counts.get("known_data_contamination_count"),
        "mixed_root_keyframe_count": counts.get("mixed_root_keyframe_count"),
        "metadata_identifier_field_count": identifier_field_count,
    }
    pass_s0a = (
        report["root"] == EXPECTED_ROOT
        and report["root_id"] == EXPECTED_ROOT
        and scene_counts == EXPECTED_SPLIT_SCENES
        and keyframe_counts == EXPECTED_SPLIT_KEYFRAMES
        and total_keyframes == EXPECTED_TOTAL_KEYFRAMES
        and report["known_data_contamination_count"] == 0
        and report["mixed_root_keyframe_count"] == 0
        and identifier_field_count == 0
    )
    report["s0a_manifest_import_pass"] = pass_s0a
    report["verdict"] = (
        "S0A_PASS_CANARY_AUTHORIZED"
        if pass_s0a
        else "INFRASTRUCTURE_NULL_STOP_BEFORE_EXTRACTION"
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / OUT_MANIFEST
    report_path = args.out_dir / OUT_REPORT
    write_json(manifest_path, manifest)
    write_json(report_path, report)
    write_text(
        args.out_dir / f"{OUT_MANIFEST}.sha256",
        f"{sha256_file(manifest_path)}  {OUT_MANIFEST}",
    )
    write_text(
        args.out_dir / f"{OUT_REPORT}.sha256",
        f"{sha256_file(report_path)}  {OUT_REPORT}",
    )
    write_text(args.out_dir / "manifest_import.command.txt", report["command"])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if pass_s0a else 2


if __name__ == "__main__":
    raise SystemExit(main())
