"""Analytic boundary controls for the separately labelled post-outcome audit."""

import math

from experiments.iter172_integrated_rrt.diagnostics import excluded_by_bounds


def test_straight_acceleration_reaches_optimistic_bound():
    before = [0, 0, 0, 2, 0]
    # Speeds 2.5, 3, 3.5, 4 over four quarter-second steps.
    assert excluded_by_bounds(before, [3.25, 0, 0, 4, 0], 4) == {}
    assert "position" in excluded_by_bounds(before, [3.29, 0, 0, 4, 0], 4)


def test_speed_cap_and_terminal_tolerances():
    before = [0, 0, 0, 6, 0]
    assert excluded_by_bounds(before, [12, 0, 0, 6, 0], 8) == {}
    assert "position" in excluded_by_bounds(before, [12.04, 0, 0, 6, 0], 8)
    assert "speed" in excluded_by_bounds(before, [0, 0, 0, 1.98, 0], 8)
    assert "speed" not in excluded_by_bounds(before, [0, 0, 0, 1.99, 0], 8)


def test_heading_wrap_and_steering_rate_are_distinct_bounds():
    before = [0, 0, math.pi - 0.05, 0, 0]
    assert excluded_by_bounds(before, [0, 0, -math.pi + 0.05, 0, 0], 1) == {}
    bad = excluded_by_bounds(before, [0, 0, 0, 0, 0.1], 1)
    assert set(bad) == {"heading", "steering"}
