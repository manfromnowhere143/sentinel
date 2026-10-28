"""Known-bad selection and ancestry controls for the exploratory branch audit."""

import copy
import pytest
from experiments.iter193_history_delay.frontier_audit import selected, reconstruct
from experiments.iter193_history_delay import frontier_audit


def sequences():
    def row(frame, state, progress):
        return dict(frame=frame, state=[state] * 5, route=dict(rc=progress))

    return {
        "1": dict(node=2, parent=1, trace=[row(0, 0, 0), row(1, 1, 0.2)]),
        "3": dict(node=3, parent=2, trace=[row(1, 1, 0.2), row(2, 2, 0.4)]),
    }


def test_selection_and_reconstruction():
    values = sequences()
    assert selected(values) == 3
    assert [r["frame"] for r in reconstruct(values, 3)] == [0, 1, 2]
    values["3"]["trace"][-1]["route"]["rc"] = 0.2
    assert selected(values) == 2
    values["3"]["trace"][-1]["frame"] = 1
    assert selected(values) == 2


@pytest.mark.parametrize("kind", ["missing", "cycle", "join", "duplicate"])
def test_bad_ancestry_rejected(kind):
    values = copy.deepcopy(sequences())
    if kind == "missing":
        del values["1"]
    elif kind == "cycle":
        values["3"]["parent"] = 3
    elif kind == "join":
        values["3"]["trace"][0]["state"][0] += 1
    else:
        values["1"]["node"] = 3
    with pytest.raises(ValueError):
        reconstruct(values, 3)


def test_changed_primary_admission_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(frontier_audit, "read", lambda *args: b"changed")
    monkeypatch.setattr(frontier_audit, "git", lambda *args: b"original")
    with pytest.raises(ValueError, match="primary_admission_changed"):
        frontier_audit.bind_primary(tmp_path)
