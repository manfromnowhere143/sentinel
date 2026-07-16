#!/bin/bash
# Iteration 135: six arms x 20 scenario pairs, executed as 120 pair-major 20-run blocks.
# The launcher is inert unless the committed manifest explicitly authorizes launch and every
# provenance, environment, storage, idle, and resource gate passes on the execution host.

set -euo pipefail
exec 3>&1 4>&2

STACK=/opt/sentinel-stack
I135=$STACK/iter135
RUNNER_SOURCE=$I135/run_dose135.sh
MANIFEST_SOURCE=$I135/launch_manifest.json
MANIFEST=$MANIFEST_SOURCE
MISSION_STATE_SOURCE=$I135/MISSION_STATE.json
SCHED=$I135/dose_schedules.json
UNION_PATCH=$I135/server_patch_union_release.py
BLIND_PATCH=$I135/server_patch_blind_dose.py
LOCK=/var/lib/sentinel/i135-analytic.lock
PREFLIGHT_LOCK=/var/lock/sentinel-i135-preflight.lock
CANONICAL_LOG=/var/log/sentinel-i135.log
OUTPUT_ROOT=/datasets/nuscenes-full/sentinel-i135-outoutput
OUTPUT_ROOT_ID=
DATASET_RUNTIME_SNAPSHOT=
DATASET_RUNTIME_SNAPSHOT_ID=
DATASET_RUNTIME_SNAPSHOT_SHA=
DOCKER_RUNTIME_SNAPSHOT=
DOCKER_RUNTIME_SNAPSHOT_ID=
DOCKER_RUNTIME_SNAPSHOT_SHA=
BASELINE_SERVER_SHA=066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424
TOTAL_CEILING_SECONDS=$((110 * 60 * 60))
TERMINATION_RESERVE_SECONDS=300
EXPECTED_MANIFEST_SHA=${SENTINEL_LAUNCH_MANIFEST_SHA256:-}
BLOCK_PLAN=
BLOCK_PLAN_ID=
BLOCK_PLAN_FD_OPEN=0
MISSION_STATE_FD_OPEN=0
MISSION_STATE_BASELINE_SHA=
MISSION_STATE_BASELINE_ID=
MISSION_STATE_BASELINE_BYTES=
PREFLIGHT_LOCK_OWNED=0
ANALYTIC_LOCK_OWNED=0
ANALYTIC_LOCK_ID=
ANALYTIC_STARTED=0
CANONICAL_LOG_OWNED=0
CANONICAL_LOG_ID=
SCHEDULE_TARGET_OWNED=0
SCHEDULE_TARGET_ID=
DECISION_ROOT_OWNED=0
DECISION_ROOT_ID=
SERVER_TOUCHED=0
OWNED_CONTAINER_IDS=()
OWNED_CONTAINER_ROLES=()
ACTIVE_COMPOSE_PID=
ANALYTIC_WATCHDOG_PID=
ANALYTIC_WATCHDOG_READY_ID=
CONTAINER_CONTROL_ROOT=
CONTAINER_CONTROL_ROOT_ID=
CURRENT_BLOCK_CID_DIR=
CURRENT_BLOCK_ORDINAL=
DOCKER_BIN=
DOCKER_BIN_ID=
DOCKER_BIN_SHA=
DOCKER_WRAPPER_SHA=
DOCKER_CONTROL_TIMEOUT_SECONDS=5
CONTAINER_QUIET_SECONDS=5
CONTAINER_QUIESCENCE_CEILING_SECONDS=20

bounded_docker() {
  local BINARY=${DOCKER_BIN:-}
  if [ -z "$BINARY" ]; then
    BINARY=$(command -v docker) || return 127
  fi
  timeout --signal=TERM --kill-after=2s "$DOCKER_CONTROL_TIMEOUT_SECONDS" \
    "$BINARY" "$@"
}

compose_process_running() {
  local PID=$1 STATE
  STATE=$(ps -o stat= -p "$PID" 2>/dev/null | awk 'NR == 1 {print substr($1, 1, 1)}') \
    || return 1
  [ -n "$STATE" ] && [ "$STATE" != "Z" ]
}

terminate_compose_process() {
  local PID=$1 INDEX
  if compose_process_running "$PID"; then
    kill -TERM "$PID" >/dev/null 2>&1 || true
    for ((INDEX = 0; INDEX < 50; INDEX += 1)); do
      compose_process_running "$PID" || break
      sleep 0.1
    done
  fi
  if compose_process_running "$PID"; then
    kill -KILL "$PID" >/dev/null 2>&1 || true
    for ((INDEX = 0; INDEX < 50; INDEX += 1)); do
      compose_process_running "$PID" || break
      sleep 0.1
    done
  fi
  if compose_process_running "$PID"; then
    return 1
  fi
  wait "$PID" >/dev/null 2>&1 || true
}

monotonic_elapsed() {
  python3 - "$START_MONOTONIC_NS" <<'PY'
import sys
import time

print((time.monotonic_ns() - int(sys.argv[1])) // 1_000_000_000)
PY
}

verify_current_mission_state() {
  python3 - "$MISSION_STATE_SOURCE" "$MANIFEST_SOURCE" "$EXPECTED_MANIFEST_SHA" \
    "/proc/$$/fd/6" "$MISSION_STATE_BASELINE_ID" "$MISSION_STATE_BASELINE_SHA" <<'PY'
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

(
    state_path,
    manifest_path,
    expected_manifest_sha,
    pinned_descriptor_path,
    expected_state_identity,
    expected_state_sha,
) = sys.argv[1:]
state_path = Path(state_path).absolute()
manifest_path = Path(manifest_path).absolute()


def stable_physical_file(path: Path, label: str) -> tuple[bytes, os.stat_result]:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"{label} is not a physical regular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        chunks = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    identity = lambda row: (
        row.st_dev,
        row.st_ino,
        row.st_size,
        row.st_mtime_ns,
        row.st_ctime_ns,
        stat.S_IMODE(row.st_mode),
    )
    payload = b"".join(chunks)
    if (
        not stat.S_ISREG(before.st_mode)
        or identity(before) != identity(after)
        or identity(before) != identity(path_after)
        or len(payload) != before.st_size
    ):
        raise SystemExit(f"{label} changed while being read")
    return payload, before


def stable_pinned_file(path: str) -> tuple[bytes, os.stat_result]:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        before = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    pinned_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
        stat.S_IMODE(before.st_mode),
    )
    if (
        not stat.S_ISREG(before.st_mode)
        or pinned_identity
        != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            stat.S_IMODE(after.st_mode),
        )
        or len(payload) != before.st_size
    ):
        raise SystemExit("pinned mission state changed while being read")
    return payload, before


manifest_payload, _ = stable_physical_file(manifest_path, "launch manifest")
manifest_sha = hashlib.sha256(manifest_payload).hexdigest()
if manifest_sha != expected_manifest_sha:
    raise SystemExit(
        f"launch manifest changed at mission-state boundary: "
        f"{manifest_sha}!={expected_manifest_sha}"
    )
manifest = json.loads(manifest_payload)
if (
    manifest.get("schema") != "iter135.launch_manifest.v2"
    or manifest.get("verdict") != "I135_TOOLING_MANIFEST_OK"
    or manifest.get("launch_authorized") is not True
    or manifest.get("mission_phase") != "LAUNCH_AUTHORIZED"
):
    raise SystemExit("launch manifest is not the bound launch authority")

state_payload, state_row = stable_physical_file(state_path, "current mission state")
pinned_payload, pinned_row = stable_pinned_file(pinned_descriptor_path)
state_identity_tuple = (
    state_row.st_dev,
    state_row.st_ino,
    state_row.st_size,
    state_row.st_mtime_ns,
    state_row.st_ctime_ns,
    stat.S_IMODE(state_row.st_mode),
)
pinned_identity_tuple = (
    pinned_row.st_dev,
    pinned_row.st_ino,
    pinned_row.st_size,
    pinned_row.st_mtime_ns,
    pinned_row.st_ctime_ns,
    stat.S_IMODE(pinned_row.st_mode),
)
if state_identity_tuple != pinned_identity_tuple or state_payload != pinned_payload:
    raise SystemExit("current mission state no longer matches pinned launch authority")
state_identity = ":".join(str(value) for value in state_identity_tuple)
state_sha = hashlib.sha256(state_payload).hexdigest()
if expected_state_identity and state_identity != expected_state_identity:
    raise SystemExit(
        f"current mission state identity drift: {state_identity}!={expected_state_identity}"
    )
if expected_state_sha and state_sha != expected_state_sha:
    raise SystemExit(f"current mission state hash drift: {state_sha}!={expected_state_sha}")

state_receipt = manifest.get("mission_state")
if (
    not isinstance(state_receipt, dict)
    or set(state_receipt) != {"source_path", "sha256", "bytes"}
    or state_receipt.get("source_path") != "MISSION_STATE.json"
    or state_receipt.get("sha256") != state_sha
    or state_receipt.get("bytes") != len(state_payload)
):
    raise SystemExit("deployed mission state is not the launch manifest's bound current state")

state = json.loads(state_payload)
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
if set(state) != expected_state_fields:
    raise SystemExit("current mission state field set drift")
expected_workspace_boundary = {
    "isolated_from": "/Users/danielwahnich/workspace/aweb",
    "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
    "cross_workspace_access_requires_explicit_operator_request": True,
}
expected_next_program = {
    "iteration": 135,
    "name": "semantics-free placebo dose-response causal closure",
    "phase": "LAUNCH_AUTHORIZED",
    "authorized_actions": [
        "launch the exact hash-bound iteration-135 analytic manifest once on sentinel-gpu",
        "collect and commit raw proof after the single launch terminates, whether done or aborted",
        "publish partial evidence and PLACEBO_DOSE_INFRA_NULL after any aborted analytic launch",
    ],
    "forbidden_actions": [
        "relaunch or retry any iteration-135 analytic block after the first analytic block starts",
        (
            "run with any manifest, payload, environment, smoke, repository, image, GPU, storage, "
            "or idle-state drift"
        ),
        "run the analyzer before raw proof is committed",
    ],
}
if (
    state.get("schema") != "sentinel.mission_state.v1"
    or state.get("canonical_repository") != "/Users/danielwahnich/workspace/sentinel"
    or state.get("workspace_boundary") != expected_workspace_boundary
    or state.get("trunk") != "master"
    or state.get("current_completed_iteration") != 134
    or state.get("current_result")
    != "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
    or state.get("current_verdict") != "PLACEBO_HARM_OR_NULL"
    or state.get("run_state") != "IDLE"
    or state.get("active_hypothesis")
    != "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
    or state.get("next_program") != expected_next_program
):
    raise SystemExit("current mission state does not authorize this analytic launch")
expected_storage = {
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
if state.get("storage_gate") != expected_storage:
    raise SystemExit("current mission state storage contract drift")
print(state_sha, state_identity, len(state_payload))
PY
}

cleanup_containers() {
  local ALL_IDS_TEXT ID ROLE INDEX OBSERVED_ID REMOVE_RC=0 STILL_PRESENT
  local -a ALL_IDS REMAINING_IDS REMAINING_ROLES
  ALL_IDS=()
  REMAINING_IDS=()
  REMAINING_ROLES=()
  if [ "${#OWNED_CONTAINER_IDS[@]}" -eq 0 ]; then
    return 0
  fi
  ALL_IDS_TEXT=$(bounded_docker ps -aq --no-trunc) || return 1
  if [ -n "$ALL_IDS_TEXT" ]; then
    mapfile -t ALL_IDS <<<"$ALL_IDS_TEXT"
  else
    ALL_IDS=()
  fi
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX += 1)); do
    ID=${OWNED_CONTAINER_IDS[$INDEX]}
    ROLE=${OWNED_CONTAINER_ROLES[$INDEX]}
    STILL_PRESENT=0
    for OBSERVED_ID in "${ALL_IDS[@]}"; do
      if [ "$OBSERVED_ID" = "$ID" ]; then
        STILL_PRESENT=1
      fi
    done
    if [ "$STILL_PRESENT" = "0" ]; then
      continue
    fi
    if ! bounded_docker rm -f "$ID" >/dev/null 2>&1; then
      ALL_IDS_TEXT=$(bounded_docker ps -aq --no-trunc) || {
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
      continue
    fi
    ALL_IDS_TEXT=$(bounded_docker ps -aq --no-trunc) || {
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
  OWNED_CONTAINER_IDS=("${REMAINING_IDS[@]}")
  OWNED_CONTAINER_ROLES=("${REMAINING_ROLES[@]}")
  return "$REMOVE_RC"
}

cleanup() {
  if [ "$MISSION_STATE_FD_OPEN" = "1" ]; then
    exec 6>&- || true
    MISSION_STATE_FD_OPEN=0
  fi
  if [ -n "$ACTIVE_COMPOSE_PID" ]; then
    terminate_compose_process "$ACTIVE_COMPOSE_PID" \
      || echo "I135_CLEANUP_FAIL compose-process-termination:$ACTIVE_COMPOSE_PID"
    ACTIVE_COMPOSE_PID=
  fi
  if [ -n "$CURRENT_BLOCK_CID_DIR" ] \
    && declare -F capture_owned_containers >/dev/null 2>&1; then
    capture_owned_containers >/dev/null 2>&1 || true
  fi
  cleanup_containers || true
  if [ -n "$CURRENT_BLOCK_CID_DIR" ] \
    && declare -F verify_container_quiescence >/dev/null 2>&1; then
    verify_container_quiescence cleanup \
      || echo "I135_CLEANUP_FAIL container-quiescence"
  fi
  if [ -n "$BLOCK_PLAN" ]; then
    if [ "$BLOCK_PLAN_FD_OPEN" = "1" ]; then
      exec 7>&- || true
      BLOCK_PLAN_FD_OPEN=0
    fi
    CURRENT_BLOCK_PLAN_ID=$(stat -Lc '%d:%i' "$BLOCK_PLAN" 2>/dev/null || true)
    if [ -n "$BLOCK_PLAN_ID" ] && [ "$CURRENT_BLOCK_PLAN_ID" = "$BLOCK_PLAN_ID" ]; then
      rm -f "$BLOCK_PLAN" || true
    fi
  fi
  if [ "$CANONICAL_LOG_OWNED" = "1" ] && [ "$ANALYTIC_STARTED" = "0" ]; then
    exec 1>&3 2>&4 || true
    if [ -z "$CANONICAL_LOG_ID" ]; then
      CANONICAL_LOG_ID=$(stat -Lc '%d:%i' "/proc/$$/fd/9" 2>/dev/null || true)
    fi
    CURRENT_LOG_ID=$(stat -Lc '%d:%i' "$CANONICAL_LOG" 2>/dev/null || true)
    if [ -n "$CANONICAL_LOG_ID" ] && [ "$CURRENT_LOG_ID" = "$CANONICAL_LOG_ID" ]; then
      rm -f "$CANONICAL_LOG" || true
    fi
    exec 9>&- || true
    CANONICAL_LOG_OWNED=0
  fi
  if [ "$ANALYTIC_STARTED" = "0" ] && [ "$DECISION_ROOT_OWNED" = "1" ]; then
    python3 - "$DECISION_ROOT" "$DECISION_ROOT_ID" <<'PY' >/dev/null 2>&1 || true
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_identity = sys.argv[2]
expected = Path("/opt/sentinel-stack/UniAD/i135-decisions")
if (
    root == expected
    and not root.is_symlink()
    and root.resolve(strict=True) == root
    and f"{root.stat().st_dev}:{root.stat().st_ino}" == expected_identity
):
    shutil.rmtree(root)
PY
    DECISION_ROOT_OWNED=0
  fi
  if [ "$ANALYTIC_STARTED" = "0" ] && [ "$SCHEDULE_TARGET_OWNED" = "1" ]; then
    python3 - "$SCHEDULE_TARGET" "$SCHEDULE_TARGET_ID" <<'PY' >/dev/null 2>&1 || true
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_identity = sys.argv[2]
expected = Path("/opt/sentinel-stack/UniAD/dose_schedules.json")
if (
    path == expected
    and not path.is_symlink()
    and path.resolve(strict=True) == path
    and f"{path.stat().st_dev}:{path.stat().st_ino}" == expected_identity
):
    path.unlink()
PY
    SCHEDULE_TARGET_OWNED=0
  fi
  if [ "$SERVER_TOUCHED" = "1" ]; then
    CURRENT_SERVER_SHA=$(sha256sum "$STACK/UniAD/inference/server.py" 2>/dev/null \
      | awk '{print $1}' || true)
    case "$CURRENT_SERVER_SHA" in
      "$BASELINE_SERVER_SHA")
        SERVER_TOUCHED=0
        ;;
      8f6ed6a9bbeefc93b0bf7ee2f15b4843921475a0eded3719db59a8ad38538056|b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf)
        if timeout --signal=TERM --kill-after=5s 15s \
          git -C "$STACK/UniAD" checkout HEAD -- inference/server.py >/dev/null 2>&1 \
          && [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" \
            = "$BASELINE_SERVER_SHA" ]; then
          SERVER_TOUCHED=0
        else
          echo "I135_CLEANUP_FAIL server-baseline-restore"
        fi
        ;;
      *)
        echo "I135_CLEANUP_FAIL server-identity-unknown:$CURRENT_SERVER_SHA"
        ;;
    esac
  fi
  if [ "$ANALYTIC_LOCK_OWNED" = "1" ] && [ "$ANALYTIC_STARTED" = "0" ]; then
    CURRENT_LOCK_ID=$(stat -Lc '%d:%i' "$LOCK" 2>/dev/null || true)
    if [ -n "$ANALYTIC_LOCK_ID" ] && [ "$CURRENT_LOCK_ID" = "$ANALYTIC_LOCK_ID" ]; then
      rm -f "$LOCK" || true
    fi
    ANALYTIC_LOCK_OWNED=0
  fi
  if [ -n "$ANALYTIC_WATCHDOG_PID" ]; then
    terminate_compose_process "$ANALYTIC_WATCHDOG_PID" || true
    ANALYTIC_WATCHDOG_PID=
  fi
  if [ -n "$CONTAINER_CONTROL_ROOT" ]; then
    python3 - "$CONTAINER_CONTROL_ROOT" "$CONTAINER_CONTROL_ROOT_ID" <<'PY' \
      >/dev/null 2>&1 || true
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_identity = sys.argv[2]
if (
    root.parent == Path("/tmp")
    and root.name.startswith("sentinel-i135-control.")
    and not root.is_symlink()
    and root.is_dir()
    and root.resolve(strict=True) == root
    and f"{root.stat().st_dev}:{root.stat().st_ino}" == expected_identity
):
    shutil.rmtree(root)
PY
    CONTAINER_CONTROL_ROOT=
  fi
  if [ "$PREFLIGHT_LOCK_OWNED" = "1" ]; then
    flock -u 8 >/dev/null 2>&1 || true
    exec 8>&- || true
    PREFLIGHT_LOCK_OWNED=0
  fi
}

abort() {
  echo "I135_ABORT $*"
  if [ "$CANONICAL_LOG_OWNED" = "1" ] && [ "$ANALYTIC_STARTED" = "0" ]; then
    echo "I135_ABORT $*" >&4
  fi
  exit 1
}

for REQUIRED_COMMAND in awk chmod cp date docker find findmnt flock git grep mkdir mktemp nvidia-smi ps python3 readlink rm rmdir sha256sum sleep stat timeout tr wc; do
  if ! command -v "$REQUIRED_COMMAND" >/dev/null 2>&1; then
    echo "I135_ABORT $REQUIRED_COMMAND-missing" >&2
    exit 1
  fi
done
DOCKER_BIN=$(readlink -f "$(command -v docker)") || {
  echo "I135_ABORT docker-binary-realpath" >&2
  exit 1
}
if [ ! -f "$DOCKER_BIN" ] || [ ! -x "$DOCKER_BIN" ] || [ -L "$DOCKER_BIN" ]; then
  echo "I135_ABORT docker-binary-physical:$DOCKER_BIN" >&2
  exit 1
fi
DOCKER_BIN_ID=$(stat -Lc '%d:%i' "$DOCKER_BIN") || {
  echo "I135_ABORT docker-binary-identity" >&2
  exit 1
}
DOCKER_BIN_SHA=$(sha256sum "$DOCKER_BIN" | awk '{print $1}') || {
  echo "I135_ABORT docker-binary-sha256" >&2
  exit 1
}
EXECUTING_RUNNER_RECEIPT=$(python3 - "$RUNNER_SOURCE" "${BASH_SOURCE[0]}" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

canonical = Path(sys.argv[1])
executing = Path(sys.argv[2]).absolute()
if (
    canonical.is_symlink()
    or not canonical.is_file()
    or canonical.resolve(strict=True) != canonical
    or executing.is_symlink()
    or not executing.is_file()
    or executing.resolve(strict=True) != canonical
):
    raise SystemExit("executing launcher is not the canonical physical source")
canonical_stat = canonical.stat()
executing_stat = executing.stat()
if (canonical_stat.st_dev, canonical_stat.st_ino) != (
    executing_stat.st_dev,
    executing_stat.st_ino,
):
    raise SystemExit("executing launcher inode differs from canonical source")
descriptor = os.open(canonical, os.O_RDONLY | os.O_NOFOLLOW)
try:
    before = os.fstat(descriptor)
    digest = hashlib.sha256()
    byte_count = 0
    with os.fdopen(descriptor, "rb", closefd=False) as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
    after = os.fstat(descriptor)
finally:
    os.close(descriptor)
identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
if identity_before != identity_after or byte_count != before.st_size:
    raise SystemExit("executing launcher changed while hashing")
print(digest.hexdigest(), f"{before.st_dev}:{before.st_ino}", byte_count)
PY
) || {
  echo "I135_ABORT executing-runner-binding" >&2
  exit 1
}
read -r EXECUTING_RUNNER_SHA EXECUTING_RUNNER_ID EXECUTING_RUNNER_BYTES \
  <<<"$EXECUTING_RUNNER_RECEIPT"
if ! [[ "$EXECUTING_RUNNER_SHA" =~ ^[0-9a-f]{64}$ \
  && "$EXECUTING_RUNNER_ID" =~ ^[0-9]+:[0-9]+$ \
  && "$EXECUTING_RUNNER_BYTES" =~ ^[1-9][0-9]*$ ]]; then
  echo "I135_ABORT executing-runner-receipt" >&2
  exit 1
