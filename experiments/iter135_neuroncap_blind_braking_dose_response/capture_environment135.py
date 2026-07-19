#!/usr/bin/env python3
"""Capture the fail-closed Iteration-135 execution-host environment receipt.

This command is read-only except for one exclusive creation of the canonical
``env_receipts.json``.  It preserves every existing attempt and never accepts an alternate output
root.  It does not prepare the host: it never creates the output root, resets Git, patches compose,
removes containers, starts Docker, or touches the GPU.  Run it only after the source-bound green
host-preparation receipt has been independently replayed.

The write-ahead marker preserves nonauthority while publication is incomplete.  A successful disk
commit retains canonical and pending names as one read-only two-link inode, durably removes the
marker, and returns a process-local completion witness after a coupled replay.  Filesystem state
cannot prove that the process returned, and physical I/O failure can still prevent bytes or
durability; absence of an artifact is never evidence that no attempt began.

The local-free value is deliberately an operator-supplied integer.  The execution host cannot
measure the evidence-collection filesystem on the operator's Mac, and this tool will not pretend it
can.
"""

from __future__ import annotations

import argparse
import ast
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
import types
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CANONICAL_MANIFEST_PATH = HERE / "make_launch_manifest.py"
CANONICAL_PATCHER_PATH = HERE / "patch_compose_dose_env.py"
CANONICAL_PREPARER_PATH = HERE / "prepare_host135.py"
CANONICAL_PACKET_MANIFEST_PATH = HERE / "host_packet_manifest.json"
CANONICAL_PREPARATION_RECEIPT_PATH = HERE / "host_preparation_receipt.json"
DEFAULT_OUTPUT = HERE / "env_receipts.json"
CANONICAL_RECEIPT_BASENAME = "env_receipts.json"
ATTEMPT_MARKER_BASENAME = (
    ".env_receipts.json.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE"
)
PENDING_RECEIPT_BASENAME = (
    ".env_receipts.json.PENDING_RECEIPT_NONAUTHORITATIVE"
)
INCOMPLETE_VERDICT = "I135_ENVIRONMENT_PREFLIGHT_INCOMPLETE"
EXPECTED_ENVIRONMENT_SCHEMA = "iter135.environment_receipts.v3"
EXPECTED_PREPARATION_SCHEMA = "iter135.host_preparation_receipt.v1"
EXPECTED_PREPARATION_VERDICT = "I135_HOST_PREPARATION_OK"
EXPECTED_PACKET_SCHEMA = "iter135.host_packet_manifest.v1"
PUBLICATION_AUTHORITY_SCHEMA = "iter135.github_publication_authority.v1"
EXPECTED_PACKET_STAGING_ROOT = Path("/opt/sentinel-stack/.iter135-packet")
EXPECTED_DATASET_ROOT = Path("/datasets/nuscenes-full")
EXPECTED_SMOKE_ROOT = EXPECTED_DATASET_ROOT / "sentinel-i135-smoke-evidence"
EXPECTED_UNIAD_ROOT = Path("/opt/sentinel-stack/UniAD")
EXPECTED_NEURONCAP_ROOT = Path("/opt/sentinel-stack/NeuroNCAP")
EXPECTED_NEURAD_ROOT = Path("/opt/sentinel-stack/neurad-studio")
EXPECTED_H_ATTEMPT_BASENAME = (
    "host_preparation_receipt.json.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE"
)
EXPECTED_H_PENDING_BASENAME = (
    "host_preparation_receipt.json.PENDING_RECEIPT_NONAUTHORITATIVE"
)
EXPECTED_UNIAD_HEAD = "4827b8be0823e90862caa75d9d146b2ae800b72f"
EXPECTED_NEURONCAP_HEAD = "ecdcf284e2b7b83c537f3292a06c0adddff55811"
EXPECTED_NEURAD_HEAD = "b25f717b23d85c865d469bf52a0bd03b244014be"
EXPECTED_UNIAD_SERVER_SHA256 = (
    "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424"
)
EXPECTED_UNIAD_SERVER_BYTES = 4_519
EXPECTED_COMPOSE_INPUT_SHA256 = (
    "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
)
EXPECTED_COMPOSE_INPUT_BYTES = 3_380
EXPECTED_COMPOSE_OUTPUT_SHA256 = (
    "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
)
EXPECTED_COMPOSE_OUTPUT_BYTES = 3_613
EXPECTED_H_MOUNT = {
    "mount_target": str(EXPECTED_DATASET_ROOT),
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}
EXPECTED_H_MINIMUM_REMOTE_FREE_BYTES = 100 * 1024**3
EXPECTED_H_PROJECTED_OUTPUT_BYTES = 72_380_432_384
EXPECTED_H_MINIMUM_RESERVE_BYTES = 25 * 1024**3
MISSION_STATE_SCHEMA = "sentinel.mission_state.v1"
EXECUTION_PHASE = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
PREREGISTERED_PHASE = "PREREGISTERED_TOOLING_REQUIRED"
CONTROL_HARDENING_PHASE = "CONTROL_HARDENING_REQUIRED"
EXPECTED_MISSION_STATE_FIELDS = frozenset(
    {
        "schema",
        "canonical_repository",
        "workspace_boundary",
        "trunk",
        "current_completed_iteration",
        "current_result",
        "current_verdict",
        "run_state",
        "active_hypothesis",
        "next_program",
        "claim_state",
        "deprecated_pending_hypotheses",
        "paper_state",
        "storage_gate",
    }
)
EXPECTED_NEXT_PROGRAM_FIELDS = frozenset(
    {"iteration", "name", "phase", "authorized_actions", "forbidden_actions"}
)
EXPECTED_MISSION_STATE_COMMON = {
    "schema": MISSION_STATE_SCHEMA,
    "canonical_repository": "/Users/danielwahnich/workspace/sentinel",
    "workspace_boundary": {
        "isolated_from": "/Users/danielwahnich/workspace/aweb",
        "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
        "cross_workspace_access_requires_explicit_operator_request": True,
    },
    "trunk": "master",
    "current_completed_iteration": 134,
    "current_result": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
    ),
    "current_verdict": "PLACEBO_HARM_OR_NULL",
    "active_hypothesis": (
        "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
    ),
    "claim_state": {
        "neuroncap_union_gain": "ESTABLISHED_ON_NEURONCAP",
        "semantic_attribution": "UNRESOLVED",
        "hugsim_transfer": "TRANSFER_NULL",
        "production_readiness": "NOT_ESTABLISHED",
    },
    "deprecated_pending_hypotheses": [
        "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md"
    ],
    "paper_state": {
        "status": "ARCHIVED_NOT_SUBMISSION_READY",
        "next_route": "peer-reviewed venue after a full evidence rewrite",
        "blocking_omissions": [
            "HUGSIM transfer null",
            "iteration-134 placebo result",
            "resolved wording for the decoder universal-negative overclaim",
        ],
    },
    "storage_gate": {
        "minimum_local_free_gib_before_new_proof_collection": 15,
        "remote_execution_filesystem_path": "/datasets/nuscenes-full",
        "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
        "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
        "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
        "policy": (
            "preserve committed proof and hashes; delete only hash-verified duplicates, "
            "reproducible renders, and caches"
        ),
    },
}
PREREGISTERED_AUTHORIZED_ACTIONS = (
    "perform only offline, repository-local, preregistered architecture, lifecycle, "
    "terminal-proof, CI, supply-chain, test, and publication-control work",
    "retain and review evidence for the later control-hardening publication without changing "
    "external governance settings",
)
PREREGISTERED_FORBIDDEN_ACTIONS = (
    "de-prepare, rebuild, normalize, clean, install, write, delete, or otherwise mutate any "
    "iteration-135 remote host, remote filesystem, host-side repository, packet, runtime, lock, "
    "container, GPU, or evidence path before lifecycle and hermetic CI controls are separately "
    "accepted",
    "create, execute, publish, or advance any H, E, P, or S descendant; launch activation; live "
    "smoke; or analytic episode before lifecycle and hermetic CI controls are separately accepted",
    "infer IDLE, termination, completion, readiness, approval, or authority from static state, "
    "absent containers, absent processes, missing reviewers, timeouts, retry exhaustion, or "
    "incomplete proof",
    "run analyzers or publish iteration-135 data, results, claims, figures, paper text, or "
    "scientific conclusions",
    "change branch protection, rulesets, Actions policy, repository visibility, credentials, "
    "secrets, access control, or other external governance settings without explicit operator "
    "authorization",
    "rerun iteration 134",
    "adopt run-index resampling as the iteration-135 primary after observing iteration-134 results",
)
CONTROL_HARDENING_AUTHORIZED_ACTIONS = (
    "implement and validate only offline, preregistered, source-bound lifecycle observation, "
    "terminal-proof, partial-proof, inconsistency, and fail-closed recovery controls",
    "implement and validate separately reviewable hermetic CI, supply-chain, and "
    "publication-evidence controls without changing external governance settings",
)
CONTROL_HARDENING_FORBIDDEN_ACTIONS = (
    "de-prepare, rebuild, normalize, clean, install, write, delete, mutate, inventory, or access "
    "any iteration-135 remote host, remote filesystem, host-side repository, packet, runtime, "
    "lock, container, GPU, credential, or external provider in a way that could create H, E, P, "
    "or S",
    "create, execute, publish, or advance any H, E, P, or S descendant; launch activation; live "
    "smoke; or analytic episode",
    "infer IDLE, termination, completion, readiness, approval, or authority from static state, "
    "absent containers, absent processes, missing reviewers, timeouts, retry exhaustion, or "
    "incomplete proof",
    "run analyzers or publish iteration-135 data, results, claims, figures, paper text, or "
    "scientific conclusions",
    "change branch protection, rulesets, Actions policy, repository visibility, credentials, "
    "secrets, access control, or other external governance settings without explicit operator "
    "authorization",
    "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after "
    "evidence",
)
TOOLING_FROZEN_AUTHORIZED_ACTIONS = (
    "prepare the exact hash-bound sentinel-gpu host contract and atomically commit "
    "host_packet_manifest.json and host_preparation_receipt.json",
    "capture and commit the read-only iteration-135 environment receipt on sentinel-gpu",
    "generate and commit only the hash-addressed incomplete pre-smoke manifest; no analytic "
    "episodes",
    "run exactly the hash-bound four-run nonanalytic G5 smoke after the incomplete pre-smoke "
    "manifest is committed",
    "validate, collect, and commit the exact nonanalytic smoke raw evidence, recomputed receipt, "
    "and mechanically generated SMOKE.md",
)
TOOLING_FROZEN_FORBIDDEN_ACTIONS = (
    "run any iteration-135 analytic episode before smoke evidence and the final launch manifest "
    "are committed green",
    "remove or bypass the permanent analytic launch lock",
    "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after "
    "evidence",
    "place any iteration-135 analytic output on the remote root filesystem",
)
MISSION_PHASE_CONTRACTS = {
    PREREGISTERED_PHASE: {
        "run_state": "UNKNOWN",
        "authorized_actions": PREREGISTERED_AUTHORIZED_ACTIONS,
        "forbidden_actions": PREREGISTERED_FORBIDDEN_ACTIONS,
    },
    CONTROL_HARDENING_PHASE: {
        "run_state": "UNKNOWN",
        "authorized_actions": CONTROL_HARDENING_AUTHORIZED_ACTIONS,
        "forbidden_actions": CONTROL_HARDENING_FORBIDDEN_ACTIONS,
    },
    EXECUTION_PHASE: {
        "run_state": "IDLE",
        "authorized_actions": TOOLING_FROZEN_AUTHORIZED_ACTIONS,
        "forbidden_actions": TOOLING_FROZEN_FORBIDDEN_ACTIONS,
    },
}
DOCKER_RUNTIME_SCHEMA = "iter135.docker_runtime_receipt.v1"
EXPECTED_INSTALL_ROOT = "/opt/sentinel-stack/iter135"
EXPECTED_ANALYTIC_ROOT = "/datasets/nuscenes-full/sentinel-i135-outoutput"
EXPECTED_PREPARATION_PACKET_FILES = {
    "MISSION_STATE.json",
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
    "tooling_verification_receipt.json",
    "prepare_host135.py",
}
EXPECTED_PREPARATION_EXECUTABLE_FILES = {
    "capture_environment135.py",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "prepare_host135.py",
}
EXPECTED_PREPARATION_PACKET_MODES = {
    name: (
        0o755
        if name in EXPECTED_PREPARATION_EXECUTABLE_FILES
        else 0o644
    )
    for name in EXPECTED_PREPARATION_PACKET_FILES
}
EXPERIMENT_REPOSITORY_ROOT = "experiments/iter135_neuroncap_blind_braking_dose_response"
HOST_PUBLICATION_ARTIFACT_PATHS = (
    f"{EXPERIMENT_REPOSITORY_ROOT}/host_packet_manifest.json",
    f"{EXPERIMENT_REPOSITORY_ROOT}/host_preparation_receipt.json",
)

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
# The committed host-preparation receipt is a multi-megabyte JSON document, far above the
# one-mebibyte JSON-envelope inline limit of the Contents API; its byte-exact replay uses the
# raw media type on the same endpoint under this dedicated hard bound.
MAX_ARTIFACT_RESPONSE_BYTES = 32 << 20
MAX_GITHUB_WORKFLOW_RUNS = 100
MAX_GITHUB_JOBS = 100
MAX_GITHUB_TREE_RESPONSE_BYTES = 16 << 20
MAX_GITHUB_TREE_ENTRIES = 20_000
DOCKER_ARCHITECTURE_ALIASES = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def _packet_repository_path(name: str) -> str:
    return name if name == "MISSION_STATE.json" else f"{EXPERIMENT_REPOSITORY_ROOT}/{name}"

EXPECTED_HOST = "sentinel-gpu"
EXPECTED_GPU_MODEL = "NVIDIA L4"
EXPECTED_GPU_UUID = "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07"
EXPECTED_GPU_DRIVER = "580.159.03"
EXPECTED_GPU_MEMORY_MIB = 23_034
EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256 = (
    "f61363c91fa6e0f3db24a6df2e32afc16ad02ebc44e3c4af66132fcc317760c2"
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REPO_DIGEST_RE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
_GPU_UUID_RE = re.compile(r"^GPU-[0-9a-f-]+$", re.IGNORECASE)
_DRIVER_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")
_PYTHON_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_EVALUATOR_RE = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|"
    r"/(?:NeuroNCAP|neuro-ncap|neuro_ncap)/(?:main\.py|neuro_ncap/)|"
    r"/UniAD/inference/server\.py|nerfstudio/scripts/closed_loop/main\.py)",
    re.IGNORECASE,
)

SANITIZED_ENVIRONMENT = {
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
    "SENTINEL_I135_CAPTURE_SANITIZED": "1",
    "TZ": "UTC",
}
PREPARATION_SANITIZED_ENVIRONMENT = {
    key: value
    for key, value in SANITIZED_ENVIRONMENT.items()
    if key != "SENTINEL_I135_CAPTURE_SANITIZED"
}
PREPARATION_SANITIZED_ENVIRONMENT["SENTINEL_I135_PREPARE_SANITIZED"] = "1"


class CaptureError(RuntimeError):
    """A bounded probe could not produce trustworthy evidence."""


