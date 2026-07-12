#!/usr/bin/env python3
"""Iteration 48 monitor patch: released union at the UniAD_SIM client interception point.

Applied ON THE BOX at launch (scp this file, run once, before any episode). It patches
`/opt/sentinel-stack/UniAD_SIM/tools/closeloop/e2e.py` — the closed-loop client — at the
pre-registered interception point: AFTER the model forward, BEFORE the plan is written to
the plan pipe. This is the ONLY permitted delta on top of the frozen UniAD_SIM tree
(HYPOTHESIS.md: frozen monitored arm); the SHA256 of this file and of the patched files
are recorded in the launch receipts.

Decision rule: the iteration-15 released union EXACTLY as committed and replay-verified in
iteration 42 (`experiments/iter42_exact_trace_replay_support/server_patch_union_trace.py`):
CPA over the planner's own plan against tracked-object constant-velocity extrapolation, plus
closing-speed TTC, in union, with the threat-cleared latch release (K consecutive clear
frames) and the latched committed-stop (all-zeros) override trajectory.

Parameters: EXACTLY the NeuroNCAP-frozen values, baked in as defaults —
cpa_margin 1.5 m / ttc_thresh 2.5 s / min_closing 3.0 m/s / max_gap 30.0 m /
min_score 0.3 / release_k 4 / plan-step dt 0.5 s. Any retuning voids the iteration (F1).
The container receives no SENTINEL_* parameter env vars (only SENTINEL_ENABLED is
forwarded by tools/e2e.sh), so the frozen defaults are the only values that can run.

Port notes (mechanism identical to NeuroNCAP, adapters only):
- plan = results[0]['planning']['result_planning']['sdc_traj'][0] — the ego/LiDAR-frame
  plan from the SAME forward pass (x right, y forward; HUGSIM's traj2control contract).
- tracked objects = results[0]['boxes_3d'/'scores_3d'/'track_ids'] — the client's own
  track outputs from the SAME forward pass (no simulator state, no ground truth, no map).
- ego pose / world frame = the client's own l2g transform (data['l2g_r_mat'],
  data['l2g_t']), i.e. exactly the lidar-to-global map UniAD itself uses across frames;
  it is orthonormal, so distances/velocities match the true world frame.
- velocities by cross-frame world-position differencing keyed on track id — the
  NeuroNCAP mechanism. HUGSIM timestamps are SECONDS (NeuroNCAP's were microseconds);
  the delta is used unit-correctly (no 1e6 division). Not a parameter change.
- env gate: SENTINEL_ENABLED != "1" returns the plan untouched — the OFF arm runs the
  identical patched binary path, unpatched in behavior.
- every episode (both arms) prints the load marker SENTINEL_I48_UNION_PATCH_LOADED with
  the echoed parameter block (iteration-42 discipline); every ON frame appends a full
  input+decision row to <output>/sentinel_iter48_decisions.jsonl and prints a
  SENTINEL_I48_DECISION line (fired/brake/release/latch). No printed token contains the
  substring 'sent' (the step counter greps for it).
"""

import hashlib
import subprocess

REPO = "/opt/sentinel-stack/UniAD_SIM"
E2E_PY = REPO + "/tools/closeloop/e2e.py"
E2E_SH = REPO + "/tools/e2e.sh"
FROZEN_UNIADSIM_SHA = "5fb279e39912a5ac7f58e00d56b065cadcd0a749"

