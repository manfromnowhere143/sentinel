# Iteration 29 - full-trainval risk-support atlas result

Status: `SUPPORT_PASS_SUCCESSOR_PREREG_AUTHORIZED`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested as a full-trainval
risk-support atlas on the official staged root `/datasets/nuscenes-full`. This iteration used
only the committed iteration-28 availability manifest, extracted frozen UniAD planner tensors and
planner outputs once, and computed the pre-registered fresh-scene support labels.

This iteration did not fit probes, write activation directions, replay interventions, touch
iteration-12 outcomes, score selectors, run NeuroNCAP, or run closed loop.

Harness:

- [`import_iter28_manifest.py`](import_iter28_manifest.py)
- [`server_patch_stage1.py`](server_patch_stage1.py)
- [`feeder_stage1.py`](feeder_stage1.py)
- [`canary_extract_run.sh`](canary_extract_run.sh)
- [`full_extract_run.sh`](full_extract_run.sh)
- [`analyze_s0.py`](analyze_s0.py)
- [`analyze_atlas.py`](analyze_atlas.py)

Artifacts:

- [`proof-canary/s0_integrity_report.json`](proof-canary/s0_integrity_report.json)
- [`proof-full-extract/sentinel-e29-extract.log`](proof-full-extract/sentinel-e29-extract.log)
- [`proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-aa`](proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-aa)
  through
  [`proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-ao`](proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-ao)
- [`proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`](proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz)
- [`proof-full-extract/s0_integrity_report.json`](proof-full-extract/s0_integrity_report.json)
- [`proof-full-extract/label_atlas_report.json`](proof-full-extract/label_atlas_report.json)
- [`proof-full-extract/sha256s.txt`](proof-full-extract/sha256s.txt)

The full extraction gzip was `1,240,350,622` bytes, so it is committed as 15 split parts under
the pre-registered `>90 MB` artifact rule. Reconstruct it with:

```bash
cat proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-* > /tmp/sentinel_e29_stage1.jsonl.gz
gzip -t /tmp/sentinel_e29_stage1.jsonl.gz
```

The reconstruction check passed locally after splitting. The SHA256 of the unsplit gzip before
splitting was:

```text
390bee5763d576005f5c49441b2ce7eab208d8396a893e329c6f70d5a0c1d03b
```

## Verdict

| gate | result |
|---|---|
| S0a manifest import | **PASS**: source manifest SHA256 matched iter28; imported `266/133/133` fit/calibration/heldout scenes and `10,726/5,375/5,360` keyframes; known-data contamination `0`; mixed-root keyframes `0`; metadata identifier fields `0` |
| S0b two-run canary | **PASS**: both canary runs joined `30/30` rows, had zero error rows, identical canonical SHA256 values, and stable tensor shapes/dtypes |
| S0c full extraction | **PASS**: `21,461/21,461` non-reset extraction rows joined GT one-to-one; duplicate extract keys `0`; duplicate GT keys `0`; error row types `{}` |
| S0c tensor stability | **PASS**: `sdc_traj_query_last_shape=[1,6,256]`, `sdc_track_query_shape=[1,256]`, both `torch.float32`, for all `21,461` joined rows |
| S1 count floors | **PASS**: no count-floor failures |
| S1 distribution bars | **PASS**: no distribution failures |
| Optional strict-collapse support | **FAIL**: strict-collapse counts are insufficient in every split |
| Scope boundary | **PASS**: no probe, activation direction, intervention, iteration-12 scoring, selector scoring, or closed-loop run was performed |

**Iteration 29 passes the low-diversity risk-support gate.** The fresh post-firewall trainval pool
contains enough `danger_4p5` / `low_diversity_1p5` support and benign controls to justify a
separate successor pre-registration for causal localization or planner repair.

It does **not** pass the optional strict-collapse note. A successor may use the term
`low_diversity` for this support, but must not call it strict planner collapse based on this
iteration.

## S0 Evidence

Full extraction completed on `sentinel-gpu` with:

```text
FEEDER_DONE mode=full split=all scenes=532 frames=21461
E29_STAGE1_EXTRACT_DONE Wed Jul  8 14:36:11 UTC 2026
```

S0 integrity report:

| quantity | value |
|---|---:|
| extraction rows total | `21,993` |
| non-reset extraction rows | `21,461` |
| GT rows | `21,461` |
| joined rows | `21,461` |
| duplicate extraction keys | `0` |
| duplicate GT keys | `0` |
| error row types | `{}` |
| fit rows | `10,726` |
| calibration rows | `5,375` |
| heldout rows | `5,360` |

Canonical row hashes:

| artifact | canonical rows | SHA256 |
|---|---:|---|
| extraction rows | `21,993` | `878d31e594c1d106b6d862e0c03f3d7377e0d28bb69817ab5f60de86de06b639` |
| GT rows | `21,461` | `a6dc71c79eabc98bf6b55a7ebb1c1afcce235d463cd607575c95415eeba45731` |

## S1 Support Evidence

Primary count-floor labels:

| label | fit | calibration | heldout |
|---|---:|---:|---:|
| `danger_4p5` | `3,038` | `1,654` | `1,670` |
| `safe_6p0` | `5,331` | `2,534` | `2,409` |
| `low_diversity_1p5` | `265` | `194` | `268` |
| `high_diversity_2p0` | `9,826` | `4,723` | `4,661` |
| `eligible_lowdiv` | `127` | `108` | `158` |
| `benign_control` | `5,084` | `2,344` | `2,245` |

Count floors all passed:

| split | required `eligible_lowdiv` | observed | required `benign_control` | observed |
|---|---:|---:|---:|---:|
| fit | `80` | `127` | `160` | `5,084` |
| calibration | `25` | `108` | `60` | `2,344` |
| heldout | `25` | `158` | `60` | `2,245` |

Distribution bars all passed:

| split | `eligible_lowdiv` frames | contributing scenes | minimum scenes | max scene fraction |
|---|---:|---:|---:|---:|
| fit | `127` | `51` | `15` | `0.150` |
| calibration | `108` | `25` | `5` | `0.185` |
| heldout | `158` | `34` | `5` | `0.114` |

The heldout max-scene fraction was below the frozen `0.25` bar.

## Strict-Collapse Null

The stricter labels are reported at full weight:

| label | fit | calibration | heldout |
|---|---:|---:|---:|
| `strict_collapse_0p5` | `0` | `1` | `4` |
| `eligible_strict` | `0` | `0` | `1` |

Strict optional failures:

- `strict_collapse_0p5.fit=0 < 120`
- `eligible_strict.fit=0 < 40`
- `strict_collapse_0p5.calibration=1 < 40`
- `eligible_strict.calibration=0 < 12`
- `strict_collapse_0p5.heldout=4 < 40`
- `eligible_strict.heldout=1 < 12`

This null does not fail S1. It limits successor language: future work may not describe this
support as strict collapse unless a new pre-registration proves those stricter counts.

## Claim Boundary

This result establishes only that the newly staged official trainval root contains enough fresh
low-diversity hazard and benign-control support for a later, separately pre-registered
causal-localization or planner-repair experiment.

It does **not** establish:

- that a probe can localize a mechanism;
- that an activation direction exists;
- that an intervention improves candidate geometry;
- that iteration-12 dangerous frames are affected;
- that the released selector is compatible with any intervention;
- that closed-loop safety improves;
- that `low_diversity_1p5` is strict planner collapse.

The next valid action is a fresh `HYPOTHESIS.md` that freezes one successor question, its split
discipline, tensors or model-side intervention surface, numeric bars, named falsifiers, and a hard
no-closed-loop-until-gate rule.
