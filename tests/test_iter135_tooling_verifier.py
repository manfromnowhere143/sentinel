from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

import scripts.mission_state as mission_state


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO / "experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py"
)
SPEC = importlib.util.spec_from_file_location("iter135_tooling_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)

AUTHORIZATION_MODULE_PATH = (
    REPO
    / "experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py"
)
AUTHORIZATION_SPEC = importlib.util.spec_from_file_location(
    "iter135_tooling_publication_launch_controller",
    AUTHORIZATION_MODULE_PATH,
)
assert AUTHORIZATION_SPEC is not None and AUTHORIZATION_SPEC.loader is not None
authorization = importlib.util.module_from_spec(AUTHORIZATION_SPEC)
AUTHORIZATION_SPEC.loader.exec_module(authorization)


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


def fake_toolchain() -> dict[str, dict[str, Any]]:
    """Return deterministic trusted-root rows without depending on CI's ambient executables."""

    return {
        name: {
            "path": f"/usr/bin/{name}",
            "sha256": hashlib.sha256(f"iter135-fixture-{name}".encode()).hexdigest(),
            "bytes": 100 + index,
            "device": 1,
            "inode": 1_000 + index,
            "mode": 0o755,
            "mtime_ns": 1_000_000 + index,
            "ctime_ns": 2_000_000 + index,
            "version": f"{name} deterministic-fixture-v1",
        }
        for index, name in enumerate(verifier.TOOL_NAMES)
    }


def stable_git(_root: Path, _paths: tuple[str, ...]) -> Any:
    return verifier.GitState(
        head="a" * 40,
        dirty_entries=(),
        porcelain_sha256=hashlib.sha256(b"").hexdigest(),
        branch="master",
        upstream="origin/master",
        upstream_head="a" * 40,
        parents=(verifier.RECOVERY_SOURCE_PARENT,),
        commit_paths=tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
    )


def stable_ancestry(_root: Path, _ancestor: str, _descendant: str) -> bool:
    return True


def replay_validate(receipt: dict[str, Any], root: Path, **kwargs: Any) -> list[str]:
    kwargs.setdefault("runner", RecordingRunner())
    kwargs.setdefault("toolchain_resolver", fake_toolchain)
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
        toolchain_resolver=fake_toolchain,
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


def test_generation_sixteen_publication_contract_matches_all_controllers() -> None:
    reason = (
        "B15_SOURCE_BOUND_LIFECYCLE_CONTROL_AND_LIFECYCLE_EVIDENCE_SEPARATION_"
        "AND_NEXT_SOURCE_CONTENT_BINDING_BOOTSTRAP"
    )
    publication = {
        "generation": 16,
        "supersedes_receipt_commit": verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT,
        "recovery_parent": verifier.GENERATION_FIFTEEN_BATON_COMMIT,
        "reason_code": reason,
    }

    assert verifier.GENERATION_SIXTEEN_REASON == reason
    assert mission_state.GENERATION_SIXTEEN_REASON_CODE == reason
    assert authorization.GENERATION_SIXTEEN_REASON == reason
    assert verifier.EXPECTED_RECOVERY_PUBLICATION == publication
    assert mission_state.EXPECTED_RECOVERY_PUBLICATION == publication
    assert authorization.EXPECTED_LIFECYCLE_CONTROL_PUBLICATION == publication


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

    assert set(receipt) == verifier.RECEIPT_FIELDS
    assert receipt["verdict"] == verifier.OK_VERDICT
    assert receipt["problem_count"] == 0
    assert receipt["inventory"] == inventory.as_dict()
    assert "tests/test_handoff_generator.py" in inventory.tests
    assert "scripts/make_handoff.py" in inventory.control_files
    assert set(receipt["files"]) == set(inventory.tested_files)
    assert verifier.RECEIPT_REL not in receipt["files"]
    assert receipt["command_contract"] == [
        list(command) for command in verifier.build_commands(inventory, fake_toolchain())
    ]
    assert runner.commands == list(verifier.build_commands(inventory, fake_toolchain()))
    assert receipt["publication"] == verifier.EXPECTED_RECOVERY_PUBLICATION
    assert (
        verifier.RECOVERY_SOURCE_COMMIT_PATHS
        == verifier.GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS
    )
    assert len(verifier.RECOVERY_SOURCE_COMMIT_PATHS) == 17
    assert "MISSION_STATE.json" not in verifier.RECOVERY_SOURCE_COMMIT_PATHS
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


def test_published_tree_inventory_classifies_exact_offline_handoff_test(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    tree_paths = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )
    )

    def fake_tree(_root: Path, argv: tuple[str, ...]) -> bytes:
        assert argv[:5] == ("ls-tree", "-r", "-z", "--name-only", "a" * 40)
        return b"\0".join(path.encode() for path in tree_paths) + b"\0"

    monkeypatch.setattr(verifier, "_git_bytes", fake_tree)

    published = verifier._source_inventory_from_tree(root, "a" * 40)  # noqa: SLF001
    discovered = verifier.discover_inventory(root)

    assert published == discovered
    assert "tests/test_handoff_generator.py" in published.tests


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


def test_default_git_cleanliness_probe_is_repository_global(
    monkeypatch: Any, tmp_path: Path
) -> None:
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
            return (
                b"\0".join(path.encode() for path in verifier.RECOVERY_SOURCE_COMMIT_PATHS) + b"\0"
            )
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


def test_published_structural_probe_supports_detached_head_without_upstream(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(_root: Path, argv: tuple[str, ...]) -> bytes:
        calls.append(argv)
        if argv == ("rev-parse", "--verify", "HEAD^{commit}"):
            return b"a" * 40 + b"\n"
        if argv == (
            "rev-parse",
            "--verify",
            "refs/remotes/origin/master^{commit}",
        ):
            return b"b" * 40 + b"\n"
        if argv[0] == "rev-list":
            return b"a" * 40 + b" " + b"c" * 40 + b"\n"
        if argv[0] == "diff-tree":
            return b"MISSION_STATE.json\0"
        if argv[0] == "status":
            return b""
        raise AssertionError(f"unexpected Git command: {argv}")

    monkeypatch.setattr(verifier, "_git_bytes", fake_git)

    state = verifier.default_structural_git_probe(tmp_path, ())

    assert state.head == "a" * 40
    assert state.upstream_head == "b" * 40
    assert state.branch == ""
    assert state.upstream == ""
    assert not any(argv[0] == "symbolic-ref" or "@{u}" in argv for argv in calls)


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


def test_git_resolution_rejects_path_precedence_shim(monkeypatch: Any, tmp_path: Path) -> None:
    shim = tmp_path / "git"
    shim.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="Git executable is outside trusted roots"):
        verifier.resolve_git()

    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001


def test_git_resolution_fails_closed_when_version_probe_fails(monkeypatch: Any) -> None:
    monkeypatch.setattr(verifier.shutil, "which", lambda name: f"/usr/bin/{name}")

    def failed_version_probe(command: tuple[str, ...], **_kwargs: Any) -> Any:
        assert command == ("/usr/bin/git", "--version")
        return verifier.subprocess.CompletedProcess(command, 7, b"", b"probe failed")

    monkeypatch.setattr(verifier.subprocess, "run", failed_version_probe)
    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="Git executable version probe failed"):
        verifier.resolve_git()

    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001


def test_ancestry_probe_uses_only_dedicated_git_resolver(monkeypatch: Any, tmp_path: Path) -> None:
    git = {"path": "/usr/bin/git"}
    monkeypatch.setattr(verifier, "resolve_git", lambda: git)

    def forbidden_full_resolver() -> dict[str, dict[str, Any]]:
        raise AssertionError("ancestry probe attempted full toolchain resolution")

    monkeypatch.setattr(verifier, "resolve_toolchain", forbidden_full_resolver)
    observed: list[tuple[str, ...]] = []

    def successful_ancestry(command: tuple[str, ...], **_kwargs: Any) -> Any:
        observed.append(command)
        return verifier.subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(verifier.subprocess, "run", successful_ancestry)

    assert verifier.default_ancestry_probe(tmp_path, "a" * 40, "b" * 40)
    assert observed == [
        verifier._hardened_git_argv(  # noqa: SLF001
            git,
            tmp_path,
            "merge-base",
            "--is-ancestor",
            "a" * 40,
            "b" * 40,
        )
    ]


def test_published_structural_validation_resolves_only_trusted_git(
    monkeypatch: Any, tmp_path: Path
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    receipt["repository"]["root"] = verifier.CANONICAL_REPOSITORY
    refresh_payload_digest(receipt)
    receipt_path = root / verifier.RECEIPT_REL
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    source = receipt["repository"]["git_start"]["head"]
    receipt_commit = "b" * 40
    inventory = verifier.discover_inventory(root)
    parents = {
        verifier.GENERATION_ONE_SOURCE_COMMIT: (verifier.GENERATION_ONE_SOURCE_PARENT,),
        verifier.GENERATION_ONE_RECEIPT_COMMIT: (verifier.GENERATION_ONE_SOURCE_COMMIT,),
        verifier.GENERATION_TWO_SOURCE_COMMIT: (verifier.GENERATION_TWO_SOURCE_PARENT,),
        verifier.GENERATION_TWO_RECEIPT_COMMIT: (verifier.GENERATION_TWO_SOURCE_COMMIT,),
        verifier.GENERATION_TWO_STATE_COMMIT: (verifier.GENERATION_TWO_RECEIPT_COMMIT,),
        verifier.GENERATION_TWO_BATON_COMMIT: (verifier.GENERATION_TWO_STATE_COMMIT,),
        verifier.GENERATION_THREE_SOURCE_COMMIT: (verifier.GENERATION_THREE_SOURCE_PARENT,),
        verifier.GENERATION_THREE_RECEIPT_COMMIT: (verifier.GENERATION_THREE_SOURCE_COMMIT,),
        verifier.GENERATION_THREE_STATE_COMMIT: (verifier.GENERATION_THREE_RECEIPT_COMMIT,),
        verifier.GENERATION_THREE_BATON_COMMIT: (verifier.GENERATION_THREE_STATE_COMMIT,),
        verifier.GENERATION_FOUR_SOURCE_COMMIT: (verifier.GENERATION_FOUR_SOURCE_PARENT,),
        verifier.GENERATION_FOUR_RECEIPT_COMMIT: (verifier.GENERATION_FOUR_SOURCE_COMMIT,),
        verifier.GENERATION_FOUR_STATE_COMMIT: (verifier.GENERATION_FOUR_RECEIPT_COMMIT,),
        verifier.GENERATION_FOUR_BATON_COMMIT: (verifier.GENERATION_FOUR_STATE_COMMIT,),
        verifier.GENERATION_FIVE_SOURCE_COMMIT: (verifier.GENERATION_FIVE_SOURCE_PARENT,),
        verifier.GENERATION_FIVE_RECEIPT_COMMIT: (verifier.GENERATION_FIVE_SOURCE_COMMIT,),
        verifier.GENERATION_SIX_SOURCE_COMMIT: (verifier.GENERATION_SIX_SOURCE_PARENT,),
        verifier.GENERATION_SIX_RECEIPT_COMMIT: (verifier.GENERATION_SIX_SOURCE_COMMIT,),
        verifier.GENERATION_SIX_STATE_COMMIT: (verifier.GENERATION_SIX_RECEIPT_COMMIT,),
        verifier.GENERATION_SIX_BATON_COMMIT: (verifier.GENERATION_SIX_STATE_COMMIT,),
        verifier.GENERATION_SEVEN_SOURCE_COMMIT: (verifier.GENERATION_SEVEN_SOURCE_PARENT,),
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT: (verifier.GENERATION_SEVEN_SOURCE_COMMIT,),
        verifier.GENERATION_SEVEN_STATE_COMMIT: (verifier.GENERATION_SEVEN_RECEIPT_COMMIT,),
        verifier.GENERATION_SEVEN_BATON_COMMIT: (verifier.GENERATION_SEVEN_STATE_COMMIT,),
        verifier.GENERATION_EIGHT_SOURCE_COMMIT: (verifier.GENERATION_EIGHT_SOURCE_PARENT,),
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT: (verifier.GENERATION_EIGHT_SOURCE_COMMIT,),
        verifier.GENERATION_EIGHT_STATE_COMMIT: (verifier.GENERATION_EIGHT_RECEIPT_COMMIT,),
        verifier.GENERATION_EIGHT_BATON_COMMIT: (verifier.GENERATION_EIGHT_STATE_COMMIT,),
        verifier.GENERATION_NINE_SOURCE_COMMIT: (verifier.GENERATION_NINE_SOURCE_PARENT,),
        verifier.GENERATION_NINE_RECEIPT_COMMIT: (verifier.GENERATION_NINE_SOURCE_COMMIT,),
        verifier.GENERATION_NINE_STATE_COMMIT: (verifier.GENERATION_NINE_RECEIPT_COMMIT,),
        verifier.GENERATION_NINE_BATON_COMMIT: (verifier.GENERATION_NINE_STATE_COMMIT,),
        verifier.GENERATION_TEN_SOURCE_COMMIT: (verifier.GENERATION_TEN_SOURCE_PARENT,),
        verifier.GENERATION_TEN_RECEIPT_COMMIT: (verifier.GENERATION_TEN_SOURCE_COMMIT,),
        verifier.GENERATION_TEN_STATE_COMMIT: (verifier.GENERATION_TEN_RECEIPT_COMMIT,),
        verifier.GENERATION_TEN_BATON_COMMIT: (verifier.GENERATION_TEN_STATE_COMMIT,),
        verifier.GENERATION_ELEVEN_SOURCE_COMMIT: (verifier.GENERATION_ELEVEN_SOURCE_PARENT,),
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT: (verifier.GENERATION_ELEVEN_SOURCE_COMMIT,),
        verifier.GENERATION_ELEVEN_STATE_COMMIT: (verifier.GENERATION_ELEVEN_RECEIPT_COMMIT,),
        verifier.GENERATION_ELEVEN_BATON_COMMIT: (verifier.GENERATION_ELEVEN_STATE_COMMIT,),
        verifier.GENERATION_TWELVE_SOURCE_COMMIT: (verifier.GENERATION_TWELVE_SOURCE_PARENT,),
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT: (verifier.GENERATION_TWELVE_SOURCE_COMMIT,),
        verifier.GENERATION_TWELVE_STATE_COMMIT: (verifier.GENERATION_TWELVE_RECEIPT_COMMIT,),
        verifier.GENERATION_TWELVE_BATON_COMMIT: (verifier.GENERATION_TWELVE_STATE_COMMIT,),
        verifier.GENERATION_THIRTEEN_SOURCE_COMMIT: (verifier.GENERATION_THIRTEEN_SOURCE_PARENT,),
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT: (verifier.GENERATION_THIRTEEN_SOURCE_COMMIT,),
        verifier.GENERATION_THIRTEEN_STATE_COMMIT: (verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT,),
        verifier.GENERATION_THIRTEEN_BATON_COMMIT: (verifier.GENERATION_THIRTEEN_STATE_COMMIT,),
        verifier.GENERATION_FOURTEEN_SOURCE_COMMIT: (verifier.GENERATION_FOURTEEN_SOURCE_PARENT,),
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT: (verifier.GENERATION_FOURTEEN_SOURCE_COMMIT,),
        verifier.GENERATION_FOURTEEN_STATE_COMMIT: (verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT,),
        verifier.GENERATION_FOURTEEN_BATON_COMMIT: (verifier.GENERATION_FOURTEEN_STATE_COMMIT,),
        verifier.GENERATION_FIFTEEN_SOURCE_COMMIT: (
            verifier.GENERATION_FIFTEEN_SOURCE_PARENT,
        ),
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT: (
            verifier.GENERATION_FIFTEEN_SOURCE_COMMIT,
        ),
        verifier.GENERATION_FIFTEEN_STATE_COMMIT: (
            verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT,
        ),
        verifier.GENERATION_FIFTEEN_BATON_COMMIT: (
            verifier.GENERATION_FIFTEEN_STATE_COMMIT,
        ),
        source: (verifier.RECOVERY_SOURCE_PARENT,),
        receipt_commit: (source,),
    }
    paths = {
        verifier.GENERATION_ONE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_ONE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_ONE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWO_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TWO_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TWO_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWO_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TWO_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_THREE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_THREE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_THREE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_THREE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_THREE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FOUR_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FOUR_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FOUR_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FOUR_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FOUR_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FIVE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FIVE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FIVE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SIX_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_SIX_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_SIX_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SIX_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_SIX_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_SEVEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_SEVEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SEVEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_SEVEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_EIGHT_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_EIGHT_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_EIGHT_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_EIGHT_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_NINE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_NINE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_NINE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_NINE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_NINE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_TEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_ELEVEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_ELEVEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_ELEVEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_ELEVEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_TWELVE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TWELVE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWELVE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TWELVE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_THIRTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_THIRTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_THIRTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FOURTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FOURTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FOURTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FIFTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FIFTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FIFTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        source: tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
        receipt_commit: (verifier.RECEIPT_REL,),
    }

    monkeypatch.setattr(
        verifier,
        "_git_commit_row",
        lambda _root, commit: (parents[commit], paths[commit]),
    )
    monkeypatch.setattr(
        verifier,
        "_source_inventory_from_tree",
        lambda _root, _commit: inventory,
    )

    def fake_git_file(_root: Path, commit: str, relative: str) -> bytes:
        if commit == receipt_commit:
            assert relative == verifier.RECEIPT_REL
            return receipt_path.read_bytes()
        if relative == "MISSION_STATE.json" and commit in {
            source,
            verifier.GENERATION_FIFTEEN_BATON_COMMIT,
        }:
            return (root / relative).read_bytes()
        assert commit == source
        return (root / relative).read_bytes()

    monkeypatch.setattr(verifier, "_git_file_bytes", fake_git_file)
    monkeypatch.setattr(
        verifier,
        "_linear_publication_chain",
        lambda _root, _ancestor, _descendant: [],
    )

    which_calls: list[str] = []

    def only_git(name: str) -> str:
        which_calls.append(name)
        if name != "git":
            raise AssertionError(f"structural validation resolved non-Git tool: {name}")
        return "/usr/bin/git"

    monkeypatch.setattr(verifier.shutil, "which", only_git)
    monkeypatch.setattr(
        verifier,
        "resolve_toolchain",
        lambda: (_ for _ in ()).throw(AssertionError("full toolchain resolution is forbidden")),
    )
    receipt_history = (
        receipt_commit,
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT,
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT,
        verifier.GENERATION_TEN_RECEIPT_COMMIT,
        verifier.GENERATION_NINE_RECEIPT_COMMIT,
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT,
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT,
        verifier.GENERATION_SIX_RECEIPT_COMMIT,
        verifier.GENERATION_FIVE_RECEIPT_COMMIT,
        verifier.GENERATION_FOUR_RECEIPT_COMMIT,
        verifier.GENERATION_THREE_RECEIPT_COMMIT,
        verifier.GENERATION_TWO_RECEIPT_COMMIT,
        verifier.GENERATION_ONE_RECEIPT_COMMIT,
    )

    def git_only_run(command: tuple[str, ...], **_kwargs: Any) -> Any:
        if command == ("/usr/bin/git", "--version"):
            return verifier.subprocess.CompletedProcess(command, 0, b"git version fixture\n", b"")
        if command[-4:] == ("log", "--format=%H", "--", verifier.RECEIPT_REL):
            stdout = ("\n".join(receipt_history) + "\n").encode()
            return verifier.subprocess.CompletedProcess(command, 0, stdout, b"")
        raise AssertionError(f"unexpected structural Git command: {command}")

    monkeypatch.setattr(verifier.subprocess, "run", git_only_run)
    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001

    current_git = verifier.GitState(
        head=receipt_commit,
        dirty_entries=(),
        porcelain_sha256=hashlib.sha256(b"").hexdigest(),
        upstream_head=receipt_commit,
        parents=(source,),
        commit_paths=(verifier.RECEIPT_REL,),
    )
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: current_git,
        ancestry_probe=stable_ancestry,
    )

    verifier._resolve_git_cached.cache_clear()  # noqa: SLF001
    assert errors == []
    assert which_calls == ["git"]


