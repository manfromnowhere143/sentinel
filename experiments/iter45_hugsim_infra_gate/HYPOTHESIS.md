# Iteration 45 - HUGSIM second-benchmark infrastructure gate pre-registration

Frozen before any HUGSIM asset download, repository clone on the box, environment build, GPU
run, renderer launch, UniAD_SIM client run, monitor patch, or claim. Committed alone, before
any iteration-45 setup command executes. The frozen shape follows the committed launch packet
`docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md` (recon 2026-07-11); this file freezes only
its Stage 0.

## Why this line

The campaign's strongest reviewer-facing criticism is single-benchmark scope: every closed-loop
number so far is NeuroNCAP (14 scenes, non-reactive adversaries). HUGSIM (arXiv 2412.01718,
TPAMI; `github.com/hyzhou404/HUGSIM`) is the selected second closed-loop benchmark family: it
ships UniAD as an integrated client (`hyzhou404/UniAD_SIM`) running the SAME
`uniad_base_e2e.pth` checkpoint we run under NeuroNCAP, its HD-Score metric has a native
progress term, and a full sweep is affordable on the L4. This iteration is the iter-1 pattern
applied to that lane: prove the infrastructure exists before any research claim is possible.
The iter22-28 lesson is binding — artifact validity is the first research object.

## Research question

Can the HUGSIM benchmark stack be stood up on `sentinel-gpu` such that one benchmark scenario
renders and the unmodified UniAD_SIM client drives it closed-loop end-to-end, producing an
HD-Score output and per-step logs, with auditable asset provenance?

## Stage-0-only scope (binding)

This gate is infrastructure-only, monitor-OFF only. It contains:

- NO monitor patch, NO sentinel code on the HUGSIM/UniAD_SIM side, NO interception;
- NO OFF-vs-ON comparison, NO seed-paired arms, NO scenario sweep;
- NO transfer claim, NO benchmark claim, NO HD-Score interpretation beyond "a finite HD-Score
  was produced";
- NO tuning of any monitor threshold, and no reading of monitor-relevant signals beyond what
  the unmodified pipeline logs by itself.

A pass authorizes ONLY the writing of the Stage-1/2 pre-registration (monitor-OFF
reproduction subset, then OFF vs released union, per the launch packet). It does not authorize
those runs themselves. A blocked gate publishes `HUGSIM_INFRA_NULL` at full weight.

## Frozen destinations and inputs

- Box: `sentinel-gpu` (us-west1-a), single-tenant; never two GPU jobs.
- Benchmark assets: `huggingface.co/datasets/XDimLab/HUGSIM` (the released pre-built scenes,
  reference size ~61 GB) staged under `/datasets/nuscenes-full/hugsim/` on the 1 TB data disk
  (266 GiB free at pre-registration; root disk holds no heavy assets — the 2026-07-12 cleanup
  record froze that rule). Every staged file gets a recorded size and SHA256 in a committed
  manifest (`proof-infra/hugsim_asset_manifest.txt`). If the full release exceeds free space,
  the nuScenes-sourced scene subset is staged first and the manifest records the subset
  honestly; Stage 0 needs one scenario, not the full library.
- Code: `github.com/hyzhou404/HUGSIM` and `github.com/hyzhou404/UniAD_SIM`, cloned on the box
  under `/opt/sentinel-stack/`; cloned commit SHAs recorded in the setup log. No sentinel
  modification to either repository in this iteration; only configuration/path/dependency-pin
  edits required to build and run, each one recorded in `SETUP_LOG.md`.
- Planner checkpoint: the box's existing `uniad_base_e2e.pth` (the NeuroNCAP checkpoint);
  its SHA256 is recorded in the setup log and must match whatever checkpoint the UniAD_SIM
  client is pointed at. If UniAD_SIM requires additional auxiliary weights (e.g. motion anchor
  files) they are downloaded per its README and recorded with SHA256s.
