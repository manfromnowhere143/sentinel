"""Freeze every late native node before evaluating a new continuation."""

import json
from pathlib import Path
from .common import BASE, PARENT, PREVIOUS, CASES, OLD, encode, read, require, sha


def build(root):
    inputs = {}

    def load(name):
        raw = read(root, name)
        inputs[str(name)] = sha(raw)
        return json.loads(raw)

    previous = load(PREVIOUS / "PLAN.json")
    admission = load(PREVIOUS / "proof/admission.json")
    load(PREVIOUS / "proof/qualification_admission.json")
    load(CASES)
    load(OLD)
    records, groups = [], {}
    for case in previous["cases"]:
        folder = PREVIOUS / "proof/search_raw" / case
        sequences = load(folder / "sequences.json")
        initial = load(folder / "selected/trace.json")[0]
        result = load(folder / "result.json")
        require(
            result
            == next({k: r[k] for k in result} for r in admission["records"] if r["case"] == case),
            "admitted_result",
        )
        raw = read(root, folder / "events.jsonl")
        inputs[str(folder / "events.jsonl")] = sha(raw)
        events = [json.loads(line) for line in raw.splitlines()]
        nodes, spent, calls, evaluations = {1: [initial]}, 0, {}, {}
        parent = None
        for row in events:
            if row["kind"] == "connection" and row["result"] is not None:
                spent += row["result"]["attempts"]
            if row["kind"] == "native_event":
                event = row["event"]
                if event["kind"] == 3:
                    parent = event["node"]
                elif event["kind"] in (1, 2):
                    sequence = sequences[str(event["token"])]
                    nodes[event["node"]] = nodes[event["parent"]] + sequence["trace"][1:]
                    frame = sequence["trace"][-1]["frame"]
                    if 24 <= frame < 32:
                        identity = f"{case}:{event['node']}"
                        state = sequence["trace"][-1]["state"]
                        key = case + ":" + sha(encode([frame, state]))
                        representative = groups.setdefault(key, identity)
                        records.append(
                            dict(
                                id=identity,
                                case=case,
                                node=event["node"],
                                parent=event["parent"],
                                token=event["token"],
                                origin="extra" if event["kind"] == 2 else "primary",
                                frame=frame,
                                state=state,
                                trace=nodes[event["node"]],
                                representative=representative,
                                consumed_attempts=spent,
                                remaining_attempts=previous["attempt_budget"] - spent,
                                registration_elapsed=row["elapsed"],
                                charged_original_wall=result["elapsed_seconds"],
                                remaining_seconds=previous["per_run_seconds"]
                                - result["elapsed_seconds"],
                            )
                        )
            elif row["kind"] == "connection":
                calls.setdefault(parent, []).append(row["call"])
            elif row["kind"] == "evaluation":
                evaluations.setdefault(parent, []).append([row["call"], row["id"]])
        require(spent == result["attempts"], "original_work_accounting")
        for record in records:
            if record["case"] == case:
                record["outgoing_calls"] = calls.get(record["node"], [])
                record["outgoing_evaluations"] = evaluations.get(record["node"], [])
    return dict(
        schema="sentinel.iter190.population.v1",
        parent_commit=PARENT,
        rule="All Iter189 registered nodes at absolute frames 24 through 31; all cases, ascending native registration.",
        inputs=inputs,
        records=records,
    )


if __name__ == "__main__":
    value = build(Path.cwd())
    require(
        len(value["records"]) == 22 and len({r["representative"] for r in value["records"]}) == 21,
        "population_size",
    )
    (BASE / "POPULATION.json").write_bytes(encode(value))
    print(
        json.dumps(
            dict(
                records=22,
                distinct_roots=21,
                inputs=len(value["inputs"]),
                outgoing_evaluations=sum(len(r["outgoing_evaluations"]) for r in value["records"]),
            )
        )
    )
