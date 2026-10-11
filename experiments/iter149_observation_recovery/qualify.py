"""Deterministic fault qualification and bounded state-sequence exploration."""

import argparse
from copy import deepcopy
import itertools
import json
from pathlib import Path

from .recovery import Limits, digest, encode, reconcile
from .replay import check

BINDING = {
    "vm_id": "fixture-vm",
    "vm_start": "fixture-start",
    "source_sha256": "1" * 64,
    "plan_sha256": "2" * 64,
    "pair": 0,
    "initialization_sha256": "3" * 64,
    "host_boot": "fixture-boot",
    "host_deadline_id": "fixture-deadline",
}


class Clock:
    def __init__(self):
        self.time = 0.0

    def __call__(self):
        return self.time

    def sleep(self, seconds):
        self.time += seconds


def terminal(binding):
    bound = digest(encode(binding))
    blobs = {
        "raw": b'{"event":"fixture"}\n',
        "worker": encode({"binding_sha256": bound, "status": "completed", "returncode": 0}),
        "summary": encode({"binding_sha256": bound, "status": "complete"}),
    }
    blobs["inventory"] = encode(
        {
            "binding_sha256": bound,
            "status": "sealed",
            "files": {
                name: {"sha256": digest(data), "bytes": len(data)} for name, data in blobs.items()
            },
        }
    )
    return blobs


def run(sequence, limits=None):
    clock = Clock()
    prior = [b""]
    calls = [0]

    def observe(request, timeout):
        i = calls[0]
        calls[0] += 1
        kind = sequence[min(i, len(sequence) - 1)]
        if kind == "disconnect":
            raise OSError("injected transport loss")
        clock.sleep(timeout + 0.25 if kind == "delay" else 0.125)
        if kind == "duplicate":
            return prior[0], {}
        if kind == "malformed":
            return b"not JSON", {}
        if kind == "partial_write":
            return b'{"state":', {}
        if kind == "oversize":
            return b"x" * 8193, {}
        state = {"running": "running", "crash": "failed", "partial": "partial"}.get(
            kind, "complete"
        )
        row = {
            "binding": deepcopy(BINDING),
            "request": request,
            "revision": i + 1,
            "state": state,
            "artifacts": {},
        }
        blobs = terminal(BINDING) if state == "complete" else {}
        row["artifacts"] = {name: digest(data) for name, data in blobs.items()}
        if kind.startswith("wrong_"):
            field = kind.removeprefix("wrong_")
            row["binding"][field] = (
                1
                if field == "pair"
                else ("4" * 64 if field.endswith("sha256") else "wrong-identity")
            )
        if kind == "stale":
            row["revision"] = 0
        if kind == "conflict":
            row.update(revision=i, state="partial", artifacts={})
            blobs = {}
        if kind == "old_request":
            row["request"] = "previous-session/0"
        if kind == "missing_artifact":
            del blobs["summary"]
        if kind == "corrupt_artifact":
            blobs["raw"] += b"corrupt"
        if kind == "false_inventory":
            blobs["raw"] += b"changed"
            row["artifacts"]["raw"] = digest(blobs["raw"])
        if kind == "failed_terminal":
            worker = json.loads(blobs["worker"])
            worker["returncode"] = 7
            blobs["worker"] = encode(worker)
            row["artifacts"]["worker"] = digest(blobs["worker"])
        raw = encode(row)
        prior[0] = raw
        return raw, blobs

    trace = reconcile(
        BINDING, limits or Limits(deadline=30), "qualification", observe, clock, clock.sleep
    )
    check(trace)
    return trace


