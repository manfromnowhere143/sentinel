"""Strict evidence I/O and source identities, separate from planner behavior."""

from pathlib import Path
from experiments.iter158_constraint_aware_search.common import (
    encode,
    git,
    read,
    require,
    rss,
    sha,
    write,
)

BASE = Path("experiments/iter192_integrated_feedback")
PARENT = "345495fee70c12a30928353779f3507046484791"
PREVIOUS = Path("experiments/iter189_uniform_timing_eligibility")
MECHANISM = Path("experiments/iter191_stop_wait_release")
OLD = Path("experiments/iter153_action_feasibility/PLAN.json")
CASES = Path("experiments/iter161_grouping_width_ablation/CASES.json")


def source_check(root, plan, source):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    for name in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(
            read(root, name) == git(root, "show", source + ":" + name), "source_changed:" + name
        )


__all__ = [
    "BASE",
    "PARENT",
    "PREVIOUS",
    "MECHANISM",
    "OLD",
    "CASES",
    "encode",
    "git",
    "read",
    "require",
    "rss",
    "sha",
    "write",
    "source_check",
]
