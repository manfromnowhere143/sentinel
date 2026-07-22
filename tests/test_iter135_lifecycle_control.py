from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter135_neuroncap_blind_braking_dose_response"
    / "validate_lifecycle135.py"
)
SPEC = importlib.util.spec_from_file_location("iter135_lifecycle_control", MODULE_PATH)
assert SPEC is not None
lifecycle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(lifecycle)

CONTROL_COMMIT = "c" * 40
SOURCE_COMMIT = "a" * 40
MISSION_STATE_SHA256 = "b" * 64
HOST_IDENTITY_SHA256 = hashlib.sha256(b"sentinel-gpu-instance-identity").hexdigest()
BOOT_ID = "123e4567-e89b-42d3-a456-426614174000"
LEASE_ID = "123e4567-e89b-42d3-b456-426614174001"
CHALLENGE_SHA256 = hashlib.sha256(b"controller-issued-one-shot-challenge").hexdigest()
ATTEMPT_ID = "i135-attempt-0001"
MANIFEST_SHA256 = hashlib.sha256(b"manifest").hexdigest()
EXECUTABLE_SHA256 = hashlib.sha256(b"observer-executable").hexdigest()
BUILD_SHA256 = hashlib.sha256(b"observer-build").hexdigest()
CGROUP_POLICY_SHA256 = hashlib.sha256(b"observer-cgroup-policy").hexdigest()
TRUSTED_CURRENT_MONOTONIC_NS = 2_100_000_000
EXPECTED_DEADLINE_MONOTONIC_NS = 3_000_000_000


def digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def noncanonical_pad_bits(encoded: str) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    padding = len(encoded) - len(encoded.rstrip("="))
    assert padding in {1, 2}
    index = len(encoded) - padding - 1
    value = alphabet.index(encoded[index])
    unused_values = 4 if padding == 1 else 16
    assert value % unused_values == 0
    return encoded[:index] + alphabet[value + 1] + encoded[index + 1 :]


def identity() -> dict[str, object]:
    return {
        "host_identity_sha256": HOST_IDENTITY_SHA256,
        "boot_id": BOOT_ID,
        "pid": 731,
        "process_start_ticks": 99_421,
        "executable_sha256": EXECUTABLE_SHA256,
        "build_sha256": BUILD_SHA256,
        "cgroup_policy_sha256": CGROUP_POLICY_SHA256,
    }


def lease_snapshot() -> dict[str, object]:
    return {
        "device": 17,
        "inode": 1935,
        "mount_id": 44,
        "mode": stat.S_IFREG | 0o600,
        "uid": 0,
        "gid": 0,
        "link_count": 1,
        "size": 0,
        "mtime_ns": 1_000_000,
        "ctime_ns": 1_000_000,
    }


def state_fields(state: str) -> dict[str, object]:
    if state == "GENESIS":
        return {
            "attempt_id": None,
            "manifest_sha256": None,
            "terminal_cause": None,
            "proof_manifest_sha256": None,
        }
    if state == "ACTIVE":
        return {
            "attempt_id": ATTEMPT_ID,
            "manifest_sha256": MANIFEST_SHA256,
            "terminal_cause": None,
            "proof_manifest_sha256": None,
        }
    if state in {"TERMINATED_COMPLETE", "TERMINATED_PARTIAL"}:
        return {
            "attempt_id": ATTEMPT_ID,
            "manifest_sha256": MANIFEST_SHA256,
            "terminal_cause": terminal_cause(state),
            "proof_manifest_sha256": hashlib.sha256(proof_manifest_bytes(state)).hexdigest(),
        }
    raise AssertionError(f"unsupported state: {state}")


def terminal_cause(state: str) -> str:
    return "EXIT_ZERO" if state == "TERMINATED_COMPLETE" else "EXIT_NONZERO"


def proof_manifest_bytes(state: str) -> bytes:
    manifest = {
        "schema": lifecycle.PROOF_MANIFEST_SCHEMA,
        "attempt_id": ATTEMPT_ID,
        "manifest_sha256": MANIFEST_SHA256,
        "terminal_state": state,
        "terminal_cause": terminal_cause(state),
        "artifact_count": 3 if state == "TERMINATED_COMPLETE" else 1,
    }
    return lifecycle._canonical_json(manifest) + b"\n"


def global_container_record(
    container_id: str,
    *,
    iteration_label: str | None,
    attempt_label: str | None,
    manifest_label: str | None,
) -> dict[str, object]:
    return {
        "attempt_label": attempt_label,
        "container_id": container_id,
        "iteration_label": iteration_label,
        "manifest_label": manifest_label,
        "runtime_state": "RUNNING",
    }


def global_record_for_mission(record: dict[str, object]) -> dict[str, object]:
    return global_container_record(
        str(record["container_id"]),
        iteration_label=str(lifecycle.ITERATION),
        attempt_label=str(record["attempt_id"]),
        manifest_label=str(record["manifest_sha256"]),
    )


def records_for(source: str, state: str) -> list[dict[str, object]]:
    if state == "GENESIS":
        return []
    if state == "ACTIVE":
        common = {"attempt_id": ATTEMPT_ID, "manifest_sha256": MANIFEST_SHA256}
        if source in {"launch_lock", "analytic_lock"}:
            return [{**common, "owner_pid": 913, "owner_process_start_ticks": 44_201}]
        if source == "launcher_process":
            return [
                {
                    **common,
                    "pid": 913,
                    "process_start_ticks": 44_201,
                    "executable_sha256": digest("launcher-executable"),
                }
            ]
        if source == "mission_containers":
            return [
                {
                    **common,
                    "container_id": "i135-mission-containers-container",
                    "runtime_state": "RUNNING",
                }
            ]
        if source == "global_containers":
            return [global_record_for_mission(records_for("mission_containers", state)[0])]
        if source == "attempt_journal":
            return [
                {
                    **common,
                    "journal_state": "ACTIVE",
                    "terminal_cause": None,
                    "proof_manifest_sha256": None,
                }
            ]
        if source == "provider_job_registry":
            return [
                {
                    **common,
                    "job_id": "provider-job-i135",
                    "provider_state": "RUNNING",
                    "terminal_cause": None,
                    "proof_manifest_sha256": None,
                }
            ]
        return []
    if state not in {"TERMINATED_COMPLETE", "TERMINATED_PARTIAL"}:
        raise AssertionError(f"unsupported state: {state}")
    if source not in {
        "attempt_journal",
        "terminal_witness",
        "proof_manifest",
        "provider_job_registry",
    }:
        return []
    cause = terminal_cause(state)
    proof_raw = proof_manifest_bytes(state)
    proof_sha256 = hashlib.sha256(proof_raw).hexdigest()
    common = {"attempt_id": ATTEMPT_ID, "manifest_sha256": MANIFEST_SHA256}
    if source == "attempt_journal":
        return [
            {
                **common,
                "journal_state": state,
                "terminal_cause": cause,
                "proof_manifest_sha256": proof_sha256,
            }
        ]
    if source == "terminal_witness":
        return [
            {
                **common,
                "terminal_state": state,
                "terminal_cause": cause,
                "proof_manifest_sha256": proof_sha256,
            }
        ]
    if source == "proof_manifest":
        return [
            {
                **common,
                "proof_manifest_base64": base64.b64encode(proof_raw).decode(),
                "proof_manifest_bytes": len(proof_raw),
                "proof_manifest_sha256": proof_sha256,
            }
        ]
    return [
        {
            **common,
            "job_id": "provider-job-i135",
            "provider_state": "SUCCEEDED" if state == "TERMINATED_COMPLETE" else "FAILED",
            "terminal_cause": cause,
            "proof_manifest_sha256": proof_sha256,
        }
    ]


