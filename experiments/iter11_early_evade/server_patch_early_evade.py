import subprocess
SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/server.py'], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter11: EARLY kinematic collision-course detection -> time-gated evade / stop ----
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_risk.jsonl")
_sentinel_run = {"i": -1, "mode": None, "evade_dir": 1.0, "spd": 8.0}
_sentinel_track = {}


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["mode"] = None
    _sentinel_run["evade_dir"] = 1.0
    _sentinel_run["spd"] = 8.0
    _sentinel_track.clear()
    try:
        with open(_SENTINEL_LOG, "a") as f:
            f.write(_sjson.dumps({"reset": True, "run": _sentinel_run["i"]}) + "\\n")
    except Exception:
        pass


def _sentinel_log(out, ts):
    try:
        aux = out.aux_outputs.to_json()
        with open(_SENTINEL_LOG, "a") as f:
            f.write(_sjson.dumps({"run": _sentinel_run["i"], "ts": int(ts),
                                  "traj": [[float(x), float(y)] for x, y in out.trajectory.tolist()],
                                  "objs": aux.get("objects_in_bev"), "scores": aux.get("object_scores")}) + "\\n")
    except Exception:
        pass


def _brake_stop(base):
    return [[0.0, 0.0] for _ in range(len(base))]


def _evade_lanechange(base, evade_dir, speed):
    # completable lane change: keep forward progress, ramp lateral to the clear side over ~2 s.
    # only issued when detection was EARLY (enough lead time for this to finish before contact).
    lat_max = float(_sos.environ.get("SENTINEL_EVADE_LAT", "3.5"))
    keep = float(_sos.environ.get("SENTINEL_EVADE_KEEP", "0.9"))  # fraction of forward speed retained
    ramp = float(_sos.environ.get("SENTINEL_EVADE_RAMP", "2.0"))  # seconds to reach full lateral
    dt = 0.5
    pts = []
    dist = 0.0
    for k in range(len(base)):
        t = (k + 1) * dt
        dist += speed * keep * dt
        lat = evade_dir * lat_max * min(1.0, t / ramp)
        pts.append([dist, lat])
    return pts


def _sentinel_intervene(out, data):
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
        contact = float(_sos.environ.get("SENTINEL_CONTACT_MARGIN", "2.0"))
        horizon_s = float(_sos.environ.get("SENTINEL_HORIZON_S", "4.0"))
        evade_on = _sos.environ.get("SENTINEL_EVADE", "0") == "1"
        t_evade_min = float(_sos.environ.get("SENTINEL_T_EVADE_MIN", "1.5"))
        max_gap = float(_sos.environ.get("SENTINEL_MAXGAP", "35.0"))
        min_score = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
        min_close = float(_sos.environ.get("SENTINEL_MIN_CLOSING", "2.0"))
        dt = 0.5
        nH = int(round(horizon_s / dt))
        aux = out.aux_outputs.to_json()
        objs = aux.get("objects_in_bev") or []
        scores = aux.get("object_scores") or []
        ids = aux.get("object_ids") or []
        e2w = _np.array(data.ego2world, dtype=float)
        ts = int(data.timestamp)
        ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
        # ego velocity (world frame) from the plan's first step, rotated out of the ego frame
        vxl, vyl = (base[0][0] / dt, base[0][1] / dt) if base else (0.0, 0.0)
        ego_vwx = e2w[0][0] * vxl + e2w[0][1] * vyl
        ego_vwy = e2w[1][0] * vxl + e2w[1][1] * vyl
        cur_speed = _smath.hypot(vxl, vyl)

        def ego_world(t):
            return (ego_wx + ego_vwx * t, ego_wy + ego_vwy * t)

        min_app = 1e9
        t_star = 1e9
        left_clear = 99.0
        right_clear = 99.0
        newtrack = {}
        for i in range(min(len(objs), len(scores))):
            if scores[i] is None or scores[i] < min_score:
                continue
            ox, oy = float(objs[i][0]), float(objs[i][1])
            if _smath.hypot(ox, oy) > max_gap:
                continue
            if -5.0 < ox < 30.0:
                if oy > 0.5:
                    left_clear = min(left_clear, _smath.hypot(ox, oy))
                elif oy < -0.5:
                    right_clear = min(right_clear, _smath.hypot(ox, oy))
            wp = e2w @ _np.array([ox, oy, 0.0, 1.0])
            wx, wy = float(wp[0]), float(wp[1])
            oid = ids[i] if i < len(ids) else ("idx_%d" % i)
            newtrack[oid] = (wx, wy, ts)
            avx = avy = 0.0
            if oid in _sentinel_track:
                pwx, pwy, pts_ = _sentinel_track[oid]
                dta = (ts - pts_) / 1e6
                if dta > 1e-3:
                    avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
            speed_ag = _smath.hypot(avx, avy)
            if speed_ag < min_close:
                continue  # not moving enough to be a driven threat
            # kinematic closest approach over the long horizon: ego (current velocity) vs agent (tracked)
            for k in range(nH):
                t = (k + 1) * dt
                ex, ey = ego_world(t)
                ax, ay = wx + avx * t, wy + avy * t
                d = _smath.hypot(ex - ax, ey - ay)
                if d < min_app:
                    min_app = d
                    t_star = t
        _sentinel_track.clear()
        _sentinel_track.update(newtrack)

        if _sentinel_run.get("mode") is None and min_app < contact:
            # a real collision course is predicted. act with the maneuver the lead time allows.
            if evade_on and t_star >= t_evade_min:
                _sentinel_run["mode"] = "evade_early"
                _sentinel_run["evade_dir"] = 1.0 if left_clear >= right_clear else -1.0
                _sentinel_run["spd"] = cur_speed
            else:
                _sentinel_run["mode"] = "stop"

        mode = _sentinel_run.get("mode")
        if mode:
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"act": mode, "run": _sentinel_run["i"], "dir": _sentinel_run["evade_dir"],
                                          "min_app": round(min_app, 2), "t_star": round(t_star, 2)}) + "\\n")
            except Exception:
                pass
            if mode == "evade_early":
                return _evade_lanechange(base, _sentinel_run["evade_dir"], _sentinel_run["spd"])
            return _brake_stop(base)
    except Exception as e:
        try:
            with open(_SENTINEL_LOG, "a") as f:
                f.write(_sjson.dumps({"intervene_err": str(e)}) + "\\n")
        except Exception:
            pass
    return base


'''

anchor = '@app.get("/alive")'
assert anchor in src
src = src.replace(anchor, HELPERS + anchor, 1)
infer_old = ("    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
             "    return InferenceOutputs(\n"
             "        trajectory=uniad_output.trajectory.tolist(),")
infer_new = ("    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
             "    _sentinel_log(uniad_output, data.timestamp)\n"
             "    return InferenceOutputs(\n"
             "        trajectory=_sentinel_intervene(uniad_output, data),")
assert infer_old in src
src = src.replace(infer_old, infer_new, 1)
reset_old = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
reset_new = "async def reset_runner() -> bool:\n    _sentinel_reset()\n    uniad_runner.reset()"
assert reset_old in src
src = src.replace(reset_old, reset_new, 1)
open(SRV, "w").write(src)
print("FULL_EARLY_EVADE_PATCHED")
