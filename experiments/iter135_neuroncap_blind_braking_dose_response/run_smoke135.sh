#!/bin/bash
# Iteration 135 one-shot, four-dose, nonanalytic live smoke.
#
# This program is intentionally inert until a separately hash-addressed pre-smoke manifest,
# every bound local/remote byte, repository state, image ID, and a single idle L4 all agree.  It
# writes only to the dedicated smoke sibling and never invokes the analytic launcher.  A failed
# attempt retains its lock, staging directory, journal, logs, and partial evidence; there is no
# retry path.

set -euo pipefail

STACK=/opt/sentinel-stack
I135=$STACK/iter135
MANIFEST_SOURCE=$I135/launch_manifest.json
ENV_SOURCE=$I135/env_receipts.json
MISSION_STATE_SOURCE=$I135/MISSION_STATE.json
RUNNER_SOURCE=$I135/run_smoke135.sh
VALIDATOR_SOURCE=$I135/validate_smoke135.py
ANALYTIC_OUTPUT_ROOT=/datasets/nuscenes-full/sentinel-i135-outoutput
SMOKE_OUTPUT_ROOT=/datasets/nuscenes-full/sentinel-i135-smoke-evidence
SMOKE_EPISODE_ROOT=$SMOKE_OUTPUT_ROOT/episodes
RAW_DIR=$SMOKE_OUTPUT_ROOT/raw
STAGING_ROOT=$STACK/UniAD/i135-smoke-staging
MODEL_STAGING_ROOT=/model/i135-smoke-staging
SCHEDULE_TARGET=$STACK/UniAD/dose_schedules.json
LOCK=/var/lib/sentinel/i135-smoke.lock
CONTAINER_CONTROL_ROOT=$SMOKE_OUTPUT_ROOT/container-control
CONTAINER_CONTROL_ROOT_ID=
EXPECTED_MANIFEST_SHA=${SENTINEL_SMOKE_INPUT_MANIFEST_SHA256:-}
CAPTURE_TIMEOUT_SECONDS=180
DOSE_TIMEOUT_SECONDS=1800
EXPECTED_BLIND_PATCHED_SERVER_SHA256=b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf
EXPECTED_UNIAD_IMAGE_ID=sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb
EXPECTED_NEURAD_IMAGE_ID=sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c
EXPECTED_NCAP_IMAGE_ID=sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce
RUNNER_SHA=
RUNNER_ID=
SMOKE_LOCK_ID=
SMOKE_STARTED=0
SCHEDULE_TARGET_ID=
STAGING_ROOT_ID=

fail_preflight() {
  echo "I135_SMOKE_PREFLIGHT_FAIL $*" >&2
  exit 1
}

for REQUIRED_COMMAND in awk bash cp dirname docker env findmnt git grep mkdir mv \
  nvidia-smi ps python3 readlink rm sed sha256sum sleep stat timeout touch tr wc; do
  command -v "$REQUIRED_COMMAND" >/dev/null 2>&1 \
    || fail_preflight "command-missing:$REQUIRED_COMMAND"
done

if [[ ! $EXPECTED_MANIFEST_SHA =~ ^[0-9a-f]{64}$ ]]; then
  fail_preflight "independent-manifest-sha256-missing-or-malformed"
fi
for path in "$MANIFEST_SOURCE" "$ENV_SOURCE" "$MISSION_STATE_SOURCE" \
  "$RUNNER_SOURCE" "$VALIDATOR_SOURCE"; do
  [ -f "$path" ] && [ ! -L "$path" ] || fail_preflight "nonregular-input:$path"
done
if [ "$(sha256sum "$MANIFEST_SOURCE" | awk '{print $1}')" != "$EXPECTED_MANIFEST_SHA" ]; then
  fail_preflight "independent-manifest-sha256-mismatch"
fi

# Reject copied, symlinked, replaced, or path-aliased invocations before any mutation.  The
# executing source, argv[0], canonical deployment path, and manifest receipt must all name the
# same stable physical inode and bytes.
RUNNER_BINDING=$(python3 - "$RUNNER_SOURCE" "$0" "${BASH_SOURCE[0]}" \
  "$MANIFEST_SOURCE" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

canonical, argv0, bash_source, manifest_path = map(Path, sys.argv[1:])
expected = Path("/opt/sentinel-stack/iter135/run_smoke135.sh")
if canonical != expected or argv0 != expected or bash_source != expected:
    raise SystemExit(
        f"runner path alias/copy: canonical={canonical} argv0={argv0} source={bash_source}"
    )
if any(path.is_symlink() or not path.is_file() for path in (canonical, argv0, bash_source)):
    raise SystemExit("runner is not a physical regular file")
if any(path.resolve(strict=True) != expected for path in (canonical, argv0, bash_source)):
    raise SystemExit("runner realpath drift")

descriptor = os.open(canonical, os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0))
try:
    before = os.fstat(descriptor)
    path_before = canonical.stat()
    digest = hashlib.sha256()
    byte_count = 0
    while True:
        chunk = os.read(descriptor, 1 << 20)
        if not chunk:
            break
        digest.update(chunk)
        byte_count += len(chunk)
    after = os.fstat(descriptor)
finally:
    os.close(descriptor)
path_after = canonical.stat()
identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
if (
    identity(before) != identity(after)
    or identity(before) != identity(path_before)
    or identity(after) != identity(path_after)
    or byte_count != before.st_size
):
    raise SystemExit("runner changed while being hash-bound")
for path in (argv0, bash_source):
    row = path.stat()
    if (row.st_dev, row.st_ino) != (before.st_dev, before.st_ino):
        raise SystemExit("runner inode drift")

manifest = json.loads(manifest_path.read_bytes())
receipt = manifest.get("hash_bound_files", {}).get("run_smoke135.sh")
actual = digest.hexdigest()
if (
    not isinstance(receipt, dict)
    or set(receipt) != {"source_path", "sha256", "bytes"}
    or receipt.get("source_path")
    != "experiments/iter135_neuroncap_blind_braking_dose_response/run_smoke135.sh"
    or receipt.get("sha256") != actual
    or receipt.get("bytes") != byte_count
):
    raise SystemExit("runner manifest receipt drift")
print(actual, f"{before.st_dev}:{before.st_ino}")
PY
) || fail_preflight "canonical-runner-binding"
read -r RUNNER_SHA RUNNER_ID <<<"$RUNNER_BINDING"
if ! [[ $RUNNER_SHA =~ ^[0-9a-f]{64}$ ]] || ! [[ $RUNNER_ID =~ ^[0-9]+:[0-9]+$ ]]; then
  fail_preflight "canonical-runner-binding-output"
fi

