"""Prefix admission binding and mechanical concatenation; no search or geometry."""

import copy
import json

from .common import BASE, git, read, require, sha


def prefix_binding(root, commit, plan, source):
    name = (BASE / "proof/prefix_admission.json").as_posix()
    data = read(root, name)
    require(git(root, "show", commit + ":" + name) == data, "prefix_admission_not_committed")
    git(root, "merge-base", "--is-ancestor", source, commit)
    doc = json.loads(data)
    require(
        doc["status"] == "supported"
        and doc["phase"] == "prefix_qualified"
        and doc["source_commit"] == source,
        "prefix_not_qualified",
    )
    require(
        doc["branch"]["frame"] == plan["start_frame"]
        and doc["branch"]["time"] == plan["start_frame"] / 4,
        "prefix_clock",
    )
    trace_path = BASE / "proof/prefix_raw/replica_0/trace.json"
    trace_data = read(root, trace_path)
    require(
        git(root, "show", doc["raw_commit"] + ":" + trace_path.as_posix()) == trace_data,
        "prefix_trace_not_committed",
    )
    trace = json.loads(trace_data)
    require(
        len(trace) == plan["start_frame"] + 1 and trace[-1]["state"] == doc["branch"]["state"],
        "prefix_branch_state",
    )
    return doc, trace, sha(data)


def concatenate(prefix, suffix):
    require(bool(prefix) and bool(suffix), "empty_concatenation")
    require(
        prefix[-1]["frame"] == suffix[0]["frame"]
        and prefix[-1]["state"] == suffix[0]["state"]
        and prefix[-1]["background"] == suffix[0]["background"],
        "branch_join",
    )
    require(
        suffix[0]["id"] == 0 and suffix[0]["parent"] is None and suffix[0]["action"] is None,
        "suffix_initial_identity",
    )
    result = copy.deepcopy(prefix)
    for row in suffix[1:]:
        require(row["frame"] == result[-1]["frame"] + 1, "suffix_clock")
        item = copy.deepcopy(row)
        item["id"], item["parent"] = item["frame"], item["frame"] - 1
        result.append(item)
    return result
