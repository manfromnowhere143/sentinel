# Iteration 23 - S0-hardened causal localization count-floor null

The Stage 1 hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the
pre-registered availability manifest, two-run canary, full non-evaluation extraction, S0 integrity
analysis, and frozen label/minimum-count analysis. The run did not touch iteration-12 frames and
did not run a closed-loop evaluation.

S0 fixed the iteration-22 artifact failure: the canary was deterministic, the full extraction
joined one-to-one on `(scene, sample_index, timestamp_us)`, and every scored row had stable
primary tensor shapes. The next frozen gate then failed: the extracted non-evaluation corpus did
not contain enough collapse-positive or eligible-intervention frames to fit a probe or define an
activation direction under the hypothesis.

Harnesses:

- [`analyze_s0.py`](analyze_s0.py)
- [`analyze_labels.py`](analyze_labels.py)

Metrics:

- [`proof-canary/s0_integrity_report.json`](proof-canary/s0_integrity_report.json)
- [`proof-full-extract/s0_integrity_report.json`](proof-full-extract/s0_integrity_report.json)
- [`proof-full-extract/label_count_report.json`](proof-full-extract/label_count_report.json)

## Verdict

| gate | result |
|---|---|
| Availability manifest | **PASS**: 66 eligible scenes, 39 fit / 13 calibration / 14 heldout, 554 planned heldout keyframes |
| Canary S0 | **PASS**: two clean canary runs, 18 extraction rows and 15 GT rows per run, 15/15 joins per run, identical canonical hashes |
| Full extraction S0 | **PASS**: 2,627 non-reset extraction rows, 2,627 GT rows, 2,627 joined rows, zero duplicate keys, zero error rows |
| Tensor integrity | **PASS**: `sdc_track_query` shape `[1, 256]` and `sdc_traj_query` last-layer shape `[1, 6, 256]` for all 2,627 scored rows |
| Minimum count floors | **FAIL**: collapse-positive frames were 0 in every split; heldout danger positives were 17 below the frozen 30-frame floor; eligible intervention frames were 0 |
| Probe fitting | **NOT RUN**: stopped before S1 |
| Activation direction and intervention grid | **NOT RUN**: no direction was written and no alpha was selected |
| Iteration-12 and closed loop | **NOT RUN**: prohibited by the Stage 1 result |

**Per the frozen gate rule, iteration 23 publishes a data-null and stops. No probe fitting,
activation direction, intervention replay, iteration-12 scoring, selector claim, or closed-loop
run is authorized from this hypothesis.**

## Count-floor result

The full extraction stayed internally valid:

- extraction rows total: 2,693, including reset rows;
- non-reset extraction rows: 2,627;
- GT rows: 2,627;
- joined rows: 2,627;
- rows by split: fit 1,557, calibration 516, heldout 554;
- error row types: none.

The frozen label/count gate failed:

| label | fit | calibration | heldout |
|---|---:|---:|---:|
| `collapse_positive` | 0 | 0 | 0 |
| `high_diversity_control` | 1,499 | 487 | 540 |
| `danger_positive` | 131 | 75 | 17 |
| `safe_control` | 1,189 | 343 | 418 |
| `eligible_intervention_frame` | 0 | 0 | 0 |
| `benign_control_frame` | 1,163 | 331 | 410 |

Frozen failures:

- `collapse_positive.fit=0 < 30`
- `collapse_positive.calibration=0 < 15`
- `eligible_intervention_frame.calibration=0 < 10`
- `collapse_positive.heldout=0 < 30`
- `danger_positive.heldout=17 < 30`
- `eligible_intervention_frame.heldout=0 < 20`

Endpoint-spread summaries explain the collapse-label null: under the registered
`collapse_positive <= 0.5 m` definition, no split contained a collapsed frame. The minimum
endpoint spread was 0.886 m in fit, 0.816 m in calibration, and 1.153 m in heldout. In contrast,
high-diversity controls were abundant under the registered `>= 2.0 m` definition.

## What the null establishes

This result establishes that the hardened S0 procedure works on the committed non-evaluation
corpus: availability support, deterministic canary extraction, full extraction join integrity,
shape stability, gzip splitting, and frozen label counting are all auditable from committed
evidence.

