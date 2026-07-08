# Iteration 30 - full-trainval low-diversity localization result

Status: `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`

## Claim Boundary

This result establishes a diagnostic fact only: on the committed full-trainval fresh-scene split,
the concatenated UniAD motion/planning-bridge representation
`sdc_traj_query_last || sdc_track_query` carries linearly decodable information about the frozen
`eligible_lowdiv` label beyond the registered metadata and ego-plan-kinematic controls.

It does **not** establish:

- that the probe is an explanation;
- that this representation is the cause of low candidate diversity;
- that an activation direction exists;
- that an intervention would improve candidate geometry;
- that iteration-12 dangerous frames are affected;
- that the released selector is compatible with any intervention;
- that closed-loop safety improves;
- that the result transfers to VAD, other UniAD checkpoints, or other planners.

The only authorized next action is a separate causal-intervention pre-registration. No activation
patching, iteration-12 scoring, selector evaluation, GPU run, or closed-loop work is authorized
from this result.

Harness:

- [`HYPOTHESIS.md`](HYPOTHESIS.md)
- [`analyze_localization.py`](analyze_localization.py)

Artifacts:

- [`proof-localization/localization_report.json`](proof-localization/localization_report.json)

## Verdict

| gate | result |
|---|---|
| S0 input hashes | **PASS**: reconstructed iter29 extraction SHA256 and GT SHA256 matched the committed proof table |
| S0 iter29 reports | **PASS**: iter29 S0 integrity report passed; iter29 support atlas passed; strict optional support remained false |
| S0 recomputed counts | **PASS**: `eligible_lowdiv` `127/108/158` and `benign_control` `5084/2344/2245` fit/calibration/heldout, exactly matching iter29 |
| S1 primary internal probe | **PASS**: heldout AUROC `0.950`, AP `0.615`, balanced accuracy `0.867`, recall `0.873`, specificity `0.861` |
| S1 metadata separation | **PASS**: metadata AUROC `0.596`; internal margin `+0.355` >= `0.10` |
| S1 ego-plan-kinematic separation | **PASS**: ego-plan-kinematic AUROC `0.674`; internal margin `+0.276` >= `0.10` |
| S1 shuffled-label sanity | **PASS**: shuffled-label internal AUROC `0.531` and balanced accuracy `0.507`, both inside the frozen null band |
| S2 scene-cluster robustness | **PASS**: 1000/1000 valid resamples; AUROC p05 `0.922`, median `0.951`; balanced-accuracy p05 `0.809` |
| Scope boundary | **PASS**: no new extraction, GPU work, activation direction, intervention, iteration-12 scoring, selector scoring, or closed-loop run was performed |

## S0 Evidence

The analyzer used only the committed iteration-29 proof artifacts. No new model extraction ran.

Hash validation:

| artifact | observed SHA256 | expected SHA256 | result |
|---|---|---|---|
| reconstructed extraction gzip | `390bee5763d576005f5c49441b2ce7eab208d8396a893e329c6f70d5a0c1d03b` | `390bee5763d576005f5c49441b2ce7eab208d8396a893e329c6f70d5a0c1d03b` | PASS |
| GT gzip | `3d2cecd2233cd43cd0ecde0e0bc1d834ad0928a1cbae3cb82756085be8134648` | `3d2cecd2233cd43cd0ecde0e0bc1d834ad0928a1cbae3cb82756085be8134648` | PASS |

Row and label counts:

| quantity | value |
|---|---:|
| extraction rows total | `21,993` |
| non-reset extraction rows | `21,461` |
| joined rows | `21,461` |
| row errors | `{}` |
| ambiguous rows, fit/calibration/heldout | `5,515 / 2,923 / 2,957` |
| `eligible_lowdiv`, fit/calibration/heldout | `127 / 108 / 158` |
| `benign_control`, fit/calibration/heldout | `5,084 / 2,344 / 2,245` |

Heldout `eligible_lowdiv` support remained distributed across 34 scenes; the largest heldout
scene contributed 18/158 rows (`0.114`), below the frozen `0.25` bar inherited from iter29.

## S1 Evidence

Primary probe:

| metric | value | bar |
|---|---:|---:|
| heldout AUROC | `0.950` | `>= 0.800` |
| heldout average precision | `0.615` | `>= 0.200` |
| heldout balanced accuracy | `0.867` | `>= 0.700` |
| heldout recall on `eligible_lowdiv` | `0.873` | `>= 0.600` |
| heldout specificity on `benign_control` | `0.861` | `>= 0.700` |
| calibration threshold | `0.5767576891` | frozen on calibration |
| PCA components | `32` | frozen max |
| constant dimensions dropped | `0` | reported |
| model SHA256 | `0d14c8c458b1c47405fe91bbb3dae452a188eed5fb679633cbf3631d420a9784` | reported |

Controls:

| probe | AUROC | AP | balanced accuracy | interpretation |
|---|---:|---:|---:|---|
| internal tensor | `0.950` | `0.615` | `0.867` | primary diagnostic signal |
| metadata control | `0.596` | `0.088` | `0.505` | does not explain the signal |
| ego-plan-kinematic control | `0.674` | `0.453` | `0.709` | useful but far below internal tensor |
| shuffled-label internal control | `0.531` | `0.070` | `0.507` | within frozen null band |
| candidate-geometry positive control | `1.000` | `1.000` | `0.987` | expected because labels are defined from candidate geometry; not a negative control |

Run note: NumPy emitted one preprocessing warning during the candidate-geometry positive-control
fit because `closest_gap` can be infinite when no object is present. That control is report-only
and not part of the S1 negative-control pass/fail logic. The primary internal tensor and the
registered negative controls used finite feature sets.

## S2 Evidence

Heldout scenes were resampled as clusters exactly 1000 times with seed `30`.

| bootstrap quantity | value | bar |
|---|---:|---:|
| valid resamples | `1000` | `>= 900` |
| skipped single-class resamples | `0` | reported |
| AUROC p05 | `0.922` | `>= 0.700` |
| AUROC median | `0.951` | `>= 0.800` |
| AUROC p95 | `0.972` | reported |
| balanced accuracy p05 | `0.809` | `>= 0.620` |
| balanced accuracy median | `0.872` | reported |
| balanced accuracy p95 | `0.912` | reported |

## Interpretation

Iteration 29 established that the full trainval root contains enough fresh low-diversity hazard
support and benign controls. Iteration 30 shows that the planner's frozen motion/planning-bridge
tensors are not merely carrying scene identity or ego-plan kinematics: a low-capacity linear probe
on those tensors separates `eligible_lowdiv` from `benign_control` on heldout fresh scenes with a
large margin over the registered controls and robust scene-cluster resampling.

The result is still diagnostic. A probe can identify a stable representation-level correlate; it
cannot prove a mechanism. The next valid experiment must pre-register one causal intervention
question, freeze the direction/grid/benign controls before running, and publish a null if the
diagnostic signal cannot causally move downstream candidate geometry without corrupting benign
frames.
