# Iteration 35 - response-heterogeneity audit pre-registration

Frozen after iteration 34 was published as `DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE`, and before any
iteration-35 analyzer, row-stratum table, threshold calculation, proof report, GPU command, gcloud
command, model replay, heldout replay, iteration-12 scoring, selector evaluation, or closed-loop
work.

This is a post-result offline audit over committed iteration-33 and iteration-34 artifacts. It does
not retry iteration 33, rescue iteration 34, select an alpha, or authorize a same-direction
scale-only successor. Its narrow purpose is to decide whether the failed global bridge-centroid
direction failed uniformly, or whether the response is localized to a simple pre-declared row
stratum that could justify a later, different intervention pre-registration.

## Research question

Using only committed calibration artifacts, is the row-level response to the global bridge-centroid
direction structured by baseline geometry strongly enough to support a future conditioned
intervention hypothesis?

Acceptable positive claim if every bar passes:

> The committed iteration-33 calibration artifacts contain one or more pre-declared baseline
> geometry strata where eligible-lowdiv rows respond consistently and benign-control rows remain
> inside the frozen safety envelope, sufficient to justify a separate future pre-registration for a
> conditioned intervention family.

Forbidden claims, even on a pass:

- no claim that iteration 33 or iteration 34 passed;
- no selection of an iteration-33 alpha;
- no heldout, iteration-12, selector, NeuroNCAP, closed-loop, deployment, or safety claim;
- no same-direction scale-only successor claim;
- no claim that the bridge tensor is causally repaired;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets.

## Frozen input artifacts

Iteration 35 may read only committed source and proof artifacts:

- `experiments/iter33_prefix_preserving_bridge_intervention/analyze_intervention.py`;
- `experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/calibration_report.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sha256s.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/unsplit_sha256s.txt`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75.jsonl.gz.part-*`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00.jsonl.gz.part-*`;
- `experiments/iter34_direction_specificity_audit/RESULT.md`;
- `experiments/iter34_direction_specificity_audit/proof-audit/direction_specificity_report.json`.

Iteration 35 must not read iteration-12 frames, selector outcomes, heldout iteration-33 target
rows, uncommitted GPU files, fresh model output, or any external provider output.

## Frozen row and metric definitions

Rows are matched by `(scene, sample_index, timestamp_us)` and must use iteration-33 calibration
target rows only. Context-only prefix rows are audit rows and must not enter pass/fail metrics.

Metrics reuse iteration 33's definitions exactly:

- endpoint spread for the three command candidates;
- endpoint-spread delta from alpha `0.00`;
- best candidate closest gap and best-candidate-gap delta;
- executed final-endpoint displacement;
- danger crossing, low-diversity collapse, and gross-validity predicates.

Iteration 35 may additionally compute the following baseline-only covariates from alpha `0.00`
target rows:

- `object_count = len(objs)`;
- `original_endpoint_spread`;
- `original_best_candidate_gap`;
- `original_executed_gap`;
- scene id and target key, for support accounting only.

The audit may compute deterministic least-squares slopes over the frozen alpha grid for
`endpoint_spread_delta` and `best_candidate_gap_delta`.

## S0 - artifact and row integrity

Before any heterogeneity audit:

- iteration 34 report verdict must be `DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE`;
- iteration 34 S0 must be `true`;
- iteration 33 calibration report verdict must be `CALIBRATION_NULL_NO_USABLE_ALPHA`;
- prefix replay integrity in the iteration-33 calibration report must be `true`;
- all five alphas must be present: `0.00`, `0.25`, `0.50`, `0.75`, `1.00`;
- each alpha must contain exactly `2452` target rows, `108` `eligible_lowdiv` rows, and `2344`
  `benign_control` rows;
- error rows must be `0`;
- gross-validity failures must be `0`;
- target keys must match exactly across all five alpha cells;
- split-gzip model shards must reconstruct into readable gzip streams;
- committed `sha256s.txt` and `unsplit_sha256s.txt` must be recorded in the report.

If any S0 bar fails, publish an infrastructure null and stop.

