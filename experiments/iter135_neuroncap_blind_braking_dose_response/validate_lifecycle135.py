#!/usr/bin/env python3
"""Pure, offline reduction of raw iteration-135 lifecycle capture bytes.

The only public entrypoint accepts bytes plus detached trusted bindings.  This module performs no
host observation and serializes no permission.  In particular, a receipt cannot prove that a file
descriptor is still open or that a lock is still held.  A future performing controller must retain
and atomically consume that nonserializable live capability before any host mutation.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from datetime import datetime
import hashlib
import json
import math
import re
import stat
from typing import Any, NamedTuple


SCHEMA = "iter135.lifecycle_observation.v2"
SOURCE_SCHEMA = "iter135.lifecycle_source_observation.v2"
PROOF_MANIFEST_SCHEMA = "iter135.lifecycle_proof_manifest.v1"
ITERATION = 135
EXPERIMENT = "experiments/iter135_neuroncap_blind_braking_dose_response"
EXPECTED_HOST = "sentinel-gpu"
LEASE_PATH = "/var/lib/sentinel/i135-lifecycle-observer.lock"
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
MAX_STREAM_BYTES = 64 * 1024
MAX_RECORDS_PER_SOURCE = 1024
MAX_PAGES_PER_SOURCE = 1024
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 20_000
MAX_PROBLEMS = 256
MAX_INT = (1 << 63) - 1
MAX_OBSERVATION_DURATION_NS = 5_000_000_000
MAX_CAPTURE_DURATION_NS = 2_000_000_000
MAX_CONSUMPTION_WINDOW_NS = 2_000_000_000
MIN_ROUND_DWELL_NS = 500_000_000
TIME_AGREEMENT_TOLERANCE_NS = 100_000_000
EXPECTED_LEASE_MODE = stat.S_IFREG | 0o600

SOURCE_NAMES = (
    "launch_lock",
    "launcher_process",
    "mission_containers",
    "global_containers",
    "analytic_lock",
    "attempt_journal",
    "terminal_witness",
    "proof_manifest",
    "provider_job_registry",
)
QUERY_PARSERS = {
    "launch_lock": "bounded-launch-lock-records.v2",
    "launcher_process": "bounded-launcher-process-records.v2",
    "mission_containers": "bounded-mission-container-records.v2",
    "global_containers": "bounded-global-container-records.v2",
    "analytic_lock": "bounded-analytic-lock-records.v2",
    "attempt_journal": "bounded-attempt-journal-records.v2",
    "terminal_witness": "bounded-terminal-witness-records.v2",
    "proof_manifest": "bounded-retained-proof-manifest-records.v2",
    "provider_job_registry": "bounded-provider-job-records.v2",
}
ENUMERATION_SCOPES = {
    "launch_lock": "iteration-135-launch-lock-path",
    "launcher_process": "complete-host-process-table",
    "mission_containers": "complete-runtime-container-registry",
    "global_containers": "complete-runtime-container-registry",
    "analytic_lock": "iteration-135-analytic-lock-path",
    "attempt_journal": "iteration-135-attempt-journal-directory",
    "terminal_witness": "iteration-135-terminal-witness-directory",
    "proof_manifest": "iteration-135-proof-manifest-directory",
    "provider_job_registry": "configured-provider-project-region-job-registry",
}
ENUMERATION_FILTERS = {
    "launch_lock": "canonical-path-exact",
    "launcher_process": "all-processes-then-exact-iteration-binding",
    "mission_containers": "label-iteration=135",
    "global_containers": "all-containers-then-exact-iteration-binding",
    "analytic_lock": "canonical-path-exact",
    "attempt_journal": "attempt-prefix=i135-",
    "terminal_witness": "attempt-prefix=i135-",
    "proof_manifest": "attempt-prefix=i135-",
    "provider_job_registry": "mission-label-iteration=135",
}
ENUMERATION_SORT = "canonical-json-record-bytes-ascending"
MAX_RECORDS_BY_SOURCE = {
    source: 1 if source in {"launch_lock", "analytic_lock"} else MAX_RECORDS_PER_SOURCE
    for source in SOURCE_NAMES
}
# These hashes domain-separate the strict retained-record parsers.  They are not hashes of a host
# command, argv, environment, working directory, provider request, or executable query plan; no
# such performing implementation is accepted by this source-only generation.
QUERY_CONTRACTS = {
    name: json.dumps(
        {
            "challenge_binding": "sha256",
            "host_boot_binding": "exact",
            "host_invocation": "outside-generation-16",
            "enumeration_filter": ENUMERATION_FILTERS[name],
            "enumeration_scope": ENUMERATION_SCOPES[name],
            "enumeration_sort": ENUMERATION_SORT,
            "maximum_pages": MAX_PAGES_PER_SOURCE,
            "maximum_records": MAX_RECORDS_BY_SOURCE[name],
            "output": "canonical-json-line",
            "parser": QUERY_PARSERS[name],
            "parser_contract_schema": "iter135.lifecycle.parser_contract.v2",
            "records": "bounded-complete-canonically-sorted-array",
            "rounds": ["initial", "terminal"],
            "source": name,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    + b"\n"
    for name in SOURCE_NAMES
}
QUERY_SHA256 = {
    name: hashlib.sha256(contract).hexdigest() for name, contract in QUERY_CONTRACTS.items()
}
QUERY_POLICY_SHA256 = hashlib.sha256(
    json.dumps(
        QUERY_SHA256,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
).hexdigest()

ROOT_FIELDS = {
    "schema",
    "mission",
    "observer",
    "lease",
    "sources",
    "verdict",
    "quiescence_evidence_complete",
    "launch_authorized",
    "relaunch_authorized",
    "problems",
    "problem_count",
    "receipt_payload_self_checksum_sha256",
}
MISSION_FIELDS = {
    "iteration",
    "experiment",
    "source_commit",
    "mission_state_sha256",
    "manifest_sha256",
    "attempt_id",
}
OBSERVER_FIELDS = {
    "control_source_commit",
    "host",
    "query_policy_sha256",
    "challenge_nonce_sha256",
    "started_at_utc",
    "finished_at_utc",
    "deadline_at_utc",
    "started_monotonic_ns",
    "finished_monotonic_ns",
    "deadline_monotonic_ns",
    "initial_identity",
    "terminal_identity",
}
IDENTITY_FIELDS = {
    "host_identity_sha256",
    "boot_id",
    "pid",
    "process_start_ticks",
    "executable_sha256",
    "build_sha256",
    "cgroup_policy_sha256",
}
LEASE_FIELDS = {
    "id",
    "path",
    "owner_identity",
    "acquired_at_utc",
    "initial_snapshot",
    "terminal_snapshot",
}
LEASE_SNAPSHOT_FIELDS = {
    "device",
    "inode",
    "mount_id",
    "mode",
    "uid",
    "gid",
    "link_count",
    "size",
    "mtime_ns",
    "ctime_ns",
}
SOURCE_PAIR_FIELDS = {"initial", "terminal"}
CAPTURE_FIELDS = {
    "query_sha256",
    "started_monotonic_ns",
    "finished_monotonic_ns",
    "return_code",
    "timed_out",
    "truncated",
    "stdout_base64",
    "stdout_bytes",
    "stdout_sha256",
    "stderr_base64",
    "stderr_bytes",
    "stderr_sha256",
}
SOURCE_OBSERVATION_FIELDS = {
    "schema",
    "source",
    "query_sha256",
    "challenge_nonce_sha256",
    "host_identity_sha256",
    "boot_id",
    "observed_monotonic_ns",
    "enumeration",
    "records",
}
ENUMERATION_FIELDS = {
    "scope",
    "filter",
    "sort",
    "page_count",
    "record_count",
    "complete",
    "continuation_token",
}
RECORD_FIELDS = {
    "launch_lock": {
        "attempt_id",
        "manifest_sha256",
        "owner_pid",
        "owner_process_start_ticks",
    },
    "launcher_process": {
        "attempt_id",
        "manifest_sha256",
        "pid",
        "process_start_ticks",
        "executable_sha256",
    },
    "mission_containers": {
        "attempt_id",
        "manifest_sha256",
        "container_id",
        "runtime_state",
    },
    "global_containers": {
        "attempt_id",
        "manifest_sha256",
        "container_id",
        "runtime_state",
    },
    "analytic_lock": {
        "attempt_id",
        "manifest_sha256",
        "owner_pid",
        "owner_process_start_ticks",
    },
    "attempt_journal": {
        "attempt_id",
        "manifest_sha256",
        "journal_state",
        "terminal_cause",
        "proof_manifest_sha256",
    },
    "terminal_witness": {
        "attempt_id",
        "manifest_sha256",
        "terminal_state",
        "terminal_cause",
        "proof_manifest_sha256",
    },
    "proof_manifest": {
        "attempt_id",
        "manifest_sha256",
        "proof_manifest_base64",
        "proof_manifest_bytes",
        "proof_manifest_sha256",
    },
    "provider_job_registry": {
        "attempt_id",
        "manifest_sha256",
        "job_id",
        "provider_state",
        "terminal_cause",
        "proof_manifest_sha256",
    },
}
PROOF_MANIFEST_FIELDS = {
    "schema",
    "attempt_id",
    "manifest_sha256",
    "terminal_state",
    "terminal_cause",
    "artifact_count",
}
COMPLETE_TERMINAL_CAUSES = {"EXIT_ZERO"}
PARTIAL_TERMINAL_CAUSES = {
    "CANCELLED",
    "EXIT_NONZERO",
    "INFRA_FAILURE",
    "SIGNALLED",
    "TIMEOUT",
}
PROVIDER_STATE_BY_CAUSE = {
    "EXIT_ZERO": "SUCCEEDED",
    "CANCELLED": "CANCELLED",
    "EXIT_NONZERO": "FAILED",
    "INFRA_FAILURE": "FAILED",
    "SIGNALLED": "FAILED",
    "TIMEOUT": "FAILED",
}
VERDICTS = {
    "UNKNOWN",
    "RUNNING",
    "TERMINATED_COMPLETE",
    "TERMINATED_PARTIAL",
    "INCONSISTENT",
    "QUIESCENCE_EVIDENCE_COMPLETE",
}

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\Z")
_ATTEMPT_ID = re.compile(r"i135-[a-z0-9][a-z0-9._-]{0,126}\Z")
_RESOURCE_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:@/-]{0,255}\Z")
_PROBLEM_CODE = re.compile(r"[a-z][a-z0-9_.:-]{0,255}\Z")


class LifecycleReceiptError(ValueError):
    """Receipt bytes could not be decoded without ambiguity."""


class ValidationResult(NamedTuple):
    problems: tuple[str, ...]
    verdict: str
    quiescence_evidence_complete: bool
    receipt_sha256: str


class SourceFact(NamedTuple):
    kind: str
    attempt_id: str | None
    manifest_sha256: str | None
    terminal_cause: str | None
    proof_manifest_sha256: str | None
    record_sha256: str


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LifecycleReceiptError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise LifecycleReceiptError(f"non-finite JSON number: {value}")


def _decode_json(raw: bytes, *, label: str, maximum: int) -> Any:
    if type(raw) is not bytes or not raw or len(raw) > maximum:
        raise LifecycleReceiptError(f"{label} byte length is outside the accepted range")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except LifecycleReceiptError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
        OverflowError,
    ) as error:
        raise LifecycleReceiptError(f"{label} malformed JSON: {type(error).__name__}") from error
    node_count = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        node_count += 1
        if depth > MAX_JSON_DEPTH or node_count > MAX_JSON_NODES:
            raise LifecycleReceiptError(f"{label} JSON shape exceeds the accepted bound")
        if type(current) is dict:
            stack.extend((item, depth + 1) for item in current.values())
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in current)
        elif type(current) is int and (current < -MAX_INT or current > MAX_INT):
            raise LifecycleReceiptError(f"{label} integer exceeds the accepted bound")
        elif type(current) is float:
            if not math.isfinite(current):
                raise LifecycleReceiptError(f"{label} contains a non-finite JSON number")
            raise LifecycleReceiptError(f"{label} floating-point JSON numbers are not accepted")
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _payload_self_checksum(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_payload_self_checksum_sha256", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _sha256(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _commit(value: object) -> bool:
    return type(value) is str and _COMMIT.fullmatch(value) is not None


def _uuid(value: object) -> bool:
    return type(value) is str and _UUID.fullmatch(value) is not None


def _exact_int(value: object, *, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= MAX_INT


def _utc_datetime(value: object) -> datetime | None:
    if type(value) is not str or _UTC.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return None
    return parsed if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") == value else None


def _nanoseconds(delta_seconds: float) -> int:
    return round(delta_seconds * 1_000_000_000)


def _field_set(value: object, expected: set[str], label: str) -> list[str]:
    if type(value) is not dict:
        return [f"{label}:not-object"]
    return [] if set(value) == expected else [f"{label}:field-set"]


def _identity_problems(identity: object, label: str) -> list[str]:
    problems = _field_set(identity, IDENTITY_FIELDS, label)
    if type(identity) is not dict:
        return problems
    for field in (
        "host_identity_sha256",
        "executable_sha256",
        "build_sha256",
        "cgroup_policy_sha256",
    ):
        if not _sha256(identity.get(field)):
            problems.append(f"{label}:{field.replace('_', '-')}")
    if not _uuid(identity.get("boot_id")):
        problems.append(f"{label}:boot-id")
    if not _exact_int(identity.get("pid"), minimum=1):
        problems.append(f"{label}:pid")
    if not _exact_int(identity.get("process_start_ticks")):
        problems.append(f"{label}:process-start-ticks")
    return problems


def _lease_snapshot_problems(snapshot: object, label: str) -> list[str]:
    problems = _field_set(snapshot, LEASE_SNAPSHOT_FIELDS, label)
    if type(snapshot) is not dict:
        return problems
    for field in (
        "device",
        "mount_id",
        "uid",
        "gid",
        "link_count",
        "size",
        "mtime_ns",
        "ctime_ns",
    ):
        if not _exact_int(snapshot.get(field)):
            problems.append(f"{label}:{field.replace('_', '-')}")
    if not _exact_int(snapshot.get("inode"), minimum=1):
        problems.append(f"{label}:inode")
    if snapshot.get("mode") != EXPECTED_LEASE_MODE:
        problems.append(f"{label}:mode")
    if snapshot.get("uid") != 0 or snapshot.get("gid") != 0:
        problems.append(f"{label}:ownership")
    if snapshot.get("link_count") != 1:
        problems.append(f"{label}:link-count")
    return problems


def _stream_bytes(
    capture: Mapping[str, Any], prefix: str, label: str
) -> tuple[bytes | None, list[str]]:
    problems: list[str] = []
    encoded = capture.get(f"{prefix}_base64")
    if type(encoded) is not str or len(encoded) > 4 * MAX_STREAM_BYTES + 16:
        return None, [f"{label}:{prefix}-base64"]
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None, [f"{label}:{prefix}-base64"]
    if base64.b64encode(decoded).decode("ascii") != encoded:
        problems.append(f"{label}:{prefix}-base64-noncanonical")
    if len(decoded) > MAX_STREAM_BYTES:
        problems.append(f"{label}:{prefix}-size-bound")
    byte_count = capture.get(f"{prefix}_bytes")
    if not _exact_int(byte_count) or byte_count != len(decoded):
        problems.append(f"{label}:{prefix}-bytes")
    if capture.get(f"{prefix}_sha256") != hashlib.sha256(decoded).hexdigest():
        problems.append(f"{label}:{prefix}-sha256")
    return decoded, problems


def _capture_problems(capture: object, source: str, label: str) -> tuple[list[str], bytes | None]:
    problems = _field_set(capture, CAPTURE_FIELDS, label)
    if type(capture) is not dict:
        return problems, None
    if capture.get("query_sha256") != QUERY_SHA256[source]:
        problems.append(f"{label}:query-sha256")
    started = capture.get("started_monotonic_ns")
    finished = capture.get("finished_monotonic_ns")
    if not _exact_int(started):
        problems.append(f"{label}:started-monotonic-ns")
    if not _exact_int(finished):
        problems.append(f"{label}:finished-monotonic-ns")
    if _exact_int(started) and _exact_int(finished):
        if finished <= started:
            problems.append(f"{label}:monotonic-order")
        elif finished - started > MAX_CAPTURE_DURATION_NS:
            problems.append(f"{label}:duration")
    return_code = capture.get("return_code")
    if not _exact_int(return_code) or return_code > 255:
        problems.append(f"{label}:return-code")
    for field in ("timed_out", "truncated"):
        if type(capture.get(field)) is not bool:
            problems.append(f"{label}:{field.replace('_', '-')}")
    stdout, stdout_problems = _stream_bytes(capture, "stdout", label)
    stderr, stderr_problems = _stream_bytes(capture, "stderr", label)
    problems.extend(stdout_problems)
    problems.extend(stderr_problems)
    observed = (
        not problems
        and return_code == 0
        and capture.get("timed_out") is False
        and capture.get("truncated") is False
        and stderr == b""
        and stdout is not None
    )
    return problems, stdout if observed else None


def _attempt_manifest_problems(record: Mapping[str, Any], label: str) -> list[str]:
    problems: list[str] = []
    attempt_id = record.get("attempt_id")
    if type(attempt_id) is not str or _ATTEMPT_ID.fullmatch(attempt_id) is None:
        problems.append(f"{label}:attempt-id")
    if not _sha256(record.get("manifest_sha256")):
        problems.append(f"{label}:manifest-sha256")
    return problems


def _terminal_state_for_cause(cause: object) -> str | None:
    if type(cause) is not str:
        return None
    if cause in COMPLETE_TERMINAL_CAUSES:
        return "TERMINATED_COMPLETE"
    if cause in PARTIAL_TERMINAL_CAUSES:
        return "TERMINATED_PARTIAL"
    return None


def _terminal_fact(
    record: Mapping[str, Any],
    *,
    state_field: str,
    label: str,
) -> tuple[list[str], SourceFact | None]:
    problems = _attempt_manifest_problems(record, label)
    cause = record.get("terminal_cause")
    derived_state = _terminal_state_for_cause(cause)
    if derived_state is None:
        problems.append(f"{label}:terminal-cause")
    if record.get(state_field) != derived_state:
        problems.append(f"{label}:{state_field.replace('_', '-')}-cause-mapping")
    proof_sha256 = record.get("proof_manifest_sha256")
    if not _sha256(proof_sha256):
        problems.append(f"{label}:proof-manifest-sha256")
    if problems or derived_state is None:
        return sorted(set(problems)), None
    return [], SourceFact(
        derived_state,
        record["attempt_id"],
        record["manifest_sha256"],
        cause,
        proof_sha256,
        hashlib.sha256(_canonical_json([record])).hexdigest(),
    )


def _proof_manifest_fact(
    record: Mapping[str, Any], label: str
) -> tuple[list[str], SourceFact | None]:
    problems = _attempt_manifest_problems(record, label)
    encoded = record.get("proof_manifest_base64")
    if type(encoded) is not str or len(encoded) > 4 * MAX_STREAM_BYTES + 16:
        return sorted(set(problems + [f"{label}:proof-manifest-base64"])), None
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return sorted(set(problems + [f"{label}:proof-manifest-base64"])), None
    if base64.b64encode(raw).decode("ascii") != encoded:
        problems.append(f"{label}:proof-manifest-base64-noncanonical")
    if len(raw) > MAX_STREAM_BYTES:
        problems.append(f"{label}:proof-manifest-size-bound")
    byte_count = record.get("proof_manifest_bytes")
    if not _exact_int(byte_count) or byte_count != len(raw):
        problems.append(f"{label}:proof-manifest-bytes")
    raw_digest = hashlib.sha256(raw).hexdigest()
    if record.get("proof_manifest_sha256") != raw_digest:
        problems.append(f"{label}:proof-manifest-sha256")
    try:
        manifest = _decode_json(raw, label=f"{label}:proof-manifest", maximum=MAX_STREAM_BYTES)
    except LifecycleReceiptError as error:
        problems.append(f"{label}:proof-manifest-json:{error}")
        return sorted(set(problems)), None
    problems.extend(_field_set(manifest, PROOF_MANIFEST_FIELDS, f"{label}:proof-manifest"))
    if type(manifest) is not dict:
        return sorted(set(problems)), None
    if raw != _canonical_json(manifest) + b"\n":
        problems.append(f"{label}:proof-manifest-noncanonical-bytes")
    if manifest.get("schema") != PROOF_MANIFEST_SCHEMA:
        problems.append(f"{label}:proof-manifest-schema")
    for field in ("attempt_id", "manifest_sha256"):
        if manifest.get(field) != record.get(field):
            problems.append(f"{label}:proof-manifest-{field.replace('_', '-')}-binding")
    cause = manifest.get("terminal_cause")
    derived_state = _terminal_state_for_cause(cause)
    if derived_state is None:
        problems.append(f"{label}:proof-manifest-terminal-cause")
    if manifest.get("terminal_state") != derived_state:
        problems.append(f"{label}:proof-manifest-state-cause-mapping")
    artifact_count = manifest.get("artifact_count")
    if not _exact_int(artifact_count):
        problems.append(f"{label}:proof-manifest-artifact-count")
    elif derived_state == "TERMINATED_COMPLETE" and artifact_count < 1:
        problems.append(f"{label}:proof-manifest-complete-artifact-count")
    if problems or derived_state is None:
        return sorted(set(problems)), None
    return [], SourceFact(
        derived_state,
        record["attempt_id"],
        record["manifest_sha256"],
        cause,
        raw_digest,
        hashlib.sha256(_canonical_json([record])).hexdigest(),
    )


def _enumeration_problems(
    enumeration: object,
    *,
    source: str,
    record_count: int | None,
    label: str,
) -> list[str]:
    problems = _field_set(enumeration, ENUMERATION_FIELDS, f"{label}:enumeration")
    if type(enumeration) is not dict:
        return problems
    if enumeration.get("scope") != ENUMERATION_SCOPES[source]:
        problems.append(f"{label}:enumeration:scope")
    if enumeration.get("filter") != ENUMERATION_FILTERS[source]:
        problems.append(f"{label}:enumeration:filter")
    if enumeration.get("sort") != ENUMERATION_SORT:
        problems.append(f"{label}:enumeration:sort")
    page_count = enumeration.get("page_count")
    if not _exact_int(page_count, minimum=1) or page_count > MAX_PAGES_PER_SOURCE:
        problems.append(f"{label}:enumeration:page-count")
    observed_record_count = enumeration.get("record_count")
    if (
        not _exact_int(observed_record_count)
        or observed_record_count > MAX_RECORDS_BY_SOURCE[source]
        or (record_count is not None and observed_record_count != record_count)
    ):
        problems.append(f"{label}:enumeration:record-count")
    if enumeration.get("complete") is not True:
        problems.append(f"{label}:enumeration:complete")
    if enumeration.get("continuation_token") is not None:
        problems.append(f"{label}:enumeration:continuation-token")
    return sorted(set(problems))


def _record_fact(
    records: object,
    *,
    source: str,
    label: str,
) -> tuple[list[str], SourceFact | None]:
    if type(records) is not list:
        return [f"{label}:records"], None
    if len(records) > MAX_RECORDS_BY_SOURCE[source]:
        return [f"{label}:records-cardinality"], None
    if not records:
        return [], SourceFact(
            "EMPTY",
            None,
            None,
            None,
            None,
            hashlib.sha256(_canonical_json(records)).hexdigest(),
        )
    canonical_records = [_canonical_json(record) for record in records]
    if canonical_records != sorted(canonical_records):
        return [f"{label}:records-order"], None
    if len(canonical_records) != len(set(canonical_records)):
        return [f"{label}:records-duplicate"], None
    if len(records) > 1:
        problems: list[str] = []
        facts: list[SourceFact] = []
        for index, record in enumerate(records):
            record_problems, fact = _record_fact(
                [record],
                source=source,
                label=f"{label}:records:{index}",
            )
            problems.extend(record_problems)
            if fact is not None:
                facts.append(fact)
        if problems or len(facts) != len(records):
            return sorted(set(problems)), None
        semantic_facts = {
            (
                fact.kind,
                fact.attempt_id,
                fact.manifest_sha256,
                fact.terminal_cause,
                fact.proof_manifest_sha256,
            )
            for fact in facts
        }
        records_sha256 = hashlib.sha256(_canonical_json(records)).hexdigest()
        if len(semantic_facts) != 1:
            return [], SourceFact("CONFLICT", None, None, None, None, records_sha256)
        kind, attempt_id, manifest_sha256, terminal_cause, proof_sha256 = next(iter(semantic_facts))
        return [], SourceFact(
            kind,
            attempt_id,
            manifest_sha256,
            terminal_cause,
            proof_sha256,
            records_sha256,
        )
    record = records[0]
    problems = _field_set(record, RECORD_FIELDS[source], f"{label}:record")
    if type(record) is not dict:
        return problems, None
    problems.extend(_attempt_manifest_problems(record, f"{label}:record"))
    if source in {"launch_lock", "analytic_lock"}:
        if not _exact_int(record.get("owner_pid"), minimum=1):
            problems.append(f"{label}:record:owner-pid")
        if not _exact_int(record.get("owner_process_start_ticks")):
            problems.append(f"{label}:record:owner-process-start-ticks")
        fact = SourceFact(
            "ACTIVE",
            record.get("attempt_id"),
            record.get("manifest_sha256"),
            None,
            None,
            hashlib.sha256(_canonical_json(records)).hexdigest(),
        )
    elif source == "launcher_process":
        if not _exact_int(record.get("pid"), minimum=1):
            problems.append(f"{label}:record:pid")
        if not _exact_int(record.get("process_start_ticks")):
            problems.append(f"{label}:record:process-start-ticks")
        if not _sha256(record.get("executable_sha256")):
            problems.append(f"{label}:record:executable-sha256")
        fact = SourceFact(
            "ACTIVE",
            record.get("attempt_id"),
            record.get("manifest_sha256"),
            None,
            None,
            hashlib.sha256(_canonical_json(records)).hexdigest(),
        )
    elif source in {"mission_containers", "global_containers"}:
        container_id = record.get("container_id")
        if type(container_id) is not str or _RESOURCE_ID.fullmatch(container_id) is None:
            problems.append(f"{label}:record:container-id")
        if record.get("runtime_state") != "RUNNING":
            problems.append(f"{label}:record:runtime-state")
        fact = SourceFact(
            "ACTIVE",
            record.get("attempt_id"),
            record.get("manifest_sha256"),
            None,
            None,
            hashlib.sha256(_canonical_json(records)).hexdigest(),
        )
    elif source == "attempt_journal":
        journal_state = record.get("journal_state")
        if journal_state == "ACTIVE":
            if record.get("terminal_cause") is not None:
                problems.append(f"{label}:record:active-terminal-cause")
            if record.get("proof_manifest_sha256") is not None:
                problems.append(f"{label}:record:active-proof-manifest-sha256")
            fact = SourceFact(
                "ACTIVE",
                record.get("attempt_id"),
                record.get("manifest_sha256"),
                None,
                None,
                hashlib.sha256(_canonical_json(records)).hexdigest(),
            )
        else:
            terminal_problems, terminal_fact = _terminal_fact(
                record,
                state_field="journal_state",
                label=f"{label}:record",
            )
            problems.extend(terminal_problems)
            fact = terminal_fact
    elif source == "terminal_witness":
        terminal_problems, terminal_fact = _terminal_fact(
            record,
            state_field="terminal_state",
            label=f"{label}:record",
        )
        problems.extend(terminal_problems)
        fact = terminal_fact
    elif source == "proof_manifest":
        proof_problems, proof_fact = _proof_manifest_fact(record, f"{label}:record")
        problems.extend(proof_problems)
        fact = proof_fact
    else:
        provider_state = record.get("provider_state")
        cause = record.get("terminal_cause")
        proof_sha256 = record.get("proof_manifest_sha256")
        job_id = record.get("job_id")
        if type(job_id) is not str or _RESOURCE_ID.fullmatch(job_id) is None:
            problems.append(f"{label}:record:job-id")
        if provider_state == "RUNNING":
            if cause is not None:
                problems.append(f"{label}:record:running-terminal-cause")
            if proof_sha256 is not None:
                problems.append(f"{label}:record:running-proof-manifest-sha256")
            fact = SourceFact(
                "ACTIVE",
                record.get("attempt_id"),
                record.get("manifest_sha256"),
                None,
                None,
                hashlib.sha256(_canonical_json(records)).hexdigest(),
            )
        else:
            derived_state = _terminal_state_for_cause(cause)
            if derived_state is None:
                problems.append(f"{label}:record:terminal-cause")
            expected_provider_state = (
                PROVIDER_STATE_BY_CAUSE.get(cause) if type(cause) is str else None
            )
            if provider_state != expected_provider_state:
                problems.append(f"{label}:record:provider-state-cause-mapping")
            if not _sha256(proof_sha256):
                problems.append(f"{label}:record:proof-manifest-sha256")
            fact = (
                None
                if derived_state is None
                else SourceFact(
                    derived_state,
                    record.get("attempt_id"),
                    record.get("manifest_sha256"),
                    cause,
                    proof_sha256,
                    hashlib.sha256(_canonical_json(records)).hexdigest(),
                )
            )
    return sorted(set(problems)), fact if not problems else None


def _source_observation_problems(
    raw: bytes,
    *,
    source: str,
    query_sha256: str,
    challenge_nonce_sha256: str,
    host_identity_sha256: str,
    boot_id: str,
    capture_started_ns: int,
    capture_finished_ns: int,
    label: str,
) -> tuple[list[str], dict[str, Any] | None, SourceFact | None]:
    try:
        observation = _decode_json(raw, label=label, maximum=MAX_STREAM_BYTES)
    except LifecycleReceiptError as error:
        return [f"{label}:json:{error}"], None, None
    problems = _field_set(observation, SOURCE_OBSERVATION_FIELDS, label)
    if type(observation) is not dict:
        return problems, None, None
    if raw != _canonical_json(observation) + b"\n":
        problems.append(f"{label}:noncanonical-bytes")
    exact_values = (
        ("schema", observation.get("schema"), SOURCE_SCHEMA),
        ("source", observation.get("source"), source),
        ("query-sha256", observation.get("query_sha256"), query_sha256),
        (
            "challenge-nonce-sha256",
            observation.get("challenge_nonce_sha256"),
            challenge_nonce_sha256,
        ),
        (
            "host-identity-sha256",
            observation.get("host_identity_sha256"),
            host_identity_sha256,
        ),
        ("boot-id", observation.get("boot_id"), boot_id),
    )
    for field, observed, expected in exact_values:
        if observed != expected:
            problems.append(f"{label}:{field}")
    observed_ns = observation.get("observed_monotonic_ns")
    if (
        not _exact_int(observed_ns)
        or observed_ns <= capture_started_ns
        or observed_ns >= capture_finished_ns
    ):
        problems.append(f"{label}:observed-monotonic-ns")
    records = observation.get("records")
    problems.extend(
        _enumeration_problems(
            observation.get("enumeration"),
            source=source,
            record_count=len(records) if type(records) is list else None,
            label=label,
        )
    )
    record_problems, fact = _record_fact(
        records,
        source=source,
        label=label,
    )
    problems.extend(record_problems)
    if problems:
        return sorted(set(problems)), None, None
    return [], observation, fact


def _base_problems(receipt: object) -> list[str]:
    if type(receipt) is not dict:
        return ["receipt:not-object"]
    problems: list[str] = []
    if set(receipt) != ROOT_FIELDS:
        problems.append("receipt:field-set")
    if receipt.get("schema") != SCHEMA:
        problems.append("receipt:schema")

    mission = receipt.get("mission")
    problems.extend(_field_set(mission, MISSION_FIELDS, "mission"))
    if type(mission) is dict:
        if mission.get("iteration") != ITERATION or type(mission.get("iteration")) is not int:
            problems.append("mission:iteration")
        if mission.get("experiment") != EXPERIMENT:
            problems.append("mission:experiment")
        if not _commit(mission.get("source_commit")):
            problems.append("mission:source-commit")
        if not _sha256(mission.get("mission_state_sha256")):
            problems.append("mission:mission-state-sha256")
        manifest_sha256 = mission.get("manifest_sha256")
        if manifest_sha256 is not None and not _sha256(manifest_sha256):
            problems.append("mission:manifest-sha256")
        attempt_id = mission.get("attempt_id")
        if attempt_id is not None and (
            type(attempt_id) is not str or _ATTEMPT_ID.fullmatch(attempt_id) is None
        ):
            problems.append("mission:attempt-id")

    observer = receipt.get("observer")
    problems.extend(_field_set(observer, OBSERVER_FIELDS, "observer"))
    if type(observer) is dict:
        if not _commit(observer.get("control_source_commit")):
            problems.append("observer:control-source-commit")
        if observer.get("host") != EXPECTED_HOST:
            problems.append("observer:host")
        if observer.get("query_policy_sha256") != QUERY_POLICY_SHA256:
            problems.append("observer:query-policy-sha256")
        if not _sha256(observer.get("challenge_nonce_sha256")):
            problems.append("observer:challenge-nonce-sha256")
        initial_identity = observer.get("initial_identity")
        terminal_identity = observer.get("terminal_identity")
        problems.extend(_identity_problems(initial_identity, "observer:initial-identity"))
        problems.extend(_identity_problems(terminal_identity, "observer:terminal-identity"))
        if type(initial_identity) is dict and type(terminal_identity) is dict:
            if initial_identity != terminal_identity:
                problems.append("observer:identity-drift")
        utc_values = {
            field: _utc_datetime(observer.get(field))
            for field in ("started_at_utc", "finished_at_utc", "deadline_at_utc")
        }
        for field, value in utc_values.items():
            if value is None:
                problems.append(f"observer:{field.replace('_', '-')}")
        monotonic_values = {
            field: observer.get(field)
            for field in (
                "started_monotonic_ns",
                "finished_monotonic_ns",
                "deadline_monotonic_ns",
            )
        }
        for field, value in monotonic_values.items():
            if not _exact_int(value):
                problems.append(f"observer:{field.replace('_', '-')}")
        start_ns = monotonic_values["started_monotonic_ns"]
        finish_ns = monotonic_values["finished_monotonic_ns"]
        deadline_ns = monotonic_values["deadline_monotonic_ns"]
        if all(_exact_int(value) for value in (start_ns, finish_ns, deadline_ns)):
            if not (start_ns < finish_ns < deadline_ns):
                problems.append("observer:monotonic-order")
            else:
                if finish_ns - start_ns > MAX_OBSERVATION_DURATION_NS:
                    problems.append("observer:duration")
                if deadline_ns - finish_ns > MAX_CONSUMPTION_WINDOW_NS:
                    problems.append("observer:deadline-window")
        started_utc = utc_values["started_at_utc"]
        finished_utc = utc_values["finished_at_utc"]
        deadline_utc = utc_values["deadline_at_utc"]
        if all(value is not None for value in (started_utc, finished_utc, deadline_utc)):
            assert started_utc is not None and finished_utc is not None and deadline_utc is not None
            if not (started_utc < finished_utc < deadline_utc):
                problems.append("observer:utc-order")
            else:
                utc_duration = _nanoseconds((finished_utc - started_utc).total_seconds())
                utc_deadline = _nanoseconds((deadline_utc - finished_utc).total_seconds())
                if utc_duration > MAX_OBSERVATION_DURATION_NS:
                    problems.append("observer:utc-duration")
                if utc_deadline > MAX_CONSUMPTION_WINDOW_NS:
                    problems.append("observer:utc-deadline-window")
            if started_utc < finished_utc < deadline_utc and all(
                _exact_int(value) for value in (start_ns, finish_ns, deadline_ns)
            ):
                if abs(utc_duration - (finish_ns - start_ns)) > TIME_AGREEMENT_TOLERANCE_NS:
                    problems.append("observer:duration-clock-disagreement")
                if abs(utc_deadline - (deadline_ns - finish_ns)) > TIME_AGREEMENT_TOLERANCE_NS:
                    problems.append("observer:deadline-clock-disagreement")

    lease = receipt.get("lease")
    problems.extend(_field_set(lease, LEASE_FIELDS, "lease"))
    if type(lease) is dict:
        if not _uuid(lease.get("id")):
            problems.append("lease:id")
        if lease.get("path") != LEASE_PATH:
            problems.append("lease:path")
        owner_identity = lease.get("owner_identity")
        problems.extend(_identity_problems(owner_identity, "lease:owner-identity"))
        if type(observer) is dict and owner_identity != observer.get("initial_identity"):
            problems.append("lease:owner-identity-binding")
        acquired = _utc_datetime(lease.get("acquired_at_utc"))
        if acquired is None:
            problems.append("lease:acquired-at-utc")
        elif type(observer) is dict:
            started = _utc_datetime(observer.get("started_at_utc"))
            if started is not None and acquired > started:
                problems.append("lease:acquired-after-observation-start")
        initial_snapshot = lease.get("initial_snapshot")
        terminal_snapshot = lease.get("terminal_snapshot")
        problems.extend(_lease_snapshot_problems(initial_snapshot, "lease:initial-snapshot"))
        problems.extend(_lease_snapshot_problems(terminal_snapshot, "lease:terminal-snapshot"))
        if type(initial_snapshot) is dict and type(terminal_snapshot) is dict:
            if initial_snapshot != terminal_snapshot:
                problems.append("lease:snapshot-drift")

    sources = receipt.get("sources")
    if type(sources) is not dict:
        problems.append("sources:not-object")
    elif set(sources) != set(SOURCE_NAMES):
        problems.append("sources:field-set")
    if type(sources) is dict:
        round_windows: dict[str, list[tuple[str, int, int]]] = {
            "initial": [],
            "terminal": [],
        }
        for source in SOURCE_NAMES:
            pair = sources.get(source)
            problems.extend(_field_set(pair, SOURCE_PAIR_FIELDS, f"sources:{source}"))
            if type(pair) is dict:
                capture_windows: dict[str, tuple[int, int]] = {}
                for position in ("initial", "terminal"):
                    capture = pair.get(position)
                    capture_problems, _ = _capture_problems(
                        capture,
                        source,
                        f"sources:{source}:{position}",
                    )
                    problems.extend(capture_problems)
                    if type(capture) is dict:
                        capture_started = capture.get("started_monotonic_ns")
                        capture_finished = capture.get("finished_monotonic_ns")
                        if _exact_int(capture_started) and _exact_int(capture_finished):
                            capture_windows[position] = (capture_started, capture_finished)
                            round_windows[position].append(
                                (source, capture_started, capture_finished)
                            )
                            if type(observer) is dict:
                                observer_started = observer.get("started_monotonic_ns")
                                observer_finished = observer.get("finished_monotonic_ns")
                                if (
                                    _exact_int(observer_started)
                                    and _exact_int(observer_finished)
                                    and (
                                        capture_started < observer_started
                                        or capture_finished > observer_finished
                                    )
                                ):
                                    problems.append(
                                        f"sources:{source}:{position}:outside-observer-window"
                                    )
                if set(capture_windows) == {"initial", "terminal"}:
                    if capture_windows["initial"][1] >= capture_windows["terminal"][0]:
                        problems.append(f"sources:{source}:capture-order")
        for position, windows in round_windows.items():
            if len(windows) == len(SOURCE_NAMES):
                for index in range(1, len(windows)):
                    previous = windows[index - 1]
                    current = windows[index]
                    if previous[2] > current[1]:
                        problems.append(f"sources:{position}:global-capture-order")
        initial_windows = round_windows["initial"]
        terminal_windows = round_windows["terminal"]
        if len(initial_windows) == len(SOURCE_NAMES) and len(terminal_windows) == len(SOURCE_NAMES):
            dwell_ns = terminal_windows[0][1] - initial_windows[-1][2]
            if dwell_ns <= 0:
                problems.append("sources:global-round-separation")
            if dwell_ns < MIN_ROUND_DWELL_NS:
                problems.append("sources:minimum-round-dwell")

    verdict = receipt.get("verdict")
    if type(verdict) is not str or verdict not in VERDICTS:
        problems.append("receipt:verdict")
    for field in (
        "quiescence_evidence_complete",
        "launch_authorized",
        "relaunch_authorized",
    ):
        if type(receipt.get(field)) is not bool:
            problems.append(f"receipt:{field.replace('_', '-')}")
    receipt_problems = receipt.get("problems")
    if (
        type(receipt_problems) is not list
        or len(receipt_problems) > MAX_PROBLEMS
        or any(
            type(problem) is not str or _PROBLEM_CODE.fullmatch(problem) is None
            for problem in receipt_problems
        )
        or receipt_problems != sorted(set(receipt_problems))
    ):
        problems.append("receipt:problems")
    problem_count = receipt.get("problem_count")
    if not _exact_int(problem_count) or (
        type(receipt_problems) is list and problem_count != len(receipt_problems)
    ):
        problems.append("receipt:problem-count")
    checksum = receipt.get("receipt_payload_self_checksum_sha256")
    if not _sha256(checksum):
        problems.append("receipt:payload-self-checksum-sha256")
    else:
        try:
            expected_checksum = _payload_self_checksum(receipt)
        except (TypeError, ValueError, RecursionError, OverflowError):
            problems.append("receipt:payload-self-checksum-canonicalization")
        else:
            if checksum != expected_checksum:
                problems.append("receipt:payload-self-checksum-mismatch")
    return sorted(set(problems))


def _observations(
    receipt: Mapping[str, Any],
) -> tuple[list[str], dict[str, tuple[SourceFact | None, SourceFact | None]]]:
    problems: list[str] = []
    facts: dict[str, tuple[SourceFact | None, SourceFact | None]] = {}
    observer = receipt["observer"]
    identity = observer["initial_identity"]
    source_pairs = receipt["sources"]
    successful_digests: dict[str, list[str]] = {"initial": [], "terminal": []}
    for source in SOURCE_NAMES:
        parsed: list[SourceFact | None] = []
        for position in ("initial", "terminal"):
            capture = source_pairs[source][position]
            _, stdout = _capture_problems(
                capture,
                source,
                f"sources:{source}:{position}",
            )
            if stdout is None:
                parsed.append(None)
                continue
            observation_problems, observation, fact = _source_observation_problems(
                stdout,
                source=source,
                query_sha256=QUERY_SHA256[source],
                challenge_nonce_sha256=observer["challenge_nonce_sha256"],
                host_identity_sha256=identity["host_identity_sha256"],
                boot_id=identity["boot_id"],
                capture_started_ns=capture["started_monotonic_ns"],
                capture_finished_ns=capture["finished_monotonic_ns"],
                label=f"sources:{source}:{position}:observation",
            )
            problems.extend(observation_problems)
            parsed.append(fact)
            if observation is not None:
                successful_digests[position].append(capture["stdout_sha256"])
        facts[source] = (parsed[0], parsed[1])
    if len(set(QUERY_SHA256.values())) != len(SOURCE_NAMES):
        problems.append("sources:query-domain-collision")
    for position, digests in successful_digests.items():
        if len(digests) != len(set(digests)):
            problems.append(f"sources:{position}:observation-domain-collision")
    return sorted(set(problems)), facts


def _reduce(receipt: Mapping[str, Any]) -> tuple[str, list[str]]:
    if _base_problems(receipt):
        return "UNKNOWN", []
    receipt_problems = receipt.get("problems")
    if receipt_problems:
        return "UNKNOWN", [f"receipt-reported:{problem}" for problem in receipt_problems]
    observation_problems, facts_by_source = _observations(receipt)
    if observation_problems:
        return "UNKNOWN", observation_problems
    available = [fact for pair in facts_by_source.values() for fact in pair if fact is not None]
    if not available:
        return "UNKNOWN", []
    if any(
        initial is not None and terminal is not None and initial != terminal
        for initial, terminal in facts_by_source.values()
    ):
        return "INCONSISTENT", []
    stable = [
        initial
        for initial, terminal in facts_by_source.values()
        if initial is not None and terminal is not None and initial == terminal
    ]
    if len(stable) != len(SOURCE_NAMES):
        return "UNKNOWN", []
    if any(fact.kind == "CONFLICT" for fact in stable):
        return "INCONSISTENT", []
    active = [fact for fact in stable if fact.kind == "ACTIVE"]
    terminal = [fact for fact in stable if fact.kind.startswith("TERMINATED_")]
    if active and terminal:
        return "INCONSISTENT", []
    mission = receipt["mission"]
    if active:
        active_bindings = {(fact.attempt_id, fact.manifest_sha256) for fact in active}
        if len(active_bindings) != 1:
            return "INCONSISTENT", []
        attempt_id, manifest_sha256 = next(iter(active_bindings))
        if (
            mission.get("attempt_id") != attempt_id
            or mission.get("manifest_sha256") != manifest_sha256
        ):
            return "INCONSISTENT", []
        return "RUNNING", []
    if terminal:
        required_terminal_sources = {
            "attempt_journal",
            "terminal_witness",
            "proof_manifest",
            "provider_job_registry",
        }
        observed_terminal_sources = {
            source
            for source, pair in facts_by_source.items()
            if pair[0] is not None and pair[0].kind.startswith("TERMINATED_")
        }
        if observed_terminal_sources != required_terminal_sources:
            return "UNKNOWN", []
        terminal_bindings = {
            (
                fact.kind,
                fact.attempt_id,
                fact.manifest_sha256,
                fact.terminal_cause,
                fact.proof_manifest_sha256,
            )
            for fact in terminal
        }
        if len(terminal_bindings) != 1:
            return "INCONSISTENT", []
        terminal_state, attempt_id, manifest_sha256, _, _ = next(iter(terminal_bindings))
        if (
            mission.get("attempt_id") != attempt_id
            or mission.get("manifest_sha256") != manifest_sha256
        ):
            return "INCONSISTENT", []
        if any(
            pair[0] is not None
            and source not in required_terminal_sources
            and pair[0].kind != "EMPTY"
            for source, pair in facts_by_source.items()
        ):
            return "INCONSISTENT", []
        return terminal_state, []
    if all(fact.kind == "EMPTY" for fact in stable):
        if mission.get("attempt_id") is not None or mission.get("manifest_sha256") is not None:
            return "INCONSISTENT", []
        return "QUIESCENCE_EVIDENCE_COMPLETE", []
    return "UNKNOWN", []


def parse_validate_reduce(
    raw: bytes,
    *,
    expected_receipt_sha256: str,
    expected_control_source_commit: str,
    expected_source_commit: str,
    expected_mission_state_sha256: str,
    expected_host_identity_sha256: str,
    expected_challenge_nonce_sha256: str,
    expected_boot_id: str,
    expected_observer_executable_sha256: str,
    expected_observer_build_sha256: str,
    expected_cgroup_policy_sha256: str,
    expected_lease_id: str,
    trusted_current_monotonic_ns: int,
    expected_deadline_monotonic_ns: int,
    expected_host: str = EXPECTED_HOST,
) -> ValidationResult:
    """Strict-decode, bind, validate, and reduce one raw receipt.

    The detached expected receipt digest and source bindings must come from an independently
    accepted manifest or performing controller.  A green result is evidence classification only;
    it is not a reusable capability or permission.
    """

    if type(raw) is not bytes:
        raise LifecycleReceiptError("receipt input must be bytes")
    receipt_sha256 = hashlib.sha256(raw).hexdigest()
    if not _sha256(expected_receipt_sha256):
        raise LifecycleReceiptError("expected receipt SHA-256 is malformed")
    for name, value in (
        ("control source commit", expected_control_source_commit),
        ("source commit", expected_source_commit),
    ):
        if not _commit(value):
            raise LifecycleReceiptError(f"expected {name} is malformed")
    for name, value in (
        ("mission-state SHA-256", expected_mission_state_sha256),
        ("host-identity SHA-256", expected_host_identity_sha256),
        ("challenge-nonce SHA-256", expected_challenge_nonce_sha256),
        ("observer-executable SHA-256", expected_observer_executable_sha256),
        ("observer-build SHA-256", expected_observer_build_sha256),
        ("cgroup-policy SHA-256", expected_cgroup_policy_sha256),
    ):
        if not _sha256(value):
            raise LifecycleReceiptError(f"expected {name} is malformed")
    if not _uuid(expected_boot_id):
        raise LifecycleReceiptError("expected boot ID is malformed")
    if not _uuid(expected_lease_id):
        raise LifecycleReceiptError("expected lease ID is malformed")
    if not _exact_int(trusted_current_monotonic_ns):
        raise LifecycleReceiptError("trusted current monotonic time is malformed")
    if not _exact_int(expected_deadline_monotonic_ns):
        raise LifecycleReceiptError("expected monotonic deadline is malformed")
    if type(expected_host) is not str or not expected_host:
        raise LifecycleReceiptError("expected host is malformed")
    receipt = _decode_json(raw, label="receipt", maximum=MAX_RECEIPT_BYTES)
    if type(receipt) is not dict:
        raise LifecycleReceiptError("receipt root must be an object")
    problems = _base_problems(receipt)
    if raw != _canonical_json(receipt) + b"\n":
        problems.append("receipt:noncanonical-bytes")
    if receipt_sha256 != expected_receipt_sha256:
        problems.append("binding:receipt-sha256")
    mission = receipt.get("mission")
    observer = receipt.get("observer")
    if type(mission) is dict and type(observer) is dict:
        identity = observer.get("initial_identity")
        bindings = (
            (
                "binding:control-source-commit",
                observer.get("control_source_commit"),
                expected_control_source_commit,
            ),
            ("binding:source-commit", mission.get("source_commit"), expected_source_commit),
            (
                "binding:mission-state-sha256",
                mission.get("mission_state_sha256"),
                expected_mission_state_sha256,
            ),
            ("binding:host", observer.get("host"), expected_host),
            (
                "binding:host-identity-sha256",
                identity.get("host_identity_sha256") if type(identity) is dict else None,
                expected_host_identity_sha256,
            ),
            (
                "binding:challenge-nonce-sha256",
                observer.get("challenge_nonce_sha256"),
                expected_challenge_nonce_sha256,
            ),
            (
                "binding:boot-id",
                identity.get("boot_id") if type(identity) is dict else None,
                expected_boot_id,
            ),
            (
                "binding:observer-executable-sha256",
                identity.get("executable_sha256") if type(identity) is dict else None,
                expected_observer_executable_sha256,
            ),
            (
                "binding:observer-build-sha256",
                identity.get("build_sha256") if type(identity) is dict else None,
                expected_observer_build_sha256,
            ),
            (
                "binding:cgroup-policy-sha256",
                identity.get("cgroup_policy_sha256") if type(identity) is dict else None,
                expected_cgroup_policy_sha256,
            ),
            (
                "binding:deadline-monotonic-ns",
                observer.get("deadline_monotonic_ns"),
                expected_deadline_monotonic_ns,
            ),
        )
        for problem, observed, expected in bindings:
            if observed != expected:
                problems.append(problem)
    lease = receipt.get("lease")
    if type(lease) is dict and lease.get("id") != expected_lease_id:
        problems.append("binding:lease-id")
    if trusted_current_monotonic_ns > expected_deadline_monotonic_ns:
        problems.append("binding:trusted-current-after-deadline")
    if type(observer) is dict:
        finished_ns = observer.get("finished_monotonic_ns")
        if _exact_int(finished_ns) and trusted_current_monotonic_ns < finished_ns:
            problems.append("binding:trusted-current-before-capture-finished")
    reduced, reduction_problems = _reduce(receipt)
    problems.extend(reduction_problems)
    if problems:
        reduced = "UNKNOWN"
    if receipt.get("verdict") != reduced:
        problems.append(f"receipt:verdict-mismatch:{receipt.get('verdict')!r}!={reduced!r}")
        reduced = "UNKNOWN"
    expected_quiescence = reduced == "QUIESCENCE_EVIDENCE_COMPLETE"
    if receipt.get("quiescence_evidence_complete") is not expected_quiescence:
        problems.append("receipt:quiescence-evidence-complete-mismatch")
    if receipt.get("launch_authorized") is not False:
        problems.append("receipt:launch-authorized")
    if receipt.get("relaunch_authorized") is not False:
        problems.append("receipt:relaunch-authorized")
    unique_problems = tuple(sorted(set(problems)))
    if unique_problems:
        reduced = "UNKNOWN"
        expected_quiescence = False
    return ValidationResult(
        problems=unique_problems,
        verdict=reduced,
        quiescence_evidence_complete=not unique_problems and expected_quiescence,
        receipt_sha256=receipt_sha256,
    )
