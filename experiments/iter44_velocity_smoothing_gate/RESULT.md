# Iteration 44 - offline velocity temporal-smoothing repair gate: no-repair null

Status: `VELOCITY_SMOOTHING_NO_REPAIR_NULL`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with one run of the committed
analyzer over the committed iteration-42 exact trace, per the frozen estimator grid (`fd_k2`,
`fd_k3`, `ema_a0p5`, `ema_a0p3`), the frozen V1/V2/V3 bars, and the seed-paired iteration-43
perturbation layer. This iteration is entirely offline: no gcloud, Docker, GPU, model, or
closed-loop command ran. The trace SHA256 was verified identical before and after analysis
(`8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d`). The analyzer imported the
committed iteration-42 replay module and the committed iteration-43 perturbation/classifier
module; the only new code path is the registered velocity estimator, and the S1/S1b gates below
prove it drift-free at neutral parameters.

Claim boundary: this is **offline decision-replay evidence about a registered smoothed-velocity
modification of the monitor rule, not vehicle outcomes**. The released union itself is
unchanged by this iteration. Replay does not re-render and does not close the loop: when the
smoothed rule changes a brake decision — on the clean trace or under perturbation — the
downstream consequences (vehicle position, actor behavior, collisions, NeuroNCAP score) are not
observable offline and are not measured here. V1 "fidelity" is decision-agreement with the
online stream, not proof of equal safety. No sensor/camera degradation, closed-loop, benchmark,
NeuroNCAP-score, selector, deployment, latency, comfort, production-cost, or safety claim is
made.

Harness:

- [`analyze_velocity_smoothing.py`](analyze_velocity_smoothing.py)
- [`../../tests/test_iter44_velocity_smoothing.py`](../../tests/test_iter44_velocity_smoothing.py)

Primary evidence:

- [`proof-smoothing/velocity_smoothing_report.json`](proof-smoothing/velocity_smoothing_report.json)
- [`proof-smoothing/analyze_velocity_smoothing.command.txt`](proof-smoothing/analyze_velocity_smoothing.command.txt)
- [`proof-smoothing/local_verification.txt`](proof-smoothing/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 static provenance | **PASS**: HYPOTHESIS committed alone (`e19a4af`) before any iteration-44 code existed; analyzer and tests committed (`507a757`) before the single run; trace SHA256 matched the frozen value before and after; iteration 42's committed verdict is `TRACE_REPLAY_SUPPORT_PASS` and iteration 43's is `OBJECT_PERTURBATION_MILD_FRAGILE`; local `ruff`/`pytest`/`validate_docs` green before the run; no compute leakage |
| S1 neutral-parameter identity | **PASS**: both neutral cells (`fd_k1`, `ema_a1p0`), replayed through the iteration-44 smoothed implementation and the imported iteration-43 zero-strength input path, reproduced the online stream exactly — `0` mismatched frames over `6,474`, totals exactly `1,205` brake frames, `156` releases, `230` intervention episodes |
| S1b seed-paired equivalence | **PASS**: the neutral `fd_k1` cell under the imported iteration-43 perturbation layer reproduced the committed iteration-43 jitter cells field-for-field (retained `218`, new `17`, brake frames `1,275`, brake flips `240` at `0.05 m`; retained `214`, new `36`, brake frames `1,445`, brake flips `484` at `0.10 m`) |
| S2 frozen grid, run once | **RUN**: all four estimator cells computed once; determinism-guard cell (`fd_k2` × jitter `0.10 m`) repeated with identical summary hashes; **no cell passed V1, V2, or V3** → verdict `VELOCITY_SMOOTHING_NO_REPAIR_NULL` (the `TRADEOFF_NULL` branch was not reached because no cell passed V2) |
| S3 claim-boundary audit | **PASS**: this document and the active-doc updates state that this is offline decision-replay evidence about a modified rule only — the released union is unchanged; not sensor degradation, not closed-loop, not a benchmark, selector, deployment, or safety claim |
| S4 successor boundary | **HELD**: per the pre-registration, the no-repair null closes the temporal-smoothing repair line at these frozen parameters; any successor requires a fresh pre-registration; no GPU, sensor perturbation, closed-loop, iteration-38 calibration, heldout, iteration-12, selector, deployment, or safety work is authorized |

The authoritative analyzer report verdict is:

```text
verdict=VELOCITY_SMOOTHING_NO_REPAIR_NULL
passing_cells=[]  v2_passing_cells=[]
determinism_guard=pass
trace_sha256 unchanged
```

## V1 - baseline fidelity on the unperturbed trace (bars: retention `>= 225/230`, new `<= 4/170`, median delay `<= 1`, delay `> 2` frames `<= 0.05`, brake frames in `[1085, 1325]`)

| estimator | retained | new interv. | median delay (frames) | delay > 2 frac | brake frames | brake flips /6,474 | V1 |
|---|---:|---:|---:|---:|---:|---:|---|
| fd_k2 | **215**/230 | **5**/170 | 0 | 0.009 | 1,155 | 140 | **FAIL** (retention; new) |
| fd_k3 | **213**/230 | **6**/170 | 0 | 0.005 | 1,136 | 181 | **FAIL** (retention; new) |
| ema_a0p5 | **213**/230 | **5**/170 | 0 | 0.009 | 1,137 | 154 | **FAIL** (retention; new) |
| ema_a0p3 | **209**/230 | **5**/170 | 0 | 0.010 | 1,098 | 201 | **FAIL** (retention; new) |

The delay bars — the cost this pre-registration honestly expected smoothing to pay — were NOT
the binding failure: median first-brake delay is `0` everywhere and the `> 2`-frame fraction
stays at 0.5-1.0%. Retained interventions do not fire later; **lost interventions vanish
entirely** (15-21 of the 230 online interventions contain no smoothed brake frame at all), and
the smoothed rule also invents 5-6 interventions the online rule never made, on the clean,
unperturbed trace.

## V2 - jitter repair under the seed-paired iteration-43 cells (iteration-43 bars, reused verbatim)

| cell | raw rule (iter43, committed) | fd_k2 | fd_k3 | ema_a0p5 | ema_a0p3 |
|---|---|---|---|---|---|
| jitter `0.05 m` retained (bar `>= 219`) | 218 | 213 | 211 | 211 | 212 |
| jitter `0.05 m` new interv. (bar `<= 8`) | 17 | 14 | 14 | 11 | 11 |
| jitter `0.10 m` retained (bar `>= 219`) | 214 | 213 | 209 | 208 | 206 |
| jitter `0.10 m` new interv. (bar `<= 8`) | 36 | 18 | 19 | 19 | 20 |
| jitter `0.10 m` brake frames (bar `[1025, 1385]`) | 1,445 | 1,263 | 1,215 | 1,225 | 1,182 |
| classification (both cells) | FRAGILE | FRAGILE | FRAGILE | FRAGILE | FRAGILE |

Smoothing measurably shrinks the over-firing channel — at `0.10 m` new interventions drop from
`36` to `18-20` and the brake budget returns inside its bar — but it never reaches the `<= 8`
bar, and it pays for the reduction with retention that now fails on BOTH jitter cells. In the
dose-response characterization the same pattern holds to the top of the grid (at `1.00 m`, new
interventions `151` raw → `120-125` smoothed).

## V3 - the other families' mild cells (iteration-43 bars)

| cell | raw rule (iter43) | fd_k2 | fd_k3 | ema_a0p5 | ema_a0p3 |
|---|---|---|---|---|---|
| dropout `0.05` retained | 219 (STABLE) | 208 | 206 | 205 | 202 |
| score `0.90` retained | 230 (STABLE, bit-identical) | 215 | 213 | 213 | 209 |
| churn `0.05` retained | 223 (STABLE) | 212 | 210 | 207 | 207 |
| classification (all three) | STABLE | FRAGILE | FRAGILE | FRAGILE | FRAGILE |

The V3 failures are mostly inherited, not interactive: each smoothed cell's score-`0.90` row is
decision-identical to its own unperturbed fidelity row (the same identity iteration 43 found for
the raw rule), and dropout/churn subtract roughly the same handful of episodes from the smoothed
rule as they did from the raw rule — but the smoothed rule starts from `209-215` retained on the
clean trace, already below the `219` bar.

## Interpretation

The registered hypothesis is refuted at all four frozen estimator cells, and the refutation is
informative on both sides of the tradeoff the pre-registration named:

1. **The rule's genuine firings are themselves velocity-transient events.** On the unperturbed
   trace, replacing the one-frame finite difference with any registered smoothed estimator
   erases 15-21 of the 230 online interventions outright (they do not fire late — they never
   fire) and invents 5-6 new ones. The velocity spikes that iteration 43 showed manufacture
   false interventions under jitter are, on this trace, also load-bearing for a meaningful
   fraction of the true ones: at the 2 Hz monitor cadence the CPA/TTC terms cross their
   thresholds on one-frame velocity transients, in both directions.
2. **The jitter fragility is only partly velocity-mediated.** Smoothing halves the
   false-intervention count at `0.10 m` (36 → 18-20) — the spurious-velocity mechanism named in
   iteration 43 is real — but the residual over-firing (still `11-20` vs the `<= 8` bar)
   survives every registered estimator, consistent with a second, velocity-independent noise
   path: the CPA term consumes the jittered positions directly, and no velocity filter touches
   that channel.
3. **Convergence with iteration 18, sharpened.** Iteration 18 showed velocity continuity
   repairs missed stops (the flicker class); iteration 44 shows the mirror image: suppressing
   velocity transients erases genuine firings. Together they bound the same object from both
   sides — the released-union rule's decision boundary sits on the raw estimator's transient
   behavior, so no low-pass filter on this estimator can be the repair. A successor, if
   pursued, must change the estimator class (a tracking filter with an explicit
   measurement-noise model, iteration 18's family) or make the rule terms robust to position
   noise by construction — either needs a fresh pre-registration, and iteration 18's
   overfitting warning applies in full.

Stated within scope: these are decision-replay statements about modified rules on the frozen
trace. Whether any lost or invented intervention would change a vehicle outcome is not
observable offline, and nothing here alters, re-tunes, or re-evaluates the released union,
whose committed benchmark and deployment measurements stand unchanged.

No corrections: no code bug was found after the run; the single run stands as published.

## Next Authorized Step

Stop iteration 44. Per the pre-registered S4 boundary, the no-repair null closes the
velocity temporal-smoothing repair line at these frozen parameters; any successor — an
estimator-class change, a noise-robust rule term, or any closed-loop line — requires a fresh
pre-registration. Iteration 44 authorizes no GPU run, sensor/image perturbation, closed-loop
degradation run, modification of the released union, iteration-38 calibration, heldout replay,
iteration-12 scoring, selector evaluation, deployment language, or safety claim.