def observation_bytes(source: str, state: str, observed_ns: int) -> bytes:
    records = sorted(
        records_for(source, state),
        key=lifecycle._canonical_json,
    )
    observation = {
        "schema": lifecycle.SOURCE_SCHEMA,
        "source": source,
        "query_sha256": lifecycle.QUERY_SHA256[source],
        "challenge_nonce_sha256": CHALLENGE_SHA256,
        "host_identity_sha256": HOST_IDENTITY_SHA256,
        "boot_id": BOOT_ID,
        "observed_monotonic_ns": observed_ns,
        "enumeration": {
            "scope": lifecycle.ENUMERATION_SCOPES[source],
            "filter": lifecycle.ENUMERATION_FILTERS[source],
            "sort": lifecycle.ENUMERATION_SORT,
            "page_count": 1,
            "record_count": len(records),
            "complete": True,
            "continuation_token": None,
        },
        "records": records,
    }
    return lifecycle._canonical_json(observation) + b"\n"


def capture(
    source: str,
    state: str,
    position: str,
    source_index: int,
    *,
    return_code: int = 0,
    timed_out: bool = False,
    truncated: bool = False,
) -> dict[str, object]:
    base = 1_100_000_000 if position == "initial" else 1_800_000_000
    started_ns = base + source_index * 1_000_000
    finished_ns = started_ns + 100_000
    stdout = observation_bytes(
        source,
        state,
        started_ns + 50_000,
    )
    stderr = b""
    return {
        "query_sha256": lifecycle.QUERY_SHA256[source],
        "started_monotonic_ns": started_ns,
        "finished_monotonic_ns": finished_ns,
        "return_code": return_code,
        "timed_out": timed_out,
        "truncated": truncated,
        "stdout_base64": base64.b64encode(stdout).decode(),
        "stdout_bytes": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_base64": base64.b64encode(stderr).decode(),
        "stderr_bytes": len(stderr),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


def claimed_verdict(state: str) -> str:
    return {
        "GENESIS": "QUIESCENCE_EVIDENCE_COMPLETE",
        "ACTIVE": "RUNNING",
        "TERMINATED_COMPLETE": "TERMINATED_COMPLETE",
        "TERMINATED_PARTIAL": "TERMINATED_PARTIAL",
    }[state]


def receipt_for(state: str = "GENESIS") -> dict[str, object]:
    attempt = state_fields(state)["attempt_id"]
    manifest = state_fields(state)["manifest_sha256"]
    sources: dict[str, object] = {}
    for index, source in enumerate(lifecycle.SOURCE_NAMES):
        sources[source] = {
            position: capture(
                source,
                state,
                position,
                index,
            )
            for position in ("initial", "terminal")
        }
    receipt: dict[str, object] = {
        "schema": lifecycle.SCHEMA,
        "mission": {
            "iteration": 135,
            "experiment": lifecycle.EXPERIMENT,
            "source_commit": SOURCE_COMMIT,
            "mission_state_sha256": MISSION_STATE_SHA256,
            "manifest_sha256": manifest,
            "attempt_id": attempt,
        },
        "observer": {
            "control_source_commit": CONTROL_COMMIT,
            "host": lifecycle.EXPECTED_HOST,
            "query_policy_sha256": lifecycle.QUERY_POLICY_SHA256,
            "challenge_nonce_sha256": CHALLENGE_SHA256,
            "started_at_utc": "2026-07-21T09:00:00.000000Z",
            "finished_at_utc": "2026-07-21T09:00:01.000000Z",
            "deadline_at_utc": "2026-07-21T09:00:02.000000Z",
            "started_monotonic_ns": 1_000_000_000,
            "finished_monotonic_ns": 2_000_000_000,
            "deadline_monotonic_ns": 3_000_000_000,
            "initial_identity": identity(),
            "terminal_identity": identity(),
        },
        "lease": {
            "id": LEASE_ID,
            "path": lifecycle.LEASE_PATH,
            "owner_identity": identity(),
            "acquired_at_utc": "2026-07-21T08:59:59.000000Z",
            "initial_snapshot": lease_snapshot(),
            "terminal_snapshot": lease_snapshot(),
        },
        "sources": sources,
        "verdict": claimed_verdict(state),
        "quiescence_evidence_complete": state == "GENESIS",
        "launch_authorized": False,
        "relaunch_authorized": False,
        "problems": [],
        "problem_count": 0,
        "receipt_payload_self_checksum_sha256": "",
    }
    return seal(receipt)


def seal(receipt: dict[str, object]) -> dict[str, object]:
    receipt["receipt_payload_self_checksum_sha256"] = lifecycle._payload_self_checksum(receipt)
    return receipt


def raw_receipt(receipt: dict[str, object]) -> bytes:
    return lifecycle._canonical_json(receipt) + b"\n"


def validate(
    receipt: dict[str, object],
    *,
    expected_raw: bytes | None = None,
    expected_host_identity_sha256: str = HOST_IDENTITY_SHA256,
    detached_overrides: dict[str, object] | None = None,
) -> lifecycle.ValidationResult:
    raw = raw_receipt(receipt)
    detached_raw = raw if expected_raw is None else expected_raw
    detached: dict[str, object] = {
        "expected_receipt_sha256": hashlib.sha256(detached_raw).hexdigest(),
        "expected_control_source_commit": CONTROL_COMMIT,
        "expected_source_commit": SOURCE_COMMIT,
        "expected_mission_state_sha256": MISSION_STATE_SHA256,
        "expected_host_identity_sha256": expected_host_identity_sha256,
        "expected_challenge_nonce_sha256": CHALLENGE_SHA256,
        "expected_boot_id": BOOT_ID,
        "expected_observer_executable_sha256": EXECUTABLE_SHA256,
        "expected_observer_build_sha256": BUILD_SHA256,
        "expected_cgroup_policy_sha256": CGROUP_POLICY_SHA256,
        "expected_lease_id": LEASE_ID,
        "trusted_current_monotonic_ns": TRUSTED_CURRENT_MONOTONIC_NS,
        "expected_deadline_monotonic_ns": EXPECTED_DEADLINE_MONOTONIC_NS,
    }
    if detached_overrides:
        detached.update(detached_overrides)
    return lifecycle.parse_validate_reduce(raw, **detached)


@pytest.mark.parametrize(
    ("state", "verdict", "quiescence"),
    [
        ("GENESIS", "QUIESCENCE_EVIDENCE_COMPLETE", True),
        ("ACTIVE", "RUNNING", False),
        ("TERMINATED_COMPLETE", "TERMINATED_COMPLETE", False),
        ("TERMINATED_PARTIAL", "TERMINATED_PARTIAL", False),
    ],
)
def test_lifecycle_variants_are_derived_from_raw_capture_bytes(
    state: str, verdict: str, quiescence: bool
) -> None:
    result = validate(receipt_for(state))

    assert result.problems == ()
    assert result.verdict == verdict
    assert result.quiescence_evidence_complete is quiescence


def test_receipt_serializes_evidence_not_permission() -> None:
    receipt = receipt_for()
    result = validate(receipt)

    assert "host_boundary_permitted" not in receipt
    assert not hasattr(lifecycle, "admit_host_boundary")
    assert result.quiescence_evidence_complete is True
    assert receipt["launch_authorized"] is False
    assert receipt["relaunch_authorized"] is False


def test_same_evidence_can_be_replayed_but_never_consumes_host_authority() -> None:
    receipt = receipt_for()

    first = validate(receipt)
    second = validate(receipt)

    assert first == second
    assert first.quiescence_evidence_complete is True
    assert "permission" not in lifecycle.ValidationResult._fields


def test_missing_provider_observation_keeps_verdict_unknown() -> None:
    receipt = receipt_for()
    capture_row = receipt["sources"]["provider_job_registry"]["terminal"]
    capture_row["return_code"] = 124
    capture_row["timed_out"] = True
    receipt["verdict"] = "UNKNOWN"
    receipt["quiescence_evidence_complete"] = False
    seal(receipt)

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "UNKNOWN"


def test_empty_container_rows_cannot_hide_active_launcher_evidence() -> None:
    receipt = receipt_for("ACTIVE")
    for source in ("mission_containers", "global_containers"):
        for position in ("initial", "terminal"):
            capture_row = receipt["sources"][source][position]
            observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
            observation["records"] = []
            observation["enumeration"]["record_count"] = 0
            replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)

    assert validate(receipt).verdict == "RUNNING"


