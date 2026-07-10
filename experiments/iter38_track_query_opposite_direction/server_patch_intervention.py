#!/usr/bin/env python3
"""Iteration-38 UniAD patch: prefix-preserving track-query intervention logging."""

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

PRE_CALL = r'''        # SENTINEL_E38_TRACK_QUERY_INTERVENTION: target-aware track-query patch and stash.
        try:
            import hashlib as _e38_hashlib
            import json as _e38_json
            import os as _e38_os
            import sys as _e38_sys

            def _e38_tensor_hash(*_e38_tensors):
                _e38_flat = torch.cat([
                    _e38_tensor.detach().float().reshape(-1).cpu()
                    for _e38_tensor in _e38_tensors
                ])
                return _e38_hashlib.sha256(_e38_flat.numpy().tobytes()).hexdigest()

            def _e38_bridge_hash(_e38_last, _e38_track):
                return _e38_tensor_hash(_e38_last, _e38_track)

            def _e38_plan(_e38_cmd, _e38_traj_query, _e38_track_query):
                _e38_out = self.model.planning_head.forward(
                    bev_embed,
                    occ_mask,
                    outs_motion["bev_pos"],
                    _e38_traj_query,
                    _e38_track_query,
                    command=torch.tensor(int(_e38_cmd)).to(self.device).unsqueeze(0),
                )
                return _format_trajs(_e38_out["sdc_traj"])[0].cpu().numpy().tolist()

            _e38_enabled = _e38_os.environ.get("SENTINEL_E38_PREFIX_INTERVENTION", "0") == "1"
            if _e38_enabled:
                _e38_ctx_path = _e38_os.environ.get(
                    "SENTINEL_E38_CONTEXT", "/model/sentinel_e38_context.json"
                )
                try:
                    with open(_e38_ctx_path) as _e38_ctx_f:
                        _e38_ctx = _e38_json.load(_e38_ctx_f)
                except Exception as _e38_ctx_e:
                    _e38_ctx = {"context_error": f"{type(_e38_ctx_e).__name__}: {_e38_ctx_e}"}

                _e38_target_row = bool(_e38_ctx.get("target_row", False))
                _e38_run_alpha = float(_e38_os.environ.get("SENTINEL_E38_ALPHA", "0.0"))
                _e38_alpha = _e38_run_alpha if _e38_target_row else 0.0
                _e38_tq = outs_motion["sdc_traj_query"]
                _e38_trk = outs_motion["sdc_track_query"]
                _e38_last = _e38_tq[-1]
                _e38_dir_path = _e38_os.environ.get(
                    "SENTINEL_E38_DIRECTION", "/model/track_query_opposite_direction_iter38.json"
                )
                with open(_e38_dir_path) as _e38_dir_f:
                    _e38_direction_payload = _e38_json.load(_e38_dir_f)
                _e38_direction_values = list(_e38_direction_payload["direction_raw"])
                _e38_direction_sha = _e38_direction_payload.get(
                    "direction_and_fit_stats_sha256", ""
                )
                _e38_iter37_sign = _e38_direction_payload.get("iter37_sign_equivalence", {})
                if len(_e38_direction_values) != 256:
                    raise RuntimeError(f"direction length {len(_e38_direction_values)} != 256")

                _e38_original_bridge_sha = _e38_bridge_hash(_e38_last, _e38_trk)
                _e38_original_track_sha = _e38_tensor_hash(_e38_trk)
                _e38_original_traj_last_sha = _e38_tensor_hash(_e38_last)
                _e38_stash = {
                    "target_row": bool(_e38_target_row),
                    "run_alpha": float(_e38_run_alpha),
                    "intervention_alpha": float(_e38_alpha),
                    "intervention_applied": False,
                    "target_site": "track_query",
                    "intervention_direction_json": _e38_dir_path,
                    "intervention_direction_sha256": _e38_direction_sha,
                    "iter37_direction_file_sha256": _e38_iter37_sign.get("file_sha256", ""),
                    "iter37_direction_and_fit_stats_sha256": _e38_iter37_sign.get(
                        "direction_and_fit_stats_sha256", ""
                    ),
                    "iter37_sign_equivalence_pass": bool(
                        _e38_iter37_sign.get("sign_equivalence_pass", False)
                    ),
                    "server_patch_sha256": _e38_os.environ.get("SENTINEL_E38_PATCH_SHA256", ""),
                    "uniad_source_commit": _e38_os.environ.get("SENTINEL_E38_UNIAD_COMMIT", ""),
                    "original_bridge_sha256": _e38_original_bridge_sha,
                    "original_track_query_sha256": _e38_original_track_sha,
                    "original_sdc_traj_query_last_sha256": _e38_original_traj_last_sha,
                    "sdc_traj_query_last_shape": list(_e38_last.shape),
                    "sdc_traj_query_last_dtype": str(_e38_last.dtype),
                    "sdc_track_query_shape": list(_e38_trk.shape),
                    "sdc_track_query_dtype": str(_e38_trk.dtype),
                    "iter38_patch_mode": "prefix_preserving_track_query_intervention",
                }

                if _e38_target_row and abs(_e38_alpha) > 0.0:
                    _e38_stash["original_traj"] = _e38_plan(int(input.command), _e38_tq, _e38_trk)
                    _e38_stash["original_cands"] = [
                        _e38_plan(_e38_cmd, _e38_tq, _e38_trk) for _e38_cmd in (0, 1, 2)
                    ]

                _e38_applied = bool(_e38_target_row and abs(_e38_alpha) > 0.0)
                if _e38_applied:
                    _e38_direction = torch.tensor(
                        _e38_direction_values,
                        dtype=_e38_trk.detach().float().dtype,
                        device=_e38_trk.device,
                    )
                    _e38_dir_trk = _e38_direction.reshape(_e38_trk.shape).to(
                        device=_e38_trk.device,
                        dtype=_e38_trk.dtype,
                    )
                    outs_motion["sdc_track_query"] = _e38_trk + _e38_alpha * _e38_dir_trk
                    _e38_last_after = _e38_last
                    _e38_trk_after = outs_motion["sdc_track_query"]
                else:
                    _e38_last_after = _e38_last
                    _e38_trk_after = _e38_trk

                _e38_intervened_bridge_sha = _e38_bridge_hash(_e38_last_after, _e38_trk_after)
                _e38_intervened_track_sha = _e38_tensor_hash(_e38_trk_after)
                _e38_intervened_traj_last_sha = _e38_tensor_hash(_e38_last_after)
                _e38_stash.update(
                    {
                        "intervention_applied": bool(_e38_applied),
                        "intervened_bridge_sha256": _e38_intervened_bridge_sha,
                        "bridge_sha256": _e38_intervened_bridge_sha,
                        "bridge_sha256_changed": _e38_intervened_bridge_sha != _e38_original_bridge_sha,
                        "intervened_track_query_sha256": _e38_intervened_track_sha,
                        "track_query_sha256_changed": _e38_intervened_track_sha != _e38_original_track_sha,
                        "intervened_sdc_traj_query_last_sha256": _e38_intervened_traj_last_sha,
                        "sdc_traj_query_last_sha256_changed": (
                            _e38_intervened_traj_last_sha != _e38_original_traj_last_sha
                        ),
                        "sdc_traj_query_last": _e38_last_after.detach().float().cpu().numpy().ravel().tolist(),
                        "sdc_track_query": _e38_trk_after.detach().float().cpu().numpy().ravel().tolist(),
                    }
                )
                self.model.planning_head._sentinel_e38_stash = _e38_stash
        except Exception as _e38_e:
            print(f"E38_PRE_CALL_ERROR: {type(_e38_e).__name__}: {_e38_e}",
                  file=_e38_sys.stderr, flush=True)
            try:
                self.model.planning_head._sentinel_e38_stash = {
                    "intervention_error": f"{type(_e38_e).__name__}: {_e38_e}"
                }
            except Exception:
                pass

'''
runner = runner.replace(CALL_ANCHOR, PRE_CALL + CALL_ANCHOR, 1)

