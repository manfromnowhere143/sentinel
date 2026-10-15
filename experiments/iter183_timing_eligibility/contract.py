"""Limit changes to timing eligibility, its accounting and independent replay."""

import json

from .common import BASE, git, read, require

PARENT = "51ccd68c11454a61ad4e76342c26f12d30bd12be"
PREVIOUS = "experiments/iter181_checkpoint_prefix_selection/"
BASELINE = "experiments/iter178_root_domain_consistency/"


def once(value, before, after):
    require(value.count(before) == 1, "substitution_anchor")
    return value.replace(before, after)


def expected_connection(value):
    value = once(value, b"query, emit):", b"query, emit, eligibility):")
    value = once(
        value,
        b"        self.query, self.emit = query, emit",
        b"        self.query, self.emit = query, emit\n        self.eligibility = eligibility",
    )
    value = once(
        value,
        b"        selected_prefix = prefix_index(\n            rows, valid_prefix, interrupted, world_complete,",
        b"""        eligibility = self.eligibility.scan(rows, valid_prefix, interrupted, self.deadline)
        if not eligibility["complete"]:
            interrupted = "time_budget"
        selected_prefix = prefix_index(
            rows, eligibility["eligible_prefix"], interrupted, world_complete,""",
    )
    value = once(
        value,
        b"            selected_prefix=selected_prefix,",
        b"            selected_prefix=selected_prefix,\n            eligibility=eligibility,",
    )
    value = once(
        value,
        b"""        if world_complete:
            raise StopEvaluation("model_complete")
        if row["target_complete"]:
            raise StopEvaluation("qualified_candidate")
        if interrupted:
            raise StopEvaluation(interrupted)""",
        b"""        if interrupted:
            raise StopEvaluation(interrupted)
        if world_complete:
            raise StopEvaluation("model_complete")
        if row["target_complete"] and selected_prefix == horizon:
            raise StopEvaluation("qualified_candidate")""",
    )
    return value


def expected_adapter(value):
    value = once(
        value,
        b"from experiments.iter181_checkpoint_prefix_selection.connection",
        b"from experiments.iter183_timing_eligibility.connection",
    )
    value = once(
        value,
        b"from experiments.iter177_pose_aware_seed.forward import solve as forward",
        b"from experiments.iter177_pose_aware_seed.forward import solve as forward\nfrom .eligibility import Eligibility",
    )
    value = once(
        value,
        b"        self.accepted = {}",
        b"        self.accepted = {}\n        self.eligibility = Eligibility(geometry, old, self.started)",
    )
    value = once(
        value,
        b"            self.query,\n            emit,\n        )",
        b"            self.query,\n            emit,\n            self.eligibility,\n        )",
    )
    return value


def expected_replay(value):
    value = once(
        value,
        b"def evaluation(row, connection, case, old):",
        b"def evaluation(row, connection, case, old, eligibility):",
    )
    value = once(
        value,
        b"    selected = selection_index(row, connection, case, old)",
        b"    eligibility.check(row)\n    selected = selection_index(row, connection, case, old)",
    )
    value = once(
        value,
        b"def connection_check(c, events, case, old, plan, remaining):",
        b"def connection_check(c, events, case, old, plan, remaining, eligibility):",
    )
    value = once(
        value,
        b"attempts = sum(evaluation(row, c, case, old) for row in ev)",
        b"attempts = sum(evaluation(row, c, case, old, eligibility) for row in ev)",
    )
    value = once(
        value,
        b"""            ev[-1][key]
            and all(not e["world_complete"] and not e["target_complete"] for e in ev[:-1]),""",
        b"""            ev[-1][key] and ev[-1]["selected_prefix"] > 0
            and (stop != "qualified_candidate" or ev[-1]["selected_prefix"] == c["task"]["terminal_frame"])
            and all(not e["world_complete"] and not (
                e["target_complete"] and e["selected_prefix"] == c["task"]["terminal_frame"]
            ) for e in ev[:-1]),""",
    )
    return value


def reference(root, iteration=178):
    require(iteration in (178, 181), "reference_iteration")
    prefix = BASELINE if iteration == 178 else PREVIOUS
    return json.loads(read(root, prefix + "proof/admission.json"))


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS + "PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    for key, value in old.items():
        if key not in {"iteration", "schema", "parent_commit", "scope", "source_files"}:
            require(plan[key] == value, "changed_contract:" + key)
    require(
        plan["iteration"] == 183
        and plan["schema"] == "sentinel.iter183.plan.v1"
        and plan["parent_commit"] == PARENT,
        "study_identity",
    )
    for name, transform in (
        ("connection.py", expected_connection),
        ("adapter.py", expected_adapter),
        ("replay.py", expected_replay),
    ):
        require(
            read(root, BASE / name) == transform(read(root, PREVIOUS + name)),
            "substitution:" + name,
        )
    for name in ("controls.py", "selection.py", "RUNTIME.json"):
        require(read(root, BASE / name) == read(root, PREVIOUS + name), "unchanged:" + name)
    names = [
        PREVIOUS + n
        for n in (
            "PLAN.json",
            "connection.py",
            "adapter.py",
            "replay.py",
            "selection.py",
            "selection_check.py",
            "controls.py",
            "RUNTIME.json",
            "proof/admission.json",
        )
    ]
    names += [
        BASELINE + "proof/admission.json",
        "experiments/iter177_pose_aware_seed/forward.py",
        "experiments/iter177_pose_aware_seed/seed.py",
    ]
    names += [
        "experiments/iter182_late_frontier_timing/" + n
        for n in (
            "bound.py",
            "bound_check.py",
            "premature.py",
            "premature_check.py",
            "MATHEMATICS.md",
            "proof/admission.json",
        )
    ]
    for name in names:
        require(
            read(root, name) == git(root, "show", PARENT + ":" + name), "reference_changed:" + name
        )
    for iteration, count in ((178, 3), (181, 2)):
        baseline = reference(root, iteration)
        require(
            baseline["phase"] == "closed"
            and baseline["iteration"] == iteration
            and baseline["complete_cases"] == count
            and baseline["qualified_for_source_comparison"] is False,
            "reference_status",
        )
