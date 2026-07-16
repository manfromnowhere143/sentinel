#!/usr/bin/env python3
"""Produce and independently validate the frozen Iteration-135 tooling receipt.

This verifier is intentionally local-only.  It discovers the complete Iteration-135 focused test
surface, binds every relevant source byte, executes the frozen validation commands without a
shell, and rejects file- or test-set drift at every command boundary.  Command output is never
embedded in the receipt: only byte counts and SHA-256 digests are retained.

Usage:
    verify_tooling135.py [OUTPUT.json]
    verify_tooling135.py --verify-receipt RECEIPT.json

The default output is ``tooling_verification_receipt.json`` beside this file.  A successful run
exits zero.  Any failed command, provenance failure, or temporal drift emits a red receipt and
exits two.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


SCHEMA = "iter135.tooling_verification.v2"
OK_VERDICT = "I135_TOOLING_VERIFICATION_OK"
FAIL_VERDICT = "I135_TOOLING_VERIFICATION_FAILED"

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_RECEIPT = HERE / "tooling_verification_receipt.json"
EXPERIMENT_REL = "experiments/iter135_neuroncap_blind_braking_dose_response"
RECEIPT_REL = f"{EXPERIMENT_REL}/tooling_verification_receipt.json"
EXPECTED_PREREGISTRATION_HEAD = "3fcb607fea8e1a251c2c82da385dd096dd650909"
POST_FREEZE_EXACT_PATHS = {
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/env_receipts.json",
    f"{EXPERIMENT_REL}/launch_manifest.json",
}
POST_FREEZE_PATH_PREFIXES = (f"{EXPERIMENT_REL}/smoke-evidence/",)

# These are mandatory members of the frozen surface.  Discovery is deliberately open to
# additional test/Python files so a newly added Iter135 source cannot silently escape the receipt.
REQUIRED_TEST_FILES = (
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
)
REQUIRED_PYTHON_TOOL_FILES = (
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/extract_union_windows.py",
    f"{EXPERIMENT_REL}/generate_nested_dose_schedules.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
    f"{EXPERIMENT_REL}/server_patch_blind_dose.py",
    f"{EXPERIMENT_REL}/server_patch_union_release.py",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
)
REQUIRED_SHELL_FILES = (
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
)
REQUIRED_DATA_FILES = (f"{EXPERIMENT_REL}/dose_schedules.json",)
REQUIRED_CONTROL_FILES = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    "README.md",
    "docs/NEXT_PHASE.md",
    "docs/REPORT.md",
    "docs/paper/STATUS.md",
    "docs/research/BENCH2DRIVE_ROBUST_PREFLIGHT_2026-07-16.md",
    "docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md",
    "pyproject.toml",
    "scripts/mission_state.py",
    "scripts/validate_docs.py",
    "tests/test_mission_state.py",
    f"{EXPERIMENT_REL}/HYPOTHESIS.md",
)
EXPECTED_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "MISSION_STATE.json",
    "README.md",
    "docs/research/BENCH2DRIVE_ROBUST_PREFLIGHT_2026-07-16.md",
    "docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md",
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/dose_schedules.json",
    f"{EXPERIMENT_REL}/extract_union_windows.py",
    f"{EXPERIMENT_REL}/generate_nested_dose_schedules.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/server_patch_blind_dose.py",
    f"{EXPERIMENT_REL}/server_patch_union_release.py",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
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

DISCOVERY_CONTRACT = (
    "required frozen members plus every top-level experiment *.py and every top-level "
    "tests/test_iter135_*.py; exact two shell launchers, dose_schedules.json, and frozen CI/test/"
    "mission control inputs; receipt JSON excluded"
)


class VerificationError(RuntimeError):
    """A fail-closed discovery, snapshot, or receipt error."""


@dataclass(frozen=True)
class Inventory:
    tests: tuple[str, ...]
    python_tools: tuple[str, ...]
    shell_files: tuple[str, ...]
    data_files: tuple[str, ...]
    control_files: tuple[str, ...]

    @property
    def python_files(self) -> tuple[str, ...]:
        return tuple(sorted((*self.python_tools, *self.tests)))

    @property
    def tested_files(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                (
                    *self.tests,
                    *self.python_tools,
                    *self.shell_files,
                    *self.data_files,
                    *self.control_files,
                )
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": DISCOVERY_CONTRACT,
            "tests": list(self.tests),
            "python_tools": list(self.python_tools),
            "python_files": list(self.python_files),
            "shell_files": list(self.shell_files),
            "data_files": list(self.data_files),
            "control_files": list(self.control_files),
            "tested_files": list(self.tested_files),
        }


@dataclass(frozen=True)
class FileFingerprint:
    sha256: str
    bytes: int
    device: int
    inode: int
    mode: int
    mtime_ns: int
    ctime_ns: int

    def public(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "bytes": self.bytes,
            "execution_identity": {
                "device": self.device,
                "inode": self.inode,
                "mode": self.mode,
                "mtime_ns": self.mtime_ns,
                "ctime_ns": self.ctime_ns,
            },
        }


@dataclass(frozen=True)
class RawCommandResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


@dataclass(frozen=True)
class GitState:
    head: str
    dirty_entries: tuple[str, ...]
    porcelain_sha256: str
    branch: str = ""
    upstream: str = ""
    upstream_head: str = ""
    parents: tuple[str, ...] = ()
    commit_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "head": self.head,
            "dirty_entries": list(self.dirty_entries),
            "porcelain_v1_z_sha256": self.porcelain_sha256,
            "branch": self.branch,
            "upstream": self.upstream,
            "upstream_head": self.upstream_head,
            "parents": list(self.parents),
            "commit_paths": list(self.commit_paths),
        }


Runner = Callable[[tuple[str, ...], Path], Any]
GitProbe = Callable[[Path, tuple[str, ...]], GitState]
AncestryProbe = Callable[[Path, str, str], bool]
Clock = Callable[[], int]

TOOL_NAMES = ("pytest", "bash", "shellcheck", "ruff", "python3", "git")
ALLOWED_TOOL_ROOTS = (
    Path("/bin"),
    Path("/usr/bin"),
    Path("/usr/local"),
    Path("/opt/homebrew"),
    Path("/Library/Frameworks"),
    Path("/System/Cryptexes"),
)
TOOL_VERSION_ARGS = {
    "pytest": ("--version",),
    "bash": ("--version",),
    "shellcheck": ("--version",),
    "ruff": ("--version",),
    "python3": ("--version",),
    "git": ("--version",),
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _allowed_tool_path(path: Path) -> bool:
    return any(path == root or path.is_relative_to(root) for root in ALLOWED_TOOL_ROOTS)


def _stable_external_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise VerificationError(f"tool executable is not a physical regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    byte_count = 0
    try:
        before = os.fstat(descriptor)
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    before_row = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_row = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    path_row = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_mode,
        path_after.st_size,
        path_after.st_mtime_ns,
        path_after.st_ctime_ns,
    )
    if before_row != after_row or before_row != path_row or byte_count != before.st_size:
        raise VerificationError(f"tool executable changed while hashing: {path}")
    return {
        "path": str(path),
        "sha256": digest.hexdigest(),
        "bytes": byte_count,
        "device": before.st_dev,
        "inode": before.st_ino,
        "mode": stat.S_IMODE(before.st_mode),
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
    }


def _sanitized_environment(toolchain: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    directories = []
    for name in TOOL_NAMES:
        path = str(Path(str(toolchain[name]["path"])).parent)
        if path not in directories:
            directories.append(path)
    for path in ("/usr/bin", "/bin", "/usr/sbin", "/sbin"):
        if path not in directories:
            directories.append(path)
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join(directories),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "TZ": "UTC",
    }


@lru_cache(maxsize=8)
def _resolve_toolchain_cached(
    candidates: tuple[tuple[str, str, int, int, int, int, int], ...],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, path_text, *_identity in candidates:
        physical = Path(path_text)
        receipts[name] = _stable_external_file(physical)
    environment = _sanitized_environment(receipts)
    for name in TOOL_NAMES:
        completed = subprocess.run(  # noqa: S603 - exact physical binary resolved above
            (receipts[name]["path"], *TOOL_VERSION_ARGS[name]),
            cwd=REPO_ROOT,
            env=environment,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        if completed.returncode != 0:
            raise VerificationError(f"verification executable version probe failed: {name}")
        first_line = completed.stdout.decode("utf-8", errors="replace").splitlines()
        receipts[name]["version"] = first_line[0] if first_line else ""
    return receipts


def resolve_toolchain() -> dict[str, dict[str, Any]]:
    candidates = []
    for name in TOOL_NAMES:
        located = shutil.which(name)
        if not located:
            raise VerificationError(f"required verification executable is missing: {name}")
        physical = Path(located).resolve(strict=True)
        if not _allowed_tool_path(physical):
            raise VerificationError(f"verification executable is outside trusted roots: {name}")
        observed = physical.stat(follow_symlinks=False)
        candidates.append(
            (
                name,
                str(physical),
                observed.st_dev,
                observed.st_ino,
                observed.st_size,
                observed.st_mtime_ns,
                observed.st_ctime_ns,
            )
        )
    return _resolve_toolchain_cached(tuple(candidates))


def _utc_from_ns(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _relative_regular_files(root: Path, pattern: str) -> tuple[str, ...]:
    paths: list[str] = []
    for path in root.glob(pattern):
        if path.is_symlink():
            raise VerificationError(f"symlink is forbidden in tested source inventory: {path}")
        if not path.is_file():
            continue
        paths.append(path.relative_to(root).as_posix())
    return tuple(sorted(paths))


def discover_inventory(repo_root: Path) -> Inventory:
    """Discover the exact focused surface, with frozen members as a mandatory floor."""

    root = repo_root.resolve(strict=True)
    tests = _relative_regular_files(root, "tests/test_iter135_*.py")
    python_tools = _relative_regular_files(root, f"{EXPERIMENT_REL}/*.py")
    shell_discovered = _relative_regular_files(root, f"{EXPERIMENT_REL}/*.sh")
    forbidden_configs = [
        relative
        for relative in (
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "ruff.toml",
            ".ruff.toml",
            ".shellcheckrc",
            "conftest.py",
        )
        if (root / relative).exists() or (root / relative).is_symlink()
    ]
    for test_root in (root / "tests", root / "engine", root / "method"):
        if test_root.is_dir() and not test_root.is_symlink():
            forbidden_configs.extend(
                path.relative_to(root).as_posix()
                for path in test_root.rglob("conftest.py")
                if path.exists() or path.is_symlink()
            )

    missing_tests = sorted(set(REQUIRED_TEST_FILES) - set(tests))
    missing_tools = sorted(set(REQUIRED_PYTHON_TOOL_FILES) - set(python_tools))
    missing_shell = sorted(set(REQUIRED_SHELL_FILES) - set(shell_discovered))
    unexpected_shell = sorted(set(shell_discovered) - set(REQUIRED_SHELL_FILES))
    missing_data = sorted(
        rel for rel in REQUIRED_DATA_FILES if not (root / rel).is_file() or (root / rel).is_symlink()
    )
    missing_controls = sorted(
        rel
        for rel in REQUIRED_CONTROL_FILES
        if not (root / rel).is_file() or (root / rel).is_symlink()
    )
    if missing_tests:
        raise VerificationError(f"required focused tests missing: {missing_tests}")
    if missing_tools:
        raise VerificationError(f"required Python tooling missing: {missing_tools}")
    if missing_shell:
        raise VerificationError(f"required shell tooling missing: {missing_shell}")
    if unexpected_shell:
        raise VerificationError(f"unreviewed Iter135 shell tooling present: {unexpected_shell}")
    if missing_data:
        raise VerificationError(f"required tooling data missing: {missing_data}")
    if missing_controls:
        raise VerificationError(f"required control files missing: {missing_controls}")
    if forbidden_configs:
        raise VerificationError(
            f"unbound command-influencing configuration present: {sorted(forbidden_configs)}"
        )

    inventory = Inventory(
        tests=tests,
        python_tools=python_tools,
        shell_files=tuple(sorted(REQUIRED_SHELL_FILES)),
        data_files=tuple(sorted(REQUIRED_DATA_FILES)),
        control_files=tuple(sorted(REQUIRED_CONTROL_FILES)),
    )
    if RECEIPT_REL in inventory.tested_files:
        raise VerificationError("receipt output entered tested-source inventory")
    if len(inventory.tested_files) != len(set(inventory.tested_files)):
        raise VerificationError("duplicate tested-source inventory member")
    return inventory


def _fingerprint_file(repo_root: Path, relative_path: str) -> FileFingerprint:
    root = repo_root.resolve(strict=True)
    path = root / relative_path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise VerificationError(f"tested source unavailable: {relative_path}") from exc
    if resolved != path.absolute():
        raise VerificationError(f"tested source traverses a symlink: {relative_path}")
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"tested source escapes repository: {relative_path}") from exc

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise VerificationError(f"cannot open tested source: {relative_path}") from exc
    digest = hashlib.sha256()
    byte_count = 0
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise VerificationError(f"tested source is not regular: {relative_path}")
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    final_path = path.lstat()
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    identity_path = (
        final_path.st_dev,
        final_path.st_ino,
        final_path.st_mode,
        final_path.st_size,
        final_path.st_mtime_ns,
        final_path.st_ctime_ns,
    )
    if identity_before != identity_after or identity_after != identity_path:
        raise VerificationError(f"tested source changed while hashing: {relative_path}")
    if byte_count != after.st_size:
        raise VerificationError(f"tested source byte count raced: {relative_path}")
    return FileFingerprint(
        sha256=digest.hexdigest(),
        bytes=byte_count,
        device=after.st_dev,
        inode=after.st_ino,
        mode=after.st_mode,
        mtime_ns=after.st_mtime_ns,
        ctime_ns=after.st_ctime_ns,
    )


def snapshot_files(repo_root: Path, relative_paths: Sequence[str]) -> dict[str, FileFingerprint]:
    return {rel: _fingerprint_file(repo_root, rel) for rel in sorted(relative_paths)}


def _snapshot_public(snapshot: Mapping[str, FileFingerprint]) -> dict[str, Any]:
    return {rel: value.public() for rel, value in sorted(snapshot.items())}


def _content_projection(snapshot: Mapping[str, FileFingerprint]) -> dict[str, Any]:
    return {
        rel: {"sha256": value.sha256, "bytes": value.bytes}
        for rel, value in sorted(snapshot.items())
    }


def build_commands(
    inventory: Inventory,
    toolchain: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return the canonical, shell-free command contract in execution order."""

    tools = toolchain or resolve_toolchain()
    return (
        (str(tools["pytest"]["path"]), "-q", *inventory.tests),
        (str(tools["bash"]["path"]), "-n", "--", inventory.shell_files[0]),
        (str(tools["bash"]["path"]), "-n", "--", inventory.shell_files[1]),
        (
            str(tools["shellcheck"]["path"]),
            "--rcfile",
            "/dev/null",
            "--",
            *inventory.shell_files,
        ),
        (str(tools["ruff"]["path"]), "check", "."),
        (str(tools["pytest"]["path"]), "-q"),
        (str(tools["python3"]["path"]), "scripts/validate_docs.py"),
        (str(tools["python3"]["path"]), "scripts/mission_state.py"),
    )


