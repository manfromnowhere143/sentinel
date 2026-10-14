"""Known-bads for preserved history, absolute clocks, concatenation and admission."""

import copy
import json
from pathlib import Path
import subprocess
import time

import numpy as np
import pytest

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter161_grouping_width_ablation.search import search as original_search
from experiments.iter164_monitor_time_continuation import prefix as producer
from experiments.iter164_monitor_time_continuation import prefix_check, run, check
from experiments.iter164_monitor_time_continuation.binding import bind_history
from experiments.iter164_monitor_time_continuation.common import BASE, encode, sha, source_check
from experiments.iter164_monitor_time_continuation.continuation import concatenate, prefix_binding
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter164_monitor_time_continuation.search import search

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root).decode().strip()


def commit(root):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Daniel Wahnich",
        "-c",
        "user.email=cogitoergosum143@gmail.com",
        "commit",
        "-qm",
        "Constructed qualification fixture",
    )
    return git(root, "rev-parse", "HEAD")


def fixture_data(root):
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 2.0, 0.0],
        route=[[0.0, i / 10] for i in range(81)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={
            "before_branch": dict(hazard_time=0.25, rc=0.0),
            "after_branch": dict(hazard_time=1.0, rc=0.0),
        },
    )
    points = np.array([[100.0, 0.5, 100.0]], dtype="<f4")
    arrays = dict(
        population_xyz=points.copy(),
        selected_xyz=points.copy(),
        population_features=np.array([[0.0, 0.0, 1.0]], dtype="<f4"),
        population_opacity=np.array([1.0], dtype="<f4"),
        selection=np.array([1], dtype="u1"),
        ground_poses=np.eye(4, dtype="<f4")[None, :, :],
    )
    plan = dict(
        start_frame=2,
        beam_width=24,
        attempt_budget=4000,
        max_actions=24,
        per_run_seconds=30,
        prefix_producer_seconds=60,
        prefix_checker_seconds=60,
        search_producer_seconds=120,
        search_checker_seconds=120,
        max_rss_bytes=1024**3,
        minimum_free_bytes=0,
        max_output_bytes=16 * 1024**2,
        finalization_reserve_bytes=1024**2,
        selected_points=1,
        population_sha256=sha(points.tobytes()),
        source_files=[],
        inputs={},
        histories=[],
    )
    for replica in range(2):
        episode = f"toy_{replica}"
        events = []

        def event(kind, **fields):
            events.append(dict(event=kind, seq=len(events), **fields))

        event("header", episode=episode, arm="monitor", seed=144, route=geometry["route"])
        state = geometry["reset"]
        event("reset", state=state, time=0.0)
        decisions = []
        for frame in range(3):
            box = [state[0], -state[1], 0.0, 1.6, 3.0, 1.5, -state[2]]
            info = dict(timestamp=frame / 4, obj_boxes=[], ego_box=box)
            event("observation", frame=frame, time=frame / 4, info=info)
            decision = dict(frame_index=frame, ts=frame / 4, fired=frame == 2)
            decisions.append(decision)
            event("monitor", frame=frame, raw=json.dumps(decision))
            event(
                "control",
                frame=frame,
                result=dict(applied=[0.0, 0.0], application_time=(frame + 1) / 4),
            )
            if frame == 2:
                break
            before = state
            state = transition(state, [0.0, 0.0], OLD)
            box = [state[0], -state[1], 0.0, 1.6, 3.0, 1.5, -state[2]]
            event(
                "actor",
                value=dict(
                    event="consume",
                    time=(frame + 1) / 4,
                    states={"agent_0": [100.0, 100.0, 0.0, 0.0]},
                    transforms={"agent_0": [[1.0, 0.0], [0.0, 1.0]]},
                ),
            )
            event(
                "step",
                frame=frame + 1,
                time=(frame + 1) / 4,
                before=before,
                after=state,
                applied=dict(acc=0.0, steer_rate=0.0),
                info=dict(timestamp=(frame + 1) / 4, obj_boxes=[], ego_box=box),
            )
            route = route_outcome(state, geometry["route"])
            event(
                "outcome_observation",
                frame=frame + 1,
                time=(frame + 1) / 4,
                collision=False,
                off_route=False,
                source_completion=False,
                nearest_index=route["nearest"],
                rc=route["rc"],
                route_distance=route["distance"],
            )
        trace = f"history_{replica}.jsonl"
        decision = f"decisions_{replica}.jsonl"
        (root / trace).write_bytes(b"".join(encode(r) for r in events))
        (root / decision).write_bytes(b"".join(encode(r) for r in decisions))
        plan["histories"].append(
            dict(
                episode=episode,
                trace_path=trace,
                decision_path=decision,
                trace_sha256=sha((root / trace).read_bytes()),
                decision_sha256=sha((root / decision).read_bytes()),
            )
        )
    return geometry, arrays, plan