class EnvironmentAdmissionStop(CaptureError):
    """The prerequisites for beginning an environment-capture attempt were absent."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        raise CaptureError("host-publication-authority:redirect")


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-key")
        result[key] = value
    return result


def _reject_nonfinite_json(_value: str) -> None:
    raise ValueError("non-finite-number")


def _exact_json_value(observed: object, expected: object) -> bool:
    """Compare JSON values without accepting bool/int, int/float, or subclass equivalence."""

    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        observed_dict = observed
        expected_dict = expected
        return set(observed_dict) == set(expected_dict) and all(
            _exact_json_value(observed_dict[key], expected_dict[key])
            for key in expected_dict
        )
    if type(expected) is list:
        observed_list = observed
        expected_list = expected
        return len(observed_list) == len(expected_list) and all(
            _exact_json_value(observed_item, expected_item)
            for observed_item, expected_item in zip(
                observed_list, expected_list, strict=True
            )
        )
    return observed == expected


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
        raise CaptureError("host-publication-authority:url")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "sentinel-iter135-environment-authority/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
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
                raise CaptureError("host-publication-authority:redirect")
            if response.status != 200:
                raise CaptureError("host-publication-authority:http-status")
            content_type = response.headers.get_content_type()
            if content_type not in {"application/json", "application/vnd.github+json"}:
                raise CaptureError("host-publication-authority:content-type")
            if "/git/trees/" in parsed.path:
                response_limit = MAX_GITHUB_TREE_RESPONSE_BYTES
            elif "/actions/workflows/" in parsed.path and parsed.path.endswith("/runs"):
                response_limit = MAX_GITHUB_WORKFLOW_RESPONSE_BYTES
            else:
                response_limit = MAX_GITHUB_RESPONSE_BYTES
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    declared_bytes = int(declared, 10)
                except ValueError as error:
                    raise CaptureError("host-publication-authority:content-length") from error
                if declared_bytes < 0 or declared_bytes > response_limit:
                    raise CaptureError("host-publication-authority:content-length")
            payload = response.read(response_limit + 1)
    except CaptureError:
        raise
    except (OSError, TimeoutError, urllib.error.URLError) as error:
        raise CaptureError(
            f"host-publication-authority:transport:{type(error).__name__}"
        ) from error
    if len(payload) > response_limit:
        raise CaptureError("host-publication-authority:response-size")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise CaptureError("host-publication-authority:json") from error


def _fetch_raw(url: str) -> bytes:
    """Fetch one bounded raw-media GitHub Contents payload over authenticated-server TLS.

    Same endpoint and GET budget as the JSON-envelope fetch; the raw media type is the only way
    the Contents API returns the exact bytes of a blob above its one-mebibyte inline limit.
    """

    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise CaptureError("host-publication-authority:url")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.raw+json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "sentinel-iter135-environment-authority/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context),
        _NoRedirect(),
    )
    try:
        with opener.open(request, timeout=60) as response:
            if response.geturl() != url:
                raise CaptureError("host-publication-authority:redirect")
            if response.status != 200:
                raise CaptureError("host-publication-authority:http-status")
            content_type = response.headers.get_content_type()
            if content_type != "application/vnd.github.raw+json":
                raise CaptureError("host-publication-authority:content-type")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    declared_bytes = int(declared, 10)
                except ValueError as error:
                    raise CaptureError("host-publication-authority:content-length") from error
                if declared_bytes < 0 or declared_bytes > MAX_ARTIFACT_RESPONSE_BYTES:
                    raise CaptureError("host-publication-authority:content-length")
            payload = response.read(MAX_ARTIFACT_RESPONSE_BYTES + 1)
    except CaptureError:
        raise
    except (OSError, TimeoutError, urllib.error.URLError) as error:
        raise CaptureError(
            f"host-publication-authority:transport:{type(error).__name__}"
        ) from error
    if len(payload) > MAX_ARTIFACT_RESPONSE_BYTES:
        raise CaptureError("host-publication-authority:response-size")
    return payload


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
    prefix: str = "host-publication-authority",
) -> dict[str, Any]:
    """Select the exact latest push run of the canonical workflow on ``master``."""

    runs = document.get("workflow_runs") if isinstance(document, Mapping) else None
    total_count = document.get("total_count") if isinstance(document, Mapping) else None
    if (
        type(total_count) is not int
        or not isinstance(runs, list)
        or total_count != len(runs)
        or total_count < 1
        or total_count > MAX_GITHUB_WORKFLOW_RUNS
    ):
        raise CaptureError(f"{prefix}:workflow-run-envelope")
    projected: list[dict[str, Any]] = []
    run_ids: set[int] = set()
    suite_ids: set[int] = set()
    run_numbers: set[int] = set()
    for run in runs:
        if not isinstance(run, Mapping):
            raise CaptureError(f"{prefix}:workflow-run-row")
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
            raise CaptureError(f"{prefix}:workflow-run-row")
        if (
            run_id in run_ids
            or suite_id in suite_ids
            or run_number in run_numbers
        ):
            raise CaptureError(f"{prefix}:workflow-run-identity")
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
            raise CaptureError(f"{prefix}:workflow-run-timestamp")
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
            raise CaptureError(f"{prefix}:workflow-run-binding")
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
        raise CaptureError(f"{prefix}:workflow-run-not-green")
    return selected


def _project_exact_checks(
    document: object,
    source_commit: str,
    workflow_run: Mapping[str, Any],
    *,
    prefix: str = "host-publication-authority",
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
        raise CaptureError(f"{prefix}:job-envelope")
    selected: dict[str, Mapping[str, Any]] = {}
    identities: set[int] = set()
    for run in runs:
        if not isinstance(run, Mapping):
            raise CaptureError(f"{prefix}:job-row")
        name = run.get("name")
        if name not in REQUIRED_GITHUB_CHECKS:
            raise CaptureError(f"{prefix}:unexpected-check")
        run_id = run.get("id")
        if type(run_id) is not int or run_id <= 0:
            raise CaptureError(f"{prefix}:job-row")
        if run_id in identities:
            raise CaptureError(f"{prefix}:duplicate-check-id")
        identities.add(run_id)
        if name in selected:
            raise CaptureError(f"{prefix}:required-check-set")
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
            raise CaptureError(f"{prefix}:check-timestamp:{name}")
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
            raise CaptureError(f"{prefix}:check-not-green:{name}")
        selected[name] = run
    if set(selected) != set(REQUIRED_GITHUB_CHECKS):
        raise CaptureError(f"{prefix}:required-check-set")
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
            raise CaptureError(f"{prefix}:check-not-green:{name}")
        checks.append(projected)
    if len({row["id"] for row in checks}) != len(checks):
        raise CaptureError(f"{prefix}:duplicate-check-id")
    return checks


def verify_publication_authority(
    source_commit: str,
    fetch_json: Callable[[str], Any] = _fetch_json,
    *,
    commit_tree_sha: str,
    artifact_payloads: Mapping[str, bytes] | None = None,
    fetch_raw: Callable[[str], bytes] = _fetch_raw,
) -> dict[str, Any]:
    """Require current master and its exact latest successful ``ci.yml`` push attempt."""

    if not isinstance(source_commit, str) or not _COMMIT_RE.fullmatch(source_commit):
        raise CaptureError("host-publication-authority:source-commit")
    branch_url = f"{GITHUB_API_ROOT}/branches/{GITHUB_BRANCH}"
    workflow_runs_url = (
        f"{GITHUB_API_ROOT}/actions/workflows/{GITHUB_WORKFLOW_FILE}/runs?"
        f"branch={GITHUB_BRANCH}&event=push&head_sha={source_commit}&"
        f"per_page={MAX_GITHUB_WORKFLOW_RUNS}&page=1"
    )
    try:
        branch_document = fetch_json(branch_url)
        workflow_runs_document = fetch_json(workflow_runs_url)
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:fetch:{type(error).__name__}"
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
        raise CaptureError("host-publication-authority:branch-head")
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
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:jobs-fetch:{type(error).__name__}"
        ) from error
    checks = _project_exact_checks(jobs_document, source_commit, workflow_run)
    try:
        workflow_replay_document = fetch_json(workflow_runs_url)
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:workflow-replay-fetch:{type(error).__name__}"
        ) from error
    if _project_exact_workflow_run(
        workflow_replay_document,
        source_commit,
    ) != workflow_run:
        raise CaptureError("host-publication-authority:workflow-run-replay")
    if not isinstance(commit_tree_sha, str) or _COMMIT_RE.fullmatch(commit_tree_sha) is None:
        raise CaptureError("host-publication-authority:commit-tree")
    tree_url = f"{GITHUB_API_ROOT}/git/trees/{commit_tree_sha}?recursive=1"
    try:
        tree_document = fetch_json(tree_url)
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:tree-fetch:{type(error).__name__}"
        ) from error
    tree_rows = tree_document.get("tree") if isinstance(tree_document, Mapping) else None
    if (
        not isinstance(tree_document, Mapping)
        or tree_document.get("sha") != commit_tree_sha
        or tree_document.get("truncated") is not False
        or not isinstance(tree_rows, list)
        or len(tree_rows) > MAX_GITHUB_TREE_ENTRIES
    ):
        raise CaptureError("host-publication-authority:tree-envelope")
    selected_tree: dict[str, Mapping[str, Any]] = {}
    for row in tree_rows:
        if not isinstance(row, Mapping):
            raise CaptureError("host-publication-authority:tree-row")
        path = row.get("path")
        if not isinstance(path, str):
            raise CaptureError("host-publication-authority:tree-row")
        if path not in HOST_PUBLICATION_ARTIFACT_PATHS:
            continue
        if path in selected_tree:
            raise CaptureError(
                f"host-publication-authority:duplicate-tree-path:{path}"
            )
        selected_tree[path] = row
    if set(selected_tree) != set(HOST_PUBLICATION_ARTIFACT_PATHS):
        raise CaptureError("host-publication-authority:tree-artifact-set")
    payloads = dict(artifact_payloads or {})
    if set(payloads) != set(HOST_PUBLICATION_ARTIFACT_PATHS):
        raise CaptureError("host-publication-authority:artifact-set")
    artifacts: list[dict[str, Any]] = []
    for path in HOST_PUBLICATION_ARTIFACT_PATHS:
        payload = payloads[path]
        if (
            not isinstance(payload, bytes)
            or not payload
            or len(payload) > MAX_ARTIFACT_RESPONSE_BYTES
        ):
            raise CaptureError(f"host-publication-authority:artifact-payload:{Path(path).name}")
        git_blob_oid = _git_blob_oid(payload)
        tree_row = selected_tree[path]
        if (
            tree_row.get("path") != path
            or tree_row.get("type") != "blob"
            or tree_row.get("mode") != "100644"
            or type(tree_row.get("size")) is not int
            or tree_row.get("size") != len(payload)
            or tree_row.get("sha") != git_blob_oid
        ):
            raise CaptureError(
                f"host-publication-authority:tree-artifact:{Path(path).name}"
            )
        # The recursive tree above already binds the exact path, blob type, `100644` mode,
        # integer size, and Git blob identity of the committed artifact. The raw-media fetch
        # completes the proof with the committed bytes themselves, which the JSON envelope
        # cannot inline above one mebibyte. Same endpoint, same single GET per artifact.
        encoded_path = urllib.parse.quote(path, safe="/")
        content_url = f"{GITHUB_API_ROOT}/contents/{encoded_path}?ref={source_commit}"
        try:
            committed = fetch_raw(content_url)
        except CaptureError:
            raise
        except Exception as error:
            raise CaptureError(
                f"host-publication-authority:artifact-fetch:{type(error).__name__}"
            ) from error
        if not isinstance(committed, bytes) or committed != payload:
            raise CaptureError(
                f"host-publication-authority:artifact-drift:{Path(path).name}"
            )
        artifacts.append(
            {
                "path": path,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "git_blob_oid": git_blob_oid,
                "git_mode": "100644",
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


def verify_host_commit_topology(
    host_commit: str,
    packet_source_commit: str,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> str:
    """Prove H is the sole-child publication of the authorized B3 packet."""

    if not isinstance(host_commit, str) or _COMMIT_RE.fullmatch(host_commit) is None:
        raise CaptureError("host-publication-authority:topology-host-commit")
    if (
        not isinstance(packet_source_commit, str)
        or _COMMIT_RE.fullmatch(packet_source_commit) is None
    ):
        raise CaptureError("host-publication-authority:topology-packet-commit")
    url = f"{GITHUB_API_ROOT}/commits/{host_commit}?per_page=100&page=1"
    try:
        document = fetch_json(url)
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:topology-fetch:{type(error).__name__}"
        ) from error
    parents = document.get("parents") if isinstance(document, Mapping) else None
    commit = document.get("commit") if isinstance(document, Mapping) else None
    tree = commit.get("tree") if isinstance(commit, Mapping) else None
    tree_sha = tree.get("sha") if isinstance(tree, Mapping) else None
    if (
        not isinstance(document, Mapping)
        or document.get("sha") != host_commit
        or not isinstance(parents, list)
        or len(parents) != 1
        or not isinstance(parents[0], Mapping)
        or parents[0].get("sha") != packet_source_commit
        or not isinstance(tree_sha, str)
        or _COMMIT_RE.fullmatch(tree_sha) is None
    ):
        raise CaptureError("host-publication-authority:commit-parent")
    files = document.get("files")
    if not isinstance(files, list):
        raise CaptureError("host-publication-authority:changed-paths")
    filenames: list[str] = []
    for row in files:
        filename = row.get("filename") if isinstance(row, Mapping) else None
        if not isinstance(filename, str) or row.get("previous_filename") is not None:
            raise CaptureError("host-publication-authority:changed-paths")
        filenames.append(filename)
    if len(filenames) != len(set(filenames)) or set(filenames) != set(
        HOST_PUBLICATION_ARTIFACT_PATHS
    ):
        raise CaptureError("host-publication-authority:changed-paths")
    return tree_sha


def verify_current_authority(
    source_commit: str,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> list[dict[str, Any]]:
    """Replay exact master, workflow run, and attempt jobs before returning green E."""

    try:
        document = fetch_json(f"{GITHUB_API_ROOT}/branches/{GITHUB_BRANCH}")
        workflow_runs_document = fetch_json(
            f"{GITHUB_API_ROOT}/actions/workflows/{GITHUB_WORKFLOW_FILE}/runs?"
            f"branch={GITHUB_BRANCH}&event=push&head_sha={source_commit}&"
            f"per_page={MAX_GITHUB_WORKFLOW_RUNS}&page=1"
        )
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    commit = document.get("commit") if isinstance(document, Mapping) else None
    if (
        not isinstance(document, Mapping)
        or document.get("name") != GITHUB_BRANCH
        or not isinstance(commit, Mapping)
        or commit.get("sha") != source_commit
    ):
        raise CaptureError("host-publication-authority:branch-recheck")
    workflow_run = _project_exact_workflow_run(
        workflow_runs_document,
        source_commit,
        prefix="host-publication-authority:terminal",
    )
    try:
        jobs_document = fetch_json(
            f"{GITHUB_API_ROOT}/actions/runs/{workflow_run['id']}/attempts/"
            f"{workflow_run['run_attempt']}/jobs?per_page={MAX_GITHUB_JOBS}&page=1"
        )
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    checks = _project_exact_checks(
        jobs_document,
        source_commit,
        workflow_run,
        prefix="host-publication-authority:terminal",
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
    except CaptureError:
        raise
    except Exception as error:
        raise CaptureError(
            f"host-publication-authority:branch-recheck-fetch:{type(error).__name__}"
        ) from error
    if _project_exact_workflow_run(
        workflow_replay_document,
        source_commit,
        prefix="host-publication-authority:terminal",
    ) != workflow_run:
        raise CaptureError("host-publication-authority:terminal:workflow-run-replay")
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
        raise CaptureError("host-publication-authority:branch-recheck")
    return checks


def _publication_authority_problems(
    authority: Any,
    *,
    source_commit: Any,
    artifacts: list[dict[str, Any]],
    label: str,
) -> list[str]:
    problems: list[str] = []
    expected_fields = {
        "schema",
        "repository",
        "branch",
        "source_commit",
        "branch_head_sha",
        "required_checks",
        "checks",
        "artifacts",
        "verified",
    }
    if type(authority) is not dict or set(authority) != expected_fields:
        return [f"{label}:field-set"]
    checks = authority.get("checks")
    if (
        authority.get("schema") != PUBLICATION_AUTHORITY_SCHEMA
        or authority.get("repository") != GITHUB_REPOSITORY
        or authority.get("branch") != GITHUB_BRANCH
        or not isinstance(source_commit, str)
        or _COMMIT_RE.fullmatch(source_commit) is None
        or authority.get("source_commit") != source_commit
        or authority.get("branch_head_sha") != source_commit
        or not _exact_json_value(
            authority.get("required_checks"),
            list(REQUIRED_GITHUB_CHECKS),
        )
        or not _exact_json_value(authority.get("artifacts"), artifacts)
        or authority.get("verified") is not True
    ):
        problems.append(f"{label}:contract")
    check_ids: list[int] = []
    if not isinstance(checks, list) or len(checks) != len(REQUIRED_GITHUB_CHECKS):
        problems.append(f"{label}:check-set")
    else:
        for row, name in zip(checks, REQUIRED_GITHUB_CHECKS):
            check_id = row.get("id") if type(row) is dict else None
            if (
                type(row) is not dict
                or set(row)
                != {"name", "id", "status", "conclusion", "head_sha", "app_slug"}
                or row.get("name") != name
                or type(check_id) is not int
                or check_id <= 0
                or row.get("status") != "completed"
                or row.get("conclusion") != "success"
                or row.get("head_sha") != source_commit
                or row.get("app_slug") != EXPECTED_CHECK_APP
            ):
                problems.append(f"{label}:check-binding:{name}")
            else:
                check_ids.append(check_id)
        if len(check_ids) != len(REQUIRED_GITHUB_CHECKS) or len(set(check_ids)) != len(
            check_ids
        ):
            problems.append(f"{label}:check-ids")
    return problems


def _default_docker_client_path() -> Path:
    located = shutil.which("docker", path=SANITIZED_ENVIRONMENT["PATH"])
    if located is None:
        raise CaptureError("docker-runtime:client-missing")
    return Path(located)


@dataclass(frozen=True)
class Contract:
    schema: str
    ready_verdict: str
    remote_files: Mapping[str, tuple[str, str, int]]
    repositories: Mapping[str, Mapping[str, Any]]
    required_untracked_bindings: Mapping[tuple[str, str], str]
    storage_identity: Mapping[str, Any]
    dataset_schema: str
    dataset_contract_sha256: str
    dataset_root: str
    dataset_version: str
    dataset_archive_root: str
    dataset_metadata_root: str
    dataset_map_root: str
    dataset_mount: Mapping[str, str]
    dataset_proof_basis: Mapping[str, Any]
    dataset_archives: Mapping[str, tuple[str, int]]
    dataset_metadata_files: tuple[str, ...]
    dataset_map_anchors: tuple[str, ...]
    dataset_map_directories: Mapping[str, tuple[str, ...]]
    image_ids: Mapping[str, str]
    compose_input_sha256: str
    compose_output_sha256: str
    projected_output_bytes: int
    minimum_remote_free_bytes: int
    minimum_reserve_bytes: int
    minimum_local_free_bytes: int
    host: str = EXPECTED_HOST
    gpu_model: str = EXPECTED_GPU_MODEL
    gpu_uuid: str = EXPECTED_GPU_UUID
    gpu_driver: str = EXPECTED_GPU_DRIVER
    gpu_memory_mib: int = EXPECTED_GPU_MEMORY_MIB


def _run_command(argv: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            list(argv),
            env=SANITIZED_ENVIRONMENT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CaptureError(f"command:{argv[0]}:{type(error).__name__}") from error
    if completed.returncode != 0:
        raise CaptureError(f"command:{argv[0]}:exit-{completed.returncode}")
    return completed.stdout


@dataclass(frozen=True)
class Hooks:
    run: Callable[[Sequence[str]], bytes] = _run_command
    fetch_json: Callable[[str], Any] = _fetch_json
    fetch_raw: Callable[[str], bytes] = _fetch_raw
    hostname: Callable[[], str] = socket.gethostname
    disk_free: Callable[[Path], int] = lambda path: shutil.disk_usage(path).free
    device: Callable[[Path], int] = lambda path: path.stat().st_dev
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)
    pid: Callable[[], int] = os.getpid
    dataset_read: Callable[[Path], tuple[dict[str, Any], list[str]]] = lambda path: (
        _read_dataset_file(path)
    )
    interpreter_receipt: Callable[[], tuple[dict[str, Any], list[str]]] | None = None
    invocation_receipt: Callable[[], tuple[dict[str, Any], list[str]]] | None = None
    preparation_receipt: Callable[[], tuple[dict[str, Any], list[str]]] | None = None
    host_artifact_payloads: (
        Callable[[], tuple[dict[str, bytes], list[str]]] | None
    ) = None
    docker_client_path: Callable[[], Path] = _default_docker_client_path
    mission_state_path: Callable[[], Path] = lambda: HERE / "MISSION_STATE.json"


@dataclass(frozen=True)
class _EnvironmentAdmission:
    host_preparation: dict[str, Any]
    preparation_parent_identity: tuple[int, int, int]
    manifest_claim: dict[str, Any]


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _component_snapshot(path: Path) -> tuple[list[tuple[str, tuple[int, int, int]]], list[str]]:
    problems: list[str] = []
    snapshots: list[tuple[str, tuple[int, int, int]]] = []
    if not path.is_absolute():
        return snapshots, [f"path:not-absolute:{path}"]
    cursor = Path(path.anchor)
    for component in path.parts[1:]:
        cursor /= component
        try:
            info = cursor.lstat()
        except OSError as error:
            problems.append(f"path:lstat:{cursor}:{type(error).__name__}")
            break
        snapshots.append((str(cursor), (info.st_dev, info.st_ino, info.st_mode)))
        if stat.S_ISLNK(info.st_mode):
            problems.append(f"path:symlink:{cursor}")
    return snapshots, problems


def stable_read(
    path: Path,
    *,
    collect_bytes: bool = False,
    include_mode: bool = False,
) -> tuple[dict[str, Any], bytes | None, list[str]]:
    """Read one regular physical file without accepting symlinks or an unstable inode."""

    path = Path(path)
    problems: list[str] = []
    components_before, component_problems = _component_snapshot(path)
    problems.extend(component_problems)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        resolved = None
        problems.append(f"path:resolve:{path}:{type(error).__name__}")
    if resolved is not None and resolved != path:
        problems.append(f"path:realpath:{path}:{resolved}")

    digest = hashlib.sha256()
    chunks: list[bytes] | None = [] if collect_bytes else None
    byte_count: int | None = None
    before: os.stat_result | None = None
    after: os.stat_result | None = None
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            problems.append(f"path:not-regular:{path}")
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
            if chunks is not None:
                chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as error:
        problems.append(f"path:read:{path}:{type(error).__name__}")
    finally:
        if descriptor is not None:
            os.close(descriptor)

    if before is not None and after is not None and _stat_identity(before) != _stat_identity(after):
        problems.append(f"path:unstable-file:{path}")
    components_after, after_problems = _component_snapshot(path)
    problems.extend(after_problems)
    if components_before != components_after:
        problems.append(f"path:unstable-components:{path}")
    if before is not None and components_after:
        final = components_after[-1][1]
        if (before.st_dev, before.st_ino, before.st_mode) != final:
            problems.append(f"path:descriptor-mismatch:{path}")

    receipt = {
        "path": str(path),
        "sha256": digest.hexdigest() if byte_count is not None else None,
        "bytes": byte_count,
    }
    if include_mode:
        receipt["mode"] = (
            stat.S_IMODE(before.st_mode)
            if before is not None and stat.S_ISREG(before.st_mode)
            else None
        )
    data = b"".join(chunks) if chunks is not None and byte_count is not None else None
    return receipt, data, sorted(set(problems))


def validate_source_bound_mission_state(
    host_preparation: Any,
    mission_state_path: Path,
) -> dict[str, Any]:
    """Reject every non-executable phase before GitHub or runtime observation begins."""

    evidence = (
        host_preparation.get("evidence")
        if isinstance(host_preparation, Mapping)
        else None
    )
    packet = evidence.get("packet") if isinstance(evidence, Mapping) else None
    source_commit = (
        packet.get("source_commit")
        if isinstance(packet, Mapping)
        else None
    )
    files = packet.get("files") if isinstance(packet, Mapping) else None
    claim = (
        files.get("MISSION_STATE.json")
        if isinstance(files, Mapping)
        else None
    )
    if (
        not isinstance(source_commit, str)
        or _COMMIT_RE.fullmatch(source_commit) is None
        or not isinstance(claim, Mapping)
        or set(claim) != {"path", "sha256", "bytes", "mode"}
    ):
        raise EnvironmentAdmissionStop("mission-state:packet-binding")
    observed, payload, read_problems = stable_read(
        Path(mission_state_path),
        collect_bytes=True,
        include_mode=True,
    )
    if (
        read_problems
        or payload is None
        or not _same_file_claim(observed, claim)
    ):
        raise EnvironmentAdmissionStop("mission-state:packet-binding")
    try:
        state = json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise EnvironmentAdmissionStop(
            f"mission-state:json:{type(error).__name__}"
        ) from error
    if type(state) is not dict:
        raise EnvironmentAdmissionStop("mission-state:document")
    if set(state) != EXPECTED_MISSION_STATE_FIELDS:
        raise EnvironmentAdmissionStop("mission-state:field-set")
    if state.get("schema") != MISSION_STATE_SCHEMA:
        raise EnvironmentAdmissionStop("mission-state:schema")
    next_program = state.get("next_program")
    if (
        type(next_program) is not dict
        or set(next_program) != EXPECTED_NEXT_PROGRAM_FIELDS
    ):
        raise EnvironmentAdmissionStop("mission-state:next-program-field-set")
    phase = next_program.get("phase")
    if type(phase) is not str or phase not in MISSION_PHASE_CONTRACTS:
        raise EnvironmentAdmissionStop("mission-state:phase")
    phase_contract = MISSION_PHASE_CONTRACTS[phase]
    for field, expected in EXPECTED_MISSION_STATE_COMMON.items():
        if not _exact_json_value(state.get(field), expected):
            raise EnvironmentAdmissionStop("mission-state:contract")
    if not _exact_json_value(state.get("run_state"), phase_contract["run_state"]):
        raise EnvironmentAdmissionStop("mission-state:run-state")
    expected_next_program = {
        "iteration": 135,
        "name": "semantics-free placebo dose-response causal closure",
        "phase": phase,
        "authorized_actions": list(phase_contract["authorized_actions"]),
        "forbidden_actions": list(phase_contract["forbidden_actions"]),
    }
    if not _exact_json_value(next_program, expected_next_program):
        raise EnvironmentAdmissionStop("mission-state:next-program")
    if phase == CONTROL_HARDENING_PHASE:
        raise EnvironmentAdmissionStop("mission-state:control-hardening-required")
    if phase == PREREGISTERED_PHASE:
        raise EnvironmentAdmissionStop("mission-state:preregistered-tooling-required")
    return state


def _admit_environment_attempt(hooks: Hooks) -> _EnvironmentAdmission:
    """Require an exact green H receipt and its source-bound executable state.

    This function is intentionally free of clock, hostname, GitHub, Docker, dataset, storage,
    and output operations.  A failure here is not an E attempt and must not create an E receipt.
    """

    try:
        host_preparation, preparation_problems = (
            hooks.preparation_receipt()
            if hooks.preparation_receipt is not None
            else load_and_validate_preparation_receipt()
        )
    except Exception as error:
        raise EnvironmentAdmissionStop(
            f"host-preparation:probe:{type(error).__name__}"
        ) from error
    semantic_problems = validate_host_preparation_evidence(host_preparation)
    if (
        type(preparation_problems) is not list
        or preparation_problems
        or semantic_problems
    ):
        raise EnvironmentAdmissionStop("host-preparation:not-green")
    try:
        replayed_preparation, replay_problems = (
            load_and_validate_preparation_receipt()
        )
    except Exception as error:
        raise EnvironmentAdmissionStop(
            f"host-preparation:replay:{type(error).__name__}"
        ) from error
    if (
        replay_problems
        or not _exact_json_value(
            host_preparation,
            replayed_preparation,
        )
    ):
        raise EnvironmentAdmissionStop("host-preparation:not-green")
    try:
        preparation_payload = _preparation_receipt_file_payload(
            replayed_preparation["evidence"]
        )
        before_mission = _observe_receipt_pair(
            CANONICAL_PREPARATION_RECEIPT_PATH,
            pending_basename=EXPECTED_H_PENDING_BASENAME,
            marker_basename=EXPECTED_H_ATTEMPT_BASENAME,
            payload=preparation_payload,
            problem_prefix="preparation:terminal-topology",
        )
    except (CaptureError, KeyError, TypeError, ValueError) as error:
        raise EnvironmentAdmissionStop(
            "host-preparation:terminal-replay"
        ) from error
    validate_source_bound_mission_state(
        host_preparation,
        hooks.mission_state_path(),
    )
    try:
        after_mission = _observe_receipt_pair(
            CANONICAL_PREPARATION_RECEIPT_PATH,
            pending_basename=EXPECTED_H_PENDING_BASENAME,
            marker_basename=EXPECTED_H_ATTEMPT_BASENAME,
            payload=preparation_payload,
            problem_prefix="preparation:terminal-topology",
        )
    except CaptureError as error:
        raise EnvironmentAdmissionStop(
            "host-preparation:terminal-replay"
        ) from error
    if before_mission != after_mission:
        raise EnvironmentAdmissionStop("host-preparation:parent-drift")
    evidence = host_preparation.get("evidence")
    packet = evidence.get("packet") if type(evidence) is dict else None
    files = packet.get("files") if type(packet) is dict else None
    manifest_claim = (
        files.get(CANONICAL_MANIFEST_PATH.name)
        if type(files) is dict
        else None
    )
    if not _exact_file_claim_shape(manifest_claim):
        raise EnvironmentAdmissionStop("host-preparation:manifest-binding")
    return _EnvironmentAdmission(
        host_preparation=dict(host_preparation),
        preparation_parent_identity=after_mission.parent_identity,
        manifest_claim=dict(manifest_claim),
    )


def _host_artifact_payloads() -> tuple[dict[str, bytes], list[str]]:
    payloads: dict[str, bytes] = {}
    problems: list[str] = []
    local_paths = (
        CANONICAL_PACKET_MANIFEST_PATH,
        CANONICAL_PREPARATION_RECEIPT_PATH,
    )
    for repository_path, local_path in zip(
        HOST_PUBLICATION_ARTIFACT_PATHS, local_paths, strict=True
    ):
        _receipt, payload, file_problems = stable_read(local_path, collect_bytes=True)
        problems.extend(
            f"host-publication-artifact:{Path(repository_path).name}:{item}"
            for item in file_problems
        )
        if payload is not None:
            payloads[repository_path] = payload
    return payloads, sorted(set(problems))


def _bounded_text(value: Any, label: str, *, maximum: int = 256) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise CaptureError(f"docker-runtime:{label}")
    return value


def _bounded_positive_integer(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0 or value >= 2**63:
        raise CaptureError(f"docker-runtime:{label}")
    return value


def _normalized_docker_architecture(value: str) -> str:
    return DOCKER_ARCHITECTURE_ALIASES.get(value, value)


def _docker_json(hooks: Hooks, client: Path, *arguments: str) -> Mapping[str, Any]:
    payload = hooks.run((str(client), *arguments))
    if len(payload) > MAX_GITHUB_RESPONSE_BYTES:
        raise CaptureError("docker-runtime:command-response-size")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CaptureError("docker-runtime:command-json") from error
    if not isinstance(value, Mapping):
        raise CaptureError("docker-runtime:command-object")
    return value


def _docker_text(hooks: Hooks, client: Path, *arguments: str) -> str:
    payload = hooks.run((str(client), *arguments))
    if len(payload) > 4096:
        raise CaptureError("docker-runtime:command-response-size")
    try:
        value = payload.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise CaptureError("docker-runtime:command-text") from error
    return _bounded_text(value, "command-text")


def _client_version_projection(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise CaptureError("docker-runtime:client-version")
    return {
        "version": _bounded_text(value.get("Version"), "client-version:version"),
        "api_version": _bounded_text(value.get("ApiVersion"), "client-version:api-version"),
        "git_commit": _bounded_text(value.get("GitCommit"), "client-version:git-commit"),
        "go_version": _bounded_text(value.get("GoVersion"), "client-version:go-version"),
        "os": _bounded_text(value.get("Os"), "client-version:os"),
        "arch": _bounded_text(value.get("Arch"), "client-version:arch"),
        "build_time": _bounded_text(value.get("BuildTime"), "client-version:build-time"),
        "context": _bounded_text(value.get("Context"), "client-version:context"),
    }


def _daemon_engine_details(value: Mapping[str, Any]) -> Mapping[str, Any]:
    # Docker Engine 29 moved GitCommit, GoVersion, BuildTime, and Experimental out of the
    # top-level Server object into the Engine component's Details map (Experimental became the
    # string "true"/"false" there). Older engines carry them at the top level. Read the Engine
    # component when present so both generations of output validate exactly.
    components = value.get("Components")
    if isinstance(components, list):
        for row in components:
            if isinstance(row, Mapping) and row.get("Name") == "Engine":
                details = row.get("Details")
                if isinstance(details, Mapping):
                    return details
    return {}


def _daemon_field(value: Mapping[str, Any], details: Mapping[str, Any], name: str) -> Any:
    field = value.get(name)
    if field is None:
        field = details.get(name)
    return field


def _daemon_version_projection(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CaptureError("docker-runtime:daemon-version")
    platform_row = value.get("Platform")
    if not isinstance(platform_row, Mapping):
        raise CaptureError("docker-runtime:daemon-version:platform")
    details = _daemon_engine_details(value)
    experimental = _daemon_field(value, details, "Experimental")
    if experimental in ("true", "false"):
        experimental = experimental == "true"
    if type(experimental) is not bool:
        raise CaptureError("docker-runtime:daemon-version:experimental")
    return {
        "platform_name": _bounded_text(
            platform_row.get("Name"), "daemon-version:platform-name"
        ),
        "version": _bounded_text(value.get("Version"), "daemon-version:version"),
        "api_version": _bounded_text(value.get("ApiVersion"), "daemon-version:api-version"),
        "min_api_version": _bounded_text(
            value.get("MinAPIVersion"), "daemon-version:min-api-version"
        ),
        "git_commit": _bounded_text(
            _daemon_field(value, details, "GitCommit"), "daemon-version:git-commit"
        ),
        "go_version": _bounded_text(
            _daemon_field(value, details, "GoVersion"), "daemon-version:go-version"
        ),
        "os": _bounded_text(value.get("Os"), "daemon-version:os"),
        "arch": _bounded_text(value.get("Arch"), "daemon-version:arch"),
        "build_time": _bounded_text(
            _daemon_field(value, details, "BuildTime"), "daemon-version:build-time"
        ),
        "experimental": experimental,
    }


def _daemon_info_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": _bounded_text(value.get("ID"), "daemon-info:id"),
        "name": _bounded_text(value.get("Name"), "daemon-info:name"),
        "server_version": _bounded_text(
            value.get("ServerVersion"), "daemon-info:server-version"
        ),
        "docker_root_dir": _bounded_text(
            value.get("DockerRootDir"), "daemon-info:docker-root-dir", maximum=1024
        ),
        "driver": _bounded_text(value.get("Driver"), "daemon-info:driver"),
        "operating_system": _bounded_text(
            value.get("OperatingSystem"), "daemon-info:operating-system"
        ),
        "os_type": _bounded_text(value.get("OSType"), "daemon-info:os-type"),
        "architecture": _bounded_text(
            value.get("Architecture"), "daemon-info:architecture"
        ),
        "ncpu": _bounded_positive_integer(value.get("NCPU"), "daemon-info:ncpu"),
        "mem_total": _bounded_positive_integer(
            value.get("MemTotal"), "daemon-info:mem-total"
        ),
        "kernel_version": _bounded_text(
            value.get("KernelVersion"), "daemon-info:kernel-version"
        ),
        "cgroup_driver": _bounded_text(
            value.get("CgroupDriver"), "daemon-info:cgroup-driver"
        ),
        "cgroup_version": _bounded_text(
            value.get("CgroupVersion"), "daemon-info:cgroup-version"
        ),
    }


def _docker_client_identity(path: Path) -> tuple[int, int, int, int, int, int]:
    try:
        info = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CaptureError(f"docker-runtime:client-identity:{type(error).__name__}") from error
    if resolved != path or not stat.S_ISREG(info.st_mode):
        raise CaptureError("docker-runtime:client-identity")
    return _stat_identity(info)


def _revalidate_docker_client(
    path: Path | None,
    client_receipt: Mapping[str, Any] | None,
    expected_identity: tuple[int, int, int, int, int, int] | None,
    *,
    label: str,
    problems: list[str],
) -> bool:
    """Rehash the exact physical client around every Docker-dependent phase."""

    if path is None or client_receipt is None or expected_identity is None:
        return False
    try:
        before = _docker_client_identity(path)
        observed, _payload, read_problems = stable_read(path)
        after = _docker_client_identity(path)
        if (
            read_problems
            or before != expected_identity
            or after != expected_identity
            or observed.get("sha256") != client_receipt.get("sha256")
            or type(client_receipt.get("bytes")) is not int
            or observed.get("bytes") != client_receipt.get("bytes")
            or client_receipt.get("physical_path") != str(path)
            or client_receipt.get("realpath") != str(path)
            or not os.access(path, os.X_OK)
        ):
            raise CaptureError("docker-runtime:client-drift")
    except (CaptureError, OSError):
        problems.append(f"docker-runtime:client-drift:{label}")
        return False
    return True


def _probe_docker_runtime(
    hooks: Hooks,
    *,
    expected_host: str,
    problems: list[str],
) -> tuple[
    dict[str, Any] | None,
    Path | None,
    tuple[int, int, int, int, int, int] | None,
]:
    """Bind a fixed, non-secret projection of the client, endpoint, and daemon."""

    try:
        invocation_path = Path(hooks.docker_client_path()).absolute()
        physical_path = invocation_path.resolve(strict=True)
        client_identity = _docker_client_identity(physical_path)
        client_file, _payload, client_problems = stable_read(physical_path)
        if client_problems:
            raise CaptureError("docker-runtime:client-file")
        if not os.access(physical_path, os.X_OK):
            raise CaptureError("docker-runtime:client-executable")
        version_document = _docker_json(
            hooks, physical_path, "version", "--format", "{{json .}}"
        )
        info_document = _docker_json(hooks, physical_path, "info", "--format", "{{json .}}")
        context_name = _docker_text(hooks, physical_path, "context", "show")
        endpoint_payload = hooks.run(
            (
                str(physical_path),
                "context",
                "inspect",
                "--format",
                "{{json .Endpoints.docker.Host}}",
                context_name,
            )
        )
        if len(endpoint_payload) > 4096:
            raise CaptureError("docker-runtime:context-endpoint-size")
        try:
            endpoint = json.loads(endpoint_payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CaptureError("docker-runtime:context-endpoint-json") from error
        endpoint = _bounded_text(endpoint, "context-endpoint", maximum=1024)
        client_version = _client_version_projection(version_document.get("Client"))
        daemon_version = _daemon_version_projection(version_document.get("Server"))
        daemon_info = _daemon_info_projection(info_document)
        if (
            context_name != "default"
            or endpoint != "unix:///var/run/docker.sock"
            or client_version["context"] != context_name
            or daemon_info["name"] != expected_host
            or daemon_info["server_version"] != daemon_version["version"]
            or daemon_info["os_type"] != daemon_version["os"]
            or _normalized_docker_architecture(daemon_info["architecture"])
            != _normalized_docker_architecture(daemon_version["arch"])
            or not Path(daemon_info["docker_root_dir"]).is_absolute()
        ):
            raise CaptureError("docker-runtime:identity")
        receipt = {
                "schema": DOCKER_RUNTIME_SCHEMA,
                "client": {
                    "invocation_path": str(invocation_path),
                    "physical_path": str(physical_path),
                    "realpath": str(physical_path),
                    "sha256": client_file["sha256"],
                    "bytes": client_file["bytes"],
                    "version": client_version,
                },
                "context": {"name": context_name, "endpoint": endpoint},
                "daemon": {"info": daemon_info, "version": daemon_version},
            }
        revalidation_problems: list[str] = []
        if not _revalidate_docker_client(
            physical_path,
            receipt["client"],
            client_identity,
            label="runtime-probe",
            problems=revalidation_problems,
        ):
            raise CaptureError(revalidation_problems[0])
        return receipt, physical_path, client_identity
    except (CaptureError, OSError) as error:
        code = str(error) if isinstance(error, CaptureError) else f"docker-runtime:{type(error).__name__}"
        problems.append(code)
        return None, None, None


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _interpreter_receipt() -> tuple[dict[str, Any], list[str]]:
    """Bind the physical interpreter that executes every host probe."""

    problems: list[str] = []
    invocation_path = Path(sys.executable).absolute()
    try:
        physical_path = invocation_path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        physical_path = invocation_path
        problems.append(f"interpreter:resolve:{type(error).__name__}")
    executable, _payload, file_problems = stable_read(physical_path)
    problems.extend(f"interpreter:{item}" for item in file_problems)
    version = platform.python_version()
    implementation = platform.python_implementation()
    if not _PYTHON_VERSION_RE.fullmatch(version):
        problems.append("interpreter:version-format")
    if sys.version_info < (3, 10):
        problems.append("interpreter:minimum-version")
    if implementation not in {"CPython"}:
        problems.append("interpreter:implementation")
    return (
        {
            "invocation_path": str(invocation_path),
            "physical_path": str(physical_path),
            "realpath": str(physical_path),
            "sha256": executable.get("sha256"),
            "bytes": executable.get("bytes"),
            "version": version,
            "implementation": implementation,
        },
        sorted(set(problems)),
    )


def _invocation_receipt() -> tuple[dict[str, Any], list[str]]:
    """Prove that the command was re-executed with the frozen minimal environment."""

    problems: list[str] = []
    observed = dict(os.environ)
    if observed != SANITIZED_ENVIRONMENT:
        problems.append("invocation:environment")
    if sys.flags.isolated != 1:
        problems.append("invocation:not-isolated")
    script = Path(sys.argv[0]).absolute() if sys.argv else Path("")
    if script != Path(__file__).absolute() or script != HERE / "capture_environment135.py":
        problems.append("invocation:canonical-script")
    try:
        physical_interpreter = str(Path(sys.executable).resolve(strict=True))
    except (OSError, RuntimeError):
        physical_interpreter = str(Path(sys.executable).absolute())
        problems.append("invocation:interpreter-realpath")
    return (
        {
            "sanitized": not problems,
            "isolated": sys.flags.isolated == 1,
            "environment": dict(SANITIZED_ENVIRONMENT),
            "argv": [physical_interpreter, "-I", *sys.argv],
            "canonical_script": str(HERE / "capture_environment135.py"),
        },
        sorted(set(problems)),
    )


def _exact_file_claim_shape(value: object) -> bool:
    if type(value) is not dict or set(value) != {"path", "sha256", "bytes", "mode"}:
        return False
    path = value.get("path")
    sha256 = value.get("sha256")
    byte_count = value.get("bytes")
    mode = value.get("mode")
    return (
        type(path) is str
        and bool(path)
        and type(sha256) is str
        and _SHA256_RE.fullmatch(sha256) is not None
        and type(byte_count) is int
        and byte_count >= 0
        and type(mode) is int
        and 0 <= mode <= 0o777
    )


def _same_file_claim(actual: Mapping[str, Any], claimed: Mapping[str, Any]) -> bool:
    return (
        _exact_file_claim_shape(actual)
        and _exact_file_claim_shape(claimed)
        and all(
            _exact_json_value(actual[field], claimed[field])
            for field in ("sha256", "bytes", "mode")
        )
    )


def _stable_claim(path: Path) -> tuple[dict[str, Any], list[str]]:
    row, _payload, problems = stable_read(path, include_mode=True)
    return row, problems


def _canonical_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo != timezone.utc or parsed.isoformat().replace("+00:00", "Z") != value:
        return None
    return parsed


def _preparation_receipt_file_payload(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            indent=1,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _expected_h_forbidden_paths(
    install_root: Path,
    analytic_root: Path,
) -> dict[str, bool]:
    return {
        str(install_root): False,
        str(analytic_root): False,
        str(EXPECTED_SMOKE_ROOT): False,
        str(EXPECTED_UNIAD_ROOT / "i135-smoke-staging"): False,
        str(EXPECTED_UNIAD_ROOT / "dose_schedules.json"): False,
        str(EXPECTED_UNIAD_ROOT / "i135-decisions"): False,
        "/var/lib/sentinel/i135-smoke.lock": False,
        "/var/lib/sentinel/i135-analytic.lock": False,
        "/var/log/sentinel-i135.log": False,
    }


def _safe_sorted_relative_paths(value: object) -> bool:
    if type(value) is not list or any(type(path) is not str for path in value):
        return False
    if value != sorted(set(value)):
        return False
    for path in value:
        if (
            not path
            or path.startswith("/")
            or "\0" in path
            or any(part in {"", ".", ".."} for part in Path(path).parts)
            or path != "/".join(Path(path).parts)
        ):
            return False
    return True


def _exact_h_claim(
    value: object,
    *,
    path: Path,
    mode: int,
    sha256: str | None = None,
    byte_count: int | None = None,
) -> bool:
    if not _exact_file_claim_shape(value):
        return False
    claim = value
    return (
        claim.get("path") == str(path)
        and type(claim.get("mode")) is int
        and claim.get("mode") == mode
        and (sha256 is None or claim.get("sha256") == sha256)
        and (byte_count is None or claim.get("bytes") == byte_count)
    )


def _validate_h_repository_row(
    value: object,
    *,
    path: Path,
    head: str,
    dirty: list[str] | tuple[list[str], ...],
    untracked: list[str] | None = None,
    untracked_prefix: str | None = None,
) -> bool:
    if type(value) is not dict or set(value) != {
        "path",
        "head",
        "staged_paths",
        "dirty_tracked_paths",
        "untracked_paths",
    }:
        return False
    observed_dirty = value.get("dirty_tracked_paths")
    allowed_dirty = dirty if isinstance(dirty, tuple) else (dirty,)
    observed_untracked = value.get("untracked_paths")
    return (
        value.get("path") == str(path)
        and value.get("head") == head
        and _exact_json_value(value.get("staged_paths"), [])
        and any(
            _exact_json_value(observed_dirty, expected)
            for expected in allowed_dirty
        )
        and _safe_sorted_relative_paths(observed_untracked)
        and (
            untracked is None
            or _exact_json_value(observed_untracked, untracked)
        )
        and (
            untracked_prefix is None
            or all(
                item == untracked_prefix
                or item.startswith(f"{untracked_prefix}/")
                for item in observed_untracked
            )
        )
    )


def validate_host_preparation_evidence(
    host_preparation: object,
    *,
    install_root: Path | None = None,
    analytic_root: Path | None = None,
) -> list[str]:
    """Validate the complete green H document without observing host or output state.

    This is deliberately a pure JSON contract validator.  Test hooks may supply bytes, but they
    cannot select a smaller schema or bypass any semantic/type/cross-binding check.  Filesystem
    topology and installed-byte replay are separate admission requirements.
    """

    install_root = Path(HERE if install_root is None else install_root)
    analytic_root = Path(
        EXPECTED_ANALYTIC_ROOT if analytic_root is None else analytic_root
    )
    problems: list[str] = []
    if type(host_preparation) is not dict or set(host_preparation) != {
        "receipt_file",
        "evidence",
    }:
        return ["preparation:envelope-field-set"]
    receipt_file = host_preparation.get("receipt_file")
    receipt = host_preparation.get("evidence")
    if type(receipt) is not dict:
        return ["preparation:evidence-document"]
    expected_receipt_fields = {
        "schema",
        "verdict",
        "started_at_utc",
        "finished_at_utc",
        "host",
        "problem_count",
        "problems",
        "publication_authority",
        "packet_manifest_sha256",
        "packet",
        "controller",
        "repositories",
        "compose",
        "storage",
        "forbidden_paths",
        "actions",
        "invocation",
        "receipt_payload_sha256",
    }
    if set(receipt) != expected_receipt_fields:
        problems.append("preparation:field-set")
    try:
        payload = _preparation_receipt_file_payload(receipt)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return sorted({*problems, "preparation:serialization"})
    if (
        type(receipt_file) is not dict
        or set(receipt_file) != {"path", "sha256", "bytes"}
        or receipt_file.get("path") != str(CANONICAL_PREPARATION_RECEIPT_PATH)
        or receipt_file.get("sha256") != hashlib.sha256(payload).hexdigest()
        or type(receipt_file.get("bytes")) is not int
        or receipt_file.get("bytes") != len(payload)
    ):
        problems.append("preparation:receipt-file-binding")
    if receipt.get("schema") != EXPECTED_PREPARATION_SCHEMA:
        problems.append("preparation:schema")
    if receipt.get("verdict") != EXPECTED_PREPARATION_VERDICT:
        problems.append("preparation:verdict")
    if (
        type(receipt.get("problem_count")) is not int
        or receipt.get("problem_count") != 0
        or not _exact_json_value(receipt.get("problems"), [])
    ):
        problems.append("preparation:problem-metadata")
    if receipt.get("host") != EXPECTED_HOST:
        problems.append("preparation:host")
    started = _canonical_utc(receipt.get("started_at_utc"))
    finished = _canonical_utc(receipt.get("finished_at_utc"))
    if started is None or finished is None or started > finished:
        problems.append("preparation:timestamps")
    claimed_payload_sha = receipt.get("receipt_payload_sha256")
    hash_payload = dict(receipt)
    hash_payload.pop("receipt_payload_sha256", None)
    try:
        actual_payload_sha = hashlib.sha256(
            _canonical_json_bytes(hash_payload)
        ).hexdigest()
    except (TypeError, ValueError, OverflowError, RecursionError):
        actual_payload_sha = None
    if (
        type(claimed_payload_sha) is not str
        or claimed_payload_sha != actual_payload_sha
    ):
        problems.append("preparation:receipt-payload-sha256")

    packet = receipt.get("packet")
    manifest_sha = receipt.get("packet_manifest_sha256")
    if type(manifest_sha) is not str or _SHA256_RE.fullmatch(manifest_sha) is None:
        problems.append("preparation:packet-manifest-sha256")
    if type(packet) is not dict or set(packet) != {
        "schema",
        "source_commit",
        "manifest",
        "independently_supplied_manifest_sha256",
        "files",
    }:
        problems.append("preparation:packet")
        packet = {}
    source_commit = packet.get("source_commit")
    if packet.get("schema") != EXPECTED_PACKET_SCHEMA:
        problems.append("preparation:packet-schema")
    if type(source_commit) is not str or _COMMIT_RE.fullmatch(source_commit) is None:
        problems.append("preparation:packet-source-commit")
    if packet.get("independently_supplied_manifest_sha256") != manifest_sha:
        problems.append("preparation:packet-independent-sha256")
    if not _exact_h_claim(
        packet.get("manifest"),
        path=EXPECTED_PACKET_STAGING_ROOT / "host_packet_manifest.json",
        mode=0o644,
        sha256=manifest_sha if type(manifest_sha) is str else None,
    ):
        problems.append("preparation:packet-manifest-claim")
    files = packet.get("files")
    if type(files) is not dict or set(files) != EXPECTED_PREPARATION_PACKET_FILES:
        problems.append("preparation:packet-file-set")
        files = {}
    for name in EXPECTED_PREPARATION_PACKET_FILES:
        if not _exact_h_claim(
            files.get(name),
            path=EXPECTED_PACKET_STAGING_ROOT / name,
            mode=EXPECTED_PREPARATION_PACKET_MODES[name],
        ):
            problems.append(f"preparation:packet-file:{name}:claim")

    controller = receipt.get("controller")
    if (
        type(files.get("prepare_host135.py")) is not dict
        or not _exact_json_value(controller, files.get("prepare_host135.py"))
    ):
        problems.append("preparation:controller-binding")

    compose = receipt.get("compose")
    compose_path = EXPECTED_NEURONCAP_ROOT / "scripts/_docker_compose_release.sh"
    if type(compose) is not dict or set(compose) != {"patcher", "before", "after"}:
        problems.append("preparation:compose-field-set")
        compose = {}
    if (
        type(files.get("patch_compose_dose_env.py")) is not dict
        or not _exact_json_value(
            compose.get("patcher"),
            files.get("patch_compose_dose_env.py"),
        )
    ):
        problems.append("preparation:compose-patcher-binding")
    if not _exact_h_claim(
        compose.get("before"),
        path=compose_path,
        mode=0o755,
        sha256=EXPECTED_COMPOSE_INPUT_SHA256,
        byte_count=EXPECTED_COMPOSE_INPUT_BYTES,
    ):
        problems.append("preparation:compose-before")
    if not _exact_h_claim(
        compose.get("after"),
        path=compose_path,
        mode=0o755,
        sha256=EXPECTED_COMPOSE_OUTPUT_SHA256,
        byte_count=EXPECTED_COMPOSE_OUTPUT_BYTES,
    ):
        problems.append("preparation:compose-after")

    repositories = receipt.get("repositories")
    if type(repositories) is not dict or set(repositories) != {"before", "after"}:
        problems.append("preparation:repositories-field-set")
        repositories = {}
    before_repositories = repositories.get("before")
    after_repositories = repositories.get("after")
    if (
        type(before_repositories) is not dict
        or set(before_repositories) != {"uniad", "neuroncap", "neurad"}
        or type(after_repositories) is not dict
        or set(after_repositories) != {"uniad", "neuroncap", "neurad"}
    ):
        problems.append("preparation:repository-phase-set")
        before_repositories = {}
        after_repositories = {}
    uniad_after_dirty = [
        "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"
    ]
    uniad_before_dirty = (
        [
            "inference/server.py",
            "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
        ],
        uniad_after_dirty,
    )
    for phase, rows in (
        ("before", before_repositories),
        ("after", after_repositories),
    ):
        if not _validate_h_repository_row(
            rows.get("uniad"),
            path=EXPECTED_UNIAD_ROOT,
            head=EXPECTED_UNIAD_HEAD,
            dirty=(
                uniad_before_dirty
                if phase == "before"
                else uniad_after_dirty
            ),
            untracked=["checkpoints"],
        ):
            problems.append(f"preparation:repository:{phase}:uniad")
        if not _validate_h_repository_row(
            rows.get("neuroncap"),
            path=EXPECTED_NEURONCAP_ROOT,
            head=EXPECTED_NEURONCAP_HEAD,
            dirty=[
                "docker/Dockerfile",
                "scripts/_docker_compose_release.sh",
            ],
            untracked_prefix="outoutput",
        ):
            problems.append(f"preparation:repository:{phase}:neuroncap")
        if not _validate_h_repository_row(
            rows.get("neurad"),
            path=EXPECTED_NEURAD_ROOT,
            head=EXPECTED_NEURAD_HEAD,
            dirty=["Dockerfile"],
            untracked=["Dockerfile.bak"],
        ):
            problems.append(f"preparation:repository:{phase}:neurad")
    if (
        type(before_repositories) is dict
        and type(after_repositories) is dict
        and any(
            not _exact_json_value(
                before_repositories.get(role, {}).get("untracked_paths"),
                after_repositories.get(role, {}).get("untracked_paths"),
            )
            for role in ("uniad", "neuroncap", "neurad")
            if type(before_repositories.get(role)) is dict
            and type(after_repositories.get(role)) is dict
        )
    ):
        problems.append("preparation:repository-untracked-race")

    actions = receipt.get("actions")
    if type(actions) is not list or len(actions) != 4:
        problems.append("preparation:actions-count")
        actions = [{}, {}, {}, {}]
    expected_action_shapes = (
        {
            "action",
            "performed",
            "before",
            "after",
        },
        {
            "action",
            "performed",
            "before_sha256",
            "after_sha256",
        },
        {"action", "performed", "path"},
        {"action", "performed", "from", "to"},
    )
    if any(
        type(row) is not dict or set(row) != shape
        for row, shape in zip(actions, expected_action_shapes, strict=True)
    ):
        problems.append("preparation:actions-field-set")
        actions = [
            row if type(row) is dict else {}
            for row in actions
        ]
    action_names = [
        "normalize_uniad_server_from_verified_head_blob",
        "atomically_patch_compose_from_exact_preimage",
        "create_absent_empty_analytic_root",
        "atomically_install_verified_packet",
    ]
    if [
        row.get("action") if type(row) is dict else None
        for row in actions
    ] != action_names:
        problems.append("preparation:actions-order")
    first_action = actions[0]
    performed = first_action.get("performed")
    before_server = first_action.get("before")
    after_server = first_action.get("after")
    server_path = EXPECTED_UNIAD_ROOT / "inference/server.py"
    if type(performed) is not bool:
        problems.append("preparation:action-server-performed")
    if not _exact_h_claim(before_server, path=server_path, mode=0o644):
        problems.append("preparation:action-server-before")
    if not _exact_h_claim(
        after_server,
        path=server_path,
        mode=0o644,
        sha256=EXPECTED_UNIAD_SERVER_SHA256,
        byte_count=EXPECTED_UNIAD_SERVER_BYTES,
    ):
        problems.append("preparation:action-server-after")
    observed_before_dirty = (
        before_repositories.get("uniad", {}).get("dirty_tracked_paths")
        if type(before_repositories.get("uniad")) is dict
        else None
    )
    if type(performed) is bool and (
        (performed is False and not _exact_json_value(before_server, after_server))
        or (
            performed is True
            and _exact_json_value(before_server, after_server)
        )
        or (
            performed
            != (
                observed_before_dirty
                == [
                    "inference/server.py",
                    "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
                ]
            )
        )
    ):
        problems.append("preparation:action-server-cross-binding")
    if (
        actions[1].get("performed") is not True
        or actions[1].get("before_sha256") != EXPECTED_COMPOSE_INPUT_SHA256
        or actions[1].get("after_sha256") != EXPECTED_COMPOSE_OUTPUT_SHA256
    ):
        problems.append("preparation:action-compose")
    if (
        actions[2].get("performed") is not True
        or actions[2].get("path") != str(analytic_root)
    ):
        problems.append("preparation:action-analytic-root")
    if (
        actions[3].get("performed") is not True
        or actions[3].get("from") != str(EXPECTED_PACKET_STAGING_ROOT)
        or actions[3].get("to") != str(install_root)
    ):
        problems.append("preparation:action-packet-install")

    storage = receipt.get("storage")
    storage_fields = {
        "mount_target",
        "mount_source",
        "mount_fstype",
        "mount_uuid",
        "dataset_st_dev",
        "root_st_dev",
        "free_bytes_before",
        "minimum_remote_free_bytes",
        "projected_output_bytes",
        "minimum_reserve_bytes",
        "analytic_root",
        "analytic_root_realpath",
        "analytic_root_is_symlink",
        "analytic_root_empty",
        "analytic_root_st_dev",
        "free_bytes_after",
    }
    if type(storage) is not dict or set(storage) != storage_fields:
        problems.append("preparation:storage-field-set")
        storage = {}
    integer_fields = (
        "dataset_st_dev",
        "root_st_dev",
        "free_bytes_before",
        "minimum_remote_free_bytes",
        "projected_output_bytes",
        "minimum_reserve_bytes",
        "analytic_root_st_dev",
        "free_bytes_after",
    )
    if any(type(storage.get(field)) is not int for field in integer_fields):
        problems.append("preparation:storage-integer-types")
    expected_mount = {
        **EXPECTED_H_MOUNT,
        "minimum_remote_free_bytes": EXPECTED_H_MINIMUM_REMOTE_FREE_BYTES,
        "projected_output_bytes": EXPECTED_H_PROJECTED_OUTPUT_BYTES,
        "minimum_reserve_bytes": EXPECTED_H_MINIMUM_RESERVE_BYTES,
        "analytic_root": str(analytic_root),
        "analytic_root_realpath": str(analytic_root),
        "analytic_root_is_symlink": False,
        "analytic_root_empty": True,
    }
    if any(
        not _exact_json_value(storage.get(field), expected)
        for field, expected in expected_mount.items()
    ):
        problems.append("preparation:storage-contract")
    device_fields = (
        "dataset_st_dev",
        "root_st_dev",
        "analytic_root_st_dev",
    )
    if all(type(storage.get(field)) is int for field in device_fields) and any(
        storage[field] < 0 for field in device_fields
    ):
        problems.append("preparation:storage-device-values")
    if all(type(storage.get(field)) is int for field in integer_fields):
        dataset_device = storage["dataset_st_dev"]
        root_device = storage["root_st_dev"]
        if (
            dataset_device == root_device
            or storage["analytic_root_st_dev"] != dataset_device
            or storage["free_bytes_before"]
            < storage["minimum_remote_free_bytes"]
            or storage["free_bytes_after"]
            < storage["minimum_remote_free_bytes"]
            or storage["free_bytes_before"]
            - storage["projected_output_bytes"]
            < storage["minimum_reserve_bytes"]
            or storage["free_bytes_after"]
            - storage["projected_output_bytes"]
            < storage["minimum_reserve_bytes"]
        ):
            problems.append("preparation:storage-cross-binding")

    if not _exact_json_value(
        receipt.get("forbidden_paths"),
        _expected_h_forbidden_paths(install_root, analytic_root),
    ):
        problems.append("preparation:forbidden-paths")

    invocation = receipt.get("invocation")
    if (
        type(invocation) is not dict
        or set(invocation)
        != {
            "environment",
            "environment_matches",
            "isolated",
            "python_implementation",
            "python_version",
        }
        or not _exact_json_value(
            invocation.get("environment"),
            PREPARATION_SANITIZED_ENVIRONMENT,
        )
        or invocation.get("environment_matches") is not True
        or invocation.get("isolated") is not True
        or invocation.get("python_implementation") != "CPython"
        or type(invocation.get("python_version")) is not str
        or _PYTHON_VERSION_RE.fullmatch(invocation["python_version"]) is None
    ):
        problems.append("preparation:invocation")

    authority = receipt.get("publication_authority")
    artifacts: list[dict[str, Any]] = []
    authority_artifacts = (
        authority.get("artifacts") if type(authority) is dict else None
    )
    artifacts_by_path = (
        {
            row.get("path"): row
            for row in authority_artifacts
            if type(row) is dict and type(row.get("path")) is str
        }
        if type(authority_artifacts) is list
        else {}
    )
    for name in EXPECTED_PREPARATION_PACKET_FILES:
        claim = files.get(name)
        repository_path = _packet_repository_path(name)
        authority_row = artifacts_by_path.get(repository_path)
        expected_git_mode = (
            "100755"
            if EXPECTED_PREPARATION_PACKET_MODES[name] == 0o755
            else "100644"
        )
        if (
            type(claim) is not dict
            or type(authority_row) is not dict
            or set(authority_row)
            != {
                "path",
                "sha256",
                "bytes",
                "git_blob_oid",
                "git_mode",
            }
            or authority_row.get("sha256") != claim.get("sha256")
            or not _exact_json_value(
                authority_row.get("bytes"),
                claim.get("bytes"),
            )
            or type(authority_row.get("git_blob_oid")) is not str
            or re.fullmatch(
                r"[0-9a-f]{40}",
                authority_row["git_blob_oid"],
            )
            is None
            or authority_row.get("git_mode") != expected_git_mode
        ):
            problems.append(
                f"preparation:publication-artifact:{name}"
            )
            continue
        artifacts.append(dict(authority_row))
    artifacts.sort(key=lambda row: row["path"])
    problems.extend(
        _publication_authority_problems(
            authority,
            source_commit=source_commit,
            artifacts=artifacts,
            label="preparation:publication-authority",
        )
    )
    return sorted(set(problems))


@dataclass(frozen=True)
class _ReceiptPairObservation:
    parent_identity: tuple[int, int, int]
    receipt_inode: tuple[int, int]
    byte_count: int
    payload_sha256: str


def _read_exact_receipt_descriptor(
    descriptor: int,
    expected: bytes,
    *,
    problem: str,
) -> None:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        observed = bytearray()
        while len(observed) <= len(expected):
            chunk = os.read(
                descriptor,
                min(1 << 20, len(expected) + 1 - len(observed)),
            )
            if not chunk:
                break
            observed.extend(chunk)
    except OSError as error:
        raise CaptureError(problem) from error
    if bytes(observed) != expected:
        raise CaptureError(problem)


def _observe_receipt_pair(
    canonical_path: Path,
    *,
    pending_basename: str,
    marker_basename: str,
    payload: bytes,
    problem_prefix: str,
) -> _ReceiptPairObservation:
    """Replay one disk-committed canonical+pending pair under one held parent.

    This proves only the exact filesystem state observed during this call.  It cannot prove that
    the producing process returned, and no POSIX observation prevents a later writer with parent
    directory authority from mutating the names after the observation.
    """

    canonical_path = Path(canonical_path)
    parent_path = canonical_path.parent
    parent_fd = _open_physical_directory(parent_path)
    descriptors: list[int] = []
    try:
        parent_identity = _directory_identity(parent_fd)
        try:
            os.stat(
                marker_basename,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        except OSError as error:
            raise CaptureError(f"{problem_prefix}:marker-probe") from error
        else:
            raise CaptureError(f"{problem_prefix}:marker-present")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        rows: list[os.stat_result] = []
        for basename in (pending_basename, canonical_path.name):
            try:
                descriptor = os.open(basename, flags, dir_fd=parent_fd)
            except OSError as error:
                raise CaptureError(f"{problem_prefix}:pair-open") from error
            descriptors.append(descriptor)
            before = os.fstat(descriptor)
            named = os.stat(
                basename,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(before.st_mode)
                or not stat.S_ISREG(named.st_mode)
                or (before.st_dev, before.st_ino)
                != (named.st_dev, named.st_ino)
                or before.st_dev != parent_identity[0]
                or stat.S_IMODE(before.st_mode) != 0o444
                or stat.S_IMODE(named.st_mode) != 0o444
                or before.st_nlink != 2
                or named.st_nlink != 2
                or before.st_size != len(payload)
                or named.st_size != len(payload)
            ):
                raise CaptureError(f"{problem_prefix}:pair-identity")
            _read_exact_receipt_descriptor(
                descriptor,
                payload,
                problem=f"{problem_prefix}:pair-content",
            )
            after = os.fstat(descriptor)
            if (
                (after.st_dev, after.st_ino, after.st_mode, after.st_size)
                != (
                    before.st_dev,
                    before.st_ino,
                    before.st_mode,
                    before.st_size,
                )
                or after.st_nlink != 2
            ):
                raise CaptureError(f"{problem_prefix}:pair-drift")
            rows.append(after)
        if (rows[0].st_dev, rows[0].st_ino) != (
            rows[1].st_dev,
            rows[1].st_ino,
        ):
            raise CaptureError(f"{problem_prefix}:pair-inode")
        replay_fd = _open_physical_directory(parent_path)
        try:
            if _directory_identity(replay_fd) != parent_identity:
                raise CaptureError(f"{problem_prefix}:parent-drift")
            for basename, expected_row in zip(
                (pending_basename, canonical_path.name),
                rows,
                strict=True,
            ):
                terminal = os.stat(
                    basename,
                    dir_fd=replay_fd,
                    follow_symlinks=False,
                )
                if (
                    (
                        terminal.st_dev,
                        terminal.st_ino,
                        terminal.st_mode,
                        terminal.st_size,
                    )
                    != (
                        expected_row.st_dev,
                        expected_row.st_ino,
                        expected_row.st_mode,
                        expected_row.st_size,
                    )
                    or terminal.st_nlink != 2
                ):
                    raise CaptureError(f"{problem_prefix}:pair-drift")
            try:
                os.stat(
                    marker_basename,
                    dir_fd=replay_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            except OSError as error:
                raise CaptureError(f"{problem_prefix}:marker-probe") from error
            else:
                raise CaptureError(f"{problem_prefix}:marker-present")
        finally:
            os.close(replay_fd)
        return _ReceiptPairObservation(
            parent_identity=parent_identity,
            receipt_inode=(rows[0].st_dev, rows[0].st_ino),
            byte_count=len(payload),
            payload_sha256=hashlib.sha256(payload).hexdigest(),
        )
    except CaptureError:
        raise
    except OSError as error:
        raise CaptureError(f"{problem_prefix}:pair-replay") from error
    finally:
        for descriptor in descriptors:
            try:
                os.close(descriptor)
            except OSError:
                pass
        os.close(parent_fd)


def load_and_validate_preparation_receipt(
    receipt_path: Path | None = None,
    *,
    install_root: Path | None = None,
    controller_path: Path | None = None,
    packet_manifest_path: Path | None = None,
    analytic_root: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Load and independently replay the one-shot host-preparation receipt."""

    receipt_path = Path(
        CANONICAL_PREPARATION_RECEIPT_PATH
        if receipt_path is None
        else receipt_path
    )
    install_root = Path(HERE if install_root is None else install_root)
    controller_path = Path(
        CANONICAL_PREPARER_PATH if controller_path is None else controller_path
    )
    packet_manifest_path = Path(
        CANONICAL_PACKET_MANIFEST_PATH
        if packet_manifest_path is None
        else packet_manifest_path
    )
    analytic_root = Path(
        EXPECTED_ANALYTIC_ROOT if analytic_root is None else analytic_root
    )
    problems: list[str] = []
    receipt_file, payload, file_problems = stable_read(receipt_path, collect_bytes=True)
    problems.extend(f"preparation:receipt:{item}" for item in file_problems)
    if payload is None:
        return {"receipt_file": receipt_file, "evidence": None}, sorted(set(problems))
    try:
        receipt = json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        problems.append(f"preparation:receipt-json:{type(error).__name__}")
        return {"receipt_file": receipt_file, "evidence": None}, sorted(set(problems))
    envelope = {"receipt_file": receipt_file, "evidence": receipt}
    problems.extend(
        validate_host_preparation_evidence(
            envelope,
            install_root=install_root,
            analytic_root=analytic_root,
        )
    )
    expected_fields = {
        "schema",
        "verdict",
        "started_at_utc",
        "finished_at_utc",
        "host",
        "problem_count",
        "problems",
        "publication_authority",
        "packet_manifest_sha256",
        "packet",
        "controller",
        "repositories",
        "compose",
        "storage",
        "forbidden_paths",
        "actions",
        "invocation",
        "receipt_payload_sha256",
    }
    if type(receipt) is not dict or set(receipt) != expected_fields:
        problems.append("preparation:field-set")
        receipt = receipt if type(receipt) is dict else {}
    if receipt.get("schema") != EXPECTED_PREPARATION_SCHEMA:
        problems.append("preparation:schema")
    if receipt.get("verdict") != EXPECTED_PREPARATION_VERDICT:
        problems.append("preparation:verdict")
    if (
        type(receipt.get("problem_count")) is not int
        or receipt.get("problem_count") != 0
        or receipt.get("problems") != []
    ):
        problems.append("preparation:problem-metadata")
    if receipt.get("host") != EXPECTED_HOST:
        problems.append("preparation:host")
    started = _canonical_utc(receipt.get("started_at_utc"))
    finished = _canonical_utc(receipt.get("finished_at_utc"))
    if started is None or finished is None or started > finished:
        problems.append("preparation:timestamps")
    claimed_payload_sha = receipt.get("receipt_payload_sha256")
    hash_payload = dict(receipt)
    hash_payload.pop("receipt_payload_sha256", None)
    if claimed_payload_sha != hashlib.sha256(_canonical_json_bytes(hash_payload)).hexdigest():
        problems.append("preparation:receipt-payload-sha256")

    packet = receipt.get("packet")
    manifest_sha = receipt.get("packet_manifest_sha256")
    if not isinstance(manifest_sha, str) or not _SHA256_RE.fullmatch(manifest_sha):
        problems.append("preparation:packet-manifest-sha256")
    if type(packet) is not dict or set(packet) != {
        "schema",
        "source_commit",
        "manifest",
        "independently_supplied_manifest_sha256",
        "files",
    }:
        problems.append("preparation:packet")
        packet = {}
    if packet.get("schema") != EXPECTED_PACKET_SCHEMA:
        problems.append("preparation:packet-schema")
    if not isinstance(packet.get("source_commit"), str) or not re.fullmatch(
        r"[0-9a-f]{40}", packet["source_commit"]
    ):
        problems.append("preparation:packet-source-commit")
    if packet.get("independently_supplied_manifest_sha256") != manifest_sha:
        problems.append("preparation:packet-independent-sha256")
    manifest_claim = packet.get("manifest")
    manifest_actual, manifest_payload, raw_manifest_problems = stable_read(
        packet_manifest_path,
        collect_bytes=True,
        include_mode=True,
    )
    manifest_problems = list(raw_manifest_problems)
    problems.extend(f"preparation:packet-manifest:{item}" for item in manifest_problems)
    if (
        type(manifest_claim) is not dict
        or not _same_file_claim(manifest_actual, manifest_claim)
        or manifest_actual.get("sha256") != manifest_sha
    ):
        problems.append("preparation:packet-manifest-binding")

    files = packet.get("files")
    if type(files) is not dict or set(files) != EXPECTED_PREPARATION_PACKET_FILES:
        problems.append("preparation:packet-file-set")
        files = {}
    preparation_artifacts: list[dict[str, Any]] = []
    for name in EXPECTED_PREPARATION_PACKET_FILES:
        claim = files.get(name)
        installed_path = install_root / name
        actual, installed_payload, item_problems = stable_read(
            installed_path,
            collect_bytes=True,
            include_mode=True,
        )
        problems.extend(
            f"preparation:packet-file:{name}:{item}" for item in item_problems
        )
        if (
            actual.get("path") != str(installed_path)
            or type(claim) is not dict
            or not _same_file_claim(actual, claim)
        ):
            problems.append(f"preparation:packet-file:{name}:binding")
        git_mode = {
            0o644: "100644",
            0o755: "100755",
        }.get(actual.get("mode"))
        preparation_artifacts.append(
            {
                "path": _packet_repository_path(name),
                "sha256": actual.get("sha256"),
                "bytes": actual.get("bytes"),
                "git_blob_oid": (
                    _git_blob_oid(installed_payload)
                    if isinstance(installed_payload, bytes)
                    else None
                ),
                "git_mode": git_mode,
            }
        )
    preparation_artifacts.sort(key=lambda row: row["path"])
    problems.extend(
        _publication_authority_problems(
            receipt.get("publication_authority"),
            source_commit=packet.get("source_commit"),
            artifacts=preparation_artifacts,
            label="preparation:publication-authority",
        )
    )
    manifest_document = None
    if manifest_payload is not None:
        try:
            manifest_document = json.loads(
                manifest_payload,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_nonfinite_json,
            )
        except (UnicodeDecodeError, ValueError) as error:
            problems.append(
                f"preparation:packet-manifest-json:{type(error).__name__}"
            )
    expected_manifest_files = {
        name: {
            "sha256": claim.get("sha256"),
            "bytes": claim.get("bytes"),
            "mode": claim.get("mode"),
        }
        for name, claim in files.items()
        if type(name) is str and type(claim) is dict
    }
    if (
        type(manifest_document) is not dict
        or set(manifest_document) != {"schema", "source_commit", "files"}
        or manifest_document.get("schema") != EXPECTED_PACKET_SCHEMA
        or manifest_document.get("source_commit") != packet.get("source_commit")
        or not _exact_json_value(
            manifest_document.get("files"),
            expected_manifest_files,
        )
    ):
        problems.append("preparation:packet-manifest-replay")

    controller_claim = receipt.get("controller")
    controller_actual, controller_problems = _stable_claim(controller_path)
    problems.extend(f"preparation:controller:{item}" for item in controller_problems)
    if (
        controller_actual.get("path") != str(controller_path)
        or
        type(controller_claim) is not dict
        or not _same_file_claim(controller_actual, controller_claim)
        or type(files.get("prepare_host135.py")) is not dict
        or not _same_file_claim(controller_actual, files["prepare_host135.py"])
    ):
        problems.append("preparation:controller-binding")

    actions = receipt.get("actions")
    expected_actions = [
        "normalize_uniad_server_from_verified_head_blob",
        "atomically_patch_compose_from_exact_preimage",
        "create_absent_empty_analytic_root",
        "atomically_install_verified_packet",
    ]
    if (
        not isinstance(actions, list)
        or [row.get("action") if isinstance(row, dict) else None for row in actions]
        != expected_actions
        or any(row.get("performed") is not True for row in actions[1:] if isinstance(row, dict))
    ):
        problems.append("preparation:actions")
    forbidden_paths = receipt.get("forbidden_paths")
    if (
        not isinstance(forbidden_paths, dict)
        or not forbidden_paths
        or any(value is not False for value in forbidden_paths.values())
    ):
        problems.append("preparation:forbidden-paths")
    elif not {str(install_root), str(analytic_root)}.issubset(forbidden_paths):
        problems.append("preparation:forbidden-path-set")
    else:
        expected_present = {str(install_root), str(analytic_root)}
        for path_text in forbidden_paths:
            if os.path.lexists(path_text) != (path_text in expected_present):
                problems.append(f"preparation:forbidden-path-drift:{path_text}")
    invocation = receipt.get("invocation")
    if (
        not isinstance(invocation, dict)
        or set(invocation)
        != {
            "environment",
            "environment_matches",
            "isolated",
            "python_implementation",
            "python_version",
        }
        or invocation.get("environment") != PREPARATION_SANITIZED_ENVIRONMENT
        or invocation.get("environment_matches") is not True
        or invocation.get("isolated") is not True
        or invocation.get("python_implementation") != "CPython"
        or not isinstance(invocation.get("python_version"), str)
        or not _PYTHON_VERSION_RE.fullmatch(invocation["python_version"])
    ):
        problems.append("preparation:invocation")
    repositories = receipt.get("repositories")
    if (
        not isinstance(repositories, dict)
        or set(repositories) != {"before", "after"}
        or any(
            not isinstance(repositories.get(phase), dict)
            or set(repositories[phase]) != {"uniad", "neuroncap", "neurad"}
            for phase in ("before", "after")
        )
    ):
        problems.append("preparation:repositories")
    if not isinstance(receipt.get("compose"), dict):
        problems.append("preparation:compose")
    storage = receipt.get("storage")
    if (
        not isinstance(storage, dict)
        or storage.get("analytic_root") != str(analytic_root)
        or storage.get("analytic_root_realpath") != str(analytic_root)
        or storage.get("analytic_root_is_symlink") is not False
        or storage.get("analytic_root_empty") is not True
    ):
        problems.append("preparation:storage")
    try:
        resolved_install = Path(install_root).resolve(strict=True)
    except (OSError, RuntimeError):
        resolved_install = None
    if resolved_install != Path(install_root):
        problems.append("preparation:install-root")
    try:
        analytic_info = analytic_root.lstat()
        analytic_resolved = analytic_root.resolve(strict=True)
        analytic_entries = list(analytic_root.iterdir())
    except (OSError, RuntimeError) as error:
        problems.append(
            f"preparation:analytic-root:{type(error).__name__}"
        )
    else:
        if (
            not stat.S_ISDIR(analytic_info.st_mode)
            or stat.S_ISLNK(analytic_info.st_mode)
            or analytic_resolved != analytic_root
            or analytic_entries
            or type(storage) is not dict
            or type(storage.get("analytic_root_st_dev")) is not int
            or analytic_info.st_dev != storage.get("analytic_root_st_dev")
        ):
            problems.append("preparation:analytic-root")
    try:
        _observe_receipt_pair(
            receipt_path,
            pending_basename=EXPECTED_H_PENDING_BASENAME,
            marker_basename=EXPECTED_H_ATTEMPT_BASENAME,
            payload=payload,
            problem_prefix="preparation:receipt-topology",
        )
    except CaptureError as error:
        problems.append(str(error))
    return envelope, sorted(set(problems))


