#!/usr/bin/env python3
"""Verify one hash-locked CI installation without granting authority.

This verifier is intended to run inside a fresh isolated virtual environment after pip has been
invoked with ``--force-reinstall --require-hashes --only-binary=:all: --no-deps``
and a new ``--report`` path.  It independently reconciles three
views: the selected lock, pip's installation report, and distributions visible
only in the interpreter's ``purelib``/``platlib`` directories.

An honestly executed success establishes only this bounded reconciliation.  It
does not authenticate the package index, freeze pip or bootstrap packages,
prove a reproducible build, or grant launch or scientific authority.
"""

from __future__ import annotations

import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import urlsplit


MAX_LOCK_BYTES = 4 * 1024 * 1024
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_PYVENV_CONFIG_BYTES = 64 * 1024
MAX_PACKAGES = 2048
MAX_HASHES_PER_PACKAGE = 4096
BOOTSTRAP_PACKAGES = frozenset({"pip", "setuptools", "wheel"})

_MINOR = re.compile(r"^[0-9]+\.[0-9]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+!-]*$")
_REQUIREMENT_START = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;\\]+)\s+\\$")
_HASH_LINE = re.compile(r"^    --hash=sha256:([0-9a-f]{64})(?:\s+\\)?$")


class InstallVerificationError(ValueError):
    """A lock, report, runtime, or installed inventory violated the contract."""


def _normalize_name(name: str) -> str:
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    if not normalized or re.fullmatch(r"[a-z0-9][a-z0-9-]*", normalized) is None:
        raise InstallVerificationError("package name is malformed")
    return normalized