CASES = {
    "normal_completion": (["running", "complete"], "worker_complete"),
    "temporary_disconnection": (["disconnect", "running", "complete"], "worker_complete"),
    "completion_during_disconnection": (["running", "disconnect", "complete"], "worker_complete"),
    "permanent_disconnection": (["disconnect"], "unavailable_limit"),
    "delayed_response": (["delay", "complete"], "worker_complete"),
    "duplicate_reply": (["running", "duplicate", "complete"], "worker_complete"),
    "stale_revision": (["running", "stale", "complete"], "worker_complete"),
    "conflicting_revision": (["running", "conflict", "complete"], "worker_complete"),
    "old_request": (["old_request", "complete"], "worker_complete"),
    "malformed_reply": (["malformed", "complete"], "worker_complete"),
    "oversize_reply": (["oversize", "complete"], "worker_complete"),
    "partial_write": (["partial_write", "complete"], "worker_complete"),
    "worker_crash": (["running", "crash"], "worker_failed"),
    "missing_terminal_artifact": (["missing_artifact", "complete"], "worker_complete"),
    "corrupt_terminal_artifact": (["corrupt_artifact", "complete"], "worker_complete"),
    "false_inventory": (["false_inventory", "complete"], "worker_complete"),
    "failed_terminal": (["failed_terminal", "crash"], "worker_failed"),
    "partial_evidence": (["partial", "complete"], "worker_complete"),
    "partial_never_completes": (["partial"], "read_limit"),
    "second_outage": (["disconnect", "running", "disconnect", "complete"], "worker_complete"),
    "budget_exhaustion": (["running"], "deadline"),
    "read_exhaustion": (["running"], "read_limit"),
}
for field in BINDING:
    CASES["wrong_" + field] = (["wrong_" + field], "identity_mismatch")


def qualify(output):
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name, (sequence, expected) in CASES.items():
        limits = Limits(deadline=5) if name == "budget_exhaustion" else Limits(deadline=30)
        trace = run(sequence, limits)
        if trace["reason"] != expected:
            raise ValueError(f"{name}: expected {expected}, got {trace['reason']}")
        (output / (name + ".json")).write_bytes(encode(trace) + b"\n")
        results.append({"case": name, "reason": expected, "trace_sha256": digest(encode(trace))})
    # Every length-four sequence over six faults/states, fixed before execution.
    alphabet = ("disconnect", "running", "partial", "complete", "crash", "malformed")
    exhaustive = []
    for sequence in itertools.product(alphabet, repeat=4):
        trace = run(sequence)
        if len(trace["events"]) > 12 or trace["finished"] > 30:
            raise ValueError("bound")
        exhaustive.append(
            {"sequence": sequence, "trace_sha256": digest(encode(trace)), "reason": trace["reason"]}
        )
    # Corrupt retained traces so checker correctness isn't inferred from agreement alone.
    base = run(["running", "complete"])
    corruptions = {}
    for name in (
        "false_success",
        "wrong_classification",
        "timeout_extension",
        "extra_read",
        "negative_clock",
        "missing_artifact",
        "scientific_admission",
        "restart_action",
        "changed_binding",
        "wrong_reason",
        "budget_extension",
        "premature_stop",
    ):
        bad = deepcopy(base)
        if name == "false_success":
            bad["worker_complete"] = False
        elif name == "wrong_classification":
            bad["events"][0]["state"] = "worker_complete"
        elif name == "timeout_extension":
            bad["events"][0]["timeout"] += 1
        elif name == "extra_read":
            bad["events"].append(deepcopy(bad["events"][-1]))
        elif name == "negative_clock":
            bad["events"][0]["end"] = -1
        elif name == "missing_artifact":
            bad["events"][-1]["blobs_hex"].pop("summary")
        elif name == "scientific_admission":
            bad["scientific_admission"] = True
        elif name == "restart_action":
            bad["next_action"] = "restart"
        elif name == "changed_binding":
            bad["binding"]["vm_start"] = "new-start"
        elif name == "wrong_reason":
            bad["reason"] = "deadline"
        elif name == "budget_extension":
            bad["limits"]["deadline"] = 0.1
        elif name == "premature_stop":
            bad["events"] = bad["events"][:1]
        try:
            check(bad)
        except ValueError as exc:
            corruptions[name] = str(exc)
        else:
            raise ValueError(f"checker accepted {name}")
        (output / ("known_bad_" + name + ".json")).write_bytes(encode(bad) + b"\n")
    (output / "exhaustive.json").write_bytes(encode(exhaustive) + b"\n")
    report = {
        "status": "supported",
        "scope": "deterministic_local_control",
        "named_cases": results,
        "exhaustive_sequences": len(exhaustive),
        "checker_known_bads": corruptions,
        "cloud_qualified": False,
        "scientific_outcomes": 0,
    }
    (output / "qualification.json").write_bytes(encode(report) + b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = qualify(args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "named_cases"}, indent=2))
