from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NoReturn

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


def assert_exact_attempt_marker(
    marker_path: Path,
    *,
    attempt: capture._EnvironmentOutputAttempt | None = None,
) -> dict[str, Any]:
    payload = marker_path.read_bytes()
    marker = json.loads(payload)
    assert set(marker) == {
        "schema",
        "authority",
        "status",
        "attempt_id",
        "parent_identity",
        "canonical_receipt",
        "pending_receipt",
        "publication_rule",
    }
    assert marker["schema"] == "iter135.environment_capture_attempt_marker.v2"
    assert marker["authority"] == "NONE"
    assert marker["status"] == "ATTEMPT_IN_PROGRESS_NO_ENVIRONMENT_VERDICT"
    assert (
        type(marker["attempt_id"]) is str
        and len(marker["attempt_id"]) == 64
        and set(marker["attempt_id"]) <= set("0123456789abcdef")
    )
    assert marker["canonical_receipt"] == capture.CANONICAL_RECEIPT_BASENAME
    assert marker["pending_receipt"] == capture.PENDING_RECEIPT_BASENAME
    if attempt is not None:
        assert payload == attempt.marker_payload
        assert marker["attempt_id"] == attempt.attempt_id
        assert marker["parent_identity"] == {
            "st_dev": attempt.parent_identity[0],
            "st_ino": attempt.parent_identity[1],
            "st_mode": attempt.parent_identity[2],
        }
    return marker


