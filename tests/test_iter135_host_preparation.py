from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO
    / "experiments/iter135_neuroncap_blind_braking_dose_response/prepare_host135.py"
)
SPEC = importlib.util.spec_from_file_location("iter135_host_preparation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare
SPEC.loader.exec_module(prepare)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


WORKFLOW_RUN_ID = 7_310
CHECK_SUITE_ID = 8_310


def github_timestamp(minute: int) -> str:
    value = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc) + timedelta(
        minutes=minute
    )
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def workflow_run_row(
    commit: str,
    *,
    run_id: int = WORKFLOW_RUN_ID,
    suite_id: int = CHECK_SUITE_ID,
    run_number: int = 731,
    run_attempt: int = 1,
    minute: int = 0,
    branch: str = "master",
    event: str = "push",
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict[str, Any]:
    run_url = f"{prepare.GITHUB_API_ROOT}/actions/runs/{run_id}"
    return {
        "id": run_id,
        "check_suite_id": suite_id,
        "workflow_id": prepare.GITHUB_WORKFLOW_ID,
        "name": prepare.GITHUB_WORKFLOW_NAME,
        "path": prepare.GITHUB_WORKFLOW_PATH,
        "head_branch": branch,
        "head_sha": commit,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "run_number": run_number,
        "run_attempt": run_attempt,
        "created_at": github_timestamp(minute),
        "run_started_at": (
            github_timestamp(minute + 1) if status != "queued" else None
        ),
        "updated_at": github_timestamp(minute + 30),
        "url": run_url,
        "jobs_url": f"{run_url}/jobs",
    }


def workflow_document(
    commit: str, rows: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    selected = rows or [workflow_run_row(commit)]
    return {"total_count": len(selected), "workflow_runs": selected}


def job_document(
    commit: str,
    *,
    run_id: int = WORKFLOW_RUN_ID,
    ids: tuple[int, int] = (310, 311),
    names: tuple[str, ...] = prepare.REQUIRED_GITHUB_CHECKS,
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict[str, Any]:
    rows = []
    for index, (name, check_id) in enumerate(zip(names, ids, strict=False)):
        rows.append(
            {
                "name": name,
                "id": check_id,
                "run_id": run_id,
                "run_attempt": 1,
                "head_sha": commit,
                "head_branch": prepare.GITHUB_BRANCH,
                "workflow_name": prepare.GITHUB_WORKFLOW_NAME,
                "status": status,
                "conclusion": conclusion,
                "started_at": github_timestamp(10 + index),
                "completed_at": github_timestamp(11 + index),
                "url": f"{prepare.GITHUB_API_ROOT}/actions/jobs/{check_id}",
                "run_url": f"{prepare.GITHUB_API_ROOT}/actions/runs/{run_id}",
                "check_run_url": f"{prepare.GITHUB_API_ROOT}/check-runs/{check_id}",
            }
        )
    return {"total_count": len(rows), "jobs": rows}


@pytest.mark.parametrize("payload", [b"", b"payload\n", bytes(range(256))])
def test_git_blob_oid_matches_git_hash_object(payload: bytes) -> None:
    expected = subprocess.run(
        ["git", "hash-object", "--stdin"],
        input=payload,
        check=True,
        capture_output=True,
    ).stdout.decode().strip()

    assert prepare._git_blob_oid(payload) == expected


def nul(rows: list[str]) -> bytes:
    return b"" if not rows else b"\0".join(row.encode() for row in rows) + b"\0"


class FakeRunner:
    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture
        self.calls: list[tuple[str, ...]] = []
        self.staged: dict[str, list[str]] = {"uniad": [], "neuroncap": [], "neurad": []}

    def __call__(self, argv: list[str] | tuple[str, ...]) -> bytes:
        command = tuple(argv)
        self.calls.append(command)
        if command[0] == "/usr/bin/findmnt":
            return json.dumps({"filesystems": [self.fixture["mount"]]}).encode()
        assert command[0] == "/usr/bin/git"
        repo = Path(command[command.index("-C") + 1])
        args = command[command.index("-C") + 2 :]
        repo_id = self.fixture["repo_ids"][repo]
        if args == ("rev-parse", "HEAD"):
            return f"{self.fixture['heads'][repo_id]}\n".encode()
        if args == ("diff", "--cached", "--name-only", "-z"):
            return nul(self.staged[repo_id])
        if args == ("diff", "--name-only", "-z"):
            if repo_id == "uniad":
                server = self.fixture["server"].read_bytes()
                rows = ["projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"]
                if server != self.fixture["baseline"]:
                    rows.insert(0, "inference/server.py")
                return nul(rows)
            if repo_id == "neuroncap":
                return nul(["docker/Dockerfile", "scripts/_docker_compose_release.sh"])
            return nul(["Dockerfile"])
        if args == ("ls-files", "--others", "--exclude-standard", "-z"):
            if repo_id == "neurad":
                return nul(["Dockerfile.bak"])
            if repo_id == "uniad":
                # The real host keeps the load-bearing `checkpoints` -> `ckpts` symlink untracked.
                return nul(
                    list(
                        self.fixture.get(
                            "uniad_untracked", prepare.UNIAD_REQUIRED_UNTRACKED
                        )
                    )
                )
            return nul([])
        if args == ("show", "HEAD:inference/server.py") and repo_id == "uniad":
            return self.fixture["baseline"]
        raise AssertionError(f"unexpected command: {command}")


class FakeGitHub:
    def __init__(
        self,
        source_commit: str,
        artifacts: dict[str, tuple[bytes, str]],
    ) -> None:
        self.source_commit = source_commit
        self.branch_head = source_commit
        self.branch_heads: list[str] = []
        self.status = "completed"
        self.conclusion = "success"
        self.names = list(prepare.REQUIRED_GITHUB_CHECKS)
        self.workflow_documents: list[dict[str, Any]] = []
        self.check_documents: list[dict[str, Any]] = []
        self.tree_sha = "e" * 40
        self.commit_sha = source_commit
        self.commit_tree_sha = self.tree_sha
        self.tree_document_sha = self.tree_sha
        self.tree_truncated = False
        self.tree_rows: list[dict[str, Any]] = []
        for path, (payload, mode) in sorted(artifacts.items()):
            blob_sha = prepare._git_blob_oid(payload)
            self.tree_rows.append(
                {
                    "path": path,
                    "mode": mode,
                    "type": "blob",
                    "sha": blob_sha,
                    "size": len(payload),
                }
            )
        self.calls: list[str] = []

    def __call__(self, url: str) -> dict[str, Any]:
        self.calls.append(url)
        if "/branches/master" in url:
            head = self.branch_heads.pop(0) if self.branch_heads else self.branch_head
            return {"name": "master", "commit": {"sha": head}}
        if "/actions/workflows/" in url:
            if self.workflow_documents:
                return self.workflow_documents.pop(0)
            return workflow_document(self.source_commit)
        if "/actions/runs/" in url and "/jobs?" in url:
            if self.check_documents:
                return self.check_documents.pop(0)
            return job_document(
                self.source_commit,
                names=tuple(self.names),
                ids=tuple(310 + index for index in range(len(self.names))),
                status=self.status,
                conclusion=self.conclusion,
            )
        if "/git/commits/" in url:
            return {"sha": self.commit_sha, "tree": {"sha": self.commit_tree_sha}}
        if "/git/trees/" in url:
            return {
                "sha": self.tree_document_sha,
                "truncated": self.tree_truncated,
                "tree": list(self.tree_rows),
            }
        raise AssertionError(f"unexpected GitHub URL: {url}")


def check_document(
    commit: str,
    *,
    ids: tuple[int, int] = (310, 311),
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict[str, Any]:
    return job_document(
        commit,
        ids=ids,
        status=status,
        conclusion=conclusion,
    )


@pytest.mark.parametrize(
    ("final_url", "content_type", "problem"),
    [
        (
            "https://api.github.com/repos/manfromnowhere143/sentinel/redirected",
            "application/json",
            "publication-authority:redirect",
        ),
        (
            None,
            "text/html",
            "publication-authority:content-type",
        ),
    ],
)
def test_github_transport_rejects_redirect_and_non_json(
    monkeypatch: pytest.MonkeyPatch,
    final_url: str | None,
    content_type: str,
    problem: str,
) -> None:
    requested = f"{prepare.GITHUB_API_ROOT}/branches/master"

    class Headers(dict):
        def get_content_type(self):
            return content_type

    class Response:
        status = 200
        headers = Headers({"Content-Length": "2"})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return final_url or requested

        def read(self, _limit):
            return b"{}"

    handlers = []

    class Opener:
        def open(self, _request, timeout):
            assert timeout == 15
            return Response()

    def build_opener(*items):
        handlers.extend(items)
        return Opener()

    monkeypatch.setattr(prepare.urllib.request, "build_opener", build_opener)

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare._fetch_json(requested)
    assert any(
        isinstance(handler, prepare.urllib.request.ProxyHandler)
        and handler.proxies == {}
        for handler in handlers
    )


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'])
def test_github_transport_rejects_duplicate_and_nonfinite_json(
    monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    requested = f"{prepare.GITHUB_API_ROOT}/branches/master"

    class Headers(dict):
        def get_content_type(self):
            return "application/json"

    class Response:
        status = 200
        headers = Headers({"Content-Length": str(len(payload))})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return requested

        def read(self, _limit):
            return payload

    class Opener:
        def open(self, _request, timeout):
            return Response()

    monkeypatch.setattr(
        prepare.urllib.request, "build_opener", lambda *_handlers: Opener()
    )
    with pytest.raises(prepare.PreparationError, match="publication-authority:json"):
        prepare._fetch_json(requested)


def test_github_transport_emits_cache_bypass_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = f"{prepare.GITHUB_API_ROOT}/branches/master"
    observed_requests = []

    class Headers(dict):
        def get_content_type(self):
            return "application/json"

    class Response:
        status = 200
        headers = Headers({"Content-Length": "2"})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return requested

        def read(self, _limit):
            return b"{}"

    class Opener:
        def open(self, request, timeout):
            assert timeout == 15
            observed_requests.append(request)
            return Response()

    monkeypatch.setattr(
        prepare.urllib.request, "build_opener", lambda *_handlers: Opener()
    )

    assert prepare._fetch_json(requested) == {}
    assert len(observed_requests) == 1
    assert observed_requests[0].get_header("Cache-control") == "no-cache"
    assert observed_requests[0].get_header("Pragma") == "no-cache"


def test_workflow_run_transport_uses_its_dedicated_bounded_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = (
        f"{prepare.GITHUB_API_ROOT}/actions/workflows/{prepare.GITHUB_WORKFLOW_FILE}/runs"
    )

    class Headers(dict):
        def get_content_type(self):
            return "application/json"

    class Response:
        status = 200
        headers = Headers({"Content-Length": "2"})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return requested

        def read(self, limit):
            assert limit == prepare.MAX_GITHUB_WORKFLOW_RESPONSE_BYTES + 1
            return b"{}"

    class Opener:
        def open(self, _request, timeout):
            assert timeout == 15
            return Response()

    monkeypatch.setattr(
        prepare.urllib.request, "build_opener", lambda *_handlers: Opener()
    )

    assert prepare._fetch_json(requested) == {}
    assert 2 << 20 <= prepare.MAX_GITHUB_WORKFLOW_RESPONSE_BYTES <= 8 << 20


def mission_state_document(phase: str, run_state: object) -> dict[str, Any]:
    state = json.loads(json.dumps(prepare.EXPECTED_MISSION_STATE_COMMON))
    phase_contract = prepare.MISSION_PHASE_CONTRACTS.get(phase)
    state["run_state"] = run_state
    state["next_program"] = {
        "iteration": 135,
        "name": "semantics-free placebo dose-response causal closure",
        "phase": phase,
        "authorized_actions": (
            list(phase_contract["authorized_actions"])
            if phase_contract is not None
            else []
        ),
        "forbidden_actions": (
            list(phase_contract["forbidden_actions"])
            if phase_contract is not None
            else []
        ),
    }
    return state


def build_fixture(
    tmp_path: Path,
    *,
    mission_phase: str = prepare.EXECUTION_PHASE,
    run_state: str = "IDLE",
) -> tuple[prepare.HostConfig, prepare.Hooks, FakeRunner, str, dict]:
    root = tmp_path.resolve()
    stack = root / "stack"
    packet = stack / ".iter135-packet"
    install = stack / "iter135"
    uniad = stack / "UniAD"
    neuroncap = stack / "NeuroNCAP"
    neurad = stack / "neurad-studio"
    server = uniad / "inference/server.py"
    compose = neuroncap / "scripts/_docker_compose_release.sh"
    dataset = root / "dataset"
    analytic = dataset / "sentinel-i135-outoutput"
    smoke = dataset / "sentinel-i135-smoke-evidence"
    for path in (
        packet,
        server.parent,
        compose.parent,
        neuroncap / "docker",
        neurad,
        dataset,
    ):
        path.mkdir(parents=True, exist_ok=True)
    (neuroncap / "docker/Dockerfile").write_text("modified\n")
    (neurad / "Dockerfile").write_text("modified\n")
    (neurad / "Dockerfile.bak").write_text("backup\n")

    baseline = b"baseline server\n"
    server.write_bytes(b"residual server\n")
    compose_before = b"compose-before\n"
    compose_after = b"compose-after\n"
    compose.write_bytes(compose_before)
    patcher = (
        f'EXPECTED_INPUT_SHA256 = "{digest(compose_before)}"\n'
        f'EXPECTED_OUTPUT_SHA256 = "{digest(compose_after)}"\n'
        "def patch_text(source):\n"
        "    if source != 'compose-before\\n':\n"
        "        raise ValueError('preimage')\n"
        "    return 'compose-after\\n'\n"
    ).encode()

    required = (
        "MISSION_STATE.json",
        "prepare_host135.py",
        "patch_compose_dose_env.py",
        "payload.txt",
    )
    modes = {
        "MISSION_STATE.json": 0o644,
        "prepare_host135.py": 0o755,
        "patch_compose_dose_env.py": 0o644,
        "payload.txt": 0o644,
    }
    repository_paths = {name: f"fixture/{name}" for name in required}
    (packet / "MISSION_STATE.json").write_text(
        json.dumps(
            mission_state_document(mission_phase, run_state),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.copyfile(MODULE_PATH, packet / "prepare_host135.py")
    (packet / "patch_compose_dose_env.py").write_bytes(patcher)
    (packet / "payload.txt").write_text("payload\n")
    for name, mode in modes.items():
        (packet / name).chmod(mode)
    files = {}
    for name in required:
        payload = (packet / name).read_bytes()
        files[name] = {"sha256": digest(payload), "bytes": len(payload), "mode": modes[name]}
    manifest = {
        "schema": prepare.PACKET_SCHEMA,
        "source_commit": "a" * 40,
        "files": files,
    }
    manifest_payload = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    (packet / prepare.PACKET_MANIFEST_NAME).write_bytes(manifest_payload)
    manifest_sha = digest(manifest_payload)

    heads = {"uniad": "1" * 40, "neuroncap": "2" * 40, "neurad": "3" * 40}
    mount = {
        "target": str(dataset),
        "source": "/dev/test-evidence",
        "fstype": "ext4",
        "uuid": "11111111-2222-3333-4444-555555555555",
    }
    forbidden = (
        install,
        analytic,
        smoke,
        uniad / "i135-smoke-staging",
        uniad / "dose_schedules.json",
        uniad / "i135-decisions",
        root / "i135-smoke.lock",
        root / "i135-analytic.lock",
        root / "sentinel-i135.log",
    )
    config = prepare.HostConfig(
        packet_root=packet,
        install_root=install,
        executing_controller=packet / "prepare_host135.py",
        required_packet_files=required,
        expected_packet_modes=modes,
        packet_repository_paths=repository_paths,
        uniad_repo=uniad,
        neuroncap_repo=neuroncap,
        neurad_repo=neurad,
        expected_uniad_head=heads["uniad"],
        expected_neuroncap_head=heads["neuroncap"],
        expected_neurad_head=heads["neurad"],
        expected_server_sha256=digest(baseline),
        expected_server_bytes=len(baseline),
        expected_compose_input_sha256=digest(compose_before),
        expected_compose_input_bytes=len(compose_before),
        expected_compose_output_sha256=digest(compose_after),
        expected_compose_output_bytes=len(compose_after),
        dataset_root=dataset,
        analytic_root=analytic,
        smoke_root=smoke,
        minimum_remote_free_bytes=200,
        projected_output_bytes=100,
        minimum_reserve_bytes=50,
        expected_mount={
            "mount_target": str(dataset),
            "mount_source": mount["source"],
            "mount_fstype": mount["fstype"],
            "mount_uuid": mount["uuid"],
        },
        forbidden_paths=forbidden,
    )
    fixture = {
        "repo_ids": {uniad: "uniad", neuroncap: "neuroncap", neurad: "neurad"},
        "heads": heads,
        "mount": mount,
        "server": server,
        "baseline": baseline,
        "compose": compose,
        "compose_before": compose_before,
        "compose_after": compose_after,
        "analytic": analytic,
        "packet": packet,
        "install": install,
        "forbidden": forbidden,
    }
    runner = FakeRunner(fixture)
    github = FakeGitHub(
        manifest["source_commit"],
        {
            repository_paths[name]: (
                (packet / name).read_bytes(),
                "100755" if modes[name] == 0o755 else "100644",
            )
            for name in required
        },
    )
    fixture["github"] = github
    fixed = datetime(2026, 7, 16, 14, 0, tzinfo=timezone.utc)
    hooks = prepare.Hooks(
        run=runner,
        fetch_json=github,
        hostname=lambda: "sentinel-gpu",
        disk_free=lambda _path: 1_000,
        device=lambda path: (
            dataset.stat().st_dev + 1 if Path(path) == Path("/") else Path(path).stat().st_dev
        ),
        now=lambda: fixed,
        environment=lambda: dict(prepare._SAFE_ENVIRONMENT),
        isolated=lambda: True,
    )
    return config, hooks, runner, manifest_sha, fixture


def host_attempt_bomb(label: str):
    def fail(*_args, **_kwargs):
        raise AssertionError(f"host attempt called before state authority: {label}")

    return fail


def no_host_attempt_hooks(hooks: prepare.Hooks) -> prepare.Hooks:
    return replace(
        hooks,
        run=host_attempt_bomb("run"),
        fetch_json=host_attempt_bomb("fetch-json"),
        hostname=host_attempt_bomb("hostname"),
        disk_free=host_attempt_bomb("disk-free"),
        device=host_attempt_bomb("device"),
        now=host_attempt_bomb("now"),
        environment=host_attempt_bomb("environment"),
        isolated=host_attempt_bomb("isolated"),
        before_replace=host_attempt_bomb("before-replace"),
        rename=host_attempt_bomb("rename"),
    )


def prohibit_host_attempt_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        prepare,
        "_base_receipt",
        host_attempt_bomb("_base_receipt"),
    )
    monkeypatch.setattr(
        prepare,
        "_atomic_create_receipt",
        host_attempt_bomb("_atomic_create_receipt"),
    )
    monkeypatch.setattr(
        prepare,
        "_forbidden_state",
        host_attempt_bomb("_forbidden_state"),
    )


def rewrite_packet_json_member(
    fixture: dict[str, Any],
    name: str,
    document: object,
) -> str:
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    (fixture["packet"] / name).write_bytes(payload)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"][name].update(
        {
            "sha256": digest(payload),
            "bytes": len(payload),
        }
    )
    manifest_payload = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_payload)
    return digest(manifest_payload)


def test_green_preparation_is_exact_one_shot_and_never_touches_runtime(
    tmp_path: Path,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.READY_VERDICT
    assert receipt["problem_count"] == 0
    assert receipt["problems"] == []
    assert receipt["started_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["finished_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["host"] == "sentinel-gpu"
    assert all(
        receipt[field] is not None
        for field in ("started_at_utc", "finished_at_utc", "host")
    )
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert fixture["install"].is_dir()
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir() and not any(fixture["analytic"].iterdir())
    assert receipt["packet_manifest_sha256"] == manifest_sha
    assert receipt["publication_authority"] == {
        "schema": prepare.PUBLICATION_AUTHORITY_SCHEMA,
        "repository": prepare.GITHUB_REPOSITORY,
        "branch": prepare.GITHUB_BRANCH,
        "source_commit": "a" * 40,
        "branch_head_sha": "a" * 40,
        "required_checks": list(prepare.REQUIRED_GITHUB_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 310 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": "a" * 40,
                "app_slug": "github-actions",
            }
            for index, name in enumerate(prepare.REQUIRED_GITHUB_CHECKS)
        ],
        "artifacts": [
            {
                "path": path,
                "sha256": receipt["packet"]["files"][name]["sha256"],
                "bytes": receipt["packet"]["files"][name]["bytes"],
                "git_blob_oid": prepare._git_blob_oid(
                    (fixture["install"] / name).read_bytes()
                ),
                "git_mode": (
                    "100755"
                    if config.packet_modes()[name] == 0o755
                    else "100644"
                ),
            }
            for path, name in sorted(
                (path, name) for name, path in config.repository_paths().items()
            )
        ],
        "verified": True,
    }
    assert receipt["invocation"]["environment_matches"] is True
    assert receipt["invocation"]["isolated"] is True
    assert receipt["packet"]["independently_supplied_manifest_sha256"] == manifest_sha
    assert receipt["controller"]["sha256"] == receipt["packet"]["files"][
        "prepare_host135.py"
    ]["sha256"]
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert not marker.exists()
    assert pending.read_bytes() == output.read_bytes()
    assert (
        pending.stat(follow_symlinks=False).st_dev,
        pending.stat(follow_symlinks=False).st_ino,
    ) == (
        output.stat(follow_symlinks=False).st_dev,
        output.stat(follow_symlinks=False).st_ino,
    )
    assert pending.stat(follow_symlinks=False).st_nlink == 2
    assert output.stat(follow_symlinks=False).st_nlink == 2
    assert pending.stat(follow_symlinks=False).st_mode & 0o777 == 0o444
    assert output.stat(follow_symlinks=False).st_mode & 0o777 == 0o444
    flattened = " ".join(" ".join(call) for call in runner.calls)
    for forbidden in ("docker", "nvidia-smi", " checkout ", " reset ", " rm "):
        assert forbidden not in flattened
    github = fixture["github"]
    branch_url = f"{prepare.GITHUB_API_ROOT}/branches/{prepare.GITHUB_BRANCH}"
    workflows_url = (
        f"{prepare.GITHUB_API_ROOT}/actions/workflows/{prepare.GITHUB_WORKFLOW_FILE}/runs?"
        f"branch={prepare.GITHUB_BRANCH}&event=push&head_sha={github.source_commit}&"
        f"per_page={prepare.MAX_GITHUB_WORKFLOW_RUNS}&page=1"
    )
    jobs_url = (
        f"{prepare.GITHUB_API_ROOT}/actions/runs/{WORKFLOW_RUN_ID}/attempts/1/jobs?"
        f"per_page={prepare.MAX_GITHUB_JOBS}&page=1"
    )
    assert github.calls == [
        branch_url,
        workflows_url,
        f"{prepare.GITHUB_API_ROOT}/git/commits/{github.source_commit}",
        jobs_url,
        workflows_url,
        f"{prepare.GITHUB_API_ROOT}/git/trees/{github.tree_sha}?recursive=1",
        branch_url,
        workflows_url,
        jobs_url,
        workflows_url,
        branch_url,
        branch_url,
        workflows_url,
        jobs_url,
        workflows_url,
        branch_url,
    ]
    assert not any("/git/blobs/" in url for url in github.calls)


def test_analytic_root_parent_fsync_failure_yields_durable_red_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_analytic_parent_fsync(descriptor: int, problem: str) -> None:
        if problem == "storage:analytic-root-parent-fsync":
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_analytic_parent_fsync,
    )

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=hooks,
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["storage:analytic-root-parent-fsync"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert fixture["analytic"].is_dir()
    assert not fixture["install"].exists()
    assert not output.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert json.loads(output.read_bytes()) == receipt
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2


@pytest.mark.parametrize(
    ("initial_sample", "problem"),
    [
        pytest.param(OSError("clock unavailable"), "timing:started:OSError"),
        pytest.param(object(), "timing:started:TypeError", id="non-datetime"),
        pytest.param(
            datetime(2026, 7, 16, 14, 0),
            "timing:started:ValueError",
            id="naive-datetime",
        ),
        pytest.param(
            datetime(
                2026,
                7,
                16,
                16,
                0,
                tzinfo=timezone(timedelta(hours=2)),
            ),
            "timing:started:ValueError",
            id="non-utc-datetime",
        ),
    ],
)
def test_initial_clock_failure_persists_null_safe_red_attempt(
    tmp_path: Path,
    initial_sample: object,
    problem: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixed = datetime(2026, 7, 16, 14, 0, tzinfo=timezone.utc)
    samples = iter((initial_sample, fixed))

    def sample_time() -> object:
        value = next(samples)
        if isinstance(value, Exception):
            raise value
        return value

    hooks = replace(
        hooks,
        now=sample_time,
        hostname=host_attempt_bomb("hostname-after-start-clock-failure"),
    )

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [problem]
    assert receipt["problem_count"] == len(receipt["problems"]) == 1
    assert receipt["started_at_utc"] is None
    assert receipt["finished_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["host"] is None
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    assert fixture["github"].calls == []
    assert runner.calls == []
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()


@pytest.mark.parametrize(
    ("hostname", "problem"),
    [
        pytest.param(RuntimeError("hostname unavailable"), "host:probe:RuntimeError"),
        pytest.param(["sentinel-gpu"], "host:probe:TypeError", id="json-non-string"),
        pytest.param(object(), "host:probe:TypeError", id="non-json-object"),
    ],
)
def test_hostname_probe_failure_persists_only_validated_json_metadata(
    tmp_path: Path,
    hostname: object,
    problem: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)

    def sample_hostname() -> object:
        if isinstance(hostname, Exception):
            raise hostname
        return hostname

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, hostname=sample_hostname),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [problem]
    assert receipt["problem_count"] == len(receipt["problems"]) == 1
    assert receipt["started_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["finished_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["host"] is None
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    assert fixture["github"].calls == []
    assert runner.calls == []
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()


def test_terminal_clock_failure_after_install_downgrades_and_persists_red_attempt(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixed = datetime(2026, 7, 16, 14, 0, tzinfo=timezone.utc)
    samples = iter((fixed, OSError("clock unavailable")))

    def sample_time() -> datetime:
        value = next(samples)
        if isinstance(value, Exception):
            raise value
        return value

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, now=sample_time),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["timing:finished:OSError"]
    assert receipt["problem_count"] == len(receipt["problems"]) == 1
    assert receipt["started_at_utc"] == "2026-07-16T14:00:00Z"
    assert receipt["finished_at_utc"] is None
    assert receipt["host"] == "sentinel-gpu"
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert fixture["install"].is_dir()
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir()
    assert receipt["actions"][-1]["action"] == "atomically_install_verified_packet"


@pytest.mark.parametrize(
    ("isolated_hook", "problem"),
    [
        pytest.param(
            lambda: object(),
            "invocation:isolation-probe:TypeError",
            id="non-json-return",
        ),
        pytest.param(
            lambda: (_ for _ in ()).throw(RuntimeError("private hook prose")),
            "invocation:isolation-probe:RuntimeError",
            id="hook-exception",
        ),
    ],
)
def test_isolation_hook_type_and_exception_faults_create_bounded_red_receipt(
    tmp_path: Path,
    isolated_hook,
    problem: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, isolated=isolated_hook),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [problem]
    assert len(receipt["problems"][0].encode()) <= prepare.MAX_PROBLEM_TOKEN_BYTES
    assert "private hook prose" not in json.dumps(receipt)
    assert receipt["invocation"]["isolated"] is None
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    assert fixture["github"].calls == []
    assert runner.calls == []
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()


def test_rename_hook_that_moves_then_faults_persists_red_receipt_under_install_root(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def move_then_fault(source: Path, destination: Path) -> None:
        source.rename(destination)
        raise OSError("fault after successful rename")

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=move_then_fault),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["internal:OSError"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert fixture["install"].is_dir()
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir()


@pytest.mark.parametrize(
    ("hook_result", "problem"),
    [
        ("return", "packet:rename-hook-source-identity"),
        ("raise", "internal:OSError"),
    ],
)
def test_moved_packet_with_recreated_source_keeps_red_receipt_on_original_inode(
    tmp_path: Path,
    hook_result: str,
    problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    recreated_identity: list[tuple[int, int]] = []

    def move_recreate_source(source: Path, destination: Path) -> None:
        source.rename(destination)
        source.mkdir()
        recreated = source.stat(follow_symlinks=False)
        recreated_identity.append((recreated.st_dev, recreated.st_ino))
        if hook_result == "raise":
            raise OSError("fault after move and source recreation")

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=move_recreate_source),
    )

    installed = fixture["install"].stat(follow_symlinks=False)
    assert recreated_identity == [
        (
            fixture["packet"].stat(follow_symlinks=False).st_dev,
            fixture["packet"].stat(follow_symlinks=False).st_ino,
        )
    ]
    assert (installed.st_dev, installed.st_ino) != recreated_identity[0]
    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [problem]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert json.loads(output.read_bytes()) == receipt
    assert not output.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2
    assert fixture["packet"].is_dir()
    assert not any(fixture["packet"].iterdir())


def test_rename_hook_noop_cannot_suppress_controller_owned_exclusive_install(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=lambda _source, _destination: None),
    )

    assert receipt["verdict"] == prepare.READY_VERDICT
    assert receipt["problems"] == []
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert fixture["install"].is_dir()
    assert json.loads(output.read_bytes()) == receipt
    assert receipt["receipt_payload_sha256"] == prepare._receipt_payload_sha256(receipt)


@pytest.mark.parametrize("rename_mode", ["controller-owned", "hook-bypassed"])
def test_install_parent_fsync_failure_yields_durable_red_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rename_mode: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_install_parent_fsync(descriptor: int, problem: str) -> None:
        if problem == "packet:install-parent-fsync":
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    def hook_rename(source: Path, destination: Path) -> None:
        if rename_mode == "hook-bypassed":
            source.rename(destination)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_install_parent_fsync,
    )
    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=hook_rename),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:install-parent-fsync"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert fixture["install"].is_dir()
    assert not output.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert json.loads(output.read_bytes()) == receipt
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2


def test_rename_hook_copy_is_not_accepted_as_install_and_receipt_stays_with_packet(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=shutil.copytree),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:install-root-race"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert fixture["packet"].is_dir()
    assert fixture["install"].is_dir()
    assert json.loads(output.read_bytes()) == receipt
    assert not (fixture["install"] / prepare.RECEIPT_NAME).exists()


def test_raced_install_destination_is_never_replaced_or_cleaned(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def create_raced_destination(_source: Path, destination: Path) -> None:
        destination.mkdir()

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=create_raced_destination),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:install-root-race"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert fixture["packet"].is_dir()
    assert fixture["install"].is_dir()
    assert not any(fixture["install"].iterdir())
    assert json.loads(output.read_bytes()) == receipt


def test_missing_platform_no_replace_primitive_fails_closed_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    monkeypatch.setattr(prepare.sys, "platform", "unsupported-test-platform")

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=hooks,
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:exclusive-install-unsupported"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert fixture["packet"].is_dir()
    assert not fixture["install"].exists()
    assert json.loads(output.read_bytes()) == receipt


def test_kernel_exclusive_rename_primitive_never_replaces_empty_destination(
    tmp_path: Path,
) -> None:
    parent = tmp_path.resolve() / "exclusive-rename-parent"
    source = parent / "source"
    destination = parent / "destination"
    source.mkdir(parents=True)
    destination.mkdir()
    source_before = source.stat(follow_symlinks=False)
    destination_before = destination.stat(follow_symlinks=False)
    descriptor = os.open(
        parent,
        os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY,
    )
    try:
        with pytest.raises(
            prepare.PreparationError,
            match="^packet:install-root-race$",
        ):
            prepare._exclusive_rename_at(
                descriptor,
                source.name,
                destination.name,
            )
    finally:
        os.close(descriptor)

    source_after = source.stat(follow_symlinks=False)
    destination_after = destination.stat(follow_symlinks=False)
    assert (source_after.st_dev, source_after.st_ino) == (
        source_before.st_dev,
        source_before.st_ino,
    )
    assert (destination_after.st_dev, destination_after.st_ino) == (
        destination_before.st_dev,
        destination_before.st_ino,
    )


def test_hook_cannot_hide_raced_destination_by_replacing_it_with_packet(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    raced_identity: list[tuple[int, int]] = []

    def reproduce_replace_race(source: Path, destination: Path) -> None:
        destination.mkdir()
        raced = destination.stat(follow_symlinks=False)
        raced_identity.append((raced.st_dev, raced.st_ino))
        source.rename(destination)

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=reproduce_replace_race),
    )

    installed = fixture["install"].stat(follow_symlinks=False)
    assert len(raced_identity) == 1
    assert (installed.st_dev, installed.st_ino) != raced_identity[0]
    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:exclusive-install-bypassed"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert not fixture["packet"].exists()
    assert json.loads(output.read_bytes()) == receipt


def test_stack_parent_replacement_during_rename_seam_blocks_green_receipt(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    stack = fixture["packet"].parent
    moved_stack = stack.with_name("stack-moved-during-install")

    def replace_parent_and_move_packet(source: Path, _destination: Path) -> None:
        stack.rename(moved_stack)
        stack.mkdir()
        (moved_stack / source.name).rename(stack / source.name)

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=replace_parent_and_move_packet),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:install-parent-identity"]
    assert output == stack / fixture["packet"].name / prepare.RECEIPT_NAME
    assert output.is_file()
    assert json.loads(output.read_bytes()) == receipt
    assert moved_stack.is_dir()
    assert (moved_stack / "UniAD").is_dir()
    assert (moved_stack / "NeuroNCAP").is_dir()
    assert (moved_stack / "neurad-studio").is_dir()
    assert not fixture["install"].exists()


def test_final_clock_hook_cannot_replace_a_bound_canonical_root_before_green(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixed = datetime(2026, 7, 16, 14, 0, tzinfo=timezone.utc)
    uniad = config.uniad_repo
    moved_uniad = uniad.with_name("UniAD-moved-before-green")
    samples = 0

    def mutate_on_terminal_clock() -> datetime:
        nonlocal samples
        samples += 1
        if samples == 2:
            uniad.rename(moved_uniad)
            uniad.mkdir()
        return fixed

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, now=mutate_on_terminal_clock),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["canonical-root:uniad-root:identity"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert output.is_file()
    assert moved_uniad.is_dir()
    assert json.loads(output.read_bytes()) == receipt


@pytest.mark.parametrize(
    "receipt_stage",
    ["receipt-before-open", "receipt-after-open"],
)
def test_receipt_parent_rename_and_recreation_cannot_return_green(
    tmp_path: Path,
    receipt_stage: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    install = fixture["install"]
    moved_install = install.with_name(f"iter135-moved-{receipt_stage}")

    def replace_receipt_parent(label: str, _path: Path) -> None:
        if label == receipt_stage:
            install.rename(moved_install)
            install.mkdir()

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt-parent:identity$",
    ):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=replace_receipt_parent),
        )

    assert install.is_dir()
    assert not any(install.iterdir())
    assert moved_install.is_dir()
    moved_receipt = moved_install / prepare.RECEIPT_NAME
    moved_marker = moved_install / prepare.RECEIPT_ATTEMPT_NAME
    moved_pending = moved_install / prepare.RECEIPT_PENDING_NAME
    assert not moved_receipt.exists()
    assert moved_marker.is_file()
    assert moved_pending.exists() is (receipt_stage == "receipt-after-open")
    if moved_pending.exists():
        assert moved_pending.stat().st_size == 0


@pytest.mark.parametrize(
    ("receipt_stage", "mutation", "problem"),
    [
        (
            "receipt-before-leaf-verify",
            "replace",
            r"^receipt:pending-identity$",
        ),
        (
            "receipt-after-directory-fsync",
            "remove",
            r"^receipt:canonical-missing$",
        ),
    ],
)
def test_receipt_leaf_replacement_or_removal_cannot_return_green(
    tmp_path: Path,
    receipt_stage: str,
    mutation: str,
    problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    hostile = b"same-directory hostile replacement\n"

    def mutate_receipt_leaf(label: str, path: Path) -> None:
        if label != receipt_stage:
            return
        path.unlink()
        if mutation == "replace":
            path.write_bytes(hostile)

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=mutate_receipt_leaf),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    if mutation == "replace":
        assert not output.exists()
        assert output.with_name(prepare.RECEIPT_PENDING_NAME).read_bytes() == hostile
    else:
        assert not output.exists()


def test_receipt_exclusive_create_preserves_a_raced_leaf(tmp_path: Path) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    hostile = b"pre-existing raced receipt\n"

    def race_receipt_create(label: str, path: Path) -> None:
        if label == "receipt-before-open":
            path.write_bytes(hostile)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:already-exists$",
    ):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=race_receipt_create),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.read_bytes() == hostile


