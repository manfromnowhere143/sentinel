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
    assert set(receipt["files"]) == set(inventory.tested_files)
    assert verifier.RECEIPT_REL not in receipt["files"]
    assert receipt["command_contract"] == [
        list(command) for command in verifier.build_commands(inventory, fake_toolchain())
    ]
    assert runner.commands == list(verifier.build_commands(inventory, fake_toolchain()))
    assert receipt["publication"] == verifier.EXPECTED_RECOVERY_PUBLICATION
    assert verifier.RECOVERY_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "MISSION_STATE.json",
        f"{verifier.EXPERIMENT_REL}/authorize_launch135.py",
        f"{verifier.EXPERIMENT_REL}/run_dose135.sh",
        f"{verifier.EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/mission_state.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_launcher.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )
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
                path.encode() for path in verifier.RECOVERY_SOURCE_COMMIT_PATHS
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


def test_git_resolution_rejects_path_precedence_shim(
    monkeypatch: Any, tmp_path: Path
) -> None:
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
        (
            "/usr/bin/git",
            "-C",
            str(tmp_path),
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
    state_commit = "c" * 40
    baton_commit = "d" * 40
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
        assert commit == source
        return (root / relative).read_bytes()

    monkeypatch.setattr(verifier, "_git_file_bytes", fake_git_file)
    monkeypatch.setattr(
        verifier,
        "_linear_publication_chain",
        lambda _root, _ancestor, _descendant: [
            (state_commit, ("MISSION_STATE.json",)),
            (baton_commit, ("CONTINUITY.md", "HANDOFF.md")),
        ],
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
        head=baton_commit,
        dirty_entries=(),
        porcelain_sha256=hashlib.sha256(b"").hexdigest(),
        upstream_head=baton_commit,
        parents=(state_commit,),
        commit_paths=("CONTINUITY.md", "HANDOFF.md"),
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


def test_replay_rejects_missing_or_forged_generation_four_publication(
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
    ):
        forged = copy.deepcopy(receipt)
        if publication is None:
            forged.pop("publication")
        else:
            forged["publication"] = publication
        refresh_payload_digest(forged)

        errors = replay_validate(forged, root, git_probe=stable_git)

        assert "generation-four publication block mismatch" in errors


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
        source: tuple(sorted(verifier.RECOVERY_SOURCE_COMMIT_PATHS)),
        receipt_commit: (verifier.RECEIPT_REL,),
        state_commit: ("MISSION_STATE.json",),
        baton_commit: ("CONTINUITY.md", "HANDOFF.md"),
        later_commit: (verifier.REQUIRED_PYTHON_TOOL_FILES[0],),
    }
    receipt_history = [
        receipt_commit,
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
    assert any("complete state-only and offline-baton transition is missing" in error for error in errors)

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

    def receipt_missing_from_origin(
        _root: Path, ancestor: str, descendant: str
    ) -> bool:
        return not (ancestor == receipt_commit and descendant == detached_origin)

    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit, detached_origin),
        ancestry_probe=receipt_missing_from_origin,
    )
    assert any("generation-thirteen receipt is not published on origin/master" in error for error in errors)

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
    assert any("violates evidence order" in error for error in errors)

    receipt_history.pop()
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any("receipt history is not exact generation-thirteen" in error for error in errors)
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
    assert any("generation-three source topology or path scope changed" in error for error in errors)
    paths[verifier.GENERATION_THREE_SOURCE_COMMIT] = tuple(
        sorted(verifier.GENERATION_THREE_SOURCE_COMMIT_PATHS)
    )

    parents[source] = ("f" * 40,)
    errors = verifier.validate_published_receipt_structure(
        receipt,
        root,
        git_probe=lambda _root, _paths: publication_git(baton_commit),
        ancestry_probe=stable_ancestry,
    )
    assert any(
        "actual generation-four source topology or path scope is wrong" in error
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


def test_receipt_payload_digest_detects_structural_tampering(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    receipt, _runner = run_green(root)
    forged = copy.deepcopy(receipt)
    forged["problem_count"] = 0
    forged["timing"]["wall_duration_ns"] += 1

    errors = replay_validate(forged, root, git_probe=stable_git)

    assert "receipt payload digest mismatch" in errors


@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_receipt_root_field_set_is_exact_in_both_validators(
    tmp_path: Path, mutation: str
) -> None:
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
def test_receipt_parser_rejects_duplicate_and_nonfinite_json(
    payload: str, problem: str
) -> None:
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
