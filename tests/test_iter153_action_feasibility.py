from copy import deepcopy
import json
from pathlib import Path
import time

import pytest

from experiments.iter153_action_feasibility import check, geometry, planner, qualify, search
from experiments.iter153_action_feasibility.inputs import BASE, digest, document, load

ROOT = Path(__file__).resolve().parents[1]
PLAN = document(ROOT / BASE / "PLAN.json")


@pytest.fixture(scope="module")
def sample():
    g = dict(
        route=[[0, float(i)] for i in range(12)],
        reset=[0, 0, 0, 1, 0],
        ego_dimensions=[1.6, 3, 1.5],
        obstacles=[[100.0, 0.0, 0.0, 2.0, 4.0, 2.0, 0.0]],
        comparators=dict(
            nominal=dict(hazard_time=7.75, rc=0.3), monitor=dict(hazard_time=9.0, rc=0.3)
        ),
    )
    spec = planner.candidates(PLAN)[0]
    raw = search.trial(g, spec, PLAN, 1, time.monotonic() + 30)
    return g, spec, raw


def test_source_and_retained_evidence():
    q = qualify.run(ROOT)
    assert q["status"] == "supported"
    assert q["historical_actions_replayed"] == 134
    assert len(q["source_transition_fixtures"]) == 48
    assert len(q["source_rectangle_fixtures"]) == 12
    assert len(q["independent_rectangle_pairs"]) == 27


def test_fixed_inventory_and_policy_replay(sample):
    assert planner.candidates(PLAN) == check.population(PLAN)
    assert len(planner.candidates(PLAN)) == 75
    g, spec, raw = sample
    result = check.verify_trial(raw, g, spec, PLAN, 1)
    assert result["eligible"] and result["live_recovery"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "state",
        "action",
        "axis",
        "yaw",
        "width",
        "missing_obstacle",
        "false_success",
        "false_clearance",
        "false_progress",
        "false_background",
        "false_road",
        "wrong_replica",
        "extra_field",
        "boolean_verdict",
        "short_trace",
    ],
)
def test_independent_checker_rejects_corruption(sample, fault):
    oldg, spec, old = sample
    g, raw = deepcopy(oldg), deepcopy(old)
    if fault == "state":
        raw["states"][2][0] += 0.1
    if fault == "action":
        raw["actions"][0][0] = 2.1
    if fault == "axis":
        g["route"] = [p[::-1] for p in g["route"]]
    if fault == "yaw":
        raw["states"][1][2] += 0.5
    if fault == "width":
        g["ego_dimensions"][0] = -1
    if fault == "missing_obstacle":
        g["obstacles"] = []
    if fault == "false_success":
        raw["stop"] = "foreground_contact"
    if fault == "false_clearance":
        raw["producer"]["swept_clear"] = False
    if fault == "false_progress":
        raw["producer"]["progress"]["nominal"] = False
    if fault == "false_background":
        raw["background_collision"] = False
    if fault == "false_road":
        raw["road_compliance"] = True
    if fault == "wrong_replica":
        raw["replica"] = True
    if fault == "extra_field":
        raw["safety_guaranteed"] = True
    if fault == "boolean_verdict":
        raw["producer"]["eligible"] = 1
    if fault == "short_trace":
        raw["actions"].pop()
    # Bind changed geometry so the challenge reaches the actual independent model checks.
    raw["geometry_sha256"] = digest(g)
    with pytest.raises((ValueError, IndexError, TypeError)):
        check.verify_trial(raw, g, spec, PLAN, 1)


def test_between_sample_contact_and_touching():
    a, b = [0, 0, 0, 4, 0], [4, 0, 0, 4, 0]
    dims = [1, 1, 1]
    obs = [[2, 0, 1, 1, 0]]
    assert check.gap([0, 0, 1, 1, 0], obs[0]) > 0 and check.gap([4, 0, 1, 1, 0], obs[0]) > 0
    assert not check.swept(a, b, dims, obs, PLAN)
    assert not geometry.sweep_clear(a, b, dims, obs, PLAN)
    assert check.gap([0, 0, 2, 2, 0], [2, 0, 2, 2, 0]) == 0


@pytest.mark.parametrize(
    "state,action",
    [
        ([0, 0, 0, 6.1, 0], [0, 0]),
        ([0, 0, 0, -0.1, 0], [0, 0]),
        ([0, 0, 0, 1, 0], [2.1, 0]),
        ([0, 0, 0, 1, 0], [0, 0.27]),
        ([0, 0, 0, 1, 1.1], [0, 0]),
        ([0, 0, 0, 6, 0.8], [0, 0]),
    ],
)
def test_control_limits(state, action):
    assert not planner.limits(state, action, PLAN)


