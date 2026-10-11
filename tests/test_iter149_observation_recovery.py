"""Faults at the observation/execution boundary, including real owned subprocess expiry."""

from copy import deepcopy
import json
import os
import subprocess
import sys
import time

import pytest

from experiments.iter149_observation_recovery import local_host
from experiments.iter149_observation_recovery.qualify import BINDING, CASES, qualify, run
from experiments.iter149_observation_recovery.recovery import (
    Limits,
    closure,
    decode,
    encode,
    reconcile,
)
from experiments.iter149_observation_recovery.replay import check


@pytest.mark.parametrize("name", CASES)
def test_fault_matrix(name):
    sequence, expected = CASES[name]
    limits = Limits(deadline=5) if name == "budget_exhaustion" else Limits(deadline=30)
    trace = run(sequence, limits)
    assert trace["reason"] == expected
    assert check(trace)["status"] == "supported"
    assert trace["scientific_admission"] is False
    if name in {"temporary_disconnection", "completion_during_disconnection"}:
        assert any(e["state"] == "observation_unavailable" for e in trace["events"])


def test_retained_exhaustive_qualification(tmp_path):
    report = qualify(tmp_path / "qualification")
    assert report["exhaustive_sequences"] == 1296
    assert len(report["checker_known_bads"]) == 12


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0, True])
def test_invalid_budgets(value):
    with pytest.raises(ValueError):
        Limits(deadline=value).validate()


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b"{} ", b"[]" * 4097])
def test_strict_encoding(raw):
    with pytest.raises(ValueError):
        decode(raw)


def test_closure_does_not_infer_success_from_command_or_wrong_identity():
    assert closure(BINDING, None) == "unknown"
    assert closure(BINDING, {"returncode": 0}) == "unknown"
    stale = deepcopy(BINDING)
    stale["vm_start"] = "replacement"
    assert closure(BINDING, {"binding": stale, "status": "terminated"}) == "unknown"
    assert closure(BINDING, {"binding": BINDING, "status": "running"}) == "unknown"
    assert closure(BINDING, {"binding": BINDING, "status": "terminated"}) == "verified"


def test_no_follow_or_unbounded_file_reads(tmp_path):
    (tmp_path / "target").write_bytes(b"abc")
    (tmp_path / "link").symlink_to(tmp_path / "target")
    with pytest.raises(OSError):
        local_host.read(tmp_path, "link")
    with pytest.raises(ValueError):
        local_host.read(tmp_path, "target", limit=2)
    with pytest.raises(ValueError):
        local_host.read(tmp_path, "../target")
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(ValueError):
        local_host.read(tmp_path, "pipe")


def test_completion_at_deadline_is_not_admitted():
    trace = run(["complete"], Limits(deadline=0.125))
    assert trace["reason"] == "deadline"
    assert trace["worker_complete"] is False


def test_recovery_does_not_replenish_total_reads():
    trace = run(
        ["disconnect", "running", "disconnect", "complete"], Limits(deadline=30, max_reads=3)
    )
    assert trace["reason"] == "read_limit"
    assert len(trace["events"]) == 3


@pytest.mark.parametrize("mode", ["complete", "crash", "disconnected"])
def test_real_host_is_independent_of_observer(tmp_path, mode):
    root = tmp_path / "owned"
    argv = [
        sys.executable,
        "-m",
        "experiments.iter149_observation_recovery.local_host",
        "host",
        str(root),
        "10" if mode == "disconnected" else "0.25",
        "--budget",
        "1.5",
    ]
    if mode == "crash":
        argv.append("--crash")
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise
    assert process.returncode == 0, (stdout, stderr)
    binding = json.loads((root / "binding.json").read_bytes())
    marker = (root / "initialized.json").read_bytes()
    raw = (root / "raw.json").read_bytes()
    receipt = json.loads((root / "closure.json").read_bytes())
    assert closure(binding, receipt) == "verified"
    assert receipt["elapsed"] < 5
    assert receipt["partial_raw_preserved"] is True and raw
    second = subprocess.run(argv, capture_output=True, timeout=5)
    assert second.returncode != 0
    assert (root / "initialized.json").read_bytes() == marker
    assert (root / "raw.json").read_bytes() == raw
    assert json.loads((root / "launch.json").read_bytes())["initializations"] == 1
    if mode == "disconnected":
        assert receipt["deadline_fired"] is True
        assert receipt["returncode"] == -9
        assert json.loads((root / "snapshot.json").read_bytes())["state"] == "partial"
    else:
        trace = reconcile(
            binding,
            Limits(deadline=time.monotonic() + 2),
            "reconnect",
            lambda request, timeout: local_host.observe(root, request, timeout),
            time.monotonic,
            time.sleep,
        )
        assert check(trace)["status"] == "supported"
        assert trace["reason"] == ("worker_failed" if mode == "crash" else "worker_complete")
    assert encode(json.loads(marker)) == marker


def test_typed_closure_identity():
    false_pair = deepcopy(BINDING)
    false_pair["pair"] = False
    assert closure(BINDING, {"binding": false_pair, "status": "terminated"}) == "unknown"


@pytest.mark.parametrize("field", ["attempt", "worker_complete"])
def test_checker_rejects_boolean_integer_aliases(field):
    trace = run(["running", "complete"])
    if field == "attempt":
        trace["events"][0]["attempt"] = False
    else:
        trace[field] = 1
    with pytest.raises(ValueError):
        check(trace)


def test_local_partial_snapshot_is_unavailable(tmp_path):
    (tmp_path / "snapshot.json").write_bytes(b'{"state":')
    with pytest.raises(OSError):
        local_host.observe(tmp_path, "request", 1)