def replace_stdout(capture_row: dict[str, object], stdout: bytes) -> None:
    capture_row["stdout_base64"] = base64.b64encode(stdout).decode()
    capture_row["stdout_bytes"] = len(stdout)
    capture_row["stdout_sha256"] = hashlib.sha256(stdout).hexdigest()


def mutate_observation(
    receipt: dict[str, object],
    source: str,
    position: str,
    field: str,
    value: object,
) -> None:
    capture_row = receipt["sources"][source][position]
    observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
    observation[field] = value
    replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)


def mutate_record(
    receipt: dict[str, object],
    source: str,
    position: str,
    field: str,
    value: object,
) -> None:
    capture_row = receipt["sources"][source][position]
    observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
    observation["records"][0][field] = value
    replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)


def replace_records(
    receipt: dict[str, object],
    source: str,
    position: str,
    records: list[dict[str, object]],
    *,
    canonical_sort: bool = True,
) -> None:
    capture_row = receipt["sources"][source][position]
    observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
    observation["records"] = (
        sorted(records, key=lifecycle._canonical_json) if canonical_sort else records
    )
    observation["enumeration"]["record_count"] = len(records)
    replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)


def mutate_enumeration(
    receipt: dict[str, object],
    source: str,
    position: str,
    field: str,
    value: object,
) -> None:
    capture_row = receipt["sources"][source][position]
    observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
    observation["enumeration"][field] = value
    replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)


def set_claimed_verdict(receipt: dict[str, object], verdict: str) -> None:
    receipt["verdict"] = verdict
    receipt["quiescence_evidence_complete"] = verdict == "QUIESCENCE_EVIDENCE_COMPLETE"
    seal(receipt)


GLOBAL_OCCUPANT_CASES = (
    (
        "foreign",
        global_container_record(
            "foreign-service-container",
            iteration_label="foreign-service",
            attempt_label="foreign-job-7",
            manifest_label="foreign-manifest",
        ),
    ),
    (
        "unlabelled",
        global_container_record(
            "unlabelled-container",
            iteration_label=None,
            attempt_label=None,
            manifest_label=None,
        ),
    ),
    (
        "differently-labelled",
        global_container_record(
            "i134-container",
            iteration_label="134",
            attempt_label="i134-attempt-0001",
            manifest_label=digest("iter134-manifest"),
        ),
    ),
)


def test_global_container_contract_is_unfiltered_and_mission_agnostic() -> None:
    contract = json.loads(lifecycle.QUERY_CONTRACTS["global_containers"])

    assert lifecycle.SCHEMA.endswith(".v3")
    assert lifecycle.SOURCE_SCHEMA.endswith(".v3")
    assert lifecycle.ENUMERATION_SCOPES["global_containers"] == (
        "complete-host-runtime-container-registry"
    )
    assert lifecycle.ENUMERATION_FILTERS["global_containers"] == "none"
    assert contract["enumeration_filter"] == "none"
    assert set(lifecycle.RECORD_FIELDS["global_containers"]) == {
        "attempt_label",
        "container_id",
        "iteration_label",
        "manifest_label",
        "runtime_state",
    }


@pytest.mark.parametrize(
    "state", ["GENESIS", "ACTIVE", "TERMINATED_COMPLETE", "TERMINATED_PARTIAL"]
)
@pytest.mark.parametrize(("occupant_kind", "occupant"), GLOBAL_OCCUPANT_CASES)
def test_stable_foreign_global_occupancy_blocks_every_lifecycle_classification(
    state: str,
    occupant_kind: str,
    occupant: dict[str, object],
) -> None:
    receipt = receipt_for(state)
    for position in ("initial", "terminal"):
        records = records_for("global_containers", state) + [copy.deepcopy(occupant)]
        replace_records(receipt, "global_containers", position, records)
    set_claimed_verdict(receipt, "HOST_OCCUPIED")

    result = validate(receipt)

    assert occupant_kind in {"foreign", "unlabelled", "differently-labelled"}
    assert result.problems == ()
    assert result.verdict == "HOST_OCCUPIED"
    assert result.quiescence_evidence_complete is False


def test_foreign_occupancy_does_not_mask_mission_binding_inconsistency() -> None:
    receipt = receipt_for("ACTIVE")
    for position in ("initial", "terminal"):
        mutate_record(
            receipt,
            "attempt_journal",
            position,
            "attempt_id",
            "i135-attempt-0002",
        )
        records = records_for("global_containers", "ACTIVE") + [
            copy.deepcopy(GLOBAL_OCCUPANT_CASES[1][1])
        ]
        replace_records(receipt, "global_containers", position, records)
    set_claimed_verdict(receipt, "INCONSISTENT")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"


