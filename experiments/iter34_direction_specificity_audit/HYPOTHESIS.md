# Iteration 34 - direction-specificity audit pre-registration

Frozen after iteration 33 was published as `CALIBRATION_NULL_NO_USABLE_ALPHA`, and before any
iteration-34 analyzer, report, threshold calculation, extrapolation table, GPU command, gcloud
command, model replay, heldout replay, iteration-12 scoring, selector evaluation, or closed-loop
work.

This is a post-result governance audit, not a blind confirmatory experiment. The iteration-33
aggregate calibration result is already known: no nonzero alpha passed S1. Iteration 34 asks a
narrow follow-up question using only committed calibration artifacts: does the failed global
bridge-centroid direction show enough target-specific, safety-aligned dose response to justify a
future scale-only or same-direction successor pre-registration, or should that line be closed?

## Research question

Using only the committed iteration-33 calibration proof artifacts, does the global
`fit_split_benign_centroid_minus_eligible_lowdiv_centroid` bridge direction produce a response that
is:

- monotonic enough to show the patch is coupled to downstream candidate geometry;
- stronger on `eligible_lowdiv` target rows than on `benign_control` rows;
- aligned with best-candidate gap rather than only spreading trajectories; and
- large enough that a scale-only successor would be numerically plausible without immediately
  exhausting the registered benign-control headroom?

Acceptable positive claim if every bar passes:

> The committed iteration-33 calibration artifacts show a target-specific, safety-aligned
> dose response for the existing global bridge-centroid direction, sufficient to justify a
> separate pre-registration for a scale-normalized same-direction intervention family.

Forbidden claims, even on a pass:

- no claim that iteration 33 passed;
- no selection of an iteration-33 alpha;
- no heldout, iteration-12, selector, NeuroNCAP, closed-loop, deployment, or safety claim;
- no claim that the bridge tensor is causally repaired;
- no claim that a larger alpha is safe, useful, or authorized;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets.

## Frozen input artifacts

Iteration 34 may read only committed source and proof artifacts:

- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/direction.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/HYPOTHESIS.md`;
- `experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md`;
- `experiments/iter33_prefix_preserving_bridge_intervention/analyze_intervention.py`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-prefix/prefix_manifest_report.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/canary_report.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/calibration_report.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sha256s.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/unsplit_sha256s.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/artifact_reconstruction.command.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/analyze_intervention.command.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00.jsonl.gz.part-*`.

Iteration 34 must not read iteration-12 frames, selector outcomes, closed-loop logs, heldout
iteration-33 target rows, uncommitted GPU files, or any fresh model output.

## Frozen row and metric definitions

Rows are matched by `(scene, sample_index, timestamp_us)` and must use iteration-33 target rows
only. Context-only prefix rows are audit rows and must not enter pass/fail metrics.

Metrics reuse iteration 33's definitions exactly:

- endpoint spread for the three command candidates;
- endpoint-spread delta from alpha `0.00`;
- best candidate closest gap and best-candidate-gap delta;
- executed final-endpoint displacement;
- danger crossing, low-diversity collapse, and gross-validity predicates.

The audit may compute only deterministic summaries of these metrics: medians, fractions, ratios,
least-squares slopes over the frozen alpha grid, and linear extrapolations clearly labeled as
diagnostic. Extrapolation is not evidence that an unrun alpha is safe or effective.

## S0 - artifact and row integrity

Before any response audit:

- `calibration_report.json` verdict must be `CALIBRATION_NULL_NO_USABLE_ALPHA`;
- prefix replay integrity in that report must be `true`;
- all five alphas must be present: `0.00`, `0.25`, `0.50`, `0.75`, `1.00`;
- each alpha must contain exactly `2452` target rows, `108` `eligible_lowdiv` rows, and `2344`
  `benign_control` rows;
- error rows must be `0`;
- gross-validity failures must be `0`;
- target keys must match exactly across all five alpha cells;
- split-gzip model shards must reconstruct into readable gzip streams;
- committed `sha256s.txt` and `unsplit_sha256s.txt` must be recorded in the report.

If any S0 bar fails, publish an infrastructure null and stop.

## S1 - dose-response coupling bars

S1 asks whether the patch produced an ordered downstream response at all. It is necessary but not
sufficient for any successor.

Pass bars:

- eligible median endpoint-spread delta is strictly increasing across nonzero alphas;
- eligible median endpoint-spread delta has Pearson correlation `>= 0.95` with alpha over the
  five-point grid;
- at least `70%` of `eligible_lowdiv` target rows have nonnegative endpoint-spread slope over the
  five-point grid;
- alpha `1.00` changes endpoint spread by more than `0.25 m` on at least `10%` of
  `eligible_lowdiv` rows.

If S1 fails, publish a no-dose-response null. No same-direction successor may be recommended.

## S2 - target-specificity and safety-alignment bars

S2 asks whether the response is specific enough to justify a future scale-only or same-direction
intervention pre-registration.

Pass bars:

- at alpha `1.00`, `eligible_lowdiv` median endpoint-spread delta is at least `0.10 m`;
- at alpha `1.00`, the ratio
  `eligible_lowdiv_median_endpoint_spread_delta / benign_control_median_endpoint_spread_delta`
  is at least `1.50`;
- at alpha `1.00`, `eligible_lowdiv` median best-candidate-gap delta is `>= 0.00 m`;
- at least `3` of the `4` nonzero alpha cells have nonnegative `eligible_lowdiv` median
  best-candidate-gap delta;
- the least-squares alpha needed to reach `0.25 m` eligible median endpoint-spread delta is
  `<= 2.00`;
- multiplying alpha `1.00` benign p95 executed final-endpoint displacement by that least-squares
  alpha estimate stays `<= 2.00 m`.

If S2 fails, publish a direction-specificity null. The same global bridge-centroid direction is
closed for scale-only successor work unless a later pre-registration changes the direction family,
target site, row conditioning, or claim.

## Named falsifiers

- **Artifact drift.** Required committed artifacts are missing, unreadable, or inconsistent with
  their recorded hashes.
- **Row mismatch.** Target keys, label counts, or alpha cells differ across the frozen grid.
- **No dose response.** Candidate-spread response is not ordered or not present on enough target
  rows.
- **Nonspecific perturbation.** Benign-control rows move as much as or more than eligible rows.
- **Spread without safety alignment.** Candidate spread increases while best-candidate gap does
  not improve.
- **Scale-only implausibility.** A diagnostic linear extrapolation needs alpha beyond the frozen
  benign-control headroom.
- **Leakage.** Any iteration-12 frame, selector outcome, heldout target row, uncommitted model log,
  GPU rerun, altered alpha grid, or post-hoc label change is used.
- **Overclaim.** RESULT language treats this audit as causal repair, alpha selection, heldout
  evidence, closed-loop safety, or deployment evidence.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/direction_specificity_report.json`;
- `proof-audit/local_verification.txt`;
- artifact/hash validation summary;
- row-count and target-key consistency summary;
- S1/S2 pass/fail table with every failed bar listed;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running the iteration-34 analyzer.
2. Commit analyzer code and tests before producing the audit report.
3. Run the analyzer once on committed iteration-33 calibration artifacts.
4. Publish `RESULT.md` at full weight whether S0, S1, or S2 fails or passes.
5. A pass authorizes only a separate future pre-registration. It does not authorize heldout replay,
   iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or a safety
   claim.