It also establishes that this exact non-evaluation manifest and label definition cannot support
the registered Stage 1 causal-localization test. There are no collapse-positive frames, no
eligible intervention frames, and too few heldout danger positives to run the registered probe and
intervention protocol without moving the bars.

## Claim boundary

This result does **not** show that the motion/planning bridge lacks a causal collapse signal. It
does **not** show that activation interventions cannot affect candidate geometry. It shows only
that under the committed iteration-23 manifest, hook, extraction artifacts, and frozen labels, the
minimum support required to test the registered mechanism was absent.

The only positive methodological claim is S0-hardening: the iteration-22 join failure was repaired
and the repository now contains a reproducible non-evaluation extraction/counting surface for this
question. A scientific successor needs a fresh pre-registration with a revised data-support plan
before any new extraction, probe, intervention, iteration-12 gate, or closed-loop run.

## Evidence

Pre-run artifacts:

- [`availability_manifest.json`](availability_manifest.json)
- [`availability_manifest.sha256`](availability_manifest.sha256)
- [`availability_manifest.command.txt`](availability_manifest.command.txt)
- [`availability_manifest.exclusions.txt`](availability_manifest.exclusions.txt)
- [`server_patch_stage1.py`](server_patch_stage1.py)
- [`feeder_stage1.py`](feeder_stage1.py)
- [`canary_extract_run.sh`](canary_extract_run.sh)
- [`full_extract_run.sh`](full_extract_run.sh)
- [`canonical_jsonl_hash.py`](canonical_jsonl_hash.py)

Canary proof:

- [`proof-canary/sentinel-e23-canary.log`](proof-canary/sentinel-e23-canary.log)
- [`proof-canary/sentinel_e23_canary_a.jsonl.gz`](proof-canary/sentinel_e23_canary_a.jsonl.gz)
- [`proof-canary/sentinel_e23_canary_a_gt.jsonl.gz`](proof-canary/sentinel_e23_canary_a_gt.jsonl.gz)
- [`proof-canary/sentinel_e23_canary_b.jsonl.gz`](proof-canary/sentinel_e23_canary_b.jsonl.gz)
- [`proof-canary/sentinel_e23_canary_b_gt.jsonl.gz`](proof-canary/sentinel_e23_canary_b_gt.jsonl.gz)
- [`proof-canary/s0_integrity_report.json`](proof-canary/s0_integrity_report.json)

Full extraction and label proof:

- [`proof-full-extract/sentinel-e23-extract.log`](proof-full-extract/sentinel-e23-extract.log)
- [`proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-00`](proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-00)
- [`proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-01`](proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-01)
- [`proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz`](proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz)
- [`proof-full-extract/sha256s.txt`](proof-full-extract/sha256s.txt)
- [`proof-full-extract/artifact_reconstruction.txt`](proof-full-extract/artifact_reconstruction.txt)
- [`proof-full-extract/s0_integrity_report.json`](proof-full-extract/s0_integrity_report.json)
- [`proof-full-extract/label_count_report.json`](proof-full-extract/label_count_report.json)

The full extraction log records `FEEDER_DONE mode=full split=all scenes=66 frames=2627` and
`E23_STAGE1_EXTRACT_DONE Mon Jul  6 14:44:16 UTC 2026`.

Reproduce the full S0 analysis after reconstructing the split extraction gzip:

```bash
cd experiments/iter23_s0_hardened_causal_localization/proof-full-extract
cat sentinel_e23_stage1.jsonl.gz.part-00 sentinel_e23_stage1.jsonl.gz.part-01 > sentinel_e23_stage1.jsonl.gz
shasum -a 256 sentinel_e23_stage1.jsonl.gz
gzip -t sentinel_e23_stage1.jsonl.gz
gzip -t sentinel_e23_stage1_gt.jsonl.gz
cd ../../..
python3 experiments/iter23_s0_hardened_causal_localization/analyze_s0.py \
  --extract experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1.jsonl.gz \
  --gt experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz \
  --out-dir experiments/iter23_s0_hardened_causal_localization/proof-full-extract
```

Reproduce the frozen label/count gate directly from the committed split parts:

```bash
python3 experiments/iter23_s0_hardened_causal_localization/analyze_labels.py \
  --extract-part experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-00 \
  --extract-part experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-01 \
  --gt experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz \
  --out-dir experiments/iter23_s0_hardened_causal_localization/proof-full-extract
```
