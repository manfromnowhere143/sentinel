from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter124_manuscript_report_freshness"
    / "verify_manuscript_report_freshness.py"
)
SPEC = importlib.util.spec_from_file_location("iter124_freshness", MODULE_PATH)
assert SPEC is not None
freshness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(freshness)


def test_missing_items_normalizes_line_wrapping() -> None:
    text = "descriptive support-core taxonomy only; no repair,\nactor-causality"
    required = ["no repair, actor-causality"]

    assert freshness.missing_items(text, required) == []


def test_absent_check_fails_on_stale_marker() -> None:
    check = freshness.check_absent("sample", "Technical report updated 2026-07-10", ["updated 2026-07-10"])

    assert check["passed"] is False
    assert check["unexpected"] == ["updated 2026-07-10"]


def test_committed_report_and_manuscript_are_fresh() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = freshness.build_report(repo)

    assert report["verdict"] == freshness.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["passed_check_count"] == report["summary"]["check_count"]
