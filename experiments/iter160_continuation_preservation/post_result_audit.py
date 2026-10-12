"""Exploratory audit of committed logs after Iter160; no new motion/query execution."""

import json
from pathlib import Path

from experiments.iter159_route_search_qualification.check import equivalent, key, ordering
from .common import BASE, PREVIOUS, encode, read, require, sha


def follow(rows, depths, trace, frame, representative):
    """Locate retention of an already admitted continuation inside old attempts."""
    by_parent, by_frame = {}, {}
    for row in rows:
        by_parent.setdefault(row["parent"], []).append(row)
        by_frame.setdefault(row["frame"], []).append(row)
    require(equivalent(rows[representative]["state"], trace[frame]["state"]), "start_binding")
    if representative not in depths[frame - 1]["beam"]:
        return dict(frame=frame, cause="initial_representative_not_in_beam", attempt=representative)
    parent = representative
    for target in trace[frame + 1 :]:
        f = target["frame"]
        if f > len(depths) or not depths[f - 1]["complete"]:
            return dict(frame=f, cause="run_stopped_before_continuation")
        children = [r for r in by_parent.get(parent, []) if r["action"] == target["action"]]
        require(len(children) == 1, "covered_child")
        child = children[0]
        require(equivalent(child["state"], target["state"]), "state_binding")
        require(child["reason"] == "clear", "admitted_child_rejected")
        if child["route"]["rc"] >= 1:
            return dict(frame=f, cause="continuation_complete", attempt=child["id"])
        if child["id"] not in depths[f - 1]["beam"]:
            peers = [r for r in by_frame[f] if r["reason"] == "clear" and key(r) == key(child)]
            winner = min(peers, key=ordering)
            return dict(
                frame=f,
                cause="cell_representative" if winner["id"] != child["id"] else "beam_width",
                attempt=child["id"],
                replacement=winner["id"],
                replacement_in_beam=winner["id"] in depths[f - 1]["beam"],
            )
        parent = child["id"]
    return dict(frame=trace[-1]["frame"], cause="fixed_suffix_exhausted")


def audit(root):
    inputs = json.loads(read(root, BASE / "INPUTS.json"))
    identities, records = {}, []

    def document(path, lines=False):
        data = read(root, path)
        identities[str(path)] = sha(data)
        return [json.loads(x) for x in data.splitlines()] if lines else json.loads(data)

    for i, pair in enumerate(inputs["pairs"]):
        trace = document(BASE / "proof/raw" / f"pair_{i}_representative" / "trace.json")
        for binding in pair["bindings"]:
            folder = PREVIOUS / "proof/raw" / binding["run"]
            rows = document(folder / "attempts.jsonl", True)
            depths = document(folder / "depths.jsonl", True)
            retained = binding["representative"] in depths[pair["frame"] - 1]["beam"]
            result = follow(rows, depths, trace["rows"], pair["frame"], binding["representative"])
            records.append(
                dict(
                    run=binding["run"],
                    pair=pair["id"],
                    first_representative_in_beam=retained,
                    admitted_suffix=trace["stop"],
                    next_loss=result,
                )
            )
    identities[str(BASE / "INPUTS.json")] = sha(read(root, BASE / "INPUTS.json"))
    return dict(
        status="exploratory",
        acquisition="post-result committed-log inspection only",
        bindings=len(records),
        representatives_in_beam=sum(r["first_representative_in_beam"] for r in records),
        records=records,
        input_sha256=identities,
        new_trajectories=0,
        new_background_queries=0,
        whole_search_causation=None,
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    target = root / BASE / "proof/post-result-retention.json"
    with target.open("xb") as stream:
        stream.write(encode(audit(root)))
