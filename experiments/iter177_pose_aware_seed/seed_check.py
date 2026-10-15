"""Independent polynomial coefficients; imports neither seed nor generator."""

import math

from experiments.iter153_action_feasibility.check import near
from experiments.iter169_full_horizon_control.check import variables
from experiments.iter173_matched_connector_cost.check import expected_proposal
from .common import require


def expected_seed(reset, task):
    if task["wait_until"] or task["stop_from"] is not None:
        return expected_proposal(reset, task, 0)
    target, n = task["target"], task["terminal_frame"]
    duration = n/4
    sx, sy = target[0]-reset[0], target[1]-reset[1]
    dx = sx*math.cos(reset[2])+sy*math.sin(reset[2])
    dy = sy*math.cos(reset[2])-sx*math.sin(reset[2])
    theta = math.remainder(target[2]-reset[2], 2*math.pi)
    v, delta = reset[3:]
    s1 = n*(n+1)/2
    s2 = n*(n+1)*(2*n+1)/6
    s3 = s1*s1
    s4 = n*(n+1)*(2*n+1)*(3*n*n+3*n-1)/30
    gain = s1/16
    acceleration = (gain*(dx-v*duration)+duration*(target[3]-v)/4) / (
        gain*gain+duration*duration/4)
    acceleration = min(2, (6-v)/duration, max(-2, -v/duration, acceleration))
    b = acceleration/4
    sv, sjv = n*v+b*s1, v*s1+b*s2
    cross = (sv*sv-(n*v*v+2*v*b*s1+b*b*s2))/2
    cross_j = v*v*(s2-s1)/2+v*b*(5*s3-6*s2+s1)/6+b*b*(2*s4-3*s3+s2)/6
    tangent = math.tan(delta)
    derivative = 1+tangent*tangent
    y0, t0 = tangent*cross/(16*2.7), tangent*sv/(4*2.7)
    gy, gt = derivative*cross_j/(64*2.7), derivative*sjv/(16*2.7)
    rate = (gy*(dy-y0)+4*gt*(theta-t0)+4*duration*(target[4]-delta)) / (
        gy*gy+4*gt*gt+4*duration*duration)
    rate = min(math.pi/12, (math.pi/3-delta)/duration,
               max(-math.pi/12, (-math.pi/3-delta)/duration, rate))
    return [acceleration/2 if k == 0 else rate/(math.pi/12) for _, k in variables(task)]


def proposal_check(events, reset, task, limit, result):
    requests = [row for row in events if row["kind"] == "request"]
    require(len(requests) <= limit and not result["optimizer"]["started"], "forward_scope")
    for index, request in enumerate(requests):
        require(request["caller"] == ("initial" if index == 0 else "forward_proposal"),
                "proposal_caller")
        expected = expected_seed(reset, task) if index == 0 else expected_proposal(reset, task, index)
        near(request["values"], expected, 2e-14 if index == 0 else 2e-15)
