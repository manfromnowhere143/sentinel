"""Small visibility graph for search ordering only, never collision admission.

Inflated axis-aligned foreground bounds are a heuristic. They ignore background,
vehicle orientation, dynamic reachability and road semantics. The exact predicates
remain mandatory even if this heuristic says that a route is short.
"""

import heapq
import math


def crosses(a, b, rectangle):
    """Whether the open segment enters the strict interior of an axis-aligned box."""
    enter, leave = 0.0, 1.0
    for k in range(2):
        delta = b[k] - a[k]
        low, high = rectangle[k], rectangle[k + 2]
        if abs(delta) < 1e-12:
            if not low < a[k] < high:
                return False
        else:
            p, q = (low - a[k]) / delta, (high - a[k]) / delta
            enter, leave = max(enter, min(p, q)), min(leave, max(p, q))
    return enter < leave - 1e-12


class Guidance:
    def __init__(self, geometry):
        radius = math.hypot(*geometry["ego_dimensions"][:2]) / 2 + 0.25
        self.rectangles = []
        for o in geometry["obstacles"]:
            c, s = abs(math.cos(o[6])), abs(math.sin(o[6]))
            dx, dy = (o[4] * c + o[3] * s) / 2 + radius, (o[4] * s + o[3] * c) / 2 + radius
            self.rectangles.append((o[0] - dx, -o[1] - dy, o[0] + dx, -o[1] + dy))
        goal = geometry["route"][math.ceil(0.9 * len(geometry["route"])) - 1][::-1]
        self.nodes = [goal]
        for x0, y0, x1, y1 in self.rectangles:
            self.nodes.extend([(x0, y0), (x0, y1), (x1, y0), (x1, y1)])
        self.distances = [math.inf] * len(self.nodes)
        self.distances[0] = 0.0
        queue = [(0.0, 0)]
        while queue:
            distance, index = heapq.heappop(queue)
            if distance != self.distances[index]:
                continue
            for j, point in enumerate(self.nodes):
                if self.visible(self.nodes[index], point):
                    value = distance + math.dist(self.nodes[index], point)
                    if value < self.distances[j]:
                        self.distances[j] = value
                        heapq.heappush(queue, (value, j))

    def visible(self, a, b):
        return not any(crosses(a, b, rect) for rect in self.rectangles)

    def distance(self, state):
        position = state[:2]
        choices = [
            (math.dist(position, p) + d, j)
            for j, (p, d) in enumerate(zip(self.nodes, self.distances))
            if self.visible(position, p) and math.isfinite(d)
        ]
        # Being inside the heuristic inflation never becomes a hard rejection.
        if not choices:
            return 1e6 + math.dist(position, self.nodes[0])
        remaining, index = min(choices)
        point = self.nodes[index]
        target = math.atan2(point[1] - position[1], point[0] - position[0])
        error = abs(math.atan2(math.sin(target - state[2]), math.cos(target - state[2])))
        return remaining + 2.7 * error
