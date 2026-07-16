from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import subprocess
import sys
import urllib.parse
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


REPO = Path(__file__).resolve().parents[1]
ITER135 = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"
MODULE_PATH = ITER135 / "capture_environment135.py"
HOST_COMMIT = "d" * 40
SPEC = importlib.util.spec_from_file_location("iter135_environment_capture", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
capture = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = capture
SPEC.loader.exec_module(capture)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("payload", [b"", b"host authority\n", bytes(range(256))])
def test_host_authority_git_blob_oid_matches_git_hash_object(payload: bytes) -> None:
    expected = subprocess.run(
        ["git", "hash-object", "--stdin"],
        input=payload,
        check=True,
        capture_output=True,
    ).stdout.decode().strip()

    assert capture._git_blob_oid(payload) == expected


def nul_rows(rows: list[str]) -> bytes:
    return b"" if not rows else b"\0".join(row.encode() for row in rows) + b"\0"


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.repositories: dict[str, dict[str, Any]] = {}
        self.images: dict[str, dict[str, Any]] = {}
        self.gpu_row = (
            f"{capture.EXPECTED_GPU_MODEL}, {capture.EXPECTED_GPU_UUID}, "
            f"{capture.EXPECTED_GPU_DRIVER}, {capture.EXPECTED_GPU_MEMORY_MIB}\n"
        ).encode()
        self.compute = b""
        self.containers = b""
        self.processes = b"500 1 python capture_environment135.py\n1 0 /sbin/init\n"
        self.mount = {
            "target": None,
            "source": "/dev/test-evidence",
            "fstype": "ext4",
            "uuid": "11111111-2222-3333-4444-555555555555",
        }
        self.fail_prefix: str | None = None
        self.docker_version = {
            "Client": {
                "Version": "28.3.2",
                "ApiVersion": "1.51",
                "GitCommit": "clientcommit",
                "GoVersion": "go1.24.5",
                "Os": "linux",
                "Arch": "amd64",
                "BuildTime": "2026-07-01T00:00:00Z",
                "Context": "default",
            },
            "Server": {
                "Platform": {"Name": "Docker Engine - Community"},
                "Version": "28.3.2",
                "ApiVersion": "1.51",
                "MinAPIVersion": "1.24",
                "GitCommit": "servercommit",
                "GoVersion": "go1.24.5",
                "Os": "linux",
                "Arch": "amd64",
                "BuildTime": "2026-07-01T00:00:00Z",
                "Experimental": False,
            },
        }
        self.docker_info = {
            "ID": "daemon-id",
            "Name": capture.EXPECTED_HOST,
            "ServerVersion": "28.3.2",
            "DockerRootDir": "/var/lib/docker",
            "Driver": "overlay2",
            "OperatingSystem": "Ubuntu 24.04.2 LTS",
            "OSType": "linux",
            "Architecture": "amd64",
            "NCPU": 16,
            "MemTotal": 67_108_864_000,
            "KernelVersion": "6.8.0-test",
            "CgroupDriver": "systemd",
            "CgroupVersion": "2",
        }

    def __call__(self, argv: list[str] | tuple[str, ...]) -> bytes:
        command = tuple(argv)
        self.calls.append(command)
        if self.fail_prefix is not None and (
            command[0] == self.fail_prefix or Path(command[0]).name == self.fail_prefix
        ):
            raise capture.CaptureError(f"injected:{self.fail_prefix}")
        if command[0] == "git":
            repo = command[command.index("-C") + 1]
            args = command[command.index("-C") + 2 :]
            state = self.repositories[repo]
            if args == ("rev-parse", "--show-toplevel"):
                return f"{repo}\n".encode()
            if args == ("rev-parse", "HEAD"):
                return f"{state['head']}\n".encode()
            if args == ("diff", "--cached", "--name-only", "-z"):
                return nul_rows(state["staged"])
            if args == ("diff", "--name-only", "-z"):
                return nul_rows(state["dirty"])
            if args == ("ls-files", "--others", "--exclude-standard", "-z"):
                return nul_rows(state["untracked"])
        if Path(command[0]).name == "docker" and command[1:3] == ("image", "inspect"):
            return json.dumps([self.images[command[3]]]).encode()
        if Path(command[0]).name == "docker" and command[1:] == ("ps", "-aq", "--no-trunc"):
            return self.containers
        if Path(command[0]).name == "docker" and command[1:] == (
            "version",
            "--format",
            "{{json .}}",
        ):
            return json.dumps(self.docker_version).encode()
        if Path(command[0]).name == "docker" and command[1:] == (
            "info",
            "--format",
            "{{json .}}",
        ):
            return json.dumps(self.docker_info).encode()
        if Path(command[0]).name == "docker" and command[1:] == ("context", "show"):
            return b"default\n"
        if Path(command[0]).name == "docker" and command[1:5] == (
            "context",
            "inspect",
            "--format",
            "{{json .Endpoints.docker.Host}}",
        ):
            return json.dumps("unix:///var/run/docker.sock").encode()
        if command[0] == "nvidia-smi" and "--query-gpu=" in command[1]:
            return self.gpu_row
        if command[0] == "nvidia-smi" and "--query-compute-apps=pid" in command:
            return self.compute
        if command == ("ps", "-eo", "pid=,ppid=,args="):
            return self.processes
        if command[0] == "findmnt":
            return json.dumps({"filesystems": [self.mount]}).encode()
        raise AssertionError(f"unexpected command: {command}")


class FakeGitHub:
    def __init__(self, artifacts: dict[str, bytes]) -> None:
        self.branch_head = HOST_COMMIT
        self.branch_heads: list[str] = []
        self.status = "completed"
        self.conclusion = "success"
        self.app_slug = "github-actions"
        self.artifacts = dict(artifacts)
        self.parent_commit = "a" * 40
        self.commit_sha = HOST_COMMIT
        self.tree_sha = "d" * 40
        self.tree_document_sha = self.tree_sha
        self.tree_truncated = False
        self.tree_rows = [
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": capture._git_blob_oid(payload),
                "size": len(payload),
            }
            for path, payload in sorted(self.artifacts.items())
        ]
        self.changed_paths = list(capture.HOST_PUBLICATION_ARTIFACT_PATHS)
        self.previous_filename: str | None = None
        self.names = list(capture.REQUIRED_GITHUB_CHECKS)
        self.check_documents: list[dict[str, Any]] = []
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
                    "id": 410 + index,
                    "status": self.status,
                    "conclusion": self.conclusion,
                    "head_sha": HOST_COMMIT,
                    "app": {"slug": self.app_slug},
                }
                for index, name in enumerate(self.names)
            ]
            return {"total_count": len(rows), "check_runs": rows}
        if f"/commits/{HOST_COMMIT}?" in url:
            files = [{"filename": path} for path in self.changed_paths]
            if self.previous_filename is not None and files:
                files[0]["previous_filename"] = self.previous_filename
            return {
                "sha": self.commit_sha,
                "parents": [{"sha": self.parent_commit}],
                "files": files,
                "commit": {"tree": {"sha": self.tree_sha}},
            }
        if "/git/trees/" in url:
            return {
                "sha": self.tree_document_sha,
                "truncated": self.tree_truncated,
                "tree": list(self.tree_rows),
            }
        if "/contents/" in url:
            encoded_path = url.split("/contents/", 1)[1].split("?", 1)[0]
            path = urllib.parse.unquote(encoded_path)
            payload = self.artifacts[path]
            return {
                "type": "file",
                "path": path,
                "sha": capture._git_blob_oid(payload),
                "encoding": "base64",
                "size": len(payload),
                "content": base64.b64encode(payload).decode(),
            }
        raise AssertionError(f"unexpected GitHub URL: {url}")


