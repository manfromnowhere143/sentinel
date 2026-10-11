from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from experiments.iter152_recovery_continuation import admission as a, aggregate, ownership, worker
from experiments.iter152_recovery_continuation.records import record, read
from experiments.iter150_cloud_observation.native import bind, observe
from experiments.iter149_observation_recovery.qualify import BINDING
from experiments.iter149_observation_recovery.recovery import classify

ROOT = Path(__file__).resolve().parents[1]
PLAN = read(ROOT / a.BASE / "STUDY_PLAN.json")


def receipts(count):
    result = []
    for i in range(count):
        result.append(
            dict(
                status="supported",
                pair=i,
                plan_sha256=a.PLAN,
                previous_receipt_sha256=a.identity(result[-1])
                if result
                else a.identity(PLAN["historical_comparator"]),
                historical_comparator_sha256=a.identity(PLAN["historical_comparator"]),
                historical_slots_counted_as_new=0,
                replica_check="supported",
                raw_commit="a" * 40,
                raw_inventory_sha256="b" * 64,
                steps=2,
                scenario_comparison_status="supported",
            )
        )
    return result


def test_exact_unrun_population_preserved():
    a.validate_plan(PLAN)
    original = read(ROOT / "experiments/iter151_recovery_canary/STUDY_PLAN.json")
    assert len(PLAN["slots"]) == 14
    for actual, old in zip(PLAN["slots"], original["slots"][2:]):
        assert {k: v for k, v in actual.items() if k not in ("id", "index")} == {
            k: v for k, v in old.items() if k not in ("id", "index")
        }
    assert len({s["id"] for s in PLAN["slots"]}) == 14
    assert not ({s["id"] for s in PLAN["slots"]} & {s["id"] for s in original["slots"]})
    assert PLAN["slots"][0]["arm"] == "monitor"
    from experiments.iter151_recovery_canary.admission import validate_plan

    with pytest.raises(ValueError):
        validate_plan(PLAN)


@pytest.mark.parametrize(
    "field",
    [
        "slots",
        "initialized_retry",
        "child_seconds",
        "compute_cap_usd",
        "purpose",
        "success_stopping",
    ],
)
def test_plan_mutation_rejected(field):
    changed = deepcopy(PLAN)
    changed[field] = None
    with pytest.raises(ValueError, match="canary_plan_changed"):
        a.validate_plan(changed)


@pytest.mark.parametrize(
    "fault", ["order", "status", "plan", "chain", "raw", "replica", "comparison"]
)
def test_history_known_bads(fault):
    rows = receipts(4)
    a.history(PLAN, rows, 4)
    if fault == "order":
        rows[0]["pair"] = True
    if fault == "status":
        rows[0]["status"] = "invalid"
    if fault == "plan":
        rows[0]["plan_sha256"] = "f" * 64
    if fault == "chain":
        rows[0]["previous_receipt_sha256"] = "f" * 64
    if fault == "raw":
        rows[0]["raw_commit"] = "uncommitted"
    if fault == "replica":
        rows[0]["replica_check"] = "failed"
    if fault == "comparison":
        rows[2]["scenario_comparison_status"] = "failed"
    with pytest.raises(ValueError):
        a.history(PLAN, rows, 4)


@pytest.mark.parametrize("pair", [-1, 8, True, 1.0])
def test_pair_bound(pair):
    with pytest.raises(ValueError):
        a.history(PLAN, [], pair)


@pytest.mark.parametrize("delta", [2800, -1, float("inf"), float("nan"), True])
def test_current_time_reserve(delta):
    with pytest.raises(ValueError):
        a.remaining(delta, 0)
    a.remaining(2801, 0)


def test_exclusive_claim_before_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "basis", lambda root: "q")
    chosen = a.claim(ROOT, tmp_path, PLAN, 0, [], "q", 0, "m")
    assert chosen == PLAN["slots"][:2]
    original = (tmp_path / "pair_000_started.json").read_bytes()
    with pytest.raises(ValueError, match="initialized_history"):
        a.claim(ROOT, tmp_path, PLAN, 0, [], "q", 0, "m")
    assert (tmp_path / "pair_000_started.json").read_bytes() == original
    with pytest.raises(ValueError):
        a.claim(ROOT, tmp_path, PLAN, 1, [], "q", 0, "m")
    with pytest.raises(ValueError):
        a.claim(ROOT, tmp_path, PLAN, 0, [], "q", 1, "m")
    with pytest.raises(ValueError):
        a.claim(ROOT, tmp_path, PLAN, 0, [], "wrong", 0, "m")


