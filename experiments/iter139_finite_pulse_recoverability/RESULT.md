# Iteration 139: finite pulse recovery null

Status: **null / FINITE_PULSE_RECOVERY_NULL**, 2026-10-09.
The complete, valid six-cell intervention grid produced **0/6 useful recoveries** on the
disclosed development case `scene-0411-hard-00`. Every branch collided. This closes the frozen
experiment; its grid, outcomes, tolerances and stopping rules were unchanged after evidence.

One pulse, starting at 2 seconds and lasting 1 second, was collision-free at the reference
hazard time of 6.5 seconds, with exactly the reference progress, but collided at 7.0 seconds.
Its half-second delay fails the registered recovery endpoint. A check ending at the reference
collision time would have overstated the benefit.

## Registered outcomes

The two references each contain 26 actions, collide at **T=6.5 simulated seconds**, and have
raw route completion **R=0.11557062998555366**. Their driving traces are byte-identical;
complete numerical controller records match and the independent Decimal comparison agrees.
The trace SHA-256 is `df49e87e5eb0f1ba23ea787f5925a1fb1d2ea812b8c2a48bf4462628f3bfb7aa`.
The retrospective recount also finds the reference frame bodies and footer equal to Iter138's
reference, excluding the changed schema/identity header. This is evidence on this configuration.

The frozen progress bar is **R-0.05=0.06557062998555366** at T. Useful recovery also requires
collision-free route completion within the original horizon, the complete pulse and resumption,
and at most two seconds of override. All six pulses and their resumptions were fully observed;
none of these branches was censored, invalid or unobserved. They all failed through actual collision.

