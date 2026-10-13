"""Reproduce the full-population CPU fixture; never creates a native simulator or GPU job."""

import argparse
import gzip
import json
from pathlib import Path
import time

from .background_check import population, query
from .check import verify
from .fixtures import execute


def qualify(root, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    rows, summary, selected, geometry, slot, calls = execute(
        root, output / "full_source_trace", full_background=True
    )
    result = verify(rows, summary, selected, geometry, slot)
    binding, points, ground = population(root)
    native = [c for c in calls if c["kind"] == "background"]
    steps = [r for r in rows if r["event"] == "step"]
    (output / "full_source_background.json.gz").write_bytes(
        gzip.compress(json.dumps(native, sort_keys=True).encode(), mtime=0)
    )
    reports = [
        query(
            row,
            step["after"],
            step["info"]["ego_pos"],
            points,
            ground,
            binding["arrays"]["selected_xyz"]["sha256"],
        )
        for row, step in zip(native, steps)
    ]
    value = dict(
        status="supported"
        if len(reports) == 66 and all(r["status"] == "supported" for r in reports)
        else "failed",
        steps=len(steps),
        renderer="synthetic CPU 2x2",
        foreground="source predicate with CPU SAT polygon substitute",
        background="retained full population and source predicate on CPU; actual mask tap",
        new_native_episodes=0,
        elapsed_seconds=time.monotonic() - began,
        point_state_classifications=len(points) * len(reports),
        outcome=result["outcome"],
        frames=reports,
    )
    (output / "full_source_replay.json").write_text(json.dumps(value, indent=2) + "\n")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(Path.cwd(), args.output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("frames", "outcome")}))
    raise SystemExit(0 if result["status"] == "supported" else 1)
