from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from experiments.iter149_observation_recovery.qualify import BINDING
from experiments.iter149_observation_recovery.recovery import classify, encode
from experiments.iter150_cloud_observation import native
from experiments.iter150_cloud_observation.check import verify

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "experiments/iter148_recovery_study/proof/study_raw"


def binding(root, pair=0):
    return native.bind(root, pair, BINDING)[0]


@pytest.mark.parametrize("pair", [0, 1])
def test_actual_completed_native_pairs(pair):
    root = RAW / f"pair_{pair:03d}"
    expected = binding(root, pair)
    raw, blobs = native.observe(root, pair, expected, expected, "fresh/0")
    assert classify(raw, blobs, "fresh/0", expected, -1, None)[0] == "worker_complete"
    report = verify(root, blobs, expected)
    assert report["files"] == 16
    assert report["bytes"] > 1024**2
    assert len(blobs["raw"]) < 65536


def test_original_partial_pair_stays_partial():
    root = RAW / "pair_002"
    expected = binding(root, 2)
    raw, blobs = native.observe(root, 2, expected, expected, "fresh/0")
    assert classify(raw, blobs, "fresh/0", expected, -1, None)[0] == "partial_evidence"


@pytest.mark.parametrize("field", ["source_sha256", "plan_sha256", "initialization_sha256"])
def test_independent_checker_reconstructs_native_identity(field):
    root = RAW / "pair_000"
    expected = binding(root)
    _, blobs = native.observe(root, 0, expected, expected, "fresh/0")
    forged = dict(expected, **{field: "f" * 64})
    with pytest.raises(ValueError, match="native_identity"):
        verify(root, blobs, forged)


@pytest.fixture
def copied(tmp_path):
    return Path(shutil.copytree(RAW / "pair_000", tmp_path / "native"))


@pytest.mark.parametrize(
    "fault",
    [
        "parent_slot",
        "parent_returncode",
        "parent_deadline",
        "parent_cleanup",
        "worker_status",
        "summary_disagrees",
        "event_changed",
        "missing_worker",
        "symlink_trace",
        "symlink_directory",
        "duplicate_json",
    ],
)
def test_native_corruptions_never_complete(copied, fault):
    expected = binding(copied)
    slot = json.loads((copied / "plan.json").read_text())["slots"][0]["id"]
    run = copied / "runs" / slot
    if fault.startswith("parent_"):
        path = copied / "pair_000_result.json"
        value = json.loads(path.read_text())
        field = fault.removeprefix("parent_")
        value["cases"][0][{"deadline": "deadline_exceeded"}.get(field, field)] = {
            "slot": {},
            "returncode": True,
            "deadline": True,
            "cleanup": {"status": "running"},
        }[field]
        path.write_text(json.dumps(value))
    elif fault == "worker_status":
        path = run / "worker.json"
        value = json.loads(path.read_text())
        value["status"] = "failed"
        path.write_text(json.dumps(value))
    elif fault == "summary_disagrees":
        path = run / "trace/summary.json"
        value = json.loads(path.read_text())
        value["steps"] += 1
        path.write_text(json.dumps(value))
    elif fault == "event_changed":
        with (run / "trace/events.jsonl").open("ab") as f:
            f.write(b"changed")
    elif fault == "missing_worker":
        (run / "worker.json").unlink()
    elif fault == "symlink_trace":
        path = run / "trace/events.jsonl"
        other = run / "saved"
        path.rename(other)
        path.symlink_to(other)
    elif fault == "symlink_directory":
        path = run / "trace"
        other = run / "saved"
        path.rename(other)
        path.symlink_to(other)
    elif fault == "duplicate_json":
        (run / "worker.json").write_text('{"status":"completed","status":"completed"}')
    raw, blobs = native.observe(copied, 0, expected, expected, "fresh/0")
    assert classify(raw, blobs, "fresh/0", expected, -1, None)[0] == "partial_evidence"


@pytest.mark.parametrize(
    "field",
    [
        "vm_id",
        "vm_start",
        "host_boot",
        "host_deadline_id",
        "source_sha256",
        "plan_sha256",
        "initialization_sha256",
    ],
)
def test_identity_changes_stop_reconciliation(field):
    root = RAW / "pair_000"
    actual = binding(root)
    expected = deepcopy(actual)
    expected[field] = "9" * 64 if field.endswith("sha256") else "wrong"
    raw, blobs = native.observe(root, 0, actual, expected, "fresh/0")
    assert classify(raw, blobs, "fresh/0", expected, -1, None)[0] == "identity_mismatch"


