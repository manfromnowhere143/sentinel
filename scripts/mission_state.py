#!/usr/bin/env python3
"""Load and validate Sentinel's single canonical current-state contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "MISSION_STATE.json"
EXPECTED_SCHEMA = "sentinel.mission_state.v1"


def load_state(path: Path = STATE_PATH) -> dict:
    return json.loads(path.read_text())


def validate_state(state: dict, repo: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    if state.get("schema") != EXPECTED_SCHEMA:
        problems.append(f"schema:{state.get('schema')!r}!={EXPECTED_SCHEMA!r}")

    completed = state.get("current_completed_iteration")
    if not isinstance(completed, int) or completed < 1:
        problems.append(f"current_completed_iteration:{completed!r}")

    result = state.get("current_result")
    result_path = repo / result if isinstance(result, str) else None
    if result_path is None or not result_path.is_file():
        problems.append(f"current_result_missing:{result!r}")
    else:
        result_text = result_path.read_text(errors="replace")
        verdict = state.get("current_verdict")
        if not verdict or verdict not in result_text:
            problems.append(f"current_verdict_not_in_result:{verdict!r}")

    completed_results: dict[int, Path] = {}
    for candidate in repo.glob("experiments/iter*/RESULT.md"):
        match = re.match(r"iter(\d+)(?:_|$)", candidate.parent.name)
        if match:
            completed_results[int(match.group(1))] = candidate
    discovered_completed = max(completed_results, default=0)
    if completed != discovered_completed:
        problems.append(f"current_completed_iteration:{completed!r}!={discovered_completed}")
    elif result_path is not None and result_path != completed_results.get(discovered_completed):
        problems.append(
            f"current_result:{result!r}!={completed_results[discovered_completed].relative_to(repo)}"
        )

    next_program = state.get("next_program") or {}
    next_iteration = next_program.get("iteration")
    if isinstance(completed, int) and next_iteration != completed + 1:
        problems.append(f"next_iteration:{next_iteration!r}!={completed + 1}")
    if next_program.get("phase") not in {
        "PREREGISTRATION_REQUIRED",
        "PREREGISTERED_TOOLING_REQUIRED",
        "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
        "LAUNCH_AUTHORIZED",
        "RUNNING",
        "ANALYSIS_REQUIRED",
    }:
        problems.append(f"next_phase:{next_program.get('phase')!r}")

    if state.get("run_state") not in {"IDLE", "RUNNING", "UNKNOWN"}:
        problems.append(f"run_state:{state.get('run_state')!r}")

    deprecated = set(state.get("deprecated_pending_hypotheses", []))
    for hypothesis in deprecated:
        if not (repo / hypothesis).is_file():
            problems.append(f"deprecated_pending_hypothesis_missing:{hypothesis}")

    active_hypothesis = state.get("active_hypothesis")
    classified = set(deprecated)
    if active_hypothesis is not None:
        if not isinstance(active_hypothesis, str) or not (repo / active_hypothesis).is_file():
            problems.append(f"active_hypothesis_missing:{active_hypothesis!r}")
        else:
            classified.add(active_hypothesis)
    pending = {
        str(path.relative_to(repo))
        for path in repo.glob("experiments/iter*/HYPOTHESIS.md")
        if not path.with_name("RESULT.md").is_file()
    }
    if pending != classified:
        problems.append(
            "pending_hypothesis_classification:"
            f"unclassified={sorted(pending - classified)}:nonpending={sorted(classified - pending)}"
        )

    storage = state.get("storage_gate") or {}
    for key in (
        "minimum_local_free_gib_before_new_proof_collection",
        "minimum_remote_root_free_gib_before_gpu_launch",
    ):
        value = storage.get(key)
        if not isinstance(value, (int, float)) or value <= 0:
            problems.append(f"storage_gate:{key}:{value!r}")

    return problems


def current_summary(state: dict) -> str:
    next_program = state["next_program"]
    return (
        f"iteration {state['current_completed_iteration']} / {state['current_verdict']} / "
        f"run {state['run_state']} / next iteration {next_program['iteration']} "
        f"{next_program['phase']}"
    )


if __name__ == "__main__":
    loaded = load_state()
    failures = validate_state(loaded)
    if failures:
        raise SystemExit("MISSION STATE INVALID:\n - " + "\n - ".join(failures))
    print(f"MISSION_STATE_OK {current_summary(loaded)}")
