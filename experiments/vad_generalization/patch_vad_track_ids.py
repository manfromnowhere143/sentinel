#!/usr/bin/env python3
"""Give the VAD fork persistent object IDs (world-frame nearest-neighbor association).

The VAD fork exposes no `object_ids` at all — the field is absent from both the runner dataclass
and the server response model. Two consequences: the orchestrator's logger crashes indexing an
empty id tensor against N detections (the second episode-killer), and the union monitor's
multi-frame tracking silently degrades to per-frame index matching.

This patch adds a stateful, label-free ID layer in the runner: detections are transformed to the
world frame (lidar_pose) and greedily matched to the previous frame's detections within a 3.0 m
gate; unmatched detections get fresh ids. State clears on reset(). The ids flow through the
dataclass -> to_json -> server response model (field added there too).

This is an INPUT-layer adaptation (id association), not a change to the monitor's decision rule —
recorded as a pre-run amendment in HYPOTHESIS.md. Apply order: after server_patch_union_vad.py +
patch_vad_image_decode.py (server) and patch_vad_candidates.py + patch_vad_empty_fix.py (runner).
Idempotent.
"""
RUNNER = '/opt/sentinel-stack/VAD/inference/runner.py'
SERVER = '/opt/sentinel-stack/VAD/inference/server.py'

rsrc = open(RUNNER).read()
ssrc = open(SERVER).read()
if 'VAD_TRACK_IDS' in rsrc:
    print('already patched')
    raise SystemExit(0)

# 1. runner dataclass field
OLD = """    object_scores: Optional[List[float]] = None  # (N, )
    segmentation: Optional[List[List[float]]] = None"""
NEW = """    object_scores: Optional[List[float]] = None  # (N, )
    object_ids: Optional[List[int]] = None  # (N, ) — VAD_TRACK_IDS: NN-associated, world frame
    segmentation: Optional[List[List[float]]] = None"""
assert OLD in rsrc
rsrc = rsrc.replace(OLD, NEW, 1)

# 2. runner to_json
OLD = """            object_scores=self.object_scores,
            segmentation=self.segmentation,"""
NEW = """            object_scores=self.object_scores,
            object_ids=self.object_ids,
            segmentation=self.segmentation,"""
assert OLD in rsrc
rsrc = rsrc.replace(OLD, NEW, 1)

# 3. reset() clears the association state
OLD = """    def reset(self):
        # making a new scene token for each new scene. these are used in the model."""
NEW = """    def reset(self):
        self._sentinel_ids_state = None  # VAD_TRACK_IDS
        # making a new scene token for each new scene. these are used in the model."""
assert OLD in rsrc
rsrc = rsrc.replace(OLD, NEW, 1)

# 4. compute ids just before the output is assembled (anchor includes the empty-fix text)
OLD = """        return VADInferenceOutput(
            trajectory=trajectory,
            aux_outputs=VADAuxOutputs(
                objects_in_bev=objects_in_bev.tolist() if len(objects_in_bev) else None,
                object_scores=object_scores.tolist() if len(object_scores) else None,"""
NEW = """        # VAD_TRACK_IDS: stateful world-frame nearest-neighbor id association (3.0 m gate)
        try:
            _st = getattr(self, "_sentinel_ids_state", None) or {"pts": [], "ids": [], "next": 0}
            _R = np.array(input.lidar_pose)[:3, :3]
            _t = np.array(input.lidar_pose)[:3, 3]
            _cur = []
            for _row in objects_in_bev:
                _w = _R @ np.array([_row[0], _row[1], 0.0]) + _t
                _cur.append((float(_w[0]), float(_w[1])))
            _ids = [-1] * len(_cur)
            _used = set()
            for _i, (_cx, _cy) in enumerate(_cur):
                _best, _bd = -1, 3.0
                for _j, (_px, _py) in enumerate(_st["pts"]):
                    if _j not in _used:
                        _d = ((_cx - _px) ** 2 + (_cy - _py) ** 2) ** 0.5
                        if _d < _bd:
                            _best, _bd = _j, _d
                if _best >= 0:
                    _ids[_i] = _st["ids"][_best]
                    _used.add(_best)
                else:
                    _ids[_i] = _st["next"]
                    _st["next"] += 1
            self._sentinel_ids_state = {"pts": _cur, "ids": _ids, "next": _st["next"]}
        except Exception:
            _ids = list(range(len(objects_in_bev)))

        return VADInferenceOutput(
            trajectory=trajectory,
            aux_outputs=VADAuxOutputs(
                objects_in_bev=objects_in_bev.tolist() if len(objects_in_bev) else None,
                object_scores=object_scores.tolist() if len(object_scores) else None,
                object_ids=_ids if len(_ids) else None,"""
assert OLD in rsrc
rsrc = rsrc.replace(OLD, NEW, 1)

# 5. server response model carries the field
OLD = """    object_scores: Optional[List[float]] = None  # (N, )
    segmentation: Optional[List[List[float]]] = None"""
NEW = """    object_scores: Optional[List[float]] = None  # (N, )
    object_ids: Optional[List[int]] = None  # (N, ) — VAD_TRACK_IDS
    segmentation: Optional[List[List[float]]] = None"""
assert OLD in ssrc, 'server aux model anchor not found'
ssrc = ssrc.replace(OLD, NEW, 1)

open(RUNNER, 'w').write(rsrc)
open(SERVER, 'w').write(ssrc)
print('VAD_TRACK_IDS_PATCHED')
