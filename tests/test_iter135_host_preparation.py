from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
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


def build_fixture(tmp_path: Path) -> tuple[prepare.HostConfig, prepare.Hooks, FakeRunner, str, dict]:
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

    required = ("prepare_host135.py", "patch_compose_dose_env.py", "payload.txt")
    modes = {
        "prepare_host135.py": 0o755,
        "patch_compose_dose_env.py": 0o644,
        "payload.txt": 0o644,
    }
    repository_paths = {name: f"fixture/{name}" for name in required}
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


def test_green_preparation_is_exact_one_shot_and_never_touches_runtime(
    tmp_path: Path,
) -> None:
    config, hooks, runner, manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.READY_VERDICT
    assert receipt["problem_count"] == 0
    assert receipt["problems"] == []
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


def test_independent_packet_manifest_mismatch_preserves_red_attempt_without_mutation(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, _manifest_sha, fixture = build_fixture(tmp_path)

    receipt, output = prepare.prepare_host("f" * 64, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["packet:manifest-sha256"]
    assert output == fixture["packet"] / prepare.RECEIPT_NAME
    assert output.is_file()
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
    assert receipt["actions"][-1]["action"] == "atomically_install_verified_packet"


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

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == ["host:forbidden-path-present"]
    assert residue.read_text() == "retain me\n"
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]


def test_packet_extra_file_and_symlink_fail_before_preparation(tmp_path: Path) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    (fixture["packet"] / "unregistered.py").write_text("bad\n")

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == ["packet:root-entry-set"]
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert not fixture["analytic"].exists()


@pytest.mark.parametrize("mutation", ["duplicate-key", "non-finite"])
def test_packet_manifest_strict_json_rejects_hostile_documents_before_mutation(
    tmp_path: Path, mutation: str
) -> None:
    config, hooks, _runner, _manifest_sha, fixture = build_fixture(tmp_path)
    manifest_path = fixture["packet"] / prepare.PACKET_MANIFEST_NAME
    original = manifest_path.read_bytes()
    if mutation == "duplicate-key":
        hostile = b'{"schema":"first","schema":"second",' + original[1:]
    else:
        hostile = b'{"hostile":NaN,' + original[1:]
    manifest_path.write_bytes(hostile)

    receipt, _output = prepare.prepare_host(
        digest(hostile), config=config, hooks=hooks
    )

    assert receipt["problems"] == ["packet:manifest-json:ValueError"]
    assert fixture["server"].read_bytes() != fixture["baseline"]
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()


def test_packet_member_symlink_is_rejected_even_when_manifest_name_set_is_exact(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    payload = fixture["packet"] / "payload.txt"
    replacement = tmp_path.resolve() / "replacement.txt"
    replacement.write_bytes(payload.read_bytes())
    payload.unlink()
    payload.symlink_to(replacement)

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [f"file:not-physical:{payload}"]
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


def test_red_attempt_is_never_overwritten_by_a_retry(tmp_path: Path) -> None:
    config, hooks, _runner, _manifest_sha, fixture = build_fixture(tmp_path)

    _receipt, output = prepare.prepare_host("f" * 64, config=config, hooks=hooks)
    original = output.read_bytes()

    with pytest.raises(prepare.PreparationError, match="receipt:already-exists"):
        prepare.prepare_host("f" * 64, config=config, hooks=hooks)
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
