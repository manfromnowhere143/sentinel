"""Iteration 55 HUGSIM source-map analyzer tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path

EXP = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter55_hugsim_collision_instrumentation_source_audit"
)

spec = importlib.util.spec_from_file_location("analyze_source_map", EXP / "analyze_source_map.py")
az = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = az
spec.loader.exec_module(az)


def run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def init_repo(tmp_path: Path, source: str) -> tuple[Path, str]:
    root = tmp_path / "HUGSIM"
    root.mkdir()
    (root / "metrics").mkdir()
    (root / "metrics" / "score.py").write_text(source)
    run(["git", "init"], root)
    run(["git", "config", "user.email", "test@example.com"], root)
    run(["git", "config", "user.name", "Sentinel Test"], root)
    run(["git", "remote", "add", "origin", "https://token@example.com/hyzhou404/HUGSIM"], root)
    run(["git", "add", "."], root)
    run(["git", "commit", "-m", "fixture"], root)
    return root, run(["git", "rev-parse", "HEAD"], root)


def test_redacts_https_remote_credentials():
    assert (
        az.redact_remote_url("https://token@example.com/hyzhou404/HUGSIM.git")
        == "https://example.com/hyzhou404/HUGSIM.git"
    )


def test_redacts_ssh_remote_identity():
    assert (
        az.redact_remote_url("git@github.com:hyzhou404/HUGSIM.git")
        == "github.com/hyzhou404/HUGSIM.git"
    )


def test_source_map_complete_on_co_located_metric_geometry_identity(tmp_path):
    source = """
import json


def evaluate_episode(objects):
    metrics = {"hdscore": 1.0, "nc": 1.0, "pdms": 1.0, "dac": 1.0, "ttc": 1.0}
    for object_row in objects:
        bbox = object_row["bbox"]
        distance = bbox.distance_to_ego()
        if distance < 0.5:
            metrics["nc"] = 0.0
            metrics["collision_actor_id"] = object_row["track_id"]
    with open("eval.json", "w") as out:
        json.dump(metrics, out)
"""
    root, head = init_repo(tmp_path, source)
    report = az.run_analysis(
        root,
        tmp_path / "report.json",
        tmp_path / "report.md",
        expected_sha=head,
        max_files=10,
    )
    assert report["verdict"] == az.COMPLETE_VERDICT
    assert report["labels"]["metric_source_identified"] is True
    assert report["labels"]["collision_geometry_source_identified"] is True
    assert report["labels"]["actor_identity_available_in_source"] is True
    assert report["labels"]["instrumentation_point_supported"] is True
    assert report["repository_identity"]["remotes"][0]["url"] == "https://example.com/hyzhou404/HUGSIM"


def test_sha_mismatch_forces_null(tmp_path):
    root, _head = init_repo(tmp_path, 'open("eval.json", "w").write("{}")\n')
    report = az.run_analysis(
        root,
        tmp_path / "report.json",
        tmp_path / "report.md",
        expected_sha="deadbeef",
        max_files=10,
    )
    assert report["verdict"] == az.NULL_VERDICT
    assert report["labels"]["source_map_insufficient"] is True
    assert any(problem.startswith("sha_mismatch:") for problem in report["problems"])


def test_missing_metric_path_is_insufficient(tmp_path):
    root, head = init_repo(tmp_path, "def helper(vehicle):\n    return vehicle.name\n")
    report = az.run_analysis(
        root,
        tmp_path / "report.json",
        tmp_path / "report.md",
        expected_sha=head,
        max_files=10,
    )
    assert report["verdict"] == az.NULL_VERDICT
    assert report["labels"]["metric_source_identified"] is False
    assert report["labels"]["source_map_insufficient"] is True