def default_runner(command: tuple[str, ...], cwd: Path) -> RawCommandResult:
    toolchain = resolve_toolchain()
    try:
        completed = subprocess.run(  # noqa: S603 - command is a frozen argv tuple, never a shell
            command,
            cwd=cwd,
            env=_sanitized_environment(toolchain),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3_600,
        )
    except subprocess.TimeoutExpired as exc:
        return RawCommandResult(
            returncode=124,
            stdout=exc.stdout or b"",
            stderr=exc.stderr or b"",
        )
    return RawCommandResult(completed.returncode, completed.stdout, completed.stderr)


def _git_bytes(repo_root: Path, argv: Sequence[str]) -> bytes:
    toolchain = resolve_toolchain()
    completed = subprocess.run(  # noqa: S603 - fixed git command and validated source paths
        (toolchain["git"]["path"], "-C", str(repo_root), *argv),
        env=_sanitized_environment(toolchain),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"Git provenance command failed with return code {completed.returncode}"
        )
    return completed.stdout


def default_git_probe(repo_root: Path, relative_paths: tuple[str, ...]) -> GitState:
    head_raw = _git_bytes(repo_root, ("rev-parse", "--verify", "HEAD"))
    head = head_raw.decode("ascii", errors="strict").strip()
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise VerificationError("Git HEAD is not a lowercase 40-hex commit")
    branch = _git_bytes(repo_root, ("symbolic-ref", "--quiet", "--short", "HEAD")).decode(
        "utf-8", errors="strict"
    ).strip()
    upstream = _git_bytes(
        repo_root, ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    ).decode("utf-8", errors="strict").strip()
    upstream_head = _git_bytes(repo_root, ("rev-parse", "--verify", "@{u}")).decode(
        "ascii", errors="strict"
    ).strip()
    if len(upstream_head) != 40 or any(
        character not in "0123456789abcdef" for character in upstream_head
    ):
        raise VerificationError("Git upstream HEAD is not a lowercase 40-hex commit")
    parent_fields = _git_bytes(repo_root, ("rev-list", "--parents", "-n", "1", "HEAD")).decode(
        "ascii", errors="strict"
    ).strip().split()
    if not parent_fields or parent_fields[0] != head:
        raise VerificationError("Git parent receipt does not start with HEAD")
    parents = tuple(parent_fields[1:])
    commit_paths = tuple(
        sorted(
            field.decode("utf-8", errors="surrogateescape")
            for field in _git_bytes(
                repo_root,
                (
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "-z",
                    "HEAD",
                ),
            ).split(b"\0")
            if field
        )
    )
    del relative_paths
    status = _git_bytes(
        repo_root,
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
    )
    entries = tuple(
        field.decode("utf-8", errors="surrogateescape")
        for field in status.split(b"\0")
        if field
    )
    return GitState(
        head=head,
        dirty_entries=entries,
        porcelain_sha256=_sha256_bytes(status),
        branch=branch,
        upstream=upstream,
        upstream_head=upstream_head,
        parents=parents,
        commit_paths=commit_paths,
    )