def test_partial_receipt_write_fails_closed_without_a_green_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_write = os.write
    write_calls = 0

    def activate_short_write(label: str, _path: Path) -> None:
        if label == "receipt-after-open":
            monkeypatch.setattr(prepare.os, "write", partial_then_stop)

    def partial_then_stop(descriptor: int, payload: bytes) -> int:
        nonlocal write_calls
        write_calls += 1
        if write_calls == 1:
            assert payload.endswith(b"\n")
            return original_write(descriptor, payload[:-1])
        return 0

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:short-write$",
    ):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=activate_short_write),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert marker.is_file()
    assert not output.exists()
    partial = pending.read_bytes()
    assert write_calls == 2
    assert partial.endswith(b"}") and not partial.endswith(b"\n")
    assert type(json.loads(partial)) is dict


def test_attempt_write_oserror_leaves_denial_name_without_receipt_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def fail_write(_descriptor: int, _payload: bytes) -> int:
        raise OSError("injected attempt write failure")

    monkeypatch.setattr(prepare.os, "write", fail_write)
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:write$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["packet"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    assert marker.is_file()
    assert marker.read_bytes() == b""
    assert stat.S_IMODE(marker.stat().st_mode) == 0o600
    assert not output.with_name(prepare.RECEIPT_PENDING_NAME).exists()
    assert not output.exists()


def test_pending_write_oserror_retains_marker_without_canonical_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def activate_write_failure(label: str, _path: Path) -> None:
        if label == "receipt-after-open":
            monkeypatch.setattr(
                prepare.os,
                "write",
                lambda _descriptor, _payload: (_ for _ in ()).throw(
                    OSError("injected receipt write failure")
                ),
            )

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:write$",
    ):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=activate_write_failure),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert marker.is_file()
    assert json.loads(marker.read_bytes())["status"] == (
        "ATTEMPT_IN_PROGRESS_NO_HOST_PREPARATION_VERDICT"
    )
    assert pending.is_file()
    assert pending.stat().st_size == 0
    assert not output.exists()


