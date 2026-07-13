"""Iteration 57 refined HUGSIM patch guard tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path

EXP = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter57_hugsim_patch_guard_refinement"
)

spec = importlib.util.spec_from_file_location("verify_refined_guard", EXP / "verify_refined_guard.py")
vr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = vr
spec.loader.exec_module(vr)


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


def write_patch(repo: Path, patch_path: Path, body: str) -> str:
    (repo / "sim" / "utils" / "score_calculator.py").write_text(body)
    diff = run(["git", "diff"], repo) + "\n"
    patch_path.write_text(diff)
    return vr.sha256(patch_path)


def good_body() -> str:
    return (
        "class ScoreCalculator:\n"
        "    collision_provenance = []\n"
        "\n"
        "    def _calculate_no_collision_provenance(self):\n"
        "        score_nc = 0.0\n"
        "        if score_nc == 0.0:\n"
        "            return {'source': 'nc', 'contact_distance': 0.0}\n"
        "\n"
        "final_score_dict = {}\n"
        "final_score_dict['collision_provenance'] = ScoreCalculator.collision_provenance\n"
    )


def test_refined_guard_allows_read_only_score_comparison(tmp_path):
    repo, _head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    write_patch(repo, patch, good_body())
    summary = vr.parse_patch(patch.read_text())
    guard = vr.guard_patch(summary)
    assert guard["metric_assignment_guard_passed"] is False

    # Remove the fixture assignment; the comparison itself must not be what fails.
    comparison_only = patch.read_text().replace("+        score_nc = 0.0\n", "")
    summary = vr.parse_patch(comparison_only)
    guard = vr.guard_patch(summary)
    assert guard["metric_assignment_guard_passed"] is True
    assert guard["required_provenance_fields_present"] is True


def test_full_refined_verifier_accepts_byte_bound_patch(tmp_path):
    repo, head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    patch_sha = write_patch(repo, patch, good_body().replace("        score_nc = 0.0\n", ""))
    run(["git", "checkout", "--", "sim/utils/score_calculator.py"], repo)
    report = vr.build_report(repo, patch, head, patch_sha, work_root=tmp_path / "work")
    assert report["verdict"] == vr.COMPLETE_VERDICT
    assert report["labels"]["patch_sha_match"] is True
    assert report["labels"]["metric_assignment_guard_passed"] is True
    assert report["labels"]["python_compile_passed"] is True


def test_refined_guard_rejects_metric_assignment(tmp_path):
    repo, _head = init_repo(tmp_path)
    patch = tmp_path / "bad.patch"
    write_patch(repo, patch, good_body())
    summary = vr.parse_patch(patch.read_text())
    guard = vr.guard_patch(summary)
    assert guard["metric_assignment_guard_passed"] is False
    assert any("score_nc = 0.0" in problem for problem in guard["problems"])


def test_patch_sha_mismatch_forces_null(tmp_path):
    repo, head = init_repo(tmp_path)
    patch = tmp_path / "good.patch"
    write_patch(repo, patch, good_body().replace("        score_nc = 0.0\n", ""))
    run(["git", "checkout", "--", "sim/utils/score_calculator.py"], repo)
    report = vr.build_report(repo, patch, head, "deadbeef", work_root=tmp_path / "work")
    assert report["verdict"] == vr.NULL_VERDICT
    assert report["labels"]["patch_sha_match"] is False
    assert any(problem.startswith("patch_sha_mismatch:") for problem in report["problems"])
