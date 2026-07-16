#!/bin/bash -p
# Iteration 135: six arms x 20 scenario pairs, executed as 120 pair-major 20-run blocks.
# The launcher is inert unless the committed manifest explicitly authorizes launch and every
# provenance, environment, storage, idle, and resource gate passes on the execution host.

# Deployment precondition: invoke this file from a trusted, sanitized `env -i` or
# equivalently locked-down systemd unit. These checks detect inherited contamination;
# they cannot undo native dynamic-loader code that ran before Bash read its first byte.
# Privileged-mode Bash suppresses BASH_ENV processing and imported shell functions.
HOSTILE_LOADER_VARIABLE=
if [[ ${LD_PRELOAD+x} ]]; then
  HOSTILE_LOADER_VARIABLE=LD_PRELOAD
elif [[ ${LD_AUDIT+x} ]]; then
  HOSTILE_LOADER_VARIABLE=LD_AUDIT
elif [[ ${LD_LIBRARY_PATH+x} ]]; then
  HOSTILE_LOADER_VARIABLE=LD_LIBRARY_PATH
elif [[ ${DYLD_INSERT_LIBRARIES+x} ]]; then
  HOSTILE_LOADER_VARIABLE=DYLD_INSERT_LIBRARIES
elif [[ ${DYLD_LIBRARY_PATH+x} ]]; then
  HOSTILE_LOADER_VARIABLE=DYLD_LIBRARY_PATH
fi
if [ -n "$HOSTILE_LOADER_VARIABLE" ]; then
  echo "I135_ABORT hostile-dynamic-loader:$HOSTILE_LOADER_VARIABLE" >&2
  exit 1
fi
CANONICAL_PATH=/usr/bin:/bin:/usr/sbin:/sbin
BOOTSTRAP_ENV_PROBLEM=
BOOTSTRAP_ENV_COUNT=0
while IFS= read -r BOOTSTRAP_NAME; do
  BOOTSTRAP_ENV_COUNT=$((BOOTSTRAP_ENV_COUNT + 1))
  case "$BOOTSTRAP_NAME" in
    PATH|PWD|SHLVL|SENTINEL_LAUNCH_MANIFEST_SHA256|SENTINEL_LAUNCH_ACTIVATION_COMMIT|SENTINEL_LAUNCH_ACTIVATION_SHA256)
      ;;
    *)
      BOOTSTRAP_ENV_PROBLEM=$BOOTSTRAP_NAME
      break
      ;;
  esac
done < <(compgen -e)
if [ -n "$BOOTSTRAP_ENV_PROBLEM" ]; then
  echo "I135_ABORT hostile-bootstrap-environment:$BOOTSTRAP_ENV_PROBLEM" >&2
  exit 1
fi
if [ "$BOOTSTRAP_ENV_COUNT" != "6" ]; then
  echo "I135_ABORT bootstrap-environment-field-set" >&2
  exit 1
fi
if [ "${PATH-}" != "$CANONICAL_PATH" ]; then
  echo "I135_ABORT hostile-bootstrap-path" >&2
  exit 1
fi
if [ "${PWD-}" != "/opt/sentinel-stack/iter135" ] \
  || [ "$(pwd -P)" != "/opt/sentinel-stack/iter135" ]; then
  echo "I135_ABORT hostile-bootstrap-working-directory" >&2
  exit 1
fi
if [ "${SHLVL-}" != "1" ]; then
  echo "I135_ABORT hostile-bootstrap-shell-level" >&2
  exit 1
fi
export PATH=$CANONICAL_PATH LC_ALL=C LANG=C TZ=UTC HOME=/nonexistent \
  DOCKER_CONFIG=/nonexistent DOCKER_HOST=unix:///var/run/docker.sock \
  GIT_CONFIG_NOSYSTEM=1 GIT_OPTIONAL_LOCKS=0 GIT_TERMINAL_PROMPT=0
unset BASH_ENV ENV CDPATH GLOBIGNORE DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH \
  HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY http_proxy https_proxy all_proxy no_proxy \
  SSL_CERT_FILE SSL_CERT_DIR SSLKEYLOGFILE GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS \
  GIT_SSH GIT_SSH_COMMAND LD_PRELOAD LD_AUDIT LD_LIBRARY_PATH \
  DYLD_INSERT_LIBRARIES DYLD_LIBRARY_PATH
IFS=$' \t\n'
umask 077
set -euo pipefail
exec 3>&1 4>&2

STACK=/opt/sentinel-stack
I135=$STACK/iter135
RUNNER_SOURCE=$I135/run_dose135.sh
MANIFEST_SOURCE=$I135/launch_manifest.json
MANIFEST=$MANIFEST_SOURCE
MISSION_STATE_SOURCE=$I135/MISSION_STATE.json
ACTIVATION_SOURCE=$I135/launch_activation_receipt.json
ENV_SOURCE=$I135/env_receipts.json
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
ACTIVATION_FD_OPEN=0
ACTIVATION_BASELINE_SHA=
ACTIVATION_BASELINE_ID=
ACTIVATION_BASELINE_BYTES=
EXPECTED_ACTIVATION_COMMIT=${SENTINEL_LAUNCH_ACTIVATION_COMMIT:-}
EXPECTED_ACTIVATION_SHA=${SENTINEL_LAUNCH_ACTIVATION_SHA256:-}
GITHUB_ACTIVATION_COMMIT=
GITHUB_FINAL_MANIFEST_COMMIT=
GITHUB_CHECK_310_ID=
GITHUB_CHECK_311_ID=
LOCAL_FINAL_MANIFEST_COMMIT=
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
DOCKER_COMMAND=
DOCKER_FD_PATH=
DOCKER_FD_OPEN=0
DOCKER_BIN_ID=
DOCKER_BIN_SHA=
DOCKER_BIN_BYTES=
DOCKER_WRAPPER_SHA=
PYTHON_WRAPPER_SHA=
PYTHON_BIN=
PYTHON_FD_PATH=
PYTHON_FD_OPEN=0
PYTHON_BIN_ID=
PYTHON_BIN_SHA=
PYTHON_BIN_BYTES=
PYTHON_BIN_VERSION=
DOCKER_CONTROL_TIMEOUT_SECONDS=5
CONTAINER_QUIET_SECONDS=5
CONTAINER_QUIESCENCE_CEILING_SECONDS=20