def check_document(
    commit: str,
    *,
    ids: tuple[int, int] = (410, 411),
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
            for name, check_id in zip(capture.REQUIRED_GITHUB_CHECKS, ids)
        ],
    }


@pytest.mark.parametrize(
    ("final_url", "content_type", "problem"),
    [
        (
            "https://api.github.com/repos/manfromnowhere143/sentinel/redirected",
            "application/json",
            "host-publication-authority:redirect",
        ),
        (
            None,
            "text/html",
            "host-publication-authority:content-type",
        ),
    ],
)
def test_github_transport_rejects_redirect_and_non_json(
    monkeypatch: pytest.MonkeyPatch,
    final_url: str | None,
    content_type: str,
    problem: str,
) -> None:
    requested = f"{capture.GITHUB_API_ROOT}/branches/master"

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

    monkeypatch.setattr(capture.urllib.request, "build_opener", build_opener)

    with pytest.raises(capture.CaptureError, match=problem):
        capture._fetch_json(requested)
    assert any(
        isinstance(handler, capture.urllib.request.ProxyHandler)
        and handler.proxies == {}
        for handler in handlers
    )


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":-Infinity}'])
def test_github_transport_rejects_duplicate_and_nonfinite_json(
    monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    requested = f"{capture.GITHUB_API_ROOT}/branches/master"

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
        capture.urllib.request, "build_opener", lambda *_handlers: Opener()
    )
    with pytest.raises(capture.CaptureError, match="host-publication-authority:json"):
        capture._fetch_json(requested)


def patch_constants() -> dict[str, str]:
    names = {
        "ANCHOR",
        "REPLACEMENT",
        "OUTPUT_DECLARATION_ANCHOR",
        "OUTPUT_DECLARATION_REPLACEMENT",
        "OUTPUT_MOUNT_ANCHOR",
        "OUTPUT_MOUNT_REPLACEMENT",
        "OUTPUT_LOG_ANCHOR",
        "OUTPUT_LOG_REPLACEMENT",
    }
    return capture._literal_assignments((ITER135 / "patch_compose_dose_env.py").read_bytes(), names)


def compose_pair() -> tuple[bytes, bytes]:
    values = patch_constants()
    source = (
        "#!/bin/bash\n"
        + values["OUTPUT_DECLARATION_ANCHOR"]
        + "renderer block\n"
        + "if [ $SHOULD_START_MODEL == true ]; then\n"
        + "docker run "
        + values["ANCHOR"]
        + "-e SENTINEL_TTC model\n"
        + "docker run --rm --gpus all \\\n"
        + values["OUTPUT_MOUNT_ANCHOR"]
        + values["OUTPUT_LOG_ANCHOR"]
    )
    final = source
    for anchor_name, replacement_name in (
        ("ANCHOR", "REPLACEMENT"),
        ("OUTPUT_DECLARATION_ANCHOR", "OUTPUT_DECLARATION_REPLACEMENT"),
        ("OUTPUT_MOUNT_ANCHOR", "OUTPUT_MOUNT_REPLACEMENT"),
        ("OUTPUT_LOG_ANCHOR", "OUTPUT_LOG_REPLACEMENT"),
    ):
        final = final.replace(values[anchor_name], values[replacement_name], 1)
    return source.encode(), final.encode()


