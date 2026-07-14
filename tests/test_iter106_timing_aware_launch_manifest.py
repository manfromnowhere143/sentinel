from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter106_hugsim_timing_aware_launch_manifest"
    / "analyze_timing_aware_launch_manifest.py"
)

spec = importlib.util.spec_from_file_location("iter106_manifest", MODULE_PATH)
assert spec is not None and spec.loader is not None
ITER106 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ITER106)


def _sha(index: int) -> str:
    return f"{index:064x}"[-64:]


def _slot(index: int, scenario: str, run: int, dataset: str, tier: str, channel: str, timing: str) -> dict:
    return {
        "brake_frames": 10 + index,
        "dataset": dataset,
        "fire_timing_label": timing,
        "fired_frames": 3 + index,
        "first_fire_channel": channel,
        "first_fire_lead_time": float(index),
        "first_fire_ts": 10.0,
        "first_on_nc_time": 10.0 + index,
        "run": run,
        "scenario": scenario,
        "selection_reason": "test",
        "slot_id": f"i105_slot_{index:02d}",
        "slot_index": index,
        "tier": tier,
    }


def _actual_shape_rows() -> list[dict]:
    return [
        _slot(1, "scene-0138-medium-01", 1, "iter48_easy_medium", "medium", "ttc_only", "long_lead_fire"),
        _slot(2, "scene-0064-hard-00", 2, "iter49_hard_extreme", "hard", "cpa_only", "long_lead_fire"),
        _slot(3, "scene-0166-easy-00", 2, "iter48_easy_medium", "easy", "cpa_only", "long_lead_fire"),
        _slot(4, "scene-0138-medium-01", 2, "iter48_easy_medium", "medium", "ttc_only", "long_lead_fire"),
        _slot(5, "scene-0064-easy-00", 2, "iter48_easy_medium", "easy", "cpa_only", "long_lead_fire"),
        _slot(6, "scene-0166-medium-01", 2, "iter48_easy_medium", "medium", "cpa_only", "long_lead_fire"),
        _slot(7, "scene-0064-hard-00", 1, "iter49_hard_extreme", "hard", "cpa_only", "long_lead_fire"),
        _slot(8, "scene-0411-extreme-00", 1, "iter49_hard_extreme", "extreme", "ttc_only", "long_lead_fire"),
        _slot(9, "scene-0071-easy-00", 2, "iter48_easy_medium", "easy", "ttc_only", "long_lead_fire"),
        _slot(10, "scene-0411-hard-00", 2, "iter49_hard_extreme", "hard", "ttc_only", "short_lead_fire"),
        _slot(11, "scene-0138-hard-00", 1, "iter49_hard_extreme", "hard", "cpa_only", "long_lead_fire"),
        _slot(12, "scene-0071-extreme-00", 1, "iter49_hard_extreme", "extreme", "cpa_only", "long_lead_fire"),
        _slot(13, "scene-0064-medium-01", 1, "iter48_easy_medium", "medium", "cpa_only", "long_lead_fire"),
    ]


def _iter105_report(rows: list[dict]) -> dict:
    return {
        "event": {"measurements": {"selected_rows": rows}},
        "summary": ITER106.EXPECTED_SUMMARY,
        "verdict": ITER106.ITER105_VERDICT,
    }


def _manifests(rows: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    iter48: dict[str, str] = {}
    iter49: dict[str, str] = {}
    for index, row in enumerate(rows, start=1):
        target = iter48 if row["dataset"] == "iter48_easy_medium" else iter49
        target[row["scenario"]] = _sha(index)
    return iter48, iter49


def _receipts() -> dict:
    return dict(ITER106.EXPECTED_STACK)


def _launcher_constants() -> dict:
    return dict(ITER106.EXPECTED_LAUNCHER_CONSTANTS)


def test_manifest_preserves_duplicate_slots() -> None:
    rows = _actual_shape_rows()
    iter48, iter49 = _manifests(rows)
    report = ITER106.build_report_from_data(
        _iter105_report(rows),
        iter48,
        iter49,
        _receipts(),
        _launcher_constants(),
        {"test": "test"},
    )
    assert report["verdict"] == ITER106.COMPLETE_VERDICT
    assert report["summary"]["slot_count"] == 13
    assert report["summary"]["unique_scenario_count"] == 11
    assert report["summary"]["duplicate_scenario_count"] == 2
    assert len({slot["slot_id"] for slot in report["manifest"]["slots"]}) == 13


def test_missing_scenario_sha_blocks_manifest() -> None:
    rows = _actual_shape_rows()
    iter48, iter49 = _manifests(rows)
    iter48.pop("scene-0138-medium-01")
    report = ITER106.build_report_from_data(
        _iter105_report(rows),
        iter48,
        iter49,
        _receipts(),
        _launcher_constants(),
        {"test": "test"},
    )
    assert report["verdict"] == ITER106.BLOCKED_VERDICT
    assert any("missing-scenario-sha" in problem for problem in report["infra_problems"])


def test_committed_inputs_build_complete_manifest() -> None:
    root = Path(__file__).resolve().parents[1]
    report = ITER106.build_report(
        root
        / "experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/"
        / "timing_aware_provenance_batch_design_report.json",
        root / "experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256",
        root / "experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256",
        root / "experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json",
        root / "experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh",
    )
    assert report["verdict"] == ITER106.COMPLETE_VERDICT
    assert report["summary"]["scenario_sha_bound_count"] == 13
