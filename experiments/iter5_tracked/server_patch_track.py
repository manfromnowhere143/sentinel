import subprocess
SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/server.py'], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel: shadow logging + brake gated on OBSERVED (tracked) agent velocity --------------
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_risk.jsonl")
_sentinel_run = {"i": -1, "braking": False}
_sentinel_track = {}  # object_id -> (world_x, world_y, timestamp_us)


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["braking"] = False
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


def _sentinel_intervene(out, data):
    """Brake when an agent whose OBSERVED motion is toward the ego has low time-to-collision."""
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
        ttc_thresh = float(_sos.environ.get("SENTINEL_TTC", "2.5"))
        max_gap = float(_sos.environ.get("SENTINEL_MAXGAP", "25.0"))
        min_score = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
        min_close = float(_sos.environ.get("SENTINEL_MIN_CLOSING", "3.0"))
        track_vel = _sos.environ.get("SENTINEL_TRACK_VEL", "0") == "1"
        dt = 0.5
        aux = out.aux_outputs.to_json()
        objs = aux.get("objects_in_bev") or []
        scores = aux.get("object_scores") or []
        ids = aux.get("object_ids") or []
        futs = aux.get("future_trajs") or []
        ego = base
        ego_vx = ego[0][0] / dt if ego else 0.0
        ego_vy = ego[0][1] / dt if ego else 0.0
        e2w = _np.array(data.ego2world, dtype=float) if track_vel else None
        ts = int(data.timestamp)
        min_ttc = 1e9
        newtrack = {}
        for i in range(min(len(objs), len(scores))):
            if scores[i] is None or scores[i] < min_score:
                continue
            ox, oy = float(objs[i][0]), float(objs[i][1])
            gap = _smath.hypot(ox, oy)
            if gap > max_gap or gap < 1e-3:
                continue
            if track_vel and i < len(ids):
                # OBSERVED velocity: track this object's WORLD position across frames
                oid = ids[i]
                wp = e2w @ _np.array([ox, oy, 0.0, 1.0])
                wx, wy = float(wp[0]), float(wp[1])
                newtrack[oid] = (wx, wy, ts)
                closing = 0.0
                if oid in _sentinel_track:
                    pwx, pwy, pts = _sentinel_track[oid]
                    dta = (ts - pts) / 1e6
                    if dta > 1e-3:
                        awvx, awvy = (wx - pwx) / dta, (wy - pwy) / dta  # agent world velocity
                        ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
                        dx, dy = ego_wx - wx, ego_wy - wy
                        dn = _smath.hypot(dx, dy) or 1.0
                        closing = (awvx * dx + awvy * dy) / dn  # agent speed toward the ego
                gate = max(min_close, 0.5)
            else:
                # forecast-based (iter4) when MIN_CLOSING>0, else total-closing (iter2/3)
                avx = avy = 0.0; nm = 0
                for mode in futs[i] if i < len(futs) else []:
                    if len(mode) >= 1:
                        avx += float(mode[0][0]) / dt; avy += float(mode[0][1]) / dt; nm += 1
                if nm:
                    avx /= nm; avy /= nm
                if min_close > 0.0:
                    closing = -(avx * ox + avy * oy) / gap
                    gate = max(min_close, 0.5)
                else:
                    closing = -((avx - ego_vx) * ox + (avy - ego_vy) * oy) / gap
                    gate = 0.5
            if closing > gate:
                ttc = gap / closing
                if ttc < min_ttc:
                    min_ttc = ttc
        if track_vel:
            _sentinel_track.clear()
            _sentinel_track.update(newtrack)
        if _sentinel_run.get("braking") or min_ttc < ttc_thresh:
            _sentinel_run["braking"] = True
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"brake": True, "run": _sentinel_run["i"],
                                          "ttc": round(min_ttc, 2)}) + "\\n")
            except Exception:
                pass
            return [[0.0, 0.0] for _ in range(len(base))]
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
print("FULL_TRACK_PATCHED")
