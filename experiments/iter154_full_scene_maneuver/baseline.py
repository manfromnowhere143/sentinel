"""Recheck historical evidence while keeping its outcomes out of the new denominator."""

from experiments.iter153_action_feasibility.inputs import load
from experiments.iter152_recovery_continuation.baseline import verify as nominal


def verify(root):
    nominal(root)
    return load(root)
