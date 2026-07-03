# Iteration 16 — softer than a stop: the null publishes; the full stop stands

All 120 episodes completed, zero failures. OFF, union, and released comparators are the committed
full-benchmark and iteration-15 evidence (identical deterministic episodes); analysis is
[`analyze_iter16.py`](analyze_iter16.py) on the committed logs, exactly as pre-registered.

**The pre-registered side falsifier fired: side-class collisions 57% > the frozen 45% bar. Per
[`HYPOTHESIS.md`](HYPOTHESIS.md), the null publishes and the full stop stands as the correct
intervention. The released union remains the campaign's best configuration.**

## Result

| pooled (14 scenes, seed-paired) | OFF | union | released | **crawl** |
|---|---:|---:|---:|---:|
| NCAP score | 2.15 | 3.09 | 3.09 | **2.64** |
| safe-progress | 2.372 | 2.203 | 2.448 | **2.544** |
| side collisions | 73% | 37% | 37% | **57%** |
| stationary collisions | 32% | 17% | 17% | 25% |
| frontal score | 1.32 | 1.90 | 1.90 | 1.71 |

- **crawl − released: NCAP −0.450, CI [−0.525, −0.371] — significantly *worse* on the
  benchmark's metric** — while safe-progress is +0.096, CI [+0.033, +0.167], significantly
  *better*. The crawl buys real driving and pays for it in exactly the safety the union earned.
- **crawl − OFF: safe-progress +0.171, CI [−0.036, +0.359] — still includes zero.** The largest
  point estimate of the campaign against the unmonitored planner, and still not a win.

## H16 scorecard (pre-registered)

1. **Safety held: not met.** NCAP 2.64 is 0.45 below the released union's 3.09 (tolerance was
   0.15); side collisions 57% exceed the 45% falsifier bar. Stationary sits exactly at its 25%
   bar with class score 3.99 ≥ OFF's 3.52 (inside the letter of the criterion, at its edge);
   frontal 1.71 ≥ OFF's 1.32 (met).
2. **Deployment verdict vs OFF flips positive (primary): not met** (CI includes zero).
3. **Dominance over released on safe-progress: met in isolation** (+0.096, CI excludes zero) —
   but conditional on criterion 1, which failed. H16 fails overall.

## The mechanism, from the committed evidence

The stop is not merely a speed reduction — it is a **position guarantee**, and the crawl
surrenders it:

- **Side (the falsifier's named mechanism, confirmed in the impact data).** The stop halts the
  ego short of the T-bone's crossing point and the actor passes ahead; the 2 m/s crawl delivers
  the ego *into* the crossing point at contact time. side-0108 collapses from 4.17 / 17%
  (released) to **0.00 / 100%**, with impacts at **4.0–5.1 m/s and zero score** — near the
  scenario's reference severity, i.e. essentially unmitigated hits. side-0278's crawl collisions
  land at 9–10 m/s. These are not low-speed taps; they are arrivals at the wrong place.
- **Stationary (the second falsifier, at its edge).** On 0101 the crawl converts three clean
  stops into taps at **1.9, 1.9, and 3.4 m/s** — the ego's own crawl speed — trading score 5.00
  for 3.22/2.59 while recovering progress (13.0 → 22.1 m). Class collisions land exactly on the
  25% bar.
- **The progress it bought was real.** 411 crawl frames across 69 intervened episodes (38 later
  released, 34 latched to episode end, oscillation 0/120); pooled safe-progress 2.544 is the
  campaign's highest. The trade is genuine — and the pre-registered bars exist precisely to price
  it: the safety cost is larger than the progress gain is worth on the benchmark's own metric.

Together with iteration 11 this completes a two-sided structural result about intervention
softness: **a swerve is unsafe when the trigger is wrong (iteration 11); a crawl is unsafe when
the trigger is right (this iteration). The committed stop is the only intervention in this
campaign that is safe in both cases**, and the released union is its calibrated form.

## What this closes and what it leaves open

The cost-of-stopping floor identified by iteration 15 is now shown *not* to be recoverable by
uniform intervention softness: the deployment gap vs the unmonitored planner (+0.08 released,
+0.17 crawl, both CIs including zero) is the measured price of stopping inside fixed-horizon
episodes. A mechanism that recovers progress without surrendering position would need
threat-class routing (stop for crossings and in-path obstacles, softer only where geometry
proves an overlap-free path) — noted as a possible successor, not built post-hoc.

## Evidence

[`proof/`](proof/): run log, per-frame decision log (crawl/release events per episode), per-run
trajectories/metrics/actors for all 120 episodes, analyzer output. Reproduce:
`python3 analyze_iter16.py <f14 log> <f14 runs> <i15 log> <i15 runs> proof/sentinel-iter16.log <i16 runs> proof/sentinel_i16_crawl.jsonl.gz`.
