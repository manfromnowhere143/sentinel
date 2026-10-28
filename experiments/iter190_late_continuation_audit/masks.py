"""All-query retention and separate scalar replay, scoped to one source case."""

import json
import math
import time
import numpy as np
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter182_late_frontier_timing.retained import state_key
from experiments.iter155_background_witness.geometry import ground_height, vertices, count_points
from .common import read, require, rss, sha, write


class Queries:
    def __init__(self, folder, query):
        self.folder, self.query, self.rows, self.calls = folder, query, {}, 0
        folder.mkdir()

    def __call__(self, state):
        actual = self.query(state)
        self.calls += 1
        result = summary(actual)
        key = state_key(state)
        if key not in self.rows:
            self.rows[key] = dict(key=key, state=state, background=result)
            (self.folder / (key + ".bin")).write_bytes(
                np.packbits(actual.mask, bitorder="little").tobytes()
            )
        require(result == self.rows[key]["background"], "query_conflict")
        return result

    def retain(self, row):
        if row["background"] is not None:
            require(self(row["state"]) == row["background"], "retained_query_disagreement")

    def finish(self):
        write(self.folder / "states.json", list(self.rows.values()))


def verify(folder, case, deadline, max_states=50000):
    rows = json.loads(read(folder / "masks", "states.json"))
    require(isinstance(rows, list) and 0 < len(rows) <= max_states, "mask_population")
    result = {}
    for row in rows:
        require(time.monotonic() < deadline and rss() <= 1073741824, "scalar_resources")
        require(set(row) == {"key", "state", "background"}, "mask_schema")
        state, key = row["state"], row["key"]
        require(
            isinstance(state, list)
            and len(state) == 5
            and all(type(x) in (int, float) and math.isfinite(x) for x in state),
            "mask_state",
        )
        require(key == state_key(state) and key not in result, "mask_identity")
        height, _ = ground_height(case["ground"], state[1], state[0])
        actual = count_points(case["points"], vertices([state[1], height, state[0]], state[2]))
        packed = np.packbits(np.array(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(read(folder / "masks", key + ".bin", 40000) == packed, "scalar_mask")
        expected = {k: actual[k] for k in ("count", "certain_inside", "possible_inside")}
        expected.update(
            mask_sha256=sha(packed),
            decision="clear"
            if actual["possible_inside"] <= 100
            else ("collision" if actual["certain_inside"] > 100 else "numerically_ambiguous"),
        )
        require(expected == row["background"], "scalar_counts")
        result[key] = row
    require(
        {p.name for p in (folder / "masks").iterdir()}
        == {"states.json", *(k + ".bin" for k in result)},
        "mask_inventory",
    )
    return result
