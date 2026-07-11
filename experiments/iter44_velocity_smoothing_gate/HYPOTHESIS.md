# Iteration 44 - offline velocity temporal-smoothing repair gate pre-registration

Frozen after iteration 43 was published as `OBJECT_PERTURBATION_MILD_FRAGILE`, and before any
iteration-44 analyzer, estimator code, proof report, documentation claim update, gcloud command,
Docker command, GPU run, model replay, image perturbation, iteration-38 calibration replay,
heldout replay, selector evaluation, or closed-loop work. No iteration-44 analysis code has read
the committed trace at the time this file is committed.

Iteration 43's S4 boundary closed the offline object-stream perturbation line at the committed
trace and required a fresh pre-registration for any successor, naming smoothed-input variants
explicitly as one such successor. This is that fresh pre-registration.

## Motivation (the convergent finding this gate tests)

Two independent lines of this campaign converge on velocity-estimation quality as the binding
constraint of the released-union rule:

- **Iteration 18** (the deployment-flip line): the offline tracker gate showed the measured
  velocity-flicker class is real and repairable — velocity continuity through identity breaks
  converted 12/13 unsafe crawl frames — and its published warning stands: any velocity-repair
  successor must carry an explicit overfitting guard, with bars frozen before data
  (`experiments/iter18_tracker/RESULT.md`).
- **Iteration 43** (the robustness line): the rule over-fires under 5 cm per-frame position
  jitter (`17` new interventions vs the `<=8` bar at sigma `0.05 m`, `36` at `0.10 m`), and the
  published mechanism reading is that object velocity is a per-frame finite difference of
  world-frame positions at the ~2 Hz monitor cadence, so independent per-frame position noise
  manufactures spurious velocity near the CPA/TTC thresholds
  (`experiments/iter43_object_stream_perturbation_gate/RESULT.md`).

## Research question and hypothesis

On the committed iteration-42 exact trace, does replacing the rule's one-frame
finite-difference velocity estimator with a temporally smoothed estimator (frozen variants and
parameters below) restore decision stability under the iteration-43 jitter cells **while
preserving fidelity to the online decision stream on the unperturbed trace and without creating
new fragility in the other perturbation families' mild cells**?

Hypothesis: at least one frozen estimator cell passes all three registered gates (V1 baseline
fidelity, V2 jitter repair, V3 no new fragility). The competing outcome is itself the finding:
if smoothing repairs jitter only at the price of baseline fidelity, the registered result is
the fidelity-repair tradeoff, published at full weight.

## Honest boundary, stated before anything else

This gate measures **decision-flip behavior of a modified monitor rule in offline replay**, not
vehicle outcomes. Replay does not re-render, does not re-run the planner, and does not close
the loop: when the smoothed rule changes a brake decision — on the clean trace or under
perturbation — every subsequent logged frame still comes from the unperturbed online run, so
the downstream consequences of the changed decision (vehicle position, actor behavior, later
monitor inputs, collisions, NeuroNCAP score) are **not observable offline** and are not
measured here. V1 "fidelity" is decision-agreement with the online stream, not proof of equal
safety. A full pass authorizes ONLY a future closed-loop pre-registration for a smoothed-rule
variant; it does not modify the released union, and it is not a robustness, benchmark,
deployment, or safety claim.

## Frozen input artifacts

Iteration 44 may read only committed artifacts:

- `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz`
  (SHA256 must equal `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d` before
  and after analysis);
- `experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py` (the replay
  implementation of the released-union rule — imported, not reimplemented);
- `experiments/iter43_object_stream_perturbation_gate/analyze_object_perturbation.py` (the
  perturbation layer, seed derivation, and stability-bar classifier — imported, not
  reimplemented);
- `experiments/iter43_object_stream_perturbation_gate/proof-perturbation/object_perturbation_report.json`
  (the committed iteration-43 per-cell reference numbers);
- `experiments/iter42_exact_trace_replay_support/RESULT.md` and `HYPOTHESIS.md`;
- `experiments/iter43_object_stream_perturbation_gate/RESULT.md` and `HYPOTHESIS.md`;
- `README.md`, `docs/REPORT.md`.

It must not read remote GPU files, uncommitted logs, model checkpoints, dataset files, or any
external source. It must not mutate any committed artifact.

## Frozen rule surface (reuse, not reimplementation)

The iteration-44 analyzer must import and call:

- the committed iteration-42 module (`analyze_trace_replay.py`) for trace parsing
  (`parse_trace_blocks`, `PAIR_ORDER`), geometry (`transform_point`), and parameters
  (`params_for_row`, `PARAMS`);
