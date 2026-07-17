from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

import scripts.mission_state as mission_state
from scripts.mission_state import (
    CANONICAL_REPOSITORY,
    EMPTY_GIT_STATUS_SHA256,
    EXPECTED_SOURCE_COMMIT_PATHS,
    GENERATION_FIVE_REASON_CODE,
    GENERATION_FIVE_SOURCE_COMMIT_PATHS,
    GENERATION_SIX_REASON_CODE,
    GENERATION_SIX_SOURCE_COMMIT_PATHS,
    GENERATION_SEVEN_REASON_CODE,
    GENERATION_SEVEN_SOURCE_COMMIT_PATHS,
    GENERATION_EIGHT_REASON_CODE,
    GENERATION_EIGHT_SOURCE_COMMIT_PATHS,
    GENERATION_NINE_REASON_CODE,
    GENERATION_NINE_SOURCE_COMMIT_PATHS,
    GENERATION_TEN_REASON_CODE,
    GENERATION_TEN_SOURCE_COMMIT_PATHS,
    GENERATION_FOUR_REASON_CODE,
    GENERATION_FOUR_SOURCE_COMMIT_PATHS,
    GENERATION_THREE_REASON_CODE,
    GENERATION_THREE_SOURCE_COMMIT_PATHS,
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
    validate_local_launch_candidate,
    validate_state,
)


AUTH_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py"
)
AUTH_SPEC = importlib.util.spec_from_file_location("mission_state_launch_controller", AUTH_MODULE_PATH)
assert AUTH_SPEC is not None and AUTH_SPEC.loader is not None
launch_controller = importlib.util.module_from_spec(AUTH_SPEC)
AUTH_SPEC.loader.exec_module(launch_controller)


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("/usr/bin/git", *arguments),
        cwd=repo,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _complete_tooling_receipt(receipt: dict) -> dict:
    receipt.update(
        {
            "inventory": {
                "contract": "frozen fixture inventory",
                "tests": [],
                "python_tools": [],
                "python_files": [],
                "shell_files": [],
                "data_files": [],
                "control_files": [],
                "tested_files": [],
            },
            "inventory_sha256": "1" * 64,
            "toolchain": {},
            "environment_contract": {},
            "files": {},
            "file_content_set_sha256": "2" * 64,
            "command_contract": [],
            "commands": [],
            "timing": {
                "started_at_utc": "2026-07-16T00:00:00Z",
                "finished_at_utc": "2026-07-16T00:00:01Z",
                "wall_duration_ns": 1_000_000_000,
                "monotonic_duration_ns": 1_000_000_000,
            },
        }
    )
    receipt["receipt_payload_sha256"] = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    return receipt


def test_actual_frozen_module_loaders_restore_sys_modules_lifecycle(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "-b", "master")
    _git(tmp_path, "config", "user.name", "Sentinel Test")
    _git(tmp_path, "config", "user.email", "sentinel-test@example.invalid")
    source_root = Path(__file__).resolve().parents[1]
    for relative in (
        mission_state.TOOLING_VALIDATOR_REL,
        mission_state.LAUNCH_CONTROLLER_REL,
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source_root / relative).read_bytes())
    _git(
        tmp_path,
        "add",
        mission_state.TOOLING_VALIDATOR_REL.as_posix(),
        mission_state.LAUNCH_CONTROLLER_REL.as_posix(),
    )
    _git(tmp_path, "commit", "-m", "actual frozen controller sources")
    source_commit = _git(tmp_path, "rev-parse", "HEAD").decode().strip()
    mission_module_name = "sentinel_iter135_tooling_receipt_validator"
    controller_module_name = "iter135_frozen_tooling_receipt_validator"
    launch_module_name = "sentinel_iter135_launch_controller"
    previous_mission_module = sys.modules.get(mission_module_name)
    previous_controller_module = sys.modules.get(controller_module_name)
    previous_launch_module = sys.modules.get(launch_module_name)

    mission_validator = mission_state._load_tooling_receipt_validator(
        tmp_path,
        source_commit,
    )
    controller_validator = launch_controller._load_frozen_tooling_receipt_validator(
        tmp_path,
        source_commit,
    )
    launch_validator = mission_state._load_launch_controller(tmp_path, source_commit)

    assert callable(mission_validator)
    assert callable(controller_validator)
    assert callable(launch_validator)
    assert sys.modules.get(mission_module_name) is previous_mission_module
    assert sys.modules.get(controller_module_name) is previous_controller_module
    assert sys.modules.get(launch_module_name) is previous_launch_module


def _structural_launch_controller(
    repo: Path,
    *,
    phase: str,
    tooling_receipt_commit: str,
    tooling_baton_commit: str,
    descendants: list[str],
    upstream_commit: str,
    candidate: bool = False,
) -> dict:
    del tooling_receipt_commit, tooling_baton_commit
    problems: list[str] = []
    expected_count = 7 if phase == "LAUNCH_AUTHORIZED" else 4
    if phase == "LAUNCH_AUTHORIZED" and len(descendants) != expected_count:
        problems.append(f"authorization:launch-descendant-count:{len(descendants)}")
    expected_upstream = (
        descendants[3]
        if candidate and len(descendants) >= 4
        else descendants[-1] if descendants else None
    )
    if upstream_commit != expected_upstream:
        problems.append(
            "authorization:preflight-not-on-origin-master"
            if candidate
            else "authorization:head-not-on-origin-master"
        )
    references = {}
    if len(descendants) >= 7:
        references = {
            "MISSION_STATE.json": descendants[4],
            launch_controller.MANIFEST_REL: descendants[5],
            launch_controller.ACTIVATION_REL: descendants[6],
        }
    if candidate:
        problems.append("authorization:candidate-non-authoritative")
    return {
        "problems": problems,
        "references": references,
        "authority": "non-authoritative-local-candidate" if candidate else "origin-published",
        "launch_authorized": not candidate and not problems,
        "candidate_valid": candidate and problems == ["authorization:candidate-non-authoritative"],
    }


def _use_structural_launch_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mission_state,
        "_load_launch_controller",
        lambda _repo, _source_commit: _structural_launch_controller,
    )


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
    _complete_tooling_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation two receipt only")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    if extra_receipt_history:
        receipt["timing"]["wall_duration_ns"] += 1
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
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()

    return {
        "generation_one_source": generation_one_source,
        "generation_one_receipt": generation_one_receipt,
        "generation_one_state": generation_one_state,
        "recovery_parent": recovery_parent,
        "recovery_source": source_commit,
        "recovery_receipt": receipt_commit,
        "recovery_state": state_commit,
        "recovery_baton": baton_commit,
    }


