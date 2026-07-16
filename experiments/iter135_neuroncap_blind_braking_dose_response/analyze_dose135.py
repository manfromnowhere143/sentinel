#!/usr/bin/env python3
"""Frozen Iteration-135 raw-proof analyzer.

This program is intentionally the first mutable boundary after the raw proof.  It reads the
merged benchmark log, run archive (or an exact extracted root), per-arm decision logs, frozen
schedule, launch validity receipt, and Iteration-134 drift oracle directly.  There is no accepted
intermediate table or post-run normalizer.

The command-line interface is flag-only so every evidence input is named and manifest-bindable::

    analyze_dose135.py \
      --i135-log proof/sentinel-i135.log.gz \
      --i135-runs proof/i135-runs.tar.gz \
      --schedule dose_schedules.json \
      --launch-manifest launch_manifest.json \
      --validity-receipt proof/launch_validity_receipt.json \
      --proof-commit-receipt /tmp/iter135-proof-commit-receipt.json \
      --decision-log off_baseline=proof/sentinel_i135_off.jsonl.gz \
      --decision-log released_union_semantic_reference=proof/sentinel_i135_union.jsonl.gz \
      --decision-log blind_0_5x=proof/sentinel_i135_blind_0_5x.jsonl.gz \
      --decision-log blind_1_0x=proof/sentinel_i135_blind_1_0x.jsonl.gz \
      --decision-log blind_1_5x=proof/sentinel_i135_blind_1_5x.jsonl.gz \
      --decision-log blind_2_0x=proof/sentinel_i135_blind_2_0x.jsonl.gz \
      --oracle-log ../iter134.../proof/sentinel-i134.log.gz \
      --oracle-runs ../iter134.../proof/i134-runs.tar.gz \
      --oracle-union-log ../iter134.../proof/sentinel_i134_union.jsonl.gz.part-aa \
      --oracle-union-log ../iter134.../proof/sentinel_i134_union.jsonl.gz.part-ab \
      --out proof/dose135_report.json

Split gzip byte streams are supplied by repeating a flag in byte order.  The analyzer concatenates
and decompresses them internally; callers must not assemble a mutable normalized file.
The dataset/Docker runtime snapshots and retained analytic-lock receipt are mandatory siblings of
``--validity-receipt`` and are independently commit-bound, replayed, and TOCTOU-fingerprinted.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import dataclasses
import gzip
import hashlib
import io
import json
import math
import os
import pathlib
import random
import re
import statistics
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any, TextIO

CLASSES = ("stationary", "frontal", "side")
CLASS_PAIRS = {
    "stationary": ("0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"),
    "frontal": ("0103", "0106", "0110", "0346", "0923"),
    "side": ("0103", "0108", "0110", "0278", "0921"),
}
NRUNS = 20
ARMS = (
    "off_baseline",
    "released_union_semantic_reference",
    "blind_0_5x",
    "blind_1_0x",
    "blind_1_5x",
    "blind_2_0x",
)
BLIND_ARMS = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
ARM_DIRS = {
    "off_baseline": "i135-off",
    "released_union_semantic_reference": "i135-union",
    "blind_0_5x": "i135-blind_0_5x",
    "blind_1_0x": "i135-blind_1_0x",
    "blind_1_5x": "i135-blind_1_5x",
    "blind_2_0x": "i135-blind_2_0x",
}
ORACLE_DIRS = {
    "off_baseline": "i134-off",
    "released_union_semantic_reference": "i134-union",
}
DOSE_BUDGETS = {
    "blind_0_5x": {"stationary": 208, "frontal": 238, "side": 157},
    "blind_1_0x": {"stationary": 416, "frontal": 475, "side": 314},
    "blind_1_5x": {"stationary": 624, "frontal": 713, "side": 471},
    "blind_2_0x": {"stationary": 832, "frontal": 950, "side": 628},
}
DONOR_HORIZON_TOTALS = {"stationary": 3_624, "frontal": 1_347, "side": 1_503}
DONOR_BRAKE_TOTALS = {"stationary": 416, "frontal": 475, "side": 314}
BOOT_DRAWS = 100_000
BOOT_SEED = 135
LCB_INDEX = 4_999
UCB_INDEX = 94_999
CI_LO_INDEX = 2_499
CI_HI_INDEX = 97_499
MAX_T_INDEX = 94_999
DONE_MARKER = "I135_DOSE_DONE"
EXPECTED_UNION_BRAKES = 1_205
EXPECTED_UNION_RELEASES = 156
EXPECTED_ORACLE_LOG_SHA256 = "55c5a77e898f1a1834a984dd02c576f128c0ac445c71f9721256beaac2b04b14"
EXPECTED_ORACLE_RUNS_SHA256 = "b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315"
EXPECTED_ORACLE_UNION_PART_SHA256 = (
    "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
    "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
)
LAUNCH_MANIFEST_SCHEMA = "iter135.launch_manifest.v2"
VALIDITY_RECEIPT_SCHEMA = "iter135.analyzer_validity_receipt.v2"
ENVIRONMENT_SCHEMA = "iter135.environment_receipts.v2"
DATASET_SCHEMA = "iter135.nuscenes_dataset_receipt.v1"
DATASET_RUNTIME_SCHEMA = "iter135.dataset_runtime_snapshot.v1"
DOCKER_RUNTIME_SCHEMA = "iter135.docker_runtime_snapshot.v1"
ANALYTIC_LOCK_SCHEMA = "iter135.analytic_lock.v2"
COMMITTED_PROOF_RECEIPT_SCHEMA = "iter135.committed_proof_receipt.v1"
RAW_PROOF_RECEIPT_SCHEMA = "iter135.raw_proof_receipt.v1"
MINIMUM_LOCAL_COLLECTION_BYTES = 15 * 1024**3
EXPECTED_DATASET_ROOT = "/datasets/nuscenes-full"
EXPECTED_DATASET_VERSION = "v1.0-trainval"
EXPECTED_DATASET_ARCHIVE_ROOT = f"{EXPECTED_DATASET_ROOT}/archives"
EXPECTED_DATASET_METADATA_ROOT = f"{EXPECTED_DATASET_ROOT}/{EXPECTED_DATASET_VERSION}"
EXPECTED_DATASET_MAP_ROOT = f"{EXPECTED_DATASET_ROOT}/maps"
EXPECTED_DATASET_CONTRACT_SHA256 = (
    "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
)
EXPECTED_DATASET_MOUNT = {
    "mount_target": EXPECTED_DATASET_ROOT,
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}
EXPECTED_DATASET_PROOF_BASIS = {
    "iteration": 28,
    "result_path": "experiments/iter28_nuscenes_trainval_staging/RESULT.md",
    "receipt_directory": "experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads",
    "archive_count": 11,
    "archive_total_bytes": 314_886_603_672,
}
EXPECTED_DATASET_ARCHIVES = {
    "v1.0-trainval_meta.tgz": (
        "db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b",
        461_678_030,
    ),
    "v1.0-trainval01_blobs.tgz": (
        "fee4316c55f0780532819ea1b01f347b2ad964303c93477cc815f8191b126171",
        31_579_122_687,
    ),
    "v1.0-trainval02_blobs.tgz": (
        "292301394af9d4a8eb62cee41b3b3031c6cad78e2b39bf63a91bd6d3b7592373",
        30_134_721_083,
    ),
    "v1.0-trainval03_blobs.tgz": (
        "9e6e7c949fbea971321112757dfcff757add646078393c191981a0a49d5f483c",
        29_872_679_856,
    ),
    "v1.0-trainval04_blobs.tgz": (
        "6927f765f8555ce6f901ed2763569bd860b33ad5e076709bbc6c4cc8a51ffc76",
        32_075_538_096,
    ),
    "v1.0-trainval05_blobs.tgz": (
        "ea8d886bc79be30d02e9552d229aaa0843ecffccaaff6606644540b4183f605f",
        28_191_611_840,
    ),
    "v1.0-trainval06_blobs.tgz": (
        "26e3dfff85d8ef6354d4b9dc0a9d8b3f0ebd8719b6d84eac5841fa31b97b8deb",
        27_516_468_993,
    ),
    "v1.0-trainval07_blobs.tgz": (
        "70287e2d65386bce2d67001ef56f5c0abdd3dd95d1ec404c3e00a39208fa60b7",
        29_534_216_608,
    ),
    "v1.0-trainval08_blobs.tgz": (
        "744080381fcfbca3e3ee8d20c5340dce4b5b7fae8020a7e90338ec98b20802c1",
        30_275_496_199,
    ),
    "v1.0-trainval09_blobs.tgz": (
        "ca3aba09dc63cd22fdc455959f3aea99e0f6ed4de822c8c3f5f96f0efa372ec5",
        33_517_622_306,
    ),
    "v1.0-trainval10_blobs.tgz": (
        "046aa7c5ff2cab63a25eaa6210e00bd8197f835e5324457d305a2a16a262f57a",
        41_727_447_974,
    ),
}
EXPECTED_DATASET_METADATA_FILES = (
    "attribute.json",
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "instance.json",
    "log.json",
    "map.json",
    "sample.json",
    "sample_annotation.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
    "visibility.json",
)
EXPECTED_DATASET_MAP_ANCHORS = (
    "36092f0b03a857c6a3403e25b4b7aab3.png",
    "37819e65e09e5547b8a3ceaefba56bb2.png",
    "53992ee3023e5494b90c316c183be829.png",
    "93406b464a165eaba6d9de76ca09f5da.png",
)
RUNTIME_EVIDENCE_FILENAMES = {
    "dataset_runtime_snapshot": "dataset_runtime_snapshot.json",
    "docker_runtime_snapshot": "docker_runtime_snapshot.json",
    "analytic_lock": "analytic_lock.json",
}
DOCKER_DAEMON_INFO_FIELDS = (
    "ID",
    "Name",
    "ServerVersion",
    "DockerRootDir",
    "Driver",
    "OperatingSystem",
    "OSType",
    "Architecture",
    "NCPU",
    "MemTotal",
    "KernelVersion",
    "CgroupDriver",
    "CgroupVersion",
)
DOCKER_DAEMON_VERSION_FIELDS = (
    "Platform",
    "Version",
    "ApiVersion",
    "MinAPIVersion",
    "GitCommit",
    "GoVersion",
    "Os",
    "Arch",
    "BuildTime",
    "Experimental",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")

# The manifest-bound collector/analyzer boundary.  These public names are intentionally explicit:
# hostile tests import them, and a future collector may not silently rename or widen the schema.
EVIDENCE_SCHEMA = "iter135.dose_analysis_evidence.v1"
REPORT_SCHEMA = "iter135.dose_analysis_report.v1"
GATE_IDS = tuple(f"G{index}" for index in range(10))
PAIRS_BY_CLASS = CLASS_PAIRS
RUNS = tuple(range(NRUNS))
OFF_ARM = "off_baseline"
UNION_ARM = "released_union_semantic_reference"
SCHEDULED_BUDGETS = DOSE_BUDGETS
BOOTSTRAP_DRAWS = BOOT_DRAWS
BOOTSTRAP_SEED = BOOT_SEED
ONE_SIDED_LOWER_INDEX = LCB_INDEX
ONE_SIDED_UPPER_INDEX = UCB_INDEX
TWO_SIDED_LOWER_INDEX = CI_LO_INDEX
TWO_SIDED_UPPER_INDEX = CI_HI_INDEX
MAX_T_CRITICAL_INDEX = MAX_T_INDEX
NCAP_MARGIN = 0.25
Q16_NONINFERIORITY_MARGIN = -0.05
BLIND_Q16_COMPETITIVE_UPPER = 0.05

Pair = tuple[str, str]
Cell = tuple[str, str, str, int]


class AnalysisInputError(ValueError):
    """The raw trust boundary is malformed or incomplete."""


# Public schema-boundary name retained separately from raw-proof parser terminology.
EvidenceError = AnalysisInputError


@dataclasses.dataclass(frozen=True)
class ScoreRow:
    ncap: float
    impact_speed: float


@dataclasses.dataclass(frozen=True)
class RunArtifact:
    ego_poses: Mapping[str, Any]
    metrics: Mapping[str, Any]
    actors: Mapping[str, Any] | Sequence[Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class Episode:
    cell: Cell
    ncap: float
    impact_speed: float
    collision: bool
    q16_distance: float
    raw_path_length: float


@dataclasses.dataclass
class DecisionCell:
    frames: set[int] = dataclasses.field(default_factory=set)
    brakes: set[int] = dataclasses.field(default_factory=set)
    releases: int = 0


@dataclasses.dataclass
class ParsedDecisionLog:
    cells: dict[Cell, DecisionCell]
    problems: list[str]
    brake_rows: int
    release_rows: int


@dataclasses.dataclass(frozen=True)
class Bounds:
    lcb95: float
    ucb95: float
    ci95: tuple[float, float]


@dataclasses.dataclass(frozen=True)
class PrimaryInference:
    delta_ncap: float
    lcb_ncap: float
    ucb_ncap: float
    ci_ncap: tuple[float, float]
    delta_q16: float
    lcb_q16: float
    ucb_q16: float
    ci_q16: tuple[float, float]


@dataclasses.dataclass(frozen=True)
class FrontierInference:
    arm: str
    delta_ncap: float
    interval_ncap: tuple[float, float]
    delta_q16: float
    interval_q16: tuple[float, float]


@dataclasses.dataclass(frozen=True)
class EvidenceEpisode:
    arm: str
    scenario_class: str
    pair: str
    run: int
    ncap_score: float
    impact_speed: float
    ego_points: tuple[tuple[float, float], ...]
    collision: bool
    terminal_reason: str
    episode_frame_count: int
    scheduled_brake_frames: tuple[int, ...]
    realized_brake_frames: tuple[int, ...]
    realized_release_frames: tuple[int, ...]

    @property
    def cell(self) -> Cell:
        return self.arm, self.scenario_class, self.pair, self.run


@dataclasses.dataclass(frozen=True)
class ParsedEvidence:
    episodes: tuple[EvidenceEpisode, ...]
    validity_gates: dict[str, dict[str, Any]]
    falsifiers: tuple[str, ...]


def canonical_pairs() -> tuple[Pair, ...]:
    return tuple((cls, seq) for cls in CLASSES for seq in CLASS_PAIRS[cls])


def canonical_pair_runs() -> tuple[tuple[str, str, int], ...]:
    return tuple((cls, seq, run) for cls, seq in canonical_pairs() for run in range(NRUNS))


def expected_cells(arms: Sequence[str] = ARMS) -> set[Cell]:
    return {(arm, cls, seq, run) for arm in arms for cls, seq, run in canonical_pair_runs()}


def expected_execution_blocks() -> list[tuple[str, str, str]]:
    """The amended 120 compose blocks: pair-major, rotated by global pair index."""

    blocks: list[tuple[str, str, str]] = []
    for global_pair_index, (cls, seq) in enumerate(canonical_pairs()):
        rotation = global_pair_index % len(ARMS)
        rotated = ARMS[rotation:] + ARMS[:rotation]
        blocks.extend((arm, cls, seq) for arm in rotated)
    return blocks


def expected_execution_order() -> list[Cell]:
    return [
        (arm, cls, seq, run)
        for arm, cls, seq in expected_execution_blocks()
        for run in range(NRUNS)
    ]


def sha256_file(path: str | pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_input_fingerprint(path: pathlib.Path) -> tuple[str, str, int]:
    """Hash one regular input with an inode-stability check, or record its non-file state."""

    try:
        before = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return ("missing", "", 0)
    if path.is_symlink():
        return ("symlink", "", 0)
    if path.is_dir():
        return ("directory", source_digest(path)["sha256"], 0)
    if not path.is_file():
        return ("non-regular", "", before.st_mode)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        opened_identity = (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        )
        if opened_identity != identity:
            raise AnalysisInputError(f"input replaced before fingerprint: {path}")
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
        after_open = os.fstat(handle.fileno())
    after = path.stat(follow_symlinks=False)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if opened_identity != (
        after_open.st_dev,
        after_open.st_ino,
        after_open.st_size,
        after_open.st_mtime_ns,
    ) or after_identity != opened_identity:
        raise AnalysisInputError(f"input mutated during fingerprint: {path}")
    return ("file", digest.hexdigest(), opened.st_size)


def _analysis_input_paths(args: argparse.Namespace) -> dict[str, pathlib.Path]:
    validity_path = pathlib.Path(args.validity_receipt)
    paths = {
        "i135_log": pathlib.Path(args.i135_log),
        "i135_runs": pathlib.Path(args.i135_runs),
        "schedule": pathlib.Path(args.schedule),
        "launch_manifest": pathlib.Path(args.launch_manifest),
        "validity_receipt": validity_path,
        "proof_commit_receipt": pathlib.Path(args.proof_commit_receipt),
        "oracle_log": pathlib.Path(args.oracle_log),
        "oracle_runs": pathlib.Path(args.oracle_runs),
        **{
            role: validity_path.parent / filename
            for role, filename in RUNTIME_EVIDENCE_FILENAMES.items()
        },
    }
    for index, value in enumerate(args.decision_log):
        _arm, separator, raw_path = value.partition("=")
        if separator and raw_path:
            paths[f"decision_{index}"] = pathlib.Path(raw_path)
    for index, raw_path in enumerate(args.oracle_union_log):
        paths[f"oracle_union_{index}"] = pathlib.Path(raw_path)
    return paths


def capture_analysis_input_state(
    args: argparse.Namespace,
) -> dict[str, tuple[str, str, int]]:
    return {
        role: _stable_input_fingerprint(path)
        for role, path in sorted(_analysis_input_paths(args).items())
    }


def source_digest(path: str | pathlib.Path) -> dict[str, str]:
    """Bind an archive byte-for-byte or an extracted root by relative path and file digest."""

    source = pathlib.Path(path)
    if source.is_file():
        return {"kind": "file", "sha256": sha256_file(source)}
    if not source.is_dir():
        raise AnalysisInputError(f"cannot digest missing run source: {source}")
    digest = hashlib.sha256()
    for member in sorted(source.rglob("*")):
        if member.is_symlink():
            raise AnalysisInputError(f"run source contains symlink: {member}")
        if not member.is_file():
            continue
        relative = member.relative_to(source).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        file_digest = bytes.fromhex(sha256_file(member))
        digest.update(file_digest)
    return {"kind": "directory-tree", "sha256": digest.hexdigest()}


class _ConcatenatedRaw(io.RawIOBase):
    """Read several files as one byte stream without materializing a concatenated copy."""

    def __init__(self, paths: Sequence[str | pathlib.Path]):
        super().__init__()
        self._paths = iter(paths)
        self._current: io.BufferedReader | None = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray) -> int:
        view = memoryview(buffer)
        total = 0
        while total < len(view):
            if self._current is None:
                try:
                    self._current = open(next(self._paths), "rb")
                except StopIteration:
                    break
            count = self._current.readinto(view[total:])
            if count:
                total += count
                continue
            self._current.close()
            self._current = None
        return total

    def close(self) -> None:
        if self._current is not None:
            self._current.close()
            self._current = None
        super().close()


@contextlib.contextmanager
def open_text_parts(paths: Sequence[str | pathlib.Path]) -> Iterator[TextIO]:
    """Open raw text files or a (possibly physically split) gzip stream."""

    if not paths:
        raise AnalysisInputError("no input paths supplied")
    for path in paths:
        if not pathlib.Path(path).is_file():
            raise AnalysisInputError(f"input is not a file: {path}")
    with open(paths[0], "rb") as first:
        compressed = first.read(2) == b"\x1f\x8b"
    raw = _ConcatenatedRaw(paths)
    buffered = io.BufferedReader(raw)
    binary: io.BufferedIOBase | gzip.GzipFile
    binary = gzip.GzipFile(fileobj=buffered, mode="rb") if compressed else buffered
    text = io.TextIOWrapper(binary, encoding="utf-8", errors="replace")
    try:
        yield text
    finally:
        text.close()


_FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_I135_MARKER = re.compile(r"^##### I135BLOCK (\S+) (\S+) (\S+)(?: #####)?$")
_I134_MARKER = re.compile(r"^##### I134PAIR (\S+) (\S+) (\S+)(?: #####)?$")
_SCORE = re.compile(
    rf"ncap_score:\s*({_FLOAT}),\s*impact_speed:\s*({_FLOAT})"
)


def parse_i135_log(path: str | pathlib.Path) -> tuple[dict[Cell, ScoreRow], list[str], list[Cell]]:
    """Bind each strict I135 compose-block marker to its next 20 benchmark scores."""

    scores: dict[Cell, ScoreRow] = {}
    flattened_order: list[Cell] = []
    block_order: list[tuple[str, str, str]] = []
    problems: list[str] = []
    current: tuple[str, str, str] | None = None
    block_score_count = 0
    done_count = 0
    exact = expected_cells()

    def close_block(where: str) -> None:
        if current is not None and block_score_count != NRUNS:
            problems.append(
                f"merged-log:block-score-count:{'/'.join(current)}:{block_score_count}/{NRUNS}:{where}"
            )

    with open_text_parts([path]) as handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            marker = _I135_MARKER.fullmatch(line)
            if marker:
                close_block(f"before-line-{lineno}")
                arm, cls, seq = marker.groups()
                current = (arm, cls, seq)
                block_score_count = 0
                block_order.append(current)
                if not all((arm, cls, seq, run) in exact for run in range(NRUNS)):
                    problems.append(f"merged-log:unexpected-block:{'/'.join(current)}")
                continue
            if line.startswith("##### I135"):
                close_block(f"before-malformed-line-{lineno}")
                problems.append(f"merged-log:malformed-marker:{lineno}")
                current = None
                block_score_count = 0
                continue
            score_match = _SCORE.search(line)
            if score_match:
                if current is None:
                    problems.append(f"merged-log:unbound-score:{lineno}")
                    continue
                if block_score_count >= NRUNS:
                    problems.append(
                        f"merged-log:too-many-scores:{'/'.join(current)}:{block_score_count + 1}:{lineno}"
                    )
                    block_score_count += 1
                    continue
                cell = (*current, block_score_count)
                flattened_order.append(cell)
                ncap, impact = map(float, score_match.groups())
                if not math.isfinite(ncap) or not math.isfinite(impact):
                    problems.append(f"merged-log:nonfinite-score:{cell_id(cell)}")
                elif ncap < 0 or impact < 0:
                    problems.append(f"merged-log:negative-score:{cell_id(cell)}")
                else:
                    scores[cell] = ScoreRow(ncap=ncap, impact_speed=impact)
                block_score_count += 1
            if line == DONE_MARKER:
                done_count += 1
    close_block("at-eof")
    missing = sorted(exact - scores.keys())
    extra = sorted(scores.keys() - exact)
    if missing:
        problems.append(f"merged-log:missing-cells:{len(missing)}:{cell_id(missing[0])}")
    if extra:
        problems.append(f"merged-log:extra-cells:{len(extra)}:{cell_id(extra[0])}")
    expected_blocks = expected_execution_blocks()
    if len(block_order) != len(expected_blocks):
        problems.append(f"merged-log:block-count:{len(block_order)}/{len(expected_blocks)}")
    if block_order != expected_blocks:
        mismatch = first_sequence_mismatch(block_order, expected_blocks)
        problems.append(f"merged-log:block-order:{mismatch}")
    expected_order = expected_execution_order()
    if flattened_order != expected_order:
        mismatch = first_sequence_mismatch(flattened_order, expected_order)
        problems.append(f"merged-log:execution-order:{mismatch}")
    if done_count != 1:
        problems.append(f"merged-log:done-marker-count:{done_count}")
    return scores, problems, flattened_order


def parse_i134_oracle_log(path: str | pathlib.Path) -> tuple[dict[Cell, ScoreRow], list[str]]:
    """Parse the raw Iteration-134 OFF/union oracle; run identity is within-block order."""

    arm_map = {"off": "off_baseline", "union": "released_union_semantic_reference"}
    blocks: dict[tuple[str, str, str], list[ScoreRow]] = collections.defaultdict(list)
    problems: list[str] = []
    current: tuple[str, str, str] | None = None
    with open_text_parts([path]) as handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            marker = _I134_MARKER.fullmatch(line)
            if marker:
                old_arm, cls, seq = marker.groups()
                current = (old_arm, cls, seq) if old_arm in arm_map else None
                continue
            score_match = _SCORE.search(line)
            if score_match and current is not None:
                ncap, impact = map(float, score_match.groups())
                blocks[current].append(ScoreRow(ncap=ncap, impact_speed=impact))
                if len(blocks[current]) > NRUNS:
                    problems.append(f"oracle-log:too-many-scores:{'/'.join(current)}:{lineno}")
    out: dict[Cell, ScoreRow] = {}
    for old_arm, new_arm in arm_map.items():
        for cls, seq in canonical_pairs():
            rows = blocks.get((old_arm, cls, seq), [])
            if len(rows) != NRUNS:
                problems.append(f"oracle-log:count:{old_arm}/{cls}/{seq}:{len(rows)}/{NRUNS}")
            for run, row in enumerate(rows[:NRUNS]):
                out[(new_arm, cls, seq, run)] = row
    return out, problems


def first_sequence_mismatch(actual: Sequence[Any], expected: Sequence[Any]) -> str:
    for index, (left, right) in enumerate(zip(actual, expected)):
        if left != right:
            return f"index={index}:actual={left}:expected={right}"
    return f"length:actual={len(actual)}:expected={len(expected)}"


def cell_id(cell: Cell) -> str:
    return f"{cell[0]}/{cell[1]}/{cell[2]}/{cell[3]}"


def _load_json_bytes(payload: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AnalysisInputError(f"malformed JSON at {label}: {error}") from error
    if not isinstance(value, dict):
        raise AnalysisInputError(f"JSON object required at {label}")
    return value


def _load_actors_bytes(payload: bytes, label: str) -> Mapping[str, Any] | Sequence[Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AnalysisInputError(f"malformed JSON at {label}: {error}") from error
    if not isinstance(value, (dict, list)):
        raise AnalysisInputError(f"actors JSON object or list required at {label}")
    return value


def load_run_artifacts(
    source: str | pathlib.Path,
    arm_dirs: Mapping[str, str],
    cells: set[Cell],
) -> tuple[dict[Cell, RunArtifact], list[str]]:
    """Load only raw per-run metrics and poses from a tar or exact extracted root."""

    path = pathlib.Path(source)
    required: dict[str, tuple[Cell, str]] = {}
    for cell in cells:
        arm, cls, seq, run = cell
        prefix = arm_dirs[arm]
        base = f"{prefix}/{cls}-{seq}/run_{run}"
        required[f"{base}/ego_poses.json"] = (cell, "ego")
        required[f"{base}/metrics.json"] = (cell, "metrics")
        required[f"{base}/actors.json"] = (cell, "actors")
    found: dict[tuple[Cell, str], Any] = {}
    problems: list[str] = []

    def accept(name: str, payload: bytes) -> None:
        normalized = name.removeprefix("./")
        target = required.get(normalized)
        if target is None:
            return
        if target in found:
            problems.append(f"runs:duplicate-member:{normalized}")
            return
        found[target] = (
            _load_actors_bytes(payload, normalized)
            if target[1] == "actors"
            else _load_json_bytes(payload, normalized)
        )

    if path.is_dir():
        for name in required:
            file_path = path / name
            if file_path.is_file():
                accept(name, file_path.read_bytes())
    elif path.is_file():
        try:
            with tarfile.open(path, "r:*") as archive:
                for member in archive:
                    normalized = member.name.removeprefix("./")
                    if normalized not in required:
                        continue
                    if not member.isfile():
                        problems.append(f"runs:not-regular-file:{normalized}")
                        continue
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        problems.append(f"runs:unreadable-member:{normalized}")
                        continue
                    accept(normalized, extracted.read())
        except tarfile.TarError as error:
            raise AnalysisInputError(f"runs source is not a readable tar archive: {path}: {error}") from error
    else:
        raise AnalysisInputError(f"runs source is neither directory nor archive: {path}")

    artifacts: dict[Cell, RunArtifact] = {}
    for cell in sorted(cells):
        ego = found.get((cell, "ego"))
        metrics = found.get((cell, "metrics"))
        actors = found.get((cell, "actors"))
        if ego is None or metrics is None or actors is None:
            missing_kinds = [
                kind
                for kind, value in (("ego", ego), ("metrics", metrics), ("actors", actors))
                if value is None
            ]
            problems.append(f"runs:missing:{cell_id(cell)}:{','.join(missing_kinds)}")
            continue
        artifacts[cell] = RunArtifact(ego_poses=ego, metrics=metrics, actors=actors)
    if len(artifacts) != len(cells):
        problems.append(f"runs:complete-cells:{len(artifacts)}/{len(cells)}")
    return artifacts, problems


def _pose_sort_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except (TypeError, ValueError):
        return (1, str(value))


def pose_xy(ego_poses: Mapping[str, Any]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for key, matrix in sorted(ego_poses.items(), key=lambda item: _pose_sort_key(item[0])):
        try:
            x = float(matrix[0][3])
            y = float(matrix[1][3])
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise AnalysisInputError(f"invalid ego transform at pose {key}") from error
        if not math.isfinite(x) or not math.isfinite(y):
            raise AnalysisInputError(f"nonfinite ego translation at pose {key}")
        out.append((x, y))
    return out


def pose_points(raw: Any, where: str = "ego_poses") -> tuple[tuple[float, float], ...]:
    """Strictly validate raw 4x4 poses and return XY translations in sorted-key order."""

    if not isinstance(raw, dict) or not raw:
        raise EvidenceError(f"{where} must be a nonempty timestamp-keyed object")
    if not all(isinstance(key, str) for key in raw):
        raise EvidenceError(f"{where} keys must be strings")
    for key, matrix in raw.items():
        if not isinstance(matrix, list) or len(matrix) != 4:
            raise EvidenceError(f"{where}[{key!r}] must be a 4x4 matrix")
        for row_index, row in enumerate(matrix):
            if not isinstance(row, list) or len(row) != 4:
                raise EvidenceError(f"{where}[{key!r}][{row_index}] must have four values")
            for column_index, value in enumerate(row):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise EvidenceError(
                        f"{where}[{key!r}][{row_index}][{column_index}] must be numeric"
                    )
                if not math.isfinite(float(value)):
                    raise EvidenceError(
                        f"{where}[{key!r}][{row_index}][{column_index}] must be finite"
                    )
    return tuple(pose_xy(raw))


def path_distance(points: Sequence[tuple[float, float]]) -> float:
    return math.fsum(
        math.hypot(right[0] - left[0], right[1] - left[1])
        for left, right in zip(points, points[1:])
    )


def q16_distance(
    ego_poses_or_points: Mapping[str, Any] | Sequence[tuple[float, float]],
) -> float:
    """Distance over at most the first 16 poses; early terminal poses are absorbing."""

    if isinstance(ego_poses_or_points, Mapping):
        points = pose_xy(ego_poses_or_points)
    else:
        points = ego_poses_or_points
    return path_distance(points[:16])


def assemble_episodes(
    scores: Mapping[Cell, ScoreRow], artifacts: Mapping[Cell, RunArtifact]
) -> tuple[dict[Cell, Episode], list[str]]:
    problems: list[str] = []
    episodes: dict[Cell, Episode] = {}
    all_cells = expected_cells()
    for cell in sorted(all_cells):
        score = scores.get(cell)
        artifact = artifacts.get(cell)
        if score is None or artifact is None:
            continue
        metric_score = artifact.metrics.get("ncap_score")
        try:
            metric_score_float = float(metric_score)
        except (TypeError, ValueError):
            problems.append(f"runs:metrics-ncap-missing:{cell_id(cell)}")
        else:
            if metric_score_float != score.ncap:
                problems.append(
                    f"runs:metrics-log-ncap-mismatch:{cell_id(cell)}:{metric_score_float}!={score.ncap}"
                )
        collision = artifact.metrics.get("any_collide@0.0s")
        if type(collision) is not bool:
            problems.append(f"runs:metrics-collision-missing-or-nonboolean:{cell_id(cell)}")
            continue
        try:
            points = pose_xy(artifact.ego_poses)
        except AnalysisInputError as error:
            problems.append(f"runs:ego-invalid:{cell_id(cell)}:{error}")
            continue
        if not points:
            problems.append(f"runs:ego-empty:{cell_id(cell)}")
            continue
        episodes[cell] = Episode(
            cell=cell,
            ncap=score.ncap,
            impact_speed=score.impact_speed,
            collision=collision,
            q16_distance=path_distance(points[:16]),
            raw_path_length=path_distance(points),
        )
    if len(episodes) != len(all_cells):
        problems.append(f"assembly:complete-cells:{len(episodes)}/{len(all_cells)}")
    return episodes, problems


def validate_exact_cells(actual: Iterable[Cell], expected: Iterable[Cell]) -> list[str]:
    actual_list = list(actual)
    actual_set = set(actual_list)
    expected_set = set(expected)
    problems: list[str] = []
    if len(actual_list) != len(actual_set):
        problems.append(f"duplicate-cells:{len(actual_list) - len(actual_set)}")
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        problems.append(f"missing-cells:{len(missing)}:{cell_id(missing[0])}")
    if extra:
        problems.append(f"extra-cells:{len(extra)}:{cell_id(extra[0])}")
    return problems


def load_schedule(path: str | pathlib.Path) -> tuple[dict[Cell, Mapping[str, Any]], list[str], Mapping[str, Any]]:
    raw = _load_json_bytes(pathlib.Path(path).read_bytes(), str(path))
    problems: list[str] = []
    if raw.get("schema") != "iter135.nested_dose_schedules.v1":
        problems.append(f"schedule:schema:{raw.get('schema')}")
    if raw.get("verdict") != "NESTED_DOSE_SCHEDULES_OK":
        problems.append(f"schedule:verdict:{raw.get('verdict')}")
    rows_raw = raw.get("schedules")
    if not isinstance(rows_raw, dict):
        raise AnalysisInputError("schedule.schedules must be an object")
    schedules: dict[Cell, Mapping[str, Any]] = {}
    expected = expected_cells(BLIND_ARMS)
    if set(rows_raw) != set(BLIND_ARMS):
        problems.append(
            "schedule:dose-set:"
            f"missing={sorted(set(BLIND_ARMS) - set(rows_raw))}:"
            f"extra={sorted(set(rows_raw) - set(BLIND_ARMS))}"
        )
    for arm in BLIND_ARMS:
        dose_rows = rows_raw.get(arm)
        if not isinstance(dose_rows, dict):
            problems.append(f"schedule:dose-not-object:{arm}")
            continue
        for key, value in dose_rows.items():
            if not isinstance(value, dict):
                problems.append(f"schedule:row-not-object:{arm}/{key}")
                continue
            try:
                row_arm = str(value["dose_id"])
                cls = str(value["target_class"])
                seq = str(value["target_seq"])
                run = int(value["target_run"])
            except (KeyError, TypeError, ValueError) as error:
                problems.append(f"schedule:identity:{arm}/{key}:{error}")
                continue
            cell = (arm, cls, seq, run)
            canonical_key = f"{cls}/{seq}/{run}"
            if row_arm != arm:
                problems.append(f"schedule:dose-identity-mismatch:{arm}/{key}:{row_arm}")
            if key != canonical_key:
                problems.append(f"schedule:key-identity-mismatch:{arm}/{key}:{canonical_key}")
            if cell in schedules:
                problems.append(f"schedule:duplicate-cell:{cell_id(cell)}")
                continue
            schedules[cell] = value
    if raw.get("schedule_count") != len(expected):
        problems.append(f"schedule:declared-count:{raw.get('schedule_count')}/{len(expected)}")
    problems.extend(f"schedule:{item}" for item in validate_exact_cells(schedules, expected))

    for cell in sorted(expected & schedules.keys()):
        row = schedules[cell]
        arm, cls, seq, run = cell
        frames = row.get("brake_frames")
        if not isinstance(frames, list) or any(type(frame) is not int for frame in frames):
            problems.append(f"schedule:brake-frames-type:{cell_id(cell)}")
            continue
        if frames != sorted(set(frames)):
            problems.append(f"schedule:brake-frames-not-sorted-unique:{cell_id(cell)}")
        try:
            horizon = int(row["donor_frame_count"])
            scheduled_count = int(row["scheduled_brake_count"])
            donor_class = str(row["donor_class"])
            donor_seq = str(row["donor_seq"])
            donor_run = int(row["donor_run"])
        except (KeyError, TypeError, ValueError) as error:
            problems.append(f"schedule:fields:{cell_id(cell)}:{error}")
            continue
        if scheduled_count != len(frames):
            problems.append(f"schedule:count-mismatch:{cell_id(cell)}:{scheduled_count}!={len(frames)}")
        if not frames:
            problems.append(f"schedule:no-support:{cell_id(cell)}")
        if horizon <= 0 or any(frame < 0 or frame >= horizon for frame in frames):
            problems.append(f"schedule:horizon:{cell_id(cell)}:{horizon}")
        if donor_class != cls or donor_seq == seq or donor_run == run:
            problems.append(f"schedule:donor-exclusion:{cell_id(cell)}")
        pair_index = CLASS_PAIRS[cls].index(seq) if cls in CLASS_PAIRS and seq in CLASS_PAIRS[cls] else -1
        if pair_index >= 0:
            expected_donor_seq = CLASS_PAIRS[cls][(pair_index + 2) % len(CLASS_PAIRS[cls])]
            expected_donor_run = (run + 7) % NRUNS
            if donor_seq != expected_donor_seq or donor_run != expected_donor_run:
                problems.append(
                    f"schedule:donor-rule:{cell_id(cell)}:{donor_seq}/{donor_run}!="
                    f"{expected_donor_seq}/{expected_donor_run}"
                )
        donor_brakes = row.get("donor_brake_frames")
        if (
            not isinstance(donor_brakes, list)
            or any(type(frame) is not int for frame in donor_brakes)
            or donor_brakes != sorted(set(donor_brakes))
            or any(frame < 0 or frame >= horizon for frame in donor_brakes)
        ):
            problems.append(f"schedule:donor-brake-frames:{cell_id(cell)}")

    for arm in BLIND_ARMS:
        for cls in CLASSES:
            total = sum(
                len(schedules[(arm, cls, seq, run)].get("brake_frames", []))
                for seq in CLASS_PAIRS[cls]
                for run in range(NRUNS)
                if (arm, cls, seq, run) in schedules
            )
            required = DOSE_BUDGETS[arm][cls]
            if total != required:
                problems.append(f"schedule:class-budget:{arm}/{cls}:{total}/{required}")
            rows = [
                schedules[(arm, cls, seq, run)]
                for seq in CLASS_PAIRS[cls]
                for run in range(NRUNS)
                if (arm, cls, seq, run) in schedules
            ]
            horizon_total = sum(int(row.get("donor_frame_count", 0)) for row in rows)
            donor_brake_total = sum(len(row.get("donor_brake_frames", [])) for row in rows)
            if horizon_total != DONOR_HORIZON_TOTALS[cls]:
                problems.append(
                    f"schedule:donor-horizon-total:{arm}/{cls}:"
                    f"{horizon_total}/{DONOR_HORIZON_TOTALS[cls]}"
                )
            if donor_brake_total != DONOR_BRAKE_TOTALS[cls]:
                problems.append(
                    f"schedule:donor-brake-total:{arm}/{cls}:"
                    f"{donor_brake_total}/{DONOR_BRAKE_TOTALS[cls]}"
                )

    for cls, seq, run in canonical_pair_runs():
        prior: set[int] = set()
        prior_donor_identity: tuple[Any, ...] | None = None
        for arm in BLIND_ARMS:
            row = schedules.get((arm, cls, seq, run), {})
            frames = set(row.get("brake_frames", []))
            if not prior.issubset(frames):
                problems.append(f"schedule:not-nested:{arm}/{cls}/{seq}/{run}")
            prior = frames
            donor_identity = (
                row.get("donor_class"),
                row.get("donor_seq"),
                row.get("donor_run"),
                row.get("donor_frame_count"),
                tuple(row.get("donor_brake_frames", [])),
            )
            if prior_donor_identity is not None and donor_identity != prior_donor_identity:
                problems.append(f"schedule:donor-drift-across-dose:{arm}/{cls}/{seq}/{run}")
            prior_donor_identity = donor_identity
    if raw.get("problem_count") != 0 or raw.get("problems") not in ([], None):
        problems.append("schedule:generator-reported-problems")
    return schedules, problems, raw


def _row_identity(row: Mapping[str, Any], arm: str) -> Cell | None:
    dose = row.get("dose_id", row.get("dose"))
    if dose is not None and str(dose) != arm:
        return None
    cls = row.get("class", row.get("target_class"))
    seq = row.get("seq", row.get("target_seq"))
    pair = row.get("pair")
    if isinstance(pair, str) and "/" in pair:
        pair_cls, pair_seq = pair.split("/", 1)
        cls = cls if cls is not None else pair_cls
        seq = seq if seq is not None else pair_seq
    elif isinstance(pair, str) and seq is None:
        seq = pair
    run = row.get("target_run", row.get("run"))
    try:
        cell = (arm, str(cls), str(seq), int(run))
    except (TypeError, ValueError):
        return None
    return cell if cell in expected_cells([arm]) else None


def _json_rows(paths: Sequence[str | pathlib.Path], label: str) -> Iterator[tuple[int, Mapping[str, Any]]]:
    with open_text_parts(paths) as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise AnalysisInputError(f"{label}:malformed-json:{lineno}:{error}") from error
            if not isinstance(row, dict):
                raise AnalysisInputError(f"{label}:row-not-object:{lineno}")
            yield lineno, row


def parse_blind_decisions(
    arm: str,
    paths: Sequence[str | pathlib.Path],
    schedules: Mapping[Cell, Mapping[str, Any]],
) -> ParsedDecisionLog:
    expected = expected_cells([arm])
    cells: dict[Cell, DecisionCell] = {}
    problems: list[str] = []
    current: Cell | None = None
    brake_rows = release_rows = 0
    for lineno, row in _json_rows(paths, f"decision:{arm}"):
        if row.get("reset") is True:
            current = _row_identity(row, arm)
            if current is None:
                problems.append(f"decision:{arm}:reset-identity:{lineno}")
                continue
            if current in cells:
                problems.append(f"decision:{arm}:duplicate-reset:{cell_id(current)}")
            cells.setdefault(current, DecisionCell())
            continue
        if row.get("intervene_err") is not None or row.get("schedule_missing") is True:
            problems.append(f"decision:{arm}:runtime-error:{lineno}")
        identity = _row_identity(row, arm)
        if identity is not None:
            if current is not None and identity != current:
                problems.append(f"decision:{arm}:identity-switch-without-reset:{lineno}")
            current = identity
        if current is None:
            problems.append(f"decision:{arm}:unbound-row:{lineno}")
            continue
        cell_data = cells.setdefault(current, DecisionCell())
        if row.get("frame") is True:
            try:
                frame = int(row["frame_index"])
            except (KeyError, TypeError, ValueError):
                problems.append(f"decision:{arm}:frame-index:{lineno}")
            else:
                if frame in cell_data.frames:
                    problems.append(f"decision:{arm}:duplicate-frame:{cell_id(current)}:{frame}")
                cell_data.frames.add(frame)
        if row.get("brake") is True:
            brake_rows += 1
            try:
                frame = int(row["frame_index"])
            except (KeyError, TypeError, ValueError):
                problems.append(f"decision:{arm}:brake-index:{lineno}")
            else:
                if frame in cell_data.brakes:
                    problems.append(f"decision:{arm}:duplicate-brake:{cell_id(current)}:{frame}")
                cell_data.brakes.add(frame)
        if row.get("release") is True:
            release_rows += 1
            cell_data.releases += 1

    problems.extend(f"decision:{arm}:{item}" for item in validate_exact_cells(cells, expected))
    for cell in sorted(expected & cells.keys()):
        data = cells[cell]
        frames_sorted = sorted(data.frames)
        if frames_sorted != list(range(len(frames_sorted))):
            problems.append(f"decision:{arm}:noncontiguous-frame-counter:{cell_id(cell)}")
        if not data.brakes.issubset(data.frames):
            problems.append(f"decision:{arm}:brake-without-frame:{cell_id(cell)}")
        scheduled = set(schedules.get(cell, {}).get("brake_frames", []))
        if not data.brakes.issubset(scheduled):
            problems.append(f"decision:{arm}:unscheduled-brake:{cell_id(cell)}")
        expected_realized = scheduled & data.frames
        if data.brakes != expected_realized:
            problems.append(f"decision:{arm}:missed-reachable-schedule:{cell_id(cell)}")
        if data.releases:
            problems.append(f"decision:{arm}:blind-release-row:{cell_id(cell)}")
    return ParsedDecisionLog(cells, problems, brake_rows, release_rows)


def parse_semantic_decisions(
    arm: str, paths: Sequence[str | pathlib.Path]
) -> ParsedDecisionLog:
    """Map current released-patch logs using launcher-authored block identity receipts."""

    if arm not in ("off_baseline", "released_union_semantic_reference"):
        raise AnalysisInputError(f"semantic decision parser received blind arm: {arm}")
    expected = expected_cells([arm])
    expected_pairs = set(canonical_pairs())
    cells: dict[Cell, DecisionCell] = {}
    problems: list[str] = []
    current: Cell | None = None
    block_pair: Pair | None = None
    block_reset_count = 0
    seen_pairs: set[Pair] = set()
    brake_rows = release_rows = 0
    frame_counter = 0
    for lineno, row in _json_rows(paths, f"decision:{arm}"):
        if row.get("block_identity") is True:
            if block_pair is not None and block_reset_count != NRUNS:
                problems.append(
                    f"decision:{arm}:block-reset-count:{block_pair[0]}/{block_pair[1]}:"
                    f"{block_reset_count}/{NRUNS}"
                )
            identity = (str(row.get("class")), str(row.get("pair")))
            if row.get("arm") != arm or identity not in expected_pairs:
                problems.append(f"decision:{arm}:block-identity:{lineno}")
                block_pair = None
                current = None
                block_reset_count = 0
                continue
            if identity in seen_pairs:
                problems.append(f"decision:{arm}:duplicate-block:{identity[0]}/{identity[1]}")
            seen_pairs.add(identity)
            block_pair = identity
            block_reset_count = 0
            current = None
            frame_counter = 0
            continue
        if row.get("reset") is True:
            if block_pair is None:
                problems.append(f"decision:{arm}:reset-without-block-identity:{lineno}")
                current = None
                continue
            run = row.get("run")
            if type(run) is not int or run != block_reset_count or run not in range(NRUNS):
                problems.append(
                    f"decision:{arm}:block-run-order:{block_pair[0]}/{block_pair[1]}:"
                    f"{run!r}!={block_reset_count}"
                )
                current = None
                continue
            current = (arm, block_pair[0], block_pair[1], run)
            block_reset_count += 1
            if current in cells:
                problems.append(f"decision:{arm}:duplicate-reset:{cell_id(current)}")
            cells.setdefault(current, DecisionCell())
            frame_counter = 0
            continue
        if row.get("intervene_err") is not None:
            problems.append(f"decision:{arm}:runtime-error:{lineno}")
        if current is None:
            problems.append(f"decision:{arm}:unbound-row:{lineno}")
            continue
        data = cells[current]
        if "ts" in row and "traj" in row:
            data.frames.add(frame_counter)
            frame_counter += 1
        if row.get("brake") is True:
            brake_rows += 1
            # The released patch logs the decision after the corresponding inference row.
            frame = max(frame_counter - 1, 0)
            if frame in data.brakes:
                problems.append(f"decision:{arm}:duplicate-brake:{cell_id(current)}:{frame}")
            data.brakes.add(frame)
        if row.get("release") is True:
            release_rows += 1
            data.releases += 1
    if block_pair is not None and block_reset_count != NRUNS:
        problems.append(
            f"decision:{arm}:block-reset-count:{block_pair[0]}/{block_pair[1]}:"
            f"{block_reset_count}/{NRUNS}"
        )
    missing_pairs = sorted(expected_pairs - seen_pairs)
    extra_pairs = sorted(seen_pairs - expected_pairs)
    if missing_pairs:
        problems.append(f"decision:{arm}:missing-blocks:{len(missing_pairs)}")
    if extra_pairs:
        problems.append(f"decision:{arm}:extra-blocks:{len(extra_pairs)}")
    problems.extend(f"decision:{arm}:{item}" for item in validate_exact_cells(cells, expected))
    if arm == "off_baseline" and (brake_rows or release_rows):
        problems.append(f"decision:off:actuation:{brake_rows}/{release_rows}")
    return ParsedDecisionLog(cells, problems, brake_rows, release_rows)


def parse_legacy_oracle_semantic_decisions(
    paths: Sequence[str | pathlib.Path],
) -> ParsedDecisionLog:
    """Parse the frozen Iter134 union proof after its exact byte digests are verified."""

    arm = "released_union_semantic_reference"
    canonical = [(arm, cls, seq, run) for cls, seq, run in canonical_pair_runs()]
    cells: dict[Cell, DecisionCell] = {}
    problems: list[str] = []
    current: Cell | None = None
    reset_index = 0
    brake_rows = release_rows = 0
    frame_counter = 0
    for lineno, row in _json_rows(paths, "decision:iter134-oracle-union"):
        if row.get("reset") is True:
            if reset_index >= len(canonical):
                problems.append(f"decision:oracle:extra-reset:{lineno}")
                current = None
                continue
            current = canonical[reset_index]
            reset_index += 1
            cells[current] = DecisionCell()
            frame_counter = 0
            continue
        if row.get("intervene_err") is not None:
            problems.append(f"decision:oracle:runtime-error:{lineno}")
        if current is None:
            problems.append(f"decision:oracle:unbound-row:{lineno}")
            continue
        data = cells[current]
        if "ts" in row and "traj" in row:
            data.frames.add(frame_counter)
            frame_counter += 1
        if row.get("brake") is True:
            brake_rows += 1
            frame = max(frame_counter - 1, 0)
            if frame in data.brakes:
                problems.append(f"decision:oracle:duplicate-brake:{cell_id(current)}:{frame}")
            data.brakes.add(frame)
        if row.get("release") is True:
            release_rows += 1
            data.releases += 1
    problems.extend(f"decision:oracle:{item}" for item in validate_exact_cells(cells, set(canonical)))
    if reset_index != len(canonical):
        problems.append(f"decision:oracle:reset-count:{reset_index}/{len(canonical)}")
    return ParsedDecisionLog(cells, problems, brake_rows, release_rows)


def contiguous_window_count(frames: Iterable[int]) -> int:
    ordered = sorted(set(frames))
    return sum(index == 0 or value != ordered[index - 1] + 1 for index, value in enumerate(ordered))


def aggregate_equal_class(pair_metric: Mapping[Pair, float]) -> float:
    class_means = []
    for cls in CLASSES:
        values = [pair_metric[(cls, seq)] for seq in CLASS_PAIRS[cls]]
        class_means.append(math.fsum(values) / len(values))
    return math.fsum(class_means) / len(class_means)


def make_metric_tables(
    episodes: Mapping[Cell, Episode],
) -> tuple[
    dict[str, dict[Pair, dict[str, float]]],
    dict[str, dict[str, dict[Pair, list[float]]]],
]:
    """Return pair means plus episode values needed by run-index sensitivity."""

    episode_values: dict[str, dict[str, dict[Pair, list[float]]]] = {
        arm: {metric: {} for metric in ("ncap", "impact_speed", "q16_distance", "raw_path_length")}
        for arm in ARMS
    }
    for arm in ARMS:
        for pair in canonical_pairs():
            cls, seq = pair
            rows = [episodes[(arm, cls, seq, run)] for run in range(NRUNS)]
            for metric in episode_values[arm]:
                episode_values[arm][metric][pair] = [getattr(row, metric) for row in rows]

    off_q16 = {
        pair: math.fsum(episode_values["off_baseline"]["q16_distance"][pair]) / NRUNS
        for pair in canonical_pairs()
    }
    off_full = {
        pair: math.fsum(episode_values["off_baseline"]["raw_path_length"][pair]) / NRUNS
        for pair in canonical_pairs()
    }
    pair_tables: dict[str, dict[Pair, dict[str, float]]] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        for pair in canonical_pairs():
            rows = [episodes[(arm, pair[0], pair[1], run)] for run in range(NRUNS)]
            q_base = off_q16[pair]
            full_base = off_full[pair]
            if q_base <= 0 or full_base <= 0:
                raise AnalysisInputError(f"fresh OFF denominator is nonpositive for {pair[0]}/{pair[1]}")
            pair_tables[arm][pair] = {
                "ncap": math.fsum(row.ncap for row in rows) / NRUNS,
                "impact_speed": math.fsum(row.impact_speed for row in rows) / NRUNS,
                "q16": math.fsum(min(1.0, row.q16_distance / q_base) for row in rows) / NRUNS,
                "raw_path_length": math.fsum(row.raw_path_length for row in rows) / NRUNS,
                "legacy_safe_progress": math.fsum(
                    row.ncap * min(1.0, row.raw_path_length / full_base) for row in rows
                )
                / NRUNS,
                "collision_rate": sum(row.collision for row in rows) / NRUNS,
            }
    return pair_tables, episode_values


def arm_summaries(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]]
) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for arm in ARMS:
        by_pair = {
            f"{cls}/{seq}": dict(pair_tables[arm][(cls, seq)]) for cls, seq in canonical_pairs()
        }
        by_class: dict[str, dict[str, float]] = {}
        for cls in CLASSES:
            by_class[cls] = {}
            for metric in pair_tables[arm][(cls, CLASS_PAIRS[cls][0])]:
                values = [pair_tables[arm][(cls, seq)][metric] for seq in CLASS_PAIRS[cls]]
                by_class[cls][metric] = math.fsum(values) / len(values)
        aggregate = {
            metric: math.fsum(by_class[cls][metric] for cls in CLASSES) / len(CLASSES)
            for metric in next(iter(by_class.values()))
        }
        summaries[arm] = {
            "episodes": len(canonical_pair_runs()),
            "aggregate_equal_class": aggregate,
            "by_class": by_class,
            "by_pair": by_pair,
        }
    return summaries


def class_stratified_draws(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]],
    draws: int = BOOT_DRAWS,
    seed: int = BOOT_SEED,
) -> dict[str, list[float]]:
    """Joint paired 10/5/5 bootstrap for all eight frozen frontier contrasts."""

    contrast_names = [f"{arm}:{metric}" for arm in BLIND_ARMS for metric in ("ncap", "q16")]
    out = {name: [] for name in contrast_names}
    rng = random.Random(seed)
    union = "released_union_semantic_reference"
    for _ in range(draws):
        selected = {
            cls: [rng.randrange(len(CLASS_PAIRS[cls])) for _ in CLASS_PAIRS[cls]]
            for cls in CLASSES
        }
        for blind in BLIND_ARMS:
            for metric in ("ncap", "q16"):
                class_deltas = []
                for cls in CLASSES:
                    deltas = [
                        pair_tables[union][(cls, CLASS_PAIRS[cls][index])][metric]
                        - pair_tables[blind][(cls, CLASS_PAIRS[cls][index])][metric]
                        for index in selected[cls]
                    ]
                    class_deltas.append(math.fsum(deltas) / len(deltas))
                out[f"{blind}:{metric}"].append(math.fsum(class_deltas) / len(CLASSES))
    return out


def frozen_bounds(draws: Sequence[float]) -> Bounds:
    if len(draws) != BOOT_DRAWS:
        raise AnalysisInputError(f"frozen inference requires {BOOT_DRAWS} draws, got {len(draws)}")
    ordered = sorted(draws)
    return Bounds(
        lcb95=ordered[LCB_INDEX],
        ucb95=ordered[UCB_INDEX],
        ci95=(ordered[CI_LO_INDEX], ordered[CI_HI_INDEX]),
    )


def simultaneous_max_t(
    points: Mapping[str, float], draw_family: Mapping[str, Sequence[float]]
) -> tuple[float, dict[str, dict[str, float | list[float] | bool]]]:
    """Frozen max-|T| family, including exact handling of zero bootstrap SE."""

    if set(points) != set(draw_family):
        missing = sorted(set(points) - set(draw_family))
        extra = sorted(set(draw_family) - set(points))
        raise AnalysisInputError(f"max-T contrast family mismatch: missing={missing}, extra={extra}")
    ses: dict[str, float] = {}
    for name, values in draw_family.items():
        if len(values) != BOOT_DRAWS:
            raise AnalysisInputError(f"max-T {name} has {len(values)} draws, expected {BOOT_DRAWS}")
        # Explicit range test makes a mathematically constant contrast exactly zero-SE even when
        # statistics.stdev would accumulate harmless floating roundoff.
        ses[name] = 0.0 if min(values) == max(values) else statistics.stdev(values)
    active = [name for name, se in ses.items() if se != 0.0]
    maxima: list[float] = []
    if active:
        for index in range(BOOT_DRAWS):
            maxima.append(
                max(abs((draw_family[name][index] - points[name]) / ses[name]) for name in active)
            )
        critical = sorted(maxima)[MAX_T_INDEX]
    else:
        critical = 0.0
    intervals: dict[str, dict[str, float | list[float] | bool]] = {}
    for name, point in points.items():
        se = ses[name]
        lower = point if se == 0.0 else point - critical * se
        upper = point if se == 0.0 else point + critical * se
        intervals[name] = {
            "point": point,
            "se": se,
            "zero_se": se == 0.0,
            "simultaneous_ci95": [lower, upper],
        }
    return critical, intervals


def contrast_points(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]]
) -> dict[str, float]:
    union = "released_union_semantic_reference"
    out: dict[str, float] = {}
    for blind in BLIND_ARMS:
        for metric in ("ncap", "q16"):
            pair_delta = {
                pair: pair_tables[union][pair][metric] - pair_tables[blind][pair][metric]
                for pair in canonical_pairs()
            }
            out[f"{blind}:{metric}"] = aggregate_equal_class(pair_delta)
    return out


def primary_and_frontier(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]],
    draws: Mapping[str, Sequence[float]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    points = contrast_points(pair_tables)
    n_name = "blind_1_0x:ncap"
    q_name = "blind_1_0x:q16"
    n_bounds = frozen_bounds(draws[n_name])
    q_bounds = frozen_bounds(draws[q_name])
    primary = {
        "contrast": "released_union_semantic_reference-minus-blind_1_0x",
        "delta_ncap": points[n_name],
        "ncap_bounds": dataclasses.asdict(n_bounds),
        "delta_q16": points[q_name],
        "q16_bounds": dataclasses.asdict(q_bounds),
        "ncap_superiority_gate": points[n_name] >= 0.25 and n_bounds.lcb95 > 0.0,
        "q16_noninferiority_gate": q_bounds.lcb95 > -0.05,
        "blind_primary_competitive": n_bounds.ucb95 < 0.25 and q_bounds.ucb95 < 0.05,
    }
    primary["confirmatory_gate"] = (
        primary["ncap_superiority_gate"] and primary["q16_noninferiority_gate"]
    )
    primary["blind_primary_reverse_dominance"] = primary["blind_primary_competitive"] and (
        (points[n_name] <= -0.25 and n_bounds.ucb95 < 0.0)
        or (points[q_name] <= -0.05 and q_bounds.ucb95 < 0.0)
    )

    critical, intervals = simultaneous_max_t(points, draws)
    dose_rows: dict[str, Any] = {}
    for blind in BLIND_ARMS:
        n = intervals[f"{blind}:ncap"]
        q = intervals[f"{blind}:q16"]
        n_lower, n_upper = n["simultaneous_ci95"]
        q_lower, q_upper = q["simultaneous_ci95"]
        competitive = n_upper < 0.25 and q_upper < 0.05
        dominates = competitive and (
            (n["point"] <= -0.25 and n_upper < 0.0)
            or (q["point"] <= -0.05 and q_upper < 0.0)
        )
        dose_rows[blind] = {
            "union_minus_blind_ncap": n,
            "union_minus_blind_q16": q,
            "competitive": competitive,
            "pareto_dominates": dominates,
        }
    frontier = {
        "method": "paired_class_stratified_simultaneous_two_sided_95_max_abs_t",
        "critical_value": critical,
        "doses": dose_rows,
    }
    return primary, frontier


def decide_verdict(
    infrastructure_valid: bool,
    primary: Mapping[str, Any],
    frontier: Mapping[str, Any],
) -> tuple[str, str | None]:
    dose_rows = frontier.get("doses", {})
    any_dominates = any(row.get("pareto_dominates") is True for row in dose_rows.values())
    any_competitive = any(row.get("competitive") is True for row in dose_rows.values())
    if not infrastructure_valid:
        return "PLACEBO_DOSE_INFRA_NULL", None
    if primary.get("blind_primary_reverse_dominance") is True or any_dominates:
        verdict = "GENERIC_BRAKING_DOMINATES"
    elif primary.get("confirmatory_gate") is True:
        verdict = "SEMANTIC_MATCHED_BUDGET_CONFIRMED"
    elif primary.get("blind_primary_competitive") is True:
        verdict = "BLIND_MATCHED_BUDGET_COMPETITIVE"
    else:
        verdict = "MATCHED_BUDGET_INCONCLUSIVE"
    if any_dominates:
        qualifier = "BLIND_FRONTIER_DOMINATES"
    elif any_competitive:
        qualifier = "BLIND_FRONTIER_COMPETITIVE"
    else:
        qualifier = "NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED"
    return verdict, qualifier


def drift_gate(
    fresh_scores: Mapping[Cell, ScoreRow],
    fresh_artifacts: Mapping[Cell, RunArtifact],
    oracle_scores: Mapping[Cell, ScoreRow],
    oracle_artifacts: Mapping[Cell, RunArtifact],
    fresh_union_decisions: ParsedDecisionLog,
    oracle_union_decisions: ParsedDecisionLog,
) -> tuple[bool, list[str]]:
    problems: list[str] = []
    arms = ("off_baseline", "released_union_semantic_reference")
    for cell in sorted(expected_cells(arms)):
        fresh = fresh_scores.get(cell)
        oracle = oracle_scores.get(cell)
        if fresh is None or oracle is None:
            problems.append(f"g6:score-cell-missing:{cell_id(cell)}")
            continue
        if fresh.ncap != oracle.ncap or fresh.impact_speed != oracle.impact_speed:
            problems.append(
                f"g6:score-drift:{cell_id(cell)}:{fresh.ncap}/{fresh.impact_speed}!="
                f"{oracle.ncap}/{oracle.impact_speed}"
            )
        fresh_artifact = fresh_artifacts.get(cell)
        oracle_artifact = oracle_artifacts.get(cell)
        if fresh_artifact is None or oracle_artifact is None:
            problems.append(f"g6:run-cell-missing:{cell_id(cell)}")
            continue
        difference = abs(q16_distance(fresh_artifact.ego_poses) - q16_distance(oracle_artifact.ego_poses))
        if difference > 1e-6:
            problems.append(f"g6:q16-drift:{cell_id(cell)}:{difference}")
    if fresh_union_decisions.brake_rows != EXPECTED_UNION_BRAKES:
        problems.append(
            f"g6:fresh-union-brakes:{fresh_union_decisions.brake_rows}/{EXPECTED_UNION_BRAKES}"
        )
    if fresh_union_decisions.release_rows != EXPECTED_UNION_RELEASES:
        problems.append(
            f"g6:fresh-union-releases:{fresh_union_decisions.release_rows}/{EXPECTED_UNION_RELEASES}"
        )
    if oracle_union_decisions.brake_rows != EXPECTED_UNION_BRAKES:
        problems.append(
            f"g6:oracle-union-brakes:{oracle_union_decisions.brake_rows}/{EXPECTED_UNION_BRAKES}"
        )
    if oracle_union_decisions.release_rows != EXPECTED_UNION_RELEASES:
        problems.append(
            f"g6:oracle-union-releases:{oracle_union_decisions.release_rows}/{EXPECTED_UNION_RELEASES}"
        )
    return not problems, problems


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dataset_file_problems(
    receipt: Any,
    *,
    label: str,
    expected_path: str,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> list[str]:
    problems: list[str] = []
    if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256", "bytes"}:
        return [f"manifest:dataset:{label}:field-set"]
    if receipt.get("path") != expected_path:
        problems.append(f"manifest:dataset:{label}:path")
    digest = receipt.get("sha256")
    byte_count = receipt.get("bytes")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        problems.append(f"manifest:dataset:{label}:sha256")
    if type(byte_count) is not int or byte_count <= 0:
        problems.append(f"manifest:dataset:{label}:bytes")
    if expected_sha256 is not None and digest != expected_sha256:
        problems.append(f"manifest:dataset:{label}:expected-sha256")
    if expected_bytes is not None and byte_count != expected_bytes:
        problems.append(f"manifest:dataset:{label}:expected-bytes")
    return problems


def validate_manifest_dataset(
    manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Validate dataset provenance separately from analytic-completion G7."""

    problems: list[str] = []
    dataset = manifest.get("dataset_receipt")
    environment = manifest.get("environment_receipts")
    if not isinstance(environment, dict) or environment.get("schema") != ENVIRONMENT_SCHEMA:
        problems.append("manifest:environment-receipts-v2")
        environment = {}
    if not isinstance(dataset, dict):
        problems.append("manifest:dataset:missing")
        dataset = {}
    if environment.get("dataset") != dataset:
        problems.append("manifest:dataset-environment-mismatch")
    expected_fields = {
        "schema",
        "contract_sha256",
        "proof_basis",
        "identity",
        "archives",
        "metadata_json",
        "map_anchors",
        "receipt_payload_sha256",
    }
    if set(dataset) != expected_fields:
        problems.append("manifest:dataset:field-set")
    if dataset.get("schema") != DATASET_SCHEMA:
        problems.append("manifest:dataset:schema")
    if dataset.get("contract_sha256") != EXPECTED_DATASET_CONTRACT_SHA256:
        problems.append("manifest:dataset:contract-sha256")
    if dataset.get("proof_basis") != EXPECTED_DATASET_PROOF_BASIS:
        problems.append("manifest:dataset:proof-basis")

    identity = dataset.get("identity")
    expected_identity_fields = {
        "dataset_root",
        "dataset_realpath",
        "dataset_is_symlink",
        "dataset_version",
        "archive_root",
        "archive_realpath",
        "archive_is_symlink",
        "metadata_root",
        "metadata_realpath",
        "metadata_is_symlink",
        "map_root",
        "map_realpath",
        "map_is_symlink",
        "mount_target",
        "mount_source",
        "mount_fstype",
        "mount_uuid",
        "dataset_st_dev",
        "mount_st_dev",
        "root_st_dev",
    }
    if not isinstance(identity, dict) or set(identity) != expected_identity_fields:
        problems.append("manifest:dataset:identity-field-set")
        identity = {}
    expected_identity = {
        "dataset_root": EXPECTED_DATASET_ROOT,
        "dataset_realpath": EXPECTED_DATASET_ROOT,
        "dataset_is_symlink": False,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "archive_root": EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_realpath": EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_is_symlink": False,
        "metadata_root": EXPECTED_DATASET_METADATA_ROOT,
        "metadata_realpath": EXPECTED_DATASET_METADATA_ROOT,
        "metadata_is_symlink": False,
        "map_root": EXPECTED_DATASET_MAP_ROOT,
        "map_realpath": EXPECTED_DATASET_MAP_ROOT,
        "map_is_symlink": False,
        **EXPECTED_DATASET_MOUNT,
    }
    for field, expected in expected_identity.items():
        actual = identity.get(field)
        if actual != expected or (isinstance(expected, bool) and type(actual) is not bool):
            problems.append(f"manifest:dataset:identity:{field}")
    dataset_device = identity.get("dataset_st_dev")
    mount_device = identity.get("mount_st_dev")
    root_device = identity.get("root_st_dev")
    devices = (dataset_device, mount_device, root_device)
    if any(type(value) is not int for value in devices):
        problems.append("manifest:dataset:device-identity")
    elif min(devices) < 0 or dataset_device != mount_device or dataset_device == root_device:
        problems.append("manifest:dataset:device-identity")

    archives = dataset.get("archives")
    if not isinstance(archives, dict) or set(archives) != set(EXPECTED_DATASET_ARCHIVES):
        problems.append("manifest:dataset:archive-set")
        archives = archives if isinstance(archives, dict) else {}
    for name, (digest, byte_count) in EXPECTED_DATASET_ARCHIVES.items():
        problems.extend(
            _dataset_file_problems(
                archives.get(name),
                label=f"archive:{name}",
                expected_path=f"{EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
                expected_sha256=digest,
                expected_bytes=byte_count,
            )
        )

    metadata = dataset.get("metadata_json")
    if not isinstance(metadata, dict) or set(metadata) != set(EXPECTED_DATASET_METADATA_FILES):
        problems.append("manifest:dataset:metadata-set")
        metadata = metadata if isinstance(metadata, dict) else {}
    for name in EXPECTED_DATASET_METADATA_FILES:
        problems.extend(
            _dataset_file_problems(
                metadata.get(name),
                label=f"metadata:{name}",
                expected_path=f"{EXPECTED_DATASET_METADATA_ROOT}/{name}",
            )
        )

    maps = dataset.get("map_anchors")
    if not isinstance(maps, dict) or set(maps) != set(EXPECTED_DATASET_MAP_ANCHORS):
        problems.append("manifest:dataset:map-set")
        maps = maps if isinstance(maps, dict) else {}
    for name in EXPECTED_DATASET_MAP_ANCHORS:
        problems.extend(
            _dataset_file_problems(
                maps.get(name),
                label=f"map:{name}",
                expected_path=f"{EXPECTED_DATASET_MAP_ROOT}/{name}",
            )
        )

    receipt_payload_sha256 = dataset.get("receipt_payload_sha256")
    digest_payload = dict(dataset)
    digest_payload.pop("receipt_payload_sha256", None)
    if (
        not isinstance(receipt_payload_sha256, str)
        or _SHA256_RE.fullmatch(receipt_payload_sha256) is None
        or receipt_payload_sha256 != _canonical_json_sha256(digest_payload)
    ):
        problems.append("manifest:dataset:receipt-payload-sha256")

    bound_files = manifest.get("hash_bound_files")
    environment_binding = (
        bound_files.get("env_receipts.json") if isinstance(bound_files, dict) else None
    )
    if (
        not isinstance(environment_binding, dict)
        or set(environment_binding) != {"source_path", "sha256", "bytes"}
        or environment_binding.get("source_path") != "env_receipts.json"
        or not isinstance(environment_binding.get("sha256"), str)
        or _SHA256_RE.fullmatch(environment_binding["sha256"]) is None
        or type(environment_binding.get("bytes")) is not int
        or environment_binding["bytes"] <= 0
    ):
        problems.append("manifest:environment-receipt-binding")
        environment_sha256 = None
    else:
        environment_sha256 = environment_binding["sha256"]
    return (
        {
            "environment_schema": ENVIRONMENT_SCHEMA,
            "environment_receipt_sha256": environment_sha256,
            "dataset_schema": DATASET_SCHEMA,
            "dataset_contract_sha256": EXPECTED_DATASET_CONTRACT_SHA256,
            "dataset_receipt_payload_sha256": receipt_payload_sha256,
            "dataset_file_count": (
                len(EXPECTED_DATASET_ARCHIVES)
                + len(EXPECTED_DATASET_METADATA_FILES)
                + len(EXPECTED_DATASET_MAP_ANCHORS)
            ),
        },
        sorted(set(problems)),
    )