@pytest.mark.parametrize(
    "problem",
    [
        "receipt:attempt-file-fsync",
        "receipt:attempt-parent-fsync",
    ],
)
def test_attempt_sync_failures_cannot_create_canonical_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_selected_sync(descriptor: int, observed_problem: str) -> None:
        if observed_problem == problem:
            raise prepare.PreparationError(observed_problem)
        original_fsync(descriptor, observed_problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_selected_sync,
    )
    with pytest.raises(prepare.PreparationError, match=rf"^{problem}$"):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["packet"] / prepare.RECEIPT_NAME
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert not output.with_name(prepare.RECEIPT_PENDING_NAME).exists()
    assert not output.exists()


def test_receipt_file_fsync_failure_retains_marker_and_pending_without_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_pending_fsync(descriptor: int, problem: str) -> None:
        if problem == "receipt:pending-file-fsync":
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_pending_fsync,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:pending-file-fsync$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert marker.is_file()
    assert pending.is_file()
    assert type(json.loads(pending.read_bytes())) is dict
    assert not output.exists()


@pytest.mark.parametrize(
    ("problem", "canonical_exists"),
    [
        ("receipt:pending-parent-fsync", False),
        ("receipt:canonical-parent-fsync", True),
    ],
)
def test_receipt_parent_sync_failures_retain_nonauthority_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
    canonical_exists: bool,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_selected_sync(descriptor: int, observed_problem: str) -> None:
        if observed_problem == problem:
            raise prepare.PreparationError(observed_problem)
        original_fsync(descriptor, observed_problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_selected_sync,
    )
    with pytest.raises(prepare.PreparationError, match=rf"^{problem}$"):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert marker.is_file()
    assert pending.is_file()
    assert output.exists() is canonical_exists
    if canonical_exists:
        assert pending.stat().st_ino == output.stat().st_ino
        assert pending.stat().st_nlink == output.stat().st_nlink == 2


