from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter47_map_staging_and_off_completion"
ITER46 = ROOT / "experiments/iter46_hugsim_off_baseline"
STAGING = EXP / "stage_map_expansion.py"
ANALYZER = EXP / "analyze_completion.py"
RUN_SH = EXP / "run_completion.sh"
HYPOTHESIS = EXP / "HYPOTHESIS.md"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


staging = load(STAGING, "iter47_staging")
completion = load(ANALYZER, "iter47_completion")
analyzer46 = completion.load_iter46_analyzer()


# ---- frozen schedule ----

def test_schedule_is_exactly_the_14_iter46_dual_failures():
    assert len(completion.FAILED_SCENARIOS) == 7
    assert all(s.endswith("-medium-01") for s in completion.FAILED_SCENARIOS)
    assert completion.FAILED_SCENARIOS == sorted(completion.FAILED_SCENARIOS)
    assert len(completion.NEW_EPISODES) == 14
    # every failed scenario is inside the frozen iter46 stochastic subset
    assert set(completion.FAILED_SCENARIOS) <= set(analyzer46.STOCHASTIC_SUBSET)


def test_carried_plus_new_partition_the_52_stochastic_episodes():
    carried = completion.carried_episodes(analyzer46)
    assert len(carried) == 38
    together = set(carried) | set(completion.NEW_EPISODES)
    assert len(together) == 52
    assert together == set(analyzer46.scheduled_episodes("stochastic"))
    assert not set(carried) & set(completion.NEW_EPISODES)


def test_run_script_schedule_and_gates():
    run_sh = RUN_SH.read_text()
    hyp = HYPOTHESIS.read_text()
    for s in completion.FAILED_SCENARIOS:
        assert s in run_sh and s in hyp
    carried_scenarios = sorted({s for s, _ in completion.carried_episodes(analyzer46)})
    assert len(carried_scenarios) == 19
    for s in carried_scenarios:
        assert s in run_sh
    # frozen provenance constants (identical to iteration 46) in both docs
    for sha in (
        "62c690d39fd90020e68a196bd8bcc1c4d4191f2e",
        "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
        "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
        "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c",
        "f73ef3884063",
    ):
        assert sha in run_sh and sha in hyp
    # iter47-specific gates and markers
    assert "I47_OFF_COMPLETION_DONE" in run_sh
    assert "I47_OFF_ABORT_CONSECUTIVE_FAILURES" in run_sh
    assert "I47_OFF_ABORT_DISK" in run_sh
    for loc in ("singapore-onenorth", "singapore-hollandvillage",
                "singapore-queenstown", "boston-seaport"):
        assert loc in run_sh
    assert "d0_verdict.txt" in run_sh and "stochastic" in run_sh
    # no D0 re-probe: the branch decision is carried, never re-derived
    assert "d0_compare" not in run_sh
    # the 52-yaml manifest is still provenance-verified
    assert run_sh.count(".yaml") >= 52
    # iter46's heavy manifest box file is not overwritten
    assert "heavy_manifest_iter47.txt" in run_sh


# ---- staging safety ----

def test_member_is_unsafe(tmp_path):
    dest = tmp_path / "maps"
    dest.mkdir()
    assert staging.member_is_unsafe("/etc/passwd", dest) is True
    assert staging.member_is_unsafe("../evil.json", dest) is True
    assert staging.member_is_unsafe("expansion/../../evil.json", dest) is True
    assert staging.member_is_unsafe("expansion/singapore-onenorth.json", dest) is False
    assert staging.member_is_unsafe("basemap/x.png", dest) is False


def test_scan_zip_safety_flags_traversal(tmp_path):
    dest = tmp_path / "maps"
    dest.mkdir()
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("expansion/ok.json", "{}")
        zf.writestr("../escape.json", "{}")
    report = staging.scan_zip_safety(bad, dest)
    assert report["members_scanned"] == 2
    assert report["unsafe_members"] == ["../escape.json"]

    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as zf:
        for rel in staging.REQUIRED_JSONS:
            zf.writestr(rel, "{}")
    report = staging.scan_zip_safety(good, dest)
    assert report["members_scanned"] == 4
    assert report["unsafe_members"] == []


def test_redacted_provenance_never_carries_query_material():
    prov = staging.redacted_provenance(
        "https://motional-nuscenes.s3.amazonaws.com/public/v1.0/"
        "nuScenes-map-expansion-v1.3.zip?X-Amz-Signature=SECRET&X-Amz-Credential=KEY",
        "signed_url",
    )
    blob = json.dumps(prov)
    assert "SECRET" not in blob and "KEY" not in blob and "?" not in blob
    assert prov["source_host"] == "motional-nuscenes.s3.amazonaws.com"
    assert prov["source_path_basename"] == "nuScenes-map-expansion-v1.3.zip"


