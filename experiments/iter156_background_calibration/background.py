"""Full-population background queries for source-predicate calibration.

This is a privileged offline model, not a deployed monitor or physical occupancy
model. It deliberately scans every selected point. Vectorization changes cost,
not the population, strict boundaries, or native >100 collision threshold.
"""

from dataclasses import dataclass
import hashlib
import math

import numpy as np

MAX_POINTS = 2_000_000
FACTOR = 64
THRESHOLD = 100


@dataclass(frozen=True)
class BackgroundQuery:
    count: int
    predicate_collision: bool
    certain_inside: int
    possible_inside: int
    ambiguous_points: int
    decision: str
    mask: np.ndarray
    ambiguous: np.ndarray
    minimum_absolute_projection_margin: float | None
    population_sha256: str


def _sum3(products):
    # No BLAS reduction or fused dot: preserve the scalar oracle's add order.
    return (products[..., 0] + products[..., 1]) + products[..., 2]


def _box_planes(box):
    if not isinstance(box, np.ndarray) or box.dtype != np.dtype("<f4"):
        raise ValueError("box_dtype")
    if box.shape != (8, 3) or not np.isfinite(box).all():
        raise ValueError("box_shape_or_values")
    b = box.astype(np.float64)
    origin = b[0]
    # Native edge subtraction rounds to binary32 before scalar projections.
    edges = (b[[1, 2, 5]] - origin).astype(np.float32).astype(np.float64)
    if not np.isfinite(edges).all():
        raise ValueError("box_edge_values")
    norm2 = _sum3(edges * edges)
    if np.any(norm2 <= 1e-12):
        raise ValueError("degenerate_box")
    for i in range(3):
        for j in range(i):
            if abs(float(_sum3(edges[i] * edges[j]))) > 1e-5 * math.sqrt(
                float(norm2[i] * norm2[j])
            ):
                raise ValueError("nonorthogonal_box")
    weights = np.array(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 1), (0, 0, 1), (1, 1, 1), (0, 1, 1)],
        dtype=np.float64,
    )
    reconstructed = origin + weights @ edges
    if np.max(np.abs(b - reconstructed)) > 2e-5:
        raise ValueError("box_corner_order")
    lower = _sum3(origin * edges)
    upper = _sum3(b[[1, 2, 5]] * edges)
    magnitude = np.maximum(
        1.0, np.maximum(_sum3(np.abs(origin * edges)), _sum3(np.abs(b[[1, 2, 5]] * edges)))
    )
    return edges, lower, upper, magnitude


class BackgroundPopulation:
    """Owned immutable copy; caller changes cannot silently change the scene."""

    def __init__(self, points, expected_sha256):
        if (
            not isinstance(points, np.ndarray)
            or points.dtype != np.dtype("<f4")
            or points.ndim != 2
            or points.shape[1:] != (3,)
            or len(points) > MAX_POINTS
            or not np.isfinite(points).all()
        ):
            raise ValueError("point_population")
        if (
            not isinstance(expected_sha256, str)
            or len(expected_sha256) != 64
            or any(c not in "0123456789abcdef" for c in expected_sha256)
        ):
            raise ValueError("population_identity_encoding")
        raw = np.ascontiguousarray(points).tobytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_sha256:
            raise ValueError("population_identity")
        self.sha256 = actual
        # bytes-backed read-only arrays cannot be re-enabled with setflags.
        self._points = np.frombuffer(
            np.frombuffer(raw, dtype="<f4").astype("<f8").tobytes(), dtype="<f8"
        ).reshape(-1, 3)

    def query(self, box):
        edges, lower, upper, base_magnitude = _box_planes(box)
        n = len(self._points)
        inside = np.ones(n, dtype=bool)
        definite_inside = np.ones(n, dtype=bool)
        definite_outside = np.zeros(n, dtype=bool)
        min_margin = math.inf
        # Three bounded N-by-3 temporary products; never an N-by-Q query tensor.
        for axis in range(3):
            products = self._points * edges[axis]
            projection = _sum3(products)
            margin = np.minimum(projection - lower[axis], upper[axis] - projection)
            band = FACTOR * 2**-24 * np.maximum(base_magnitude[axis], _sum3(np.abs(products)))
            inside &= margin > 0
            definite_inside &= margin > band
            definite_outside |= margin < -band
            if n:
                min_margin = min(min_margin, float(np.min(np.abs(margin))))
        ambiguous = np.flatnonzero(~definite_inside & ~definite_outside)
        count = int(np.count_nonzero(inside))
        certain = int(np.count_nonzero(definite_inside))
        possible = n - int(np.count_nonzero(definite_outside))
        # This is the retained diagnostic band, NOT a certified roundoff bound.
        # An uncertain threshold crossing must never become a clear result.
        decision = (
            "collision"
            if certain > THRESHOLD
            else ("clear" if possible <= THRESHOLD else "numerically_ambiguous")
        )
        return BackgroundQuery(
            count=count,
            predicate_collision=count > THRESHOLD,
            certain_inside=certain,
            possible_inside=possible,
            ambiguous_points=len(ambiguous),
            decision=decision,
            mask=inside,
            ambiguous=ambiguous,
            minimum_absolute_projection_margin=min_margin if n else None,
            population_sha256=self.sha256,
        )


def box_for_state(state, ground_poses):
    """State [forward, lateral, yaw, speed, steer] to source collision vertices."""
    state = np.asarray(state, dtype=np.float64)
    poses = np.asarray(ground_poses, dtype=np.float64)
    if state.shape != (5,) or not np.isfinite(state).all():
        raise ValueError("state")
    if poses.ndim != 3 or poses.shape[1:] != (4, 4) or not len(poses):
        raise ValueError("ground_shape")
    if not np.isfinite(poses).all():
        raise ValueError("ground_values")
    if not np.array_equal(poses[:, 3, :], np.tile([0, 0, 0, 1], (len(poses), 1))):
        raise ValueError("ground_affine")
    u, v = float(state[1]), float(state[0])
    distance = (poses[:, 0, 3] - u) ** 2 + (poses[:, 2, 3] - v) ** 2
    if not np.isfinite(distance).all():
        raise ValueError("ground_distance")
    nearest = int(np.argmin(distance))  # first index on a tie, as in native source
    pose = poses[nearest]
    try:
        local = np.linalg.solve(pose, np.array([u, 0.0, v, 1.0]))
    except np.linalg.LinAlgError as exc:
        raise ValueError("singular_ground") from exc
    local[1] = 0.0
    height = float(pose[1, :3] @ local[:3] + pose[1, 3])
    if not np.isfinite(local).all() or not math.isfinite(height):
        raise ValueError("ground_projection")
    corners = np.array(
        [
            (0.5, 0, 0.5),
            (0.5, 0, -0.5),
            (0.5, 1, 0.5),
            (0.5, 1, -0.5),
            (-0.5, 0, -0.5),
            (-0.5, 0, 0.5),
            (-0.5, 1, -0.5),
            (-0.5, 1, 0.5),
        ]
    ) * np.array([1.6, 1.5, 3.0])
    c, s = math.cos(float(state[2])), math.sin(float(state[2]))
    box = np.column_stack(
        (
            c * corners[:, 0] + s * corners[:, 2] + u,
            corners[:, 1] + height,
            -s * corners[:, 0] + c * corners[:, 2] + v,
        )
    )
    result = box.astype("<f4")
    if not np.isfinite(result).all():
        raise ValueError("box_projection")
    return result, height, nearest
