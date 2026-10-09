"""Capture-to-actuation fixtures and adversarial checks for the frozen canary."""

from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pytest

from experiments.iter137_controller_execution_contract.verify import Replay
from experiments.iter141_nominal_continuation import (
    client,
    fixture,
    independent,
    instrument,
    live_trace,
    run_episode,
    summarize,
    trace,
    verify_live as v,
)


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    root = tmp_path_factory.mktemp("iter141")
    values = {}
    replay = Replay()
    # macOS Accelerate is not exposed by threadpoolctl. This local synthetic
    # fixture mocks only that observation; the bound host fixture does not.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(live_trace, "threadpool_info", lambda: [dict(num_threads=1)])
        for arm in ("reference_a", "reference_b", "nominal_a", "nominal_b"):
            fixture.run(root / arm, arm)
            values[arm] = v.validate_episode(root / arm, replay)
    return root, values


def test_full_path_and_replicas(captured):
    root, data = captured
    a, ca, da, _ = data["reference_a"]
    for arm in ("reference_b", "nominal_a", "nominal_b"):
        b, cb, db, _ = data[arm]
        result = v.compare(a, b, ca, cb, da, db)
        assert result["prefix"] == "matched"
        if arm.startswith("nominal"):
            assert result["first_contrast"] == 1
            endpoint = v.outcomes(a, b, db)
            assert endpoint["useful_recovery"]
            assert independent.check(root / "reference_a", root / arm)["outcomes"] == endpoint
        assert len({d["nominal"]["sha256"] for d in db}) == 4
    b, cb, db, _ = data["nominal_a"]
    n, cn, dn, _ = data["nominal_b"]
    assert v.compare(b, n, cb, cn, db, dn)["prefix"] == "matched"
    assert independent.check(root / "nominal_a", root / "nominal_b")["prefix"] == "matched"


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "reordered",
        "mode",
        "dtype",
        "bytes",
        "nominal",
        "proposed",
        "delivered",
        "monitor",
        "control",
        "time",
    ],
)
def test_linkage_known_bads(captured, bad):
    root, data = captured
    a, c, d, _ = deepcopy(data["nominal_a"])
    m, raw = v.read(root / "nominal_a/sentinel_iter48_decisions.jsonl")
    if bad == "missing":
        d.pop()
    elif bad == "reordered":
        d.reverse()
    elif bad == "mode":
        d[0]["mode"] = "reference"
    elif bad == "dtype":
        d[0]["nominal"]["dtype"] = "<f8"
    elif bad == "bytes":
        d[0]["delivered"]["bytes_hex"] = "00"
    elif bad in ("nominal", "proposed", "delivered"):
        d[1][bad] = (
            client.typed(np.zeros((6, 2), dtype="float32"))
            if bad != "proposed"
            else d[1]["nominal"]
        )
    elif bad == "monitor":
        m[0]["params"] = {}
    elif bad == "control":
        a[0 + 1]["control"][0] += 1
    elif bad == "time":
        c[1]["time"] = 10
    with pytest.raises(ValueError):
        v.validate_linkage(a, c, d, m, raw)


@pytest.mark.parametrize(
    "control,steer",
    [([3.01, 0], 0), ([0, 0.41], 0), ([0, 0], 1.1), ([0, float("nan")], 0), ([True, 0], 0)],
)
def test_control_envelope_known_bads(control, steer):
    with pytest.raises(ValueError):
        v.control_envelope(control, steer)


def test_declared_gym_violation_is_retained():
    assert v.control_envelope([-3.0, 0.4], 0.0) is True
    assert v.control_envelope([2.0, 0.0], 0.0) is False


@pytest.mark.parametrize("bad", ["observation", "nominal", "numerical", "runtime"])
def test_prefix_known_bads(captured, bad):
    _, data = captured
    a, ca, da, _ = data["reference_a"]
    b, cb, db, _ = deepcopy(data["nominal_a"])
    if bad == "observation":
        b[2]["observation_sha256"] = "f" * 64
    elif bad == "nominal":
        db[1]["nominal"]["sha256"] = "f" * 64
    elif bad == "numerical":
        cb[1]["receipt"]["numerical"]["control"][0] += 1
    else:
        cb[0]["numpy"] = "other"
    with pytest.raises(ValueError):
        v.compare(a, b, ca, cb, da, db)


def test_replica_known_bad(captured):
    _, data = captured
    a, ca, da, _ = data["nominal_a"]
    b, cb, db, _ = deepcopy(data["nominal_b"])
    b[-2]["route_completion"] -= 0.01
    with pytest.raises(ValueError, match="replica"):
        v.compare(a, b, ca, cb, da, db)


def write_rows(path, rows):
    path.write_bytes(b"\n".join(trace.canonical(x) for x in rows) + b"\n")


@pytest.mark.parametrize("reason", ["truncated", "collision", "other_termination"])
def test_early_end_not_recovery(captured, tmp_path, reason):
    root, data = captured
    a, _, _, _ = data["reference_a"]
    b, _, ds, _ = deepcopy(data["nominal_a"])
    b = b[:3] + [dict(end="completed", frames=2, reason=reason)]
    ds = ds[:2]
    b[-2].update(
        terminated=reason != "truncated",
        truncated=reason == "truncated",
        collision=reason == "collision",
        route_completion=0.2,
    )
    trace.validate(b)
    out = v.outcomes(a, b, ds)
    assert not out["useful_recovery"] and out["hazard_progress"] is None
    write_rows(tmp_path / "iter141_trace.jsonl", b)
    write_rows(tmp_path / "delivery141.jsonl", ds)
    assert independent.check(root / "reference_a", tmp_path)["outcomes"] == out


