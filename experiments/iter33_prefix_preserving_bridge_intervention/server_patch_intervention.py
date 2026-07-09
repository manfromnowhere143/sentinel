#!/usr/bin/env python3
"""Iteration-33 UniAD patch: prefix-preserving bridge intervention logging."""

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

PRE_CALL = r'''        # SENTINEL_E33_PREFIX_BRIDGE_INTERVENTION: target-aware bridge patch and stash.
        try:
            import hashlib as _e33_hashlib
            import json as _e33_json
            import os as _e33_os
            import sys as _e33_sys

            def _e33_bridge_hash(_e33_last, _e33_track):
                _e33_flat = torch.cat([
                    _e33_last.detach().float().reshape(-1).cpu(),
                    _e33_track.detach().float().reshape(-1).cpu(),
                ])
                return _e33_hashlib.sha256(_e33_flat.numpy().tobytes()).hexdigest()

            def _e33_plan(_e33_cmd, _e33_traj_query, _e33_track_query):
                _e33_out = self.model.planning_head.forward(
                    bev_embed,
                    occ_mask,
                    outs_motion["bev_pos"],
                    _e33_traj_query,
                    _e33_track_query,
                    command=torch.tensor(int(_e33_cmd)).to(self.device).unsqueeze(0),
                )
                return _format_trajs(_e33_out["sdc_traj"])[0].cpu().numpy().tolist()

            _e33_enabled = _e33_os.environ.get("SENTINEL_E33_PREFIX_INTERVENTION", "0") == "1"
            if _e33_enabled:
                _e33_ctx_path = _e33_os.environ.get(
                    "SENTINEL_E33_CONTEXT", "/model/sentinel_e33_context.json"
                )
                try:
                    with open(_e33_ctx_path) as _e33_ctx_f:
                        _e33_ctx = _e33_json.load(_e33_ctx_f)
                except Exception as _e33_ctx_e:
                    _e33_ctx = {"context_error": f"{type(_e33_ctx_e).__name__}: {_e33_ctx_e}"}

                _e33_target_row = bool(_e33_ctx.get("target_row", False))
                _e33_run_alpha = float(_e33_os.environ.get("SENTINEL_E33_ALPHA", "0.0"))
                _e33_alpha = _e33_run_alpha if _e33_target_row else 0.0
                _e33_tq = outs_motion["sdc_traj_query"]
                _e33_trk = outs_motion["sdc_track_query"]
                _e33_last = _e33_tq[-1]
                _e33_dir_path = _e33_os.environ.get(
                    "SENTINEL_E33_DIRECTION", "/model/iter33_direction.json"
                )
                with open(_e33_dir_path) as _e33_dir_f:
                    _e33_direction_payload = _e33_json.load(_e33_dir_f)
                _e33_direction_values = list(_e33_direction_payload["direction_raw"])
                _e33_direction_sha = _e33_direction_payload.get(
                    "direction_and_fit_stats_sha256", ""
                )
                if len(_e33_direction_values) != 1792:
                    raise RuntimeError(f"direction length {len(_e33_direction_values)} != 1792")

                _e33_original_bridge_sha = _e33_bridge_hash(_e33_last, _e33_trk)
                _e33_stash = {
                    "target_row": bool(_e33_target_row),
                    "run_alpha": float(_e33_run_alpha),
                    "intervention_alpha": float(_e33_alpha),
                    "intervention_applied": False,
                    "intervention_direction_json": _e33_dir_path,
                    "intervention_direction_sha256": _e33_direction_sha,
                    "original_bridge_sha256": _e33_original_bridge_sha,
                    "sdc_traj_query_last_shape": list(_e33_last.shape),
                    "sdc_traj_query_last_dtype": str(_e33_last.dtype),
                    "sdc_track_query_shape": list(_e33_trk.shape),
                    "sdc_track_query_dtype": str(_e33_trk.dtype),
                    "iter33_patch_mode": "prefix_preserving_bridge_intervention",
                }

                if _e33_target_row:
                    _e33_stash["original_traj"] = _e33_plan(int(input.command), _e33_tq, _e33_trk)
                    _e33_stash["original_cands"] = [
                        _e33_plan(_e33_cmd, _e33_tq, _e33_trk) for _e33_cmd in (0, 1, 2)
                    ]

                _e33_applied = bool(_e33_target_row and abs(_e33_alpha) > 0.0)
                if _e33_applied:
                    _e33_direction = torch.tensor(
                        _e33_direction_values,
                        dtype=_e33_last.detach().float().dtype,
                        device=_e33_last.device,
                    )
                    _e33_dir_last = _e33_direction[:1536].reshape(_e33_last.shape).to(
                        device=_e33_last.device,
                        dtype=_e33_last.dtype,
                    )
                    _e33_dir_trk = _e33_direction[1536:].reshape(_e33_trk.shape).to(
                        device=_e33_trk.device,
                        dtype=_e33_trk.dtype,
                    )
                    outs_motion["sdc_traj_query"][-1] = _e33_last + _e33_alpha * _e33_dir_last
                    outs_motion["sdc_track_query"] = _e33_trk + _e33_alpha * _e33_dir_trk
                    _e33_last_after = outs_motion["sdc_traj_query"][-1]
                    _e33_trk_after = outs_motion["sdc_track_query"]
                else:
                    _e33_last_after = _e33_last
                    _e33_trk_after = _e33_trk

                _e33_intervened_bridge_sha = _e33_bridge_hash(_e33_last_after, _e33_trk_after)
                _e33_stash.update(
                    {
                        "intervention_applied": bool(_e33_applied),
                        "intervened_bridge_sha256": _e33_intervened_bridge_sha,
                        "bridge_sha256": _e33_intervened_bridge_sha,
                        "bridge_sha256_changed": _e33_intervened_bridge_sha != _e33_original_bridge_sha,
                        "sdc_traj_query_last": _e33_last_after.detach().float().cpu().numpy().ravel().tolist(),
                        "sdc_track_query": _e33_trk_after.detach().float().cpu().numpy().ravel().tolist(),
                    }
                )
                self.model.planning_head._sentinel_e33_stash = _e33_stash
        except Exception as _e33_e:
            print(f"E33_PRE_CALL_ERROR: {type(_e33_e).__name__}: {_e33_e}",
                  file=_e33_sys.stderr, flush=True)
            try:
                self.model.planning_head._sentinel_e33_stash = {
                    "intervention_error": f"{type(_e33_e).__name__}: {_e33_e}"
                }
            except Exception:
                pass

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E33_PREFIX_BRIDGE_INTERVENTION: log prefix and target rows.
        try:
            import json as _e33_json
            import os as _e33_os
            import sys as _e33_sys

            if _e33_os.environ.get("SENTINEL_E33_PREFIX_INTERVENTION", "0") == "1":
                _e33_ctx_path = _e33_os.environ.get(
                    "SENTINEL_E33_CONTEXT", "/model/sentinel_e33_context.json"
                )
                try:
                    with open(_e33_ctx_path) as _e33_ctx_f:
                        _e33_ctx = _e33_json.load(_e33_ctx_f)
                except Exception as _e33_ctx_e:
                    _e33_ctx = {"context_error": f"{type(_e33_ctx_e).__name__}: {_e33_ctx_e}"}
                _e33_target_row = bool(_e33_ctx.get("target_row", False))
                _e33_cands = []
                if _e33_target_row:
                    for _e33_cmd in (0, 1, 2):
                        _e33_op = self.model.planning_head.forward(
                            bev_embed,
                            occ_mask,
                            outs_motion["bev_pos"],
                            outs_motion["sdc_traj_query"],
                            outs_motion["sdc_track_query"],
                            command=torch.tensor(_e33_cmd).to(self.device).unsqueeze(0),
                        )
                        _e33_cands.append(
                            _format_trajs(_e33_op["sdc_traj"])[0].cpu().numpy().tolist()
                        )
                _e33_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e33_stash = getattr(self.model.planning_head, "_sentinel_e33_stash", {})
                _e33_intervened_traj = _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist()
                _e33_rec = {
                    "scene": _e33_ctx.get("scene", ""),
                    "split": _e33_ctx.get("split", ""),
                    "sample_index": _e33_ctx.get("sample_index", None),
                    "timestamp_us": _e33_ctx.get("timestamp_us", None),
                    "target_row": _e33_target_row,
                    "source_label": _e33_ctx.get("source_label", None),
                    "source_label_name": _e33_ctx.get("source_label_name", ""),
                    "label": _e33_ctx.get("label", None),
                    "label_name": _e33_ctx.get("label_name", ""),
                    "run_alpha": _e33_ctx.get("run_alpha", None),
                    "alpha": _e33_ctx.get("alpha", None),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _e33_intervened_traj,
                    "cands": _e33_cands,
                    "intervened_traj": _e33_intervened_traj,
                    "intervened_cands": _e33_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e33_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e33_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e33_n_obj else []
                    ),
                }
                if "context_error" in _e33_ctx:
                    _e33_rec["context_error"] = _e33_ctx["context_error"]
                _e33_rec.update(_e33_stash)
                with open(
                    _e33_os.environ.get("SENTINEL_E33_LOG", "/model/sentinel_e33_intervention.jsonl"),
                    "a",
                ) as _e33_f:
                    _e33_f.write(_e33_json.dumps(_e33_rec) + "\n")
        except Exception as _e33_e2:
            print(f"E33_LOG_ERROR: {type(_e33_e2).__name__}: {_e33_e2}",
                  file=_e33_sys.stderr, flush=True)
        # SENTINEL_E33_PREFIX_BRIDGE_INTERVENTION end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter33 prefix-preserving bridge-intervention context/reset -------------------
import json as _e33_srv_json
import os as _e33_srv_os
from fastapi import Request as _e33_Request


def _e33_reset_marker():
    if _e33_srv_os.environ.get("SENTINEL_E33_PREFIX_INTERVENTION", "0") != "1":
        return
    try:
        with open(
            _e33_srv_os.environ.get("SENTINEL_E33_LOG", "/model/sentinel_e33_intervention.jsonl"),
            "a",
        ) as _e33_srv_f:
            _e33_srv_f.write(_e33_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e33_context")
async def sentinel_e33_context(request: _e33_Request) -> bool:
    payload = await request.json()
    with open(
        _e33_srv_os.environ.get("SENTINEL_E33_CONTEXT", "/model/sentinel_e33_context.json"),
        "w",
    ) as _e33_ctx_f:
        _e33_srv_json.dump(payload, _e33_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e33_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E33_PREFIX_BRIDGE_INTERVENTION_PATCHED")
