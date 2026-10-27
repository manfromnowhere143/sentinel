"""Constructed straight corridor for wiring checks; no four-case outcomes."""

import argparse
import json
from pathlib import Path

from .worker import collect
from .common import BASE, read, write


def case():
    return dict(
        id="constructed_straight",
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 1.3, 0.0],
            route=[[0.0, i / 4] for i in range(81)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={},
        ),
        points=[[10.0, 0.5, 10.0]],
        ground=[
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ],
    )


def produce(root, output, library):
    plan = json.loads(read(root, BASE / "PLAN.json"))
    plan.update(attempt_budget=512, per_run_seconds=10)
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    c = case()
    output.mkdir(exist_ok=False)
    result = collect(output, c, old, plan, 20261027, library)
    write(output / "inputs.json", dict(case=c, old=old, plan=plan))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--library", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(produce(a.root.resolve(), a.output.resolve(), a.library.resolve())))
