"""Numeric retained-prefix reconstruction; every ancestry choice remains visible."""

import copy

from .common import require


def extract(connections, trial, k):
    table = {r["call"]: r for r in connections}
    call = trial["call"]
    cursor, cutoff = table[call]["before"], call
    reverse, joins = [], []
    while cursor[5] > 0:
        choices = [
            n
            for n, r in table.items()
            if n < cutoff
            and r["result"] is not None
            and len(r["trace"]) > 1
            and [*r["trace"][-1]["state"], r["trace"][-1]["frame"]] == cursor
        ]
        require(bool(choices), "ancestor_missing")
        choices.sort()
        chosen = choices[0]
        joins.append(dict(cutoff=cutoff, state_clock=cursor, choices=choices, chosen=chosen))
        require(table[chosen]["before"][5] < cursor[5], "ancestor_clock")
        reverse.append(chosen)
        cursor, cutoff = table[chosen]["before"], chosen
    chain = list(reversed(reverse))
    trace = []
    for number in chain:
        segment = table[number]["trace"]
        if not trace:
            trace.append(copy.deepcopy(segment[0]))
        require(
            [*trace[-1]["state"], trace[-1]["frame"]] == table[number]["before"], "ancestor_join"
        )
        trace.extend(copy.deepcopy(segment[1:]))
    segment = trial["trace"][: k + 1]
    if not trace:
        trace.append(copy.deepcopy(segment[0]))
    require(
        trace[-1]["state"] == segment[0]["state"] and trace[-1]["frame"] == segment[0]["frame"],
        "discarded_join",
    )
    trace.extend(copy.deepcopy(segment[1:]))
    return dict(
        call=call,
        evaluation=trial["id"],
        prefix=k,
        chain=chain,
        joins=joins,
        ambiguous_joins=sum(len(j["choices"]) > 1 for j in joins),
        trace=trace,
    )
