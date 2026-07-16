#!/usr/bin/env python3
"""Freeze Iteration-135 model inputs and route analytic output to the evidence volume."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXPECTED_INPUT_SHA256 = "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
EXPECTED_OUTPUT_SHA256 = "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
ANCHOR = "-e SENTINEL_ENABLED -e SENTINEL_PLACEBO_PAIR -e SENTINEL_PLACEBO_SCHEDULE "
REPLACEMENT = (
    ANCHOR
    + "-e SENTINEL_DOSE_PAIR -e SENTINEL_DOSE_ID "
    + "-e SENTINEL_DOSE_SCHEDULE -e SENTINEL_RELEASE_K "
)
OUTPUT_DECLARATION_ANCHOR = 'output_name=${2:?"No output name given (for logging)"}\n'
OUTPUT_DECLARATION_REPLACEMENT = (
    OUTPUT_DECLARATION_ANCHOR
    + ': "${SENTINEL_OUTPUT_ROOT:?SENTINEL_OUTPUT_ROOT must be set}"\n'
)
OUTPUT_MOUNT_ANCHOR = "  -v $PWD:/neuro_ncap \\\n  -v $NUSCENES_PATH:$NUSCENES_PATH \\\n"
OUTPUT_MOUNT_REPLACEMENT = (
    "  -v $PWD:/neuro_ncap \\\n"
    '  --mount "type=bind,src=$SENTINEL_OUTPUT_ROOT,dst=/sentinel_output" \\\n'
    "  -v $NUSCENES_PATH:$NUSCENES_PATH:ro \\\n"
)
OUTPUT_LOG_ANCHOR = (
    "  --engine.logger.log-dir outoutput/$TIME_NOW/$output_name-$seq \\\n"
)
OUTPUT_LOG_REPLACEMENT = (
    "  --engine.logger.log-dir /sentinel_output/$TIME_NOW/$output_name-$seq \\\n"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_text(source: str) -> str:
    anchors = {
        "model env": ANCHOR,
        "output declaration": OUTPUT_DECLARATION_ANCHOR,
        "output mount": OUTPUT_MOUNT_ANCHOR,
        "output logger": OUTPUT_LOG_ANCHOR,
    }
    for label, anchor in anchors.items():
        if source.count(anchor) != 1:
            raise ValueError(f"{label} anchor count is {source.count(anchor)}, expected 1")
    patched = source.replace(ANCHOR, REPLACEMENT, 1)
    patched = patched.replace(
        OUTPUT_DECLARATION_ANCHOR, OUTPUT_DECLARATION_REPLACEMENT, 1
    )
    patched = patched.replace(OUTPUT_MOUNT_ANCHOR, OUTPUT_MOUNT_REPLACEMENT, 1)
    patched = patched.replace(OUTPUT_LOG_ANCHOR, OUTPUT_LOG_REPLACEMENT, 1)
    for name in (
        "SENTINEL_DOSE_PAIR",
        "SENTINEL_DOSE_ID",
        "SENTINEL_DOSE_SCHEDULE",
        "SENTINEL_RELEASE_K",
    ):
        if patched.count(f"-e {name}") != 1:
            raise ValueError(f"{name} was not forwarded exactly once")
    renderer, model = patched.split("if [ $SHOULD_START_MODEL == true ]; then", 1)
    if (
        "SENTINEL_DOSE_" in renderer
        or "SENTINEL_DOSE_" not in model
        or "SENTINEL_RELEASE_K" in renderer
    ):
        raise ValueError("assigned-dose and release variables must reach the model block only")
    if (
        patched.count("${SENTINEL_OUTPUT_ROOT:?") != 1
        or patched.count("src=$SENTINEL_OUTPUT_ROOT,dst=/sentinel_output") != 1
    ):
        raise ValueError("output root must be required once and mounted once")
    dataset_bind_lines = [
        line.strip()
        for line in patched.splitlines()
        if line.strip().startswith("-v $NUSCENES_PATH:$NUSCENES_PATH")
    ]
    if dataset_bind_lines != ["-v $NUSCENES_PATH:$NUSCENES_PATH:ro \\"]:
        raise ValueError(
            "nuScenes foreground bind must exist exactly once and be explicitly read-only"
        )
    if patched.count("/sentinel_output/$TIME_NOW/$output_name-$seq") != 1:
        raise ValueError("analytic logger must target the dedicated evidence mount exactly once")
    if "--engine.logger.log-dir outoutput/" in patched:
        raise ValueError("root-filesystem analytic output path survived patching")
    return patched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    original = args.path.read_bytes()
    actual = digest(original)
    if actual != EXPECTED_INPUT_SHA256:
        raise SystemExit(f"INPUT_SHA256_MISMATCH {actual} != {EXPECTED_INPUT_SHA256}")
    patched = patch_text(original.decode())
    output = digest(patched.encode())
    if output != EXPECTED_OUTPUT_SHA256:
        raise SystemExit(f"OUTPUT_SHA256_MISMATCH {output} != {EXPECTED_OUTPUT_SHA256}")
    args.path.write_text(patched)
    print(f"COMPOSE_DOSE_ENV_PATCHED input={actual} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
