#!/usr/bin/env python3
"""Iteration 133 NeuroNCAP placebo semantics control design preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE"
INFRA_NULL_VERDICT = "NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_INFRA_NULL"
PRIMARY_PLACEBO_ID = "semantics_scrambled_budget_matched_placebo"
DESIGN_VERSION = "iter133.neuroncap_placebo_semantics_control_design.v1"
EXPECTED_VERDICT_CLASSES = (
    "SEMANTIC_VALUE_CONFIRMED",
    "PLACEBO_EXPLAINS_GAIN",
    "PLACEBO_HARM_OR_NULL",
    "PLACEBO_CONTROL_INFRA_NULL",
)
SOURCE_FACTS = {
    "full_power_measured_episodes": 799,
    "full_power_planned_episodes": 800,
    "ncap_delta": 0.783,
    "ncap_ci95": [0.605, 0.928],
    "safe_progress_delta": -0.032,
    "safe_progress_ci95": [-0.127, 0.065],
    "rss_safe_progress_delta_union_minus_rss": 1.345,
    "rss_safe_progress_ci95": [0.944, 1.701],
    "opportunity_rho": 0.7003,
    "opportunity_rho_bar": 0.5,
    "opportunity_high_collision_pair_count": 12,
    "opportunity_low_collision_pair_count": 8,
}

FULL_POWER_RESULT_PATH = Path("experiments/full14_power/RESULT.md")
FULL_POWER_HYPOTHESIS_PATH = Path("experiments/full14_power/HYPOTHESIS.md")
FULL_POWER_ANALYZER_PATH = Path("experiments/full14_power/analyze_power14.py")
RSS_RESULT_PATH = Path("experiments/iter13_rss_baseline/RESULT.md")
OPPORTUNITY_RESULT_PATH = Path("experiments/iter50_collision_opportunity_audit/RESULT.md")
OPPORTUNITY_REPORT_PATH = Path(
    "experiments/iter50_collision_opportunity_audit/proof-audit/opportunity_report.json"
)
ITER132_RESULT_PATH = Path(
    "experiments/iter132_support_core_schema_instance_creation_preflight/RESULT.md"
)
HANDOFF_PATH = Path("HANDOFF.md")
DESIGN_NOTE_PATH = Path(
    "docs/research/NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path(
    "experiments/iter133_neuroncap_placebo_semantics_control_design/proof-design"
)
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "neuroncap_placebo_semantics_control_design_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "neuroncap_placebo_semantics_control_design.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "generate_neuroncap_placebo_semantics_control_design.command.txt"

FALSE_AUTHORIZATION_FIELDS = (
    "gpu_authorized",
    "neuroncap_execution_authorized",
    "hugsim_execution_authorized",
    "scenario_generation_authorized",
    "generated_artifact_authorized",
    "reserved_path_creation_authorized",
    "execution_slot_selection_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
    "learning_update_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_claim_authorized",
    "benchmark_ranking_claim_authorized",
    "production_authorized",
    "commercial_claim_authorized",
    "frontier_equivalence_claim_authorized",
)
SEMANTIC_TRIGGER_FIELDS = (
    "uses_live_sentinel_risk_score",
    "uses_planner_risk_introspection",
    "uses_observed_closing_ttc_trigger",
    "uses_plan_vs_path_cpa_trigger",
    "uses_learned_predictor",
    "uses_outcome_feedback",
)
BOUNDARY = (
    "placebo-semantics control design only; no GPU launch, NeuroNCAP execution, HUGSIM "
    "execution, reserved path creation, generated scenario artifact, scenario generation, "
    "execution-slot selection, learning/update step, repair, actor-causality, threshold-value, "
    "transfer upgrade, safety, deployment, robustness, benchmark-ranking, population-rate, "
    "HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, "
    "retuning, production, commercial claim, or frontier-stack equivalence claim"
)


def false_authorizations() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORIZATION_FIELDS}


def canonical(text: str) -> str:
    normalized = text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    return " ".join(normalized.split())


def load_text(path: Path, label: str) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{label}:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-text-failed:{label}:{path}:{exc}"]


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-or-empty:{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-json-failed:{label}:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"json-not-dict:{label}:{path}"]
    return data, []


def require_contains(
    problems: list[str],
    label: str,
    text: str,
    needles: tuple[str, ...] | list[str],
) -> None:
    haystack = canonical(text)
    for needle in needles:
        if canonical(needle) not in haystack:
            problems.append(f"{label}-missing:{needle}")


def almost_equal(actual: Any, expected: float, tolerance: float = 1e-4) -> bool:
    return isinstance(actual, int | float) and abs(float(actual) - expected) <= tolerance


def validate_source_inputs(
    full_power_text: str,
    full_power_hypothesis_text: str,
    full_power_analyzer_text: str,
    rss_text: str,
    opportunity_text: str,
    opportunity_report: dict[str, Any],
    iter132_text: str,
    handoff_text: str,
    problems: list[str],
) -> dict[str, Any]:
    require_contains(
        problems,
        "full-power-result",
        full_power_text,
        [
            "799 of 800 planned episodes",
            "H-P0 - the validity gate: PASS",
            "off/side-0921 is reported at n=19",
            "NCAP score",
            "+0.783",
            "+0.605",
            "+0.928",
            "Safe-progress",
            "-0.032",
            "-0.127",
            "+0.065",
        ],
    )
    require_contains(
        problems,
        "full-power-hypothesis",
        full_power_hypothesis_text,
        [
            "20 runs per pair",
            "H-P0",
            "H-P1",
            "H-P2",
            "analyze_power14.py",
        ],
    )
    require_contains(
        problems,
        "full-power-analyzer",
        full_power_analyzer_text,
        [
            "bootstrap",
            "ncap_score",
            "safe-progress",
        ],
    )
    require_contains(
        problems,
        "rss-result",
        rss_text,
        [
            "observed kinematics",
            "latched-stop actuator",
            "isolating one variable, the decision rule",
            "Union - RSS on safe-progress: +1.345",
            "+0.944",
            "+1.701",
        ],
    )
    require_contains(
        problems,
        "opportunity-result",
        opportunity_text,
        [
            "A1_CONFIRMED",
            "Spearman rho",
            "+0.7003",
            "benefit concentrates where the OFF arm collides",
            "No new safety, transfer, deployment, robustness, benchmark-ranking, real-world, or monitor-performance claim",
        ],
    )
    require_contains(
        problems,
        "iter132-result",
        iter132_text,
        [
            "SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_COMPLETE",
            "This still authorizes no reserved path creation",
            "This still authorizes no reserved path creation, generated scenario artifact, scenario generation",
        ],
    )
    require_contains(
        problems,
        "handoff-critique",
        handoff_text,
        [
            "Iterations 125-132 are valuable only as controlled evidence infrastructure",
            "not new empirical improvement",
            "placebo/sham intervention with matched timing, actuator budget, and opportunity",
        ],
    )

    integrity = opportunity_report.get("integrity")
    a1 = opportunity_report.get("a1")
    frozen = opportunity_report.get("frozen")
    if opportunity_report.get("verdict") != "OPPORTUNITY_AUDIT_COMPLETE":
        problems.append("opportunity-report-verdict-mismatch")
    if not isinstance(integrity, dict) or integrity.get("problems") != []:
        problems.append("opportunity-report-integrity-problems")
    if not isinstance(a1, dict):
        problems.append("opportunity-report-a1-not-dict")
    else:
        if a1.get("verdict") != "A1_CONFIRMED":
            problems.append("opportunity-report-a1-verdict-mismatch")
        if not almost_equal(a1.get("point_rho"), 0.7003430781759243):
            problems.append(f"opportunity-report-rho-mismatch:{a1.get('point_rho')!r}")
        rho_ci = a1.get("rho_ci95")
        if not (
            isinstance(rho_ci, list)
            and len(rho_ci) == 2
            and almost_equal(rho_ci[0], 0.3908878667515415)
            and almost_equal(rho_ci[1], 0.8762072870941174)
        ):
            problems.append(f"opportunity-report-rho-ci-mismatch:{rho_ci!r}")
        strata = a1.get("strata")
        if not isinstance(strata, dict):
            problems.append("opportunity-report-strata-not-dict")
        else:
            high = strata.get("high_opportunity", {})
            low = strata.get("low_opportunity", {})
            if not isinstance(high, dict) or high.get("n") != 12:
                problems.append("opportunity-report-high-stratum-count-mismatch")
            if not isinstance(low, dict) or low.get("n") != 8:
                problems.append("opportunity-report-low-stratum-count-mismatch")
    if not isinstance(frozen, dict) or frozen.get("a1_rho_bar") != 0.5:
        problems.append("opportunity-report-rho-bar-mismatch")

    return {
        "full_power": {
            "measured_episodes": SOURCE_FACTS["full_power_measured_episodes"],
            "planned_episodes": SOURCE_FACTS["full_power_planned_episodes"],
            "seed_paired_runs_per_pair": 20,
            "known_exception": "off/side-0921 n=19",
            "validity_gate": "H-P0 PASS",
            "ncap_delta_best_minus_off": SOURCE_FACTS["ncap_delta"],
            "ncap_delta_ci95": SOURCE_FACTS["ncap_ci95"],
            "safe_progress_delta_best_minus_off": SOURCE_FACTS["safe_progress_delta"],
            "safe_progress_delta_ci95": SOURCE_FACTS["safe_progress_ci95"],
        },
        "rss_style_baseline": {
            "same_kinematics": True,
            "same_latched_stop_actuator": True,
            "isolated_variable": "decision_rule",
            "union_minus_rss_safe_progress": SOURCE_FACTS[
                "rss_safe_progress_delta_union_minus_rss"
            ],
            "union_minus_rss_safe_progress_ci95": SOURCE_FACTS["rss_safe_progress_ci95"],
        },
        "opportunity_audit": {
            "verdict": "A1_CONFIRMED",
            "rho": SOURCE_FACTS["opportunity_rho"],
            "rho_bar": SOURCE_FACTS["opportunity_rho_bar"],
            "high_collision_pair_count": SOURCE_FACTS["opportunity_high_collision_pair_count"],
            "low_collision_pair_count": SOURCE_FACTS["opportunity_low_collision_pair_count"],
            "reading": "NeuroNCAP benefit concentrates where OFF-arm collision opportunity exists.",
        },
        "post_iter132_boundary": {
            "preflight_chain_status": "evidence_infrastructure_only",
            "empirical_claim_upgraded": False,
        },
    }


def build_primary_placebo_arm() -> dict[str, Any]:
    arm = {
        "arm_id": PRIMARY_PLACEBO_ID,
        "role": "primary_future_placebo_control",
        "status": "design_only_not_authorized_to_run",
        "primary_placebo": True,
        "actuator_family": "threat_cleared_latched_stop_release",
        "actuator_inherited_from": "released_union",
        "semantic_trigger_removed": True,
        "intervention_windows_are": "timing_and_budget_replay_windows_only",
        "budget_match_unit": "scenario_class_x_run_index",
        "donor_schedule_source": (
            "committed released-union decision logs or future launch-manifest-bound released-union "
            "schedule, never target outcome feedback"
        ),
        "donor_selection": {
            "method": "deterministic_hash_from_committed_identifiers",
            "same_scenario_class_required": True,
            "exclude_target_scenario_pair": True,
            "exclude_target_seed": True,
            "fallback_if_no_donor": "PLACEBO_CONTROL_INFRA_NULL",
        },
        "matched_budget_fields": [
            "intervention_window_count",
            "total_brake_frames",
            "window_start_frame_offsets",
            "window_duration_frames",
            "release_clear_frame_rule",
        ],
        "forbidden_live_inputs": list(SEMANTIC_TRIGGER_FIELDS),
        **{field: False for field in SEMANTIC_TRIGGER_FIELDS},
        **false_authorizations(),
    }
    return arm


def build_matching_contract() -> dict[str, Any]:
    return {
        "contract_id": "neuroncap_placebo_matching_contract_v1",
        "benchmark_family": "NeuroNCAP",
        "future_arms": [
            "off_baseline",
            "released_union_semantic_reference",
            PRIMARY_PLACEBO_ID,
        ],
        "reference_only_prior_control": "iter13_rss_style_envelope",
        "same_frozen_planner_required": True,
        "same_benchmark_stack_required": True,
        "same_route_scenario_list_required": True,
        "seed_pairing_required": True,
        "target_run_indices_per_pair": 20,
        "class_level_matching_required": True,
        "donor_exclusion_required": True,
        "actuator_budget_matching_required": True,
        "one_pass_analyzer_reuse_required": True,
        "hidden_tuning_forbidden": True,
        "post_run_schedule_selection_forbidden": True,
        "future_launch_manifest_must_bind": [
            "scenario_pair_ids",
            "scenario_classes",
            "run_indices",
            "arm_ids",
            "donor_schedule_ids",
            "donor_exclusion_receipts",
            "actuator_budget_summaries",
            "patch_file_sha256",
            "analyzer_file_sha256",
            "environment_receipts",
        ],
        **false_authorizations(),
    }


def build_verdict_contract() -> dict[str, Any]:
    return {
        "contract_id": "neuroncap_placebo_verdict_contract_v1",
        "future_verdict_classes": list(EXPECTED_VERDICT_CLASSES),
        "primary_metric": "NCAP score",
        "primary_comparison": "released_union_ncap_minus_placebo_ncap",
        "primary_bootstrap": {
            "cluster_unit": "scenario_pair",
            "seed_paired": True,
            "discipline": "same scenario-clustered bootstrap family as analyze_power14.py",
        },
        "minimum_semantic_margin_ncap": 0.25,
        "semantic_value_confirmed_rule": (
            "released_union_ncap_minus_placebo_ncap >= 0.25 and the 95% scenario-clustered "
            "CI excludes zero from below"
        ),
        "placebo_explains_gain_rule": (
            "placebo_ncap_minus_off_ncap CI excludes zero from below while released_union_ncap_"
            "minus_placebo_ncap fails the semantic margin or includes zero"
        ),
        "placebo_harm_or_null_rule": (
            "placebo_ncap_minus_off_ncap includes zero, excludes zero from above, or creates an "
            "unhidden safe-progress cost"
        ),
        "infra_null_rule": (
            "any source, launch-manifest, donor-exclusion, matching, analyzer, or no-hidden-tuning "
            "gate fails"
        ),
        "secondary_metric": "safe_progress",
        "secondary_metric_policy": "reported at full weight and cannot be hidden by NCAP score",
        "null_publication_policy": "all nulls published at full weight",
        **false_authorizations(),
    }


def build_design_contract() -> dict[str, Any]:
    return {
        "design_version": DESIGN_VERSION,
        "design_status": "future_protocol_only",
        "primary_placebo_arm": build_primary_placebo_arm(),
        "matching_contract": build_matching_contract(),
        "verdict_contract": build_verdict_contract(),
        "future_execution_requires": [
            "fresh HYPOTHESIS.md",
            "operator approval for GPU use",
            "launch manifest passing this design",
            "hash-bound patch files",
            "hash-bound analyzer files",
            "full null publication",
        ],
        "claim_boundary": BOUNDARY,
        **false_authorizations(),
    }


def check_false_authorizations(item: Any, problems: list[str], path: str = "root") -> None:
    if isinstance(item, dict):
        for field in FALSE_AUTHORIZATION_FIELDS:
            if field in item and item[field] is not False:
                problems.append(f"authorization-not-false:{path}.{field}")
        for key, value in item.items():
            check_false_authorizations(value, problems, f"{path}.{key}")
    elif isinstance(item, list):
        for index, value in enumerate(item):
            check_false_authorizations(value, problems, f"{path}[{index}]")


def validate_design_contract(contract: dict[str, Any], problems: list[str]) -> dict[str, int]:
    primary_arm = contract.get("primary_placebo_arm")
    matching = contract.get("matching_contract")
    verdict = contract.get("verdict_contract")
    primary_arm_count = 0
    semantic_trigger_leak_count = 0
    missing_verdict_class_count = 0
    if not isinstance(primary_arm, dict):
        problems.append("primary-placebo-arm-not-dict")
        primary_arm = {}
    if primary_arm.get("primary_placebo") is True:
        primary_arm_count = 1
    if primary_arm.get("arm_id") != PRIMARY_PLACEBO_ID:
        problems.append(f"primary-placebo-id-mismatch:{primary_arm.get('arm_id')!r}")
    for field in SEMANTIC_TRIGGER_FIELDS:
        if primary_arm.get(field) is not False:
            semantic_trigger_leak_count += 1
            problems.append(f"semantic-trigger-not-false:{field}")
    if primary_arm.get("semantic_trigger_removed") is not True:
        problems.append("semantic-trigger-removed-not-true")
    donor = primary_arm.get("donor_selection")
    if not isinstance(donor, dict):
        problems.append("donor-selection-not-dict")
    else:
        for key in (
            "same_scenario_class_required",
            "exclude_target_scenario_pair",
            "exclude_target_seed",
        ):
            if donor.get(key) is not True:
                problems.append(f"donor-selection-{key}-not-true")
        if donor.get("fallback_if_no_donor") != "PLACEBO_CONTROL_INFRA_NULL":
            problems.append("donor-selection-fallback-mismatch")
    if not isinstance(matching, dict):
        problems.append("matching-contract-not-dict")
        matching = {}
    else:
        for key in (
            "same_frozen_planner_required",
            "same_benchmark_stack_required",
            "same_route_scenario_list_required",
            "seed_pairing_required",
            "class_level_matching_required",
            "donor_exclusion_required",
            "actuator_budget_matching_required",
            "one_pass_analyzer_reuse_required",
            "hidden_tuning_forbidden",
            "post_run_schedule_selection_forbidden",
        ):
            if matching.get(key) is not True:
                problems.append(f"matching-{key}-not-true")
        if PRIMARY_PLACEBO_ID not in matching.get("future_arms", []):
            problems.append("matching-primary-placebo-arm-missing")
    if not isinstance(verdict, dict):
        problems.append("verdict-contract-not-dict")
        verdict = {}
    else:
        classes = verdict.get("future_verdict_classes")
        if set(classes or []) != set(EXPECTED_VERDICT_CLASSES):
            missing = sorted(set(EXPECTED_VERDICT_CLASSES) - set(classes or []))
            missing_verdict_class_count += len(missing)
            problems.append(f"future-verdict-classes-mismatch:{classes!r}")
        if verdict.get("primary_comparison") != "released_union_ncap_minus_placebo_ncap":
            problems.append("primary-comparison-mismatch")
        if verdict.get("secondary_metric") != "safe_progress":
            problems.append("secondary-metric-mismatch")
        if "full weight" not in str(verdict.get("null_publication_policy", "")):
            problems.append("null-publication-policy-missing")
    if BOUNDARY not in contract.get("claim_boundary", ""):
        problems.append("claim-boundary-mismatch")
    if primary_arm_count != 1:
        problems.append(f"primary-placebo-arm-count-mismatch:{primary_arm_count}")
    check_false_authorizations(contract, problems)
    return {
        "primary_placebo_arm_count": primary_arm_count,
        "semantic_trigger_leak_count": semantic_trigger_leak_count,
        "missing_verdict_class_count": missing_verdict_class_count,
    }


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    full_power_text, text_problems = load_text(repo_root / FULL_POWER_RESULT_PATH, "full-power")
    problems.extend(text_problems)
    full_power_hypothesis_text, text_problems = load_text(
        repo_root / FULL_POWER_HYPOTHESIS_PATH,
        "full-power-hypothesis",
    )
    problems.extend(text_problems)
    full_power_analyzer_text, text_problems = load_text(
        repo_root / FULL_POWER_ANALYZER_PATH,
        "full-power-analyzer",
    )
    problems.extend(text_problems)
    rss_text, text_problems = load_text(repo_root / RSS_RESULT_PATH, "rss-result")
    problems.extend(text_problems)
    opportunity_text, text_problems = load_text(
        repo_root / OPPORTUNITY_RESULT_PATH,
        "opportunity-result",
    )
    problems.extend(text_problems)
    opportunity_report, json_problems = load_json(
        repo_root / OPPORTUNITY_REPORT_PATH,
        "opportunity-report",
    )
    problems.extend(json_problems)
    iter132_text, text_problems = load_text(repo_root / ITER132_RESULT_PATH, "iter132-result")
    problems.extend(text_problems)
    handoff_text, text_problems = load_text(repo_root / HANDOFF_PATH, "handoff")
    problems.extend(text_problems)

    source_facts = validate_source_inputs(
        full_power_text,
        full_power_hypothesis_text,
        full_power_analyzer_text,
        rss_text,
        opportunity_text,
        opportunity_report,
        iter132_text,
        handoff_text,
        problems,
    )
    design_contract = build_design_contract()
    design_summary = validate_design_contract(design_contract, problems)
    summary = {
        **design_summary,
        "future_arm_count": len(design_contract["matching_contract"]["future_arms"]),
        "future_verdict_class_count": len(EXPECTED_VERDICT_CLASSES),
        "false_authorization_field_count": len(FALSE_AUTHORIZATION_FIELDS),
        "true_authorization_count": 0,
        "gpu_authorized": False,
        "neuroncap_execution_authorized": False,
        "hugsim_execution_authorized": False,
        "semantic_trigger_leak_count": design_summary["semantic_trigger_leak_count"],
        "source_problem_count": len([problem for problem in problems if "missing" in problem]),
    }
    report = {
        "iteration": 133,
        "verdict": INFRA_NULL_VERDICT if problems else COMPLETE_VERDICT,
        "problems": problems,
        "source_paths": {
            "full_power_result": str(FULL_POWER_RESULT_PATH),
            "full_power_hypothesis": str(FULL_POWER_HYPOTHESIS_PATH),
            "full_power_analyzer": str(FULL_POWER_ANALYZER_PATH),
            "rss_result": str(RSS_RESULT_PATH),
            "opportunity_result": str(OPPORTUNITY_RESULT_PATH),
            "opportunity_report": str(OPPORTUNITY_REPORT_PATH),
            "iter132_result": str(ITER132_RESULT_PATH),
            "handoff": str(HANDOFF_PATH),
        },
        "source_facts": source_facts,
        "design_contract": design_contract,
        "summary": summary,
        "claim_boundary": BOUNDARY,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    contract = report["design_contract"]
    arm = contract["primary_placebo_arm"]
    verdict_contract = contract["verdict_contract"]
    lines = [
        "# Iteration 133 - NeuroNCAP placebo semantics control design",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
        f"- `primary_placebo_arm_count`: `{summary['primary_placebo_arm_count']}`",
        f"- `future_arm_count`: `{summary['future_arm_count']}`",
        f"- `future_verdict_class_count`: `{summary['future_verdict_class_count']}`",
        f"- `semantic_trigger_leak_count`: `{summary['semantic_trigger_leak_count']}`",
        f"- `true_authorization_count`: `{summary['true_authorization_count']}`",
        f"- `gpu_authorized`: `{summary['gpu_authorized']}`",
        f"- `neuroncap_execution_authorized`: `{summary['neuroncap_execution_authorized']}`",
        f"- `hugsim_execution_authorized`: `{summary['hugsim_execution_authorized']}`",
        "",
        "## Primary Placebo Arm",
        "",
        f"- arm id: `{arm['arm_id']}`",
        f"- actuator family: `{arm['actuator_family']}`",
        f"- semantic trigger removed: `{arm['semantic_trigger_removed']}`",
        f"- budget match unit: `{arm['budget_match_unit']}`",
        f"- donor method: `{arm['donor_selection']['method']}`",
        f"- donor excludes target pair: `{arm['donor_selection']['exclude_target_scenario_pair']}`",
        f"- donor excludes target seed: `{arm['donor_selection']['exclude_target_seed']}`",
        "",
        "## Future Verdict Classes",
        "",
    ]
    for verdict_class in verdict_contract["future_verdict_classes"]:
        lines.append(f"- `{verdict_class}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            BOUNDARY,
            "",
        ]
    )
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
        lines.append("")
    return "\n".join(lines)


def render_note(report: dict[str, Any]) -> str:
    facts = report["source_facts"]
    contract = report["design_contract"]
    arm = contract["primary_placebo_arm"]
    verdict_contract = contract["verdict_contract"]
    lines = [
        "# NeuroNCAP placebo semantics control design",
        "",
        "Status: iteration-133 adversarial-control design note. This freezes a future placebo/sham",
        "control protocol only; it authorizes no GPU launch, NeuroNCAP execution, HUGSIM execution,",
        "scenario generation, reserved artifact creation, repair, deployment, production, commercial,",
        "or frontier-equivalence claim.",
        "",
        "## Source Anchors",
        "",
        f"- full-power NCAP delta: `{facts['full_power']['ncap_delta_best_minus_off']}`",
        f"- full-power NCAP CI95: `{facts['full_power']['ncap_delta_ci95']}`",
        f"- full-power safe-progress delta: `{facts['full_power']['safe_progress_delta_best_minus_off']}`",
        f"- RSS-style union-minus-RSS safe-progress: `{facts['rss_style_baseline']['union_minus_rss_safe_progress']}`",
        f"- opportunity-audit rho: `{facts['opportunity_audit']['rho']}`",
        "",
        "## Primary Placebo",
        "",
        f"`{arm['arm_id']}` preserves the released union's latched-stop/release actuator family but",
        "removes live Sentinel risk semantics. It replays deterministic timing/budget windows from",
        "donor schedules selected by committed identifiers while excluding the target scenario pair",
        "and target seed.",
        "",
        "## Future Run Contract",
        "",
        "- OFF, released union, and placebo arms must run under the same frozen planner and benchmark stack.",
        "- The future launch manifest must bind scenario ids, run indices, donor ids, actuator budgets, patch hashes, analyzer hashes, and environment receipts.",
        "- The analyzer must report NCAP and safe-progress; safe-progress cannot be hidden by a benchmark-score win.",
        "- Nulls publish at full weight.",
        "",
        "## Verdict Classes",
        "",
    ]
    for verdict_class in verdict_contract["future_verdict_classes"]:
        lines.append(f"- `{verdict_class}`")
    lines.extend(["", "## Claim Boundary", "", BOUNDARY, ""])
    return "\n".join(lines)


def write_outputs(
    report: dict[str, Any],
    report_path: Path,
    markdown_path: Path,
    note_path: Path,
    command_path: Path,
    command_text: str,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    command_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report))
    note_path.write_text(render_note(report))
    command_path.write_text(command_text.rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--note", type=Path, default=DESIGN_NOTE_PATH)
    parser.add_argument("--command", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    command_text = (
        "python3 experiments/iter133_neuroncap_placebo_semantics_control_design/"
        "generate_neuroncap_placebo_semantics_control_design.py"
    )
    write_outputs(
        report,
        repo_root / args.report,
        repo_root / args.markdown,
        repo_root / args.note,
        repo_root / args.command,
        command_text,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0 if report["verdict"] == COMPLETE_VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
