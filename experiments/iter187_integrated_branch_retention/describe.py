"""Retrospective chronology only; no new controls, queries or causal attribution."""

from collections import Counter
import json
from pathlib import Path

from .common import BASE, read, write, require


def describe(root):
    admitted = json.loads(read(root, BASE / "proof/admission.json"))
    rows = []
    for result in admitted["records"]:
        name = result["case"]
        events = [
            json.loads(v)
            for v in read(root, BASE / f"proof/search_raw/{name}/events.jsonl").splitlines()
        ]
        previous = [
            json.loads(v)
            for v in read(
                root, f"experiments/iter183_timing_eligibility/proof/search_raw/{name}/events.jsonl"
            ).splitlines()
        ]
        parents, origins, requests, work, extras = {}, {}, {}, Counter(), []
        for event in events:
            if event["kind"] == "native_event":
                n = event["event"]
                if n["kind"] in (0, 1, 2):
                    parents[n["node"]] = n
                    origins[n["node"]] = n["kind"] == 2 or origins.get(n["parent"], False)
                    if n["kind"] == 2:
                        extras.append(
                            dict(call=n["token"] // 2, node=n["node"], frame=n["state"][5])
                        )
            elif event["kind"] == "branch_choice":
                requests[event["call"]] = event["parent"]
        connections = [e for e in events if e["kind"] == "connection"]
        for c in connections:
            work["extra_ancestry" if origins[requests[c["call"]]] else "primary_only_ancestry"] += (
                c["result"]["attempts"] if c["result"] else 0
            )
        require(
            sum(work.values()) == result["attempts"] and len(extras) == result["registered_extra"],
            "diagnostic_accounting",
        )
        reference = [e for e in previous if e["kind"] == "connection"]
        divergence = next(
            (
                c["call"]
                for c, p in zip(connections, reference)
                if (c["before"], c["target"]) != (p["before"], p["target"])
            ),
            None,
        )

        def reasons(log):
            return dict(
                Counter(
                    next(
                        (r["reason"] for r in e["trace"][1:] if r["reason"] != "clear"),
                        "all_reported_clear",
                    )
                    for e in log
                    if e["kind"] == "evaluation"
                )
            )

        rows.append(
            dict(
                case=name,
                extra_registrations=extras,
                attempted_work_by_parent_ancestry=dict(work),
                first_numeric_request_divergence_from_iter183=divergence,
                maximum_registered_frame=max(n["state"][5] for n in parents.values()),
                first_rejection_counts=reasons(events),
                iter183_first_rejection_counts=reasons(previous),
            )
        )
    return dict(
        status="exploratory",
        scope="Post-outcome retained chronology. No new motion or mask queries. Work ancestry is descriptive, not causal attribution. Unregistered background labels remain producer evidence.",
        raw_commit=admitted["raw_commit"],
        records=rows,
    )


if __name__ == "__main__":
    write(Path.cwd() / BASE / "proof/chronology.json", describe(Path.cwd()))
