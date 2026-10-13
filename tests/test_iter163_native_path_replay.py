"""Faults challenge native source execution, independent outcomes and ownership boundaries."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from experiments.iter163_native_path_replay import (
    admission,
    contract,
    native,
    execute as coordinator,
)
from experiments.iter163_native_path_replay.check import verify, verify_device
from experiments.iter163_native_path_replay.fixtures import execute
from experiments.iter163_native_path_replay.runner import classify
from experiments.iter151_recovery_canary.records import record

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def good(tmp_path_factory):
    return execute(ROOT, tmp_path_factory.mktemp("iter163") / "trace")


def test_source_exact_maneuver_completion(good):
    rows, summary, selected, geometry, slot, calls = good
    result = verify(rows, summary, selected, geometry, slot)
    assert result["steps"] == 66 and result["outcome"]["completion_qualified"]
    assert len([c for c in calls if c["kind"] == "render"]) == 402
    assert result["outcome"]["road_compliance"] is None


def test_native_background_failure_is_not_success(tmp_path):
    rows, summary, selected, geometry, slot, _ = execute(ROOT, tmp_path / "trace", background=True)
    result = verify(rows, summary, selected, geometry, slot)
    assert result["steps"] == 1 and result["outcome"]["background_collision"] is True
    assert result["outcome"]["completion_qualified"] is False
    assert result["outcome"]["progress_checks"]["nominal"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "action",
        "frame",
        "before",
        "after",
        "route",
        "rc",
        "background",
        "foreground",
        "missing_collision",
        "termination",
        "truncation",
        "reward",
        "missing_step",
        "duplicate_reset",
        "camera",
        "unknown_event",
        "actor",
        "outcome",
        "unknown_claim",
        "stop",
        "timing",
        "inference",
        "slot",
    ],
)
def test_independent_known_bads(good, fault):
    rows, summary, selected, geometry, slot, _ = copy.deepcopy(good)
    step = next(r for r in rows if r["event"] == "step")
    action = next(r for r in rows if r["event"] == "action")
    actor = next(
        r["value"] for r in rows if r["event"] == "actor" and r["value"]["event"] == "consume"
    )
    if fault == "action":
        action["applied"]["acc"] = 2.1
    elif fault == "frame":
        action["frame"] = 1
    elif fault == "before":
        action["before"][0] += 1
    elif fault == "after":
        step["after"][0] += 0.01
    elif fault == "route":
        rows[0]["route"][0][0] += 1
    elif fault == "rc":
        step["rc"] = 1
    elif fault == "background":
        step["collision_records"][0]["result"] = True
    elif fault == "foreground":
        step["collision_records"][1]["result"] = True
    elif fault == "missing_collision":
        step["collision_records"].pop()
    elif fault == "termination":
        step["terminated"] = True
    elif fault == "truncation":
        step["truncated"] = True
    elif fault == "reward":
        step["reward"] = 1000
    elif fault == "missing_step":
        rows.remove(step)
    elif fault == "duplicate_reset":
        rows.insert(1, copy.deepcopy(rows[1]))
    elif fault == "camera":
        step["rgb"].pop(next(iter(step["rgb"])))
    elif fault == "unknown_event":
        action["event"] = "fabricated"
    elif fault == "actor":
        actor["states"]["agent_0"][0] += 1
    elif fault == "outcome":
        summary["outcome"]["completion_qualified"] = False
    elif fault == "unknown_claim":
        summary["outcome"]["road_compliance"] = True
    elif fault == "stop":
        summary["stop_reason"] = "action_cap"
    elif fault == "timing":
        summary["timings"][0]["full_loop_ns"] = 0
    elif fault == "inference":
        summary["inference_bypassed"] = False
    elif fault == "slot":
        rows[0]["slot"]["scenario"] = "different.yaml"
    with pytest.raises((ValueError, KeyError)):
        verify(rows, summary, selected, geometry, slot)


@pytest.mark.parametrize("fault", ["reset", "clock", "route", "bounds"])
def test_runner_rejects_wrong_source_state(tmp_path, fault):
    def mutate(env):
        if fault == "reset":
            env.start_velo = 2
        elif fault == "clock":
            env.timestamp = 1
        elif fault == "route":
            env.ground_model[0][0, 0, 3] += 1
        elif fault == "bounds":
            env.kinematic["max_acc"] = 3

    _, summary, *_ = execute(ROOT, tmp_path / "trace", mutate=mutate)
    assert summary["status"] == "failed" and not summary["outcome"]["completion_qualified"]


def device_fixture(good):
    rows, summary, _, _, slot, _ = good
    actors = [
        r["value"] for r in rows if r["event"] == "actor" and r["value"]["event"] == "consume"
    ]
    steps = [r for r in rows if r["event"] == "step"]
    # Fabricated device metadata exercises receipt consistency only, never GPU qualification.
    renders = [
        dict(
            index=6 * t + j,
            time=t / 4,
            elapsed_ns=1,
            device="cuda:0",
            shape=[3, 450, 800],
            transforms=actors[max(0, t - 1)]["transforms"],
        )
        for t in range(67)
        for j in range(6)
    ]
    collisions = []
    for step in steps:
        for row in step["collision_records"]:
            collisions.append(
                dict(
                    row,
                    **({"device": "cuda:0", "points": 1} if row["kind"] == "background" else {}),
                )
            )
    return dict(
        status="completed",
        gpu_observed=True,
        inference_bypassed=True,
        summary=summary,
        slot=slot,
        episode=slot["id"],
        purpose="study",
        seed=144,
        actor_types={"agent_0": "ConstantPlanner"},
        geos="synthetic",
        torch="synthetic",
        cuda_device="synthetic",
        cleanup={"status": "absent"},
        render_events=renders,
        collision_events=collisions,
    )


@pytest.mark.parametrize(
    "fault", [None, "render", "transform", "background", "missing", "bypass", "runtime"]
)
def test_device_receipt_known_bads(good, fault):
    rows, summary, _, _, slot, _ = good
    worker = copy.deepcopy(device_fixture(good))
    if fault == "render":
        worker["render_events"][0]["device"] = "cpu"
    elif fault == "transform":
        worker["render_events"][6]["transforms"]["agent_0"][0][3] += 1
    elif fault == "background":
        worker["collision_events"][0]["points"] = 0
    elif fault == "missing":
        worker["render_events"].pop()
    elif fault == "bypass":
        worker["inference_bypassed"] = False
    elif fault == "runtime":
        worker["actor_types"] = {}
    if fault is None:
        verify_device(rows, summary, worker, slot)
    else:
        with pytest.raises(ValueError):
            verify_device(rows, summary, worker, slot)


@pytest.mark.parametrize("fault", ["packet", "geometry", "plan", "symlink"])
def test_packet_identity(tmp_path, fault):
    plan = json.loads((ROOT / admission.BASE / "STUDY_PLAN.json").read_text())
    for name in (
        admission.BASE + "/STUDY_PLAN.json",
        plan["selected_packet_path"],
        plan["geometry_path"],
        json.loads((ROOT / plan["selected_packet_path"]).read_text())["trace_path"],
    ):
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    name = (
        plan["selected_packet_path"]
        if fault in ("packet", "symlink")
        else plan["geometry_path"]
        if fault == "geometry"
        else admission.BASE + "/STUDY_PLAN.json"
    )
    p = tmp_path / name
    if fault == "symlink":
        p.unlink()
        p.symlink_to(ROOT / name)
    else:
        p.write_bytes(p.read_bytes() + b" " if fault != "plan" else b"{}")
    with pytest.raises((ValueError, OSError)):
        contract.packet(tmp_path)


@pytest.mark.parametrize("frame", [-1, 66, True, 1.5])
def test_no_out_of_order_action(good, frame):
    selected = good[2]
    with pytest.raises(ValueError):
        contract.action_at(selected, frame, selected["reset_state"])


def test_bad_control_cannot_be_applied(good):
    selected = copy.deepcopy(good[2])
    selected["actions"][0][0] = 3
    with pytest.raises(ValueError, match="action_bounds"):
        contract.action_at(selected, 0, selected["reset_state"])


def test_censored_and_missing_are_not_success():
    value = classify([], "action_cap", "completed")
    assert value["collision_observed"] is None and not value["completion_qualified"]
    assert value["road_compliance"] is None and value["censored"]


@pytest.mark.parametrize("block", [1, 2, -1, True])
def test_one_execution_block(block):
    with pytest.raises(ValueError):
        coordinator.block_pairs(block)


def test_duplicate_initialization_rejected(tmp_path, monkeypatch):
    document = json.loads((ROOT / admission.BASE / "STUDY_PLAN.json").read_text())
    monkeypatch.setattr(admission, "basis", lambda _: "qualified")
    args = (ROOT, tmp_path, document, 0, [], "qualified", 0, "manifest")
    assert len(admission.claim(*args)) == 2
    before = (tmp_path / "pair_000_started.json").read_bytes()
    with pytest.raises(ValueError, match="initialized_history"):
        admission.claim(*args)
    assert (tmp_path / "pair_000_started.json").read_bytes() == before


def test_operational_missing_and_failed_are_distinct(tmp_path):
    # The unchanged reconciliation protocol never converts absent evidence into success.
    with pytest.raises(FileNotFoundError):
        native.document(tmp_path, "missing.json")
    record(tmp_path / "duplicate.json", {"status": "failed"})
    with pytest.raises(FileExistsError):
        record(tmp_path / "duplicate.json", {"status": "completed"})
    assert hashlib.sha256((tmp_path / "duplicate.json").read_bytes()).hexdigest()


def operational_fixture(root, good):
    from experiments.iter149_observation_recovery.recovery import encode, digest
    from experiments.iter151_recovery_canary.records import record

    document = json.loads((ROOT / admission.BASE / "STUDY_PLAN.json").read_text())
    record(root / "plan.json", document)
    record(root / "execution_manifest.json", {"scope": "SYNTHETIC QUALIFICATION ONLY"})
    record(root / "pair_000_started.json", {"pair": 0, "plan_sha256": admission.PLAN})
    cases = []
    for slot in document["slots"]:
        rows, summary, *_ = copy.deepcopy(good)
        rows[0]["slot"] = slot
        summary["episode"] = slot["id"]
        worker = device_fixture((rows, summary, None, None, slot, None))
        worker["episode"] = slot["id"]
        destination = root / "runs" / slot["id"]
        (destination / "trace").mkdir(parents=True)
        raw = b"".join(encode(r) + b"\n" for r in rows)
        summary.update(events_sha256=digest(raw), events_bytes=len(raw))
        worker["summary"] = summary
        record(
            destination / "worker_started.json",
            {"slot": slot, "episode": slot["id"], "purpose": "study"},
        )
        record(destination / "worker.json", worker)
        record(destination / "trace/summary.json", summary)
        (destination / "trace/events.jsonl").write_bytes(raw)
        cases.append(
            dict(slot=slot, returncode=0, deadline_exceeded=False, cleanup={"status": "absent"})
        )
    record(
        root / "pair_000_result.json",
        dict(pair=0, status="completed", plan_sha256=admission.PLAN, cases=cases),
    )
    environment = dict(
        vm_id="3834622546652649531",
        vm_start="synthetic-start",
        host_boot="synthetic-boot",
        host_deadline_id="synthetic.timer",
    )
    binding, _ = native.bind(root, 0, environment)
    return document, binding


@pytest.mark.parametrize(
    "fault", [None, "schema", "identity", "summary", "trace", "missing", "client_not_required"]
)
def test_direct_action_native_reconciliation(tmp_path, good, fault):
    from experiments.iter149_observation_recovery.recovery import classify as observation_classify

    document, binding = operational_fixture(tmp_path, good)
    case = tmp_path / "runs" / document["slots"][0]["id"]
    if fault in ("schema", "identity", "summary"):
        p = case / "trace/summary.json"
        v = json.loads(p.read_text())
        if fault == "schema":
            v["schema"] = "sentinel.iter146.summary.v2"
        elif fault == "identity":
            v["episode"] = "different"
        else:
            v["outcome"]["execution_valid"] = False
        p.write_text(json.dumps(v))
    elif fault == "trace":
        p = case / "trace/events.jsonl"
        p.write_bytes(p.read_bytes() + b"\n")
    elif fault == "missing":
        (case / "worker.json").unlink()
    raw, blobs = native.observe(tmp_path, 0, binding, binding, "fixture/0", alive=False)
    status = observation_classify(raw, blobs, "fixture/0", binding, -1, None)[0]
    if fault in (None, "client_not_required"):
        assert status == "worker_complete"
        assert not list(case.glob("*decisions*")) and not (case / "delivery145.jsonl").exists()
    else:
        assert status == "partial_evidence"


def test_commit_archive_replay_roundtrip(tmp_path, good, monkeypatch):
    import subprocess
    from experiments.iter151_recovery_canary import collection
    from experiments.iter147_full_horizon_execution.coordinator import raw_identity
    from experiments.iter146_route_outcome_contract.check import read

    control = tmp_path / "control"
    control.mkdir()
    document, binding = operational_fixture(control, good)
    record(control / "pair_000_owner.json", dict(binding=binding))
    monkeypatch.setattr(collection, "alive", lambda *a: False)
    monkeypatch.setattr(collection, "idle", lambda: {})
    archive = collection.archive(control, 0)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Synthetic Qualification"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True
    )
    destination = repo / admission.BASE / "proof/study_raw/pair_000"
    collection.extract(control / "pair_000_raw.tar.gz", destination, archive)
    commit = coordinator.commit(repo, [destination], "synthetic retention fixture")
    assert len(raw_identity(repo, commit, destination)) == 64
    for slot in document["slots"]:
        rows, summary = read(destination / "runs" / slot["id"] / "trace")
        assert verify(rows, summary, good[2], good[3], slot)["outcome"]["completion_qualified"]
    # Exact retained raw is required: post-commit mutation is not accepted evidence.
    p = destination / "plan.json"
    p.write_bytes(p.read_bytes() + b" ")
    with pytest.raises(ValueError):
        raw_identity(repo, commit, destination)


def test_qualified_source_mutation_is_rejected(tmp_path):
    (tmp_path / admission.BASE).mkdir(parents=True)
    name = "source.py"
    (tmp_path / name).write_bytes(b"qualified source\n")
    manifest = {
        "files": {name: {"bytes": 17, "sha256": hashlib.sha256(b"qualified source\n").hexdigest()}}
    }
    record(tmp_path / admission.BASE / "INPUTS.json", manifest)
    receipt = dict(
        status="supported",
        inputs_sha256=admission.identity(manifest),
        plan_sha256=admission.PLAN,
        scientific_outcomes=0,
    )
    record(tmp_path / admission.BASE / "QUALIFICATION.json", receipt)
    assert admission.basis(tmp_path) == admission.identity(receipt)
    (tmp_path / name).write_bytes(b"changed source\n")
    with pytest.raises(ValueError, match="qualified_input_changed"):
        admission.basis(tmp_path)


def test_worker_is_dispatched_once_with_matching_owner(tmp_path, good, monkeypatch):
    import os
    from experiments.iter163_native_path_replay import worker

    document, binding = operational_fixture(tmp_path, good)
    record(tmp_path / "pair_000_owner.json", dict(process={"pid": os.getppid()}, binding=binding))
    monkeypatch.setattr(worker, "alive", lambda *_: True)
    calls = []
    assert worker.dispatch(tmp_path, 0, lambda *a: calls.append(a)) is None
    with pytest.raises(FileExistsError):
        worker.dispatch(tmp_path, 0, lambda *a: calls.append(a))
    assert len(calls) == 1 and calls[0][2] == document["slots"][0]


@pytest.mark.parametrize(
    "fault",
    [None, "success_reply", "other_error", "missing", "running", "new_start", "wrong_vm", "shape"],
)
def test_denied_start_is_not_confused_with_owned_start(fault):
    from experiments.iter163_native_path_replay.startup import denied_start

    before = dict(
        id="3834622546652649531",
        status="TERMINATED",
        lastStartTimestamp="prior",
        machineType="g2-standard-8",
        guestAccelerators=[{"acceleratorType": "nvidia-l4"}],
    )
    observations = [copy.deepcopy(before), copy.deepcopy(before)]
    code, stderr = 1, "ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS"
    if fault == "success_reply":
        code = 0
    elif fault == "other_error":
        stderr = "UNKNOWN_NETWORK_ERROR"
    elif fault == "missing":
        observations.pop()
    elif fault == "running":
        observations[-1]["status"] = "RUNNING"
    elif fault == "new_start":
        observations[-1]["lastStartTimestamp"] = "new"
    elif fault == "wrong_vm":
        observations[-1]["id"] = "other"
    elif fault == "shape":
        observations[-1]["machineType"] = "other"
    if fault is None:
        value = denied_start(before, code, stderr, observations)
        assert value["new_start_observed"] is False and value["scientific_slots_initialized"] == 0
    else:
        with pytest.raises(ValueError):
            denied_start(before, code, stderr, observations)


def test_packet_is_exact_admitted_source_path(good):
    selected = good[2]
    original = json.loads((ROOT / selected["trace_path"]).read_text())
    assert selected["actions"] == [r["action"] for r in original[1:]]
    assert selected["expected_model_states"] == [r["state"] for r in original]
    assert len(selected["actions"]) == 66
    assert contract.action_at(selected, 65, selected["expected_model_states"][65])


@pytest.mark.parametrize("n", [0, 100, 101])
def test_mask_tap_preserves_exact_native_threshold(n):
    import ast
    import torch
    from experiments.iter163_native_path_replay.background import tapped
    from experiments.iter155_background_witness.geometry import vertices

    binding = json.loads((ROOT / admission.BASE / "BACKGROUND.json").read_text())
    source = ROOT / binding["source_path"]
    node = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "bg_collision_det"
    )
    ns = {"torch": torch}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), ns)
    masks = []
    observed = tapped(
        ns["bg_collision_det"],
        lambda m, p, b: masks.append(m.clone()),
        binding["predicate_source_sha256"],
    )
    points = torch.tensor([[0.0, 0.5, 0.0]] * n, dtype=torch.float32).reshape(n, 3)
    box = torch.tensor(vertices([0.0, 0.0, 0.0], 0), dtype=torch.float32)
    assert observed(points, box) is ns["bg_collision_det"](points, box) is (n > 100)
    assert len(masks) == 1 and int(masks[0].sum()) == n
    with pytest.raises(ValueError, match="background_source_identity"):
        tapped(ns["bg_collision_det"], lambda *_: None, "0" * 64)


def background_fixture():
    import numpy as np
    from experiments.iter155_background_witness.geometry import vertices

    points = [[0.0, 0.5, 0.0]] * 101
    ground = [np.eye(4).tolist()]
    row = dict(
        time=0.25,
        population_sha256="expected",
        population_dtype="<f4",
        points=101,
        mask_encoding="packbits_little_zero_padding",
        mask_hex=(b"\xff" * 12 + b"\x1f").hex(),
        box=vertices([0.0, 0.0, 0.0], 0),
        count=101,
        result=True,
    )
    return row, [0.0, 0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0], points, ground


@pytest.mark.parametrize(
    "fault",
    [None, "population", "count", "result", "padding", "encoding", "truncated", "point_count"],
)
def test_background_known_bads(fault):
    from experiments.iter163_native_path_replay.background_check import query

    row, state, position, points, ground = background_fixture()
    if fault == "population":
        row["population_sha256"] = "changed"
    elif fault == "count":
        row["count"] = 0
    elif fault == "result":
        row["result"] = False
    elif fault == "padding":
        row["mask_hex"] = "ff" * 13
    elif fault == "encoding":
        row["mask_hex"] = row["mask_hex"].upper()
    elif fault == "truncated":
        row["mask_hex"] = row["mask_hex"][:-2]
    elif fault == "point_count":
        row["points"] = 100
    if fault is None:
        result = query(row, state, position, points, ground, "expected")
        assert result["status"] == "supported" and result["scalar_count"] == 101
    else:
        with pytest.raises(ValueError):
            query(row, state, position, points, ground, "expected")


@pytest.mark.parametrize("fault", ["mask", "box", "height"])
def test_background_discrepancy_is_retained_not_success(fault):
    from experiments.iter163_native_path_replay.background_check import query

    row, state, position, points, ground = background_fixture()
    if fault == "mask":
        row.update(mask_hex="00" * 13, count=0, result=False)
    elif fault == "box":
        for p in row["box"]:
            p[0] += 1
    else:
        position[1] = 1
    result = query(row, state, position, points, ground, "expected")
    assert result["status"] == "contradicted"


def test_background_threshold_ambiguity_stays_unknown():
    from experiments.iter163_native_path_replay.background_check import query

    row, state, position, points, ground = background_fixture()
    points[:] = [[0.0, 1e-8, 0.0]] * 101
    result = query(row, state, position, points, ground, "expected")
    assert result["status"] == "inconclusive"
    assert result["certain_inside"] == 0 and result["possible_inside"] == 101


@pytest.mark.parametrize(
    "fault,expected",
    [
        (None, "supported"),
        ("different", "inconclusive"),
        ("collision", "contradicted"),
        ("off_route", "contradicted"),
        ("background", "contradicted"),
        ("numeric", "inconclusive"),
        ("horizon", "inconclusive"),
    ],
)
def test_replica_and_scientific_status_are_separate(fault, expected):
    from experiments.iter163_native_path_replay.replay import pair_status

    reports = [
        dict(
            scientific=[0],
            outcome=dict(
                completion_qualified=True, collision_observed=False, off_route_observed=False
            ),
            background=dict(status="supported"),
        )
        for _ in range(2)
    ]
    if fault == "different":
        reports[1]["scientific"] = [1]
    elif fault == "collision":
        reports[1]["outcome"]["collision_observed"] = True
    elif fault == "off_route":
        reports[1]["outcome"]["off_route_observed"] = True
    elif fault == "background":
        reports[1]["background"]["status"] = "contradicted"
    elif fault == "numeric":
        reports[1]["background"]["status"] = "inconclusive"
    elif fault == "horizon":
        reports[1]["outcome"]["completion_qualified"] = False
    assert pair_status(reports)[1] == expected
    with pytest.raises(ValueError, match="replica_inventory"):
        pair_status(reports[:1])


@pytest.mark.parametrize(
    "fault", [None, "points_dtype", "points_count", "box", "mask", "nonfinite"]
)
def test_mask_capture_validates_native_inputs(fault):
    import torch
    from experiments.iter163_native_path_replay.background import capture
    from experiments.iter155_background_witness.geometry import vertices

    points = torch.zeros((276519, 3), dtype=torch.float32)
    box = torch.tensor(vertices([0.0, 0.0, 0.0], 0), dtype=torch.float32)
    mask = torch.zeros(276519, dtype=torch.bool)
    if fault == "points_dtype":
        points = points.double()
    elif fault == "points_count":
        points = points[:-1]
    elif fault == "box":
        box = box[:7]
    elif fault == "mask":
        mask = mask.to(torch.uint8)
    elif fault == "nonfinite":
        box[0, 0] = float("nan")
    if fault is None:
        value = capture(mask, points, box)
        assert value["count"] == 0 and len(value["mask_hex"]) == 69130
    else:
        with pytest.raises(ValueError, match="background_input_shape"):
            capture(mask, points, box)


def test_mask_tap_rejects_unqualified_return_shape(monkeypatch):
    from experiments.iter163_native_path_replay import background

    source = "def other(points, box):\n    return False\n"
    monkeypatch.setattr(background.inspect, "getsource", lambda _: source)
    identity = hashlib.sha256(source.encode()).hexdigest()
    with pytest.raises(ValueError, match="background_source_shape"):
        background.tapped(lambda: None, lambda *_: None, identity)


@pytest.mark.parametrize("position", [[0], [0, 0, 0, 0], [0, float("nan"), 0]])
def test_background_missing_position_is_invalid(position):
    from experiments.iter163_native_path_replay.background_check import query

    row, state, _, points, ground = background_fixture()
    with pytest.raises(ValueError, match="native_position"):
        query(row, state, position, points, ground, "expected")
