"""Source-bound monitor and nonempty actors with disclosed CPU environment substitutes."""

import ast
import hashlib
import json
import math
import os
import random
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from experiments.iter141_nominal_continuation.instrument import CLIENT_SHA
from experiments.iter145_constrained_execution.source_fixture import fixture
from experiments.iter145_constrained_execution.client import deliver
from experiments.iter146_route_outcome_contract.runner import run
from .client import diagnostic_result


def monitor_source(root):
    raw = (
        Path(root) / "experiments/iter145_constrained_execution/source/released_client.py.txt"
    ).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CLIENT_SHA:
        raise ValueError("monitor source identity")
    tree = ast.parse(raw)
    names = {"_s48_write", "_sentinel_i48_intervene"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assignments = {"_S48_PARAMS", "_S48_ENABLED", "_s48_state", "_s48_track"}
    nodes = [
        n
        for n in tree.body
        if n in nodes
        or isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id in assignments for t in n.targets)
    ]
    ns = dict(np=np, _sos=os, _sjson=json, _smath=math)
    with patch.dict(os.environ, {"SENTINEL_ENABLED": "1"}):
        exec(
            compile(ast.Module(body=nodes, type_ignores=[]), "<bound-released-monitor>", "exec"), ns
        )
    return ns["_sentinel_i48_intervene"]


class Exchange:
    def __init__(self, root, output, episode, arm, mode):
        self.monitor = monitor_source(root)
        self.output = output
        self.episode = episode
        self.arm = arm
        self.mode = mode

    def __call__(self, obs, info):
        nominal = np.array([[0.0, j * 2.0] for j in range(1, 7)], dtype=np.float32)
        present = self.mode == "hold" or self.mode == "release" and info["sentinel_frame"] < 2
        result = diagnostic_result(nominal, present=present)
        data = dict(timestamp=info["timestamp"], l2g_r_mat=torch.eye(3), l2g_t=torch.zeros(3))
        with patch.dict(
            os.environ, {"SENTINEL_I145_EPISODE": self.episode, "SENTINEL_I145_MODE": self.arm}
        ):
            return deliver(nominal, result, data, self.output, self.monitor, True, info)

    def line(self, frame):
        return (self.output / "sentinel_iter48_decisions.jsonl").read_bytes().splitlines()[frame]


def execute(root, output, *, actors=(), mode="release", max_actions=32):
    random.seed(144)
    np.random.seed(144)
    torch.manual_seed(144)
    output = Path(output)
    output.mkdir(exist_ok=False)
    env, _ = fixture(Path(root), actors=actors)
    poses = np.tile(np.eye(4), (1000, 1, 1))
    poses[:, 2, 3] = np.arange(1000)
    env.ground_model = (poses, 0.0, [2] * 1000)
    arm = "monitor" if mode == "hold" else "nominal"
    exchange = Exchange(root, output, output.name, arm, mode)
    with patch.object(torch.Tensor, "cuda", lambda self, *a, **k: self):
        return run(
            env,
            exchange,
            output=output / "trace",
            episode=output.name,
            arm=arm,
            monitor_reader=exchange.line,
            max_actions=max_actions,
            max_seconds=180,
            device="cpu",
        )
