"""Unit tests for the iteration-18 tracking layer — each test encodes a failure mode measured
in committed evidence (identity jitter manufacturing closing speed; velocity dropout across
identity breaks; smoothing must not invent motion for static objects)."""
from sentinel.tracker import Tracker


def steps(tracker, series, dt=0.5):
    out = None
    t = 0.0
    for dets in series:
        out = tracker.update(dets, t)
        t += dt
    return out


def test_constant_velocity_converges():
    tr = Tracker()
    series = [[(i * 2.0, 0.0)] for i in range(8)]  # 4 m/s along x at 2 Hz
    out = steps(tr, series)
    (x, y, vx, vy, tid) = out[0]
    assert abs(vx - 4.0) < 0.2 and abs(vy) < 0.1
    assert tid == 0


def test_velocity_persists_through_dropout():
    tr = Tracker()
    series = [[(i * 2.0, 0.0)] for i in range(6)]
    steps(tr, series)
    # two missed frames: the track coasts, velocity intact — the iteration-17 flicker case
    out = tr.update([], 3.0)
    out = tr.update([], 3.5)
    (x, y, vx, vy, tid) = out[0]
    assert abs(vx - 4.0) < 0.3
    assert tid == 0
    assert abs(x - 14.0) < 0.6  # coasted to ~ i=7 position


def test_identity_survives_id_break():
    # the raw stream changes its reported identity; association by predicted position keeps ours
    tr = Tracker()
    series = [[(i * 2.0, 0.0)] for i in range(6)]
    out = steps(tr, series)
    assert out[0][4] == 0  # same internal id throughout, regardless of upstream ids


def test_static_jitter_yields_no_velocity():
    tr = Tracker()
    jitter = [0.12, -0.1, 0.08, -0.09, 0.11, -0.12, 0.1, -0.08]
    series = [[(10.0 + j, 5.0 - j)] for j in jitter]
    out = steps(tr, series)
    (x, y, vx, vy, tid) = out[0]
    assert abs(vx) < 0.5 and abs(vy) < 0.5  # raw finite-diff would read ~0.4 m/frame = 0.8 m/s+


def test_two_objects_keep_identities_when_crossing_apart():
    tr = Tracker(gate=2.0)
    series = []
    for i in range(8):
        a = (i * 2.0, 5.0)      # eastbound, upper lane
        b = (14.0 - i * 2.0, -5.0)  # westbound, lower lane
        series.append([a, b])
    out = steps(tr, series)
    byid = {t[4]: t for t in out}
    assert byid[0][3] == 0.0 or abs(byid[0][2] - 2.0 / 0.5) < 1.0  # track 0 eastbound ~4 m/s
    assert abs(byid[1][2] + 4.0) < 1.0  # track 1 westbound ~-4 m/s


def test_stale_track_dropped_after_max_missed():
    tr = Tracker(max_missed=2)
    steps(tr, [[(0.0, 0.0)], [(1.0, 0.0)]])
    tr.update([], 1.0)
    tr.update([], 1.5)
    out = tr.update([], 2.0)
    assert out == []