def _read_dataset_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    receipt, _data, problems = stable_read(path)
    return receipt, problems


def _load_module_from_stable_bytes(
    path: Path,
    module_name: str,
    *,
    expected_claim: Mapping[str, Any] | None = None,
    expected_parent_identity: tuple[int, int, int] | None = None,
) -> types.ModuleType:
    parent_fd = -1
    if expected_parent_identity is not None:
        try:
            parent_fd = _open_physical_directory(path.parent)
            if _directory_identity(parent_fd) != expected_parent_identity:
                raise CaptureError("canonical-source:parent-drift")
        except CaptureError:
            if parent_fd >= 0:
                os.close(parent_fd)
            raise
    receipt, source, problems = stable_read(
        path,
        collect_bytes=True,
        include_mode=True,
    )
    if parent_fd >= 0:
        try:
            if _directory_identity(parent_fd) != expected_parent_identity:
                raise CaptureError("canonical-source:parent-drift")
            replay_fd = _open_physical_directory(path.parent)
            try:
                if _directory_identity(replay_fd) != expected_parent_identity:
                    raise CaptureError("canonical-source:parent-drift")
            finally:
                os.close(replay_fd)
        finally:
            os.close(parent_fd)
    if problems or source is None:
        raise CaptureError(f"canonical-source:{path.name}:{','.join(problems)}")
    if expected_claim is not None and (
        not _exact_file_claim_shape(expected_claim)
        or not _same_file_claim(receipt, expected_claim)
    ):
        raise CaptureError("canonical-source:host-binding")
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _exact_contract_string(value: object) -> str:
    if type(value) is not str:
        raise CaptureError("canonical-manifest:contract-types")
    return value


