# Launch packet — second closed-loop benchmark family: HUGSIM transfer of the released union

Status: launch packet only (same class as `CAUSAL_PLANNER_INTERPRETABILITY.md`). It is not a
pre-registration and authorizes no download, environment build, GPU run, or claim. Its job is to
record the reconnaissance and freeze the shape of the future pre-registration so the official
HYPOTHESIS.md can be written quickly and honestly. Recon date 2026-07-11; source list at bottom;
facts below should be re-verified against the repos at pre-registration time.

## Why this line (from `FRONTIER_POSITIONING_2026-07-11.md`)

The external survey's strongest reviewer-facing criticism of the campaign is single-benchmark
scope: NeuroNCAP is niche (~62 citations, 14 scenes, non-reactive adversaries). The two upgrades
that most change expert reception are a second planner and a second closed-loop benchmark
family. This packet is the second-family line.

## Recon verdict: HUGSIM primary, Bench2Drive subset as a labeled stretch

**HUGSIM (arXiv 2412.01718, TPAMI; github.com/hyzhou404/HUGSIM):**

- Ships UniAD as an integrated client (`--ad uniad`, fork `hyzhou404/UniAD_SIM`) running the
  SAME `uniad_base_e2e.pth` checkpoint we run under NeuroNCAP. VAD and Latent-TransFuser
  clients also ship.
- Interface is functionally our `/infer` pattern with named pipes instead of HTTP: simulator
  writes `(obs, info)` per step; client returns `sdc_traj`. Interception point for the monitor
  is client-side in `UniAD_SIM/tools/closeloop/e2e.py` after model forward and before the
  `plan_pipe` write — same signal set we consume today (plan + tracked boxes/scores + ego pose;
  if motion-forecast keys differ, our tracker derives velocities from per-frame positions).
  Override = write the latched committed-stop trajectory into the pipe; `traj2control` brakes.
- Benchmark: 70+ splat-reconstructed scenes (KITTI-360, Waymo, nuScenes, PandaSet), 400+
  scenarios in four tiers (Easy/Medium/Hard/Extreme, the last with actors actively targeting
  ego). Metric HD-Score = (NC x DAC x weighted(TTC, COM)) per step, x route completion — it has
  a PROGRESS TERM BUILT IN, so the deployment question NeuroNCAP cannot ask natively (our
  safe-progress metric had to be constructed) is native here. Pre-built scenes downloadable
  (~61 GB HuggingFace `XDimLab/HUGSIM`; no per-scene splat training; older scenes need
  `--ver0` conversion).
- Fits our budget: renderer ~89 FPS on a 3090, UniAD inference dominates; one L4 24GB + <100GB
  disk suffices; a full sweep is order 10-20 GPU-hours, so OFF/ON arms with seed-pairing and
  CIs are affordable.
- No published monitor/shield work on HUGSIM found — first-mover slot, at the cost of no
  monitor baseline to compare against (published RealADSim closed-loop anchors: HD-Score
  ~0.30-0.42; ICCV 2025 challenge is closed).

**Bench2Drive (NeurIPS 2024 D&B):** CARLA-trained UniAD/VAD checkpoints exist
(Bench2DriveZoo, `uniad/vad` branch; interception in `team_code/uniad_b2d_agent.py` between
`sdc_traj` extraction and the PID). But (a) the authors' own cost table implies a full 220-route
UniAD-Base pass is ~8xH800x2 days — weeks per arm on one L4, operationally fragile (CARLA VRAM
leaks on a shared 24GB card); (b) Argus (ASE 2025) already occupies the monitor-on-Bench2Drive
slot with reroute/IDM mitigation on the same zoo checkpoints. If touched at all: a documented
subset (e.g., the Emergency-Brake ability routes, ~30-50 routes), labeled as a subset, framed
against Argus as the differing-design baseline (planner's-own-outputs geometry + committed stop
vs their privileged/perception monitor + invented takeover trajectory). Not the primary line.

## Frozen shape of the future pre-registration (bars to be numerically frozen then)

1. **Stage 0 — infra gate (the iter-1 pattern):** environments up, one scene renders, UniAD
   client drives it, monitor-OFF smoke completes, per-step logs captured. No bars beyond
   completion; publishes an infrastructure null if blocked (the iter22-28 lesson: artifact
   validity is the first research object).
2. **Stage 1 — monitor-OFF reproduction:** unmonitored UniAD on a frozen scenario subset;
   sanity-anchor against published closed-loop anchors; freeze the scenario list and seeds.
3. **Stage 2 — OFF vs released union, seed-paired:** primary = HD-Score delta with
   scene-clustered bootstrap CI; secondary = NC/DAC collision terms and route completion
   separately (RC isolates over-braking). Falsifiers stated up front, at minimum: (a)
   over-braking (RC collapse a la iter3/iter13 — the RSS lesson), (b) trigger mistuned for
   splat-rendered tracking noise (fires constantly or never; report as transfer-boundary null,
   do not retune on eval scenes), (c) renderer-specific artifact sensitivity. Any threshold
   retuning happens on a disjoint fit subset, pre-registered.
4. **Scope limits, binding:** UniAD-class planners only; no real-world safety claim; no
   deployment claim; the campaign's wording rules from iteration 39 apply. A null publishes at
   full weight — "the union does not transfer off NeuroNCAP" is itself the external-validity
   answer this line exists to obtain.
5. **Sequencing:** launches only when the GPU box is free (iter42 first), only after its own
   HYPOTHESIS.md is committed, and does not preempt the iter42-gated perturbation successor.
   Disk note: box root is at 94%; HUGSIM assets (~61 GB) likely belong on the 1TB
   `/datasets/nuscenes-full` disk (verify free space at pre-reg time).

## Sources (recon 2026-07-11)

HUGSIM repo github.com/hyzhou404/HUGSIM; paper arXiv 2412.01718; assets
huggingface.co/datasets/XDimLab/HUGSIM; UniAD client github.com/hyzhou404/UniAD_SIM; RealADSim
realadsim.github.io/2025; Bench2Drive github.com/Thinklab-SJTU/Bench2Drive (paper arXiv
2406.03877); zoo github.com/Thinklab-SJTU/Bench2DriveZoo (branch uniad/vad); Argus arXiv
2511.09032, github.com/Argus4ADS/Argus.
