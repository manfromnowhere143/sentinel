#!/usr/bin/env python3
"""Iteration-37 UniAD patch: prefix-preserving track-query intervention logging."""

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

PRE_CALL = r'''        # SENTINEL_E37_TRACK_QUERY_INTERVENTION: target-aware track-query patch and stash.
        try:
            import hashlib as _e37_hashlib
            import json as _e37_json
            import os as _e37_os
            import sys as _e37_sys

            def _e37_tensor_hash(*_e37_tensors):
                _e37_flat = torch.cat([
                    _e37_tensor.detach().float().reshape(-1).cpu()
                    for _e37_tensor in _e37_tensors
                ])
                return _e37_hashlib.sha256(_e37_flat.numpy().tobytes()).hexdigest()

            def _e37_bridge_hash(_e37_last, _e37_track):
                return _e37_tensor_hash(_e37_last, _e37_track)

            def _e37_plan(_e37_cmd, _e37_traj_query, _e37_track_query):
                _e37_out = self.model.planning_head.forward(
                    bev_embed,
                    occ_mask,
                    outs_motion["bev_pos"],
                    _e37_traj_query,
                    _e37_track_query,
                    command=torch.tensor(int(_e37_cmd)).to(self.device).unsqueeze(0),
                )
                return _format_trajs(_e37_out["sdc_traj"])[0].cpu().numpy().tolist()

            _e37_enabled = _e37_os.environ.get("SENTINEL_E37_PREFIX_INTERVENTION", "0") == "1"
            if _e37_enabled:
                _e37_ctx_path = _e37_os.environ.get(
                    "SENTINEL_E37_CONTEXT", "/model/sentinel_e37_context.json"
                )
                try:
                    with open(_e37_ctx_path) as _e37_ctx_f:
                        _e37_ctx = _e37_json.load(_e37_ctx_f)
                except Exception as _e37_ctx_e:
                    _e37_ctx = {"context_error": f"{type(_e37_ctx_e).__name__}: {_e37_ctx_e}"}

                _e37_target_row = bool(_e37_ctx.get("target_row", False))
                _e37_run_alpha = float(_e37_os.environ.get("SENTINEL_E37_ALPHA", "0.0"))
                _e37_alpha = _e37_run_alpha if _e37_target_row else 0.0
                _e37_tq = outs_motion["sdc_traj_query"]
                _e37_trk = outs_motion["sdc_track_query"]
                _e37_last = _e37_tq[-1]
                _e37_dir_path = _e37_os.environ.get(
                    "SENTINEL_E37_DIRECTION", "/model/track_query_direction_iter37.json"
                )
                with open(_e37_dir_path) as _e37_dir_f:
                    _e37_direction_payload = _e37_json.load(_e37_dir_f)
                _e37_direction_values = list(_e37_direction_payload["direction_raw"])
                _e37_direction_sha = _e37_direction_payload.get(
                    "direction_and_fit_stats_sha256", ""
                )
                if len(_e37_direction_values) != 256:
                    raise RuntimeError(f"direction length {len(_e37_direction_values)} != 256")

                _e37_original_bridge_sha = _e37_bridge_hash(_e37_last, _e37_trk)
                _e37_original_track_sha = _e37_tensor_hash(_e37_trk)
                _e37_original_traj_last_sha = _e37_tensor_hash(_e37_last)
                _e37_stash = {
                    "target_row": bool(_e37_target_row),
                    "run_alpha": float(_e37_run_alpha),
                    "intervention_alpha": float(_e37_alpha),
                    "intervention_applied": False,
                    "target_site": "track_query",
                    "intervention_direction_json": _e37_dir_path,
                    "intervention_direction_sha256": _e37_direction_sha,
                    "server_patch_sha256": _e37_os.environ.get("SENTINEL_E37_PATCH_SHA256", ""),
                    "uniad_source_commit": _e37_os.environ.get("SENTINEL_E37_UNIAD_COMMIT", ""),
                    "original_bridge_sha256": _e37_original_bridge_sha,
                    "original_track_query_sha256": _e37_original_track_sha,
                    "original_sdc_traj_query_last_sha256": _e37_original_traj_last_sha,
                    "sdc_traj_query_last_shape": list(_e37_last.shape),
                    "sdc_traj_query_last_dtype": str(_e37_last.dtype),
                    "sdc_track_query_shape": list(_e37_trk.shape),
                    "sdc_track_query_dtype": str(_e37_trk.dtype),
                    "iter37_patch_mode": "prefix_preserving_track_query_intervention",
                }

                if _e37_target_row and abs(_e37_alpha) > 0.0:
                    _e37_stash["original_traj"] = _e37_plan(int(input.command), _e37_tq, _e37_trk)
                    _e37_stash["original_cands"] = [
                        _e37_plan(_e37_cmd, _e37_tq, _e37_trk) for _e37_cmd in (0, 1, 2)
                    ]

                _e37_applied = bool(_e37_target_row and abs(_e37_alpha) > 0.0)
                if _e37_applied:
                    _e37_direction = torch.tensor(
                        _e37_direction_values,
                        dtype=_e37_trk.detach().float().dtype,
                        device=_e37_trk.device,
                    )
                    _e37_dir_trk = _e37_direction.reshape(_e37_trk.shape).to(
                        device=_e37_trk.device,
                        dtype=_e37_trk.dtype,
                    )
                    outs_motion["sdc_track_query"] = _e37_trk + _e37_alpha * _e37_dir_trk
                    _e37_last_after = _e37_last
                    _e37_trk_after = outs_motion["sdc_track_query"]
                else:
                    _e37_last_after = _e37_last
                    _e37_trk_after = _e37_trk

                _e37_intervened_bridge_sha = _e37_bridge_hash(_e37_last_after, _e37_trk_after)
                _e37_intervened_track_sha = _e37_tensor_hash(_e37_trk_after)
                _e37_intervened_traj_last_sha = _e37_tensor_hash(_e37_last_after)
                _e37_stash.update(
                    {
                        "intervention_applied": bool(_e37_applied),
                        "intervened_bridge_sha256": _e37_intervened_bridge_sha,
                        "bridge_sha256": _e37_intervened_bridge_sha,
                        "bridge_sha256_changed": _e37_intervened_bridge_sha != _e37_original_bridge_sha,
                        "intervened_track_query_sha256": _e37_intervened_track_sha,
                        "track_query_sha256_changed": _e37_intervened_track_sha != _e37_original_track_sha,
                        "intervened_sdc_traj_query_last_sha256": _e37_intervened_traj_last_sha,
                        "sdc_traj_query_last_sha256_changed": (
                            _e37_intervened_traj_last_sha != _e37_original_traj_last_sha
                        ),
                        "sdc_traj_query_last": _e37_last_after.detach().float().cpu().numpy().ravel().tolist(),
                        "sdc_track_query": _e37_trk_after.detach().float().cpu().numpy().ravel().tolist(),
                    }
                )
                self.model.planning_head._sentinel_e37_stash = _e37_stash
        except Exception as _e37_e:
            print(f"E37_PRE_CALL_ERROR: {type(_e37_e).__name__}: {_e37_e}",
                  file=_e37_sys.stderr, flush=True)
            try:
                self.model.planning_head._sentinel_e37_stash = {
                    "intervention_error": f"{type(_e37_e).__name__}: {_e37_e}"
                }
            except Exception:
                pass

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E37_TRACK_QUERY_INTERVENTION: log prefix and target rows.
        try:
            import json as _e37_json
            import os as _e37_os
            import sys as _e37_sys

            if _e37_os.environ.get("SENTINEL_E37_PREFIX_INTERVENTION", "0") == "1":
                _e37_ctx_path = _e37_os.environ.get(
                    "SENTINEL_E37_CONTEXT", "/model/sentinel_e37_context.json"
                )
                try:
                    with open(_e37_ctx_path) as _e37_ctx_f:
                        _e37_ctx = _e37_json.load(_e37_ctx_f)
                except Exception as _e37_ctx_e:
                    _e37_ctx = {"context_error": f"{type(_e37_ctx_e).__name__}: {_e37_ctx_e}"}
                _e37_target_row = bool(_e37_ctx.get("target_row", False))
                _e37_cands = []
                if _e37_target_row:
                    for _e37_cmd in (0, 1, 2):
                        _e37_op = self.model.planning_head.forward(
                            bev_embed,
                            occ_mask,
                            outs_motion["bev_pos"],
                            outs_motion["sdc_traj_query"],
                            outs_motion["sdc_track_query"],
                            command=torch.tensor(_e37_cmd).to(self.device).unsqueeze(0),
                        )
                        _e37_cands.append(
                            _format_trajs(_e37_op["sdc_traj"])[0].cpu().numpy().tolist()
                        )
                _e37_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e37_stash = getattr(self.model.planning_head, "_sentinel_e37_stash", {})
                _e37_intervened_traj = _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist()
                if _e37_target_row and "original_traj" not in _e37_stash:
                    _e37_stash["original_traj"] = _e37_intervened_traj
                    _e37_stash["original_cands"] = _e37_cands
                _e37_rec = {
                    "scene": _e37_ctx.get("scene", ""),
                    "split": _e37_ctx.get("split", ""),
                    "sample_index": _e37_ctx.get("sample_index", None),
                    "timestamp_us": _e37_ctx.get("timestamp_us", None),
                    "target_row": _e37_target_row,
                    "source_label": _e37_ctx.get("source_label", None),
                    "source_label_name": _e37_ctx.get("source_label_name", ""),
                    "label": _e37_ctx.get("label", None),
                    "label_name": _e37_ctx.get("label_name", ""),
                    "run_alpha": _e37_ctx.get("run_alpha", None),
                    "alpha": _e37_ctx.get("alpha", None),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _e37_intervened_traj,
                    "cands": _e37_cands,
                    "intervened_traj": _e37_intervened_traj,
                    "intervened_cands": _e37_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e37_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e37_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e37_n_obj else []
                    ),
                }
                if "context_error" in _e37_ctx:
                    _e37_rec["context_error"] = _e37_ctx["context_error"]
                _e37_rec.update(_e37_stash)
                with open(
                    _e37_os.environ.get("SENTINEL_E37_LOG", "/model/sentinel_e37_intervention.jsonl"),
                    "a",
                ) as _e37_f:
                    _e37_f.write(_e37_json.dumps(_e37_rec) + "\n")
        except Exception as _e37_e2:
            print(f"E37_LOG_ERROR: {type(_e37_e2).__name__}: {_e37_e2}",
                  file=_e37_sys.stderr, flush=True)
        # SENTINEL_E37_TRACK_QUERY_INTERVENTION end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter37 prefix-preserving track-query intervention context/reset ---------------
import json as _e37_srv_json
import os as _e37_srv_os
from fastapi import Request as _e37_Request


def _e37_reset_marker():
    if _e37_srv_os.environ.get("SENTINEL_E37_PREFIX_INTERVENTION", "0") != "1":
        return
    try:
        with open(
            _e37_srv_os.environ.get("SENTINEL_E37_LOG", "/model/sentinel_e37_intervention.jsonl"),
            "a",
        ) as _e37_srv_f:
            _e37_srv_f.write(_e37_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e37_context")
async def sentinel_e37_context(request: _e37_Request) -> bool:
    payload = await request.json()
    with open(
        _e37_srv_os.environ.get("SENTINEL_E37_CONTEXT", "/model/sentinel_e37_context.json"),
        "w",
    ) as _e37_ctx_f:
        _e37_srv_json.dump(payload, _e37_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e37_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E37_TRACK_QUERY_INTERVENTION_PATCHED")
