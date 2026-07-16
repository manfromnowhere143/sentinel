from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts.mission_state import (
    EMPTY_GIT_STATUS_SHA256,
    EXPECTED_SOURCE_COMMIT_PATHS,
    LAUNCH_AUTHORIZED_ACTIONS,
    LAUNCH_FORBIDDEN_ACTIONS,
    TOOLING_FROZEN_AUTHORIZED_ACTIONS,
    TOOLING_FROZEN_FORBIDDEN_ACTIONS,
    TOOLING_RECEIPT_REL,
    _canonical_json,
    load_state,
    validate_state,
)


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("/usr/bin/git", *arguments),
        cwd=repo,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _minimal_state_repo(tmp_path: Path) -> tuple[Path, dict]:
    state = copy.deepcopy(load_state())
    state["canonical_repository"] = str(tmp_path)
    required_files = (
        state["current_result"],
        state["active_hypothesis"],
        *state["deprecated_pending_hypotheses"],
    )
    for relative in required_files:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = state["current_verdict"] if relative == state["current_result"] else "frozen\n"
        path.write_text(content)
    (tmp_path / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    return tmp_path, state


def _set_tooling_phase(state: dict) -> None:
    state["next_program"]["phase"] = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
    state["next_program"]["authorized_actions"] = list(TOOLING_FROZEN_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(TOOLING_FROZEN_FORBIDDEN_ACTIONS)


def _commit_source_and_green_receipt(repo: Path) -> None:
    _git(repo, "init", "-b", "master")
    _git(repo, "config", "user.name", "Sentinel Test")
    _git(repo, "config", "user.email", "sentinel-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "baseline")
    for relative in EXPECTED_SOURCE_COMMIT_PATHS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(path.read_text() + "\n")
        else:
            path.write_text(f"frozen source: {relative}\n")
    _git(repo, "add", *EXPECTED_SOURCE_COMMIT_PATHS)
    _git(repo, "commit", "-m", "source freeze")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "remote", "add", "origin", ".")
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    _git(repo, "branch", "--set-upstream-to", "origin/master", "master")
    source_paths = sorted(
        item.decode()
        for item in _git(
            repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            source_commit,
        ).split(b"\0")
        if item
    )
    source_parents = _git(repo, "show", "-s", "--format=%P", source_commit).decode().split()
    git_state = {
        "head": source_commit,
        "dirty_entries": [],
        "porcelain_v1_z_sha256": EMPTY_GIT_STATUS_SHA256,
        "branch": "master",
        "upstream": "origin/master",
        "upstream_head": source_commit,
        "parents": source_parents,
        "commit_paths": source_paths,
    }
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "repository": {
            "root": str(repo),
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    receipt["receipt_payload_sha256"] = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "receipt only")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)


def _commit_state_transition(repo: Path, state: dict, *, extra_path: str | None = None) -> None:
    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    if extra_path is not None:
        extra = repo / extra_path
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("unexpected\n")
        _git(repo, "add", extra_path)
    _git(repo, "commit", "-m", "state transition")


def _commit_offline_baton(repo: Path) -> None:
    (repo / "CONTINUITY.md").write_text("offline transition log\n")
    (repo / "HANDOFF.md").write_text("GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION\n")
    _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
    _git(repo, "commit", "-m", "offline baton")


def test_committed_mission_state_is_valid() -> None:
    assert validate_state(load_state()) == []


def test_next_iteration_must_follow_completed_iteration() -> None:
    state = copy.deepcopy(load_state())
    state["next_program"]["iteration"] = state["current_completed_iteration"] + 2

    assert any(problem.startswith("next_iteration:") for problem in validate_state(state))


def test_current_verdict_must_be_present_in_result() -> None:
    state = copy.deepcopy(load_state())
    state["current_verdict"] = "IMPOSSIBLE_VERDICT"

    assert "current_verdict_not_in_result:'IMPOSSIBLE_VERDICT'" in validate_state(state)


def test_state_cannot_roll_back_latest_completed_iteration() -> None:
    state = copy.deepcopy(load_state())
    state["current_completed_iteration"] = 133
    state["current_result"] = (
        "experiments/iter133_neuroncap_placebo_semantics_control_design/RESULT.md"
    )
    state["current_verdict"] = "NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE"
    state["next_program"]["iteration"] = 134

    assert "current_completed_iteration:133!=134" in validate_state(state)


def test_every_pending_hypothesis_must_be_classified() -> None:
    state = copy.deepcopy(load_state())
    state["deprecated_pending_hypotheses"] = []

    assert any(
        problem.startswith("pending_hypothesis_classification:")
        for problem in validate_state(state)
    )


def test_storage_gate_names_the_dedicated_execution_filesystem() -> None:
    state = copy.deepcopy(load_state())
    storage = state["storage_gate"]
    storage["remote_execution_filesystem_path"] = "/"
    storage["analytic_output_root"] = "/opt/sentinel-stack/NeuroNCAP/outoutput"

    problems = validate_state(state)

    assert "storage_gate:remote_execution_filesystem_path:'/'" in problems
    assert "storage_gate:analytic_output_root:'/opt/sentinel-stack/NeuroNCAP/outoutput'" in problems


def test_storage_gate_thresholds_cannot_be_weakened() -> None:
    state = copy.deepcopy(load_state())
    storage = state["storage_gate"]
    storage["minimum_local_free_gib_before_new_proof_collection"] = 1
    storage["minimum_remote_execution_filesystem_free_gib_before_gpu_launch"] = 99
    storage["minimum_remote_execution_filesystem_reserve_gib_after_projected_output"] = 24

    problems = validate_state(state)

    assert "storage_gate:minimum_local_free_gib_before_new_proof_collection:1" in problems
    assert (
        "storage_gate:minimum_remote_execution_filesystem_free_gib_before_gpu_launch:99" in problems
    )
    assert (
        "storage_gate:minimum_remote_execution_filesystem_reserve_gib_after_projected_output:24"
        in problems
    )


def test_workspace_boundary_is_machine_enforced() -> None:
    state = copy.deepcopy(load_state())
    state["canonical_repository"] = "/Users/danielwahnich/workspace/aweb"
    state["workspace_boundary"]["cross_workspace_access_requires_explicit_operator_request"] = False

    problems = validate_state(state)

    assert "canonical_repository:'/Users/danielwahnich/workspace/aweb'" in problems
    assert any(problem.startswith("workspace_boundary:") for problem in problems)


def test_preregistered_phase_actions_are_exact() -> None:
    state = copy.deepcopy(load_state())
    state["next_program"]["authorized_actions"].append("unfrozen extra action")
    state["next_program"]["forbidden_actions"].reverse()

    problems = validate_state(state)

    assert any(
        problem.startswith("phase_authorized_actions:PREREGISTERED_TOOLING_REQUIRED:")
        for problem in problems
    )
    assert any(
        problem.startswith("phase_forbidden_actions:PREREGISTERED_TOOLING_REQUIRED:")
        for problem in problems
    )


def test_tooling_phase_fails_closed_without_receipt(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)

    problems = validate_state(state, repo)

    assert (
        "tooling_publication:receipt_missing:"
        "experiments/iter135_neuroncap_blind_braking_dose_response/"
        "tooling_verification_receipt.json"
    ) in problems


def test_tooling_phase_fails_closed_on_malformed_receipt(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    receipt = repo / TOOLING_RECEIPT_REL
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text('{"schema":"iter135.tooling_verification.v2", invalid')

    problems = validate_state(state, repo)

    assert any(
        problem.startswith("tooling_publication:structural_probe:ToolingPublicationError:")
        and "malformed receipt JSON" in problem
        for problem in problems
    )


def test_tooling_phase_rejects_action_mismatch_even_without_receipt(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    state["next_program"]["authorized_actions"][0] = "run an unfrozen preflight"

    problems = validate_state(state, repo)

    assert any(
        problem.startswith("phase_authorized_actions:TOOLING_FROZEN_PREFLIGHT_REQUIRED:")
        for problem in problems
    )


@pytest.mark.parametrize("phase", ["LAUNCH_AUTHORIZED", "RUNNING", "ANALYSIS_REQUIRED"])
def test_post_preflight_phases_fail_closed_without_artifact_contracts(
    tmp_path: Path, phase: str
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    state["next_program"]["phase"] = phase
    if phase == "LAUNCH_AUTHORIZED":
        state["next_program"]["authorized_actions"] = list(LAUNCH_AUTHORIZED_ACTIONS)
        state["next_program"]["forbidden_actions"] = list(LAUNCH_FORBIDDEN_ACTIONS)
    if phase == "RUNNING":
        state["run_state"] = "RUNNING"

    problems = validate_state(state, repo)

    assert f"phase_artifact_contract:{phase}:not_implemented" in problems


def test_tooling_phase_accepts_exact_published_h_h1_h2_topology(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _commit_source_and_green_receipt(repo)
    _set_tooling_phase(state)
    _commit_state_transition(repo, state)

    assert validate_state(state, repo) == []


def test_tooling_phase_rejects_h2_with_extra_path(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _commit_source_and_green_receipt(repo)
    _set_tooling_phase(state)
    _commit_state_transition(repo, state, extra_path="unexpected.txt")

    problems = validate_state(state, repo)

    assert "tooling_publication:state_commit_not_state_only" in problems


def test_tooling_phase_accepts_exact_offline_baton_h3(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _commit_source_and_green_receipt(repo)
    _set_tooling_phase(state)
    _commit_state_transition(repo, state)
    _commit_offline_baton(repo)

    assert validate_state(state, repo) == []


def test_tooling_phase_accepts_authorized_preflight_descendant(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _commit_source_and_green_receipt(repo)
    _set_tooling_phase(state)
    _commit_state_transition(repo, state)
    _commit_offline_baton(repo)
    environment_receipt = repo / (
        "experiments/iter135_neuroncap_blind_braking_dose_response/env_receipts.json"
    )
    environment_receipt.write_text('{"read_only": true}\n')
    _git(repo, "add", str(environment_receipt.relative_to(repo)))
    _git(repo, "commit", "-m", "preflight environment receipt")

    assert validate_state(state, repo) == []


@pytest.mark.parametrize("relative_path", ["README.md", "MISSION_STATE.json"])
def test_tooling_phase_rejects_frozen_tool_or_state_descendant(
    tmp_path: Path, relative_path: str
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _commit_source_and_green_receipt(repo)
    _set_tooling_phase(state)
    _commit_state_transition(repo, state)
    _commit_offline_baton(repo)
    frozen = repo / relative_path
    frozen.write_text(frozen.read_text() + "\n")
    _git(repo, "add", relative_path)
    _git(repo, "commit", "-m", "forbidden frozen mutation")

    problems = validate_state(state, repo)

    assert f"tooling_publication:immutable_path_changed:{relative_path}" in problems
    assert any(
        problem.startswith("tooling_publication:preflight_descendant_scope:")
        for problem in problems
    )
