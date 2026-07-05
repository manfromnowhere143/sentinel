# Iteration 17 — threat-class routing: the safety gate fails; the released union stands — and the deployment flip is shown to be achievable

All 120 episodes completed, zero failures. Comparators are committed evidence (identical
deterministic episodes); analysis is [`analyze_iter17.py`](analyze_iter17.py), exactly as
pre-registered in [`HYPOTHESIS.md`](HYPOTHESIS.md).

**Verdict: H17 fails on criterion 1, the gate.** Side-class collisions reach **47%** (frozen
bar: 45%) and the benchmark score gives up **0.170** against a 0.15 tolerance. Per the
pre-registration, the null publishes and **the released union remains the best configuration.**

## Result

| pooled (14 scenes, seed-paired, n=6) | OFF | released | crawl | **routed** |
|---|---:|---:|---:|---:|
| NCAP score | 2.15 | **3.09** | 2.64 | 2.92 |
| safe-progress | 2.372 | 2.448 | 2.544 | **2.598** |
| side collisions | 73% | **37%** | 57% | 47% |
| stationary collisions | 32% | 17% | 25% | 20% |
| frontal score | 1.32 | 1.90 | 1.71 | **1.97** |

- **routed − OFF: safe-progress +0.226, CI [+0.004, +0.421] — excludes zero.** The first
  configuration in this campaign whose deployment-metric advantage over the unmonitored planner
  excludes zero at benchmark scope. Under a failed safety gate this is an observation, not a
  claim — but it establishes that the deployment flip is *achievable* by routing, which no prior
  arm had shown.
- **routed − released: NCAP −0.170, CI [−0.317, −0.011]** (a real benchmark cost) **·
  safe-progress +0.150, CI [+0.045, +0.255]** (a real deployment gain). The trade is genuine and
  the pre-registered bars price it: not acceptable.
- **routed − crawl: NCAP +0.281, CI [+0.172, +0.408]** — the router recovers most of the crawl's
  safety loss (side 57% → 47%, stationary 25% → 20%) while keeping more progress than the
  released union. The position-guarantee logic works *where the predicate routes correctly*.

## H17 scorecard (pre-registered)

1. **Safety held: NOT MET.** NCAP delta −0.170 exceeds the 0.15 tolerance; side 47% exceeds the
   45% falsifier bar. (Stationary 20% ≤ 25% met; frontal 1.97 ≥ 1.32 met — the best frontal
   score of any arm in the campaign.)
2. **Deployment flip vs OFF (primary): met in isolation** (+0.226, CI excludes zero) — voided as
   a claim by the failed gate.
3. **Dominance over released: met in isolation** (+0.150, CI excludes zero) — likewise voided.

## The failure, localized precisely

The falsifier breach is carried by **one pair: side-0108** (released 4.17 / 17% → routed
1.67 / 67%). The other four side pairs match the released union almost exactly — including
side-0103 at a perfect 5.00 / 0%. The decision log shows the router crawling in frames where
0108's crossing actor should have mandated the stop: the constant-velocity path projection
misses that crossing's geometry (a turning or late-tracked actor projects clear of the planned
corridor while genuinely converging on it). One scene's geometry defeats the predicate; the
pre-registered bar correctly converts that single localized failure into a campaign-level null.

Routing audit: 69/120 episodes intervened; 170 stop frames vs 240 crawl frames (59% crawl
share); 57 releases; oscillation 4/120.

## What this establishes

1. **The released union survives its fourth challenger** (evasions, crawl, and now routing) and
   remains the best configuration.
2. **The deployment flip is achievable** — routing produced the campaign's first
   CI-positive-vs-OFF deployment result at benchmark scope. The open problem is now narrower
   and sharper: a routing predicate whose misclassification rate on crossings is low enough to
   keep side ≤ 45%. Candidate successors (named, not built post-hoc): route on the *firing
   term* (CPA-fired → always stop; TTC-only → crawl); require N consecutive no-overlap frames
   before the first crawl frame; overlap on observed positions over a window rather than a
   constant-velocity projection.
3. The frontal observation (routed 1.97, the campaign's best) suggests continued slow motion
   marginally softens head-on outcomes relative to the full stop — consistent with iteration
   16's frontal cells, and folded into the frontal-ceiling picture rather than claimed.

## Evidence

[`proof/`](proof/): run log, per-frame decision log (stop/crawl/release records with the
overlap distance per frame), per-run trajectories/metrics/actors for all 120 episodes, analyzer
output. Reproduce: `python3 analyze_iter17.py <f14 log> <f14 runs> <i15 log> <i15 runs>
<i16 log> <i16 runs> proof/sentinel-iter17.log <i17 runs> proof/sentinel_i17_routed.jsonl.gz`.
