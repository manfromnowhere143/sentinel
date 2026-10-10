"""Replay four explicit shorter-horizon fixtures twice through full source methods."""

import argparse
import json
from pathlib import Path
import platform
import warnings
from unittest.mock import patch
import numpy as np
import scipy
import torch
from .driver import run
from .nominal import packet
from .source_fixture import fixture


def qualify(root, output_dir):
    output_dir.mkdir(exist_ok=False)
    cases = []
    for speed, curved in [(0.0, False), (4.0, False), (0.0, True), (4.0, True)]:
        for replica in range(2):
            episode = f"speed{speed:g}_curve{int(curved)}_replica{replica}"
            env, calls = fixture(root, speed=speed)

            def exchange(obs, info):
                positions = np.array(
                    [[0.03 * i * i if curved else 0.0, 2.0 * i] for i in range(1, 7)],
                    dtype=np.float64,
                )
                return packet(
                    positions,
                    positions.copy(),
                    positions.copy(),
                    episode=episode,
                    frame=info["sentinel_frame"],
                    time=info["timestamp"],
                    mode="nominal",
                    monitor_sha256="a" * 64,
                )

            with patch.object(torch.Tensor, "cuda", lambda self, *a, **k: self):
                summary = run(
                    env,
                    exchange,
                    output=output_dir / episode,
                    episode=episode,
                    max_steps=12,
                    max_seconds=60,
                    device="cpu",
                )
            events = [
                json.loads(line)
                for line in (output_dir / episode / "events.jsonl").read_text().splitlines()
            ]
            boundary = []
            for tick in range(1, 13):
                group = [c for c in calls if c["time"] == tick * 0.25]
                boundary.append(
                    dict(
                        time=tick * 0.25,
                        sequence=[c["kind"] for c in group],
                        shared_transform_object=len({c["planning_id"] for c in group}) == 1
                        if group
                        else None,
                        observations=[
                            {k: v for k, v in c.items() if k != "planning_id"} for c in group
                        ],
                    )
                )
            cases.append(
                dict(
                    episode=episode,
                    speed=speed,
                    curved=curved,
                    replica=replica,
                    summary=summary,
                    events=events,
                    boundary=boundary,
                )
            )
    return dict(
        schema="sentinel.iter145.integration_cpu.v1",
        status="completed",
        cases=cases,
        substitutions=[
            "CUDA tensor transfer identity",
            "six cameras rendered with deterministic 2x2 zero RGB/depth fixtures",
            "background point collision returns false",
            "Shapely polygon intersects replaced by separating-axis fixture",
            "asset-loading constructor replaced by explicit source fixture state",
            "planner/monitor transport synthetic typed nominal delivery",
        ],
        environment=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            torch=torch.__version__,
            platform=platform.platform(),
        ),
        gpu_observed=False,
        live_study_admitted=False,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        value = qualify(a.root, a.output_dir)
    with a.output.open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(
            dict(
                cases=len(value["cases"]), statuses=[r["summary"]["status"] for r in value["cases"]]
            )
        )
    )
    return 0 if all(r["summary"]["status"] == "completed" for r in value["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