def test_prior_marker_and_parent_required(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "basis", lambda root: "q")
    a.claim(ROOT, tmp_path, PLAN, 0, [], "q", 0, "m")
    rows = receipts(1)
    with pytest.raises(FileNotFoundError):
        a.claim(ROOT, tmp_path, PLAN, 1, rows, "q", 0, "m")
    parent = dict(
        status="completed",
        pair=0,
        plan_sha256=a.PLAN,
        cases=[
            dict(slot=s, returncode=0, deadline_exceeded=False, cleanup={"status": "absent"})
            for s in PLAN["slots"][:2]
        ],
    )
    record(tmp_path / "pair_000_result.json", parent)
    with pytest.raises(ValueError, match="started_receipt_changed"):
        a.claim(ROOT, tmp_path, PLAN, 1, rows, "q", 0, "different-manifest")
    assert a.claim(ROOT, tmp_path, PLAN, 1, rows, "q", 0, "m") == PLAN["slots"][2:4]


def test_qualification_source_binding(tmp_path):
    from experiments.iter150_cloud_observation.native import file

    base = tmp_path / a.BASE
    base.mkdir(parents=True)
    source = tmp_path / "source.py"
    source.write_text("first")
    inputs = {"files": {"source.py": file(tmp_path, "source.py", 100)}}
    record(base / "INPUTS.json", inputs)
    record(
        base / "QUALIFICATION.json",
        dict(
            status="supported",
            inputs_sha256=a.identity(inputs),
            plan_sha256=a.PLAN,
            scientific_outcomes=0,
        ),
    )
    assert len(a.basis(tmp_path)) == 64
    source.write_text("changed")
    with pytest.raises(ValueError, match="qualified_input_changed"):
        a.basis(tmp_path)


@pytest.fixture
def proc(tmp_path):
    p = tmp_path / "proc"
    folder = p / "12"
    folder.mkdir(parents=True)
    fields = ["S", "1"] + ["0"] * 17 + ["12345"] + ["0"] * 30
    (folder / "stat").write_text("12 (has ) spaces) " + " ".join(fields))
    (folder / "cmdline").write_bytes(b"python\0-u\0-m\0pair\0")
    (folder / "exe").symlink_to("/usr/bin/python3")
    (folder / "cwd").symlink_to("/owned")
    boot = p / "sys/kernel/random/boot_id"
    boot.parent.mkdir(parents=True)
    boot.write_text(BINDING["host_boot"])
    return p


def test_actual_proc_field_offset_and_parentheses(proc):
    value = ownership.snapshot(12, proc)
    assert value["start_ticks"] == 12345 and value["parent"] == 1
    assert value["command"] == ["python", "-u", "-m", "pair"]
    owner = dict(binding=BINDING, process=value)
    assert ownership.alive(owner, BINDING, proc)
    (proc / "12/cmdline").unlink()
    assert ownership.alive(owner, BINDING, proc) is False


@pytest.mark.parametrize(
    "field", ["pid", "start_ticks", "command", "executable", "cwd", "boot", "parent", "binding"]
)
def test_live_owner_identity_known_bads(proc, field):
    owner = dict(binding=deepcopy(BINDING), process=ownership.snapshot(12, proc))
    if field == "binding":
        owner["binding"]["source_sha256"] = "f" * 64
    elif field == "pid":
        owner["process"][field] = -1
    else:
        owner["process"][field] = "different"
    with pytest.raises(ValueError):
        ownership.alive(owner, BINDING, proc)


def test_owner_partial_is_not_completion(tmp_path):
    record(tmp_path / "plan.json", PLAN)
    record(tmp_path / "execution_manifest.json", {"fixture": True})
    record(tmp_path / "pair_000_started.json", dict(pair=0, plan_sha256=a.PLAN))
    binding, _ = bind(tmp_path, 0, BINDING)
    for active, label in [(True, "worker_running"), (False, "partial_evidence")]:
        raw, blobs = observe(tmp_path, 0, binding, binding, "read/0", alive=active)
        assert classify(raw, blobs, "read/0", binding, -1, None)[0] == label


