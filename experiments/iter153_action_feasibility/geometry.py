"""Producer geometry in controller forward/lateral coordinates."""

import math
import numpy as np


def polygon(box):
    x, y, width, length, heading = box
    local = np.array([[1, 1], [1, -1], [-1, -1], [-1, 1]]) * [length / 2, width / 2]
    c, s = math.cos(heading), math.sin(heading)
    return local @ np.array([[c, s], [-s, c]]) + [x, y]


def separation(a, b):
    p, q = polygon(a), polygon(b)
    edges = np.vstack([np.roll(p, -1, axis=0) - p, np.roll(q, -1, axis=0) - q])
    axes = np.c_[-edges[:, 1], edges[:, 0]]
    axes /= np.linalg.norm(axes, axis=1)[:, None]
    aa, bb = p @ axes.T, q @ axes.T
    gaps = np.maximum(
        np.min(aa, axis=0) - np.max(bb, axis=0), np.min(bb, axis=0) - np.max(aa, axis=0)
    )
    return float(np.max(gaps))


def ego_box(state, dimensions):
    return [state[0], state[1], dimensions[0], dimensions[1], state[2]]


def obstacles(geometry):
    return [[b[0], -b[1], b[3], b[4], -b[6]] for b in geometry["obstacles"]]


def sweep_clear(a, b, dimensions, boxes, plan):
    radius = math.hypot(*dimensions[:2]) / 2
    n = plan["sweep_subdivisions"]
    delta = np.asarray(b[:3]) - np.asarray(a[:3])
    if abs(delta[2]) > math.pi:
        return False
    bound = math.hypot(*delta[:2]) / (2 * n) + 2 * radius * math.sin(abs(delta[2]) / (4 * n))
    for k in range(n):
        mid = np.asarray(a[:3]) + delta * ((k + 0.5) / n)
        rectangle = [mid[0], mid[1], dimensions[0], dimensions[1], mid[2]]
        if any(separation(rectangle, obj) <= bound + plan["foreground_margin"] for obj in boxes):
            return False
    return True


def route_outcome(state, route):
    distances = np.linalg.norm(np.asarray(route) - [state[1], state[0]], axis=1)
    nearest = int(np.argmin(distances))
    return dict(
        rc=(nearest + 1) / (0.9 * len(route)), distance=float(distances[nearest]), nearest=nearest
    )
