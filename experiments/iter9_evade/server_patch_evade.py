import subprocess
SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/server.py'], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter9: threat-aware response -- SIDE crossing -> stop; FRONTAL head-on -> evade -------
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_risk.jsonl")
_sentinel_run = {"i": -1, "mode": None, "evade_dir": -1.0}
_sentinel_track = {}


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["mode"] = None
    _sentinel_run["evade_dir"] = -1.0
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


def _evade(base, evade_dir):
    lat_max = float(_sos.environ.get("SENTINEL_EVADE_LAT", "4.0"))
    dt = 0.5
    pts = []
    for k, (px, py) in enumerate(base):
        t = (k + 1) * dt
        lat = evade_dir * lat_max * min(1.0, t / 1.5)
        pts.append([float(px) * 0.85, lat])
    return pts


def _sentinel_intervene(out, data):
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
        cpa_margin = float(_sos.environ.get("SENTINEL_CPA_MARGIN", "1.5"))
        ttc_thresh = float(_sos.environ.get("SENTINEL_TTC", "2.5"))
        min_close = float(_sos.environ.get("SENTINEL_MIN_CLOSING", "3.0"))
        max_gap = float(_sos.environ.get("SENTINEL_MAXGAP", "30.0"))
        min_score = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
        evade_on = _sos.environ.get("SENTINEL_EVADE", "0") == "1"
        dt = 0.5
        aux = out.aux_outputs.to_json()
        objs = aux.get("objects_in_bev") or []
        scores = aux.get("object_scores") or []
        ids = aux.get("object_ids") or []
        e2w = _np.array(data.ego2world, dtype=float)
        ts = int(data.timestamp)
        ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
        ego_world_plan = []
        for px, py in base:
            wp = e2w @ _np.array([px, py, 0.0, 1.0])
            ego_world_plan.append((float(wp[0]), float(wp[1])))
        H = len(ego_world_plan)
        min_cpa = 1e9
        min_ttc = 1e9
        ttc_agent_oy = 0.0
        newtrack = {}
        for i in range(min(len(objs), len(scores))):
            if scores[i] is None or scores[i] < min_score:
                continue
            ox, oy = float(objs[i][0]), float(objs[i][1])
            if _smath.hypot(ox, oy) > max_gap:
                continue
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
            for k in range(H):
                t = (k + 1) * dt
                ax, ay = wx + avx * t, wy + avy * t
                ex, ey = ego_world_plan[k]
                d = _smath.hypot(ex - ax, ey - ay)
                if d < min_cpa:
                    min_cpa = d
            dx, dy = ego_wx - wx, ego_wy - wy
            gapw = _smath.hypot(dx, dy)
            if gapw > 1e-3:
                closing = (avx * dx + avy * dy) / gapw
                if closing > max(min_close, 0.5):
                    ttc = gapw / closing
                    if ttc < min_ttc:
                        min_ttc = ttc
                        ttc_agent_oy = oy
        _sentinel_track.clear()
        _sentinel_track.update(newtrack)

        if _sentinel_run.get("mode") is None:
            if evade_on and min_ttc < ttc_thresh:
                _sentinel_run["mode"] = "evade"
                _sentinel_run["evade_dir"] = -1.0 if ttc_agent_oy > 0.0 else 1.0
            elif min_cpa < cpa_margin:
                _sentinel_run["mode"] = "stop"
            elif min_ttc < ttc_thresh:
                _sentinel_run["mode"] = "stop"

        mode = _sentinel_run.get("mode")
        if mode:
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"act": mode, "run": _sentinel_run["i"],
                                          "cpa": round(min_cpa, 2), "ttc": round(min_ttc, 2)}) + "\\n")
            except Exception:
                pass
            return _evade(base, _sentinel_run["evade_dir"]) if mode == "evade" else _brake_stop(base)
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
print("FULL_EVADE_PATCHED")
