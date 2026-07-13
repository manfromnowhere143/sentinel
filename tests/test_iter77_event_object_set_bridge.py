from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ITER76_TEST_PATH = Path(__file__).resolve().parents[0] / "test_iter76_switch_foreground_bridge.py"
ITER76_SPEC = importlib.util.spec_from_file_location("iter76_test_helpers", ITER76_TEST_PATH)
assert ITER76_SPEC is not None
iter76_helpers = importlib.util.module_from_spec(ITER76_SPEC)
assert ITER76_SPEC.loader is not None
ITER76_SPEC.loader.exec_module(iter76_helpers)

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter77_hugsim_event_object_set_bridge"
    / "analyze_event_object_set_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter77_event_object_set_bridge", MODULE_PATH)
assert SPEC is not None
event_set_bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(event_set_bridge)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


@pytest.fixture(name="reports")
def reports_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    iter59, iter70, iter72, iter73, iter74, iter75 = iter76_helpers._reports(tmp_path, active_match=True)
    iter76 = _write_json(
        tmp_path / "iter76.json",
        {
            "verdict": "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "no_foreground_bridge_support",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "no_foreground_bridge_support",
                },
            ],
        },
    )
    return iter59, iter70, iter72, iter73, iter74, iter75, iter76


def test_event_object_set_active_match_complete(reports: tuple[Path, Path, Path, Path, Path, Path, Path]) -> None:
    report = event_set_bridge.build_report(*reports)
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_EVENT_SET_FOREGROUND_ACTIVE_MATCH_COMPLETE"
    assert labels["both_distinct_extreme"] == "active_set_foreground_match"
    assert labels["ttc_medium_a"] == "active_set_foreground_match"


def test_event_object_set_blocks_bad_source_verdict(
    tmp_path: Path,
    reports: tuple[Path, Path, Path, Path, Path, Path, Path],
) -> None:
    iter59, iter70, iter72, iter73, iter74, iter75, _iter76 = reports
    bad_iter76 = _write_json(
        tmp_path / "bad_iter76.json",
        {"verdict": "WRONG", "infra_problems": [], "episodes": []},
    )
    report = event_set_bridge.build_report(iter59, iter70, iter72, iter73, iter74, iter75, bad_iter76)

    assert report["verdict"] == "HUGSIM_EVENT_SET_FOREGROUND_BRIDGE_BLOCKED"
    assert report["episodes"] == []
    assert "iter76-verdict-not-HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE" in report["infra_problems"]
