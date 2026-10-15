"""Same control interface with next-root bounds matching existing motion tolerance."""

import math

import numpy as np

from .common import require


class Controls:
    def __init__(self, reset, task):
        self.reset, self.task = reset, task
        horizon, wait, stop = task["terminal_frame"], task["wait_until"], task["stop_from"]
        require(type(horizon) is int and 1 <= horizon <= 16, "task_horizon")
        require(type(wait) is int and 0 <= wait <= horizon, "wait_domain")
        require(stop is None or type(stop) is int and wait < stop <= horizon, "stop_domain")
        require(
            len(reset) == 5
            and len(task["target"]) == 5
            and all(
                type(v) in (int, float) and math.isfinite(v) for v in [*reset, *task["target"]]
            ),
            "state_domain",
        )
        require(-1e-12 <= reset[3] <= 6 + 1e-12 and abs(reset[4]) <= math.pi / 3 + 1e-12, "reset_bounds")
        require(
            len(task["tolerance"]) == 5
            and all(
                type(v) in (int, float) and math.isfinite(v) and v > 0 for v in task["tolerance"]
            ),
            "tolerance_domain",
        )
        self.variables = []
        for frame in range(wait + 1, horizon + 1):
            if stop is None or frame < stop:
                self.variables.append((frame, 0))
            self.variables.append((frame, 1))

    def initial(self):
        task, reset = self.task, self.reset
        duration = (task["stop_from"] or task["terminal_frame"]) - task["wait_until"]
        acceleration = ((0 if task["stop_from"] else task["target"][3]) - reset[3]) / (
            0.25 * max(1, duration)
        )
        rate = (task["target"][4] - reset[4]) / (
            0.25 * max(1, task["terminal_frame"] - task["wait_until"])
        )
        return np.asarray(
            [
                np.clip(acceleration / 2 if k == 0 else rate / (math.pi / 12), -1.0, 1.0)
                for _, k in self.variables
            ],
            dtype=float,
        )

    def table(self, values):
        require(
            len(values) == len(self.variables) and np.isfinite(values).all(), "parameter_domain"
        )
        return {pair: float(value) for pair, value in zip(self.variables, values)}

    def action(self, table, frame, state):
        a = 2 * table.get((frame, 0), 0.0)
        if frame == self.task["stop_from"]:
            a = -state[3] / 0.25
        return [a, math.pi / 12 * table.get((frame, 1), 0.0)]
