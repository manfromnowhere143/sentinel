#!/usr/bin/env python3
"""Analyze iteration-32 prefix replay logs against committed iter29 baselines."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER31 = ROOT / "experiments/iter31_full_trainval_bridge_intervention"
JOIN_KEY = ("scene", "sample_index", "timestamp_us")
TARGET_ROWS = 12
PREFIX_ROWS = 44
GT_TOLERANCE = 1e-9
MODEL_TOLERANCE = 1e-5


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
    return (row.get("scene"), int(row.get("sample_index")), int(row.get("timestamp_us")))


def key_label(key: tuple) -> str:
    return f"{key[0]}:{key[1]}:{key[2]}"


def default_extract_parts() -> list[Path]:
    return sorted((ITER29 / "proof-full-extract").glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def max_abs_nested_delta(a, b) -> float:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isfinite(float(a)) or not math.isfinite(float(b)):
            return float("inf")
        return abs(float(a) - float(b))
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        if not a:
            return 0.0
        return max(max_abs_nested_delta(x, y) for x, y in zip(a, b))
    return float("inf")


def canonical_target_sha256(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for row in rows:
        encoded = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        h.update(encoded)
        h.update(b"\n")
    return h.hexdigest()


def target_keys_from_manifest(path: Path) -> set[tuple]:
    keys = set()
    for row in json.loads(path.read_text(encoding="utf-8")):
        keys.add((row["scene"], int(row["sample_index"]), int(row["timestamp_us"])))
    return keys


def load_reference(paths: list[Path], keys: set[tuple]) -> tuple[dict[tuple, dict], Counter]:
    rows = {}
    counts: Counter = Counter()
    for row in iter_jsonl(paths):
        if row.get("reset"):
            continue
        key = key_of(row)
        if key not in keys:
            continue
        counts[key] += 1
        rows.setdefault(key, row)
    return rows, counts


def row_error(row: dict) -> bool:
    return bool(row.get("error") or row.get("context_error") or row.get("intervention_error"))


def compare_exact(row: dict, reference: dict, fields: list[str], failures: list[str], prefix: str) -> None:
    key = key_label(key_of(row))
    for field in fields:
        if row.get(field) != reference.get(field):
            failures.append(f"{prefix}:{key}:{field}={row.get(field)} != {reference.get(field)}")


def compare_numeric(
    row: dict,
    reference: dict,
    fields: list[str],
    tolerance: float,
    failures: list[str],
    prefix: str,
) -> float:
    key = key_label(key_of(row))
    max_delta = 0.0
    for field in fields:
        if field not in row:
            failures.append(f"{prefix}:{key}:missing_{field}")
            continue
        if field not in reference:
            failures.append(f"{prefix}:{key}:missing_reference_{field}")
            continue
        delta = max_abs_nested_delta(row[field], reference[field])
        max_delta = max(max_delta, delta)
        if delta > tolerance:
            failures.append(f"{prefix}:{key}:{field}_max_abs={delta:.9g} > {tolerance:.9g}")
    return max_delta


def summarize_model_run(path: Path, target_keys: set[tuple]) -> dict:
    rows = [row for row in iter_jsonl([path]) if not row.get("reset")]
    target_rows = [row for row in rows if row.get("target_row")]
    keys = [key_of(row) for row in target_rows]
    unexpected = sorted(key for key in keys if key not in target_keys)
    missing = sorted(target_keys - set(keys))
    duplicates = sorted(key for key, count in Counter(keys).items() if count != 1)
    return {
        "path": str(path),
        "rows": rows,
        "target_rows_data": target_rows,
        "non_reset_rows": len(rows),
        "target_rows": len(target_rows),
        "context_only_rows": len(rows) - len(target_rows),
        "error_rows": sum(1 for row in rows if row_error(row)),
        "target_canonical_sha256": canonical_target_sha256(target_rows),
        "unexpected_target_keys": unexpected,
        "missing_target_keys": missing,
        "duplicate_target_keys": duplicates,
    }


def summarize_gt_run(path: Path, target_keys: set[tuple]) -> dict:
    rows = [row for row in iter_jsonl([path]) if not row.get("reset")]
    target_rows = [row for row in rows if row.get("target_row")]
    keys = [key_of(row) for row in target_rows]
    return {
        "path": str(path),
        "rows": rows,
        "target_rows_data": target_rows,
        "non_reset_rows": len(rows),
        "target_rows": len(target_rows),
        "context_only_rows": len(rows) - len(target_rows),
        "target_canonical_sha256": canonical_target_sha256(target_rows),
        "unexpected_target_keys": sorted(key for key in keys if key not in target_keys),
        "missing_target_keys": sorted(target_keys - set(keys)),
        "duplicate_target_keys": sorted(key for key, count in Counter(keys).items() if count != 1),
    }


def public_run_summary(summary: dict) -> dict:
    return {
        key: value
        for key, value in summary.items()
        if key not in {"rows", "target_rows_data"}
    }


def analyze(
    log_paths: list[Path],
    gt_paths: list[Path],
    target_manifest: Path,
    extract_parts: list[Path],
    iter29_gt: Path,
) -> dict:
    target_keys = target_keys_from_manifest(target_manifest)
    reference_extract, extract_counts = load_reference(extract_parts, target_keys)
    reference_gt, gt_counts = load_reference([iter29_gt], target_keys)
    failures = []
    if len(log_paths) != 2:
        failures.append(f"log_paths={len(log_paths)} != 2")
    if len(gt_paths) != 2:
        failures.append(f"gt_paths={len(gt_paths)} != 2")
    if len(target_keys) != TARGET_ROWS:
        failures.append(f"target_keys={len(target_keys)} != {TARGET_ROWS}")
    for key in sorted(target_keys):
        if extract_counts[key] != 1:
            failures.append(f"iter29_extract_count[{key_label(key)}]={extract_counts[key]} != 1")
        if gt_counts[key] != 1:
            failures.append(f"iter29_gt_count[{key_label(key)}]={gt_counts[key]} != 1")

    model_runs = [summarize_model_run(path, target_keys) for path in log_paths]
    gt_runs = [summarize_gt_run(path, target_keys) for path in gt_paths]

    for run in model_runs:
        if run["non_reset_rows"] != PREFIX_ROWS:
            failures.append(f"{run['path']}:non_reset_rows={run['non_reset_rows']} != {PREFIX_ROWS}")
        if run["target_rows"] != TARGET_ROWS:
            failures.append(f"{run['path']}:target_rows={run['target_rows']} != {TARGET_ROWS}")
        if run["context_only_rows"] != PREFIX_ROWS - TARGET_ROWS:
            failures.append(f"{run['path']}:context_only_rows={run['context_only_rows']} != 32")
        if run["error_rows"]:
            failures.append(f"{run['path']}:error_rows={run['error_rows']} != 0")
        for kind in ("unexpected_target_keys", "missing_target_keys", "duplicate_target_keys"):
            if run[kind]:
                failures.append(f"{run['path']}:{kind}={run[kind]}")

    for run in gt_runs:
        if run["non_reset_rows"] != PREFIX_ROWS:
            failures.append(f"{run['path']}:gt_non_reset_rows={run['non_reset_rows']} != {PREFIX_ROWS}")
        if run["target_rows"] != TARGET_ROWS:
            failures.append(f"{run['path']}:gt_target_rows={run['target_rows']} != {TARGET_ROWS}")
        for kind in ("unexpected_target_keys", "missing_target_keys", "duplicate_target_keys"):
            if run[kind]:
                failures.append(f"{run['path']}:{kind}={run[kind]}")

    model_hashes = [run["target_canonical_sha256"] for run in model_runs]
    gt_hashes = [run["target_canonical_sha256"] for run in gt_runs]
    if len(set(model_hashes)) > 1:
        failures.append(f"model_target_hashes_not_equal={model_hashes}")
    if len(set(gt_hashes)) > 1:
        failures.append(f"gt_target_hashes_not_equal={gt_hashes}")

    max_model_delta = 0.0
    max_gt_delta = 0.0
    for run in model_runs:
        for row in run["target_rows_data"]:
            key = key_of(row)
            reference = reference_extract.get(key)
            if reference is None:
                continue
            compare_exact(row, reference, ["command", "runner_timestamp"], failures, "model")
            max_model_delta = max(
                max_model_delta,
                compare_numeric(
                    row,
                    reference,
                    ["traj", "cands", "objs", "futs", "sdc_traj_query_last", "sdc_track_query"],
                    MODEL_TOLERANCE,
                    failures,
                    "model",
                ),
            )

    for run in gt_runs:
        for row in run["target_rows_data"]:
            key = key_of(row)
            reference = reference_gt.get(key)
            if reference is None:
                continue
            compare_exact(row, reference, ["command"], failures, "gt")
            max_gt_delta = max(
                max_gt_delta,
                compare_numeric(
                    row,
                    reference,
                    ["speed", "yaw_rate", "accel", "gt_future"],
                    GT_TOLERANCE,
                    failures,
                    "gt",
                ),
            )

    return {
        "schema_version": "sentinel.iter32.prefix_replay_report.v1",
        "command_line": " ".join(sys.argv),
        "target_manifest": str(target_manifest),
        "target_rows_expected": TARGET_ROWS,
        "prefix_rows_expected": PREFIX_ROWS,
        "model_runs": [public_run_summary(run) for run in model_runs],
        "gt_runs": [public_run_summary(run) for run in gt_runs],
        "model_target_repeat_hashes": model_hashes,
        "gt_target_repeat_hashes": gt_hashes,
        "max_model_abs_delta_vs_iter29": max_model_delta,
        "model_tolerance": MODEL_TOLERANCE,
        "max_gt_abs_delta_vs_iter29": max_gt_delta,
        "gt_tolerance": GT_TOLERANCE,
        "failure_count": len(failures),
        "failures": failures[:100],
        "s1_prefix_replay_pass": not failures,
        "claim_boundary": (
            "This report checks no-op prefix replay baseline parity only. It is not an "
            "intervention, calibration, heldout, iteration-12, selector, closed-loop, or safety result."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="append", required=True)
    parser.add_argument("--gt-log", action="append", required=True)
    parser.add_argument(
        "--target-manifest",
        default=str(ITER31 / "proof-direction/replay_manifest_canary.json"),
    )
    parser.add_argument("--extract-part", action="append")
    parser.add_argument(
        "--iter29-gt",
        default=str(ITER29 / "proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"),
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    extract_parts = [Path(path) for path in args.extract_part] if args.extract_part else default_extract_parts()
    report = analyze(
        [Path(path) for path in args.log],
        [Path(path) for path in args.gt_log],
        Path(args.target_manifest),
        extract_parts,
        Path(args.iter29_gt),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["s1_prefix_replay_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
