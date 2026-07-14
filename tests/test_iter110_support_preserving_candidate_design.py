from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter110_hugsim_support_preserving_candidate_design"
    / "analyze_support_preserving_candidate_design.py"
)
SPEC = importlib.util.spec_from_file_location("iter110_design", MODULE_PATH)
assert SPEC is not None
design = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(design)


def _row(
    *,
    scenario: str = "scene-0001-hard-00",
    run: int = 1,
    channel: str = "ttc_only",
    timing: str = "short_lead_fire",
    lead: float = 0.5,
) -> dict:
    return {
        "dataset": "iter49_hard_extreme",
        "fire_timing_label": timing,
        "first_fire_channel": channel,
        "first_fire_lead_time": lead,
        "first_fire_ts": 10.0,
        "first_on_nc_time": 10.0 + lead,
        "monitor_provenance_label": "unique_ttc_object" if channel == "ttc_only" else "unique_cpa_object",
        "on_collision": True,
        "run": run,
        "scenario": scenario,
        "tier": "hard",
    }


def test_design_label_prioritizes_exact_anchor_then_scenario_analogue() -> None:
    evidence = {
        "exact_positive": {("scene-0001-hard-00", 1): ["iter109:classifiable_success:actor_mismatch"]},
        "exact_nonclassifiable": {},
        "scenario_positive": {
            "scene-0001-hard-00": ["iter109:classifiable_success:actor_mismatch"],
            "scene-0002-hard-00": ["iter59:classifiable_foreground:actor_mismatch"],
        },
        "scenario_nonclassifiable": {},
        "prior_scenarios": ["scene-0001-hard-00", "scene-0002-hard-00"],
    }

    assert design.design_label(_row(scenario="scene-0001-hard-00", run=1), evidence) == (
        "exact_ttc_classifiable_anchor"
    )
    assert design.design_label(_row(scenario="scene-0002-hard-00", run=2), evidence) == (
        "ttc_classifiable_scenario_analogue"
    )
    assert design.design_label(_row(scenario="scene-0003-hard-00", run=1), evidence) == "ttc_residual_risk_probe"
    assert design.design_label(_row(channel="cpa_only"), evidence) == "cpa_residual_risk_fallback"


def test_design_label_blocks_exact_nonclassifiable_scenario_analogue() -> None:
    evidence = {
        "exact_positive": {},
        "exact_nonclassifiable": {("scene-0002-hard-00", 2): ["iter104:background_collision_only"]},
        "scenario_positive": {"scene-0002-hard-00": ["iter59:classifiable_foreground:actor_mismatch"]},
        "scenario_nonclassifiable": {"scene-0002-hard-00": ["iter104:background_collision_only"]},
        "prior_scenarios": ["scene-0002-hard-00"],
    }

    assert design.design_label(_row(scenario="scene-0002-hard-00", run=2), evidence) == "ttc_residual_risk_probe"


def test_choose_verdict_uses_frozen_core_bars() -> None:
    assert design.choose_verdict(13, [], []) == design.THIRTEEN_SLOT_COMPLETE_VERDICT
    assert design.choose_verdict(4, [], []) == design.CORE_COMPLETE_VERDICT
    assert design.choose_verdict(3, [], []) == design.SUPPORT_NULL_VERDICT
    assert design.choose_verdict(13, ["bad"], []) == design.INFRA_NULL_VERDICT
    assert design.choose_verdict(13, [], ["unknown"]) == design.INFRA_NULL_VERDICT


def test_timing_crosscheck_detects_timing_bin_mismatch() -> None:
    row = _row(timing="short_lead_fire", lead=0.25)
    timing_row = {
        "first_fire_ts": row["first_fire_ts"],
        "first_on_nc_time": row["first_on_nc_time"],
        "lead_time": row["first_fire_lead_time"],
        "run": row["run"],
        "scenario": row["scenario"],
        "timing_bin": "long_lead_brake",
    }

    problems = design.crosscheck_timing_rows([row], [timing_row])

    assert any(problem.startswith("timing-bin-mismatch") for problem in problems)


def test_committed_reports_build_support_preserving_core_design() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = design.build_report(
        repo / "experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json",
        repo
        / "experiments"
        / "iter54_hugsim_provenance_support_audit"
        / "proof-provenance"
        / "provenance_support_report.json",
        repo / "experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json",
        repo
        / "experiments"
        / "iter104_hugsim_provenance_batch_actor_match_audit"
        / "proof-actor-match"
        / "provenance_batch_actor_match_report.json",
        repo
        / "experiments"
        / "iter109_hugsim_timing_aware_support_yield_decomposition"
        / "proof-decomposition"
        / "timing_aware_support_yield_decomposition_report.json",
    )

    assert report["verdict"] == design.CORE_COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["timing_eligible_count"] == 35
    assert report["summary"]["support_preserving_core_count"] >= 4
    assert report["summary"]["support_preserving_core_count"] < 13
    assert report["summary"]["core_channel_counts"] == {"ttc_only": report["summary"]["support_preserving_core_count"]}