@pytest.mark.parametrize(
    "state", ["GENESIS", "ACTIVE", "TERMINATED_COMPLETE", "TERMINATED_PARTIAL"]
)
@pytest.mark.parametrize("churn", ["appears", "disappears", "identity-replaced"])
def test_global_container_churn_forces_unknown(state: str, churn: str) -> None:
    receipt = receipt_for(state)
    first = global_container_record(
        "foreign-container-a",
        iteration_label=None,
        attempt_label=None,
        manifest_label=None,
    )
    second = {**first, "container_id": "foreign-container-b"}
    initial_records = records_for("global_containers", state)
    terminal_records = records_for("global_containers", state)
    if churn == "appears":
        terminal_records.append(first)
    elif churn == "disappears":
        initial_records.append(first)
    else:
        initial_records.append(first)
        terminal_records.append(second)
    replace_records(receipt, "global_containers", "initial", initial_records)
    replace_records(receipt, "global_containers", "terminal", terminal_records)
    set_claimed_verdict(receipt, "UNKNOWN")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_quiescence_requires_both_unfiltered_global_rounds_to_be_empty() -> None:
    receipt = receipt_for()
    for position in ("initial", "terminal"):
        raw = base64.b64decode(receipt["sources"]["global_containers"][position]["stdout_base64"])
        observation = json.loads(raw)
        assert observation["enumeration"]["filter"] == "none"
        assert observation["records"] == []

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "QUIESCENCE_EVIDENCE_COMPLETE"
    assert result.quiescence_evidence_complete is True


@pytest.mark.parametrize(
    "fault",
    [
        "mission-row-absent-globally",
        "global-i135-row-absent-from-mission-view",
        "global-i135-binding-mismatch",
        "mission-row-absent-in-one-round",
    ],
)
def test_mission_and_global_container_views_must_be_exactly_consistent(fault: str) -> None:
    state = "GENESIS" if fault == "global-i135-row-absent-from-mission-view" else "ACTIVE"
    receipt = receipt_for(state)
    if fault == "mission-row-absent-globally":
        for position in ("initial", "terminal"):
            replace_records(receipt, "global_containers", position, [])
    elif fault == "global-i135-row-absent-from-mission-view":
        unexpected = global_container_record(
            "unreported-i135-container",
            iteration_label="135",
            attempt_label=ATTEMPT_ID,
            manifest_label=MANIFEST_SHA256,
        )
        for position in ("initial", "terminal"):
            replace_records(receipt, "global_containers", position, [unexpected])
    elif fault == "global-i135-binding-mismatch":
        mismatched = records_for("global_containers", "ACTIVE")[0]
        mismatched["attempt_label"] = "i135-attempt-0002"
        for position in ("initial", "terminal"):
            replace_records(receipt, "global_containers", position, [mismatched])
    else:
        replace_records(receipt, "global_containers", "terminal", [])
    set_claimed_verdict(receipt, "UNKNOWN")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_stable_global_row_with_terminal_empty_mission_projection_is_unknown() -> None:
    receipt = receipt_for("ACTIVE")
    replace_records(receipt, "mission_containers", "terminal", [])
    set_claimed_verdict(receipt, "UNKNOWN")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False
    assert receipt["launch_authorized"] is False
    assert receipt["relaunch_authorized"] is False


@pytest.mark.parametrize("state", ["TERMINATED_COMPLETE", "TERMINATED_PARTIAL"])
def test_terminal_evidence_cannot_hide_a_running_i135_global_container(state: str) -> None:
    receipt = receipt_for(state)
    unexpected = global_container_record(
        "still-running-i135-container",
        iteration_label="135",
        attempt_label=ATTEMPT_ID,
        manifest_label=MANIFEST_SHA256,
    )
    for position in ("initial", "terminal"):
        replace_records(receipt, "global_containers", position, [unexpected])
    set_claimed_verdict(receipt, "UNKNOWN")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


