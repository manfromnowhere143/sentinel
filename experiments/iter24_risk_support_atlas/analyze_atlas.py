#!/usr/bin/env python3
"""Iteration-24 frozen label-atlas and support-bar analysis.

This script runs only after S0 integrity passes. It computes the pre-registered
fresh risk-support labels, evaluates count and distribution bars, and stops
before probe fitting or activation-direction writing.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import math
from collections import Counter
from pathlib import Path


JOIN_KEY = ("scene", "sample_index", "timestamp_us")
SPLITS = ("fit", "calibration", "heldout")
LABEL_KEYS = (
    "danger_3p5",
    "danger_4p5",
    "safe_5p0",
    "safe_6p0",
    "strict_collapse_0p5",
    "low_diversity_1p0",
    "low_diversity_1p5",
    "high_diversity_2p0",
    "eligible_strict",
    "eligible_lowdiv",
    "benign_control",
)
IMMEDIATE_HORIZON_STEPS = 3
COUNT_FLOORS = {
    "fit": {
        "low_diversity_1p5": 60,
        "high_diversity_2p0": 60,
        "danger_4p5": 60,
        "safe_6p0": 60,
        "eligible_lowdiv": 20,
        "benign_control": 40,
    },
    "calibration": {
        "low_diversity_1p5": 20,
        "high_diversity_2p0": 20,
        "danger_4p5": 20,
        "safe_6p0": 20,
        "eligible_lowdiv": 8,
        "benign_control": 15,
    },
    "heldout": {
        "low_diversity_1p5": 20,
        "high_diversity_2p0": 20,
        "danger_4p5": 20,
        "safe_6p0": 20,
        "eligible_lowdiv": 8,
        "benign_control": 15,
    },
}
STRICT_COUNTS = {
    "fit": {"strict_collapse_0p5": 30, "eligible_strict": 10},
    "calibration": {"strict_collapse_0p5": 10, "eligible_strict": 4},
    "heldout": {"strict_collapse_0p5": 10, "eligible_strict": 4},
}
MIN_ELIGIBLE_LOWDIV_SCENES = {"fit": 5, "calibration": 2, "heldout": 2}
MAX_HELDOUT_SINGLE_SCENE_FRACTION = 0.40


class ConcatenatedBinaryFiles(io.RawIOBase):
    """Read split binary files as one continuous stream."""

    def __init__(self, paths: list[Path]):
        super().__init__()
        self.paths = paths
        self.index = 0
        self.current = open(paths[0], "rb")

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        while self.current is not None:
            n_read = self.current.readinto(buffer)
            if n_read:
                return n_read
            self.current.close()
            self.index += 1
            if self.index >= len(self.paths):
                self.current = None
                return 0
            self.current = open(self.paths[self.index], "rb")
        return 0

    def close(self) -> None:
        if self.current is not None:
            self.current.close()
            self.current = None
        super().close()


def iter_jsonl_gzip(path: str | None = None, parts: list[str] | None = None):
    if parts:
        raw = ConcatenatedBinaryFiles([Path(part) for part in parts])
        with raw, gzip.GzipFile(fileobj=io.BufferedReader(raw), mode="rb") as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as text:
                for line in text:
                    if line.strip():
                        yield json.loads(line)
        return
    if path is None:
        raise SystemExit("either --extract or --extract-part is required")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def key_of(row: dict) -> tuple:
    return tuple(row.get(k) for k in JOIN_KEY)


def load_gt(path: str) -> tuple[dict[tuple, dict], Counter[str], int]:
    gt_by_key = {}
    errors: Counter[str] = Counter()
    total = 0
    for row in iter_jsonl_gzip(path):
        total += 1
        key = key_of(row)
        if None in key or "" in key:
            errors["gt_missing_join_key"] += 1
            continue
        if key in gt_by_key:
            errors["duplicate_gt_key"] += 1
            continue
        gt_by_key[key] = row
    return gt_by_key, errors, total


def endpoint_spread(cands: list) -> float:
    endpoints = [cand[-1] for cand in cands if cand]
    if len(endpoints) < 2:
        return 0.0
    return float(
        max(
            math.hypot(a[0] - b[0], a[1] - b[1])
            for a in endpoints
            for b in endpoints
        )
    )


def closest_gap(plan: list, objs: list, futs: list) -> float:
    best = float("inf")
    for obj, fut in zip(objs, futs):
        ox, oy = obj[0], obj[1]
        mode = fut[0] if fut else []
        if not mode:
            continue
        for k in range(min(IMMEDIATE_HORIZON_STEPS, len(plan))):
            px, py = plan[k]
            ax = ox + (mode[k][0] if k < len(mode) else mode[-1][0])
            ay = oy + (mode[k][1] if k < len(mode) else mode[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


def annotate(row: dict) -> dict:
    gap = closest_gap(row["traj"], row.get("objs", []), row.get("futs", []))
    spread = endpoint_spread(row["cands"])
    danger_3p5 = gap < 3.5
    danger_4p5 = gap < 4.5
    safe_5p0 = gap >= 5.0
    safe_6p0 = gap >= 6.0
    strict_collapse_0p5 = spread <= 0.5
    low_diversity_1p0 = spread <= 1.0
    low_diversity_1p5 = spread <= 1.5
    high_diversity_2p0 = spread >= 2.0
    return {
        "danger_3p5": danger_3p5,
        "danger_4p5": danger_4p5,
        "safe_5p0": safe_5p0,
        "safe_6p0": safe_6p0,
        "strict_collapse_0p5": strict_collapse_0p5,
        "low_diversity_1p0": low_diversity_1p0,
        "low_diversity_1p5": low_diversity_1p5,
        "high_diversity_2p0": high_diversity_2p0,
        "eligible_strict": danger_3p5 and strict_collapse_0p5,
        "eligible_lowdiv": danger_4p5 and low_diversity_1p5,
        "benign_control": safe_6p0 and high_diversity_2p0,
        "closest_gap": gap,
        "endpoint_spread": spread,
    }


def split_label_counts() -> dict[str, dict[str, int]]:
    return {key: {split: 0 for split in SPLITS} for key in LABEL_KEYS}


def scene_label_counts() -> dict[str, dict[str, Counter[str]]]:
    return {key: {split: Counter() for split in SPLITS} for key in LABEL_KEYS}


def split_total_template() -> dict[str, int]:
    return {split: 0 for split in SPLITS}


def summarize_values(values: list[float]) -> dict:
    finite = sorted(v for v in values if math.isfinite(v))
    if not finite:
        return {"count": len(values), "finite_count": 0, "infinite_count": len(values)}
    mid = len(finite) // 2
    median = finite[mid] if len(finite) % 2 else (finite[mid - 1] + finite[mid]) / 2.0
    return {
        "count": len(values),
        "finite_count": len(finite),
        "infinite_count": len(values) - len(finite),
        "min": finite[0],
        "median": median,
        "max": finite[-1],
    }


def count_floor_failures(label_counts: dict[str, dict[str, int]]) -> list[str]:
    failures = []
    for split, requirements in COUNT_FLOORS.items():
        for label, minimum in requirements.items():
            value = label_counts[label][split]
            if value < minimum:
                failures.append(f"{label}.{split}={value} < {minimum}")
    return failures


def strict_count_failures(label_counts: dict[str, dict[str, int]]) -> list[str]:
    failures = []
    for split, requirements in STRICT_COUNTS.items():
        for label, minimum in requirements.items():
            value = label_counts[label][split]
            if value < minimum:
                failures.append(f"{label}.{split}={value} < {minimum}")
    return failures


def distribution_failures(scene_counts: dict[str, dict[str, Counter[str]]]) -> list[str]:
    failures = []
    eligible = scene_counts["eligible_lowdiv"]
    for split, minimum_scene_count in MIN_ELIGIBLE_LOWDIV_SCENES.items():
        contributing = [scene for scene, count in eligible[split].items() if count > 0]
        if len(contributing) < minimum_scene_count:
            failures.append(
                f"eligible_lowdiv.{split}.scene_count={len(contributing)} < {minimum_scene_count}"
            )
    heldout_total = sum(eligible["heldout"].values())
    if heldout_total:
        max_scene, max_count = max(eligible["heldout"].items(), key=lambda item: item[1])
        frac = max_count / heldout_total
        if frac > MAX_HELDOUT_SINGLE_SCENE_FRACTION:
            failures.append(
                "eligible_lowdiv.heldout.max_scene_fraction="
                f"{max_scene}:{frac:.3f} > {MAX_HELDOUT_SINGLE_SCENE_FRACTION:.3f}"
            )
    return failures


def serializable_scene_counts(scene_counts: dict[str, dict[str, Counter[str]]]) -> dict:
    return {
        label: {split: dict(sorted(counter.items())) for split, counter in split_counts.items()}
        for label, split_counts in scene_counts.items()
    }


def analyze(args: argparse.Namespace) -> dict:
    gt_by_key, gt_errors, gt_rows_total = load_gt(args.gt)
    seen_extract_keys = set()
    label_counts = split_label_counts()
    by_scene = scene_label_counts()
    rows_by_split = split_total_template()
    gap_values = {split: [] for split in SPLITS}
    spread_values = {split: [] for split in SPLITS}
    errors: Counter[str] = Counter(gt_errors)
    extract_rows_total = 0
    extract_nonreset_rows_total = 0
    joined_rows = 0

    for row in iter_jsonl_gzip(args.extract, args.extract_part):
        extract_rows_total += 1
        if row.get("reset"):
            continue
        extract_nonreset_rows_total += 1
        key = key_of(row)
        if None in key or "" in key:
            errors["extract_missing_join_key"] += 1
            continue
        if key in seen_extract_keys:
            errors["duplicate_extract_key"] += 1
            continue
        seen_extract_keys.add(key)
        gt = gt_by_key.get(key)
        if gt is None:
            errors["missing_gt"] += 1
            continue
        split = gt.get("split")
        scene = gt.get("scene")
        if split not in SPLITS:
            errors["invalid_gt_split"] += 1
            continue
        if not isinstance(scene, str) or not scene.startswith("scene-"):
            errors["invalid_gt_scene"] += 1
            continue
        if row.get("split") != split:
            errors["extract_gt_split_mismatch"] += 1
            continue
        if row.get("intervention_alpha") != 0.0:
            errors["nonzero_intervention_alpha"] += 1
            continue
        if len(row.get("cands", [])) != 3:
            errors["invalid_candidate_count"] += 1
            continue
        try:
            ann = annotate(row)
        except Exception as exc:  # noqa: BLE001 - report all annotation failures by type.
            errors[f"annotation_error_{type(exc).__name__}"] += 1
            continue
        joined_rows += 1
        rows_by_split[split] += 1
        gap_values[split].append(float(ann["closest_gap"]))
        spread_values[split].append(float(ann["endpoint_spread"]))
        for label in LABEL_KEYS:
            if ann[label]:
                label_counts[label][split] += 1
                by_scene[label][split][scene] += 1

    for key in set(gt_by_key) - seen_extract_keys:
        if None not in key:
            errors["gt_without_extract"] += 1

    count_failures = count_floor_failures(label_counts)
    scene_distribution_failures = distribution_failures(by_scene)
    strict_failures = strict_count_failures(label_counts)
    pass_integrity = (
        not errors
        and extract_nonreset_rows_total == gt_rows_total
        and joined_rows == gt_rows_total
    )
    support_pass = pass_integrity and not count_failures and not scene_distribution_failures
    strict_support_pass = pass_integrity and not strict_failures
    if not pass_integrity:
        verdict = "INFRASTRUCTURE_NULL_STOP_BEFORE_SUPPORT_CLAIM"
    elif support_pass:
        verdict = "SUPPORT_PASS_SUCCESSOR_PREREG_AUTHORIZED"
    else:
        verdict = "SUPPORT_NULL_STOP_NO_SUCCESSOR_AUTHORIZED"

    return {
        "stage": "iter24_fresh_risk_support_atlas",
        "inputs": {
            "extract": args.extract,
            "extract_parts": args.extract_part,
            "gt": args.gt,
        },
        "row_counts": {
            "extract_rows_total": extract_rows_total,
            "extract_nonreset_rows_total": extract_nonreset_rows_total,
            "gt_rows_total": gt_rows_total,
            "joined_rows": joined_rows,
            "rows_by_split": rows_by_split,
        },
        "error_row_types": dict(errors),
        "s0_integrity_rechecked": pass_integrity,
        "label_counts": label_counts,
        "label_counts_by_scene": serializable_scene_counts(by_scene),
        "count_floors": COUNT_FLOORS,
        "count_floor_failures": count_failures,
        "distribution_bars": {
            "min_eligible_lowdiv_scenes": MIN_ELIGIBLE_LOWDIV_SCENES,
            "max_heldout_single_scene_fraction": MAX_HELDOUT_SINGLE_SCENE_FRACTION,
        },
        "distribution_failures": scene_distribution_failures,
        "support_pass": support_pass,
        "strict_optional_counts": STRICT_COUNTS,
        "strict_optional_failures": strict_failures,
        "strict_optional_support_pass": strict_support_pass,
        "closest_gap_summary": {split: summarize_values(gap_values[split]) for split in SPLITS},
        "endpoint_spread_summary": {
            split: summarize_values(spread_values[split]) for split in SPLITS
        },
        "verdict": verdict,
        "claim_boundary": (
            "This report computes only frozen fresh-scene risk-support labels and support bars. "
            "A pass authorizes only a separate successor pre-registration; it does not authorize "
            "probe fitting, activation intervention, iteration-12 scoring, selector evaluation, "
            "or closed-loop evaluation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", help="Reconstructed extraction gzip.")
    parser.add_argument(
        "--extract-part",
        action="append",
        help="Split extraction gzip part. Repeat in byte-concatenation order.",
    )
    parser.add_argument("--gt", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    if args.extract and args.extract_part:
        raise SystemExit("use either --extract or --extract-part, not both")
    if not args.extract and not args.extract_part:
        raise SystemExit("either --extract or --extract-part is required")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = analyze(args)
    (out_dir / "label_atlas_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
