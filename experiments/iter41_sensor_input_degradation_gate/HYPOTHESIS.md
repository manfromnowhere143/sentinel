# Iteration 41 - monitor-input degradation gate pre-registration

Frozen after iteration 40 was published as `TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE`, and before
any iteration-41 analyzer, replay table, perturbation result, proof report, documentation claim
update, gcloud command, Docker command, model replay, image perturbation run, iteration-38
calibration replay, heldout replay, selector evaluation, or closed-loop work.

Iteration 41 is an offline external-validity gate over committed decision logs. It does not modify
camera images, rerun UniAD, rerun NeuroNCAP, or claim closed-loop safety under degraded sensors.
Its narrow purpose is to test a necessary precondition for any sensor-degradation claim:

> If the released-union monitor's own object-stream decision rule is brittle under mild frozen
> object-input perturbations on the committed full14/power evidence, then no degraded-sensor GPU
> or closed-loop run is scientifically justified yet.

This gate is intentionally allowed to fail. A failure is a useful hidden-assumption finding.

## Research question

Using only committed full14/power released-union decision logs and run archives, does the monitor's
object-stream decision rule preserve its intervention behavior under four frozen mild input
degradations?

Acceptable positive claim if every bar passes:

> On the committed full14/power released-union decision stream, the monitor's offline object-stream
> replay is stable under the frozen score-threshold, range-limit, deterministic dropout, and
> deterministic jitter perturbations strongly enough to justify a separate degraded-sensor
> closed-loop pre-registration.

Acceptable negative claim if any bar fails:

> The released-union monitor is brittle under at least one frozen object-stream degradation in
> offline replay. Sensor-degradation robustness is not established, and no degraded-sensor
> closed-loop run is authorized from this line.

Forbidden claims, even on a pass:

- no camera/image degradation claim;
- no claim that UniAD itself is robust under degraded sensors;
- no closed-loop, NeuroNCAP, selector, deployment, production, or real-world safety claim;
- no claim that object-stream perturbation equals physical sensor degradation;
- no wall-clock latency or production-cost claim;
- no claim that iteration 38 passed calibration or heldout.

## Frozen input artifacts

Iteration 41 may read only committed artifacts:

- `experiments/iter40_timing_cost_audit/RESULT.md`;
- `experiments/iter40_timing_cost_audit/proof-audit/timing_cost_report.json`;
- `experiments/full14_power/RESULT.md`;
- `experiments/full14_power/proof/analysis_output.txt`;
- `experiments/full14_power/proof/p14-runs.tar.gz`;
- `experiments/full14_power/proof/sentinel-power14-merged.log`;
- `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa`;
- `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-ab`;
- `experiments/iter15_latch_release/server_patch_union_release.py`;
- `experiments/iter15_latch_release/RESULT.md`;
- `docs/REPORT.md`;
- `docs/paper/MANUSCRIPT.md`;
- `README.md`.

Iteration 41 must not read remote GPU files, uncommitted logs, unpublished iteration-38 calibration
output, fresh model output, image files outside committed archives, external web sources, or any
dataset files outside committed archives.

## Frozen replay rule

The offline replay must implement the released-union decision rule from
`experiments/iter15_latch_release/server_patch_union_release.py`:

- object score threshold `SENTINEL_MIN_SCORE = 0.3`;
- maximum object gap `SENTINEL_MAXGAP = 30.0 m`;
- CPA margin `SENTINEL_CPA_MARGIN = 1.5 m`;
- TTC threshold `SENTINEL_TTC = 2.5 s`;
- minimum closing speed `SENTINEL_MIN_CLOSING = 3.0 m/s`;
- latch release after `SENTINEL_RELEASE_K = 4` consecutive clear frames;
- ego plan points and object positions use the logged ego-frame `traj` and `objs`;
- object identities use logged `object_ids` if present, otherwise deterministic object index
  `idx_<i>`, matching the patch fallback.

The replay may use only the best-arm frame rows in reconstructed
`sentinel_p14_best.jsonl.gz`. It must not use the `brake` rows as input to decide future state
except for the S0 vanilla reproduction comparison.

## Frozen perturbations

After S0 vanilla replay passes, run exactly these perturbation modes:

1. `score_0p50`: raise the object score threshold to `0.50`;
2. `range_20m`: lower maximum object gap to `20.0 m`;
3. `dropout_20pct`: delete an object row when
   `sha256("iter41|dropout_20pct|<scenario>|<run>|<frame_index>|<object_index>") mod 100 < 20`;
4. `jitter_0p25m`: add deterministic ego-frame x/y offsets in `[-0.25 m, +0.25 m]` from
   `sha256("iter41|jitter_0p25m|<scenario>|<run>|<frame_index>|<object_index>|x|y")`.

Perturbations are global and frozen. No per-scene, per-class, per-row, adaptive, or post-hoc
perturbation strength is allowed.

## Frozen episode labels

