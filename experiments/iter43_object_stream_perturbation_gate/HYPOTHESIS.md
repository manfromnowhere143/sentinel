# Iteration 43 - offline object-stream perturbation gate pre-registration

Frozen after iteration 42 was published as `TRACE_REPLAY_SUPPORT_PASS`, and before any
iteration-43 analyzer, perturbation code, proof report, documentation claim update, gcloud
command, Docker command, GPU run, model replay, image perturbation, iteration-38 calibration
replay, heldout replay, selector evaluation, or closed-loop work. No analysis code has read the
committed trace at the time this file is committed.

Iteration 43 is the successor iteration 42 explicitly authorized and nothing more: an offline
object-stream perturbation gate over the committed iteration-42 exact trace
(`experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz`,
SHA256 `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d`). Iteration 42 proved
that offline replay of the released-union rule from logged inputs reproduces every online
decision exactly at perturbation strength zero. Iteration 43 perturbs those logged inputs and
measures how the replayed decisions move.

## Honest boundary, stated before anything else

This gate measures **decision-flip sensitivity of the monitor rule**, not vehicle outcomes.
Replay does not re-render, does not re-run the planner, and does not close the loop: when a
perturbed replay changes a brake decision, every subsequent logged frame still comes from the
unperturbed online run, so the downstream consequences of the changed decision — vehicle
position, actor behavior, later monitor inputs, collisions, NeuroNCAP score — are **not
observable offline** and are not measured here. Perturbing the logged object stream is also not
sensor degradation: the objects are the frozen planner's detection outputs as consumed by the
monitor, the perturbation is injected between the log and the rule, and the planner never sees
it. Scope is exactly: the released-union monitor RULE's input-robustness on the frozen
full14/power best-arm trace, in replay.

## Research question

On the committed iteration-42 exact trace, how stable are the released-union monitor's replayed
brake/release/intervention decisions under frozen deterministic perturbations of the logged
object stream — object position jitter, detection dropout, object-score attenuation, and
track-identity churn — and do the mild perturbation levels keep the decision stream within the
frozen stability bars?

Acceptable positive claim if every bar passes:

> On the frozen full14/power exact trace, the released-union monitor rule's replayed decisions
> are stable under the registered mild object-stream perturbations: intervention retention,
> false-intervention introduction, first-brake timing, and brake-frame budget all stay within
> the frozen bars. This is replay decision-stability evidence only.

Acceptable negative claim if any mild bar fails:

> The released-union monitor rule is decision-fragile in replay under at least one registered
> mild object-stream perturbation on the frozen trace. The fragile family and failed bars are
> named. This is a full-weight finding about the rule's input sensitivity, not a closed-loop or
> safety result.

Forbidden claims, even on a pass:

- no camera, image, or physical sensor degradation claim;
- no claim that UniAD (or its detector) is robust or fragile under degraded sensors;
- no closed-loop claim of any kind — replay does not re-render, and closed-loop consequences of
  changed decisions are not observable offline;
- no new benchmark, NeuroNCAP-score, selector, deployment, production, or real-world safety
  claim;
- no claim that replay decision-stability implies the closed-loop score would survive the same
  perturbations;
- no wall-clock latency, comfort, or production-cost claim;
- no claim that iteration 38 passed calibration or heldout.

## Frozen input artifacts

Iteration 43 may read only committed artifacts:

- `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz`
  (SHA256 must equal `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d` before
  and after analysis);
- `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel-iter42-trace.log`
  (pair-order check only);
- `experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py` (the replay
  implementation of the released-union rule — reused, not reimplemented);
- `experiments/iter42_exact_trace_replay_support/RESULT.md` and `HYPOTHESIS.md`;
- `README.md`, `docs/REPORT.md`.

It must not read remote GPU files, uncommitted logs, model checkpoints, dataset files, or any
external source. It must not mutate any committed artifact.

## Frozen replay rule (reuse, not reimplementation)

The iteration-43 analyzer must import and call the committed iteration-42 replay functions
(`frame_support` / `replay_block` in
`experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py`) for every replay,
perturbed or not. Writing a second implementation of the released-union rule is a named
falsifier. The six released-union parameters stay exactly as logged per row:
`SENTINEL_MIN_SCORE = 0.3`, `SENTINEL_MAXGAP = 30.0 m`, `SENTINEL_CPA_MARGIN = 1.5 m`,
`SENTINEL_TTC = 2.5 s`, `SENTINEL_MIN_CLOSING = 3.0 m/s`, `SENTINEL_RELEASE_K = 4`.

