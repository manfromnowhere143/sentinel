#!/usr/bin/env python3
"""Extract Iteration-134 released-union frame and braking-window support.

The committed decision log is one gzip member split at arbitrary byte boundaries.  The parser
therefore presents the ordered shards as one binary stream before gzip decoding; opening shards
as independent gzip files would be incorrect.  Parsing is strict and frame indices follow the
Iteration-135 preregistration: frame ``k`` is the zero-based frame row after reset, and a brake row
emitted after that frame assigns brake frame ``k``.

Usage:
    extract_union_windows.py OUT.json LOG.jsonl.gz.part-aa [LOG.jsonl.gz.part-ab ...]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import BinaryIO, Iterable, Sequence


CLASS_SEQS = {
    "stationary": ["0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"],
    "frontal": ["0103", "0106", "0110", "0346", "0923"],
    "side": ["0103", "0108", "0110", "0278", "0921"],
}
CLASSES = ["stationary", "frontal", "side"]
PAIR_ORDER = [(cls, seq) for cls in CLASSES for seq in CLASS_SEQS[cls]]
RUNS = 20
EXPECTED_BLOCKS = len(PAIR_ORDER) * RUNS

SCHEMA = "iter135.union_windows.v1"
EXPECTED_PART_SHA256 = [
    "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
    "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
]
EXPECTED_JOINED_SHA256 = "f06178aba6d7b5fd7424469891795f039eca65dd8eb4942f0b0706ccd838a21c"
EXPECTED_COUNTS = {
    "frame_rows": 6474,
    "brake_rows": 1205,
    "release_rows": 156,
    "braking_windows": 265,
    "zero_brake_episodes": 170,
}
EXPECTED_CLASS_COUNTS = {
    "stationary": {"frame_rows": 3624, "brake_rows": 416},
    "frontal": {"frame_rows": 1347, "brake_rows": 475},
    "side": {"frame_rows": 1503, "brake_rows": 314},
}


class UnionLogError(ValueError):
    """The split union log cannot be interpreted under the frozen contract."""


class _ConcatenatedParts(io.RawIOBase):
    """Read ordered files as one non-seekable byte stream without materializing the join."""

    def __init__(self, paths: Sequence[Path]):
        super().__init__()
        self._paths = list(paths)
        self._index = 0
        self._current: BinaryIO | None = None

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def _open_current(self) -> BinaryIO | None:
        while self._current is None and self._index < len(self._paths):
            self._current = self._paths[self._index].open("rb")
        return self._current

    def readinto(self, buffer: bytearray | memoryview) -> int:
        view = memoryview(buffer).cast("B")
        written = 0
        while written < len(view):
            current = self._open_current()
            if current is None:
                break
            count = current.readinto(view[written:])
            if count:
                written += count
                continue
            current.close()
            self._current = None
            self._index += 1
        return written

    def close(self) -> None:
        if self._current is not None:
            self._current.close()
            self._current = None
        super().close()


def canonical_parts(parts: Iterable[str | Path]) -> list[Path]:
    """Return unique shards in lexical path order, independent of caller argument order."""
    paths = [Path(part) for part in parts]
    if not paths:
        raise UnionLogError("at least one split-gzip part is required")
    if len({str(path) for path in paths}) != len(paths):
        raise UnionLogError("duplicate split-gzip part")
    paths.sort(key=lambda path: str(path))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise UnionLogError(f"missing split-gzip parts: {missing}")
    return paths


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_joined(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def contiguous_windows(brake_frames: Sequence[int]) -> list[list[int]]:
    """Return maximal contiguous brake-frame windows in ascending order."""
    if not brake_frames:
        return []
    frames = sorted(brake_frames)
    if len(frames) != len(set(frames)):
        raise UnionLogError("duplicate brake frame")
    windows = [[frames[0]]]
    for frame in frames[1:]:
        if frame == windows[-1][-1] + 1:
            windows[-1].append(frame)
        else:
            windows.append([frame])
    return windows


def read_blocks(parts: Iterable[str | Path]) -> tuple[list[dict], list[Path]]:
    """Strictly stream-decode split gzip parts and return blocks in reset order."""
    paths = canonical_parts(parts)
    blocks: list[dict] = []
    current: dict | None = None

    raw = _ConcatenatedParts(paths)
    buffered = io.BufferedReader(raw, buffer_size=1 << 20)
    try:
        with gzip.GzipFile(fileobj=buffered, mode="rb") as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", errors="strict") as text:
                for line_number, line in enumerate(text, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        row = json.loads(stripped)
                    except json.JSONDecodeError as exc:
                        raise UnionLogError(f"invalid JSON at decompressed line {line_number}") from exc
                    if not isinstance(row, dict):
                        raise UnionLogError(f"non-object JSON at decompressed line {line_number}")

                    if row.get("reset") is True:
                        if set(row) != {"reset", "run"}:
                            raise UnionLogError(f"unexpected reset schema at line {line_number}")
                        run = row.get("run")
                        if not isinstance(run, int) or isinstance(run, bool):
                            raise UnionLogError(f"invalid reset run at line {line_number}")
                        current = {
                            "log_run": run,
                            "frame_count": 0,
                            "brake_frames": [],
                            "brake_row_count": 0,
                            "release_row_count": 0,
                        }
                        blocks.append(current)
                        continue

                    if current is None:
                        raise UnionLogError(f"event before first reset at line {line_number}")
                    if row.get("run") != current["log_run"]:
                        raise UnionLogError(f"event/reset run mismatch at line {line_number}")

                    if "ts" in row:
                        required = {"run", "ts", "traj", "objs", "scores", "futs"}
                        if set(row) != required:
                            raise UnionLogError(f"unexpected frame schema at line {line_number}")
                        current["frame_count"] += 1
                    elif row.get("brake") is True:
                        required = {"run", "brake", "clear", "cpa", "ttc"}
                        if set(row) != required:
                            raise UnionLogError(f"unexpected brake schema at line {line_number}")
                        frame = current["frame_count"] - 1
                        if frame < 0:
                            raise UnionLogError(f"brake before first frame at line {line_number}")
                        if frame in current["brake_frames"]:
                            raise UnionLogError(f"duplicate brake frame at line {line_number}")
                        current["brake_frames"].append(frame)
                        current["brake_row_count"] += 1
                    elif row.get("release") is True:
                        required = {"run", "release", "cpa", "ttc"}
                        if set(row) != required:
                            raise UnionLogError(f"unexpected release schema at line {line_number}")
                        if current["frame_count"] == 0:
                            raise UnionLogError(f"release before first frame at line {line_number}")
                        current["release_row_count"] += 1
                    else:
                        raise UnionLogError(f"unknown union-log row at line {line_number}")
    except (gzip.BadGzipFile, EOFError, UnicodeDecodeError) as exc:
        raise UnionLogError("invalid or incomplete joined gzip stream") from exc
    finally:
        buffered.close()

    for block in blocks:
        block["brake_windows"] = contiguous_windows(block["brake_frames"])
    return blocks, paths


def extract_union_windows(
    parts: Iterable[str | Path], *, enforce_frozen_source: bool = True
) -> dict:
    """Build the canonical union-window inventory and its fail-closed receipt."""
    blocks, paths = read_blocks(parts)
    part_receipts = [{"path": str(path), "sha256": _sha256_file(path)} for path in paths]
    joined_sha256 = _sha256_joined(paths)
    problems: list[str] = []

    if len(blocks) != EXPECTED_BLOCKS:
        problems.append(f"block-count:{len(blocks)}!={EXPECTED_BLOCKS}")

    episodes: dict[str, dict] = {}
    for block_index, block in enumerate(blocks[:EXPECTED_BLOCKS]):
        cls, seq = PAIR_ORDER[block_index // RUNS]
        run = block_index % RUNS
        if block["log_run"] != run:
            problems.append(f"run-index:{cls}/{seq}/{run}:log={block['log_run']}")
        if any(frame < 0 or frame >= block["frame_count"] for frame in block["brake_frames"]):
            problems.append(f"brake-horizon:{cls}/{seq}/{run}")
        key = f"{cls}/{seq}/{run}"
        episodes[key] = {
            "class": cls,
            "seq": seq,
            "run": run,
            "frame_count": block["frame_count"],
            "brake_frames": block["brake_frames"],
            "brake_windows": block["brake_windows"],
            "brake_row_count": block["brake_row_count"],
            "release_row_count": block["release_row_count"],
        }

    totals = {
        "frame_rows": sum(block["frame_count"] for block in blocks),
        "brake_rows": sum(block["brake_row_count"] for block in blocks),
        "release_rows": sum(block["release_row_count"] for block in blocks),
        "braking_windows": sum(len(block["brake_windows"]) for block in blocks),
        "zero_brake_episodes": sum(not block["brake_frames"] for block in blocks),
    }
    per_class = {}
    for cls in CLASSES:
        class_rows = [row for row in episodes.values() if row["class"] == cls]
        per_class[cls] = {
            "episodes": len(class_rows),
            "frame_rows": sum(row["frame_count"] for row in class_rows),
            "brake_rows": sum(row["brake_row_count"] for row in class_rows),
            "release_rows": sum(row["release_row_count"] for row in class_rows),
            "braking_windows": sum(len(row["brake_windows"]) for row in class_rows),
            "zero_brake_episodes": sum(not row["brake_frames"] for row in class_rows),
        }

    if enforce_frozen_source:
        observed_part_hashes = [row["sha256"] for row in part_receipts]
        if observed_part_hashes != EXPECTED_PART_SHA256:
            problems.append("source-part-sha256")
        if joined_sha256 != EXPECTED_JOINED_SHA256:
            problems.append("source-joined-sha256")
        for name, expected in EXPECTED_COUNTS.items():
            if totals[name] != expected:
                problems.append(f"source-{name}:{totals[name]}!={expected}")
        for cls, expected_counts in EXPECTED_CLASS_COUNTS.items():
            for name, expected in expected_counts.items():
                if per_class[cls][name] != expected:
                    problems.append(f"source-{cls}-{name}:{per_class[cls][name]}!={expected}")

    report = {
        "schema": SCHEMA,
        "verdict": "UNION_WINDOWS_OK" if not problems else "UNION_WINDOWS_INVALID",
        "source_log_parts": part_receipts,
        "source_joined_sha256": joined_sha256,
        "pair_order": [f"{cls}/{seq}" for cls, seq in PAIR_ORDER],
        "runs_per_pair": RUNS,
        "block_count": len(blocks),
        "totals": totals,
        "per_class": per_class,
        "episodes": episodes,
        "problem_count": len(problems),
        "problems": problems,
    }
    return report


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("parts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        report = extract_union_windows(args.parts)
    except (OSError, UnionLogError) as exc:
        print(f"UNION_WINDOWS_INVALID: {exc}", file=sys.stderr)
        return 1
    _write_json(args.output, report)
    print(
        f"{report['verdict']} blocks={report['block_count']} "
        f"frames={report['totals']['frame_rows']} brakes={report['totals']['brake_rows']} "
        f"windows={report['totals']['braking_windows']} problems={report['problem_count']}"
    )
    return 0 if report["verdict"] == "UNION_WINDOWS_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
