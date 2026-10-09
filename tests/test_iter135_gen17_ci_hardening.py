"""Hostile Iteration-135 controls for the exact Gen17 CI-input replay gate."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools/ci/verify_supply_chain.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_supply_chain", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sc = _load_module()
MIRROR_FILES = (*sc.BOUND_FILES, sc.MANIFEST_REL)
CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
VERIFY = sc.EXPECTED_RUN_COMMANDS[0]
VENV = sc.EXPECTED_RUN_COMMANDS[1]
INSTALL = sc.EXPECTED_RUN_COMMANDS[2]
PIP_CHECK = sc.EXPECTED_RUN_COMMANDS[3]
INSTALL_VERIFY = sc.EXPECTED_RUN_COMMANDS[4]
RUFF = sc.EXPECTED_RUN_COMMANDS[5]
TARGETED_PYTEST = sc.EXPECTED_RUN_COMMANDS[6]
PYTEST = sc.EXPECTED_RUN_COMMANDS[7]
DOCS = sc.EXPECTED_RUN_COMMANDS[8]


def _mirror(root: Path) -> Path:
    for relative in MIRROR_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((REPO / relative).read_bytes())
    return root


def _replace(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text("utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _derive_refuses(root: Path, match: str) -> None:
    with pytest.raises(sc.SupplyChainError, match=match):
        sc.derive(root)


def _reseal(root: Path) -> None:
    (root / sc.MANIFEST_REL).write_bytes(sc._canonical(sc.derive(root)))


def _reanchor_static(
    root: Path, relative: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(
        sc.EXPECTED_STATIC_SHA256,
        relative,
        sc._sha256_bytes((root / relative).read_bytes()),
    )


def test_real_repository_replays_clean() -> None:
    assert sc.verify(REPO) == []


def test_positive_mirror_replays_clean(tmp_path: Path) -> None:
    assert sc.verify(_mirror(tmp_path)) == []


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        (CHECKOUT, "actions/checkout@v4", "frozen static input digest"),
        (SETUP_PYTHON, "actions/setup-python@v5", "frozen static input digest"),
        ("runs-on: ubuntu-latest", "runs-on: ubuntu-24.04", "frozen static input digest"),
        (
            'python-version: "3.10"',
            'python-version: "3.12"',
            "frozen static input digest",
        ),
        (
            "lock: tools/ci/requirements-ci-py310.lock",
            "lock: tools/ci/requirements-ci-py311.lock",
            "frozen static input digest",
        ),
        (INSTALL, INSTALL.replace(" --require-hashes", ""), "frozen static input digest"),
        (INSTALL, INSTALL.replace(" --only-binary=':all:'", ""), "frozen static input digest"),
        (INSTALL, INSTALL.replace(" --no-deps", ""), "frozen static input digest"),
        (INSTALL, INSTALL.replace(" --force-reinstall", ""), "frozen static input digest"),
        (
            INSTALL,
            INSTALL.replace(
                ' --report "${RUNNER_TEMP}/sentinel-ci-install-'
                '${{ matrix.python-version }}.json"',
                "",
            ),
            "frozen static input digest",
        ),
        (VENV, "python -m venv .venv", "frozen static input digest"),
        (INSTALL_VERIFY, "true", "frozen static input digest"),
        (
            VERIFY,
            "python -c 'print(1)'",
            "frozen static input digest",
        ),
        (PIP_CHECK, PIP_CHECK.replace(" check", " list"), "frozen static input digest"),
        (TARGETED_PYTEST, TARGETED_PYTEST + " -k smoke", "frozen static input digest"),
        (PYTEST, PYTEST + " -k smoke", "frozen static input digest"),
        (RUFF, RUFF.replace(" check .", " check tests"), "frozen static input digest"),
        (
            DOCS,
            "python -c 'print(1)'",
            "frozen static input digest",
        ),
        ("persist-credentials: false", "persist-credentials: true", "frozen static input digest"),
        ("contents: read", "contents: write", "frozen static input digest"),
        ("timeout-minutes: 45", "timeout-minutes: 450", "frozen static input digest"),
    ],
)
def test_frozen_workflow_mutations_are_refused(
    tmp_path: Path, old: str, new: str, problem: str
) -> None:
    root = _mirror(tmp_path)
    _replace(root, sc.WORKFLOW_REL, old, new)
    _derive_refuses(root, problem)


def test_unknown_unpinned_action_is_refused_before_manifest_comparison(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    _replace(
        root,
        sc.WORKFLOW_REL,
        f"      - uses: {CHECKOUT}",
        f"      - uses: owner/unknown@main\n      - uses: {CHECKOUT}",
    )
    _derive_refuses(root, "frozen static input digest")


def test_duplicate_mutable_action_is_refused_before_manifest_comparison(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    _replace(
        root,
        sc.WORKFLOW_REL,
        f"      - uses: {CHECKOUT}",
        f"      - uses: actions/checkout@v4\n      - uses: {CHECKOUT}",
    )
    _derive_refuses(root, "frozen static input digest")


def test_required_action_only_in_comment_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    _replace(
        root,
        sc.WORKFLOW_REL,
        f"      - uses: {SETUP_PYTHON}",
        f"      # - uses: {SETUP_PYTHON}",
    )
    _derive_refuses(root, "frozen static input digest")


def test_action_disabled_by_false_condition_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    _replace(
        root,
        sc.WORKFLOW_REL,
        f"      - uses: {SETUP_PYTHON}",
        f"      - if: false\n        uses: {SETUP_PYTHON}",
    )
    _derive_refuses(root, "frozen static input digest")


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "    runs-on: ubuntu-latest",
            "    if: false\n    runs-on: ubuntu-latest",
        ),
        (VERIFY, VERIFY + "\n        if: false"),
        (VERIFY, VERIFY + '\n        "if": false'),
        (VERIFY, VERIFY + "\n        continue-on-error: true"),
        (
            f"      - uses: {SETUP_PYTHON}",
            f"      - uses: {SETUP_PYTHON}\n        if: false",
        ),
    ],
)
def test_semantic_disable_is_refused_after_workflow_digest_reanchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    old: str,
    new: str,
) -> None:
    root = _mirror(tmp_path)
    _replace(root, sc.WORKFLOW_REL, old, new)
    _reanchor_static(root, sc.WORKFLOW_REL, monkeypatch)
    _derive_refuses(root, "forbidden control key")


@pytest.mark.parametrize(
    "mapping_rows",
    [
        '"i\\u0066": false',
        '"\\x69f": false',
        "!!str if: false",
        "&condition if: false",
        "? if\n        : false",
        "{if: false}: ignored",
    ],
)
def test_noncanonical_mapping_key_cannot_hide_semantic_disable_after_reanchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mapping_rows: str,
) -> None:
    root = _mirror(tmp_path)
    _replace(root, sc.WORKFLOW_REL, VERIFY, VERIFY + "\n        " + mapping_rows)
    _reanchor_static(root, sc.WORKFLOW_REL, monkeypatch)
    _derive_refuses(root, "noncanonical mapping-key syntax")


def test_action_run_interleaving_is_refused_after_workflow_digest_reanchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    workflow = root / sc.WORKFLOW_REL
    text = workflow.read_text("utf-8")
    setup_block = (
        f"      - uses: {SETUP_PYTHON} # v5\n"
        "        with:\n"
        "          python-version: ${{ matrix.python-version }}"
    )
    assert VERIFY in text and setup_block in text
    text = text.replace(f"      - run: {VERIFY}\n{setup_block}", setup_block + f"\n      - run: {VERIFY}")
    workflow.write_text(text, encoding="utf-8")
    _reanchor_static(root, sc.WORKFLOW_REL, monkeypatch)
    _derive_refuses(root, "action/run interleaving")


def test_isolated_verifier_ignores_sibling_stdlib_shadow(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    shadow = root / "tools/ci/json.py"
    shadow.write_text("raise SystemExit(0)\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-S", str(root / sc.VERIFIER_REL)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "SUPPLY_CHAIN_VERIFICATION_OK\n"


def test_isolated_python_m_ignores_repository_pip_shadow(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    shadow = root / "pip/__main__.py"
    shadow.parent.mkdir()
    (shadow.parent / "__init__.py").write_text("", encoding="utf-8")
    shadow.write_text('print("REPOSITORY_PIP_SHADOW_EXECUTED")\n', encoding="utf-8")
    nonisolated = subprocess.run(
        [sys.executable, "-B", "-m", "pip", "--version"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert nonisolated.returncode == 0, nonisolated.stderr
    assert nonisolated.stdout == "REPOSITORY_PIP_SHADOW_EXECUTED\n"
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pip", "--isolated", "--version"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "REPOSITORY_PIP_SHADOW_EXECUTED" not in completed.stdout


def _pytest_launcher_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONOPTIMIZE", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        environment.pop(name, None)
    environment["PYTHONPATH"] = ""
    environment["PYTHONHASHSEED"] = "0"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return environment


def _fake_launcher_python(root: Path) -> Path:
    venv = root / "launcher-venv"
    subprocess.run(
        [sys.executable, "-I", "-B", "-m", "venv", "--without-pip", str(venv)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    fake_pytest = (
        venv
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages/pytest/__init__.py"
    )
    fake_pytest.parent.mkdir(parents=True)
    fake_pytest.write_text(
        'def console_main():\n    print("pytest isolated-fixture")\n    return 0\n',
        encoding="utf-8",
    )
    return venv / "bin/python"


def test_pytest_launcher_ignores_sibling_pytest_shadow(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    launcher_python = _fake_launcher_python(root)
    shadow = root / "tools/ci/pytest.py"
    shadow.write_text('print("REPOSITORY_PYTEST_SHADOW_EXECUTED")\n', encoding="utf-8")
    completed = subprocess.run(
        [str(launcher_python), "-B", "-S", str(root / sc.PYTEST_LAUNCHER_REL), "--version"],
        cwd=root,
        env=_pytest_launcher_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "REPOSITORY_PYTEST_SHADOW_EXECUTED" not in completed.stdout
    assert completed.stdout == "pytest isolated-fixture\n"


@pytest.mark.parametrize(
    "relative_route",
    [
        "lib",
        f"lib/python{sys.version_info.major}.{sys.version_info.minor}",
        f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
    ],
)
def test_pytest_launcher_refuses_symlinked_install_route(
    tmp_path: Path, relative_route: str
) -> None:
    root = _mirror(tmp_path)
    launcher_python = _fake_launcher_python(root)
    venv_root = launcher_python.parent.parent
    route = venv_root / relative_route
    target = tmp_path / ("outside-" + relative_route.replace("/", "-"))
    route.replace(target)
    route.symlink_to(target, target_is_directory=True)
    completed = subprocess.run(
        [str(launcher_python), "-B", "-S", str(root / sc.PYTEST_LAUNCHER_REL)],
        cwd=root,
        env=_pytest_launcher_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 2
    assert "install route is not a physical directory" in completed.stderr


@pytest.mark.parametrize(
    ("key", "value", "problem"),
    [
        ("PYTHONHASHSEED", "random", "PYTHONHASHSEED must be exactly 0"),
        ("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0", "pytest plugin autoload must be disabled"),
        ("PYTHONPATH", "/hostile", "non-interpreter import path is present before admission"),
        ("PYTEST_ADDOPTS", "--collect-only", "PYTEST_ADDOPTS must be absent"),
        ("PYTEST_PLUGINS", "pytester", "PYTEST_PLUGINS must be absent"),
        ("PYTHONOPTIMIZE", "2", "Python optimization must be disabled"),
    ],
)
def test_pytest_launcher_refuses_environment_drift(
    tmp_path: Path, key: str, value: str, problem: str
) -> None:
    root = _mirror(tmp_path)
    launcher_python = _fake_launcher_python(root)
    environment = _pytest_launcher_environment()
    environment[key] = value
    completed = subprocess.run(
        [str(launcher_python), "-B", "-S", str(root / sc.PYTEST_LAUNCHER_REL), "--version"],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 2
    assert problem in completed.stderr


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        (
            "include-system-site-packages = false",
            "include-system-site-packages = true",
            "admits system site packages",
        ),
        (
            f"version = {sys.version_info.major}.{sys.version_info.minor}",
            "version = 9.9",
            "minor differs from runtime",
        ),
    ],
)
def test_pytest_launcher_refuses_pyvenv_drift(
    tmp_path: Path, old: str, new: str, problem: str
) -> None:
    root = _mirror(tmp_path)
    launcher_python = _fake_launcher_python(root)
    configuration = launcher_python.parent.parent / "pyvenv.cfg"
    text = configuration.read_text("utf-8")
    assert old in text
    configuration.write_text(text.replace(old, new, 1), encoding="utf-8")
    completed = subprocess.run(
        [str(launcher_python), "-B", "-S", str(root / sc.PYTEST_LAUNCHER_REL), "--version"],
        cwd=root,
        env=_pytest_launcher_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 2
    assert problem in completed.stderr


def test_workflow_comment_drift_is_bound(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    workflow = root / sc.WORKFLOW_REL
    workflow.write_text(workflow.read_text("utf-8") + "# drift\n", encoding="utf-8")
    _derive_refuses(root, "frozen static input digest")


@pytest.mark.parametrize(
    "relative",
    [
        sc.AGENTS_REL,
        sc.REQUIREMENTS_INPUT_REL,
        sc.LOCKS["3.10"],
        sc.LOCKS["3.11"],
        sc.PYPROJECT_REL,
    ],
)
def test_static_input_byte_drift_is_refused(tmp_path: Path, relative: str) -> None:
    root = _mirror(tmp_path)
    path = root / relative
    path.write_text(path.read_text("utf-8") + "# drift\n", encoding="utf-8")
    _derive_refuses(root, "frozen static input digest")


@pytest.mark.parametrize(
    "relative",
    [
        sc.VERIFIER_REL,
        sc.KNOWN_BADS_REL,
        sc.PYTEST_LAUNCHER_REL,
        sc.INSTALL_VERIFIER_REL,
        sc.INSTALL_KNOWN_BADS_REL,
        sc.LAUNCHER_KNOWN_BADS_REL,
    ],
)
def test_self_control_byte_drift_requires_manifest_rebinding(
    tmp_path: Path, relative: str
) -> None:
    root = _mirror(tmp_path)
    path = root / relative
    path.write_text(path.read_text("utf-8") + "# drift\n", encoding="utf-8")
    assert sc.verify(root) == ["supply_chain:manifest_drift"]


def test_missing_bound_file_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    (root / sc.REQUIREMENTS_INPUT_REL).unlink()
    assert any("file cannot be stated" in problem for problem in sc.verify(root))


def test_symlinked_bound_file_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    lock = root / sc.LOCKS["3.10"]
    target = root / "outside.lock"
    target.write_bytes(lock.read_bytes())
    lock.unlink()
    lock.symlink_to(target)
    assert any("not a physical regular file" in problem for problem in sc.verify(root))


def test_missing_manifest_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    (root / sc.MANIFEST_REL).unlink()
    assert any("manifest" in problem for problem in sc.verify(root))


def test_duplicate_manifest_key_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    manifest = root / sc.MANIFEST_REL
    text = manifest.read_text("utf-8")
    manifest.write_text(text.replace("{\n", '{\n  "schema": "shadow",\n', 1), encoding="utf-8")
    problems = sc.verify(root)
    assert any("duplicate JSON key: schema" in problem for problem in problems)


def test_semantically_equal_noncanonical_manifest_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    manifest = root / sc.MANIFEST_REL
    document = json.loads(manifest.read_text("utf-8"))
    manifest.write_text(json.dumps(document, separators=(",", ":")), encoding="utf-8")
    problems = sc.verify(root)
    assert any("not canonical JSON" in problem for problem in problems)


@pytest.mark.parametrize("replacement", ["[]\n", "true\n", "1\n"])
def test_manifest_root_type_impostor_is_refused(tmp_path: Path, replacement: str) -> None:
    root = _mirror(tmp_path)
    (root / sc.MANIFEST_REL).write_text(replacement, encoding="utf-8")
    assert sc.verify(root)


def test_unknown_manifest_field_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    manifest = root / sc.MANIFEST_REL
    document = json.loads(manifest.read_text("utf-8"))
    document["authority"] = True
    manifest.write_bytes(sc._canonical(document))
    assert sc.verify(root) == ["supply_chain:manifest_drift"]


def test_lock_unpinned_requirement_is_refused_even_if_static_digest_is_reanchored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.LOCKS["3.10"]
    _replace(root, relative, "pytest==9.1.1", "pytest>=9.1.1")
    monkeypatch.setitem(sc.EXPECTED_STATIC_SHA256, relative, sc._sha256_bytes((root / relative).read_bytes()))
    _derive_refuses(root, "unpinned or malformed row")


def test_lock_missing_hash_is_refused_even_if_static_digest_is_reanchored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.LOCKS["3.10"]
    path = root / relative
    text = path.read_text("utf-8")
    block_start = text.index("exceptiongroup==1.3.1")
    block_end = text.index("\niniconfig==", block_start)
    block = text[block_start:block_end]
    hashless_block = "\n".join(
        line for line in block.splitlines() if "--hash=sha256:" not in line
    )
    path.write_text(
        text[:block_start] + hashless_block + text[block_end:], encoding="utf-8"
    )
    monkeypatch.setitem(sc.EXPECTED_STATIC_SHA256, relative, sc._sha256_bytes(path.read_bytes()))
    _derive_refuses(root, "lacks exact SHA-256 hashes|unrecognized continuation")


def test_lock_unknown_indented_option_is_refused_after_reanchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.LOCKS["3.10"]
    path = root / relative
    text = path.read_text("utf-8")
    marker = "    # via pytest"
    assert marker in text
    path.write_text(text.replace(marker, "    --trusted-host hostile.invalid\n" + marker, 1))
    monkeypatch.setitem(sc.EXPECTED_STATIC_SHA256, relative, sc._sha256_bytes(path.read_bytes()))
    _derive_refuses(root, "unrecognized continuation")


def test_lock_preamble_option_is_refused_after_reanchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.LOCKS["3.10"]
    path = root / relative
    path.write_text(
        "    --extra-index-url https://hostile.invalid/simple\n"
        + path.read_text("utf-8"),
        encoding="utf-8",
    )
    _reanchor_static(root, relative, monkeypatch)
    _derive_refuses(root, "unrecognized preamble")


def test_direct_requirement_version_drift_is_refused_after_reanchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.LOCKS["3.10"]
    _replace(root, relative, "numpy==2.2.6", "numpy==2.2.5")
    path = root / relative
    monkeypatch.setitem(sc.EXPECTED_STATIC_SHA256, relative, sc._sha256_bytes(path.read_bytes()))
    _derive_refuses(root, "direct package versions differ")


def test_requirement_input_floating_constraint_is_refused_after_reanchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _mirror(tmp_path)
    relative = sc.REQUIREMENTS_INPUT_REL
    _replace(root, relative, "pytest==9.1.1", "pytest")
    path = root / relative
    monkeypatch.setitem(sc.EXPECTED_STATIC_SHA256, relative, sc._sha256_bytes(path.read_bytes()))
    _derive_refuses(root, "requirements input differs")


def test_resealed_nonpolicy_bound_file_change_replays_but_needs_external_receipt(
    tmp_path: Path
) -> None:
    root = _mirror(tmp_path)
    verifier = root / sc.VERIFIER_REL
    verifier.write_text(verifier.read_text("utf-8") + "# reviewed candidate change\n")
    _reseal(root)
    assert sc.verify(root) == []
    assert "independently accepted commit/receipt" in sc.LIMITATIONS[4]


def test_lock_inventory_is_exactly_pinned_and_hashed() -> None:
    document = sc.derive(REPO)
    for version, expected_direct in sc.EXPECTED_DIRECT_PACKAGES.items():
        packages = {
            row["name"]: row for row in document["locks"][version]["packages"]
        }
        assert packages
        assert all(row["hash_count"] > 0 for row in packages.values())
        assert all(row["version"] for row in packages.values())
        for name, expected in expected_direct.items():
            assert packages[name]["version"] == expected
