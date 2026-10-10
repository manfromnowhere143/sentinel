from pathlib import Path
import math
import numpy as np
import pytest

from experiments.iter145_constrained_execution.optimizer import (
    ConstrainedController,
    certificate,
    controls_constraints,
    objective,
    require_action,
    rollout,
)
from experiments.iter144_timed_trajectory.control import transition
from experiments.iter144_timed_trajectory.trajectory import ContractError

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("v", [0.0, 4.0, -1.0])
@pytest.mark.parametrize("u", [(1.0, 0.1), (-1.0, -0.1), (0.0, 0.0)])
def test_smooth_feasible_motion_matches_execution(v, u):
    state = np.array([0.0, 0.0, 0.3, v, 0.2])
    seq = np.tile(u, (8, 1))
    states, sens = rollout(state, seq)
    actual = state
    for i in range(8):
        actual = transition(actual, seq[i])[0]
        np.testing.assert_allclose(actual, states[i + 1], atol=1e-10, rtol=0)
    eps = 1e-6
    for j in [0, 1, 14, 15]:
        p = seq.ravel().copy()
        m = p.copy()
        p[j] += eps
        m[j] -= eps
        numerical = (rollout(state, p.reshape(-1, 2))[0] - rollout(state, m.reshape(-1, 2))[0]) / (
            2 * eps
        )
        np.testing.assert_allclose(numerical, sens[:, :, j], atol=1e-6, rtol=0)


def test_objective_gradient_including_actuator_boundary():
    s = np.array([0.0, 0.0, 0.2, 0.0, 0.1])
    u = np.tile([0.4, 0.03], (6, 1))
    u[0, 0] = 2.0
    ref = np.zeros((7, 5))
    ref[:, 0] = np.arange(7) * 0.3
    value, g = objective(u.ravel(), s, ref)
    eps = 1e-6
    numerical = []
    for j in range(u.size):
        p = u.ravel().copy()
        m = p.copy()
        p[j] += eps
        m[j] -= eps
        numerical.append((objective(p, s, ref)[0] - objective(m, s, ref)[0]) / (2 * eps))
    np.testing.assert_allclose(g, numerical, atol=1e-6, rtol=0)
    assert value >= 0


def test_constraints_include_accumulated_steering():
    C, b = controls_constraints(19, 0.9)
    u = np.tile([0.0, math.pi / 12], 19)
    assert max(C @ u - b) > 0
    C, b = controls_constraints(19, 0.0)
    assert max(C @ np.zeros(38) - b) < 0


@pytest.mark.parametrize("n,d", [(0, 0), (20, 0), (3, 2), (3, float("nan"))])
def test_bad_constraint_domain(n, d):
    with pytest.raises(ContractError):
        controls_constraints(n, d)


def test_kkt_requires_feasibility_and_stationarity():
    C, b = controls_constraints(1, 0.0)
    assert certificate(np.zeros(2), np.zeros(2), C, b)["admitted"]
    assert not certificate(np.array([3.0, 0.0]), np.zeros(2), C, b)["admitted"]
    assert not certificate(np.zeros(2), np.ones(2), C, b)["admitted"]
    assert certificate(np.array([2.0, 0.0]), np.array([-1.0, 0.0]), C, b)["admitted"]
    assert not certificate(np.array([2.0, 0.0]), np.array([1.0, 0.0]), C, b)["admitted"]


def test_certificate_does_not_mistake_clipped_derivative_for_feasible_derivative():
    s = [0.0, 0.0, 0.0, 0.0, 0.0]
    u = np.array([[2.0, 0.0]])
    projected_B = transition(s, u[0])[3]
    smooth_B = rollout(s, u)[1][1, :, :2]
    assert projected_B[3, 0] == 0 and smooth_B[3, 0] == 0.25


def test_iteration_limit_cannot_actuate():
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13) * 0.5
    r = ConstrainedController().solve(np.zeros(5), ref, max_iterations=1)
    assert not r["admitted"] and r["applied"] is None
    with pytest.raises(ContractError):
        require_action(r)


