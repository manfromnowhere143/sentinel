"""Known-bads for causal scope, ancestry, timing and full scalar failure admission."""

import ast
import copy
import json
import math
from pathlib import Path
import time

import pytest

from experiments.iter160_continuation_preservation.common import prefix, validate_inputs
from experiments.iter160_continuation_preservation.check import scalar, verify
from experiments.iter160_continuation_preservation.run import evaluate, replay
from experiments.iter159_route_search_qualification.run import query_for

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/iter160_continuation_preservation"
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


def toy():
    case = dict(
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 2.0, 0.0],
            route=[[0.0, i / 10] for i in range(21)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={},
        ),
        points=[[100.0, 0.5, 100.0]],
        ground=[[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]],
    )
    history = [
        dict(frame=0, action=None, state=case["geometry"]["reset"]),
        dict(frame=1, action=[0.0, 0.0], state=[0.5, 0.0, 0.0, 2.0, 0.0]),
    ]
    pair = dict(
        id="toy",
        case="toy",
        frame=1,
        discarded_prefix=history,
        representative_prefix=history,
        suffix=[[0.0, 0.0]] * 3,
    )
    return case, pair


def acquired(case=None, pair=None):
    if case is None:
        case, pair = toy()
    masks = {}
    trace = replay(
        pair, "discarded", case, OLD, lambda f, m: masks.update({f: m}) if m is not None else None
    )
    return trace, masks, case, pair


def admit(trace, masks, case, pair):
    return verify(trace, pair, "discarded", case, OLD, masks.__getitem__, time.monotonic() + 10)


def test_complete_and_exhausted_are_distinct():
    trace, masks, case, pair = acquired()
    assert admit(trace, masks, case, pair)["stop"] == "model_complete"
    pair["suffix"] = [[0.0, 0.0]]
    trace, masks, case, pair = acquired(case, pair)
    assert admit(trace, masks, case, pair)["stop"] == "suffix_exhausted"


@pytest.mark.parametrize("kind", ["collision", "numerically_ambiguous", "progress", "controls"])
def test_failure_replays_and_later_checks_remain_unobserved(kind):
    case, pair = toy()
    if kind in ("collision", "numerically_ambiguous"):
        # Clear at reset and frame1; >100 points enter at frame2.
        z = 2.25 if kind == "collision" else 2.5
        case["points"] = [[0.0, 0.5, z]] * 101
    elif kind == "progress":
        case["geometry"]["comparators"] = {"due": dict(hazard_time=0.5, rc=0.99)}
    else:
        pair["suffix"][0] = [3.0, 0.0]
    trace, masks, case, pair = acquired(case, pair)
    expected = "background_" + kind if kind in ("collision", "numerically_ambiguous") else kind
    result = admit(trace, masks, case, pair)
    assert result["stop"] == expected and result["final_frame"] == 2
    assert trace["rows"][-1]["predicates"]["completion"] is None
    if kind in ("progress", "controls"):
        assert trace["rows"][-1]["background"] is None and 2 not in masks


@pytest.mark.parametrize("kind", ["foreground", "foreground_sweep", "route_distance"])
def test_geometric_failures_have_separate_predicates(kind):
    case, _ = toy()
    before, state, action = [0.0, 0.0, 0.0, 2.0, 0.0], [0.5, 0.0, 0.0, 2.0, 0.0], [0.0, 0.0]
    if kind == "foreground":
        case["geometry"]["obstacles"] = [[0.5, 0.0, 0.0, 0.5, 0.5, 1.0, 0.0]]
    elif kind == "foreground_sweep":
        case["geometry"]["obstacles"] = [[2.26, 0.0, 0.0, 0.5, 0.5, 1.0, 0.0]]
    else:
        case["geometry"]["route"] = [[20.0, 0.0], [20.0, 1.0]]
    produced, pm = evaluate(before, state, action, 1, case, OLD, query_for(case))
    checked, cm = scalar(before, state, action, 1, case, OLD)
    assert produced["reason"] == checked["reason"] == kind
    assert produced["predicates"] == checked["predicates"]
    assert pm is cm is None


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("state", "numeric_replay"),
        ("action", "fixed_command"),
        ("mask", "scalar_mask"),
        ("time", "absolute_frame"),
        ("prefix", "numeric_replay"),
        ("missing", "premature_exhaustion"),
        ("completion", "terminal_status"),
        ("failure", "first_failure"),
        ("background", "scalar_background"),
        ("predicate", "predicate_vector"),
        ("later", "continued_after_terminal"),
        ("identity", "trace_identity"),
    ],
)
def test_tampered_observations_fail(mutation, reason):
    trace, masks, case, pair = acquired()
    if mutation == "state":
        trace["rows"][2]["state"][0] += 0.1
    elif mutation == "action":
        trace["rows"][2]["action"] = [0.2, 0.0]
    elif mutation == "mask":
        masks[2] = b"\x01"
    elif mutation == "time":
        trace["rows"][2]["frame"] = 1
    elif mutation == "prefix":
        trace["rows"][0]["state"] = [0.5, 0.0, 0.0, 2.0, 0.0]
    elif mutation == "missing":
        trace["rows"].pop()
    elif mutation == "completion":
        trace["stop"] = "suffix_exhausted"
    elif mutation == "failure":
        trace["rows"][2]["reason"] = "progress"
    elif mutation == "background":
        trace["rows"][2]["background"]["count"] += 1
    elif mutation == "predicate":
        trace["rows"][2]["predicates"]["progress"] = True
    elif mutation == "later":
        pair["suffix"].append([0.0, 0.0])
        trace["rows"].append(copy.deepcopy(trace["rows"][-1]))
    else:
        trace["arm"] = "representative"
    with pytest.raises(ValueError, match=reason):
        admit(trace, masks, case, pair)


