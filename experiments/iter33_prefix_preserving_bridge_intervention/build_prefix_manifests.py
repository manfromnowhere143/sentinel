#!/usr/bin/env python3
"""Build iteration-33 prefix manifests and offline S0 receipts.

This script is offline-only. It combines the frozen iteration-31 target-row
manifests with the iteration-32 prefix-replay lesson, then verifies the
registered direction and prerequisite result statuses before any GPU replay is
eligible.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER30 = ROOT / "experiments/iter30_full_trainval_lowdiv_localization"
ITER31 = ROOT / "experiments/iter31_full_trainval_bridge_intervention"
ITER32 = ROOT / "experiments/iter32_prefix_replay_baseline_recovery"
ITER33 = ROOT / "experiments/iter33_prefix_preserving_bridge_intervention"
OUT = ITER33 / "proof-prefix"
JOIN_KEY = ("scene", "sample_index", "timestamp_us")

EXPECTED_ITER30_STATUS = "LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED"
EXPECTED_ITER31_STATUS = "INFRASTRUCTURE_NULL_S0_CANARY_ALPHA_ZERO_REPRODUCTION_FAIL"
EXPECTED_ITER32_STATUS = "BASELINE_RECOVERY_PASS_S1_PREFIX_REPLAY"
EXPECTED_DIRECTION_SHA = "3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794"
EXPECTED_ITER32_MODEL_TARGET_SHA = "2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e"
EXPECTED_ITER32_GT_TARGET_SHA = "5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7"

EXPECTED_SPLITS = {
    "canary": {
        "source_manifest": ITER31 / "proof-direction/replay_manifest_canary.json",
        "scenes": 3,
        "prefix_replay_rows": 44,
        "target_rows": 12,
        "context_only_rows": 32,
        "eligible_lowdiv": 6,
        "benign_control": 6,
    },
    "calibration": {
        "source_manifest": ITER31 / "proof-direction/replay_manifest_calibration.json",
        "scenes": 121,
        "prefix_replay_rows": 4293,
        "target_rows": 2452,
        "context_only_rows": 1841,
        "eligible_lowdiv": 108,
        "benign_control": 2344,
    },
    "heldout": {
        "source_manifest": ITER31 / "proof-direction/replay_manifest_heldout.json",
        "scenes": 122,
        "prefix_replay_rows": 4283,
        "target_rows": 2403,
        "context_only_rows": 1880,
        "eligible_lowdiv": 158,
        "benign_control": 2245,
    },
}


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


def key_label(key: tuple) -> str:
    return f"{key[0]}:{int(key[1])}:{int(key[2])}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_extract_parts() -> list[Path]:
    return sorted((ITER29 / "proof-full-extract").glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def load_status(result_path: Path) -> str | None:
    text = result_path.read_text(encoding="utf-8")
    match = re.search(r"^Status:\s*`([^`]+)`", text, flags=re.MULTILINE)
    return match.group(1) if match else None


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


def prefix_stats(prefix_manifest: list[dict]) -> dict:
    by_scene: OrderedDict[str, dict] = OrderedDict()
    labels: Counter = Counter()
    target_keys = []
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
            labels[row["source_label_name"]] += 1
            target_keys.append((row["scene"], int(row["sample_index"]), int(row["timestamp_us"])))
    target_rows = sum(1 for row in prefix_manifest if row["target_row"])
    return {
        "scenes": len(by_scene),
        "prefix_replay_rows": len(prefix_manifest),
        "target_rows": target_rows,
        "context_only_rows": len(prefix_manifest) - target_rows,
        "target_label_counts": dict(sorted(labels.items())),
        "target_keys": target_keys,
        "by_scene": by_scene,
    }


def reference_counts(paths: list[Path], keys: set[tuple]) -> Counter:
    counts: Counter = Counter()
    for row in iter_jsonl(paths):
        if row.get("reset"):
            continue
        key = key_of(row)
        if key in keys:
            counts[key] += 1
    return counts


def direction_receipt(direction_path: Path) -> tuple[dict, list[str]]:
    payload = json.loads(direction_path.read_text(encoding="utf-8"))
    failures = []
    if payload.get("feature_count") != 1792:
        failures.append(f"direction_feature_count={payload.get('feature_count')} != 1792")
    if payload.get("fit_rows") != 5211:
        failures.append(f"direction_fit_rows={payload.get('fit_rows')} != 5211")
    if payload.get("dropped_dimension_count") != 0:
        failures.append(f"direction_dropped_dimensions={payload.get('dropped_dimension_count')} != 0")
    if payload.get("direction_and_fit_stats_sha256") != EXPECTED_DIRECTION_SHA:
        failures.append(
            "direction_and_fit_stats_sha256="
            f"{payload.get('direction_and_fit_stats_sha256')} != {EXPECTED_DIRECTION_SHA}"
        )
    if len(payload.get("direction_raw", [])) != 1792:
        failures.append(f"direction_raw_len={len(payload.get('direction_raw', []))} != 1792")
    receipt = {
        "path": str(direction_path.relative_to(ROOT)),
        "file_sha256": sha256_file(direction_path),
        "direction_and_fit_stats_sha256": payload.get("direction_and_fit_stats_sha256"),
        "feature_order": payload.get("feature_order"),
        "feature_count": payload.get("feature_count"),
        "fit_rows": payload.get("fit_rows"),
        "dropped_dimension_count": payload.get("dropped_dimension_count"),
        "direction_raw_len": len(payload.get("direction_raw", [])),
    }
    return receipt, failures


def prerequisite_report(direction_path: Path, iter32_report_path: Path) -> tuple[dict, list[str]]:
    failures = []
    statuses = {
        "iter30_result_status": load_status(ITER30 / "RESULT.md"),
        "iter31_result_status": load_status(ITER31 / "RESULT.md"),
        "iter32_result_status": load_status(ITER32 / "RESULT.md"),
    }
    expected = {
        "iter30_result_status": EXPECTED_ITER30_STATUS,
        "iter31_result_status": EXPECTED_ITER31_STATUS,
        "iter32_result_status": EXPECTED_ITER32_STATUS,
    }
    for key, value in statuses.items():
        if value != expected[key]:
            failures.append(f"{key}={value} != {expected[key]}")

    direction, direction_failures = direction_receipt(direction_path)
    failures.extend(direction_failures)

    iter32_report = json.loads(iter32_report_path.read_text(encoding="utf-8"))
    model_hashes = iter32_report.get("model_target_repeat_hashes", [])
    gt_hashes = iter32_report.get("gt_target_repeat_hashes", [])
    if iter32_report.get("s1_prefix_replay_pass") is not True:
        failures.append("iter32_s1_prefix_replay_pass_not_true")
    if model_hashes != [EXPECTED_ITER32_MODEL_TARGET_SHA, EXPECTED_ITER32_MODEL_TARGET_SHA]:
        failures.append(f"iter32_model_target_repeat_hashes={model_hashes}")
    if gt_hashes != [EXPECTED_ITER32_GT_TARGET_SHA, EXPECTED_ITER32_GT_TARGET_SHA]:
        failures.append(f"iter32_gt_target_repeat_hashes={gt_hashes}")

    return {
        **statuses,
        "direction": direction,
        "iter32_baseline_recovery": {
            "path": str(iter32_report_path.relative_to(ROOT)),
            "s1_prefix_replay_pass": iter32_report.get("s1_prefix_replay_pass"),
            "model_target_repeat_hashes": model_hashes,
            "gt_target_repeat_hashes": gt_hashes,
            "max_model_abs_delta_vs_iter29": iter32_report.get("max_model_abs_delta_vs_iter29"),
            "max_gt_abs_delta_vs_iter29": iter32_report.get("max_gt_abs_delta_vs_iter29"),
        },
    }, failures


def split_manifest_report(
    split: str,
    source_manifest: Path,
    prefix_manifest: list[dict],
    extract_parts: list[Path],
    gt_path: Path,
) -> tuple[dict, list[str]]:
    expected = EXPECTED_SPLITS[split]
    stats = prefix_stats(prefix_manifest)
    failures = []
    for key in ("scenes", "prefix_replay_rows", "target_rows", "context_only_rows"):
        if stats[key] != expected[key]:
            failures.append(f"{split}:{key}={stats[key]} != {expected[key]}")
    for label in ("eligible_lowdiv", "benign_control"):
        if stats["target_label_counts"].get(label, 0) != expected[label]:
            failures.append(
                f"{split}:{label}_targets={stats['target_label_counts'].get(label, 0)} != {expected[label]}"
            )

    target_keys = set(stats["target_keys"])
    extract_counts = reference_counts(extract_parts, target_keys)
    gt_counts = reference_counts([gt_path], target_keys)
    missing_extract = sorted(key for key in target_keys if extract_counts[key] != 1)
    missing_gt = sorted(key for key in target_keys if gt_counts[key] != 1)
    for key in missing_extract[:20]:
        failures.append(f"{split}:iter29_extract_count[{key_label(key)}]={extract_counts[key]} != 1")
    for key in missing_gt[:20]:
        failures.append(f"{split}:iter29_gt_count[{key_label(key)}]={gt_counts[key]} != 1")
    if len(missing_extract) > 20:
        failures.append(f"{split}:additional_iter29_extract_count_failures={len(missing_extract) - 20}")
    if len(missing_gt) > 20:
        failures.append(f"{split}:additional_iter29_gt_count_failures={len(missing_gt) - 20}")

    return {
        "source_target_manifest": str(source_manifest.relative_to(ROOT)),
        "source_target_manifest_sha256": sha256_file(source_manifest),
        "scenes": stats["scenes"],
        "prefix_replay_rows": stats["prefix_replay_rows"],
        "target_rows": stats["target_rows"],
        "context_only_rows": stats["context_only_rows"],
        "target_label_counts": stats["target_label_counts"],
        "missing_or_duplicate_iter29_extract_target_keys": [list(key) for key in missing_extract],
        "missing_or_duplicate_iter29_gt_target_keys": [list(key) for key in missing_gt],
        "by_scene": stats["by_scene"],
    }, failures


def stdout_summary(report: dict) -> dict:
    return {
        "schema_version": report["schema_version"],
        "offline_manifest_pass": report["offline_manifest_pass"],
        "failure_count": report["failure_count"],
        "failures": report["failures"][:20],
        "direction_and_fit_stats_sha256": report["prerequisites"]["direction"][
            "direction_and_fit_stats_sha256"
        ],
        "iter32_s1_prefix_replay_pass": report["prerequisites"]["iter32_baseline_recovery"][
            "s1_prefix_replay_pass"
        ],
        "splits": {
            split: {
                "scenes": payload["scenes"],
                "prefix_replay_rows": payload["prefix_replay_rows"],
                "target_rows": payload["target_rows"],
                "context_only_rows": payload["context_only_rows"],
                "target_label_counts": payload["target_label_counts"],
                "prefix_manifest_sha256": payload["prefix_manifest_sha256"],
            }
            for split, payload in report["splits"].items()
        },
        "claim_boundary": report["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-part", action="append")
    parser.add_argument(
        "--gt",
        default=str(ITER29 / "proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"),
    )
    parser.add_argument(
        "--direction",
        default=str(ITER31 / "proof-direction/direction.json"),
    )
    parser.add_argument(
        "--iter32-report",
        default=str(ITER32 / "proof-prefix/baseline_recovery_report.json"),
    )
    parser.add_argument("--out-dir", default=str(OUT))
    args = parser.parse_args()

    extract_parts = [Path(path) for path in args.extract_part] if args.extract_part else default_extract_parts()
    gt_path = Path(args.gt)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prerequisites, failures = prerequisite_report(Path(args.direction), Path(args.iter32_report))
    split_reports = {}
    for split, expected in EXPECTED_SPLITS.items():
        source_manifest = expected["source_manifest"]
        target_rows = json.loads(source_manifest.read_text(encoding="utf-8"))
        prefix_manifest = make_prefix_manifest(target_rows)
        manifest_path = out_dir / f"prefix_manifest_{split}.json"
        write_json(manifest_path, prefix_manifest)
        split_report, split_failures = split_manifest_report(
            split, source_manifest, prefix_manifest, extract_parts, gt_path
        )
        split_report["prefix_manifest_path"] = path_label(manifest_path)
        split_report["prefix_manifest_sha256"] = sha256_file(manifest_path)
        split_reports[split] = split_report
        failures.extend(split_failures)

    write_json(out_dir / "direction_receipt.json", prerequisites["direction"])
    report = {
        "schema_version": "sentinel.iter33.prefix_manifest_report.v1",
        "command_line": " ".join(sys.argv),
        "prerequisites": prerequisites,
        "iter29_extract_reference_paths": [str(path.relative_to(ROOT)) for path in extract_parts],
        "iter29_gt_reference_path": str(gt_path.relative_to(ROOT)),
        "splits": split_reports,
        "offline_manifest_pass": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "claim_boundary": (
            "This is an offline manifest, prerequisite, and direction-receipt gate only. It "
            "authorizes no GPU replay, calibration, heldout, iteration-12, selector, closed-loop, "
            "deployment, or safety claim."
        ),
    }
    write_json(out_dir / "prefix_manifest_report.json", report)
    (out_dir / "build_prefix_manifests.command.txt").write_text(
        " ".join(sys.argv) + "\n", encoding="utf-8"
    )
    print(json.dumps(stdout_summary(report), indent=2, sort_keys=True))
    return 0 if report["offline_manifest_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
