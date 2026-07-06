#!/usr/bin/env python3
"""Iteration-23 Stage 1 UniAD patch: S0-hardened motion-query extraction.

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

PRE_CALL = r'''        # SENTINEL_E23_STAGE1: stash motion/planning bridge tensors.
        try:
            _e23_tq = outs_motion["sdc_traj_query"]
            _e23_trk = outs_motion["sdc_track_query"]
            _e23_last = _e23_tq[-1]
            self.model.planning_head._sentinel_e23_stash = {
                "sdc_traj_query_last": _e23_last.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_traj_query_last_shape": list(_e23_last.shape),
                "sdc_track_query": _e23_trk.detach().float().cpu().numpy().ravel().tolist(),
                "sdc_track_query_shape": list(_e23_trk.shape),
                "intervention_alpha": 0.0,
                "intervention_direction_json": "",
                "intervention_applied": False,
            }
        except Exception as _e23_e:
            import sys as _e23_sys
            print(f"E23_PRE_CALL_ERROR: {type(_e23_e).__name__}: {_e23_e}",
                  file=_e23_sys.stderr, flush=True)

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E23_STAGE1: log tensors, candidates, and frozen join context.
        try:
            import json as _e23_json
            import os as _e23_os
            import sys as _e23_sys

            if _e23_os.environ.get("SENTINEL_E23_STAGE1", "0") == "1":
                _e23_ctx_path = _e23_os.environ.get(
                    "SENTINEL_E23_CONTEXT", "/model/sentinel_e23_context.json"
                )
                try:
                    with open(_e23_ctx_path) as _e23_ctx_f:
                        _e23_ctx = _e23_json.load(_e23_ctx_f)
                except Exception as _e23_ctx_e:
                    _e23_ctx = {"context_error": f"{type(_e23_ctx_e).__name__}: {_e23_ctx_e}"}
                _e23_cands = []
                for _e23_cmd in (0, 1, 2):
                    _e23_op = self.model.planning_head.forward(
                        bev_embed,
                        occ_mask,
                        outs_motion["bev_pos"],
                        outs_motion["sdc_traj_query"],
                        outs_motion["sdc_track_query"],
                        command=torch.tensor(_e23_cmd).to(self.device).unsqueeze(0),
                    )
                    _e23_cands.append(
                        _format_trajs(_e23_op["sdc_traj"])[0].cpu().numpy().tolist()
                    )
                _e23_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e23_stash = getattr(self.model.planning_head, "_sentinel_e23_stash", {})
                _e23_rec = {
                    "scene": _e23_ctx.get("scene", ""),
                    "split": _e23_ctx.get("split", ""),
                    "sample_index": _e23_ctx.get("sample_index", None),
                    "timestamp_us": _e23_ctx.get("timestamp_us", None),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist(),
                    "cands": _e23_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e23_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e23_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e23_n_obj else []
                    ),
                }
                if "context_error" in _e23_ctx:
                    _e23_rec["context_error"] = _e23_ctx["context_error"]
                _e23_rec.update(_e23_stash)
                with open(
                    _e23_os.environ.get("SENTINEL_E23_LOG", "/model/sentinel_e23_stage1.jsonl"),
                    "a",
                ) as _e23_f:
                    _e23_f.write(_e23_json.dumps(_e23_rec) + "\n")
        except Exception as _e23_e2:
            print(f"E23_LOG_ERROR: {type(_e23_e2).__name__}: {_e23_e2}",
                  file=_e23_sys.stderr, flush=True)
        # SENTINEL_E23_STAGE1 end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter23 Stage 1 context and reset markers ------------------------------------
import json as _e23_srv_json
import os as _e23_srv_os
from fastapi import Request as _e23_Request


def _e23_reset_marker():
    if _e23_srv_os.environ.get("SENTINEL_E23_STAGE1", "0") != "1":
        return
    try:
        with open(
            _e23_srv_os.environ.get("SENTINEL_E23_LOG", "/model/sentinel_e23_stage1.jsonl"),
            "a",
        ) as _e23_srv_f:
            _e23_srv_f.write(_e23_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e23_context")
async def sentinel_e23_context(request: _e23_Request) -> bool:
    payload = await request.json()
    with open(
        _e23_srv_os.environ.get("SENTINEL_E23_CONTEXT", "/model/sentinel_e23_context.json"),
        "w",
    ) as _e23_ctx_f:
        _e23_srv_json.dump(payload, _e23_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e23_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E23_STAGE1_PATCHED")
