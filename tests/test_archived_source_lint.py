from pathlib import Path
import shutil
import subprocess

import pytest

from tools.ci import verify_supply_chain as sc


def test_archived_source_corruption_is_rejected_before_lint(tmp_path: Path) -> None:
    for relative in sc.BOUND_FILES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((sc.ROOT / relative).read_bytes())
    target = tmp_path / sc.ARCHIVED_SOURCE_FILES[0]
    target.write_bytes(target.read_bytes() + b"\n# corrupted archived evidence\n")
    with pytest.raises(sc.SupplyChainError, match="frozen static input digest"):
        sc.derive(tmp_path)


def test_only_exact_archived_paths_are_excluded(tmp_path: Path) -> None:
    shutil.copyfile(sc.ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    archived = tmp_path / sc.ARCHIVED_SOURCE_FILES[0]
    archived.parent.mkdir(parents=True)
    archived.write_text("undefined_archived_name\n")
    command = [shutil.which("ruff") or "ruff", "check", "--no-cache", "."]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    maintained = archived.with_name("new_maintained_source.py")
    maintained.write_text("undefined_maintained_name\n")
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert "undefined_maintained_name" in result.stdout
    assert "undefined_archived_name" not in result.stdout