def test_unknown_progress_after_early_contact(sample):
    g, spec, _ = deepcopy(sample)
    g["obstacles"] = [[3, 0, 0, 2, 4, 2, 0]]
    raw = search.trial(g, spec, PLAN, 1, time.monotonic() + 30)
    result = check.verify_trial(raw, g, spec, PLAN, 1)
    assert result["stop"] == "initial_contact"
    assert not result["eligible"]
    assert result["progress"] == dict(nominal=None, monitor=None)


def test_budget_partial_is_not_success(sample):
    g, spec, _ = sample
    raw = search.trial(g, spec, PLAN, 1, time.monotonic() - 1)
    assert raw["stop"] == "budget_expired"
    with pytest.raises(ValueError, match="unexpected_partial"):
        check.verify_trial(raw, g, spec, PLAN, 1)


@pytest.mark.parametrize("payload", [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":1e999}'])
def test_strict_record(tmp_path, payload):
    p = tmp_path / "record.json"
    p.write_bytes(payload)
    with pytest.raises(ValueError):
        document(p)


def test_no_follow(tmp_path):
    p = tmp_path / "record.json"
    p.write_text("{}")
    q = tmp_path / "link.json"
    q.symlink_to(p)
    with pytest.raises(OSError):
        document(q)


def test_wrong_search_path(tmp_path):
    with pytest.raises(ValueError, match="search_directory"):
        search.execute(ROOT, tmp_path / "wrong")


@pytest.mark.parametrize("fault", ["missing", "extra", "duplicate"])
def test_raw_inventory(tmp_path, fault):
    specs = check.population(PLAN)
    for name in ["initialized.json", "geometry.json", "execution.json"] + [
        f"{s['id']}_{r}.json" for s in specs for r in (1, 2)
    ]:
        (tmp_path / name).write_text("{}")
    if fault == "missing":
        (tmp_path / "maneuver_000_1.json").unlink()
    else:
        (tmp_path / ("unexpected.json" if fault == "extra" else "maneuver_000_3.json")).write_text(
            "{}"
        )
    with pytest.raises(ValueError, match="raw_inventory"):
        check.inventory(tmp_path, specs, 2)


def test_input_hash_mutation(tmp_path):
    base = tmp_path / BASE
    base.mkdir(parents=True)
    path = tmp_path / "source"
    path.write_text("changed")
    (base / "INPUTS.json").write_text(
        json.dumps(dict(files={"source": dict(bytes=3, sha256="a" * 64)}))
    )
    with pytest.raises(ValueError, match="input_identity"):
        load(tmp_path)


@pytest.mark.parametrize("fault", ["qualification", "source", "geometry", "duplicate"])
def test_execution_initialization_guards(tmp_path, monkeypatch, sample, fault):
    g, _, _ = sample
    base = tmp_path / BASE
    base.mkdir(parents=True)
    (base / "proof").mkdir()
    (base / "PLAN.json").write_text(json.dumps(PLAN))
    q = dict(
        status="failed" if fault == "qualification" else "supported",
        geometry_sha256="wrong" if fault == "geometry" else digest(g),
    )
    (base / "QUALIFICATION.json").write_text(json.dumps(q))
    binding = dict(files={})
    if fault == "source":
        (tmp_path / "code").write_text("different")
        binding["files"]["code"] = dict(bytes=9, sha256="0" * 64)
    (base / "SOURCE.json").write_text(json.dumps(binding))
    monkeypatch.setattr(search, "load", lambda root: g)
    seen = []

    def failure(*args):
        seen.append(True)
        raise RuntimeError("constructed execution failure")

    monkeypatch.setattr(search, "trial", failure)
    output = base / "proof/search_000"
    if fault == "duplicate":
        assert search.execute(tmp_path, output) == 1
        assert len(seen) == 1
        assert document(output / "execution.json")["retained_trials"] == 0
        with pytest.raises(FileExistsError):
            search.execute(tmp_path, output)
        assert len(seen) == 1
    else:
        with pytest.raises(ValueError):
            search.execute(tmp_path, output)
        assert not output.exists() and not seen


def test_collision_cannot_be_promoted_to_success(sample):
    g, spec, _ = deepcopy(sample)
    g["obstacles"] = [[6, 0, 0, 2, 4, 2, 0]]
    raw = search.trial(g, spec, PLAN, 1, time.monotonic() + 30)
    assert raw["stop"] == "foreground_contact"
    raw["stop"] = "model_complete"
    raw["producer"].update(model_complete=True, eligible=True)
    with pytest.raises(ValueError, match="stop_reason"):
        check.verify_trial(raw, g, spec, PLAN, 1)
