"""Constrain the candidate to checkpoint ranking and its independent replay."""

import json

from .common import BASE, git, read, require

PARENT = "a52187abe34a198a6289b962ca97fd5cb8c72912"
PREVIOUS = "experiments/iter178_root_domain_consistency/"
REPLAY = "experiments/iter172_integrated_rrt/check.py"


def replace_once(data, before, after):
    require(data.count(before) == 1, "substitution_anchor")
    return data.replace(before, after)


def expected_connection(original):
    value = replace_once(
        original,
        b"import numpy as np",
        b"from .selection import checkpoint_frames, prefix_index, evaluation_rank\n\nimport numpy as np",
    )
    value = replace_once(value, b"import distance, terminal_frame", b"import terminal_frame")
    value = replace_once(
        value,
        b"        self.controls = Controls(before[:5], task)",
        b"        self.checkpoints = checkpoint_frames(geometry, old)\n        self.controls = Controls(before[:5], task)",
    )
    begin = value.index(b"        candidates = range(1, valid_prefix + 1)")
    end = value.index(b"        row = dict(", begin)
    value = (
        value[:begin]
        + b"""        selected_prefix = prefix_index(
            rows, valid_prefix, interrupted, world_complete,
            self.target, self.before[5], self.checkpoints,
        )
"""
        + value[end:]
    )
    begin = value.index(b"            endpoint = rows[selected_prefix]")
    end = value.index(b"            if self.best_rank is None", begin)
    return (
        value[:begin]
        + b"""            rank = evaluation_rank(row, self.target, self.before[5], self.checkpoints)
"""
        + value[end:]
    )


def expected_replay(original):
    header = b'''"""Separate motion/accounting replay with independently specified prefix selection."""

import math
import struct

from experiments.iter153_action_feasibility.check import near
from experiments.iter168_control_connector.check import physical, completed
from experiments.iter169_full_horizon_control.check import variables, objective
from experiments.iter172_integrated_rrt.check import task_check, outcome
from .common import require
from .selection_check import selection_index, selection_rank


'''
    value = original[original.index(b"def evaluation(") : original.index(b"def path_tokens(")]
    begin = value.index(b"    choices = range(1, prefix + 1)")
    end = value.index(b'    require(row["selected_prefix"] == selected', begin)
    value = (
        value[:begin]
        + b"    selected = selection_index(row, connection, case, old)\n"
        + value[end:]
    )
    begin = value.index(b"    def rank(r):")
    end = value.index(b"    best = min(candidates, key=rank)", begin)
    value = (
        value[:begin]
        + b"    def rank(r):\n        return selection_rank(r, c, case, old)\n\n"
        + value[end:]
    )
    value = value.replace(b'    target = connection["target"]\n', b"")
    return header + value.rstrip(b"\n") + b"\n"


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS + "PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    metadata = {"iteration", "schema", "parent_commit", "scope", "source_files"}
    for key, value in old.items():
        if key not in metadata:
            require(plan[key] == value, "changed_contract:" + key)
    require(plan["parent_commit"] == PARENT, "parent_identity")
    require(
        plan["iteration"] == 181 and plan["schema"] == "sentinel.iter181.plan.v1", "study_identity"
    )
    require(
        read(root, BASE / "connection.py")
        == expected_connection(read(root, PREVIOUS + "connection.py")),
        "evaluator_substitution",
    )
    require(
        read(root, BASE / "replay.py") == expected_replay(read(root, REPLAY)), "replay_substitution"
    )
    adapter = read(root, PREVIOUS + "adapter.py").replace(
        b"from experiments.iter178_root_domain_consistency.connection",
        b"from experiments.iter181_checkpoint_prefix_selection.connection",
    )
    require(read(root, BASE / "adapter.py") == adapter, "adapter_substitution")
    for name in ("controls.py", "RUNTIME.json"):
        require(read(root, BASE / name) == read(root, PREVIOUS + name), "unchanged:" + name)
    names = [
        PREVIOUS + name
        for name in (
            "PLAN.json",
            "connection.py",
            "adapter.py",
            "controls.py",
            "RUNTIME.json",
            "proof/admission.json",
        )
    ]
    names += [
        REPLAY,
        "experiments/iter177_pose_aware_seed/forward.py",
        "experiments/iter177_pose_aware_seed/seed.py",
        "experiments/iter180_equal_work_continuation/proof/admission.json",
        "experiments/iter180_equal_work_continuation/proof/selection_notes.json",
    ]
    for name in names:
        require(
            read(root, name) == git(root, "show", PARENT + ":" + name), "reference_changed:" + name
        )
    baseline = reference(root)
    require(
        baseline["phase"] == "closed"
        and baseline["iteration"] == 178
        and baseline["complete_cases"] == 3
        and baseline["qualified_for_source_comparison"] is False,
        "reference_status",
    )


def reference(root):
    return json.loads(read(root, PREVIOUS + "proof/admission.json"))