def default_ancestry_probe(repo_root: Path, ancestor: str, descendant: str) -> bool:
    """Return whether ANCESTOR is reachable from DESCENDANT, failing closed on Git errors."""

    toolchain = resolve_toolchain()
    completed = subprocess.run(  # noqa: S603 - commits are validated lowercase 40-hex IDs
        (
            toolchain["git"]["path"],
            "-C",
            str(repo_root),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ),
        env=_sanitized_environment(toolchain),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise VerificationError(
        f"Git ancestry command failed with return code {completed.returncode}"
    )


def _to_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="surrogateescape")
    raise TypeError(f"command stream has unsupported type {type(value).__name__}")


def _command_record(command: tuple[str, ...], runner: Runner, cwd: Path) -> dict[str, Any]:
    error_type: str | None = None
    try:
        result = runner(command, cwd)
        returncode = int(result.returncode)
        stdout = _to_bytes(result.stdout)
        stderr = _to_bytes(result.stderr)
    except Exception as exc:  # fail closed while retaining no exception/log plaintext
        error_type = type(exc).__name__
        returncode = 125
        stdout = b""
        stderr = str(exc).encode("utf-8", errors="replace")
    record = {
        "argv": list(command),
        "return_code": returncode,
        "stdout_bytes": len(stdout),
        "stdout_sha256": _sha256_bytes(stdout),
        "stderr_bytes": len(stderr),
        "stderr_sha256": _sha256_bytes(stderr),
    }
    if error_type is not None:
        record["runner_error_type"] = error_type
    return record