def test_worker_dispatch_exact_slot_once(tmp_path, monkeypatch):
    record(tmp_path / "plan.json", PLAN)
    record(tmp_path / "pair_000_started.json", dict(pair=0, plan_sha256=a.PLAN))
    record(tmp_path / "execution_manifest.json", {"fixture": True})
    record(
        tmp_path / "pair_000_owner.json",
        dict(process={"pid": os.getppid()}, binding=bind(tmp_path, 0, BINDING)[0]),
    )
    monkeypatch.setattr(worker, "alive", lambda *_: True)
    calls = []

    def run(control, document, slot):
        calls.append((control, document, slot))
        return 0

    assert worker.dispatch(tmp_path, 0, run) == 0
    assert calls[0][1:] == (PLAN, PLAN["slots"][0])
    with pytest.raises(FileExistsError):
        worker.dispatch(tmp_path, 0, run)
    assert len(calls) == 1
    with pytest.raises(ValueError):
        worker.dispatch(tmp_path, True, run)


def test_wrong_worker_parent_never_invoked(tmp_path):
    record(tmp_path / "plan.json", PLAN)
    record(tmp_path / "pair_000_started.json", dict(pair=0, plan_sha256=a.PLAN))
    record(tmp_path / "execution_manifest.json", {"fixture": True})
    record(
        tmp_path / "pair_000_owner.json",
        dict(process={"pid": -1}, binding=bind(tmp_path, 0, BINDING)[0]),
    )
    with pytest.raises(ValueError, match="worker_parent"):
        worker.dispatch(tmp_path, 0, lambda *_: pytest.fail("worker called"))


def test_missing_denominator_preserved():
    result = aggregate.summarize(PLAN, [])
    assert result["status"] == "inconclusive"
    assert result["new_slots_without_supported_admission"] == 14
    assert result["per_pulse"]["brake_t0"]["intersection_witness"] == dict(
        true=0, false=0, unknown=0, missing=2
    )


def test_durable_record_refuses_symlink_and_duplicates(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"preserved")
    (tmp_path / "link").symlink_to(target)
    with pytest.raises(FileExistsError):
        record(tmp_path / "link", {})
    assert target.read_bytes() == b"preserved"
    record(tmp_path / "record", {"value": None})
    with pytest.raises(FileExistsError):
        record(tmp_path / "record", {})
    assert json.loads((tmp_path / "record").read_text()) == {"value": None}


@pytest.mark.parametrize("fault", ["id", "deadline", "kill_mode", "invocation", "unavailable"])
def test_service_ownership_and_deadline_rejections(fault):
    import subprocess

    values = dict(
        Id="fixture.service",
        ActiveState="active",
        MainPID="12",
        InvocationID="invocation",
        RuntimeMaxUSec="41min 40s",
        KillMode="control-group",
    )

    def run(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv,
            1 if fault == "unavailable" else 0,
            "\n".join(k + "=" + v for k, v in values.items()),
            "",
        )

    if fault == "id":
        values["Id"] = "other.service"
    if fault == "deadline":
        values["RuntimeMaxUSec"] = "infinity"
    if fault == "kill_mode":
        values["KillMode"] = "process"
    if fault == "invocation":
        values["InvocationID"] = "replacement"
    with pytest.raises((ValueError, OSError)):
        ownership.check_service("fixture.service", "invocation", run=run)


def test_lost_launch_reply_never_reissues_command(tmp_path, monkeypatch):
    import subprocess
    import time
    from experiments.iter152_recovery_continuation import remote_ops as remote
    from experiments.iter150_cloud_observation.native import file

    record(tmp_path / "execution_manifest.json", {"fixture": True})
    envelope = dict(deadline_monotonic=time.monotonic() + 5000, pair_units={"0": "fixture.service"})
    record(tmp_path / "block_000_envelope.json", envelope)
    record(tmp_path / "host_qualification.json", dict(status="supported"))
    permit = dict(
        pair=0,
        block=0,
        envelope_sha256=a.identity(envelope),
        manifest_sha256=file(tmp_path, "execution_manifest.json", 1024)["sha256"],
        plan_sha256=a.PLAN,
    )
    monkeypatch.setattr(remote, "idle", lambda: None)
    launched = []

    def run(argv, **kwargs):
        launched.append(argv)
        raise subprocess.TimeoutExpired(argv, 15)

    monkeypatch.setattr(remote.subprocess, "run", run)
    with pytest.raises(subprocess.TimeoutExpired):
        remote.launch(tmp_path, permit)
    assert read(tmp_path / "pair_000_launch_intent.json")["maximum_launch_commands"] == 1
    with pytest.raises(FileExistsError):
        remote.launch(tmp_path, permit)
    assert len(launched) == 1
    assert "--property=RuntimeMaxSec=2500" in launched[0]
    assert "--property=KillMode=control-group" in launched[0]


