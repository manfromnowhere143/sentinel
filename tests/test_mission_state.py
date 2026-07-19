from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types

import pytest

import scripts.mission_state as mission_state
from scripts.mission_state import (
    CANONICAL_REPOSITORY,
    CONTROL_HARDENING_AUTHORIZED_ACTIONS,
    CONTROL_HARDENING_FORBIDDEN_ACTIONS,
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
    GENERATION_ELEVEN_REASON_CODE,
    GENERATION_ELEVEN_SOURCE_COMMIT_PATHS,
    GENERATION_TWELVE_REASON_CODE,
    GENERATION_TWELVE_SOURCE_COMMIT_PATHS,
    GENERATION_THIRTEEN_REASON_CODE,
    GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS,
    GENERATION_FOURTEEN_REASON_CODE,
    GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS,
    GENERATION_FIFTEEN_REASON_CODE,
    GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS,
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
    validate_local_launch_candidate as _validate_local_launch_candidate_without_fixture_integrity,
    validate_state as _validate_state_without_fixture_integrity,
)


AUTH_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py"
)
AUTH_SPEC = importlib.util.spec_from_file_location(
    "mission_state_launch_controller", AUTH_MODULE_PATH
)
assert AUTH_SPEC is not None and AUTH_SPEC.loader is not None
launch_controller = importlib.util.module_from_spec(AUTH_SPEC)
AUTH_SPEC.loader.exec_module(launch_controller)

SYNTHETIC_GIT_DURABILITY_CONFIG = (
    "-c",
    "commit.gpgSign=false",
    "-c",
    "core.createObject=rename",
    "-c",
    "core.fsync=committed,reference",
    "-c",
    "core.fsyncMethod=fsync",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "gc.auto=0",
    "-c",
    "maintenance.auto=false",
)
SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS = (
    "fsck",
    "--connectivity-only",
    "--strict",
    "--no-dangling",
)
SYNTHETIC_GIT_COMMAND_TIMEOUT_SECONDS = 120
SYNTHETIC_GIT_OUTPUT_BYTE_LIMIT = 8 * 1024 * 1024
SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT = 16 * 1024
SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER = b"...<diagnostic truncated>"
SYNTHETIC_GIT_ENVIRONMENT = {
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
    "GIT_AUTHOR_EMAIL": "sentinel-test@example.invalid",
    "GIT_AUTHOR_NAME": "Sentinel Test",
    "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
    "GIT_COMMITTER_EMAIL": "sentinel-test@example.invalid",
    "GIT_COMMITTER_NAME": "Sentinel Test",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_PAGER": "cat",
    "GIT_TERMINAL_PROMPT": "0",
    "HOME": "/nonexistent/sentinel-synthetic-git-home",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "PAGER": "cat",
    "TZ": "UTC",
    "XDG_CONFIG_HOME": "/nonexistent/sentinel-synthetic-git-xdg",
}
_SYNTHETIC_GIT_REPOSITORIES: dict[Path, tuple[int, int]] = {}
ACTIVE_BATON_SECTION_START = (
    "## The baton protocol (one operator at a time — hard rule; PERMANENT, BIDIRECTIONAL)"
)
ACTIVE_BATON_SECTION_END = "## Operating surfaces"


def _stale_generated_handoff_problems(document: str) -> list[str]:
    """Reject legacy generated HANDOFF bytes that can manufacture false-IDLE state."""

    lines = document.splitlines()
    problems: list[str] = []
    if any(
        line.startswith("Generated: ") and "scripts/make_handoff.py" in line
        for line in lines
    ):
        problems.append("active-handoff:legacy-generated-header")
    if "## GPU box quick-state (live probe)" in lines:
        problems.append("active-handoff:legacy-live-probe-section")
    if "GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS" in lines:
        problems.append("active-handoff:false-idle-container-absence")
    return problems


def test_active_handoff_is_not_a_legacy_generated_false_idle_snapshot() -> None:
    handoff = (Path(__file__).resolve().parents[1] / "HANDOFF.md").read_text()

    assert _stale_generated_handoff_problems(handoff) == []


@pytest.mark.parametrize(
    ("known_bad_line", "expected_problem"),
    [
        (
            "Generated: Sun Jul 19 12:00:00 UTC 2026 by scripts/make_handoff.py. "
            "Read CONTINUITY.md first.",
            "active-handoff:legacy-generated-header",
        ),
        (
            "## GPU box quick-state (live probe)",
            "active-handoff:legacy-live-probe-section",
        ),
        (
            "GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS",
            "active-handoff:false-idle-container-absence",
        ),
    ],
)
def test_active_handoff_gate_fires_on_known_bad_generated_bytes(
    known_bad_line: str,
    expected_problem: str,
) -> None:
    handoff = (Path(__file__).resolve().parents[1] / "HANDOFF.md").read_text()

    assert expected_problem in _stale_generated_handoff_problems(
        f"{handoff.rstrip()}\n{known_bad_line}\n"
    )


def _handoff_mission_contract_problems(
    document: str,
    *,
    canonical_state: dict | None = None,
) -> list[str]:
    """Bind the active HANDOFF action bullets to the canonical mission-state contract."""

    start_marker = "## Canonical mission state (`MISSION_STATE.json`)"
    end_marker = "## Publication sequence"
    if document.count(start_marker) != 1 or document.count(end_marker) != 1:
        return ["active-handoff:mission-contract-section"]
    start = document.index(start_marker)
    end = document.index(end_marker, start)
    section_lines = document[start:end].splitlines()
    authorized_marker = "- Authorized now:"
    forbidden_marker = "- Forbidden now:"
    if (
        section_lines.count(authorized_marker) != 1
        or section_lines.count(forbidden_marker) != 1
    ):
        return ["active-handoff:mission-contract-structure"]
    authorized_index = section_lines.index(authorized_marker)
    forbidden_index = section_lines.index(forbidden_marker)
    if authorized_index >= forbidden_index:
        return ["active-handoff:mission-contract-structure"]

    def parse_action_block(lines: list[str]) -> list[str] | None:
        actions: list[str] = []
        for line in lines:
            if line.startswith("  - "):
                actions.append(line[4:].strip())
            elif line.startswith("    ") and actions:
                actions[-1] = f"{actions[-1]} {line.strip()}"
            elif line.strip():
                return None
        return [
            " ".join(action.replace("`", "").rstrip(";.").split())
            for action in actions
        ]

    observed_authorized = parse_action_block(
        section_lines[authorized_index + 1 : forbidden_index]
    )
    observed_forbidden = parse_action_block(section_lines[forbidden_index + 1 :])
    if observed_authorized is None or observed_forbidden is None:
        return ["active-handoff:mission-contract-structure"]

    canonical_state = load_state() if canonical_state is None else canonical_state
    next_program = canonical_state.get("next_program")
    if type(next_program) is not dict:
        return ["active-handoff:mission-contract-state"]
    expected_authorized = next_program.get("authorized_actions")
    expected_forbidden = next_program.get("forbidden_actions")
    if (
        type(expected_authorized) is not list
        or any(type(action) is not str for action in expected_authorized)
        or type(expected_forbidden) is not list
        or any(type(action) is not str for action in expected_forbidden)
    ):
        return ["active-handoff:mission-contract-state"]

    problems: list[str] = []
    for index, action in enumerate(expected_authorized):
        if (
            index >= len(observed_authorized)
            or observed_authorized[index] != " ".join(action.split())
        ):
            problems.append(f"active-handoff:authorized-action:{index}")
    for index in range(
        len(expected_authorized),
        len(observed_authorized),
    ):
        problems.append(f"active-handoff:authorized-action:extra:{index}")
    for index, action in enumerate(expected_forbidden):
        if (
            index >= len(observed_forbidden)
            or observed_forbidden[index] != " ".join(action.split())
        ):
            problems.append(f"active-handoff:forbidden-action:{index}")
    for index in range(
        len(expected_forbidden),
        len(observed_forbidden),
    ):
        problems.append(f"active-handoff:forbidden-action:extra:{index}")
    return problems


def test_active_handoff_reproduces_exact_canonical_action_contract() -> None:
    handoff = (Path(__file__).resolve().parents[1] / "HANDOFF.md").read_text()

    assert _handoff_mission_contract_problems(handoff) == []


def test_handoff_contract_tracks_control_hardening_state_and_known_bad() -> None:
    state = copy.deepcopy(load_state())
    state["next_program"] = {
        "iteration": 135,
        "name": mission_state.EXPECTED_PROGRAM_NAME,
        "phase": "CONTROL_HARDENING_REQUIRED",
        "authorized_actions": list(CONTROL_HARDENING_AUTHORIZED_ACTIONS),
        "forbidden_actions": list(CONTROL_HARDENING_FORBIDDEN_ACTIONS),
    }
    document = "\n".join(
        [
            "## Canonical mission state (`MISSION_STATE.json`)",
            "",
            "- Authorized now:",
            *(
                f"  - {action}"
                for action in state["next_program"]["authorized_actions"]
            ),
            "- Forbidden now:",
            *(
                f"  - {action}"
                for action in state["next_program"]["forbidden_actions"]
            ),
            "",
            "## Publication sequence",
        ]
    )

    assert (
        _handoff_mission_contract_problems(document, canonical_state=state) == []
    )
    assert _handoff_mission_contract_problems(
        document.replace("hermetic CI", "CI"),
        canonical_state=state,
    ) == ["active-handoff:authorized-action:1"]