- the committed iteration-43 module (`analyze_object_perturbation.py`) for the perturbation
  layer (`perturb_block`), the seed derivation, and the frozen stability-bar classifier
  (`classify_cell`, `BARS`, `ONLINE`).

The ONLY registered modification is the object-velocity estimator inside the frame rule. All
other terms — score/gap filtering, world-frame transform, CPA minimization over the plan, the
closing/TTC test, the fired condition, and the K=4 latch/release state machine — must be
byte-for-byte the same expressions as the iteration-42 implementation, enforced by the S1
exact-identity gate below. The six released-union parameters stay exactly as logged per row:
`SENTINEL_MIN_SCORE = 0.3`, `SENTINEL_MAXGAP = 30.0 m`, `SENTINEL_CPA_MARGIN = 1.5 m`,
`SENTINEL_TTC = 2.5 s`, `SENTINEL_MIN_CLOSING = 3.0 m/s`, `SENTINEL_RELEASE_K = 4`.

## Frozen smoothed velocity estimators (two variants, four verdict cells, no additions)

Reference (the online rule, iteration 42): per surviving object identity, velocity is the
one-frame finite difference of consecutive world-frame positions,
`v = (w_t - w_{t-1}) / dt` with `dt = (ts_t - ts_{t-1})/1e6` and a `dt > 1e-3` guard; an
identity absent from the previous frame's filtered set has velocity `0`; per-identity state is
rebuilt each frame from only the objects that survive the score/gap filters (an identity that
misses one frame loses all state).

Both smoothed variants keep exactly those state-lifetime semantics (state rebuilt each frame
from filter survivors; one missed frame clears the identity's history; first appearance has
velocity `0`; the `dt > 1e-3` guard applies and a guarded frame contributes velocity `0`).
Only the velocity value changes:

1. **FD-k (k-frame finite difference).** Per identity, keep the last `k` surviving
   world-frame observations `(w, ts)`. Velocity is the finite difference from the OLDEST stored
   observation: `v = (w_t - w_oldest) / ((ts_t - ts_oldest)/1e6)`. With fewer than `k` stored
   observations the oldest available is used (so the first frame after appearance equals the
   raw estimator). Frozen parameters: `k ∈ {2, 3}`. Neutral parameter `k = 1` is algebraically
   the raw rule and is reserved for the S1 identity gates, not the verdict.
2. **EMA (exponential moving average on the velocity).** Per identity, compute the raw
   one-frame finite-difference velocity `v_raw` exactly as the reference, then smooth:
   `v_hat_t = alpha * v_raw_t + (1 - alpha) * v_hat_{t-1}` when a previous smoothed velocity
   exists for the identity, else `v_hat_t = v_raw_t`. The rule consumes `v_hat_t`. On a
   `dt <= 1e-3` guarded frame the consumed velocity is `0` and the stored EMA state carries
   unchanged. Frozen parameters: `alpha ∈ {0.5, 0.3}`. Neutral parameter `alpha = 1.0` is
   algebraically the raw rule and is reserved for the S1 identity gates, not the verdict.

The four verdict cells are exactly: `fd_k2`, `fd_k3`, `ema_a0p5`, `ema_a0p3`. No other
variant, parameter, interpolation, per-scene/per-family parameter, composition, or post-hoc
grid widening is allowed. Iteration 18's overfitting warning is binding: these parameters are
frozen before any iteration-44 code reads the trace, and no parameter is revisited after data.

## Frozen determinism seed

Iteration 44's perturbation draws MUST be bit-identical to iteration 43's, so every comparison
is seed-paired: the imported iteration-43 layer is used with its committed seed string
`iter43-object-stream-perturbation-v1` and its committed SHA256 derivation, unchanged. The
smoothed estimators are deterministic and introduce no randomness. The fresh iteration-44 run
identifier `iter44-velocity-smoothing-v1` is committed here and stamped into the report; it
seeds nothing.

## Frozen evaluation grid (run once)

Per estimator verdict cell (4 cells):

- **V1 fidelity**: the unperturbed trace, replayed with the smoothed rule.
- **V2 repair**: the iteration-43 jitter cells `sigma ∈ {0.05, 0.10} m`, same seed.
- **V3 no new fragility**: the iteration-43 mild cells of the other three families —
  dropout `p = 0.05`, score `f = 0.90`, churn `p = 0.05`, same seed.
