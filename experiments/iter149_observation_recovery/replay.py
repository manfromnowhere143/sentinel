"""Independent trace checker. Deliberately imports no production recovery code."""

import hashlib
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parsed(data, limit):
    if len(data) > limit:
        raise ValueError("oversize")
    value = json.loads(data)
    # Canonical roundtrip also rejects duplicate keys and whitespace variants.
    if canonical(value) != data:
        raise ValueError("encoding")
    return value


def observed(event, binding, revision, previous):
    if event["error"] is not None or event["end"] - event["start"] > event["timeout"]:
        return "observation_unavailable", "transport_or_timeout", revision, previous
    try:
        data = parsed(bytes.fromhex(event["raw_hex"]), 8192)
        if type(data) is not dict or set(data) != {
            "binding",
            "request",
            "revision",
            "state",
            "artifacts",
        }:
            raise ValueError("fields")
        candidate = data["binding"]
        if type(candidate) is not dict or set(candidate) != set(binding):
            raise ValueError("binding")
        for key, value in candidate.items():
            if key == "pair":
                if type(value) is not int or value < 0:
                    raise ValueError("pair")
            elif type(value) is not str or not 1 <= len(value) <= 256:
                raise ValueError("value")
            elif key.endswith("sha256") and (
                len(value) != 64 or set(value) - set("0123456789abcdef")
            ):
                raise ValueError("hash")
        if candidate != binding:
            return "identity_mismatch", "binding", revision, previous
        if data["request"] != event["request"]:
            raise ValueError("request")
        current = data["revision"]
        if type(current) is not int or current < 0 or current < revision:
            raise ValueError("revision")
        snapshot = {key: value for key, value in data.items() if key != "request"}
        identity = sha(canonical(snapshot))
        if current == revision and identity != previous:
            raise ValueError("conflict")
        states = {
            "running": "worker_running",
            "partial": "partial_evidence",
            "failed": "worker_failed",
            "complete": "worker_complete",
        }
        state = states[data["state"]]
        hashes = data["artifacts"]
        names = {"worker", "summary", "inventory", "raw"}
        if type(hashes) is not dict or set(hashes) - names:
            raise ValueError("artifacts")
        if any(
            type(v) is not str or len(v) != 64 or set(v) - set("0123456789abcdef")
            for v in hashes.values()
        ):
            raise ValueError("artifact_hashes")
        if state == "worker_complete":
            valid = set(hashes) == names and set(event["blobs_hex"]) == names
            content = {}
            try:
                for name, encoded in event["blobs_hex"].items():
                    raw = bytes.fromhex(encoded)
                    content[name] = raw
                    valid &= len(raw) <= 65536 and sha(raw) == hashes[name]
                    if name != "raw":
                        record = parsed(raw, 65536)
                        valid &= record.get("binding_sha256") == sha(canonical(binding))
                        valid &= (
                            record.get("status")
                            == {
                                "worker": "completed",
                                "summary": "complete",
                                "inventory": "sealed",
                            }[name]
                        )
                        if name == "worker":
                            valid &= type(record.get("returncode")) is int
                            valid &= record.get("returncode") == 0
                index = parsed(content["inventory"], 65536)
                valid &= canonical(index.get("files")) == canonical(
                    {
                        name: {"sha256": sha(content[name]), "bytes": len(content[name])}
                        for name in ("raw", "worker", "summary")
                    }
                )
            except (ValueError, KeyError, TypeError, AttributeError):
                valid = False
            if not valid:
                return "partial_evidence", "terminal_artifacts", current, identity
        return state, "snapshot", current, identity
    except (ValueError, KeyError, TypeError, UnicodeError):
        return "observation_unavailable", "invalid_response", revision, previous


def check(trace):
    """Raise on an invalid trace, including incorrect claims or resource accounting."""
    cfg, binding = trace["limits"], trace["binding"]
    if set(binding) != {
        "vm_id",
        "vm_start",
        "source_sha256",
        "plan_sha256",
        "pair",
        "initialization_sha256",
        "host_boot",
        "host_deadline_id",
    }:
        raise ValueError("binding")
    values = [
        trace["started"],
        trace["finished"],
        cfg["deadline"],
        cfg["read_timeout"],
        cfg["poll_seconds"],
        *cfg["backoff"],
    ]
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("clock_or_limits")
    if (
        not cfg["backoff"]
        or min(cfg["read_timeout"], cfg["poll_seconds"], cfg["deadline"], *cfg["backoff"]) <= 0
    ):
        raise ValueError("limits")
    for key in ("max_reads", "max_unavailable"):
        if type(cfg[key]) is not int or not 1 <= cfg[key] <= 1000:
            raise ValueError("limits")
    events = trace["events"]
    if len(events) > cfg["max_reads"]:
        raise ValueError("reads")
    earliest = trace["started"]
    revision, snapshot, misses = -1, None, 0
    reason = None
    for i, event in enumerate(events):
        if reason is not None:
            raise ValueError("observation_after_stop")
        start, end = event["start"], event["end"]
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end)):
            raise ValueError("time")
        if start < earliest or start >= cfg["deadline"] or end < start:
            raise ValueError("time_order")
        if (
            type(event["attempt"]) is not int
            or event["attempt"] != i
            or event["request"] != f"{trace['session']}/{i}"
        ):
            raise ValueError("request_order")
        if event["timeout"] != min(cfg["read_timeout"], cfg["deadline"] - start):
            raise ValueError("timeout_extension")
        if end >= cfg["deadline"]:
            state, why = "observation_unavailable", "transport_or_timeout"
        else:
            state, why, revision, snapshot = observed(event, binding, revision, snapshot)
        if (event["state"], event["reason"]) != (state, why):
            raise ValueError("classification")
        if end >= cfg["deadline"]:
            reason = "deadline"
        elif state in {"worker_complete", "worker_failed", "identity_mismatch"}:
            reason = state
        elif state == "observation_unavailable":
            misses += 1
            if misses >= cfg["max_unavailable"]:
                reason = "unavailable_limit"
        else:
            misses = 0
        delay = (
            cfg["backoff"][min(misses - 1, len(cfg["backoff"]) - 1)]
            if misses
            else cfg["poll_seconds"]
        )
        earliest = end + min(delay, max(0.0, cfg["deadline"] - end))
    finish = trace["finished"]
    if finish < (events[-1]["end"] if events else trace["started"]):
        raise ValueError("finish")
    if reason is None:
        if len(events) == cfg["max_reads"]:
            reason = "read_limit"
        elif finish >= cfg["deadline"]:
            reason = "deadline"
        else:
            raise ValueError("premature_stop")
    if trace["reason"] != reason or trace["worker_complete"] is not (reason == "worker_complete"):
        raise ValueError("final_claim")
    if (
        trace["next_action"] != "reconcile_owned_closure"
        or trace["scientific_admission"] is not False
    ):
        raise ValueError("unauthorized_action")
    return {"status": "supported", "observations": len(events), "reason": reason}
