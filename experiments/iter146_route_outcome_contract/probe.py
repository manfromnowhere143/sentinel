"""Produce fresh finite CPU fixture traces; no analyzer or external access."""

import argparse
import json
from pathlib import Path
import platform

from .fixtures import execute
from .runner import ARMS


def produce(root, output):
    output = Path(output)
    output.mkdir(exist_ok=False)
    cases = []
    population = [
        (kind, arm, replica)
        for kind in ("completion", "censor")
        for arm in ARMS
        for replica in (1, 2)
    ]
    population += [(kind, "nominal", 1) for kind in ("collision_completion", "off_route")]
    for kind, arm, replica in population:
        name = f"{kind}__{arm}__{replica}"
        summary = execute(root, output / name, kind=kind, arm=arm)
        cases.append(
            dict(
                name=name,
                kind=kind,
                arm=arm,
                replica=replica,
                status=summary["status"],
                steps=summary["steps"],
            )
        )
        if summary["status"] != "completed":
            break
    result = dict(
        schema="sentinel.iter146.cpu_population.v1",
        cases=cases,
        expected_cases=len(population),
        python=platform.python_version(),
        status="completed"
        if len(cases) == len(population) and all(r["status"] == "completed" for r in cases)
        else "failed",
        scope="CPU constructed assets, identity CUDA transfer, 2x2 deterministic rendering, synthetic nominal/monitor, no actors, SAT foreground and controlled background; no GPU or driving evidence",
    )
    (output / "population.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = produce(a.root, a.output)
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "completed" else 1)
