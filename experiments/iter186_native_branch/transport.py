"""Strict expansion by native IDs and bound sequence tokens; no numeric parent lookup."""

from experiments.iter158_constraint_aware_search.common import require


def integer(value):
    return type(value) in (int, float) and float(value).is_integer() and 0 <= value <= 2**53 - 1


def expand(rows, sequences, start, dt=0.25):
    require(dt == 0.25 and len(start) == 6, "native_contract")
    initial = dict(id=int(start[5]), parent=None, frame=int(start[5]), action=None, state=start[:5])
    if not rows:
        return [initial], []
    require(rows[0] == [*start, 0, 1, 0, 0, 0], "native_root")
    trace, tokens, nodes, previous = [initial], [], {1}, 1
    for row in rows[1:]:
        require(len(row) == 11 and all(integer(row[i]) for i in (6, 7, 8, 9)), "native_encoding")
        token, node, parent, steps = (int(row[i]) for i in (6, 7, 8, 9))
        require(token in sequences and token not in tokens, "native_token")
        require(node not in nodes and node > parent == previous, "native_parent_id")
        record = sequences[token]
        require(record["parent"] == parent and record["node"] == node, "native_ancestry")
        segment = record["trace"]
        require(1 <= steps <= 8 and steps == len(segment) - 1, "native_steps")
        require(
            [*segment[0]["state"], segment[0]["frame"]]
            == [*trace[-1]["state"], trace[-1]["frame"]],
            "native_parent_state",
        )
        require(row[:6] == [*segment[-1]["state"], segment[-1]["frame"]], "native_endpoint")
        require(row[10] == steps * dt, "native_duration")
        for i, state in enumerate(segment[1:], 1):
            require(state["frame"] == segment[0]["frame"] + i, "native_clock")
            require(len(state["action"]) == 2, "native_control")
        trace.extend(dict(r) for r in segment[1:])
        tokens.append(token)
        nodes.add(node)
        previous = node
    return trace, tokens