def test_exact_straight_motion_is_certified():
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    assert r["admitted"] and r["certificate"]["stationarity_inf"] <= 1e-6
    assert abs(require_action(r)["acc"]) < 1e-8


def test_independent_reverse_gradient_and_certificate():
    from copy import deepcopy
    from experiments.iter145_constrained_execution.independent import (
        certificate as second_cert,
        cost_gradient,
    )

    s = [0.0, 0.0, 0.2, 4.0, 0.1]
    u = np.tile([0.5, 0.01], (6, 1))
    ref = np.zeros((7, 5))
    value, g, _ = cost_gradient(s, u.tolist(), ref.tolist())
    value2, g2 = objective(u.ravel(), np.asarray(s), ref)
    assert value == pytest.approx(value2, abs=1e-9)
    np.testing.assert_allclose(g, g2, atol=1e-9, rtol=0)
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    second_cert(r)
    for field, value in [("stationarity_inf", 1.0), ("max_violation", 1.0)]:
        bad = deepcopy(r)
        bad["certificate"][field] = value
        with pytest.raises(ValueError):
            second_cert(bad)
    bad = deepcopy(r)
    bad["certificate"]["multipliers"][0] = -1.0
    with pytest.raises(ValueError):
        second_cert(bad)


def test_callback_is_not_final_solution_when_no_refinement():
    from copy import deepcopy
    from experiments.iter145_constrained_execution.independent import (
        certificate as second_cert,
        cost_gradient,
    )

    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    assert r["refinement"] == []
    progress = np.asarray(r["inputs"])
    progress[0, 0] += 1e-5
    r["history"][-1]["inputs"] = progress.tolist()
    r["history"][-1]["objective"] = cost_gradient(
        r["initial_state"], progress.tolist(), r["reference"]
    )[0]
    second_cert(r)
    bad = deepcopy(r)
    bad["inputs"][0][0] += 0.01
    with pytest.raises(ValueError):
        second_cert(bad)


def make_delivery(frame=0, mode="nominal", episode="fixture", curved=False):
    from experiments.iter145_constrained_execution.nominal import packet

    positions = np.array(
        [[0.03 * i * i if curved else 0.0, 2.0 * i] for i in range(1, 7)], dtype=np.float64
    )
    return packet(
        positions,
        positions.copy(),
        positions.copy(),
        episode=episode,
        frame=frame,
        time=frame * 0.25,
        mode=mode,
        monitor_sha256="a" * 64,
    )


@pytest.mark.parametrize("speed", [-4.0, -0.1, 0.0, 0.1, 4.0])
def test_brake_pulse_matches_registered_signed_law(speed):
    from experiments.iter145_constrained_execution.simulator import arm_action

    nominal = dict(acc=0.5, steer_rate=0.07)
    for mode, start in [("brake_t0", 0.0), ("brake_t2_5", 2.5)]:
        for now in [start, start + 0.25, start + 0.5, start + 0.75]:
            action = arm_action(mode, now, speed, nominal)
            after = speed + action["acc"] * 0.25
            assert abs(after) <= abs(speed) and after * speed >= 0
            assert action["steer_rate"] == nominal["steer_rate"]
        assert arm_action(mode, start + 1.0, speed, nominal) == nominal
        if start > 0:
            assert arm_action(mode, start - 0.25, speed, nominal) == nominal


def test_nominal_supported_clock_and_world_heading():
    from experiments.iter145_constrained_execution.nominal import reference

    r = reference(make_delivery(), [10.0, 20.0, 0.3, -1.0], episode="fixture", frame=0, time=0.0)
    assert r.times == tuple(i * 0.25 for i in range(13)) and r.states[0][3] == -1
    assert r.states[-1][0] == pytest.approx(10 + 12 * math.sin(0.3))
    assert r.states[-1][1] == pytest.approx(20 + 12 * math.cos(0.3))
    assert r.states[-1][2] == pytest.approx(math.pi / 2 - 0.3)
    with pytest.raises(ContractError, match="extrapolation"):
        r.at(3.25)