def _exact_contract_integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise CaptureError("canonical-manifest:contract-types")
    return value


def _exact_contract_string_tuple(value: object) -> tuple[str, ...]:
    if (
        type(value) is not tuple
        or any(type(item) is not str for item in value)
    ):
        raise CaptureError("canonical-manifest:contract-types")
    return value


def _dataset_contract_from_module(module: types.ModuleType) -> dict[str, Any]:
    raw_archives = module.EXPECTED_DATASET_ARCHIVES
    if type(raw_archives) is not dict:
        raise CaptureError("canonical-manifest:contract-types")
    archives: dict[str, dict[str, Any]] = {}
    for name, row in sorted(raw_archives.items()):
        if (
            type(name) is not str
            or type(row) is not tuple
            or len(row) != 2
        ):
            raise CaptureError("canonical-manifest:contract-types")
        archives[name] = {
            "sha256": _exact_contract_string(row[0]),
            "bytes": _exact_contract_integer(row[1]),
        }
    mount = module.EXPECTED_DATASET_MOUNT
    if (
        type(mount) is not dict
        or any(
            type(key) is not str or type(value) is not str
            for key, value in mount.items()
        )
    ):
        raise CaptureError("canonical-manifest:contract-types")
    proof_basis = module.EXPECTED_DATASET_PROOF_BASIS
    if (
        type(proof_basis) is not dict
        or set(proof_basis)
        != {
            "iteration",
            "result_path",
            "receipt_directory",
            "archive_count",
            "archive_total_bytes",
            "map_expansion_result_path",
        }
        or any(
            type(proof_basis[field]) is not int
            for field in ("iteration", "archive_count", "archive_total_bytes")
        )
        or any(
            type(proof_basis[field]) is not str
            for field in (
                "result_path",
                "receipt_directory",
                "map_expansion_result_path",
            )
        )
    ):
        raise CaptureError("canonical-manifest:contract-types")
    metadata_files = _exact_contract_string_tuple(
        module.EXPECTED_DATASET_METADATA_FILES
    )
    map_anchors = _exact_contract_string_tuple(
        module.EXPECTED_DATASET_MAP_ANCHORS
    )
    raw_map_directories = module.EXPECTED_DATASET_MAP_DIRECTORIES
    if type(raw_map_directories) is not dict:
        raise CaptureError("canonical-manifest:contract-types")
    map_directories: dict[str, list[str]] = {}
    for name, files in sorted(raw_map_directories.items()):
        if type(name) is not str:
            raise CaptureError("canonical-manifest:contract-types")
        map_directories[name] = list(_exact_contract_string_tuple(files))
    return {
        "schema": _exact_contract_string(module.EXPECTED_DATASET_SCHEMA),
        "dataset_root": _exact_contract_string(module.EXPECTED_DATASET_ROOT),
        "dataset_version": _exact_contract_string(
            module.EXPECTED_DATASET_VERSION
        ),
        "archive_root": _exact_contract_string(
            module.EXPECTED_DATASET_ARCHIVE_ROOT
        ),
        "metadata_root": _exact_contract_string(
            module.EXPECTED_DATASET_METADATA_ROOT
        ),
        "map_root": _exact_contract_string(module.EXPECTED_DATASET_MAP_ROOT),
        "mount": dict(mount),
        "proof_basis": dict(proof_basis),
        "archives": archives,
        "metadata_json_names": list(metadata_files),
        "map_anchor_names": list(map_anchors),
        "map_directory_names": map_directories,
    }


