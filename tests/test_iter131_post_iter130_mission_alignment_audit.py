from __future__ import annotations

import hashlib
import importlib.util
import json
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

HISTORICAL_REPORT_PATH = (
    MODULE_PATH.parent
    / "proof-audit"
    / "post_iter130_mission_alignment_audit_report.json"
)
HISTORICAL_REPORT_SHA256 = (
    "a4a6e5324ac52ece55c0eb91d60b7bec80615a078943475ac744bed40e63248a"
)


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


def test_committed_post_iter130_audit_retains_point_in_time_complete_evidence() -> None:
    raw_report = HISTORICAL_REPORT_PATH.read_bytes()
    report = json.loads(raw_report)

    assert hashlib.sha256(raw_report).hexdigest() == HISTORICAL_REPORT_SHA256
    assert report["verdict"] == audit.COMPLETE_VERDICT
    assert report["problems"] == []
    assert report["summary"] == {
        "check_count": 14,
        "passed_check_count": 14,
        "problem_count": 0,
        "source_anchor_count": len(audit.SOURCE_ANCHORS),
    }
    assert all(item["passed"] for item in report["checks"])


def test_current_audit_replay_fails_closed_without_a_live_probe() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = audit.build_report(repo)

    assert report["verdict"] == audit.INFRA_NULL_VERDICT
    assert report["problems"] == []
    failed = [item for item in report["checks"] if not item["passed"]]
    assert failed == [
        {
            "label": "handoff-post-130",
            "required": [
                "newest completed experiment is iteration 130 or newer",
                "GPU_RUN_STATE= reported by the live probe",
            ],
            "missing": ["GPU_RUN_STATE= reported by the live probe"],
            "passed": False,
        }
    ]


def test_offline_unknown_tombstone_does_not_impersonate_live_probe_evidence() -> None:
    tombstone = (
        "Canonical completed experiment: experiments/iter134_result/RESULT.md\n"
        "Observation status: "
        "OBSERVATION_UNAVAILABLE_SOURCE_BOUND_LIFECYCLE_OBSERVER_NOT_ACCEPTED\n"
        "Lifecycle state: UNKNOWN\n"
    )

    check = audit.check_handoff_freshness(tombstone)

    assert check["passed"] is False
    assert check["missing"] == ["GPU_RUN_STATE= reported by the live probe"]
