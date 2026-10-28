"""Bounded evidence I/O and exact source identities."""

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

BASE = Path("experiments/iter191_stop_wait_release")
PARENT = "cde1d294ca687eedaef30ad67c728ffe46d9eed8"
PREVIOUS = Path("experiments/iter189_uniform_timing_eligibility")
AUDIT = Path("experiments/iter190_late_continuation_audit")
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
    "AUDIT",
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
