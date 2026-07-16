#!/usr/bin/env python3
"""Load and validate Sentinel's single canonical current-state contract."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "MISSION_STATE.json"
EXPECTED_SCHEMA = "sentinel.mission_state.v1"
EXPECTED_PROGRAM_NAME = "semantics-free placebo dose-response causal closure"
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
TOOLING_RECEIPT_SCHEMA = "iter135.tooling_verification.v2"
TOOLING_RECEIPT_VERDICT = "I135_TOOLING_VERIFICATION_OK"
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
EXPECTED_SOURCE_COMMIT_PATHS = (
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
    "prepare only the exact hash-bound sentinel-gpu host contract, including the dedicated "
    "iteration-135 output root",
    "capture and commit the read-only iteration-135 environment receipt on sentinel-gpu",
    "generate and commit only the hash-addressed incomplete pre-smoke manifest; no analytic "
    "episodes",
    "run exactly the hash-bound four-run nonanalytic G5 smoke after the incomplete pre-smoke "
    "manifest is committed",
    "validate, collect, and commit the exact nonanalytic smoke evidence and receipt",
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
UNIMPLEMENTED_ARTIFACT_PHASES = {"LAUNCH_AUTHORIZED", "RUNNING", "ANALYSIS_REQUIRED"}
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


def _validate_tooling_publication(repo: Path) -> list[str]:
    """Validate receipt structure and Git topology without executing its command contract."""

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
        payload = dict(receipt)
        claimed_payload_sha256 = payload.pop("receipt_payload_sha256", None)
        actual_payload_sha256 = hashlib.sha256(_canonical_json(payload)).hexdigest()
        if claimed_payload_sha256 != actual_payload_sha256:
            problems.append("tooling_publication:receipt_payload_sha256_mismatch")

        repository = receipt.get("repository")
        if not isinstance(repository, Mapping):
            raise ToolingPublicationError("receipt repository block is malformed")
        if repository.get("root") != str(root):
            problems.append(f"tooling_publication:repository_root:{repository.get('root')!r}")
        git_start = repository.get("git_start")
        git_end = repository.get("git_end")
        if not isinstance(git_start, Mapping) or not isinstance(git_end, Mapping):
            raise ToolingPublicationError("receipt Git provenance is malformed")
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

        _git(root, "rev-parse", "--verify", f"{source_commit}^{{commit}}")
        actual_source_parents = (
            _git(root, "show", "-s", "--format=%P", source_commit).decode("ascii").strip().split()
        )
        if git_start.get("parents") != actual_source_parents:
            problems.append("tooling_publication:source_parent_claim_mismatch")
        actual_source_paths = _nul_paths(
            _git(
                root,
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                source_commit,
            )
        )
        if (
            git_start.get("commit_paths") != actual_source_paths
            or git_end.get("commit_paths") != actual_source_paths
        ):
            problems.append("tooling_publication:source_path_claim_mismatch")
        if actual_source_paths != sorted(EXPECTED_SOURCE_COMMIT_PATHS):
            problems.append("tooling_publication:source_commit_scope")

        current_commit = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
        current_branch = _git(root, "symbolic-ref", "--short", "HEAD").decode("utf-8").strip()
        current_upstream = (
            _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
            .decode("utf-8")
            .strip()
        )
        if current_branch != "master":
            problems.append(f"tooling_publication:current_branch:{current_branch!r}")
        if current_upstream != "origin/master":
            problems.append(f"tooling_publication:current_upstream:{current_upstream!r}")
        ancestry = (
            _git(
                root,
                "rev-list",
                "--reverse",
                "--ancestry-path",
                f"{source_commit}..{current_commit}",
            )
            .decode("ascii")
            .splitlines()
        )
        if not ancestry:
            raise ToolingPublicationError("receipt-only child commit is missing")
        receipt_commit = ancestry[0]
        receipt_commit_line = (
            _git(root, "rev-list", "--parents", "-n", "1", receipt_commit).decode("ascii").split()
        )
        if receipt_commit_line != [receipt_commit, source_commit]:
            problems.append("tooling_publication:receipt_not_direct_source_child")
        receipt_commit_paths = _nul_paths(
            _git(
                root,
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                receipt_commit,
            )
        )
        if receipt_commit_paths != [TOOLING_RECEIPT_REL.as_posix()]:
            problems.append("tooling_publication:receipt_commit_not_receipt_only")
        committed_receipt = _git(root, "show", f"{receipt_commit}:{TOOLING_RECEIPT_REL.as_posix()}")
        if committed_receipt != raw_receipt:
            problems.append("tooling_publication:receipt_bytes_not_committed")
        if len(ancestry) < 2:
            problems.append(f"tooling_publication:publication_commit_count:{len(ancestry)}")
        else:
            state_commit = ancestry[1]
            state_commit_line = (
                _git(root, "rev-list", "--parents", "-n", "1", state_commit).decode("ascii").split()
            )
            if state_commit_line != [state_commit, receipt_commit]:
                problems.append("tooling_publication:state_not_direct_receipt_child")
            state_commit_paths = _nul_paths(
                _git(
                    root,
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "-z",
                    state_commit,
                )
            )
            if state_commit_paths != ["MISSION_STATE.json"]:
                problems.append("tooling_publication:state_commit_not_state_only")
            committed_state = _git(root, "show", f"{state_commit}:MISSION_STATE.json")
            try:
                physical_state = _read_regular_file(root / "MISSION_STATE.json", root)
            except FileNotFoundError as exc:
                raise ToolingPublicationError("committed mission state is missing") from exc
            if physical_state != committed_state:
                problems.append("tooling_publication:mission_state_bytes_not_committed")
            if len(ancestry) >= 3:
                baton_commit = ancestry[2]
                baton_commit_line = (
                    _git(root, "rev-list", "--parents", "-n", "1", baton_commit)
                    .decode("ascii")
                    .split()
                )
                if baton_commit_line != [baton_commit, state_commit]:
                    problems.append("tooling_publication:baton_not_direct_state_child")
                baton_paths = _nul_paths(
                    _git(
                        root,
                        "diff-tree",
                        "--root",
                        "--no-commit-id",
                        "--name-only",
                        "-r",
                        "-z",
                        baton_commit,
                    )
                )
                if baton_paths != ["CONTINUITY.md", "HANDOFF.md"]:
                    problems.append("tooling_publication:baton_commit_scope")
                previous_commit = baton_commit
                for descendant in ancestry[3:]:
                    descendant_line = (
                        _git(root, "rev-list", "--parents", "-n", "1", descendant)
                        .decode("ascii")
                        .split()
                    )
                    if descendant_line != [descendant, previous_commit]:
                        problems.append("tooling_publication:preflight_history_not_linear")
                    descendant_paths = _nul_paths(
                        _git(
                            root,
                            "diff-tree",
                            "--root",
                            "--no-commit-id",
                            "--name-only",
                            "-r",
                            "-z",
                            descendant,
                        )
                    )
                    if not descendant_paths or not all(
                        _preflight_mutable(relative) for relative in descendant_paths
                    ):
                        problems.append(
                            f"tooling_publication:preflight_descendant_scope:{descendant_paths}"
                        )
                    previous_commit = descendant

            immutable_paths = sorted(
                (set(EXPECTED_SOURCE_COMMIT_PATHS) - {"CONTINUITY.md", "MISSION_STATE.json"})
                | {
                    ITER135_HYPOTHESIS_REL,
                    "MISSION_STATE.json",
                    TOOLING_RECEIPT_REL.as_posix(),
                }
            )
            for relative in immutable_paths:
                h2_blob = _git(root, "show", f"{state_commit}:{relative}")
                current_blob = _git(root, "show", f"{current_commit}:{relative}")
                if current_blob != h2_blob:
                    problems.append(f"tooling_publication:immutable_path_changed:{relative}")
                try:
                    physical_blob = _read_regular_file(root / relative, root)
                except FileNotFoundError as exc:
                    raise ToolingPublicationError(f"immutable path is missing: {relative}") from exc
                if physical_blob != h2_blob:
                    problems.append(
                        f"tooling_publication:immutable_worktree_path_changed:{relative}"
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


def load_state(path: Path = STATE_PATH) -> dict:
    return json.loads(path.read_text())


def validate_state(state: dict, repo: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    if state.get("schema") != EXPECTED_SCHEMA:
        problems.append(f"schema:{state.get('schema')!r}!={EXPECTED_SCHEMA!r}")

    if state.get("canonical_repository") != str(repo):
        problems.append(f"canonical_repository:{state.get('canonical_repository')!r}")
    expected_boundary = {
        "isolated_from": "/Users/danielwahnich/workspace/aweb",
        "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
        "cross_workspace_access_requires_explicit_operator_request": True,
    }
    if state.get("workspace_boundary") != expected_boundary:
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
        problems.extend(_validate_tooling_publication(repo))
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
    for hypothesis in deprecated:
        if not (repo / hypothesis).is_file():
            problems.append(f"deprecated_pending_hypothesis_missing:{hypothesis}")

    active_hypothesis = state.get("active_hypothesis")
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

    return problems


def current_summary(state: dict) -> str:
    next_program = state["next_program"]
    return (
        f"iteration {state['current_completed_iteration']} / {state['current_verdict']} / "
        f"run {state['run_state']} / next iteration {next_program['iteration']} "
        f"{next_program['phase']}"
    )


if __name__ == "__main__":
    loaded = load_state()
    failures = validate_state(loaded)
    if failures:
        raise SystemExit("MISSION STATE INVALID:\n - " + "\n - ".join(failures))
    print(f"MISSION_STATE_OK {current_summary(loaded)}")