def fixture(
    tmp_path: Path,
) -> tuple[capture.Contract, capture.Hooks, FakeRunner, dict[str, Path]]:
    root = tmp_path.resolve()
    files = root / "files"
    files.mkdir(parents=True)
    repositories = {
        "uniad": root / "UniAD",
        "neuroncap": root / "NeuroNCAP",
        "neurad": root / "neurad-studio",
    }
    for path in repositories.values():
        path.mkdir()
    backup = repositories["neurad"] / "Dockerfile.bak"
    backup.write_bytes(b"frozen backup\n")
    source, final = compose_pair()
    patcher_source = (ITER135 / "patch_compose_dose_env.py").read_text()
    patcher_source = patcher_source.replace(
        "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d",
        digest(source),
    ).replace(
        "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada",
        digest(final),
    )
    patcher_path = files / "patcher.py"
    patcher_path.write_text(patcher_source)
    compose_path = files / "_docker_compose_release.sh"
    compose_path.write_bytes(final)
    payload_path = files / "runtime.py"
    payload_path.write_bytes(b"print('runtime')\n")
    docker_client = files / "docker"
    docker_client.write_bytes(b"#!/bin/sh\nexit 0\n")
    docker_client.chmod(0o755)

    mount = root / "evidence-mount"
    mount.mkdir()
    output = mount / "sentinel-i135-outoutput"
    output.mkdir()
    archive_root = mount / "archives"
    metadata_root = mount / "v1.0-trainval"
    map_root = mount / "maps"
    archive_root.mkdir()
    metadata_root.mkdir()
    map_root.mkdir()
    archive_contract = {
        "v1.0-trainval_meta.tgz": ("4" * 64, 461_678_030),
        "v1.0-trainval01_blobs.tgz": ("5" * 64, 31_579_122_687),
    }
    for name in archive_contract:
        (archive_root / name).write_bytes(f"test fixture for {name}\n".encode())
    metadata_names = ("scene.json", "sample.json")
    for name in metadata_names:
        (metadata_root / name).write_text(json.dumps({"fixture": name}) + "\n")
    map_names = ("36092f0b03a857c6a3403e25b4b7aab3.png",)
    for name in map_names:
        (map_root / name).write_bytes(f"fixture:{name}\n".encode())
    expected_repositories = {
        "uniad": {
            "path": str(repositories["uniad"]),
            "head": "a" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["shim.py"],
            "required_untracked_paths": [],
        },
        "neuroncap": {
            "path": str(repositories["neuroncap"]),
            "head": "b" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["docker/Dockerfile", "scripts/compose.sh"],
            "required_untracked_paths": [],
        },
        "neurad": {
            "path": str(repositories["neurad"]),
            "head": "c" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["Dockerfile"],
            "required_untracked_paths": ["Dockerfile.bak"],
        },
    }
    image_ids = {
        "ncap:latest": "sha256:" + "1" * 64,
        "neurad:latest": "sha256:" + "2" * 64,
        "uniad:latest": "sha256:" + "3" * 64,
    }
    contract = capture.Contract(
        schema="iter135.environment_receipts.test.v1",
        ready_verdict="I135_ENVIRONMENT_PREFLIGHT_OK",
        remote_files={
            "compose_script": (str(compose_path), digest(final), len(final)),
            "neurad_dockerfile_backup": (
                str(backup),
                digest(backup.read_bytes()),
                backup.stat().st_size,
            ),
            "runtime": (
                str(payload_path),
                digest(payload_path.read_bytes()),
                payload_path.stat().st_size,
            ),
        },
        repositories=expected_repositories,
        required_untracked_bindings={("neurad", "Dockerfile.bak"): "neurad_dockerfile_backup"},
        storage_identity={
            "filesystem_path": str(output),
            "filesystem_realpath": str(output),
            "filesystem_is_symlink": False,
            "filesystem_empty": True,
            "mount_target": str(mount),
            "mount_source": "/dev/test-evidence",
            "mount_fstype": "ext4",
            "mount_uuid": "11111111-2222-3333-4444-555555555555",
        },
        dataset_schema="iter135.nuscenes_dataset_receipt.test.v1",
        dataset_contract_sha256="",
        dataset_root=str(mount),
        dataset_version="v1.0-trainval",
        dataset_archive_root=str(archive_root),
        dataset_metadata_root=str(metadata_root),
        dataset_map_root=str(map_root),
        dataset_mount={
            "mount_target": str(mount),
            "mount_source": "/dev/test-evidence",
            "mount_fstype": "ext4",
            "mount_uuid": "11111111-2222-3333-4444-555555555555",
        },
        dataset_proof_basis={
            "iteration": 28,
            "result_path": "fixture/RESULT.md",
            "receipt_directory": "fixture/uploads",
            "archive_count": 2,
            "archive_total_bytes": sum(row[1] for row in archive_contract.values()),
        },
        dataset_archives=archive_contract,
        dataset_metadata_files=metadata_names,
        dataset_map_anchors=map_names,
        image_ids=image_ids,
        compose_input_sha256=digest(source),
        compose_output_sha256=digest(final),
        projected_output_bytes=100,
        minimum_remote_free_bytes=200,
        minimum_reserve_bytes=50,
        minimum_local_free_bytes=150,
    )
    contract = replace(
        contract,
        dataset_contract_sha256=capture._canonical_json_sha256(
            capture._dataset_contract_payload(contract)
        ),
    )
    runner = FakeRunner()
    runner.mount["target"] = str(mount)
    for repo_id, expected in expected_repositories.items():
        runner.repositories[expected["path"]] = {
            "head": expected["head"],
            "staged": list(expected["staged_paths"]),
            "dirty": list(expected["dirty_tracked_paths"]),
            "untracked": (
                ["outoutput/old/run_0/metrics.json"]
                if repo_id == "neuroncap"
                else list(expected["required_untracked_paths"])
            ),
        }
    for name, image_id in image_ids.items():
        runner.images[name] = {
            "Id": image_id,
            "RepoDigests": [f"{name.rsplit(':', 1)[0]}@{image_id}"],
        }
    runner.images["ncap:latest"]["RepoDigests"] = []
    runner.images["neurad:latest"]["RepoDigests"] = [
        "neurad@sha256:" + "e" * 64,
        "neurad@sha256:" + "d" * 64,
    ]
    fixed_time = datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc)

    preparation_source_commit = "a" * 40
    preparation_authority = {
        "schema": capture.PUBLICATION_AUTHORITY_SCHEMA,
        "repository": capture.GITHUB_REPOSITORY,
        "branch": capture.GITHUB_BRANCH,
        "source_commit": preparation_source_commit,
        "branch_head_sha": preparation_source_commit,
        "required_checks": list(capture.REQUIRED_GITHUB_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 310 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": preparation_source_commit,
                "app_slug": capture.EXPECTED_CHECK_APP,
            }
            for index, name in enumerate(capture.REQUIRED_GITHUB_CHECKS)
        ],
        "artifacts": [],
        "verified": True,
    }
    preparation_evidence = {
        "schema": capture.EXPECTED_PREPARATION_SCHEMA,
        "verdict": capture.EXPECTED_PREPARATION_VERDICT,
        "publication_authority": preparation_authority,
        "packet": {"source_commit": preparation_source_commit},
    }
    preparation_payload = (
        json.dumps(preparation_evidence, indent=1, sort_keys=True) + "\n"
    ).encode()
    packet_payload = b'{"schema":"iter135.host_packet_manifest.test.v1"}\n'
    host_artifacts = {
        capture.HOST_PUBLICATION_ARTIFACT_PATHS[0]: packet_payload,
        capture.HOST_PUBLICATION_ARTIFACT_PATHS[1]: preparation_payload,
    }
    github = FakeGitHub(host_artifacts)

    def dataset_read(path: Path) -> tuple[dict[str, Any], list[str]]:
        if path.parent == archive_root:
            archive_sha256, archive_bytes = contract.dataset_archives[path.name]
            return {
                "path": str(path),
                "sha256": archive_sha256,
                "bytes": archive_bytes,
            }, []
        return capture._read_dataset_file(path)

    hooks = capture.Hooks(
        run=runner,
        fetch_json=github,
        hostname=lambda: capture.EXPECTED_HOST,
        disk_free=lambda _path: 1_000,
        device=lambda path: 1 if path == Path("/") else 2,
        now=lambda: fixed_time,
        pid=lambda: 500,
        dataset_read=dataset_read,
        interpreter_receipt=lambda: (
            {
                "invocation_path": "/usr/bin/python3.10",
                "physical_path": "/usr/bin/python3.10",
                "realpath": "/usr/bin/python3.10",
                "sha256": "8" * 64,
                "bytes": 6_000_000,
                "version": "3.10.14",
                "implementation": "CPython",
            },
            [],
        ),
        invocation_receipt=lambda: (
            {
                "sanitized": True,
                "isolated": True,
                "environment": dict(capture.SANITIZED_ENVIRONMENT),
                "argv": [
                    "/usr/bin/python3.10",
                    "-I",
                    str(capture.CANONICAL_MANIFEST_PATH.parent / "capture_environment135.py"),
                    "--local-free-bytes",
                    "500",
                ],
                "canonical_script": str(
                    capture.CANONICAL_MANIFEST_PATH.parent / "capture_environment135.py"
                ),
            },
            [],
        ),
        preparation_receipt=lambda: (
            {
                "receipt_file": {
                    "path": "/opt/sentinel-stack/iter135/host_preparation_receipt.json",
                    "sha256": digest(preparation_payload),
                    "bytes": len(preparation_payload),
                },
                "evidence": preparation_evidence,
            },
            [],
        ),
        host_artifact_payloads=lambda: (dict(host_artifacts), []),
        docker_client_path=lambda: docker_client,
    )
    return (
        contract,
        hooks,
        runner,
        {
            "output": output,
            "mount": mount,
            "payload": payload_path,
            "compose": compose_path,
            "backup": backup,
            "patcher": patcher_path,
            "docker": docker_client,
            "github": github,
            "host_artifacts": host_artifacts,
            "dataset_root": mount,
            "archive_root": archive_root,
            "metadata_root": metadata_root,
            "map_root": map_root,
        },
    )


