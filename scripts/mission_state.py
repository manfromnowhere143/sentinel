#!/usr/bin/env python3
"""Load and validate Sentinel's single canonical current-state contract."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import types
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "MISSION_STATE.json"
CANONICAL_REPOSITORY = "/Users/danielwahnich/workspace/sentinel"
EXPECTED_SCHEMA = "sentinel.mission_state.v1"
EXPECTED_PROGRAM_NAME = "semantics-free placebo dose-response causal closure"
EXPECTED_WORKSPACE_BOUNDARY = {
    "isolated_from": "/Users/danielwahnich/workspace/aweb",
    "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
    "cross_workspace_access_requires_explicit_operator_request": True,
}
EXPECTED_CURRENT_COMPLETED_ITERATION = 134
EXPECTED_CURRENT_RESULT = (
    "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
)
EXPECTED_STATE_FIELDS = {
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
EXPECTED_CURRENT_VERDICT = "PLACEBO_HARM_OR_NULL"
EXPECTED_ACTIVE_HYPOTHESIS = (
    "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
)
EXPECTED_DEPRECATED_HYPOTHESES = [
    "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md"
]
EXPECTED_CLAIM_STATE = {
    "neuroncap_union_gain": "ESTABLISHED_ON_NEURONCAP",
    "semantic_attribution": "UNRESOLVED",
    "hugsim_transfer": "TRANSFER_NULL",
    "production_readiness": "NOT_ESTABLISHED",
}
EXPECTED_PAPER_STATE = {
    "status": "ARCHIVED_NOT_SUBMISSION_READY",
    "next_route": "peer-reviewed venue after a full evidence rewrite",
    "blocking_omissions": [
        "HUGSIM transfer null",
        "iteration-134 placebo result",
        "resolved wording for the decoder universal-negative overclaim",
    ],
}
EXPECTED_STORAGE_GATE = {
    "minimum_local_free_gib_before_new_proof_collection": 15,
    "remote_execution_filesystem_path": "/datasets/nuscenes-full",
    "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
    "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
    "policy": (
        "preserve committed proof and hashes; delete only hash-verified duplicates, "
        "reproducible renders, and caches"
    ),
}
EXPECTED_NEXT_PROGRAM_FIELDS = {
    "iteration",
    "name",
    "phase",
    "authorized_actions",
    "forbidden_actions",
}
TOOLING_RECEIPT_REL = Path(
    "experiments/iter135_neuroncap_blind_braking_dose_response/tooling_verification_receipt.json"
)
LAUNCH_CONTROLLER_REL = Path(
    "experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py"
)
TOOLING_VALIDATOR_REL = Path(
    "experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py"
)
TOOLING_RECEIPT_SCHEMA = "iter135.tooling_verification.v2"
TOOLING_RECEIPT_VERDICT = "I135_TOOLING_VERIFICATION_OK"
TOOLING_RECEIPT_FIELDS = {
    "schema",
    "publication",
    "verdict",
    "problem_count",
    "problems",
    "repository",
    "inventory",
    "inventory_sha256",
    "toolchain",
    "environment_contract",
    "files",
    "file_content_set_sha256",
    "command_contract",
    "commands",
    "timing",
    "receipt_payload_sha256",
}
TOOLING_REPOSITORY_FIELDS = {
    "root",
    "git_start",
    "git_end",
    "git_head_stable",
    "git_state_stable",
    "repository_clean_state_stable",
}
TOOLING_GIT_STATE_FIELDS = {
    "head",
    "dirty_entries",
    "porcelain_v1_z_sha256",
    "branch",
    "upstream",
    "upstream_head",
    "parents",
    "commit_paths",
}
TOOLING_INVENTORY_FIELDS = {
    "contract",
    "tests",
    "python_tools",
    "python_files",
    "shell_files",
    "data_files",
    "control_files",
    "tested_files",
}
TOOLING_TIMING_FIELDS = {
    "started_at_utc",
    "finished_at_utc",
    "wall_duration_ns",
    "monotonic_duration_ns",
}
EMPTY_GIT_STATUS_SHA256 = hashlib.sha256(b"").hexdigest()
ITER135_EXPERIMENT_REL = "experiments/iter135_neuroncap_blind_braking_dose_response"
ITER135_HYPOTHESIS_REL = f"{ITER135_EXPERIMENT_REL}/HYPOTHESIS.md"
PREFLIGHT_MUTABLE_PATHS = {
    "CONTINUITY.md",
    "HANDOFF.md",
    f"{ITER135_EXPERIMENT_REL}/env_receipts.json",
    f"{ITER135_EXPERIMENT_REL}/launch_manifest.json",
}
PREFLIGHT_MUTABLE_PREFIXES = (f"{ITER135_EXPERIMENT_REL}/smoke-evidence/",)
GENERATION_ONE_SOURCE_PARENT = "3fcb607fea8e1a251c2c82da385dd096dd650909"
GENERATION_ONE_SOURCE_COMMIT = "2d94cf45acb337ff3ba923da1d1de6e6dda6dab7"
GENERATION_ONE_RECEIPT_COMMIT = "0b5b2d9a4956606fe0619f53288a64d2da58284a"
GENERATION_ONE_STATE_COMMIT = "d8f091c6886d3231fd68382836d16fd23f1101bb"
RECOVERY_SOURCE_PARENT = "c868040f542f9277fc99a451a108138848e80b33"
RECOVERY_REASON_CODE = "H3_PHASE_TRANSITION_SUITE_AND_CI_PORTABILITY_FAILURE"
GENERATION_ONE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "MISSION_STATE.json",
    "README.md",
    "docs/research/BENCH2DRIVE_ROBUST_PREFLIGHT_2026-07-16.md",
    "docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md",
    f"{ITER135_EXPERIMENT_REL}/analyze_dose135.py",
    f"{ITER135_EXPERIMENT_REL}/capture_environment135.py",
    f"{ITER135_EXPERIMENT_REL}/collect_proof135.py",
    f"{ITER135_EXPERIMENT_REL}/dose_schedules.json",
    f"{ITER135_EXPERIMENT_REL}/extract_union_windows.py",
    f"{ITER135_EXPERIMENT_REL}/generate_nested_dose_schedules.py",
    f"{ITER135_EXPERIMENT_REL}/make_launch_manifest.py",
    f"{ITER135_EXPERIMENT_REL}/patch_compose_dose_env.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/run_smoke135.sh",
    f"{ITER135_EXPERIMENT_REL}/server_patch_blind_dose.py",
    f"{ITER135_EXPERIMENT_REL}/server_patch_union_release.py",
    f"{ITER135_EXPERIMENT_REL}/validate_smoke135.py",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_analyzer.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_harness_patches.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_runtime_patches.py",
    "tests/test_iter135_schedule_tools.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
RECOVERY_SOURCE_COMMIT_PATHS = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_TWO_SOURCE_COMMIT = "90773c3686e0e01562a62f3d0f21ddaf594de7d4"
GENERATION_TWO_RECEIPT_COMMIT = "b0eca127ff1d522aefa6164271de7bce3bcaf1a7"
GENERATION_TWO_STATE_COMMIT = "71a137faa268c63d73ae5d1ec0f8409306f446e5"
GENERATION_TWO_BATON_COMMIT = "ee0c0c953ace80b53f3cce97ddd7eb262fb22a2d"
GENERATION_THREE_SOURCE_PARENT = GENERATION_TWO_BATON_COMMIT
GENERATION_THREE_REASON_CODE = (
    "PRE_SMOKE_CONTROL_GAPS_INTERPRETER_SUMMARY_AND_LAUNCH_AUTHORIZATION"
)
GENERATION_THREE_SOURCE_COMMIT_PATHS = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{ITER135_EXPERIMENT_REL}/analyze_dose135.py",
    f"{ITER135_EXPERIMENT_REL}/authorize_launch135.py",
    f"{ITER135_EXPERIMENT_REL}/capture_environment135.py",
    f"{ITER135_EXPERIMENT_REL}/collect_proof135.py",
    f"{ITER135_EXPERIMENT_REL}/make_launch_manifest.py",
    f"{ITER135_EXPERIMENT_REL}/prepare_host135.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/run_smoke135.sh",
    f"{ITER135_EXPERIMENT_REL}/validate_smoke135.py",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_analyzer.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_THREE_SOURCE_COMMIT = "1820fcfd65483fa9c7429dd54fe65dbf91dc6b35"
GENERATION_THREE_RECEIPT_COMMIT = "755489f36ae2b8cefad183341edefd7c30c047e7"
GENERATION_THREE_STATE_COMMIT = "d9e261075d27d5d717debebe5c881fa4d6e882c5"
GENERATION_THREE_BATON_COMMIT = "30b6390b3e165fc517ec6a7d1d7a26502ea45e2a"
GENERATION_FOUR_SOURCE_PARENT = GENERATION_THREE_BATON_COMMIT
GENERATION_FOUR_REASON_CODE = "B3_CI_STRUCTURAL_GIT_READER_TOOLCHAIN_ROOT_FAILURE"
GENERATION_FOUR_SOURCE_COMMIT = "052404fb13aee8395f538a92cc3c898c13f06adc"
GENERATION_FOUR_RECEIPT_COMMIT = "c3e891b9e41f2291b47edc9cec7abffd5259f674"
GENERATION_FOUR_STATE_COMMIT = "0137eeb97442f7af92eaefeb57befcd53c8c2319"
GENERATION_FOUR_BATON_COMMIT = "27c7f02b5474dd156c4a7686de774a6f408df42e"
GENERATION_FIVE_SOURCE_PARENT = GENERATION_FOUR_BATON_COMMIT
GENERATION_FIVE_REASON_CODE = "B4_H_CONTRACT_UNIAD_LOAD_BEARING_UNTRACKED_SYMLINK"
GENERATION_FIVE_SOURCE_COMMIT = "27c19216387bc211810e7ae8379040f3eee13bd7"
GENERATION_FIVE_RECEIPT_COMMIT = "1f70e367cd1ffcc2c3dab1c801d0e195a1341ef2"
# Generation five published only its source and receipt before its own structural probe fired on
# the stale four-entry receipt-history check; no generation-five state or baton commit exists.
GENERATION_SIX_SOURCE_PARENT = GENERATION_FIVE_RECEIPT_COMMIT
GENERATION_SIX_REASON_CODE = "T5_FROZEN_STRUCTURAL_VALIDATOR_STALE_RECEIPT_HISTORY"
GENERATION_SIX_SOURCE_COMMIT = "b4e0f82fd2ba2a4d3b2604115e9f47f59895e533"
GENERATION_SIX_RECEIPT_COMMIT = "4fb4d819d56f6a6c6331abfa4e8039bf8bedf7be"
GENERATION_SIX_STATE_COMMIT = "b2d4980dcf786427cee518f2998f8e9ec8225dc0"
GENERATION_SIX_BATON_COMMIT = "a37d1fc0fc9b96604e68e37006c0a8b3515984bb"
GENERATION_SEVEN_SOURCE_PARENT = GENERATION_SIX_BATON_COMMIT
GENERATION_SEVEN_REASON_CODE = "H1_CHECK_RUN_ENVELOPE_INCOMPATIBLE_WITH_BRANCH_VALIDATION"
GENERATION_SEVEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{ITER135_EXPERIMENT_REL}/authorize_launch135.py",
    f"{ITER135_EXPERIMENT_REL}/prepare_host135.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_SIX_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    f"{ITER135_EXPERIMENT_REL}/authorize_launch135.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_FIVE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{ITER135_EXPERIMENT_REL}/authorize_launch135.py",
    f"{ITER135_EXPERIMENT_REL}/prepare_host135.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_FOUR_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{ITER135_EXPERIMENT_REL}/authorize_launch135.py",
    f"{ITER135_EXPERIMENT_REL}/run_dose135.sh",
    f"{ITER135_EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
EXPECTED_RECOVERY_PUBLICATION = {
    "generation": 7,
    "supersedes_receipt_commit": GENERATION_SIX_RECEIPT_COMMIT,
    "recovery_parent": GENERATION_SEVEN_SOURCE_PARENT,
    "reason_code": GENERATION_SEVEN_REASON_CODE,
}

# Compatibility name: this is always the immutable generation-one 31-path baseline. Recovery
# publication has its own paired parent/scope contract and must never redefine this surface.
EXPECTED_SOURCE_COMMIT_PATHS = GENERATION_ONE_SOURCE_COMMIT_PATHS

PREREGISTERED_AUTHORIZED_ACTIONS = (
    "build and validate only the tooling and tests frozen by the active iteration-135 hypothesis",
    "inventory storage and provenance before any safe cleanup or live smoke",
    "publish a read-only external-benchmark commercial, license, compute, and integration preflight",
)
PREREGISTERED_FORBIDDEN_ACTIONS = (
    "GPU launch before the iteration-135 hypothesis, analyzer, manifest, provenance, storage, and smoke gates are frozen",
    "rerun iteration 134",
    "adopt run-index resampling as the iteration-135 primary after observing iteration-134 results",
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
LAUNCH_AUTHORIZED_ACTIONS = (
    "launch the exact hash-bound iteration-135 analytic manifest once on sentinel-gpu",
    "collect and commit raw proof after the single launch terminates, whether done or aborted",
    "publish partial evidence and PLACEBO_DOSE_INFRA_NULL after any aborted analytic launch",
)
LAUNCH_FORBIDDEN_ACTIONS = (
    "relaunch or retry any iteration-135 analytic block after the first analytic block starts",
    "run with any manifest, payload, environment, smoke, repository, image, GPU, storage, or "
    "idle-state drift",
    "run the analyzer before raw proof is committed",
)
PHASE_ACTION_CONTRACTS = {
    "PREREGISTERED_TOOLING_REQUIRED": (
        PREREGISTERED_AUTHORIZED_ACTIONS,
        PREREGISTERED_FORBIDDEN_ACTIONS,
    ),
    "TOOLING_FROZEN_PREFLIGHT_REQUIRED": (
        TOOLING_FROZEN_AUTHORIZED_ACTIONS,
        TOOLING_FROZEN_FORBIDDEN_ACTIONS,
    ),
    "LAUNCH_AUTHORIZED": (LAUNCH_AUTHORIZED_ACTIONS, LAUNCH_FORBIDDEN_ACTIONS),
}
ADVANCED_PHASES = {
    "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
    "LAUNCH_AUTHORIZED",
    "RUNNING",
    "ANALYSIS_REQUIRED",
}
UNIMPLEMENTED_ARTIFACT_PHASES = {"RUNNING", "ANALYSIS_REQUIRED"}
PHASE_RUN_STATES = {
    "PREREGISTRATION_REQUIRED": "IDLE",
    "PREREGISTERED_TOOLING_REQUIRED": "IDLE",
    "TOOLING_FROZEN_PREFLIGHT_REQUIRED": "IDLE",
    "LAUNCH_AUTHORIZED": "IDLE",
    "RUNNING": "RUNNING",
    "ANALYSIS_REQUIRED": "IDLE",
}


class ToolingPublicationError(RuntimeError):
    """A structural tooling-receipt or publication contract failed closed."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ToolingPublicationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ToolingPublicationError(f"non-finite JSON value: {value}")


