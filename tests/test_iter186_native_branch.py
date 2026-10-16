"""Native identity, deadlines and prospective selection; no development-case searches."""

import copy
import os
from pathlib import Path

import pytest

from experiments.iter186_native_branch import fixtures, native, selection, transport


@pytest.fixture
def library():
    path = os.environ.get("SENTINEL_RRT186_LIBRARY")
    if not path:
        pytest.skip("Iter186 native build unavailable")
    return Path(path)


def test_extra_becomes_exact_native_parent(library):
    result = fixtures.extra(library)
    assert result["status"] == 2 and result["stop_code"] == 3
    assert [r[7:10] for r in result["rows"]] == [[1, 0, 0], [3, 1, 1], [4, 3, 1]]
    assert [r[6] for r in result["rows"]] == [0, 2, 3]
    assert [r["kind"] for r in result["events"]] == [0, 3, 1, 2, 3, 1]


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("parent", "branch_parent"),
        ("before", "branch_parent"),
        ("token", "branch_token"),
        ("reused_token", "branch_token"),
        ("duration", "branch_duration"),
        ("flags", "branch_eligibility"),
        ("finite", "branch_finite"),
        ("duplicate", "branch_duplicate"),
        ("count", "branch_count"),
    ],
)
def test_native_corruption_rejected(library, mutation, reason):
    with pytest.raises(ValueError, match=reason):
        fixtures.extra(library, mutation=mutation)


@pytest.mark.parametrize(
    "expiry",
    ["initial", "before_callback", "after_callback", "after_primary", "after_extra", "after_goal"],
)
def test_deadline_has_precedence(library, expiry):
    result = fixtures.extra(library, expiry=expiry)
    assert result["status"] == 0 and result["stop_code"] == 2 and result["rows"] == []
    if expiry in ("initial", "before_callback"):
        assert result["directed_calls"] == 0


def state(x, frame):
    return dict(state=[float(x), 0.0, 0.0, 1.0, 0.0], frame=frame, action=[0.0, 0.0])


def evaluation(number, x, frame=2):
    return dict(
        id=number,
        trace=[state(0, 0), state(x, frame)],
        valid_prefix=1,
        interrupted=None,
        eligibility=dict(eligible_prefix=1, complete=True),
    )


def test_one_advancing_branch_ties_and_selected_edge_exclusion():
    route = [[0.0, float(i)] for i in range(12)]
    primary = dict(trace=[state(0, 0), state(2, 1)])
    evaluations = [evaluation(3, 8, 3), evaluation(2, 8, 2), evaluation(1, 8, 2)]
    chosen = selection.choose(evaluations, primary, 1, set(), route)
    assert (chosen["evaluation"], chosen["prefix"], chosen["nearest_index"]) == (1, 1, 8)
    assert selection.choose(evaluations, primary, 8, set(), route) is None
    assert (
        selection.choose(
            evaluations,
            primary,
            1,
            {selection.endpoint(state(8, 2)), selection.endpoint(state(8, 3))},
            route,
        )
        is None
    )
    assert selection.choose([evaluation(1, 2, 1)], primary, 1, set(), route) is None


@pytest.mark.parametrize("mutation", ["invalid", "ineligible", "interrupted", "unfinished"])
def test_selection_rejects_unusable_work(mutation):
    row = evaluation(1, 8)
    if mutation == "invalid":
        row["valid_prefix"] = row["eligibility"]["eligible_prefix"] = 0
    elif mutation == "ineligible":
        row["eligibility"]["eligible_prefix"] = 0
    elif mutation == "interrupted":
        row["interrupted"] = "time_budget"
    else:
        row["eligibility"]["complete"] = False
    assert (
        selection.choose(
            [row],
            dict(trace=[state(0, 0), state(1, 1)]),
            0,
            set(),
            [[0.0, float(i)] for i in range(12)],
        )
        is None
    )


def example():
    start = [0.0, 0.0, 0.0, 1.0, 0.0, 0]
    segment = [dict(state(0, 0), action=None), state(1, 1), state(2, 2)]
    rows = [[*start, 0, 1, 0, 0, 0], [*segment[-1]["state"], 2, 17, 3, 1, 2, 0.5]]
    sequences = {17: dict(parent=1, node=3, trace=segment)}
    return start, rows, sequences


