"""A scheduled feedback proposal; no rollout, query, case identity or witness input."""

import math
import numpy as np
from experiments.iter153_action_feasibility.planner import command, reference
from experiments.iter183_timing_eligibility.connection import Evaluator as Previous
from .common import require

PARAMETERS = [1.0, 2.0]  # Program version and fixed release target speed, not actuator values.


def checkpoint(geometry, old):
    values = [c["hazard_time"] / old["dt"] for c in geometry["comparators"].values()]
    require(
        all(math.isfinite(v) and v >= 0 and float(v).is_integer() for v in values), "policy_clock"
    )
    return int(max(values)) if values else None


def active(geometry, before, old, plan):
    final = checkpoint(geometry, old)
    return final is not None and 0 < final - before[5] <= plan["connection_horizon"]


class Feedback:
    def __init__(self, before, geometry, old):
        self.before, self.old = before, old
        self.final = checkpoint(geometry, old)
        require(self.final is not None, "policy_checkpoint_required")
        self.path, self.arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)

    def table(self, values):
        require(list(values) == PARAMETERS, "policy_parameters")
        return None

    def action(self, table, local, state):
        if int(self.before[5]) + local <= self.final:
            bound = self.old["acceleration_bound"]
            return [max(-bound, min(bound, -state[3] / self.old["dt"])), 0.0]
        return command(state, self.path, self.arc, {"speed": 2.0}, self.old)


class Evaluator(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback_cache = {}

    def evaluate_feedback(self):
        controls, cache = self.controls, self.cache
        self.controls = Feedback(self.before, self.geometry, self.old)
        self.cache = self.feedback_cache
        try:
            return super().evaluate(np.asarray(PARAMETERS), "stop_wait_release")
        finally:
            self.controls, self.cache = controls, cache
