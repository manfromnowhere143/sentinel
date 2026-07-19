#!/bin/bash -p
# Iteration 135 one-shot, four-dose, nonanalytic live smoke.
#
# This program is intentionally inert until a separately hash-addressed pre-smoke manifest,
# every bound local/remote byte, repository state, image ID, and a single idle L4 all agree.  It
# writes only to the dedicated smoke sibling and never invokes the analytic launcher.  A failed
# attempt retains its lock, staging directory, journal, logs, and partial evidence; there is no
# retry path.

# Deployment precondition: invoke this file from a trusted, sanitized `env -i` or
# equivalently locked-down systemd unit. These checks detect inherited contamination;
# they cannot undo native dynamic-loader code that ran before Bash read its first byte.
# Privileged-mode Bash suppresses BASH_ENV processing and imported shell functions. The caller
# must also supply the same minimal PATH used by the captured v3 host receipt.
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
  echo "I135_SMOKE_PREFLIGHT_FAIL hostile-dynamic-loader:$HOSTILE_LOADER_VARIABLE" >&2
  exit 1
fi
CANONICAL_PATH=/usr/bin:/bin:/usr/sbin:/sbin
BOOTSTRAP_ENV_PROBLEM=
BOOTSTRAP_ENV_COUNT=0
while IFS= read -r BOOTSTRAP_NAME; do
  BOOTSTRAP_ENV_COUNT=$((BOOTSTRAP_ENV_COUNT + 1))
  case "$BOOTSTRAP_NAME" in
    PATH|PWD|SHLVL|SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT|SENTINEL_SMOKE_INPUT_MANIFEST_SHA256)
      ;;
    *)
      BOOTSTRAP_ENV_PROBLEM=$BOOTSTRAP_NAME
      break
      ;;
  esac
done < <(compgen -e)
if [ -n "$BOOTSTRAP_ENV_PROBLEM" ]; then
  echo "I135_SMOKE_PREFLIGHT_FAIL hostile-bootstrap-environment:$BOOTSTRAP_ENV_PROBLEM" >&2
  exit 1
fi
if [ "$BOOTSTRAP_ENV_COUNT" != "5" ]; then
  echo "I135_SMOKE_PREFLIGHT_FAIL bootstrap-environment-field-set" >&2
  exit 1
fi
if [ "${PATH-}" != "$CANONICAL_PATH" ]; then
  echo "I135_SMOKE_PREFLIGHT_FAIL hostile-bootstrap-path" >&2
  exit 1
fi
if [ "${PWD-}" != "/opt/sentinel-stack/iter135" ] \
  || [ "$(pwd -P)" != "/opt/sentinel-stack/iter135" ]; then
  echo "I135_SMOKE_PREFLIGHT_FAIL hostile-bootstrap-working-directory" >&2
  exit 1
fi
if [ "${SHLVL-}" != "1" ]; then
  echo "I135_SMOKE_PREFLIGHT_FAIL hostile-bootstrap-shell-level" >&2
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

STACK=/opt/sentinel-stack
I135=$STACK/iter135
MANIFEST_SOURCE=$I135/launch_manifest.json
ENV_SOURCE=$I135/env_receipts.json
HOST_PACKET_SOURCE=$I135/host_packet_manifest.json
HOST_PREPARATION_SOURCE=$I135/host_preparation_receipt.json
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
EXPECTED_MANIFEST_COMMIT=${SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT:-}
CAPTURE_TIMEOUT_SECONDS=180
DOSE_TIMEOUT_SECONDS=1800
EXPECTED_BLIND_PATCHED_SERVER_SHA256=b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf
EXPECTED_UNIAD_IMAGE_ID=sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb
EXPECTED_NEURAD_IMAGE_ID=sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c
EXPECTED_NCAP_IMAGE_ID=sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce
RUNNER_SHA=
RUNNER_ID=
SMOKE_LOCK_ID=
SMOKE_LOCK_SHA=
SMOKE_STARTED=0
SCHEDULE_TARGET_ID=
STAGING_ROOT_ID=
PYTHON_BIN=
PYTHON_FD_PATH=
PYTHON_BIN_ID=
PYTHON_BIN_SHA=
PYTHON_BIN_BYTES=
PYTHON_BIN_VERSION=
DOCKER_BIN=
DOCKER_COMMAND=
DOCKER_FD_PATH=
DOCKER_BIN_ID=
DOCKER_BIN_SHA=
DOCKER_BIN_BYTES=
DOCKER_WRAPPER_SHA=
PYTHON_WRAPPER_SHA=

fail_preflight() {
  echo "I135_SMOKE_PREFLIGHT_FAIL $*" >&2
  exit 1
}

for REQUIRED_COMMAND in awk bash cp dirname docker env findmnt git grep mkdir mv \
  nvidia-smi ps python3 readlink rm sed sha256sum sleep stat timeout touch tr wc; do
  command -v "$REQUIRED_COMMAND" >/dev/null 2>&1 \
    || fail_preflight "command-missing:$REQUIRED_COMMAND"
done

