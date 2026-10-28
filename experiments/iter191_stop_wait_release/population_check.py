"""Independent request windows, original-result accounting and backward ancestry."""

import json
import math
from experiments.iter190_late_continuation_audit.population_check import load as late_population
from .common import AUDIT, BASE, CASES, PARENT, PREVIOUS, encode, read, require, sha


def load(root):
    value = json.loads(read(root, BASE / "POPULATION.json"))
    late, sources = late_population(root)
    inputs = dict(late["inputs"])
    for name in [
        AUDIT / "POPULATION.json",
        AUDIT / "proof/admission.json",
        CASES,
        PREVIOUS / "PLAN.json",
    ]:
        inputs[str(name)] = sha(read(root, name))
    require(value["inputs"] == inputs and value["parent_commit"] == PARENT, "population_inputs")
    original, goals = [], []
    for source in sources:
        case = source["case"]
        name = case["id"]
        members = [r for r in late["records"] if r["case"] == name]
        by_node = {r["node"]: r for r in members}
        folder = PREVIOUS / "proof/search_raw" / name
        events = [json.loads(line) for line in read(root, folder / "events.jsonl").splitlines()]
        wall = json.loads(read(root, folder / "result.json"))["elapsed_seconds"]
        native = [(i, r["event"]) for i, r in enumerate(events) if r["kind"] == "native_event"]

        def context(index):
            return {str(e["node"]): e for i, e in native if i <= index and e["kind"] in (0, 1, 2)}

        connections = [(i, r) for i, r in enumerate(events) if r["kind"] == "connection"]
        consumed = 0
        for index, c in connections:
            request_at, event = next(
                (i, e) for i, e in reversed(native) if i < index and e["kind"] == 3
            )
            parent = event["node"]
            if parent in by_node:
                member = by_node[parent]
                require(
                    c["before"] == event["state"] and c["target"] == event["target"],
                    "original_request_binding",
                )
                original.append(
                    dict(
                        id=f"original:{name}:{c['call']}",
                        kind="original",
                        case=name,
                        call=c["call"],
                        members=[member["id"]],
                        parent=parent,
                        before=c["before"],
                        target=c["target"],
                        consumed_attempts=consumed,
                        charged_original_wall=wall,
                        nodes=context(request_at),
                        trace=source["paths"][parent],
                        original_connection=c,
                    )
                )
            consumed += c["result"]["attempts"] if c["result"] is not None else 0
        route = case["geometry"]["route"]
        goal = next(i for i in range(len(route)) if (i + 1) / (0.9 * len(route)) >= 1)
        left, right = route[max(0, goal - 1)], route[min(len(route) - 1, goal + 1)]
        target = [
            route[goal][1],
            route[goal][0],
            math.atan2(right[0] - left[0], right[1] - left[1]),
            2,
            0,
            96,
        ]
        for representative in [r for r in members if r["id"] == r["representative"]]:
            group = [r for r in members if r["representative"] == representative["id"]]
            latest = max(group, key=lambda r: r["consumed_attempts"])
            at = next(i for i, e in native if e["kind"] in (1, 2) and e["node"] == latest["node"])
            next_request = next((i for i, e in native if i > at and e["kind"] == 3), len(events))
            snapshot = context(next_request - 1)
            next_call = max((n["token"] + 1) // 2 for n in snapshot.values()) + 1
            goals.append(
                dict(
                    id="goal:" + representative["id"],
                    kind="goal",
                    case=name,
                    call=next_call,
                    members=[r["id"] for r in group],
                    parent=latest["node"],
                    before=[*latest["state"], latest["frame"]],
                    target=target,
                    consumed_attempts=latest["consumed_attempts"],
                    charged_original_wall=wall,
                    nodes=snapshot,
                    trace=source["paths"][latest["node"]],
                    original_connection=None,
                )
            )
    expected = json.loads(
        encode(
            dict(
                schema="sentinel.iter191.population.v1",
                parent_commit=PARENT,
                inputs=inputs,
                original_requests=23,
                goal_requests=21,
                records=original + goals,
            )
        )
    )
    require(
        value == expected and len(original) == 23 and len(goals) == 21,
        "complete_request_population",
    )
    return value, {s["case"]["id"]: s["case"] for s in sources}
