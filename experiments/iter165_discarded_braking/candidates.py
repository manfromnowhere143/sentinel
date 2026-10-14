"""Mechanical candidate enumeration from bound historical search records."""

import copy
import json

from .common import read, require

HISTORY = "experiments/iter164_monitor_time_continuation/proof"


def candidates(root):
    rows = [json.loads(x) for x in read(root, HISTORY + "/search_raw/attempts.jsonl").splitlines()]
    nodes = {r["id"]: r for r in rows}
    depth = next(
        json.loads(x)
        for x in read(root, HISTORY + "/search_raw/depths.jsonl").splitlines()
        if json.loads(x)["frame"] == 27
    )
    retained = sorted(depth["beam"])
    discarded = sorted(
        r["id"]
        for r in rows
        if r["frame"] == 27
        and r["reason"] == "clear"
        and r["action"][0] == -2
        and nodes[r["parent"]]["action"][0] == -2
        and r["id"] not in retained
    )
    require(len(discarded) == 25 and len(retained) == 24, "candidate_population")
    schedule = []
    for i in range(25):
        for cohort, ids in [("discarded", discarded), ("retained", retained)]:
            if i < len(ids):
                schedule.append(dict(cohort=cohort, node_id=ids[i]))
    return schedule, nodes


def prefix_for(root, nodes, node_id):
    prefix = json.loads(read(root, HISTORY + "/prefix_raw/replica_0/trace.json"))
    node = nodes[node_id]
    additions = []
    while node["parent"] is not None:
        additions.append(node)
        node = nodes[node["parent"]]
    require(node["state"] == prefix[-1]["state"] and node["frame"] == 25, "historical_join")
    for original in reversed(additions):
        row = copy.deepcopy(original)
        row["id"], row["parent"] = row["frame"], row["frame"] - 1
        require(row["frame"] == prefix[-1]["frame"] + 1, "candidate_clock")
        prefix.append(row)
    require(len(prefix) == 28, "candidate_length")
    return prefix
