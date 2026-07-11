from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter46_hugsim_off_baseline"
ANALYZER = EXP / "analyze_off_baseline.py"
D0 = EXP / "d0_compare.py"
RUN_SH = EXP / "run_off_baseline.sh"
HYPOTHESIS = EXP / "HYPOTHESIS.md"
SHIM = EXP / "shim/sitecustomize.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load(ANALYZER, "iter46_analyzer")
d0mod = load(D0, "iter46_d0")


def write_episode(root: Path, scenario: str, run: int, *, hdscore=0.5, steps=15,
                  attempt=1, output_txt=True):
    ep = root / f"{scenario}__r{run}"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(
        {"hdscore": hdscore, "nc": 1.0, "dac": 1.0, "ttc": 1.0, "comfort": 1.0, "rc": hdscore}))
    (ep / "episode_meta.json").write_text(json.dumps(
        {"scenario": scenario, "run": run, "attempt": attempt, "rc": 0, "steps": steps}))
    if output_txt:
        (ep / "output.txt").write_text("".join(f"received\nsent {i:04d}\n" for i in range(steps)))
    return ep


def write_d0(root: Path, verdict: str):
    (root / "d0_comparison.json").write_text(json.dumps({"verdict": verdict}))


def test_frozen_scenario_list_is_52_lexicographic_easy_medium():
    assert len(analyzer.SCENARIOS) == 52
    assert analyzer.SCENARIOS == sorted(analyzer.SCENARIOS)
    assert all(("-easy-" in s) or ("-medium-" in s) for s in analyzer.SCENARIOS)
    assert sum(1 for s in analyzer.SCENARIOS if "-easy-" in s) == 18
    assert sum(1 for s in analyzer.SCENARIOS if "-medium-" in s) == 34
    assert analyzer.SCENARIOS[0] == "scene-0013-easy-00"
    assert len(analyzer.STOCHASTIC_SUBSET) == 26


def test_scenario_list_matches_run_script_manifest_and_hypothesis():
    run_sh = RUN_SH.read_text()
    hyp = HYPOTHESIS.read_text()
    for s in analyzer.SCENARIOS:
        assert f"{s}.yaml" in run_sh
        assert f"{s}.yaml" in hyp
    # frozen provenance constants appear in both the pre-registration and the run script
    for sha in (
        "62c690d39fd90020e68a196bd8bcc1c4d4191f2e",
        "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
        "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
        "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c",
        "f73ef3884063",
    ):
        assert sha in run_sh and sha in hyp
    assert "I46_OFF_ALL_DONE" in run_sh


def test_shim_byte_copy_matches_frozen_sha():
    import hashlib

    digest = hashlib.sha256(SHIM.read_bytes()).hexdigest()
    assert digest == "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c"


def test_schedule_deterministic_and_stochastic_branches():
    det = analyzer.scheduled_episodes("deterministic")
    assert len(det) == 52 and all(r == 1 for _, r in det)
    sto = analyzer.scheduled_episodes("stochastic")
    assert len(sto) == 52
    assert {s for s, _ in sto} == set(analyzer.SCENARIOS[:26])
    assert all(sto.count((s, r)) == 1 for s, r in sto)


def test_deterministic_happy_path_passes(tmp_path):
    write_d0(tmp_path, "deterministic")
    for s in analyzer.SCENARIOS:
        write_episode(tmp_path, s, 1, hdscore=0.4)
    report = analyzer.analyze(tmp_path)
    assert report["bars"] == {"C1_all_episodes_complete": True, "C2_per_step_logs": True}
    assert report["verdict"] == "PASS_BARS_MET"
    assert report["completion"]["complete"] == 52
    assert abs(report["hdscore"]["mean"] - 0.4) < 1e-12
    assert report["hdscore"]["per_tier_mean"]["easy"] is not None


def test_missing_episode_fails_c1(tmp_path):
    write_d0(tmp_path, "deterministic")
    for s in analyzer.SCENARIOS[:-1]:
        write_episode(tmp_path, s, 1)
    report = analyzer.analyze(tmp_path)
    assert report["bars"]["C1_all_episodes_complete"] is False
    assert report["verdict"] == "NULL_COMPLETION_BAR_FAILED"
    assert report["completion"]["incomplete"][0]["reason"] == "missing"


