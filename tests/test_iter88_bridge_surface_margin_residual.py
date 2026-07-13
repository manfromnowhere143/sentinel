from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter88_hugsim_bridge_surface_margin_residual"
    / "analyze_bridge_surface_margin_residual.py"
)
SPEC = importlib.util.spec_from_file_location("iter88_residual", MODULE_PATH)
assert SPEC is not None
residual = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(residual)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _metric(
    state: str,
    min_cpa: float,
    active_cpa_margin_m: float,
    *,
    ttc: float | None = None,
    active_ttc_margin_s: float | None = None,
    ttc_borderline: bool = False,
) -> dict:
    return {
        "state": state,
        "min_cpa": min_cpa,
        "active_cpa_margin_m": active_cpa_margin_m,
        "ttc": ttc,
        "active_ttc_margin_s": active_ttc_margin_s,
        "cpa_active_logged_threshold": False,
        "ttc_active_logged_threshold": False,
        "cpa_borderline_registered": False,
        "ttc_borderline_registered": ttc_borderline,
        "cpa_rank": 2,
        "ttc_rank": 1 if ttc is not None else None,
    }


def _event85(audit_id: str, scenario: str, role: str, object_id: int, band: str, distance: float) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": object_id,
        "selected_bridge": {"distance_band": "no_support"},
        "support_bridge": {"distance_band": band, "best_distance_m": distance},
        "row_label": "path_horizon_support_bridge_timing_split",
        "problems": [],
    }


def _event87(
    audit_id: str,
    scenario: str,
    role: str,
    object_id: int,
    replay_ts: float,
    alignment: str,
    metric: dict,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": object_id,
        "selection": {"replay_ts": replay_ts, "alignment": alignment},
        "replay_metric": metric,
        "row_label": "interval_support_surface_arrival"
        if metric["state"] == "borderline"
        else "interval_support_surface_miss",
        "problems": [],
    }


def _reports(tmp_path: Path, *, iter87_verdict: str = "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"):
    iter85_events = [
        _event85("both_distinct_extreme", "scene-0138-extreme-00", "pre", 9, "ambiguous", 3.7),
        _event85("ttc_medium_a", "scene-0071-medium-01", "pre", 10, "match", 1.1),
        _event85("ttc_medium_a", "scene-0071-medium-01", "active", 10, "match", 1.3),
    ]
    iter87_events = [
        _event87(
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            "pre",
            9,
            5.5,
            "exact_bridge_ts",
            _metric("borderline", 21.5, 20.0, ttc=4.8, active_ttc_margin_s=2.3, ttc_borderline=True),
        ),
        _event87(
            "ttc_medium_a",
            "scene-0071-medium-01",
            "pre",
            10,
            4.0,
            "exact_bridge_ts",
            _metric("subthreshold", 11.1, 9.6),
        ),
        _event87(
            "ttc_medium_a",
            "scene-0071-medium-01",
            "active",
            10,
            5.75,
            "nearest_before_bridge_ts",
            _metric("subthreshold", 12.1, 10.6),
        ),
    ]
    iter85 = _write_json(
        tmp_path / "iter85.json",
        {"verdict": "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE", "infra_problems": [], "events": iter85_events},
    )
    iter87 = _write_json(
        tmp_path / "iter87.json",
        {"verdict": iter87_verdict, "infra_problems": [], "events": iter87_events},
    )
    return iter85, iter87


def test_bridge_surface_margin_residual_split_complete(tmp_path: Path) -> None:
    report = residual.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "bridge_surface_ttc_borderline_cpa_far"
    assert labels[("ttc_medium_a", "pre")] == "bridge_surface_no_finite_ttc_cpa_far"
    assert labels[("ttc_medium_a", "active")] == "bridge_surface_no_finite_ttc_cpa_far"
    assert report["summary"]["row_label_counts"]["bridge_surface_ttc_borderline_cpa_far"] == 1
    assert report["summary"]["row_label_counts"]["bridge_surface_no_finite_ttc_cpa_far"] == 2
    assert report["summary"]["replay_state_counts"]["borderline"] == 1
    assert report["summary"]["replay_state_counts"]["subthreshold"] == 2


def test_bridge_surface_margin_residual_blocks_bad_iter87_verdict(tmp_path: Path) -> None:
    report = residual.build_report(*_reports(tmp_path, iter87_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_BLOCKED"
    assert report["events"] == []
    assert "iter87-verdict-not-HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE" in report["infra_problems"]