def _problem(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _inventory_digest(inventory: Inventory) -> str:
    return _sha256_bytes(_canonical_json(inventory.as_dict()))


def _snapshot_digest(snapshot: Mapping[str, FileFingerprint]) -> str:
    return _sha256_bytes(_canonical_json(_content_projection(snapshot)))


def _changed_paths(
    initial: Mapping[str, FileFingerprint], current: Mapping[str, FileFingerprint]
) -> list[str]:
    return sorted(
        rel
        for rel in set(initial) | set(current)
        if initial.get(rel) != current.get(rel)
    )


def run_verification(
    repo_root: Path = REPO_ROOT,
    *,
    runner: Runner = default_runner,
    git_probe: GitProbe = default_git_probe,
    wall_clock_ns: Clock = time.time_ns,
    monotonic_clock_ns: Clock = time.monotonic_ns,
) -> dict[str, Any]:
    """Run the complete receipt pipeline and return the in-memory receipt."""

    root = repo_root.resolve(strict=True)
    wall_start = wall_clock_ns()
    monotonic_start = monotonic_clock_ns()
    problems: list[dict[str, str]] = []
    commands: list[dict[str, Any]] = []

    try:
        toolchain = resolve_toolchain()
        inventory = discover_inventory(root)
        initial = snapshot_files(root, inventory.tested_files)
        # Close discovery-to-snapshot races before any validation command executes.
        if discover_inventory(root) != inventory:
            raise VerificationError("focused inventory changed during initial snapshot")
        if snapshot_files(root, inventory.tested_files) != initial:
            raise VerificationError("tested sources changed during initial snapshot")
        git_start = git_probe(root, inventory.tested_files)
    except Exception as exc:
        problems.append(_problem("INITIALIZATION_FAILED", f"{type(exc).__name__}: {exc}"))
        inventory = Inventory((), (), (), (), ())
        initial = {}
        toolchain = {}
        git_start = GitState("", (), _sha256_bytes(b""))

    command_contract = (
        build_commands(inventory, toolchain) if inventory.tested_files and toolchain else ()
    )

    if git_start.dirty_entries or git_start.porcelain_sha256 != _sha256_bytes(b""):
        problems.append(
            _problem(
                "GIT_REPOSITORY_DIRTY_START",
                "repository was not globally clean before verification",
            )
        )
    if git_start.branch != "master":
        problems.append(_problem("GIT_BRANCH", f"expected master, observed {git_start.branch!r}"))
    if git_start.upstream != "origin/master":
        problems.append(
            _problem("GIT_UPSTREAM", f"expected origin/master, observed {git_start.upstream!r}")
        )
    if git_start.upstream_head != git_start.head:
        problems.append(
            _problem("SOURCE_NOT_PUSHED", "source HEAD does not equal the frozen upstream HEAD")
        )
    if git_start.parents != (EXPECTED_PREREGISTRATION_HEAD,):
        problems.append(
            _problem(
                "SOURCE_PARENT",
                "source HEAD is not the direct child of the final preregistration amendment",
            )
        )
    if git_start.commit_paths != tuple(sorted(EXPECTED_SOURCE_COMMIT_PATHS)):
        problems.append(
            _problem(
                "SOURCE_COMMIT_SCOPE",
                "source HEAD path set is not the exact frozen source-only publication set",
            )
        )

    def checkpoint(label: str) -> bool:
        try:
            observed_inventory = discover_inventory(root)
            if observed_inventory != inventory:
                expected = set(inventory.tested_files)
                observed = set(observed_inventory.tested_files)
                problems.append(
                    _problem(
                        "INVENTORY_DRIFT",
                        f"{label}: added={sorted(observed - expected)} removed={sorted(expected - observed)}",
                    )
                )
                return False
            if resolve_toolchain() != toolchain:
                problems.append(_problem("TOOLCHAIN_DRIFT", f"{label}: executable receipt changed"))
                return False
            observed_git = git_probe(root, inventory.tested_files)
            if observed_git != git_start:
                problems.append(_problem("GIT_STATE_DRIFT", f"{label}: Git state changed"))
                return False
            observed = snapshot_files(root, inventory.tested_files)
            changed = _changed_paths(initial, observed)
            if changed:
                problems.append(_problem("TESTED_FILE_DRIFT", f"{label}: {changed}"))
                return False
            return True
        except Exception as exc:
            problems.append(
                _problem("CHECKPOINT_FAILED", f"{label}: {type(exc).__name__}: {exc}")
            )
            return False

    if not problems:
        for index, command in enumerate(command_contract):
            if not checkpoint(f"before_command_{index}"):
                break
            record = _command_record(command, runner, root)
            commands.append(record)
            if record["return_code"] != 0:
                problems.append(
                    _problem(
                        "COMMAND_FAILED",
                        f"command_{index} returned {record['return_code']}",
                    )
                )
            if not checkpoint(f"after_command_{index}"):
                break

    # The final probes run even after a command failure; a drifted surface can never be green.
    checkpoint("final") if inventory.tested_files else None
    try:
        final = snapshot_files(root, inventory.tested_files) if inventory.tested_files else {}
    except Exception as exc:
        problems.append(_problem("FINAL_SNAPSHOT_FAILED", f"{type(exc).__name__}: {exc}"))
        final = {}
    try:
        git_end = git_probe(root, inventory.tested_files) if inventory.tested_files else git_start
    except Exception as exc:
        problems.append(_problem("FINAL_GIT_PROBE_FAILED", f"{type(exc).__name__}: {exc}"))
        git_end = GitState("", (), _sha256_bytes(b""))

    if git_start.head != git_end.head:
        problems.append(_problem("GIT_HEAD_DRIFT", "Git HEAD changed during verification"))
    if git_start != git_end:
        problems.append(_problem("GIT_STATE_DRIFT", "Git publication state changed during verification"))
    if git_end.dirty_entries or git_end.porcelain_sha256 != _sha256_bytes(b""):
        problems.append(
            _problem(
                "GIT_REPOSITORY_DIRTY_END",
                "repository was not globally clean at verification end",
            )
        )
    if git_start.dirty_entries != git_end.dirty_entries:
        problems.append(
            _problem("GIT_DIRTY_STATE_DRIFT", "repository dirty state changed during verification")
        )
    if initial != final:
        changed = _changed_paths(initial, final)
        marker = _problem("FINAL_TESTED_FILE_DRIFT", f"changed={changed}")
        if marker not in problems:
            problems.append(marker)
    if len(commands) != len(command_contract):
        problems.append(
            _problem(
                "COMMAND_SET_INCOMPLETE",
                f"executed={len(commands)} expected={len(command_contract)}",
            )
        )

    monotonic_end = monotonic_clock_ns()
    wall_end = wall_clock_ns()
    if monotonic_end < monotonic_start:
        problems.append(_problem("MONOTONIC_CLOCK_REGRESSED", "monotonic duration is negative"))
    if wall_end < wall_start:
        problems.append(_problem("WALL_CLOCK_REGRESSED", "wall duration is negative"))

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "verdict": OK_VERDICT if not problems else FAIL_VERDICT,
        "problem_count": len(problems),
        "problems": problems,
        "repository": {
            "root": str(root),
            "git_start": git_start.as_dict(),
            "git_end": git_end.as_dict(),
            "git_head_stable": git_start.head == git_end.head,
            "git_state_stable": git_start == git_end,
            "repository_clean_state_stable": (
                not git_start.dirty_entries
                and git_start.porcelain_sha256 == _sha256_bytes(b"")
                and git_start == git_end
            ),
        },
        "inventory": inventory.as_dict(),
        "inventory_sha256": _inventory_digest(inventory),
        "toolchain": toolchain,
        "environment_contract": _sanitized_environment(toolchain) if toolchain else {},
        "files": _snapshot_public(initial),
        "file_content_set_sha256": _snapshot_digest(initial),
        "command_contract": [list(command) for command in command_contract],
        "commands": commands,
        "timing": {
            "started_at_utc": _utc_from_ns(wall_start),
            "finished_at_utc": _utc_from_ns(wall_end),
            "wall_duration_ns": max(0, wall_end - wall_start),
            "monotonic_duration_ns": max(0, monotonic_end - monotonic_start),
        },
    }
    receipt["receipt_payload_sha256"] = _sha256_bytes(_canonical_json(receipt))
    return receipt


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(
        character in "0123456789abcdef" for character in value
    )


