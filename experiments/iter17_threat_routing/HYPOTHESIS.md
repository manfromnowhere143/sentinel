# Iteration 17 — threat-class routing: pre-registration

Frozen before the run. The evidence chain that defines this mechanism:

- The power run resolved the deployment question to a **tight null** (released − OFF safe-progress
  −0.03, CI [−0.13, +0.07] at n=20): the stop's safety is bought at approximately zero net
  deployment cost — but not at a *gain*.
- Iteration 16 showed a uniform crawl posts the campaign's highest safe-progress (2.544, +0.096
  over released with CI excluding zero) but surrenders the stop's **position guarantee** exactly
  where geometry makes it load-bearing: the crossing (side 37% → 57%) and in-path (stationary
  taps) classes.
- The prescription, named in that null and in [`docs/NEXT_PHASE.md`](../../docs/NEXT_PHASE.md):
  **keep the stop wherever the threat's path overlaps the ego's plan; crawl only where tracked
  geometry shows no overlap** — the class of firings that costs progress on benign scenes.

## The change (one mechanism: a geometric router between two existing responses)

Triggers, thresholds, the 2.0 m/s crawl re-parameterization (iteration 16), and the K=4
threat-cleared release (iteration 15) are all unchanged. While the latch is active, each frame
routes between the two existing responses by a **path-overlap predicate** computed from the same
tracked kinematics the union already uses:

- For every tracked object in range, project its constant-velocity world path over the plan
  horizon and take the minimum spatial distance to the ego's planned polyline (static objects
  reduce to point-to-polyline distance).
- **Overlap** (min distance < `SENTINEL_ROUTE_MARGIN` = **2.0 m**) → the committed stop. This
  covers the side crossing, the in-path stationary obstacle, and the head-on — every case where
  the stop's position guarantee is the safety mechanism.
- **No overlap** for any tracked object → the crawl. These are firings whose threat never enters
  the ego's corridor (e.g. closing traffic that passes clear) — geometrically the false-alarm
  class where iteration 16 proved motion is worth keeping.

The margin is set at 2.0 m — deliberately wider than the union's 1.5 m CPA margin — so the
predicate errs toward **stopping**: plan waypoints are discrete (metre-scale spacing), and the
router must never rationalize a crawl through sampling gaps. Fixed here; no sweep.

## H17 (pre-registered)

Against the committed comparators (OFF and released from the power evidence — whose first-6
indices are proven identical to the f14/i15 logs; crawl from iteration 16), seed-paired on
identical episodes, one new arm at 6 runs/pair (120 episodes):

1. **Safety held (gate for everything else).** Pooled NCAP within 0.15 of the released union's
   3.09 (n=6 scale); side ≤ 45%, stationary ≤ 25%, frontal class score ≥ OFF's 1.32 — the
   iteration-16 bars, unchanged.
2. **The deployment verdict flips (primary).** Safe-progress (routed − OFF) > 0 with the
   within-pair bootstrap CI excluding zero — the criterion no configuration has met at benchmark
   scope.
3. **Dominance over the current best.** Safe-progress (routed − released) > 0 with CI excluding
   zero.

## Falsifiers, named up front

- **Misrouted crossing.** If the predicate ever classifies a real crossing as no-overlap, the
  crawl re-opens the side case: side > 45% → the null publishes and the released union stands.
- **The predicate is vacuous.** If overlap covers essentially all real firings, the routed arm
  degenerates to the released union (crawl frames ≈ 0 in the decision log; safe-progress delta
  ≈ 0). That null is informative: TTC-only, no-overlap firings are too rare to matter, and the
  deployment null is a floor no router can lift.
- **Frontal severity.** Frontal class score below OFF's 1.32 → reported.
- Decision-log accounting (stop frames vs crawl frames per class) is committed either way, so
  whichever outcome occurs carries its mechanism.

## Protocol

One arm (`routed`: `SENTINEL_ROUTE_MARGIN=2.0`, `SENTINEL_CRAWL_V=2.0`, `SENTINEL_RELEASE_K=4`)
on all 20 pairs × 6 runs. Patch: [`server_patch_union_routed.py`](server_patch_union_routed.py)
(git-checkout base, then the iteration-16 patch plus the router). Analysis:
[`analyze_iter17.py`](analyze_iter17.py) — four-way (OFF / released / crawl / routed) per-pair
and per-class tables, pooled NCAP and safe-progress with seed-paired bootstrap CIs, and the
decision-log routing audit. The run script re-arms the swapfile and the vitals watchdog at
launch (the memory-exhaustion fix and forensics from the power run). Evidence committed under
`proof/`.