@pytest.mark.parametrize(
    ("field", "value", "problem"),
    [
        ("iteration_label", True, "iteration-label"),
        ("attempt_label", "line\nbreak", "attempt-label"),
        ("manifest_label", "x" * 257, "manifest-label"),
    ],
)
def test_global_container_label_projection_is_exact_and_bounded(
    field: str,
    value: object,
    problem: str,
) -> None:
    receipt = receipt_for()
    record = global_container_record(
        "foreign-container",
        iteration_label=None,
        attempt_label=None,
        manifest_label=None,
    )
    record[field] = value
    for position in ("initial", "terminal"):
        replace_records(receipt, "global_containers", position, [record])
    set_claimed_verdict(receipt, "UNKNOWN")

    result = validate(receipt)

    assert any(problem in item for item in result.problems)
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_producer_supplied_registry_state_assertion_is_rejected() -> None:
    receipt = receipt_for()
    mutate_observation(receipt, "attempt_journal", "terminal", "registry_state", "GENESIS")

    result = validate(receipt)

    assert any("field-set" in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"


@pytest.mark.parametrize("field", ["attempt_id", "manifest_sha256", "proof_manifest_sha256"])
def test_terminal_evidence_requires_cross_bound_identifiers(field: str) -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    mutate_record(receipt, "terminal_witness", "terminal", field, None)

    result = validate(receipt)

    assert any(field.replace("_", "-") in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"


def test_terminal_cross_binding_mismatch_is_inconsistent() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    for position in ("initial", "terminal"):
        capture_row = receipt["sources"]["proof_manifest"][position]
        observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
        record = observation["records"][0]
        proof = json.loads(base64.b64decode(record["proof_manifest_base64"]))
        proof["artifact_count"] = 4
        proof_raw = lifecycle._canonical_json(proof) + b"\n"
        record["proof_manifest_base64"] = base64.b64encode(proof_raw).decode()
        record["proof_manifest_bytes"] = len(proof_raw)
        record["proof_manifest_sha256"] = hashlib.sha256(proof_raw).hexdigest()
        replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    receipt["verdict"] = "INCONSISTENT"
    seal(receipt)

    assert validate(receipt).verdict == "INCONSISTENT"


def test_active_and_terminal_sources_are_inconsistent() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    for position in ("initial", "terminal"):
        capture_row = capture(
            "launcher_process",
            "ACTIVE",
            position,
            lifecycle.SOURCE_NAMES.index("launcher_process"),
        )
        receipt["sources"]["launcher_process"][position] = capture_row
    receipt["verdict"] = "INCONSISTENT"
    seal(receipt)

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"


def test_foreign_occupancy_precedes_active_and_terminal_conflict() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    foreign_occupant = copy.deepcopy(GLOBAL_OCCUPANT_CASES[1][1])
    for position in ("initial", "terminal"):
        receipt["sources"]["launcher_process"][position] = capture(
            "launcher_process",
            "ACTIVE",
            position,
            lifecycle.SOURCE_NAMES.index("launcher_process"),
        )
        replace_records(receipt, "global_containers", position, [foreign_occupant])
    set_claimed_verdict(receipt, "HOST_OCCUPIED")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "HOST_OCCUPIED"
    assert result.quiescence_evidence_complete is False


def test_foreign_occupancy_does_not_mask_active_terminal_binding_drift() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    foreign_occupant = copy.deepcopy(GLOBAL_OCCUPANT_CASES[1][1])
    for position in ("initial", "terminal"):
        receipt["sources"]["launcher_process"][position] = capture(
            "launcher_process",
            "ACTIVE",
            position,
            lifecycle.SOURCE_NAMES.index("launcher_process"),
        )
        mutate_record(
            receipt,
            "launcher_process",
            position,
            "attempt_id",
            "i135-attempt-0002",
        )
        replace_records(receipt, "global_containers", position, [foreign_occupant])
    set_claimed_verdict(receipt, "INCONSISTENT")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"
    assert result.quiescence_evidence_complete is False


def test_foreign_occupancy_precedes_incomplete_terminal_evidence() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    foreign_occupant = copy.deepcopy(GLOBAL_OCCUPANT_CASES[1][1])
    for position in ("initial", "terminal"):
        replace_records(receipt, "proof_manifest", position, [])
        replace_records(receipt, "global_containers", position, [foreign_occupant])
    set_claimed_verdict(receipt, "HOST_OCCUPIED")

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "HOST_OCCUPIED"
    assert result.quiescence_evidence_complete is False


@pytest.mark.parametrize(
    ("field", "value", "problem_fragment"),
    [
        ("mode", stat.S_IFREG | 0o666, "snapshot:mode"),
        ("uid", 501, "snapshot:ownership"),
        ("gid", 20, "snapshot:ownership"),
        ("link_count", 2, "snapshot:link-count"),
    ],
)
def test_lease_permissions_ownership_and_link_count_are_exact(
    field: str, value: int, problem_fragment: str
) -> None:
    receipt = receipt_for()
    receipt["lease"]["initial_snapshot"][field] = value
    receipt["lease"]["terminal_snapshot"][field] = value
    seal(receipt)

    result = validate(receipt)

    assert any(problem_fragment in problem for problem in result.problems)


def test_boolean_link_count_alias_fails_closed() -> None:
    receipt = receipt_for()
    receipt["lease"]["initial_snapshot"]["link_count"] = True
    receipt["lease"]["terminal_snapshot"]["link_count"] = True
    seal(receipt)

    result = validate(receipt)

    assert any("snapshot:link-count" in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"


@pytest.mark.parametrize("source", ["launch_lock", "analytic_lock"])
def test_canonical_lock_sources_reject_multiple_owner_rows(source: str) -> None:
    receipt = receipt_for("ACTIVE")
    records = records_for(source, "ACTIVE")
    second = copy.deepcopy(records[0])
    second["owner_pid"] += 1
    second["owner_process_start_ticks"] += 1
    for position in ("initial", "terminal"):
        replace_records(receipt, source, position, [records[0], second])
    seal(receipt)

    result = validate(receipt)

    assert any("records-cardinality" in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"


def test_lease_snapshot_swap_is_rejected() -> None:
    receipt = receipt_for()
    receipt["lease"]["terminal_snapshot"]["inode"] += 1
    seal(receipt)

    assert "lease:snapshot-drift" in validate(receipt).problems


def test_structural_fault_cannot_retain_positive_quiescence() -> None:
    receipt = receipt_for()
    receipt["lease"]["initial_snapshot"]["mode"] = stat.S_IFREG | 0o666
    receipt["lease"]["terminal_snapshot"]["mode"] = stat.S_IFREG | 0o666
    seal(receipt)

    result = validate(receipt)

    assert result.problems
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


@pytest.mark.parametrize("field", ["exclusive_ofd_lock", "opened_nofollow"])
def test_serialized_live_lease_capability_claims_are_not_in_schema(field: str) -> None:
    receipt = receipt_for()
    receipt["lease"][field] = True
    seal(receipt)

    result = validate(receipt)

    assert "lease:field-set" in result.problems
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_observer_identity_drift_is_rejected() -> None:
    receipt = receipt_for()
    receipt["observer"]["terminal_identity"]["process_start_ticks"] += 1
    seal(receipt)

    assert "observer:identity-drift" in validate(receipt).problems


def test_resealed_arbitrary_host_identity_fails_detached_binding() -> None:
    receipt = receipt_for()
    hostile_identity = "f" * 64
    for identity_row in (
        receipt["observer"]["initial_identity"],
        receipt["observer"]["terminal_identity"],
        receipt["lease"]["owner_identity"],
    ):
        identity_row["host_identity_sha256"] = hostile_identity
    for source in lifecycle.SOURCE_NAMES:
        for position in ("initial", "terminal"):
            mutate_observation(
                receipt,
                source,
                position,
                "host_identity_sha256",
                hostile_identity,
            )
    seal(receipt)

    assert "binding:host-identity-sha256" in validate(receipt).problems


def test_query_policy_and_each_query_hash_are_frozen() -> None:
    receipt = receipt_for()
    receipt["observer"]["query_policy_sha256"] = "f" * 64
    receipt["sources"]["launch_lock"]["initial"]["query_sha256"] = "e" * 64
    seal(receipt)

    problems = validate(receipt).problems

    assert "observer:query-policy-sha256" in problems
    assert "sources:launch_lock:initial:query-sha256" in problems


def test_copying_one_source_capture_to_another_is_rejected() -> None:
    receipt = receipt_for()
    receipt["sources"]["analytic_lock"] = copy.deepcopy(receipt["sources"]["launch_lock"])
    seal(receipt)

    problems = validate(receipt).problems

    assert any("sources:analytic_lock" in problem for problem in problems)


@pytest.mark.parametrize(
    ("utc_finish", "utc_deadline", "mono_finish", "problem"),
    [
        (
            "2032-07-21T21:00:00.000000Z",
            "2032-07-21T21:00:01.000000Z",
            2_000_000_000,
            "observer:utc-duration",
        ),
        (
            "2026-07-21T09:00:01.000000Z",
            "2026-07-21T09:00:02.000000Z",
            1_000_000_000,
            "observer:monotonic-order",
        ),
        (
            "2026-07-21T09:00:02.000000Z",
            "2026-07-21T09:00:03.000000Z",
            2_000_000_000,
            "observer:duration-clock-disagreement",
        ),
    ],
)
def test_stale_zero_duration_and_clock_disagreement_fail_closed(
    utc_finish: str, utc_deadline: str, mono_finish: int, problem: str
) -> None:
    receipt = receipt_for()
    receipt["observer"]["finished_at_utc"] = utc_finish
    receipt["observer"]["deadline_at_utc"] = utc_deadline
    receipt["observer"]["finished_monotonic_ns"] = mono_finish
    seal(receipt)

    assert any(item.startswith(problem) for item in validate(receipt).problems)


def test_capture_must_stay_inside_observer_window_and_initial_precedes_terminal() -> None:
    receipt = receipt_for()
    receipt["sources"]["launch_lock"]["initial"]["started_monotonic_ns"] = 999_999_999
    receipt["sources"]["launch_lock"]["terminal"]["started_monotonic_ns"] = 1_100_000_000
    seal(receipt)

    problems = validate(receipt).problems

    assert "sources:launch_lock:initial:outside-observer-window" in problems
    assert "sources:launch_lock:capture-order" in problems


def test_zero_duration_captures_cannot_support_quiescence() -> None:
    receipt = receipt_for()
    for source in lifecycle.SOURCE_NAMES:
        for position in ("initial", "terminal"):
            capture_row = receipt["sources"][source][position]
            started = capture_row["started_monotonic_ns"]
            capture_row["finished_monotonic_ns"] = started
            observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
            observation["observed_monotonic_ns"] = started
            replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)

    result = validate(receipt)

    assert any("monotonic-order" in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


@pytest.mark.parametrize(
    ("field", "value", "problem_fragment"),
    [
        ("stdout_bytes", 0, "stdout-bytes"),
        ("stdout_sha256", "f" * 64, "stdout-sha256"),
        ("truncated", True, "verdict-mismatch"),
    ],
)
def test_stream_count_digest_and_truncation_fail_closed(
    field: str, value: object, problem_fragment: str
) -> None:
    receipt = receipt_for()
    receipt["sources"]["launch_lock"]["terminal"][field] = value
    seal(receipt)

    assert any(problem_fragment in problem for problem in validate(receipt).problems)


def test_self_checksum_is_not_accepted_as_detached_integrity() -> None:
    receipt = receipt_for()
    accepted_raw = raw_receipt(receipt)
    receipt["observer"]["host"] = "attacker-controlled-host"
    seal(receipt)

    result = validate(receipt, expected_raw=accepted_raw)

    assert "binding:receipt-sha256" in result.problems
    assert "observer:host" in result.problems


@pytest.mark.parametrize(
    ("binding", "value", "problem"),
    [
        ("expected_challenge_nonce_sha256", "d" * 64, "binding:challenge-nonce-sha256"),
        ("expected_boot_id", "223e4567-e89b-42d3-a456-426614174000", "binding:boot-id"),
        (
            "expected_observer_executable_sha256",
            "d" * 64,
            "binding:observer-executable-sha256",
        ),
        (
            "expected_observer_build_sha256",
            "d" * 64,
            "binding:observer-build-sha256",
        ),
        ("expected_cgroup_policy_sha256", "d" * 64, "binding:cgroup-policy-sha256"),
        ("expected_lease_id", "223e4567-e89b-42d3-b456-426614174001", "binding:lease-id"),
        (
            "expected_deadline_monotonic_ns",
            EXPECTED_DEADLINE_MONOTONIC_NS + 1,
            "binding:deadline-monotonic-ns",
        ),
        (
            "trusted_current_monotonic_ns",
            EXPECTED_DEADLINE_MONOTONIC_NS + 1,
            "binding:trusted-current-after-deadline",
        ),
        (
            "trusted_current_monotonic_ns",
            1_999_999_999,
            "binding:trusted-current-before-capture-finished",
        ),
    ],
)
def test_every_detached_trust_fault_forces_unknown(
    binding: str, value: object, problem: str
) -> None:
    result = validate(receipt_for(), detached_overrides={binding: value})

    assert problem in result.problems
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_detached_monotonic_boolean_is_rejected_as_not_an_integer() -> None:
    with pytest.raises(lifecycle.LifecycleReceiptError, match="current monotonic"):
        validate(
            receipt_for(),
            detached_overrides={"trusted_current_monotonic_ns": True},
        )


@pytest.mark.parametrize(
    ("target", "problem"),
    [
        ("observer", "observer:started-monotonic-ns"),
        ("capture", "sources:launch_lock:initial:return-code"),
        ("record", "sources:launch_lock:initial:observation:record:owner-pid"),
    ],
)
def test_boolean_integer_aliases_fail_closed(target: str, problem: str) -> None:
    receipt = receipt_for("ACTIVE")
    if target == "observer":
        receipt["observer"]["started_monotonic_ns"] = True
    elif target == "capture":
        receipt["sources"]["launch_lock"]["initial"]["return_code"] = False
    else:
        mutate_record(receipt, "launch_lock", "initial", "owner_pid", True)
    seal(receipt)

    result = validate(receipt)

    assert problem in result.problems
    assert result.verdict == "UNKNOWN"


def test_boolean_empty_stream_byte_count_alias_fails_closed() -> None:
    receipt = receipt_for()
    for source in lifecycle.SOURCE_NAMES:
        for position in ("initial", "terminal"):
            receipt["sources"][source][position]["stderr_bytes"] = False
    seal(receipt)

    result = validate(receipt)

    assert any(problem.endswith(":stderr-bytes") for problem in result.problems)
    assert result.verdict == "UNKNOWN"


def test_noncanonical_base64_pad_bits_cannot_retain_quiescence() -> None:
    receipt = receipt_for()
    capture_row = receipt["sources"]["launch_lock"]["initial"]
    canonical = capture_row["stdout_base64"]
    alternate = noncanonical_pad_bits(canonical)
    assert base64.b64decode(alternate, validate=True) == base64.b64decode(
        canonical,
        validate=True,
    )
    capture_row["stdout_base64"] = alternate
    seal(receipt)

    result = validate(receipt)

    assert any("stdout-base64-noncanonical" in problem for problem in result.problems)
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_every_serialized_integer_leaf_rejects_boolean_aliases() -> None:
    baseline = receipt_for()
    integer_paths: list[tuple[str | int, ...]] = []

    def collect(value: object, path: tuple[str | int, ...] = ()) -> None:
        if type(value) is int:
            integer_paths.append(path)
        elif type(value) is dict:
            for key, child in value.items():
                collect(child, (*path, key))
        elif type(value) is list:
            for index, child in enumerate(value):
                collect(child, (*path, index))

    collect(baseline)
    assert integer_paths
    for path in integer_paths:
        for alias in (False, True):
            receipt = copy.deepcopy(baseline)
            parent: object = receipt
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = alias
            seal(receipt)

            result = validate(receipt)

            assert result.verdict == "UNKNOWN", (path, alias, result)
            assert result.quiescence_evidence_complete is False


def test_global_rounds_require_preregistered_minimum_dwell() -> None:
    receipt = receipt_for()
    for source in lifecycle.SOURCE_NAMES:
        capture_row = receipt["sources"][source]["terminal"]
        capture_row["started_monotonic_ns"] -= 300_000_000
        capture_row["finished_monotonic_ns"] -= 300_000_000
        observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
        observation["observed_monotonic_ns"] -= 300_000_000
        replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)

    result = validate(receipt)

    assert "sources:minimum-round-dwell" in result.problems
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_producer_appearing_between_global_rounds_is_inconsistent() -> None:
    receipt = receipt_for()
    receipt["sources"]["launcher_process"]["terminal"] = capture(
        "launcher_process",
        "ACTIVE",
        "terminal",
        lifecycle.SOURCE_NAMES.index("launcher_process"),
    )
    receipt["verdict"] = "INCONSISTENT"
    receipt["quiescence_evidence_complete"] = False
    seal(receipt)

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"


@pytest.mark.parametrize(
    ("source", "field", "value"),
    [
        ("launcher_process", "process_start_ticks", 44_202),
        ("launcher_process", "executable_sha256", "e" * 64),
    ],
)
def test_source_record_identity_drift_between_rounds_is_inconsistent(
    source: str, field: str, value: object
) -> None:
    receipt = receipt_for("ACTIVE")
    mutate_record(receipt, source, "terminal", field, value)
    receipt["verdict"] = "INCONSISTENT"
    seal(receipt)

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"


@pytest.mark.parametrize(
    ("source", "field", "value", "problem"),
    [
        (
            "attempt_journal",
            "terminal_cause",
            "EXIT_NONZERO",
            "journal-state-cause-mapping",
        ),
        (
            "provider_job_registry",
            "terminal_cause",
            "EXIT_NONZERO",
            "provider-state-cause-mapping",
        ),
        (
            "terminal_witness",
            "terminal_cause",
            "UNREGISTERED_CAUSE",
            "terminal-cause",
        ),
    ],
)
def test_terminal_state_and_cause_mapping_is_exact(
    source: str, field: str, value: str, problem: str
) -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    for position in ("initial", "terminal"):
        mutate_record(receipt, source, position, field, value)

    result = validate(receipt)

    assert any(problem in item for item in result.problems)
    assert result.verdict == "UNKNOWN"


@pytest.mark.parametrize("fault", ["boolean-count", "digest", "noncanonical", "cause-map"])
def test_retained_proof_manifest_bytes_are_strictly_validated(fault: str) -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    for position in ("initial", "terminal"):
        capture_row = receipt["sources"]["proof_manifest"][position]
        observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
        record = observation["records"][0]
        if fault == "boolean-count":
            record["proof_manifest_bytes"] = True
        elif fault == "digest":
            record["proof_manifest_sha256"] = "f" * 64
        else:
            proof = json.loads(base64.b64decode(record["proof_manifest_base64"]))
            if fault == "cause-map":
                proof["terminal_cause"] = "EXIT_NONZERO"
                proof_raw = lifecycle._canonical_json(proof) + b"\n"
            else:
                proof_raw = json.dumps(proof, indent=2).encode() + b"\n"
            record["proof_manifest_base64"] = base64.b64encode(proof_raw).decode()
            record["proof_manifest_bytes"] = len(proof_raw)
            record["proof_manifest_sha256"] = hashlib.sha256(proof_raw).hexdigest()
        replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)

    result = validate(receipt)

    assert any("proof-manifest" in item for item in result.problems)
    assert result.verdict == "UNKNOWN"


def test_noncanonical_proof_manifest_base64_pad_bits_fail_closed() -> None:
    receipt = receipt_for("TERMINATED_COMPLETE")
    for position in ("initial", "terminal"):
        capture_row = receipt["sources"]["proof_manifest"][position]
        observation = json.loads(base64.b64decode(capture_row["stdout_base64"]))
        canonical = observation["records"][0]["proof_manifest_base64"]
        alternate = noncanonical_pad_bits(canonical)
        assert base64.b64decode(alternate, validate=True) == base64.b64decode(
            canonical,
            validate=True,
        )
        observation["records"][0]["proof_manifest_base64"] = alternate
        replace_stdout(capture_row, lifecycle._canonical_json(observation) + b"\n")
    seal(receipt)

    result = validate(receipt)

    assert any("proof-manifest-base64-noncanonical" in item for item in result.problems)
    assert result.verdict == "UNKNOWN"


def test_source_payloads_retain_records_not_lifecycle_assertions() -> None:
    receipt = receipt_for("ACTIVE")
    raw = base64.b64decode(receipt["sources"]["launcher_process"]["initial"]["stdout_base64"])
    observation = json.loads(raw)

    assert set(observation) == lifecycle.SOURCE_OBSERVATION_FIELDS
    assert "registry_state" not in observation
    assert observation["records"][0]["pid"] == 913


def test_bounded_multi_record_container_inventory_is_representable() -> None:
    receipt = receipt_for("ACTIVE")
    records = records_for("mission_containers", "ACTIVE")
    second = copy.deepcopy(records[0])
    second["container_id"] = "i135-mission-containers-sidecar"
    records.append(second)
    for position in ("initial", "terminal"):
        replace_records(receipt, "mission_containers", position, records)
        replace_records(
            receipt,
            "global_containers",
            position,
            [global_record_for_mission(record) for record in records],
        )

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "RUNNING"


@pytest.mark.parametrize(
    ("field", "value", "problem"),
    [
        ("scope", "partial-process-sample", "enumeration:scope"),
        ("filter", "unbound", "enumeration:filter"),
        ("sort", "arrival-order", "enumeration:sort"),
        ("page_count", False, "enumeration:page-count"),
        ("record_count", True, "enumeration:record-count"),
        ("complete", False, "enumeration:complete"),
        ("continuation_token", "next-page", "enumeration:continuation-token"),
    ],
)
def test_enumeration_scope_pagination_and_completeness_are_exact(
    field: str, value: object, problem: str
) -> None:
    receipt = receipt_for()
    mutate_enumeration(receipt, "launcher_process", "terminal", field, value)

    result = validate(receipt)

    assert any(problem in item for item in result.problems)
    assert result.verdict == "UNKNOWN"
    assert result.quiescence_evidence_complete is False


def test_multi_record_arrays_require_canonical_order() -> None:
    receipt = receipt_for("ACTIVE")
    first = records_for("mission_containers", "ACTIVE")[0]
    second = copy.deepcopy(first)
    first["container_id"] = "z-container"
    second["container_id"] = "a-container"
    for position in ("initial", "terminal"):
        replace_records(
            receipt,
            "mission_containers",
            position,
            [first, second],
            canonical_sort=False,
        )

    result = validate(receipt)

    assert any("records-order" in item for item in result.problems)
    assert result.verdict == "UNKNOWN"


def test_multi_record_semantic_conflict_is_inconsistent() -> None:
    receipt = receipt_for("ACTIVE")
    first = records_for("mission_containers", "ACTIVE")[0]
    second = copy.deepcopy(first)
    second["attempt_id"] = "i135-attempt-0002"
    second["container_id"] = "i135-second-attempt-container"
    for position in ("initial", "terminal"):
        replace_records(receipt, "mission_containers", position, [first, second])
        replace_records(
            receipt,
            "global_containers",
            position,
            [global_record_for_mission(record) for record in (first, second)],
        )
    receipt["verdict"] = "INCONSISTENT"
    seal(receipt)

    result = validate(receipt)

    assert result.problems == ()
    assert result.verdict == "INCONSISTENT"


@pytest.mark.parametrize("field", ["launch_authorized", "relaunch_authorized"])
@pytest.mark.parametrize(
    "state",
    ["GENESIS", "ACTIVE", "TERMINATED_COMPLETE", "TERMINATED_PARTIAL"],
)
def test_every_verdict_rejects_forbidden_authority_flags(state: str, field: str) -> None:
    receipt = receipt_for(state)
    receipt[field] = True
    seal(receipt)

    assert f"receipt:{field.replace('_', '-')}" in validate(receipt).problems


@pytest.mark.parametrize("field", ["launch_authorized", "relaunch_authorized"])
def test_host_occupied_rejects_forbidden_authority_flags(field: str) -> None:
    receipt = receipt_for()
    occupant = copy.deepcopy(GLOBAL_OCCUPANT_CASES[1][1])
    for position in ("initial", "terminal"):
        replace_records(receipt, "global_containers", position, [occupant])
    set_claimed_verdict(receipt, "HOST_OCCUPIED")
    receipt[field] = True
    seal(receipt)

    assert f"receipt:{field.replace('_', '-')}" in validate(receipt).problems


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b'{"schema":"first","schema":"second"}\n', "duplicate JSON key"),
        (b'{"value":NaN}\n', "non-finite JSON number"),
        (b'{"value":1e999999}\n', "non-finite JSON number"),
        (b'{"value":' + b"9" * 5000 + b"}\n", "malformed JSON"),
    ],
)
def test_public_parser_rejects_ambiguous_or_unbounded_numbers(payload: bytes, message: str) -> None:
    with pytest.raises(lifecycle.LifecycleReceiptError, match=message):
        lifecycle.parse_validate_reduce(
            payload,
            expected_receipt_sha256=hashlib.sha256(payload).hexdigest(),
            expected_control_source_commit=CONTROL_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_mission_state_sha256=MISSION_STATE_SHA256,
            expected_host_identity_sha256=HOST_IDENTITY_SHA256,
            expected_challenge_nonce_sha256=CHALLENGE_SHA256,
            expected_boot_id=BOOT_ID,
            expected_observer_executable_sha256=EXECUTABLE_SHA256,
            expected_observer_build_sha256=BUILD_SHA256,
            expected_cgroup_policy_sha256=CGROUP_POLICY_SHA256,
            expected_lease_id=LEASE_ID,
            trusted_current_monotonic_ns=TRUSTED_CURRENT_MONOTONIC_NS,
            expected_deadline_monotonic_ns=EXPECTED_DEADLINE_MONOTONIC_NS,
        )