HELPERS = '''
# ---- Sentinel iter48: released union, client-side port (frozen NeuroNCAP params) --------
# Decision rule and parameters are the iteration-15 released union exactly as replay-verified
# in iteration 42. SENTINEL_ENABLED gates behavior: OFF arm returns the plan untouched.
import json as _sjson, math as _smath, os as _sos

_S48_PARAMS = {
    "cpa_margin": float(_sos.environ.get("SENTINEL_CPA_MARGIN", "1.5")),
    "ttc_thresh": float(_sos.environ.get("SENTINEL_TTC", "2.5")),
    "min_closing": float(_sos.environ.get("SENTINEL_MIN_CLOSING", "3.0")),
    "max_gap": float(_sos.environ.get("SENTINEL_MAXGAP", "30.0")),
    "min_score": float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3")),
    "release_k": int(_sos.environ.get("SENTINEL_RELEASE_K", "4")),
    "dt": 0.5,
}
_S48_ENABLED = _sos.environ.get("SENTINEL_ENABLED", "0") == "1"
_s48_state = {"frame": -1, "braking": False, "clear": 0}
_s48_track = {}
print("SENTINEL_I48_UNION_PATCH_LOADED enabled=%d params=%s"
      % (1 if _S48_ENABLED else 0, _sjson.dumps(_S48_PARAMS, sort_keys=True)), flush=True)


def _s48_write(output_dir, row):
    try:
        with open(_sos.path.join(output_dir, "sentinel_iter48_decisions.jsonl"), "a") as f:
            f.write(_sjson.dumps(row, sort_keys=True) + "\\n")
    except Exception:
        pass


def _sentinel_i48_intervene(plan_traj, result, data, output_dir):
    if not _S48_ENABLED:
        return plan_traj
    _s48_state["frame"] += 1
    try:
        p = _S48_PARAMS
        base = [[float(x), float(y)] for x, y in plan_traj.tolist()]
        boxes = result["boxes_3d"]
        centers = boxes.gravity_center.numpy()
        scores = result["scores_3d"].numpy()
        ids = result["track_ids"].numpy()
        R = data["l2g_r_mat"].detach().cpu().numpy().reshape(3, 3)
        t = data["l2g_t"].detach().cpu().numpy().reshape(3)
        ts = float(data["timestamp"])  # HUGSIM: seconds
        pre_braking = bool(_s48_state["braking"])
        pre_clear = int(_s48_state["clear"])
        ego_wx, ego_wy = float(t[0]), float(t[1])
        ego_world_plan = []
        for px, py in base:
            w = R @ np.array([px, py, 0.0]) + t
            ego_world_plan.append((float(w[0]), float(w[1])))
        H = len(ego_world_plan)
        min_cpa = 1e9
        min_ttc = 1e9
        newtrack = {}
        objs_log = []
        for i in range(min(len(centers), len(scores))):
            sc = float(scores[i])
            if not _smath.isfinite(sc) or sc < p["min_score"]:
                continue
            ox, oy = float(centers[i][0]), float(centers[i][1])
            if _smath.hypot(ox, oy) > p["max_gap"]:
                continue
            w = R @ np.array([ox, oy, 0.0]) + t
            wx, wy = float(w[0]), float(w[1])
            oid = int(ids[i]) if i < len(ids) else "idx_%d" % i
            newtrack[oid] = (wx, wy, ts)
            avx = avy = 0.0
            if oid in _s48_track:
                pwx, pwy, pts = _s48_track[oid]
                dta = ts - pts  # seconds already (unit-correct NeuroNCAP mechanism)
                if dta > 1e-3:
                    avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
            for k in range(H):
                th = (k + 1) * p["dt"]
                ax, ay = wx + avx * th, wy + avy * th
                ex, ey = ego_world_plan[k]
                d = _smath.hypot(ex - ax, ey - ay)
                if d < min_cpa:
                    min_cpa = d
            dx, dy = ego_wx - wx, ego_wy - wy
            gapw = _smath.hypot(dx, dy)
            if gapw > 1e-3:
                closing = (avx * dx + avy * dy) / gapw
                if closing > max(p["min_closing"], 0.5):
                    ttc = gapw / closing
                    if ttc < min_ttc:
                        min_ttc = ttc
            objs_log.append({"id": oid, "bev": [ox, oy], "world": [wx, wy],
                             "vel": [avx, avy], "score": sc})
        _s48_track.clear()
        _s48_track.update(newtrack)
        fired = min_cpa < p["cpa_margin"] or min_ttc < p["ttc_thresh"]
        release = False
        if fired:
            _s48_state["braking"] = True
            _s48_state["clear"] = 0
        elif _s48_state["braking"]:
            _s48_state["clear"] += 1
            if _s48_state["clear"] >= p["release_k"]:
                _s48_state["braking"] = False
                _s48_state["clear"] = 0
                release = True
        brake = bool(_s48_state["braking"])
        _s48_write(output_dir, {
            "trace_version": "iter48_hugsim_union_v1",
            "frame_index": _s48_state["frame"],
            "ts": ts,
            "traj": base,
            "objs": objs_log,
            "l2g_t": [float(v) for v in t.tolist()],
            "l2g_r_mat": [[float(v) for v in row] for row in R.tolist()],
            "params": p,
            "pre_braking": pre_braking,
            "pre_clear": pre_clear,
            "min_cpa": float(min_cpa),
            "min_ttc": float(min_ttc),
            "fired": bool(fired),
            "post_braking": bool(_s48_state["braking"]),
            "post_clear": int(_s48_state["clear"]),
            "brake": brake,
            "release": bool(release),
        })
        print("SENTINEL_I48_DECISION frame=%d fired=%d brake=%d release=%d clear=%d "
              "min_cpa=%.4f min_ttc=%.4f objs=%d"
              % (_s48_state["frame"], int(fired), int(brake), int(release),
                 _s48_state["clear"], min_cpa, min_ttc, len(objs_log)), flush=True)
        if brake:
            return np.zeros_like(plan_traj)  # latched committed-stop trajectory
    except Exception as e:
        _s48_write(output_dir, {"trace_version": "iter48_hugsim_union_v1",
                                "trace_error": str(e),
                                "frame_index": _s48_state["frame"]})
        print("SENTINEL_I48_DECISION_ERROR frame=%d err=%s"
              % (_s48_state["frame"], str(e).replace("\\n", " ")[:200]), flush=True)
    return plan_traj


'''

