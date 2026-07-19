#!/usr/bin/env python3
"""Prepare the exact Iteration-135 execution-host contract without launching work.

The controller is deliberately one-shot.  It accepts only the fixed staging and installation
paths, verifies an independently supplied packet-manifest digest, records every accepted
preimage, and preserves a red receipt after any failure.  It never starts or removes a container,
touches the GPU, resets a repository, deletes evidence, or retries a failed preparation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "iter135.host_preparation_receipt.v1"
PACKET_SCHEMA = "iter135.host_packet_manifest.v1"
READY_VERDICT = "I135_HOST_PREPARATION_OK"
INCOMPLETE_VERDICT = "I135_HOST_PREPARATION_INCOMPLETE"
PUBLICATION_AUTHORITY_SCHEMA = "iter135.github_publication_authority.v1"

GITHUB_REPOSITORY = "manfromnowhere143/sentinel"
GITHUB_BRANCH = "master"
GITHUB_API_ROOT = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
GITHUB_WORKFLOW_ID = 304353015
GITHUB_WORKFLOW_NAME = "ci"
GITHUB_WORKFLOW_FILE = "ci.yml"
GITHUB_WORKFLOW_PATH = ".github/workflows/ci.yml"
REQUIRED_GITHUB_CHECKS = ("check (3.10)", "check (3.11)")
EXPECTED_CHECK_APP = "github-actions"
MAX_GITHUB_RESPONSE_BYTES = 1 << 20
MAX_GITHUB_WORKFLOW_RESPONSE_BYTES = 8 << 20
MAX_GITHUB_WORKFLOW_RUNS = 100
MAX_GITHUB_JOBS = 100
MAX_GITHUB_TREE_RESPONSE_BYTES = 16 << 20
MAX_GITHUB_TREE_ENTRIES = 20_000

STACK = Path("/opt/sentinel-stack")
PACKET_ROOT = STACK / ".iter135-packet"
INSTALL_ROOT = STACK / "iter135"
PACKET_MANIFEST_NAME = "host_packet_manifest.json"
RECEIPT_NAME = "host_preparation_receipt.json"
CONTROLLER_NAME = "prepare_host135.py"

ITER135_PAYLOAD_NAMES = (
    "HYPOTHESIS.md",
    "extract_union_windows.py",
    "generate_nested_dose_schedules.py",
    "dose_schedules.json",
    "server_patch_union_release.py",
    "server_patch_blind_dose.py",
    "analyze_dose135.py",
    "collect_proof135.py",
    "run_dose135.sh",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "capture_environment135.py",
    "verify_tooling135.py",
    "patch_compose_dose_env.py",
    "make_launch_manifest.py",
    "authorize_launch135.py",
)
REQUIRED_PACKET_FILES = (
    "MISSION_STATE.json",
    *ITER135_PAYLOAD_NAMES,
    "tooling_verification_receipt.json",
    CONTROLLER_NAME,
)
EXPERIMENT_REPOSITORY_ROOT = "experiments/iter135_neuroncap_blind_braking_dose_response"
PACKET_REPOSITORY_PATHS = {
    name: (
        "MISSION_STATE.json"
        if name == "MISSION_STATE.json"
        else f"{EXPERIMENT_REPOSITORY_ROOT}/{name}"
    )
    for name in REQUIRED_PACKET_FILES
}
EXECUTABLE_PACKET_FILES = {
    "capture_environment135.py",
    "run_smoke135.sh",
    "validate_smoke135.py",
    CONTROLLER_NAME,
}
EXPECTED_PACKET_MODES = {
    name: (0o755 if name in EXECUTABLE_PACKET_FILES else 0o644)
    for name in REQUIRED_PACKET_FILES
}

UNIAD_HEAD = "4827b8be0823e90862caa75d9d146b2ae800b72f"
# UniAD's untracked set is required to be exactly this tuple, not empty.  `checkpoints` is a
# load-bearing symlink to the gitignored `ckpts` payload: the tracked config
# `projects/configs/stage2_e2e/base_e2e.py` reads `anchor_info_path=
# "checkpoints/motion_anchor_infos_mode6.pkl"`, which only resolves through it.  Removing the link
# to satisfy an empty-untracked contract would pass host preparation and then fail the later smoke
# run.  The link cannot be tracked or gitignored either: UniAD is third-party and its `.gitignore`
# is tracked, so editing it would violate the frozen dirty-path contract instead.  Excluding the
# link via `.git/info/exclude` was rejected: it would empty the observation without changing the
# host, making the receipt attest an untracked set that does not exist.  The receipt must state
# what is true, so the contract names the exception explicitly.
UNIAD_REQUIRED_UNTRACKED = ("checkpoints",)
NEURONCAP_HEAD = "ecdcf284e2b7b83c537f3292a06c0adddff55811"
NEURAD_HEAD = "b25f717b23d85c865d469bf52a0bd03b244014be"
UNIAD_SERVER_SHA256 = "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424"
UNIAD_SERVER_BYTES = 4_519
COMPOSE_INPUT_SHA256 = "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
COMPOSE_INPUT_BYTES = 3_380
COMPOSE_OUTPUT_SHA256 = "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
COMPOSE_OUTPUT_BYTES = 3_613

DATASET_ROOT = Path("/datasets/nuscenes-full")
ANALYTIC_ROOT = DATASET_ROOT / "sentinel-i135-outoutput"
SMOKE_ROOT = DATASET_ROOT / "sentinel-i135-smoke-evidence"
MINIMUM_REMOTE_FREE_BYTES = 100 * 1024**3
PROJECTED_OUTPUT_BYTES = 72_380_432_384
MINIMUM_RESERVE_BYTES = 25 * 1024**3
EXPECTED_MOUNT = {
    "mount_target": str(DATASET_ROOT),
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ENVIRONMENT = {
    "DOCKER_CONFIG": "/nonexistent",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "SENTINEL_I135_PREPARE_SANITIZED": "1",
    "TZ": "UTC",
}


class PreparationError(RuntimeError):
    """A stable preparation contract failed."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        raise PreparationError("publication-authority:redirect")


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-key")
        result[key] = value
    return result


def _reject_nonfinite_json(_value: str) -> None:
    raise ValueError("non-finite-number")


