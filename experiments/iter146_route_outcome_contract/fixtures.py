"""Retained HUGSIM methods with explicit synthetic CPU inputs and render substitutes."""

import hashlib
import json
from pathlib import Path
import random
from unittest.mock import patch

import numpy as np
import torch

from experiments.iter145_constrained_execution.nominal import packet
from experiments.iter145_constrained_execution.source_fixture import fixture
from .runner import run


def environment(root, kind="completion"):
    env, calls = fixture(root, speed=4.0, actors=())
    length = 1000 if kind == "censor" else 20
    poses = np.tile(np.eye(4), (length, 1, 1))
    poses[:, 2, 3] = np.arange(length)
    if kind == "collision_completion":
        poses[:, 2, 3] = np.linspace(0, 1, length)
        env.step.__func__.__globals__["bg_collision_det"] = lambda points, verts: True
    if kind == "off_route":
        poses[:, 0, 3] = 20
    env.ground_model = (poses, 0.0, [2] * length)
    return env, calls


class Exchange:
    def __init__(self, episode, arm):
        self.episode, self.arm, self.lines = episode, arm, []

    def __call__(self, obs, info):
        frame = info["sentinel_frame"]
        nominal = np.array([[0.0, j * 2.0] for j in range(1, 7)], dtype=np.float64)
        firing = 2 <= frame < 6
        proposed = np.zeros_like(nominal) if firing else nominal.copy()
        row = dict(frame_index=frame, ts=info["timestamp"], brake=firing, traj=nominal.tolist())
        line = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        self.lines.append(line)
        return packet(
            nominal,
            proposed,
            proposed if self.arm == "monitor" else nominal,
            episode=self.episode,
            frame=frame,
            time=info["timestamp"],
            mode=self.arm,
            monitor_sha256=hashlib.sha256(line).hexdigest(),
        )

    def monitor(self, frame):
        return self.lines[frame]


def execute(root, output, *, kind="completion", arm="nominal", max_actions=401, **kwargs):
    random.seed(144)
    np.random.seed(144)
    torch.manual_seed(144)
    env, calls = environment(root, kind)
    episode = Path(output).name
    exchange = Exchange(episode, arm)
    with patch.object(torch.Tensor, "cuda", lambda self, *a, **k: self):
        result = run(
            env,
            exchange,
            output=output,
            episode=episode,
            arm=arm,
            monitor_reader=exchange.monitor,
            max_actions=max_actions,
            device="cpu",
            **kwargs,
        )
    return result