bounded_docker() {
  local BINARY=${DOCKER_FD_PATH:-${DOCKER_BIN:-}}
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
    def identity(row):
        return (
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

def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise SystemExit(f"duplicate mission-state JSON key: {key}")
        value[key] = item
    return value


def reject_nonfinite(value):
    raise SystemExit(f"non-finite mission-state JSON number: {value}")


state = json.loads(
    state_payload,
    object_pairs_hook=strict_object,
    parse_constant=reject_nonfinite,
)
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
expected_claim_state = {
    "neuroncap_union_gain": "ESTABLISHED_ON_NEURONCAP",
    "semantic_attribution": "UNRESOLVED",
    "hugsim_transfer": "TRANSFER_NULL",
    "production_readiness": "NOT_ESTABLISHED",
}
expected_deprecated = [
    "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md"
]
expected_paper_state = {
    "status": "ARCHIVED_NOT_SUBMISSION_READY",
    "next_route": "peer-reviewed venue after a full evidence rewrite",
    "blocking_omissions": [
        "HUGSIM transfer null",
        "iteration-134 placebo result",
        "resolved wording for the decoder universal-negative overclaim",
    ],
}
if (
    state.get("storage_gate") != expected_storage
    or state.get("claim_state") != expected_claim_state
    or state.get("deprecated_pending_hypotheses") != expected_deprecated
    or state.get("paper_state") != expected_paper_state
):
    raise SystemExit("current mission state storage contract drift")
print(state_sha, state_identity, len(state_payload))
PY
}

verify_github_launch_authority() {
  python3 - "$EXPECTED_ACTIVATION_COMMIT" "$EXPECTED_ACTIVATION_SHA" \
    "$ACTIVATION_SOURCE" <<'PY'
# BEGIN I135_GITHUB_LAUNCH_AUTHORITY_PYTHON
import base64
import hashlib
import json
import os
import re
import ssl
import stat
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API_ROOT = "https://api.github.com/repos/manfromnowhere143/sentinel"
ACTIVATION_REPOSITORY_PATH = (
    "experiments/iter135_neuroncap_blind_braking_dose_response/"
    "launch_activation_receipt.json"
)
EXPECTED_CHECKS = {"check (3.10)", "check (3.11)"}
OID = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        raise RuntimeError(f"GitHub API redirect rejected: {code}")


def strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key rejected: {key}")
        document[key] = value
    return document


def reject_nonfinite_json(value: str) -> None:
    raise ValueError(f"non-finite JSON number rejected: {value}")


def strict_json_loads(payload: bytes) -> object:
    return json.loads(
        payload,
        object_pairs_hook=strict_json_object,
        parse_constant=reject_nonfinite_json,
    )


def stable_physical_bytes(path: Path) -> bytes:
    path = path.absolute()
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"deployed activation receipt is not physical: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        chunks = []
        while chunk := os.read(descriptor, 1 << 20):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.stat(follow_symlinks=False)
    def identity(row):
        return (
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
        or identity(after) != identity(final)
        or len(payload) != before.st_size
    ):
        raise SystemExit("deployed activation receipt changed while read")
    return payload


def validate_ref(payload: object, expected_commit: str) -> None:
    if not isinstance(payload, dict):
        raise ValueError("GitHub master ref is not an object")
    target = payload.get("object")
    if (
        payload.get("ref") != "refs/heads/master"
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != expected_commit
    ):
        raise ValueError("activation B is not the current canonical GitHub master")


def validate_ci(payload: object, expected_commit: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("check_runs"), list):
        raise ValueError("GitHub check-runs response is malformed")
    check_runs = payload["check_runs"]
    if (
        type(payload.get("total_count")) is not int
        or payload["total_count"] != len(check_runs)
        or payload["total_count"] != len(EXPECTED_CHECKS)
        or payload["total_count"] > 100
    ):
        raise ValueError("GitHub check-runs page is incomplete or not the exact CI matrix")
    grouped = {name: [] for name in EXPECTED_CHECKS}
    for row in check_runs:
        if not isinstance(row, dict) or row.get("name") not in EXPECTED_CHECKS:
            raise ValueError("GitHub check-runs contains an unexpected matrix row")
        app = row.get("app")
        if (
            row.get("head_sha") != expected_commit
            or not isinstance(app, dict)
            or app.get("slug") != "github-actions"
            or type(row.get("id")) is not int
            or row["id"] <= 0
        ):
            raise ValueError(f"GitHub CI identity drift: {row.get('name')}")
        grouped[row["name"]].append(row)
    projection = []
    for name, rows in grouped.items():
        if len(rows) != 1:
            raise ValueError(f"required GitHub CI check missing: {name}")
        latest = max(rows, key=lambda row: row["id"])
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise ValueError(f"required GitHub CI check is not green: {name}")
        projection.append(
            {
                "name": name,
                "id": latest["id"],
                "head_sha": expected_commit,
                "app_slug": "github-actions",
                "status": "completed",
                "conclusion": "success",
            }
        )
    projection.sort(key=lambda row: row["name"])
    if len({row["id"] for row in projection}) != len(projection):
        raise ValueError("GitHub CI check IDs are not unique")
    return projection


def validate_commit(payload: object, expected_commit: str) -> str:
    if not isinstance(payload, dict) or payload.get("sha") != expected_commit:
        raise ValueError("GitHub activation commit response drift")
    parents = payload.get("parents")
    if (
        not isinstance(parents, list)
        or len(parents) != 1
        or not isinstance(parents[0], dict)
        or OID.fullmatch(parents[0].get("sha", "")) is None
    ):
        raise ValueError("activation B must have exactly one final-manifest parent F")
    files = payload.get("files")
    expected_paths = {
        "CONTINUITY.md",
        "HANDOFF.md",
        ACTIVATION_REPOSITORY_PATH,
    }
    if not isinstance(files, list) or len(files) != len(expected_paths):
        raise ValueError("activation B changed-path scope is not exact")
    observed_paths = []
    for row in files:
        if (
            not isinstance(row, dict)
            or row.get("filename") not in expected_paths
            or row.get("status") not in {"added", "modified"}
            or "previous_filename" in row
        ):
            raise ValueError("activation B changed-path scope is not exact")
        observed_paths.append(row["filename"])
    if len(set(observed_paths)) != len(expected_paths) or set(observed_paths) != expected_paths:
        raise ValueError("activation B changed-path scope is not exact")
    return parents[0]["sha"]


def validate_activation_blob(
    payload: object,
    deployed: bytes,
    expected_sha: str,
    expected_final_manifest: str,
) -> None:
    if (
        not isinstance(payload, dict)
        or payload.get("type") != "file"
        or payload.get("path") != ACTIVATION_REPOSITORY_PATH
        or payload.get("encoding") != "base64"
        or type(payload.get("size")) is not int
        or OID.fullmatch(payload.get("sha", "")) is None
        or not isinstance(payload.get("content"), str)
    ):
        raise ValueError("GitHub activation blob response is malformed")
    encoded = payload["content"].replace("\n", "").replace("\r", "")
    remote = base64.b64decode(encoded, validate=True)
    git_oid = hashlib.sha1(
        f"blob {len(remote)}\0".encode() + remote, usedforsecurity=False
    ).hexdigest()
    if (
        payload["size"] != len(remote)
        or git_oid != payload["sha"]
        or remote != deployed
        or hashlib.sha256(remote).hexdigest() != expected_sha
    ):
        raise ValueError("deployed activation receipt does not equal the GitHub B blob")
    activation = strict_json_loads(remote)
    commits = activation.get("commits") if isinstance(activation, dict) else None
    if (
        not isinstance(commits, dict)
        or commits.get("final_manifest") != expected_final_manifest
        or commits.get("baton_parent") != expected_final_manifest
    ):
        raise ValueError("activation B parent does not equal receipt-bound F")


def github_json(relative: str) -> object:
    if not relative.startswith("/") or ".." in relative:
        raise ValueError("unsafe GitHub API relative path")
    url = API_ROOT + relative
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context), NoRedirect()
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "sentinel-iter135-publication-gate",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    with opener.open(request, timeout=20) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError(f"GitHub API response drift: {response.status}")
        content_type = response.headers.get_content_type()
        if content_type not in {"application/json", "application/vnd.github+json"}:
            raise ValueError(f"GitHub API content type drift: {content_type}")
        raw = response.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("GitHub API response exceeds frozen byte ceiling")
    return strict_json_loads(raw)


def main() -> None:
    expected_commit, expected_sha, activation_text = sys.argv[1:]
    if OID.fullmatch(expected_commit) is None or SHA256.fullmatch(expected_sha) is None:
        raise SystemExit("independent activation commit or SHA-256 is malformed")
    deployed = stable_physical_bytes(Path(activation_text))
    if hashlib.sha256(deployed).hexdigest() != expected_sha:
        raise SystemExit("independent activation receipt SHA-256 drift")
    validate_ref(github_json("/git/ref/heads/master"), expected_commit)
    ci_projection = validate_ci(
        github_json(
            f"/commits/{expected_commit}/check-runs?filter=latest&per_page=100&page=1"
        ),
        expected_commit,
    )
    final_manifest = validate_commit(
        github_json(f"/commits/{expected_commit}?per_page=100&page=1"), expected_commit
    )
    quoted_path = urllib.parse.quote(ACTIVATION_REPOSITORY_PATH, safe="/")
    validate_activation_blob(
        github_json(f"/contents/{quoted_path}?ref={expected_commit}"),
        deployed,
        expected_sha,
        final_manifest,
    )
    validate_ref(github_json("/git/ref/heads/master"), expected_commit)
    print(
        expected_commit,
        final_manifest,
        *(str(row["id"]) for row in ci_projection),
    )


if __name__ == "__main__":
    main()
# END I135_GITHUB_LAUNCH_AUTHORITY_PYTHON
PY
}

verify_launch_activation() {
  python3 - "$ACTIVATION_SOURCE" "$MISSION_STATE_SOURCE" "$MANIFEST_SOURCE" \
    "$I135" "$EXPECTED_ACTIVATION_COMMIT" "$EXPECTED_ACTIVATION_SHA" \
    "/proc/$$/fd/5" "$ACTIVATION_BASELINE_ID" \
    "$ACTIVATION_BASELINE_SHA" "$EXPECTED_MANIFEST_SHA" <<'PY'
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

(
    activation_text,
    state_text,
    manifest_text,
    experiment_text,
    expected_activation_commit,
    expected_activation_sha,
    pinned_descriptor_path,
    expected_activation_identity,
    expected_activation_baseline_sha,
    expected_manifest_sha,
) = sys.argv[1:]
activation_path = Path(activation_text).absolute()
state_path = Path(state_text).absolute()
manifest_path = Path(manifest_text).absolute()
experiment = Path(experiment_text).absolute()
oid = re.compile(r"^[0-9a-f]{40}$")
sha = re.compile(r"^[0-9a-f]{64}$")


# BEGIN I135_TOOLING_PUBLICATION_CONTRACT_PYTHON
EXPECTED_TOOLING_PUBLICATION = {
    "generation": 4,
    "supersedes_receipt_commit": "755489f36ae2b8cefad183341edefd7c30c047e7",
    "recovery_parent": "30b6390b3e165fc517ec6a7d1d7a26502ea45e2a",
    "reason_code": "B3_CI_STRUCTURAL_GIT_READER_TOOLCHAIN_ROOT_FAILURE",
}


def tooling_receipt_is_exact(tooling: object) -> bool:
    if not isinstance(tooling, dict):
        return False
    tooling_source = tooling.get("repository", {}).get("git_start", {}).get("head")
    return (
        tooling.get("schema") == "iter135.tooling_verification.v2"
        and tooling.get("verdict") == "I135_TOOLING_VERIFICATION_OK"
        and tooling.get("publication") == EXPECTED_TOOLING_PUBLICATION
        and isinstance(tooling_source, str)
        and oid.fullmatch(tooling_source) is not None
    )


# END I135_TOOLING_PUBLICATION_CONTRACT_PYTHON


def stable_physical(path: Path, label: str) -> tuple[bytes, os.stat_result]:
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
    final = path.stat(follow_symlinks=False)
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
        or identity(after) != identity(final)
        or len(payload) != before.st_size
    ):
        raise SystemExit(f"{label} changed while read")
    return payload, before


def stable_pinned(path: str) -> tuple[bytes, os.stat_result]:
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
    identity = lambda row: (
        row.st_dev,
        row.st_ino,
        row.st_size,
        row.st_mtime_ns,
        row.st_ctime_ns,
        stat.S_IMODE(row.st_mode),
    )
    if not stat.S_ISREG(before.st_mode) or identity(before) != identity(after):
        raise SystemExit("pinned activation receipt changed while read")
    return payload, before


