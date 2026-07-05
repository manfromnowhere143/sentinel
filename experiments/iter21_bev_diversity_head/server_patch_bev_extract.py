import subprocess

UNIAD = '/opt/sentinel-stack/UniAD'
SRV = f'{UNIAD}/inference/server.py'
RUN = f'{UNIAD}/inference/runner.py'
subprocess.run(['git', '-C', UNIAD, 'checkout', '--', 'inference/server.py', 'inference/runner.py'],
               check=True)

# ---- runner: summarize scene-level BEV before the planning-query bottleneck ------------------
# The NCAP runner calls planning_head.forward directly. At that call site, UniAD's scene-level
# BEV tensor is still in local scope or in the track/motion dictionaries. We store an 8x8
# adaptive-average spatial summary, not planning queries, to test the iteration-21 mechanism.
src = open(RUN).read()
anchor = "        # get the planning output\n        outs_planning = self.model.planning_head.forward("
assert anchor in src, 'runner planning call-site anchor not found'
stash = r'''
        # SENTINEL_BEV_EXTRACT: scene-level BEV summary, before planning-query collapse.
        try:
            import math as _sb_math
            import torch as _sb_torch
            import torch.nn.functional as _sb_F

            _bev = locals().get('bev_embed', None)
            if _bev is None and isinstance(locals().get('outs_track', None), dict):
                _bev = outs_track.get('bev_embed')
            if _bev is None and isinstance(locals().get('outs_motion', None), dict):
                _bev = outs_motion.get('bev_embed')

            def _sb_pool8(_tensor):
                if isinstance(_tensor, (list, tuple)):
                    _tensor = _tensor[0]
                if not isinstance(_tensor, _sb_torch.Tensor):
                    return {'bev_err': 'bev_embed_not_tensor'}
                _x = _tensor.detach().float()
                _src_shape = list(_x.shape)
                while _x.dim() > 2 and _x.shape[0] == 1:
                    _x = _x.squeeze(0)
                if _x.dim() == 4:
                    if _x.shape[0] == 1:
                        _x = _x.squeeze(0)
                    else:
                        _x = _x.mean(0)
                if _x.dim() == 3 and _x.shape[0] <= 1024 and _x.shape[1] > 4 and _x.shape[2] > 4:
                    _chw = _x
                elif _x.dim() >= 2 and _x.shape[-1] <= 1024:
                    _tok = _x.reshape(-1, _x.shape[-1])
                    _n, _c = int(_tok.shape[0]), int(_tok.shape[1])
                    _side = int(_sb_math.sqrt(_n))
                    if _side * _side == _n:
                        _chw = _tok[:_side * _side].view(_side, _side, _c).permute(2, 0, 1)
                    else:
                        _seq = _tok.t().unsqueeze(0)
                        _pooled1 = _sb_F.adaptive_avg_pool1d(_seq, 64)[0].t()
                        _chw = _pooled1.view(8, 8, _c).permute(2, 0, 1)
                elif _x.dim() == 3 and _x.shape[-1] > 4:
                    _chw = _x.permute(2, 0, 1)
                else:
                    return {'bev_err': 'unsupported_bev_shape', 'bev_src_shape': _src_shape}
                if _chw.shape[0] > 512:
                    _chw = _chw[:512]
                _pooled = _sb_F.adaptive_avg_pool2d(_chw.unsqueeze(0), (8, 8))[0]
                _hwc = _pooled.permute(1, 2, 0).contiguous()
                _flat = [round(float(v), 5) for v in _hwc.reshape(-1).cpu().tolist()]
                return {
                    'bev_pool': _flat,
                    'bev_pool_shape': list(_hwc.shape),
                    'bev_src_shape': _src_shape,
                    'bev_summary': 'adaptive_avg_pool_8x8_scene_bev',
                }

            self.model.planning_head._sentinel_bev_stash = _sb_pool8(_bev)
        except Exception as _sb_e:
            self.model.planning_head._sentinel_bev_stash = {'bev_err': str(_sb_e)}
'''
src = src.replace(anchor, stash + "\n" + anchor, 1)
open(RUN, 'w').write(src)

# ---- server: dump per-frame BEV summary + executed trajectory when enabled -------------------
src = open(SRV).read()
HELPERS = '''
# ---- Sentinel iter21: BEV training-data extraction -----------------------------------------
import json as _bjson, os as _bos
_B_LOG = _bos.environ.get("SENTINEL_BEV_EXTRACT_LOG", "/model/sentinel_bev_extract.jsonl")
_b_on = _bos.environ.get("SENTINEL_BEV_EXTRACT", "0") == "1"


def _b_reset():
    if not _b_on:
        return
    try:
        with open(_B_LOG, "a") as f:
            f.write(_bjson.dumps({"reset": True}) + "\\n")
    except Exception:
        pass


def _b_dump(out, data):
    if not _b_on:
        return
    try:
        stash = getattr(uniad_runner.model.planning_head, "_sentinel_bev_stash", None) or {}
        rec = {
            "ts": int(data.timestamp),
            "command": int(data.command),
            "ego2world": [[float(v) for v in row] for row in data.ego2world],
            "traj": [[float(x), float(y)] for x, y in out.trajectory.tolist()],
        }
        rec.update(stash)
        with open(_B_LOG, "a") as f:
            f.write(_bjson.dumps(rec) + "\\n")
    except Exception as e:
        try:
            with open(_B_LOG, "a") as f:
                f.write(_bjson.dumps({"bev_extract_err": str(e)}) + "\\n")
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
                  "    _b_dump(uniad_output, data)\n"
                  "    return InferenceOutputs(\n", 1)
reset_old = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
assert reset_old in src
src = src.replace(reset_old,
                  "async def reset_runner() -> bool:\n    _b_reset()\n    uniad_runner.reset()", 1)
open(SRV, 'w').write(src)
print("BEV_EXTRACT_PATCHED")