# The only permitted incomplete pre-smoke state is the mechanically missing G5 receipt itself.
# The same pass also rehashes every bound local and execution-host file, rechecks repository dirty
# state, verifies all three image IDs, and emits the four canonical run-zero targets as TSV.
TARGET_PLAN=$(python3 - "$MANIFEST_SOURCE" "$ENV_SOURCE" "$MISSION_STATE_SOURCE" \
  "$I135" "$ANALYTIC_OUTPUT_ROOT" "$SMOKE_OUTPUT_ROOT" <<'PY'
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

(
    manifest_path,
    environment_path,
    mission_state_path,
    experiment_path,
    analytic_output_root,
    smoke_output_root,
) = map(Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text())
environment = json.loads(environment_path.read_text())
mission_state = json.loads(mission_state_path.read_text())
problems = []


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


if manifest.get("schema") != "iter135.launch_manifest.v2":
    problems.append("manifest-schema")
if manifest.get("verdict") != "I135_TOOLING_MANIFEST_INCOMPLETE":
    problems.append("manifest-verdict")
if manifest.get("launch_authorized") is not False:
    problems.append("manifest-already-analytic")
if manifest.get("missing_artifacts") != ["smoke-evidence/smoke_receipt.json"]:
    problems.append("manifest-missing-set")
if manifest.get("problem_count") != 1 or manifest.get("problems") != ["smoke:receipt-missing"]:
    problems.append("manifest-problem-set")
expected_manifest_fields = {
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
if set(manifest) != expected_manifest_fields:
    problems.append("manifest-field-set")
if manifest.get("mission_phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED":
    problems.append("manifest-mission-phase")
if manifest.get("planned_blocks") != 120 or manifest.get("planned_episodes") != 2400:
    problems.append("manifest-analytic-plan-cardinality")
expected_gates = {
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
if manifest.get("gates") != expected_gates:
    problems.append("manifest-pre-smoke-gate-contract")

expected_authorized_actions = [
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
expected_forbidden_actions = [
    (
        "run any iteration-135 analytic episode before smoke evidence and the final launch manifest "
        "are committed green"
    ),
    "remove or bypass the permanent analytic launch lock",
    (
        "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies "
        "after evidence"
    ),
    "place any iteration-135 analytic output on the remote root filesystem",
]
expected_state_fields = {
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
if set(mission_state) != expected_state_fields:
    problems.append("mission-state-field-set")
expected_workspace_boundary = {
    "isolated_from": "/Users/danielwahnich/workspace/aweb",
    "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
    "cross_workspace_access_requires_explicit_operator_request": True,
}
expected_program = {
    "iteration": 135,
    "name": "semantics-free placebo dose-response causal closure",
    "phase": "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
    "authorized_actions": expected_authorized_actions,
    "forbidden_actions": expected_forbidden_actions,
}
if (
    mission_state.get("schema") != "sentinel.mission_state.v1"
    or mission_state.get("canonical_repository") != "/Users/danielwahnich/workspace/sentinel"
    or mission_state.get("workspace_boundary") != expected_workspace_boundary
    or mission_state.get("trunk") != "master"
    or mission_state.get("current_completed_iteration") != 134
    or mission_state.get("current_result")
    != "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
    or mission_state.get("current_verdict") != "PLACEBO_HARM_OR_NULL"
    or mission_state.get("run_state") != "IDLE"
    or mission_state.get("active_hypothesis")
    != "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
    or mission_state.get("next_program") != expected_program
):
    problems.append("mission-state-authority-contract")
expected_state_storage = {
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
if mission_state.get("storage_gate") != expected_state_storage:
    problems.append("mission-state-storage-contract")
mission_receipt = manifest.get("mission_state")
mission_payload = mission_state_path.read_bytes()
if (
    not isinstance(mission_receipt, dict)
    or set(mission_receipt) != {"source_path", "sha256", "bytes"}
    or mission_receipt.get("source_path") != "MISSION_STATE.json"
    or mission_receipt.get("sha256") != hashlib.sha256(mission_payload).hexdigest()
    or mission_receipt.get("bytes") != len(mission_payload)
):
    problems.append("mission-state-receipt-drift")

bound = manifest.get("hash_bound_files")
required = {
    "dose_schedules.json",
    "server_patch_blind_dose.py",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "env_receipts.json",
    "tooling_verification_receipt.json",
}
if not isinstance(bound, dict) or not required.issubset(bound):
    problems.append("manifest-required-tooling-set")
    bound = {}
for relative, receipt in sorted(bound.items()):
    path = experiment_path / relative
    try:
        path.resolve().relative_to(experiment_path.resolve())
    except ValueError:
        problems.append(f"bound-path-escape:{relative}")
        continue
    if path.is_symlink() or not path.is_file() or not isinstance(receipt, dict):
        problems.append(f"bound-file:{relative}:nonregular")
        continue
    actual = digest(path)
    if receipt.get("sha256") != actual or receipt.get("bytes") != path.stat().st_size:
        problems.append(f"bound-file:{relative}:drift")

environment_bound = bound.get("env_receipts.json")
if not isinstance(environment_bound, dict) or environment_bound.get("sha256") != digest(environment_path):
    problems.append("environment-bound-hash")
tooling_path = experiment_path / "tooling_verification_receipt.json"
tooling_bound = bound.get("tooling_verification_receipt.json")
try:
    tooling = json.loads(tooling_path.read_bytes())
except (OSError, json.JSONDecodeError) as error:
    problems.append(f"tooling-receipt-read:{type(error).__name__}")
    tooling = {}
if (
    not isinstance(tooling_bound, dict)
    or tooling_bound != manifest.get("tooling_verification_receipt")
    or tooling_bound.get("sha256") != digest(tooling_path)
    or tooling_bound.get("bytes") != tooling_path.stat().st_size
):
    problems.append("tooling-receipt-binding")
tooling_payload = dict(tooling)
claimed_tooling_payload_sha = tooling_payload.pop("receipt_payload_sha256", None)
actual_tooling_payload_sha = hashlib.sha256(
    json.dumps(tooling_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
).hexdigest()
if (
    tooling.get("schema") != "iter135.tooling_verification.v2"
    or tooling.get("verdict") != "I135_TOOLING_VERIFICATION_OK"
    or tooling.get("problem_count") != 0
    or tooling.get("problems") != []
    or claimed_tooling_payload_sha != actual_tooling_payload_sha
):
    problems.append("tooling-receipt-contract")
if environment.get("schema") != "iter135.environment_receipts.v2":
    problems.append("environment-schema")
if environment.get("verdict") != "I135_ENVIRONMENT_PREFLIGHT_OK":
    problems.append("environment-verdict")
if environment.get("problem_count") != 0 or environment.get("problems") != []:
    problems.append("environment-problem-metadata")
expected_environment_fields = {
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
if set(environment) != expected_environment_fields:
    problems.append("environment-field-set")
if environment.get("host") != "sentinel-gpu" or socket.gethostname() != "sentinel-gpu":
    problems.append(f"environment-live-host:{socket.gethostname()}")
expected_gpu = {
    "model": "NVIDIA L4",
    "count": 1,
    "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
    "driver_version": "580.159.03",
    "memory_total_mib": 23034,
}
if environment.get("gpu") != expected_gpu:
    problems.append("environment-frozen-gpu")
expected_box = {
    "idle": True,
    "all_containers": 0,
    "gpu_compute_processes": 0,
    "known_evaluation_processes": 0,
}
if environment.get("box") != expected_box:
    problems.append("environment-box-contract")

storage = environment.get("storage")
expected_storage_identity = {
    "filesystem_path": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "filesystem_realpath": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "filesystem_is_symlink": False,
    "filesystem_empty": True,
    "mount_target": "/datasets/nuscenes-full",
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}
expected_storage_fields = {
    "remote_output_free_bytes",
    "projected_output_bytes",
    "minimum_reserve_bytes",
    "local_free_bytes",
    "remote_output_free_gib",
    "projected_output_gib",
    "minimum_reserve_gib",
    "local_free_gib",
    *expected_storage_identity,
}
if not isinstance(storage, dict) or set(storage) != expected_storage_fields:
    problems.append("environment-storage-field-set")
    storage = {}
for field, expected in expected_storage_identity.items():
    if storage.get(field) != expected or (
        isinstance(expected, bool) and type(storage.get(field)) is not bool
    ):
        problems.append(f"environment-storage-identity:{field}")
remote_free_bytes = storage.get("remote_output_free_bytes")
projected_bytes = storage.get("projected_output_bytes")
reserve_bytes = storage.get("minimum_reserve_bytes")
local_free_bytes = storage.get("local_free_bytes")
if (
    type(remote_free_bytes) is not int
    or type(projected_bytes) is not int
    or type(reserve_bytes) is not int
    or type(local_free_bytes) is not int
    or remote_free_bytes < 100 * 1024**3
    or projected_bytes != 72_380_432_384
    or reserve_bytes != 25 * 1024**3
    or local_free_bytes < 15 * 1024**3
    or remote_free_bytes - projected_bytes < reserve_bytes
    or storage.get("remote_output_free_gib") != remote_free_bytes / 1024**3
    or storage.get("projected_output_gib") != projected_bytes / 1024**3
    or storage.get("minimum_reserve_gib") != reserve_bytes / 1024**3
    or storage.get("local_free_gib") != local_free_bytes / 1024**3
):
    problems.append("environment-storage-values")

devices = environment.get("storage_devices")
if (
    not isinstance(devices, dict)
    or set(devices) != {"filesystem_st_dev", "mount_st_dev", "root_st_dev"}
    or any(type(devices.get(field)) is not int for field in devices)
    or devices["filesystem_st_dev"] != devices["mount_st_dev"]
    or devices["filesystem_st_dev"] == devices["root_st_dev"]
):
    problems.append("environment-storage-device-contract")
    devices = {}
if (
    analytic_output_root != Path("/datasets/nuscenes-full/sentinel-i135-outoutput")
    or smoke_output_root != Path("/datasets/nuscenes-full/sentinel-i135-smoke-evidence")
    or analytic_output_root.is_symlink()
    or not analytic_output_root.is_dir()
    or analytic_output_root.resolve(strict=True) != analytic_output_root
    or any(analytic_output_root.iterdir())
):
    problems.append("live-storage-output-root-contract")
else:
    mount = Path("/datasets/nuscenes-full")
    live_devices = {
        "filesystem_st_dev": analytic_output_root.stat().st_dev,
        "mount_st_dev": mount.stat().st_dev,
        "root_st_dev": Path("/").stat().st_dev,
    }
    if live_devices != devices:
        problems.append(f"live-storage-device-drift:{live_devices}!={devices}")
    if smoke_output_root.parent != mount or smoke_output_root.exists() or smoke_output_root.is_symlink():
        problems.append("live-smoke-output-root-contract")
    try:
        mount_row = subprocess.check_output(
            ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(analytic_output_root)],
            text=True,
        ).split()
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"live-storage-findmnt:{type(error).__name__}")
    else:
        if mount_row != [
            "/dev/nvme0n2",
            "ext4",
            "9a98277e-b21f-4ffc-8f14-3f2235b43103",
        ]:
            problems.append(f"live-storage-mount-identity:{mount_row}")
    live_free = shutil.disk_usage(analytic_output_root).free
    if live_free < 100 * 1024**3 or live_free - 72_380_432_384 < 25 * 1024**3:
        problems.append(f"live-storage-free:{live_free}")

dataset = environment.get("dataset")
manifest_tool_path = experiment_path / "make_launch_manifest.py"
namespace = {}
try:
    manifest_tool_payload = manifest_tool_path.read_bytes()
    manifest_tool_receipt = bound.get("make_launch_manifest.py")
    if (
        manifest_tool_path.is_symlink()
        or not manifest_tool_path.is_file()
        or manifest_tool_path.resolve(strict=True) != manifest_tool_path
        or not isinstance(manifest_tool_receipt, dict)
        or manifest_tool_receipt.get("sha256")
        != hashlib.sha256(manifest_tool_payload).hexdigest()
        or manifest_tool_receipt.get("bytes") != len(manifest_tool_payload)
    ):
        raise RuntimeError("manifest tool binding drift")
    namespace = {
        "__file__": str(manifest_tool_path),
        "__name__": "iter135_smoke_dataset_contract",
    }
    exec(compile(manifest_tool_payload, str(manifest_tool_path), "exec"), namespace)
    dataset_problems = namespace["validate_dataset_receipt"](
        dataset if isinstance(dataset, dict) else None
    )
except (OSError, RuntimeError, KeyError, TypeError) as error:
    problems.append(f"dataset-validator-load:{type(error).__name__}:{error}")
    dataset_problems = []
problems.extend(f"dataset-contract:{item}" for item in dataset_problems)
if (
    namespace.get("SCHEMA") != "iter135.launch_manifest.v2"
    or namespace.get("EXPECTED_ENV_SCHEMA") != "iter135.environment_receipts.v2"
    or namespace.get("EXPECTED_DATASET_SCHEMA") != "iter135.nuscenes_dataset_receipt.v1"
    or namespace.get("EXPECTED_DATASET_CONTRACT_SHA256")
    != "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
):
    problems.append("dataset-validator-frozen-constant-drift")
if manifest.get("dataset_receipt") != dataset:
    problems.append("manifest-dataset-receipt-drift")
if isinstance(dataset, dict):
    identity = dataset.get("identity")
    expected_dataset_paths = {
        "dataset_root": Path("/datasets/nuscenes-full"),
        "archive_root": Path("/datasets/nuscenes-full/archives"),
        "metadata_root": Path("/datasets/nuscenes-full/v1.0-trainval"),
        "map_root": Path("/datasets/nuscenes-full/maps"),
    }
    if not isinstance(identity, dict):
        problems.append("live-dataset-identity")
        identity = {}
    for field, path in expected_dataset_paths.items():
        if (
            identity.get(field) != str(path)
            or identity.get(field.replace("_root", "_realpath")) != str(path)
            or identity.get(field.replace("_root", "_is_symlink")) is not False
            or path.is_symlink()
            or not path.is_dir()
            or path.resolve(strict=True) != path
        ):
            problems.append(f"live-dataset-path:{field}")
    dataset_root = expected_dataset_paths["dataset_root"]
    live_dataset_devices = {
        "dataset_st_dev": dataset_root.stat().st_dev,
        "mount_st_dev": dataset_root.stat().st_dev,
        "root_st_dev": Path("/").stat().st_dev,
    }
    if any(identity.get(field) != value for field, value in live_dataset_devices.items()):
        problems.append(f"live-dataset-device-drift:{live_dataset_devices}")
    try:
        dataset_mount_row = subprocess.check_output(
            ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(dataset_root)],
            text=True,
        ).split()
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"live-dataset-findmnt:{type(error).__name__}")
    else:
        if dataset_mount_row != [
            "/dev/nvme0n2",
            "ext4",
            "9a98277e-b21f-4ffc-8f14-3f2235b43103",
        ]:
            problems.append(f"live-dataset-mount-identity:{dataset_mount_row}")
    for section, rehash in (("archives", False), ("metadata_json", True), ("map_anchors", True)):
        rows = dataset.get(section)
        if not isinstance(rows, dict):
            problems.append(f"live-dataset-section:{section}")
            continue
        for name, receipt in sorted(rows.items()):
            if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256", "bytes"}:
                problems.append(f"live-dataset-receipt:{section}:{name}")
                continue
            path = Path(str(receipt.get("path", "")))
            if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
                problems.append(f"live-dataset-file:{section}:{name}")
                continue
            if path.stat().st_size != receipt.get("bytes"):
                problems.append(f"live-dataset-bytes:{section}:{name}")
            if rehash and digest(path) != receipt.get("sha256"):
                problems.append(f"live-dataset-sha256:{section}:{name}")

manifest_environment = manifest.get("environment_receipts")
expected_manifest_environment = {
    **environment,
    "docker_image_ids": {
        name: row.get("image_id")
        for name, row in environment.get("container_images", {}).items()
        if isinstance(name, str) and isinstance(row, dict)
    },
}
if manifest_environment != expected_manifest_environment:
    problems.append("manifest-environment-receipt-drift")
if manifest.get("container_images") != environment.get("container_images"):
    problems.append("manifest-container-images-drift")

manifest_storage = manifest.get("storage_gate")
expected_manifest_storage_fields = {
    "minimum_remote_free_gib",
    "minimum_reserve_gib",
    "minimum_local_free_gib",
    "minimum_remote_free_bytes",
    "minimum_reserve_bytes",
    "minimum_local_free_bytes",
    "filesystem_path",
    "projected_output_gib",
    "projected_output_bytes",
    "observed_remote_free_gib",
    "observed_remote_free_bytes",
    "observed_local_free_gib",
    "observed_local_free_bytes",
    "filesystem_realpath",
    "filesystem_is_symlink",
    "filesystem_empty",
    "mount_target",
    "mount_source",
    "mount_fstype",
    "mount_uuid",
}
if not isinstance(manifest_storage, dict) or set(manifest_storage) != expected_manifest_storage_fields:
    problems.append("manifest-storage-field-set")
    manifest_storage = {}
expected_manifest_storage_values = {
    "minimum_remote_free_gib": 100,
    "minimum_reserve_gib": 25,
    "minimum_local_free_gib": 15,
    "minimum_remote_free_bytes": 100 * 1024**3,
    "minimum_reserve_bytes": 25 * 1024**3,
    "minimum_local_free_bytes": 15 * 1024**3,
    "projected_output_bytes": 72_380_432_384,
    "filesystem_path": expected_storage_identity["filesystem_path"],
    "filesystem_realpath": expected_storage_identity["filesystem_realpath"],
    "filesystem_is_symlink": False,
    "filesystem_empty": True,
    "mount_target": expected_storage_identity["mount_target"],
    "mount_source": expected_storage_identity["mount_source"],
    "mount_fstype": expected_storage_identity["mount_fstype"],
    "mount_uuid": expected_storage_identity["mount_uuid"],
    "observed_remote_free_bytes": remote_free_bytes,
    "observed_local_free_bytes": local_free_bytes,
    "observed_remote_free_gib": storage.get("remote_output_free_gib"),
    "observed_local_free_gib": storage.get("local_free_gib"),
    "projected_output_gib": storage.get("projected_output_gib"),
}
if any(manifest_storage.get(key) != value for key, value in expected_manifest_storage_values.items()):
    problems.append("manifest-storage-contract")

remote_files = environment.get("remote_files")
if not isinstance(remote_files, dict) or not remote_files:
    problems.append("environment-remote-files")
    remote_files = {}
for role, receipt in sorted(remote_files.items()):
    if not isinstance(receipt, dict):
        problems.append(f"remote:{role}:receipt")
        continue
    path = Path(str(receipt.get("path", "")))
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        problems.append(f"remote:{role}:nonregular:{path}")
        continue
    if receipt.get("bytes") != path.stat().st_size or receipt.get("sha256") != digest(path):
        problems.append(f"remote:{role}:drift")

repositories = environment.get("repositories")
if not isinstance(repositories, dict) or not repositories:
    problems.append("environment-repositories")
    repositories = {}
if set(repositories) != {"uniad", "neuroncap", "neurad"}:
    problems.append("environment-repository-set")
for repository_id, receipt in sorted(repositories.items()):
    if not isinstance(receipt, dict):
        problems.append(f"repository:{repository_id}:receipt")
        continue
    path = Path(str(receipt.get("path", "")))
    if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
        problems.append(f"repository:{repository_id}:missing")
        continue
    def git_text(*args):
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={path}", "-C", str(path), *args], text=True
        ).strip()
    def git_paths(*args):
        payload = subprocess.check_output(
            ["git", "-c", f"safe.directory={path}", "-C", str(path), *args, "-z"]
        )
        return sorted(
            item.decode("utf-8", errors="strict")
            for item in payload.split(b"\0")
            if item
        )
    try:
        head = git_text("rev-parse", "HEAD")
        staged = git_paths("diff", "--cached", "--name-only")
        dirty = git_paths("diff", "--name-only")
        untracked = git_paths("ls-files", "--others", "--exclude-standard")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        problems.append(f"repository:{repository_id}:git-query")
        continue
    required_untracked = sorted(receipt.get("required_untracked_paths", []))
    frozen_required_untracked = {
        "uniad": [],
        "neuroncap": [],
        "neurad": ["Dockerfile.bak"],
    }.get(repository_id)
    if head != receipt.get("head"):
        problems.append(f"repository:{repository_id}:head")
    if staged != sorted(receipt.get("staged_paths", [])):
        problems.append(f"repository:{repository_id}:staged")
    if dirty != sorted(receipt.get("dirty_tracked_paths", [])):
        problems.append(f"repository:{repository_id}:dirty")
    if required_untracked != frozen_required_untracked:
        problems.append(f"repository:{repository_id}:required-untracked-policy")
    if repository_id == "neuroncap":
        unexpected_untracked = [
            item for item in untracked if item != "outoutput" and not item.startswith("outoutput/")
        ]
        if unexpected_untracked:
            problems.append(
                f"repository:{repository_id}:unexpected-untracked:{unexpected_untracked}"
            )
    elif untracked != required_untracked:
        problems.append(
            f"repository:{repository_id}:unexpected-untracked:"
            f"expected={required_untracked}:actual={untracked}"
        )

images = environment.get("container_images")
expected_images = {
    "ncap:latest": "sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce",
    "neurad:latest": "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c",
    "uniad:latest": "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb",
}
if not isinstance(images, dict) or set(images) != set(expected_images):
    problems.append("environment-container-images")
    images = {}
for name, expected_id in sorted(expected_images.items()):
    receipt = images.get(name)
    if not isinstance(receipt, dict):
        problems.append(f"image:{name}:receipt")
        continue
    if receipt.get("image_id") != expected_id:
        problems.append(f"image:{name}:frozen-id")
        continue
    try:
        tag_actual = subprocess.check_output(
            ["docker", "image", "inspect", name, "--format", "{{.Id}}"], text=True
        ).strip()
        id_actual = subprocess.check_output(
            ["docker", "image", "inspect", expected_id, "--format", "{{.Id}}"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        problems.append(f"image:{name}:missing")
        continue
    if tag_actual != expected_id or id_actual != expected_id:
        problems.append(f"image:{name}:drift")

schedule = json.loads((experiment_path / "dose_schedules.json").read_text())
doses = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
schedules = schedule.get("schedules")
if not isinstance(schedules, dict) or set(schedules) != set(doses):
    problems.append("schedule-dose-set")
    schedules = {}
targets = []
for dose in doses:
    rows = schedules.get(dose)
    candidates = []
    if isinstance(rows, dict):
        candidates = sorted(
            (key, row)
            for key, row in rows.items()
            if isinstance(key, str)
            and isinstance(row, dict)
            and key.endswith("/0")
            and isinstance(row.get("brake_frames"), list)
            and row["brake_frames"]
        )
    if not candidates:
        problems.append(f"schedule:{dose}:canonical-run-zero")
        continue
    target, row = candidates[0]
    scenario_class, sequence, run_text = target.split("/")
    if (
        row.get("dose_id") != dose
        or row.get("target_class") != scenario_class
        or row.get("target_seq") != sequence
        or row.get("target_run") != int(run_text)
    ):
        problems.append(f"schedule:{dose}:identity")
    targets.append((dose, f"{dose}/{target}", scenario_class, sequence))

if problems:
    print("I135_SMOKE_PROVENANCE_FAIL", *problems, sep="\n - ", file=sys.stderr)
    raise SystemExit(1)
for row in targets:
    print("\t".join(row))
PY
) || fail_preflight "provenance-or-environment"
if [ "$(printf '%s\n' "$TARGET_PLAN" | sed '/^$/d' | wc -l | tr -d ' ')" != "4" ]; then
  fail_preflight "canonical-target-count"
fi

# No mutation happens above this line.  Live single-tenant gates are the final read-only checks.
if ! ALL_CONTAINER_IDS=$(docker ps -aq --no-trunc); then
  fail_preflight "docker-container-probe-failed"
fi
if [ -n "$ALL_CONTAINER_IDS" ]; then
  fail_preflight "docker-container-present"
fi
python3 - "$ENV_SOURCE" <<'PY' || fail_preflight "gpu-identity-drift"
import csv
import json
import subprocess
import sys

environment = json.load(open(sys.argv[1]))
expected = environment.get("gpu")
fields = {"model", "count", "uuid", "driver_version", "memory_total_mib"}
if not isinstance(expected, dict) or set(expected) != fields:
    raise SystemExit("environment GPU identity is malformed")
if (
    expected.get("model") != "NVIDIA L4"
    or expected.get("count") != 1
    or not isinstance(expected.get("uuid"), str)
    or not expected["uuid"].startswith("GPU-")
    or not isinstance(expected.get("driver_version"), str)
    or not expected["driver_version"]
    or type(expected.get("memory_total_mib")) is not int
    or expected["memory_total_mib"] <= 0
):
    raise SystemExit("environment GPU identity values are invalid")
output = subprocess.check_output(
    [
        "nvidia-smi",
        "--query-gpu=name,uuid,driver_version,memory.total",
        "--format=csv,noheader,nounits",
    ],
    text=True,
)
rows = list(csv.reader(output.splitlines(), skipinitialspace=True))
if len(rows) != 1 or len(rows[0]) != 4:
    raise SystemExit(f"expected exactly one GPU identity row, observed {rows!r}")
name, uuid, driver, memory = (item.strip() for item in rows[0])
observed = {
    "model": name,
    "count": 1,
    "uuid": uuid,
    "driver_version": driver,
    "memory_total_mib": int(memory),
}
if observed != expected:
    raise SystemExit(f"live GPU identity drift: {observed!r} != {expected!r}")
PY
if ! GPU_COMPUTE_PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader); then
  fail_preflight "gpu-compute-process-probe-failed"
fi
if [[ $GPU_COMPUTE_PIDS =~ [^[:space:]] ]]; then
  fail_preflight "gpu-compute-process-present"
fi
python3 - <<'PY' || fail_preflight "evaluation-process-present"
import os
import re
import subprocess

pattern = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
matches = []
for raw in subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines():
    pid_text, _, command = raw.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid in {os.getpid(), os.getppid()}:
        continue
    if pattern.search(command):
        matches.append(f"{pid}:{command}")
if matches:
    print(*matches, sep="\n")
    raise SystemExit(1)
PY
if [ -e "$LOCK" ] || [ -L "$LOCK" ] || [ -e "$SMOKE_OUTPUT_ROOT" ] \
  || [ -L "$SMOKE_OUTPUT_ROOT" ] || [ -e "$STAGING_ROOT" ] || [ -L "$STAGING_ROOT" ] \
  || [ -e "$SCHEDULE_TARGET" ] || [ -L "$SCHEDULE_TARGET" ]; then
  fail_preflight "one-shot-path-exists"
fi
if [ "$(dirname "$SMOKE_OUTPUT_ROOT")" != "$(dirname "$ANALYTIC_OUTPUT_ROOT")" ] \
  || [ "$SMOKE_OUTPUT_ROOT" = "$ANALYTIC_OUTPUT_ROOT" ]; then
  fail_preflight "smoke-output-not-dedicated-sibling"
fi

# Crossing this point is the explicit one-shot smoke launch.  The fixed lock and output paths are
# deliberately retained on both success and failure so a second attempt requires a disclosed,
# manual forensic action.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0=$STACK/UniAD
SMOKE_LOCK_ID=$(python3 - "$LOCK" "$EXPECTED_MANIFEST_SHA" "$RUNNER_SHA" \
  "$MISSION_STATE_SOURCE" "$MANIFEST_SOURCE" "$RUNNER_SOURCE" "$$" <<'PY'
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

lock = Path(sys.argv[1])
manifest_sha256, runner_sha256 = sys.argv[2:4]
mission_state_path = Path(sys.argv[4])
manifest_path = Path(sys.argv[5])
runner_path = Path(sys.argv[6])
pid = int(sys.argv[7])
if (
    lock != Path("/var/lib/sentinel/i135-smoke.lock")
    or not lock.parent.is_dir()
    or lock.parent.is_symlink()
    or lock.parent.resolve(strict=True) != lock.parent
    or lock.exists()
    or lock.is_symlink()
    or any(
        len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
        for value in (manifest_sha256, runner_sha256)
    )
    or mission_state_path.is_symlink()
    or not mission_state_path.is_file()
    or mission_state_path.resolve(strict=True) != mission_state_path
    or manifest_path.is_symlink()
    or not manifest_path.is_file()
    or manifest_path.resolve(strict=True) != manifest_path
    or runner_path != Path("/opt/sentinel-stack/iter135/run_smoke135.sh")
    or runner_path.is_symlink()
    or not runner_path.is_file()
    or runner_path.resolve(strict=True) != runner_path
):
    raise SystemExit("smoke lock publication contract drift")


def stable_payload(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat()
    identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns)
    payload = b"".join(chunks)
    if identity(before) != identity(after) or identity(after) != identity(path_after) \
        or len(payload) != before.st_size:
        raise SystemExit(f"smoke lock input changed while read: {path}")
    return payload


mission_state_payload = stable_payload(mission_state_path)
manifest_payload = stable_payload(manifest_path)
runner_payload = stable_payload(runner_path)
manifest = json.loads(manifest_payload)
mission_receipt = manifest.get("mission_state")
runner_receipt = manifest.get("hash_bound_files", {}).get("run_smoke135.sh")
if (
    hashlib.sha256(manifest_payload).hexdigest() != manifest_sha256
    or hashlib.sha256(runner_payload).hexdigest() != runner_sha256
    or not isinstance(mission_receipt, dict)
    or mission_receipt.get("sha256") != hashlib.sha256(mission_state_payload).hexdigest()
    or mission_receipt.get("bytes") != len(mission_state_payload)
    or not isinstance(runner_receipt, dict)
    or runner_receipt.get("sha256") != runner_sha256
    or runner_receipt.get("bytes") != len(runner_payload)
):
    raise SystemExit("smoke lock provenance recheck drift")
payload = {
    "schema": "iter135.smoke_lock.v1",
    "manifest_sha256": manifest_sha256,
    "runner_sha256": runner_sha256,
    "mission_state_sha256": hashlib.sha256(mission_state_payload).hexdigest(),
    "pid": pid,
    "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "mode": "nonanalytic_g5_smoke",
    "nonanalytic": True,
    "analytic_episode_count": 0,
    "dose_invocation_count": 4,
    "retry_policy": "one_shot_no_retry_lock_retained",
    "smoke_output_root": "/datasets/nuscenes-full/sentinel-i135-smoke-evidence",
}
descriptor, temporary_name = tempfile.mkstemp(
    prefix=f".{lock.name}.", suffix=".tmp", dir=lock.parent
)
temporary = Path(temporary_name)
temporary_stat = os.fstat(descriptor)
temporary_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
published = False
try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o444)
    observed_temporary = temporary.stat()
    if (observed_temporary.st_dev, observed_temporary.st_ino) != temporary_identity:
        raise SystemExit("smoke lock temporary identity drift")
    os.link(temporary, lock, follow_symlinks=False)
    published = True
    temporary.unlink()
    parent_descriptor = os.open(lock.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)
    if (
        lock.is_symlink()
        or not lock.is_file()
        or lock.resolve(strict=True) != lock
        or (lock.stat().st_mode & 0o777) != 0o444
        or json.loads(lock.read_text()) != payload
    ):
        raise SystemExit("smoke lock receipt verification failed")
    row = lock.stat()
    print(f"{row.st_dev}:{row.st_ino}")
except BaseException:
    if not published and temporary.exists() and not temporary.is_symlink():
        observed = temporary.stat()
        if (observed.st_dev, observed.st_ino) == temporary_identity:
            temporary.unlink()
    # Once the durable one-shot path is published it is never removed automatically, even when a
    # later verification step fails.  That is the no-retry safety boundary.
    raise
PY
) || fail_preflight "persistent-smoke-lock-publication"
if ! [[ $SMOKE_LOCK_ID =~ ^[0-9]+:[0-9]+$ ]] \
  || [ "$(stat -Lc '%d:%i' "$LOCK")" != "$SMOKE_LOCK_ID" ]; then
  fail_preflight "persistent-smoke-lock-identity"
fi
SMOKE_STARTED=1
mkdir -m 0755 "$SMOKE_OUTPUT_ROOT" || fail_preflight "smoke-output-root-create"
mkdir -m 0755 "$RAW_DIR" "$SMOKE_EPISODE_ROOT" \
  || fail_preflight "smoke-output-layout-create"
mkdir -m 0700 "$CONTAINER_CONTROL_ROOT" || fail_preflight "container-control-root-create"
CONTAINER_CONTROL_ROOT_ID=$(stat -Lc '%d:%i' "$CONTAINER_CONTROL_ROOT") \
  || fail_preflight "container-control-root-identity"
mkdir -m 0755 "$STAGING_ROOT" || fail_preflight "smoke-staging-create"
STAGING_ROOT_ID=$(stat -Lc '%d:%i' "$STAGING_ROOT") \
  || fail_preflight "smoke-staging-identity"

COMPOSE_PID=
CURRENT_DOSE_ORDINAL=
CURRENT_DOSE_CID_DIR=
OWNED_CONTAINER_IDS=()
OWNED_CONTAINER_ROLES=()
SERVER_TOUCHED=0
DOCKER_BIN=
DOCKER_BIN_ID=
DOCKER_BIN_SHA=
DOCKER_WRAPPER_SHA=

record_owned_container() {
  local ID=${1:?container id required} ROLE=${2:?container role required}
  local INDEX KNOWN_ID KNOWN_ROLE
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    KNOWN_ID=${OWNED_CONTAINER_IDS[$INDEX]}
    KNOWN_ROLE=${OWNED_CONTAINER_ROLES[$INDEX]}
    if [ "$KNOWN_ROLE" = "$ROLE" ] && [ "$KNOWN_ID" != "$ID" ]; then
      echo "I135_SMOKE_CONTAINER_REPLACED role=$ROLE old=$KNOWN_ID new=$ID" >&2
      return 88
    fi
    if [ "$KNOWN_ID" = "$ID" ]; then
      [ "$KNOWN_ROLE" = "$ROLE" ] || return 88
      return 0
    fi
  done
  OWNED_CONTAINER_IDS+=("$ID")
  OWNED_CONTAINER_ROLES+=("$ROLE")
}

capture_owned_containers() {
  local IDS_TEXT ID IDENTITY OBSERVED_ID OBSERVED_NAME OBSERVED_IMAGE
  local OBSERVED_MISSION OBSERVED_MANIFEST OBSERVED_MODE OBSERVED_DOSE OBSERVED_ROLE
  local EXPECTED_NAME EXPECTED_IMAGE
  if ! IDS_TEXT=$(docker ps -aq --no-trunc); then
    echo "I135_SMOKE_CONTAINER_PROBE_FAIL scope=all" >&2
    return 81
  fi
  [ -n "$IDS_TEXT" ] || return 0
  while IFS= read -r ID; do
    if ! [[ $ID =~ ^[0-9a-f]{64}$ ]]; then
      echo "I135_SMOKE_CONTAINER_OWNERSHIP_FAIL malformed-id=$ID" >&2
      return 82
    fi
    if ! IDENTITY=$(docker inspect --format \
      '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{index .Config.Labels "sentinel.mission"}}|{{index .Config.Labels "sentinel.manifest"}}|{{index .Config.Labels "sentinel.mode"}}|{{index .Config.Labels "sentinel.dose"}}|{{index .Config.Labels "sentinel.role"}}' \
      "$ID"); then
      echo "I135_SMOKE_CONTAINER_INSPECT_FAIL id=$ID" >&2
      return 83
    fi
    IFS='|' read -r OBSERVED_ID OBSERVED_NAME OBSERVED_IMAGE OBSERVED_MISSION \
      OBSERVED_MANIFEST OBSERVED_MODE OBSERVED_DOSE OBSERVED_ROLE <<<"$IDENTITY"
    case "$OBSERVED_ROLE" in
      renderer)
        EXPECTED_NAME=/renderer
        EXPECTED_IMAGE=$EXPECTED_NEURAD_IMAGE_ID
        ;;
      model)
        EXPECTED_NAME=/model
        EXPECTED_IMAGE=$EXPECTED_UNIAD_IMAGE_ID
        ;;
      ncap)
        EXPECTED_NAME=
        EXPECTED_IMAGE=$EXPECTED_NCAP_IMAGE_ID
        ;;
      *)
        echo "I135_SMOKE_CONTAINER_OWNERSHIP_FAIL unowned-id=$ID identity=$IDENTITY" >&2
        return 84
        ;;
    esac
    if [ "$OBSERVED_ID" != "$ID" ] \
      || [ "$OBSERVED_IMAGE" != "$EXPECTED_IMAGE" ] \
      || [ "$OBSERVED_MISSION" != "iter135" ] \
      || [ "$OBSERVED_MANIFEST" != "$EXPECTED_MANIFEST_SHA" ] \
      || [ "$OBSERVED_MODE" != "nonanalytic-smoke" ] \
      || [ "$OBSERVED_DOSE" != "$CURRENT_DOSE_ORDINAL" ] \
      || { [ -n "$EXPECTED_NAME" ] && [ "$OBSERVED_NAME" != "$EXPECTED_NAME" ]; } \
      || { [ "$OBSERVED_ROLE" = "ncap" ] \
        && { [ "$OBSERVED_NAME" = "/renderer" ] || [ "$OBSERVED_NAME" = "/model" ]; }; }; then
      echo "I135_SMOKE_CONTAINER_OWNERSHIP_FAIL id=$ID identity=$IDENTITY" >&2
      return 84
    fi
    record_owned_container "$ID" "$OBSERVED_ROLE" || return $?
  done <<<"$IDS_TEXT"
}

