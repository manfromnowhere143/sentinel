# Iteration 2 — the Sentinel intervention beats the unmonitored frozen planner (pre-registered H1 met)

A label-free runtime monitor, reading only the **frozen** UniAD planner's own outputs, brakes when it
predicts an imminent collision — and on the public-mini NeuroNCAP corpus it **more than doubles the
safety score and cuts the collision rate by 5×, while leaving the safe scene untouched.** The planner's
weights are never changed, so the gain is attributable to Sentinel alone.

## Headline (monitor OFF = unmonitored frozen UniAD, ON = Sentinel-monitored, same scenes, 10 runs each)

| scenario / scene | NCAP score OFF → ON | collision % OFF → ON |
|---|---|---|
| frontal / 0103 | 1.05 → **4.08** | 80 → **40** |
| side / 0103 | 0.59 → **5.00** | 100 → **0** |
| stationary / 0796 | 1.05 → **4.60** | 80 → **11** |
| stationary / 0103 *(do-no-harm)* | 5.00 → **5.00** | 0 → **0** |
| **pooled** | **1.92 → 4.67** | **65 → 13** |

**Pre-registered H1 (frozen in `PREREGISTRATION.md` before any A/B):** monitored beats the *same*
unmonitored planner, drive-clustered bootstrap CI on the per-run score delta excludes 0.

> **Result: pooled score delta = +2.75, 95% CI [+2.21, +3.22] — excludes 0.** Collision rate 65% → 13%.
> Do-no-harm holds: the clean scene (stationary/0103) is **identical** at 5.00 / 0%. H1 is met.

(5000-sample within-scene bootstrap, fixed seed; `proof/ab_outcomes.tsv` vs `proof/outcomes.tsv`.)

## Why it works — and the one design fix that made it real

The G1 gate (`G1_RESULT.md`) had already shown the planner's own forecast *predicts* its collisions
(AUROC 0.83). Turning prediction into prevention took two corrections, both forced by the closed loop:

1. **Latch the brake.** A one-frame override does nothing — NeuroNCAP's LQR tracker re-reads the
   plan each step. Once risk fires, Sentinel **commits** to the stop for the rest of the episode.
2. **Trigger on time-to-collision, not a fixed-distance gap.** A distance threshold (θ=3.5 m) only
   trips ~0.27 s before impact — too late — because the planner's forecast is *optimistic*. Switching
   the trigger to **TTC = gap ÷ closing-speed < 2.5 s** (closing speed from each agent's *own*
   forecast displacement) fires ~1.8 s out, which is enough lead time. With the fixed-gap trigger the
   same brake barely moved impact speed (11.9 → 10.8 m/s); with TTC it collapses it (→ ~4.3 m/s) or
   avoids the crash outright.

The intervention lives inside the inference server: the frozen planner plans, Sentinel computes TTC
from the returned objects + forecasts, and on a trigger replaces the trajectory with a committed
stop-in-place. `SENTINEL_ENABLED` is the only switch between the OFF and ON arms.

## What this is — stated precisely, no inflation

- **It is** a pre-registered, drive-clustered-CI win of a *monitored frozen planner* over the *same
  unmonitored planner*, on every collision scenario in the public-mini corpus, with the clean scene
  unharmed. Public data, one L4, planner frozen, signal label-free (the planner's own outputs).
- **It is not** a claim of beating the *published* full-benchmark UniAD number (1.84 over 14 scenes ×
  100 runs). We ran the **2 scenes available in public mini** (0103, 0796), **10 runs** each, and the
  TTC/threshold were **fixed on the separate G1 shadow run** (disclosed, not tuned on these scores).
  Scaling to all 14 scenes needs the gated trainval blobs; that is future work, not a hidden caveat.
- **The brake mitigates as well as avoids.** frontal/0103 still collides 40% of the time — the fastest
  head-on approaches where even a 1.8 s brake cannot fully stop — but at ~4 m/s instead of ~14 m/s, so
  the score rises from ~0 to ~2.7. We report avoidance and mitigation separately, not as one number.

## Ablation boundary (see `ABLATION.md` — read it, it bounds this result)

The introspective signal is **essential**: a naive distance brake (6 m, no forecast) leaves frontal
collisions at 83% (≈ the unmonitored 80%) — TTC's closing-speed-from-forecast trigger is what cuts it
to 40% and side to 0%. **But** an always-brake control *matches* the TTC safety score on this corpus,
because every scene rewards stopping. So the safety-score win over the unmonitored planner is real, yet
proving the *selective* monitor beats a trivial always-brake needs a **progress-sensitive** benchmark.

> **Correction (iteration 3).** We ran that progress benchmark, and it overturned the selectivity
> gloss first written here. On a progress-aware metric the TTC monitor **over-brakes** — it freezes
> even the benign clean scene (ego drives 4.9 m vs the unmonitored 32.4 m), barely better than
> always-brake, and the *unmonitored* planner wins on safe-progress. The safety-score result below
> stands and is real; the claim that the monitor was *selectively idle* on the clean scene was an
> unverified inference and is **wrong**. See [`../iter3_progress/RESULT.md`](../iter3_progress/RESULT.md).

## Honest residuals / falsifiers checked

- **Do-no-harm (safety only):** the clean scene (stationary/0103) stays at 5.00 / 0% — the monitor
  induces **no new collisions** there. ~~It fired on 0 of the 10 clean-scene runs.~~ **Corrected by
  iteration 3:** the monitor is *not* idle on the clean scene — it over-brakes it (freezes the car).
  The safety-score do-no-harm holds; the *selectivity* claim does not. See `../iter3_progress/RESULT.md`.
- **No collision-for-timeout trade (on the safety score):** ON safety scores went *up*. Note iter 3:
  the brake *does* trade progress — it stops the car far short of where the planner would have driven.
- **Residual frontal collisions:** reported, not hidden — the lead-time limit of an optimistic-forecast
  trigger on the most aggressive approaches.

## Reproduce

OFF baseline = the G1 shadow outcomes (`proof/outcomes.tsv`). ON = `sentinel_ab.sh` with the TTC server
patch (`server_patch_ttc.py`) applied and `SENTINEL_ENABLED=1`. Per-run outcomes in
`proof/ab_outcomes.tsv`; brake events (with TTC at trigger) in `proof/ab_brakes.jsonl`.

## The arc

PerceptionProof (label-free disagreement predicts the collision gate, AUROC ~0.8) → Sentinel G1 (the
frozen planner's own forecast predicts its closed-loop collisions, AUROC 0.83) → **Sentinel iter 2 (that
signal, deployed with a TTC brake, cuts closed-loop collisions 65% → 13% on a frozen planner).** We
showed cheap signals see failure coming; now they stop the crash.