def test_streaming_size_and_path_bounds(tmp_path):
    path = tmp_path / "large"
    path.write_bytes(b"x" * 1025)
    with pytest.raises(native.EvidenceError):
        native.file(tmp_path, "large", 1024)
    with pytest.raises(native.EvidenceError):
        native.file(tmp_path, "../large", 2048)


def test_checker_rejects_changed_manifest():
    root = RAW / "pair_000"
    expected = binding(root)
    _, blobs = native.observe(root, 0, expected, expected, "fresh/0")
    manifest = json.loads(blobs["raw"])
    manifest["files"].pop("plan.json")
    blobs["raw"] = encode(manifest)
    with pytest.raises(ValueError):
        verify(root, blobs, expected)


@pytest.mark.parametrize("changed", ["id", "lastStartTimestamp", "status"])
def test_provider_identity_gate(changed):
    from experiments.iter150_cloud_observation.cloud import same_start, VM_ID

    expected = {"id": VM_ID, "lastStartTimestamp": "owned", "status": "RUNNING"}
    actual = dict(expected)
    actual[changed] = "wrong"
    with pytest.raises(ValueError):
        same_start(actual, expected, running=True)


def test_wrong_start_never_calls_stop(tmp_path):
    import subprocess
    from experiments.iter150_cloud_observation.cloud import Cloud, VM_ID

    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(
            argv,
            0,
            json.dumps(
                {"id": VM_ID, "lastStartTimestamp": "replacement", "status": "RUNNING"}
            ).encode(),
            b"",
        )

    cloud = Cloud(tmp_path, runner=runner)
    with pytest.raises(ValueError):
        cloud.stop("wrong", {"id": VM_ID, "lastStartTimestamp": "owned"})
    assert len(calls) == 1 and "stop" not in calls[0]


def test_stop_command_success_is_not_termination(tmp_path):
    import subprocess
    from experiments.iter150_cloud_observation.cloud import Cloud, VM_ID

    expected = {"id": VM_ID, "lastStartTimestamp": "owned", "status": "RUNNING"}

    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, json.dumps(expected).encode(), b"")

    with pytest.raises(OSError):
        Cloud(tmp_path, runner=runner).stop("unclosed", expected)


def test_streaming_detects_change(tmp_path, monkeypatch):
    path = tmp_path / "changing"
    path.write_bytes(b"initial")
    original = native.os.read
    changed = [False]

    def read_then_change(fd, size):
        data = original(fd, size)
        if data and not changed[0]:
            changed[0] = True
            with path.open("ab") as stream:
                stream.write(b"new")
        return data

    monkeypatch.setattr(native.os, "read", read_then_change)
    with pytest.raises(native.EvidenceError):
        native.file(tmp_path, "changing", 1024)


def test_lost_start_reply_reconciles_without_new_start(tmp_path):
    from experiments.iter150_cloud_observation.cloud import recover_start, VM_ID

    prior = {"id": VM_ID, "status": "TERMINATED", "lastStartTimestamp": "old"}
    (tmp_path / "start_intent.json").write_text(
        json.dumps({"before": prior, "maximum_start_commands": 1})
    )

    class Provider:
        def identity(self, label):
            return {"id": VM_ID, "status": "RUNNING", "lastStartTimestamp": "fresh"}

    assert recover_start(Provider(), tmp_path, "reconcile")["lastStartTimestamp"] == "fresh"

    class StaleProvider:
        def identity(self, label):
            return prior

    with pytest.raises(ValueError):
        recover_start(StaleProvider(), tmp_path, "stale")


def test_command_receipt_cannot_collide_with_domain_report(tmp_path):
    import subprocess
    from experiments.iter150_cloud_observation.cloud import Cloud, write

    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, b'{"status":"supported"}', b"")

    cloud = Cloud(tmp_path, runner=runner)
    cloud.run("postflight", ["fixture"])
    write(tmp_path / "postflight.json", {"status": "supported"})
    assert json.loads((tmp_path / "commands/postflight.json").read_text())["returncode"] == 0
    assert json.loads((tmp_path / "postflight.json").read_text())["status"] == "supported"
    with pytest.raises(ValueError):
        cloud.run("postflight", ["fixture"])


@pytest.mark.parametrize("label", ["../escape", "postflight.json", ""])
def test_command_label_stays_in_its_namespace(tmp_path, label):
    from experiments.iter150_cloud_observation.cloud import Cloud

    with pytest.raises(ValueError):
        Cloud(tmp_path).run(label, ["never-executed"])