def load_contract(
    path: Path = CANONICAL_MANIFEST_PATH,
    *,
    expected_claim: Mapping[str, Any] | None = None,
    expected_parent_identity: tuple[int, int, int] | None = None,
) -> Contract:
    """Load only the canonical sibling manifest and reject an incomplete role topology."""

    path = Path(path)
    if path != CANONICAL_MANIFEST_PATH:
        expected_parent = CANONICAL_MANIFEST_PATH.parent
        if path.parent.resolve(strict=True) != expected_parent:
            raise CaptureError("canonical-manifest:outside-iter135")
    module = _load_module_from_stable_bytes(
        path,
        "iter135_environment_contract",
        expected_claim=expected_claim,
        expected_parent_identity=expected_parent_identity,
    )
    environment_schema = _exact_contract_string(module.EXPECTED_ENV_SCHEMA)
    ready_verdict = _exact_contract_string(module.EXPECTED_ENV_VERDICT)
    if environment_schema != EXPECTED_ENVIRONMENT_SCHEMA:
        raise CaptureError("canonical-manifest:environment-schema")
    if ready_verdict != "I135_ENVIRONMENT_PREFLIGHT_OK":
        raise CaptureError("canonical-manifest:environment-verdict")
    raw_remote_files = module.EXPECTED_REMOTE_FILES
    if type(raw_remote_files) is not dict:
        raise CaptureError("canonical-manifest:contract-types")
    remote_files: dict[str, tuple[str, str, int]] = {}
    for role, row in raw_remote_files.items():
        if (
            type(role) is not str
            or type(row) is not tuple
            or len(row) != 3
        ):
            raise CaptureError("canonical-manifest:contract-types")
        remote_files[role] = (
            _exact_contract_string(row[0]),
            _exact_contract_string(row[1]),
            _exact_contract_integer(row[2]),
        )
    if (
        len(remote_files) != 82
        or sum(role.startswith("scenario:") for role in remote_files) != 20
        or sum(role.startswith("renderer:") for role in remote_files) != 42
    ):
        raise CaptureError("canonical-manifest:remote-role-topology")
    raw_repositories = module.EXPECTED_REPOSITORIES
    repository_fields = {
        "path",
        "head",
        "staged_paths",
        "dirty_tracked_paths",
        "required_untracked_paths",
    }
    if type(raw_repositories) is not dict:
        raise CaptureError("canonical-manifest:contract-types")
    repositories: dict[str, dict[str, Any]] = {}
    for repo_id, repository in raw_repositories.items():
        if (
            type(repo_id) is not str
            or type(repository) is not dict
            or set(repository) != repository_fields
            or type(repository.get("path")) is not str
            or type(repository.get("head")) is not str
            or any(
                type(repository.get(field)) is not list
                or any(type(item) is not str for item in repository[field])
                for field in (
                    "staged_paths",
                    "dirty_tracked_paths",
                    "required_untracked_paths",
                )
            )
        ):
            raise CaptureError("canonical-manifest:contract-types")
        repositories[repo_id] = {
            "path": repository["path"],
            "head": repository["head"],
            "staged_paths": list(repository["staged_paths"]),
            "dirty_tracked_paths": list(repository["dirty_tracked_paths"]),
            "required_untracked_paths": list(
                repository["required_untracked_paths"]
            ),
        }
    raw_untracked_bindings = module.EXPECTED_REQUIRED_UNTRACKED_BINDINGS
    if type(raw_untracked_bindings) is not dict:
        raise CaptureError("canonical-manifest:contract-types")
    untracked_bindings: dict[tuple[str, str], str] = {}
    for binding, role in raw_untracked_bindings.items():
        if (
            type(binding) is not tuple
            or len(binding) != 2
            or any(type(item) is not str for item in binding)
            or type(role) is not str
        ):
            raise CaptureError("canonical-manifest:contract-types")
        untracked_bindings[binding] = role
    required_untracked = {
        (repo_id, relative_path)
        for repo_id, repository in repositories.items()
        for relative_path in repository["required_untracked_paths"]
    }
    if required_untracked != set(untracked_bindings):
        raise CaptureError("canonical-manifest:untracked-binding-topology")
    for (repo_id, relative_path), role in untracked_bindings.items():
        expected_path = f"{repositories[repo_id]['path']}/{relative_path}"
        if role not in remote_files or remote_files[role][0] != expected_path:
            raise CaptureError("canonical-manifest:untracked-binding-path")
    dataset_contract = _dataset_contract_from_module(module)
    dataset_contract_sha256 = _canonical_json_sha256(dataset_contract)
    declared_dataset_contract_sha256 = _exact_contract_string(
        module.EXPECTED_DATASET_CONTRACT_SHA256
    )
    if (
        declared_dataset_contract_sha256 != EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256
        or dataset_contract_sha256 != EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256
    ):
        raise CaptureError("canonical-manifest:dataset-contract-sha256")
    expected_archive_names = {
        "v1.0-trainval_meta.tgz",
        *(f"v1.0-trainval{index:02d}_blobs.tgz" for index in range(1, 11)),
        "nuScenes-map-expansion-v1.3.zip",
    }
    archives = {
        name: (row["sha256"], row["bytes"])
        for name, row in dataset_contract["archives"].items()
    }
    if (
        set(archives) != expected_archive_names
        or len(dataset_contract["metadata_json_names"]) != 13
        or len(set(dataset_contract["metadata_json_names"])) != 13
        or len(dataset_contract["map_anchor_names"]) != 5
        or len(set(dataset_contract["map_anchor_names"])) != 5
        or len(dataset_contract["map_directory_names"]) != 3
        or {
            name: len(files)
            for name, files in dataset_contract["map_directory_names"].items()
        } != {"basemap": 4, "expansion": 4, "prediction": 1}
        or sum(row[1] for row in archives.values()) != 315_285_139_203
    ):
        raise CaptureError("canonical-manifest:dataset-contract-topology")
    dataset_root = dataset_contract["dataset_root"]
    dataset_version = dataset_contract["dataset_version"]
    if (
        dataset_root != "/datasets/nuscenes-full"
        or dataset_version != "v1.0-trainval"
        or dataset_contract["archive_root"] != f"{dataset_root}/archives"
        or dataset_contract["metadata_root"] != f"{dataset_root}/{dataset_version}"
        or dataset_contract["map_root"] != f"{dataset_root}/maps"
    ):
        raise CaptureError("canonical-manifest:dataset-contract-paths")
    storage_identity = module.EXPECTED_STORAGE_IDENTITY
    storage_fields = {
        "filesystem_path",
        "filesystem_realpath",
        "filesystem_is_symlink",
        "filesystem_empty",
        "mount_target",
        "mount_source",
        "mount_fstype",
        "mount_uuid",
    }
    if (
        type(storage_identity) is not dict
        or set(storage_identity) != storage_fields
        or type(storage_identity.get("filesystem_is_symlink")) is not bool
        or type(storage_identity.get("filesystem_empty")) is not bool
        or any(
            type(storage_identity[field]) is not str
            for field in storage_fields
            - {"filesystem_is_symlink", "filesystem_empty"}
        )
    ):
        raise CaptureError("canonical-manifest:contract-types")
    image_ids = module.EXPECTED_IMAGE_IDS
    if (
        type(image_ids) is not dict
        or any(
            type(name) is not str
            or type(image_id) is not str
            or _IMAGE_ID_RE.fullmatch(image_id) is None
            for name, image_id in image_ids.items()
        )
    ):
        raise CaptureError("canonical-manifest:contract-types")
    compose_input_sha256 = _exact_contract_string(
        module.EXPECTED_COMPOSE_INPUT_SHA256
    )
    compose_output_sha256 = _exact_contract_string(
        module.EXPECTED_COMPOSE_OUTPUT_SHA256
    )
    projected_output_bytes = _exact_contract_integer(
        module.PROJECTED_OUTPUT_BYTES
    )
    minimum_remote_free_bytes = _exact_contract_integer(
        module.MINIMUM_REMOTE_FREE_BYTES
    )
    minimum_reserve_bytes = _exact_contract_integer(
        module.MINIMUM_RESERVE_BYTES
    )
    minimum_local_free_bytes = _exact_contract_integer(
        module.MINIMUM_LOCAL_FREE_BYTES
    )
    return Contract(
        schema=EXPECTED_ENVIRONMENT_SCHEMA,
        ready_verdict=ready_verdict,
        remote_files=remote_files,
        repositories=repositories,
        required_untracked_bindings=untracked_bindings,
        storage_identity=dict(storage_identity),
        dataset_schema=dataset_contract["schema"],
        dataset_contract_sha256=dataset_contract_sha256,
        dataset_root=dataset_root,
        dataset_version=dataset_version,
        dataset_archive_root=dataset_contract["archive_root"],
        dataset_metadata_root=dataset_contract["metadata_root"],
        dataset_map_root=dataset_contract["map_root"],
        dataset_mount=dict(dataset_contract["mount"]),
        dataset_proof_basis=dict(dataset_contract["proof_basis"]),
        dataset_archives=archives,
        dataset_metadata_files=tuple(dataset_contract["metadata_json_names"]),
        dataset_map_anchors=tuple(dataset_contract["map_anchor_names"]),
        dataset_map_directories={
            name: tuple(files)
            for name, files in sorted(dataset_contract["map_directory_names"].items())
        },
        image_ids=dict(image_ids),
        compose_input_sha256=compose_input_sha256,
        compose_output_sha256=compose_output_sha256,
        projected_output_bytes=projected_output_bytes,
        minimum_remote_free_bytes=minimum_remote_free_bytes,
        minimum_reserve_bytes=minimum_reserve_bytes,
        minimum_local_free_bytes=minimum_local_free_bytes,
    )


def _literal_assignments(source: bytes, names: set[str]) -> dict[str, str]:
    tree = ast.parse(source.decode("utf-8"))
    values: dict[str, str] = {}

    def evaluate(node: ast.expr) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return evaluate(node.left) + evaluate(node.right)
        raise CaptureError("compose-patcher:nonliteral-contract")

    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name) or target.id not in names:
            continue
        values[target.id] = evaluate(statement.value)
    if set(values) != names:
        raise CaptureError(f"compose-patcher:missing-constants:{sorted(names - set(values))}")
    return values


def _compose_preimage(
    final_bytes: bytes,
    patcher_bytes: bytes,
    expected_input_sha256: str,
    expected_output_sha256: str,
) -> tuple[bytes | None, list[str]]:
    names = {
        "EXPECTED_INPUT_SHA256",
        "EXPECTED_OUTPUT_SHA256",
        "ANCHOR",
        "REPLACEMENT",
        "OUTPUT_DECLARATION_ANCHOR",
        "OUTPUT_DECLARATION_REPLACEMENT",
        "OUTPUT_MOUNT_ANCHOR",
        "OUTPUT_MOUNT_REPLACEMENT",
        "OUTPUT_LOG_ANCHOR",
        "OUTPUT_LOG_REPLACEMENT",
    }
    problems: list[str] = []
    try:
        values = _literal_assignments(patcher_bytes, names)
        final = final_bytes.decode("utf-8")
    except (CaptureError, UnicodeDecodeError) as error:
        return None, [f"compose:preimage:{type(error).__name__}"]
    if values["EXPECTED_INPUT_SHA256"] != expected_input_sha256:
        problems.append("compose:patcher-input-contract")
    if values["EXPECTED_OUTPUT_SHA256"] != expected_output_sha256:
        problems.append("compose:patcher-output-contract")
    pairs = (
        (values["ANCHOR"], values["REPLACEMENT"]),
        (values["OUTPUT_DECLARATION_ANCHOR"], values["OUTPUT_DECLARATION_REPLACEMENT"]),
        (values["OUTPUT_MOUNT_ANCHOR"], values["OUTPUT_MOUNT_REPLACEMENT"]),
        (values["OUTPUT_LOG_ANCHOR"], values["OUTPUT_LOG_REPLACEMENT"]),
    )
    recovered = final
    for anchor, replacement in reversed(pairs):
        if recovered.count(replacement) != 1:
            problems.append("compose:replacement-count")
            continue
        recovered = recovered.replace(replacement, anchor, 1)
    replay = recovered
    for anchor, replacement in pairs:
        if replay.count(anchor) != 1:
            problems.append("compose:anchor-count")
            continue
        replay = replay.replace(anchor, replacement, 1)
    if replay != final:
        problems.append("compose:replay-drift")
    return recovered.encode("utf-8"), sorted(set(problems))


def _decode_nul(output: bytes, label: str, problems: list[str]) -> list[str]:
    if not output:
        return []
    if not output.endswith(b"\0"):
        problems.append(f"repository:{label}:not-nul-terminated")
    rows: list[str] = []
    for raw in output.rstrip(b"\0").split(b"\0"):
        try:
            row = raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"repository:{label}:non-utf8")
            continue
        if not row or row.startswith("/") or ".." in Path(row).parts:
            problems.append(f"repository:{label}:unsafe-path")
            continue
        rows.append(row)
    return sorted(rows)


def _git(hooks: Hooks, repo: Path, *args: str) -> bytes:
    return hooks.run(
        [
            "git",
            "-c",
            f"safe.directory={repo}",
            "-C",
            str(repo),
            *args,
        ]
    )


def _repository_snapshot(
    hooks: Hooks,
    repo_id: str,
    repo: Path,
    problems: list[str],
) -> dict[str, Any]:
    return {
        "top": _git(hooks, repo, "rev-parse", "--show-toplevel").decode().strip(),
        "head": _git(hooks, repo, "rev-parse", "HEAD").decode().strip(),
        "staged": _decode_nul(
            _git(hooks, repo, "diff", "--cached", "--name-only", "-z"),
            f"{repo_id}:staged",
            problems,
        ),
        "dirty": _decode_nul(
            _git(hooks, repo, "diff", "--name-only", "-z"),
            f"{repo_id}:dirty",
            problems,
        ),
        "untracked": _decode_nul(
            _git(hooks, repo, "ls-files", "--others", "--exclude-standard", "-z"),
            f"{repo_id}:untracked",
            problems,
        ),
    }


