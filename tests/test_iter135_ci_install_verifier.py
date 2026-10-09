"""Hostile controls for the independent CI installation verifier."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools/ci/verify_ci_install.py"
HASH_A = "a" * 64
HASH_B = "b" * 64


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_ci_install", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ci = _load_module()


def _lock() -> str:
    return (
        "alpha_pkg==1.2.3 \\\n"
        f"    --hash=sha256:{HASH_A}\n"
        "beta-pkg==4.5.6 \\\n"
        f"    --hash=sha256:{HASH_B}\n"
    )


def _item(name: str, version: str, archive_hash: str) -> dict[str, object]:
    return {
        "download_info": {
            "url": f"https://packages.invalid/{name}.whl",
            "archive_info": {
                "hash": f"sha256={archive_hash}",
                "hashes": {"sha256": archive_hash},
            },
        },
        "is_direct": False,
        "is_yanked": False,
        "requested": True,
        "metadata": {"name": name, "version": version},
    }


def _report() -> dict[str, object]:
    return {
        "version": "1",
        "pip_version": "25.3",
        "install": [
            _item("alpha-pkg", "1.2.3", HASH_A),
            _item("beta-pkg", "4.5.6", HASH_B),
        ],
        "environment": {"python_version": "3.10"},
    }


def _write_fixture(
    root: Path,
    *,
    lock_text: str | None = None,
    report: object | None = None,
) -> tuple[Path, Path]:
    lock_path = root / "requirements.lock"
    report_path = root / "report.json"
    lock_path.write_text(lock_text if lock_text is not None else _lock(), encoding="utf-8")
    report_path.write_text(
        json.dumps(_report() if report is None else report, indent=2) + "\n",
        encoding="utf-8",
    )
    return lock_path, report_path


def _records(*extra: tuple[str, str]):
    return [
        ("alpha-pkg", "1.2.3"),
        ("beta_pkg", "4.5.6"),
        ("pip", "25.3"),
        *extra,
    ]


def _verify(
    lock_path: Path,
    report_path: Path,
    records=None,
    *,
    expected_minor: str = "3.10",
    runtime_minor: str = "3.10",
) -> str:
    selected = _records() if records is None else records
    return ci.verify_ci_install(
        lock_path,
        report_path,
        expected_minor,
        runtime_python_minor=runtime_minor,
        inventory_loader=lambda _paths: selected,
        install_paths=(lock_path.parent,),
    )


def test_positive_reconciliation_reports_bootstrap_as_unbound(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    assert _verify(lock_path, report_path) == (
        "CI_INSTALL_VERIFICATION_OK python=3.10 locked_packages=2 "
        "unbound_bootstrap=pip==25.3"
    )


def test_report_missing_package_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"] = report["install"][:-1]
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="missing locked packages: beta-pkg"):
        _verify(lock_path, report_path)


def test_report_extra_package_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"].append(_item("gamma", "1", "c" * 64))
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="report contains extra packages: gamma"):
        _verify(lock_path, report_path)


def test_report_duplicate_normalized_package_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"].append(_item("alpha_pkg", "1.2.3", HASH_A))
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="duplicate package: alpha-pkg"):
        _verify(lock_path, report_path)


def test_report_version_drift_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["metadata"]["version"] = "1.2.4"
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="version differs from lock: alpha-pkg"):
        _verify(lock_path, report_path)


def test_report_wrong_archive_hash_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0] = _item("alpha-pkg", "1.2.3", "c" * 64)
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="SHA-256 is not admitted: alpha-pkg"):
        _verify(lock_path, report_path)


def test_report_sdist_with_admitted_hash_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["download_info"]["url"] = (
        "https://packages.invalid/alpha_pkg-1.2.3.tar.gz"
    )
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="not an admitted wheel URL"):
        _verify(lock_path, report_path)


def test_report_direct_url_semantics_are_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["is_direct"] = True
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="direct URL outside"):
        _verify(lock_path, report_path)


@pytest.mark.parametrize("requested_extras", [[], ["feature"]])
def test_report_requested_extras_field_is_refused(
    tmp_path: Path, requested_extras: list[str]
) -> None:
    report = _report()
    report["install"][0]["requested_extras"] = requested_extras
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="requested extras outside"):
        _verify(lock_path, report_path)


def test_already_installed_without_download_evidence_is_refused(tmp_path: Path) -> None:
    report = _report()
    del report["install"][0]["download_info"]
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="force-reinstall was not evidenced"):
        _verify(lock_path, report_path)


def test_already_installed_empty_report_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"] = []
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="missing locked packages"):
        _verify(lock_path, report_path)


def test_lock_version_drift_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(
        tmp_path, lock_text=_lock().replace("alpha_pkg==1.2.3", "alpha_pkg==1.2.4")
    )
    with pytest.raises(ci.InstallVerificationError, match="version differs from lock: alpha-pkg"):
        _verify(lock_path, report_path)


def test_lock_hash_drift_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(
        tmp_path, lock_text=_lock().replace(HASH_A, "c" * 64)
    )
    with pytest.raises(ci.InstallVerificationError, match="SHA-256 is not admitted: alpha-pkg"):
        _verify(lock_path, report_path)


def test_malformed_json_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    report_path.write_text("{\n", encoding="utf-8")
    with pytest.raises(ci.InstallVerificationError, match="malformed JSON"):
        _verify(lock_path, report_path)


def test_duplicate_json_key_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    report_path.write_text(
        '{"version":"1","version":"1","pip_version":"25.3",'
        '"install":[],"environment":{"python_version":"3.10"}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ci.InstallVerificationError, match="duplicate JSON key: version"):
        _verify(lock_path, report_path)


def test_report_install_wrong_type_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"] = {}
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="install is not a list"):
        _verify(lock_path, report_path)


def test_report_metadata_version_wrong_type_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["metadata"]["version"] = 123
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="version is not a string"):
        _verify(lock_path, report_path)


def test_report_boolean_wrong_type_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["requested"] = 1
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="requested is not a boolean"):
        _verify(lock_path, report_path)


def test_report_transitive_resolution_item_is_refused(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["requested"] = False
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="not explicitly requested"):
        _verify(lock_path, report_path)


def test_report_archive_hash_fields_must_agree(tmp_path: Path) -> None:
    report = _report()
    report["install"][0]["download_info"]["archive_info"]["hash"] = "sha256=" + "c" * 64
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="SHA-256 fields disagree"):
        _verify(lock_path, report_path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_is_refused(tmp_path: Path, constant: str) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    report_path.write_text(
        '{"version":"1","pip_version":"25.3","install":[],'
        f'"environment":{{"python_version":"3.10","bad":{constant}}}}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ci.InstallVerificationError, match="non-finite JSON number"):
        _verify(lock_path, report_path)


def test_inventory_missing_package_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    with pytest.raises(ci.InstallVerificationError, match="missing locked package: beta-pkg"):
        _verify(lock_path, report_path, [("alpha-pkg", "1.2.3")])


def test_inventory_version_drift_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    records = [("alpha-pkg", "1.2.4"), ("beta-pkg", "4.5.6")]
    with pytest.raises(ci.InstallVerificationError, match="installed version differs"):
        _verify(lock_path, report_path, records)


def test_inventory_extra_nonbootstrap_package_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    with pytest.raises(ci.InstallVerificationError, match="extra packages: gamma"):
        _verify(lock_path, report_path, _records(("gamma", "1")))


def test_inventory_duplicate_normalized_package_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    with pytest.raises(ci.InstallVerificationError, match="duplicate package: alpha-pkg"):
        _verify(lock_path, report_path, _records(("alpha_pkg", "1.2.3")))


def test_bootstrap_version_cannot_break_stable_output_line(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    records = [("alpha-pkg", "1.2.3"), ("beta-pkg", "4.5.6"), ("pip", "25.3\nbad")]
    with pytest.raises(ci.InstallVerificationError, match="version is malformed"):
        _verify(lock_path, report_path, records)


def test_all_explicit_bootstrap_packages_are_reported_unbound(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    records = _records(("setuptools", "80.0"), ("wheel", "1.0"))
    assert _verify(lock_path, report_path, records).endswith(
        "unbound_bootstrap=pip==25.3,setuptools==80.0,wheel==1.0"
    )


def test_report_producer_pip_must_match_installed_bootstrap(tmp_path: Path) -> None:
    report = _report()
    report["pip_version"] = "25.2"
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="pip version differs"):
        _verify(lock_path, report_path)


def test_report_producer_pip_must_exist_in_inventory(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    with pytest.raises(ci.InstallVerificationError, match="missing report-producing pip"):
        _verify(
            lock_path,
            report_path,
            [("alpha-pkg", "1.2.3"), ("beta-pkg", "4.5.6")],
        )


def test_cli_runtime_and_report_python_minor_must_agree(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    with pytest.raises(ci.InstallVerificationError, match="differs from runtime"):
        _verify(lock_path, report_path, expected_minor="3.11")
    report = _report()
    report["environment"]["python_version"] = "3.11"
    lock_path, report_path = _write_fixture(tmp_path, report=report)
    with pytest.raises(ci.InstallVerificationError, match="differs from report"):
        _verify(lock_path, report_path)


def test_symlinked_report_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    target = tmp_path / "target.json"
    report_path.replace(target)
    report_path.symlink_to(target)
    with pytest.raises(ci.InstallVerificationError, match="physical file"):
        _verify(lock_path, report_path)


def test_symlinked_lock_is_refused(tmp_path: Path) -> None:
    lock_path, report_path = _write_fixture(tmp_path)
    target = tmp_path / "target.lock"
    lock_path.replace(target)
    lock_path.symlink_to(target)
    with pytest.raises(ci.InstallVerificationError, match="physical file"):
        _verify(lock_path, report_path)


def test_duplicate_normalized_lock_package_is_refused(tmp_path: Path) -> None:
    duplicate = _lock() + "alpha-pkg==1.2.3 \\\n" + f"    --hash=sha256:{HASH_A}\n"
    lock_path, report_path = _write_fixture(tmp_path, lock_text=duplicate)
    with pytest.raises(ci.InstallVerificationError, match="duplicate package: alpha-pkg"):
        _verify(lock_path, report_path)


def _fake_venv(root: Path, minor: str = "3.10") -> tuple[Path, Path]:
    venv_root = root / ".venv-ci"
    bin_directory = venv_root / "bin"
    site_packages = venv_root / "lib" / f"python{minor}" / "site-packages"
    bin_directory.mkdir(parents=True)
    site_packages.mkdir(parents=True)
    executable = bin_directory / "python"
    executable.write_bytes(b"placeholder")
    (venv_root / "pyvenv.cfg").write_text(
        "home = /external/python\n"
        "include-system-site-packages = false\n"
        f"version = {minor}.19\n",
        encoding="utf-8",
    )
    return executable, site_packages


def test_venv_install_path_is_derived_from_executable_not_sys_prefix(tmp_path: Path) -> None:
    executable, site_packages = _fake_venv(tmp_path)
    assert ci._venv_install_paths("3.10", executable) == (site_packages,)


def test_venv_with_system_site_packages_is_refused(tmp_path: Path) -> None:
    executable, _site_packages = _fake_venv(tmp_path)
    config = executable.parent.parent / "pyvenv.cfg"
    config.write_text(
        config.read_text("utf-8").replace(
            "include-system-site-packages = false",
            "include-system-site-packages = true",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ci.InstallVerificationError, match="exclude system site-packages"):
        ci._venv_install_paths("3.10", executable)


def test_pyvenv_minor_drift_is_refused(tmp_path: Path) -> None:
    executable, _site_packages = _fake_venv(tmp_path, "3.11")
    with pytest.raises(ci.InstallVerificationError, match="minor differs from CLI"):
        ci._venv_install_paths("3.10", executable)


def test_symlinked_pyvenv_config_is_refused(tmp_path: Path) -> None:
    executable, _site_packages = _fake_venv(tmp_path)
    config = executable.parent.parent / "pyvenv.cfg"
    target = executable.parent.parent / "real.cfg"
    config.replace(target)
    config.symlink_to(target)
    with pytest.raises(ci.InstallVerificationError, match="physical file"):
        ci._venv_install_paths("3.10", executable)


@pytest.mark.parametrize(
    "relative_route",
    ["lib", "lib/python3.10", "lib/python3.10/site-packages"],
)
def test_symlinked_venv_install_route_is_refused(
    tmp_path: Path, relative_route: str
) -> None:
    executable, _site_packages = _fake_venv(tmp_path)
    venv_root = executable.parent.parent
    route = venv_root / relative_route
    target = tmp_path / ("outside-" + relative_route.replace("/", "-"))
    route.replace(target)
    route.symlink_to(target, target_is_directory=True)
    with pytest.raises(ci.InstallVerificationError, match="install route is not a physical"):
        ci._venv_install_paths("3.10", executable)


def test_default_inventory_reads_only_explicit_venv_site_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable, site_packages = _fake_venv(tmp_path)
    observed: list[list[str]] = []

    class FakeDistribution:
        def __init__(self, name: str, version: str):
            self.metadata = {"Name": name}
            self.version = version

    def distributions(*, path):
        observed.append(path)
        return [FakeDistribution("alpha-pkg", "1.2.3")]

    monkeypatch.setattr(ci.metadata, "distributions", distributions)
    admitted = ci._venv_install_paths("3.10", executable)
    assert admitted == (site_packages,)
    assert list(ci._installed_records(admitted)) == [("alpha-pkg", "1.2.3")]
    assert observed == [[str(site_packages)]]


@pytest.mark.parametrize("minor", ["3.10", "3.11"])
def test_real_without_pip_venv_is_discovered_under_no_site(tmp_path: Path, minor: str) -> None:
    interpreter = shutil.which(f"python{minor}")
    if interpreter is None:
        pytest.skip(f"python{minor} is unavailable")
    venv_root = tmp_path / minor / ".venv-ci"
    completed = subprocess.run(
        [interpreter, "-m", "venv", "--without-pip", str(venv_root)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    code = (
        "import importlib.util,pathlib,sys;"
        f"p=pathlib.Path({str(MODULE_PATH)!r});"
        "s=importlib.util.spec_from_file_location('ci_install_probe',p);"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);"
        f"print(m._venv_install_paths({minor!r})[0])"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment["PYTHONPATH"] = ""
    probed = subprocess.run(
        [str(venv_root / "bin" / "python"), "-I", "-B", "-S", "-c", code],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert probed.returncode == 0, probed.stderr
    expected = venv_root / "lib" / f"python{minor}" / "site-packages"
    assert probed.stdout == f"{expected}\n"
