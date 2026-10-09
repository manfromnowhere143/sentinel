#!/usr/bin/env python3
"""Replay the exact repository-local inputs of Sentinel's Gen17 CI candidate.

This verifier is deliberately narrower than a hermetic-build or provenance system. It binds the
exact workflow, requirement input, resolved hash locks, verifier, and hostile test bytes; enforces
the frozen critical workflow shape; strict-decodes a canonical manifest; and refuses drift.

An honestly executed green result establishes only that these repository-local inputs and
structural rules match the committed manifest. It does not authenticate upstream actions or
packages, freeze the hosted runner, Python patch release, pip implementation, package index, or
network, reproduce a lock solve, retain an offline wheel mirror, produce an SBOM, or establish
SLSA/hermeticity/readiness.

Usage:
    python3 -I -B -S tools/ci/verify_supply_chain.py
    python3 -I -B -S tools/ci/verify_supply_chain.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENTS_REL = "AGENTS.md"
WORKFLOW_REL = ".github/workflows/ci.yml"
MANIFEST_REL = "tools/ci/supply-chain-manifest.json"
MANIFEST = ROOT / MANIFEST_REL
REQUIREMENTS_INPUT_REL = "tools/ci/requirements-ci.in"
VERIFIER_REL = "tools/ci/verify_supply_chain.py"
KNOWN_BADS_REL = "tests/test_iter135_gen17_ci_hardening.py"
PYTEST_LAUNCHER_REL = "tools/ci/run_pytest_isolated.py"
INSTALL_VERIFIER_REL = "tools/ci/verify_ci_install.py"
INSTALL_KNOWN_BADS_REL = "tests/test_iter135_ci_install_verifier.py"
LAUNCHER_KNOWN_BADS_REL = "tests/test_iter135_launcher.py"
PYPROJECT_REL = "pyproject.toml"
LOCKS = {
    "3.10": "tools/ci/requirements-ci-py310.lock",
    "3.11": "tools/ci/requirements-ci-py311.lock",
}
BOUND_FILES = (
    AGENTS_REL,
    WORKFLOW_REL,
    REQUIREMENTS_INPUT_REL,
    LOCKS["3.10"],
    LOCKS["3.11"],
    VERIFIER_REL,
    KNOWN_BADS_REL,
    PYTEST_LAUNCHER_REL,
    INSTALL_VERIFIER_REL,
    INSTALL_KNOWN_BADS_REL,
    LAUNCHER_KNOWN_BADS_REL,
    PYPROJECT_REL,
)

SCHEMA = "sentinel.ci_input_manifest.v2"
CLAIM = (
    "exact identities of enumerated repository-local Gen17 controls and frozen critical "
    "workflow shape replay"
)
LIMITATIONS = (
    "no upstream action or package authenticity claim",
    "GitHub-hosted runner image, Python patch, pip, index, and network are not content-addressed",
    "hash-locked install is not an offline wheel mirror or rebuild proof",
    "lock solving is not claimed deterministic or reproducible from requirements-ci.in",
    "co-edited inputs and manifest require an independently accepted commit/receipt identity",
    "no hermeticity, SBOM, SLSA, product-readiness, launch-authority, or scientific claim",
    "enumerated controls are not whole-tree identity; that requires the accepted source commit",
)

EXPECTED_ACTIONS = (
    ("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262"),
    ("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065"),
)
EXPECTED_RUNNER = "ubuntu-latest"
EXPECTED_MATRIX = (
    ("3.10", LOCKS["3.10"]),
    ("3.11", LOCKS["3.11"]),
)
EXPECTED_RUN_COMMANDS = (
    "python3 -I -B -S tools/ci/verify_supply_chain.py",
    'test -n "${RUNNER_TEMP:-}" && test -d "${RUNNER_TEMP}" && test ! -L '
    '"${RUNNER_TEMP}" && test ! -e "${RUNNER_TEMP}/sentinel-ci-'
    '${{ matrix.python-version }}" && python -I -B -m venv '
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}"',
    'test ! -e "${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json" && '
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B -m pip '
    "--isolated --disable-pip-version-check install --no-input --force-reinstall "
    "--require-hashes --only-binary=':all:' --no-deps --report "
    '"${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json" '
    "-r ${{ matrix.lock }}",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B '
    "-m pip --isolated --disable-pip-version-check check",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B '
    "-S tools/ci/verify_ci_install.py --python-minor "
    '"${{ matrix.python-version }}" --lock "${{ matrix.lock }}" --report '
    '"${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json"',
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/ruff" check .',
    "env -u PYTHONHOME -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS "
    "PYTHONPATH= PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -B -S '
    "tools/ci/run_pytest_isolated.py -q "
    "-c pyproject.toml --noconftest --strict-config --strict-markers "
    "tests/test_iter135_gen17_ci_hardening.py tests/test_iter135_ci_install_verifier.py",
    "env -u PYTHONHOME -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS "
    "PYTHONPATH= PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -B -S '
    "tools/ci/run_pytest_isolated.py -q "
    "-c pyproject.toml --noconftest --strict-config --strict-markers",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B -S '
    "-c 'import runpy,sys;"
    "sys.path.append(\"scripts\");"
    "runpy.run_path(\"scripts/validate_docs.py\",run_name=\"__main__\")'",
)
EXPECTED_STEP_SEQUENCE = (
    (
        "uses",
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    ),
    ("run", EXPECTED_RUN_COMMANDS[0]),
    (
        "uses",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    ),
    *(("run", command) for command in EXPECTED_RUN_COMMANDS[1:]),
)
EXPECTED_STATIC_SHA256 = {
    AGENTS_REL: "9dd96d223327384d77760671396b8075a5a57bc1396abdcff5a12095055add69",
    WORKFLOW_REL: "09c7fb25eff2429aa9474ca9b4a4d0fdeb88efc3ff3d0cdb92c760bbdcd535d8",
    REQUIREMENTS_INPUT_REL: "d5de49ff7c882e801ec1b11fb34d5d72babd5eb32636a79ef9a82ef0185b7ea0",
    LOCKS["3.10"]: "d0e296ff6d3b90e29af4607e4c9a00aa203a90853de690b591ce116e4158fb32",
    LOCKS["3.11"]: "7a225e43c33b077ce74697e5fb03a621ab531b68fe95d3786c7d4dedadaa5018",
    PYPROJECT_REL: "ab80da2c41d29f98ace7d372c5b87ee6bbd3fee072b89892db499a01a620bc0d",
}
EXPECTED_REQUIREMENTS_INPUT = (
    "ruff==0.15.20",
    "pytest==9.1.1",
    'numpy==2.2.6 ; python_version == "3.10"',
    'numpy==2.4.6 ; python_version == "3.11"',
    'scikit-learn==1.7.2 ; python_version == "3.10"',
    'scikit-learn==1.9.0 ; python_version == "3.11"',
)
EXPECTED_DIRECT_PACKAGES = {
    "3.10": {
        "numpy": "2.2.6",
        "pytest": "9.1.1",
        "ruff": "0.15.20",
        "scikit-learn": "1.7.2",
    },
    "3.11": {
        "numpy": "2.4.6",
        "pytest": "9.1.1",
        "ruff": "0.15.20",
        "scikit-learn": "1.9.0",
    },
}

MAX_BOUND_FILE_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_BYTES = 512 * 1024
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_USES_LINE = re.compile(
    r"^\s*-\s+uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)(?:\s+#.*)?$"
)
_RUN_LINE = re.compile(r"^\s*-\s+run:\s*(.*?)\s*$")
_RUNNER_LINE = re.compile(r"^\s*runs-on:\s*([^\s#]+)\s*$")
_MATRIX_PYTHON_LINE = re.compile(r'^\s*-\s+python-version:\s*"([^"]+)"\s*$')
_MATRIX_LOCK_LINE = re.compile(r"^\s+lock:\s*([^\s#]+)\s*$")
_PLAIN_WORKFLOW_MAPPING_LINE = re.compile(
    r"^ *(?:- )?[A-Za-z][A-Za-z0-9_-]*:(?: .*)?$"
)
_FORBIDDEN_WORKFLOW_CONTROL_LINE = re.compile(
    r'''^\s*(?:-\s*)?["']?(?:if|continue-on-error|concurrency|container|defaults|needs|services)'''
    r'''["']?\s*:'''
)
_REQUIREMENT_START = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;\\]+)\s+\\$"
)
_HASH_TOKEN = re.compile(
    r"^    --hash=sha256:([0-9a-f]{64})(?:\s+\\)?$", re.MULTILINE
)


class SupplyChainError(ValueError):
    """A CI input or manifest is absent, unsafe, malformed, or outside the frozen contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(document: object) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode("ascii")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SupplyChainError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise SupplyChainError(f"non-finite JSON number: {value}")