def test_active_handoff_contract_gate_fires_when_hermetic_boundary_is_removed() -> None:
    handoff = (Path(__file__).resolve().parents[1] / "HANDOFF.md").read_text()
    mutated = handoff.replace("hermetic CI", "CI")
    next_program = load_state()["next_program"]
    expected_problems = [
        f"active-handoff:{kind}-action:{index}"
        for kind, actions in (
            ("authorized", next_program["authorized_actions"]),
            ("forbidden", next_program["forbidden_actions"]),
        )
        for index, action in enumerate(actions)
        if "hermetic CI" in action
    ]

    assert expected_problems
    assert _handoff_mission_contract_problems(mutated) == expected_problems


def test_active_handoff_contract_gate_fires_on_extra_authorized_action() -> None:
    handoff = (Path(__file__).resolve().parents[1] / "HANDOFF.md").read_text()
    mutated = handoff.replace(
        "- Forbidden now:",
        "  - launch arbitrary remote workload now;\n- Forbidden now:",
        1,
    )
    expected_index = len(load_state()["next_program"]["authorized_actions"])

    assert _handoff_mission_contract_problems(mutated) == [
        f"active-handoff:authorized-action:extra:{expected_index}"
    ]


def _active_baton_instruction_problems(document: str) -> list[str]:
    """Reject active handoff instructions that can recreate a false-IDLE claim."""

    if (
        document.count(ACTIVE_BATON_SECTION_START) != 1
        or document.count(ACTIVE_BATON_SECTION_END) != 1
    ):
        return ["active-baton:section-structure"]
    start = document.index(ACTIVE_BATON_SECTION_START)
    end = document.index(ACTIVE_BATON_SECTION_END, start)
    section = document[start:end]
    problems: list[str] = []
    legacy_generator_commands = (
        "runs `python3 scripts/make_handoff.py`",
        "run `python3 scripts/make_handoff.py > HANDOFF.md`",
    )
    if any(command in section for command in legacy_generator_commands):
        problems.append("active-baton:legacy-generator-command")
    if "whether the GPU box is IDLE or a run is IN FLIGHT" in section:
        problems.append("active-baton:binary-idle-in-flight-rule")
    return problems


def test_active_baton_instructions_do_not_infer_a_binary_runtime_state() -> None:
    continuity = (Path(__file__).resolve().parents[1] / "CONTINUITY.md").read_text()

    assert _active_baton_instruction_problems(continuity) == []


@pytest.mark.parametrize(
    ("known_bad_instruction", "expected_problem"),
    [
        (
            "The incoming operator runs `python3 scripts/make_handoff.py`.\n",
            "active-baton:legacy-generator-command",
        ),
        (
            "State whether the GPU box is IDLE or a run is IN FLIGHT.\n",
            "active-baton:binary-idle-in-flight-rule",
        ),
    ],
)
def test_active_baton_instruction_gate_fires_on_known_bad_rules(
    known_bad_instruction: str,
    expected_problem: str,
) -> None:
    continuity = (Path(__file__).resolve().parents[1] / "CONTINUITY.md").read_text()
    mutated = continuity.replace(
        ACTIVE_BATON_SECTION_END,
        known_bad_instruction + ACTIVE_BATON_SECTION_END,
        1,
    )

    assert expected_problem in _active_baton_instruction_problems(mutated)


def _controller_source_for_publication(
    *,
    generation: int,
    supersedes_receipt_commit: str,
    recovery_parent: str,
    reason_code: str,
) -> str:
    """Rebind the live controller's one active publication block for a historical fixture."""

    source = AUTH_MODULE_PATH.read_text()
    active_block = (
        '    "generation": 15,\n'
        '    "supersedes_receipt_commit": GENERATION_FOURTEEN_RECEIPT_COMMIT,\n'
        '    "recovery_parent": GENERATION_FOURTEEN_BATON_COMMIT,\n'
        '    "reason_code": GENERATION_FIFTEEN_REASON,\n'
    )
    if source.count(active_block) != 1:
        raise AssertionError("live controller active publication block is not exact")
    fixture_block = (
        f'    "generation": {generation},\n'
        f'    "supersedes_receipt_commit": "{supersedes_receipt_commit}",\n'
        f'    "recovery_parent": "{recovery_parent}",\n'
        f'    "reason_code": "{reason_code}",\n'
    )
    return source.replace(active_block, fixture_block)


def _synthetic_git_environment() -> dict[str, str]:
    return dict(SYNTHETIC_GIT_ENVIRONMENT)


def _bounded_git_diagnostic(value: bytes | str | None) -> str:
    if value is None:
        return ""
    raw = value.encode("utf-8", errors="replace") if isinstance(value, str) else value
    encoded = raw.decode("utf-8", errors="replace").encode("utf-8")
    if len(encoded) > SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT:
        retained_byte_count = (
            SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
            - len(SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER)
        )
        retained_text = encoded[:retained_byte_count].decode(
            "utf-8",
            errors="ignore",
        )
        return (
            retained_text
            + SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER.decode("ascii")
        )
    return encoded.decode("utf-8")


def _synthetic_git_failure(
    repo: Path,
    command: tuple[str, ...],
    *,
    return_code: int | str,
    stdout: bytes | str | None,
    stderr: bytes | str | None,
) -> AssertionError:
    try:
        free_bytes: int | str = shutil.disk_usage(repo).free
    except OSError as diagnostic_error:
        free_bytes = f"unavailable:{type(diagnostic_error).__name__}"
    try:
        filesystem = os.statvfs(repo)
        free_inodes: int | str = filesystem.f_favail
    except OSError as diagnostic_error:
        free_inodes = f"unavailable:{type(diagnostic_error).__name__}"
    return AssertionError(
        f"synthetic Git command failed: cwd={str(repo)!r} argv={list(command)!r} "
        f"return_code={return_code!r} free_bytes={free_bytes!r} "
        f"free_inodes={free_inodes!r} stdout={_bounded_git_diagnostic(stdout)!r} "
        f"stderr={_bounded_git_diagnostic(stderr)!r}"
    )


def _run_synthetic_git(repo: Path, *arguments: str) -> bytes:
    effective_arguments = arguments
    if arguments and arguments[0] == "init":
        effective_arguments = (
            "init",
            "--object-format=sha1",
            "--template=",
            *arguments[1:],
        )
    command = (
        "/usr/bin/git",
        *SYNTHETIC_GIT_DURABILITY_CONFIG,
        *effective_arguments,
    )
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_synthetic_git_environment(),
            timeout=SYNTHETIC_GIT_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.CalledProcessError as error:
        raise _synthetic_git_failure(
            repo,
            command,
            return_code=error.returncode,
            stdout=error.stdout,
            stderr=error.stderr,
        ) from error
    except subprocess.TimeoutExpired as error:
        raise _synthetic_git_failure(
            repo,
            command,
            return_code=f"timeout_after_{SYNTHETIC_GIT_COMMAND_TIMEOUT_SECONDS}s",
            stdout=error.stdout,
            stderr=error.stderr,
        ) from error
    except OSError as error:
        raise _synthetic_git_failure(
            repo,
            command,
            return_code=f"os_error:{type(error).__name__}",
            stdout=None,
            stderr=str(error),
        ) from error
    stdout = completed.stdout or b""
    stderr = completed.stderr or b""
    if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        raise _synthetic_git_failure(
            repo,
            command,
            return_code="output_contract_violation",
            stdout=stdout,
            stderr=stderr,
        )
    if stderr:
        raise _synthetic_git_failure(
            repo,
            command,
            return_code="unexpected_success_stderr",
            stdout=stdout,
            stderr=stderr,
        )
    if len(stdout) > SYNTHETIC_GIT_OUTPUT_BYTE_LIMIT:
        raise _synthetic_git_failure(
            repo,
            command,
            return_code="output_contract_violation",
            stdout=stdout,
            stderr=stderr,
        )
    return stdout


def _register_synthetic_git_repository(repo: Path) -> None:
    """Capture the physical repository identity before Git can create metadata."""

    physical_repo = repo.resolve(strict=True)
    repository_stat = physical_repo.stat()
    if not physical_repo.is_dir():
        raise AssertionError(f"synthetic Git repository is not a directory: {repo}")
    identity = (repository_stat.st_dev, repository_stat.st_ino)
    previous_identity = _SYNTHETIC_GIT_REPOSITORIES.get(physical_repo)
    if previous_identity is not None and previous_identity != identity:
        raise AssertionError(
            f"synthetic Git repository identity changed before registration: {physical_repo}"
        )
    _SYNTHETIC_GIT_REPOSITORIES[physical_repo] = identity


def _git(repo: Path, *arguments: str) -> bytes:
    if arguments and arguments[0] == "init":
        _register_synthetic_git_repository(repo)
    output = _run_synthetic_git(repo, *arguments)
    if arguments and arguments[0] == "commit":
        _run_synthetic_git(repo, *SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS)
    return output


def _assert_synthetic_git_connectivity(repo: Path) -> None:
    """Reject an incomplete fixture graph before the policy validator can inspect it."""

    _run_synthetic_git(repo, *SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS)


def validate_state(
    state: dict,
    repo: Path = mission_state.REPO_ROOT,
) -> list[str]:
    """Gate synthetic Git connectivity separately from mission-policy validation."""

    if repo.resolve() != mission_state.REPO_ROOT.resolve() and (repo / ".git").is_dir():
        _assert_synthetic_git_connectivity(repo)
    return _validate_state_without_fixture_integrity(state, repo)


def validate_local_launch_candidate(
    repo: Path = mission_state.REPO_ROOT,
) -> dict:
    """Gate synthetic Git connectivity before local candidate-policy validation."""

    if repo.resolve() != mission_state.REPO_ROOT.resolve() and (repo / ".git").is_dir():
        _assert_synthetic_git_connectivity(repo)
    return _validate_local_launch_candidate_without_fixture_integrity(repo)


