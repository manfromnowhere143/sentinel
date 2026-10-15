"""Retained numeric joins and vector-mask materialization; not native ancestry."""

import copy
import numpy as np

from experiments.iter158_constraint_aware_search.search import summary
from .common import require, write
from .retained import state_key


def extract(connections, call):
    table = {r["call"]: r for r in connections}
    chain, ambiguous = [call], 0
    cursor, cutoff = table[call]["before"], call
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
        chosen = min(choices)
        ambiguous += len(choices) > 1
        require(table[chosen]["before"][5] < cursor[5], "ancestor_clock")
        chain.append(chosen)
        cursor, cutoff = table[chosen]["before"], chosen
    chain.reverse()
    trace = [copy.deepcopy(table[chain[0]]["trace"][0])]
    for n in chain:
        edge = table[n]
        require([*trace[-1]["state"], trace[-1]["frame"]] == edge["before"], "ancestor_join")
        trace.extend(copy.deepcopy(edge["trace"][1:]))
    return dict(call=call, chain=chain, ambiguous_joins=ambiguous, trace=trace)


class Masks:
    def __init__(self, folder, query):
        self.folder, self.query, self.rows = folder, query, {}
        folder.mkdir()

    def add(self, state, expected):
        key = state_key(state)
        if key not in self.rows:
            result = self.query(state)
            claimed = summary(result)
            require(claimed == expected, "vector_materialization")
            self.rows[key] = dict(key=key, state=state, background=claimed)
            (self.folder / (key + ".bin")).write_bytes(
                np.packbits(result.mask, bitorder="little").tobytes()
            )
        require(self.rows[key]["background"] == expected, "state_label_conflict")
        return key

    def path(self, trace):
        return [self.add(row["state"], row["background"]) for row in trace]

    def finish(self):
        write(self.folder / "states.json", list(self.rows.values()))