INTERCEPT_OLD = (
    "        if results is not None:\n"
    "            plan_traj = results[0]['planning']['result_planning']"
    "['sdc_traj'][0].detach().cpu().numpy()\n"
    "            with open(plan_pipe, \"wb\") as pipe:\n"
)
INTERCEPT_NEW = (
    "        if results is not None:\n"
    "            plan_traj = results[0]['planning']['result_planning']"
    "['sdc_traj'][0].detach().cpu().numpy()\n"
    "            plan_traj = _sentinel_i48_intervene(plan_traj, results[0], data, args.output)\n"
    "            with open(plan_pipe, \"wb\") as pipe:\n"
)
HELPER_ANCHOR = "def parse_args():"

# tools/e2e.sh (the iter45-recorded docker wrapper) must forward SENTINEL_ENABLED into the
# ephemeral container. Fixed -e list pattern (CONTINUITY box playbook); idempotent.
SH_OLD = "-e PYTHONPATH=.:/shim -e CUDA_VISIBLE_DEVICES=$CUDA_ID"
SH_NEW = "-e PYTHONPATH=.:/shim -e SENTINEL_ENABLED -e CUDA_VISIBLE_DEVICES=$CUDA_ID"


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert head == FROZEN_UNIADSIM_SHA, f"UniAD_SIM HEAD {head} != frozen"
    # iteration-42 discipline: restore the pristine file, then apply (idempotent relaunch).
    subprocess.run(["git", "-C", REPO, "checkout", "--", "tools/closeloop/e2e.py"], check=True)
    src = open(E2E_PY).read()
    assert HELPER_ANCHOR in src, "helper anchor missing"
    assert INTERCEPT_OLD in src, "intercept anchor missing"
    src = src.replace(HELPER_ANCHOR, HELPERS + HELPER_ANCHOR, 1)
    src = src.replace(INTERCEPT_OLD, INTERCEPT_NEW, 1)
    open(E2E_PY, "w").write(src)

    sh = open(E2E_SH).read()
    if "SENTINEL_ENABLED" not in sh:
        assert SH_OLD in sh, "e2e.sh env anchor missing"
        sh = sh.replace(SH_OLD, SH_NEW, 1)
        open(E2E_SH, "w").write(sh)

    print("ITER48_UNION_PATCHED")
    print(f"ITER48_E2E_PY_SHA256={sha256(E2E_PY)}")
    print(f"ITER48_E2E_SH_SHA256={sha256(E2E_SH)}")


if __name__ == "__main__":
    main()