def test_exception_only_terminal_hook_retains_durable_nonauthority_marker(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def fail_terminal_hook(label: str, path: Path) -> None:
        if label == "receipt-before-terminal-coupled-check":
            assert path.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
            raise OSError("terminal callback fault")

    with pytest.raises(OSError, match=r"^terminal callback fault$"):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(hooks, before_replace=fail_terminal_hook),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert marker.is_file()
    assert json.loads(marker.read_bytes())["status"] == (
        "ATTEMPT_IN_PROGRESS_NO_HOST_PREPARATION_VERDICT"
    )
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2


@pytest.mark.parametrize("unlink_fault", ["before-remove", "after-remove"])
def test_attempt_marker_remove_failure_cannot_return_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unlink_fault: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_unlink = prepare.os.unlink

    def fail_marker_unlink(path: str | bytes, *args, **kwargs) -> None:
        if path == prepare.RECEIPT_ATTEMPT_NAME and kwargs.get("dir_fd") is not None:
            if unlink_fault == "after-remove":
                original_unlink(path, *args, **kwargs)
            raise OSError("marker unlink fault")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(prepare.os, "unlink", fail_marker_unlink)
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:attempt-remove$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).stat().st_nlink == 2
    assert output.stat().st_nlink == 2


def test_completion_parent_fsync_failure_restores_durable_attempt_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor
    completion_faults = 0

    def fail_completion_fsync_once(descriptor: int, problem: str) -> None:
        nonlocal completion_faults
        if problem == "receipt:completion-parent-fsync" and completion_faults == 0:
            completion_faults += 1
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_completion_fsync_once,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:completion-parent-fsync$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert completion_faults == 1
    assert marker.is_file()
    assert json.loads(marker.read_bytes())["status"] == (
        "ATTEMPT_IN_PROGRESS_NO_HOST_PREPARATION_VERDICT"
    )
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2


