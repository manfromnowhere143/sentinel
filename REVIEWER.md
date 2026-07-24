# Sentinel — reviewer entry point

One page for a reviewer with an hour. Every number below is derivable from evidence committed in
this repository; nothing rests on an external service or an author's recollection. The full
narrative is [README.md](README.md); the campaign history is [docs/CAMPAIGN.md](docs/CAMPAIGN.md).

## What is this?

A runtime safety monitor for a **frozen** UniAD end-to-end driving planner. The monitor is
**label-free** — it reads the planner's own internal signals, predicts the collision the planner
is about to cause, and intervenes with a committed stop. It is measured **closed-loop** on
NeuroNCAP: by whether the car crashes and whether it can still drive, never by open-loop proxy
metrics. The planner is never retrained or modified.

## Strongest verified result — and its boundaries, stated together

On the full official 14-scene NeuroNCAP set at 20 runs per pair (**799 seed-paired episodes**;
one pair is n=19, disclosed in the result), the monitored planner moves the NeuroNCAP score from
**2.12 to 2.91 — delta +0.783, 95% CI [+0.605, +0.928]**, seed-paired bootstrap, CI excludes zero
([experiments/full14_power/RESULT.md](experiments/full14_power/RESULT.md)).

That number does not stand alone; two co-equal boundaries are published at full weight:

- **Deployment-metric tight null.** On safe-progress (safety × route progress — the metric a
  deployment decision would use), the same 799 episodes give **−0.03, 95% CI [−0.13, +0.07]**:
  the benchmark safety gain costs approximately nothing, and buys approximately nothing, on the
  deployment metric.
- **HUGSIM transfer null.** Under frozen parameters on a second simulator, the NeuroNCAP benefit
  does not measurably transfer: mean paired HD-Score delta −0.017, CI [−0.055, +0.026] on
  easy+medium ([iter48](experiments/iter48_hugsim_transfer_gate/RESULT.md)) and −0.0089,
  CI [−0.0438, +0.0203] on hard/extreme
  ([iter49](experiments/iter49_hugsim_hard_tier_gate/RESULT.md)).

## Where is the evidence?

- [experiments/full14_power/proof/](experiments/full14_power/proof/) — the committed raw run
  logs, the per-episode trajectory/metrics tarball, the committed analyzer output, and (one
  directory up) the frozen merge/analyze scripts. The merge enforces a determinism cross-check,
  and the run's H-P0 gate required the first six runs of every pair to reproduce the earlier
  committed evidence exactly. Hash-bound proof manifests exist where a run shipped one, e.g.
  [experiments/iter134_neuroncap_placebo_semantics_execution/proof/SHA256SUMS.txt](experiments/iter134_neuroncap_placebo_semantics_execution/proof/SHA256SUMS.txt).
- [MISSION_STATE.json](MISSION_STATE.json) `claim_state` — the machine-validated claim ledger:
  what is established, on what benchmark, and what is not.
- [experiments/VERIFICATION.md](experiments/VERIFICATION.md) — the independent audit that
  **withdrew** the original pooled headline as statistically invalid and re-established the
  result on honest data. The committed withdrawal is part of the evidence, not a footnote.

## Reproduce the headline on a CPU in under a minute

From `experiments/full14_power/` (verified 2026-07-24; output byte-identical to
[proof/analysis_output.txt](experiments/full14_power/proof/analysis_output.txt)):

```
tar -xzf proof/p14-runs.tar.gz
python3 merge_power14_logs.py merged.log proof/sentinel-power14.log \
    proof/sentinel-power14b-attempt3.log proof/sentinel-power14c.log
python3 analyze_power14.py merged.log . \
    ../full14_benchmark/proof/sentinel-full14.log \
    ../iter15_latch_release/proof/sentinel-iter15.log I15PAIR released
```

The final lines must read `NCAP delta +0.783  CI [+0.605, +0.928]  excludes 0: True` and
`safe-prog  -0.032  CI [-0.127, +0.065]  excludes 0: False`.

## What remains unverified

- **Semantic attribution — `UNRESOLVED`.** Iteration 134's semantics-free placebo returned
  `PLACEBO_HARM_OR_NULL` with a pre-registered dose-realization confound that fired; whether the
  gain needs the monitor's risk semantics is not resolved in either direction
  ([iter134](experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md)).
- **Production readiness — `NOT_ESTABLISHED`.** The released implementation is
  benchmark-integrated, not production-ready.
- **Paper — `ARCHIVED_NOT_SUBMISSION_READY`.** The archived manuscript predates the transfer
  null and the placebo result; see [docs/paper/STATUS.md](docs/paper/STATUS.md).
- **Iteration 135 is pre-registered, not run.** The dose-matched successor exists only as a
  frozen hypothesis and gated tooling
  ([HYPOTHESIS.md](experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md));
  no data, no claim.
