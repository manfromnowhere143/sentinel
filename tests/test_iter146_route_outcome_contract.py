from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.iter146_route_outcome_contract.check import read, strict, verify
from experiments.iter146_route_outcome_contract.client import instrument
from experiments.iter146_route_outcome_contract.compare import compare, replicas
from experiments.iter146_route_outcome_contract.fixtures import execute
from experiments.iter146_route_outcome_contract.resources import (
    output_guard,
    proposed_storage,
    CASE_STOP,
)
from experiments.iter146_route_outcome_contract.runner import classify, Journal

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def completion(tmp_path_factory):
    path = tmp_path_factory.mktemp("route146").resolve() / "completion"
    summary = execute(ROOT, path)
    assert summary["status"] == "completed", summary["stop_reason"]
    return read(path)


def test_source_completion_is_proxy_not_literal_end(completion):
    report = verify(*completion)
    assert report["outcome"]["completion_qualified"]
    assert report["outcome"]["final_sample_observed"] is False
    assert report["outcome"]["collision_observed"] is False


@pytest.mark.parametrize("arm", ["nominal", "monitor", "brake_t0", "brake_t2_5"])
def test_all_arms_reach_full_401_action_cap(tmp_path, arm):
    path = tmp_path.resolve() / arm
    summary = execute(ROOT, path, kind="censor", arm=arm)
    assert summary["status"] == "completed", summary["stop_reason"]
    report = verify(*read(path))
    assert report["steps"] == 401
    assert report["outcome"]["censored"] and not report["outcome"]["completion_qualified"]
    if arm.startswith("brake"):
        start = 0 if arm == "brake_t0" else 10
        rows = report["scientific"]
        assert all(r["action"][0] <= 0 for r in rows[start : start + 4])
        assert rows[start + 4]["action"] == rows[start + 4]["nominal_action"]


@pytest.mark.parametrize("kind", ["collision_completion", "off_route"])
def test_source_failure_overrides_reward(tmp_path, kind):
    path = tmp_path.resolve() / kind
    execute(ROOT, path, kind=kind)
    rows, summary = read(path)
    report = verify(rows, summary)
    assert not report["outcome"]["completion_qualified"]
    assert report["outcome"]["first_failure_time"] == 0.25
    outcome = next(r for r in rows if r["event"] == "outcome_observation")
    if kind == "collision_completion":
        assert outcome["reward"] == 1000
        assert outcome["source_completion"] and outcome["collision"]
    else:
        assert outcome["off_route"] and outcome["reward"] == -50


@pytest.mark.parametrize("reason", ["deadline", "resource"])
def test_stops_never_become_success_or_zero(tmp_path, reason):
    path = tmp_path.resolve() / reason

    def fail():
        raise ValueError("fixture_resource_limit")

    kwargs = dict(max_seconds=1e-9) if reason == "deadline" else dict(guard=fail)
    result = execute(ROOT, path, **kwargs)
    assert result["outcome"]["collision_observed"] is None
    assert result["outcome"]["censored"] and not result["outcome"]["completion_qualified"]
    if reason == "deadline":
        report = verify(*read(path))
        assert report["max_stationarity"] is None
    else:
        assert result["status"] == "failed" and "resource_limit" in result["stop_reason"]
        with pytest.raises(ValueError):
            verify(*read(path))


MUTATIONS = [
    ("step", "after", [999, 0, 0, 4, 0]),
    ("step", "frame", 2),
    ("outcome_observation", "collision", True),
    ("outcome_observation", "off_route", True),
    ("outcome_observation", "source_completion", True),
    ("outcome_observation", "nearest_index", 999),
    ("outcome_observation", "rc", 1.0),
    ("outcome_observation", "route_distance", 11.0),
    ("outcome_observation", "route_samples", 999),
    ("outcome_observation", "final_sample_observed", True),
    ("outcome_observation", "terminated", True),
    ("outcome_observation", "reward", 1000.0),
    ("delivery", "frame", 9),
    ("monitor", "raw", "{}"),
    ("header", "seed", 136),
    ("header", "max_actions", 402),
    ("header", "route", [[0, 0], [0, 1]]),
    ("runner_stop", "reason", "action_cap"),
]