def binding(path: str, payload: bytes) -> dict[str, object]:
    return {
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


if (
    oid.fullmatch(expected_activation_commit) is None
    or sha.fullmatch(expected_activation_sha) is None
):
    raise SystemExit("independently supplied activation authority is malformed")
activation_payload, activation_row = stable_physical(activation_path, "activation receipt")
pinned_payload, pinned_row = stable_pinned(pinned_descriptor_path)
identity = lambda row: (
    row.st_dev,
    row.st_ino,
    row.st_size,
    row.st_mtime_ns,
    row.st_ctime_ns,
    stat.S_IMODE(row.st_mode),
)
if identity(activation_row) != identity(pinned_row) or activation_payload != pinned_payload:
    raise SystemExit("activation receipt no longer matches its pinned authority")
activation_identity = ":".join(str(value) for value in identity(activation_row))
activation_sha = hashlib.sha256(activation_payload).hexdigest()
if activation_sha != expected_activation_sha:
    raise SystemExit("activation receipt differs from independently supplied SHA-256")
if expected_activation_identity and activation_identity != expected_activation_identity:
    raise SystemExit("activation receipt identity drift")
if expected_activation_baseline_sha and activation_sha != expected_activation_baseline_sha:
    raise SystemExit("activation receipt hash drift")

activation = json.loads(activation_payload)
if set(activation) != {
    "schema",
    "verdict",
    "problem_count",
    "problems",
    "phase",
    "commits",
    "artifacts",
    "receipt_payload_sha256",
}:
    raise SystemExit("activation receipt field set drift")
canonical = dict(activation)
claimed_payload_sha = canonical.pop("receipt_payload_sha256", None)
actual_payload_sha = hashlib.sha256(
    json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
).hexdigest()
if (
    activation.get("schema") != "iter135.launch_activation.v1"
    or activation.get("verdict") != "I135_LAUNCH_ACTIVATION_OK"
    or activation.get("problem_count") != 0
    or activation.get("problems") != []
    or activation.get("phase") != "LAUNCH_AUTHORIZED"
    or claimed_payload_sha != actual_payload_sha
):
    raise SystemExit("activation receipt is not exactly green")

commits = activation.get("commits")
expected_commit_fields = {
    "tooling_receipt",
    "host_preparation",
    "environment",
    "pre_smoke_manifest",
    "smoke",
    "state",
    "final_manifest",
    "baton_parent",
}
if (
    not isinstance(commits, dict)
    or set(commits) != expected_commit_fields
    or any(oid.fullmatch(value) is None for value in commits.values())
    or commits.get("baton_parent") != commits.get("final_manifest")
    or len(set(commits.values())) != 7
    or expected_activation_commit in commits.values()
):
    raise SystemExit("activation commit topology drift")

relative_root = "experiments/iter135_neuroncap_blind_braking_dose_response"
physical = {
    "mission_state": ("MISSION_STATE.json", state_path),
    "host_preparation": (
        f"{relative_root}/host_preparation_receipt.json",
        experiment / "host_preparation_receipt.json",
    ),
    "host_packet_manifest": (
        f"{relative_root}/host_packet_manifest.json",
        experiment / "host_packet_manifest.json",
    ),
    "environment": (f"{relative_root}/env_receipts.json", experiment / "env_receipts.json"),
    "pre_smoke_manifest": (
        f"{relative_root}/launch_manifest.json",
        experiment / "smoke-evidence/raw/pre_smoke_manifest.json",
    ),
    "smoke_receipt": (
        f"{relative_root}/smoke-evidence/smoke_receipt.json",
        experiment / "smoke-evidence/smoke_receipt.json",
    ),
    "final_manifest": (f"{relative_root}/launch_manifest.json", manifest_path),
}
artifacts = activation.get("artifacts")
if not isinstance(artifacts, dict) or set(artifacts) != set(physical):
    raise SystemExit("activation artifact set drift")
payloads = {}
for role, (repository_path, local_path) in physical.items():
    payload, _row = stable_physical(local_path, f"activation artifact {role}")
    payloads[role] = payload
    if artifacts.get(role) != binding(repository_path, payload):
        raise SystemExit(f"activation artifact binding drift: {role}")

manifest_payload = payloads["final_manifest"]
if hashlib.sha256(manifest_payload).hexdigest() != expected_manifest_sha:
    raise SystemExit("activation final manifest SHA-256 drift")
manifest = json.loads(manifest_payload)
state_payload = payloads["mission_state"]
if manifest.get("git_provenance", {}).get("head") != commits.get("state"):
    raise SystemExit("final manifest does not bind the exact state commit")
if manifest.get("mission_state") != {
    "source_path": "MISSION_STATE.json",
    "sha256": hashlib.sha256(state_payload).hexdigest(),
    "bytes": len(state_payload),
}:
    raise SystemExit("final manifest mission state binding drift")
bound = manifest.get("hash_bound_files")
expected_bound_payloads = {
    "host_packet_manifest.json": payloads["host_packet_manifest"],
    "host_preparation_receipt.json": payloads["host_preparation"],
    "env_receipts.json": payloads["environment"],
    "smoke-evidence/smoke_receipt.json": payloads["smoke_receipt"],
}
if not isinstance(bound, dict):
    raise SystemExit("final manifest hash-bound set missing")
for name, payload in expected_bound_payloads.items():
    expected = {
        "source_path": f"{relative_root}/{name}",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    if bound.get(name) != expected:
        raise SystemExit(f"final manifest artifact link drift: {name}")
if (
    manifest.get("host_packet_manifest") != bound.get("host_packet_manifest.json")
    or manifest.get("host_preparation_receipt") != bound.get("host_preparation_receipt.json")
    or manifest.get("smoke_receipt") != bound.get("smoke-evidence/smoke_receipt.json")
):
    raise SystemExit("final manifest evidence pointer drift")

host_packet = json.loads(payloads["host_packet_manifest"])
host_preparation = json.loads(payloads["host_preparation"])
environment = json.loads(payloads["environment"])
smoke = json.loads(payloads["smoke_receipt"])
tooling_payload, _row = stable_physical(
    experiment / "tooling_verification_receipt.json", "tooling verification receipt"
)
tooling = json.loads(tooling_payload)
if (
    host_packet.get("schema") != "iter135.host_packet_manifest.v1"
    or oid.fullmatch(host_packet.get("source_commit", "")) is None
    or host_preparation.get("schema") != "iter135.host_preparation_receipt.v1"
    or host_preparation.get("verdict") != "I135_HOST_PREPARATION_OK"
    or host_preparation.get("packet_manifest_sha256")
    != hashlib.sha256(payloads["host_packet_manifest"]).hexdigest()
    or environment.get("schema") != "iter135.environment_receipts.v3"
    or environment.get("verdict") != "I135_ENVIRONMENT_PREFLIGHT_OK"
    or smoke.get("schema") != "iter135.smoke_receipt.v1"
    or smoke.get("verdict") != "I135_LIVE_SMOKE_OK"
    or smoke.get("nonanalytic") is not True
    or smoke.get("analytic_episode_count") != 0
    or not tooling_receipt_is_exact(tooling)
    or oid.fullmatch(commits.get("tooling_receipt", "")) is None
):
    raise SystemExit("activation source, tooling, host, environment, or smoke contract drift")

print(
    activation_sha,
    activation_identity,
    len(activation_payload),
    commits["final_manifest"],
)
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
  if [ "$ACTIVATION_FD_OPEN" = "1" ]; then
    exec 5>&- || true
    ACTIVATION_FD_OPEN=0
  fi
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
  if [ "$PYTHON_FD_OPEN" = "1" ]; then
    exec 10>&- || true
    PYTHON_FD_OPEN=0
  fi
  if [ "$DOCKER_FD_OPEN" = "1" ]; then
    exec 11>&- || true
    DOCKER_FD_OPEN=0
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
if ! [[ $EXPECTED_ACTIVATION_COMMIT =~ ^[0-9a-f]{40}$ \
  && $EXPECTED_ACTIVATION_SHA =~ ^[0-9a-f]{64}$ ]]; then
  echo "I135_ABORT independent-activation-commit-or-sha256-missing-or-malformed" >&2
  exit 1
fi
for AUTHORITY_PATH in "$ENV_SOURCE" "$ACTIVATION_SOURCE" "$MISSION_STATE_SOURCE" \
  "$MANIFEST_SOURCE"; do
  if [ -L "$AUTHORITY_PATH" ] || [ ! -f "$AUTHORITY_PATH" ]; then
    echo "I135_ABORT authority-input-not-physical:$AUTHORITY_PATH" >&2
    exit 1
  fi
done

# Freeze the exact physical CPython interpreter captured in the v3 host receipt.  Every later
# Python call goes through this immutable path with isolated mode enabled.
PYTHON_COMMAND=$(command -v python3) || {
  echo "I135_ABORT python-command-resolution" >&2
  exit 1
}
PYTHON_BIN=$(readlink -f "$PYTHON_COMMAND") || {
  echo "I135_ABORT python-physical-path" >&2
  exit 1
}
if [ ! -f "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ] || [ -L "$PYTHON_BIN" ]; then
  echo "I135_ABORT python-physical-binary:$PYTHON_BIN" >&2
  exit 1
fi
if ! exec 10< "$PYTHON_BIN"; then
  echo "I135_ABORT python-pinned-fd-open:$PYTHON_BIN" >&2
  exit 1
fi
PYTHON_FD_OPEN=1
PYTHON_FD_PATH=/proc/$$/fd/10
if [ ! -e "$PYTHON_FD_PATH" ]; then
  echo "I135_ABORT python-pinned-fd-missing" >&2
  exit 1
fi
PYTHON_BIN_ID=$(stat -Lc '%d:%i' "$PYTHON_FD_PATH") || {
  echo "I135_ABORT python-physical-identity" >&2
  exit 1
}
if [ "$(stat -Lc '%d:%i' "$PYTHON_BIN")" != "$PYTHON_BIN_ID" ]; then
  echo "I135_ABORT python-path-raced-before-pin" >&2
  exit 1
fi
PYTHON_BIN_SHA=$(sha256sum "$PYTHON_FD_PATH" | awk '{print $1}') || {
  echo "I135_ABORT python-physical-sha256" >&2
  exit 1
}
PYTHON_BIN_BYTES=$(stat -Lc '%s' "$PYTHON_FD_PATH") || {
  echo "I135_ABORT python-physical-bytes" >&2
  exit 1
}
PYTHON_BIN_VERSION=$("$PYTHON_FD_PATH" -I -c \
  'import platform; print(platform.python_version())') || {
  echo "I135_ABORT python-physical-version" >&2
  exit 1
}
"$PYTHON_FD_PATH" -I - "$ENV_SOURCE" "$PYTHON_BIN" "$PYTHON_BIN_SHA" \
  "$PYTHON_BIN_BYTES" "$PYTHON_BIN_VERSION" <<'PY' || {
import json
import platform
import sys
from pathlib import Path

environment = json.loads(Path(sys.argv[1]).read_bytes())
physical_path, sha256, byte_count, version = sys.argv[2:]
interpreter = environment.get("interpreter")
invocation = environment.get("invocation")
if environment.get("schema") != "iter135.environment_receipts.v3":
    raise SystemExit("environment schema does not bind the generation-three interpreter")
if not isinstance(interpreter, dict) or set(interpreter) != {
    "invocation_path",
    "physical_path",
    "realpath",
    "sha256",
    "bytes",
    "version",
    "implementation",
}:
    raise SystemExit("environment interpreter receipt is malformed")
if (
    interpreter.get("invocation_path") != physical_path
    or interpreter.get("physical_path") != physical_path
    or interpreter.get("realpath") != physical_path
    or interpreter.get("sha256") != sha256
    or interpreter.get("bytes") != int(byte_count)
    or interpreter.get("version") != version
    or interpreter.get("version") != platform.python_version()
    or interpreter.get("implementation") != "CPython"
    or platform.python_implementation() != "CPython"
):
    raise SystemExit("captured physical interpreter drift")
if (
    not isinstance(invocation, dict)
    or invocation.get("sanitized") is not True
    or invocation.get("isolated") is not True
    or not isinstance(invocation.get("argv"), list)
    or len(invocation["argv"]) < 3
    or invocation["argv"][:3]
    != [physical_path, "-I", "/opt/sentinel-stack/iter135/capture_environment135.py"]
):
    raise SystemExit("captured isolated invocation drift")
PY
  echo "I135_ABORT python-environment-binding" >&2
  exit 1
}
readonly PYTHON_BIN PYTHON_FD_PATH PYTHON_BIN_ID PYTHON_BIN_SHA PYTHON_BIN_BYTES \
  PYTHON_BIN_VERSION
python3() {
  "$PYTHON_FD_PATH" -I "$@"
}
verify_python_interpreter_binding() {
  [ -e "$PYTHON_FD_PATH" ] \
    && [ "$(stat -Lc '%d:%i' "$PYTHON_FD_PATH")" = "$PYTHON_BIN_ID" ] \
    && [ "$(stat -Lc '%s' "$PYTHON_FD_PATH")" = "$PYTHON_BIN_BYTES" ] \
    && [ "$(sha256sum "$PYTHON_FD_PATH" | awk '{print $1}')" = "$PYTHON_BIN_SHA" ] \
    && [ -f "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ] && [ ! -L "$PYTHON_BIN" ] \
    && [ "$(readlink -f "$PYTHON_BIN")" = "$PYTHON_BIN" ] \
    && [ "$(stat -Lc '%d:%i' "$PYTHON_BIN")" = "$PYTHON_BIN_ID" ] \
    && [ "$(stat -Lc '%s' "$PYTHON_BIN")" = "$PYTHON_BIN_BYTES" ] \
    && [ "$(sha256sum "$PYTHON_BIN" | awk '{print $1}')" = "$PYTHON_BIN_SHA" ] \
    && [ "$("$PYTHON_FD_PATH" -I -c 'import platform; print(platform.python_version())')" \
      = "$PYTHON_BIN_VERSION" ]
}
verify_python_interpreter_binding || {
  echo "I135_ABORT python-interpreter-initial-drift" >&2
  exit 1
}
DOCKER_COMMAND=$(command -v docker) || {
  echo "I135_ABORT docker-command-resolution" >&2
  exit 1
}
DOCKER_BIN=$(readlink -f "$DOCKER_COMMAND") || {
  echo "I135_ABORT docker-binary-realpath" >&2
  exit 1
}
if [ ! -f "$DOCKER_BIN" ] || [ ! -x "$DOCKER_BIN" ] || [ -L "$DOCKER_BIN" ]; then
  echo "I135_ABORT docker-binary-physical:$DOCKER_BIN" >&2
  exit 1
fi
if ! exec 11< "$DOCKER_BIN"; then
  echo "I135_ABORT docker-pinned-fd-open:$DOCKER_BIN" >&2
  exit 1
fi
DOCKER_FD_OPEN=1
DOCKER_FD_PATH=/proc/$$/fd/11
DOCKER_BIN_ID=$(stat -Lc '%d:%i' "$DOCKER_FD_PATH") || {
  echo "I135_ABORT docker-binary-identity" >&2
  exit 1
}
if [ "$(stat -Lc '%d:%i' "$DOCKER_BIN")" != "$DOCKER_BIN_ID" ]; then
  echo "I135_ABORT docker-path-raced-before-pin" >&2
  exit 1
fi
DOCKER_BIN_SHA=$(sha256sum "$DOCKER_FD_PATH" | awk '{print $1}') || {
  echo "I135_ABORT docker-binary-sha256" >&2
  exit 1
}
DOCKER_BIN_BYTES=$(stat -Lc '%s' "$DOCKER_FD_PATH") || {
  echo "I135_ABORT docker-binary-bytes" >&2
  exit 1
}
readonly DOCKER_COMMAND DOCKER_BIN DOCKER_FD_PATH DOCKER_BIN_ID DOCKER_BIN_SHA \
  DOCKER_BIN_BYTES
verify_docker_client_binding() {
  [ -e "$DOCKER_FD_PATH" ] \
    && [ "$(stat -Lc '%d:%i' "$DOCKER_FD_PATH")" = "$DOCKER_BIN_ID" ] \
    && [ "$(stat -Lc '%s' "$DOCKER_FD_PATH")" = "$DOCKER_BIN_BYTES" ] \
    && [ "$(sha256sum "$DOCKER_FD_PATH" | awk '{print $1}')" = "$DOCKER_BIN_SHA" ] \
    && [ -f "$DOCKER_BIN" ] && [ -x "$DOCKER_BIN" ] && [ ! -L "$DOCKER_BIN" ] \
    && [ "$(readlink -f "$DOCKER_BIN")" = "$DOCKER_BIN" ] \
    && [ "$(stat -Lc '%d:%i' "$DOCKER_BIN")" = "$DOCKER_BIN_ID" ] \
    && [ "$(stat -Lc '%s' "$DOCKER_BIN")" = "$DOCKER_BIN_BYTES" ] \
    && [ "$(sha256sum "$DOCKER_BIN" | awk '{print $1}')" = "$DOCKER_BIN_SHA" ]
}
verify_docker_client_binding || {
  echo "I135_ABORT docker-client-initial-drift" >&2
  exit 1
}
verify_docker_v3_runtime() {
  python3 - "$ENV_SOURCE" "$DOCKER_COMMAND" "$DOCKER_BIN" "$DOCKER_FD_PATH" \
    "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" "$DOCKER_BIN_BYTES" <<'PY'
# BEGIN I135_DOCKER_RUNTIME_PYTHON
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

env_text, invocation_text, physical_text, executable_text, expected_id, expected_sha, size_text = (
    sys.argv[1:]
)
invocation = Path(invocation_text).absolute()
physical = Path(physical_text).absolute()
executable = Path(executable_text)
expected_size = int(size_text)
receipt = json.loads(Path(env_text).read_bytes()).get("docker_runtime")


def stable_digest(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(descriptor, 1 << 20):
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    def identity(row):
        return (
            row.st_dev,
            row.st_ino,
            row.st_size,
            row.st_mtime_ns,
            row.st_ctime_ns,
            stat.S_IMODE(row.st_mode),
        )
    if identity(before) != identity(after) or size != before.st_size:
        raise SystemExit("Docker client changed while read")
    return digest.hexdigest(), size, before, identity(before)


if (
    not invocation.is_file()
    or invocation.resolve(strict=True) != physical
    or physical.is_symlink()
    or not physical.is_file()
    or physical.resolve(strict=True) != physical
    or not executable.exists()
):
    raise SystemExit("Docker client physical path drift")
fd_sha, fd_size, fd_row, fd_identity = stable_digest(executable)
path_sha, path_size, path_row, path_identity = stable_digest(physical)
if (
    f"{fd_row.st_dev}:{fd_row.st_ino}" != expected_id
    or fd_identity != path_identity
    or fd_sha != path_sha
    or fd_sha != expected_sha
    or fd_size != path_size
    or fd_size != expected_size
):
    raise SystemExit("Docker client pinned FD or pathname drift")
runtime_descriptor = os.open(executable, os.O_RDONLY | os.O_CLOEXEC)
runtime_executable = f"/proc/self/fd/{runtime_descriptor}"

docker_env = {
    "DOCKER_CONFIG": "/nonexistent",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "TZ": "UTC",
}


def run(*args):
    value = subprocess.run(
        [runtime_executable, *args],
        check=True,
        capture_output=True,
        env=docker_env,
        timeout=20,
        pass_fds=(runtime_descriptor,),
    )
    if len(value.stdout) > 4 * 1024 * 1024 or len(value.stderr) > 64 * 1024:
        raise SystemExit("Docker probe byte ceiling")
    return value.stdout


def document(*args):
    value = json.loads(run(*args))
    if not isinstance(value, dict):
        raise SystemExit("Docker probe object schema")
    return value


def bounded(value, label, maximum=512):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SystemExit(f"Docker text field drift:{label}")
    return value


def project(source, fields, prefix):
    if not isinstance(source, dict):
        raise SystemExit(f"Docker projection source drift:{prefix}")
    return {
        target: bounded(source.get(origin), f"{prefix}:{target}")
        for target, origin in fields.items()
    }


version = document("version", "--format", "{{json .}}")
info = document("info", "--format", "{{json .}}")
client_raw = version.get("Client")
server_raw = version.get("Server")
platform_raw = server_raw.get("Platform") if isinstance(server_raw, dict) else None
client_version = project(
    client_raw,
    {
        "version": "Version",
        "api_version": "ApiVersion",
        "git_commit": "GitCommit",
        "go_version": "GoVersion",
        "os": "Os",
        "arch": "Arch",
        "build_time": "BuildTime",
        "context": "Context",
    },
    "client",
)
daemon_version = project(
    server_raw,
    {
        "version": "Version",
        "api_version": "ApiVersion",
        "min_api_version": "MinAPIVersion",
        "git_commit": "GitCommit",
        "go_version": "GoVersion",
        "os": "Os",
        "arch": "Arch",
        "build_time": "BuildTime",
    },
    "daemon",
)
daemon_version["platform_name"] = bounded(
    platform_raw.get("Name") if isinstance(platform_raw, dict) else None,
    "daemon:platform_name",
)
experimental = server_raw.get("Experimental") if isinstance(server_raw, dict) else None
if type(experimental) is not bool:
    raise SystemExit("Docker daemon experimental field drift")
daemon_version["experimental"] = experimental
daemon_info = project(
    info,
    {
        "id": "ID",
        "name": "Name",
        "server_version": "ServerVersion",
        "docker_root_dir": "DockerRootDir",
        "driver": "Driver",
        "operating_system": "OperatingSystem",
        "os_type": "OSType",
        "architecture": "Architecture",
        "kernel_version": "KernelVersion",
        "cgroup_driver": "CgroupDriver",
        "cgroup_version": "CgroupVersion",
    },
    "info",
)
for target, origin, maximum in (
    ("ncpu", "NCPU", 1_000_000),
    ("mem_total", "MemTotal", 2**63 - 1),
):
    value = info.get(origin)
    if type(value) is not int or not (0 < value <= maximum):
        raise SystemExit(f"Docker integer field drift:{target}")
    daemon_info[target] = value
context_name = bounded(run("context", "show").decode().strip(), "context:name")
endpoint = bounded(
    json.loads(
        run(
            "context",
            "inspect",
            "--format",
            "{{json .Endpoints.docker.Host}}",
            context_name,
        )
    ),
    "context:endpoint",
    maximum=1024,
)
live = {
    "schema": "iter135.docker_runtime_receipt.v1",
    "client": {
        "invocation_path": str(invocation),
        "physical_path": str(physical),
        "realpath": str(physical),
        "sha256": fd_sha,
        "bytes": fd_size,
        "version": client_version,
    },
    "context": {"name": context_name, "endpoint": endpoint},
    "daemon": {"info": daemon_info, "version": daemon_version},
}
architecture_family = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}
if (
    context_name != "default"
    or endpoint != "unix:///var/run/docker.sock"
    or client_version["context"] != context_name
    or daemon_info["server_version"] != daemon_version["version"]
    or daemon_info["os_type"] != daemon_version["os"]
    or architecture_family.get(daemon_info["architecture"], daemon_info["architecture"])
    != architecture_family.get(daemon_version["arch"], daemon_version["arch"])
    or not Path(daemon_info["docker_root_dir"]).is_absolute()
    or receipt != live
):
    raise SystemExit("live Docker client/context/daemon drift from v3 receipt")
print(hashlib.sha256(json.dumps(live, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
# END I135_DOCKER_RUNTIME_PYTHON
PY
}
DOCKER_RUNTIME_RECEIPT_SHA=$(verify_docker_v3_runtime) || {
  echo "I135_ABORT docker-v3-runtime-binding" >&2
  exit 1
}
if ! [[ $DOCKER_RUNTIME_RECEIPT_SHA =~ ^[0-9a-f]{64}$ ]]; then
  echo "I135_ABORT docker-v3-runtime-binding-output" >&2
  exit 1
fi
readonly DOCKER_RUNTIME_RECEIPT_SHA
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
if ! exec 5< "$ACTIVATION_SOURCE"; then
  abort "launch-activation-pinned-open:$ACTIVATION_SOURCE"
fi
ACTIVATION_FD_OPEN=1
# The pinned activation receipt is sufficient for reversible preflight.  The public
# GitHub authority is intentionally sampled exactly once, at the final analytic arm,
# so a later network transient cannot invalidate an already-started 120-block run.
ACTIVATION_BINDING=$(verify_launch_activation) \
  || abort "launch-activation-authority"
read -r ACTIVATION_BASELINE_SHA ACTIVATION_BASELINE_ID \
  ACTIVATION_BASELINE_BYTES LOCAL_FINAL_MANIFEST_COMMIT <<<"$ACTIVATION_BINDING"
if ! [[ "$ACTIVATION_BASELINE_SHA" =~ ^[0-9a-f]{64}$ \
  && "$ACTIVATION_BASELINE_ID" =~ ^([0-9]+:){5}[0-9]+$ \
  && "$ACTIVATION_BASELINE_BYTES" =~ ^[1-9][0-9]*$ \
  && "$LOCAL_FINAL_MANIFEST_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  abort "launch-activation-binding-output:$ACTIVATION_BINDING"
fi

echo "I135_PREFLIGHT_INVOCATION at=$(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ manifest_sha256=${EXPECTED_MANIFEST_SHA:-missing}"
echo "I135_EXECUTING_RUNNER_OK sha256=$EXECUTING_RUNNER_SHA id=$EXECUTING_RUNNER_ID bytes=$EXECUTING_RUNNER_BYTES"
echo "I135_MISSION_STATE_OK sha256=$MISSION_STATE_BASELINE_SHA id=$MISSION_STATE_BASELINE_ID bytes=$MISSION_STATE_BASELINE_BYTES"
echo "I135_LAUNCH_ACTIVATION_OK commit=$EXPECTED_ACTIVATION_COMMIT sha256=$ACTIVATION_BASELINE_SHA id=$ACTIVATION_BASELINE_ID bytes=$ACTIVATION_BASELINE_BYTES"

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
  "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" "$DOCKER_FD_PATH" <<'PY' \
  || abort "preflight"
import hashlib
import json
import os
import platform
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
docker_executable = sys.argv[7]
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
    "host_packet_manifest",
    "host_preparation_receipt",
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
        "authorize_launch135.py",
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
        "prepare_host135.py",
        "verify_tooling135.py",
        "tooling_verification_receipt.json",
        "patch_compose_dose_env.py",
        "make_launch_manifest.py",
        "env_receipts.json",
        "host_packet_manifest.json",
        "host_preparation_receipt.json",
        "smoke-evidence/SMOKE.md",
        "smoke-evidence/smoke_receipt.json",
    }
    smoke_raw_names = {
        "smoke-evidence/raw/execution.jsonl",
        "smoke-evidence/raw/pre_smoke_manifest.json",
        "smoke-evidence/raw/pre_smoke_mission_state.json",
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
            or source_path
            != f"experiments/iter135_neuroncap_blind_braking_dose_response/{name}"
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
    if manifest.get("host_packet_manifest") != hash_bound.get(
        "host_packet_manifest.json"
    ):
        problems.append("host-packet-manifest:hash-binding-drift")
    if manifest.get("host_preparation_receipt") != hash_bound.get(
        "host_preparation_receipt.json"
    ):
        problems.append("host-preparation-receipt:hash-binding-drift")
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
        "interpreter",
        "invocation",
        "host_preparation",
        "host_publication_authority",
        "docker_runtime",
        "runtime_snapshots",
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
    if environment.get("schema") != "iter135.environment_receipts.v3":
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

    interpreter = environment.get("interpreter")
    live_interpreter = Path(sys.executable).resolve(strict=True)
    if (
        not isinstance(interpreter, dict)
        or set(interpreter)
        != {
            "invocation_path",
            "physical_path",
            "realpath",
            "sha256",
            "bytes",
            "version",
            "implementation",
        }
        or interpreter.get("physical_path") != str(live_interpreter)
        or interpreter.get("realpath") != str(live_interpreter)
        or interpreter.get("sha256")
        != hashlib.sha256(live_interpreter.read_bytes()).hexdigest()
        or interpreter.get("bytes") != live_interpreter.stat().st_size
        or interpreter.get("version") != platform.python_version()
        or interpreter.get("implementation") != platform.python_implementation()
        or sys.flags.isolated != 1
    ):
        problems.append("environment-interpreter:contract-drift")
    invocation = environment.get("invocation")
    expected_capture_environment = {
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
        "SENTINEL_I135_CAPTURE_SANITIZED": "1",
        "TZ": "UTC",
    }
    if (
        not isinstance(invocation, dict)
        or set(invocation)
        != {"sanitized", "isolated", "environment", "argv", "canonical_script"}
        or invocation.get("sanitized") is not True
        or invocation.get("isolated") is not True
        or invocation.get("environment") != expected_capture_environment
        or invocation.get("canonical_script")
        != "/opt/sentinel-stack/iter135/capture_environment135.py"
        or not isinstance(invocation.get("argv"), list)
        or len(invocation["argv"]) < 3
        or invocation["argv"][:3]
        != [
            str(live_interpreter),
            "-I",
            "/opt/sentinel-stack/iter135/capture_environment135.py",
        ]
    ):
        problems.append("environment-invocation:contract-drift")
    preparation_link = environment.get("host_preparation")
    preparation_path = payload_root / "host_preparation_receipt.json"
    try:
        preparation_payload = preparation_path.read_bytes()
        preparation_evidence = json.loads(preparation_payload)
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"environment-host-preparation:read:{type(error).__name__}")
        preparation_payload = b""
        preparation_evidence = None
    expected_preparation_file = {
        "path": "/opt/sentinel-stack/iter135/host_preparation_receipt.json",
        "sha256": hashlib.sha256(preparation_payload).hexdigest(),
        "bytes": len(preparation_payload),
    }
    if (
        not isinstance(preparation_link, dict)
        or set(preparation_link) != {"receipt_file", "evidence"}
        or preparation_link.get("receipt_file") != expected_preparation_file
        or preparation_link.get("evidence") != preparation_evidence
    ):
        problems.append("environment-host-preparation:contract-drift")

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
    runtime_snapshots = environment.get("runtime_snapshots")
    frozen_gpu = {
        "model": "NVIDIA L4",
        "count": 1,
        "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
        "driver_version": "580.159.03",
        "memory_total_mib": 23034,
    }
    if (
        not isinstance(runtime_snapshots, dict)
        or set(runtime_snapshots) != {"before_dataset_hashing", "after_dataset_hashing"}
        or any(
            not isinstance(runtime_snapshots.get(phase), dict)
            or set(runtime_snapshots[phase]) != {"gpu", "box"}
            or runtime_snapshots[phase].get("gpu") != frozen_gpu
            or runtime_snapshots[phase].get("box") != expected_box
            for phase in ("before_dataset_hashing", "after_dataset_hashing")
        )
    ):
        problems.append("environment-runtime-snapshots:contract-drift")
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
                    [docker_executable, "image", "inspect", "--format={{.Id}}", image],
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
  "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" "$DOCKER_FD_PATH" <<'PY'
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
docker_executable = sys.argv[6]
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
        [docker_executable, *args],
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
if {
    name: os.environ.get(name)
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
} != {
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "DOCKER_CONTEXT": None,
    "DOCKER_TLS_VERIFY": None,
    "DOCKER_CERT_PATH": None,
}:
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
    "$DOCKER_BIN_SHA" "$EXPECTED_MANIFEST_SHA" "$PHASE" "$DOCKER_FD_PATH" <<'PY'
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
    docker_executable,
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
if {
    name: os.environ.get(name)
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
} != {
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "DOCKER_CONTEXT": None,
    "DOCKER_TLS_VERIFY": None,
    "DOCKER_CERT_PATH": None,
}:
    raise SystemExit("Docker runtime environment override appeared")


def command(*args: str) -> str:
    completed = subprocess.run(
        [docker_executable, *args],
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
payload = r'''#!/bin/bash -p
set -euo pipefail

: "${SENTINEL_DOCKER_BIN:?SENTINEL_DOCKER_BIN must be set}"
: "${SENTINEL_DOCKER_EXECUTABLE:?SENTINEL_DOCKER_EXECUTABLE must be set}"
: "${SENTINEL_DOCKER_BIN_ID:?SENTINEL_DOCKER_BIN_ID must be set}"
: "${SENTINEL_DOCKER_BIN_SHA256:?SENTINEL_DOCKER_BIN_SHA256 must be set}"
: "${SENTINEL_DOCKER_WRAPPER_SHA256:?SENTINEL_DOCKER_WRAPPER_SHA256 must be set}"
: "${SENTINEL_MANIFEST_SHA256:?SENTINEL_MANIFEST_SHA256 must be set}"
: "${SENTINEL_BLOCK_ORDINAL:?SENTINEL_BLOCK_ORDINAL must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT:?SENTINEL_CONTAINER_CONTROL_ROOT must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT_ID:?SENTINEL_CONTAINER_CONTROL_ROOT_ID must be set}"
: "${SENTINEL_CONTAINER_CID_DIR:?SENTINEL_CONTAINER_CID_DIR must be set}"
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
OBSERVED_DOCKER_EXECUTABLE_ID=$(stat -Lc '%d:%i' "$SENTINEL_DOCKER_EXECUTABLE" \
  2>/dev/null || stat -f '%d:%i' "$SENTINEL_DOCKER_EXECUTABLE" 2>/dev/null || true)
if [ ! -e "$SENTINEL_DOCKER_EXECUTABLE" ] \
  || [ "$OBSERVED_DOCKER_EXECUTABLE_ID" != "$SENTINEL_DOCKER_BIN_ID" ] \
  || [ "$(sha256sum "$SENTINEL_DOCKER_EXECUTABLE" | awk '{print $1}')" \
    != "$SENTINEL_DOCKER_BIN_SHA256" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL docker-pinned-executable-drift" >&2
  exit 125
fi
OBSERVED_WRAPPER_MODE=$(stat -Lc '%a' "$0" 2>/dev/null \
  || stat -f '%Lp' "$0" 2>/dev/null || true)
OBSERVED_CONTROL_ROOT_ID=$(stat -Lc '%d:%i' "$SENTINEL_CONTAINER_CONTROL_ROOT" \
  2>/dev/null || stat -f '%d:%i' "$SENTINEL_CONTAINER_CONTROL_ROOT" 2>/dev/null || true)
if [ "$0" != "$SENTINEL_CONTAINER_CONTROL_ROOT/docker" ] \
  || [ -L "$0" ] || [ ! -f "$0" ] \
  || [ "$OBSERVED_WRAPPER_MODE" != "500" ] \
  || [ "$(sha256sum "$0" | awk '{print $1}')" != "$SENTINEL_DOCKER_WRAPPER_SHA256" ] \
  || [ -L "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ "$OBSERVED_CONTROL_ROOT_ID" != "$SENTINEL_CONTAINER_CONTROL_ROOT_ID" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL wrapper-identity-drift" >&2
  exit 125
fi
if ! [[ "$SENTINEL_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] \
  || ! [[ "$SENTINEL_BLOCK_ORDINAL" =~ ^([0-9]|[1-9][0-9]|1[01][0-9])$ ]] \
  || [ "$SENTINEL_CONTAINER_CID_DIR" \
    != "$SENTINEL_CONTAINER_CONTROL_ROOT/block-$SENTINEL_BLOCK_ORDINAL" ] \
  || [ -L "$SENTINEL_CONTAINER_CID_DIR" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CID_DIR" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL control-contract" >&2
  exit 125
fi
if [ "$#" -lt 1 ]; then
  echo "I135_DOCKER_WRAPPER_FAIL command-missing" >&2
  exit 125
fi
COMMAND=$1
shift
if [ "$COMMAND" = "kill" ]; then
  if [ "$#" != "1" ]; then
    echo "I135_DOCKER_WRAPPER_FAIL kill-arity" >&2
    exit 125
  fi
  case "$1" in
    renderer|model) ROLE=$1 ;;
    *)
      echo "I135_DOCKER_WRAPPER_FAIL kill-role:$1" >&2
      exit 125
      ;;
  esac
  CID_FILE=$SENTINEL_CONTAINER_CID_DIR/$ROLE.cid
  if [ -L "$CID_FILE" ] || [ ! -f "$CID_FILE" ]; then
    echo "I135_DOCKER_WRAPPER_FAIL kill-cid-file:$ROLE" >&2
    exit 125
  fi
  CID=$(<"$CID_FILE")
  if ! [[ "$CID" =~ ^[0-9a-f]{64}$ ]]; then
    echo "I135_DOCKER_WRAPPER_FAIL kill-cid:$ROLE" >&2
    exit 125
  fi
  INSPECT=$(
    "$SENTINEL_DOCKER_EXECUTABLE" inspect --format \
      '{{.Id}}|{{.Name}}|{{index .Config.Labels "sentinel.mission"}}|{{index .Config.Labels "sentinel.manifest"}}|{{index .Config.Labels "sentinel.mode"}}|{{index .Config.Labels "sentinel.block"}}|{{index .Config.Labels "sentinel.role"}}' \
      "$CID"
  ) || {
    echo "I135_DOCKER_WRAPPER_FAIL kill-inspect:$ROLE" >&2
    exit 125
  }
  EXPECTED_INSPECT="$CID|/$ROLE|iter135|$SENTINEL_MANIFEST_SHA256|analytic|$SENTINEL_BLOCK_ORDINAL|$ROLE"
  if [ "$INSPECT" != "$EXPECTED_INSPECT" ]; then
    echo "I135_DOCKER_WRAPPER_FAIL kill-ownership:$ROLE" >&2
    exit 125
  fi
  exec "$SENTINEL_DOCKER_EXECUTABLE" kill "$CID"
fi
if [ "$COMMAND" != "run" ]; then
  echo "I135_DOCKER_WRAPPER_FAIL unexpected-command:$COMMAND" >&2
  exit 125
fi
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
exec "$SENTINEL_DOCKER_EXECUTABLE" run \
  --label sentinel.mission=iter135 \
  --label "sentinel.manifest=$SENTINEL_MANIFEST_SHA256" \
  --label sentinel.mode=analytic \
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

# I135_PINNED_PYTHON_WRAPPER
PYTHON_WRAPPER_SHA=$(python3 - "$CONTAINER_CONTROL_ROOT/python" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = r'''#!/bin/bash -p
set -euo pipefail

: "${SENTINEL_PYTHON_BIN:?SENTINEL_PYTHON_BIN must be set}"
: "${SENTINEL_PYTHON_EXECUTABLE:?SENTINEL_PYTHON_EXECUTABLE must be set}"
: "${SENTINEL_PYTHON_BIN_ID:?SENTINEL_PYTHON_BIN_ID must be set}"
: "${SENTINEL_PYTHON_BIN_SHA256:?SENTINEL_PYTHON_BIN_SHA256 must be set}"
: "${SENTINEL_PYTHON_WRAPPER_SHA256:?SENTINEL_PYTHON_WRAPPER_SHA256 must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT:?SENTINEL_CONTAINER_CONTROL_ROOT must be set}"
: "${SENTINEL_CONTAINER_CONTROL_ROOT_ID:?SENTINEL_CONTAINER_CONTROL_ROOT_ID must be set}"
if [ "$0" != "$SENTINEL_CONTAINER_CONTROL_ROOT/python" ] \
  || [ -L "$0" ] || [ ! -f "$0" ] \
  || [ "$(stat -Lc '%a' "$0")" != "500" ] \
  || [ "$(sha256sum "$0" | awk '{print $1}')" != "$SENTINEL_PYTHON_WRAPPER_SHA256" ] \
  || [ -L "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ ! -d "$SENTINEL_CONTAINER_CONTROL_ROOT" ] \
  || [ "$(stat -Lc '%d:%i' "$SENTINEL_CONTAINER_CONTROL_ROOT")" \
    != "$SENTINEL_CONTAINER_CONTROL_ROOT_ID" ]; then
  echo "I135_PYTHON_WRAPPER_FAIL wrapper-identity-drift" >&2
  exit 126
fi
if [ -L "$SENTINEL_PYTHON_BIN" ] || [ ! -f "$SENTINEL_PYTHON_BIN" ] \
  || [ ! -x "$SENTINEL_PYTHON_BIN" ] \
  || [ "$(stat -Lc '%d:%i' "$SENTINEL_PYTHON_BIN")" != "$SENTINEL_PYTHON_BIN_ID" ] \
  || [ "$(sha256sum "$SENTINEL_PYTHON_BIN" | awk '{print $1}')" \
    != "$SENTINEL_PYTHON_BIN_SHA256" ] \
  || [ ! -e "$SENTINEL_PYTHON_EXECUTABLE" ] \
  || [ "$(stat -Lc '%d:%i' "$SENTINEL_PYTHON_EXECUTABLE")" \
    != "$SENTINEL_PYTHON_BIN_ID" ] \
  || [ "$(sha256sum "$SENTINEL_PYTHON_EXECUTABLE" | awk '{print $1}')" \
    != "$SENTINEL_PYTHON_BIN_SHA256" ]; then
  echo "I135_PYTHON_WRAPPER_FAIL interpreter-drift" >&2
  exit 126
fi
exec "$SENTINEL_PYTHON_EXECUTABLE" -I "$@"
'''
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o500)
with os.fdopen(descriptor, "wb") as stream:
    stream.write(payload.encode())
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(path, 0o500)
print(hashlib.sha256(payload.encode()).hexdigest())
PY
) || abort "python-wrapper-create"

verify_container_control() {
  python3 - "$CONTAINER_CONTROL_ROOT" "$CONTAINER_CONTROL_ROOT_ID" \
    "$DOCKER_WRAPPER_SHA" "$PYTHON_WRAPPER_SHA" \
    "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" \
    "$PYTHON_BIN" "$PYTHON_BIN_ID" "$PYTHON_BIN_SHA" <<'PY'
import hashlib
import re
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1])
(
    root_identity,
    docker_wrapper_sha,
    python_wrapper_sha,
    docker_text,
    docker_identity,
    docker_sha,
    python_text,
    python_identity,
    python_sha,
) = sys.argv[2:]
docker = Path(docker_text)
python = Path(python_text)
docker_wrapper = root / "docker"
python_wrapper = root / "python"
unexpected = []
for child in root.iterdir() if root.is_dir() else ():
    if child.name in {"docker", "python"}:
        continue
    if re.fullmatch(r"block-(?:[0-9]|[1-9][0-9]|1[01][0-9])", child.name):
        if (
            child.is_symlink()
            or not child.is_dir()
            or stat.S_IMODE(child.stat().st_mode) != 0o700
        ):
            unexpected.append(child.name)
        continue
    if child.name == "watchdog.ready":
        if child.is_symlink() or not child.is_file():
            unexpected.append(child.name)
        continue
    unexpected.append(child.name)
if (
    root.parent != Path("/tmp")
    or not root.name.startswith("sentinel-i135-control.")
    or root.is_symlink()
    or not root.is_dir()
    or root.resolve(strict=True) != root
    or f"{root.stat().st_dev}:{root.stat().st_ino}" != root_identity
    or unexpected
    or docker_wrapper.is_symlink()
    or not docker_wrapper.is_file()
    or docker_wrapper.resolve(strict=True) != docker_wrapper
    or stat.S_IMODE(docker_wrapper.stat().st_mode) != 0o500
    or hashlib.sha256(docker_wrapper.read_bytes()).hexdigest() != docker_wrapper_sha
    or python_wrapper.is_symlink()
    or not python_wrapper.is_file()
    or python_wrapper.resolve(strict=True) != python_wrapper
    or stat.S_IMODE(python_wrapper.stat().st_mode) != 0o500
    or hashlib.sha256(python_wrapper.read_bytes()).hexdigest() != python_wrapper_sha
    or docker.is_symlink()
    or not docker.is_file()
    or docker.resolve(strict=True) != docker
    or f"{docker.stat().st_dev}:{docker.stat().st_ino}" != docker_identity
    or hashlib.sha256(docker.read_bytes()).hexdigest() != docker_sha
    or python.is_symlink()
    or not python.is_file()
    or python.resolve(strict=True) != python
    or f"{python.stat().st_dev}:{python.stat().st_ino}" != python_identity
    or hashlib.sha256(python.read_bytes()).hexdigest() != python_sha
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
    "$DOCKER_BIN" "$DOCKER_BIN_ID" "$DOCKER_BIN_SHA" "$DOCKER_FD_PATH" <<'PY'
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
    docker_executable,
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
        [docker_executable, "image", "inspect", "--format", "{{.Id}}", expected_image],
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
    SENTINEL_DOCKER_EXECUTABLE="$DOCKER_FD_PATH" \
    SENTINEL_DOCKER_BIN_ID="$DOCKER_BIN_ID" \
    SENTINEL_DOCKER_BIN_SHA256="$DOCKER_BIN_SHA" \
    SENTINEL_DOCKER_WRAPPER_SHA256="$DOCKER_WRAPPER_SHA" \
    SENTINEL_PYTHON_BIN="$PYTHON_BIN" \
    SENTINEL_PYTHON_EXECUTABLE="$PYTHON_FD_PATH" \
    SENTINEL_PYTHON_BIN_ID="$PYTHON_BIN_ID" \
    SENTINEL_PYTHON_BIN_SHA256="$PYTHON_BIN_SHA" \
    SENTINEL_PYTHON_WRAPPER_SHA256="$PYTHON_WRAPPER_SHA" \
    SENTINEL_MANIFEST_SHA256="$EXPECTED_MANIFEST_SHA" \
    SENTINEL_BLOCK_ORDINAL="$ORDINAL" \
    SENTINEL_CONTAINER_CONTROL_ROOT="$CONTAINER_CONTROL_ROOT" \
    SENTINEL_CONTAINER_CONTROL_ROOT_ID="$CONTAINER_CONTROL_ROOT_ID" \
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
    "$DOCKER_RUNTIME_SNAPSHOT_SHA" "$EXPECTED_ACTIVATION_SHA" \
    "$GITHUB_ACTIVATION_COMMIT" "$GITHUB_FINAL_MANIFEST_COMMIT" \
    "$GITHUB_CHECK_310_ID" "$GITHUB_CHECK_311_ID" \
    "$PYTHON_WRAPPER_SHA" "$PYTHON_BIN_SHA" "$PYTHON_BIN_ID" "$$" <<'PY'
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

lock = Path(sys.argv[1])
manifest_sha256 = sys.argv[2]
dataset_snapshot_sha256 = sys.argv[3]
docker_snapshot_sha256 = sys.argv[4]
activation_receipt_sha256 = sys.argv[5]
activation_commit = sys.argv[6]
final_manifest_commit = sys.argv[7]
check_310_id = int(sys.argv[8])
check_311_id = int(sys.argv[9])
python_wrapper_sha256 = sys.argv[10]
python_binary_sha256 = sys.argv[11]
python_binary_identity = sys.argv[12]
pid = int(sys.argv[13])
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
    or re.fullmatch(r"[0-9a-f]{64}", activation_receipt_sha256) is None
    or re.fullmatch(r"[0-9a-f]{40}", activation_commit) is None
    or re.fullmatch(r"[0-9a-f]{40}", final_manifest_commit) is None
    or activation_commit == final_manifest_commit
    or check_310_id <= 0
    or check_311_id <= 0
    or check_310_id == check_311_id
    or re.fullmatch(r"[0-9a-f]{64}", python_wrapper_sha256) is None
    or re.fullmatch(r"[0-9a-f]{64}", python_binary_sha256) is None
    or re.fullmatch(r"[0-9]+:[0-9]+", python_binary_identity) is None
):
    raise SystemExit("analytic lock publication contract drift")
authority = {
    "schema": "iter135.github_launch_authority.v1",
    "repository": "manfromnowhere143/sentinel",
    "branch": "master",
    "activation_commit": activation_commit,
    "final_manifest_commit": final_manifest_commit,
    "activation_receipt_sha256": activation_receipt_sha256,
    "manifest_sha256": manifest_sha256,
    "checks": [
        {
            "name": "check (3.10)",
            "id": check_310_id,
            "head_sha": activation_commit,
            "app_slug": "github-actions",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "name": "check (3.11)",
            "id": check_311_id,
            "head_sha": activation_commit,
            "app_slug": "github-actions",
            "status": "completed",
            "conclusion": "success",
        },
    ],
}
authority["authority_payload_sha256"] = hashlib.sha256(
    json.dumps(
        authority,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
).hexdigest()
payload = {
    "schema": "iter135.analytic_lock.v3",
    "manifest_sha256": manifest_sha256,
    "dataset_runtime_snapshot_sha256": dataset_snapshot_sha256,
    "docker_runtime_snapshot_sha256": docker_snapshot_sha256,
    "python_wrapper_sha256": python_wrapper_sha256,
    "python_binary_sha256": python_binary_sha256,
    "python_binary_identity": python_binary_identity,
    "github_launch_authority": authority,
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
verify_docker_client_binding \
  || abort "docker-client-revoked-at-final-analytic-arm"
[ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_RECEIPT_SHA" ] \
  || abort "docker-v3-runtime-revoked-at-final-analytic-arm"
verify_current_mission_state >/dev/null \
  || abort "mission-state-revoked-at-final-analytic-arm"
verify_python_interpreter_binding \
  || abort "python-interpreter-revoked-at-final-analytic-arm"
FINAL_LOCAL_ACTIVATION_BINDING=$(verify_launch_activation) \
  || abort "launch-activation-revoked-at-final-analytic-arm"
if [ "$FINAL_LOCAL_ACTIVATION_BINDING" \
  != "$ACTIVATION_BASELINE_SHA $ACTIVATION_BASELINE_ID $ACTIVATION_BASELINE_BYTES $LOCAL_FINAL_MANIFEST_COMMIT" ]; then
  abort "launch-activation-binding-drift-at-final-analytic-arm"
fi
GITHUB_LAUNCH_BINDING=$(verify_github_launch_authority) \
  || abort "github-launch-authority-revoked-at-final-analytic-arm"
read -r GITHUB_ACTIVATION_COMMIT GITHUB_FINAL_MANIFEST_COMMIT \
  GITHUB_CHECK_310_ID GITHUB_CHECK_311_ID \
  <<<"$GITHUB_LAUNCH_BINDING"
if ! [[ "$GITHUB_ACTIVATION_COMMIT" =~ ^[0-9a-f]{40}$ \
  && "$GITHUB_FINAL_MANIFEST_COMMIT" =~ ^[0-9a-f]{40}$ \
  && "$GITHUB_CHECK_310_ID" =~ ^[1-9][0-9]*$ \
  && "$GITHUB_CHECK_311_ID" =~ ^[1-9][0-9]*$ ]] \
  || [ "$GITHUB_ACTIVATION_COMMIT" != "$EXPECTED_ACTIVATION_COMMIT" ] \
  || [ "$GITHUB_FINAL_MANIFEST_COMMIT" != "$LOCAL_FINAL_MANIFEST_COMMIT" ] \
  || [ "$GITHUB_FINAL_MANIFEST_COMMIT" = "$GITHUB_ACTIVATION_COMMIT" ] \
  || [ "$GITHUB_CHECK_310_ID" = "$GITHUB_CHECK_311_ID" ]; then
  abort "github-launch-publication-output:$GITHUB_LAUNCH_BINDING"
fi
readonly GITHUB_ACTIVATION_COMMIT GITHUB_FINAL_MANIFEST_COMMIT \
  GITHUB_CHECK_310_ID GITHUB_CHECK_311_ID
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
echo "I135_ANALYTIC_ARMED lock=$LOCK lock_id=$ANALYTIC_LOCK_ID output_root=$OUTPUT_ROOT python_wrapper_sha256=$PYTHON_WRAPPER_SHA python_binary_sha256=$PYTHON_BIN_SHA python_binary_identity=$PYTHON_BIN_ID"
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
  verify_python_interpreter_binding \
    || abort "python-interpreter-revoked-before-block:$ORDINAL"
  verify_docker_client_binding \
    || abort "docker-client-revoked-before-block:$ORDINAL"
  [ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_RECEIPT_SHA" ] \
    || abort "docker-v3-runtime-revoked-before-block:$ORDINAL"
  verify_launch_activation >/dev/null \
    || abort "launch-activation-revoked-before-block:$ORDINAL"
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
verify_docker_client_binding || abort "docker-client-revoked-before-done"
[ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_RECEIPT_SHA" ] \
  || abort "docker-v3-runtime-revoked-before-done"
verify_output_storage_identity before-done 0 \
  || abort "storage-identity-before-done"
verify_current_mission_state >/dev/null \
  || abort "mission-state-revoked-before-done"
verify_python_interpreter_binding \
  || abort "python-interpreter-revoked-before-done"
verify_launch_activation >/dev/null \
  || abort "launch-activation-revoked-before-done"
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
  "$DATASET_RUNTIME_SNAPSHOT_SHA" "$DOCKER_RUNTIME_SNAPSHOT_SHA" \
  "$EXPECTED_ACTIVATION_SHA" "$GITHUB_ACTIVATION_COMMIT" \
  "$GITHUB_FINAL_MANIFEST_COMMIT" "$GITHUB_CHECK_310_ID" \
  "$GITHUB_CHECK_311_ID" "$PYTHON_WRAPPER_SHA" "$PYTHON_BIN_SHA" \
  "$PYTHON_BIN_ID" "$$" <<'PY' \
  || abort "analytic-lock-drift-before-done"
import hashlib
import json
import stat
import sys
from pathlib import Path

lock = Path(sys.argv[1])
expected_identity = sys.argv[2]
expected_manifest = sys.argv[3]
expected_dataset_snapshot = sys.argv[4]
expected_docker_snapshot = sys.argv[5]
expected_activation_sha = sys.argv[6]
expected_activation_commit = sys.argv[7]
expected_final_manifest = sys.argv[8]
expected_check_ids = [int(sys.argv[9]), int(sys.argv[10])]
expected_python_wrapper = sys.argv[11]
expected_python_sha = sys.argv[12]
expected_python_identity = sys.argv[13]
expected_pid = int(sys.argv[14])
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
        "python_wrapper_sha256",
        "python_binary_sha256",
        "python_binary_identity",
        "github_launch_authority",
        "pid",
        "created_at_utc",
    }
    or payload.get("schema") != "iter135.analytic_lock.v3"
    or payload.get("manifest_sha256") != expected_manifest
    or payload.get("dataset_runtime_snapshot_sha256") != expected_dataset_snapshot
    or payload.get("docker_runtime_snapshot_sha256") != expected_docker_snapshot
    or payload.get("python_wrapper_sha256") != expected_python_wrapper
    or payload.get("python_binary_sha256") != expected_python_sha
    or payload.get("python_binary_identity") != expected_python_identity
    or payload.get("pid") != expected_pid
    or not isinstance(payload.get("created_at_utc"), str)
    or not payload["created_at_utc"].endswith("Z")
):
    raise SystemExit("analytic lock receipt contract drift")
authority = payload.get("github_launch_authority")
if not isinstance(authority, dict) or set(authority) != {
    "schema",
    "repository",
    "branch",
    "activation_commit",
    "final_manifest_commit",
    "activation_receipt_sha256",
    "manifest_sha256",
    "checks",
    "authority_payload_sha256",
}:
    raise SystemExit("analytic lock GitHub authority field-set drift")
claimed_authority_sha = authority.get("authority_payload_sha256")
canonical_authority = dict(authority)
canonical_authority.pop("authority_payload_sha256")
actual_authority_sha = hashlib.sha256(
    json.dumps(
        canonical_authority,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
).hexdigest()
expected_checks = [
    {
        "name": name,
        "id": check_id,
        "head_sha": expected_activation_commit,
        "app_slug": "github-actions",
        "status": "completed",
        "conclusion": "success",
    }
    for name, check_id in zip(("check (3.10)", "check (3.11)"), expected_check_ids)
]
if (
    authority.get("schema") != "iter135.github_launch_authority.v1"
    or authority.get("repository") != "manfromnowhere143/sentinel"
    or authority.get("branch") != "master"
    or authority.get("activation_commit") != expected_activation_commit
    or authority.get("final_manifest_commit") != expected_final_manifest
    or authority.get("activation_receipt_sha256") != expected_activation_sha
    or authority.get("manifest_sha256") != expected_manifest
    or authority.get("checks") != expected_checks
    or claimed_authority_sha != actual_authority_sha
):
    raise SystemExit("analytic lock GitHub authority binding drift")
PY
FINAL_LOG_ID=$(stat -Lc '%d:%i' "$CANONICAL_LOG") || abort "canonical-log-missing-before-done"
if [ "$FINAL_LOG_ID" != "$CANONICAL_LOG_ID" ]; then
  abort "canonical-log-inode-drift-before-done:$FINAL_LOG_ID!=$CANONICAL_LOG_ID"
fi
FINAL_ELAPSED=$(monotonic_elapsed) || abort "G9-monotonic-clock-before-done"
if [ "$FINAL_ELAPSED" -gt "$CEILING_SECONDS" ]; then
  abort "G9-ceiling-before-done:$FINAL_ELAPSED"
fi
echo "I135_DONE_METADATA at=$(date -u +%Y-%m-%dT%H:%M:%SZ) manifest_sha256=$EXPECTED_MANIFEST_SHA runtime_snapshot=$RUNTIME_SNAPSHOT dataset_runtime_snapshot_sha256=$DATASET_RUNTIME_SNAPSHOT_SHA dataset_runtime_snapshot_id=$DATASET_RUNTIME_SNAPSHOT_ID docker_runtime_snapshot_sha256=$DOCKER_RUNTIME_SNAPSHOT_SHA docker_runtime_snapshot_id=$DOCKER_RUNTIME_SNAPSHOT_ID python_wrapper_sha256=$PYTHON_WRAPPER_SHA python_binary_sha256=$PYTHON_BIN_SHA python_binary_identity=$PYTHON_BIN_ID launch_lock_retained=$LOCK launch_lock_id=$ANALYTIC_LOCK_ID elapsed_seconds=$FINAL_ELAPSED prior_smoke_gpu_seconds=$PRIOR_SMOKE_SECONDS blocks=$EXECUTED_BLOCKS episodes=$((EXECUTED_BLOCKS * 20)) output_root=$OUTPUT_ROOT output_device=/dev/nvme0n2 output_uuid=9a98277e-b21f-4ffc-8f14-3f2235b43103 start_free_bytes=$START_FREE_BYTES end_free_bytes=$END_FREE_BYTES output_bytes=$OUTPUT_BYTES"
echo "I135_DOSE_DONE"
