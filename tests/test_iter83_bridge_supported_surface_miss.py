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
    / "iter83_hugsim_bridge_supported_surface_miss_decomposition"
    / "analyze_bridge_supported_surface_miss.py"
)
SPEC = importlib.util.spec_from_file_location("iter83_surface_miss", MODULE_PATH)
assert SPEC is not None
surface_miss = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(surface_miss)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(tmp_path: Path, *, iter82_verdict: str = "HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE"):
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
    iter82 = _write_json(
        tmp_path / "iter82.json",
        {
            "verdict": iter82_verdict,
            "infra_problems": [],
            "objects": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "support_object_id": 9,
                    "row_label": "support_surface_bridge_borderline_only",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "support_object_id": 10,
                    "row_label": "support_bridge_never_surface",
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter82


def test_bridge_supported_active_surface_present_complete(tmp_path: Path) -> None:
    report = surface_miss.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["objects"]}

    assert report["verdict"] == "HUGSIM_BRIDGE_SUPPORTED_ACTIVE_SURFACE_PRESENT_COMPLETE"
    assert labels["both_distinct_extreme"] == "bridge_supported_active_surface_present"
    assert labels["ttc_medium_a"] == "bridge_supported_subthreshold_no_finite_ttc"
    assert report["summary"]["bridge_supported_frames"] == 3


def test_bridge_supported_surface_miss_blocks_bad_iter82_verdict(tmp_path: Path) -> None:
    report = surface_miss.build_report(*_reports(tmp_path, iter82_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_BLOCKED"
    assert report["objects"] == []
    assert "iter82-verdict-not-HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE" in report["infra_problems"]
