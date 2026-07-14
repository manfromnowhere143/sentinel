from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter126_support_core_candidate_manifest_preflight"
    / "generate_support_core_candidate_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("iter126_manifest", MODULE_PATH)
assert SPEC is not None
manifest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(manifest)


def test_mutation_family_pairs_cover_timing_and_branch_cases() -> None:
    never_supported = {
        "archetype_id": "blindspot_never_supported_selected_nearest",
        "support_side_branch": "never_supported_reference",
        "timing_gap_class": "no_pre_fire_support",
    }
    post_fire = {
        "archetype_id": "blindspot_post_fire_support_selected_nearest",
        "support_side_branch": "post_fire_support_only",
        "timing_gap_class": "post_fire_support",
    }
    drifted = {
        "archetype_id": "blindspot_pre_support_drifted_selected_not_nearest",
        "support_side_branch": "pre_fire_support_drifted_outside_support",
        "timing_gap_class": "measured_support_gap",
    }
    lost = {
        "archetype_id": "blindspot_pre_support_lost_absent_selected_nearest",
        "support_side_branch": "pre_fire_support_lost_absent_at_fire",
        "timing_gap_class": "measured_support_gap",
    }

    assert (
        manifest.mutation_family(never_supported, "branch_stress")
        == "unsupported_nearest_reference_pressure"
    )
    assert (
        manifest.mutation_family(never_supported, "counterfactual_control")
        == "introduce_pre_fire_support_reference_control"
    )
    assert manifest.mutation_family(post_fire, "branch_stress") == "post_fire_support_delay_pressure"
    assert (
        manifest.mutation_family(post_fire, "counterfactual_control")
        == "shift_post_fire_evidence_to_pre_fire_control"
    )
    assert manifest.mutation_family(drifted, "branch_stress") == "support_drift_outside_band_sweep"
    assert (
        manifest.mutation_family(drifted, "counterfactual_control")
        == "support_band_border_continuity_control"
    )
    assert manifest.mutation_family(lost, "branch_stress") == "support_loss_gap_sweep"
    assert (
        manifest.mutation_family(lost, "counterfactual_control")
        == "same_object_visibility_continuity_control"
    )


def test_committed_inputs_build_complete_manifest() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = manifest.build_report(
        repo / manifest.ITER125_REPORT_PATH,
        repo / manifest.ITER125_RESULT_PATH,
        repo / manifest.ITER125_DESIGN_NOTE_PATH,
    )

    assert report["verdict"] == manifest.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["archetype_count"] == 5
    assert report["summary"]["candidate_count"] == 10
    assert report["summary"]["candidate_role_counts"] == {
        "branch_stress": 5,
        "counterfactual_control": 5,
    }
    assert report["summary"]["role_pair_complete_count"] == 5
    assert report["summary"]["source_slot_count"] == 8
    assert report["summary"]["covered_source_slot_count"] == 8
    assert report["summary"]["missing_source_slot_count"] == 0


def test_each_archetype_has_exactly_one_branch_and_control_candidate() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = manifest.build_report(
        repo / manifest.ITER125_REPORT_PATH,
        repo / manifest.ITER125_RESULT_PATH,
        repo / manifest.ITER125_DESIGN_NOTE_PATH,
    )
    by_archetype: dict[str, list[str]] = {}
    for candidate in report["manifest_candidates"]:
        by_archetype.setdefault(candidate["archetype_id"], []).append(candidate["candidate_role"])

    assert len(by_archetype) == 5
    assert all(sorted(roles) == ["branch_stress", "counterfactual_control"] for roles in by_archetype.values())


def test_candidates_are_inert_and_carry_gates() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = manifest.build_report(
        repo / manifest.ITER125_REPORT_PATH,
        repo / manifest.ITER125_RESULT_PATH,
        repo / manifest.ITER125_DESIGN_NOTE_PATH,
    )

    for candidate in report["manifest_candidates"]:
        assert candidate["future_hypothesis_required"] is True
        for field in manifest.FALSE_AUTHORIZATION_FIELDS:
            assert candidate[field] is False
        for key in manifest.FORBIDDEN_CANDIDATE_KEYS:
            assert key not in candidate
        assert candidate["source_slot_ids"]
        assert candidate["source_scenarios"]
        assert candidate["mutation_family"]
        assert candidate["candidate_generation_knobs"]
        assert candidate["required_gates"]