@pytest.mark.parametrize(
    "field,value",
    [
        ("frame", True),
        ("frame", 1),
        ("episode", "wrong"),
        ("observation_time", 0.25),
        ("knot_times", [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]),
        ("coordinate_frame", "world"),
        ("mode", "unknown"),
        ("monitor_sha256", "z" * 64),
    ],
)
def test_delivery_known_bads(field, value):
    from experiments.iter145_constrained_execution.nominal import validate

    bad = make_delivery()
    bad[field] = value
    with pytest.raises((ContractError, ValueError)):
        validate(bad, episode="fixture", frame=0, time=0.0)


def test_delivery_bytes_and_policy_known_bads():
    from experiments.iter145_constrained_execution.nominal import validate

    bad = make_delivery()
    bad["delivered"]["values"][0][0] = 1
    with pytest.raises(ContractError):
        validate(bad, episode="fixture", frame=0, time=0.0)
    bad = make_delivery()
    bad["delivered"]["sha256"] = "b" * 64
    with pytest.raises(ContractError):
        validate(bad, episode="fixture", frame=0, time=0.0)


@pytest.mark.parametrize("speed,curved", [(0.0, False), (4.0, False), (0.0, True), (4.0, True)])
def test_full_source_step_render_collision_and_short_control(speed, curved, monkeypatch):
    import torch
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session

    monkeypatch.setattr(torch.Tensor, "cuda", lambda self, *a, **k: self)
    env, calls = fixture(ROOT, speed=speed)
    session = Session(env, "fixture", device="cpu")
    obs, info = session.reset()
    assert info["timestamp"] == 0 and env.planner.tick == 0
    for frame in range(12):
        output = session.step(make_delivery(frame=frame, curved=curved))
        assert output[-1]["timestamp"] == (frame + 1) * 0.25
        assert not session.stopped
        group = [c for c in calls if c["time"] == (frame + 1) * 0.25]
        assert [c["kind"] for c in group] == ["collision"] + ["render"] * 6
        assert len({c["planning_id"] for c in group}) == 1
        assert group[0]["boxes"] == env.objs_list
        for name, matrix in env.render_kwargs["planning"][0].items():
            state = env.planner.native(name)
            assert matrix[0, 3].item() == pytest.approx(state[0], abs=5e-6)
            assert matrix[2, 3].item() == pytest.approx(state[1], abs=5e-6)
            rotation = (
                -state[2]
                if type(env.planner.controller[name]).__name__ == "UnicyclePlanner"
                else -state[2] - math.pi / 2
            )
            assert matrix[0, 0].item() == pytest.approx(math.cos(rotation), abs=1e-6)
    assert sum(e["event"] == "select" for e in env.planner.events) == 2
    with pytest.raises(ContractError, match="duplicate_reset"):
        session.reset()


def test_reset_clock_and_runtime_known_bads(monkeypatch):
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session, check_runtime

    env, _ = fixture(ROOT, actors=("ConstantPlanner",))
    env.kinematic["Lr"] = 1.4
    with pytest.raises(ContractError, match="kinematics"):
        check_runtime(env)
    env.kinematic["Lr"] = 1.35
    session = Session(env, "fixture", device="cpu")
    session.reset()
    with pytest.raises(ContractError, match="tick"):
        env.planner.plan_traj(0.5, env.ego_state)
    with pytest.raises(ContractError, match="stopped"):
        env.planner.plan_traj(0.25, env.ego_state)


def test_unicycle_unsupported_time_and_unknown_actor():
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session, TimedPlanner

    env, _ = fixture(ROOT, actors=("UnicyclePlanner",))
    with pytest.raises(ContractError, match="unsupported_time"):
        TimedPlanner.unicycle_support(env.planner.controller["agent_0"], 21.0)
    env.planner.controller["agent_0"] = object()
    with pytest.raises(ContractError, match="unknown_actor_type"):
        Session(env, "fixture", device="cpu")


