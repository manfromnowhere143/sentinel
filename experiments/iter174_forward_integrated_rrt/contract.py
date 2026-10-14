"""Check that this qualification changes only the connector, before outcomes."""

import json

from .common import BASE, read, require

OLD_BASE = "experiments/iter172_integrated_rrt/"


def check_contract(root, plan):
    old = json.loads(read(root, OLD_BASE + "PLAN.json"))
    metadata = {"iteration", "schema", "parent_commit", "scope", "source_files"}
    for key, value in old.items():
        if key not in metadata:
            require(plan.get(key) == value, "changed_contract:" + key)
    forward = json.loads(read(root, "experiments/iter173_matched_connector_cost/PLAN.json"))
    require(plan["max_proposals"] == forward["max_proposals"], "proposal_cap")
    baseline = read(root, OLD_BASE + "adapter.py").decode()
    expected = baseline.replace(
        "from .connection import Evaluator, solve, task_for",
        "from experiments.iter172_integrated_rrt.connection import Evaluator, task_for\n"
        "from experiments.iter173_matched_connector_cost.forward import solve as forward",
    ).replace("result = solve(evaluator)", 'result = forward(evaluator, True, self.plan["max_proposals"])')
    require(read(root, BASE / "adapter.py").decode() == expected, "adapter_scope")
    require(read(root, BASE / "RUNTIME.json") == read(root, OLD_BASE + "RUNTIME.json"),
            "unchanged_runtime")