def _git_blob_oid(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def _fetch_json(url: str) -> Any:
    """Fetch one bounded GitHub API document over authenticated-server TLS."""

    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise PreparationError("publication-authority:url")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "sentinel-iter135-host-authority/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    if "/git/trees/" in parsed.path:
        response_limit = MAX_GITHUB_TREE_RESPONSE_BYTES
    elif "/actions/workflows/" in parsed.path and parsed.path.endswith("/runs"):
        response_limit = MAX_GITHUB_WORKFLOW_RESPONSE_BYTES
    else:
        response_limit = MAX_GITHUB_RESPONSE_BYTES
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context),
        _NoRedirect(),
    )
    try:
        with opener.open(request, timeout=15) as response:
            if response.geturl() != url:
                raise PreparationError("publication-authority:redirect")
            if response.status != 200:
                raise PreparationError("publication-authority:http-status")
            content_type = response.headers.get_content_type()
            if content_type not in {"application/json", "application/vnd.github+json"}:
                raise PreparationError("publication-authority:content-type")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    declared_bytes = int(declared, 10)
                except ValueError as error:
                    raise PreparationError("publication-authority:content-length") from error
                if declared_bytes < 0 or declared_bytes > response_limit:
                    raise PreparationError("publication-authority:content-length")
            payload = response.read(response_limit + 1)
    except PreparationError:
        raise
    except (OSError, TimeoutError, urllib.error.URLError) as error:
        raise PreparationError(
            f"publication-authority:transport:{type(error).__name__}"
        ) from error
    if len(payload) > response_limit:
        raise PreparationError("publication-authority:response-size")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise PreparationError("publication-authority:json") from error


def _canonical_github_utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None
    return parsed if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value else None


def _project_exact_workflow_run(
    document: object,
    source_commit: str,
    *,
    prefix: str = "publication-authority",
) -> dict[str, Any]:
    """Select the exact latest push run of the canonical workflow on ``master``.

    ``run_number`` is GitHub's workflow-local run sequence. Numeric object ids and response
    ordering are identities and transport details, never chronology.
    """

    runs = document.get("workflow_runs") if isinstance(document, Mapping) else None
    total_count = document.get("total_count") if isinstance(document, Mapping) else None
    if (
        type(total_count) is not int
        or not isinstance(runs, list)
        or total_count != len(runs)
        or total_count < 1
        or total_count > MAX_GITHUB_WORKFLOW_RUNS
    ):
        raise PreparationError(f"{prefix}:workflow-run-envelope")
    projected: list[dict[str, Any]] = []
    run_ids: set[int] = set()
    suite_ids: set[int] = set()
    run_numbers: set[int] = set()
    for run in runs:
        if not isinstance(run, Mapping):
            raise PreparationError(f"{prefix}:workflow-run-row")
        run_id = run.get("id")
        suite_id = run.get("check_suite_id")
        run_number = run.get("run_number")
        run_attempt = run.get("run_attempt")
        if (
            type(run_id) is not int
            or run_id <= 0
            or type(suite_id) is not int
            or suite_id <= 0
            or type(run_number) is not int
            or run_number <= 0
            or type(run_attempt) is not int
            or run_attempt <= 0
        ):
            raise PreparationError(f"{prefix}:workflow-run-row")
        if (
            run_id in run_ids
            or suite_id in suite_ids
            or run_number in run_numbers
        ):
            raise PreparationError(f"{prefix}:workflow-run-identity")
        run_ids.add(run_id)
        suite_ids.add(suite_id)
        run_numbers.add(run_number)
        created_at = _canonical_github_utc(run.get("created_at"))
        updated_at = _canonical_github_utc(run.get("updated_at"))
        started_value = run.get("run_started_at")
        run_started_at = (
            _canonical_github_utc(started_value) if started_value is not None else None
        )
        if (
            created_at is None
            or updated_at is None
            or created_at > updated_at
            or (
                started_value is not None
                and run_started_at is not None
                and not (created_at <= run_started_at <= updated_at)
            )
            or (started_value is not None and run_started_at is None)
        ):
            raise PreparationError(f"{prefix}:workflow-run-timestamp")
        expected_run_url = f"{GITHUB_API_ROOT}/actions/runs/{run_id}"
        if (
            type(run.get("workflow_id")) is not int
            or run.get("workflow_id") != GITHUB_WORKFLOW_ID
            or run.get("name") != GITHUB_WORKFLOW_NAME
            or run.get("path") != GITHUB_WORKFLOW_PATH
            or run.get("head_branch") != GITHUB_BRANCH
            or run.get("head_sha") != source_commit
            or run.get("event") != "push"
            or not isinstance(run.get("status"), str)
            or (
                run.get("conclusion") is not None
                and not isinstance(run.get("conclusion"), str)
            )
            or run.get("url") != expected_run_url
            or run.get("jobs_url") != f"{expected_run_url}/jobs"
        ):
            raise PreparationError(f"{prefix}:workflow-run-binding")
        projected.append(
            {
                "id": run_id,
                "check_suite_id": suite_id,
                "workflow_id": GITHUB_WORKFLOW_ID,
                "name": GITHUB_WORKFLOW_NAME,
                "path": GITHUB_WORKFLOW_PATH,
                "head_branch": GITHUB_BRANCH,
                "head_sha": source_commit,
                "event": "push",
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "run_number": run_number,
                "run_attempt": run_attempt,
                "created_at": run.get("created_at"),
                "run_started_at": started_value,
                "updated_at": run.get("updated_at"),
            }
        )
    selected = max(projected, key=lambda row: row["run_number"])
    if (
        selected["status"] != "completed"
        or selected["conclusion"] != "success"
        or selected["run_started_at"] is None
    ):
        raise PreparationError(f"{prefix}:workflow-run-not-green")
    return selected


