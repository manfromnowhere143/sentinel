"""Post-admission descriptive tree audit; no search, repair or causal attribution."""

from collections import Counter
import json
from pathlib import Path
from experiments.iter172_integrated_rrt.check import outcome
from .common import BASE, load_source, read, sha, write


def main(root):
    admission = json.loads(read(root, BASE / "proof/admission.json"))
    case, old, _ = load_source(root)
    rows = []
    for record in admission["records"]:
        condition = record["condition"]
        offset = condition["origin"] + condition["delay"]
        folder = root / BASE / "proof/search_raw" / condition["id"]
        nodes, requested, reasons, feedback = {}, set(), Counter(), []
        if (folder / "events.jsonl").exists():
            with (folder / "events.jsonl").open() as stream:
                for line in stream:
                    event = json.loads(line)
                    if event["kind"] == "native_event":
                        event = event["event"]
                        if event["kind"] == 3:
                            requested.add(event["node"])
                        else:
                            nodes[event["node"]] = dict(
                                frame=offset + int(event["state"][5]),
                                progress=outcome(event["state"][:5], case["geometry"])["rc"],
                            )
                    elif event["kind"] == "request" and event["caller"] == "stop_wait_release":
                        feedback.append(dict(call=event["call"], evaluation=event["evaluation"]))
                    elif event["kind"] == "evaluation":
                        reasons.update(r["reason"] for r in event["trace"][1:])
        rows.append(
            dict(
                condition=condition,
                complete=record["complete"],
                stop=record["stop"],
                native_nodes=len(nodes),
                requested_nodes=len(requested),
                unrequested_nodes=len(set(nodes) - requested),
                maximum_registered_absolute_frame=max(
                    (n["frame"] for n in nodes.values()), default=None
                ),
                maximum_registered_progress=max(
                    (n["progress"] for n in nodes.values()), default=None
                ),
                registered_at_or_after_checkpoints={
                    name: sum(n["frame"] * old["dt"] >= c["hazard_time"] for n in nodes.values())
                    for name, c in case["geometry"]["comparators"].items()
                },
                feedback_requests=feedback,
                attempted_transition_labels=dict(reasons),
                attempts=record["attempts"],
                queries=record["queries"],
                search_seconds=record.get("elapsed_seconds"),
                worker_seconds=record["worker_seconds"],
            )
        )
    write(
        root / BASE / "proof/descriptive.json",
        dict(
            status="exploratory",
            analysis="post-admission descriptive audit",
            raw_commit=admission["raw_commit"],
            admission_sha256=sha(read(root, BASE / "proof/admission.json")),
            script_sha256=sha(read(root, BASE / "diagnose.py")),
            records=rows,
            boundary="Registered reach and attempt labels describe this finite search. Unselected background labels remain producer evidence. Counts do not establish causal pruning failure or physical infeasibility.",
        ),
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main(Path.cwd())