def _probe_repositories(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for repo_id, expected in sorted(contract.repositories.items()):
        repo = Path(str(expected["path"]))
        components_before, path_problems = _component_snapshot(repo)
        problems.extend(f"repository:{repo_id}:{item}" for item in path_problems)
        try:
            resolved = repo.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            resolved = None
            problems.append(f"repository:{repo_id}:resolve:{type(error).__name__}")
        if resolved is not None and resolved != repo:
            problems.append(f"repository:{repo_id}:realpath:{resolved}")
        try:
            first = _repository_snapshot(hooks, repo_id, repo, problems)
            second = _repository_snapshot(hooks, repo_id, repo, problems)
            if first != second:
                problems.append(f"repository:{repo_id}:unstable-snapshot")
            top = second["top"]
            head = second["head"]
            staged = second["staged"]
            dirty = second["dirty"]
            untracked = second["untracked"]
        except (CaptureError, UnicodeDecodeError) as error:
            problems.append(f"repository:{repo_id}:probe:{type(error).__name__}")
            top, head, staged, dirty, untracked = None, None, [], [], []
        components_after, after_problems = _component_snapshot(repo)
        problems.extend(f"repository:{repo_id}:{item}" for item in after_problems)
        if components_before != components_after:
            problems.append(f"repository:{repo_id}:unstable-components")

        if top != str(repo):
            problems.append(f"repository:{repo_id}:top-level")
        if head != expected["head"]:
            problems.append(f"repository:{repo_id}:head")
        if staged != expected["staged_paths"]:
            problems.append(f"repository:{repo_id}:staged-paths")
        if dirty != expected["dirty_tracked_paths"]:
            problems.append(f"repository:{repo_id}:dirty-tracked-paths")

        required = sorted(str(value) for value in expected["required_untracked_paths"])
        if repo_id == "neuroncap":
            unexpected = [path for path in untracked if not path.startswith("outoutput/")]
            observed_required: list[str] = []
        elif repo_id == "neurad":
            unexpected = [path for path in untracked if path not in required]
            observed_required = sorted(path for path in untracked if path in required)
        elif repo_id == "uniad":
            # The UniAD checkout carries exactly one untracked entry: the load-bearing
            # `checkpoints` symlink through which the tracked configuration resolves its
            # motion anchors into the gitignored `ckpts` payload. It is a directory
            # symlink, so it cannot be hash-bound like the regular-file untracked
            # requirements; its presence, type, and exact target are the contract.
            unexpected = [path for path in untracked if path != "checkpoints"]
            observed_required = sorted(path for path in untracked if path in required)
            checkpoints_link = repo / "checkpoints"
            if untracked.count("checkpoints") != 1:
                problems.append(f"repository:{repo_id}:checkpoints-untracked-missing")
            try:
                link_target = os.readlink(checkpoints_link)
            except OSError:
                link_target = None
            if not checkpoints_link.is_symlink() or link_target != "ckpts":
                problems.append(f"repository:{repo_id}:checkpoints-symlink")
        else:
            unexpected = list(untracked)
            observed_required = sorted(path for path in untracked if path in required)
        if unexpected:
            problems.append(f"repository:{repo_id}:unexpected-untracked:{len(unexpected)}")
        if observed_required != required:
            problems.append(f"repository:{repo_id}:required-untracked")
        receipts[repo_id] = {
            "path": str(repo),
            "head": head,
            "staged_paths": staged,
            "dirty_tracked_paths": dirty,
            "required_untracked_paths": observed_required,
        }
    return receipts


def _probe_remote_files(
    contract: Contract,
    patcher_path: Path,
    problems: list[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    compose_bytes: bytes | None = None
    for role, (path_text, expected_digest, expected_bytes) in sorted(contract.remote_files.items()):
        row, data, file_problems = stable_read(
            Path(path_text), collect_bytes=role == "compose_script"
        )
        problems.extend(f"remote-file:{role}:{item}" for item in file_problems)
        if row["sha256"] != expected_digest:
            problems.append(f"remote-file:{role}:sha256")
        if row["bytes"] != expected_bytes:
            problems.append(f"remote-file:{role}:bytes")
        receipts[role] = row
        if role == "compose_script":
            compose_bytes = data

    patcher, patcher_bytes, patcher_problems = stable_read(patcher_path, collect_bytes=True)
    problems.extend(f"compose:patcher:{item}" for item in patcher_problems)
    compose = receipts.get("compose_script")
    if isinstance(compose, dict):
        compose["source_sha256"] = None
        compose["patcher_sha256"] = patcher.get("sha256")
    if compose_bytes is None or patcher_bytes is None:
        problems.append("compose:provenance-unavailable")
    else:
        source, source_problems = _compose_preimage(
            compose_bytes,
            patcher_bytes,
            contract.compose_input_sha256,
            contract.compose_output_sha256,
        )
        problems.extend(source_problems)
        source_digest = hashlib.sha256(source).hexdigest() if source is not None else None
        if isinstance(compose, dict):
            compose["source_sha256"] = source_digest
        if source_digest != contract.compose_input_sha256:
            problems.append("compose:source-sha256")
        if hashlib.sha256(compose_bytes).hexdigest() != contract.compose_output_sha256:
            problems.append("compose:output-sha256")
    return receipts


def _probe_images(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
    docker_client: Path | None,
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, expected_id in sorted(contract.image_ids.items()):
        image_id: Any = None
        repo_digests: Any = None
        try:
            if docker_client is None:
                raise CaptureError("docker-client-unavailable")
            raw = json.loads(hooks.run([str(docker_client), "image", "inspect", name]))
            if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], dict):
                raise CaptureError("image-inspect-schema")
            image_id = raw[0].get("Id")
            repo_digests = raw[0].get("RepoDigests")
        except (CaptureError, json.JSONDecodeError) as error:
            problems.append(f"image:{name}:probe:{type(error).__name__}")
        if (
            image_id != expected_id
            or not isinstance(image_id, str)
            or not _IMAGE_ID_RE.fullmatch(image_id)
        ):
            problems.append(f"image:{name}:id")
        if not isinstance(repo_digests, list) or not all(
            isinstance(value, str) and _REPO_DIGEST_RE.fullmatch(value) for value in repo_digests
        ):
            problems.append(f"image:{name}:repo-digests-schema")
            repo_digests = []
        else:
            if len(repo_digests) != len(set(repo_digests)):
                problems.append(f"image:{name}:repo-digests-duplicate")
            repo_digests = sorted(set(repo_digests))
        receipts[name] = {"image_id": image_id, "repo_digests": repo_digests}
    return receipts


def _probe_gpu_and_idle(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
    docker_client: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    gpu: dict[str, Any] = {
        "model": None,
        "count": 0,
        "uuid": None,
        "driver_version": None,
        "memory_total_mib": None,
    }
    try:
        rows = [
            line.strip()
            for line in hooks.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,uuid,driver_version,memory.total",
                    "--format=csv,noheader,nounits",
                ]
            )
            .decode()
            .splitlines()
            if line.strip()
        ]
        gpu["count"] = len(rows)
        if len(rows) == 1:
            fields = [field.strip() for field in rows[0].split(",")]
            if len(fields) == 4:
                gpu.update(
                    {
                        "model": fields[0],
                        "uuid": fields[1],
                        "driver_version": fields[2],
                        "memory_total_mib": int(fields[3]),
                    }
                )
    except (CaptureError, UnicodeDecodeError, ValueError) as error:
        problems.append(f"gpu:probe:{type(error).__name__}")
    expected_gpu = {
        "model": contract.gpu_model,
        "count": 1,
        "uuid": contract.gpu_uuid,
        "driver_version": contract.gpu_driver,
        "memory_total_mib": contract.gpu_memory_mib,
    }
    if gpu != expected_gpu:
        problems.append("gpu:identity")
    if not isinstance(gpu.get("uuid"), str) or not _GPU_UUID_RE.fullmatch(gpu["uuid"]):
        problems.append("gpu:uuid-format")
    if not isinstance(gpu.get("driver_version"), str) or not _DRIVER_RE.fullmatch(
        gpu["driver_version"]
    ):
        problems.append("gpu:driver-format")

    container_count: int | None = None
    compute_count: int | None = None
    evaluator_count: int | None = None
    try:
        if docker_client is None:
            raise CaptureError("docker-client-unavailable")
        containers = [
            row
            for row in hooks.run(
                [str(docker_client), "ps", "-aq", "--no-trunc"]
            ).splitlines()
            if row
        ]
        container_count = len(containers)
    except CaptureError as error:
        problems.append(f"idle:containers:{type(error).__name__}")
    if container_count != 0:
        problems.append("idle:containers-present")
    try:
        compute = [
            row
            for row in hooks.run(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid",
                    "--format=csv,noheader,nounits",
                ]
            ).splitlines()
            if row.strip()
        ]
        compute_count = len(compute)
    except CaptureError as error:
        problems.append(f"idle:gpu-processes:{type(error).__name__}")
    if compute_count != 0:
        problems.append("idle:gpu-process-present")
    try:
        process_rows = hooks.run(["ps", "-eo", "pid=,ppid=,args="]).decode().splitlines()
        parsed: dict[int, tuple[int, str]] = {}
        for row in process_rows:
            fields = row.strip().split(maxsplit=2)
            if len(fields) != 3:
                continue
            parsed[int(fields[0])] = (int(fields[1]), fields[2])
        ancestors: set[int] = set()
        cursor = hooks.pid()
        while cursor in parsed and cursor not in ancestors:
            ancestors.add(cursor)
            cursor = parsed[cursor][0]
        evaluator_count = sum(
            1
            for pid, (_parent, command) in parsed.items()
            if pid not in ancestors and _EVALUATOR_RE.search(command)
        )
    except (CaptureError, UnicodeDecodeError, ValueError) as error:
        problems.append(f"idle:evaluator-processes:{type(error).__name__}")
    if evaluator_count != 0:
        problems.append("idle:evaluator-process-present")
    idle = container_count == compute_count == evaluator_count == 0
    box = {
        "idle": idle,
        "all_containers": container_count,
        "gpu_compute_processes": compute_count,
        "known_evaluation_processes": evaluator_count,
    }
    return gpu, box


def _dataset_contract_payload(contract: Contract) -> dict[str, Any]:
    return {
        "schema": contract.dataset_schema,
        "dataset_root": contract.dataset_root,
        "dataset_version": contract.dataset_version,
        "archive_root": contract.dataset_archive_root,
        "metadata_root": contract.dataset_metadata_root,
        "map_root": contract.dataset_map_root,
        "mount": dict(contract.dataset_mount),
        "proof_basis": dict(contract.dataset_proof_basis),
        "archives": {
            name: {"sha256": digest, "bytes": byte_count}
            for name, (digest, byte_count) in sorted(contract.dataset_archives.items())
        },
        "metadata_json_names": list(contract.dataset_metadata_files),
        "map_anchor_names": list(contract.dataset_map_anchors),
        "map_directory_names": {
            name: list(files)
            for name, files in sorted(contract.dataset_map_directories.items())
        },
    }


def _dataset_directory_snapshot(
    path: Path,
    expected_names: set[str] | None,
    label: str,
    problems: list[str],
    expected_directories: set[str] | None = None,
) -> tuple[dict[str, Any], tuple[Any, ...] | None]:
    identity: dict[str, Any] = {"realpath": None, "is_symlink": None}
    components, component_problems = _component_snapshot(path)
    problems.extend(f"dataset:{label}:{item}" for item in component_problems)
    try:
        directory = path.lstat()
        identity["is_symlink"] = stat.S_ISLNK(directory.st_mode)
        resolved = path.resolve(strict=True)
        identity["realpath"] = str(resolved)
        if resolved != path:
            problems.append(f"dataset:{label}:realpath:{resolved}")
        if not stat.S_ISDIR(directory.st_mode):
            problems.append(f"dataset:{label}:not-directory")
        entries: list[tuple[str, tuple[int, int, int, int, int, int]]] = []
        allowed_directories = expected_directories or set()
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            child_info = child.lstat()
            entries.append((child.name, _stat_identity(child_info)))
            if child.name in allowed_directories:
                # A contract-pinned subdirectory must be a physical directory; its own
                # file set is validated by a dedicated snapshot.
                if stat.S_ISLNK(child_info.st_mode) or not stat.S_ISDIR(child_info.st_mode):
                    problems.append(f"dataset:{label}:nonphysical-directory:{child.name}")
                continue
            if expected_names is not None and (
                stat.S_ISLNK(child_info.st_mode) or not stat.S_ISREG(child_info.st_mode)
            ):
                problems.append(f"dataset:{label}:nonphysical-file:{child.name}")
        observed_names = {name for name, _info in entries}
        if expected_names is not None and observed_names != (
            expected_names | allowed_directories
        ):
            problems.append(f"dataset:{label}:file-set")
        snapshot: tuple[Any, ...] | None = (
            tuple(components),
            _stat_identity(directory),
            tuple(entries),
        )
    except OSError as error:
        problems.append(f"dataset:{label}:directory:{type(error).__name__}")
        snapshot = None
    return identity, snapshot


def _dataset_file(
    hooks: Hooks,
    path: Path,
    label: str,
    problems: list[str],
) -> dict[str, Any]:
    try:
        observed, file_problems = hooks.dataset_read(path)
    except (OSError, CaptureError) as error:
        problems.append(f"dataset:{label}:read:{type(error).__name__}")
        observed, file_problems = {}, []
    problems.extend(f"dataset:{label}:{item}" for item in file_problems)
    row = {
        "path": observed.get("path"),
        "sha256": observed.get("sha256"),
        "bytes": observed.get("bytes"),
    }
    if row["path"] != str(path):
        problems.append(f"dataset:{label}:path")
    if not isinstance(row["sha256"], str) or not _SHA256_RE.fullmatch(row["sha256"]):
        problems.append(f"dataset:{label}:sha256")
    if type(row["bytes"]) is not int or row["bytes"] <= 0:
        problems.append(f"dataset:{label}:bytes")
    return row