def test_sanitized_environment_drops_inherited_pytest_controls(monkeypatch: Any) -> None:
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    environment = verifier._sanitized_environment(fake_toolchain())  # noqa: SLF001

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
            parents=(verifier.RECOVERY_SOURCE_PARENT,),
            commit_paths=(verifier.REQUIRED_TEST_FILES[0],),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=unpublishable_git,
        toolchain_resolver=fake_toolchain,
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


def test_source_verification_rejects_wrong_recovery_parent(tmp_path: Path) -> None:
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
        toolchain_resolver=fake_toolchain,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert runner.commands == []
    assert "SOURCE_PARENT" in problem_codes(receipt)


def test_generation_one_source_cannot_mint_a_second_generation_one_receipt(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)

    def generation_one_git(_root: Path, _paths: tuple[str, ...]) -> Any:
        return verifier.GitState(
            head=verifier.GENERATION_ONE_SOURCE_COMMIT,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            branch="master",
            upstream="origin/master",
            upstream_head=verifier.GENERATION_ONE_SOURCE_COMMIT,
            parents=(verifier.GENERATION_ONE_SOURCE_PARENT,),
            commit_paths=tuple(sorted(verifier.GENERATION_ONE_SOURCE_COMMIT_PATHS)),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=generation_one_git,
        toolchain_resolver=fake_toolchain,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert runner.commands == []
    assert {"SOURCE_PARENT", "SOURCE_COMMIT_SCOPE"} <= problem_codes(receipt)
    assert receipt["publication"] == verifier.EXPECTED_RECOVERY_PUBLICATION


def test_receipt_validators_reject_missing_or_forged_generation_sixteen_publication(
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)

    for publication in (
        None,
        {
            **verifier.EXPECTED_RECOVERY_PUBLICATION,
            "supersedes_receipt_commit": "f" * 40,
        },
        {
            **verifier.EXPECTED_RECOVERY_PUBLICATION,
            "reason_code": "UNRECORDED_REASON",
        },
        {
            **verifier.EXPECTED_RECOVERY_PUBLICATION,
            "generation": 15.0,
        },
    ):
        forged = copy.deepcopy(receipt)
        if publication is None:
            forged.pop("publication")
        else:
            forged["publication"] = publication
        refresh_payload_digest(forged)

        errors = replay_validate(forged, root, git_probe=stable_git)
        structural_errors = verifier.validate_published_receipt_structure(
            forged,
            root,
        )

        assert "generation-sixteen publication block mismatch" in errors
        assert "generation-sixteen publication block mismatch" in structural_errors


@pytest.mark.parametrize(
    ("field", "forged_value", "expected_error"),
    (
        (
            "parents",
            [verifier.GENERATION_ONE_SOURCE_PARENT],
            "claimed source parent mismatch at start",
        ),
        (
            "commit_paths",
            sorted(verifier.GENERATION_ONE_SOURCE_COMMIT_PATHS),
            "claimed source commit scope mismatch at start",
        ),
    ),
)
def test_replay_rejects_generation_one_or_nonexact_recovery_source_claims(
    field: str,
    forged_value: list[str],
    expected_error: str,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    for label in ("git_start", "git_end"):
        forged["repository"][label][field] = forged_value
    refresh_payload_digest(forged)

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert expected_error in errors


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


@pytest.mark.parametrize(
    "relative",
    [
        "tests/test_handoff_generator.py",
        "scripts/make_handoff.py",
    ],
)
def test_missing_frozen_handoff_surface_is_initialization_failure(
    tmp_path: Path,
    relative: str,
) -> None:
    root = make_repo(tmp_path)
    (root / relative).unlink()

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
            parents=(verifier.RECOVERY_SOURCE_PARENT,),
            commit_paths=tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=drifting_git,
        toolchain_resolver=fake_toolchain,
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
            parents=(verifier.RECOVERY_SOURCE_PARENT,),
            commit_paths=tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
        )

    runner = RecordingRunner()
    receipt = verifier.run_verification(
        root,
        runner=runner,
        git_probe=dirty_git,
        toolchain_resolver=fake_toolchain,
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


def test_published_structure_binds_exact_recovery_chain_and_rejects_hostile_history(
    monkeypatch: Any, tmp_path: Path
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    assert str(root) != verifier.CANONICAL_REPOSITORY
    receipt["repository"]["root"] = verifier.CANONICAL_REPOSITORY
    refresh_payload_digest(receipt)
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
        verifier.GENERATION_ONE_SOURCE_COMMIT: (verifier.GENERATION_ONE_SOURCE_PARENT,),
        verifier.GENERATION_ONE_RECEIPT_COMMIT: (verifier.GENERATION_ONE_SOURCE_COMMIT,),
        verifier.GENERATION_TWO_SOURCE_COMMIT: (verifier.GENERATION_TWO_SOURCE_PARENT,),
        verifier.GENERATION_TWO_RECEIPT_COMMIT: (verifier.GENERATION_TWO_SOURCE_COMMIT,),
        verifier.GENERATION_TWO_STATE_COMMIT: (verifier.GENERATION_TWO_RECEIPT_COMMIT,),
        verifier.GENERATION_TWO_BATON_COMMIT: (verifier.GENERATION_TWO_STATE_COMMIT,),
        verifier.GENERATION_THREE_SOURCE_COMMIT: (verifier.GENERATION_THREE_SOURCE_PARENT,),
        verifier.GENERATION_THREE_RECEIPT_COMMIT: (verifier.GENERATION_THREE_SOURCE_COMMIT,),
        verifier.GENERATION_THREE_STATE_COMMIT: (verifier.GENERATION_THREE_RECEIPT_COMMIT,),
        verifier.GENERATION_THREE_BATON_COMMIT: (verifier.GENERATION_THREE_STATE_COMMIT,),
        verifier.GENERATION_FOUR_SOURCE_COMMIT: (verifier.GENERATION_FOUR_SOURCE_PARENT,),
        verifier.GENERATION_FOUR_RECEIPT_COMMIT: (verifier.GENERATION_FOUR_SOURCE_COMMIT,),
        verifier.GENERATION_FOUR_STATE_COMMIT: (verifier.GENERATION_FOUR_RECEIPT_COMMIT,),
        verifier.GENERATION_FOUR_BATON_COMMIT: (verifier.GENERATION_FOUR_STATE_COMMIT,),
        verifier.GENERATION_FIVE_SOURCE_COMMIT: (verifier.GENERATION_FIVE_SOURCE_PARENT,),
        verifier.GENERATION_FIVE_RECEIPT_COMMIT: (verifier.GENERATION_FIVE_SOURCE_COMMIT,),
        verifier.GENERATION_SIX_SOURCE_COMMIT: (verifier.GENERATION_SIX_SOURCE_PARENT,),
        verifier.GENERATION_SIX_RECEIPT_COMMIT: (verifier.GENERATION_SIX_SOURCE_COMMIT,),
        verifier.GENERATION_SIX_STATE_COMMIT: (verifier.GENERATION_SIX_RECEIPT_COMMIT,),
        verifier.GENERATION_SIX_BATON_COMMIT: (verifier.GENERATION_SIX_STATE_COMMIT,),
        verifier.GENERATION_SEVEN_SOURCE_COMMIT: (verifier.GENERATION_SEVEN_SOURCE_PARENT,),
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT: (verifier.GENERATION_SEVEN_SOURCE_COMMIT,),
        verifier.GENERATION_SEVEN_STATE_COMMIT: (verifier.GENERATION_SEVEN_RECEIPT_COMMIT,),
        verifier.GENERATION_SEVEN_BATON_COMMIT: (verifier.GENERATION_SEVEN_STATE_COMMIT,),
        verifier.GENERATION_EIGHT_SOURCE_COMMIT: (verifier.GENERATION_EIGHT_SOURCE_PARENT,),
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT: (verifier.GENERATION_EIGHT_SOURCE_COMMIT,),
        verifier.GENERATION_EIGHT_STATE_COMMIT: (verifier.GENERATION_EIGHT_RECEIPT_COMMIT,),
        verifier.GENERATION_EIGHT_BATON_COMMIT: (verifier.GENERATION_EIGHT_STATE_COMMIT,),
        verifier.GENERATION_NINE_SOURCE_COMMIT: (verifier.GENERATION_NINE_SOURCE_PARENT,),
        verifier.GENERATION_NINE_RECEIPT_COMMIT: (verifier.GENERATION_NINE_SOURCE_COMMIT,),
        verifier.GENERATION_NINE_STATE_COMMIT: (verifier.GENERATION_NINE_RECEIPT_COMMIT,),
        verifier.GENERATION_NINE_BATON_COMMIT: (verifier.GENERATION_NINE_STATE_COMMIT,),
        verifier.GENERATION_TEN_SOURCE_COMMIT: (verifier.GENERATION_TEN_SOURCE_PARENT,),
        verifier.GENERATION_TEN_RECEIPT_COMMIT: (verifier.GENERATION_TEN_SOURCE_COMMIT,),
        verifier.GENERATION_TEN_STATE_COMMIT: (verifier.GENERATION_TEN_RECEIPT_COMMIT,),
        verifier.GENERATION_TEN_BATON_COMMIT: (verifier.GENERATION_TEN_STATE_COMMIT,),
        verifier.GENERATION_ELEVEN_SOURCE_COMMIT: (verifier.GENERATION_ELEVEN_SOURCE_PARENT,),
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT: (verifier.GENERATION_ELEVEN_SOURCE_COMMIT,),
        verifier.GENERATION_ELEVEN_STATE_COMMIT: (verifier.GENERATION_ELEVEN_RECEIPT_COMMIT,),
        verifier.GENERATION_ELEVEN_BATON_COMMIT: (verifier.GENERATION_ELEVEN_STATE_COMMIT,),
        verifier.GENERATION_TWELVE_SOURCE_COMMIT: (verifier.GENERATION_TWELVE_SOURCE_PARENT,),
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT: (verifier.GENERATION_TWELVE_SOURCE_COMMIT,),
        verifier.GENERATION_TWELVE_STATE_COMMIT: (verifier.GENERATION_TWELVE_RECEIPT_COMMIT,),
        verifier.GENERATION_TWELVE_BATON_COMMIT: (verifier.GENERATION_TWELVE_STATE_COMMIT,),
        verifier.GENERATION_THIRTEEN_SOURCE_COMMIT: (verifier.GENERATION_THIRTEEN_SOURCE_PARENT,),
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT: (verifier.GENERATION_THIRTEEN_SOURCE_COMMIT,),
        verifier.GENERATION_THIRTEEN_STATE_COMMIT: (verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT,),
        verifier.GENERATION_THIRTEEN_BATON_COMMIT: (verifier.GENERATION_THIRTEEN_STATE_COMMIT,),
        verifier.GENERATION_FOURTEEN_SOURCE_COMMIT: (verifier.GENERATION_FOURTEEN_SOURCE_PARENT,),
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT: (verifier.GENERATION_FOURTEEN_SOURCE_COMMIT,),
        verifier.GENERATION_FOURTEEN_STATE_COMMIT: (verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT,),
        verifier.GENERATION_FOURTEEN_BATON_COMMIT: (verifier.GENERATION_FOURTEEN_STATE_COMMIT,),
        verifier.GENERATION_FIFTEEN_SOURCE_COMMIT: (
            verifier.GENERATION_FIFTEEN_SOURCE_PARENT,
        ),
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT: (
            verifier.GENERATION_FIFTEEN_SOURCE_COMMIT,
        ),
        verifier.GENERATION_FIFTEEN_STATE_COMMIT: (
            verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT,
        ),
        verifier.GENERATION_FIFTEEN_BATON_COMMIT: (
            verifier.GENERATION_FIFTEEN_STATE_COMMIT,
        ),
        source: (verifier.RECOVERY_SOURCE_PARENT,),
        receipt_commit: (source,),
        state_commit: (receipt_commit,),
        baton_commit: (state_commit,),
        later_commit: (baton_commit,),
    }
    paths = {
        verifier.GENERATION_ONE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_ONE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_ONE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWO_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TWO_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TWO_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWO_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TWO_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_THREE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_THREE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_THREE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_THREE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_THREE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FOUR_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FOUR_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FOUR_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FOUR_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FOUR_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FIVE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FIVE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FIVE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SIX_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_SIX_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_SIX_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SIX_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_SIX_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_SEVEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_SEVEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_SEVEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_SEVEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_EIGHT_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_EIGHT_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_EIGHT_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_EIGHT_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_NINE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_NINE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_NINE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_NINE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_NINE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_TEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_ELEVEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_ELEVEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_ELEVEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_ELEVEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_TWELVE_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_TWELVE_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_TWELVE_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_TWELVE_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_THIRTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_THIRTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_THIRTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FOURTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FOURTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FOURTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        verifier.GENERATION_FIFTEEN_SOURCE_COMMIT: tuple(
            sorted(verifier.GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS)
        ),
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT: (verifier.RECEIPT_REL,),
        verifier.GENERATION_FIFTEEN_STATE_COMMIT: ("MISSION_STATE.json",),
        verifier.GENERATION_FIFTEEN_BATON_COMMIT: ("CONTINUITY.md", "HANDOFF.md"),
        source: tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
        receipt_commit: (verifier.RECEIPT_REL,),
        state_commit: ("MISSION_STATE.json",),
        baton_commit: ("CONTINUITY.md", "HANDOFF.md"),
        later_commit: (verifier.REQUIRED_PYTHON_TOOL_FILES[0],),
    }
    receipt_history = [
        receipt_commit,
        verifier.GENERATION_FIFTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_THIRTEEN_RECEIPT_COMMIT,
        verifier.GENERATION_TWELVE_RECEIPT_COMMIT,
        verifier.GENERATION_ELEVEN_RECEIPT_COMMIT,
        verifier.GENERATION_TEN_RECEIPT_COMMIT,
        verifier.GENERATION_NINE_RECEIPT_COMMIT,
        verifier.GENERATION_EIGHT_RECEIPT_COMMIT,
        verifier.GENERATION_SEVEN_RECEIPT_COMMIT,
        verifier.GENERATION_SIX_RECEIPT_COMMIT,
        verifier.GENERATION_FIVE_RECEIPT_COMMIT,
        verifier.GENERATION_FOUR_RECEIPT_COMMIT,
        verifier.GENERATION_THREE_RECEIPT_COMMIT,
        verifier.GENERATION_TWO_RECEIPT_COMMIT,
        verifier.GENERATION_ONE_RECEIPT_COMMIT,
    ]
    accepted_state_bytes = (root / "MISSION_STATE.json").read_bytes()
    ci_state = {"phase": "CI_HARDENING_REQUIRED", "run_state": "UNKNOWN"}
    ci_state_bytes = verifier._canonical_json(ci_state)  # noqa: SLF001
    monkeypatch.setattr(
        verifier,
        "_expected_ci_hardening_state",
        lambda _root: ci_state,
    )

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
            if relative == "MISSION_STATE.json":
                if commit in {source, verifier.GENERATION_FIFTEEN_BATON_COMMIT}:
                    return accepted_state_bytes
                if commit == state_commit:
                    return ci_state_bytes
            assert commit == source
            return (root / relative).read_bytes()
        if argv[0] == "log":
            return ("\n".join(receipt_history) + "\n").encode()
        raise AssertionError(f"unexpected Git command: {argv}")

    monkeypatch.setattr(verifier, "_git_bytes", fake_git)

    def publication_git(head: str, origin_head: str | None = None) -> Any:
        return verifier.GitState(
            head=head,
            dirty_entries=(),
            porcelain_sha256=hashlib.sha256(b"").hexdigest(),
            upstream_head=head if origin_head is None else origin_head,
            parents=parents[head],
            commit_paths=paths[head],
        )

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(state_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any(
        "origin/master is not exact F16, R16, or B16 for this stage" in error
        for error in errors
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
        git_probe=lambda _root, _paths: publication_git(baton_commit, ""),
        ancestry_probe=stable_ancestry,
    )
    assert any("origin/master commit is malformed or missing" in error for error in errors)

    detached_origin = "f" * 40

    def receipt_missing_from_origin(_root: Path, ancestor: str, descendant: str) -> bool:
        return not (ancestor == receipt_commit and descendant == detached_origin)

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit, detached_origin),
        ancestry_probe=receipt_missing_from_origin,
    )
    assert any(
        "origin/master is not exact F16, R16, or B16 for this stage" in error
        for error in errors
    )

    wrong_root = copy.deepcopy(receipt)
    wrong_root["repository"]["root"] = str(root)
    refresh_payload_digest(wrong_root)
    receipt_path.write_text(
        json.dumps(wrong_root, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    errors = verifier.validate_published_receipt_structure(
        wrong_root,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("canonical repository identity is malformed" in error for error in errors)
    receipt_path.write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(later_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("commits beyond exact T16 and B16" in error for error in errors)

    receipt_history.pop()
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("receipt history is not exact generation-sixteen" in error for error in errors)
    receipt_history.append(verifier.GENERATION_ONE_RECEIPT_COMMIT)

    paths[verifier.GENERATION_ONE_SOURCE_COMMIT] = ("MISSION_STATE.json",)
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("generation-one source topology or path scope changed" in error for error in errors)
    paths[verifier.GENERATION_ONE_SOURCE_COMMIT] = tuple(
        sorted(verifier.GENERATION_ONE_SOURCE_COMMIT_PATHS)
    )

    paths[verifier.GENERATION_ONE_RECEIPT_COMMIT] = (
        verifier.RECEIPT_REL,
        "unexpected.json",
    )
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("generation-one receipt topology or path scope changed" in error for error in errors)
    paths[verifier.GENERATION_ONE_RECEIPT_COMMIT] = (verifier.RECEIPT_REL,)

    paths[verifier.GENERATION_THREE_SOURCE_COMMIT] = ("MISSION_STATE.json",)
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any(
        "generation-three source topology or path scope changed" in error for error in errors
    )
    paths[verifier.GENERATION_THREE_SOURCE_COMMIT] = tuple(
        sorted(verifier.GENERATION_THREE_SOURCE_COMMIT_PATHS)
    )

    paths[verifier.GENERATION_FOURTEEN_SOURCE_COMMIT] = ("MISSION_STATE.json",)
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any(
        "generation-fourteen source topology or path scope changed" in error for error in errors
    )
    paths[verifier.GENERATION_FOURTEEN_SOURCE_COMMIT] = tuple(
        sorted(verifier.GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS)
    )

    for transition_commit, transition_name in (
        (verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT, "receipt"),
        (verifier.GENERATION_FOURTEEN_STATE_COMMIT, "state"),
        (verifier.GENERATION_FOURTEEN_BATON_COMMIT, "baton"),
    ):
        expected_error = f"generation-fourteen {transition_name} topology or path scope changed"
        expected_parents = parents[transition_commit]
        parents[transition_commit] = ("f" * 40,)
        errors = verifier.validate_published_receipt_structure(
            receipt,
            root,
            git_probe=lambda _root, _paths: publication_git(baton_commit),
            ancestry_probe=stable_ancestry,
        )
        assert any(expected_error in error for error in errors)
        parents[transition_commit] = expected_parents

        expected_paths = paths[transition_commit]
        paths[transition_commit] = (
            *expected_paths,
            "unexpected-generation-fourteen.txt",
        )
        errors = verifier.validate_published_receipt_structure(
            receipt,
            root,
            git_probe=lambda _root, _paths: publication_git(baton_commit),
            ancestry_probe=stable_ancestry,
        )
        assert any(expected_error in error for error in errors)
        paths[transition_commit] = expected_paths

    parents[source] = ("f" * 40,)
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any(
        "actual generation-sixteen source topology or path scope is wrong" in error
        for error in errors
    )


def test_post_baton_chain_accepts_only_exact_evidence_and_atomic_launch_order() -> None:
    exp = verifier.EXPERIMENT_REL
    exact = [
        (
            "1" * 40,
            (
                f"{exp}/host_packet_manifest.json",
                f"{exp}/host_preparation_receipt.json",
            ),
        ),
        ("2" * 40, (f"{exp}/env_receipts.json",)),
        ("3" * 40, (f"{exp}/launch_manifest.json",)),
        (
            "4" * 40,
            verifier.SMOKE_EVIDENCE_PATHS,
        ),
        ("5" * 40, ("MISSION_STATE.json",)),
        ("6" * 40, (f"{exp}/launch_manifest.json",)),
        (
            "7" * 40,
            (
                "CONTINUITY.md",
                "HANDOFF.md",
                f"{exp}/launch_activation_receipt.json",
            ),
        ),
    ]

    for prefix_length in range(5):
        verifier._validate_post_baton_chain(exact[:prefix_length])  # noqa: SLF001
    verifier._validate_post_baton_chain(exact)  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="violates evidence order"):
        verifier._validate_post_baton_chain([exact[1]])  # noqa: SLF001
    # A and A/F are deterministic construction prefixes, never launch authority by themselves.
    verifier._validate_post_baton_chain(exact[:5])  # noqa: SLF001
    verifier._validate_post_baton_chain(exact[:6])  # noqa: SLF001
    with pytest.raises(verifier.VerificationError, match="wrong scope"):
        hostile = [*exact[:-1], ("7" * 40, ("CONTINUITY.md", "HANDOFF.md"))]
        verifier._validate_post_baton_chain(hostile)  # noqa: SLF001

    smoke_index = 3
    for hostile_paths in (
        verifier.SMOKE_EVIDENCE_PATHS[:-1],
        tuple(sorted((*verifier.SMOKE_EVIDENCE_PATHS, f"{exp}/smoke-evidence/extra.txt"))),
        (f"{exp}/smoke-evidence/arbitrary-prefixed-path.txt",),
    ):
        hostile = list(exact)
        hostile[smoke_index] = ("4" * 40, hostile_paths)
        with pytest.raises(verifier.VerificationError, match="exact smoke-evidence freeze"):
            verifier._validate_post_baton_chain(hostile)  # noqa: SLF001


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
        toolchain_resolver=fake_toolchain,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    encoded = json.dumps(receipt)
    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert "super-secret-command-output" not in encoded
    assert receipt["commands"][0]["return_code"] == 125
    assert receipt["commands"][0]["runner_error_type"] == "RuntimeError"


@pytest.mark.parametrize("hostile_returncode", [False, 0.0, True, 1.0])
def test_runner_returncode_rejects_bool_and_float_aliases_before_receipt_generation(
    tmp_path: Path,
    hostile_returncode: object,
) -> None:
    root = make_repo(tmp_path)

    def hostile_runner(_command: tuple[str, ...], _cwd: Path) -> Any:
        return verifier.RawCommandResult(
            returncode=hostile_returncode,
            stdout=b"",
            stderr=b"",
        )

    receipt = verifier.run_verification(
        root,
        runner=hostile_runner,
        git_probe=stable_git,
        toolchain_resolver=fake_toolchain,
        wall_clock_ns=SequenceClock(1, 2),
        monotonic_clock_ns=SequenceClock(1, 2),
    )

    assert receipt["verdict"] == verifier.FAIL_VERDICT
    assert receipt["commands"][0]["return_code"] == 125
    assert receipt["commands"][0]["runner_error_type"] == "TypeError"
    assert "COMMAND_FAILED" in problem_codes(receipt)


def test_atomic_writer_round_trips_and_refuses_output_symlink(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    output = root / verifier.EXPERIMENT_REL / "tooling_verification_receipt.json"
    receipt = verifier.run_and_write_verification(
        output,
        root,
        runner=RecordingRunner(),
        git_probe=stable_git,
        toolchain_resolver=fake_toolchain,
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
            toolchain_resolver=fake_toolchain,
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


@pytest.mark.parametrize(
    ("target", "forged_value", "expected_error"),
    (
        ("problem_count", False, "problem_count is not exact integer zero"),
        ("problem_count", 0.0, "problem_count is not exact integer zero"),
        ("return_code", False, "command_0 return_code is not exact integer zero"),
        ("return_code", 0.0, "command_0 return_code is not exact integer zero"),
    ),
)
def test_green_integer_claims_reject_bool_and_equal_valued_float_in_both_validators(
    target: str,
    forged_value: object,
    expected_error: str,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    if target == "problem_count":
        forged[target] = forged_value
    else:
        forged["commands"][0][target] = forged_value
    refresh_payload_digest(forged)

    replay_errors = replay_validate(forged, root, git_probe=stable_git)
    structural_errors = verifier.validate_published_receipt_structure(forged, root)

    assert expected_error in replay_errors
    assert expected_error in structural_errors


@pytest.mark.parametrize(
    ("target", "expected_error"),
    (
        ("repository", "repository field set mismatch"),
        ("git_start", "repository git_start field set mismatch"),
        ("toolchain", "toolchain row field set mismatch: pytest"),
        ("file", "file binding row field set mismatch:"),
        ("execution_identity", "file execution_identity field set mismatch:"),
        ("command", "command_0 field set mismatch"),
        ("timing", "timing field set mismatch"),
    ),
)
def test_nested_receipt_field_sets_are_exact_in_both_validators(
    target: str,
    expected_error: str,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    first_file = next(iter(forged["files"]))
    targets = {
        "repository": forged["repository"],
        "git_start": forged["repository"]["git_start"],
        "toolchain": forged["toolchain"]["pytest"],
        "file": forged["files"][first_file],
        "execution_identity": forged["files"][first_file]["execution_identity"],
        "command": forged["commands"][0],
        "timing": forged["timing"],
    }
    targets[target]["unregistered_claim"] = 0
    refresh_payload_digest(forged)

    replay_errors = replay_validate(forged, root, git_probe=stable_git)
    structural_errors = verifier.validate_published_receipt_structure(forged, root)

    assert any(expected_error in error for error in replay_errors)
    assert any(expected_error in error for error in structural_errors)


@pytest.mark.parametrize(
    ("target", "expected_error"),
    (
        ("repository_flag", "repository git_head_stable is not a JSON boolean"),
        ("toolchain_bytes", "toolchain bytes malformed: pytest"),
        ("file_inode", "file execution_identity inode malformed:"),
        ("stdout_bytes", "command_0 stdout byte count malformed"),
        ("stdout_digest", "command_0 stdout digest malformed"),
        (
            "stderr_binding",
            "command_0 stderr byte count and digest are inconsistent",
        ),
        ("wall_duration_ns", "wall_duration_ns malformed"),
    ),
)
def test_nested_receipt_scalar_metadata_is_typed_and_bound_in_both_validators(
    target: str,
    expected_error: str,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    first_file = next(iter(forged["files"]))
    if target == "repository_flag":
        forged["repository"]["git_head_stable"] = 1
    elif target == "toolchain_bytes":
        value = forged["toolchain"]["pytest"]["bytes"]
        forged["toolchain"]["pytest"]["bytes"] = float(value)
    elif target == "file_inode":
        value = forged["files"][first_file]["execution_identity"]["inode"]
        forged["files"][first_file]["execution_identity"]["inode"] = float(value)
    elif target == "stdout_bytes":
        value = forged["commands"][0]["stdout_bytes"]
        forged["commands"][0]["stdout_bytes"] = float(value)
    elif target == "stdout_digest":
        forged["commands"][0]["stdout_sha256"] = "A" * 64
    elif target == "stderr_binding":
        forged["commands"][0]["stderr_sha256"] = "0" * 64
    else:
        value = forged["timing"]["wall_duration_ns"]
        forged["timing"]["wall_duration_ns"] = float(value)
    refresh_payload_digest(forged)

    replay_errors = replay_validate(forged, root, git_probe=stable_git)
    structural_errors = verifier.validate_published_receipt_structure(forged, root)

    assert any(expected_error in error for error in replay_errors)
    assert any(expected_error in error for error in structural_errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        ("noncanonical_start", "timing started_at_utc is not canonical UTC"),
        ("reverse", "timing UTC timestamps are out of order"),
        (
            "inconsistent_duration",
            "timing wall duration is inconsistent with UTC timestamps",
        ),
    ),
)
def test_timing_claims_require_canonical_ordered_duration_consistency(
    mutation: str,
    expected_error: str,
    tmp_path: Path,
) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    timing = forged["timing"]
    if mutation == "noncanonical_start":
        timing["started_at_utc"] = timing["started_at_utc"].removesuffix("Z") + "+00:00"
    elif mutation == "reverse":
        timing["started_at_utc"], timing["finished_at_utc"] = (
            timing["finished_at_utc"],
            timing["started_at_utc"],
        )
    else:
        timing["wall_duration_ns"] += verifier.WALL_TIMESTAMP_ROUNDING_BUDGET_NS + 1
    refresh_payload_digest(forged)

    replay_errors = replay_validate(forged, root, git_probe=stable_git)
    structural_errors = verifier.validate_published_receipt_structure(forged, root)

    assert expected_error in replay_errors
    assert expected_error in structural_errors


def test_receipt_payload_digest_detects_structural_tampering(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    forged["problem_count"] = 0
    forged["timing"]["wall_duration_ns"] += 1

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert "receipt payload digest mismatch" in errors


def test_retained_generation_fourteen_receipt_passes_stricter_nested_shape() -> None:
    raw_receipt = subprocess.run(
        (
            "/usr/bin/git",
            "-C",
            str(REPO),
            "show",
            f"{verifier.GENERATION_FOURTEEN_RECEIPT_COMMIT}:{verifier.RECEIPT_REL}",
        ),
        cwd=REPO,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        env={
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": "/nonexistent/sentinel-r14-receipt-test",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        },
    ).stdout
    receipt = verifier._parse_receipt_json(  # noqa: SLF001
        raw_receipt
    )

    assert receipt["publication"]["generation"] == 14
    assert verifier._nested_receipt_shape_errors(receipt) == []  # noqa: SLF001


@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_receipt_root_field_set_is_exact_in_both_validators(tmp_path: Path, mutation: str) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    if mutation == "extra":
        forged["unregistered_root_claim"] = True
    else:
        forged.pop("timing")
    refresh_payload_digest(forged)

    replay_errors = replay_validate(forged, root, git_probe=stable_git)
    structural_errors = verifier.validate_published_receipt_structure(forged, root)

    assert "receipt root field set mismatch" in replay_errors
    assert "receipt root field set mismatch" in structural_errors


@pytest.mark.parametrize(
    ("payload", "problem"),
    [
        ('{"schema":"first","schema":"second"}', "duplicate receipt JSON key"),
        ('{"value":NaN}', "non-finite receipt JSON number"),
        ('{"value":Infinity}', "non-finite receipt JSON number"),
        ('{"value":-Infinity}', "non-finite receipt JSON number"),
    ],
)
def test_receipt_parser_rejects_duplicate_and_nonfinite_json(payload: str, problem: str) -> None:
    with pytest.raises(verifier.VerificationError, match=problem):
        verifier._parse_receipt_json(payload)  # noqa: SLF001


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema":"secret-one","schema":"secret-two"}',
        '{"secret-value":NaN}',
        "[]",
    ],
)
def test_verify_receipt_cli_fails_closed_without_disclosing_hostile_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: str,
) -> None:
    receipt_path = tmp_path / "hostile-receipt.json"
    receipt_path.write_text(payload, encoding="utf-8")

    return_code = verifier.main(["--verify-receipt", str(receipt_path)])
    captured = capsys.readouterr()

    assert return_code == 2
    assert captured.out.splitlines() == [verifier.FAIL_VERDICT, "problem_count=1"]
    assert captured.err == ""
    assert "secret" not in captured.out


def _fixture_git(repo: Path, *argv: str, environment: dict[str, str] | None = None) -> bytes:
    command_environment = dict(os.environ)
    command_environment.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Sentinel fixture",
            "GIT_AUTHOR_EMAIL": "sentinel@example.invalid",
            "GIT_COMMITTER_NAME": "Sentinel fixture",
            "GIT_COMMITTER_EMAIL": "sentinel@example.invalid",
            "GIT_AUTHOR_DATE": "2001-01-01T00:00:00+0000",
            "GIT_COMMITTER_DATE": "2001-01-01T00:00:00+0000",
        }
    )
    if environment is not None:
        command_environment.update(environment)
    completed = subprocess.run(
        ("git", "-C", str(repo), *argv),
        env=command_environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    assert completed.returncode == 0, (argv, completed.stderr.decode(errors="replace"))
    return completed.stdout


def _make_next_source_object_repo(tmp_path: Path) -> tuple[Path, str, str, Path]:
    repo = tmp_path / "binding-object-repo"
    repo.mkdir()
    _fixture_git(repo, "init", "-q")
    (repo / "base.txt").write_bytes(b"accepted baton\n")
    _fixture_git(repo, "add", "base.txt")
    _fixture_git(repo, "commit", "-q", "-m", "accepted B16 fixture")
    baton = _fixture_git(repo, "rev-parse", "HEAD").decode().strip()

    (repo / "base.txt").write_bytes(b"candidate source\n")
    candidate_dir = repo / "scripts/ci"
    candidate_dir.mkdir(parents=True)
    tripwire = tmp_path / "candidate-executed"
    (candidate_dir / "hashlib.py").write_text(
        f"from pathlib import Path\nPath({str(tripwire)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    launcher = candidate_dir / "candidate.sh"
    launcher.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    launcher.chmod(0o755)
    _fixture_git(
        repo,
        "add",
        "base.txt",
        "scripts/ci/hashlib.py",
        "scripts/ci/candidate.sh",
    )
    _fixture_git(repo, "commit", "-q", "-m", "candidate F17 fixture")
    candidate = _fixture_git(repo, "rev-parse", "HEAD").decode().strip()
    _fixture_git(repo, "checkout", "-q", "--detach", baton)
    return repo, baton, candidate, tripwire


def _read_fixture_candidate(repo: Path, baton: str, candidate: str) -> dict[str, Any]:
    git_path = Path(shutil.which("git") or "").resolve(strict=True)
    layout = verifier._discover_binding_git_layout(repo)  # noqa: SLF001
    reader = verifier._GitBatchObjectReader(  # noqa: SLF001
        {"path": str(git_path)}, layout
    )
    try:
        result = verifier._candidate_manifest_from_objects(  # noqa: SLF001
            reader,
            accepted_baton_commit=baton,
            candidate_commit=candidate,
        )
        reader.close()
    except Exception:
        reader.abort()
        raise
    return result


def _next_source_receipt_fixture(candidate: dict[str, Any]) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": verifier.NEXT_SOURCE_SCHEMA,
        "verdict": verifier.NEXT_SOURCE_OK_VERDICT,
        "claim": verifier.NEXT_SOURCE_CLAIM,
        "authority": {
            "launch_authorized": False,
            "publication_authorized": False,
        },
        "limitations": list(verifier.NEXT_SOURCE_LIMITATIONS),
        "policy": dict(verifier.NEXT_SOURCE_POLICY),
        "trust_root": {
            "baton_commit": candidate["parent"],
            "baton_tree": "1" * 40,
            "source_commit": "2" * 40,
            "receipt_commit": "3" * 40,
            "tooling_receipt": {
                "path": verifier.RECEIPT_REL,
                "bytes": 123,
                "sha256": "4" * 64,
            },
            "binder": {
                "path": verifier.BINDER_REL,
                "mode": "100644",
                "bytes": 456,
                "git_blob_oid": "5" * 40,
                "sha256": "6" * 64,
            },
            "python": {
                "path": "/usr/bin/python3",
                "bytes": 100,
                "sha256": "7" * 64,
                "version": "Python fixture",
            },
            "git": {
                "path": "/usr/bin/git",
                "bytes": 100,
                "sha256": "8" * 64,
                "version": "git version fixture",
            },
        },
        "candidate": copy.deepcopy(candidate),
        "problems": [],
        "problem_count": 0,
    }
    receipt["receipt_payload_sha256"] = verifier._sha256_bytes(  # noqa: SLF001
        verifier._canonical_json(receipt)  # noqa: SLF001
    )
    return receipt


def _encode_next_source_fixture(receipt: dict[str, Any]) -> bytes:
    receipt.pop("receipt_payload_sha256", None)
    receipt["receipt_payload_sha256"] = verifier._sha256_bytes(  # noqa: SLF001
        verifier._canonical_json(receipt)  # noqa: SLF001
    )
    return verifier._canonical_json(receipt) + b"\n"  # noqa: SLF001


def _raw_tree_entry(mode: str, name: bytes, oid: str = "1" * 40) -> bytes:
    return mode.encode("ascii") + b" " + name + b"\0" + bytes.fromhex(oid)


class _MappingObjectReader:
    def __init__(self, objects: dict[str, tuple[str, bytes]]) -> None:
        self.objects = objects
        self.calls: list[tuple[str, str]] = []

    def read(
        self, oid: str, *, expected_type: str, maximum: int, retain: bool
    ) -> tuple[int, str, bytes | None]:
        self.calls.append((oid, expected_type))
        object_type, payload = self.objects[oid]
        if object_type != expected_type:
            raise verifier.VerificationError("fixture object type mismatch")
        if len(payload) > maximum:
            raise verifier.VerificationError("fixture object exceeds byte bound")
        return (
            len(payload),
            hashlib.sha256(payload).hexdigest(),
            payload if retain else None,
        )


def _scripted_batch_reader(response: bytes) -> Any:
    reader = object.__new__(verifier._GitBatchObjectReader)  # noqa: SLF001
    reader._process = types.SimpleNamespace(  # noqa: SLF001
        stdin=io.BytesIO(), stdout=object()
    )
    reader._buffer = bytearray(response)  # noqa: SLF001
    reader._object_cache = {}  # noqa: SLF001
    return reader


def _fixture_tree_snapshot(
    files: dict[bytes, tuple[str, str]],
    objects: dict[str, tuple[str, bytes]],
    counter: list[int],
) -> str:
    def next_oid() -> str:
        counter[0] += 1
        return f"{counter[0]:040x}"

    def build(rows: dict[bytes, tuple[str, str]]) -> str:
        direct: dict[bytes, tuple[str, str]] = {}
        children: dict[bytes, dict[bytes, tuple[str, str]]] = {}
        for path, identity in rows.items():
            head, separator, tail = path.partition(b"/")
            if separator:
                children.setdefault(head, {})[tail] = identity
            else:
                direct[head] = identity
        entries = [
            (mode, name, oid) for name, (mode, oid) in direct.items()
        ] + [
            ("40000", name, build(child_rows))
            for name, child_rows in children.items()
        ]
        entries.sort(key=lambda row: row[1] + (b"/" if row[0] == "40000" else b"\0"))
        payload = b"".join(
            _raw_tree_entry(mode, name, oid) for mode, name, oid in entries
        )
        oid = next_oid()
        objects[oid] = ("tree", payload)
        return oid

    return build(files)


def _exact_trust_fixture(
    variant: str = "baseline",
) -> tuple[Any, Any, _MappingObjectReader, str, str, str]:
    baton_commit = "b" * 40
    state_commit = "c" * 40
    receipt_commit = "d" * 40
    source_commit = "e" * 40
    source_parent = verifier.GENERATION_SIXTEEN_SOURCE_PARENT
    receipt_oid = "8" * 40
    binder_oid = "9" * 40
    receipt_bytes = b"canonical R16 fixture\n"
    binder_bytes = b"generation-sixteen binder fixture\n"
    objects: dict[str, tuple[str, bytes]] = {
        receipt_oid: ("blob", receipt_bytes),
        binder_oid: ("blob", binder_bytes),
    }
    base_files = {
        b"base.txt": ("100644", hashlib.sha1(b"base", usedforsecurity=False).hexdigest())
    }
    source_files = dict(base_files)
    for path in verifier.GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS:
        encoded = path.encode("ascii")
        source_files[encoded] = (
            "100644",
            hashlib.sha1(b"F16:" + encoded, usedforsecurity=False).hexdigest(),
        )
    source_files[verifier.BINDER_REL.encode("ascii")] = ("100644", binder_oid)
    source_parents = (source_parent,)
    if variant == "f_wrong_parent":
        source_parents = ("0" * 40,)
    elif variant == "f_second_parent":
        source_parents = (source_parent, "0" * 40)
    elif variant == "f_same_tree":
        source_files = dict(base_files)

    receipt_files = dict(source_files)
    receipt_files[verifier.RECEIPT_REL.encode("ascii")] = ("100644", receipt_oid)
    if variant == "r_rename":
        receipt_files.pop(verifier.RECEIPT_REL.encode("ascii"))
        receipt_files[b"renamed-receipt.json"] = ("100644", receipt_oid)

    state_files = dict(receipt_files)
    state_files[b"MISSION_STATE.json"] = (
        "100644",
        hashlib.sha1(b"T16", usedforsecurity=False).hexdigest(),
    )
    if variant == "t_missing":
        state_files = dict(receipt_files)
    elif variant == "t_delete":
        state_files.pop(b"base.txt")
    elif variant == "t_mode":
        state_files[b"base.txt"] = ("100755", state_files[b"base.txt"][1])

    baton_files = dict(state_files)
    for path in (b"CONTINUITY.md", b"HANDOFF.md"):
        baton_files[path] = (
            "100644",
            hashlib.sha1(b"B16:" + path, usedforsecurity=False).hexdigest(),
        )
    if variant == "b_extra":
        baton_files[b"unexpected.txt"] = (
            "100644",
            hashlib.sha1(b"extra", usedforsecurity=False).hexdigest(),
        )

    counter = [100]
    parent_tree = _fixture_tree_snapshot(base_files, objects, counter)
    source_tree = _fixture_tree_snapshot(source_files, objects, counter)
    receipt_tree = _fixture_tree_snapshot(receipt_files, objects, counter)
    state_tree = _fixture_tree_snapshot(state_files, objects, counter)
    baton_tree = _fixture_tree_snapshot(baton_files, objects, counter)

    def commit_payload(tree: str, parents: tuple[str, ...], label: str) -> bytes:
        parent_headers = b"".join(
            f"parent {parent}\n".encode("ascii") for parent in parents
        )
        return f"tree {tree}\n".encode("ascii") + parent_headers + f"\n{label}\n".encode()

    objects[source_parent] = ("commit", commit_payload(parent_tree, (), "B15"))
    objects[source_commit] = (
        "commit",
        commit_payload(source_tree, source_parents, "F16"),
    )
    objects[receipt_commit] = (
        "commit",
        commit_payload(receipt_tree, (source_commit,), "R16"),
    )
    objects[state_commit] = (
        "commit",
        commit_payload(state_tree, (receipt_commit,), "T16"),
    )
    objects[baton_commit] = (
        "commit",
        commit_payload(baton_tree, (state_commit,), "B16"),
    )
    anchored = verifier._AnchoredBootstrap(  # noqa: SLF001
        tooling_receipt={},
        tooling_receipt_bytes=receipt_bytes,
        tooling_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        source_commit=source_commit,
        git={
            "path": "/usr/bin/git",
            "bytes": 1,
            "sha256": "1" * 64,
            "version": "git fixture",
        },
        python={
            "path": "/usr/bin/python3",
            "bytes": 1,
            "sha256": "2" * 64,
            "version": "Python fixture",
        },
        binder={
            "path": verifier.BINDER_REL,
            "bytes": len(binder_bytes),
            "sha256": hashlib.sha256(binder_bytes).hexdigest(),
        },
    )
    layout = verifier._BindingGitLayout(  # noqa: SLF001
        worktree=Path("/fixture/worktree"),
        git_dir=Path("/fixture/worktree/.git"),
        common_dir=Path("/fixture/worktree/.git"),
        objects_dir=Path("/fixture/worktree/.git/objects"),
        linked_worktree=False,
        directory_snapshots=(),
        control_snapshots=(),
    )
    return (
        anchored,
        layout,
        _MappingObjectReader(objects),
        baton_commit,
        receipt_oid,
        binder_oid,
    )


def _stub_exact_trust_commands(monkeypatch: Any, baton_commit: str) -> None:
    monkeypatch.setattr(
        verifier,
        "_read_small_physical_file",
        lambda *_args, **_kwargs: baton_commit.encode("ascii") + b"\n",
    )

    def fixed_git(
        _git: Any,
        _layout: Any,
        *argv: str,
        worktree: bool = False,
        maximum: int = 0,
    ) -> bytes:
        del worktree, maximum
        if argv and argv[0] == "status":
            return b""
        if argv == ("ls-files", "-v", "-z"):
            return b"H fixture\0"
        if argv == ("rev-parse", "--show-object-format"):
            return b"sha1\n"
        raise AssertionError(f"unexpected structural Git command: {argv}")

    monkeypatch.setattr(verifier, "_binding_git_bytes", fixed_git)


def test_next_source_raw_manifest_is_complete_and_candidate_never_executes(
    monkeypatch: Any, tmp_path: Path
) -> None:
    repo, baton, candidate, tripwire = _make_next_source_object_repo(tmp_path)
    monkeypatch.setattr(
        verifier,
        "validate_receipt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("next-source binder executed stale receipt replay")
        ),
    )

    result = _read_fixture_candidate(repo, baton, candidate)

    assert result["commit"] == candidate
    assert result["parent"] == baton
    assert result["file_count"] == 3
    assert result["files"] == sorted(result["files"], key=lambda row: row["path"])
    assert {row["path"] for row in result["files"]} == {
        "base.txt",
        "scripts/ci/candidate.sh",
        "scripts/ci/hashlib.py",
    }
    assert next(
        row for row in result["files"] if row["path"] == "scripts/ci/candidate.sh"
    )["mode"] == "100755"
    assert not tripwire.exists()


def test_next_source_raw_object_reader_rejects_wrong_detached_baton(tmp_path: Path) -> None:
    repo, _baton, candidate, _tripwire = _make_next_source_object_repo(tmp_path)

    with pytest.raises(verifier.VerificationError, match="parent is not accepted B16"):
        _read_fixture_candidate(repo, "f" * 40, candidate)


def test_next_source_tree_rejects_symlinks_without_materializing_candidate(
    tmp_path: Path,
) -> None:
    repo, baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    os.symlink("base.txt", repo / "candidate-link")
    _fixture_git(repo, "add", "candidate-link")
    _fixture_git(repo, "commit", "-q", "-m", "forbidden symlink candidate")
    candidate = _fixture_git(repo, "rev-parse", "HEAD").decode().strip()
    _fixture_git(repo, "checkout", "-q", "--detach", baton)

    with pytest.raises(verifier.VerificationError, match="forbidden mode"):
        _read_fixture_candidate(repo, baton, candidate)


def test_next_source_layout_rejects_replace_and_alternate_state(tmp_path: Path) -> None:
    repo, baton, candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    _fixture_git(repo, "replace", baton, candidate)

    with pytest.raises(verifier.VerificationError, match="replacement or promisor"):
        verifier._discover_binding_git_layout(repo)  # noqa: SLF001

    _fixture_git(repo, "replace", "-d", baton)
    alternates = repo / ".git/objects/info/alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternates.write_text("/tmp/hostile-object-store\n", encoding="utf-8")
    with pytest.raises(verifier.VerificationError, match="shallow, graft, or alternate"):
        verifier._discover_binding_git_layout(repo)  # noqa: SLF001


def test_next_source_receipt_schema_is_canonical_exact_and_type_strict(
    tmp_path: Path,
) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    candidate = _read_fixture_candidate(repo, baton, candidate_commit)
    receipt = _next_source_receipt_fixture(candidate)
    raw = verifier._canonical_json(receipt) + b"\n"  # noqa: SLF001

    assert verifier._strict_next_source_receipt(raw) == receipt  # noqa: SLF001

    for mutate in ("extra", "bool", "manifest", "limitation"):
        forged = copy.deepcopy(receipt)
        if mutate == "extra":
            forged["candidate"]["unexpected"] = 1
        elif mutate == "bool":
            forged["candidate"]["file_count"] = True
        elif mutate == "manifest":
            forged["candidate"]["files"][0]["sha256"] = "9" * 64
        else:
            forged["limitations"] = forged["limitations"][:-1]
        forged.pop("receipt_payload_sha256", None)
        forged["receipt_payload_sha256"] = verifier._sha256_bytes(  # noqa: SLF001
            verifier._canonical_json(forged)  # noqa: SLF001
        )
        forged_raw = verifier._canonical_json(forged) + b"\n"  # noqa: SLF001
        with pytest.raises(verifier.VerificationError):
            verifier._strict_next_source_receipt(forged_raw)  # noqa: SLF001

    noncanonical = json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n"
    with pytest.raises(verifier.VerificationError, match="not canonical"):
        verifier._strict_next_source_receipt(noncanonical)  # noqa: SLF001


def test_next_source_detached_receipt_digest_precedes_any_git_read(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(verifier, "_require_isolated_binding_interpreter", lambda: None)
    monkeypatch.setattr(
        verifier,
        "_discover_binding_git_layout",
        lambda *_args: (_ for _ in ()).throw(AssertionError("Git layout was read")),
    )

    with pytest.raises(
        verifier.VerificationError, match="differs from detached accepted SHA-256"
    ):
        verifier.build_next_source_binding(
            accepted_baton_commit="a" * 40,
            accepted_tooling_receipt_sha256="0" * 64,
            candidate_commit="b" * 40,
        )


def test_next_source_binding_requires_no_site_isolated_python(monkeypatch: Any) -> None:
    flags = types.SimpleNamespace(
        isolated=1,
        ignore_environment=1,
        no_user_site=1,
        no_site=0,
        dont_write_bytecode=1,
        safe_path=1,
    )
    monkeypatch.setattr(verifier.sys, "flags", flags)
    with pytest.raises(verifier.VerificationError, match="-I -B -S"):
        verifier._require_isolated_binding_interpreter()  # noqa: SLF001

    flags.no_site = 1
    verifier._require_isolated_binding_interpreter()  # noqa: SLF001


def test_next_source_no_clobber_writer_never_replaces_existing_receipt(
    tmp_path: Path,
) -> None:
    output = tmp_path / "next-source.json"
    payload = b'{"fixture":true}\n'

    verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    with pytest.raises(verifier.VerificationError, match="already exists"):
        verifier._write_next_source_no_clobber(output, b"replacement\n")  # noqa: SLF001
    assert output.read_bytes() == payload


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "must not be empty"),
        (_raw_tree_entry("100644", b".GIT"), "outside the contract"),
        (_raw_tree_entry("160000", b"submodule"), "forbidden mode"),
        (
            _raw_tree_entry("100644", b"same")
            + _raw_tree_entry("40000", b"same", "2" * 40),
            "duplicate component",
        ),
    ],
    ids=("empty", "casefold-dot-git", "gitlink", "file-tree-duplicate"),
)
def test_next_source_raw_tree_rejects_unrepresentable_entries(
    payload: bytes, message: str
) -> None:
    with pytest.raises(verifier.VerificationError, match=message):
        verifier._parse_next_source_tree(payload)  # noqa: SLF001


def test_next_source_receipt_rejects_blob_oid_identity_drift(tmp_path: Path) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    candidate = _read_fixture_candidate(repo, baton, candidate_commit)
    receipt = _next_source_receipt_fixture(candidate)
    first, second = receipt["candidate"]["files"][:2]
    second["git_blob_oid"] = first["git_blob_oid"]
    second["bytes"] = first["bytes"]
    second["sha256"] = "e" * 64
    receipt["candidate"]["total_file_bytes"] = sum(
        row["bytes"] for row in receipt["candidate"]["files"]
    )
    receipt["candidate"]["manifest_sha256"] = verifier._sha256_bytes(  # noqa: SLF001
        verifier._canonical_json(receipt["candidate"]["files"])  # noqa: SLF001
    )

    with pytest.raises(verifier.VerificationError, match="identity drift"):
        verifier._strict_next_source_receipt(  # noqa: SLF001
            _encode_next_source_fixture(receipt)
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tree_object_count", 0),
        ("tree_object_bytes", 0),
        ("file_count", 0),
        ("unique_blob_count", 0),
        ("unique_blob_count", 4),
        ("unique_blob_bytes", 10_000),
    ],
)
def test_next_source_receipt_rejects_impossible_nonempty_aggregates(
    tmp_path: Path, field: str, value: int
) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    candidate = _read_fixture_candidate(repo, baton, candidate_commit)
    receipt = _next_source_receipt_fixture(candidate)
    receipt["candidate"][field] = value

    with pytest.raises(verifier.VerificationError):
        verifier._strict_next_source_receipt(  # noqa: SLF001
            _encode_next_source_fixture(receipt)
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1.0}',
        b'{"x":1e0}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":9223372036854775808}',
        b'{"x":1,"x":2}',
    ],
    ids=("finite-float", "exponent-float", "nan", "infinity", "huge-int", "duplicate"),
)
def test_next_source_json_parser_rejects_hostile_scalars_and_duplicates(
    raw: bytes,
) -> None:
    with pytest.raises((verifier.VerificationError, ValueError)):
        verifier._parse_next_source_json(raw)  # noqa: SLF001