Use iteration-40's committed episode labels exactly:

- `off_collision=true`;
- `off_collision=false`;
- `off_collision=null` for the one missing OFF run.

Use iteration-40's committed lead-time rows exactly to identify the `61` measured lead-time
episodes and their OFF contact timestamps.

## S0 - artifact and vanilla replay integrity

S0 passes only if:

- every frozen input path exists and is committed;
- full14/power H-P0 is PASS in the committed analysis output;
- iteration 40 verdict is `TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE`;
- reconstructed `sentinel_p14_best.jsonl.gz` has exactly `400` reset blocks, `7,835` frame rows,
  and `1,205` logged brake rows;
- vanilla offline replay reproduces the logged released-union decisions exactly:
  - `1,205` brake frames;
  - `230` intervention episodes;
  - every episode's brake-frame count matches the logged count;
  - every episode's first-brake frame index matches the logged first-brake frame index when the
    episode has an intervention;
- no gcloud, Docker, model replay, image perturbation, selector, heldout, or closed-loop command
  runs.

If S0 fails, publish `DEGRADATION_GATE_INFRASTRUCTURE_NULL` and stop. No degradation claim is
authorized.

## S1 - safety-retention bars under perturbation

For each perturbation mode, among episodes with `off_collision=true` and a vanilla intervention:

- at least `90%` remain intervention episodes;
- median first-brake delay relative to vanilla is `<= 0.50 s`;
- no more than `10%` have first-brake delay `> 1.00 s`;
- total brake frames are at least `70%` of vanilla total brake frames for this subset.

If any perturbation fails S1, publish `DEGRADATION_GATE_NULL_SAFETY_RETENTION_FAIL`. No
degraded-sensor GPU run is authorized.

## S2 - selectivity/no-extra-cost bars under perturbation

For each perturbation mode, among episodes with `off_collision=false`:

- new intervention episodes among vanilla no-intervention episodes are `<= 5%` of
  `off_collision=false` episodes;
- total brake frames are `<= 125%` of vanilla total brake frames for `off_collision=false`
  episodes;
- median brake frames per intervention episode are `<= 125%` of vanilla median for this subset,
  or unchanged if vanilla has zero interventions.

If any perturbation fails S2, publish `DEGRADATION_GATE_NULL_SELECTIVITY_COST_FAIL`. No
degraded-sensor GPU run is authorized.

## S3 - lead-time stability bars under perturbation

For each perturbation mode, on the `61` iteration-40 measured lead-time episodes:

- at least `90%` retain an intervention;
- measured median lead-time delta relative to vanilla is `>= -0.50 s`;
- no more than `10%` of retained interventions have lead-time delta `< -1.00 s`;
- negative lead-time fraction is `<= 0.10`.

If any perturbation fails S3, publish `DEGRADATION_GATE_NULL_LEADTIME_STABILITY_FAIL`. No
degraded-sensor GPU run is authorized.

## S4 - successor authorization boundary

If S0-S3 all pass, the only authorized next step is a separate degraded-sensor closed-loop
pre-registration. That future pre-registration must name the physical/image degradation, scenario
set, run budget, H-P0-style validity gate, safety-retention bars, and selectivity/no-extra-cost
bars before any GPU run.

Iteration 41 itself authorizes no GPU work, image perturbation, closed-loop result, selector
evaluation, deployment language, or safety claim.

## Named falsifiers

- **Artifact drift.** Required committed evidence is missing, untracked, unreadable, or no longer
  matches the frozen counts.
- **Replay mismatch.** The vanilla offline replay cannot reproduce logged released-union brake
  frames and first-brake indices exactly.
- **Safety-retention brittleness.** Perturbation removes or delays interventions on episodes where
  OFF collided and vanilla intervened.
- **Selectivity/cost brittleness.** Perturbation introduces extra interventions or brake budget on
  OFF-noncollision episodes.
- **Lead-time brittleness.** Perturbation materially reduces reconstructable lead time.
- **Overclaim.** RESULT language treats object-stream replay as camera degradation, closed-loop
  safety, deployment readiness, or real-world robustness.
- **GPU leakage.** Any model/GPU/closed-loop work runs before this offline gate is published.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/degradation_gate_report.json`;
- `proof-audit/local_verification.txt`;
- reconstructed gzip SHA256 receipt if temporary reconstruction is used;
- S0/S1/S2/S3/S4 pass/fail tables with every failed bar listed;
- per-perturbation safety-retention, selectivity/cost, and lead-time summaries;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running iteration-41 tooling.
2. Commit analyzer code and tests before producing the audit report.
3. Run the audit once on committed inputs.
4. Publish `RESULT.md` at full weight whether S0, S1, S2, or S3 fails or passes.
5. A pass authorizes only a separate future degraded-sensor closed-loop pre-registration. It does
   not authorize iteration-38 calibration, a GPU run, selector evaluation, deployment language, or
   safety claims.