@pytest.mark.parametrize("fault", ["path", "symlink", "duplicate", "identity", "collection_budget"])
def test_archive_known_bads(tmp_path, fault):
    import tarfile
    import io
    import hashlib
    from experiments.iter152_recovery_continuation.collection import extract

    archive = tmp_path / "raw.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        item = tarfile.TarInfo("../escape" if fault == "path" else "file")
        item.size = 1
        if fault == "symlink":
            item.type = tarfile.SYMTYPE
            item.linkname = "/etc/passwd"
            item.size = 0
        tar.addfile(item, io.BytesIO(b"x"))
        if fault == "duplicate":
            tar.addfile(item, io.BytesIO(b"x"))
    raw = archive.read_bytes()
    expected = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if fault == "identity":
        expected["sha256"] = "f" * 64
    with pytest.raises(ValueError):
        extract(
            archive,
            tmp_path / "destination",
            expected,
            remaining_bytes=0 if fault == "collection_budget" else 512 * 1024**2,
        )
    assert not (tmp_path / "destination").exists()


def test_raw_commit_precedes_scientific_replay(tmp_path, monkeypatch):
    from experiments.iter152_recovery_continuation import replay

    def absent(*args):
        raise ValueError("raw_not_committed")

    monkeypatch.setattr(replay, "raw_identity", absent)
    monkeypatch.setattr(replay, "pair_reports", lambda *args: pytest.fail("uncommitted replay"))
    with pytest.raises(ValueError, match="raw_not_committed"):
        replay.admit(ROOT, tmp_path, PLAN, 0, "a" * 40, [], tmp_path)


def test_unknown_is_separate_from_unrun_case():
    rows = receipts(3)
    per_comparator = dict(opportunity=True, progress_at_hazard_satisfied=None, witness=None)
    comparison = dict(
        intersection_witness=None,
        action_contrast=True,
        harm_vs_successful_nominal=False,
        nominal=per_comparator,
        monitor=per_comparator,
    )
    rows[-1]["comparisons"] = {"brake_t0": comparison, "brake_t2_5": comparison}
    value = aggregate.summarize(PLAN, rows)
    assert value["per_pulse"]["brake_t0"]["intersection_witness"] == dict(
        true=0, false=0, unknown=1, missing=1
    )
    assert value["admitted_new_slots"] == 6 and value["new_slots_without_supported_admission"] == 8
    assert value["historical_comparator_slots"] == 2


@pytest.mark.parametrize("fault", ["machine", "accelerator", "count"])
def test_provider_shape_before_start(fault):
    from experiments.iter152_recovery_continuation.execute import provider_shape

    value = dict(
        id="3834622546652649531",
        machineType="types/g2-standard-8",
        guestAccelerators=[dict(acceleratorCount=1, acceleratorType="types/nvidia-l4")],
    )
    provider_shape(value)
    if fault == "machine":
        value["machineType"] = "types/g2-standard-16"
    if fault == "accelerator":
        value["guestAccelerators"][0]["acceleratorType"] = "types/other"
    if fault == "count":
        value["guestAccelerators"][0]["acceleratorCount"] = 2
    with pytest.raises(ValueError, match="provider_shape"):
        provider_shape(value)


