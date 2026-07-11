# Iteration 43 - offline object-stream perturbation gate: mild-fragile finding

Status: `OBJECT_PERTURBATION_MILD_FRAGILE`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with one run of the committed
analyzer over the committed iteration-42 exact trace, per the frozen 14-cell grid and the
committed seed `iter43-object-stream-perturbation-v1`. This iteration is entirely offline: no
gcloud, Docker, GPU, model, or closed-loop command ran. The trace SHA256 was verified identical
before and after analysis
(`8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d`), and the analyzer imported
the committed iteration-42 replay implementation rather than reimplementing the rule.

Claim boundary: this is **replay decision-flip sensitivity of the monitor rule, not vehicle
outcomes**. Perturbing the logged object stream is not sensor or camera degradation — the
perturbation is injected between the committed log and the rule, and the planner never sees it.
Replay does not re-render and does not close the loop: when a perturbed replay changes a brake
decision, all subsequent logged frames still come from the unperturbed online run, so the
closed-loop consequences of changed decisions (vehicle position, actor behavior, collisions,
NeuroNCAP score) are not observable offline and are not measured here. No benchmark, UniAD
robustness, selector, deployment, latency, comfort, production-cost, or safety claim is made.

Harness:

- [`analyze_object_perturbation.py`](analyze_object_perturbation.py)
- [`../../tests/test_iter43_object_perturbation.py`](../../tests/test_iter43_object_perturbation.py)

Primary evidence:

