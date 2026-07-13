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
    / "iter82_hugsim_support_surface_bridge_cooccurrence"
    / "analyze_support_surface_bridge_cooccurrence.py"
)
SPEC = importlib.util.spec_from_file_location("iter82_support_cooccurrence", MODULE_PATH)
assert SPEC is not None
support_cooccurrence = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(support_cooccurrence)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(tmp_path: Path, *, iter81_verdict: str = "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE"):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.0, [h._obj(9, [0.0, 1.0])]),
                h._decision_row(7.0, [h._obj(9, [0.0, 9.0])]),
            ],
            [0.0, 1.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.0, [h._obj(10, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter81 = _write_json(
        tmp_path / "iter81.json",
        {
            "verdict": iter81_verdict,
            "infra_problems": [],
            "objects": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "support_object_id": 9,
                    "row_label": "support_object_ever_active",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "support_object_id": 10,
                    "row_label": "support_object_visible_never_surface",
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter81


def test_support_surface_bridge_active_match_complete(tmp_path: Path) -> None:
    report = support_cooccurrence.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["objects"]}

    assert report["verdict"] == "HUGSIM_SUPPORT_SURFACE_BRIDGE_ACTIVE_MATCH_COMPLETE"
    assert labels["both_distinct_extreme"] == "support_surface_bridge_active_match"
    assert labels["ttc_medium_a"] == "support_bridge_never_surface"
    assert report["summary"]["objects_with_surface_bridge_cooccurrence"] == 1


def test_support_surface_bridge_blocks_bad_iter81_verdict(tmp_path: Path) -> None:
    report = support_cooccurrence.build_report(*_reports(tmp_path, iter81_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SUPPORT_SURFACE_BRIDGE_BLOCKED"
    assert report["objects"] == []
    assert "iter81-verdict-not-HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE" in report["infra_problems"]
