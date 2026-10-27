"""Closed input/source inventory and prospective budget/population contract."""

from .common import BASE, CASES, GEOMETRY, HISTORY, OLD, PARENT, git, read, require, sha

COHORT = "e1defe45cf0122ffb2f39a7d0bcff9175b48dbd3"
NEW = ("__init__.py", "common.py", "population.py", "population_check.py", "bound.py",
       "bound_check.py", "probes.py", "probes_check.py", "runtime.py", "contract.py",
       "produce.py", "check.py", "PROTOCOL.md", "MATHEMATICS.md", "RESEARCH.md",
       "RUNTIME.json", "POPULATION.json", "QUALIFICATION.json", "RESEARCH_SOURCES.json",
       "proof/qualification/qualification.stdout.gz", "proof/qualification/qualification.stderr",
       "proof/qualification/qualification-corrected.stdout", "proof/qualification/qualification-corrected.stderr",
       "proof/qualification/qualification-final.stdout.gz", "proof/qualification/qualification-final.stderr",
       "proof/qualification/qualification-final-corrected.stdout", "proof/qualification/qualification-final-corrected.stderr",
       "proof/qualification/lint.stdout", "proof/qualification/supply-chain.stdout")
PARENTS = (
    "experiments/iter149_observation_recovery/__init__.py",
    "experiments/iter149_observation_recovery/recovery.py",
    "experiments/iter150_cloud_observation/__init__.py",
    "experiments/iter150_cloud_observation/native.py",
    "experiments/iter153_action_feasibility/__init__.py",
    "experiments/iter153_action_feasibility/geometry.py",
    "experiments/iter153_action_feasibility/planner.py",
    "experiments/iter155_background_witness/storage.py",
    "experiments/iter158_constraint_aware_search/__init__.py",
    "experiments/iter158_constraint_aware_search/common.py",
)


def inputs():
    paths = {GEOMETRY, OLD}
    for directory in HISTORY.values():
        paths |= {directory + "/PLAN.json", directory + "/proof/admission.json"}
        for case in CASES:
            paths.add(directory + f"/proof/search_raw/{case}/selected/trace.json")
    for case in CASES:
        for name in ("sequences.json", "events.jsonl"):
            paths.add(HISTORY[187] + f"/proof/search_raw/{case}/{name}")
    return sorted(paths)


def skeleton():
    return dict(schema="sentinel.iter188.plan.v1", iteration=188, parent_commit=PARENT,
                cohort_commit=COHORT, cases=list(CASES), producer_seconds=300, checker_seconds=300,
                max_rss_bytes=1024**3, max_output_bytes=64 * 1024**2, minimum_free_bytes=1024**3,
                source_files=sorted([str(BASE / n) for n in NEW] + list(PARENTS) +
                                    ["tests/test_iter188_early_timing.py"]), inputs=None)


def check_plan(root, plan):
    expected = skeleton()
    require(set(plan) == set(expected), "plan_fields")
    require(all(plan[k] == v for k, v in expected.items() if k != "inputs"), "frozen_plan")
    require(set(plan["inputs"]) == set(inputs()), "input_inventory")
    for name, identity in plan["inputs"].items():
        data = read(root, name)
        require(data == git(root, "show", PARENT + ":" + name) and sha(data) == identity, "parent_input")
    for name in PARENTS:
        require(read(root, name) == git(root, "show", PARENT + ":" + name), "parent_implementation")
    require(read(root, BASE / "POPULATION.json") == git(root, "show", COHORT + ":" + str(BASE / "POPULATION.json")), "frozen_population")
