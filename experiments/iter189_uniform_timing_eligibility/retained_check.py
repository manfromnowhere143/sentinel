"""Rebuild retained ancestries in forward native registration order and replay."""

import json
import time

from .common import read, require
from .eligibility_check import EligibilityReplay


def check(root, path, deadline, limit=120):
    population = json.loads(
        read(root, "experiments/iter188_early_timing_feasibility/POPULATION.json")
    )
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    cases = {
        c["id"]: c["geometry"]
        for c in json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    }
    traces, expected, replay = {}, [], {}
    for case in cases:
        base = "experiments/iter187_integrated_branch_retention/proof/search_raw/" + case + "/"
        by_token = json.loads(read(root, base + "sequences.json"))
        initial = json.loads(read(root, base + "selected/trace.json"))[0]
        nodes = {1: [initial]}
        for line in read(root, base + "events.jsonl").splitlines():
            event = json.loads(line)
            if event["kind"] == "native_event" and event["event"]["kind"] in (1, 2):
                event = event["event"]
                part = by_token[str(event["token"])]["trace"]
                parent = nodes[event["parent"]]
                require(
                    parent[-1]["state"] == part[0]["state"]
                    and parent[-1]["frame"] == part[0]["frame"],
                    "retained_join",
                )
                nodes[event["node"]] = parent + part[1:]
        traces[case] = nodes
        replay[case] = EligibilityReplay(cases[case], old, limit)
    for endpoint in population["endpoints"]:
        trace = traces[endpoint["case"]][endpoint["node"]]
        require(
            trace[-1]["state"] == endpoint["state"] and trace[-1]["frame"] == endpoint["frame"],
            "retained_population_identity",
        )
        expected.append(("endpoint", endpoint["id"], endpoint["case"], trace))
    controls = population["successful_transition_controls"]
    for iteration, case, name in sorted({(c["iteration"], c["case"], c["path"]) for c in controls}):
        trace = json.loads(read(root, name))
        bound = [c for c in controls if c["path"] == name]
        require(
            len(bound) == len(trace) - 1
            and all(
                c["offset"] == i and c["state"] == trace[i]["state"] and c["next"] == trace[i + 1]
                for i, c in enumerate(bound)
            ),
            "retained_success_binding",
        )
        expected.append(("success", f"{iteration}:{case}", case, trace))
    records = json.loads(path.read_bytes())
    require(len(records) == len(expected) == 264, "retained_population")
    cuts, successes, transitions = [], 0, 0
    for record, (group, identity, case, trace) in zip(records, expected):
        require(time.monotonic() < deadline, "retained_checker_deadline")
        require(
            set(record) == {"group", "id", "case", "eligibility"}
            and (record["group"], record["id"], record["case"]) == (group, identity, case),
            "retained_identity",
        )
        claim = record["eligibility"]
        replay[case].check(
            dict(eligibility=claim, trace=trace, valid_prefix=len(trace) - 1, interrupted=None)
        )
        require(claim["complete"], "retained_incomplete")
        if group == "success":
            require(claim["eligible_prefix"] == len(trace) - 1, "retained_success_cut")
            successes += 1
            transitions += len(trace) - 1
        elif claim["eligible_prefix"] != len(trace) - 1:
            cuts.append(identity)
    require(
        cuts == ["bend_left:18", "bend_left:50"] and successes == 9 and transitions == 300,
        "retained_expected",
    )
    return dict(
        endpoints=255,
        excluded_paths=cuts,
        successful_paths=successes,
        successful_transitions=transitions,
        cases={k: v.summary() for k, v in replay.items()},
    )
