from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO
    / "experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py"
)
SPEC = importlib.util.spec_from_file_location("iter135_tooling_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


class SequenceClock:
    def __init__(self, *values: int) -> None:
        self._values = iter(values)

    def __call__(self) -> int:
        return next(self._values)


class RecordingRunner:
    def __init__(self, hook: Any = None, failure_index: int | None = None) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.hook = hook
        self.failure_index = failure_index

    def __call__(self, command: tuple[str, ...], cwd: Path) -> Any:
        index = len(self.commands)
        self.commands.append(command)
        if self.hook is not None:
            self.hook(index, command, cwd)
        return verifier.RawCommandResult(
            returncode=7 if index == self.failure_index else 0,
            stdout=f"stdout-{index}".encode(),
            stderr=f"stderr-{index}".encode() if index == self.failure_index else b"",
        )


def stable_git(_root: Path, _paths: tuple[str, ...]) -> Any:
    return verifier.GitState(
        head="a" * 40,
        dirty_entries=(),
        porcelain_sha256=hashlib.sha256(b"").hexdigest(),
        branch="master",
        upstream="origin/master",
        upstream_head="a" * 40,
        parents=(verifier.EXPECTED_PREREGISTRATION_HEAD,),
        commit_paths=tuple(sorted(verifier.EXPECTED_SOURCE_COMMIT_PATHS)),
    )


def stable_ancestry(_root: Path, _ancestor: str, _descendant: str) -> bool:
    return True


def replay_validate(receipt: dict[str, Any], root: Path, **kwargs: Any) -> list[str]:
    kwargs.setdefault("runner", RecordingRunner())
    return verifier.validate_receipt(receipt, root, **kwargs)


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "sentinel"
    for relative in verifier.REQUIRED_TEST_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    for relative in verifier.REQUIRED_PYTHON_TOOL_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")
    for relative in verifier.REQUIRED_SHELL_FILES:
        path = root / relative
        path.write_text("#!/bin/bash\nset -euo pipefail\n", encoding="utf-8")
    for relative in verifier.REQUIRED_DATA_FILES:
        path = root / relative
        path.write_text('{"schema":"fixture"}\n', encoding="utf-8")
    for relative in verifier.REQUIRED_CONTROL_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture control: {relative}\n", encoding="utf-8")
    return root


def run_green(root: Path, runner: RecordingRunner | None = None) -> tuple[dict, RecordingRunner]:
    active_runner = runner or RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=active_runner,
        git_probe=stable_git,
        wall_clock_ns=SequenceClock(1_000_000_000, 4_000_000_000),
        monotonic_clock_ns=SequenceClock(10_000, 20_000),
    )
    return receipt, active_runner


def refresh_payload_digest(receipt: dict[str, Any]) -> None:
    receipt.pop("receipt_payload_sha256", None)
    receipt["receipt_payload_sha256"] = verifier._sha256_bytes(  # noqa: SLF001
        verifier._canonical_json(receipt)  # noqa: SLF001
    )


def problem_codes(receipt: dict) -> set[str]:
    return {problem["code"] for problem in receipt["problems"]}