def resource_fixture():
    from experiments.iter145_constrained_execution.resources import HOST

    observation = dict(
        HOST,
        observation_kind="host_readback",
        state="RUNNING",
        containers=[],
        gpu_processes=[],
        observed_epoch=1000.0,
        local_free_gib=20.0,
        remote_free_gib=110.0,
        shutdown_owner="sentinel.iter145",
        owned_shutdown_epoch=1800.0,
    )
    envelope = dict(
        max_output_gib=8.0,
        max_seconds=600.0,
        hourly_upper_usd=2.0,
        max_cost_usd=1.0,
        capacity_attempts=1,
        smoke_attempts=1,
        source_commit="a" * 40,
        cleanup_owner="sentinel.iter145",
        price_source_sha256="b" * 64,
    )
    return observation, envelope


@pytest.mark.parametrize(
    "key,value",
    [
        ("local_free_gib", 14.99),
        ("remote_free_gib", 99.99),
        ("remote_free_gib", None),
        ("remote_free_gib", float("nan")),
        ("id", "wrong"),
        ("containers", ["foreign"]),
        ("gpu_processes", [1]),
        ("state", "TERMINATED"),
        ("observed_epoch", 0.0),
        ("owned_shutdown_epoch", 1600.0),
        ("shutdown_owner", "foreign"),
        ("observation_kind", "unobserved"),
    ],
)
def test_resource_gate_known_bads(key, value):
    from experiments.iter145_constrained_execution.resources import resource_gate

    obs, env = resource_fixture()
    assert resource_gate(obs, env, now=1000.0)
    obs[key] = value
    with pytest.raises(ContractError):
        resource_gate(obs, env, now=1000.0)


@pytest.mark.parametrize(
    "key,value",
    [
        ("max_output_gib", 90.0),
        ("max_cost_usd", 0.01),
        ("hourly_upper_usd", 0.0),
        ("capacity_attempts", 2),
        ("smoke_attempts", 2),
        ("source_commit", ""),
        ("price_source_sha256", ""),
        ("max_seconds", None),
    ],
)
def test_resource_envelope_known_bads(key, value):
    from experiments.iter145_constrained_execution.resources import resource_gate

    obs, env = resource_fixture()
    env[key] = value
    with pytest.raises(ContractError):
        resource_gate(obs, env, now=1000.0)


def test_asset_reader_rejects_symlink_truncation_and_empty(tmp_path):
    from experiments.iter145_constrained_execution.resources import file_identity

    directory = tmp_path.resolve()
    source = directory / "source"
    source.write_bytes(b"abc")
    assert file_identity(source)["bytes"] == 3
    link = directory / "link"
    link.symlink_to(source)
    with pytest.raises(OSError):
        file_identity(link)
    sublink = directory / "sub"
    sublink.symlink_to(directory, target_is_directory=True)
    with pytest.raises(OSError):
        file_identity(sublink / "source")
    with pytest.raises(ContractError):
        file_identity(source, max_bytes=2)
    source.write_bytes(b"")
    with pytest.raises(ContractError):
        file_identity(source)


def test_missing_gpu_cannot_become_resource_projection():
    from experiments.iter145_constrained_execution.resources import study_projection

    with pytest.raises(ContractError):
        study_projection(dict(status="supported", gpu_observed=False))


def test_driver_retains_stop_and_rejects_reuse(tmp_path, monkeypatch):
    import json
    import torch
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.driver import run

    monkeypatch.setattr(torch.Tensor, "cuda", lambda self, *a, **k: self)
    env, _ = fixture(ROOT, actors=("ConstantPlanner",))
    result = run(
        env,
        lambda obs, info: make_delivery(frame=info["sentinel_frame"]),
        output=tmp_path / "run",
        episode="fixture",
        max_steps=2,
        max_seconds=30,
        device="cpu",
    )
    assert (
        result["status"] == "completed"
        and result["stop_reason"] == "smoke_step_cap"
        and result["steps"] == 2
    )
    with pytest.raises(FileExistsError):
        run(
            env,
            None,
            output=tmp_path / "run",
            episode="fixture",
            max_steps=2,
            max_seconds=30,
            device="cpu",
        )
    env, _ = fixture(ROOT, actors=("ConstantPlanner",))
    result = run(
        env,
        lambda obs, info: make_delivery(frame=1),
        output=tmp_path / "bad",
        episode="fixture",
        max_steps=2,
        max_seconds=30,
        device="cpu",
    )
    assert result["status"] == "failed" and result["steps"] == 0
    assert (
        json.loads((tmp_path / "bad/summary.json").read_text())["stop_reason"]
        == result["stop_reason"]
    )


