"""Preserve the physical experiment while translating optimizer coordinates."""

import json
from .common import read, require
from experiments.iter170_derivative_step.binding import METADATA


def compare(previous, current):
    old = {k: v for k, v in previous.items() if k not in METADATA}
    new = {k: v for k, v in current.items() if k not in METADATA}
    require(
        new.pop("optimizer_coordinates", None) == "increments_from_initial", "coordinate_change"
    )
    require(old == new, "single_factor")


def verify_comparison(root, plan):
    compare(json.loads(read(root, "experiments/iter170_derivative_step/PLAN.json")), plan)
