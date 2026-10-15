"""Post-admission descriptive inventory; no collision query or motion search."""

import json
from pathlib import Path

from experiments.iter183_timing_eligibility.common import git, read, require, sha, write

BASE = Path("experiments/iter183_timing_eligibility")
RAW = "172cf0f5449e4171c3f9a25bc45d6e6cb7f03bd5"
ADMITTED = "c53ac67984fde742a6f16a7451451f55a7913e70"


def main():
    root = Path.cwd()
    name = BASE / "proof/search_raw/bend_right/events.jsonl"
    data = read(root, name)
    require(data == git(root, "show", RAW + ":" + str(name)), "raw_binding")
    admitted_name = BASE / "proof/admission.json"
    admitted = read(root, admitted_name)
    require(admitted == git(root, "show", ADMITTED + ":" + str(admitted_name)), "admission_binding")
    admission = json.loads(admitted)
    require(admission["raw_commit"] == RAW and admission["complete_cases"] == 3, "admission_scope")
    events = [json.loads(line) for line in data.splitlines()]
    connections = {r["call"]: r for r in events if r["kind"] == "connection"}
    evaluations = [r for r in events if r["kind"] == "evaluation"]
    accepted = [r for r in connections.values() if r["result"] is not None and len(r["trace"]) > 1]
    highest = max(r["trace"][-1]["route"]["nearest"] for r in accepted)
    advanced = []
    for trial in evaluations:
        for k in range(1, trial["eligibility"]["eligible_prefix"] + 1):
            row = trial["trace"][k]
            if row["route"]["nearest"] <= highest:
                continue
            connection = connections[trial["call"]]
            chosen = connection["result"]
            on_edge = (
                chosen["selected_evaluation"] == trial["id"] and k <= chosen["selected_prefix"]
            )
            advanced.append(
                dict(
                    call=trial["call"],
                    evaluation=trial["id"],
                    prefix=k,
                    frame=row["frame"],
                    state=row["state"],
                    route=row["route"],
                    selected_edge_interior=on_edge,
                    selected_evaluation=chosen["selected_evaluation"],
                    selected_prefix=chosen["selected_prefix"],
                )
            )
    maxima = []
    for call in sorted({r["call"] for r in advanced}):
        group = [r for r in advanced if r["call"] == call]
        chosen = min(
            group, key=lambda r: (-r["route"]["nearest"], r["frame"], r["evaluation"], r["prefix"])
        )
        consumed = sum(
            c["result"]["attempts"]
            for n, c in connections.items()
            if n <= call and c["result"] is not None
        )
        maxima.append(
            dict(
                **chosen,
                attempts_through_connection=consumed,
                remaining_original_attempts=18000 - consumed,
            )
        )
    late = []
    for c in accepted:
        last = c["trace"][-1]
        if last["frame"] < 24:
            continue
        outgoing = [
            r["call"]
            for r in connections.values()
            if r["before"] == [*last["state"], last["frame"]]
        ]
        late.append(
            dict(
                call=c["call"],
                frame=last["frame"],
                state=last["state"],
                route=last["route"],
                outgoing_calls=outgoing,
            )
        )
    write(
        root / BASE / "proof/frontier_notes.json",
        dict(
            status="exploratory",
            scope="Post-admission descriptive recorded-valid/eligible prefixes; no new scalar masks, continuation acquisition or counterfactual tree.",
            raw_commit=RAW,
            admission_commit=ADMITTED,
            input_sha256=sha(data),
            admission_sha256=sha(admitted),
            accepted_endpoint_count=len(accepted),
            maximum_accepted_nearest_index=highest,
            advanced_prefix_records=len(advanced),
            advancing_connections=len(maxima),
            records=advanced,
            per_connection_maxima=maxima,
            late_accepted_endpoints=late,
            generated_valid_frame32=sum(
                r["trace"][r["valid_prefix"]]["frame"] >= 32 for r in evaluations
            ),
            boundary="Motion, eligibility and recorded labels were checked; these extra prefix masks have not received full scalar replay. Higher route progress is not evidence of an extendable path, full completion or a repair.",
        ),
    )
    print(
        json.dumps(
            dict(
                advanced_prefix_records=len(advanced),
                advancing_connections=len(maxima),
                maximum_accepted_nearest_index=highest,
                late_accepted_endpoints=len(late),
            )
        )
    )


if __name__ == "__main__":
    main()