def test_next_source_json_parser_enforces_iterative_depth_and_node_bounds(
    monkeypatch: Any,
) -> None:
    too_deep = b'{"x":' + b"[" * 32 + b"0" + b"]" * 32 + b"}"
    too_many_nodes = b'{"x":[' + b"0," * verifier.NEXT_SOURCE_MAX_JSON_NODES + b"0]}"
    monkeypatch.setattr(
        verifier.json,
        "loads",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("recursive JSON decoder ran before iterative bounds")
        ),
    )

    with pytest.raises(verifier.VerificationError, match="depth"):
        verifier._parse_next_source_json(too_deep)  # noqa: SLF001
    with pytest.raises(verifier.VerificationError, match="node count"):
        verifier._parse_next_source_json(too_many_nodes)  # noqa: SLF001


@pytest.mark.parametrize("alias", [0, 1])
def test_next_source_receipt_rejects_integer_authority_aliases(
    tmp_path: Path, alias: int
) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    receipt = _next_source_receipt_fixture(
        _read_fixture_candidate(repo, baton, candidate_commit)
    )
    receipt["authority"]["launch_authorized"] = alias

    with pytest.raises(verifier.VerificationError, match="fixed contract"):
        verifier._strict_next_source_receipt(  # noqa: SLF001
            _encode_next_source_fixture(receipt)
        )