@pytest.fixture(autouse=True)
def bind_physical_h_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Give every hook fixture a complete, isolated canonical H filesystem."""

    host_root = tmp_path.resolve() / "physical-h-contract"
    install_root = host_root / "iter135"
    staging_root = host_root / ".iter135-packet"
    dataset_root = host_root / "datasets"
    analytic_root = dataset_root / "sentinel-i135-outoutput"
    install_root.mkdir(parents=True)
    staging_root.mkdir()
    analytic_root.mkdir(parents=True)
    uniad_root = host_root / "UniAD"
    neuroncap_root = host_root / "NeuroNCAP"
    neurad_root = host_root / "neurad-studio"
    monkeypatch.setattr(capture, "HERE", install_root)
    monkeypatch.setattr(
        capture,
        "CANONICAL_PREPARER_PATH",
        install_root / "prepare_host135.py",
    )
    monkeypatch.setattr(
        capture,
        "CANONICAL_PACKET_MANIFEST_PATH",
        install_root / "host_packet_manifest.json",
    )
    monkeypatch.setattr(
        capture,
        "CANONICAL_PREPARATION_RECEIPT_PATH",
        install_root / "host_preparation_receipt.json",
    )
    monkeypatch.setattr(
        capture,
        "DEFAULT_OUTPUT",
        install_root / capture.CANONICAL_RECEIPT_BASENAME,
    )
    monkeypatch.setattr(capture, "EXPECTED_INSTALL_ROOT", str(install_root))
    monkeypatch.setattr(capture, "EXPECTED_PACKET_STAGING_ROOT", staging_root)
    monkeypatch.setattr(capture, "EXPECTED_DATASET_ROOT", dataset_root)
    monkeypatch.setattr(
        capture,
        "EXPECTED_SMOKE_ROOT",
        dataset_root / "sentinel-i135-smoke-evidence",
    )
    monkeypatch.setattr(capture, "EXPECTED_ANALYTIC_ROOT", str(analytic_root))
    monkeypatch.setattr(capture, "EXPECTED_UNIAD_ROOT", uniad_root)
    monkeypatch.setattr(capture, "EXPECTED_NEURONCAP_ROOT", neuroncap_root)
    monkeypatch.setattr(capture, "EXPECTED_NEURAD_ROOT", neurad_root)
    monkeypatch.setattr(
        capture,
        "EXPECTED_H_MOUNT",
        {
            "mount_target": str(dataset_root),
            "mount_source": "/dev/test-h-evidence",
            "mount_fstype": "ext4",
            "mount_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        },
    )


WORKFLOW_RUN_ID = 7_410
CHECK_SUITE_ID = 8_410


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
    run_number: int = 741,
    run_attempt: int = 1,
    minute: int = 0,
    branch: str = "master",
    event: str = "push",
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict[str, Any]:
    run_url = f"{capture.GITHUB_API_ROOT}/actions/runs/{run_id}"
    return {
        "id": run_id,
        "check_suite_id": suite_id,
        "workflow_id": capture.GITHUB_WORKFLOW_ID,
        "name": capture.GITHUB_WORKFLOW_NAME,
        "path": capture.GITHUB_WORKFLOW_PATH,
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
    ids: tuple[int, int] = (410, 411),
    names: tuple[str, ...] = capture.REQUIRED_GITHUB_CHECKS,
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
                "head_branch": capture.GITHUB_BRANCH,
                "workflow_name": capture.GITHUB_WORKFLOW_NAME,
                "status": status,
                "conclusion": conclusion,
                "started_at": github_timestamp(10 + index),
                "completed_at": github_timestamp(11 + index),
                "url": f"{capture.GITHUB_API_ROOT}/actions/jobs/{check_id}",
                "run_url": f"{capture.GITHUB_API_ROOT}/actions/runs/{run_id}",
                "check_run_url": f"{capture.GITHUB_API_ROOT}/check-runs/{check_id}",
            }
        )
    return {"total_count": len(rows), "jobs": rows}


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
        self.workflow_documents: list[dict[str, Any]] = []
        self.check_documents: list[dict[str, Any]] = []
        self.calls: list[str] = []

    def __call__(self, url: str) -> dict[str, Any]:
        self.calls.append(url)
        if "/branches/master" in url:
            head = self.branch_heads.pop(0) if self.branch_heads else self.branch_head
            return {"name": "master", "commit": {"sha": head}}
        if "/actions/workflows/" in url:
            if self.workflow_documents:
                return self.workflow_documents.pop(0)
            return workflow_document(HOST_COMMIT)
        if "/actions/runs/" in url and "/jobs?" in url:
            if self.check_documents:
                return self.check_documents.pop(0)
            return job_document(
                HOST_COMMIT,
                names=tuple(self.names),
                ids=tuple(410 + index for index in range(len(self.names))),
                status=self.status,
                conclusion=self.conclusion,
            )
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

    def fetch_raw(self, url: str) -> bytes:
        self.calls.append(url)
        if "/contents/" not in url:
            raise AssertionError(f"unexpected raw GitHub URL: {url}")
        encoded_path = url.split("/contents/", 1)[1].split("?", 1)[0]
        path = urllib.parse.unquote(encoded_path)
        return self.artifacts[path]


def check_document(
    commit: str,
    *,
    ids: tuple[int, int] = (410, 411),
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


def test_github_transport_emits_cache_bypass_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = f"{capture.GITHUB_API_ROOT}/branches/master"
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
        capture.urllib.request, "build_opener", lambda *_handlers: Opener()
    )

    assert capture._fetch_json(requested) == {}
    assert len(observed_requests) == 1
    assert observed_requests[0].get_header("Cache-control") == "no-cache"
    assert observed_requests[0].get_header("Pragma") == "no-cache"


def test_github_raw_transport_emits_cache_bypass_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = (
        f"{capture.GITHUB_API_ROOT}/contents/"
        "experiments/iter135_neuroncap_blind_braking_dose_response/payload.bin"
        f"?ref={HOST_COMMIT}"
    )
    observed_requests = []

    class Headers(dict):
        def get_content_type(self):
            return "application/vnd.github.raw+json"

    class Response:
        status = 200
        headers = Headers({"Content-Length": "7"})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return requested

        def read(self, _limit):
            return b"payload"

    class Opener:
        def open(self, request, timeout):
            assert timeout == 60
            observed_requests.append(request)
            return Response()

    monkeypatch.setattr(
        capture.urllib.request, "build_opener", lambda *_handlers: Opener()
    )

    assert capture._fetch_raw(requested) == b"payload"
    assert len(observed_requests) == 1
    assert observed_requests[0].get_header("Cache-control") == "no-cache"
    assert observed_requests[0].get_header("Pragma") == "no-cache"


def test_workflow_run_transport_uses_its_dedicated_bounded_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = (
        f"{capture.GITHUB_API_ROOT}/actions/workflows/{capture.GITHUB_WORKFLOW_FILE}/runs"
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
            assert limit == capture.MAX_GITHUB_WORKFLOW_RESPONSE_BYTES + 1
            return b"{}"

    class Opener:
        def open(self, _request, timeout):
            assert timeout == 15
            return Response()

    monkeypatch.setattr(
        capture.urllib.request, "build_opener", lambda *_handlers: Opener()
    )

    assert capture._fetch_json(requested) == {}
    assert 2 << 20 <= capture.MAX_GITHUB_WORKFLOW_RESPONSE_BYTES <= 8 << 20


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


def mission_state_document(phase: str, run_state: object) -> dict[str, Any]:
    state = json.loads(json.dumps(capture.EXPECTED_MISSION_STATE_COMMON))
    phase_contract = capture.MISSION_PHASE_CONTRACTS.get(phase)
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


def install_green_h_fixture(
    mission_state_path: Path,
) -> tuple[dict[str, Any], bytes, bytes]:
    """Install a full canonical green H receipt and its retained success pair."""

    install_root = capture.HERE
    analytic_root = Path(capture.EXPECTED_ANALYTIC_ROOT)
    payloads: dict[str, bytes] = {}
    for name in sorted(capture.EXPECTED_PREPARATION_PACKET_FILES):
        if name == "MISSION_STATE.json":
            payload = mission_state_path.read_bytes()
        else:
            payload = f"canonical H fixture for {name}\n".encode()
        path = install_root / name
        path.write_bytes(payload)
        path.chmod(capture.EXPECTED_PREPARATION_PACKET_MODES[name])
        payloads[name] = payload
    file_claims = {
        name: {
            "path": str(capture.EXPECTED_PACKET_STAGING_ROOT / name),
            "sha256": digest(payload),
            "bytes": len(payload),
            "mode": capture.EXPECTED_PREPARATION_PACKET_MODES[name],
        }
        for name, payload in payloads.items()
    }
    source_commit = "a" * 40
    manifest_document = {
        "schema": capture.EXPECTED_PACKET_SCHEMA,
        "source_commit": source_commit,
        "files": {
            name: {
                "sha256": claim["sha256"],
                "bytes": claim["bytes"],
                "mode": claim["mode"],
            }
            for name, claim in file_claims.items()
        },
    }
    manifest_payload = (
        json.dumps(manifest_document, indent=1, sort_keys=True) + "\n"
    ).encode()
    capture.CANONICAL_PACKET_MANIFEST_PATH.write_bytes(manifest_payload)
    capture.CANONICAL_PACKET_MANIFEST_PATH.chmod(0o644)
    manifest_sha256 = digest(manifest_payload)
    authority = {
        "schema": capture.PUBLICATION_AUTHORITY_SCHEMA,
        "repository": capture.GITHUB_REPOSITORY,
        "branch": capture.GITHUB_BRANCH,
        "source_commit": source_commit,
        "branch_head_sha": source_commit,
        "required_checks": list(capture.REQUIRED_GITHUB_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 310 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": source_commit,
                "app_slug": capture.EXPECTED_CHECK_APP,
            }
            for index, name in enumerate(capture.REQUIRED_GITHUB_CHECKS)
        ],
        "artifacts": [
            {
                "path": capture._packet_repository_path(name),
                "sha256": file_claims[name]["sha256"],
                "bytes": file_claims[name]["bytes"],
                "git_blob_oid": capture._git_blob_oid(payloads[name]),
                "git_mode": (
                    "100755"
                    if file_claims[name]["mode"] == 0o755
                    else "100644"
                ),
            }
            for name in sorted(
                file_claims,
                key=capture._packet_repository_path,
            )
        ],
        "verified": True,
    }
    server_claim = {
        "path": str(capture.EXPECTED_UNIAD_ROOT / "inference/server.py"),
        "sha256": capture.EXPECTED_UNIAD_SERVER_SHA256,
        "bytes": capture.EXPECTED_UNIAD_SERVER_BYTES,
        "mode": 0o644,
    }
    compose_path = (
        capture.EXPECTED_NEURONCAP_ROOT
        / "scripts/_docker_compose_release.sh"
    )
    before_repositories = {
        "uniad": {
            "path": str(capture.EXPECTED_UNIAD_ROOT),
            "head": capture.EXPECTED_UNIAD_HEAD,
            "staged_paths": [],
            "dirty_tracked_paths": [
                "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"
            ],
            "untracked_paths": ["checkpoints"],
        },
        "neuroncap": {
            "path": str(capture.EXPECTED_NEURONCAP_ROOT),
            "head": capture.EXPECTED_NEURONCAP_HEAD,
            "staged_paths": [],
            "dirty_tracked_paths": [
                "docker/Dockerfile",
                "scripts/_docker_compose_release.sh",
            ],
            "untracked_paths": ["outoutput/i134/receipt.json"],
        },
        "neurad": {
            "path": str(capture.EXPECTED_NEURAD_ROOT),
            "head": capture.EXPECTED_NEURAD_HEAD,
            "staged_paths": [],
            "dirty_tracked_paths": ["Dockerfile"],
            "untracked_paths": ["Dockerfile.bak"],
        },
    }
    dataset_device = analytic_root.stat().st_dev
    receipt: dict[str, Any] = {
        "schema": capture.EXPECTED_PREPARATION_SCHEMA,
        "verdict": capture.EXPECTED_PREPARATION_VERDICT,
        "started_at_utc": "2026-07-16T14:00:00Z",
        "finished_at_utc": "2026-07-16T14:00:01Z",
        "host": capture.EXPECTED_HOST,
        "problem_count": 0,
        "problems": [],
        "publication_authority": authority,
        "packet_manifest_sha256": manifest_sha256,
        "packet": {
            "schema": capture.EXPECTED_PACKET_SCHEMA,
            "source_commit": source_commit,
            "manifest": {
                "path": str(
                    capture.EXPECTED_PACKET_STAGING_ROOT
                    / "host_packet_manifest.json"
                ),
                "sha256": manifest_sha256,
                "bytes": len(manifest_payload),
                "mode": 0o644,
            },
            "independently_supplied_manifest_sha256": manifest_sha256,
            "files": file_claims,
        },
        "controller": file_claims["prepare_host135.py"],
        "repositories": {
            "before": before_repositories,
            "after": json.loads(json.dumps(before_repositories)),
        },
        "compose": {
            "patcher": file_claims["patch_compose_dose_env.py"],
            "before": {
                "path": str(compose_path),
                "sha256": capture.EXPECTED_COMPOSE_INPUT_SHA256,
                "bytes": capture.EXPECTED_COMPOSE_INPUT_BYTES,
                "mode": 0o755,
            },
            "after": {
                "path": str(compose_path),
                "sha256": capture.EXPECTED_COMPOSE_OUTPUT_SHA256,
                "bytes": capture.EXPECTED_COMPOSE_OUTPUT_BYTES,
                "mode": 0o755,
            },
        },
        "storage": {
            **capture.EXPECTED_H_MOUNT,
            "dataset_st_dev": dataset_device,
            "root_st_dev": dataset_device + 1,
            "free_bytes_before": 220 * 1024**3,
            "minimum_remote_free_bytes": (
                capture.EXPECTED_H_MINIMUM_REMOTE_FREE_BYTES
            ),
            "projected_output_bytes": (
                capture.EXPECTED_H_PROJECTED_OUTPUT_BYTES
            ),
            "minimum_reserve_bytes": capture.EXPECTED_H_MINIMUM_RESERVE_BYTES,
            "analytic_root": str(analytic_root),
            "analytic_root_realpath": str(analytic_root),
            "analytic_root_is_symlink": False,
            "analytic_root_empty": True,
            "analytic_root_st_dev": dataset_device,
            "free_bytes_after": 220 * 1024**3,
        },
        "forbidden_paths": capture._expected_h_forbidden_paths(
            install_root,
            analytic_root,
        ),
        "actions": [
            {
                "action": "normalize_uniad_server_from_verified_head_blob",
                "performed": False,
                "before": server_claim,
                "after": dict(server_claim),
            },
            {
                "action": "atomically_patch_compose_from_exact_preimage",
                "performed": True,
                "before_sha256": capture.EXPECTED_COMPOSE_INPUT_SHA256,
                "after_sha256": capture.EXPECTED_COMPOSE_OUTPUT_SHA256,
            },
            {
                "action": "create_absent_empty_analytic_root",
                "performed": True,
                "path": str(analytic_root),
            },
            {
                "action": "atomically_install_verified_packet",
                "performed": True,
                "from": str(capture.EXPECTED_PACKET_STAGING_ROOT),
                "to": str(install_root),
            },
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
    hash_payload = dict(receipt)
    hash_payload.pop("receipt_payload_sha256")
    receipt["receipt_payload_sha256"] = digest(
        capture._canonical_json_bytes(hash_payload)
    )
    receipt_payload = capture._preparation_receipt_file_payload(receipt)
    receipt_path = capture.CANONICAL_PREPARATION_RECEIPT_PATH
    receipt_path.with_name(capture.EXPECTED_H_PENDING_BASENAME).unlink(
        missing_ok=True
    )
    receipt_path.unlink(missing_ok=True)
    receipt_path.write_bytes(receipt_payload)
    receipt_path.chmod(0o444)
    pending_path = receipt_path.with_name(capture.EXPECTED_H_PENDING_BASENAME)
    pending_path.hardlink_to(receipt_path)
    envelope = {
        "receipt_file": {
            "path": str(receipt_path),
            "sha256": digest(receipt_payload),
            "bytes": len(receipt_payload),
        },
        "evidence": receipt,
    }
    return envelope, manifest_payload, receipt_payload


def fixture(
    tmp_path: Path,
    *,
    mission_phase: str = capture.EXECUTION_PHASE,
    run_state: object = "IDLE",
) -> tuple[capture.Contract, capture.Hooks, FakeRunner, dict[str, Path]]:
    root = tmp_path.resolve()
    files = root / "files"
    files.mkdir(parents=True)
    mission_state_path = root / "MISSION_STATE.json"
    mission_state_path.write_text(
        json.dumps(
            mission_state_document(mission_phase, run_state),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    repositories = {
        "uniad": root / "UniAD",
        "neuroncap": root / "NeuroNCAP",
        "neurad": root / "neurad-studio",
    }
    for path in repositories.values():
        path.mkdir()
    (repositories["uniad"] / "ckpts").mkdir()
    (repositories["uniad"] / "checkpoints").symlink_to("ckpts")
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
        dataset_map_directories={},
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
                else ["checkpoints"]
                if repo_id == "uniad"
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

    host_preparation, packet_payload, preparation_payload = (
        install_green_h_fixture(mission_state_path)
    )
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
        fetch_raw=github.fetch_raw,
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
                    str(capture.HERE / "capture_environment135.py"),
                    "--local-free-bytes",
                    "500",
                ],
                "canonical_script": str(capture.HERE / "capture_environment135.py"),
            },
            [],
        ),
        preparation_receipt=lambda: (host_preparation, []),
        host_artifact_payloads=lambda: (dict(host_artifacts), []),
        docker_client_path=lambda: docker_client,
        mission_state_path=lambda: mission_state_path,
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
            "host_preparation": host_preparation,
            "dataset_root": mount,
            "mission_state": mission_state_path,
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


def bind_attempt_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    install_root = tmp_path.resolve() / "installed-iter135"
    install_root.mkdir(exist_ok=True)
    preparation_path = install_root / "host_preparation_receipt.json"
    output_path = install_root / "env_receipts.json"
    monkeypatch.setattr(capture, "HERE", install_root)
    monkeypatch.setattr(
        capture,
        "CANONICAL_PREPARER_PATH",
        install_root / "prepare_host135.py",
    )
    monkeypatch.setattr(
        capture,
        "CANONICAL_PACKET_MANIFEST_PATH",
        install_root / "host_packet_manifest.json",
    )
    monkeypatch.setattr(
        capture,
        "CANONICAL_PREPARATION_RECEIPT_PATH",
        preparation_path,
    )
    monkeypatch.setattr(capture, "DEFAULT_OUTPUT", output_path)
    monkeypatch.setattr(capture, "EXPECTED_INSTALL_ROOT", str(install_root))
    return output_path


def persist_h_evidence(host_preparation: dict[str, Any]) -> None:
    """Re-hash and reinstall a deliberately changed otherwise-canonical H fixture."""

    evidence = host_preparation["evidence"]
    packet = evidence["packet"]
    files = packet["files"]
    manifest = {
        "schema": packet["schema"],
        "source_commit": packet["source_commit"],
        "files": {
            name: {
                "sha256": claim["sha256"],
                "bytes": claim["bytes"],
                "mode": claim["mode"],
            }
            for name, claim in files.items()
        },
    }
    manifest_payload = (
        json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    ).encode()
    capture.CANONICAL_PACKET_MANIFEST_PATH.write_bytes(manifest_payload)
    capture.CANONICAL_PACKET_MANIFEST_PATH.chmod(0o644)
    manifest_sha256 = digest(manifest_payload)
    evidence["packet_manifest_sha256"] = manifest_sha256
    packet["independently_supplied_manifest_sha256"] = manifest_sha256
    packet["manifest"].update(
        {
            "sha256": manifest_sha256,
            "bytes": len(manifest_payload),
            "mode": 0o644,
        }
    )
    artifacts = evidence["publication_authority"]["artifacts"]
    artifacts_by_path = {row["path"]: row for row in artifacts}
    for name, claim in files.items():
        payload = (capture.HERE / name).read_bytes()
        artifacts_by_path[capture._packet_repository_path(name)].update(
            {
                "sha256": claim["sha256"],
                "bytes": claim["bytes"],
                "git_blob_oid": capture._git_blob_oid(payload),
            }
        )
    hash_payload = dict(evidence)
    hash_payload.pop("receipt_payload_sha256", None)
    evidence["receipt_payload_sha256"] = digest(
        capture._canonical_json_bytes(hash_payload)
    )
    receipt_payload = capture._preparation_receipt_file_payload(evidence)
    canonical = capture.CANONICAL_PREPARATION_RECEIPT_PATH
    pending = canonical.with_name(capture.EXPECTED_H_PENDING_BASENAME)
    pending.unlink(missing_ok=True)
    canonical.unlink(missing_ok=True)
    canonical.write_bytes(receipt_payload)
    canonical.chmod(0o444)
    pending.hardlink_to(canonical)
    host_preparation["receipt_file"] = {
        "path": str(canonical),
        "sha256": digest(receipt_payload),
        "bytes": len(receipt_payload),
    }


def rehash_h_document(host_preparation: dict[str, Any]) -> None:
    """Keep outer hashes coherent so a hostile test isolates the selected contract."""

    evidence = host_preparation["evidence"]
    hash_payload = dict(evidence)
    hash_payload.pop("receipt_payload_sha256", None)
    evidence["receipt_payload_sha256"] = digest(
        capture._canonical_json_bytes(hash_payload)
    )
    receipt_payload = capture._preparation_receipt_file_payload(evidence)
    host_preparation["receipt_file"] = {
        "path": str(capture.CANONICAL_PREPARATION_RECEIPT_PATH),
        "sha256": digest(receipt_payload),
        "bytes": len(receipt_payload),
    }


def rewrite_bound_mission_state(
    hooks: capture.Hooks,
    path: Path,
    state: dict[str, Any],
) -> None:
    payload = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    (capture.HERE / "MISSION_STATE.json").write_bytes(payload)
    (capture.HERE / "MISSION_STATE.json").chmod(0o644)
    host_preparation, preparation_problems = hooks.preparation_receipt()
    assert preparation_problems == []
    claim = host_preparation["evidence"]["packet"]["files"]["MISSION_STATE.json"]
    claim.update(
        {
            "sha256": digest(payload),
            "bytes": len(payload),
            "mode": path.stat().st_mode & 0o777,
        }
    )
    persist_h_evidence(host_preparation)


def test_environment_admission_mirror_matches_canonical_state_validator() -> None:
    state_path = REPO / "scripts/mission_state.py"
    state_spec = importlib.util.spec_from_file_location(
        "sentinel_mission_state_contract_for_environment_test",
        state_path,
    )
    assert state_spec is not None and state_spec.loader is not None
    state_module = importlib.util.module_from_spec(state_spec)
    state_spec.loader.exec_module(state_module)

    assert capture.EXPECTED_MISSION_STATE_FIELDS == state_module.EXPECTED_STATE_FIELDS
    assert capture.EXPECTED_NEXT_PROGRAM_FIELDS == (
        state_module.EXPECTED_NEXT_PROGRAM_FIELDS
    )
    assert capture.EXPECTED_MISSION_STATE_COMMON == {
        "schema": state_module.EXPECTED_SCHEMA,
        "canonical_repository": state_module.CANONICAL_REPOSITORY,
        "workspace_boundary": state_module.EXPECTED_WORKSPACE_BOUNDARY,
        "trunk": "master",
        "current_completed_iteration": (
            state_module.EXPECTED_CURRENT_COMPLETED_ITERATION
        ),
        "current_result": state_module.EXPECTED_CURRENT_RESULT,
        "current_verdict": state_module.EXPECTED_CURRENT_VERDICT,
        "active_hypothesis": state_module.EXPECTED_ACTIVE_HYPOTHESIS,
        "claim_state": state_module.EXPECTED_CLAIM_STATE,
        "deprecated_pending_hypotheses": (
            state_module.EXPECTED_DEPRECATED_HYPOTHESES
        ),
        "paper_state": state_module.EXPECTED_PAPER_STATE,
        "storage_gate": state_module.EXPECTED_STORAGE_GATE,
    }
    for phase, contract in capture.MISSION_PHASE_CONTRACTS.items():
        authorized, forbidden = state_module.PHASE_ACTION_CONTRACTS[phase]
        assert contract == {
            "run_state": state_module.PHASE_RUN_STATES[phase],
            "authorized_actions": authorized,
            "forbidden_actions": forbidden,
        }


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("missing-top-level", "mission-state:field-set"),
        ("extra-top-level", "mission-state:field-set"),
        ("workspace-extra", "mission-state:contract"),
        ("workspace-bool-as-int", "mission-state:contract"),
        ("completed-bool", "mission-state:contract"),
        ("completed-float", "mission-state:contract"),
        ("claim-nested-type", "mission-state:contract"),
        ("missing-next-field", "mission-state:next-program-field-set"),
        ("extra-next-field", "mission-state:next-program-field-set"),
        ("iteration-bool", "mission-state:next-program"),
        ("iteration-float", "mission-state:next-program"),
        ("authorized-action", "mission-state:next-program"),
        ("forbidden-action-order", "mission-state:next-program"),
        ("run-state-bool", "mission-state:run-state"),
        ("run-state-float", "mission-state:run-state"),
    ],
)
def test_source_bound_mission_state_semantic_drift_is_pre_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    problem: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    state = json.loads(paths["mission_state"].read_text())
    if mutation == "missing-top-level":
        state.pop("claim_state")
    elif mutation == "extra-top-level":
        state["extra"] = None
    elif mutation == "workspace-extra":
        state["workspace_boundary"]["extra"] = "forged"
    elif mutation == "workspace-bool-as-int":
        state["workspace_boundary"][
            "cross_workspace_access_requires_explicit_operator_request"
        ] = 1
    elif mutation == "completed-bool":
        state["current_completed_iteration"] = True
    elif mutation == "completed-float":
        state["current_completed_iteration"] = 134.0
    elif mutation == "claim-nested-type":
        state["claim_state"]["semantic_attribution"] = ["UNRESOLVED"]
    elif mutation == "missing-next-field":
        state["next_program"].pop("authorized_actions")
    elif mutation == "extra-next-field":
        state["next_program"]["extra"] = None
    elif mutation == "iteration-bool":
        state["next_program"]["iteration"] = True
    elif mutation == "iteration-float":
        state["next_program"]["iteration"] = 135.0
    elif mutation == "authorized-action":
        state["next_program"]["authorized_actions"][0] += " forged"
    elif mutation == "forbidden-action-order":
        state["next_program"]["forbidden_actions"].reverse()
    elif mutation == "run-state-bool":
        state["run_state"] = True
    else:
        state["run_state"] = 0.0
    rewrite_bound_mission_state(hooks, paths["mission_state"], state)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"semantic mission-state drift accessed {label}")

    hostile_hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
    )

    with pytest.raises(capture.EnvironmentAdmissionStop, match=problem):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hostile_hooks,
        )

    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("mission_phase", "run_state", "problem"),
    [
        (
            capture.CONTROL_HARDENING_PHASE,
            "UNKNOWN",
            "mission-state:control-hardening-required",
        ),
        (
            capture.EXECUTION_PHASE,
            "UNKNOWN",
            "mission-state:run-state",
        ),
    ],
)
def test_packet_bound_control_stop_precedes_authority_and_runtime_access(
    tmp_path: Path,
    mission_phase: str,
    run_state: str,
    problem: str,
) -> None:
    contract, hooks, runner, paths = fixture(
        tmp_path,
        mission_phase=mission_phase,
        run_state=run_state,
    )
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"stopped state accessed {label}")

    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        disk_free=lambda _path: forbidden("output-disk"),
        device=lambda _path: forbidden("output-device"),
        dataset_read=lambda _path: forbidden("dataset"),
        docker_client_path=lambda: forbidden("docker-client"),
        host_artifact_payloads=lambda: (
            later_calls.append("host-artifacts") or {},
            [],
        ),
        interpreter_receipt=lambda: (
            later_calls.append("interpreter") or {},
            [],
        ),
        invocation_receipt=lambda: (
            later_calls.append("invocation") or {},
            [],
        ),
    )

    with pytest.raises(capture.CaptureError, match=problem):
        run_capture(contract, hooks)

    assert paths["github"].calls == []
    assert runner.calls == []
    assert later_calls == []
    assert list(paths["output"].iterdir()) == []
    assert json.loads(paths["mission_state"].read_text())["run_state"] == run_state


@pytest.mark.parametrize(
    "mutation",
    ["red-verdict", "reported-problem", "receipt-path", "validator-problem"],
)
def test_non_green_h_is_pre_admission_and_creates_no_e_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    host_preparation, preparation_problems = hooks.preparation_receipt()
    host_preparation = json.loads(json.dumps(host_preparation))
    preparation_problems = list(preparation_problems)
    if mutation == "red-verdict":
        host_preparation["evidence"]["verdict"] = capture.INCOMPLETE_VERDICT
    elif mutation == "reported-problem":
        host_preparation["evidence"]["problem_count"] = 1
        host_preparation["evidence"]["problems"] = ["host:red"]
    elif mutation == "receipt-path":
        host_preparation["receipt_file"]["path"] = str(
            output_path.parent / "other" / "host_preparation_receipt.json"
        )
    else:
        preparation_problems.append("preparation:controller-binding")
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"invalid H accessed {label}")

    hostile_hooks = replace(
        hooks,
        preparation_receipt=lambda: (host_preparation, preparation_problems),
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
    )

    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="host-preparation:not-green",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hostile_hooks,
        )

    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("top-missing", "preparation:field-set"),
        ("top-extra", "preparation:field-set"),
        ("receipt-path", "preparation:receipt-file-binding"),
        ("receipt-bytes-bool", "preparation:receipt-file-binding"),
        ("receipt-bytes-float", "preparation:receipt-file-binding"),
        ("packet-missing", "preparation:packet"),
        ("packet-extra", "preparation:packet"),
        ("manifest-staging-path", "preparation:packet-manifest-claim"),
        ("manifest-extra", "preparation:packet-manifest-claim"),
        ("file-live-path", "preparation:packet-file:MISSION_STATE.json:claim"),
        ("file-bytes-bool", "preparation:packet-file:MISSION_STATE.json:claim"),
        ("file-bytes-float", "preparation:packet-file:MISSION_STATE.json:claim"),
        ("file-mode-bool", "preparation:packet-file:MISSION_STATE.json:claim"),
        ("file-document", "preparation:packet-file:MISSION_STATE.json:claim"),
        ("controller-cross-binding", "preparation:controller-binding"),
        ("compose-missing", "preparation:compose-field-set"),
        ("compose-extra", "preparation:compose-field-set"),
        ("compose-patcher", "preparation:compose-patcher-binding"),
        ("compose-target", "preparation:compose-before"),
        ("actions-count", "preparation:actions-count"),
        ("action-extra", "preparation:actions-field-set"),
        ("action-document", "preparation:actions-field-set"),
        ("action-performed-int", "preparation:action-compose"),
        ("action-server-cross-binding", "preparation:action-server-cross-binding"),
        ("action-install-target", "preparation:action-packet-install"),
        ("repositories-extra", "preparation:repositories-field-set"),
        ("repository-phase-missing", "preparation:repository-phase-set"),
        ("repository-row-extra", "preparation:repository:before:uniad"),
        ("repository-row-document", "preparation:repository:before:uniad"),
        ("repository-head", "preparation:repository:before:neuroncap"),
        ("repository-staged-bool", "preparation:repository:before:neurad"),
        ("repository-unsafe-path", "preparation:repository:before:neuroncap"),
        ("repository-unsorted", "preparation:repository:before:neuroncap"),
        ("repository-untracked-drift", "preparation:repository-untracked-race"),
        ("storage-missing", "preparation:storage-field-set"),
        ("storage-extra", "preparation:storage-field-set"),
        ("storage-document", "preparation:storage-field-set"),
        ("storage-device-bool", "preparation:storage-integer-types"),
        ("storage-device-negative", "preparation:storage-device-values"),
        ("storage-free-float", "preparation:storage-integer-types"),
        ("storage-device-cross-binding", "preparation:storage-cross-binding"),
        ("storage-reserve", "preparation:storage-cross-binding"),
        ("forbidden-missing", "preparation:forbidden-paths"),
        ("forbidden-extra", "preparation:forbidden-paths"),
        ("forbidden-true", "preparation:forbidden-paths"),
        ("invocation-missing", "preparation:invocation"),
        ("invocation-extra", "preparation:invocation"),
        ("invocation-match-int", "preparation:invocation"),
        ("invocation-environment", "preparation:invocation"),
        (
            "publication-artifact-bytes-float",
            "preparation:publication-artifact:MISSION_STATE.json",
        ),
        (
            "publication-artifact-document",
            "preparation:publication-artifact:MISSION_STATE.json",
        ),
    ],
)
def test_complete_h_contract_hostile_matrix_stops_before_every_e_hook(
    tmp_path: Path,
    mutation: str,
    problem: str,
) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)
    original, preparation_problems = hooks.preparation_receipt()
    assert preparation_problems == []
    hostile = json.loads(json.dumps(original))
    receipt = hostile["evidence"]
    packet = receipt["packet"]
    files = packet["files"]
    if mutation == "top-missing":
        receipt.pop("compose")
    elif mutation == "top-extra":
        receipt["extra"] = None
    elif mutation == "receipt-path":
        hostile["receipt_file"]["path"] += ".forged"
    elif mutation == "receipt-bytes-bool":
        hostile["receipt_file"]["bytes"] = True
    elif mutation == "receipt-bytes-float":
        hostile["receipt_file"]["bytes"] = float(
            hostile["receipt_file"]["bytes"]
        )
    elif mutation == "packet-missing":
        packet.pop("manifest")
    elif mutation == "packet-extra":
        packet["extra"] = None
    elif mutation == "manifest-staging-path":
        packet["manifest"]["path"] = str(
            capture.CANONICAL_PACKET_MANIFEST_PATH
        )
    elif mutation == "manifest-extra":
        packet["manifest"]["extra"] = None
    elif mutation == "file-live-path":
        files["MISSION_STATE.json"]["path"] = str(
            capture.HERE / "MISSION_STATE.json"
        )
    elif mutation == "file-bytes-bool":
        files["MISSION_STATE.json"]["bytes"] = True
    elif mutation == "file-bytes-float":
        files["MISSION_STATE.json"]["bytes"] = float(
            files["MISSION_STATE.json"]["bytes"]
        )
    elif mutation == "file-mode-bool":
        files["MISSION_STATE.json"]["mode"] = True
    elif mutation == "file-document":
        files["MISSION_STATE.json"] = []
    elif mutation == "controller-cross-binding":
        receipt["controller"] = files["capture_environment135.py"]
    elif mutation == "compose-missing":
        receipt["compose"].pop("after")
    elif mutation == "compose-extra":
        receipt["compose"]["extra"] = None
    elif mutation == "compose-patcher":
        receipt["compose"]["patcher"] = files["prepare_host135.py"]
    elif mutation == "compose-target":
        receipt["compose"]["before"]["path"] += ".forged"
    elif mutation == "actions-count":
        receipt["actions"].pop()
    elif mutation == "action-extra":
        receipt["actions"][1]["extra"] = None
    elif mutation == "action-document":
        receipt["actions"][1] = []
    elif mutation == "action-performed-int":
        receipt["actions"][1]["performed"] = 1
    elif mutation == "action-server-cross-binding":
        receipt["actions"][0]["performed"] = True
    elif mutation == "action-install-target":
        receipt["actions"][3]["to"] += ".forged"
    elif mutation == "repositories-extra":
        receipt["repositories"]["extra"] = None
    elif mutation == "repository-phase-missing":
        receipt["repositories"]["before"].pop("neurad")
    elif mutation == "repository-row-extra":
        receipt["repositories"]["before"]["uniad"]["extra"] = None
    elif mutation == "repository-row-document":
        receipt["repositories"]["before"]["uniad"] = []
    elif mutation == "repository-head":
        receipt["repositories"]["before"]["neuroncap"]["head"] = "f" * 40
    elif mutation == "repository-staged-bool":
        receipt["repositories"]["before"]["neurad"]["staged_paths"] = False
    elif mutation == "repository-unsafe-path":
        receipt["repositories"]["before"]["neuroncap"][
            "untracked_paths"
        ] = ["../escape"]
    elif mutation == "repository-unsorted":
        receipt["repositories"]["before"]["neuroncap"][
            "untracked_paths"
        ] = ["outoutput/z", "outoutput/a"]
    elif mutation == "repository-untracked-drift":
        receipt["repositories"]["after"]["neuroncap"][
            "untracked_paths"
        ].append("outoutput/later")
    elif mutation == "storage-missing":
        receipt["storage"].pop("free_bytes_after")
    elif mutation == "storage-extra":
        receipt["storage"]["extra"] = None
    elif mutation == "storage-document":
        receipt["storage"] = []
    elif mutation == "storage-device-bool":
        receipt["storage"]["dataset_st_dev"] = True
    elif mutation == "storage-device-negative":
        receipt["storage"]["dataset_st_dev"] = -2
        receipt["storage"]["analytic_root_st_dev"] = -2
        receipt["storage"]["root_st_dev"] = -1
    elif mutation == "storage-free-float":
        receipt["storage"]["free_bytes_before"] = float(
            receipt["storage"]["free_bytes_before"]
        )
    elif mutation == "storage-device-cross-binding":
        receipt["storage"]["root_st_dev"] = receipt["storage"]["dataset_st_dev"]
    elif mutation == "storage-reserve":
        receipt["storage"]["free_bytes_after"] = (
            receipt["storage"]["projected_output_bytes"]
            + receipt["storage"]["minimum_reserve_bytes"]
            - 1
        )
    elif mutation == "forbidden-missing":
        receipt["forbidden_paths"].pop(next(iter(receipt["forbidden_paths"])))
    elif mutation == "forbidden-extra":
        receipt["forbidden_paths"]["/tmp/forged"] = False
    elif mutation == "forbidden-true":
        first = next(iter(receipt["forbidden_paths"]))
        receipt["forbidden_paths"][first] = True
    elif mutation == "invocation-missing":
        receipt["invocation"].pop("isolated")
    elif mutation == "invocation-extra":
        receipt["invocation"]["extra"] = None
    elif mutation == "invocation-match-int":
        receipt["invocation"]["environment_matches"] = 1
    elif mutation == "invocation-environment":
        receipt["invocation"]["environment"]["EXTRA"] = "forged"
    elif mutation == "publication-artifact-bytes-float":
        authority_row = next(
            row
            for row in receipt["publication_authority"]["artifacts"]
            if row["path"] == "MISSION_STATE.json"
        )
        authority_row["bytes"] = float(authority_row["bytes"])
    else:
        receipt["publication_authority"]["artifacts"] = [
            row
            for row in receipt["publication_authority"]["artifacts"]
            if row["path"] != "MISSION_STATE.json"
        ]
        receipt["publication_authority"]["artifacts"].append([])
    if not mutation.startswith("receipt-"):
        rehash_h_document(hostile)

    assert problem in capture.validate_host_preparation_evidence(hostile)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"invalid H reached E hook {label}")

    hostile_hooks = replace(
        hooks,
        preparation_receipt=lambda: (hostile, []),
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        fetch_raw=lambda _url: forbidden("github-raw"),
        disk_free=lambda _path: forbidden("disk"),
        device=lambda _path: forbidden("device"),
        dataset_read=lambda _path: forbidden("dataset"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
        mission_state_path=lambda: forbidden("mission-state"),
    )
    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="host-preparation:not-green",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=capture.DEFAULT_OUTPUT,
            patcher_path=paths["patcher"],
            hooks=hostile_hooks,
        )
    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []
    assert not capture.DEFAULT_OUTPUT.exists()
    assert not (
        capture.DEFAULT_OUTPUT.parent / capture.ATTEMPT_MARKER_BASENAME
    ).exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "marker-present",
        "pending-missing",
        "pending-new-inode",
        "canonical-new-inode",
        "pair-writable",
        "third-hardlink",
        "canonical-symlink",
    ],
)
def test_h_success_topology_known_bads_are_pre_admission(
    tmp_path: Path,
    mutation: str,
) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)
    canonical = capture.CANONICAL_PREPARATION_RECEIPT_PATH
    pending = canonical.with_name(capture.EXPECTED_H_PENDING_BASENAME)
    marker = canonical.with_name(capture.EXPECTED_H_ATTEMPT_BASENAME)
    payload = canonical.read_bytes()
    if mutation == "marker-present":
        marker.write_bytes(b"attempt remains\n")
        marker.chmod(0o444)
    elif mutation == "pending-missing":
        pending.unlink()
    elif mutation == "pending-new-inode":
        pending.unlink()
        pending.write_bytes(payload)
        pending.chmod(0o444)
    elif mutation == "canonical-new-inode":
        canonical.unlink()
        canonical.write_bytes(payload)
        canonical.chmod(0o444)
    elif mutation == "pair-writable":
        canonical.chmod(0o644)
    elif mutation == "third-hardlink":
        canonical.with_name("third-host-receipt-link").hardlink_to(canonical)
    else:
        canonical.unlink()
        canonical.symlink_to(pending.name)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"invalid H topology reached E hook {label}")

    hostile_hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
    )
    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="host-preparation:not-green",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=capture.DEFAULT_OUTPUT,
            patcher_path=paths["patcher"],
            hooks=hostile_hooks,
        )
    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []
    assert not capture.DEFAULT_OUTPUT.exists()


def test_h_topology_replay_rejects_parent_replacement_between_coupled_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contract, hooks, _runner, _paths = fixture(tmp_path)
    host_preparation, preparation_problems = hooks.preparation_receipt()
    assert preparation_problems == []
    canonical = capture.CANONICAL_PREPARATION_RECEIPT_PATH
    payload = canonical.read_bytes()
    parent = canonical.parent
    displaced = tmp_path.resolve() / "displaced-h-parent"
    original_open = capture._open_physical_directory
    parent_open_count = 0

    def replace_on_replay(path: Path) -> int:
        nonlocal parent_open_count
        if Path(path) == parent:
            parent_open_count += 1
            if parent_open_count == 2:
                parent.rename(displaced)
                parent.mkdir()
        return original_open(path)

    monkeypatch.setattr(capture, "_open_physical_directory", replace_on_replay)
    with pytest.raises(
        capture.CaptureError,
        match="preparation:receipt-topology:parent-drift",
    ):
        capture._observe_receipt_pair(
            canonical,
            pending_basename=capture.EXPECTED_H_PENDING_BASENAME,
            marker_basename=capture.EXPECTED_H_ATTEMPT_BASENAME,
            payload=capture._preparation_receipt_file_payload(
                host_preparation["evidence"]
            ),
            problem_prefix="preparation:receipt-topology",
        )
    assert payload == (
        displaced / canonical.name
    ).read_bytes()


def test_parent_swap_after_h_replay_cannot_move_e_to_cloned_green_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    admitted_parent = output_path.parent
    clone = tmp_path.resolve() / "cloned-green-h-parent"
    displaced = tmp_path.resolve() / "displaced-admitted-h-parent"
    shutil.copytree(admitted_parent, clone)
    clone_canonical = clone / capture.CANONICAL_PREPARATION_RECEIPT_PATH.name
    clone_pending = clone / capture.EXPECTED_H_PENDING_BASENAME
    clone_pending.unlink()
    clone_pending.hardlink_to(clone_canonical)
    swapped = False

    def swap_after_replay() -> Path:
        nonlocal swapped
        if not swapped:
            admitted_parent.rename(displaced)
            clone.rename(admitted_parent)
            swapped = True
        return paths["mission_state"]

    hostile_hooks = replace(
        hooks,
        mission_state_path=swap_after_replay,
        now=lambda: (_ for _ in ()).throw(
            AssertionError("parent drift reached E clock")
        ),
    )
    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="host-preparation:parent-drift",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hostile_hooks,
        )

    assert swapped is True
    assert not output_path.exists()
    assert not (
        admitted_parent / capture.ATTEMPT_MARKER_BASENAME
    ).exists()
    assert not (
        displaced / capture.ATTEMPT_MARKER_BASENAME
    ).exists()
    assert runner.calls == []
    assert paths["github"].calls == []


def test_parent_swap_after_terminal_h_admission_is_rejected_before_e_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    admission = capture._admit_environment_attempt(hooks)
    admitted_parent = output_path.parent
    displaced = tmp_path.resolve() / "displaced-after-terminal-h-admission"
    admitted_parent.rename(displaced)
    admitted_parent.mkdir()

    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="output:preparation-parent-drift",
    ):
        capture._capture_environment_attempt_admitted(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            admission=admission,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert list(admitted_parent.iterdir()) == []
    assert not (
        displaced / capture.ATTEMPT_MARKER_BASENAME
    ).exists()
    assert runner.calls == []
    assert paths["github"].calls == []


@pytest.mark.parametrize(
    ("clock_value", "expected_problems"),
    [
        (
            object(),
            {"timing:started:TypeError", "timing:finished:TypeError"},
        ),
        (
            datetime(2026, 7, 18, 12, 0),
            {"timing:started:ValueError", "timing:finished:ValueError"},
        ),
    ],
)
def test_initial_clock_fault_is_durable_red_without_runtime_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clock_value: object,
    expected_problems: set[str],
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    hooks = replace(hooks, now=lambda: clock_value)

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output_path,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert set(receipt["problems"]) == expected_problems
    assert receipt["capture_started_at_utc"] is None
    assert receipt["captured_at_utc"] is None
    assert receipt["host"] is None
    assert json.loads(output_path.read_text()) == receipt
    assert runner.calls == []
    assert paths["github"].calls == []


@pytest.mark.parametrize("hostname", [None, 7, False, b"sentinel-gpu"])
def test_non_string_hostname_is_durable_red_and_never_crosses_runtime_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: object,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    hooks = replace(hooks, hostname=lambda: hostname)

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output_path,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert receipt["problems"] == ["host:probe:TypeError"]
    assert receipt["host"] is None
    assert json.loads(output_path.read_text()) == receipt
    assert runner.calls == []
    assert paths["github"].calls == []


def test_terminal_clock_fault_is_durable_red(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, _runner, paths = fixture(tmp_path)
    clock_values = iter(
        [datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc), object()]
    )
    hooks = replace(hooks, now=lambda: next(clock_values))

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output_path,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert receipt["problems"] == ["timing:finished:TypeError"]
    assert receipt["capture_started_at_utc"] == "2026-07-18T12:00:00Z"
    assert receipt["captured_at_utc"] is None
    assert json.loads(output_path.read_text()) == receipt


def test_runtime_type_fault_is_durable_red_with_bounded_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, _runner, paths = fixture(tmp_path)

    def broken_artifacts() -> NoReturn:
        raise KeyError("unretained private detail")

    hooks = replace(hooks, host_artifact_payloads=broken_artifacts)

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output_path,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert receipt["problems"] == ["internal:KeyError"]
    assert "unretained private detail" not in output_path.read_text()
    assert json.loads(output_path.read_text()) == receipt


def test_candidate_serialization_fault_is_replaced_by_durable_red_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, _runner, paths = fixture(tmp_path)
    hooks = replace(
        hooks,
        interpreter_receipt=lambda: ({"hostile": object()}, []),
    )

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output_path,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert receipt["problems"] == ["serialization:TypeError"]
    assert receipt["interpreter"] is None
    assert json.loads(output_path.read_text()) == receipt


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        ("interpreter-missing", "interpreter:receipt-field-set"),
        ("interpreter-extra", "interpreter:receipt-field-set"),
        ("interpreter-bytes-bool", "interpreter:receipt-bytes"),
        ("interpreter-bytes-float", "interpreter:receipt-bytes"),
        ("interpreter-version-list", "interpreter:receipt-version"),
        ("interpreter-implementation-int", "interpreter:receipt-implementation"),
        ("interpreter-problems-tuple", "interpreter:receipt-problem-list"),
        ("invocation-missing", "invocation:receipt-field-set"),
        ("invocation-extra", "invocation:receipt-field-set"),
        ("invocation-sanitized-int", "invocation:receipt-sanitized"),
        ("invocation-isolated-int", "invocation:receipt-isolated"),
        ("invocation-environment-nested-type", "invocation:receipt-environment"),
        ("invocation-argv-tuple", "invocation:receipt-argv"),
        ("invocation-argv-numeric", "invocation:receipt-argv"),
        (
            "invocation-canonical-script-list",
            "invocation:receipt-canonical-script",
        ),
        ("invocation-problems-tuple", "invocation:receipt-problem-list"),
    ],
)
def test_hostile_nested_hook_projections_and_types_are_never_green(
    tmp_path: Path,
    mutation: str,
    problem: str,
) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    assert hooks.interpreter_receipt is not None
    assert hooks.invocation_receipt is not None
    interpreter, interpreter_problems = hooks.interpreter_receipt()
    invocation, invocation_problems = hooks.invocation_receipt()
    interpreter = json.loads(json.dumps(interpreter))
    invocation = json.loads(json.dumps(invocation))
    if mutation == "interpreter-missing":
        interpreter.pop("sha256")
    elif mutation == "interpreter-extra":
        interpreter["extra"] = None
    elif mutation == "interpreter-bytes-bool":
        interpreter["bytes"] = True
    elif mutation == "interpreter-bytes-float":
        interpreter["bytes"] = float(interpreter["bytes"])
    elif mutation == "interpreter-version-list":
        interpreter["version"] = ["3", "10", "14"]
    elif mutation == "interpreter-implementation-int":
        interpreter["implementation"] = 1
    elif mutation == "interpreter-problems-tuple":
        interpreter_problems = ()
    elif mutation == "invocation-missing":
        invocation.pop("isolated")
    elif mutation == "invocation-extra":
        invocation["extra"] = None
    elif mutation == "invocation-sanitized-int":
        invocation["sanitized"] = 1
    elif mutation == "invocation-isolated-int":
        invocation["isolated"] = 1
    elif mutation == "invocation-environment-nested-type":
        invocation["environment"]["PATH"] = [invocation["environment"]["PATH"]]
    elif mutation == "invocation-argv-tuple":
        invocation["argv"] = tuple(invocation["argv"])
    elif mutation == "invocation-argv-numeric":
        invocation["argv"][1] = 1
    elif mutation == "invocation-canonical-script-list":
        invocation["canonical_script"] = [invocation["canonical_script"]]
    else:
        invocation_problems = ()
    hostile_hooks = replace(
        hooks,
        interpreter_receipt=lambda: (interpreter, interpreter_problems),
        invocation_receipt=lambda: (invocation, invocation_problems),
    )

    receipt = run_capture(contract, hostile_hooks)

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert problem in receipt["problems"]
    assert receipt["problem_count"] == len(receipt["problems"])


@pytest.mark.parametrize("existing", [b"prior-attempt\n", b""])
def test_existing_e_receipt_is_preserved_before_any_e_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    existing: bytes,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    output_path.write_bytes(existing)
    contract, hooks, runner, paths = fixture(tmp_path)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"existing E accessed {label}")

    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
    )

    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="output:already-exists",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert output_path.read_bytes() == existing
    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []


@pytest.mark.parametrize(
    ("basename", "problem", "payload"),
    [
        (
            capture.ATTEMPT_MARKER_BASENAME,
            "output:attempt-marker-exists",
            b'{"status":"retained-attempt-marker"}\n',
        ),
        (
            capture.PENDING_RECEIPT_BASENAME,
            "output:pending-exists",
            b'{"status":"PENDING_NONAUTHORITATIVE"}\n',
        ),
    ],
)
def test_existing_attempt_marker_or_pending_receipt_stops_before_e_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    basename: str,
    problem: str,
    payload: bytes,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    retained = output_path.parent / basename
    retained.write_bytes(payload)
    contract, hooks, runner, paths = fixture(tmp_path)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"retained attempt evidence accessed {label}")

    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
        host_artifact_payloads=lambda: forbidden("host-artifacts"),
    )

    with pytest.raises(capture.EnvironmentAdmissionStop, match=problem):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert retained.read_bytes() == payload
    assert not output_path.exists()
    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []


def test_parent_swap_during_marker_creation_writes_only_through_held_dirfd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    original_parent = output_path.parent
    displaced_parent = tmp_path.resolve() / "displaced-iter135"
    external_target = tmp_path.resolve() / "external-target"
    external_target.mkdir()
    original_create = capture._exclusive_create_fsynced
    swapped = False

    def swapping_create(
        parent_fd: int,
        basename: str,
        payload: bytes,
        *,
        label: str,
    ) -> int:
        nonlocal swapped
        if basename == capture.ATTEMPT_MARKER_BASENAME and not swapped:
            original_parent.rename(displaced_parent)
            original_parent.symlink_to(external_target, target_is_directory=True)
            swapped = True
        return original_create(
            parent_fd,
            basename,
            payload,
            label=label,
        )

    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"parent-swap admission accessed {label}")

    monkeypatch.setattr(capture, "_exclusive_create_fsynced", swapping_create)
    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
        fetch_json=lambda _url: forbidden("github"),
    )

    with pytest.raises(capture.CaptureError, match="output:parent-drift"):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert swapped is True
    assert_exact_attempt_marker(
        displaced_parent / capture.ATTEMPT_MARKER_BASENAME
    )
    assert list(external_target.iterdir()) == []
    assert later_calls == []
    assert runner.calls == []
    assert paths["github"].calls == []


def test_parent_swap_after_probes_retains_marker_and_pending_in_held_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    original_parent = output_path.parent
    displaced_parent = tmp_path.resolve() / "displaced-after-probes"
    external_target = tmp_path.resolve() / "external-after-probes"
    external_target.mkdir()
    original_artifacts = hooks.host_artifact_payloads
    assert original_artifacts is not None
    swapped = False

    def swap_then_artifacts() -> tuple[dict[str, bytes], list[str]]:
        nonlocal swapped
        if not swapped:
            original_parent.rename(displaced_parent)
            original_parent.symlink_to(external_target, target_is_directory=True)
            swapped = True
        return original_artifacts()

    hooks = replace(hooks, host_artifact_payloads=swap_then_artifacts)

    with pytest.raises(
        capture.CaptureError,
        match="output:(?:parent-drift|completion-ambiguous)",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    marker = displaced_parent / capture.ATTEMPT_MARKER_BASENAME
    pending = displaced_parent / capture.PENDING_RECEIPT_BASENAME
    assert swapped is True
    assert_exact_attempt_marker(marker)
    assert not pending.exists()
    assert not (displaced_parent / capture.CANONICAL_RECEIPT_BASENAME).exists()
    assert list(external_target.iterdir()) == []
    assert runner.calls
    assert paths["github"].calls


@pytest.mark.parametrize(
    "cleanup_operation",
    ["marker-unlink", "cleanup-sync"],
)
@pytest.mark.parametrize("replacement_kind", ["directory", "symlink"])
@pytest.mark.parametrize("swap_timing", ["before", "after"])
def test_parent_swap_around_each_cleanup_operation_cannot_report_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cleanup_operation: str,
    replacement_kind: str,
    swap_timing: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    original_parent = output_path.parent
    displaced_parent = (
        tmp_path.resolve() / f"displaced-{cleanup_operation}-{replacement_kind}"
    )
    external_target = (
        tmp_path.resolve() / f"external-{cleanup_operation}-{replacement_kind}"
    )
    original_unlink = capture.os.unlink
    original_parent_sync = capture._fsync_attempt_parent
    swapped = False

    def swap_parent() -> None:
        nonlocal swapped
        original_parent.rename(displaced_parent)
        if replacement_kind == "directory":
            original_parent.mkdir()
        else:
            external_target.mkdir()
            original_parent.symlink_to(external_target, target_is_directory=True)
        swapped = True

    def swapping_unlink(path: str, *args, **kwargs) -> None:
        selected_operation = (
            cleanup_operation == "marker-unlink"
            and path == capture.ATTEMPT_MARKER_BASENAME
        )
        if not swapped and selected_operation and swap_timing == "before":
            swap_parent()
        original_unlink(path, *args, **kwargs)
        if not swapped and selected_operation and swap_timing == "after":
            swap_parent()

    def swapping_parent_sync(
        attempt: capture._EnvironmentOutputAttempt,
        *,
        label: str,
    ) -> None:
        selected_operation = (
            cleanup_operation == "cleanup-sync" and label == "cleanup-sync"
        )
        if not swapped and selected_operation and swap_timing == "before":
            swap_parent()
        original_parent_sync(attempt, label=label)
        if not swapped and selected_operation and swap_timing == "after":
            swap_parent()

    monkeypatch.setattr(capture.os, "unlink", swapping_unlink)
    monkeypatch.setattr(capture, "_fsync_attempt_parent", swapping_parent_sync)

    with pytest.raises(
        capture.CaptureError,
        match="output:(?:parent-drift|completion-ambiguous)",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert swapped is True
    assert not output_path.exists()
    if replacement_kind == "directory":
        assert list(original_parent.iterdir()) == []
    else:
        assert original_parent.is_symlink()
        assert list(external_target.iterdir()) == []
    assert (
        displaced_parent / capture.CANONICAL_RECEIPT_BASENAME
    ).is_file()
    assert (
        displaced_parent / capture.ATTEMPT_MARKER_BASENAME
    ).is_file()
    assert (
        displaced_parent / capture.PENDING_RECEIPT_BASENAME
    ).is_file()
    assert runner.calls
    assert paths["github"].calls


@pytest.mark.parametrize(
    "cleanup_operation",
    ["marker-unlink", "cleanup-sync"],
)
@pytest.mark.parametrize("mutation", ["remove", "replace"])
@pytest.mark.parametrize("mutation_timing", ["before", "after"])
def test_canonical_mutation_around_each_cleanup_operation_cannot_report_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cleanup_operation: str,
    mutation: str,
    mutation_timing: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    original_unlink = capture.os.unlink
    original_parent_sync = capture._fsync_attempt_parent
    mutated = False

    def mutate_canonical() -> None:
        nonlocal mutated
        original_unlink(
            capture.CANONICAL_RECEIPT_BASENAME,
            dir_fd=attempt.parent_fd,
        )
        if mutation == "replace":
            descriptor = capture.os.open(
                capture.CANONICAL_RECEIPT_BASENAME,
                capture.os.O_WRONLY
                | capture.os.O_CREAT
                | capture.os.O_EXCL
                | getattr(capture.os, "O_NOFOLLOW", 0),
                0o444,
                dir_fd=attempt.parent_fd,
            )
            try:
                capture._write_all(
                    descriptor,
                    b'{"forged":true}\n',
                    label="test:forged-canonical",
                )
                capture.os.fchmod(descriptor, 0o444)
                capture.os.fsync(descriptor)
            finally:
                capture.os.close(descriptor)
        mutated = True

    def mutating_unlink(path: str, *args, **kwargs) -> None:
        selected_operation = (
            cleanup_operation == "marker-unlink"
            and path == capture.ATTEMPT_MARKER_BASENAME
        )
        if selected_operation and mutation_timing == "before":
            mutate_canonical()
        original_unlink(path, *args, **kwargs)
        if selected_operation and mutation_timing == "after":
            mutate_canonical()

    def mutating_parent_sync(
        active_attempt: capture._EnvironmentOutputAttempt,
        *,
        label: str,
    ) -> None:
        selected_operation = (
            cleanup_operation == "cleanup-sync" and label == "cleanup-sync"
        )
        if selected_operation and mutation_timing == "before":
            mutate_canonical()
        original_parent_sync(active_attempt, label=label)
        if selected_operation and mutation_timing == "after":
            mutate_canonical()

    monkeypatch.setattr(capture.os, "unlink", mutating_unlink)
    monkeypatch.setattr(capture, "_fsync_attempt_parent", mutating_parent_sync)

    try:
        with pytest.raises(capture.CaptureError, match="output:canonical-drift"):
            capture._publish_environment_receipt(attempt, receipt)
    finally:
        attempt.close()

    assert mutated is True
    if mutation == "remove":
        assert not output_path.exists()
    else:
        assert output_path.read_bytes() == b'{"forged":true}\n'


def test_canonical_rename_and_replacement_during_payload_replay_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    payload = capture._serialize_receipt(receipt)
    pending_fd = capture._exclusive_create_fsynced(
        attempt.parent_fd,
        capture.PENDING_RECEIPT_BASENAME,
        payload,
        label="test:pending",
    )
    try:
        pending_info = capture.os.fstat(pending_fd)
    finally:
        capture.os.close(pending_fd)
    capture.os.link(
        capture.PENDING_RECEIPT_BASENAME,
        capture.CANONICAL_RECEIPT_BASENAME,
        src_dir_fd=attempt.parent_fd,
        dst_dir_fd=attempt.parent_fd,
        follow_symlinks=False,
    )
    binding = capture._open_canonical_receipt_binding(
        attempt,
        pending_info=pending_info,
        payload=payload,
    )
    original_read = capture.os.read
    mutated = False

    def rename_then_read(descriptor: int, byte_count: int) -> bytes:
        nonlocal mutated
        if descriptor == binding.descriptor and not mutated:
            capture.os.rename(
                capture.CANONICAL_RECEIPT_BASENAME,
                ".env_receipts.json.EXACT_RECEIPT_DISPLACED_BY_TEST",
                src_dir_fd=attempt.parent_fd,
                dst_dir_fd=attempt.parent_fd,
            )
            forged_fd = capture.os.open(
                capture.CANONICAL_RECEIPT_BASENAME,
                capture.os.O_WRONLY
                | capture.os.O_CREAT
                | capture.os.O_EXCL
                | getattr(capture.os, "O_NOFOLLOW", 0),
                0o444,
                dir_fd=attempt.parent_fd,
            )
            try:
                capture._write_all(
                    forged_fd,
                    b'{"forged":true}\n',
                    label="test:forged-canonical",
                )
                capture.os.fchmod(forged_fd, 0o444)
            finally:
                capture.os.close(forged_fd)
            mutated = True
        return original_read(descriptor, byte_count)

    monkeypatch.setattr(capture.os, "read", rename_then_read)
    try:
        with pytest.raises(capture.CaptureError, match="output:canonical-drift"):
            capture._verify_canonical_receipt(
                attempt,
                binding,
                payload,
                expected_link_count=2,
            )
    finally:
        capture.os.close(binding.descriptor)
        attempt.close()

    assert mutated is True
    assert output_path.read_bytes() == b'{"forged":true}\n'


def test_parent_replacement_inside_canonical_replay_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    payload = capture._serialize_receipt(receipt)
    pending_fd = capture._exclusive_create_fsynced(
        attempt.parent_fd,
        capture.PENDING_RECEIPT_BASENAME,
        payload,
        label="test:pending",
    )
    try:
        pending_info = capture.os.fstat(pending_fd)
    finally:
        capture.os.close(pending_fd)
    capture.os.link(
        capture.PENDING_RECEIPT_BASENAME,
        capture.CANONICAL_RECEIPT_BASENAME,
        src_dir_fd=attempt.parent_fd,
        dst_dir_fd=attempt.parent_fd,
        follow_symlinks=False,
    )
    binding = capture._open_canonical_receipt_binding(
        attempt,
        pending_info=pending_info,
        payload=payload,
    )
    original_directory_identity = capture._directory_identity
    displaced_parent = tmp_path.resolve() / "displaced-during-canonical-replay"
    mutated = False

    def replace_parent_after_identity(descriptor: int) -> tuple[int, int, int]:
        nonlocal mutated
        identity = original_directory_identity(descriptor)
        if descriptor != attempt.parent_fd and not mutated:
            attempt.parent_path.rename(displaced_parent)
            attempt.parent_path.mkdir()
            (attempt.parent_path / capture.CANONICAL_RECEIPT_BASENAME).write_bytes(
                b'{"forged":true}\n'
            )
            mutated = True
        return identity

    monkeypatch.setattr(capture, "_directory_identity", replace_parent_after_identity)
    try:
        with pytest.raises(
            capture.CaptureError,
            match="output:(?:parent|canonical)-drift",
        ):
            capture._verify_canonical_receipt(
                attempt,
                binding,
                payload,
                expected_link_count=2,
            )
    finally:
        capture.os.close(binding.descriptor)
        attempt.close()

    assert mutated is True
    assert output_path.read_bytes() == b'{"forged":true}\n'
    assert (
        displaced_parent / capture.CANONICAL_RECEIPT_BASENAME
    ).read_bytes() == payload


def test_pending_writable_descriptor_is_closed_before_canonical_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    original_create = capture._exclusive_create_fsynced
    original_link = capture.os.link
    pending_descriptor: int | None = None
    link_observed = False

    def recording_create(
        parent_fd: int,
        basename: str,
        payload: bytes,
        *,
        label: str,
    ) -> int:
        nonlocal pending_descriptor
        descriptor = original_create(
            parent_fd,
            basename,
            payload,
            label=label,
        )
        if basename == capture.PENDING_RECEIPT_BASENAME:
            pending_descriptor = descriptor
        return descriptor

    def checking_link(*args, **kwargs) -> None:
        nonlocal link_observed
        assert pending_descriptor is not None
        with pytest.raises(OSError):
            capture.os.fstat(pending_descriptor)
        link_observed = True
        original_link(*args, **kwargs)

    monkeypatch.setattr(capture, "_exclusive_create_fsynced", recording_create)
    monkeypatch.setattr(capture.os, "link", checking_link)

    try:
        capture._publish_environment_receipt(attempt, receipt)
    finally:
        attempt.close()

    assert link_observed is True
    assert output_path.read_bytes() == capture._serialize_receipt(receipt)


@pytest.mark.parametrize(
    "fault",
    ["marker-write", "marker-file-sync", "marker-parent-sync"],
)
def test_marker_failures_retain_nonauthoritative_attempt_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    original_write_all = capture._write_all
    original_fsync = capture.os.fsync
    original_parent_sync = capture._fsync_attempt_parent

    def failing_write_all(descriptor: int, payload: bytes, *, label: str) -> None:
        if fault == "marker-write" and label == "output:attempt-marker":
            raise capture.CaptureError("injected:marker-write")
        original_write_all(descriptor, payload, label=label)

    def failing_fsync(descriptor: int) -> None:
        if fault == "marker-file-sync":
            raise OSError("injected-marker-file-sync")
        original_fsync(descriptor)

    def failing_parent_sync(
        attempt: capture._EnvironmentOutputAttempt,
        *,
        label: str,
    ) -> None:
        if fault == "marker-parent-sync" and label == "attempt-marker-sync":
            raise capture.CaptureError("injected:marker-parent-sync")
        original_parent_sync(attempt, label=label)

    monkeypatch.setattr(capture, "_write_all", failing_write_all)
    monkeypatch.setattr(capture.os, "fsync", failing_fsync)
    monkeypatch.setattr(capture, "_fsync_attempt_parent", failing_parent_sync)

    with pytest.raises(capture.CaptureError):
        capture._begin_environment_output_attempt(output_path)

    marker = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    assert marker.exists()
    if fault == "marker-write":
        assert marker.read_bytes() == b""
    else:
        assert_exact_attempt_marker(marker)
    assert not (output_path.parent / capture.PENDING_RECEIPT_BASENAME).exists()
    assert not output_path.exists()


@pytest.mark.parametrize("entropy", [b"", b"x" * 32, b"x" * 64])
def test_attempt_randomness_must_be_exact_and_domain_separated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entropy: bytes,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    monkeypatch.setattr(capture.os, "urandom", lambda _count: entropy)

    with pytest.raises(capture.CaptureError, match="output:attempt-randomness"):
        capture._begin_environment_output_attempt(output_path)

    assert not (
        output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    ).exists()
    assert not output_path.exists()


@pytest.mark.parametrize(
    "fault",
    [
        "pending-write",
        "pending-file-sync",
        "pending-parent-sync",
        "link",
        "canonical-link-sync",
        "marker-unlink",
        "cleanup-sync",
    ],
)
def test_publication_failures_retain_consistent_attempt_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    payload = capture._serialize_receipt(receipt)
    original_write_all = capture._write_all
    original_fsync = capture.os.fsync
    original_parent_sync = capture._fsync_attempt_parent
    original_link = capture.os.link
    original_unlink = capture.os.unlink

    def failing_write_all(descriptor: int, data: bytes, *, label: str) -> None:
        if fault == "pending-write" and label == "output:pending":
            raise capture.CaptureError("injected:pending-write")
        original_write_all(descriptor, data, label=label)

    def failing_fsync(descriptor: int) -> None:
        if fault == "pending-file-sync":
            raise OSError("injected-pending-file-sync")
        original_fsync(descriptor)

    def failing_parent_sync(
        active_attempt: capture._EnvironmentOutputAttempt,
        *,
        label: str,
    ) -> None:
        if (
            fault == "pending-parent-sync"
            and label == "pending-sync"
        ) or (
            fault == "canonical-link-sync"
            and label == "canonical-link-sync"
        ) or (fault == "cleanup-sync" and label == "cleanup-sync"):
            raise capture.CaptureError(f"injected:{fault}")
        original_parent_sync(active_attempt, label=label)

    def failing_link(*_args, **_kwargs) -> None:
        if fault == "link":
            raise OSError("injected-link")
        original_link(*_args, **_kwargs)

    def failing_unlink(path: str, *args, **kwargs) -> None:
        if (
            fault == "marker-unlink"
            and path == capture.ATTEMPT_MARKER_BASENAME
        ):
            raise OSError(f"injected-{fault}")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(capture, "_write_all", failing_write_all)
    monkeypatch.setattr(capture.os, "fsync", failing_fsync)
    monkeypatch.setattr(capture, "_fsync_attempt_parent", failing_parent_sync)
    monkeypatch.setattr(capture.os, "link", failing_link)
    monkeypatch.setattr(capture.os, "unlink", failing_unlink)

    try:
        with pytest.raises(capture.CaptureError):
            capture._publish_environment_receipt(attempt, receipt)
    finally:
        attempt.close()

    marker = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    pending = output_path.parent / capture.PENDING_RECEIPT_BASENAME
    canonical_expected = fault in {
        "canonical-link-sync",
        "marker-unlink",
        "cleanup-sync",
    }
    assert_exact_attempt_marker(marker, attempt=attempt)
    assert pending.is_file()
    assert pending.read_bytes() == (b"" if fault == "pending-write" else payload)
    assert output_path.exists() is canonical_expected
    if canonical_expected:
        assert output_path.read_bytes() == payload


@pytest.mark.parametrize("fault_kind", ["capture-error", "base-exception"])
def test_fault_after_marker_removal_durably_restores_nonauthority_and_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault_kind: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    payload = capture._serialize_receipt(receipt)
    original_pair_check = capture._verify_environment_receipt_pair

    def fail_terminal_pair(
        active_attempt: capture._EnvironmentOutputAttempt,
        binding: capture._CanonicalReceiptBinding,
        observed_payload: bytes,
        *,
        marker_present: bool,
    ) -> capture._ReceiptPairObservation:
        if not marker_present:
            if fault_kind == "base-exception":
                raise KeyboardInterrupt("injected-post-marker-removal")
            raise capture.CaptureError("injected:post-marker-removal")
        return original_pair_check(
            active_attempt,
            binding,
            observed_payload,
            marker_present=marker_present,
        )

    monkeypatch.setattr(
        capture,
        "_verify_environment_receipt_pair",
        fail_terminal_pair,
    )
    try:
        expected_error = (
            KeyboardInterrupt
            if fault_kind == "base-exception"
            else capture.CaptureError
        )
        with pytest.raises(expected_error):
            capture._publish_environment_receipt(attempt, receipt)
    finally:
        attempt.close()

    marker = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    pending = output_path.parent / capture.PENDING_RECEIPT_BASENAME
    assert_exact_attempt_marker(marker, attempt=attempt)
    assert pending.read_bytes() == payload
    assert output_path.read_bytes() == payload
    assert pending.stat(follow_symlinks=False).st_ino == output_path.stat(
        follow_symlinks=False
    ).st_ino
    assert pending.stat(follow_symlinks=False).st_nlink == 2
    assert output_path.stat(follow_symlinks=False).st_nlink == 2


@pytest.mark.parametrize(
    "fault",
    [
        "entry-probe",
        "existing-bind",
        "absent-create",
        "absent-close",
        "absent-bind",
        "parent-sync",
        "parent-replay",
        "terminal-verify",
    ],
)
def test_every_restore_failure_branch_is_completion_ambiguous(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    marker_path = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    absent_branch = fault.startswith("absent-")
    if absent_branch:
        marker_path.unlink()
    if fault == "entry-probe":
        monkeypatch.setattr(
            capture,
            "_dir_entry_exists",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError("injected:restore-entry-probe")
            ),
        )
    elif fault in {"existing-bind", "absent-bind"}:
        monkeypatch.setattr(
            capture,
            "_bind_attempt_marker",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError(f"injected:{fault}")
            ),
        )
    elif fault == "absent-create":
        monkeypatch.setattr(
            capture,
            "_exclusive_create_fsynced",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError("injected:restore-create")
            ),
        )
    elif fault == "absent-close":
        original_create = capture._exclusive_create_fsynced
        original_close = capture.os.close
        created_descriptor: int | None = None
        close_failed = False

        def recording_create(*args, **kwargs) -> int:
            nonlocal created_descriptor
            created_descriptor = original_create(*args, **kwargs)
            return created_descriptor

        def perform_then_fail_close(descriptor: int) -> None:
            nonlocal close_failed
            original_close(descriptor)
            if descriptor == created_descriptor and not close_failed:
                close_failed = True
                raise OSError("injected-restore-close")

        monkeypatch.setattr(
            capture,
            "_exclusive_create_fsynced",
            recording_create,
        )
        monkeypatch.setattr(capture.os, "close", perform_then_fail_close)
    elif fault == "parent-sync":
        monkeypatch.setattr(
            capture,
            "_fsync_attempt_parent",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError("injected:restore-parent-sync")
            ),
        )
    elif fault == "parent-replay":
        monkeypatch.setattr(
            capture,
            "_replay_attempt_parent",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError("injected:restore-parent-replay")
            ),
        )
    else:
        monkeypatch.setattr(
            capture,
            "_verify_attempt_marker",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                capture.CaptureError("injected:restore-terminal-verify")
            ),
        )
    try:
        with pytest.raises(
            capture.CaptureError,
            match="output:completion-ambiguous",
        ):
            capture._restore_marker_or_raise_completion_ambiguous(
                attempt,
                capture.CaptureError("injected:original-completion-fault"),
            )
    finally:
        attempt.close()


@pytest.mark.parametrize(
    ("fault", "problem"),
    [
        ("stat-error", "output:attempt-marker-probe"),
        ("still-present", "output:attempt-marker-still-present"),
        ("retained-descriptor", "output:attempt-marker-probe"),
    ],
)
def test_every_terminal_marker_probe_failure_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    problem: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    marker_path = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    if fault == "stat-error":
        original_stat = capture.os.stat

        def fail_marker_stat(path, *args, **kwargs):
            if path == capture.ATTEMPT_MARKER_BASENAME:
                raise OSError("injected-marker-stat")
            return original_stat(path, *args, **kwargs)

        monkeypatch.setattr(capture.os, "stat", fail_marker_stat)
    elif fault == "retained-descriptor":
        marker_path.unlink()
        capture.os.close(attempt.marker_fd)
        attempt.marker_fd = -1
    try:
        with pytest.raises(capture.CaptureError, match=problem):
            capture._attempt_marker_absent(attempt)
    finally:
        attempt.close()


@pytest.mark.parametrize(
    "witness_mutation",
    [
        "wrong-type",
        "exact-clone",
        "attempt-id",
        "nonce",
        "verdict",
        "parent",
        "inode",
        "bytes-bool",
        "bytes-float",
        "payload-sha",
    ],
)
def test_capture_consumes_exact_completion_witness_or_restores_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    witness_mutation: str,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, _runner, paths = fixture(tmp_path)
    original_publish = capture._publish_environment_receipt

    def forged_publish(
        attempt: capture._EnvironmentOutputAttempt,
        receipt: dict[str, Any],
    ) -> object:
        witness = original_publish(attempt, receipt)
        if witness_mutation == "wrong-type":
            return {
                "attempt_id": witness.attempt_id,
                "completion_nonce": witness.completion_nonce,
                "verdict": witness.verdict,
                "parent_identity": witness.parent_identity,
                "receipt_inode": witness.receipt_inode,
                "byte_count": witness.byte_count,
                "payload_sha256": witness.payload_sha256,
            }
        if witness_mutation == "exact-clone":
            return replace(witness)
        if witness_mutation == "attempt-id":
            return replace(witness, attempt_id="f" * 64)
        if witness_mutation == "nonce":
            return replace(witness, completion_nonce=b"\xff" * 32)
        if witness_mutation == "verdict":
            return replace(witness, verdict="FORGED")
        if witness_mutation == "parent":
            return replace(
                witness,
                parent_identity=(
                    witness.parent_identity[0],
                    witness.parent_identity[1] + 1,
                    witness.parent_identity[2],
                ),
            )
        if witness_mutation == "inode":
            return replace(
                witness,
                receipt_inode=(
                    witness.receipt_inode[0],
                    witness.receipt_inode[1] + 1,
                ),
            )
        if witness_mutation == "bytes-bool":
            return replace(witness, byte_count=True)
        if witness_mutation == "bytes-float":
            return replace(witness, byte_count=float(witness.byte_count))
        return replace(witness, payload_sha256="f" * 64)

    monkeypatch.setattr(
        capture,
        "_publish_environment_receipt",
        forged_publish,
    )
    with pytest.raises(
        capture.CaptureError,
        match="output:completion-witness",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )
    marker = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    pending = output_path.parent / capture.PENDING_RECEIPT_BASENAME
    assert_exact_attempt_marker(marker)
    assert pending.is_file() and output_path.is_file()
    assert pending.read_bytes() == output_path.read_bytes()
    assert pending.stat(follow_symlinks=False).st_ino == output_path.stat(
        follow_symlinks=False
    ).st_ino
    assert pending.stat(follow_symlinks=False).st_nlink == 2


def test_completion_witness_exact_clone_and_replay_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    receipt = {
        "schema": "iter135.environment_receipts.audit-fixture.v1",
        "verdict": "I135_ENVIRONMENT_READY",
        "problem_count": 0,
        "problems": [],
    }
    try:
        witness = capture._publish_environment_receipt(attempt, receipt)
        with pytest.raises(
            capture.CaptureError,
            match="output:completion-witness$",
        ):
            capture._consume_environment_completion_witness(
                attempt,
                receipt,
                replace(witness),
            )
        capture._consume_environment_completion_witness(
            attempt,
            receipt,
            witness,
        )
        with pytest.raises(
            capture.CaptureError,
            match="output:completion-witness-replayed",
        ):
            capture._consume_environment_completion_witness(
                attempt,
                receipt,
                witness,
            )
    finally:
        attempt.close()


def test_exact_marker_payload_replay_on_a_new_inode_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    attempt = capture._begin_environment_output_attempt(output_path)
    marker_path = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    try:
        marker_path.unlink()
        marker_path.write_bytes(attempt.marker_payload)
        marker_path.chmod(0o444)
        with pytest.raises(
            capture.CaptureError,
            match="output:attempt-marker-drift",
        ):
            capture._verify_attempt_marker(attempt)
    finally:
        attempt.close()


def test_link_failure_after_probes_retains_nonauthoritative_attempt_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)

    def fail_link(*_args, **_kwargs) -> NoReturn:
        raise OSError("forced-link-failure")

    monkeypatch.setattr(capture.os, "link", fail_link)

    with pytest.raises(capture.CaptureError, match="output:link:OSError"):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    marker_path = output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    pending_path = output_path.parent / capture.PENDING_RECEIPT_BASENAME
    marker = json.loads(marker_path.read_text())
    pending = json.loads(pending_path.read_text())
    assert marker["authority"] == "NONE"
    assert marker["status"] == "ATTEMPT_IN_PROGRESS_NO_ENVIRONMENT_VERDICT"
    assert marker["pending_receipt"] == capture.PENDING_RECEIPT_BASENAME
    assert "no authority" in marker["publication_rule"]
    assert "NONAUTHORITATIVE" in pending_path.name
    assert pending["schema"] == contract.schema
    assert pending["verdict"] == contract.ready_verdict
    assert not output_path.exists()
    assert runner.calls
    assert paths["github"].calls


def test_arbitrary_e_destination_is_rejected_before_any_e_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, runner, paths = fixture(tmp_path)
    attempted = output_path.parent / "attacker-selected.json"
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"arbitrary output accessed {label}")

    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
    )

    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="output:not-canonical",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=attempted,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert not attempted.exists()
    assert not output_path.exists()
    assert later_calls == []
    assert runner.calls == []


def test_symlinked_canonical_install_parent_is_rejected_during_h_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    physical_install = root / "physical-iter135"
    physical_install.mkdir()
    linked_install = root / "linked-iter135"
    linked_install.symlink_to(physical_install, target_is_directory=True)
    output_path = linked_install / "env_receipts.json"
    monkeypatch.setattr(capture, "HERE", linked_install)
    monkeypatch.setattr(
        capture,
        "CANONICAL_PREPARATION_RECEIPT_PATH",
        linked_install / "host_preparation_receipt.json",
    )
    monkeypatch.setattr(capture, "DEFAULT_OUTPUT", output_path)
    contract, hooks, runner, paths = fixture(tmp_path)
    later_calls: list[str] = []

    def forbidden(label: str) -> NoReturn:
        later_calls.append(label)
        raise AssertionError(f"symlinked output accessed {label}")

    hooks = replace(
        hooks,
        now=lambda: forbidden("clock"),
        hostname=lambda: forbidden("host"),
        run=lambda _argv: forbidden("runtime"),
    )

    with pytest.raises(
        capture.EnvironmentAdmissionStop,
        match="host-preparation:not-green",
    ):
        capture.capture_environment_attempt(
            contract,
            host_commit=HOST_COMMIT,
            local_free_bytes=2_000,
            output_path=output_path,
            patcher_path=paths["patcher"],
            hooks=hooks,
        )

    assert not output_path.exists()
    assert later_calls == []
    assert runner.calls == []


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
    workflows_url = (
        f"{capture.GITHUB_API_ROOT}/actions/workflows/{capture.GITHUB_WORKFLOW_FILE}/runs?"
        f"branch={capture.GITHUB_BRANCH}&event=push&head_sha={HOST_COMMIT}&"
        f"per_page={capture.MAX_GITHUB_WORKFLOW_RUNS}&page=1"
    )
    jobs_url = (
        f"{capture.GITHUB_API_ROOT}/actions/runs/{WORKFLOW_RUN_ID}/attempts/1/jobs?"
        f"per_page={capture.MAX_GITHUB_JOBS}&page=1"
    )
    expected_urls = [
        f"{capture.GITHUB_API_ROOT}/commits/{HOST_COMMIT}?per_page=100&page=1",
        branch_url,
        workflows_url,
        jobs_url,
        workflows_url,
        f"{capture.GITHUB_API_ROOT}/git/trees/{github.tree_sha}?recursive=1",
        *[
            f"{capture.GITHUB_API_ROOT}/contents/{urllib.parse.quote(path, safe='/')}?ref={HOST_COMMIT}"
            for path in capture.HOST_PUBLICATION_ARTIFACT_PATHS
        ],
        branch_url,
        workflows_url,
        jobs_url,
        workflows_url,
        branch_url,
    ]
    assert github.calls == expected_urls
    assert len(github.calls) == 13
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
        (["check (3.10)"], "host-publication-authority:job-envelope"),
        (
            ["check (3.10)", "check (3.10)"],
            "host-publication-authority:required-check-set",
        ),
        (
            ["check (3.10)", "unexpected green check"],
            "host-publication-authority:unexpected-check",
        ),
        (
            [*capture.REQUIRED_GITHUB_CHECKS, "unexpected green check"],
            "host-publication-authority:job-envelope",
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
    job_calls = [url for url in github.calls if "/attempts/" in url and "/jobs?" in url]
    assert job_calls == [
        f"{capture.GITHUB_API_ROOT}/actions/runs/{WORKFLOW_RUN_ID}/attempts/1/jobs?"
        f"per_page={capture.MAX_GITHUB_JOBS}&page=1"
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


def test_workflow_rerun_started_during_initial_authority_proof_fails_closed(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.workflow_documents = [
        workflow_document(HOST_COMMIT),
        workflow_document(
            HOST_COMMIT,
            [workflow_run_row(HOST_COMMIT, run_attempt=2)],
        ),
    ]

    receipt = run_capture(contract, hooks)

    assert "host-publication-authority:workflow-run-replay" in receipt["problems"]
    assert receipt["host_publication_authority"] is None
    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT


def test_workflow_rerun_started_during_terminal_authority_proof_fails_closed(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    github.workflow_documents = [
        workflow_document(HOST_COMMIT),
        workflow_document(HOST_COMMIT),
        workflow_document(HOST_COMMIT),
        workflow_document(
            HOST_COMMIT,
            [workflow_run_row(HOST_COMMIT, run_attempt=2)],
        ),
    ]

    receipt = run_capture(contract, hooks)

    assert (
        "host-publication-authority:terminal:workflow-run-replay"
        in receipt["problems"]
    )
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


def test_uniad_checkpoints_symlink_contract_is_enforced(tmp_path: Path) -> None:
    """The load-bearing `checkpoints` symlink must exist, be a symlink, target `ckpts`,
    and be the only untracked entry; every deviation must fail closed."""

    # Missing untracked entry: the link exists physically but git does not report it.
    contract, hooks, runner, _paths = fixture(tmp_path)
    uniad = str(contract.repositories["uniad"]["path"])
    runner.repositories[uniad]["untracked"] = []
    receipt = run_capture(contract, hooks)
    assert "repository:uniad:checkpoints-untracked-missing" in receipt["problems"]

    # Wrong target: the symlink points somewhere other than `ckpts`.
    contract, hooks, runner, paths = fixture(tmp_path / "wrong-target")
    uniad_root = Path(contract.repositories["uniad"]["path"])
    (uniad_root / "checkpoints").unlink()
    (uniad_root / "checkpoints").symlink_to("elsewhere")
    receipt = run_capture(contract, hooks)
    assert "repository:uniad:checkpoints-symlink" in receipt["problems"]

    # Regular file impostor instead of a symlink.
    contract, hooks, runner, paths = fixture(tmp_path / "regular-file")
    uniad_root = Path(contract.repositories["uniad"]["path"])
    (uniad_root / "checkpoints").unlink()
    (uniad_root / "checkpoints").write_bytes(b"not a symlink\n")
    receipt = run_capture(contract, hooks)
    assert "repository:uniad:checkpoints-symlink" in receipt["problems"]

    # Extra stray artifact next to the contractual link.
    contract, hooks, runner, paths = fixture(tmp_path / "extra-stray")
    uniad = str(contract.repositories["uniad"]["path"])
    runner.repositories[uniad]["untracked"] = ["checkpoints", "stray_weights.pt"]
    receipt = run_capture(contract, hooks)
    assert "repository:uniad:unexpected-untracked:1" in receipt["problems"]


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


@pytest.mark.parametrize("hostile_device", [True, 2.0])
def test_dataset_and_storage_device_numeric_json_aliases_fail_closed(
    tmp_path: Path,
    hostile_device: object,
) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    aliased_hooks = replace(
        hooks,
        device=lambda path: 3 if path == Path("/") else hostile_device,
    )

    receipt = run_capture(contract, aliased_hooks)

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert receipt["problem_count"] > 0
    for problem in (
        "dataset:dataset-device-type",
        "dataset:mount-device-type",
        "storage:filesystem-device-type",
        "storage:mount-device-type",
    ):
        assert problem in receipt["problems"]


def test_dataset_and_storage_negative_device_ids_fail_closed(tmp_path: Path) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    negative_hooks = replace(
        hooks,
        device=lambda path: 1 if path == Path("/") else -2,
    )

    receipt = run_capture(contract, negative_hooks)

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert receipt["problem_count"] > 0
    for problem in (
        "dataset:dataset-device-negative",
        "dataset:mount-device-negative",
        "storage:filesystem-device-negative",
        "storage:mount-device-negative",
    ):
        assert problem in receipt["problems"]


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


def test_successful_attempt_retains_exact_pair_and_removes_only_attempt_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = bind_attempt_destination(tmp_path, monkeypatch)
    contract, hooks, _runner, paths = fixture(tmp_path)

    receipt = capture.capture_environment_attempt(
        contract,
        host_commit=HOST_COMMIT,
        local_free_bytes=2_000,
        output_path=output,
        patcher_path=paths["patcher"],
        hooks=hooks,
    )

    assert json.loads(output.read_text()) == receipt
    assert not (output.parent / capture.ATTEMPT_MARKER_BASENAME).exists()
    pending = output.parent / capture.PENDING_RECEIPT_BASENAME
    assert pending.read_bytes() == output.read_bytes()
    assert pending.stat(follow_symlinks=False).st_ino == output.stat(
        follow_symlinks=False
    ).st_ino
    assert pending.stat(follow_symlinks=False).st_nlink == 2
    assert output.stat(follow_symlinks=False).st_nlink == 2
    assert pending.stat(follow_symlinks=False).st_mode & 0o777 == 0o444
    assert output.stat(follow_symlinks=False).st_mode & 0o777 == 0o444
    assert {
        capture.CANONICAL_RECEIPT_BASENAME,
        capture.PENDING_RECEIPT_BASENAME,
    }.issubset({path.name for path in output.parent.iterdir()})
    assert capture.ATTEMPT_MARKER_BASENAME not in {
        path.name for path in output.parent.iterdir()
    }
    assert output.stat().st_mode & 0o777 == 0o444
    assert output.stat().st_nlink == 2
    assert output.read_bytes() == capture._serialize_receipt(receipt)


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
    assert len(contract.dataset_archives) == 12
    assert sum(row[1] for row in contract.dataset_archives.values()) == 315_285_139_203
    assert len(contract.dataset_metadata_files) == 13
    assert len(contract.dataset_map_anchors) == 5
    assert set(contract.dataset_map_directories) == {"basemap", "expansion", "prediction"}


@pytest.mark.parametrize(
    "mutation",
    [
        "schema-bytes",
        "verdict-bytes",
        "remote-bytes-bool",
        "repository-path-list-tuple",
        "untracked-role-int",
        "dataset-archive-bytes-float",
        "dataset-metadata-list",
        "storage-bool-int",
        "image-id-bytes",
        "projected-bytes-float",
    ],
)
def test_manifest_contract_never_normalizes_hostile_types(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    module = capture._load_module_from_stable_bytes(
        capture.CANONICAL_MANIFEST_PATH,
        f"iter135_contract_type_fixture_{mutation}",
    )
    if mutation == "schema-bytes":
        module.EXPECTED_ENV_SCHEMA = module.EXPECTED_ENV_SCHEMA.encode()
    elif mutation == "verdict-bytes":
        module.EXPECTED_ENV_VERDICT = module.EXPECTED_ENV_VERDICT.encode()
    elif mutation == "remote-bytes-bool":
        role = next(iter(module.EXPECTED_REMOTE_FILES))
        row = module.EXPECTED_REMOTE_FILES[role]
        module.EXPECTED_REMOTE_FILES[role] = (row[0], row[1], True)
    elif mutation == "repository-path-list-tuple":
        module.EXPECTED_REPOSITORIES["uniad"]["staged_paths"] = ()
    elif mutation == "untracked-role-int":
        binding = next(iter(module.EXPECTED_REQUIRED_UNTRACKED_BINDINGS))
        module.EXPECTED_REQUIRED_UNTRACKED_BINDINGS[binding] = 1
    elif mutation == "dataset-archive-bytes-float":
        name = next(iter(module.EXPECTED_DATASET_ARCHIVES))
        row = module.EXPECTED_DATASET_ARCHIVES[name]
        module.EXPECTED_DATASET_ARCHIVES[name] = (row[0], float(row[1]))
    elif mutation == "dataset-metadata-list":
        module.EXPECTED_DATASET_METADATA_FILES = list(
            module.EXPECTED_DATASET_METADATA_FILES
        )
    elif mutation == "storage-bool-int":
        module.EXPECTED_STORAGE_IDENTITY["filesystem_empty"] = 1
    elif mutation == "image-id-bytes":
        name = next(iter(module.EXPECTED_IMAGE_IDS))
        module.EXPECTED_IMAGE_IDS[name] = module.EXPECTED_IMAGE_IDS[name].encode()
    else:
        module.PROJECTED_OUTPUT_BYTES = float(module.PROJECTED_OUTPUT_BYTES)
    monkeypatch.setattr(
        capture,
        "_load_module_from_stable_bytes",
        lambda *_args, **_kwargs: module,
    )

    with pytest.raises(
        capture.CaptureError,
        match="canonical-manifest:contract-types",
    ):
        capture.load_contract()


def test_main_never_loads_manifest_before_h_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    fixture(tmp_path)
    manifest_loaded = False

    def reject_admission(_hooks: capture.Hooks) -> NoReturn:
        raise capture.EnvironmentAdmissionStop("injected:h-not-admitted")

    def forbidden_load(*_args, **_kwargs) -> NoReturn:
        nonlocal manifest_loaded
        manifest_loaded = True
        raise AssertionError("manifest loaded before H admission")

    monkeypatch.setattr(capture, "_admit_environment_attempt", reject_admission)
    monkeypatch.setattr(capture, "load_contract", forbidden_load)

    result = capture.main(
        [
            "--host-commit",
            HOST_COMMIT,
            "--local-free-bytes",
            "2000",
            "--output",
            str(output_path),
        ]
    )

    assert result == 2
    assert manifest_loaded is False
    assert not (
        output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    ).exists()


def test_manifest_mutation_after_h_admission_is_rejected_before_exec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = bind_attempt_destination(tmp_path, monkeypatch)
    fixture(tmp_path)
    manifest_path = capture.HERE / "make_launch_manifest.py"
    side_effect = tmp_path.resolve() / "manifest-executed"
    original_admit = capture._admit_environment_attempt

    def admit_then_mutate(hooks: capture.Hooks) -> capture._EnvironmentAdmission:
        admission = original_admit(hooks)
        manifest_path.chmod(0o644)
        manifest_path.write_text(
            "from pathlib import Path\n"
            f"Path({str(side_effect)!r}).write_text('executed')\n"
        )
        return admission

    monkeypatch.setattr(capture, "CANONICAL_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(capture, "_admit_environment_attempt", admit_then_mutate)

    result = capture.main(
        [
            "--host-commit",
            HOST_COMMIT,
            "--local-free-bytes",
            "2000",
            "--output",
            str(output_path),
        ]
    )

    assert result == 2
    assert not side_effect.exists()
    assert not (
        output_path.parent / capture.ATTEMPT_MARKER_BASENAME
    ).exists()


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
    tmp_path: Path,
) -> None:
    _contract, hooks, _runner, _paths = fixture(tmp_path)
    expected, expected_problems = hooks.preparation_receipt()
    assert expected_problems == []
    bound, problems = capture.load_and_validate_preparation_receipt()

    assert problems == []
    assert bound == expected
    controller = capture.CANONICAL_PREPARER_PATH
    controller_payload = controller.read_bytes()
    controller.write_bytes(b"# hostile replacement\n")
    _bound, drift = capture.load_and_validate_preparation_receipt()
    assert "preparation:controller-binding" in drift
    assert "preparation:packet-file:prepare_host135.py:binding" in drift

    controller.write_bytes(controller_payload)
    controller.chmod(0o755)
    manifest_path = capture.CANONICAL_PACKET_MANIFEST_PATH
    original_manifest = manifest_path.read_bytes()
    hostile_manifests = (
        b'{"schema":"first","schema":"second",' + original_manifest[1:],
        b'{"hostile":Infinity,' + original_manifest[1:],
    )
    for hostile_manifest in hostile_manifests:
        manifest_path.write_bytes(hostile_manifest)
        _bound, hostile_problems = (
            capture.load_and_validate_preparation_receipt()
        )
        assert "preparation:packet-manifest-json:ValueError" in hostile_problems
        assert "preparation:packet-manifest-replay" in hostile_problems
    manifest_path.write_bytes(original_manifest)


@pytest.mark.parametrize(
    ("field", "hostile_value"),
    [
        ("bytes", 7.0),
        ("bytes", True),
        ("mode", 292.0),
        ("mode", True),
    ],
)
def test_file_claims_reject_numeric_json_aliases(
    field: str,
    hostile_value: object,
) -> None:
    actual = {
        "path": "/tmp/exact-file-claim",
        "sha256": "a" * 64,
        "bytes": 7,
        "mode": 292,
    }
    hostile = dict(actual)
    hostile[field] = hostile_value

    assert capture._same_file_claim(actual, actual)
    assert not capture._same_file_claim(actual, hostile)


@pytest.mark.parametrize("mutation", ["missing", "extra", "non-string-path"])
def test_file_claims_require_exact_object_shape(mutation: str) -> None:
    actual = {
        "path": "/tmp/exact-file-claim",
        "sha256": "a" * 64,
        "bytes": 7,
        "mode": 292,
    }
    hostile = dict(actual)
    if mutation == "missing":
        hostile.pop("mode")
    elif mutation == "extra":
        hostile["extra"] = None
    else:
        hostile["path"] = ["/tmp/exact-file-claim"]

    assert not capture._same_file_claim(actual, hostile)


@pytest.mark.parametrize(
    "mutation",
    ["artifact-bytes-float", "artifact-bytes-bool", "artifact-extra", "artifact-row-list"],
)
def test_preparation_publication_artifacts_require_recursive_exact_json(
    mutation: str,
) -> None:
    source_commit = "a" * 40
    artifacts = [
        {
            "path": (
                "experiments/iter135_neuroncap_blind_braking_dose_response/"
                "payload.txt"
            ),
            "sha256": "b" * 64,
            "bytes": 7,
            "git_blob_oid": "c" * 40,
            "git_mode": "100644",
        }
    ]
    authority = {
        "schema": capture.PUBLICATION_AUTHORITY_SCHEMA,
        "repository": capture.GITHUB_REPOSITORY,
        "branch": capture.GITHUB_BRANCH,
        "source_commit": source_commit,
        "branch_head_sha": source_commit,
        "required_checks": list(capture.REQUIRED_GITHUB_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 700 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": source_commit,
                "app_slug": capture.EXPECTED_CHECK_APP,
            }
            for index, name in enumerate(capture.REQUIRED_GITHUB_CHECKS)
        ],
        "artifacts": json.loads(json.dumps(artifacts)),
        "verified": True,
    }
    assert capture._publication_authority_problems(
        authority,
        source_commit=source_commit,
        artifacts=artifacts,
        label="preparation:publication-authority",
    ) == []

    if mutation == "artifact-bytes-float":
        authority["artifacts"][0]["bytes"] = 7.0
    elif mutation == "artifact-bytes-bool":
        authority["artifacts"][0]["bytes"] = True
    elif mutation == "artifact-extra":
        authority["artifacts"][0]["extra"] = {"nested": []}
    else:
        authority["artifacts"][0] = ["not", "an", "artifact"]

    assert capture._publication_authority_problems(
        authority,
        source_commit=source_commit,
        artifacts=artifacts,
        label="preparation:publication-authority",
    ) == ["preparation:publication-authority:contract"]


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


def test_workflow_run_number_selects_latest_despite_nonmonotonic_ids_and_times() -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(
            commit,
            run_id=9_999,
            suite_id=19_999,
            run_number=740,
            minute=20,
            status="completed",
            conclusion="failure",
        ),
        workflow_run_row(
            commit,
            run_id=1,
            suite_id=2,
            run_number=741,
            minute=0,
        ),
    ]
    selected = capture._project_exact_workflow_run(workflow_document(commit, rows), commit)
    assert selected["id"] == 1
    assert selected["run_number"] == 741


def test_same_sha_validation_branch_cannot_mask_failed_master_workflow() -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(
            commit,
            run_id=1,
            suite_id=11,
            run_number=740,
            status="completed",
            conclusion="failure",
        ),
        workflow_run_row(
            commit,
            run_id=2,
            suite_id=12,
            run_number=741,
            branch="ci-validate-b14",
        ),
    ]

    with pytest.raises(capture.CaptureError, match="workflow-run-binding"):
        capture._project_exact_workflow_run(workflow_document(commit, rows), commit)


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

    with pytest.raises(capture.CaptureError, match="workflow-run-binding"):
        capture._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize(
    "hostile_workflow_id",
    [True, float(capture.GITHUB_WORKFLOW_ID)],
)
def test_workflow_run_workflow_id_requires_exact_json_integer(
    hostile_workflow_id: object,
) -> None:
    commit = "a" * 40
    row = workflow_run_row(commit)
    row["workflow_id"] = hostile_workflow_id

    with pytest.raises(capture.CaptureError, match="workflow-run-binding"):
        capture._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize("mutation", ["noncanonical", "reversed"])
def test_workflow_run_timestamps_are_canonical_and_ordered(mutation: str) -> None:
    commit = "a" * 40
    row = workflow_run_row(commit)
    if mutation == "noncanonical":
        row["created_at"] = "2026-7-18t12:0:0z"
    else:
        row["created_at"] = github_timestamp(31)

    with pytest.raises(capture.CaptureError, match="workflow-run-timestamp"):
        capture._project_exact_workflow_run(workflow_document(commit, [row]), commit)


@pytest.mark.parametrize(
    ("status", "conclusion"),
    [("completed", "failure"), ("queued", None), ("in_progress", None)],
)
def test_latest_canonical_workflow_run_must_be_green(
    status: str, conclusion: str | None
) -> None:
    commit = "a" * 40
    rows = [
        workflow_run_row(commit, run_id=1, suite_id=11, run_number=740),
        workflow_run_row(
            commit,
            run_id=2,
            suite_id=12,
            run_number=741,
            minute=3,
            status=status,
            conclusion=conclusion,
        ),
    ]

    with pytest.raises(capture.CaptureError, match="workflow-run-not-green"):
        capture._project_exact_workflow_run(workflow_document(commit, rows), commit)


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
        for index in range(capture.MAX_GITHUB_WORKFLOW_RUNS)
    ]
    selected = capture._project_exact_workflow_run(
        workflow_document(commit, rows),
        commit,
    )
    assert selected["run_number"] == 199

    truncated = {"total_count": 101, "workflow_runs": rows}
    with pytest.raises(capture.CaptureError, match="workflow-run-envelope"):
        capture._project_exact_workflow_run(truncated, commit)


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
    workflow = capture._project_exact_workflow_run(workflow_document(commit), commit)
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

    with pytest.raises(capture.CaptureError, match=problem):
        capture._project_exact_checks(document, commit, workflow)


@pytest.mark.parametrize(
    ("selected_run_id", "hostile_run_id"),
    [(1, True), (WORKFLOW_RUN_ID, float(WORKFLOW_RUN_ID))],
)
def test_exact_attempt_job_run_id_requires_exact_json_integer(
    selected_run_id: int,
    hostile_run_id: object,
) -> None:
    commit = "a" * 40
    workflow = capture._project_exact_workflow_run(
        workflow_document(
            commit,
            [workflow_run_row(commit, run_id=selected_run_id)],
        ),
        commit,
    )
    document = job_document(commit, run_id=selected_run_id)
    document["jobs"][0]["run_id"] = hostile_run_id

    with pytest.raises(capture.CaptureError, match="check-not-green"):
        capture._project_exact_checks(document, commit, workflow)


@pytest.mark.parametrize("mutation", ["missing", "bool", "float"])
def test_exact_attempt_job_run_attempt_requires_positive_exact_json_integer(
    mutation: str,
) -> None:
    commit = "a" * 40
    workflow = capture._project_exact_workflow_run(workflow_document(commit), commit)
    document = job_document(commit)
    if mutation == "missing":
        document["jobs"][0].pop("run_attempt")
    elif mutation == "bool":
        document["jobs"][0]["run_attempt"] = True
    else:
        document["jobs"][0]["run_attempt"] = 1.0

    with pytest.raises(capture.CaptureError, match="check-not-green"):
        capture._project_exact_checks(document, commit, workflow)


def test_daemon_version_projection_accepts_both_docker_generations() -> None:
    """Docker 29 moved GitCommit, GoVersion, BuildTime, and Experimental into the Engine
    component's Details (Experimental as a string); older engines carry top-level fields."""

    legacy = {
        "Platform": {"Name": "Docker Engine - Community"},
        "Version": "27.0.0",
        "ApiVersion": "1.46",
        "MinAPIVersion": "1.24",
        "GitCommit": "abc1234",
        "GoVersion": "go1.21.0",
        "Os": "linux",
        "Arch": "amd64",
        "BuildTime": "Mon Jan 1 00:00:00 2026",
        "Experimental": False,
    }
    row = capture._daemon_version_projection(legacy)
    assert row["experimental"] is False and row["git_commit"] == "abc1234"

    modern = {
        "Platform": {"Name": "Docker Engine - Community"},
        "Version": "29.6.1",
        "ApiVersion": "1.55",
        "MinAPIVersion": "1.40",
        "Os": "linux",
        "Arch": "amd64",
        "Components": [
            {
                "Name": "Engine",
                "Version": "29.6.1",
                "Details": {
                    "GitCommit": "8ec5ab3",
                    "GoVersion": "go1.26.4",
                    "BuildTime": "Fri Jun 26 11:40:26 2026",
                    "Experimental": "false",
                },
            }
        ],
    }
    row = capture._daemon_version_projection(modern)
    assert row["experimental"] is False
    assert row["git_commit"] == "8ec5ab3"
    assert row["go_version"] == "go1.26.4"

    hostile = dict(modern)
    hostile["Components"] = [
        {"Name": "Engine", "Details": dict(modern["Components"][0]["Details"])}
    ]
    hostile["Components"][0]["Details"]["Experimental"] = "maybe"
    with pytest.raises(capture.CaptureError, match="experimental"):
        capture._daemon_version_projection(hostile)


