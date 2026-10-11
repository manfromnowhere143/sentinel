"""Independent scalar geometry; imports no native producer, torch, scipy or simulator."""

import math
import struct

CORNERS = (
    (0.5, 0, 0.5),
    (0.5, 0, -0.5),
    (0.5, 1, 0.5),
    (0.5, 1, -0.5),
    (-0.5, 0, -0.5),
    (-0.5, 0, 0.5),
    (-0.5, 1, -0.5),
    (-0.5, 1, 0.5),
)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def finite_rows(rows, width):
    if any(len(r) != width or any(not math.isfinite(float(v)) for v in r) for r in rows):
        raise ValueError("nonfinite_or_shape")


def vertices(position, yaw, dimensions=(1.6, 1.5, 3.0)):
    finite_rows([position, dimensions], 3)
    if not math.isfinite(yaw) or min(dimensions) <= 0:
        raise ValueError("pose_or_dimensions")
    c, s = math.cos(yaw), math.sin(yaw)
    result = []
    for a, b, d in CORNERS:
        x, y, z = a * dimensions[0], b * dimensions[1], d * dimensions[2]
        result.append(
            [
                f32(c * x + s * z + position[0]),
                f32(y + position[1]),
                f32(-s * x + c * z + position[2]),
            ]
        )
    return result


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def count_points(points, box, factor=64):
    """Strict projections in binary64 on retained binary32 box/point inputs."""
    finite_rows(box, 3)
    if len(box) != 8 or factor != 64:
        raise ValueError("box_or_factor")
    origin = box[0]
    edges = [[f32(box[j][i] - origin[i]) for i in range(3)] for j in (1, 2, 5)]
    if any(dot(e, e) <= 1e-12 for e in edges):
        raise ValueError("degenerate_box")
    if any(
        abs(dot(edges[i], edges[j]))
        > 1e-5 * math.sqrt(dot(edges[i], edges[i]) * dot(edges[j], edges[j]))
        for i in range(3)
        for j in range(i)
    ):
        raise ValueError("nonorthogonal_box")
    # Check every unused corner: a shuffled/skewed box must not silently change the region.
    sums = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 1), (0, 0, 1), (1, 1, 1), (0, 1, 1))
    for row, factors in zip(box, sums):
        expected = [origin[i] + sum(factors[j] * edges[j][i] for j in range(3)) for i in range(3)]
        if max(abs(row[i] - expected[i]) for i in range(3)) > 2e-5:
            raise ValueError("box_corner_order")
    bounds = [(dot(origin, e), dot(box[j], e)) for j, e in zip((1, 2, 5), edges)]
    mask, ambiguous, certain_in, possible_in = [], [], 0, 0
    minimum_margin = math.inf
    for index, p in enumerate(points):
        if len(p) != 3 or not all(math.isfinite(float(v)) for v in p):
            raise ValueError("invalid_point")
        inside, definite_inside, definite_outside = True, True, False
        for j, (e, (low, high)) in enumerate(zip(edges, bounds)):
            projection = dot(p, e)
            margin = min(projection - low, high - projection)
            magnitude = max(
                1.0,
                sum(abs(float(p[i]) * e[i]) for i in range(3)),
                sum(abs(origin[i] * e[i]) for i in range(3)),
                sum(abs(box[(1, 2, 5)[j]][i] * e[i]) for i in range(3)),
            )
            band = factor * (2**-24) * magnitude
            inside &= margin > 0
            definite_inside &= margin > band
            definite_outside |= margin < -band
            minimum_margin = min(minimum_margin, abs(margin))
        mask.append(bool(inside))
        certain_in += bool(definite_inside)
        possible_in += not definite_outside
        if not definite_inside and not definite_outside:
            ambiguous.append(index)
    count = sum(mask)
    return dict(
        count=count,
        collision=count > 100,
        mask=mask,
        ambiguous=ambiguous,
        certain_inside=certain_in,
        possible_inside=possible_in,
        minimum_absolute_projection_margin=minimum_margin if len(mask) else None,
    )


def inverse4(matrix):
    finite_rows(matrix, 4)
    if len(matrix) != 4:
        raise ValueError("ground_shape")
    a = [
        [float(v) for v in row] + [float(i == j) for j in range(4)] for i, row in enumerate(matrix)
    ]
    for i in range(4):
        pivot = max(range(i, 4), key=lambda j: abs(a[j][i]))
        if abs(a[pivot][i]) < 1e-14:
            raise ValueError("singular_ground")
        a[i], a[pivot] = a[pivot], a[i]
        scale = a[i][i]
        a[i] = [v / scale for v in a[i]]
        for j in range(4):
            if j != i:
                scale = a[j][i]
                a[j] = [v - scale * w for v, w in zip(a[j], a[i])]
    return [r[4:] for r in a]


def ground_height(poses, u, v):
    if not len(poses) or not math.isfinite(u) or not math.isfinite(v):
        raise ValueError("ground_input")
    index = min(
        range(len(poses)), key=lambda j: (poses[j][0][3] - u) ** 2 + (poses[j][2][3] - v) ** 2
    )
    pose = poses[index]
    inv = inverse4(pose)
    local = [sum(inv[i][j] * value for j, value in enumerate((u, 0, v, 1))) for i in range(3)]
    local[1] = 0
    height = sum(pose[1][j] * local[j] for j in range(3)) + pose[1][3]
    return float(height), index
