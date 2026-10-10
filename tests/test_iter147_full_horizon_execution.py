from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from experiments.iter147_full_horizon_execution.protocol import plan, validate, identity
from experiments.iter147_full_horizon_execution.coordinator import claim
from experiments.iter147_full_horizon_execution.resources import guard, CASE_STOP
from experiments.iter147_full_horizon_execution.fixtures import execute
from experiments.iter147_full_horizon_execution.monitor import replay
from experiments.iter146_route_outcome_contract.check import verify, read
from experiments.iter147_full_horizon_execution.client import instrument

ROOT = Path(__file__).resolve().parents[1]


def test_fixed_study_and_qualification_populations():
    s = plan(ROOT, "study")
    q = plan(ROOT, "qualification")
    assert len(s["slots"]) == 112 and len(q["slots"]) == 8
    assert q["host_seconds"] == 10800 and q["compute_cap_usd"] == 9
    assert all(x["probe"] == "none" for x in s["slots"])
    assert {x["arm"] for x in s["slots"]} == {"nominal", "monitor", "brake_t0", "brake_t2_5"}
    validate(ROOT, s)
    validate(ROOT, q)


@pytest.mark.parametrize(
    "change", ["drop", "reorder", "seed", "horizon", "probe", "budget", "retry"]
)
def test_changed_population_rejected(change):
    q = plan(ROOT, "qualification")
    if change == "drop":
        q["slots"].pop()
    elif change == "reorder":
        q["slots"].reverse()
    elif change == "seed":
        q["slots"][0]["seed"] = 145
    elif change == "horizon":
        q["slots"][0]["max_actions"] = 12
    elif change == "probe":
        q["slots"][2]["probe"] = "monitor_hold"
    elif change == "budget":
        q["host_seconds"] += 1
    else:
        q["initialized_retry"] = True
    with pytest.raises(ValueError, match="frozen_plan"):
        validate(ROOT, q)


def test_no_initialized_retry_skip_or_unverified_later_pair(tmp_path):
    q = plan(ROOT, "qualification")
    claim(ROOT, tmp_path, q, 0)
    with pytest.raises(FileExistsError):
        claim(ROOT, tmp_path, q, 0)
    with pytest.raises(ValueError, match="not_admitted"):
        claim(ROOT, tmp_path, q, 1)
    previous = dict(
        status="supported",
        pair=0,
        plan_sha256=identity(q),
        raw_commit="a" * 40,
        raw_inventory_sha256="b" * 64,
    )
    assert claim(ROOT, tmp_path, q, 1, previous) == q["slots"][2:4]
    with pytest.raises(ValueError, match="not_admitted"):
        claim(ROOT, tmp_path, q, 3, previous)


@pytest.mark.parametrize("field", ["status", "plan_sha256", "raw_commit", "raw_inventory_sha256"])
def test_bad_previous_receipt(tmp_path, field):
    q = plan(ROOT, "qualification")
    p = dict(
        status="supported",
        pair=0,
        plan_sha256=identity(q),
        raw_commit="a" * 40,
        raw_inventory_sha256="b" * 64,
    )
    p[field] = "wrong"
    with pytest.raises(ValueError):
        claim(ROOT, tmp_path, q, 1, p)


def test_parent_log_and_every_owned_output_counted(tmp_path):
    case = tmp_path / "runs" / "case"
    case.mkdir(parents=True)
    log = case / "parent.log"
    log.write_bytes(b"1234")

    def free(p):
        return SimpleNamespace(free=100 * 1024**3)

    assert guard(tmp_path, case, 8, usage=free) == dict(case_bytes=4, total_owned_bytes=4)
    with log.open("wb") as f:
        f.truncate(CASE_STOP)
    with pytest.raises(ValueError, match="output_limit"):
        guard(tmp_path, case, 8, usage=free)
    log.unlink()
    (tmp_path / "alias").symlink_to("/tmp")
    with pytest.raises(ValueError, match="entry_type"):
        guard(tmp_path, case, 8, usage=free)


@pytest.fixture(scope="module")
def monitor_fixture(tmp_path_factory):
    output = tmp_path_factory.mktemp("monitor147") / "release"
    summary = execute(ROOT, output, mode="release", max_actions=12)
    assert summary["status"] == "completed", summary
    verified = verify(*read(output / "trace"))
    assert verified["steps"] == 12
    rows = [
        json.loads(line)
        for line in (output / "sentinel_iter48_decisions.jsonl").read_text().splitlines()
    ]
    return rows


