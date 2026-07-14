from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter105_hugsim_timing_aware_provenance_batch_design"
    / "analyze_timing_aware_provenance_batch_design.py"
)

spec = importlib.util.spec_from_file_location("iter105_design", MODULE_PATH)
assert spec is not None and spec.loader is not None
ITER105 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ITER105)


def _row(
    index: int,
    *,
    dataset: str = "iter48_easy_medium",
    tier: str = "medium",
    channel: str = "cpa_only",
    timing: str = "long_lead_fire",
    lead: float = 5.0,
    scenario: str | None = None,
) -> dict:
    scenario_value = scenario or f"scene-{index:04d}-{tier}-00"
    label = "unique_cpa_object" if channel == "cpa_only" else "unique_ttc_object"
    return {
        "brake_frames": 20 + index,
        "dataset": dataset,
        "fire_timing_label": timing,
        "fired_frames": 5 + index,
        "first_fire_channel": channel,
        "first_fire_lead_time": lead,
        "first_fire_ts": 10.0,
        "first_on_nc_time": 10.0 + lead,
        "monitor_provenance_label": label,
        "on_collision": True,
        "run": 1,
        "scenario": scenario_value,
        "tier": tier,
    }


def _reports(rows: list[dict]) -> tuple[dict, dict, dict, dict]:
    iter52_pairs = []
    for row in rows:
        timing = "long_lead_brake" if row["fire_timing_label"] == "long_lead_fire" else "short_lead_brake"
        iter52_pairs.append(
            {
                "first_fire_ts": row["first_fire_ts"],
                "first_on_nc_time": row["first_on_nc_time"],
                "lead_time": row["first_fire_lead_time"],
                "run": row["run"],
                "scenario": row["scenario"],
                "timing_bin": timing,
            }
        )
    padding_count = 104 - len(rows)
    for index in range(padding_count):
        pad = _row(1000 + index, scenario=f"pad-{index}")
        pad["on_collision"] = False
        rows.append(pad)
        iter52_pairs.append(
            {
                "first_fire_ts": None,
                "first_on_nc_time": None,
                "lead_time": None,
                "run": 1,
                "scenario": f"pad-{index}",
                "timing_bin": "no_brake_no_surface_proxy",
            }
        )
    iter52 = {"pairs": iter52_pairs, "verdict": ITER105.ITER52_VERDICT}
    iter54 = {"infrastructure_problems": [], "pairs": rows, "verdict": ITER105.ITER54_VERDICT}
    iter59 = {"episodes": [], "infra_problems": [], "verdict": ITER105.ITER59_VERDICT}
    iter104 = {
        "episodes": [],
        "infra_problems": [],
        "summary": {"classifiable_foreground": 1, "min_classifiable_bar": 4},
        "verdict": ITER105.ITER104_VERDICT,
    }
    return iter52, iter54, iter59, iter104


def test_timing_aware_schedule_completes_with_diverse_pool() -> None:
    rows = [
        _row(1, dataset="iter48_easy_medium", tier="easy", channel="cpa_only", lead=9.0),
        _row(2, dataset="iter48_easy_medium", tier="medium", channel="ttc_only", lead=8.0),
        _row(3, dataset="iter49_hard_extreme", tier="hard", channel="cpa_only", lead=7.0),
        _row(4, dataset="iter49_hard_extreme", tier="extreme", channel="ttc_only", lead=6.0),
        _row(5, dataset="iter49_hard_extreme", tier="hard", channel="ttc_only", timing="short_lead_fire", lead=0.5),
    ]
    rows.extend(_row(index, dataset="iter48_easy_medium", tier="medium", lead=float(index)) for index in range(6, 14))
    iter52, iter54, iter59, iter104 = _reports(rows)
    report = ITER105.build_report_from_data_for_test(iter52, iter54, iter59, iter104)
    assert report["verdict"] == ITER105.COMPLETE_VERDICT
    assert report["summary"]["selected_slot_count"] == 13
    assert "short_lead_fire" in report["summary"]["selected_timing_counts"]


def test_support_null_when_primary_pool_is_too_small() -> None:
    rows = [_row(index) for index in range(1, 10)]
    iter52, iter54, iter59, iter104 = _reports(rows)
    report = ITER105.build_report_from_data_for_test(iter52, iter54, iter59, iter104)
    assert report["verdict"] == ITER105.SUPPORT_NULL_VERDICT
    assert any(problem.startswith("primary-pool-too-small") for problem in report["support_problems"])


def test_iter52_timing_mismatch_is_infra_null() -> None:
    rows = [
        _row(1, dataset="iter48_easy_medium", tier="easy", channel="cpa_only", lead=9.0),
        _row(2, dataset="iter48_easy_medium", tier="medium", channel="ttc_only", lead=8.0),
        _row(3, dataset="iter49_hard_extreme", tier="hard", channel="cpa_only", lead=7.0),
        _row(4, dataset="iter49_hard_extreme", tier="extreme", channel="ttc_only", lead=6.0),
        _row(5, dataset="iter49_hard_extreme", tier="hard", channel="ttc_only", timing="short_lead_fire", lead=0.5),
    ]
    rows.extend(_row(index, dataset="iter48_easy_medium", tier="medium", lead=float(index)) for index in range(6, 14))
    iter52, iter54, iter59, iter104 = _reports(rows)
    iter52["pairs"][0]["timing_bin"] = "post_collision_first_brake"
    report = ITER105.build_report_from_data_for_test(iter52, iter54, iter59, iter104)
    assert report["verdict"] == ITER105.INFRA_NULL_VERDICT
    assert any("iter52-timing-bin-mismatch" in problem for problem in report["infra_problems"])


def test_committed_reports_build_complete_timing_aware_schedule() -> None:
    root = Path(__file__).resolve().parents[1]
    report = ITER105.build_report(
        root / "experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json",
        root / "experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json",
        root / "experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json",
        root
        / "experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/"
        / "provenance_batch_actor_match_report.json",
    )
    assert report["verdict"] == ITER105.COMPLETE_VERDICT
    assert report["summary"]["primary_eligible_count"] >= 13
    assert report["summary"]["selected_slot_count"] == 13
