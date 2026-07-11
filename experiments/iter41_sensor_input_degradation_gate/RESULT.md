# Iteration 41 - monitor-input degradation gate infrastructure null

Status: `DEGRADATION_GATE_INFRASTRUCTURE_NULL`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed offline analyzer.
The audit used only committed full14/power logs, the committed p14 run archive, and the committed
iteration-40 timing/cost report. It did not run gcloud, Docker, a GPU, UniAD, NeuroNCAP, image
perturbations, iteration-38 calibration, heldout replay, selector evaluation, or closed-loop work.

Claim boundary: this is an **offline replay-support null**, not a sensor-degradation robustness
result. The frozen evidence can count logged decisions, but it cannot support the registered exact
world-frame replay because many logged monitor-frame timestamps have no exact committed
`p14-best` ego-pose timestamp. No score-threshold, range-limit, dropout, or jitter perturbation
bar was reached.

Harness:

- [`analyze_degradation_gate.py`](analyze_degradation_gate.py)
- [`../../tests/test_iter41_degradation_gate.py`](../../tests/test_iter41_degradation_gate.py)

Primary evidence:

- [`proof-audit/degradation_gate_report.json`](proof-audit/degradation_gate_report.json)
- [`proof-audit/analyze_degradation_gate.command.txt`](proof-audit/analyze_degradation_gate.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 artifact and vanilla replay integrity | **FAIL**: frozen paths were present and committed; full14/power H-P0 and iteration-40 verdict were intact; reconstructed best-arm log counts matched the frozen row envelope (`8,235` rows, `400` resets, `7,835` non-reset rows, `1,205` brake-key rows). But exact timestamp lookup into committed `p14-best` ego poses failed for `1,388/6,474` timestamped frame rows (`21.44%`) across `400/400` episodes. Vanilla replay was therefore skipped. |
| S1 safety-retention bars | **SKIPPED**: S0 failed before perturbations. |
| S2 selectivity/no-extra-cost bars | **SKIPPED**: S0 failed before perturbations. |
| S3 lead-time stability bars | **SKIPPED**: S0 failed before perturbations. |
| S4 successor authorization boundary | **SKIPPED**: no pass-state successor authorization exists. |

The authoritative audit report verdict is:

```text
verdict=DEGRADATION_GATE_INFRASTRUCTURE_NULL
s0_pass=false
s0_failure=pose_timestamp_exact_miss=1388/6474
```

The pre-registration inherited iteration 40's row-count shorthand for the best decision log. The
analyzer records the exact split: `7,835` non-reset rows comprise `6,474` timestamped monitor frame
rows, `1,205` brake rows, and `156` release rows.

## Falsifier

The registered offline replay rule required ego plan points and object positions to be transformed
from logged ego frame into world frame through the same episode timestamp's committed `p14-best`
`ego_poses.json` pose. That exact-join condition fails.

Representative first misses from the proof report:

| scenario | run | frame | logged timestamp | nearest pose timestamp | delta |
|---|---:|---:|---:|---:|---:|
| `stationary-0099` | `0` | `0` | `1533151417647268` | `1533151419197895` | `1,550,627 us` |
| `stationary-0099` | `0` | `1` | `1533151418147694` | `1533151419197895` | `1,050,201 us` |
| `stationary-0099` | `0` | `2` | `1533151418697895` | `1533151419197895` | `500,000 us` |
| `stationary-0099` | `1` | `0` | `1533151417647268` | `1533151419197895` | `1,550,627 us` |
| `stationary-0099` | `1` | `1` | `1533151418147694` | `1533151419197895` | `1,050,201 us` |

There were no missing pose files. The blocker is timestamp support, not archive absence.

## Interpretation

This is the useful kind of failed reproduction. The released-union online patch used `data.ego2world`
at inference time. The committed decision log stores the monitor inputs and timestamps, and the
committed run archive stores ego poses, but those two committed sources are not aligned exactly
enough to replay the world-frame monitor under the frozen Iter41 rule.

The scientifically correct action is to stop. Interpolating poses, snapping to nearest poses, or
switching to ego-frame replay after seeing this failure would change the registered replay rule and
turn an artifact-support null into a post-hoc robustness story. Iteration 41 therefore says only:

- the current committed full14/power evidence is insufficient for exact world-frame object-stream
  degradation replay;
- no offline object-stream degradation robustness result exists;
- no degraded-sensor GPU, camera perturbation, closed-loop, selector, deployment, or safety claim
  is authorized from Iter41.

## Next Authorized Step

Stop iteration 41.

The defensible successor, if this line is still worth pursuing, is a fresh replay-support
pre-registration before any new result: either log the exact `ego2world` transform alongside the
monitor frame rows in a new closed-loop run, or pre-register a pose-interpolation/snap rule and
then test vanilla replay before any perturbation bars. That would be an artifact-support remedy,
not a continuation of this result.

Otherwise, move to another external-validity falsifier such as adversarial perturbations,
independent planner transfer, unseen scenario families, calibration stability, or deployment
trade-offs. In every case, prefer the narrower claim that survives hostile scrutiny.
