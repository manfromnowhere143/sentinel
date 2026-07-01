# VAD generalization — staged (the union on a second frozen planner)

The strongest open question after the validated union is **generalization**: does the same monitor work
on a *different* frozen end-to-end planner, or is it UniAD-specific? The natural test is **VAD**
(hustvl/VAD; NeuroNCAP adapter fork at `wljungbergh/VAD`). This is that build, staged to a clean
continuation point.

## Why it should work by construction

VAD's inference server returns the **same `InferenceAuxOutputs` schema** as UniAD — `objects_in_bev`,
`object_scores`, `future_trajs`, `object_ids` — so the union monitor's logic is **unchanged**; only the
code anchors differ (`vad_*` vs `uniad_*`). The NeuRAD renderer is planner-agnostic (reused as-is), and
the public-mini scenes (0103, 0796) are already staged. A positive result would show the union is a
**general method on any frozen planner exposing plan + detections + forecasts**, not a UniAD trick.

## Done (this session)

- **VAD adapter fork cloned** — `wljungbergh/VAD@main` at `/opt/sentinel-stack/VAD` (has
  `inference/server.py` + `runner.py`, the NeuroNCAP model node).
- **VAD-Base checkpoint downloaded** — `VAD_base.pth` (707 MB, public Google Drive) → `VAD/ckpts/`.
- **Generic val data-infos downloaded** — `vad_nuscenes_infos_temporal_val.pkl` (145 MB).
- **VAD Docker image build** — from `VAD/docker/Dockerfile` (CUDA 11.1, torch 1.9.1+cu111, mmdet 2.14,
  mmdet3d 0.17.1, casadi; near-identical to the UniAD stack, uvicorn/fastapi already included).
- **Union monitor patched onto VAD** — `server_patch_union_vad.py` applied to `VAD/inference/server.py`
  (`VAD_UNION_PATCHED`): the identical CPA-OR-closing-TTC intervention, anchored on `vad_output` /
  `vad_runner`. Reads the shared aux schema, so no logic change.

## The remaining blocker (the honest one)

VAD's NeuroNCAP config (`projects/configs/VAD/VAD_base_e2e.py`) points at a **NeuroNCAP-specific**
data-infos file, `vad_nuscenes_infos_temporal_our_ncap_val.pkl`, plus `nuscenes_map_anns_val.json` — and
these are **not published** in the VAD fork or NeuroNCAP repo (the VAD docs say "generate by yourself").
They must be produced by VAD's own data-prep (`tools/create_data.py`-style) restricted to the NCAP
scenes, run inside the VAD environment. That is a non-trivial data-generation step, and starting it at
the tail of a long session risks an open-ended grind — so it is staged rather than forced.

## To finish (clean continuation)

1. Finish/confirm the `vad:latest` image (it was finalizing its export).
2. Generate `vad_nuscenes_infos_temporal_our_ncap_val.pkl` (+ `nuscenes_map_anns_val.json`) for the mini
   scenes via VAD's data-prep inside the container, or obtain them from the fork author.
3. Run OFF (VAD, unmonitored) vs union (VAD, monitored) on 0103/0796 via the NeuroNCAP eval with
   `MODEL_NAME=VAD`, `MODEL_IMAGE=vad:latest`, `MODEL_CHECKPOINT_PATH=ckpts/VAD_base.pth`,
   `MODEL_CFG_PATH=projects/configs/VAD/VAD_inference.py`.
4. Report whether the union's properties (selective, side-solved, net-positive) transfer to VAD.

The union stands as the campaign's statistically-validated result on UniAD; VAD generalization is the
next milestone, staged here to a precise restart point.
