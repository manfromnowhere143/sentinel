#!/usr/bin/env python3
"""Recompute Iteration-135 G5 from raw live-smoke evidence.

The receipt written by this module is a deterministic projection of raw decision rows, raw
``env -0`` output captured inside each model container, the execution journal, compose output,
the frozen schedule, and pre-smoke provenance receipts.  No pass/fail claim already present in a
receipt is consumed.  ``recompute_smoke_receipt`` is the side-effect-free integration hook for
the launch-manifest builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
RAW_REL = Path("smoke-evidence/raw")
RECEIPT_REL = Path("smoke-evidence/smoke_receipt.json")

RECEIPT_SCHEMA = "iter135.smoke_receipt.v1"
RAW_SCHEMA = "iter135.smoke_execution.v1"
OK_VERDICT = "I135_LIVE_SMOKE_OK"
FAIL_VERDICT = "I135_LIVE_SMOKE_INFRA_NULL"
ENV_SCHEMA = "iter135.environment_receipts.v2"
ENV_VERDICT = "I135_ENVIRONMENT_PREFLIGHT_OK"
MANIFEST_SCHEMA = "iter135.launch_manifest.v2"
PRE_SMOKE_VERDICT = "I135_TOOLING_MANIFEST_INCOMPLETE"
MISSION_STATE_SCHEMA = "sentinel.mission_state.v1"
CANONICAL_REPOSITORY = "/Users/danielwahnich/workspace/sentinel"
WORKSPACE_BOUNDARY = {
    "isolated_from": "/Users/danielwahnich/workspace/aweb",
    "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
    "cross_workspace_access_requires_explicit_operator_request": True,
}
MISSION_STATE_FIELDS = {
    "schema",
    "canonical_repository",
    "workspace_boundary",
    "trunk",
    "current_completed_iteration",
    "current_result",
    "current_verdict",
    "run_state",
    "active_hypothesis",
    "next_program",
    "claim_state",
    "deprecated_pending_hypotheses",
    "paper_state",
    "storage_gate",
}
PREFLIGHT_AUTHORIZED_ACTIONS = [
    (
        "prepare only the exact hash-bound sentinel-gpu host contract, including the dedicated "
        "iteration-135 output root"
    ),
    "capture and commit the read-only iteration-135 environment receipt on sentinel-gpu",
    (
        "generate and commit only the hash-addressed incomplete pre-smoke manifest; no analytic "
        "episodes"
    ),
    (
        "run exactly the hash-bound four-run nonanalytic G5 smoke after the incomplete pre-smoke "
        "manifest is committed"
    ),
    "validate, collect, and commit the exact nonanalytic smoke evidence and receipt",
]
PREFLIGHT_FORBIDDEN_ACTIONS = [
    (
        "run any iteration-135 analytic episode before smoke evidence and the final launch "
        "manifest are committed green"
    ),
    "remove or bypass the permanent analytic launch lock",
    (
        "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies "
        "after evidence"
    ),
    "place any iteration-135 analytic output on the remote root filesystem",
]
PREFLIGHT_PROGRAM = {
    "iteration": 135,
    "name": "semantics-free placebo dose-response causal closure",
    "phase": "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
    "authorized_actions": PREFLIGHT_AUTHORIZED_ACTIONS,
    "forbidden_actions": PREFLIGHT_FORBIDDEN_ACTIONS,
}
MISSION_STORAGE_GATE = {
    "minimum_local_free_gib_before_new_proof_collection": 15,
    "remote_execution_filesystem_path": "/datasets/nuscenes-full",
    "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
    "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
    "policy": (
        "preserve committed proof and hashes; delete only hash-verified duplicates, "
        "reproducible renders, and caches"
    ),
}
DATASET_SCHEMA = "iter135.nuscenes_dataset_receipt.v1"
DATASET_CONTRACT_SHA256 = (
    "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
)

BLIND_DOSES = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
REQUIRED_MODEL_ENV = (
    "SENTINEL_ENABLED",
    "SENTINEL_DOSE_PAIR",
    "SENTINEL_DOSE_ID",
    "SENTINEL_DOSE_SCHEDULE",
    "SENTINEL_LOG",
    "SENTINEL_RELEASE_K",
)
ANALYTIC_OUTPUT_ROOT = "/datasets/nuscenes-full/sentinel-i135-outoutput"
SMOKE_OUTPUT_ROOT = "/datasets/nuscenes-full/sentinel-i135-smoke-evidence"
SMOKE_EPISODE_ROOT = f"{SMOKE_OUTPUT_ROOT}/episodes"
MODEL_LOG_ROOT = "/model/i135-smoke-staging"
GPU_CEILING_NS = 110 * 60 * 60 * 1_000_000_000
EXPECTED_BLIND_PATCHED_SERVER_SHA256 = (
    "b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf"
)
GPU_FIELDS = {"model", "count", "uuid", "driver_version", "memory_total_mib"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_RE = re.compile(r"^[0-9]+:[0-9]+$")
EXPECTED_GPU = {
    "model": "NVIDIA L4",
    "count": 1,
    "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
    "driver_version": "580.159.03",
    "memory_total_mib": 23034,
}
EXPECTED_IMAGE_IDS = {
    "ncap:latest": "sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce",
    "neurad:latest": "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c",
    "uniad:latest": "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb",
}
DATASET_ROOT = "/datasets/nuscenes-full"
DATASET_VERSION = "v1.0-trainval"
DATASET_ARCHIVE_ROOT = f"{DATASET_ROOT}/archives"
DATASET_METADATA_ROOT = f"{DATASET_ROOT}/{DATASET_VERSION}"
DATASET_MAP_ROOT = f"{DATASET_ROOT}/maps"
DATASET_MOUNT = {
    "mount_target": DATASET_ROOT,
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}
DATASET_PROOF_BASIS = {
    "iteration": 28,
    "result_path": "experiments/iter28_nuscenes_trainval_staging/RESULT.md",
    "receipt_directory": "experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads",
    "archive_count": 11,
    "archive_total_bytes": 314_886_603_672,
}
DATASET_ARCHIVES = {
    "v1.0-trainval_meta.tgz": (
        "db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b",
        461_678_030,
    ),
    "v1.0-trainval01_blobs.tgz": (
        "fee4316c55f0780532819ea1b01f347b2ad964303c93477cc815f8191b126171",
        31_579_122_687,
    ),
    "v1.0-trainval02_blobs.tgz": (
        "292301394af9d4a8eb62cee41b3b3031c6cad78e2b39bf63a91bd6d3b7592373",
        30_134_721_083,
    ),
    "v1.0-trainval03_blobs.tgz": (
        "9e6e7c949fbea971321112757dfcff757add646078393c191981a0a49d5f483c",
        29_872_679_856,
    ),
    "v1.0-trainval04_blobs.tgz": (
        "6927f765f8555ce6f901ed2763569bd860b33ad5e076709bbc6c4cc8a51ffc76",
        32_075_538_096,
    ),
    "v1.0-trainval05_blobs.tgz": (
        "ea8d886bc79be30d02e9552d229aaa0843ecffccaaff6606644540b4183f605f",
        28_191_611_840,
    ),
    "v1.0-trainval06_blobs.tgz": (
        "26e3dfff85d8ef6354d4b9dc0a9d8b3f0ebd8719b6d84eac5841fa31b97b8deb",
        27_516_468_993,
    ),
    "v1.0-trainval07_blobs.tgz": (
        "70287e2d65386bce2d67001ef56f5c0abdd3dd95d1ec404c3e00a39208fa60b7",
        29_534_216_608,
    ),
    "v1.0-trainval08_blobs.tgz": (
        "744080381fcfbca3e3ee8d20c5340dce4b5b7fae8020a7e90338ec98b20802c1",
        30_275_496_199,
    ),
    "v1.0-trainval09_blobs.tgz": (
        "ca3aba09dc63cd22fdc455959f3aea99e0f6ed4de822c8c3f5f96f0efa372ec5",
        33_517_622_306,
    ),
    "v1.0-trainval10_blobs.tgz": (
        "046aa7c5ff2cab63a25eaa6210e00bd8197f835e5324457d305a2a16a262f57a",
        41_727_447_974,
    ),
}
DATASET_METADATA_FILES = {
    "attribute.json",
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "instance.json",
    "log.json",
    "map.json",
    "sample.json",
    "sample_annotation.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
    "visibility.json",
}
DATASET_MAP_ANCHORS = {
    "36092f0b03a857c6a3403e25b4b7aab3.png",
    "37819e65e09e5547b8a3ceaefba56bb2.png",
    "53992ee3023e5494b90c316c183be829.png",
    "93406b464a165eaba6d9de76ca09f5da.png",
}
ERROR_RE = re.compile(
    rb"(?:Traceback \(most recent call last\)|RuntimeError|CUDA error|"
    rb"I135_SMOKE_(?:ABORT|FAIL)|SENTINEL_[A-Z0-9_]*ERROR)",
    re.IGNORECASE,
)
ENVIRONMENT_FIELDS = {
    "schema",
    "verdict",
    "captured_at_utc",
    "capture_started_at_utc",
    "host",
    "problem_count",
    "problems",
    "gpu",
    "box",
    "storage",
    "storage_devices",
    "dataset",
    "repositories",
    "remote_files",
    "container_images",
}
MANIFEST_FIELDS = {
    "schema",
    "verdict",
    "launch_authorized",
    "mission_phase",
    "mission_state",
    "git_provenance",
    "design",
    "planned_blocks",
    "planned_episodes",
    "pair_order",
    "execution_blocks",
    "execution_cells",
    "hash_bound_files",
    "source_artifacts",
    "remote_artifacts",
    "dataset_receipt",
    "environment_receipts",
    "container_images",
    "storage_gate",
    "resource_gate",
    "smoke_receipt",
    "tooling_verification_receipt",
    "gates",
    "missing_artifacts",
    "problem_count",
    "problems",
}
PRE_SMOKE_GATES = {
    "g0_preregistration": True,
    "g1_provenance": True,
    "g2_released_behavior": True,
    "g3_schedule_integrity": True,
    "g4_semantic_leak": True,
    "g5_live_smoke": False,
    "g7_dataset_provenance": True,
    "g8_storage_environment": True,
    "g9_resource_plan": False,
    "execution_plan": True,
    "execution_consumers": True,
    "tooling_verification": True,
    "mission_state": False,
}
EXPECTED_BOX = {
    "idle": True,
    "all_containers": 0,
    "gpu_compute_processes": 0,
    "known_evaluation_processes": 0,
}
CONTAINER_ROLES = {"renderer", "model", "ncap"}
SESSION_START_FIELDS = {
    "event",
    "schema",
    "nonanalytic",
    "analytic_episode_count",
    "analytic_output_root",
    "smoke_output_root",
    "smoke_episode_root",
    "manifest_sha256",
    "canonical_runner_sha256",
    "canonical_runner_identity",
    "persistent_smoke_lock",
    "persistent_smoke_lock_identity",
    "retry_policy",
    "docker_wrapper_sha256",
    "docker_binary_sha256",
    "docker_binary_identity",
    "container_control_root_identity",
    "environment_receipt_sha256",
    "schedule_sha256",
    "blind_patch_sha256",
    "runner_sha256",
    "validator_sha256",
    "compose_sha256",
    "container_image_ids",
    "gpu_identity",
}
DOSE_START_FIELDS = {
    "event",
    "ordinal",
    "dose",
    "schedule_id",
    "scenario_class",
    "sequence",
    "run",
    "runs",
    "nonanalytic",
    "analytic_inclusion",
    "analytic_episode_count",
    "output_root",
    "model_log_path",
    "clock",
    "start_ns",
    "argv",
}
DOSE_FINISH_FIELDS = {
    "event",
    "ordinal",
    "dose",
    "schedule_id",
    "scenario_class",
    "sequence",
    "run",
    "clock",
    "end_ns",
    "elapsed_ns",
    "compose_exit_code",
    "env_capture_exit_code",
    "container_monitor_exit_code",
    "container_cleanup_exit_code",
    "container_receipts",
    "patched_server_sha256",
}
SESSION_FINISH_FIELDS = {
    "event",
    "status",
    "exit_code",
    "dose_invocation_count",
    "analytic_episode_count",
    "total_gpu_elapsed_ns",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _canonical_json_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_preflight_mission_state(
    state: Mapping[str, Any] | None,
    problems: list[str],
) -> None:
    if not isinstance(state, Mapping):
        problems.append("mission-state:missing-or-not-object")
        return
    if set(state) != MISSION_STATE_FIELDS:
        problems.append("mission-state:field-set")
    if state.get("workspace_boundary") != WORKSPACE_BOUNDARY:
        problems.append("mission-state:workspace-boundary")
    if (
        state.get("schema") != MISSION_STATE_SCHEMA
        or state.get("canonical_repository") != CANONICAL_REPOSITORY
        or state.get("trunk") != "master"
        or state.get("current_completed_iteration") != 134
        or state.get("current_result")
        != "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
        or state.get("current_verdict") != "PLACEBO_HARM_OR_NULL"
        or state.get("run_state") != "IDLE"
        or state.get("active_hypothesis")
        != "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
        or state.get("next_program") != PREFLIGHT_PROGRAM
        or state.get("storage_gate") != MISSION_STORAGE_GATE
    ):
        problems.append("mission-state:authority-contract")


def _validate_dataset_file_receipt(
    receipt: object,
    *,
    label: str,
    expected_path: str,
    problems: list[str],
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> None:
    if not isinstance(receipt, Mapping) or set(receipt) != {"path", "sha256", "bytes"}:
        problems.append(f"environment:dataset:{label}:field-set")
        return
    if receipt.get("path") != expected_path:
        problems.append(f"environment:dataset:{label}:path")
    digest = receipt.get("sha256")
    if not _is_sha256(digest):
        problems.append(f"environment:dataset:{label}:sha256")
    elif expected_sha256 is not None and digest != expected_sha256:
        problems.append(f"environment:dataset:{label}:expected-sha256")
    byte_count = receipt.get("bytes")
    if type(byte_count) is not int or byte_count <= 0:
        problems.append(f"environment:dataset:{label}:bytes")
    elif expected_bytes is not None and byte_count != expected_bytes:
        problems.append(f"environment:dataset:{label}:expected-bytes")


def _validate_dataset_receipt(receipt: object, problems: list[str]) -> Mapping[str, Any]:
    if not isinstance(receipt, Mapping):
        problems.append("environment:dataset:missing")
        return {}
    expected_fields = {
        "schema",
        "contract_sha256",
        "proof_basis",
        "identity",
        "archives",
        "metadata_json",
        "map_anchors",
        "receipt_payload_sha256",
    }
    if set(receipt) != expected_fields:
        problems.append("environment:dataset:field-set")
    if receipt.get("schema") != DATASET_SCHEMA:
        problems.append("environment:dataset:schema")
    if receipt.get("contract_sha256") != DATASET_CONTRACT_SHA256:
        problems.append("environment:dataset:contract-sha256")
    if receipt.get("proof_basis") != DATASET_PROOF_BASIS:
        problems.append("environment:dataset:proof-basis")

    identity = receipt.get("identity")
    expected_identity_fields = {
        "dataset_root",
        "dataset_realpath",
        "dataset_is_symlink",
        "dataset_version",
        "archive_root",
        "archive_realpath",
        "archive_is_symlink",
        "metadata_root",
        "metadata_realpath",
        "metadata_is_symlink",
        "map_root",
        "map_realpath",
        "map_is_symlink",
        "mount_target",
        "mount_source",
        "mount_fstype",
        "mount_uuid",
        "dataset_st_dev",
        "mount_st_dev",
        "root_st_dev",
    }
    if not isinstance(identity, Mapping) or set(identity) != expected_identity_fields:
        problems.append("environment:dataset:identity-field-set")
        identity = {}
    expected_identity = {
        "dataset_root": DATASET_ROOT,
        "dataset_realpath": DATASET_ROOT,
        "dataset_is_symlink": False,
        "dataset_version": DATASET_VERSION,
        "archive_root": DATASET_ARCHIVE_ROOT,
        "archive_realpath": DATASET_ARCHIVE_ROOT,
        "archive_is_symlink": False,
        "metadata_root": DATASET_METADATA_ROOT,
        "metadata_realpath": DATASET_METADATA_ROOT,
        "metadata_is_symlink": False,
        "map_root": DATASET_MAP_ROOT,
        "map_realpath": DATASET_MAP_ROOT,
        "map_is_symlink": False,
        **DATASET_MOUNT,
    }
    for field, expected in expected_identity.items():
        actual = identity.get(field)
        if actual != expected or (isinstance(expected, bool) and type(actual) is not bool):
            problems.append(f"environment:dataset:identity:{field}")
    dataset_device = identity.get("dataset_st_dev")
    mount_device = identity.get("mount_st_dev")
    root_device = identity.get("root_st_dev")
    if (
        type(dataset_device) is not int
        or type(mount_device) is not int
        or type(root_device) is not int
        or min(dataset_device, mount_device, root_device) < 0
        or dataset_device != mount_device
        or dataset_device == root_device
    ):
        problems.append("environment:dataset:device-identity")

    archives = receipt.get("archives")
    if not isinstance(archives, Mapping) or set(archives) != set(DATASET_ARCHIVES):
        problems.append("environment:dataset:archive-set")
        archives = archives if isinstance(archives, Mapping) else {}
    for name, (digest, byte_count) in DATASET_ARCHIVES.items():
        _validate_dataset_file_receipt(
            archives.get(name),
            label=f"archive:{name}",
            expected_path=f"{DATASET_ARCHIVE_ROOT}/{name}",
            expected_sha256=digest,
            expected_bytes=byte_count,
            problems=problems,
        )

    metadata = receipt.get("metadata_json")
    if not isinstance(metadata, Mapping) or set(metadata) != DATASET_METADATA_FILES:
        problems.append("environment:dataset:metadata-set")
        metadata = metadata if isinstance(metadata, Mapping) else {}
    for name in DATASET_METADATA_FILES:
        _validate_dataset_file_receipt(
            metadata.get(name),
            label=f"metadata:{name}",
            expected_path=f"{DATASET_METADATA_ROOT}/{name}",
            problems=problems,
        )

    maps = receipt.get("map_anchors")
    if not isinstance(maps, Mapping) or set(maps) != DATASET_MAP_ANCHORS:
        problems.append("environment:dataset:map-set")
        maps = maps if isinstance(maps, Mapping) else {}
    for name in DATASET_MAP_ANCHORS:
        _validate_dataset_file_receipt(
            maps.get(name),
            label=f"map:{name}",
            expected_path=f"{DATASET_MAP_ROOT}/{name}",
            problems=problems,
        )

    payload = dict(receipt)
    claimed_payload_sha256 = payload.pop("receipt_payload_sha256", None)
    if (
        not _is_sha256(claimed_payload_sha256)
        or claimed_payload_sha256 != _canonical_json_sha256(payload)
    ):
        problems.append("environment:dataset:receipt-payload-sha256")
    return receipt


def _load_json(path: Path, label: str, problems: list[str]) -> dict[str, Any] | None:
    if path.is_symlink() or not path.is_file():
        problems.append(f"{label}:missing-or-nonregular")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        problems.append(f"{label}:invalid-json:{type(error).__name__}")
        return None
    if not isinstance(value, dict):
        problems.append(f"{label}:not-object")
        return None
    return value


def _canonical_targets(
    schedule: Mapping[str, Any] | None, problems: list[str]
) -> dict[str, tuple[str, Mapping[str, Any]]]:
    if not isinstance(schedule, Mapping):
        return {}
    schedules = schedule.get("schedules")
    if not isinstance(schedules, Mapping) or set(schedules) != set(BLIND_DOSES):
        problems.append("schedule:dose-set")
        return {}

    selected: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for dose in BLIND_DOSES:
        rows = schedules.get(dose)
        if not isinstance(rows, Mapping):
            problems.append(f"schedule:{dose}:rows")
            continue
        candidates: list[tuple[str, Mapping[str, Any]]] = []
        for target, row in rows.items():
            if not isinstance(target, str) or not isinstance(row, Mapping):
                continue
            parts = target.split("/")
            frames = row.get("brake_frames")
            if (
                len(parts) == 3
                and parts[2] == "0"
                and isinstance(frames, list)
                and bool(frames)
            ):
                candidates.append((target, row))
        if not candidates:
            problems.append(f"schedule:{dose}:canonical-run-zero-missing")
            continue
        target, row = sorted(candidates, key=lambda item: item[0])[0]
        scenario_class, sequence, run_text = target.split("/")
        frames = row.get("brake_frames")
        if (
            row.get("dose_id") != dose
            or row.get("target_class") != scenario_class
            or row.get("target_seq") != sequence
            or row.get("target_run") != int(run_text)
        ):
            problems.append(f"schedule:{dose}:canonical-identity")
        if (
            not isinstance(frames, list)
            or any(type(frame) is not int or frame < 0 for frame in frames)
            or frames != sorted(set(frames))
        ):
            problems.append(f"schedule:{dose}:brake-frames")
        selected[dose] = (target, row)
    return selected


def _raw_json_value(line: str, key: str) -> tuple[Any, str] | None:
    """Return a decoded JSON value and its exact source token for a top-level key."""

    matches = list(re.finditer(rf'"{re.escape(key)}"\s*:\s*', line))
    if len(matches) != 1:
        return None
    start = matches[0].end()
    try:
        value, length = json.JSONDecoder().raw_decode(line[start:])
    except json.JSONDecodeError:
        return None
    return value, line[start : start + length]


def _finite_trajectory(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for point in value:
        if not isinstance(point, list) or len(point) != 2:
            return False
        for coordinate in point:
            if (
                not isinstance(coordinate, (int, float))
                or isinstance(coordinate, bool)
                or not math.isfinite(float(coordinate))
            ):
                return False
    return True


def _exact_zero_trajectory(value: object, base: object) -> bool:
    if not isinstance(value, list) or not isinstance(base, list) or len(value) != len(base):
        return False
    return all(
        isinstance(point, list)
        and len(point) == 2
        and all(type(coordinate) is float and coordinate == 0.0 for coordinate in point)
        for point in value
    )


def _read_jsonl_with_source(
    path: Path, label: str, problems: list[str]
) -> list[tuple[dict[str, Any], str]]:
    if path.is_symlink() or not path.is_file():
        problems.append(f"{label}:missing-or-nonregular")
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        problems.append(f"{label}:read:{type(error).__name__}")
        return []
    if not text.endswith("\n"):
        problems.append(f"{label}:missing-final-newline")
    rows: list[tuple[dict[str, Any], str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"{label}:line-{lineno}:invalid-json")
            continue
        if not isinstance(row, dict):
            problems.append(f"{label}:line-{lineno}:not-object")
            continue
        rows.append((row, line))
    if not rows:
        problems.append(f"{label}:empty")
    return rows


def _parse_env_capture(path: Path, label: str, problems: list[str]) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        problems.append(f"{label}:missing-or-nonregular")
        return {}
    payload = path.read_bytes()
    if not payload or not payload.endswith(b"\0"):
        problems.append(f"{label}:not-env-zero")
        return {}
    values: dict[str, str] = {}
    for index, raw in enumerate(payload[:-1].split(b"\0")):
        try:
            item = raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{label}:entry-{index}:utf8")
            continue
        key, separator, value = item.partition("=")
        if not separator or not key:
            problems.append(f"{label}:entry-{index}:shape")
            continue
        if key in values:
            problems.append(f"{label}:duplicate:{key}")
            continue
        values[key] = value
    return values


def _event_identity(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("ordinal"),
        row.get("dose"),
        row.get("schedule_id"),
        row.get("scenario_class"),
        row.get("sequence"),
        row.get("run"),
    )


def _validate_decisions(
    path: Path,
    *,
    dose: str,
    target: str,
    expected_frames: list[int],
    problems: list[str],
) -> dict[str, Any]:
    label = f"decisions:{dose}"
    sourced_rows = _read_jsonl_with_source(path, label, problems)
    scenario_class, sequence, _run = target.split("/")
    resets: list[int] = []
    frame_rows: dict[int, tuple[dict[str, Any], str]] = {}
    brake_frames: list[int] = []
    row_order: list[tuple[str, int]] = []
    schedule_missing = 0
    intervene_errors = 0

    reset_keys = {"reset", "run", "class", "pair", "dose"}
    frame_keys = {
        "frame",
        "scheduled",
        "run",
        "class",
        "pair",
        "dose",
        "frame_index",
        "base_trajectory",
        "returned_trajectory",
    }
    brake_keys = {"brake", "run", "class", "pair", "dose", "frame_index"}
    for lineno, (row, source) in enumerate(sourced_rows, 1):
        identity_ok = (
            row.get("class") == scenario_class
            and row.get("pair") == sequence
            and row.get("dose") == dose
            and type(row.get("run")) is int
            and row.get("run") == 0
        )
        if not identity_ok:
            problems.append(f"{label}:line-{lineno}:identity")
        if row.get("schedule_missing") is True:
            schedule_missing += 1
            problems.append(f"{label}:line-{lineno}:schedule-missing")
            continue
        if row.get("intervene_error") is True or row.get("error") is not None:
            intervene_errors += 1
            problems.append(f"{label}:line-{lineno}:intervene-error")
            continue
        if row.get("reset") is True:
            if set(row) != reset_keys:
                problems.append(f"{label}:line-{lineno}:reset-field-set")
            resets.append(row.get("run"))
            row_order.append(("reset", row.get("run")))
        elif row.get("frame") is True:
            if set(row) != frame_keys:
                problems.append(f"{label}:line-{lineno}:frame-field-set")
            frame_index = row.get("frame_index")
            if type(frame_index) is not int or frame_index < 0:
                problems.append(f"{label}:line-{lineno}:frame-index")
                continue
            if frame_index in frame_rows:
                problems.append(f"{label}:frame-{frame_index}:duplicate")
            frame_rows[frame_index] = (row, source)
            row_order.append(("frame", frame_index))
        elif row.get("brake") is True:
            if set(row) != brake_keys:
                problems.append(f"{label}:line-{lineno}:brake-field-set")
            frame_index = row.get("frame_index")
            if type(frame_index) is not int or frame_index < 0:
                problems.append(f"{label}:line-{lineno}:brake-index")
            else:
                brake_frames.append(frame_index)
                row_order.append(("brake", frame_index))
        else:
            problems.append(f"{label}:line-{lineno}:unknown-row")

    if resets != [0]:
        problems.append(f"{label}:reset-sequence:{resets}")
    ordered_indices = sorted(frame_rows)
    if not ordered_indices or ordered_indices != list(range(len(ordered_indices))):
        problems.append(f"{label}:noncontiguous-frames:{ordered_indices}")
    if expected_frames and (not ordered_indices or expected_frames[-1] > ordered_indices[-1]):
        problems.append(f"{label}:scheduled-frame-unobserved")
    expected_row_order: list[tuple[str, int]] = [("reset", 0)]
    expected_frame_set = set(expected_frames)
    for frame_index in ordered_indices:
        expected_row_order.append(("frame", frame_index))
        if frame_index in expected_frame_set:
            expected_row_order.append(("brake", frame_index))
    if row_order != expected_row_order:
        problems.append(f"{label}:row-order")

    observed_scheduled: list[int] = []
    pass_through_exact = True
    zero_actuator_exact = True
    nonscheduled_count = 0
    for frame_index in ordered_indices:
        row, source = frame_rows[frame_index]
        scheduled = row.get("scheduled")
        if type(scheduled) is not bool:
            problems.append(f"{label}:frame-{frame_index}:scheduled-type")
            continue
        should_schedule = frame_index in expected_frame_set
        if scheduled != should_schedule:
            problems.append(f"{label}:frame-{frame_index}:schedule-flag")
        if scheduled:
            observed_scheduled.append(frame_index)
        else:
            nonscheduled_count += 1

        base_token = _raw_json_value(source, "base_trajectory")
        returned_token = _raw_json_value(source, "returned_trajectory")
        if base_token is None or returned_token is None:
            problems.append(f"{label}:frame-{frame_index}:trajectory-source")
            pass_through_exact = False
            zero_actuator_exact = False
            continue
        base_value, base_source = base_token
        returned_value, returned_source = returned_token
        if not _finite_trajectory(base_value):
            problems.append(f"{label}:frame-{frame_index}:base-trajectory")
        if should_schedule:
            if not _exact_zero_trajectory(returned_value, base_value):
                zero_actuator_exact = False
                problems.append(f"{label}:frame-{frame_index}:not-exact-zero")
        elif returned_value != base_value or returned_source != base_source:
            pass_through_exact = False
            problems.append(f"{label}:frame-{frame_index}:pass-through-drift")

    if nonscheduled_count == 0:
        pass_through_exact = False
        problems.append(f"{label}:no-nonscheduled-frame")
    if observed_scheduled != expected_frames:
        problems.append(f"{label}:scheduled-set")
    if brake_frames != expected_frames:
        problems.append(f"{label}:brake-row-set")

    return {
        "expected_brake_frames": expected_frames,
        "observed_brake_frames": observed_scheduled,
        "pass_through_exact": pass_through_exact,
        "zero_actuator_exact": zero_actuator_exact,
        "identity_fields": ["class", "pair", "run", "frame", "dose"],
        "schedule_missing": schedule_missing,
        "intervene_errors": intervene_errors,
        "frame_count": len(frame_rows),
    }


def _artifact_receipts(experiment_dir: Path, raw_dir: Path) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    if raw_dir.is_symlink() or not raw_dir.is_dir():
        return receipts
    for path in sorted(raw_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and not path.is_symlink():
            try:
                relative = path.resolve().relative_to(experiment_dir.resolve())
            except ValueError:
                continue
            receipts.append({"path": str(relative), "sha256": sha256_file(path)})
    return receipts


def recompute_smoke_receipt(
    experiment_dir: Path = HERE,
    raw_dir: Path | None = None,
) -> dict[str, Any]:
    """Return a deterministic G5 receipt derived only from raw evidence and frozen inputs."""

    experiment_dir = Path(experiment_dir).resolve()
    raw_dir = Path(raw_dir).absolute() if raw_dir is not None else experiment_dir / RAW_REL
    problems: list[str] = []

    if raw_dir.is_symlink() or not raw_dir.is_dir():
        problems.append("raw:missing-or-nondirectory")

    expected_names = {
        "execution.jsonl",
        "pre_smoke_manifest.json",
        "environment_receipt.json",
        *{f"{dose}.decisions.jsonl" for dose in BLIND_DOSES},
        *{f"{dose}.model-env.bin" for dose in BLIND_DOSES},
        *{f"{dose}.compose.log" for dose in BLIND_DOSES},
    }
    if raw_dir.is_dir() and not raw_dir.is_symlink():
        actual_names = {path.name for path in raw_dir.iterdir()}
        if actual_names != expected_names:
            problems.append(
                "raw:file-set:missing="
                + ",".join(sorted(expected_names - actual_names))
                + ":extra="
                + ",".join(sorted(actual_names - expected_names))
            )
        for path in raw_dir.iterdir():
            if path.is_symlink() or not path.is_file():
                problems.append(f"raw:nonregular:{path.name}")

    schedule_path = experiment_dir / "dose_schedules.json"
    patch_path = experiment_dir / "server_patch_blind_dose.py"
    runner_path = experiment_dir / "run_smoke135.sh"
    validator_path = experiment_dir / "validate_smoke135.py"
    canonical_env_path = experiment_dir / "env_receipts.json"
    mission_state_path = experiment_dir / "MISSION_STATE.json"
    schedule = _load_json(schedule_path, "schedule", problems)
    if isinstance(schedule, Mapping):
        if schedule.get("schema") != "iter135.nested_dose_schedules.v1":
            problems.append("schedule:schema")
        if schedule.get("verdict") != "NESTED_DOSE_SCHEDULES_OK":
            problems.append("schedule:verdict")
        if schedule.get("problem_count") != 0 or schedule.get("problems") != []:
            problems.append("schedule:problem-metadata")
    canonical_targets = _canonical_targets(schedule, problems)

    raw_environment = _load_json(raw_dir / "environment_receipt.json", "environment", problems)
    pre_manifest = _load_json(raw_dir / "pre_smoke_manifest.json", "pre-manifest", problems)
    if mission_state_path.is_symlink() or not mission_state_path.is_file():
        mission_state = None
    else:
        mission_state = _load_json(mission_state_path, "mission-state", problems)
    _validate_preflight_mission_state(mission_state, problems)
    if canonical_env_path.is_file() and raw_environment is not None:
        if sha256_file(canonical_env_path) != sha256_file(raw_dir / "environment_receipt.json"):
            problems.append("environment:canonical-hash-drift")
    else:
        problems.append("environment:canonical-missing")

    environment_sha256 = (
        sha256_file(raw_dir / "environment_receipt.json")
        if (raw_dir / "environment_receipt.json").is_file()
        else None
    )
    raw_dataset: Mapping[str, Any] = {}
    if isinstance(raw_environment, Mapping):
        if set(raw_environment) != ENVIRONMENT_FIELDS:
            problems.append("environment:field-set")
        if raw_environment.get("schema") != ENV_SCHEMA:
            problems.append("environment:schema")
        if raw_environment.get("verdict") != ENV_VERDICT:
            problems.append("environment:verdict")
        if raw_environment.get("problem_count") != 0 or raw_environment.get("problems") != []:
            problems.append("environment:problem-metadata")
        if raw_environment.get("host") != "sentinel-gpu":
            problems.append("environment:host")
        if raw_environment.get("box") != EXPECTED_BOX:
            problems.append("environment:box-idle")
        raw_dataset = _validate_dataset_receipt(raw_environment.get("dataset"), problems)

        storage_devices = raw_environment.get("storage_devices")
        dataset_identity = raw_dataset.get("identity")
        if (
            not isinstance(storage_devices, Mapping)
            or set(storage_devices) != {"filesystem_st_dev", "mount_st_dev", "root_st_dev"}
            or not isinstance(dataset_identity, Mapping)
            or dataset_identity.get("dataset_st_dev")
            != storage_devices.get("filesystem_st_dev")
            or dataset_identity.get("mount_st_dev") != storage_devices.get("mount_st_dev")
            or dataset_identity.get("root_st_dev") != storage_devices.get("root_st_dev")
        ):
            problems.append("environment:dataset:storage-device-link")

    local_hashes: dict[str, str | None] = {}
    for name, path in (
        ("dose_schedules.json", schedule_path),
        ("server_patch_blind_dose.py", patch_path),
        ("run_smoke135.sh", runner_path),
        ("validate_smoke135.py", validator_path),
        ("env_receipts.json", canonical_env_path),
    ):
        if path.is_symlink() or not path.is_file():
            problems.append(f"tooling:{name}:missing-or-nonregular")
            local_hashes[name] = None
        else:
            local_hashes[name] = sha256_file(path)

    manifest_sha256 = (
        sha256_file(raw_dir / "pre_smoke_manifest.json")
        if (raw_dir / "pre_smoke_manifest.json").is_file()
        else None
    )
    if isinstance(pre_manifest, Mapping):
        if set(pre_manifest) != MANIFEST_FIELDS:
            problems.append("pre-manifest:field-set")
        if pre_manifest.get("schema") != MANIFEST_SCHEMA:
            problems.append("pre-manifest:schema")
        if pre_manifest.get("verdict") != PRE_SMOKE_VERDICT:
            problems.append("pre-manifest:verdict")
        if pre_manifest.get("launch_authorized") is not False:
            problems.append("pre-manifest:analytic-launch-state")
        if pre_manifest.get("mission_phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED":
            problems.append("pre-manifest:mission-phase")
        if pre_manifest.get("planned_blocks") != 120 or pre_manifest.get(
            "planned_episodes"
        ) != 2400:
            problems.append("pre-manifest:analytic-plan-cardinality")
        if pre_manifest.get("gates") != PRE_SMOKE_GATES:
            problems.append("pre-manifest:gate-contract")
        if pre_manifest.get("missing_artifacts") != [str(RECEIPT_REL)]:
            problems.append("pre-manifest:missing-artifact-set")
        if pre_manifest.get("problem_count") != 1 or pre_manifest.get("problems") != [
            "smoke:receipt-missing"
        ]:
            problems.append("pre-manifest:problem-set")
        mission_receipt = pre_manifest.get("mission_state")
        if mission_state_path.is_file() and not mission_state_path.is_symlink():
            mission_sha256 = sha256_file(mission_state_path)
            mission_bytes = mission_state_path.stat().st_size
        else:
            mission_sha256 = None
            mission_bytes = None
        if (
            not isinstance(mission_receipt, Mapping)
            or set(mission_receipt) != {"source_path", "sha256", "bytes"}
            or mission_receipt.get("source_path") != "MISSION_STATE.json"
            or mission_receipt.get("sha256") != mission_sha256
            or mission_receipt.get("bytes") != mission_bytes
        ):
            problems.append("pre-manifest:mission-state-receipt")
        bound = pre_manifest.get("hash_bound_files")
        if not isinstance(bound, Mapping):
            problems.append("pre-manifest:hash-bound-files")
        else:
            for name, actual in local_hashes.items():
                row = bound.get(name)
                local_path = experiment_dir / name
                expected_bytes = (
                    local_path.stat().st_size
                    if local_path.is_file() and not local_path.is_symlink()
                    else None
                )
                if (
                    not isinstance(row, Mapping)
                    or set(row) != {"source_path", "sha256", "bytes"}
                    or row.get("source_path") != name
                    or row.get("sha256") != actual
                    or row.get("bytes") != expected_bytes
                ):
                    problems.append(f"pre-manifest:hash:{name}")
            env_row = bound.get("env_receipts.json")
            if not isinstance(env_row, Mapping) or env_row.get("sha256") != environment_sha256:
                problems.append("pre-manifest:environment-hash")

        manifest_environment = pre_manifest.get("environment_receipts")
        expected_manifest_environment = (
            {
                **raw_environment,
                "docker_image_ids": dict(EXPECTED_IMAGE_IDS),
            }
            if isinstance(raw_environment, Mapping)
            else None
        )
        if manifest_environment != expected_manifest_environment:
            problems.append("pre-manifest:environment-link")
        if pre_manifest.get("dataset_receipt") != raw_dataset or not raw_dataset:
            problems.append("pre-manifest:dataset-link")
        if (
            not isinstance(manifest_environment, Mapping)
            or manifest_environment.get("dataset") != raw_dataset
        ):
            problems.append("pre-manifest:environment-dataset-link")
        expected_container_images = (
            raw_environment.get("container_images")
            if isinstance(raw_environment, Mapping)
            else None
        )
        if pre_manifest.get("container_images") != expected_container_images:
            problems.append("pre-manifest:container-images-link")

    execution_rows = _read_jsonl_with_source(
        raw_dir / "execution.jsonl", "execution", problems
    )
    events = [row for row, _source in execution_rows]
    start = events[0] if events else {}
    finish = events[-1] if events else {}
    expected_event_count = 2 * len(BLIND_DOSES) + 2
    if len(events) != expected_event_count:
        problems.append(f"execution:event-count:{len(events)}!={expected_event_count}")
    if set(start) != SESSION_START_FIELDS:
        problems.append("execution:session-start-field-set")
    if start.get("event") != "session_start" or start.get("schema") != RAW_SCHEMA:
        problems.append("execution:session-start")
    if (
        start.get("nonanalytic") is not True
        or type(start.get("analytic_episode_count")) is not int
        or start.get("analytic_episode_count") != 0
    ):
        problems.append("execution:nonanalytic-boundary")
    if (
        start.get("analytic_output_root") != ANALYTIC_OUTPUT_ROOT
        or start.get("smoke_output_root") != SMOKE_OUTPUT_ROOT
        or start.get("smoke_episode_root") != SMOKE_EPISODE_ROOT
        or Path(SMOKE_OUTPUT_ROOT).parent != Path(ANALYTIC_OUTPUT_ROOT).parent
        or Path(SMOKE_OUTPUT_ROOT) == Path(ANALYTIC_OUTPUT_ROOT)
    ):
        problems.append("execution:output-isolation")
    if start.get("manifest_sha256") != manifest_sha256:
        problems.append("execution:manifest-hash")
    if start.get("environment_receipt_sha256") != environment_sha256:
        problems.append("execution:environment-hash")
    for field, name in (
        ("schedule_sha256", "dose_schedules.json"),
        ("blind_patch_sha256", "server_patch_blind_dose.py"),
        ("runner_sha256", "run_smoke135.sh"),
        ("validator_sha256", "validate_smoke135.py"),
    ):
        if start.get(field) != local_hashes.get(name):
            problems.append(f"execution:{field}")
    if (
        start.get("canonical_runner_sha256") != start.get("runner_sha256")
        or start.get("canonical_runner_sha256") != local_hashes.get("run_smoke135.sh")
    ):
        problems.append("execution:canonical-runner-hash")
    if not isinstance(start.get("canonical_runner_identity"), str) or IDENTITY_RE.fullmatch(
        start["canonical_runner_identity"]
    ) is None:
        problems.append("execution:canonical-runner-identity")
    if start.get("persistent_smoke_lock") != "/var/lib/sentinel/i135-smoke.lock":
        problems.append("execution:persistent-lock-path")
    if not isinstance(start.get("persistent_smoke_lock_identity"), str) or IDENTITY_RE.fullmatch(
        start["persistent_smoke_lock_identity"]
    ) is None:
        problems.append("execution:persistent-lock-identity")
    if start.get("retry_policy") != "one_shot_no_retry_lock_retained":
        problems.append("execution:retry-policy")
    if not _is_sha256(start.get("docker_wrapper_sha256")):
        problems.append("execution:docker-wrapper-sha256")
    if not _is_sha256(start.get("docker_binary_sha256")):
        problems.append("execution:docker-binary-sha256")
    for field in ("docker_binary_identity", "container_control_root_identity"):
        value = start.get(field)
        if not isinstance(value, str) or IDENTITY_RE.fullmatch(value) is None:
            problems.append(f"execution:{field.replace('_', '-')}")

    remote_files = (
        raw_environment.get("remote_files") if isinstance(raw_environment, Mapping) else None
    )
    compose = remote_files.get("compose_script") if isinstance(remote_files, Mapping) else None
    remote_compose_sha256 = compose.get("sha256") if isinstance(compose, Mapping) else None
    if not isinstance(compose, Mapping) or compose.get("path") != (
        "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh"
    ):
        problems.append("environment:compose-physical-path")
    if not _is_sha256(remote_compose_sha256) or start.get("compose_sha256") != remote_compose_sha256:
        problems.append("execution:compose-hash")

    environment_images = (
        raw_environment.get("container_images")
        if isinstance(raw_environment, Mapping)
        else None
    )
    if not isinstance(environment_images, Mapping) or set(environment_images) != set(
        EXPECTED_IMAGE_IDS
    ):
        problems.append("environment:container-image-set")
        environment_images = {}
    for name, expected_id in EXPECTED_IMAGE_IDS.items():
        image = environment_images.get(name)
        if (
            not isinstance(image, Mapping)
            or set(image) != {"image_id", "repo_digests"}
            or image.get("image_id") != expected_id
            or not isinstance(image.get("repo_digests"), list)
            or image.get("repo_digests") != sorted(set(image.get("repo_digests", [])))
            or any(
                not isinstance(digest, str)
                or re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", digest) is None
                for digest in image.get("repo_digests", [])
            )
        ):
            problems.append(f"environment:image:{name}")
    if start.get("container_image_ids") != EXPECTED_IMAGE_IDS:
        problems.append("execution:image-identities")
    environment_gpu = raw_environment.get("gpu") if isinstance(raw_environment, Mapping) else None
    if not isinstance(environment_gpu, Mapping) or set(environment_gpu) != GPU_FIELDS:
        problems.append("environment:gpu-identity")
        environment_gpu = {}
    elif dict(environment_gpu) != EXPECTED_GPU:
        problems.append("environment:gpu-identity-values")
    if start.get("gpu_identity") != dict(environment_gpu):
        problems.append("execution:gpu-identity")

    dose_results: dict[str, dict[str, Any]] = {}
    container_receipts_by_dose: dict[str, dict[str, str]] = {}
    observed_container_ids: set[str] = set()
    durations_ns: list[int] = []
    all_forwarded = {name: True for name in REQUIRED_MODEL_ENV}
    pair_present_on_every_frame = True
    for ordinal, dose in enumerate(BLIND_DOSES):
        target_row = canonical_targets.get(dose)
        if target_row is None:
            continue
        target, schedule_row = target_row
        scenario_class, sequence, _run = target.split("/")
        schedule_id = f"{dose}/{target}"
        expected_frames = schedule_row.get("brake_frames")
        if not isinstance(expected_frames, list):
            expected_frames = []

        start_index = 1 + ordinal * 2
        dose_start = events[start_index] if start_index < len(events) else {}
        dose_finish = events[start_index + 1] if start_index + 1 < len(events) else {}
        identity = (ordinal, dose, schedule_id, scenario_class, sequence, 0)
        if set(dose_start) != DOSE_START_FIELDS:
            problems.append(f"execution:{dose}:start-field-set")
        if set(dose_finish) != DOSE_FINISH_FIELDS:
            problems.append(f"execution:{dose}:finish-field-set")
        if (
            dose_start.get("event") != "dose_start"
            or type(dose_start.get("ordinal")) is not int
            or type(dose_start.get("run")) is not int
            or _event_identity(dose_start) != identity
        ):
            problems.append(f"execution:{dose}:start-identity")
        if (
            dose_finish.get("event") != "dose_finish"
            or type(dose_finish.get("ordinal")) is not int
            or type(dose_finish.get("run")) is not int
            or _event_identity(dose_finish) != identity
        ):
            problems.append(f"execution:{dose}:finish-identity")
        expected_argv = [
            "bash",
            "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
            sequence,
            scenario_class,
            f"--scenario-category={scenario_class}",
            "--runs",
            "1",
        ]
        if (
            type(dose_start.get("runs")) is not int
            or dose_start.get("runs") != 1
            or dose_start.get("nonanalytic") is not True
            or dose_start.get("analytic_inclusion") is not False
            or type(dose_start.get("analytic_episode_count")) is not int
            or dose_start.get("analytic_episode_count") != 0
            or dose_start.get("output_root") != SMOKE_EPISODE_ROOT
            or dose_start.get("argv") != expected_argv
            or dose_start.get("model_log_path") != f"{MODEL_LOG_ROOT}/{dose}.decisions.jsonl"
            or dose_start.get("clock") != "monotonic_ns"
        ):
            problems.append(f"execution:{dose}:invocation-contract")
        start_ns = dose_start.get("start_ns")
        end_ns = dose_finish.get("end_ns")
        elapsed_ns = dose_finish.get("elapsed_ns")
        if (
            type(start_ns) is not int
            or type(end_ns) is not int
            or type(elapsed_ns) is not int
            or start_ns < 0
            or end_ns <= start_ns
            or elapsed_ns != end_ns - start_ns
        ):
            problems.append(f"execution:{dose}:gpu-duration")
        else:
            durations_ns.append(elapsed_ns)
        if (
            type(dose_finish.get("compose_exit_code")) is not int
            or dose_finish.get("compose_exit_code") != 0
        ):
            problems.append(f"execution:{dose}:compose-exit")
        if (
            type(dose_finish.get("env_capture_exit_code")) is not int
            or dose_finish.get("env_capture_exit_code") != 0
        ):
            problems.append(f"execution:{dose}:env-capture-exit")
        if (
            type(dose_finish.get("container_monitor_exit_code")) is not int
            or dose_finish.get("container_monitor_exit_code") != 0
        ):
            problems.append(f"execution:{dose}:container-monitor-exit")
        if (
            type(dose_finish.get("container_cleanup_exit_code")) is not int
            or dose_finish.get("container_cleanup_exit_code") != 0
        ):
            problems.append(f"execution:{dose}:container-cleanup-exit")
        container_receipts = dose_finish.get("container_receipts")
        if not isinstance(container_receipts, Mapping) or set(container_receipts) != CONTAINER_ROLES:
            problems.append(f"execution:{dose}:container-receipt-set")
            container_receipts = (
                container_receipts if isinstance(container_receipts, Mapping) else {}
            )
        normalized_receipts: dict[str, str] = {}
        valid_ids: list[str] = []
        for role in sorted(CONTAINER_ROLES):
            container_id = container_receipts.get(role)
            if not isinstance(container_id, str) or SHA256_RE.fullmatch(container_id) is None:
                problems.append(f"execution:{dose}:container-receipt:{role}")
                continue
            normalized_receipts[role] = container_id
            valid_ids.append(container_id)
        if len(valid_ids) != len(set(valid_ids)):
            problems.append(f"execution:{dose}:container-receipt-duplicates")
        reused_ids = observed_container_ids.intersection(valid_ids)
        if reused_ids:
            problems.append(f"execution:{dose}:container-receipt-reuse")
        observed_container_ids.update(valid_ids)
        container_receipts_by_dose[dose] = normalized_receipts
        if dose_finish.get("clock") != "monotonic_ns":
            problems.append(f"execution:{dose}:clock")
        if dose_finish.get("patched_server_sha256") != EXPECTED_BLIND_PATCHED_SERVER_SHA256:
            problems.append(f"execution:{dose}:patched-server-hash")

        env_values = _parse_env_capture(
            raw_dir / f"{dose}.model-env.bin", f"environment:{dose}", problems
        )
        expected_env = {
            "SENTINEL_ENABLED": "1",
            "SENTINEL_DOSE_PAIR": f"{scenario_class}/{sequence}",
            "SENTINEL_DOSE_ID": dose,
            "SENTINEL_DOSE_SCHEDULE": "/model/dose_schedules.json",
            "SENTINEL_LOG": f"{MODEL_LOG_ROOT}/{dose}.decisions.jsonl",
            "SENTINEL_RELEASE_K": "4",
        }
        forwarding = {name: env_values.get(name) == value for name, value in expected_env.items()}
        for name, forwarded in forwarding.items():
            all_forwarded[name] = all_forwarded[name] and forwarded
            if not forwarded:
                problems.append(f"environment:{dose}:{name}")

        compose_log = raw_dir / f"{dose}.compose.log"
        if compose_log.is_symlink() or not compose_log.is_file() or compose_log.stat().st_size == 0:
            problems.append(f"compose-log:{dose}:missing-or-empty")
        elif ERROR_RE.search(compose_log.read_bytes()):
            problems.append(f"compose-log:{dose}:runtime-error")

        decision_result = _validate_decisions(
            raw_dir / f"{dose}.decisions.jsonl",
            dose=dose,
            target=target,
            expected_frames=expected_frames,
            problems=problems,
        )
        decision_result["schedule_id"] = schedule_id
        dose_results[dose] = decision_result
        if decision_result["frame_count"] <= 0:
            pair_present_on_every_frame = False

    if set(finish) != SESSION_FINISH_FIELDS:
        problems.append("execution:session-finish-field-set")
    if finish.get("event") != "session_finish":
        problems.append("execution:session-finish")
    total_ns = sum(durations_ns)
    if (
        finish.get("status") != "complete"
        or type(finish.get("exit_code")) is not int
        or finish.get("exit_code") != 0
        or type(finish.get("dose_invocation_count")) is not int
        or finish.get("dose_invocation_count") != len(BLIND_DOSES)
        or type(finish.get("analytic_episode_count")) is not int
        or finish.get("analytic_episode_count") != 0
        or type(finish.get("total_gpu_elapsed_ns")) is not int
        or finish.get("total_gpu_elapsed_ns") != total_ns
    ):
        problems.append("execution:completion-contract")
    if len(durations_ns) != len(BLIND_DOSES) or total_ns <= 0 or total_ns >= GPU_CEILING_NS:
        problems.append("execution:gpu-budget")
    gpu_seconds = math.ceil(total_ns / 1_000_000_000) if total_ns > 0 else 0

    artifacts = _artifact_receipts(experiment_dir, raw_dir)
    success_artifact_names = {Path(row["path"]).name for row in artifacts}
    if success_artifact_names != expected_names:
        problems.append("raw:artifact-receipt-set")

    unique_problems = sorted(set(problems))
    return {
        "schema": RECEIPT_SCHEMA,
        "verdict": OK_VERDICT if not unique_problems else FAIL_VERDICT,
        "problem_count": len(unique_problems),
        "problems": unique_problems,
        "nonanalytic": True,
        "analytic_episode_count": 0,
        "gpu_seconds": gpu_seconds,
        "gpu_elapsed_ns": total_ns,
        "schedule_sha256": local_hashes.get("dose_schedules.json"),
        "blind_patch_sha256": local_hashes.get("server_patch_blind_dose.py"),
        "remote_compose_sha256": remote_compose_sha256,
        "pre_smoke_manifest_sha256": manifest_sha256,
        "environment_receipt_sha256": environment_sha256,
        "dataset_contract_sha256": raw_dataset.get("contract_sha256"),
        "dataset_receipt_payload_sha256": raw_dataset.get("receipt_payload_sha256"),
        "runner_sha256": local_hashes.get("run_smoke135.sh"),
        "validator_sha256": local_hashes.get("validate_smoke135.py"),
        "canonical_runner_sha256": start.get("canonical_runner_sha256"),
        "canonical_runner_identity": start.get("canonical_runner_identity"),
        "persistent_smoke_lock": start.get("persistent_smoke_lock"),
        "persistent_smoke_lock_identity": start.get("persistent_smoke_lock_identity"),
        "retry_policy": start.get("retry_policy"),
        "docker_wrapper_sha256": start.get("docker_wrapper_sha256"),
        "docker_binary_sha256": start.get("docker_binary_sha256"),
        "docker_binary_identity": start.get("docker_binary_identity"),
        "container_control_root_identity": start.get("container_control_root_identity"),
        "container_receipts": container_receipts_by_dose,
        "gpu_identity": dict(environment_gpu),
        "model_environment_forwarded": all_forwarded,
        "pair_present_on_every_frame": pair_present_on_every_frame and not any(
            problem.endswith(":identity") for problem in unique_problems
        ),
        "dose_results": dose_results,
        "artifacts": artifacts,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=HERE)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    output = args.output or args.experiment_dir / RECEIPT_REL
    receipt = recompute_smoke_receipt(args.experiment_dir, args.raw_dir)
    _write_json(output, receipt)
    print(
        f"{receipt['verdict']} problems={receipt['problem_count']} "
        f"gpu_seconds={receipt['gpu_seconds']} output={output}",
        file=sys.stderr,
    )
    return 0 if receipt["verdict"] == OK_VERDICT else 2


if __name__ == "__main__":
    raise SystemExit(main())