fi
if [ -e "$LOCK" ]; then
  echo "I135_ABORT lock-exists:$LOCK" >&2
  exit 1
fi
if [ -e "$CANONICAL_LOG" ]; then
  echo "I135_ABORT canonical-log-exists:$CANONICAL_LOG" >&2
  exit 1
fi
python3 - "$PREFLIGHT_LOCK" <<'PY' || {
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.parent.resolve(strict=True).is_dir():
    raise SystemExit("preflight lock parent is not a directory")
if path.is_symlink() or (path.exists() and not path.is_file()):
    raise SystemExit("preflight lock path is not a physical regular file")
PY
  echo "I135_ABORT preflight-lock-path:$PREFLIGHT_LOCK" >&2
  exit 1
}
if [ -e "$PREFLIGHT_LOCK" ]; then
  if ! exec 8<> "$PREFLIGHT_LOCK"; then
    echo "I135_ABORT preflight-lock-open:$PREFLIGHT_LOCK" >&2
    exit 1
  fi
else
  set -o noclobber
  if ! exec 8> "$PREFLIGHT_LOCK"; then
    set +o noclobber
    echo "I135_ABORT preflight-lock-create:$PREFLIGHT_LOCK" >&2
    exit 1
  fi
  set +o noclobber
fi
PREFLIGHT_LOCK_FD_ID=$(stat -Lc '%d:%i' "/proc/$$/fd/8") || {
  exec 8>&-
  echo "I135_ABORT preflight-lock-fd-identity:$PREFLIGHT_LOCK" >&2
  exit 1
}
PREFLIGHT_LOCK_PATH_ID=$(stat -Lc '%d:%i' "$PREFLIGHT_LOCK") || {
  exec 8>&-
  echo "I135_ABORT preflight-lock-path-identity:$PREFLIGHT_LOCK" >&2
  exit 1
}
if [ -L "$PREFLIGHT_LOCK" ] || [ ! -f "$PREFLIGHT_LOCK" ] \
  || [ "$PREFLIGHT_LOCK_PATH_ID" != "$PREFLIGHT_LOCK_FD_ID" ]; then
  exec 8>&-
  echo "I135_ABORT preflight-lock-open-race:$PREFLIGHT_LOCK" >&2
  exit 1
fi
if ! flock -n 8; then
  exec 8>&-
  echo "I135_ABORT preflight-lock-unavailable:$PREFLIGHT_LOCK" >&2
  exit 1
fi
PREFLIGHT_LOCK_OWNED=1
trap cleanup EXIT

if [ -L "$MISSION_STATE_SOURCE" ] || [ ! -f "$MISSION_STATE_SOURCE" ]; then
  abort "mission-state-not-physical:$MISSION_STATE_SOURCE"
fi
if ! exec 6< "$MISSION_STATE_SOURCE"; then
  abort "mission-state-pinned-open:$MISSION_STATE_SOURCE"
fi
MISSION_STATE_FD_OPEN=1
MISSION_STATE_BINDING=$(verify_current_mission_state) \
  || abort "mission-state-launch-authority"
read -r MISSION_STATE_BASELINE_SHA MISSION_STATE_BASELINE_ID \
  MISSION_STATE_BASELINE_BYTES <<<"$MISSION_STATE_BINDING"
if ! [[ "$MISSION_STATE_BASELINE_SHA" =~ ^[0-9a-f]{64}$ \
  && "$MISSION_STATE_BASELINE_ID" =~ ^([0-9]+:){5}[0-9]+$ \
  && "$MISSION_STATE_BASELINE_BYTES" =~ ^[1-9][0-9]*$ ]]; then
  abort "mission-state-binding-output:$MISSION_STATE_BINDING"
fi

echo "I135_PREFLIGHT_INVOCATION at=$(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ manifest_sha256=${EXPECTED_MANIFEST_SHA:-missing}"
echo "I135_EXECUTING_RUNNER_OK sha256=$EXECUTING_RUNNER_SHA id=$EXECUTING_RUNNER_ID bytes=$EXECUTING_RUNNER_BYTES"
echo "I135_MISSION_STATE_OK sha256=$MISSION_STATE_BASELINE_SHA id=$MISSION_STATE_BASELINE_ID bytes=$MISSION_STATE_BASELINE_BYTES"

CONTAINER_IDS=$(bounded_docker ps -aq --no-trunc) || abort "container-probe-before-launch"
if [ -n "$CONTAINER_IDS" ]; then
  abort "containers-present-before-launch"
fi
GPU_NAMES_TEXT=$(nvidia-smi --query-gpu=name --format=csv,noheader) \
  || abort "gpu-topology-probe-before-launch"
mapfile -t GPU_NAMES <<<"$GPU_NAMES_TEXT"
if [ "${#GPU_NAMES[@]}" != "1" ] || [ "${GPU_NAMES[0]}" != "NVIDIA L4" ]; then
  abort "live-gpu-topology:${GPU_NAMES[*]:-none}"
fi
GPU_COMPUTE_PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader \
  | tr -d '[:space:]') || abort "gpu-process-probe-before-launch"
if [ -n "$GPU_COMPUTE_PIDS" ]; then
  abort "live-gpu-process-present"
fi
python3 - <<'PY' || abort "evaluator-process-present"
import os
import re
import subprocess

patterns = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
rows = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines()
matches = []
for row in rows:
    pid_text, _, command = row.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid in {os.getpid(), os.getppid()}:
        continue
    if patterns.search(command):
        matches.append(f"{pid}:{command}")
if matches:
    print("I135_LIVE_EVALUATOR_PROCESS_FAIL", *matches, sep="\n - ")
    raise SystemExit(1)
PY

# Recompute the frozen execution plan and verify every launch-bound local/remote receipt.
python3 - "$MANIFEST" "$EXPECTED_MANIFEST_SHA" "$EXECUTING_RUNNER_SHA" \
  "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" <<'PY' \
  || abort "preflight"
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

manifest_path = Path(sys.argv[1]).absolute()
expected_manifest_sha256 = sys.argv[2]
expected_executing_runner_sha256 = sys.argv[3]
docker_binary = Path(sys.argv[4])
expected_docker_identity = sys.argv[5]
expected_docker_sha256 = sys.argv[6]
problems = []
environment_devices = None

try:
    if (
        docker_binary.is_symlink()
        or not docker_binary.is_file()
        or docker_binary.resolve(strict=True) != docker_binary
        or f"{docker_binary.stat().st_dev}:{docker_binary.stat().st_ino}"
        != expected_docker_identity
        or hashlib.sha256(docker_binary.read_bytes()).hexdigest()
        != expected_docker_sha256
    ):
        problems.append("docker-client-binary-drift")
except OSError as error:
    problems.append(f"docker-client-binary:{type(error).__name__}:{error}")


def parse_canonical_utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo != timezone.utc or parsed.isoformat().replace("+00:00", "Z") != value:
        return None
    return parsed

if (
    manifest_path.is_symlink()
    or not manifest_path.is_file()
    or manifest_path.resolve(strict=True) != manifest_path
):
    raise SystemExit(f"manifest is not a regular non-symlink file: {manifest_path}")
before = manifest_path.stat()
manifest_payload = manifest_path.read_bytes()
after = manifest_path.stat()
identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
if identity_before != identity_after or len(manifest_payload) != before.st_size:
    raise SystemExit("manifest changed while being read")
manifest = json.loads(manifest_payload)
actual_manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
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
if len(expected_manifest_sha256) != 64 or any(
    character not in "0123456789abcdef" for character in expected_manifest_sha256
):
    problems.append("independent-manifest-sha256:missing-or-malformed")
elif actual_manifest_sha256 != expected_manifest_sha256:
    problems.append(
        f"independent-manifest-sha256:{actual_manifest_sha256}!={expected_manifest_sha256}"
    )
if manifest.get("schema") != "iter135.launch_manifest.v2":
    problems.append(f"manifest-schema:{manifest.get('schema')}")
if manifest.get("verdict") != "I135_TOOLING_MANIFEST_OK":
    problems.append(f"manifest-verdict:{manifest.get('verdict')}")
if manifest.get("launch_authorized") is not True:
    problems.append("launch-authorized:false")
if manifest.get("problem_count") != 0 or manifest.get("problems") != []:
    problems.append("manifest-problem-metadata")
if manifest.get("missing_artifacts") != []:
    problems.append(f"manifest-missing-artifacts:{manifest.get('missing_artifacts')}")
if manifest.get("mission_phase") != "LAUNCH_AUTHORIZED":
    problems.append(f"manifest-mission-phase:{manifest.get('mission_phase')}")
if manifest.get("planned_blocks") != 120:
    problems.append(f"planned-blocks:{manifest.get('planned_blocks')}")
if manifest.get("planned_episodes") != 2400:
    problems.append(f"planned-episodes:{manifest.get('planned_episodes')}")
design = manifest.get("design")
if not isinstance(design, dict):
    problems.append("design:missing")
else:
    if design.get("retry_policy") != "no_automatic_retry_abort_on_first_block_failure":
        problems.append(f"design:retry-policy:{design.get('retry_policy')}")
    if design.get("allowed_retries") != 0:
        problems.append(f"design:allowed-retries:{design.get('allowed_retries')}")

classes = {
    "stationary": ["0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"],
    "frontal": ["0103", "0106", "0110", "0346", "0923"],
    "side": ["0103", "0108", "0110", "0278", "0921"],
}
arms = [
    "off_baseline",
    "released_union_semantic_reference",
    "blind_0_5x",
    "blind_1_0x",
    "blind_1_5x",
    "blind_2_0x",
]
expected_design = {
    "iteration": 135,
    "execution_unit": "pair-major-20-run-arm-block",
    "pair_count": 20,
    "arms": arms,
    "arm_config": {
        "off_baseline": {
            "patch": "server_patch_union_release.py",
            "sentinel_enabled": "0",
            "dose_id": None,
        },
        "released_union_semantic_reference": {
            "patch": "server_patch_union_release.py",
            "sentinel_enabled": "1",
            "dose_id": None,
        },
        **{
            dose: {
                "patch": "server_patch_blind_dose.py",
                "sentinel_enabled": "1",
                "dose_id": dose,
            }
            for dose in arms[2:]
        },
    },
    "run_indices": list(range(20)),
    "planned_blocks": 120,
    "planned_episodes": 2400,
    "frozen_union_parameters": {
        "SENTINEL_MIN_SCORE": "0.3",
        "SENTINEL_MAXGAP": "30",
        "SENTINEL_CPA_MARGIN": "1.5",
        "SENTINEL_TTC": "2.5",
        "SENTINEL_MIN_CLOSING": "3",
        "SENTINEL_RELEASE_K": "4",
    },
    "done_marker": "I135_DOSE_DONE",
    "gpu": "single NVIDIA L4",
    "absolute_gpu_hour_ceiling": 110,
    "retry_policy": "no_automatic_retry_abort_on_first_block_failure",
    "allowed_retries": 0,
}
if design != expected_design:
    problems.append("design:contract-drift")
expected_pair_order = [
    f"{scenario_class}/{sequence}"
    for scenario_class, sequences in classes.items()
    for sequence in sequences
]
if manifest.get("pair_order") != expected_pair_order:
    problems.append("pair-order-drift")
expected_blocks = []
expected_cells = []
block_ordinal = 0
cell_ordinal = 0
pair_index = 0
for scenario_class, sequences in classes.items():
    for sequence in sequences:
        rotation = pair_index % len(arms)
        for temporal_position, arm_id in enumerate(arms[rotation:] + arms[:rotation]):
            expected_blocks.append(
                {
                    "ordinal": block_ordinal,
                    "pair_index": pair_index,
                    "temporal_position": temporal_position,
                    "arm_id": arm_id,
                    "scenario_class": scenario_class,
                    "sequence": sequence,
                    "run_indices": list(range(20)),
                }
            )
            for run_index in range(20):
                expected_cells.append(
                    {
                        "ordinal": cell_ordinal,
                        "block_ordinal": block_ordinal,
                        "pair_index": pair_index,
                        "temporal_position": temporal_position,
                        "arm_id": arm_id,
                        "scenario_class": scenario_class,
                        "sequence": sequence,
                        "run_index": run_index,
                    }
                )
                cell_ordinal += 1
            block_ordinal += 1
        pair_index += 1

if manifest.get("execution_blocks") != expected_blocks:
    problems.append("execution-block-order-drift")
if manifest.get("execution_cells") != expected_cells:
    problems.append("execution-cell-order-drift")

gates = manifest.get("gates")
expected_gate_ids = {
    "g0_preregistration",
    "g1_provenance",
    "g2_released_behavior",
    "g3_schedule_integrity",
    "g4_semantic_leak",
    "g5_live_smoke",
    "g7_dataset_provenance",
    "g8_storage_environment",
    "g9_resource_plan",
    "execution_plan",
    "execution_consumers",
    "tooling_verification",
    "mission_state",
}
if not isinstance(gates, dict) or set(gates) != expected_gate_ids:
    problems.append(f"gates:set:{sorted(gates) if isinstance(gates, dict) else None}")
else:
    for gate_id, receipt in sorted(gates.items()):
        passed = receipt.get("passed") if isinstance(receipt, dict) else receipt
        if passed is not True:
            problems.append(f"gate:{gate_id}:not-passed")

payload_root = manifest_path.parent
hash_bound = manifest.get("hash_bound_files")
if not isinstance(hash_bound, dict) or not hash_bound:
    problems.append("hash-bound-files:missing")
else:
    required_payloads = {
        "HYPOTHESIS.md",
        "extract_union_windows.py",
        "generate_nested_dose_schedules.py",
        "dose_schedules.json",
        "server_patch_union_release.py",
        "server_patch_blind_dose.py",
        "analyze_dose135.py",
        "collect_proof135.py",
        "run_dose135.sh",
        "run_smoke135.sh",
        "validate_smoke135.py",
        "capture_environment135.py",
        "verify_tooling135.py",
        "tooling_verification_receipt.json",
        "patch_compose_dose_env.py",
        "make_launch_manifest.py",
        "env_receipts.json",
        "smoke-evidence/smoke_receipt.json",
    }
    smoke_raw_names = {
        "smoke-evidence/raw/execution.jsonl",
        "smoke-evidence/raw/pre_smoke_manifest.json",
        "smoke-evidence/raw/environment_receipt.json",
        *{
            f"smoke-evidence/raw/{dose}.{suffix}"
            for dose in arms[2:]
            for suffix in ("decisions.jsonl", "model-env.bin", "compose.log")
        },
    }
    expected_hash_bound = required_payloads | smoke_raw_names
    if set(hash_bound) != expected_hash_bound:
        problems.append(
            "hash-bound-file-set:"
            f"missing={sorted(expected_hash_bound - set(hash_bound))}:"
            f"extra={sorted(set(hash_bound) - expected_hash_bound)}"
        )
    for name, receipt in sorted(hash_bound.items()):
        if not isinstance(receipt, dict) or set(receipt) != {"source_path", "sha256", "bytes"}:
            problems.append(f"payload-receipt-schema:{name}")
            continue
        source_path = receipt.get("source_path")
        if (
            not isinstance(source_path, str)
            or not source_path
            or Path(source_path).is_absolute()
            or ".." in Path(source_path).parts
        ):
            problems.append(f"payload-source-path:{name}:{source_path}")
        path = (payload_root / name).absolute()
        try:
            resolved_path = path.resolve(strict=True)
            path.relative_to(payload_root)
        except (OSError, ValueError):
            problems.append(f"payload-outside-root:{name}")
            continue
        if path.is_symlink() or resolved_path != path or not path.is_file():
            problems.append(f"payload-missing:{name}")
            continue
        if type(receipt.get("bytes")) is not int or path.stat().st_size != receipt["bytes"]:
            problems.append(f"payload-bytes:{name}:{path.stat().st_size}!={receipt.get('bytes')}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = receipt.get("sha256")
        if actual != expected:
            problems.append(f"payload-sha:{name}:{actual}!={expected}")
    runner_receipt = hash_bound.get("run_dose135.sh")
    if (
        not isinstance(runner_receipt, dict)
        or runner_receipt.get("sha256") != expected_executing_runner_sha256
    ):
        problems.append("executing-runner-manifest-binding")
    if manifest.get("smoke_receipt") != hash_bound.get(
        "smoke-evidence/smoke_receipt.json"
    ):
        problems.append("smoke-receipt:hash-binding-drift")
    if manifest.get("tooling_verification_receipt") != hash_bound.get(
        "tooling_verification_receipt.json"
    ):
        problems.append("tooling-verification-receipt:hash-binding-drift")

mission_state_receipt = manifest.get("mission_state")
if (
    not isinstance(mission_state_receipt, dict)
    or set(mission_state_receipt) != {"source_path", "sha256", "bytes"}
    or mission_state_receipt.get("source_path") != "MISSION_STATE.json"
    or type(mission_state_receipt.get("bytes")) is not int
    or mission_state_receipt["bytes"] <= 0
    or not isinstance(mission_state_receipt.get("sha256"), str)
    or len(mission_state_receipt["sha256"]) != 64
    or any(character not in "0123456789abcdef" for character in mission_state_receipt["sha256"])
):
    problems.append("mission-state-receipt:contract")

remote_artifacts = manifest.get("remote_artifacts")
expected_remote_paths = {
    "compose_script": "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
    "uniad_server_baseline": "/opt/sentinel-stack/UniAD/inference/server.py",
    "uniad_runner": "/opt/sentinel-stack/UniAD/inference/runner.py",
    "uniad_inference_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/stage2_e2e/inference_e2e.py"
    ),
    "uniad_base_config": "/opt/sentinel-stack/UniAD/projects/configs/stage2_e2e/base_e2e.py",
    "uniad_dataset_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/_base_/datasets/nus-3d.py"
    ),
    "uniad_runtime_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/_base_/default_runtime.py"
    ),
    "checkpoint": "/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth",
    "shim": (
        "/opt/sentinel-stack/UniAD/projects/mmdet3d_plugin/uniad/detectors/"
        "uniad_track.py"
    ),
    "neuroncap_dockerfile": "/opt/sentinel-stack/NeuroNCAP/docker/Dockerfile",
    "neuroncap_main": "/opt/sentinel-stack/NeuroNCAP/main.py",
    "neuroncap_engine": "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/engine.py",
    "neuroncap_evaluator": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/components/evaluator.py"
    ),
    "neuroncap_scenario": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/components/scenario.py"
    ),
    "neuroncap_config": "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/utils/config.py",
    "neuroncap_collision": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/evaluation/collision.py"
    ),
    "neuroncap_target_recall": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/evaluation/target_recall.py"
    ),
    "neurad_dockerfile": "/opt/sentinel-stack/neurad-studio/Dockerfile",
    "neurad_dockerfile_backup": "/opt/sentinel-stack/neurad-studio/Dockerfile.bak",
    "neurad_main": (
        "/opt/sentinel-stack/neurad-studio/nerfstudio/scripts/closed_loop/main.py"
    ),
}
for scenario_class, sequences in classes.items():
    for sequence in sequences:
        role = f"scenario:{scenario_class}/{sequence}"
        expected_remote_paths[role] = (
            f"/opt/sentinel-stack/NeuroNCAP/scenarios/{scenario_class}/{sequence}.yaml"
        )
for sequence in sorted({sequence for sequences in classes.values() for sequence in sequences}):
    renderer_root = f"/opt/sentinel-stack/neurad-studio/checkpoints/{sequence}"
    expected_remote_paths[f"renderer:{sequence}:config"] = f"{renderer_root}/config.yml"
    expected_remote_paths[f"renderer:{sequence}:transforms"] = (
        f"{renderer_root}/dataparser_transforms.json"
    )
    expected_remote_paths[f"renderer:{sequence}:checkpoint"] = (
        f"{renderer_root}/step-000150000.ckpt"
    )
if len(expected_remote_paths) != 82:
    problems.append(f"remote-contract-role-count:{len(expected_remote_paths)}!=82")