def test_evidence_git_commit_preserves_captured_whitespace(tmp_path):
    import subprocess
    from experiments.iter152_recovery_continuation.execute import commit

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for key, value in [("user.name", "Fixture"), ("user.email", "fixture@example.invalid")]:
        subprocess.run(["git", "config", key, value], cwd=tmp_path, check=True)
    captured = tmp_path / a.BASE / "proof/raw/e2e.py"
    captured.parent.mkdir(parents=True)
    raw = b"# Immutable captured source  \n\n"
    captured.write_bytes(raw)
    sha = commit(tmp_path, [captured.parent], "Retain fixture bytes")
    assert (
        subprocess.check_output(
            ["git", "show", sha + ":" + captured.relative_to(tmp_path).as_posix()], cwd=tmp_path
        )
        == raw
    )
    # This reproduces why a source whitespace gate was inappropriate here.
    assert (
        subprocess.run(
            ["git", "show", "--check", sha], cwd=tmp_path, capture_output=True
        ).returncode
        != 0
    )
    outside = tmp_path / "authored.py"
    outside.write_text("source\n")
    with pytest.raises(ValueError, match="non_evidence_commit_scope"):
        commit(tmp_path, [outside], "Forbidden scope")
    (captured.parent / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="evidence_symlink"):
        commit(tmp_path, [captured.parent], "Forbidden symlink")


@pytest.mark.parametrize("pair,block", [(0, 0), (2, 0), (3, 1), (6, 1)])
def test_fresh_block_mapping(pair, block):
    from experiments.iter152_recovery_continuation.execute import block_pairs

    assert pair in block_pairs(block)
    assert pair not in block_pairs(1 - block)


@pytest.mark.parametrize("fault", ["anchor", "counted_as_new", "scenario_boundary", "skipped_pair"])
def test_complete_chain_and_historical_anchor(fault):
    rows = receipts(7)
    a.history(PLAN, rows, 7)
    if fault == "anchor":
        rows[0]["historical_comparator_sha256"] = "f" * 64
    if fault == "counted_as_new":
        rows[0]["historical_slots_counted_as_new"] = 2
    if fault == "scenario_boundary":
        rows[6]["scenario_comparison_status"] = "invalid"
    if fault == "skipped_pair":
        rows.pop(3)
    with pytest.raises(ValueError):
        a.history(PLAN, rows, 7)


def test_historical_baseline_independently_replays():
    from experiments.iter152_recovery_continuation.baseline import verify

    reports = verify(ROOT)
    assert [r["steps"] for r in reports] == [31, 31]
    assert [r["outcome"]["first_failure_time"] for r in reports] == [7.75, 7.75]


@pytest.mark.parametrize("fault", ["receipt", "inventory"])
def test_historical_mutations_rejected(tmp_path, monkeypatch, fault):
    from experiments.iter152_recovery_continuation import baseline

    base = tmp_path / a.BASE
    base.mkdir(parents=True)
    record(base / "STUDY_PLAN.json", PLAN)
    binding = PLAN["historical_comparator"]
    target = tmp_path / binding["admission_path"]
    target.parent.mkdir(parents=True)
    data = (ROOT / binding["admission_path"]).read_bytes()
    target.write_bytes(data + (b" " if fault == "receipt" else b""))
    monkeypatch.setattr(baseline, "raw_identity", lambda *args: "f" * 64)
    with pytest.raises(ValueError, match="historical_"):
        baseline.verify(tmp_path)


@pytest.mark.parametrize("field", ["route", "reset_state", "actor_types"])
def test_historical_comparability_faults(field):
    from experiments.iter152_recovery_continuation.baseline import compatible

    original = dict(
        route=[1.0, 2.0],
        reset_state=[0.0, 0.0, 0.0, 1.0, 0.0],
        actor_types={"a": "ConstantPlanner"},
    )
    changed = deepcopy(original)
    changed[field] = {"a": "IDM"} if field == "actor_types" else [999.0]
    with pytest.raises((ValueError, AssertionError)):
        compatible([original, original], [changed, changed])


def test_changed_captured_client_refused(tmp_path):
    from experiments.iter152_recovery_continuation.baseline import client_identity

    (tmp_path / "e2e147.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="historical_client_changed"):
        client_identity(ROOT, tmp_path)


@pytest.mark.parametrize(
    "prior",
    [
        dict(status="failed", termination_verified=True),
        dict(status="supported", termination_verified=False),
    ],
)
def test_second_envelope_requires_successful_closure(tmp_path, monkeypatch, prior):
    from experiments.iter152_recovery_continuation import baseline
    from experiments.iter152_recovery_continuation.execute import execute

    monkeypatch.setattr(baseline, "verify", lambda root: [])
    base = tmp_path / a.BASE / "proof/block_000"
    base.mkdir(parents=True)
    record(base / "result.json", prior)
    with pytest.raises(ValueError, match="previous_block_not_closed"):
        execute(tmp_path, 1, "a" * 40)
    assert not (base.parent / "block_001").exists()
