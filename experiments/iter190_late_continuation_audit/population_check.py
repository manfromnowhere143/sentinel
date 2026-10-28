"""Independent backward native ancestry and evaluation-based original accounting."""

import json
from .common import BASE, CASES, PARENT, PREVIOUS, encode, read, require, sha


def load(root):
    population = json.loads(read(root, BASE / "POPULATION.json"))
    require(population["parent_commit"] == PARENT, "population_parent")
    for name, digest in population["inputs"].items():
        require(sha(read(root, name)) == digest, "population_input:" + name)
    plan = json.loads(read(root, PREVIOUS / "PLAN.json"))
    cases = {c["id"]: c for c in json.loads(read(root, CASES))}
    result, expected, representatives = [], [], {}
    for name in plan["cases"]:
        folder = PREVIOUS / "proof/search_raw" / name
        sequences = json.loads(read(root, folder / "sequences.json"))
        by_node = {s["node"]: dict(s, token=int(token)) for token, s in sequences.items()}
        initial = json.loads(read(root, folder / "selected/trace.json"))[0]
        original = json.loads(read(root, folder / "result.json"))
        spent, registrations, outgoing, calls, parent = 0, {}, {}, {}, None
        for line in read(root, folder / "events.jsonl").splitlines():
            row = json.loads(line)
            if row["kind"] == "evaluation":
                spent += len(row["trace"]) - 1
                outgoing.setdefault(parent, []).append(row)
            elif row["kind"] == "connection":
                calls.setdefault(parent, []).append(row["call"])
            elif row["kind"] == "native_event":
                event = row["event"]
                if event["kind"] == 3:
                    parent = event["node"]
                elif event["kind"] in (1, 2):
                    s = by_node[event["node"]]
                    require(
                        s["parent"] == event["parent"]
                        and s["token"] == event["token"]
                        and s["extra"] == (event["kind"] == 2)
                        and event["state"] == [*s["trace"][-1]["state"], s["trace"][-1]["frame"]]
                        and event["steps"] == len(s["trace"]) - 1,
                        "native_binding",
                    )
                    registrations[event["node"]] = dict(spent=spent, elapsed=row["elapsed"])
        require(spent == original["attempts"], "original_attempts")
        paths = {1: [initial]}
        ancestry = {1: [1]}
        for node in by_node:
            chain, seen = [], set()
            cursor = node
            while cursor != 1:
                require(cursor in by_node and cursor not in seen, "native_chain")
                seen.add(cursor)
                chain.append(cursor)
                cursor = by_node[cursor]["parent"]
            path = [initial]
            for child in reversed(chain):
                part = by_node[child]["trace"]
                require(
                    path[-1]["state"] == part[0]["state"] and path[-1]["frame"] == part[0]["frame"],
                    "native_join",
                )
                path += part[1:]
            paths[node] = path
            ancestry[node] = [1, *reversed(chain)]
        for node, registered in registrations.items():
            last = paths[node][-1]
            if not 24 <= last["frame"] < 32:
                continue
            identity = f"{name}:{node}"
            signature = name + ":" + sha(encode([last["frame"], last["state"]]))
            rep = representatives.setdefault(signature, identity)
            s = by_node[node]
            expected.append(
                dict(
                    id=identity,
                    case=name,
                    node=node,
                    parent=s["parent"],
                    token=s["token"],
                    origin="extra" if s["extra"] else "primary",
                    frame=last["frame"],
                    state=last["state"],
                    trace=paths[node],
                    representative=rep,
                    consumed_attempts=registered["spent"],
                    remaining_attempts=plan["attempt_budget"] - registered["spent"],
                    registration_elapsed=registered["elapsed"],
                    charged_original_wall=original["elapsed_seconds"],
                    remaining_seconds=plan["per_run_seconds"] - original["elapsed_seconds"],
                    outgoing_calls=calls.get(node, []),
                    outgoing_evaluations=[[r["call"], r["id"]] for r in outgoing.get(node, [])],
                )
            )
        result.append(
            dict(
                case=cases[name],
                paths=paths,
                ancestry=ancestry,
                outgoing=outgoing,
                sequences=sequences,
            )
        )
    require(
        population["records"] == expected and len(expected) == 22 and len(representatives) == 21,
        "population_complete_identity",
    )
    return population, result


def through_rejection(row):
    result = []
    for state in row["trace"]:
        result.append(state)
        if state["reason"] != "clear":
            break
    return result


def match(suffix, candidate):
    count = 0
    for x, y in zip(suffix[1:], candidate[1:]):
        if (
            x["frame"] != y["frame"]
            or x["state"] != y["state"]
            or x["action"] != y["action"]
            or y["reason"] != "clear"
        ):
            break
        count += 1
    return count


def expansion(record, suffix, source):
    rows = source["outgoing"].get(record["node"], [])
    generated = max((match(suffix, through_rejection(e)) for e in rows), default=0)
    registered = 0
    for node, chain in source["ancestry"].items():
        if record["node"] in chain:
            path = source["paths"][node]
            registered = max(registered, match(suffix, path[record["frame"] :]))
    size = len(suffix) - 1
    return dict(
        requested=bool(record["outgoing_calls"]),
        requests=len(record["outgoing_calls"]),
        evaluations=len(rows),
        matched_generated_steps=generated,
        matched_registered_steps=registered,
        full_continuation_generated=generated >= size,
        full_continuation_registered=registered >= size,
    )
