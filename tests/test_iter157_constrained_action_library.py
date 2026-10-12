"""New rejection/admission gates, exercised before any library query."""

import copy
import json
import subprocess

import pytest

from experiments.iter157_constrained_action_library.execute import verdict, select
from experiments.iter157_constrained_action_library.check import (
    classify,
    verify_row,
    selections,
    verify_mask,
    resource_gate,
)
from experiments.iter157_constrained_action_library.support import committed_raw, inputs, sha


def fixture():
    spec = dict(id="maneuver_000", speed=2, offset=0, start=0, length=10)
    prior = dict(candidate=spec, completion_time=0.25, eligible=True)
    states = [[0, 0, 0, 1, 0], [0.25, 0, 0, 1, 0]]
    queries = [
        dict(
            frame=i,
            time=i / 4,
            state=state,
            mask=dict(path=f"maneuver_000_{i:03d}.bin", sha256="0" * 64),
            count=0,
            certain_inside=0,
            possible_inside=0,
            decision="clear",
        )
        for i, state in enumerate(states)
    ]
    row = dict(
        candidate=spec,
        completion_time=0.25,
        prior_eligible=True,
        verdict="qualified",
        queries=queries,
        background_complete=True,
        road_compliance=None,
        physical_occupancy=None,
        useful_recovery=None,
        information_benefit=None,
    )
    return prior, states, row


def test_complete_admission_and_rejection_witness_scope():
    prior, states, row = fixture()
    assert verify_row(row, prior, states) == [0, 1]
    assert verdict(True, row["queries"], 2) == "qualified"
    row["queries"][-1].update(
        count=101, certain_inside=101, possible_inside=101, decision="collision"
    )
    row["verdict"] = "background_collision"
    assert verify_row(row, prior, states) == [1]
    assert verdict(True, row["queries"], 2) == "background_collision"


@pytest.mark.parametrize(
    "kind",
    [
        "candidate",
        "prior",
        "completion",
        "unknown",
        "missing",
        "duplicate",
        "nonconsecutive",
        "state",
        "time",
        "path",
        "count",
        "ambiguity",
        "continued",
        "partial",
        "coverage",
        "favorable",
        "drop_failure",
    ],
)
def test_row_corruptions(kind):
    prior, states, row = fixture()
    if kind == "candidate":
        row["candidate"] = dict(prior["candidate"], id="maneuver_001")
    elif kind == "prior":
        row["prior_eligible"] = False
    elif kind == "completion":
        row["completion_time"] = 0
    elif kind == "unknown":
        row["useful_recovery"] = True
    elif kind == "missing":
        row["queries"] = []
    elif kind == "duplicate":
        row["queries"].append(copy.deepcopy(row["queries"][0]))
    elif kind == "nonconsecutive":
        row["queries"][1]["frame"] = 3
    elif kind == "state":
        row["queries"][0]["state"] = [0, 0, 0, 6, 0]
    elif kind == "time":
        row["queries"][1]["time"] = 0.5
    elif kind == "path":
        row["queries"][0]["mask"]["path"] = "../mask.bin"
    elif kind == "count":
        row["queries"][0]["count"] = -1
    elif kind == "ambiguity":
        row["queries"][1]["possible_inside"] = 101
    elif kind == "continued":
        row["queries"][0].update(
            count=101, certain_inside=101, possible_inside=101, decision="collision"
        )
    elif kind == "partial":
        row["queries"] = row["queries"][:1]
        row["background_complete"] = False
    elif kind == "coverage":
        row["background_complete"] = False
    elif kind == "favorable":
        row["queries"][1].update(
            count=101, certain_inside=101, possible_inside=101, decision="collision"
        )
    elif kind == "drop_failure":
        prior["eligible"] = False
        row["prior_eligible"] = False
    with pytest.raises(ValueError):
        verify_row(row, prior, states)


@pytest.mark.parametrize(
    "count,certain,possible,expected",
    [
        (100, 100, 100, "clear"),
        (101, 101, 101, "collision"),
        (100, 99, 101, "numerically_ambiguous"),
        (101, 100, 102, "numerically_ambiguous"),
    ],
)
def test_strict_threshold_and_abstention(count, certain, possible, expected):
    assert classify(dict(count=count, certain_inside=certain, possible_inside=possible)) == expected


