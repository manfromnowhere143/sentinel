# Iteration 1 — infrastructure gate CLEARED (closed-loop smoke, scene 0103)

The pre-registration named the binding constraint plainly: *"standing up NeuroNCAP (NeuRAD
neural rendering) + a frozen UniAD/VAD planner on single-digit GPUs is the real gate."* That gate
is now cleared. The full NeuroNCAP closed loop runs end-to-end on one GPU and emits the genuine
benchmark metric.

## What ran

- **Hardware:** one NVIDIA **L4** (24 GB), `sentinel-gpu`.
- **Stack:** the three-container public release — `neurad:latest` (NeuRAD neural renderer),
  `uniad:latest` (**frozen** UniAD planner, served over HTTP), `ncap:latest` (closed-loop
  orchestrator + scorer).
- **Scenario:** `stationary` on **scene-0103**, `RUNS=2`. Each run is a full closed-loop episode:
  NeuroNCAP resets the scene, then for each step it asks NeuRAD to **render** the six camera images
  from the current ego pose, posts them to the frozen UniAD server for an **`/infer`** (plan), and
  steps the simulation — 15 steps per run, both runs completed, clean shutdown.

This is the exact loop the method depends on: `render_image → infer → update_actors → score`.

## The number it produced

```
run_0:  ncap_score 5.0   any_collide@0.0s=false   recall@5-35m=1.0   impact_speed 0.0
run_1:  ncap_score 5.0   any_collide@0.0s=false   recall@5-35m=1.0   impact_speed 0.0
```

The frozen UniAD planner **detected the target actor** (recall 1.0 across range bands) and **avoided
collision** on both runs of this stationary scene, so NeuroNCAP scored it 5.0/5.0. Per-run
`metrics.json`, `trajectories.json`, `ego_poses.json`, and `reference_trajectory.json` were written
for both runs. Scalar-field dump and the closed-loop log excerpt: [`proof/smoke_0103_raw.txt`](proof/smoke_0103_raw.txt).

## Honest scope — what this is, and what it is not

- **It is:** proof the entire closed-loop apparatus works on a single GPU and produces the real
  NeuroNCAP metric schema with a *frozen* planner in the loop. The engineering risk the pre-reg
  flagged is retired.
- **It is not yet** the published baseline number. The headline UniAD figures (stationary 3.50,
  overall 1.84) are an **average over 10/5/5 scenes × 100 runs**. Here we ran **one scene × 2 runs**
  of one scenario type and got 5.0 — a single low-variance smoke point, not the averaged baseline,
  and scene-0103-stationary is a comparatively easy case (a stationary target). No baseline claim is
  made from it.
- **To reach the full averaged baseline** we need (a) the gated full nuScenes **trainval sensor
  blobs** for all 14 scenes (the public `v1.0-mini` used here only carries scenes 0103 + 0796), and
  (b) the 100-run scale. Both are now *compute + download*, not engineering unknowns.

## The eight blockers cleared (durable insights for the engine)

Every one of these is the kind of integration friction that silently sinks a reproduction; each is
logged so the engine never re-pays it.

1. **ncap image — numpy 2.0 ABI break.** C-extensions compiled against numpy 1.x fail to import
   under numpy 2.x (`numpy.core.multiarray failed to import`). Fix: pin `numpy<2` in the ncap image.
2. **Wrong UniAD.** Vanilla `OpenDriveLab/UniAD` has no `inference/server.py`; NeuroNCAP's reference
   adapter lives in the **`wljungbergh/UniAD`** fork (NeuroNCAP's first author). The model repo is
   *mounted*, so swapping it needs no image rebuild.
3. **uniad image missing the server deps.** The fork's `server.py` runs FastAPI/uvicorn and uses
   `pydantic.Base64Bytes` (**pydantic v2**). The vanilla-built image lacked them; a one-layer derived
   rebuild (`pip install uvicorn fastapi`) fixes it — all model deps were already present.
4. **`find_free_port` used `python`.** The DLVM root shell has `python3` but no bare `python`, so the
   renderer port came back empty (`--engine.renderer.port: expected 1 argument`). Patched to `python3`.
5. **NeuRAD needs raw sensor data, not just metadata.** The dataparser reads the actual LIDAR +
   camera files to build scene geometry even when rendering from a pretrained checkpoint. The public
   **`v1.0-mini`** (4.2 GB, no login) carries full sensor data for scenes **0103 + 0796** — both in
   NeuroNCAP's set — enough to run the loop without the 290 GB trainval blobs.
6. **UniAD `motion_anchor_infos_mode6.pkl` missing.** MotionHead needs it at *build* time; it is a
   public OpenDriveLab v1.0 release asset.
7. **`checkpoints/` vs `ckpts/` mismatch.** The config hardcodes `checkpoints/...` while the weights
   live in `ckpts/`. Symlink `checkpoints → ckpts` so both the `.pth` and the anchor pkl resolve.
8. **L4 (sm_89) × torch cu111 cuSOLVER incompatibility.** UniAD's pinned `torch 1.9.1+cu111`
   predates Ada; cuBLAS/cuDNN work via PTX JIT (rendering + inference run) but **cuSOLVER cannot
   create a handle on sm_89**, so `torch.linalg.inv` throws `CUSOLVER_STATUS_INTERNAL_ERROR`. There
   is exactly one such GPU call in the inference path (`uniad_track.py:270`, a tiny transform
   matrix); routing it through CPU costs nothing and clears the loop. *Lesson: the newest GPU is not
   the most compatible one for a four-year-old pinned CUDA stack.*

## Reproduce

On the GPU box (`/opt/sentinel-stack`, the three images built), with `v1.0-mini` sensor data merged
into the nuScenes tree and the fork + fixes above in place:

```bash
cd /opt/sentinel-stack/neuro-ncap && bash sentinel_smoke.sh   # scene 0103, 2 runs
```

Outputs land under `NeuroNCAP/outoutput/<ts>/stationary-0103/run_{0,1}/metrics.json`.
