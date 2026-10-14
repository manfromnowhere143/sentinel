"""Producer extraction of the frozen historical prefix; no future actions are exposed."""

import json

from .common import read, require, sha


def extract(root, plan):
    cases = []
    for spec in plan["histories"]:
        raw = read(root, spec["trace_path"])
        decisions = read(root, spec["decision_path"])
        require(sha(raw) == spec["trace_sha256"], "history_trace_identity")
        require(sha(decisions) == spec["decision_sha256"], "history_decision_identity")
        rows = [json.loads(line) for line in raw.splitlines()]
        decision_rows = [json.loads(line) for line in decisions.splitlines()]
        first = next(d for d in decision_rows if d["fired"])
        require(
            first["frame_index"] == plan["start_frame"] and first["ts"] == plan["start_frame"] / 4,
            "first_fire",
        )
        reset = next(r for r in rows if r["event"] == "reset")
        steps = [r for r in rows if r["event"] == "step" and r["frame"] <= plan["start_frame"]]
        require(
            [r["frame"] for r in steps] == list(range(1, plan["start_frame"] + 1)), "prefix_steps"
        )
        require(reset["time"] == 0, "reset_time")
        states = [reset["state"], *(r["after"] for r in steps)]
        actions = [None, *([r["applied"]["acc"], r["applied"]["steer_rate"]] for r in steps)]
        cases.append(dict(episode=spec["episode"], states=states, actions=actions))
    require(
        len(cases) == 2
        and cases[0]["states"] == cases[1]["states"]
        and cases[0]["actions"] == cases[1]["actions"],
        "prefix_replica_agreement",
    )
    return cases
