#!/usr/bin/env python3
"""Prepare the exact Iteration-135 execution-host contract without launching work.

The controller is deliberately one-shot.  It accepts only the fixed staging and installation
paths, verifies an independently supplied packet-manifest digest, records every accepted
preimage, and records a red receipt for handled failures once the packet-bound mission state
admits a host-preparation attempt.  The attempt marker precedes every host observation or
mutation.  Receipt-publication faults fail closed and retain the marker and any pending inode;
they never return preparation authority.  A canonical leaf is nonauthoritative while the marker
exists, and marker absence alone is not a completion witness.  An unvalidated or non-executable
packet produces no H receipt.  The controller never starts or removes a container, touches the
GPU, resets a repository, deletes evidence, or retries a failed preparation.

POSIX cannot prevent a writer with directory authority from changing a name after the terminal
observation.  Nor can physical I/O failure guarantee that structured evidence reaches durable
storage.  The process completion witness consumed before public return binds the last coupled
parent/name/inode/byte observation; missing artifacts never prove that an attempt did not begin.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = "iter135.host_preparation_receipt.v1"
PACKET_SCHEMA = "iter135.host_packet_manifest.v1"
READY_VERDICT = "I135_HOST_PREPARATION_OK"
INCOMPLETE_VERDICT = "I135_HOST_PREPARATION_INCOMPLETE"
PUBLICATION_AUTHORITY_SCHEMA = "iter135.github_publication_authority.v1"
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
MAX_PROBLEM_TOKEN_BYTES = 512

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
RECEIPT_ATTEMPT_NAME = (
    f"{RECEIPT_NAME}.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE"
)
RECEIPT_PENDING_NAME = (
    f"{RECEIPT_NAME}.PENDING_RECEIPT_NONAUTHORITATIVE"
)
RECEIPT_ATTEMPT_SCHEMA = "iter135.host_preparation_attempt.v1"
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


class MissionStateStop(PreparationError):
    """The packet-bound mission state prohibits every live host action."""


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


def _exact_json_value(observed: object, expected: object) -> bool:
    """Compare JSON values without Python's bool/int or subclass equivalence."""

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


def _exception_kind(error: BaseException) -> str:
    """Map arbitrary exception classes to a fixed, bounded diagnostic vocabulary."""

    for kind in (
        TimeoutError,
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
        AssertionError,
        AttributeError,
        LookupError,
    ):
        if isinstance(error, kind):
            return kind.__name__
    return "Exception"


def _bounded_problem(error: BaseException) -> str:
    """Preserve internal contract tokens but never persist arbitrary exception prose."""

    if isinstance(error, PreparationError):
        try:
            candidate = str(error)
            if (
                candidate
                and len(candidate.encode("utf-8", errors="replace"))
                <= MAX_PROBLEM_TOKEN_BYTES
                and not any(ord(character) < 0x20 for character in candidate)
            ):
                return candidate
        except Exception:
            pass
        return "internal:PreparationError"
    return f"internal:{_exception_kind(error)}"


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


_POSITIVE_INTEGER_CONFIG_FIELDS = (
    "expected_server_bytes",
    "expected_compose_input_bytes",
    "expected_compose_output_bytes",
    "minimum_remote_free_bytes",
    "projected_output_bytes",
    "minimum_reserve_bytes",
)


def _validate_host_config_numeric_contract(config: HostConfig) -> None:
    values = tuple(
        getattr(config, field) for field in _POSITIVE_INTEGER_CONFIG_FIELDS
    )
    if any(type(value) is not int or value <= 0 for value in values):
        raise PreparationError("config:numeric-contract")
    if (
        config.projected_output_bytes + config.minimum_reserve_bytes
        > config.minimum_remote_free_bytes
    ):
        raise PreparationError("config:storage-capacity-contract")


def _rename_test_seam(_source: Path, _destination: Path) -> None:
    """Default no-op seam immediately before the controller's exclusive rename."""


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
    rename: Callable[[Path, Path], None] = _rename_test_seam


@dataclass
class _ReceiptTransaction:
    """Held attempt state; names alone never constitute completion authority."""

    parent_descriptor: int
    marker_descriptor: int
    parent_identity: tuple[int, int, int]
    marker_inode: tuple[int, int]
    marker_payload: bytes
    attempt_id: str
    marker_name: str
    pending_name: str
    canonical_name: str
    closed: bool = False


@dataclass(frozen=True)
class ReceiptCompletionWitness:
    """Process-returned binding for one fully replayed receipt publication."""

    attempt_id: str
    verdict: str
    parent_identity: tuple[int, int, int]
    receipt_inode: tuple[int, int]
    byte_count: int
    payload_sha256: str


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


def _directory_identity(row: os.stat_result) -> tuple[int, int, int]:
    return (row.st_dev, row.st_ino, row.st_mode)


def _capture_canonical_root_contract(
    config: HostConfig,
) -> dict[str, tuple[Path, tuple[int, int, int]]]:
    paths = {
        "stack-parent": config.packet_root.parent,
        "packet-root": config.packet_root,
        "uniad-root": config.uniad_repo,
        "neuroncap-root": config.neuroncap_repo,
        "neurad-root": config.neurad_repo,
        "dataset-root": config.dataset_root,
        "analytic-root": config.analytic_root,
    }
    contract: dict[str, tuple[Path, tuple[int, int, int]]] = {}
    for label, candidate in paths.items():
        path = Path(candidate).absolute()
        row = _physical_directory(path, f"canonical-root:{label}")
        contract[label] = (path, _directory_identity(row))
    if len({path for path, _identity_row in contract.values()}) != len(contract):
        raise PreparationError("canonical-root:path-alias")
    return contract


def _replay_canonical_root_contract(
    config: HostConfig,
    contract: Mapping[str, tuple[Path, tuple[int, int, int]]],
    *,
    installed: bool | None,
) -> None:
    expected_labels = {
        "stack-parent",
        "packet-root",
        "uniad-root",
        "neuroncap-root",
        "neurad-root",
        "dataset-root",
        "analytic-root",
    }
    if set(contract) != expected_labels:
        raise PreparationError("canonical-root:contract")
    for label in sorted(expected_labels):
        if label == "packet-root" and installed is None:
            continue
        expected_path, expected_identity = contract[label]
        observed_path = (
            config.install_root
            if label == "packet-root" and installed
            else expected_path
        )
        row = _physical_directory(observed_path, f"canonical-root:{label}:replay")
        if _directory_identity(row) != expected_identity:
            raise PreparationError(f"canonical-root:{label}:identity")
    if installed is True and os.path.lexists(config.packet_root):
        raise PreparationError("canonical-root:packet-source-survived")


