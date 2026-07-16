#!/usr/bin/env python3
"""Capture the fail-closed Iteration-135 execution-host environment receipt.

This command is read-only except for one atomic replacement of ``env_receipts.json``.  It does not
prepare the host: it never creates the output root, resets Git, patches compose, removes containers,
starts Docker, or touches the GPU.  Run it only after those explicitly authorized preparation steps
have completed.

The local-free value is deliberately an operator-supplied integer.  The execution host cannot
measure the evidence-collection filesystem on the operator's Mac, and this tool will not pretend it
can.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import types
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CANONICAL_MANIFEST_PATH = HERE / "make_launch_manifest.py"
CANONICAL_PATCHER_PATH = HERE / "patch_compose_dose_env.py"
DEFAULT_OUTPUT = HERE / "env_receipts.json"
INCOMPLETE_VERDICT = "I135_ENVIRONMENT_PREFLIGHT_INCOMPLETE"

EXPECTED_HOST = "sentinel-gpu"
EXPECTED_GPU_MODEL = "NVIDIA L4"
EXPECTED_GPU_UUID = "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07"
EXPECTED_GPU_DRIVER = "580.159.03"
EXPECTED_GPU_MEMORY_MIB = 23_034
EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256 = (
    "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REPO_DIGEST_RE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
_GPU_UUID_RE = re.compile(r"^GPU-[0-9a-f-]+$", re.IGNORECASE)
_DRIVER_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")
_EVALUATOR_RE = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|"
    r"/(?:NeuroNCAP|neuro-ncap|neuro_ncap)/(?:main\.py|neuro_ncap/)|"
    r"/UniAD/inference/server\.py|nerfstudio/scripts/closed_loop/main\.py)",
    re.IGNORECASE,
)


class CaptureError(RuntimeError):
    """A bounded probe could not produce trustworthy evidence."""


@dataclass(frozen=True)
class Contract:
    schema: str
    ready_verdict: str
    remote_files: Mapping[str, tuple[str, str, int]]
    repositories: Mapping[str, Mapping[str, Any]]
    required_untracked_bindings: Mapping[tuple[str, str], str]
    storage_identity: Mapping[str, Any]
    dataset_schema: str
    dataset_contract_sha256: str
    dataset_root: str
    dataset_version: str
    dataset_archive_root: str
    dataset_metadata_root: str
    dataset_map_root: str
    dataset_mount: Mapping[str, str]
    dataset_proof_basis: Mapping[str, Any]
    dataset_archives: Mapping[str, tuple[str, int]]
    dataset_metadata_files: tuple[str, ...]
    dataset_map_anchors: tuple[str, ...]
    image_ids: Mapping[str, str]
    compose_input_sha256: str
    compose_output_sha256: str
    projected_output_bytes: int
    minimum_remote_free_bytes: int
    minimum_reserve_bytes: int
    minimum_local_free_bytes: int
    host: str = EXPECTED_HOST
    gpu_model: str = EXPECTED_GPU_MODEL
    gpu_uuid: str = EXPECTED_GPU_UUID
    gpu_driver: str = EXPECTED_GPU_DRIVER
    gpu_memory_mib: int = EXPECTED_GPU_MEMORY_MIB


def _run_command(argv: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CaptureError(f"command:{argv[0]}:{type(error).__name__}") from error
    if completed.returncode != 0:
        raise CaptureError(f"command:{argv[0]}:exit-{completed.returncode}")
    return completed.stdout


@dataclass(frozen=True)
class Hooks:
    run: Callable[[Sequence[str]], bytes] = _run_command
    hostname: Callable[[], str] = socket.gethostname
    disk_free: Callable[[Path], int] = lambda path: shutil.disk_usage(path).free
    device: Callable[[Path], int] = lambda path: path.stat().st_dev
    now: Callable[[], datetime] = lambda: datetime.now(UTC)
    pid: Callable[[], int] = os.getpid
    dataset_read: Callable[[Path], tuple[dict[str, Any], list[str]]] = lambda path: (
        _read_dataset_file(path)
    )


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _component_snapshot(path: Path) -> tuple[list[tuple[str, tuple[int, int, int]]], list[str]]:
    problems: list[str] = []
    snapshots: list[tuple[str, tuple[int, int, int]]] = []
    if not path.is_absolute():
        return snapshots, [f"path:not-absolute:{path}"]
    cursor = Path(path.anchor)
    for component in path.parts[1:]:
        cursor /= component
        try:
            info = cursor.lstat()
        except OSError as error:
            problems.append(f"path:lstat:{cursor}:{type(error).__name__}")
            break
        snapshots.append((str(cursor), (info.st_dev, info.st_ino, info.st_mode)))
        if stat.S_ISLNK(info.st_mode):
            problems.append(f"path:symlink:{cursor}")
    return snapshots, problems


def stable_read(
    path: Path,
    *,
    collect_bytes: bool = False,
) -> tuple[dict[str, Any], bytes | None, list[str]]:
    """Read one regular physical file without accepting symlinks or an unstable inode."""

    path = Path(path)
    problems: list[str] = []
    components_before, component_problems = _component_snapshot(path)
    problems.extend(component_problems)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        resolved = None
        problems.append(f"path:resolve:{path}:{type(error).__name__}")
    if resolved is not None and resolved != path:
        problems.append(f"path:realpath:{path}:{resolved}")

    digest = hashlib.sha256()
    chunks: list[bytes] | None = [] if collect_bytes else None
    byte_count: int | None = None
    before: os.stat_result | None = None
    after: os.stat_result | None = None
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            problems.append(f"path:not-regular:{path}")
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
            if chunks is not None:
                chunks.append(chunk)
        after = os.fstat(descriptor)
    except OSError as error:
        problems.append(f"path:read:{path}:{type(error).__name__}")
    finally:
        if descriptor is not None:
            os.close(descriptor)

    if before is not None and after is not None and _stat_identity(before) != _stat_identity(after):
        problems.append(f"path:unstable-file:{path}")
    components_after, after_problems = _component_snapshot(path)
    problems.extend(after_problems)
    if components_before != components_after:
        problems.append(f"path:unstable-components:{path}")
    if before is not None and components_after:
        final = components_after[-1][1]
        if (before.st_dev, before.st_ino, before.st_mode) != final:
            problems.append(f"path:descriptor-mismatch:{path}")

    receipt = {
        "path": str(path),
        "sha256": digest.hexdigest() if byte_count is not None else None,
        "bytes": byte_count,
    }
    data = b"".join(chunks) if chunks is not None and byte_count is not None else None
    return receipt, data, sorted(set(problems))


def _read_dataset_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    receipt, _data, problems = stable_read(path)
    return receipt, problems


def _load_module_from_stable_bytes(path: Path, module_name: str) -> types.ModuleType:
    _receipt, source, problems = stable_read(path, collect_bytes=True)
    if problems or source is None:
        raise CaptureError(f"canonical-source:{path.name}:{','.join(problems)}")
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dataset_contract_from_module(module: types.ModuleType) -> dict[str, Any]:
    archives = {
        str(name): {"sha256": str(row[0]), "bytes": int(row[1])}
        for name, row in sorted(module.EXPECTED_DATASET_ARCHIVES.items())
    }
    return {
        "schema": str(module.EXPECTED_DATASET_SCHEMA),
        "dataset_root": str(module.EXPECTED_DATASET_ROOT),
        "dataset_version": str(module.EXPECTED_DATASET_VERSION),
        "archive_root": str(module.EXPECTED_DATASET_ARCHIVE_ROOT),
        "metadata_root": str(module.EXPECTED_DATASET_METADATA_ROOT),
        "map_root": str(module.EXPECTED_DATASET_MAP_ROOT),
        "mount": dict(module.EXPECTED_DATASET_MOUNT),
        "proof_basis": dict(module.EXPECTED_DATASET_PROOF_BASIS),
        "archives": archives,
        "metadata_json_names": [str(value) for value in module.EXPECTED_DATASET_METADATA_FILES],
        "map_anchor_names": [str(value) for value in module.EXPECTED_DATASET_MAP_ANCHORS],
    }


def load_contract(path: Path = CANONICAL_MANIFEST_PATH) -> Contract:
    """Load only the canonical sibling manifest and reject an incomplete role topology."""

    path = Path(path)
    if path != CANONICAL_MANIFEST_PATH:
        expected_parent = CANONICAL_MANIFEST_PATH.parent
        if path.parent.resolve(strict=True) != expected_parent:
            raise CaptureError("canonical-manifest:outside-iter135")
    module = _load_module_from_stable_bytes(path, "iter135_environment_contract")
    remote_files = {
        str(role): (str(row[0]), str(row[1]), int(row[2]))
        for role, row in module.EXPECTED_REMOTE_FILES.items()
    }
    if (
        len(remote_files) != 82
        or sum(role.startswith("scenario:") for role in remote_files) != 20
        or sum(role.startswith("renderer:") for role in remote_files) != 42
    ):
        raise CaptureError("canonical-manifest:remote-role-topology")
    repositories = json.loads(json.dumps(module.EXPECTED_REPOSITORIES))
    untracked_bindings = dict(module.EXPECTED_REQUIRED_UNTRACKED_BINDINGS)
    required_untracked = {
        (str(repo_id), str(relative_path))
        for repo_id, repository in repositories.items()
        for relative_path in repository["required_untracked_paths"]
    }
    if required_untracked != set(untracked_bindings):
        raise CaptureError("canonical-manifest:untracked-binding-topology")
    for (repo_id, relative_path), role in untracked_bindings.items():
        expected_path = f"{repositories[repo_id]['path']}/{relative_path}"
        if role not in remote_files or remote_files[role][0] != expected_path:
            raise CaptureError("canonical-manifest:untracked-binding-path")
    dataset_contract = _dataset_contract_from_module(module)
    dataset_contract_sha256 = _canonical_json_sha256(dataset_contract)
    declared_dataset_contract_sha256 = str(module.EXPECTED_DATASET_CONTRACT_SHA256)
    if (
        declared_dataset_contract_sha256 != EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256
        or dataset_contract_sha256 != EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256
    ):
        raise CaptureError("canonical-manifest:dataset-contract-sha256")
    expected_archive_names = {
        "v1.0-trainval_meta.tgz",
        *(f"v1.0-trainval{index:02d}_blobs.tgz" for index in range(1, 11)),
    }
    archives = {
        name: (str(row["sha256"]), int(row["bytes"]))
        for name, row in dataset_contract["archives"].items()
    }
    if (
        set(archives) != expected_archive_names
        or len(dataset_contract["metadata_json_names"]) != 13
        or len(set(dataset_contract["metadata_json_names"])) != 13
        or len(dataset_contract["map_anchor_names"]) != 4
        or len(set(dataset_contract["map_anchor_names"])) != 4
        or sum(row[1] for row in archives.values()) != 314_886_603_672
    ):
        raise CaptureError("canonical-manifest:dataset-contract-topology")
    dataset_root = str(dataset_contract["dataset_root"])
    dataset_version = str(dataset_contract["dataset_version"])
    if (
        dataset_root != "/datasets/nuscenes-full"
        or dataset_version != "v1.0-trainval"
        or dataset_contract["archive_root"] != f"{dataset_root}/archives"
        or dataset_contract["metadata_root"] != f"{dataset_root}/{dataset_version}"
        or dataset_contract["map_root"] != f"{dataset_root}/maps"
    ):
        raise CaptureError("canonical-manifest:dataset-contract-paths")
    return Contract(
        schema=str(module.EXPECTED_ENV_SCHEMA),
        ready_verdict=str(module.EXPECTED_ENV_VERDICT),
        remote_files=remote_files,
        repositories=repositories,
        required_untracked_bindings=untracked_bindings,
        storage_identity=dict(module.EXPECTED_STORAGE_IDENTITY),
        dataset_schema=str(dataset_contract["schema"]),
        dataset_contract_sha256=dataset_contract_sha256,
        dataset_root=dataset_root,
        dataset_version=dataset_version,
        dataset_archive_root=str(dataset_contract["archive_root"]),
        dataset_metadata_root=str(dataset_contract["metadata_root"]),
        dataset_map_root=str(dataset_contract["map_root"]),
        dataset_mount=dict(dataset_contract["mount"]),
        dataset_proof_basis=dict(dataset_contract["proof_basis"]),
        dataset_archives=archives,
        dataset_metadata_files=tuple(dataset_contract["metadata_json_names"]),
        dataset_map_anchors=tuple(dataset_contract["map_anchor_names"]),
        image_ids=dict(module.EXPECTED_IMAGE_IDS),
        compose_input_sha256=str(module.EXPECTED_COMPOSE_INPUT_SHA256),
        compose_output_sha256=str(module.EXPECTED_COMPOSE_OUTPUT_SHA256),
        projected_output_bytes=int(module.PROJECTED_OUTPUT_BYTES),
        minimum_remote_free_bytes=int(module.MINIMUM_REMOTE_FREE_BYTES),
        minimum_reserve_bytes=int(module.MINIMUM_RESERVE_BYTES),
        minimum_local_free_bytes=int(module.MINIMUM_LOCAL_FREE_BYTES),
    )


def _literal_assignments(source: bytes, names: set[str]) -> dict[str, str]:
    tree = ast.parse(source.decode("utf-8"))
    values: dict[str, str] = {}

    def evaluate(node: ast.expr) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return evaluate(node.left) + evaluate(node.right)
        raise CaptureError("compose-patcher:nonliteral-contract")

    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name) or target.id not in names:
            continue
        values[target.id] = evaluate(statement.value)
    if set(values) != names:
        raise CaptureError(f"compose-patcher:missing-constants:{sorted(names - set(values))}")
    return values


def _compose_preimage(
    final_bytes: bytes,
    patcher_bytes: bytes,
    expected_input_sha256: str,
    expected_output_sha256: str,
) -> tuple[bytes | None, list[str]]:
    names = {
        "EXPECTED_INPUT_SHA256",
        "EXPECTED_OUTPUT_SHA256",
        "ANCHOR",
        "REPLACEMENT",
        "OUTPUT_DECLARATION_ANCHOR",
        "OUTPUT_DECLARATION_REPLACEMENT",
        "OUTPUT_MOUNT_ANCHOR",
        "OUTPUT_MOUNT_REPLACEMENT",
        "OUTPUT_LOG_ANCHOR",
        "OUTPUT_LOG_REPLACEMENT",
    }
    problems: list[str] = []
    try:
        values = _literal_assignments(patcher_bytes, names)
        final = final_bytes.decode("utf-8")
    except (CaptureError, UnicodeDecodeError) as error:
        return None, [f"compose:preimage:{type(error).__name__}"]
    if values["EXPECTED_INPUT_SHA256"] != expected_input_sha256:
        problems.append("compose:patcher-input-contract")
    if values["EXPECTED_OUTPUT_SHA256"] != expected_output_sha256:
        problems.append("compose:patcher-output-contract")
    pairs = (
        (values["ANCHOR"], values["REPLACEMENT"]),
        (values["OUTPUT_DECLARATION_ANCHOR"], values["OUTPUT_DECLARATION_REPLACEMENT"]),
        (values["OUTPUT_MOUNT_ANCHOR"], values["OUTPUT_MOUNT_REPLACEMENT"]),
        (values["OUTPUT_LOG_ANCHOR"], values["OUTPUT_LOG_REPLACEMENT"]),
    )
    recovered = final
    for anchor, replacement in reversed(pairs):
        if recovered.count(replacement) != 1:
            problems.append("compose:replacement-count")
            continue
        recovered = recovered.replace(replacement, anchor, 1)
    replay = recovered
    for anchor, replacement in pairs:
        if replay.count(anchor) != 1:
            problems.append("compose:anchor-count")
            continue
        replay = replay.replace(anchor, replacement, 1)
    if replay != final:
        problems.append("compose:replay-drift")
    return recovered.encode("utf-8"), sorted(set(problems))


def _decode_nul(output: bytes, label: str, problems: list[str]) -> list[str]:
    if not output:
        return []
    if not output.endswith(b"\0"):
        problems.append(f"repository:{label}:not-nul-terminated")
    rows: list[str] = []
    for raw in output.rstrip(b"\0").split(b"\0"):
        try:
            row = raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"repository:{label}:non-utf8")
            continue
        if not row or row.startswith("/") or ".." in Path(row).parts:
            problems.append(f"repository:{label}:unsafe-path")
            continue
        rows.append(row)
    return sorted(rows)


def _git(hooks: Hooks, repo: Path, *args: str) -> bytes:
    return hooks.run(
        [
            "git",
            "-c",
            f"safe.directory={repo}",
            "-C",
            str(repo),
            *args,
        ]
    )


def _repository_snapshot(
    hooks: Hooks,
    repo_id: str,
    repo: Path,
    problems: list[str],
) -> dict[str, Any]:
    return {
        "top": _git(hooks, repo, "rev-parse", "--show-toplevel").decode().strip(),
        "head": _git(hooks, repo, "rev-parse", "HEAD").decode().strip(),
        "staged": _decode_nul(
            _git(hooks, repo, "diff", "--cached", "--name-only", "-z"),
            f"{repo_id}:staged",
            problems,
        ),
        "dirty": _decode_nul(
            _git(hooks, repo, "diff", "--name-only", "-z"),
            f"{repo_id}:dirty",
            problems,
        ),
        "untracked": _decode_nul(
            _git(hooks, repo, "ls-files", "--others", "--exclude-standard", "-z"),
            f"{repo_id}:untracked",
            problems,
        ),
    }


def _probe_repositories(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for repo_id, expected in sorted(contract.repositories.items()):
        repo = Path(str(expected["path"]))
        components_before, path_problems = _component_snapshot(repo)
        problems.extend(f"repository:{repo_id}:{item}" for item in path_problems)
        try:
            resolved = repo.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            resolved = None
            problems.append(f"repository:{repo_id}:resolve:{type(error).__name__}")
        if resolved is not None and resolved != repo:
            problems.append(f"repository:{repo_id}:realpath:{resolved}")
        try:
            first = _repository_snapshot(hooks, repo_id, repo, problems)
            second = _repository_snapshot(hooks, repo_id, repo, problems)
            if first != second:
                problems.append(f"repository:{repo_id}:unstable-snapshot")
            top = second["top"]
            head = second["head"]
            staged = second["staged"]
            dirty = second["dirty"]
            untracked = second["untracked"]
        except (CaptureError, UnicodeDecodeError) as error:
            problems.append(f"repository:{repo_id}:probe:{type(error).__name__}")
            top, head, staged, dirty, untracked = None, None, [], [], []
        components_after, after_problems = _component_snapshot(repo)
        problems.extend(f"repository:{repo_id}:{item}" for item in after_problems)
        if components_before != components_after:
            problems.append(f"repository:{repo_id}:unstable-components")

        if top != str(repo):
            problems.append(f"repository:{repo_id}:top-level")
        if head != expected["head"]:
            problems.append(f"repository:{repo_id}:head")
        if staged != expected["staged_paths"]:
            problems.append(f"repository:{repo_id}:staged-paths")
        if dirty != expected["dirty_tracked_paths"]:
            problems.append(f"repository:{repo_id}:dirty-tracked-paths")

        required = sorted(str(value) for value in expected["required_untracked_paths"])
        if repo_id == "neuroncap":
            unexpected = [path for path in untracked if not path.startswith("outoutput/")]
            observed_required: list[str] = []
        elif repo_id == "neurad":
            unexpected = [path for path in untracked if path not in required]
            observed_required = sorted(path for path in untracked if path in required)
        else:
            unexpected = list(untracked)
            observed_required = sorted(path for path in untracked if path in required)
        if unexpected:
            problems.append(f"repository:{repo_id}:unexpected-untracked:{len(unexpected)}")
        if observed_required != required:
            problems.append(f"repository:{repo_id}:required-untracked")
        receipts[repo_id] = {
            "path": str(repo),
            "head": head,
            "staged_paths": staged,
            "dirty_tracked_paths": dirty,
            "required_untracked_paths": observed_required,
        }
    return receipts


def _probe_remote_files(
    contract: Contract,
    patcher_path: Path,
    problems: list[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    compose_bytes: bytes | None = None
    for role, (path_text, expected_digest, expected_bytes) in sorted(contract.remote_files.items()):
        row, data, file_problems = stable_read(
            Path(path_text), collect_bytes=role == "compose_script"
        )
        problems.extend(f"remote-file:{role}:{item}" for item in file_problems)
        if row["sha256"] != expected_digest:
            problems.append(f"remote-file:{role}:sha256")
        if row["bytes"] != expected_bytes:
            problems.append(f"remote-file:{role}:bytes")
        receipts[role] = row
        if role == "compose_script":
            compose_bytes = data

    patcher, patcher_bytes, patcher_problems = stable_read(patcher_path, collect_bytes=True)
    problems.extend(f"compose:patcher:{item}" for item in patcher_problems)
    compose = receipts.get("compose_script")
    if isinstance(compose, dict):
        compose["source_sha256"] = None
        compose["patcher_sha256"] = patcher.get("sha256")
    if compose_bytes is None or patcher_bytes is None:
        problems.append("compose:provenance-unavailable")
    else:
        source, source_problems = _compose_preimage(
            compose_bytes,
            patcher_bytes,
            contract.compose_input_sha256,
            contract.compose_output_sha256,
        )
        problems.extend(source_problems)
        source_digest = hashlib.sha256(source).hexdigest() if source is not None else None
        if isinstance(compose, dict):
            compose["source_sha256"] = source_digest
        if source_digest != contract.compose_input_sha256:
            problems.append("compose:source-sha256")
        if hashlib.sha256(compose_bytes).hexdigest() != contract.compose_output_sha256:
            problems.append("compose:output-sha256")
    return receipts


def _probe_images(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, expected_id in sorted(contract.image_ids.items()):
        image_id: Any = None
        repo_digests: Any = None
        try:
            raw = json.loads(hooks.run(["docker", "image", "inspect", name]))
            if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], dict):
                raise CaptureError("image-inspect-schema")
            image_id = raw[0].get("Id")
            repo_digests = raw[0].get("RepoDigests")
        except (CaptureError, json.JSONDecodeError) as error:
            problems.append(f"image:{name}:probe:{type(error).__name__}")
        if (
            image_id != expected_id
            or not isinstance(image_id, str)
            or not _IMAGE_ID_RE.fullmatch(image_id)
        ):
            problems.append(f"image:{name}:id")
        if not isinstance(repo_digests, list) or not all(
            isinstance(value, str) and _REPO_DIGEST_RE.fullmatch(value) for value in repo_digests
        ):
            problems.append(f"image:{name}:repo-digests-schema")
            repo_digests = []
        else:
            if len(repo_digests) != len(set(repo_digests)):
                problems.append(f"image:{name}:repo-digests-duplicate")
            repo_digests = sorted(set(repo_digests))
        receipts[name] = {"image_id": image_id, "repo_digests": repo_digests}
    return receipts


def _probe_gpu_and_idle(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    gpu: dict[str, Any] = {
        "model": None,
        "count": 0,
        "uuid": None,
        "driver_version": None,
        "memory_total_mib": None,
    }
    try:
        rows = [
            line.strip()
            for line in hooks.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,uuid,driver_version,memory.total",
                    "--format=csv,noheader,nounits",
                ]
            )
            .decode()
            .splitlines()
            if line.strip()
        ]
        gpu["count"] = len(rows)
        if len(rows) == 1:
            fields = [field.strip() for field in rows[0].split(",")]
            if len(fields) == 4:
                gpu.update(
                    {
                        "model": fields[0],
                        "uuid": fields[1],
                        "driver_version": fields[2],
                        "memory_total_mib": int(fields[3]),
                    }
                )
    except (CaptureError, UnicodeDecodeError, ValueError) as error:
        problems.append(f"gpu:probe:{type(error).__name__}")
    expected_gpu = {
        "model": contract.gpu_model,
        "count": 1,
        "uuid": contract.gpu_uuid,
        "driver_version": contract.gpu_driver,
        "memory_total_mib": contract.gpu_memory_mib,
    }
    if gpu != expected_gpu:
        problems.append("gpu:identity")
    if not isinstance(gpu.get("uuid"), str) or not _GPU_UUID_RE.fullmatch(gpu["uuid"]):
        problems.append("gpu:uuid-format")
    if not isinstance(gpu.get("driver_version"), str) or not _DRIVER_RE.fullmatch(
        gpu["driver_version"]
    ):
        problems.append("gpu:driver-format")

    container_count: int | None = None
    compute_count: int | None = None
    evaluator_count: int | None = None
    try:
        containers = [
            row for row in hooks.run(["docker", "ps", "-aq", "--no-trunc"]).splitlines() if row
        ]
        container_count = len(containers)
    except CaptureError as error:
        problems.append(f"idle:containers:{type(error).__name__}")
    if container_count != 0:
        problems.append("idle:containers-present")
    try:
        compute = [
            row
            for row in hooks.run(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid",
                    "--format=csv,noheader,nounits",
                ]
            ).splitlines()
            if row.strip()
        ]
        compute_count = len(compute)
    except CaptureError as error:
        problems.append(f"idle:gpu-processes:{type(error).__name__}")
    if compute_count != 0:
        problems.append("idle:gpu-process-present")
    try:
        process_rows = hooks.run(["ps", "-eo", "pid=,ppid=,args="]).decode().splitlines()
        parsed: dict[int, tuple[int, str]] = {}
        for row in process_rows:
            fields = row.strip().split(maxsplit=2)
            if len(fields) != 3:
                continue
            parsed[int(fields[0])] = (int(fields[1]), fields[2])
        ancestors: set[int] = set()
        cursor = hooks.pid()
        while cursor in parsed and cursor not in ancestors:
            ancestors.add(cursor)
            cursor = parsed[cursor][0]
        evaluator_count = sum(
            1
            for pid, (_parent, command) in parsed.items()
            if pid not in ancestors and _EVALUATOR_RE.search(command)
        )
    except (CaptureError, UnicodeDecodeError, ValueError) as error:
        problems.append(f"idle:evaluator-processes:{type(error).__name__}")
    if evaluator_count != 0:
        problems.append("idle:evaluator-process-present")
    idle = container_count == compute_count == evaluator_count == 0
    box = {
        "idle": idle,
        "all_containers": container_count,
        "gpu_compute_processes": compute_count,
        "known_evaluation_processes": evaluator_count,
    }
    return gpu, box


def _dataset_contract_payload(contract: Contract) -> dict[str, Any]:
    return {
        "schema": contract.dataset_schema,
        "dataset_root": contract.dataset_root,
        "dataset_version": contract.dataset_version,
        "archive_root": contract.dataset_archive_root,
        "metadata_root": contract.dataset_metadata_root,
        "map_root": contract.dataset_map_root,
        "mount": dict(contract.dataset_mount),
        "proof_basis": dict(contract.dataset_proof_basis),
        "archives": {
            name: {"sha256": digest, "bytes": byte_count}
            for name, (digest, byte_count) in sorted(contract.dataset_archives.items())
        },
        "metadata_json_names": list(contract.dataset_metadata_files),
        "map_anchor_names": list(contract.dataset_map_anchors),
    }


def _dataset_directory_snapshot(
    path: Path,
    expected_names: set[str] | None,
    label: str,
    problems: list[str],
) -> tuple[dict[str, Any], tuple[Any, ...] | None]:
    identity: dict[str, Any] = {"realpath": None, "is_symlink": None}
    components, component_problems = _component_snapshot(path)
    problems.extend(f"dataset:{label}:{item}" for item in component_problems)
    try:
        directory = path.lstat()
        identity["is_symlink"] = stat.S_ISLNK(directory.st_mode)
        resolved = path.resolve(strict=True)
        identity["realpath"] = str(resolved)
        if resolved != path:
            problems.append(f"dataset:{label}:realpath:{resolved}")
        if not stat.S_ISDIR(directory.st_mode):
            problems.append(f"dataset:{label}:not-directory")
        entries: list[tuple[str, tuple[int, int, int, int, int, int]]] = []
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            child_info = child.lstat()
            entries.append((child.name, _stat_identity(child_info)))
            if expected_names is not None and (
                stat.S_ISLNK(child_info.st_mode) or not stat.S_ISREG(child_info.st_mode)
            ):
                problems.append(f"dataset:{label}:nonphysical-file:{child.name}")
        observed_names = {name for name, _info in entries}
        if expected_names is not None and observed_names != expected_names:
            problems.append(f"dataset:{label}:file-set")
        snapshot: tuple[Any, ...] | None = (
            tuple(components),
            _stat_identity(directory),
            tuple(entries),
        )
    except OSError as error:
        problems.append(f"dataset:{label}:directory:{type(error).__name__}")
        snapshot = None
    return identity, snapshot


def _dataset_file(
    hooks: Hooks,
    path: Path,
    label: str,
    problems: list[str],
) -> dict[str, Any]:
    try:
        observed, file_problems = hooks.dataset_read(path)
    except (OSError, CaptureError) as error:
        problems.append(f"dataset:{label}:read:{type(error).__name__}")
        observed, file_problems = {}, []
    problems.extend(f"dataset:{label}:{item}" for item in file_problems)
    row = {
        "path": observed.get("path"),
        "sha256": observed.get("sha256"),
        "bytes": observed.get("bytes"),
    }
    if row["path"] != str(path):
        problems.append(f"dataset:{label}:path")
    if not isinstance(row["sha256"], str) or not _SHA256_RE.fullmatch(row["sha256"]):
        problems.append(f"dataset:{label}:sha256")
    if type(row["bytes"]) is not int or row["bytes"] <= 0:
        problems.append(f"dataset:{label}:bytes")
    return row


def _dataset_receipt_payload_sha256(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_payload_sha256", None)
    return _canonical_json_sha256(payload)


def _probe_dataset(
    contract: Contract,
    hooks: Hooks,
    problems: list[str],
) -> dict[str, Any]:
    if _canonical_json_sha256(_dataset_contract_payload(contract)) != (
        contract.dataset_contract_sha256
    ):
        problems.append("dataset:contract-sha256")

    root = Path(contract.dataset_root)
    archive_root = Path(contract.dataset_archive_root)
    metadata_root = Path(contract.dataset_metadata_root)
    map_root = Path(contract.dataset_map_root)
    root_identity, root_before = _dataset_directory_snapshot(root, None, "root", problems)
    archive_identity, archives_before = _dataset_directory_snapshot(
        archive_root, set(contract.dataset_archives), "archives", problems
    )
    metadata_identity, metadata_before = _dataset_directory_snapshot(
        metadata_root, set(contract.dataset_metadata_files), "metadata", problems
    )
    map_identity, maps_before = _dataset_directory_snapshot(
        map_root, set(contract.dataset_map_anchors), "maps", problems
    )

    archives: dict[str, dict[str, Any]] = {}
    for name, (expected_digest, expected_bytes) in sorted(contract.dataset_archives.items()):
        row = _dataset_file(hooks, archive_root / name, f"archive:{name}", problems)
        if row["sha256"] != expected_digest:
            problems.append(f"dataset:archive:{name}:expected-sha256")
        if row["bytes"] != expected_bytes:
            problems.append(f"dataset:archive:{name}:expected-bytes")
        archives[name] = row

    metadata: dict[str, dict[str, Any]] = {}
    for name in contract.dataset_metadata_files:
        metadata[name] = _dataset_file(hooks, metadata_root / name, f"metadata:{name}", problems)

    maps: dict[str, dict[str, Any]] = {}
    for name in contract.dataset_map_anchors:
        maps[name] = _dataset_file(hooks, map_root / name, f"map:{name}", problems)

    _root_after_identity, root_after = _dataset_directory_snapshot(
        root, None, "root-after", problems
    )
    _archive_after_identity, archives_after = _dataset_directory_snapshot(
        archive_root, set(contract.dataset_archives), "archives-after", problems
    )
    _metadata_after_identity, metadata_after = _dataset_directory_snapshot(
        metadata_root, set(contract.dataset_metadata_files), "metadata-after", problems
    )
    _map_after_identity, maps_after = _dataset_directory_snapshot(
        map_root, set(contract.dataset_map_anchors), "maps-after", problems
    )
    for label, before, after in (
        ("root", root_before, root_after),
        ("archives", archives_before, archives_after),
        ("metadata", metadata_before, metadata_after),
        ("maps", maps_before, maps_after),
    ):
        if before != after:
            problems.append(f"dataset:{label}:unstable-directory")

    mount_identity = {
        "mount_target": None,
        "mount_source": None,
        "mount_fstype": None,
        "mount_uuid": None,
    }
    try:
        mount_raw = json.loads(
            hooks.run(
                [
                    "findmnt",
                    "--json",
                    "--output",
                    "TARGET,SOURCE,FSTYPE,UUID",
                    "--target",
                    str(root),
                ]
            )
        )
        rows = mount_raw.get("filesystems") if isinstance(mount_raw, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise CaptureError("findmnt-schema")
        mount_identity = {
            "mount_target": rows[0].get("target"),
            "mount_source": rows[0].get("source"),
            "mount_fstype": rows[0].get("fstype"),
            "mount_uuid": rows[0].get("uuid"),
        }
    except (CaptureError, json.JSONDecodeError) as error:
        problems.append(f"dataset:findmnt:{type(error).__name__}")
    for field, expected in contract.dataset_mount.items():
        if mount_identity.get(field) != expected:
            problems.append(f"dataset:identity:{field}")

    dataset_device = mount_device = root_device = None
    try:
        dataset_device = hooks.device(root)
        mount_device = hooks.device(Path(str(contract.dataset_mount["mount_target"])))
        root_device = hooks.device(Path("/"))
    except OSError as error:
        problems.append(f"dataset:device:{type(error).__name__}")
    if dataset_device is None or dataset_device != mount_device:
        problems.append("dataset:device-mismatch")
    if dataset_device is None or dataset_device == root_device:
        problems.append("dataset:not-dedicated-device")

    identity = {
        "dataset_root": str(root),
        "dataset_realpath": root_identity["realpath"],
        "dataset_is_symlink": root_identity["is_symlink"],
        "dataset_version": contract.dataset_version,
        "archive_root": str(archive_root),
        "archive_realpath": archive_identity["realpath"],
        "archive_is_symlink": archive_identity["is_symlink"],
        "metadata_root": str(metadata_root),
        "metadata_realpath": metadata_identity["realpath"],
        "metadata_is_symlink": metadata_identity["is_symlink"],
        "map_root": str(map_root),
        "map_realpath": map_identity["realpath"],
        "map_is_symlink": map_identity["is_symlink"],
        **mount_identity,
        "dataset_st_dev": dataset_device,
        "mount_st_dev": mount_device,
        "root_st_dev": root_device,
    }
    receipt = {
        "schema": contract.dataset_schema,
        "contract_sha256": contract.dataset_contract_sha256,
        "proof_basis": dict(contract.dataset_proof_basis),
        "identity": identity,
        "archives": archives,
        "metadata_json": metadata,
        "map_anchors": maps,
    }
    receipt["receipt_payload_sha256"] = _dataset_receipt_payload_sha256(receipt)
    return receipt


def _probe_storage(
    contract: Contract,
    hooks: Hooks,
    local_free_bytes: int,
    problems: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = contract.storage_identity
    output_root = Path(str(expected["filesystem_path"]))
    identity = {
        "filesystem_path": str(output_root),
        "filesystem_realpath": None,
        "filesystem_is_symlink": None,
        "filesystem_empty": None,
        "mount_target": None,
        "mount_source": None,
        "mount_fstype": None,
        "mount_uuid": None,
    }
    _, component_problems = _component_snapshot(output_root)
    problems.extend(f"storage:{item}" for item in component_problems)
    try:
        root_lstat = output_root.lstat()
        identity["filesystem_is_symlink"] = stat.S_ISLNK(root_lstat.st_mode)
        resolved = output_root.resolve(strict=True)
        identity["filesystem_realpath"] = str(resolved)
        if not stat.S_ISDIR(root_lstat.st_mode):
            problems.append("storage:output-root-not-directory")
        identity["filesystem_empty"] = not any(output_root.iterdir())
    except OSError as error:
        problems.append(f"storage:output-root:{type(error).__name__}")
    for field, expected_value in expected.items():
        if field.startswith("mount_"):
            continue
        actual = identity.get(field)
        if actual != expected_value or (
            isinstance(expected_value, bool) and type(actual) is not bool
        ):
            problems.append(f"storage:identity:{field}")
    try:
        mount_raw = json.loads(
            hooks.run(
                [
                    "findmnt",
                    "--json",
                    "--output",
                    "TARGET,SOURCE,FSTYPE,UUID",
                    "--target",
                    str(output_root),
                ]
            )
        )
        rows = mount_raw.get("filesystems") if isinstance(mount_raw, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise CaptureError("findmnt-schema")
        mount = rows[0]
        identity.update(
            {
                "mount_target": mount.get("target"),
                "mount_source": mount.get("source"),
                "mount_fstype": mount.get("fstype"),
                "mount_uuid": mount.get("uuid"),
            }
        )
    except (CaptureError, json.JSONDecodeError) as error:
        problems.append(f"storage:findmnt:{type(error).__name__}")
    for field in ("mount_target", "mount_source", "mount_fstype", "mount_uuid"):
        if identity.get(field) != expected[field]:
            problems.append(f"storage:identity:{field}")

    output_device = mount_device = root_device = None
    try:
        output_device = hooks.device(output_root)
        mount_device = hooks.device(Path(str(expected["mount_target"])))
        root_device = hooks.device(Path("/"))
    except OSError as error:
        problems.append(f"storage:device:{type(error).__name__}")
    if output_device is None or output_device != mount_device:
        problems.append("storage:output-device-mismatch")
    if output_device is None or output_device == root_device:
        problems.append("storage:not-dedicated-device")

    remote_free_bytes: int | None = None
    try:
        remote_free_bytes = hooks.disk_free(output_root)
    except OSError as error:
        problems.append(f"storage:disk-free:{type(error).__name__}")
    if type(remote_free_bytes) is not int or remote_free_bytes < contract.minimum_remote_free_bytes:
        problems.append("storage:remote-free")
    if (
        type(remote_free_bytes) is not int
        or remote_free_bytes - contract.projected_output_bytes < contract.minimum_reserve_bytes
    ):
        problems.append("storage:projected-reserve")
    if type(local_free_bytes) is not int or local_free_bytes < contract.minimum_local_free_bytes:
        problems.append("storage:local-free")

    storage = {
        "remote_output_free_bytes": remote_free_bytes,
        "projected_output_bytes": contract.projected_output_bytes,
        "minimum_reserve_bytes": contract.minimum_reserve_bytes,
        "local_free_bytes": local_free_bytes,
        "remote_output_free_gib": (
            remote_free_bytes / 1024**3 if type(remote_free_bytes) is int else None
        ),
        "projected_output_gib": contract.projected_output_bytes / 1024**3,
        "minimum_reserve_gib": contract.minimum_reserve_bytes / 1024**3,
        "local_free_gib": local_free_bytes / 1024**3,
        **identity,
    }
    devices = {
        "filesystem_st_dev": output_device,
        "mount_st_dev": mount_device,
        "root_st_dev": root_device,
    }
    return storage, devices


def capture_environment(
    contract: Contract,
    *,
    local_free_bytes: int,
    patcher_path: Path = CANONICAL_PATCHER_PATH,
    hooks: Hooks = Hooks(),
) -> dict[str, Any]:
    problems: list[str] = []
    started = hooks.now().astimezone(UTC).isoformat().replace("+00:00", "Z")
    host = hooks.hostname()
    if host != contract.host:
        problems.append("host:identity")
    remote_files = _probe_remote_files(contract, patcher_path, problems)
    repositories = _probe_repositories(contract, hooks, problems)
    for (repo_id, relative_path), role in contract.required_untracked_bindings.items():
        repository = repositories.get(repo_id)
        remote = remote_files.get(role)
        if not isinstance(repository, dict) or not isinstance(remote, dict):
            problems.append(f"repository:{repo_id}:untracked-binding:{relative_path}")
            continue
        if remote.get("path") != f"{repository.get('path')}/{relative_path}":
            problems.append(f"repository:{repo_id}:untracked-binding:{relative_path}")
    images = _probe_images(contract, hooks, problems)
    gpu, box = _probe_gpu_and_idle(contract, hooks, problems)
    dataset = _probe_dataset(contract, hooks, problems)
    storage, storage_devices = _probe_storage(contract, hooks, local_free_bytes, problems)
    dataset_identity = dataset.get("identity")
    if not isinstance(dataset_identity, dict) or (
        dataset_identity.get("dataset_st_dev") != storage_devices.get("filesystem_st_dev")
        or dataset_identity.get("mount_st_dev") != storage_devices.get("mount_st_dev")
        or dataset_identity.get("root_st_dev") != storage_devices.get("root_st_dev")
    ):
        problems.append("dataset:storage-device-link")
    all_problems = sorted(set(problems))
    captured = hooks.now().astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {
        "schema": contract.schema,
        "verdict": contract.ready_verdict if not all_problems else INCOMPLETE_VERDICT,
        "captured_at_utc": captured,
        "capture_started_at_utc": started,
        "host": host,
        "problem_count": len(all_problems),
        "problems": all_problems,
        "gpu": gpu,
        "box": box,
        "dataset": dataset,
        "storage": storage,
        "storage_devices": storage_devices,
        "repositories": repositories,
        "remote_files": remote_files,
        "container_images": images,
    }


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    parent = path.parent
    _, parent_problems = _component_snapshot(parent)
    if parent_problems or parent.resolve(strict=True) != parent:
        raise CaptureError("output:nonphysical-parent")
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise CaptureError("output:unsafe-existing-path")
    payload = (json.dumps(value, indent=1, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_text = tempfile.mkstemp(
        dir=parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_text)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()


def _nonnegative_integer(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a base-10 integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-free-bytes", required=True, type=_nonnegative_integer)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        contract = load_contract()
        receipt = capture_environment(
            contract,
            local_free_bytes=args.local_free_bytes,
        )
        atomic_write_json(args.output, receipt)
    except CaptureError as error:
        print(f"I135_ENVIRONMENT_CAPTURE_FAIL {error}", file=sys.stderr)
        return 2
    print(
        f"{receipt['verdict']} problems={receipt['problem_count']} output={args.output}",
        file=sys.stderr,
    )
    return 0 if receipt["problem_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