assert_no_conflicting_containers() {
  local NAME IDS_TEXT
  for NAME in renderer model ncap; do
    if ! IDS_TEXT=$(docker ps -aq --no-trunc --filter "name=^/${NAME}$"); then
      echo "I135_SMOKE_CONTAINER_PROBE_FAIL name=$NAME" >&2
      return 85
    fi
    if [ -n "$IDS_TEXT" ]; then
      echo "I135_SMOKE_PREEXISTING_CONTAINER name=$NAME ids=$IDS_TEXT" >&2
      return 86
    fi
  done
}

assert_docker_empty() {
  local IDS_TEXT
  if ! IDS_TEXT=$(docker ps -aq --no-trunc); then
    echo "I135_SMOKE_CONTAINER_PROBE_FAIL scope=all" >&2
    return 89
  fi
  if [ -n "$IDS_TEXT" ]; then
    echo "I135_SMOKE_PREEXISTING_CONTAINER scope=all ids=$IDS_TEXT" >&2
    return 90
  fi
}

assert_immutable_images() {
  local EXPECTED_ID OBSERVED_ID
  for EXPECTED_ID in \
    "$EXPECTED_UNIAD_IMAGE_ID" \
    "$EXPECTED_NEURAD_IMAGE_ID" \
    "$EXPECTED_NCAP_IMAGE_ID"; do
    if ! OBSERVED_ID=$(docker image inspect "$EXPECTED_ID" --format '{{.Id}}'); then
      echo "I135_SMOKE_IMAGE_PROBE_FAIL expected=$EXPECTED_ID" >&2
      return 93
    fi
    if [ "$OBSERVED_ID" != "$EXPECTED_ID" ]; then
      echo "I135_SMOKE_IMAGE_ID_DRIFT expected=$EXPECTED_ID actual=$OBSERVED_ID" >&2
      return 94
    fi
  done
}

