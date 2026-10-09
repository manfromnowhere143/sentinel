"""Exercise the whole outer sequence and failed boundaries before any provider access."""

import json
from pathlib import Path
import subprocess

import pytest

from experiments.iter142_nominal_continuation_completion import coordinator as c
from experiments.iter142_nominal_continuation_completion.run_episode import retained_reference


class Backend:
    def __init__(self, fail=None, invalid=None):
        self.calls = []
        self.fail = fail
        self.invalid = invalid

    def step(self, name, arm=None):
        self.calls.append((name, arm))
        if self.fail == name:
            raise ValueError("injected " + name)

    def preflight(self, branch, source):
        self.step("preflight")
        if branch != c.BRANCH:
            raise ValueError("wrong branch")

    def launch(self, arm):
        self.step("launch", arm)

    def wait(self, arm):
        self.step("wait", arm)
        return {"returncode": 1 if self.invalid == "episode" else 0}

    def collect(self, arm):
        self.step("collect", arm)

    def commit(self, arm):
        self.step("commit", arm)
        return "wrong" if self.invalid == "commit" else str(c.ARMS.index(arm) + 1) * 40

    def check_commit(self, commit, arm):
        self.step("check_commit", arm)

    def verify(self, arm):
        self.step("verify", arm)
        if self.invalid == "verify":
            return None
        return dict(
            status="validated",
            verdict="REPLAY_MATCHED",
            prefix="matched",
            nominal_replica={"prefix": "matched"},
        )


def test_entire_sequence_and_raw_before_verification(tmp_path):
    b = Backend()
    reports = c.run_schedule(tmp_path, "a" * 40, b)
    assert list(reports) == list(c.ARMS)
    assert b.calls == [("preflight", None)] + [
        (step, arm)
        for arm in c.ARMS
        for step in ["launch", "wait", "collect", "commit", "check_commit", "verify"]
    ]
    events = [json.loads(x) for x in (tmp_path / "events.jsonl").read_text().splitlines()]
    for arm in c.ARMS:
        own = [e for e in events if e.get("arm") == arm]
        assert [e["kind"] for e in own] == ["launch_requested", "raw_committed", "validated"]
        assert own[1]["raw_commit"] == str(c.ARMS.index(arm) + 1) * 40
    assert events[-1]["kind"] == "schedule_complete"


@pytest.mark.parametrize(
    "stage", ["preflight", "launch", "wait", "collect", "commit", "check_commit", "verify"]
)
def test_failure_stops_later_arms(tmp_path, stage):
    b = Backend(fail=stage)
    with pytest.raises(ValueError, match="injected"):
        c.run_schedule(tmp_path, "a" * 40, b)
    assert not any(arm in ("nominal_a", "nominal_b") for _, arm in b.calls)
    if stage != "preflight":
        assert (
            json.loads((tmp_path / "events.jsonl").read_text().splitlines()[-1])["kind"] == "failed"
        )


@pytest.mark.parametrize("invalid", ["episode", "commit", "verify"])
def test_invalid_return_stops_and_preserves_marker(tmp_path, invalid):
    b = Backend(invalid=invalid)
    with pytest.raises(ValueError):
        c.run_schedule(tmp_path, "a" * 40, b)
    assert (tmp_path / "schedule_started.json").exists()
    assert not any(arm == "nominal_a" for _, arm in b.calls)
    if invalid == "episode":
        assert ("collect", "reference_b") in b.calls and ("commit", "reference_b") in b.calls
        assert ("verify", "reference_b") not in b.calls


def test_no_schedule_restart(tmp_path):
    c.run_schedule(tmp_path, "a" * 40, Backend())
    b = Backend()
    with pytest.raises(FileExistsError):
        c.run_schedule(tmp_path, "a" * 40, b)
    assert b.calls == [("preflight", None)]


def test_bad_branch_rejected_before_start(tmp_path):
    b = Backend()
    with pytest.raises(ValueError, match="wrong branch"):
        c.run_schedule(tmp_path, "a" * 40, b, "research/iter142-finite-pulse")
    assert b.calls == [("preflight", None)] and not (tmp_path / "schedule_started.json").exists()


def test_actual_candidate_ref_and_known_bad():
    repo = Path(__file__).resolve().parents[1]
    source = (
        subprocess.check_output(["git", "rev-parse", "refs/heads/" + c.BRANCH], cwd=repo)
        .decode()
        .strip()
    )
    assert c.candidate(repo, c.BRANCH, source) == source
    with pytest.raises(subprocess.CalledProcessError):
        c.candidate(repo, "research/iter142-finite-pulse", source)


@pytest.mark.parametrize(
    "arm,bad",
    [
        ("reference_b", {"status": "validated", "verdict": "REPLAY_DIVERGED"}),
        ("nominal_a", {"status": "validated", "prefix": "unobserved"}),
        ("nominal_b", {"status": "validated", "prefix": "matched"}),
    ],
)
def test_admission_known_bads(arm, bad):
    with pytest.raises(ValueError):
        c.admitted(arm, bad)


def test_retained_reference_bound_and_corruption(tmp_path):
    packet = tmp_path / "packet"
    root = packet / "experiments/iter142_nominal_continuation_completion"
    root.mkdir(parents=True)
    source = (
        Path(__file__).resolve().parents[1]
        / "experiments/iter142_nominal_continuation_completion/INPUTS.json"
    )
    manifest = json.loads(source.read_text())
    repo = Path(__file__).resolve().parents[1]
    for name in manifest["files"]:
        p = packet / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((repo / name).read_bytes())
    (root / "INPUTS.json").write_bytes(source.read_bytes())
    retained_reference(tmp_path)
    p = packet / next(iter(manifest["files"]))
    p.write_bytes(p.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="runtime file mismatch"):
        retained_reference(tmp_path)


def test_committed_raw_identity_and_known_bads():
    import os

    repo = Path(os.environ.get("SENTINEL_TEST_REPOSITORY", Path(__file__).resolve().parents[1]))
    base = "experiments/iter141_nominal_continuation/proof/live/reference_a"
    records = json.loads((repo / base / "remote_inventory.json").read_text())["retained"]
    commit = "888a8a3c86f327de15612d5b7a8553e66b43805f"
    c.committed_files(repo, commit, base, records)
    bad = json.loads(json.dumps(records))
    bad[next(iter(bad))]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="content mismatch"):
        c.committed_files(repo, commit, base, bad)
    with pytest.raises(ValueError, match="identity"):
        c.committed_files(repo, "bad", base, records)
    with pytest.raises(ValueError, match="empty"):
        c.committed_files(repo, commit, base, {})