@pytest.fixture
def prefix_acquired(tmp_path, monkeypatch, request):
    root = tmp_path
    git(root, "init", "-q")
    (root / BASE / "proof").mkdir(parents=True)
    geometry, arrays, plan = fixture_data(root)
    changes = getattr(request, "param", {})
    if "prefix_points" in changes:
        points = np.array([changes["prefix_points"]] * 101, dtype="<f4")
        arrays.update(
            population_xyz=points.copy(),
            selected_xyz=points.copy(),
            population_features=np.tile(np.array([[0.0, 0.0, 1.0]], dtype="<f4"), (101, 1)),
            population_opacity=np.ones(101, dtype="<f4"),
            selection=np.ones(101, dtype="u1"),
        )
        plan.update(selected_points=101, population_sha256=sha(points.tobytes()))
    plan.update({k: v for k, v in changes.items() if k != "prefix_points"})
    (root / BASE / "PLAN.json").write_bytes(encode(plan))
    for module in [producer, prefix_check, run, check]:
        monkeypatch.setattr(
            module,
            "inputs",
            lambda *args: (copy.deepcopy(geometry), copy.deepcopy(OLD), copy.deepcopy(arrays)),
        )
    source = commit(root)
    raw = root / BASE / "proof/prefix_raw"
    producer.run(root, raw, source)
    raw_commit = commit(root)
    admission = prefix_check.check(root, raw, raw_commit)
    (root / BASE / "proof/prefix_admission.json").write_bytes(encode(admission))
    prefix_commit = commit(root)
    return root, geometry, arrays, plan, source, raw_commit, prefix_commit, admission


@pytest.fixture
def acquired(prefix_acquired):
    root, geometry, arrays, plan, source, _, prefix_commit, _ = prefix_acquired
    raw = root / BASE / "proof/search_raw"
    run.run(root, raw, source, prefix_commit)
    return (*prefix_acquired, raw, commit(root))


def test_full_two_stage_qualification(acquired):
    root, _, _, _, _, _, _, prefix, raw, raw_commit = acquired
    assert prefix["status"] == "supported" and prefix["verified_states"] == 6
    result = check.check(root, raw, raw_commit)
    assert result["status"] == "supported" and result["complete_runs"] == 1
    assert result["start_frame"] == 2 and result["progress_checks"] == 2
    assert result["selected_actions"] == result["suffix_actions"] + 2
    assert result["new_driving_episodes"] == result["provider_spend"] == 0


def test_duplicate_stage_is_refused(prefix_acquired):
    root, _, _, _, source, *_ = prefix_acquired
    with pytest.raises(FileExistsError):
        producer.run(root, root / BASE / "proof/prefix_raw", source)


def test_unqualified_prefix_cannot_initialize_search(prefix_acquired):
    root, _, _, plan, source, _, _, _ = prefix_acquired
    path = root / BASE / "proof/prefix_admission.json"
    doc = json.loads(path.read_text())
    doc["status"] = "contradicted"
    path.write_bytes(encode(doc))
    bad_commit = commit(root)
    with pytest.raises(ValueError, match="prefix_not_qualified"):
        run.run(root, root / BASE / "proof/search_raw", source, bad_commit)
    assert not (root / BASE / "proof/search_raw").exists()