## S1 - measurable heterogeneity bars

S1 asks whether the failed global direction has enough row-level response spread to justify a
stratum audit at all.

Pass bars:

- at least `20` eligible-lowdiv rows have `endpoint_spread_delta` slope `>= 0.05 m/alpha`;
- at least `20` eligible-lowdiv rows have `endpoint_spread_delta` slope `< 0.00 m/alpha`;
- eligible-lowdiv p75 minus p25 slope width is `>= 0.05 m/alpha`.

If S1 fails, publish a uniform-response null and stop. No conditioned successor may be
recommended.

## S2 - frozen stratum localization bars

S2 evaluates only these pre-declared baseline strata:

- `executed_danger`: `original_executed_gap < 4.5`;
- `executed_not_danger`: `original_executed_gap >= 4.5`;
- `best_candidate_danger`: `original_best_candidate_gap < 4.5`;
- `best_candidate_safe`: `original_best_candidate_gap >= 6.0`;
- `very_low_spread`: `original_endpoint_spread <= 1.0`;
- `near_lowdiv_threshold`: `1.0 < original_endpoint_spread <= 1.5`;
- `single_object`: `object_count == 1`;
- `multi_object`: `object_count >= 2`.

A stratum is actionable only if every bar passes:

- eligible-lowdiv support is `>= 24` rows;
- benign-control support is `>= 100` rows;
- eligible-lowdiv nonnegative endpoint-spread slope fraction is `>= 0.85`;
- eligible-lowdiv median endpoint-spread slope is `>= 0.08 m/alpha`;
- eligible-lowdiv median best-candidate-gap slope is `>= 0.00 m/alpha`;
- eligible-lowdiv alpha `1.00` fraction with endpoint-spread delta `> 0.25 m` is `>= 0.25`;
- benign-control alpha `1.00` median executed endpoint displacement is `<= 0.50 m`;
- benign-control alpha `1.00` p95 executed endpoint displacement is `<= 2.00 m`;
- benign-control alpha `1.00` danger-cross fraction is `<= 0.05`;
- benign-control alpha `1.00` low-diversity-collapse fraction is `<= 0.05`.

If no stratum passes, publish a heterogeneity null. If one or more strata pass, publish a
conditioned-stratum audit pass. A pass authorizes only a separate future pre-registration that
changes the intervention family, target site, or row conditioning. It does not authorize heldout
replay or any live/model run.

## Named falsifiers

- **Artifact drift.** Required committed artifacts are missing, unreadable, or inconsistent with
  recorded hashes.
- **Row mismatch.** Target keys, label counts, or alpha cells differ across the frozen grid.
- **Uniform response.** The row-level slope distribution is too narrow or too one-sided to support
  a heterogeneity claim.
- **No actionable stratum.** No frozen baseline-geometry stratum clears support, target response,
  and benign-control bars.
- **Spread without safety alignment.** Candidate spread increases while best-candidate gap slope is
  negative in the same stratum.
- **Benign harm.** Benign-control rows in a candidate stratum exceed displacement, danger-cross, or
  collapse bars.
- **Leakage.** Any iteration-12 frame, selector outcome, heldout target row, uncommitted model log,
  GPU rerun, altered alpha grid, or post-hoc stratum is used.
- **Overclaim.** RESULT language treats this audit as causal repair, alpha selection, heldout
  evidence, closed-loop safety, deployment evidence, or authorization for same-direction scaling.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/response_heterogeneity_report.json`;
- `proof-audit/local_verification.txt`;
- artifact/hash validation summary;
- S0/S1/S2 pass/fail table with every failed bar listed;
- all frozen stratum summaries, including non-passing strata;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running the iteration-35 analyzer.
2. Commit analyzer code and tests before producing the audit report.
3. Run the analyzer once on committed iteration-33/34 artifacts.
4. Publish `RESULT.md` at full weight whether S0, S1, or S2 fails or passes.
5. A pass authorizes only a separate future pre-registration. It does not authorize heldout replay,
   iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or a safety
   claim.
