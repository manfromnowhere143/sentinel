# Iteration 48 - HUGSIM Stage-2 transfer gate: monitor-OFF vs released union, seed-paired

Frozen before any iteration-48 tooling, monitor patch, byte movement, GPU command, simulator
launch, or claim. Committed alone. This is the ONE pre-registration authorized by the
iteration-47 completion pass
(`experiments/iter47_map_staging_and_off_completion/RESULT.md`), and it follows the frozen
shape recorded in the launch packet
[`docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md`](../../docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md).
It authorizes the Stage-2 runs it describes and nothing else. This iteration is **THE transfer
verdict** of the second-benchmark line: a pass OR a null publishes at full weight — "the
released union does not transfer off NeuroNCAP" is exactly the external-validity answer this
line exists to obtain.

## Research question

Does the campaign's released union — the iteration-15 configuration, with its
NeuroNCAP-frozen parameters, unmodified — change closed-loop HUGSIM driving outcomes on the
frozen 26-scenario easy+medium subset, measured seed-paired against the unmonitored planner
(HD-Score delta with a scenario-clustered bootstrap CI), on the same frozen UniAD checkpoint?

## Frozen monitored arm (binding; any deviation = VOID, see falsifier F1)

**Rule.** The iteration-15 released union exactly as committed and replay-verified in
iteration 42 (`experiments/iter42_exact_trace_replay_support/server_patch_union_trace.py`):
two label-free geometric detectors (CPA over the planner's own plan against tracked-object
constant-velocity extrapolation; closing-speed TTC) in union, with the threat-cleared latch
release. Brake = the committed-stop override (latched stop trajectory), release after K
consecutive clear frames.

**Parameters — EXACTLY the NeuroNCAP-frozen values.** `cpa_margin = 1.5` m, `ttc_thresh =
2.5` s, `min_closing = 3.0` m/s, `max_gap = 30.0` m, `min_score = 0.3`, `release_k = 4`,
plan-step `dt = 0.5` s. **Any retuning, rescaling, or "adaptation" of any of these values for
HUGSIM — before, during, or after the run — voids the iteration (F1).** Transfer means the
frozen rule as released; a mistuned trigger publishes as a transfer-boundary null, not as an
invitation to fit the eval scenes.

**Interception point.** Client-side in UniAD_SIM's closed-loop e2e loop
(`/opt/sentinel-stack/UniAD_SIM`, frozen SHA below): after the model forward and before the
plan is written to the plan pipe. Inputs are the planner's own outputs from the SAME forward
pass — the ego-frame plan plus tracked object boxes/scores (and ids where exposed) — plus the
ego pose; object velocities are derived by cross-frame world-position differencing keyed on
track id, exactly the NeuroNCAP mechanism (no privileged simulator state, no ground-truth
actors, no map queries). On brake, the override trajectory is written into the pipe so
`traj2control` executes the stop. The patch prints a load marker to the episode log
(iteration-42 discipline) so every launched episode proves which code ran; the patch byte-copy
is committed BEFORE launch.

## Frozen schedule and pairing (binding)

- **Scenarios:** the same frozen 26-scenario easy+medium subset as iterations 46/47 (the
  lexicographically first 26 of the 52-yaml release manifest), same released yaml files; the
  launcher re-verifies all 52 per-file SHA256 receipts from the iteration-46 manifest as a
  hard provenance gate.
