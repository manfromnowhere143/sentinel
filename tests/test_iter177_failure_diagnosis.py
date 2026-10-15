"""Exposed failure witness and corruptions; no repeated integrated schedule."""

import copy
import json
from pathlib import Path

import pytest

from experiments.iter177_pose_aware_seed import failure_check as check

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"experiments/iter177_pose_aware_seed"


def inputs():
    events = [json.loads(line) for line in (BASE/"proof/search_raw/chicane_right/events.jsonl").read_text().splitlines()]
    cases = json.loads((ROOT/"experiments/iter161_grouping_width_ablation/CASES.json").read_text())
    case = next(c for c in cases if c["id"] == "chicane_right")
    old = json.loads((ROOT/"experiments/iter153_action_feasibility/PLAN.json").read_text())
    plan = json.loads((BASE/"PLAN.json").read_text())
    return events, case, old, plan


def test_retained_edge_is_valid_but_cannot_satisfy_strict_next_root_domain():
    result = check.diagnose(*inputs())
    assert result["verified_states"] == 6 and result["attempts_checked"] == 125
    assert result["ulps_above_six"] == 2
    assert result["scalar_motion_and_physical_checks"] and not result["strict_next_root_domain"]


@pytest.mark.parametrize("corruption", ["motion", "mask"])
def test_changed_witness_rejected(corruption):
    events, case, old, plan = inputs()
    if corruption == "motion":
        events[-1]["trace"][-1]["state"][3] = 6
    else:
        events[-1]["trace"][0]["background"]["mask_sha256"] = "0"*64
    with pytest.raises(ValueError):
        check.diagnose(events, case, old, plan)


@pytest.mark.parametrize("corruption,reason", [("failure", "failure_signature"),
                                               ("missing", "incomplete_schedule"),
                                               ("execution", "incomplete_schedule"),
                                               ("closure", "producer_closure")])
def test_invalid_classification_scope_is_bound(corruption, reason):
    failure = dict(status="invalid", error="ValueError:worker_failed:chicane_right")
    cases = ["bend_left", "bend_right", "chicane_left"]
    supervision = dict(status="invalid", returncode=1, process_reaped=True)
    check.scope(failure, cases, False, supervision)
    bad = copy.deepcopy(failure)
    if corruption == "failure":
        bad["error"] = "another failure"
    if corruption == "missing":
        cases.pop()
    if corruption == "closure":
        supervision["process_reaped"] = False
    with pytest.raises(ValueError, match=reason):
        check.scope(bad, cases, corruption == "execution", supervision)
