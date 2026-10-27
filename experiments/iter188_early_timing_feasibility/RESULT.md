# Iter188 — two early endpoints cannot satisfy the final checkpoint

27 October 2026. **The registered early-exclusion hypothesis is supported.**
Two of all 255 retained Iter187 native endpoints necessarily complete the route
on their next step, before the required frame-32 checkpoint. Both are extra
branches on the lost left bend, at frames 19 and 21. The latter is that run's
returned endpoint. These are source-model timing exclusions, not claims of
physical unavoidability or a causal explanation of the entire search loss.

| Case | All endpoints | Timing-excluded | Known completion suffix | Unknown |
|---|---:|---:|---:|---:|
| Left bend | 87 | 2 | 3 | 82 |
| Right bend | 49 | 0 | 8 | 41 |
| Left chicane | 36 | 0 | 10 | 26 |
| Right chicane | 83 | 0 | 13 | 70 |
| **Total** | **255** | **2** | **34** | **219** |

The population includes four roots and all 251 registered primary/extra nodes,
without selecting on frame or outcome. Shared states remain separate records,
not independent observations. The 34 positive records match complete retained
suffixes exactly in case, absolute frame and every state coordinate; three are
already-completed endpoints with zero-length suffixes. Their prior collision
admission is reused. The 219 unknowns are neither certified feasible nor excluded.

![Endpoint timing evidence by case and frame](proof/timing-feasibility.png)

[Figure data](proof/figure-data.json) retain every endpoint identity. The old
eligibility window starts at frame 24; both new exclusions occur earlier.

## Why these two endpoints are excluded

The source updates speed, then position along the old heading, then heading.
The audit encloses the next position for the entire allowed acceleration range,
including the existing numerical tolerance. Over that enclosing rectangle, a
completing route vertex is strictly nearer than every noncompleting vertex,
with a conservative numerical margin. Every admissible next action therefore
triggers completion at frame 20 or 22, before frame 32. Steering cannot change
that step's position in this particular update order.

| Node / sequence token | Parent | Frame / simulated time | Speed | Origin |
|---|---:|---:|---:|---|
| 18 / 50 | 14 | 19 / 4.75 s | 5.0 m/s | extra |
| 50 / 168 | 22 | 21 / 5.25 s | 3.5 m/s | extra; returned endpoint |

The producer uses outward binary64 intervals and exact rational affine minima.
The separate checker reconstructs the primitive rounding enclosures and checks
squared-distance differences at all four corners. The frozen
[numerical derivation](MATHEMATICS.md) states the domain, comparison error and
libm assumptions; this is not machine-checked compiler verification. Ignoring
some joint-motion and scene constraints enlarges the bound's reachable set.
Excluding that superset is valid; overlap alone cannot prove a feasible action.

## Counterchecks and limits

Independent replay accepts **555 certificate records and 9,925 scalar probes**.
All **300 actual successful transitions from nine admitted Iter178/183/187 paths**
remain unexcluded. Fixed scalar actions respect coupled control, speed, steering,
yaw and lateral bounds. At 238 endpoints, a physically admissible probe defeats
the premise that every next action completes prematurely. Such a step does not
establish collision freedom, timely full completion or controller performance.
The probe grid is a countercheck, not an exhaustive continuous-control search.

No planner changed, integrated search ran, background collision was queried,
simulator driving episode ran, or provider spending occurred. The integrated
result remains **3/4**. Source comparison stays closed. The next test is a
prospectively qualified application of this necessary rule before selecting
primary or extra endpoints, with unchanged budgets and explicit gains and losses.
Success on today's retained paths does not guarantee preservation of a changed
tree's successes. [Next decision](DECISION.md).

## Chronology, identities and validation

The complete endpoint/control population was committed before new bound evaluation
at `e1defe45cf0122ffb2f39a7d0bcff9175b48dbd3`. Qualified source and protocol were
frozen at `818d06cd4f96f364b7f7e0b1df80eeb7448ccddd`. The sole raw acquisition
was committed at `45b36644d6eda7d1d4cd48899f4b95b3f156e42d` before independent
admission at `6cd2c7c2`.

**147 focused tests pass with zero skips, including 90 new controls.** Initial
fixture/inventory and test-binding failures, their corrections, and a preflight
refusal before acquisition are retained in [qualification](QUALIFICATION.json).
No scientific result was acquired before the final qualified freeze.

The producer took 3.891 seconds / 137,347,072 bytes peak RSS; the checker took
12.520 seconds / 152,764,416 bytes. Both exited and were reaped within their
separate 300-second / 1-GiB envelopes. The observed environment is macOS Python
3.14.2, not a hermetic runtime or a real-time vehicle system. Hosted software CI
and publication are observed separately from this scientific admission. These
exposed development cases provide no population or competitive-superiority claim.

[Protocol](PROTOCOL.md) · [admission](proof/admission.json) · [state](STATE.json) ·
[primary research](RESEARCH.md) · [implementation](bound.py) · [separate checker](bound_check.py).