LOG_ANCHOR = '        n_objects = outs_track[0]["boxes_3d"].tensor.shape[0]\n'
assert LOG_ANCHOR in runner, "object-count anchor not found"
assert runner.count(LOG_ANCHOR) == 1, "object-count anchor not unique"

LOG_INSERT = r'''        # SENTINEL_E38_TRACK_QUERY_INTERVENTION: log prefix and target rows.
        try:
            import json as _e38_json
            import os as _e38_os
            import sys as _e38_sys

            if _e38_os.environ.get("SENTINEL_E38_PREFIX_INTERVENTION", "0") == "1":
                _e38_ctx_path = _e38_os.environ.get(
                    "SENTINEL_E38_CONTEXT", "/model/sentinel_e38_context.json"
                )
                try:
                    with open(_e38_ctx_path) as _e38_ctx_f:
                        _e38_ctx = _e38_json.load(_e38_ctx_f)
                except Exception as _e38_ctx_e:
                    _e38_ctx = {"context_error": f"{type(_e38_ctx_e).__name__}: {_e38_ctx_e}"}
                _e38_target_row = bool(_e38_ctx.get("target_row", False))
                _e38_cands = []
                if _e38_target_row:
                    for _e38_cmd in (0, 1, 2):
                        _e38_op = self.model.planning_head.forward(
                            bev_embed,
                            occ_mask,
                            outs_motion["bev_pos"],
                            outs_motion["sdc_traj_query"],
                            outs_motion["sdc_track_query"],
                            command=torch.tensor(_e38_cmd).to(self.device).unsqueeze(0),
                        )
                        _e38_cands.append(
                            _format_trajs(_e38_op["sdc_traj"])[0].cpu().numpy().tolist()
                        )
                _e38_n_obj = outs_track[0]["boxes_3d"].tensor.shape[0]
                _e38_stash = getattr(self.model.planning_head, "_sentinel_e38_stash", {})
                _e38_intervened_traj = _format_trajs(outs_planning["sdc_traj"])[0].cpu().numpy().tolist()
                if _e38_target_row and "original_traj" not in _e38_stash:
                    _e38_stash["original_traj"] = _e38_intervened_traj
                    _e38_stash["original_cands"] = _e38_cands
                _e38_rec = {
                    "scene": _e38_ctx.get("scene", ""),
                    "split": _e38_ctx.get("split", ""),
                    "sample_index": _e38_ctx.get("sample_index", None),
                    "timestamp_us": _e38_ctx.get("timestamp_us", None),
                    "target_row": _e38_target_row,
                    "source_label": _e38_ctx.get("source_label", None),
                    "source_label_name": _e38_ctx.get("source_label_name", ""),
                    "label": _e38_ctx.get("label", None),
                    "label_name": _e38_ctx.get("label_name", ""),
                    "run_alpha": _e38_ctx.get("run_alpha", None),
                    "alpha": _e38_ctx.get("alpha", None),
                    "runner_timestamp": int(input.timestamp),
                    "command": int(input.command),
                    "traj": _e38_intervened_traj,
                    "cands": _e38_cands,
                    "intervened_traj": _e38_intervened_traj,
                    "intervened_cands": _e38_cands,
                    "objs": (
                        _format_boxes(outs_track[0]["boxes_3d"]).cpu().numpy().tolist()
                        if _e38_n_obj else []
                    ),
                    "scores": (
                        outs_track[0]["scores_3d"].cpu().numpy().tolist() if _e38_n_obj else []
                    ),
                    "futs": (
                        _format_trajs(future_trajs[..., :2]).cpu().numpy().tolist()
                        if _e38_n_obj else []
                    ),
                }
                if "context_error" in _e38_ctx:
                    _e38_rec["context_error"] = _e38_ctx["context_error"]
                _e38_rec.update(_e38_stash)
                with open(
                    _e38_os.environ.get("SENTINEL_E38_LOG", "/model/sentinel_e38_intervention.jsonl"),
                    "a",
                ) as _e38_f:
                    _e38_f.write(_e38_json.dumps(_e38_rec) + "\n")
        except Exception as _e38_e2:
            print(f"E38_LOG_ERROR: {type(_e38_e2).__name__}: {_e38_e2}",
                  file=_e38_sys.stderr, flush=True)
        # SENTINEL_E38_TRACK_QUERY_INTERVENTION end.

'''
runner = runner.replace(LOG_ANCHOR, LOG_ANCHOR + LOG_INSERT, 1)
open(RUNNER, "w").write(runner)

