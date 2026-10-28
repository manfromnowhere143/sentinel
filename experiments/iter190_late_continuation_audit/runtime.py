"""Bind the observed numerical and science-stack runtime; no hermeticity claim."""

import json
from experiments.iter171_centered_shooting.runtime import identity
from experiments.iter188_early_timing_feasibility.runtime import observe
from .common import BASE, read, require


def verify(root):
    expected = json.loads(read(root, BASE / "RUNTIME.json"))
    require(expected == dict(numeric=observe(), science=identity()), "runtime_identity")