assert_gpu_compute_idle() {
  local PIDS
  if ! PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader); then
    echo "I135_SMOKE_GPU_PROBE_FAIL" >&2
    return 91
  fi
  if [[ $PIDS =~ [^[:space:]] ]]; then
    echo "I135_SMOKE_GPU_BUSY pids=$PIDS" >&2
    return 92
  fi
}

assert_evaluator_idle() {
  python3 - <<'PY'
import os
import re
import subprocess

pattern = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
matches = []
for raw in subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines():
    pid_text, _, command = raw.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid not in {os.getpid(), os.getppid()} and pattern.search(command):
        matches.append(f"{pid}:{command}")
if matches:
    print("I135_SMOKE_EVALUATOR_BUSY", *matches, sep="\n - ")
    raise SystemExit(1)
PY
}

verify_final_live_contract() {
  python3 - "$ENV_SOURCE" "$MANIFEST_SOURCE" "$LOCK" "$SMOKE_LOCK_ID" \
    "$EXPECTED_MANIFEST_SHA" "$RUNNER_SHA" "$RUNNER_SOURCE" "$RUNNER_ID" \
    "$MISSION_STATE_SOURCE" "$$" <<'PY'
import csv
import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path

(
    environment_text,
    manifest_text,
    lock_text,
    lock_identity,
    manifest_sha,
    runner_sha,
    runner_text,
    runner_identity,
    mission_text,
    expected_pid_text,
) = sys.argv[1:]
expected_pid = int(expected_pid_text)
environment_path = Path(environment_text)
manifest_path = Path(manifest_text)
runner = Path(runner_text)
mission = Path(mission_text)
for path in (environment_path, manifest_path, runner, mission):
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"final provenance path drift: {path}")
environment_payload = environment_path.read_bytes()
manifest_payload = manifest_path.read_bytes()
runner_payload = runner.read_bytes()
mission_payload = mission.read_bytes()
manifest = json.loads(manifest_payload)
if (
    hashlib.sha256(manifest_payload).hexdigest() != manifest_sha
    or hashlib.sha256(runner_payload).hexdigest() != runner_sha
    or f"{runner.stat().st_dev}:{runner.stat().st_ino}" != runner_identity
    or manifest.get("hash_bound_files", {}).get("env_receipts.json", {}).get("sha256")
    != hashlib.sha256(environment_payload).hexdigest()
    or manifest.get("mission_state", {}).get("sha256")
    != hashlib.sha256(mission_payload).hexdigest()
    or manifest.get("dataset_receipt")
    != manifest.get("environment_receipts", {}).get("dataset")
):
    raise SystemExit("final provenance receipt drift")
environment = json.loads(environment_payload)
dataset = manifest.get("dataset_receipt")
identity = dataset.get("identity") if isinstance(dataset, dict) else None
dataset_root = Path("/datasets/nuscenes-full")
if (
    not isinstance(identity, dict)
    or dataset_root.is_symlink()
    or not dataset_root.is_dir()
    or dataset_root.resolve(strict=True) != dataset_root
    or identity.get("dataset_st_dev") != dataset_root.stat().st_dev
    or identity.get("mount_st_dev") != dataset_root.stat().st_dev
    or identity.get("root_st_dev") != Path("/").stat().st_dev
    or dataset_root.stat().st_dev == Path("/").stat().st_dev
):
    raise SystemExit("final dataset device drift")