def test_outer_publication_handler_does_not_repeat_inner_marker_restoration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor
    original_restore = prepare._restore_attempt_marker
    completion_faults = 0
    restoration_calls = 0

    def fail_completion_fsync_once(descriptor: int, problem: str) -> None:
        nonlocal completion_faults
        if problem == "receipt:completion-parent-fsync" and completion_faults == 0:
            completion_faults += 1
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    def count_restoration(*args, **kwargs) -> None:
        nonlocal restoration_calls
        restoration_calls += 1
        original_restore(*args, **kwargs)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_completion_fsync_once,
    )
    monkeypatch.setattr(prepare, "_restore_attempt_marker", count_restoration)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:completion-parent-fsync$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert completion_faults == 1
    assert restoration_calls == 1
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).stat().st_nlink == 2
    assert output.stat().st_nlink == 2


@pytest.mark.parametrize(
    "restoration_problem",
    [
        "receipt:attempt-restore-file-fsync",
        "receipt:attempt-restore-parent-fsync",
    ],
)
def test_failed_marker_restoration_reports_completion_ambiguous(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restoration_problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_completion_and_restoration_fsync(
        descriptor: int,
        problem: str,
    ) -> None:
        if problem in {
            "receipt:completion-parent-fsync",
            restoration_problem,
        }:
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_completion_and_restoration_fsync,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:completion-ambiguous$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()


def test_attempt_recovery_parent_fsync_failure_reports_completion_ambiguous(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_fsync = prepare._fsync_receipt_descriptor

    def fail_publication_and_recovery_sync(
        descriptor: int,
        problem: str,
    ) -> None:
        if problem in {
            "receipt:pending-file-fsync",
            "receipt:attempt-recovery-parent-fsync",
        }:
            raise prepare.PreparationError(problem)
        original_fsync(descriptor, problem)

    monkeypatch.setattr(
        prepare,
        "_fsync_receipt_descriptor",
        fail_publication_and_recovery_sync,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:completion-ambiguous$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).is_file()
    assert not output.exists()


def test_post_removal_replay_fault_restores_attempt_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_observation = prepare._receipt_pair_observation

    def fail_marker_absent_replay(*args, marker_absent: bool, **kwargs):
        if marker_absent:
            raise prepare.PreparationError("receipt:test-terminal-replay")
        return original_observation(
            *args,
            marker_absent=marker_absent,
            **kwargs,
        )

    monkeypatch.setattr(
        prepare,
        "_receipt_pair_observation",
        fail_marker_absent_replay,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:test-terminal-replay$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).stat().st_nlink == 2
    assert output.stat().st_nlink == 2


@pytest.mark.parametrize(
    "witness_mutation",
    ["byte-count-float", "receipt-inode-drift"],
)
def test_prepare_host_consumes_exact_completion_witness_before_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    witness_mutation: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_commit = prepare._commit_receipt_transaction

    def forge_witness(*args, **kwargs):
        witness = original_commit(*args, **kwargs)
        if witness_mutation == "byte-count-float":
            return replace(
                witness,
                byte_count=float(witness.byte_count),
            )
        return replace(
            witness,
            receipt_inode=(
                witness.receipt_inode[0],
                witness.receipt_inode[1] + 1,
            ),
        )

    monkeypatch.setattr(
        prepare,
        "_commit_receipt_transaction",
        forge_witness,
    )
    with pytest.raises(
        prepare.PreparationError,
        match=(
            r"^receipt:completion-witness$"
            if witness_mutation == "byte-count-float"
            else r"^receipt:pending-identity$"
        ),
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.with_name(prepare.RECEIPT_PENDING_NAME).stat().st_nlink == 2
    assert output.stat().st_nlink == 2


def test_commit_then_raise_restores_marker_before_producer_error_escapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    original_commit = prepare._commit_receipt_transaction
    committed = False

    def commit_then_raise(*args, **kwargs):
        nonlocal committed
        witness = original_commit(*args, **kwargs)
        output_path = Path(args[1])
        assert not output_path.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()
        assert witness.verdict == prepare.READY_VERDICT
        committed = True
        raise OSError("post-commit producer wrapper fault")

    monkeypatch.setattr(
        prepare,
        "_commit_receipt_transaction",
        commit_then_raise,
    )
    with pytest.raises(
        OSError,
        match=r"^post-commit producer wrapper fault$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert committed
    assert marker.is_file()
    assert json.loads(marker.read_bytes())["status"] == (
        "ATTEMPT_IN_PROGRESS_NO_HOST_PREPARATION_VERDICT"
    )
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        (
            "analytic-child",
            r"^storage:analytic-root-terminal-drift$",
        ),
        (
            "packet-payload",
            r"^packet:revalidation:terminal-publication:payload\.txt$",
        ),
        (
            "canonical-root",
            r"^canonical-root:uniad-root:identity$",
        ),
        (
            "repository-snapshot",
            r"^repository:terminal-drift$",
        ),
        (
            "repository-content",
            r"^compose:terminal-drift$",
        ),
        (
            "forbidden-path",
            r"^host:forbidden-path-race$",
        ),
    ],
)
def test_last_receipt_callback_cannot_drift_terminal_host_contract(
    tmp_path: Path,
    mutation: str,
    problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    callback_observed = False

    def mutate_after_every_earlier_host_replay(label: str, path: Path) -> None:
        nonlocal callback_observed
        if label != "receipt-before-terminal-coupled-check":
            return
        callback_observed = True
        if mutation == "analytic-child":
            (config.analytic_root / "late-hostile-output").write_bytes(b"late\n")
        elif mutation == "packet-payload":
            (path.parent / "payload.txt").write_bytes(b"late packet drift\n")
        elif mutation == "canonical-root":
            moved = config.uniad_repo.with_name("UniAD-moved-at-terminal-receipt")
            config.uniad_repo.rename(moved)
            config.uniad_repo.mkdir()
        elif mutation == "repository-snapshot":
            fixture["server"].write_bytes(b"late repository status drift\n")
        elif mutation == "repository-content":
            fixture["compose"].write_bytes(b"late repository content drift\n")
        elif mutation == "forbidden-path":
            config.smoke_root.mkdir()
        else:
            raise AssertionError(f"unsupported terminal mutation: {mutation}")

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(
                hooks,
                before_replace=mutate_after_every_earlier_host_replay,
            ),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    marker = output.with_name(prepare.RECEIPT_ATTEMPT_NAME)
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert callback_observed
    assert marker.is_file()
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert pending.stat().st_nlink == output.stat().st_nlink == 2
    assert json.loads(output.read_bytes())["verdict"] == prepare.READY_VERDICT


def test_leaf_swap_at_terminal_boundary_cannot_return_a_completion(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    boundary_observed = False

    def swap_canonical_before_marker_removal(label: str, path: Path) -> None:
        nonlocal boundary_observed
        if label != "receipt-before-terminal-coupled-check":
            return
        boundary_observed = True
        assert path.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
        payload = path.read_bytes()
        path.unlink()
        path.write_bytes(payload)
        path.chmod(0o444)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^receipt:pending-identity$",
    ):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(
                hooks,
                before_replace=swap_canonical_before_marker_removal,
            ),
        )

    output = fixture["install"] / prepare.RECEIPT_NAME
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert boundary_observed
    assert output.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert output.read_bytes() == pending.read_bytes()
    assert output.stat().st_ino != pending.stat().st_ino


@pytest.mark.parametrize(
    ("mismatched_name", "problem"),
    [
        (prepare.RECEIPT_ATTEMPT_NAME, r"^receipt:attempt-identity$"),
        (prepare.RECEIPT_PENDING_NAME, r"^receipt:pending-identity$"),
        (prepare.RECEIPT_NAME, r"^receipt:pending-identity$"),
    ],
)
def test_marker_pending_or_canonical_inode_mismatch_cannot_return_green(
    tmp_path: Path,
    mismatched_name: str,
    problem: str,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    mutation_observed = False

    def replace_with_same_payload_on_new_inode(label: str, path: Path) -> None:
        nonlocal mutation_observed
        if label != "receipt-after-directory-fsync":
            return
        mutation_observed = True
        target = path.parent / mismatched_name
        payload = target.read_bytes()
        target.unlink()
        target.write_bytes(payload)
        target.chmod(0o444)

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare.prepare_host(
            manifest_sha,
            config=config,
            hooks=replace(
                hooks,
                before_replace=replace_with_same_payload_on_new_inode,
            ),
        )

    install = fixture["install"]
    assert mutation_observed
    assert (install / prepare.RECEIPT_ATTEMPT_NAME).is_file()
    assert (install / prepare.RECEIPT_PENDING_NAME).is_file()
    assert (install / prepare.RECEIPT_NAME).is_file()


def test_canonical_receipt_is_not_returned_while_attempt_marker_exists(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, _fixture = build_fixture(tmp_path)
    observed_precommit_state = False

    def inspect_before_marker_removal(label: str, path: Path) -> None:
        nonlocal observed_precommit_state
        if label != "receipt-after-directory-fsync":
            return
        observed_precommit_state = True
        assert path.is_file()
        assert path.with_name(prepare.RECEIPT_PENDING_NAME).is_file()
        assert path.with_name(prepare.RECEIPT_ATTEMPT_NAME).is_file()

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, before_replace=inspect_before_marker_removal),
    )

    assert observed_precommit_state
    assert receipt["verdict"] == prepare.READY_VERDICT
    assert not output.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()


def test_receipt_serialization_type_fault_degrades_to_durable_minimal_red_document(
    tmp_path: Path,
) -> None:
    supplied_sha = "a" * 64
    receipt_root = tmp_path.resolve() / "packet"
    receipt_root.mkdir()
    receipt = prepare._base_receipt(supplied_sha)
    receipt["started_at_utc"] = "2026-07-16T14:00:00Z"
    receipt["invocation"] = {"isolated": object()}

    safe = prepare._serialization_safe_receipt(receipt, supplied_sha)
    output = receipt_root / prepare.RECEIPT_NAME
    prepare._atomic_create_receipt(output, safe)

    assert safe["verdict"] == prepare.INCOMPLETE_VERDICT
    assert safe["problems"] == ["receipt:serialization:TypeError"]
    assert safe["problem_count"] == 1
    assert safe["started_at_utc"] == "2026-07-16T14:00:00Z"
    assert safe["invocation"] is None
    assert json.loads(output.read_bytes()) == safe
    pending = output.with_name(prepare.RECEIPT_PENDING_NAME)
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat().st_ino == output.stat().st_ino
    assert not output.with_name(prepare.RECEIPT_ATTEMPT_NAME).exists()
    assert safe["receipt_payload_sha256"] == prepare._receipt_payload_sha256(safe)


@pytest.mark.parametrize(
    ("mission_phase", "run_state", "problem"),
    [
        (
            prepare.CONTROL_HARDENING_PHASE,
            "UNKNOWN",
            "mission-state:control-hardening-required",
        ),
        (
            prepare.PREREGISTERED_PHASE,
            "UNKNOWN",
            "mission-state:preregistered-tooling-required",
        ),
        (
            prepare.EXECUTION_PHASE,
            "UNKNOWN",
            "mission-state:run-state",
        ),
        (
            "OUT_OF_SCOPE_PHASE",
            "IDLE",
            "mission-state:phase",
        ),
    ],
)
def test_packet_bound_control_stop_precedes_authority_and_every_host_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mission_phase: str,
    run_state: str,
    problem: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(
        tmp_path,
        mission_phase=mission_phase,
        run_state=run_state,
    )
    preserved_paths: list[Path] = []
    for index, path in enumerate(config.forbidden()):
        if path.suffix in {".json", ".lock", ".log"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"preserved forbidden file {index}\n".encode())
            preserved_paths.append(path)
        else:
            path.mkdir(parents=True, exist_ok=True)
            marker = path / f".preserved-{index}"
            marker.write_bytes(f"preserved forbidden directory {index}\n".encode())
            preserved_paths.extend((path, marker))
    preserved = {
        path: (
            path.stat(follow_symlinks=False).st_dev,
            path.stat(follow_symlinks=False).st_ino,
            path.stat(follow_symlinks=False).st_mode,
            path.stat(follow_symlinks=False).st_size,
            path.stat(follow_symlinks=False).st_mtime_ns,
            path.read_bytes() if path.is_file() else None,
        )
        for path in preserved_paths
    }

    def bomb(label: str):
        def fail(*_args, **_kwargs):
            raise AssertionError(f"post-state operation called: {label}")

        return fail

    hooks = replace(
        hooks,
        run=bomb("run"),
        fetch_json=bomb("fetch-json"),
        hostname=bomb("hostname"),
        disk_free=bomb("disk-free"),
        device=bomb("device"),
        now=bomb("now"),
        environment=bomb("environment"),
        isolated=bomb("isolated"),
        before_replace=bomb("before-replace"),
        rename=bomb("rename"),
    )
    for name in (
        "_base_receipt",
        "_forbidden_state",
        "_atomic_create_receipt",
        "verify_publication_authority",
        "repository_snapshot",
        "_mount_snapshot",
        "_atomic_replace",
        "revalidate_packet_payloads",
    ):
        monkeypatch.setattr(prepare, name, bomb(name))

    with pytest.raises(prepare.MissionStateStop, match=problem):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert not (fixture["install"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert {
        path: (
            path.stat(follow_symlinks=False).st_dev,
            path.stat(follow_symlinks=False).st_ino,
            path.stat(follow_symlinks=False).st_mode,
            path.stat(follow_symlinks=False).st_size,
            path.stat(follow_symlinks=False).st_mtime_ns,
            path.read_bytes() if path.is_file() else None,
        )
        for path in preserved
    } == preserved


@pytest.mark.parametrize(
    ("mismatch", "problem"),
    [
        ("mission-state", r"^packet:file-drift:MISSION_STATE\.json$"),
        ("invoked-controller", r"^packet:controller-path$"),
    ],
)
def test_invocation_packet_state_binding_fails_before_any_host_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
    problem: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    if mismatch == "mission-state":
        state_path = fixture["packet"] / "MISSION_STATE.json"
        state = json.loads(state_path.read_bytes())
        state["run_state"] = "UNKNOWN"
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    else:
        invoked_controller = tmp_path / "invoked-prepare_host135.py"
        shutil.copyfile(fixture["packet"] / prepare.CONTROLLER_NAME, invoked_controller)
        config = replace(config, executing_controller=invoked_controller)

    def bomb(label: str):
        def fail(*_args, **_kwargs):
            raise AssertionError(f"host attempt called: {label}")

        return fail

    hooks = replace(
        hooks,
        run=bomb("run"),
        fetch_json=bomb("fetch-json"),
        hostname=bomb("hostname"),
        disk_free=bomb("disk-free"),
        device=bomb("device"),
        now=bomb("now"),
        environment=bomb("environment"),
        isolated=bomb("isolated"),
        before_replace=bomb("before-replace"),
        rename=bomb("rename"),
    )
    monkeypatch.setattr(prepare, "_base_receipt", bomb("_base_receipt"))
    monkeypatch.setattr(
        prepare, "_atomic_create_receipt", bomb("_atomic_create_receipt")
    )
    monkeypatch.setattr(prepare, "_forbidden_state", bomb("_forbidden_state"))

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


@pytest.mark.parametrize(
    ("field", "impostor"),
    [
        ("bytes", "float"),
        ("bytes", "bool"),
        ("mode", "float"),
        ("mode", "bool"),
    ],
)
def test_packet_file_claims_reject_numeric_type_impostors_before_host_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    impostor: str,
) -> None:
    config, hooks, runner, _manifest_sha, fixture = build_fixture(tmp_path)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    exact = manifest["files"]["payload.txt"][field]
    manifest["files"]["payload.txt"][field] = (
        float(exact) if impostor == "float" else bool(exact)
    )
    manifest_payload = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_payload)
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^packet:file-drift:payload\.txt$",
    ):
        prepare.prepare_host(
            digest(manifest_payload),
            config=config,
            hooks=hooks,
        )

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


@pytest.mark.parametrize("mutation", ["duplicate-key", "non-finite"])
def test_manifest_bound_mission_state_rejects_hostile_json_before_host_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    config, hooks, runner, _manifest_sha, fixture = build_fixture(tmp_path)
    state_path = fixture["packet"] / "MISSION_STATE.json"
    original = state_path.read_bytes()
    if mutation == "duplicate-key":
        hostile = b'{"schema":"first","schema":"second",' + original[1:]
    else:
        hostile = b'{"hostile":NaN,' + original[1:]
    state_path.write_bytes(hostile)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["MISSION_STATE.json"].update(
        {
            "sha256": digest(hostile),
            "bytes": len(hostile),
        }
    )
    manifest_payload = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_payload)
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.MissionStateStop,
        match=r"^mission-state:json:ValueError$",
    ):
        prepare.prepare_host(
            digest(manifest_payload),
            config=config,
            hooks=hooks,
        )

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("top-level-list", "mission-state:document"),
        ("missing-top-level", "mission-state:field-set"),
        ("wrong-schema", "mission-state:schema"),
        ("workspace-nested-field", "mission-state:contract"),
        ("bool-current-iteration", "mission-state:contract"),
        ("float-storage-threshold", "mission-state:contract"),
        ("missing-next-field", "mission-state:next-program-field-set"),
        ("bool-run-state", "mission-state:run-state"),
        ("action-drift", "mission-state:next-program"),
    ],
)
def test_incomplete_or_noncanonical_mission_state_stops_before_host_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    problem: str,
) -> None:
    config, hooks, runner, _manifest_sha, fixture = build_fixture(tmp_path)
    state: object = mission_state_document(prepare.EXECUTION_PHASE, "IDLE")
    if mutation == "top-level-list":
        state = [state]
    elif mutation == "missing-top-level":
        assert isinstance(state, dict)
        state.pop("paper_state")
    elif mutation == "wrong-schema":
        assert isinstance(state, dict)
        state["schema"] = "sentinel.mission_state.v0"
    elif mutation == "workspace-nested-field":
        assert isinstance(state, dict)
        state["workspace_boundary"]["unregistered"] = True
    elif mutation == "bool-current-iteration":
        assert isinstance(state, dict)
        state["current_completed_iteration"] = True
    elif mutation == "float-storage-threshold":
        assert isinstance(state, dict)
        state["storage_gate"][
            "minimum_remote_execution_filesystem_free_gib_before_gpu_launch"
        ] = 100.0
    elif mutation == "missing-next-field":
        assert isinstance(state, dict)
        state["next_program"].pop("forbidden_actions")
    elif mutation == "bool-run-state":
        assert isinstance(state, dict)
        state["run_state"] = True
    else:
        assert isinstance(state, dict)
        state["next_program"]["authorized_actions"][0] += " (changed)"
    manifest_sha = rewrite_packet_json_member(
        fixture,
        "MISSION_STATE.json",
        state,
    )
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(prepare.MissionStateStop, match=f"^{problem}$"):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert not fixture["install"].exists()
    assert not fixture["analytic"].exists()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_host_admission_pure_data_mirror_matches_canonical_state_validator() -> None:
    state_path = REPO / "scripts/mission_state.py"
    state_spec = importlib.util.spec_from_file_location(
        "sentinel_mission_state_contract_for_host_test",
        state_path,
    )
    assert state_spec is not None and state_spec.loader is not None
    state_module = importlib.util.module_from_spec(state_spec)
    state_spec.loader.exec_module(state_module)

    assert prepare.EXPECTED_MISSION_STATE_FIELDS == state_module.EXPECTED_STATE_FIELDS
    assert prepare.EXPECTED_NEXT_PROGRAM_FIELDS == state_module.EXPECTED_NEXT_PROGRAM_FIELDS
    assert prepare.EXPECTED_MISSION_STATE_COMMON == {
        "schema": state_module.EXPECTED_SCHEMA,
        "canonical_repository": state_module.CANONICAL_REPOSITORY,
        "workspace_boundary": state_module.EXPECTED_WORKSPACE_BOUNDARY,
        "trunk": "master",
        "current_completed_iteration": state_module.EXPECTED_CURRENT_COMPLETED_ITERATION,
        "current_result": state_module.EXPECTED_CURRENT_RESULT,
        "current_verdict": state_module.EXPECTED_CURRENT_VERDICT,
        "active_hypothesis": state_module.EXPECTED_ACTIVE_HYPOTHESIS,
        "claim_state": state_module.EXPECTED_CLAIM_STATE,
        "deprecated_pending_hypotheses": state_module.EXPECTED_DEPRECATED_HYPOTHESES,
        "paper_state": state_module.EXPECTED_PAPER_STATE,
        "storage_gate": state_module.EXPECTED_STORAGE_GATE,
    }
    for phase, contract in prepare.MISSION_PHASE_CONTRACTS.items():
        authorized, forbidden = state_module.PHASE_ACTION_CONTRACTS[phase]
        assert contract == {
            "run_state": state_module.PHASE_RUN_STATES[phase],
            "authorized_actions": authorized,
            "forbidden_actions": forbidden,
        }


