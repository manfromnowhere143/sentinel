# Iteration 22, Stage 1 - causal localization stopped at S0

The Stage 1 hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested only through the
pre-registered baseline extraction and integrity analysis. The run used the committed
non-evaluation split manifest and extraction patch. It did not touch iteration-12 frames and did
not run a closed-loop evaluation.

Harness: [`analyze_stage1_baseline.py`](analyze_stage1_baseline.py). Metrics:
[`proof-baseline/stage1_baseline_metrics.json`](proof-baseline/stage1_baseline_metrics.json).

## Verdict

| bar | result |
|---|---|
| **S0** split, extraction, and integrity | **FAIL**: 1,507 non-reset extraction rows and 1,507 GT rows were produced, but 1,507 rows failed the committed timestamp join (`missing_gt`) |
| **S0** heldout data support | **FAIL**: GT rows by split were fit 1,428, calibration 79, heldout 0; heldout minimum-count floors could not be evaluated or met |
| **S1** low-capacity collapse localization | **NOT RUN**: stopped before probe fitting |
| **S2** frozen causal movement | **NOT RUN**: no activation direction was written and no calibration grid ran |
| **S3** benign control | **NOT RUN**: no intervention replay ran |

**Per the frozen gate rule, Stage 1 publishes a data-null and stops. No probe fitting, activation
direction, calibration grid, heldout intervention, iteration-12 scoring, selector claim, or
closed-loop run is authorized from this hypothesis.**

## What the null establishes

This is an integrity/data-support null, not a mechanistic finding about UniAD. The launched Stage
1 artifact pair cannot support the registered causal-localization test because the extracted rows
were timestamped at second precision while the GT sidecar kept microsecond timestamps:

- extraction timestamp summary: 1,507 rows, 761 unique timestamps, min 1,531,883,530, max
  1,533,153,766;
- GT timestamp summary: 1,507 rows, 1,507 unique timestamps, min 1,531,883,530,449,377, max
  1,533,153,766,547,527.

Independently, the frozen manifest/staged-data combination produced zero heldout GT frames. Even
with a corrected join key, the heldout count floors frozen in the hypothesis could not pass from
this extraction. The correct outcome is therefore to publish the null and stop, not to move
scenes, retune labels, or run a rescue extraction under the same hypothesis.

## Claim boundary

This result does **not** show that the motion/planning bridge lacks a collapse signal. It does
**not** show that an activation direction cannot change downstream candidate geometry. It shows
only that this registered Stage 1 run failed before label scoring because the committed artifacts
did not satisfy S0 integrity and heldout data-support requirements.

Any successor must be a fresh pre-registration. At minimum it must freeze a manifest whose scenes
are known to have local frame support, freeze an auditable GT/extraction join key before launch,
and preserve the rule that iteration-12 frames remain untouched until a later separately
registered gate.

## Evidence

Extraction proof:

- [`proof-extract/sentinel-e22-extract.log`](proof-extract/sentinel-e22-extract.log)
- [`proof-extract/sentinel_e22_stage1.jsonl.gz`](proof-extract/sentinel_e22_stage1.jsonl.gz)
- [`proof-extract/sentinel_e22_stage1_gt.jsonl.gz`](proof-extract/sentinel_e22_stage1_gt.jsonl.gz)

The extraction log records `FEEDER_DONE split=all scenes=90 frames=1507` and
`E22_STAGE1_EXTRACT_DONE Mon Jul  6 11:27:07 UTC 2026`.

Reproduce the S0 analysis:

```bash
python3 experiments/iter22_causal_planner_interpretability/analyze_stage1_baseline.py \
  --extract experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1.jsonl.gz \
  --gt experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1_gt.jsonl.gz \
  --out-dir experiments/iter22_causal_planner_interpretability/proof-baseline
```

Analysis note: the analyzer originally stopped before probes on the same null, but its first
metrics did not expose the error type. A reporting-only patch added timestamp summaries, GT split
coverage, and `error_row_types`; it did not change any threshold, move any split, fit any probe, or
authorize any intervention.
