"""Identity and bounded I/O only; no scientific predicates."""

from pathlib import Path

from experiments.iter158_constraint_aware_search.common import (
    encode, git, read, require, rss, sha, write,
)

BASE = Path("experiments/iter188_early_timing_feasibility")
PARENT = "0490e766a2833ad8d59ee85f4d07335a4fee7146"
CASES = ("bend_left", "bend_right", "chicane_left", "chicane_right")
GEOMETRY = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
HISTORY = {
    178: "experiments/iter178_root_domain_consistency",
    183: "experiments/iter183_timing_eligibility",
    187: "experiments/iter187_integrated_branch_retention",
}


def source_check(root, source, plan):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_id")
    git(root, "merge-base", "--is-ancestor", PARENT, source)
    for name in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(read(root, name) == git(root, "show", source + ":" + name), "source_changed:" + name)
    for name, identity in plan["inputs"].items():
        data = read(root, name)
        require(sha(data) == identity and data == git(root, "show", PARENT + ":" + name), "input_changed:" + name)


__all__ = ["BASE", "PARENT", "CASES", "GEOMETRY", "OLD", "HISTORY", "encode", "git", "read", "require", "rss", "sha", "write", "source_check"]