def stable_sha256(path: Path) -> tuple[str, int]:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(8 * 1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    identity_path = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if identity_before != identity_after or identity_before != identity_path or size != before.st_size:
        raise RuntimeError(f"file changed while hashing: {path}")
    return digest.hexdigest(), size


remote_rows = {}
if not isinstance(remote_artifacts, list):
    problems.append("remote-artifacts:missing")
else:
    for index, receipt in enumerate(remote_artifacts):
        if not isinstance(receipt, dict) or set(receipt) != {"role", "path", "sha256", "bytes"}:
            problems.append(f"remote-artifact-schema:{index}")
            continue
        role = receipt.get("role")
        if not isinstance(role, str) or role in remote_rows:
            problems.append(f"remote-artifact-role:{index}:{role}")
            continue
        remote_rows[role] = receipt
    if set(remote_rows) != set(expected_remote_paths):
        problems.append(
            "remote-artifacts:set:"
            f"missing={sorted(set(expected_remote_paths) - set(remote_rows))}:"
            f"extra={sorted(set(remote_rows) - set(expected_remote_paths))}"
        )
    for role, expected_path in sorted(expected_remote_paths.items()):
        receipt = remote_rows.get(role)
        if not isinstance(receipt, dict):
            continue
        if receipt.get("path") != expected_path:
            problems.append(f"remote-path:{role}:{receipt.get('path')}!={expected_path}")
            continue
        path = Path(expected_path)
        try:
            if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
                problems.append(f"remote-not-physical-regular-file:{role}:{path}")
                continue
            actual, byte_count = stable_sha256(path)
        except (OSError, RuntimeError) as error:
            problems.append(f"remote-read:{role}:{type(error).__name__}:{error}")
            continue
        if type(receipt.get("bytes")) is not int or byte_count != receipt["bytes"]:
            problems.append(f"remote-bytes:{role}:{byte_count}!={receipt.get('bytes')}")
        if actual != receipt.get("sha256"):
            problems.append(f"remote-sha:{role}:{actual}!={receipt.get('sha256')}")

environment = manifest.get("environment_receipts")
if not isinstance(environment, dict):
    problems.append("environment-receipts:missing")
else:
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
        "docker_image_ids",
    }
    if set(environment) != expected_environment_fields:
        problems.append("environment-receipts:field-set")
    if environment.get("schema") != "iter135.environment_receipts.v2":
        problems.append(f"environment-receipts:schema:{environment.get('schema')}")
    if environment.get("verdict") != "I135_ENVIRONMENT_PREFLIGHT_OK":
        problems.append(f"environment-receipts:verdict:{environment.get('verdict')}")
    if environment.get("problem_count") != 0 or environment.get("problems") != []:
        problems.append("environment-receipts:problems")
    captured_at = parse_canonical_utc(environment.get("captured_at_utc"))
    capture_started_at = parse_canonical_utc(environment.get("capture_started_at_utc"))
    if captured_at is None:
        problems.append("environment-receipts:captured-at")
    if (
        capture_started_at is None
        or captured_at is None
        or capture_started_at > captured_at
    ):
        problems.append("environment-receipts:capture-started-at")
    environment_path = payload_root / "env_receipts.json"
    try:
        environment_file = json.loads(environment_path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"environment-file:{type(error).__name__}:{error}")
    else:
        embedded_environment = {
            key: value for key, value in environment.items() if key != "docker_image_ids"
        }
        if environment_file != embedded_environment:
            problems.append("environment-file:embedded-receipt-drift")

    dataset = manifest.get("dataset_receipt")
    environment_dataset = environment.get("dataset")
    expected_archives = {
        "v1.0-trainval_meta.tgz": (
            "db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b",
            461678030,
        ),
        "v1.0-trainval01_blobs.tgz": (
            "fee4316c55f0780532819ea1b01f347b2ad964303c93477cc815f8191b126171",
            31579122687,
        ),
        "v1.0-trainval02_blobs.tgz": (
            "292301394af9d4a8eb62cee41b3b3031c6cad78e2b39bf63a91bd6d3b7592373",
            30134721083,
        ),
        "v1.0-trainval03_blobs.tgz": (
            "9e6e7c949fbea971321112757dfcff757add646078393c191981a0a49d5f483c",
            29872679856,
        ),
        "v1.0-trainval04_blobs.tgz": (
            "6927f765f8555ce6f901ed2763569bd860b33ad5e076709bbc6c4cc8a51ffc76",
            32075538096,
        ),
        "v1.0-trainval05_blobs.tgz": (
            "ea8d886bc79be30d02e9552d229aaa0843ecffccaaff6606644540b4183f605f",
            28191611840,
        ),
        "v1.0-trainval06_blobs.tgz": (
            "26e3dfff85d8ef6354d4b9dc0a9d8b3f0ebd8719b6d84eac5841fa31b97b8deb",
            27516468993,
        ),
        "v1.0-trainval07_blobs.tgz": (
            "70287e2d65386bce2d67001ef56f5c0abdd3dd95d1ec404c3e00a39208fa60b7",
            29534216608,
        ),
        "v1.0-trainval08_blobs.tgz": (
            "744080381fcfbca3e3ee8d20c5340dce4b5b7fae8020a7e90338ec98b20802c1",
            30275496199,
        ),
        "v1.0-trainval09_blobs.tgz": (
            "ca3aba09dc63cd22fdc455959f3aea99e0f6ed4de822c8c3f5f96f0efa372ec5",
            33517622306,
        ),
        "v1.0-trainval10_blobs.tgz": (
            "046aa7c5ff2cab63a25eaa6210e00bd8197f835e5324457d305a2a16a262f57a",
            41727447974,
        ),
    }
    expected_metadata = {
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
    expected_maps = {
        "36092f0b03a857c6a3403e25b4b7aab3.png",
        "37819e65e09e5547b8a3ceaefba56bb2.png",
        "53992ee3023e5494b90c316c183be829.png",
        "93406b464a165eaba6d9de76ca09f5da.png",
    }
    expected_dataset_fields = {
        "schema",
        "contract_sha256",
        "proof_basis",
        "identity",
        "archives",
        "metadata_json",
        "map_anchors",
        "receipt_payload_sha256",
    }
    if not isinstance(dataset, dict) or set(dataset) != expected_dataset_fields:
        problems.append("dataset-receipt:field-set")
        dataset = dataset if isinstance(dataset, dict) else {}
    if dataset != environment_dataset:
        problems.append("dataset-receipt:environment-link")
    if dataset.get("schema") != "iter135.nuscenes_dataset_receipt.v1":
        problems.append("dataset-receipt:schema")
    if dataset.get("contract_sha256") != (
        "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b"
    ):
        problems.append("dataset-receipt:contract-sha256")
    expected_proof_basis = {
        "iteration": 28,
        "result_path": "experiments/iter28_nuscenes_trainval_staging/RESULT.md",
        "receipt_directory": (
            "experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads"
        ),
        "archive_count": 11,
        "archive_total_bytes": 314886603672,
    }
    if dataset.get("proof_basis") != expected_proof_basis:
        problems.append("dataset-receipt:proof-basis")
    canonical_dataset_payload = dict(dataset)
    declared_dataset_payload_sha = canonical_dataset_payload.pop(
        "receipt_payload_sha256", None
    )
    actual_dataset_payload_sha = hashlib.sha256(
        json.dumps(
            canonical_dataset_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    if declared_dataset_payload_sha != actual_dataset_payload_sha:
        problems.append("dataset-receipt:payload-sha256")

    dataset_identity = dataset.get("identity")
    expected_dataset_identity_values = {
        "dataset_root": "/datasets/nuscenes-full",
        "dataset_realpath": "/datasets/nuscenes-full",
        "dataset_is_symlink": False,
        "dataset_version": "v1.0-trainval",
        "archive_root": "/datasets/nuscenes-full/archives",
        "archive_realpath": "/datasets/nuscenes-full/archives",
        "archive_is_symlink": False,
        "metadata_root": "/datasets/nuscenes-full/v1.0-trainval",
        "metadata_realpath": "/datasets/nuscenes-full/v1.0-trainval",
        "metadata_is_symlink": False,
        "map_root": "/datasets/nuscenes-full/maps",
        "map_realpath": "/datasets/nuscenes-full/maps",
        "map_is_symlink": False,
        "mount_target": "/datasets/nuscenes-full",
        "mount_source": "/dev/nvme0n2",
        "mount_fstype": "ext4",
        "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
    }
    expected_dataset_identity_fields = {
        *expected_dataset_identity_values,
        "dataset_st_dev",
        "mount_st_dev",
        "root_st_dev",
    }
    if (
        not isinstance(dataset_identity, dict)
        or set(dataset_identity) != expected_dataset_identity_fields
    ):
        problems.append("dataset-receipt:identity-field-set")
        dataset_identity = dataset_identity if isinstance(dataset_identity, dict) else {}
    for field, expected in expected_dataset_identity_values.items():
        if dataset_identity.get(field) != expected:
            problems.append(f"dataset-receipt:identity:{field}")
    dataset_device = dataset_identity.get("dataset_st_dev")
    dataset_mount_device = dataset_identity.get("mount_st_dev")
    dataset_root_device = dataset_identity.get("root_st_dev")
    if (
        type(dataset_device) is not int
        or type(dataset_mount_device) is not int
        or type(dataset_root_device) is not int
        or dataset_device != dataset_mount_device
        or dataset_device == dataset_root_device
    ):
        problems.append("dataset-receipt:device-identity")

    dataset_groups = (
        (
            "archive",
            dataset.get("archives"),
            expected_archives,
            Path("/datasets/nuscenes-full/archives"),
        ),
        (
            "metadata",
            dataset.get("metadata_json"),
            {name: (None, None) for name in expected_metadata},
            Path("/datasets/nuscenes-full/v1.0-trainval"),
        ),
        (
            "map",
            dataset.get("map_anchors"),
            {name: (None, None) for name in expected_maps},
            Path("/datasets/nuscenes-full/maps"),
        ),
    )
    dataset_root = Path("/datasets/nuscenes-full")
    for path in (dataset_root, *(group[3] for group in dataset_groups)):
        try:
            if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
                problems.append(f"dataset-live-directory:{path}")
        except OSError as error:
            problems.append(f"dataset-live-directory:{path}:{type(error).__name__}")
    try:
        live_dataset_devices = {
            "dataset_st_dev": dataset_root.stat().st_dev,
            "mount_st_dev": dataset_root.stat().st_dev,
            "root_st_dev": Path("/").stat().st_dev,
        }
    except OSError as error:
        problems.append(f"dataset-live-device:{type(error).__name__}")
    else:
        receipt_dataset_devices = {
            "dataset_st_dev": dataset_device,
            "mount_st_dev": dataset_mount_device,
            "root_st_dev": dataset_root_device,
        }
        if live_dataset_devices != receipt_dataset_devices:
            problems.append(
                f"dataset-live-device:{live_dataset_devices}!={receipt_dataset_devices}"
            )
    try:
        dataset_mount_row = subprocess.check_output(
            ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(dataset_root)],
            text=True,
        ).split()
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"dataset-live-mount:{type(error).__name__}")
    else:
        if dataset_mount_row != [
            "/dev/nvme0n2",
            "ext4",
            "9a98277e-b21f-4ffc-8f14-3f2235b43103",
        ]:
            problems.append(f"dataset-live-mount:{dataset_mount_row}")

    for label, receipts, expected_rows, parent in dataset_groups:
        if not isinstance(receipts, dict) or set(receipts) != set(expected_rows):
            problems.append(f"dataset-receipt:{label}-set")
            receipts = receipts if isinstance(receipts, dict) else {}
        try:
            observed_names = {path.name for path in parent.iterdir()}
        except OSError as error:
            problems.append(f"dataset-live:{label}-set:{type(error).__name__}")
        else:
            if observed_names != set(expected_rows):
                problems.append(f"dataset-live:{label}-set")
        for name, (expected_sha, expected_bytes) in sorted(expected_rows.items()):
            receipt = receipts.get(name)
            path = parent / name
            if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256", "bytes"}:
                problems.append(f"dataset-receipt:{label}:{name}:field-set")
                continue
            if receipt.get("path") != str(path):
                problems.append(f"dataset-receipt:{label}:{name}:path")
            if expected_sha is not None and receipt.get("sha256") != expected_sha:
                problems.append(f"dataset-receipt:{label}:{name}:frozen-sha256")
            if expected_bytes is not None and receipt.get("bytes") != expected_bytes:
                problems.append(f"dataset-receipt:{label}:{name}:frozen-bytes")
            try:
                if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
                    problems.append(f"dataset-live:{label}:{name}:physical")
                    continue
                live_bytes = path.stat(follow_symlinks=False).st_size
            except OSError as error:
                problems.append(
                    f"dataset-live:{label}:{name}:{type(error).__name__}:{error}"
                )
                continue
            if live_bytes != receipt.get("bytes"):
                problems.append(f"dataset-live:{label}:{name}:byte-drift")

    if environment.get("host") != "sentinel-gpu":
        problems.append(f"environment-host-contract:{environment.get('host')}")
    if socket.gethostname() != environment.get("host"):
        problems.append(f"host:{socket.gethostname()}!={environment.get('host')}")
    expected_box = {
        "idle": True,
        "all_containers": 0,
        "gpu_compute_processes": 0,
        "known_evaluation_processes": 0,
    }
    if environment.get("box") != expected_box:
        problems.append("environment-box:contract-drift")
    environment_devices = environment.get("storage_devices")
    expected_device_fields = {"filesystem_st_dev", "mount_st_dev", "root_st_dev"}
    if (
        not isinstance(environment_devices, dict)
        or set(environment_devices) != expected_device_fields
        or any(type(environment_devices.get(field)) is not int for field in expected_device_fields)
        or any(environment_devices[field] < 0 for field in expected_device_fields)
        or environment_devices["filesystem_st_dev"] != environment_devices["mount_st_dev"]
        or environment_devices["filesystem_st_dev"] == environment_devices["root_st_dev"]
    ):
        problems.append("environment-storage-devices:contract-drift")
    gpu_receipt = environment.get("gpu")
    expected_gpu_fields = {
        "model",
        "count",
        "uuid",
        "driver_version",
        "memory_total_mib",
    }
    if not isinstance(gpu_receipt, dict) or set(gpu_receipt) != expected_gpu_fields:
        problems.append("gpu-receipt:field-set")
    else:
        expected_gpu = {
            "model": "NVIDIA L4",
            "count": 1,
            "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
            "driver_version": "580.159.03",
            "memory_total_mib": 23034,
        }
        if gpu_receipt != expected_gpu:
            problems.append(f"gpu-receipt:frozen-identity:{gpu_receipt}!={expected_gpu}")
        try:
            gpu_rows = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,uuid,driver_version,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
            ).splitlines()
            if len(gpu_rows) != 1:
                raise ValueError(f"expected one GPU row, observed {len(gpu_rows)}")
            model, uuid, driver_version, memory_total_mib = [
                value.strip() for value in gpu_rows[0].split(",")
            ]
            live_gpu = {
                "model": model,
                "count": 1,
                "uuid": uuid,
                "driver_version": driver_version,
                "memory_total_mib": int(memory_total_mib),
            }
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            problems.append(f"gpu-live-receipt:{type(error).__name__}:{error}")
        else:
            if live_gpu != gpu_receipt:
                problems.append(f"gpu-live-drift:{live_gpu}!={gpu_receipt}")
    image_ids = environment.get("docker_image_ids")
    if not isinstance(image_ids, dict) or not image_ids:
        problems.append("docker-image-ids:missing")
    else:
        for image, expected in sorted(image_ids.items()):
            try:
                actual = subprocess.check_output(
                    [str(docker_binary), "image", "inspect", "--format={{.Id}}", image],
                    text=True,
                    timeout=5,
                ).strip()
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                problems.append(f"image-inspect:{image}:{error}")
                continue
            if actual != expected:
                problems.append(f"image-id:{image}:{actual}!={expected}")
    container_images = environment.get("container_images")
    expected_image_names = set(image_ids) if isinstance(image_ids, dict) else set()
    if not isinstance(container_images, dict) or set(container_images) != expected_image_names:
        problems.append("container-images:set")
    elif isinstance(image_ids, dict):
        for image, image_receipt in sorted(container_images.items()):
            if (
                not isinstance(image_receipt, dict)
                or set(image_receipt) != {"image_id", "repo_digests"}
                or image_receipt.get("image_id") != image_ids.get(image)
            ):
                problems.append(f"container-image-receipt:{image}")
    if manifest.get("container_images") != container_images:
        problems.append("container-images:embedded-drift")

    environment_remote_files = environment.get("remote_files")
    if not isinstance(environment_remote_files, dict) or set(environment_remote_files) != set(
        expected_remote_paths
    ):
        problems.append("environment-remote-files:set")
    else:
        for role, launch_row in sorted(remote_rows.items()):
            environment_row = environment_remote_files.get(role)
            if not isinstance(environment_row, dict) or any(
                environment_row.get(field) != launch_row.get(field)
                for field in ("path", "sha256", "bytes")
            ):
                problems.append(f"environment-remote-file-link:{role}")

    expected_repositories = {
        "uniad": {
            "path": "/opt/sentinel-stack/UniAD",
            "head": "4827b8be0823e90862caa75d9d146b2ae800b72f",
            "staged_paths": [],
            "dirty_tracked_paths": [
                "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"
            ],
            "required_untracked_paths": [],
        },
        "neuroncap": {
            "path": "/opt/sentinel-stack/NeuroNCAP",
            "head": "ecdcf284e2b7b83c537f3292a06c0adddff55811",
            "staged_paths": [],
            "dirty_tracked_paths": [
                "docker/Dockerfile",
                "scripts/_docker_compose_release.sh",
            ],
            "required_untracked_paths": [],
        },
        "neurad": {
            "path": "/opt/sentinel-stack/neurad-studio",
            "head": "b25f717b23d85c865d469bf52a0bd03b244014be",
            "staged_paths": [],
            "dirty_tracked_paths": ["Dockerfile"],
            "required_untracked_paths": ["Dockerfile.bak"],
        },
    }
    repositories = environment.get("repositories")
    if not isinstance(repositories, dict) or repositories != expected_repositories:
        problems.append("environment-repositories:contract-drift")
    else:
        for repository_id, expected_repository in sorted(expected_repositories.items()):
            repository_path = Path(expected_repository["path"])
            if (
                repository_path.is_symlink()
                or not repository_path.is_dir()
                or repository_path.resolve(strict=True) != repository_path
            ):
                problems.append(
                    f"live-repository-path:{repository_id}:{repository_path}"
                )
                continue

            def git_output(*arguments: str) -> bytes:
                return subprocess.check_output(
                    [
                        "git",
                        "-c",
                        f"safe.directory={repository_path}",
                        "-C",
                        str(repository_path),
                        *arguments,
                    ]
                )

            try:
                top_level = Path(
                    git_output("rev-parse", "--show-toplevel").decode().strip()
                ).resolve(strict=True)
                head = git_output("rev-parse", "HEAD").decode().strip()
                staged = sorted(
                    path.decode(errors="surrogateescape")
                    for path in git_output(
                        "diff", "--cached", "--name-only", "--no-renames", "-z"
                    ).split(b"\0")
                    if path
                )
                dirty_tracked = sorted(
                    path.decode(errors="surrogateescape")
                    for path in git_output(
                        "diff", "--name-only", "--no-renames", "-z"
                    ).split(b"\0")
                    if path
                )
                status_rows = git_output(
                    "status", "--porcelain=v1", "-z", "--untracked-files=normal"
                ).split(b"\0")
                untracked = sorted(
                    row[3:].decode(errors="surrogateescape")
                    for row in status_rows
                    if row.startswith(b"?? ")
                )
            except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
                problems.append(
                    f"live-repository-read:{repository_id}:{type(error).__name__}:{error}"
                )
                continue
            if top_level != repository_path:
                problems.append(
                    f"live-repository-top-level:{repository_id}:{top_level}!={repository_path}"
                )
            if head != expected_repository["head"]:
                problems.append(
                    f"live-repository-head:{repository_id}:{head}!={expected_repository['head']}"
                )
            if staged != expected_repository["staged_paths"]:
                problems.append(
                    f"live-repository-staged:{repository_id}:{staged}"
                )
            if dirty_tracked != expected_repository["dirty_tracked_paths"]:
                problems.append(
                    f"live-repository-dirty:{repository_id}:{dirty_tracked}"
                )
            required_untracked = expected_repository["required_untracked_paths"]
            if repository_id == "neuroncap":
                unexpected_untracked = [
                    path
                    for path in untracked
                    if path != "outoutput/" and not path.startswith("outoutput/")
                ]
                observed_required = []
            else:
                unexpected_untracked = [
                    path for path in untracked if path not in required_untracked
                ]
                observed_required = [
                    path for path in required_untracked if path in untracked
                ]
            if unexpected_untracked or observed_required != required_untracked:
                problems.append(
                    f"live-repository-untracked:{repository_id}:"
                    f"required={observed_required}:unexpected={unexpected_untracked}"
                )

git_provenance = manifest.get("git_provenance")
if not isinstance(git_provenance, dict):
    problems.append("git-provenance:missing")
else:
    if git_provenance.get("schema") != "iter135.git_provenance.v1":
        problems.append("git-provenance:schema")
    if git_provenance.get("verdict") != "I135_GIT_PROVENANCE_OK":
        problems.append("git-provenance:verdict")
    if git_provenance.get("problem_count") != 0 or git_provenance.get("problems") != []:
        problems.append("git-provenance:problems")
    if git_provenance.get("dirty_lines") != []:
        problems.append("git-provenance:dirty")

source_artifacts = manifest.get("source_artifacts")
expected_source_hashes = {
    "iter134_oracle_log": "55c5a77e898f1a1834a984dd02c576f128c0ac445c71f9721256beaac2b04b14",
    "iter134_oracle_runs": "b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315",
    "iter134_union_part_aa": "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
    "iter134_union_part_ab": "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
    "iter15_released_union": "d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189",
    "iter134_released_union": "d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189",
}
if not isinstance(source_artifacts, dict) or set(source_artifacts) != set(expected_source_hashes):
    problems.append("source-artifacts:set")
else:
    for role, receipt in sorted(source_artifacts.items()):
        if (
            not isinstance(receipt, dict)
            or set(receipt)
            != {
                "source_path",
                "sha256",
                "bytes",
                "expected_sha256",
                "matches_frozen_sha256",
            }
            or receipt.get("sha256") != expected_source_hashes[role]
            or receipt.get("expected_sha256") != expected_source_hashes[role]
            or type(receipt.get("bytes")) is not int
            or receipt["bytes"] <= 0
            or receipt.get("matches_frozen_sha256") is not True
        ):
            problems.append(f"source-artifact:{role}:drift")

storage = manifest.get("storage_gate")
if not isinstance(storage, dict):
    problems.append("storage-gate:missing")
