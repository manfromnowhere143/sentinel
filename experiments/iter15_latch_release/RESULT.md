# Iteration 15 — threat-cleared release: strictly better than the union, deployment gap vs OFF narrows but stays open

All 120 episodes completed, zero failures. OFF and union comparators are the committed
full-benchmark evidence (identical deterministic episodes); analysis is
[`analyze_iter15.py`](analyze_iter15.py) on the committed logs.

## Result

| pooled (14 scenes, seed-paired) | OFF | union | **released-union** |
|---|---:|---:|---:|
| NCAP score | 2.15 | 3.09 | **3.09** |
| safe-progress | 2.372 | 2.203 | **2.448** |

- **released − union: +0.246 safe-progress, 95% CI [+0.206, +0.293] — excludes zero — at
  *identical* safety** (every per-pair score and collision cell matches the union exactly;
  NCAP delta +0.000). The release mechanism recovered progress and cost nothing.
- **released − OFF: +0.076, CI [−0.122, +0.262] — still includes zero.** H15's third criterion
  (flip the deployment verdict against the unmonitored planner) is **not met**.

## H15 scorecard (pre-registered)

1. **Progress > 60% of OFF on the over-braked pairs: not met.** 0101 recovers 7.2 → 13.0 m (26%
   of OFF), 0108 recovers 7.4 → 18.6 m (44%). Real, insufficient.
2. **Safety held: met exactly.** Released ≡ union on all 20 pairs — 44 releases in 120 episodes,
   none followed by a new collision (the premature-release falsifier did not fire).
3. **Deployment verdict vs OFF flips positive: not met** (CI includes zero).

Falsifiers: oscillation negligible (2/120 episodes with ≥2 release–re-brake cycles); premature
release absent (criterion 2).

## Reading it honestly

The mechanism does exactly what it was designed to do — release when the threat has verifiably
cleared — and it does so *safely*, making **released-union the campaign's best configuration**
(it strictly dominates the union: same benchmark score, significantly more driving). What it
cannot do is refund progress that the episode clock has already spent: after a correct stop, the
ego resumes from a standstill mid-episode, and within NeuroNCAP's fixed horizon only part of the
route can still be covered (0101 recovers 26%, not 60%). The residual deployment gap vs OFF is
therefore not a triggering flaw but a *cost-of-stopping* floor in short fixed-horizon episodes —
closing it would need either earlier release (risking the premature-release failure mode that
did not fire at K=4 but would be pressured at smaller K) or braking less than a full stop
(a softer intervention — a different pre-registrable mechanism).

## Evidence

[`proof/`](proof/): run log, per-frame decision log (brake/release events per episode), per-run
trajectories/metrics/actors, analyzer output. Reproduce:
`python3 analyze_iter15.py <f14 log> <f14 runs> proof/sentinel-iter15.log <i15 runs> proof/sentinel_i15_released.jsonl.gz`.