def _git_commit_row(repo_root: Path, commit: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not _valid_commit(commit):
        raise VerificationError("publication commit is not lowercase 40-hex")
    parent_fields = _git_bytes(
        repo_root, ("rev-list", "--parents", "-n", "1", commit)
    ).decode("ascii", errors="strict").strip().split()
    if not parent_fields or parent_fields[0] != commit:
        raise VerificationError("publication parent row does not start with requested commit")
    parents = tuple(parent_fields[1:])
    paths = tuple(
        sorted(
            field.decode("utf-8", errors="surrogateescape")
            for field in _git_bytes(
                repo_root,
                (
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "-z",
                    commit,
                ),
            ).split(b"\0")
            if field
        )
    )
    return parents, paths


def _git_file_bytes(repo_root: Path, commit: str, relative_path: str) -> bytes:
    if not _valid_commit(commit):
        raise VerificationError("publication file commit is malformed")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative_path:
        raise VerificationError(f"publication file path is unsafe: {relative_path!r}")
    return _git_bytes(
        repo_root,
        ("show", "--no-ext-diff", "--no-textconv", f"{commit}:{relative_path}"),
    )


def _source_inventory_from_tree(repo_root: Path, source_commit: str) -> Inventory:
    tree_paths = {
        field.decode("utf-8", errors="surrogateescape")
        for field in _git_bytes(
            repo_root,
            ("ls-tree", "-r", "-z", "--name-only", source_commit),
        ).split(b"\0")
        if field
    }
    tests = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == "tests"
            and PurePosixPath(path).match("test_iter135_*.py")
        )
    )
    python_tools = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == EXPERIMENT_REL
            and PurePosixPath(path).suffix == ".py"
        )
    )
    shell_files = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == EXPERIMENT_REL
            and PurePosixPath(path).suffix == ".sh"
        )
    )
    missing = sorted(
        (
            set(REQUIRED_TEST_FILES)
            | set(REQUIRED_PYTHON_TOOL_FILES)
            | set(REQUIRED_SHELL_FILES)
            | set(REQUIRED_DATA_FILES)
            | set(REQUIRED_CONTROL_FILES)
        )
        - tree_paths
    )
    if missing:
        raise VerificationError(f"published source tree is missing frozen files: {missing}")
    if shell_files != tuple(sorted(REQUIRED_SHELL_FILES)):
        raise VerificationError("published source tree has an unreviewed shell-file set")
    forbidden = {
        path
        for path in tree_paths
        if path
        in {
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "ruff.toml",
            ".ruff.toml",
            ".shellcheckrc",
            "conftest.py",
        }
        or (
            path.endswith("/conftest.py")
            and path.split("/", 1)[0] in {"tests", "engine", "method"}
        )
    }
    if forbidden:
        raise VerificationError(
            f"published source tree has unbound command configuration: {sorted(forbidden)}"
        )
    return Inventory(
        tests=tests,
        python_tools=python_tools,
        shell_files=shell_files,
        data_files=tuple(sorted(REQUIRED_DATA_FILES)),
        control_files=tuple(sorted(REQUIRED_CONTROL_FILES)),
    )


def _read_stable_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path.absolute():
        raise VerificationError(f"publication receipt is not a physical regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.stat(follow_symlinks=False)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    identity_path = (
        final.st_dev,
        final.st_ino,
        final.st_mode,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    )
    payload = b"".join(chunks)
    if identity_before != identity_after or identity_after != identity_path:
        raise VerificationError("publication receipt changed while reading")
    if not stat.S_ISREG(after.st_mode) or len(payload) != after.st_size:
        raise VerificationError("publication receipt byte count or type is invalid")
    return payload