def _commit_generation_three_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    receipt_root_mutation: str | None = None,
    receipt_nested_mutation: bool = False,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_THREE_SOURCE_COMMIT_PATHS,
) -> dict[str, str]:
    generation_two = _commit_recovery_publication(repo, state, monkeypatch)
    generation_two_baton = generation_two["recovery_baton"]
    monkeypatch.setattr(
        mission_state, "GENERATION_TWO_SOURCE_COMMIT", generation_two["recovery_source"]
    )
    monkeypatch.setattr(
        mission_state, "GENERATION_TWO_RECEIPT_COMMIT", generation_two["recovery_receipt"]
    )
    monkeypatch.setattr(
        mission_state, "GENERATION_TWO_STATE_COMMIT", generation_two["recovery_state"]
    )
    monkeypatch.setattr(mission_state, "GENERATION_TWO_BATON_COMMIT", generation_two_baton)
    monkeypatch.setattr(mission_state, "GENERATION_THREE_SOURCE_PARENT", generation_two_baton)
    expected_publication = {
        "generation": 3,
        "supersedes_receipt_commit": generation_two["recovery_receipt"],
        "recovery_parent": generation_two_baton,
        "reason_code": GENERATION_THREE_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)
    monkeypatch.setattr(
        mission_state,
        "_load_tooling_receipt_validator",
        lambda _repo, _source_commit: lambda _receipt, **_kwargs: [],
    )

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation three source transition\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation three source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            path.write_bytes(
                _git(
                    source_repo,
                    "show",
                    f"{mission_state.GENERATION_THREE_SOURCE_COMMIT}:{relative}",
                )
            )
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return ['nested receipt invalid'] if receipt.get('commands') else []\n"
            )
        else:
            path.write_text(f"generation three source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation three source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
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
    git_state = {
        "head": source_commit,
        "dirty_entries": [],
        "porcelain_v1_z_sha256": EMPTY_GIT_STATUS_SHA256,
        "branch": "master",
        "upstream": "origin/master",
        "upstream_head": source_commit,
        "parents": [generation_two_baton],
        "commit_paths": source_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    if receipt_nested_mutation:
        receipt["commands"] = [{"forged": True}]
    if receipt_root_mutation == "extra":
        receipt["unexpected_root"] = True
    elif receipt_root_mutation == "missing":
        receipt.pop("timing")
    elif receipt_root_mutation is not None:
        raise AssertionError(f"unsupported receipt mutation: {receipt_root_mutation}")
    if receipt_root_mutation is not None or receipt_nested_mutation:
        receipt["receipt_payload_sha256"] = hashlib.sha256(
            _canonical_json(
                {key: value for key, value in receipt.items() if key != "receipt_payload_sha256"}
            )
        ).hexdigest()
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation three receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation three state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation three tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation three tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation three tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_two,
        "generation_three_source": source_commit,
        "generation_three_receipt": receipt_commit,
        "generation_three_state": state_commit,
        "generation_three_baton": baton_commit,
    }


def _commit_generation_four_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_FOUR_SOURCE_COMMIT_PATHS,
    extra_receipt_history: bool = False,
    wrong_source_parent: bool = False,
    hostile_generation_three_baton: bool = False,
) -> dict[str, str]:
    generation_three = _commit_generation_three_publication(repo, state, monkeypatch)
    generation_three_baton = generation_three["generation_three_baton"]
    monkeypatch.setattr(
        mission_state,
        "GENERATION_THREE_SOURCE_COMMIT",
        generation_three["generation_three_source"],
    )
    monkeypatch.setattr(
        mission_state,
        "GENERATION_THREE_RECEIPT_COMMIT",
        generation_three["generation_three_receipt"],
    )
    monkeypatch.setattr(
        mission_state,
        "GENERATION_THREE_STATE_COMMIT",
        generation_three["generation_three_state"],
    )
    monkeypatch.setattr(
        mission_state,
        "GENERATION_THREE_BATON_COMMIT",
        generation_three_baton,
    )
    if wrong_source_parent or hostile_generation_three_baton:
        unexpected = repo / "unexpected-generation-three-topology.txt"
        unexpected.write_text("not the frozen generation-three baton\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-three topology edge")
        synthetic_parent = _git(repo, "rev-parse", "HEAD").decode().strip()
        if hostile_generation_three_baton:
            monkeypatch.setattr(
                mission_state,
                "GENERATION_THREE_BATON_COMMIT",
                synthetic_parent,
            )
            generation_three_baton = synthetic_parent
    monkeypatch.setattr(
        mission_state,
        "GENERATION_FOUR_SOURCE_PARENT",
        generation_three_baton,
    )
    expected_publication = {
        "generation": 4,
        "supersedes_receipt_commit": generation_three["generation_three_receipt"],
        "recovery_parent": generation_three_baton,
        "reason_code": GENERATION_FOUR_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation four source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation four source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # The live controller binds the ACTIVE generation. These historical generation-four
            # tests need a generation-four-era controller, so rebind its frozen publication
            # expectation before writing it into the synthetic repository.
            controller_source = (source_repo / relative).read_text()
            controller_source = controller_source.replace(
                '    "generation": 10,\n'
                '    "supersedes_receipt_commit": GENERATION_NINE_RECEIPT_COMMIT,\n'
                '    "recovery_parent": GENERATION_NINE_STAGE_ZERO_COMMIT,\n'
                '    "reason_code": GENERATION_TEN_REASON,\n',
                '    "generation": 4,\n'
                '    "supersedes_receipt_commit": GENERATION_THREE_RECEIPT_COMMIT,\n'
                '    "recovery_parent": GENERATION_THREE_BATON_COMMIT,\n'
                '    "reason_code": '
                '"B3_CI_STRUCTURAL_GIT_READER_TOOLCHAIN_ROOT_FAILURE",\n',
            )
            controller_source = controller_source.replace(
                launch_controller.GENERATION_THREE_RECEIPT_COMMIT,
                generation_three["generation_three_receipt"],
            ).replace(
                launch_controller.GENERATION_THREE_BATON_COMMIT,
                generation_three_baton,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation four source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation four source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {
            **generation_three,
            "generation_four_source": source_commit,
        }

    source_commit_paths = sorted(
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation four receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    if extra_receipt_history:
        receipt["timing"]["wall_duration_ns"] += 1
        receipt["receipt_payload_sha256"] = hashlib.sha256(
            _canonical_json(
                {key: value for key, value in receipt.items() if key != "receipt_payload_sha256"}
            )
        ).hexdigest()
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
        _git(repo, "commit", "-m", "unexpected second generation four receipt")

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation four state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation four tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation four tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation four tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_three,
        "generation_four_source": source_commit,
        "generation_four_receipt": receipt_commit,
        "generation_four_state": state_commit,
        "generation_four_baton": baton_commit,
    }


def _commit_generation_five_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_FIVE_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
    include_state: bool = True,
) -> dict[str, str]:
    """Build the exact generation-five topology on top of a real generation-four chain."""

    generation_four = _commit_generation_four_publication(repo, state, monkeypatch)
    generation_four_baton = generation_four["generation_four_baton"]
    for name, key in (
        ("GENERATION_FOUR_SOURCE_COMMIT", "generation_four_source"),
        ("GENERATION_FOUR_RECEIPT_COMMIT", "generation_four_receipt"),
        ("GENERATION_FOUR_STATE_COMMIT", "generation_four_state"),
        ("GENERATION_FOUR_BATON_COMMIT", "generation_four_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_four[key])
    monkeypatch.setattr(
        mission_state, "GENERATION_FOUR_SOURCE_COMMIT_PATHS", GENERATION_FOUR_SOURCE_COMMIT_PATHS
    )
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-four-topology.txt"
        unexpected.write_text("not the frozen generation-four baton\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-four topology edge")
    monkeypatch.setattr(mission_state, "GENERATION_FIVE_SOURCE_PARENT", generation_four_baton)
    expected_publication = {
        "generation": 5,
        "supersedes_receipt_commit": generation_four["generation_four_receipt"],
        "recovery_parent": generation_four_baton,
        "reason_code": GENERATION_FIVE_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation five source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation five source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # Rebind the live generation-six controller to its generation-five era before the
            # synthetic SHA substitution.
            controller_source = (source_repo / relative).read_text()
            controller_source = controller_source.replace(
                '''    "generation": 10,
    "supersedes_receipt_commit": GENERATION_NINE_RECEIPT_COMMIT,
    "recovery_parent": GENERATION_NINE_STAGE_ZERO_COMMIT,
    "reason_code": GENERATION_TEN_REASON,
''',
                '    "generation": 5,\n'
                '    "supersedes_receipt_commit": GENERATION_FOUR_RECEIPT_COMMIT,\n'
                '    "recovery_parent": GENERATION_FOUR_BATON_COMMIT,\n'
                '    "reason_code": '
                '"B4_H_CONTRACT_UNIAD_LOAD_BEARING_UNTRACKED_SYMLINK",\n',
            )
            controller_source = controller_source.replace(
                launch_controller.GENERATION_FOUR_RECEIPT_COMMIT,
                generation_four["generation_four_receipt"],
            ).replace(
                launch_controller.GENERATION_FOUR_BATON_COMMIT,
                generation_four_baton,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation five\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation five source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation five source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_four, "generation_five_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation five receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    if not include_state:
        return {
            **generation_four,
            "generation_five_source": source_commit,
            "generation_five_receipt": receipt_commit,
        }

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation five state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation five tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation five tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation five tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_four,
        "generation_five_source": source_commit,
        "generation_five_receipt": receipt_commit,
        "generation_five_state": state_commit,
        "generation_five_baton": baton_commit,
    }


def _commit_generation_six_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_SIX_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-six topology on top of the real truncated generation-five chain.

    Generation five published only its source and receipt before its structural probe fired, so
    the synthetic history here carries no generation-five state or baton commit and generation six
    parents directly off the generation-five receipt.
    """

    generation_five = _commit_generation_five_publication(
        repo, state, monkeypatch, include_state=False
    )
    generation_five_receipt = generation_five["generation_five_receipt"]
    monkeypatch.setattr(
        mission_state,
        "GENERATION_FIVE_SOURCE_COMMIT",
        generation_five["generation_five_source"],
    )
    monkeypatch.setattr(
        mission_state, "GENERATION_FIVE_RECEIPT_COMMIT", generation_five_receipt
    )
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-five-topology.txt"
        unexpected.write_text("not the frozen generation-five receipt\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-five topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_SIX_SOURCE_PARENT", generation_five_receipt
    )
    expected_publication = {
        "generation": 6,
        "supersedes_receipt_commit": generation_five_receipt,
        "recovery_parent": generation_five_receipt,
        "reason_code": GENERATION_SIX_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation six source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation six source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # Rebind the live generation-seven controller to its generation-six era before the
            # synthetic SHA substitution.
            controller_source = (source_repo / relative).read_text()
            controller_source = controller_source.replace(
                '    "generation": 10,\n'
                '    "supersedes_receipt_commit": GENERATION_NINE_RECEIPT_COMMIT,\n'
                '    "recovery_parent": GENERATION_NINE_STAGE_ZERO_COMMIT,\n'
                '    "reason_code": GENERATION_TEN_REASON,\n',
                '    "generation": 6,\n'
                '    "supersedes_receipt_commit": GENERATION_FIVE_RECEIPT_COMMIT,\n'
                '    "recovery_parent": GENERATION_FIVE_RECEIPT_COMMIT,\n'
                '    "reason_code": '
                '"T5_FROZEN_STRUCTURAL_VALIDATOR_STALE_RECEIPT_HISTORY",\n',
            )
            controller_source = controller_source.replace(
                launch_controller.GENERATION_FIVE_RECEIPT_COMMIT,
                generation_five_receipt,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation six\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation six source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation six source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_five, "generation_six_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation six receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation six state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation six tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation six tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation six tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_five,
        "generation_six_source": source_commit,
        "generation_six_receipt": receipt_commit,
        "generation_six_state": state_commit,
        "generation_six_baton": baton_commit,
    }


def _commit_generation_seven_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_SEVEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-seven topology on top of a complete generation-six chain."""

    generation_six = _commit_generation_six_publication(repo, state, monkeypatch)
    generation_six_baton = generation_six["generation_six_baton"]
    for name, key in (
        ("GENERATION_SIX_SOURCE_COMMIT", "generation_six_source"),
        ("GENERATION_SIX_RECEIPT_COMMIT", "generation_six_receipt"),
        ("GENERATION_SIX_STATE_COMMIT", "generation_six_state"),
        ("GENERATION_SIX_BATON_COMMIT", "generation_six_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_six[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-six-topology.txt"
        unexpected.write_text("not the frozen generation-six baton\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-six topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_SEVEN_SOURCE_PARENT", generation_six_baton
    )
    expected_publication = {
        "generation": 7,
        "supersedes_receipt_commit": generation_six["generation_six_receipt"],
        "recovery_parent": generation_six_baton,
        "reason_code": GENERATION_SEVEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation seven source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation seven source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # The live controller now binds the generation-eight publication, so this
            # generation-seven-era fixture rewrites the live literals back to the
            # generation-seven shape bound to the fixture chain.
            controller_source = (source_repo / relative).read_text()
            controller_source = (
                controller_source.replace(
                    launch_controller.GENERATION_NINE_RECEIPT_COMMIT,
                    generation_six["generation_six_receipt"],
                )
                .replace(
                    launch_controller.GENERATION_NINE_STAGE_ZERO_COMMIT,
                    generation_six_baton,
                )
                .replace('"generation": 10,', '"generation": 7,')
                .replace(
                    launch_controller.GENERATION_TEN_REASON,
                    GENERATION_SEVEN_REASON_CODE,
                )
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation seven\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation seven source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation seven source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_six, "generation_seven_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation seven receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation seven state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation seven tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation seven tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation seven tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_six,
        "generation_seven_source": source_commit,
        "generation_seven_receipt": receipt_commit,
        "generation_seven_state": state_commit,
        "generation_seven_baton": baton_commit,
    }


def _commit_generation_eight_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_EIGHT_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-eight topology on top of a complete generation-seven chain."""

    generation_seven = _commit_generation_seven_publication(repo, state, monkeypatch)
    generation_seven_baton = generation_seven["generation_seven_baton"]
    for name, key in (
        ("GENERATION_SEVEN_SOURCE_COMMIT", "generation_seven_source"),
        ("GENERATION_SEVEN_RECEIPT_COMMIT", "generation_seven_receipt"),
        ("GENERATION_SEVEN_STATE_COMMIT", "generation_seven_state"),
        ("GENERATION_SEVEN_BATON_COMMIT", "generation_seven_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_seven[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-seven-topology.txt"
        unexpected.write_text("not the frozen generation-seven baton\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-seven topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_EIGHT_SOURCE_PARENT", generation_seven_baton
    )
    expected_publication = {
        "generation": 8,
        "supersedes_receipt_commit": generation_seven["generation_seven_receipt"],
        "recovery_parent": generation_seven_baton,
        "reason_code": GENERATION_EIGHT_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation eight source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation eight source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # The live controller already binds generation eight; rebind its frozen
            # generation-seven receipt and baton literals to this fixture chain.
            controller_source = (source_repo / relative).read_text()
            controller_source = (
                controller_source.replace(
                    launch_controller.GENERATION_NINE_RECEIPT_COMMIT,
                    generation_seven["generation_seven_receipt"],
                )
                .replace(
                    launch_controller.GENERATION_NINE_STAGE_ZERO_COMMIT,
                    generation_seven_baton,
                )
                .replace('"generation": 10,', '"generation": 8,')
                .replace(
                    launch_controller.GENERATION_TEN_REASON,
                    GENERATION_EIGHT_REASON_CODE,
                )
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation eight\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation eight source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation eight source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_seven, "generation_eight_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation eight receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation eight state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation eight tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation eight tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation eight tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_seven,
        "generation_eight_source": source_commit,
        "generation_eight_receipt": receipt_commit,
        "generation_eight_state": state_commit,
        "generation_eight_baton": baton_commit,
    }


def _commit_generation_nine_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_NINE_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-nine topology on top of a complete generation-eight chain."""

    generation_eight = _commit_generation_eight_publication(repo, state, monkeypatch)
    generation_eight_baton = generation_eight["generation_eight_baton"]
    for name, key in (
        ("GENERATION_EIGHT_SOURCE_COMMIT", "generation_eight_source"),
        ("GENERATION_EIGHT_RECEIPT_COMMIT", "generation_eight_receipt"),
        ("GENERATION_EIGHT_STATE_COMMIT", "generation_eight_state"),
        ("GENERATION_EIGHT_BATON_COMMIT", "generation_eight_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_eight[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-eight-topology.txt"
        unexpected.write_text("not the frozen generation-eight baton\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-eight topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_NINE_SOURCE_PARENT", generation_eight_baton
    )
    expected_publication = {
        "generation": 9,
        "supersedes_receipt_commit": generation_eight["generation_eight_receipt"],
        "recovery_parent": generation_eight_baton,
        "reason_code": GENERATION_NINE_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation nine source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation nine source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # The live controller already binds generation nine; rebind its frozen
            # generation-eight receipt and baton literals to this fixture chain.
            controller_source = (source_repo / relative).read_text()
            controller_source = (
                controller_source.replace(
                    launch_controller.GENERATION_NINE_RECEIPT_COMMIT,
                    generation_eight["generation_eight_receipt"],
                )
                .replace(
                    launch_controller.GENERATION_NINE_STAGE_ZERO_COMMIT,
                    generation_eight_baton,
                )
                .replace('"generation": 10,', '"generation": 9,')
                .replace(
                    launch_controller.GENERATION_TEN_REASON,
                    GENERATION_NINE_REASON_CODE,
                )
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation nine\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation nine source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation nine source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_eight, "generation_nine_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation nine receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation nine state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation nine tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation nine tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation nine tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_eight,
        "generation_nine_source": source_commit,
        "generation_nine_receipt": receipt_commit,
        "generation_nine_state": state_commit,
        "generation_nine_baton": baton_commit,
    }


def _commit_generation_ten_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_TEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-ten topology on top of a complete generation-nine chain."""

    generation_nine = _commit_generation_nine_publication(repo, state, monkeypatch)
    generation_nine_baton = generation_nine["generation_nine_baton"]
    for name, key in (
        ("GENERATION_NINE_SOURCE_COMMIT", "generation_nine_source"),
        ("GENERATION_NINE_RECEIPT_COMMIT", "generation_nine_receipt"),
        ("GENERATION_NINE_STATE_COMMIT", "generation_nine_state"),
        ("GENERATION_NINE_BATON_COMMIT", "generation_nine_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_nine[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-nine-topology.txt"
        unexpected.write_text("not the frozen generation-nine tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-nine topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_TEN_SOURCE_PARENT", generation_nine_baton
    )
    expected_publication = {
        "generation": 10,
        "supersedes_receipt_commit": generation_nine["generation_nine_receipt"],
        "recovery_parent": generation_nine_baton,
        "reason_code": GENERATION_TEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    source_repo = Path(__file__).resolve().parents[1]
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation ten source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation ten source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            # The live controller already binds generation ten; rebind its frozen
            # generation-nine receipt and stage-zero parent literals to this fixture chain.
            controller_source = (source_repo / relative).read_text()
            controller_source = controller_source.replace(
                launch_controller.GENERATION_NINE_RECEIPT_COMMIT,
                generation_nine["generation_nine_receipt"],
            ).replace(
                launch_controller.GENERATION_NINE_STAGE_ZERO_COMMIT,
                generation_nine_baton,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation ten\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation ten source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation ten source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_nine, "generation_ten_source": source_commit}

    source_commit_paths = sorted(
        item.decode()
        for item in _git(
            repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", source_commit
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
        "commit_paths": source_commit_paths,
    }
    publication = dict(expected_publication)
    if publication_overrides:
        publication.update(publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": CANONICAL_REPOSITORY,
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    receipt_path = repo / TOOLING_RECEIPT_REL
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", TOOLING_RECEIPT_REL.as_posix())
    _git(repo, "commit", "-m", "generation ten receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation ten state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation ten tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation ten tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation ten tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_nine,
        "generation_ten_source": source_commit,
        "generation_ten_receipt": receipt_commit,
        "generation_ten_state": state_commit,
        "generation_ten_baton": baton_commit,
    }


def _append_launch_authorization_chain(
    repo: Path, state: dict, commits: dict[str, str]
) -> dict[str, str]:
    experiment = repo / mission_state.ITER135_EXPERIMENT_REL

    def commit_json(relative: str, value: dict, message: str) -> str:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        _git(repo, "add", relative)
        _git(repo, "commit", "-m", message)
        return _git(repo, "rev-parse", "HEAD").decode().strip()

    host_packet = {
        "schema": launch_controller.HOST_PACKET_SCHEMA,
        "source_commit": commits["generation_three_baton"],
        "files": {},
    }
    host_packet_path = repo / launch_controller.HOST_PACKET_REL
    host_packet_path.parent.mkdir(parents=True, exist_ok=True)
    host_packet_path.write_text(json.dumps(host_packet, indent=2, sort_keys=True) + "\n")
    host_packet_payload = host_packet_path.read_bytes()
    host_path = repo / launch_controller.HOST_REL
    host_receipt = {
        "schema": launch_controller.HOST_SCHEMA,
        "verdict": launch_controller.HOST_VERDICT,
        "problem_count": 0,
        "problems": [],
        "packet_manifest_sha256": hashlib.sha256(host_packet_payload).hexdigest(),
        "packet": {
            "schema": launch_controller.HOST_PACKET_SCHEMA,
            "source_commit": host_packet["source_commit"],
            "manifest": {"sha256": hashlib.sha256(host_packet_payload).hexdigest()},
        },
    }
    host_receipt["receipt_payload_sha256"] = hashlib.sha256(
        launch_controller._canonical_json(host_receipt)
    ).hexdigest()
    host_path.write_text(json.dumps(host_receipt, indent=2, sort_keys=True) + "\n")
    _git(repo, "add", launch_controller.HOST_PACKET_REL, launch_controller.HOST_REL)
    _git(repo, "commit", "-m", "host preparation")
    host_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    host_payload = (repo / launch_controller.HOST_REL).read_bytes()
    environment_commit = commit_json(
        launch_controller.ENV_REL,
        {
            "schema": launch_controller.ENV_SCHEMA,
            "verdict": launch_controller.ENV_VERDICT,
            "problem_count": 0,
            "problems": [],
        },
        "environment receipt",
    )
    environment_payload = (repo / launch_controller.ENV_REL).read_bytes()
    pre_smoke_commit = commit_json(
        launch_controller.MANIFEST_REL,
        {
            "schema": launch_controller.MANIFEST_SCHEMA,
            "verdict": launch_controller.PRE_SMOKE_VERDICT,
            "launch_authorized": False,
            "mission_phase": launch_controller.TOOLING_PHASE,
            "missing_artifacts": ["smoke-evidence/smoke_receipt.json"],
            "problem_count": 1,
            "problems": ["smoke:receipt-missing"],
        },
        "pre-smoke manifest",
    )
    pre_smoke_payload = (repo / launch_controller.MANIFEST_REL).read_bytes()
    for relative in launch_controller.SMOKE_EVIDENCE_PATHS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"evidence:{relative}\n")
    (repo / launch_controller.SMOKE_RECEIPT_REL).write_text(
        json.dumps(
            {
                "schema": launch_controller.SMOKE_SCHEMA,
                "verdict": launch_controller.SMOKE_VERDICT,
                "problem_count": 0,
                "problems": [],
                "nonanalytic": True,
                "analytic_episode_count": 0,
            },
            sort_keys=True,
        )
        + "\n"
    )
    (repo / launch_controller.RAW_PRE_MANIFEST_REL).write_bytes(pre_smoke_payload)
    (repo / launch_controller.RAW_ENV_REL).write_bytes(environment_payload)
    _git(repo, "add", *launch_controller.SMOKE_EVIDENCE_PATHS)
    _git(repo, "commit", "-m", "smoke evidence")
    smoke_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    smoke_payload = (repo / launch_controller.SMOKE_RECEIPT_REL).read_bytes()

    launch_state = copy.deepcopy(state)
    launch_state["next_program"]["phase"] = "LAUNCH_AUTHORIZED"
    launch_state["next_program"]["authorized_actions"] = list(LAUNCH_AUTHORIZED_ACTIONS)
    launch_state["next_program"]["forbidden_actions"] = list(LAUNCH_FORBIDDEN_ACTIONS)
    (repo / "MISSION_STATE.json").write_text(json.dumps(launch_state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "launch authorization state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    state_payload = (repo / "MISSION_STATE.json").read_bytes()

    def binding(source_path: str, payload: bytes) -> dict[str, object]:
        return {
            "source_path": source_path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }

    host_binding = binding("host_preparation_receipt.json", host_payload)
    host_packet_binding = binding("host_packet_manifest.json", host_packet_payload)
    final_manifest_commit = commit_json(
        launch_controller.MANIFEST_REL,
        {
            "schema": launch_controller.MANIFEST_SCHEMA,
            "verdict": launch_controller.FINAL_MANIFEST_VERDICT,
            "launch_authorized": True,
            "mission_phase": "LAUNCH_AUTHORIZED",
            "problem_count": 0,
            "problems": [],
            "gates": {"all": True},
            "host_preparation_receipt": host_binding,
            "host_packet_manifest": host_packet_binding,
            "mission_state": binding("MISSION_STATE.json", state_payload),
            "hash_bound_files": {
                "host_packet_manifest.json": host_packet_binding,
                "host_preparation_receipt.json": host_binding,
                "env_receipts.json": binding("env_receipts.json", environment_payload),
                "smoke-evidence/smoke_receipt.json": binding(
                    "smoke-evidence/smoke_receipt.json", smoke_payload
                ),
            },
        },
        "final launch manifest",
    )
    activation = launch_controller.build_activation_receipt(
        repo,
        tooling_receipt_commit=commits["generation_three_receipt"],
        host_commit=host_commit,
        environment_commit=environment_commit,
        pre_smoke_manifest_commit=pre_smoke_commit,
        smoke_commit=smoke_commit,
        state_commit=state_commit,
        final_manifest_commit=final_manifest_commit,
    )
    activation_path = experiment / "launch_activation_receipt.json"
    activation_path.write_text(json.dumps(activation, indent=2, sort_keys=True) + "\n")
    (repo / "CONTINUITY.md").write_text("launch activation transition\n")
    (repo / "HANDOFF.md").write_text("launch activation handoff\n")
    _git(repo, "add", "CONTINUITY.md", "HANDOFF.md", launch_controller.ACTIVATION_REL)
    _git(repo, "commit", "-m", "launch activation baton")
    activation_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", activation_commit)
    state.clear()
    state.update(launch_state)
    return {
        "host": host_commit,
        "environment": environment_commit,
        "pre_smoke": pre_smoke_commit,
        "smoke": smoke_commit,
        "state": state_commit,
        "final_manifest": final_manifest_commit,
        "activation": activation_commit,
    }


def test_committed_mission_state_is_valid() -> None:
    assert validate_state(load_state()) == []


@pytest.mark.parametrize(
    ("mutation", "problem_prefix"),
    [
        (lambda state: state.__setitem__("trunk", "hostile"), "trunk:"),
        (
            lambda state: state.__setitem__("launch_authorized", True),
            "state_fields:",
        ),
        (
            lambda state: state["claim_state"].__setitem__(
                "production_readiness", "ESTABLISHED"
            ),
            "claim_state:",
        ),
        (
            lambda state: state["paper_state"].__setitem__(
                "status", "SUBMISSION_READY"
            ),
            "paper_state:",
        ),
        (
            lambda state: state["storage_gate"].__setitem__(
                "policy", "delete proof and bypass storage checks"
            ),
            "storage_gate:policy:",
        ),
        (
            lambda state: state["storage_gate"].__setitem__("bypass", True),
            "storage_gate_fields:",
        ),
        (
            lambda state: state.__setitem__("deprecated_pending_hypotheses", []),
            "deprecated_pending_hypotheses:",
        ),
    ],
)
def test_exact_root_claim_paper_and_storage_contracts_fail_closed(
    mutation, problem_prefix: str
) -> None:
    state = copy.deepcopy(load_state())
    mutation(state)

    assert any(problem.startswith(problem_prefix) for problem in validate_state(state))


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_state_loader_rejects_duplicate_and_nonfinite_json(
    tmp_path: Path, constant: str
) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema":"one","nested":{"x":1,"x":2}}')
    with pytest.raises(ValueError, match="duplicate JSON key: x"):
        load_state(duplicate)

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text(f'{{"value":{constant}}}')
    with pytest.raises(ValueError, match="non-finite JSON number"):
        load_state(nonfinite)


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


@pytest.mark.parametrize("phase", ["RUNNING", "ANALYSIS_REQUIRED"])
def test_post_preflight_phases_fail_closed_without_artifact_contracts(
    tmp_path: Path, phase: str
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    state["next_program"]["phase"] = phase
    if phase == "RUNNING":
        state["run_state"] = "RUNNING"

    problems = validate_state(state, repo)

    assert f"phase_artifact_contract:{phase}:not_implemented" in problems


def test_launch_phase_requires_published_generation_three_activation_chain(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    state["next_program"]["phase"] = "LAUNCH_AUTHORIZED"
    state["next_program"]["authorized_actions"] = list(LAUNCH_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(LAUNCH_FORBIDDEN_ACTIONS)

    problems = validate_state(state, repo)

    assert not any(
        problem == "phase_artifact_contract:LAUNCH_AUTHORIZED:not_implemented"
        for problem in problems
    )
    assert any(problem.startswith("tooling_publication:receipt_missing:") for problem in problems)


def test_tooling_phase_accepts_exact_generation_two_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_recovery_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_tooling_phase_accepts_exact_generation_three_controller_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_three_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_four_source_ci_accepts_preregistered_rollback_before_new_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        include_receipt=False,
    )

    assert state["next_program"]["phase"] == "PREREGISTERED_TOOLING_REQUIRED"
    assert _git(repo, "rev-parse", "HEAD").decode().strip() == commits["generation_four_source"]
    assert validate_state(state, repo) == []


def test_tooling_phase_accepts_exact_generation_four_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("generation", 3),
        ("supersedes_receipt_commit", "0" * 40),
        ("recovery_parent", "1" * 40),
        ("reason_code", "UNREGISTERED_GENERATION_FOUR_REASON"),
    ],
)
def test_generation_four_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    bad_value: object,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        publication_overrides={field: bad_value},
    )

    assert any(
        problem.startswith(f"tooling_publication:receipt_publication_{field}:")
        for problem in validate_state(state, repo)
    )


def test_generation_four_source_scope_is_exactly_the_eleven_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    wrong_scope = (*GENERATION_FOUR_SOURCE_COMMIT_PATHS, "unexpected-generation-four.txt")
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        source_paths=wrong_scope,
    )

    assert len(GENERATION_FOUR_SOURCE_COMMIT_PATHS) == 11
    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_four_source_must_be_direct_child_of_frozen_generation_three_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        wrong_source_parent=True,
    )

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_four_rejects_hostile_generation_three_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        hostile_generation_three_baton=True,
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_three_baton_parent" in problems
    assert "tooling_publication:generation_three_baton_scope" in problems


def test_generation_ten_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_ten_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_ten_receipt_history_is_exactly_ten_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_ten_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_ten_receipt"],
        commits["generation_nine_receipt"],
        commits["generation_eight_receipt"],
        commits["generation_seven_receipt"],
        commits["generation_six_receipt"],
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 9}, "tooling_publication:receipt_publication_generation:9"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_ten_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_ten_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_ten_source_scope_is_exactly_the_fifteen_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_TEN_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/capture_environment135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_smoke135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_environment_capture.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_smoke_pipeline.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_ten_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_TEN_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_ten_source_must_be_direct_child_of_the_published_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_ten_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_ten_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_ten_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_ten_rejects_hostile_generation_nine_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_ten_publication(repo, state, monkeypatch)
    monkeypatch.setattr(
        mission_state, "GENERATION_NINE_BATON_COMMIT", commits["generation_nine_state"]
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_nine_baton_scope" in problems


def test_generation_nine_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_nine_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_nine_receipt_history_is_exactly_nine_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_nine_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_nine_receipt"],
        commits["generation_eight_receipt"],
        commits["generation_seven_receipt"],
        commits["generation_six_receipt"],
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 8}, "tooling_publication:receipt_publication_generation:8"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_nine_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_nine_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_nine_source_scope_is_exactly_the_fifteen_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_NINE_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/capture_environment135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_smoke135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_environment_capture.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_smoke_pipeline.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_nine_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_NINE_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_nine_source_must_be_direct_child_of_generation_eight_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_nine_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_nine_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_nine_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_nine_rejects_hostile_generation_eight_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_nine_publication(repo, state, monkeypatch)
    monkeypatch.setattr(
        mission_state, "GENERATION_EIGHT_BATON_COMMIT", commits["generation_eight_state"]
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_eight_baton_scope" in problems


def test_generation_eight_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eight_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_eight_receipt_history_is_exactly_eight_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_eight_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_eight_receipt"],
        commits["generation_seven_receipt"],
        commits["generation_six_receipt"],
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 7}, "tooling_publication:receipt_publication_generation:7"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_eight_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eight_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_eight_source_scope_is_exactly_the_eleven_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_EIGHT_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eight_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_EIGHT_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_eight_source_must_be_direct_child_of_generation_seven_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eight_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_eight_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eight_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_eight_rejects_hostile_generation_seven_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_eight_publication(repo, state, monkeypatch)
    monkeypatch.setattr(
        mission_state, "GENERATION_SEVEN_BATON_COMMIT", commits["generation_seven_state"]
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_seven_baton_scope" in problems


def test_generation_seven_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_seven_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_seven_receipt_history_is_exactly_seven_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_seven_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_seven_receipt"],
        commits["generation_six_receipt"],
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 6}, "tooling_publication:receipt_publication_generation:6"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_seven_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_seven_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_seven_source_scope_is_exactly_the_thirteen_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_SEVEN_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/prepare_host135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_host_preparation.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_seven_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_SEVEN_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_seven_source_must_be_direct_child_of_generation_six_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_seven_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_seven_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_seven_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_six_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_six_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_six_receipt_history_is_exactly_six_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_six_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_six_receipt"],
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 5}, "tooling_publication:receipt_publication_generation:5"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_six_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_six_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_six_source_scope_is_exactly_the_ten_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scope excludes MISSION_STATE.json: generation five already rolled it back, and an
    unchanged file can never appear in the source commit's path set."""

    assert mission_state.GENERATION_SIX_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_six_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_SIX_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_six_source_must_be_direct_child_of_generation_five_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_six_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_six_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_six_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_five_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_five_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_five_receipt_history_is_exactly_five_to_four_to_three_to_two_to_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_five_publication(repo, state, monkeypatch)

    history = _git(
        repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()
    ).decode().splitlines()

    assert history == [
        commits["generation_five_receipt"],
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 4}, "tooling_publication:receipt_publication_generation:4"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            "tooling_publication:receipt_publication_supersedes_receipt_commit:"
            f"{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_five_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_five_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_five_source_scope_is_exactly_the_thirteen_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scope is the generation-four bookkeeping set plus the two H-contract paths.

    A cross-layer replay proved the launch controller and the analytic launcher each bind the
    tooling generation exactly, so a scope that changed only the H contract would leave both
    consumers demanding a superseded generation-four receipt.
    """

    assert mission_state.GENERATION_FIVE_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/prepare_host135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_host_preparation.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_five_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_FIVE_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_five_source_must_be_direct_child_of_frozen_generation_four_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_five_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_five_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_five_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_four_receipt_history_is_exactly_four_to_three_to_two_to_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_four_publication(repo, state, monkeypatch)

    history = _git(
        repo,
        "log",
        "--format=%H",
        "--",
        TOOLING_RECEIPT_REL.as_posix(),
    ).decode().splitlines()

    assert history == [
        commits["generation_four_receipt"],
        commits["generation_three_receipt"],
        commits["recovery_receipt"],
        commits["generation_one_receipt"],
    ]
    assert validate_state(state, repo) == []


def test_generation_four_rejects_nonexact_receipt_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        extra_receipt_history=True,
    )

    assert any(
        problem.startswith("tooling_publication:receipt_history:")
        for problem in validate_state(state, repo)
    )


def test_generation_four_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_four_publication(
        repo,
        state,
        monkeypatch,
        include_baton=False,
    )

    assert "tooling_publication:generation_four_commit_count:1" in validate_state(state, repo)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("generation", 2),
        ("supersedes_receipt_commit", "0" * 40),
        ("recovery_parent", "1" * 40),
        ("reason_code", "UNREGISTERED_REASON"),
    ],
)
def test_generation_three_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    bad_value: object,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_three_publication(
        repo,
        state,
        monkeypatch,
        publication_overrides={field: bad_value},
    )

    assert any(
        problem.startswith(f"tooling_publication:receipt_publication_{field}:")
        for problem in validate_state(state, repo)
    )


@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_tooling_transition_rejects_nonexact_receipt_root_before_controller(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_three_publication(
        repo,
        state,
        monkeypatch,
        receipt_root_mutation=mutation,
    )

    def controller_must_not_load(*_args, **_kwargs):
        pytest.fail("launch controller loaded after a nonexact tooling receipt root")

    monkeypatch.setattr(mission_state, "_load_launch_controller", controller_must_not_load)

    problems = validate_state(state, repo)

    assert any(
        problem.startswith("tooling_publication:structural_probe:ToolingPublicationError:")
        and "receipt root field set is not exact" in problem
        for problem in problems
    )


def test_tooling_transition_routes_nested_receipt_to_frozen_validator_before_controller(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_three_publication(
        repo,
        state,
        monkeypatch,
        receipt_nested_mutation=True,
    )

    def frozen_validator(_repo: Path, _source_commit: str):
        def validate(receipt: dict, **_kwargs):
            return ["executed command set incomplete"] if receipt.get("commands") else []

        return validate

    def controller_must_not_load(*_args, **_kwargs):
        pytest.fail("launch controller loaded after frozen receipt validation failed")

    monkeypatch.setattr(mission_state, "_load_tooling_receipt_validator", frozen_validator)
    monkeypatch.setattr(mission_state, "_load_launch_controller", controller_must_not_load)

    problems = validate_state(state, repo)

    assert any(
        "published tooling receipt failed frozen validation: "
        "executed command set incomplete" in problem
        for problem in problems
    )


def test_generation_three_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_three_publication(repo, state, monkeypatch, include_baton=False)

    assert "tooling_publication:generation_three_commit_count:1" in validate_state(state, repo)


def test_generation_three_source_scope_is_exactly_the_25_path_controller_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    wrong_scope = (*GENERATION_THREE_SOURCE_COMMIT_PATHS, "unexpected-generation-three.txt")
    _commit_generation_three_publication(
        repo,
        state,
        monkeypatch,
        source_paths=wrong_scope,
    )

    assert len(GENERATION_THREE_SOURCE_COMMIT_PATHS) == 25
    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_launch_phase_accepts_only_complete_origin_contained_h_e_p_s_a_f_b(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    _append_launch_authorization_chain(repo, state, generation)
    _use_structural_launch_controller(monkeypatch)

    assert validate_state(state, repo) == []


def test_launch_phase_rejects_activation_baton_not_on_origin_master(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    _git(repo, "update-ref", "refs/remotes/origin/master", launch["final_manifest"])
    _use_structural_launch_controller(monkeypatch)

    assert "authorization:head-not-on-origin-master" in validate_state(state, repo)


def test_launch_phase_rejects_origin_advanced_beyond_exact_activation_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    tree = _git(repo, "rev-parse", f"{launch['activation']}^{{tree}}").decode().strip()
    advanced = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        launch["activation"],
        "-m",
        "unreviewed origin advancement",
    ).decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", advanced)
    _use_structural_launch_controller(monkeypatch)

    assert "authorization:head-not-on-origin-master" in validate_state(state, repo)


def test_local_launch_candidate_is_validated_but_never_grants_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    _git(repo, "update-ref", "refs/remotes/origin/master", launch["smoke"])
    _use_structural_launch_controller(monkeypatch)

    result = validate_local_launch_candidate(repo)

    assert result["candidate_valid"] is True
    assert result["authoritative"] is False
    assert result["launch_authorized"] is False
    assert result["problems"] == ["authorization:candidate-non-authoritative"]


def test_local_launch_candidate_rejects_origin_advanced_beyond_exact_smoke_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    tree = _git(repo, "rev-parse", f"{launch['smoke']}^{{tree}}").decode().strip()
    advanced = _git(
        repo,
        "commit-tree",
        tree,
        "-p",
        launch["smoke"],
        "-m",
        "unreviewed preflight advancement",
    ).decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", advanced)
    _use_structural_launch_controller(monkeypatch)

    result = validate_local_launch_candidate(repo)

    assert result["candidate_valid"] is False
    assert result["authoritative"] is False
    assert result["launch_authorized"] is False
    assert result["problems"] == ["authorization:preflight-not-on-origin-master"]


@pytest.mark.parametrize(
    ("mutation", "expected_problem"),
    [
        (lambda state: state.__setitem__("launch_authorized", True), "candidate:state-field-set"),
        (
            lambda state: state.__setitem__("canonical_repository", "/tmp/hostile"),
            "candidate:state-canonical-repository",
        ),
        (lambda state: state.__setitem__("trunk", "dev"), "candidate:state-trunk"),
        (
            lambda state: state.__setitem__("current_completed_iteration", 133),
            "candidate:state-current-iteration",
        ),
        (
            lambda state: state.__setitem__("current_result", "experiments/iter133/RESULT.md"),
            "candidate:state-current-result",
        ),
        (
            lambda state: state.__setitem__("current_verdict", "UNREVIEWED"),
            "candidate:state-current-verdict",
        ),
        (
            lambda state: state["claim_state"].__setitem__("production_readiness", "READY"),
            "candidate:state-claim-state",
        ),
        (
            lambda state: state.__setitem__("deprecated_pending_hypotheses", []),
            "candidate:state-deprecated-hypotheses",
        ),
        (
            lambda state: state["paper_state"].__setitem__("status", "SUBMISSION_READY"),
            "candidate:state-paper-state",
        ),
        (
            lambda state: state["storage_gate"].__setitem__("policy", "delete proof"),
            "candidate:state-storage-gate",
        ),
        (
            lambda state: state["next_program"].__setitem__(
                "phase", "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
            ),
            "candidate:state-next-program",
        ),
        (
            lambda state: state["next_program"]["authorized_actions"].append(
                "unregistered launch"
            ),
            "candidate:state-next-program",
        ),
        (lambda state: state.__setitem__("run_state", "RUNNING"), "candidate:state-run-state"),
    ],
)
def test_local_launch_candidate_rejects_hostile_state_before_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    expected_problem: str,
) -> None:
    state = copy.deepcopy(load_state())
    state["next_program"]["phase"] = "LAUNCH_AUTHORIZED"
    state["next_program"]["authorized_actions"] = list(LAUNCH_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(LAUNCH_FORBIDDEN_ACTIONS)
    mutation(state)
    (tmp_path / "MISSION_STATE.json").write_text(json.dumps(state) + "\n")

    def topology_must_not_run(*_args, **_kwargs):
        pytest.fail("candidate topology ran before exact mission-state validation")

    monkeypatch.setattr(mission_state, "_validate_tooling_publication", topology_must_not_run)

    result = validate_local_launch_candidate(tmp_path)

    assert result["candidate_valid"] is False
    assert result["authoritative"] is False
    assert result["launch_authorized"] is False
    assert expected_problem in result["problems"]


@pytest.mark.parametrize(
    "payload",
    [
        '{"trunk":"master","trunk":"hostile"}',
        '{"value":NaN}',
        '{"value":Infinity}',
        "[]",
    ],
)
def test_local_launch_candidate_rejects_ambiguous_state_before_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: str,
) -> None:
    (tmp_path / "MISSION_STATE.json").write_text(payload)

    def topology_must_not_run(*_args, **_kwargs):
        pytest.fail("candidate topology ran after malformed mission state")

    monkeypatch.setattr(mission_state, "_validate_tooling_publication", topology_must_not_run)

    result = validate_local_launch_candidate(tmp_path)

    assert result["candidate_valid"] is False
    assert result["authoritative"] is False
    assert result["launch_authorized"] is False
    assert result["problems"] == ["candidate:mission-state:ValueError"]


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
