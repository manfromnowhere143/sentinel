from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ITER76_TEST_PATH = Path(__file__).resolve().parents[0] / "test_iter76_switch_foreground_bridge.py"
ITER76_SPEC = importlib.util.spec_from_file_location("iter76_test_helpers", ITER76_TEST_PATH)
assert ITER76_SPEC is not None
iter76_helpers = importlib.util.module_from_spec(ITER76_SPEC)
assert ITER76_SPEC.loader is not None
ITER76_SPEC.loader.exec_module(iter76_helpers)

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter92_hugsim_path_proximity_arbitration"
    / "analyze_path_proximity_arbitration.py"
)
SPEC = importlib.util.spec_from_file_location("iter92_arbitration", MODULE_PATH)
assert SPEC is not None
arbitration = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(arbitration)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _event91(
    audit_id: str,
    scenario: str,
    role: str,
    support_object_id: int,
    replay_ts: float,
    alignment: str,
    label: str,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": support_object_id,
        "replay_ts": replay_ts,
        "replay_alignment": alignment,
        "active_bridge_supported_count": 0,
        "row_label": label,
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter91_verdict: str = "HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE",
) -> tuple[Path, Path]:
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.5, [h._obj(9, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(4.0, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.75, [h._obj(10, [0.0, 9.0]), h._obj(24, [0.0, 1.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter91 = _write_json(
        tmp_path / "iter91.json",
        {
            "verdict": iter91_verdict,
            "infra_problems": [],
            "summary": {"active_bridge_supported_total": 0},
            "events": [
                _event91(
                    "both_distinct_extreme",
                    "scene-0138-extreme-00",
                    "pre",
                    9,
                    5.5,
                    "exact_bridge_ts",
                    "provenance_near_path_inactive",
                ),
                _event91(
                    "ttc_medium_a",
                    "scene-0071-medium-01",
                    "pre",
                    10,
                    4.0,
                    "exact_bridge_ts",
                    "provenance_near_path_inactive",
                ),
                _event91(
                    "ttc_medium_a",
                    "scene-0071-medium-01",
                    "active",
                    10,
                    5.75,
                    "nearest_before_bridge_ts",
                    "path_active_provenance_far_with_bridge_nonactive",
                ),
            ],
        },
    )
    return iter59, iter91


def test_path_proximity_arbitration_split_complete(tmp_path: Path) -> None:
    report = arbitration.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "path_provenance_same_nonactive"
    assert labels[("ttc_medium_a", "pre")] == "path_provenance_same_nonactive"
    assert labels[("ttc_medium_a", "active")] == "path_best_active_no_bridge"
    active_row = next(row for row in report["events"] if row["event_role"] == "active")
    assert active_row["path_best"]["object_id"] == 24
    assert active_row["path_best"]["state"] == "active"
    assert active_row["path_best"]["bridge_geometry"]["distance_band"] == "no_support"
    assert active_row["provenance_best"]["object_id"] == 10
    assert active_row["provenance_best"]["state"] == "subthreshold"


def test_path_proximity_arbitration_blocks_bad_iter91_verdict(tmp_path: Path) -> None:
    report = arbitration.build_report(*_reports(tmp_path, iter91_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_PATH_PROXIMITY_ARBITRATION_BLOCKED"
    assert report["events"] == []
    assert (
        "iter91-verdict-not-HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE"
        in report["infra_problems"]
    )
