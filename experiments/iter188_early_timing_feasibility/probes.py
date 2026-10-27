"""Fixed scalar countercheck grid evaluated by the retained source functions."""

import math

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import limits, transition


def actions(state):
    acceleration, rate = 2 + 1e-12, math.pi / 12 + 1e-12

    def clip(value, bound):
        return min(bound, max(-bound, value))

    first = dict.fromkeys([-acceleration, -2.0, -1.0, 0.0, 1.0, 2.0, acceleration, clip(-4 * state[3], acceleration), clip(4 * (6 - state[3]), acceleration)])
    second = dict.fromkeys([-rate, -math.pi / 24, 0.0, math.pi / 24, rate, clip(-4 * state[4], rate)])
    return [[a, r] for a in first for r in second]


def probe(state, frame, action, geometry, old):
    after = transition(state, action, old)
    control = limits(after, action, old)
    outcome = route_outcome(after, geometry["route"])
    early = frame + 1 < max(c["hazard_time"] * 4 for c in geometry["comparators"].values())
    return dict(action=action, state=after, controls_valid=control, nearest=outcome["nearest"],
                rc=outcome["rc"], timing_counterexample=bool(early and control and outcome["rc"] < 1))
