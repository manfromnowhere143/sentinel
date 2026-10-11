"""New exact-plan worker entrypoint; calls the released scientific worker unchanged."""

import argparse
import os
from pathlib import Path

from .admission import validate_plan, PLAN
from .records import read, record
from .ownership import alive
from experiments.iter150_cloud_observation.native import bind


def dispatch(control, slot_index, invoke):
    control = Path(control)
    document = validate_plan(read(control / "plan.json"))
    if type(slot_index) is not int or not 0 <= slot_index < 14:
        raise ValueError("slot")
    pair = slot_index // 2
    marker = read(control / f"pair_{pair:03d}_started.json")
    owner = read(control / f"pair_{pair:03d}_owner.json")
    expected, _ = bind(control, pair, owner["binding"])
    if (
        marker["plan_sha256"] != PLAN
        or marker["pair"] != pair
        or owner["process"]["pid"] != os.getppid()
        or not alive(owner, expected)
    ):
        raise ValueError("worker_parent")
    slot = document["slots"][slot_index]
    record(
        control / f"slot_{slot_index:03d}_dispatched.json",
        dict(slot=slot, pair=pair, plan_sha256=PLAN, owner_binding=owner["binding"]),
    )
    return invoke(control, document, slot)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--slot", type=int, required=True)
    args = parser.parse_args()
    from experiments.iter147_full_horizon_execution.gpu import worker

    return dispatch(args.control, args.slot, worker)


if __name__ == "__main__":
    raise SystemExit(main())