def _exact_json_value(observed: object, expected: object) -> bool:
    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        observed_dict = observed
        expected_dict = expected
        return set(observed_dict) == set(expected_dict) and all(
            _exact_json_value(observed_dict[key], expected_dict[key]) for key in expected_dict
        )
    if type(expected) is list:
        observed_list = observed
        expected_list = expected
        return len(observed_list) == len(expected_list) and all(
            _exact_json_value(left, right)
            for left, right in zip(observed_list, expected_list, strict=True)
        )
    return observed == expected


def _read_regular_file(root: Path, relative: str, maximum: int) -> bytes:
    path = root / relative
    try:
        before = path.lstat()
    except OSError as exc:
        raise SupplyChainError(f"file cannot be stated: {relative}:{type(exc).__name__}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise SupplyChainError(f"file is not a physical regular file: {relative}")
    if before.st_size < 0 or before.st_size > maximum:
        raise SupplyChainError(f"file exceeds byte bound: {relative}")
    try:
        payload = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise SupplyChainError(f"file cannot be read: {relative}:{type(exc).__name__}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(payload) != after.st_size:
        raise SupplyChainError(f"file changed while read: {relative}")
    return payload


def _decode_utf8(payload: bytes, relative: str) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SupplyChainError(f"file is not UTF-8: {relative}") from exc
    if not text.endswith("\n") or "\r" in text or "\x00" in text:
        raise SupplyChainError(f"file text framing is noncanonical: {relative}")
    return text


def _parse_workflow(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if sum(line == "on: [push, pull_request]" for line in lines) != 1:
        raise SupplyChainError("workflow trigger is not exact push/pull_request")

    actions: list[tuple[str, str]] = []
    commands: list[str] = []
    runners: list[str] = []
    matrix: list[tuple[str, str]] = []
    steps: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if _FORBIDDEN_WORKFLOW_CONTROL_LINE.match(line):
            raise SupplyChainError("workflow contains a forbidden control key")
        if _PLAIN_WORKFLOW_MAPPING_LINE.fullmatch(line) is None:
            raise SupplyChainError("workflow contains noncanonical mapping-key syntax")
        if "uses:" in line:
            match = _USES_LINE.fullmatch(line)
            if match is None:
                raise SupplyChainError("workflow contains an unparseable action use")
            actions.append((match.group(1), match.group(2)))
            steps.append(("uses", f"{match.group(1)}@{match.group(2)}"))
        if "run:" in line:
            match = _RUN_LINE.fullmatch(line)
            if match is None or not match.group(1):
                raise SupplyChainError("workflow contains an unparseable run step")
            commands.append(match.group(1))
            steps.append(("run", match.group(1)))
        if "runs-on:" in line:
            match = _RUNNER_LINE.fullmatch(line)
            if match is None:
                raise SupplyChainError("workflow contains an unparseable runner")
            runners.append(match.group(1))
        python_match = _MATRIX_PYTHON_LINE.fullmatch(line)
        if python_match is not None:
            if index + 1 >= len(lines):
                raise SupplyChainError("workflow matrix row lacks a lock")
            lock_match = _MATRIX_LOCK_LINE.fullmatch(lines[index + 1])
            if lock_match is None:
                raise SupplyChainError("workflow matrix lock row is malformed")
            matrix.append((python_match.group(1), lock_match.group(1)))

    if tuple(actions) != EXPECTED_ACTIONS:
        raise SupplyChainError("workflow action inventory/order/ref differs from frozen contract")
    if any(not _SHA40.fullmatch(ref) for _owner, ref in actions):
        raise SupplyChainError("workflow action ref is not lowercase 40-hex")
    if runners != [EXPECTED_RUNNER]:
        raise SupplyChainError("workflow runner differs from frozen contract")
    if tuple(matrix) != EXPECTED_MATRIX:
        raise SupplyChainError("workflow Python/lock matrix differs from frozen contract")
    if tuple(commands) != EXPECTED_RUN_COMMANDS:
        raise SupplyChainError("workflow run-step inventory/order differs from frozen contract")
    if tuple(steps) != EXPECTED_STEP_SEQUENCE:
        raise SupplyChainError("workflow action/run interleaving differs from frozen contract")
    if text.count("python-version: ${{ matrix.python-version }}") != 1:
        raise SupplyChainError("setup-python matrix binding differs from frozen contract")
    return {
        "triggers": ["push", "pull_request"],
        "runner": EXPECTED_RUNNER,
        "actions": [
            {"owner_repo": owner_repo, "ref": ref} for owner_repo, ref in actions
        ],
        "python_lock_matrix": [
            {"python": version, "lock": lock} for version, lock in matrix
        ],
        "run_commands": commands,
        "steps": [{"kind": kind, "value": value} for kind, value in steps],
    }


def _parse_requirements_input(text: str) -> list[str]:
    rows = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if tuple(rows) != EXPECTED_REQUIREMENTS_INPUT:
        raise SupplyChainError("requirements input differs from frozen exact direct constraints")
    return rows


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_lock(text: str, version: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        if not line or line.startswith(("#", " ", "\t")):
            continue
        match = _REQUIREMENT_START.fullmatch(line)
        if match is None:
            raise SupplyChainError(f"lock {version} contains an unpinned or malformed row")
        starts.append((index, match))
    if not starts:
        raise SupplyChainError(f"lock {version} contains no requirements")
    for preamble_line in lines[: starts[0][0]]:
        if preamble_line and not preamble_line.startswith("#"):
            raise SupplyChainError(f"lock {version} contains an unrecognized preamble")

    packages: dict[str, dict[str, Any]] = {}
    for ordinal, (start, match) in enumerate(starts):
        end = starts[ordinal + 1][0] if ordinal + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end])
        for continuation in lines[start + 1 : end]:
            if (
                not continuation
                or continuation.startswith("    #")
                or _HASH_TOKEN.fullmatch(continuation) is not None
            ):
                continue
            raise SupplyChainError(f"lock {version} contains an unrecognized continuation")
        hashes = _HASH_TOKEN.findall(block)
        if not hashes or block.count("--hash=") != len(hashes):
            raise SupplyChainError(f"lock {version} requirement lacks exact SHA-256 hashes")
        if len(hashes) != len(set(hashes)) or any(not _SHA256.fullmatch(item) for item in hashes):
            raise SupplyChainError(f"lock {version} contains duplicate or malformed hashes")
        name = _normalize_name(match.group(1))
        if name in packages:
            raise SupplyChainError(f"lock {version} contains duplicate package: {name}")
        packages[name] = {
            "version": match.group(2),
            "hash_count": len(hashes),
        }

    direct = EXPECTED_DIRECT_PACKAGES[version]
    if any(
        name not in packages or packages[name]["version"] != expected
        for name, expected in direct.items()
    ):
        raise SupplyChainError(f"lock {version} direct package versions differ")
    return [{"name": name, **packages[name]} for name in sorted(packages)]


def derive(root: Path) -> dict[str, Any]:
    """Derive the complete frozen Gen17 CI-input projection from repository bytes."""

    root = root.resolve(strict=True)
    payloads = {
        relative: _read_regular_file(root, relative, MAX_BOUND_FILE_BYTES)
        for relative in BOUND_FILES
    }
    for relative, expected_sha256 in EXPECTED_STATIC_SHA256.items():
        if _sha256_bytes(payloads[relative]) != expected_sha256:
            raise SupplyChainError(f"frozen static input digest differs: {relative}")
    workflow = _parse_workflow(_decode_utf8(payloads[WORKFLOW_REL], WORKFLOW_REL))
    requirements_input = _parse_requirements_input(
        _decode_utf8(payloads[REQUIREMENTS_INPUT_REL], REQUIREMENTS_INPUT_REL)
    )
    locks: dict[str, Any] = {}
    for version, relative in LOCKS.items():
        locks[version] = {
            "path": relative,
            "sha256": _sha256_bytes(payloads[relative]),
            "packages": _parse_lock(_decode_utf8(payloads[relative], relative), version),
        }
    return {
        "schema": SCHEMA,
        "claim": CLAIM,
        "limitations": list(LIMITATIONS),
        "files": {
            relative: {
                "bytes": len(payloads[relative]),
                "sha256": _sha256_bytes(payloads[relative]),
            }
            for relative in sorted(payloads)
        },
        "requirements_input": requirements_input,
        "workflow": workflow,
        "locks": locks,
    }


def _load_manifest(root: Path) -> dict[str, Any]:
    raw = _read_regular_file(root, MANIFEST_REL, MAX_MANIFEST_BYTES)
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, ValueError, SupplyChainError) as exc:
        raise SupplyChainError(f"manifest strict decode failed: {exc}") from exc
    if type(document) is not dict:
        raise SupplyChainError("manifest root is not an exact object")
    if raw != _canonical(document):
        raise SupplyChainError("manifest bytes are not canonical JSON")
    return document


def verify(root: Path) -> list[str]:
    """Return stable problems; an empty list means exact repository-local replay."""

    try:
        derived = derive(root)
    except (OSError, SupplyChainError) as exc:
        return [f"supply_chain:derive:{exc}"]
    try:
        committed = _load_manifest(root.resolve(strict=True))
    except (OSError, SupplyChainError) as exc:
        return [f"supply_chain:manifest:{exc}"]
    if not _exact_json_value(committed, derived):
        return ["supply_chain:manifest_drift"]
    return []


def _write_manifest(document: dict[str, Any]) -> None:
    payload = _canonical(document)
    staging = MANIFEST.with_name(f".{MANIFEST.name}.tmp-{os.getpid()}")
    descriptor: int | None = None
    try:
        descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, MANIFEST)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the canonical derived manifest")
    args = parser.parse_args(argv)

    if args.write:
        try:
            document = derive(ROOT)
            _write_manifest(document)
        except (OSError, SupplyChainError) as exc:
            print(f"SUPPLY_CHAIN_MANIFEST_WRITE_FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {MANIFEST_REL}")
        return 0

    problems = verify(ROOT)
    if problems:
        print("SUPPLY_CHAIN_VERIFICATION_FAILED", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print("SUPPLY_CHAIN_VERIFICATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