def test_hazard_survival_is_not_recovery(captured):
    _, data = captured
    a, _, _, _ = data["reference_a"]
    b, _, ds, _ = deepcopy(data["nominal_a"])
    b[-2].update(terminated=False, truncated=True, route_completion=0.3)
    b[-1]["reason"] = "truncated"
    out = v.outcomes(a, b, ds)
    assert out["collision_free_through_hazard"] and not out["useful_recovery"] and out["censored"]


@pytest.mark.parametrize("bad", ["outcome", "control", "bytes", "prefix", "missing"])
def test_independent_known_bads(captured, tmp_path, bad):
    root, data = captured
    b, _, ds, _ = deepcopy(data["nominal_a"])
    if bad == "outcome":
        b[-2]["collision"] = None
    elif bad == "control":
        b[1]["control"] = [3.1, 0.0]
    elif bad == "bytes":
        ds[0]["nominal"]["bytes_hex"] = "00"
    elif bad == "prefix":
        b[2]["observation_sha256"] = "f" * 64
    else:
        ds.pop()
    write_rows(tmp_path / "iter141_trace.jsonl", b)
    write_rows(tmp_path / "delivery141.jsonl", ds)
    with pytest.raises(ValueError):
        independent.check(root / "reference_a", tmp_path)


def test_monitor_disabled_and_error_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_I141_MODE", "nominal")
    plan = np.ones((6, 2), dtype="float32")
    with pytest.raises(ValueError, match="enabled"):
        client.deliver(plan, None, {"timestamp": 0}, tmp_path, lambda *a: plan, False)

    def failure(*args):
        (tmp_path / "sentinel_iter48_decisions.jsonl").write_text('{"trace_error":"failure"}\n')
        return plan

    with pytest.raises(ValueError, match="alignment/error"):
        client.deliver(plan, None, {"timestamp": 0}, tmp_path, failure, True)


@pytest.mark.parametrize("dtype", ["int32", "float16"])
def test_client_rejects_dtype(dtype):
    with pytest.raises(ValueError):
        client.typed(np.ones((6, 2), dtype=dtype))


def test_source_identity_known_bad():
    with pytest.raises(ValueError, match="identity"):
        instrument.instrument_client(b"wrong source")


@pytest.mark.parametrize(
    "free,remaining,exists", [(99, 1230, False), (101, 1229, False), (101, 1230, True)]
)
def test_resource_gates(free, remaining, exists):
    with pytest.raises(ValueError):
        run_episode.check_budget(free, remaining, exists)


def test_predecessor_gate(tmp_path):
    folder = tmp_path / "scene-0411_hard_00"
    folder.mkdir()
    files = {}
    for name in v.FILES:
        (folder / name).write_bytes(b"proof")
        files[name] = hashlib.sha256(b"proof").hexdigest()
    report = dict(
        status="validated", candidate=dict(files=files), prefix="matched", verdict="REPLAY_MATCHED"
    )
    run_episode.check_predecessor(report, "reference_b", tmp_path)
    bad = deepcopy(report)
    bad["verdict"] = "REPLAY_DIVERGED"
    with pytest.raises(ValueError):
        run_episode.check_predecessor(bad, "reference_b", tmp_path)
    (folder / v.FILES[0]).write_bytes(b"changed")
    with pytest.raises(ValueError):
        run_episode.check_predecessor(report, "nominal_a", tmp_path)


def test_decision_no_partial_success():
    assert summarize.summarize({})["verdict"] == "SCHEDULE_INCOMPLETE"
    reports = {a: dict(status="validated") for a in run_episode.ARMS}
    reports["reference_b"]["verdict"] = "REPLAY_MATCHED"
    for a in ("nominal_a", "nominal_b"):
        reports[a].update(
            prefix="matched",
            outcomes=dict(useful_recovery=True, censored=False, action_contrast_observed=True),
        )
    reports["nominal_b"]["nominal_replica"] = dict(prefix="matched")
    assert summarize.summarize(reports)["status"] == "supported"
    for a in ("nominal_a", "nominal_b"):
        reports[a]["outcomes"]["useful_recovery"] = False
    assert summarize.summarize(reports)["status"] == "null"
    reports["nominal_a"]["outcomes"]["censored"] = True
    assert summarize.summarize(reports)["status"] == "inconclusive"
    reports["nominal_b"]["nominal_replica"]["prefix"] = "different"
    assert summarize.summarize(reports)["status"] == "invalid"


def test_independent_has_no_primary_import():
    text = Path(independent.__file__).read_text()
    assert "from experiments" not in text and "import numpy" not in text


def test_historical_reference_and_known_bad():
    from experiments.iter138_numerical_live_replay.verify_live import read_contract
    from experiments.iter139_finite_pulse_recoverability.trace import load_trace

    root = Path(__file__).resolve().parents[1]
    folder = (
        root
        / "experiments/iter139_finite_pulse_recoverability/proof/live/reference_a/scene-0411_hard_00"
    )
    a = load_trace(folder / "iter139_trace.jsonl")
    c = read_contract(folder / "controller139.jsonl")
    a[0]["schema"] = trace.SCHEMA
    c[0]["schema"] = "sentinel.iter141.controller_trace.v1"
    assert v.historical(a, c, folder) == "matched"
    a[1]["observation_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="historical reference trace"):
        v.historical(a, c, folder)


def test_no_action_contrast_cannot_support_recovery(captured):
    _, data = captured
    a, _, _, _ = data["reference_a"]
    b, _, ds, _ = deepcopy(data["nominal_a"])
    for d in ds:
        d["proposed"] = deepcopy(d["nominal"])
    result = v.outcomes(a, b, ds)
    assert not result["action_contrast_observed"] and not result["useful_recovery"]