dataset_mount = subprocess.check_output(
    ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(dataset_root)],
    text=True,
).split()
if dataset_mount != [
    "/dev/nvme0n2",
    "ext4",
    "9a98277e-b21f-4ffc-8f14-3f2235b43103",
]:
    raise SystemExit(f"final dataset mount drift: {dataset_mount}")
if socket.gethostname() != "sentinel-gpu" or environment.get("host") != "sentinel-gpu":
    raise SystemExit("final host identity drift")
rows = list(
    csv.reader(
        subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,driver_version,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).splitlines(),
        skipinitialspace=True,
    )
)
if len(rows) != 1 or len(rows[0]) != 4:
    raise SystemExit("final GPU row drift")
name, uuid, driver, memory = (value.strip() for value in rows[0])
live_gpu = {
    "model": name,
    "count": 1,
    "uuid": uuid,
    "driver_version": driver,
    "memory_total_mib": int(memory),
}
if live_gpu != environment.get("gpu") or live_gpu != {
    "model": "NVIDIA L4",
    "count": 1,
    "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
    "driver_version": "580.159.03",
    "memory_total_mib": 23034,
}:
    raise SystemExit("final GPU identity drift")
lock = Path(lock_text)
if (
    lock != Path("/var/lib/sentinel/i135-smoke.lock")
    or lock.is_symlink()
    or not lock.is_file()
    or lock.resolve(strict=True) != lock
    or f"{lock.stat().st_dev}:{lock.stat().st_ino}" != lock_identity
    or (lock.stat().st_mode & 0o777) != 0o444
):
    raise SystemExit("persistent smoke lock identity drift")
payload = json.loads(lock.read_text())
expected_fields = {
    "schema",
    "manifest_sha256",
    "runner_sha256",
    "mission_state_sha256",
    "pid",
    "created_at_utc",
    "mode",
    "nonanalytic",
    "analytic_episode_count",
    "dose_invocation_count",
    "retry_policy",
    "smoke_output_root",
}
if (
    set(payload) != expected_fields
    or payload.get("schema") != "iter135.smoke_lock.v1"
    or payload.get("manifest_sha256") != manifest_sha
    or payload.get("runner_sha256") != runner_sha
    or payload.get("mission_state_sha256") != hashlib.sha256(mission_payload).hexdigest()
    or payload.get("pid") != expected_pid
    or payload.get("mode") != "nonanalytic_g5_smoke"
    or payload.get("nonanalytic") is not True
    or payload.get("analytic_episode_count") != 0
    or payload.get("dose_invocation_count") != 4
    or payload.get("retry_policy") != "one_shot_no_retry_lock_retained"
    or payload.get("smoke_output_root")
    != "/datasets/nuscenes-full/sentinel-i135-smoke-evidence"
):
    raise SystemExit("persistent smoke lock receipt drift")
PY
}

owned_container_id() {
  local REQUESTED_ROLE=${1:?container role required} INDEX
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    if [ "${OWNED_CONTAINER_ROLES[$INDEX]}" = "$REQUESTED_ROLE" ]; then
      printf '%s\n' "${OWNED_CONTAINER_IDS[$INDEX]}"
      return 0
    fi
  done
  return 1
}

owned_container_name_count() {
  local ROLE INDEX
  local RENDERER_SEEN=0 MODEL_SEEN=0 NCAP_SEEN=0
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    ROLE=${OWNED_CONTAINER_ROLES[$INDEX]}
    case "$ROLE" in
      renderer) RENDERER_SEEN=1 ;;
      model) MODEL_SEEN=1 ;;
      ncap) NCAP_SEEN=1 ;;
      *) return 1 ;;
    esac
  done
  printf '%s\n' "$((RENDERER_SEEN + MODEL_SEEN + NCAP_SEEN))"
}

cleanup_owned_containers() {
  local ALL_IDS_TEXT ID ROLE INDEX OBSERVED_ID REMOVE_RC=0
  local -a REMAINING_IDS=() REMAINING_ROLES=()
  if [ "${#OWNED_CONTAINER_IDS[@]}" -eq 0 ]; then
    return 0
  fi
  ALL_IDS_TEXT=$(docker ps -aq --no-trunc) || return 1
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    ID=${OWNED_CONTAINER_IDS[$INDEX]}
    ROLE=${OWNED_CONTAINER_ROLES[$INDEX]}
    if ! printf '%s\n' "$ALL_IDS_TEXT" | grep -Fxq "$ID"; then
      continue
    fi
    if ! docker rm -f "$ID" >/dev/null 2>&1; then
      REMAINING_IDS+=("$ID")
      REMAINING_ROLES+=("$ROLE")
      REMOVE_RC=1
      continue
    fi
    ALL_IDS_TEXT=$(docker ps -aq --no-trunc) || {
      REMAINING_IDS+=("$ID")
      REMAINING_ROLES+=("$ROLE")
      REMOVE_RC=1
      continue
    }
    if printf '%s\n' "$ALL_IDS_TEXT" | grep -Fxq "$ID"; then
      REMAINING_IDS+=("$ID")
      REMAINING_ROLES+=("$ROLE")
      REMOVE_RC=1
    fi
  done
  OWNED_CONTAINER_IDS=()
  OWNED_CONTAINER_ROLES=()
  if [ "${#REMAINING_IDS[@]}" -gt 0 ]; then
    OWNED_CONTAINER_IDS=("${REMAINING_IDS[@]}")
    OWNED_CONTAINER_ROLES=("${REMAINING_ROLES[@]}")
  fi
  return "$REMOVE_RC"
}

cleanup_smoke() {
  if [[ ${COMPOSE_PID:-} =~ ^[0-9]+$ ]] && kill -0 "$COMPOSE_PID" 2>/dev/null; then
    kill -TERM "$COMPOSE_PID" >/dev/null 2>&1 || true
    wait "$COMPOSE_PID" 2>/dev/null || true
  fi
  if [ -n "$CURRENT_DOSE_CID_DIR" ]; then
    capture_owned_containers >/dev/null 2>&1 || true
  fi
  cleanup_owned_containers >/dev/null 2>&1 || true
  if [ "$SERVER_TOUCHED" = "1" ]; then
    git -C "$STACK/UniAD" checkout HEAD -- inference/server.py >/dev/null 2>&1 || true
    SERVER_TOUCHED=0
  fi
}
trap cleanup_smoke EXIT

DOCKER_BIN=$(readlink -f "$(command -v docker)") || fail_preflight "docker-binary-realpath"
if [ ! -f "$DOCKER_BIN" ] || [ ! -x "$DOCKER_BIN" ] || [ -L "$DOCKER_BIN" ]; then
  fail_preflight "docker-binary-physical:$DOCKER_BIN"
fi
DOCKER_BIN_ID=$(stat -Lc '%d:%i' "$DOCKER_BIN") || fail_preflight "docker-binary-identity"
DOCKER_BIN_SHA=$(sha256sum "$DOCKER_BIN" | awk '{print $1}') \
  || fail_preflight "docker-binary-sha256"
DOCKER_WRAPPER_SHA=$(python3 - "$CONTAINER_CONTROL_ROOT/docker" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = r'''#!/bin/bash
set -euo pipefail

: "${SENTINEL_DOCKER_BIN:?SENTINEL_DOCKER_BIN must be set}"
: "${SENTINEL_DOCKER_BIN_ID:?SENTINEL_DOCKER_BIN_ID must be set}"
: "${SENTINEL_DOCKER_BIN_SHA256:?SENTINEL_DOCKER_BIN_SHA256 must be set}"
: "${SENTINEL_DOCKER_WRAPPER_SHA256:?SENTINEL_DOCKER_WRAPPER_SHA256 must be set}"
: "${SENTINEL_MANIFEST_SHA256:?SENTINEL_MANIFEST_SHA256 must be set}"
: "${SENTINEL_SMOKE_DOSE_ORDINAL:?SENTINEL_SMOKE_DOSE_ORDINAL must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT:?SENTINEL_CONTAINER_CONTROL_ROOT must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT_ID:?SENTINEL_CONTAINER_CONTROL_ROOT_ID must be set}"
: "${SENTINEL_CONTAINER_CID_DIR:?SENTINEL_CONTAINER_CID_DIR must be set}"
if [ ! -f "$SENTINEL_DOCKER_BIN" ] || [ ! -x "$SENTINEL_DOCKER_BIN" ] \
  || [ -L "$SENTINEL_DOCKER_BIN" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL docker-binary" >&2
  exit 125
fi
if [ "$(stat -Lc '%d:%i' "$SENTINEL_DOCKER_BIN")" != "$SENTINEL_DOCKER_BIN_ID" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL docker-binary-identity-drift" >&2
  exit 125
fi
OBSERVED_DOCKER_SHA=$(sha256sum "$SENTINEL_DOCKER_BIN" | awk '{print $1}')
if [ "$OBSERVED_DOCKER_SHA" != "$SENTINEL_DOCKER_BIN_SHA256" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL docker-binary-drift" >&2
  exit 125
fi
if [ "$0" != "$SENTINEL_CONTAINER_CONTROL_ROOT/docker" ] \
  || [ -L "$0" ] || [ ! -f "$0" ] \
  || [ "$(sha256sum "$0" | awk '{print $1}')" != "$SENTINEL_DOCKER_WRAPPER_SHA256" ] \
  || [ "$(stat -Lc '%d:%i' "$SENTINEL_CONTAINER_CONTROL_ROOT")" \
    != "$SENTINEL_CONTAINER_CONTROL_ROOT_ID" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL wrapper-identity-drift" >&2
  exit 125
fi
if ! [[ "$SENTINEL_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] \
  || ! [[ "$SENTINEL_SMOKE_DOSE_ORDINAL" =~ ^[0-3]$ ]] \
  || [ "$SENTINEL_CONTAINER_CID_DIR" \
    != "$SENTINEL_CONTAINER_CONTROL_ROOT/dose-$SENTINEL_SMOKE_DOSE_ORDINAL" ] \
  || [ -L "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ -L "$SENTINEL_CONTAINER_CID_DIR" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CID_DIR" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL control-contract" >&2
  exit 125
fi
if [ "$#" -lt 1 ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL command-missing" >&2
  exit 125
fi
COMMAND=$1
shift
if [ "$COMMAND" != "run" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL unexpected-command:$COMMAND" >&2
  exit 125
fi
ARGS=("$@")
NAME=
ROLE=
EXPECTED_IMAGE=
for ((INDEX = 0; INDEX < ${#ARGS[@]}; INDEX++)); do
  ARG=${ARGS[$INDEX]}
  if [ "$ARG" = "--name" ]; then
    if [ $((INDEX + 1)) -ge ${#ARGS[@]} ]; then
      echo "I135_SMOKE_DOCKER_WRAPPER_FAIL name-value" >&2
      exit 125
    fi
    NAME=${ARGS[$((INDEX + 1))]}
  elif [[ "$ARG" == --name=* ]]; then
    NAME=${ARG#--name=}
  fi
done
case "$NAME" in
  renderer)
    ROLE=renderer
    EXPECTED_IMAGE=sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c
    ;;
  model)
    ROLE=model
    EXPECTED_IMAGE=sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb
    ;;
  "")
    ROLE=ncap
    EXPECTED_IMAGE=sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce
    ;;
  *)
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL unexpected-name:$NAME" >&2
    exit 125
    ;;
esac
IMAGE_MATCHES=0
for ARG in "${ARGS[@]}"; do
  if [ "$ARG" = "$EXPECTED_IMAGE" ]; then
    IMAGE_MATCHES=$((IMAGE_MATCHES + 1))
  fi
done
if [ "$IMAGE_MATCHES" != "1" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL image:$ROLE:$IMAGE_MATCHES" >&2
  exit 125
fi
CID_FILE=$SENTINEL_CONTAINER_CID_DIR/$ROLE.cid
if [ -e "$CID_FILE" ] || [ -L "$CID_FILE" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL cid-preexists:$ROLE" >&2
  exit 125
fi
exec "$SENTINEL_DOCKER_BIN" run \
  --label sentinel.mission=iter135 \
  --label "sentinel.manifest=$SENTINEL_MANIFEST_SHA256" \
  --label sentinel.mode=nonanalytic-smoke \
  --label "sentinel.dose=$SENTINEL_SMOKE_DOSE_ORDINAL" \
  --label "sentinel.role=$ROLE" \
  --cidfile "$CID_FILE" \
  "${ARGS[@]}"
'''
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o500)
with os.fdopen(descriptor, "wb") as stream:
    stream.write(payload.encode())
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(path, 0o500)
print(hashlib.sha256(payload.encode()).hexdigest())
PY
) || fail_preflight "docker-wrapper-create"