else:
    storage_path = Path(storage.get("filesystem_path", ""))
    expected_output_root = Path("/datasets/nuscenes-full/sentinel-i135-outoutput")
    if storage_path != expected_output_root:
        problems.append(f"storage-path-contract:{storage_path}!={expected_output_root}")
    if not storage_path.is_absolute() or not storage_path.is_dir() or storage_path.is_symlink():
        problems.append(f"storage-path:{storage_path}")
    else:
        try:
            if storage_path.resolve(strict=True) != expected_output_root:
                problems.append("storage-path-realpath-drift")
        except OSError as error:
            problems.append(f"storage-path-realpath:{error}")
        cursor = Path("/")
        for component in storage_path.parts[1:]:
            cursor /= component
            if cursor.is_symlink():
                problems.append(f"storage-path-component-symlink:{cursor}")
        data_mount = Path("/datasets/nuscenes-full")
        live_devices = {
            "filesystem_st_dev": storage_path.stat().st_dev,
            "mount_st_dev": data_mount.stat().st_dev,
            "root_st_dev": Path("/").stat().st_dev,
        }
        if live_devices != environment_devices:
            problems.append(
                f"storage-live-device-drift:{live_devices}!={environment_devices}"
            )
        if storage_path.stat().st_dev != data_mount.stat().st_dev:
            problems.append("storage-path-device-mismatch")
        if storage_path.stat().st_dev == Path("/").stat().st_dev:
            problems.append("storage-path-not-dedicated-filesystem")
        try:
            mount_row = subprocess.check_output(
                ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(storage_path)],
                text=True,
            ).split()
        except (OSError, subprocess.CalledProcessError) as error:
            problems.append(f"storage-findmnt:{error}")
        else:
            expected_mount_row = [
                "/dev/nvme0n2",
                "ext4",
                "9a98277e-b21f-4ffc-8f14-3f2235b43103",
            ]
            if mount_row != expected_mount_row:
                problems.append(f"storage-mount-identity:{mount_row}!={expected_mount_row}")
        if any(storage_path.iterdir()):
            problems.append("storage-output-root-not-empty")
        historical_root = Path("/opt/sentinel-stack/NeuroNCAP/outoutput")
        if os.path.lexists(historical_root):
            if (
                historical_root.is_symlink()
                or not historical_root.is_dir()
                or historical_root.resolve(strict=True) != historical_root
            ):
                problems.append("historical-root-not-physical-directory")
            elif any(
                child.name.startswith("i135-") for child in historical_root.iterdir()
            ):
                problems.append("historical-root-has-i135-output")
        free_bytes = shutil.disk_usage(storage_path).free
        minimum = storage.get("minimum_remote_free_bytes")
        projected = storage.get("projected_output_bytes")
        reserve = storage.get("minimum_reserve_bytes")
        if minimum != 100 * 1024**3:
            problems.append(f"remote-minimum-bytes:{minimum}")
        if projected != 72_380_432_384:
            problems.append(f"projected-output-bytes:{projected}")
        if reserve != 25 * 1024**3:
            problems.append(f"reserve-bytes:{reserve}")
        if type(minimum) is int and free_bytes < minimum:
            problems.append(f"remote-free-bytes:{free_bytes}<{minimum}")
        if type(projected) is int and type(reserve) is int and free_bytes - projected < reserve:
            problems.append(f"projected-reserve-bytes:{free_bytes}-{projected}<{reserve}")

resource = manifest.get("resource_gate")
if not isinstance(resource, dict):
    problems.append("resource-gate:missing")
else:
    smoke_path = payload_root / "smoke-evidence/smoke_receipt.json"
    tooling_receipt_path = payload_root / "tooling_verification_receipt.json"
    try:
        smoke_evidence = json.loads(smoke_path.read_bytes())
        tooling_evidence = json.loads(tooling_receipt_path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"evidence-receipt-read:{type(error).__name__}:{error}")
        smoke_evidence = {}
        tooling_evidence = {}
    if (
        smoke_evidence.get("schema") != "iter135.smoke_receipt.v1"
        or smoke_evidence.get("verdict") != "I135_LIVE_SMOKE_OK"
        or smoke_evidence.get("problem_count") != 0
        or smoke_evidence.get("problems") != []
        or smoke_evidence.get("nonanalytic") is not True
        or smoke_evidence.get("analytic_episode_count") != 0
    ):
        problems.append("smoke-evidence-receipt:contract")
    if (
        tooling_evidence.get("schema") != "iter135.tooling_verification.v2"
        or tooling_evidence.get("verdict") != "I135_TOOLING_VERIFICATION_OK"
        or tooling_evidence.get("problem_count") != 0
        or tooling_evidence.get("problems") != []
    ):
        problems.append("tooling-evidence-receipt:contract")
    total = resource.get("total_gpu_ceiling_seconds")
    prior = resource.get("prior_smoke_gpu_seconds")
    remaining = resource.get("remaining_analytic_seconds")
    if total != 110 * 60 * 60 or type(prior) is not int or prior < 0:
        problems.append("resource-gate:values")
    elif remaining != total - prior or remaining <= 0:
        problems.append("resource-gate:remaining")
    if prior != smoke_evidence.get("gpu_seconds"):
        problems.append(
            f"resource-gate:smoke-link:{prior}!={smoke_evidence.get('gpu_seconds')}"
        )

if problems:
    print("I135_PREFLIGHT_FAIL", *problems, sep="\n - ")
    raise SystemExit(1)
print(
    "I135_PREFLIGHT_OK",
    f"manifest_sha256={actual_manifest_sha256}",
    f"blocks={len(expected_blocks)}",
    f"cells={len(expected_cells)}",
    f"payloads={len(hash_bound)}",
    f"remote={len(remote_artifacts)}",
)
PY

OUTPUT_ROOT_ID=$(stat -Lc '%d:%i' "$OUTPUT_ROOT") || abort "storage-output-root-identity"

RUNTIME_SNAPSHOT=$(python3 - "$MANIFEST_SOURCE" "$EXPECTED_MANIFEST_SHA" \
  "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

source_manifest = Path(sys.argv[1]).absolute()
expected_manifest_sha = sys.argv[2]
docker_binary = Path(sys.argv[3])
expected_docker_identity = sys.argv[4]
expected_docker_sha = sys.argv[5]
if (
    source_manifest.is_symlink()
    or not source_manifest.is_file()
    or source_manifest.resolve(strict=True) != source_manifest
):
    raise SystemExit(f"snapshot manifest is not physical: {source_manifest}")
manifest_payload = source_manifest.read_bytes()
if hashlib.sha256(manifest_payload).hexdigest() != expected_manifest_sha:
    raise SystemExit("manifest changed between preflight and snapshot")
manifest = json.loads(manifest_payload)
payloads = (
    "dose_schedules.json",
    "server_patch_union_release.py",
    "server_patch_blind_dose.py",
)
parent = Path("/var/lib/sentinel")
parent.mkdir(mode=0o755, parents=True, exist_ok=True)
if parent.is_symlink() or parent.resolve(strict=True) != parent:
    raise SystemExit(f"runtime snapshot parent is not physical: {parent}")
snapshot = parent / f"i135-runtime-{expected_manifest_sha}"

def stable_payload(path: Path) -> bytes:
    if (
        path.is_symlink()
        or not path.is_file()
        or path.resolve(strict=True) != path.absolute()
    ):
        raise SystemExit(f"snapshot source is not a regular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    identity_path = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        identity_before != identity_after
        or identity_before != identity_path
        or len(payload) != before.st_size
    ):
        raise SystemExit(f"snapshot source changed while reading: {path}")
    return payload

rows = [("launch_manifest.json", source_manifest, expected_manifest_sha)]
for name in payloads:
    receipt = manifest.get("hash_bound_files", {}).get(name)
    expected = receipt.get("sha256") if isinstance(receipt, dict) else None
    rows.append((name, source_manifest.parent / name, expected))
prepared = []
for name, source, expected in rows:
    payload = stable_payload(source)
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SystemExit(f"snapshot source hash drift: {name}:{actual}!={expected}")
    prepared.append((name, payload, expected))

dataset_receipt = manifest.get("dataset_receipt")
if not isinstance(dataset_receipt, dict):
    raise SystemExit("dataset receipt missing from runtime snapshot source")
dataset_groups = {
    "archive": dataset_receipt.get("archives"),
    "metadata": dataset_receipt.get("metadata_json"),
    "map": dataset_receipt.get("map_anchors"),
}
if any(not isinstance(group, dict) for group in dataset_groups.values()):
    raise SystemExit("dataset receipt groups missing from runtime snapshot source")


def stable_dataset_file(
    path: Path,
    expected_sha: str,
    expected_bytes: int,
    expected_device: int,
) -> dict:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"dataset snapshot source is not physical: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        byte_count = 0
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                digest.update(chunk)
                byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    before_row = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_row = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    path_row = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
        path_after.st_ctime_ns,
    )
    actual_sha = digest.hexdigest()
    if (
        before_row != after_row
        or before_row != path_row
        or byte_count != before.st_size
        or byte_count != expected_bytes
        or actual_sha != expected_sha
        or not stat.S_ISREG(before.st_mode)
        or before.st_dev != expected_device
    ):
        raise SystemExit(f"dataset snapshot byte proof drift: {path}")
    return {
        "path": str(path),
        "sha256": actual_sha,
        "bytes": byte_count,
        "st_dev": before.st_dev,
        "st_ino": before.st_ino,
        "st_mode": stat.S_IMODE(before.st_mode),
        "st_mtime_ns": before.st_mtime_ns,
        "st_ctime_ns": before.st_ctime_ns,
    }


dataset_root = Path("/datasets/nuscenes-full")
dataset_root_stat = dataset_root.stat(follow_symlinks=False)
if (
    dataset_root.is_symlink()
    or not stat.S_ISDIR(dataset_root_stat.st_mode)
    or dataset_root.resolve(strict=True) != dataset_root
):
    raise SystemExit("dataset snapshot root is not physical")
dataset_files = {}
for label, group in dataset_groups.items():
    for name, receipt in sorted(group.items()):
        if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256", "bytes"}:
            raise SystemExit(f"dataset snapshot receipt drift: {label}:{name}")
        path = Path(receipt["path"])
        dataset_files[f"{label}:{name}"] = stable_dataset_file(
            path,
            receipt["sha256"],
            receipt["bytes"],
            dataset_root_stat.st_dev,
        )
dataset_snapshot = {
    "schema": "iter135.dataset_runtime_snapshot.v1",
    "manifest_sha256": expected_manifest_sha,
    "dataset_receipt_payload_sha256": dataset_receipt.get("receipt_payload_sha256"),
    "dataset_root": {
        "path": str(dataset_root),
        "st_dev": dataset_root_stat.st_dev,
        "st_ino": dataset_root_stat.st_ino,
        "st_mode": stat.S_IMODE(dataset_root_stat.st_mode),
        "st_mtime_ns": dataset_root_stat.st_mtime_ns,
        "st_ctime_ns": dataset_root_stat.st_ctime_ns,
    },
    "files": dataset_files,
}
dataset_snapshot_payload = (
    json.dumps(dataset_snapshot, sort_keys=True, separators=(",", ":")) + "\n"
).encode("utf-8")
dataset_snapshot_sha = hashlib.sha256(dataset_snapshot_payload).hexdigest()
prepared.append(
    ("dataset_runtime_snapshot.json", dataset_snapshot_payload, dataset_snapshot_sha)
)


