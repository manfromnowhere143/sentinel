from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter131_post_iter130_mission_alignment_audit"
    / "verify_post_iter130_mission_alignment_audit.py"
)
SPEC = importlib.util.spec_from_file_location("iter131_audit", MODULE_PATH)
assert SPEC is not None
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)


def test_missing_items_normalizes_whitespace() -> None:
    text = "schema-instance\ncreation preflight keeps future artifact work bounded"
    required = ["schema-instance creation preflight keeps future artifact work bounded"]

    assert audit.missing_items(text, required) == []


def test_current_through_at_least_accepts_newer_readme() -> None:
    text = "Honest status up front (current through iteration 131)"

    assert audit.current_through_at_least(text, 130)
    assert not audit.current_through_at_least(text, 132)


def test_handoff_freshness_accepts_newer_experiment() -> None:
    text = (
        "Newest completed experiment: "
        "experiments/iter131_post_iter130_mission_alignment_audit/RESULT.md\n"
        "GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS"
    )

    assert audit.check_handoff_freshness(text)["passed"]


def test_verdict_blocks_failed_check() -> None:
    checks = [{"label": "x", "passed": False, "missing": ["needed"]}]

    assert audit.choose_verdict([], checks) == audit.INFRA_NULL_VERDICT


def test_committed_post_iter130_audit_builds_complete() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = audit.build_report(repo)

    assert report["verdict"] == audit.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["source_anchor_count"] == len(audit.SOURCE_ANCHORS)
    assert report["summary"]["passed_check_count"] == report["summary"]["check_count"]
    assert all(item["passed"] for item in report["checks"])