def _read_regular_file(path: Path, repo: Path) -> bytes:
    cursor = repo
    for part in path.relative_to(repo).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ToolingPublicationError("receipt path contains a symlink")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ToolingPublicationError("receipt is not a regular file")
        if before.st_size > 16 * 1024 * 1024:
            raise ToolingPublicationError("receipt exceeds the structural size limit")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    payload = b"".join(chunks)
    if identity_before != identity_after or len(payload) != before.st_size:
        raise ToolingPublicationError("receipt changed while it was read")
    return payload


def _git(repo: Path, *arguments: str, allowed_returncodes: tuple[int, ...] = (0,)) -> bytes:
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": str(repo),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    completed = subprocess.run(  # noqa: S603 - fixed argv and sanitized environment
        ("/usr/bin/git", "-c", "core.hooksPath=/dev/null", *arguments),
        cwd=repo,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if completed.returncode not in allowed_returncodes:
        raise ToolingPublicationError(f"Git structural probe failed: {arguments[0]}")
    return completed.stdout


def _oid(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _nul_paths(payload: bytes) -> list[str]:
    return sorted(item.decode("utf-8") for item in payload.split(b"\0") if item)


def _preflight_mutable(relative_path: str) -> bool:
    return relative_path in PREFLIGHT_MUTABLE_PATHS or relative_path.startswith(
        PREFLIGHT_MUTABLE_PREFIXES
    )


def _commit_row(repo: Path, commit: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    _git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
    parents = tuple(
        _git(repo, "show", "-s", "--format=%P", commit).decode("ascii").strip().split()
    )
    paths = tuple(
        _nul_paths(
            _git(
                repo,
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                commit,
            )
        )
    )
    return parents, paths


def _load_launch_controller(repo: Path, source_commit: str):
    path = repo / LAUNCH_CONTROLLER_REL
    source = _git(repo, "show", f"{source_commit}:{LAUNCH_CONTROLLER_REL.as_posix()}")
    module_name = "sentinel_iter135_launch_controller"
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    previous_module = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        exec(  # noqa: S102 - controller is loaded from the receipt-bound source commit
            compile(source, str(path), "exec"),
            module.__dict__,
        )
    except Exception as exc:  # noqa: BLE001 - every frozen-controller fault fails closed
        raise ToolingPublicationError(
            f"launch authorization controller failed to load: {type(exc).__name__}"
        ) from exc
    finally:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
    validator = getattr(module, "validate_publication_descendants", None)
    if not callable(validator):
        raise ToolingPublicationError("launch authorization controller validator is missing")
    return validator


def _load_tooling_receipt_validator(repo: Path, source_commit: str):
    path = repo / TOOLING_VALIDATOR_REL
    source = _git(repo, "show", f"{source_commit}:{TOOLING_VALIDATOR_REL.as_posix()}")
    module_name = "sentinel_iter135_tooling_receipt_validator"
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    previous_module = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        exec(  # noqa: S102 - validator is loaded from the receipt-bound source commit
            compile(source, str(path), "exec"),
            module.__dict__,
        )
    except Exception as exc:  # noqa: BLE001 - every frozen-validator fault fails closed
        raise ToolingPublicationError(
            f"published tooling receipt validator failed to load: {type(exc).__name__}"
        ) from exc
    finally:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
    validator = getattr(module, "validate_published_receipt_structure", None)
    if not callable(validator):
        raise ToolingPublicationError("published tooling receipt validator is missing")
    return validator


def _validate_tooling_publication(
    repo: Path,
    *,
    phase: str = "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
    candidate: bool = False,
) -> list[str]:
    """Validate generation publication and its phase-specific descendant controller."""

    problems: list[str] = []
    try:
        root = repo.resolve(strict=True)
        receipt_path = root / TOOLING_RECEIPT_REL
        try:
            raw_receipt = _read_regular_file(receipt_path, root)
        except FileNotFoundError:
            return [f"tooling_publication:receipt_missing:{TOOLING_RECEIPT_REL.as_posix()}"]
        try:
            receipt = json.loads(
                raw_receipt,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonfinite,
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ToolingPublicationError,
            ValueError,
        ) as exc:
            raise ToolingPublicationError(f"malformed receipt JSON: {type(exc).__name__}") from exc
        if not isinstance(receipt, dict):
            raise ToolingPublicationError("receipt root is not an object")
        if set(receipt) != TOOLING_RECEIPT_FIELDS:
            raise ToolingPublicationError(
                f"receipt root field set is not exact: {sorted(receipt)}"
            )
        if receipt.get("schema") != TOOLING_RECEIPT_SCHEMA:
            problems.append(f"tooling_publication:receipt_schema:{receipt.get('schema')!r}")
        if receipt.get("verdict") != TOOLING_RECEIPT_VERDICT:
            problems.append(f"tooling_publication:receipt_verdict:{receipt.get('verdict')!r}")
        if type(receipt.get("problem_count")) is not int or receipt.get("problem_count") != 0:
            problems.append(
                f"tooling_publication:receipt_problem_count:{receipt.get('problem_count')!r}"
            )
        if receipt.get("problems") != []:
            problems.append("tooling_publication:receipt_problems_nonempty_or_malformed")
        publication = receipt.get("publication")
        if not isinstance(publication, Mapping):
            problems.append("tooling_publication:receipt_publication_malformed")
            publication = {}
        if set(publication) != set(EXPECTED_RECOVERY_PUBLICATION):
            problems.append(
                f"tooling_publication:receipt_publication_fields:{sorted(publication)}"
            )
        for field, expected in EXPECTED_RECOVERY_PUBLICATION.items():
            if publication.get(field) != expected:
                problems.append(
                    f"tooling_publication:receipt_publication_{field}:"
                    f"{publication.get(field)!r}"
                )
        payload = dict(receipt)
        claimed_payload_sha256 = payload.pop("receipt_payload_sha256", None)
        actual_payload_sha256 = hashlib.sha256(_canonical_json(payload)).hexdigest()
        if claimed_payload_sha256 != actual_payload_sha256:
            problems.append("tooling_publication:receipt_payload_sha256_mismatch")

        repository = receipt.get("repository")
        if not isinstance(repository, Mapping) or set(repository) != TOOLING_REPOSITORY_FIELDS:
            raise ToolingPublicationError("receipt repository block is malformed")
        if repository.get("root") != CANONICAL_REPOSITORY:
            problems.append(f"tooling_publication:repository_root:{repository.get('root')!r}")
        git_start = repository.get("git_start")
        git_end = repository.get("git_end")
        if (
            not isinstance(git_start, Mapping)
            or set(git_start) != TOOLING_GIT_STATE_FIELDS
            or not isinstance(git_end, Mapping)
            or set(git_end) != TOOLING_GIT_STATE_FIELDS
        ):
            raise ToolingPublicationError("receipt Git provenance is malformed")
        inventory = receipt.get("inventory")
        timing = receipt.get("timing")
        if not isinstance(inventory, Mapping) or set(inventory) != TOOLING_INVENTORY_FIELDS:
            raise ToolingPublicationError("receipt inventory block is malformed")
        if not isinstance(timing, Mapping) or set(timing) != TOOLING_TIMING_FIELDS:
            raise ToolingPublicationError("receipt timing block is malformed")
        if (
            not isinstance(receipt.get("toolchain"), Mapping)
            or not isinstance(receipt.get("environment_contract"), Mapping)
            or not isinstance(receipt.get("files"), Mapping)
            or not isinstance(receipt.get("command_contract"), list)
            or not isinstance(receipt.get("commands"), list)
            or not isinstance(receipt.get("inventory_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", receipt["inventory_sha256"]) is None
            or not isinstance(receipt.get("file_content_set_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", receipt["file_content_set_sha256"])
            is None
        ):
            raise ToolingPublicationError("receipt evidence structure is malformed")
        if git_start != git_end:
            problems.append("tooling_publication:receipt_git_state_drift")
        for key in (
            "git_head_stable",
            "git_state_stable",
            "repository_clean_state_stable",
        ):
            if repository.get(key) is not True:
                problems.append(f"tooling_publication:{key}_not_true")
        source_commit = git_start.get("head")
        if not _oid(source_commit):
            raise ToolingPublicationError("receipt source commit is malformed")
        for label, claimed in (("start", git_start), ("end", git_end)):
            if claimed.get("head") != source_commit:
                problems.append(f"tooling_publication:{label}_head_mismatch")
            if claimed.get("dirty_entries") != []:
                problems.append(f"tooling_publication:{label}_dirty")
            if claimed.get("porcelain_v1_z_sha256") != EMPTY_GIT_STATUS_SHA256:
                problems.append(f"tooling_publication:{label}_status_digest")
            if claimed.get("branch") != "master":
                problems.append(f"tooling_publication:{label}_branch")
            if claimed.get("upstream") != "origin/master":
                problems.append(f"tooling_publication:{label}_upstream")
            if claimed.get("upstream_head") != source_commit:
                problems.append(f"tooling_publication:{label}_source_not_pushed")

        publication_generation = publication.get("generation")
        if publication_generation == 7:
            expected_source_parent = GENERATION_SEVEN_SOURCE_PARENT
            expected_source_paths = tuple(sorted(GENERATION_SEVEN_SOURCE_COMMIT_PATHS))
        elif publication_generation == 6:
            expected_source_parent = GENERATION_SIX_SOURCE_PARENT
            expected_source_paths = tuple(sorted(GENERATION_SIX_SOURCE_COMMIT_PATHS))
        elif publication_generation == 5:
            expected_source_parent = GENERATION_FIVE_SOURCE_PARENT
            expected_source_paths = tuple(sorted(GENERATION_FIVE_SOURCE_COMMIT_PATHS))
        elif publication_generation == 4:
            expected_source_parent = GENERATION_FOUR_SOURCE_PARENT
            expected_source_paths = tuple(sorted(GENERATION_FOUR_SOURCE_COMMIT_PATHS))
        elif publication_generation == 3:
            expected_source_parent = GENERATION_THREE_SOURCE_PARENT
            expected_source_paths = tuple(sorted(GENERATION_THREE_SOURCE_COMMIT_PATHS))
        elif publication_generation == 2:
            # Generation-two compatibility is retained only for isolated historical tests.
            expected_source_parent = RECOVERY_SOURCE_PARENT
            expected_source_paths = tuple(sorted(RECOVERY_SOURCE_COMMIT_PATHS))
        else:
            raise ToolingPublicationError(
                f"unsupported publication generation: {publication_generation!r}"
            )
        actual_source_parents, actual_source_paths = _commit_row(root, source_commit)
        if git_start.get("parents") != list(actual_source_parents):
            problems.append("tooling_publication:source_parent_claim_mismatch")
        if (
            git_start.get("commit_paths") != list(actual_source_paths)
            or git_end.get("commit_paths") != list(actual_source_paths)
        ):
            problems.append("tooling_publication:source_path_claim_mismatch")
        if actual_source_parents != (expected_source_parent,):
            problems.append("tooling_publication:recovery_source_parent")
        if actual_source_paths != expected_source_paths:
            problems.append("tooling_publication:recovery_source_commit_scope")

        if publication_generation in {3, 4, 5, 6, 7}:
            try:
                frozen_errors = _load_tooling_receipt_validator(root, source_commit)(
                    receipt,
                    repo_root=root,
                )
            except ToolingPublicationError:
                raise
            except Exception as exc:  # noqa: BLE001 - frozen validation must fail closed
                raise ToolingPublicationError(
                    f"published tooling receipt validator failed: {type(exc).__name__}"
                ) from exc
            if not isinstance(frozen_errors, list) or any(
                not isinstance(item, str) for item in frozen_errors
            ):
                raise ToolingPublicationError(
                    "published tooling receipt validator returned malformed errors"
                )
            if frozen_errors:
                raise ToolingPublicationError(
                    f"published tooling receipt failed frozen validation: {frozen_errors[0][:256]}"
                )

        generation_one_parents, generation_one_paths = _commit_row(
            root, GENERATION_ONE_SOURCE_COMMIT
        )
        if generation_one_parents != (GENERATION_ONE_SOURCE_PARENT,):
            problems.append("tooling_publication:generation_one_source_parent")
        if generation_one_paths != tuple(sorted(GENERATION_ONE_SOURCE_COMMIT_PATHS)):
            problems.append("tooling_publication:generation_one_source_commit_scope")
        old_receipt_parents, old_receipt_paths = _commit_row(
            root, GENERATION_ONE_RECEIPT_COMMIT
        )
        if old_receipt_parents != (GENERATION_ONE_SOURCE_COMMIT,):
            problems.append("tooling_publication:generation_one_receipt_parent")
        if old_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
            problems.append("tooling_publication:generation_one_receipt_scope")
        old_state_parents, old_state_paths = _commit_row(root, GENERATION_ONE_STATE_COMMIT)
        if old_state_parents != (GENERATION_ONE_RECEIPT_COMMIT,):
            problems.append("tooling_publication:generation_one_state_parent")
        if old_state_paths != ("MISSION_STATE.json",):
            problems.append("tooling_publication:generation_one_state_scope")
        recovery_parent_parents, recovery_parent_paths = _commit_row(
            root, RECOVERY_SOURCE_PARENT
        )
        if recovery_parent_parents != (GENERATION_ONE_STATE_COMMIT,):
            problems.append("tooling_publication:generation_one_baton_parent")
        if recovery_parent_paths != ("CONTINUITY.md", "HANDOFF.md"):
            problems.append("tooling_publication:generation_one_baton_scope")

        if publication_generation in {3, 4, 5, 6, 7}:
            generation_two_parents, generation_two_paths = _commit_row(
                root, GENERATION_TWO_SOURCE_COMMIT
            )
            if generation_two_parents != (RECOVERY_SOURCE_PARENT,):
                problems.append("tooling_publication:generation_two_source_parent")
            if generation_two_paths != tuple(sorted(RECOVERY_SOURCE_COMMIT_PATHS)):
                problems.append("tooling_publication:generation_two_source_commit_scope")
            generation_two_receipt_parents, generation_two_receipt_paths = _commit_row(
                root, GENERATION_TWO_RECEIPT_COMMIT
            )
            if generation_two_receipt_parents != (GENERATION_TWO_SOURCE_COMMIT,):
                problems.append("tooling_publication:generation_two_receipt_parent")
            if generation_two_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
                problems.append("tooling_publication:generation_two_receipt_scope")
            generation_two_state_parents, generation_two_state_paths = _commit_row(
                root, GENERATION_TWO_STATE_COMMIT
            )
            if generation_two_state_parents != (GENERATION_TWO_RECEIPT_COMMIT,):
                problems.append("tooling_publication:generation_two_state_parent")
            if generation_two_state_paths != ("MISSION_STATE.json",):
                problems.append("tooling_publication:generation_two_state_scope")
            generation_two_baton_parents, generation_two_baton_paths = _commit_row(
                root, GENERATION_TWO_BATON_COMMIT
            )
            if generation_two_baton_parents != (GENERATION_TWO_STATE_COMMIT,):
                problems.append("tooling_publication:generation_two_baton_parent")
            if generation_two_baton_paths != ("CONTINUITY.md", "HANDOFF.md"):
                problems.append("tooling_publication:generation_two_baton_scope")

        if publication_generation == 7:
            generation_six_parents, generation_six_paths = _commit_row(
                root, GENERATION_SIX_SOURCE_COMMIT
            )
            if generation_six_parents != (GENERATION_SIX_SOURCE_PARENT,):
                problems.append("tooling_publication:generation_six_source_parent")
            if generation_six_paths != tuple(sorted(GENERATION_SIX_SOURCE_COMMIT_PATHS)):
                problems.append("tooling_publication:generation_six_source_commit_scope")
            generation_six_receipt_parents, generation_six_receipt_paths = _commit_row(
                root, GENERATION_SIX_RECEIPT_COMMIT
            )
            if generation_six_receipt_parents != (GENERATION_SIX_SOURCE_COMMIT,):
                problems.append("tooling_publication:generation_six_receipt_parent")
            if generation_six_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
                problems.append("tooling_publication:generation_six_receipt_scope")
            generation_six_state_parents, generation_six_state_paths = _commit_row(
                root, GENERATION_SIX_STATE_COMMIT
            )
            if generation_six_state_parents != (GENERATION_SIX_RECEIPT_COMMIT,):
                problems.append("tooling_publication:generation_six_state_parent")
            if generation_six_state_paths != ("MISSION_STATE.json",):
                problems.append("tooling_publication:generation_six_state_scope")
            generation_six_baton_parents, generation_six_baton_paths = _commit_row(
                root, GENERATION_SIX_BATON_COMMIT
            )
            if generation_six_baton_parents != (GENERATION_SIX_STATE_COMMIT,):
                problems.append("tooling_publication:generation_six_baton_parent")
            if generation_six_baton_paths != ("CONTINUITY.md", "HANDOFF.md"):
                problems.append("tooling_publication:generation_six_baton_scope")

        if publication_generation in {6, 7}:
            generation_five_parents, generation_five_paths = _commit_row(
                root, GENERATION_FIVE_SOURCE_COMMIT
            )
            if generation_five_parents != (GENERATION_FIVE_SOURCE_PARENT,):
                problems.append("tooling_publication:generation_five_source_parent")
            if generation_five_paths != tuple(sorted(GENERATION_FIVE_SOURCE_COMMIT_PATHS)):
                problems.append("tooling_publication:generation_five_source_commit_scope")
            generation_five_receipt_parents, generation_five_receipt_paths = _commit_row(
                root, GENERATION_FIVE_RECEIPT_COMMIT
            )
            if generation_five_receipt_parents != (GENERATION_FIVE_SOURCE_COMMIT,):
                problems.append("tooling_publication:generation_five_receipt_parent")
            if generation_five_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
                problems.append("tooling_publication:generation_five_receipt_scope")

        if publication_generation in {5, 6, 7}:
            generation_four_parents, generation_four_paths = _commit_row(
                root, GENERATION_FOUR_SOURCE_COMMIT
            )
            if generation_four_parents != (GENERATION_FOUR_SOURCE_PARENT,):
                problems.append("tooling_publication:generation_four_source_parent")
            if generation_four_paths != tuple(sorted(GENERATION_FOUR_SOURCE_COMMIT_PATHS)):
                problems.append("tooling_publication:generation_four_source_commit_scope")
            generation_four_receipt_parents, generation_four_receipt_paths = _commit_row(
                root, GENERATION_FOUR_RECEIPT_COMMIT
            )
            if generation_four_receipt_parents != (GENERATION_FOUR_SOURCE_COMMIT,):
                problems.append("tooling_publication:generation_four_receipt_parent")
            if generation_four_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
                problems.append("tooling_publication:generation_four_receipt_scope")
            generation_four_state_parents, generation_four_state_paths = _commit_row(
                root, GENERATION_FOUR_STATE_COMMIT
            )
            if generation_four_state_parents != (GENERATION_FOUR_RECEIPT_COMMIT,):
                problems.append("tooling_publication:generation_four_state_parent")
            if generation_four_state_paths != ("MISSION_STATE.json",):
                problems.append("tooling_publication:generation_four_state_scope")
            generation_four_baton_parents, generation_four_baton_paths = _commit_row(
                root, GENERATION_FOUR_BATON_COMMIT
            )
            if generation_four_baton_parents != (GENERATION_FOUR_STATE_COMMIT,):
                problems.append("tooling_publication:generation_four_baton_parent")
            if generation_four_baton_paths != ("CONTINUITY.md", "HANDOFF.md"):
                problems.append("tooling_publication:generation_four_baton_scope")

        if publication_generation in {4, 5, 6, 7}:
            generation_three_parents, generation_three_paths = _commit_row(
                root, GENERATION_THREE_SOURCE_COMMIT
            )
            if generation_three_parents != (GENERATION_THREE_SOURCE_PARENT,):
                problems.append("tooling_publication:generation_three_source_parent")
            if generation_three_paths != tuple(sorted(GENERATION_THREE_SOURCE_COMMIT_PATHS)):
                problems.append("tooling_publication:generation_three_source_commit_scope")
            generation_three_receipt_parents, generation_three_receipt_paths = _commit_row(
                root, GENERATION_THREE_RECEIPT_COMMIT
            )
            if generation_three_receipt_parents != (GENERATION_THREE_SOURCE_COMMIT,):
                problems.append("tooling_publication:generation_three_receipt_parent")
            if generation_three_receipt_paths != (TOOLING_RECEIPT_REL.as_posix(),):
                problems.append("tooling_publication:generation_three_receipt_scope")
            generation_three_state_parents, generation_three_state_paths = _commit_row(
                root, GENERATION_THREE_STATE_COMMIT
            )
            if generation_three_state_parents != (GENERATION_THREE_RECEIPT_COMMIT,):
                problems.append("tooling_publication:generation_three_state_parent")
            if generation_three_state_paths != ("MISSION_STATE.json",):
                problems.append("tooling_publication:generation_three_state_scope")
            generation_three_baton_parents, generation_three_baton_paths = _commit_row(
                root, GENERATION_THREE_BATON_COMMIT
            )
            if generation_three_baton_parents != (GENERATION_THREE_STATE_COMMIT,):
                problems.append("tooling_publication:generation_three_baton_parent")
            if generation_three_baton_paths != ("CONTINUITY.md", "HANDOFF.md"):
                problems.append("tooling_publication:generation_three_baton_scope")

        current_commit = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
        receipt_history = tuple(
            line
            for line in _git(
                root,
                "log",
                "--format=%H",
                "--",
                TOOLING_RECEIPT_REL.as_posix(),
            )
            .decode("ascii")
            .splitlines()
            if line
        )
        if publication_generation == 7:
            expected_receipt_history_tail = (
                GENERATION_SIX_RECEIPT_COMMIT,
                GENERATION_FIVE_RECEIPT_COMMIT,
                GENERATION_FOUR_RECEIPT_COMMIT,
                GENERATION_THREE_RECEIPT_COMMIT,
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        elif publication_generation == 6:
            expected_receipt_history_tail = (
                GENERATION_FIVE_RECEIPT_COMMIT,
                GENERATION_FOUR_RECEIPT_COMMIT,
                GENERATION_THREE_RECEIPT_COMMIT,
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        elif publication_generation == 5:
            expected_receipt_history_tail = (
                GENERATION_FOUR_RECEIPT_COMMIT,
                GENERATION_THREE_RECEIPT_COMMIT,
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        elif publication_generation == 4:
            expected_receipt_history_tail = (
                GENERATION_THREE_RECEIPT_COMMIT,
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        elif publication_generation == 3:
            expected_receipt_history_tail = (
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        else:
            expected_receipt_history_tail = (GENERATION_ONE_RECEIPT_COMMIT,)
        if (
            len(receipt_history) != len(expected_receipt_history_tail) + 1
            or not _oid(receipt_history[0])
            or receipt_history[1:] != expected_receipt_history_tail
        ):
            problems.append(f"tooling_publication:receipt_history:{list(receipt_history)}")
        if not receipt_history or not _oid(receipt_history[0]):
            raise ToolingPublicationError("active generation receipt commit is missing")
        receipt_commit = receipt_history[0]
        receipt_commit_parents, receipt_commit_paths = _commit_row(root, receipt_commit)
        if receipt_commit_parents != (source_commit,):
            problems.append("tooling_publication:receipt_not_direct_recovery_source_child")
        if receipt_commit_paths != (TOOLING_RECEIPT_REL.as_posix(),):
            problems.append("tooling_publication:receipt_commit_not_receipt_only")
        committed_receipt = _git(root, "show", f"{receipt_commit}:{TOOLING_RECEIPT_REL.as_posix()}")
        if committed_receipt != raw_receipt:
            problems.append("tooling_publication:receipt_bytes_not_committed")

        ancestry = (
            _git(
                root,
                "rev-list",
                "--reverse",
                "--ancestry-path",
                f"{receipt_commit}..{current_commit}",
            )
            .decode("ascii")
            .splitlines()
        )
        if len(ancestry) < 2:
            generation_label = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}[
                publication_generation
            ]
            problems.append(
                f"tooling_publication:generation_{generation_label}_commit_count:{len(ancestry)}"
            )
        else:
            state_commit, baton_commit = ancestry[:2]
            state_commit_parents, state_commit_paths = _commit_row(root, state_commit)
            if state_commit_parents != (receipt_commit,):
                problems.append("tooling_publication:state_not_direct_receipt_child")
            if state_commit_paths != ("MISSION_STATE.json",):
                problems.append("tooling_publication:state_commit_not_state_only")
            committed_state = _git(root, "show", f"{state_commit}:MISSION_STATE.json")
            try:
                physical_state = _read_regular_file(root / "MISSION_STATE.json", root)
            except FileNotFoundError as exc:
                raise ToolingPublicationError("committed mission state is missing") from exc
            if phase != "LAUNCH_AUTHORIZED" and physical_state != committed_state:
                problems.append("tooling_publication:mission_state_bytes_not_committed")
            baton_commit_parents, baton_commit_paths = _commit_row(root, baton_commit)
            if baton_commit_parents != (state_commit,):
                problems.append("tooling_publication:baton_not_direct_state_child")
            if baton_commit_paths != ("CONTINUITY.md", "HANDOFF.md"):
                problems.append("tooling_publication:baton_commit_scope")
            authorization_references: Mapping[str, str] = {}
            if publication_generation in {3, 4, 5, 6, 7}:
                upstream_for_controller = (
                    _git(root, "rev-parse", "origin/master").decode("ascii").strip()
                )
                controller_result = _load_launch_controller(root, source_commit)(
                    root,
                    phase=phase,
                    tooling_receipt_commit=receipt_commit,
                    tooling_baton_commit=baton_commit,
                    descendants=ancestry[2:],
                    upstream_commit=upstream_for_controller,
                    candidate=candidate,
                )
                if not isinstance(controller_result, Mapping):
                    raise ToolingPublicationError("launch controller returned a malformed result")
                controller_problems = controller_result.get("problems")
                if not isinstance(controller_problems, list) or any(
                    not isinstance(item, str) for item in controller_problems
                ):
                    raise ToolingPublicationError("launch controller problems are malformed")
                problems.extend(controller_problems)
                candidate_references = controller_result.get("references")
                if isinstance(candidate_references, Mapping) and all(
                    isinstance(key, str) and isinstance(value, str)
                    for key, value in candidate_references.items()
                ):
                    authorization_references = candidate_references
                else:
                    problems.append("authorization:reference-map")
            else:
                previous_commit = baton_commit
                for descendant in ancestry[2:]:
                    descendant_parents, descendant_paths = _commit_row(root, descendant)
                    if descendant_parents != (previous_commit,):
                        problems.append("tooling_publication:preflight_history_not_linear")
                    if not descendant_paths or not all(
                        _preflight_mutable(relative) for relative in descendant_paths
                    ):
                        problems.append(
                            f"tooling_publication:preflight_descendant_scope:"
                            f"{list(descendant_paths)}"
                        )
                    previous_commit = descendant

            immutable_source_paths = sorted(
                (
                    set(GENERATION_ONE_SOURCE_COMMIT_PATHS)
                    | set(RECOVERY_SOURCE_COMMIT_PATHS)
                    | (
                        set(GENERATION_THREE_SOURCE_COMMIT_PATHS)
                        if publication_generation in {3, 4, 5, 6, 7}
                        else set()
                    )
                    | (
                        set(GENERATION_FOUR_SOURCE_COMMIT_PATHS)
                        if publication_generation in {4, 5, 6, 7}
                        else set()
                    )
                    | (
                        set(GENERATION_FIVE_SOURCE_COMMIT_PATHS)
                        if publication_generation in {5, 6, 7}
                        else set()
                    )
                    | (
                        set(GENERATION_SIX_SOURCE_COMMIT_PATHS)
                        if publication_generation in {6, 7}
                        else set()
                    )
                    | {ITER135_HYPOTHESIS_REL}
                )
                - {"CONTINUITY.md", "HANDOFF.md", "MISSION_STATE.json"}
            )
            for relative in immutable_source_paths:
                recovery_blob = _git(root, "show", f"{source_commit}:{relative}")
                current_blob = _git(root, "show", f"{current_commit}:{relative}")
                if current_blob != recovery_blob:
                    problems.append(f"tooling_publication:immutable_path_changed:{relative}")
                try:
                    physical_blob = _read_regular_file(root / relative, root)
                except FileNotFoundError as exc:
                    raise ToolingPublicationError(f"immutable path is missing: {relative}") from exc
                if physical_blob != recovery_blob:
                    problems.append(
                        f"tooling_publication:immutable_worktree_path_changed:{relative}"
                    )
            state_reference_commit = authorization_references.get(
                "MISSION_STATE.json", state_commit
            )
            for relative, reference_commit in (
                ("MISSION_STATE.json", state_reference_commit),
                (TOOLING_RECEIPT_REL.as_posix(), receipt_commit),
            ):
                reference_blob = _git(root, "show", f"{reference_commit}:{relative}")
                current_blob = _git(root, "show", f"{current_commit}:{relative}")
                if current_blob != reference_blob:
                    problems.append(f"tooling_publication:immutable_path_changed:{relative}")
                physical_blob = _read_regular_file(root / relative, root)
                if physical_blob != reference_blob:
                    problems.append(
                        f"tooling_publication:immutable_worktree_path_changed:{relative}"
                    )
            for relative in ("CONTINUITY.md", "HANDOFF.md"):
                current_blob = _git(root, "show", f"{current_commit}:{relative}")
                physical_blob = _read_regular_file(root / relative, root)
                if physical_blob != current_blob:
                    problems.append(
                        f"tooling_publication:mutable_worktree_path_changed:{relative}"
                    )
        upstream_commit = _git(root, "rev-parse", "origin/master").decode("ascii").strip()
        upstream_contains_receipt = subprocess.run(  # noqa: S603 - fixed local Git probe
            (
                "/usr/bin/git",
                "-c",
                "core.hooksPath=/dev/null",
                "merge-base",
                "--is-ancestor",
                receipt_commit,
                upstream_commit,
            ),
            cwd=root,
            env={
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "HOME": str(root),
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        ).returncode
        if upstream_contains_receipt != 0:
            problems.append("tooling_publication:receipt_commit_not_published")
    except (OSError, subprocess.SubprocessError, ToolingPublicationError, ValueError) as exc:
        problems.append(f"tooling_publication:structural_probe:{type(exc).__name__}:{exc}")
    return problems


def validate_local_launch_candidate(repo: Path = REPO_ROOT) -> dict[str, Any]:
    """Evaluate a complete clean local A/F/B candidate without granting authority.

    This path exists only to close the pre-push validation gap.  The canonical
    ``validate_state`` path never enables it, and the result always carries
    ``launch_authorized=false``.  Exact origin-tip equality and a normal validation pass remain
    the sole launch authority.
    """

    root = Path(repo).resolve(strict=True)
    try:
        state = load_state(root / "MISSION_STATE.json")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return {
            "schema": "sentinel.local_launch_candidate.v1",
            "verdict": "I135_LOCAL_LAUNCH_CANDIDATE_INVALID",
            "candidate_valid": False,
            "authoritative": False,
            "launch_authorized": False,
            "problems": [f"candidate:mission-state:{type(exc).__name__}"],
        }
    problems = _exact_launch_state_contract_problems(state)
    if problems:
        return {
            "schema": "sentinel.local_launch_candidate.v1",
            "verdict": "I135_LOCAL_LAUNCH_CANDIDATE_INVALID",
            "candidate_valid": False,
            "authoritative": False,
            "launch_authorized": False,
            "problems": sorted(set(problems)),
        }
    problems.extend(
        _validate_tooling_publication(
            root,
            phase="LAUNCH_AUTHORIZED",
            candidate=True,
        )
    )
    marker = "authorization:candidate-non-authoritative"
    marker_present = marker in problems
    substantive = sorted(set(item for item in problems if item != marker))
    candidate_valid = marker_present and not substantive
    return {
        "schema": "sentinel.local_launch_candidate.v1",
        "verdict": (
            "I135_LOCAL_LAUNCH_CANDIDATE_VALID_NON_AUTHORITATIVE"
            if candidate_valid
            else "I135_LOCAL_LAUNCH_CANDIDATE_INVALID"
        ),
        "candidate_valid": candidate_valid,
        "authoritative": False,
        "launch_authorized": False,
        "problems": [marker] if candidate_valid else substantive,
    }


def _exact_launch_state_contract_problems(state: Mapping[str, Any]) -> list[str]:
    """Validate the exact launch-state document before any topology probe.

    Candidate validation is intentionally stricter than a phase-only transition check.  A local
    A/F/B chain is not even inspected unless its physical mission state is the complete frozen
    launch contract.  This helper is deterministic and grants no publication authority.
    """

    problems: list[str] = []
    if set(state) != EXPECTED_STATE_FIELDS:
        problems.append("candidate:state-field-set")
    exact_fields: tuple[tuple[str, Any, str], ...] = (
        ("schema", EXPECTED_SCHEMA, "candidate:state-schema"),
        (
            "canonical_repository",
            CANONICAL_REPOSITORY,
            "candidate:state-canonical-repository",
        ),
        (
            "workspace_boundary",
            EXPECTED_WORKSPACE_BOUNDARY,
            "candidate:state-workspace-boundary",
        ),
        ("trunk", "master", "candidate:state-trunk"),
        (
            "current_completed_iteration",
            EXPECTED_CURRENT_COMPLETED_ITERATION,
            "candidate:state-current-iteration",
        ),
        ("current_result", EXPECTED_CURRENT_RESULT, "candidate:state-current-result"),
        (
            "current_verdict",
            EXPECTED_CURRENT_VERDICT,
            "candidate:state-current-verdict",
        ),
        ("run_state", "IDLE", "candidate:state-run-state"),
        (
            "active_hypothesis",
            EXPECTED_ACTIVE_HYPOTHESIS,
            "candidate:state-active-hypothesis",
        ),
        ("claim_state", EXPECTED_CLAIM_STATE, "candidate:state-claim-state"),
        (
            "deprecated_pending_hypotheses",
            EXPECTED_DEPRECATED_HYPOTHESES,
            "candidate:state-deprecated-hypotheses",
        ),
        ("paper_state", EXPECTED_PAPER_STATE, "candidate:state-paper-state"),
        ("storage_gate", EXPECTED_STORAGE_GATE, "candidate:state-storage-gate"),
    )
    for field, expected, problem in exact_fields:
        if state.get(field) != expected:
            problems.append(problem)

    next_program = state.get("next_program")
    if not isinstance(next_program, Mapping) or set(next_program) != EXPECTED_NEXT_PROGRAM_FIELDS:
        problems.append("candidate:state-next-program-field-set")
    expected_next_program = {
        "iteration": EXPECTED_CURRENT_COMPLETED_ITERATION + 1,
        "name": EXPECTED_PROGRAM_NAME,
        "phase": "LAUNCH_AUTHORIZED",
        "authorized_actions": list(LAUNCH_AUTHORIZED_ACTIONS),
        "forbidden_actions": list(LAUNCH_FORBIDDEN_ACTIONS),
    }
    if next_program != expected_next_program:
        problems.append("candidate:state-next-program")
    return sorted(set(problems))


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def load_state(path: Path = STATE_PATH) -> dict:
    loaded = json.loads(
        path.read_text(),
        object_pairs_hook=_strict_json_object,
        parse_constant=_reject_nonfinite_json,
    )
    if not isinstance(loaded, dict):
        raise ValueError("mission state top level must be an object")
    return loaded


def validate_state(state: dict, repo: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    if set(state) != EXPECTED_STATE_FIELDS:
        problems.append(f"state_fields:{sorted(state)}")
    if state.get("schema") != EXPECTED_SCHEMA:
        problems.append(f"schema:{state.get('schema')!r}!={EXPECTED_SCHEMA!r}")

    if state.get("canonical_repository") != CANONICAL_REPOSITORY:
        problems.append(f"canonical_repository:{state.get('canonical_repository')!r}")
    if state.get("trunk") != "master":
        problems.append(f"trunk:{state.get('trunk')!r}")
    if state.get("workspace_boundary") != EXPECTED_WORKSPACE_BOUNDARY:
        problems.append(f"workspace_boundary:{state.get('workspace_boundary')!r}")

    completed = state.get("current_completed_iteration")
    if not isinstance(completed, int) or completed < 1:
        problems.append(f"current_completed_iteration:{completed!r}")

    result = state.get("current_result")
    result_path = repo / result if isinstance(result, str) else None
    if result_path is None or not result_path.is_file():
        problems.append(f"current_result_missing:{result!r}")
    else:
        result_text = result_path.read_text(errors="replace")
        verdict = state.get("current_verdict")
        if not verdict or verdict not in result_text:
            problems.append(f"current_verdict_not_in_result:{verdict!r}")
    if state.get("current_verdict") != EXPECTED_CURRENT_VERDICT:
        problems.append(f"current_verdict:{state.get('current_verdict')!r}")

    completed_results: dict[int, Path] = {}
    for candidate in repo.glob("experiments/iter*/RESULT.md"):
        match = re.match(r"iter(\d+)(?:_|$)", candidate.parent.name)
        if match:
            completed_results[int(match.group(1))] = candidate
    discovered_completed = max(completed_results, default=0)
    if completed != discovered_completed:
        problems.append(f"current_completed_iteration:{completed!r}!={discovered_completed}")
    elif result_path is not None and result_path != completed_results.get(discovered_completed):
        problems.append(
            f"current_result:{result!r}!={completed_results[discovered_completed].relative_to(repo)}"
        )

    next_program = state.get("next_program") or {}
    if set(next_program) != EXPECTED_NEXT_PROGRAM_FIELDS:
        problems.append(f"next_program_fields:{sorted(next_program)}")
    if next_program.get("name") != EXPECTED_PROGRAM_NAME:
        problems.append(f"next_program_name:{next_program.get('name')!r}")
    next_iteration = next_program.get("iteration")
    if isinstance(completed, int) and next_iteration != completed + 1:
        problems.append(f"next_iteration:{next_iteration!r}!={completed + 1}")
    phase = next_program.get("phase")
    if phase not in {
        "PREREGISTRATION_REQUIRED",
        "PREREGISTERED_TOOLING_REQUIRED",
        "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
        "LAUNCH_AUTHORIZED",
        "RUNNING",
        "ANALYSIS_REQUIRED",
    }:
        problems.append(f"next_phase:{phase!r}")

    action_contract = PHASE_ACTION_CONTRACTS.get(phase)
    if action_contract is not None:
        expected_authorized, expected_forbidden = action_contract
        if next_program.get("authorized_actions") != list(expected_authorized):
            problems.append(
                f"phase_authorized_actions:{phase}:{next_program.get('authorized_actions')!r}"
            )
        if next_program.get("forbidden_actions") != list(expected_forbidden):
            problems.append(
                f"phase_forbidden_actions:{phase}:{next_program.get('forbidden_actions')!r}"
            )
    elif phase == "PREREGISTRATION_REQUIRED":
        problems.append("phase_contract:PREREGISTRATION_REQUIRED:not_implemented")

    if phase in ADVANCED_PHASES:
        problems.extend(_validate_tooling_publication(repo, phase=phase))
    if phase in UNIMPLEMENTED_ARTIFACT_PHASES:
        problems.append(f"phase_artifact_contract:{phase}:not_implemented")

    if state.get("run_state") not in {"IDLE", "RUNNING", "UNKNOWN"}:
        problems.append(f"run_state:{state.get('run_state')!r}")
    expected_run_state = PHASE_RUN_STATES.get(phase)
    if expected_run_state is not None and state.get("run_state") != expected_run_state:
        problems.append(
            f"phase_run_state:{phase}:{state.get('run_state')!r}!={expected_run_state!r}"
        )

    deprecated = set(state.get("deprecated_pending_hypotheses", []))
    if state.get("deprecated_pending_hypotheses") != EXPECTED_DEPRECATED_HYPOTHESES:
        problems.append(
            "deprecated_pending_hypotheses:"
            f"{state.get('deprecated_pending_hypotheses')!r}"
        )
    for hypothesis in deprecated:
        if not (repo / hypothesis).is_file():
            problems.append(f"deprecated_pending_hypothesis_missing:{hypothesis}")

    active_hypothesis = state.get("active_hypothesis")
    if active_hypothesis != EXPECTED_ACTIVE_HYPOTHESIS:
        problems.append(f"active_hypothesis:{active_hypothesis!r}")
    classified = set(deprecated)
    if active_hypothesis is not None:
        if not isinstance(active_hypothesis, str) or not (repo / active_hypothesis).is_file():
            problems.append(f"active_hypothesis_missing:{active_hypothesis!r}")
        else:
            classified.add(active_hypothesis)
    pending = {
        str(path.relative_to(repo))
        for path in repo.glob("experiments/iter*/HYPOTHESIS.md")
        if not path.with_name("RESULT.md").is_file()
    }
    if pending != classified:
        problems.append(
            "pending_hypothesis_classification:"
            f"unclassified={sorted(pending - classified)}:nonpending={sorted(classified - pending)}"
        )

    storage = state.get("storage_gate") or {}
    if not isinstance(storage, Mapping) or set(storage) != set(EXPECTED_STORAGE_GATE):
        problems.append(f"storage_gate_fields:{sorted(storage) if isinstance(storage, Mapping) else []}")
    expected_thresholds = {
        "minimum_local_free_gib_before_new_proof_collection": 15,
        "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
        "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
    }
    for key, expected in expected_thresholds.items():
        if storage.get(key) != expected:
            problems.append(f"storage_gate:{key}:{storage.get(key)!r}")
    expected_paths = {
        "remote_execution_filesystem_path": "/datasets/nuscenes-full",
        "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    }
    for key, expected in expected_paths.items():
        if storage.get(key) != expected:
            problems.append(f"storage_gate:{key}:{storage.get(key)!r}")
    if storage.get("policy") != EXPECTED_STORAGE_GATE["policy"]:
        problems.append(f"storage_gate:policy:{storage.get('policy')!r}")

    if state.get("claim_state") != EXPECTED_CLAIM_STATE:
        problems.append(f"claim_state:{state.get('claim_state')!r}")
    if state.get("paper_state") != EXPECTED_PAPER_STATE:
        problems.append(f"paper_state:{state.get('paper_state')!r}")

    return problems


def current_summary(state: dict) -> str:
    next_program = state["next_program"]
    return (
        f"iteration {state['current_completed_iteration']} / {state['current_verdict']} / "
        f"run {state['run_state']} / next iteration {next_program['iteration']} "
        f"{next_program['phase']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="validate a complete clean local A/F/B candidate without granting authority",
    )
    args = parser.parse_args(argv)
    if args.candidate:
        result = validate_local_launch_candidate()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["candidate_valid"] else 1
    loaded = load_state()
    failures = validate_state(loaded)
    if failures:
        print("MISSION STATE INVALID:\n - " + "\n - ".join(failures))
        return 1
    print(f"MISSION_STATE_OK {current_summary(loaded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
