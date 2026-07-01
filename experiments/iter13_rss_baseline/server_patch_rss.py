import subprocess
SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/server.py'], check=True)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter13: RSS-style formal longitudinal envelope (baseline arm) ---------------------
# A guaranteed-stopping-distance rule in the spirit of Responsibility-Sensitive Safety's
# longitudinal minimum-distance formula, applied to the OBSERVED closing kinematics between the
# ego and each tracked object:
#
#     d_safe = v_c * rho + 0.5 * a_acc * rho^2 + (v_c + rho * a_acc)^2 / (2 * a_brake) + margin
#
# where v_c is the observed closing speed (rate of gap decrease, ego and agent motion combined,
# from the same multi-frame world-frame tracking the union monitor uses), rho the response time,
# a_acc the worst-case acceleration during the response, a_brake the guaranteed braking. Brake
# (latched, identical committed stop) when the actual gap is inside the envelope.
#
# Scope, stated plainly: this is the longitudinal rule only — no lateral rule, no proper-response
# modulation, closing-speed form rather than the two-vehicle same-direction decomposition — i.e.
# an RSS-inspired formal envelope, not a full RSS implementation. It shares the union's inputs
# and actuator so the comparison isolates ONE variable: formal envelope vs introspective
# plan-aware risk.
import json as _sjson, os as _sos, math as _smath
import numpy as _np
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_risk.jsonl")
_sentinel_run = {"i": -1, "braking": False}
_sentinel_track = {}
_sentinel_ego = {}


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["braking"] = False
    _sentinel_track.clear()
    _sentinel_ego.clear()
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
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
        rho = float(_sos.environ.get("SENTINEL_RSS_RHO", "0.5"))
        a_brake = float(_sos.environ.get("SENTINEL_RSS_BRAKE", "6.0"))
        a_acc = float(_sos.environ.get("SENTINEL_RSS_ACC", "2.0"))
        margin = float(_sos.environ.get("SENTINEL_RSS_MARGIN", "1.0"))
        contact = float(_sos.environ.get("SENTINEL_RSS_CONTACT", "2.0"))
        max_gap = float(_sos.environ.get("SENTINEL_MAXGAP", "30.0"))
        min_score = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
        aux = out.aux_outputs.to_json()
        objs = aux.get("objects_in_bev") or []
        scores = aux.get("object_scores") or []
        ids = aux.get("object_ids") or []
        e2w = _np.array(data.ego2world, dtype=float)
        ts = int(data.timestamp)
        ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
        evx = evy = 0.0
        if _sentinel_ego:
            dte = (ts - _sentinel_ego["ts"]) / 1e6
            if dte > 1e-3:
                evx = (ego_wx - _sentinel_ego["x"]) / dte
                evy = (ego_wy - _sentinel_ego["y"]) / dte
        _sentinel_ego.update({"x": ego_wx, "y": ego_wy, "ts": ts})
        newtrack = {}
        worst = None  # (gap - d_safe) most violated
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
            dx, dy = wx - ego_wx, wy - ego_wy
            gapw = _smath.hypot(dx, dy)
            if gapw < 1e-3:
                continue
            ux, uy = dx / gapw, dy / gapw  # ego -> agent line of sight
            v_close = -((avx - evx) * ux + (avy - evy) * uy)  # rate of gap decrease, observed
            if v_close <= 0.3:
                continue
            gap = gapw - contact
            d_safe = (v_close * rho + 0.5 * a_acc * rho * rho
                      + (v_close + rho * a_acc) ** 2 / (2.0 * a_brake) + margin)
            viol = gap - d_safe
            if worst is None or viol < worst[0]:
                worst = (viol, gap, d_safe, v_close)
        _sentinel_track.clear()
        _sentinel_track.update(newtrack)
        if _sentinel_run.get("braking") or (worst is not None and worst[0] < 0):
            _sentinel_run["braking"] = True
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"brake": True, "run": _sentinel_run["i"],
                                          "gap": round(worst[1], 2) if worst else None,
                                          "d_safe": round(worst[2], 2) if worst else None,
                                          "v_close": round(worst[3], 2) if worst else None}) + "\\n")
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
print("RSS_BASELINE_PATCHED")