def _project_exact_checks(
    document: object,
    source_commit: str,
    workflow_run: Mapping[str, Any],
    *,
    prefix: str = "publication-authority",
) -> list[dict[str, Any]]:
    """Validate the two jobs from the selected workflow run's exact current attempt."""

    runs = document.get("jobs") if isinstance(document, Mapping) else None
    total_count = document.get("total_count") if isinstance(document, Mapping) else None
    if (
        type(total_count) is not int
        or not isinstance(runs, list)
        or total_count != len(runs)
        or total_count != len(REQUIRED_GITHUB_CHECKS)
        or total_count > MAX_GITHUB_JOBS
    ):
        raise PreparationError(f"{prefix}:job-envelope")
    selected: dict[str, Mapping[str, Any]] = {}
    identities: set[int] = set()
    for run in runs:
        if not isinstance(run, Mapping):
            raise PreparationError(f"{prefix}:job-row")
        name = run.get("name")
        if name not in REQUIRED_GITHUB_CHECKS:
            raise PreparationError(f"{prefix}:unexpected-check")
        run_id = run.get("id")
        if type(run_id) is not int or run_id <= 0:
            raise PreparationError(f"{prefix}:job-row")
        if run_id in identities:
            raise PreparationError(f"{prefix}:duplicate-check-id")
        identities.add(run_id)
        if name in selected:
            raise PreparationError(f"{prefix}:required-check-set")
        started_at = _canonical_github_utc(run.get("started_at"))
        completed_at = _canonical_github_utc(run.get("completed_at"))
        workflow_created_at = _canonical_github_utc(workflow_run.get("created_at"))
        workflow_updated_at = _canonical_github_utc(workflow_run.get("updated_at"))
        if (
            started_at is None
            or completed_at is None
            or workflow_created_at is None
            or workflow_updated_at is None
            or not (
                workflow_created_at
                <= started_at
                <= completed_at
                <= workflow_updated_at
            )
        ):
            raise PreparationError(f"{prefix}:check-timestamp:{name}")
        expected_run_id = workflow_run.get("id")
        expected_run_attempt = workflow_run.get("run_attempt")
        job_run_id = run.get("run_id")
        job_run_attempt = run.get("run_attempt")
        if (
            run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or type(job_run_id) is not int
            or job_run_id <= 0
            or job_run_id != expected_run_id
            or type(job_run_attempt) is not int
            or job_run_attempt <= 0
            or job_run_attempt != expected_run_attempt
            or run.get("head_sha") != source_commit
            or run.get("head_branch") != GITHUB_BRANCH
            or run.get("workflow_name") != GITHUB_WORKFLOW_NAME
            or run.get("url") != f"{GITHUB_API_ROOT}/actions/jobs/{run_id}"
            or run.get("run_url") != f"{GITHUB_API_ROOT}/actions/runs/{expected_run_id}"
            or run.get("check_run_url")
            != f"{GITHUB_API_ROOT}/check-runs/{run_id}"
        ):
            raise PreparationError(f"{prefix}:check-not-green:{name}")
        selected[name] = run
    if set(selected) != set(REQUIRED_GITHUB_CHECKS):
        raise PreparationError(f"{prefix}:required-check-set")
    checks: list[dict[str, Any]] = []
    for name in REQUIRED_GITHUB_CHECKS:
        row = selected[name]
        check_id = row.get("id")
        projected = {
            "name": name,
            "id": check_id,
            "status": row.get("status"),
            "conclusion": row.get("conclusion"),
            "head_sha": row.get("head_sha"),
            "app_slug": EXPECTED_CHECK_APP,
        }
        if projected != {
            "name": name,
            "id": check_id,
            "status": "completed",
            "conclusion": "success",
            "head_sha": source_commit,
            "app_slug": EXPECTED_CHECK_APP,
        } or type(check_id) is not int or check_id <= 0:
            raise PreparationError(f"{prefix}:check-not-green:{name}")
        checks.append(projected)
    if len({row["id"] for row in checks}) != len(checks):
        raise PreparationError(f"{prefix}:duplicate-check-id")
    return checks


def verify_publication_authority(
    source_commit: str,
    fetch_json: Callable[[str], Any] = _fetch_json,
    *,
    artifact_bindings: Mapping[str, Mapping[str, Any]],
    expected_git_modes: Mapping[str, str],
) -> dict[str, Any]:
    """Require current master and its exact latest successful ``ci.yml`` push attempt."""

    if not isinstance(source_commit, str) or not _COMMIT_RE.fullmatch(source_commit):
        raise PreparationError("publication-authority:source-commit")
    branch_url = f"{GITHUB_API_ROOT}/branches/{GITHUB_BRANCH}"
    workflow_runs_url = (
        f"{GITHUB_API_ROOT}/actions/workflows/{GITHUB_WORKFLOW_FILE}/runs?"
        f"branch={GITHUB_BRANCH}&event=push&head_sha={source_commit}&"
        f"per_page={MAX_GITHUB_WORKFLOW_RUNS}&page=1"
    )
    commit_url = f"{GITHUB_API_ROOT}/git/commits/{source_commit}"
    try:
        branch_document = fetch_json(branch_url)
        workflow_runs_document = fetch_json(workflow_runs_url)
        commit_document = fetch_json(commit_url)
    except PreparationError:
        raise
    except Exception as error:
        # Never include exception text: an injected transport can carry credentials or response data.
        raise PreparationError(
            f"publication-authority:fetch:{type(error).__name__}"
        ) from error
    branch_commit = (
        branch_document.get("commit") if isinstance(branch_document, Mapping) else None
    )
    branch_head = branch_commit.get("sha") if isinstance(branch_commit, Mapping) else None
    if (
        not isinstance(branch_document, Mapping)
        or branch_document.get("name") != GITHUB_BRANCH
        or branch_head != source_commit
    ):
        raise PreparationError("publication-authority:branch-head")
    workflow_run = _project_exact_workflow_run(
        workflow_runs_document,
        source_commit,
    )
    jobs_url = (
        f"{GITHUB_API_ROOT}/actions/runs/{workflow_run['id']}/attempts/"
        f"{workflow_run['run_attempt']}/jobs?per_page={MAX_GITHUB_JOBS}&page=1"
    )
    try:
        jobs_document = fetch_json(jobs_url)
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:jobs-fetch:{type(error).__name__}"
        ) from error
    checks = _project_exact_checks(jobs_document, source_commit, workflow_run)
    try:
        workflow_replay_document = fetch_json(workflow_runs_url)
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:workflow-replay-fetch:{type(error).__name__}"
        ) from error
    if _project_exact_workflow_run(
        workflow_replay_document,
        source_commit,
    ) != workflow_run:
        raise PreparationError("publication-authority:workflow-run-replay")
    bindings = dict(artifact_bindings)
    modes = dict(expected_git_modes)
    if (
        not bindings
        or set(bindings) != set(modes)
        or len(bindings) != len(set(bindings))
        or any(
            path.startswith("/")
            or ".." in Path(path).parts
            or mode not in {"100644", "100755"}
            for path, mode in modes.items()
        )
    ):
        raise PreparationError("publication-authority:artifact-contract")
    commit_tree = commit_document.get("tree") if isinstance(commit_document, Mapping) else None
    tree_sha = commit_tree.get("sha") if isinstance(commit_tree, Mapping) else None
    if (
        not isinstance(commit_document, Mapping)
        or commit_document.get("sha") != source_commit
        or not isinstance(tree_sha, str)
        or _COMMIT_RE.fullmatch(tree_sha) is None
    ):
        raise PreparationError("publication-authority:commit-tree")
    tree_url = f"{GITHUB_API_ROOT}/git/trees/{tree_sha}?recursive=1"
    try:
        tree_document = fetch_json(tree_url)
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:tree-fetch:{type(error).__name__}"
        ) from error
    tree_rows = tree_document.get("tree") if isinstance(tree_document, Mapping) else None
    if (
        not isinstance(tree_document, Mapping)
        or tree_document.get("sha") != tree_sha
        or tree_document.get("truncated") is not False
        or not isinstance(tree_rows, list)
        or len(tree_rows) > MAX_GITHUB_TREE_ENTRIES
    ):
        raise PreparationError("publication-authority:tree-envelope")
    selected_tree: dict[str, Mapping[str, Any]] = {}
    for row in tree_rows:
        if not isinstance(row, Mapping):
            raise PreparationError("publication-authority:tree-row")
        path = row.get("path")
        if not isinstance(path, str):
            raise PreparationError("publication-authority:tree-row")
        if path not in bindings:
            continue
        if path in selected_tree:
            raise PreparationError(f"publication-authority:duplicate-tree-path:{path}")
        selected_tree[path] = row
    if set(selected_tree) != set(bindings):
        raise PreparationError("publication-authority:tree-artifact-set")
    artifacts: list[dict[str, Any]] = []
    for path in sorted(bindings):
        binding = bindings[path]
        row = selected_tree[path]
        if not isinstance(binding, Mapping) or set(binding) != {
            "sha256",
            "bytes",
            "git_blob_oid",
        }:
            raise PreparationError(
                f"publication-authority:tree-artifact:{Path(path).name}"
            )
        blob_sha = row.get("sha")
        expected_sha256 = binding.get("sha256")
        expected_bytes = binding.get("bytes")
        expected_blob_oid = binding.get("git_blob_oid")
        if (
            row.get("path") != path
            or row.get("type") != "blob"
            or row.get("mode") != modes[path]
            or not isinstance(blob_sha, str)
            or _COMMIT_RE.fullmatch(blob_sha) is None
            or type(row.get("size")) is not int
            or row.get("size") != expected_bytes
            or not isinstance(expected_sha256, str)
            or _SHA256_RE.fullmatch(expected_sha256) is None
            or type(expected_bytes) is not int
            or expected_bytes <= 0
            or expected_bytes > MAX_GITHUB_RESPONSE_BYTES
            or not isinstance(expected_blob_oid, str)
            or _COMMIT_RE.fullmatch(expected_blob_oid) is None
        ):
            raise PreparationError(
                f"publication-authority:tree-artifact:{Path(path).name}"
            )
        if blob_sha != expected_blob_oid:
            raise PreparationError(
                f"publication-authority:tree-blob-oid:{Path(path).name}"
            )
        artifacts.append(
            {
                "path": path,
                "sha256": expected_sha256,
                "bytes": expected_bytes,
                "git_blob_oid": expected_blob_oid,
                "git_mode": modes[path],
            }
        )
    return {
        "schema": PUBLICATION_AUTHORITY_SCHEMA,
        "repository": GITHUB_REPOSITORY,
        "branch": GITHUB_BRANCH,
        "source_commit": source_commit,
        "branch_head_sha": branch_head,
        "required_checks": list(REQUIRED_GITHUB_CHECKS),
        "checks": checks,
        "artifacts": artifacts,
        "verified": True,
    }


