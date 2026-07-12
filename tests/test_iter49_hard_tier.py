"""Iteration 49 hard-tier gate tooling tests: analyzer bars/falsifiers + launcher gates."""

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXP = REPO / "experiments" / "iter49_hugsim_hard_tier_gate"
EXP48 = REPO / "experiments" / "iter48_hugsim_transfer_gate"

spec = importlib.util.spec_from_file_location("analyze_hard_tier", EXP / "analyze_hard_tier.py")
az = importlib.util.module_from_spec(spec)
spec.loader.exec_module(az)

FROZEN = dict(az.FROZEN_PARAMS)


def write_receipts(root: Path, params=None, patch_sha=None) -> Path:
    receipts = {
        "monitor_params": params if params is not None else FROZEN,
        "monitor_patch_sha": patch_sha if patch_sha is not None else az.FROZEN_PATCH_SHA,
        "e2e_py_patched_sha": "y" * 64,
        "e2e_sh_patched_sha": "z" * 64,
        "carried_d0_verdict": "stochastic",
    }
    p = root / "receipts.json"
    p.write_text(json.dumps(receipts))
    return p


def decision_row(frame, fired=False, brake=False, release=False, params=None):
    return {
        "trace_version": "iter48_hugsim_union_v1",
        "frame_index": frame,
        "ts": frame * 0.25,
        "traj": [[0.0, 1.0]] * 6,
        "objs": [],
        "params": params if params is not None else FROZEN,
        "min_cpa": 9.9 if not fired else 0.5,
        "min_ttc": 99.0,
        "fired": fired,
        "brake": brake,
        "release": release,
        "pre_braking": False,
        "pre_clear": 0,
        "post_braking": brake,
        "post_clear": 0,
    }


def write_episode(root: Path, scenario: str, arm: str, run: int, hd: float,
                  terms=None, decisions=None, marker=True, decision_lines=True,
                  steps=15):
    d = root / f"{scenario}__{arm}_r{run}"
    d.mkdir(parents=True)
    ev = {"nc": 1.0, "dac": 1.0, "ttc": 1.0, "c": 1.0, "rc": hd, "hdscore": hd}
    if terms:
        ev.update(terms)
    (d / "eval.json").write_text(json.dumps(ev))
    (d / "episode_meta.json").write_text(json.dumps(
        {"scenario": scenario, "arm": arm, "run": run, "attempt": 1, "rc": 0,
         "hdscore": hd, "steps": steps, "start_epoch": 0, "end_epoch": 200}))
    lines = []
    if marker:
        lines.append(f"SENTINEL_I48_UNION_PATCH_LOADED enabled={1 if arm == 'on' else 0} "
                     f"params={json.dumps(FROZEN, sort_keys=True)}")
    if arm == "on":
        if decisions is None:
            decisions = [decision_row(0, fired=True, brake=True),
                         decision_row(1, fired=False, brake=False, release=True)]
        (d / "sentinel_iter48_decisions.jsonl").write_text(
            "\n".join(json.dumps(r) for r in decisions) + "\n")
        if decision_lines:
            for r in decisions:
                lines.append(
                    f"SENTINEL_I48_DECISION frame={r['frame_index']} "
                    f"fired={int(bool(r['fired']))} brake={int(bool(r['brake']))} "
                    f"release={int(bool(r['release']))} clear=0 min_cpa=1.0 "
                    f"min_ttc=99.0 objs=0")
    lines.extend(["received"] * 15 + ["sent"] * 15)
    (d / "output.txt").write_text("\n".join(lines) + "\n")


def build_tree(root: Path, on_bonus=0.0, **episode_kwargs) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for s in az.SCENARIOS26:
        base = 0.30 + (hash(s) % 100) / 1000.0
        for r in az.RUNS:
            write_episode(root, s, "off", r, base)
            write_episode(root, s, "on", r, base + on_bonus, **episode_kwargs)
    return root


def test_scenario_list_is_the_frozen_hard_tier_schedule():
    assert len(az.SCENARIOS26) == 26
    assert az.SCENARIOS26[0] == "scene-0013-extreme-00"
    assert az.SCENARIOS26[-1] == "scene-0411-hard-00"
    assert sum("-extreme-" in s for s in az.SCENARIOS26) == 13
    assert sum("-hard-" in s for s in az.SCENARIOS26) == 13
    assert az.SCENARIOS26 == sorted(az.SCENARIOS26)
    assert az.BOOTSTRAP_SEED == 49


