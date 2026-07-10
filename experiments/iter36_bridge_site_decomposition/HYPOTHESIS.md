# Iteration 36 - bridge-site decomposition audit pre-registration

Frozen after iteration 35 was published as `HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM`, and before
any iteration-36 analyzer, component-probe run, proof report, target-site recommendation, GPU
command, gcloud command, model replay, heldout replay, iteration-12 scoring, selector evaluation,
or closed-loop work.

Iterations 33-35 close the tested global bridge-centroid direction and simple row conditioning.
Iteration 36 changes the question. It is an offline target-site audit over the committed
iteration-29 extraction artifacts: does the diagnostic low-diversity signal from iteration 30
localize to a smaller pre-declared bridge site strongly enough to justify a separate future
site-specific intervention pre-registration?

This is not an intervention. It does not patch activations, fit a direction for replay, choose an
alpha, use the GPU, or inspect any evaluation-only iteration-12 or closed-loop data.

## Research question

Using only the committed full-trainval extraction rows, does any individual motion/planning bridge
site carry enough out-of-sample `eligible_lowdiv` diagnostic signal to justify a later
site-specific intervention hypothesis?

Acceptable positive claim if every bar passes:

> The committed iteration-29/30 evidence contains at least one pre-declared bridge subsite whose
> diagnostic low-diversity signal is strong, scene-robust, and close enough to the full bridge to
> justify a separate future pre-registration for a site-specific intervention family.

Forbidden claims, even on a pass:

- no claim that iteration 33, 34, or 35 passed;
- no claim that any activation patch would work;
- no direction, alpha, heldout replay, iteration-12 scoring, selector evaluation, NeuroNCAP,
  closed-loop, deployment, or safety claim;
- no same-global-direction scale-only successor claim;
- no row-conditioned successor claim from iteration-35 strata;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets.

## Frozen input artifacts

