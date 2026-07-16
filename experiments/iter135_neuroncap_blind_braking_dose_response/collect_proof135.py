#!/usr/bin/env python3
"""Collect and commit-verify the frozen Iteration-135 raw proof.

Collection is intentionally a one-way raw boundary.  It validates the launcher log, decision
streams, run artifacts, dataset/Docker runtime snapshots, and retained analytic lock before
creating deterministic proof artifacts.  It never imports or executes the analyzer.  The default
CLI has no free-space override; tests inject providers through :func:`collect_proof`.

After the raw proof is committed, ``--verify-committed`` emits a transient, fail-closed receipt
that binds every analyzer input to the exact clean Git ``HEAD``.  Write that receipt outside the
repository (or to stdout); it is evidence about the prior proof commit, not part of that commit.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, BinaryIO


SCHEMA = "iter135.raw_proof_receipt.v1"
VALIDITY_SCHEMA = "iter135.analyzer_validity_receipt.v2"
COMMITTED_SCHEMA = "iter135.committed_proof_receipt.v1"
MANIFEST_SCHEMA = "iter135.launch_manifest.v2"
ENVIRONMENT_SCHEMA = "iter135.environment_receipts.v3"
DATASET_SCHEMA = "iter135.nuscenes_dataset_receipt.v1"
DATASET_RUNTIME_SCHEMA = "iter135.dataset_runtime_snapshot.v1"
DOCKER_RUNTIME_SCHEMA = "iter135.docker_runtime_snapshot.v1"
ANALYTIC_LOCK_SCHEMA = "iter135.analytic_lock.v3"
DONE_MARKER = "I135_DOSE_DONE"
MINIMUM_LOCAL_FREE_BYTES = 15 * 1024**3
TOTAL_GPU_CEILING_SECONDS = 110 * 60 * 60
EXPECTED_OUTPUT_ROOT = "/datasets/nuscenes-full/sentinel-i135-outoutput"
EXPECTED_OUTPUT_DEVICE = "/dev/nvme0n2"
EXPECTED_OUTPUT_UUID = "9a98277e-b21f-4ffc-8f14-3f2235b43103"
EXPECTED_LAUNCH_LOCK = "/var/lib/sentinel/i135-analytic.lock"
RUNTIME_SNAPSHOT_ROOT = "/var/lib/sentinel"
RUNTIME_EVIDENCE_FILENAMES = {
    "dataset_runtime_snapshot": "dataset_runtime_snapshot.json",
    "docker_runtime_snapshot": "docker_runtime_snapshot.json",
    "analytic_lock": "analytic_lock.json",
}
EXPECTED_DATASET_ROOT = "/datasets/nuscenes-full"
EXPECTED_DATASET_VERSION = "v1.0-trainval"
EXPECTED_DATASET_ARCHIVE_ROOT = f"{EXPECTED_DATASET_ROOT}/archives"
EXPECTED_DATASET_METADATA_ROOT = f"{EXPECTED_DATASET_ROOT}/{EXPECTED_DATASET_VERSION}"
EXPECTED_DATASET_MAP_ROOT = f"{EXPECTED_DATASET_ROOT}/maps"
EXPECTED_DATASET_CONTRACT_SHA256 = (
    "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
)
EXPECTED_DATASET_MOUNT = {
    "mount_target": EXPECTED_DATASET_ROOT,
    "mount_source": EXPECTED_OUTPUT_DEVICE,
    "mount_fstype": "ext4",
    "mount_uuid": EXPECTED_OUTPUT_UUID,
}
EXPECTED_DATASET_PROOF_BASIS = {
    "iteration": 28,
    "result_path": "experiments/iter28_nuscenes_trainval_staging/RESULT.md",
    "receipt_directory": "experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads",
    "archive_count": 11,
    "archive_total_bytes": 314_886_603_672,
}
EXPECTED_DATASET_ARCHIVES = {
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
EXPECTED_DATASET_METADATA_FILES = (
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
)
EXPECTED_DATASET_MAP_ANCHORS = (
    "36092f0b03a857c6a3403e25b4b7aab3.png",
    "37819e65e09e5547b8a3ceaefba56bb2.png",
    "53992ee3023e5494b90c316c183be829.png",
    "93406b464a165eaba6d9de76ca09f5da.png",
)
DOCKER_DAEMON_INFO_FIELDS = (
    "ID",
    "Name",
    "ServerVersion",
    "DockerRootDir",
    "Driver",
    "OperatingSystem",
    "OSType",
    "Architecture",
    "NCPU",
    "MemTotal",
    "KernelVersion",
    "CgroupDriver",
    "CgroupVersion",
)
DOCKER_DAEMON_VERSION_FIELDS = (
    "Platform",
    "Version",
    "ApiVersion",
    "MinAPIVersion",
    "GitCommit",
    "GoVersion",
    "Os",
    "Arch",
    "BuildTime",
    "Experimental",
)
RUNS = tuple(range(20))
CLASSES = ("stationary", "frontal", "side")
PAIRS_BY_CLASS = {
    "stationary": (
        "0099",
        "0101",
        "0103",
        "0106",
        "0108",
        "0278",
        "0331",
        "0783",
        "0796",
        "0966",
    ),
    "frontal": ("0103", "0106", "0110", "0346", "0923"),
    "side": ("0103", "0108", "0110", "0278", "0921"),
}
ARMS = (
    "off_baseline",
    "released_union_semantic_reference",
    "blind_0_5x",
    "blind_1_0x",
    "blind_1_5x",
    "blind_2_0x",
)
BLIND_ARMS = frozenset(ARMS[2:])
ARM_SHORT = {
    "off_baseline": "off",
    "released_union_semantic_reference": "union",
    "blind_0_5x": "blind_0_5x",
    "blind_1_0x": "blind_1_0x",
    "blind_1_5x": "blind_1_5x",
    "blind_2_0x": "blind_2_0x",
}
ARM_RUN_DIR = {arm: f"i135-{short}" for arm, short in ARM_SHORT.items()}
DECISION_FILENAMES = {
    arm: f"sentinel_i135_{short}.jsonl.gz" for arm, short in ARM_SHORT.items()
}
RUN_ARTIFACT_NAMES = ("ego_poses.json", "metrics.json", "actors.json")
REQUIRED_MANIFEST_GATES = {
    "G0": "g0_preregistration",
    "G1": "g1_provenance",
    "G2": "g2_released_behavior",
    "G3": "g3_schedule_integrity",
    "G4": "g4_semantic_leak",
    "G5": "g5_live_smoke",
    "G8": "g8_storage_environment",
    "G9": "g9_resource_plan",
}
EXPECTED_MANIFEST_GATE_NAMES = frozenset(
    {
        *REQUIRED_MANIFEST_GATES.values(),
        "g7_dataset_provenance",
        "execution_plan",
        "execution_consumers",
        "tooling_verification",
        "mission_state",
    }
)

_FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_BLOCK_MARKER = re.compile(r"^##### I135BLOCK (\S+) (\S+) (\S+) #####$")
_SCORE = re.compile(rf"ncap_score:\s*({_FLOAT}),\s*impact_speed:\s*({_FLOAT})")
_BLOCK_START = re.compile(
    r"^I135_BLOCK_START ordinal=(\d+) arm=(\S+) pair=(\S+)/(\S+)$"
)
_BLOCK_OK = re.compile(
    r"^I135_BLOCK_OK ordinal=(\d+) arm=(\S+) pair=(\S+)/(\S+) runs=(\d+)$"
)
_BLOCK_VALID = re.compile(r"^I135_BLOCK_VALIDATION_OK arm=(\S+) pair=(\S+)/(\S+)$")
_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HEX_GIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class ProofCollectionError(RuntimeError):
    """A raw-trust-boundary violation; collection must publish nothing."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256_bytes(payload)