def test_staging_frozen_values_match_hypothesis():
    hyp = HYPOTHESIS.read_text()
    assert staging.CANONICAL_NAME in hyp
    assert staging.PUBLIC_URL in hyp
    for rel in staging.REQUIRED_JSONS:
        assert rel in hyp
    assert staging.MIN_JSON_BYTES == 1_000_000
    assert staging.MIN_ARCHIVE_BYTES == 100_000_000
    assert staging.MAX_ARCHIVE_BYTES == 2_000_000_000


# ---- analyzer over carried + new ----

def write_episode(root: Path, scenario: str, run: int, *, hdscore=0.5, steps=15, attempt=1):
    ep = root / f"{scenario}__r{run}"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(
        {"hdscore": hdscore, "nc": 1.0, "dac": 1.0, "ttc": 1.0, "comfort": 1.0, "rc": hdscore}))
    (ep / "episode_meta.json").write_text(json.dumps(
        {"scenario": scenario, "run": run, "attempt": attempt, "rc": 0, "steps": steps}))
    (ep / "output.txt").write_text("".join(f"received\nsent {i:04d}\n" for i in range(steps)))
    return ep


def build_fixture(tmp_path: Path):
    """Fake committed-iter46 episodes root + new-episodes root + matching box hashes."""
    iter46_eps = tmp_path / "iter46_episodes"
    new_eps = tmp_path / "new_episodes"
    iter46_eps.mkdir()
    new_eps.mkdir()
    (iter46_eps / "d0_comparison.json").write_text(json.dumps({"verdict": "stochastic"}))
    for scenario, run in completion.carried_episodes(analyzer46):
        write_episode(iter46_eps, scenario, run, hdscore=0.40)
    for scenario, run in completion.NEW_EPISODES:
        write_episode(new_eps, scenario, run, hdscore=0.42)
    lines = []
    for root, pairs in ((iter46_eps, completion.carried_episodes(analyzer46)),
                        (new_eps, completion.NEW_EPISODES)):
        for scenario, run in pairs:
            for fname in completion.INTEGRITY_FILES:
                p = root / f"{scenario}__r{run}" / fname
                digest = hashlib.sha256(p.read_bytes()).hexdigest()
                lines.append(f"{digest}  ./{scenario}__r{run}/{fname}")
    hashes = tmp_path / "box_episode_hashes.txt"
    hashes.write_text("\n".join(lines) + "\n")
    return iter46_eps, new_eps, hashes


def test_full_52_happy_path_passes(tmp_path):
    iter46_eps, new_eps, hashes = build_fixture(tmp_path)
    report = completion.analyze_completion(iter46_eps, new_eps, hashes)
    assert report["carried_integrity"]["pass"] is True
    assert report["carried_integrity"]["files_checked"] == 104  # 52 dirs x 2 files
    assert report["full_52"]["completion"]["complete"] == 52
    assert report["full_52"]["bars"] == {
        "C1_all_episodes_complete": True, "C2_per_step_logs": True}
    assert report["full_52"]["falsifiers"]["pairing_infeasibility"]["pairs_measured"] == 26
    assert report["verdict"] == "PASS_BARS_MET"


def test_carried_tamper_is_a_null(tmp_path):
    iter46_eps, new_eps, hashes = build_fixture(tmp_path)
    victim = iter46_eps / "scene-0013-easy-00__r1" / "eval.json"
    victim.write_text(json.dumps({"hdscore": 0.99}))  # box hash no longer matches
    report = completion.analyze_completion(iter46_eps, new_eps, hashes)
    assert report["carried_integrity"]["pass"] is False
    assert report["verdict"] == "NULL_CARRIED_INTEGRITY"


def test_missing_new_episode_fails_c1(tmp_path):
    import shutil

    iter46_eps, new_eps, hashes = build_fixture(tmp_path)
    shutil.rmtree(new_eps / "scene-0166-medium-01__r2")
    report = completion.analyze_completion(iter46_eps, new_eps, hashes)
    assert report["full_52"]["bars"]["C1_all_episodes_complete"] is False
    assert report["verdict"].startswith("NULL_")


def test_new_dual_failure_dir_fires_crash_loop_falsifier(tmp_path):
    import shutil

    iter46_eps, new_eps, hashes = build_fixture(tmp_path)
    shutil.rmtree(new_eps / "scene-0038-medium-01__r1")
    (new_eps / "scene-0038-medium-01__r1__failed").mkdir()
    report = completion.analyze_completion(iter46_eps, new_eps, hashes)
    assert report["full_52"]["falsifiers"]["crash_loop_dual_failures"]["fired"] is True
    assert report["verdict"].startswith("NULL_FALSIFIER_")