def _dataset_receipt_payload_sha256(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_payload_sha256", None)
    return _canonical_json_sha256(payload)


def _probe_dataset(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> dict[str, Any]:
    if _canonical_json_sha256(_dataset_contract_payload(contract)) != (
        contract.dataset_contract_sha256
    ):
        problems.append("dataset:contract-sha256")

    root = Path(contract.dataset_root)
    archive_root = Path(contract.dataset_archive_root)
    metadata_root = Path(contract.dataset_metadata_root)
    map_root = Path(contract.dataset_map_root)
    root_identity, root_before = _dataset_directory_snapshot(root, None, "root", problems)
    archive_identity, archives_before = _dataset_directory_snapshot(
        archive_root, set(contract.dataset_archives), "archives", problems
    )
    metadata_identity, metadata_before = _dataset_directory_snapshot(
        metadata_root, set(contract.dataset_metadata_files), "metadata", problems
    )
    map_identity, maps_before = _dataset_directory_snapshot(
        map_root,
        set(contract.dataset_map_anchors),
        "maps",
        problems,
        expected_directories=set(contract.dataset_map_directories),
    )
    map_directory_snapshots: dict[str, tuple[Any, ...] | None] = {}
    for directory_name, directory_files in sorted(contract.dataset_map_directories.items()):
        _directory_identity, directory_before = _dataset_directory_snapshot(
            map_root / directory_name,
            set(directory_files),
            f"maps:{directory_name}",
            problems,
        )
        map_directory_snapshots[directory_name] = directory_before

    archives: dict[str, dict[str, Any]] = {}
    for name, (expected_digest, expected_bytes) in sorted(contract.dataset_archives.items()):
        row = _dataset_file(hooks, archive_root / name, f"archive:{name}", problems)
        if row["sha256"] != expected_digest:
            problems.append(f"dataset:archive:{name}:expected-sha256")
        if row["bytes"] != expected_bytes:
            problems.append(f"dataset:archive:{name}:expected-bytes")
        archives[name] = row

    metadata: dict[str, dict[str, Any]] = {}
    for name in contract.dataset_metadata_files:
        metadata[name] = _dataset_file(hooks, metadata_root / name, f"metadata:{name}", problems)

    maps: dict[str, dict[str, Any]] = {}
    for name in contract.dataset_map_anchors:
        maps[name] = _dataset_file(hooks, map_root / name, f"map:{name}", problems)

    _root_after_identity, root_after = _dataset_directory_snapshot(
        root, None, "root-after", problems
    )
    _archive_after_identity, archives_after = _dataset_directory_snapshot(
        archive_root, set(contract.dataset_archives), "archives-after", problems
    )
    _metadata_after_identity, metadata_after = _dataset_directory_snapshot(
        metadata_root, set(contract.dataset_metadata_files), "metadata-after", problems
    )
    _map_after_identity, maps_after = _dataset_directory_snapshot(
        map_root,
        set(contract.dataset_map_anchors),
        "maps-after",
        problems,
        expected_directories=set(contract.dataset_map_directories),
    )
    for directory_name, directory_files in sorted(contract.dataset_map_directories.items()):
        _directory_identity, directory_after = _dataset_directory_snapshot(
            map_root / directory_name,
            set(directory_files),
            f"maps:{directory_name}-after",
            problems,
        )
        if map_directory_snapshots.get(directory_name) != directory_after:
            problems.append(f"dataset:maps:{directory_name}:unstable-directory")
    for label, before, after in (
        ("root", root_before, root_after),
        ("archives", archives_before, archives_after),
        ("metadata", metadata_before, metadata_after),
        ("maps", maps_before, maps_after),
    ):
        if before != after:
            problems.append(f"dataset:{label}:unstable-directory")

    mount_identity = {
        "mount_target": None,
        "mount_source": None,
        "mount_fstype": None,
        "mount_uuid": None,
    }
    try:
        mount_raw = json.loads(
            hooks.run(
                [
                    "findmnt",
                    "--json",
                    "--output",
                    "TARGET,SOURCE,FSTYPE,UUID",
                    "--target",
                    str(root),
                ]
            )
        )
        rows = mount_raw.get("filesystems") if isinstance(mount_raw, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise CaptureError("findmnt-schema")
        mount_identity = {
            "mount_target": rows[0].get("target"),
            "mount_source": rows[0].get("source"),
            "mount_fstype": rows[0].get("fstype"),
            "mount_uuid": rows[0].get("uuid"),
        }
    except (CaptureError, json.JSONDecodeError) as error:
        problems.append(f"dataset:findmnt:{type(error).__name__}")
    for field, expected in contract.dataset_mount.items():
        if mount_identity.get(field) != expected:
            problems.append(f"dataset:identity:{field}")

    dataset_device = mount_device = root_device = None
    try:
        dataset_device = hooks.device(root)
        mount_device = hooks.device(Path(str(contract.dataset_mount["mount_target"])))
        root_device = hooks.device(Path("/"))
    except OSError as error:
        problems.append(f"dataset:device:{type(error).__name__}")
    for label, value in (
        ("dataset", dataset_device),
        ("mount", mount_device),
        ("root", root_device),
    ):
        if type(value) is not int:
            problems.append(f"dataset:{label}-device-type")
        elif value < 0:
            problems.append(f"dataset:{label}-device-negative")
    if (
        type(dataset_device) is not int
        or type(mount_device) is not int
        or dataset_device != mount_device
    ):
        problems.append("dataset:device-mismatch")
    if (
        type(dataset_device) is not int
        or type(root_device) is not int
        or dataset_device == root_device
    ):
        problems.append("dataset:not-dedicated-device")

    identity = {
        "dataset_root": str(root),
        "dataset_realpath": root_identity["realpath"],
        "dataset_is_symlink": root_identity["is_symlink"],
        "dataset_version": contract.dataset_version,
        "archive_root": str(archive_root),
        "archive_realpath": archive_identity["realpath"],
        "archive_is_symlink": archive_identity["is_symlink"],
        "metadata_root": str(metadata_root),
        "metadata_realpath": metadata_identity["realpath"],
        "metadata_is_symlink": metadata_identity["is_symlink"],
        "map_root": str(map_root),
        "map_realpath": map_identity["realpath"],
        "map_is_symlink": map_identity["is_symlink"],
        **mount_identity,
        "dataset_st_dev": dataset_device,
        "mount_st_dev": mount_device,
        "root_st_dev": root_device,
    }
    receipt = {
        "schema": contract.dataset_schema,
        "contract_sha256": contract.dataset_contract_sha256,
        "proof_basis": dict(contract.dataset_proof_basis),
        "identity": identity,
        "archives": archives,
        "metadata_json": metadata,
        "map_anchors": maps,
    }
    receipt["receipt_payload_sha256"] = _dataset_receipt_payload_sha256(receipt)
    return receipt


def _probe_storage(
    contract: Contract,
    hooks: Hooks,
    local_free_bytes: int,
    problems: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = contract.storage_identity
    output_root = Path(str(expected["filesystem_path"]))
    identity = {
        "filesystem_path": str(output_root),
        "filesystem_realpath": None,
        "filesystem_is_symlink": None,
        "filesystem_empty": None,
        "mount_target": None,
        "mount_source": None,
        "mount_fstype": None,
        "mount_uuid": None,
    }
    _, component_problems = _component_snapshot(output_root)
    problems.extend(f"storage:{item}" for item in component_problems)
    try:
        root_lstat = output_root.lstat()
        identity["filesystem_is_symlink"] = stat.S_ISLNK(root_lstat.st_mode)
        resolved = output_root.resolve(strict=True)
        identity["filesystem_realpath"] = str(resolved)
        if not stat.S_ISDIR(root_lstat.st_mode):
            problems.append("storage:output-root-not-directory")
        identity["filesystem_empty"] = not any(output_root.iterdir())
    except OSError as error:
        problems.append(f"storage:output-root:{type(error).__name__}")
    for field, expected_value in expected.items():
        if field.startswith("mount_"):
            continue
        actual = identity.get(field)
        if actual != expected_value or (
            isinstance(expected_value, bool) and type(actual) is not bool
        ):
            problems.append(f"storage:identity:{field}")
    try:
        mount_raw = json.loads(
            hooks.run(
                [
                    "findmnt",
                    "--json",
                    "--output",
                    "TARGET,SOURCE,FSTYPE,UUID",
                    "--target",
                    str(output_root),
                ]
            )
        )
        rows = mount_raw.get("filesystems") if isinstance(mount_raw, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise CaptureError("findmnt-schema")
        mount = rows[0]
        identity.update(
            {
                "mount_target": mount.get("target"),
                "mount_source": mount.get("source"),
                "mount_fstype": mount.get("fstype"),
                "mount_uuid": mount.get("uuid"),
            }
        )
    except (CaptureError, json.JSONDecodeError) as error:
        problems.append(f"storage:findmnt:{type(error).__name__}")
    for field in ("mount_target", "mount_source", "mount_fstype", "mount_uuid"):
        if identity.get(field) != expected[field]:
            problems.append(f"storage:identity:{field}")

    output_device = mount_device = root_device = None
    try:
        output_device = hooks.device(output_root)
        mount_device = hooks.device(Path(str(expected["mount_target"])))
        root_device = hooks.device(Path("/"))
    except OSError as error:
        problems.append(f"storage:device:{type(error).__name__}")
    for label, value in (
        ("filesystem", output_device),
        ("mount", mount_device),
        ("root", root_device),
    ):
        if type(value) is not int:
            problems.append(f"storage:{label}-device-type")
        elif value < 0:
            problems.append(f"storage:{label}-device-negative")
    if (
        type(output_device) is not int
        or type(mount_device) is not int
        or output_device != mount_device
    ):
        problems.append("storage:output-device-mismatch")
    if (
        type(output_device) is not int
        or type(root_device) is not int
        or output_device == root_device
    ):
        problems.append("storage:not-dedicated-device")

    remote_free_bytes: int | None = None
    try:
        remote_free_bytes = hooks.disk_free(output_root)
    except OSError as error:
        problems.append(f"storage:disk-free:{type(error).__name__}")
    if type(remote_free_bytes) is not int or remote_free_bytes < contract.minimum_remote_free_bytes:
        problems.append("storage:remote-free")
    if (
        type(remote_free_bytes) is not int
        or remote_free_bytes - contract.projected_output_bytes < contract.minimum_reserve_bytes
    ):
        problems.append("storage:projected-reserve")
    if type(local_free_bytes) is not int or local_free_bytes < contract.minimum_local_free_bytes:
        problems.append("storage:local-free")

    storage = {
        "remote_output_free_bytes": remote_free_bytes,
        "projected_output_bytes": contract.projected_output_bytes,
        "minimum_reserve_bytes": contract.minimum_reserve_bytes,
        "local_free_bytes": local_free_bytes,
        "remote_output_free_gib": (
            remote_free_bytes / 1024**3 if type(remote_free_bytes) is int else None
        ),
        "projected_output_gib": contract.projected_output_bytes / 1024**3,
        "minimum_reserve_gib": contract.minimum_reserve_bytes / 1024**3,
        "local_free_gib": local_free_bytes / 1024**3,
        **identity,
    }
    devices = {
        "filesystem_st_dev": output_device,
        "mount_st_dev": mount_device,
        "root_st_dev": root_device,
    }
    return storage, devices


def _interpreter_receipt_problems(value: object) -> list[str]:
    fields = {
        "invocation_path",
        "physical_path",
        "realpath",
        "sha256",
        "bytes",
        "version",
        "implementation",
    }
    if type(value) is not dict or set(value) != fields:
        return ["interpreter:receipt-field-set"]
    invocation_path = value.get("invocation_path")
    physical_path = value.get("physical_path")
    realpath = value.get("realpath")
    sha256 = value.get("sha256")
    byte_count = value.get("bytes")
    version = value.get("version")
    implementation = value.get("implementation")
    problems: list[str] = []
    if (
        type(invocation_path) is not str
        or not Path(invocation_path).is_absolute()
        or type(physical_path) is not str
        or not Path(physical_path).is_absolute()
        or type(realpath) is not str
        or realpath != physical_path
        or not Path(realpath).is_absolute()
    ):
        problems.append("interpreter:receipt-paths")
    if type(sha256) is not str or _SHA256_RE.fullmatch(sha256) is None:
        problems.append("interpreter:receipt-sha256")
    if type(byte_count) is not int or byte_count <= 0:
        problems.append("interpreter:receipt-bytes")
    if type(version) is not str or _PYTHON_VERSION_RE.fullmatch(version) is None:
        problems.append("interpreter:receipt-version")
    else:
        parsed_version = tuple(int(part) for part in version.split("."))
        if parsed_version < (3, 10, 0):
            problems.append("interpreter:receipt-version")
    if type(implementation) is not str or implementation != "CPython":
        problems.append("interpreter:receipt-implementation")
    return problems


def _invocation_receipt_problems(
    value: object,
    interpreter: object,
) -> list[str]:
    fields = {
        "sanitized",
        "isolated",
        "environment",
        "argv",
        "canonical_script",
    }
    if type(value) is not dict or set(value) != fields:
        return ["invocation:receipt-field-set"]
    problems: list[str] = []
    if value.get("sanitized") is not True:
        problems.append("invocation:receipt-sanitized")
    if value.get("isolated") is not True:
        problems.append("invocation:receipt-isolated")
    if not _exact_json_value(value.get("environment"), SANITIZED_ENVIRONMENT):
        problems.append("invocation:receipt-environment")
    argv = value.get("argv")
    canonical_script = value.get("canonical_script")
    expected_script = str(HERE / "capture_environment135.py")
    physical_interpreter = (
        interpreter.get("physical_path")
        if type(interpreter) is dict
        else None
    )
    if (
        type(argv) is not list
        or len(argv) < 3
        or any(type(item) is not str for item in argv)
        or argv[0] != physical_interpreter
        or argv[1] != "-I"
        or argv[2] != expected_script
    ):
        problems.append("invocation:receipt-argv")
    if type(canonical_script) is not str or canonical_script != expected_script:
        problems.append("invocation:receipt-canonical-script")
    return problems


def _capture_environment_body(
    contract: Contract,
    *,
    host_commit: str,
    local_free_bytes: int,
    host_preparation: Mapping[str, Any],
    started: str,
    host: str,
    patcher_path: Path = CANONICAL_PATCHER_PATH,
    hooks: Hooks = Hooks(),
) -> dict[str, Any]:
    problems: list[str] = []
    artifact_payloads, artifact_problems = (
        hooks.host_artifact_payloads()
        if hooks.host_artifact_payloads is not None
        else _host_artifact_payloads()
    )
    problems.extend(artifact_problems)
    interpreter, interpreter_problems = (
        hooks.interpreter_receipt()
        if hooks.interpreter_receipt is not None
        else _interpreter_receipt()
    )
    if (
        type(interpreter_problems) is not list
        or any(type(item) is not str for item in interpreter_problems)
    ):
        problems.append("interpreter:receipt-problem-list")
    else:
        problems.extend(interpreter_problems)
    problems.extend(_interpreter_receipt_problems(interpreter))
    invocation, invocation_problems = (
        hooks.invocation_receipt()
        if hooks.invocation_receipt is not None
        else _invocation_receipt()
    )
    if (
        type(invocation_problems) is not list
        or any(type(item) is not str for item in invocation_problems)
    ):
        problems.append("invocation:receipt-problem-list")
    else:
        problems.extend(invocation_problems)
    problems.extend(_invocation_receipt_problems(invocation, interpreter))
    preparation_evidence = (
        host_preparation.get("evidence")
        if isinstance(host_preparation, Mapping)
        else None
    )
    preparation_packet = (
        preparation_evidence.get("packet")
        if isinstance(preparation_evidence, Mapping)
        else None
    )
    packet_source_commit = (
        preparation_packet.get("source_commit")
        if isinstance(preparation_packet, Mapping)
        else None
    )
    try:
        host_commit_tree_sha = verify_host_commit_topology(
            host_commit,
            packet_source_commit,
            hooks.fetch_json,
        )
        host_publication_authority = verify_publication_authority(
            host_commit,
            hooks.fetch_json,
            commit_tree_sha=host_commit_tree_sha,
            artifact_payloads=artifact_payloads,
            fetch_raw=hooks.fetch_raw,
        )
    except CaptureError as error:
        host_publication_authority = None
        problems.append(str(error))
    preparation_file = (
        host_preparation.get("receipt_file")
        if isinstance(host_preparation, Mapping)
        else None
    )
    preparation_payload = artifact_payloads.get(HOST_PUBLICATION_ARTIFACT_PATHS[1])
    if (
        not isinstance(preparation_file, Mapping)
        or not isinstance(preparation_payload, bytes)
        or preparation_file.get("sha256") != hashlib.sha256(preparation_payload).hexdigest()
        or type(preparation_file.get("bytes")) is not int
        or preparation_file.get("bytes") != len(preparation_payload)
    ):
        problems.append("host-publication-artifact:preparation-receipt-binding")
    remote_files = _probe_remote_files(contract, patcher_path, problems)
    repositories = _probe_repositories(contract, hooks, problems)
    for (repo_id, relative_path), role in contract.required_untracked_bindings.items():
        repository = repositories.get(repo_id)
        remote = remote_files.get(role)
        if not isinstance(repository, dict) or not isinstance(remote, dict):
            problems.append(f"repository:{repo_id}:untracked-binding:{relative_path}")
            continue
        if remote.get("path") != f"{repository.get('path')}/{relative_path}":
            problems.append(f"repository:{repo_id}:untracked-binding:{relative_path}")
    docker_runtime, docker_client, docker_client_identity = _probe_docker_runtime(
        hooks,
        expected_host=contract.host,
        problems=problems,
    )
    docker_client_receipt = (
        docker_runtime.get("client") if isinstance(docker_runtime, Mapping) else None
    )
    image_client = (
        docker_client
        if _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="images-before",
            problems=problems,
        )
        else None
    )
    images = _probe_images(contract, hooks, problems, image_client)
    if docker_client is not None:
        _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="images-after",
            problems=problems,
        )
    before_runtime_problems: list[str] = []
    before_runtime_client = (
        docker_client
        if _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="runtime-before-dataset-before",
            problems=problems,
        )
        else None
    )
    gpu_before, box_before = _probe_gpu_and_idle(
        contract, hooks, before_runtime_problems, before_runtime_client
    )
    if docker_client is not None:
        _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="runtime-before-dataset-after",
            problems=problems,
        )
    problems.extend(before_runtime_problems)
    dataset = _probe_dataset(contract, hooks, problems)
    after_runtime_problems: list[str] = []
    after_runtime_client = (
        docker_client
        if _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="runtime-after-dataset-before",
            problems=problems,
        )
        else None
    )
    gpu_after, box_after = _probe_gpu_and_idle(
        contract, hooks, after_runtime_problems, after_runtime_client
    )
    if docker_client is not None:
        _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="runtime-after-dataset-after",
            problems=problems,
        )
    problems.extend(after_runtime_problems)
    if gpu_before != gpu_after or box_before != box_after:
        problems.append("runtime-snapshots:drift")
    storage, storage_devices = _probe_storage(contract, hooks, local_free_bytes, problems)
    dataset_identity = dataset.get("identity")
    if not isinstance(dataset_identity, dict) or (
        not _exact_json_value(
            dataset_identity.get("dataset_st_dev"),
            storage_devices.get("filesystem_st_dev"),
        )
        or not _exact_json_value(
            dataset_identity.get("mount_st_dev"),
            storage_devices.get("mount_st_dev"),
        )
        or not _exact_json_value(
            dataset_identity.get("root_st_dev"),
            storage_devices.get("root_st_dev"),
        )
    ):
        problems.append("dataset:storage-device-link")
    if docker_client is not None:
        _revalidate_docker_client(
            docker_client,
            docker_client_receipt,
            docker_client_identity,
            label="final",
            problems=problems,
        )
    if host_publication_authority is not None:
        try:
            host_publication_authority["checks"] = verify_current_authority(
                host_commit,
                hooks.fetch_json,
            )
        except CaptureError as error:
            problems.append(str(error))
    all_problems = sorted(set(problems))
    return {
        "schema": contract.schema,
        "verdict": contract.ready_verdict if not all_problems else INCOMPLETE_VERDICT,
        "captured_at_utc": None,
        "capture_started_at_utc": started,
        "host": host,
        "problem_count": len(all_problems),
        "problems": all_problems,
        "host_publication_authority": host_publication_authority,
        "interpreter": interpreter,
        "invocation": invocation,
        "host_preparation": host_preparation,
        "docker_runtime": docker_runtime,
        "runtime_snapshots": {
            "before_dataset_hashing": {"gpu": gpu_before, "box": box_before},
            "after_dataset_hashing": {"gpu": gpu_after, "box": box_after},
        },
        "gpu": gpu_after,
        "box": box_after,
        "dataset": dataset,
        "storage": storage,
        "storage_devices": storage_devices,
        "repositories": repositories,
        "remote_files": remote_files,
        "container_images": images,
    }