def _write_bytes(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _strict_json_bytes(payload: bytes, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite constant {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for key, value in pairs:
            if key in row:
                raise ValueError(f"duplicate key {key!r}")
            row[key] = value
        return row

    try:
        return json.loads(
            payload,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ProofCollectionError(f"malformed-json:{label}:{error}") from error


def canonical_pairs() -> list[tuple[str, str]]:
    return [(scenario_class, pair) for scenario_class in CLASSES for pair in PAIRS_BY_CLASS[scenario_class]]


def expected_blocks() -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    ordinal = 0
    for pair_index, (scenario_class, sequence) in enumerate(canonical_pairs()):
        rotation = pair_index % len(ARMS)
        rotated = ARMS[rotation:] + ARMS[:rotation]
        for temporal_position, arm in enumerate(rotated):
            blocks.append(
                {
                    "ordinal": ordinal,
                    "pair_index": pair_index,
                    "temporal_position": temporal_position,
                    "arm_id": arm,
                    "scenario_class": scenario_class,
                    "sequence": sequence,
                    "run_indices": list(RUNS),
                }
            )
            ordinal += 1
    return blocks


def expected_cells() -> list[tuple[str, str, str, int]]:
    return [
        (block["arm_id"], block["scenario_class"], block["sequence"], run)
        for block in expected_blocks()
        for run in RUNS
    ]


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ProofCollectionError(f"required-regular-file:{label}:{path}")


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProofCollectionError(f"number-required:{label}:{value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ProofCollectionError(f"finite-number-required:{label}:{value!r}")
    return result


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ProofCollectionError(f"integer-required:{label}:{value!r}")
    return value


def _key_value_tokens(line: str, prefix: str, *, exact_fields: set[str]) -> dict[str, str]:
    if not line.startswith(prefix):
        raise ProofCollectionError(f"launcher-log:marker-prefix:{prefix.rstrip()}")
    row: dict[str, str] = {}
    for token in line.removeprefix(prefix).split():
        key, separator, value = token.partition("=")
        if not separator or not key or not value or key in row:
            raise ProofCollectionError(f"launcher-log:malformed-marker-token:{prefix.rstrip()}:{token}")
        row[key] = value
    if set(row) != exact_fields:
        raise ProofCollectionError(
            f"launcher-log:marker-fields:{prefix.rstrip()}:"
            f"missing={sorted(exact_fields - set(row))}:extra={sorted(set(row) - exact_fields)}"
        )
    return row


def _validate_dataset_file_receipt(
    receipt: Any,
    *,
    label: str,
    expected_path: str,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> None:
    if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256", "bytes"}:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:field-set")
    if receipt.get("path") != expected_path:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:path")
    digest = receipt.get("sha256")
    byte_count = receipt.get("bytes")
    if not isinstance(digest, str) or _HEX_SHA256.fullmatch(digest) is None:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:sha256")
    if type(byte_count) is not int or byte_count <= 0:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:bytes")
    if expected_sha256 is not None and digest != expected_sha256:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:expected-sha256")
    if expected_bytes is not None and byte_count != expected_bytes:
        raise ProofCollectionError(f"launch-manifest:dataset:{label}:expected-bytes")


def validate_manifest_dataset(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Independently bind the v2 manifest's dataset and environment provenance."""

    dataset = manifest.get("dataset_receipt")
    environment = manifest.get("environment_receipts")
    if not isinstance(environment, dict) or environment.get("schema") != ENVIRONMENT_SCHEMA:
        raise ProofCollectionError("launch-manifest:environment-receipts-v3")
    if not isinstance(dataset, dict) or environment.get("dataset") != dataset:
        raise ProofCollectionError("launch-manifest:dataset-environment-mismatch")
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
    if set(dataset) != expected_fields:
        raise ProofCollectionError("launch-manifest:dataset:field-set")
    if dataset.get("schema") != DATASET_SCHEMA:
        raise ProofCollectionError("launch-manifest:dataset:schema")
    if dataset.get("contract_sha256") != EXPECTED_DATASET_CONTRACT_SHA256:
        raise ProofCollectionError("launch-manifest:dataset:contract-sha256")
    if dataset.get("proof_basis") != EXPECTED_DATASET_PROOF_BASIS:
        raise ProofCollectionError("launch-manifest:dataset:proof-basis")

    identity = dataset.get("identity")
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
    if not isinstance(identity, dict) or set(identity) != expected_identity_fields:
        raise ProofCollectionError("launch-manifest:dataset:identity-field-set")
    expected_identity = {
        "dataset_root": EXPECTED_DATASET_ROOT,
        "dataset_realpath": EXPECTED_DATASET_ROOT,
        "dataset_is_symlink": False,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "archive_root": EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_realpath": EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_is_symlink": False,
        "metadata_root": EXPECTED_DATASET_METADATA_ROOT,
        "metadata_realpath": EXPECTED_DATASET_METADATA_ROOT,
        "metadata_is_symlink": False,
        "map_root": EXPECTED_DATASET_MAP_ROOT,
        "map_realpath": EXPECTED_DATASET_MAP_ROOT,
        "map_is_symlink": False,
        **EXPECTED_DATASET_MOUNT,
    }
    for field, expected in expected_identity.items():
        actual = identity.get(field)
        if actual != expected or (isinstance(expected, bool) and type(actual) is not bool):
            raise ProofCollectionError(f"launch-manifest:dataset:identity:{field}")
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
        raise ProofCollectionError("launch-manifest:dataset:device-identity")

    archives = dataset.get("archives")
    if not isinstance(archives, dict) or set(archives) != set(EXPECTED_DATASET_ARCHIVES):
        raise ProofCollectionError("launch-manifest:dataset:archive-set")
    for name, (digest, byte_count) in EXPECTED_DATASET_ARCHIVES.items():
        _validate_dataset_file_receipt(
            archives.get(name),
            label=f"archive:{name}",
            expected_path=f"{EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
            expected_sha256=digest,
            expected_bytes=byte_count,
        )

    metadata = dataset.get("metadata_json")
    if not isinstance(metadata, dict) or set(metadata) != set(EXPECTED_DATASET_METADATA_FILES):
        raise ProofCollectionError("launch-manifest:dataset:metadata-set")
    for name in EXPECTED_DATASET_METADATA_FILES:
        _validate_dataset_file_receipt(
            metadata.get(name),
            label=f"metadata:{name}",
            expected_path=f"{EXPECTED_DATASET_METADATA_ROOT}/{name}",
        )

    maps = dataset.get("map_anchors")
    if not isinstance(maps, dict) or set(maps) != set(EXPECTED_DATASET_MAP_ANCHORS):
        raise ProofCollectionError("launch-manifest:dataset:map-set")
    for name in EXPECTED_DATASET_MAP_ANCHORS:
        _validate_dataset_file_receipt(
            maps.get(name),
            label=f"map:{name}",
            expected_path=f"{EXPECTED_DATASET_MAP_ROOT}/{name}",
        )

    receipt_payload_sha256 = dataset.get("receipt_payload_sha256")
    digest_payload = dict(dataset)
    digest_payload.pop("receipt_payload_sha256", None)
    if (
        not isinstance(receipt_payload_sha256, str)
        or _HEX_SHA256.fullmatch(receipt_payload_sha256) is None
        or receipt_payload_sha256 != _canonical_json_sha256(digest_payload)
    ):
        raise ProofCollectionError("launch-manifest:dataset:receipt-payload-sha256")

    bound_files = manifest.get("hash_bound_files")
    environment_binding = (
        bound_files.get("env_receipts.json") if isinstance(bound_files, dict) else None
    )
    if (
        not isinstance(environment_binding, dict)
        or set(environment_binding) != {"source_path", "sha256", "bytes"}
        or environment_binding.get("source_path") != "env_receipts.json"
        or not isinstance(environment_binding.get("sha256"), str)
        or _HEX_SHA256.fullmatch(environment_binding["sha256"]) is None
        or type(environment_binding.get("bytes")) is not int
        or environment_binding["bytes"] <= 0
    ):
        raise ProofCollectionError("launch-manifest:environment-receipt-binding")
    return {
        "environment_schema": ENVIRONMENT_SCHEMA,
        "environment_receipt_sha256": environment_binding["sha256"],
        "dataset_schema": DATASET_SCHEMA,
        "dataset_contract_sha256": EXPECTED_DATASET_CONTRACT_SHA256,
        "dataset_receipt_payload_sha256": receipt_payload_sha256,
        "dataset_file_count": (
            len(EXPECTED_DATASET_ARCHIVES)
            + len(EXPECTED_DATASET_METADATA_FILES)
            + len(EXPECTED_DATASET_MAP_ANCHORS)
        ),
    }


def _canonical_runtime_snapshot(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _runtime_integer(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise ProofCollectionError(f"runtime-snapshot:{label}:integer")
    return value


def _validate_dataset_runtime_snapshot(
    payload: bytes,
    *,
    source_id: str,
    manifest: Mapping[str, Any],
    manifest_facts: Mapping[str, Any],
    log_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _strict_json_bytes(payload, "dataset-runtime-snapshot")
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "schema",
        "manifest_sha256",
        "dataset_receipt_payload_sha256",
        "dataset_root",
        "files",
    }:
        raise ProofCollectionError("runtime-snapshot:dataset:field-set")
    if payload != _canonical_runtime_snapshot(snapshot):
        raise ProofCollectionError("runtime-snapshot:dataset:noncanonical-json")
    digest = sha256_bytes(payload)
    if digest != log_receipt.get("dataset_runtime_snapshot_sha256"):
        raise ProofCollectionError("runtime-snapshot:dataset:log-sha256")
    if source_id != log_receipt.get("dataset_runtime_snapshot_id"):
        raise ProofCollectionError("runtime-snapshot:dataset:source-id")
    if snapshot.get("schema") != DATASET_RUNTIME_SCHEMA:
        raise ProofCollectionError("runtime-snapshot:dataset:schema")
    if snapshot.get("manifest_sha256") != manifest_facts["launch_manifest_sha256"]:
        raise ProofCollectionError("runtime-snapshot:dataset:manifest-sha256")
    dataset = manifest["dataset_receipt"]
    if snapshot.get("dataset_receipt_payload_sha256") != dataset["receipt_payload_sha256"]:
        raise ProofCollectionError("runtime-snapshot:dataset:receipt-payload-sha256")

    dataset_root = snapshot.get("dataset_root")
    if not isinstance(dataset_root, dict) or set(dataset_root) != {
        "path",
        "st_dev",
        "st_ino",
        "st_mode",
        "st_mtime_ns",
        "st_ctime_ns",
    }:
        raise ProofCollectionError("runtime-snapshot:dataset:root-field-set")
    if dataset_root.get("path") != EXPECTED_DATASET_ROOT:
        raise ProofCollectionError("runtime-snapshot:dataset:root-path")
    if dataset_root.get("st_dev") != dataset["identity"]["dataset_st_dev"]:
        raise ProofCollectionError("runtime-snapshot:dataset:root-device")
    _runtime_integer(dataset_root.get("st_ino"), "dataset:root-st-ino", positive=True)
    root_mode = _runtime_integer(dataset_root.get("st_mode"), "dataset:root-st-mode", positive=True)
    if root_mode > 0o7777:
        raise ProofCollectionError("runtime-snapshot:dataset:root-st-mode-range")
    _runtime_integer(dataset_root.get("st_mtime_ns"), "dataset:root-st-mtime-ns")
    _runtime_integer(dataset_root.get("st_ctime_ns"), "dataset:root-st-ctime-ns")

    expected_files = {
        **{f"archive:{name}": row for name, row in dataset["archives"].items()},
        **{f"metadata:{name}": row for name, row in dataset["metadata_json"].items()},
        **{f"map:{name}": row for name, row in dataset["map_anchors"].items()},
    }
    files = snapshot.get("files")
    if not isinstance(files, dict) or set(files) != set(expected_files):
        raise ProofCollectionError("runtime-snapshot:dataset:file-set")
    for label, expected in expected_files.items():
        row = files[label]
        if not isinstance(row, dict) or set(row) != {
            "path",
            "sha256",
            "bytes",
            "st_dev",
            "st_ino",
            "st_mode",
            "st_mtime_ns",
            "st_ctime_ns",
        }:
            raise ProofCollectionError(f"runtime-snapshot:dataset:file-fields:{label}")
        for field in ("path", "sha256", "bytes"):
            if row.get(field) != expected[field]:
                raise ProofCollectionError(f"runtime-snapshot:dataset:file-{field}:{label}")
        if row.get("st_dev") != dataset["identity"]["dataset_st_dev"]:
            raise ProofCollectionError(f"runtime-snapshot:dataset:file-device:{label}")
        _runtime_integer(row.get("st_ino"), f"dataset:file-st-ino:{label}", positive=True)
        mode = _runtime_integer(row.get("st_mode"), f"dataset:file-st-mode:{label}", positive=True)
        if mode > 0o7777:
            raise ProofCollectionError(f"runtime-snapshot:dataset:file-st-mode-range:{label}")
        _runtime_integer(row.get("st_mtime_ns"), f"dataset:file-st-mtime-ns:{label}")
        _runtime_integer(row.get("st_ctime_ns"), f"dataset:file-st-ctime-ns:{label}")
    return {
        "source_path": f"{log_receipt['runtime_snapshot']}/dataset_runtime_snapshot.json",
        "schema": DATASET_RUNTIME_SCHEMA,
        "sha256": digest,
        "bytes": len(payload),
        "source_id": source_id,
        "manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "dataset_receipt_payload_sha256": dataset["receipt_payload_sha256"],
        "file_count": len(expected_files),
    }


def _validate_docker_runtime_snapshot(
    payload: bytes,
    *,
    source_id: str,
    manifest_facts: Mapping[str, Any],
    log_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _strict_json_bytes(payload, "docker-runtime-snapshot")
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "schema",
        "manifest_sha256",
        "client",
        "context",
        "endpoint",
        "socket",
        "daemon_info",
        "daemon_version",
    }:
        raise ProofCollectionError("runtime-snapshot:docker:field-set")
    if payload != _canonical_runtime_snapshot(snapshot):
        raise ProofCollectionError("runtime-snapshot:docker:noncanonical-json")
    digest = sha256_bytes(payload)
    if digest != log_receipt.get("docker_runtime_snapshot_sha256"):
        raise ProofCollectionError("runtime-snapshot:docker:log-sha256")
    if source_id != log_receipt.get("docker_runtime_snapshot_id"):
        raise ProofCollectionError("runtime-snapshot:docker:source-id")
    if snapshot.get("schema") != DOCKER_RUNTIME_SCHEMA:
        raise ProofCollectionError("runtime-snapshot:docker:schema")
    if snapshot.get("manifest_sha256") != manifest_facts["launch_manifest_sha256"]:
        raise ProofCollectionError("runtime-snapshot:docker:manifest-sha256")
    if snapshot.get("context") != "default":
        raise ProofCollectionError("runtime-snapshot:docker:context")
    if snapshot.get("endpoint") != "unix:///var/run/docker.sock":
        raise ProofCollectionError("runtime-snapshot:docker:endpoint")

    client = snapshot.get("client")
    if not isinstance(client, dict) or set(client) != {"path", "sha256", "st_dev", "st_ino"}:
        raise ProofCollectionError("runtime-snapshot:docker:client-field-set")
    client_path = client.get("path")
    if not isinstance(client_path, str) or not Path(client_path).is_absolute():
        raise ProofCollectionError("runtime-snapshot:docker:client-path")
    client_sha = client.get("sha256")
    if not isinstance(client_sha, str) or _HEX_SHA256.fullmatch(client_sha) is None:
        raise ProofCollectionError("runtime-snapshot:docker:client-sha256")
    _runtime_integer(client.get("st_dev"), "docker:client-st-dev")
    _runtime_integer(client.get("st_ino"), "docker:client-st-ino", positive=True)

    socket = snapshot.get("socket")
    if not isinstance(socket, dict) or set(socket) != {
        "declared_path",
        "realpath",
        "st_dev",
        "st_ino",
        "st_mode",
        "st_uid",
        "st_gid",
    }:
        raise ProofCollectionError("runtime-snapshot:docker:socket-field-set")
    if socket.get("declared_path") != "/var/run/docker.sock":
        raise ProofCollectionError("runtime-snapshot:docker:socket-declared-path")
    socket_realpath = socket.get("realpath")
    if not isinstance(socket_realpath, str) or not Path(socket_realpath).is_absolute():
        raise ProofCollectionError("runtime-snapshot:docker:socket-realpath")
    for field in ("st_dev", "st_uid", "st_gid"):
        _runtime_integer(socket.get(field), f"docker:socket-{field}")
    _runtime_integer(socket.get("st_ino"), "docker:socket-st-ino", positive=True)
    socket_mode = _runtime_integer(socket.get("st_mode"), "docker:socket-st-mode", positive=True)
    if socket_mode > 0o7777:
        raise ProofCollectionError("runtime-snapshot:docker:socket-st-mode-range")

    daemon_info = snapshot.get("daemon_info")
    if not isinstance(daemon_info, dict) or set(daemon_info) != set(DOCKER_DAEMON_INFO_FIELDS):
        raise ProofCollectionError("runtime-snapshot:docker:daemon-info-field-set")
    for field in DOCKER_DAEMON_INFO_FIELDS:
        value = daemon_info[field]
        if field in {"NCPU", "MemTotal"}:
            _runtime_integer(value, f"docker:daemon-info-{field}", positive=True)
        elif not isinstance(value, str) or not value:
            raise ProofCollectionError(f"runtime-snapshot:docker:daemon-info-{field}")
    if not Path(daemon_info["DockerRootDir"]).is_absolute():
        raise ProofCollectionError("runtime-snapshot:docker:daemon-root")
    if daemon_info["ID"] != log_receipt.get("docker_runtime_daemon_id"):
        raise ProofCollectionError("runtime-snapshot:docker:daemon-id-log-binding")

    daemon_version = snapshot.get("daemon_version")
    if not isinstance(daemon_version, dict) or set(daemon_version) != set(
        DOCKER_DAEMON_VERSION_FIELDS
    ):
        raise ProofCollectionError("runtime-snapshot:docker:daemon-version-field-set")
    platform = daemon_version.get("Platform")
    if not isinstance(platform, dict) or set(platform) != {"Name"} or not platform["Name"]:
        raise ProofCollectionError("runtime-snapshot:docker:daemon-version-platform")
    for field in set(DOCKER_DAEMON_VERSION_FIELDS) - {"Platform", "Experimental"}:
        if not isinstance(daemon_version[field], str) or not daemon_version[field]:
            raise ProofCollectionError(f"runtime-snapshot:docker:daemon-version-{field}")
    if type(daemon_version.get("Experimental")) is not bool:
        raise ProofCollectionError("runtime-snapshot:docker:daemon-version-experimental")
    return {
        "source_path": f"{log_receipt['runtime_snapshot']}/docker_runtime_snapshot.json",
        "schema": DOCKER_RUNTIME_SCHEMA,
        "sha256": digest,
        "bytes": len(payload),
        "source_id": source_id,
        "manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "client_path": client_path,
        "client_sha256": client_sha,
        "context": "default",
        "endpoint": "unix:///var/run/docker.sock",
        "daemon_id": daemon_info["ID"],
        "server_version": daemon_info["ServerVersion"],
    }


def _validate_analytic_lock(
    payload: bytes,
    *,
    source_id: str,
    manifest_facts: Mapping[str, Any],
    log_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    lock = _strict_json_bytes(payload, "analytic-lock")
    if not isinstance(lock, dict) or set(lock) != {
        "schema",
        "manifest_sha256",
        "dataset_runtime_snapshot_sha256",
        "docker_runtime_snapshot_sha256",
        "python_wrapper_sha256",
        "python_binary_sha256",
        "python_binary_identity",
        "github_launch_authority",
        "pid",
        "created_at_utc",
    }:
        raise ProofCollectionError("analytic-lock:field-set")
    canonical = (json.dumps(lock, sort_keys=True) + "\n").encode("utf-8")
    if payload != canonical:
        raise ProofCollectionError("analytic-lock:noncanonical-json")
    if source_id != log_receipt.get("launch_lock_id"):
        raise ProofCollectionError("analytic-lock:source-id")
    if lock.get("schema") != ANALYTIC_LOCK_SCHEMA:
        raise ProofCollectionError("analytic-lock:schema")
    expected = {
        "manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "dataset_runtime_snapshot_sha256": log_receipt[
            "dataset_runtime_snapshot_sha256"
        ],
        "docker_runtime_snapshot_sha256": log_receipt["docker_runtime_snapshot_sha256"],
        "python_wrapper_sha256": log_receipt["python_wrapper_sha256"],
        "python_binary_sha256": log_receipt["python_binary_sha256"],
        "python_binary_identity": log_receipt["python_binary_identity"],
        "pid": log_receipt["invocation_pid"],
    }
    for field, value in expected.items():
        if lock.get(field) != value:
            raise ProofCollectionError(f"analytic-lock:{field}")
    created_at = lock.get("created_at_utc")
    if (
        not isinstance(created_at, str)
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", created_at)
        is None
    ):
        raise ProofCollectionError("analytic-lock:created-at-utc")
    authority = lock.get("github_launch_authority")
    authority_fields = {
        "schema",
        "repository",
        "branch",
        "activation_commit",
        "final_manifest_commit",
        "activation_receipt_sha256",
        "manifest_sha256",
        "checks",
        "authority_payload_sha256",
    }
    if not isinstance(authority, dict) or set(authority) != authority_fields:
        raise ProofCollectionError("analytic-lock:github-authority-field-set")
    claimed_authority_sha = authority.get("authority_payload_sha256")
    authority_payload = dict(authority)
    authority_payload.pop("authority_payload_sha256")
    actual_authority_sha = hashlib.sha256(
        json.dumps(
            authority_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    activation_commit = authority.get("activation_commit")
    final_manifest_commit = authority.get("final_manifest_commit")
    checks = authority.get("checks")
    if (
        authority.get("schema") != "iter135.github_launch_authority.v1"
        or authority.get("repository") != "manfromnowhere143/sentinel"
        or authority.get("branch") != "master"
        or not isinstance(activation_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", activation_commit) is None
        or not isinstance(final_manifest_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", final_manifest_commit) is None
        or activation_commit == final_manifest_commit
        or _HEX_SHA256.fullmatch(str(authority.get("activation_receipt_sha256"))) is None
        or authority.get("manifest_sha256") != expected["manifest_sha256"]
        or claimed_authority_sha != actual_authority_sha
        or not isinstance(checks, list)
        or len(checks) != 2
    ):
        raise ProofCollectionError("analytic-lock:github-authority-binding")
    check_ids: list[int] = []
    for row, name in zip(checks, ("check (3.10)", "check (3.11)")):
        if not isinstance(row, dict) or set(row) != {
            "name",
            "id",
            "head_sha",
            "app_slug",
            "status",
            "conclusion",
        }:
            raise ProofCollectionError("analytic-lock:github-check-field-set")
        check_id = row.get("id")
        if (
            row.get("name") != name
            or type(check_id) is not int
            or check_id <= 0
            or row.get("head_sha") != activation_commit
            or row.get("app_slug") != "github-actions"
            or row.get("status") != "completed"
            or row.get("conclusion") != "success"
        ):
            raise ProofCollectionError("analytic-lock:github-check-binding")
        check_ids.append(check_id)
    if len(set(check_ids)) != 2:
        raise ProofCollectionError("analytic-lock:github-check-ids")
    return {
        "source_path": EXPECTED_LAUNCH_LOCK,
        "source_id": source_id,
        "schema": ANALYTIC_LOCK_SCHEMA,
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        **expected,
        "github_launch_authority": authority,
        "created_at_utc": created_at,
    }


def validate_runtime_evidence_payloads(
    payloads: Mapping[str, bytes],
    *,
    source_ids: Mapping[str, str],
    manifest: Mapping[str, Any],
    manifest_facts: Mapping[str, Any],
    log_receipt: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    expected_roles = {
        "dataset_runtime_snapshot",
        "docker_runtime_snapshot",
        "analytic_lock",
    }
    if set(payloads) != expected_roles or set(source_ids) != expected_roles:
        raise ProofCollectionError("runtime-snapshot:payload-role-set")
    return {
        "dataset_runtime_snapshot": _validate_dataset_runtime_snapshot(
            payloads["dataset_runtime_snapshot"],
            source_id=source_ids["dataset_runtime_snapshot"],
            manifest=manifest,
            manifest_facts=manifest_facts,
            log_receipt=log_receipt,
        ),
        "docker_runtime_snapshot": _validate_docker_runtime_snapshot(
            payloads["docker_runtime_snapshot"],
            source_id=source_ids["docker_runtime_snapshot"],
            manifest_facts=manifest_facts,
            log_receipt=log_receipt,
        ),
        "analytic_lock": _validate_analytic_lock(
            payloads["analytic_lock"],
            source_id=source_ids["analytic_lock"],
            manifest_facts=manifest_facts,
            log_receipt=log_receipt,
        ),
    }


def validate_manifest(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the exact launch authorization and return mechanically derived facts."""

    _require_regular_file(path, "launch-manifest")
    payload = path.read_bytes()
    manifest = _strict_json_bytes(payload, str(path))
    if not isinstance(manifest, dict):
        raise ProofCollectionError("launch-manifest:not-object")
    exact = {
        "schema": MANIFEST_SCHEMA,
        "verdict": "I135_TOOLING_MANIFEST_OK",
        "launch_authorized": True,
        "mission_phase": "LAUNCH_AUTHORIZED",
        "planned_blocks": 120,
        "planned_episodes": 2400,
        "problem_count": 0,
        "problems": [],
        "missing_artifacts": [],
    }
    for key, expected in exact.items():
        if manifest.get(key) != expected:
            raise ProofCollectionError(f"launch-manifest:{key}:{manifest.get(key)!r}!={expected!r}")
    design = manifest.get("design")
    if not isinstance(design, dict):
        raise ProofCollectionError("launch-manifest:design-not-object")
    if design.get("retry_policy") != "no_automatic_retry_abort_on_first_block_failure":
        raise ProofCollectionError("launch-manifest:retry-policy")
    if design.get("allowed_retries") != 0:
        raise ProofCollectionError("launch-manifest:allowed-retries")
    if manifest.get("execution_blocks") != expected_blocks():
        raise ProofCollectionError("launch-manifest:execution-block-order-drift")
    cells = manifest.get("execution_cells")
    if not isinstance(cells, list) or len(cells) != 2400:
        raise ProofCollectionError("launch-manifest:execution-cell-count")
    expected_cell_rows = []
    ordinal = 0
    for block in expected_blocks():
        for run in RUNS:
            expected_cell_rows.append(
                {
                    "ordinal": ordinal,
                    "block_ordinal": block["ordinal"],
                    "pair_index": block["pair_index"],
                    "temporal_position": block["temporal_position"],
                    "arm_id": block["arm_id"],
                    "scenario_class": block["scenario_class"],
                    "sequence": block["sequence"],
                    "run_index": run,
                }
            )
            ordinal += 1
    if cells != expected_cell_rows:
        raise ProofCollectionError("launch-manifest:execution-cell-order-drift")

    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        raise ProofCollectionError("launch-manifest:gates-not-object")
    if set(gates) != EXPECTED_MANIFEST_GATE_NAMES:
        raise ProofCollectionError(
            "launch-manifest:gate-set:"
            f"missing={sorted(EXPECTED_MANIFEST_GATE_NAMES - set(gates))}:"
            f"extra={sorted(set(gates) - EXPECTED_MANIFEST_GATE_NAMES)}"
        )
    for gate_name, passed in gates.items():
        if passed is not True:
            raise ProofCollectionError(f"launch-manifest:gate-not-green:{gate_name}:{passed!r}")
    dataset_facts = validate_manifest_dataset(manifest)

    bound_files = manifest.get("hash_bound_files")
    collector_receipt = (
        bound_files.get("collect_proof135.py") if isinstance(bound_files, dict) else None
    )
    current_collector_sha = sha256_file(Path(__file__).resolve())
    if not isinstance(collector_receipt, dict) or collector_receipt.get("sha256") != current_collector_sha:
        raise ProofCollectionError("launch-manifest:collector-sha256-mismatch")

    storage = manifest.get("storage_gate")
    if not isinstance(storage, dict):
        raise ProofCollectionError("launch-manifest:storage-gate-missing")
    remote_free = _number(storage.get("observed_remote_free_gib"), "observed-remote-free-gib")
    projected = _number(storage.get("projected_output_gib"), "projected-output-gib")
    minimum_remote = _number(storage.get("minimum_remote_free_gib"), "minimum-remote-free-gib")
    minimum_reserve = _number(storage.get("minimum_reserve_gib"), "minimum-reserve-gib")
    minimum_remote_bytes = _integer(
        storage.get("minimum_remote_free_bytes"), "minimum-remote-free-bytes"
    )
    projected_output_bytes = _integer(
        storage.get("projected_output_bytes"), "projected-output-bytes"
    )
    minimum_reserve_bytes = _integer(
        storage.get("minimum_reserve_bytes"), "minimum-reserve-bytes"
    )
    if minimum_remote < 100 or minimum_reserve < 25:
        raise ProofCollectionError("launch-manifest:weakened-storage-minimum")
    if minimum_remote_bytes != 100 * 1024**3 or minimum_reserve_bytes != 25 * 1024**3:
        raise ProofCollectionError("launch-manifest:weakened-storage-byte-minimum")
    if projected_output_bytes <= 0:
        raise ProofCollectionError("launch-manifest:invalid-projected-output-bytes")
    projected_reserve = remote_free - projected
    if remote_free < minimum_remote or projected_reserve < minimum_reserve:
        raise ProofCollectionError("launch-manifest:remote-storage-gate-not-green")

    resource = manifest.get("resource_gate")
    if not isinstance(resource, dict):
        raise ProofCollectionError("launch-manifest:resource-gate-missing")
    total = resource.get("total_gpu_ceiling_seconds")
    prior_smoke = resource.get("prior_smoke_gpu_seconds")
    remaining = resource.get("remaining_analytic_seconds")
    if total != TOTAL_GPU_CEILING_SECONDS:
        raise ProofCollectionError(f"launch-manifest:gpu-ceiling:{total}")
    if type(prior_smoke) is not int or not (0 <= prior_smoke < total):
        raise ProofCollectionError(f"launch-manifest:prior-smoke-seconds:{prior_smoke}")
    if remaining != total - prior_smoke or remaining <= 0:
        raise ProofCollectionError(f"launch-manifest:remaining-analytic-seconds:{remaining}")

    manifest_sha256 = sha256_bytes(payload)
    runtime_snapshot = f"{RUNTIME_SNAPSHOT_ROOT}/i135-runtime-{manifest_sha256}"
    return manifest, {
        "launch_manifest_sha256": manifest_sha256,
        "manifest_gates": {gate: gates[name] for gate, name in REQUIRED_MANIFEST_GATES.items()},
        "manifest_dataset_gate": gates["g7_dataset_provenance"],
        "dataset_provenance": {
            **dataset_facts,
            "manifest_gate": "g7_dataset_provenance",
            "passed": True,
            "runtime_snapshot_contract": {
                "schema": DATASET_RUNTIME_SCHEMA,
                "path": f"{runtime_snapshot}/dataset_runtime_snapshot.json",
                "manifest_sha256": manifest_sha256,
                "dataset_receipt_payload_sha256": dataset_facts[
                    "dataset_receipt_payload_sha256"
                ],
                "file_count": dataset_facts["dataset_file_count"],
            },
        },
        "remote_free_gib_at_launch": remote_free,
        "remote_projected_reserve_gib": projected_reserve,
        "minimum_remote_free_bytes": minimum_remote_bytes,
        "projected_output_bytes": projected_output_bytes,
        "minimum_reserve_bytes": minimum_reserve_bytes,
        "prior_smoke_gpu_seconds": prior_smoke,
        "remaining_analytic_seconds": remaining,
        "total_gpu_ceiling_seconds": total,
    }


def validate_run_log_payload(payload: bytes, manifest_facts: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact launcher-log bytes that will cross the raw-proof boundary."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProofCollectionError(f"launcher-log:not-utf8:{error}") from error
    if payload and not payload.endswith(b"\n"):
        raise ProofCollectionError("launcher-log:missing-final-newline")
    lines = text.splitlines()
    expected = expected_blocks()
    expected_identity = [
        (row["arm_id"], row["scenario_class"], row["sequence"]) for row in expected
    ]

    block_markers: list[tuple[str, str, str]] = []
    starts: list[tuple[int, str, str, str]] = []
    successes: list[tuple[int, str, str, str, int]] = []
    validations: list[tuple[str, str, str]] = []
    score_counts: list[int] = []
    current_score_count: int | None = None
    score_total = 0
    invocation_rows: list[dict[str, str]] = []
    preflight_rows: list[dict[str, str]] = []
    runtime_snapshot_rows: list[dict[str, str]] = []
    dataset_snapshot_rows: list[dict[str, str]] = []
    docker_snapshot_rows: list[dict[str, str]] = []
    dataset_runtime_rows: list[dict[str, str]] = []
    docker_runtime_rows: list[dict[str, str]] = []
    analytic_armed_rows: list[dict[str, str]] = []
    live_idle_count = 0
    done_count = 0
    done_line_index: int | None = None
    metadata_rows: list[dict[str, str]] = []
    failure_lines: list[str] = []

    for index, line in enumerate(lines):
        if line.startswith("I135_INVOCATION_START "):
            invocation_rows.append(
                _key_value_tokens(
                    line,
                    "I135_INVOCATION_START ",
                    exact_fields={"at", "pid", "manifest_sha256"},
                )
            )
        if line.startswith("I135_PREFLIGHT_OK "):
            preflight_rows.append(
                _key_value_tokens(
                    line,
                    "I135_PREFLIGHT_OK ",
                    exact_fields={"manifest_sha256", "blocks", "cells", "payloads", "remote"},
                )
            )
        if line.startswith("I135_RUNTIME_SNAPSHOT_OK "):
            runtime_snapshot_rows.append(
                _key_value_tokens(
                    line,
                    "I135_RUNTIME_SNAPSHOT_OK ",
                    exact_fields={"manifest_sha256", "path"},
                )
            )
        if line.startswith("I135_DATASET_SNAPSHOT_OK "):
            dataset_snapshot_rows.append(
                _key_value_tokens(
                    line,
                    "I135_DATASET_SNAPSHOT_OK ",
                    exact_fields={"sha256", "id", "files"},
                )
            )
        if line.startswith("I135_DOCKER_SNAPSHOT_OK "):
            docker_snapshot_rows.append(
                _key_value_tokens(
                    line,
                    "I135_DOCKER_SNAPSHOT_OK ",
                    exact_fields={"sha256", "id"},
                )
            )
        if line.startswith("I135_DATASET_RUNTIME_OK "):
            dataset_runtime_rows.append(
                _key_value_tokens(
                    line,
                    "I135_DATASET_RUNTIME_OK ",
                    exact_fields={"phase", "files"},
                )
            )
        if line.startswith("I135_DOCKER_RUNTIME_OK "):
            docker_runtime_rows.append(
                _key_value_tokens(
                    line,
                    "I135_DOCKER_RUNTIME_OK ",
                    exact_fields={"phase", "daemon_id"},
                )
            )
        if line.startswith("I135_ANALYTIC_ARMED "):
            analytic_armed_rows.append(
                _key_value_tokens(
                    line,
                    "I135_ANALYTIC_ARMED ",
                    exact_fields={
                        "lock",
                        "lock_id",
                        "output_root",
                        "python_wrapper_sha256",
                        "python_binary_sha256",
                        "python_binary_identity",
                    },
                )
            )
        if line.startswith("I135_LIVE_IDLE_OK "):
            live_idle_count += 1
        if line.startswith(
            (
                "I135_ABORT",
                "I135_BLOCK_VALIDATION_FAIL",
                "I135_PREFLIGHT_FAIL",
                "I135_LIVE_EVALUATOR_PROCESS_FAIL",
            )
        ):
            failure_lines.append(line)

        marker = _BLOCK_MARKER.fullmatch(line)
        if marker:
            if current_score_count is not None:
                score_counts.append(current_score_count)
            block_markers.append(marker.groups())
            current_score_count = 0
            continue
        if line.startswith("##### I135BLOCK"):
            raise ProofCollectionError(f"launcher-log:malformed-block-marker:line-{index + 1}")
        score = _SCORE.search(line)
        if score:
            if current_score_count is None:
                raise ProofCollectionError(f"launcher-log:score-without-block:line-{index + 1}")
            ncap, impact = map(float, score.groups())
            if not math.isfinite(ncap) or not math.isfinite(impact) or ncap < 0 or impact < 0:
                raise ProofCollectionError(f"launcher-log:invalid-score:line-{index + 1}")
            current_score_count += 1
            score_total += 1

        start = _BLOCK_START.fullmatch(line)
        if start:
            starts.append((int(start.group(1)), *start.groups()[1:]))
        success = _BLOCK_OK.fullmatch(line)
        if success:
            successes.append(
                (
                    int(success.group(1)),
                    success.group(2),
                    success.group(3),
                    success.group(4),
                    int(success.group(5)),
                )
            )
        valid = _BLOCK_VALID.fullmatch(line)
        if valid:
            validations.append(valid.groups())
        if line.startswith("I135_DONE_METADATA "):
            row: dict[str, str] = {}
            for token in line.removeprefix("I135_DONE_METADATA ").split():
                key, separator, value = token.partition("=")
                if not separator or not key or key in row:
                    raise ProofCollectionError(f"launcher-log:malformed-done-metadata:{token}")
                row[key] = value
            metadata_rows.append(row)
        if line == DONE_MARKER:
            done_count += 1
            done_line_index = index

    if current_score_count is not None:
        score_counts.append(current_score_count)
    if failure_lines:
        raise ProofCollectionError(f"launcher-log:failure-marker:{failure_lines[0]}")
    if len(invocation_rows) != 1:
        raise ProofCollectionError(f"launcher-log:invocation-count:{len(invocation_rows)}/1")
    if (
        len(preflight_rows) != 1
        or len(runtime_snapshot_rows) != 1
        or len(dataset_snapshot_rows) != 1
        or len(docker_snapshot_rows) != 1
        or len(analytic_armed_rows) != 1
        or live_idle_count != 1
    ):
        raise ProofCollectionError(
            "launcher-log:preflight-runtime-dataset-docker-live-count:"
            f"{len(preflight_rows)}/{len(runtime_snapshot_rows)}/"
            f"{len(dataset_snapshot_rows)}/{len(docker_snapshot_rows)}/"
            f"{len(analytic_armed_rows)}/{live_idle_count}"
        )
    manifest_sha = manifest_facts["launch_manifest_sha256"]
    runtime_snapshot = f"{RUNTIME_SNAPSHOT_ROOT}/i135-runtime-{manifest_sha}"
    if invocation_rows[0]["manifest_sha256"] != manifest_sha:
        raise ProofCollectionError("launcher-log:invocation-manifest-sha256")
    try:
        invocation_pid = int(invocation_rows[0]["pid"])
    except ValueError as error:
        raise ProofCollectionError("launcher-log:invocation-pid") from error
    if invocation_pid <= 0:
        raise ProofCollectionError("launcher-log:invocation-pid")
    if preflight_rows[0] != {
        "manifest_sha256": manifest_sha,
        "blocks": "120",
        "cells": "2400",
        "payloads": preflight_rows[0]["payloads"],
        "remote": preflight_rows[0]["remote"],
    }:
        raise ProofCollectionError("launcher-log:preflight-identity")
    for field in ("payloads", "remote"):
        try:
            if int(preflight_rows[0][field]) <= 0:
                raise ValueError
        except ValueError as error:
            raise ProofCollectionError(f"launcher-log:preflight-{field}") from error
    if runtime_snapshot_rows[0] != {
        "manifest_sha256": manifest_sha,
        "path": runtime_snapshot,
    }:
        raise ProofCollectionError("launcher-log:runtime-snapshot-identity")
    dataset_snapshot = dataset_snapshot_rows[0]
    docker_snapshot = docker_snapshot_rows[0]
    if (
        _HEX_SHA256.fullmatch(dataset_snapshot["sha256"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", dataset_snapshot["id"]) is None
        or dataset_snapshot["files"] != "28"
    ):
        raise ProofCollectionError("launcher-log:dataset-snapshot-receipt")
    if (
        _HEX_SHA256.fullmatch(docker_snapshot["sha256"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", docker_snapshot["id"]) is None
    ):
        raise ProofCollectionError("launcher-log:docker-snapshot-receipt")
    expected_runtime_phase_counts = {
        "analytic-arm": 1,
        "before": 120,
        "after": 120,
        "before-done": 1,
    }
    dataset_phase_counts = Counter(row["phase"] for row in dataset_runtime_rows)
    docker_phase_counts = Counter(row["phase"] for row in docker_runtime_rows)
    docker_daemon_ids = {row["daemon_id"] for row in docker_runtime_rows}
    if dict(dataset_phase_counts) != expected_runtime_phase_counts or any(
        row["files"] != "28" for row in dataset_runtime_rows
    ):
        raise ProofCollectionError(
            f"launcher-log:dataset-runtime-check-counts:{dict(dataset_phase_counts)}"
        )
    if (
        dict(docker_phase_counts) != expected_runtime_phase_counts
        or len(docker_daemon_ids) != 1
        or not next(iter(docker_daemon_ids), "")
    ):
        raise ProofCollectionError(
            f"launcher-log:docker-runtime-check-counts:{dict(docker_phase_counts)}"
        )
    if block_markers != expected_identity:
        raise ProofCollectionError("launcher-log:block-marker-order-or-identity")
    if score_counts != [20] * 120 or score_total != 2400:
        raise ProofCollectionError(
            f"launcher-log:score-completeness:{score_total}/2400:block-counts={score_counts[:3]}"
        )
    expected_starts = [
        (row["ordinal"], row["arm_id"], row["scenario_class"], row["sequence"])
        for row in expected
    ]
    expected_successes = [(*row, 20) for row in expected_starts]
    if starts != expected_starts:
        raise ProofCollectionError("launcher-log:block-start-order-or-identity")
    if successes != expected_successes:
        raise ProofCollectionError("launcher-log:block-success-order-or-identity")
    if validations != expected_identity:
        raise ProofCollectionError("launcher-log:block-validation-order-or-identity")
    if done_count != 1 or done_line_index != len(lines) - 1:
        raise ProofCollectionError(f"launcher-log:done-marker-count-or-position:{done_count}")
    if len(metadata_rows) != 1:
        raise ProofCollectionError(f"launcher-log:done-metadata-count:{len(metadata_rows)}")
    metadata = metadata_rows[0]
    required_metadata = {
        "at",
        "manifest_sha256",
        "runtime_snapshot",
        "dataset_runtime_snapshot_sha256",
        "dataset_runtime_snapshot_id",
        "docker_runtime_snapshot_sha256",
        "docker_runtime_snapshot_id",
        "python_wrapper_sha256",
        "python_binary_sha256",
        "python_binary_identity",
        "launch_lock_retained",
        "launch_lock_id",
        "elapsed_seconds",
        "prior_smoke_gpu_seconds",
        "blocks",
        "episodes",
        "output_root",
        "output_device",
        "output_uuid",
        "start_free_bytes",
        "end_free_bytes",
        "output_bytes",
    }
    if set(metadata) != required_metadata:
        raise ProofCollectionError(
            "launcher-log:done-metadata-fields:"
            f"missing={sorted(required_metadata - set(metadata))}:"
            f"extra={sorted(set(metadata) - required_metadata)}"
        )
    try:
        elapsed = int(metadata["elapsed_seconds"])
        prior_smoke = int(metadata["prior_smoke_gpu_seconds"])
        blocks = int(metadata["blocks"])
        episodes = int(metadata["episodes"])
        start_free_bytes = int(metadata["start_free_bytes"])
        end_free_bytes = int(metadata["end_free_bytes"])
        output_bytes = int(metadata["output_bytes"])
    except ValueError as error:
        raise ProofCollectionError("launcher-log:done-metadata-integer") from error
    if elapsed < 0 or blocks != 120 or episodes != 2400:
        raise ProofCollectionError("launcher-log:done-metadata-values")
    expected_done_identity = {
        "manifest_sha256": manifest_sha,
        "runtime_snapshot": runtime_snapshot,
        "dataset_runtime_snapshot_sha256": dataset_snapshot["sha256"],
        "dataset_runtime_snapshot_id": dataset_snapshot["id"],
        "docker_runtime_snapshot_sha256": docker_snapshot["sha256"],
        "docker_runtime_snapshot_id": docker_snapshot["id"],
        "python_wrapper_sha256": analytic_armed_rows[0]["python_wrapper_sha256"],
        "python_binary_sha256": analytic_armed_rows[0]["python_binary_sha256"],
        "python_binary_identity": analytic_armed_rows[0]["python_binary_identity"],
        "launch_lock_retained": EXPECTED_LAUNCH_LOCK,
        "launch_lock_id": analytic_armed_rows[0]["lock_id"],
        "output_root": EXPECTED_OUTPUT_ROOT,
        "output_device": EXPECTED_OUTPUT_DEVICE,
        "output_uuid": EXPECTED_OUTPUT_UUID,
    }
    for field, expected_value in expected_done_identity.items():
        if metadata[field] != expected_value:
            raise ProofCollectionError(
                f"launcher-log:done-{field}:{metadata[field]!r}!={expected_value!r}"
            )
    if analytic_armed_rows[0] != {
        "lock": EXPECTED_LAUNCH_LOCK,
        "lock_id": metadata["launch_lock_id"],
        "output_root": EXPECTED_OUTPUT_ROOT,
        "python_wrapper_sha256": metadata["python_wrapper_sha256"],
        "python_binary_sha256": metadata["python_binary_sha256"],
        "python_binary_identity": metadata["python_binary_identity"],
    } or (
        re.fullmatch(r"[0-9]+:[0-9]+", metadata["launch_lock_id"]) is None
        or _HEX_SHA256.fullmatch(metadata["python_wrapper_sha256"]) is None
        or _HEX_SHA256.fullmatch(metadata["python_binary_sha256"]) is None
        or re.fullmatch(r"[0-9]+:[0-9]+", metadata["python_binary_identity"]) is None
    ):
        raise ProofCollectionError("launcher-log:analytic-armed-identity")
    if start_free_bytes < manifest_facts["minimum_remote_free_bytes"]:
        raise ProofCollectionError("launcher-log:start-free-below-minimum")
    if end_free_bytes < manifest_facts["minimum_reserve_bytes"]:
        raise ProofCollectionError("launcher-log:end-free-below-reserve")
    if output_bytes < 0 or output_bytes > manifest_facts["projected_output_bytes"]:
        raise ProofCollectionError("launcher-log:output-bytes-above-projection")
    if prior_smoke != manifest_facts["prior_smoke_gpu_seconds"]:
        raise ProofCollectionError("launcher-log:prior-smoke-mismatch")
    if elapsed > manifest_facts["remaining_analytic_seconds"]:
        raise ProofCollectionError("launcher-log:analytic-resource-ceiling")
    if elapsed + prior_smoke > manifest_facts["total_gpu_ceiling_seconds"]:
        raise ProofCollectionError("launcher-log:total-resource-ceiling")
    return {
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "invocations": len(invocation_rows),
        "blocks": len(successes),
        "cells": score_total,
        "done_marker_count": done_count,
        "elapsed_seconds": elapsed,
        "prior_smoke_gpu_seconds": prior_smoke,
        "retry_policy_violations": 0,
        "runtime_snapshot": runtime_snapshot,
        "dataset_runtime_snapshot_sha256": dataset_snapshot["sha256"],
        "dataset_runtime_snapshot_id": dataset_snapshot["id"],
        "docker_runtime_snapshot_sha256": docker_snapshot["sha256"],
        "docker_runtime_snapshot_id": docker_snapshot["id"],
        "python_wrapper_sha256": metadata["python_wrapper_sha256"],
        "python_binary_sha256": metadata["python_binary_sha256"],
        "python_binary_identity": metadata["python_binary_identity"],
        "launch_lock_retained": EXPECTED_LAUNCH_LOCK,
        "launch_lock_id": metadata["launch_lock_id"],
        "dataset_runtime_check_counts": expected_runtime_phase_counts,
        "docker_runtime_check_counts": expected_runtime_phase_counts,
        "docker_runtime_daemon_id": next(iter(docker_daemon_ids)),
        "invocation_pid": invocation_pid,
        "output_root": EXPECTED_OUTPUT_ROOT,
        "output_device": EXPECTED_OUTPUT_DEVICE,
        "output_uuid": EXPECTED_OUTPUT_UUID,
        "start_free_bytes": start_free_bytes,
        "end_free_bytes": end_free_bytes,
        "output_bytes": output_bytes,
    }


def validate_run_log(path: Path, manifest_facts: Mapping[str, Any]) -> dict[str, Any]:
    """Read one stable launcher log and validate those exact bytes."""

    _require_regular_file(path, "launcher-log")
    return validate_run_log_payload(_read_stable_file(path, "launcher-log"), manifest_facts)


def _check_tree_exact(root: Path, expected_relative_files: set[str], label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ProofCollectionError(f"required-directory:{label}:{root}")
    actual: set[str] = set()
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ProofCollectionError(f"symlink-forbidden:{label}:{item}")
        if item.is_file():
            actual.add(item.relative_to(root).as_posix())
        elif not item.is_dir():
            raise ProofCollectionError(f"special-file-forbidden:{label}:{item}")
    missing = sorted(expected_relative_files - actual)
    extra = sorted(actual - expected_relative_files)
    if missing or extra:
        raise ProofCollectionError(
            f"tree-not-exact:{label}:missing={missing[:1]}({len(missing)}):extra={extra[:1]}({len(extra)})"
        )


def validate_decision_tree(decision_root: Path) -> dict[str, list[Path]]:
    if decision_root.is_symlink() or not decision_root.is_dir():
        raise ProofCollectionError(f"required-directory:decision-root:{decision_root}")
    expected_directories = set(ARM_SHORT.values())
    actual_directories = {item.name for item in decision_root.iterdir() if item.is_dir() and not item.is_symlink()}
    non_directories = [item.name for item in decision_root.iterdir() if not item.is_dir() or item.is_symlink()]
    if actual_directories != expected_directories or non_directories:
        raise ProofCollectionError(
            "decision-root:not-exact:"
            f"dirs={sorted(actual_directories)}:other={sorted(non_directories)}"
        )
    paths: dict[str, list[Path]] = {}
    for arm in ARMS:
        arm_root = decision_root / ARM_SHORT[arm]
        expected_names = {f"{scenario_class}-{pair}.jsonl" for scenario_class, pair in canonical_pairs()}
        _check_tree_exact(arm_root, expected_names, f"decision:{arm}")
        paths[arm] = [
            arm_root / f"{scenario_class}-{pair}.jsonl"
            for scenario_class, pair in canonical_pairs()
        ]
    return paths


def _stable_stat(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat(follow_symlinks=False)
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _fd_stat(handle: BinaryIO) -> tuple[int, int, int, int]:
    stat = os.fstat(handle.fileno())
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _read_stable_file(path: Path, label: str) -> bytes:
    before_path = _stable_stat(path)
    with path.open("rb") as handle:
        before_fd = _fd_stat(handle)
        if before_fd != before_path:
            raise ProofCollectionError(f"source-replaced-before-read:{label}:{path}")
        payload = handle.read()
        after_fd = _fd_stat(handle)
    after_path = _stable_stat(path)
    if before_fd != after_fd or after_fd != after_path or len(payload) != after_fd[2]:
        raise ProofCollectionError(f"source-mutated-during-read:{label}:{path}")
    return payload


def _read_stable_evidence_file(path: Path, label: str) -> tuple[bytes, str]:
    """Read immutable runtime evidence once and retain its source inode identity."""

    _require_regular_file(path, label)
    before_path = _stable_stat(path)
    with path.open("rb") as handle:
        before_fd = _fd_stat(handle)
        if before_fd != before_path:
            raise ProofCollectionError(f"source-replaced-before-read:{label}:{path}")
        payload = handle.read()
        after_fd = _fd_stat(handle)
    after_path = _stable_stat(path)
    if before_fd != after_fd or after_fd != after_path or len(payload) != after_fd[2]:
        raise ProofCollectionError(f"source-mutated-during-read:{label}:{path}")
    return payload, f"{before_fd[0]}:{before_fd[1]}"


def _validate_and_copy_decision_block(
    source: Path,
    destination: BinaryIO,
    arm: str,
    scenario_class: str,
    pair: str,
) -> dict[str, Any]:
    payload = _read_stable_file(source, "decision")
    receipt = _validate_decision_block_payload(
        payload,
        arm,
        scenario_class,
        pair,
        str(source),
    )
    destination.write(payload)
    return receipt


def _validate_decision_block_payload(
    payload: bytes,
    arm: str,
    scenario_class: str,
    pair: str,
    label: str,
) -> dict[str, Any]:
    """Replay one decision block from the exact bytes copied into the proof stream."""

    digest = hashlib.sha256()
    byte_count = 0
    reset_runs: list[int] = []
    identity_count = 0
    current_run: int | None = None
    line_count = 0
    for line_count, raw_line in enumerate(payload.splitlines(keepends=True), 1):
        if not raw_line.endswith(b"\n"):
            raise ProofCollectionError(f"decision:unterminated-line:{label}:{line_count}")
        digest.update(raw_line)
        byte_count += len(raw_line)
        row = _strict_json_bytes(raw_line, f"{label}:{line_count}")
        if not isinstance(row, dict):
            raise ProofCollectionError(f"decision:row-not-object:{label}:{line_count}")
        if row.get("schedule_missing") or "intervene_err" in row:
            raise ProofCollectionError(f"decision:runtime-error:{label}:{line_count}")
        if "arm" in row and row["arm"] != arm:
            raise ProofCollectionError(f"decision:arm-identity:{label}:{line_count}")
        if "class" in row and row["class"] != scenario_class:
            raise ProofCollectionError(f"decision:class-identity:{label}:{line_count}")
        if "pair" in row and row["pair"] != pair:
            raise ProofCollectionError(f"decision:pair-identity:{label}:{line_count}")
        if arm in BLIND_ARMS:
            if row.get("dose") != arm:
                raise ProofCollectionError(f"decision:dose-identity:{label}:{line_count}")
            if (row.get("class"), row.get("pair")) != (scenario_class, pair):
                raise ProofCollectionError(f"decision:schedule-identity:{label}:{line_count}")
        if row.get("block_identity") is True:
            identity_count += 1
            if line_count != 1 or (row.get("arm"), row.get("class"), row.get("pair")) != (
                arm,
                scenario_class,
                pair,
            ):
                raise ProofCollectionError(f"decision:block-identity:{label}:{line_count}")
            continue
        if row.get("reset") is True:
            run = row.get("run")
            if type(run) is not int:
                raise ProofCollectionError(f"decision:reset-run-type:{label}:{line_count}")
            reset_runs.append(run)
            current_run = run
        else:
            if current_run is None:
                raise ProofCollectionError(f"decision:row-before-reset:{label}:{line_count}")
            if row.get("run") != current_run:
                raise ProofCollectionError(f"decision:row-run-identity:{label}:{line_count}")
    if line_count == 0:
        raise ProofCollectionError(f"decision:empty:{label}")
    if reset_runs != list(RUNS):
        raise ProofCollectionError(f"decision:reset-order:{label}:{reset_runs}")
    expected_identity_count = 0 if arm in BLIND_ARMS else 1
    if identity_count != expected_identity_count:
        raise ProofCollectionError(
            f"decision:block-identity-count:{label}:{identity_count}/{expected_identity_count}"
        )
    return {
        "arm": arm,
        "scenario_class": scenario_class,
        "pair": pair,
        "reset_count": len(reset_runs),
        "source_sha256": digest.hexdigest(),
        "source_bytes": byte_count,
        "source_lines": line_count,
    }


def _open_deterministic_gzip(path: Path) -> tuple[BinaryIO, gzip.GzipFile]:
    raw = path.open("xb")
    compressed = gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0)
    return raw, compressed


def collect_decisions(
    paths: Mapping[str, Sequence[Path]], staging: Path
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    block_receipts: dict[str, list[dict[str, Any]]] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        destination = staging / DECISION_FILENAMES[arm]
        raw, compressed = _open_deterministic_gzip(destination)
        rows: list[dict[str, Any]] = []
        try:
            for source, (scenario_class, pair) in zip(paths[arm], canonical_pairs(), strict=True):
                rows.append(
                    _validate_and_copy_decision_block(
                        source,
                        compressed,
                        arm,
                        scenario_class,
                        pair,
                    )
                )
        finally:
            compressed.close()
            raw.flush()
            os.fsync(raw.fileno())
            raw.close()
        block_receipts[arm] = rows
        role = f"decision_{arm}"
        artifacts[role] = _artifact_receipt(destination, destination.name)
    return block_receipts, artifacts


def _decompress_gzip_bytes(payload: bytes, label: str) -> bytes:
    try:
        decompressed = gzip.decompress(payload)
    except (EOFError, OSError) as error:
        raise ProofCollectionError(f"gzip-unreadable:{label}:{error}") from error
    if not payload.startswith(b"\x1f\x8b"):
        raise ProofCollectionError(f"gzip-header-missing:{label}")
    return decompressed


def replay_packaged_decision_stream(payload: bytes, arm: str) -> list[dict[str, Any]]:
    """Independently recover and validate all 20 source blocks in one arm proof."""

    decompressed = _decompress_gzip_bytes(payload, f"decision:{arm}")
    lines = decompressed.splitlines(keepends=True)
    if not lines or any(not line.endswith(b"\n") for line in lines):
        raise ProofCollectionError(f"decision:packaged-lines:{arm}")
    starts: list[int] = []
    for index, raw_line in enumerate(lines):
        row = _strict_json_bytes(raw_line, f"decision:{arm}:packaged-line-{index + 1}")
        if not isinstance(row, dict):
            raise ProofCollectionError(f"decision:packaged-row-not-object:{arm}:{index + 1}")
        if arm in BLIND_ARMS:
            if row.get("reset") is True and row.get("run") == 0:
                starts.append(index)
        elif row.get("block_identity") is True:
            starts.append(index)
    if starts != sorted(set(starts)) or len(starts) != len(canonical_pairs()) or starts[0] != 0:
        raise ProofCollectionError(f"decision:packaged-block-count:{arm}:{len(starts)}/20")
    boundaries = [*starts, len(lines)]
    receipts: list[dict[str, Any]] = []
    for block_index, (scenario_class, pair) in enumerate(canonical_pairs()):
        block_payload = b"".join(lines[boundaries[block_index] : boundaries[block_index + 1]])
        receipts.append(
            _validate_decision_block_payload(
                block_payload,
                arm,
                scenario_class,
                pair,
                f"packaged:{arm}:{scenario_class}-{pair}",
            )
        )
    if len(receipts) != 20 or sum(row["reset_count"] for row in receipts) != 400:
        raise ProofCollectionError(f"decision:packaged-completeness:{arm}")
    return receipts


def validate_runs_tree(runs_root: Path) -> None:
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise ProofCollectionError(f"required-directory:runs-root:{runs_root}")
    expected_run_dirs = set(ARM_RUN_DIR.values())
    unexpected_i135 = sorted(
        child.name
        for child in runs_root.iterdir()
        if child.name.startswith("i135-") and child.name not in expected_run_dirs
    )
    if unexpected_i135:
        raise ProofCollectionError(f"runs-root:unexpected-i135-directories:{unexpected_i135}")
    for arm, directory in ARM_RUN_DIR.items():
        arm_root = runs_root / directory
        expected = {
            f"{scenario_class}-{pair}/run_{run}/{name}"
            for scenario_class, pair in canonical_pairs()
            for run in RUNS
            for name in RUN_ARTIFACT_NAMES
        }
        _check_tree_exact(arm_root, expected, f"runs:{arm}")


def _validate_run_payload(payload: bytes, name: str, member_name: str) -> None:
    value = _strict_json_bytes(payload, member_name)
    if name in {"ego_poses.json", "metrics.json"} and not isinstance(value, dict):
        raise ProofCollectionError(f"run-json-object-required:{member_name}")
    if name == "actors.json" and not isinstance(value, (dict, list)):
        raise ProofCollectionError(f"run-actors-container-required:{member_name}")


def collect_runs(runs_root: Path, destination: Path) -> dict[str, Any]:
    aggregate = hashlib.sha256()
    member_count = 0
    cell_count = 0
    raw, compressed = _open_deterministic_gzip(destination)
    try:
        with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.GNU_FORMAT) as archive:
            for arm, scenario_class, pair, run in expected_cells():
                cell_count += 1
                for name in RUN_ARTIFACT_NAMES:
                    member_name = f"{ARM_RUN_DIR[arm]}/{scenario_class}-{pair}/run_{run}/{name}"
                    source = runs_root / member_name
                    payload = _read_stable_file(source, "runs")
                    _validate_run_payload(payload, name, member_name)
                    digest = sha256_bytes(payload)
                    encoded_name = member_name.encode("utf-8")
                    aggregate.update(len(encoded_name).to_bytes(8, "big"))
                    aggregate.update(encoded_name)
                    aggregate.update(len(payload).to_bytes(8, "big"))
                    aggregate.update(bytes.fromhex(digest))
                    info = tarfile.TarInfo(member_name)
                    info.size = len(payload)
                    info.mode = 0o444
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, fileobj=_BytesReader(payload))
                    member_count += 1
    finally:
        compressed.close()
        raw.flush()
        os.fsync(raw.fileno())
        raw.close()
    if member_count != 7200 or cell_count != 2400:
        raise ProofCollectionError(f"runs:archive-count:{member_count}/7200:{cell_count}/2400")
    return {
        "member_count": member_count,
        "cell_count": cell_count,
        "source_tree_sha256": aggregate.hexdigest(),
    }


def replay_packaged_runs(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay the exact stable tar bytes and require the canonical 7,200-member archive."""

    _require_regular_file(path, "packaged-runs")
    before = _stable_stat(path)
    compressed_digest = hashlib.sha256()
    compressed_bytes = 0
    aggregate = hashlib.sha256()
    member_count = 0
    expected_names = [
        f"{ARM_RUN_DIR[arm]}/{scenario_class}-{pair}/run_{run}/{name}"
        for arm, scenario_class, pair, run in expected_cells()
        for name in RUN_ARTIFACT_NAMES
    ]
    try:
        with path.open("rb") as handle:
            if _fd_stat(handle) != before:
                raise ProofCollectionError(f"runs:packaged-replaced-before-read:{path}")
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                compressed_digest.update(chunk)
                compressed_bytes += len(chunk)
            handle.seek(0)
            with tarfile.open(fileobj=handle, mode="r:gz") as archive:
                members = archive.getmembers()
                actual_names = [member.name for member in members]
                if actual_names != expected_names:
                    mismatch = next(
                        (
                            index
                            for index, (actual, expected) in enumerate(
                                zip(actual_names, expected_names, strict=False)
                            )
                            if actual != expected
                        ),
                        min(len(actual_names), len(expected_names)),
                    )
                    raise ProofCollectionError(
                        "runs:packaged-member-order-or-set:"
                        f"count={len(actual_names)}/7200:first-mismatch={mismatch}"
                    )
                for member, member_name in zip(members, expected_names, strict=True):
                    if not member.isfile():
                        raise ProofCollectionError(f"runs:packaged-not-regular:{member_name}")
                    if (
                        member.mode != 0o444
                        or member.mtime != 0
                        or member.uid != 0
                        or member.gid != 0
                        or member.uname != ""
                        or member.gname != ""
                    ):
                        raise ProofCollectionError(f"runs:packaged-metadata:{member_name}")
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise ProofCollectionError(f"runs:packaged-unreadable:{member_name}")
                    payload = extracted.read()
                    if len(payload) != member.size:
                        raise ProofCollectionError(f"runs:packaged-size:{member_name}")
                    name = member_name.rsplit("/", 1)[1]
                    _validate_run_payload(payload, name, member_name)
                    digest = sha256_bytes(payload)
                    encoded_name = member_name.encode("utf-8")
                    aggregate.update(len(encoded_name).to_bytes(8, "big"))
                    aggregate.update(encoded_name)
                    aggregate.update(len(payload).to_bytes(8, "big"))
                    aggregate.update(bytes.fromhex(digest))
                    member_count += 1
            after_fd = _fd_stat(handle)
    except tarfile.TarError as error:
        raise ProofCollectionError(f"runs:packaged-tar:{error}") from error
    after = _stable_stat(path)
    if before != after_fd or after_fd != after:
        raise ProofCollectionError(f"runs:packaged-mutated-during-read:{path}")
    if member_count != 7200:
        raise ProofCollectionError(f"runs:packaged-member-count:{member_count}/7200")
    return (
        {
            "member_count": member_count,
            "cell_count": member_count // len(RUN_ARTIFACT_NAMES),
            "source_tree_sha256": aggregate.hexdigest(),
        },
        {
            "path": path.name,
            "sha256": compressed_digest.hexdigest(),
            "bytes": compressed_bytes,
        },
    )


class _BytesReader:
    """Minimal zero-copy reader accepted by ``TarFile.addfile``."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.offset = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.payload) - self.offset
        chunk = self.payload[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def _artifact_receipt(path: Path, relative: str) -> dict[str, Any]:
    return {"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def _artifact_receipt_bytes(payload: bytes, relative: str) -> dict[str, Any]:
    return {"path": relative, "sha256": sha256_bytes(payload), "bytes": len(payload)}


def _compress_bytes(payload: bytes, destination: Path) -> None:
    raw, compressed = _open_deterministic_gzip(destination)
    try:
        compressed.write(payload)
    finally:
        compressed.close()
        raw.flush()
        os.fsync(raw.fileno())
        raw.close()


def _build_validity_receipt(
    manifest_facts: Mapping[str, Any],
    log_receipt: Mapping[str, Any],
    runtime_receipts: Mapping[str, Mapping[str, Any]],
    local_free_bytes: int,
) -> dict[str, Any]:
    gates = dict(manifest_facts["manifest_gates"])
    if set(gates) != set(REQUIRED_MANIFEST_GATES) or any(value is not True for value in gates.values()):
        raise ProofCollectionError("validity-receipt:manifest-gate-derivation-failed")
    manifest_dataset_provenance = manifest_facts.get("dataset_provenance")
    if (
        manifest_facts.get("manifest_dataset_gate") is not True
        or not isinstance(manifest_dataset_provenance, dict)
        or manifest_dataset_provenance.get("manifest_gate") != "g7_dataset_provenance"
        or manifest_dataset_provenance.get("passed") is not True
    ):
        raise ProofCollectionError("validity-receipt:dataset-gate-derivation-failed")
    if set(runtime_receipts) != {
        "dataset_runtime_snapshot",
        "docker_runtime_snapshot",
        "analytic_lock",
    }:
        raise ProofCollectionError("validity-receipt:runtime-snapshot-role-set")
    dataset_runtime = runtime_receipts["dataset_runtime_snapshot"]
    docker_runtime = runtime_receipts["docker_runtime_snapshot"]
    analytic_lock = runtime_receipts["analytic_lock"]
    if (
        dataset_runtime.get("sha256") != log_receipt.get("dataset_runtime_snapshot_sha256")
        or docker_runtime.get("sha256") != log_receipt.get("docker_runtime_snapshot_sha256")
    ):
        raise ProofCollectionError("validity-receipt:runtime-snapshot-log-binding")
    if (
        analytic_lock.get("source_id") != log_receipt.get("launch_lock_id")
        or analytic_lock.get("dataset_runtime_snapshot_sha256")
        != dataset_runtime.get("sha256")
        or analytic_lock.get("docker_runtime_snapshot_sha256") != docker_runtime.get("sha256")
    ):
        raise ProofCollectionError("validity-receipt:analytic-lock-binding")
    runtime_contract = manifest_dataset_provenance.get("runtime_snapshot_contract")
    if not isinstance(runtime_contract, dict) or dataset_runtime.get("source_path") != runtime_contract.get(
        "path"
    ):
        raise ProofCollectionError("validity-receipt:dataset-runtime-path")
    dataset_provenance = {
        **manifest_dataset_provenance,
        "runtime_snapshot_contract": {
            **runtime_contract,
            "sha256": dataset_runtime["sha256"],
            "bytes": dataset_runtime["bytes"],
            "source_id": dataset_runtime["source_id"],
        },
    }
    docker_provenance = {
        "schema": DOCKER_RUNTIME_SCHEMA,
        "path": docker_runtime["source_path"],
        "manifest_sha256": docker_runtime["manifest_sha256"],
        "sha256": docker_runtime["sha256"],
        "bytes": docker_runtime["bytes"],
        "source_id": docker_runtime["source_id"],
        "client_path": docker_runtime["client_path"],
        "client_sha256": docker_runtime["client_sha256"],
        "context": docker_runtime["context"],
        "endpoint": docker_runtime["endpoint"],
        "daemon_id": docker_runtime["daemon_id"],
        "server_version": docker_runtime["server_version"],
    }
    analytic_lock_provenance = {
        "schema": ANALYTIC_LOCK_SCHEMA,
        "path": analytic_lock["source_path"],
        "source_id": analytic_lock["source_id"],
        "sha256": analytic_lock["sha256"],
        "bytes": analytic_lock["bytes"],
        "manifest_sha256": analytic_lock["manifest_sha256"],
        "dataset_runtime_snapshot_sha256": analytic_lock[
            "dataset_runtime_snapshot_sha256"
        ],
        "docker_runtime_snapshot_sha256": analytic_lock[
            "docker_runtime_snapshot_sha256"
        ],
        "python_wrapper_sha256": analytic_lock["python_wrapper_sha256"],
        "python_binary_sha256": analytic_lock["python_binary_sha256"],
        "python_binary_identity": analytic_lock["python_binary_identity"],
        "github_launch_authority": analytic_lock["github_launch_authority"],
        "pid": analytic_lock["pid"],
        "created_at_utc": analytic_lock["created_at_utc"],
    }
    elapsed = log_receipt["elapsed_seconds"]
    prior = log_receipt["prior_smoke_gpu_seconds"]
    if elapsed + prior > manifest_facts["total_gpu_ceiling_seconds"]:
        raise ProofCollectionError("validity-receipt:resource-derivation-failed")
    local_free_gib = local_free_bytes / 1024**3
    return {
        "schema": VALIDITY_SCHEMA,
        "launch_manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "gates": gates,
        # This is intentionally separate: analytic-validity G7 remains completion/order.
        "dataset_provenance": dataset_provenance,
        "docker_runtime_provenance": docker_provenance,
        "analytic_lock_provenance": analytic_lock_provenance,
        "falsifiers_clear": True,
        "done_marker": DONE_MARKER,
        "analytic_gpu_hours": elapsed / 3600,
        "total_gpu_hours_including_smoke": (elapsed + prior) / 3600,
        "remote_free_gib_at_launch": manifest_facts["remote_free_gib_at_launch"],
        "remote_projected_reserve_gib": manifest_facts["remote_projected_reserve_gib"],
        "local_free_gib_at_collection": local_free_gib,
        "retry_policy_violations": log_receipt["retry_policy_violations"],
        "unexpected_falsifiers": [],
        "derivation": {
            **{
                gate: f"launch_manifest.gates.{name} == true"
                for gate, name in REQUIRED_MANIFEST_GATES.items()
            },
            "completion": (
                "launcher log has one invocation, one final I135_DOSE_DONE, 120 canonical "
                "successful blocks, 2400 scores, exact decision resets, and 7200 run files"
            ),
            "resources": (
                "I135_DONE_METADATA.elapsed_seconds + manifest prior_smoke_gpu_seconds <= "
                "manifest total_gpu_ceiling_seconds"
            ),
            "storage": (
                "manifest launch storage gate plus collection-time shutil.disk_usage free bytes"
            ),
            "dataset_provenance": (
                "launch_manifest.gates.g7_dataset_provenance == true; top-level dataset_receipt "
                "equals environment_receipts.dataset; the v3 environment binding, frozen nuScenes "
                "contract, packaged dataset runtime snapshot, DONE hash, and derived runtime "
                "snapshot contract all match"
            ),
            "docker_runtime_provenance": (
                "the packaged canonical Docker runtime snapshot matches the DONE hash and binds "
                "the physical client, default context, Unix socket endpoint, daemon identity, "
                "and server version"
            ),
            "analytic_lock_provenance": (
                "the exact retained analytic-lock bytes and inode identity match I135_ANALYTIC_ARMED "
                "and DONE metadata and bind the manifest plus both runtime-snapshot hashes"
            ),
        },
    }


def _disk_free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def collect_proof(
    *,
    run_log: Path,
    decision_root: Path,
    runs_root: Path,
    launch_manifest: Path,
    proof_dir: Path,
    free_bytes_provider: Callable[[Path], int] = _disk_free_bytes,
    runtime_evidence_provider: Callable[[Path, str], tuple[bytes, str]] = (
        _read_stable_evidence_file
    ),
) -> dict[str, Any]:
    """Collect a complete proof atomically; dependency injection is reserved for tests."""

    proof_dir = proof_dir.resolve()
    if proof_dir.exists():
        raise ProofCollectionError(f"proof-output-already-exists:{proof_dir}")
    if not proof_dir.parent.is_dir():
        raise ProofCollectionError(f"proof-parent-missing:{proof_dir.parent}")
    local_free_bytes = free_bytes_provider(proof_dir.parent)
    if type(local_free_bytes) is not int or local_free_bytes < MINIMUM_LOCAL_FREE_BYTES:
        raise ProofCollectionError(
            f"local-free-space:{local_free_bytes}/{MINIMUM_LOCAL_FREE_BYTES}-bytes"
        )

    manifest, manifest_facts = validate_manifest(launch_manifest.resolve())
    log_payload = _read_stable_file(run_log.resolve(), "launcher-log")
    log_receipt = validate_run_log_payload(log_payload, manifest_facts)
    runtime_root = Path(log_receipt["runtime_snapshot"])
    runtime_source_paths = {
        "dataset_runtime_snapshot": runtime_root / "dataset_runtime_snapshot.json",
        "docker_runtime_snapshot": runtime_root / "docker_runtime_snapshot.json",
        "analytic_lock": Path(log_receipt["launch_lock_retained"]),
    }
    runtime_payloads: dict[str, bytes] = {}
    runtime_source_ids: dict[str, str] = {}
    for role, source_path in runtime_source_paths.items():
        payload, source_id = runtime_evidence_provider(source_path, role)
        if not isinstance(payload, bytes) or not isinstance(source_id, str):
            raise ProofCollectionError(f"runtime-evidence:provider-contract:{role}")
        runtime_payloads[role] = payload
        runtime_source_ids[role] = source_id
    runtime_receipts = validate_runtime_evidence_payloads(
        runtime_payloads,
        source_ids=runtime_source_ids,
        manifest=manifest,
        manifest_facts=manifest_facts,
        log_receipt=log_receipt,
    )
    decision_paths = validate_decision_tree(decision_root.resolve())
    validate_runs_tree(runs_root.resolve())

    staging = Path(tempfile.mkdtemp(prefix=".i135-proof-stage-", dir=proof_dir.parent))
    try:
        artifacts: dict[str, dict[str, Any]] = {}
        compressed_log = staging / "sentinel-i135.log.gz"
        _compress_bytes(log_payload, compressed_log)
        artifacts["i135_log"] = _artifact_receipt(compressed_log, compressed_log.name)

        for role, filename in RUNTIME_EVIDENCE_FILENAMES.items():
            destination = staging / filename
            _write_bytes(destination, runtime_payloads[role])
            artifacts[role] = _artifact_receipt(destination, destination.name)

        decision_blocks, decision_artifacts = collect_decisions(decision_paths, staging)
        artifacts.update(decision_artifacts)

        runs_archive = staging / "i135-runs.tar.gz"
        run_archive_receipt = collect_runs(runs_root.resolve(), runs_archive)
        artifacts["i135_runs"] = _artifact_receipt(runs_archive, runs_archive.name)

        validity = _build_validity_receipt(
            manifest_facts,
            log_receipt,
            runtime_receipts,
            local_free_bytes,
        )
        validity_path = staging / "launch_validity_receipt.json"
        _write_bytes(validity_path, _canonical_json(validity))
        artifacts["validity_receipt"] = _artifact_receipt(validity_path, validity_path.name)

        raw_receipt = {
            "schema": SCHEMA,
            "verdict": "I135_RAW_PROOF_COMPLETE",
            "launch_manifest_sha256": manifest_facts["launch_manifest_sha256"],
            "collector_sha256": sha256_file(Path(__file__).resolve()),
            "collection_gate": {
                "minimum_local_free_bytes": MINIMUM_LOCAL_FREE_BYTES,
                "observed_local_free_bytes": local_free_bytes,
                "passed": True,
            },
            "completion": {
                "done_marker": DONE_MARKER,
                "done_marker_count": log_receipt["done_marker_count"],
                "successful_blocks": log_receipt["blocks"],
                "analytic_cells": log_receipt["cells"],
                "decision_blocks": sum(len(rows) for rows in decision_blocks.values()),
                "decision_resets": sum(
                    row["reset_count"] for rows in decision_blocks.values() for row in rows
                ),
                "run_archive_cells": run_archive_receipt["cell_count"],
                "run_archive_members": run_archive_receipt["member_count"],
            },
            "source_receipts": {
                "launcher_log": log_receipt,
                "runtime_evidence": runtime_receipts,
                "decision_blocks": decision_blocks,
                "run_tree": run_archive_receipt,
            },
            "artifacts": dict(sorted(artifacts.items())),
            "problem_count": 0,
            "problems": [],
        }
        raw_receipt_path = staging / "raw_proof_receipt.json"
        _write_bytes(raw_receipt_path, _canonical_json(raw_receipt))

        checksum_artifacts = {
            **artifacts,
            "raw_proof_receipt": _artifact_receipt(
                raw_receipt_path, raw_receipt_path.name
            ),
        }
        checksum_lines = [
            f"{row['sha256']}  {row['path']}\n"
            for row in sorted(checksum_artifacts.values(), key=lambda item: item["path"])
        ]
        _write_bytes(staging / "SHA256SUMS.txt", "".join(checksum_lines).encode("ascii"))

        os.replace(staging, proof_dir)
        directory_fd = os.open(proof_dir.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return raw_receipt
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _parse_checksums(path: Path) -> dict[str, str]:
    _require_regular_file(path, "sha256s")
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ProofCollectionError(f"sha256s:not-ascii:{error}") from error
    rows: dict[str, str] = {}
    for index, line in enumerate(lines, 1):
        if len(line) < 67 or line[64:66] != "  ":
            raise ProofCollectionError(f"sha256s:format:line-{index}")
        digest, relative = line[:64], line[66:]
        if not _HEX_SHA256.fullmatch(digest):
            raise ProofCollectionError(f"sha256s:digest:line-{index}")
        parts = Path(relative).parts
        if not relative or Path(relative).is_absolute() or ".." in parts or relative in rows:
            raise ProofCollectionError(f"sha256s:path:line-{index}:{relative}")
        rows[relative] = digest
    if list(rows) != sorted(rows):
        raise ProofCollectionError("sha256s:not-sorted")
    return rows


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise ProofCollectionError(f"git-command-failed:{' '.join(args)}:{stderr}")
    return result


def _repo_relative(path: Path, repo: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError as error:
        raise ProofCollectionError(f"path-outside-repository:{label}:{path}") from error


def _verify_head_file(repo: Path, path: Path, label: str) -> dict[str, Any]:
    _require_regular_file(path, label)
    relative = _repo_relative(path, repo, label)
    _git(repo, "ls-files", "--error-unmatch", "--", relative)
    object_id = _git(repo, "rev-parse", f"HEAD:{relative}").stdout.decode().strip()
    if _git(repo, "cat-file", "-t", object_id).stdout.strip() != b"blob":
        raise ProofCollectionError(f"git-head-not-blob:{label}:{relative}")
    try:
        committed_size = int(_git(repo, "cat-file", "-s", object_id).stdout)
    except ValueError as error:
        raise ProofCollectionError(f"git-blob-size:{label}:{relative}") from error
    process = subprocess.Popen(
        ["git", "cat-file", "blob", object_id],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None:  # pragma: no cover - subprocess contract
        raise ProofCollectionError(f"git-blob-stream-missing:{label}:{relative}")
    digest = hashlib.sha256()
    streamed_size = 0
    for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
        digest.update(chunk)
        streamed_size += len(chunk)
    stderr = process.stderr.read() if process.stderr is not None else b""
    returncode = process.wait()
    if returncode != 0:
        raise ProofCollectionError(
            f"git-blob-read:{label}:{relative}:{stderr.decode(errors='replace').strip()}"
        )
    current_size = path.stat().st_size
    current_sha256 = sha256_file(path)
    if (
        committed_size != streamed_size
        or streamed_size != current_size
        or digest.hexdigest() != current_sha256
    ):
        raise ProofCollectionError(f"git-head-content-mismatch:{label}:{relative}")
    return {"path": relative, "sha256": current_sha256, "bytes": current_size}


def _proof_input_paths(proof_dir: Path) -> dict[str, Path]:
    return {
        "i135_log": proof_dir / "sentinel-i135.log.gz",
        "i135_runs": proof_dir / "i135-runs.tar.gz",
        "validity_receipt": proof_dir / "launch_validity_receipt.json",
        **{
            role: proof_dir / filename
            for role, filename in RUNTIME_EVIDENCE_FILENAMES.items()
        },
        "raw_proof_receipt": proof_dir / "raw_proof_receipt.json",
        **{
            f"decision_{arm}": proof_dir / DECISION_FILENAMES[arm]
            for arm in ARMS
        },
    }


def verify_committed_proof(
    *,
    launch_manifest: Path,
    proof_dir: Path,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Bind the exact analyzer input set to a clean, committed Git ``HEAD``."""

    anchor = (repository_root or proof_dir).resolve()
    repo_text = _git(anchor, "rev-parse", "--show-toplevel").stdout.decode().strip()
    repo = Path(repo_text).resolve()
    if repository_root is not None and repo != repository_root.resolve():
        raise ProofCollectionError(f"repository-root-mismatch:{repo}!={repository_root.resolve()}")
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if status:
        first = status.decode("utf-8", errors="replace").splitlines()[0]
        raise ProofCollectionError(f"repository-not-clean:{first}")
    proof_commit = _git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    if not _HEX_GIT.fullmatch(proof_commit):
        raise ProofCollectionError(f"git-head-malformed:{proof_commit}")

    manifest_row = _verify_head_file(repo, launch_manifest.resolve(), "launch-manifest")
    manifest, manifest_facts = validate_manifest(launch_manifest.resolve())
    if manifest_row["sha256"] != manifest_facts["launch_manifest_sha256"]:
        raise ProofCollectionError("launch-manifest:head-hash-mismatch")

    proof_dir = proof_dir.resolve()
    inputs = _proof_input_paths(proof_dir)
    expected_files = {path.name for path in inputs.values()} | {"SHA256SUMS.txt"}
    actual_files: set[str] = set()
    for item in proof_dir.rglob("*"):
        if item.is_symlink():
            raise ProofCollectionError(f"proof:symlink-forbidden:{item}")
        if item.is_file():
            try:
                actual_files.add(item.relative_to(proof_dir).as_posix())
            except ValueError as error:  # pragma: no cover - resolve/rglob invariant
                raise ProofCollectionError(f"proof:path-resolution:{item}") from error
    if actual_files != expected_files:
        raise ProofCollectionError(
            f"proof:file-set:missing={sorted(expected_files - actual_files)}:"
            f"extra={sorted(actual_files - expected_files)}"
        )

    raw_path = inputs["raw_proof_receipt"]
    raw = _strict_json_bytes(raw_path.read_bytes(), str(raw_path))
    if not isinstance(raw, dict):
        raise ProofCollectionError("raw-proof-receipt:not-object")
    expected_raw_fields = {
        "schema",
        "verdict",
        "launch_manifest_sha256",
        "collector_sha256",
        "collection_gate",
        "completion",
        "source_receipts",
        "artifacts",
        "problem_count",
        "problems",
    }
    if set(raw) != expected_raw_fields:
        raise ProofCollectionError(
            "raw-proof-receipt:field-set:"
            f"missing={sorted(expected_raw_fields - set(raw))}:"
            f"extra={sorted(set(raw) - expected_raw_fields)}"
        )
    for key, expected in {
        "schema": SCHEMA,
        "verdict": "I135_RAW_PROOF_COMPLETE",
        "launch_manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "problem_count": 0,
        "problems": [],
    }.items():
        if raw.get(key) != expected:
            raise ProofCollectionError(f"raw-proof-receipt:{key}:{raw.get(key)!r}")
    if raw.get("collector_sha256") != sha256_file(Path(__file__).resolve()):
        raise ProofCollectionError("raw-proof-receipt:collector-sha256")

    artifact_rows = raw.get("artifacts")
    artifact_roles = set(inputs) - {"raw_proof_receipt"}
    if not isinstance(artifact_rows, dict) or set(artifact_rows) != artifact_roles:
        raise ProofCollectionError("raw-proof-receipt:artifact-role-set")
    for role in sorted(artifact_roles):
        path = inputs[role]
        row = artifact_rows[role]
        if not isinstance(row, dict) or row != _artifact_receipt(path, path.name):
            raise ProofCollectionError(f"raw-proof-receipt:artifact:{role}")

    checksums = _parse_checksums(proof_dir / "SHA256SUMS.txt")
    expected_checksum_paths = {path.name for path in inputs.values()}
    if set(checksums) != expected_checksum_paths:
        raise ProofCollectionError("sha256s:file-set")
    for relative, expected_digest in checksums.items():
        if sha256_file(proof_dir / relative) != expected_digest:
            raise ProofCollectionError(f"sha256s:mismatch:{relative}")

    validity = _strict_json_bytes(inputs["validity_receipt"].read_bytes(), "validity-receipt")
    if not isinstance(validity, dict) or validity.get("schema") != VALIDITY_SCHEMA:
        raise ProofCollectionError("validity-receipt:schema")
    if validity.get("launch_manifest_sha256") != manifest_facts["launch_manifest_sha256"]:
        raise ProofCollectionError("validity-receipt:manifest-sha256")

    source_receipts = raw.get("source_receipts")
    if not isinstance(source_receipts, dict) or set(source_receipts) != {
        "launcher_log",
        "runtime_evidence",
        "decision_blocks",
        "run_tree",
    }:
        raise ProofCollectionError("raw-proof-receipt:source-receipt-set")

    compressed_log_payload = _read_stable_file(inputs["i135_log"], "packaged-log")
    if raw["artifacts"]["i135_log"] != _artifact_receipt_bytes(
        compressed_log_payload, inputs["i135_log"].name
    ):
        raise ProofCollectionError("raw-proof-receipt:stable-artifact:i135_log")
    log_payload = _decompress_gzip_bytes(compressed_log_payload, "i135-log")
    replayed_log = validate_run_log_payload(log_payload, manifest_facts)
    if source_receipts["launcher_log"] != replayed_log:
        raise ProofCollectionError("raw-proof-receipt:launcher-log-source-receipt")

    raw_runtime_receipts = source_receipts["runtime_evidence"]
    if not isinstance(raw_runtime_receipts, dict) or set(raw_runtime_receipts) != set(
        RUNTIME_EVIDENCE_FILENAMES
    ):
        raise ProofCollectionError("raw-proof-receipt:runtime-evidence-source-receipts")
    runtime_payloads: dict[str, bytes] = {}
    runtime_source_ids: dict[str, str] = {}
    for role in RUNTIME_EVIDENCE_FILENAMES:
        payload = _read_stable_file(inputs[role], f"packaged-runtime-evidence:{role}")
        if raw["artifacts"][role] != _artifact_receipt_bytes(payload, inputs[role].name):
            raise ProofCollectionError(f"raw-proof-receipt:stable-artifact:{role}")
        row = raw_runtime_receipts.get(role)
        if not isinstance(row, dict) or not isinstance(row.get("source_id"), str):
            raise ProofCollectionError(f"raw-proof-receipt:runtime-source-id:{role}")
        runtime_payloads[role] = payload
        runtime_source_ids[role] = row["source_id"]
    replayed_runtime_receipts = validate_runtime_evidence_payloads(
        runtime_payloads,
        source_ids=runtime_source_ids,
        manifest=manifest,
        manifest_facts=manifest_facts,
        log_receipt=replayed_log,
    )
    if raw_runtime_receipts != replayed_runtime_receipts:
        raise ProofCollectionError("raw-proof-receipt:runtime-evidence-not-replayed")

    replayed_decisions: dict[str, list[dict[str, Any]]] = {}
    for arm in ARMS:
        role = f"decision_{arm}"
        decision_payload = _read_stable_file(inputs[role], f"packaged-decision:{arm}")
        if raw["artifacts"][role] != _artifact_receipt_bytes(
            decision_payload, inputs[role].name
        ):
            raise ProofCollectionError(f"raw-proof-receipt:stable-artifact:{role}")
        replayed_decisions[arm] = replay_packaged_decision_stream(decision_payload, arm)
    if source_receipts["decision_blocks"] != replayed_decisions:
        raise ProofCollectionError("raw-proof-receipt:decision-source-receipts")

    replayed_runs, stable_runs_artifact = replay_packaged_runs(inputs["i135_runs"])
    if raw["artifacts"]["i135_runs"] != stable_runs_artifact:
        raise ProofCollectionError("raw-proof-receipt:stable-artifact:i135_runs")
    if source_receipts["run_tree"] != replayed_runs:
        raise ProofCollectionError("raw-proof-receipt:run-tree-source-receipt")

    expected_completion = {
        "done_marker": DONE_MARKER,
        "done_marker_count": replayed_log["done_marker_count"],
        "successful_blocks": replayed_log["blocks"],
        "analytic_cells": replayed_log["cells"],
        "decision_blocks": sum(len(rows) for rows in replayed_decisions.values()),
        "decision_resets": sum(
            row["reset_count"] for rows in replayed_decisions.values() for row in rows
        ),
        "run_archive_cells": replayed_runs["cell_count"],
        "run_archive_members": replayed_runs["member_count"],
    }
    if raw.get("completion") != expected_completion:
        raise ProofCollectionError("raw-proof-receipt:completion-not-replayed")

    collection_gate = raw.get("collection_gate")
    if not isinstance(collection_gate, dict) or set(collection_gate) != {
        "minimum_local_free_bytes",
        "observed_local_free_bytes",
        "passed",
    }:
        raise ProofCollectionError("raw-proof-receipt:collection-gate")
    observed_local = collection_gate.get("observed_local_free_bytes")
    if (
        collection_gate.get("minimum_local_free_bytes") != MINIMUM_LOCAL_FREE_BYTES
        or type(observed_local) is not int
        or observed_local < MINIMUM_LOCAL_FREE_BYTES
        or collection_gate.get("passed") is not True
    ):
        raise ProofCollectionError("raw-proof-receipt:collection-gate-values")
    replayed_validity = _build_validity_receipt(
        manifest_facts,
        replayed_log,
        replayed_runtime_receipts,
        observed_local,
    )
    if validity != replayed_validity:
        raise ProofCollectionError("validity-receipt:not-replayed-from-raw-proof")

    # SHA256SUMS is not an analyzer input, but it is part of the exact committed raw proof.
    _verify_head_file(repo, proof_dir / "SHA256SUMS.txt", "sha256s")
    input_rows = {
        role: [_verify_head_file(repo, path, role)] for role, path in sorted(inputs.items())
    }
    return {
        "schema": COMMITTED_SCHEMA,
        "launch_manifest_sha256": manifest_facts["launch_manifest_sha256"],
        "repository_root": str(repo),
        "proof_commit": proof_commit,
        "inputs": input_rows,
        "problem_count": 0,
        "problems": [],
    }


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(description=__doc__)
    out.add_argument("--verify-committed", action="store_true")
    out.add_argument("--launch-manifest", required=True, type=Path)
    out.add_argument("--proof-dir", required=True, type=Path)
    out.add_argument("--run-log", type=Path)
    out.add_argument("--decision-root", type=Path)
    out.add_argument("--runs-root", type=Path)
    out.add_argument(
        "--commit-receipt-out",
        type=Path,
        help="verify mode only; omit to emit the transient receipt on stdout",
    )
    out.add_argument("--repository-root", type=Path, help=argparse.SUPPRESS)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.verify_committed:
            if any((args.run_log, args.decision_root, args.runs_root)):
                raise ProofCollectionError("verify-mode:collection-inputs-forbidden")
            receipt = verify_committed_proof(
                launch_manifest=args.launch_manifest,
                proof_dir=args.proof_dir,
                repository_root=args.repository_root,
            )
            payload = _canonical_json(receipt)
            if args.commit_receipt_out is None:
                sys.stdout.buffer.write(payload)
            else:
                output = args.commit_receipt_out.resolve()
                repo = Path(receipt["repository_root"])
                try:
                    output.relative_to(repo)
                except ValueError:
                    pass
                else:
                    raise ProofCollectionError("commit-receipt-output-must-be-outside-repository")
                _write_bytes(output, payload)
                print(f"I135_COMMITTED_PROOF_OK {output}")
        else:
            if args.commit_receipt_out is not None:
                raise ProofCollectionError("collection-mode:commit-receipt-output-forbidden")
            missing = [
                name
                for name, value in (
                    ("--run-log", args.run_log),
                    ("--decision-root", args.decision_root),
                    ("--runs-root", args.runs_root),
                )
                if value is None
            ]
            if missing:
                raise ProofCollectionError(f"collection-mode:missing:{','.join(missing)}")
            collect_proof(
                run_log=args.run_log,
                decision_root=args.decision_root,
                runs_root=args.runs_root,
                launch_manifest=args.launch_manifest,
                proof_dir=args.proof_dir,
            )
            print(f"I135_RAW_PROOF_COMPLETE {args.proof_dir.resolve()}")
        return 0
    except (OSError, ProofCollectionError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"I135_PROOF_COLLECTION_FAIL {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
