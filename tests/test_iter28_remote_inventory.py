from __future__ import annotations

import importlib.util
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter28_nuscenes_trainval_staging/run_remote_inventory.py"


def load_remote_inventory_module():
    spec = importlib.util.spec_from_file_location("iter28_remote_inventory", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_required_file_manifest_names_committed_firewall_inputs():
    module = load_remote_inventory_module()

    paths = {entry["path"] for entry in module.required_file_manifest()}

    assert "experiments/iter28_nuscenes_trainval_staging/bounded_inventory.py" in paths
    assert "experiments/iter25_staged_data_inventory/inventory_roots.py" in paths
    assert "experiments/iter22_causal_planner_interpretability/official_train_scenes.txt" in paths
    assert "experiments/iter24_risk_support_atlas/availability_manifest.exclusions.txt" in paths


def test_safe_extract_result_rejects_path_traversal(tmp_path):
    module = load_remote_inventory_module()
    result_tgz = tmp_path / "bad.tgz"
    evil = tmp_path / "evil.txt"
    evil.write_text("bad")
    with tarfile.open(result_tgz, "w:gz") as tf:
        tf.add(evil, arcname="../evil.txt")

    with pytest.raises(SystemExit, match="unsafe inventory result member"):
        module.safe_extract_result(result_tgz, tmp_path / "out")


def test_safe_extract_result_accepts_repo_relative_proof_dir(tmp_path):
    module = load_remote_inventory_module()
    result_tgz = tmp_path / "proof.tgz"
    proof_dir = (
        tmp_path
        / "bundle"
        / "experiments"
        / "iter28_nuscenes_trainval_staging"
        / "proof-inventory"
    )
    proof_dir.mkdir(parents=True)
    (proof_dir / "availability_inventory.command.txt").write_text("cmd\n")
    with tarfile.open(result_tgz, "w:gz") as tf:
        tf.add(tmp_path / "bundle" / "experiments", arcname="experiments")

    out = tmp_path / "out"
    module.safe_extract_result(result_tgz, out)

    assert (out / "availability_inventory.command.txt").read_text() == "cmd\n"