def test_fixed_rankings_and_null():
    _, _, a = fixture()
    b = copy.deepcopy(a)
    a["candidate"]["offset"] = 2
    b["candidate"]["offset"] = 1
    a["completion_time"] = 5
    b["completion_time"] = 6
    b["candidate"]["id"] = "maneuver_001"
    assert selections([a, b]) == ("maneuver_000", "maneuver_001")
    assert select([a, b]) == "maneuver_000" and select([a, b], True) == "maneuver_001"
    a["verdict"] = b["verdict"] = "background_collision"
    assert selections([a, b]) == (None, None) and select([a, b]) is None


@pytest.mark.parametrize("kind", ["valid", "count", "hash", "length", "padding", "missing"])
def test_complete_mask_gate(tmp_path, kind):
    data = bytearray((276519 + 7) // 8)
    if kind == "padding":
        data[-1] = 128
    if kind == "length":
        data.pop()
    path = tmp_path / "mask.bin"
    if kind != "missing":
        path.write_bytes(data)
    q = dict(
        count=1 if kind == "count" else 0,
        mask=dict(path="mask.bin", sha256="0" * 64 if kind == "hash" else sha(data)),
    )
    if kind == "valid":
        assert verify_mask(tmp_path, q) == bytes(data)
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            verify_mask(tmp_path, q)


@pytest.mark.parametrize(
    "field,value",
    [
        ("peak_rss_bytes", 0),
        ("peak_rss_bytes", 1025),
        ("peak_rss_bytes", None),
        ("elapsed_seconds", 0),
        ("elapsed_seconds", 301),
        ("elapsed_seconds", float("nan")),
    ],
)
def test_resource_limits(field, value):
    data = dict(peak_rss_bytes=512, elapsed_seconds=1.0)
    data[field] = value
    with pytest.raises(ValueError):
        resource_gate(data, dict(max_rss_bytes=1024, producer_seconds=300))


def test_input_corruption(tmp_path):
    (tmp_path / "input").write_bytes(b"old")
    plan = dict(inputs={"input": sha(b"old")})
    inputs(tmp_path, plan)
    (tmp_path / "input").write_bytes(b"new")
    with pytest.raises(ValueError, match="input_identity"):
        inputs(tmp_path, plan)


@pytest.mark.parametrize(
    "kind", ["valid", "uncommitted", "extra", "source_drift", "wrong_source", "budget"]
)
def test_committed_raw_source_gates(tmp_path, kind):
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(tmp_path), *args], stderr=subprocess.DEVNULL
        )

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    base = tmp_path / "experiments/iter157_constrained_action_library"
    base.mkdir(parents=True)
    plan = dict(inputs={}, source_files=["query.py"], max_output_bytes=1024)
    (base / "PLAN.json").write_text(json.dumps(plan))
    (tmp_path / "query.py").write_text("pass\n")
    git("add", ".")
    git("commit", "-qm", "fixture source")
    source = git("rev-parse", "HEAD").decode().strip()
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "one.json").write_text("{}")
    git("add", ".")
    git("commit", "-qm", "fixture raw")
    commit = git("rev-parse", "HEAD").decode().strip()
    data = dict(source_commit=source, plan_sha256=sha((base / "PLAN.json").read_bytes()))
    if kind == "uncommitted":
        (raw / "one.json").write_text('{"favorable":true}')
    elif kind == "extra":
        (raw / "hidden.json").write_text("{}")
    elif kind == "source_drift":
        (tmp_path / "query.py").write_text("changed\n")
    elif kind == "wrong_source":
        data["source_commit"] = "0" * 40
    elif kind == "budget":
        plan["max_output_bytes"] = 1
    if kind == "valid":
        assert len(committed_raw(tmp_path, raw, commit, plan, data)) == 1
    else:
        with pytest.raises(ValueError):
            committed_raw(tmp_path, raw, commit, plan, data)


@pytest.mark.parametrize("count", [None, False, -1, 0, 1194])
def test_query_resource_bound(count):
    from experiments.iter157_constrained_action_library.support import query_budget

    query_budget(1193, 1193)
    with pytest.raises(ValueError, match="query_budget"):
        query_budget(count, 1193)