def test_public_parser_rejects_excessive_nesting() -> None:
    payload = ("[" * 24 + "0" + "]" * 24).encode()

    with pytest.raises(lifecycle.LifecycleReceiptError, match="shape exceeds"):
        lifecycle.parse_validate_reduce(
            payload,
            expected_receipt_sha256=hashlib.sha256(payload).hexdigest(),
            expected_control_source_commit=CONTROL_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_mission_state_sha256=MISSION_STATE_SHA256,
            expected_host_identity_sha256=HOST_IDENTITY_SHA256,
            expected_challenge_nonce_sha256=CHALLENGE_SHA256,
            expected_boot_id=BOOT_ID,
            expected_observer_executable_sha256=EXECUTABLE_SHA256,
            expected_observer_build_sha256=BUILD_SHA256,
            expected_cgroup_policy_sha256=CGROUP_POLICY_SHA256,
            expected_lease_id=LEASE_ID,
            trusted_current_monotonic_ns=TRUSTED_CURRENT_MONOTONIC_NS,
            expected_deadline_monotonic_ns=EXPECTED_DEADLINE_MONOTONIC_NS,
        )


def test_public_entrypoint_requires_bytes() -> None:
    receipt = receipt_for()

    with pytest.raises(lifecycle.LifecycleReceiptError, match="input must be bytes"):
        lifecycle.parse_validate_reduce(
            receipt,
            expected_receipt_sha256="f" * 64,
            expected_control_source_commit=CONTROL_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_mission_state_sha256=MISSION_STATE_SHA256,
            expected_host_identity_sha256=HOST_IDENTITY_SHA256,
            expected_challenge_nonce_sha256=CHALLENGE_SHA256,
            expected_boot_id=BOOT_ID,
            expected_observer_executable_sha256=EXECUTABLE_SHA256,
            expected_observer_build_sha256=BUILD_SHA256,
            expected_cgroup_policy_sha256=CGROUP_POLICY_SHA256,
            expected_lease_id=LEASE_ID,
            trusted_current_monotonic_ns=TRUSTED_CURRENT_MONOTONIC_NS,
            expected_deadline_monotonic_ns=EXPECTED_DEADLINE_MONOTONIC_NS,
        )