@pytest.mark.parametrize("event,field,value", MUTATIONS)
def test_corrupt_trace_rejected(completion, event, field, value):
    rows, summary = deepcopy(completion)
    next(r for r in rows if r["event"] == event)[field] = value
    with pytest.raises((ValueError, KeyError)):
        verify(rows, summary)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_collision",
        "background_type",
        "duplicate_reset",
        "false_success",
        "timing",
        "control",
        "drop_frame",
        "unknown",
        "seq_type",
    ],
)
def test_structural_known_bads(completion, mutation):
    rows, summary = deepcopy(completion)
    if mutation == "missing_collision":
        next(r for r in rows if r["event"] == "outcome_observation")["collision_records"].pop()
    elif mutation == "background_type":
        next(r for r in rows if r["event"] == "outcome_observation")["collision_records"][0][
            "result"
        ] = 0
    elif mutation == "duplicate_reset":
        rows.append(deepcopy(next(r for r in rows if r["event"] == "reset")))
    elif mutation == "false_success":
        summary["outcome"]["censored"] = True
    elif mutation == "timing":
        summary["timings"][0]["full_loop_ns"] = 1
    elif mutation == "control":
        next(r for r in rows if r["event"] == "control")["result"]["applied"][0] = -2
    elif mutation == "drop_frame":
        rows.pop(4)
    elif mutation == "unknown":
        rows[2]["event"] = "favorable_substitution"
    else:
        rows[1]["seq"] = True
    with pytest.raises((ValueError, KeyError)):
        verify(rows, summary)