def test_transport_positive_and_integer_tokens():
    start, rows, sequences = example()
    trace, tokens = transport.expand(rows, sequences, start)
    assert [(r["state"], r["frame"], r["action"]) for r in trace] == [
        (r["state"], r["frame"], r["action"]) for r in sequences[17]["trace"]
    ] and tokens == [17]
    with pytest.raises(ValueError, match="token_encoding"):
        native.branch(1, 1.5, trace)


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_token",
        "parent_id",
        "node",
        "duration",
        "steps",
        "endpoint",
        "parent_state",
        "clock",
    ],
)
def test_transport_corruption_rejected(mutation):
    start, rows, sequences = example()
    rows, sequences = copy.deepcopy(rows), copy.deepcopy(sequences)
    if mutation == "unknown_token":
        rows[1][6] = 999
    elif mutation == "parent_id":
        rows[1][8] = 2
    elif mutation == "node":
        sequences[17]["node"] = 4
    elif mutation == "duration":
        rows[1][10] += 0.25
    elif mutation == "steps":
        rows[1][9] = 1
    elif mutation == "endpoint":
        rows[1][0] += 0.1
    elif mutation == "parent_state":
        sequences[17]["trace"][0]["state"][0] += 0.1
    else:
        sequences[17]["trace"][1]["frame"] = 99
    with pytest.raises(ValueError, match="native_"):
        transport.expand(rows, sequences, start)


def test_primary_completion_ends_before_extra(library):
    calls = []

    def branches(parent, before, target):
        calls.append(parent)
        primary = fixtures.row(parent, 1, before, 1.0)
        extra = fixtures.row(parent, 2, before, 2.0)
        extra["flags"] = 0  # Must never be inserted after the primary completes.
        return [primary, extra]

    result = native.solve(
        library,
        fixtures.SEED,
        fixtures.START,
        fixtures.LOW,
        fixtures.HIGH,
        fixtures.TARGET,
        branches,
        lambda state: 0.0,
        lambda: bool(calls),
        lambda: False,
        lambda: fixtures.TARGET,
    )
    assert result["status"] == 2
    assert [r["kind"] for r in result["events"]] == [0, 3, 1]


def test_native_identical_states_keep_distinct_parent_identity(library):
    # Separate primary edges may reach the exact same numeric state. Their IDs
    # must stay distinct, and the next request must identify which node it used.
    calls = 0

    def branches(parent, before, target):
        nonlocal calls
        calls += 1
        return [fixtures.row(parent, calls, before, 1.0)]

    result = native.solve(
        library,
        fixtures.SEED,
        fixtures.START,
        fixtures.LOW,
        fixtures.HIGH,
        fixtures.START,
        branches,
        lambda state: 1.0,
        lambda: calls >= 3,
        lambda: False,
        lambda: fixtures.START,
    )
    registrations = [r for r in result["events"] if r["kind"] == 1]
    assert [r["node"] for r in registrations] == [2, 3, 4]
    assert all(r["parent"] == 1 for r in registrations)
    assert registrations[0]["state"] == registrations[1]["state"] == registrations[2]["state"]


def test_independent_selection_rejects_wrong_winner():
    from experiments.iter186_native_branch import check, qualify

    rows = qualify.selection_controls()
    check.selection(rows)
    rows[0]["result"]["evaluation"] = 3
    with pytest.raises(ValueError, match="selection_rank"):
        check.selection(rows)


def test_independent_tree_rejects_ambiguous_numeric_parent():
    from experiments.iter186_native_branch.check import tree

    state = [1.0, 0.0, 0.0, 1.0, 0.0, 1.0]
    root = dict(kind=0, node=1, parent=0, token=0, steps=0, state=fixtures.START, target=None)
    request = dict(kind=3, node=1, parent=1, token=0, steps=0, state=fixtures.START, target=state)
    one = dict(kind=1, node=2, parent=1, token=1, steps=1, state=state, target=None)
    two = dict(one, node=3, token=2)
    value = dict(events=[root, request, one, request, two], rows=[])
    assert len(tree(value)) == 3
    bad = copy.deepcopy(value)
    bad["events"][-1]["parent"] = 2
    with pytest.raises(ValueError, match="event_parent"):
        tree(bad)


def test_runtime_rejects_wrong_native_binary(tmp_path, monkeypatch):
    from experiments.iter186_native_branch import runtime

    path = tmp_path / "wrong.dylib"
    path.write_bytes(b"wrong")
    monkeypatch.setattr(runtime, "document", lambda *args: dict(bridge_sha256="0" * 64))
    with pytest.raises(ValueError, match="bridge_identity"):
        runtime.verify(tmp_path, path, path, tmp_path)
