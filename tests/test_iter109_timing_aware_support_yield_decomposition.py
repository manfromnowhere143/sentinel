from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter109_hugsim_timing_aware_support_yield_decomposition"
    / "analyze_timing_aware_support_yield_decomposition.py"
)
SPEC = importlib.util.spec_from_file_location("iter109_decomposition", MODULE_PATH)
assert SPEC is not None
decomposition = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(decomposition)


def test_residual_label_mapping() -> None:
    assert decomposition.residual_label({"support_label": "classifiable_foreground"}) == "classifiable_success"
    assert decomposition.residual_label({"support_label": "background_collision_only"}) == "observed_background_only"
    assert (
        decomposition.residual_label({"support_label": "no_collision_provenance"})
        == "observed_empty_collision_provenance"
    )
    assert decomposition.residual_label({"support_label": "post_collision_fire"}) == "observed_post_collision_fire"
    assert decomposition.residual_label({"support_label": "no_monitor_fire"}) == "observed_no_monitor_fire"
    assert decomposition.residual_label({"support_label": "weird"}) == "observed_infra_or_schema_gap"
    assert decomposition.residual_label({"support_label": "classifiable_foreground", "problems": ["bad"]}) == (
        "observed_infra_or_schema_gap"
    )


def test_choose_verdict_requires_thirteen_labeled_rows() -> None:
    rows = [{"residual_label": "classifiable_success"} for _ in range(12)]

    assert decomposition.choose_verdict(rows, []) == decomposition.INFRA_NULL_VERDICT
    assert decomposition.choose_verdict(rows + [{"residual_label": "observed_background_only"}], []) == (
        decomposition.COMPLETE_VERDICT
    )
    assert decomposition.choose_verdict(rows + [{"residual_label": None}], []) == decomposition.INFRA_NULL_VERDICT
    assert decomposition.choose_verdict(rows + [{"residual_label": "observed_background_only"}], ["bad"]) == (
        decomposition.INFRA_NULL_VERDICT
    )


def test_committed_inputs_build_support_yield_decomposition() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = decomposition.build_report(
        repo
        / "experiments"
        / "iter105_hugsim_timing_aware_provenance_batch_design"
        / "proof-design"
        / "timing_aware_provenance_batch_design_report.json",
        repo
        / "experiments"
        / "iter106_hugsim_timing_aware_launch_manifest"
        / "proof-launch-manifest"
        / "timing_aware_launch_manifest.json",
        repo
        / "experiments"
        / "iter107_hugsim_timing_aware_batch_execution"
        / "proof-execution"
        / "timing_aware_batch_execution_report.json",
        repo
        / "experiments"
        / "iter108_hugsim_timing_aware_batch_actor_match_audit"
        / "proof-actor-match"
        / "timing_aware_batch_actor_match_report.json",
    )

    assert report["verdict"] == decomposition.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["slot_count"] == 13
    assert sum(report["summary"]["residual_counts"].values()) == 13
    assert report["summary"]["classifiable_success"] == 2
    assert report["summary"]["foreground_absent_or_empty_count"] == 7