def test_next_source_receipt_rejects_extra_trailing_newline(tmp_path: Path) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    receipt = _next_source_receipt_fixture(
        _read_fixture_candidate(repo, baton, candidate_commit)
    )

    with pytest.raises(verifier.VerificationError, match="not canonical"):
        verifier._strict_next_source_receipt(  # noqa: SLF001
            _encode_next_source_fixture(receipt) + b"\n"
        )


def test_next_source_bounded_reader_rejects_sparse_oversize_before_read(
    monkeypatch: Any, tmp_path: Path
) -> None:
    oversized = tmp_path / "oversized.json"
    with oversized.open("wb") as handle:
        handle.truncate(verifier.NEXT_SOURCE_MAX_RECEIPT_BYTES + 1)
    monkeypatch.setattr(
        verifier.os,
        "read",
        lambda *_args: (_ for _ in ()).throw(AssertionError("oversized file was read")),
    )

    with pytest.raises(verifier.VerificationError, match="size or type is outside"):
        verifier._read_stable_regular_file_bounded(  # noqa: SLF001
            oversized, verifier.NEXT_SOURCE_MAX_RECEIPT_BYTES
        )


def test_next_source_bounded_reader_rejects_ancestor_swap_without_attacker_bytes(
    monkeypatch: Any, tmp_path: Path
) -> None:
    trusted_parent = tmp_path / "trusted"
    trusted_parent.mkdir()
    trusted_file = trusted_parent / "receipt.json"
    trusted_file.write_bytes(b"trusted\n")
    moved_parent = tmp_path / "trusted-moved"
    attacker_parent = tmp_path / "attacker"
    attacker_parent.mkdir()
    (attacker_parent / trusted_file.name).write_bytes(b"attacker\n")
    original_open = os.open
    swapped = False

    def swapping_open(
        path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal swapped
        if not swapped and dir_fd is not None and path == trusted_file.name:
            trusted_parent.rename(moved_parent)
            trusted_parent.symlink_to(attacker_parent, target_is_directory=True)
            swapped = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(verifier.os, "open", swapping_open)
    with pytest.raises(verifier.VerificationError, match="physical directory component"):
        verifier._read_stable_regular_file_bounded(trusted_file, 1_024)  # noqa: SLF001
    assert (moved_parent / trusted_file.name).read_bytes() == b"trusted\n"
    assert (attacker_parent / trusted_file.name).read_bytes() == b"attacker\n"


@pytest.mark.parametrize("control_snapshot", [False, True])
def test_next_source_bounded_readers_reject_fifo_without_blocking(
    tmp_path: Path, control_snapshot: bool
) -> None:
    fifo = tmp_path / "hostile-fifo"
    os.mkfifo(fifo)

    with pytest.raises(verifier.VerificationError, match="size or type"):
        if control_snapshot:
            verifier._binding_control_snapshot(fifo, 1_024, required=True)  # noqa: SLF001
        else:
            verifier._read_stable_regular_file_bounded(fifo, 1_024)  # noqa: SLF001


def test_next_source_physical_route_containment_uses_device_inode_not_spelling() -> None:
    route = (
        ("/case-preserving/SENTINEL", (17, 23, stat.S_IFDIR | 0o700, 501, 20)),
        ("/unrelated/label", (17, 29, stat.S_IFDIR | 0o700, 501, 20)),
    )

    assert verifier._physical_route_contains_directory_identity(  # noqa: SLF001
        route, (17, 23)
    )
    assert not verifier._physical_route_contains_directory_identity(  # noqa: SLF001
        route, (17, 31)
    )


def test_next_source_object_reader_has_a_hard_deadline(
    monkeypatch: Any, tmp_path: Path
) -> None:
    repo, _baton, candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    git_path = Path(shutil.which("git") or "").resolve(strict=True)
    reader = verifier._GitBatchObjectReader(  # noqa: SLF001
        {"path": str(git_path)}, verifier._discover_binding_git_layout(repo)  # noqa: SLF001
    )
    monkeypatch.setattr(verifier.select, "select", lambda *_args: ([], [], []))

    with pytest.raises(verifier.VerificationError, match="deadline expired"):
        reader.read(
            candidate,
            expected_type="commit",
            maximum=verifier.NEXT_SOURCE_MAX_COMMIT_BYTES,
            retain=True,
        )
    assert reader._process.poll() is not None  # noqa: SLF001


@pytest.mark.parametrize("oversized", [False, True])
def test_next_source_object_reader_requires_empty_bounded_stderr(
    monkeypatch: Any, tmp_path: Path, oversized: bool
) -> None:
    repo, _baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    git_path = Path(shutil.which("git") or "").resolve(strict=True)
    reader = verifier._GitBatchObjectReader(  # noqa: SLF001
        {"path": str(git_path)}, verifier._discover_binding_git_layout(repo)  # noqa: SLF001
    )
    if oversized:
        monkeypatch.setattr(verifier, "NEXT_SOURCE_MAX_GIT_STDERR_BYTES", 8)
    reader._stderr.write(b"diagnostic" if not oversized else b"123456789")  # noqa: SLF001

    message = "oversized" if oversized else "reader failed"
    try:
        with pytest.raises(verifier.VerificationError, match=message):
            reader.close()
    finally:
        reader.abort()


@pytest.mark.parametrize(
    ("flag", "tag"),
    [("--assume-unchanged", b"h "), ("--skip-worktree", b"S ")],
)
def test_next_source_index_inventory_rejects_hidden_flags(
    tmp_path: Path, flag: str, tag: bytes
) -> None:
    repo, _baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    _fixture_git(repo, "update-index", flag, "base.txt")
    rows = _fixture_git(repo, "ls-files", "-v", "-z")
    assert rows.startswith(tag)

    with pytest.raises(verifier.VerificationError, match="index contains"):
        verifier._validate_binding_index_rows(rows)  # noqa: SLF001


def test_next_source_layout_supports_canonical_linked_worktree(tmp_path: Path) -> None:
    repo, baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    linked = tmp_path / "linked-worktree"
    _fixture_git(repo, "worktree", "add", "--detach", "-q", str(linked), baton)

    layout = verifier._discover_binding_git_layout(linked)  # noqa: SLF001

    assert layout.worktree == linked.resolve()
    assert layout.common_dir == (repo / ".git").resolve()
    assert layout.git_dir.parent == (repo / ".git/worktrees").resolve()


def test_next_source_writer_prelink_fsync_failure_leaves_no_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    monkeypatch.setattr(
        verifier.os,
        "fsync",
        lambda *_args: (_ for _ in ()).throw(OSError("prelink fsync fault")),
    )

    with pytest.raises(OSError, match="prelink fsync fault"):
        verifier._write_next_source_no_clobber(output, b"prelink\n")  # noqa: SLF001
    assert not output.exists()
    assert list(tmp_path.glob(".next-source.*.tmp")) == []


def test_next_source_writer_prelink_link_failure_leaves_no_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    monkeypatch.setattr(
        verifier.os,
        "link",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("link fault")),
    )

    with pytest.raises(OSError, match="link fault"):
        verifier._write_next_source_no_clobber(output, b"prelink\n")  # noqa: SLF001
    assert not output.exists()
    assert list(tmp_path.glob(".next-source.*.tmp")) == []