verify_container_control() {
  python3 - "$CONTAINER_CONTROL_ROOT" "$CONTAINER_CONTROL_ROOT_ID" \
    "$DOCKER_WRAPPER_SHA" "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" <<'PY'
import hashlib
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1])
root_identity, wrapper_sha, docker_text, docker_identity, docker_sha = sys.argv[2:]
docker = Path(docker_text)
wrapper = root / "docker"
if (
    root != Path("/datasets/nuscenes-full/sentinel-i135-smoke-evidence/container-control")
    or root.is_symlink()
    or not root.is_dir()
    or root.resolve(strict=True) != root
    or f"{root.stat().st_dev}:{root.stat().st_ino}" != root_identity
    or wrapper.is_symlink()
    or not wrapper.is_file()
    or wrapper.resolve(strict=True) != wrapper
    or stat.S_IMODE(wrapper.stat().st_mode) != 0o500
    or hashlib.sha256(wrapper.read_bytes()).hexdigest() != wrapper_sha
    or docker.is_symlink()
    or not docker.is_file()
    or docker.resolve(strict=True) != docker
    or f"{docker.stat().st_dev}:{docker.stat().st_ino}" != docker_identity
    or hashlib.sha256(docker.read_bytes()).hexdigest() != docker_sha
):
    raise SystemExit("smoke container control contract drift")
PY
}
verify_container_control || fail_preflight "container-control-verification"

verify_container_receipts() {
  local INDEX
  local -a OWNED_ARGS=()
  if [ "${#OWNED_CONTAINER_IDS[@]}" != "3" ] \
    || [ "${#OWNED_CONTAINER_ROLES[@]}" != "3" ]; then
    return 76
  fi
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    OWNED_ARGS+=("${OWNED_CONTAINER_ROLES[$INDEX]}=${OWNED_CONTAINER_IDS[$INDEX]}")
  done
  python3 - "$CURRENT_DOSE_CID_DIR" "$CURRENT_DOSE_ORDINAL" \
    "${OWNED_ARGS[@]}" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
ordinal = sys.argv[2]
owned = {}
for value in sys.argv[3:]:
    role, separator, container_id = value.partition("=")
    if separator != "=" or role in owned:
        raise SystemExit("owned container argument drift")
    owned[role] = container_id
expected_roles = {"renderer", "model", "ncap"}
if (
    ordinal not in {"0", "1", "2", "3"}
    or root != Path(
        "/datasets/nuscenes-full/sentinel-i135-smoke-evidence/container-control"
    )
    / f"dose-{ordinal}"
    or root.is_symlink()
    or not root.is_dir()
    or root.resolve(strict=True) != root
    or {path.name for path in root.iterdir()}
    != {f"{role}.cid" for role in expected_roles}
    or set(owned) != expected_roles
):
    raise SystemExit("container cid directory contract drift")
receipts = {}
for role in sorted(expected_roles):
    path = root / f"{role}.cid"
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"container cid is not physical: {role}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        payload = os.read(descriptor, 256)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or len(payload) != before.st_size
    ):
        raise SystemExit(f"container cid changed while read: {role}")
    container_id = payload.decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise SystemExit(f"container cid malformed: {role}")
    if owned.get(role) != container_id:
        raise SystemExit(f"container cid was not captured live: {role}")
    receipts[role] = container_id
if len(set(receipts.values())) != 3:
    raise SystemExit("container cid identities are not unique")
print(json.dumps(receipts, sort_keys=True, separators=(",", ":")))
PY
}

captured_container_receipts_json() {
  local INDEX
  local -a OWNED_ARGS=()
  if [ "${#OWNED_CONTAINER_IDS[@]}" = "0" ]; then
    printf '{}\n'
    return 0
  fi
  [ "${#OWNED_CONTAINER_IDS[@]}" = "${#OWNED_CONTAINER_ROLES[@]}" ] || return 1
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX++)); do
    OWNED_ARGS+=("${OWNED_CONTAINER_ROLES[$INDEX]}=${OWNED_CONTAINER_IDS[$INDEX]}")
  done
  python3 - "${OWNED_ARGS[@]}" <<'PY'
import json
import re
import sys

receipts = {}
for value in sys.argv[1:]:
    role, separator, container_id = value.partition("=")
    if (
        separator != "="
        or role not in {"renderer", "model", "ncap"}
        or role in receipts
        or not re.fullmatch(r"[0-9a-f]{64}", container_id)
    ):
        raise SystemExit("captured container receipt drift")
    receipts[role] = container_id
if len(set(receipts.values())) != len(receipts):
    raise SystemExit("captured container IDs are not unique")
print(json.dumps(receipts, sort_keys=True, separators=(",", ":")))
PY
}

verify_smoke_runtime_inputs() {
  local SCENARIO_CLASS=$1 SEQUENCE=$2 EXPECTED_SERVER_SHA=$3 PHASE=$4
  python3 - "$MANIFEST_SOURCE" "$EXPECTED_MANIFEST_SHA" "$SCHEDULE_TARGET" \
    "$SMOKE_OUTPUT_ROOT/server_patch_blind_dose.py" "$STACK/UniAD/inference/server.py" \
    "$EXPECTED_SERVER_SHA" "$SCENARIO_CLASS" "$SEQUENCE" "$PHASE" \
    "$EXPECTED_UNIAD_IMAGE_ID" "$EXPECTED_NEURAD_IMAGE_ID" "$EXPECTED_NCAP_IMAGE_ID" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

(
    manifest_text,
    expected_manifest_sha,
    schedule_text,
    patch_text,
    server_text,
    expected_server_sha,
    scenario_class,
    sequence,
    phase,
    model_image,
    rendering_image,
    ncap_image,
) = sys.argv[1:]
if phase not in {"before", "after"}:
    raise SystemExit(f"invalid smoke runtime phase: {phase}")
classes = {
    "stationary": {"0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"},
    "frontal": {"0103", "0106", "0110", "0346", "0923"},
    "side": {"0103", "0108", "0110", "0278", "0921"},
}
if scenario_class not in classes or sequence not in classes[scenario_class]:
    raise SystemExit(f"invalid smoke runtime pair: {scenario_class}/{sequence}")


def stable_receipt(path: Path) -> tuple[str, int]:
    path = path.absolute()
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"smoke runtime input is not physical: {path}")
    path_before = path.stat()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fd_before = os.fstat(descriptor)
        if (path_before.st_dev, path_before.st_ino) != (fd_before.st_dev, fd_before.st_ino):
            raise SystemExit(f"smoke runtime input open race: {path}")
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        fd_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat()
    identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns)
    if (
        identity(path_before) != identity(fd_before)
        or identity(fd_before) != identity(fd_after)
        or identity(fd_after) != identity(path_after)
        or byte_count != fd_before.st_size
    ):
        raise SystemExit(f"smoke runtime input changed while hashing: {path}")
    return digest.hexdigest(), byte_count


manifest_path = Path(manifest_text)
manifest_sha, _manifest_bytes = stable_receipt(manifest_path)
if manifest_sha != expected_manifest_sha:
    raise SystemExit("smoke runtime manifest drift")
manifest_payload = manifest_path.read_bytes()
if hashlib.sha256(manifest_payload).hexdigest() != expected_manifest_sha:
    raise SystemExit("smoke runtime manifest second-read drift")
manifest = json.loads(manifest_payload)
if manifest.get("schema") != "iter135.launch_manifest.v2":
    raise SystemExit("smoke runtime manifest schema drift")
dataset = manifest.get("dataset_receipt")
environment_dataset = manifest.get("environment_receipts", {}).get("dataset")
identity = dataset.get("identity") if isinstance(dataset, dict) else None
dataset_root = Path("/datasets/nuscenes-full")
if (
    dataset != environment_dataset
    or not isinstance(dataset, dict)
    or dataset.get("schema") != "iter135.nuscenes_dataset_receipt.v1"
    or dataset.get("contract_sha256")
    != "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
    or not isinstance(identity, dict)
    or identity.get("dataset_root") != str(dataset_root)
    or identity.get("dataset_realpath") != str(dataset_root)
    or identity.get("dataset_is_symlink") is not False
    or dataset_root.is_symlink()
    or not dataset_root.is_dir()
    or dataset_root.resolve(strict=True) != dataset_root
    or identity.get("dataset_st_dev") != dataset_root.stat().st_dev
    or identity.get("mount_st_dev") != dataset_root.stat().st_dev
    or identity.get("root_st_dev") != Path("/").stat().st_dev
    or dataset_root.stat().st_dev == Path("/").stat().st_dev
):
    raise SystemExit("smoke runtime dataset identity drift")
dataset_mount = subprocess.run(
    ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(dataset_root)],
    check=True,
    capture_output=True,
    text=True,
).stdout.split()
if dataset_mount != [
    "/dev/nvme0n2",
    "ext4",
    "9a98277e-b21f-4ffc-8f14-3f2235b43103",
]:
    raise SystemExit(f"smoke runtime dataset mount drift: {dataset_mount}")
artifacts = manifest.get("remote_artifacts")
if not isinstance(artifacts, list) or len(artifacts) != 82:
    raise SystemExit("smoke runtime remote artifact cardinality drift")
by_role = {}
for row in artifacts:
    if not isinstance(row, dict) or set(row) != {"role", "path", "sha256", "bytes"}:
        raise SystemExit("smoke runtime artifact schema drift")
    role = row.get("role")
    if not isinstance(role, str) or role in by_role:
        raise SystemExit(f"smoke runtime artifact role drift: {role}")
    by_role[role] = row
if (
    sum(role.startswith("scenario:") for role in by_role) != 20
    or sum(role.startswith("renderer:") for role in by_role) != 42
    or "uniad_server_baseline" not in by_role
):
    raise SystemExit("smoke runtime artifact role-set drift")
selected_roles = {
    role
    for role in by_role
    if not role.startswith("scenario:")
    and not role.startswith("renderer:")
    and role != "uniad_server_baseline"
}
selected_roles.add(f"scenario:{scenario_class}/{sequence}")
selected_roles.update(
    {
        f"renderer:{sequence}:config",
        f"renderer:{sequence}:transforms",
        f"renderer:{sequence}:checkpoint",
    }
)
if len(selected_roles) != 23 or not selected_roles.issubset(by_role):
    raise SystemExit("smoke runtime selected role-set drift")
for role in sorted(selected_roles):
    row = by_role[role]
    actual_sha, actual_bytes = stable_receipt(Path(row["path"]))
    if actual_sha != row["sha256"] or actual_bytes != row["bytes"]:
        raise SystemExit(f"smoke runtime artifact drift: {role}")

server_sha, _server_bytes = stable_receipt(Path(server_text))
if server_sha != expected_server_sha:
    raise SystemExit(f"smoke runtime server drift: {server_sha}!={expected_server_sha}")
schedule = Path(schedule_text)
schedule_receipt = manifest.get("hash_bound_files", {}).get("dose_schedules.json")
schedule_sha, schedule_bytes = stable_receipt(schedule)
if (
    not isinstance(schedule_receipt, dict)
    or set(schedule_receipt) != {"source_path", "sha256", "bytes"}
    or stat.S_IMODE(schedule.stat().st_mode) != 0o444
    or schedule_sha != schedule_receipt.get("sha256")
    or schedule_bytes != schedule_receipt.get("bytes")
):
    raise SystemExit("smoke runtime schedule drift")
patch_receipt = manifest.get("hash_bound_files", {}).get("server_patch_blind_dose.py")
patch_sha, patch_bytes = stable_receipt(Path(patch_text))
if (
    not isinstance(patch_receipt, dict)
    or set(patch_receipt) != {"source_path", "sha256", "bytes"}
    or patch_sha != patch_receipt.get("sha256")
    or patch_bytes != patch_receipt.get("bytes")
):
    raise SystemExit("smoke runtime blind patch drift")
expected_images = {
    "uniad:latest": model_image,
    "neurad:latest": rendering_image,
    "ncap:latest": ncap_image,
}
if manifest.get("container_images") is None or set(manifest["container_images"]) != set(expected_images):
    raise SystemExit("smoke runtime image receipt set drift")