def test_frozen_patch_sha_matches_committed_iter48_byte_copy():
    digest = hashlib.sha256(
        (EXP48 / "client_patch_union_iter48.py").read_bytes()).hexdigest()
    assert digest == az.FROZEN_PATCH_SHA


def test_pass_transfer_positive(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.10)
    rec = write_receipts(tmp_path)
    rep = az.analyze(root, rec)
    assert rep["bars"] == {"K1_all_episodes_complete": True,
                           "K2_per_step_and_decision_logs": True}
    assert rep["verdict"] == "PASS_TRANSFER_POSITIVE"
    assert rep["primary"]["pairs"] == 52
    assert rep["primary"]["mean_ci95"][0] > 0


def test_transfer_null_and_negative(tmp_path):
    rep0 = az.analyze(build_tree(tmp_path / "null", on_bonus=0.0),
                      write_receipts(tmp_path))
    assert rep0["verdict"] == "TRANSFER_NULL"
    rep_neg = az.analyze(build_tree(tmp_path / "neg", on_bonus=-0.10),
                         write_receipts(tmp_path))
    assert rep_neg["verdict"] == "TRANSFER_NEGATIVE"


def test_completion_null_on_missing_episode(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05)
    victim = root / f"{az.SCENARIOS26[3]}__on_r2"
    for f in victim.iterdir():
        f.unlink()
    victim.rmdir()
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "NULL_COMPLETION_BAR_FAILED"
    assert rep["completion"]["complete"] == 103


def test_f4_dual_failure_is_completion_null(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05)
    victim = root / f"{az.SCENARIOS26[0]}__off_r1"
    victim.rename(root / f"{az.SCENARIOS26[0]}__off_r1__failed")
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "NULL_COMPLETION_BAR_FAILED"
    assert rep["falsifiers"]["F4_crash_loop"]["fired"] is True


def test_f1_void_on_receipts_params(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05)
    bad = dict(FROZEN, cpa_margin=2.0)
    rep = az.analyze(root, write_receipts(tmp_path, params=bad))
    assert rep["verdict"] == "VOID_RETUNED"
    assert "primary" not in rep


def test_f1_void_on_patch_sha_mismatch(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05)
    rep = az.analyze(root, write_receipts(tmp_path, patch_sha="0" * 64))
    assert rep["verdict"] == "VOID_RETUNED"
    assert "monitor-patch-sha-mismatch" in rep["falsifiers"]["F1_retuned"]["problems"]


def test_f1_void_on_decision_row_params(tmp_path):
    bad_rows = [decision_row(0, fired=True, brake=True,
                             params=dict(FROZEN, ttc_thresh=9.0))]
    root = build_tree(tmp_path / "eps", on_bonus=0.05, decisions=bad_rows)
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "VOID_RETUNED"


def test_f2_never_fire_boundary_null(tmp_path):
    quiet = [decision_row(i, fired=False, brake=False) for i in range(10)]
    root = build_tree(tmp_path / "eps", on_bonus=0.05, decisions=quiet)
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "TRANSFER_BOUNDARY_NULL_F2_NEVER_FIRE"
    assert rep["firing_statistics"]["fired_frames"] == 0
    assert rep["primary_ci_verdict_for_record"] == "PASS_TRANSFER_POSITIVE"


def test_f2_over_fire_boundary_null(tmp_path):
    loud = [decision_row(i, fired=True, brake=True) for i in range(10)]
    root = build_tree(tmp_path / "eps", on_bonus=0.05, decisions=loud)
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "TRANSFER_BOUNDARY_NULL_F2_OVER_FIRE"
    assert rep["falsifiers"]["F2_splat_noise_mistuned"]["brake_frame_fraction"] == 1.0


def test_f3_rc_collapse_named_without_replacing_verdict(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05, terms={"rc": 0.01})
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["falsifiers"]["F3_rc_collapse"]["fired"] is True
    assert rep["verdict"] in ("PASS_TRANSFER_POSITIVE", "TRANSFER_NULL",
                              "TRANSFER_NEGATIVE")


