"""Unchanged released monitor, with an explicitly labelled diagnostic detector input."""

import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
from experiments.iter146_route_outcome_contract.client import instrument as prior_instrument
from experiments.iter145_constrained_execution.client import deliver as prior_deliver


def diagnostic_result(nominal, *, present):
    import torch

    centers = [[float(nominal[0, 0]), float(nominal[0, 1]), 0.0]] if present else []
    return dict(
        boxes_3d=SimpleNamespace(gravity_center=torch.tensor(centers).reshape(-1, 3)),
        scores_3d=torch.ones(len(centers)),
        track_ids=torch.full((len(centers),), 147),
    )


def deliver(nominal, result, data, output, monitor, enabled, info):
    mode = os.environ.get("SENTINEL_I147_PROBE", "none")
    if mode not in ("none", "monitor_hold"):
        raise ValueError("diagnostic_mode")
    if mode == "monitor_hold":
        if os.environ["SENTINEL_I145_MODE"] != "monitor":
            raise ValueError("diagnostic_arm")
        target = Path(output) / "diagnostic_inputs.jsonl"
        record = dict(
            frame=info["sentinel_frame"],
            time=info["timestamp"],
            kind="injected_detector_input_not_natural_perception",
            center=[float(nominal[0, 0]), float(nominal[0, 1]), 0.0],
            score=1.0,
            track_id=147,
            original_model_detection_count=len(result["scores_3d"]),
        )
        with target.open("x" if info["sentinel_frame"] == 0 else "a") as f:
            f.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        result = diagnostic_result(nominal, present=True)
    return prior_deliver(nominal, result, data, output, monitor, enabled, info)


def instrument(raw):
    old = prior_instrument(raw).decode()
    before = "from experiments.iter145_constrained_execution.client import deliver"
    after = "from experiments.iter147_full_horizon_execution.client import deliver"
    if old.count(before) != 1:
        raise ValueError("client_import_anchor")
    new = old.replace(before, after)
    expected = ast.parse(old)
    changes = 0
    for node in ast.walk(expected):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "experiments.iter145_constrained_execution.client"
        ):
            node.module = "experiments.iter147_full_horizon_execution.client"
            changes += 1
    if changes != 1 or ast.dump(expected) != ast.dump(ast.parse(new)):
        raise ValueError("unexpected_client_delta")
    compile(new, "iter147_client.py", "exec")
    return new.encode()