def run_capture(
    contract: capture.Contract,
    hooks: capture.Hooks,
    *,
    local_free_bytes: int = 500,
) -> dict[str, Any]:
    patcher_path = Path(contract.remote_files["compose_script"][0]).parent / "patcher.py"
    return capture.capture_environment(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=local_free_bytes,
        patcher_path=patcher_path,
        hooks=hooks,
    )


def test_green_capture_is_raw_exact_and_read_only(tmp_path: Path) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)

    receipt = run_capture(contract, hooks)

    assert receipt["verdict"] == contract.ready_verdict
    assert receipt["problem_count"] == 0
    assert receipt["problems"] == []
    assert receipt["host_publication_authority"]["source_commit"] == HOST_COMMIT
    assert receipt["host_publication_authority"]["artifacts"] == [
        {
            "path": path,
            "sha256": digest(paths["host_artifacts"][path]),
            "bytes": len(paths["host_artifacts"][path]),
            "git_blob_oid": capture._git_blob_oid(paths["host_artifacts"][path]),
            "git_mode": "100644",
        }
        for path in capture.HOST_PUBLICATION_ARTIFACT_PATHS
    ]
    assert receipt["docker_runtime"] == {
        "schema": capture.DOCKER_RUNTIME_SCHEMA,
        "client": {
            "invocation_path": str(paths["docker"]),
            "physical_path": str(paths["docker"]),
            "realpath": str(paths["docker"]),
            "sha256": digest(paths["docker"].read_bytes()),
            "bytes": paths["docker"].stat().st_size,
            "version": {
                "version": "28.3.2",
                "api_version": "1.51",
                "git_commit": "clientcommit",
                "go_version": "go1.24.5",
                "os": "linux",
                "arch": "amd64",
                "build_time": "2026-07-01T00:00:00Z",
                "context": "default",
            },
        },
        "context": {"name": "default", "endpoint": "unix:///var/run/docker.sock"},
        "daemon": {
            "info": {
                "id": "daemon-id",
                "name": capture.EXPECTED_HOST,
                "server_version": "28.3.2",
                "docker_root_dir": "/var/lib/docker",
                "driver": "overlay2",
                "operating_system": "Ubuntu 24.04.2 LTS",
                "os_type": "linux",
                "architecture": "amd64",
                "ncpu": 16,
                "mem_total": 67_108_864_000,
                "kernel_version": "6.8.0-test",
                "cgroup_driver": "systemd",
                "cgroup_version": "2",
            },
            "version": {
                "platform_name": "Docker Engine - Community",
                "version": "28.3.2",
                "api_version": "1.51",
                "min_api_version": "1.24",
                "git_commit": "servercommit",
                "go_version": "go1.24.5",
                "os": "linux",
                "arch": "amd64",
                "build_time": "2026-07-01T00:00:00Z",
                "experimental": False,
            },
        },
    }
    assert receipt["gpu"] == {
        "model": capture.EXPECTED_GPU_MODEL,
        "count": 1,
        "uuid": capture.EXPECTED_GPU_UUID,
        "driver_version": capture.EXPECTED_GPU_DRIVER,
        "memory_total_mib": capture.EXPECTED_GPU_MEMORY_MIB,
    }
    assert receipt["interpreter"]["version"] == "3.10.14"
    assert receipt["interpreter"]["sha256"] == "8" * 64
    assert receipt["invocation"]["sanitized"] is True
    assert receipt["host_preparation"]["evidence"]["verdict"] == (
        capture.EXPECTED_PREPARATION_VERDICT
    )
    assert receipt["runtime_snapshots"] == {
        "before_dataset_hashing": {"gpu": receipt["gpu"], "box": receipt["box"]},
        "after_dataset_hashing": {"gpu": receipt["gpu"], "box": receipt["box"]},
    }
    assert receipt["box"]["all_containers"] == 0
    assert receipt["box"]["gpu_compute_processes"] == 0
    assert receipt["box"]["known_evaluation_processes"] == 0
    assert set(receipt["box"]) == {
        "idle",
        "all_containers",
        "gpu_compute_processes",
        "known_evaluation_processes",
    }
    assert receipt["container_images"]["ncap:latest"]["repo_digests"] == []
    assert receipt["container_images"]["neurad:latest"]["repo_digests"] == [
        "neurad@sha256:" + "d" * 64,
        "neurad@sha256:" + "e" * 64,
    ]
    assert receipt["storage_devices"] == {
        "filesystem_st_dev": 2,
        "mount_st_dev": 2,
        "root_st_dev": 1,
    }
    assert receipt["dataset"]["schema"] == contract.dataset_schema
    assert receipt["dataset"]["contract_sha256"] == contract.dataset_contract_sha256
    assert set(receipt["dataset"]["archives"]) == set(contract.dataset_archives)
    assert set(receipt["dataset"]["metadata_json"]) == set(contract.dataset_metadata_files)
    assert set(receipt["dataset"]["map_anchors"]) == set(contract.dataset_map_anchors)
    assert receipt["dataset"]["identity"] == {
        "dataset_root": contract.dataset_root,
        "dataset_realpath": contract.dataset_root,
        "dataset_is_symlink": False,
        "dataset_version": contract.dataset_version,
        "archive_root": contract.dataset_archive_root,
        "archive_realpath": contract.dataset_archive_root,
        "archive_is_symlink": False,
        "metadata_root": contract.dataset_metadata_root,
        "metadata_realpath": contract.dataset_metadata_root,
        "metadata_is_symlink": False,
        "map_root": contract.dataset_map_root,
        "map_realpath": contract.dataset_map_root,
        "map_is_symlink": False,
        **contract.dataset_mount,
        "dataset_st_dev": 2,
        "mount_st_dev": 2,
        "root_st_dev": 1,
    }
    assert receipt["dataset"]["receipt_payload_sha256"] == (
        capture._dataset_receipt_payload_sha256(receipt["dataset"])
    )
    assert receipt["remote_files"]["compose_script"]["source_sha256"] == (
        contract.compose_input_sha256
    )
    assert receipt["remote_files"]["compose_script"]["patcher_sha256"] == digest(
        paths["patcher"].read_bytes()
    )
    flattened = " ".join(" ".join(command) for command in runner.calls)
    for forbidden in ("docker run", "git checkout", "git reset", " mkdir ", " rm "):
        assert forbidden not in flattened
    github = paths["github"]
    branch_url = f"{capture.GITHUB_API_ROOT}/branches/{capture.GITHUB_BRANCH}"
    checks_url = (
        f"{capture.GITHUB_API_ROOT}/commits/{HOST_COMMIT}/check-runs?"
        "filter=latest&per_page=100&page=1"
    )
    expected_urls = [
        f"{capture.GITHUB_API_ROOT}/commits/{HOST_COMMIT}?per_page=100&page=1",
        branch_url,
        checks_url,
        f"{capture.GITHUB_API_ROOT}/git/trees/{github.tree_sha}?recursive=1",
        *[
            f"{capture.GITHUB_API_ROOT}/contents/{urllib.parse.quote(path, safe='/')}?ref={HOST_COMMIT}"
            for path in capture.HOST_PUBLICATION_ARTIFACT_PATHS
        ],
        branch_url,
        checks_url,
    ]
    assert github.calls == expected_urls
    assert len(github.calls) == 8
    assert not any("/git/blobs/" in url for url in github.calls)


