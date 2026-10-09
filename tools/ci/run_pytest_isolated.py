#!/usr/bin/env python3
"""Run pytest from admitted install paths without site startup or repository import shadowing."""

from __future__ import annotations

import sys


def _refuse(message: str):
    print(f"ISOLATED_PYTEST_LAUNCH_REFUSED: {message}", file=sys.stderr)
    raise SystemExit(2)


if sys.flags.no_site != 1 or sys.flags.ignore_environment != 0:
    _refuse("requires -S while preserving PYTHONHASHSEED")
if sys.flags.optimize != 0:
    _refuse("Python optimization must be disabled")
if not sys.path:
    _refuse("initial import path is empty")

script_path_entry = sys.path.pop(0)
normalized_script_entry = script_path_entry.replace("\\", "/").rstrip("/")
if not normalized_script_entry.endswith("/tools/ci"):
    _refuse("first import path is not the launcher directory")
if any(not entry for entry in sys.path):
    _refuse("unsafe empty import-path entry remains")
if any(
    not entry.startswith((sys.base_prefix, sys.prefix))
    for entry in sys.path
):
    _refuse("non-interpreter import path is present before admission")

# These imports occur only after the repository script directory and empty-path aliases are gone.
import os  # noqa: E402
from pathlib import Path  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402


if os.environ.get("PYTHONHASHSEED") != "0":
    _refuse("PYTHONHASHSEED must be exactly 0")
if os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
    _refuse("pytest plugin autoload must be disabled")
if os.environ.get("PYTHONPATH") not in (None, ""):
    _refuse("PYTHONPATH must be absent or empty")
for forbidden_environment_name in (
    "PYTHONHOME",
    "PYTHONOPTIMIZE",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
):
    if forbidden_environment_name in os.environ:
        _refuse(f"{forbidden_environment_name} must be absent")

executable = Path(sys.executable)
if not executable.is_absolute() or executable.parent.name != "bin":
    _refuse("interpreter is not an absolute POSIX virtual-environment executable")
venv_root = executable.parent.parent
try:
    executable_stat = executable.lstat()
    bin_stat = executable.parent.lstat()
    root_stat = venv_root.lstat()
except OSError:
    _refuse("virtual-environment executable or directories are unavailable")
if not (
    stat.S_ISREG(executable_stat.st_mode) or stat.S_ISLNK(executable_stat.st_mode)
):
    _refuse("virtual-environment executable is not a file or symlink")
if (
    not stat.S_ISDIR(bin_stat.st_mode)
    or stat.S_ISLNK(bin_stat.st_mode)
    or not stat.S_ISDIR(root_stat.st_mode)
    or stat.S_ISLNK(root_stat.st_mode)
):
    _refuse("virtual-environment root and bin are not physical directories")

configuration = venv_root / "pyvenv.cfg"
try:
    configuration_stat = configuration.lstat()
except OSError:
    _refuse("pyvenv.cfg is unavailable")
if (
    not stat.S_ISREG(configuration_stat.st_mode)
    or stat.S_ISLNK(configuration_stat.st_mode)
    or not 1 <= configuration_stat.st_size <= 16 * 1024
):
    _refuse("pyvenv.cfg is not a bounded physical file")
try:
    configuration_text = configuration.read_text("utf-8")
except (OSError, UnicodeError):
    _refuse("pyvenv.cfg is unreadable")
normalized_configuration: dict[str, str] = {}
for configuration_line in configuration_text.splitlines():
    if not configuration_line or "=" not in configuration_line:
        _refuse("pyvenv.cfg contains a malformed row")
    configuration_key, configuration_value = configuration_line.split("=", 1)
    normalized_key = configuration_key.strip().lower()
    if not normalized_key or normalized_key in normalized_configuration:
        _refuse("pyvenv.cfg contains an empty or duplicate key")
    normalized_configuration[normalized_key] = configuration_value.strip().lower()
if normalized_configuration.get("include-system-site-packages") != "false":
    _refuse("virtual environment admits system site packages")
configured_version = normalized_configuration.get("version", "")
if re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", configured_version) is None:
    _refuse("pyvenv.cfg version is malformed")
configured_minor = ".".join(configured_version.split(".")[:2])
runtime_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
if configured_minor != runtime_minor:
    _refuse("pyvenv.cfg Python minor differs from runtime")

lib_directory = venv_root / "lib"
python_directory = lib_directory / f"python{runtime_minor}"
site_packages = python_directory / "site-packages"
for route, label in (
    (lib_directory, "lib"),
    (python_directory, f"lib/python{runtime_minor}"),
    (site_packages, f"lib/python{runtime_minor}/site-packages"),
):
    try:
        route_stat = route.lstat()
    except OSError:
        _refuse(f"virtual-environment install route is unavailable: {label}")
    if not stat.S_ISDIR(route_stat.st_mode) or stat.S_ISLNK(route_stat.st_mode):
        _refuse(f"virtual-environment install route is not a physical directory: {label}")
try:
    physical_root = venv_root.resolve(strict=True)
    physical_site_packages = site_packages.resolve(strict=True)
except OSError:
    _refuse("virtual-environment install route cannot be resolved")
if not physical_site_packages.is_relative_to(physical_root):
    _refuse("virtual-environment install route escapes the physical venv root")
admitted = (str(physical_site_packages),)
sys.path.extend(admitted)

import pytest  # noqa: E402


pytest_path = Path(pytest.__file__).resolve(strict=True)
if not any(pytest_path.is_relative_to(Path(root)) for root in admitted):
    _refuse("pytest did not resolve from admitted install paths")

raise SystemExit(pytest.console_main())