def _validated_utc_timestamp(value: object) -> tuple[datetime, str]:
    if type(value) is not datetime:
        raise TypeError("timestamp-return-type")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp-not-utc")
    rendered = value.isoformat().replace("+00:00", "Z")
    try:
        replay = datetime.fromisoformat(rendered.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise ValueError("timestamp-not-canonical") from error
    if (
        not rendered.endswith("Z")
        or replay.tzinfo != timezone.utc
        or replay != value
        or replay.isoformat().replace("+00:00", "Z") != rendered
    ):
        raise ValueError("timestamp-not-canonical")
    return value, rendered


def _base_environment_receipt(
    contract: Contract,
    host_preparation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": contract.schema,
        "verdict": INCOMPLETE_VERDICT,
        "captured_at_utc": None,
        "capture_started_at_utc": None,
        "host": None,
        "problem_count": 0,
        "problems": [],
        "host_publication_authority": None,
        "interpreter": None,
        "invocation": None,
        "host_preparation": dict(host_preparation),
        "docker_runtime": None,
        "runtime_snapshots": None,
        "gpu": None,
        "box": None,
        "dataset": None,
        "storage": None,
        "storage_devices": None,
        "repositories": None,
        "remote_files": None,
        "container_images": None,
    }


def _set_receipt_problems(receipt: dict[str, Any], problems: Sequence[str]) -> None:
    exact = sorted(set(problems))
    receipt["problems"] = exact
    receipt["problem_count"] = len(exact)
    if exact:
        receipt["verdict"] = INCOMPLETE_VERDICT


def _bounded_fault(error: Exception) -> str:
    if isinstance(error, CaptureError):
        message = str(error)
        if re.fullmatch(r"[A-Za-z0-9_.:/-]{1,240}", message):
            return message
    return f"internal:{type(error).__name__}"


def _serialize_receipt(receipt: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            receipt,
            indent=1,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _execute_admitted_capture(
    contract: Contract,
    *,
    host_commit: str,
    local_free_bytes: int,
    host_preparation: Mapping[str, Any],
    patcher_path: Path,
    hooks: Hooks,
) -> dict[str, Any]:
    receipt = _base_environment_receipt(contract, host_preparation)
    attempt_problems: list[str] = []
    started_value: datetime | None = None
    try:
        try:
            started_value, started = _validated_utc_timestamp(hooks.now())
        except Exception as error:
            attempt_problems.append(f"timing:started:{type(error).__name__}")
        else:
            receipt["capture_started_at_utc"] = started

        if not attempt_problems:
            try:
                host = hooks.hostname()
                if type(host) is not str:
                    raise TypeError("hostname-return-type")
            except Exception as error:
                attempt_problems.append(f"host:probe:{type(error).__name__}")
            else:
                receipt["host"] = host
                if host != contract.host:
                    attempt_problems.append("host:identity")

        if not attempt_problems:
            try:
                receipt = _capture_environment_body(
                    contract,
                    host_commit=host_commit,
                    local_free_bytes=local_free_bytes,
                    host_preparation=host_preparation,
                    started=receipt["capture_started_at_utc"],
                    host=receipt["host"],
                    patcher_path=patcher_path,
                    hooks=hooks,
                )
            except Exception as error:
                attempt_problems.append(_bounded_fault(error))
    finally:
        try:
            finished_value, finished = _validated_utc_timestamp(hooks.now())
            if started_value is not None and finished_value < started_value:
                raise ValueError("finished-before-started")
        except Exception as error:
            attempt_problems.append(f"timing:finished:{type(error).__name__}")
        else:
            receipt["captured_at_utc"] = finished

    _set_receipt_problems(
        receipt,
        [*receipt.get("problems", []), *attempt_problems],
    )
    try:
        _serialize_receipt(receipt)
    except (TypeError, ValueError, OverflowError, RecursionError) as error:
        preserved_started = receipt.get("capture_started_at_utc")
        preserved_finished = receipt.get("captured_at_utc")
        preserved_host = receipt.get("host")
        receipt = _base_environment_receipt(contract, host_preparation)
        receipt["capture_started_at_utc"] = (
            preserved_started if type(preserved_started) is str else None
        )
        receipt["captured_at_utc"] = (
            preserved_finished if type(preserved_finished) is str else None
        )
        receipt["host"] = preserved_host if type(preserved_host) is str else None
        _set_receipt_problems(
            receipt,
            [*attempt_problems, f"serialization:{type(error).__name__}"],
        )
    return receipt


def capture_environment(
    contract: Contract,
    *,
    host_commit: str,
    local_free_bytes: int,
    patcher_path: Path = CANONICAL_PATCHER_PATH,
    hooks: Hooks = Hooks(),
) -> dict[str, Any]:
    admission = _admit_environment_attempt(hooks)
    return _execute_admitted_capture(
        contract,
        host_commit=host_commit,
        local_free_bytes=local_free_bytes,
        host_preparation=admission.host_preparation,
        patcher_path=patcher_path,
        hooks=hooks,
    )


@dataclass
class _EnvironmentOutputAttempt:
    output_path: Path
    parent_path: Path
    parent_fd: int
    parent_identity: tuple[int, int, int]
    attempt_id: str
    completion_nonce: bytes
    marker_payload: bytes
    marker_fd: int = -1
    marker_identity: tuple[int, int, int, int] | None = None
    issued_witness: object | None = None
    completion_consumed: bool = False

    def close(self) -> None:
        if self.marker_fd >= 0:
            try:
                os.close(self.marker_fd)
            except OSError:
                pass
            self.marker_fd = -1
        if self.parent_fd >= 0:
            try:
                os.close(self.parent_fd)
            except OSError:
                # Receipt bytes and the parent durability barrier precede descriptor release.
                pass
            self.parent_fd = -1


@dataclass(frozen=True)
class EnvironmentReceiptCompletionWitness:
    """Process-local binding for the final coupled E receipt observation.

    The witness carries a per-attempt process-local nonce, is accepted only as the exact object
    issued by the publisher, and is single-use.  The nonce is not deliberately persisted, so with
    uncompromised OS randomness retained disk bytes do not contain the full witness.  This does not
    defend against arbitrary same-process code that can mutate the live attempt object, nor prevent
    a later directory-authorized writer from mutating committed names.
    """

    attempt_id: str
    completion_nonce: bytes
    verdict: str
    parent_identity: tuple[int, int, int]
    receipt_inode: tuple[int, int]
    byte_count: int
    payload_sha256: str


def _environment_attempt_marker_payload(
    attempt_id: str,
    parent_identity: tuple[int, int, int],
) -> bytes:
    if (
        type(attempt_id) is not str
        or re.fullmatch(r"[0-9a-f]{64}", attempt_id) is None
        or type(parent_identity) is not tuple
        or len(parent_identity) != 3
        or any(type(item) is not int for item in parent_identity)
    ):
        raise CaptureError("output:attempt-identity")
    return (
        json.dumps(
            {
                "schema": "iter135.environment_capture_attempt_marker.v2",
                "authority": "NONE",
                "status": "ATTEMPT_IN_PROGRESS_NO_ENVIRONMENT_VERDICT",
                "attempt_id": attempt_id,
                "parent_identity": {
                    "st_dev": parent_identity[0],
                    "st_ino": parent_identity[1],
                    "st_mode": parent_identity[2],
                },
                "canonical_receipt": CANONICAL_RECEIPT_BASENAME,
                "pending_receipt": PENDING_RECEIPT_BASENAME,
                "publication_rule": (
                    "pending bytes have no authority until exclusively linked at the canonical "
                    "basename and the held parent directory is fsynced"
                ),
            },
            indent=1,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _output_path_contract(path: Path) -> Path:
    path = Path(path)
    if (
        HERE / "host_preparation_receipt.json" != CANONICAL_PREPARATION_RECEIPT_PATH
        or HERE / CANONICAL_RECEIPT_BASENAME != DEFAULT_OUTPUT
        or path != DEFAULT_OUTPUT
        or path.name != CANONICAL_RECEIPT_BASENAME
        or not path.is_absolute()
    ):
        raise EnvironmentAdmissionStop("output:not-canonical")
    return path


def _open_physical_directory(path: Path) -> int:
    """Open an absolute directory component-by-component without following symlinks."""

    path = Path(path)
    if not path.is_absolute() or any(part in {".", ".."} for part in path.parts[1:]):
        raise CaptureError("output:nonphysical-parent")
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = -1
    try:
        descriptor = os.open(path.anchor, flags)
        for component in path.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("not-directory")
        return descriptor
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        raise CaptureError("output:nonphysical-parent") from error


def _directory_identity(descriptor: int) -> tuple[int, int, int]:
    info = os.fstat(descriptor)
    if not stat.S_ISDIR(info.st_mode):
        raise CaptureError("output:nonphysical-parent")
    return info.st_dev, info.st_ino, info.st_mode


def _dir_entry_exists(parent_fd: int, basename: str) -> bool:
    try:
        os.stat(basename, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise CaptureError(f"output:entry-probe:{type(error).__name__}") from error
    return True


def _write_all(descriptor: int, payload: bytes, *, label: str) -> None:
    offset = 0
    while offset < len(payload):
        try:
            written = os.write(descriptor, payload[offset:])
        except OSError as error:
            raise CaptureError(f"{label}:write:{type(error).__name__}") from error
        if type(written) is not int or written <= 0:
            raise CaptureError(f"{label}:write-zero")
        offset += written


def _exclusive_create_fsynced(
    parent_fd: int,
    basename: str,
    payload: bytes,
    *,
    label: str,
) -> int:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(basename, flags, 0o444, dir_fd=parent_fd)
    except FileExistsError as error:
        raise CaptureError(f"{label}:already-exists") from error
    except OSError as error:
        raise CaptureError(f"{label}:create:{type(error).__name__}") from error
    try:
        os.fchmod(descriptor, 0o444)
        _write_all(descriptor, payload, label=label)
        os.fsync(descriptor)
        return descriptor
    except CaptureError:
        os.close(descriptor)
        raise
    except OSError as error:
        os.close(descriptor)
        raise CaptureError(f"{label}:write:{type(error).__name__}") from error


def _fsync_attempt_parent(attempt: _EnvironmentOutputAttempt, *, label: str) -> None:
    try:
        os.fsync(attempt.parent_fd)
    except OSError as error:
        raise CaptureError(f"output:{label}:{type(error).__name__}") from error


def _replay_attempt_parent(attempt: _EnvironmentOutputAttempt) -> None:
    try:
        _output_path_contract(attempt.output_path)
        replay_fd = _open_physical_directory(attempt.parent_path)
    except CaptureError as error:
        raise CaptureError("output:parent-drift") from error
    try:
        if _directory_identity(replay_fd) != attempt.parent_identity:
            raise CaptureError("output:parent-drift")
    finally:
        os.close(replay_fd)


def _marker_stat_identity(value: os.stat_result) -> tuple[int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_mode, value.st_size


def _bind_attempt_marker(
    attempt: _EnvironmentOutputAttempt,
    *,
    synchronize_file: bool,
) -> None:
    """Bind the marker name to one stable read descriptor and exact attempt bytes."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = -1
    try:
        descriptor = os.open(
            ATTEMPT_MARKER_BASENAME,
            flags,
            dir_fd=attempt.parent_fd,
        )
        if synchronize_file:
            os.fsync(descriptor)
        before = os.fstat(descriptor)
        named_before = os.stat(
            ATTEMPT_MARKER_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        _read_exact_receipt_descriptor(
            descriptor,
            attempt.marker_payload,
            problem="output:attempt-marker-drift",
        )
        after = os.fstat(descriptor)
        named_after = os.stat(
            ATTEMPT_MARKER_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        identity = _marker_stat_identity(before)
        if (
            identity != _marker_stat_identity(after)
            or identity != _marker_stat_identity(named_before)
            or identity != _marker_stat_identity(named_after)
            or not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o444
            or before.st_size != len(attempt.marker_payload)
            or before.st_nlink != 1
            or after.st_nlink != 1
            or named_before.st_nlink != 1
            or named_after.st_nlink != 1
            or before.st_dev != attempt.parent_identity[0]
        ):
            raise CaptureError("output:attempt-marker-drift")
        previous = attempt.marker_fd
        attempt.marker_fd = descriptor
        attempt.marker_identity = identity
        descriptor = -1
        if previous >= 0:
            os.close(previous)
    except CaptureError:
        raise
    except OSError as error:
        raise CaptureError("output:attempt-marker-drift") from error
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _verify_attempt_marker(attempt: _EnvironmentOutputAttempt) -> None:
    if attempt.marker_fd < 0 or attempt.marker_identity is None:
        raise CaptureError("output:attempt-marker-drift")
    try:
        _replay_attempt_parent(attempt)
        before = os.fstat(attempt.marker_fd)
        named_before = os.stat(
            ATTEMPT_MARKER_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        _read_exact_receipt_descriptor(
            attempt.marker_fd,
            attempt.marker_payload,
            problem="output:attempt-marker-drift",
        )
        after = os.fstat(attempt.marker_fd)
        named_after = os.stat(
            ATTEMPT_MARKER_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        if (
            _marker_stat_identity(before) != attempt.marker_identity
            or _marker_stat_identity(after) != attempt.marker_identity
            or _marker_stat_identity(named_before) != attempt.marker_identity
            or _marker_stat_identity(named_after) != attempt.marker_identity
            or before.st_nlink != 1
            or after.st_nlink != 1
            or named_before.st_nlink != 1
            or named_after.st_nlink != 1
            or before.st_dev != attempt.parent_identity[0]
        ):
            raise CaptureError("output:attempt-marker-drift")
    except OSError as error:
        raise CaptureError("output:attempt-marker-drift") from error


def _attempt_marker_absent(attempt: _EnvironmentOutputAttempt) -> None:
    try:
        os.stat(
            ATTEMPT_MARKER_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        pass
    except OSError as error:
        raise CaptureError("output:attempt-marker-probe") from error
    else:
        raise CaptureError("output:attempt-marker-still-present")
    if attempt.marker_fd < 0 or attempt.marker_identity is None:
        raise CaptureError("output:attempt-marker-probe")
    try:
        retained = os.fstat(attempt.marker_fd)
    except OSError as error:
        raise CaptureError("output:attempt-marker-probe") from error
    if (
        _marker_stat_identity(retained) != attempt.marker_identity
        or retained.st_nlink != 0
    ):
        raise CaptureError("output:attempt-marker-probe")


def _restore_attempt_marker(attempt: _EnvironmentOutputAttempt) -> None:
    """Durably restore nonauthority after a fault beyond marker removal."""

    attempt.issued_witness = None
    if _dir_entry_exists(attempt.parent_fd, ATTEMPT_MARKER_BASENAME):
        _bind_attempt_marker(attempt, synchronize_file=True)
    else:
        marker_fd = _exclusive_create_fsynced(
            attempt.parent_fd,
            ATTEMPT_MARKER_BASENAME,
            attempt.marker_payload,
            label="output:attempt-marker-restore",
        )
        try:
            os.close(marker_fd)
        except OSError as error:
            raise CaptureError(
                "output:attempt-marker-restore-close"
            ) from error
        _bind_attempt_marker(attempt, synchronize_file=False)
    _fsync_attempt_parent(attempt, label="attempt-marker-restore-sync")
    _replay_attempt_parent(attempt)
    _verify_attempt_marker(attempt)


def _restore_marker_or_raise_completion_ambiguous(
    attempt: _EnvironmentOutputAttempt,
    original_error: BaseException,
) -> None:
    try:
        _restore_attempt_marker(attempt)
    except BaseException:
        raise CaptureError("output:completion-ambiguous") from original_error


@dataclass(frozen=True)
class _CanonicalReceiptBinding:
    descriptor: int
    identity: tuple[int, int, int, int]
    payload_sha256: str


def _open_canonical_receipt_binding(
    attempt: _EnvironmentOutputAttempt,
    *,
    pending_info: os.stat_result,
    payload: bytes,
) -> _CanonicalReceiptBinding:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(
            CANONICAL_RECEIPT_BASENAME,
            flags,
            dir_fd=attempt.parent_fd,
        )
    except OSError as error:
        raise CaptureError(
            f"output:canonical-open:{type(error).__name__}"
        ) from error
    try:
        info = os.fstat(descriptor)
        identity = (info.st_dev, info.st_ino, info.st_mode, info.st_size)
        pending_identity = (
            pending_info.st_dev,
            pending_info.st_ino,
            pending_info.st_mode,
            pending_info.st_size,
        )
        if (
            identity != pending_identity
            or not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o444
            or info.st_size != len(payload)
            or info.st_nlink != 2
        ):
            raise CaptureError("output:canonical-link-drift")
        return _CanonicalReceiptBinding(
            descriptor=descriptor,
            identity=identity,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
        )
    except Exception:
        os.close(descriptor)
        raise


def _verify_canonical_receipt(
    attempt: _EnvironmentOutputAttempt,
    binding: _CanonicalReceiptBinding,
    payload: bytes,
    *,
    expected_link_count: int,
) -> None:
    try:
        _replay_attempt_parent(attempt)
        before = os.fstat(binding.descriptor)
        named = os.stat(
            CANONICAL_RECEIPT_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
        )
        named_identity = (
            named.st_dev,
            named.st_ino,
            named.st_mode,
            named.st_size,
        )
        if (
            before_identity != binding.identity
            or named_identity != binding.identity
            or not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(named.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o444
            or stat.S_IMODE(named.st_mode) != 0o444
            or before.st_size != len(payload)
            or named.st_size != len(payload)
            or before.st_nlink != expected_link_count
            or named.st_nlink != expected_link_count
        ):
            raise CaptureError("output:canonical-drift")
        os.lseek(binding.descriptor, 0, os.SEEK_SET)
        observed = bytearray()
        while len(observed) <= len(payload):
            chunk = os.read(
                binding.descriptor,
                len(payload) + 1 - len(observed),
            )
            if not chunk:
                break
            observed.extend(chunk)
        after = os.fstat(binding.descriptor)
        named_after = os.stat(
            CANONICAL_RECEIPT_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
        )
        named_after_identity = (
            named_after.st_dev,
            named_after.st_ino,
            named_after.st_mode,
            named_after.st_size,
        )
        observed_bytes = bytes(observed)
        if (
            after_identity != binding.identity
            or named_after_identity != binding.identity
            or not stat.S_ISREG(named_after.st_mode)
            or stat.S_IMODE(named_after.st_mode) != 0o444
            or after.st_nlink != expected_link_count
            or named_after.st_nlink != expected_link_count
            or observed_bytes != payload
            or hashlib.sha256(observed_bytes).hexdigest()
            != binding.payload_sha256
        ):
            raise CaptureError("output:canonical-drift")
        terminal_parent_fd = _open_physical_directory(attempt.parent_path)
        try:
            if _directory_identity(terminal_parent_fd) != attempt.parent_identity:
                raise CaptureError("output:parent-drift")
            terminal_named = os.stat(
                CANONICAL_RECEIPT_BASENAME,
                dir_fd=terminal_parent_fd,
                follow_symlinks=False,
            )
            terminal_identity = (
                terminal_named.st_dev,
                terminal_named.st_ino,
                terminal_named.st_mode,
                terminal_named.st_size,
            )
            if (
                terminal_identity != binding.identity
                or not stat.S_ISREG(terminal_named.st_mode)
                or stat.S_IMODE(terminal_named.st_mode) != 0o444
                or terminal_named.st_nlink != expected_link_count
            ):
                raise CaptureError("output:canonical-drift")
        finally:
            os.close(terminal_parent_fd)
        terminal_path = os.stat(attempt.output_path, follow_symlinks=False)
        terminal_path_identity = (
            terminal_path.st_dev,
            terminal_path.st_ino,
            terminal_path.st_mode,
            terminal_path.st_size,
        )
        if (
            terminal_path_identity != binding.identity
            or not stat.S_ISREG(terminal_path.st_mode)
            or stat.S_IMODE(terminal_path.st_mode) != 0o444
            or terminal_path.st_nlink != expected_link_count
        ):
            raise CaptureError("output:canonical-drift")
    except CaptureError:
        raise
    except OSError as error:
        raise CaptureError("output:canonical-drift") from error


def _verify_environment_receipt_pair(
    attempt: _EnvironmentOutputAttempt,
    binding: _CanonicalReceiptBinding,
    payload: bytes,
    *,
    marker_present: bool,
) -> _ReceiptPairObservation:
    """Couple both retained names, their shared inode, exact bytes, and the held parent."""

    _verify_canonical_receipt(
        attempt,
        binding,
        payload,
        expected_link_count=2,
    )
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        pending_fd = os.open(
            PENDING_RECEIPT_BASENAME,
            flags,
            dir_fd=attempt.parent_fd,
        )
    except OSError as error:
        raise CaptureError("output:pending-drift") from error
    try:
        before = os.fstat(pending_fd)
        named = os.stat(
            PENDING_RECEIPT_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
        )
        named_identity = (
            named.st_dev,
            named.st_ino,
            named.st_mode,
            named.st_size,
        )
        if (
            identity != binding.identity
            or named_identity != binding.identity
            or not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(named.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o444
            or stat.S_IMODE(named.st_mode) != 0o444
            or before.st_nlink != 2
            or named.st_nlink != 2
        ):
            raise CaptureError("output:pending-drift")
        _read_exact_receipt_descriptor(
            pending_fd,
            payload,
            problem="output:pending-drift",
        )
        after = os.fstat(pending_fd)
        if (
            (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_size,
            )
            != binding.identity
            or after.st_nlink != 2
        ):
            raise CaptureError("output:pending-drift")
    except OSError as error:
        raise CaptureError("output:pending-drift") from error
    finally:
        os.close(pending_fd)
    _replay_attempt_parent(attempt)
    if marker_present:
        _verify_attempt_marker(attempt)
    else:
        _attempt_marker_absent(attempt)
    # Repeat both name observations after the parent and marker replay.  This is the coupled
    # boundary from which the process-local completion witness is derived.
    _verify_canonical_receipt(
        attempt,
        binding,
        payload,
        expected_link_count=2,
    )
    pending_terminal = os.stat(
        PENDING_RECEIPT_BASENAME,
        dir_fd=attempt.parent_fd,
        follow_symlinks=False,
    )
    if (
        (
            pending_terminal.st_dev,
            pending_terminal.st_ino,
            pending_terminal.st_mode,
            pending_terminal.st_size,
        )
        != binding.identity
        or pending_terminal.st_nlink != 2
    ):
        raise CaptureError("output:pending-drift")
    if marker_present:
        _verify_attempt_marker(attempt)
    else:
        _attempt_marker_absent(attempt)
    return _ReceiptPairObservation(
        parent_identity=attempt.parent_identity,
        receipt_inode=(binding.identity[0], binding.identity[1]),
        byte_count=len(payload),
        payload_sha256=binding.payload_sha256,
    )


def _begin_environment_output_attempt(
    path: Path,
    *,
    expected_parent_identity: tuple[int, int, int] | None = None,
) -> _EnvironmentOutputAttempt:
    output_path = _output_path_contract(path)
    try:
        parent_fd = _open_physical_directory(output_path.parent)
        identity = _directory_identity(parent_fd)
    except CaptureError as error:
        raise EnvironmentAdmissionStop(str(error)) from error
    if expected_parent_identity is not None and identity != expected_parent_identity:
        os.close(parent_fd)
        raise EnvironmentAdmissionStop("output:preparation-parent-drift")
    try:
        entropy = os.urandom(64)
    except OSError as error:
        os.close(parent_fd)
        raise CaptureError("output:attempt-randomness") from error
    if (
        type(entropy) is not bytes
        or len(entropy) != 64
        or entropy[:32] == entropy[32:]
    ):
        os.close(parent_fd)
        raise CaptureError("output:attempt-randomness")
    attempt_id = entropy[:32].hex()
    completion_nonce = entropy[32:]
    attempt = _EnvironmentOutputAttempt(
        output_path=output_path,
        parent_path=output_path.parent,
        parent_fd=parent_fd,
        parent_identity=identity,
        attempt_id=attempt_id,
        completion_nonce=completion_nonce,
        marker_payload=_environment_attempt_marker_payload(
            attempt_id,
            identity,
        ),
    )
    try:
        if _dir_entry_exists(parent_fd, CANONICAL_RECEIPT_BASENAME):
            raise EnvironmentAdmissionStop("output:already-exists")
        if _dir_entry_exists(parent_fd, ATTEMPT_MARKER_BASENAME):
            raise EnvironmentAdmissionStop("output:attempt-marker-exists")
        if _dir_entry_exists(parent_fd, PENDING_RECEIPT_BASENAME):
            raise EnvironmentAdmissionStop("output:pending-exists")
        marker_fd = _exclusive_create_fsynced(
            parent_fd,
            ATTEMPT_MARKER_BASENAME,
            attempt.marker_payload,
            label="output:attempt-marker",
        )
        try:
            os.close(marker_fd)
        except OSError as error:
            raise CaptureError("output:attempt-marker-close") from error
        _bind_attempt_marker(attempt, synchronize_file=False)
        _fsync_attempt_parent(attempt, label="attempt-marker-sync")
        _replay_attempt_parent(attempt)
        _verify_attempt_marker(attempt)
        return attempt
    except Exception:
        attempt.close()
        raise


def _publish_environment_receipt(
    attempt: _EnvironmentOutputAttempt,
    value: Mapping[str, Any],
) -> EnvironmentReceiptCompletionWitness:
    """Disk-commit E as a retained hard-link pair and return a process witness.

    Marker absence plus the exact canonical+pending pair is the replayable disk-commit state.  It
    does not prove that this process returned.  The returned witness represents the process return
    boundary and is consumed by ``capture_environment_attempt`` before that function reports
    success.
    """

    payload = _serialize_receipt(value)
    verdict = value.get("verdict")
    if type(verdict) is not str:
        raise CaptureError("output:verdict")
    if _dir_entry_exists(attempt.parent_fd, CANONICAL_RECEIPT_BASENAME):
        raise CaptureError("output:already-exists")
    if _dir_entry_exists(attempt.parent_fd, PENDING_RECEIPT_BASENAME):
        raise CaptureError("output:pending-exists")
    _verify_attempt_marker(attempt)
    pending_fd = _exclusive_create_fsynced(
        attempt.parent_fd,
        PENDING_RECEIPT_BASENAME,
        payload,
        label="output:pending",
    )
    canonical_binding: _CanonicalReceiptBinding | None = None
    marker_removal_started = False
    try:
        pending_info = os.fstat(pending_fd)
        named_pending = os.stat(
            PENDING_RECEIPT_BASENAME,
            dir_fd=attempt.parent_fd,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(pending_info.st_mode)
            or stat.S_IMODE(pending_info.st_mode) != 0o444
            or pending_info.st_size != len(payload)
            or pending_info.st_nlink != 1
            or (
                pending_info.st_dev,
                pending_info.st_ino,
                pending_info.st_mode,
                pending_info.st_size,
            )
            != (
                named_pending.st_dev,
                named_pending.st_ino,
                named_pending.st_mode,
                named_pending.st_size,
            )
        ):
            raise CaptureError("output:pending-drift")
        _fsync_attempt_parent(attempt, label="pending-sync")
        _replay_attempt_parent(attempt)
        _verify_attempt_marker(attempt)
        try:
            os.close(pending_fd)
        except OSError as error:
            raise CaptureError(
                f"output:pending-close:{type(error).__name__}"
            ) from error
        pending_fd = -1
        try:
            os.link(
                PENDING_RECEIPT_BASENAME,
                CANONICAL_RECEIPT_BASENAME,
                src_dir_fd=attempt.parent_fd,
                dst_dir_fd=attempt.parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise CaptureError("output:already-exists") from error
        except OSError as error:
            raise CaptureError(f"output:link:{type(error).__name__}") from error
        canonical_binding = _open_canonical_receipt_binding(
            attempt,
            pending_info=pending_info,
            payload=payload,
        )
        _verify_environment_receipt_pair(
            attempt,
            canonical_binding,
            payload,
            marker_present=True,
        )
        _fsync_attempt_parent(attempt, label="canonical-link-sync")
        _verify_environment_receipt_pair(
            attempt,
            canonical_binding,
            payload,
            marker_present=True,
        )
        try:
            _verify_attempt_marker(attempt)
            marker_removal_started = True
            os.unlink(ATTEMPT_MARKER_BASENAME, dir_fd=attempt.parent_fd)
        except OSError as error:
            raise CaptureError(f"output:cleanup:{type(error).__name__}") from error
        _fsync_attempt_parent(attempt, label="cleanup-sync")
        observation = _verify_environment_receipt_pair(
            attempt,
            canonical_binding,
            payload,
            marker_present=False,
        )
        witness = EnvironmentReceiptCompletionWitness(
            attempt_id=attempt.attempt_id,
            completion_nonce=attempt.completion_nonce,
            verdict=verdict,
            parent_identity=observation.parent_identity,
            receipt_inode=observation.receipt_inode,
            byte_count=observation.byte_count,
            payload_sha256=observation.payload_sha256,
        )
        attempt.issued_witness = witness
        return witness
    except BaseException as error:
        if marker_removal_started:
            _restore_marker_or_raise_completion_ambiguous(attempt, error)
        if isinstance(error, OSError):
            raise CaptureError(
                f"output:publication:{type(error).__name__}"
            ) from error
        raise
    finally:
        if canonical_binding is not None:
            try:
                os.close(canonical_binding.descriptor)
            except OSError:
                pass
        if pending_fd >= 0:
            try:
                os.close(pending_fd)
            except OSError:
                pass


def _consume_environment_completion_witness(
    attempt: _EnvironmentOutputAttempt,
    receipt: Mapping[str, Any],
    witness: object,
) -> None:
    """Independently bind the publication return value to the replayed disk commit."""

    if attempt.completion_consumed:
        raise CaptureError("output:completion-witness-replayed")
    payload = _serialize_receipt(receipt)
    if (
        type(witness) is not EnvironmentReceiptCompletionWitness
        or witness is not attempt.issued_witness
        or type(witness.attempt_id) is not str
        or witness.attempt_id != attempt.attempt_id
        or type(witness.completion_nonce) is not bytes
        or len(witness.completion_nonce) != 32
        or witness.completion_nonce != attempt.completion_nonce
        or type(witness.verdict) is not str
        or witness.verdict != receipt.get("verdict")
        or type(witness.parent_identity) is not tuple
        or len(witness.parent_identity) != 3
        or any(type(item) is not int for item in witness.parent_identity)
        or type(witness.receipt_inode) is not tuple
        or len(witness.receipt_inode) != 2
        or any(type(item) is not int for item in witness.receipt_inode)
        or type(witness.byte_count) is not int
        or type(witness.payload_sha256) is not str
        or witness.parent_identity != attempt.parent_identity
        or witness.byte_count != len(payload)
        or witness.payload_sha256 != hashlib.sha256(payload).hexdigest()
    ):
        raise CaptureError("output:completion-witness")
    observation = _observe_receipt_pair(
        attempt.output_path,
        pending_basename=PENDING_RECEIPT_BASENAME,
        marker_basename=ATTEMPT_MARKER_BASENAME,
        payload=payload,
        problem_prefix="output:completion-replay",
    )
    if (
        witness.parent_identity != observation.parent_identity
        or witness.receipt_inode != observation.receipt_inode
        or witness.byte_count != observation.byte_count
        or witness.payload_sha256 != observation.payload_sha256
    ):
        raise CaptureError("output:completion-witness")
    attempt.completion_consumed = True
    attempt.issued_witness = None


def _capture_environment_attempt_admitted(
    contract: Contract,
    *,
    host_commit: str,
    local_free_bytes: int,
    admission: _EnvironmentAdmission,
    output_path: Path = DEFAULT_OUTPUT,
    patcher_path: Path = CANONICAL_PATCHER_PATH,
    hooks: Hooks = Hooks(),
) -> dict[str, Any]:
    attempt = _begin_environment_output_attempt(
        output_path,
        expected_parent_identity=admission.preparation_parent_identity,
    )
    try:
        receipt = _execute_admitted_capture(
            contract,
            host_commit=host_commit,
            local_free_bytes=local_free_bytes,
            host_preparation=admission.host_preparation,
            patcher_path=patcher_path,
            hooks=hooks,
        )
        try:
            witness = _publish_environment_receipt(attempt, receipt)
            _consume_environment_completion_witness(
                attempt,
                receipt,
                witness,
            )
        except BaseException as error:
            _restore_marker_or_raise_completion_ambiguous(attempt, error)
            raise
        return receipt
    finally:
        attempt.close()


def capture_environment_attempt(
    contract: Contract,
    *,
    host_commit: str,
    local_free_bytes: int,
    output_path: Path = DEFAULT_OUTPUT,
    patcher_path: Path = CANONICAL_PATCHER_PATH,
    hooks: Hooks = Hooks(),
) -> dict[str, Any]:
    admission = _admit_environment_attempt(hooks)
    return _capture_environment_attempt_admitted(
        contract,
        host_commit=host_commit,
        local_free_bytes=local_free_bytes,
        admission=admission,
        output_path=output_path,
        patcher_path=patcher_path,
        hooks=hooks,
    )


def _nonnegative_integer(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a base-10 integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def _commit(value: str) -> str:
    if _COMMIT_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be a lowercase 40-hex commit")
    return value


def _reexec_with_sanitized_environment() -> None:
    if os.environ.get("SENTINEL_I135_CAPTURE_SANITIZED") == "1":
        return
    script = Path(__file__).absolute()
    if script != HERE / "capture_environment135.py" or script.is_symlink():
        raise CaptureError("invocation:canonical-script")
    try:
        physical_interpreter = Path(sys.executable).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CaptureError("invocation:physical-interpreter") from error
    if physical_interpreter.is_symlink() or not physical_interpreter.is_file():
        raise CaptureError("invocation:physical-interpreter")
    os.execve(
        physical_interpreter,
        [str(physical_interpreter), "-I", str(script), *sys.argv[1:]],
        SANITIZED_ENVIRONMENT,
    )


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        try:
            _reexec_with_sanitized_environment()
        except CaptureError as error:
            print(f"I135_ENVIRONMENT_CAPTURE_FAIL {error}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-commit", required=True, type=_commit)
    parser.add_argument("--local-free-bytes", required=True, type=_nonnegative_integer)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        admission = _admit_environment_attempt(Hooks())
        _output_path_contract(args.output)
        contract = load_contract(
            CANONICAL_MANIFEST_PATH,
            expected_claim=admission.manifest_claim,
            expected_parent_identity=admission.preparation_parent_identity,
        )
        receipt = _capture_environment_attempt_admitted(
            contract,
            host_commit=args.host_commit,
            local_free_bytes=args.local_free_bytes,
            admission=admission,
            output_path=args.output,
        )
    except CaptureError as error:
        print(f"I135_ENVIRONMENT_CAPTURE_FAIL {error}", file=sys.stderr)
        return 2
    print(
        f"{receipt['verdict']} problems={receipt['problem_count']} output={args.output}",
        file=sys.stderr,
    )
    return 0 if receipt["problem_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