def docker_text(*args: str) -> str:
    completed = subprocess.run(
        [str(docker_binary), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=5,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Docker runtime receipt command failed: {args}")
    return completed.stdout.strip()


docker_stat = docker_binary.stat(follow_symlinks=False)
if (
    docker_binary.is_symlink()
    or not docker_binary.is_file()
    or docker_binary.resolve(strict=True) != docker_binary
    or f"{docker_stat.st_dev}:{docker_stat.st_ino}" != expected_docker_identity
    or hashlib.sha256(docker_binary.read_bytes()).hexdigest() != expected_docker_sha
):
    raise SystemExit("Docker runtime client binary drift")
if any(
    os.environ.get(name)
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
):
    raise SystemExit("Docker runtime environment override is forbidden")
docker_context = docker_text("context", "show")
docker_endpoint = json.loads(
    docker_text(
        "context",
        "inspect",
        "--format",
        "{{json .Endpoints.docker.Host}}",
        docker_context,
    )
)
if docker_context != "default" or docker_endpoint != "unix:///var/run/docker.sock":
    raise SystemExit(f"Docker runtime endpoint drift: {docker_context}:{docker_endpoint}")
docker_info = json.loads(docker_text("info", "--format", "{{json .}}"))
docker_version = json.loads(docker_text("version", "--format", "{{json .}}"))
server_version = docker_version.get("Server")
if not isinstance(docker_info, dict) or not isinstance(server_version, dict):
    raise SystemExit("Docker runtime daemon receipt missing")
info_fields = (
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
version_fields = (
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
daemon_info = {name: docker_info.get(name) for name in info_fields}
daemon_version = {name: server_version.get(name) for name in version_fields}
if any(value is None for value in daemon_info.values()) or any(
    value is None for value in daemon_version.values()
):
    raise SystemExit("Docker runtime daemon field missing")
declared_socket = Path("/var/run/docker.sock")
socket_stat = declared_socket.stat(follow_symlinks=False)
if declared_socket.is_symlink() or not stat.S_ISSOCK(socket_stat.st_mode):
    raise SystemExit("Docker runtime endpoint is not a physical Unix socket")
docker_runtime_snapshot = {
    "schema": "iter135.docker_runtime_snapshot.v1",
    "manifest_sha256": expected_manifest_sha,
    "client": {
        "path": str(docker_binary),
        "sha256": expected_docker_sha,
        "st_dev": docker_stat.st_dev,
        "st_ino": docker_stat.st_ino,
    },
    "context": docker_context,
    "endpoint": docker_endpoint,
    "socket": {
        "declared_path": str(declared_socket),
        "realpath": str(declared_socket.resolve(strict=True)),
        "st_dev": socket_stat.st_dev,
        "st_ino": socket_stat.st_ino,
        "st_mode": stat.S_IMODE(socket_stat.st_mode),
        "st_uid": socket_stat.st_uid,
        "st_gid": socket_stat.st_gid,
    },
    "daemon_info": daemon_info,
    "daemon_version": daemon_version,
}
docker_runtime_payload = (
    json.dumps(docker_runtime_snapshot, sort_keys=True, separators=(",", ":")) + "\n"
).encode("utf-8")
docker_runtime_sha = hashlib.sha256(docker_runtime_payload).hexdigest()
prepared.append(
    ("docker_runtime_snapshot.json", docker_runtime_payload, docker_runtime_sha)
)


def validate_snapshot(root: Path) -> None:
    expected_names = {name for name, _payload, _digest in prepared}
    if (
        root.is_symlink()
        or not root.is_dir()
        or root.resolve(strict=True) != root
        or stat.S_IMODE(root.stat().st_mode) != 0o555
        or {path.name for path in root.iterdir()} != expected_names
    ):
        raise SystemExit("existing runtime snapshot contract drift")
    for name, _payload, expected in prepared:
        path = root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or path.resolve(strict=True) != path
            or stat.S_IMODE(path.stat().st_mode) != 0o444
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise SystemExit(f"existing runtime snapshot payload drift: {name}")


if snapshot.exists() or snapshot.is_symlink():
    validate_snapshot(snapshot)
    print(snapshot)
    raise SystemExit(0)

temporary = Path(tempfile.mkdtemp(prefix=f".{snapshot.name}.", suffix=".tmp", dir=parent))
try:
    for name, payload, _expected in prepared:
        destination = temporary / name
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)
        os.chmod(destination, 0o444)
    os.chmod(temporary, 0o555)
    directory_fd = os.open(temporary, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    os.rename(temporary, snapshot)
    parent_fd = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
finally:
    if temporary.exists():
        os.chmod(temporary, 0o755)
        for child in temporary.iterdir():
            os.chmod(child, 0o644)
            child.unlink()
        temporary.rmdir()
validate_snapshot(snapshot)
print(snapshot)
PY
) || abort "runtime-snapshot"
MANIFEST=$RUNTIME_SNAPSHOT/launch_manifest.json
SCHED=$RUNTIME_SNAPSHOT/dose_schedules.json
UNION_PATCH=$RUNTIME_SNAPSHOT/server_patch_union_release.py
BLIND_PATCH=$RUNTIME_SNAPSHOT/server_patch_blind_dose.py
DATASET_RUNTIME_SNAPSHOT=$RUNTIME_SNAPSHOT/dataset_runtime_snapshot.json
DATASET_RUNTIME_SNAPSHOT_ID=$(stat -Lc '%d:%i' "$DATASET_RUNTIME_SNAPSHOT") \
  || abort "dataset-runtime-snapshot-identity"
DATASET_RUNTIME_SNAPSHOT_SHA=$(sha256sum "$DATASET_RUNTIME_SNAPSHOT" | awk '{print $1}') \
  || abort "dataset-runtime-snapshot-sha256"
DOCKER_RUNTIME_SNAPSHOT=$RUNTIME_SNAPSHOT/docker_runtime_snapshot.json
DOCKER_RUNTIME_SNAPSHOT_ID=$(stat -Lc '%d:%i' "$DOCKER_RUNTIME_SNAPSHOT") \
  || abort "docker-runtime-snapshot-identity"
DOCKER_RUNTIME_SNAPSHOT_SHA=$(sha256sum "$DOCKER_RUNTIME_SNAPSHOT" | awk '{print $1}') \
  || abort "docker-runtime-snapshot-sha256"
if ! [[ "$DATASET_RUNTIME_SNAPSHOT_ID" =~ ^[0-9]+:[0-9]+$ \
  && "$DATASET_RUNTIME_SNAPSHOT_SHA" =~ ^[0-9a-f]{64}$ \
  && "$DOCKER_RUNTIME_SNAPSHOT_ID" =~ ^[0-9]+:[0-9]+$ \
  && "$DOCKER_RUNTIME_SNAPSHOT_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  abort "runtime-snapshot-receipt"
fi
echo "I135_RUNTIME_SNAPSHOT_OK manifest_sha256=$EXPECTED_MANIFEST_SHA path=$RUNTIME_SNAPSHOT"
echo "I135_DATASET_SNAPSHOT_OK sha256=$DATASET_RUNTIME_SNAPSHOT_SHA id=$DATASET_RUNTIME_SNAPSHOT_ID files=28"
echo "I135_DOCKER_SNAPSHOT_OK sha256=$DOCKER_RUNTIME_SNAPSHOT_SHA id=$DOCKER_RUNTIME_SNAPSHOT_ID"

verify_runtime_snapshot() {
  python3 - "$RUNTIME_SNAPSHOT" "$EXPECTED_MANIFEST_SHA" \
    "$DATASET_RUNTIME_SNAPSHOT_ID" "$DATASET_RUNTIME_SNAPSHOT_SHA" \
    "$DOCKER_RUNTIME_SNAPSHOT_ID" "$DOCKER_RUNTIME_SNAPSHOT_SHA" <<'PY'
import hashlib
import json
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_manifest = sys.argv[2]
expected_dataset_identity = sys.argv[3]
expected_dataset_sha = sys.argv[4]
expected_docker_identity = sys.argv[5]
expected_docker_sha = sys.argv[6]
expected_names = {
    "launch_manifest.json",
    "dose_schedules.json",
    "server_patch_union_release.py",
    "server_patch_blind_dose.py",
    "dataset_runtime_snapshot.json",
    "docker_runtime_snapshot.json",
}
if root.is_symlink() or not root.is_dir() or {path.name for path in root.iterdir()} != expected_names:
    raise SystemExit("runtime snapshot file-set drift")
if stat.S_IMODE(root.stat().st_mode) != 0o555:
    raise SystemExit("runtime snapshot directory mode drift")
manifest_path = root / "launch_manifest.json"
if (
    manifest_path.is_symlink()
    or not manifest_path.is_file()
    or manifest_path.resolve(strict=True) != manifest_path.absolute()
    or stat.S_IMODE(manifest_path.stat().st_mode) != 0o444
    or hashlib.sha256(manifest_path.read_bytes()).hexdigest() != expected_manifest
):
    raise SystemExit("runtime snapshot manifest drift")
manifest = json.loads(manifest_path.read_bytes())
for name in expected_names - {
    "launch_manifest.json",
    "dataset_runtime_snapshot.json",
    "docker_runtime_snapshot.json",
}:
    path = root / name
    receipt = manifest.get("hash_bound_files", {}).get(name)
    expected = receipt.get("sha256") if isinstance(receipt, dict) else None
    if (
        path.is_symlink()
        or not path.is_file()
        or path.resolve(strict=True) != path.absolute()
        or stat.S_IMODE(path.stat().st_mode) != 0o444
        or hashlib.sha256(path.read_bytes()).hexdigest() != expected
    ):
        raise SystemExit(f"runtime snapshot payload drift: {name}")
dataset_snapshot = root / "dataset_runtime_snapshot.json"
if (
    dataset_snapshot.is_symlink()
    or not dataset_snapshot.is_file()
    or dataset_snapshot.resolve(strict=True) != dataset_snapshot.absolute()
    or stat.S_IMODE(dataset_snapshot.stat().st_mode) != 0o444
    or f"{dataset_snapshot.stat().st_dev}:{dataset_snapshot.stat().st_ino}"
    != expected_dataset_identity
    or hashlib.sha256(dataset_snapshot.read_bytes()).hexdigest() != expected_dataset_sha
):
    raise SystemExit("dataset runtime snapshot payload drift")
docker_snapshot = root / "docker_runtime_snapshot.json"
if (
    docker_snapshot.is_symlink()
    or not docker_snapshot.is_file()
    or docker_snapshot.resolve(strict=True) != docker_snapshot.absolute()
    or stat.S_IMODE(docker_snapshot.stat().st_mode) != 0o444
    or f"{docker_snapshot.stat().st_dev}:{docker_snapshot.stat().st_ino}"
    != expected_docker_identity
    or hashlib.sha256(docker_snapshot.read_bytes()).hexdigest() != expected_docker_sha
):
    raise SystemExit("Docker runtime snapshot payload drift")
PY
}
verify_runtime_snapshot || abort "runtime-snapshot-verification"

verify_dataset_runtime_identity() {
  local PHASE=$1
  python3 - "$MANIFEST" "$DATASET_RUNTIME_SNAPSHOT" \
    "$DATASET_RUNTIME_SNAPSHOT_ID" "$DATASET_RUNTIME_SNAPSHOT_SHA" "$PHASE" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

manifest_text, snapshot_text, expected_identity, expected_sha, phase = sys.argv[1:]
if phase not in {"analytic-arm", "before", "after", "before-done"}:
    raise SystemExit(f"dataset runtime phase drift: {phase}")
manifest = json.loads(Path(manifest_text).read_bytes())
dataset_receipt = manifest.get("dataset_receipt")
snapshot_path = Path(snapshot_text)
if (
    snapshot_path.is_symlink()
    or not snapshot_path.is_file()
    or snapshot_path.resolve(strict=True) != snapshot_path
    or stat.S_IMODE(snapshot_path.stat().st_mode) != 0o444
    or f"{snapshot_path.stat().st_dev}:{snapshot_path.stat().st_ino}" != expected_identity
):
    raise SystemExit("dataset runtime snapshot filesystem drift")
snapshot_payload = snapshot_path.read_bytes()
if hashlib.sha256(snapshot_payload).hexdigest() != expected_sha:
    raise SystemExit("dataset runtime snapshot hash drift")
snapshot = json.loads(snapshot_payload)
if (
    not isinstance(dataset_receipt, dict)
    or set(snapshot) != {
        "schema",
        "manifest_sha256",
        "dataset_receipt_payload_sha256",
        "dataset_root",
        "files",
    }
    or snapshot.get("schema") != "iter135.dataset_runtime_snapshot.v1"
    or snapshot.get("dataset_receipt_payload_sha256")
    != dataset_receipt.get("receipt_payload_sha256")
):
    raise SystemExit("dataset runtime snapshot schema drift")

root = Path("/datasets/nuscenes-full")
root_receipt = snapshot.get("dataset_root")
root_stat = root.stat(follow_symlinks=False)
if (
    root.is_symlink()
    or not stat.S_ISDIR(root_stat.st_mode)
    or root.resolve(strict=True) != root
    or root_receipt
    != {
        "path": str(root),
        "st_dev": root_stat.st_dev,
        "st_ino": root_stat.st_ino,
        "st_mode": stat.S_IMODE(root_stat.st_mode),
        "st_mtime_ns": root_stat.st_mtime_ns,
        "st_ctime_ns": root_stat.st_ctime_ns,
    }
):
    raise SystemExit("dataset runtime root identity drift")
mount_row = subprocess.run(
    ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(root)],
    check=True,
    capture_output=True,
    text=True,
).stdout.split()
if mount_row != [
    "/dev/nvme0n2",
    "ext4",
    "9a98277e-b21f-4ffc-8f14-3f2235b43103",
]:
    raise SystemExit(f"dataset runtime mount drift: {mount_row}")
identity_receipt = dataset_receipt.get("identity")
if (
    not isinstance(identity_receipt, dict)
    or identity_receipt.get("dataset_st_dev") != root_stat.st_dev
    or identity_receipt.get("mount_st_dev") != root_stat.st_dev
    or identity_receipt.get("root_st_dev") != Path("/").stat().st_dev
):
    raise SystemExit("dataset runtime device receipt drift")

groups = {
    "archive": (
        Path("/datasets/nuscenes-full/archives"),
        dataset_receipt.get("archives"),
    ),
    "metadata": (
        Path("/datasets/nuscenes-full/v1.0-trainval"),
        dataset_receipt.get("metadata_json"),
    ),
    "map": (
        Path("/datasets/nuscenes-full/maps"),
        dataset_receipt.get("map_anchors"),
    ),
}
expected_snapshot_roles = set()
for label, (parent, receipts) in groups.items():
    if (
        not isinstance(receipts, dict)
        or parent.is_symlink()
        or not parent.is_dir()
        or parent.resolve(strict=True) != parent
        or parent.stat().st_dev != root_stat.st_dev
    ):
        raise SystemExit(f"dataset runtime group drift: {label}")
    if {path.name for path in parent.iterdir()} != set(receipts):
        raise SystemExit(f"dataset runtime direct-entry drift: {label}")
    expected_snapshot_roles.update(f"{label}:{name}" for name in receipts)
files = snapshot.get("files")
if not isinstance(files, dict) or set(files) != expected_snapshot_roles:
    raise SystemExit("dataset runtime snapshot role-set drift")


def stable_live_receipt(path: Path, *, hash_bytes: bool) -> tuple[dict, str | None]:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"dataset runtime file is not physical: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256() if hash_bytes else None
        byte_count = 0
        if digest is not None:
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                while chunk := stream.read(8 * 1024 * 1024):
                    digest.update(chunk)
                    byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    before_row = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_row = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    path_row = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
        path_after.st_ctime_ns,
    )
    if (
        before_row != after_row
        or before_row != path_row
        or before.st_dev != root_stat.st_dev
    ):
        raise SystemExit(f"dataset runtime file changed during probe: {path}")
    row = {
        "path": str(path),
        "sha256": None,
        "bytes": before.st_size,
        "st_dev": before.st_dev,
        "st_ino": before.st_ino,
        "st_mode": stat.S_IMODE(before.st_mode),
        "st_mtime_ns": before.st_mtime_ns,
        "st_ctime_ns": before.st_ctime_ns,
    }
    return row, digest.hexdigest() if digest is not None else None


for label, (parent, receipts) in groups.items():
    for name, receipt in sorted(receipts.items()):
        role = f"{label}:{name}"
        frozen = files[role]
        path = parent / name
        live, live_sha = stable_live_receipt(path, hash_bytes=label != "archive")
        expected_live_identity = dict(frozen)
        expected_live_identity["sha256"] = None
        if live != expected_live_identity:
            raise SystemExit(f"dataset runtime stat identity drift: {role}")
        if (
            frozen.get("sha256") != receipt.get("sha256")
            or frozen.get("bytes") != receipt.get("bytes")
        ):
            raise SystemExit(f"dataset runtime receipt link drift: {role}")
        if label != "archive" and live_sha != receipt.get("sha256"):
            raise SystemExit(f"dataset runtime byte drift: {role}")
print(f"I135_DATASET_RUNTIME_OK phase={phase} files={len(files)}")
PY
}

verify_docker_runtime_identity() {
  local PHASE=$1
  python3 - "$DOCKER_RUNTIME_SNAPSHOT" "$DOCKER_RUNTIME_SNAPSHOT_ID" \
    "$DOCKER_RUNTIME_SNAPSHOT_SHA" "$DOCKER_BIN" "$DOCKER_BIN_ID" \
    "$DOCKER_BIN_SHA" "$EXPECTED_MANIFEST_SHA" "$PHASE" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

(
    snapshot_text,
    expected_snapshot_identity,
    expected_snapshot_sha,
    docker_text,
    expected_docker_identity,
    expected_docker_sha,
    expected_manifest_sha,
    phase,
) = sys.argv[1:]
if phase not in {"analytic-arm", "before", "after", "before-done"}:
    raise SystemExit(f"Docker runtime phase drift: {phase}")
snapshot_path = Path(snapshot_text)
docker_binary = Path(docker_text)
snapshot_stat = snapshot_path.stat(follow_symlinks=False)
if (
    snapshot_path.is_symlink()
    or not stat.S_ISREG(snapshot_stat.st_mode)
    or snapshot_path.resolve(strict=True) != snapshot_path
    or f"{snapshot_stat.st_dev}:{snapshot_stat.st_ino}" != expected_snapshot_identity
):
    raise SystemExit("Docker runtime snapshot filesystem drift")
snapshot_payload = snapshot_path.read_bytes()
if hashlib.sha256(snapshot_payload).hexdigest() != expected_snapshot_sha:
    raise SystemExit("Docker runtime snapshot hash drift")
expected = json.loads(snapshot_payload)
if (
    set(expected)
    != {
        "schema",
        "manifest_sha256",
        "client",
        "context",
        "endpoint",
        "socket",
        "daemon_info",
        "daemon_version",
    }
    or expected.get("schema") != "iter135.docker_runtime_snapshot.v1"
    or expected.get("manifest_sha256") != expected_manifest_sha
):
    raise SystemExit("Docker runtime snapshot schema drift")
docker_stat = docker_binary.stat(follow_symlinks=False)
if (
    docker_binary.is_symlink()
    or not stat.S_ISREG(docker_stat.st_mode)
    or docker_binary.resolve(strict=True) != docker_binary
    or f"{docker_stat.st_dev}:{docker_stat.st_ino}" != expected_docker_identity
    or hashlib.sha256(docker_binary.read_bytes()).hexdigest() != expected_docker_sha
):
    raise SystemExit("Docker runtime client drift")
if expected.get("client") != {
    "path": str(docker_binary),
    "sha256": expected_docker_sha,
    "st_dev": docker_stat.st_dev,
    "st_ino": docker_stat.st_ino,
}:
    raise SystemExit("Docker runtime client receipt drift")
if any(
    os.environ.get(name)
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
):
    raise SystemExit("Docker runtime environment override appeared")


def command(*args: str) -> str:
    completed = subprocess.run(
        [str(docker_binary), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=5,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Docker runtime command failed: {args}")
    return completed.stdout.strip()


context = command("context", "show")
endpoint = json.loads(
    command(
        "context",
        "inspect",
        "--format",
        "{{json .Endpoints.docker.Host}}",
        context,
    )
)
if context != "default" or endpoint != "unix:///var/run/docker.sock":
    raise SystemExit(f"Docker runtime endpoint drift: {context}:{endpoint}")
info = json.loads(command("info", "--format", "{{json .}}"))
version = json.loads(command("version", "--format", "{{json .}}"))
server = version.get("Server") if isinstance(version, dict) else None
if not isinstance(info, dict) or not isinstance(server, dict):
    raise SystemExit("Docker runtime daemon receipt missing")
expected_info_fields = {
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
}
expected_version_fields = {
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
}
if set(expected.get("daemon_info", {})) != expected_info_fields or set(
    expected.get("daemon_version", {})
) != expected_version_fields:
    raise SystemExit("Docker runtime frozen field set drift")
live_info = {name: info.get(name) for name in expected_info_fields}
live_version = {name: server.get(name) for name in expected_version_fields}
socket_path = Path("/var/run/docker.sock")
socket_stat = socket_path.stat(follow_symlinks=False)
live_socket = {
    "declared_path": str(socket_path),
    "realpath": str(socket_path.resolve(strict=True)),
    "st_dev": socket_stat.st_dev,
    "st_ino": socket_stat.st_ino,
    "st_mode": stat.S_IMODE(socket_stat.st_mode),
    "st_uid": socket_stat.st_uid,
    "st_gid": socket_stat.st_gid,
}
if (
    socket_path.is_symlink()
    or not stat.S_ISSOCK(socket_stat.st_mode)
    or expected.get("context") != context
    or expected.get("endpoint") != endpoint
    or expected.get("socket") != live_socket
    or expected.get("daemon_info") != live_info
    or expected.get("daemon_version") != live_version
):
    raise SystemExit("Docker runtime daemon identity drift")
print(f"I135_DOCKER_RUNTIME_OK phase={phase} daemon_id={live_info['ID']}")
PY
}

PRIOR_SMOKE_SECONDS=$(python3 - "$MANIFEST" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["resource_gate"]["prior_smoke_gpu_seconds"])
PY
)
CEILING_SECONDS=$((TOTAL_CEILING_SECONDS - PRIOR_SMOKE_SECONDS))
if [ "$CEILING_SECONDS" -le 0 ]; then
  abort "G9-no-analytic-budget prior_smoke_seconds=$PRIOR_SMOKE_SECONDS"
fi
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0="$STACK/UniAD"
cd "$STACK/NeuroNCAP" || abort "neuro-ncap-missing"
SCHEDULE_TARGET="$STACK/UniAD/dose_schedules.json"
DECISION_ROOT="$STACK/UniAD/i135-decisions"

BASE_DIR=$STACK
NUSCENES_PATH=/datasets/nuscenes-full
MODEL_NAME=UniAD
MODEL_FOLDER=$BASE_DIR/UniAD
MODEL_CHECKPOINT_PATH=ckpts/uniad_base_e2e.pth
MODEL_CFG_PATH=projects/configs/stage2_e2e/inference_e2e.py
MODEL_IMAGE=sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb
RENDERING_FOLDER=$BASE_DIR/neurad-studio
RENDERING_CHECKPOITNS_PATH=checkpoints
RENDERING_IMAGE=sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c
NCAP_FOLDER=$BASE_DIR/NeuroNCAP
NCAP_IMAGE=sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce

CONTAINER_CONTROL_ROOT=$(mktemp -d /tmp/sentinel-i135-control.XXXXXX) \
  || abort "container-control-root-create"
CONTAINER_CONTROL_ROOT_ID=$(stat -Lc '%d:%i' "$CONTAINER_CONTROL_ROOT") || {
  rmdir "$CONTAINER_CONTROL_ROOT" >/dev/null 2>&1 || true
  CONTAINER_CONTROL_ROOT=
  abort "container-control-root-identity"
}
DOCKER_WRAPPER_SHA=$(python3 - "$CONTAINER_CONTROL_ROOT/docker" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = r'''#!/bin/bash
set -euo pipefail

: "${SENTINEL_DOCKER_BIN:?SENTINEL_DOCKER_BIN must be set}"
: "${SENTINEL_DOCKER_BIN_SHA256:?SENTINEL_DOCKER_BIN_SHA256 must be set}"
if [ ! -f "$SENTINEL_DOCKER_BIN" ] || [ ! -x "$SENTINEL_DOCKER_BIN" ] \
  || [ -L "$SENTINEL_DOCKER_BIN" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL docker-binary" >&2
  exit 125
fi
OBSERVED_DOCKER_SHA=$(sha256sum "$SENTINEL_DOCKER_BIN" | awk '{print $1}')
if [ "$OBSERVED_DOCKER_SHA" != "$SENTINEL_DOCKER_BIN_SHA256" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL docker-binary-drift" >&2
  exit 125
fi
if [ "$#" -lt 1 ]; then
  echo "I135_DOCKER_WRAPPER_FAIL command-missing" >&2
  exit 125
fi
COMMAND=$1
shift
if [ "$COMMAND" != "run" ]; then
  exec "$SENTINEL_DOCKER_BIN" "$COMMAND" "$@"
fi
: "${SENTINEL_MANIFEST_SHA256:?SENTINEL_MANIFEST_SHA256 must be set}"
: "${SENTINEL_BLOCK_ORDINAL:?SENTINEL_BLOCK_ORDINAL must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT:?SENTINEL_CONTAINER_CONTROL_ROOT must be set}"
: "${SENTINEL_CONTAINER_CID_DIR:?SENTINEL_CONTAINER_CID_DIR must be set}"
if ! [[ "$SENTINEL_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] \
  || ! [[ "$SENTINEL_BLOCK_ORDINAL" =~ ^([0-9]|[1-9][0-9]|1[01][0-9])$ ]] \
  || [ "$SENTINEL_CONTAINER_CID_DIR" \
    != "$SENTINEL_CONTAINER_CONTROL_ROOT/block-$SENTINEL_BLOCK_ORDINAL" ] \
  || [ -L "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ -L "$SENTINEL_CONTAINER_CID_DIR" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CID_DIR" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL control-contract" >&2
  exit 125
fi
ARGS=("$@")
NAME=
ROLE=
EXPECTED_IMAGE=
for ((INDEX = 0; INDEX < ${#ARGS[@]}; INDEX += 1)); do
  ARG=${ARGS[$INDEX]}
  if [ "$ARG" = "--name" ]; then
    if [ $((INDEX + 1)) -ge ${#ARGS[@]} ]; then
      echo "I135_DOCKER_WRAPPER_FAIL name-value" >&2
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
    echo "I135_DOCKER_WRAPPER_FAIL unexpected-name:$NAME" >&2
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
  echo "I135_DOCKER_WRAPPER_FAIL image:$ROLE:$IMAGE_MATCHES" >&2
  exit 125
fi
CID_FILE=$SENTINEL_CONTAINER_CID_DIR/$ROLE.cid
if [ -e "$CID_FILE" ] || [ -L "$CID_FILE" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL cid-preexists:$ROLE" >&2
  exit 125
fi
exec "$SENTINEL_DOCKER_BIN" run \
  --label sentinel.mission=iter135 \
  --label "sentinel.manifest=$SENTINEL_MANIFEST_SHA256" \
  --label "sentinel.block=$SENTINEL_BLOCK_ORDINAL" \
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
) || abort "docker-wrapper-create"

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
    root.parent != Path("/tmp")
    or not root.name.startswith("sentinel-i135-control.")
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
    raise SystemExit("container control contract drift")
PY
}
verify_container_control || abort "container-control-verification"

verify_output_storage_identity() {
  local PHASE=$1 REQUIRE_EMPTY=$2
  python3 - "$MANIFEST" "$OUTPUT_ROOT" "$OUTPUT_ROOT_ID" "$PHASE" "$REQUIRE_EMPTY" <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

manifest_text, output_text, expected_identity, phase, require_empty_text = sys.argv[1:]
if phase not in {"analytic-arm", "before-block", "after-block", "before-done"}:
    raise SystemExit(f"storage verification phase drift: {phase}")
if require_empty_text not in {"0", "1"}:
    raise SystemExit("storage empty policy drift")
require_empty = require_empty_text == "1"
manifest = json.loads(Path(manifest_text).read_bytes())
storage = manifest.get("storage_gate")
environment = manifest.get("environment_receipts")
devices = environment.get("storage_devices") if isinstance(environment, dict) else None
expected_root = Path("/datasets/nuscenes-full/sentinel-i135-outoutput")
output = Path(output_text)
mount = Path("/datasets/nuscenes-full")
if (
    not isinstance(storage, dict)
    or storage.get("filesystem_path") != str(expected_root)
    or storage.get("filesystem_realpath") != str(expected_root)
    or storage.get("filesystem_is_symlink") is not False
    or storage.get("mount_target") != str(mount)
    or storage.get("mount_source") != "/dev/nvme0n2"
    or storage.get("mount_fstype") != "ext4"
    or storage.get("mount_uuid") != "9a98277e-b21f-4ffc-8f14-3f2235b43103"
):
    raise SystemExit("storage manifest identity drift")
if not isinstance(devices, dict) or set(devices) != {
    "filesystem_st_dev",
    "mount_st_dev",
    "root_st_dev",
}:
    raise SystemExit("storage device receipt drift")
if (
    output != expected_root
    or output.is_symlink()
    or not output.is_dir()
    or output.resolve(strict=True) != expected_root
    or mount.is_symlink()
    or not mount.is_dir()
    or mount.resolve(strict=True) != mount
):
    raise SystemExit("storage physical path drift")
cursor = Path("/")
for component in output.parts[1:]:
    cursor /= component
    if cursor.is_symlink():
        raise SystemExit(f"storage component symlink: {cursor}")
output_stat = output.stat()
mount_stat = mount.stat()
root_stat = Path("/").stat()
observed_identity = f"{output_stat.st_dev}:{output_stat.st_ino}"
observed_devices = {
    "filesystem_st_dev": output_stat.st_dev,
    "mount_st_dev": mount_stat.st_dev,
    "root_st_dev": root_stat.st_dev,
}
if observed_identity != expected_identity or observed_devices != devices:
    raise SystemExit(
        f"storage live identity drift: {observed_identity}/{observed_devices}!="
        f"{expected_identity}/{devices}"
    )
mount_row = subprocess.run(
    ["findmnt", "-n", "-o", "SOURCE,FSTYPE,UUID", "-T", str(output)],
    check=True,
    capture_output=True,
    text=True,
).stdout.split()
if mount_row != [
    "/dev/nvme0n2",
    "ext4",
    "9a98277e-b21f-4ffc-8f14-3f2235b43103",
]:
    raise SystemExit(f"storage live mount drift: {mount_row}")
entries = list(output.iterdir())
if require_empty and entries:
    raise SystemExit("storage output root lost empty arming state")
for directory, directories, files in os.walk(output, followlinks=False):
    directory_path = Path(directory)
    if directory_path.stat().st_dev != output_stat.st_dev:
        raise SystemExit(f"storage nested device drift: {directory_path}")
    for name in [*directories, *files]:
        path = directory_path / name
        if path.is_symlink():
            raise SystemExit(f"symlink in analytic output: {path}")
        if path.stat().st_dev != output_stat.st_dev:
            raise SystemExit(f"storage artifact device drift: {path}")
print(f"I135_STORAGE_IDENTITY_OK phase={phase} device={output_stat.st_dev}")
PY
}

verify_block_runtime_inputs() {
  local SCENARIO_CLASS=$1 SEQUENCE=$2 EXPECTED_SERVER_SHA=$3 PHASE=$4
  verify_docker_runtime_identity "$PHASE" || return 1
  verify_dataset_runtime_identity "$PHASE" || return 1
  python3 - "$MANIFEST" "$SCHEDULE_TARGET" "$STACK/UniAD/inference/server.py" \
    "$EXPECTED_SERVER_SHA" "$SCENARIO_CLASS" "$SEQUENCE" "$PHASE" \
    "$MODEL_IMAGE" "$RENDERING_IMAGE" "$NCAP_IMAGE" \
    "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

(
    manifest_text,
    schedule_text,
    server_text,
    expected_server_sha,
    scenario_class,
    sequence,
    phase,
    model_image,
    rendering_image,
    ncap_image,
    docker_text,
    docker_identity,
    docker_sha256,
) = sys.argv[1:]
if phase not in {"before", "after"}:
    raise SystemExit(f"invalid runtime verification phase: {phase}")
classes = {
    "stationary": {"0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"},
    "frontal": {"0103", "0106", "0110", "0346", "0923"},
    "side": {"0103", "0108", "0110", "0278", "0921"},
}
if scenario_class not in classes or sequence not in classes[scenario_class]:
    raise SystemExit(f"invalid runtime pair: {scenario_class}/{sequence}")
if len(expected_server_sha) != 64 or any(
    character not in "0123456789abcdef" for character in expected_server_sha
):
    raise SystemExit("invalid patched server digest")


def stable_receipt(path: Path) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path.absolute():
        raise SystemExit(f"runtime input is not a physical regular file: {path}")
    path_before = path.stat()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fd_before = os.fstat(descriptor)
        if (path_before.st_dev, path_before.st_ino) != (fd_before.st_dev, fd_before.st_ino):
            raise SystemExit(f"runtime input open race: {path}")
        digest = hashlib.sha256()
        byte_count = 0
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                digest.update(chunk)
                byte_count += len(chunk)
        fd_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat()
    before_identity = (
        path_before.st_dev,
        path_before.st_ino,
        path_before.st_size,
        path_before.st_mtime_ns,
    )
    fd_identity = (
        fd_before.st_dev,
        fd_before.st_ino,
        fd_before.st_size,
        fd_before.st_mtime_ns,
    )
    after_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if before_identity != fd_identity or fd_identity != after_identity or byte_count != fd_before.st_size:
        raise SystemExit(f"runtime input changed while hashing: {path}")
    return digest.hexdigest(), byte_count


manifest = json.loads(Path(manifest_text).read_bytes())
artifacts = manifest.get("remote_artifacts")
if not isinstance(artifacts, list) or len(artifacts) != 82:
    raise SystemExit("runtime remote artifact cardinality drift")
by_role = {}
for row in artifacts:
    if not isinstance(row, dict) or set(row) != {"role", "path", "sha256", "bytes"}:
        raise SystemExit("runtime remote artifact schema drift")
    role = row.get("role")
    if not isinstance(role, str) or role in by_role:
        raise SystemExit(f"runtime remote artifact role drift: {role}")
    by_role[role] = row
if (
    sum(role.startswith("scenario:") for role in by_role) != 20
    or sum(role.startswith("renderer:") for role in by_role) != 42
    or "uniad_server_baseline" not in by_role
):
    raise SystemExit("runtime remote artifact role-set drift")
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
    raise SystemExit("runtime selected role-set drift")
for role in sorted(selected_roles):
    row = by_role[role]
    path = Path(row["path"])
    actual_sha, actual_bytes = stable_receipt(path)
    if actual_sha != row["sha256"] or actual_bytes != row["bytes"]:
        raise SystemExit(
            f"runtime artifact drift: {role}:{actual_sha}/{actual_bytes}!="
            f"{row['sha256']}/{row['bytes']}"
        )

server = Path(server_text)
server_sha, _server_bytes = stable_receipt(server)
if server_sha != expected_server_sha:
    raise SystemExit(f"runtime patched server drift: {server_sha}!={expected_server_sha}")

schedule = Path(schedule_text)
schedule_receipt = manifest.get("hash_bound_files", {}).get("dose_schedules.json")
if not isinstance(schedule_receipt, dict) or set(schedule_receipt) != {
    "source_path",
    "sha256",
    "bytes",
}:
    raise SystemExit("runtime schedule receipt drift")
schedule_sha, schedule_bytes = stable_receipt(schedule)
if (
    stat.S_IMODE(schedule.stat().st_mode) != 0o444
    or schedule_sha != schedule_receipt["sha256"]
    or schedule_bytes != schedule_receipt["bytes"]
):
    raise SystemExit("runtime schedule target drift")

expected_images = {
    "uniad:latest": model_image,
    "neurad:latest": rendering_image,
    "ncap:latest": ncap_image,
}
docker_binary = Path(docker_text)
docker_sha, _docker_bytes = stable_receipt(docker_binary)
if (
    f"{docker_binary.stat().st_dev}:{docker_binary.stat().st_ino}" != docker_identity
    or docker_sha != docker_sha256
):
    raise SystemExit("runtime Docker client identity drift")
images = manifest.get("container_images")
if not isinstance(images, dict) or set(images) != set(expected_images):
    raise SystemExit("runtime image receipt set drift")
for name, expected_image in expected_images.items():
    row = images.get(name)
    if not isinstance(row, dict) or row.get("image_id") != expected_image:
        raise SystemExit(f"runtime image receipt drift: {name}")
    observed = subprocess.run(
        [str(docker_binary), "image", "inspect", "--format", "{{.Id}}", expected_image],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    if observed != expected_image:
        raise SystemExit(f"runtime image identity drift: {name}:{observed}")
print(
    f"I135_BLOCK_RUNTIME_INPUTS_OK phase={phase} "
    f"pair={scenario_class}/{sequence} roles={len(selected_roles)}"
)
PY
}

map_arm() {
  case "$1" in
    off_baseline) echo "off 0 $UNION_PATCH none 8f6ed6a9bbeefc93b0bf7ee2f15b4843921475a0eded3719db59a8ad38538056" ;;
    released_union_semantic_reference) echo "union 1 $UNION_PATCH none 8f6ed6a9bbeefc93b0bf7ee2f15b4843921475a0eded3719db59a8ad38538056" ;;
    blind_0_5x) echo "blind_0_5x 1 $BLIND_PATCH blind_0_5x b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf" ;;
    blind_1_0x) echo "blind_1_0x 1 $BLIND_PATCH blind_1_0x b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf" ;;
    blind_1_5x) echo "blind_1_5x 1 $BLIND_PATCH blind_1_5x b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf" ;;
    blind_2_0x) echo "blind_2_0x 1 $BLIND_PATCH blind_2_0x b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf" ;;
    *) return 1 ;;
  esac
}

record_owned_container() {
  local ID=$1 ROLE=$2 INDEX KNOWN_ID KNOWN_ROLE
  if ! [[ "$ID" =~ ^[0-9a-f]{64}$ ]] \
    || ! [[ "$ROLE" =~ ^(renderer|model|ncap)$ ]]; then
    echo "I135_CONTAINER_OWNERSHIP_FAIL malformed-receipt=$ROLE:$ID"
    return 85
  fi
  for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX += 1)); do
    KNOWN_ID=${OWNED_CONTAINER_IDS[$INDEX]}
    KNOWN_ROLE=${OWNED_CONTAINER_ROLES[$INDEX]}
    if [ "$KNOWN_ROLE" = "$ROLE" ] && [ "$KNOWN_ID" != "$ID" ]; then
      echo "I135_CONTAINER_OWNERSHIP_FAIL role-replacement=$ROLE:$KNOWN_ID!=$ID"
      return 85
    fi
    if [ "$KNOWN_ID" = "$ID" ]; then
      if [ "$KNOWN_ROLE" != "$ROLE" ]; then
        echo "I135_CONTAINER_OWNERSHIP_FAIL id-role-drift=$ID"
        return 85
      fi
      return 0
    fi
  done
  OWNED_CONTAINER_IDS+=("$ID")
  OWNED_CONTAINER_ROLES+=("$ROLE")
}

container_receipt_rows() {
  python3 - "$CURRENT_BLOCK_CID_DIR" "$CURRENT_BLOCK_ORDINAL" <<'PY'
import re
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
ordinal = sys.argv[2]
expected_root = Path("/tmp")
expected_names = {"renderer.cid", "model.cid", "ncap.cid"}
if (
    not ordinal.isdigit()
    or root.parent.parent != expected_root
    or not root.parent.name.startswith("sentinel-i135-control.")
    or root.name != f"block-{ordinal}"
    or root.is_symlink()
    or not root.is_dir()
    or root.resolve(strict=True) != root
):
    raise SystemExit("container cid directory contract drift")
names = {path.name for path in root.iterdir()}
if not names.issubset(expected_names):
    raise SystemExit("unexpected container cid receipt")
rows = []
for role in ("renderer", "model", "ncap"):
    path = root / f"{role}.cid"
    if not os.path.lexists(path):
        continue
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"container cid is not physical: {role}")
    container_id = path.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise SystemExit(f"container cid malformed: {role}")
    rows.append((role, container_id))
if len({container_id for _role, container_id in rows}) != len(rows):
    raise SystemExit("container cid identities are not unique")
for role, container_id in rows:
    print(role, container_id, sep="\t")
PY
}

capture_owned_containers() {
  local IDS_TEXT ID IDENTITY OBSERVED_ID OBSERVED_NAME OBSERVED_IMAGE RECEIPT_ROWS
  local OBSERVED_MISSION OBSERVED_MANIFEST OBSERVED_BLOCK OBSERVED_ROLE
  local EXPECTED_NAME EXPECTED_IMAGE LIVE_AFTER ROLE RECEIPT_ID
  local -a IDS
  IDS_TEXT=$(bounded_docker ps -aq --no-trunc) || return 81
  if [ -n "$IDS_TEXT" ]; then
    mapfile -t IDS <<<"$IDS_TEXT"
  else
    IDS=()
  fi
  for ID in "${IDS[@]}"; do
    if ! [[ "$ID" =~ ^[0-9a-f]{64}$ ]]; then
      echo "I135_CONTAINER_OWNERSHIP_FAIL malformed-id=$ID"
      return 82
    fi
    if ! IDENTITY=$(bounded_docker inspect --format \
      '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{index .Config.Labels "sentinel.mission"}}|{{index .Config.Labels "sentinel.manifest"}}|{{index .Config.Labels "sentinel.block"}}|{{index .Config.Labels "sentinel.role"}}' \
      "$ID"); then
      LIVE_AFTER=$(bounded_docker ps -aq --no-trunc) || return 83
      if printf '%s\n' "$LIVE_AFTER" | grep -Fxq "$ID"; then
        return 83
      fi
      ROLE=$(container_receipt_rows | awk -F '\t' -v id="$ID" '$2 == id {print $1}') \
        || return 83
      if ! [[ "$ROLE" =~ ^(renderer|model|ncap)$ ]]; then
        echo "I135_CONTAINER_OWNERSHIP_FAIL vanished-without-receipt=$ID"
        return 83
      fi
      record_owned_container "$ID" "$ROLE" || return 85
      continue
    fi
    IFS='|' read -r OBSERVED_ID OBSERVED_NAME OBSERVED_IMAGE OBSERVED_MISSION \
      OBSERVED_MANIFEST OBSERVED_BLOCK OBSERVED_ROLE <<<"$IDENTITY"
    case "$OBSERVED_ROLE" in
      renderer)
        EXPECTED_NAME=/renderer
        EXPECTED_IMAGE=$RENDERING_IMAGE
        ;;
      model)
        EXPECTED_NAME=/model
        EXPECTED_IMAGE=$MODEL_IMAGE
        ;;
      ncap)
        EXPECTED_NAME=
        EXPECTED_IMAGE=$NCAP_IMAGE
        ;;
      *)
        echo "I135_CONTAINER_OWNERSHIP_FAIL unowned-id=$ID identity=$IDENTITY"
        return 84
        ;;
    esac
    if [ "$OBSERVED_ID" != "$ID" ] \
      || [ "$OBSERVED_IMAGE" != "$EXPECTED_IMAGE" ] \
      || [ "$OBSERVED_MISSION" != "iter135" ] \
      || [ "$OBSERVED_MANIFEST" != "$EXPECTED_MANIFEST_SHA" ] \
      || [ "$OBSERVED_BLOCK" != "$CURRENT_BLOCK_ORDINAL" ] \
      || { [ -n "$EXPECTED_NAME" ] && [ "$OBSERVED_NAME" != "$EXPECTED_NAME" ]; } \
      || { [ "$OBSERVED_ROLE" = "ncap" ] \
        && { [ "$OBSERVED_NAME" = "/renderer" ] || [ "$OBSERVED_NAME" = "/model" ]; }; }; then
      echo "I135_CONTAINER_OWNERSHIP_FAIL id=$ID identity=$IDENTITY"
      return 84
    fi
    record_owned_container "$ID" "$OBSERVED_ROLE" || return 85
  done
  RECEIPT_ROWS=$(container_receipt_rows) || return 86
  if [ -n "$RECEIPT_ROWS" ]; then
    while IFS=$'\t' read -r ROLE RECEIPT_ID; do
      LIVE_AFTER=$(bounded_docker ps -aq --no-trunc) || return 86
      if ! printf '%s\n' "$LIVE_AFTER" | grep -Fxq "$RECEIPT_ID"; then
        record_owned_container "$RECEIPT_ID" "$ROLE" || return 85
      fi
    done <<<"$RECEIPT_ROWS"
  fi
}

verify_container_quiescence() {
  local PHASE=$1 START_MS NOW_MS DEADLINE_MS QUIET_START_MS='' IDS_TEXT
  START_MS=$(python3 - <<'PY'
import time

print(time.monotonic_ns() // 1_000_000)
PY
  ) || return 61
  DEADLINE_MS=$((START_MS + CONTAINER_QUIESCENCE_CEILING_SECONDS * 1000))
  while :; do
    NOW_MS=$(python3 - <<'PY'
import time

print(time.monotonic_ns() // 1_000_000)
PY
    ) || return 61
    if [ "$NOW_MS" -ge "$DEADLINE_MS" ]; then
      echo "I135_CONTAINER_QUIESCENCE_FAIL phase=$PHASE reason=deadline"
      return 62
    fi
    IDS_TEXT=$(bounded_docker ps -aq --no-trunc) || return 63
    if [ -z "$IDS_TEXT" ]; then
      if [ -z "$QUIET_START_MS" ]; then
        QUIET_START_MS=$NOW_MS
      elif [ $((NOW_MS - QUIET_START_MS)) \
        -ge $((CONTAINER_QUIET_SECONDS * 1000)) ]; then
        echo "I135_CONTAINER_QUIESCENCE_OK phase=$PHASE quiet_seconds=$CONTAINER_QUIET_SECONDS"
        return 0
      fi
    else
      QUIET_START_MS=''
      capture_owned_containers || return 64
      cleanup_containers || return 65
    fi
    sleep 0.25
  done
}

verify_container_receipts() {
  local ROLE ID INDEX FOUND COUNT=0
  while IFS=$'\t' read -r ROLE ID; do
    FOUND=0
    for ((INDEX = 0; INDEX < ${#OWNED_CONTAINER_IDS[@]}; INDEX += 1)); do
      if [ "${OWNED_CONTAINER_IDS[$INDEX]}" = "$ID" ] \
        && [ "${OWNED_CONTAINER_ROLES[$INDEX]}" = "$ROLE" ]; then
        FOUND=1
      fi
    done
    if [ "$FOUND" != "1" ]; then
      echo "I135_CONTAINER_RECEIPT_FAIL unseen=$ROLE:$ID"
      return 76
    fi
    echo "I135_CONTAINER_RECEIPT role=$ROLE id=$ID block=$CURRENT_BLOCK_ORDINAL"
    COUNT=$((COUNT + 1))
  done < <(python3 - "$CURRENT_BLOCK_CID_DIR" "$CURRENT_BLOCK_ORDINAL" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
ordinal = sys.argv[2]
expected = {"renderer.cid", "model.cid", "ncap.cid"}
if (
    root.name != f"block-{ordinal}"
    or root.is_symlink()
    or not root.is_dir()
    or root.resolve(strict=True) != root
    or {path.name for path in root.iterdir()} != expected
):
    raise SystemExit("container cid directory contract drift")
rows = []
for role in ("renderer", "model", "ncap"):
    path = root / f"{role}.cid"
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"container cid is not physical: {role}")
    container_id = path.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise SystemExit(f"container cid malformed: {role}")
    rows.append((role, container_id))
if len({container_id for _role, container_id in rows}) != 3:
    raise SystemExit("container cid identities are not unique")
for role, container_id in rows:
    print(role, container_id, sep="\t")
PY
  ) || return 77
  [ "$COUNT" = "3" ] || return 77
}

block_stream() {
  python3 - "$MANIFEST" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1]))
for block in manifest["execution_blocks"]:
    print(
        block["ordinal"],
        block["arm_id"],
        block["scenario_class"],
        block["sequence"],
        sep="\t",
    )
PY
}

verify_block_plan_row() {
  local ORDINAL=$1 ARM_ID=$2 SCENARIO_CLASS=$3 SEQUENCE=$4
  python3 - "$MANIFEST" "$ORDINAL" "$ARM_ID" "$SCENARIO_CLASS" "$SEQUENCE" <<'PY'
import json
import sys

manifest_text, ordinal_text, arm_id, scenario_class, sequence = sys.argv[1:]
try:
    ordinal = int(ordinal_text)
except ValueError as error:
    raise SystemExit(f"block ordinal is not an integer: {ordinal_text}") from error
blocks = json.load(open(manifest_text))["execution_blocks"]
if not 0 <= ordinal < len(blocks):
    raise SystemExit(f"block ordinal outside manifest: {ordinal}")
block = blocks[ordinal]
observed = (ordinal, arm_id, scenario_class, sequence)
expected = (
    block.get("ordinal"),
    block.get("arm_id"),
    block.get("scenario_class"),
    block.get("sequence"),
)
if observed != expected or block.get("run_indices") != list(range(20)):
    raise SystemExit(f"block plan row drift: {observed}!={expected}")
PY
}

validate_block() {
  local ARM_ID=$1 SCENARIO=$2 SEQ=$3 DOSE=$4 OUTPUT_DIR=$5 OUTPUT_DIR_ID=$6
  local DECISION_LOG=$7 DECISION_LOG_ID=$8
  python3 - "$ARM_ID" "$SCENARIO" "$SEQ" "$DOSE" "$OUTPUT_DIR" \
    "$OUTPUT_DIR_ID" "$DECISION_LOG" "$DECISION_LOG_ID" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path

(
    arm,
    scenario_class,
    sequence,
    dose,
    output_text,
    output_identity,
    decision_text,
    decision_identity,
) = sys.argv[1:]
output = Path(output_text)
decision = Path(decision_text)
problems = []


def identity(path: Path) -> str:
    observed = path.stat(follow_symlinks=False)
    return f"{observed.st_dev}:{observed.st_ino}"


def stable_regular_bytes(path: Path, expected_identity: str | None = None) -> bytes:
    if path.is_symlink():
        raise RuntimeError(f"symlink:{path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError(f"not-regular:{path}")
        if expected_identity is not None and (
            f"{before.st_dev}:{before.st_ino}" != expected_identity
        ):
            raise RuntimeError(f"identity:{path}")
        payload = b""
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while chunk := stream.read(1024 * 1024):
                payload += chunk
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    before_row = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_row = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_row = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if before_row != after_row or before_row != path_row or len(payload) != before.st_size:
        raise RuntimeError(f"read-race:{path}")
    return payload


try:
    output_stat = output.stat(follow_symlinks=False)
    if (
        output.is_symlink()
        or not stat.S_ISDIR(output_stat.st_mode)
        or output.resolve(strict=True) != output
        or identity(output) != output_identity
    ):
        problems.append("output-directory-identity")
except OSError as error:
    problems.append(f"output-directory:{type(error).__name__}")
    output_stat = None
for run in range(20):
    root = output / f"run_{run}"
    for name in ("ego_poses.json", "metrics.json", "actors.json"):
        path = root / name
        try:
            payload = stable_regular_bytes(path)
            if output_stat is not None and path.stat(follow_symlinks=False).st_dev != output_stat.st_dev:
                raise RuntimeError(f"device:{path}")
            if not payload:
                raise RuntimeError(f"empty:{path}")
        except (OSError, RuntimeError):
            problems.append(f"output-missing:run_{run}/{name}")
if output_stat is not None:
    for directory, directories, files in os.walk(output, followlinks=False):
        directory_path = Path(directory)
        for name in [*directories, *files]:
            path = directory_path / name
            try:
                observed = path.stat(follow_symlinks=False)
            except OSError as error:
                problems.append(f"output-stat:{path}:{type(error).__name__}")
                continue
            if path.is_symlink() or observed.st_dev != output_stat.st_dev:
                problems.append(f"output-physical-contract:{path}")
try:
    decision_payload = stable_regular_bytes(decision, decision_identity)
except (OSError, RuntimeError):
    problems.append("decision-log-missing")
else:
    resets = []
    identities = []
    for lineno, line in enumerate(decision_payload.decode(errors="replace").splitlines(), 1):
        try:
            row = json.loads(line)
        except ValueError:
            problems.append(f"decision-json:{lineno}")
            continue
        if row.get("reset"):
            resets.append(row.get("run"))
        if row.get("block_identity") is True:
            identities.append(
                (row.get("arm"), row.get("class"), row.get("pair"))
            )
        if row.get("schedule_missing") or row.get("intervene_err"):
            problems.append(f"decision-runtime-error:{lineno}")
        if arm.startswith("blind_") and (row.get("frame") or row.get("brake")):
            if row.get("class") != scenario_class or row.get("pair") != sequence:
                problems.append(f"decision-pair:{lineno}")
            if row.get("dose") != dose:
                problems.append(f"decision-dose:{lineno}")
            if not isinstance(row.get("frame_index"), int) or row["frame_index"] < 0:
                problems.append(f"decision-frame:{lineno}")
    if resets != list(range(20)):
        problems.append(f"decision-resets:{resets}")
    expected_identity = [(arm, scenario_class, sequence)] if not arm.startswith("blind_") else []
    if identities != expected_identity:
        problems.append(f"decision-block-identity:{identities}")
try:
    if identity(output) != output_identity or identity(decision) != decision_identity:
        problems.append("block-path-identity-changed-during-validation")
except OSError:
    problems.append("block-path-missing-after-validation")
if problems:
    print("I135_BLOCK_VALIDATION_FAIL", *problems, sep="\n - ")
    raise SystemExit(1)
print(f"I135_BLOCK_VALIDATION_OK arm={arm} pair={scenario_class}/{sequence}")
PY
}

run_block() {
  local ORDINAL=$1 ARM_ID=$2 SCENARIO=$3 SEQ=$4
  local SHORT ENABLED PATCH DOSE EXPECTED_PATCHED_SERVER_SHA
  read -r SHORT ENABLED PATCH DOSE EXPECTED_PATCHED_SERVER_SHA <<<"$(map_arm "$ARM_ID")" || return 90

  git -C "$STACK/UniAD" diff --cached --quiet -- || return 99
  if [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" != "$BASELINE_SERVER_SHA" ]; then
    return 98
  fi
  SERVER_TOUCHED=1
  python3 "$PATCH" || return 92
  if [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" != "$EXPECTED_PATCHED_SERVER_SHA" ]; then
    return 89
  fi
  git -C "$STACK/UniAD" diff --cached --quiet -- || return 88
  verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$EXPECTED_PATCHED_SERVER_SHA" before \
    || return 80

  local DECISION_DIR="$DECISION_ROOT/$SHORT"
  local DECISION_LOG="$DECISION_DIR/$SCENARIO-$SEQ.jsonl"
  local DECISION_CONTAINER="/model/i135-decisions/$SHORT/$SCENARIO-$SEQ.jsonl"
  local OUTPUT_DIR="$OUTPUT_ROOT/i135-$SHORT/$SCENARIO-$SEQ"
  local BLOCK_PATH_IDENTITIES DECISION_LOG_ID OUTPUT_DIR_ID
  BLOCK_PATH_IDENTITIES=$(python3 - \
    "$DECISION_ROOT" "$DECISION_ROOT_ID" "$OUTPUT_ROOT" "$OUTPUT_ROOT_ID" \
    "$SHORT" "$ARM_ID" "$SCENARIO" "$SEQ" "$DECISION_LOG" "$OUTPUT_DIR" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path

(
    decision_root_text,
    decision_root_identity,
    output_root_text,
    output_root_identity,
    short,
    arm,
    scenario_class,
    sequence,
    decision_text,
    output_text,
) = sys.argv[1:]
arm_shorts = {
    "off_baseline": "off",
    "released_union_semantic_reference": "union",
    "blind_0_5x": "blind_0_5x",
    "blind_1_0x": "blind_1_0x",
    "blind_1_5x": "blind_1_5x",
    "blind_2_0x": "blind_2_0x",
}
if arm_shorts.get(arm) != short:
    raise SystemExit("block path arm mapping drift")
if scenario_class not in {"stationary", "frontal", "side"} or not (
    len(sequence) == 4 and sequence.isdigit()
):
    raise SystemExit("block path pair contract drift")
decision_root = Path(decision_root_text)
output_root = Path(output_root_text)
decision = Path(decision_text)
output = Path(output_text)
expected_decision_root = Path("/opt/sentinel-stack/UniAD/i135-decisions")
expected_output_root = Path("/datasets/nuscenes-full/sentinel-i135-outoutput")
pair_name = f"{scenario_class}-{sequence}"
expected_decision = expected_decision_root / short / f"{pair_name}.jsonl"
expected_output = expected_output_root / f"i135-{short}" / pair_name
if (
    decision_root != expected_decision_root
    or output_root != expected_output_root
    or decision != expected_decision
    or output != expected_output
):
    raise SystemExit("block path canonical contract drift")


def open_bound_root(path: Path, expected_identity: str) -> int:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    observed = os.fstat(descriptor)
    if (
        f"{observed.st_dev}:{observed.st_ino}" != expected_identity
        or not stat.S_ISDIR(observed.st_mode)
        or path.is_symlink()
        or path.resolve(strict=True) != path
    ):
        os.close(descriptor)
        raise SystemExit(f"block root identity drift: {path}")
    return descriptor


def open_or_create_directory(parent_fd: int, name: str) -> tuple[int, bool]:
    created = False
    try:
        os.mkdir(name, 0o755, dir_fd=parent_fd)
        created = True
        os.fsync(parent_fd)
    except FileExistsError:
        pass
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=parent_fd,
    )
    observed = os.fstat(descriptor)
    if not stat.S_ISDIR(observed.st_mode):
        os.close(descriptor)
        raise SystemExit(f"block parent is not a physical directory: {name}")
    return descriptor, created


decision_root_fd = open_bound_root(decision_root, decision_root_identity)
output_root_fd = open_bound_root(output_root, output_root_identity)
decision_arm_fd = -1
output_arm_fd = -1
decision_fd = -1
output_fd = -1
decision_arm_created = False
output_arm_created = False
decision_created = False
output_created = False
decision_identity = None
output_identity = None
try:
    decision_arm_fd, decision_arm_created = open_or_create_directory(
        decision_root_fd, short
    )
    output_arm_fd, output_arm_created = open_or_create_directory(
        output_root_fd, f"i135-{short}"
    )
    os.mkdir(pair_name, 0o755, dir_fd=output_arm_fd)
    output_created = True
    os.fsync(output_arm_fd)
    output_fd = os.open(
        pair_name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=output_arm_fd,
    )
    output_stat = os.fstat(output_fd)
    output_identity = (output_stat.st_dev, output_stat.st_ino)
    if (
        not stat.S_ISDIR(output_stat.st_mode)
        or output_stat.st_dev != os.fstat(output_root_fd).st_dev
    ):
        raise SystemExit("block output is not a physical directory")

    decision_fd = os.open(
        f"{pair_name}.jsonl",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o644,
        dir_fd=decision_arm_fd,
    )
    decision_created = True
    payload = b""
    if arm in {"off_baseline", "released_union_semantic_reference"}:
        payload = (
            json.dumps(
                {
                    "block_identity": True,
                    "arm": arm,
                    "class": scenario_class,
                    "pair": sequence,
                },
                sort_keys=True,
            )
            + "\n"
        ).encode()
    if payload and os.write(decision_fd, payload) != len(payload):
        raise SystemExit("short decision identity write")
    os.fsync(decision_fd)
    decision_stat = os.fstat(decision_fd)
    decision_identity = (decision_stat.st_dev, decision_stat.st_ino)
    if (
        not stat.S_ISREG(decision_stat.st_mode)
        or stat.S_IMODE(decision_stat.st_mode) != 0o644
        or decision_stat.st_dev != os.fstat(decision_arm_fd).st_dev
    ):
        raise SystemExit("block decision log is not a bound regular file")
    os.fsync(decision_arm_fd)
except BaseException:
    if decision_fd >= 0:
        os.close(decision_fd)
        decision_fd = -1
    if output_fd >= 0:
        os.close(output_fd)
        output_fd = -1
    if decision_created and decision_identity is not None:
        observed = os.stat(
            f"{pair_name}.jsonl", dir_fd=decision_arm_fd, follow_symlinks=False
        )
        if (observed.st_dev, observed.st_ino) == decision_identity:
            os.unlink(f"{pair_name}.jsonl", dir_fd=decision_arm_fd)
    if output_created and output_identity is not None:
        observed = os.stat(pair_name, dir_fd=output_arm_fd, follow_symlinks=False)
        if (observed.st_dev, observed.st_ino) == output_identity:
            os.rmdir(pair_name, dir_fd=output_arm_fd)
    if decision_arm_created:
        try:
            os.rmdir(short, dir_fd=decision_root_fd)
        except OSError:
            pass
    if output_arm_created:
        try:
            os.rmdir(f"i135-{short}", dir_fd=output_root_fd)
        except OSError:
            pass
    raise
finally:
    for descriptor in (
        decision_fd,
        output_fd,
        decision_arm_fd,
        output_arm_fd,
        decision_root_fd,
        output_root_fd,
    ):
        if descriptor >= 0:
            os.close(descriptor)
print(
    f"{decision_identity[0]}:{decision_identity[1]}",
    f"{output_identity[0]}:{output_identity[1]}",
)
PY
  ) || return 95
  read -r DECISION_LOG_ID OUTPUT_DIR_ID <<<"$BLOCK_PATH_IDENTITIES" || return 93
  if ! [[ "$DECISION_LOG_ID" =~ ^[0-9]+:[0-9]+$ \
    && "$OUTPUT_DIR_ID" =~ ^[0-9]+:[0-9]+$ ]]; then
    return 94
  fi
  python3 - "$DECISION_LOG" "$DECISION_LOG_ID" "$OUTPUT_DIR" "$OUTPUT_DIR_ID" <<'PY' \
    || return 91
import os
import stat
import sys
from pathlib import Path

decision = Path(sys.argv[1])
decision_identity = sys.argv[2]
output = Path(sys.argv[3])
output_identity = sys.argv[4]
decision_stat = decision.stat(follow_symlinks=False)
output_stat = output.stat(follow_symlinks=False)
if (
    decision.is_symlink()
    or not stat.S_ISREG(decision_stat.st_mode)
    or decision.resolve(strict=True) != decision
    or f"{decision_stat.st_dev}:{decision_stat.st_ino}" != decision_identity
    or output.is_symlink()
    or not stat.S_ISDIR(output_stat.st_mode)
    or output.resolve(strict=True) != output
    or f"{output_stat.st_dev}:{output_stat.st_ino}" != output_identity
):
    raise SystemExit("block staged path identity drift")
PY

  verify_container_control || return 78
  CURRENT_BLOCK_ORDINAL=$ORDINAL
  CURRENT_BLOCK_CID_DIR=$CONTAINER_CONTROL_ROOT/block-$ORDINAL
  if ! mkdir -m 0700 "$CURRENT_BLOCK_CID_DIR"; then
    return 77
  fi
  echo "I135_BLOCK_START ordinal=$ORDINAL arm=$ARM_ID pair=$SCENARIO/$SEQ"
  echo "##### I135BLOCK $ARM_ID $SCENARIO $SEQ #####"
  TIME_NOW="i135-$SHORT"
  local COMPOSE_RC=0
  local OWNERSHIP_RC=0
  local PRE_COMPOSE_ELAPSED COMPOSE_WALL_REMAINING COMPOSE_TIMEOUT_SECONDS
  PRE_COMPOSE_ELAPSED=$(monotonic_elapsed) || return 70
  COMPOSE_WALL_REMAINING=$((CEILING_SECONDS - PRE_COMPOSE_ELAPSED))
  if [ "$COMPOSE_WALL_REMAINING" -le "$TERMINATION_RESERVE_SECONDS" ]; then
    return 69
  fi
  COMPOSE_TIMEOUT_SECONDS=$((COMPOSE_WALL_REMAINING - TERMINATION_RESERVE_SECONDS))
  timeout --signal=TERM --kill-after=60s "$COMPOSE_TIMEOUT_SECONDS" env \
    PATH="$CONTAINER_CONTROL_ROOT:$PATH" \
    SENTINEL_DOCKER_BIN="$DOCKER_BIN" \
    SENTINEL_DOCKER_BIN_SHA256="$DOCKER_BIN_SHA" \
    SENTINEL_MANIFEST_SHA256="$EXPECTED_MANIFEST_SHA" \
    SENTINEL_BLOCK_ORDINAL="$ORDINAL" \
    SENTINEL_CONTAINER_CONTROL_ROOT="$CONTAINER_CONTROL_ROOT" \
    SENTINEL_CONTAINER_CID_DIR="$CURRENT_BLOCK_CID_DIR" \
    BASE_DIR="$BASE_DIR" NUSCENES_PATH="$NUSCENES_PATH" \
    MODEL_NAME="$MODEL_NAME" MODEL_FOLDER="$MODEL_FOLDER" \
    MODEL_CHECKPOINT_PATH="$MODEL_CHECKPOINT_PATH" MODEL_CFG_PATH="$MODEL_CFG_PATH" \
    MODEL_IMAGE="$MODEL_IMAGE" RENDERING_FOLDER="$RENDERING_FOLDER" \
    RENDERING_CHECKPOITNS_PATH="$RENDERING_CHECKPOITNS_PATH" \
    RENDERING_IMAGE="$RENDERING_IMAGE" NCAP_FOLDER="$NCAP_FOLDER" \
    NCAP_IMAGE="$NCAP_IMAGE" TIME_NOW="$TIME_NOW" \
    SENTINEL_ENABLED="$ENABLED" SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 \
    SENTINEL_CPA_MARGIN=1.5 SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
    SENTINEL_RELEASE_K=4 SENTINEL_DOSE_PAIR="$SCENARIO/$SEQ" \
    SENTINEL_DOSE_ID="$DOSE" SENTINEL_DOSE_SCHEDULE=/model/dose_schedules.json \
    SENTINEL_LOG="$DECISION_CONTAINER" SENTINEL_OUTPUT_ROOT="$OUTPUT_ROOT" \
    bash scripts/_docker_compose_release.sh "$SEQ" "$SCENARIO" \
      --scenario-category="$SCENARIO" --runs 20 &
  ACTIVE_COMPOSE_PID=$!
  while compose_process_running "$ACTIVE_COMPOSE_PID"; do
    local MONITOR_ELAPSED
    MONITOR_ELAPSED=$(monotonic_elapsed) || {
      OWNERSHIP_RC=1
      terminate_compose_process "$ACTIVE_COMPOSE_PID" || true
      break
    }
    if [ "$MONITOR_ELAPSED" -ge $((CEILING_SECONDS - TERMINATION_RESERVE_SECONDS)) ]; then
      OWNERSHIP_RC=1
      terminate_compose_process "$ACTIVE_COMPOSE_PID" || true
      break
    fi
    if capture_owned_containers; then
      :
    else
      OWNERSHIP_RC=$?
      terminate_compose_process "$ACTIVE_COMPOSE_PID" || true
      break
    fi
    sleep 0.2
  done
  if wait "$ACTIVE_COMPOSE_PID"; then
    COMPOSE_RC=0
  else
    COMPOSE_RC=$?
  fi
  ACTIVE_COMPOSE_PID=
  if capture_owned_containers; then
    :
  else
    OWNERSHIP_RC=$?
  fi
  if [ "$OWNERSHIP_RC" != "0" ]; then
    return 87
  fi
  if [ "$COMPOSE_RC" != "0" ]; then
    return 96
  fi
  if ! verify_container_receipts; then
    return 86
  fi
  cleanup_containers || return 73
  verify_container_quiescence "after-block-$ORDINAL" || return 74

  validate_block "$ARM_ID" "$SCENARIO" "$SEQ" "$DOSE" "$OUTPUT_DIR" \
    "$OUTPUT_DIR_ID" "$DECISION_LOG" "$DECISION_LOG_ID" || return 97
  verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$EXPECTED_PATCHED_SERVER_SHA" after \
    || return 79
  git -C "$STACK/UniAD" checkout HEAD -- inference/server.py || return 72
  if [ "$(sha256sum "$STACK/UniAD/inference/server.py" | awk '{print $1}')" != "$BASELINE_SERVER_SHA" ]; then
    return 71
  fi
  SERVER_TOUCHED=0
  echo "I135_BLOCK_OK ordinal=$ORDINAL arm=$ARM_ID pair=$SCENARIO/$SEQ runs=20"
}

BLOCK_PLAN=$(mktemp /tmp/sentinel-i135-block-plan.XXXXXX)
BLOCK_PLAN_ID=$(stat -Lc '%d:%i' "$BLOCK_PLAN") || abort "execution-block-plan-identity"
if ! block_stream > "$BLOCK_PLAN"; then
  abort "execution-block-stream-generation"
fi
if [ "$(wc -l < "$BLOCK_PLAN" | tr -d ' ')" != "120" ]; then
  abort "execution-block-stream-count"
fi
chmod 0444 "$BLOCK_PLAN" || abort "execution-block-plan-seal"
if ! exec 7< "$BLOCK_PLAN"; then
  abort "execution-block-plan-open"
fi
BLOCK_PLAN_FD_OPEN=1
BLOCK_PLAN_FD_ID=$(stat -Lc '%d:%i' "/proc/$$/fd/7") \
  || abort "execution-block-plan-fd-identity"
BLOCK_PLAN_PATH_ID=$(stat -Lc '%d:%i' "$BLOCK_PLAN") \
  || abort "execution-block-plan-path-identity"
if [ "$BLOCK_PLAN_FD_ID" != "$BLOCK_PLAN_ID" ] \
  || [ "$BLOCK_PLAN_PATH_ID" != "$BLOCK_PLAN_ID" ]; then
  abort "execution-block-plan-open-race"
fi

# Recheck the live boundary immediately before the persistent analytic lock is acquired.
ARMED_CONTAINER_IDS=$(bounded_docker ps -aq --no-trunc) \
  || abort "container-probe-at-analytic-arm"
if [ -n "$ARMED_CONTAINER_IDS" ]; then
  abort "containers-present-at-analytic-arm"
fi
ARMED_GPU_NAMES_TEXT=$(nvidia-smi --query-gpu=name --format=csv,noheader) \
  || abort "gpu-topology-probe-at-analytic-arm"
mapfile -t ARMED_GPU_NAMES <<<"$ARMED_GPU_NAMES_TEXT"
if [ "${#ARMED_GPU_NAMES[@]}" != "1" ] || [ "${ARMED_GPU_NAMES[0]}" != "NVIDIA L4" ]; then
  abort "live-gpu-topology-at-analytic-arm:${ARMED_GPU_NAMES[*]:-none}"
fi
ARMED_GPU_COMPUTE_PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader \
  | tr -d '[:space:]') || abort "gpu-process-probe-at-analytic-arm"
if [ -n "$ARMED_GPU_COMPUTE_PIDS" ]; then
  abort "live-gpu-process-at-analytic-arm"
fi
python3 - <<'PY' || abort "evaluator-process-at-analytic-arm"
import os
import re
import subprocess

patterns = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
rows = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines()
matches = []
for row in rows:
    pid_text, _, command = row.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid in {os.getpid(), os.getppid()}:
        continue
    if patterns.search(command):
        matches.append(f"{pid}:{command}")
if matches:
    print("I135_LIVE_EVALUATOR_PROCESS_FAIL", *matches, sep="\n - ")
    raise SystemExit(1)
PY

START_FREE_BYTES=$(python3 - "$OUTPUT_ROOT" <<'PY'
import shutil
import sys

print(shutil.disk_usage(sys.argv[1]).free)
PY
) || abort "G8-start-free-measurement"
if ! [[ "$START_FREE_BYTES" =~ ^[0-9]+$ ]] \
  || [ "$START_FREE_BYTES" -lt $((100 * 1024 * 1024 * 1024)) ] \
  || [ $((START_FREE_BYTES - 72380432384)) -lt $((25 * 1024 * 1024 * 1024)) ]; then
  abort "G8-storage-at-analytic-arm:$START_FREE_BYTES"
fi
verify_output_storage_identity analytic-arm 1 \
  || abort "storage-identity-at-analytic-arm"

PREFLIGHT_COUNTS=$(python3 - "$MANIFEST" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1]))
print(len(manifest["hash_bound_files"]), len(manifest["remote_artifacts"]))
PY
) || abort "preflight-summary-counts"
read -r PREFLIGHT_PAYLOADS PREFLIGHT_REMOTE <<<"$PREFLIGHT_COUNTS"
if ! [[ "$PREFLIGHT_PAYLOADS" =~ ^[1-9][0-9]*$ && "$PREFLIGHT_REMOTE" =~ ^[1-9][0-9]*$ ]]; then
  abort "preflight-summary-values:$PREFLIGHT_COUNTS"
fi

publish_analytic_lock() {
  python3 - "$LOCK" "$EXPECTED_MANIFEST_SHA" "$DATASET_RUNTIME_SNAPSHOT_SHA" \
    "$DOCKER_RUNTIME_SNAPSHOT_SHA" "$$" <<'PY'
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

lock = Path(sys.argv[1])
manifest_sha256 = sys.argv[2]
dataset_snapshot_sha256 = sys.argv[3]
docker_snapshot_sha256 = sys.argv[4]
pid = int(sys.argv[5])
if (
    not lock.parent.is_dir()
    or lock.parent.is_symlink()
    or lock.parent.resolve(strict=True) != lock.parent
    or lock.exists()
    or lock.is_symlink()
    or len(manifest_sha256) != 64
    or any(character not in "0123456789abcdef" for character in manifest_sha256)
    or len(dataset_snapshot_sha256) != 64
    or any(character not in "0123456789abcdef" for character in dataset_snapshot_sha256)
    or len(docker_snapshot_sha256) != 64
    or any(character not in "0123456789abcdef" for character in docker_snapshot_sha256)
):
    raise SystemExit("analytic lock publication contract drift")
payload = {
    "schema": "iter135.analytic_lock.v2",
    "manifest_sha256": manifest_sha256,
    "dataset_runtime_snapshot_sha256": dataset_snapshot_sha256,
    "docker_runtime_snapshot_sha256": docker_snapshot_sha256,
    "pid": pid,
    "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
}
descriptor, temporary_name = tempfile.mkstemp(
    prefix=f".{lock.name}.", suffix=".tmp", dir=lock.parent
)
temporary = Path(temporary_name)
published = False
temporary_stat = os.fstat(descriptor)
temporary_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o444)
    temporary_stat = temporary.stat()
    if (temporary_stat.st_dev, temporary_stat.st_ino) != temporary_identity:
        raise SystemExit("analytic lock temporary identity drift")
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
        raise SystemExit("analytic lock receipt verification failed")
    stat_result = lock.stat()
    print(f"{stat_result.st_dev}:{stat_result.st_ino}")
except BaseException:
    if temporary.exists() and not temporary.is_symlink() and temporary_identity is not None:
        observed = temporary.stat()
        if (observed.st_dev, observed.st_ino) == temporary_identity:
            temporary.unlink()
    if published and lock.exists() and not lock.is_symlink() and temporary_identity is not None:
        observed = lock.stat()
        if (observed.st_dev, observed.st_ino) == temporary_identity:
            lock.unlink()
    raise
PY
}

FINAL_ARM_CONTAINER_IDS=$(bounded_docker ps -aq --no-trunc) \
  || abort "container-probe-at-final-analytic-arm"
if [ -n "$FINAL_ARM_CONTAINER_IDS" ]; then
  abort "containers-present-at-final-analytic-arm"
fi
FINAL_ARM_GPU_COMPUTE_PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader \
  | tr -d '[:space:]') || abort "gpu-process-probe-at-final-analytic-arm"
if [ -n "$FINAL_ARM_GPU_COMPUTE_PIDS" ]; then
  abort "live-gpu-process-at-final-analytic-arm"
fi
python3 - <<'PY' || abort "evaluator-process-at-final-analytic-arm"
import os
import re
import subprocess

patterns = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
rows = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines()
for row in rows:
    pid_text, _, command = row.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid not in {os.getpid(), os.getppid()} and patterns.search(command):
        raise SystemExit(f"live evaluator appeared at final analytic arm: {pid}:{command}")
PY

verify_output_storage_identity analytic-arm 1 \
  || abort "storage-identity-at-final-analytic-arm"
verify_dataset_runtime_identity analytic-arm \
  || abort "dataset-identity-at-final-analytic-arm"
verify_docker_runtime_identity analytic-arm \
  || abort "docker-identity-at-final-analytic-arm"
verify_current_mission_state >/dev/null \
  || abort "mission-state-revoked-at-final-analytic-arm"
ANALYTIC_LOCK_ID=$(publish_analytic_lock) || abort "analytic-lock-receipt"
ANALYTIC_LOCK_OWNED=1

ANALYTIC_STAGING_IDS=$(python3 - "$SCHED" "$SCHEDULE_TARGET" "$DECISION_ROOT" <<'PY'
import hashlib
import os
import stat
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
decision_root = Path(sys.argv[3])
expected_target = Path("/opt/sentinel-stack/UniAD/dose_schedules.json")
expected_decision_root = Path("/opt/sentinel-stack/UniAD/i135-decisions")
if (
    target != expected_target
    or decision_root != expected_decision_root
    or source.is_symlink()
    or not source.is_file()
    or source.resolve(strict=True) != source.absolute()
    or target.parent.is_symlink()
    or target.parent.resolve(strict=True) != target.parent
    or decision_root.parent != target.parent
    or os.path.lexists(target)
    or os.path.lexists(decision_root)
):
    raise SystemExit("analytic staging path contract drift")
descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
try:
    before = os.fstat(descriptor)
    payload = b""
    with os.fdopen(descriptor, "rb", closefd=False) as stream:
        payload = stream.read()
    after = os.fstat(descriptor)
finally:
    os.close(descriptor)
identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
if identity_before != identity_after or len(payload) != before.st_size:
    raise SystemExit("schedule source changed while being read")

target_descriptor = -1
target_identity = None
root_identity = None
try:
    target_descriptor = os.open(
        target,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o444,
    )
    with os.fdopen(target_descriptor, "wb", closefd=True) as stream:
        target_descriptor = -1
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(target, 0o444, follow_symlinks=False)
    target_stat = target.stat(follow_symlinks=False)
    target_identity = (target_stat.st_dev, target_stat.st_ino)
    if (
        not stat.S_ISREG(target_stat.st_mode)
        or stat.S_IMODE(target_stat.st_mode) != 0o444
        or hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(payload).digest()
    ):
        raise SystemExit("schedule copy verification failed")
    os.mkdir(decision_root, 0o755)
    root_stat = decision_root.stat(follow_symlinks=False)
    root_identity = (root_stat.st_dev, root_stat.st_ino)
    if (
        not stat.S_ISDIR(root_stat.st_mode)
        or decision_root.is_symlink()
        or decision_root.resolve(strict=True) != decision_root
        or root_stat.st_dev != target_stat.st_dev
    ):
        raise SystemExit("decision root verification failed")
    parent_descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)
except BaseException:
    if target_descriptor >= 0:
        os.close(target_descriptor)
    if root_identity is not None and os.path.lexists(decision_root):
        observed = decision_root.stat(follow_symlinks=False)
        if (observed.st_dev, observed.st_ino) == root_identity:
            decision_root.rmdir()
    if target_identity is not None and os.path.lexists(target):
        observed = target.stat(follow_symlinks=False)
        if (observed.st_dev, observed.st_ino) == target_identity:
            target.unlink()
    raise
print(
    f"{target_identity[0]}:{target_identity[1]}",
    f"{root_identity[0]}:{root_identity[1]}",
)
PY
) || abort "analytic-staging"
read -r SCHEDULE_TARGET_ID DECISION_ROOT_ID <<<"$ANALYTIC_STAGING_IDS" \
  || abort "analytic-staging-identity-read"
SCHEDULE_TARGET_OWNED=1
DECISION_ROOT_OWNED=1
if ! [[ "$SCHEDULE_TARGET_ID" =~ ^[0-9]+:[0-9]+$ \
  && "$DECISION_ROOT_ID" =~ ^[0-9]+:[0-9]+$ ]]; then
  abort "analytic-staging-identities"
fi

python3 - "$CANONICAL_LOG" <<'PY' || abort "canonical-log-create"
import sys
from pathlib import Path

path = Path(sys.argv[1])
if path.parent.is_symlink() or path.parent.resolve(strict=True) != path.parent:
    raise SystemExit("canonical log parent is not physical")
if path.exists() or path.is_symlink():
    raise SystemExit("canonical log already exists")
PY
set -o noclobber
if ! exec 9> "$CANONICAL_LOG"; then
  set +o noclobber
  abort "canonical-log-exclusive-open"
fi
set +o noclobber
CANONICAL_LOG_OWNED=1
CANONICAL_LOG_ID=$(stat -Lc '%d:%i' "/proc/$$/fd/9") || abort "canonical-log-fd-identity"
CANONICAL_LOG_PATH_ID=$(stat -Lc '%d:%i' "$CANONICAL_LOG") \
  || abort "canonical-log-path-identity"
if [ "$CANONICAL_LOG_PATH_ID" != "$CANONICAL_LOG_ID" ]; then
  abort "canonical-log-open-race:$CANONICAL_LOG_PATH_ID!=$CANONICAL_LOG_ID"
fi
START_MONOTONIC_NS=$(python3 - <<'PY'
import time

print(time.monotonic_ns())
PY
) || abort "G9-monotonic-clock-at-analytic-arm"
WATCHDOG_TERM_AFTER=$((CEILING_SECONDS - TERMINATION_RESERVE_SECONDS))
if [ "$WATCHDOG_TERM_AFTER" -le 0 ]; then
  abort "G9-watchdog-no-runtime:$WATCHDOG_TERM_AFTER"
fi
WATCHDOG_READY=$CONTAINER_CONTROL_ROOT/watchdog.ready
python3 - "$$" "$WATCHDOG_TERM_AFTER" "$WATCHDOG_READY" <<'PY' &
import ctypes
import json
import os
import signal
import sys
import time
from pathlib import Path

parent_pid = int(sys.argv[1])
term_after = int(sys.argv[2])
ready_path = Path(sys.argv[3])
self_pid = os.getpid()
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(1, signal.SIGTERM) != 0:
    raise SystemExit("watchdog prctl failed")
if os.getppid() != parent_pid:
    raise SystemExit("watchdog parent changed before arming")
if (
    ready_path.parent.parent != Path("/tmp")
    or not ready_path.parent.name.startswith("sentinel-i135-control.")
    or ready_path.name != "watchdog.ready"
    or ready_path.parent.is_symlink()
    or ready_path.parent.resolve(strict=True) != ready_path.parent
):
    raise SystemExit("watchdog ready path contract drift")
ready_payload = {
    "schema": "iter135.deadline_watchdog.v1",
    "pid": self_pid,
    "parent_pid": parent_pid,
    "term_after_seconds": term_after,
    "kill_grace_seconds": 180,
}
ready_fd = os.open(
    ready_path,
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
    0o444,
)
with os.fdopen(ready_fd, "w", encoding="utf-8") as stream:
    json.dump(ready_payload, stream, sort_keys=True)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
parent_fd = os.open(ready_path.parent, os.O_RDONLY | os.O_DIRECTORY)
try:
    os.fsync(parent_fd)
finally:
    os.close(parent_fd)


def process_parent(pid: int) -> int | None:
    try:
        payload = (Path("/proc") / str(pid) / "stat").read_text()
        fields = payload.rsplit(") ", 1)[1].split()
        return int(fields[1])
    except (IndexError, OSError, ValueError):
        return None


def descendants(root_pid: int) -> list[int]:
    parents = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        parent = process_parent(pid)
        if parent is not None:
            parents.setdefault(parent, []).append(pid)
    found = []
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        for child in parents.get(parent, []):
            if child != self_pid and child not in found:
                found.append(child)
                pending.append(child)
    return found


def signal_tree(sig: signal.Signals) -> None:
    for pid in reversed(descendants(parent_pid)):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass
    try:
        os.kill(parent_pid, sig)
    except ProcessLookupError:
        raise SystemExit(0)


deadline = time.monotonic() + term_after
while time.monotonic() < deadline:
    if os.getppid() != parent_pid:
        raise SystemExit(0)
    time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
signal_tree(signal.SIGTERM)
kill_deadline = time.monotonic() + 180
while time.monotonic() < kill_deadline:
    if os.getppid() != parent_pid:
        raise SystemExit(0)
    time.sleep(1.0)
signal_tree(signal.SIGKILL)
PY
ANALYTIC_WATCHDOG_PID=$!
if ! [[ "$ANALYTIC_WATCHDOG_PID" =~ ^[1-9][0-9]*$ ]]; then
  abort "G9-watchdog-pid"
fi
for _WATCHDOG_WAIT in {1..50}; do
  [ -e "$WATCHDOG_READY" ] && break
  compose_process_running "$ANALYTIC_WATCHDOG_PID" \
    || abort "G9-watchdog-exited-before-ready"
  sleep 0.1
done
ANALYTIC_WATCHDOG_READY_ID=$(python3 - "$WATCHDOG_READY" \
  "$ANALYTIC_WATCHDOG_PID" "$$" "$WATCHDOG_TERM_AFTER" <<'PY'
import json
import stat
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected = {
    "schema": "iter135.deadline_watchdog.v1",
    "pid": int(sys.argv[2]),
    "parent_pid": int(sys.argv[3]),
    "term_after_seconds": int(sys.argv[4]),
    "kill_grace_seconds": 180,
}
observed = path.stat(follow_symlinks=False)
if (
    path.is_symlink()
    or not stat.S_ISREG(observed.st_mode)
    or stat.S_IMODE(observed.st_mode) != 0o444
    or path.resolve(strict=True) != path
    or json.loads(path.read_text()) != expected
):
    raise SystemExit("watchdog ready receipt drift")
print(f"{observed.st_dev}:{observed.st_ino}")
PY
) || abort "G9-watchdog-ready-receipt"
if ! [[ "$ANALYTIC_WATCHDOG_READY_ID" =~ ^[0-9]+:[0-9]+$ ]] \
  || ! compose_process_running "$ANALYTIC_WATCHDOG_PID"; then
  abort "G9-watchdog-not-live-after-ready"
fi

verify_deadline_watchdog() {
  compose_process_running "$ANALYTIC_WATCHDOG_PID" || return 1
  python3 - "$WATCHDOG_READY" "$ANALYTIC_WATCHDOG_READY_ID" \
    "$ANALYTIC_WATCHDOG_PID" "$$" "$WATCHDOG_TERM_AFTER" <<'PY'
import json
import stat
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_identity = sys.argv[2]
expected = {
    "schema": "iter135.deadline_watchdog.v1",
    "pid": int(sys.argv[3]),
    "parent_pid": int(sys.argv[4]),
    "term_after_seconds": int(sys.argv[5]),
    "kill_grace_seconds": 180,
}
observed = path.stat(follow_symlinks=False)
if (
    path.is_symlink()
    or not stat.S_ISREG(observed.st_mode)
    or stat.S_IMODE(observed.st_mode) != 0o444
    or path.resolve(strict=True) != path
    or f"{observed.st_dev}:{observed.st_ino}" != expected_identity
    or json.loads(path.read_text()) != expected
):
    raise SystemExit("watchdog live receipt drift")
PY
}
exec 1>&9 2>&1
echo "I135_INVOCATION_START at=$(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ manifest_sha256=$EXPECTED_MANIFEST_SHA"
echo "I135_LIVE_IDLE_OK gpu=NVIDIA_L4 count=1 compute_processes=0 evaluators=0"
echo "I135_PREFLIGHT_OK manifest_sha256=$EXPECTED_MANIFEST_SHA blocks=120 cells=2400 payloads=$PREFLIGHT_PAYLOADS remote=$PREFLIGHT_REMOTE"
echo "I135_RUNTIME_SNAPSHOT_OK manifest_sha256=$EXPECTED_MANIFEST_SHA path=$RUNTIME_SNAPSHOT"
echo "I135_DATASET_SNAPSHOT_OK sha256=$DATASET_RUNTIME_SNAPSHOT_SHA id=$DATASET_RUNTIME_SNAPSHOT_ID files=28"
echo "I135_DOCKER_SNAPSHOT_OK sha256=$DOCKER_RUNTIME_SNAPSHOT_SHA id=$DOCKER_RUNTIME_SNAPSHOT_ID"
echo "I135_EXECUTING_RUNNER_OK sha256=$EXECUTING_RUNNER_SHA id=$EXECUTING_RUNNER_ID bytes=$EXECUTING_RUNNER_BYTES"
echo "I135_ANALYTIC_ARMED lock=$LOCK lock_id=$ANALYTIC_LOCK_ID output_root=$OUTPUT_ROOT"
echo "I135_WATCHDOG_ARMED pid=$ANALYTIC_WATCHDOG_PID term_after_seconds=$WATCHDOG_TERM_AFTER kill_grace_seconds=180"

EXECUTED_BLOCKS=0
EXPECTED_ORDINAL=0
while IFS=$'\t' read -r ORDINAL ARM_ID SCENARIO SEQ; do
  if [ "$ORDINAL" != "$EXPECTED_ORDINAL" ]; then
    abort "execution-block-ordinal:$ORDINAL!=$EXPECTED_ORDINAL"
  fi
  verify_block_plan_row "$ORDINAL" "$ARM_ID" "$SCENARIO" "$SEQ" \
    || abort "execution-block-row-drift:$ORDINAL"
  ELAPSED=$(monotonic_elapsed) || abort "G9-monotonic-clock-before-block:$ORDINAL"
  if [ "$ELAPSED" -ge "$CEILING_SECONDS" ]; then
    abort "G9-ceiling-before-block:$ORDINAL elapsed=$ELAPSED"
  fi
  verify_runtime_snapshot || abort "runtime-snapshot-drift-before-block:$ORDINAL"
  verify_deadline_watchdog || abort "deadline-watchdog-drift-before-block:$ORDINAL"
  verify_output_storage_identity before-block 0 \
    || abort "storage-identity-before-block:$ORDINAL"
  cleanup_containers || abort "owned-container-cleanup-before-block:$ORDINAL"
  if [ "$ORDINAL" != "0" ]; then
    verify_container_quiescence "before-block-$ORDINAL" \
      || abort "container-quiescence-before-block:$ORDINAL"
  fi
  BLOCK_CONTAINER_IDS=$(bounded_docker ps -aq --no-trunc) \
    || abort "container-probe-before-block:$ORDINAL"
  if [ -n "$BLOCK_CONTAINER_IDS" ]; then
    abort "containers-present-before-block:$ORDINAL"
  fi
  verify_current_mission_state >/dev/null \
    || abort "mission-state-revoked-before-block:$ORDINAL"
  if [ "$ANALYTIC_STARTED" = "0" ]; then
    ANALYTIC_STARTED=1
    echo "I135_ANALYTIC_EXECUTION_STARTED ordinal=$ORDINAL"
  fi
  if run_block "$ORDINAL" "$ARM_ID" "$SCENARIO" "$SEQ"; then
    :
  else
    RC=$?
    abort "G7-block-failed ordinal=$ORDINAL arm=$ARM_ID pair=$SCENARIO/$SEQ rc=$RC"
  fi
  verify_output_storage_identity after-block 0 \
    || abort "storage-identity-after-block:$ORDINAL"
  ELAPSED=$(monotonic_elapsed) || abort "G9-monotonic-clock-after-block:$ORDINAL"
  if [ "$ELAPSED" -gt "$CEILING_SECONDS" ]; then
    abort "G9-ceiling-after-block:$ORDINAL elapsed=$ELAPSED"
  fi
  CURRENT_FREE_BYTES=$(python3 - "$OUTPUT_ROOT" <<'PY'
import shutil
import sys

print(shutil.disk_usage(sys.argv[1]).free)
PY
  ) || abort "G8-free-measurement-after-block:$ORDINAL"
  if ! [[ "$CURRENT_FREE_BYTES" =~ ^[0-9]+$ ]] \
    || [ "$CURRENT_FREE_BYTES" -lt $((25 * 1024 * 1024 * 1024)) ]; then
    abort "G8-reserve-after-block:$ORDINAL free=$CURRENT_FREE_BYTES"
  fi
  EXECUTED_BLOCKS=$((EXECUTED_BLOCKS + 1))
  EXPECTED_ORDINAL=$((EXPECTED_ORDINAL + 1))
done <&7
exec 7>&- || abort "execution-block-plan-fd-close"
BLOCK_PLAN_FD_OPEN=0

if [ "$EXECUTED_BLOCKS" != "120" ] || [ "$EXPECTED_ORDINAL" != "120" ]; then
  abort "execution-incomplete blocks=$EXECUTED_BLOCKS next=$EXPECTED_ORDINAL"
fi

cleanup_containers || abort "owned-container-cleanup-before-done"
verify_container_quiescence before-done || abort "container-quiescence-before-done"
verify_deadline_watchdog || abort "deadline-watchdog-drift-before-done"
verify_runtime_snapshot || abort "runtime-snapshot-drift-before-done"
verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$BASELINE_SERVER_SHA" after \
  || abort "runtime-input-drift-before-done"
verify_dataset_runtime_identity before-done \
  || abort "dataset-identity-before-done"
verify_docker_runtime_identity before-done \
  || abort "docker-identity-before-done"
verify_output_storage_identity before-done 0 \
  || abort "storage-identity-before-done"
read -r END_FREE_BYTES OUTPUT_BYTES <<<"$(python3 - "$OUTPUT_ROOT" <<'PY'
import os
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
total = 0
for directory, directories, files in os.walk(root, followlinks=False):
    directory_path = Path(directory)
    for name in [*directories, *files]:
        path = directory_path / name
        if path.is_symlink():
            raise SystemExit(f"symlink in analytic output: {path}")
    for name in files:
        total += (directory_path / name).stat().st_size
print(shutil.disk_usage(root).free, total)
PY
)" || abort "G8-final-storage-measurement"
if ! [[ "$START_FREE_BYTES" =~ ^[0-9]+$ && "$END_FREE_BYTES" =~ ^[0-9]+$ && "$OUTPUT_BYTES" =~ ^[0-9]+$ ]]; then
  abort "G8-final-storage-values"
fi
if [ "$START_FREE_BYTES" -lt $((100 * 1024 * 1024 * 1024)) ]; then
  abort "G8-start-free-below-minimum:$START_FREE_BYTES"
fi
if [ "$END_FREE_BYTES" -lt $((25 * 1024 * 1024 * 1024)) ]; then
  abort "G8-final-reserve-below-minimum:$END_FREE_BYTES"
fi
if [ "$OUTPUT_BYTES" -le 0 ] || [ "$OUTPUT_BYTES" -gt 72380432384 ]; then
  abort "G8-output-size:$OUTPUT_BYTES"
fi
HISTORICAL_I135_OUTPUT=$(python3 - <<'PY'
import os
from pathlib import Path

root = Path("/opt/sentinel-stack/NeuroNCAP/outoutput")
if os.path.lexists(root):
    if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != root:
        raise SystemExit("historical output root is not a physical directory")
    for child in root.iterdir():
        if child.name.startswith("i135-"):
            print(child)
            break
PY
) || abort "G8-historical-root-probe"
if [ -n "$HISTORICAL_I135_OUTPUT" ]; then
  abort "G8-historical-root-contamination"
fi
FINAL_CONTAINER_IDS=$(bounded_docker ps -aq --no-trunc) \
  || abort "container-probe-after-completion"
if [ -n "$FINAL_CONTAINER_IDS" ]; then
  abort "containers-present-after-completion"
fi
FINAL_GPU_COMPUTE_PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader \
  | tr -d '[:space:]') || abort "gpu-process-probe-after-completion"
if [ -n "$FINAL_GPU_COMPUTE_PIDS" ]; then
  abort "gpu-process-present-after-completion"
fi
python3 - <<'PY' || { echo "I135_ABORT evaluator-process-present-after-completion"; exit 1; }
import os
import re
import subprocess

patterns = re.compile(
    r"(CarlaUE4|leaderboard[^ ]*evaluator|neuro[-_]?ncap|UniAD/inference/server\.py|"
    r"neurad[^ ]*(render|viewer))",
    re.IGNORECASE,
)
rows = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines()
for row in rows:
    pid_text, _, command = row.strip().partition(" ")
    try:
        pid = int(pid_text)
    except ValueError:
        continue
    if pid not in {os.getpid(), os.getppid()} and patterns.search(command):
        raise SystemExit(f"live evaluator remains: {pid}:{command}")
PY
python3 - "$LOCK" "$ANALYTIC_LOCK_ID" "$EXPECTED_MANIFEST_SHA" \
  "$DATASET_RUNTIME_SNAPSHOT_SHA" "$DOCKER_RUNTIME_SNAPSHOT_SHA" "$$" <<'PY' \
  || abort "analytic-lock-drift-before-done"
import json
import stat
import sys
from pathlib import Path

lock = Path(sys.argv[1])
expected_identity = sys.argv[2]
expected_manifest = sys.argv[3]
expected_dataset_snapshot = sys.argv[4]
expected_docker_snapshot = sys.argv[5]
expected_pid = int(sys.argv[6])
if (
    lock.is_symlink()
    or not lock.is_file()
    or lock.resolve(strict=True) != lock
    or stat.S_IMODE(lock.stat().st_mode) != 0o444
    or f"{lock.stat().st_dev}:{lock.stat().st_ino}" != expected_identity
):
    raise SystemExit("analytic lock filesystem contract drift")
payload = json.loads(lock.read_text())
if (
    set(payload)
    != {
        "schema",
        "manifest_sha256",
        "dataset_runtime_snapshot_sha256",
        "docker_runtime_snapshot_sha256",
        "pid",
        "created_at_utc",
    }
    or payload.get("schema") != "iter135.analytic_lock.v2"
    or payload.get("manifest_sha256") != expected_manifest
    or payload.get("dataset_runtime_snapshot_sha256") != expected_dataset_snapshot
    or payload.get("docker_runtime_snapshot_sha256") != expected_docker_snapshot
    or payload.get("pid") != expected_pid
    or not isinstance(payload.get("created_at_utc"), str)
    or not payload["created_at_utc"].endswith("Z")
):
    raise SystemExit("analytic lock receipt contract drift")
PY
FINAL_LOG_ID=$(stat -Lc '%d:%i' "$CANONICAL_LOG") || abort "canonical-log-missing-before-done"
if [ "$FINAL_LOG_ID" != "$CANONICAL_LOG_ID" ]; then
  abort "canonical-log-inode-drift-before-done:$FINAL_LOG_ID!=$CANONICAL_LOG_ID"
fi
FINAL_ELAPSED=$(monotonic_elapsed) || abort "G9-monotonic-clock-before-done"
if [ "$FINAL_ELAPSED" -gt "$CEILING_SECONDS" ]; then
  abort "G9-ceiling-before-done:$FINAL_ELAPSED"
fi
echo "I135_DONE_METADATA at=$(date -u +%Y-%m-%dT%H:%M:%SZ) manifest_sha256=$EXPECTED_MANIFEST_SHA runtime_snapshot=$RUNTIME_SNAPSHOT dataset_runtime_snapshot_sha256=$DATASET_RUNTIME_SNAPSHOT_SHA dataset_runtime_snapshot_id=$DATASET_RUNTIME_SNAPSHOT_ID docker_runtime_snapshot_sha256=$DOCKER_RUNTIME_SNAPSHOT_SHA docker_runtime_snapshot_id=$DOCKER_RUNTIME_SNAPSHOT_ID launch_lock_retained=$LOCK launch_lock_id=$ANALYTIC_LOCK_ID elapsed_seconds=$FINAL_ELAPSED prior_smoke_gpu_seconds=$PRIOR_SMOKE_SECONDS blocks=$EXECUTED_BLOCKS episodes=$((EXECUTED_BLOCKS * 20)) output_root=$OUTPUT_ROOT output_device=/dev/nvme0n2 output_uuid=9a98277e-b21f-4ffc-8f14-3f2235b43103 start_free_bytes=$START_FREE_BYTES end_free_bytes=$END_FREE_BYTES output_bytes=$OUTPUT_BYTES"
echo "I135_DOSE_DONE"
