#!/usr/bin/env python3
"""Fix the VAD fork's empty/cold-start aux-output handling (two episode-killing fork bugs).

Observed on the first 20-episode attempt (decode fix working, /infer serving):
1. The orchestrator's aux validator requires `objects_in_bev` shaped (N, 5); VAD's runner sends
   `np.empty((0, 5)).tolist() == []`, which loses the shape — `ValueError: Expected shape (0, 5),
   got torch.Size([0])`. The UniAD fork returns None for the empty case and the orchestrator
   accepts it; mirror that.
2. On cold-start frames VAD can emit detections without matching motion forecasts
   (`trajs_3d` empty while `boxes_3d` has N rows); the orchestrator's logger then indexes the
   empty forecast tensor with an N-long mask — `IndexError: shape of the mask [4] ... indexed
   tensor [0]`. Pad zero-displacement forecasts to match the detection count (behaviourally sane:
   no history yet means no forecast information).

Applies to /opt/sentinel-stack/VAD/inference/runner.py in place (no git checkout — composes after
patch_vad_candidates.py). Idempotent.
"""
RUNNER = '/opt/sentinel-stack/VAD/inference/runner.py'
src = open(RUNNER).read()

MARK = 'VAD_EMPTY_FIX'
if MARK in src:
    print('already patched')
    raise SystemExit(0)

# fix 2: pad missing forecasts to the detection count right after future_trajs is built
OLD_FUT = """        future_trajs = (
            bbox_results[0]["trajs_3d"].reshape(-1, 6, 6, 2).cumsum(dim=-2)
        )  # + bboxes.bev[:, :2].unsqueeze(1).unsqueeze(1)"""
NEW_FUT = """        future_trajs = (
            bbox_results[0]["trajs_3d"].reshape(-1, 6, 6, 2).cumsum(dim=-2)
        )  # + bboxes.bev[:, :2].unsqueeze(1).unsqueeze(1)
        # VAD_EMPTY_FIX (2): cold-start frames can carry detections without forecasts; pad
        # zero-displacement forecasts so every consumer sees consistent lengths.
        _n_boxes = len(bbox_results[0]["boxes_3d"].tensor)
        if future_trajs.shape[0] != _n_boxes:
            future_trajs = torch.zeros((_n_boxes, 6, 6, 2), dtype=future_trajs.dtype)"""
assert OLD_FUT in src, 'future_trajs anchor not found'
src = src.replace(OLD_FUT, NEW_FUT, 1)

# fix 1: empty aux fields -> None (the orchestrator's validator accepts None, not shape-less [])
OLD_RET = """            aux_outputs=VADAuxOutputs(
                objects_in_bev=objects_in_bev.tolist(),
                object_scores=object_scores.tolist(),
                object_classes=object_classes,"""
NEW_RET = """            aux_outputs=VADAuxOutputs(
                objects_in_bev=objects_in_bev.tolist() if len(objects_in_bev) else None,
                object_scores=object_scores.tolist() if len(object_scores) else None,
                object_classes=object_classes if len(object_classes) else None,"""
assert OLD_RET in src, 'return-aux anchor not found'
src = src.replace(OLD_RET, NEW_RET, 1)

OLD_FUT2 = """                future_trajs=future_trajs.tolist(),  # N x 6 modes x 6 future_timesteps x 2 (x, y)"""
NEW_FUT2 = """                future_trajs=future_trajs.tolist() if len(future_trajs) else None,  # N x 6 x 6 x 2"""
assert OLD_FUT2 in src, 'return-futs anchor not found'
src = src.replace(OLD_FUT2, NEW_FUT2, 1)

open(RUNNER, 'w').write(src)
print('VAD_EMPTY_FIX_PATCHED')