def test_host_commit_requires_current_green_exact_matrix_and_committed_blobs(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.branch_head = "e" * 40

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"] is None
    assert "host-publication-authority:branch-head" in receipt["problems"]

    contract, hooks, _runner, paths = fixture(tmp_path / "failed-check")
    paths["github"].status = "completed"
    paths["github"].conclusion = "failure"
    receipt = run_capture(contract, hooks)
    assert "host-publication-authority:check-not-green:check (3.10)" in receipt["problems"]

    contract, hooks, _runner, paths = fixture(tmp_path / "blob-drift")
    packet_path = capture.HOST_PUBLICATION_ARTIFACT_PATHS[0]
    paths["github"].artifacts[packet_path] = b"different committed packet bytes\n"
    receipt = run_capture(contract, hooks)
    assert (
        "host-publication-authority:artifact-drift:host_packet_manifest.json"
        in receipt["problems"]
    )


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("missing", "host-publication-authority:tree-artifact-set"),
        (
            "duplicate",
            "host-publication-authority:duplicate-tree-path:"
            "experiments/iter135_neuroncap_blind_braking_dose_response/"
            "host_packet_manifest.json",
        ),
        (
            "wrong-oid",
            "host-publication-authority:tree-artifact:host_packet_manifest.json",
        ),
        (
            "wrong-mode",
            "host-publication-authority:tree-artifact:host_packet_manifest.json",
        ),
        (
            "wrong-type",
            "host-publication-authority:tree-artifact:host_packet_manifest.json",
        ),
        (
            "bool-size",
            "host-publication-authority:tree-artifact:host_packet_manifest.json",
        ),
    ],
)
def test_host_commit_requires_exact_recursive_tree_artifact_contract(
    tmp_path: Path, mutation: str, problem: str
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    packet_path = capture.HOST_PUBLICATION_ARTIFACT_PATHS[0]
    row = next(item for item in github.tree_rows if item["path"] == packet_path)
    if mutation == "missing":
        github.tree_rows.remove(row)
    elif mutation == "duplicate":
        github.tree_rows.append(dict(row))
    elif mutation == "wrong-oid":
        row["sha"] = "f" * 40
    elif mutation == "wrong-mode":
        row["mode"] = "100755"
    elif mutation == "wrong-type":
        row["type"] = "tree"
    else:
        row["size"] = True

    receipt = run_capture(contract, hooks)

    assert problem in receipt["problems"]
    assert receipt["host_publication_authority"] is None


@pytest.mark.parametrize("mutation", ["wrong-tree", "truncated"])
def test_host_commit_rejects_recursive_tree_envelope_drift(
    tmp_path: Path, mutation: str
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    if mutation == "wrong-tree":
        paths["github"].tree_document_sha = "e" * 40
    else:
        paths["github"].tree_truncated = True

    receipt = run_capture(contract, hooks)

    assert "host-publication-authority:tree-envelope" in receipt["problems"]
    assert receipt["host_publication_authority"] is None


def test_host_commit_rejects_same_size_different_contents_blob(tmp_path: Path) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    packet_path = capture.HOST_PUBLICATION_ARTIFACT_PATHS[0]
    original = paths["github"].artifacts[packet_path]
    hostile = bytes([original[0] ^ 1]) + original[1:]
    assert len(hostile) == len(original) and hostile != original
    paths["github"].artifacts[packet_path] = hostile

    receipt = run_capture(contract, hooks)

    assert (
        "host-publication-authority:artifact-drift:host_packet_manifest.json"
        in receipt["problems"]
    )
    assert receipt["host_publication_authority"] is None


@pytest.mark.parametrize(
    ("names", "problem"),
    [
        (["check (3.10)"], "host-publication-authority:check-run-envelope"),
        (
            ["check (3.10)", "check (3.10)"],
            "host-publication-authority:duplicate-check:check (3.10)",
        ),
        (
            ["check (3.10)", "unexpected green check"],
            "host-publication-authority:unexpected-check",
        ),
        (
            [*capture.REQUIRED_GITHUB_CHECKS, "unexpected green check"],
            "host-publication-authority:check-run-envelope",
        ),
    ],
)
def test_host_commit_check_page_is_exact_and_page_complete(
    tmp_path: Path, names: list[str], problem: str
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.names = names

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"] is None
    assert problem in receipt["problems"]
    checks_calls = [url for url in github.calls if "/check-runs?" in url]
    assert checks_calls == [
        f"{capture.GITHUB_API_ROOT}/commits/{HOST_COMMIT}/check-runs?"
        "filter=latest&per_page=100&page=1"
    ]


def test_host_commit_requires_sole_packet_parent_and_exact_publication_path_set(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    paths["github"].parent_commit = "b" * 40

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"] is None
    assert "host-publication-authority:commit-parent" in receipt["problems"]

    contract, hooks, _runner, paths = fixture(tmp_path / "extra-path")
    paths["github"].changed_paths.append("unexpected.txt")

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"] is None
    assert "host-publication-authority:changed-paths" in receipt["problems"]

    contract, hooks, _runner, paths = fixture(tmp_path / "rename")
    paths["github"].previous_filename = "unexpected-old-path.txt"

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"] is None
    assert "host-publication-authority:changed-paths" in receipt["problems"]


def test_host_commit_tip_is_rechecked_immediately_before_green_capture(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    paths["github"].branch_heads = [HOST_COMMIT, "e" * 40]

    receipt = run_capture(contract, hooks)

    assert receipt["host_publication_authority"]["verified"] is True
    assert "host-publication-authority:branch-recheck" in receipt["problems"]
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT


def test_terminal_check_replay_blocks_green_capture_with_stable_master(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.check_documents = [
        check_document(HOST_COMMIT),
        check_document(
            HOST_COMMIT,
            ids=(510, 511),
            status="completed",
            conclusion="failure",
        ),
    ]

    receipt = run_capture(contract, hooks)

    assert "host-publication-authority:terminal:check-not-green:check (3.10)" in receipt[
        "problems"
    ]
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT


def test_terminal_green_check_rotation_is_persisted_in_environment_receipt(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.check_documents = [
        check_document(HOST_COMMIT),
        check_document(HOST_COMMIT, ids=(610, 611)),
    ]

    receipt = run_capture(contract, hooks)

    assert receipt["verdict"] == contract.ready_verdict
    assert [row["id"] for row in receipt["host_publication_authority"]["checks"]] == [
        610,
        611,
    ]


def test_docker_daemon_identity_or_unbounded_projection_fails_closed(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.docker_info["Name"] = "different-host"
    runner.docker_info["OperatingSystem"] = "x" * 257

    receipt = run_capture(contract, hooks)

    assert receipt["docker_runtime"] is None
    assert any(problem.startswith("docker-runtime:") for problem in receipt["problems"])
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT


def test_docker_architecture_aliases_are_fixed_and_cross_family_drift_is_rejected(
    tmp_path: Path,
) -> None:
    for info_arch, version_arch in (("x86_64", "amd64"), ("aarch64", "arm64")):
        case = tmp_path / f"{info_arch}-{version_arch}"
        contract, hooks, runner, _paths = fixture(case)
        runner.docker_info["Architecture"] = info_arch
        runner.docker_version["Server"]["Arch"] = version_arch

        receipt = run_capture(contract, hooks)

        assert receipt["verdict"] == contract.ready_verdict
        assert receipt["docker_runtime"]["daemon"]["info"]["architecture"] == info_arch
        assert receipt["docker_runtime"]["daemon"]["version"]["arch"] == version_arch

    contract, hooks, runner, _paths = fixture(tmp_path / "cross-family")
    runner.docker_info["Architecture"] = "x86_64"
    runner.docker_version["Server"]["Arch"] = "arm64"

    receipt = run_capture(contract, hooks)

    assert receipt["docker_runtime"] is None
    assert "docker-runtime:identity" in receipt["problems"]


def test_docker_client_is_rehashed_after_runtime_and_each_dependent_phase(
    tmp_path: Path,
) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)
    original = runner.__call__
    changed = False

    def drift_after_image(argv: list[str] | tuple[str, ...]) -> bytes:
        nonlocal changed
        command = tuple(argv)
        result = original(argv)
        if (
            not changed
            and Path(command[0]).name == "docker"
            and command[1:3] == ("image", "inspect")
        ):
            paths["docker"].write_bytes(b"#!/bin/sh\nexit 17\n")
            paths["docker"].chmod(0o755)
            changed = True
        return result

    receipt = run_capture(contract, replace(hooks, run=drift_after_image))

    assert "docker-runtime:client-drift:images-after" in receipt["problems"]
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT

    contract, hooks, runner, paths = fixture(tmp_path / "runtime-probe")
    original = runner.__call__

    def drift_during_runtime_probe(argv: list[str] | tuple[str, ...]) -> bytes:
        command = tuple(argv)
        result = original(argv)
        if Path(command[0]).name == "docker" and command[1:5] == (
            "context",
            "inspect",
            "--format",
            "{{json .Endpoints.docker.Host}}",
        ):
            paths["docker"].write_bytes(b"#!/bin/sh\nexit 23\n")
            paths["docker"].chmod(0o755)
        return result

    receipt = run_capture(contract, replace(hooks, run=drift_during_runtime_probe))

    assert receipt["docker_runtime"] is None
    assert "docker-runtime:client-drift:runtime-probe" in receipt["problems"]
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT


def test_host_commit_cli_contract_is_exact_lowercase_oid() -> None:
    assert capture._commit(HOST_COMMIT) == HOST_COMMIT
    for value in ("D" * 40, "d" * 39, "not-a-commit"):
        try:
            capture._commit(value)
        except Exception:
            pass
        else:
            raise AssertionError(f"invalid host commit accepted: {value}")


def test_remote_byte_drift_and_symlink_are_rejected(tmp_path: Path) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    paths["payload"].write_bytes(b"mutated\n")
    target = paths["backup"].with_name("backup-target")
    target.write_bytes(paths["backup"].read_bytes())
    paths["backup"].unlink()
    paths["backup"].symlink_to(target)

    receipt = run_capture(contract, hooks)

    assert "remote-file:runtime:sha256" in receipt["problems"]
    assert "remote-file:runtime:bytes" in receipt["problems"]
    assert any(
        problem.startswith("remote-file:neurad_dockerfile_backup:path:symlink:")
        for problem in receipt["problems"]
    )
    assert any(
        problem.startswith("remote-file:neurad_dockerfile_backup:path:realpath:")
        for problem in receipt["problems"]
    )


def test_repository_head_status_and_untracked_code_are_rejected(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    uniad = str(contract.repositories["uniad"]["path"])
    neurad = str(contract.repositories["neurad"]["path"])
    runner.repositories[uniad].update(
        {
            "head": "f" * 40,
            "staged": ["runtime.py"],
            "dirty": ["inference/server.py"],
            "untracked": ["evil.py"],
        }
    )
    runner.repositories[neurad]["untracked"] = []

    receipt = run_capture(contract, hooks)

    for problem in (
        "repository:uniad:head",
        "repository:uniad:staged-paths",
        "repository:uniad:dirty-tracked-paths",
        "repository:uniad:unexpected-untracked:1",
        "repository:neurad:required-untracked",
    ):
        assert problem in receipt["problems"]


def test_image_gpu_container_and_evaluator_drift_are_rejected(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.images["uniad:latest"]["Id"] = "sha256:" + "f" * 64
    runner.images["ncap:latest"]["RepoDigests"] = ["not-a-distribution-digest"]
    duplicate = "neurad@sha256:" + "a" * 64
    runner.images["neurad:latest"]["RepoDigests"] = [duplicate, duplicate]
    runner.gpu_row = (
        f"NVIDIA L4, GPU-ffffffff-ffff-ffff-ffff-ffffffffffff, "
        f"{capture.EXPECTED_GPU_DRIVER}, {capture.EXPECTED_GPU_MEMORY_MIB}\n"
    ).encode()
    runner.containers = b"a" * 64 + b"\n"
    runner.compute = b"4321\n"
    runner.processes += b"700 1 python /opt/sentinel-stack/NeuroNCAP/main.py\n"

    receipt = run_capture(contract, hooks)

    for problem in (
        "image:uniad:latest:id",
        "image:ncap:latest:repo-digests-schema",
        "image:neurad:latest:repo-digests-duplicate",
        "gpu:identity",
        "idle:containers-present",
        "idle:gpu-process-present",
        "idle:evaluator-process-present",
    ):
        assert problem in receipt["problems"]
    assert receipt["container_images"]["neurad:latest"]["repo_digests"] == [duplicate]
    assert receipt["box"]["idle"] is False


def test_storage_mount_device_emptiness_and_local_free_fail_closed(tmp_path: Path) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)
    (paths["output"] / "unexpected").write_text("occupied")
    runner.mount["source"] = "/dev/root"
    bad_hooks = replace(
        hooks,
        device=lambda _path: 1,
        disk_free=lambda _path: 149,
    )

    receipt = run_capture(contract, bad_hooks, local_free_bytes=149)

    for problem in (
        "storage:identity:filesystem_empty",
        "storage:identity:mount_source",
        "storage:not-dedicated-device",
        "storage:projected-reserve",
        "storage:local-free",
    ):
        assert problem in receipt["problems"]


def test_dataset_archive_byte_proof_drift_fails_closed_without_large_fixture(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    original_reader = hooks.dataset_read
    target_name = next(iter(contract.dataset_archives))

    def drifted_reader(path: Path) -> tuple[dict[str, Any], list[str]]:
        row, problems = original_reader(path)
        if path.name == target_name:
            row = {**row, "sha256": "f" * 64, "bytes": row["bytes"] + 1}
        return row, problems

    receipt = run_capture(contract, replace(hooks, dataset_read=drifted_reader))

    assert f"dataset:archive:{target_name}:expected-sha256" in receipt["problems"]
    assert f"dataset:archive:{target_name}:expected-bytes" in receipt["problems"]


def test_dataset_exact_metadata_set_and_physical_map_anchor_fail_closed(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    (paths["metadata_root"] / "self-declared.json").write_text("{}\n")
    map_name = contract.dataset_map_anchors[0]
    anchor = paths["map_root"] / map_name
    replacement_path = paths["dataset_root"] / "map-replacement.png"
    replacement_path.write_bytes(anchor.read_bytes())
    anchor.unlink()
    anchor.symlink_to(replacement_path)

    receipt = run_capture(contract, hooks)

    assert "dataset:metadata:file-set" in receipt["problems"]
    assert f"dataset:maps:nonphysical-file:{map_name}" in receipt["problems"]
    assert any(
        problem.startswith(f"dataset:map:{map_name}:path:symlink:")
        for problem in receipt["problems"]
    )


def test_dataset_contract_digest_and_device_identity_fail_closed(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.mount["uuid"] = "00000000-0000-0000-0000-000000000000"
    bad_contract = replace(contract, dataset_version="v1.0-mini")
    bad_hooks = replace(hooks, device=lambda _path: 1)

    receipt = run_capture(bad_contract, bad_hooks)

    assert "dataset:contract-sha256" in receipt["problems"]
    assert "dataset:identity:mount_uuid" in receipt["problems"]
    assert "dataset:not-dedicated-device" in receipt["problems"]


def test_compose_preimage_or_patcher_drift_cannot_self_assert(tmp_path: Path) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    contract = replace(contract, compose_input_sha256="0" * 64)

    receipt = run_capture(contract, hooks)

    assert "compose:source-sha256" in receipt["problems"]
    assert receipt["remote_files"]["compose_script"]["source_sha256"] != "0" * 64


def test_command_failure_is_incomplete_not_green(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.fail_prefix = "docker"

    receipt = run_capture(contract, hooks)

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert receipt["problem_count"] > 0
    assert any(problem.startswith("image:") for problem in receipt["problems"])
    assert any(problem.startswith("idle:containers:") for problem in receipt["problems"])


def test_atomic_writer_replaces_regular_file_without_temp_residue(tmp_path: Path) -> None:
    output = tmp_path.resolve() / "env_receipts.json"
    output.write_text("old\n")
    receipt = {"schema": "test", "problem_count": 0, "problems": []}

    capture.atomic_write_json(output, receipt)

    assert json.loads(output.read_text()) == receipt
    assert list(output.parent.glob(f".{output.name}.*.tmp")) == []
    assert output.stat().st_mode & 0o777 == 0o600


def test_canonical_contract_loads_exact_82_role_topology() -> None:
    contract = capture.load_contract()

    assert len(contract.remote_files) == 82
    assert sum(role.startswith("scenario:") for role in contract.remote_files) == 20
    assert sum(role.startswith("renderer:") for role in contract.remote_files) == 42
    assert set(contract.repositories) == {"uniad", "neuroncap", "neurad"}
    assert contract.required_untracked_bindings == {
        ("neurad", "Dockerfile.bak"): "neurad_dockerfile_backup"
    }
    assert contract.schema == "iter135.environment_receipts.v3"
    assert contract.dataset_root == "/datasets/nuscenes-full"
    assert contract.dataset_version == "v1.0-trainval"
    assert contract.dataset_contract_sha256 == (capture.EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256)
    assert len(contract.dataset_archives) == 11
    assert sum(row[1] for row in contract.dataset_archives.values()) == 314_886_603_672
    assert len(contract.dataset_metadata_files) == 13
    assert len(contract.dataset_map_anchors) == 4


def test_local_free_cli_value_is_mandatory_and_nonnegative() -> None:
    parser = capture._nonnegative_integer

    assert parser("123") == 123
    for value in ("-1", "1.5", "secret"):
        try:
            parser(value)
        except Exception:
            pass
        else:
            raise AssertionError(f"invalid explicit byte count accepted: {value}")


def test_runtime_idle_is_reprobed_after_dataset_hashing_and_drift_fails_closed(
    tmp_path: Path,
) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    original = runner.__call__
    compute_calls = 0

    def drifting_run(argv: list[str] | tuple[str, ...]) -> bytes:
        nonlocal compute_calls
        command = tuple(argv)
        if command[0] == "nvidia-smi" and "--query-compute-apps=pid" in command:
            compute_calls += 1
            if compute_calls == 2:
                return b"4321\n"
        return original(argv)

    receipt = run_capture(contract, replace(hooks, run=drifting_run))

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert "idle:gpu-process-present" in receipt["problems"]
    assert "runtime-snapshots:drift" in receipt["problems"]
    assert receipt["runtime_snapshots"]["before_dataset_hashing"]["box"][
        "gpu_compute_processes"
    ] == 0
    assert receipt["runtime_snapshots"]["after_dataset_hashing"]["box"][
        "gpu_compute_processes"
    ] == 1


def test_preparation_receipt_is_replayed_against_installed_controller_and_packet(
    tmp_path: Path, monkeypatch
) -> None:
    install = tmp_path.resolve() / "iter135"
    analytic = tmp_path.resolve() / "sentinel-i135-outoutput"
    install.mkdir()
    analytic.mkdir()
    controller = install / "prepare_host135.py"
    payload_file = install / "payload.txt"
    manifest_path = install / "host_packet_manifest.json"
    controller.write_text("# exact controller\n")
    controller.chmod(0o755)
    payload_file.write_text("payload\n")

    def claim(path: Path) -> dict[str, Any]:
        payload = path.read_bytes()
        return {
            "path": str(path.with_name(f"staged-{path.name}")),
            "sha256": digest(payload),
            "bytes": len(payload),
            "mode": path.stat().st_mode & 0o777,
        }

    packet_files = {
        "prepare_host135.py": claim(controller),
        "payload.txt": claim(payload_file),
    }
    manifest_path.write_text(
        json.dumps(
            {
                "schema": capture.EXPECTED_PACKET_SCHEMA,
                "source_commit": "a" * 40,
                "files": {
                    name: {
                        "sha256": row["sha256"],
                        "bytes": row["bytes"],
                        "mode": row["mode"],
                    }
                    for name, row in packet_files.items()
                },
            },
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    manifest_claim = claim(manifest_path)
    manifest_sha = manifest_claim["sha256"]
    receipt = {
        "schema": capture.EXPECTED_PREPARATION_SCHEMA,
        "verdict": capture.EXPECTED_PREPARATION_VERDICT,
        "started_at_utc": "2026-07-16T10:00:00Z",
        "finished_at_utc": "2026-07-16T10:01:00Z",
        "host": capture.EXPECTED_HOST,
        "problem_count": 0,
        "problems": [],
        "publication_authority": {
            "schema": capture.PUBLICATION_AUTHORITY_SCHEMA,
            "repository": capture.GITHUB_REPOSITORY,
            "branch": capture.GITHUB_BRANCH,
            "source_commit": "a" * 40,
            "branch_head_sha": "a" * 40,
            "required_checks": list(capture.REQUIRED_GITHUB_CHECKS),
            "checks": [
                {
                    "name": name,
                    "id": 310 + index,
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": "a" * 40,
                    "app_slug": capture.EXPECTED_CHECK_APP,
                }
                for index, name in enumerate(capture.REQUIRED_GITHUB_CHECKS)
            ],
            "artifacts": sorted(
                (
                    {
                        "path": capture._packet_repository_path(name),
                        "sha256": claim["sha256"],
                        "bytes": claim["bytes"],
                        "git_blob_oid": capture._git_blob_oid(
                            (install / name).read_bytes()
                        ),
                        "git_mode": (
                            "100755" if claim["mode"] == 0o755 else "100644"
                        ),
                    }
                    for name, claim in packet_files.items()
                ),
                key=lambda row: row["path"],
            ),
            "verified": True,
        },
        "packet_manifest_sha256": manifest_sha,
        "packet": {
            "schema": capture.EXPECTED_PACKET_SCHEMA,
            "source_commit": "a" * 40,
            "manifest": manifest_claim,
            "independently_supplied_manifest_sha256": manifest_sha,
            "files": packet_files,
        },
        "controller": packet_files["prepare_host135.py"],
        "repositories": {
            "before": {"uniad": {}, "neuroncap": {}, "neurad": {}},
            "after": {"uniad": {}, "neuroncap": {}, "neurad": {}},
        },
        "compose": {},
        "storage": {
            "analytic_root": str(analytic),
            "analytic_root_realpath": str(analytic),
            "analytic_root_is_symlink": False,
            "analytic_root_empty": True,
        },
        "forbidden_paths": {
            str(install): False,
            str(analytic): False,
            str(tmp_path.resolve() / "i135-smoke.lock"): False,
        },
        "actions": [
            {
                "action": "normalize_uniad_server_from_verified_head_blob",
                "performed": False,
            },
            {
                "action": "atomically_patch_compose_from_exact_preimage",
                "performed": True,
            },
            {"action": "create_absent_empty_analytic_root", "performed": True},
            {"action": "atomically_install_verified_packet", "performed": True},
        ],
        "invocation": {
            "environment": dict(capture.PREPARATION_SANITIZED_ENVIRONMENT),
            "environment_matches": True,
            "isolated": True,
            "python_implementation": "CPython",
            "python_version": "3.10.14",
        },
        "receipt_payload_sha256": None,
    }
    receipt["receipt_payload_sha256"] = hashlib.sha256(
        capture._canonical_json_bytes(
            {key: value for key, value in receipt.items() if key != "receipt_payload_sha256"}
        )
    ).hexdigest()
    receipt_path = install / "host_preparation_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    monkeypatch.setattr(
        capture,
        "EXPECTED_PREPARATION_PACKET_FILES",
        {"prepare_host135.py", "payload.txt"},
    )

    bound, problems = capture.load_and_validate_preparation_receipt(
        receipt_path,
        install_root=install,
        controller_path=controller,
        packet_manifest_path=manifest_path,
        analytic_root=analytic,
    )

    assert problems == []
    assert bound["evidence"] == receipt
    controller.write_text("# hostile replacement\n")
    _bound, drift = capture.load_and_validate_preparation_receipt(
        receipt_path,
        install_root=install,
        controller_path=controller,
        packet_manifest_path=manifest_path,
        analytic_root=analytic,
    )
    assert "preparation:controller-binding" in drift
    assert "preparation:packet-file:prepare_host135.py:binding" in drift

    controller.write_text("# exact controller\n")
    original_manifest = manifest_path.read_bytes()
    hostile_manifests = (
        b'{"schema":"first","schema":"second",' + original_manifest[1:],
        b'{"hostile":Infinity,' + original_manifest[1:],
    )
    for hostile_manifest in hostile_manifests:
        manifest_path.write_bytes(hostile_manifest)
        _bound, hostile_problems = capture.load_and_validate_preparation_receipt(
            receipt_path,
            install_root=install,
            controller_path=controller,
            packet_manifest_path=manifest_path,
            analytic_root=analytic,
        )
        assert "preparation:packet-manifest-json:ValueError" in hostile_problems
        assert "preparation:packet-manifest-replay" in hostile_problems
    manifest_path.write_bytes(original_manifest)


@pytest.mark.parametrize(
    "payload",
    [b'{"schema":"first","schema":"second"}\n', b'{"hostile":-Infinity}\n'],
)
def test_preparation_receipt_strict_json_rejects_hostile_documents(
    tmp_path: Path, payload: bytes
) -> None:
    receipt_path = tmp_path.resolve() / "host_preparation_receipt.json"
    receipt_path.write_bytes(payload)

    bound, problems = capture.load_and_validate_preparation_receipt(receipt_path)

    assert bound["evidence"] is None
    assert problems == ["preparation:receipt-json:ValueError"]


def test_declared_python_minimum_and_ci_matrix_cover_python_310() -> None:
    source = MODULE_PATH.read_text()
    workflow = (REPO / ".github/workflows/ci.yml").read_text()

    assert "from datetime import UTC" not in source
    assert "datetime.now(timezone.utc)" in source
    assert "python-version:" in workflow
    assert "name: check (${{ matrix.python-version }})" in workflow
    assert '"3.10"' in workflow
    assert '"3.11"' in workflow
    interpreter, problems = capture._interpreter_receipt()
    assert problems == []
    assert interpreter["implementation"] == "CPython"
    assert isinstance(interpreter["sha256"], str) and len(interpreter["sha256"]) == 64
