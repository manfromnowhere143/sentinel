#!/usr/bin/env python3
"""Render a deterministic, repository-local Sentinel handoff tombstone.

This renderer deliberately has no execution-lifecycle observer.  Until a separately
accepted, source-bound observer exists, it reports observation unavailable and unknown.
It reads repository artifacts, performs no application-level filesystem writes, and writes
rendered bytes only to standard output.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

if __name__ == "__main__":
    sys.dont_write_bytecode = True

if __package__:
    from . import mission_state as mission_contract
else:
    import mission_state as mission_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_STATUS = (
    "OBSERVATION_UNAVAILABLE_SOURCE_BOUND_LIFECYCLE_OBSERVER_NOT_ACCEPTED"
)
STATE_MAX_BYTES = 1024 * 1024
TOMBSTONE_PHASES = frozenset(
    {
        "PREREGISTERED_TOOLING_REQUIRED",
        "CONTROL_HARDENING_REQUIRED",
    }
)


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _exact_json_value(observed: object, expected: object) -> bool:
    """Compare JSON values without bool/int or int/float equivalence."""

    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        observed_dict = observed
        expected_dict = expected
        return set(observed_dict) == set(expected_dict) and all(
            _exact_json_value(observed_dict[key], expected_dict[key])
            for key in expected_dict
        )
    if type(expected) is list:
        observed_list = observed
        expected_list = expected
        return len(observed_list) == len(expected_list) and all(
            _exact_json_value(observed_item, expected_item)
            for observed_item, expected_item in zip(
                observed_list,
                expected_list,
                strict=True,
            )
        )
    return observed == expected


def _node_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Return the stable identity needed to replay a filesystem node."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
    )


def _file_snapshot_identity(
    metadata: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    """Return identity and mutation metadata for a fixed regular-file snapshot."""

    return (
        *_node_identity(metadata),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _no_follow_flag() -> int:
    """Fail closed when the platform cannot provide no-follow descriptor opens."""

    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("platform lacks required no-follow descriptor support")
    return os.O_NOFOLLOW


def load_state() -> dict[str, Any]:
    """Load the fixed state file only while its canonical pathname stays bound."""

    state_path = REPO_ROOT / "MISSION_STATE.json"
    if state_path.is_symlink():
        raise ValueError("MISSION_STATE.json must not be a symlink")
    no_follow = _no_follow_flag()
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | no_follow
    file_flags = os.O_RDONLY | os.O_NONBLOCK | no_follow
    root_descriptor = -1
    descriptor = -1
    replay_root_descriptor = -1
    replay_descriptor = -1
    try:
        root_descriptor = os.open(REPO_ROOT, directory_flags)
        root_before = os.fstat(root_descriptor)
        if not stat.S_ISDIR(root_before.st_mode):
            raise ValueError("repository root must be a directory")
        descriptor = os.open("MISSION_STATE.json", file_flags, dir_fd=root_descriptor)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("MISSION_STATE.json must be a regular file")
        if before.st_size > STATE_MAX_BYTES:
            raise ValueError("MISSION_STATE.json exceeds the size limit")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, min(64 * 1024, STATE_MAX_BYTES + 1))
            if not chunk:
                break
            chunks.append(chunk)
            if sum(len(item) for item in chunks) > STATE_MAX_BYTES:
                raise ValueError("MISSION_STATE.json exceeds the size limit")
        after = os.fstat(descriptor)
        root_after = os.fstat(root_descriptor)

        replay_root_descriptor = os.open(REPO_ROOT, directory_flags)
        replay_root = os.fstat(replay_root_descriptor)
        replay_descriptor = os.open(
            "MISSION_STATE.json",
            file_flags,
            dir_fd=replay_root_descriptor,
        )
        replay_leaf = os.fstat(replay_descriptor)
    finally:
        for open_descriptor in (
            replay_descriptor,
            replay_root_descriptor,
            descriptor,
            root_descriptor,
        ):
            if open_descriptor >= 0:
                os.close(open_descriptor)
    payload = b"".join(chunks)
    if (
        _node_identity(root_before) != _node_identity(root_after)
        or _node_identity(root_before) != _node_identity(replay_root)
        or _file_snapshot_identity(before) != _file_snapshot_identity(after)
        or _file_snapshot_identity(before) != _file_snapshot_identity(replay_leaf)
        or len(payload) != before.st_size
    ):
        raise ValueError("MISSION_STATE.json changed while it was read")
    loaded = json.loads(
        payload,
        object_pairs_hook=_strict_json_object,
        parse_constant=_reject_nonfinite_json,
    )
    if type(loaded) is not dict:
        raise ValueError("MISSION_STATE.json top level must be an object")
    return loaded


def _repository_path_problem(value: Any, *, field: str) -> str | None:
    if not isinstance(value, str) or not value:
        return f"{field}:not-a-nonempty-string"
    relative = Path(value)
    if not relative.parts or relative == Path(".") or relative.is_absolute() or ".." in relative.parts:
        return f"{field}:not-repository-relative"
    initial_descriptors: list[int] = []
    replay_descriptors: list[int] = []
    try:
        no_follow = _no_follow_flag()
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | no_follow
        file_flags = os.O_RDONLY | os.O_NONBLOCK | no_follow

        def open_chain(descriptors: list[int]) -> list[os.stat_result]:
            descriptors.append(os.open(REPO_ROOT, directory_flags))
            metadata = [os.fstat(descriptors[-1])]
            if not stat.S_ISDIR(metadata[-1].st_mode):
                raise ValueError("repository root is not a directory")
            for index, part in enumerate(relative.parts):
                flags = (
                    file_flags
                    if index == len(relative.parts) - 1
                    else directory_flags
                )
                descriptors.append(
                    os.open(part, flags, dir_fd=descriptors[-1])
                )
                metadata.append(os.fstat(descriptors[-1]))
            return metadata

        initial_metadata = open_chain(initial_descriptors)
        replay_metadata = open_chain(replay_descriptors)
        if tuple(map(_node_identity, initial_metadata)) != tuple(
            map(_node_identity, replay_metadata)
        ):
            return f"{field}:changed-during-validation"
        mode = initial_metadata[-1].st_mode
    except (OSError, ValueError):
        return f"{field}:missing"
    finally:
        for descriptor in reversed((*initial_descriptors, *replay_descriptors)):
            os.close(descriptor)
    if not stat.S_ISREG(mode):
        return f"{field}:not-a-file"
    return None


def _repository_local_state_problems(state: Any) -> list[str]:
    """Validate the exact non-performing state contract without external control."""

    if type(state) is not dict:
        return ["top-level:not-an-object"]
    problems: list[str] = []
    if set(state) != mission_contract.EXPECTED_STATE_FIELDS:
        problems.append("top-level:field-set")
    exact_fields: tuple[tuple[str, Any], ...] = (
        ("schema", mission_contract.EXPECTED_SCHEMA),
        ("canonical_repository", mission_contract.CANONICAL_REPOSITORY),
        ("workspace_boundary", mission_contract.EXPECTED_WORKSPACE_BOUNDARY),
        ("trunk", "master"),
        (
            "current_completed_iteration",
            mission_contract.EXPECTED_CURRENT_COMPLETED_ITERATION,
        ),
        ("current_result", mission_contract.EXPECTED_CURRENT_RESULT),
        ("current_verdict", mission_contract.EXPECTED_CURRENT_VERDICT),
        ("run_state", "UNKNOWN"),
        ("active_hypothesis", mission_contract.EXPECTED_ACTIVE_HYPOTHESIS),
        ("claim_state", mission_contract.EXPECTED_CLAIM_STATE),
        (
            "deprecated_pending_hypotheses",
            mission_contract.EXPECTED_DEPRECATED_HYPOTHESES,
        ),
        ("paper_state", mission_contract.EXPECTED_PAPER_STATE),
        ("storage_gate", mission_contract.EXPECTED_STORAGE_GATE),
    )
    for field, expected in exact_fields:
        if not _exact_json_value(state.get(field), expected):
            problems.append(f"{field}:contract")

    next_program = state.get("next_program")
    if type(next_program) is not dict:
        problems.append("next_program:not-an-object")
    else:
        if set(next_program) != mission_contract.EXPECTED_NEXT_PROGRAM_FIELDS:
            problems.append("next_program:field-set")
        phase = next_program.get("phase")
        if type(phase) is not str or phase not in TOMBSTONE_PHASES:
            problems.append("next_program:phase-not-supported-by-tombstone")
        if (
            type(next_program.get("iteration")) is not int
            or next_program.get("iteration")
            != mission_contract.EXPECTED_CURRENT_COMPLETED_ITERATION + 1
        ):
            problems.append("next_program:iteration")
        if not _exact_json_value(
            next_program.get("name"),
            mission_contract.EXPECTED_PROGRAM_NAME,
        ):
            problems.append("next_program:name")
        action_contract = (
            mission_contract.PHASE_ACTION_CONTRACTS.get(phase)
            if type(phase) is str
            else None
        )
        if action_contract is None:
            problems.append("next_program:action-contract")
        else:
            expected_authorized, expected_forbidden = action_contract
            if not _exact_json_value(
                next_program.get("authorized_actions"),
                list(expected_authorized),
            ):
                problems.append("next_program:authorized-actions")
            if not _exact_json_value(
                next_program.get("forbidden_actions"),
                list(expected_forbidden),
            ):
                problems.append("next_program:forbidden-actions")
        expected_run_state = (
            mission_contract.PHASE_RUN_STATES.get(phase)
            if type(phase) is str
            else None
        )
        if expected_run_state != "UNKNOWN" or not _exact_json_value(
            state.get("run_state"),
            expected_run_state,
        ):
            problems.append("run_state:contract")

    for field, value in (
        ("current_result", state.get("current_result")),
        ("active_hypothesis", state.get("active_hypothesis")),
    ):
        path_problem = _repository_path_problem(value, field=field)
        if path_problem:
            problems.append(path_problem)
    deprecated = state.get("deprecated_pending_hypotheses")
    if isinstance(deprecated, list):
        for index, value in enumerate(deprecated):
            path_problem = _repository_path_problem(
                value,
                field=f"deprecated_pending_hypotheses[{index}]",
            )
            if path_problem:
                problems.append(path_problem)
    return sorted(set(problems))


def render_handoff() -> str:
    """Return a deterministic snapshot derived only from repository-local bytes."""

    mission_state = load_state()
    state_problems = _repository_local_state_problems(mission_state)
    if state_problems:
        raise ValueError("MISSION_STATE.json invalid:\n - " + "\n - ".join(state_problems))

    output = io.StringIO()

    def emit(line: str = "") -> None:
        print(line, file=output)

    emit("# HANDOFF — offline repository snapshot")
    emit()
    emit(
        "Mode: deterministic repository-local tombstone from "
        "`scripts/make_handoff.py`. Read `CONTINUITY.md` first."
    )
    emit("Authority: NONE. This output is not execution-lifecycle evidence.")
    emit(
        "Publication: do not replace the retained `HANDOFF.md` without a separately "
        "reviewed repository publication control."
    )
    emit()
    emit("## Repository observation")
    emit()
    emit(f"- Working-tree state: {OBSERVATION_STATUS}")
    emit("- Commit identity: UNKNOWN")
    emit(
        "- This renderer does not execute commands; validate repository identity and "
        "working-tree status through an independently accepted control."
    )
    emit()

    next_program = mission_state["next_program"]
    emit("## Canonical mission state (`MISSION_STATE.json`)")
    emit()
    emit(
        f"- Current: iteration {mission_state['current_completed_iteration']} / "
        f"{mission_state['current_verdict']} / run {mission_state['run_state']} / "
        f"next iteration {next_program['iteration']} {next_program['phase']}"
    )
    emit(f"- Current result: {mission_state['current_result']}")
    emit(f"- Next program: {next_program['name']}")
    emit("- Authorized now:")
    for action in next_program["authorized_actions"]:
        emit(f"  - {action}")
    emit("- Forbidden now:")
    for action in next_program["forbidden_actions"]:
        emit(f"  - {action}")
    emit()

    emit("## Execution lifecycle observation")
    emit()
    emit(f"- Observation status: {OBSERVATION_STATUS}")
    emit("- Lifecycle state: UNKNOWN")
    emit(
        "- No execution, completion, termination, readiness, or relaunch conclusion is "
        "licensed by this snapshot."
    )
    emit()

    emit("## Open threads (from repository-local experiment docs)")
    emit()
    emit(
        f"- Canonical completed experiment: {mission_state['current_result']} — "
        "read it before opening new work."
    )
    active_hypothesis = mission_state.get("active_hypothesis")
    if active_hypothesis:
        emit(
            f"- Active pending pre-registration: {active_hypothesis} — read it with "
            "`MISSION_STATE.json`; neither file overrides the other."
        )
    for legacy_path in mission_state["deprecated_pending_hypotheses"]:
        emit(
            f"- Deprecated pending pre-registration: {legacy_path} — "
            "historical only; it does not govern the next action."
        )
    emit(
        f"- Canonical next action: iteration {next_program['iteration']} / "
        f"{next_program['phase']} / {next_program['name']}."
    )
    emit(
        "- Lifecycle correction: the frozen current-status prose in `README.md` and "
        "`docs/NEXT_PHASE.md` that says no run is in flight is retracted as execution "
        "evidence; lifecycle state remains `UNKNOWN`."
    )
    emit("- docs/NEXT_PHASE.md: check its status ledger and decision rules.")
    emit("- docs/paper/MANUSCRIPT.md: check its status ledger and decision rules.")
    emit()

    emit("## Verification before you act")
    emit()
    emit("- Run: `ruff check . && pytest -q && python3 scripts/validate_docs.py`")
    emit("- All three must pass before and after changes; CI enforces the same on push.")

    return output.getvalue()


def main() -> int:
    try:
        rendered = render_handoff()
    except (OSError, ValueError) as exc:
        print(f"HANDOFF_RENDER_BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
