from __future__ import annotations

from scripts.paper_evidence import validate_paper_text, validate_submission


def test_current_archived_paper_is_not_submission_ready() -> None:
    problems = validate_submission()

    assert any(problem.startswith("paper_status:") for problem in problems)
    assert "missing:HUGSIM transfer boundary" in problems
    assert "missing:iteration-134 control" in problems


def test_evidence_complete_bounded_text_passes_content_gate() -> None:
    text = """
    HUGSIM produced a transfer null. Iteration 134 tested the control, and semantic attribution
    remains unresolved.
    """

    assert validate_paper_text(text) == []


def test_universal_decoder_claim_is_rejected() -> None:
    text = """
    HUGSIM produced a transfer null. Iteration 134 showed semantic attribution remains unresolved.
    The defect is not in any decoder above it.
    """

    assert "forbidden:not in any decoder above it" in validate_paper_text(text)