def test_independent_packet_manifest_mismatch_is_not_a_host_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, runner, _manifest_sha, fixture = build_fixture(tmp_path)
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(prepare.PreparationError, match="packet:manifest-sha256"):
        prepare.prepare_host("f" * 64, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    assert not fixture["install"].exists()


@pytest.mark.parametrize(
    "untracked",
    [
        (),
        ("checkpoints", "stray_artifact.json"),
        ("stray_artifact.json",),
        ("bev_diversity_head.pt", "checkpoints"),
    ],
)
def test_uniad_untracked_drift_blocks_before_host_mutation(
    tmp_path: Path, untracked: tuple[str, ...]
) -> None:
    """The untracked contract must name the load-bearing symlink and reject anything else.

    An empty set is rejected too: `checkpoints` -> `ckpts` is required by the tracked config
    `base_e2e.py`, so a host missing it would pass preparation and fail the later smoke run.
    """

    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixture["uniad_untracked"] = untracked

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [f"repository:untracked:{config.uniad_repo}"]
    assert output.is_file()
    # Nothing on the host may be touched when the contract is not satisfied.
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["install"].exists()


def test_uniad_required_untracked_is_exactly_the_load_bearing_symlink() -> None:
    assert prepare.UNIAD_REQUIRED_UNTRACKED == ("checkpoints",)
    assert prepare.HostConfig().expected_uniad_untracked == ("checkpoints",)


def test_publication_authority_blocks_before_host_mutation(tmp_path: Path) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixture["github"].branch_head = "b" * 40

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["publication-authority:branch-head"]
    assert receipt["publication_authority"] is None
    assert output.is_file()
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    assert not fixture["install"].exists()


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("missing", "publication-authority:job-envelope"),
        ("duplicate", "publication-authority:required-check-set"),
        ("unexpected", "publication-authority:unexpected-check"),
        ("extra", "publication-authority:job-envelope"),
        ("pending", "publication-authority:check-not-green:check (3.10)"),
        ("wrong-workflow", "publication-authority:check-not-green:check (3.10)"),
    ],
)
def test_publication_authority_requires_exact_green_python_matrix(
    tmp_path: Path, mutation: str, problem: str
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    document = job_document(github.source_commit)
    if mutation == "missing":
        document["jobs"] = document["jobs"][:1]
        document["total_count"] = 1
    elif mutation == "duplicate":
        document["jobs"][1]["name"] = "check (3.10)"
    elif mutation == "unexpected":
        document["jobs"][1]["name"] = "unexpected green check"
    elif mutation == "extra":
        extra = dict(document["jobs"][0])
        extra["id"] = 999
        document["jobs"].append(extra)
        document["total_count"] = 3
    elif mutation == "pending":
        document["jobs"][0]["status"] = "in_progress"
        document["jobs"][0]["conclusion"] = None
    else:
        document["jobs"][0]["workflow_name"] = "untrusted"
    github.check_documents = [document]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [problem]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    job_calls = [url for url in github.calls if "/attempts/" in url and "/jobs?" in url]
    assert job_calls == [
        f"{prepare.GITHUB_API_ROOT}/actions/runs/{WORKFLOW_RUN_ID}/attempts/1/jobs?"
        f"per_page={prepare.MAX_GITHUB_JOBS}&page=1"
    ]


def test_workflow_run_number_not_ids_or_timestamps_selects_authority() -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(
            commit,
            run_id=9_999,
            suite_id=19_999,
            run_number=730,
            minute=20,
            status="completed",
            conclusion="failure",
        ),
        workflow_run_row(
            commit,
            run_id=1,
            suite_id=2,
            run_number=731,
            minute=0,
        ),
    ]
    selected = prepare._project_exact_workflow_run(workflow_document(commit, rows), commit)

    assert selected["id"] == 1
    assert selected["run_number"] == 731