- **Dose-response characterization (no verdict weight)**: jitter
  `sigma ∈ {0.25, 0.50, 1.00} m`, same seed, reported with the same per-cell classification
  but never feeding the verdict.

Outcome measures per cell are iteration 43's, unchanged, against the committed online
reference (`1,205` brake frames, `156` releases, `230/400` intervention episodes, `170`
non-intervention episodes, `6,474` frames): intervention retention, new interventions,
first-brake delay (median frames and fraction `> 2` frames among retained), total brake
frames, brake/fired flips, releases.

## Frozen bars

**V1 baseline fidelity** (per estimator cell, unperturbed trace vs the online decisions;
passes only if ALL hold):

1. Intervention retention `>= 225/230`.
2. New interventions `<= 4/170`.
3. Median first-brake delay `<= 1` frame among retained interventions.
4. Fraction of retained interventions with first-brake delay `> 2` frames `<= 0.05`.
5. Total brake frames within `[1085, 1325]` (±10% of `1,205`).

Stated honestly before data: temporal smoothing necessarily lags genuine velocity onset — FD-3
averages over up to 1.5 s of history, and EMA at `alpha = 0.3` carries 70% of the previous
estimate — so the smoothed rule WILL brake later on some true threats. One frame is one 0.5 s
monitor step of simulated time. The bars above freeze the acceptable cost: a median lag of at
most one step and gross lag (`> 2` steps, i.e. `> 1 s`) on at most 5% of retained
interventions. A cell that erases or grossly delays true onsets fails V1 and is not rescued by
passing V2; delay here is decision timing only, and its closed-loop consequence is not
measurable offline.

**V2 robustness repair** (per estimator cell): the jitter `sigma 0.05 m` AND `sigma 0.10 m`
cells must BOTH classify STABLE under iteration 43's frozen bars, reused verbatim via the
imported classifier: retention `>= 219/230`; new interventions `<= 8/170`; median first-brake
delay `<= 1` frame; delay `> 2` frames `<= 0.10` of retained; total brake frames in
`[1025, 1385]`.

**V3 no new fragility** (per estimator cell): dropout `0.05`, score `0.90`, and churn `0.05`
must ALL classify STABLE under the same iteration-43 bars. (Iteration 43 measured all three
STABLE under the raw estimator; smoothing must not break them.)

Bars never move after data.

## S0 - static provenance

S0 passes only if:

- this `HYPOTHESIS.md` is committed alone, before any iteration-44 analyzer or estimator code
  exists;
- the analyzer and tests are committed before the single analysis run;
- the committed trace file's SHA256 equals the frozen value above;
- iteration 42's committed verdict is `TRACE_REPLAY_SUPPORT_PASS` and iteration 43's committed
  verdict is `OBJECT_PERTURBATION_MILD_FRAGILE`;
- local `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py` pass before the
  run;
- no gcloud, Docker, GPU, model, or closed-loop command is needed or used.

If S0 fails, publish `VELOCITY_SMOOTHING_STATIC_NULL` and stop.

## S1 - neutral-parameter identity (the rule-drift gate)

S1 passes only if BOTH neutral estimator cells (`fd_k1` and `ema_a1p0`), replayed through the
iteration-44 smoothed implementation on the unperturbed trace via the imported iteration-43
zero-strength input path, reproduce the online decision stream exactly: `0` mismatched frames
on `fired`/`brake`/`release`/`post_braking`/`post_clear` over `400` blocks and `6,474` frames,
totals exactly `1,205` brake frames, `156` releases, `230` intervention episodes.

**S1b - seed-paired perturbation equivalence.** The neutral `fd_k1` cell, replayed under the
imported iteration-43 perturbation layer at jitter `sigma 0.05 m` and `sigma 0.10 m` with the
committed seed, must reproduce iteration 43's committed cell metrics exactly (equality on
`retained_interventions`, `lost_interventions`, `new_interventions`,
`median_first_brake_delay_frames`, `delay_gt2_fraction`, `brake_frames`, `release_frames`,
`brake_flips`, `fired_flips`, field by field against the committed
`object_perturbation_report.json` — headline integers: retained `218`, new `17`, brake frames
`1275`, brake flips `240` at `0.05`; retained `214`, new `36`, brake frames `1445`, brake
flips `484` at `0.10`).

If S1 or S1b fails, publish `VELOCITY_SMOOTHING_IDENTITY_NULL` and stop before any smoothed
cell is interpreted.

## S2 - the frozen grid, run once

Run the full frozen evaluation grid exactly once. The designated determinism-guard cell
(`fd_k2` under jitter `sigma 0.10 m`) is computed twice inside the same run and its two summary
hashes must match; a mismatch publishes `VELOCITY_SMOOTHING_DETERMINISM_NULL`.

