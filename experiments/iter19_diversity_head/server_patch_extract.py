import subprocess

UNIAD = '/opt/sentinel-stack/UniAD'
SRV = f'{UNIAD}/inference/server.py'
PH = f'{UNIAD}/projects/mmdet3d_plugin/uniad/dense_heads/planning_head.py'
subprocess.run(['git', '-C', UNIAD, 'checkout', '--',
                'inference/server.py', 'projects/mmdet3d_plugin/uniad/dense_heads/planning_head.py'],
               check=True)

# ---- planning head: stash the conditioning tensors at their source ---------------------------
src = open(PH).read()
anchor = ("        outs_planning = self(bev_embed, occ_mask, bev_pos, sdc_traj_query, "
          "sdc_track_query, command)\n        return outs_planning")
assert anchor in src, 'planning_head forward_test anchor not found'
patched = anchor.replace(
    "        return outs_planning",
    "        self._sentinel_stash = {\n"
    "            'sdc_traj_query': sdc_traj_query.detach().float().cpu().numpy().ravel().tolist(),\n"
    "            'sdc_traj_query_shape': list(sdc_traj_query.shape),\n"
    "            'sdc_track_query': sdc_track_query.detach().float().cpu().numpy().ravel().tolist(),\n"
    "            'sdc_track_query_shape': list(sdc_track_query.shape),\n"
    "        }\n"
    "        return outs_planning",
)
open(PH, 'w').write(src.replace(anchor, patched, 1))

# ---- server: dump per-frame conditioning + trajectory when SENTINEL_EXTRACT=1 ----------------
src = open(SRV).read()
HELPERS = '''
# ---- Sentinel iter19: training-data extraction (planning-query conditioning dump) ------------
import json as _xjson, os as _xos
_X_LOG = _xos.environ.get("SENTINEL_EXTRACT_LOG", "/model/sentinel_extract.jsonl")
_x_on = _xos.environ.get("SENTINEL_EXTRACT", "0") == "1"


def _x_reset():
    if not _x_on:
        return
    try:
        with open(_X_LOG, "a") as f:
            f.write(_xjson.dumps({"reset": True}) + "\\n")
    except Exception:
        pass


def _x_dump(out, data):
    if not _x_on:
        return
    try:
        stash = getattr(uniad_runner.model.planning_head, "_sentinel_stash", None) or {}
        rec = {
            "ts": int(data.timestamp),
            "command": int(data.command),
            "ego2world": [[float(v) for v in row] for row in data.ego2world],
            "traj": [[float(x), float(y)] for x, y in out.trajectory.tolist()],
        }
        rec.update(stash)
        with open(_X_LOG, "a") as f:
            f.write(_xjson.dumps(rec) + "\\n")
    except Exception as e:
        try:
            with open(_X_LOG, "a") as f:
                f.write(_xjson.dumps({"extract_err": str(e)}) + "\\n")
        except Exception:
            pass


'''
anchor = '@app.get("/alive")'
assert anchor in src
src = src.replace(anchor, HELPERS + anchor, 1)
infer_old = ("    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
             "    return InferenceOutputs(\n")
assert infer_old in src
src = src.replace(infer_old,
                  "    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
                  "    _x_dump(uniad_output, data)\n"
                  "    return InferenceOutputs(\n", 1)
reset_old = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert reset_old in src
src = src.replace(reset_old,
                  "async def reset_runner() -> bool:\n    _x_reset()\n    uniad_runner.reset()", 1)
open(SRV, 'w').write(src)
print("EXTRACT_PATCHED")