- **Arms and N:** N=2 per scenario per arm → `26 x 2 x 2 = 104` episodes.
- **Pairing (per the carried stochastic D0 verdict — no re-probe):** the loop is stochastic
  (iteration 46's D0, carried through iteration 47), so pairing is WITHIN-LAUNCH,
  BACK-TO-BACK. Per scenario, in lexicographic order, the frozen episode order is:
  `OFF r1 -> ON r1 -> OFF r2 -> ON r2`, all inside a single launch. The paired unit is
  (ON rN − OFF rN) per scenario per N → `52` paired HD deltas in `26` scenario clusters.
- **Noise floor (measured, carried):** the iteration-46/47 within-scenario OFF-OFF spread
  over all 26 pairs — median |dHD| `0.0251`, 22/26 pairs <= `0.09`, max `0.7419`
  (`scene-0138-medium-01`) — is the stochastic noise floor. A single pair can swing by most
  of the score range; no per-pair delta is interpretable alone.

## Frozen paired-analysis design (binding)

ONE run of a committed analyzer over committed artifacts:

- **Primary bar (the transfer verdict):** the 95% scenario-clustered bootstrap CI (resample
  the 26 scenario clusters with replacement, `10,000` draws, seed `48`) on the MEAN paired
  HD-Score delta (ON − OFF) over the 52 pairs.
  - `PASS_TRANSFER_POSITIVE` if the CI excludes zero from below (monitored arm higher).
  - `TRANSFER_NEGATIVE` if the CI excludes zero from above (monitored arm lower) — published
    at full weight as the transfer answer.
  - `TRANSFER_NULL` if the CI includes zero — published at full weight as the transfer
    answer, with the noise floor stated.
- **Heavy-tail treatment (stated up front):** alongside the primary mean-delta CI, the
  analyzer reports the MEDIAN paired delta with the same scenario-clustered bootstrap CI and
  the full 52-delta distribution (per-pair table). If the mean and median CIs disagree in
  sign, the verdict follows the pre-registered primary (mean) and the disagreement is
  reported on the record as a heavy-tail caveat — bars never move after data.
- **Secondary (descriptive, over-braking visibility; NOT bars):** paired deltas of the
  HD-Score component terms — NC, DAC, the weighted TTC/COM term — and route completion (RC)
  separately. RC isolates over-braking (the iteration-3/13 RSS lesson): a monitor can "win"
  NC while destroying progress, and HD-Score's built-in progress term makes that visible
  natively. ON-arm firing statistics (fired frames, brake frames, releases, intervention
  episodes) are reported from the monitor's per-episode log lines.

## Frozen environment and provenance (hard gate at launch, `I48_STAGE2_PROVENANCE_FAIL` on any mismatch)

All values identical to iterations 46/47:

- HUGSIM `/opt/sentinel-stack/HUGSIM` @ `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
  UniAD_SIM `/opt/sentinel-stack/UniAD_SIM` @ `5fb279e39912a5ac7f58e00d56b065cadcd0a749`
  (plus the committed, byte-hashed iteration-48 monitor patch applied at launch — the ONLY
  permitted delta, its SHA256 recorded in the receipts).
- Docker image `uniad:latest` id `f73ef3884063`; checkpoint `uniad_base_e2e.pth` SHA256
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`.
- The iteration-45 CPU-fallback shim carried unchanged:
  `/opt/sentinel-stack/hugsim-shim/sitecustomize.py` SHA256
  `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c`.
- All 52 scenario-yaml SHA256s from the iteration-46 manifest verify; the four
  `maps/expansion/*.json` vector maps present (iteration-47 Stage A).
- Carried D0 verdict file reads `stochastic` (decided once in iteration 46; no re-probe).
- Single-tenant rule: refuse to start if any Docker container is up; never alongside another
  GPU job.
- Launcher discipline carried from iterations 46/47: per-episode retry-once, the
  3-consecutive-dual-failure abort, the 20 GiB disk guard before every episode, per-episode
  markers (`I48_EP_START`/`I48_EP_RC`/`I48_EP_DONE` with arm labels), fresh collection root
  `/datasets/nuscenes-full/hugsim/iter48_runs/`, log `/var/log/sentinel-iter48-stage2.log`,
  done marker **`I48_STAGE2_DONE`**.

## Completion bars (all required before the transfer verdict is read)

- **K1 — all 104 episodes complete:** every scheduled episode terminates by the benchmark's
  own rule within the 1200 s per-episode bound with an `eval.json` carrying a finite
  `hdscore`, after at most ONE scripted retry. Any episode failing both attempts fails K1 and
  the iteration publishes as a completion null — NOT a transfer verdict.
- **K2 — per-step logs for all 104:** `output.txt` round-trip lines and a positive step count
  per episode; ON-arm episodes additionally carry the monitor's per-frame decision lines
  (fired/brake/release) and the patch load marker; heavy artifacts stay on the box behind a
  committed SHA manifest.
- **K3 — evidence committed:** launch receipts (including the monitor-patch SHA256), the run
  log, all 104 episodes' `eval.json`/`output.txt`/`episode_meta.json`, the heavy manifest,
  and the single analyzer report committed under this experiment (files >90 MB split into
  `.part-*`).

## Budget (frozen, with the arithmetic)

- `104` episodes. Absolute single-attempt ceiling: `104 x 1200 s = 34.7` GPU-hours; the
  retry-once clause can only add attempts the consecutive-failure guard has not already
  aborted (3 consecutive dual failures abort the run), so the practical state ceiling is
  ~`35` GPU-hours and an early-abort run costs far less.
- Expected from the measured iteration-46/47 OFF walls (102-509 s, median ~250 s) plus ON-arm
  monitor overhead (negligible compute; possible longer episodes under braking):
  **~8-16 GPU-hours**, one detached run, box otherwise idle.

## Named falsifiers

- **F1 — retuning void.** Any launched monitor parameter differing from the seven frozen
  values above, or any parameter change between launch and analysis → the iteration is VOID
  (published as `VOID_RETUNED`, no transfer verdict, no partial claim). Verification is
  mechanical: the receipts record the patch SHA256 and the env/param block echoed at load.
- **F2 — trigger mistuned for splat tracking noise (the iteration-43 connection).** Iteration
  43 measured that position jitter at 5 cm already makes the frozen rule over-fire in replay;
  splat-reconstructed rendering may put HUGSIM's tracked boxes in that noise regime. Frozen
  detection, either direction: pooled over all 52 ON episodes, brake frames > `80%` of all
  frames (fires constantly) OR `0` fired frames across all 52 ON episodes (fires never) →
  publish as a transfer-boundary null naming the mechanism, with the firing statistics; NO
  retuning on these scenes.
- **F3 — over-braking (RC collapse).** Mean paired RC delta (ON − OFF) < `-0.30` → the
  over-braking finding is named in the published verdict regardless of the primary HD
  outcome (an HD "pass" bought by luck while RC collapses is reported as such).
- **F4 — crash/deadlock loop.** Any episode failing both attempts fails K1; three consecutive
  dual-failure episodes abort early (`I48_ABORT_CONSECUTIVE_FAILURES`) — publish the
  completion null rather than burning the budget.
- **F5 — pairing infeasibility re-check.** Median |dHD| over this run's 26 fresh OFF-OFF
  within-scenario pairs > `0.15` → the OFF arm's own noise invalidates the pairing design;
  publish as a pairing finding; the transfer CI is still reported but flagged as
  noise-dominated.
- **F6 — VRAM overflow / disk exhaustion.** As in iterations 46/47: systematic OOM via the
  consecutive guard is the falsifier form of the null; disk aborts (`I48_ABORT_DISK`) are
  interrupted runs with a resume point, not nulls.

## Forbidden claims (binding)

No NeuroNCAP-equivalence claim (HD-Score and NeuroNCAP score are different metrics on
different scenes; nothing here ranks one against the other). No deployment, real-world,
production, or safety claim. No benchmark-ranking or UniAD-performance claim. No
generalization claim beyond UniAD-class planners on these 26 scenarios. No monitor-robustness
claim (iteration 43's mild-fragile finding stands). The iteration-39 wording rules apply to
every doc this iteration touches. A pass authorizes successor pre-registrations on this line
(scenario-tier extension, second-planner transfer); it does not itself authorize any run
beyond the single registered launch here.

## Required proof artifacts

- `proof-stage2/receipts.json`: launch provenance-gate output (all frozen values re-verified,
  monitor-patch SHA256, echoed parameter block, carried D0 verdict).
- `proof-stage2/episodes/<scenario>__<arm>_r<n>/`: all 104 episodes' `eval.json`,
  `output.txt`, `episode_meta.json` (any `__failed` dirs included).
- `proof-stage2/i48-stage2-run.log`: the full box-side run log with per-episode arm-labelled
  markers and the final `I48_STAGE2_DONE`.
- `proof-stage2/heavy_manifest_iter48.txt`: SHA256 manifest of heavy on-box artifacts.
- `proof-stage2/transfer_report.json` (+ per-pair markdown table): the single analyzer run —
  primary mean-delta CI, median-delta CI, per-term secondary deltas, firing statistics,
  falsifier evaluations.

## Protocol

1. Commit this `HYPOTHESIS.md` alone, CI green, before any tooling or patch exists.
2. Commit tooling: the monitor patch (interception + frozen parameters + load marker + trace
   lines), the Stage-2 launcher (iteration-46/47 launcher pattern with the OFF/ON
   interleaved schedule and iteration-48 gates), the analyzer, and unit tests; ruff + pytest
   + validate_docs green.
3. Launch the single registered detached run per the box playbook; verify the patch load
   marker and the first OFF/ON pair before leaving; record IN FLIGHT state in
   CONTINUITY/HANDOFF. Never alongside another GPU job.
4. On `I48_STAGE2_DONE`: collect and commit proof FIRST, run the committed analyzer ONCE,
   publish `RESULT.md` at full weight (pass, transfer-negative, null, void, or completion
   null per the registered bars), update README/CONTINUITY/HANDOFF.
