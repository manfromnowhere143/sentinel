import subprocess
SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/server.py'], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter16: the released union with a crawl instead of a full stop ---------------------
# Identical triggers, thresholds, and K-frame release to iteration 15; ONE change: while the latch
# is active, the returned trajectory is the planner's OWN current plan re-parameterized by arc
# length to SENTINEL_CRAWL_V m/s (path geometry untouched, never faster than the planner's plan),
# instead of the zero trajectory (full stop).
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_risk.jsonl")
_sentinel_run = {"i": -1, "braking": False, "clear": 0}
_sentinel_track = {}


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["braking"] = False
    _sentinel_run["clear"] = 0
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
                                  "objs": aux.get("objects_in_bev"), "scores": aux.get("object_scores"),
                                  "futs": aux.get("future_trajs")}) + "\\n")
    except Exception:
        pass


def _sentinel_crawl_traj(base, v, dt):
    """Re-parameterize the planner's plan by arc length to at most v m/s (never faster than
    the plan itself). Waypoint k sits on the plan's polyline at min(arclen_k, v*dt*k)."""
    pts = [(0.0, 0.0)] + [(float(p[0]), float(p[1])) for p in base]
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + _smath.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    for k in range(1, len(pts)):
        s = min(cum[k], v * dt * k)
        j = 1
        while j < len(cum) - 1 and cum[j] < s:
            j += 1
        seg = cum[j] - cum[j - 1]
        f = 0.0 if seg <= 1e-9 else max(0.0, min(1.0, (s - cum[j - 1]) / seg))
        out.append([pts[j - 1][0] + f * (pts[j][0] - pts[j - 1][0]),
                    pts[j - 1][1] + f * (pts[j][1] - pts[j - 1][1])])
    return out


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
        release_k = int(_sos.environ.get("SENTINEL_RELEASE_K", "4"))
        crawl_v = float(_sos.environ.get("SENTINEL_CRAWL_V", "2.0"))
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
        _sentinel_track.clear()
        _sentinel_track.update(newtrack)
        fired = min_cpa < cpa_margin or min_ttc < ttc_thresh
        if fired:
            _sentinel_run["braking"] = True
            _sentinel_run["clear"] = 0
        elif _sentinel_run.get("braking"):
            _sentinel_run["clear"] += 1
            if _sentinel_run["clear"] >= release_k:
                _sentinel_run["braking"] = False
                _sentinel_run["clear"] = 0
                try:
                    with open(_SENTINEL_LOG, "a") as f:
                        f.write(_sjson.dumps({"release": True, "run": _sentinel_run["i"],
                                              "cpa": round(min_cpa, 2), "ttc": round(min_ttc, 2)}) + "\\n")
                except Exception:
                    pass
        if _sentinel_run.get("braking"):
            crawl = _sentinel_crawl_traj(base, crawl_v, dt)
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"crawl": True, "run": _sentinel_run["i"],
                                          "cpa": round(min_cpa, 2), "ttc": round(min_ttc, 2),
                                          "clear": _sentinel_run["clear"]}) + "\\n")
            except Exception:
                pass
            return crawl
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
print("UNION_CRAWL_PATCHED")