def test_source_foreground_overlap_and_separation():
    from experiments.iter145_constrained_execution.source_fixture import source_namespace

    source = source_namespace(ROOT)["fg_collision_det"]
    ego = [0.0, 0.0, 0.0, 2.0, 4.0, 1.0, 0.0]
    assert source(ego, [ego])
    assert not source(ego, [[10.0, 0.0, 0.0, 2.0, 4.0, 1.0, 0.0]])


def test_client_full_monitor_packet_and_instrumentation(tmp_path, monkeypatch):
    import json
    from experiments.iter145_constrained_execution.client import deliver, instrument

    monkeypatch.setenv("SENTINEL_I145_EPISODE", "fixture")
    monkeypatch.setenv("SENTINEL_I145_MODE", "monitor")
    p = np.array([[0.0, 2.0 * i] for i in range(1, 7)])

    def monitor(plan, result, data, output):
        row = dict(frame_index=0, ts=0.0, brake=True, traj=plan.tolist())
        (tmp_path / "sentinel_iter48_decisions.jsonl").write_text(json.dumps(row) + "\n")
        return np.zeros_like(plan)

    info = dict(sentinel_episode="fixture", sentinel_frame=0, timestamp=0.0)
    value = deliver(p, {}, dict(timestamp=0.0), str(tmp_path), monitor, True, info)
    assert (
        value["nominal"]["values"] == p.tolist()
        and value["delivered"]["values"] == np.zeros_like(p).tolist()
    )
    source = (
        ROOT / "experiments/iter145_constrained_execution/source/released_client.py.txt"
    ).read_bytes()
    assert b"raw_data[1]" in instrument(source)
    with pytest.raises(ValueError):
        instrument(source + b"\n")


@pytest.mark.parametrize(
    "mutation",
    [
        "population",
        "scenario_hash",
        "missing",
        "null_size",
        "image",
        "actor",
        "unresolved",
        "runtime",
        "roles",
        "empty_then_missing_count",
        "missing_types",
        "malformed_types",
        "negative_count",
    ],
)
def test_asset_gate_known_bads(mutation):
    import json
    from experiments.iter145_constrained_execution.resources import asset_gate, IMAGE

    inventory = json.loads(
        (ROOT / "experiments/iter143_model_contract/proof/case_inventory.json").read_text()
    )
    roles = [
        "scene",
        "ground",
        "scene_config",
        "actor_model",
        "actor_dimensions",
        "planner_checkpoint",
        "runtime_source",
        "camera_config",
        "kinematic_config",
    ]
    files = {
        "/fixture/" + role: dict(status="observed", sha256="a" * 64, bytes=1, role=role)
        for role in roles
    }
    scenarios = {
        r["name"]: dict(
            sha256=r["sha256"],
            dependencies=list(files),
            controller_types=["AttackPlanner"],
            actor_count=1,
            unresolved_dependencies=[],
        )
        for r in inventory["rows"]
        if r["role"] == "proposed_pilot"
    }
    value = dict(
        observation_kind="host_readback",
        files=files,
        scenarios=scenarios,
        roles=roles,
        image_id=IMAGE,
    )
    assert asset_gate(inventory, value)
    name = next(iter(scenarios))
    if mutation == "population":
        del scenarios[name]
    elif mutation == "scenario_hash":
        scenarios[name]["sha256"] = "b" * 64
    elif mutation == "missing":
        del files["/fixture/scene"]
    elif mutation == "null_size":
        files["/fixture/scene"]["bytes"] = None
    elif mutation == "image":
        value["image_id"] = "unknown"
    elif mutation == "actor":
        scenarios[name]["controller_types"] = ["unknown"]
    elif mutation == "unresolved":
        scenarios[name]["unresolved_dependencies"] = ["map"]
    elif mutation == "runtime":
        files["/fixture/runtime_source"]["status"] = "unavailable"
    elif mutation == "roles":
        value["roles"] = ["scene"]
    elif mutation == "empty_then_missing_count":
        scenarios[name].update(controller_types=[], actor_count=0)
        assert asset_gate(inventory, value)
        del scenarios[name]["actor_count"]
    elif mutation == "missing_types":
        del scenarios[name]["controller_types"]
    elif mutation == "malformed_types":
        scenarios[name]["controller_types"] = "AttackPlanner"
    elif mutation == "negative_count":
        scenarios[name]["actor_count"] = -1
    with pytest.raises(ContractError):
        asset_gate(inventory, value)