def test_real_monitor_latch_and_release(monitor_fixture):
    r = replay(monitor_fixture)
    assert r["firings"] == 2 and r["braking_frames"] == 5 and r["releases"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("fired", False),
        ("brake", False),
        ("pre_braking", True),
        ("post_clear", 4),
        ("min_cpa", 10.0),
        ("min_ttc", 0.1),
    ],
)
def test_monitor_known_bads(monitor_fixture, field, value):
    rows = deepcopy(monitor_fixture)
    rows[0][field] = value
    with pytest.raises(ValueError):
        replay(rows)


def test_exact_client_import_delta():
    raw = (
        ROOT / "experiments/iter145_constrained_execution/source/released_client.py.txt"
    ).read_bytes()
    out = instrument(raw)
    assert b"from experiments.iter147_full_horizon_execution.client import deliver" in out
    assert b"results = model(" in out
    with pytest.raises(ValueError):
        instrument(raw + b"\n")


def test_raw_gate_requires_exact_committed_bytes(tmp_path):
    import subprocess
    from experiments.iter147_full_horizon_execution.coordinator import raw_identity

    repo = tmp_path / "repository"
    repo.mkdir()
    raw = repo / "raw"
    raw.mkdir()
    p = raw / "record.json"
    p.write_text('{"observed":null}\n')

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, stderr=subprocess.DEVNULL)

    git("init")
    git("add", "raw")
    git(
        "-c",
        "user.name=Daniel Wahnich",
        "-c",
        "user.email=cogitoergosum143@gmail.com",
        "commit",
        "-m",
        "Known-good raw fixture",
    )
    commit = git("rev-parse", "HEAD").decode().strip()
    assert len(raw_identity(repo, commit, raw)) == 64
    p.write_text('{"observed":0}\n')
    with pytest.raises(ValueError, match="not_committed"):
        raw_identity(repo, commit, raw)
    p.unlink()
    p.symlink_to(repo / "outside")
    with pytest.raises(ValueError, match="symlink"):
        raw_identity(repo, commit, raw)


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "slot",
        "purpose",
        "timing",
        "horizon",
        "actor",
        "injection",
        "accepted",
        "censor",
        "natural_injection",
    ],
)
def test_gpu_slot_and_injection_known_bads(tmp_path, monkeypatch, mutation):
    """Synthetic boundary receipts; the base CUDA checker is deliberately stubbed here."""
    from experiments.iter147_full_horizon_execution import gpu_check

    q = plan(ROOT, "qualification")
    slot = q["slots"][0]
    source = ROOT / "experiments/iter147_full_horizon_execution/proof/cpu_raw/hold__1"
    summary = json.loads((source / "trace/summary.json").read_text())
    worker = dict(slot=slot, purpose="qualification", summary=summary, actor_types={})
    report = dict(episode=slot["id"], arm="monitor", steps=401, outcome=dict(censored=True))
    monitor = [
        json.loads(line)
        for line in (source / "sentinel_iter48_decisions.jsonl").read_text().splitlines()
    ]
    injected = [
        dict(
            frame=i,
            time=i / 4,
            kind="injected_detector_input_not_natural_perception",
            center=r["traj"][0] + [0.0],
            score=1.0,
            track_id=147,
            original_model_detection_count=0,
        )
        for i, r in enumerate(monitor)
    ]
    if mutation == "slot":
        worker["slot"] = dict(slot, seed=145)
    elif mutation == "purpose":
        worker["purpose"] = "study"
    elif mutation == "timing":
        summary["schema"] = "sentinel.iter146.summary.v1"
    elif mutation == "horizon":
        summary["max_actions"] = 24
    elif mutation == "actor":
        worker["actor_types"] = {"x": "IDM"}
    elif mutation == "injection":
        injected[0]["kind"] = "natural"
    elif mutation == "accepted":
        monitor[0]["objs"][0]["id"] = 100
    elif mutation == "censor":
        report["outcome"]["censored"] = False
    elif mutation == "natural_injection":
        slot = q["slots"][2]
        worker["slot"] = slot
        worker["actor_types"] = {"x": "AttackPlanner"}
        report.update(episode=slot["id"], arm=slot["arm"])
    monkeypatch.setattr(gpu_check, "prior_verify", lambda path: report)
    (tmp_path / "worker.json").write_text(json.dumps(worker))
    (tmp_path / "sentinel_iter48_decisions.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in monitor)
    )
    (tmp_path / "diagnostic_inputs.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in injected)
    )
    if mutation is None:
        assert gpu_check.verify_case(tmp_path, slot, "qualification")["monitor"]["firings"] == 401
    else:
        with pytest.raises(ValueError):
            gpu_check.verify_case(tmp_path, slot, "qualification")