def test_checkpoint_uses_absolute_time_after_prefix():
    case, pair = toy()
    case["geometry"]["comparators"] = {"due": dict(hazard_time=0.5, rc=0.99)}
    trace, masks, case, pair = acquired(case, pair)
    assert admit(trace, masks, case, pair)["stop"] == "progress"
    trace["rows"][-1]["predicates"]["progress"] = None
    with pytest.raises(ValueError, match="predicate_vector"):
        admit(trace, masks, case, pair)


@pytest.mark.parametrize("mutation", ["parent", "frame", "reset", "reason"])
def test_bad_ancestry_fails(mutation):
    rows = [
        dict(id=0, parent=None, frame=0, action=None, state=[0] * 5, reason="clear"),
        dict(id=1, parent=0, frame=1, action=[0, 0], state=[0] * 5, reason="clear"),
    ]
    if mutation == "parent":
        rows[1]["parent"] = 1
    elif mutation == "frame":
        rows[1]["frame"] = 2
    elif mutation == "reset":
        rows[1]["parent"] = None
    else:
        rows[1]["reason"] = "collision"
    with pytest.raises(ValueError, match="ancestry"):
        prefix(rows, 1)


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("pair", "pair_population"),
        ("suffix", "suffix_binding"),
        ("history", "representative_state"),
        ("source", "admission_identity"),
        ("attempt", "attempt_identity"),
        ("loss", "loss_binding"),
        ("bindings", "binding_population"),
    ],
)
def test_frozen_input_corruption_fails(mutation, reason):
    inputs = json.loads((BASE / "INPUTS.json").read_text())
    pair = inputs["pairs"][0]
    if mutation == "pair":
        inputs["pairs"].pop()
    elif mutation == "suffix":
        pair["suffix"].pop()
    elif mutation == "history":
        pair["representative_prefix"][-1]["state"][0] += 1
    elif mutation == "source":
        inputs["admission_sha256"] = "0" * 64
    elif mutation == "attempt":
        pair["bindings"][0]["attempts_sha256"] = "0" * 64
    elif mutation == "loss":
        pair["bindings"][0]["representative"] = 999
    else:
        pair["bindings"].pop()
    with pytest.raises(ValueError, match=reason):
        validate_inputs(ROOT, inputs)


def test_checker_has_no_producer_or_vector_query_import():
    imports = [
        n.module
        for n in ast.walk(ast.parse((BASE / "check.py").read_text()))
        if isinstance(n, ast.ImportFrom)
    ]
    assert not any(
        m and any(m.endswith(s) for s in ("run", "planner", "search", "background"))
        for m in imports
    )
    assert math.isclose(OLD["dt"], 0.25)


def test_same_suffix_can_distinguish_reachable_states():
    case, pair = toy()
    pair["representative_prefix"] = [
        copy.deepcopy(pair["discarded_prefix"][0]),
        dict(frame=1, action=[-2.0, 0.0], state=[0.375, 0.0, 0.0, 1.5, 0.0]),
    ]
    masks = {}
    trace = replay(
        pair,
        "representative",
        case,
        OLD,
        lambda f, m: masks.update({f: m}) if m is not None else None,
    )
    result = verify(
        trace, pair, "representative", case, OLD, masks.__getitem__, time.monotonic() + 10
    )
    assert result["stop"] == "suffix_exhausted"
    original, original_masks, _, _ = acquired(case, pair)
    assert admit(original, original_masks, case, pair)["stop"] == "model_complete"


def test_source_identity_and_bytes_are_checked(tmp_path):
    from experiments.iter160_continuation_preservation.common import BASE as REL, source_check
    import subprocess

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path)

    git("init", "-q")
    (tmp_path / REL).mkdir(parents=True)
    (tmp_path / REL / "PLAN.json").write_text("{}")
    (tmp_path / "input.json").write_text("[]")
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
    head = git("rev-parse", "HEAD").decode().strip()
    plan = dict(source_files=[], input_files={})
    source_check(tmp_path, plan, head)
    with pytest.raises(ValueError, match="source_encoding"):
        source_check(tmp_path, plan, "bad")
    (tmp_path / REL / "PLAN.json").write_text("changed")
    with pytest.raises(ValueError, match="source_changed"):
        source_check(tmp_path, plan, head)
    (tmp_path / REL / "PLAN.json").write_text("{}")
    plan["input_files"] = {"input.json": "0" * 64}
    with pytest.raises(ValueError, match="input_identity"):
        source_check(tmp_path, plan, head)