@pytest.mark.parametrize(
    "mutation",
    ["none", "escape", "wrong_link", "directory", "file_link", "unknown", "hash", "size"],
)
def test_historical_actor_alias_is_bounded(tmp_path, mutation):
    from experiments.iter145_constrained_execution.resources import actor_identity, file_identity

    root = tmp_path.resolve() / "cars"
    car = root / "2024_07_05_16_16_38"
    (car / "postprocess").mkdir(parents=True)
    model = car / "gs.pth"
    model.write_bytes(b"frozen model fixture")
    link = car / "postprocess/shadow.pth"
    link.symlink_to("..")
    relative = Path("2024_07_05_16_16_38/postprocess/shadow.pth")
    expected = {str(model): file_identity(model)}
    if mutation == "escape":
        relative = Path("../2024_07_05_16_16_38/postprocess/shadow.pth")
    elif mutation in ("wrong_link", "directory"):
        link.unlink()
        if mutation == "directory":
            link.mkdir()
        else:
            link.symlink_to("../..")
    elif mutation == "file_link":
        target = car / "other"
        model.rename(target)
        model.symlink_to(target)
    elif mutation == "unknown":
        expected = {}
    elif mutation == "hash":
        expected[str(model)]["sha256"] = "0" * 64
    elif mutation == "size":
        expected[str(model)]["bytes"] += 1
    if mutation == "none":
        result = actor_identity(root, relative, "gs.pth", expected)
        assert result["physical_path"] == str(model)
        assert result["alias_target"] == ".."
        assert result["sha256"] == expected[str(model)]["sha256"]
    else:
        with pytest.raises((ContractError, OSError)):
            actor_identity(root, relative, "gs.pth", expected)


