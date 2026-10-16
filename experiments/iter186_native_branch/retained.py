"""Transport already admitted numerical paths; no motion search or mask acquisition."""

from .native import branch, solve
from .fixtures import SEED
from .transport import expand
from experiments.iter158_constraint_aware_search.common import require


def transport(library, path):
    trace = path["trace"]
    start = [*trace[0]["state"], trace[0]["frame"]]
    last = [*trace[-1]["state"], trace[-1]["frame"]]
    cursor, calls, next_token, latest = 0, 0, 1, 1
    sequences = {}
    states = {1: start}

    def event(row):
        nonlocal latest
        if row["kind"] in (1, 2):
            states[row["node"]] = row["state"]
            sequences[row["token"]]["node"] = row["node"]
            latest = row["node"]

    def branches(parent, before, target):
        nonlocal cursor, calls, next_token
        calls += 1
        if parent != latest:
            return []
        require(before == [*trace[cursor]["state"], trace[cursor]["frame"]], "retained_parent")
        remaining = len(trace) - 1 - cursor
        steps = min(8, remaining)
        if remaining == 9:
            steps = 7
        segments = [trace[cursor : cursor + steps + 1]]
        if remaining <= 8 and steps >= 2:
            segments.insert(0, segments[0][:-1])
        rows = []
        for segment in segments:
            token = next_token
            next_token += 1
            sequences[token] = dict(parent=parent, node=None, trace=segment)
            rows.append(branch(parent, token, segment))
        cursor += steps
        return rows

    result = solve(
        library,
        SEED,
        start,
        [-10000] * 6,
        [10000] * 6,
        last,
        branches,
        lambda state: abs(last[5] - state[5]),
        lambda: calls >= 128,
        lambda: False,
        lambda: states[latest],
        event,
    )
    require(result["status"] == 2 and result["stop_code"] == 3, "retained_transport_incomplete")
    expanded, tokens = expand(result["rows"], sequences, start)
    require(
        [(r["state"], r["frame"], r["action"]) for r in expanded]
        == [(r["state"], r["frame"], r["action"]) for r in trace],
        "retained_transport_changed",
    )
    return dict(
        call=path["call"],
        evaluation=path["evaluation"],
        prefix=path["prefix"],
        original_ambiguous_joins=path["ambiguous_joins"],
        native=result,
        sequences={str(k): v for k, v in sequences.items()},
        tokens=tokens,
        directed_calls=calls,
        transported_states=len(trace),
        new_motion_searches=0,
        new_mask_queries=0,
    )
