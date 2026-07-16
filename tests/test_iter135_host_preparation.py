from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
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
        self.app_slug = "github-actions"
        self.names = list(prepare.REQUIRED_GITHUB_CHECKS)
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
        if "/check-runs?" in url:
            if self.check_documents:
                return self.check_documents.pop(0)
            rows = [
                {
                    "name": name,
                    "id": 310 + index,
                    "status": self.status,
                    "conclusion": self.conclusion,
                    "head_sha": self.source_commit,
                    "app": {"slug": self.app_slug},
                }
                for index, name in enumerate(self.names)
            ]
            return {"total_count": len(rows), "check_runs": rows}
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
    return {
        "total_count": 2,
        "check_runs": [
            {
                "name": name,
                "id": check_id,
                "status": status,
                "conclusion": conclusion,
                "head_sha": commit,
                "app": {"slug": "github-actions"},
            }
            for name, check_id in zip(prepare.REQUIRED_GITHUB_CHECKS, ids)
        ],
    }


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
    checks_url = (
        f"{prepare.GITHUB_API_ROOT}/commits/{github.source_commit}/check-runs?"
        "filter=latest&per_page=100&page=1"
    )
    assert github.calls == [
        branch_url,
        checks_url,
        f"{prepare.GITHUB_API_ROOT}/git/commits/{github.source_commit}",
        f"{prepare.GITHUB_API_ROOT}/git/trees/{github.tree_sha}?recursive=1",
        branch_url,
        checks_url,
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
        ("missing", "publication-authority:check-run-envelope"),
        ("duplicate", "publication-authority:duplicate-check:check (3.10)"),
        ("unexpected", "publication-authority:unexpected-check"),
        ("extra", "publication-authority:check-run-envelope"),
        ("pending", "publication-authority:check-not-green:check (3.10)"),
        ("wrong-app", "publication-authority:check-not-green:check (3.10)"),
    ],
)
def test_publication_authority_requires_exact_green_python_matrix(
    tmp_path: Path, mutation: str, problem: str
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    if mutation == "missing":
        github.names = ["check (3.10)"]
    elif mutation == "duplicate":
        github.names = ["check (3.10)", "check (3.10)"]
    elif mutation == "unexpected":
        github.names = ["check (3.10)", "unexpected green check"]
    elif mutation == "extra":
        github.names = [*prepare.REQUIRED_GITHUB_CHECKS, "unexpected green check"]
    elif mutation == "pending":
        github.status = "in_progress"
        github.conclusion = None
    else:
        github.app_slug = "untrusted-check-app"

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["problems"] == [problem]
    assert fixture["server"].read_bytes() == b"residual server\n"
    assert fixture["compose"].read_bytes() == fixture["compose_before"]
    assert not fixture["analytic"].exists()
    checks_calls = [url for url in github.calls if "/check-runs?" in url]
    assert checks_calls == [
        f"{prepare.GITHUB_API_ROOT}/commits/{github.source_commit}/check-runs?"
        "filter=latest&per_page=100&page=1"
    ]


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
    fixture["github"].branch_heads = ["a" * 40, "a" * 40, "b" * 40]

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


def test_terminal_green_check_rotation_is_persisted_in_host_receipt(
    tmp_path: Path,
) -> None:
    config, hooks, _runner, manifest_sha, fixture = build_fixture(tmp_path)
    github = fixture["github"]
    github.check_documents = [
        check_document(github.source_commit),
        check_document(github.source_commit, ids=(410, 411)),
    ]

    receipt, _output = prepare.prepare_host(manifest_sha, config=config, hooks=hooks)

    assert receipt["verdict"] == prepare.READY_VERDICT
    assert [row["id"] for row in receipt["publication_authority"]["checks"]] == [
        410,
        411,
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