def test_green_receipt_binds_complete_discovered_surface_and_exact_commands(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    extra_test = root / "tests/test_iter135_new_guard.py"
    extra_test.write_text("def test_new_guard():\n    assert True\n", encoding="utf-8")
    extra_tool = root / verifier.EXPERIMENT_REL / "new_guard.py"
    extra_tool.write_text("VALUE = 2\n", encoding="utf-8")

    receipt, runner = run_green(root)
    inventory = verifier.discover_inventory(root)

    assert receipt["verdict"] == verifier.OK_VERDICT
    assert receipt["problem_count"] == 0
    assert receipt["inventory"] == inventory.as_dict()
    assert set(receipt["files"]) == set(inventory.tested_files)
    assert verifier.RECEIPT_REL not in receipt["files"]
    assert receipt["command_contract"] == [
        list(command) for command in verifier.build_commands(inventory)
    ]
    assert runner.commands == list(verifier.build_commands(inventory))
    assert len(receipt["commands"]) == 8
    assert Path(receipt["commands"][3]["argv"][0]).name == "shellcheck"
    assert Path(receipt["commands"][4]["argv"][0]).name == "ruff"
    assert receipt["commands"][4]["argv"][1:] == ["check", "."]
    assert Path(receipt["commands"][5]["argv"][0]).name == "pytest"
    assert receipt["commands"][5]["argv"][1:] == ["-q"]
    assert Path(receipt["commands"][6]["argv"][0]).name.startswith("python3")
    assert receipt["commands"][6]["argv"][1:] == ["scripts/validate_docs.py"]
    assert Path(receipt["commands"][7]["argv"][0]).name.startswith("python3")
    assert receipt["commands"][7]["argv"][1:] == ["scripts/mission_state.py"]
    assert all("stdout" not in record and "stderr" not in record for record in receipt["commands"])
    assert receipt["timing"]["wall_duration_ns"] == 3_000_000_000
    assert receipt["timing"]["monotonic_duration_ns"] == 10_000
    assert replay_validate(receipt, root, git_probe=stable_git) == []


def test_command_failure_cannot_emit_green_receipt(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, runner = run_green(root, RecordingRunner(failure_index=1))

    assert len(runner.commands) == 8
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "COMMAND_FAILED" in problem_codes(receipt)
    assert receipt["commands"][1]["return_code"] == 7
    assert "stderr" not in receipt["commands"][1]
    assert replay_validate(receipt, root, git_probe=stable_git)


def test_forged_green_from_failed_run_is_rejected_by_independent_replay(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root, RecordingRunner(failure_index=2))
    forged = copy.deepcopy(receipt)
    forged["verdict"] = verifier.OK_VERDICT
    forged["problem_count"] = 0
    forged["problems"] = []
    forged["commands"][2]["return_code"] = 0
    refresh_payload_digest(forged)

    errors = replay_validate(
        forged,
        root,
        runner=RecordingRunner(failure_index=2),
        git_probe=stable_git,
    )

    assert "command_2 independent replay failed" in errors


def test_default_git_cleanliness_probe_is_repository_global(monkeypatch: Any, tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(_root: Path, argv: tuple[str, ...]) -> bytes:
        calls.append(argv)
        if argv[:3] == ("rev-parse", "--verify", "HEAD"):
            return b"a" * 40 + b"\n"
        if argv[0] == "symbolic-ref":
            return b"master\n"
        if argv[:2] == ("rev-parse", "--abbrev-ref"):
            return b"origin/master\n"
        if argv[:3] == ("rev-parse", "--verify", "@{u}"):
            return b"a" * 40 + b"\n"
        if argv[0] == "rev-list":
            return b"a" * 40 + b" " + b"0" * 40 + b"\n"
        if argv[0] == "diff-tree":
            return b"\0".join(
                path.encode() for path in verifier.EXPECTED_SOURCE_COMMIT_PATHS
            ) + b"\0"
        return b""

    monkeypatch.setattr(verifier, "_git_bytes", fake_git)

    verifier.default_git_probe(tmp_path, ("tests/test_iter135_analyzer.py",))

    status_argv = next(argv for argv in calls if argv[0] == "status")
    assert status_argv == (
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )


def test_toolchain_resolution_rejects_path_precedence_shim(
    monkeypatch: Any, tmp_path: Path
) -> None:
    shim = tmp_path / "pytest"
    shim.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    verifier._resolve_toolchain_cached.cache_clear()  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="outside trusted roots: pytest"):
        verifier.resolve_toolchain()

    verifier._resolve_toolchain_cached.cache_clear()  # noqa: SLF001


def test_sanitized_environment_drops_inherited_pytest_controls(monkeypatch: Any) -> None:
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    environment = verifier._sanitized_environment(verifier.resolve_toolchain())  # noqa: SLF001

    assert "PYTEST_ADDOPTS" not in environment
    assert "PYTEST_PLUGINS" not in environment
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONNOUSERSITE"] == "1"


def test_source_verification_requires_pushed_master_and_exact_commit_scope(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)

    def unpublishable_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        return verifier.GitState(
            head="a" * 40,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="feature",
            upstream="origin/feature",
            upstream_head="b" * 40,
            parents=(verifier.EXPECTED_PREREGISTRATION_HEAD,),
            commit_paths=(verifier.REQUIRED_TEST_FILES[0],),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=unpublishable_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert runner.commands == []
    assert {
        "GIT_BRANCH",
        "GIT_UPSTREAM",
        "SOURCE_NOT_PUSHED",
        "SOURCE_COMMIT_SCOPE",
    } <= problem_codes(receipt)


def test_source_verification_rejects_non_preregistered_parent(tmp_path: Path) -> None:
    root = make_repo(tmp_path)

    def wrong_parent_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        state = stable_git(_root, _paths)
        return verifier.GitState(
            head=state.head,
            dirty_entries=state.dirty_entries,
            porcelain_sha256=state.porcelain_sha256,
            branch=state.branch,
            upstream=state.upstream,
            upstream_head=state.upstream_head,
            parents=("f" * 40,),
            commit_paths=state.commit_paths,
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=wrong_parent_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert runner.commands == []
    assert "SOURCE_PARENT" in problem_codes(receipt)


def test_content_drift_during_test_execution_is_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    target = root / verifier.REQUIRED_PYTHON_TOOL_FILES[0]

    def mutate(index: int, _command: tuple[str, ...], _cwd: Path) -> None:
        if index == 0:
            target.write_text("VALUE = 999\n", encoding="utf-8")

    receipt, runner = run_green(root, RecordingRunner(hook=mutate))

    assert len(runner.commands) == 1
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "TESTED_FILE_DRIFT" in problem_codes(receipt)
    assert "COMMAND_SET_INCOMPLETE" in problem_codes(receipt)


def test_modify_then_restore_is_detected_by_execution_identity(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    target = root / verifier.REQUIRED_PYTHON_TOOL_FILES[0]
    original = target.read_bytes()
    original_times = target.stat().st_atime_ns, target.stat().st_mtime_ns

    def mutate_and_restore(index: int, _command: tuple[str, ...], _cwd: Path) -> None:
        if index == 0:
            target.write_bytes(b"VALUE = 999\n")
            target.write_bytes(original)
            os.utime(target, ns=original_times)

    receipt, runner = run_green(root, RecordingRunner(hook=mutate_and_restore))

    assert len(runner.commands) == 1
    assert target.read_bytes() == original
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "TESTED_FILE_DRIFT" in problem_codes(receipt)


def test_test_set_drift_during_execution_is_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)

    def add_test(index: int, _command: tuple[str, ...], cwd: Path) -> None:
        if index == 0:
            (cwd / "tests/test_iter135_injected.py").write_text(
                "def test_injected():\n    assert False\n", encoding="utf-8"
            )

    receipt, runner = run_green(root, RecordingRunner(hook=add_test))

    assert len(runner.commands) == 1
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "INVENTORY_DRIFT" in problem_codes(receipt)
    assert "COMMAND_SET_INCOMPLETE" in problem_codes(receipt)


def test_missing_frozen_test_is_initialization_failure(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / verifier.REQUIRED_TEST_FILES[0]).unlink()

    receipt, runner = run_green(root)

    assert not runner.commands
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "INITIALIZATION_FAILED" in problem_codes(receipt)


def test_unreviewed_shell_tool_is_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / verifier.EXPERIMENT_REL / "surprise.sh").write_text("exit 0\n", encoding="utf-8")

    with pytest.raises(verifier.VerificationError, match="unreviewed"):
        verifier.discover_inventory(root)


def test_forged_command_and_payload_are_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    forged["commands"][0]["return_code"] = 0
    forged["commands"][0]["argv"] = ["true"]
    forged["command_contract"][0] = ["true"]
    refresh_payload_digest(forged)

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert "command contract mismatch" in errors
    assert "command_0 argv mismatch" in errors


def test_stale_receipt_is_rejected_after_bound_source_changes(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    target = root / verifier.REQUIRED_PYTHON_TOOL_FILES[-1]
    target.write_text("VALUE = 'changed'\n", encoding="utf-8")

    errors = replay_validate(receipt, root, git_probe=stable_git)

    assert "tested source content is stale or forged" in errors
    assert "file content-set digest mismatch" in errors


def test_git_head_or_dirty_state_drift_is_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    calls = 0

    def drifting_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        nonlocal calls
        calls += 1
        return verifier.GitState(
            head=("a" if calls == 1 else "b") * 40,
            dirty_entries=(() if calls == 1 else (" M tests/test_iter135_analyzer.py",)),
            porcelain_sha256=hashlib.sha256(str(calls).encode()).hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head=("a" if calls == 1 else "b") * 40,
            commit_paths=tuple(sorted(verifier.EXPECTED_SOURCE_COMMIT_PATHS)),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=drifting_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "GIT_HEAD_DRIFT" in problem_codes(receipt)
    assert "GIT_DIRTY_STATE_DRIFT" in problem_codes(receipt)


def test_dirty_tested_paths_at_verification_time_cannot_emit_green(tmp_path: Path) -> None:
    root = make_repo(tmp_path)

    def dirty_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        raw = b" M tests/test_iter135_analyzer.py\0"
        return verifier.GitState(
            head="a" * 40,
            dirty_entries=(" M tests/test_iter135_analyzer.py",),
            porcelain_sha256=hashlib.sha256(raw).hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head="a" * 40,
            commit_paths=tuple(sorted(verifier.EXPECTED_SOURCE_COMMIT_PATHS)),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=dirty_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "GIT_REPOSITORY_DIRTY_START" in problem_codes(receipt)
    assert "GIT_REPOSITORY_DIRTY_END" in problem_codes(receipt)
    assert runner.commands == []


def test_receipt_only_descendant_commit_preserves_clean_receipt_validity(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    ancestry_calls: list[tuple[str, str]] = []

    def descendant_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        return verifier.GitState(
            head="b" * 40,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head="b" * 40,
            parents=("a" * 40,),
            commit_paths=(verifier.RECEIPT_REL,),
        )

    def ancestry(_root: Path, ancestor: str, descendant: str) -> bool:
        ancestry_calls.append((ancestor, descendant))
        return True

    errors = replay_validate(
        receipt,
        root,
        git_probe=descendant_git,
        ancestry_probe=ancestry,
    )

    assert errors == []
    assert ancestry_calls == [("a" * 40, "b" * 40)]


def test_receipt_only_commit_can_be_replayed_before_push(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)

    def prepush_receipt_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        return verifier.GitState(
            head="b" * 40,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head="a" * 40,
            parents=("a" * 40,),
            commit_paths=(verifier.RECEIPT_REL,),
        )

    errors = replay_validate(
        receipt,
        root,
        git_probe=prepush_receipt_git,
        ancestry_probe=stable_ancestry,
    )

    assert errors == []


def test_published_structure_binds_exact_h_to_h3_and_rejects_later_tool_drift(
    monkeypatch: Any, tmp_path: Path
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    receipt_path = root / verifier.RECEIPT_REL
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    source = "a" * 40
    receipt_commit = "b" * 40
    state_commit = "c" * 40
    baton_commit = "d" * 40
    later_commit = "e" * 40
    source_tree = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path != receipt_path
        )
    )
    parents = {
        source: (verifier.EXPECTED_PREREGISTRATION_HEAD,),
        receipt_commit: (source,),
        state_commit: (receipt_commit,),
        baton_commit: (state_commit,),
        later_commit: (baton_commit,),
    }
    paths = {
        source: tuple(sorted(verifier.EXPECTED_SOURCE_COMMIT_PATHS)),
        receipt_commit: (verifier.RECEIPT_REL,),
        state_commit: ("MISSION_STATE.json",),
        baton_commit: ("CONTINUITY.md", "HANDOFF.md"),
        later_commit: (verifier.REQUIRED_PYTHON_TOOL_FILES[0],),
    }

    def fake_git(_root: Path, argv: tuple[str, ...]) -> bytes:
        if argv[0] == "rev-list":
            commit = argv[-1]
            return (" ".join((commit, *parents[commit])) + "\n").encode()
        if argv[0] == "diff-tree":
            return b"\0".join(path.encode() for path in paths[argv[-1]]) + b"\0"
        if argv[0] == "ls-tree":
            return b"\0".join(path.encode() for path in source_tree) + b"\0"
        if argv[0] == "show":
            commit, relative = argv[-1].split(":", 1)
            if commit == receipt_commit and relative == verifier.RECEIPT_REL:
                return receipt_path.read_bytes()
            assert commit == source
            return (root / relative).read_bytes()
        if argv[0] == "log":
            return f"{receipt_commit}\n".encode()
        raise AssertionError(f"unexpected Git command: {argv}")

    monkeypatch.setattr(verifier, "_git_bytes", fake_git)

    def publication_git(head: str) -> Any:
        return verifier.GitState(
            head=head,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head=head,
            parents=parents[head],
            commit_paths=paths[head],
        )

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert errors == []

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(later_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("changed unauthorized paths" in error for error in errors)


def test_non_ancestor_current_head_rejects_otherwise_exact_receipt(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)

    def unrelated_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        return verifier.GitState(
            head="c" * 40,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head="c" * 40,
            parents=("f" * 40,),
            commit_paths=(verifier.RECEIPT_REL,),
        )

    errors = replay_validate(
        receipt,
        root,
        git_probe=unrelated_git,
        ancestry_probe=lambda _root, _ancestor, _descendant: False,
    )

    assert "claimed tested Git HEAD is not an ancestor of current HEAD" in errors


def test_current_dirty_tested_paths_reject_clean_ancestor_receipt(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)

    def current_dirty_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        raw = b" M tests/test_iter135_launcher.py\0"
        return verifier.GitState(
            head="b" * 40,
            dirty_entries=(" M tests/test_iter135_launcher.py",),
            porcelain_sha256=hashlib.sha256(raw).hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head="b" * 40,
            parents=("a" * 40,),
            commit_paths=(verifier.RECEIPT_REL,),
        )

    errors = replay_validate(
        receipt,
        root,
        git_probe=current_dirty_git,
        ancestry_probe=stable_ancestry,
    )

    assert "current repository is dirty before command replay" in errors
    assert "current repository is dirty" in errors


def test_forged_claim_of_dirty_test_execution_is_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    dirty = [" M tests/test_iter135_analyzer.py"]
    dirty_sha = hashlib.sha256(b" M tests/test_iter135_analyzer.py\0").hexdigest()
    for key in ("git_start", "git_end"):
        forged["repository"][key]["dirty_entries"] = dirty
        forged["repository"][key]["porcelain_v1_z_sha256"] = dirty_sha
    refresh_payload_digest(forged)

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert "claimed repository was dirty at start" in errors
    assert "claimed repository was dirty at end" in errors


def test_runner_exception_is_hashed_without_log_disclosure(tmp_path: Path) -> None:
    root = make_repo(tmp_path)

    def exploding_runner(_command: tuple[str, ...], _cwd: Path) -> Any:
        raise RuntimeError("super-secret-command-output")

    receipt = verifier.run_verification(
        root,
        runner=exploding_runner,
        git_probe=stable_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    encoded = json.dumps(receipt)
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "super-secret-command-output" not in encoded
    assert receipt["commands"][0]["return_code"] == 125
    assert receipt["commands"][0]["runner_error_type"] == "RuntimeError"


def test_atomic_writer_round_trips_and_refuses_output_symlink(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    output = root / verifier.EXPERIMENT_REL / "tooling_verification_receipt.json"
    receipt = verifier.run_and_write_verification(
        output,
        root,
        runner=RecordingRunner(),
        git_probe=stable_git,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )
    assert json.loads(output.read_text(encoding="utf-8")) == receipt
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))

    output.unlink()
    target = tmp_path / "outside.json"
    target.write_text("untouched", encoding="utf-8")
    output.symlink_to(target)
    with pytest.raises(verifier.VerificationError, match="symlink"):
        verifier.write_json_atomic(output, receipt)
    assert target.read_text(encoding="utf-8") == "untouched"


def test_receipt_writer_cannot_overwrite_frozen_data_source(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    output = root / verifier.REQUIRED_DATA_FILES[0]
    original = output.read_bytes()

    with pytest.raises(verifier.VerificationError, match="canonical receipt path"):
        verifier.run_and_write_verification(
            output,
            root,
            runner=RecordingRunner(),
            git_probe=stable_git,
            wall_clock_ns=SequenceClock(1, 2),
            monotonic_clock_ns=SequenceClock(1, 2),
        )

    assert output.read_bytes() == original


@pytest.mark.parametrize(
    "relative",
    ("MISSION_STATE.json", verifier.EXPERIMENT_REL + "/HYPOTHESIS.md"),
)
def test_receipt_writer_cannot_overwrite_control_plane(relative: str, tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    output = root / relative
    original = output.read_bytes()

    with pytest.raises(verifier.VerificationError, match="canonical receipt path"):
        verifier.run_and_write_verification(output, root)

    assert output.read_bytes() == original


def test_receipt_payload_digest_detects_structural_tampering(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    forged["problem_count"] = 0
    forged["timing"]["wall_duration_ns"] += 1

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert "receipt payload digest mismatch" in errors
