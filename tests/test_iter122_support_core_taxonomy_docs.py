from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter122_support_core_taxonomy_documentation"
    / "verify_support_core_taxonomy_docs.py"
)
SPEC = importlib.util.spec_from_file_location("iter122_docs", MODULE_PATH)
assert SPEC is not None
docs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(docs)


def test_boundary_phrase_is_exact_and_bounded() -> None:
    assert docs.BOUNDARY_PHRASE.startswith("descriptive support-core taxonomy only")
    assert "repair" in docs.BOUNDARY_PHRASE
    assert "commercial claim" in docs.BOUNDARY_PHRASE
    assert "transfer upgrade" in docs.BOUNDARY_PHRASE


def test_doc_check_reports_missing_requirements() -> None:
    check = docs.check_doc("sample", "alpha beta", ["alpha", "gamma"])

    assert check["passed"] is False
    assert check["missing"] == ["gamma"]


def test_verdict_blocks_missing_check() -> None:
    checks = [{"label": "x", "passed": False, "missing": ["needed"]}]
    summary = {
        "iter121_verdict": docs.ITER121_VERDICT,
        "two_track_split_count": 8,
        "selected_never_supported_count": 8,
    }

    assert docs.choose_verdict([], checks, summary) == docs.INFRA_NULL_VERDICT


def test_committed_docs_build_complete_verdict() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = docs.build_report(repo)

    assert report["verdict"] == docs.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["two_track_split_count"] == 8
    assert report["summary"]["selected_never_supported_count"] == 8
    assert all(check["passed"] for check in report["checks"])
