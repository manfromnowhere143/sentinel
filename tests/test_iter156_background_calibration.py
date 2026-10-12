"""Adversarial synthetic qualification; no retained scene is opened here."""

from dataclasses import replace
import hashlib
import math

import numpy as np
import pytest

from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter155_background_witness.geometry import count_points, vertices


def population(points):
    points = np.asarray(points, dtype="<f4").reshape(-1, 3)
    return BackgroundPopulation(points, hashlib.sha256(points.tobytes()).hexdigest())


def box(position=(0, 0, 0), yaw=0):
    return np.array(vertices(position, yaw), dtype="<f4")


def verify(result, oracle):
    assert result.count == oracle["count"]
    assert result.predicate_collision == oracle["collision"]
    assert result.certain_inside == oracle["certain_inside"]
    assert result.possible_inside == oracle["possible_inside"]
    assert result.ambiguous_points == len(oracle["ambiguous"])
    np.testing.assert_array_equal(result.mask, oracle["mask"])
    np.testing.assert_array_equal(result.ambiguous, oracle["ambiguous"])


@pytest.mark.parametrize("yaw", [0, math.pi / 2, math.pi / 4, -2.4, 1e-6])
@pytest.mark.parametrize("position", [(0, 0, 0), (15, -0.2, 30), (-500, 2, 1)])
def test_random_full_masks_against_scalar(yaw, position):
    points = np.random.default_rng(156).uniform(-4, 4, (501, 3)) + position
    p = np.asarray(points, dtype="<f4")
    b = box(position, yaw)
    verify(population(p).query(b), count_points(p.tolist(), b.tolist()))


@pytest.mark.parametrize("n", [0, 1, 99, 100, 101, 273])
def test_strict_100_101(n):
    result = population([[0, 0.5, 0]] * n).query(box())
    assert result.count == n
    assert result.predicate_collision is (n > 100)
    assert result.decision == ("collision" if n > 100 else "clear")


def test_faces_edges_corners_are_not_interior():
    b = box()
    faces = [[0.8, 0.5, 0], [-0.8, 0.5, 0], [0, 0, 0], [0, 1.5, 0], [0, 0.5, 1.5], [0, 0.5, -1.5]]
    points = np.array(faces + b.tolist(), dtype="<f4")
    r = population(points).query(b)
    verify(r, count_points(points.tolist(), b.tolist()))
    assert r.count == 0
    assert r.ambiguous_points == len(points)


def test_ambiguous_threshold_crossing_does_not_become_clear():
    p = np.array([[0, 0.5, 0]] * 100 + [[0, 0, 0]], dtype="<f4")
    r = population(p).query(box())
    assert r.count == 100 and not r.predicate_collision
    assert r.certain_inside == 100 and r.possible_inside == 101
    assert r.decision == "numerically_ambiguous"
    verify(r, count_points(p.tolist(), box().tolist()))


def test_changed_population_or_hash_is_rejected():
    p = np.array([[0, 0.5, 0]] * 101, dtype="<f4")
    digest = hashlib.sha256(p.tobytes()).hexdigest()
    with pytest.raises(ValueError, match="population_identity"):
        BackgroundPopulation(p[:-1], digest)
    with pytest.raises(ValueError, match="population_identity_encoding"):
        BackgroundPopulation(p, digest.upper())


def test_caller_mutation_cannot_change_owned_population():
    p = np.array([[0, 0.5, 0]], dtype="<f4")
    scene = population(p)
    p[:] = 100
    assert scene.query(box()).count == 1
    with pytest.raises(ValueError):
        scene._points.setflags(write=True)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [[0, 0, 0]],
        np.zeros((3, 2), dtype="<f4"),
        np.zeros((3, 3), dtype="<f8"),
        np.array([[np.nan, 0, 0]], dtype="<f4"),
        np.array([[np.inf, 0, 0]], dtype="<f4"),
    ],
)
def test_invalid_points_never_become_zero(bad):
    with pytest.raises(ValueError, match="point_population"):
        BackgroundPopulation(bad, "0" * 64)


@pytest.mark.parametrize("fault", ["nan", "collapsed", "swap", "skew", "dtype"])
def test_invalid_box_rejected(fault):
    b = box()
    if fault == "nan":
        b[0, 0] = np.nan
    elif fault == "collapsed":
        b[1] = b[0]
    elif fault == "swap":
        b[[3, 6]] = b[[6, 3]]
    elif fault == "skew":
        b[2, 0] += 0.1
    else:
        b = b.astype("<f8")
    with pytest.raises(ValueError):
        population([[0, 0.5, 0]]).query(b)


def test_geometry_mapping_and_first_ground_tie():
    ground = np.repeat(np.eye(4)[None], 2, axis=0)
    ground[0, 1, 3] = 2
    ground[1, 1, 3] = 5
    state = [0, 0, 0.7, 2, 0]
    actual, height, index = box_for_state(state, ground)
    assert index == 0 and height == 2
    np.testing.assert_array_equal(actual, box((0, 2, 0), 0.7))


@pytest.mark.parametrize("fault", ["empty", "shape", "nan", "nonaffine", "singular", "state"])
def test_invalid_ground_never_becomes_clear(fault):
    ground = np.eye(4)[None].copy()
    state = [0, 0, 0, 0, 0]
    if fault == "empty":
        ground = ground[:0]
    elif fault == "shape":
        ground = ground[:, :3]
    elif fault == "nan":
        ground[0, 0, 0] = np.nan
    elif fault == "nonaffine":
        ground[0, 3, 3] = 2
    elif fault == "singular":
        ground[0, 0] = 0
    else:
        state[0] = np.nan
    with pytest.raises(ValueError):
        box_for_state(state, ground)


def test_scalar_checker_rejects_silent_favorable_pruning():
    p = np.array([[0, 0.5, 0]] * 101, dtype="<f4")
    r = population(p).query(box())
    oracle = count_points(p.tolist(), box().tolist())
    with pytest.raises(AssertionError):
        verify(replace(r, count=100, predicate_collision=False), oracle)
    faulty_mask = r.mask.copy()
    faulty_mask[-1] = False
    with pytest.raises(AssertionError):
        verify(replace(r, mask=faulty_mask), oracle)