def test_artifact_replay_rejects_drift_and_accepts_large_payloads(tmp_path: Path) -> None:
    """The raw-media replay must byte-compare committed artifacts of any bound size and
    fail closed on a single flipped byte."""

    contract, hooks, _runner, paths = fixture(tmp_path)
    github = paths["github"]
    receipt_rel = capture.HOST_PUBLICATION_ARTIFACT_PATHS[1]
    big = b"{\"pad\": \"" + b"a" * (2 * 1024 * 1024) + b"\"}\n"
    github.artifacts[receipt_rel] = big
    receipt = run_capture(contract, hooks)
    # The oversized local payload no longer fails the payload bound, but its bytes now
    # disagree with the locally captured receipt file, so drift (or tree binding) fires.
    assert receipt["host_publication_authority"] is None

    contract, hooks, _runner, paths = fixture(tmp_path / "drift")
    github = paths["github"]
    original = github.artifacts[receipt_rel]
    github.artifacts[receipt_rel] = original[:-2] + b"X\n"
    receipt = run_capture(contract, hooks)
    assert receipt["host_publication_authority"] is None
    assert any(
        "host-publication-authority" in problem for problem in receipt["problems"]
    )


def test_dataset_map_directory_contract_is_enforced(tmp_path: Path) -> None:
    """A contract-pinned map subdirectory must exist as a physical directory with the exact
    file set; strays and symlinks fail closed."""

    problems: list[str] = []
    maps_root = tmp_path / "maps"
    (maps_root / "expansion").mkdir(parents=True)
    for name in ("a.json", "b.json"):
        (maps_root / "expansion" / name).write_text("{}\n")
    (maps_root / "anchor.png").write_bytes(b"png")

    capture._dataset_directory_snapshot(
        maps_root,
        {"anchor.png"},
        "maps",
        problems,
        expected_directories={"expansion"},
    )
    assert problems == []

    capture._dataset_directory_snapshot(
        maps_root / "expansion", {"a.json", "b.json"}, "maps:expansion", problems
    )
    assert problems == []

    capture._dataset_directory_snapshot(
        maps_root / "expansion", {"a.json"}, "maps:expansion", problems
    )
    assert "dataset:maps:expansion:file-set" in problems

    problems = []
    (maps_root / "stray-dir").mkdir()
    capture._dataset_directory_snapshot(
        maps_root,
        {"anchor.png"},
        "maps",
        problems,
        expected_directories={"expansion"},
    )
    assert "dataset:maps:nonphysical-file:stray-dir" in problems
    assert "dataset:maps:file-set" in problems

    problems = []
    link_root = tmp_path / "link-maps"
    link_root.mkdir()
    (link_root / "anchor.png").write_bytes(b"png")
    (link_root / "expansion").symlink_to(maps_root / "expansion")
    capture._dataset_directory_snapshot(
        link_root,
        {"anchor.png"},
        "maps",
        problems,
        expected_directories={"expansion"},
    )
    assert "dataset:maps:nonphysical-directory:expansion" in problems