def _strict_runtime_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite constant {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for key, value in pairs:
            if key in row:
                raise ValueError(f"duplicate key {key}")
            row[key] = value
        return row

    try:
        value = json.loads(
            payload,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise AnalysisInputError(f"runtime-evidence:{label}:malformed-json:{error}") from error
    if not isinstance(value, dict):
        raise AnalysisInputError(f"runtime-evidence:{label}:object-required")
    return value


def _canonical_runtime_snapshot(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _runtime_integer(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise AnalysisInputError(f"runtime-evidence:{label}:integer")
    return value


def _runtime_tokens(line: str, prefix: str, fields: set[str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for token in line.removeprefix(prefix).split():
        key, separator, value = token.partition("=")
        if not separator or not key or not value or key in row:
            raise AnalysisInputError(f"runtime-log:malformed-token:{prefix.strip()}:{token}")
        row[key] = value
    if set(row) != fields:
        raise AnalysisInputError(f"runtime-log:field-set:{prefix.strip()}")
    return row


def runtime_log_facts(payload: bytes) -> dict[str, Any]:
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise AnalysisInputError(f"runtime-log:not-utf8:{error}") from error
    prefixes = {
        "invocation": (
            "I135_INVOCATION_START ",
            {"at", "pid", "manifest_sha256"},
        ),
        "snapshot": (
            "I135_RUNTIME_SNAPSHOT_OK ",
            {"manifest_sha256", "path"},
        ),
        "dataset": (
            "I135_DATASET_SNAPSHOT_OK ",
            {"sha256", "id", "files"},
        ),
        "docker": (
            "I135_DOCKER_SNAPSHOT_OK ",
            {"sha256", "id"},
        ),
        "armed": (
            "I135_ANALYTIC_ARMED ",
            {"lock", "lock_id", "output_root"},
        ),
    }
    rows: dict[str, list[dict[str, str]]] = {name: [] for name in prefixes}
    dataset_runtime: list[dict[str, str]] = []
    docker_runtime: list[dict[str, str]] = []
    done_rows: list[dict[str, str]] = []
    for line in lines:
        for name, (prefix, fields) in prefixes.items():
            if line.startswith(prefix):
                rows[name].append(_runtime_tokens(line, prefix, fields))
        if line.startswith("I135_DATASET_RUNTIME_OK "):
            dataset_runtime.append(
                _runtime_tokens(
                    line,
                    "I135_DATASET_RUNTIME_OK ",
                    {"phase", "files"},
                )
            )
        if line.startswith("I135_DOCKER_RUNTIME_OK "):
            docker_runtime.append(
                _runtime_tokens(
                    line,
                    "I135_DOCKER_RUNTIME_OK ",
                    {"phase", "daemon_id"},
                )
            )
        if line.startswith("I135_DONE_METADATA "):
            done_rows.append(
                _runtime_tokens(
                    line,
                    "I135_DONE_METADATA ",
                    {
                        "at",
                        "manifest_sha256",
                        "runtime_snapshot",
                        "dataset_runtime_snapshot_sha256",
                        "dataset_runtime_snapshot_id",
                        "docker_runtime_snapshot_sha256",
                        "docker_runtime_snapshot_id",
                        "launch_lock_retained",
                        "launch_lock_id",
                        "elapsed_seconds",
                        "prior_smoke_gpu_seconds",
                        "blocks",
                        "episodes",
                        "output_root",
                        "output_device",
                        "output_uuid",
                        "start_free_bytes",
                        "end_free_bytes",
                        "output_bytes",
                    },
                )
            )
    if any(len(value) != 1 for value in rows.values()) or len(done_rows) != 1:
        raise AnalysisInputError("runtime-log:marker-count")
    if not lines or lines[-1] != DONE_MARKER:
        raise AnalysisInputError("runtime-log:terminal-done-marker")
    invocation = rows["invocation"][0]
    snapshot = rows["snapshot"][0]
    dataset = rows["dataset"][0]
    docker = rows["docker"][0]
    armed = rows["armed"][0]
    done = done_rows[0]
    try:
        invocation_pid = int(invocation["pid"])
    except ValueError as error:
        raise AnalysisInputError("runtime-log:invocation-pid") from error
    if invocation_pid <= 0:
        raise AnalysisInputError("runtime-log:invocation-pid")
    if (
        _SHA256_RE.fullmatch(dataset["sha256"]) is None
        or _SHA256_RE.fullmatch(docker["sha256"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", dataset["id"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", docker["id"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", armed["lock_id"]) is None
        or dataset["files"] != "28"
    ):
        raise AnalysisInputError("runtime-log:snapshot-receipt")
    manifest_sha = invocation["manifest_sha256"]
    expected_runtime = f"/var/lib/sentinel/i135-runtime-{manifest_sha}"
    if snapshot != {"manifest_sha256": manifest_sha, "path": expected_runtime}:
        raise AnalysisInputError("runtime-log:snapshot-identity")
    if armed != {
        "lock": "/var/lib/sentinel/i135-analytic.lock",
        "lock_id": armed["lock_id"],
        "output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    }:
        raise AnalysisInputError("runtime-log:analytic-armed")
    expected_done = {
        "manifest_sha256": manifest_sha,
        "runtime_snapshot": expected_runtime,
        "dataset_runtime_snapshot_sha256": dataset["sha256"],
        "dataset_runtime_snapshot_id": dataset["id"],
        "docker_runtime_snapshot_sha256": docker["sha256"],
        "docker_runtime_snapshot_id": docker["id"],
        "launch_lock_retained": "/var/lib/sentinel/i135-analytic.lock",
        "launch_lock_id": armed["lock_id"],
        "output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
        "output_device": "/dev/nvme0n2",
        "output_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
    }
    for field, expected in expected_done.items():
        if done[field] != expected:
            raise AnalysisInputError(f"runtime-log:done-{field}")
    expected_phase_counts = {
        "analytic-arm": 1,
        "before": 120,
        "after": 120,
        "before-done": 1,
    }
    dataset_counts = dict(collections.Counter(row["phase"] for row in dataset_runtime))
    docker_counts = dict(collections.Counter(row["phase"] for row in docker_runtime))
    docker_daemon_ids = {row["daemon_id"] for row in docker_runtime}
    if dataset_counts != expected_phase_counts or any(
        row["files"] != "28" for row in dataset_runtime
    ):
        raise AnalysisInputError(f"runtime-log:dataset-check-counts:{dataset_counts}")
    if (
        docker_counts != expected_phase_counts
        or len(docker_daemon_ids) != 1
        or not next(iter(docker_daemon_ids), "")
    ):
        raise AnalysisInputError(f"runtime-log:docker-check-counts:{docker_counts}")
    return {
        "manifest_sha256": manifest_sha,
        "runtime_snapshot": expected_runtime,
        "dataset_runtime_snapshot_sha256": dataset["sha256"],
        "dataset_runtime_snapshot_id": dataset["id"],
        "docker_runtime_snapshot_sha256": docker["sha256"],
        "docker_runtime_snapshot_id": docker["id"],
        "launch_lock_retained": expected_done["launch_lock_retained"],
        "launch_lock_id": armed["lock_id"],
        "invocation_pid": invocation_pid,
        "dataset_runtime_check_counts": expected_phase_counts,
        "docker_runtime_check_counts": expected_phase_counts,
        "docker_runtime_daemon_id": next(iter(docker_daemon_ids)),
    }


def _dataset_runtime_facts(
    payload: bytes,
    *,
    manifest: Mapping[str, Any],
    manifest_sha: str,
    log_facts: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _strict_runtime_json(payload, "dataset-runtime-snapshot")
    if set(snapshot) != {
        "schema",
        "manifest_sha256",
        "dataset_receipt_payload_sha256",
        "dataset_root",
        "files",
    } or payload != _canonical_runtime_snapshot(snapshot):
        raise AnalysisInputError("runtime-evidence:dataset:shape-or-canonical-json")
    digest = hashlib.sha256(payload).hexdigest()
    dataset = manifest.get("dataset_receipt")
    if not isinstance(dataset, dict):
        raise AnalysisInputError("runtime-evidence:dataset:manifest-receipt")
    if (
        snapshot.get("schema") != DATASET_RUNTIME_SCHEMA
        or snapshot.get("manifest_sha256") != manifest_sha
        or snapshot.get("dataset_receipt_payload_sha256")
        != dataset.get("receipt_payload_sha256")
        or digest != log_facts.get("dataset_runtime_snapshot_sha256")
    ):
        raise AnalysisInputError("runtime-evidence:dataset:binding")
    root = snapshot.get("dataset_root")
    root_fields = {"path", "st_dev", "st_ino", "st_mode", "st_mtime_ns", "st_ctime_ns"}
    if not isinstance(root, dict) or set(root) != root_fields:
        raise AnalysisInputError("runtime-evidence:dataset:root-fields")
    identity = dataset.get("identity")
    if (
        not isinstance(identity, dict)
        or root.get("path") != EXPECTED_DATASET_ROOT
        or root.get("st_dev") != identity.get("dataset_st_dev")
    ):
        raise AnalysisInputError("runtime-evidence:dataset:root-identity")
    for field in ("st_ino", "st_mode"):
        _runtime_integer(root.get(field), f"dataset:root-{field}", positive=True)
    for field in ("st_mtime_ns", "st_ctime_ns"):
        _runtime_integer(root.get(field), f"dataset:root-{field}")
    if root["st_mode"] > 0o7777:
        raise AnalysisInputError("runtime-evidence:dataset:root-mode")
    expected_files = {
        **{f"archive:{name}": row for name, row in dataset["archives"].items()},
        **{f"metadata:{name}": row for name, row in dataset["metadata_json"].items()},
        **{f"map:{name}": row for name, row in dataset["map_anchors"].items()},
    }
    files = snapshot.get("files")
    file_fields = {
        "path",
        "sha256",
        "bytes",
        "st_dev",
        "st_ino",
        "st_mode",
        "st_mtime_ns",
        "st_ctime_ns",
    }
    if not isinstance(files, dict) or set(files) != set(expected_files):
        raise AnalysisInputError("runtime-evidence:dataset:file-set")
    for label, expected in expected_files.items():
        row = files[label]
        if not isinstance(row, dict) or set(row) != file_fields:
            raise AnalysisInputError(f"runtime-evidence:dataset:file-fields:{label}")
        if any(row.get(field) != expected.get(field) for field in ("path", "sha256", "bytes")):
            raise AnalysisInputError(f"runtime-evidence:dataset:file-receipt:{label}")
        if row.get("st_dev") != identity["dataset_st_dev"]:
            raise AnalysisInputError(f"runtime-evidence:dataset:file-device:{label}")
        for field in ("st_ino", "st_mode"):
            _runtime_integer(row.get(field), f"dataset:file-{field}:{label}", positive=True)
        for field in ("st_mtime_ns", "st_ctime_ns"):
            _runtime_integer(row.get(field), f"dataset:file-{field}:{label}")
        if row["st_mode"] > 0o7777:
            raise AnalysisInputError(f"runtime-evidence:dataset:file-mode:{label}")
    return {
        "source_path": f"{log_facts['runtime_snapshot']}/dataset_runtime_snapshot.json",
        "source_id": log_facts["dataset_runtime_snapshot_id"],
        "schema": DATASET_RUNTIME_SCHEMA,
        "sha256": digest,
        "bytes": len(payload),
        "manifest_sha256": manifest_sha,
        "dataset_receipt_payload_sha256": dataset["receipt_payload_sha256"],
        "file_count": len(expected_files),
    }


def _docker_runtime_facts(
    payload: bytes,
    *,
    manifest_sha: str,
    log_facts: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _strict_runtime_json(payload, "docker-runtime-snapshot")
    fields = {
        "schema",
        "manifest_sha256",
        "client",
        "context",
        "endpoint",
        "socket",
        "daemon_info",
        "daemon_version",
    }
    if set(snapshot) != fields or payload != _canonical_runtime_snapshot(snapshot):
        raise AnalysisInputError("runtime-evidence:docker:shape-or-canonical-json")
    digest = hashlib.sha256(payload).hexdigest()
    if (
        snapshot.get("schema") != DOCKER_RUNTIME_SCHEMA
        or snapshot.get("manifest_sha256") != manifest_sha
        or snapshot.get("context") != "default"
        or snapshot.get("endpoint") != "unix:///var/run/docker.sock"
        or digest != log_facts.get("docker_runtime_snapshot_sha256")
    ):
        raise AnalysisInputError("runtime-evidence:docker:binding")
    client = snapshot.get("client")
    if not isinstance(client, dict) or set(client) != {"path", "sha256", "st_dev", "st_ino"}:
        raise AnalysisInputError("runtime-evidence:docker:client-fields")
    if (
        not isinstance(client.get("path"), str)
        or not pathlib.Path(client["path"]).is_absolute()
        or not isinstance(client.get("sha256"), str)
        or _SHA256_RE.fullmatch(client["sha256"]) is None
    ):
        raise AnalysisInputError("runtime-evidence:docker:client-binding")
    _runtime_integer(client.get("st_dev"), "docker:client-st-dev")
    _runtime_integer(client.get("st_ino"), "docker:client-st-ino", positive=True)
    socket = snapshot.get("socket")
    socket_fields = {
        "declared_path",
        "realpath",
        "st_dev",
        "st_ino",
        "st_mode",
        "st_uid",
        "st_gid",
    }
    if not isinstance(socket, dict) or set(socket) != socket_fields:
        raise AnalysisInputError("runtime-evidence:docker:socket-fields")
    if (
        socket.get("declared_path") != "/var/run/docker.sock"
        or not isinstance(socket.get("realpath"), str)
        or not pathlib.Path(socket["realpath"]).is_absolute()
    ):
        raise AnalysisInputError("runtime-evidence:docker:socket-path")
    for field in ("st_dev", "st_uid", "st_gid"):
        _runtime_integer(socket.get(field), f"docker:socket-{field}")
    for field in ("st_ino", "st_mode"):
        _runtime_integer(socket.get(field), f"docker:socket-{field}", positive=True)
    if socket["st_mode"] > 0o7777:
        raise AnalysisInputError("runtime-evidence:docker:socket-mode")
    info = snapshot.get("daemon_info")
    if not isinstance(info, dict) or set(info) != set(DOCKER_DAEMON_INFO_FIELDS):
        raise AnalysisInputError("runtime-evidence:docker:daemon-info-fields")
    for field in DOCKER_DAEMON_INFO_FIELDS:
        value = info[field]
        if field in {"NCPU", "MemTotal"}:
            _runtime_integer(value, f"docker:daemon-info-{field}", positive=True)
        elif not isinstance(value, str) or not value:
            raise AnalysisInputError(f"runtime-evidence:docker:daemon-info-{field}")
    if not pathlib.Path(info["DockerRootDir"]).is_absolute():
        raise AnalysisInputError("runtime-evidence:docker:daemon-root")
    if info["ID"] != log_facts.get("docker_runtime_daemon_id"):
        raise AnalysisInputError("runtime-evidence:docker:daemon-id-log-binding")
    version = snapshot.get("daemon_version")
    if not isinstance(version, dict) or set(version) != set(DOCKER_DAEMON_VERSION_FIELDS):
        raise AnalysisInputError("runtime-evidence:docker:daemon-version-fields")
    platform = version.get("Platform")
    if not isinstance(platform, dict) or set(platform) != {"Name"} or not platform["Name"]:
        raise AnalysisInputError("runtime-evidence:docker:daemon-platform")
    for field in set(DOCKER_DAEMON_VERSION_FIELDS) - {"Platform", "Experimental"}:
        if not isinstance(version[field], str) or not version[field]:
            raise AnalysisInputError(f"runtime-evidence:docker:daemon-version-{field}")
    if type(version.get("Experimental")) is not bool:
        raise AnalysisInputError("runtime-evidence:docker:daemon-experimental")
    return {
        "source_path": f"{log_facts['runtime_snapshot']}/docker_runtime_snapshot.json",
        "source_id": log_facts["docker_runtime_snapshot_id"],
        "schema": DOCKER_RUNTIME_SCHEMA,
        "sha256": digest,
        "bytes": len(payload),
        "manifest_sha256": manifest_sha,
        "client_path": client["path"],
        "client_sha256": client["sha256"],
        "context": "default",
        "endpoint": "unix:///var/run/docker.sock",
        "daemon_id": info["ID"],
        "server_version": info["ServerVersion"],
    }


def _analytic_lock_facts(
    payload: bytes,
    *,
    manifest_sha: str,
    log_facts: Mapping[str, Any],
) -> dict[str, Any]:
    lock = _strict_runtime_json(payload, "analytic-lock")
    if set(lock) != {
        "schema",
        "manifest_sha256",
        "dataset_runtime_snapshot_sha256",
        "docker_runtime_snapshot_sha256",
        "pid",
        "created_at_utc",
    } or payload != (json.dumps(lock, sort_keys=True) + "\n").encode("utf-8"):
        raise AnalysisInputError("runtime-evidence:analytic-lock:shape-or-canonical-json")
    expected = {
        "schema": ANALYTIC_LOCK_SCHEMA,
        "manifest_sha256": manifest_sha,
        "dataset_runtime_snapshot_sha256": log_facts[
            "dataset_runtime_snapshot_sha256"
        ],
        "docker_runtime_snapshot_sha256": log_facts["docker_runtime_snapshot_sha256"],
        "pid": log_facts["invocation_pid"],
    }
    if any(lock.get(field) != value for field, value in expected.items()):
        raise AnalysisInputError("runtime-evidence:analytic-lock:binding")
    created_at = lock.get("created_at_utc")
    if (
        not isinstance(created_at, str)
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", created_at)
        is None
    ):
        raise AnalysisInputError("runtime-evidence:analytic-lock:created-at")
    return {
        "source_path": log_facts["launch_lock_retained"],
        "source_id": log_facts["launch_lock_id"],
        "schema": ANALYTIC_LOCK_SCHEMA,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "manifest_sha256": manifest_sha,
        "dataset_runtime_snapshot_sha256": expected["dataset_runtime_snapshot_sha256"],
        "docker_runtime_snapshot_sha256": expected["docker_runtime_snapshot_sha256"],
        "pid": expected["pid"],
        "created_at_utc": created_at,
    }


def validate_runtime_evidence_payloads(
    payloads: Mapping[str, bytes],
    *,
    manifest: Mapping[str, Any],
    manifest_sha: str,
    log_facts: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    expected_roles = set(RUNTIME_EVIDENCE_FILENAMES)
    if set(payloads) != expected_roles:
        return {}, ["runtime-evidence:role-set"]
    facts: dict[str, dict[str, Any]] = {}
    problems: list[str] = []
    validators = {
        "dataset_runtime_snapshot": lambda payload: _dataset_runtime_facts(
            payload,
            manifest=manifest,
            manifest_sha=manifest_sha,
            log_facts=log_facts,
        ),
        "docker_runtime_snapshot": lambda payload: _docker_runtime_facts(
            payload,
            manifest_sha=manifest_sha,
            log_facts=log_facts,
        ),
        "analytic_lock": lambda payload: _analytic_lock_facts(
            payload,
            manifest_sha=manifest_sha,
            log_facts=log_facts,
        ),
    }
    for role in sorted(expected_roles):
        try:
            facts[role] = validators[role](payloads[role])
        except (AnalysisInputError, AttributeError, KeyError, TypeError, ValueError) as error:
            problems.append(f"runtime-evidence:{role}:{error}")
    return facts, problems


def validate_manifest_bindings(
    manifest_path: str | pathlib.Path,
    schedule_path: str | pathlib.Path,
    *,
    analyzer_path: str | pathlib.Path | None = None,
) -> tuple[Mapping[str, Any], list[str]]:
    """Bind the exact schedule and the executing analyzer to the launch manifest."""

    manifest = _load_json_bytes(pathlib.Path(manifest_path).read_bytes(), str(manifest_path))
    problems: list[str] = []
    if manifest.get("schema") != LAUNCH_MANIFEST_SCHEMA:
        problems.append(f"manifest:schema:{manifest.get('schema')}")
    if manifest.get("verdict") != "I135_TOOLING_MANIFEST_OK":
        problems.append(f"manifest:verdict:{manifest.get('verdict')}")
    if manifest.get("launch_authorized") is not True:
        problems.append("manifest:launch-not-authorized")
    gates = manifest.get("gates")
    expected_gate_names = {
        "g0_preregistration",
        "g1_provenance",
        "g2_released_behavior",
        "g3_schedule_integrity",
        "g4_semantic_leak",
        "g5_live_smoke",
        "g7_dataset_provenance",
        "g8_storage_environment",
        "g9_resource_plan",
        "execution_plan",
        "execution_consumers",
        "tooling_verification",
        "mission_state",
    }
    if not isinstance(gates, dict) or set(gates) != expected_gate_names:
        problems.append("manifest:gate-set")
    elif any(value is not True for value in gates.values()):
        problems.append("manifest:gate-not-green")
    _dataset_facts, dataset_problems = validate_manifest_dataset(manifest)
    problems.extend(dataset_problems)
    bound = manifest.get("hash_bound_files")
    if not isinstance(bound, dict):
        problems.append("manifest:hash-bound-files-not-object")
        bound = {}
    bindings = {
        "dose_schedules.json": pathlib.Path(schedule_path),
        "analyze_dose135.py": pathlib.Path(analyzer_path or __file__),
    }
    for name, path in bindings.items():
        row = bound.get(name)
        if not isinstance(row, dict):
            problems.append(f"manifest:missing-hash-binding:{name}")
            continue
        expected_sha = row.get("sha256")
        expected_bytes = row.get("bytes")
        if not isinstance(expected_sha, str) or _SHA256_RE.fullmatch(expected_sha) is None:
            problems.append(f"manifest:invalid-bound-sha256:{name}")
            continue
        if type(expected_bytes) is not int or expected_bytes < 0:
            problems.append(f"manifest:invalid-bound-bytes:{name}")
            continue
        if not path.is_file() or path.is_symlink():
            problems.append(f"manifest:bound-input-not-regular-file:{name}")
            continue
        actual_sha = sha256_file(path)
        actual_bytes = path.stat().st_size
        if actual_sha != expected_sha:
            problems.append(f"manifest:bound-sha256-mismatch:{name}:{actual_sha}!={expected_sha}")
        if actual_bytes != expected_bytes:
            problems.append(f"manifest:bound-bytes-mismatch:{name}:{actual_bytes}!={expected_bytes}")
    return manifest, problems


def _git(
    repository_root: pathlib.Path, *arguments: str, text_output: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text_output,
    )


def _commit_blob_receipt(
    repository_root: pathlib.Path, commit: str, relative_path: str
) -> tuple[str, int] | None:
    listing = _git(
        repository_root,
        "ls-tree",
        "-z",
        commit,
        "--",
        relative_path,
        text_output=False,
    )
    if listing.returncode != 0 or not listing.stdout:
        return None
    rows = bytes(listing.stdout).rstrip(b"\0").split(b"\0")
    if len(rows) != 1:
        return None
    try:
        metadata, listed_path = rows[0].split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        decoded_path = listed_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None
    if decoded_path != relative_path or object_type != "blob" or not mode.startswith("100"):
        return None
    process = subprocess.Popen(
        ["git", "-C", str(repository_root), "cat-file", "blob", object_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    digest = hashlib.sha256()
    byte_count = 0
    for chunk in iter(lambda: process.stdout.read(1 << 20), b""):
        digest.update(chunk)
        byte_count += len(chunk)
    _stderr = process.stderr.read() if process.stderr is not None else b""
    if process.wait() != 0:
        return None
    return digest.hexdigest(), byte_count


def _proof_input_paths(
    args: argparse.Namespace, decision_paths: Mapping[str, Sequence[str | pathlib.Path]]
) -> dict[str, list[pathlib.Path]]:
    paths = {
        "i135_log": [pathlib.Path(args.i135_log)],
        "i135_runs": [pathlib.Path(args.i135_runs)],
        "validity_receipt": [pathlib.Path(args.validity_receipt)],
        **{
            role: [pathlib.Path(args.validity_receipt).parent / filename]
            for role, filename in RUNTIME_EVIDENCE_FILENAMES.items()
        },
    }
    paths.update(
        {f"decision_{arm}": [pathlib.Path(path) for path in decision_paths[arm]] for arm in ARMS}
    )
    return paths


def _validate_raw_proof_chain(
    repository_root: pathlib.Path,
    proof_commit: str,
    manifest_path: str | pathlib.Path,
    rows_by_role: Mapping[str, Sequence[tuple[str, str, int]]],
) -> list[str]:
    """Verify the collector's raw receipt and committed checksum sidecar independently."""

    problems: list[str] = []
    raw_rows = rows_by_role.get("raw_proof_receipt", ())
    if len(raw_rows) != 1:
        return ["raw-proof-chain:raw-receipt-row-count"]
    raw_relative, _raw_sha, _raw_bytes = raw_rows[0]
    raw_path = repository_root / pathlib.PurePosixPath(raw_relative)
    try:
        raw = _load_json_bytes(raw_path.read_bytes(), str(raw_path))
    except (AnalysisInputError, OSError) as error:
        return [f"raw-proof-chain:receipt-unreadable:{type(error).__name__}:{error}"]

    exact_root_fields = {
        "schema",
        "verdict",
        "launch_manifest_sha256",
        "collector_sha256",
        "collection_gate",
        "completion",
        "source_receipts",
        "artifacts",
        "problem_count",
        "problems",
    }
    if set(raw) != exact_root_fields:
        problems.append(
            "raw-proof-chain:root-fields:"
            f"missing={sorted(exact_root_fields - set(raw))}:"
            f"unknown={sorted(set(raw) - exact_root_fields)}"
        )
    expected_manifest_sha = sha256_file(manifest_path)
    for field, expected in (
        ("schema", RAW_PROOF_RECEIPT_SCHEMA),
        ("verdict", "I135_RAW_PROOF_COMPLETE"),
        ("launch_manifest_sha256", expected_manifest_sha),
        ("problem_count", 0),
        ("problems", []),
    ):
        if raw.get(field) != expected:
            problems.append(f"raw-proof-chain:{field}:{raw.get(field)!r}")

    try:
        manifest = _load_json_bytes(
            pathlib.Path(manifest_path).read_bytes(), str(manifest_path)
        )
    except (AnalysisInputError, OSError) as error:
        problems.append(f"raw-proof-chain:manifest-unreadable:{type(error).__name__}:{error}")
        manifest = {}
    bound_files = manifest.get("hash_bound_files")
    collector_row = bound_files.get("collect_proof135.py") if isinstance(bound_files, dict) else None
    collector_sha = collector_row.get("sha256") if isinstance(collector_row, dict) else None
    if (
        not isinstance(collector_sha, str)
        or _SHA256_RE.fullmatch(collector_sha) is None
        or raw.get("collector_sha256") != collector_sha
    ):
        problems.append("raw-proof-chain:collector-not-manifest-bound")

    gate = raw.get("collection_gate")
    if not isinstance(gate, dict) or set(gate) != {
        "minimum_local_free_bytes",
        "observed_local_free_bytes",
        "passed",
    }:
        problems.append("raw-proof-chain:collection-gate-fields")
    else:
        minimum = gate.get("minimum_local_free_bytes")
        observed = gate.get("observed_local_free_bytes")
        if minimum != MINIMUM_LOCAL_COLLECTION_BYTES:
            problems.append(f"raw-proof-chain:collection-minimum:{minimum}")
        if type(observed) is not int or observed < MINIMUM_LOCAL_COLLECTION_BYTES:
            problems.append(f"raw-proof-chain:collection-observed:{observed}")
        if gate.get("passed") is not True:
            problems.append("raw-proof-chain:collection-not-passed")

    expected_completion = {
        "done_marker": DONE_MARKER,
        "done_marker_count": 1,
        "successful_blocks": 120,
        "analytic_cells": 2_400,
        "decision_blocks": 120,
        "decision_resets": 2_400,
        "run_archive_cells": 2_400,
        "run_archive_members": 7_200,
    }
    if raw.get("completion") != expected_completion:
        problems.append(f"raw-proof-chain:completion:{raw.get('completion')!r}")
    source_receipts = raw.get("source_receipts")
    if not isinstance(source_receipts, dict):
        problems.append("raw-proof-chain:source-receipts-not-object")
        source_receipts = {}
    elif set(source_receipts) != {
        "launcher_log",
        "runtime_evidence",
        "decision_blocks",
        "run_tree",
    }:
        problems.append("raw-proof-chain:source-receipt-role-set")

    artifact_roles = set(rows_by_role) - {"raw_proof_receipt"}
    raw_artifacts = raw.get("artifacts")
    if not isinstance(raw_artifacts, dict) or set(raw_artifacts) != artifact_roles:
        problems.append("raw-proof-chain:artifact-role-set")
        raw_artifacts = {}
    proof_parent = pathlib.PurePosixPath(raw_relative).parent
    expected_checksums: dict[str, str] = {}
    for role in sorted(rows_by_role):
        rows = rows_by_role[role]
        if len(rows) != 1:
            continue
        relative_path, digest, byte_count = rows[0]
        pure_path = pathlib.PurePosixPath(relative_path)
        if pure_path.parent != proof_parent:
            problems.append(f"raw-proof-chain:not-flat-single-proof-directory:{relative_path}")
        expected_checksums[pure_path.name] = digest
        if role == "raw_proof_receipt":
            continue
        expected_artifact = {
            "path": pure_path.name,
            "sha256": digest,
            "bytes": byte_count,
        }
        if raw_artifacts.get(role) != expected_artifact:
            problems.append(f"raw-proof-chain:artifact-mismatch:{role}")

    runtime_payloads: dict[str, bytes] = {}
    for role in RUNTIME_EVIDENCE_FILENAMES:
        role_rows = rows_by_role.get(role, ())
        if len(role_rows) != 1:
            problems.append(f"raw-proof-chain:runtime-row-count:{role}")
            continue
        relative_path = role_rows[0][0]
        try:
            runtime_payloads[role] = (
                repository_root / pathlib.PurePosixPath(relative_path)
            ).read_bytes()
        except OSError as error:
            problems.append(
                f"raw-proof-chain:runtime-unreadable:{role}:{type(error).__name__}:{error}"
            )
    log_rows = rows_by_role.get("i135_log", ())
    runtime_facts: dict[str, dict[str, Any]] = {}
    if len(log_rows) != 1:
        problems.append("raw-proof-chain:runtime-log-row-count")
    else:
        log_path = repository_root / pathlib.PurePosixPath(log_rows[0][0])
        try:
            log_payload = gzip.decompress(log_path.read_bytes())
            log_facts = runtime_log_facts(log_payload)
        except (OSError, EOFError, gzip.BadGzipFile, AnalysisInputError) as error:
            problems.append(f"raw-proof-chain:runtime-log:{type(error).__name__}:{error}")
        else:
            if log_facts.get("manifest_sha256") != expected_manifest_sha:
                problems.append("raw-proof-chain:runtime-log-manifest-sha256")
            runtime_facts, runtime_problems = validate_runtime_evidence_payloads(
                runtime_payloads,
                manifest=manifest,
                manifest_sha=expected_manifest_sha,
                log_facts=log_facts,
            )
            problems.extend(f"raw-proof-chain:{problem}" for problem in runtime_problems)
    if source_receipts.get("runtime_evidence") != runtime_facts:
        problems.append("raw-proof-chain:runtime-source-receipts")

    proof_directory = raw_path.parent
    checksum_path = proof_directory / "SHA256SUMS.txt"
    expected_names = set(expected_checksums) | {"SHA256SUMS.txt"}
    if proof_directory.is_dir():
        actual_names = {
            path.name
            for path in proof_directory.iterdir()
            if path.is_file() and not path.is_symlink()
        }
        invalid_entries = [
            path.name
            for path in proof_directory.iterdir()
            if path.is_symlink() or not path.is_file()
        ]
        if actual_names != expected_names or invalid_entries:
            problems.append(
                "raw-proof-chain:file-set:"
                f"missing={sorted(expected_names - actual_names)}:"
                f"extra={sorted(actual_names - expected_names)}:"
                f"invalid={sorted(invalid_entries)}"
            )
    if not checksum_path.is_file() or checksum_path.is_symlink():
        problems.append("raw-proof-chain:sha256s-not-regular-file")
        return problems
    checksum_rows: dict[str, str] = {}
    try:
        checksum_lines = checksum_path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        problems.append(f"raw-proof-chain:sha256s-unreadable:{type(error).__name__}:{error}")
        return problems
    for index, line in enumerate(checksum_lines, 1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", line)
        if match is None or match.group(2) in checksum_rows:
            problems.append(f"raw-proof-chain:sha256s-row:{index}")
            continue
        checksum_rows[match.group(2)] = match.group(1)
    if checksum_rows != expected_checksums:
        problems.append("raw-proof-chain:sha256s-content-mismatch")

    checksum_relative = checksum_path.relative_to(repository_root).as_posix()
    checksum_current = (sha256_file(checksum_path), checksum_path.stat().st_size)
    checksum_committed = _commit_blob_receipt(
        repository_root, proof_commit, checksum_relative
    )
    if checksum_committed != checksum_current:
        problems.append("raw-proof-chain:sha256s-commit-blob-mismatch")
    tracked = _git(repository_root, "ls-files", "--error-unmatch", "--", checksum_relative)
    worktree_diff = _git(
        repository_root, "diff", "--quiet", proof_commit, "--", checksum_relative
    )
    index_diff = _git(
        repository_root,
        "diff",
        "--cached",
        "--quiet",
        proof_commit,
        "--",
        checksum_relative,
    )
    if tracked.returncode != 0 or worktree_diff.returncode != 0 or index_diff.returncode != 0:
        problems.append("raw-proof-chain:sha256s-not-current-committed-proof")
    return problems


def validate_committed_proof_receipt(
    receipt_path: str | pathlib.Path,
    manifest_path: str | pathlib.Path,
    args: argparse.Namespace,
    decision_paths: Mapping[str, Sequence[str | pathlib.Path]],
    *,
    expected_repository_root: str | pathlib.Path | None = None,
) -> tuple[Mapping[str, Any], list[str]]:
    """Verify current proof bytes against exact blobs in an ancestor Git commit.

    The receipt contains no trusted ``git_clean`` boolean.  Every proof input is checked against
    the named commit, the current index, and the current working-tree bytes by this analyzer.
    """

    receipt = _load_json_bytes(pathlib.Path(receipt_path).read_bytes(), str(receipt_path))
    problems: list[str] = []
    expected_root_fields = {
        "schema",
        "launch_manifest_sha256",
        "repository_root",
        "proof_commit",
        "inputs",
        "problem_count",
        "problems",
    }
    if set(receipt) != expected_root_fields:
        problems.append(
            "proof-receipt:root-fields:"
            f"missing={sorted(expected_root_fields - set(receipt))}:"
            f"unknown={sorted(set(receipt) - expected_root_fields)}"
        )
    if receipt.get("schema") != COMMITTED_PROOF_RECEIPT_SCHEMA:
        problems.append(f"proof-receipt:schema:{receipt.get('schema')}")
    try:
        manifest_sha = sha256_file(manifest_path)
    except OSError as error:
        problems.append(f"proof-receipt:manifest-unreadable:{type(error).__name__}:{error}")
        manifest_sha = None
    if receipt.get("launch_manifest_sha256") != manifest_sha:
        problems.append("proof-receipt:launch-manifest-hash-mismatch")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        problems.append("proof-receipt:collector-reported-problems")

    root_value = receipt.get("repository_root")
    repository_root = pathlib.Path(root_value).resolve() if isinstance(root_value, str) else None
    expected_root = pathlib.Path(expected_repository_root or pathlib.Path(__file__).resolve().parents[2]).resolve()
    if repository_root is None or not pathlib.Path(root_value).is_absolute():
        problems.append("proof-receipt:repository-root-not-absolute")
        repository_root = expected_root
    if repository_root != expected_root:
        problems.append(f"proof-receipt:repository-root:{repository_root}!={expected_root}")
    top = _git(repository_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        problems.append("proof-receipt:repository-not-git")
    else:
        try:
            discovered_root = pathlib.Path(top.stdout.strip()).resolve()
        except (OSError, RuntimeError):
            discovered_root = pathlib.Path("/")
        if discovered_root != repository_root:
            problems.append(
                f"proof-receipt:git-root-mismatch:{discovered_root}!={repository_root}"
            )

    proof_commit = receipt.get("proof_commit")
    commit_valid = isinstance(proof_commit, str) and _GIT_COMMIT_RE.fullmatch(proof_commit) is not None
    if not commit_valid:
        problems.append(f"proof-receipt:invalid-proof-commit:{proof_commit}")
    else:
        exists = _git(repository_root, "cat-file", "-e", f"{proof_commit}^{{commit}}")
        if exists.returncode != 0:
            problems.append("proof-receipt:proof-commit-not-found")
            commit_valid = False
        ancestor = _git(repository_root, "merge-base", "--is-ancestor", proof_commit, "HEAD")
        if ancestor.returncode != 0:
            problems.append("proof-receipt:proof-commit-not-ancestor-of-head")

    actual_inputs = _proof_input_paths(args, decision_paths)
    expected_roles = set(actual_inputs) | {"raw_proof_receipt"}
    raw_inputs = receipt.get("inputs")
    if not isinstance(raw_inputs, dict):
        problems.append("proof-receipt:inputs-not-object")
        raw_inputs = {}
    if set(raw_inputs) != expected_roles:
        problems.append(
            "proof-receipt:roles:"
            f"missing={sorted(expected_roles - set(raw_inputs))}:"
            f"unknown={sorted(set(raw_inputs) - expected_roles)}"
        )

    seen_paths: set[str] = set()
    rows_by_role: dict[str, list[tuple[str, str, int]]] = {}
    for role in sorted(expected_roles):
        raw_rows = raw_inputs.get(role)
        if not isinstance(raw_rows, list) or not raw_rows:
            problems.append(f"proof-receipt:{role}:rows-not-nonempty-list")
            continue
        if len(raw_rows) != 1:
            problems.append(f"proof-receipt:{role}:expected-one-row:{len(raw_rows)}")

        receipt_paths: list[str] = []
        validated_rows: list[tuple[str, str, int]] = []
        for index, row in enumerate(raw_rows):
            where = f"proof-receipt:{role}:{index}"
            if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes"}:
                problems.append(f"{where}:fields")
                continue
            relative_path = row.get("path")
            expected_sha = row.get("sha256")
            expected_bytes = row.get("bytes")
            if not isinstance(relative_path, str):
                problems.append(f"{where}:path-not-string")
                continue
            pure_path = pathlib.PurePosixPath(relative_path)
            if (
                pure_path.is_absolute()
                or relative_path != pure_path.as_posix()
                or relative_path in ("", ".")
                or ".." in pure_path.parts
            ):
                problems.append(f"{where}:path-not-canonical-repository-relative")
                continue
            if relative_path in seen_paths:
                problems.append(f"{where}:duplicate-path:{relative_path}")
            seen_paths.add(relative_path)
            receipt_paths.append(relative_path)
            if not isinstance(expected_sha, str) or _SHA256_RE.fullmatch(expected_sha) is None:
                problems.append(f"{where}:invalid-sha256")
                continue
            if type(expected_bytes) is not int or expected_bytes < 0:
                problems.append(f"{where}:invalid-bytes")
                continue
            validated_rows.append((relative_path, expected_sha, expected_bytes))
        rows_by_role[role] = validated_rows

        if role != "raw_proof_receipt":
            actual_paths = actual_inputs.get(role, [])
            actual_relative_paths: list[str] = []
            for actual_path in actual_paths:
                try:
                    actual_relative_paths.append(
                        actual_path.resolve(strict=True).relative_to(repository_root).as_posix()
                    )
                except (FileNotFoundError, OSError, ValueError):
                    problems.append(f"proof-receipt:{role}:actual-path-outside-or-missing:{actual_path}")
            if actual_relative_paths != receipt_paths:
                problems.append(
                    f"proof-receipt:{role}:path-order-mismatch:"
                    f"actual={actual_relative_paths}:receipt={receipt_paths}"
                )

        for relative_path, expected_sha, expected_bytes in validated_rows:
            current_path = repository_root / pathlib.PurePosixPath(relative_path)
            if not current_path.is_file() or current_path.is_symlink():
                problems.append(f"proof-receipt:not-regular-file:{relative_path}")
                continue
            actual_sha = sha256_file(current_path)
            actual_bytes = current_path.stat().st_size
            if actual_sha != expected_sha:
                problems.append(f"proof-receipt:current-sha256-mismatch:{relative_path}")
            if actual_bytes != expected_bytes:
                problems.append(f"proof-receipt:current-bytes-mismatch:{relative_path}")
            if not commit_valid:
                continue
            committed = _commit_blob_receipt(repository_root, proof_commit, relative_path)
            if committed is None:
                problems.append(f"proof-receipt:not-blob-at-proof-commit:{relative_path}")
                continue
            if committed != (expected_sha, expected_bytes):
                problems.append(f"proof-receipt:commit-blob-mismatch:{relative_path}")
            tracked = _git(repository_root, "ls-files", "--error-unmatch", "--", relative_path)
            if tracked.returncode != 0:
                problems.append(f"proof-receipt:not-tracked-in-index:{relative_path}")
            worktree_diff = _git(repository_root, "diff", "--quiet", proof_commit, "--", relative_path)
            index_diff = _git(
                repository_root, "diff", "--cached", "--quiet", proof_commit, "--", relative_path
            )
            if worktree_diff.returncode != 0 or index_diff.returncode != 0:
                problems.append(f"proof-receipt:current-state-differs-from-proof-commit:{relative_path}")
    if commit_valid:
        problems.extend(
            _validate_raw_proof_chain(
                repository_root,
                proof_commit,
                manifest_path,
                rows_by_role,
            )
        )
    return receipt, problems


def validate_receipt(
    receipt_path: str | pathlib.Path, manifest_path: str | pathlib.Path
) -> tuple[dict[str, bool], list[str], Mapping[str, Any]]:
    receipt = _load_json_bytes(pathlib.Path(receipt_path).read_bytes(), str(receipt_path))
    problems: list[str] = []
    if receipt.get("schema") != VALIDITY_RECEIPT_SCHEMA:
        problems.append(f"receipt:schema:{receipt.get('schema')}")
    manifest_hash = sha256_file(manifest_path)
    if receipt.get("launch_manifest_sha256") != manifest_hash:
        problems.append("receipt:launch-manifest-hash-mismatch")
    raw_gates = receipt.get("gates")
    gates: dict[str, bool] = {}
    if not isinstance(raw_gates, dict):
        problems.append("receipt:gates-not-object")
        raw_gates = {}
    expected_receipt_gates = {"G0", "G1", "G2", "G3", "G4", "G5", "G8", "G9"}
    if set(raw_gates) != expected_receipt_gates:
        problems.append(
            "receipt:gate-set:"
            f"missing={sorted(expected_receipt_gates - set(raw_gates))}:"
            f"extra={sorted(set(raw_gates) - expected_receipt_gates)}"
        )
    for gate in sorted(expected_receipt_gates):
        gates[gate] = raw_gates.get(gate) is True
        if not gates[gate]:
            problems.append(f"receipt:{gate}:not-explicitly-true")

    try:
        manifest = _load_json_bytes(pathlib.Path(manifest_path).read_bytes(), str(manifest_path))
    except (AnalysisInputError, OSError) as error:
        problems.append(f"receipt:dataset-manifest-unreadable:{type(error).__name__}:{error}")
        manifest = {}
    dataset_facts, dataset_manifest_problems = validate_manifest_dataset(manifest)
    problems.extend(f"receipt:{problem}" for problem in dataset_manifest_problems)
    if manifest.get("gates", {}).get("g7_dataset_provenance") is not True:
        problems.append("receipt:manifest-dataset-gate-not-green")
    proof_directory = pathlib.Path(receipt_path).parent
    runtime_payloads: dict[str, bytes] = {}
    runtime_facts: dict[str, dict[str, Any]] = {}
    try:
        runtime_log_path = proof_directory / "sentinel-i135.log.gz"
        if runtime_log_path.is_symlink() or not runtime_log_path.is_file():
            raise AnalysisInputError("runtime log is not a physical regular file")
        packaged_log = gzip.decompress(runtime_log_path.read_bytes())
        log_facts = runtime_log_facts(packaged_log)
    except (OSError, EOFError, gzip.BadGzipFile, AnalysisInputError) as error:
        problems.append(f"receipt:runtime-log:{type(error).__name__}:{error}")
    else:
        if log_facts.get("manifest_sha256") != manifest_hash:
            problems.append("receipt:runtime-log-manifest-sha256")
        for role, filename in RUNTIME_EVIDENCE_FILENAMES.items():
            try:
                runtime_path = proof_directory / filename
                if runtime_path.is_symlink() or not runtime_path.is_file():
                    raise AnalysisInputError("not a physical regular file")
                runtime_payloads[role] = runtime_path.read_bytes()
            except (AnalysisInputError, OSError) as error:
                problems.append(
                    f"receipt:runtime-evidence-unreadable:{role}:{type(error).__name__}:{error}"
                )
        runtime_facts, runtime_problems = validate_runtime_evidence_payloads(
            runtime_payloads,
            manifest=manifest,
            manifest_sha=manifest_hash,
            log_facts=log_facts,
        )
        problems.extend(f"receipt:{problem}" for problem in runtime_problems)
    runtime_snapshot = f"/var/lib/sentinel/i135-runtime-{manifest_hash}"
    dataset_runtime = runtime_facts.get("dataset_runtime_snapshot", {})
    expected_dataset_provenance = {
        **dataset_facts,
        "manifest_gate": "g7_dataset_provenance",
        "passed": True,
        "runtime_snapshot_contract": {
            "schema": DATASET_RUNTIME_SCHEMA,
            "path": f"{runtime_snapshot}/dataset_runtime_snapshot.json",
            "manifest_sha256": manifest_hash,
            "dataset_receipt_payload_sha256": dataset_facts.get(
                "dataset_receipt_payload_sha256"
            ),
            "file_count": dataset_facts["dataset_file_count"],
            "sha256": dataset_runtime.get("sha256"),
            "bytes": dataset_runtime.get("bytes"),
            "source_id": dataset_runtime.get("source_id"),
        },
    }
    if receipt.get("dataset_provenance") != expected_dataset_provenance:
        problems.append("receipt:dataset-provenance-drift")
    docker_runtime = runtime_facts.get("docker_runtime_snapshot", {})
    expected_docker_provenance = {
        "schema": DOCKER_RUNTIME_SCHEMA,
        "path": docker_runtime.get("source_path"),
        "manifest_sha256": docker_runtime.get("manifest_sha256"),
        "sha256": docker_runtime.get("sha256"),
        "bytes": docker_runtime.get("bytes"),
        "source_id": docker_runtime.get("source_id"),
        "client_path": docker_runtime.get("client_path"),
        "client_sha256": docker_runtime.get("client_sha256"),
        "context": docker_runtime.get("context"),
        "endpoint": docker_runtime.get("endpoint"),
        "daemon_id": docker_runtime.get("daemon_id"),
        "server_version": docker_runtime.get("server_version"),
    }
    if receipt.get("docker_runtime_provenance") != expected_docker_provenance:
        problems.append("receipt:docker-runtime-provenance-drift")
    analytic_lock = runtime_facts.get("analytic_lock", {})
    expected_lock_provenance = {
        "schema": ANALYTIC_LOCK_SCHEMA,
        "path": analytic_lock.get("source_path"),
        "source_id": analytic_lock.get("source_id"),
        "sha256": analytic_lock.get("sha256"),
        "bytes": analytic_lock.get("bytes"),
        "manifest_sha256": analytic_lock.get("manifest_sha256"),
        "dataset_runtime_snapshot_sha256": analytic_lock.get(
            "dataset_runtime_snapshot_sha256"
        ),
        "docker_runtime_snapshot_sha256": analytic_lock.get(
            "docker_runtime_snapshot_sha256"
        ),
        "pid": analytic_lock.get("pid"),
        "created_at_utc": analytic_lock.get("created_at_utc"),
    }
    if receipt.get("analytic_lock_provenance") != expected_lock_provenance:
        problems.append("receipt:analytic-lock-provenance-drift")
    if receipt.get("falsifiers_clear") is not True:
        problems.append("receipt:falsifiers-not-clear")
    if receipt.get("done_marker") != DONE_MARKER:
        problems.append(f"receipt:done-marker:{receipt.get('done_marker')}")
    try:
        gpu_hours = float(receipt["analytic_gpu_hours"])
    except (KeyError, TypeError, ValueError):
        problems.append("receipt:analytic-gpu-hours-missing")
    else:
        if not math.isfinite(gpu_hours) or gpu_hours < 0 or gpu_hours > 110:
            problems.append(f"receipt:resource-ceiling:{gpu_hours}")
    for field, minimum in (
        ("remote_free_gib_at_launch", 100.0),
        ("remote_projected_reserve_gib", 25.0),
        ("local_free_gib_at_collection", 15.0),
    ):
        try:
            value = float(receipt[field])
        except (KeyError, TypeError, ValueError):
            problems.append(f"receipt:{field}:missing")
        else:
            if not math.isfinite(value) or value < minimum:
                problems.append(f"receipt:{field}:{value}<{minimum}")
    if receipt.get("retry_policy_violations") != 0:
        problems.append(f"receipt:retry-policy-violations:{receipt.get('retry_policy_violations')}")
    unexpected = receipt.get("unexpected_falsifiers", receipt.get("falsifier_violations"))
    if unexpected != []:
        problems.append(f"receipt:unexpected-falsifiers:{unexpected}")
    return gates, problems, receipt


def make_realization_report(
    schedules: Mapping[Cell, Mapping[str, Any]],
    decisions: Mapping[str, ParsedDecisionLog],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arm in BLIND_ARMS:
        cells: list[dict[str, Any]] = []
        by_class: dict[str, dict[str, float | int]] = {}
        for cls in CLASSES:
            class_cells: list[dict[str, Any]] = []
            for seq in CLASS_PAIRS[cls]:
                for run in range(NRUNS):
                    cell = (arm, cls, seq, run)
                    scheduled = list(schedules[cell]["brake_frames"])
                    decision = decisions[arm].cells[cell]
                    row = {
                        "class": cls,
                        "pair": seq,
                        "run": run,
                        "scheduled_brake_frames": scheduled,
                        "scheduled_brake_count": len(scheduled),
                        "scheduled_window_count": contiguous_window_count(scheduled),
                        "realized_brake_frames": sorted(decision.brakes),
                        "realized_brake_count": len(decision.brakes),
                        "realized_window_count": contiguous_window_count(decision.brakes),
                        "episode_frame_count": len(decision.frames),
                    }
                    class_cells.append(row)
                    cells.append(row)
            scheduled_total = sum(int(row["scheduled_brake_count"]) for row in class_cells)
            realized_total = sum(int(row["realized_brake_count"]) for row in class_cells)
            by_class[cls] = {
                "scheduled_brake_frames": scheduled_total,
                "realized_brake_frames": realized_total,
                "realization_fraction": realized_total / scheduled_total,
                "intervention_free_realized_episode_fraction": sum(
                    int(row["realized_brake_count"]) == 0 for row in class_cells
                )
                / len(class_cells),
            }
        scheduled_total = sum(int(row["scheduled_brake_count"]) for row in cells)
        realized_total = sum(int(row["realized_brake_count"]) for row in cells)
        out[arm] = {
            "scheduled_brake_frames": scheduled_total,
            "realized_brake_frames": realized_total,
            "realization_fraction": realized_total / scheduled_total,
            "scheduled_windows": sum(int(row["scheduled_window_count"]) for row in cells),
            "realized_windows": sum(int(row["realized_window_count"]) for row in cells),
            "intervention_free_realized_episode_fraction": sum(
                int(row["realized_brake_count"]) == 0 for row in cells
            )
            / len(cells),
            "by_class": by_class,
            "by_class_pair_run": cells,
        }
    return out


def unstratified_sensitivity(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]]
) -> dict[str, Bounds]:
    rng = random.Random(BOOT_SEED)
    pairs = canonical_pairs()
    union = "released_union_semantic_reference"
    blind = "blind_1_0x"
    values = {"ncap": [], "q16": []}
    for _ in range(BOOT_DRAWS):
        draw = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        for metric in values:
            deltas = [pair_tables[union][pair][metric] - pair_tables[blind][pair][metric] for pair in draw]
            values[metric].append(math.fsum(deltas) / len(deltas))
    return {metric: frozen_bounds(draws) for metric, draws in values.items()}


def source_scene_sensitivity(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]]
) -> dict[str, Bounds]:
    rng = random.Random(BOOT_SEED)
    sources = tuple(dict.fromkeys(seq for _, seq in canonical_pairs()))
    if len(sources) != 14:
        raise AnalysisInputError(f"source-scene sensitivity expected 14 scenes, got {len(sources)}")
    union = "released_union_semantic_reference"
    blind = "blind_1_0x"
    values = {"ncap": [], "q16": []}
    # A source-cluster draw can omit every source belonging to a five-pair class.  Such a draw
    # cannot evaluate the frozen equal-class estimand, so deterministically reject it and continue
    # until 100,000 valid source-cluster draws exist.  This is sensitivity-only and cannot affect
    # the verdict.
    while len(values["ncap"]) < BOOT_DRAWS:
        sampled = [sources[rng.randrange(len(sources))] for _ in sources]
        weights = collections.Counter(sampled)
        if any(not any(weights[seq] for seq in CLASS_PAIRS[cls]) for cls in CLASSES):
            continue
        for metric in values:
            class_means = []
            for cls in CLASSES:
                deltas: list[float] = []
                for seq in CLASS_PAIRS[cls]:
                    delta = pair_tables[union][(cls, seq)][metric] - pair_tables[blind][(cls, seq)][metric]
                    deltas.extend([delta] * weights[seq])
                class_means.append(math.fsum(deltas) / len(deltas))
            values[metric].append(math.fsum(class_means) / len(CLASSES))
    return {metric: frozen_bounds(draws) for metric, draws in values.items()}


def run_index_sensitivity(
    episode_values: Mapping[str, Mapping[str, Mapping[Pair, Sequence[float]]]]
) -> dict[str, Bounds]:
    rng = random.Random(BOOT_SEED)
    union = "released_union_semantic_reference"
    blind = "blind_1_0x"
    values = {"ncap": [], "q16": []}
    for _ in range(BOOT_DRAWS):
        indices = [rng.randrange(NRUNS) for _ in range(NRUNS)]
        ncap_pair: dict[Pair, float] = {}
        q_pair: dict[Pair, float] = {}
        for pair in canonical_pairs():
            un = episode_values[union]["ncap"][pair]
            bn = episode_values[blind]["ncap"][pair]
            ncap_pair[pair] = math.fsum(un[index] - bn[index] for index in indices) / NRUNS
            off_q = episode_values["off_baseline"]["q16_distance"][pair]
            uq = episode_values[union]["q16_distance"][pair]
            bq = episode_values[blind]["q16_distance"][pair]
            denominator = math.fsum(off_q[index] for index in indices) / NRUNS
            if denominator <= 0:
                raise AnalysisInputError(f"run-index OFF Q16 denominator is nonpositive for {pair}")
            q_pair[pair] = math.fsum(
                min(1.0, uq[index] / denominator) - min(1.0, bq[index] / denominator)
                for index in indices
            ) / NRUNS
        values["ncap"].append(aggregate_equal_class(ncap_pair))
        values["q16"].append(aggregate_equal_class(q_pair))
    return {metric: frozen_bounds(draws) for metric, draws in values.items()}


def sensitivity_report(
    pair_tables: Mapping[str, Mapping[Pair, Mapping[str, float]]],
    episode_values: Mapping[str, Mapping[str, Mapping[Pair, Sequence[float]]]],
    primary: Mapping[str, Any],
) -> dict[str, Any]:
    unstratified = unstratified_sensitivity(pair_tables)
    source = source_scene_sensitivity(pair_tables)
    run_index = run_index_sensitivity(episode_values)
    primary_decisions = {
        "ncap_lcb_excludes_zero": primary["ncap_bounds"]["lcb95"] > 0,
        "q16_lcb_above_margin": primary["q16_bounds"]["lcb95"] > -0.05,
    }
    methods = {
        "unstratified_20_pair": unstratified,
        "source_scene_14_cluster": source,
        "run_index": run_index,
    }
    out: dict[str, Any] = {
        "primary_decisions": primary_decisions,
        "source_scene_empty_class_rule": "deterministic rejection until 100000 valid draws",
        "methods": {},
    }
    any_disagreement = False
    for name, bounds_by_metric in methods.items():
        method_decisions = {
            "ncap_lcb_excludes_zero": bounds_by_metric["ncap"].lcb95 > 0,
            "q16_lcb_above_margin": bounds_by_metric["q16"].lcb95 > -0.05,
        }
        disagreement = method_decisions != primary_decisions
        any_disagreement = any_disagreement or disagreement
        out["methods"][name] = {
            "ncap_bounds": dataclasses.asdict(bounds_by_metric["ncap"]),
            "q16_bounds": dataclasses.asdict(bounds_by_metric["q16"]),
            "decisions": method_decisions,
            "disagrees_with_primary": disagreement,
        }
    out["any_disagreement"] = any_disagreement
    return out


def parse_decision_arguments(values: Sequence[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = collections.defaultdict(list)
    for value in values:
        if "=" not in value:
            raise AnalysisInputError(f"--decision-log must be ARM=PATH: {value}")
        arm, path = value.split("=", 1)
        if arm not in ARMS:
            raise AnalysisInputError(f"unknown decision-log arm: {arm}")
        if not path:
            raise AnalysisInputError(f"empty decision-log path for {arm}")
        grouped[arm].append(path)
    missing = [arm for arm in ARMS if arm not in grouped]
    if missing:
        raise AnalysisInputError(f"missing decision logs for arms: {missing}")
    return dict(grouped)


def input_digest_report(paths: Mapping[str, Sequence[str | pathlib.Path]]) -> dict[str, Any]:
    return {
        label: [{"path": str(path), "sha256": sha256_file(path)} for path in members]
        for label, members in paths.items()
    }


def verify_frozen_oracle_inputs(args: argparse.Namespace) -> None:
    """Reject any drift-oracle substitution before parsing outcomes."""

    problems: list[str] = []
    for label, raw_path, expected in (
        ("log", args.oracle_log, EXPECTED_ORACLE_LOG_SHA256),
        ("runs", args.oracle_runs, EXPECTED_ORACLE_RUNS_SHA256),
    ):
        path = pathlib.Path(raw_path)
        if not path.is_file():
            problems.append(f"{label}:not-file")
            continue
        actual = sha256_file(path)
        if actual != expected:
            problems.append(f"{label}:sha256:{actual}!={expected}")
    union_paths = [pathlib.Path(path) for path in args.oracle_union_log]
    if len(union_paths) != len(EXPECTED_ORACLE_UNION_PART_SHA256):
        problems.append(f"union-parts:count:{len(union_paths)}/2")
    else:
        for index, (path, expected) in enumerate(
            zip(union_paths, EXPECTED_ORACLE_UNION_PART_SHA256, strict=True)
        ):
            if not path.is_file():
                problems.append(f"union-part-{index}:not-file")
                continue
            actual = sha256_file(path)
            if actual != expected:
                problems.append(f"union-part-{index}:sha256:{actual}!={expected}")
    if problems:
        raise AnalysisInputError("frozen-oracle-provenance:" + ";".join(problems))


# ---- Manifest-bound normalized evidence API ----------------------------------------------
#
# The prelaunch collector owns raw log/tar parsing and emits this deliberately narrow schema.
# Keeping this layer pure makes every estimator and hostile boundary testable without creating a
# future analytic artifact or accepting a precomputed endpoint.

_ROOT_FIELDS = frozenset({"schema", "episodes", "validity_gates", "falsifiers"})
_GATE_FIELDS = frozenset({"passed", "detail"})
_EPISODE_FIELDS = frozenset(
    {
        "arm",
        "scenario_class",
        "pair",
        "run",
        "ncap_score",
        "impact_speed",
        "ego_poses",
        "collision",
        "terminal_reason",
        "episode_frame_count",
        "scheduled_brake_frames",
        "realized_brake_frames",
        "realized_release_frames",
    }
)


def _exact_schema_fields(value: Mapping[str, Any], expected: frozenset[str], where: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise EvidenceError(f"{where} fields: missing={missing}, unknown={unknown}")


def _finite_schema_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{where} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceError(f"{where} must be finite")
    return result


def _schema_frames(value: Any, where: str) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise EvidenceError(f"{where} must be a list")
    if any(isinstance(frame, bool) or not isinstance(frame, int) or frame < 0 for frame in value):
        raise EvidenceError(f"{where} must contain only nonnegative integers")
    if value != sorted(set(value)):
        raise EvidenceError(f"{where} must be sorted and unique")
    return tuple(value)


def _parse_evidence_episode(raw: Any, index: int) -> EvidenceEpisode:
    where = f"episodes[{index}]"
    if not isinstance(raw, dict):
        raise EvidenceError(f"{where} must be an object")
    _exact_schema_fields(raw, _EPISODE_FIELDS, where)
    arm = raw["arm"]
    scenario_class = raw["scenario_class"]
    pair = raw["pair"]
    run = raw["run"]
    if arm not in ARMS:
        raise EvidenceError(f"{where}.arm is not registered: {arm!r}")
    if scenario_class not in CLASSES:
        raise EvidenceError(f"{where}.scenario_class is not registered: {scenario_class!r}")
    if not isinstance(pair, str) or pair not in CLASS_PAIRS[scenario_class]:
        raise EvidenceError(f"{where}.pair is not registered for {scenario_class}: {pair!r}")
    if isinstance(run, bool) or not isinstance(run, int) or run not in RUNS:
        raise EvidenceError(f"{where}.run must be one of 0..19")
    ncap = _finite_schema_number(raw["ncap_score"], f"{where}.ncap_score")
    impact = _finite_schema_number(raw["impact_speed"], f"{where}.impact_speed")
    if not 0.0 <= ncap <= 5.0:
        raise EvidenceError(f"{where}.ncap_score must be in [0,5]")
    if impact < 0.0:
        raise EvidenceError(f"{where}.impact_speed must be nonnegative")
    if not isinstance(raw["collision"], bool):
        raise EvidenceError(f"{where}.collision must be boolean")
    terminal_reason = raw["terminal_reason"]
    if not isinstance(terminal_reason, str) or not terminal_reason.strip():
        raise EvidenceError(f"{where}.terminal_reason must be a nonempty string")
    frame_count = raw["episode_frame_count"]
    if isinstance(frame_count, bool) or not isinstance(frame_count, int) or frame_count <= 0:
        raise EvidenceError(f"{where}.episode_frame_count must be a positive integer")
    scheduled = _schema_frames(raw["scheduled_brake_frames"], f"{where}.scheduled_brake_frames")
    realized = _schema_frames(raw["realized_brake_frames"], f"{where}.realized_brake_frames")
    releases = _schema_frames(raw["realized_release_frames"], f"{where}.realized_release_frames")
    if any(frame >= frame_count for frame in realized + releases):
        raise EvidenceError(f"{where} has a realized frame outside episode_frame_count")
    return EvidenceEpisode(
        arm=arm,
        scenario_class=scenario_class,
        pair=pair,
        run=run,
        ncap_score=ncap,
        impact_speed=impact,
        ego_points=pose_points(raw["ego_poses"], f"{where}.ego_poses"),
        collision=raw["collision"],
        terminal_reason=terminal_reason,
        episode_frame_count=frame_count,
        scheduled_brake_frames=scheduled,
        realized_brake_frames=realized,
        realized_release_frames=releases,
    )


def parse_evidence(document: Any) -> ParsedEvidence:
    """Parse the exact collector schema and reject every unregistered/precomputed field."""

    if not isinstance(document, dict):
        raise EvidenceError("evidence root must be an object")
    _exact_schema_fields(document, _ROOT_FIELDS, "root")
    if document["schema"] != EVIDENCE_SCHEMA:
        raise EvidenceError(f"schema must be {EVIDENCE_SCHEMA!r}")
    raw_gates = document["validity_gates"]
    if not isinstance(raw_gates, dict) or set(raw_gates) != set(GATE_IDS):
        missing = sorted(set(GATE_IDS) - set(raw_gates)) if isinstance(raw_gates, dict) else list(GATE_IDS)
        unknown = sorted(set(raw_gates) - set(GATE_IDS)) if isinstance(raw_gates, dict) else []
        raise EvidenceError(
            f"validity_gates must contain exactly G0..G9; missing={missing}, unknown={unknown}"
        )
    gates: dict[str, dict[str, Any]] = {}
    for gate_id in GATE_IDS:
        raw_gate = raw_gates[gate_id]
        if not isinstance(raw_gate, dict):
            raise EvidenceError(f"validity_gates.{gate_id} must be an object")
        _exact_schema_fields(raw_gate, _GATE_FIELDS, f"validity_gates.{gate_id}")
        if not isinstance(raw_gate["passed"], bool):
            raise EvidenceError(f"validity_gates.{gate_id}.passed must be boolean")
        if not isinstance(raw_gate["detail"], str) or not raw_gate["detail"].strip():
            raise EvidenceError(f"validity_gates.{gate_id}.detail must be nonempty")
        gates[gate_id] = {"passed": raw_gate["passed"], "detail": raw_gate["detail"]}
    falsifiers = document["falsifiers"]
    if not isinstance(falsifiers, list) or not all(
        isinstance(item, str) and item.strip() for item in falsifiers
    ):
        raise EvidenceError("falsifiers must be a list of nonempty strings")
    if len(falsifiers) != len(set(falsifiers)):
        raise EvidenceError("falsifiers must not contain duplicates")
    raw_episodes = document["episodes"]
    if not isinstance(raw_episodes, list):
        raise EvidenceError("episodes must be a list")
    return ParsedEvidence(
        episodes=tuple(_parse_evidence_episode(raw, index) for index, raw in enumerate(raw_episodes)),
        validity_gates=gates,
        falsifiers=tuple(falsifiers),
    )


def count_windows(frames: Sequence[int]) -> int:
    return sum(index == 0 or frame != frames[index - 1] + 1 for index, frame in enumerate(frames))


def evidence_integrity_problems(evidence: ParsedEvidence) -> list[str]:
    problems = [
        f"gate:{gate_id}:{gate['detail']}"
        for gate_id, gate in evidence.validity_gates.items()
        if not gate["passed"]
    ]
    problems.extend(f"falsifier:{item}" for item in evidence.falsifiers)
    counts = collections.Counter(episode.cell for episode in evidence.episodes)
    expected = expected_cells()
    missing = sorted(expected - set(counts))
    duplicates = sorted(cell for cell, count in counts.items() if count != 1)
    if missing:
        problems.append(f"G7:missing-analytic-cells:{len(missing)}")
    if duplicates:
        problems.append(f"G7:duplicate-analytic-cells:{len(duplicates)}")
    if len(evidence.episodes) != len(expected):
        problems.append(f"G7:episode-count:{len(evidence.episodes)}/{len(expected)}")
    if missing or duplicates:
        return problems
    by_cell = {episode.cell: episode for episode in evidence.episodes}
    for episode in evidence.episodes:
        scheduled = set(episode.scheduled_brake_frames)
        realized = set(episode.realized_brake_frames)
        if episode.arm in BLIND_ARMS:
            if not scheduled:
                problems.append(f"G3:no-schedule-support:{episode.cell}")
            if not realized <= scheduled:
                problems.append(f"G3:realized-outside-schedule:{episode.cell}")
            if episode.realized_release_frames:
                problems.append(f"G3:blind-release-row:{episode.cell}")
        elif scheduled:
            problems.append(f"G3:nonblind-scheduled-row:{episode.cell}")
        if episode.arm == OFF_ARM and (realized or episode.realized_release_frames):
            problems.append(f"G2:off-intervention-row:{episode.cell}")
    for arm, by_class in SCHEDULED_BUDGETS.items():
        for scenario_class, budget in by_class.items():
            actual = sum(
                len(episode.scheduled_brake_frames)
                for episode in evidence.episodes
                if episode.arm == arm and episode.scenario_class == scenario_class
            )
            if actual != budget:
                problems.append(f"G3:budget:{arm}:{scenario_class}:{actual}/{budget}")
    for scenario_class, pair, run in canonical_pair_runs():
        schedules = [
            set(by_cell[(arm, scenario_class, pair, run)].scheduled_brake_frames)
            for arm in BLIND_ARMS
        ]
        if not all(left <= right for left, right in zip(schedules, schedules[1:])):
            problems.append(f"G3:not-nested:{scenario_class}:{pair}:{run}")
    union_brakes = sum(
        len(episode.realized_brake_frames) for episode in evidence.episodes if episode.arm == UNION_ARM
    )
    union_releases = sum(
        len(episode.realized_release_frames) for episode in evidence.episodes if episode.arm == UNION_ARM
    )
    if union_brakes != EXPECTED_UNION_BRAKES:
        problems.append(f"G6:union-brakes:{union_brakes}/{EXPECTED_UNION_BRAKES}")
    if union_releases != EXPECTED_UNION_RELEASES:
        problems.append(f"G6:union-releases:{union_releases}/{EXPECTED_UNION_RELEASES}")
    return problems


def _schema_mean(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        raise EvidenceError("internal empty mean")
    return math.fsum(materialized) / len(materialized)


def derive_pair_values(
    evidence: ParsedEvidence,
) -> tuple[dict[tuple[str, str, str], dict[str, float]], dict[Cell, dict[str, float]]]:
    by_cell = {episode.cell: episode for episode in evidence.episodes}
    episode_values: dict[Cell, dict[str, float]] = {}
    pair_values: dict[tuple[str, str, str], dict[str, float]] = {}
    for scenario_class, pair in canonical_pairs():
        off_q16 = _schema_mean(
            q16_distance(by_cell[(OFF_ARM, scenario_class, pair, run)].ego_points) for run in RUNS
        )
        off_full = _schema_mean(
            path_distance(by_cell[(OFF_ARM, scenario_class, pair, run)].ego_points) for run in RUNS
        )
        if off_q16 <= 0.0 or off_full <= 0.0:
            raise EvidenceError(f"fresh OFF denominator is nonpositive for {scenario_class}/{pair}")
        for arm in ARMS:
            for run in RUNS:
                episode = by_cell[(arm, scenario_class, pair, run)]
                q16_raw = q16_distance(episode.ego_points)
                raw_path = path_distance(episode.ego_points)
                episode_values[(arm, scenario_class, pair, run)] = {
                    "ncap": episode.ncap_score,
                    "impact_speed": episode.impact_speed,
                    "q16_raw": q16_raw,
                    "q16": min(1.0, q16_raw / off_q16),
                    "raw_path": raw_path,
                    "legacy_safe_progress": episode.ncap_score * min(1.0, raw_path / off_full),
                    "collision": float(episode.collision),
                    "episode_frame_count": float(episode.episode_frame_count),
                }
            rows = [episode_values[(arm, scenario_class, pair, run)] for run in RUNS]
            pair_values[(arm, scenario_class, pair)] = {
                metric: _schema_mean(row[metric] for row in rows)
                for metric in rows[0]
            }
    return pair_values, episode_values


def class_equal_arm_mean(
    pair_values: Mapping[tuple[str, str, str], Mapping[str, float]], arm: str, metric: str
) -> float:
    return _schema_mean(
        _schema_mean(
            pair_values[(arm, scenario_class, pair)][metric]
            for pair in CLASS_PAIRS[scenario_class]
        )
        for scenario_class in CLASSES
    )


def contrast_keys() -> tuple[tuple[str, str], ...]:
    return tuple((arm, metric) for arm in BLIND_ARMS for metric in ("ncap", "q16"))


def class_stratified_contrast_draws(
    pair_values: Mapping[tuple[str, str, str], Mapping[str, float]],
    draw_count: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], list[float]]]:
    if draw_count <= 0:
        raise ValueError("draw_count must be positive")
    keys = contrast_keys()
    points = {
        (arm, metric): class_equal_arm_mean(pair_values, UNION_ARM, metric)
        - class_equal_arm_mean(pair_values, arm, metric)
        for arm, metric in keys
    }
    differences = {
        (scenario_class, arm, metric): [
            pair_values[(UNION_ARM, scenario_class, pair)][metric]
            - pair_values[(arm, scenario_class, pair)][metric]
            for pair in CLASS_PAIRS[scenario_class]
        ]
        for scenario_class in CLASSES
        for arm, metric in keys
    }
    output = {key: [] for key in keys}
    rng = random.Random(seed)
    for _ in range(draw_count):
        selected = {
            scenario_class: [rng.randrange(len(CLASS_PAIRS[scenario_class])) for _ in CLASS_PAIRS[scenario_class]]
            for scenario_class in CLASSES
        }
        for arm, metric in keys:
            output[(arm, metric)].append(
                _schema_mean(
                    _schema_mean(
                        differences[(scenario_class, arm, metric)][index]
                        for index in selected[scenario_class]
                    )
                    for scenario_class in CLASSES
                )
            )
    return points, output


def canonical_interval(draws: Sequence[float]) -> dict[str, Any]:
    if len(draws) != BOOTSTRAP_DRAWS:
        raise ValueError(f"canonical inference requires exactly {BOOTSTRAP_DRAWS} draws")
    ordered = sorted(draws)
    return {
        "one_sided_lcb": ordered[ONE_SIDED_LOWER_INDEX],
        "one_sided_ucb": ordered[ONE_SIDED_UPPER_INDEX],
        "two_sided_95": [ordered[TWO_SIDED_LOWER_INDEX], ordered[TWO_SIDED_UPPER_INDEX]],
    }


def simultaneous_max_t_intervals(
    points: Mapping[tuple[str, str], float],
    draws: Mapping[tuple[str, str], Sequence[float]],
) -> tuple[float, dict[tuple[str, str], dict[str, float]]]:
    keys = contrast_keys()
    if set(points) != set(keys) or set(draws) != set(keys):
        raise ValueError("max-|T| family must contain exactly the frozen eight contrasts")
    if any(len(draws[key]) != BOOTSTRAP_DRAWS for key in keys):
        raise ValueError(f"max-|T| family requires exactly {BOOTSTRAP_DRAWS} draws per contrast")
    standard_errors = {key: statistics.stdev(draws[key]) for key in keys}
    active = [key for key in keys if standard_errors[key] != 0.0]
    if active:
        maxima = [
            max(abs((draws[key][index] - points[key]) / standard_errors[key]) for key in active)
            for index in range(BOOTSTRAP_DRAWS)
        ]
        critical = sorted(maxima)[MAX_T_CRITICAL_INDEX]
    else:
        critical = 0.0
    intervals = {}
    for key in keys:
        se = standard_errors[key]
        radius = 0.0 if se == 0.0 else critical * se
        intervals[key] = {"se": se, "lower": points[key] - radius, "upper": points[key] + radius}
    return critical, intervals


def primary_from_statistics(
    points: Mapping[tuple[str, str], float], draws: Mapping[tuple[str, str], Sequence[float]]
) -> PrimaryInference:
    ncap = canonical_interval(draws[("blind_1_0x", "ncap")])
    q16 = canonical_interval(draws[("blind_1_0x", "q16")])
    return PrimaryInference(
        delta_ncap=points[("blind_1_0x", "ncap")],
        lcb_ncap=ncap["one_sided_lcb"],
        ucb_ncap=ncap["one_sided_ucb"],
        ci_ncap=tuple(ncap["two_sided_95"]),
        delta_q16=points[("blind_1_0x", "q16")],
        lcb_q16=q16["one_sided_lcb"],
        ucb_q16=q16["one_sided_ucb"],
        ci_q16=tuple(q16["two_sided_95"]),
    )


def frontier_from_intervals(
    points: Mapping[tuple[str, str], float],
    intervals: Mapping[tuple[str, str], Mapping[str, float]],
) -> tuple[FrontierInference, ...]:
    return tuple(
        FrontierInference(
            arm=arm,
            delta_ncap=points[(arm, "ncap")],
            interval_ncap=(intervals[(arm, "ncap")]["lower"], intervals[(arm, "ncap")]["upper"]),
            delta_q16=points[(arm, "q16")],
            interval_q16=(intervals[(arm, "q16")]["lower"], intervals[(arm, "q16")]["upper"]),
        )
        for arm in BLIND_ARMS
    )


def frontier_competitive(item: FrontierInference) -> bool:
    return item.interval_ncap[1] < NCAP_MARGIN and item.interval_q16[1] < BLIND_Q16_COMPETITIVE_UPPER


def frontier_dominates(item: FrontierInference) -> bool:
    return frontier_competitive(item) and (
        (item.delta_ncap <= -NCAP_MARGIN and item.interval_ncap[1] < 0.0)
        or (item.delta_q16 <= Q16_NONINFERIORITY_MARGIN and item.interval_q16[1] < 0.0)
    )


def primary_competitive(primary: PrimaryInference) -> bool:
    return primary.ucb_ncap < NCAP_MARGIN and primary.ucb_q16 < BLIND_Q16_COMPETITIVE_UPPER


def primary_reverse_dominates(primary: PrimaryInference) -> bool:
    return primary_competitive(primary) and (
        (primary.delta_ncap <= -NCAP_MARGIN and primary.ucb_ncap < 0.0)
        or (primary.delta_q16 <= Q16_NONINFERIORITY_MARGIN and primary.ucb_q16 < 0.0)
    )


def primary_semantic_confirmed(primary: PrimaryInference) -> bool:
    return (
        primary.delta_ncap >= NCAP_MARGIN
        and primary.lcb_ncap > 0.0
        and primary.lcb_q16 > Q16_NONINFERIORITY_MARGIN
    )


def select_verdict(
    validity_ok: bool,
    primary: PrimaryInference | None,
    frontier: Sequence[FrontierInference],
) -> tuple[str, str | None]:
    if not validity_ok:
        return "PLACEBO_DOSE_INFRA_NULL", None
    if primary is None or len(frontier) != len(BLIND_ARMS):
        raise ValueError("valid inference requires one primary and the complete four-dose frontier")
    any_dominance = any(frontier_dominates(item) for item in frontier)
    any_competitive = any(frontier_competitive(item) for item in frontier)
    if any_dominance:
        qualifier = "BLIND_FRONTIER_DOMINATES"
    elif any_competitive:
        qualifier = "BLIND_FRONTIER_COMPETITIVE"
    else:
        qualifier = "NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED"
    if primary_reverse_dominates(primary) or any_dominance:
        verdict = "GENERIC_BRAKING_DOMINATES"
    elif primary_semantic_confirmed(primary):
        verdict = "SEMANTIC_MATCHED_BUDGET_CONFIRMED"
    elif primary_competitive(primary):
        verdict = "BLIND_MATCHED_BUDGET_COMPETITIVE"
    else:
        verdict = "MATCHED_BUDGET_INCONCLUSIVE"
    return verdict, qualifier


def _normalized_arm_report(
    arm: str,
    evidence: ParsedEvidence,
    pair_values: Mapping[tuple[str, str, str], Mapping[str, float]],
) -> dict[str, Any]:
    metrics = tuple(next(iter(pair_values.values())))
    by_class = {
        scenario_class: {
            metric: _schema_mean(
                pair_values[(arm, scenario_class, pair)][metric]
                for pair in CLASS_PAIRS[scenario_class]
            )
            for metric in metrics
        }
        for scenario_class in CLASSES
    }
    arm_episodes = [episode for episode in evidence.episodes if episode.arm == arm]
    scheduled = sum(len(episode.scheduled_brake_frames) for episode in arm_episodes)
    realized = sum(len(episode.realized_brake_frames) for episode in arm_episodes)
    return {
        "aggregate": {
            metric: _schema_mean(by_class[scenario_class][metric] for scenario_class in CLASSES)
            for metric in metrics
        },
        "per_class": by_class,
        "pairs": {
            scenario_class: {
                pair: dict(pair_values[(arm, scenario_class, pair)])
                for pair in CLASS_PAIRS[scenario_class]
            }
            for scenario_class in CLASSES
        },
        "scheduled_brake_frames": scheduled,
        "scheduled_brake_windows": sum(count_windows(row.scheduled_brake_frames) for row in arm_episodes),
        "realized_brake_frames": realized,
        "realized_brake_windows": sum(count_windows(row.realized_brake_frames) for row in arm_episodes),
        "realized_release_frames": sum(len(row.realized_release_frames) for row in arm_episodes),
        "realization_fraction": realized / scheduled if scheduled else None,
        "intervention_free_realized_episode_fraction": _schema_mean(
            float(not row.realized_brake_frames) for row in arm_episodes
        ),
        "terminal_reason_counts": dict(
            sorted(collections.Counter(row.terminal_reason for row in arm_episodes).items())
        ),
    }


def analyze_evidence(document: Any) -> dict[str, Any]:
    evidence = parse_evidence(document)
    problems = evidence_integrity_problems(evidence)
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "input_schema": EVIDENCE_SCHEMA,
        "expected_episodes": 2_400,
        "observed_episode_rows": len(evidence.episodes),
        "validity_gates": evidence.validity_gates,
        "falsifiers": list(evidence.falsifiers),
        "problem_count": len(problems),
        "problems": problems,
    }
    if problems:
        report.update(
            {
                "verdict": "PLACEBO_DOSE_INFRA_NULL",
                "qualifier": None,
                "headline": "PLACEBO_DOSE_INFRA_NULL",
                "primary": None,
                "secondary_frontier": None,
                "arms": None,
                "episode_disclosures": None,
            }
        )
        return report
    try:
        pair_values, _episode_values = derive_pair_values(evidence)
    except EvidenceError as error:
        problems.append(f"G7:outcome-derivation:{error}")
        report.update(
            {
                "problem_count": len(problems),
                "problems": problems,
                "verdict": "PLACEBO_DOSE_INFRA_NULL",
                "qualifier": None,
                "headline": "PLACEBO_DOSE_INFRA_NULL",
                "primary": None,
                "secondary_frontier": None,
                "arms": None,
                "episode_disclosures": None,
            }
        )
        return report
    points, draws = class_stratified_contrast_draws(
        pair_values, draw_count=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED
    )
    primary = primary_from_statistics(points, draws)
    critical, simultaneous = simultaneous_max_t_intervals(points, draws)
    frontier = frontier_from_intervals(points, simultaneous)
    verdict, qualifier = select_verdict(True, primary, frontier)
    report.update(
        {
            "verdict": verdict,
            "qualifier": qualifier,
            "headline": f"{verdict} — {qualifier}",
            "primary": {
                "delta_ncap": primary.delta_ncap,
                "ncap_one_sided_lcb": primary.lcb_ncap,
                "ncap_one_sided_ucb": primary.ucb_ncap,
                "ncap_two_sided_95": list(primary.ci_ncap),
                "delta_q16": primary.delta_q16,
                "q16_one_sided_lcb": primary.lcb_q16,
                "q16_one_sided_ucb": primary.ucb_q16,
                "q16_two_sided_95": list(primary.ci_q16),
                "semantic_confirmed": primary_semantic_confirmed(primary),
                "blind_competitive": primary_competitive(primary),
                "blind_reverse_dominates": primary_reverse_dominates(primary),
            },
            "simultaneous_max_t_critical": critical,
            "secondary_frontier": [
                {
                    "arm": item.arm,
                    "delta_ncap": item.delta_ncap,
                    "simultaneous_ncap_95": list(item.interval_ncap),
                    "se_ncap": simultaneous[(item.arm, "ncap")]["se"],
                    "delta_q16": item.delta_q16,
                    "simultaneous_q16_95": list(item.interval_q16),
                    "se_q16": simultaneous[(item.arm, "q16")]["se"],
                    "competitive": frontier_competitive(item),
                    "pareto_dominates": frontier_dominates(item),
                }
                for item in frontier
            ],
            "arms": {arm: _normalized_arm_report(arm, evidence, pair_values) for arm in ARMS},
            "dose_curve": {
                "form": "ascending_assigned_dose_straight_line_segments_only",
                "points": [
                    {
                        "arm": arm,
                        "ncap": class_equal_arm_mean(pair_values, arm, "ncap"),
                        "q16": class_equal_arm_mean(pair_values, arm, "q16"),
                    }
                    for arm in BLIND_ARMS
                ],
            },
            "episode_disclosures": [
                {
                    "arm": row.arm,
                    "scenario_class": row.scenario_class,
                    "pair": row.pair,
                    "run": row.run,
                    "scheduled_brake_frames": len(row.scheduled_brake_frames),
                    "scheduled_brake_windows": count_windows(row.scheduled_brake_frames),
                    "realized_brake_frames": len(row.realized_brake_frames),
                    "realized_brake_windows": count_windows(row.realized_brake_frames),
                    "realized_release_frames": len(row.realized_release_frames),
                    "realization_fraction": (
                        len(row.realized_brake_frames) / len(row.scheduled_brake_frames)
                        if row.scheduled_brake_frames
                        else None
                    ),
                    "intervention_free_realized_episode": not row.realized_brake_frames,
                    "episode_frame_count": row.episode_frame_count,
                    "collision": row.collision,
                    "terminal_reason": row.terminal_reason,
                }
                for row in evidence.episodes
            ],
        }
    )
    return report


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    problems: list[str] = []
    caught_errors = (AnalysisInputError, KeyError, OSError, TypeError, ValueError)

    try:
        decision_paths = parse_decision_arguments(args.decision_log)
    except caught_errors as error:
        problems.append(f"decision-arguments:{type(error).__name__}:{error}")
        decision_paths = {arm: [] for arm in ARMS}

    try:
        manifest_raw, manifest_problems = validate_manifest_bindings(
            args.launch_manifest, args.schedule
        )
    except caught_errors as error:
        manifest_raw = {}
        manifest_problems = [f"manifest:unreadable:{type(error).__name__}:{error}"]
    problems.extend(manifest_problems)

    try:
        schedule, schedule_problems, schedule_raw = load_schedule(args.schedule)
    except caught_errors as error:
        schedule, schedule_raw = {}, {}
        schedule_problems = [f"schedule:unreadable:{type(error).__name__}:{error}"]
    problems.extend(schedule_problems)

    try:
        receipt_gates, receipt_problems, receipt_raw = validate_receipt(
            args.validity_receipt, args.launch_manifest
        )
    except caught_errors as error:
        receipt_gates = {f"G{index}": False for index in range(10)}
        receipt_raw = {}
        receipt_problems = [f"receipt:unreadable:{type(error).__name__}:{error}"]
    problems.extend(receipt_problems)

    try:
        proof_receipt_raw, proof_receipt_problems = validate_committed_proof_receipt(
            args.proof_commit_receipt,
            args.launch_manifest,
            args,
            decision_paths,
        )
    except caught_errors as error:
        proof_receipt_raw = {}
        proof_receipt_problems = [
            f"proof-receipt:unreadable:{type(error).__name__}:{error}"
        ]
    problems.extend(proof_receipt_problems)

    try:
        scores, log_problems, marker_order = parse_i135_log(args.i135_log)
    except caught_errors as error:
        scores, marker_order = {}, []
        log_problems = [f"i135-log:unreadable:{type(error).__name__}:{error}"]
    problems.extend(log_problems)
    try:
        artifacts, run_problems = load_run_artifacts(
            args.i135_runs, ARM_DIRS, expected_cells()
        )
    except caught_errors as error:
        artifacts = {}
        run_problems = [f"runs:unreadable:{type(error).__name__}:{error}"]
    problems.extend(run_problems)
    episodes, assembly_problems = assemble_episodes(scores, artifacts)
    problems.extend(assembly_problems)

    oracle_verified = True
    try:
        verify_frozen_oracle_inputs(args)
    except caught_errors as error:
        oracle_verified = False
        problems.append(f"oracle:{type(error).__name__}:{error}")
    if oracle_verified:
        try:
            oracle_scores, oracle_log_problems = parse_i134_oracle_log(args.oracle_log)
        except caught_errors as error:
            oracle_scores = {}
            oracle_log_problems = [f"log-unreadable:{type(error).__name__}:{error}"]
        problems.extend(f"oracle:{problem}" for problem in oracle_log_problems)
    else:
        oracle_scores = {}
    oracle_cells = expected_cells(("off_baseline", "released_union_semantic_reference"))
    if oracle_verified:
        try:
            oracle_artifacts, oracle_run_problems = load_run_artifacts(
                args.oracle_runs, ORACLE_DIRS, oracle_cells
            )
        except caught_errors as error:
            oracle_artifacts = {}
            oracle_run_problems = [f"runs-unreadable:{type(error).__name__}:{error}"]
        problems.extend(f"oracle:{problem}" for problem in oracle_run_problems)
    else:
        oracle_artifacts = {}

    decisions: dict[str, ParsedDecisionLog] = {}
    for arm in ARMS:
        try:
            if arm in BLIND_ARMS:
                parsed = parse_blind_decisions(arm, decision_paths[arm], schedule)
            else:
                parsed = parse_semantic_decisions(arm, decision_paths[arm])
        except caught_errors as error:
            parsed = ParsedDecisionLog({}, [], 0, 0)
            problems.append(f"decision:{arm}:unreadable:{type(error).__name__}:{error}")
        decisions[arm] = parsed
        problems.extend(parsed.problems)
    if oracle_verified:
        try:
            oracle_union = parse_legacy_oracle_semantic_decisions(args.oracle_union_log)
        except caught_errors as error:
            oracle_union = ParsedDecisionLog({}, [], 0, 0)
            problems.append(f"oracle:union-unreadable:{type(error).__name__}:{error}")
        problems.extend(f"oracle:{problem}" for problem in oracle_union.problems)
    else:
        oracle_union = ParsedDecisionLog({}, [], 0, 0)

    if oracle_verified:
        try:
            g6_pass, g6_problems = drift_gate(
                scores,
                artifacts,
                oracle_scores,
                oracle_artifacts,
                decisions["released_union_semantic_reference"],
                oracle_union,
            )
        except caught_errors as error:
            g6_pass = False
            g6_problems = [f"g6:not-evaluable:{type(error).__name__}:{error}"]
    else:
        g6_pass = False
        g6_problems = ["g6:not-evaluable:frozen-oracle-provenance-failed"]
    problems.extend(g6_problems)
    g7_pass = (
        len(scores) == 2_400
        and len(artifacts) == 2_400
        and len(episodes) == 2_400
        and marker_order == expected_execution_order()
    )
    if not g7_pass:
        problems.append("g7:completion-or-order-failed")

    gates = dict(receipt_gates)
    gates["G0"] = gates.get("G0", False) and not manifest_problems and not proof_receipt_problems
    gates["G3"] = gates.get("G3", False) and not schedule_problems
    gates["G6"] = g6_pass
    gates["G7"] = g7_pass
    for arm, parsed in decisions.items():
        if parsed.problems:
            gates["G7"] = False
            problems.append(f"g7:decision-integrity:{arm}")

    infrastructure_valid = all(gates.get(f"G{index}", False) for index in range(10)) and not problems
    if not infrastructure_valid:
        return infra_null_report(
            problems=problems,
            gates=gates,
            context={
                "manifest_schema": manifest_raw.get("schema"),
                "schedule_schema": schedule_raw.get("schema"),
                "validity_receipt_schema": receipt_raw.get("schema"),
                "dataset_provenance": receipt_raw.get("dataset_provenance"),
                "docker_runtime_provenance": receipt_raw.get("docker_runtime_provenance"),
                "analytic_lock_provenance": receipt_raw.get("analytic_lock_provenance"),
                "proof_commit_receipt_schema": proof_receipt_raw.get("schema"),
                "proof_commit": proof_receipt_raw.get("proof_commit"),
                "observed_scores": len(scores),
                "observed_run_artifacts": len(artifacts),
                "assembled_episodes": len(episodes),
                "execution_markers": len(marker_order),
            },
        )

    try:
        pair_tables, episode_values = make_metric_tables(episodes)
        summaries = arm_summaries(pair_tables)
        bootstrap_draws = class_stratified_draws(pair_tables)
        primary, frontier = primary_and_frontier(pair_tables, bootstrap_draws)
        verdict, qualifier = decide_verdict(True, primary, frontier)
        sensitivity = sensitivity_report(pair_tables, episode_values, primary)
        realization = make_realization_report(schedule, decisions)
    except caught_errors as error:
        return infra_null_report(
            problems=[f"pre-inference-integrity:{type(error).__name__}:{error}"],
            gates={**gates, "G7": False},
            context={
                "manifest_schema": manifest_raw.get("schema"),
                "schedule_schema": schedule_raw.get("schema"),
                "validity_receipt_schema": receipt_raw.get("schema"),
                "dataset_provenance": receipt_raw.get("dataset_provenance"),
                "docker_runtime_provenance": receipt_raw.get("docker_runtime_provenance"),
                "analytic_lock_provenance": receipt_raw.get("analytic_lock_provenance"),
                "proof_commit_receipt_schema": proof_receipt_raw.get("schema"),
                "proof_commit": proof_receipt_raw.get("proof_commit"),
                "observed_scores": len(scores),
                "observed_run_artifacts": len(artifacts),
                "assembled_episodes": len(episodes),
                "execution_markers": len(marker_order),
            },
        )
    dose_curve = {
        "interpolation": "straight_line_segments_only",
        "points": [
            {
                "assigned_dose": dose,
                "arm": arm,
                "ncap": summaries[arm]["aggregate_equal_class"]["ncap"],
                "q16": summaries[arm]["aggregate_equal_class"]["q16"],
            }
            for dose, arm in zip((0.5, 1.0, 1.5, 2.0), BLIND_ARMS)
        ],
    }

    episode_rows = []
    for cell in expected_execution_order():
        # The order list contains each cell once and preserves the frozen temporal execution order.
        episode = episodes[cell]
        arm, cls, seq, run = cell
        decision = decisions[arm].cells[cell]
        terminal_reason = "collision" if episode.collision else "benchmark_noncollision_terminal"
        episode_rows.append(
            {
                "arm": arm,
                "class": cls,
                "pair": seq,
                "run": run,
                "ncap": episode.ncap,
                "impact_speed": episode.impact_speed,
                "q16_distance_m": episode.q16_distance,
                "raw_path_length_m": episode.raw_path_length,
                "collision": episode.collision,
                "terminal_reason": terminal_reason,
                "episode_frame_count": len(decision.frames),
                "scheduled_brake_frames": (
                    list(schedule[cell]["brake_frames"]) if arm in BLIND_ARMS else None
                ),
                "realized_brake_frames": sorted(decision.brakes),
                "realized_brake_windows": contiguous_window_count(decision.brakes),
            }
        )

    all_digest_paths: dict[str, Sequence[str | pathlib.Path]] = {
        "i135_log": [args.i135_log],
        "schedule": [args.schedule],
        "launch_manifest": [args.launch_manifest],
        "validity_receipt": [args.validity_receipt],
        "proof_commit_receipt": [args.proof_commit_receipt],
        "oracle_log": [args.oracle_log],
        "oracle_union_log": args.oracle_union_log,
        **{
            role: [pathlib.Path(args.validity_receipt).parent / filename]
            for role, filename in RUNTIME_EVIDENCE_FILENAMES.items()
        },
    }
    all_digest_paths.update({f"decision_{arm}": paths for arm, paths in decision_paths.items()})
    headline = verdict if qualifier is None else f"{verdict} — {qualifier}"
    return {
        "schema": "iter135.neuroncap_blind_braking_dose_response_report.v1",
        "headline": headline,
        "verdict": verdict,
        "frontier_qualifier": qualifier,
        "claim_boundary": "fixed public 20-pair NeuroNCAP suite only",
        "infrastructure_valid": infrastructure_valid,
        "problem_count": len(problems),
        "problems": problems,
        "validity_gates": {gate: {"pass": passed} for gate, passed in sorted(gates.items())},
        "method": {
            "population_unit": "scenario_pair",
            "within_pair_runs": NRUNS,
            "class_pair_counts": {cls: len(CLASS_PAIRS[cls]) for cls in CLASSES},
            "bootstrap": "paired class-stratified 10/5/5",
            "draws": BOOT_DRAWS,
            "seed": BOOT_SEED,
            "one_sided_lcb_index": LCB_INDEX,
            "one_sided_ucb_index": UCB_INDEX,
            "two_sided_indices": [CI_LO_INDEX, CI_HI_INDEX],
            "max_abs_t_index": MAX_T_INDEX,
            "q16": "sum translation over at most first 16 sorted ego poses; early terminal absorbing",
        },
        "input_sha256": input_digest_report(all_digest_paths),
        "run_sources": {
            "i135": {"path": str(args.i135_runs), **source_digest(args.i135_runs)},
            "oracle_i134": {"path": str(args.oracle_runs), **source_digest(args.oracle_runs)},
        },
        "receipt_schema": receipt_raw.get("schema"),
        "dataset_provenance": receipt_raw.get("dataset_provenance"),
        "docker_runtime_provenance": receipt_raw.get("docker_runtime_provenance"),
        "analytic_lock_provenance": receipt_raw.get("analytic_lock_provenance"),
        "proof_commit_receipt_schema": proof_receipt_raw.get("schema"),
        "proof_commit": proof_receipt_raw.get("proof_commit"),
        "schedule_schema": schedule_raw.get("schema"),
        "arm_summary": summaries,
        "episode_rows_in_frozen_execution_order": episode_rows,
        "dose_realization": realization,
        "primary": primary,
        "simultaneous_frontier": frontier,
        "blind_dose_curve": dose_curve,
        "sensitivity": sensitivity,
    }


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(description=__doc__)
    out.add_argument("--i135-log", required=True)
    out.add_argument("--i135-runs", required=True)
    out.add_argument("--schedule", required=True)
    out.add_argument("--launch-manifest", required=True)
    out.add_argument("--validity-receipt", required=True)
    out.add_argument("--proof-commit-receipt", required=True)
    out.add_argument("--decision-log", action="append", default=[], metavar="ARM=PATH")
    out.add_argument("--oracle-log", required=True)
    out.add_argument("--oracle-runs", required=True)
    out.add_argument("--oracle-union-log", action="append", required=True)
    out.add_argument("--out", required=True)
    return out


def infra_null_report(
    error: Exception | None = None,
    *,
    problems: Sequence[str] | None = None,
    gates: Mapping[str, bool] | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    diagnostics = list(problems or ())
    if error is not None:
        diagnostics.append(f"raw-trust-boundary:{type(error).__name__}:{error}")
    if not diagnostics:
        diagnostics.append("raw-trust-boundary:unspecified-infrastructure-failure")
    gate_values = {
        f"G{index}": bool(gates and gates.get(f"G{index}", False)) for index in range(10)
    }
    report = {
        "schema": "iter135.neuroncap_blind_braking_dose_response_report.v1",
        "headline": "PLACEBO_DOSE_INFRA_NULL",
        "verdict": "PLACEBO_DOSE_INFRA_NULL",
        "frontier_qualifier": None,
        "claim_boundary": "fixed public 20-pair NeuroNCAP suite only",
        "infrastructure_valid": False,
        "problem_count": len(diagnostics),
        "problems": diagnostics,
        "validity_gates": {
            gate: {"pass": passed} for gate, passed in sorted(gate_values.items())
        },
        "analysis_status": "INFERENCE_NOT_RUN",
        "analysis_skip_reason": "pre-inference trust or completeness gate failed",
        "diagnostic_context": dict(context or {}),
        "arm_summary": None,
        "episode_rows_in_frozen_execution_order": None,
        "dose_realization": None,
        "primary": None,
        "simultaneous_frontier": None,
        "blind_dose_curve": None,
        "sensitivity": None,
    }
    return report


def _toctou_null_report(
    report: Mapping[str, Any],
    initial: Mapping[str, tuple[str, str, int]],
    final: Mapping[str, tuple[str, str, int]],
) -> dict[str, Any]:
    changed = sorted(
        role for role in set(initial) | set(final) if initial.get(role) != final.get(role)
    )
    if not changed:
        return dict(report)
    prior_problems = report.get("problems")
    diagnostics = list(prior_problems) if isinstance(prior_problems, list) else []
    diagnostics.append(f"input-toctou:post-verification-mutation:{','.join(changed)}")
    gate_rows = report.get("validity_gates")
    gates = {
        gate: isinstance(row, dict) and row.get("pass") is True
        for gate, row in gate_rows.items()
    } if isinstance(gate_rows, dict) else {}
    gates["G0"] = False
    gates["G7"] = False
    return infra_null_report(problems=diagnostics, gates=gates)


def _write_report_temp(output: pathlib.Path, report: Mapping[str, Any]) -> pathlib.Path:
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = pathlib.Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        initial_input_state = capture_analysis_input_state(args)
    except Exception as error:
        initial_input_state = {}
        fingerprint_error: Exception | None = error
    else:
        fingerprint_error = None
    try:
        report = build_report(args)
    except Exception as error:
        report = infra_null_report(error)
    if fingerprint_error is not None:
        report = infra_null_report(
            problems=[
                *list(report.get("problems", [])),
                f"input-fingerprint:{type(fingerprint_error).__name__}:{fingerprint_error}",
            ]
        )
    try:
        output = pathlib.Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = _write_report_temp(output, report)
        try:
            try:
                final_input_state = capture_analysis_input_state(args)
            except Exception as error:
                report = infra_null_report(
                    problems=[
                        *list(report.get("problems", [])),
                        f"input-final-fingerprint:{type(error).__name__}:{error}",
                    ]
                )
            else:
                report = _toctou_null_report(report, initial_input_state, final_input_state)
            if report.get("verdict") == "PLACEBO_DOSE_INFRA_NULL" and (
                json.loads(temporary.read_text(encoding="utf-8")) != report
            ):
                temporary.unlink()
                temporary = _write_report_temp(output, report)
            os.replace(temporary, output)
            directory_fd = os.open(output.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    except (OSError, TypeError, ValueError) as error:
        fallback = {
            "schema": "iter135.analyzer_output_failure.v1",
            "stage": "write-report",
            "error": f"{type(error).__name__}:{error}",
            "report": report,
        }
        print(json.dumps(fallback, sort_keys=True), file=sys.stderr)
        return 3
    print(f"=== iteration 135: {report['headline']} ===")
    print(f"  infrastructure valid: {report['infrastructure_valid']}")
    print(f"  problems: {report['problem_count']}")
    sensitivity = report.get("sensitivity")
    if sensitivity:
        print(f"  sensitivity disagreement: {sensitivity['any_disagreement']}")
        for name, row in sensitivity["methods"].items():
            print(f"    {name}: disagrees={row['disagrees_with_primary']}")
    for problem in report.get("problems", [])[:20]:
        print(f"  problem: {problem}")
    return 0 if report.get("infrastructure_valid") is True else 2


if __name__ == "__main__":
    sys.exit(main())