def test_next_source_writer_foreign_staging_collision_is_never_unlinked(
    monkeypatch: Any, tmp_path: Path
) -> None:
    process_id = 0x1234
    monotonic_tick = 0x5678
    temporary = tmp_path / f".next-source.{process_id:x}.{monotonic_tick:x}.tmp"
    temporary.write_bytes(b"foreign-staging-entry\n")
    output = tmp_path / "binding.json"
    monkeypatch.setattr(verifier.os, "getpid", lambda: process_id)
    monkeypatch.setattr(verifier.time, "monotonic_ns", lambda: monotonic_tick)

    with pytest.raises(FileExistsError):
        verifier._write_next_source_no_clobber(output, b"candidate\n")  # noqa: SLF001

    assert not output.exists()
    assert temporary.read_bytes() == b"foreign-staging-entry\n"


@pytest.mark.parametrize("mixed_case", [False, True])
def test_next_source_writer_rejects_reserved_staging_namespace_case_insensitively(
    monkeypatch: Any, tmp_path: Path, mixed_case: bool
) -> None:
    process_id = 0x1234
    monotonic_tick = 0x5678
    name = f".next-source.{process_id:x}.{monotonic_tick:x}.tmp"
    if mixed_case:
        name = name.upper()
    output = tmp_path / name
    monkeypatch.setattr(verifier.os, "getpid", lambda: process_id)
    monkeypatch.setattr(verifier.time, "monotonic_ns", lambda: monotonic_tick)

    with pytest.raises(verifier.VerificationError, match="reserved staging namespace"):
        verifier._write_next_source_no_clobber(output, b"candidate\n")  # noqa: SLF001

    assert not output.exists()