- [`proof-perturbation/object_perturbation_report.json`](proof-perturbation/object_perturbation_report.json)
- [`proof-perturbation/analyze_object_perturbation.command.txt`](proof-perturbation/analyze_object_perturbation.command.txt)
- [`proof-perturbation/local_verification.txt`](proof-perturbation/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 static provenance | **PASS**: HYPOTHESIS committed (`733dc3d`) before any iteration-43 code existed; analyzer and tests committed (`14be64a`) before the single run; trace SHA256 matched the frozen value before and after; iteration 42's committed verdict is `TRACE_REPLAY_SUPPORT_PASS`; local `ruff`/`pytest`/`validate_docs` green before the run; no compute leakage |
| S1 zero-strength identity | **PASS**: the analyzer's perturbation-capable input path at strength zero, calling the imported iteration-42 replay functions, reproduced the online decision stream exactly — `0` mismatched frames over `6,474`, totals exactly `1,205` brake frames, `156` releases, `230` intervention episodes over `400` blocks |
| S2 frozen grid, run once | **RUN**: all `14` cells computed once with the committed seed; the duplicated determinism-guard cell (jitter `0.25 m`) produced identical summary hashes; per the frozen bars, **2 of 5 mild cells are FRAGILE** (`jitter:sigma_0p05`, `jitter:sigma_0p10`) → verdict `OBJECT_PERTURBATION_MILD_FRAGILE` |
| S3 claim-boundary audit | **PASS**: this document and the active-doc updates state that this is replay decision-flip sensitivity only — not sensor degradation, not closed-loop, not a benchmark, selector, deployment, or safety claim |
| S4 successor boundary | **HELD**: per the pre-registration, the mild-fragile finding closes the offline line at this trace; any successor requires a fresh pre-registration; no GPU, degradation, heldout, iteration-12, selector, closed-loop, deployment, or safety work is authorized |

The authoritative analyzer report verdict is:

```text
verdict=OBJECT_PERTURBATION_MILD_FRAGILE
mild_fragile_cells=jitter:sigma_0p05, jitter:sigma_0p10
determinism_guard=pass
trace_sha256 unchanged
```

## Per-family results (all vs the online reference: 1,205 brake frames, 230/400 intervention episodes, 170 non-intervention episodes)

Frozen stability bars per cell: retention `>= 219/230`; new interventions `<= 8/170`; median
first-brake delay `<= 1` frame; delay `> 2` frames `<= 10%` of retained; total brake frames in
`[1025, 1385]`.

### Position jitter (Gaussian ego-frame x/y, per axis) — the fragile family

| sigma (m) | retained | new interv. | median delay (frames) | brake frames | brake flips /6,474 | classification |
|---:|---:|---:|---:|---:|---:|---|
| 0.05 (mild) | 218/230 | **17**/170 | 0.0 | 1,275 | 240 | **FRAGILE** (retention 218 < 219; new 17 > 8) |
| 0.10 (mild) | 214/230 | **36**/170 | 0.0 | 1,445 | 484 | **FRAGILE** (retention; new; budget) |
| 0.25 | 216/230 | 79/170 | 0.0 | 1,946 | 1,045 | FRAGILE |
| 0.50 | 221/230 | 111/170 | −1 | 2,837 | 1,934 | FRAGILE |
| 1.00 | 228/230 | 151/170 | −2.0 | 3,996 | 3,043 | FRAGILE |

### Detection dropout (per-object per-frame)

| p | retained | new interv. | median delay | brake frames | brake flips | classification |
|---:|---:|---:|---:|---:|---:|---|
| 0.05 (mild) | 219/230 | 0/170 | 0 | 1,143 | 64 | **STABLE** |
| 0.10 | 222/230 | 0/170 | 0.0 | 1,123 | 94 | STABLE |
| 0.20 | 199/230 | 0/170 | 0 | 965 | 246 | FRAGILE (retention; budget) |

### Score attenuation (multiplicative)

| factor | retained | new interv. | median delay | brake frames | brake flips | classification |
|---:|---:|---:|---:|---:|---:|---|
| 0.90 (mild) | 230/230 | 0/170 | 0.0 | 1,205 | 0 | **STABLE** (bit-identical) |
| 0.80 | 229/230 | 0/170 | 0 | 1,185 | 20 | STABLE |
| 0.60 | 219/230 | 0/170 | 0 | 1,130 | 77 | STABLE |

### Track-identity churn (the registered velocity-noise family)

| p | retained | new interv. | median delay | brake frames | brake flips | classification |
|---:|---:|---:|---:|---:|---:|---|
| 0.05 (mild) | 223/230 | 1/170 | 0 | 1,176 | 39 | **STABLE** |
| 0.10 | 214/230 | 1/170 | 0.0 | 1,106 | 111 | FRAGILE (retention 214 < 219) |
| 0.20 | 195/230 | 1/170 | 0 | 985 | 254 | FRAGILE (retention; budget) |

Logged persistent object ids were present in the trace (`logged_ids_present=true`), so churn
perturbed real identities, not index fallbacks.

## Interpretation

The registered mild-stability hypothesis is refuted, and the refutation is specific: **position
jitter is the fragile axis, and the fragility is dominated by over-firing, not missed
threats.** At sigma `0.05 m` — five centimeters of per-frame position noise — the rule gains
`17` new intervention episodes on episodes where the online monitor never braked (10% of the
non-intervention set, against the frozen 5% bar) and loses `12` of `230` online interventions
(one episode below the frozen retention bar). The dose-response is monotonic and steep on the
false-positive side (`17 → 36 → 79 → 111 → 151` new interventions across the sigma grid) while
retention stays comparatively high, and median first-brake timing actually moves earlier at
heavy jitter. The mechanism is consistent with the rule's construction: object velocity is
derived from cross-frame world-frame positions at the ~2 Hz monitor cadence, so independent
per-frame position noise manufactures spurious velocity, and the CPA/TTC terms sit near their
thresholds on many benign frames.

The other three families pass their mild bars cleanly. Score attenuation at `0.90` is
decision-identical to the online stream (`0` fired or brake flips — any objects it filtered
never carried a decision), and even at
`0.60` the rule stays within all bars — threshold-crossing score noise mostly removes low-score
objects the decisions did not depend on. Dropout and identity churn degrade in the expected
direction (lost interventions, shrinking brake budget) and cross the retention bar only at the
20% and 10-20% levels respectively; neither introduces false interventions.

Stated within scope: on the frozen trace, the released-union rule's decisions are stable in
replay when objects disappear, lose score, or lose identity at mild rates, but not when their
reported positions carry even small independent per-frame noise. Because the online trace is
the planner's own detection output, this says nothing about how noisy UniAD's detections
actually are, and — since replay cannot propagate a changed decision into the world — nothing
about what the extra or lost interventions would do to the closed-loop score. Those questions
remain untested and are not claimable from this result.

## Next Authorized Step

Stop iteration 43. Per the pre-registered S4 boundary, the mild-fragile finding closes the
offline object-stream perturbation line at this trace; any successor — for example a
correlated-noise or smoothed-input variant, or any closed-loop degradation line — requires a
fresh pre-registration. Iteration 43 authorizes no GPU run, sensor/image perturbation,
closed-loop degradation run, iteration-38 calibration, heldout replay, iteration-12 scoring,
selector evaluation, deployment language, or safety claim.
