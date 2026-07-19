#!/usr/bin/env python3
"""Validate and materialize Iteration-135 launch authorization.

This controller is deliberately non-executing: it neither mutates ``MISSION_STATE.json`` nor
starts a container.  Mission control supplies the exact committed H/E/P/S/A/F/B topology.  The
controller validates artifact semantics and can emit the receipt that is committed in B.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import types
from typing import Any, Mapping, Sequence


EXPERIMENT_REL = "experiments/iter135_neuroncap_blind_braking_dose_response"
HOST_REL = f"{EXPERIMENT_REL}/host_preparation_receipt.json"
HOST_PACKET_REL = f"{EXPERIMENT_REL}/host_packet_manifest.json"
ENV_REL = f"{EXPERIMENT_REL}/env_receipts.json"
MANIFEST_REL = f"{EXPERIMENT_REL}/launch_manifest.json"
SMOKE_ROOT_REL = f"{EXPERIMENT_REL}/smoke-evidence"
SMOKE_RECEIPT_REL = f"{SMOKE_ROOT_REL}/smoke_receipt.json"
RAW_PRE_MANIFEST_REL = f"{SMOKE_ROOT_REL}/raw/pre_smoke_manifest.json"
RAW_ENV_REL = f"{SMOKE_ROOT_REL}/raw/environment_receipt.json"
RAW_PRE_STATE_REL = f"{SMOKE_ROOT_REL}/raw/pre_smoke_mission_state.json"
ACTIVATION_REL = f"{EXPERIMENT_REL}/launch_activation_receipt.json"
MISSION_REL = "MISSION_STATE.json"
TOOLING_RECEIPT_REL = f"{EXPERIMENT_REL}/tooling_verification_receipt.json"

TOOLING_PHASE = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
LAUNCH_PHASE = "LAUNCH_AUTHORIZED"
HOST_SCHEMA = "iter135.host_preparation_receipt.v1"
HOST_VERDICT = "I135_HOST_PREPARATION_OK"
HOST_PACKET_SCHEMA = "iter135.host_packet_manifest.v1"
ENV_SCHEMA = "iter135.environment_receipts.v3"
ENV_VERDICT = "I135_ENVIRONMENT_PREFLIGHT_OK"
MANIFEST_SCHEMA = "iter135.launch_manifest.v2"
PRE_SMOKE_VERDICT = "I135_TOOLING_MANIFEST_INCOMPLETE"
FINAL_MANIFEST_VERDICT = "I135_TOOLING_MANIFEST_OK"
SMOKE_SCHEMA = "iter135.smoke_receipt.v1"
SMOKE_VERDICT = "I135_LIVE_SMOKE_OK"
ACTIVATION_SCHEMA = "iter135.launch_activation.v1"
ACTIVATION_VERDICT = "I135_LAUNCH_ACTIVATION_OK"

BLIND_DOSES = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
SMOKE_EVIDENCE_PATHS = tuple(
    sorted(
        {
            f"{SMOKE_ROOT_REL}/SMOKE.md",
            SMOKE_RECEIPT_REL,
            f"{SMOKE_ROOT_REL}/raw/execution.jsonl",
            RAW_PRE_MANIFEST_REL,
            RAW_ENV_REL,
            f"{SMOKE_ROOT_REL}/raw/pre_smoke_mission_state.json",
            *{
                f"{SMOKE_ROOT_REL}/raw/{dose}.{suffix}"
                for dose in BLIND_DOSES
                for suffix in ("decisions.jsonl", "model-env.bin", "compose.log")
            },
        }
    )
)
PREFLIGHT_STAGE_PATHS = (
    (HOST_PACKET_REL, HOST_REL),
    (ENV_REL,),
    (MANIFEST_REL,),
    SMOKE_EVIDENCE_PATHS,
)
LAUNCH_STAGE_PATHS = (
    (MISSION_REL,),
    (MANIFEST_REL,),
    (ACTIVATION_REL, "CONTINUITY.md", "HANDOFF.md"),
)
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PREPARE_REL = f"{EXPERIMENT_REL}/prepare_host135.py"
CAPTURE_REL = f"{EXPERIMENT_REL}/capture_environment135.py"
MANIFEST_BUILDER_REL = f"{EXPERIMENT_REL}/make_launch_manifest.py"
SMOKE_VALIDATOR_REL = f"{EXPERIMENT_REL}/validate_smoke135.py"
TOOLING_VALIDATOR_REL = f"{EXPERIMENT_REL}/verify_tooling135.py"
FROZEN_REPLAY_PATHS = (
    PREPARE_REL,
    CAPTURE_REL,
    MANIFEST_BUILDER_REL,
    SMOKE_VALIDATOR_REL,
    TOOLING_VALIDATOR_REL,
)

HOST_REPOSITORY_HEADS = {
    "uniad": "4827b8be0823e90862caa75d9d146b2ae800b72f",
    "neuroncap": "ecdcf284e2b7b83c537f3292a06c0adddff55811",
    "neurad": "b25f717b23d85c865d469bf52a0bd03b244014be",
}
HOST_REPOSITORY_PATHS = {
    "uniad": "/opt/sentinel-stack/UniAD",
    "neuroncap": "/opt/sentinel-stack/NeuroNCAP",
    "neurad": "/opt/sentinel-stack/neurad-studio",
}
HOST_SAFE_ENVIRONMENT = {
    "DOCKER_CONFIG": "/nonexistent",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "SENTINEL_I135_PREPARE_SANITIZED": "1",
    "TZ": "UTC",
}
EXPECTED_HOST_FORBIDDEN_PATHS = {
    "/opt/sentinel-stack/iter135",
    "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "/datasets/nuscenes-full/sentinel-i135-smoke-evidence",
    "/opt/sentinel-stack/UniAD/i135-smoke-staging",
    "/opt/sentinel-stack/UniAD/dose_schedules.json",
    "/opt/sentinel-stack/UniAD/i135-decisions",
    "/var/lib/sentinel/i135-smoke.lock",
    "/var/lib/sentinel/i135-analytic.lock",
    "/var/log/sentinel-i135.log",
}
PUBLICATION_AUTHORITY_SCHEMA = "iter135.github_publication_authority.v1"
PUBLICATION_REPOSITORY = "manfromnowhere143/sentinel"
PUBLICATION_BRANCH = "master"
PUBLICATION_CHECKS = ("check (3.10)", "check (3.11)")
TOOLING_RECEIPT_FIELDS = {
    "schema",
    "publication",
    "verdict",
    "problem_count",
    "problems",
    "repository",
    "inventory",
    "inventory_sha256",
    "toolchain",
    "environment_contract",
    "files",
    "file_content_set_sha256",
    "command_contract",
    "commands",
    "timing",
    "receipt_payload_sha256",
}
TOOLING_PUBLICATION_FIELDS = {
    "generation",
    "supersedes_receipt_commit",
    "recovery_parent",
    "reason_code",
}
GENERATION_THREE_RECEIPT_COMMIT = "755489f36ae2b8cefad183341edefd7c30c047e7"
GENERATION_THREE_BATON_COMMIT = "30b6390b3e165fc517ec6a7d1d7a26502ea45e2a"
GENERATION_FOUR_RECEIPT_COMMIT = "c3e891b9e41f2291b47edc9cec7abffd5259f674"
GENERATION_FOUR_BATON_COMMIT = "27c7f02b5474dd156c4a7686de774a6f408df42e"
GENERATION_FIVE_RECEIPT_COMMIT = "1f70e367cd1ffcc2c3dab1c801d0e195a1341ef2"
GENERATION_SIX_RECEIPT_COMMIT = "4fb4d819d56f6a6c6331abfa4e8039bf8bedf7be"
GENERATION_SIX_BATON_COMMIT = "a37d1fc0fc9b96604e68e37006c0a8b3515984bb"
GENERATION_SEVEN_RECEIPT_COMMIT = "470ec333b29f3da8e8b2ee696982f2503ea66161"
GENERATION_SEVEN_BATON_COMMIT = "04801441ce17e104ed2e78a4dd02370d4ffdde17"
GENERATION_EIGHT_REASON = "B7_STAGE_ZERO_DEEP_REPLAY_CHECKOUT_TIMEOUT_UNSATISFIABLE"
GENERATION_EIGHT_RECEIPT_COMMIT = "faf8a2d0a35be2ad053dae1946893cf69f024f5c"
GENERATION_EIGHT_BATON_COMMIT = "833a00cd930b44e3fac63edb09c6590efd128933"
GENERATION_NINE_REASON = "B8_STAGE_ZERO_HOST_STATE_MIRRORS_STALE_ACROSS_FROZEN_TOOLS"
GENERATION_NINE_RECEIPT_COMMIT = "133c7c924a3f47a8e1ff9bf9f975e4e99902fea2"
# Generation ten's source parent is the published generation-nine stage-zero commit, the exact
# master tip when the remaining check-run-envelope fossils were found (the generation-six
# precedent: the source parent is the published tip, not necessarily a baton).
GENERATION_NINE_STAGE_ZERO_COMMIT = "023d7ca638de5f3bde29ef9c6068bc64ecf711f2"
GENERATION_TEN_REASON = "E_PREFLIGHT_CHECK_RUN_ENVELOPE_FOSSILS_IN_CAPTURE_AND_LAUNCHERS"
GENERATION_TEN_RECEIPT_COMMIT = "146d52e5b662bf6af0fd26925367c6218822fa39"
# Generation eleven's source parent is the published generation-ten stage-zero commit, the
# master tip when the first live environment capture failed closed against stale dataset,
# Docker 29, and artifact-replay contracts.
GENERATION_TEN_STAGE_ZERO_COMMIT = "50511a9261e904f4367b390bcc5fa85572e09c26"
GENERATION_ELEVEN_REASON = "E1_ENVIRONMENT_CONTRACTS_STALE_DATASET_DOCKER_ARTIFACT_REPLAY"
GENERATION_ELEVEN_RECEIPT_COMMIT = "97dc88eaa44831eb329d86579f49a4a10a3347e4"
# Generation twelve's source parent is the published generation-eleven stage-zero commit, the
# master tip when the first live E-commit validation exposed the controller's wiring defects.
GENERATION_ELEVEN_STAGE_ZERO_COMMIT = "a698cbbe3cf6c9e1320c74ab2748f576e68b114e"
GENERATION_TWELVE_REASON = "E2_COMMIT_VALIDATOR_WIRING_PATCHER_AND_AUTHORITY_ARTIFACTS"
GENERATION_TWELVE_RECEIPT_COMMIT = "fa073e6903be65ff449fc7566df751395d585929"
# Generation thirteen's source parent is the published generation-twelve environment-receipt tip
# (the E commit), the master tip when the pre-smoke rebuild's origin/master hazard was found.
GENERATION_TWELVE_ENV_COMMIT = "2c70393f95dcad0871bee24647dd93a151d7b954"
GENERATION_THIRTEEN_REASON = "E3_PRESMOKE_REBUILD_ORIGIN_MASTER_AHEAD_OF_STAGE_PARENT"
GENERATION_THIRTEEN_RECEIPT_COMMIT = "688182ad3b7afbb0d58141accbcf554981e6fb20"
# Generation fourteen's source parent is the published generation-thirteen pre-smoke launch
# manifest tip (the P commit), the master tip when the live smoke preflight exposed that the
# Docker Engine 29 daemon-schema fossil generation eleven repaired in the environment capture
# was still frozen into both live launchers.
GENERATION_THIRTEEN_MANIFEST_COMMIT = "1ba42bbb869c652fd6d3d951a3c92ec404f61e72"
GENERATION_FOURTEEN_REASON = "S1_SMOKE_AND_DOSE_DOCKER29_DAEMON_EXPERIMENTAL_SCHEMA_FOSSIL"
GENERATION_FOURTEEN_RECEIPT_COMMIT = "b260ca5b0910c4d499c13e42add97affd726b77c"
GENERATION_FOURTEEN_BATON_COMMIT = "69bd2e2face00ccabb426382347eb04e8a0dbe83"
GENERATION_FIFTEEN_REASON = (
    "B14_H_DESCENDANT_CONTROLLER_OMISSION_GITHUB_RUN_AUTHORITY_"
    "AND_CI_FIXTURE_RESOURCE_FOSSILS"
)
EXPECTED_TOOLING_PUBLICATION = {
    "generation": 15,
    "supersedes_receipt_commit": GENERATION_FOURTEEN_RECEIPT_COMMIT,
    "recovery_parent": GENERATION_FOURTEEN_BATON_COMMIT,
    "reason_code": GENERATION_FIFTEEN_REASON,
}
TOOLING_REPOSITORY_FIELDS = {
    "root",
    "git_start",
    "git_end",
    "git_head_stable",
    "git_state_stable",
    "repository_clean_state_stable",
}
TOOLING_GIT_STATE_FIELDS = {
    "head",
    "dirty_entries",
    "porcelain_v1_z_sha256",
    "branch",
    "upstream",
    "upstream_head",
    "parents",
    "commit_paths",
}
TOOLING_INVENTORY_FIELDS = {
    "contract",
    "tests",
    "python_tools",
    "python_files",
    "shell_files",
    "data_files",
    "control_files",
    "tested_files",
}
TOOLING_TIMING_FIELDS = {
    "started_at_utc",
    "finished_at_utc",
    "wall_duration_ns",
    "monotonic_duration_ns",
}


class AuthorizationError(RuntimeError):
    """A launch-authorization input could not be read without ambiguity."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _git_blob_oid(payload: bytes) -> str:
    return hashlib.sha1(  # noqa: S324 - native Git blob object identity, not security hashing
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _strict_json_object(payload: bytes, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise AuthorizationError(f"duplicate JSON key in {label}")
            value[key] = item
        return value

    def reject_constant(_value: str) -> None:
        raise AuthorizationError(f"non-finite JSON value in {label}")

    value = json.loads(
        payload,
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )
    if not isinstance(value, dict):
        raise AuthorizationError(f"JSON root is not an object: {label}")
    return value


def _git(repo: Path, *arguments: str, timeout: int = 10) -> bytes:
    completed = subprocess.run(  # noqa: S603 - fixed Git executable and bounded argv
        ("/usr/bin/git", "-c", "core.hooksPath=/dev/null", *arguments),
        cwd=repo,
        env={
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": str(repo),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise AuthorizationError(f"Git probe failed: {arguments[0]}")
    return completed.stdout


def _commit_row(repo: Path, commit: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(commit, str) or _OID_RE.fullmatch(commit) is None:
        raise AuthorizationError("commit is not lowercase 40-hex")
    parents = tuple(
        _git(repo, "show", "-s", "--format=%P", commit).decode("ascii").strip().split()
    )
    paths = tuple(
        sorted(
            item.decode("utf-8")
            for item in _git(
                repo,
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                commit,
            ).split(b"\0")
            if item
        )
    )
    return parents, paths


def _blob(repo: Path, commit: str, relative: str) -> bytes:
    if relative.startswith("/") or ".." in Path(relative).parts:
        raise AuthorizationError(f"unsafe repository path: {relative!r}")
    return _git(repo, "show", f"{commit}:{relative}")


def _json_blob(repo: Path, commit: str, relative: str) -> dict[str, Any]:
    try:
        value = _strict_json_object(_blob(repo, commit, relative), relative)
    except (UnicodeDecodeError, json.JSONDecodeError, AuthorizationError) as exc:
        raise AuthorizationError(f"malformed JSON at {commit}:{relative}") from exc
    return value


def _binding(relative: str, payload: bytes) -> dict[str, Any]:
    return {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def _stable_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise AuthorizationError(f"not a physical regular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
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
    if (
        not stat.S_ISREG(before.st_mode)
        or identity_before != identity_after
        or len(payload) != before.st_size
    ):
        raise AuthorizationError(f"file changed while read: {path}")
    return payload


def _canonical_pretty_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(value),
            indent=1,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo != timezone.utc or parsed.isoformat().replace("+00:00", "Z") != value:
        return None
    return parsed


def _load_frozen_tooling_receipt_validator(repo: Path, source_commit: str):
    validator_source = _blob(repo, source_commit, TOOLING_VALIDATOR_REL)
    validator_module_name = "iter135_frozen_tooling_receipt_validator"
    validator_module = types.ModuleType(validator_module_name)
    validator_module.__file__ = str(repo / TOOLING_VALIDATOR_REL)
    previous_validator_module = sys.modules.get(validator_module_name)
    sys.modules[validator_module_name] = validator_module
    try:
        exec(  # noqa: S102 - the validator is loaded from the receipt-bound source commit
            compile(validator_source, validator_module.__file__, "exec"),
            validator_module.__dict__,
        )
    except Exception as exc:  # noqa: BLE001 - every frozen-validator fault fails closed
        raise AuthorizationError(
            f"frozen tooling receipt validator failed: {type(exc).__name__}"
        ) from exc
    finally:
        if previous_validator_module is None:
            sys.modules.pop(validator_module_name, None)
        else:
            sys.modules[validator_module_name] = previous_validator_module
    validator = getattr(validator_module, "validate_published_receipt_structure", None)
    if not callable(validator):
        raise AuthorizationError("frozen tooling receipt validator is missing")
    return validator


def _tooling_source_commit(repo: Path, tooling_receipt_commit: str) -> str:
    parents, paths = _commit_row(repo, tooling_receipt_commit)
    if len(parents) != 1 or paths != (TOOLING_RECEIPT_REL,):
        raise AuthorizationError("tooling receipt is not an isolated direct source child")
    source_commit = parents[0]
    receipt = _json_blob(repo, tooling_receipt_commit, TOOLING_RECEIPT_REL)
    if set(receipt) != TOOLING_RECEIPT_FIELDS:
        raise AuthorizationError("tooling receipt root field set is not exact")
    repository = receipt.get("repository")
    start = repository.get("git_start") if isinstance(repository, Mapping) else None
    end = repository.get("git_end") if isinstance(repository, Mapping) else None
    publication = receipt.get("publication")
    inventory = receipt.get("inventory")
    timing = receipt.get("timing")
    payload = dict(receipt)
    claimed_payload_sha256 = payload.pop("receipt_payload_sha256", None)
    if (
        receipt.get("schema") != "iter135.tooling_verification.v2"
        or receipt.get("verdict") != "I135_TOOLING_VERIFICATION_OK"
        or receipt.get("problem_count") != 0
        or receipt.get("problems") != []
        or not isinstance(publication, Mapping)
        or set(publication) != TOOLING_PUBLICATION_FIELDS
        or publication != EXPECTED_TOOLING_PUBLICATION
        or not isinstance(repository, Mapping)
        or set(repository) != TOOLING_REPOSITORY_FIELDS
        or not isinstance(start, Mapping)
        or set(start) != TOOLING_GIT_STATE_FIELDS
        or start.get("head") != source_commit
        or not isinstance(end, Mapping)
        or set(end) != TOOLING_GIT_STATE_FIELDS
        or end != start
        or repository.get("git_head_stable") is not True
        or repository.get("git_state_stable") is not True
        or repository.get("repository_clean_state_stable") is not True
        or not isinstance(inventory, Mapping)
        or set(inventory) != TOOLING_INVENTORY_FIELDS
        or not isinstance(timing, Mapping)
        or set(timing) != TOOLING_TIMING_FIELDS
        or not isinstance(receipt.get("toolchain"), Mapping)
        or not isinstance(receipt.get("environment_contract"), Mapping)
        or not isinstance(receipt.get("files"), Mapping)
        or not isinstance(receipt.get("command_contract"), list)
        or not isinstance(receipt.get("commands"), list)
        or not isinstance(receipt.get("inventory_sha256"), str)
        or _SHA256_RE.fullmatch(receipt["inventory_sha256"]) is None
        or not isinstance(receipt.get("file_content_set_sha256"), str)
        or _SHA256_RE.fullmatch(receipt["file_content_set_sha256"]) is None
        or claimed_payload_sha256 != hashlib.sha256(_canonical_json(payload)).hexdigest()
    ):
        raise AuthorizationError(
            "tooling receipt does not bind the exact green generation-fifteen source"
        )
    try:
        validator = _load_frozen_tooling_receipt_validator(repo, source_commit)
        frozen_errors = validator(receipt, repo_root=repo)
    except AuthorizationError:
        raise
    except Exception as exc:  # noqa: BLE001 - every frozen-validator fault fails closed
        raise AuthorizationError(
            f"frozen tooling receipt validator failed: {type(exc).__name__}"
        ) from exc
    if not isinstance(frozen_errors, list) or any(
        not isinstance(item, str) for item in frozen_errors
    ):
        raise AuthorizationError("frozen tooling receipt validator returned malformed errors")
    if frozen_errors:
        raise AuthorizationError(
            f"tooling receipt failed frozen validation: {frozen_errors[0][:256]}"
        )
    for relative in FROZEN_REPLAY_PATHS:
        _blob(repo, source_commit, relative)
    return source_commit


def _git_tree_mode(repo: Path, commit: str, relative: str) -> int:
    raw = _git(repo, "ls-tree", "-z", commit, "--", relative)
    rows = [row for row in raw.split(b"\0") if row]
    if len(rows) != 1:
        raise AuthorizationError(f"tree entry is missing or ambiguous: {relative}")
    header, separator, observed = rows[0].partition(b"\t")
    fields = header.split()
    if not separator or observed.decode("utf-8") != relative or len(fields) != 3:
        raise AuthorizationError(f"tree entry is malformed: {relative}")
    mode = fields[0]
    if mode == b"100755":
        return 0o755
    if mode == b"100644":
        return 0o644
    raise AuthorizationError(f"unsupported packet tree mode: {relative}:{mode!r}")


def _module_from_checkout(
    repo: Path,
    checkout: Path,
    source_commit: str,
    relative: str,
    module_label: str,
) -> types.ModuleType:
    path = checkout / relative
    source = _stable_bytes(path)
    if source != _blob(repo, source_commit, relative):
        raise AuthorizationError(f"frozen validator drift: {relative}")
    module_name = f"sentinel_i135_authority_{module_label}_{hashlib.sha256(source).hexdigest()[:12]}"
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)  # noqa: S102 - frozen source
    finally:
        sys.modules.pop(module_name, None)
    return module


# Materializing a replay working tree writes the full committed evidence tree (multiple GiB and
# growing with every published stage), so it gets its own generous hang bound instead of the
# ten-second probe timeout. Generation seven froze the probe timeout for every Git call; the first
# descendant validation then proved the checkout cannot finish inside ten seconds on either the
# canonical operator host (~14-18 s measured) or the hosted CI runners. The bound below is still a
# hard fail-closed ceiling, not permission to hang.
REPLAY_CHECKOUT_TIMEOUT_SECONDS = 600


def _checkout(repo: Path, checkout: Path, commit: str) -> None:
    _git(
        checkout,
        "checkout",
        "--detach",
        "--force",
        "--quiet",
        commit,
        timeout=REPLAY_CHECKOUT_TIMEOUT_SECONDS,
    )
    head = _git(checkout, "rev-parse", "HEAD").decode("ascii").strip()
    if head != commit:
        raise AuthorizationError("isolated materialization checked out the wrong commit")


def _isolated_clone(repo: Path, destination: Path) -> None:
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": str(destination.parent),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    completed = subprocess.run(  # noqa: S603 - fixed executable and bounded local arguments
        (
            "/usr/bin/git",
            "-c",
            "core.hooksPath=/dev/null",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            "--",
            str(repo),
            str(destination),
        ),
        cwd=destination.parent,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise AuthorizationError("could not create isolated local replay clone")


def _packet_source_path(name: str) -> str:
    return MISSION_REL if name == "MISSION_STATE.json" else f"{EXPERIMENT_REL}/{name}"


def _packet_bindings(
    repo: Path,
    tooling_baton_commit: str,
    names: Sequence[str],
) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    for name in names:
        relative = _packet_source_path(name)
        payload = _blob(repo, tooling_baton_commit, relative)
        mode = _git_tree_mode(repo, tooling_baton_commit, relative)
        git_mode = {0o644: "100644", 0o755: "100755"}.get(mode)
        if git_mode is None:
            raise AuthorizationError(f"unsupported packet mode: {relative}:{mode!r}")
        bindings[name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "mode": mode,
            "git_blob_oid": _git_blob_oid(payload),
            "git_mode": git_mode,
        }
    return bindings


def _validate_repository_snapshot(
    row: Any,
    *,
    label: str,
    dirty: Sequence[str] | tuple[Sequence[str], ...],
    untracked: Sequence[str] | None = None,
    untracked_prefix: str | None = None,
) -> list[str]:
    if not isinstance(row, Mapping) or set(row) != {
        "path",
        "head",
        "staged_paths",
        "dirty_tracked_paths",
        "untracked_paths",
    }:
        return [f"host:repository:{label}:field-set"]
    problems: list[str] = []
    if row.get("path") != HOST_REPOSITORY_PATHS[label]:
        problems.append(f"host:repository:{label}:path")
    if row.get("head") != HOST_REPOSITORY_HEADS[label]:
        problems.append(f"host:repository:{label}:head")
    if row.get("staged_paths") != []:
        problems.append(f"host:repository:{label}:staged")
    accepted_dirty: tuple[Sequence[str], ...]
    if dirty and isinstance(dirty[0], (list, tuple)):  # type: ignore[index]
        accepted_dirty = tuple(dirty)  # type: ignore[arg-type]
    else:
        accepted_dirty = (dirty,)  # type: ignore[assignment]
    if row.get("dirty_tracked_paths") not in [list(value) for value in accepted_dirty]:
        problems.append(f"host:repository:{label}:dirty")
    observed_untracked = row.get("untracked_paths")
    if untracked is not None and observed_untracked != list(untracked):
        problems.append(f"host:repository:{label}:untracked")
    if untracked_prefix is not None and (
        not isinstance(observed_untracked, list)
        or any(
            value != untracked_prefix and not value.startswith(f"{untracked_prefix}/")
            for value in observed_untracked
            if isinstance(value, str)
        )
        or any(not isinstance(value, str) for value in observed_untracked)
    ):
        problems.append(f"host:repository:{label}:untracked")
    return problems


def _validate_host_receipt_deep(
    host: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    packet_payload: bytes,
    expected_files: Mapping[str, Mapping[str, Any]],
    tooling_baton_commit: str,
) -> list[str]:
    problems: list[str] = []
    expected_fields = {
        "schema",
        "verdict",
        "started_at_utc",
        "finished_at_utc",
        "host",
        "problem_count",
        "problems",
        "packet_manifest_sha256",
        "publication_authority",
        "packet",
        "controller",
        "repositories",
        "compose",
        "storage",
        "forbidden_paths",
        "actions",
        "invocation",
        "receipt_payload_sha256",
    }
    if set(host) != expected_fields:
        problems.append("host:field-set")
    problems.extend(_green_receipt(host, HOST_SCHEMA, HOST_VERDICT, "host"))
    started = _canonical_utc(host.get("started_at_utc"))
    finished = _canonical_utc(host.get("finished_at_utc"))
    if started is None or finished is None or started > finished:
        problems.append("host:timestamps")
    if host.get("host") != "sentinel-gpu":
        problems.append("host:identity")
    payload = dict(host)
    claim = payload.pop("receipt_payload_sha256", None)
    if claim != hashlib.sha256(_canonical_json(payload)).hexdigest():
        problems.append("host:receipt-payload-sha256")

    packet_digest = hashlib.sha256(packet_payload).hexdigest()
    if host.get("packet_manifest_sha256") != packet_digest:
        problems.append("host:packet-manifest-sha256")
    problems.extend(
        _validate_publication_authority(
            host.get("publication_authority"),
            expected_commit=tooling_baton_commit,
            expected_artifacts=sorted(
                (
                    {
                        "path": _packet_source_path(name),
                        "sha256": row.get("sha256"),
                        "bytes": row.get("bytes"),
                        "git_blob_oid": row.get("git_blob_oid"),
                        "git_mode": row.get("git_mode"),
                    }
                    for name, row in expected_files.items()
                ),
                key=lambda row: str(row["path"]),
            ),
            label="host:publication-authority",
        )
    )
    embedded = host.get("packet")
    observed_files = embedded.get("files") if isinstance(embedded, Mapping) else None
    if (
        not isinstance(embedded, Mapping)
        or embedded.get("schema") != HOST_PACKET_SCHEMA
        or embedded.get("source_commit") != tooling_baton_commit
        or embedded.get("independently_supplied_manifest_sha256") != packet_digest
        or not isinstance(observed_files, Mapping)
        or set(observed_files) != set(expected_files)
    ):
        problems.append("host:packet-replay")
        observed_files = {}
    manifest_claim = embedded.get("manifest") if isinstance(embedded, Mapping) else None
    if (
        not isinstance(manifest_claim, Mapping)
        or manifest_claim.get("sha256") != packet_digest
        or manifest_claim.get("bytes") != len(packet_payload)
        or manifest_claim.get("mode") != 0o644
    ):
        problems.append("host:packet-manifest-binding")
    for name, expected in expected_files.items():
        row = observed_files.get(name) if isinstance(observed_files, Mapping) else None
        if (
            not isinstance(row, Mapping)
            or row.get("path") != f"/opt/sentinel-stack/.iter135-packet/{name}"
            or any(row.get(field) != expected.get(field) for field in ("sha256", "bytes", "mode"))
        ):
            problems.append(f"host:packet-file:{name}")
    if host.get("controller") != observed_files.get("prepare_host135.py"):
        problems.append("host:controller-binding")

    repositories = host.get("repositories")
    if not isinstance(repositories, Mapping) or set(repositories) != {"before", "after"}:
        problems.append("host:repositories")
    else:
        before = repositories.get("before")
        after = repositories.get("after")
        if not isinstance(before, Mapping) or set(before) != set(HOST_REPOSITORY_HEADS):
            problems.append("host:repositories-before")
            before = {}
        if not isinstance(after, Mapping) or set(after) != set(HOST_REPOSITORY_HEADS):
            problems.append("host:repositories-after")
            after = {}
        problems.extend(
            _validate_repository_snapshot(
                before.get("uniad"),
                label="uniad",
                dirty=(
                    ["inference/server.py", "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"],
                    ["projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"],
                ),
                # The UniAD checkout carries exactly one untracked entry: the load-bearing
                # `checkpoints` symlink through which the tracked config resolves its motion
                # anchors. Generation five accepted that reality in the host contract; this
                # mirror expectation was left at the pre-generation-five empty set and could
                # never accept a true receipt.
                untracked=["checkpoints"],
            )
        )
        problems.extend(
            _validate_repository_snapshot(
                after.get("uniad"),
                label="uniad",
                dirty=["projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"],
                untracked=["checkpoints"],
            )
        )
        for rows in (before, after):
            problems.extend(
                _validate_repository_snapshot(
                    rows.get("neuroncap"),
                    label="neuroncap",
                    dirty=["docker/Dockerfile", "scripts/_docker_compose_release.sh"],
                    untracked_prefix="outoutput",
                )
            )
            problems.extend(
                _validate_repository_snapshot(
                    rows.get("neurad"),
                    label="neurad",
                    dirty=["Dockerfile"],
                    untracked=["Dockerfile.bak"],
                )
            )

    compose = host.get("compose")
    if not isinstance(compose, Mapping) or set(compose) != {"patcher", "before", "after"}:
        problems.append("host:compose")
    else:
        if compose.get("patcher") != observed_files.get("patch_compose_dose_env.py"):
            problems.append("host:compose-patcher")
        before_compose = compose.get("before")
        after_compose = compose.get("after")
        expected_compose = (
            (before_compose, "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d", 3_380),
            (after_compose, "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada", 3_613),
        )
        for label, (row, digest, byte_count) in zip(("before", "after"), expected_compose):
            if (
                not isinstance(row, Mapping)
                or row.get("path")
                != "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh"
                or row.get("sha256") != digest
                or row.get("bytes") != byte_count
                or row.get("mode") not in (0o644, 0o755)
            ):
                problems.append(f"host:compose-{label}")

    storage = host.get("storage")
    if not isinstance(storage, Mapping):
        problems.append("host:storage")
    else:
        expected_mount = {
            "mount_target": "/datasets/nuscenes-full",
            "mount_source": "/dev/nvme0n2",
            "mount_fstype": "ext4",
            "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
        }
        if any(storage.get(key) != value for key, value in expected_mount.items()):
            problems.append("host:storage-mount")
        dataset_device = storage.get("dataset_st_dev")
        root_device = storage.get("root_st_dev")
        if (
            type(dataset_device) is not int
            or type(root_device) is not int
            or dataset_device == root_device
            or storage.get("analytic_root_st_dev") != dataset_device
        ):
            problems.append("host:storage-device")
        free_before = storage.get("free_bytes_before")
        free_after = storage.get("free_bytes_after")
        projected = storage.get("projected_output_bytes")
        reserve = storage.get("minimum_reserve_bytes")
        if (
            type(free_before) is not int
            or type(free_after) is not int
            or type(projected) is not int
            or type(reserve) is not int
            or storage.get("minimum_remote_free_bytes") != 100 * 1024**3
            or projected != 72_380_432_384
            or free_before < 100 * 1024**3
            or free_after < 100 * 1024**3
            or min(free_before, free_after) - projected < reserve
            or reserve != 25 * 1024**3
        ):
            problems.append("host:storage-capacity")
        if (
            storage.get("analytic_root")
            != "/datasets/nuscenes-full/sentinel-i135-outoutput"
            or storage.get("analytic_root_realpath")
            != "/datasets/nuscenes-full/sentinel-i135-outoutput"
            or storage.get("analytic_root_is_symlink") is not False
            or storage.get("analytic_root_empty") is not True
        ):
            problems.append("host:storage-analytic-root")

    forbidden = host.get("forbidden_paths")
    if (
        not isinstance(forbidden, Mapping)
        or set(forbidden) != EXPECTED_HOST_FORBIDDEN_PATHS
        or any(value is not False for value in forbidden.values())
    ):
        problems.append("host:forbidden-paths")
    actions = host.get("actions")
    action_names = [
        "normalize_uniad_server_from_verified_head_blob",
        "atomically_patch_compose_from_exact_preimage",
        "create_absent_empty_analytic_root",
        "atomically_install_verified_packet",
    ]
    if (
        not isinstance(actions, list)
        or [row.get("action") if isinstance(row, Mapping) else None for row in actions]
        != action_names
        or any(
            row.get("performed") is not True
            for row in actions[1:]
            if isinstance(row, Mapping)
        )
    ):
        problems.append("host:actions")
    invocation = host.get("invocation")
    if (
        not isinstance(invocation, Mapping)
        or invocation.get("environment") != HOST_SAFE_ENVIRONMENT
        or invocation.get("isolated") is not True
        or invocation.get("python_implementation") != "CPython"
        or not isinstance(invocation.get("python_version"), str)
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", invocation["python_version"]) is None
    ):
        problems.append("host:invocation")
    return sorted(set(problems))


def _validate_publication_authority(
    authority: Any,
    *,
    expected_commit: str,
    expected_artifacts: Sequence[Mapping[str, Any]],
    label: str,
) -> list[str]:
    fields = {
        "schema",
        "repository",
        "branch",
        "source_commit",
        "branch_head_sha",
        "required_checks",
        "checks",
        "artifacts",
        "verified",
    }
    if not isinstance(authority, Mapping) or set(authority) != fields:
        return [f"{label}:field-set"]
    problems: list[str] = []
    if (
        authority.get("schema") != PUBLICATION_AUTHORITY_SCHEMA
        or authority.get("repository") != PUBLICATION_REPOSITORY
        or authority.get("branch") != PUBLICATION_BRANCH
        or authority.get("source_commit") != expected_commit
        or authority.get("branch_head_sha") != expected_commit
        or authority.get("required_checks") != list(PUBLICATION_CHECKS)
        or authority.get("verified") is not True
    ):
        problems.append(f"{label}:contract")
    expected_rows = [dict(row) for row in expected_artifacts]
    if (
        not expected_rows
        or len({row.get("path") for row in expected_rows}) != len(expected_rows)
        or any(
            set(row) != {"path", "sha256", "bytes", "git_blob_oid", "git_mode"}
            or not isinstance(row.get("path"), str)
            or not row["path"]
            or not isinstance(row.get("sha256"), str)
            or _SHA256_RE.fullmatch(row["sha256"]) is None
            or type(row.get("bytes")) is not int
            or row["bytes"] <= 0
            or not isinstance(row.get("git_blob_oid"), str)
            or _OID_RE.fullmatch(row["git_blob_oid"]) is None
            or row.get("git_mode") not in {"100644", "100755"}
            for row in expected_rows
        )
    ):
        problems.append(f"{label}:expected-artifact-contract")
    if authority.get("artifacts") != expected_rows:
        problems.append(f"{label}:artifacts")
    checks = authority.get("checks")
    if not isinstance(checks, list) or len(checks) != len(PUBLICATION_CHECKS):
        problems.append(f"{label}:checks")
    else:
        check_ids: list[int] = []
        for expected_name, row in zip(PUBLICATION_CHECKS, checks, strict=True):
            check_id = row.get("id") if isinstance(row, Mapping) else None
            if (
                not isinstance(row, Mapping)
                or set(row)
                != {"name", "id", "status", "conclusion", "head_sha", "app_slug"}
                or row.get("name") != expected_name
                or type(check_id) is not int
                or check_id <= 0
                or row.get("status") != "completed"
                or row.get("conclusion") != "success"
                or row.get("head_sha") != expected_commit
                or row.get("app_slug") != "github-actions"
            ):
                problems.append(f"{label}:check:{expected_name}")
            else:
                check_ids.append(check_id)
        if len(check_ids) != len(PUBLICATION_CHECKS) or len(set(check_ids)) != len(check_ids):
            problems.append(f"{label}:check-ids")
    return problems


def _observed_git_provenance(
    checkout: Path,
    manifest_module: types.ModuleType,
    *,
    include_smoke: bool,
) -> dict[str, Any]:
    names = tuple(getattr(manifest_module, "REQUIRED_PAYLOAD_NAMES"))
    paths = [MISSION_REL, *(f"{EXPERIMENT_REL}/{name}" for name in names)]
    paths.extend(
        (
            TOOLING_RECEIPT_REL,
            HOST_PACKET_REL,
            HOST_REL,
            ENV_REL,
        )
    )
    if include_smoke:
        paths.extend(SMOKE_EVIDENCE_PATHS)
    relative_paths = sorted(set(paths))
    status = _git(checkout, "status", "--porcelain", "--", *relative_paths)
    dirty_lines = sorted(line for line in status.decode("utf-8").splitlines() if line)
    problems = [f"git:dirty:{line}" for line in dirty_lines]
    file_commits: dict[str, str | None] = {}
    for relative in relative_paths:
        tracked = subprocess.run(  # noqa: S603 - fixed local Git probe
            (
                "/usr/bin/git",
                "-c",
                "core.hooksPath=/dev/null",
                "ls-files",
                "--error-unmatch",
                "--",
                relative,
            ),
            cwd=checkout,
            env={
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "HOME": str(checkout),
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
        if tracked.returncode != 0:
            problems.append(f"git:untracked:{relative}")
            file_commits[relative] = None
        else:
            commit = _git(checkout, "log", "-1", "--format=%H", "--", relative).decode(
                "ascii"
            ).strip()
            file_commits[relative] = commit or None
            if not commit:
                problems.append(f"git:no-commit:{relative}")
    hypothesis_rel = getattr(
        manifest_module,
        "HYPOTHESIS_REL",
        f"{EXPERIMENT_REL}/HYPOTHESIS.md",
    )
    hypothesis_commits = (
        _git(checkout, "log", "--reverse", "--format=%H", "--", hypothesis_rel)
        .decode("ascii")
        .splitlines()
    )
    if len(hypothesis_commits) < 2:
        problems.append("git:hypothesis-amendment-history")
    for commit in hypothesis_commits:
        touched = sorted(
            line
            for line in _git(
                checkout,
                "show",
                "--pretty=format:",
                "--name-only",
                commit,
            )
            .decode("utf-8")
            .splitlines()
            if line
        )
        if touched != [hypothesis_rel]:
            problems.append(f"git:hypothesis-commit-not-isolated:{commit}")
    latest_hypothesis = hypothesis_commits[-1] if hypothesis_commits else None
    if latest_hypothesis is not None:
        for relative, commit in file_commits.items():
            if relative == hypothesis_rel or commit is None:
                continue
            if subprocess.run(  # noqa: S603 - fixed local ancestry probe
                (
                    "/usr/bin/git",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "merge-base",
                    "--is-ancestor",
                    latest_hypothesis,
                    commit,
                ),
                cwd=checkout,
                env={
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_OPTIONAL_LOCKS": "0",
                    "GIT_TERMINAL_PROMPT": "0",
                    "HOME": str(checkout),
                    "LANG": "C",
                    "LC_ALL": "C",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                },
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            ).returncode != 0:
                problems.append(f"git:tool-predates-hypothesis:{relative}")
    head = _git(checkout, "rev-parse", "HEAD").decode("ascii").strip()
    unique = sorted(set(problems))
    return {
        "schema": "iter135.git_provenance.v1",
        "verdict": "I135_GIT_PROVENANCE_OK" if not unique else "I135_GIT_PROVENANCE_INCOMPLETE",
        "head": head,
        "hypothesis_commits": hypothesis_commits,
        "latest_hypothesis_commit": latest_hypothesis,
        "file_commits": dict(sorted(file_commits.items())),
        "dirty_lines": dirty_lines,
        "problem_count": len(unique),
        "problems": unique,
    }


def _green_receipt(
    receipt: Mapping[str, Any], schema: str, verdict: str, label: str
) -> list[str]:
    problems: list[str] = []
    if receipt.get("schema") != schema:
        problems.append(f"{label}:schema")
    if receipt.get("verdict") != verdict:
        problems.append(f"{label}:verdict")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        problems.append(f"{label}:problem-metadata")
    return problems


def _validate_pre_smoke_manifest(manifest: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if manifest.get("schema") != MANIFEST_SCHEMA:
        problems.append("pre-smoke:schema")
    if manifest.get("verdict") != PRE_SMOKE_VERDICT:
        problems.append("pre-smoke:verdict")
    if manifest.get("launch_authorized") is not False:
        problems.append("pre-smoke:launch-authorized")
    if manifest.get("mission_phase") != TOOLING_PHASE:
        problems.append("pre-smoke:mission-phase")
    if manifest.get("missing_artifacts") != ["smoke-evidence/smoke_receipt.json"]:
        problems.append("pre-smoke:missing-artifacts")
    if manifest.get("problem_count") != 1 or manifest.get("problems") != [
        "smoke:receipt-missing"
    ]:
        problems.append("pre-smoke:problem-contract")
    return problems


def _validate_final_manifest(
    manifest: Mapping[str, Any],
    *,
    state_payload: bytes,
    host_packet_payload: bytes,
    host_payload: bytes,
    env_payload: bytes,
    smoke_payload: bytes,
) -> list[str]:
    problems: list[str] = []
    if manifest.get("schema") != MANIFEST_SCHEMA:
        problems.append("final-manifest:schema")
    if manifest.get("verdict") != FINAL_MANIFEST_VERDICT:
        problems.append("final-manifest:verdict")
    if manifest.get("launch_authorized") is not True:
        problems.append("final-manifest:launch-authorized")
    if manifest.get("mission_phase") != LAUNCH_PHASE:
        problems.append("final-manifest:mission-phase")
    if manifest.get("problem_count") != 0 or manifest.get("problems") != []:
        problems.append("final-manifest:problem-metadata")
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or not gates or any(value is not True for value in gates.values()):
        problems.append("final-manifest:gates")
    state_binding = manifest.get("mission_state")
    if state_binding != {
        "source_path": MISSION_REL,
        "sha256": hashlib.sha256(state_payload).hexdigest(),
        "bytes": len(state_payload),
    }:
        problems.append("final-manifest:mission-state-binding")
    bound = manifest.get("hash_bound_files")
    expected = {
        "host_packet_manifest.json": host_packet_payload,
        "host_preparation_receipt.json": host_payload,
        "env_receipts.json": env_payload,
        "smoke-evidence/smoke_receipt.json": smoke_payload,
    }
    if not isinstance(bound, Mapping):
        problems.append("final-manifest:hash-bound-files")
    else:
        for relative, payload in expected.items():
            row = bound.get(relative)
            if not isinstance(row, Mapping) or row.get("sha256") != hashlib.sha256(
                payload
            ).hexdigest() or row.get("bytes") != len(payload):
                problems.append(f"final-manifest:binding:{relative}")
        if manifest.get("host_preparation_receipt") != bound.get(
            "host_preparation_receipt.json"
        ):
            problems.append("final-manifest:host-preparation-link")
        if manifest.get("host_packet_manifest") != bound.get("host_packet_manifest.json"):
            problems.append("final-manifest:host-packet-link")
    return problems


def _deep_replay_publication(
    repo: Path,
    *,
    tooling_receipt_commit: str,
    tooling_baton_commit: str,
    commits: Sequence[str],
) -> list[str]:
    """Replay H/E/P/S[/A/F] from the active frozen tooling source in isolation."""

    problems: list[str] = []
    try:
        source_commit = _tooling_source_commit(repo, tooling_receipt_commit)
    except (AuthorizationError, OSError, subprocess.SubprocessError) as exc:
        return [f"authorization:frozen-source:{type(exc).__name__}:{exc}"]
    if not commits:
        return []

    with tempfile.TemporaryDirectory(prefix="sentinel-i135-authority-") as temporary:
        checkout = Path(temporary) / "replay"
        try:
            _isolated_clone(repo, checkout)
            _checkout(repo, checkout, commits[0])
            for relative in FROZEN_REPLAY_PATHS:
                if _stable_bytes(checkout / relative) != _blob(repo, source_commit, relative):
                    problems.append(f"authorization:frozen-validator-drift:{relative}")

            prepare = _module_from_checkout(
                repo, checkout, source_commit, PREPARE_REL, "prepare"
            )
            capture = _module_from_checkout(
                repo, checkout, source_commit, CAPTURE_REL, "capture"
            )
            manifest_builder = _module_from_checkout(
                repo, checkout, source_commit, MANIFEST_BUILDER_REL, "manifest_h"
            )
            packet_names = tuple(getattr(prepare, "REQUIRED_PACKET_FILES"))
            if set(packet_names) != set(getattr(manifest_builder, "HOST_PACKET_FILE_NAMES")):
                problems.append("host:packet-validator-contract-drift")
            if set(packet_names) != set(
                getattr(capture, "EXPECTED_PREPARATION_PACKET_FILES")
            ):
                problems.append("host:capture-packet-contract-drift")
            expected_files = _packet_bindings(repo, tooling_baton_commit, packet_names)
            # The committed packet manifest carries exactly three fields per file, so the
            # exact-rebuild comparison below uses this projection. The frozen evidence
            # validator additionally reads `git_blob_oid` and `git_mode` from its
            # `expected_file_bindings` argument, so it must receive the FULL binding rows;
            # passing this projection there made the authority-artifact expectation `None`
            # and unconditionally red.
            expected_packet_files = {
                name: {
                    field: row[field]
                    for field in ("sha256", "bytes", "mode")
                }
                for name, row in expected_files.items()
            }
            expected_modes = dict(getattr(prepare, "EXPECTED_PACKET_MODES"))
            if expected_modes != {
                name: row["mode"] for name, row in expected_files.items()
            }:
                problems.append("host:packet-mode-contract-drift")
            packet_payload = _blob(repo, commits[0], HOST_PACKET_REL)
            packet = _strict_json_object(packet_payload, HOST_PACKET_REL)
            expected_packet = {
                "schema": HOST_PACKET_SCHEMA,
                "source_commit": tooling_baton_commit,
                "files": expected_packet_files,
            }
            if packet != expected_packet:
                problems.append("host:packet-exact-rebuild")
            host_payload = _blob(repo, commits[0], HOST_REL)
            host = _strict_json_object(host_payload, HOST_REL)
            packet_binding = {
                "source_path": HOST_PACKET_REL,
                "sha256": hashlib.sha256(packet_payload).hexdigest(),
                "bytes": len(packet_payload),
            }
            validator = getattr(
                manifest_builder, "validate_host_preparation_evidence", None
            )
            if not callable(validator):
                raise AuthorizationError("frozen host evidence validator is missing")
            host_validator_problems = validator(
                packet,
                host,
                packet_binding=packet_binding,
                expected_file_bindings=expected_files,
            )
            if not isinstance(host_validator_problems, list) or any(
                not isinstance(item, str) for item in host_validator_problems
            ):
                raise AuthorizationError("frozen host validator returned malformed problems")
            problems.extend(f"host:validator:{item}" for item in host_validator_problems)
            problems.extend(
                _validate_host_receipt_deep(
                    host,
                    packet=packet if isinstance(packet, Mapping) else {},
                    packet_payload=packet_payload,
                    expected_files=expected_files,
                    tooling_baton_commit=tooling_baton_commit,
                )
            )

            environment: dict[str, Any] | None = None
            env_payload: bytes | None = None
            if len(commits) >= 2:
                _checkout(repo, checkout, commits[1])
                manifest_builder = _module_from_checkout(
                    repo,
                    checkout,
                    source_commit,
                    MANIFEST_BUILDER_REL,
                    "manifest_e",
                )
                environment = _json_blob(repo, commits[1], ENV_REL)
                env_payload = _blob(repo, commits[1], ENV_REL)
                problems.extend(
                    _green_receipt(environment, ENV_SCHEMA, ENV_VERDICT, "environment")
                )
                environment_validator = getattr(
                    manifest_builder, "validate_environment_receipt", None
                )
                if not callable(environment_validator):
                    raise AuthorizationError("frozen environment validator is missing")
                # The frozen environment validator additionally reads the compose patcher's
                # binding from `bound_hashes` and requires the two host-authority artifact
                # rows to be supplied explicitly; omitting either made its checks fire
                # against a true receipt at the first live E-commit validation.
                patcher_payload = _blob(
                    repo,
                    tooling_baton_commit,
                    f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
                )
                bound_hashes = {
                    "host_packet_manifest.json": packet_binding,
                    "host_preparation_receipt.json": {
                        "source_path": HOST_REL,
                        "sha256": hashlib.sha256(host_payload).hexdigest(),
                        "bytes": len(host_payload),
                    },
                    "patch_compose_dose_env.py": {
                        "source_path": f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
                        "sha256": hashlib.sha256(patcher_payload).hexdigest(),
                        "bytes": len(patcher_payload),
                    },
                }
                expected_host_artifacts = [
                    {
                        "path": HOST_PACKET_REL,
                        "sha256": hashlib.sha256(packet_payload).hexdigest(),
                        "bytes": len(packet_payload),
                        "git_blob_oid": _git_blob_oid(packet_payload),
                        "git_mode": "100644",
                    },
                    {
                        "path": HOST_REL,
                        "sha256": hashlib.sha256(host_payload).hexdigest(),
                        "bytes": len(host_payload),
                        "git_blob_oid": _git_blob_oid(host_payload),
                        "git_mode": "100644",
                    },
                ]
                environment_problems = environment_validator(
                    environment,
                    bound_hashes,
                    expected_host_preparation=host,
                    expected_host_authority_artifacts=expected_host_artifacts,
                )
                if not isinstance(environment_problems, list) or any(
                    not isinstance(item, str) for item in environment_problems
                ):
                    raise AuthorizationError(
                        "frozen environment validator returned malformed problems"
                    )
                problems.extend(
                    f"environment:validator:{item}" for item in environment_problems
                )
                host_preparation = environment.get("host_preparation")
                if (
                    not isinstance(host_preparation, Mapping)
                    or host_preparation.get("evidence") != host
                    or not isinstance(host_preparation.get("receipt_file"), Mapping)
                    or host_preparation["receipt_file"].get("sha256")
                    != hashlib.sha256(host_payload).hexdigest()
                    or host_preparation["receipt_file"].get("bytes") != len(host_payload)
                ):
                    problems.append("environment:host-preparation-deep-link")
                problems.extend(
                    _validate_publication_authority(
                        environment.get("host_publication_authority"),
                        expected_commit=commits[0],
                        expected_artifacts=expected_host_artifacts,
                        label="environment:host-publication-authority",
                    )
                )
                docker_runtime = environment.get("docker_runtime")
                if (
                    not isinstance(docker_runtime, Mapping)
                    or docker_runtime.get("schema") != "iter135.docker_runtime_receipt.v1"
                ):
                    problems.append("environment:docker-runtime-source-binding")

            if len(commits) >= 3:
                if environment is None or env_payload is None:
                    raise AuthorizationError("pre-smoke replay lacks environment evidence")
                # P was generated with E as clean HEAD.  Recompute its provenance with fixed Git
                # and feed that observation into the frozen builder; never trust P's own claim.
                _checkout(repo, checkout, commits[1])
                # The frozen manifest builder runs a tooling-receipt gate that requires
                # origin/master to be an ancestor of the current HEAD.  P was generated when its
                # parent (commits[1]) was the clean HEAD and origin/master pointed at it; but by
                # replay time the tip has advanced past commits[1], and the isolated --shared
                # clone inherits that advanced tip as origin/master, which would inject a spurious
                # `origin/master is not an ancestor of current HEAD` problem into the rebuild.
                # Pin origin/master back to the exact stage parent so the rebuild sees the same
                # ref state P was generated under; every other gate is unchanged.
                _git(checkout, "update-ref", "refs/remotes/origin/master", commits[1])
                manifest_builder = _module_from_checkout(
                    repo,
                    checkout,
                    source_commit,
                    MANIFEST_BUILDER_REL,
                    "manifest_p",
                )
                observed_p = _observed_git_provenance(
                    checkout, manifest_builder, include_smoke=False
                )
                build_manifest = getattr(manifest_builder, "build_manifest", None)
                if not callable(build_manifest):
                    raise AuthorizationError("frozen launch manifest builder is missing")
                rebuilt_pre = build_manifest(
                    repo_root=checkout,
                    experiment_dir=checkout / EXPERIMENT_REL,
                    mission_state_path=checkout / MISSION_REL,
                    git_provenance=observed_p,
                )
                if not isinstance(rebuilt_pre, dict):
                    raise AuthorizationError("frozen pre-smoke builder returned non-object")
                committed_pre_payload = _blob(repo, commits[2], MANIFEST_REL)
                if _canonical_pretty_json(rebuilt_pre) != committed_pre_payload:
                    problems.append("pre-smoke:exact-rebuild-mismatch")
                problems.extend(_validate_pre_smoke_manifest(rebuilt_pre))

            if len(commits) >= 4:
                _checkout(repo, checkout, commits[3])
                smoke_validator = _module_from_checkout(
                    repo,
                    checkout,
                    source_commit,
                    SMOKE_VALIDATOR_REL,
                    "smoke",
                )
                experiment = checkout / EXPERIMENT_REL
                recomputer = getattr(smoke_validator, "recompute_smoke_receipt", None)
                canonicalizer = getattr(
                    smoke_validator, "canonical_smoke_receipt_bytes", None
                )
                renderer = getattr(smoke_validator, "render_smoke_summary", None)
                if not all(callable(item) for item in (recomputer, canonicalizer, renderer)):
                    raise AuthorizationError("frozen smoke replay API is incomplete")
                recomputed_smoke = recomputer(experiment)
                if not isinstance(recomputed_smoke, dict):
                    raise AuthorizationError("frozen smoke recomputer returned non-object")
                expected_receipt_bytes = canonicalizer(recomputed_smoke)
                if expected_receipt_bytes != _blob(repo, commits[3], SMOKE_RECEIPT_REL):
                    problems.append("smoke:receipt-recomputation-mismatch")
                if renderer(recomputed_smoke, expected_receipt_bytes) != _blob(
                    repo, commits[3], f"{SMOKE_ROOT_REL}/SMOKE.md"
                ):
                    problems.append("smoke:summary-recomputation-mismatch")
                problems.extend(
                    _green_receipt(
                        recomputed_smoke,
                        SMOKE_SCHEMA,
                        SMOKE_VERDICT,
                        "smoke",
                    )
                )
                if (
                    recomputed_smoke.get("nonanalytic") is not True
                    or recomputed_smoke.get("analytic_episode_count") != 0
                ):
                    problems.append("smoke:analytic-boundary")
                if _blob(repo, commits[3], RAW_PRE_MANIFEST_REL) != _blob(
                    repo, commits[2], MANIFEST_REL
                ):
                    problems.append("smoke:pre-manifest-link")
                if _blob(repo, commits[3], RAW_ENV_REL) != _blob(
                    repo, commits[1], ENV_REL
                ):
                    problems.append("smoke:environment-link")
                pre_state_payload = _blob(repo, commits[3], RAW_PRE_STATE_REL)
                baton_state_payload = _blob(repo, tooling_baton_commit, MISSION_REL)
                if pre_state_payload != baton_state_payload:
                    problems.append("smoke:pre-state-baton-link")
                pre_manifest = _json_blob(repo, commits[2], MANIFEST_REL)
                mission_binding = pre_manifest.get("mission_state")
                if mission_binding != {
                    "source_path": MISSION_REL,
                    "sha256": hashlib.sha256(pre_state_payload).hexdigest(),
                    "bytes": len(pre_state_payload),
                }:
                    problems.append("smoke:pre-state-manifest-link")

            if len(commits) >= 6:
                _checkout(repo, checkout, commits[4])
                # Same replay-time origin/master hazard as the pre-smoke rebuild above: the final
                # manifest was generated with commits[4] as the clean HEAD, so pin origin/master
                # to it before rebuilding so the builder's tooling-receipt gate sees the exact ref
                # state F was generated under instead of the advanced replay tip.
                _git(checkout, "update-ref", "refs/remotes/origin/master", commits[4])
                manifest_builder = _module_from_checkout(
                    repo,
                    checkout,
                    source_commit,
                    MANIFEST_BUILDER_REL,
                    "manifest_f",
                )
                observed_f = _observed_git_provenance(
                    checkout, manifest_builder, include_smoke=True
                )
                build_manifest = getattr(manifest_builder, "build_manifest", None)
                if not callable(build_manifest):
                    raise AuthorizationError("frozen final manifest builder is missing")
                rebuilt_final = build_manifest(
                    repo_root=checkout,
                    experiment_dir=checkout / EXPERIMENT_REL,
                    mission_state_path=checkout / MISSION_REL,
                    git_provenance=observed_f,
                )
                if not isinstance(rebuilt_final, dict):
                    raise AuthorizationError("frozen final builder returned non-object")
                if _canonical_pretty_json(rebuilt_final) != _blob(
                    repo, commits[5], MANIFEST_REL
                ):
                    problems.append("final-manifest:exact-rebuild-mismatch")
                if rebuilt_final.get("git_provenance") != observed_f:
                    problems.append("final-manifest:observed-git-provenance")
        except Exception as exc:  # noqa: BLE001 - every frozen replay fault fails closed
            problems.append(f"authorization:deep-replay:{type(exc).__name__}:{exc}")
    return sorted(set(problems))


def build_activation_receipt(
    repo: Path,
    *,
    tooling_receipt_commit: str,
    host_commit: str,
    environment_commit: str,
    pre_smoke_manifest_commit: str,
    smoke_commit: str,
    state_commit: str,
    final_manifest_commit: str,
) -> dict[str, Any]:
    """Build the deterministic receipt committed with the B activation baton."""

    root = Path(repo).resolve(strict=True)
    commit_map = {
        "tooling_receipt": tooling_receipt_commit,
        "host_preparation": host_commit,
        "environment": environment_commit,
        "pre_smoke_manifest": pre_smoke_manifest_commit,
        "smoke": smoke_commit,
        "state": state_commit,
        "final_manifest": final_manifest_commit,
        "baton_parent": final_manifest_commit,
    }
    if any(_OID_RE.fullmatch(value) is None for value in commit_map.values()):
        raise AuthorizationError("activation commit map contains a malformed commit")
    artifacts = {
        "mission_state": _binding(MISSION_REL, _blob(root, state_commit, MISSION_REL)),
        "host_preparation": _binding(HOST_REL, _blob(root, host_commit, HOST_REL)),
        "host_packet_manifest": _binding(
            HOST_PACKET_REL, _blob(root, host_commit, HOST_PACKET_REL)
        ),
        "environment": _binding(ENV_REL, _blob(root, environment_commit, ENV_REL)),
        "pre_smoke_manifest": _binding(
            MANIFEST_REL, _blob(root, pre_smoke_manifest_commit, MANIFEST_REL)
        ),
        "smoke_receipt": _binding(
            SMOKE_RECEIPT_REL, _blob(root, smoke_commit, SMOKE_RECEIPT_REL)
        ),
        "final_manifest": _binding(
            MANIFEST_REL, _blob(root, final_manifest_commit, MANIFEST_REL)
        ),
    }
    receipt: dict[str, Any] = {
        "schema": ACTIVATION_SCHEMA,
        "verdict": ACTIVATION_VERDICT,
        "problem_count": 0,
        "problems": [],
        "phase": LAUNCH_PHASE,
        "commits": commit_map,
        "artifacts": artifacts,
    }
    receipt["receipt_payload_sha256"] = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    return receipt


def validate_publication_descendants(
    repo: Path,
    *,
    phase: str,
    tooling_receipt_commit: str,
    tooling_baton_commit: str,
    descendants: Sequence[str],
    upstream_commit: str,
    candidate: bool = False,
) -> dict[str, Any]:
    """Validate the ordered H/E/P/S[/A/F/B] chain and return reference commits."""

    root = Path(repo).resolve(strict=True)
    problems: list[str] = []
    commits = tuple(descendants)
    required = 4 if phase == TOOLING_PHASE else 7 if phase == LAUNCH_PHASE else -1
    if required < 0:
        return {
            "problems": [f"authorization:unsupported-phase:{phase}"],
            "references": {},
            "authority": "none",
            "launch_authorized": False,
        }
    if candidate and phase != LAUNCH_PHASE:
        return {
            "problems": ["authorization:candidate-requires-launch-phase"],
            "references": {},
            "authority": "none",
            "launch_authorized": False,
            "candidate_valid": False,
        }
    if phase == TOOLING_PHASE and len(commits) > 4:
        problems.append(f"authorization:tooling-descendant-count:{len(commits)}")
    if phase == LAUNCH_PHASE and len(commits) != 7:
        problems.append(f"authorization:launch-descendant-count:{len(commits)}")

    expected_stages = (*PREFLIGHT_STAGE_PATHS, *LAUNCH_STAGE_PATHS)
    previous = tooling_baton_commit
    for index, commit in enumerate(commits):
        try:
            parents, paths = _commit_row(root, commit)
        except (OSError, subprocess.SubprocessError, AuthorizationError) as exc:
            problems.append(f"authorization:commit-probe:{index}:{type(exc).__name__}")
            break
        if parents != (previous,):
            problems.append(f"authorization:nonlinear:{index}")
        if index >= len(expected_stages) or paths != tuple(sorted(expected_stages[index])):
            problems.append(f"authorization:scope:{index}:{list(paths)}")
        previous = commit

    references: dict[str, str] = {}
    publication_tip = commits[-1] if commits else tooling_baton_commit
    # Containment is insufficient authority: origin/master may have advanced to unrelated or
    # unreviewed bytes after this chain.  Normal validation binds the exact published tip; local
    # A/F/B candidate validation binds the exact already-published smoke commit S.
    expected_upstream = commits[3] if candidate and len(commits) >= 4 else publication_tip
    if upstream_commit != expected_upstream:
        problems.append(
            "authorization:preflight-not-on-origin-master"
            if candidate
            else "authorization:head-not-on-origin-master"
        )

    if candidate:
        try:
            head = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
            status = _git(root, "status", "--porcelain=v1", "-z")
        except (OSError, subprocess.SubprocessError, AuthorizationError):
            head = ""
            status = b"probe-failed"
        if not commits or head != commits[-1]:
            problems.append("authorization:candidate-head-not-baton")
        if status:
            problems.append("authorization:candidate-worktree-dirty")

    problems.extend(
        _deep_replay_publication(
            root,
            tooling_receipt_commit=tooling_receipt_commit,
            tooling_baton_commit=tooling_baton_commit,
            commits=commits,
        )
    )

    try:
        if len(commits) >= 1:
            host = _json_blob(root, commits[0], HOST_REL)
            problems.extend(_green_receipt(host, HOST_SCHEMA, HOST_VERDICT, "host"))
            host_packet_payload = _blob(root, commits[0], HOST_PACKET_REL)
            host_packet = _strict_json_object(host_packet_payload, HOST_PACKET_REL)
            host_payload = dict(host)
            claimed_host_payload_sha256 = host_payload.pop("receipt_payload_sha256", None)
            embedded_packet = host.get("packet")
            embedded_manifest = (
                embedded_packet.get("manifest") if isinstance(embedded_packet, Mapping) else None
            )
            if (
                not isinstance(host_packet, dict)
                or set(host_packet) != {"schema", "source_commit", "files"}
                or host_packet.get("schema") != HOST_PACKET_SCHEMA
                or not isinstance(host_packet.get("source_commit"), str)
                or _OID_RE.fullmatch(host_packet["source_commit"]) is None
                or host_packet.get("source_commit") != tooling_baton_commit
                or not isinstance(host_packet.get("files"), dict)
                or host.get("packet_manifest_sha256")
                != hashlib.sha256(host_packet_payload).hexdigest()
                or claimed_host_payload_sha256
                != hashlib.sha256(_canonical_json(host_payload)).hexdigest()
                or not isinstance(embedded_packet, Mapping)
                or embedded_packet.get("schema") != HOST_PACKET_SCHEMA
                or embedded_packet.get("source_commit") != host_packet.get("source_commit")
                or not isinstance(embedded_manifest, Mapping)
                or embedded_manifest.get("sha256")
                != hashlib.sha256(host_packet_payload).hexdigest()
            ):
                problems.append("host:packet-manifest-binding")
            references[HOST_REL] = commits[0]
            references[HOST_PACKET_REL] = commits[0]
        if len(commits) >= 2:
            environment = _json_blob(root, commits[1], ENV_REL)
            problems.extend(_green_receipt(environment, ENV_SCHEMA, ENV_VERDICT, "environment"))
            references[ENV_REL] = commits[1]
        if len(commits) >= 3:
            pre_manifest = _json_blob(root, commits[2], MANIFEST_REL)
            problems.extend(_validate_pre_smoke_manifest(pre_manifest))
            references[MANIFEST_REL] = commits[2]
        if len(commits) >= 4:
            smoke = _json_blob(root, commits[3], SMOKE_RECEIPT_REL)
            problems.extend(_green_receipt(smoke, SMOKE_SCHEMA, SMOKE_VERDICT, "smoke"))
            if smoke.get("nonanalytic") is not True or smoke.get("analytic_episode_count") != 0:
                problems.append("smoke:analytic-boundary")
            if _blob(root, commits[3], RAW_PRE_MANIFEST_REL) != _blob(
                root, commits[2], MANIFEST_REL
            ):
                problems.append("smoke:pre-manifest-link")
            if _blob(root, commits[3], RAW_ENV_REL) != _blob(root, commits[1], ENV_REL):
                problems.append("smoke:environment-link")
            references[SMOKE_RECEIPT_REL] = commits[3]
        if len(commits) >= 7:
            state_payload = _blob(root, commits[4], MISSION_REL)
            state = _strict_json_object(state_payload, MISSION_REL)
            if not isinstance(state, dict) or state.get("next_program", {}).get("phase") != LAUNCH_PHASE:
                problems.append("authorization:state-phase")
            env_payload = _blob(root, commits[1], ENV_REL)
            host_payload = _blob(root, commits[0], HOST_REL)
            host_packet_payload = _blob(root, commits[0], HOST_PACKET_REL)
            smoke_payload = _blob(root, commits[3], SMOKE_RECEIPT_REL)
            final_manifest = _json_blob(root, commits[5], MANIFEST_REL)
            problems.extend(
                _validate_final_manifest(
                    final_manifest,
                    state_payload=state_payload,
                    host_packet_payload=host_packet_payload,
                    host_payload=host_payload,
                    env_payload=env_payload,
                    smoke_payload=smoke_payload,
                )
            )
            actual_activation = _json_blob(root, commits[6], ACTIVATION_REL)
            expected_activation = build_activation_receipt(
                root,
                tooling_receipt_commit=tooling_receipt_commit,
                host_commit=commits[0],
                environment_commit=commits[1],
                pre_smoke_manifest_commit=commits[2],
                smoke_commit=commits[3],
                state_commit=commits[4],
                final_manifest_commit=commits[5],
            )
            if actual_activation != expected_activation:
                problems.append("authorization:activation-receipt")
            references[MISSION_REL] = commits[4]
            references[MANIFEST_REL] = commits[5]
            references[ACTIVATION_REL] = commits[6]
    except (OSError, subprocess.SubprocessError, AuthorizationError, json.JSONDecodeError) as exc:
        problems.append(f"authorization:artifact-probe:{type(exc).__name__}:{exc}")

    physical_references: dict[str, str] = {}
    if len(commits) >= 1:
        physical_references[HOST_REL] = commits[0]
        physical_references[HOST_PACKET_REL] = commits[0]
    if len(commits) >= 2:
        physical_references[ENV_REL] = commits[1]
    if len(commits) >= 3:
        physical_references[MANIFEST_REL] = commits[2]
    if len(commits) >= 4:
        physical_references.update({relative: commits[3] for relative in SMOKE_EVIDENCE_PATHS})
    if len(commits) >= 7:
        physical_references[MISSION_REL] = commits[4]
        physical_references[MANIFEST_REL] = commits[5]
        physical_references[ACTIVATION_REL] = commits[6]
        physical_references["CONTINUITY.md"] = commits[6]
        physical_references["HANDOFF.md"] = commits[6]
    for relative, commit in physical_references.items():
        try:
            if _stable_bytes(root / relative) != _blob(root, commit, relative):
                problems.append(f"authorization:physical-drift:{relative}")
        except (OSError, subprocess.SubprocessError, AuthorizationError) as exc:
            problems.append(f"authorization:physical-probe:{relative}:{type(exc).__name__}")

    unique_problems = sorted(set(problems))
    if candidate:
        candidate_valid = not unique_problems
        unique_problems.append("authorization:candidate-non-authoritative")
        return {
            "problems": sorted(set(unique_problems)),
            "references": references,
            "authority": "non-authoritative-local-candidate",
            "launch_authorized": False,
            "candidate_valid": candidate_valid,
        }
    launch_authorized = phase == LAUNCH_PHASE and not unique_problems
    return {
        "problems": unique_problems,
        "references": references,
        "authority": "origin-published" if launch_authorized else "none",
        "launch_authorized": launch_authorized,
    }


def validate_local_candidate(
    repo: Path,
    *,
    tooling_receipt_commit: str,
    tooling_baton_commit: str,
    descendants: Sequence[str],
    upstream_commit: str,
) -> dict[str, Any]:
    """Validate a complete clean local A/F/B candidate without granting launch authority."""

    return validate_publication_descendants(
        repo,
        phase=LAUNCH_PHASE,
        tooling_receipt_commit=tooling_receipt_commit,
        tooling_baton_commit=tooling_baton_commit,
        descendants=descendants,
        upstream_commit=upstream_commit,
        candidate=True,
    )


def _stable_json(path: Path) -> dict[str, Any]:
    return _strict_json_object(_stable_bytes(path), str(path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--tooling-receipt-commit", required=True)
    parser.add_argument("--host-commit", required=True)
    parser.add_argument("--environment-commit", required=True)
    parser.add_argument("--pre-smoke-manifest-commit", required=True)
    parser.add_argument("--smoke-commit", required=True)
    parser.add_argument("--state-commit", required=True)
    parser.add_argument("--final-manifest-commit", required=True)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args(argv)
    receipt = build_activation_receipt(
        args.repo,
        tooling_receipt_commit=args.tooling_receipt_commit,
        host_commit=args.host_commit,
        environment_commit=args.environment_commit,
        pre_smoke_manifest_commit=args.pre_smoke_manifest_commit,
        smoke_commit=args.smoke_commit,
        state_commit=args.state_commit,
        final_manifest_commit=args.final_manifest_commit,
    )
    if args.validate is not None:
        observed = _stable_json(args.validate)
        if observed != receipt:
            print("I135_LAUNCH_ACTIVATION_INVALID")
            return 1
        print("I135_LAUNCH_ACTIVATION_OK")
        return 0
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
