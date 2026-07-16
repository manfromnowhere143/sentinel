#!/usr/bin/env python3
"""Fail closed unless the actual shipped paper carries Sentinel's current evidence boundary."""

from __future__ import annotations

from pathlib import Path

try:
    from mission_state import REPO_ROOT, load_state
except ModuleNotFoundError:  # imported as scripts.paper_evidence in tests
    from scripts.mission_state import REPO_ROOT, load_state


REQUIRED_CONCEPTS = {
    "HUGSIM transfer boundary": ("hugsim", "transfer null"),
    "iteration-134 control": ("iteration 134",),
    "semantic-attribution boundary": ("semantic attribution", "unresolved"),
}
FORBIDDEN_STALE_CLAIMS = (
    "not in any decoder above it",
    "this campaign uses one simulator",
    "across nineteen pre-registered campaign iterations",
)


def validate_paper_text(text: str) -> list[str]:
    lowered = " ".join(text.lower().split())
    problems: list[str] = []
    for label, terms in REQUIRED_CONCEPTS.items():
        if not all(term in lowered for term in terms):
            problems.append(f"missing:{label}")
    for claim in FORBIDDEN_STALE_CLAIMS:
        if claim in lowered:
            problems.append(f"forbidden:{claim}")
    return problems


def validate_submission(repo: Path = REPO_ROOT) -> list[str]:
    state = load_state(repo / "MISSION_STATE.json")
    problems: list[str] = []
    if state.get("paper_state", {}).get("status") != "READY_FOR_PEER_REVIEW_SUBMISSION":
        problems.append(f"paper_status:{state.get('paper_state', {}).get('status')!r}")
    problems.extend(validate_paper_text((repo / "docs/paper/paper.tex").read_text()))
    return problems


if __name__ == "__main__":
    failures = validate_submission()
    if failures:
        raise SystemExit("PAPER EVIDENCE GATE FAILED:\n - " + "\n - ".join(failures))
    print("PAPER_EVIDENCE_GATE_OK")