- Environments: separate Python environments are explicitly allowed (HUGSIM's renderer stack
  and UniAD_SIM's mmcv-era stack have incompatible dependency sets); the UniAD_SIM client may
  alternatively run inside the existing sentinel UniAD Docker image. Environment locations,
  Python/CUDA/torch versions, and the chosen isolation mechanism are recorded in
  `SETUP_LOG.md`. Heavy environments (>5 GiB) live on the data disk.

## Frozen smoke-scenario selection rule (no cherry-picking)

The single Stage-0 scenario is chosen by rule, before any closed-loop attempt, and recorded in
`SETUP_LOG.md`: the lexicographically first nuScenes-sourced scenario directory that the
staged assets and the shipped HUGSIM configs both support, at the easiest available difficulty
tier. If that scenario fails for a scenario-specific asset reason (not an environment reason),
the next scenario in lexicographic order may be tried, and every attempt is logged. Older
scenes requiring the repository's `--ver0` conversion are converted with the shipped tool and
the conversion command is logged.

## Gates (completion bars, per the launch packet: no numeric bars beyond completion)

- **G1 — assets staged with provenance.** The staged files exist under
  `/datasets/nuscenes-full/hugsim/`, and the committed manifest lists every staged file with
  byte size and SHA256, plus the total byte count and the free-space receipt after staging.
- **G2 — environments installed.** The HUGSIM environment imports and launches its
  renderer/simulator entry point, and the UniAD_SIM client environment loads the UniAD model
  with the recorded checkpoint, each demonstrated by a logged command.
- **G3 — one scenario renders.** The HUGSIM simulator starts the selected scenario and
  produces rendered observations (logged startup plus a saved sample observation or its
  logged shape/checksum).
- **G4 — closed-loop smoke completes, monitor-OFF.** The unmodified UniAD_SIM client drives
  the selected scenario end-to-end through the pipe interface: the run terminates by the
  benchmark's own termination rule (route end, collision, or its timeout), produces an
  HD-Score output for the scenario, and per-step logs (at minimum: step index, ego state or
  plan, and the pipe round-trip completing every step) are captured and committed under
  `proof-infra/`. Wall-clock bound: the single smoke run gets at most 120 minutes before it is
  declared hung (pipe-client deadlock falsifier) — long GPU evaluation is out of scope.

Verdict:

- all of G1-G4 -> `HUGSIM_INFRA_GATE_PASS` (authorizes only the Stage-1/2 pre-registration);
- any gate blocked after honest attempts -> `HUGSIM_INFRA_NULL`, published at full weight
  with the blocking evidence (the iter41 pattern), naming the failed gate and falsifier.

## Named falsifiers

- **Environment/CUDA incompatibility with the L4 stack.** HUGSIM's renderer (gsplat-era
  CUDA) or UniAD_SIM's mmcv-era stack fails to build or run on the box's driver/CUDA
  combination after honest pinning attempts.
- **Asset-format mismatch.** The released scenes do not load in the cloned code (including
  `--ver0` conversion failures) — staged bytes are not usable scenes.
- **Pipe-client deadlock.** Simulator and client each wait on the other's named pipe; the
  smoke run makes no step progress within the wall-clock bound.
- **VRAM overflow.** Renderer plus UniAD inference exceed the L4's 24 GB and the run cannot
  complete a scenario even at the benchmark's own minimal settings.
- **Checkpoint mismatch.** The UniAD_SIM client cannot run the NeuroNCAP
  `uniad_base_e2e.pth` weights (incompatible state dict) — this would undercut the
  same-checkpoint premise of the whole transfer line and must be reported as such.

Any of these, if terminal after honest attempts, produces `HUGSIM_INFRA_NULL` at full weight.
Partial progress (e.g. assets staged, environments half-built) is committed as `SETUP_LOG.md`
progress notes with exact resume points; an interrupted setup is NOT a null — only a
falsifier-grade blocker is.

## Honest boundary

A pass means the pipeline runs; it says nothing about whether the released union transfers,
what UniAD's HD-Score level is, or how splat-rendered tracking noise interacts with the
monitor. Published RealADSim closed-loop anchors (~0.30-0.42 HD-Score) are context for the
FUTURE Stage-1 sanity check, not a bar here. No safety, deployment, robustness, or benchmark
claim of any kind follows from this gate. The campaign's iteration-39 wording rules apply to
every doc this iteration touches.

## Required proof artifacts

- `SETUP_LOG.md` in this directory: every setup step, command, pin, deviation, and the exact
  resume point if interrupted (committed at every state change);
- `proof-infra/hugsim_asset_manifest.txt`: per-file size + SHA256 of staged assets, totals,
  free-space receipts;
- `proof-infra/` smoke-run evidence: launch command records, per-step log, HD-Score output,
  environment freeze records (`pip freeze`/`conda list` captures), checkpoint SHA256 receipt;
- box-side detached-run logs under `/var/log/sentinel-hugsim-*.log` with `set -x` and
  start/done markers (the box playbook), copied into `proof-infra/` when the gate concludes.

## Protocol

1. Commit this `HYPOTHESIS.md` alone, CI green, before any setup command runs on the box.
2. Stage assets (detached, logged), then commit the manifest.
3. Build environments (detached, logged); commit `SETUP_LOG.md` progress at every state
   change; never leave the box in an unrecorded state.
4. Run the single monitor-OFF smoke scenario once per the frozen selection rule.
5. Publish `RESULT.md` at full weight — pass or infrastructure null — and update README,
   CONTINUITY, and HANDOFF. No Stage-1/2 run happens under this pre-registration.