for name, expected_image in expected_images.items():
    row = manifest["container_images"].get(name)
    if not isinstance(row, dict) or row.get("image_id") != expected_image:
        raise SystemExit(f"smoke runtime image receipt drift: {name}")
    observed = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", expected_image],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if observed != expected_image:
        raise SystemExit(f"smoke runtime image identity drift: {name}")
print(
    f"I135_SMOKE_RUNTIME_INPUTS_OK phase={phase} "
    f"pair={scenario_class}/{sequence} roles={len(selected_roles)}"
)
PY
}

cp "$MANIFEST_SOURCE" "$RAW_DIR/pre_smoke_manifest.json"
cp "$ENV_SOURCE" "$RAW_DIR/environment_receipt.json"
for name in dose_schedules.json server_patch_blind_dose.py run_smoke135.sh validate_smoke135.py env_receipts.json; do
  cp "$I135/$name" "$SMOKE_OUTPUT_ROOT/$name"
done
cp "$MISSION_STATE_SOURCE" "$SMOKE_OUTPUT_ROOT/MISSION_STATE.json"
SCHEDULE_TARGET_ID=$(python3 - "$SMOKE_OUTPUT_ROOT/dose_schedules.json" \
  "$SCHEDULE_TARGET" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
if (
    source.is_symlink()
    or not source.is_file()
    or source.resolve(strict=True) != source
    or target != Path("/opt/sentinel-stack/UniAD/dose_schedules.json")
    or target.exists()
    or target.is_symlink()
    or target.parent.is_symlink()
    or target.parent.resolve(strict=True) != target.parent
):
    raise SystemExit("schedule copy physical-path contract drift")
before = source.stat()
payload = source.read_bytes()
after = source.stat()
identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns)
if identity(before) != identity(after) or len(payload) != before.st_size:
    raise SystemExit("schedule source changed while read")
descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
try:
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(target, 0o444)
    if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(payload).digest():
        raise SystemExit("schedule copy hash drift")
    parent_descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)
    row = target.stat()
    print(f"{row.st_dev}:{row.st_ino}")
except BaseException:
    if target.exists() and not target.is_symlink():
        target.unlink()
    raise
PY
) || fail_preflight "schedule-copy"

EXECUTION_LOG=$RAW_DIR/execution.jsonl
python3 - "$EXECUTION_LOG" "$SMOKE_OUTPUT_ROOT" "$EXPECTED_MANIFEST_SHA" \
  "$RUNNER_SHA" "$RUNNER_ID" "$LOCK" "$SMOKE_LOCK_ID" "$DOCKER_WRAPPER_SHA" \
  "$DOCKER_BIN_SHA" "$DOCKER_BIN_ID" "$CONTAINER_CONTROL_ROOT_ID" <<'PY'
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

(
    log_path,
    root_text,
    manifest_hash,
    runner_sha,
    runner_identity,
    lock_path,
    lock_identity,
    wrapper_sha,
    docker_sha,
    docker_identity,
    container_control_root_identity,
) = sys.argv[1:]
root = Path(root_text)
environment = json.loads((root / "env_receipts.json").read_text())


def digest(name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()


frozen_images = {
    "ncap:latest": "sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce",
    "neurad:latest": "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c",
    "uniad:latest": "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb",
}
environment_images = {
    name: row.get("image_id")
    for name, row in environment.get("container_images", {}).items()
    if isinstance(name, str) and isinstance(row, dict)
}
if environment_images != frozen_images:
    raise SystemExit("frozen image IDs changed after preflight")
images = {}
for name, expected_id in sorted(frozen_images.items()):
    tag_actual = subprocess.check_output(
        ["docker", "image", "inspect", name, "--format", "{{.Id}}"], text=True
    ).strip()
    id_actual = subprocess.check_output(
        ["docker", "image", "inspect", expected_id, "--format", "{{.Id}}"], text=True
    ).strip()
    if tag_actual != expected_id or id_actual != expected_id:
        raise SystemExit(f"frozen image ID drift: {name}")
    images[name] = id_actual
gpu_rows = list(
    csv.reader(
        subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,driver_version,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).splitlines(),
        skipinitialspace=True,
    )
)
if len(gpu_rows) != 1 or len(gpu_rows[0]) != 4:
    raise SystemExit(f"live GPU identity row drift: {gpu_rows!r}")
gpu_name, gpu_uuid, gpu_driver, gpu_memory = (item.strip() for item in gpu_rows[0])
gpu_identity = {
    "model": gpu_name,
    "count": 1,
    "uuid": gpu_uuid,
    "driver_version": gpu_driver,
    "memory_total_mib": int(gpu_memory),
}
if gpu_identity != environment["gpu"]:
    raise SystemExit("live GPU identity changed after preflight")
event = {
    "event": "session_start",
    "schema": "iter135.smoke_execution.v1",
    "nonanalytic": True,
    "analytic_episode_count": 0,
    "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
    "smoke_output_root": "/datasets/nuscenes-full/sentinel-i135-smoke-evidence",
    "smoke_episode_root": "/datasets/nuscenes-full/sentinel-i135-smoke-evidence/episodes",
    "manifest_sha256": manifest_hash,
    "canonical_runner_sha256": runner_sha,
    "canonical_runner_identity": runner_identity,
    "persistent_smoke_lock": lock_path,
    "persistent_smoke_lock_identity": lock_identity,
    "retry_policy": "one_shot_no_retry_lock_retained",
    "docker_wrapper_sha256": wrapper_sha,
    "docker_binary_sha256": docker_sha,
    "docker_binary_identity": docker_identity,
    "container_control_root_identity": container_control_root_identity,
    "environment_receipt_sha256": hashlib.sha256(
        (root / "raw/environment_receipt.json").read_bytes()
    ).hexdigest(),
    "schedule_sha256": digest("dose_schedules.json"),
    "blind_patch_sha256": digest("server_patch_blind_dose.py"),
    "runner_sha256": digest("run_smoke135.sh"),
    "validator_sha256": digest("validate_smoke135.py"),
    "compose_sha256": environment["remote_files"]["compose_script"]["sha256"],
    "container_image_ids": images,
    "gpu_identity": gpu_identity,
}
descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
PY

capture_model_environment() {
  local MODEL_CONTAINER_ID=${1:?model container id required}
  local DESTINATION=${2:?environment destination required} PARTIAL=$2.partial
  if docker exec "$MODEL_CONTAINER_ID" sh -c 'env -0' > "$PARTIAL" 2>/dev/null; then
    mv "$PARTIAL" "$DESTINATION"
    return 0
  fi
  rm -f "$PARTIAL"
  return 1
}