@pytest.mark.parametrize("value", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'])
def test_strict_json(value):
    with pytest.raises(ValueError):
        strict(value)


def test_file_boundary_and_trace_cap(tmp_path):
    output = tmp_path.resolve() / "bounded"
    output.mkdir()
    journal = Journal(output / "small", limit=20)
    with pytest.raises(ValueError, match="trace_resource_limit"):
        journal.write(dict(event="a" * 20))
    journal.stream.close()
    (output / "events.jsonl").symlink_to(output / "small")
    with pytest.raises(OSError):
        read(output)


def test_output_guard_and_storage_budget(tmp_path):
    def plenty(p):
        return SimpleNamespace(free=100 * 1024**3)

    output = tmp_path.resolve()
    assert output_guard(output, usage=plenty) == 0
    with pytest.raises(ValueError, match="storage_limit"):
        output_guard(output, usage=lambda p: SimpleNamespace(free=1))
    f = output / "sparse"
    with f.open("wb") as stream:
        stream.truncate(CASE_STOP)
    with pytest.raises(ValueError, match="storage_limit"):
        output_guard(output, usage=plenty)
    f.unlink()
    (output / "link").symlink_to("/tmp")
    with pytest.raises(ValueError, match="entry_type"):
        output_guard(output, usage=plenty)
    assert proposed_storage(100 * 1024**3, 4 * 1024**3)["fits"]
    assert not proposed_storage(70 * 1024**3, 0)["fits"]
    with pytest.raises(ValueError):
        proposed_storage(True, 0)


def test_client_delta_is_exact_display_process_removal():
    raw = (
        ROOT / "experiments/iter145_constrained_execution/source/released_client.py.txt"
    ).read_bytes()
    value = instrument(raw)
    assert b"process.start()" not in value
    assert b"plan_traj = deliver(" in value
    assert b"results = model(" in value
    with pytest.raises(ValueError):
        instrument(raw + b"\n")


def test_replica_disagreement_is_not_averaged(completion):
    report = verify(*completion)
    assert replicas([report, deepcopy(report)])
    bad = deepcopy(report)
    bad["scientific"][0]["action"][0] += 0.01
    with pytest.raises(ValueError, match="numeric replay"):
        replicas([report, bad])


def test_no_false_recovery_from_all_successes(completion):
    nominal = verify(*completion)
    monitor, intervention = deepcopy(nominal), deepcopy(nominal)
    monitor["arm"], intervention["arm"] = "monitor", "brake_t0"
    report = compare([nominal] * 2, [monitor] * 2, [intervention] * 2)
    assert not report["intersection_witness"] and not report["action_contrast"]
    assert report["harm_vs_successful_nominal"] is False


def test_missing_classification_never_implies_zero():
    row = classify([], "resource_limit", "failed")
    assert row["collision_observed"] is row["simulator_completion"] is None
    assert row["execution_valid"] is False


@pytest.mark.parametrize("phase", ["exchange", "step", "truncate"])
def test_unfinished_execution_is_censored(tmp_path, phase):
    import time
    from types import MethodType
    from unittest.mock import patch
    import torch
    from experiments.iter146_route_outcome_contract.fixtures import environment, Exchange
    from experiments.iter146_route_outcome_contract.runner import run

    env, _ = environment(ROOT, "censor")
    exchange = Exchange(phase, "nominal")
    offset, guards = [0], [0]

    def clock():
        return time.perf_counter_ns() + offset[0]

    def delayed(obs, info):
        value = exchange(obs, info)
        if phase == "exchange":
            offset[0] = 200 * 10**9
        return value

    def guard():
        guards[0] += 1
        if phase == "step" and guards[0] == 3:
            offset[0] = 200 * 10**9

    if phase == "truncate":
        ns = env.step.__func__.__globals__
        ns["_base_step"] = env.step.__func__
        exec(
            "def truncated_step(self, action):\n    obs, reward, term, _, info = _base_step(self, action)\n    return obs, reward, term, True, info\n",
            ns,
        )
        env.step = MethodType(ns["truncated_step"], env)
    path = tmp_path.resolve() / phase
    with patch.object(torch.Tensor, "cuda", lambda self, *a, **k: self):
        summary = run(
            env,
            delayed,
            output=path,
            episode=phase,
            arm="nominal",
            monitor_reader=exchange.monitor,
            device="cpu",
            clock=clock,
            guard=guard,
        )
    assert summary["status"] == "completed", summary
    if phase == "step":
        assert summary["timings"][0]["full_loop_ns"] >= 200 * 10**9
    report = verify(*read(path))
    assert report["outcome"]["censored"] and not report["outcome"]["completion_qualified"]
    assert (
        summary["stop_reason"]
        == {
            "exchange": "wall_deadline_after_exchange",
            "step": "wall_deadline_after_step",
            "truncate": "source_truncated",
        }[phase]
    )


@pytest.mark.parametrize(
    "mutation", [None, "device", "seed", "cleanup", "camera", "collision", "monitor"]
)
def test_gpu_receipt_gates_with_explicitly_synthetic_records(tmp_path, mutation):
    from experiments.iter146_route_outcome_contract.gpu_check import verify_case

    directory = tmp_path.resolve() / "synthetic_gpu_receipt"
    directory.mkdir()
    execute(ROOT, directory / "trace", max_actions=2)
    rows, summary = read(directory / "trace")
    deliveries = [r["value"] for r in rows if r["event"] == "delivery"]
    monitors = [r["raw"] for r in rows if r["event"] == "monitor"]
    outcomes = [r for r in rows if r["event"] == "outcome_observation"]
    worker = dict(
        status="completed",
        gpu_observed=True,
        summary=summary,
        episode=summary["episode"],
        seed=144,
        geos="synthetic",
        torch="synthetic",
        cuda_device="synthetic",
        cleanup=dict(status="removed"),
        render_events=[
            dict(time=t / 4, device="cuda:0", shape=[3, 3, 3], elapsed_ns=1, transforms={})
            for t in range(3)
            for _ in range(6)
        ],
        collision_events=[
            dict(**r, **(dict(device="cuda:0", points=1) if r["kind"] == "background" else {}))
            for o in outcomes
            for r in o["collision_records"]
        ],
    )
    if mutation == "device":
        worker["gpu_observed"] = False
    elif mutation == "seed":
        worker["seed"] = 136
    elif mutation == "cleanup":
        worker["cleanup"]["status"] = "failed"
    elif mutation == "camera":
        worker["render_events"][0]["device"] = "cpu"
    elif mutation == "collision":
        worker["collision_events"].pop()
    elif mutation == "monitor":
        monitors[0] = "{}"
    (directory / "worker.json").write_text(json.dumps(worker))
    (directory / "delivery145.jsonl").write_text("".join(json.dumps(d) + "\n" for d in deliveries))
    (directory / "sentinel_iter48_decisions.jsonl").write_text("\n".join(monitors) + "\n")
    if mutation:
        with pytest.raises(ValueError):
            verify_case(directory)
    else:
        assert verify_case(directory)["status"] == "supported"


@pytest.mark.parametrize(
    "change",
    [None, "prior_arm", "raw_commit", "replay_sha256", "status", "arm", "manifest_sha256", "bytes"],
)
def test_later_arm_requires_prior_raw_and_replay(change):
    import hashlib
    from experiments.iter146_route_outcome_contract.gpu_pair import validate_clearance

    raw = b"{}"
    digest = hashlib.sha256(raw).hexdigest()
    permit = dict(
        arm="monitor",
        manifest_sha256=digest,
        status="supported",
        prior_arm="nominal",
        raw_commit="a" * 40,
        replay_sha256="b" * 64,
    )
    if change and change != "bytes":
        permit[change] = "wrong"
    encoded = json.dumps(permit).encode()
    args = (
        raw,
        encoded,
        "monitor",
        digest,
        "0" * 64 if change == "bytes" else hashlib.sha256(encoded).hexdigest(),
    )
    if change:
        with pytest.raises(ValueError):
            validate_clearance(*args)
    else:
        assert validate_clearance(*args) == permit


def comparator_report(arm, kind, *, steps=None, contrast=True, lag=0.0):
    """Constructed comparator unit inputs, not execution or driving evidence."""
    steps = steps if steps is not None else (8 if kind == "collision" else 12)
    collision = kind in ("collision", "censored_collision")
    complete = kind == "complete"
    censored = kind.startswith("censored")
    onset = 2.5 if arm == "brake_t2_5" else 0
    science = []
    for i in range(1, steps + 1):
        pulse = arm.startswith("brake_") and onset <= (i - 1) / 4 < onset + 1
        science.append(
            dict(
                time=i / 4,
                state=[i / 4, 0, 0, 1, 0],
                action=[-2 if pulse and contrast else 1, 0],
                nominal_action=[1, 0],
                actors={},
                rc=(1.1 if complete and i == steps else i / 20 - lag),
                nominal={"fixture": "plan"},
                delivered={"fixture": "plan"},
                rgb={"fixture": "images"},
                collision=collision and i == steps,
                off_route=False,
            )
        )
    return dict(
        status="supported",
        arm=arm,
        route=[[0, 0], [10, 0]],
        reset_state=[0, 0, 0, 1, 0],
        scientific=science,
        outcome=dict(
            collision_observed=collision,
            off_route_observed=False,
            completion_qualified=complete,
            censored=censored,
            first_failure_time=steps / 4 if collision else None,
        ),
    )


def comparison_fixture(nominal="collision", monitor="collision", intervention="complete", **kw):
    reports = [
        comparator_report("nominal", nominal),
        comparator_report("monitor", monitor),
        comparator_report("brake_t0", intervention, **kw),
    ]
    return compare(*[[r, deepcopy(r)] for r in reports])


def test_unknown_intersection_is_not_false():
    result = comparison_fixture(nominal="censored", monitor="censored")
    assert result["nominal"]["witness"] is None
    assert result["monitor"]["witness"] is None
    assert result["intersection_witness"] is None


def test_unknown_nominal_is_not_no_harm():
    result = comparison_fixture(nominal="censored", intervention="collision")
    assert result["harm_vs_successful_nominal"] is None


def test_censored_intervention_is_not_failed_recovery():
    result = comparison_fixture(intervention="censored")
    assert result["nominal"]["witness"] is None
    assert result["monitor"]["witness"] is None
    assert result["intersection_witness"] is None


@pytest.mark.parametrize(
    "nominal,monitor,intervention,wn,wm,intersection,harm",
    [
        ("collision", "collision", "complete", True, True, True, False),
        ("collision", "complete", "complete", True, False, False, False),
        ("complete", "collision", "complete", False, True, False, False),
        ("complete", "complete", "collision", False, False, False, True),
        ("complete", "complete", "censored", False, False, False, None),
        ("complete", "complete", "censored_collision", False, False, False, True),
        ("censored", "collision", "collision", False, False, False, None),
        ("collision", "censored", "complete", True, None, None, False),
    ],
)
def test_comparator_truth_table(nominal, monitor, intervention, wn, wm, intersection, harm):
    result = comparison_fixture(nominal, monitor, intervention)
    assert result["nominal"]["witness"] is wn
    assert result["monitor"]["witness"] is wm
    assert result["intersection_witness"] is intersection
    assert result["harm_vs_successful_nominal"] is harm


@pytest.mark.parametrize("kwargs", [{"contrast": False}, {"lag": 0.051}])
def test_no_witness_without_action_or_hazard_progress(kwargs):
    result = comparison_fixture(**kwargs)
    assert result["intersection_witness"] is False


def test_earlier_qualified_completion_meets_progress_rule():
    result = comparison_fixture(steps=4)
    assert result["intersection_witness"] is True
    assert result["nominal"]["progress_at_hazard_satisfied"] is True


def test_missing_hazard_observation_remains_unknown():
    result = comparison_fixture(intervention="censored", steps=6)
    assert result["nominal"]["progress_at_hazard_satisfied"] is None
    assert result["intersection_witness"] is None


def test_unobserved_pulse_contrast_remains_unknown():
    n = comparator_report("nominal", "collision")
    m = comparator_report("monitor", "collision")
    p = comparator_report("brake_t2_5", "censored", steps=6)
    result = compare([n] * 2, [m] * 2, [p] * 2)
    assert result["action_contrast"] is None
    assert result["intersection_witness"] is None


@pytest.mark.parametrize(
    "left,right,expected",
    [
        (False, False, False),
        (False, True, False),
        (False, None, False),
        (True, False, False),
        (True, True, True),
        (True, None, None),
        (None, False, False),
        (None, True, None),
        (None, None, None),
    ],
)
def test_three_valued_conjunction(left, right, expected):
    from experiments.iter146_route_outcome_contract.compare import conjunction

    assert conjunction(left, right) is expected


@pytest.mark.parametrize(
    "mutation", ["boolean", "start", "end", "elapsed", "full", "work", "overlap"]
)
def test_v2_timing_known_bads(completion, mutation):
    rows, summary = deepcopy(completion)
    assert summary["schema"] == "sentinel.iter146.summary.v2"
    first = summary["timings"][0]
    if mutation == "boolean":
        first["loop_start_ns"] = True
    elif mutation == "start":
        first["loop_start_ns"] = first["loop_work_end_ns"]
    elif mutation == "end":
        first["loop_end_ns"] = first["loop_work_end_ns"] - 1
    elif mutation == "elapsed":
        summary["elapsed_ns"] = first["loop_end_ns"] - 1
    elif mutation == "full":
        first["full_loop_ns"] += 1
    elif mutation == "work":
        first["loop_work_ns"] += 1
    elif mutation == "overlap":
        second = summary["timings"][1]
        second["loop_start_ns"] = first["loop_start_ns"]
        second["loop_work_ns"] = second["loop_work_end_ns"] - second["loop_start_ns"]
        second["full_loop_ns"] = second["loop_end_ns"] - second["loop_start_ns"]
    with pytest.raises(ValueError, match="timing|loops"):
        verify(rows, summary)
