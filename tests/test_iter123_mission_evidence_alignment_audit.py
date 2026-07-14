from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter123_mission_evidence_alignment_audit"
    / "verify_mission_evidence_alignment_audit.py"
)
SPEC = importlib.util.spec_from_file_location("iter123_audit", MODULE_PATH)
assert SPEC is not None
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)


def test_missing_items_normalizes_whitespace() -> None:
    text = "This audit authorizes no repair, actor-causality, threshold-value, transfer\nupgrade"
    required = ["actor-causality, threshold-value, transfer upgrade"]

    assert audit.missing_items(text, required) == []


def test_verdict_blocks_failed_check() -> None:
    checks = [{"label": "x", "passed": False, "missing": ["needed"]}]

    assert audit.choose_verdict([], checks) == audit.INFRA_NULL_VERDICT


def test_committed_audit_builds_complete() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = audit.build_report(repo)

    assert report["verdict"] == audit.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["source_anchor_count"] == len(audit.SOURCE_ANCHORS)
    assert all(item["passed"] for item in report["checks"])
