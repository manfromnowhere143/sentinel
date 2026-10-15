"""Bound one next-root acceptance correction; preserve all physical predicates."""

import json

from .common import BASE, git, read, require

PARENT = "802c6779ae50b94251870288cf76752438ed53fd"
PREVIOUS = "experiments/iter177_pose_aware_seed/"
CONTROL_SOURCE = "experiments/iter169_full_horizon_control/shooting.py"
CONNECTION_SOURCE = "experiments/iter172_integrated_rrt/connection.py"
HEADER = b'"""Same control interface with next-root bounds matching existing motion tolerance."""\n\nimport math\n\nimport numpy as np\n\nfrom .common import require\n\n\n'


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS+"PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    metadata = {"iteration", "schema", "parent_commit", "scope", "source_files"}
    for key, value in old.items():
        if key not in metadata:
            require(plan[key] == value, "changed_contract:"+key)
    require(plan["parent_commit"] == PARENT, "parent_identity")
    require(plan["iteration"] == 178 and plan["schema"] == "sentinel.iter178.plan.v1", "study_identity")
    original = read(root, CONTROL_SOURCE)
    core = original[original.index(b"class Controls:"):original.index(b"\n\ndef terminal_cost")]
    expected = HEADER+core.rstrip(b"\n").replace(
        b"0 <= reset[3] <= 6 and abs(reset[4]) <= math.pi / 3",
        b"-1e-12 <= reset[3] <= 6 + 1e-12 and abs(reset[4]) <= math.pi / 3 + 1e-12")+b"\n"
    require(read(root, BASE/"controls.py") == expected, "constructor_substitution")
    original = read(root, CONNECTION_SOURCE)
    expected = original.replace(b"    Controls,\n", b"").replace(
        b"from .common import require, rss", b"from .common import require, rss\nfrom .controls import Controls")
    require(read(root, BASE/"connection.py") == expected, "evaluator_substitution")
    original = read(root, PREVIOUS+"adapter.py")
    expected = original.replace(
        b"from experiments.iter172_integrated_rrt.connection import Evaluator, task_for",
        b"from experiments.iter178_root_domain_consistency.connection import Evaluator, task_for")
    require(read(root, BASE/"adapter.py") == expected, "adapter_substitution")
    require(read(root, BASE/"RUNTIME.json") == read(root, PREVIOUS+"RUNTIME.json"), "runtime_unchanged")
    names = [CONTROL_SOURCE, CONNECTION_SOURCE]+[PREVIOUS+name for name in
             ["PLAN.json", "adapter.py", "RUNTIME.json", "seed.py", "forward.py", "proof/admission.json"]]
    names += ["experiments/iter175_connection_allocation/proof/admission.json"]
    for name in names:
        require(read(root, name) == git(root, "show", PARENT+":"+name), "reference_changed:"+name)
    admission = json.loads(read(root, PREVIOUS+"proof/admission.json"))
    require(admission["status"] == "invalid" and admission["complete_cases"] is None, "invalid_predecessor")


def reference(root):
    return json.loads(read(root, "experiments/iter175_connection_allocation/proof/admission.json"))