| Arm | Onset / duration (s) | First collision (s) | Raw progress at T | Final raw progress | Assigned / realized / changed plan frames | Collision-free through T | Useful recovery |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pulse_0_1` | 0 / 1 | 6.5 | 0.101752 | 0.101752 | 4 / 4 / 4 | no | no |
| `pulse_0_2` | 0 / 2 | 6.0 | null | 0.057157 | 8 / 8 / 8 | no | no |
| `pulse_2_1` | 2 / 1 | 7.0 | 0.115571 | 0.116827 | 4 / 4 / 4 | yes | no |
| `pulse_2_2` | 2 / 2 | 6.0 | null | 0.062810 | 8 / 8 / 8 | no | no |
| `pulse_4_1` | 4 / 1 | 6.5 | 0.114314 | 0.114314 | 4 / 4 / 4 | no | no |
| `pulse_4_2` | 4 / 2 | 6.5 | 0.104265 | 0.104265 | 8 / 8 / 5 | no | no |

Progress is rounded here; exact values are in [grid_analysis.json](proof/grid_analysis.json).
`null` at T means the episode already collided at 6.0 seconds and never observed T; it does not
mean zero progress. Early collision is an observed failure of collision-free recovery.
The late two-second pulse overrode eight frames but changed the incoming plan on only five;
the other three incoming plans were already zero. Assigned override duration is not a measure
of additional actuation dose. Realized quantities do not adjust the primary comparison.

## Controller execution and independent verification

All **206/206 live controller calls** passed replay using the separately imported original
upstream controller source in the bound environment. All **206 stopping reasons were convergence**;
there were zero iteration-limit, deadline or input-failure stops. Numerical mode has no wall
deadline stop; zero deadline stops cannot establish timely execution. Actual incoming plan dtype
was float32 and was preserved. All six pre-action prefixes and onset observations, states and
typed incoming plans matched the reference under the preregistered rules. The independent Decimal
implementation agreed on pulse timing, prefixes and outcomes.

The exact source, runtime, image and data binding is in [EXECUTION_BINDING.md](EXECUTION_BINDING.md).
Raw bytes were committed before each interpretation and before the next episode. The
[commit ledger](proof/episode_commit_ledger.json) and per-arm reports in `proof/analysis/` retain
the order. The [stdlib recount](proof/orchestration/i139_recount.py.txt) independently recomputed
all retained timing quantiles, counts, stop reasons, terminal outcomes, monitor request counts,
raw trace hashes and override/changed-frame counts; [its output](proof/arithmetic_recount.stdout)
matched all eight reports. Original-source replay and Decimal validation are separate
implementations, not independent humans or independent scientific replications.

## Wall time, separate from simulation and stopping

Nearest-rank quantiles below include all calls, including startup; units are milliseconds.
With 24–28 calls per episode, p99 equals the observed maximum. These are dependent observations
from one case, not tail-latency guarantees or a randomized timing comparison between arms.

Complete controller adapter call:

| Arm | Calls | p50 ms | p95 ms | p99 = max ms | >50 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| `reference_a` | 26 | 57.120 | 86.256 | 92.143 | 19/26 |
| `reference_b` | 26 | 56.546 | 84.466 | 90.592 | 20/26 |
| `pulse_0_1` | 26 | 58.626 | 87.580 | 89.115 | 24/26 |
| `pulse_0_2` | 24 | 55.341 | 102.258 | 107.591 | 17/24 |
| `pulse_2_1` | 28 | 56.559 | 74.308 | 78.914 | 24/28 |
| `pulse_2_2` | 24 | 59.349 | 84.852 | 104.040 | 20/24 |
| `pulse_4_1` | 26 | 61.024 | 81.608 | 88.451 | 22/26 |
| `pulse_4_2` | 26 | 57.475 | 69.564 | 73.540 | 20/26 |

Full solver:

| Arm | p50 ms | p95 ms | p99 = max ms | >50 ms |
| --- | ---: | ---: | ---: | ---: |
| `reference_a` | 53.142 | 80.097 | 84.355 | 16/26 |
| `reference_b` | 52.537 | 80.663 | 83.083 | 17/26 |
| `pulse_0_1` | 55.372 | 81.395 | 84.722 | 20/26 |
| `pulse_0_2` | 51.472 | 96.115 | 100.517 | 13/24 |
| `pulse_2_1` | 52.762 | 70.132 | 75.178 | 21/28 |
| `pulse_2_2` | 55.677 | 80.995 | 97.556 | 18/24 |
| `pulse_4_1` | 57.107 | 77.312 | 84.760 | 17/26 |
| `pulse_4_2` | 53.564 | 65.845 | 69.655 | 15/26 |

Internal adapter and client roundtrip:

| Arm | Internal adapter p50 / p95 / p99=max ms | Client roundtrip p50 / p95 / p99=max ms |
| --- | ---: | ---: |
| `reference_a` | 57.112 / 86.246 / 92.125 | 1737.576 / 2241.044 / 32559.860 |
| `reference_b` | 56.537 / 84.454 / 90.577 | 1716.221 / 2097.094 / 15284.799 |
| `pulse_0_1` | 58.612 / 87.566 / 89.103 | 1740.842 / 2109.275 / 15465.067 |
| `pulse_0_2` | 55.332 / 102.246 / 107.575 | 1713.410 / 2090.302 / 15688.418 |
| `pulse_2_1` | 56.550 / 74.294 / 78.902 | 1698.310 / 2127.652 / 15540.369 |
| `pulse_2_2` | 59.338 / 84.843 / 104.028 | 1694.054 / 2145.310 / 15284.750 |
| `pulse_4_1` | 61.011 / 81.593 / 88.442 | 1757.093 / 2124.966 / 15612.819 |
| `pulse_4_2` | 57.461 / 69.556 / 73.527 | 1773.413 / 2146.416 / 15673.578 |

In total, **166/206 complete calls** and **137/206 full solver calls** exceeded 50 ms. The
threshold comes from the configured engineering budget; it is not a validated vehicle deadline.
Client roundtrip includes transport, serialization/deserialization and client work, not isolated
model inference. Timing boundaries retain the Iter138 contract. The simulator advances fixed
0.25-second steps independently of wall time; stale-action consequences were not evaluated.
Deterministic numerical output and poor wall-time behavior coexist in this evidence.

## Descriptive actuation check after the grid

This additional [raw recount](proof/actuation_recount.stdout) was written after all eight live
episodes. It is descriptive and does not amend any endpoint or establish a causal mechanism.
Every pulse has negative acceleration on each assigned frame and a lower speed at pulse end.
All 206 velocity updates satisfy the logged `v_after = v_before + acc * dt` with zero floating
residual in this recount. The zero plan also produces steering-rate commands; it is not a direct
brake pedal or a guaranteed stopping maneuver.

| Arm | Speed at pulse start (m/s) | Speed at pulse end (m/s) | Speed at collision (m/s) | Released-monitor brake requests |
| --- | ---: | ---: | ---: | ---: |
| `pulse_0_1` | 1.000000 | 0.192279 | 0.249152 | 6 |
| `pulse_0_2` | 1.000000 | 0.036971 | 0.234319 | 7 |
| `pulse_2_1` | 3.097647 | 0.698562 | 0.248177 | 6 |
| `pulse_2_2` | 3.097647 | 0.133545 | 0.126693 | 6 |
| `pulse_4_1` | 2.708423 | 0.559821 | 0.325464 | 4 |
| `pulse_4_2` | 2.708423 | 0.105387 | 0.045725 | 5 |

Each reference had eight released-monitor brake requests and speed 0.10744942905458194 m/s at
collision. Each of the eight raw driver logs contains the environment's `Collision with foreground`
line. This supports distinguishing actual environment collision from evaluator warnings about
planned trajectories, but it does not identify an actor or prove a contact mechanism. Low ego
speed alone does not establish low relative impact speed or low severity. The next design must
check contact geometry and other-actor response before selecting a different intervention family.

## Source and measurement corrections preserved

Before execution, source review found that raw route completion can reach 10/9; the new schema
accepts this range without clipping and has overshoot/invalid-range fixtures. Earlier Iter136/138
observations did not exceed one and remain unchanged. The evaluator's `nc` aggregates checks on
planned trajectories; it is not the probability of an executed episode avoiding collision.
Its `rc` is a clipped maximum over frames. This experiment uses actual `env.step` collision flags
and raw progress at the specified time and at termination. See [DESIGN_REVIEW.md](DESIGN_REVIEW.md)
and the [bound evaluator source](proof/score_calculator.py.txt).

## Validation and infrastructure closure

**179 distinct focused tests passed:** 41 Iter139, 32 Iter138, 51 Iter137 and 55 Iter136.
The 37 core Iter139 tests passed from extracted committed source; the four provider-readiness
known-bads passed from the exact executed packet. Local tests used ambient Python 3.14 /
NumPy 2.4.2. The bound host used Python 3.11.10 / NumPy 1.26.4 and single-thread pools; its
generated-driver stub exercised 12 controller calls, pulse/resumption and route overshoot before
live execution. The [fixture result](proof/runtime_integration_after_capacity.stdout) is synthetic,
not an observed driving success. Collected fixture bytes are retained in `proof/supplemental/`.
Implementation/test Ruff passed. Full, frozen-environment and hosted CI are not claimed.

Initial lint failures and the test invocation that inherited incompatible home-directory pytest
arguments are retained with their successful corrections. The first provider start failed from
zone stockout. A local orchestration error attempted two dependent SSH connections; both failed
at IAP before a successful host connection. The [pre-live correction](PRE_EXECUTION_INFRASTRUCTURE_CORRECTION.md)
records the mistake and the provider-readiness guard added and tested before live execution.
The second start succeeded within the frozen allowance. There were no initialized-episode retries,
replacement machines, package/image installations or post-evidence source changes.

Postflight matched all **471 bound files**, with no owned episode processes, containers or GPU
applications and **109.731 GiB** free. The owned shutdown timer was cancelled,
the stop operation completed, and [provider readback](proof/final_provider_state.stdout) confirms
**TERMINATED**. There were two start requests and one stop request. The provider start/stop
interval was **1802.635 seconds**; first start-operation
insertion through completed shutdown was **1953.422 seconds**,
inside the original 180-minute budget, which was not reset. Billed cost was not measured.
[Resource accounting](proof/resource_accounting.json) uses same-provider timestamps.

The repository retains **88 raw collected episode files**, with their byte hashes checked.
Another **650 scene/image/video files** remain on the stopped host's persistent disk,
with retained path/size/hash inventories; their content bytes are not in Git. Raw controller and
state replay is narrower than a fully self-contained simulator/assets distribution.

| Arm | Raw evidence commit, before interpretation | Supervisor wall seconds |
| --- | --- | ---: |
| `reference_a` | `f86b94ca85bbf30ba0aa5419efec98401a3ecf02` | 133.447 |
| `reference_b` | `c3fc81aff90efffee80997b268392083be211063` | 114.034 |
| `pulse_0_1` | `c0facd8a09d33bbb1581082ac89f447faa6a6d00` | 114.602 |
| `pulse_0_2` | `5c4917a0bb6d1ed4a78fd62c4a9a4436ed3f727a` | 109.345 |
| `pulse_2_1` | `c7b4eb7d06c952491c8780227f1d14e480cdcf64` | 119.839 |
| `pulse_2_2` | `ae1df261da801e5c8d986b2b2122446db88b5369` | 108.705 |
| `pulse_4_1` | `5c7f706e645154cff7c184616e6db4dbe0d2a8ec` | 116.121 |
| `pulse_4_2` | `2714d5b6fef90453b8fefd7ff34a26dd2ccd05c0` | 116.476 |

Preregistration: `0b1ab853c78ad89db102483e590d7349c8998210`.
Executed source: `6991f8f48559ce8f6539a05a8b0eef749639eb26`.
Candidate branch: `research/iter139-finite-pulse`, local and unpushed. Canonical master remains
F17. Iter135 remains deferred; Iter136/137/138 evidence and unrelated WIP are preserved.

## Decision and claim boundary

Close this six-cell experiment as null. No tested pulse achieved recovery; no inference follows
about untested actions, continuous timing, other scenes, physical inevitability or the value of
additional information. These dependent development trajectories do not support a population
rate or confidence interval. The [next step](NEXT_STEP.md) is a bounded action/contact diagnostic
on the new traces, followed by a separately frozen choice of action family or case family.
Information ablations still require a demonstrated useful intervention opportunity and a strong
responsive comparator. No safety, real-time operation, transfer, industrial superiority or
state-of-the-art result is established by this experiment.
