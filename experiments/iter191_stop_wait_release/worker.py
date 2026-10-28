"""Recorded callbacks and actual native fixtures with all-query materialization."""

import json
from pathlib import Path
import time
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter186_native_branch.selection import nearest
from experiments.iter189_uniform_timing_eligibility import adapter as baseline
from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
from experiments.iter190_late_continuation_audit.masks import Queries
from . import adapter
from .common import OLD, PREVIOUS, encode, read, require, write


def request(record, case, old, plan, query, enabled):
    started = time.monotonic()
    events = []

    def emit(kind, row):
        events.append(dict(kind=kind, **row))

    edges = (adapter.RetainingEdges if enabled else baseline.RetainingEdges)(
        case["geometry"], old, plan, query, emit
    )
    edges.started = started - record["charged_original_wall"]
    edges.eligibility = Eligibility(case["geometry"], old, edges.started)
    edges.attempts = record["consumed_attempts"]
    edges.calls = record["call"] - 1
    edges.nodes = {int(k): v for k, v in record["nodes"].items()}
    edges.endpoints = {tuple(n["state"]) for n in edges.nodes.values()}
    edges.maximum = max(
        nearest(n["state"][:5], case["geometry"]["route"]) for n in edges.nodes.values()
    )
    branches = edges.branches(record["parent"], record["before"], record["target"])
    return dict(
        input_id=record["id"],
        arm="candidate" if enabled else "baseline",
        events=events,
        branches=branches,
        sequences=edges.sequences,
        attempts=edges.attempts - record["consumed_attempts"],
        queries=edges.queries,
        before_payload_seconds=time.monotonic() - started,
    ), started


def native_fixture(root, output, library, label, enabled):
    from .fixtures import case as make_case
    from .runtime import verify

    verify(root, library)
    case = make_case(label)
    old = json.loads(read(root, OLD))
    plan = json.loads(read(root, PREVIOUS / "PLAN.json"))
    plan.update(attempt_budget=512, per_run_seconds=10)
    output.mkdir(exist_ok=False)
    query = Queries(output / "masks", query_for(case))
    with (output / "events.jsonl").open("xb") as events:

        def emit(kind, row):
            events.write(encode(dict(kind=kind, **row)))
            require(events.tell() < 16 * 1024 * 1024, "fixture_output")

        result = (adapter.search if enabled else baseline.search)(
            library, case["geometry"], old, plan, query, emit, 20261028
        )
    trace, sequences = result.pop("trace"), result.pop("sequences")
    query.finish()
    write(output / "inputs.json", dict(case=case, old=old, plan=plan, enabled=enabled))
    write(output / "trace.json", trace)
    write(output / "sequences.json", sequences)
    write(output / "result.json", result)
    verify(root, library)
    print(
        json.dumps(
            dict(
                fixture=label,
                arm="candidate" if enabled else "baseline",
                complete=result["complete"],
                attempts=result["attempts"],
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--fixture", required=True)
    p.add_argument("--candidate", action="store_true")
    a = p.parse_args()
    native_fixture(Path.cwd(), a.output, a.library, a.fixture, a.candidate)
