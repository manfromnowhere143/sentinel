"""Arithmetic controls for the labelled post-outcome work audit."""

import pytest
from experiments.iter174_forward_integrated_rrt.diagnostics import selection_summary


def trial(identity, prefix, selected, interrupted=None):
    return dict(kind="evaluation", id=identity, trace=[dict(frame=f) for f in [14, 15, 16]],
                valid_prefix=prefix, selected_prefix=selected, interrupted=interrupted)


def connection(call, selected, attempts):
    return dict(kind="connection", call=call, result=dict(selected_evaluation=selected, attempts=attempts))


def test_work_after_selection_and_no_edge_are_separate():
    rows = [trial(1, 2, 1), trial(2, 1, 1), connection(1, 1, 4),
            trial(1, 0, 0), connection(2, None, 2),
            dict(kind="connection", call=3, result=None)]
    r = selection_summary(rows)
    assert r["accepted_requests"] == r["final_selection_by_128"] == 1
    assert r["attempts_after_final_selection"] == r["attempts_without_edge"] == 2
    assert r["maximum_reported_valid_frame"] == 16 and r["truncated_trial_prefixes"] == 1
    assert r["calls"][1]["final_selection_at"] is None


def test_interrupted_rollout_cannot_supply_a_valid_extension():
    r = selection_summary([trial(1, 2, 0, "time_budget"), connection(1, None, 2)])
    assert r["maximum_reported_valid_frame"] == r["truncated_trial_prefixes"] == 0
    assert r["attempts_without_edge"] == 2


def test_missing_selected_evaluation_rejected():
    with pytest.raises(AssertionError, match="diagnostic_selection"):
        selection_summary([trial(1, 2, 1), connection(1, 999, 2)])
