from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter116_hugsim_support_core_collision_actor_timeline"
    / "analyze_support_core_collision_actor_timeline.py"
)
SPEC = importlib.util.spec_from_file_location("iter116_timeline", MODULE_PATH)
assert SPEC is not None
timeline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(timeline)


def test_timeline_frame_phase_labels() -> None:
    assert timeline.frame_phase(1.0, 2.0) == "pre_fire"
    assert timeline.frame_phase(2.0, 2.0) == "at_fire"
    assert timeline.frame_phase(2.25, 2.0) == "post_fire_pre_collision"


def test_timeline_verdict_blocks_row_problem() -> None:
    rows = [{"first_support_phase": "never_before_collision", "problems": []} for _ in range(7)]
    rows.append({"first_support_phase": "never_before_collision", "problems": ["bad"]})
    summary = {"row_count": 8, "first_support_phase_counts": {"never_before_collision": 8}}

    assert timeline.choose_verdict([], rows, summary) == timeline.INFRA_NULL_VERDICT


def test_timeline_verdict_requires_eight_phase_labels() -> None:
    rows = [{"first_support_phase": "never_before_collision", "problems": []} for _ in range(8)]
    bad_summary = {"row_count": 8, "first_support_phase_counts": {"never_before_collision": 7}}

    assert timeline.choose_verdict([], rows, bad_summary) == timeline.INFRA_NULL_VERDICT


def test_iter112_proof_builds_complete_timeline_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = timeline.build_report(
        repo
        / "experiments"
        / "iter115_hugsim_support_core_monitor_set_ordering"
        / "proof-ordering"
        / "support_core_monitor_set_ordering_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == timeline.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["first_support_phase_counts"].values()) == 8
