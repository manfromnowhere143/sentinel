"""Admit exactly one initial-proposal replacement against retained Iter175."""

import json

from .common import BASE, git, read, require

REFERENCE = "20130fd53a35040efa2f48e5019349feaa724233"
PARENT = "da9d78ff48b632d5f71fd8e2b3832b4a5428254d"
PREVIOUS = "experiments/iter175_connection_allocation/"
GENERATOR = "experiments/iter173_matched_connector_cost/forward.py"


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS+"PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    metadata = {"iteration", "schema", "parent_commit", "scope", "source_files"}
    for key, value in old.items():
        if key not in metadata:
            require(plan[key] == value, "changed_contract:"+key)
    require(plan["parent_commit"] == PARENT, "parent_identity")
    require(plan["iteration"] == 177 and plan["schema"] == "sentinel.iter177.plan.v1",
            "study_identity")
    original = read(root, PREVIOUS+"adapter.py")
    expected = original.replace(
        b"from experiments.iter173_matched_connector_cost.forward import solve as forward",
        b"from experiments.iter177_pose_aware_seed.forward import solve as forward")
    require(expected != original and read(root, BASE/"adapter.py") == expected, "adapter_substitution")
    original = read(root, GENERATOR)
    expected = original.replace(b"from .common import require, rss",
                                b"from .common import require, rss\nfrom .seed import initial").replace(
                                    b"yield controls.initial()", b"yield initial(controls)").replace(
                                        b"Bounded multi-step open-loop proposals; no fitted endpoint or witness input.",
                                        b"Bounded forward proposals with one algebraic pose-aware initial program.")
    require(expected != original and read(root, BASE/"forward.py") == expected, "generator_substitution")
    require(read(root, BASE/"RUNTIME.json") == read(root, PREVIOUS+"RUNTIME.json"), "runtime_unchanged")
    for name in [PREVIOUS+suffix for suffix in ["PLAN.json", "adapter.py", "RUNTIME.json",
                                               "proof/admission.json"]]+[GENERATOR]:
        require(read(root, name) == git(root, "show", REFERENCE+":"+name), "reference_changed:"+name)


def reference(root):
    return json.loads(read(root, PREVIOUS+"proof/admission.json"))