def test_non_finite_hdscore_fails(tmp_path):
    write_d0(tmp_path, "deterministic")
    for s in analyzer.SCENARIOS:
        write_episode(tmp_path, s, 1)
    bad = tmp_path / f"{analyzer.SCENARIOS[3]}__r1" / "eval.json"
    bad.write_text(json.dumps({"hdscore": "nan-ish"}))
    report = analyzer.analyze(tmp_path)
    assert report["bars"]["C1_all_episodes_complete"] is False


def test_dual_failure_fires_crash_loop_falsifier(tmp_path):
    write_d0(tmp_path, "deterministic")
    for s in analyzer.SCENARIOS[1:]:
        write_episode(tmp_path, s, 1)
    failed = tmp_path / f"{analyzer.SCENARIOS[0]}__r1__failed"
    failed.mkdir()
    report = analyzer.analyze(tmp_path)
    assert report["falsifiers"]["crash_loop_dual_failures"]["fired"] is True
    assert report["verdict"].startswith("NULL_FALSIFIER_")


def test_stochastic_pairing_falsifier(tmp_path):
    write_d0(tmp_path, "stochastic")
    for s in analyzer.STOCHASTIC_SUBSET:
        write_episode(tmp_path, s, 1, hdscore=0.8)
        write_episode(tmp_path, s, 2, hdscore=0.4)  # |delta|=0.4 > 0.15 bar
    report = analyzer.analyze(tmp_path)
    assert report["bars"]["C1_all_episodes_complete"] is True
    f = report["falsifiers"]["pairing_infeasibility"]
    assert f["pairs_measured"] == 26 and f["fired"] is True
    assert report["verdict"] == "NULL_FALSIFIER_PAIRING_INFEASIBILITY"


def test_stochastic_small_deltas_pass(tmp_path):
    write_d0(tmp_path, "stochastic")
    for s in analyzer.STOCHASTIC_SUBSET:
        write_episode(tmp_path, s, 1, hdscore=0.50)
        write_episode(tmp_path, s, 2, hdscore=0.51)
    report = analyzer.analyze(tmp_path)
    assert report["falsifiers"]["pairing_infeasibility"]["fired"] is False
    assert report["verdict"] == "PASS_BARS_MET"


def test_missing_d0_is_null(tmp_path):
    report = analyzer.analyze(tmp_path)
    assert report["verdict"] == "NULL_D0_MISSING"


def test_d0_numeric_leaves_equal_exact():
    eq, delta = d0mod.numeric_leaves_equal({"a": [1.0, 2.0]}, {"a": [1.0, 2.0]})
    assert eq is True and delta == 0.0
    eq, delta = d0mod.numeric_leaves_equal({"a": [1.0, 2.0]}, {"a": [1.0, 2.0000001]})
    assert eq is False and delta > 0.0
    eq, _ = d0mod.numeric_leaves_equal([1, [2, 3]], [1, [2, 3, 4]])
    assert eq is False
    eq, _ = d0mod.numeric_leaves_equal({"k": True}, {"k": False})
    assert eq is False


def test_d0_compare_episode_dirs_deterministic_and_not(tmp_path):
    import pickle

    for run, hd in ((1, 0.5), (2, 0.5)):
        ep = write_episode(tmp_path, "scene-0013-easy-00", run, hdscore=hd, steps=15)
        with open(ep / "data.pkl", "wb") as fh:
            pickle.dump({"ego": [[0.0, 0.0], [1.0, 0.5]]}, fh)
    r = d0mod.compare_episode_dirs(
        tmp_path / "scene-0013-easy-00__r1", tmp_path / "scene-0013-easy-00__r2")
    assert r["verdict"] == "deterministic"
    # perturb run 2's pickle numerically -> stochastic even though eval/steps match
    with open(tmp_path / "scene-0013-easy-00__r2" / "data.pkl", "wb") as fh:
        pickle.dump({"ego": [[0.0, 0.0], [1.0, 0.500001]]}, fh)
    r = d0mod.compare_episode_dirs(
        tmp_path / "scene-0013-easy-00__r1", tmp_path / "scene-0013-easy-00__r2")
    assert r["verdict"] == "stochastic"
    assert r["data_pkl"]["sha_equal"] is False
