"""Enforce the registered single scientific parameter change."""

import json
from .common import read, require

METADATA = {
    "iteration",
    "schema",
    "parent_commit",
    "scope",
    "source_files",
    "previous_source_commit",
    "previous_raw_commit",
}


def compare(previous, current):
    old = {k: v for k, v in previous.items() if k not in METADATA}
    new = {k: v for k, v in current.items() if k not in METADATA}
    require(
        old["optimizer_diff_step"] == 1e-6 and new["optimizer_diff_step"] is None,
        "derivative_change",
    )
    old["optimizer_diff_step"] = None
    require(old == new, "single_factor")


def verify_comparison(root, plan):
    compare(json.loads(read(root, "experiments/iter169_full_horizon_control/PLAN.json")), plan)
