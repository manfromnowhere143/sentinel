#!/usr/bin/env python3
"""Build the iteration-32 prefix replay manifest from the iter31 canary targets."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER31 = ROOT / "experiments/iter31_full_trainval_bridge_intervention"
OUT = ROOT / "experiments/iter32_prefix_replay_baseline_recovery/proof-prefix"
JOIN_KEY = ("scene", "sample_index", "timestamp_us")


class ChainedBinaryReader(io.RawIOBase):
    def __init__(self, paths: Iterable[Path]) -> None:
        self.paths = iter(paths)
        self.current = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        view = memoryview(buffer)
        total = 0
        while total < len(view):
            if self.current is None:
                try:
                    self.current = next(self.paths).open("rb")
                except StopIteration:
                    break
            read = self.current.readinto(view[total:])
            if read:
                total += read
                break
            self.current.close()
            self.current = None
        return total

    def close(self) -> None:
        if self.current is not None:
            self.current.close()
            self.current = None
        super().close()


def open_text(path: Path):
    if ".gz" in path.suffixes:
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def is_gzip_part(path: Path) -> bool:
    return ".gz" in path.suffixes and any(suffix.startswith(".part-") for suffix in path.suffixes)


def iter_gzip_parts(paths: list[Path]):
    reader = ChainedBinaryReader(sorted(paths))
    with reader:
        with gzip.GzipFile(fileobj=io.BufferedReader(reader), mode="rb") as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)


def iter_jsonl(paths: Iterable[Path]):
    gzip_parts = []
    for path in paths:
        if is_gzip_part(path):
            gzip_parts.append(path)
            continue
        if gzip_parts:
            yield from iter_gzip_parts(gzip_parts)
            gzip_parts = []
        with open_text(path) as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    if gzip_parts:
        yield from iter_gzip_parts(gzip_parts)


def key_of(row: dict) -> tuple:
    return tuple(row[field] for field in JOIN_KEY)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_prefix_manifest(target_rows: list[dict]) -> list[dict]:
    grouped: OrderedDict[str, dict[int, dict]] = OrderedDict()
    for row in sorted(target_rows, key=lambda r: (r["scene"], int(r["sample_index"]), int(r["timestamp_us"]))):
        scene = row["scene"]
        sample_index = int(row["sample_index"])
        grouped.setdefault(scene, OrderedDict())
        if sample_index in grouped[scene]:
            raise ValueError(f"duplicate target sample {scene}[{sample_index}]")
        grouped[scene][sample_index] = row

    manifest = []
    for scene, targets in grouped.items():
        max_index = max(targets)
        for sample_index in range(max_index + 1):
            target = targets.get(sample_index)
            row = {
                "scene": scene,
                "sample_index": sample_index,
                "target_row": target is not None,
            }
            if target is not None:
                row.update(
                    {
                        "timestamp_us": int(target["timestamp_us"]),
                        "source_split": target["split"],
                        "source_label": int(target["label"]),
                        "source_label_name": target["label_name"],
                    }
                )
            manifest.append(row)
    return manifest


def reference_counts(paths: list[Path], keys: set[tuple]) -> Counter:
    counts: Counter = Counter()
    for row in iter_jsonl(paths):
        if row.get("reset"):
            continue
        key = key_of(row)
        if key in keys:
            counts[key] += 1
    return counts


def build_report(
    target_manifest: Path,
    prefix_manifest: list[dict],
    extract_parts: list[Path],
    gt_path: Path,
) -> dict:
    target_rows = [row for row in prefix_manifest if row["target_row"]]
    target_keys = {
        (row["scene"], int(row["sample_index"]), int(row["timestamp_us"])) for row in target_rows
    }
    extract_counts = reference_counts(extract_parts, target_keys)
    gt_counts = reference_counts([gt_path], target_keys)
    missing_extract = sorted(key for key in target_keys if extract_counts[key] != 1)
    missing_gt = sorted(key for key in target_keys if gt_counts[key] != 1)
    by_scene = OrderedDict()
    for row in prefix_manifest:
        scene = row["scene"]
        item = by_scene.setdefault(
            scene,
            {
                "prefix_replay_rows": 0,
                "target_rows": 0,
                "target_sample_indices": [],
            },
        )
        item["prefix_replay_rows"] += 1
        if row["target_row"]:
            item["target_rows"] += 1
            item["target_sample_indices"].append(int(row["sample_index"]))

    context_only_rows = sum(1 for row in prefix_manifest if not row["target_row"])
    failures = []
    if len(prefix_manifest) != 44:
        failures.append(f"prefix_replay_rows={len(prefix_manifest)} != 44")
    if len(target_rows) != 12:
        failures.append(f"target_rows={len(target_rows)} != 12")
    if context_only_rows != 32:
        failures.append(f"context_only_rows={context_only_rows} != 32")
    for key in missing_extract:
        failures.append(f"iter29_extract_count[{key}]={extract_counts[key]} != 1")
    for key in missing_gt:
        failures.append(f"iter29_gt_count[{key}]={gt_counts[key]} != 1")

    return {
        "schema_version": "sentinel.iter32.prefix_manifest_report.v1",
        "command_line": " ".join(sys.argv),
        "source_target_manifest": str(target_manifest.relative_to(ROOT)),
        "source_target_manifest_sha256": sha256_file(target_manifest),
        "target_rows": len(target_rows),
        "prefix_replay_rows": len(prefix_manifest),
        "context_only_rows": context_only_rows,
        "scenes": by_scene,
        "iter29_extract_reference_paths": [str(path.relative_to(ROOT)) for path in extract_parts],
        "iter29_gt_reference_path": str(gt_path.relative_to(ROOT)),
        "missing_or_duplicate_iter29_extract_target_keys": [list(key) for key in missing_extract],
        "missing_or_duplicate_iter29_gt_target_keys": [list(key) for key in missing_gt],
        "offline_manifest_pass": not failures,
        "failures": failures,
        "claim_boundary": (
            "This is an offline manifest/reference gate only. It authorizes no intervention, "
            "calibration, heldout, iteration-12, selector, closed-loop, or safety claim."
        ),
    }


def default_extract_parts() -> list[Path]:
    return sorted((ITER29 / "proof-full-extract").glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target-manifest",
        default=str(ITER31 / "proof-direction/replay_manifest_canary.json"),
    )
    parser.add_argument("--extract-part", action="append")
    parser.add_argument(
        "--gt",
        default=str(ITER29 / "proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"),
    )
    parser.add_argument("--out-dir", default=str(OUT))
    args = parser.parse_args()

    target_manifest = Path(args.target_manifest)
    target_rows = json.loads(target_manifest.read_text(encoding="utf-8"))
    prefix_manifest = make_prefix_manifest(target_rows)
    extract_parts = [Path(path) for path in args.extract_part] if args.extract_part else default_extract_parts()
    gt_path = Path(args.gt)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "prefix_manifest.json", prefix_manifest)
    report = build_report(target_manifest, prefix_manifest, extract_parts, gt_path)
    report["prefix_manifest_sha256"] = sha256_file(out_dir / "prefix_manifest.json")
    write_json(out_dir / "prefix_manifest_report.json", report)
    (out_dir / "build_prefix_manifest.command.txt").write_text(
        " ".join(sys.argv) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["offline_manifest_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
