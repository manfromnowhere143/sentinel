"""One algebraic endpoint guess; full nonlinear rollout remains authoritative."""

import math

import numpy as np


def initial(controls):
    task, reset = controls.task, controls.reset
    if task["wait_until"] or task["stop_from"] is not None:
        return controls.initial()
    target = task["target"]
    n, h, length = task["terminal_frame"], .25, 2.7
    duration = n*h
    sx, sy = target[0]-reset[0], target[1]-reset[1]
    c, s = math.cos(reset[2]), math.sin(reset[2])
    dx, dy = c*sx+s*sy, -s*sx+c*sy
    heading = math.remainder(target[2]-reset[2], 2*math.pi)
    speed, steering = reset[3:]
    gain = h*h*n*(n+1)/2
    acceleration = (gain*(dx-speed*duration)+.25*duration*(target[3]-speed)) / (
        gain*gain+.25*duration*duration)
    acceleration = max(max(-2., -speed/duration),
                       min(min(2., (6-speed)/duration), acceleration))
    # Prefix sums for the discrete update: position uses heading before yaw update.
    total = weighted = cross = weighted_cross = 0.0
    for j in range(1, n+1):
        velocity = speed+acceleration*h*j
        cross += velocity*total
        weighted_cross += velocity*weighted
        total += velocity
        weighted += j*velocity
    tangent = math.tan(steering)
    derivative = 1+tangent*tangent
    y0, heading0 = tangent*h*h*cross/length, tangent*h*total/length
    by, bt = derivative*h**3*weighted_cross/length, derivative*h*h*weighted/length
    rate = (by*(dy-y0)+4*bt*(heading-heading0)+4*duration*(target[4]-steering)) / (
        by*by+4*bt*bt+4*duration*duration)
    rate = max(max(-math.pi/12, (-math.pi/3-steering)/duration),
               min(min(math.pi/12, (math.pi/3-steering)/duration), rate))
    return np.asarray([acceleration/2 if kind == 0 else rate/(math.pi/12)
                       for _, kind in controls.variables], dtype=float)
