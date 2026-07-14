"""Iteration 134 gates: the placebo must be a placebo, and the control must be discriminating.

These tests read the committed iteration-134 artifacts. They do not re-run generators and they do
not touch the box. Their job is to make it mechanically impossible to launch, or to publish, a
"placebo" that can see the world, a donor schedule that leaks the target, or a manifest that
fails the iteration-133 design contract.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter134_neuroncap_placebo_semantics_execution"
ITER15 = ROOT / "experiments" / "iter15_latch_release" / "server_patch_union_release.py"

SCHED = json.loads((EXP / "donor_schedules.json").read_text())
MANIFEST = json.loads((EXP / "launch_manifest.json").read_text())
PLACEBO_SRC = (EXP / "server_patch_placebo.py").read_text()
UNION_SRC = (EXP / "server_patch_union_release.py").read_text()

FORBIDDEN = MANIFEST["g1_forbidden_terms"]
RUNS = 20
PAIRS = 20


def test_donor_schedules_valid():
    assert SCHED["verdict"] == "DONOR_SCHEDULES_OK"
    assert SCHED["problem_count"] == 0
    assert SCHED["block_count"] == PAIRS * RUNS
    assert SCHED["target_count"] == PAIRS * RUNS


def test_union_log_counts_match_committed_iter42_trace():
    # 400 reset blocks, 1,205 brake frames: the counts iteration 42 committed and proved by replay
    assert SCHED["union_total_brake_frames"] == 1205


def test_every_donor_excludes_target_pair_and_seed():
    for key, row in SCHED["schedules"].items():
        assert row["donor_seq"] != row["target_seq"], f"donor pair leak: {key}"
        assert row["donor_run"] != row["target_run"], f"donor seed leak: {key}"
        assert row["donor_class"] == row["target_class"], f"class mismatch: {key}"


def test_scheduled_budget_equals_union_budget_exactly():
    assert SCHED["scheduled_total_brake_frames"] == SCHED["union_total_brake_frames"]
    assert SCHED["per_class_scheduled_brake_frames"] == SCHED["per_class_union_brake_frames"]


def test_donor_map_is_a_bijection_within_class():
    seen = {}
    for key, row in SCHED["schedules"].items():
        donor = (row["donor_class"], row["donor_seq"], row["donor_run"])
        assert donor not in seen, f"donor {donor} reused by {key} and {seen.get(donor)}"
        seen[donor] = key
    assert len(seen) == PAIRS * RUNS


def test_g1_placebo_names_no_risk_term():
    leaks = [t for t in FORBIDDEN if t in PLACEBO_SRC]
    assert leaks == [], f"the placebo can name a risk term: {leaks}"


def test_g1_guard_is_not_vacuous():
    # the same guard must fire on the semantic union, or it proves nothing about the placebo
    present = [t for t in FORBIDDEN if t in UNION_SRC]
    assert len(present) >= 10, "G1 guard does not fire on the released union; it is vacuous"


def test_placebo_inherits_the_released_union_actuator_expression():
    assert "[[0.0, 0.0] for _ in range(len(base))]" in PLACEBO_SRC
    assert "[[0.0, 0.0] for _ in range(len(base))]" in UNION_SRC


def test_carried_union_patch_is_byte_identical_to_iter15():
    assert (EXP / "server_patch_union_release.py").read_bytes() == ITER15.read_bytes()


def test_manifest_ok_and_binds_the_design_contract():
    assert MANIFEST["verdict"] == "LAUNCH_MANIFEST_OK"
    assert MANIFEST["problem_count"] == 0
    assert MANIFEST["design_contract"] == "iter133.neuroncap_placebo_semantics_control_design.v1"
    for field in ["scenario_pair_ids", "scenario_classes", "run_indices", "arm_ids",
                  "donor_schedule_ids", "donor_exclusion_receipts", "actuator_budget_summaries",
                  "patch_file_sha256", "analyzer_file_sha256", "environment_receipts"]:
        assert MANIFEST.get(field), f"manifest does not bind {field}"


def test_manifest_arms_match_the_frozen_design():
    assert MANIFEST["arm_ids"] == ["off", "union", "placebo"]
    assert MANIFEST["planned_episodes"] == PAIRS * RUNS * 3
    # OFF and UNION must be the same binary, env-gated: the F1 discipline
    arms = {a["arm_id"]: a for a in MANIFEST["arms"]}
    assert arms["off"]["patch"] == arms["union"]["patch"]
    assert arms["off"]["enabled"] == 0 and arms["union"]["enabled"] == 1
    assert arms["placebo"]["patch"] == "server_patch_placebo.py"


def test_manifest_freezes_the_union_params_unchanged():
    assert MANIFEST["frozen_union_params"] == {
        "SENTINEL_MIN_SCORE": "0.3", "SENTINEL_MAXGAP": "30", "SENTINEL_CPA_MARGIN": "1.5",
        "SENTINEL_TTC": "2.5", "SENTINEL_MIN_CLOSING": "3", "SENTINEL_RELEASE_K": "4",
    }


def test_manifest_hash_binds_patch_and_analyzer():
    import hashlib
    for name, rec in MANIFEST["hash_bound_files"].items():
        actual = hashlib.sha256((EXP / name).read_bytes()).hexdigest()
        assert actual == rec["sha256"], f"{name} drifted from the manifest"


def test_environment_receipt_pins_the_cusolver_shim_and_swap():
    env = MANIFEST["environment_receipts"]
    assert env["uniad_track_py_sha256"]
    assert env["uniad_checkpoint_sha256"] == (
        "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990")
    assert env["swap_persisted_fstab"] is True
    assert env["box_quiescence_check"]["running_containers"] == 0