Iteration 36 may read only committed source and proof artifacts:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/HYPOTHESIS.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/proof-localization/localization_report.json`;
- `experiments/iter35_response_heterogeneity_audit/RESULT.md`;
- `experiments/iter35_response_heterogeneity_audit/proof-audit/response_heterogeneity_report.json`.

Iteration 36 must not read iteration-12 frames, selector outcomes, iteration-33 heldout target rows,
uncommitted GPU files, fresh model output, or external provider output.

## Frozen sites and labels

Rows use the iteration-29 split assignments and labels exactly:

- `eligible_lowdiv`: executed-plan closest gap `< 4.5 m` and command-candidate endpoint spread
  `<= 1.5 m`;
- `benign_control`: executed-plan closest gap `>= 6.0 m` and command-candidate endpoint spread
  `>= 2.0 m`.

Only `eligible_lowdiv` and `benign_control` rows enter probe metrics. Ambiguous rows may be counted
in S0 reports but must not influence pass/fail results.

Expected primary counts:

| label | fit | calibration | heldout |
|---|---:|---:|---:|
| `eligible_lowdiv` | `127` | `108` | `158` |
| `benign_control` | `5084` | `2344` | `2245` |

The bridge vector is frozen as iteration 30 defined it:

```text
flatten(sdc_traj_query_last) || flatten(sdc_track_query)
```

The only non-global sites evaluated are:

- `traj_slot_0`: `sdc_traj_query_last[0:256]`;
- `traj_slot_1`: `sdc_traj_query_last[256:512]`;
- `traj_slot_2`: `sdc_traj_query_last[512:768]`;
- `traj_slot_3`: `sdc_traj_query_last[768:1024]`;
- `traj_slot_4`: `sdc_traj_query_last[1024:1280]`;
- `traj_slot_5`: `sdc_traj_query_last[1280:1536]`;
- `track_query`: `sdc_track_query[0:256]`.

`all_bridge` may be recomputed only as a reference reproduction of iteration 30. It is not an
actionable target site in this audit.

## Frozen probe protocol

Every site uses the same low-capacity protocol:

1. Fit only on the fit split.
2. Standardize with fit-only mean and standard deviation.
3. Drop fit-constant dimensions with standard deviation `<= 1e-12`.
4. PCA on fit rows only, with `n_components = min(32, rank, fit_rows - 1, kept_features)`.
5. Logistic regression with `max_iter=2000`, `class_weight="balanced"`, `solver="lbfgs"`, and
   `random_state=36`.
6. Choose the decision threshold on the calibration split by maximizing balanced accuracy; ties
   choose the larger threshold.
7. Report heldout AUROC, average precision, balanced accuracy, recall on `eligible_lowdiv`, and
   specificity on `benign_control`.
8. Run a scene-cluster bootstrap on heldout rows with seed `36` and `500` resamples for every
   candidate site that clears S1. Report AUROC p05/median and balanced-accuracy p05/median.

## S0 - artifact and count integrity

Before any site audit:

- iteration 30 result status must be `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`;
- iteration 35 result status must be `HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM`;
- iteration-29 extraction and GT hashes must match the committed proof table;
- iteration-29 S0 and label-atlas reports must still pass as published;
- primary counts must exactly match the table above;
- all non-reset primary rows must contain `sdc_traj_query_last` length `1536` and
  `sdc_track_query` length `256`;
- no GPU, gcloud, Docker, heldout replay, iteration-12, selector, or closed-loop command may run.

If any S0 bar fails, publish an infrastructure null and stop.

## S1 - full-bridge reproduction bars

S1 verifies that the analyzer reproduces the iteration-30 diagnostic surface closely enough to make
site comparisons meaningful.

Pass bars for `all_bridge` on heldout:

- AUROC `>= 0.93`;
- average precision `>= 0.55`;
- balanced accuracy `>= 0.83`;
- recall on `eligible_lowdiv` `>= 0.80`;
- specificity on `benign_control` `>= 0.80`.

If S1 fails, publish an analyzer-reproduction null and stop. No target-site claim is authorized.

## S2 - non-global target-site bars

A non-global site is an actionable candidate only if every bar passes:

- heldout AUROC `>= 0.85`;
- heldout average precision `>= 0.30`;
- heldout balanced accuracy `>= 0.78`;
- heldout recall on `eligible_lowdiv` `>= 0.70`;
- heldout specificity on `benign_control` `>= 0.75`;
- AUROC is within `0.08` of the reproduced `all_bridge` AUROC;
- average precision is at least `50%` of the reproduced `all_bridge` average precision;
- scene-cluster bootstrap AUROC p05 `>= 0.75`;
- scene-cluster bootstrap balanced-accuracy p05 `>= 0.65`.

If no non-global site passes, publish a target-site null. If one or more sites pass, publish the
passing sites as candidates for a future pre-registration only. This audit must not choose an
intervention direction, alpha, GPU run, heldout replay, selector evaluation, closed-loop run, or
safety claim.

## Named falsifiers

- **Artifact drift.** Required committed artifacts are missing, unreadable, or inconsistent with
  recorded hashes/counts.
- **Shape drift.** Bridge tensors do not match the frozen `1536 + 256` feature partition.
- **Analyzer mismatch.** The recomputed `all_bridge` probe cannot reproduce the iteration-30
  diagnostic surface above the frozen S1 bars.
- **No localized target site.** No pre-declared non-global site clears all S2 diagnostic and
  scene-robustness bars.
- **Global-only signal.** The full bridge is strong, but every smaller site falls more than the
  allowed AUROC/AP margin from the full bridge.
- **Leakage.** Any iteration-12 frame, selector outcome, iteration-33 heldout row, uncommitted
  model log, GPU rerun, altered site slice, or post-hoc site is used.
- **Overclaim.** RESULT language treats this audit as causal repair, activation-patch evidence,
  alpha selection, heldout intervention evidence, closed-loop safety, or deployment evidence.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/bridge_site_decomposition_report.json`;
- `proof-audit/local_verification.txt`;
- artifact/hash/count validation summary;
- full-bridge reproduction metrics;
- every frozen site summary, including non-passing sites;
- scene-bootstrap summaries for S1-passing candidate sites;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running the iteration-36 analyzer.
2. Commit analyzer code and tests before producing the audit report.
3. Run the analyzer once on committed iteration-29/30/35 artifacts.
4. Publish `RESULT.md` at full weight whether S0, S1, or S2 fails or passes.
5. A pass authorizes only a separate future pre-registration. It does not authorize heldout replay,
   iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or a safety
   claim.
