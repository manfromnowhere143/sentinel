#!/usr/bin/env python3
"""Iteration-23 S0 integrity analysis."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

from canonical_jsonl_hash import canonical_sha256


JOIN_KEY = ("scene", "sample_index", "timestamp_us")
SHAPE_KEYS = ("sdc_traj_query_last_shape", "sdc_track_query_shape")


def load_jsonl(path: str) -> list[dict]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def key_of(row: dict) -> tuple:
    return tuple(row.get(k) for k in JOIN_KEY)


def duplicate_keys(rows: list[dict]) -> list[tuple]:
    seen = set()
    dupes = []
    for row in rows:
        key = key_of(row)
        if key in seen:
            dupes.append(key)
        seen.add(key)
    return dupes


def analyze_pair(extract_path: str, gt_path: str) -> dict:
    extract_rows = load_jsonl(extract_path)
    gt_rows = load_jsonl(gt_path)
    extract_nonreset = [row for row in extract_rows if not row.get("reset")]
    gt_by_key = {key_of(row): row for row in gt_rows}
    extract_by_key = {key_of(row): row for row in extract_nonreset}
    error_types: Counter[str] = Counter()
    joined = []
    for row in extract_nonreset:
        key = key_of(row)
        if None in key or "" in key:
            error_types["missing_join_key"] += 1
            continue
        if key not in gt_by_key:
            error_types["missing_gt"] += 1
            continue
        if "context_error" in row:
            error_types["context_error"] += 1
            continue
        for shape_key in SHAPE_KEYS:
            if shape_key not in row:
                error_types[f"missing_{shape_key}"] += 1
        if any(k.endswith("_err") for k in row):
            error_types["patch_error"] += 1
        joined.append({**row, **{f"gt_{k}": v for k, v in gt_by_key[key].items()}})
    for key in set(gt_by_key) - set(extract_by_key):
        if None not in key:
            error_types["gt_without_extract"] += 1
    shape_counts = {
        shape_key: dict(Counter(json.dumps(row.get(shape_key), sort_keys=True) for row in joined))
        for shape_key in SHAPE_KEYS
    }
    split_counts = dict(Counter(row.get("gt_split") for row in joined))
    extract_hash, extract_canon_rows = canonical_sha256(extract_path)
    gt_hash, gt_canon_rows = canonical_sha256(gt_path)
    pass_s0 = (
        len(extract_nonreset) == len(gt_rows)
        and len(joined) == len(gt_rows)
        and not error_types
        and not duplicate_keys(extract_nonreset)
        and not duplicate_keys(gt_rows)
        and all(len(counts) == 1 and "null" not in counts for counts in shape_counts.values())
    )
    return {
        "extract_path": extract_path,
        "gt_path": gt_path,
        "extract_rows_total": len(extract_rows),
        "extract_nonreset_rows_total": len(extract_nonreset),
        "gt_rows_total": len(gt_rows),
        "joined_rows": len(joined),
        "split_counts": split_counts,
        "error_row_types": dict(error_types),
        "duplicate_extract_keys": len(duplicate_keys(extract_nonreset)),
        "duplicate_gt_keys": len(duplicate_keys(gt_rows)),
        "shape_counts": shape_counts,
        "canonical_sha256": {
            "extract": extract_hash,
            "extract_rows": extract_canon_rows,
            "gt": gt_hash,
            "gt_rows": gt_canon_rows,
        },
        "s0_integrity_pass": pass_s0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="append", required=True)
    parser.add_argument("--gt", action="append", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    if len(args.extract) != len(args.gt):
        raise SystemExit("--extract and --gt counts must match")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = [analyze_pair(extract, gt) for extract, gt in zip(args.extract, args.gt)]
    canary_determinism_pass = None
    if len(pairs) == 2:
        canary_determinism_pass = (
            pairs[0]["canonical_sha256"]["extract"] == pairs[1]["canonical_sha256"]["extract"]
            and pairs[0]["canonical_sha256"]["gt"] == pairs[1]["canonical_sha256"]["gt"]
        )
    report = {
        "pairs": pairs,
        "canary_determinism_pass": canary_determinism_pass,
        "all_s0_integrity_pass": all(pair["s0_integrity_pass"] for pair in pairs),
    }
    (out_dir / "s0_integrity_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
