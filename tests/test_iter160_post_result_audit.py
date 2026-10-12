"""Post-result log audit must separate a cell winner from beam retention."""

import copy

import pytest

from experiments.iter160_continuation_preservation.post_result_audit import follow


def fixture():
    first = dict(
        id=1,
        parent=0,
        frame=1,
        action=[0, 0],
        state=[0.5, 0, 0, 2, 0],
        reason="clear",
        route=dict(nearest=1, distance=0, rc=0.1),
        guide_distance=10,
        effort=0,
    )
    second = dict(first, id=2, parent=1, frame=2, state=[1, 0, 0, 2, 0], guide_distance=9)
    winner = dict(second, id=3, action=[0, 0.01], guide_distance=8)
    rows = [dict(first, id=0, parent=None, frame=0), first, second, winner]
    depths = [dict(frame=1, complete=True, beam=[1]), dict(frame=2, complete=True, beam=[3])]
    return rows, depths, copy.deepcopy(rows[:3])


def test_cell_winner_can_also_lose_to_width():
    rows, depths, trace = fixture()
    depths[1]["beam"] = []
    result = follow(rows, depths, trace, 1, 1)
    assert result["cause"] == "cell_representative" and result["replacement_in_beam"] is False
    depths[0]["beam"] = []
    assert follow(rows, depths, trace, 1, 1)["cause"] == "initial_representative_not_in_beam"


def test_width_and_run_stopping_are_distinct():
    rows, depths, trace = fixture()
    rows.pop()
    depths[1]["beam"] = []
    assert follow(rows, depths, trace, 1, 1)["cause"] == "beam_width"
    depths[1]["complete"] = False
    assert follow(rows, depths, trace, 1, 1)["cause"] == "run_stopped_before_continuation"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("state", "state_binding"),
        ("missing", "covered_child"),
        ("reject", "admitted_child_rejected"),
    ],
)
def test_bad_continuation_binding_fails(mutation, reason):
    rows, depths, trace = fixture()
    rows.pop()
    if mutation == "state":
        rows[2]["state"] = [1.1, 0, 0, 2, 0]
    elif mutation == "missing":
        rows.pop()
    else:
        rows[2]["reason"] = "collision"
    with pytest.raises(ValueError, match=reason):
        follow(rows, depths, trace, 1, 1)
