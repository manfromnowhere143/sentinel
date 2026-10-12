"""Route cost for ordering only; no admissibility or collision guarantee."""

import math

import numpy as np


class RouteGuidance:
    def __init__(self, geometry):
        self.path = np.asarray(geometry["route"], dtype=float)[:, ::-1]
        self.arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(self.path, axis=0), axis=1))]
        self.goal = math.ceil(0.9 * len(self.path)) - 1

    def distance(self, state):
        delta = self.path - state[:2]
        nearest = int(np.argmin(np.sum(delta * delta, axis=1)))
        station = min(self.arc[self.goal], self.arc[nearest] + 5.0)
        target = [float(np.interp(station, self.arc, self.path[:, j])) for j in (0, 1)]
        angle = math.atan2(target[1] - state[1], target[0] - state[0])
        error = abs(math.atan2(math.sin(angle - state[2]), math.cos(angle - state[2])))
        return (
            max(0.0, self.arc[self.goal] - self.arc[nearest])
            + 4.0 * float(np.linalg.norm(delta[nearest]))
            + 2.7 * error
        )
