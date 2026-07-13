"""Iteration 56 HUGSIM provenance patch verifier tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path

EXP = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter56_hugsim_provenance_instrumentation_patch"
)

spec = importlib.util.spec_from_file_location("verify_patch", EXP / "verify_patch.py")
vp = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = vp
spec.loader.exec_module(vp)


def run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "HUGSIM"
    (root / "sim" / "utils").mkdir(parents=True)
    (root / "sim" / "utils" / "score_calculator.py").write_text(
        "class ScoreCalculator:\n"
        "    pass\n"
        "\n"
        "final_score_dict = {}\n"
    )
    run(["git", "init"], root)
    run(["git", "config", "user.email", "test@example.com"], root)
    run(["git", "config", "user.name", "Sentinel Test"], root)
    run(["git", "add", "."], root)
    run(["git", "commit", "-m", "fixture"], root)
    return root, run(["git", "rev-parse", "HEAD"], root)


def write_good_patch(repo: Path, patch_path: Path) -> None:
    target = repo / "sim" / "utils" / "score_calculator.py"
    target.write_text(
        "class ScoreCalculator:\n"
        "    collision_provenance = []\n"
        "\n"
        "    def _calculate_no_collision_provenance(self):\n"
        "        return {'source': 'nc', 'contact_distance': 0.0}\n"
        "\n"
        "final_score_dict = {}\n"
        "final_score_dict['collision_provenance'] = ScoreCalculator.collision_provenance\n"
    )
    patch_path.write_text(run(["git", "diff"], repo) + "\n")


def test_guard_accepts_required_additive_patch(tmp_path):
    repo, _head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    write_good_patch(repo, patch)
    summary = vp.parse_patch(patch.read_text())
    guard = vp.guard_patch(summary)
    assert summary.changed_files == ["sim/utils/score_calculator.py"]
    assert guard["changed_files_allowed"] is True
    assert guard["required_provenance_fields_present"] is True
    assert guard["metric_control_guard_passed"] is True


def test_full_verifier_accepts_clean_static_patch(tmp_path):
    repo, head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    write_good_patch(repo, patch)
    run(["git", "checkout", "--", "sim/utils/score_calculator.py"], repo)
    report = vp.build_report(repo, patch, head, work_root=tmp_path / "work")
    assert report["verdict"] == vp.COMPLETE_VERDICT
    assert report["labels"]["patch_applies_cleanly"] is True
    assert report["labels"]["python_compile_passed"] is True


def test_guard_rejects_metric_formula_change(tmp_path):
    repo, _head = init_repo(tmp_path)
    target = repo / "sim" / "utils" / "score_calculator.py"
    target.write_text(
        "score_pdms = 0.0\n"
        "collision_provenance = []\n"
        "def _calculate_no_collision_provenance():\n"
        "    return {'source': 'nc', 'contact_distance': 0.0}\n"
        "final_score_dict = {}\n"
        "final_score_dict['collision_provenance'] = collision_provenance\n"
    )
    summary = vp.parse_patch(run(["git", "diff"], repo))
    guard = vp.guard_patch(summary)
    assert guard["metric_control_guard_passed"] is False
    assert any("score_pdms =" in problem for problem in guard["problems"])


def test_sha_mismatch_forces_null(tmp_path):
    repo, _head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    write_good_patch(repo, patch)
    run(["git", "checkout", "--", "sim/utils/score_calculator.py"], repo)
    report = vp.build_report(repo, patch, "deadbeef", work_root=tmp_path / "work")
    assert report["verdict"] == vp.NULL_VERDICT
    assert report["labels"]["source_sha_match"] is False
    assert any(problem.startswith("sha_mismatch:") for problem in report["problems"])