server = open(SERVER).read()
HELPERS = r'''
# ---- Sentinel iter38 prefix-preserving track-query intervention context/reset ---------------
import json as _e38_srv_json
import os as _e38_srv_os
from fastapi import Request as _e38_Request


def _e38_reset_marker():
    if _e38_srv_os.environ.get("SENTINEL_E38_PREFIX_INTERVENTION", "0") != "1":
        return
    try:
        with open(
            _e38_srv_os.environ.get("SENTINEL_E38_LOG", "/model/sentinel_e38_intervention.jsonl"),
            "a",
        ) as _e38_srv_f:
            _e38_srv_f.write(_e38_srv_json.dumps({"reset": True}) + "\n")
    except Exception:
        pass


@app.post("/sentinel_e38_context")
async def sentinel_e38_context(request: _e38_Request) -> bool:
    payload = await request.json()
    with open(
        _e38_srv_os.environ.get("SENTINEL_E38_CONTEXT", "/model/sentinel_e38_context.json"),
        "w",
    ) as _e38_ctx_f:
        _e38_srv_json.dump(payload, _e38_ctx_f, sort_keys=True)
    return True


'''
SERVER_ANCHOR = '@app.get("/alive")'
assert SERVER_ANCHOR in server, "server alive anchor not found"
server = server.replace(SERVER_ANCHOR, HELPERS + SERVER_ANCHOR, 1)

RESET_ANCHOR = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert RESET_ANCHOR in server, "server reset anchor not found"
server = server.replace(
    RESET_ANCHOR,
    "async def reset_runner() -> bool:\n    _e38_reset_marker()\n    uniad_runner.reset()",
    1,
)
open(SERVER, "w").write(server)

print("E38_TRACK_QUERY_INTERVENTION_PATCHED")
