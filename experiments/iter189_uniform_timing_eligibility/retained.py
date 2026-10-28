"""Apply the composed scan to every frozen endpoint ancestry and success path."""

import json
import time

from .common import read, require, write
from .eligibility import Eligibility

POP = "experiments/iter188_early_timing_feasibility/POPULATION.json"
CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
RAW = "experiments/iter187_integrated_branch_retention/proof/search_raw/"


def paths(root):
    population = json.loads(read(root, POP))
    cached = {}
    for item in population["endpoints"]:
        case = item["case"]
        if case not in cached:
            sequences = json.loads(read(root, RAW + case + "/sequences.json"))
            initial = json.loads(read(root, RAW + case + "/selected/trace.json"))[0]
            by_node = {s["node"]: s for s in sequences.values()}
            cached[case] = initial, by_node
        initial, by_node = cached[case]
        chain, node, seen = [], item["node"], set()
        while node != 1:
            require(node not in seen and node in by_node, "retained_parent_chain")
            seen.add(node)
            sequence = by_node[node]
            chain.append(sequence["trace"][1:])
            node = sequence["parent"]
        trace = [initial] + [r for part in reversed(chain) for r in part]
        require(
            trace[-1]["state"] == item["state"] and trace[-1]["frame"] == item["frame"],
            "retained_endpoint",
        )
        yield "endpoint", item["id"], case, trace
    successes = sorted(
        {
            (r["iteration"], r["case"], r["path"])
            for r in population["successful_transition_controls"]
        }
    )
    for iteration, case, path in successes:
        yield "success", f"{iteration}:{case}", case, json.loads(read(root, path))


def produce(root, output, limit=120):
    started = time.monotonic()
    cases = {c["id"]: c["geometry"] for c in json.loads(read(root, CASES))}
    old = json.loads(read(root, OLD))
    engines, records = {}, []
    for group, identity, case, trace in paths(root):
        require(time.monotonic() - started < limit, "retained_producer_deadline")
        engine = engines.setdefault(case, Eligibility(cases[case], old, started))
        claim = engine.scan(trace, len(trace) - 1, None, started + limit)
        records.append(dict(group=group, id=identity, case=case, eligibility=claim))
    write(output, records)
    return len(records)
