from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import scripts.mission_state as mission_state
from scripts.mission_state import (
    CANONICAL_REPOSITORY,
    EMPTY_GIT_STATUS_SHA256,
    EXPECTED_SOURCE_COMMIT_PATHS,
    LAUNCH_AUTHORIZED_ACTIONS,
    LAUNCH_FORBIDDEN_ACTIONS,
    PREREGISTERED_AUTHORIZED_ACTIONS,
    PREREGISTERED_FORBIDDEN_ACTIONS,
    RECOVERY_REASON_CODE,
    RECOVERY_SOURCE_COMMIT_PATHS,
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


def _set_preregistered_phase(state: dict) -> None:
    state["next_program"]["phase"] = "PREREGISTERED_TOOLING_REQUIRED"
    state["next_program"]["authorized_actions"] = list(PREREGISTERED_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(PREREGISTERED_FORBIDDEN_ACTIONS)


def _commit_recovery_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    recovery_paths: tuple[str, ...] = RECOVERY_SOURCE_COMMIT_PATHS,
    generation_one_paths: tuple[str, ...] = EXPECTED_SOURCE_COMMIT_PATHS,
    topology_extra_commit: bool = False,
    extra_receipt_history: bool = False,
    include_baton: bool = True,
) -> dict[str, str]:
    _git(repo, "init", "-b", "master")
    _git(repo, "config", "user.name", "Sentinel Test")
    _git(repo, "config", "user.email", "sentinel-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "baseline")
    generation_one_source_parent = _git(repo, "rev-parse", "HEAD").decode().strip()
    for relative in generation_one_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(path.read_text() + "\n")
        else:
            path.write_text(f"frozen source: {relative}\n")
    _git(repo, "add", *EXPECTED_SOURCE_COMMIT_PATHS)
    extras = sorted(set(generation_one_paths) - set(EXPECTED_SOURCE_COMMIT_PATHS))
    if extras:
        _git(repo, "add", *extras)
    _git(repo, "commit", "-m", "generation one source freeze")
    generation_one_source = _git(repo, "rev-parse", "HEAD").decode().strip()

    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text('{"generation":1,"status":"superseded-after-ci-failure"}\n')
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation one receipt")
    generation_one_receipt = _git(repo, "rev-parse", "HEAD").decode().strip()

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation one state transition")
    generation_one_state = _git(repo, "rev-parse", "HEAD").decode().strip()

    (repo / "CONTINUITY.md").write_text("generation one transition log\n")
    (repo / "HANDOFF.md").write_text("GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION\n")
    _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
    _git(repo, "commit", "-m", "generation one offline baton")
    recovery_parent = _git(repo, "rev-parse", "HEAD").decode().strip()

    monkeypatch.setattr(
        mission_state, "GENERATION_ONE_SOURCE_PARENT", generation_one_source_parent
    )
    monkeypatch.setattr(mission_state, "GENERATION_ONE_SOURCE_COMMIT", generation_one_source)
    monkeypatch.setattr(mission_state, "GENERATION_ONE_RECEIPT_COMMIT", generation_one_receipt)
    monkeypatch.setattr(mission_state, "GENERATION_ONE_STATE_COMMIT", generation_one_state)
    monkeypatch.setattr(mission_state, "RECOVERY_SOURCE_PARENT", recovery_parent)
    monkeypatch.setattr(
        mission_state,
        "EXPECTED_RECOVERY_PUBLICATION",
        {
            "generation": 2,
            "supersedes_receipt_commit": generation_one_receipt,
            "recovery_parent": recovery_parent,
            "reason_code": RECOVERY_REASON_CODE,
        },
    )

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in recovery_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation two recovery source log\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation two recovery source baton\n")
        else:
            path.write_text(f"generation two recovery source: {relative}\n")
    _git(repo, "add", *recovery_paths)
    _git(repo, "commit", "-m", "generation two recovery source")
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
        "publication": {
            "generation": 2,
            "supersedes_receipt_commit": generation_one_receipt,
            "recovery_parent": recovery_parent,
            "reason_code": RECOVERY_REASON_CODE,
        },
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    if publication_overrides:
        receipt["publication"].update(publication_overrides)
    receipt["receipt_payload_sha256"] = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation two receipt only")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    if extra_receipt_history:
        receipt["unexpected_history_entry"] = True
        receipt["receipt_payload_sha256"] = hashlib.sha256(
            _canonical_json(
                {key: value for key, value in receipt.items() if key != "receipt_payload_sha256"}
            )
        ).hexdigest()
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
        _git(repo, "commit", "-m", "unexpected second recovery receipt")

    if topology_extra_commit:
        (repo / "unexpected-topology.txt").write_text("unexpected\n")
        _git(repo, "add", "unexpected-topology.txt")
        _git(repo, "commit", "-m", "unexpected topology edge")

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation two state transition")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()

    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation two transition log\n")
        (repo / "HANDOFF.md").write_text("GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation two offline baton")

    return {
        "generation_one_source": generation_one_source,
        "generation_one_receipt": generation_one_receipt,
        "generation_one_state": generation_one_state,
        "recovery_parent": recovery_parent,
        "recovery_source": source_commit,
        "recovery_receipt": receipt_commit,
        "recovery_state": state_commit,
    }


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


def test_canonical_identity_is_independent_of_physical_checkout_path(tmp_path: Path) -> None:
    alternate_checkout = tmp_path / "alternate-checkout"
    alternate_checkout.mkdir()
    repo, state = _minimal_state_repo(alternate_checkout)
    _set_preregistered_phase(state)

    problems = validate_state(state, repo)

    assert state["canonical_repository"] == CANONICAL_REPOSITORY
    assert problems == []


def test_preregistered_phase_actions_are_exact() -> None:
    state = copy.deepcopy(load_state())
    _set_preregistered_phase(state)
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


def test_tooling_phase_accepts_exact_generation_two_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_tooling_phase_accepts_detached_alternate_ci_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch)
    _git(repo, "checkout", "--detach", "HEAD")

    assert validate_state(state, repo) == []


def test_tooling_phase_rejects_origin_without_generation_two_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_recovery_publication(repo, state, monkeypatch)
    _git(repo, "update-ref", "refs/remotes/origin/master", commits["recovery_source"])

    assert "tooling_publication:receipt_commit_not_published" in validate_state(state, repo)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("generation", 1),
        ("supersedes_receipt_commit", "0" * 40),
        ("recovery_parent", "1" * 40),
        ("reason_code", "UNSTABLE_FREE_TEXT_REASON"),
    ],
)
def test_tooling_phase_rejects_wrong_recovery_publication_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    bad_value: object,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(
        repo,
        state,
        monkeypatch,
        publication_overrides={field: bad_value},
    )

    problems = validate_state(state, repo)

    assert any(
        problem.startswith(f"tooling_publication:receipt_publication_{field}:")
        for problem in problems
    )