def _linear_publication_chain(
    repo_root: Path, ancestor: str, descendant: str
) -> list[tuple[str, tuple[str, ...]]]:
    reverse_chain: list[tuple[str, tuple[str, ...]]] = []
    cursor = descendant
    for _ in range(1_000):
        if cursor == ancestor:
            return list(reversed(reverse_chain))
        parents, paths = _git_commit_row(repo_root, cursor)
        if len(parents) != 1:
            raise VerificationError("publication chain is not linear")
        reverse_chain.append((cursor, paths))
        cursor = parents[0]
    raise VerificationError("publication chain exceeded the bounded history walk")


def _post_freeze_path_allowed(relative_path: str) -> bool:
    return relative_path in POST_FREEZE_EXACT_PATHS or relative_path.startswith(
        POST_FREEZE_PATH_PREFIXES
    )


def validate_published_receipt_structure(
    receipt: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    *,
    git_probe: GitProbe = default_git_probe,
    ancestry_probe: AncestryProbe = default_ancestry_probe,
) -> list[str]:
    """Validate the immutable H/H+1 receipt proof after state-only descendants exist.

    Independent command replay is deliberately performed at the exact receipt-only H+1 commit by
    :func:`validate_receipt`.  This post-transition validator instead proves that the committed
    receipt still binds the exact published source tree and that every later commit follows the
    narrow state/baton/preflight-artifact topology without changing frozen tooling.
    """

    errors: list[str] = []
    if receipt.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if receipt.get("verdict") != OK_VERDICT:
        errors.append("receipt verdict is not green")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        errors.append("receipt problem metadata is not exactly green")
    payload = dict(receipt)
    claimed_payload_hash = payload.pop("receipt_payload_sha256", None)
    if claimed_payload_hash != _sha256_bytes(_canonical_json(payload)):
        errors.append("receipt payload digest mismatch")

    try:
        root = repo_root.resolve(strict=True)
        repository = receipt.get("repository")
        if not isinstance(repository, Mapping) or repository.get("root") != str(root):
            raise VerificationError("receipt repository root is malformed")
        claimed_start = repository.get("git_start")
        claimed_end = repository.get("git_end")
        if not isinstance(claimed_start, Mapping) or claimed_start != claimed_end:
            raise VerificationError("receipt source Git state was not stable")
        source_commit = claimed_start.get("head")
        if not _valid_commit(source_commit):
            raise VerificationError("receipt source commit is malformed")
        empty_status = _sha256_bytes(b"")
        expected_source_paths = tuple(sorted(EXPECTED_SOURCE_COMMIT_PATHS))
        if (
            claimed_start.get("dirty_entries") != []
            or claimed_start.get("porcelain_v1_z_sha256") != empty_status
            or claimed_start.get("branch") != "master"
            or claimed_start.get("upstream") != "origin/master"
            or claimed_start.get("upstream_head") != source_commit
            or claimed_start.get("parents") != [EXPECTED_PREREGISTRATION_HEAD]
            or claimed_start.get("commit_paths") != list(expected_source_paths)
        ):
            raise VerificationError("receipt source publication claim is malformed")
        if (
            repository.get("git_head_stable") is not True
            or repository.get("git_state_stable") is not True
            or repository.get("repository_clean_state_stable") is not True
        ):
            raise VerificationError("receipt repository stability flags are not green")

        source_parents, source_paths = _git_commit_row(root, source_commit)
        if source_parents != (EXPECTED_PREREGISTRATION_HEAD,) or source_paths != expected_source_paths:
            raise VerificationError("actual source commit topology or path scope is wrong")

        inventory = _source_inventory_from_tree(root, source_commit)
        if receipt.get("inventory") != inventory.as_dict():
            raise VerificationError("receipt inventory does not match the published source tree")
        if receipt.get("inventory_sha256") != _inventory_digest(inventory):
            raise VerificationError("receipt inventory digest is wrong")
        claimed_files = receipt.get("files")
        if not isinstance(claimed_files, Mapping) or set(claimed_files) != set(
            inventory.tested_files
        ):
            raise VerificationError("receipt file binding set is malformed")
        source_projection: dict[str, dict[str, Any]] = {}
        for relative_path in inventory.tested_files:
            source_bytes = _git_file_bytes(root, source_commit, relative_path)
            projection = {"sha256": _sha256_bytes(source_bytes), "bytes": len(source_bytes)}
            source_projection[relative_path] = projection
            row = claimed_files.get(relative_path)
            if not isinstance(row, Mapping) or {
                "sha256": row.get("sha256"),
                "bytes": row.get("bytes"),
            } != projection:
                raise VerificationError(
                    f"receipt file binding differs from source commit: {relative_path}"
                )
        if receipt.get("file_content_set_sha256") != _sha256_bytes(
            _canonical_json(source_projection)
        ):
            raise VerificationError("receipt source content-set digest is wrong")

        toolchain = receipt.get("toolchain")
        if not isinstance(toolchain, Mapping) or set(toolchain) != set(TOOL_NAMES):
            raise VerificationError("receipt toolchain set is malformed")
        for name in TOOL_NAMES:
            row = toolchain.get(name)
            if not isinstance(row, Mapping):
                raise VerificationError(f"receipt toolchain row is malformed: {name}")
            path = Path(str(row.get("path", "")))
            digest = row.get("sha256")
            if (
                not path.is_absolute()
                or not _allowed_tool_path(path)
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
                or not isinstance(row.get("bytes"), int)
                or not isinstance(row.get("version"), str)
            ):
                raise VerificationError(f"receipt toolchain row is invalid: {name}")
        if receipt.get("environment_contract") != _sanitized_environment(toolchain):
            raise VerificationError("receipt environment contract is malformed")
        expected_commands = build_commands(inventory, toolchain)
        if receipt.get("command_contract") != [list(command) for command in expected_commands]:
            raise VerificationError("receipt command contract is malformed")
        command_rows = receipt.get("commands")
        if not isinstance(command_rows, list) or len(command_rows) != len(expected_commands):
            raise VerificationError("receipt command result set is incomplete")
        for index, (row, command) in enumerate(zip(command_rows, expected_commands)):
            if (
                not isinstance(row, Mapping)
                or row.get("argv") != list(command)
                or row.get("return_code") != 0
            ):
                raise VerificationError(f"receipt command result is not green: {index}")

        history_raw = _git_bytes(root, ("log", "--format=%H", "--", RECEIPT_REL))
        receipt_history = tuple(
            line for line in history_raw.decode("ascii", errors="strict").splitlines() if line
        )
        if len(receipt_history) != 1 or not _valid_commit(receipt_history[0]):
            raise VerificationError("canonical receipt does not have exactly one history commit")
        receipt_commit = receipt_history[0]
        receipt_parents, receipt_paths = _git_commit_row(root, receipt_commit)
        if receipt_parents != (source_commit,) or receipt_paths != (RECEIPT_REL,):
            raise VerificationError("receipt commit is not the exact receipt-only H+1")

        receipt_path = root / RECEIPT_REL
        current_receipt_bytes = _read_stable_regular_file(receipt_path)
        if _git_file_bytes(root, receipt_commit, RECEIPT_REL) != current_receipt_bytes:
            raise VerificationError("canonical receipt bytes differ from committed H+1 bytes")
        committed_receipt = json.loads(current_receipt_bytes.decode("utf-8"))
        if committed_receipt != dict(receipt):
            raise VerificationError("supplied receipt differs from the committed canonical receipt")

        current_git = git_probe(root, inventory.tested_files)
        if current_git.dirty_entries or current_git.porcelain_sha256 != empty_status:
            raise VerificationError("current repository is dirty")
        if current_git.branch != "master" or current_git.upstream != "origin/master":
            raise VerificationError("current publication branch/upstream is wrong")
        if not ancestry_probe(root, receipt_commit, current_git.head):
            raise VerificationError("receipt H+1 is not an ancestor of current HEAD")
        if not ancestry_probe(root, receipt_commit, current_git.upstream_head):
            raise VerificationError("receipt H+1 is not published on origin/master")
        if current_git.upstream_head != current_git.head and not ancestry_probe(
            root, current_git.upstream_head, current_git.head
        ):
            raise VerificationError("origin/master is not an ancestor of current HEAD")

        chain = _linear_publication_chain(root, receipt_commit, current_git.head)
        if not chain or chain[0][1] != ("MISSION_STATE.json",):
            raise VerificationError("state-only H+2 is missing or has the wrong path scope")
        if len(chain) >= 2 and chain[1][1] != ("CONTINUITY.md", "HANDOFF.md"):
            raise VerificationError("offline baton H+3 has the wrong path scope")
        if len(chain) > 2:
            for commit, paths in chain[2:]:
                rejected = [path for path in paths if not _post_freeze_path_allowed(path)]
                if rejected:
                    raise VerificationError(
                        f"post-freeze commit {commit} changed unauthorized paths: {rejected}"
                    )
    except Exception as exc:
        errors.append(f"published receipt structure invalid: {type(exc).__name__}: {exc}")
    return errors


