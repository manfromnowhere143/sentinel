from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter133_neuroncap_placebo_semantics_control_design"
    / "generate_neuroncap_placebo_semantics_control_design.py"
)
SPEC = importlib.util.spec_from_file_location("iter133_placebo", MODULE_PATH)
assert SPEC is not None
placebo_design = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(placebo_design)


def build_committed_report() -> dict:
    repo = Path(__file__).resolve().parents[1]
    return placebo_design.build_report(repo)


def test_committed_inputs_build_complete_design() -> None:
    report = build_committed_report()

    assert report["verdict"] == placebo_design.COMPLETE_VERDICT
    assert report["problems"] == []
    assert report["summary"]["primary_placebo_arm_count"] == 1
    assert report["summary"]["semantic_trigger_leak_count"] == 0
    assert report["summary"]["future_verdict_class_count"] == 4
    assert report["summary"]["true_authorization_count"] == 0


def test_primary_placebo_removes_live_semantics() -> None:
    report = build_committed_report()
    arm = report["design_contract"]["primary_placebo_arm"]

    assert arm["arm_id"] == placebo_design.PRIMARY_PLACEBO_ID
    assert arm["semantic_trigger_removed"] is True
    for field in placebo_design.SEMANTIC_TRIGGER_FIELDS:
        assert arm[field] is False
    assert arm["donor_selection"]["exclude_target_scenario_pair"] is True
    assert arm["donor_selection"]["exclude_target_seed"] is True


def test_matching_contract_preserves_pairing_and_budget_without_run_authorization() -> None:
    report = build_committed_report()
    matching = report["design_contract"]["matching_contract"]

    assert placebo_design.PRIMARY_PLACEBO_ID in matching["future_arms"]
    assert matching["seed_pairing_required"] is True
    assert matching["actuator_budget_matching_required"] is True
    assert matching["hidden_tuning_forbidden"] is True
    assert matching["post_run_schedule_selection_forbidden"] is True
    for field in placebo_design.FALSE_AUTHORIZATION_FIELDS:
        assert matching[field] is False


def test_verdict_contract_keeps_safe_progress_and_nulls_first_class() -> None:
    report = build_committed_report()
    verdict = report["design_contract"]["verdict_contract"]

    assert set(verdict["future_verdict_classes"]) == set(
        placebo_design.EXPECTED_VERDICT_CLASSES
    )
    assert verdict["primary_comparison"] == "released_union_ncap_minus_placebo_ncap"
    assert verdict["secondary_metric"] == "safe_progress"
    assert "full weight" in verdict["null_publication_policy"]


def test_source_facts_anchor_power_rss_and_opportunity_numbers() -> None:
    report = build_committed_report()
    facts = report["source_facts"]

    assert facts["full_power"]["measured_episodes"] == 799
    assert facts["full_power"]["ncap_delta_best_minus_off"] == 0.783
    assert facts["rss_style_baseline"]["union_minus_rss_safe_progress"] == 1.345
    assert facts["opportunity_audit"]["verdict"] == "A1_CONFIRMED"
    assert facts["opportunity_audit"]["rho"] == 0.7003


def test_claim_boundary_forbids_execution_and_claim_upgrade() -> None:
    report = build_committed_report()
    boundary = report["claim_boundary"]

    assert "no GPU launch" in boundary
    assert "NeuroNCAP execution" in boundary
    assert "commercial claim" in boundary
    assert "frontier-stack equivalence claim" in boundary
    assert report["summary"]["gpu_authorized"] is False
    assert report["summary"]["neuroncap_execution_authorized"] is False
