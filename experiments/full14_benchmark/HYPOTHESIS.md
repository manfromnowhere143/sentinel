# Full 14-scene benchmark — pre-registration

Frozen before the run. All prior results live on the 2 public-mini scenes; this is the first
evaluation on the complete official NeuroNCAP scene set (the release arrays: 10 stationary, 5
frontal, 5 side scene-scenario pairs across 14 unique scenes), with the 12 non-mini scenes'
sensor data pulled from nuScenes' public AWS mirror and the release NeuRAD checkpoints.

## Protocol

OFF vs union (exact iteration-8 configuration, the committed patch), 6 runs per scene-scenario
pair per arm — 240 episodes. Deterministic run indices make the arms seed-paired. Metrics:
per-scenario-class NCAP score and collision rate (the published benchmark's units), plus
safe-progress with a within-scene bootstrap CI (this repo's deployment metric).

## Hypotheses

- **H14-1 (baseline reproduction):** unmonitored UniAD's pooled NCAP score lands near the
  published 1.84 (single-preprint number, never independently reproduced — landing within ±0.4
  at n=6/pair would be the first independent confirmation; a larger gap is reported as-is).
- **H14-2 (the win generalizes):** the union improves pooled NCAP score and safe-progress over
  OFF across the full set, CI excluding zero — the pre-registered campaign bar, now at benchmark
  scope.
- **H14-3 (per-class structure holds):** side-impact reduction strongest, frontal mitigation
  (score up, rate ≈ flat), stationary ≈ unchanged where OFF is already clean.

## Falsifiers, named up front

- The mini-scene results could be scene-lucky: if the union's side-impact reduction does not
  appear on the four unseen side scenes, the "side case solved" claim shrinks to scene-0103 and
  is corrected everywhere it appears.
- New-scene rendering or perception quality may differ; a broken pair (crashes, non-scoring) is
  excluded ONLY with the exclusion logged in the result — no silent drops.
- 0103 pairs re-run here under v1.0-trainval metadata: if their outcomes drift from the committed
  v20 numbers (which ran under mini metadata), that is a validity flag on cross-version
  comparability and gets investigated before any pooled claim.