append_dose_start() {
  python3 - "$EXECUTION_LOG" "$@" <<'PY'
import json
import os
import sys
from pathlib import Path

path, ordinal, dose, schedule_id, scenario_class, sequence, start_ns = sys.argv[1:]
event = {
    "event": "dose_start",
    "ordinal": int(ordinal),
    "dose": dose,
    "schedule_id": schedule_id,
    "scenario_class": scenario_class,
    "sequence": sequence,
    "run": 0,
    "runs": 1,
    "nonanalytic": True,
    "analytic_inclusion": False,
    "analytic_episode_count": 0,
    "output_root": "/datasets/nuscenes-full/sentinel-i135-smoke-evidence/episodes",
    "model_log_path": f"/model/i135-smoke-staging/{dose}.decisions.jsonl",
    "clock": "monotonic_ns",
    "start_ns": int(start_ns),
    "argv": [
        "bash",
        "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
        sequence,
        scenario_class,
        f"--scenario-category={scenario_class}",
        "--runs",
        "1",
    ],
}
with Path(path).open("a") as stream:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

append_dose_finish() {
  python3 - "$EXECUTION_LOG" "$@" <<'PY'
import json
import os
import sys
from pathlib import Path

(
    path,
    ordinal,
    dose,
    schedule_id,
    scenario_class,
    sequence,
    end_ns,
    elapsed_ns,
    compose_rc,
    capture_rc,
    monitor_rc,
    cleanup_rc,
    container_receipts_json,
    server_hash,
) = sys.argv[1:]
event = {
    "event": "dose_finish",
    "ordinal": int(ordinal),
    "dose": dose,
    "schedule_id": schedule_id,
    "scenario_class": scenario_class,
    "sequence": sequence,
    "run": 0,
    "clock": "monotonic_ns",
    "end_ns": int(end_ns),
    "elapsed_ns": int(elapsed_ns),
    "compose_exit_code": int(compose_rc),
    "env_capture_exit_code": int(capture_rc),
    "container_monitor_exit_code": int(monitor_rc),
    "container_cleanup_exit_code": int(cleanup_rc),
    "container_receipts": json.loads(container_receipts_json),
    "patched_server_sha256": server_hash,
}
with Path(path).open("a") as stream:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

append_abort() {
  local REASON=${1:?abort reason required}
  python3 - "$EXECUTION_LOG" "$REASON" <<'PY'
import json
import os
import sys
from pathlib import Path

with Path(sys.argv[1]).open("a") as stream:
    stream.write(json.dumps({"event": "session_abort", "reason": sys.argv[2]}, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
PY
}

BASE_DIR=$STACK
NUSCENES_PATH=/datasets/nuscenes-full
MODEL_NAME=UniAD
MODEL_FOLDER=$BASE_DIR/UniAD
MODEL_CHECKPOINT_PATH=ckpts/uniad_base_e2e.pth
MODEL_CFG_PATH=projects/configs/stage2_e2e/inference_e2e.py
MODEL_IMAGE=$EXPECTED_UNIAD_IMAGE_ID
RENDERING_FOLDER=$BASE_DIR/neurad-studio
RENDERING_CHECKPOITNS_PATH=checkpoints
RENDERING_IMAGE=$EXPECTED_NEURAD_IMAGE_ID
NCAP_FOLDER=$BASE_DIR/NeuroNCAP
NCAP_IMAGE=$EXPECTED_NCAP_IMAGE_ID
COMPOSE=$NCAP_FOLDER/scripts/_docker_compose_release.sh
TOTAL_GPU_NS=0
ORDINAL=0
cd "$NCAP_FOLDER"

monotonic_ns() {
  python3 - <<'PY'
import time

print(time.monotonic_ns())
PY
}

while IFS=$'\t' read -r DOSE SCHEDULE_ID SCENARIO_CLASS SEQUENCE; do
  [ -n "$DOSE" ] || continue
  if ! assert_no_conflicting_containers; then
    append_abort "preexisting-container-conflict:$DOSE"
    exit 1
  fi
  if ! assert_docker_empty; then
    append_abort "docker-not-empty:$DOSE"
    exit 1
  fi
  if ! assert_immutable_images; then
    append_abort "immutable-image-drift:$DOSE"
    exit 1
  fi
  if ! assert_gpu_compute_idle; then
    append_abort "gpu-not-idle:$DOSE"
    exit 1
  fi
  DECISION_HOST=$STAGING_ROOT/$DOSE.decisions.jsonl
  DECISION_RAW=$RAW_DIR/$DOSE.decisions.jsonl
  DECISION_MODEL=$MODEL_STAGING_ROOT/$DOSE.decisions.jsonl
  ENV_RAW=$RAW_DIR/$DOSE.model-env.bin
  COMPOSE_LOG=$RAW_DIR/$DOSE.compose.log
  [ ! -e "$DECISION_HOST" ] && [ ! -e "$DECISION_RAW" ] && [ ! -e "$ENV_RAW" ] \
    && [ ! -e "$COMPOSE_LOG" ] || { append_abort "preexisting-dose-evidence:$DOSE"; exit 1; }

  verify_container_control || { append_abort "container-control-drift:$DOSE"; exit 1; }
  CURRENT_DOSE_ORDINAL=$ORDINAL
  CURRENT_DOSE_CID_DIR=$CONTAINER_CONTROL_ROOT/dose-$ORDINAL
  [ ! -e "$CURRENT_DOSE_CID_DIR" ] && [ ! -L "$CURRENT_DOSE_CID_DIR" ] \
    || { append_abort "container-cid-dir-preexists:$DOSE"; exit 1; }
  mkdir -m 0700 "$CURRENT_DOSE_CID_DIR" \
    || { append_abort "container-cid-dir-create:$DOSE"; exit 1; }
  OWNED_CONTAINER_IDS=()
  OWNED_CONTAINER_ROLES=()

  BASELINE_EXPECTED=$(python3 - "$RAW_DIR/environment_receipt.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["remote_files"]["uniad_server_baseline"]["sha256"])
PY
)
  if ! git -C "$STACK/UniAD" diff --cached --quiet -- \
    || [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" \
      != "$BASELINE_EXPECTED" ]; then
    append_abort "server-baseline-drift:$DOSE"
    exit 1
  fi
  SERVER_TOUCHED=1
  python3 "$SMOKE_OUTPUT_ROOT/server_patch_blind_dose.py" > "$COMPOSE_LOG" 2>&1 || {
    append_abort "blind-patch-failed:$DOSE"
    exit 1
  }
  PATCHED_SERVER_SHA=$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')
  if [ "$PATCHED_SERVER_SHA" != "$EXPECTED_BLIND_PATCHED_SERVER_SHA256" ]; then
    append_abort "blind-patched-server-sha256:$DOSE:$PATCHED_SERVER_SHA"
    exit 1
  fi
  verify_smoke_runtime_inputs "$SCENARIO_CLASS" "$SEQUENCE" \
    "$EXPECTED_BLIND_PATCHED_SERVER_SHA256" before \
    || { append_abort "runtime-input-drift-before:$DOSE"; exit 1; }

  START_NS=$(monotonic_ns)
  append_dose_start "$ORDINAL" "$DOSE" "$SCHEDULE_ID" "$SCENARIO_CLASS" "$SEQUENCE" "$START_NS"
  CAPTURE_RC=1
  MONITOR_RC=0
  CLEANUP_RC=0
  CONTAINER_RECEIPTS_JSON='{}'
  CAPTURE_DEADLINE=$((SECONDS + CAPTURE_TIMEOUT_SECONDS))
  verify_container_control \
    || { append_abort "container-control-drift-at-compose:$DOSE"; exit 1; }
  timeout --signal=TERM --kill-after=60s "$DOSE_TIMEOUT_SECONDS" env \
    PATH="$CONTAINER_CONTROL_ROOT:$PATH" \
    SENTINEL_DOCKER_BIN="$DOCKER_BIN" \
    SENTINEL_DOCKER_BIN_ID="$DOCKER_BIN_ID" \
    SENTINEL_DOCKER_BIN_SHA256="$DOCKER_BIN_SHA" \
    SENTINEL_DOCKER_WRAPPER_SHA256="$DOCKER_WRAPPER_SHA" \
    SENTINEL_MANIFEST_SHA256="$EXPECTED_MANIFEST_SHA" \
    SENTINEL_SMOKE_DOSE_ORDINAL="$ORDINAL" \
    SENTINEL_CONTAINER_CONTROL_ROOT="$CONTAINER_CONTROL_ROOT" \
    SENTINEL_CONTAINER_CONTROL_ROOT_ID="$CONTAINER_CONTROL_ROOT_ID" \
    SENTINEL_CONTAINER_CID_DIR="$CURRENT_DOSE_CID_DIR" \
    BASE_DIR="$BASE_DIR" NUSCENES_PATH="$NUSCENES_PATH" \
    MODEL_NAME="$MODEL_NAME" MODEL_FOLDER="$MODEL_FOLDER" \
    MODEL_CHECKPOINT_PATH="$MODEL_CHECKPOINT_PATH" MODEL_CFG_PATH="$MODEL_CFG_PATH" \
    MODEL_IMAGE="$MODEL_IMAGE" RENDERING_FOLDER="$RENDERING_FOLDER" \
    RENDERING_CHECKPOITNS_PATH="$RENDERING_CHECKPOITNS_PATH" \
    RENDERING_IMAGE="$RENDERING_IMAGE" NCAP_FOLDER="$NCAP_FOLDER" NCAP_IMAGE="$NCAP_IMAGE" \
    TIME_NOW="i135-smoke-$DOSE" SENTINEL_OUTPUT_ROOT="$SMOKE_EPISODE_ROOT" \
    SENTINEL_ENABLED=1 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 \
    SENTINEL_CPA_MARGIN=1.5 SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
    SENTINEL_RELEASE_K=4 SENTINEL_DOSE_PAIR="$SCENARIO_CLASS/$SEQUENCE" \
    SENTINEL_DOSE_ID="$DOSE" SENTINEL_DOSE_SCHEDULE=/model/dose_schedules.json \
    SENTINEL_LOG="$DECISION_MODEL" \
    bash "$COMPOSE" "$SEQUENCE" "$SCENARIO_CLASS" \
      "--scenario-category=$SCENARIO_CLASS" --runs 1 >> "$COMPOSE_LOG" 2>&1 &
  COMPOSE_PID=$!
  while kill -0 "$COMPOSE_PID" 2>/dev/null; do
    if capture_owned_containers; then
      :
    else
      MONITOR_RC=$?
      kill -TERM "$COMPOSE_PID" >/dev/null 2>&1 || true
      break
    fi
    if [ "$CAPTURE_RC" != "0" ]; then
      if MODEL_CONTAINER_ID=$(owned_container_id model) \
        && capture_model_environment "$MODEL_CONTAINER_ID" "$ENV_RAW"; then
        CAPTURE_RC=0
      elif [ "$SECONDS" -ge "$CAPTURE_DEADLINE" ]; then
        MONITOR_RC=87
        kill -TERM "$COMPOSE_PID" >/dev/null 2>&1 || true
        break
      fi
    fi
    sleep 0.2
  done
  if wait "$COMPOSE_PID"; then
    COMPOSE_RC=0
  else
    COMPOSE_RC=$?
  fi
  COMPOSE_PID=
  if capture_owned_containers; then
    :
  else
    FINAL_OWNERSHIP_RC=$?
    if [ "$MONITOR_RC" = "0" ]; then
      MONITOR_RC=$FINAL_OWNERSHIP_RC
    fi
  fi
  END_NS=$(monotonic_ns)
  ELAPSED_NS=$((END_NS - START_NS))
  TOTAL_GPU_NS=$((TOTAL_GPU_NS + ELAPSED_NS))
  if OWNED_NAME_COUNT=$(owned_container_name_count); then
    :
  else
    OWNED_NAME_COUNT=0
    [ "$MONITOR_RC" != "0" ] || MONITOR_RC=75
  fi
  if CONTAINER_RECEIPTS_JSON=$(captured_container_receipts_json); then
    :
  else
    CONTAINER_RECEIPTS_JSON='{}'
    [ "$MONITOR_RC" != "0" ] || MONITOR_RC=74
  fi
  if [ "$OWNED_NAME_COUNT" = "3" ]; then
    if VERIFIED_CONTAINER_RECEIPTS_JSON=$(verify_container_receipts); then
      CONTAINER_RECEIPTS_JSON=$VERIFIED_CONTAINER_RECEIPTS_JSON
    elif [ "$MONITOR_RC" = "0" ]; then
      MONITOR_RC=76
    fi
  elif [ "$MONITOR_RC" = "0" ]; then
    MONITOR_RC=77
  fi
  if cleanup_owned_containers; then
    :
  else
    CLEANUP_RC=$?
  fi
  if ! assert_docker_empty && [ "$CLEANUP_RC" = "0" ]; then
    CLEANUP_RC=78
  fi
  if [ -f "$DECISION_HOST" ]; then
    cp "$DECISION_HOST" "$DECISION_RAW"
  fi
  if ! verify_smoke_runtime_inputs "$SCENARIO_CLASS" "$SEQUENCE" \
    "$EXPECTED_BLIND_PATCHED_SERVER_SHA256" after; then
    [ "$MONITOR_RC" != "0" ] || MONITOR_RC=79
  fi
  append_dose_finish "$ORDINAL" "$DOSE" "$SCHEDULE_ID" "$SCENARIO_CLASS" "$SEQUENCE" \
    "$END_NS" "$ELAPSED_NS" "$COMPOSE_RC" "$CAPTURE_RC" "$MONITOR_RC" \
    "$CLEANUP_RC" "$CONTAINER_RECEIPTS_JSON" "$PATCHED_SERVER_SHA"
  if [ "$COMPOSE_RC" != "0" ] || [ "$CAPTURE_RC" != "0" ] \
    || [ "$MONITOR_RC" != "0" ] || [ "$CLEANUP_RC" != "0" ] \
    || [ "$OWNED_NAME_COUNT" != "3" ] \
    || [ ! -s "$DECISION_RAW" ]; then
    append_abort "dose-failed:$DOSE:compose=$COMPOSE_RC:env=$CAPTURE_RC:monitor=$MONITOR_RC:cleanup=$CLEANUP_RC:owned_roles=$OWNED_NAME_COUNT:decision=$([ -s "$DECISION_RAW" ] && echo 1 || echo 0)"
    exit 1
  fi
  git -C "$STACK/UniAD" checkout HEAD -- inference/server.py
  if [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" \
    != "$BASELINE_EXPECTED" ]; then
    append_abort "server-restore-drift:$DOSE"
    exit 1
  fi
  SERVER_TOUCHED=0
  CURRENT_DOSE_CID_DIR=
  ORDINAL=$((ORDINAL + 1))
done <<< "$TARGET_PLAN"

if [ "$ORDINAL" != "4" ]; then
  append_abort "dose-count:$ORDINAL"
  exit 1
fi
if ! assert_docker_empty; then
  append_abort "final-docker-not-empty"
  exit 1
fi
if ! assert_gpu_compute_idle; then
  append_abort "final-gpu-not-idle"
  exit 1
fi
if ! assert_evaluator_idle; then
  append_abort "final-evaluator-not-idle"
  exit 1
fi
if ! verify_final_live_contract; then
  append_abort "final-live-contract-drift"
  exit 1
fi
python3 - "$EXECUTION_LOG" "$TOTAL_GPU_NS" <<'PY'
import json
import os
import sys
from pathlib import Path

event = {
    "event": "session_finish",
    "status": "complete",
    "exit_code": 0,
    "dose_invocation_count": 4,
    "analytic_episode_count": 0,
    "total_gpu_elapsed_ns": int(sys.argv[2]),
}
with Path(sys.argv[1]).open("a") as stream:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
PY

if ! python3 "$SMOKE_OUTPUT_ROOT/validate_smoke135.py" \
  --experiment-dir "$SMOKE_OUTPUT_ROOT" --raw-dir "$RAW_DIR" \
  --output "$SMOKE_OUTPUT_ROOT/smoke_receipt.remote.json"; then
  append_abort "raw-validator-rejected"
  exit 1
fi
if [ "$(sha256sum "$SCHEDULE_TARGET" | awk '{print $1}')" \
  != "$(sha256sum "$SMOKE_OUTPUT_ROOT/dose_schedules.json" | awk '{print $1}')" ]; then
  append_abort "post-smoke-schedule-drift"
  exit 1
fi
if [ "$SMOKE_STARTED" != "1" ] \
  || ! assert_docker_empty || ! assert_gpu_compute_idle || ! assert_evaluator_idle \
  || ! verify_final_live_contract; then
  append_abort "final-green-boundary-drift"
  exit 1
fi
if ! python3 - "$SCHEDULE_TARGET" "$SCHEDULE_TARGET_ID" "$STAGING_ROOT" \
  "$STAGING_ROOT_ID" <<'PY'
import shutil
import sys
from pathlib import Path

schedule = Path(sys.argv[1])
schedule_identity = sys.argv[2]
staging = Path(sys.argv[3])
staging_identity = sys.argv[4]
if (
    schedule != Path("/opt/sentinel-stack/UniAD/dose_schedules.json")
    or schedule.is_symlink()
    or not schedule.is_file()
    or schedule.resolve(strict=True) != schedule
    or f"{schedule.stat().st_dev}:{schedule.stat().st_ino}" != schedule_identity
    or staging != Path("/opt/sentinel-stack/UniAD/i135-smoke-staging")
    or staging.is_symlink()
    or not staging.is_dir()
    or staging.resolve(strict=True) != staging
    or f"{staging.stat().st_dev}:{staging.stat().st_ino}" != staging_identity
):
    raise SystemExit("owned smoke transient identity drift")
schedule.unlink()
shutil.rmtree(staging)
PY
then
  append_abort "owned-transient-cleanup-failed"
  exit 1
fi
touch "$SMOKE_OUTPUT_ROOT/I135_LIVE_SMOKE_DONE"
echo "I135_LIVE_SMOKE_DONE doses=4 nonanalytic=1 analytic_episodes=0 gpu_elapsed_ns=$TOTAL_GPU_NS evidence=$SMOKE_OUTPUT_ROOT lock_retained=$LOCK lock_identity=$SMOKE_LOCK_ID"