def _remove_synthetic_git_metadata(root: Path) -> None:
    """Bound per-test Git-object retention without deleting fixture worktree evidence."""

    for current_root, directories, files in os.walk(root, topdown=True):
        if ".git" in directories:
            git_directory = Path(current_root) / ".git"
            if git_directory.is_symlink():
                git_directory.unlink()
            else:
                shutil.rmtree(git_directory)
            directories.remove(".git")
        if ".git" in files:
            (Path(current_root) / ".git").unlink()


def _emit_synthetic_git_failure_forensics(repo: Path) -> None:
    print(f"failed synthetic Git repository diagnostics: {repo}", file=sys.stderr)
    try:
        _assert_synthetic_git_connectivity(repo)
    except AssertionError as error:
        print(_bounded_git_diagnostic(str(error)), file=sys.stderr)


def _finalize_synthetic_git_repositories(
    tmp_root: Path,
    repositories: dict[Path, tuple[int, int]],
    *,
    failed: bool,
) -> None:
    root = tmp_root.resolve(strict=True)
    errors: list[str] = []
    for repo, expected_identity in sorted(repositories.items()):
        try:
            physical_repo = repo.resolve(strict=True)
            if physical_repo != root and not physical_repo.is_relative_to(root):
                raise AssertionError(
                    f"synthetic Git repository escaped tmp_path: {repo}"
                )
            if physical_repo != repo:
                raise AssertionError(
                    f"synthetic Git repository path was replaced: {repo}"
                )
            repository_stat = physical_repo.stat()
            observed_identity = (repository_stat.st_dev, repository_stat.st_ino)
            if observed_identity != expected_identity:
                raise AssertionError(
                    "synthetic Git repository identity was replaced: "
                    f"{repo} expected={expected_identity!r} "
                    f"observed={observed_identity!r}"
                )
        except Exception as error:
            errors.append(f"{repo}: validation: {type(error).__name__}: {error}")
            continue
        if failed:
            try:
                _emit_synthetic_git_failure_forensics(physical_repo)
            except Exception as error:
                errors.append(
                    f"{repo}: forensics: {type(error).__name__}: {error}"
                )
        try:
            metadata = physical_repo / ".git"
            if metadata.is_symlink():
                metadata.unlink()
            elif metadata.is_dir():
                physical_metadata = metadata.resolve(strict=True)
                if not physical_metadata.is_relative_to(physical_repo):
                    raise AssertionError(
                        f"synthetic Git metadata escaped repository: {metadata}"
                    )
                shutil.rmtree(metadata)
            elif metadata.is_file():
                metadata.unlink()
        except Exception as error:
            errors.append(f"{repo}: cleanup: {type(error).__name__}: {error}")
    if errors:
        raise AssertionError(
            "synthetic Git repository finalization failed after processing all "
            "registrations:\n- "
            + "\n- ".join(errors)
        )


@pytest.fixture(autouse=True)
def _bound_synthetic_git_storage(
    tmp_path: Path,
    request: pytest.FixtureRequest,
):
    """Emit bounded failure diagnostics, then discard every isolated object database."""

    failures_before = request.session.testsfailed
    _SYNTHETIC_GIT_REPOSITORIES.clear()
    yield
    try:
        _finalize_synthetic_git_repositories(
            tmp_path,
            dict(_SYNTHETIC_GIT_REPOSITORIES),
            failed=request.session.testsfailed > failures_before,
        )
    finally:
        _SYNTHETIC_GIT_REPOSITORIES.clear()


