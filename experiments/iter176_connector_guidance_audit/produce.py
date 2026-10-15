"""Proposal availability and retained-path masks; no new motion search."""

import copy
import struct
import time

from experiments.iter169_full_horizon_control.shooting import Controls
from experiments.iter173_matched_connector_cost.forward import proposals
from .common import require


def reflected(reset, task):
    state, mirrored = list(reset), copy.deepcopy(task)
    for k in (1, 2, 4):
        state[k] = -state[k]
        mirrored["target"][k] = -mirrored["target"][k]
    return state, mirrored


def nominal(reset, task, budget, limit=4096, deadline=None):
    """Count full requested rollouts without propagating or testing completion."""
    controls = Controls(reset, task)
    horizon = task["terminal_frame"]
    rows, cache = [], {}
    spent = hits = 0
    for index, vector in enumerate(proposals(controls)):
        require(index < limit, "proposal_limit")
        require(deadline is None or time.monotonic() < deadline, "producer_deadline")
        values = vector.tolist()
        key = struct.pack(">" + "d" * len(values), *values)
        row = dict(index=index, values=values, cached=False, evaluation=None, stop=None)
        if key in cache:
            hits += 1
            row.update(cached=True, evaluation=cache[key])
        elif spent + horizon > budget:
            row["stop"] = "budget"
            rows.append(row)
            break
        else:
            spent += horizon
            cache[key] = len(cache) + 1
            row["evaluation"] = cache[key]
        rows.append(row)
    return dict(nominal_transitions=spent, unique_evaluations=len(cache), cache_hits=hits,
                requests=rows)


def extract_path(connections, trial, call, reset):
    """Earliest retained ancestor chain; not a claim about native RNG ancestry."""
    target = next(row for row in connections if row["call"] == call)["before"]
    cursor, cutoff, reverse, ambiguous = target, call, [], 0
    while cursor[5] > 0:
        choices = [row for row in connections if row["call"] < cutoff
                   and row["result"] is not None and len(row["trace"]) > 1
                   and [*row["trace"][-1]["state"], row["trace"][-1]["frame"]] == cursor]
        require(bool(choices), "ancestor_missing")
        chosen = min(choices, key=lambda row: row["call"])
        require(chosen["before"][5] < cursor[5], "ancestor_clock")
        ambiguous += len(choices) > 1
        reverse.append(chosen)
        cursor, cutoff = chosen["before"], chosen["call"]
    require(cursor == [*reset, 0], "ancestor_reset")
    chain = list(reversed(reverse))
    trace = [copy.deepcopy(chain[0]["trace"][0] if chain else trial["trace"][0])]
    for edge in chain:
        require([*trace[-1]["state"], trace[-1]["frame"]] == edge["before"], "ancestor_join")
        trace.extend(copy.deepcopy(edge["trace"][1:]))
    require([*trace[-1]["state"], trace[-1]["frame"]] == target, "prefix_join")
    require(trial["interrupted"] is None and trial["valid_prefix"] > trial["selected_prefix"],
            "discarded_prefix")
    require([*trial["trace"][0]["state"], trial["trace"][0]["frame"]] == target,
            "trial_root")
    trace.extend(copy.deepcopy(trial["trace"][1:trial["valid_prefix"]+1]))
    return trace, dict(ancestor_calls=[row["call"] for row in chain], ambiguous_joins=ambiguous)