def validate_receipt(
    receipt: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    *,
    runner: Runner = default_runner,
    git_probe: GitProbe = default_git_probe,
    ancestry_probe: AncestryProbe = default_ancestry_probe,
) -> list[str]:
    """Replay every command and non-command claim against the current repository bytes."""

    errors: list[str] = []
    if receipt.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if receipt.get("verdict") != OK_VERDICT:
        errors.append("receipt verdict is not green")
    problems = receipt.get("problems")
    if not isinstance(problems, list) or problems:
        errors.append("receipt contains problems or malformed problem list")
    if receipt.get("problem_count") != 0:
        errors.append("problem_count is not zero")

    payload = dict(receipt)
    claimed_payload_hash = payload.pop("receipt_payload_sha256", None)
    if claimed_payload_hash != _sha256_bytes(_canonical_json(payload)):
        errors.append("receipt payload digest mismatch")

    try:
        root = repo_root.resolve(strict=True)
        current_toolchain = resolve_toolchain()
        inventory = discover_inventory(root)
        if receipt.get("repository", {}).get("root") != str(root):
            errors.append("repository root mismatch")
        if receipt.get("inventory") != inventory.as_dict():
            errors.append("focused inventory mismatch")
        if receipt.get("inventory_sha256") != _inventory_digest(inventory):
            errors.append("inventory digest mismatch")
        if receipt.get("toolchain") != current_toolchain:
            errors.append("toolchain receipt mismatch")
        if receipt.get("environment_contract") != _sanitized_environment(current_toolchain):
            errors.append("sanitized environment contract mismatch")

        current = snapshot_files(root, inventory.tested_files)
        claimed_files = receipt.get("files")
        if not isinstance(claimed_files, Mapping):
            errors.append("file binding map malformed")
        else:
            claimed_content = {
                rel: {
                    "sha256": value.get("sha256") if isinstance(value, Mapping) else None,
                    "bytes": value.get("bytes") if isinstance(value, Mapping) else None,
                }
                for rel, value in claimed_files.items()
            }
            if claimed_content != _content_projection(current):
                errors.append("tested source content is stale or forged")
        if receipt.get("file_content_set_sha256") != _snapshot_digest(current):
            errors.append("file content-set digest mismatch")

        empty_status_sha256 = _sha256_bytes(b"")
        replay_git_start = git_probe(root, inventory.tested_files)
        replay_allowed = not replay_git_start.dirty_entries and (
            replay_git_start.porcelain_sha256 == empty_status_sha256
        )
        if not replay_allowed:
            errors.append("current repository is dirty before command replay")

        expected_commands = build_commands(inventory, current_toolchain)
        if receipt.get("command_contract") != [list(command) for command in expected_commands]:
            errors.append("command contract mismatch")
        command_records = receipt.get("commands")
        if not isinstance(command_records, list) or len(command_records) != len(expected_commands):
            errors.append("executed command set incomplete")
        else:
            for index, (record, expected) in enumerate(zip(command_records, expected_commands)):
                if not isinstance(record, Mapping):
                    errors.append(f"command_{index} record malformed")
                    continue
                if record.get("argv") != list(expected):
                    errors.append(f"command_{index} argv mismatch")
                if record.get("return_code") != 0:
                    errors.append(f"command_{index} did not succeed")
                for stream in ("stdout", "stderr"):
                    digest = record.get(f"{stream}_sha256")
                    byte_count = record.get(f"{stream}_bytes")
                    if not isinstance(digest, str) or len(digest) != 64:
                        errors.append(f"command_{index} {stream} digest malformed")
                    elif any(char not in "0123456789abcdef" for char in digest):
                        errors.append(f"command_{index} {stream} digest malformed")
                    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
                        errors.append(f"command_{index} {stream} byte count malformed")

        # A receipt payload hash is an integrity check, not an authenticity primitive. Never trust
        # its recorded return codes as proof that the commands succeeded: independently execute the
        # exact frozen argv against the exact bound bytes. Stream hashes remain historical metadata
        # because pytest elapsed-time text and tool warnings are not deterministic across replays.
        for index, expected in enumerate(expected_commands if replay_allowed else ()):
            if discover_inventory(root) != inventory or snapshot_files(
                root, inventory.tested_files
            ) != current:
                errors.append(f"command_{index} pre-replay source drift")
                break
            if resolve_toolchain() != current_toolchain:
                errors.append(f"command_{index} pre-replay toolchain drift")
                break
            if git_probe(root, inventory.tested_files) != replay_git_start:
                errors.append(f"command_{index} pre-replay Git drift")
                break
            replay = _command_record(expected, runner, root)
            if replay["return_code"] != 0:
                errors.append(f"command_{index} independent replay failed")
            if discover_inventory(root) != inventory or snapshot_files(
                root, inventory.tested_files
            ) != current:
                errors.append(f"command_{index} post-replay source drift")
                break
            if git_probe(root, inventory.tested_files) != replay_git_start:
                errors.append(f"command_{index} post-replay Git drift")
                break
            if resolve_toolchain() != current_toolchain:
                errors.append(f"command_{index} post-replay toolchain drift")
                break

        repository = receipt.get("repository", {})
        git_start = repository.get("git_start")
        git_end = repository.get("git_end")
        if not isinstance(git_start, Mapping) or not isinstance(git_end, Mapping):
            errors.append("claimed Git provenance is malformed")
            claimed_head = ""
        else:
            claimed_head = git_end.get("head")
            if git_start != git_end:
                errors.append("claimed tested Git states differ")
            if git_start.get("head") != claimed_head:
                errors.append("claimed repository Git HEAD was not stable")
            for label, state in (("start", git_start), ("end", git_end)):
                if state.get("dirty_entries") != []:
                    errors.append(f"claimed repository was dirty at {label}")
                if state.get("porcelain_v1_z_sha256") != empty_status_sha256:
                    errors.append(f"claimed repository status digest was not empty at {label}")
                if state.get("branch") != "master":
                    errors.append(f"claimed source branch was not master at {label}")
                if state.get("upstream") != "origin/master":
                    errors.append(f"claimed source upstream was not origin/master at {label}")
                if state.get("upstream_head") != state.get("head"):
                    errors.append(f"claimed source commit was not pushed at {label}")
                if state.get("parents") != [EXPECTED_PREREGISTRATION_HEAD]:
                    errors.append(f"claimed source parent mismatch at {label}")
                if state.get("commit_paths") != sorted(EXPECTED_SOURCE_COMMIT_PATHS):
                    errors.append(f"claimed source commit scope mismatch at {label}")
            if not isinstance(claimed_head, str) or len(claimed_head) != 40 or any(
                char not in "0123456789abcdef" for char in claimed_head
            ):
                errors.append("claimed tested Git HEAD is malformed")
                claimed_head = ""

        current_git = git_probe(root, inventory.tested_files)
        if current_git != replay_git_start:
            errors.append("repository Git state changed during command replay")
        if current_git.dirty_entries or current_git.porcelain_sha256 != empty_status_sha256:
            errors.append("current repository is dirty")
        current_head_valid = len(current_git.head) == 40 and all(
            char in "0123456789abcdef" for char in current_git.head
        )
        if not current_head_valid:
            errors.append("current Git HEAD is malformed")
        elif (
            claimed_head
            and claimed_head != current_git.head
            and not ancestry_probe(root, claimed_head, current_git.head)
        ):
            errors.append("claimed tested Git HEAD is not an ancestor of current HEAD")
        if current_git.branch != "master":
            errors.append("current branch is not master")
        if current_git.upstream != "origin/master":
            errors.append("current upstream is not origin/master")
        if current_git.upstream_head not in {claimed_head, current_git.head}:
            errors.append("current receipt commit is neither exact pre-push nor pushed topology")
        if claimed_head and claimed_head != current_git.head:
            if current_git.parents != (claimed_head,):
                errors.append("receipt commit is not the direct child of the source commit")
            if current_git.commit_paths != (RECEIPT_REL,):
                errors.append("receipt commit changed paths beyond the canonical receipt")
        if repository.get("git_head_stable") is not True:
            errors.append("Git HEAD was not stable")
        if repository.get("git_state_stable") is not True:
            errors.append("Git publication state was not stable")
        if repository.get("repository_clean_state_stable") is not True:
            errors.append("repository clean state was not stable")
    except Exception as exc:
        errors.append(f"validation probe failed: {type(exc).__name__}: {exc}")

    timing = receipt.get("timing")
    if not isinstance(timing, Mapping):
        errors.append("timing block malformed")
    else:
        for key in ("wall_duration_ns", "monotonic_duration_ns"):
            value = timing.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{key} malformed")
    return errors