def test_noncanonical_receipt_bytes_fail_closed() -> None:
    receipt = receipt_for()
    noncanonical = json.dumps(receipt, indent=2).encode() + b"\n"
    result = lifecycle.parse_validate_reduce(
        noncanonical,
        expected_receipt_sha256=hashlib.sha256(noncanonical).hexdigest(),
        expected_control_source_commit=CONTROL_COMMIT,
        expected_source_commit=SOURCE_COMMIT,
        expected_mission_state_sha256=MISSION_STATE_SHA256,
        expected_host_identity_sha256=HOST_IDENTITY_SHA256,
        expected_challenge_nonce_sha256=CHALLENGE_SHA256,
        expected_boot_id=BOOT_ID,
        expected_observer_executable_sha256=EXECUTABLE_SHA256,
        expected_observer_build_sha256=BUILD_SHA256,
        expected_cgroup_policy_sha256=CGROUP_POLICY_SHA256,
        expected_lease_id=LEASE_ID,
        trusted_current_monotonic_ns=TRUSTED_CURRENT_MONOTONIC_NS,
        expected_deadline_monotonic_ns=EXPECTED_DEADLINE_MONOTONIC_NS,
    )

    assert "receipt:noncanonical-bytes" in result.problems


def test_validator_source_has_no_performing_surface() -> None:
    source = MODULE_PATH.read_text()

    for forbidden in (
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "gcloud",
        "compute ssh",
        "docker ps",
        "os.system",
        "Popen",
    ):
        assert forbidden not in source