def _open_bound_install_parent(
    config: HostConfig,
    expected_identity: tuple[int, int, int],
) -> tuple[int, str, str]:
    packet_root = Path(config.packet_root).absolute()
    install_root = Path(config.install_root).absolute()
    if (
        packet_root.parent != install_root.parent
        or packet_root == install_root
        or packet_root.name in {"", ".", ".."}
        or install_root.name in {"", ".", ".."}
        or "/" in packet_root.name
        or "/" in install_root.name
    ):
        raise PreparationError("packet:install-parent-contract")
    descriptor = os.open(
        packet_root.parent,
        os.O_RDONLY
        | os.O_CLOEXEC
        | os.O_DIRECTORY
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        observed = os.fstat(descriptor)
        canonical = _physical_directory(
            packet_root.parent,
            "packet:install-parent",
        )
        if (
            not stat.S_ISDIR(observed.st_mode)
            or _directory_identity(observed) != expected_identity
            or _directory_identity(canonical) != expected_identity
        ):
            raise PreparationError("packet:install-parent-identity")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, packet_root.name, install_root.name


def _replay_bound_install_parent(
    config: HostConfig,
    descriptor: int,
    expected_identity: tuple[int, int, int],
) -> None:
    held = os.fstat(descriptor)
    canonical = _physical_directory(
        config.packet_root.parent,
        "packet:install-parent-replay",
    )
    if (
        not stat.S_ISDIR(held.st_mode)
        or _directory_identity(held) != expected_identity
        or _directory_identity(canonical) != expected_identity
    ):
        raise PreparationError("packet:install-parent-identity")


def _directory_entry_identity_at(
    descriptor: int,
    name: str,
    *,
    label: str,
) -> tuple[int, int, int] | None:
    try:
        row = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise PreparationError(f"packet:{label}:stat") from error
    if not stat.S_ISDIR(row.st_mode):
        raise PreparationError(f"packet:{label}:not-directory")
    return _directory_identity(row)


def _exclusive_rename_at(
    descriptor: int,
    source_name: str,
    destination_name: str,
) -> None:
    """Rename one sibling directory without replacing any destination entry."""

    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        try:
            rename = library.renameatx_np
        except AttributeError as error:
            raise PreparationError("packet:exclusive-install-unsupported") from error
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        arguments = (
            descriptor,
            os.fsencode(source_name),
            descriptor,
            os.fsencode(destination_name),
            0x00000004,
        )
    elif sys.platform.startswith("linux"):
        try:
            rename = library.renameat2
        except AttributeError as error:
            raise PreparationError("packet:exclusive-install-unsupported") from error
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        arguments = (
            descriptor,
            os.fsencode(source_name),
            descriptor,
            os.fsencode(destination_name),
            0x00000001,
        )
    else:
        raise PreparationError("packet:exclusive-install-unsupported")
    ctypes.set_errno(0)
    if rename(*arguments) == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise PreparationError("packet:install-root-race")
    unsupported = {
        errno.ENOSYS,
        errno.EINVAL,
        getattr(errno, "ENOTSUP", errno.EINVAL),
        getattr(errno, "EOPNOTSUPP", errno.EINVAL),
    }
    if error_number in unsupported:
        raise PreparationError("packet:exclusive-install-unsupported")
    if error_number == errno.ENOENT:
        raise PreparationError("packet:exclusive-install-binding")
    raise PreparationError("packet:exclusive-install-failed")


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
            or not _exact_json_value(claimed.get("sha256"), row["sha256"])
            or not _exact_json_value(claimed.get("bytes"), row["bytes"])
            or not _exact_json_value(claimed.get("mode"), row["mode"])
            or not _exact_json_value(row["mode"], modes[name])
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


def validate_packet_mission_state(
    config: HostConfig,
    packet_files: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Require the complete canonical execution contract before any live host action."""

    claimed = packet_files.get("MISSION_STATE.json")
    if not isinstance(claimed, Mapping):
        raise MissionStateStop("mission-state:packet-binding")
    observed, payload = stable_file(
        config.packet_root / "MISSION_STATE.json",
        collect_bytes=True,
    )
    if payload is None or observed != claimed:
        raise MissionStateStop("mission-state:packet-binding")
    try:
        state = json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise MissionStateStop(
            f"mission-state:json:{type(error).__name__}"
        ) from error
    if type(state) is not dict:
        raise MissionStateStop("mission-state:document")
    if set(state) != EXPECTED_MISSION_STATE_FIELDS:
        raise MissionStateStop("mission-state:field-set")
    if state.get("schema") != MISSION_STATE_SCHEMA:
        raise MissionStateStop("mission-state:schema")
    next_program = state.get("next_program")
    if type(next_program) is not dict or set(next_program) != EXPECTED_NEXT_PROGRAM_FIELDS:
        raise MissionStateStop("mission-state:next-program-field-set")
    phase = next_program.get("phase")
    if type(phase) is not str or phase not in MISSION_PHASE_CONTRACTS:
        raise MissionStateStop("mission-state:phase")
    phase_contract = MISSION_PHASE_CONTRACTS[phase]
    for field, expected in EXPECTED_MISSION_STATE_COMMON.items():
        if not _exact_json_value(state.get(field), expected):
            raise MissionStateStop("mission-state:contract")
    if not _exact_json_value(state.get("run_state"), phase_contract["run_state"]):
        raise MissionStateStop("mission-state:run-state")
    expected_next_program = {
        "iteration": 135,
        "name": "semantics-free placebo dose-response causal closure",
        "phase": phase,
        "authorized_actions": list(phase_contract["authorized_actions"]),
        "forbidden_actions": list(phase_contract["forbidden_actions"]),
    }
    if not _exact_json_value(next_program, expected_next_program):
        raise MissionStateStop("mission-state:next-program")
    if phase == CONTROL_HARDENING_PHASE:
        raise MissionStateStop("mission-state:control-hardening-required")
    if phase == PREREGISTERED_PHASE:
        raise MissionStateStop("mission-state:preregistered-tooling-required")
    return state


def revalidate_packet_payloads(
    config: HostConfig,
    root: Path,
    expected_files: Mapping[str, Mapping[str, Any]],
    expected_manifest_sha256: str,
    *,
    label: str,
    receipt_pair_present: bool = False,
) -> None:
    """Replay every staged byte and mode at a mutation boundary."""

    if type(receipt_pair_present) is not bool:
        raise PreparationError(f"packet:revalidation:{label}:contract")
    _physical_directory(root, f"packet-revalidation:{label}:root")
    marker_name, pending_name = _receipt_auxiliary_names(config.receipt_name)
    expected_entries = {
        config.packet_manifest_name,
        *config.required_packet_files,
        marker_name,
    }
    if receipt_pair_present:
        expected_entries.update((pending_name, config.receipt_name))
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
    if (
        type(dataset_device) is not int
        or type(root_device) is not int
        or dataset_device != root_info.st_dev
        or dataset_device == root_device
    ):
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


def _receipt_file_payload(receipt: Mapping[str, Any]) -> bytes:
    return (json.dumps(receipt, indent=1, sort_keys=True) + "\n").encode("utf-8")


def _receipt_auxiliary_names(canonical_name: str) -> tuple[str, str]:
    if (
        type(canonical_name) is not str
        or canonical_name in {"", ".", ".."}
        or "/" in canonical_name
        or "\0" in canonical_name
    ):
        raise PreparationError("receipt:path")
    return (
        f"{canonical_name}.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE",
        f"{canonical_name}.PENDING_RECEIPT_NONAUTHORITATIVE",
    )


def _replay_bound_receipt_parent(
    parent: Path,
    descriptor: int,
    expected_parent_identity: tuple[int, int, int],
    expected_packet_identity: tuple[int, int, int] | None,
) -> None:
    try:
        held = os.fstat(descriptor)
    except OSError as error:
        raise PreparationError("receipt-parent:descriptor") from error
    canonical = _physical_directory(parent, "receipt-parent-replay")
    held_identity = _directory_identity(held)
    if (
        not stat.S_ISDIR(held.st_mode)
        or held_identity != expected_parent_identity
        or _directory_identity(canonical) != expected_parent_identity
        or (
            expected_packet_identity is not None
            and held_identity != expected_packet_identity
        )
    ):
        raise PreparationError("receipt-parent:identity")


def _open_bound_receipt_parent(
    parent: Path,
    expected_parent_identity: tuple[int, int, int] | None,
    expected_packet_identity: tuple[int, int, int] | None,
) -> tuple[int, tuple[int, int, int]]:
    parent = Path(parent).absolute()
    validated = _physical_directory(parent, "receipt-parent")
    validated_identity = _directory_identity(validated)
    if (
        expected_parent_identity is not None
        and validated_identity != expected_parent_identity
    ):
        raise PreparationError("receipt-parent:identity")
    if (
        expected_packet_identity is not None
        and validated_identity != expected_packet_identity
    ):
        raise PreparationError("receipt-parent:packet-identity")
    try:
        descriptor = os.open(
            parent,
            os.O_RDONLY
            | os.O_CLOEXEC
            | os.O_DIRECTORY
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as error:
        raise PreparationError("receipt-parent:open") from error
    try:
        _replay_bound_receipt_parent(
            parent,
            descriptor,
            validated_identity,
            expected_packet_identity,
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, validated_identity


def _write_receipt_payload(descriptor: int, payload: bytes) -> None:
    written = 0
    while written < len(payload):
        try:
            count = os.write(descriptor, payload[written:])
        except OSError as error:
            raise PreparationError("receipt:write") from error
        if type(count) is not int or count <= 0:
            raise PreparationError("receipt:short-write")
        written += count
    if written != len(payload):
        raise PreparationError("receipt:short-write")


def _fsync_receipt_descriptor(descriptor: int, problem: str) -> None:
    try:
        os.fsync(descriptor)
    except OSError as error:
        raise PreparationError(problem) from error


def _create_durable_analytic_root(
    config: HostConfig,
    *,
    expected_dataset_device: int,
) -> os.stat_result:
    """Create the analytic root through a bound dataset descriptor and sync its name."""

    dataset_root = Path(config.dataset_root).absolute()
    analytic_root = Path(config.analytic_root).absolute()
    if (
        analytic_root.parent != dataset_root
        or analytic_root.name in {"", ".", ".."}
        or "/" in analytic_root.name
    ):
        raise PreparationError("storage:analytic-root-parent-contract")
    dataset_row = _physical_directory(dataset_root, "storage:analytic-root-parent")
    dataset_identity = _directory_identity(dataset_row)
    if dataset_row.st_dev != expected_dataset_device:
        raise PreparationError("storage:analytic-root-parent-identity")
    try:
        parent_descriptor = os.open(
            dataset_root,
            os.O_RDONLY
            | os.O_CLOEXEC
            | os.O_DIRECTORY
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as error:
        raise PreparationError("storage:analytic-root-parent-open") from error
    try:
        held = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(held.st_mode)
            or _directory_identity(held) != dataset_identity
        ):
            raise PreparationError("storage:analytic-root-parent-identity")
        try:
            os.mkdir(
                analytic_root.name,
                0o755,
                dir_fd=parent_descriptor,
            )
        except OSError as error:
            raise PreparationError("storage:analytic-root-create") from error
        try:
            created = os.stat(
                analytic_root.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as error:
            raise PreparationError("storage:analytic-root-created-stat") from error
        if (
            not stat.S_ISDIR(created.st_mode)
            or created.st_dev != expected_dataset_device
        ):
            raise PreparationError("storage:analytic-root-created-identity")
        created_identity = _directory_identity(created)
        _fsync_receipt_descriptor(
            parent_descriptor,
            "storage:analytic-root-parent-fsync",
        )
        canonical_parent = _physical_directory(
            dataset_root,
            "storage:analytic-root-parent-replay",
        )
        if (
            _directory_identity(os.fstat(parent_descriptor)) != dataset_identity
            or _directory_identity(canonical_parent) != dataset_identity
        ):
            raise PreparationError("storage:analytic-root-parent-identity")
        try:
            replayed = os.stat(
                analytic_root.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as error:
            raise PreparationError("storage:analytic-root-replay-stat") from error
        canonical_root = _physical_directory(analytic_root, "analytic-root")
        if (
            _directory_identity(replayed) != created_identity
            or _directory_identity(canonical_root) != created_identity
        ):
            raise PreparationError("storage:analytic-root-created-identity")
        return canonical_root
    finally:
        os.close(parent_descriptor)


def _read_receipt_payload(descriptor: int, expected_bytes: int) -> bytes:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
    except OSError as error:
        raise PreparationError("receipt:seek") from error
    chunks: list[bytes] = []
    observed_bytes = 0
    while observed_bytes <= expected_bytes:
        try:
            chunk = os.read(
                descriptor,
                min(1 << 20, expected_bytes + 1 - observed_bytes),
            )
        except OSError as error:
            raise PreparationError("receipt:read") from error
        if not chunk:
            break
        chunks.append(chunk)
        observed_bytes += len(chunk)
    return b"".join(chunks)


def _verify_open_receipt(
    descriptor: int,
    payload: bytes,
    parent_identity: tuple[int, int, int],
    expected_inode: tuple[int, int] | None = None,
    *,
    expected_nlink: int = 1,
    problem_prefix: str = "receipt:leaf",
) -> tuple[int, int]:
    try:
        before = os.fstat(descriptor)
    except OSError as error:
        raise PreparationError(f"{problem_prefix}-stat") from error
    observed_identity = _identity(before)
    observed_inode = (before.st_dev, before.st_ino)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != expected_nlink
        or before.st_dev != parent_identity[0]
        or stat.S_IMODE(before.st_mode) != 0o444
        or before.st_size != len(payload)
        or (
            expected_inode is not None
            and observed_inode != expected_inode
        )
    ):
        raise PreparationError(f"{problem_prefix}-identity")
    observed_payload = _read_receipt_payload(descriptor, len(payload))
    try:
        after = os.fstat(descriptor)
    except OSError as error:
        raise PreparationError(f"{problem_prefix}-stat") from error
    if (
        observed_payload != payload
        or _identity(after) != observed_identity
        or after.st_nlink != expected_nlink
    ):
        raise PreparationError(f"{problem_prefix}-content")
    return observed_inode


def _open_receipt_leaf_at(
    parent_descriptor: int,
    name: str,
    *,
    problem_prefix: str,
) -> int:
    try:
        return os.open(
            name,
            os.O_RDONLY
            | os.O_CLOEXEC
            | os.O_NONBLOCK
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
    except FileNotFoundError as error:
        raise PreparationError(f"{problem_prefix}-missing") from error
    except OSError as error:
        raise PreparationError(f"{problem_prefix}-open") from error


def _named_receipt_leaf(
    parent_descriptor: int,
    name: str,
    payload: bytes,
    parent_identity: tuple[int, int, int],
    expected_inode: tuple[int, int],
    *,
    expected_nlink: int,
    problem_prefix: str,
) -> None:
    try:
        row = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError as error:
        raise PreparationError(f"{problem_prefix}-missing") from error
    except OSError as error:
        raise PreparationError(f"{problem_prefix}-stat") from error
    if (
        not stat.S_ISREG(row.st_mode)
        or (row.st_dev, row.st_ino) != expected_inode
        or row.st_dev != parent_identity[0]
        or stat.S_IMODE(row.st_mode) != 0o444
        or row.st_size != len(payload)
        or row.st_nlink != expected_nlink
    ):
        raise PreparationError(f"{problem_prefix}-identity")


def _entry_absent_at(
    parent_descriptor: int,
    name: str,
    *,
    problem: str,
) -> None:
    try:
        os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as error:
        raise PreparationError(problem) from error
    raise PreparationError(problem)


def _verify_receipt_leaf_at(
    parent_descriptor: int,
    name: str,
    payload: bytes,
    parent_identity: tuple[int, int, int],
    expected_inode: tuple[int, int],
    *,
    expected_nlink: int = 1,
    problem_prefix: str = "receipt:leaf",
) -> None:
    descriptor = _open_receipt_leaf_at(
        parent_descriptor,
        name,
        problem_prefix=problem_prefix,
    )
    try:
        _verify_open_receipt(
            descriptor,
            payload,
            parent_identity,
            expected_inode,
            expected_nlink=expected_nlink,
            problem_prefix=problem_prefix,
        )
        _named_receipt_leaf(
            parent_descriptor,
            name,
            payload,
            parent_identity,
            expected_inode,
            expected_nlink=expected_nlink,
            problem_prefix=problem_prefix,
        )
    finally:
        os.close(descriptor)


def _attempt_marker_payload(
    *,
    attempt_id: str,
    source_commit: str,
    packet_manifest_sha256: str,
    parent_identity: tuple[int, int, int],
    canonical_name: str,
    pending_name: str,
) -> bytes:
    marker = {
        "schema": RECEIPT_ATTEMPT_SCHEMA,
        "status": "ATTEMPT_IN_PROGRESS_NO_HOST_PREPARATION_VERDICT",
        "attempt_id": attempt_id,
        "source_commit": source_commit,
        "packet_manifest_sha256": packet_manifest_sha256,
        "parent_identity": {
            "st_dev": parent_identity[0],
            "st_ino": parent_identity[1],
            "st_mode": parent_identity[2],
        },
        "canonical_receipt_name": canonical_name,
        "pending_receipt_name": pending_name,
    }
    return _receipt_file_payload(marker)


def _begin_receipt_transaction(
    parent: Path,
    *,
    canonical_name: str,
    source_commit: str,
    packet_manifest_sha256: str,
    expected_parent_identity: tuple[int, int, int] | None = None,
) -> _ReceiptTransaction:
    """Durably mark one admitted attempt before any host observation or mutation."""

    if type(source_commit) is not str or not _COMMIT_RE.fullmatch(source_commit):
        raise PreparationError("receipt:attempt-source-commit")
    if (
        type(packet_manifest_sha256) is not str
        or not _SHA256_RE.fullmatch(packet_manifest_sha256)
    ):
        raise PreparationError("receipt:attempt-manifest-sha256")
    marker_name, pending_name = _receipt_auxiliary_names(canonical_name)
    parent = Path(parent).absolute()
    parent_descriptor, parent_identity = _open_bound_receipt_parent(
        parent,
        expected_parent_identity,
        expected_parent_identity,
    )
    marker_descriptor = -1
    try:
        for name in (marker_name, pending_name, canonical_name):
            _entry_absent_at(
                parent_descriptor,
                name,
                problem="receipt:attempt-already-exists",
            )
        try:
            attempt_id = os.urandom(32).hex()
        except OSError as error:
            raise PreparationError("receipt:attempt-id") from error
        if not _SHA256_RE.fullmatch(attempt_id):
            raise PreparationError("receipt:attempt-id")
        marker_payload = _attempt_marker_payload(
            attempt_id=attempt_id,
            source_commit=source_commit,
            packet_manifest_sha256=packet_manifest_sha256,
            parent_identity=parent_identity,
            canonical_name=canonical_name,
            pending_name=pending_name,
        )
        try:
            marker_descriptor = os.open(
                marker_name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent_descriptor,
            )
        except FileExistsError as error:
            raise PreparationError("receipt:attempt-already-exists") from error
        except OSError as error:
            raise PreparationError("receipt:attempt-create") from error
        _write_receipt_payload(marker_descriptor, marker_payload)
        try:
            os.fchmod(marker_descriptor, 0o444)
        except OSError as error:
            raise PreparationError("receipt:attempt-mode") from error
        _fsync_receipt_descriptor(
            marker_descriptor,
            "receipt:attempt-file-fsync",
        )
        marker_inode = _verify_open_receipt(
            marker_descriptor,
            marker_payload,
            parent_identity,
            expected_nlink=1,
            problem_prefix="receipt:attempt",
        )
        _verify_receipt_leaf_at(
            parent_descriptor,
            marker_name,
            marker_payload,
            parent_identity,
            marker_inode,
            problem_prefix="receipt:attempt",
        )
        _fsync_receipt_descriptor(
            parent_descriptor,
            "receipt:attempt-parent-fsync",
        )
        _replay_bound_receipt_parent(
            parent,
            parent_descriptor,
            parent_identity,
            parent_identity,
        )
        _verify_receipt_leaf_at(
            parent_descriptor,
            marker_name,
            marker_payload,
            parent_identity,
            marker_inode,
            problem_prefix="receipt:attempt",
        )
        return _ReceiptTransaction(
            parent_descriptor=parent_descriptor,
            marker_descriptor=marker_descriptor,
            parent_identity=parent_identity,
            marker_inode=marker_inode,
            marker_payload=marker_payload,
            attempt_id=attempt_id,
            marker_name=marker_name,
            pending_name=pending_name,
            canonical_name=canonical_name,
        )
    except Exception:
        if marker_descriptor >= 0:
            try:
                os.close(marker_descriptor)
            except OSError:
                pass
        try:
            os.close(parent_descriptor)
        except OSError:
            pass
        raise


def _close_receipt_transaction(transaction: _ReceiptTransaction) -> None:
    if transaction.closed:
        return
    for descriptor in (
        transaction.marker_descriptor,
        transaction.parent_descriptor,
    ):
        try:
            os.close(descriptor)
        except OSError:
            # All required file and directory syncs precede this best-effort descriptor release.
            pass
    transaction.closed = True


def _replay_attempt_marker(
    transaction: _ReceiptTransaction,
    parent: Path,
    expected_packet_identity: tuple[int, int, int] | None,
) -> None:
    if transaction.closed:
        raise PreparationError("receipt:transaction-closed")
    _replay_bound_receipt_parent(
        parent,
        transaction.parent_descriptor,
        transaction.parent_identity,
        expected_packet_identity,
    )
    _verify_open_receipt(
        transaction.marker_descriptor,
        transaction.marker_payload,
        transaction.parent_identity,
        transaction.marker_inode,
        expected_nlink=1,
        problem_prefix="receipt:attempt",
    )
    _verify_receipt_leaf_at(
        transaction.parent_descriptor,
        transaction.marker_name,
        transaction.marker_payload,
        transaction.parent_identity,
        transaction.marker_inode,
        problem_prefix="receipt:attempt",
    )


def _restore_attempt_marker(
    transaction: _ReceiptTransaction,
    parent: Path,
    expected_packet_identity: tuple[int, int, int] | None,
) -> None:
    """Durably restore the nonauthority marker after an incomplete completion."""

    if transaction.closed:
        raise PreparationError("receipt:transaction-closed")
    _replay_bound_receipt_parent(
        parent,
        transaction.parent_descriptor,
        transaction.parent_identity,
        expected_packet_identity,
    )
    replacement_descriptor = -1
    try:
        try:
            replacement_descriptor = os.open(
                transaction.marker_name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=transaction.parent_descriptor,
            )
        except FileExistsError:
            replacement_descriptor = _open_receipt_leaf_at(
                transaction.parent_descriptor,
                transaction.marker_name,
                problem_prefix="receipt:attempt-restore",
            )
        except OSError as error:
            raise PreparationError("receipt:attempt-restore-create") from error
        created = os.fstat(replacement_descriptor)
        if created.st_size == 0 and stat.S_IMODE(created.st_mode) == 0o600:
            _write_receipt_payload(
                replacement_descriptor,
                transaction.marker_payload,
            )
            try:
                os.fchmod(replacement_descriptor, 0o444)
            except OSError as error:
                raise PreparationError("receipt:attempt-restore-mode") from error
        _fsync_receipt_descriptor(
            replacement_descriptor,
            "receipt:attempt-restore-file-fsync",
        )
        replacement_inode = _verify_open_receipt(
            replacement_descriptor,
            transaction.marker_payload,
            transaction.parent_identity,
            expected_nlink=1,
            problem_prefix="receipt:attempt-restore",
        )
        _verify_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.marker_name,
            transaction.marker_payload,
            transaction.parent_identity,
            replacement_inode,
            problem_prefix="receipt:attempt-restore",
        )
        _fsync_receipt_descriptor(
            transaction.parent_descriptor,
            "receipt:attempt-restore-parent-fsync",
        )
        _replay_bound_receipt_parent(
            parent,
            transaction.parent_descriptor,
            transaction.parent_identity,
            expected_packet_identity,
        )
        _verify_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.marker_name,
            transaction.marker_payload,
            transaction.parent_identity,
            replacement_inode,
            problem_prefix="receipt:attempt-restore",
        )
        previous_descriptor = transaction.marker_descriptor
        transaction.marker_descriptor = replacement_descriptor
        transaction.marker_inode = replacement_inode
        replacement_descriptor = -1
        try:
            os.close(previous_descriptor)
        except OSError:
            pass
        _replay_attempt_marker(
            transaction,
            parent,
            expected_packet_identity,
        )
    finally:
        if replacement_descriptor >= 0:
            try:
                os.close(replacement_descriptor)
            except OSError:
                pass


def _restore_marker_or_raise_completion_ambiguous(
    transaction: _ReceiptTransaction,
    parent: Path,
    expected_packet_identity: tuple[int, int, int] | None,
    original_error: BaseException,
) -> None:
    try:
        _restore_attempt_marker(
            transaction,
            parent,
            expected_packet_identity,
        )
    except BaseException:
        raise PreparationError("receipt:completion-ambiguous") from original_error


def _ensure_attempt_marker_after_publication_error(
    transaction: _ReceiptTransaction,
    parent: Path,
    expected_packet_identity: tuple[int, int, int] | None,
    original_error: BaseException,
) -> None:
    """Retain one marker without recursively replaying a completed restoration."""

    try:
        os.stat(
            transaction.marker_name,
            dir_fd=transaction.parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        _restore_marker_or_raise_completion_ambiguous(
            transaction,
            parent,
            expected_packet_identity,
            original_error,
        )
        return
    except BaseException:
        raise PreparationError("receipt:completion-ambiguous") from original_error
    try:
        # Any retained marker name denies downstream disk authority.  Sync that name through the
        # held parent rather than re-entering restoration or requiring a canonical pathname that
        # may itself be the reason publication failed.
        _fsync_receipt_descriptor(
            transaction.parent_descriptor,
            "receipt:attempt-recovery-parent-fsync",
        )
        os.stat(
            transaction.marker_name,
            dir_fd=transaction.parent_descriptor,
            follow_symlinks=False,
        )
    except BaseException:
        raise PreparationError("receipt:completion-ambiguous") from original_error


def _validate_receipt_completion_witness(
    witness: ReceiptCompletionWitness,
    transaction: _ReceiptTransaction,
    path: Path,
    receipt: Mapping[str, Any],
    expected_packet_identity: tuple[int, int, int] | None,
) -> None:
    """Consume the process witness with exact types before releasing public authority."""

    payload = _receipt_file_payload(receipt)
    verdict = receipt.get("verdict")
    parent_identity = transaction.parent_identity
    if (
        type(witness) is not ReceiptCompletionWitness
        or type(witness.attempt_id) is not str
        or witness.attempt_id != transaction.attempt_id
        or type(witness.verdict) is not str
        or witness.verdict != verdict
        or type(witness.parent_identity) is not tuple
        or len(witness.parent_identity) != 3
        or any(type(value) is not int for value in witness.parent_identity)
        or witness.parent_identity != parent_identity
        or type(witness.receipt_inode) is not tuple
        or len(witness.receipt_inode) != 2
        or any(type(value) is not int for value in witness.receipt_inode)
        or witness.receipt_inode[0] != parent_identity[0]
        or type(witness.byte_count) is not int
        or witness.byte_count != len(payload)
        or type(witness.payload_sha256) is not str
        or witness.payload_sha256 != hashlib.sha256(payload).hexdigest()
    ):
        raise PreparationError("receipt:completion-witness")
    _replay_published_receipt(
        path,
        receipt,
        expected_parent_identity=transaction.parent_identity,
        expected_packet_identity=expected_packet_identity,
        expected_leaf_identity=witness.receipt_inode,
    )


def _receipt_pair_observation(
    transaction: _ReceiptTransaction,
    parent: Path,
    payload: bytes,
    receipt_inode: tuple[int, int],
    expected_packet_identity: tuple[int, int, int] | None,
    *,
    marker_absent: bool,
) -> tuple[int, int]:
    """Couple the held parent, canonical path, both names, one inode, and exact bytes."""

    pending_descriptor = _open_receipt_leaf_at(
        transaction.parent_descriptor,
        transaction.pending_name,
        problem_prefix="receipt:pending",
    )
    canonical_descriptor = -1
    try:
        canonical_descriptor = _open_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.canonical_name,
            problem_prefix="receipt:canonical",
        )
        for descriptor, prefix in (
            (pending_descriptor, "receipt:pending"),
            (canonical_descriptor, "receipt:canonical"),
        ):
            _verify_open_receipt(
                descriptor,
                payload,
                transaction.parent_identity,
                receipt_inode,
                expected_nlink=2,
                problem_prefix=prefix,
            )
        for name, prefix in (
            (transaction.pending_name, "receipt:pending"),
            (transaction.canonical_name, "receipt:canonical"),
        ):
            _named_receipt_leaf(
                transaction.parent_descriptor,
                name,
                payload,
                transaction.parent_identity,
                receipt_inode,
                expected_nlink=2,
                problem_prefix=prefix,
            )
        if marker_absent:
            _entry_absent_at(
                transaction.parent_descriptor,
                transaction.marker_name,
                problem="receipt:attempt-still-present",
            )
        else:
            _replay_attempt_marker(
                transaction,
                parent,
                expected_packet_identity,
            )
        _replay_bound_receipt_parent(
            parent,
            transaction.parent_descriptor,
            transaction.parent_identity,
            expected_packet_identity,
        )
        # These are the terminal coupled observations.  There is deliberately no test hook,
        # callback, or pathname lookup after them.
        for descriptor, name, prefix in (
            (
                pending_descriptor,
                transaction.pending_name,
                "receipt:pending",
            ),
            (
                canonical_descriptor,
                transaction.canonical_name,
                "receipt:canonical",
            ),
        ):
            _verify_open_receipt(
                descriptor,
                payload,
                transaction.parent_identity,
                receipt_inode,
                expected_nlink=2,
                problem_prefix=prefix,
            )
            _named_receipt_leaf(
                transaction.parent_descriptor,
                name,
                payload,
                transaction.parent_identity,
                receipt_inode,
                expected_nlink=2,
                problem_prefix=prefix,
            )
        if marker_absent:
            _entry_absent_at(
                transaction.parent_descriptor,
                transaction.marker_name,
                problem="receipt:attempt-still-present",
            )
        return receipt_inode
    finally:
        for descriptor in (canonical_descriptor, pending_descriptor):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def _commit_receipt_transaction(
    transaction: _ReceiptTransaction,
    path: Path,
    receipt: Mapping[str, Any],
    *,
    expected_parent_identity: tuple[int, int, int] | None = None,
    expected_packet_identity: tuple[int, int, int] | None = None,
    terminal_validate: Callable[[], None],
    hooks: Hooks = Hooks(),
) -> ReceiptCompletionWitness:
    """Publish through pending+hard-link and return only after the terminal coupled replay."""

    path = Path(path).absolute()
    parent = path.parent
    if (
        path != parent / transaction.canonical_name
        or path.name != transaction.canonical_name
        or (
            expected_parent_identity is not None
            and expected_parent_identity != transaction.parent_identity
        )
    ):
        raise PreparationError("receipt:path")
    payload = _receipt_file_payload(receipt)
    verdict = receipt.get("verdict")
    if type(verdict) is not str:
        raise PreparationError("receipt:verdict")
    if not callable(terminal_validate):
        raise PreparationError("receipt:terminal-validator")
    payload_sha256 = hashlib.sha256(payload).hexdigest()
    _replay_attempt_marker(
        transaction,
        parent,
        expected_packet_identity,
    )
    for name in (transaction.pending_name, transaction.canonical_name):
        _entry_absent_at(
            transaction.parent_descriptor,
            name,
            problem="receipt:already-exists",
        )

    hooks.before_replace("receipt-before-open", path)
    _replay_attempt_marker(
        transaction,
        parent,
        expected_packet_identity,
    )
    for name in (transaction.pending_name, transaction.canonical_name):
        _entry_absent_at(
            transaction.parent_descriptor,
            name,
            problem="receipt:already-exists",
        )

    pending_descriptor = -1
    try:
        try:
            pending_descriptor = os.open(
                transaction.pending_name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=transaction.parent_descriptor,
            )
        except FileExistsError as error:
            raise PreparationError("receipt:already-exists") from error
        except OSError as error:
            raise PreparationError("receipt:pending-create") from error
        created = os.fstat(pending_descriptor)
        if (
            not stat.S_ISREG(created.st_mode)
            or created.st_nlink != 1
            or created.st_dev != transaction.parent_identity[0]
            or created.st_size != 0
        ):
            raise PreparationError("receipt:pending-created-leaf")

        hooks.before_replace(
            "receipt-after-open",
            parent / transaction.pending_name,
        )
        _replay_attempt_marker(
            transaction,
            parent,
            expected_packet_identity,
        )
        _write_receipt_payload(pending_descriptor, payload)
        try:
            os.fchmod(pending_descriptor, 0o444)
        except OSError as error:
            raise PreparationError("receipt:pending-mode") from error
        _fsync_receipt_descriptor(
            pending_descriptor,
            "receipt:pending-file-fsync",
        )
        receipt_inode = _verify_open_receipt(
            pending_descriptor,
            payload,
            transaction.parent_identity,
            expected_nlink=1,
            problem_prefix="receipt:pending",
        )
        try:
            os.close(pending_descriptor)
        except OSError as error:
            raise PreparationError("receipt:pending-close") from error
        pending_descriptor = -1

        hooks.before_replace(
            "receipt-before-leaf-verify",
            parent / transaction.pending_name,
        )
        _replay_attempt_marker(
            transaction,
            parent,
            expected_packet_identity,
        )
        _verify_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.pending_name,
            payload,
            transaction.parent_identity,
            receipt_inode,
            problem_prefix="receipt:pending",
        )
        _entry_absent_at(
            transaction.parent_descriptor,
            transaction.canonical_name,
            problem="receipt:already-exists",
        )
        _fsync_receipt_descriptor(
            transaction.parent_descriptor,
            "receipt:pending-parent-fsync",
        )
        _replay_attempt_marker(
            transaction,
            parent,
            expected_packet_identity,
        )
        _verify_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.pending_name,
            payload,
            transaction.parent_identity,
            receipt_inode,
            problem_prefix="receipt:pending",
        )

        try:
            os.link(
                transaction.pending_name,
                transaction.canonical_name,
                src_dir_fd=transaction.parent_descriptor,
                dst_dir_fd=transaction.parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise PreparationError("receipt:already-exists") from error
        except OSError as error:
            raise PreparationError("receipt:canonical-link") from error
        _receipt_pair_observation(
            transaction,
            parent,
            payload,
            receipt_inode,
            expected_packet_identity,
            marker_absent=False,
        )
        _fsync_receipt_descriptor(
            transaction.parent_descriptor,
            "receipt:canonical-parent-fsync",
        )

        hooks.before_replace("receipt-after-directory-fsync", path)
        _receipt_pair_observation(
            transaction,
            parent,
            payload,
            receipt_inode,
            expected_packet_identity,
            marker_absent=False,
        )
        _verify_open_receipt(
            transaction.marker_descriptor,
            transaction.marker_payload,
            transaction.parent_identity,
            transaction.marker_inode,
            expected_nlink=1,
            problem_prefix="receipt:attempt",
        )
        _verify_receipt_leaf_at(
            transaction.parent_descriptor,
            transaction.marker_name,
            transaction.marker_payload,
            transaction.parent_identity,
            transaction.marker_inode,
            problem_prefix="receipt:attempt",
        )
        # The final injectable boundary and its coupled replay both occur while the durable
        # nonauthority marker remains present.  No callback can strand an apparently complete
        # canonical receipt after marker removal.
        hooks.before_replace("receipt-before-terminal-coupled-check", path)
        if terminal_validate() is not None:
            raise PreparationError("receipt:terminal-validator")
        _receipt_pair_observation(
            transaction,
            parent,
            payload,
            receipt_inode,
            expected_packet_identity,
            marker_absent=False,
        )
        try:
            try:
                os.unlink(
                    transaction.marker_name,
                    dir_fd=transaction.parent_descriptor,
                )
            except OSError as error:
                raise PreparationError("receipt:attempt-remove") from error
            _fsync_receipt_descriptor(
                transaction.parent_descriptor,
                "receipt:completion-parent-fsync",
            )
            _entry_absent_at(
                transaction.parent_descriptor,
                transaction.marker_name,
                problem="receipt:attempt-still-present",
            )
            _verify_open_receipt(
                transaction.marker_descriptor,
                transaction.marker_payload,
                transaction.parent_identity,
                transaction.marker_inode,
                expected_nlink=0,
                problem_prefix="receipt:attempt",
            )
            # This replay is terminal: marker removal is durable, both names still bind the
            # exact immutable inode, and there is no callback or pathname mutation after it.
            _receipt_pair_observation(
                transaction,
                parent,
                payload,
                receipt_inode,
                expected_packet_identity,
                marker_absent=True,
            )
            return ReceiptCompletionWitness(
                attempt_id=transaction.attempt_id,
                verdict=verdict,
                parent_identity=transaction.parent_identity,
                receipt_inode=receipt_inode,
                byte_count=len(payload),
                payload_sha256=payload_sha256,
            )
        except BaseException as error:
            _restore_marker_or_raise_completion_ambiguous(
                transaction,
                parent,
                expected_packet_identity,
                error,
            )
            raise
    finally:
        if pending_descriptor >= 0:
            try:
                os.close(pending_descriptor)
            except OSError:
                pass


def _atomic_create_receipt(
    path: Path,
    receipt: Mapping[str, Any],
    *,
    expected_parent_identity: tuple[int, int, int] | None = None,
    expected_packet_identity: tuple[int, int, int] | None = None,
    hooks: Hooks = Hooks(),
) -> ReceiptCompletionWitness:
    """Compatibility helper for tests; live preparation begins its transaction before H."""

    path = Path(path).absolute()
    parent = path.parent
    name = path.name
    if name in {"", ".", ".."} or path != parent / name or "/" in name:
        raise PreparationError("receipt:path")
    parent_row = _physical_directory(parent, "receipt-parent")
    parent_identity = _directory_identity(parent_row)
    if (
        expected_parent_identity is not None
        and parent_identity != expected_parent_identity
    ):
        raise PreparationError("receipt-parent:identity")
    manifest_sha256 = receipt.get("packet_manifest_sha256")
    packet = receipt.get("packet")
    source_commit = (
        packet.get("source_commit")
        if isinstance(packet, Mapping)
        else None
    )
    if type(manifest_sha256) is not str or not _SHA256_RE.fullmatch(manifest_sha256):
        raise PreparationError("receipt:attempt-manifest-sha256")
    if type(source_commit) is not str or not _COMMIT_RE.fullmatch(source_commit):
        source_commit = "0" * 40
    transaction = _begin_receipt_transaction(
        parent,
        canonical_name=name,
        source_commit=source_commit,
        packet_manifest_sha256=manifest_sha256,
        expected_parent_identity=parent_identity,
    )
    try:
        return _commit_receipt_transaction(
            transaction,
            path,
            receipt,
            expected_parent_identity=parent_identity,
            expected_packet_identity=expected_packet_identity,
            terminal_validate=lambda: None,
            hooks=hooks,
        )
    finally:
        _close_receipt_transaction(transaction)


def _replay_published_receipt(
    path: Path,
    receipt: Mapping[str, Any],
    *,
    expected_parent_identity: tuple[int, int, int],
    expected_packet_identity: tuple[int, int, int] | None,
    expected_leaf_identity: tuple[int, int] | tuple[int, int, int, int, int, int],
) -> None:
    """Validate filesystem state only; this cannot recreate a process completion witness."""

    path = Path(path).absolute()
    parent_descriptor, parent_identity = _open_bound_receipt_parent(
        path.parent,
        expected_parent_identity,
        expected_packet_identity,
    )
    try:
        marker_name, pending_name = _receipt_auxiliary_names(path.name)
        _entry_absent_at(
            parent_descriptor,
            marker_name,
            problem="receipt:attempt-still-present",
        )
        expected_inode = (
            expected_leaf_identity[0],
            expected_leaf_identity[1],
        )
        _verify_receipt_leaf_at(
            parent_descriptor,
            pending_name,
            _receipt_file_payload(receipt),
            parent_identity,
            expected_inode,
            expected_nlink=2,
            problem_prefix="receipt:pending",
        )
        _verify_receipt_leaf_at(
            parent_descriptor,
            path.name,
            _receipt_file_payload(receipt),
            parent_identity,
            expected_inode,
            expected_nlink=2,
            problem_prefix="receipt:canonical",
        )
        _replay_bound_receipt_parent(
            path.parent,
            parent_descriptor,
            parent_identity,
            expected_packet_identity,
        )
    finally:
        os.close(parent_descriptor)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validated_utc_timestamp(value: object) -> tuple[datetime, str]:
    """Return one exact UTC datetime and its canonical JSON representation."""

    if type(value) is not datetime:
        raise TypeError("timestamp-return-type")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp-not-utc")
    rendered = _timestamp(value)
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


def _base_receipt(supplied_sha256: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "verdict": INCOMPLETE_VERDICT,
        "started_at_utc": None,
        "finished_at_utc": None,
        "host": None,
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


def _serialization_safe_receipt(
    receipt: dict[str, Any],
    supplied_manifest_sha256: str,
) -> dict[str, Any]:
    """Hash a receipt, degrading to a minimal red document on a JSON type fault."""

    try:
        receipt["receipt_payload_sha256"] = _receipt_payload_sha256(receipt)
        _canonical_json(receipt)
        return receipt
    except Exception as error:
        fallback = _base_receipt(supplied_manifest_sha256)
        for field in ("started_at_utc", "finished_at_utc", "host"):
            value = receipt.get(field)
            if type(value) is str and len(value.encode("utf-8")) <= 256:
                fallback[field] = value
        retained_problems = receipt.get("problems")
        if type(retained_problems) is list:
            fallback["problems"] = [
                problem
                for problem in retained_problems
                if type(problem) is str
                and problem
                and len(problem.encode("utf-8", errors="replace"))
                <= MAX_PROBLEM_TOKEN_BYTES
                and not any(ord(character) < 0x20 for character in problem)
            ][:8]
        fallback["problems"].append(
            f"receipt:serialization:{_exception_kind(error)}"
        )
        fallback["problem_count"] = len(fallback["problems"])
        fallback["receipt_payload_sha256"] = _receipt_payload_sha256(fallback)
        _canonical_json(fallback)
        return fallback


def _receipt_output_root(
    config: HostConfig,
    transaction: _ReceiptTransaction,
) -> tuple[Path, tuple[int, int, int]]:
    """Recover the unique canonical name still bound to the held packet inode."""

    if transaction.closed:
        raise PreparationError("receipt:transaction-closed")
    try:
        held_identity = _directory_identity(os.fstat(transaction.parent_descriptor))
    except OSError as error:
        raise PreparationError("receipt:location") from error
    if held_identity != transaction.parent_identity:
        raise PreparationError("receipt:location")
    matches: list[tuple[Path, tuple[int, int, int]]] = []
    for label, candidate in (
        ("packet", config.packet_root),
        ("install", config.install_root),
    ):
        path = Path(candidate).absolute()
        if not os.path.lexists(path):
            continue
        try:
            identity = _directory_identity(
                _physical_directory(path, f"receipt-{label}-root")
            )
        except PreparationError:
            continue
        if identity == transaction.parent_identity:
            matches.append((path, identity))
    if len(matches) != 1:
        raise PreparationError("receipt:location")
    return matches[0]


def _forbidden_state(config: HostConfig) -> dict[str, bool]:
    return {str(path): os.path.lexists(path) for path in config.forbidden()}


def _replay_empty_analytic_root(
    config: HostConfig,
    *,
    expected_identity: tuple[int, int, int],
    expected_dataset_device: int,
) -> None:
    """Bind the terminal analytic-root name, inode, device, and empty entry set."""

    if (
        type(expected_identity) is not tuple
        or len(expected_identity) != 3
        or any(type(value) is not int for value in expected_identity)
        or type(expected_dataset_device) is not int
    ):
        raise PreparationError("storage:analytic-root-terminal-contract")
    analytic_root = Path(config.analytic_root).absolute()
    try:
        descriptor = os.open(
            analytic_root,
            os.O_RDONLY
            | os.O_CLOEXEC
            | os.O_DIRECTORY
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as error:
        raise PreparationError("storage:analytic-root-terminal-open") from error
    try:
        try:
            before = os.fstat(descriptor)
            entries = os.listdir(descriptor)
            after = os.fstat(descriptor)
        except OSError as error:
            raise PreparationError(
                "storage:analytic-root-terminal-observation"
            ) from error
        canonical = _physical_directory(
            analytic_root,
            "storage:analytic-root-terminal-replay",
        )
        if (
            not stat.S_ISDIR(before.st_mode)
            or _directory_identity(before) != expected_identity
            or _directory_identity(after) != expected_identity
            or _directory_identity(canonical) != expected_identity
            or before.st_dev != expected_dataset_device
            or entries != []
        ):
            raise PreparationError("storage:analytic-root-terminal-drift")
    finally:
        os.close(descriptor)


def _replay_terminal_host_contract(
    config: HostConfig,
    *,
    canonical_root_contract: Mapping[str, tuple[Path, tuple[int, int, int]]],
    terminal_forbidden_state: Mapping[str, bool],
    expected_dataset_device: int,
    packet_files: Mapping[str, Mapping[str, Any]],
    supplied_manifest_sha256: str,
    expected_repositories: Mapping[str, Any],
    expected_mutated_files: Mapping[str, Mapping[str, Any]],
    hooks: Hooks,
) -> None:
    """Replay every filesystem invariant that a green H receipt releases."""

    if (
        set(expected_repositories) != {"uniad", "neuroncap", "neurad"}
        or set(expected_mutated_files) != {"server", "compose"}
        or "analytic-root" not in canonical_root_contract
    ):
        raise PreparationError("host:terminal-contract")
    _replay_canonical_root_contract(
        config,
        canonical_root_contract,
        installed=True,
    )
    observed_repositories = {
        "uniad": repository_snapshot(hooks, config.uniad_repo, "uniad"),
        "neuroncap": repository_snapshot(hooks, config.neuroncap_repo, "neuroncap"),
        "neurad": repository_snapshot(hooks, config.neurad_repo, "neurad"),
    }
    if not _exact_json_value(observed_repositories, expected_repositories):
        raise PreparationError("repository:terminal-drift")
    mutated_paths = {
        "server": config.uniad_repo / config.uniad_server_rel,
        "compose": config.neuroncap_repo / config.compose_rel,
    }
    for label, path in mutated_paths.items():
        observed, _payload = stable_file(path)
        if not _exact_json_value(observed, expected_mutated_files[label]):
            raise PreparationError(f"{label}:terminal-drift")
    revalidate_packet_payloads(
        config,
        config.install_root,
        packet_files,
        supplied_manifest_sha256,
        label="terminal-publication",
        receipt_pair_present=True,
    )
    if not _exact_json_value(
        _forbidden_state(config),
        terminal_forbidden_state,
    ):
        raise PreparationError("host:forbidden-path-race")
    _replay_empty_analytic_root(
        config,
        expected_identity=canonical_root_contract["analytic-root"][1],
        expected_dataset_device=expected_dataset_device,
    )
    _replay_canonical_root_contract(
        config,
        canonical_root_contract,
        installed=True,
    )


def _prepare_host_impl(
    supplied_manifest_sha256: str,
    *,
    config: HostConfig = HostConfig(),
    hooks: Hooks = Hooks(),
    _transaction_holder: list[_ReceiptTransaction],
) -> tuple[dict[str, Any], Path]:
    # Establish the complete invocation/packet/controller/state binding before sampling even
    # read-only host identity.  A control stop or an unvalidated packet is not an H attempt and
    # must therefore create neither an in-memory receipt nor a durable red receipt.
    _validate_host_config_numeric_contract(config)
    packet_root_identity = _directory_identity(
        _physical_directory(config.packet_root, "packet-root-binding")
    )
    packet, packet_files, packet_git_blob_oids = validate_packet(
        config, supplied_manifest_sha256
    )
    validate_packet_mission_state(config, packet_files)

    receipt = _base_receipt(supplied_manifest_sha256)
    transaction = _begin_receipt_transaction(
        config.packet_root,
        canonical_name=config.receipt_name,
        source_commit=packet["source_commit"],
        packet_manifest_sha256=supplied_manifest_sha256,
        expected_parent_identity=packet_root_identity,
    )
    _transaction_holder.append(transaction)
    started_value: datetime | None = None
    canonical_root_contract: dict[
        str, tuple[Path, tuple[int, int, int]]
    ] | None = None
    terminal_forbidden_state: dict[str, bool] | None = None
    terminal_repository_state: dict[str, Any] | None = None
    terminal_mutated_files: dict[str, dict[str, Any]] | None = None
    terminal_dataset_device: int | None = None
    try:
        try:
            started_value, started = _validated_utc_timestamp(hooks.now())
        except Exception as error:
            raise PreparationError(
                f"timing:started:{_exception_kind(error)}"
            ) from error
        receipt["started_at_utc"] = started

        try:
            observed_host = hooks.hostname()
            if type(observed_host) is not str:
                raise TypeError("hostname-return-type")
        except Exception as error:
            raise PreparationError(
                f"host:probe:{_exception_kind(error)}"
            ) from error
        if observed_host != config.expected_host:
            raise PreparationError("host:identity")
        receipt["host"] = config.expected_host

        receipt["invocation"] = {
            "environment": dict(_SAFE_ENVIRONMENT),
            "environment_matches": False,
            "isolated": None,
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
        }
        try:
            observed_environment = hooks.environment()
            environment_matches = (
                isinstance(observed_environment, Mapping)
                and dict(observed_environment) == _SAFE_ENVIRONMENT
            )
        except Exception as error:
            raise PreparationError(
                f"invocation:environment-probe:{_exception_kind(error)}"
            ) from error
        receipt["invocation"]["environment_matches"] = environment_matches
        if not environment_matches:
            raise PreparationError("invocation:environment")
        try:
            isolated = hooks.isolated()
            if type(isolated) is not bool:
                raise TypeError("isolated-return-type")
        except Exception as error:
            raise PreparationError(
                f"invocation:isolation-probe:{_exception_kind(error)}"
            ) from error
        receipt["invocation"]["isolated"] = isolated
        if isolated is not True:
            raise PreparationError("invocation:not-isolated")
        if platform.python_implementation() != "CPython" or sys.version_info < (3, 10):
            raise PreparationError("invocation:interpreter")
        forbidden_state = _forbidden_state(config)
        receipt["forbidden_paths"] = forbidden_state
        if any(forbidden_state.values()):
            raise PreparationError("host:forbidden-path-present")

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
        terminal_repository_state = after_repositories
        terminal_mutated_files = {
            "server": server_after,
            "compose": compose_after,
        }

        output_info = _create_durable_analytic_root(
            config,
            expected_dataset_device=storage["dataset_st_dev"],
        )
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
        terminal_dataset_device = storage["dataset_st_dev"]
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
        canonical_root_contract = _capture_canonical_root_contract(config)
        parent_identity = canonical_root_contract["stack-parent"][1]
        expected_packet_identity = canonical_root_contract["packet-root"][1]
        parent_fd, packet_name, install_name = _open_bound_install_parent(
            config,
            parent_identity,
        )
        try:
            source_identity = _directory_entry_identity_at(
                parent_fd,
                packet_name,
                label="packet-root",
            )
            if source_identity != expected_packet_identity:
                raise PreparationError("packet:source-identity")
            if (
                _directory_entry_identity_at(
                    parent_fd,
                    install_name,
                    label="install-root",
                )
                is not None
            ):
                raise PreparationError("packet:install-root-race")
            if source_identity[0] != os.fstat(parent_fd).st_dev:
                raise PreparationError("packet:cross-device-install")
            revalidate_packet_payloads(
                config,
                config.packet_root,
                packet_files,
                supplied_manifest_sha256,
                label="pre-install",
            )

            # The hook is a deterministic race-injection seam only. The controller always owns
            # the actual no-replace rename relative to the already-held physical parent.
            try:
                hooks.rename(config.packet_root, config.install_root)
            except BaseException:
                _replay_bound_install_parent(
                    config,
                    parent_fd,
                    parent_identity,
                )
                destination_after_fault = _directory_entry_identity_at(
                    parent_fd,
                    install_name,
                    label="install-root-after-hook-fault",
                )
                if destination_after_fault == expected_packet_identity:
                    _fsync_receipt_descriptor(
                        parent_fd,
                        "packet:install-parent-fsync",
                    )
                    _replay_bound_install_parent(
                        config,
                        parent_fd,
                        parent_identity,
                    )
                _directory_entry_identity_at(
                    parent_fd,
                    packet_name,
                    label="packet-root-after-hook-fault",
                )
                raise
            _replay_bound_install_parent(
                config,
                parent_fd,
                parent_identity,
            )
            _replay_canonical_root_contract(
                config,
                canonical_root_contract,
                installed=None,
            )
            destination_after_hook = _directory_entry_identity_at(
                parent_fd,
                install_name,
                label="install-root-after-hook",
            )
            if destination_after_hook == expected_packet_identity:
                _fsync_receipt_descriptor(
                    parent_fd,
                    "packet:install-parent-fsync",
                )
                _replay_bound_install_parent(
                    config,
                    parent_fd,
                    parent_identity,
                )
            source_after_hook = _directory_entry_identity_at(
                parent_fd,
                packet_name,
                label="packet-root-after-hook",
            )
            if destination_after_hook == expected_packet_identity:
                revalidate_packet_payloads(
                    config,
                    config.install_root,
                    packet_files,
                    supplied_manifest_sha256,
                    label="post-install",
                )
                if source_after_hook is not None:
                    raise PreparationError("packet:rename-hook-source-identity")
                _replay_canonical_root_contract(
                    config,
                    canonical_root_contract,
                    installed=True,
                )
                raise PreparationError("packet:exclusive-install-bypassed")
            if source_after_hook is None:
                raise PreparationError("packet:rename-hook-source-lost")
            if source_after_hook != expected_packet_identity:
                raise PreparationError("packet:rename-hook-source-identity")
            if destination_after_hook is not None:
                raise PreparationError("packet:install-root-race")

            _exclusive_rename_at(
                parent_fd,
                packet_name,
                install_name,
            )
            _fsync_receipt_descriptor(
                parent_fd,
                "packet:install-parent-fsync",
            )
            if (
                _directory_entry_identity_at(
                    parent_fd,
                    packet_name,
                    label="packet-root-after-install",
                )
                is not None
                or _directory_entry_identity_at(
                    parent_fd,
                    install_name,
                    label="install-root-after-install",
                )
                != expected_packet_identity
            ):
                raise PreparationError("packet:exclusive-install-postcondition")
            _replay_bound_install_parent(
                config,
                parent_fd,
                parent_identity,
            )
            _replay_canonical_root_contract(
                config,
                canonical_root_contract,
                installed=True,
            )
        finally:
            os.close(parent_fd)
        terminal_forbidden_state = dict(expected_post_creation)
        terminal_forbidden_state[str(config.install_root)] = True
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
        _replay_canonical_root_contract(
            config,
            canonical_root_contract,
            installed=True,
        )
        if _forbidden_state(config) != terminal_forbidden_state:
            raise PreparationError("host:forbidden-path-race")
    except Exception as error:  # every fault after state admission publishes a durable red attempt
        receipt["problems"] = [_bounded_problem(error)]
        receipt["problem_count"] = 1
        receipt["verdict"] = INCOMPLETE_VERDICT

    try:
        finished_value, finished = _validated_utc_timestamp(hooks.now())
        if started_value is not None and finished_value < started_value:
            raise ValueError("finished-before-started")
    except Exception as error:
        receipt["problems"].append(
            f"timing:finished:{_exception_kind(error)}"
        )
        receipt["problem_count"] = len(receipt["problems"])
        receipt["verdict"] = INCOMPLETE_VERDICT
    else:
        receipt["finished_at_utc"] = finished

    if (
        receipt["problem_count"] == 0
        and canonical_root_contract is not None
        and terminal_forbidden_state is not None
    ):
        try:
            _replay_canonical_root_contract(
                config,
                canonical_root_contract,
                installed=True,
            )
            if _forbidden_state(config) != terminal_forbidden_state:
                raise PreparationError("host:forbidden-path-race")
        except Exception as error:
            receipt["problems"] = [_bounded_problem(error)]
            receipt["problem_count"] = 1
            receipt["verdict"] = INCOMPLETE_VERDICT

    if receipt["problem_count"] == 0:
        if (
            type(receipt["started_at_utc"]) is not str
            or type(receipt["finished_at_utc"]) is not str
            or type(receipt["host"]) is not str
            or canonical_root_contract is None
            or terminal_forbidden_state is None
            or terminal_repository_state is None
            or terminal_mutated_files is None
            or type(terminal_dataset_device) is not int
        ):
            receipt["problems"] = ["receipt:ready-metadata"]
            receipt["problem_count"] = 1
            receipt["verdict"] = INCOMPLETE_VERDICT
        else:
            receipt["verdict"] = READY_VERDICT
    receipt = _serialization_safe_receipt(receipt, supplied_manifest_sha256)
    output_root, output_root_identity = _receipt_output_root(config, transaction)
    output_path = output_root / config.receipt_name
    expected_packet_identity = (
        canonical_root_contract["packet-root"][1]
        if canonical_root_contract is not None
        else None
    )

    def validate_terminal_publication() -> None:
        if receipt.get("verdict") != READY_VERDICT:
            return
        if (
            canonical_root_contract is None
            or terminal_forbidden_state is None
            or terminal_repository_state is None
            or terminal_mutated_files is None
            or type(terminal_dataset_device) is not int
        ):
            raise PreparationError("host:terminal-contract")
        _replay_terminal_host_contract(
            config,
            canonical_root_contract=canonical_root_contract,
            terminal_forbidden_state=terminal_forbidden_state,
            expected_dataset_device=terminal_dataset_device,
            packet_files=packet_files,
            supplied_manifest_sha256=supplied_manifest_sha256,
            expected_repositories=terminal_repository_state,
            expected_mutated_files=terminal_mutated_files,
            hooks=hooks,
        )

    try:
        completion_witness = _commit_receipt_transaction(
            transaction,
            output_path,
            receipt,
            expected_parent_identity=output_root_identity,
            expected_packet_identity=expected_packet_identity,
            terminal_validate=validate_terminal_publication,
            hooks=hooks,
        )
        _validate_receipt_completion_witness(
            completion_witness,
            transaction,
            output_path,
            receipt,
            expected_packet_identity,
        )
    except BaseException as error:
        _ensure_attempt_marker_after_publication_error(
            transaction,
            output_root,
            expected_packet_identity,
            error,
        )
        raise
    return receipt, output_path


def prepare_host(
    supplied_manifest_sha256: str,
    *,
    config: HostConfig = HostConfig(),
    hooks: Hooks = Hooks(),
) -> tuple[dict[str, Any], Path]:
    """Run one admitted transaction and release held descriptors after its bound result."""

    transaction_holder: list[_ReceiptTransaction] = []
    try:
        return _prepare_host_impl(
            supplied_manifest_sha256,
            config=config,
            hooks=hooks,
            _transaction_holder=transaction_holder,
        )
    finally:
        for transaction in transaction_holder:
            _close_receipt_transaction(transaction)


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