@pytest.mark.parametrize("plan", [None, {}, "missing", []])
def test_asset_collect_preserves_empty_vs_missing_plan(monkeypatch, plan):
    import hashlib
    import json
    from types import SimpleNamespace
    from experiments.iter145_constrained_execution import assets

    cfg = dict(scene_name="scene-0013", load_HD_map=False)
    if plan != "missing":
        cfg["plan_list"] = plan
    raw = json.dumps(cfg).encode()
    monkeypatch.setattr(assets.socket, "gethostname", lambda: "sentinel-gpu")
    monkeypatch.setattr(
        assets.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=assets.IMAGE)
    )
    monkeypatch.setattr(
        assets,
        "file_identity",
        lambda *a, **k: dict(
            sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),
            **({"data": raw} if k.get("include_bytes") else {}),
        ),
    )
    inv = dict(
        rows=[
            dict(
                name="scene-0013-easy-00.yaml",
                scene="0013",
                role="proposed_pilot",
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        ]
    )
    result = assets.collect(inv, {}, assets.IMAGE, {})
    row = result["scenarios"]["scene-0013-easy-00.yaml"]
    if plan == []:
        assert row["actor_count"] == 0
        assert row["controller_types"] == []
        assert row["unresolved_dependencies"] == []
    else:
        assert row["actor_count"] is None
        assert "scenario_plan_list" in row["unresolved_dependencies"]


@pytest.mark.parametrize(
    "mutation", ["none", "missing", "scope", "path", "size", "digest", "totals"]
)
def test_map_dependency_binding_known_bads(mutation):
    from experiments.iter145_constrained_execution.maps import ROOTS, required_paths, validate

    files = {p: dict(bytes=1, sha256="a" * 64) for p in required_paths()}
    binding = dict(
        schema="sentinel.iter145.map_inventory.v1",
        observation_kind="host_readback",
        roots=list(ROOTS),
        scope="complete_regular_file_trees",
        status="supported",
        files=files,
        file_count=len(files),
        total_bytes=len(files),
    )
    assert validate(binding)
    name = next(iter(files))
    if mutation == "none":
        return
    if mutation == "missing":
        del files[name]
    elif mutation == "scope":
        binding["scope"] = "selected_only"
    elif mutation == "path":
        files["/root/elsewhere"] = files[name]
    elif mutation == "size":
        files[name]["bytes"] = 0
    elif mutation == "digest":
        files[name]["sha256"] = "g" * 64
    elif mutation == "totals":
        binding["file_count"] += 1
    with pytest.raises(ContractError):
        validate(binding)


def test_explicit_empty_regular_source_identity(tmp_path):
    import hashlib
    from experiments.iter145_constrained_execution.resources import file_identity

    p = tmp_path.resolve() / "__init__.py"
    p.write_bytes(b"")
    with pytest.raises(ContractError):
        file_identity(p)
    assert file_identity(p, allow_empty=True) == dict(
        bytes=0, sha256=hashlib.sha256(b"").hexdigest()
    )
    p.unlink()
    with pytest.raises(FileNotFoundError):
        file_identity(p, allow_empty=True)


def test_map_inventory_rejects_symlink(tmp_path):
    from experiments.iter145_constrained_execution.maps import inventory_tree

    root = tmp_path.resolve()
    (root / "data").write_bytes(b"data")
    (root / "alias").symlink_to("data")
    with pytest.raises(ContractError):
        inventory_tree(root)


def test_gpu_client_mounts_and_cache_boundary(tmp_path):
    from experiments.iter145_constrained_execution.gpu import client_command, cache_adapter

    argv = client_command(tmp_path / "control", tmp_path / "run", "fixture")
    assert "SENTINEL_I145_EPISODE=fixture" in argv
    assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
    assert "/opt/sentinel-stack/UniAD_SIM:/model:ro" in argv
    captured = {}

    def factory(**kwargs):
        captured.update(kwargs)
        return "constructed"

    wrapped = cache_adapter(factory, tmp_path / "cache")
    assert (
        wrapped(cache_location="~/.unified_data_cache", desired_data=["nusc_trainval"])
        == "constructed"
    )
    assert captured["cache_location"] == str(tmp_path / "cache")
    with pytest.raises(ValueError):
        wrapped(cache_location="/unexpected")


@pytest.mark.parametrize(
    "mutation",
    ["none", "cuda", "camera", "geometry", "transport", "reset", "control", "clock", "cleanup"],
)
def test_gpu_checker_synthetic_evidence_known_bads(tmp_path, mutation):
    """Synthetic GPU-shaped fixture, explicitly not evidence that GPU execution happened."""
    import hashlib
    import json
    from experiments.iter145_constrained_execution.gpu_check import verify

    case = json.loads(
        (ROOT / "experiments/iter145_constrained_execution/proof/integration_raw.json").read_text()
    )["cases"][0]
    events = case["events"]
    controls = [e for e in events if e["event"] == "control"]
    deliveries = [e for e in events if e["event"] == "delivery"]
    steps = [e for e in events if e["event"] == "step"]
    decisions = []
    client = []
    for i, (control, delivery) in enumerate(zip(controls, deliveries)):
        value = control["delivery"]
        line = json.dumps(
            dict(frame_index=i, ts=i * 0.25, brake=False, traj=value["nominal"]["values"])
        )
        decisions.append(line)
        value["monitor_sha256"] = hashlib.sha256(line.encode()).hexdigest()
        delivery["value"] = value
        client.append(value)
    render = [
        dict(time=0.0, device="cuda:0", shape=[3, 8, 8], elapsed_ns=1, transforms={})
        for _ in range(6)
    ]
    collisions = []
    for step, boundary in zip(steps, case["boundary"]):
        for record in boundary["observations"][1:]:
            render.append(
                dict(
                    time=step["time"],
                    device="cuda:0",
                    shape=[3, 8, 8],
                    elapsed_ns=1,
                    transforms=record["matrices"],
                )
            )
        collisions.append(
            dict(
                kind="foreground",
                time=step["time"],
                objects=step["info"]["obj_boxes"],
                ego_box=step["info"]["ego_box"],
                result=False,
            )
        )
    worker = dict(
        status="completed",
        episode=case["episode"],
        gpu_observed=True,
        cleanup=dict(status="removed"),
        geos="synthetic",
        render_events=render,
        collision_events=collisions,
    )
    if mutation == "cuda":
        render[6]["device"] = "cpu"
    elif mutation == "camera":
        render.pop()
    elif mutation == "geometry":
        collisions[0]["result"] = True
    elif mutation == "transport":
        client = client[:-1]
    elif mutation == "reset":
        events.append(events[0])
    elif mutation == "control":
        steps[0]["applied"]["acc"] += 0.2
    elif mutation == "clock":
        steps[0]["time"] += 0.25
    elif mutation == "cleanup":
        worker["cleanup"]["status"] = "unobserved"
    raw = "".join(json.dumps(e) + "\n" for e in events).encode()
    summary = case["summary"]
    summary["events_sha256"] = hashlib.sha256(raw).hexdigest()
    (tmp_path / "trace").mkdir()
    (tmp_path / "trace/events.jsonl").write_bytes(raw)
    (tmp_path / "trace/summary.json").write_text(json.dumps(summary))
    (tmp_path / "worker.json").write_text(json.dumps(worker))
    (tmp_path / "sentinel_iter48_decisions.jsonl").write_text("\n".join(decisions) + "\n")
    (tmp_path / "delivery145.jsonl").write_text("".join(json.dumps(v) + "\n" for v in client))
    if mutation == "none":
        assert verify(tmp_path)["status"] == "supported"
    else:
        with pytest.raises(ValueError):
            verify(tmp_path)


@pytest.mark.parametrize(
    "memory", [(19999, 30), (21000, 23), (float("nan"), 30), (float("inf"), 30), (21000, None)]
)
def test_gpu_capacity_known_bads(memory):
    from experiments.iter145_constrained_execution.gpu_batch import capacity

    assert capacity(22564, 30)
    with pytest.raises(ValueError):
        capacity(*memory)


def test_gpu_outer_deadline_stops_process(tmp_path):
    import os
    import sys
    from experiments.iter145_constrained_execution.gpu_batch import invoke

    result = invoke(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        cwd=tmp_path,
        environment=os.environ.copy(),
        log=tmp_path / "deadline.log",
        timeout=0.05,
    )
    assert result == dict(returncode=124, deadline_exceeded=True)


@pytest.mark.parametrize("mutation", ["cost", "selection", "consumption"])
def test_gpu_attack_replay_known_bads(mutation):
    import json
    from experiments.iter145_constrained_execution.gpu_check import check_attack_execution

    events = json.loads(
        (ROOT / "experiments/iter145_constrained_execution/proof/integration_raw.json").read_text()
    )["cases"][0]["events"]
    actors = [
        e["value"] for e in events if e["event"] == "actor" and e["value"]["event"] == "consume"
    ]
    assert check_attack_execution(events, actors) == 2
    selection = next(
        e["value"] for e in events if e["event"] == "actor" and e["value"]["event"] == "select"
    )
    if mutation == "cost":
        selection["costs"][0] += 0.5
    elif mutation == "selection":
        selection["selected"] = (selection["selected"] + 1) % len(selection["candidates"])
    elif mutation == "consumption":
        actors[0]["states"][selection["actor"]][0] += 0.5
    with pytest.raises(ValueError):
        check_attack_execution(events, actors)


def test_gpu_output_guard_stops_owned_process(tmp_path):
    import os
    import sys
    from experiments.iter145_constrained_execution.gpu_batch import invoke

    def stop():
        raise ValueError("output_or_storage_limit")

    result = invoke(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        cwd=tmp_path,
        environment=os.environ.copy(),
        log=tmp_path / "output.log",
        timeout=10,
        guard=stop,
    )
    assert result["returncode"] == 125 and result["stop_reason"] == "output_or_storage_limit"
