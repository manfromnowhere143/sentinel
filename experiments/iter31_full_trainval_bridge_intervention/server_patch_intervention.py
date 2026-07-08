#!/usr/bin/env python3
"""Iteration-31 UniAD patch: bridge-centroid intervention logging.

This patch is applied on the GPU box before canary, calibration, or heldout
replay. It restores the UniAD source files first, then inserts a single
pre-registered intervention at the motion/planning bridge.
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

PRE_CALL = r'''        # SENTINEL_E31_BRIDGE_INTERVENTION: original forward, bridge patch, and stash.
        try:
            import hashlib as _e31_hashlib
            import json as _e31_json
            import os as _e31_os
            import sys as _e31_sys

            def _e31_bridge_hash(_e31_last, _e31_track):
                _e31_flat = torch.cat([
                    _e31_last.detach().float().reshape(-1).cpu(),
                    _e31_track.detach().float().reshape(-1).cpu(),
                ])
                return _e31_hashlib.sha256(_e31_flat.numpy().tobytes()).hexdigest()

            def _e31_plan(_e31_cmd, _e31_traj_query, _e31_track_query):
                _e31_out = self.model.planning_head.forward(
                    bev_embed,
                    occ_mask,
                    outs_motion["bev_pos"],
                    _e31_traj_query,
                    _e31_track_query,
                    command=torch.tensor(int(_e31_cmd)).to(self.device).unsqueeze(0),
                )
                return _format_trajs(_e31_out["sdc_traj"])[0].cpu().numpy().tolist()

            _e31_enabled = _e31_os.environ.get("SENTINEL_E31_INTERVENTION", "0") == "1"
            if _e31_enabled:
                _e31_tq = outs_motion["sdc_traj_query"]
                _e31_trk = outs_motion["sdc_track_query"]
                _e31_last = _e31_tq[-1]
                _e31_alpha = float(_e31_os.environ.get("SENTINEL_E31_ALPHA", "0.0"))
                _e31_dir_path = _e31_os.environ.get(
                    "SENTINEL_E31_DIRECTION", "/model/iter31_direction.json"
                )
                _e31_direction_sha = ""
                _e31_direction_values = []
                with open(_e31_dir_path) as _e31_dir_f:
                    _e31_direction_payload = _e31_json.load(_e31_dir_f)
                _e31_direction_values = list(_e31_direction_payload["direction_raw"])
                _e31_direction_sha = _e31_direction_payload.get(
                    "direction_and_fit_stats_sha256", ""
                )
                if len(_e31_direction_values) != 1792:
                    raise RuntimeError(f"direction length {len(_e31_direction_values)} != 1792")

                _e31_original_exec = _e31_plan(int(input.command), _e31_tq, _e31_trk)
                _e31_original_cands = [_e31_plan(_e31_cmd, _e31_tq, _e31_trk) for _e31_cmd in (0, 1, 2)]
                _e31_original_bridge_sha = _e31_bridge_hash(_e31_last, _e31_trk)

                _e31_applied = abs(_e31_alpha) > 0.0
                if _e31_applied:
                    _e31_direction = torch.tensor(
                        _e31_direction_values,
                        dtype=_e31_last.detach().float().dtype,
                        device=_e31_last.device,
                    )
                    _e31_dir_last = _e31_direction[:1536].reshape(_e31_last.shape).to(
                        device=_e31_last.device,
                        dtype=_e31_last.dtype,
                    )
                    _e31_dir_trk = _e31_direction[1536:].reshape(_e31_trk.shape).to(
                        device=_e31_trk.device,
                        dtype=_e31_trk.dtype,
                    )
                    outs_motion["sdc_traj_query"][-1] = _e31_last + _e31_alpha * _e31_dir_last
                    outs_motion["sdc_track_query"] = _e31_trk + _e31_alpha * _e31_dir_trk
                    _e31_last_after = outs_motion["sdc_traj_query"][-1]
                    _e31_trk_after = outs_motion["sdc_track_query"]
                else:
                    _e31_last_after = _e31_last
                    _e31_trk_after = _e31_trk

                self.model.planning_head._sentinel_e31_stash = {
                    "intervention_alpha": _e31_alpha,
                    "intervention_applied": bool(_e31_applied),
                    "intervention_direction_json": _e31_dir_path,
                    "intervention_direction_sha256": _e31_direction_sha,
                    "original_bridge_sha256": _e31_original_bridge_sha,
                    "intervened_bridge_sha256": _e31_bridge_hash(_e31_last_after, _e31_trk_after),
                    "sdc_traj_query_last_shape": list(_e31_last_after.shape),
                    "sdc_traj_query_last_dtype": str(_e31_last_after.dtype),
                    "sdc_track_query_shape": list(_e31_trk_after.shape),
                    "sdc_track_query_dtype": str(_e31_trk_after.dtype),
                    "original_traj": _e31_original_exec,
                    "original_cands": _e31_original_cands,
                }
        except Exception as _e31_e:
            print(f"E31_PRE_CALL_ERROR: {type(_e31_e).__name__}: {_e31_e}",
                  file=_e31_sys.stderr, flush=True)
            try:
                self.model.planning_head._sentinel_e31_stash = {
                    "intervention_error": f"{type(_e31_e).__name__}: {_e31_e}"
                }
            except Exception:
                pass

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E31_BRIDGE_INTERVENTION: log original/intervened trajectories.
        try:
            import json as _e31_json
            import os as _e31_os
            import sys as _e31_sys

            if _e31_os.environ.get("SENTINEL_E31_INTERVENTION", "0") == "1":
                _e31_ctx_path = _e31_os.environ.get(
                    "SENTINEL_E31_CONTEXT", "/model/sentinel_e31_context.json"
                )
                try:
                    with open(_e31_ctx_path) as _e31_ctx_f:
                        _e31_ctx = _e31_json.load(_e31_ctx_f)
                except Exception as _e31_ctx_e:
                    _e31_ctx = {"context_error": f"{type(_e31_ctx_e).__name__}: {_e31_ctx_e}"}
                _e31_cands = []
                for _e31_cmd in (0, 1, 2):
                    _e31_op = self.model.planning_head.forward(
                        bev_embed,
                        occ_mask,
                        outs_motion["bev_pos"],
                        outs_motion["sdc_traj_query"],
                        outs_motion["sdc_track_query"],
                        command=torch.tensor(_e31_cmd).to(self.device).unsqueeze(0),
                    )
                    _e31_cands.append(
                        _format_trajs(_e31_op["sdc_traj"])[0].cpu().numpy().tolist()
                    )
                _e31_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e31_stash = getattr(self.model.planning_head, "_sentinel_e31_stash", {})
                _e31_intervened_traj = _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist()
                _e31_rec = {
                    "scene": _e31_ctx.get("scene", ""),
                    "split": _e31_ctx.get("split", ""),
                    "sample_index": _e31_ctx.get("sample_index", None),
                    "timestamp_us": _e31_ctx.get("timestamp_us", None),
                    "label": _e31_ctx.get("label", None),
                    "label_name": _e31_ctx.get("label_name", ""),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _e31_intervened_traj,
                    "cands": _e31_cands,
                    "intervened_traj": _e31_intervened_traj,
                    "intervened_cands": _e31_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e31_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e31_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e31_n_obj else []
                    ),
                }
                if "context_error" in _e31_ctx:
                    _e31_rec["context_error"] = _e31_ctx["context_error"]
                _e31_rec.update(_e31_stash)
                with open(
                    _e31_os.environ.get("SENTINEL_E31_LOG", "/model/sentinel_e31_intervention.jsonl"),
                    "a",
                ) as _e31_f:
                    _e31_f.write(_e31_json.dumps(_e31_rec) + "\n")
        except Exception as _e31_e2:
            print(f"E31_LOG_ERROR: {type(_e31_e2).__name__}: {_e31_e2}",
                  file=_e31_sys.stderr, flush=True)
        # SENTINEL_E31_BRIDGE_INTERVENTION end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter31 bridge-intervention context and reset markers -------------------------
import json as _e31_srv_json
import os as _e31_srv_os
from fastapi import Request as _e31_Request


def _e31_reset_marker():
    if _e31_srv_os.environ.get("SENTINEL_E31_INTERVENTION", "0") != "1":
        return
    try:
        with open(
            _e31_srv_os.environ.get("SENTINEL_E31_LOG", "/model/sentinel_e31_intervention.jsonl"),
            "a",
        ) as _e31_srv_f:
            _e31_srv_f.write(_e31_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e31_context")
async def sentinel_e31_context(request: _e31_Request) -> bool:
    payload = await request.json()
    with open(
        _e31_srv_os.environ.get("SENTINEL_E31_CONTEXT", "/model/sentinel_e31_context.json"),
        "w",
    ) as _e31_ctx_f:
        _e31_srv_json.dump(payload, _e31_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e31_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E31_BRIDGE_INTERVENTION_PATCHED")
