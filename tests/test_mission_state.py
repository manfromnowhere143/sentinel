from __future__ import annotations

import copy

from scripts.mission_state import load_state, validate_state


def test_committed_mission_state_is_valid() -> None:
    assert validate_state(load_state()) == []


def test_next_iteration_must_follow_completed_iteration() -> None:
    state = copy.deepcopy(load_state())
    state["next_program"]["iteration"] = state["current_completed_iteration"] + 2

    assert any(problem.startswith("next_iteration:") for problem in validate_state(state))


def test_current_verdict_must_be_present_in_result() -> None:
    state = copy.deepcopy(load_state())
    state["current_verdict"] = "IMPOSSIBLE_VERDICT"

    assert "current_verdict_not_in_result:'IMPOSSIBLE_VERDICT'" in validate_state(state)


def test_state_cannot_roll_back_latest_completed_iteration() -> None:
    state = copy.deepcopy(load_state())
    state["current_completed_iteration"] = 133
    state["current_result"] = (
        "experiments/iter133_neuroncap_placebo_semantics_control_design/RESULT.md"
    )
    state["current_verdict"] = "NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE"
    state["next_program"]["iteration"] = 134

    assert "current_completed_iteration:133!=134" in validate_state(state)


def test_every_pending_hypothesis_must_be_classified() -> None:
    state = copy.deepcopy(load_state())
    state["deprecated_pending_hypotheses"] = []

    assert any(
        problem.startswith("pending_hypothesis_classification:")
        for problem in validate_state(state)
    )
