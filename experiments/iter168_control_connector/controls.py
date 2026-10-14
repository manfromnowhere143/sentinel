"""Successor proposal library: retain old controls and add exact bounded braking."""

import math

from experiments.iter158_constraint_aware_search.search import proposals as legacy
from .common import require


def proposals(state, path, arc, old):
    require(
        len(state) == 5
        and all(type(v) in (int, float) and math.isfinite(v) for v in state)
        and 0 <= state[3] <= old["speed_bound"]
        and abs(state[4]) <= math.pi / 3,
        "proposal_state_domain",
    )
    require(old["dt"] == 0.25 and old["acceleration_bound"] == 2, "proposal_contract")
    choices = legacy(state, path, arc, old)
    acceleration = -min(old["acceleration_bound"], state[3] / old["dt"])
    choices += [[acceleration, r * math.pi / 12] for r in (-1, -0.5, 0, 0.5, 1)]
    return [list(a) for a in dict.fromkeys(tuple(a) for a in choices)]