def test_same_sha_validation_branch_cannot_mask_master_authority() -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(
            commit,
            run_id=1,
            suite_id=11,
            run_number=730,
            status="completed",
            conclusion="failure",
        ),
        workflow_run_row(
            commit,
            run_id=2,
            suite_id=12,
            run_number=731,
            branch="ci-validate-b14",
        ),
    ]

    with pytest.raises(prepare.PreparationError, match="workflow-run-binding"):
        prepare._project_exact_workflow_run(workflow_document(commit, rows), commit)


@pytest.mark.parametrize(
    "mutation",
    [
        "event",
        "path",
        "head",
        "workflow-id",
        "workflow-name",
        "run-url",
        "jobs-url",
    ],
)
def test_workflow_run_identity_fields_are_exact(mutation: str) -> None:
    commit = "a" * 40
    row = workflow_run_row(commit)
    if mutation == "event":
        row["event"] = "workflow_dispatch"
    elif mutation == "path":
        row["path"] = ".github/workflows/other.yml"
    elif mutation == "head":
        row["head_sha"] = "b" * 40
    elif mutation == "workflow-id":
        row["workflow_id"] += 1
    elif mutation == "workflow-name":
        row["name"] = "other"
    elif mutation == "run-url":
        row["url"] += "/hostile"
    else:
        row["jobs_url"] += "/hostile"

    with pytest.raises(prepare.PreparationError, match="workflow-run-binding"):
        prepare._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize(
    "hostile_workflow_id",
    [True, float(prepare.GITHUB_WORKFLOW_ID)],
)
def test_workflow_run_workflow_id_requires_exact_json_integer(
    hostile_workflow_id: object,
) -> None:
    commit = "a" * 40
    row = workflow_run_row(commit)
    row["workflow_id"] = hostile_workflow_id

    with pytest.raises(prepare.PreparationError, match="workflow-run-binding"):
        prepare._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize("mutation", ["noncanonical", "reversed"])
def test_workflow_run_timestamps_are_canonical_and_ordered(mutation: str) -> None:
    commit = "a" * 40
    row = workflow_run_row(commit)
    if mutation == "noncanonical":
        row["created_at"] = "2026-7-18t12:0:0z"
    else:
        row["created_at"] = github_timestamp(31)

    with pytest.raises(prepare.PreparationError, match="workflow-run-timestamp"):
        prepare._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize(
    ("status", "conclusion"),
    [("completed", "failure"), ("queued", None), ("in_progress", None)],
)
def test_latest_canonical_workflow_run_must_be_green(
    status: str, conclusion: str | None
) -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(commit, run_id=1, suite_id=11, run_number=730),
        workflow_run_row(
            commit,
            run_id=2,
            suite_id=12,
            run_number=731,
            minute=3,
            status=status,
            conclusion=conclusion,
        ),
    ]

    with pytest.raises(prepare.PreparationError, match="workflow-run-not-green"):
        prepare._project_exact_workflow_run(workflow_document(commit, rows), commit)


def test_workflow_history_accepts_exact_page_ceiling_and_rejects_truncation() -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(
            commit,
            run_id=10_000 + index,
            suite_id=20_000 + index,
            run_number=100 + index,
            minute=index * 3,
        )
        for index in range(prepare.MAX_GITHUB_WORKFLOW_RUNS)
    ]
    selected = prepare._project_exact_workflow_run(
        workflow_document(commit, rows),
        commit,
    )
    assert selected["run_number"] == 199

    truncated = {"total_count": 101, "workflow_runs": rows}
    with pytest.raises(prepare.PreparationError, match="workflow-run-envelope"):
        prepare._project_exact_workflow_run(truncated, commit)


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("missing-started", "check-timestamp"),
        ("malformed-completed", "check-timestamp"),
        ("noncanonical-time", "check-timestamp"),
        ("reversed-time", "check-timestamp"),
        ("outside-workflow", "check-timestamp"),
        ("wrong-run", "check-not-green"),
        ("wrong-attempt", "check-not-green"),
        ("wrong-head", "check-not-green"),
        ("wrong-branch", "check-not-green"),
        ("wrong-workflow", "check-not-green"),
        ("duplicate-id", "duplicate-check-id"),
    ],
)
def test_exact_attempt_jobs_fail_closed_on_hostile_bindings(
    mutation: str, problem: str
) -> None:
    commit = "a" * 40
    workflow = prepare._project_exact_workflow_run(workflow_document(commit), commit)
    document = job_document(commit)
    first, second = document["jobs"]
    if mutation == "missing-started":
        first.pop("started_at")
    elif mutation == "malformed-completed":
        first["completed_at"] = "not-a-time"
    elif mutation == "noncanonical-time":
        first["started_at"] = "2026-7-18t12:10:0z"
    elif mutation == "reversed-time":
        first["started_at"] = github_timestamp(20)
        first["completed_at"] = github_timestamp(19)
    elif mutation == "outside-workflow":
        first["started_at"] = github_timestamp(31)
        first["completed_at"] = github_timestamp(32)
    elif mutation == "wrong-run":
        first["run_id"] = WORKFLOW_RUN_ID + 1
    elif mutation == "wrong-attempt":
        first["run_attempt"] = 2
    elif mutation == "wrong-head":
        first["head_sha"] = "b" * 40
    elif mutation == "wrong-branch":
        first["head_branch"] = "ci-validate"
    elif mutation == "wrong-workflow":
        first["workflow_name"] = "other"
    else:
        second["id"] = first["id"]

    with pytest.raises(prepare.PreparationError, match=problem):
        prepare._project_exact_checks(document, commit, workflow)


@pytest.mark.parametrize(
    ("selected_run_id", "hostile_run_id"),
    [(1, True), (WORKFLOW_RUN_ID, float(WORKFLOW_RUN_ID))],
)
def test_exact_attempt_job_run_id_requires_exact_json_integer(
    selected_run_id: int,
    hostile_run_id: object,
) -> None:
    commit = "a" * 40
    workflow = prepare._project_exact_workflow_run(
        workflow_document(
            commit,
            [workflow_run_row(commit, run_id=selected_run_id)],
        ),
        commit,
    )
    document = job_document(commit, run_id=selected_run_id)
    document["jobs"][0]["run_id"] = hostile_run_id

    with pytest.raises(prepare.PreparationError, match="check-not-green"):
        prepare._project_exact_checks(document, commit, workflow)


@pytest.mark.parametrize("mutation", ["missing", "bool", "float"])
def test_exact_attempt_job_run_attempt_requires_positive_exact_json_integer(
    mutation: str,
) -> None:
    commit = "a" * 40
    workflow = prepare._project_exact_workflow_run(workflow_document(commit), commit)
    document = job_document(commit)
    if mutation == "missing":
        document["jobs"][0].pop("run_attempt")
    elif mutation == "bool":
        document["jobs"][0]["run_attempt"] = True
    else:
        document["jobs"][0]["run_attempt"] = 1.0

    with pytest.raises(prepare.PreparationError, match="check-not-green"):
        prepare._project_exact_checks(document, commit, workflow)