def test_f5_noise_dominated_flag(tmp_path):
    root = tmp_path / "eps"
    root.mkdir(parents=True)
    for s in az.SCENARIOS26:
        write_episode(root, s, "off", 1, 0.10)
        write_episode(root, s, "off", 2, 0.60)  # OFF-OFF spread 0.50 > 0.15 bar
        write_episode(root, s, "on", 1, 0.35)
        write_episode(root, s, "on", 2, 0.35)
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["falsifiers"]["F5_pairing_infeasibility"]["fired"] is True
    assert rep["noise_dominated_flag"] is True
    assert "primary" in rep  # CI still reported, flagged


def test_k2_on_episode_without_decision_lines_fails(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05, decision_lines=False)
    rep = az.analyze(root, write_receipts(tmp_path))
    assert rep["verdict"] == "NULL_COMPLETION_BAR_FAILED"


def test_per_episode_brake_fractions_and_step_cap_visibility(tmp_path):
    loud = [decision_row(i, fired=True, brake=True) for i in range(3)] + \
           [decision_row(i, fired=False, brake=False) for i in range(3, 10)]
    root = build_tree(tmp_path / "eps", on_bonus=0.05, decisions=loud, steps=400)
    rep = az.analyze(root, write_receipts(tmp_path))
    per = rep["firing_statistics"]["per_episode_brake_fractions"]
    assert len(per) == 52
    assert abs(per[0]["brake_fraction"] - 0.3) < 1e-9
    assert len(rep["firing_statistics"]["step_capped_episodes"]) == 52


def test_tier_split_is_descriptive_only(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.05)
    rep = az.analyze(root, write_receipts(tmp_path))
    split = rep["tier_split_descriptive"]
    assert split["hard"]["n_pairs"] == 26
    assert split["extreme"]["n_pairs"] == 26
    assert "not powered" in split["hard"]["note"]


def test_bootstrap_deterministic(tmp_path):
    root = build_tree(tmp_path / "eps", on_bonus=0.03)
    rec = write_receipts(tmp_path)
    a = az.analyze(root, rec)
    b = az.analyze(root, rec)
    assert json.dumps(a, sort_keys=True, default=str) == \
        json.dumps(b, sort_keys=True, default=str)


def test_launcher_gates_and_schedule():
    text = (EXP / "run_hard_tier_gate.sh").read_text()
    assert "SENTINEL_ENABLED=$enable" in text
    # F1 discipline: no parameter env overrides may reach the container.
    for banned in ("SENTINEL_CPA_MARGIN=", "SENTINEL_TTC=", "SENTINEL_MIN_CLOSING=",
                   "SENTINEL_MAXGAP=", "SENTINEL_MIN_SCORE=", "SENTINEL_RELEASE_K="):
        assert banned not in text
    # The staged patch must be the committed iter48 byte copy, gated by SHA.
    assert f"FROZEN_PATCH_SHA={az.FROZEN_PATCH_SHA}" in text
    assert "I49_PRECHECK_OK" in text and "I49_PRECHECK_FAIL" in text
    assert "I49_HARD_DONE" in text
    assert "/var/log/sentinel-iter49-hard.log" in text  # registered log path documented
    assert "iter49_runs" in text
    assert "off 1" in text and "on 1" in text and "off 2" in text and "on 2" in text
    # The frozen 36-yaml manifest and the first-26 schedule derivation.
    assert text.count(".yaml") >= 36
    assert 'head -26' in text
    assert 'scene-0411-hard-00' in text


def test_launcher_manifest_covers_all_36_and_schedule_is_first_26():
    text = (EXP / "run_hard_tier_gate.sh").read_text()
    lines = [ln for ln in text.splitlines()
             if ln.strip().endswith(".yaml") and len(ln.split()) == 2]
    assert len(lines) == 36
    names = sorted(ln.split()[1] for ln in lines)
    assert len(set(names)) == 36
    first26 = [n[:-len(".yaml")] for n in names[:26]]
    assert first26 == az.SCENARIOS26
    for n in first26:
        assert ("-hard-" in n) or ("-extreme-" in n)