@pytest.mark.parametrize("kind", ["clock", "state", "time", "uncommitted"])
def test_corrupted_prefix_admission_refused(prefix_acquired, kind):
    root, _, _, plan, source, _, prefix_commit, _ = prefix_acquired
    p = root / BASE / "proof/prefix_admission.json"
    d = json.loads(p.read_text())
    if kind == "clock":
        d["branch"]["frame"] = 0
    elif kind == "state":
        d["branch"]["state"][3] = 0.0
    elif kind == "time":
        d["branch"]["time"] = 0.0
    else:
        d["verified_states"] = 0
    p.write_bytes(encode(d))
    if kind != "uncommitted":
        prefix_commit = commit(root)
    with pytest.raises(ValueError):
        prefix_binding(root, prefix_commit, plan, source)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_action",
        "action",
        "state",
        "frame",
        "actor",
        "actor_time",
        "observation_clock",
        "decision_clock",
        "early_fire",
        "future_action_time",
    ],
)
def test_historical_corruptions_rejected(prefix_acquired, kind):
    root, geometry, _, plan, _, _, _, _ = prefix_acquired
    spec = copy.deepcopy(plan["histories"][0])
    trace = json.loads((root / BASE / "proof/prefix_raw/replica_0/trace.json").read_text())
    path = root / spec["trace_path"]
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    decisions = [json.loads(x) for x in (root / spec["decision_path"]).read_text().splitlines()]
    steps = [r for r in rows if r["event"] == "step"]
    if kind == "missing_action":
        rows.remove(steps[0])
    elif kind == "action":
        steps[0]["applied"]["acc"] = 1.0
    elif kind == "state":
        steps[0]["after"][3] = 0.0
    elif kind == "frame":
        steps[0]["frame"] = 0
    elif kind == "actor":
        [r for r in rows if r["event"] == "actor"][-1]["value"]["states"]["agent_0"][0] = 101.0
    elif kind == "actor_time":
        [r for r in rows if r["event"] == "actor"][-1]["value"]["time"] = 0.0
    elif kind == "observation_clock":
        next(r for r in rows if r["event"] == "observation")["time"] = 1.0
    elif kind == "decision_clock":
        decisions[0]["ts"] = 1.0
    elif kind == "early_fire":
        decisions[0]["fired"] = True
    elif kind == "future_action_time":
        [r for r in rows if r["event"] == "control"][-1]["result"]["application_time"] = 0.5
    for i, r in enumerate(rows):
        r["seq"] = i
    path.write_bytes(b"".join(encode(r) for r in rows))
    spec["trace_sha256"] = sha(path.read_bytes())
    p = root / spec["decision_path"]
    p.write_bytes(b"".join(encode(r) for r in decisions))
    spec["decision_sha256"] = sha(p.read_bytes())
    with pytest.raises(ValueError):
        bind_history(root, spec, trace, geometry, plan)


@pytest.mark.parametrize("kind", ["clock", "state", "speed", "background", "omission"])
def test_invalid_splices_refused(acquired, kind):
    root, _, _, _, _, _, _, _, raw, _ = acquired
    prefix = json.loads((root / BASE / "proof/prefix_raw/replica_0/trace.json").read_text())
    suffix = json.loads((raw / "selected/trace.json").read_text())
    if kind == "clock":
        suffix[0]["frame"] = 0
    elif kind == "state":
        suffix[0]["state"][0] += 1.0
    elif kind == "speed":
        suffix[0]["state"][3] = 0.0
    elif kind == "background":
        suffix[0]["background"]["count"] = 1
    else:
        suffix.pop(1)
    with pytest.raises(ValueError):
        concatenate(prefix, suffix)


@pytest.mark.parametrize(
    "kind",
    [
        "frame",
        "depth",
        "horizon",
        "false_complete",
        "width",
        "missing_mask",
        "corrupt_mask",
        "extra_file",
        "resource",
        "uncommitted",
    ],
)
def test_continuation_corruptions_refused(acquired, kind):
    root, _, _, plan, _, _, _, _, raw, raw_commit = acquired
    result = json.loads((raw / "result.json").read_text())
    execution = json.loads((raw / "execution.json").read_text())
    if kind == "frame":
        result["start_frame"] = 0
    elif kind == "depth":
        result["completed_depth"] -= 2
    elif kind == "horizon":
        result["stop"] = "horizon"
    elif kind == "false_complete":
        result["selected"] = None
    elif kind == "width":
        result["width"] = True
    elif kind == "missing_mask":
        next((raw / "selected").glob("mask_*.bin")).unlink()
    elif kind == "corrupt_mask":
        next((raw / "selected").glob("mask_*.bin")).write_bytes(b"bad")
    elif kind == "extra_file":
        (raw / "extra").write_text("bad")
    elif kind == "resource":
        execution["elapsed_seconds"] = plan["search_producer_seconds"] + 1
    elif kind == "uncommitted":
        execution["new_driving_episodes"] = 1
    execution["result"] = result
    (raw / "result.json").write_bytes(encode(result))
    (raw / "execution.json").write_bytes(encode(execution))
    if kind != "uncommitted":
        raw_commit = commit(root)
    with pytest.raises((ValueError, FileNotFoundError)):
        check.check(root, raw, raw_commit)


