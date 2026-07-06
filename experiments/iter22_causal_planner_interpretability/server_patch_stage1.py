#!/usr/bin/env python3
"""Iteration-22 Stage 1 UniAD patch: motion-query extraction and frozen intervention support.

This patch is applied on the GPU box before a Stage 1 extraction or intervention replay. It
adds behavior-preserving logging when no direction is supplied, and a single pre-declared
motion-query direction patch when SENTINEL_E22_DIRECTION_JSON and SENTINEL_E22_ALPHA are set.
"""

import subprocess


UNIAD = "/opt/sentinel-stack/UniAD"
RUNNER = f"{UNIAD}/inference/runner.py"
SERVER = f"{UNIAD}/inference/server.py"

subprocess.run(
    ["git", "-C", UNIAD, "checkout", "--", "inference/runner.py", "inference/server.py"],
    check=True,
)

runner = open(RUNNER).read()

CALL_ANCHOR = "        # get the planning output\n        outs_planning = self.model.planning_head.forward("
assert CALL_ANCHOR in runner, "planning call-site anchor not found"
assert runner.count(CALL_ANCHOR) == 1, "planning call-site anchor not unique"

PRE_CALL = r'''        # SENTINEL_E22_STAGE1: stash motion/planning bridge tensors and optionally patch them.
        try:
            import json as _e22_json
            import os as _e22_os
            import sys as _e22_sys
            import torch as _e22_torch

            _e22_tq = outs_motion["sdc_traj_query"]
            _e22_trk = outs_motion["sdc_track_query"]
            _e22_last = _e22_tq[-1]
            _e22_alpha = float(_e22_os.environ.get("SENTINEL_E22_ALPHA", "0.0"))
            _e22_dir_path = _e22_os.environ.get("SENTINEL_E22_DIRECTION_JSON", "")
            self.model.planning_head._sentinel_e22_stash = {
                "sdc_traj_query_last": _e22_last.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_traj_query_last_shape": list(_e22_last.shape),
                "sdc_track_query": _e22_trk.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_track_query_shape": list(_e22_trk.shape),
                "intervention_alpha": _e22_alpha,
                "intervention_direction_json": _e22_dir_path,
                "intervention_applied": False,
            }
            if _e22_dir_path and abs(_e22_alpha) > 0.0:
                _e22_key = (_e22_dir_path, _e22_alpha)
                _e22_cache = getattr(self.model.planning_head, "_sentinel_e22_direction", None)
                if _e22_cache is None or _e22_cache.get("key") != _e22_key:
                    with open(_e22_dir_path) as _e22_f:
                        _e22_payload = _e22_json.load(_e22_f)
                    _e22_cache = {
                        "key": _e22_key,
                        "traj": _e22_payload["sdc_traj_query_last_direction"],
                        "track": _e22_payload["sdc_track_query_direction"],
                    }
                    self.model.planning_head._sentinel_e22_direction = _e22_cache
                _e22_dt = _e22_torch.tensor(
                    _e22_cache["traj"], dtype=_e22_last.dtype, device=_e22_last.device
                ).reshape(_e22_last.shape)
                _e22_dk = _e22_torch.tensor(
                    _e22_cache["track"], dtype=_e22_trk.dtype, device=_e22_trk.device
                ).reshape(_e22_trk.shape)
                outs_motion["sdc_traj_query"][-1] = _e22_last + _e22_alpha * _e22_dt
                outs_motion["sdc_track_query"] = _e22_trk + _e22_alpha * _e22_dk
                self.model.planning_head._sentinel_e22_stash["intervention_applied"] = True
        except Exception as _e22_e:
            print(f"E22_PRE_CALL_ERROR: {type(_e22_e).__name__}: {_e22_e}",
                  file=_e22_sys.stderr, flush=True)

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E22_STAGE1: log tensors, command candidates, objects, and forecasts.
        try:
            import json as _e22_json2
            import os as _e22_os2
            import sys as _e22_sys2

            if _e22_os2.environ.get("SENTINEL_E22_STAGE1", "0") == "1":
                _e22_cands = []
                for _e22_cmd in (0, 1, 2):
                    _e22_op = self.model.planning_head.forward(
                        bev_embed,
                        occ_mask,
                        outs_motion["bev_pos"],
                        outs_motion["sdc_traj_query"],
                        outs_motion["sdc_track_query"],
                        command=torch.tensor(_e22_cmd).to(self.device).unsqueeze(0),
                    )
                    _e22_cands.append(
                        _format_trajs(_e22_op["sdc_traj"])[0].cpu().numpy().tolist()
                    )
                _e22_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e22_stash = getattr(self.model.planning_head, "_sentinel_e22_stash", {})
                _e22_rec = {
                    "ts": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist(),
                    "cands": _e22_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e22_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e22_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e22_n_obj else []
                    ),
                }
                _e22_rec.update(_e22_stash)
                with open(
                    _e22_os2.environ.get("SENTINEL_E22_LOG", "/model/sentinel_e22_stage1.jsonl"),
                    "a",
                ) as _e22_f:
                    _e22_f.write(_e22_json2.dumps(_e22_rec) + "\n")
        except Exception as _e22_e2:
            print(f"E22_LOG_ERROR: {type(_e22_e2).__name__}: {_e22_e2}",
                  file=_e22_sys2.stderr, flush=True)
        # SENTINEL_E22_STAGE1 end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter22 Stage 1 reset markers -----------------------------------------------
import json as _e22_srv_json
import os as _e22_srv_os


def _e22_reset_marker():
    if _e22_srv_os.environ.get("SENTINEL_E22_STAGE1", "0") != "1":
        return
    try:
        with open(
            _e22_srv_os.environ.get("SENTINEL_E22_LOG", "/model/sentinel_e22_stage1.jsonl"),
            "a",
        ) as _e22_srv_f:
            _e22_srv_f.write(_e22_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e22_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E22_STAGE1_PATCHED")
