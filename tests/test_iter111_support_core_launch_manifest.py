from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter111_hugsim_support_core_launch_manifest"
    / "analyze_support_core_launch_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("iter111_manifest", MODULE_PATH)
assert SPEC is not None
manifest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(manifest)


def _sha(index: int) -> str:
    return f"{index:064x}"[-64:]


def _slot(
    index: int,
    scenario: str,
    run: int,
    tier: str,
    role: str,
    timing: str,
) -> dict:
    return {
        "brake_frames": 10 + index,
        "dataset": "iter49_hard_extreme",
        "design_label": role,
        "exact_positive_sources": ["iter109:classifiable_success:actor_mismatch"] if role.startswith("exact") else [],
        "fire_timing_label": timing,
        "fired_frames": 3 + index,
        "first_fire_channel": "ttc_only",
        "first_fire_lead_time": float(index),
        "first_fire_ts": 10.0,
        "first_on_nc_time": 10.0 + index,
        "run": run,
        "scenario": scenario,
        "scenario_positive_sources": ["iter59:classifiable_foreground:actor_mismatch"],
        "tier": tier,
    }


def _core_rows() -> list[dict]:
    return [
        _slot(1, "scene-0411-hard-00", 2, "hard", "exact_ttc_classifiable_anchor", "short_lead_fire"),
        _slot(2, "scene-0411-extreme-00", 1, "extreme", "exact_ttc_classifiable_anchor", "long_lead_fire"),
        _slot(3, "scene-0038-hard-00", 1, "hard", "exact_ttc_classifiable_anchor", "long_lead_fire"),
        _slot(4, "scene-0038-extreme-00", 1, "extreme", "ttc_classifiable_scenario_analogue", "short_lead_fire"),
        _slot(5, "scene-0038-extreme-00", 2, "extreme", "ttc_classifiable_scenario_analogue", "short_lead_fire"),
        _slot(6, "scene-0383-extreme-00", 2, "extreme", "ttc_classifiable_scenario_analogue", "short_lead_fire"),
        _slot(7, "scene-0411-hard-00", 1, "hard", "ttc_classifiable_scenario_analogue", "short_lead_fire"),
        _slot(8, "scene-0411-extreme-00", 2, "extreme", "ttc_classifiable_scenario_analogue", "long_lead_fire"),
    ]


def _iter110_report(rows: list[dict]) -> dict:
    return {
        "event": {"measurements": {"support_preserving_core_rows": rows}},
        "summary": dict(manifest.EXPECTED_ITER110_SUMMARY),
        "verdict": manifest.ITER110_VERDICT,
    }


def _manifests(rows: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    iter48: dict[str, str] = {}
    iter49: dict[str, str] = {}
    for index, row in enumerate(rows, start=1):
        iter49[row["scenario"]] = _sha(index)
    return iter48, iter49


def _receipts() -> dict:
    return dict(manifest.EXPECTED_STACK)


def _launcher_constants() -> dict:
    return dict(manifest.EXPECTED_LAUNCHER_CONSTANTS)


def test_support_core_manifest_preserves_duplicate_slots() -> None:
    rows = _core_rows()
    iter48, iter49 = _manifests(rows)

    report = manifest.build_report_from_data(
        _iter110_report(rows),
        iter48,
        iter49,
        _receipts(),
        _launcher_constants(),
        {"test": "test"},
    )

    assert report["verdict"] == manifest.COMPLETE_VERDICT
    assert report["summary"]["slot_count"] == 8
    assert report["summary"]["unique_scenario_count"] == 5
    assert report["summary"]["duplicate_scenario_count"] == 3
    assert len({slot["slot_id"] for slot in report["manifest"]["slots"]}) == 8


def test_missing_scenario_sha_blocks_support_core_manifest() -> None:
    rows = _core_rows()
    iter48, iter49 = _manifests(rows)
    iter49.pop("scene-0411-hard-00")

    report = manifest.build_report_from_data(
        _iter110_report(rows),
        iter48,
        iter49,
        _receipts(),
        _launcher_constants(),
        {"test": "test"},
    )

    assert report["verdict"] == manifest.BLOCKED_VERDICT
    assert any("missing-scenario-sha" in problem for problem in report["infra_problems"])


def test_committed_inputs_build_complete_support_core_manifest() -> None:
    root = Path(__file__).resolve().parents[1]

    report = manifest.build_report(
        root
        / "experiments"
        / "iter110_hugsim_support_preserving_candidate_design"
        / "proof-design"
        / "support_preserving_candidate_design_report.json",
        root / "experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256",
        root / "experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256",
        root / "experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json",
        root / "experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh",
    )

    assert report["verdict"] == manifest.COMPLETE_VERDICT
    assert report["summary"]["scenario_sha_bound_count"] == 8
    assert report["summary"]["selected_channel_counts"] == {"ttc_only": 8}