# Resolve the interpreter once, compare its physical bytes and version to the v3 environment
# receipt, and route every later Python invocation through that exact binary in isolated mode.
# The first tiny parser is read-only; no smoke path or lock exists yet.
PYTHON_COMMAND=$(command -v python3) || fail_preflight "python-command-resolution"
PYTHON_BIN=$(readlink -f "$PYTHON_COMMAND") || fail_preflight "python-physical-path"
[ -f "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ] && [ ! -L "$PYTHON_BIN" ] \
  || fail_preflight "python-physical-binary:$PYTHON_BIN"
if ! exec 10< "$PYTHON_BIN"; then
  fail_preflight "python-pinned-fd-open:$PYTHON_BIN"
fi
PYTHON_FD_PATH=/proc/$$/fd/10
[ -e "$PYTHON_FD_PATH" ] || fail_preflight "python-pinned-fd-missing"
PYTHON_BIN_ID=$(stat -Lc '%d:%i' "$PYTHON_FD_PATH") \
  || fail_preflight "python-physical-identity"
if [ "$(stat -Lc '%d:%i' "$PYTHON_BIN")" != "$PYTHON_BIN_ID" ]; then
  fail_preflight "python-path-raced-before-pin"
fi
PYTHON_BIN_SHA=$(sha256sum "$PYTHON_FD_PATH" | awk '{print $1}') \
  || fail_preflight "python-physical-sha256"
PYTHON_BIN_BYTES=$(stat -Lc '%s' "$PYTHON_FD_PATH") \
  || fail_preflight "python-physical-bytes"
PYTHON_BIN_VERSION=$("$PYTHON_FD_PATH" -I -c \
  'import platform; print(platform.python_version())') \
  || fail_preflight "python-physical-version"
"$PYTHON_FD_PATH" -I - "$ENV_SOURCE" "$PYTHON_BIN" "$PYTHON_BIN_SHA" \
  "$PYTHON_BIN_BYTES" "$PYTHON_BIN_VERSION" <<'PY' \
  || fail_preflight "python-environment-binding"
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
verify_python_interpreter_binding || fail_preflight "python-interpreter-initial-drift"

DOCKER_COMMAND=$(command -v docker) || fail_preflight "docker-command-resolution"
DOCKER_BIN=$(readlink -f "$DOCKER_COMMAND") \
  || fail_preflight "docker-binary-realpath"
if [ ! -f "$DOCKER_BIN" ] || [ ! -x "$DOCKER_BIN" ] || [ -L "$DOCKER_BIN" ]; then
  fail_preflight "docker-binary-physical:$DOCKER_BIN"
fi
if ! exec 11< "$DOCKER_BIN"; then
  fail_preflight "docker-pinned-fd-open:$DOCKER_BIN"
fi
DOCKER_FD_PATH=/proc/$$/fd/11
DOCKER_BIN_ID=$(stat -Lc '%d:%i' "$DOCKER_FD_PATH") \
  || fail_preflight "docker-binary-identity"
if [ "$(stat -Lc '%d:%i' "$DOCKER_BIN")" != "$DOCKER_BIN_ID" ]; then
  fail_preflight "docker-path-raced-before-pin"
fi
DOCKER_BIN_SHA=$(sha256sum "$DOCKER_FD_PATH" | awk '{print $1}') \
  || fail_preflight "docker-binary-sha256"
DOCKER_BIN_BYTES=$(stat -Lc '%s' "$DOCKER_FD_PATH") \
  || fail_preflight "docker-binary-bytes"
readonly DOCKER_COMMAND DOCKER_BIN DOCKER_FD_PATH DOCKER_BIN_ID DOCKER_BIN_SHA \
  DOCKER_BIN_BYTES
docker() {
  "$DOCKER_FD_PATH" "$@"
}
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
verify_docker_client_binding || fail_preflight "docker-client-initial-drift"

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

(
    environment_text,
    invocation_text,
    physical_text,
    executable_text,
    expected_identity,
    expected_sha,
    expected_bytes_text,
) = sys.argv[1:]
invocation = Path(invocation_text).absolute()
physical = Path(physical_text).absolute()
executable = Path(executable_text)
expected_bytes = int(expected_bytes_text)
environment = json.loads(Path(environment_text).read_bytes())
expected = environment.get("docker_runtime")


def identity(row):
    return (
        row.st_dev,
        row.st_ino,
        row.st_size,
        row.st_mtime_ns,
        row.st_ctime_ns,
        stat.S_IMODE(row.st_mode),
    )


def digest(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        value = hashlib.sha256()
        byte_count = 0
        while chunk := os.read(descriptor, 1 << 20):
            value.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if identity(before) != identity(after) or byte_count != before.st_size:
        raise SystemExit("Docker client changed while hash-bound")
    return value.hexdigest(), byte_count, before


if (
    not invocation.is_file()
    or invocation.resolve(strict=True) != physical
    or physical.is_symlink()
    or not physical.is_file()
    or physical.resolve(strict=True) != physical
    or not executable.exists()
):
    raise SystemExit("Docker client physical path drift")
fd_sha, fd_bytes, fd_row = digest(executable)
path_sha, path_bytes, path_row = digest(physical)
actual_identity = f"{fd_row.st_dev}:{fd_row.st_ino}"
if (
    actual_identity != expected_identity
    or identity(fd_row) != identity(path_row)
    or fd_sha != path_sha
    or fd_sha != expected_sha
    or fd_bytes != path_bytes
    or fd_bytes != expected_bytes
):
    raise SystemExit("Docker client pinned FD or pathname drift")
runtime_descriptor = os.open(executable, os.O_RDONLY | os.O_CLOEXEC)
runtime_executable = f"/proc/self/fd/{runtime_descriptor}"

docker_environment = {
    "DOCKER_CONFIG": "/nonexistent",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "TZ": "UTC",
}


def run(*arguments):
    completed = subprocess.run(
        [runtime_executable, *arguments],
        check=True,
        capture_output=True,
        env=docker_environment,
        timeout=20,
        pass_fds=(runtime_descriptor,),
    )
    if len(completed.stdout) > 4 * 1024 * 1024 or len(completed.stderr) > 64 * 1024:
        raise SystemExit("Docker identity probe exceeded frozen byte ceiling")
    return completed.stdout


def document(*arguments):
    value = json.loads(run(*arguments))
    if not isinstance(value, dict):
        raise SystemExit("Docker identity probe did not return an object")
    return value


def text(value, label, maximum=512):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SystemExit(f"Docker runtime text field drift: {label}")
    return value


def integer(value, label, maximum):
    if type(value) is not int or not (0 < value <= maximum):
        raise SystemExit(f"Docker runtime integer field drift: {label}")
    return value


version = document("version", "--format", "{{json .}}")
info = document("info", "--format", "{{json .}}")
context_name = text(run("context", "show").decode().strip(), "context:name")
endpoint_raw = run(
    "context",
    "inspect",
    "--format",
    "{{json .Endpoints.docker.Host}}",
    context_name,
)
endpoint = text(json.loads(endpoint_raw), "context:endpoint", maximum=1024)
client_raw = version.get("Client")
server_raw = version.get("Server")
if not isinstance(client_raw, dict) or not isinstance(server_raw, dict):
    raise SystemExit("Docker version client/server schema drift")
platform_raw = server_raw.get("Platform")
# Docker Engine 29 moved Experimental out of the top-level Server object into the Engine
# component's Details map, where it is the string "true"/"false"; older engines carry it at the
# top level as a bool. Read the top level first and fall back to the Engine component so both
# daemon generations project to the same bool. Every other daemon field is still read from the
# top level exactly as before, so this changes no other recorded byte.
engine_details_raw = {}
components_raw = server_raw.get("Components")
if isinstance(components_raw, list):
    for component_row in components_raw:
        if isinstance(component_row, dict) and component_row.get("Name") == "Engine":
            details_row = component_row.get("Details")
            if isinstance(details_row, dict):
                engine_details_raw = details_row
            break
experimental_raw = server_raw.get("Experimental")
if experimental_raw is None:
    experimental_raw = engine_details_raw.get("Experimental")
if experimental_raw in ("true", "false"):
    experimental_raw = experimental_raw == "true"
if not isinstance(platform_raw, dict) or type(experimental_raw) is not bool:
    raise SystemExit("Docker daemon version schema drift")
client_version = {
    "version": text(client_raw.get("Version"), "client:version"),
    "api_version": text(client_raw.get("ApiVersion"), "client:api-version"),
    "git_commit": text(client_raw.get("GitCommit"), "client:git-commit"),
    "go_version": text(client_raw.get("GoVersion"), "client:go-version"),
    "os": text(client_raw.get("Os"), "client:os"),
    "arch": text(client_raw.get("Arch"), "client:arch"),
    "build_time": text(client_raw.get("BuildTime"), "client:build-time"),
    "context": text(client_raw.get("Context"), "client:context"),
}
daemon_version = {
    "platform_name": text(platform_raw.get("Name"), "daemon:platform-name"),
    "version": text(server_raw.get("Version"), "daemon:version"),
    "api_version": text(server_raw.get("ApiVersion"), "daemon:api-version"),
    "min_api_version": text(
        server_raw.get("MinAPIVersion"), "daemon:min-api-version"
    ),
    "git_commit": text(server_raw.get("GitCommit"), "daemon:git-commit"),
    "go_version": text(server_raw.get("GoVersion"), "daemon:go-version"),
    "os": text(server_raw.get("Os"), "daemon:os"),
    "arch": text(server_raw.get("Arch"), "daemon:arch"),
    "build_time": text(server_raw.get("BuildTime"), "daemon:build-time"),
    "experimental": experimental_raw,
}
daemon_info = {
    "id": text(info.get("ID"), "info:id"),
    "name": text(info.get("Name"), "info:name"),
    "server_version": text(info.get("ServerVersion"), "info:server-version"),
    "docker_root_dir": text(info.get("DockerRootDir"), "info:docker-root", maximum=1024),
    "driver": text(info.get("Driver"), "info:driver"),
    "operating_system": text(info.get("OperatingSystem"), "info:operating-system"),
    "os_type": text(info.get("OSType"), "info:os-type"),
    "architecture": text(info.get("Architecture"), "info:architecture"),
    "ncpu": integer(info.get("NCPU"), "info:ncpu", 1_000_000),
    "mem_total": integer(info.get("MemTotal"), "info:mem-total", 2**63 - 1),
    "kernel_version": text(info.get("KernelVersion"), "info:kernel-version"),
    "cgroup_driver": text(info.get("CgroupDriver"), "info:cgroup-driver"),
    "cgroup_version": text(info.get("CgroupVersion"), "info:cgroup-version"),
}
live = {
    "schema": "iter135.docker_runtime_receipt.v1",
    "client": {
        "invocation_path": str(invocation),
        "physical_path": str(physical),
        "realpath": str(physical),
        "sha256": fd_sha,
        "bytes": fd_bytes,
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
    or expected != live
):
    raise SystemExit("live Docker client/context/daemon drift from v3 receipt")
print(hashlib.sha256(json.dumps(live, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
# END I135_DOCKER_RUNTIME_PYTHON
PY
}

DOCKER_RUNTIME_SHA=$(verify_docker_v3_runtime) \
  || fail_preflight "docker-v3-runtime-binding"
[[ $DOCKER_RUNTIME_SHA =~ ^[0-9a-f]{64}$ ]] \
  || fail_preflight "docker-v3-runtime-binding-output"
readonly DOCKER_RUNTIME_SHA

verify_github_pre_smoke_authority() {
  python3 - "$EXPECTED_MANIFEST_COMMIT" "$EXPECTED_MANIFEST_SHA" \
    "$MANIFEST_SOURCE" <<'PY'
# BEGIN I135_GITHUB_SMOKE_AUTHORITY_PYTHON
import base64
import hashlib
import json
import os
import re
import ssl
import stat
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = "https://api.github.com/repos/manfromnowhere143/sentinel"
MANIFEST_REPOSITORY_PATH = (
    "experiments/iter135_neuroncap_blind_braking_dose_response/launch_manifest.json"
)
EXPECTED_CHECKS = {"check (3.10)", "check (3.11)"}
WORKFLOW_ID = 304353015
WORKFLOW_NAME = "ci"
WORKFLOW_FILE = "ci.yml"
WORKFLOW_PATH = ".github/workflows/ci.yml"
MAX_WORKFLOW_RUNS = 100
MAX_JOBS = 100
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


def canonical_github_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("GitHub timestamp is not text")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as error:
        raise ValueError("GitHub timestamp is malformed") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("GitHub timestamp is not canonical UTC")
    return parsed


def stable_physical_bytes(path: Path) -> bytes:
    path = path.absolute()
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"deployed pre-smoke manifest is not physical: {path}")
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
        raise SystemExit("deployed pre-smoke manifest changed while read")
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
        raise ValueError("pre-smoke commit is not the current canonical GitHub master")


def validate_workflow_runs(payload: object, expected_commit: str) -> dict[str, object]:
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        raise ValueError("GitHub workflow-runs response is malformed")
    runs = payload["workflow_runs"]
    if (
        type(payload.get("total_count")) is not int
        or payload["total_count"] != len(runs)
        or payload["total_count"] < 1
        or payload["total_count"] > MAX_WORKFLOW_RUNS
    ):
        raise ValueError("GitHub workflow-runs page is incomplete")
    run_ids = set()
    suite_ids = set()
    run_numbers = set()
    projection = []
    for row in runs:
        if not isinstance(row, dict):
            raise ValueError("GitHub workflow-run row is malformed")
        run_id = row.get("id")
        suite_id = row.get("check_suite_id")
        run_number = row.get("run_number")
        run_attempt = row.get("run_attempt")
        if (
            type(run_id) is not int
            or run_id <= 0
            or type(suite_id) is not int
            or suite_id <= 0
            or type(run_number) is not int
            or run_number <= 0
            or type(run_attempt) is not int
            or run_attempt <= 0
            or run_id in run_ids
            or suite_id in suite_ids
            or run_number in run_numbers
        ):
            raise ValueError("GitHub workflow-run identity drift")
        run_ids.add(run_id)
        suite_ids.add(suite_id)
        run_numbers.add(run_number)
        try:
            created_at = canonical_github_utc(row.get("created_at"))
            updated_at = canonical_github_utc(row.get("updated_at"))
            started_value = row.get("run_started_at")
            started_at = (
                canonical_github_utc(started_value)
                if started_value is not None
                else None
            )
        except ValueError as error:
            raise ValueError("GitHub workflow-run timestamp drift") from error
        if (
            created_at > updated_at
            or (started_at is not None and not (created_at <= started_at <= updated_at))
        ):
            raise ValueError("GitHub workflow-run timestamp drift")
        expected_url = f"{API_ROOT}/actions/runs/{run_id}"
        if (
            type(row.get("workflow_id")) is not int
            or row.get("workflow_id") != WORKFLOW_ID
            or row.get("name") != WORKFLOW_NAME
            or row.get("path") != WORKFLOW_PATH
            or row.get("head_branch") != "master"
            or row.get("head_sha") != expected_commit
            or row.get("event") != "push"
            or not isinstance(row.get("status"), str)
            or (
                row.get("conclusion") is not None
                and not isinstance(row.get("conclusion"), str)
            )
            or row.get("url") != expected_url
            or row.get("jobs_url") != f"{expected_url}/jobs"
        ):
            raise ValueError("GitHub workflow-run binding drift")
        projection.append(
            {
                "id": run_id,
                "check_suite_id": suite_id,
                "run_number": run_number,
                "run_attempt": run_attempt,
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "created_at": row.get("created_at"),
                "run_started_at": started_value,
                "updated_at": row.get("updated_at"),
            }
        )
    selected = max(projection, key=lambda row: row["run_number"])
    if (
        selected["status"] != "completed"
        or selected["conclusion"] != "success"
        or selected["run_started_at"] is None
    ):
        raise ValueError("latest canonical GitHub workflow run is not green")
    return selected


def validate_ci(
    payload: object, expected_commit: str, workflow_run: dict[str, object]
) -> list[dict[str, object]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("GitHub workflow jobs response is malformed")
    jobs = payload["jobs"]
    if (
        type(payload.get("total_count")) is not int
        or payload["total_count"] != len(jobs)
        or payload["total_count"] != len(EXPECTED_CHECKS)
        or payload["total_count"] > MAX_JOBS
    ):
        raise ValueError("GitHub workflow jobs page is incomplete or not the exact CI matrix")
    selected = {}
    identities = set()
    expected_run_id = workflow_run["id"]
    expected_run_attempt = workflow_run["run_attempt"]
    for row in jobs:
        if not isinstance(row, dict) or row.get("name") not in EXPECTED_CHECKS:
            raise ValueError("GitHub workflow jobs contain an unexpected matrix row")
        check_id = row.get("id")
        if (
            type(check_id) is not int
            or check_id <= 0
            or check_id in identities
            or row["name"] in selected
        ):
            raise ValueError("GitHub CI check IDs or names are not unique")
        identities.add(check_id)
        job_run_id = row.get("run_id")
        job_run_attempt = row.get("run_attempt")
        try:
            started_at = canonical_github_utc(row.get("started_at"))
            completed_at = canonical_github_utc(row.get("completed_at"))
            workflow_created_at = canonical_github_utc(workflow_run.get("created_at"))
            workflow_updated_at = canonical_github_utc(workflow_run.get("updated_at"))
        except ValueError as error:
            raise ValueError(f"GitHub CI timestamp drift: {row.get('name')}") from error
        if not (
            workflow_created_at
            <= started_at
            <= completed_at
            <= workflow_updated_at
        ):
            raise ValueError(f"GitHub CI timestamp drift: {row.get('name')}")
        if (
            type(job_run_id) is not int
            or job_run_id <= 0
            or job_run_id != expected_run_id
            or type(job_run_attempt) is not int
            or job_run_attempt <= 0
            or job_run_attempt != expected_run_attempt
            or row.get("head_sha") != expected_commit
            or row.get("head_branch") != "master"
            or row.get("workflow_name") != WORKFLOW_NAME
            or row.get("status") != "completed"
            or row.get("conclusion") != "success"
            or row.get("url") != f"{API_ROOT}/actions/jobs/{check_id}"
            or row.get("run_url") != f"{API_ROOT}/actions/runs/{expected_run_id}"
            or row.get("check_run_url") != f"{API_ROOT}/check-runs/{check_id}"
        ):
            raise ValueError(f"GitHub CI identity or conclusion drift: {row.get('name')}")
        selected[row["name"]] = row
    if set(selected) != EXPECTED_CHECKS:
        raise ValueError("required GitHub CI check missing")
    projection = [
        {
            "name": name,
            "id": selected[name]["id"],
            "head_sha": expected_commit,
            "app_slug": "github-actions",
            "status": "completed",
            "conclusion": "success",
        }
        for name in sorted(EXPECTED_CHECKS)
    ]
    if len({row["id"] for row in projection}) != len(projection):
        raise ValueError("GitHub CI check IDs are not unique")
    return projection


def validate_commit_scope(
    payload: object, expected_commit: str, expected_parent: str
) -> str:
    if not isinstance(payload, dict) or payload.get("sha") != expected_commit:
        raise ValueError("GitHub pre-smoke commit response drift")
    parents = payload.get("parents")
    files = payload.get("files")
    if (
        not isinstance(parents, list)
        or len(parents) != 1
        or not isinstance(parents[0], dict)
        or parents[0].get("sha") != expected_parent
    ):
        raise ValueError("pre-smoke P must have exactly one environment parent E")
    if not isinstance(files, list) or len(files) != 1 or not isinstance(files[0], dict):
        raise ValueError("pre-smoke P changed-path scope is not exact")
    file_row = files[0]
    if (
        file_row.get("filename") != MANIFEST_REPOSITORY_PATH
        or file_row.get("status") not in {"added", "modified"}
        or "previous_filename" in file_row
    ):
        raise ValueError("pre-smoke P changed-path scope is not exact")
    commit = payload.get("commit")
    tree = commit.get("tree") if isinstance(commit, dict) else None
    if not isinstance(tree, dict) or OID.fullmatch(tree.get("sha", "")) is None:
        raise ValueError("GitHub pre-smoke commit tree missing")
    return tree["sha"]


def manifest_blob_oid(payload: object) -> str:
    if (
        not isinstance(payload, dict)
        or payload.get("truncated") is not False
        or not isinstance(payload.get("tree"), list)
    ):
        raise ValueError("GitHub recursive tree is malformed or truncated")
    rows = [
        row
        for row in payload["tree"]
        if isinstance(row, dict) and row.get("path") == MANIFEST_REPOSITORY_PATH
    ]
    if (
        len(rows) != 1
        or rows[0].get("type") != "blob"
        or OID.fullmatch(rows[0].get("sha", "")) is None
    ):
        raise ValueError("pre-smoke manifest blob is absent or ambiguous at GitHub master")
    return rows[0]["sha"]


def validate_blob(payload: object, expected_oid: str, deployed: bytes, expected_sha: str) -> None:
    if (
        not isinstance(payload, dict)
        or payload.get("sha") != expected_oid
        or payload.get("encoding") != "base64"
        or type(payload.get("size")) is not int
        or not isinstance(payload.get("content"), str)
    ):
        raise ValueError("GitHub pre-smoke manifest blob response is malformed")
    encoded = payload["content"].replace("\n", "").replace("\r", "")
    remote = base64.b64decode(encoded, validate=True)
    git_oid = hashlib.sha1(
        f"blob {len(remote)}\0".encode() + remote, usedforsecurity=False
    ).hexdigest()
    if (
        payload["size"] != len(remote)
        or git_oid != expected_oid
        or remote != deployed
        or hashlib.sha256(remote).hexdigest() != expected_sha
    ):
        raise ValueError("deployed pre-smoke manifest does not equal the GitHub P blob")


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
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
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
    expected_commit, expected_sha, manifest_text = sys.argv[1:]
    if OID.fullmatch(expected_commit) is None or SHA256.fullmatch(expected_sha) is None:
        raise SystemExit("independent pre-smoke commit or SHA-256 is malformed")
    deployed = stable_physical_bytes(Path(manifest_text))
    if hashlib.sha256(deployed).hexdigest() != expected_sha:
        raise SystemExit("independent pre-smoke manifest SHA-256 drift")
    manifest = strict_json_loads(deployed)
    git_provenance = manifest.get("git_provenance") if isinstance(manifest, dict) else None
    environment_parent = (
        git_provenance.get("head") if isinstance(git_provenance, dict) else None
    )
    if OID.fullmatch(environment_parent or "") is None:
        raise SystemExit("pre-smoke manifest does not bind environment parent E")
    validate_ref(github_json("/git/ref/heads/master"), expected_commit)
    workflow_runs_path = (
        f"/actions/workflows/{WORKFLOW_FILE}/runs?branch=master&event=push&"
        f"head_sha={expected_commit}&per_page={MAX_WORKFLOW_RUNS}&page=1"
    )
    workflow_run = validate_workflow_runs(
        github_json(workflow_runs_path),
        expected_commit,
    )
    ci_projection = validate_ci(
        github_json(
            f"/actions/runs/{workflow_run['id']}/attempts/"
            f"{workflow_run['run_attempt']}/jobs?per_page={MAX_JOBS}&page=1"
        ),
        expected_commit,
        workflow_run,
    )
    tree_oid = validate_commit_scope(
        github_json(f"/commits/{expected_commit}?per_page=100&page=1"),
        expected_commit,
        environment_parent,
    )
    blob_oid = manifest_blob_oid(github_json(f"/git/trees/{tree_oid}?recursive=1"))
    validate_blob(github_json(f"/git/blobs/{blob_oid}"), blob_oid, deployed, expected_sha)
    validate_ref(github_json("/git/ref/heads/master"), expected_commit)
    if validate_workflow_runs(
        github_json(workflow_runs_path),
        expected_commit,
    ) != workflow_run:
        raise ValueError("canonical GitHub workflow run changed during authority proof")
    validate_ref(github_json("/git/ref/heads/master"), expected_commit)
    print(
        expected_commit,
        environment_parent,
        *(str(row["id"]) for row in ci_projection),
    )


if __name__ == "__main__":
    main()
# END I135_GITHUB_SMOKE_AUTHORITY_PYTHON
PY
}

if ! [[ $EXPECTED_MANIFEST_COMMIT =~ ^[0-9a-f]{40}$ ]]; then
  fail_preflight "independent-manifest-commit-missing-or-malformed"
fi
GITHUB_PRE_SMOKE_BINDING=$(verify_github_pre_smoke_authority) \
  || fail_preflight "github-pre-smoke-publication-authority"
read -r GITHUB_PRE_SMOKE_COMMIT GITHUB_PRE_SMOKE_PARENT \
  GITHUB_PRE_SMOKE_CHECK_310_ID GITHUB_PRE_SMOKE_CHECK_311_ID \
  <<<"$GITHUB_PRE_SMOKE_BINDING"
if [ "$GITHUB_PRE_SMOKE_COMMIT" != "$EXPECTED_MANIFEST_COMMIT" ] \
  || ! [[ "$GITHUB_PRE_SMOKE_PARENT" =~ ^[0-9a-f]{40}$ \
    && "$GITHUB_PRE_SMOKE_CHECK_310_ID" =~ ^[1-9][0-9]*$ \
    && "$GITHUB_PRE_SMOKE_CHECK_311_ID" =~ ^[1-9][0-9]*$ ]] \
  || [ "$GITHUB_PRE_SMOKE_COMMIT" = "$GITHUB_PRE_SMOKE_PARENT" ] \
  || [ "$GITHUB_PRE_SMOKE_CHECK_310_ID" = "$GITHUB_PRE_SMOKE_CHECK_311_ID" ]; then
  fail_preflight "github-pre-smoke-publication-output"
fi

if [[ ! $EXPECTED_MANIFEST_SHA =~ ^[0-9a-f]{64}$ ]]; then
  fail_preflight "independent-manifest-sha256-missing-or-malformed"
fi
for path in "$MANIFEST_SOURCE" "$ENV_SOURCE" "$HOST_PACKET_SOURCE" \
  "$HOST_PREPARATION_SOURCE" "$MISSION_STATE_SOURCE" "$RUNNER_SOURCE" \
  "$VALIDATOR_SOURCE"; do
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
    or type(receipt.get("bytes")) is not int
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
  "$I135" "$ANALYTIC_OUTPUT_ROOT" "$SMOKE_OUTPUT_ROOT" "$DOCKER_FD_PATH" <<'PY'
import hashlib
import json
import os
import platform
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
    docker_binary,
) = map(Path, sys.argv[1:])
problems = []


def strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise SystemExit(f"duplicate authority JSON key: {key}")
        value[key] = item
    return value


def reject_nonfinite(value):
    raise SystemExit(f"non-finite authority JSON number: {value}")


def strict_load(path):
    return json.loads(
        path.read_text(),
        object_pairs_hook=strict_object,
        parse_constant=reject_nonfinite,
    )


manifest = strict_load(manifest_path)
environment = strict_load(environment_path)
mission_state = strict_load(mission_state_path)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def exact_json_value(observed, expected):
    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        return set(observed) == set(expected) and all(
            exact_json_value(observed[key], expected[key]) for key in expected
        )
    if type(expected) is list:
        return len(observed) == len(expected) and all(
            exact_json_value(observed_item, expected_item)
            for observed_item, expected_item in zip(observed, expected, strict=True)
        )
    return observed == expected


if manifest.get("schema") != "iter135.launch_manifest.v2":
    problems.append("manifest-schema")
if manifest.get("verdict") != "I135_TOOLING_MANIFEST_INCOMPLETE":
    problems.append("manifest-verdict")
if manifest.get("launch_authorized") is not False:
    problems.append("manifest-already-analytic")
if not exact_json_value(
    manifest.get("missing_artifacts"),
    ["smoke-evidence/smoke_receipt.json"],
):
    problems.append("manifest-missing-set")
if (
    type(manifest.get("problem_count")) is not int
    or manifest.get("problem_count") != 1
    or not exact_json_value(manifest.get("problems"), ["smoke:receipt-missing"])
):
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
if manifest.get("mission_phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED":
    problems.append("manifest-mission-phase")
if (
    type(manifest.get("planned_blocks")) is not int
    or manifest.get("planned_blocks") != 120
    or type(manifest.get("planned_episodes")) is not int
    or manifest.get("planned_episodes") != 2400
):
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
if not exact_json_value(manifest.get("gates"), expected_gates):
    problems.append("manifest-pre-smoke-gate-contract")

expected_authorized_actions = [
    (
        "prepare the exact hash-bound sentinel-gpu host contract and atomically commit "
        "host_packet_manifest.json and host_preparation_receipt.json"
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
    (
        "validate, collect, and commit the exact nonanalytic smoke raw evidence, recomputed "
        "receipt, and mechanically generated SMOKE.md"
    ),
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
    or not exact_json_value(
        mission_state.get("workspace_boundary"),
        expected_workspace_boundary,
    )
    or mission_state.get("trunk") != "master"
    or type(mission_state.get("current_completed_iteration")) is not int
    or mission_state.get("current_completed_iteration") != 134
    or mission_state.get("current_result")
    != "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
    or mission_state.get("current_verdict") != "PLACEBO_HARM_OR_NULL"
    or mission_state.get("run_state") != "IDLE"
    or mission_state.get("active_hypothesis")
    != "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
    or not exact_json_value(mission_state.get("next_program"), expected_program)
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
if not exact_json_value(
    mission_state.get("storage_gate"),
    expected_state_storage,
):
    problems.append("mission-state-storage-contract")
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
if not all(
    (
        exact_json_value(mission_state.get("claim_state"), expected_claim_state),
        exact_json_value(
            mission_state.get("deprecated_pending_hypotheses"),
            expected_deprecated,
        ),
        exact_json_value(mission_state.get("paper_state"), expected_paper_state),
    )
):
    problems.append("mission-state-claim-paper-contract")
mission_receipt = manifest.get("mission_state")
mission_payload = mission_state_path.read_bytes()
if not exact_json_value(
    mission_receipt,
    {
        "source_path": "MISSION_STATE.json",
        "sha256": hashlib.sha256(mission_payload).hexdigest(),
        "bytes": len(mission_payload),
    },
):
    problems.append("mission-state-receipt-drift")

bound = manifest.get("hash_bound_files")
required = {
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
    "patch_compose_dose_env.py",
    "make_launch_manifest.py",
    "env_receipts.json",
    "host_packet_manifest.json",
    "host_preparation_receipt.json",
    "tooling_verification_receipt.json",
}
# BEGIN I135_PRE_SMOKE_BOUND_CONTRACT_PYTHON
def strict_bound_json_loads(payload):
    import json

    def strict_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate authority JSON key: {key}")
            value[key] = item
        return value

    def reject_nonfinite(value):
        raise ValueError(f"non-finite authority JSON number: {value}")

    return json.loads(
        payload,
        object_pairs_hook=strict_object,
        parse_constant=reject_nonfinite,
    )


def exact_json_value(observed, expected):
    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        return set(observed) == set(expected) and all(
            exact_json_value(observed[key], expected[key]) for key in expected
        )
    if type(expected) is list:
        return len(observed) == len(expected) and all(
            exact_json_value(observed_item, expected_item)
            for observed_item, expected_item in zip(observed, expected, strict=True)
        )
    return observed == expected


def load_strict_bound_json(path, receipt, expected_source_path):
    payload = path.read_bytes()
    expected_receipt = {
        "source_path": expected_source_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    if not exact_json_value(receipt, expected_receipt):
        raise ValueError("bound authority JSON payload drift")
    return strict_bound_json_loads(payload), payload


def bound_payload_receipt_matches(
    payload,
    bound_receipt,
    manifest_receipt,
    expected_source_path,
):
    expected_receipt = {
        "source_path": expected_source_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    return exact_json_value(bound_receipt, expected_receipt) and exact_json_value(
        manifest_receipt,
        expected_receipt,
    )


def zero_problem_receipt_metadata_matches(document, schema, verdict):
    return (
        type(document) is dict
        and exact_json_value(document.get("schema"), schema)
        and exact_json_value(document.get("verdict"), verdict)
        and type(document.get("problem_count")) is int
        and document.get("problem_count") == 0
        and exact_json_value(document.get("problems"), [])
    )


SMOKE_DOSES = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
SMOKE_SCHEDULE_ROW_FIELDS = {
    "brake_frames",
    "donor_brake_frames",
    "donor_class",
    "donor_frame_count",
    "donor_run",
    "donor_seq",
    "dose_id",
    "scheduled_brake_count",
    "target_class",
    "target_run",
    "target_seq",
}


def validate_smoke_schedule(schedule):
    schedule_problems = []
    targets = []
    if not zero_problem_receipt_metadata_matches(
        schedule,
        "iter135.nested_dose_schedules.v1",
        "NESTED_DOSE_SCHEDULES_OK",
    ):
        schedule_problems.append("schedule:metadata")
        return schedule_problems, targets
    schedules = schedule.get("schedules")
    if type(schedules) is not dict or set(schedules) != set(SMOKE_DOSES):
        schedule_problems.append("schedule-dose-set")
        return schedule_problems, targets
    if (
        type(schedule.get("schedule_count")) is not int
        or schedule.get("schedule_count")
        != sum(len(rows) for rows in schedules.values() if type(rows) is dict)
    ):
        schedule_problems.append("schedule-count")
    for dose in SMOKE_DOSES:
        rows = schedules.get(dose)
        if type(rows) is not dict:
            schedule_problems.append(f"schedule:{dose}:rows")
            continue
        candidate_keys = sorted(
            key
            for key in rows
            if type(key) is str
            and len(key.split("/")) == 3
            and all(key.split("/")[:2])
            and key.split("/")[2] == "0"
        )
        if not candidate_keys:
            schedule_problems.append(f"schedule:{dose}:canonical-run-zero")
            continue
        target = candidate_keys[0]
        row = rows[target]
        scenario_class, sequence, run_text = target.split("/")
        if type(row) is not dict or set(row) != SMOKE_SCHEDULE_ROW_FIELDS:
            schedule_problems.append(f"schedule:{dose}:row-contract")
            continue
        brake_frames = row.get("brake_frames")
        donor_brake_frames = row.get("donor_brake_frames")
        donor_frame_count = row.get("donor_frame_count")
        if (
            not exact_json_value(row.get("dose_id"), dose)
            or not exact_json_value(row.get("target_class"), scenario_class)
            or not exact_json_value(row.get("target_seq"), sequence)
            or type(row.get("target_run")) is not int
            or row.get("target_run") != int(run_text)
        ):
            schedule_problems.append(f"schedule:{dose}:identity")
        if (
            not exact_json_value(row.get("donor_class"), scenario_class)
            or type(row.get("donor_seq")) is not str
            or not row.get("donor_seq")
            or row.get("donor_seq") == sequence
            or type(row.get("donor_run")) is not int
            or row.get("donor_run") < 0
            or row.get("donor_run") >= 20
            or row.get("donor_run") == row.get("target_run")
        ):
            schedule_problems.append(f"schedule:{dose}:donor-identity")
        if (
            type(donor_frame_count) is not int
            or donor_frame_count <= 0
            or type(donor_brake_frames) is not list
            or any(type(frame) is not int for frame in donor_brake_frames)
            or donor_brake_frames != sorted(set(donor_brake_frames))
            or any(
                frame < 0 or frame >= donor_frame_count
                for frame in donor_brake_frames
                if type(frame) is int
            )
        ):
            schedule_problems.append(f"schedule:{dose}:donor-frames")
        if (
            type(brake_frames) is not list
            or not brake_frames
            or any(type(frame) is not int for frame in brake_frames)
            or brake_frames != sorted(set(brake_frames))
            or any(
                frame < 0 or frame >= donor_frame_count
                for frame in brake_frames
                if type(frame) is int and type(donor_frame_count) is int
            )
            or type(row.get("scheduled_brake_count")) is not int
            or row.get("scheduled_brake_count") != len(brake_frames)
        ):
            schedule_problems.append(f"schedule:{dose}:brake-frames")
        targets.append((dose, f"{dose}/{target}", scenario_class, sequence))
    return schedule_problems, targets


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
    "TZ": "UTC",
}
HOST_STORAGE_FIELDS = {
    "mount_target",
    "mount_source",
    "mount_fstype",
    "mount_uuid",
    "dataset_st_dev",
    "root_st_dev",
    "free_bytes_before",
    "free_bytes_after",
    "minimum_remote_free_bytes",
    "projected_output_bytes",
    "minimum_reserve_bytes",
    "analytic_root",
    "analytic_root_realpath",
    "analytic_root_is_symlink",
    "analytic_root_empty",
    "analytic_root_st_dev",
}


def validate_remote_artifact_contract(artifacts):
    problems = []
    if type(artifacts) is not list or len(artifacts) != 82:
        return ["remote-artifacts:cardinality"], {}
    by_role = {}
    for index, row in enumerate(artifacts):
        if type(row) is not dict or set(row) != {"role", "path", "sha256", "bytes"}:
            problems.append(f"remote-artifacts:row:{index}:field-set")
            continue
        role = row.get("role")
        path = row.get("path")
        sha256 = row.get("sha256")
        byte_count = row.get("bytes")
        if (
            type(role) is not str
            or not role
            or role in by_role
            or type(path) is not str
            or not Path(path).is_absolute()
            or type(sha256) is not str
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
            or type(byte_count) is not int
            or byte_count <= 0
        ):
            problems.append(f"remote-artifacts:row:{index}:contract")
            continue
        by_role[role] = row
    if (
        len(by_role) != 82
        or sum(role.startswith("scenario:") for role in by_role) != 20
        or sum(role.startswith("renderer:") for role in by_role) != 42
        or "uniad_server_baseline" not in by_role
    ):
        problems.append("remote-artifacts:role-set")
    return sorted(set(problems)), by_role


def validate_receipt_sidecar_topology(experiment_path):
    """Validate producer-owned disk commit state, never producer process return."""

    root = Path(experiment_path).absolute()
    problems = []
    if root.is_symlink() or not root.is_dir() or root.resolve(strict=True) != root:
        return ["receipt-topology:root"]
    contracts = (
        (
            "host",
            "host_preparation_receipt.json",
            "host_preparation_receipt.json.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE",
            "host_preparation_receipt.json.PENDING_RECEIPT_NONAUTHORITATIVE",
        ),
        (
            "environment",
            "env_receipts.json",
            ".env_receipts.json.ATTEMPT_IN_PROGRESS_NONAUTHORITATIVE",
            ".env_receipts.json.PENDING_RECEIPT_NONAUTHORITATIVE",
        ),
    )
    for label, canonical_name, marker_name, pending_name in contracts:
        canonical = root / canonical_name
        marker = root / marker_name
        pending = root / pending_name
        if marker.exists() or marker.is_symlink():
            problems.append(f"receipt-topology:{label}:attempt-marker")
        try:
            if (
                canonical.is_symlink()
                or pending.is_symlink()
                or not canonical.is_file()
                or not pending.is_file()
                or canonical.resolve(strict=True) != canonical
                or pending.resolve(strict=True) != pending
            ):
                raise OSError("nonphysical receipt leaf")
            canonical_before = canonical.stat(follow_symlinks=False)
            pending_before = pending.stat(follow_symlinks=False)
            canonical_payload = canonical.read_bytes()
            pending_payload = pending.read_bytes()
            canonical_after = canonical.stat(follow_symlinks=False)
            pending_after = pending.stat(follow_symlinks=False)
        except OSError:
            problems.append(f"receipt-topology:{label}:receipt-pair")
            continue
        identity = lambda row: (
            row.st_dev,
            row.st_ino,
            row.st_mode,
            row.st_size,
            row.st_mtime_ns,
            row.st_ctime_ns,
        )
        if (
            identity(canonical_before) != identity(canonical_after)
            or identity(pending_before) != identity(pending_after)
            or canonical_before.st_dev != pending_before.st_dev
            or canonical_before.st_ino != pending_before.st_ino
            or canonical_before.st_nlink != 2
            or pending_before.st_nlink != 2
            or canonical_before.st_mode & 0o7777 != 0o444
            or pending_before.st_mode & 0o7777 != 0o444
            or len(canonical_payload) != canonical_before.st_size
            or canonical_payload != pending_payload
        ):
            problems.append(f"receipt-topology:{label}:receipt-pair")
    return sorted(set(problems))


def validate_host_runtime_contract(host):
    problems = []
    if not isinstance(host, dict):
        return ["host-runtime:type"]
    packet = host.get("packet")
    packet_files = packet.get("files") if isinstance(packet, dict) else None
    compose = host.get("compose")
    if (
        not isinstance(compose, dict)
        or set(compose) != {"patcher", "before", "after"}
        or not isinstance(packet_files, dict)
        or not exact_json_value(
            compose.get("patcher"),
            packet_files.get("patch_compose_dose_env.py"),
        )
    ):
        problems.append("host-runtime:compose")
    else:
        compose_contracts = (
            (
                "before",
                "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d",
                3_380,
            ),
            (
                "after",
                "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada",
                3_613,
            ),
        )
        for label, expected_sha, expected_bytes in compose_contracts:
            row = compose.get(label)
            if (
                not isinstance(row, dict)
                or set(row) != {"path", "sha256", "bytes", "mode"}
                or row.get("path")
                != "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh"
                or row.get("sha256") != expected_sha
                or type(row.get("bytes")) is not int
                or row.get("bytes") != expected_bytes
                or type(row.get("mode")) is not int
                or row.get("mode") not in (0o644, 0o755)
            ):
                problems.append(f"host-runtime:compose-{label}")
    storage = host.get("storage")
    if not isinstance(storage, dict) or set(storage) != HOST_STORAGE_FIELDS:
        problems.append("host-runtime:storage-schema")
        storage = {}
    integer_fields = (
        "dataset_st_dev",
        "root_st_dev",
        "free_bytes_before",
        "free_bytes_after",
        "minimum_remote_free_bytes",
        "projected_output_bytes",
        "minimum_reserve_bytes",
        "analytic_root_st_dev",
    )
    if (
        any(type(storage.get(field)) is not int for field in integer_fields)
        or storage.get("mount_target") != "/datasets/nuscenes-full"
        or storage.get("mount_source") != "/dev/nvme0n2"
        or storage.get("mount_fstype") != "ext4"
        or storage.get("mount_uuid") != "9a98277e-b21f-4ffc-8f14-3f2235b43103"
        or storage.get("minimum_remote_free_bytes") != 100 * 1024**3
        or storage.get("projected_output_bytes") != 72_380_432_384
        or storage.get("minimum_reserve_bytes") != 25 * 1024**3
        or min(
            storage.get("dataset_st_dev"),
            storage.get("root_st_dev"),
            storage.get("analytic_root_st_dev"),
        )
        < 0
        or storage.get("dataset_st_dev") == storage.get("root_st_dev")
        or storage.get("analytic_root_st_dev") != storage.get("dataset_st_dev")
        or storage.get("analytic_root")
        != "/datasets/nuscenes-full/sentinel-i135-outoutput"
        or storage.get("analytic_root_realpath")
        != "/datasets/nuscenes-full/sentinel-i135-outoutput"
        or storage.get("analytic_root_is_symlink") is not False
        or storage.get("analytic_root_empty") is not True
    ):
        problems.append("host-runtime:storage")
    elif (
        storage["free_bytes_before"] < storage["minimum_remote_free_bytes"]
        or storage["free_bytes_after"] < storage["minimum_remote_free_bytes"]
        or min(storage["free_bytes_before"], storage["free_bytes_after"])
        - storage["projected_output_bytes"]
        < storage["minimum_reserve_bytes"]
    ):
        problems.append("host-runtime:storage")
    actions = host.get("actions")
    action_contracts = (
        (
            "normalize_uniad_server_from_verified_head_blob",
            {"action", "performed", "before", "after"},
        ),
        (
            "atomically_patch_compose_from_exact_preimage",
            {"action", "performed", "before_sha256", "after_sha256"},
        ),
        (
            "create_absent_empty_analytic_root",
            {"action", "performed", "path"},
        ),
        (
            "atomically_install_verified_packet",
            {"action", "performed", "from", "to"},
        ),
    )
    if not isinstance(actions, list) or len(actions) != len(action_contracts):
        problems.append("host-runtime:actions")
        actions = []
    if actions and all(isinstance(row, dict) for row in actions):
        for row, (name, fields) in zip(actions, action_contracts, strict=True):
            if (
                not isinstance(row, dict)
                or set(row) != fields
                or row.get("action") != name
                or type(row.get("performed")) is not bool
            ):
                problems.append("host-runtime:actions")
        normalize = actions[0]
        before_server = normalize.get("before") if isinstance(normalize, dict) else None
        after_server = normalize.get("after") if isinstance(normalize, dict) else None
        for row in (before_server, after_server):
            if (
                not isinstance(row, dict)
                or set(row) != {"path", "sha256", "bytes", "mode"}
                or row.get("path") != "/opt/sentinel-stack/UniAD/inference/server.py"
                or not isinstance(row.get("sha256"), str)
                or len(row["sha256"]) != 64
                or any(character not in "0123456789abcdef" for character in row["sha256"])
                or type(row.get("bytes")) is not int
                or row["bytes"] <= 0
                or type(row.get("mode")) is not int
                or row["mode"] not in (0o644, 0o755)
            ):
                problems.append("host-runtime:actions")
        if isinstance(after_server, dict) and (
            after_server.get("sha256")
            != "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424"
            or after_server.get("bytes") != 4_519
        ):
            problems.append("host-runtime:actions")
        if isinstance(before_server, dict) and isinstance(after_server, dict):
            expected_normalization = (
                before_server.get("sha256") != after_server.get("sha256")
            )
            if normalize.get("performed") is not expected_normalization:
                problems.append("host-runtime:actions")
        if (
            actions[1].get("performed") is not True
            or actions[1].get("before_sha256")
            != (
                compose.get("before", {}).get("sha256")
                if isinstance(compose, dict) and isinstance(compose.get("before"), dict)
                else None
            )
            or actions[1].get("after_sha256")
            != (
                compose.get("after", {}).get("sha256")
                if isinstance(compose, dict) and isinstance(compose.get("after"), dict)
                else None
            )
            or actions[2].get("performed") is not True
            or actions[2].get("path") != storage.get("analytic_root")
            or actions[3].get("performed") is not True
            or actions[3].get("from") != "/opt/sentinel-stack/.iter135-packet"
            or actions[3].get("to") != "/opt/sentinel-stack/iter135"
        ):
            problems.append("host-runtime:actions")
    elif actions:
        problems.append("host-runtime:actions")
    invocation = host.get("invocation")
    if (
        not isinstance(invocation, dict)
        or set(invocation)
        != {
            "environment",
            "environment_matches",
            "isolated",
            "python_implementation",
            "python_version",
        }
        or not exact_json_value(invocation.get("environment"), HOST_SAFE_ENVIRONMENT)
        or invocation.get("environment_matches") is not True
        or invocation.get("isolated") is not True
        or invocation.get("python_implementation") != "CPython"
        or not isinstance(invocation.get("python_version"), str)
        or len(invocation["python_version"].split(".")) != 3
        or any(not field.isdigit() for field in invocation["python_version"].split("."))
    ):
        problems.append("host-runtime:invocation")
    return sorted(set(problems))


def validate_pre_smoke_bound_contract(bound, experiment_path, required):
    contract_problems = []
    if not isinstance(bound, dict) or set(bound) != required:
        return ["manifest-required-tooling-set"], {}
    canonical_root = "experiments/iter135_neuroncap_blind_braking_dose_response"
    for relative, receipt in sorted(bound.items()):
        path = experiment_path / relative
        if (
            path.is_symlink()
            or not path.is_file()
            or path.resolve(strict=True) != path.absolute()
            or not isinstance(receipt, dict)
            or set(receipt) != {"source_path", "sha256", "bytes"}
        ):
            contract_problems.append(f"bound-file:{relative}:contract")
            continue
        expected_source_path = f"{canonical_root}/{relative}"
        payload = path.read_bytes()
        expected_receipt = {
            "source_path": expected_source_path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
        if receipt.get("source_path") != expected_source_path:
            contract_problems.append(f"bound-file:{relative}:source-path")
        if not exact_json_value(receipt, expected_receipt):
            contract_problems.append(f"bound-file:{relative}:drift")
    return contract_problems, bound
# END I135_PRE_SMOKE_BOUND_CONTRACT_PYTHON


bound_problems, bound = validate_pre_smoke_bound_contract(bound, experiment_path, required)
problems.extend(bound_problems)
remote_artifact_problems, _remote_artifacts_by_role = validate_remote_artifact_contract(
    manifest.get("remote_artifacts")
)
problems.extend(remote_artifact_problems)
problems.extend(validate_receipt_sidecar_topology(experiment_path))

environment_bound = bound.get("env_receipts.json")
if not isinstance(environment_bound, dict) or environment_bound.get("sha256") != digest(environment_path):
    problems.append("environment-bound-hash")
host_packet_path = experiment_path / "host_packet_manifest.json"
host_preparation_path = experiment_path / "host_preparation_receipt.json"
host_packet_bound = bound.get("host_packet_manifest.json")
host_preparation_bound = bound.get("host_preparation_receipt.json")
try:
    host_packet_payload = host_packet_path.read_bytes()
    host_preparation_payload = host_preparation_path.read_bytes()
    host_packet = strict_bound_json_loads(host_packet_payload)
    host_preparation = strict_bound_json_loads(host_preparation_payload)
except (OSError, ValueError) as error:
    problems.append(f"host-contract-read:{type(error).__name__}")
    host_packet_payload = b""
    host_preparation_payload = b""
    host_packet = {}
    host_preparation = {}
if not bound_payload_receipt_matches(
    host_packet_payload,
    host_packet_bound,
    manifest.get("host_packet_manifest"),
    (
        "experiments/iter135_neuroncap_blind_braking_dose_response/"
        "host_packet_manifest.json"
    ),
):
    problems.append("host-packet-manifest-binding")
if not bound_payload_receipt_matches(
    host_preparation_payload,
    host_preparation_bound,
    manifest.get("host_preparation_receipt"),
    (
        "experiments/iter135_neuroncap_blind_braking_dose_response/"
        "host_preparation_receipt.json"
    ),
):
    problems.append("host-preparation-receipt-binding")
if (
    not isinstance(host_packet, dict)
    or set(host_packet) != {"schema", "source_commit", "files"}
    or host_packet.get("schema") != "iter135.host_packet_manifest.v1"
    or not isinstance(host_packet.get("source_commit"), str)
    or len(host_packet["source_commit"]) != 40
    or any(character not in "0123456789abcdef" for character in host_packet["source_commit"])
    or not isinstance(host_packet.get("files"), dict)
    or not host_packet["files"]
):
    problems.append("host-packet-manifest-contract")
host_payload_without_hash = dict(host_preparation) if isinstance(host_preparation, dict) else {}
claimed_host_payload_sha = host_payload_without_hash.pop("receipt_payload_sha256", None)
actual_host_payload_sha = hashlib.sha256(
    json.dumps(
        host_payload_without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()
).hexdigest()
host_packet_evidence = host_preparation.get("packet") if isinstance(host_preparation, dict) else None
if (
    not zero_problem_receipt_metadata_matches(
        host_preparation,
        "iter135.host_preparation_receipt.v1",
        "I135_HOST_PREPARATION_OK",
    )
    or claimed_host_payload_sha != actual_host_payload_sha
    or host_preparation.get("packet_manifest_sha256")
    != hashlib.sha256(host_packet_payload).hexdigest()
    or not isinstance(host_packet_evidence, dict)
    or host_packet_evidence.get("independently_supplied_manifest_sha256")
    != hashlib.sha256(host_packet_payload).hexdigest()
    or host_packet_evidence.get("source_commit") != host_packet.get("source_commit")
    or host_preparation.get("controller")
    != host_packet_evidence.get("files", {}).get("prepare_host135.py")
):
    problems.append("host-preparation-receipt-contract")
problems.extend(validate_host_runtime_contract(host_preparation))
tooling_path = experiment_path / "tooling_verification_receipt.json"
tooling_bound = bound.get("tooling_verification_receipt.json")
try:
    tooling_payload_bytes = tooling_path.read_bytes()
    tooling = strict_bound_json_loads(tooling_payload_bytes)
except (OSError, ValueError) as error:
    problems.append(f"tooling-receipt-read:{type(error).__name__}")
    tooling_payload_bytes = b""
    tooling = {}
if not bound_payload_receipt_matches(
    tooling_payload_bytes,
    tooling_bound,
    manifest.get("tooling_verification_receipt"),
    (
        "experiments/iter135_neuroncap_blind_braking_dose_response/"
        "tooling_verification_receipt.json"
    ),
):
    problems.append("tooling-receipt-binding")
tooling_payload = dict(tooling)
claimed_tooling_payload_sha = tooling_payload.pop("receipt_payload_sha256", None)
actual_tooling_payload_sha = hashlib.sha256(
    json.dumps(tooling_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
).hexdigest()
if (
    not zero_problem_receipt_metadata_matches(
        tooling,
        "iter135.tooling_verification.v2",
        "I135_TOOLING_VERIFICATION_OK",
    )
    or claimed_tooling_payload_sha != actual_tooling_payload_sha
):
    problems.append("tooling-receipt-contract")
if environment.get("schema") != "iter135.environment_receipts.v3":
    problems.append("environment-schema")
if environment.get("verdict") != "I135_ENVIRONMENT_PREFLIGHT_OK":
    problems.append("environment-verdict")
if (
    type(environment.get("problem_count")) is not int
    or environment.get("problem_count") != 0
    or not exact_json_value(environment.get("problems"), [])
):
    problems.append("environment-problem-metadata")
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
}
if set(environment) != expected_environment_fields:
    problems.append("environment-field-set")
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
    or interpreter.get("sha256") != digest(live_interpreter)
    or type(interpreter.get("bytes")) is not int
    or interpreter.get("bytes") != live_interpreter.stat().st_size
    or interpreter.get("version") != platform.python_version()
    or interpreter.get("implementation") != platform.python_implementation()
    or sys.flags.isolated != 1
):
    problems.append("environment-interpreter-contract")
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
    or set(invocation) != {"sanitized", "isolated", "environment", "argv", "canonical_script"}
    or invocation.get("sanitized") is not True
    or invocation.get("isolated") is not True
    or not exact_json_value(
        invocation.get("environment"),
        expected_capture_environment,
    )
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
    problems.append("environment-invocation-contract")
environment_preparation = environment.get("host_preparation")
expected_preparation_file = {
    "path": "/opt/sentinel-stack/iter135/host_preparation_receipt.json",
    "sha256": hashlib.sha256(host_preparation_payload).hexdigest(),
    "bytes": len(host_preparation_payload),
}
if (
    not isinstance(environment_preparation, dict)
    or set(environment_preparation) != {"receipt_file", "evidence"}
    or not exact_json_value(
        environment_preparation.get("receipt_file"),
        expected_preparation_file,
    )
    or not exact_json_value(
        environment_preparation.get("evidence"),
        host_preparation,
    )
):
    problems.append("environment-host-preparation-contract")
if environment.get("host") != "sentinel-gpu" or socket.gethostname() != "sentinel-gpu":
    problems.append(f"environment-live-host:{socket.gethostname()}")
expected_gpu = {
    "model": "NVIDIA L4",
    "count": 1,
    "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
    "driver_version": "580.159.03",
    "memory_total_mib": 23034,
}
if not exact_json_value(environment.get("gpu"), expected_gpu):
    problems.append("environment-frozen-gpu")
expected_box = {
    "idle": True,
    "all_containers": 0,
    "gpu_compute_processes": 0,
    "known_evaluation_processes": 0,
}
if not exact_json_value(environment.get("box"), expected_box):
    problems.append("environment-box-contract")
runtime_snapshots = environment.get("runtime_snapshots")
if (
    not isinstance(runtime_snapshots, dict)
    or set(runtime_snapshots) != {"before_dataset_hashing", "after_dataset_hashing"}
    or any(
        not isinstance(runtime_snapshots.get(phase), dict)
        or set(runtime_snapshots[phase]) != {"gpu", "box"}
        or not exact_json_value(runtime_snapshots[phase].get("gpu"), expected_gpu)
        or not exact_json_value(runtime_snapshots[phase].get("box"), expected_box)
        for phase in ("before_dataset_hashing", "after_dataset_hashing")
    )
):
    problems.append("environment-runtime-snapshots-contract")

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
        or type(manifest_tool_receipt.get("bytes")) is not int
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
    or namespace.get("EXPECTED_ENV_SCHEMA") != "iter135.environment_receipts.v3"
    or namespace.get("EXPECTED_DATASET_SCHEMA") != "iter135.nuscenes_dataset_receipt.v1"
    or namespace.get("EXPECTED_DATASET_CONTRACT_SHA256")
    != "f61363c91fa6e0f3db24a6df2e32afc16ad02ebc44e3c4af66132fcc317760c2"
):
    problems.append("dataset-validator-frozen-constant-drift")
if not exact_json_value(manifest.get("dataset_receipt"), dataset):
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
            if (
                type(receipt.get("bytes")) is not int
                or path.stat().st_size != receipt.get("bytes")
            ):
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
if not exact_json_value(manifest_environment, expected_manifest_environment):
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
if any(
    not exact_json_value(manifest_storage.get(key), value)
    for key, value in expected_manifest_storage_values.items()
):
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
    if (
        type(receipt.get("bytes")) is not int
        or receipt.get("bytes") != path.stat().st_size
        or receipt.get("sha256") != digest(path)
    ):
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
    elif repository_id == "uniad":
        # Exactly one untracked entry is contractual: the load-bearing `checkpoints`
        # symlink resolving the tracked config's motion anchors into `ckpts`.
        if untracked != ["checkpoints"]:
            problems.append(
                f"repository:{repository_id}:unexpected-untracked:"
                f"expected=['checkpoints']:actual={untracked}"
            )
        checkpoints_link = path / "checkpoints"
        try:
            link_target = str(checkpoints_link.readlink())
        except OSError:
            link_target = None
        if not checkpoints_link.is_symlink() or link_target != "ckpts":
            problems.append(f"repository:{repository_id}:checkpoints-symlink")
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
            [str(docker_binary), "image", "inspect", name, "--format", "{{.Id}}"], text=True
        ).strip()
        id_actual = subprocess.check_output(
            [str(docker_binary), "image", "inspect", expected_id, "--format", "{{.Id}}"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        problems.append(f"image:{name}:missing")
        continue
    if tag_actual != expected_id or id_actual != expected_id:
        problems.append(f"image:{name}:drift")

schedule_path = experiment_path / "dose_schedules.json"
try:
    schedule, schedule_payload = load_strict_bound_json(
        schedule_path,
        bound.get("dose_schedules.json"),
        (
            "experiments/iter135_neuroncap_blind_braking_dose_response/"
            "dose_schedules.json"
        ),
    )
except (OSError, ValueError) as error:
    problems.append(f"schedule-read:{type(error).__name__}")
    schedule = {}
    schedule_payload = b""
schedule_problems, targets = validate_smoke_schedule(schedule)
problems.extend(schedule_problems)

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

# Terminal remote authority check: it is deliberately the last network observation and occurs
# immediately before publishing the irreversible one-shot lock.
verify_python_interpreter_binding || fail_preflight "python-interpreter-terminal-drift"
verify_docker_client_binding || fail_preflight "docker-client-terminal-drift"
[ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_SHA" ] \
  || fail_preflight "docker-v3-runtime-terminal-drift"
TERMINAL_GITHUB_PRE_SMOKE_BINDING=$(verify_github_pre_smoke_authority) \
  || fail_preflight "github-pre-smoke-terminal-authority"
read -r TERMINAL_GITHUB_PRE_SMOKE_COMMIT TERMINAL_GITHUB_PRE_SMOKE_PARENT \
  TERMINAL_GITHUB_PRE_SMOKE_CHECK_310_ID TERMINAL_GITHUB_PRE_SMOKE_CHECK_311_ID \
  <<<"$TERMINAL_GITHUB_PRE_SMOKE_BINDING"
if [ "$TERMINAL_GITHUB_PRE_SMOKE_COMMIT" != "$EXPECTED_MANIFEST_COMMIT" ] \
  || ! [[ "$TERMINAL_GITHUB_PRE_SMOKE_PARENT" =~ ^[0-9a-f]{40}$ \
    && "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_310_ID" =~ ^[1-9][0-9]*$ \
    && "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_311_ID" =~ ^[1-9][0-9]*$ ]] \
  || [ "$TERMINAL_GITHUB_PRE_SMOKE_COMMIT" = "$TERMINAL_GITHUB_PRE_SMOKE_PARENT" ] \
  || [ "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_310_ID" \
    = "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_311_ID" ]; then
  fail_preflight "github-pre-smoke-terminal-output"
fi

# Crossing this point is the explicit one-shot smoke launch.  The fixed lock and output paths are
# deliberately retained on both success and failure so a second attempt requires a disclosed,
# manual forensic action.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0=$STACK/UniAD
SMOKE_LOCK_ID=$(python3 - "$LOCK" "$EXPECTED_MANIFEST_SHA" "$RUNNER_SHA" \
  "$MISSION_STATE_SOURCE" "$MANIFEST_SOURCE" "$RUNNER_SOURCE" \
  "$TERMINAL_GITHUB_PRE_SMOKE_COMMIT" "$TERMINAL_GITHUB_PRE_SMOKE_PARENT" \
  "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_310_ID" \
  "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_311_ID" "$$" <<'PY'
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
pre_smoke_commit = sys.argv[7]
environment_parent = sys.argv[8]
check_310_id = int(sys.argv[9])
check_311_id = int(sys.argv[10])
pid = int(sys.argv[11])
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
    or len(pre_smoke_commit) != 40
    or any(character not in "0123456789abcdef" for character in pre_smoke_commit)
    or len(environment_parent) != 40
    or any(character not in "0123456789abcdef" for character in environment_parent)
    or pre_smoke_commit == environment_parent
    or check_310_id <= 0
    or check_311_id <= 0
    or check_310_id == check_311_id
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
authority = {
    "schema": "iter135.github_pre_smoke_authority.v1",
    "repository": "manfromnowhere143/sentinel",
    "branch": "master",
    "pre_smoke_commit": pre_smoke_commit,
    "environment_parent": environment_parent,
    "manifest_sha256": manifest_sha256,
    "checks": [
        {
            "name": "check (3.10)",
            "id": check_310_id,
            "head_sha": pre_smoke_commit,
            "app_slug": "github-actions",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "name": "check (3.11)",
            "id": check_311_id,
            "head_sha": pre_smoke_commit,
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
    "schema": "iter135.smoke_lock.v2",
    "manifest_sha256": manifest_sha256,
    "runner_sha256": runner_sha256,
    "mission_state_sha256": hashlib.sha256(mission_state_payload).hexdigest(),
    "github_pre_smoke_authority": authority,
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
SMOKE_LOCK_SHA=$(sha256sum "$LOCK" | awk '{print $1}') \
  || fail_preflight "persistent-smoke-lock-sha256"
[[ $SMOKE_LOCK_SHA =~ ^[0-9a-f]{64}$ ]] \
  || fail_preflight "persistent-smoke-lock-sha256-output"
readonly SMOKE_LOCK_SHA
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
  verify_docker_client_binding || return 1
  [ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_SHA" ] || return 1
  python3 - "$ENV_SOURCE" "$MANIFEST_SOURCE" "$LOCK" "$SMOKE_LOCK_ID" \
    "$EXPECTED_MANIFEST_SHA" "$RUNNER_SHA" "$RUNNER_SOURCE" "$RUNNER_ID" \
    "$MISSION_STATE_SOURCE" "$SMOKE_LOCK_SHA" \
    "$TERMINAL_GITHUB_PRE_SMOKE_COMMIT" "$TERMINAL_GITHUB_PRE_SMOKE_PARENT" \
    "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_310_ID" \
    "$TERMINAL_GITHUB_PRE_SMOKE_CHECK_311_ID" "$$" <<'PY'
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
    expected_lock_sha,
    expected_pre_smoke_commit,
    expected_environment_parent,
    expected_check_310_id,
    expected_check_311_id,
    expected_pid_text,
) = sys.argv[1:]
expected_check_ids = [int(expected_check_310_id), int(expected_check_311_id)]
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
lock_payload = lock.read_bytes()
payload = json.loads(lock_payload)
expected_fields = {
    "schema",
    "manifest_sha256",
    "runner_sha256",
    "mission_state_sha256",
    "github_pre_smoke_authority",
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
    or payload.get("schema") != "iter135.smoke_lock.v2"
    or hashlib.sha256(lock_payload).hexdigest() != expected_lock_sha
    or payload.get("manifest_sha256") != manifest_sha
    or payload.get("runner_sha256") != runner_sha
    or payload.get("mission_state_sha256") != hashlib.sha256(mission_payload).hexdigest()
    or payload.get("pid") != expected_pid
    or payload.get("mode") != "nonanalytic_g5_smoke"
    or payload.get("nonanalytic") is not True
    or type(payload.get("analytic_episode_count")) is not int
    or payload.get("analytic_episode_count") != 0
    or type(payload.get("dose_invocation_count")) is not int
    or payload.get("dose_invocation_count") != 4
    or payload.get("retry_policy") != "one_shot_no_retry_lock_retained"
    or payload.get("smoke_output_root")
    != "/datasets/nuscenes-full/sentinel-i135-smoke-evidence"
):
    raise SystemExit("persistent smoke lock receipt drift")
authority = payload.get("github_pre_smoke_authority")
if not isinstance(authority, dict) or set(authority) != {
    "schema",
    "repository",
    "branch",
    "pre_smoke_commit",
    "environment_parent",
    "manifest_sha256",
    "checks",
    "authority_payload_sha256",
}:
    raise SystemExit("persistent smoke lock GitHub authority field-set drift")
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
        "head_sha": expected_pre_smoke_commit,
        "app_slug": "github-actions",
        "status": "completed",
        "conclusion": "success",
    }
    for name, check_id in zip(("check (3.10)", "check (3.11)"), expected_check_ids)
]
if (
    authority.get("schema") != "iter135.github_pre_smoke_authority.v1"
    or authority.get("repository") != "manfromnowhere143/sentinel"
    or authority.get("branch") != "master"
    or authority.get("pre_smoke_commit") != expected_pre_smoke_commit
    or authority.get("environment_parent") != expected_environment_parent
    or manifest.get("git_provenance", {}).get("head") != expected_environment_parent
    or authority.get("manifest_sha256") != manifest_sha
    or authority.get("checks") != expected_checks
    or claimed_authority_sha != actual_authority_sha
):
    raise SystemExit("persistent smoke lock GitHub authority binding drift")
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

verify_docker_client_binding || fail_preflight "docker-client-drift-before-wrapper"
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
OBSERVED_DOCKER_EXECUTABLE_ID=$(stat -Lc '%d:%i' "$SENTINEL_DOCKER_EXECUTABLE" \
  2>/dev/null || stat -f '%d:%i' "$SENTINEL_DOCKER_EXECUTABLE" 2>/dev/null || true)
if [ ! -e "$SENTINEL_DOCKER_EXECUTABLE" ] \
  || [ "$OBSERVED_DOCKER_EXECUTABLE_ID" != "$SENTINEL_DOCKER_BIN_ID" ] \
  || [ "$(sha256sum "$SENTINEL_DOCKER_EXECUTABLE" | awk '{print $1}')" \
    != "$SENTINEL_DOCKER_BIN_SHA256" ]; then
  echo "I135_SMOKE_DOCKER_WRAPPER_FAIL docker-pinned-executable-drift" >&2
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
if [ "$COMMAND" = "kill" ]; then
  if [ "$#" != "1" ]; then
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-arity" >&2
    exit 125
  fi
  case "$1" in
    renderer|model) ROLE=$1 ;;
    *)
      echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-role:$1" >&2
      exit 125
      ;;
  esac
  CID_FILE=$SENTINEL_CONTAINER_CID_DIR/$ROLE.cid
  if [ -L "$CID_FILE" ] || [ ! -f "$CID_FILE" ]; then
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-cid-file:$ROLE" >&2
    exit 125
  fi
  CID=$(<"$CID_FILE")
  if ! [[ "$CID" =~ ^[0-9a-f]{64}$ ]]; then
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-cid:$ROLE" >&2
    exit 125
  fi
  INSPECT=$(
    "$SENTINEL_DOCKER_EXECUTABLE" inspect --format \
      '{{.Id}}|{{.Name}}|{{index .Config.Labels "sentinel.mission"}}|{{index .Config.Labels "sentinel.manifest"}}|{{index .Config.Labels "sentinel.mode"}}|{{index .Config.Labels "sentinel.dose"}}|{{index .Config.Labels "sentinel.role"}}' \
      "$CID"
  ) || {
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-inspect:$ROLE" >&2
    exit 125
  }
  EXPECTED_INSPECT="$CID|/$ROLE|iter135|$SENTINEL_MANIFEST_SHA256|nonanalytic-smoke|$SENTINEL_SMOKE_DOSE_ORDINAL|$ROLE"
  if [ "$INSPECT" != "$EXPECTED_INSPECT" ]; then
    echo "I135_SMOKE_DOCKER_WRAPPER_FAIL kill-ownership:$ROLE" >&2
    exit 125
  fi
  exec "$SENTINEL_DOCKER_EXECUTABLE" kill "$CID"
fi
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
exec "$SENTINEL_DOCKER_EXECUTABLE" run \
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
  echo "I135_SMOKE_PYTHON_WRAPPER_FAIL wrapper-identity-drift" >&2
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
  echo "I135_SMOKE_PYTHON_WRAPPER_FAIL interpreter-drift" >&2
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
) || fail_preflight "python-wrapper-create"

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
    if re.fullmatch(r"dose-[0-3]", child.name):
        if (
            child.is_symlink()
            or not child.is_dir()
            or stat.S_IMODE(child.stat().st_mode) != 0o700
        ):
            unexpected.append(child.name)
        continue
    unexpected.append(child.name)
if (
    root != Path("/datasets/nuscenes-full/sentinel-i135-smoke-evidence/container-control")
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
  verify_docker_client_binding || return 1
  [ "$(verify_docker_v3_runtime)" = "$DOCKER_RUNTIME_SHA" ] || return 1
  python3 - "$MANIFEST_SOURCE" "$EXPECTED_MANIFEST_SHA" "$SCHEDULE_TARGET" \
    "$SMOKE_OUTPUT_ROOT/server_patch_blind_dose.py" "$STACK/UniAD/inference/server.py" \
    "$EXPECTED_SERVER_SHA" "$SCENARIO_CLASS" "$SEQUENCE" "$PHASE" \
    "$EXPECTED_UNIAD_IMAGE_ID" "$EXPECTED_NEURAD_IMAGE_ID" "$EXPECTED_NCAP_IMAGE_ID" \
    "$DOCKER_FD_PATH" <<'PY'
import hashlib
import json
import os
import re
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
    docker_binary,
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
    != "f61363c91fa6e0f3db24a6df2e32afc16ad02ebc44e3c4af66132fcc317760c2"
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
    path = row.get("path")
    sha256 = row.get("sha256")
    byte_count = row.get("bytes")
    if (
        type(role) is not str
        or not role
        or role in by_role
        or type(path) is not str
        or not Path(path).is_absolute()
        or type(sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", sha256) is None
        or type(byte_count) is not int
        or byte_count <= 0
    ):
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
        [docker_binary, "image", "inspect", "--format", "{{.Id}}", expected_image],
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
cp "$MISSION_STATE_SOURCE" "$RAW_DIR/pre_smoke_mission_state.json"
for name in HYPOTHESIS.md authorize_launch135.py extract_union_windows.py \
  generate_nested_dose_schedules.py dose_schedules.json server_patch_union_release.py \
  server_patch_blind_dose.py analyze_dose135.py collect_proof135.py run_dose135.sh \
  run_smoke135.sh validate_smoke135.py capture_environment135.py prepare_host135.py \
  verify_tooling135.py patch_compose_dose_env.py make_launch_manifest.py \
  env_receipts.json host_packet_manifest.json host_preparation_receipt.json \
  tooling_verification_receipt.json; do
  cp "$I135/$name" "$SMOKE_OUTPUT_ROOT/$name"
done
cp "$MISSION_STATE_SOURCE" "$SMOKE_OUTPUT_ROOT/MISSION_STATE.json"
python3 - "$MANIFEST_SOURCE" "$SMOKE_OUTPUT_ROOT" <<'PY' \
  || fail_preflight "smoke-deployment-binding"
import hashlib
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_bytes())
root = Path(sys.argv[2])
required = {
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
    "patch_compose_dose_env.py",
    "make_launch_manifest.py",
    "env_receipts.json",
    "host_packet_manifest.json",
    "host_preparation_receipt.json",
    "tooling_verification_receipt.json",
}
bound = manifest.get("hash_bound_files")
if not isinstance(bound, dict) or not required.issubset(bound):
    raise SystemExit("deployed required payload set is not manifest-bound")
for name in sorted(required):
    path = root / name
    receipt = bound[name]
    payload = path.read_bytes()
    expected_source_path = (
        f"experiments/iter135_neuroncap_blind_braking_dose_response/{name}"
    )
    if (
        path.is_symlink()
        or not path.is_file()
        or path.resolve(strict=True) != path
        or not isinstance(receipt, dict)
        or receipt.get("source_path") != expected_source_path
        or receipt.get("sha256") != hashlib.sha256(payload).hexdigest()
        or receipt.get("bytes") != len(payload)
    ):
        raise SystemExit(f"deployed payload drift: {name}")
PY
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
  "$DOCKER_BIN_SHA" "$DOCKER_BIN_ID" "$PYTHON_WRAPPER_SHA" \
  "$PYTHON_BIN_SHA" "$PYTHON_BIN_ID" "$CONTAINER_CONTROL_ROOT_ID" \
  "$DOCKER_FD_PATH" <<'PY'
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
    python_wrapper_sha,
    python_sha,
    python_identity,
    container_control_root_identity,
    docker_binary,
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
        [docker_binary, "image", "inspect", name, "--format", "{{.Id}}"], text=True
    ).strip()
    id_actual = subprocess.check_output(
        [docker_binary, "image", "inspect", expected_id, "--format", "{{.Id}}"], text=True
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
lock_payload = Path(lock_path).read_bytes()
lock_receipt = json.loads(lock_payload)
github_pre_smoke_authority = lock_receipt.get("github_pre_smoke_authority")
if (
    lock_receipt.get("schema") != "iter135.smoke_lock.v2"
    or not isinstance(github_pre_smoke_authority, dict)
    or lock_receipt.get("manifest_sha256") != manifest_hash
):
    raise SystemExit("persistent smoke lock authority drift before journal")
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
    "persistent_smoke_lock_sha256": hashlib.sha256(lock_payload).hexdigest(),
    "github_pre_smoke_authority": github_pre_smoke_authority,
    "retry_policy": "one_shot_no_retry_lock_retained",
    "docker_wrapper_sha256": wrapper_sha,
    "docker_binary_sha256": docker_sha,
    "docker_binary_identity": docker_identity,
    "python_wrapper_sha256": python_wrapper_sha,
    "python_binary_sha256": python_sha,
    "python_binary_identity": python_identity,
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
  if ! verify_python_interpreter_binding; then
    append_abort "python-interpreter-drift-before:$DOSE"
    exit 1
  fi
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
  if ! verify_python_interpreter_binding; then
    [ "$MONITOR_RC" != "0" ] || MONITOR_RC=80
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
  || ! verify_python_interpreter_binding || ! verify_final_live_contract; then
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