def test_next_source_writer_detects_staging_replacement_and_preserves_foreign_name(
    monkeypatch: Any, tmp_path: Path
) -> None:
    process_id = 0x1234
    monotonic_tick = 0x5678
    temporary = tmp_path / f".next-source.{process_id:x}.{monotonic_tick:x}.tmp"
    output = tmp_path / "binding.json"
    foreign = b"foreign-replacement\n"
    original_open = os.open
    original_close = os.close
    staging_descriptor: int | None = None
    monkeypatch.setattr(verifier.os, "getpid", lambda: process_id)
    monkeypatch.setattr(verifier.time, "monotonic_ns", lambda: monotonic_tick)

    def tracking_open(
        path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal staging_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == temporary.name and flags & os.O_EXCL:
            staging_descriptor = descriptor
        return descriptor

    def replacing_close(descriptor: int) -> None:
        original_close(descriptor)
        if descriptor == staging_descriptor:
            temporary.unlink()
            temporary.write_bytes(foreign)

    monkeypatch.setattr(verifier.os, "open", tracking_open)
    monkeypatch.setattr(verifier.os, "close", replacing_close)

    with pytest.raises(verifier.VerificationError, match="identity changed"):
        verifier._write_next_source_no_clobber(output, b"candidate\n")  # noqa: SLF001

    assert not output.exists()
    assert temporary.read_bytes() == foreign


def test_next_source_writer_link_then_raise_reports_committed_and_preserves_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"landed-before-error\n"
    original_link = os.link

    def link_then_raise(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        raise OSError("simulated asynchronous link-call failure")

    monkeypatch.setattr(verifier.os, "link", link_then_raise)
    with pytest.raises(
        verifier.NextSourceBindingCommittedError, match="hard link landed"
    ):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


@pytest.mark.parametrize("landed", [False, True])
@pytest.mark.parametrize("reconciliation_fault", [OSError("stat fault"), KeyboardInterrupt()])
def test_next_source_writer_link_reconciliation_fault_is_indeterminate_and_preserved(
    monkeypatch: Any,
    tmp_path: Path,
    reconciliation_fault: BaseException,
    landed: bool,
) -> None:
    output = tmp_path / "binding.json"
    payload = b"landed-before-reconciliation-fault\n"
    original_link = os.link
    original_stat = os.stat
    link_attempted = False

    def link_then_raise(*args: Any, **kwargs: Any) -> None:
        nonlocal link_attempted
        if landed:
            original_link(*args, **kwargs)
        link_attempted = True
        raise OSError("simulated asynchronous link-call failure")

    def faulting_stat(
        path: Any,
        *args: Any,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        if link_attempted and path == output.name and dir_fd is not None:
            raise reconciliation_fault
        return original_stat(
            path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks
        )

    monkeypatch.setattr(verifier.os, "link", link_then_raise)
    monkeypatch.setattr(verifier.os, "stat", faulting_stat)

    with pytest.raises(
        verifier.NextSourceBindingIndeterminateError, match="outcome is indeterminate"
    ):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001

    if landed:
        assert output.read_bytes() == payload
    else:
        assert not output.exists()
    temporary_paths = list(tmp_path.glob(".next-source.*.tmp"))
    assert len(temporary_paths) == 1
    assert temporary_paths[0].read_bytes() == payload


def test_next_source_writer_link_error_with_same_inode_wrong_nlink_is_committed(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"landed-with-extra-link\n"
    original_link = os.link

    def link_twice_then_raise(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        original_link(
            args[0],
            "extra-binding-link",
            src_dir_fd=kwargs["src_dir_fd"],
            dst_dir_fd=kwargs["dst_dir_fd"],
            follow_symlinks=False,
        )
        raise OSError("link call failed after two names landed")

    monkeypatch.setattr(verifier.os, "link", link_twice_then_raise)
    with pytest.raises(
        verifier.NextSourceBindingCommittedError, match="unverifiable postcondition"
    ):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload
    assert (tmp_path / "extra-binding-link").read_bytes() == payload


@pytest.mark.parametrize("failing_fsync_call", [2, 3])
def test_next_source_writer_dir_fsync_fault_preserves_committed_final(
    monkeypatch: Any, tmp_path: Path, failing_fsync_call: int
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed\n"
    original_fsync = os.fsync
    calls = 0

    def faulting_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == failing_fsync_call:
            raise OSError("directory fsync fault")
        original_fsync(descriptor)

    monkeypatch.setattr(verifier.os, "fsync", faulting_fsync)
    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


def test_next_source_writer_postlink_base_exception_is_committed(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed-before-interrupt\n"
    original_fsync = os.fsync
    calls = 0

    def interrupting_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt
        original_fsync(descriptor)

    monkeypatch.setattr(verifier.os, "fsync", interrupting_fsync)
    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


def test_next_source_writer_postlink_unlink_fault_preserves_committed_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed\n"
    monkeypatch.setattr(
        verifier.os,
        "unlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("unlink fault")),
    )

    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


def test_next_source_writer_final_read_fault_preserves_committed_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed\n"
    monkeypatch.setattr(
        verifier,
        "_read_stable_regular_file_bounded",
        lambda *_args: (_ for _ in ()).throw(OSError("final read fault")),
    )

    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


@pytest.mark.parametrize("drift", ["payload", "mode", "link_count", "inode"])
def test_next_source_writer_final_validation_drift_is_committed(
    monkeypatch: Any, tmp_path: Path, drift: str
) -> None:
    output = tmp_path / "binding.json"
    extra_link = tmp_path / "extra-binding-link"
    payload = b"committed-before-final-drift\n"

    def drift_then_read(*_args: Any) -> bytes:
        if drift == "payload":
            return b"mismatched-read\n"
        if drift == "mode":
            output.chmod(0o644)
        elif drift == "link_count":
            os.link(output, extra_link)
        elif drift == "inode":
            output.unlink()
            output.write_bytes(payload)
            output.chmod(0o600)
        return payload

    monkeypatch.setattr(
        verifier, "_read_stable_regular_file_bounded", drift_then_read
    )

    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001

    assert output.exists()


def test_next_source_writer_final_stat_fault_preserves_committed_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed-before-final-stat-fault\n"
    original_stat = os.stat

    def faulting_stat(
        path: Any,
        *args: Any,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        if path == output.name and dir_fd is not None:
            raise OSError("final stat fault")
        return original_stat(
            path, *args, dir_fd=dir_fd, follow_symlinks=follow_symlinks
        )

    monkeypatch.setattr(verifier.os, "stat", faulting_stat)

    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001

    assert output.read_bytes() == payload


def test_next_source_writer_final_parent_revalidation_fault_is_committed(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed-before-parent-drift\n"
    original_mode = stat.S_IMODE(tmp_path.stat().st_mode)

    def drift_parent_then_read(*_args: Any) -> bytes:
        tmp_path.chmod(original_mode | 0o020)
        return payload

    monkeypatch.setattr(
        verifier, "_read_stable_regular_file_bounded", drift_parent_then_read
    )
    try:
        with pytest.raises(verifier.NextSourceBindingCommittedError):
            verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    finally:
        tmp_path.chmod(original_mode)

    assert output.read_bytes() == payload


def test_next_source_writer_directory_close_fault_preserves_committed_final(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payload = b"committed\n"
    original_close = os.close
    original_open_chain = verifier._open_physical_directory_chain  # noqa: SLF001
    writer_directory_descriptor: int | None = None

    def tracking_open_chain(
        directory: Path,
    ) -> tuple[int, tuple[tuple[str, tuple[int, ...]], ...]]:
        nonlocal writer_directory_descriptor
        descriptor, route = original_open_chain(directory)
        if Path(directory) == tmp_path and writer_directory_descriptor is None:
            writer_directory_descriptor = descriptor
        return descriptor, route

    def faulting_close(descriptor: int) -> None:
        should_fault = descriptor == writer_directory_descriptor
        original_close(descriptor)
        if should_fault:
            raise OSError("directory close fault")

    monkeypatch.setattr(
        verifier, "_open_physical_directory_chain", tracking_open_chain
    )
    monkeypatch.setattr(verifier.os, "close", faulting_close)
    with pytest.raises(verifier.NextSourceBindingCommittedError):
        verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
    assert output.read_bytes() == payload


def test_next_source_writer_two_writer_barrier_commits_exactly_one(
    monkeypatch: Any, tmp_path: Path
) -> None:
    output = tmp_path / "binding.json"
    payloads = (b"writer-one\n", b"writer-two\n")
    barrier = threading.Barrier(2)
    directory_open_barrier = threading.Barrier(2)
    initial_fstat_barrier = threading.Barrier(2)
    writer_directory_fds: set[int] = set()
    initial_fstat_seen: set[int] = set()
    synchronization_lock = threading.Lock()
    original_link = os.link
    original_open = os.open
    original_fstat = os.fstat

    def synchronized_link(*args: Any, **kwargs: Any) -> None:
        barrier.wait(timeout=10)
        original_link(*args, **kwargs)

    def synchronized_directory_open(
        path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is None and Path(path) == tmp_path:
            with synchronization_lock:
                writer_directory_fds.add(descriptor)
            directory_open_barrier.wait(timeout=10)
        return descriptor

    def synchronized_initial_fstat(descriptor: int) -> os.stat_result:
        observed = original_fstat(descriptor)
        should_wait = False
        with synchronization_lock:
            if (
                descriptor in writer_directory_fds
                and descriptor not in initial_fstat_seen
            ):
                initial_fstat_seen.add(descriptor)
                should_wait = True
        if should_wait:
            initial_fstat_barrier.wait(timeout=10)
        return observed

    def write(payload: bytes) -> Exception | None:
        try:
            verifier._write_next_source_no_clobber(output, payload)  # noqa: SLF001
        except Exception as error:  # noqa: BLE001 - outcome is the assertion surface
            return error
        return None

    monkeypatch.setattr(verifier.os, "link", synchronized_link)
    monkeypatch.setattr(verifier.os, "open", synchronized_directory_open)
    monkeypatch.setattr(verifier.os, "fstat", synchronized_initial_fstat)
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(write, payloads))

    assert sum(outcome is None for outcome in outcomes) == 1
    loser = next(outcome for outcome in outcomes if outcome is not None)
    assert type(loser) is verifier.VerificationError
    assert "already exists" in str(loser)
    assert output.read_bytes() in payloads
    assert list(tmp_path.glob(".next-source.*.tmp")) == []


def test_next_source_writer_rejects_redirected_parent_final_symlink_and_root(
    tmp_path: Path,
) -> None:
    physical = tmp_path / "physical"
    nested = physical / "nested"
    nested.mkdir(parents=True)
    redirected = tmp_path / "redirected"
    redirected.symlink_to(physical, target_is_directory=True)
    with pytest.raises(verifier.VerificationError, match="physical directory"):
        verifier._write_next_source_no_clobber(  # noqa: SLF001
            redirected / "nested/binding.json", b"redirected\n"
        )

    target = tmp_path / "target.json"
    target.write_bytes(b"target\n")
    final_symlink = tmp_path / "binding.json"
    final_symlink.symlink_to(target)
    with pytest.raises(verifier.VerificationError, match="already exists"):
        verifier._write_next_source_no_clobber(final_symlink, b"replacement\n")  # noqa: SLF001
    assert final_symlink.is_symlink()
    assert target.read_bytes() == b"target\n"

    trusted = tmp_path / "trusted"
    trusted.mkdir()
    with pytest.raises(verifier.VerificationError, match="forbidden trusted root"):
        verifier._write_next_source_no_clobber(  # noqa: SLF001
            trusted / "binding.json", b"forbidden\n", forbidden_roots=(trusted,)
        )


def test_next_source_writer_rejects_case_alias_of_forbidden_root_on_apfs(
    tmp_path: Path,
) -> None:
    trusted = tmp_path / "trustedcase"
    nested = trusted / "nested"
    nested.mkdir(parents=True)
    alias = tmp_path / "TRUSTEDCASE"
    try:
        aliases_same_directory = alias.samefile(trusted)
    except FileNotFoundError:
        aliases_same_directory = False
    if not aliases_same_directory:
        pytest.skip("fixture filesystem is case-sensitive")

    with pytest.raises(verifier.VerificationError, match="forbidden trusted root"):
        verifier._write_next_source_no_clobber(  # noqa: SLF001
            alias / "nested/binding.json",
            b"forbidden-case-alias\n",
            forbidden_roots=(trusted,),
        )


@pytest.mark.parametrize(
    ("stage", "message"),
    [
        ("header", "header is oversized"),
        ("oid", "identity or type mismatch"),
        ("type", "identity or type mismatch"),
        ("size", "size is malformed"),
        ("oversized", "exceeds byte bound"),
        ("framing", "framing is malformed"),
        ("sha1", "SHA-1 mismatch"),
        ("truncated", "ended unexpectedly"),
    ],
)
def test_next_source_raw_reader_rejects_protocol_drift(
    stage: str, message: str
) -> None:
    oid = "a" * 40
    maximum = 16
    if stage == "header":
        response = b"x" * (verifier.NEXT_SOURCE_MAX_GIT_HEADER_BYTES + 1)
    elif stage == "oid":
        response = f"{'b' * 40} commit 0\n\n".encode()
    elif stage == "type":
        response = f"{oid} tree 0\n\n".encode()
    elif stage == "size":
        response = f"{oid} commit 01\nx\n".encode()
    elif stage == "oversized":
        response = f"{oid} commit 17\n".encode()
    elif stage == "framing":
        response = f"{oid} commit 1\n".encode() + b"x!"
    elif stage == "sha1":
        response = f"{oid} commit 1\n".encode() + b"x\n"
    else:
        response = f"{oid} commit 2\n".encode() + b"x"
    reader = _scripted_batch_reader(response)
    if stage == "truncated":
        reader._fill = lambda: (_ for _ in ()).throw(  # noqa: SLF001
            verifier.VerificationError("bootstrap Git object reader ended unexpectedly")
        )

    with pytest.raises(verifier.VerificationError, match=message):
        reader.read(
            oid,
            expected_type="commit",
            maximum=maximum,
            retain=True,
        )


def test_next_source_raw_reader_requests_each_oid_once_per_pass() -> None:
    payload = b"shared"
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {len(payload)}".encode() + b"\0" + payload)
    oid = digest.hexdigest()
    response = f"{oid} blob {len(payload)}\n".encode() + payload + b"\n"
    reader = _scripted_batch_reader(response)

    first = reader.read(oid, expected_type="blob", maximum=100, retain=True)
    second = reader.read(oid, expected_type="blob", maximum=100, retain=False)

    assert first[:2] == second[:2]
    assert first[2] == payload
    assert second[2] is None
    assert reader._process.stdin.getvalue() == oid.encode() + b"\n"  # noqa: SLF001
    assert reader._buffer == b""  # noqa: SLF001


@pytest.mark.parametrize(
    "payload",
    [
        b"tree " + b"1" * 40 + b"\nparent " + b"2" * 40,
        b"author fixture\ntree " + b"1" * 40 + b"\n\nmessage",
        b"tree " + b"1" * 40 + b"\ntree " + b"2" * 40 + b"\n\nmessage",
        b"tree \nparent " + b"2" * 40 + b"\n\nmessage",
        b"tree " + b"1" * 40 + b"\n orphan\n\nmessage",
        b"tree "
        + b"1" * 40
        + b"\nparent "
        + b"2" * 40
        + b"\n continuation\n\nmessage",
    ],
    ids=(
        "no-separator",
        "misplaced-tree",
        "duplicate-tree",
        "empty-tree",
        "tree-continuation",
        "parent-continuation",
    ),
)
def test_next_source_raw_commit_parser_rejects_malformed_headers(payload: bytes) -> None:
    with pytest.raises(verifier.VerificationError):
        verifier._parse_raw_commit_links(payload)  # noqa: SLF001


def test_next_source_candidate_rejects_merge_commit_header() -> None:
    baton = "2" * 40
    payload = (
        f"tree {'1' * 40}\nparent {baton}\nparent {'3' * 40}\n\nmerge\n".encode()
    )
    with pytest.raises(verifier.VerificationError, match="parent is not accepted B16"):
        verifier._parse_next_source_commit(payload, baton)  # noqa: SLF001


def test_next_source_raw_tree_diff_handles_add_delete_mode_and_skips_equal_subtree() -> None:
    parent_commit = "1" * 40
    current_commit = "2" * 40
    parent_tree = "3" * 40
    current_tree = "4" * 40
    shared_tree = "5" * 40
    unchanged_blob = "6" * 40
    mode_blob = "7" * 40
    deleted_blob = "8" * 40
    added_blob = "9" * 40
    objects = {
        parent_commit: (
            "commit",
            f"tree {parent_tree}\nparent {'a' * 40}\n\nparent\n".encode(),
        ),
        current_commit: (
            "commit",
            f"tree {current_tree}\nparent {parent_commit}\n\ncurrent\n".encode(),
        ),
        parent_tree: (
            "tree",
            _raw_tree_entry("100644", b"deleted", deleted_blob)
            + _raw_tree_entry("100644", b"mode", mode_blob)
            + _raw_tree_entry("40000", b"shared", shared_tree),
        ),
        current_tree: (
            "tree",
            _raw_tree_entry("100644", b"added", added_blob)
            + _raw_tree_entry("100755", b"mode", mode_blob)
            + _raw_tree_entry("40000", b"shared", shared_tree),
        ),
        shared_tree: (
            "tree",
            _raw_tree_entry("100644", b"unchanged", unchanged_blob),
        ),
    }
    reader = _MappingObjectReader(objects)
    topology = verifier._RawTopologyView(reader)  # noqa: SLF001

    assert topology.changed_paths(current_commit, parent_commit) == (
        b"added",
        b"deleted",
        b"mode",
    )
    assert (shared_tree, "tree") not in reader.calls
    assert all(object_type != "blob" for _oid, object_type in reader.calls)
    assert len(reader.calls) == len(set(reader.calls))


def test_next_source_raw_tree_diff_rejects_blob_tree_transition() -> None:
    parent_tree = "1" * 40
    current_tree = "2" * 40
    nested_tree = "3" * 40
    reader = _MappingObjectReader(
        {
            parent_tree: ("tree", _raw_tree_entry("100644", b"node", "4" * 40)),
            current_tree: ("tree", _raw_tree_entry("40000", b"node", nested_tree)),
        }
    )
    topology = verifier._RawTopologyView(reader)  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="blob/tree transition"):
        topology._diff_trees(  # noqa: SLF001
            current_tree,
            parent_tree,
            b"",
            active=frozenset(),
            depth=0,
        )


@pytest.mark.parametrize("kind", ["recursive", "deep"])
def test_next_source_raw_tree_enumeration_rejects_recursive_or_deep(
    kind: str,
) -> None:
    if kind == "recursive":
        root = "1" * 40
        objects = {root: ("tree", _raw_tree_entry("40000", b"loop", root))}
    else:
        oids = [f"{index + 1:040x}" for index in range(verifier.NEXT_SOURCE_MAX_TREE_DEPTH + 3)]
        root = oids[0]
        objects = {
            oid: ("tree", _raw_tree_entry("40000", b"next", oids[index + 1]))
            for index, oid in enumerate(oids[:-1])
        }
        objects[oids[-1]] = (
            "tree",
            _raw_tree_entry("100644", b"leaf", "f" * 40),
        )
    topology = verifier._RawTopologyView(_MappingObjectReader(objects))  # noqa: SLF001

    with pytest.raises(verifier.VerificationError, match="recursive|depth"):
        topology._enumerate_leaves(  # noqa: SLF001
            ("40000", root), b"root", active=frozenset(), depth=0
        )


def test_next_source_real_tree_read_enforces_aggregate_tree_bound(
    monkeypatch: Any, tmp_path: Path
) -> None:
    repo, baton, candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    monkeypatch.setattr(verifier, "NEXT_SOURCE_MAX_TREE_BYTES", 1)

    with pytest.raises(verifier.VerificationError, match="exceeds byte bound"):
        _read_fixture_candidate(repo, baton, candidate)


@pytest.mark.parametrize("kind", ["shallow", "graft", "promisor", "partial"])
def test_next_source_layout_rejects_additional_nonlocal_graph_state(
    tmp_path: Path, kind: str
) -> None:
    repo, baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    if kind == "shallow":
        (repo / ".git/shallow").write_text(f"{baton}\n", encoding="ascii")
    elif kind == "graft":
        graft = repo / ".git/info/grafts"
        graft.parent.mkdir(parents=True, exist_ok=True)
        graft.write_text(f"{baton}\n", encoding="ascii")
    elif kind == "promisor":
        (repo / ".git/objects/pack/fixture.promisor").write_bytes(b"")
    else:
        _fixture_git(repo, "config", "extensions.partialClone", "origin")

    with pytest.raises(verifier.VerificationError):
        verifier._discover_binding_git_layout(repo)  # noqa: SLF001


def test_next_source_layout_snapshot_witnesses_transient_metadata_creation(
    tmp_path: Path,
) -> None:
    repo, _baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    before = verifier._discover_binding_git_layout(repo)  # noqa: SLF001
    info = repo / ".git/info"
    info_before = info.stat()
    transient = info / "transient-graft-witness"
    transient.write_bytes(b"created then removed\n")
    transient.unlink()
    info_after = info.stat()
    if info_after.st_mtime_ns == info_before.st_mtime_ns:
        os.utime(
            info,
            ns=(info_after.st_atime_ns, info_after.st_mtime_ns + 1),
        )

    after = verifier._discover_binding_git_layout(repo)  # noqa: SLF001

    assert before.directory_snapshots != after.directory_snapshots


@pytest.mark.parametrize("relative", ["index", "config"])
def test_next_source_layout_snapshot_rejects_identical_byte_control_replacement(
    tmp_path: Path, relative: str
) -> None:
    repo, _baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    before = verifier._discover_binding_git_layout(repo)  # noqa: SLF001
    target = repo / ".git" / relative
    replacement = repo / ".git" / f".{relative}.replacement"
    original_mode = stat.S_IMODE(target.stat().st_mode)
    replacement.write_bytes(target.read_bytes())
    replacement.chmod(original_mode)
    os.replace(replacement, target)

    after = verifier._discover_binding_git_layout(repo)  # noqa: SLF001

    assert before.control_snapshots != after.control_snapshots


@pytest.mark.parametrize("kind", ["symlink-index", "config-include"])
def test_next_source_layout_rejects_redirected_index_or_config_include(
    tmp_path: Path, kind: str
) -> None:
    repo, _baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    if kind == "symlink-index":
        index = repo / ".git/index"
        physical_index = repo / ".git/index.physical"
        index.rename(physical_index)
        index.symlink_to(physical_index.name)
    else:
        config = repo / ".git/config"
        config.write_bytes(
            config.read_bytes()
            + b"\n[include]\n\tpath = /tmp/hostile-bootstrap-config\n"
        )

    with pytest.raises(verifier.VerificationError, match="symlink|includes external"):
        verifier._discover_binding_git_layout(repo)  # noqa: SLF001


def test_next_source_layout_rejects_linked_worktree_gitfile_redirection(
    tmp_path: Path,
) -> None:
    repo, baton, _candidate, _tripwire = _make_next_source_object_repo(tmp_path)
    linked = tmp_path / "linked-worktree"
    _fixture_git(repo, "worktree", "add", "--detach", "-q", str(linked), baton)
    (linked / ".git").write_text(f"gitdir: {repo / '.git'}\n", encoding="utf-8")

    with pytest.raises(verifier.VerificationError, match="noncanonical|outside canonical"):
        verifier._discover_binding_git_layout(linked)  # noqa: SLF001


def test_next_source_writer_rejects_parent_swap_between_stat_and_open(
    monkeypatch: Any, tmp_path: Path
) -> None:
    parent = tmp_path / "output"
    parent.mkdir(mode=0o700)
    moved = tmp_path / "moved-output"
    output = parent / "binding.json"
    original_open = os.open
    swapped = False

    def swapping_open(
        path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal swapped
        if not swapped and dir_fd is not None and path == parent.name:
            parent.rename(moved)
            parent.mkdir(mode=0o700)
            swapped = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(verifier.os, "open", swapping_open)
    with pytest.raises(verifier.VerificationError, match="changed while opening"):
        verifier._write_next_source_no_clobber(output, b"race\n")  # noqa: SLF001
    assert not output.exists()
    assert not (moved / output.name).exists()


def test_next_source_topology_source_has_no_graph_or_checkout_views() -> None:
    source = inspect.getsource(verifier._validate_next_source_trust_topology)  # noqa: SLF001
    for forbidden in ("rev-list", "diff-tree", '"show"', "ls-tree"):
        assert forbidden not in source


def test_next_source_exact_chain_reducer_reads_only_two_trusted_blobs(
    monkeypatch: Any,
) -> None:
    anchored, layout, reader, baton, receipt_oid, binder_oid = _exact_trust_fixture()
    _stub_exact_trust_commands(monkeypatch, baton)

    trust = verifier._validate_next_source_trust_topology(  # noqa: SLF001
        anchored, layout, baton, reader
    )

    assert trust["baton_commit"] == baton
    assert trust["source_commit"] == anchored.source_commit
    assert [call for call in reader.calls if call[1] == "blob"] == [
        (receipt_oid, "blob"),
        (binder_oid, "blob"),
    ]


@pytest.mark.parametrize(
    "variant",
    [
        "b_extra",
        "t_missing",
        "t_delete",
        "t_mode",
        "r_rename",
        "f_wrong_parent",
        "f_second_parent",
        "f_same_tree",
    ],
)
def test_next_source_exact_chain_reducer_rejects_each_link_mutation(
    monkeypatch: Any, variant: str
) -> None:
    anchored, layout, reader, baton, _receipt_oid, _binder_oid = _exact_trust_fixture(
        variant
    )
    _stub_exact_trust_commands(monkeypatch, baton)

    with pytest.raises(verifier.VerificationError):
        verifier._validate_next_source_trust_topology(  # noqa: SLF001
            anchored, layout, baton, reader
        )


@pytest.mark.parametrize(
    "argv",
    [
        [
            "legacy.json",
            "--bind-next-source",
            "a" * 40,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            "binding.json",
        ],
        [
            "--bind-next-source",
            "a" * 40,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            "binding.json",
            "--expected-candidate-commit",
            "d" * 40,
        ],
        [
            "--verify-next-source-binding",
            "binding.json",
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--expected-candidate-commit",
            "a" * 40,
            "--expected-binding-sha256",
            "d" * 64,
            "--next-source-output",
            "ignored.json",
        ],
        ["--verify-receipt", "receipt.json", "--accepted-baton-commit", "b" * 40],
        ["--accepted-baton-commit", "b" * 40],
    ],
)
def test_next_source_cli_rejects_mode_irrelevant_argument_envelopes(
    monkeypatch: Any,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    monkeypatch.setattr(
        verifier,
        "publish_next_source_binding",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("wrong CLI envelope reached binding")
        ),
    )
    monkeypatch.setattr(
        verifier,
        "validate_next_source_binding",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("wrong CLI envelope reached replay")
        ),
    )

    assert verifier.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"{verifier.FAIL_VERDICT}: ArgumentEnvelopeError\n"


@pytest.mark.parametrize(
    "outcome",
    ["success", "precommit", "precommit_interrupted", "committed", "indeterminate"],
)
def test_next_source_bind_cli_distinguishes_all_commit_outcomes(
    monkeypatch: Any,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    outcome: str,
) -> None:
    candidate = "a" * 40
    tree = "d" * 40
    digest = "e" * 64

    def publish(*_args: Any, **_kwargs: Any) -> tuple[str, int, dict[str, Any]]:
        if outcome == "precommit":
            raise verifier.VerificationError("precommit fixture")
        if outcome == "precommit_interrupted":
            raise KeyboardInterrupt
        if outcome == "committed":
            raise verifier.NextSourceBindingCommittedError("committed fixture")
        if outcome == "indeterminate":
            raise verifier.NextSourceBindingIndeterminateError("indeterminate fixture")
        return digest, 123, {"candidate": {"commit": candidate, "tree": tree}}

    monkeypatch.setattr(verifier, "publish_next_source_binding", publish)
    result = verifier.main(
        [
            "--bind-next-source",
            candidate,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            str(tmp_path / "binding.json"),
        ]
    )
    captured = capsys.readouterr()

    if outcome == "success":
        assert result == 0
        assert captured.out.splitlines() == [
            f"receipt_sha256={digest}",
            "receipt_bytes=123",
            f"candidate_commit={candidate}",
            f"candidate_tree={tree}",
            verifier.NEXT_SOURCE_OK_VERDICT,
        ]
        assert captured.err == ""
    elif outcome == "precommit":
        assert result == 2
        assert captured.out == ""
        assert captured.err == f"{verifier.FAIL_VERDICT}: VerificationError\n"
    elif outcome == "committed":
        assert result == 3
        assert captured.out == ""
        assert captured.err == (
            f"{verifier.NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT}\n"
        )
    else:
        assert result == 4
        assert captured.out == ""
        assert captured.err == (
            f"{verifier.NEXT_SOURCE_COMMIT_STATE_INDETERMINATE_VERDICT}\n"
        )


@pytest.mark.parametrize(
    ("outcome", "expected_exit"),
    [("precommit", 2), ("committed", 3), ("indeterminate", 4), ("interrupt", 4)],
)
def test_next_source_bind_cli_stderr_fault_preserves_classified_exit(
    monkeypatch: Any,
    tmp_path: Path,
    outcome: str,
    expected_exit: int,
) -> None:
    candidate = "a" * 40

    def publish(*_args: Any, **_kwargs: Any) -> tuple[str, int, dict[str, Any]]:
        if outcome == "precommit":
            raise verifier.VerificationError("precommit fixture")
        if outcome == "committed":
            raise verifier.NextSourceBindingCommittedError("committed fixture")
        if outcome == "indeterminate":
            raise verifier.NextSourceBindingIndeterminateError("indeterminate fixture")
        raise KeyboardInterrupt

    def broken_stderr(*_args: Any, **kwargs: Any) -> None:
        if kwargs.get("file") is sys.stderr:
            raise OSError("stderr fault")
        raise AssertionError("unexpected stdout write")

    monkeypatch.setattr(verifier, "publish_next_source_binding", publish)
    monkeypatch.setattr(verifier, "print", broken_stderr, raising=False)

    result = verifier.main(
        [
            "--bind-next-source",
            candidate,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            str(tmp_path / "binding.json"),
        ]
    )

    assert result == expected_exit


@pytest.mark.parametrize(
    ("fault_call", "reporting_fault"),
    [(1, OSError("stdout fault")), (3, KeyboardInterrupt())],
)
def test_next_source_bind_cli_postpublication_reporting_fault_is_committed(
    monkeypatch: Any,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    fault_call: int,
    reporting_fault: BaseException,
) -> None:
    output = tmp_path / "binding.json"
    candidate = "a" * 40
    original_print = print
    stdout_calls = 0

    def publish(path: Path, **_kwargs: Any) -> tuple[str, int, dict[str, Any]]:
        path.write_bytes(b"committed\n")
        return "e" * 64, 10, {
            "candidate": {"commit": candidate, "tree": "d" * 40}
        }

    def faulting_print(*args: Any, **kwargs: Any) -> None:
        nonlocal stdout_calls
        if kwargs.get("file", sys.stdout) is not sys.stderr:
            stdout_calls += 1
            if stdout_calls == fault_call:
                raise reporting_fault
        original_print(*args, **kwargs)

    monkeypatch.setattr(verifier, "publish_next_source_binding", publish)
    monkeypatch.setattr(verifier, "print", faulting_print, raising=False)

    result = verifier.main(
        [
            "--bind-next-source",
            candidate,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert result == 3
    assert output.read_bytes() == b"committed\n"
    assert verifier.NEXT_SOURCE_OK_VERDICT not in captured.out
    assert captured.err == f"{verifier.NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT}\n"


def test_next_source_bind_cli_success_flush_fault_cannot_authorize_exit_zero(
    monkeypatch: Any,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    output = tmp_path / "binding.json"
    candidate = "a" * 40
    original_print = print

    def publish(path: Path, **_kwargs: Any) -> tuple[str, int, dict[str, Any]]:
        path.write_bytes(b"committed\n")
        return "e" * 64, 10, {
            "candidate": {"commit": candidate, "tree": "d" * 40}
        }

    def fault_after_success_flush(*args: Any, **kwargs: Any) -> None:
        original_print(*args, **kwargs)
        if args == (verifier.NEXT_SOURCE_OK_VERDICT,) and kwargs.get("flush") is True:
            raise OSError("success flush fault")

    monkeypatch.setattr(verifier, "publish_next_source_binding", publish)
    monkeypatch.setattr(
        verifier, "print", fault_after_success_flush, raising=False
    )

    result = verifier.main(
        [
            "--bind-next-source",
            candidate,
            "--accepted-baton-commit",
            "b" * 40,
            "--accepted-tooling-receipt-sha256",
            "c" * 64,
            "--next-source-output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert result == 3
    assert output.read_bytes() == b"committed\n"
    assert captured.out.splitlines()[-1] == verifier.NEXT_SOURCE_OK_VERDICT
    assert captured.err == f"{verifier.NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT}\n"


@pytest.mark.parametrize("valid", [True, False])
def test_next_source_verify_cli_reports_exact_success_or_failure(
    monkeypatch: Any,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    valid: bool,
) -> None:
    receipt_path = tmp_path / "binding.json"
    receipt_path.write_bytes(b"fixture\n")
    monkeypatch.setattr(verifier, "_require_isolated_binding_interpreter", lambda: None)
    monkeypatch.setattr(
        verifier,
        "_read_stable_regular_file_bounded",
        lambda *_args: b"fixture\n",
    )
    monkeypatch.setattr(
        verifier,
        "validate_next_source_binding",
        lambda *_args, **_kwargs: [] if valid else ["fixture failure"],
    )

    result = verifier.main(
        [
            "--verify-next-source-binding",
            str(receipt_path),
            "--accepted-baton-commit",
            "a" * 40,
            "--accepted-tooling-receipt-sha256",
            "b" * 64,
            "--expected-candidate-commit",
            "c" * 40,
            "--expected-binding-sha256",
            "d" * 64,
        ]
    )
    captured = capsys.readouterr()

    assert result == (0 if valid else 2)
    assert captured.out.splitlines() == (
        [verifier.NEXT_SOURCE_OK_VERDICT]
        if valid
        else [verifier.FAIL_VERDICT, "problem_count=1"]
    )
    assert captured.err == ""


@pytest.mark.parametrize("mode", ["bind", "verify"])
def test_next_source_cli_rejects_missing_required_detached_arguments(
    capsys: pytest.CaptureFixture[str], mode: str
) -> None:
    argv = (
        ["--bind-next-source", "a" * 40]
        if mode == "bind"
        else ["--verify-next-source-binding", "binding.json"]
    )

    assert verifier.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"{verifier.FAIL_VERDICT}: NextSourceArgumentError\n"


def test_next_source_validate_replays_exact_detached_receipt(
    monkeypatch: Any, tmp_path: Path
) -> None:
    repo, baton, candidate_commit, _tripwire = _make_next_source_object_repo(tmp_path)
    candidate = _read_fixture_candidate(repo, baton, candidate_commit)
    receipt = _next_source_receipt_fixture(candidate)
    raw = _encode_next_source_fixture(receipt)
    monkeypatch.setattr(verifier, "_require_isolated_binding_interpreter", lambda: None)
    monkeypatch.setattr(
        verifier,
        "build_next_source_binding",
        lambda *_args, **_kwargs: copy.deepcopy(receipt),
    )

    errors = verifier.validate_next_source_binding(
        raw,
        expected_baton_commit=baton,
        expected_tooling_receipt_sha256=receipt["trust_root"]["tooling_receipt"][
            "sha256"
        ],
        expected_candidate_commit=candidate_commit,
        expected_receipt_sha256=hashlib.sha256(raw).hexdigest(),
    )

    assert errors == []
    assert verifier.validate_next_source_binding(
        raw,
        expected_baton_commit=baton,
        expected_tooling_receipt_sha256=receipt["trust_root"]["tooling_receipt"][
            "sha256"
        ],
        expected_candidate_commit="f" * 40,
        expected_receipt_sha256=hashlib.sha256(raw).hexdigest(),
    )
