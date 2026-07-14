from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter127_post_iter126_mission_alignment_audit"
    / "verify_post_iter126_mission_alignment_audit.py"
)
SPEC = importlib.util.spec_from_file_location("iter127_audit", MODULE_PATH)
assert SPEC is not None
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)


def test_missing_items_normalizes_whitespace() -> None:
    text = "candidate-generation\nmanifest keeps design/preflight boundaries"
    required = ["candidate-generation manifest keeps design/preflight boundaries"]

    assert audit.missing_items(text, required) == []


def test_verdict_blocks_failed_check() -> None:
    checks = [{"label": "x", "passed": False, "missing": ["needed"]}]

    assert audit.choose_verdict([], checks) == audit.INFRA_NULL_VERDICT


def test_committed_post_iter126_audit_builds_complete() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = audit.build_report(repo)

    assert report["verdict"] == audit.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["source_anchor_count"] == len(audit.SOURCE_ANCHORS)
    assert report["summary"]["passed_check_count"] == report["summary"]["check_count"]
    assert all(item["passed"] for item in report["checks"])