def test_synthetic_git_cleanup_bounds_metadata_and_preserves_worktree(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "nested"
    metadata = nested / ".git" / "objects"
    metadata.mkdir(parents=True)
    (metadata / "retained-until-teardown").write_bytes(b"synthetic object\n")
    worktree = nested / "MISSION_STATE.json"
    worktree.write_text("{}\n")
    linked = tmp_path / "linked-worktree"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: /nonexistent/synthetic.git\n")
    linked_marker = linked / "HANDOFF.md"
    linked_marker.write_text("preserve\n")

    _remove_synthetic_git_metadata(tmp_path)

    assert not (nested / ".git").exists()
    assert worktree.read_text() == "{}\n"
    assert not (linked / ".git").exists()
    assert linked_marker.read_text() == "preserve\n"


def test_failed_synthetic_git_repository_emits_forensics_before_cleanup(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _git(tmp_path, "init", "-b", "master")
    _git(tmp_path, "config", "user.name", "Sentinel Test")
    _git(tmp_path, "config", "user.email", "sentinel-test@example.invalid")
    marker = tmp_path / "reachable.txt"
    marker.write_text("reachable object\n")
    _git(tmp_path, "add", marker.name)
    _git(tmp_path, "commit", "-m", "reachable object for failed-test forensics")
    blob = _git(tmp_path, "rev-parse", f"HEAD:{marker.name}").decode().strip()
    blob_object = tmp_path / ".git" / "objects" / blob[:2] / blob[2:]
    assert blob_object.is_file()
    blob_object.unlink()

    _finalize_synthetic_git_repositories(
        tmp_path,
        dict(_SYNTHETIC_GIT_REPOSITORIES),
        failed=True,
    )

    assert not (tmp_path / ".git").exists()
    diagnostics = capsys.readouterr().err
    assert "failed synthetic Git repository diagnostics" in diagnostics
    assert "fsck" in diagnostics
    assert "missing" in diagnostics
    assert blob in diagnostics


def test_partial_synthetic_git_initialization_is_registered_before_execution_and_cleaned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    physical_repo = tmp_path.resolve(strict=True)

    def fail_after_creating_metadata(command, **_kwargs):
        assert physical_repo in _SYNTHETIC_GIT_REPOSITORIES
        (tmp_path / ".git").mkdir()
        raise subprocess.CalledProcessError(
            128,
            command,
            output=b"",
            stderr=b"fatal: injected partial initialization\n",
        )

    monkeypatch.setattr(subprocess, "run", fail_after_creating_metadata)

    with pytest.raises(AssertionError, match="partial initialization"):
        _git(tmp_path, "init", "-b", "master")

    assert (tmp_path / ".git").is_dir()
    _finalize_synthetic_git_repositories(
        tmp_path,
        dict(_SYNTHETIC_GIT_REPOSITORIES),
        failed=False,
    )
    assert not (tmp_path / ".git").exists()


def test_synthetic_git_finalizer_attempts_all_safe_cleanup_before_raising(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "a-missing"
    missing.mkdir()
    missing_stat = missing.stat()
    missing_identity = (missing_stat.st_dev, missing_stat.st_ino)
    replaced = tmp_path / "b-replaced"
    (replaced / ".git").mkdir(parents=True)
    replaced_stat = replaced.stat()
    replaced_identity = (replaced_stat.st_dev, replaced_stat.st_ino)
    parked_replaced = tmp_path / "parked-replaced"
    replaced.rename(parked_replaced)
    (replaced / ".git").mkdir(parents=True)
    valid = tmp_path / "z-valid"
    (valid / ".git").mkdir(parents=True)
    valid_stat = valid.stat()
    valid_identity = (valid_stat.st_dev, valid_stat.st_ino)
    shutil.rmtree(missing)

    with pytest.raises(AssertionError, match="processing all registrations") as raised:
        _finalize_synthetic_git_repositories(
            tmp_path,
            {
                missing: missing_identity,
                replaced: replaced_identity,
                valid: valid_identity,
            },
            failed=False,
        )

    assert "a-missing" in str(raised.value)
    assert "b-replaced" in str(raised.value)
    assert (replaced / ".git").is_dir()
    assert not (valid / ".git").exists()
    shutil.rmtree(replaced)
    shutil.rmtree(parked_replaced)


def test_synthetic_git_finalizer_cleans_metadata_when_forensics_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(tmp_path, "init", "-b", "master")

    def fail_forensics(_repo: Path) -> None:
        raise RuntimeError("injected forensic failure")

    monkeypatch.setattr(
        sys.modules[__name__],
        "_emit_synthetic_git_failure_forensics",
        fail_forensics,
    )

    with pytest.raises(AssertionError, match="injected forensic failure") as raised:
        _finalize_synthetic_git_repositories(
            tmp_path,
            dict(_SYNTHETIC_GIT_REPOSITORIES),
            failed=True,
        )

    assert "forensics: RuntimeError" in str(raised.value)
    assert not (tmp_path / ".git").exists()


def test_synthetic_git_finalizer_does_not_follow_a_replaced_repository_symlink(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    repo_stat = repo.stat()
    expected_identity = (repo_stat.st_dev, repo_stat.st_ino)
    parked_repo = tmp_path / "parked-repo"
    repo.rename(parked_repo)
    external = tmp_path.parent / f"{tmp_path.name}-external-replacement"
    external.mkdir()
    marker = external / "must-survive"
    marker.write_text("external replacement\n")
    repo.symlink_to(external, target_is_directory=True)

    with pytest.raises(AssertionError, match="escaped tmp_path|path was replaced"):
        _finalize_synthetic_git_repositories(
            tmp_path,
            {repo: expected_identity},
            failed=False,
        )

    assert marker.read_text() == "external replacement\n"
    assert (parked_repo / ".git").is_dir()
    repo.unlink()
    shutil.rmtree(parked_repo)
    shutil.rmtree(external)


def test_synthetic_git_finalizer_does_not_clean_a_replaced_directory_identity(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    repo_stat = repo.stat()
    expected_identity = (repo_stat.st_dev, repo_stat.st_ino)
    parked_repo = tmp_path / "parked-repo"
    repo.rename(parked_repo)
    replacement_metadata = repo / ".git"
    replacement_metadata.mkdir(parents=True)
    replacement_marker = replacement_metadata / "must-survive"
    replacement_marker.write_text("replacement metadata\n")

    with pytest.raises(AssertionError, match="identity was replaced"):
        _finalize_synthetic_git_repositories(
            tmp_path,
            {repo: expected_identity},
            failed=False,
        )

    assert replacement_marker.read_text() == "replacement metadata\n"
    assert (parked_repo / ".git").is_dir()
    shutil.rmtree(repo)
    shutil.rmtree(parked_repo)


def test_synthetic_git_finalizer_unlinks_metadata_symlink_without_following_it(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    repo_stat = repo.stat()
    expected_identity = (repo_stat.st_dev, repo_stat.st_ino)
    external = tmp_path.parent / f"{tmp_path.name}-external-metadata"
    external.mkdir()
    marker = external / "must-survive"
    marker.write_text("external metadata\n")
    (repo / ".git").symlink_to(external, target_is_directory=True)

    _finalize_synthetic_git_repositories(
        tmp_path,
        {repo: expected_identity},
        failed=False,
    )

    assert not (repo / ".git").exists()
    assert marker.read_text() == "external metadata\n"
    shutil.rmtree(external)


def test_synthetic_git_cleanup_unlinks_metadata_symlink_without_following_it(
    tmp_path: Path,
) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external-git"
    external.mkdir()
    marker = external / "must-survive"
    marker.write_text("external metadata\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").symlink_to(external, target_is_directory=True)

    _remove_synthetic_git_metadata(tmp_path)

    assert not (repo / ".git").exists()
    assert marker.read_text() == "external metadata\n"
    shutil.rmtree(external)


def test_synthetic_git_failure_surfaces_retained_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args, **_kwargs):
        raise subprocess.CalledProcessError(
            128,
            ("/usr/bin/git", "commit"),
            output=b"partial stdout\n",
            stderr=b"fatal: injected resource failure\n",
        )

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(AssertionError) as raised:
        _git(tmp_path, "commit")

    message = str(raised.value)
    assert f"cwd={str(tmp_path)!r}" in message
    assert "return_code=128" in message
    assert "free_bytes=" in message
    assert "free_inodes=" in message
    assert "partial stdout" in message
    assert "fatal: injected resource failure" in message


def test_synthetic_git_success_output_limit_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact_output = b"x" * SYNTHETIC_GIT_OUTPUT_BYTE_LIMIT
    responses = iter((exact_output, exact_output + b"x"))

    def succeed(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=next(responses),
            stderr=b"",
        )

    monkeypatch.setattr(subprocess, "run", succeed)

    assert _run_synthetic_git(tmp_path, "status") == exact_output
    with pytest.raises(AssertionError, match="output_contract_violation"):
        _run_synthetic_git(tmp_path, "status")


def test_synthetic_git_rejects_stderr_from_a_successful_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def succeed_with_warning(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=b"",
            stderr=b"warning: core.fsync setting was ignored\n",
        )

    monkeypatch.setattr(subprocess, "run", succeed_with_warning)

    with pytest.raises(AssertionError, match="unexpected_success_stderr") as raised:
        _run_synthetic_git(tmp_path, "status")

    assert "core.fsync setting was ignored" in str(raised.value)


def test_synthetic_git_diagnostic_limit_includes_the_truncation_marker() -> None:
    exact = b"x" * SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
    over = exact + b"x"

    assert _bounded_git_diagnostic(exact).encode() == exact
    bounded = _bounded_git_diagnostic(over).encode()
    assert len(bounded) == SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
    assert bounded.endswith(SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER)
    assert bounded.startswith(
        b"x"
        * (
            SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
            - len(SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER)
        )
    )
    hostile_invalid = _bounded_git_diagnostic(
        b"\xff" * SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
    ).encode("utf-8")
    assert len(hostile_invalid) <= SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
    assert hostile_invalid.endswith(SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER)
    multibyte = _bounded_git_diagnostic("€".encode() * 6_000).encode("utf-8")
    assert len(multibyte) <= SYNTHETIC_GIT_DIAGNOSTIC_BYTE_LIMIT
    assert multibyte.endswith(SYNTHETIC_GIT_DIAGNOSTIC_TRUNCATION_MARKER)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            subprocess.TimeoutExpired(
                ("/usr/bin/git", "fsck"),
                SYNTHETIC_GIT_COMMAND_TIMEOUT_SECONDS,
                output=b"partial timeout output\n",
                stderr=b"timeout diagnostic\n",
            ),
            f"timeout_after_{SYNTHETIC_GIT_COMMAND_TIMEOUT_SECONDS}s",
        ),
        (OSError("injected exec failure"), "os_error:OSError"),
    ],
)
def test_synthetic_git_timeout_and_os_errors_are_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: BaseException,
    expected: str,
) -> None:
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(AssertionError) as raised:
        _git(tmp_path, "status")

    message = str(raised.value)
    assert expected in message
    assert f"cwd={str(tmp_path)!r}" in message
    if isinstance(error, subprocess.TimeoutExpired):
        assert "partial timeout output" in message
        assert "timeout diagnostic" in message


def test_synthetic_git_commands_force_object_and_reference_durability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, ...]] = []
    observed_environments: list[dict[str, str]] = []

    def succeed(command, **kwargs):
        observed.append(tuple(command))
        observed_environments.append(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setenv("GIT_DIR", "/hostile/inherited/git-dir")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "/hostile/hooks")
    monkeypatch.setenv("GIT_CONFIG_PARAMETERS", "'core.hooksPath'='/hostile/hooks'")
    monkeypatch.setenv("GIT_DEFAULT_HASH", "sha256")
    monkeypatch.setenv("GIT_EXEC_PATH", "/hostile/git-core")
    monkeypatch.setenv("GIT_TEMPLATE_DIR", "/hostile/templates")
    monkeypatch.setenv("LD_PRELOAD", "/hostile/library.so")
    monkeypatch.setattr(subprocess, "run", succeed)

    assert _git(tmp_path, "status", "--porcelain=v1") == b""
    assert observed == [
        (
            "/usr/bin/git",
            *SYNTHETIC_GIT_DURABILITY_CONFIG,
            "status",
            "--porcelain=v1",
        )
    ]
    assert observed_environments == [SYNTHETIC_GIT_ENVIRONMENT]
    assert "GIT_DIR" not in observed_environments[0]
    assert "GIT_CONFIG_COUNT" not in observed_environments[0]
    assert "GIT_CONFIG_KEY_0" not in observed_environments[0]
    assert "GIT_CONFIG_VALUE_0" not in observed_environments[0]
    assert "GIT_CONFIG_PARAMETERS" not in observed_environments[0]
    assert "GIT_DEFAULT_HASH" not in observed_environments[0]
    assert "GIT_EXEC_PATH" not in observed_environments[0]
    assert "GIT_TEMPLATE_DIR" not in observed_environments[0]
    assert "LD_PRELOAD" not in observed_environments[0]


def test_synthetic_git_initialization_forces_sha1_without_host_templates(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "-b", "master")

    assert _git(tmp_path, "rev-parse", "--show-object-format") == b"sha1\n"
    assert not (tmp_path / ".git" / "hooks").exists()


def test_synthetic_git_commit_checks_graph_connectivity_before_returning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, ...]] = []

    def corrupt_after_commit(command, **_kwargs):
        observed.append(tuple(command))
        if tuple(command[-len(SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS) :]) == (
            SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS
        ):
            raise subprocess.CalledProcessError(
                2,
                command,
                output=b"",
                stderr=b"missing commit object\n",
            )
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", corrupt_after_commit)

    with pytest.raises(AssertionError, match="missing commit object"):
        _git(tmp_path, "commit", "-m", "synthetic commit")

    assert observed == [
        (
            "/usr/bin/git",
            *SYNTHETIC_GIT_DURABILITY_CONFIG,
            "commit",
            "-m",
            "synthetic commit",
        ),
        (
            "/usr/bin/git",
            *SYNTHETIC_GIT_DURABILITY_CONFIG,
            *SYNTHETIC_GIT_CONNECTIVITY_ARGUMENTS,
        ),
    ]


