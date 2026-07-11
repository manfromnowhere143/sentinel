#!/usr/bin/env python3
"""Patch UniAD server.py with released-union monitor plus exact Iter42 trace logging."""

import subprocess


SRV = "/opt/sentinel-stack/UniAD/inference/server.py"
subprocess.run(["git", "-C", "/opt/sentinel-stack/UniAD", "checkout", "--", "inference/server.py"], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter42: released union with exact replay trace ------------------------------------
# Decision rule is the iteration-15 released union. New behavior is trace logging only: every
# inference frame records the exact ego2world matrix and online decision state used by the monitor.
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_iter42_trace.jsonl")
_sentinel_run = {"i": -1, "frame": -1, "braking": False, "clear": 0}
_sentinel_track = {}


def _sentinel_jsonable(x):
    try:
        if hasattr(x, "tolist"):
            return x.tolist()
        if isinstance(x, (list, tuple)):
            return [_sentinel_jsonable(v) for v in x]
        if isinstance(x, dict):
            return {str(k): _sentinel_jsonable(v) for k, v in x.items()}
        if isinstance(x, (int, float, str, bool)) or x is None:
            return x
        return str(x)
    except Exception:
        return str(x)


def _sentinel_write(row):
    try:
        with open(_SENTINEL_LOG, "a") as f:
            f.write(_sjson.dumps(row, sort_keys=True) + "\\n")
    except Exception:
        pass


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["frame"] = -1
    _sentinel_run["braking"] = False
    _sentinel_run["clear"] = 0
    _sentinel_track.clear()
    _sentinel_write({"trace_version": "iter42_exact_trace_v1",
                     "reset": True, "run": _sentinel_run["i"]})


def _sentinel_intervene(out, data):
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    _sentinel_run["frame"] += 1
    try:
        cpa_margin = float(_sos.environ.get("SENTINEL_CPA_MARGIN", "1.5"))
        ttc_thresh = float(_sos.environ.get("SENTINEL_TTC", "2.5"))
        min_close = float(_sos.environ.get("SENTINEL_MIN_CLOSING", "3.0"))
        max_gap = float(_sos.environ.get("SENTINEL_MAXGAP", "30.0"))
        min_score = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
        release_k = int(_sos.environ.get("SENTINEL_RELEASE_K", "4"))
        dt = 0.5
        aux = out.aux_outputs.to_json()
        objs = aux.get("objects_in_bev") or []
        scores = aux.get("object_scores") or []
        ids = aux.get("object_ids") or []
        e2w = _np.array(data.ego2world, dtype=float)
        e2w_json = [[float(v) for v in row] for row in e2w.tolist()]
        ts = int(data.timestamp)
        pre_braking = bool(_sentinel_run.get("braking"))
        pre_clear = int(_sentinel_run.get("clear", 0))
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
                pwx, pwy, pts = _sentinel_track[oid]
                dta = (ts - pts) / 1e6
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
        release = False
        if fired:
            _sentinel_run["braking"] = True
            _sentinel_run["clear"] = 0
        elif _sentinel_run.get("braking"):
            _sentinel_run["clear"] += 1
            if _sentinel_run["clear"] >= release_k:
                _sentinel_run["braking"] = False
                _sentinel_run["clear"] = 0
                release = True
        brake = bool(_sentinel_run.get("braking"))
        _sentinel_write({
            "trace_version": "iter42_exact_trace_v1",
            "run": _sentinel_run["i"],
            "frame_index": _sentinel_run["frame"],
            "ts": ts,
            "traj": base,
            "objs": _sentinel_jsonable(objs),
            "scores": _sentinel_jsonable(scores),
            "object_ids": _sentinel_jsonable(ids),
            "ego2world": e2w_json,
            "params": {
                "SENTINEL_MIN_SCORE": min_score,
                "SENTINEL_MAXGAP": max_gap,
                "SENTINEL_CPA_MARGIN": cpa_margin,
                "SENTINEL_TTC": ttc_thresh,
                "SENTINEL_MIN_CLOSING": min_close,
                "SENTINEL_RELEASE_K": release_k,
            },
            "pre_braking": pre_braking,
            "pre_clear": pre_clear,
            "min_cpa": float(min_cpa),
            "min_ttc": float(min_ttc),
            "fired": bool(fired),
            "post_braking": bool(_sentinel_run.get("braking")),
            "post_clear": int(_sentinel_run.get("clear", 0)),
            "brake": brake,
            "release": bool(release),
        })
        if brake:
            return [[0.0, 0.0] for _ in range(len(base))]
    except Exception as e:
        _sentinel_write({"trace_version": "iter42_exact_trace_v1",
                         "trace_error": str(e), "run": _sentinel_run["i"],
                         "frame_index": _sentinel_run.get("frame", -1)})
    return base


'''

anchor = '@app.get("/alive")'
assert anchor in src
src = src.replace(anchor, HELPERS + anchor, 1)
infer_old = (
    "    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
    "    return InferenceOutputs(\n"
    "        trajectory=uniad_output.trajectory.tolist(),"
)
infer_new = (
    "    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
    "    return InferenceOutputs(\n"
    "        trajectory=_sentinel_intervene(uniad_output, data),"
)
assert infer_old in src
src = src.replace(infer_old, infer_new, 1)
reset_old = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
reset_new = "async def reset_runner() -> bool:\n    _sentinel_reset()\n    uniad_runner.reset()"
assert reset_old in src
src = src.replace(reset_old, reset_new, 1)
open(SRV, "w").write(src)
print("ITER42_UNION_TRACE_PATCHED")