def test_clock_zero_preserves_old_search(tmp_path):
    geometry, arrays, plan = fixture_data(tmp_path)
    plan["start_frame"] = 0
    query = query_for(
        dict(geometry=geometry, points=arrays["selected_xyz"], ground=arrays["ground_poses"])
    )
    events = []
    new = search(
        geometry,
        OLD,
        plan,
        lambda s: summary(query(s)),
        lambda k, r: events.append((k, r)),
        "exact",
        dict(frame=0, time=0.0, state=geometry["reset"]),
    )
    old_events = []
    old = original_search(
        geometry,
        OLD,
        plan,
        lambda s: summary(query(s)),
        lambda k, r: old_events.append((k, r)),
        "exact",
    )
    assert events == old_events
    for result in (new, old):
        result.pop("elapsed_seconds")
    new.pop("start_frame")
    assert new == old


@pytest.mark.parametrize(
    "branch,reason",
    [
        (dict(frame=0, time=0.5), "branch_clock"),
        (dict(frame=2, time=0.0), "branch_time"),
        (dict(frame=True, time=0.25), "start_frame"),
    ],
)
def test_search_rejects_clock_reset(tmp_path, branch, reason):
    geometry, _, plan = fixture_data(tmp_path)
    with pytest.raises(ValueError, match=reason):
        search(geometry, OLD, plan, None, None, "exact", dict(**branch, state=geometry["reset"]))


def test_shifted_checkpoint_is_not_silently_ignored(acquired):
    root, geometry, arrays, _, _, _, _, _, raw, _ = acquired
    prefix = json.loads((root / BASE / "proof/prefix_raw/replica_0/trace.json").read_text())
    suffix = json.loads((raw / "selected/trace.json").read_text())
    joined = concatenate(prefix, suffix)
    # Deadline before the branch must still be checked in the preserved prefix.
    geometry["comparators"]["before_branch"]["rc"] = 1.0

    def mask(frame):
        folder = root / BASE / "proof/prefix_raw/replica_0" if frame <= 2 else raw / "selected"
        return (folder / f"mask_{frame:03d}.bin").read_bytes()

    with pytest.raises(ValueError, match="rejection_reason|path_rejected"):
        verify_path(
            joined,
            geometry,
            OLD,
            arrays["selected_xyz"].tolist(),
            arrays["ground_poses"].tolist(),
            mask,
            True,
            time.monotonic() + 10,
        )


def test_source_encoding():
    with pytest.raises(ValueError, match="source_encoding"):
        source_check(ROOT, {}, "typo")


@pytest.mark.parametrize("prefix_acquired", [{"attempt_budget": 1}], indirect=True)
def test_valid_capped_miss_retains_original_prefix(acquired):
    root, _, _, _, _, _, _, _, raw, raw_commit = acquired
    result = check.check(root, raw, raw_commit)
    assert result["status"] == "contradicted" and result["invalid_runs"] == 0
    assert result["suffix_actions"] == 0 and result["verified_states"] == 3
    assert result["progress_checks"] == 1  # Historical checkpoint still counted.


@pytest.mark.parametrize(
    "prefix_acquired",
    [{"prefix_points": [0.0, 0.5, 0.5]}, {"prefix_points": [0.0, 0.5, 1.5]}],
    indirect=True,
)
def test_independently_rejected_prefix_prevents_search(prefix_acquired):
    root, _, _, _, source, _, prefix_commit, result = prefix_acquired
    assert result["status"] == "contradicted" and result["phase"] == "prefix_rejected"
    assert result["verified_states"] == 6
    with pytest.raises(ValueError, match="prefix_not_qualified"):
        run.run(root, root / BASE / "proof/search_raw", source, prefix_commit)
    assert not (root / BASE / "proof/search_raw").exists()


@pytest.mark.parametrize("prefix_acquired", [{"max_actions": 3}], indirect=True)
def test_absolute_horizon_does_not_grant_prefix_actions_again(acquired):
    root, _, _, _, _, _, _, _, raw, raw_commit = acquired
    result = check.check(root, raw, raw_commit)
    depths = [json.loads(line) for line in (raw / "depths.jsonl").read_text().splitlines()]
    assert [row["frame"] for row in depths] == [3]
    assert result["result"]["stop"] == "horizon"
    assert result["suffix_actions"] <= 1 and result["final_absolute_time"] <= 0.75


def test_initialized_search_input_failure_is_retained(prefix_acquired, monkeypatch):
    root, _, _, _, source, _, prefix_commit, _ = prefix_acquired
    raw = root / BASE / "proof/search_raw"

    def broken_inputs(*args):
        raise ValueError("constructed_missing_input")

    monkeypatch.setattr(run, "inputs", broken_inputs)
    with pytest.raises(ValueError, match="constructed_missing_input"):
        run.run(root, raw, source, prefix_commit)
    failure = json.loads((raw / "failure.json").read_text())
    assert failure["status"] == "invalid"
    assert (raw / "initialized.json").exists() and not (raw / "execution.json").exists()
