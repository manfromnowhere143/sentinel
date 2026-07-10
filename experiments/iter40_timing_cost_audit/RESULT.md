# Iteration 40 - timing and intervention-cost audit pass

Status: `TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed offline analyzer.
The audit used only committed full14/power and verification evidence. It did not run gcloud,
Docker, a GPU, UniAD, NeuroNCAP, sensor degradation, adversarial perturbations, iteration-38
calibration, heldout replay, selector evaluation, or closed-loop work.

Claim boundary: this is a **simulation decision-log timing and intervention-budget audit**. It
does not measure wall-clock inference latency, passenger comfort, production compute cost,
certification readiness, real-world deployment, sensor robustness, adversarial robustness, or a new
safety result.

Harness:

- [`analyze_timing_cost.py`](analyze_timing_cost.py)

Primary evidence:

- [`proof-audit/timing_cost_report.json`](proof-audit/timing_cost_report.json)
- [`proof-audit/analyze_timing_cost.command.txt`](proof-audit/analyze_timing_cost.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 artifact and join integrity | **PASS**: H-P0 was PASS; `p14-runs.tar.gz` had `400` best metrics and `399` OFF metrics across `20` scenario pairs; the known `side-0921` OFF `n=19/20` exception was detected; reconstructed `sentinel_p14_best.jsonl.gz` had `400` reset blocks, `7,835` non-reset frames, and `1,205` brake-key rows; the messy OFF decision-log reset stream had `484` resets and was not used as completed episodes |
| S1 intervention-cost coverage | **PASS**: all `400/400` best completed episodes had decision-block, metric, and ego-distance joins; all `20/20` scenario pairs and all three classes were summarized |
| S2 lead-time coverage | **PASS**: `61` measured lead-time episodes across `stationary`, `frontal`, and `side`, above the frozen `20` episode / two-class bar; all intervention episodes were assigned an exclusion status |
| S3 unsupported latency/deployment boundary | **PASS**: the report states simulation timestamp timing only, brake-frame budget only, full14/power safe-progress tight null, and untested sensor/adversarial/deployment trade-offs |

The audit report verdict is:

```text
verdict=TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE
s0_pass=true
s1_pass=true
s2_pass=true
s3_pass=true
```

## Intervention Cost

Across the committed full14/power best arm:

| scope | episodes | intervention episodes | brake frames | ego distance | brake frames / km | median frames / intervention | p95 frames / intervention |
|---|---:|---:|---:|---:|---:|---:|---:|
| all best episodes | `400` | `230` | `1,205` | `10,789.9 m` | `111.68` | `4` | `9` |
| stationary | `200` | `74` | `416` | `6,350.4 m` | `65.51` | `4` | `9` |
| frontal | `100` | `92` | `475` | `2,817.2 m` | `168.61` | `5` | `9` |
| side | `100` | `64` | `314` | `1,622.3 m` | `193.55` | `4` | `8` |

Grouped by the OFF arm's committed collision outcome:

| OFF outcome | episodes | intervention episodes | brake frames | ego distance | brake frames / km |
|---|---:|---:|---:|---:|---:|
| OFF non-collision | `190` | `96` | `533` | `5,605.1 m` | `95.09` |
| OFF collision | `209` | `133` | `668` | `5,178.6 m` | `128.99` |
| OFF run missing | `1` | `1` | `4` | `6.2 m` | `644.48` |

Interpretation: the monitor is not free. Even on OFF-noncollision episodes, the released union
spends `533` brake frames over `5.61 km`. That remains compatible with the full14/power
safe-progress tight null, but it is not a production comfort or cost result.

## Lead Time

Lead time was measured only where the OFF arm had a reconstructable `2.0 m` center-distance
counterfactual contact crossing and the best arm had at least one brake frame:

| quantity | value |
|---|---:|
| measured lead-time episodes | `61` |
| measured classes | `frontal`, `side`, `stationary` |
| median lead time | `1.30 s` |
| p05 / p95 lead time | `0.40 s` / `3.50 s` |
| min / max lead time | `-0.30 s` / `6.350206 s` |
| fraction negative | `0.04918` |

All lead-time statuses:

| status | episodes |
|---|---:|
| measured | `61` |
| no OFF contact crossing | `168` |
| no best brake | `170` |
| missing OFF run | `1` |

Negative lead time is not clipped. It means the first logged brake came after the reconstructed
OFF-arm contact crossing under this offline timing definition.

## Interpretation

Iteration 40 upgrades the safety-case timing/cost story from a mini-scene summary to a
full14/power audit over the committed released-union evidence. It is useful precisely because it
keeps the uncomfortable parts:

- full14/power still has a deployment-metric tight null, not a deployment win;
- the monitor spends nontrivial brake budget even on OFF-noncollision episodes;
- lead-time support is reconstructable for `61` intervention episodes, not for every run;
- the timing axis is simulator timestamp lead time, not wall-clock runtime latency.

## Next Authorized Step

Stop iteration 40. The active story may now cite full14/power simulation intervention budget and
reconstructable lead-time coverage with the boundaries above.

This result does not authorize iteration-38 calibration, sensor-degradation runs, adversarial
runs, selector evaluation, closed-loop work, deployment-readiness language, production-cost
language, or safety claims. The next defensibility-first pre-registration should move to a still
untested external-validity axis, with sensor/input degradation now the strongest candidate.
