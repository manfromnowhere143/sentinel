#!/usr/bin/env python3
"""Checkpoint D on VAD (behaviour-preserving): log all three native ego_fut_preds candidates.

VAD's planning head emits ego_fut_preds of shape [3, 6, 2] — three command-indexed trajectory
modes from a single forward pass — and executes mode [input.command] (optionally refined by its
own collision optimizer). This patch logs, per frame: the three raw candidate trajectories
(cumsum of the deltas, ego frame), the executed command, the FINAL executed trajectory (after any
collision optimization), and the detected objects + their forecast displacements — the same record
schema iteration 12 used on UniAD, so `iter12_plan_selection/analyze_candidates.py` runs on the
output unchanged.

Patches /opt/sentinel-stack/VAD/inference/runner.py in place (no git checkout — composes with the
server-side union patch, which touches server.py only). Idempotent; failures print
CAND_LOG_ERROR to stderr (visible in the model container's docker logs).
"""
RUNNER = '/opt/sentinel-stack/VAD/inference/runner.py'
src = open(RUNNER).read()

MARK = 'VAD_CAND_LOGGING'
if MARK in src:
    print('already patched')
    raise SystemExit(0)

ANCHOR = """        return VADInferenceOutput(
            trajectory=trajectory,"""

INSERT = """        # --- VAD_CAND_LOGGING (checkpoint D on VAD): behaviour-preserving per-frame record
        try:
            import json as _cjson
            import os as _cos
            _cands = (
                bbox_results[0]["ego_fut_preds"].cumsum(dim=-2).numpy().tolist()
            )  # [3 modes, 6 steps, 2], ego frame
            _rec = {
                "ts": float(input.timestamp),
                "exe_cmd": int(input.command),
                "cands": _cands,
                "exe_traj": trajectory.tolist(),
                "objs": objects_in_bev.tolist() if len(objects_in_bev) else [],
                "scores": object_scores.tolist() if len(object_scores) else [],
                "futs": future_trajs.tolist() if len(future_trajs) else [],
            }
            with open(_cos.environ.get("SENTINEL_CAND_LOG", "/model/sentinel_vad_cand.jsonl"), "a") as _f:
                _f.write(_cjson.dumps(_rec) + "\\n")
        except Exception as _e:
            import sys as _csys
            print(f"CAND_LOG_ERROR: {type(_e).__name__}: {_e}", file=_csys.stderr, flush=True)
        # --- end VAD_CAND_LOGGING

        return VADInferenceOutput(
            trajectory=trajectory,"""

assert ANCHOR in src, 'return-anchor not found in VAD runner.py'
assert src.count(ANCHOR) == 1, 'anchor not unique'
src = src.replace(ANCHOR, INSERT)
open(RUNNER, 'w').write(src)
print('VAD_CAND_PATCHED')