def test_synthetic_git_connectivity_gate_rejects_a_missing_reachable_parent(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "-b", "master")
    _git(tmp_path, "config", "user.name", "Sentinel Test")
    _git(tmp_path, "config", "user.email", "sentinel-test@example.invalid")
    marker = tmp_path / "marker.txt"
    marker.write_text("parent\n")
    _git(tmp_path, "add", marker.name)
    _git(tmp_path, "commit", "-m", "reachable parent")
    marker.write_text("child\n")
    _git(tmp_path, "add", marker.name)
    _git(tmp_path, "commit", "-m", "reachable child")
    parent = _git(tmp_path, "rev-parse", "HEAD^").decode().strip()
    parent_object = tmp_path / ".git" / "objects" / parent[:2] / parent[2:]
    assert parent_object.is_file()
    parent_object.unlink()

    with pytest.raises(AssertionError) as raised:
        validate_state({}, tmp_path)

    message = str(raised.value)
    assert "fsck" in message
    assert parent in message


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
    problems: list[str] = []
    if phase == "CONTROL_HARDENING_REQUIRED":
        if upstream_commit == tooling_receipt_commit:
            control_publication_status = (
                mission_state.CONTROL_PUBLICATION_CANDIDATE_STATUS
            )
        elif upstream_commit == tooling_baton_commit:
            control_publication_status = (
                mission_state.CONTROL_PUBLICATION_PUBLISHED_STATUS
            )
        else:
            control_publication_status = (
                mission_state.CONTROL_PUBLICATION_INVALID_UPSTREAM_STATUS
            )
            problems.append(
                "authorization:control-hardening-origin-master-not-r15-or-b15"
            )
        if candidate:
            problems.append("authorization:control-hardening-candidate")
        if descendants:
            problems.append(
                f"authorization:control-hardening-descendant-count:{len(descendants)}"
            )
        return {
            "problems": sorted(set(problems)),
            "references": {},
            "authority": "none",
            "launch_authorized": False,
            "control_publication_status": control_publication_status,
        }
    expected_count = 7 if phase == "LAUNCH_AUTHORIZED" else 4
    if phase == "LAUNCH_AUTHORIZED" and len(descendants) != expected_count:
        problems.append(f"authorization:launch-descendant-count:{len(descendants)}")
    expected_upstream = (
        descendants[3]
        if candidate and len(descendants) >= 4
        else descendants[-1]
        if descendants
        else None
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
            "authority": "non-authoritative-local-candidate",
            "launch_authorized": False,
            "candidate_valid": problems == ["authorization:candidate-non-authoritative"],
        }
    return {
        "problems": problems,
        "references": references,
        "authority": "origin-published" if not problems else "none",
        "launch_authorized": not problems,
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
    state["run_state"] = "IDLE"
    state["next_program"]["phase"] = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
    state["next_program"]["authorized_actions"] = list(TOOLING_FROZEN_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(TOOLING_FROZEN_FORBIDDEN_ACTIONS)


def _set_preregistered_phase(state: dict) -> None:
    state["run_state"] = "UNKNOWN"
    state["next_program"]["phase"] = "PREREGISTERED_TOOLING_REQUIRED"
    state["next_program"]["authorized_actions"] = list(PREREGISTERED_AUTHORIZED_ACTIONS)
    state["next_program"]["forbidden_actions"] = list(PREREGISTERED_FORBIDDEN_ACTIONS)


def _set_control_hardening_phase(state: dict) -> None:
    state["run_state"] = "UNKNOWN"
    state["next_program"]["phase"] = "CONTROL_HARDENING_REQUIRED"
    state["next_program"]["authorized_actions"] = list(
        CONTROL_HARDENING_AUTHORIZED_ACTIONS
    )
    state["next_program"]["forbidden_actions"] = list(
        CONTROL_HARDENING_FORBIDDEN_ACTIONS
    )


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

    monkeypatch.setattr(mission_state, "GENERATION_ONE_SOURCE_PARENT", generation_one_source_parent)
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
            controller_source = _controller_source_for_publication(
                generation=4,
                supersedes_receipt_commit=generation_three["generation_three_receipt"],
                recovery_parent=generation_three_baton,
                reason_code=GENERATION_FOUR_REASON_CODE,
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
            controller_source = _controller_source_for_publication(
                generation=5,
                supersedes_receipt_commit=generation_four["generation_four_receipt"],
                recovery_parent=generation_four_baton,
                reason_code=GENERATION_FIVE_REASON_CODE,
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
    monkeypatch.setattr(mission_state, "GENERATION_FIVE_RECEIPT_COMMIT", generation_five_receipt)
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-five-topology.txt"
        unexpected.write_text("not the frozen generation-five receipt\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-five topology edge")
    monkeypatch.setattr(mission_state, "GENERATION_SIX_SOURCE_PARENT", generation_five_receipt)
    expected_publication = {
        "generation": 6,
        "supersedes_receipt_commit": generation_five_receipt,
        "recovery_parent": generation_five_receipt,
        "reason_code": GENERATION_SIX_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
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
            controller_source = _controller_source_for_publication(
                generation=6,
                supersedes_receipt_commit=generation_five_receipt,
                recovery_parent=generation_five_receipt,
                reason_code=GENERATION_SIX_REASON_CODE,
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
    monkeypatch.setattr(mission_state, "GENERATION_SEVEN_SOURCE_PARENT", generation_six_baton)
    expected_publication = {
        "generation": 7,
        "supersedes_receipt_commit": generation_six["generation_six_receipt"],
        "recovery_parent": generation_six_baton,
        "reason_code": GENERATION_SEVEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
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
            controller_source = _controller_source_for_publication(
                generation=7,
                supersedes_receipt_commit=generation_six["generation_six_receipt"],
                recovery_parent=generation_six_baton,
                reason_code=GENERATION_SEVEN_REASON_CODE,
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
    monkeypatch.setattr(mission_state, "GENERATION_EIGHT_SOURCE_PARENT", generation_seven_baton)
    expected_publication = {
        "generation": 8,
        "supersedes_receipt_commit": generation_seven["generation_seven_receipt"],
        "recovery_parent": generation_seven_baton,
        "reason_code": GENERATION_EIGHT_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
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
            controller_source = _controller_source_for_publication(
                generation=8,
                supersedes_receipt_commit=generation_seven["generation_seven_receipt"],
                recovery_parent=generation_seven_baton,
                reason_code=GENERATION_EIGHT_REASON_CODE,
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
    monkeypatch.setattr(mission_state, "GENERATION_NINE_SOURCE_PARENT", generation_eight_baton)
    expected_publication = {
        "generation": 9,
        "supersedes_receipt_commit": generation_eight["generation_eight_receipt"],
        "recovery_parent": generation_eight_baton,
        "reason_code": GENERATION_NINE_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
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
            controller_source = _controller_source_for_publication(
                generation=9,
                supersedes_receipt_commit=generation_eight["generation_eight_receipt"],
                recovery_parent=generation_eight_baton,
                reason_code=GENERATION_NINE_REASON_CODE,
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
    monkeypatch.setattr(mission_state, "GENERATION_TEN_SOURCE_PARENT", generation_nine_baton)
    expected_publication = {
        "generation": 10,
        "supersedes_receipt_commit": generation_nine["generation_nine_receipt"],
        "recovery_parent": generation_nine_baton,
        "reason_code": GENERATION_TEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
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
            controller_source = _controller_source_for_publication(
                generation=10,
                supersedes_receipt_commit=generation_nine["generation_nine_receipt"],
                recovery_parent=generation_nine_baton,
                reason_code=GENERATION_TEN_REASON_CODE,
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


def _commit_generation_eleven_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_ELEVEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-eleven topology on top of a complete generation-ten chain."""

    generation_ten = _commit_generation_ten_publication(repo, state, monkeypatch)
    generation_ten_baton = generation_ten["generation_ten_baton"]
    for name, key in (
        ("GENERATION_TEN_SOURCE_COMMIT", "generation_ten_source"),
        ("GENERATION_TEN_RECEIPT_COMMIT", "generation_ten_receipt"),
        ("GENERATION_TEN_STATE_COMMIT", "generation_ten_state"),
        ("GENERATION_TEN_BATON_COMMIT", "generation_ten_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_ten[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-ten-topology.txt"
        unexpected.write_text("not the frozen generation-ten tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-ten topology edge")
    monkeypatch.setattr(mission_state, "GENERATION_ELEVEN_SOURCE_PARENT", generation_ten_baton)
    expected_publication = {
        "generation": 11,
        "supersedes_receipt_commit": generation_ten["generation_ten_receipt"],
        "recovery_parent": generation_ten_baton,
        "reason_code": GENERATION_ELEVEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation eleven source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation eleven source handoff\n")
        elif relative == "LICENSE":
            path.write_text("Apache License fixture\n")
        elif relative.endswith("/authorize_launch135.py"):
            controller_source = _controller_source_for_publication(
                generation=11,
                supersedes_receipt_commit=generation_ten["generation_ten_receipt"],
                recovery_parent=generation_ten_baton,
                reason_code=GENERATION_ELEVEN_REASON_CODE,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation eleven\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation eleven source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation eleven source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_ten, "generation_eleven_source": source_commit}

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
    _git(repo, "commit", "-m", "generation eleven receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation eleven state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation eleven tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation eleven tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation eleven tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_ten,
        "generation_eleven_source": source_commit,
        "generation_eleven_receipt": receipt_commit,
        "generation_eleven_state": state_commit,
        "generation_eleven_baton": baton_commit,
    }


def _commit_generation_twelve_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_TWELVE_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-twelve topology on top of a complete generation-eleven chain."""

    generation_eleven = _commit_generation_eleven_publication(repo, state, monkeypatch)
    generation_eleven_baton = generation_eleven["generation_eleven_baton"]
    for name, key in (
        ("GENERATION_ELEVEN_SOURCE_COMMIT", "generation_eleven_source"),
        ("GENERATION_ELEVEN_RECEIPT_COMMIT", "generation_eleven_receipt"),
        ("GENERATION_ELEVEN_STATE_COMMIT", "generation_eleven_state"),
        ("GENERATION_ELEVEN_BATON_COMMIT", "generation_eleven_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_eleven[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-eleven-topology.txt"
        unexpected.write_text("not the frozen generation-eleven tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-eleven topology edge")
    monkeypatch.setattr(mission_state, "GENERATION_TWELVE_SOURCE_PARENT", generation_eleven_baton)
    expected_publication = {
        "generation": 12,
        "supersedes_receipt_commit": generation_eleven["generation_eleven_receipt"],
        "recovery_parent": generation_eleven_baton,
        "reason_code": GENERATION_TWELVE_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation twelve source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation twelve source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            controller_source = _controller_source_for_publication(
                generation=12,
                supersedes_receipt_commit=generation_eleven["generation_eleven_receipt"],
                recovery_parent=generation_eleven_baton,
                reason_code=GENERATION_TWELVE_REASON_CODE,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation twelve\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation twelve source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation twelve source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_eleven, "generation_twelve_source": source_commit}

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
    _git(repo, "commit", "-m", "generation twelve receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation twelve state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation twelve tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation twelve tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation twelve tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_eleven,
        "generation_twelve_source": source_commit,
        "generation_twelve_receipt": receipt_commit,
        "generation_twelve_state": state_commit,
        "generation_twelve_baton": baton_commit,
    }


def _commit_generation_thirteen_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-thirteen topology on top of a complete generation-twelve chain."""

    generation_twelve = _commit_generation_twelve_publication(repo, state, monkeypatch)
    generation_twelve_baton = generation_twelve["generation_twelve_baton"]
    for name, key in (
        ("GENERATION_TWELVE_SOURCE_COMMIT", "generation_twelve_source"),
        ("GENERATION_TWELVE_RECEIPT_COMMIT", "generation_twelve_receipt"),
        ("GENERATION_TWELVE_STATE_COMMIT", "generation_twelve_state"),
        ("GENERATION_TWELVE_BATON_COMMIT", "generation_twelve_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_twelve[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-twelve-topology.txt"
        unexpected.write_text("not the frozen generation-twelve tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-twelve topology edge")
    monkeypatch.setattr(mission_state, "GENERATION_THIRTEEN_SOURCE_PARENT", generation_twelve_baton)
    expected_publication = {
        "generation": 13,
        "supersedes_receipt_commit": generation_twelve["generation_twelve_receipt"],
        "recovery_parent": generation_twelve_baton,
        "reason_code": GENERATION_THIRTEEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation thirteen source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation thirteen source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            controller_source = _controller_source_for_publication(
                generation=13,
                supersedes_receipt_commit=generation_twelve["generation_twelve_receipt"],
                recovery_parent=generation_twelve_baton,
                reason_code=GENERATION_THIRTEEN_REASON_CODE,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation thirteen\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation thirteen source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation thirteen source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_twelve, "generation_thirteen_source": source_commit}

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
    _git(repo, "commit", "-m", "generation thirteen receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation thirteen state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation thirteen tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation thirteen tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation thirteen tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_twelve,
        "generation_thirteen_source": source_commit,
        "generation_thirteen_receipt": receipt_commit,
        "generation_thirteen_state": state_commit,
        "generation_thirteen_baton": baton_commit,
    }


def _commit_generation_fourteen_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build the exact generation-fourteen topology on top of a complete generation-thirteen chain."""

    generation_thirteen = _commit_generation_thirteen_publication(repo, state, monkeypatch)
    generation_thirteen_baton = generation_thirteen["generation_thirteen_baton"]
    for name, key in (
        ("GENERATION_THIRTEEN_SOURCE_COMMIT", "generation_thirteen_source"),
        ("GENERATION_THIRTEEN_RECEIPT_COMMIT", "generation_thirteen_receipt"),
        ("GENERATION_THIRTEEN_STATE_COMMIT", "generation_thirteen_state"),
        ("GENERATION_THIRTEEN_BATON_COMMIT", "generation_thirteen_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_thirteen[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-thirteen-topology.txt"
        unexpected.write_text("not the frozen generation-thirteen tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-thirteen topology edge")
    monkeypatch.setattr(
        mission_state, "GENERATION_FOURTEEN_SOURCE_PARENT", generation_thirteen_baton
    )
    expected_publication = {
        "generation": 14,
        "supersedes_receipt_commit": generation_thirteen["generation_thirteen_receipt"],
        "recovery_parent": generation_thirteen_baton,
        "reason_code": GENERATION_FOURTEEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation fourteen source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation fourteen source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            controller_source = _controller_source_for_publication(
                generation=14,
                supersedes_receipt_commit=generation_thirteen["generation_thirteen_receipt"],
                recovery_parent=generation_thirteen_baton,
                reason_code=GENERATION_FOURTEEN_REASON_CODE,
            )
            path.write_text(controller_source)
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation fourteen\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation fourteen source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation fourteen source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_thirteen, "generation_fourteen_source": source_commit}

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
    _git(repo, "commit", "-m", "generation fourteen receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation fourteen state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation fourteen tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation fourteen tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation fourteen tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_thirteen,
        "generation_fourteen_source": source_commit,
        "generation_fourteen_receipt": receipt_commit,
        "generation_fourteen_state": state_commit,
        "generation_fourteen_baton": baton_commit,
    }


def _commit_generation_fifteen_publication(
    repo: Path,
    state: dict,
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_overrides: dict[str, object] | None = None,
    include_receipt: bool = True,
    include_baton: bool = True,
    source_paths: tuple[str, ...] = GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS,
    wrong_source_parent: bool = False,
) -> dict[str, str]:
    """Build generation fifteen on an exact synthetic generation-one-through-fourteen chain."""

    generation_fourteen = _commit_generation_fourteen_publication(repo, state, monkeypatch)
    generation_fourteen_baton = generation_fourteen["generation_fourteen_baton"]
    for name, key in (
        ("GENERATION_FOURTEEN_SOURCE_COMMIT", "generation_fourteen_source"),
        ("GENERATION_FOURTEEN_RECEIPT_COMMIT", "generation_fourteen_receipt"),
        ("GENERATION_FOURTEEN_STATE_COMMIT", "generation_fourteen_state"),
        ("GENERATION_FOURTEEN_BATON_COMMIT", "generation_fourteen_baton"),
    ):
        monkeypatch.setattr(mission_state, name, generation_fourteen[key])
    if wrong_source_parent:
        unexpected = repo / "unexpected-generation-fourteen-topology.txt"
        unexpected.write_text("not the frozen generation-fourteen tip\n")
        _git(repo, "add", unexpected.name)
        _git(repo, "commit", "-m", "unexpected generation-fourteen topology edge")
    monkeypatch.setattr(
        mission_state,
        "GENERATION_FIFTEEN_SOURCE_PARENT",
        generation_fourteen_baton,
    )
    expected_publication = {
        "generation": 15,
        "supersedes_receipt_commit": generation_fourteen["generation_fourteen_receipt"],
        "recovery_parent": generation_fourteen_baton,
        "reason_code": GENERATION_FIFTEEN_REASON_CODE,
    }
    monkeypatch.setattr(mission_state, "EXPECTED_RECOVERY_PUBLICATION", expected_publication)

    preregistered_state = copy.deepcopy(state)
    _set_preregistered_phase(preregistered_state)
    for relative in source_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "MISSION_STATE.json":
            path.write_text(json.dumps(preregistered_state, indent=2) + "\n")
        elif relative == "CONTINUITY.md":
            path.write_text("generation fifteen source recovery\n")
        elif relative == "HANDOFF.md":
            path.write_text("generation fifteen source handoff\n")
        elif relative.endswith("/authorize_launch135.py"):
            path.write_text(
                _controller_source_for_publication(
                    generation=15,
                    supersedes_receipt_commit=generation_fourteen["generation_fourteen_receipt"],
                    recovery_parent=generation_fourteen_baton,
                    reason_code=GENERATION_FIFTEEN_REASON_CODE,
                )
            )
        elif relative.endswith("/verify_tooling135.py"):
            path.write_text(
                "# generation fifteen\n"
                "def validate_published_receipt_structure(receipt, *args, **kwargs):\n"
                "    return []\n"
            )
        else:
            path.write_text(f"generation fifteen source: {relative}\n")
    _git(repo, "add", *source_paths)
    _git(repo, "commit", "-m", "generation fifteen source")
    source_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", source_commit)
    if not include_receipt:
        state.clear()
        state.update(preregistered_state)
        return {**generation_fourteen, "generation_fifteen_source": source_commit}

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
    _git(repo, "commit", "-m", "generation fifteen receipt")
    receipt_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", receipt_commit)

    control_state = copy.deepcopy(state)
    _set_control_hardening_phase(control_state)
    state.clear()
    state.update(control_state)
    (repo / "MISSION_STATE.json").write_text(json.dumps(state, indent=2) + "\n")
    _git(repo, "add", "MISSION_STATE.json")
    _git(repo, "commit", "-m", "generation fifteen state")
    state_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        (repo / "CONTINUITY.md").write_text("generation fifteen tooling transition\n")
        (repo / "HANDOFF.md").write_text("generation fifteen tooling handoff\n")
        _git(repo, "add", "CONTINUITY.md", "HANDOFF.md")
        _git(repo, "commit", "-m", "generation fifteen tooling baton")
    baton_commit = _git(repo, "rev-parse", "HEAD").decode().strip()
    if include_baton:
        _git(repo, "update-ref", "refs/remotes/origin/master", baton_commit)
    return {
        **generation_fourteen,
        "generation_fifteen_source": source_commit,
        "generation_fifteen_receipt": receipt_commit,
        "generation_fifteen_state": state_commit,
        "generation_fifteen_baton": baton_commit,
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
    launch_state["run_state"] = "IDLE"
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
            lambda state: state["claim_state"].__setitem__("production_readiness", "ESTABLISHED"),
            "claim_state:",
        ),
        (
            lambda state: state["paper_state"].__setitem__("status", "SUBMISSION_READY"),
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


@pytest.mark.parametrize(
    ("mutation", "problem_prefix"),
    [
        (
            lambda state: state["workspace_boundary"].__setitem__(
                "cross_workspace_access_requires_explicit_operator_request",
                1,
            ),
            "workspace_boundary:",
        ),
        (
            lambda state: state["storage_gate"].__setitem__(
                "minimum_local_free_gib_before_new_proof_collection",
                15.0,
            ),
            "storage_gate:minimum_local_free_gib_before_new_proof_collection:",
        ),
        (
            lambda state: state["next_program"].__setitem__("iteration", 135.0),
            "next_iteration:",
        ),
    ],
)
def test_canonical_state_rejects_numeric_type_impostors(
    mutation,
    problem_prefix: str,
) -> None:
    state = copy.deepcopy(load_state())
    mutation(state)

    assert any(
        problem.startswith(problem_prefix)
        for problem in validate_state(state)
    )


def test_canonical_state_returns_stable_problem_for_non_object_next_program() -> None:
    state = copy.deepcopy(load_state())
    state["next_program"] = ["x"]

    problems = validate_state(state)

    assert "next_program_fields:not-object" in problems


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_state_loader_rejects_duplicate_and_nonfinite_json(tmp_path: Path, constant: str) -> None:
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


def test_preregistered_phase_is_an_exact_unknown_runtime_stop() -> None:
    state = copy.deepcopy(load_state())
    _set_preregistered_phase(state)

    assert state["run_state"] == "UNKNOWN"
    assert state["next_program"] == {
        "iteration": 135,
        "name": mission_state.EXPECTED_PROGRAM_NAME,
        "phase": "PREREGISTERED_TOOLING_REQUIRED",
        "authorized_actions": list(PREREGISTERED_AUTHORIZED_ACTIONS),
        "forbidden_actions": list(PREREGISTERED_FORBIDDEN_ACTIONS),
    }
    forbidden = " ".join(PREREGISTERED_FORBIDDEN_ACTIONS)
    for required_stop in (
        "de-prepare",
        "host",
        "H, E, P, or S",
        "launch activation",
        "live smoke",
        "analytic episode",
        "infer IDLE",
        "run analyzers",
        "external governance settings",
    ):
        assert required_stop in forbidden

    state["run_state"] = "IDLE"

    assert (
        "phase_run_state:PREREGISTERED_TOOLING_REQUIRED:'IDLE'!='UNKNOWN'"
        in validate_state(state)
    )


def test_control_hardening_phase_actions_and_unknown_runtime_are_exact(
    tmp_path: Path,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_control_hardening_phase(state)

    problems = validate_state(state, repo)

    assert state["run_state"] == "UNKNOWN"
    assert state["next_program"]["authorized_actions"] == list(
        CONTROL_HARDENING_AUTHORIZED_ACTIONS
    )
    assert state["next_program"]["forbidden_actions"] == list(
        CONTROL_HARDENING_FORBIDDEN_ACTIONS
    )
    forbidden = " ".join(CONTROL_HARDENING_FORBIDDEN_ACTIONS)
    for required_stop in (
        "host",
        "H, E, P, or S",
        "launch activation",
        "live smoke",
        "analytic episode",
        "infer IDLE",
        "run analyzers",
        "external governance settings",
    ):
        assert required_stop in forbidden
    assert any(problem.startswith("tooling_publication:receipt_missing:") for problem in problems)


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
    else:
        state["run_state"] = "IDLE"

    problems = validate_state(state, repo)

    assert f"phase_artifact_contract:{phase}:not_implemented" in problems


def test_launch_phase_requires_published_generation_three_activation_chain(tmp_path: Path) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    state["run_state"] = "IDLE"
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


def test_generation_fifteen_control_phase_accepts_canonical_r15_t15_b15(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)

    assert state["next_program"]["phase"] == "CONTROL_HARDENING_REQUIRED"
    assert state["run_state"] == "UNKNOWN"
    assert _git(repo, "rev-parse", "origin/master").decode().strip() == commits[
        "generation_fifteen_baton"
    ]
    assert validate_state(state, repo) == []


def test_generation_fifteen_control_phase_accepts_disposable_b15_with_origin_at_r15(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)
    _git(
        repo,
        "update-ref",
        "refs/remotes/origin/master",
        commits["generation_fifteen_receipt"],
    )

    assert _git(repo, "rev-parse", "HEAD").decode().strip() == commits[
        "generation_fifteen_baton"
    ]
    assert _git(repo, "rev-parse", "origin/master").decode().strip() == commits[
        "generation_fifteen_receipt"
    ]
    assert validate_state(state, repo) == []


def test_generation_fifteen_control_phase_invokes_frozen_controller_with_no_descendants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)
    observed: list[dict[str, object]] = []

    def controller(_repo: Path, **kwargs):
        observed.append(kwargs)
        return {
            "problems": [],
            "references": {},
            "authority": "none",
            "launch_authorized": False,
            "control_publication_status": (
                mission_state.CONTROL_PUBLICATION_PUBLISHED_STATUS
            ),
        }

    monkeypatch.setattr(
        mission_state,
        "_load_launch_controller",
        lambda _repo, _source_commit: controller,
    )

    assert validate_state(state, repo) == []
    assert observed == [
        {
            "phase": "CONTROL_HARDENING_REQUIRED",
            "tooling_receipt_commit": commits["generation_fifteen_receipt"],
            "tooling_baton_commit": commits["generation_fifteen_baton"],
            "descendants": [],
            "upstream_commit": commits["generation_fifteen_baton"],
            "candidate": False,
        }
    ]


def test_generation_fifteen_control_phase_rejects_every_post_b15_descendant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)
    _git(repo, "commit", "--allow-empty", "-m", "hostile post-B15 descendant")

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_fifteen_commit_count:3" in problems
    assert "authorization:control-hardening-descendant-count:1" in problems
    assert _git(repo, "rev-parse", "origin/master").decode().strip() == commits[
        "generation_fifteen_baton"
    ]


def test_generation_fifteen_control_phase_rejects_origin_advanced_beyond_b15(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)
    _git(repo, "commit", "--allow-empty", "-m", "unreviewed origin advancement")
    advanced = _git(repo, "rev-parse", "HEAD").decode().strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", advanced)
    _git(repo, "reset", "--hard", commits["generation_fifteen_baton"])

    problems = validate_state(state, repo)

    assert (
        "authorization:control-hardening-origin-master-not-r15-or-b15"
        in problems
    )


@pytest.mark.parametrize(
    ("mutation", "expected_problem"),
    [
        ("missing-status", "authorization:control-publication-status:"),
        ("malformed-status", "authorization:control-publication-status:"),
        ("wrong-status", "authorization:control-publication-status:"),
        ("wrong-authority", "authorization:control-publication-authority:"),
        (
            "launch-authorized",
            "authorization:control-publication-launch-authorized:",
        ),
        ("extra-field", "authorization:controller-field-set:"),
        ("nonstring-field", "authorization:controller-field-set:"),
        (
            "unexpected-reference",
            "authorization:control-publication-references:",
        ),
        (
            "non-dict-empty-reference",
            "authorization:control-publication-references:",
        ),
    ],
)
def test_generation_fifteen_control_phase_rejects_malformed_controller_claims(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_problem: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch)
    result: dict[str, object] = {
        "problems": [],
        "references": {},
        "authority": "none",
        "launch_authorized": False,
        "control_publication_status": (
            mission_state.CONTROL_PUBLICATION_PUBLISHED_STATUS
        ),
    }
    if mutation == "missing-status":
        result.pop("control_publication_status")
    elif mutation == "malformed-status":
        result["control_publication_status"] = []
    elif mutation == "wrong-status":
        result["control_publication_status"] = (
            mission_state.CONTROL_PUBLICATION_CANDIDATE_STATUS
        )
    elif mutation == "wrong-authority":
        result["authority"] = "origin-published"
    elif mutation == "launch-authorized":
        result["launch_authorized"] = True
    elif mutation == "extra-field":
        result["capability"] = "launch"
    elif mutation == "nonstring-field":
        result[7] = "launch"
    elif mutation == "unexpected-reference":
        result["references"] = {"MISSION_STATE.json": "f" * 40}
    elif mutation == "non-dict-empty-reference":
        result["references"] = types.MappingProxyType({})
    else:
        raise AssertionError(f"unsupported controller mutation: {mutation}")

    monkeypatch.setattr(
        mission_state,
        "_load_launch_controller",
        lambda _repo, _source_commit: lambda _root, **_kwargs: result,
    )

    assert any(
        problem.startswith(expected_problem)
        for problem in validate_state(state, repo)
    )


def test_generation_fifteen_rejects_tooling_phase_in_place_of_control_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch)
    _set_tooling_phase(state)

    problems = validate_state(state, repo)

    assert (
        "tooling_publication:generation_fifteen_phase:"
        "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
    ) in problems


def test_generation_fifteen_receipt_history_is_exactly_fifteen_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

    assert history[0] == commits["generation_fifteen_receipt"]
    assert history[1] == commits["generation_fourteen_receipt"]
    assert len(history) == 15
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 14}, "tooling_publication:receipt_publication_generation:14"),
        ({"generation": 15.0}, "tooling_publication:receipt_publication_generation:15.0"),
        (
            {"supersedes_receipt_commit": "0" * 40},
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:'{('0' * 40)}'",
        ),
        (
            {"recovery_parent": "1" * 40},
            f"tooling_publication:receipt_publication_recovery_parent:'{('1' * 40)}'",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_fifteen_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch, publication_overrides=override)

    assert expected in validate_state(state, repo)


def test_generation_fifteen_source_scope_is_exactly_the_nineteen_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert len(GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS) == 19
    assert "scripts/make_handoff.py" in GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS
    assert "tests/test_handoff_generator.py" in GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_fifteen_source_must_be_direct_child_of_the_published_b14_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_fifteen_rejects_generation_fourteen_transition_parent_and_scope_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fifteen_publication(repo, state, monkeypatch)
    commit_row = mission_state._commit_row
    transitions = (
        (
            commits["generation_fourteen_receipt"],
            "tooling_publication:generation_fourteen_receipt",
        ),
        (
            commits["generation_fourteen_state"],
            "tooling_publication:generation_fourteen_state",
        ),
        (
            commits["generation_fourteen_baton"],
            "tooling_publication:generation_fourteen_baton",
        ),
    )

    for commit, problem_prefix in transitions:
        for violation in ("parent", "scope"):

            def hostile_commit_row(
                root: Path,
                candidate: str,
                *,
                target: str = commit,
                hostile_field: str = violation,
            ) -> tuple[tuple[str, ...], tuple[str, ...]]:
                parents, paths = commit_row(root, candidate)
                if candidate != target:
                    return parents, paths
                if hostile_field == "parent":
                    return ("f" * 40,), paths
                return parents, (*paths, "unexpected-generation-fourteen.txt")

            monkeypatch.setattr(mission_state, "_commit_row", hostile_commit_row)

            assert f"{problem_prefix}_{violation}" in validate_state(state, repo)


def test_generation_fifteen_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


@pytest.mark.parametrize(
    "relative_path",
    [".github/workflows/ci.yml", "LICENSE"],
)
def test_generation_fifteen_rejects_mutation_of_earlier_frozen_source_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fifteen_publication(repo, state, monkeypatch)
    frozen = repo / relative_path
    frozen.write_text(frozen.read_text() + "hostile post-F15 mutation\n")
    _git(repo, "add", relative_path)
    _git(repo, "commit", "-m", "hostile post-F15 frozen-source mutation")

    problems = validate_state(state, repo)

    assert f"tooling_publication:immutable_path_changed:{relative_path}" in problems


@pytest.mark.parametrize(
    ("generation", "builder"),
    [
        (14, _commit_generation_fourteen_publication),
        (15, _commit_generation_fifteen_publication),
    ],
)
def test_generations_fourteen_and_fifteen_use_frozen_validator_and_launch_controller(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    generation: int,
    builder,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    builder(repo, state, monkeypatch)
    validator_calls: list[int] = []
    controller_calls: list[int] = []

    def validator(_receipt, **_kwargs):
        validator_calls.append(generation)
        return []

    def controller(*_args, **_kwargs):
        controller_calls.append(generation)
        result: dict[str, object] = {
            "problems": [],
            "references": {},
            "authority": "none",
            "launch_authorized": False,
        }
        if generation == 15:
            result.update(
                {
                    "control_publication_status": (
                        mission_state.CONTROL_PUBLICATION_PUBLISHED_STATUS
                    ),
                }
            )
        return result

    monkeypatch.setattr(
        mission_state,
        "_load_tooling_receipt_validator",
        lambda _repo, _source_commit: validator,
    )
    monkeypatch.setattr(
        mission_state,
        "_load_launch_controller",
        lambda _repo, _source_commit: controller,
    )

    assert validate_state(state, repo) == []
    assert validator_calls == [generation]
    assert controller_calls == [generation]


def test_generation_fourteen_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fourteen_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_fourteen_receipt_history_is_exactly_fourteen_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_fourteen_publication(repo, state, monkeypatch)

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

    assert history[0] == commits["generation_fourteen_receipt"]
    assert history[1] == commits["generation_thirteen_receipt"]
    assert len(history) == 14
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 13}, "tooling_publication:receipt_publication_generation:13"),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_fourteen_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fourteen_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_fourteen_source_must_be_direct_child_of_the_published_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fourteen_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_fourteen_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_fourteen_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_thirteen_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_thirteen_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_thirteen_receipt_history_is_exactly_thirteen_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_thirteen_publication(repo, state, monkeypatch)

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

    assert history[0] == commits["generation_thirteen_receipt"]
    assert history[1] == commits["generation_twelve_receipt"]
    assert len(history) == 13
    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 12}, "tooling_publication:receipt_publication_generation:12"),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_thirteen_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_thirteen_publication(
        repo, state, monkeypatch, publication_overrides=override
    )

    assert expected in validate_state(state, repo)


def test_generation_thirteen_source_must_be_direct_child_of_the_published_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_thirteen_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_thirteen_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_thirteen_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_twelve_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_twelve_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"generation": 11}, "tooling_publication:receipt_publication_generation:11"),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_twelve_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_twelve_publication(repo, state, monkeypatch, publication_overrides=override)

    assert expected in validate_state(state, repo)


def test_generation_twelve_source_scope_is_exactly_the_eleven_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_TWELVE_SOURCE_COMMIT_PATHS == (
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
    _commit_generation_twelve_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_TWELVE_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_twelve_source_must_be_direct_child_of_the_published_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_twelve_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_twelve_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_twelve_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_twelve_rejects_hostile_generation_eleven_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_twelve_publication(repo, state, monkeypatch)
    monkeypatch.setattr(
        mission_state,
        "GENERATION_ELEVEN_BATON_COMMIT",
        commits["generation_eleven_state"],
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_eleven_baton_scope" in problems


def test_generation_eleven_tooling_phase_accepts_exact_recovery_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eleven_publication(repo, state, monkeypatch)

    assert validate_state(state, repo) == []


def test_generation_eleven_receipt_history_is_exactly_eleven_generations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_eleven_publication(repo, state, monkeypatch)

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

    assert history == [
        commits["generation_eleven_receipt"],
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
        ({"generation": 10}, "tooling_publication:receipt_publication_generation:10"),
        (
            {"supersedes_receipt_commit": "f" * 40},
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
        ),
        (
            {"reason_code": "NOT_THE_FROZEN_REASON"},
            "tooling_publication:receipt_publication_reason_code:'NOT_THE_FROZEN_REASON'",
        ),
    ],
)
def test_generation_eleven_publication_claim_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
    expected: str,
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eleven_publication(repo, state, monkeypatch, publication_overrides=override)

    assert expected in validate_state(state, repo)


def test_generation_eleven_source_scope_is_exactly_the_twenty_two_path_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert mission_state.GENERATION_ELEVEN_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "LICENSE",
        "MISSION_STATE.json",
        f"{mission_state.ITER135_EXPERIMENT_REL}/analyze_dose135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/authorize_launch135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/capture_environment135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/collect_proof135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/make_launch_manifest.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_dose135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/run_smoke135.sh",
        f"{mission_state.ITER135_EXPERIMENT_REL}/validate_smoke135.py",
        f"{mission_state.ITER135_EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_environment_capture.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launch_manifest.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_proof_collector.py",
        "tests/test_iter135_smoke_pipeline.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )

    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eleven_publication(
        repo,
        state,
        monkeypatch,
        source_paths=GENERATION_ELEVEN_SOURCE_COMMIT_PATHS + ("README.md",),
    )

    assert "tooling_publication:recovery_source_commit_scope" in validate_state(state, repo)


def test_generation_eleven_source_must_be_direct_child_of_the_published_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eleven_publication(repo, state, monkeypatch, wrong_source_parent=True)

    assert "tooling_publication:recovery_source_parent" in validate_state(state, repo)


def test_generation_eleven_tooling_phase_rejects_missing_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    _commit_generation_eleven_publication(repo, state, monkeypatch, include_baton=False)

    assert validate_state(state, repo) != []


def test_generation_eleven_rejects_hostile_generation_ten_baton_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    commits = _commit_generation_eleven_publication(repo, state, monkeypatch)
    monkeypatch.setattr(
        mission_state, "GENERATION_TEN_BATON_COMMIT", commits["generation_ten_state"]
    )

    problems = validate_state(state, repo)

    assert "tooling_publication:generation_ten_baton_scope" in problems


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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_ten_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_nine_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_eight_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_seven_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_six_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(repo, "log", "--format=%H", "--", TOOLING_RECEIPT_REL.as_posix()).decode().splitlines()
    )

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
            f"tooling_publication:receipt_publication_supersedes_receipt_commit:{'f' * 40!r}",
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
    _commit_generation_five_publication(repo, state, monkeypatch, publication_overrides=override)

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

    history = (
        _git(
            repo,
            "log",
            "--format=%H",
            "--",
            TOOLING_RECEIPT_REL.as_posix(),
        )
        .decode()
        .splitlines()
    )

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
    advanced = (
        _git(
            repo,
            "commit-tree",
            tree,
            "-p",
            launch["activation"],
            "-m",
            "unreviewed origin advancement",
        )
        .decode()
        .strip()
    )
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


def test_local_launch_candidate_rejects_numeric_alias_for_controller_validity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    _git(repo, "update-ref", "refs/remotes/origin/master", launch["smoke"])

    def controller(root: Path, **kwargs):
        result = _structural_launch_controller(root, **kwargs)
        result["candidate_valid"] = 1
        return result

    monkeypatch.setattr(
        mission_state,
        "_load_launch_controller",
        lambda _repo, _source_commit: controller,
    )

    result = validate_local_launch_candidate(repo)

    assert result["candidate_valid"] is False
    assert result["authoritative"] is False
    assert result["launch_authorized"] is False
    assert result["problems"] == ["authorization:candidate-valid:1!=True"]


def test_local_launch_candidate_rejects_origin_advanced_beyond_exact_smoke_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, state = _minimal_state_repo(tmp_path)
    _set_tooling_phase(state)
    generation = _commit_generation_three_publication(repo, state, monkeypatch)
    launch = _append_launch_authorization_chain(repo, state, generation)
    tree = _git(repo, "rev-parse", f"{launch['smoke']}^{{tree}}").decode().strip()
    advanced = (
        _git(
            repo,
            "commit-tree",
            tree,
            "-p",
            launch["smoke"],
            "-m",
            "unreviewed preflight advancement",
        )
        .decode()
        .strip()
    )
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
            lambda state: state.__setitem__("current_completed_iteration", 134.0),
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
            lambda state: state["storage_gate"].__setitem__(
                "minimum_local_free_gib_before_new_proof_collection", 15.0
            ),
            "candidate:state-storage-gate",
        ),
        (
            lambda state: state["workspace_boundary"].__setitem__(
                "cross_workspace_access_requires_explicit_operator_request", 1
            ),
            "candidate:state-workspace-boundary",
        ),
        (
            lambda state: state["next_program"].__setitem__(
                "phase", "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
            ),
            "candidate:state-next-program",
        ),
        (
            lambda state: state["next_program"]["authorized_actions"].append("unregistered launch"),
            "candidate:state-next-program",
        ),
        (
            lambda state: state["next_program"].__setitem__("iteration", 135.0),
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
    state["run_state"] = "IDLE"
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
    _git(repo, "checkout", "--detach", "--quiet", "HEAD")

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
