"""Read-only reconciliation for already initialized work.

Adapters must bound reads by the supplied timeout and independently enforce host expiry.
This module cannot launch, restart, or extend a worker. Cloud adapters are not qualified here.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math

BINDING_KEYS = {
    "vm_id",
    "vm_start",
    "source_sha256",
    "plan_sha256",
    "pair",
    "initialization_sha256",
    "host_boot",
    "host_deadline_id",
}
ARTIFACTS = {"worker", "summary", "inventory", "raw"}


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw, limit=8192):
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise ValueError("size_or_type")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite_json")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if encode(value) != raw:
        raise ValueError("noncanonical_json")
    return value


def validate_binding(binding):
    if not isinstance(binding, dict) or set(binding) != BINDING_KEYS:
        raise ValueError("binding_fields")
    for key, value in binding.items():
        if key == "pair":
            if type(value) is not int or value < 0:
                raise ValueError("pair")
        elif not isinstance(value, str) or not value or len(value) > 256:
            raise ValueError("binding_value")
        elif key.endswith("sha256") and (
            len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("binding_digest")


@dataclass(frozen=True)
class Limits:
    deadline: float
    max_reads: int = 12
    max_unavailable: int = 4
    read_timeout: float = 2.0
    poll_seconds: float = 2.0
    backoff: tuple = (1.0, 2.0, 4.0)

    def validate(self):
        for value in (self.deadline, self.read_timeout, self.poll_seconds, *self.backoff):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("finite_positive_limits")
        for value in (self.max_reads, self.max_unavailable):
            if type(value) is not int or not 1 <= value <= 1000:
                raise ValueError("finite_read_limits")
        if not self.backoff:
            raise ValueError("empty_backoff")


def classify(raw, blobs, request, binding, revision, snapshot_digest):
    """Return (state, reason, accepted revision, digest); never infer missing success."""
    try:
        row = decode(raw)
        if not isinstance(row, dict) or set(row) != {
            "binding",
            "request",
            "revision",
            "state",
            "artifacts",
        }:
            raise ValueError("response_fields")
        validate_binding(row["binding"])
        if row["binding"] != binding:
            return "identity_mismatch", "binding", revision, snapshot_digest
        if row["request"] != request:
            raise ValueError("request")
        rev = row["revision"]
        if type(rev) is not int or rev < 0 or rev < revision:
            raise ValueError("stale_revision")
        snapshot = {key: value for key, value in row.items() if key != "request"}
        sha = digest(encode(snapshot))
        if rev == revision and sha != snapshot_digest:
            raise ValueError("conflicting_revision")
        state = row["state"]
        if state not in {"running", "failed", "complete", "partial"}:
            raise ValueError("state")
        hashes = row["artifacts"]
        if not isinstance(hashes, dict) or set(hashes) - ARTIFACTS:
            raise ValueError("artifact_fields")
        for value in hashes.values():
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError("artifact_digest")
        if state == "complete":
            try:
                if set(hashes) != ARTIFACTS or set(blobs) != ARTIFACTS:
                    raise ValueError("missing_artifacts")
                expected_status = {
                    "worker": "completed",
                    "summary": "complete",
                    "inventory": "sealed",
                }
                for name in sorted(ARTIFACTS):
                    data = blobs[name]
                    if not isinstance(data, bytes) or len(data) > 65536:
                        raise ValueError("artifact_size")
                    if digest(data) != hashes[name]:
                        raise ValueError("artifact_content")
                    if name == "raw":
                        continue
                    artifact = decode(data, 65536)
                    if artifact.get("binding_sha256") != digest(encode(binding)):
                        raise ValueError("artifact_binding")
                    if artifact.get("status") != expected_status[name]:
                        raise ValueError("artifact_status")
                    if name == "worker" and (
                        type(artifact.get("returncode")) is not int or artifact["returncode"] != 0
                    ):
                        raise ValueError("worker_returncode")
                inventory = decode(blobs["inventory"], 65536)
                expected_files = {
                    name: {"sha256": digest(blobs[name]), "bytes": len(blobs[name])}
                    for name in ("raw", "worker", "summary")
                }
                if encode(inventory.get("files")) != encode(expected_files):
                    raise ValueError("inventory")
            except (ValueError, TypeError, AttributeError):
                return "partial_evidence", "terminal_artifacts", rev, sha
        labels = {
            "running": "worker_running",
            "failed": "worker_failed",
            "complete": "worker_complete",
            "partial": "partial_evidence",
        }
        return labels[state], "snapshot", rev, sha
    except (ValueError, TypeError, KeyError, UnicodeError):
        return "observation_unavailable", "invalid_response", revision, snapshot_digest


def reconcile(binding, limits, session, observe, clock, sleep):
    """Adapters return (raw bytes, small artifact bytes); transport errors raise OSError.

    Every observation is recorded before a decision. Unexpected adapter bugs propagate;
    the independent host deadline must still close owned work. No automatic next-pair action.
    """
    validate_binding(binding)
    limits.validate()
    if not isinstance(session, str) or not session or len(session) > 128:
        raise ValueError("session")
    trace = {
        "binding": binding.copy(),
        "limits": asdict(limits),
        "session": session,
        "events": [],
        "started": clock(),
    }
    previous_time = trace["started"]
    if not math.isfinite(previous_time) or previous_time < 0:
        raise ValueError("clock")
    revision, snapshot, unavailable = -1, None, 0
    reason = "read_limit"
    for attempt in range(limits.max_reads):
        start = clock()
        if not math.isfinite(start) or start < previous_time:
            reason = "clock_invalid"
            break
        if start >= limits.deadline:
            reason = "deadline"
            break
        timeout = min(limits.read_timeout, limits.deadline - start)
        request = f"{session}/{attempt}"
        raw, blobs, error = b"", {}, None
        try:
            raw, blobs = observe(request, timeout)
        except (OSError, TimeoutError) as exc:
            error = type(exc).__name__
        end = clock()
        if not math.isfinite(end) or end < start:
            # This is an adapter/clock fault, not evidence about the worker.
            raise ValueError("clock")
        if error or end - start > timeout or end >= limits.deadline:
            state, why = "observation_unavailable", "transport_or_timeout"
        else:
            state, why, revision, snapshot = classify(
                raw, blobs, request, binding, revision, snapshot
            )
        trace["events"].append(
            {
                "attempt": attempt,
                "request": request,
                "start": start,
                "end": end,
                "timeout": timeout,
                "raw_hex": raw.hex(),
                "blobs_hex": {k: v.hex() for k, v in blobs.items()},
                "error": error,
                "state": state,
                "reason": why,
            }
        )
        previous_time = end
        if end >= limits.deadline:
            reason = "deadline"
            break
        if state in {"worker_complete", "worker_failed", "identity_mismatch"}:
            reason = state
            break
        if state == "observation_unavailable":
            unavailable += 1
            if unavailable >= limits.max_unavailable:
                reason = "unavailable_limit"
                break
            delay = limits.backoff[min(unavailable - 1, len(limits.backoff) - 1)]
        else:
            unavailable = 0
            delay = limits.poll_seconds
        if attempt + 1 < limits.max_reads:
            sleep(min(delay, max(0.0, limits.deadline - end)))
    trace.update(
        reason=reason,
        finished=clock(),
        worker_complete=reason == "worker_complete",
        next_action="reconcile_owned_closure",
        scientific_admission=False,
    )
    return trace


def closure(binding, readback):
    """A stop command alone is not termination. This accepts exact owned readback only."""
    validate_binding(binding)
    if not isinstance(readback, dict) or readback.get("binding") != binding:
        return "unknown"
    try:
        validate_binding(readback["binding"])
    except ValueError:
        return "unknown"
    return "verified" if readback.get("status") == "terminated" else "unknown"
