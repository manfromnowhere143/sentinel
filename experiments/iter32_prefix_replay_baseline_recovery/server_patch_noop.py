#!/usr/bin/env python3
"""Iteration-32 UniAD patch: behavior-preserving prefix replay logging."""

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

PRE_CALL = r'''        # SENTINEL_E32_PREFIX_REPLAY: stash behavior-preserving bridge tensors.
        try:
            import hashlib as _e32_hashlib
            import json as _e32_json
            import os as _e32_os
            import sys as _e32_sys

            if _e32_os.environ.get("SENTINEL_E32_PREFIX_REPLAY", "0") == "1":
                _e32_tq = outs_motion["sdc_traj_query"]
                _e32_trk = outs_motion["sdc_track_query"]
                _e32_last = _e32_tq[-1]
                _e32_flat = torch.cat([
                    _e32_last.detach().float().reshape(-1).cpu(),
                    _e32_trk.detach().float().reshape(-1).cpu(),
                ])
                self.model.planning_head._sentinel_e32_stash = {
                    "sdc_traj_query_last": _e32_last.detach().float().cpu().numpy().ravel().tolist(),
                    "sdc_traj_query_last_shape": list(_e32_last.shape),
                    "sdc_traj_query_last_dtype": str(_e32_last.dtype),
                    "sdc_track_query": _e32_trk.detach().float().cpu().numpy().ravel().tolist(),
                    "sdc_track_query_shape": list(_e32_trk.shape),
                    "sdc_track_query_dtype": str(_e32_trk.dtype),
                    "bridge_sha256": _e32_hashlib.sha256(_e32_flat.numpy().tobytes()).hexdigest(),
                    "intervention_alpha": 0.0,
                    "intervention_direction_json": "",
                    "intervention_applied": False,
                    "iter32_patch_mode": "prefix_replay_noop",
                }
        except Exception as _e32_e:
            print(f"E32_PRE_CALL_ERROR: {type(_e32_e).__name__}: {_e32_e}",
                  file=_e32_sys.stderr, flush=True)
            try:
                self.model.planning_head._sentinel_e32_stash = {
                    "error": f"{type(_e32_e).__name__}: {_e32_e}"
                }
            except Exception:
                pass

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E32_PREFIX_REPLAY: log prefix and target rows.
        try:
            import json as _e32_json
            import os as _e32_os
            import sys as _e32_sys

            if _e32_os.environ.get("SENTINEL_E32_PREFIX_REPLAY", "0") == "1":
                _e32_ctx_path = _e32_os.environ.get(
                    "SENTINEL_E32_CONTEXT", "/model/sentinel_e32_context.json"
                )
                try:
                    with open(_e32_ctx_path) as _e32_ctx_f:
                        _e32_ctx = _e32_json.load(_e32_ctx_f)
                except Exception as _e32_ctx_e:
                    _e32_ctx = {"context_error": f"{type(_e32_ctx_e).__name__}: {_e32_ctx_e}"}
                _e32_cands = []
                for _e32_cmd in (0, 1, 2):
                    _e32_op = self.model.planning_head.forward(
                        bev_embed,
                        occ_mask,
                        outs_motion["bev_pos"],
                        outs_motion["sdc_traj_query"],
                        outs_motion["sdc_track_query"],
                        command=torch.tensor(_e32_cmd).to(self.device).unsqueeze(0),
                    )
                    _e32_cands.append(
                        _format_trajs(_e32_op["sdc_traj"])[0].cpu().numpy().tolist()
                    )
                _e32_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e32_stash = getattr(self.model.planning_head, "_sentinel_e32_stash", {})
                _e32_rec = {
                    "scene": _e32_ctx.get("scene", ""),
                    "split": _e32_ctx.get("split", ""),
                    "sample_index": _e32_ctx.get("sample_index", None),
                    "timestamp_us": _e32_ctx.get("timestamp_us", None),
                    "target_row": bool(_e32_ctx.get("target_row", False)),
                    "source_label": _e32_ctx.get("source_label", None),
                    "source_label_name": _e32_ctx.get("source_label_name", ""),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist(),
                    "cands": _e32_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e32_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e32_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e32_n_obj else []
                    ),
                }
                if "context_error" in _e32_ctx:
                    _e32_rec["context_error"] = _e32_ctx["context_error"]
                _e32_rec.update(_e32_stash)
                with open(
                    _e32_os.environ.get("SENTINEL_E32_LOG", "/model/sentinel_e32_prefix.jsonl"),
                    "a",
                ) as _e32_f:
                    _e32_f.write(_e32_json.dumps(_e32_rec) + "\n")
        except Exception as _e32_e2:
            print(f"E32_LOG_ERROR: {type(_e32_e2).__name__}: {_e32_e2}",
                  file=_e32_sys.stderr, flush=True)
        # SENTINEL_E32_PREFIX_REPLAY end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter32 prefix-replay context and reset markers ------------------------------
import json as _e32_srv_json
import os as _e32_srv_os
from fastapi import Request as _e32_Request


def _e32_reset_marker():
    if _e32_srv_os.environ.get("SENTINEL_E32_PREFIX_REPLAY", "0") != "1":
        return
    try:
        with open(
            _e32_srv_os.environ.get("SENTINEL_E32_LOG", "/model/sentinel_e32_prefix.jsonl"),
            "a",
        ) as _e32_srv_f:
            _e32_srv_f.write(_e32_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e32_context")
async def sentinel_e32_context(request: _e32_Request) -> bool:
    payload = await request.json()
    with open(
        _e32_srv_os.environ.get("SENTINEL_E32_CONTEXT", "/model/sentinel_e32_context.json"),
        "w",
    ) as _e32_ctx_f:
        _e32_srv_json.dump(payload, _e32_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e32_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E32_PREFIX_REPLAY_PATCHED")