def test_publication_authority_rejects_wrong_tree_blob_oid_before_mutation(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    payload_path = config.repository_paths()["payload.txt"]
    payload_row = next(row for row in github.tree_rows if row["path"] == payload_path)
    payload_row["sha"] = "f" * 40

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [
        "publication-authority:tree-blob-oid:payload.txt"
    ]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_publication_authority_rejects_same_size_different_local_content(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, _manifest_sha, fixture = build_fixture(tmp_path)
    payload_path = fixture["packet"] / "payload.txt"
    original = payload_path.read_bytes()
    hostile = bytes([original[0] ^ 1]) + original[1:]
    assert len(hostile) == len(original) and hostile != original
    payload_path.write_bytes(hostile)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["payload.txt"]["sha256"] = digest(hostile)
    manifest_payload = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_payload)

    receipt, _output = prepare.prepare_host(
        digest(manifest_payload), config=config, hooks=hooks
    )

    assert receipt["problems"] == [
        "publication-authority:tree-blob-oid:payload.txt"
    ]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("missing", "publication-authority:tree-artifact-set"),
        (
            "duplicate",
            "publication-authority:duplicate-tree-path:fixture/payload.txt",
        ),
        ("bool-size", "publication-authority:tree-artifact:payload.txt"),
        ("wrong-type", "publication-authority:tree-artifact:payload.txt"),
        ("wrong-mode", "publication-authority:tree-artifact:payload.txt"),
    ],
)
def test_publication_authority_requires_exact_tree_artifact_contract(
    tmp_path: Path, mutation: str, problem: str
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    payload_path = config.repository_paths()["payload.txt"]
    payload_row = next(row for row in github.tree_rows if row["path"] == payload_path)
    if mutation == "missing":
        github.tree_rows.remove(payload_row)
    elif mutation == "duplicate":
        github.tree_rows.append(dict(payload_row))
    elif mutation == "bool-size":
        payload_row["size"] = True
    elif mutation == "wrong-type":
        payload_row["type"] = "tree"
    else:
        payload_row["mode"] = "100755"

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [problem]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("wrong-commit", "publication-authority:commit-tree"),
        ("wrong-commit-tree", "publication-authority:tree-envelope"),
        ("wrong-tree-document", "publication-authority:tree-envelope"),
        ("truncated", "publication-authority:tree-envelope"),
    ],
)
def test_publication_authority_requires_exact_commit_and_tree_envelopes(
    tmp_path: Path, mutation: str, problem: str
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    if mutation == "wrong-commit":
        github.commit_sha = "b" * 40
    elif mutation == "wrong-commit-tree":
        github.commit_tree_sha = "d" * 40
    elif mutation == "wrong-tree-document":
        github.tree_document_sha = "d" * 40
    else:
        github.tree_truncated = True

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [problem]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_master_tip_is_rechecked_immediately_before_first_host_mutation(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixture["github"].branch_heads = ["a" * 40, "b" * 40]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == ["publication-authority:branch-recheck"]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_master_tip_is_rechecked_again_immediately_before_green_verdict(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixture["github"].branch_heads = [
        "a" * 40,
        "a" * 40,
        "a" * 40,
        "b" * 40,
    ]

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["publication-authority:branch-recheck"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir()


def test_terminal_check_replay_blocks_first_mutation_with_stable_master(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    fixture["server"].write_bytes(fixture["baseline"])
    github = fixture["github"]
    github.check_documents = [
        check_document(github.source_commit),
        check_document(
            github.source_commit,
            ids=(410, 411),
            status="in_progress",
            conclusion=None,
        ),
    ]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [
        "publication-authority:terminal:check-not-green:check (3.10)"
    ]
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_workflow_rerun_started_during_initial_authority_proof_fails_closed(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    github.workflow_documents = [
        workflow_document(github.source_commit),
        workflow_document(
            github.source_commit,
            [workflow_run_row(github.source_commit, run_attempt=2)],
        ),
    ]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == ["publication-authority:workflow-run-replay"]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_workflow_rerun_started_during_terminal_authority_proof_fails_closed(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    github.workflow_documents = [
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(
            github.source_commit,
            [workflow_run_row(github.source_commit, run_attempt=2)],
        ),
    ]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [
        "publication-authority:terminal:workflow-run-replay"
    ]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_workflow_rerun_started_during_host_mutation_blocks_green_receipt(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    github.workflow_documents = [
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(github.source_commit),
        workflow_document(
            github.source_commit,
            [workflow_run_row(github.source_commit, run_attempt=2)],
        ),
    ]

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [
        "publication-authority:terminal:workflow-run-replay"
    ]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir()


def test_final_green_check_rotation_is_persisted_in_host_receipt(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    github.check_documents = [
        check_document(github.source_commit),
        check_document(github.source_commit, ids=(410, 411)),
        check_document(github.source_commit, ids=(510, 511)),
    ]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.READY_VERDICT
    assert [row["id"] for row in receipt["publication_authority"]["checks"]] == [
        510,
        511,
    ]


def test_packet_payloads_are_revalidated_before_and_after_atomic_install(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def mutate_before_install(label: str, _path: Path) -> None:
        if label == "compose":
            (fixture["packet"] / "payload.txt").write_text("raced before install\n")

    receipt, _output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, before_replace=mutate_before_install),
    )

    assert receipt["problems"] == ["packet:revalidation:pre-install:payload.txt"]
    assert not fixture["install"].exists()

    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path / "post-install")

    def mutate_after_rename(source: Path, destination: Path) -> None:
        source.rename(destination)
        (destination / "payload.txt").write_text("raced after install\n")

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, rename=mutate_after_rename),
    )

    assert receipt["problems"] == ["packet:revalidation:post-install:payload.txt"]
    assert output == fixture["install"] / prepare.RECEIPT_NAME
    assert output.is_file()
    assert not any(
        action["action"] == "atomically_install_verified_packet"
        for action in receipt["actions"]
    )


def test_unsanitized_marker_cannot_bypass_invocation_gate_or_leak_environment(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    secret = "do-not-log-this-secret-value"
    hostile_environment = {
        **prepare._SAFE_ENVIRONMENT,
        "SENTINEL_I135_PREPARE_SANITIZED": "1",
        "PRIVATE_TOKEN": secret,
    }

    receipt, _output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, environment=lambda: hostile_environment),
    )

    assert receipt["problems"] == ["invocation:environment"]
    assert receipt["invocation"]["environment_matches"] is False
    assert secret not in json.dumps(receipt)
    assert fixture["github"].calls == []
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_staged_repository_change_blocks_before_any_host_mutation(tmp_path: Path) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    runner.staged["uniad"] = ["inference/server.py"]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == [f"repository:staged:{config.uniad_repo}"]
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_compose_open_race_fails_closed_and_preserves_partial_action_evidence(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)

    def race(label: str, path: Path) -> None:
        if label == "compose":
            path.write_bytes(b"hostile replacement\n")

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, before_replace=race),
    )

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["compose:preimage-race"]
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == b"hostile replacement\n"
    assert output.is_file()
    assert not fixture["analytic"].exists()
    assert not fixture["install"].exists()


def test_lock_or_staging_residue_is_never_deleted_or_bypassed(tmp_path: Path) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    residue = fixture["forbidden"][-1]
    residue.write_text("retain me\n")

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["host:forbidden-path-present"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert json.loads(output.read_bytes()) == receipt
    assert residue.read_text() == "retain me\n"
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_packet_extra_file_and_symlink_fail_before_preparation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    (fixture["packet"] / "unregistered.py").write_text("bad\n")
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(prepare.PreparationError, match="packet:root-entry-set"):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert not fixture["analytic"].exists()


@pytest.mark.parametrize("mutation", ["duplicate-key", "non-finite"])
def test_packet_manifest_strict_json_rejects_hostile_documents_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    config, hooks, runner, _manifest_sha, fixture = build_fixture(tmp_path)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    original = manifest_path.read_bytes()
    if mutation == "duplicate-key":
        hostile = b'{"schema":"first","schema":"second",' + original[1:]
    else:
        hostile = b'{"hostile":NaN,' + original[1:]
    manifest_path.write_bytes(hostile)
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.PreparationError, match="packet:manifest-json:ValueError"
    ):
        prepare.prepare_host(digest(hostile), config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_packet_member_symlink_is_rejected_even_when_manifest_name_set_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    payload = fixture["packet"] / "payload.txt"
    replacement = tmp_path.resolve() / "replacement.txt"
    replacement.write_bytes(payload.read_bytes())
    payload.unlink()
    payload.symlink_to(replacement)
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.PreparationError,
        match="file:not-physical",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert not fixture["analytic"].exists()


def test_storage_drop_on_second_snapshot_stops_install_and_is_preserved(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    calls = 0

    def falling_free(_path: Path) -> int:
        nonlocal calls
        calls += 1
        return 1_000 if calls == 1 else 149

    receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=replace(hooks, disk_free=falling_free),
    )

    assert receipt["problems"] == ["storage:minimum-free"]
    assert output.is_file()
    assert fixture["server"].read_bytes() == fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_after"]
    assert fixture["analytic"].is_dir()
    assert not fixture["install"].exists()


@pytest.mark.parametrize(
    "field",
    [
        "expected_server_bytes",
        "expected_compose_input_bytes",
        "expected_compose_output_bytes",
        "minimum_remote_free_bytes",
        "projected_output_bytes",
        "minimum_reserve_bytes",
    ],
)
@pytest.mark.parametrize(
    "mutation_kind",
    ["bool", "integral-float", "zero", "negative"],
)
def test_numeric_host_config_aliases_and_nonpositive_values_fail_before_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    mutation_kind: str,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    honest = getattr(config, field)
    mutation = {
        "bool": True,
        "integral-float": float(honest),
        "zero": 0,
        "negative": -1,
    }[mutation_kind]
    config = replace(config, **{field: mutation})
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^config:numeric-contract$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    assert not fixture["install"].exists()


def test_storage_capacity_config_invariant_fails_before_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)
    config = replace(
        config,
        minimum_remote_free_bytes=149,
        projected_output_bytes=100,
        minimum_reserve_bytes=50,
    )
    hooks = no_host_attempt_hooks(hooks)
    prohibit_host_attempt_construction(monkeypatch)

    with pytest.raises(
        prepare.PreparationError,
        match=r"^config:storage-capacity-contract$",
    ):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert fixture["github"].calls == []
    assert runner.calls == []
    assert not (fixture["packet"] / prepare.RECEIPT_NAME).exists()
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    assert not fixture["install"].exists()


def test_red_attempt_makes_packet_nonretriable_and_is_never_overwritten(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    hostile_environment = {**prepare._SAFE_ENVIRONMENT, "UNEXPECTED": "1"}
    hooks = replace(hooks, environment=lambda: hostile_environment)

    _receipt, output = prepare.prepare_host(
        manifest_sha,
        config=config,
        hooks=hooks,
    )
    original = output.read_bytes()

    with pytest.raises(prepare.PreparationError, match="packet:root-entry-set"):
        prepare.prepare_host(manifest_sha, config=config, hooks=hooks)
    assert output.read_bytes() == original
    assert fixture["server"].read_bytes() != fixture["baseline"]


def test_production_packet_inventory_is_exact_and_includes_launch_authorizer() -> None:
    assert len(prepare.REQUIRED_PACKET_FILES) == 19
    assert set(prepare.REQUIRED_PACKET_FILES) == {
        "MISSION_STATE.json",
        *prepare.ITER135_PAYLOAD_NAMES,
        "tooling_verification_receipt.json",
        "prepare_host135.py",
    }
    assert "authorize_launch135.py" in prepare.REQUIRED_PACKET_FILES
    assert "host_packet_manifest.json" not in prepare.REQUIRED_PACKET_FILES
    assert prepare.EXPECTED_PACKET_MODES["prepare_host135.py"] == 0o755
    assert prepare.EXPECTED_PACKET_MODES["authorize_launch135.py"] == 0o644
    assert prepare.PACKET_REPOSITORY_PATHS == {
        name: (
            "MISSION_STATE.json"
            if name == "MISSION_STATE.json"
            else f"{prepare.EXPERIMENT_REPOSITORY_ROOT}/{name}"
        )
        for name in prepare.REQUIRED_PACKET_FILES
    }