Perturbations may modify only the per-frame logged `objs`, `scores`, and effective object
identities. They must never modify `traj`, `ego2world`, `ts`, `params`, `frame_index`, reset
structure, or block order. Because the iteration-42 patch logs `object_ids` as possibly empty
(index fallback `idx_<i>`), the perturbation layer first materializes effective identities —
the logged id if present, else `idx_<i>` — and then perturbs; dropout deletes an object
together with its materialized id, so surviving identities are never renumbered by dropout
itself. The analyzer must report whether logged ids were present in the trace.

## Frozen determinism seed

All randomness derives from the single committed seed string
`iter43-object-stream-perturbation-v1` via SHA256 counters. For a draw with role `<role>` on
object `<i>` of frame `<frame_index>` of run `<run>` of pair `<class>/<scenario>`, the uniform
is `u = int.from_bytes(sha256("iter43-object-stream-perturbation-v1|<family>|<level>|<class>|
<scenario>|<run>|<frame_index>|<i>|<role>").digest()[:8], "big") / 2**64`. Gaussian draws use
Box-Muller over two such uniforms (roles `<axis>_u1`, `<axis>_u2`). Pair class/scenario come
from the frozen iteration-42 pair order (block index // 20). No other RNG, no re-seeding, no
seed search.

## Frozen perturbation grid (14 cells, no additions, no deletions)

1. **Position jitter** — add Gaussian ego-frame offsets to each surviving object's logged x/y,
   sigma per axis, at `sigma ∈ {0.05, 0.10, 0.25, 0.50, 1.00} m`.
2. **Detection dropout** — delete an object (with its score and materialized id) when the
   dropout uniform is `< p`, at `p ∈ {0.05, 0.10, 0.20}`.
3. **Score attenuation** — multiply every logged object score by `f ∈ {0.90, 0.80, 0.60}`
   (objects falling below `SENTINEL_MIN_SCORE = 0.3` are then filtered by the unchanged rule).
4. **Track-identity churn** — replace an object's materialized identity with a fresh unique
   per-(frame, object) identity when the churn uniform is `< p`, at `p ∈ {0.05, 0.10, 0.20}`.
   Velocity is not a logged input: the rule derives object velocity from cross-frame identity,
   so identity churn is the registered velocity-noise family.

Perturbations are global over all 400 episodes and all frames; no per-scene, per-class,
adaptive, or post-hoc strength is allowed. Exactly one family/level per cell; no compositions.

The **mild set** is frozen as these five cells: jitter `0.05 m`, jitter `0.10 m`, dropout
`0.05`, score `0.90`, churn `0.05`. Only mild cells feed the verdict; all other cells publish
as dose-response characterization with the same per-cell classification but no verdict weight.

## Frozen outcome measures (per cell, vs the committed online decisions)

Online reference: the logged decision stream iteration 42 proved bit-identical to replay at
strength zero — `1,205` brake frames, `156` release rows, `230` intervention episodes out of
`400`, hence `170` non-intervention episodes.

- **Intervention retention**: count of the `230` online intervention episodes that still contain
  at least one replayed brake frame.
- **New interventions**: count of the `170` online non-intervention episodes that gain at least
  one replayed brake frame.
- **First-brake delay**: for episodes that intervene both online and perturbed, perturbed
  first-brake `frame_index` minus online first-brake `frame_index`, in frames (one frame is one
  monitor step, nominally 0.5 s of simulation time at the 2 Hz keyframe cadence); report median
  and the fraction with delay `> 2` frames.
- **Brake-frame budget**: total replayed brake frames across all frames.
- **Frame flip rate**: count of frames whose replayed `brake` boolean differs from the online
  `brake` boolean, out of `6,474` (reported; also `fired` flips).
- **Releases**: total replayed release rows (reported).

## Frozen stability bars (per cell; classify STABLE only if ALL hold)

1. Intervention retention `>= 219/230` (>= 95%).
2. New interventions `<= 8/170` (<= 5%).
3. Median first-brake delay `<= 1` frame among retained interventions.
4. Fraction of retained interventions with first-brake delay `> 2` frames `<= 0.10`.
5. Total brake frames within `[85%, 115%]` of `1,205`, i.e. the integer range `[1025, 1385]`.

A cell failing any bar is FRAGILE with the failed bars listed. Bars never move after data.

## S0 - static provenance

S0 passes only if:

- this `HYPOTHESIS.md` is committed before any iteration-43 analyzer or perturbation code
  exists;
- the analyzer and tests are committed before the single analysis run;
- the committed trace file's SHA256 equals the frozen value above;
- iteration 42's committed verdict is `TRACE_REPLAY_SUPPORT_PASS`;
- local `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py` pass before the run;
- no gcloud, Docker, GPU, model, or closed-loop command is needed or used.

If S0 fails, publish `OBJECT_PERTURBATION_STATIC_NULL` and stop.

## S1 - zero-strength identity through the reused rule

S1 passes only if the iteration-43 analyzer, calling the imported iteration-42 replay functions
through its own (perturbation-capable, strength-zero) input path, reproduces the online
decision stream exactly: `0` mismatched frames on `fired`/`brake`/`release`/`post_braking`/
`post_clear`, totals exactly `1,205` brake frames, `156` releases, `230` intervention episodes,
over `400` blocks and `6,474` frames, and the trace SHA256 is unchanged after reading.

If S1 fails, publish `OBJECT_PERTURBATION_IDENTITY_NULL` and stop before any perturbed cell is
interpreted.

## S2 - the frozen grid, run once

Run the 14-cell grid exactly once with the committed seed. The designated determinism-guard
cell (jitter `0.25 m`) is computed twice inside the same run and its two summary hashes must
match; a mismatch is a determinism falsifier and publishes
`OBJECT_PERTURBATION_DETERMINISM_NULL`. Classify every cell STABLE/FRAGILE per the frozen bars
and publish per-family tables.

Verdict from the mild set only:

- all five mild cells STABLE -> `OBJECT_PERTURBATION_MILD_STABLE_PASS`;
- any mild cell FRAGILE -> `OBJECT_PERTURBATION_MILD_FRAGILE` (published at full weight with
  the fragile families and failed bars named).

Non-mild cells never change the verdict; they are the registered dose-response
characterization.

No re-runs to improve numbers. If a code bug is found after the run, the bug, the fix, and the
re-run all go on the record in `RESULT.md`.

## S3 - claim-boundary audit

S3 passes only if `RESULT.md` and every active-doc update state: this is replay decision-flip
sensitivity of the monitor rule on the frozen trace; not sensor/camera degradation; not
closed-loop (consequences of changed decisions are not observable offline); not a benchmark,
selector, deployment, or safety claim. If S3 fails, publish
`OBJECT_PERTURBATION_OVERCLAIM_NULL` and narrow docs before any new work.

## S4 - successor authorization boundary

Whatever the verdict, iteration 43 authorizes no GPU run, image or sensor perturbation,
closed-loop degradation run, iteration-38 calibration, heldout replay, iteration-12 scoring,
selector evaluation, deployment language, or safety claim. A `MILD_STABLE_PASS` authorizes only
a separate future pre-registration if a closed-loop degradation line is ever opened; a
`MILD_FRAGILE` finding closes the offline line at this trace and requires a fresh
pre-registration for any successor.

## Named falsifiers

- **Rule reimplementation drift.** The analyzer implements its own copy of the released-union
  rule instead of importing the committed iteration-42 replay functions, or S1 zero-strength
  identity fails.
- **Trace mutation.** The committed trace SHA256 differs before vs after analysis.
- **Seed or grid drift.** Any draw outside the committed seed derivation; any cell added,
  removed, or re-leveled after this commit; any composition of families.
- **Determinism failure.** The duplicated guard cell yields differing summary hashes.
- **Bar drift.** Any stability bar or the mild-set definition changes after data.
- **Overclaim.** RESULT or doc language turns replay decision-flip sensitivity into sensor
  degradation, closed-loop robustness, deployment, or safety evidence.
- **Compute leakage.** Any gcloud, Docker, GPU, model, or closed-loop command runs in this
  iteration.

## Required proof artifacts

- exact command line;
- analyzer source and tests;
- `proof-perturbation/object_perturbation_report.json` (per-cell tables, bars, verdict);
- `proof-perturbation/analyze_object_perturbation.command.txt`;
- `proof-perturbation/local_verification.txt`;
- trace SHA256 receipts before and after the run;
- S0/S1/S2/S3/S4 pass/fail tables with every failed bar listed;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing any iteration-43 code.
2. Commit the analyzer and tests; local `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py` must pass.
3. Run the analyzer exactly once from committed artifacts per the frozen grid and seed.
4. Publish `RESULT.md` at full weight whether the verdict is pass, fragile, or null.
5. Update README, CONTINUITY, and HANDOFF; commit and push every state change.
