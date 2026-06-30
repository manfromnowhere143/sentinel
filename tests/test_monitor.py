"""Unit tests for the Sentinel collision-risk monitor — synthetic ego-BEV geometry.

These pin the monitor's behaviour independent of UniAD/NeuroNCAP, so the G1 replay and the A/B run
test integration, not arithmetic.
"""

from sentinel.monitor import (
    AgentForecast,
    compute_risk,
    emergency_brake,
    speed_from_canbus_or_traj,
)


def _straight_ego(n=6, step=4.0):
    """Ego drives forward along +x at `step` m per waypoint."""
    return [[step * (t + 1), 0.0] for t in range(n)]


def test_head_on_collision_is_high_risk():
    """An agent whose own forecast crosses the ego's planned path => risk near 1."""
    ego = _straight_ego()
    # agent ahead, forecast marches back toward the ego along -x, overlapping the ego path.
    mode = [[20.0 - 3.5 * t, 0.0] for t in range(6)]
    agents = [AgentForecast(score=0.9, half_extent=1.4, modes=[mode])]
    out = compute_risk(ego, agents)
    assert out.risk > 0.8
    assert out.min_predicted_gap < 2.0


def test_far_agent_is_low_risk():
    """An agent off to the side, forecast staying away => risk near 0."""
    ego = _straight_ego()
    mode = [[5.0, 30.0 + t] for t in range(6)]  # 30 m to the side and receding
    agents = [AgentForecast(score=0.9, half_extent=1.4, modes=[mode])]
    out = compute_risk(ego, agents)
    assert out.risk < 0.1


def test_low_confidence_detection_is_ignored():
    """A would-be collision the planner barely believes (low score) is gated out by min_score."""
    ego = _straight_ego()
    mode = [[20.0 - 3.5 * t, 0.0] for t in range(6)]
    agents = [AgentForecast(score=0.05, half_extent=1.4, modes=[mode])]
    out = compute_risk(ego, agents)
    assert out.risk == 0.0


def test_disagreement_raises_risk_vs_proximity_only():
    """Two agents at the same closest approach: the one with fanned-out modes scores higher."""
    ego = _straight_ego()
    # tight: all three modes identical, grazing the ego path.
    graze = [[12.0, 2.6] for _ in range(6)]
    tight = AgentForecast(score=0.8, half_extent=1.4, modes=[graze, graze, graze])
    # fanned: same mean endpoint, but modes spread widely.
    fan = AgentForecast(
        score=0.8,
        half_extent=1.4,
        modes=[[[12.0, 2.6]] * 6, [[12.0, 8.0]] * 6, [[12.0, -3.0]] * 6],
    )
    r_tight = compute_risk(ego, [tight]).risk
    r_fan = compute_risk(ego, [fan]).risk
    assert r_fan > r_tight


def test_disagreement_switch_off_makes_them_equal():
    """With the disagreement term disabled, the ablation collapses the two cases together."""
    ego = _straight_ego()
    graze = [[12.0, 2.6] for _ in range(6)]
    tight = AgentForecast(score=0.8, half_extent=1.4, modes=[graze, graze, graze])
    fan = AgentForecast(
        score=0.8, half_extent=1.4,
        modes=[[[12.0, 2.6]] * 6, [[12.0, 8.0]] * 6, [[12.0, -3.0]] * 6],
    )
    r_tight = compute_risk(ego, [tight], use_disagreement=False).risk
    r_fan = compute_risk(ego, [fan], use_disagreement=False).risk
    assert abs(r_fan - r_tight) < 1e-9


def test_no_agents_is_zero_risk():
    assert compute_risk(_straight_ego(), []).risk == 0.0


def test_emergency_brake_decelerates_and_stops():
    """Brake waypoints advance monotonically, with shrinking gaps, then hold once stopped."""
    pts = emergency_brake(current_speed=10.0, n_points=6, dt=0.5, decel=4.0)
    xs = [p[0] for p in pts]
    # monotonic non-decreasing forward distance
    assert all(xs[i + 1] >= xs[i] - 1e-9 for i in range(len(xs) - 1))
    # step sizes shrink (decelerating)
    steps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    assert all(steps[i + 1] <= steps[i] + 1e-9 for i in range(len(steps) - 1))
    # comes to rest within the horizon (10 m/s, 4 m/s^2 -> ~2.5 s < 3 s)
    assert steps[-1] < 1e-6


def test_emergency_brake_already_stopped_holds():
    pts = emergency_brake(current_speed=0.0, n_points=6)
    assert all(abs(p[0]) < 1e-9 and abs(p[1]) < 1e-9 for p in pts)


def test_speed_estimate_from_trajectory():
    # first waypoint 2 m ahead at dt=0.5 s -> 4 m/s
    assert abs(speed_from_canbus_or_traj([[2.0, 0.0]], dt=0.5) - 4.0) < 1e-9
