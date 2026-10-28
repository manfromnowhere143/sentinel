"""Freeze original late requests and disclosed goal requests before new outcomes."""

import copy
import json
import math
from pathlib import Path
from .common import AUDIT, BASE, CASES, PARENT, PREVIOUS, encode, read, sha


def build(root):
    pop = json.loads(read(root, AUDIT / "POPULATION.json"))
    cases = json.loads(read(root, CASES))
    inputs = dict(pop["inputs"])
    for name in [
        AUDIT / "POPULATION.json",
        AUDIT / "proof/admission.json",
        CASES,
        PREVIOUS / "PLAN.json",
    ]:
        inputs[str(name)] = sha(read(root, name))
    actual, synthetic = [], []
    for case in cases:
        name = case["id"]
        members = [r for r in pop["records"] if r["case"] == name]
        by_node = {r["node"]: r for r in members}
        folder = PREVIOUS / "proof/search_raw" / name
        events = [json.loads(line) for line in read(root, folder / "events.jsonl").splitlines()]
        original = json.loads(read(root, folder / "result.json"))
        nodes, registered, spent, request = {}, {}, 0, None
        for event_index, row in enumerate(events):
            if row["kind"] == "native_event":
                event = row["event"]
                if event["kind"] in (0, 1, 2):
                    nodes[event["node"]] = event
                    if event["node"] in by_node:
                        registered[event["node"]] = event_index
                elif event["kind"] == 3:
                    request = dict(
                        parent=event["node"],
                        before=event["state"],
                        target=event["target"],
                        consumed_attempts=spent,
                        nodes=copy.deepcopy(nodes),
                    )
            elif row["kind"] == "evaluation":
                spent += len(row["trace"]) - 1
            elif row["kind"] == "connection" and request["parent"] in by_node:
                member = by_node[request["parent"]]
                actual.append(
                    dict(
                        id=f"original:{name}:{row['call']}",
                        kind="original",
                        case=name,
                        call=row["call"],
                        members=[member["id"]],
                        trace=member["trace"],
                        charged_original_wall=original["elapsed_seconds"],
                        original_connection=row,
                        **copy.deepcopy(request),
                    )
                )
        route = case["geometry"]["route"]
        goal = math.ceil(0.9 * len(route)) - 1
        a, b = route[max(0, goal - 1)], route[min(len(route) - 1, goal + 1)]
        target = [route[goal][1], route[goal][0], math.atan2(b[0] - a[0], b[1] - a[1]), 2, 0, 96]
        for member in members:
            if member["id"] != member["representative"]:
                continue
            group = [r for r in members if r["representative"] == member["id"]]
            latest = min(group, key=lambda r: r["remaining_attempts"])
            at = registered[latest["node"]]
            end = next(
                (
                    i
                    for i in range(at + 1, len(events))
                    if events[i]["kind"] == "native_event" and events[i]["event"]["kind"] == 3
                ),
                len(events),
            )
            snapshot = {
                r["event"]["node"]: r["event"]
                for r in events[:end]
                if r["kind"] == "native_event" and r["event"]["kind"] in (0, 1, 2)
            }
            synthetic.append(
                dict(
                    id="goal:" + member["id"],
                    kind="goal",
                    case=name,
                    call=(latest["token"] + 1) // 2 + 1,
                    members=[r["id"] for r in group],
                    parent=latest["node"],
                    before=[*latest["state"], latest["frame"]],
                    target=target,
                    consumed_attempts=latest["consumed_attempts"],
                    charged_original_wall=original["elapsed_seconds"],
                    nodes=snapshot,
                    trace=latest["trace"],
                    original_connection=None,
                )
            )
    # JSON object keys canonicalize native node IDs to decimal strings.
    return json.loads(
        encode(
            dict(
                schema="sentinel.iter191.population.v1",
                parent_commit=PARENT,
                inputs=inputs,
                original_requests=len(actual),
                goal_requests=len(synthetic),
                records=actual + synthetic,
            )
        )
    )


if __name__ == "__main__":
    value = build(Path.cwd())
    (Path.cwd() / BASE / "POPULATION.json").write_bytes(encode(value))
    print(json.dumps({k: v for k, v in value.items() if k not in ("inputs", "records")}))
