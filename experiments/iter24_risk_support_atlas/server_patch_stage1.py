#!/usr/bin/env python3
"""Iteration-24 Stage 1 UniAD patch: S0-hardened motion-query extraction.

This patch is applied on the GPU box before canary or full extraction. It is
behavior-preserving: it logs the motion/planning bridge tensors, command
candidates, objects, forecasts, and the feeder-supplied join context.
"""

from __future__ import annotations

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

PRE_CALL = r'''        # SENTINEL_E24_STAGE1: stash motion/planning bridge tensors.
        try:
            _e24_tq = outs_motion["sdc_traj_query"]
            _e24_trk = outs_motion["sdc_track_query"]
            _e24_last = _e24_tq[-1]
            self.model.planning_head._sentinel_e24_stash = {
                "sdc_traj_query_last": _e24_last.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_traj_query_last_shape": list(_e24_last.shape),
                "sdc_traj_query_last_dtype": str(_e24_last.dtype),
                "sdc_track_query": _e24_trk.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_track_query_shape": list(_e24_trk.shape),
                "sdc_track_query_dtype": str(_e24_trk.dtype),
                "intervention_alpha": 0.0,
                "intervention_direction_json": "",
                "intervention_applied": False,
            }
        except Exception as _e24_e:
            import sys as _e24_sys
            print(f"E24_PRE_CALL_ERROR: {type(_e24_e).__name__}: {_e24_e}",
                  file=_e24_sys.stderr, flush=True)

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E24_STAGE1: log tensors, candidates, and frozen join context.
        try:
            import json as _e24_json
            import os as _e24_os
            import sys as _e24_sys

            if _e24_os.environ.get("SENTINEL_E24_STAGE1", "0") == "1":
                _e24_ctx_path = _e24_os.environ.get(
                    "SENTINEL_E24_CONTEXT", "/model/sentinel_e24_context.json"
                )
                try:
                    with open(_e24_ctx_path) as _e24_ctx_f:
                        _e24_ctx = _e24_json.load(_e24_ctx_f)
                except Exception as _e24_ctx_e:
                    _e24_ctx = {"context_error": f"{type(_e24_ctx_e).__name__}: {_e24_ctx_e}"}
                _e24_cands = []
                for _e24_cmd in (0, 1, 2):
                    _e24_op = self.model.planning_head.forward(
                        bev_embed,
                        occ_mask,
                        outs_motion["bev_pos"],
                        outs_motion["sdc_traj_query"],
                        outs_motion["sdc_track_query"],
                        command=torch.tensor(_e24_cmd).to(self.device).unsqueeze(0),
                    )
                    _e24_cands.append(
                        _format_trajs(_e24_op["sdc_traj"])[0].cpu().numpy().tolist()
                    )
                _e24_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e24_stash = getattr(self.model.planning_head, "_sentinel_e24_stash", {})
                _e24_rec = {
                    "scene": _e24_ctx.get("scene", ""),
                    "split": _e24_ctx.get("split", ""),
                    "sample_index": _e24_ctx.get("sample_index", None),
                    "timestamp_us": _e24_ctx.get("timestamp_us", None),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist(),
                    "cands": _e24_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e24_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e24_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e24_n_obj else []
                    ),
                }
                if "context_error" in _e24_ctx:
                    _e24_rec["context_error"] = _e24_ctx["context_error"]
                _e24_rec.update(_e24_stash)
                with open(
                    _e24_os.environ.get("SENTINEL_E24_LOG", "/model/sentinel_e24_stage1.jsonl"),
                    "a",
                ) as _e24_f:
                    _e24_f.write(_e24_json.dumps(_e24_rec) + "\n")
        except Exception as _e24_e2:
            print(f"E24_LOG_ERROR: {type(_e24_e2).__name__}: {_e24_e2}",
                  file=_e24_sys.stderr, flush=True)
        # SENTINEL_E24_STAGE1 end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter24 Stage 1 context and reset markers ------------------------------------
import json as _e24_srv_json
import os as _e24_srv_os
from fastapi import Request as _e24_Request


def _e24_reset_marker():
    if _e24_srv_os.environ.get("SENTINEL_E24_STAGE1", "0") != "1":
        return
    try:
        with open(
            _e24_srv_os.environ.get("SENTINEL_E24_LOG", "/model/sentinel_e24_stage1.jsonl"),
            "a",
        ) as _e24_srv_f:
            _e24_srv_f.write(_e24_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e24_context")
async def sentinel_e24_context(request: _e24_Request) -> bool:
    payload = await request.json()
    with open(
        _e24_srv_os.environ.get("SENTINEL_E24_CONTEXT", "/model/sentinel_e24_context.json"),
        "w",
    ) as _e24_ctx_f:
        _e24_srv_json.dump(payload, _e24_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e24_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E24_STAGE1_PATCHED")
