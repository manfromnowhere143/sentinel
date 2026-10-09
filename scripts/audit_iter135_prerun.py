"""Exploratory pre-run sensitivity from committed Iteration-134 evidence.

This is design analysis, not an Iteration-135 outcome or registered analyzer.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import random
import re
import statistics
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "experiments/iter134_neuroncap_placebo_semantics_execution/proof/i134-runs.tar.gz"
ARCHIVE_SHA256 = "b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315"
CLASSES = ("stationary", "frontal", "side")
ARMS = ("off", "union", "placebo")
PAIRS_BY_CLASS = {
    "stationary": "0099 0101 0103 0106 0108 0278 0331 0783 0796 0966".split(),
    "frontal": "0103 0106 0110 0346 0923".split(),
    "side": "0103 0108 0110 0278 0921".split(),
}
PAIR_IDS = [(cls, scene) for cls in CLASSES for scene in PAIRS_BY_CLASS[cls]]
SCENES = tuple(dict.fromkeys(scene for _, scene in PAIR_IDS))
MEMBER = re.compile(
    r"i134-(off|union|placebo)/(stationary|frontal|side)-(\d{4})/"
    r"run_(\d+)/(metrics|ego_poses)\.json"
)
MAX_JSON_BYTES = 10_000_000
DRAWS = 100_000
SEED = 135


def checked_digest(path: Path, expected: str = ARCHIVE_SHA256) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError(f"archive SHA256 mismatch: {actual}")
    return actual


def finite_number(value: object) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("non-finite or non-numeric metric/pose")
    return float(value)


def fixed_horizon_distance(poses: object) -> float:
    if not isinstance(poses, dict) or len(poses) < 2:
        raise ValueError("missing ego poses")
    ordered = [poses[key] for key in sorted(poses, key=int)[:16]]
    xy = [(finite_number(p[0][3]), finite_number(p[1][3])) for p in ordered]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(xy, xy[1:]))


def read_rows(path: Path = ARCHIVE) -> dict[tuple[str, str, str, int], dict[str, float]]:
    checked_digest(path)
    rows: dict[tuple[str, str, str, int], dict[str, float]] = collections.defaultdict(dict)
    seen: set[tuple[str, str, str, int, str]] = set()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            match = MEMBER.fullmatch(member.name)
            if match is None:
                continue
            arm, cls, scene, run_text, kind = match.groups()
            run = int(run_text)
            if not member.isfile() or not 0 <= run < 20 or (cls, scene) not in PAIR_IDS:
                raise ValueError(f"unexpected member: {member.name}")
            key = (arm, cls, scene, run, kind)
            if key in seen or member.size > MAX_JSON_BYTES:
                raise ValueError(f"duplicate or oversized member: {member.name}")
            seen.add(key)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable member: {member.name}")
            payload = stream.read(MAX_JSON_BYTES + 1)
            if len(payload) != member.size or len(payload) > MAX_JSON_BYTES:
                raise ValueError(f"invalid member size: {member.name}")
            obj = json.loads(payload)
            row = rows[arm, cls, scene, run]
            if kind == "metrics":
                row["ncap"] = finite_number(obj["ncap_score"])
            else:
                row["distance"] = fixed_horizon_distance(obj)
    expected = {
        (arm, cls, scene, run, kind)
        for arm in ARMS
        for cls, scene in PAIR_IDS
        for run in range(20)
        for kind in ("metrics", "ego_poses")
    }
    if seen != expected:
        raise ValueError(
            f"member inventory mismatch: missing={len(expected - seen)} extra={len(seen - expected)}"
        )
    if len(rows) != 1200 or any(set(row) != {"ncap", "distance"} for row in rows.values()):
        raise ValueError("episode inventory mismatch")
    return rows


def means_from_rows(
    rows: dict[tuple[str, str, str, int], dict[str, float]],
) -> dict[tuple[str, str, str], dict[str, float]]:
    means: dict[tuple[str, str, str], dict[str, float]] = {}
    for arm in ARMS:
        for cls, scene in PAIR_IDS:
            episodes = [rows[arm, cls, scene, run] for run in range(20)]
            means[arm, cls, scene] = {
                "ncap": statistics.mean(row["ncap"] for row in episodes),
                "distance": statistics.mean(row["distance"] for row in episodes),
            }
    for arm in ARMS:
        for cls, scene in PAIR_IDS:
            baseline = means["off", cls, scene]["distance"]
            if baseline <= 0:
                raise ValueError(f"zero OFF distance for {cls}/{scene}")
            means[arm, cls, scene]["q16"] = statistics.mean(
                min(1.0, rows[arm, cls, scene, run]["distance"] / baseline) for run in range(20)
            )
    return means


def class_balanced(values: dict[tuple[str, str], float]) -> float:
    return statistics.mean(
        statistics.mean(values[cls, scene] for scene in PAIRS_BY_CLASS[cls]) for cls in CLASSES
    )


def percentile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    return ordered[int(proportion * len(ordered)) - 1]


def pair_bootstrap(deltas: dict[tuple[str, str], float]) -> dict[str, float]:
    rng = random.Random(SEED)
    samples = []
    for _ in range(DRAWS):
        class_means = []
        for cls in CLASSES:
            scenes = PAIRS_BY_CLASS[cls]
            class_means.append(
                statistics.mean(deltas[cls, scenes[rng.randrange(len(scenes))]] for _ in scenes)
            )
        samples.append(statistics.mean(class_means))
    return {
        "lower_95": percentile(samples, 0.025),
        "upper_95": percentile(samples, 0.975),
        "se": statistics.stdev(samples),
    }


def shared_scene_bootstrap(deltas: dict[tuple[str, str], float]) -> dict[str, float | int]:
    rng = random.Random(SEED)
    samples = []
    attempts = 0
    while len(samples) < DRAWS:
        attempts += 1
        counts = collections.Counter(SCENES[rng.randrange(len(SCENES))] for _ in SCENES)
        class_means = []
        for cls in CLASSES:
            denominator = sum(counts[scene] for scene in PAIRS_BY_CLASS[cls])
            if denominator == 0:
                break
            class_means.append(
                sum(counts[scene] * deltas[cls, scene] for scene in PAIRS_BY_CLASS[cls])
                / denominator
            )
        if len(class_means) == 3:
            samples.append(statistics.mean(class_means))
    return {
        "lower_95": percentile(samples, 0.025),
        "upper_95": percentile(samples, 0.975),
        "valid_draws": len(samples),
        "attempted_draws": attempts,
    }


def normal_gate_sensitivity(se_n: float, se_q: float) -> dict[str, object]:
    """Illustrative plug-in normal approximation, not an Iteration-135 power claim."""
    normal = statistics.NormalDist()
    z = normal.inv_cdf(0.95)
    n_cut = max(0.25, z * se_n)
    q_cut = -0.05 + z * se_q
    return {
        "ncap_observed_cut": n_cut,
        "q16_observed_cut": q_cut,
        "ncap_gate_probability_by_true_delta": {
            str(delta): 1 - normal.cdf((n_cut - delta) / se_n) for delta in (0.25, 0.5, 0.61, 0.75)
        },
        "q16_gate_probability_by_true_delta": {
            str(delta): 1 - normal.cdf((q_cut - delta) / se_q) for delta in (0.0, 0.003114, 0.06)
        },
    }


def main() -> None:
    rows = read_rows()
    means = means_from_rows(rows)
    report: dict[str, object] = {
        "status": "exploratory_pre_run_design_audit_not_iter135_outcome",
        "archive_sha256": ARCHIVE_SHA256,
        "episodes": len(rows),
        "pair_cells": len(PAIR_IDS),
        "source_scenes": len(SCENES),
        "bootstrap_draws": DRAWS,
        "bootstrap_seed": SEED,
        "metrics": {},
    }
    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    for metric in ("ncap", "q16"):
        arm_means = {
            arm: class_balanced(
                {(cls, scene): means[arm, cls, scene][metric] for cls, scene in PAIR_IDS}
            )
            for arm in ARMS
        }
        deltas = {
            (cls, scene): means["union", cls, scene][metric] - means["placebo", cls, scene][metric]
            for cls, scene in PAIR_IDS
        }
        metrics[metric] = {
            "arm_means": arm_means,
            "union_minus_placebo": class_balanced(deltas),
            "class_stratified_pair_bootstrap": pair_bootstrap(deltas),
            "shared_source_scene_bootstrap": shared_scene_bootstrap(deltas),
        }
    ncap = metrics["ncap"]
    q16 = metrics["q16"]
    report["normal_gate_sensitivity"] = normal_gate_sensitivity(
        ncap["class_stratified_pair_bootstrap"]["se"],
        q16["class_stratified_pair_bootstrap"]["se"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