def verify_current_authority(
    source_commit: str,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> list[dict[str, Any]]:
    """Replay exact master, workflow run, and attempt jobs after immutable-blob proof."""

    try:
        document = fetch_json(f"{GITHUB_API_ROOT}/branches/{GITHUB_BRANCH}")
        workflow_runs_document = fetch_json(
            f"{GITHUB_API_ROOT}/actions/workflows/{GITHUB_WORKFLOW_FILE}/runs?"
            f"branch={GITHUB_BRANCH}&event=push&head_sha={source_commit}&"
            f"per_page={MAX_GITHUB_WORKFLOW_RUNS}&page=1"
        )
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    commit = document.get("commit") if isinstance(document, Mapping) else None
    if (
        not isinstance(document, Mapping)
        or document.get("name") != GITHUB_BRANCH
        or not isinstance(commit, Mapping)
        or commit.get("sha") != source_commit
    ):
        raise PreparationError("publication-authority:branch-recheck")
    workflow_run = _project_exact_workflow_run(
        workflow_runs_document,
        source_commit,
        prefix="publication-authority:terminal",
    )
    try:
        jobs_document = fetch_json(
            f"{GITHUB_API_ROOT}/actions/runs/{workflow_run['id']}/attempts/"
            f"{workflow_run['run_attempt']}/jobs?per_page={MAX_GITHUB_JOBS}&page=1"
        )
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    checks = _project_exact_checks(
        jobs_document,
        source_commit,
        workflow_run,
        prefix="publication-authority:terminal",
    )
    try:
        workflow_replay_document = fetch_json(
            f"{GITHUB_API_ROOT}/actions/workflows/{GITHUB_WORKFLOW_FILE}/runs?"
            f"branch={GITHUB_BRANCH}&event=push&head_sha={source_commit}&"
            f"per_page={MAX_GITHUB_WORKFLOW_RUNS}&page=1"
        )
        branch_replay_document = fetch_json(
            f"{GITHUB_API_ROOT}/branches/{GITHUB_BRANCH}"
        )
    except PreparationError:
        raise
    except Exception as error:
        raise PreparationError(
            f"publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    if _project_exact_workflow_run(
        workflow_replay_document,
        source_commit,
        prefix="publication-authority:terminal",
    ) != workflow_run:
        raise PreparationError("publication-authority:terminal:workflow-run-replay")
    branch_replay_commit = (
        branch_replay_document.get("commit")
        if isinstance(branch_replay_document, Mapping)
        else None
    )
    if (
        not isinstance(branch_replay_document, Mapping)
        or branch_replay_document.get("name") != GITHUB_BRANCH
        or not isinstance(branch_replay_commit, Mapping)
        or branch_replay_commit.get("sha") != source_commit
    ):
        raise PreparationError("publication-authority:branch-recheck")
    return checks


def _run_command(argv: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            list(argv),
            env=_SAFE_ENVIRONMENT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PreparationError(f"command:{Path(argv[0]).name}:{type(error).__name__}") from error
    if completed.returncode != 0:
        raise PreparationError(f"command:{Path(argv[0]).name}:exit-{completed.returncode}")
    return completed.stdout


@dataclass(frozen=True)
class HostConfig:
    packet_root: Path = PACKET_ROOT
    install_root: Path = INSTALL_ROOT
    packet_manifest_name: str = PACKET_MANIFEST_NAME
    receipt_name: str = RECEIPT_NAME
    controller_name: str = CONTROLLER_NAME
    executing_controller: Path | None = None
    required_packet_files: tuple[str, ...] = REQUIRED_PACKET_FILES
    expected_packet_modes: Mapping[str, int] | None = None
    packet_repository_paths: Mapping[str, str] | None = None
    uniad_repo: Path = STACK / "UniAD"
    neuroncap_repo: Path = STACK / "NeuroNCAP"
    neurad_repo: Path = STACK / "neurad-studio"
    uniad_server_rel: str = "inference/server.py"
    compose_rel: str = "scripts/_docker_compose_release.sh"
    expected_uniad_head: str = UNIAD_HEAD
    expected_uniad_untracked: tuple[str, ...] = UNIAD_REQUIRED_UNTRACKED
    expected_neuroncap_head: str = NEURONCAP_HEAD
    expected_neurad_head: str = NEURAD_HEAD
    expected_server_sha256: str = UNIAD_SERVER_SHA256
    expected_server_bytes: int = UNIAD_SERVER_BYTES
    expected_compose_input_sha256: str = COMPOSE_INPUT_SHA256
    expected_compose_input_bytes: int = COMPOSE_INPUT_BYTES
    expected_compose_output_sha256: str = COMPOSE_OUTPUT_SHA256
    expected_compose_output_bytes: int = COMPOSE_OUTPUT_BYTES
    dataset_root: Path = DATASET_ROOT
    analytic_root: Path = ANALYTIC_ROOT
    smoke_root: Path = SMOKE_ROOT
    minimum_remote_free_bytes: int = MINIMUM_REMOTE_FREE_BYTES
    projected_output_bytes: int = PROJECTED_OUTPUT_BYTES
    minimum_reserve_bytes: int = MINIMUM_RESERVE_BYTES
    expected_mount: Mapping[str, str] | None = None
    forbidden_paths: tuple[Path, ...] | None = None
    expected_host: str = "sentinel-gpu"

    def packet_modes(self) -> Mapping[str, int]:
        return self.expected_packet_modes or EXPECTED_PACKET_MODES

    def repository_paths(self) -> Mapping[str, str]:
        return self.packet_repository_paths or PACKET_REPOSITORY_PATHS

    def mount_contract(self) -> Mapping[str, str]:
        return self.expected_mount or EXPECTED_MOUNT

    def forbidden(self) -> tuple[Path, ...]:
        return self.forbidden_paths or (
            self.install_root,
            self.analytic_root,
            self.smoke_root,
            self.uniad_repo / "i135-smoke-staging",
            self.uniad_repo / "dose_schedules.json",
            self.uniad_repo / "i135-decisions",
            Path("/var/lib/sentinel/i135-smoke.lock"),
            Path("/var/lib/sentinel/i135-analytic.lock"),
            Path("/var/log/sentinel-i135.log"),
        )


@dataclass(frozen=True)
class Hooks:
    run: Callable[[Sequence[str]], bytes] = _run_command
    fetch_json: Callable[[str], Any] = _fetch_json
    hostname: Callable[[], str] = socket.gethostname
    disk_free: Callable[[Path], int] = lambda path: shutil.disk_usage(path).free
    device: Callable[[Path], int] = lambda path: path.stat().st_dev
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)
    environment: Callable[[], Mapping[str, str]] = lambda: dict(os.environ)
    isolated: Callable[[], bool] = lambda: sys.flags.isolated == 1
    before_replace: Callable[[str, Path], None] = lambda _label, _path: None
    rename: Callable[[Path, Path], None] = os.rename


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _receipt_payload_sha256(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_payload_sha256", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _identity(row: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        row.st_dev,
        row.st_ino,
        row.st_mode,
        row.st_size,
        row.st_mtime_ns,
        row.st_ctime_ns,
    )


def stable_file(path: Path, *, collect_bytes: bool = False) -> tuple[dict[str, Any], bytes | None]:
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise PreparationError(f"file:not-physical:{path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        byte_count = 0
        chunks: list[bytes] | None = [] if collect_bytes else None
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
            if chunks is not None:
                chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if _identity(before) != _identity(after) or byte_count != before.st_size:
        raise PreparationError(f"file:unstable:{path}")
    return (
        {
            "path": str(path),
            "sha256": digest.hexdigest(),
            "bytes": byte_count,
            "mode": stat.S_IMODE(before.st_mode),
        },
        b"".join(chunks) if chunks is not None else None,
    )


def _physical_directory(path: Path, label: str) -> os.stat_result:
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
        raise PreparationError(f"{label}:not-physical:{path}")
    return path.stat(follow_symlinks=False)


def _decode_nul(payload: bytes, label: str) -> list[str]:
    if payload and not payload.endswith(b"\0"):
        raise PreparationError(f"repository:{label}:not-nul-terminated")
    try:
        rows = [row.decode("utf-8") for row in payload.rstrip(b"\0").split(b"\0") if row]
    except UnicodeDecodeError as error:
        raise PreparationError(f"repository:{label}:non-utf8") from error
    if any(path.startswith("/") or ".." in Path(path).parts for path in rows):
        raise PreparationError(f"repository:{label}:unsafe-path")
    return sorted(rows)


def _git(hooks: Hooks, repo: Path, *arguments: str) -> bytes:
    return hooks.run(
        (
            "/usr/bin/git",
            "-c",
            f"safe.directory={repo}",
            "-C",
            str(repo),
            *arguments,
        )
    )


def repository_snapshot(hooks: Hooks, repo: Path, label: str) -> dict[str, Any]:
    return {
        "path": str(repo),
        "head": _git(hooks, repo, "rev-parse", "HEAD").decode("ascii").strip(),
        "staged_paths": _decode_nul(
            _git(hooks, repo, "diff", "--cached", "--name-only", "-z"), f"{label}:staged"
        ),
        "dirty_tracked_paths": _decode_nul(
            _git(hooks, repo, "diff", "--name-only", "-z"), f"{label}:dirty"
        ),
        "untracked_paths": _decode_nul(
            _git(hooks, repo, "ls-files", "--others", "--exclude-standard", "-z"),
            f"{label}:untracked",
        ),
    }


def _validate_repository_snapshot(
    row: Mapping[str, Any],
    *,
    head: str,
    staged: list[str],
    dirty: list[str],
    untracked: list[str] | None = None,
    untracked_prefix: str | None = None,
) -> None:
    if row.get("head") != head:
        raise PreparationError(f"repository:head:{row.get('path')}")
    if row.get("staged_paths") != staged:
        raise PreparationError(f"repository:staged:{row.get('path')}")
    if row.get("dirty_tracked_paths") != dirty:
        raise PreparationError(f"repository:dirty:{row.get('path')}")
    observed = row.get("untracked_paths")
    if untracked is not None and observed != untracked:
        raise PreparationError(f"repository:untracked:{row.get('path')}")
    if untracked_prefix is not None and (
        not isinstance(observed, list)
        or any(path != untracked_prefix and not path.startswith(f"{untracked_prefix}/") for path in observed)
    ):
        raise PreparationError(f"repository:untracked:{row.get('path')}")


def validate_packet(
    config: HostConfig, supplied_manifest_sha256: str
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    if not _SHA256_RE.fullmatch(supplied_manifest_sha256):
        raise PreparationError("packet:independent-manifest-sha256")
    packet_info = _physical_directory(config.packet_root, "packet-root")
    if stat.S_IMODE(packet_info.st_mode) != 0o755:
        raise PreparationError("packet:root-mode")
    manifest_path = config.packet_root / config.packet_manifest_name
    manifest_receipt, manifest_payload = stable_file(manifest_path, collect_bytes=True)
    if (
        manifest_receipt["sha256"] != supplied_manifest_sha256
        or manifest_receipt["mode"] != 0o644
        or manifest_payload is None
    ):
        raise PreparationError("packet:manifest-sha256")
    try:
        manifest = json.loads(
            manifest_payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise PreparationError(f"packet:manifest-json:{type(error).__name__}") from error
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "source_commit", "files"}:
        raise PreparationError("packet:manifest-fields")
    if manifest.get("schema") != PACKET_SCHEMA:
        raise PreparationError("packet:manifest-schema")
    if not isinstance(manifest.get("source_commit"), str) or not _COMMIT_RE.fullmatch(
        manifest["source_commit"]
    ):
        raise PreparationError("packet:source-commit")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != set(config.required_packet_files):
        raise PreparationError("packet:file-set")
    expected_entries = {config.packet_manifest_name, *config.required_packet_files}
    if {entry.name for entry in config.packet_root.iterdir()} != expected_entries:
        raise PreparationError("packet:root-entry-set")
    observed: dict[str, dict[str, Any]] = {}
    git_blob_oids: dict[str, str] = {}
    modes = config.packet_modes()
    if set(modes) != set(config.required_packet_files):
        raise PreparationError("packet:mode-contract")
    for name in config.required_packet_files:
        claimed = files.get(name)
        if not isinstance(claimed, dict) or set(claimed) != {"sha256", "bytes", "mode"}:
            raise PreparationError(f"packet:file-receipt:{name}")
        row, payload = stable_file(config.packet_root / name, collect_bytes=True)
        if (
            payload is None
            or len(payload) != row["bytes"]
            or claimed.get("sha256") != row["sha256"]
            or claimed.get("bytes") != row["bytes"]
            or claimed.get("mode") != row["mode"]
            or row["mode"] != modes[name]
        ):
            raise PreparationError(f"packet:file-drift:{name}")
        observed[name] = row
        git_blob_oids[name] = _git_blob_oid(payload)
    controller = observed.get(config.controller_name)
    executing = Path(config.executing_controller or __file__).absolute()
    if controller is None or executing != config.packet_root / config.controller_name:
        raise PreparationError("packet:controller-path")
    executing_row, _payload = stable_file(executing)
    if executing_row != controller:
        raise PreparationError("packet:controller-binding")
    return (
        {
            "schema": PACKET_SCHEMA,
            "source_commit": manifest["source_commit"],
            "manifest": manifest_receipt,
            "independently_supplied_manifest_sha256": supplied_manifest_sha256,
            "files": observed,
        },
        observed,
        git_blob_oids,
    )


def revalidate_packet_payloads(
    config: HostConfig,
    root: Path,
    expected_files: Mapping[str, Mapping[str, Any]],
    expected_manifest_sha256: str,
    *,
    label: str,
) -> None:
    """Replay every staged byte and mode at a mutation boundary."""

    _physical_directory(root, f"packet-revalidation:{label}:root")
    expected_entries = {config.packet_manifest_name, *config.required_packet_files}
    if {entry.name for entry in root.iterdir()} != expected_entries:
        raise PreparationError(f"packet:revalidation:{label}:entry-set")
    modes = config.packet_modes()
    if set(expected_files) != set(config.required_packet_files) or set(modes) != set(
        config.required_packet_files
    ):
        raise PreparationError(f"packet:revalidation:{label}:contract")
    for name in config.required_packet_files:
        row, _payload = stable_file(root / name)
        expected = expected_files[name]
        if (
            row["sha256"] != expected.get("sha256")
            or row["bytes"] != expected.get("bytes")
            or row["mode"] != expected.get("mode")
            or row["mode"] != modes[name]
        ):
            raise PreparationError(f"packet:revalidation:{label}:{name}")
    manifest, _payload = stable_file(root / config.packet_manifest_name)
    if (
        manifest["sha256"] != expected_manifest_sha256
        or manifest["mode"] != 0o644
    ):
        raise PreparationError(f"packet:revalidation:{label}:manifest")


def _atomic_replace(
    path: Path,
    payload: bytes,
    expected_before: Mapping[str, Any],
    *,
    label: str,
    hooks: Hooks,
) -> dict[str, Any]:
    parent = path.parent
    _physical_directory(parent, f"{label}:parent")
    descriptor, temporary_text = tempfile.mkstemp(dir=parent, prefix=f".{path.name}.i135-", suffix=".tmp")
    temporary = Path(temporary_text)
    replaced = False
    try:
        os.fchmod(descriptor, int(expected_before["mode"]))
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        hooks.before_replace(label, path)
        current, _current_payload = stable_file(path)
        if current != expected_before:
            raise PreparationError(f"{label}:preimage-race")
        os.replace(temporary, path)
        replaced = True
        parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        # A failed temporary is evidence.  It is intentionally not deleted.
        if replaced and temporary.exists():
            raise PreparationError(f"{label}:temporary-survived")
    row, _data = stable_file(path)
    return row


def _load_patcher(path: Path, expected_receipt: Mapping[str, Any]) -> Any:
    row, payload = stable_file(path, collect_bytes=True)
    if row != expected_receipt or payload is None:
        raise PreparationError("compose:patcher-binding")
    namespace: dict[str, Any] = {"__file__": str(path), "__name__": "iter135_host_patcher"}
    try:
        exec(compile(payload, str(path), "exec"), namespace)
    except Exception as error:
        raise PreparationError(f"compose:patcher-load:{type(error).__name__}") from error
    return namespace


def _mount_snapshot(config: HostConfig, hooks: Hooks) -> dict[str, Any]:
    root_info = _physical_directory(config.dataset_root, "dataset-root")
    try:
        raw = json.loads(
            hooks.run(
                (
                    "/usr/bin/findmnt",
                    "--json",
                    "--output",
                    "TARGET,SOURCE,FSTYPE,UUID",
                    "--target",
                    str(config.dataset_root),
                )
            )
        )
    except json.JSONDecodeError as error:
        raise PreparationError("storage:findmnt-json") from error
    rows = raw.get("filesystems") if isinstance(raw, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise PreparationError("storage:findmnt-schema")
    observed = {
        "mount_target": rows[0].get("target"),
        "mount_source": rows[0].get("source"),
        "mount_fstype": rows[0].get("fstype"),
        "mount_uuid": rows[0].get("uuid"),
    }
    if observed != dict(config.mount_contract()):
        raise PreparationError("storage:mount-identity")
    dataset_device = hooks.device(config.dataset_root)
    root_device = hooks.device(Path("/"))
    if dataset_device != root_info.st_dev or dataset_device == root_device:
        raise PreparationError("storage:device-identity")
    free = hooks.disk_free(config.dataset_root)
    if type(free) is not int or free < config.minimum_remote_free_bytes:
        raise PreparationError("storage:minimum-free")
    if free - config.projected_output_bytes < config.minimum_reserve_bytes:
        raise PreparationError("storage:projected-reserve")
    return {
        **observed,
        "dataset_st_dev": dataset_device,
        "root_st_dev": root_device,
        "free_bytes_before": free,
        "minimum_remote_free_bytes": config.minimum_remote_free_bytes,
        "projected_output_bytes": config.projected_output_bytes,
        "minimum_reserve_bytes": config.minimum_reserve_bytes,
    }


def _atomic_create_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    parent = path.parent
    _physical_directory(parent, "receipt-parent")
    if path.exists() or path.is_symlink():
        raise PreparationError("receipt:already-exists")
    payload = (json.dumps(receipt, indent=1, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o444,
    )
    try:
        os.fchmod(descriptor, 0o444)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_receipt(started: str, host: str, supplied_sha256: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "verdict": INCOMPLETE_VERDICT,
        "started_at_utc": started,
        "finished_at_utc": started,
        "host": host,
        "problem_count": 0,
        "problems": [],
        "publication_authority": None,
        "packet_manifest_sha256": supplied_sha256,
        "packet": None,
        "controller": None,
        "repositories": None,
        "compose": None,
        "storage": None,
        "forbidden_paths": None,
        "actions": [],
        "invocation": None,
        "receipt_payload_sha256": None,
    }


def _forbidden_state(config: HostConfig) -> dict[str, bool]:
    return {str(path): os.path.lexists(path) for path in config.forbidden()}


def prepare_host(
    supplied_manifest_sha256: str,
    *,
    config: HostConfig = HostConfig(),
    hooks: Hooks = Hooks(),
) -> tuple[dict[str, Any], Path]:
    started = _timestamp(hooks.now())
    host = hooks.hostname()
    receipt = _base_receipt(started, host, supplied_manifest_sha256)
    installed = False
    try:
        observed_environment = hooks.environment()
        environment_matches = (
            isinstance(observed_environment, Mapping)
            and dict(observed_environment) == _SAFE_ENVIRONMENT
        )
        isolated = hooks.isolated()
        receipt["invocation"] = {
            "environment": dict(_SAFE_ENVIRONMENT),
            "environment_matches": environment_matches,
            "isolated": isolated,
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
        }
        if not environment_matches:
            raise PreparationError("invocation:environment")
        if isolated is not True:
            raise PreparationError("invocation:not-isolated")
        if platform.python_implementation() != "CPython" or sys.version_info < (3, 10):
            raise PreparationError("invocation:interpreter")
        if host != config.expected_host:
            raise PreparationError("host:identity")
        forbidden_state = _forbidden_state(config)
        receipt["forbidden_paths"] = forbidden_state
        if any(forbidden_state.values()):
            raise PreparationError("host:forbidden-path-present")

        packet, packet_files, packet_git_blob_oids = validate_packet(
            config, supplied_manifest_sha256
        )
        receipt["packet"] = packet
        receipt["controller"] = packet_files[config.controller_name]
        repository_paths = dict(config.repository_paths())
        packet_modes = dict(config.packet_modes())
        if (
            set(repository_paths) != set(config.required_packet_files)
            or len(set(repository_paths.values())) != len(repository_paths)
            or set(packet_modes) != set(config.required_packet_files)
            or any(mode not in {0o644, 0o755} for mode in packet_modes.values())
        ):
            raise PreparationError("packet:repository-path-contract")
        artifact_bindings = {
            repository_paths[name]: {
                "sha256": packet_files[name]["sha256"],
                "bytes": packet_files[name]["bytes"],
                "git_blob_oid": packet_git_blob_oids[name],
            }
            for name in config.required_packet_files
        }
        expected_git_modes = {
            repository_paths[name]: (
                "100755" if packet_modes[name] == 0o755 else "100644"
            )
            for name in config.required_packet_files
        }
        receipt["publication_authority"] = verify_publication_authority(
            packet["source_commit"],
            hooks.fetch_json,
            artifact_bindings=artifact_bindings,
            expected_git_modes=expected_git_modes,
        )

        before_repositories = {
            "uniad": repository_snapshot(hooks, config.uniad_repo, "uniad"),
            "neuroncap": repository_snapshot(hooks, config.neuroncap_repo, "neuroncap"),
            "neurad": repository_snapshot(hooks, config.neurad_repo, "neurad"),
        }
        allowed_uniad_dirty = [
            "inference/server.py",
            "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
        ]
        if before_repositories["uniad"]["dirty_tracked_paths"] not in (
            allowed_uniad_dirty,
            allowed_uniad_dirty[1:],
        ):
            raise PreparationError("repository:uniad:preparation-dirty-set")
        _validate_repository_snapshot(
            before_repositories["uniad"],
            head=config.expected_uniad_head,
            staged=[],
            dirty=before_repositories["uniad"]["dirty_tracked_paths"],
            untracked=list(config.expected_uniad_untracked),
        )
        _validate_repository_snapshot(
            before_repositories["neuroncap"],
            head=config.expected_neuroncap_head,
            staged=[],
            dirty=["docker/Dockerfile", config.compose_rel],
            untracked_prefix="outoutput",
        )
        _validate_repository_snapshot(
            before_repositories["neurad"],
            head=config.expected_neurad_head,
            staged=[],
            dirty=["Dockerfile"],
            untracked=["Dockerfile.bak"],
        )

        # Finish every read-only host gate before changing a tracked byte.
        storage = _mount_snapshot(config, hooks)
        if _forbidden_state(config) != forbidden_state:
            raise PreparationError("host:forbidden-path-race")

        head_server = _git(
            hooks, config.uniad_repo, "show", f"HEAD:{config.uniad_server_rel}"
        )
        if (
            hashlib.sha256(head_server).hexdigest() != config.expected_server_sha256
            or len(head_server) != config.expected_server_bytes
        ):
            raise PreparationError("server:head-blob")
        server_path = config.uniad_repo / config.uniad_server_rel
        server_before, _server_payload = stable_file(server_path)
        server_replaced = server_before["sha256"] != config.expected_server_sha256
        revalidate_packet_payloads(
            config,
            config.packet_root,
            packet_files,
            supplied_manifest_sha256,
            label="pre-mutation",
        )
        if server_replaced:
            if config.uniad_server_rel not in before_repositories["uniad"]["dirty_tracked_paths"]:
                raise PreparationError("server:untracked-preimage")
            receipt["publication_authority"]["checks"] = verify_current_authority(
                packet["source_commit"],
                hooks.fetch_json,
            )
            server_after = _atomic_replace(
                server_path, head_server, server_before, label="server", hooks=hooks
            )
        else:
            server_after = server_before
        if (
            server_after["sha256"] != config.expected_server_sha256
            or server_after["bytes"] != config.expected_server_bytes
        ):
            raise PreparationError("server:normalized-drift")
        receipt["actions"].append(
            {
                "action": "normalize_uniad_server_from_verified_head_blob",
                "performed": server_replaced,
                "before": server_before,
                "after": server_after,
            }
        )

        compose_path = config.neuroncap_repo / config.compose_rel
        compose_before, compose_payload = stable_file(compose_path, collect_bytes=True)
        if (
            compose_payload is None
            or compose_before["sha256"] != config.expected_compose_input_sha256
            or compose_before["bytes"] != config.expected_compose_input_bytes
        ):
            raise PreparationError("compose:preimage")
        patcher = _load_patcher(
            config.packet_root / "patch_compose_dose_env.py",
            packet_files["patch_compose_dose_env.py"],
        )
        if (
            patcher.get("EXPECTED_INPUT_SHA256") != config.expected_compose_input_sha256
            or patcher.get("EXPECTED_OUTPUT_SHA256") != config.expected_compose_output_sha256
            or not callable(patcher.get("patch_text"))
        ):
            raise PreparationError("compose:patcher-contract")
        try:
            patched = patcher["patch_text"](compose_payload.decode("utf-8")).encode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise PreparationError(f"compose:patch:{type(error).__name__}") from error
        if (
            hashlib.sha256(patched).hexdigest() != config.expected_compose_output_sha256
            or len(patched) != config.expected_compose_output_bytes
        ):
            raise PreparationError("compose:output")
        if not server_replaced:
            receipt["publication_authority"]["checks"] = verify_current_authority(
                packet["source_commit"],
                hooks.fetch_json,
            )
        compose_after = _atomic_replace(
            compose_path, patched, compose_before, label="compose", hooks=hooks
        )
        receipt["compose"] = {
            "patcher": packet_files["patch_compose_dose_env.py"],
            "before": compose_before,
            "after": compose_after,
        }
        receipt["actions"].append(
            {
                "action": "atomically_patch_compose_from_exact_preimage",
                "performed": True,
                "before_sha256": compose_before["sha256"],
                "after_sha256": compose_after["sha256"],
            }
        )

        after_repositories = {
            "uniad": repository_snapshot(hooks, config.uniad_repo, "uniad"),
            "neuroncap": repository_snapshot(hooks, config.neuroncap_repo, "neuroncap"),
            "neurad": repository_snapshot(hooks, config.neurad_repo, "neurad"),
        }
        _validate_repository_snapshot(
            after_repositories["uniad"],
            head=config.expected_uniad_head,
            staged=[],
            dirty=["projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"],
            untracked=list(config.expected_uniad_untracked),
        )
        _validate_repository_snapshot(
            after_repositories["neuroncap"],
            head=config.expected_neuroncap_head,
            staged=[],
            dirty=["docker/Dockerfile", config.compose_rel],
            untracked_prefix="outoutput",
        )
        _validate_repository_snapshot(
            after_repositories["neurad"],
            head=config.expected_neurad_head,
            staged=[],
            dirty=["Dockerfile"],
            untracked=["Dockerfile.bak"],
        )
        receipt["repositories"] = {
            "before": before_repositories,
            "after": after_repositories,
        }

        os.mkdir(config.analytic_root, 0o755)
        output_info = _physical_directory(config.analytic_root, "analytic-root")
        if output_info.st_dev != storage["dataset_st_dev"] or any(config.analytic_root.iterdir()):
            raise PreparationError("storage:analytic-root")
        storage_after = _mount_snapshot(config, hooks)
        stable_storage_fields = {
            "mount_target",
            "mount_source",
            "mount_fstype",
            "mount_uuid",
            "dataset_st_dev",
            "root_st_dev",
            "minimum_remote_free_bytes",
            "projected_output_bytes",
            "minimum_reserve_bytes",
        }
        if any(storage_after[field] != storage[field] for field in stable_storage_fields):
            raise PreparationError("storage:identity-race")
        storage.update(
            {
                "analytic_root": str(config.analytic_root),
                "analytic_root_realpath": str(config.analytic_root.resolve(strict=True)),
                "analytic_root_is_symlink": False,
                "analytic_root_empty": True,
                "analytic_root_st_dev": output_info.st_dev,
                "free_bytes_after": storage_after["free_bytes_before"],
            }
        )
        receipt["storage"] = storage
        receipt["actions"].append(
            {
                "action": "create_absent_empty_analytic_root",
                "performed": True,
                "path": str(config.analytic_root),
            }
        )

        if os.path.lexists(config.install_root):
            raise PreparationError("packet:install-root-race")
        post_creation_forbidden = _forbidden_state(config)
        expected_post_creation = dict(forbidden_state)
        expected_post_creation[str(config.analytic_root)] = True
        if post_creation_forbidden != expected_post_creation:
            raise PreparationError("host:forbidden-path-race")
        if config.packet_root.stat().st_dev != config.install_root.parent.stat().st_dev:
            raise PreparationError("packet:cross-device-install")
        revalidate_packet_payloads(
            config,
            config.packet_root,
            packet_files,
            supplied_manifest_sha256,
            label="pre-install",
        )
        hooks.rename(config.packet_root, config.install_root)
        installed = True
        _physical_directory(config.install_root, "install-root")
        receipt["actions"].append(
            {
                "action": "atomically_install_verified_packet",
                "performed": True,
                "from": str(config.packet_root),
                "to": str(config.install_root),
            }
        )
        revalidate_packet_payloads(
            config,
            config.install_root,
            packet_files,
            supplied_manifest_sha256,
            label="post-install",
        )
        receipt["publication_authority"]["checks"] = verify_current_authority(
            packet["source_commit"],
            hooks.fetch_json,
        )
        receipt["verdict"] = READY_VERDICT
    except Exception as error:  # every preparation fault must publish a durable red attempt
        code = str(error) if isinstance(error, PreparationError) else f"internal:{type(error).__name__}"
        receipt["problems"] = [code]
        receipt["problem_count"] = 1
        receipt["verdict"] = INCOMPLETE_VERDICT

    receipt["finished_at_utc"] = _timestamp(hooks.now())
    receipt["receipt_payload_sha256"] = _receipt_payload_sha256(receipt)
    output_root = config.install_root if installed else config.packet_root
    output_path = output_root / config.receipt_name
    _atomic_create_receipt(output_path, receipt)
    return receipt, output_path


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None and (dict(os.environ) != _SAFE_ENVIRONMENT or sys.flags.isolated != 1):
        script = Path(__file__).absolute()
        try:
            interpreter = Path(sys.executable).resolve(strict=True)
        except (OSError, RuntimeError):
            print("I135_HOST_PREPARATION_FAIL invocation:physical-interpreter", file=sys.stderr)
            return 2
        if script != PACKET_ROOT / CONTROLLER_NAME or script.is_symlink():
            print("I135_HOST_PREPARATION_FAIL invocation:canonical-controller", file=sys.stderr)
            return 2
        os.execve(
            interpreter,
            [str(interpreter), "-I", str(script), *sys.argv[1:]],
            _SAFE_ENVIRONMENT,
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-manifest-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        receipt, output = prepare_host(args.packet_manifest_sha256)
    except PreparationError as error:
        print(f"I135_HOST_PREPARATION_FAIL {error}", file=sys.stderr)
        return 2
    print(
        f"{receipt['verdict']} problems={receipt['problem_count']} output={output}",
        file=sys.stderr,
    )
    return 0 if receipt["problem_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
