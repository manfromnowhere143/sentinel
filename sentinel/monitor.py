"""Sentinel runtime collision-risk monitor.

A label-free, introspective monitor that reads a *frozen* end-to-end planner's own ego-BEV outputs
and scores the risk that the current plan ends in a collision — using only what the planner already
publishes (its planned trajectory, detected objects, detection confidences, and its own multimodal
motion forecasts). No ground truth, no privileged simulator state.

The signal (pre-registered in experiments/iter2_monitor/HYPOTHESIS.md):

    risk = max over agents a, forecast modes m, horizon steps t of
             w(a, m) * proximity( ego_plan(t), agent_forecast(a, m, t) )

where `proximity` rises as the predicted ego-agent gap closes below a physical collision margin,
and `w` weights by detection confidence and by multimodal disagreement (the PerceptionProof insight:
a forecast that is both near the ego path and internally uncertain is the imminent-failure tell).

Pure functions, no torch/model dependency — unit-testable on synthetic geometry and replayable on
logged outputs for the G1 gate before any intervention is built.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import List, Optional, Sequence


# ---- physical constants (ego BEV frame, metres) -------------------------------------------------

# Half-extents (approx) for a passenger ego + a generic vehicle target, plus a safety buffer.
# proximity crosses its midpoint at roughly "bumpers touching + buffer".
EGO_HALF_LENGTH = 2.4
EGO_HALF_WIDTH = 1.0
DEFAULT_TARGET_HALF_EXTENT = 1.4
SAFETY_BUFFER = 0.6

# Planner output cadence. UniAD plans at 2 Hz; future_trajs are 12 steps. We compare them on the
# overlapping horizon at matched time, taking the shorter of the two.
PLAN_DT = 0.5  # seconds between ego plan waypoints


@dataclass
class AgentForecast:
    """One detected agent and the planner's own multimodal forecast of its future.

    Coordinates are in the ego BEV frame, matching the inference server's `aux_outputs`.
    """

    score: float  # detection confidence in [0, 1]
    half_extent: float  # approx radius of the agent footprint (m)
    modes: List[List[Sequence[float]]]  # M modes x T steps x (x, y)


@dataclass
class RiskBreakdown:
    """Risk plus the term attributions used for the ablation (engine: attribute *why*)."""

    risk: float
    proximity_only: float
    min_predicted_gap: float  # metres; the closest predicted ego-agent approach over the horizon
    worst_agent: int = -1
    worst_mode: int = -1
    worst_step: int = -1
    n_agents: int = 0
    extras: dict = field(default_factory=dict)


def _mode_disagreement(modes: List[List[Sequence[float]]]) -> float:
    """Spread of an agent's forecast modes at their endpoints, normalised to ~[0, 1].

    High when the planner's own 6 modes fan out (it is unsure where the agent goes) — the
    label-free uncertainty term. Zero when all modes agree (or only one mode exists).
    """
    endpoints = [m[-1] for m in modes if len(m) > 0]
    if len(endpoints) < 2:
        return 0.0
    cx = sum(p[0] for p in endpoints) / len(endpoints)
    cy = sum(p[1] for p in endpoints) / len(endpoints)
    spread = sum(hypot(p[0] - cx, p[1] - cy) for p in endpoints) / len(endpoints)
    # squash: ~5 m of endpoint spread saturates toward 1
    return spread / (spread + 5.0)


def _proximity(gap: float, collision_margin: float) -> float:
    """Map a predicted ego-agent centre gap (m) to a [0, 1] proximity risk.

    1 when the predicted gap is at/under the collision margin, decaying smoothly outward over a few
    metres. Monotonic, bounded, no tuning beyond the physical margin.
    """
    over = gap - collision_margin
    if over <= 0.0:
        return 1.0
    # exponential-ish soft decay; ~half at margin + 2 m, near 0 by margin + ~6 m
    return max(0.0, 1.0 - over / 6.0)


def compute_risk(
    trajectory: Sequence[Sequence[float]],
    agents: Sequence[AgentForecast],
    *,
    use_confidence: bool = True,
    use_disagreement: bool = True,
    min_score: float = 0.2,
    horizon: Optional[int] = None,
) -> RiskBreakdown:
    """Predicted-collision risk for one frame, from the frozen planner's own outputs.

    Args:
        trajectory: ego planned waypoints, ego BEV frame, list of (x, y).
        agents: detected agents with confidence, footprint, and multimodal forecasts.
        use_confidence / use_disagreement: term switches for the ablation.
        min_score: ignore detections below this confidence (the planner itself is unsure they exist).

    Returns:
        RiskBreakdown with the scalar risk in [0, 1], the proximity-only risk, the closest predicted
        gap, and the worst (agent, mode, step) for inspection.
    """
    ego = [(float(p[0]), float(p[1])) for p in trajectory]
    out = RiskBreakdown(risk=0.0, proximity_only=0.0, min_predicted_gap=float("inf"),
                        n_agents=len(agents))
    if not ego:
        out.min_predicted_gap = float("nan")
        return out

    for ai, a in enumerate(agents):
        if a.score < min_score or not a.modes:
            continue
        margin = EGO_HALF_WIDTH + a.half_extent + SAFETY_BUFFER
        disagree = _mode_disagreement(a.modes) if use_disagreement else 0.0
        conf = a.score if use_confidence else 1.0
        # weight: confidence gates whether to trust the detection; disagreement *raises* concern.
        weight = conf * (1.0 + disagree)

        for mi, mode in enumerate(a.modes):
            h = min(len(ego), len(mode))
            if horizon is not None:
                h = min(h, horizon)
            for t in range(h):
                ex, ey = ego[t]
                ax, ay = float(mode[t][0]), float(mode[t][1])
                gap = hypot(ex - ax, ey - ay)
                if gap < out.min_predicted_gap:
                    out.min_predicted_gap = gap
                prox = _proximity(gap, margin)
                if prox <= 0.0:
                    continue
                r = weight * prox
                out.proximity_only = max(out.proximity_only, prox)
                if r > out.risk:
                    out.risk = r
                    out.worst_agent, out.worst_mode, out.worst_step = ai, mi, t

    # weight can exceed 1 via the disagreement multiplier; clamp the reported risk to [0, 1].
    out.risk = min(1.0, out.risk)
    return out


def emergency_brake(
    current_speed: float,
    n_points: int,
    *,
    dt: float = PLAN_DT,
    decel: float = 4.0,
    heading: Optional[Sequence[float]] = None,
) -> List[List[float]]:
    """A kinematic comfort-bounded emergency-brake trajectory in the ego BEV frame.

    Decelerates from `current_speed` at `decel` m/s^2 along the current heading (default +x, the
    ego-forward axis in this BEV convention), returning `n_points` cumulative (x, y) waypoints. Once
    stopped, the ego holds position. This is the safe fallback the monitor substitutes for the
    planner's trajectory when risk > theta.
    """
    hx, hy = (1.0, 0.0) if heading is None else (float(heading[0]), float(heading[1]))
    norm = hypot(hx, hy) or 1.0
    hx, hy = hx / norm, hy / norm

    pts: List[List[float]] = []
    dist = 0.0
    speed = max(0.0, float(current_speed))
    for _ in range(n_points):
        speed = max(0.0, speed - decel * dt)
        dist += speed * dt
        pts.append([hx * dist, hy * dist])
    return pts


def speed_from_canbus_or_traj(trajectory: Sequence[Sequence[float]], dt: float = PLAN_DT) -> float:
    """Estimate current ego speed (m/s) from the first step of its own planned trajectory."""
    if len(trajectory) < 1:
        return 0.0
    x0, y0 = float(trajectory[0][0]), float(trajectory[0][1])
    return hypot(x0, y0) / dt