def test_tooling_phase_rejects_wrong_recovery_source_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    wrong_scope = (*RECOVERY_SOURCE_COMMIT_PATHS, "unexpected-recovery-source.txt")
    _commit_recovery_publication(
        repo,
        state,
        monkeypatch,
        recovery_paths=wrong_scope,
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_tooling_phase_keeps_generation_one_scope_as_separate_immutable_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    wrong_baseline = (*EXPECTED_SOURCE_COMMIT_PATHS, "unexpected-generation-one-source.txt")
    _commit_recovery_publication(
        repo,
        state,
        monkeypatch,
        generation_one_paths=wrong_baseline,
    )

    assert "tooling_publication:generation_one_source_commit_scope" in validate_state(state, repo)


def test_tooling_phase_rejects_wrong_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(
        repo,
        state,
        monkeypatch,
        topology_extra_commit=True,
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:state_commit_not_state_only" in problems
    assert "tooling_publication:baton_commit_scope" in problems


def test_tooling_phase_rejects_incomplete_generation_two_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch, include_baton=False)

    assert "tooling_publication:generation_two_commit_count:1" in validate_state(state, repo)


def test_tooling_phase_rejects_nonexact_receipt_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch, extra_receipt_history=True)

    assert any(
        problem.startswith("tooling_publication:receipt_history:")
        for problem in validate_state(state, repo)
    )


def test_tooling_phase_accepts_authorized_preflight_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch)
    environment_receipt = repo / (
        "experiments/iter135_neuroncap_blind_braking_dose_response/env_receipts.json"
    )
    environment_receipt.write_text('{"read_only": true}\n')
    _git(repo, "add", str(environment_receipt.relative_to(repo)))
    _git(repo, "commit", "-m", "preflight environment receipt")

    assert validate_state(state, repo) == []


@pytest.mark.parametrize("relative_path", ["README.md", "MISSION_STATE.json"])
def test_tooling_phase_rejects_frozen_tool_or_state_descendant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch)
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