Verdict, from the four verdict cells only:

- at least one estimator cell passes V1 AND V2 AND V3 ->
  `VELOCITY_SMOOTHING_REPAIR_PASS` (every passing cell is named; no post-hoc selection of a
  single winner beyond reporting all passing cells);
- no cell passes all three, but at least one cell passes V2 ->
  `VELOCITY_SMOOTHING_TRADEOFF_NULL` (the registered fidelity-repair tradeoff, published at
  full weight with every failed bar named per cell — the finding is that smoothing buys jitter
  stability only at the price of baseline fidelity or new fragility);
- no cell passes V2 -> `VELOCITY_SMOOTHING_NO_REPAIR_NULL` (published at full weight — the
  fragility is then not repaired by temporal velocity smoothing at these frozen parameters,
  which bounds the mechanism reading of iteration 43).

Dose-response cells never change the verdict. No re-runs to improve numbers. If a code bug is
found after the run, the bug, the fix, and the re-run all go on the record in `RESULT.md`.

## S3 - claim-boundary audit

S3 passes only if `RESULT.md` and every active-doc update state: this is offline
decision-replay evidence about a modified rule's input sensitivity on the frozen trace; the
released union itself is unchanged; changed decisions' vehicle outcomes are not observable
offline; and no sensor/camera degradation, closed-loop, benchmark, NeuroNCAP-score, selector,
deployment, production, latency, comfort, or safety claim is made. If S3 fails, publish
`VELOCITY_SMOOTHING_OVERCLAIM_NULL` and narrow docs before any new work.

## S4 - successor authorization boundary

Whatever the verdict, iteration 44 authorizes no GPU run, image or sensor perturbation,
closed-loop degradation run, modification of the released union, iteration-38 calibration,
heldout replay, iteration-12 scoring, selector evaluation, deployment language, or safety
claim. A `REPAIR_PASS` authorizes ONLY a separate future closed-loop pre-registration for a
smoothed-velocity rule variant (which must carry its own safety gates and falsifiers before any
GPU time). A `TRADEOFF_NULL` or `NO_REPAIR_NULL` closes the temporal-smoothing repair line at
these frozen parameters; any successor requires a fresh pre-registration.

## Named falsifiers

- **Fidelity-repair tradeoff.** Smoothing passes V2 but every cell fails V1 (or V3): the
  registered finding is the tradeoff, published as `VELOCITY_SMOOTHING_TRADEOFF_NULL` at full
  weight.
- **Parameter overfitting.** Any estimator variant or parameter outside the frozen four
  verdict cells; any post-hoc grid widening, interpolation, or per-scene/per-family parameter
  (iteration 18's warning, binding here).
- **Rule reimplementation drift.** The analyzer fails to import the committed iteration-42
  replay module and iteration-43 perturbation/classifier module; or S1 neutral identity is not
  exact; or S1b does not reproduce iteration 43's committed cell numbers exactly.
- **Trace mutation.** The committed trace SHA256 differs before vs after analysis.
- **Seed drift.** Any perturbation draw outside the committed iteration-43 derivation and seed
  string; any new randomness.
- **Determinism failure.** The duplicated guard cell yields differing summary hashes.
- **Bar drift.** Any V1/V2/V3 bar, the estimator grid, or the verdict rule changes after data.
- **Overclaim.** RESULT or doc language turns offline decision-replay evidence into sensor
  degradation, closed-loop robustness, deployment, or safety evidence, or presents the
  smoothed rule as the released configuration.
- **Compute leakage.** Any gcloud, Docker, GPU, model, or closed-loop command runs in this
  iteration.

## Required proof artifacts

- exact command line;
- analyzer source and tests;
- `proof-smoothing/velocity_smoothing_report.json` (S1/S1b receipts, per-cell V1/V2/V3
  tables with every failed bar, dose-response tables, determinism guard, verdict);
- `proof-smoothing/analyze_velocity_smoothing.command.txt`;
- `proof-smoothing/local_verification.txt`;
- trace SHA256 receipts before and after the run;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` alone, before writing any iteration-44 code.
2. Commit the analyzer and tests; local `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py` must pass.
3. Run the analyzer exactly once from committed artifacts per the frozen grid and seed.
4. Publish `RESULT.md` at full weight whether the verdict is pass, tradeoff, no-repair, or
   null.
5. Update README, CONTINUITY, and HANDOFF; commit and push every state change.