def write_json_atomic(output: Path, payload: Mapping[str, Any]) -> None:
    """Durably replace OUTPUT with canonical JSON, never following an output symlink."""

    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise VerificationError(f"refusing symlink receipt output: {output}")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        directory_fd = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def run_and_write_verification(
    output: Path = DEFAULT_RECEIPT,
    repo_root: Path = REPO_ROOT,
    **kwargs: Any,
) -> dict[str, Any]:
    output_abs = output.absolute()
    try:
        output_rel = output_abs.relative_to(repo_root.resolve(strict=True)).as_posix()
    except ValueError:
        output_rel = None
    if output_rel is not None and output_rel != RECEIPT_REL:
        raise VerificationError("in-repository receipt output must use the canonical receipt path")
    receipt = run_verification(repo_root, **kwargs)
    write_json_atomic(output_abs, receipt)
    return receipt


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument(
        "--verify-receipt",
        type=Path,
        help="validate an existing green receipt against current files instead of running tools",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.verify_receipt is not None:
        try:
            receipt = json.loads(args.verify_receipt.read_text(encoding="utf-8"))
            errors = validate_receipt(receipt)
        except Exception as exc:
            errors = [f"receipt read failed: {type(exc).__name__}: {exc}"]
        print(OK_VERDICT if not errors else FAIL_VERDICT)
        if errors:
            print(f"problem_count={len(errors)}")
        return 0 if not errors else 2

    try:
        receipt = run_and_write_verification(args.output)
    except Exception as exc:
        print(f"{FAIL_VERDICT}: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(receipt["verdict"])
    print(f"problem_count={receipt['problem_count']}")
    print(f"receipt={args.output.absolute()}")
    return 0 if receipt["verdict"] == OK_VERDICT else 2


if __name__ == "__main__":
    raise SystemExit(main())