def _read_regular_nofollow(path: Path, maximum: int, label: str) -> bytes:
    if not hasattr(os, "O_NOFOLLOW"):
        raise InstallVerificationError("platform lacks nofollow file reads")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InstallVerificationError(
            f"{label} cannot be opened as a physical file: {type(exc).__name__}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InstallVerificationError(f"{label} is not a physical regular file")
        if before.st_size < 0 or before.st_size > maximum:
            raise InstallVerificationError(f"{label} exceeds byte bound")
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise InstallVerificationError(f"{label} exceeds byte bound")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    payload = b"".join(chunks)
    if before_identity != after_identity or len(payload) != after.st_size:
        raise InstallVerificationError(f"{label} changed while read")
    return payload


def _decode_utf8(payload: bytes, label: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallVerificationError(f"{label} is not UTF-8") from exc


def parse_lock_bytes(payload: bytes) -> dict[str, tuple[str, frozenset[str]]]:
    """Parse exact pins and per-row SHA-256 allowlists from one retained lock."""

    text = _decode_utf8(payload, "lock")
    if not text.endswith("\n") or "\r" in text or "\x00" in text:
        raise InstallVerificationError("lock text framing is noncanonical")
    cpu_source = "--find-links https://download.pytorch.org/whl/cpu/torch/\n"
    if cpu_source in text and not text.startswith(cpu_source):
        raise InstallVerificationError("lock contains an unrecognized preamble")
    if text.startswith(cpu_source):
        text = text[len(cpu_source):]
    lines = text.splitlines()
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        if not line or line.startswith(("#", " ", "\t")):
            continue
        match = _REQUIREMENT_START.fullmatch(line)
        if match is None:
            raise InstallVerificationError("lock contains an unpinned or malformed row")
        starts.append((index, match))
    if not starts:
        raise InstallVerificationError("lock contains no packages")
    if len(starts) > MAX_PACKAGES:
        raise InstallVerificationError("lock package count exceeds bound")
    for line in lines[: starts[0][0]]:
        if line and not line.startswith("#"):
            raise InstallVerificationError("lock contains an unrecognized preamble")

    packages: dict[str, tuple[str, frozenset[str]]] = {}
    for ordinal, (start, match) in enumerate(starts):
        end = starts[ordinal + 1][0] if ordinal + 1 < len(starts) else len(lines)
        hashes: list[str] = []
        for continuation in lines[start + 1 : end]:
            if not continuation or continuation.startswith("    #"):
                continue
            hash_match = _HASH_LINE.fullmatch(continuation)
            if hash_match is None:
                raise InstallVerificationError("lock contains an unrecognized continuation")
            hashes.append(hash_match.group(1))
        if not hashes:
            raise InstallVerificationError("lock package lacks a SHA-256 allowlist")
        if len(hashes) > MAX_HASHES_PER_PACKAGE:
            raise InstallVerificationError("lock hash count exceeds bound")
        if len(hashes) != len(set(hashes)):
            raise InstallVerificationError("lock package contains a duplicate SHA-256")
        name = _normalize_name(match.group(1))
        version = match.group(2)
        if _VERSION.fullmatch(version) is None:
            raise InstallVerificationError("lock package version is malformed")
        if name in packages:
            raise InstallVerificationError(f"lock contains duplicate package: {name}")
        packages[name] = (version, frozenset(hashes))
    return packages


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InstallVerificationError(f"report contains duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise InstallVerificationError(f"report contains non-finite JSON number: {value}")


def _require_exact_type(value: object, expected: type, message: str) -> Any:
    if type(value) is not expected:
        raise InstallVerificationError(message)
    return value


def _archive_sha256(archive: dict[str, Any]) -> str:
    values: list[str] = []
    if "hashes" in archive:
        hashes = _require_exact_type(
            archive["hashes"], dict, "report archive hashes are not an object"
        )
        if set(hashes) != {"sha256"}:
            raise InstallVerificationError("report archive hashes are not exactly SHA-256")
        value = _require_exact_type(hashes["sha256"], str, "report archive SHA-256 is not a string")
        values.append(value)
    if "hash" in archive:
        legacy = _require_exact_type(
            archive["hash"], str, "report legacy archive hash is not a string"
        )
        prefix = "sha256="
        if not legacy.startswith(prefix):
            raise InstallVerificationError("report legacy archive hash is not SHA-256")
        values.append(legacy[len(prefix) :])
    if not values:
        raise InstallVerificationError("report package lacks an archive SHA-256")
    if any(_SHA256.fullmatch(value) is None for value in values):
        raise InstallVerificationError("report archive SHA-256 is malformed")
    if len(set(values)) != 1:
        raise InstallVerificationError("report archive SHA-256 fields disagree")
    return values[0]


def parse_report_bytes(
    payload: bytes,
) -> tuple[str, str, dict[str, tuple[str, str]]]:
    """Strict-decode pip report v1 and return its Python minor and packages."""

    try:
        document = json.loads(
            _decode_utf8(payload, "report"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except (ValueError, InstallVerificationError) as exc:
        if isinstance(exc, InstallVerificationError):
            raise
        raise InstallVerificationError("report is malformed JSON") from exc
    document = _require_exact_type(document, dict, "report root is not an object")
    if set(document) != {"version", "pip_version", "install", "environment"}:
        raise InstallVerificationError("report top-level fields differ from pip report v1")
    if document["version"] != "1" or type(document["version"]) is not str:
        raise InstallVerificationError("report version is not exactly v1")
    pip_version = _require_exact_type(
        document["pip_version"], str, "report pip_version is not a string"
    )
    if not pip_version:
        raise InstallVerificationError("report pip_version is empty")
    if _VERSION.fullmatch(pip_version) is None:
        raise InstallVerificationError("report pip_version is malformed")
    environment = _require_exact_type(
        document["environment"], dict, "report environment is not an object"
    )
    python_minor = _require_exact_type(
        environment.get("python_version"),
        str,
        "report Python minor is not a string",
    )
    if _MINOR.fullmatch(python_minor) is None:
        raise InstallVerificationError("report Python minor is malformed")
    install = _require_exact_type(document["install"], list, "report install is not a list")
    if len(install) > MAX_PACKAGES:
        raise InstallVerificationError("report package count exceeds bound")

    packages: dict[str, tuple[str, str]] = {}
    for item in install:
        item = _require_exact_type(item, dict, "report install item is not an object")
        for field in ("is_direct", "requested"):
            _require_exact_type(item.get(field), bool, f"report package {field} is not a boolean")
        # CPython 3.10's bundled pip 23.0.1 report v1 predates this field.
        # Its exact producer implementation omits it; later pip must supply a bool.
        if pip_version == "23.0.1":
            if "is_yanked" in item:
                raise InstallVerificationError(
                    "legacy pip 23.0.1 report unexpectedly includes is_yanked"
                )
        else:
            _require_exact_type(
                item.get("is_yanked"), bool, "report package is_yanked is not a boolean"
            )
        if item["is_direct"] is not False:
            raise InstallVerificationError(
                "report package uses a direct URL outside the selected lock invocation"
            )
        if item["requested"] is not True:
            raise InstallVerificationError(
                "report package was not explicitly requested from the selected lock"
            )
        if "requested_extras" in item:
            raise InstallVerificationError(
                "report package requested extras outside the selected lock invocation"
            )
        metadata_object = _require_exact_type(
            item.get("metadata"), dict, "report package metadata is not an object"
        )
        raw_name = _require_exact_type(
            metadata_object.get("name"), str, "report package name is not a string"
        )
        version = _require_exact_type(
            metadata_object.get("version"), str, "report package version is not a string"
        )
        if _VERSION.fullmatch(version) is None:
            raise InstallVerificationError("report package version is malformed")
        name = _normalize_name(raw_name)
        if name in packages:
            raise InstallVerificationError(f"report contains duplicate package: {name}")
        download = _require_exact_type(
            item.get("download_info"),
            dict,
            "report package lacks download information; force-reinstall was not evidenced",
        )
        url = _require_exact_type(
            download.get("url"), str, "report package download URL is not a string"
        )
        if not url:
            raise InstallVerificationError("report package download URL is empty")
        parsed_url = urlsplit(url)
        if parsed_url.scheme not in {"file", "https"} or not parsed_url.path.lower().endswith(
            ".whl"
        ):
            raise InstallVerificationError("report package artifact is not an admitted wheel URL")
        archive = _require_exact_type(
            download.get("archive_info"), dict, "report package archive_info is not an object"
        )
        packages[name] = (version, _archive_sha256(archive))
    return python_minor, pip_version, packages


def _runtime_minor() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def _parse_pyvenv_config(payload: bytes, expected_python_minor: str) -> dict[str, str]:
    text = _decode_utf8(payload, "pyvenv.cfg")
    if not text.endswith("\n") or "\r" in text or "\x00" in text:
        raise InstallVerificationError("pyvenv.cfg text framing is noncanonical")
    document: dict[str, str] = {}
    for raw_line in text.splitlines():
        if not raw_line:
            continue
        key, separator, value = raw_line.partition("=")
        key = key.strip().lower()
        value = value.strip()
        if separator != "=" or re.fullmatch(r"[a-z][a-z0-9-]*", key) is None or not value:
            raise InstallVerificationError("pyvenv.cfg contains a malformed row")
        if key in document:
            raise InstallVerificationError(f"pyvenv.cfg contains duplicate key: {key}")
        document[key] = value
    if document.get("include-system-site-packages", "").lower() != "false":
        raise InstallVerificationError("venv must exclude system site-packages")
    version = document.get("version")
    if type(version) is not str or re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", version) is None:
        raise InstallVerificationError("pyvenv.cfg version is malformed")
    configured_minor = ".".join(version.split(".")[:2])
    if configured_minor != expected_python_minor:
        raise InstallVerificationError("pyvenv.cfg Python minor differs from CLI")
    return document


def _venv_install_paths(
    expected_python_minor: str, executable: Path | None = None
) -> tuple[Path, ...]:
    raw_executable = Path(sys.executable) if executable is None else executable
    if not raw_executable.is_absolute():
        raise InstallVerificationError("runtime executable path is not absolute")
    raw_bin_directory = raw_executable.parent
    try:
        executable_status = raw_executable.lstat()
        raw_bin_status = raw_bin_directory.lstat()
        bin_directory = raw_bin_directory.resolve(strict=True)
    except OSError as exc:
        raise InstallVerificationError("runtime executable path is unavailable") from exc
    if not (stat.S_ISREG(executable_status.st_mode) or stat.S_ISLNK(executable_status.st_mode)):
        raise InstallVerificationError("runtime executable is not a file or symlink")
    if not stat.S_ISDIR(raw_bin_status.st_mode) or stat.S_ISLNK(raw_bin_status.st_mode):
        raise InstallVerificationError("venv bin must be a physical directory")
    if bin_directory.name != "bin":
        raise InstallVerificationError("runtime executable is not inside a venv bin directory")
    venv_root = bin_directory.parent
    try:
        root_status = venv_root.lstat()
        bin_status = bin_directory.lstat()
    except OSError as exc:
        raise InstallVerificationError("physical venv directories are unavailable") from exc
    if not stat.S_ISDIR(root_status.st_mode) or not stat.S_ISDIR(bin_status.st_mode):
        raise InstallVerificationError("venv root and bin must be physical directories")

    config_path = venv_root / "pyvenv.cfg"
    _parse_pyvenv_config(
        _read_regular_nofollow(config_path, MAX_PYVENV_CONFIG_BYTES, "pyvenv.cfg"),
        expected_python_minor,
    )
    lib_directory = venv_root / "lib"
    python_directory = lib_directory / f"python{expected_python_minor}"
    site_packages = python_directory / "site-packages"
    for route, label in (
        (lib_directory, "lib"),
        (python_directory, f"lib/python{expected_python_minor}"),
        (site_packages, f"lib/python{expected_python_minor}/site-packages"),
    ):
        try:
            route_status = route.lstat()
        except OSError as exc:
            raise InstallVerificationError(f"venv install route is unavailable: {label}") from exc
        if not stat.S_ISDIR(route_status.st_mode) or stat.S_ISLNK(route_status.st_mode):
            raise InstallVerificationError(
                f"venv install route is not a physical directory: {label}"
            )
    try:
        physical_root = venv_root.resolve(strict=True)
        physical_site_packages = site_packages.resolve(strict=True)
    except OSError as exc:
        raise InstallVerificationError("venv install route cannot be resolved") from exc
    if not physical_site_packages.is_relative_to(physical_root):
        raise InstallVerificationError("venv install route escapes the physical venv root")
    return (site_packages,)


def _installed_records(paths: Sequence[Path]) -> Iterable[tuple[str, str]]:
    for distribution in metadata.distributions(path=[str(path) for path in paths]):
        name = distribution.metadata.get("Name")
        version = distribution.version
        if type(name) is not str or type(version) is not str:
            raise InstallVerificationError("installed distribution metadata is malformed")
        yield name, version


def _inventory(
    records: Iterable[tuple[str, str]],
) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for raw_name, version in records:
        if type(raw_name) is not str or type(version) is not str:
            raise InstallVerificationError("installed distribution metadata is malformed")
        if _VERSION.fullmatch(version) is None:
            raise InstallVerificationError("installed distribution version is malformed")
        name = _normalize_name(raw_name)
        if name in inventory:
            raise InstallVerificationError(
                f"installed inventory contains duplicate package: {name}"
            )
        inventory[name] = version
        if len(inventory) > MAX_PACKAGES:
            raise InstallVerificationError("installed package count exceeds bound")
    return inventory


def verify_ci_install(
    lock_path: Path,
    report_path: Path,
    expected_python_minor: str,
    *,
    runtime_python_minor: str | None = None,
    inventory_loader: Callable[[Sequence[Path]], Iterable[tuple[str, str]]] | None = None,
    install_paths: Sequence[Path] | None = None,
) -> str:
    """Verify and return the one stable success line; raise on any discrepancy."""

    if type(expected_python_minor) is not str or _MINOR.fullmatch(expected_python_minor) is None:
        raise InstallVerificationError("CLI Python minor is malformed")
    observed_runtime_minor = (
        _runtime_minor() if runtime_python_minor is None else runtime_python_minor
    )
    if type(observed_runtime_minor) is not str or _MINOR.fullmatch(observed_runtime_minor) is None:
        raise InstallVerificationError("runtime Python minor is malformed")
    if observed_runtime_minor != expected_python_minor:
        raise InstallVerificationError("CLI Python minor differs from runtime")

    lock = parse_lock_bytes(_read_regular_nofollow(lock_path, MAX_LOCK_BYTES, "lock"))
    report_minor, report_pip_version, reported = parse_report_bytes(
        _read_regular_nofollow(report_path, MAX_REPORT_BYTES, "report")
    )
    if report_minor != expected_python_minor:
        raise InstallVerificationError("CLI Python minor differs from report")

    lock_names = set(lock)
    report_names = set(reported)
    missing_report = sorted(lock_names - report_names)
    extra_report = sorted(report_names - lock_names)
    if missing_report:
        raise InstallVerificationError(
            "report is missing locked packages: " + ",".join(missing_report)
        )
    if extra_report:
        raise InstallVerificationError("report contains extra packages: " + ",".join(extra_report))
    for name in sorted(lock):
        locked_version, allowed_hashes = lock[name]
        reported_version, archive_hash = reported[name]
        if reported_version != locked_version:
            raise InstallVerificationError(f"report version differs from lock: {name}")
        if archive_hash not in allowed_hashes:
            raise InstallVerificationError(f"report archive SHA-256 is not admitted: {name}")

    paths = (
        tuple(install_paths)
        if install_paths is not None
        else _venv_install_paths(expected_python_minor)
    )
    loader = inventory_loader or _installed_records
    installed = _inventory(loader(paths))
    for name, (locked_version, _hashes) in sorted(lock.items()):
        if name not in installed:
            raise InstallVerificationError(f"installed inventory is missing locked package: {name}")
        if installed[name] != locked_version:
            raise InstallVerificationError(f"installed version differs from lock: {name}")
    extras = sorted(set(installed) - lock_names)
    forbidden = [name for name in extras if name not in BOOTSTRAP_PACKAGES]
    if forbidden:
        raise InstallVerificationError(
            "installed inventory contains extra packages: " + ",".join(forbidden)
        )
    installed_pip_version = installed.get("pip")
    if installed_pip_version is None:
        raise InstallVerificationError("installed inventory is missing report-producing pip")
    if installed_pip_version != report_pip_version:
        raise InstallVerificationError("installed pip version differs from report producer")
    unbound = [f"{name}=={installed[name]}" for name in extras]
    unbound_text = ",".join(unbound) if unbound else "none"
    return (
        "CI_INSTALL_VERIFICATION_OK "
        f"python={expected_python_minor} locked_packages={len(lock)} "
        f"unbound_bootstrap={unbound_text}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--python-minor", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_ci_install(args.lock, args.report, args.python_minor)
    except (OSError, InstallVerificationError) as exc:
        print(f"CI_INSTALL_VERIFICATION_FAILED: {exc}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
