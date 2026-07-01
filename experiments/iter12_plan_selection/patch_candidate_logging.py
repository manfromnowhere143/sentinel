#!/usr/bin/env python3
"""Checkpoint D (behaviour-preserving): log all three command-conditioned UniAD candidate plans.

Patches /opt/sentinel-stack/UniAD/inference/runner.py from pristine. After the planning head runs
for the executed command, the head alone is re-run for each command in (0, 1, 2) — the backbone,
tracking and motion stages are not repeated — and every frame appends one JSON line:

    {"ts": ..., "exe_cmd": c, "cands": [[...6x2] for commands 0, 1, 2],
     "objs": [[x,y,w,h,yaw], ...], "scores": [...], "futs": [[6 modes x 12 x 2], ...]}

Command semantics (from the runner's own docstring, which corrects the planning doc):
0 = right, 1 = left, 2 = straight.

to SENTINEL_CAND_LOG (default /model/sentinel_cand.jsonl -> UniAD/sentinel_cand.jsonl on the host).
The trajectory returned to the simulator is untouched. Failures print CAND_LOG_ERROR to stderr so
they are visible in the model container's docker logs instead of failing silently.
"""
import subprocess

RUNNER = '/opt/sentinel-stack/UniAD/inference/runner.py'
subprocess.run(['git', '-C', '/opt/sentinel-stack/UniAD', 'checkout', '--', 'inference/runner.py'],
               check=True)
src = open(RUNNER).read()

ANCHOR = """        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]
"""

INSERT = """        # --- Sentinel checkpoint D: log all command-conditioned candidate plans (no behaviour change)
        try:
            import json as _cjson
            import os as _cos
            import sys as _csys
            _cands = []
            for _c in (0, 1, 2):
                _op = self.model.planning_head.forward(
                    bev_embed,
                    occ_mask,
                    outs_motion["bev_pos"],
                    outs_motion["sdc_traj_query"],
                    outs_motion["sdc_track_query"],
                    command=torch.tensor(_c).to(self.device).unsqueeze(0),
                )
                _cands.append(_format_trajs(_op["sdc_traj"])[0].cpu().numpy().tolist())
            _n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
            _rec = {
                "ts": float(input.timestamp),
                "exe_cmd": int(input.command),
                "cands": _cands,
                "objs": _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist() if _n_obj else [],
                "scores": outs_track[0]["scores_3d"].cpu().numpy().tolist() if _n_obj else [],
                "futs": _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist() if _n_obj else [],
            }
            with open(_cos.environ.get("SENTINEL_CAND_LOG", "/model/sentinel_cand.jsonl"), "a") as _f:
                _f.write(_cjson.dumps(_rec) + "\\n")
        except Exception as _e:  # loud, not silent — visible in docker logs
            import sys as _csys2
            print(f"CAND_LOG_ERROR: {type(_e).__name__}: {_e}", file=_csys2.stderr, flush=True)
        # --- end checkpoint D

"""

assert ANCHOR in src, 'anchor not found in pristine runner.py'
assert src.count(ANCHOR) == 1, 'anchor not unique'
src = src.replace(ANCHOR, ANCHOR + INSERT)
open(RUNNER, 'w').write(src)
print('CANDIDATE_LOGGING_PATCHED')
