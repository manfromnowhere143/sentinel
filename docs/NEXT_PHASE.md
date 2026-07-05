# Next phase — candidate lines after the power run

Written while the 20-run power measurement executes; nothing here presumes its outcome. Each line
is stated with the evidence that motivates it, the mechanism, the pre-registerable bar, and the
cost. Ordering is by expected knowledge-per-GPU-hour; the decision rules at the bottom say what
runs when.

## Line 1 — a diversity-trained candidate head under the runtime selector

**Motivation (measured, twice):** iterations 12 and 14 established that frozen planners hold no
plan B precisely when it matters — UniAD's command-conditioned candidates collapse from 14 m of
benign diversity to 4 cm under threat (0/37 escapes); VAD's native modes retain only partial
diversity (21% escapes, below the 30% viability bar). The runtime selector mechanism is sound
(introspection sees the danger); the missing ingredient is a candidate set that stays diverse
under threat. To the verified corpus ([RELATED_WORK.md](RELATED_WORK.md)) no published system
trains a diversity-preserving candidate head for a *frozen* planner and selects among its outputs
with a label-free runtime risk score.

**Mechanism:** a small trajectory head (MLP/GRU over the frozen planner's BEV features, weights
of the planner untouched) trained on nuScenes train split with an explicit diversity objective
(winner-takes-all regression plus an inter-mode repulsion term), producing K candidates per
frame. At runtime, the union's risk score ranks the candidates; the committed-stop floor remains
(a candidate is executed only if its risk clears the plan's; otherwise the released stop fires).
Safe on false alarms by construction — the iteration-11 asymmetry is respected because every
candidate is trained on in-distribution driving.

**Pre-registerable bar (frozen before any training):** under-threat escape rate > 30% on the
iteration-12 frame corpus (the exact bar the planner's own candidates failed); then closed-loop:
frontal collision rate below the released-union's at equal selectivity (clean-scene cells within
noise of OFF), benchmark score not below the released-union's.

**Cost:** the first line requiring training — feature-extraction pipeline plus a small head;
single-L4 feasible; the largest engineering lift of the three.

> **Line 2 outcome (2026-07-05):** run as iteration 17 — the pre-registered safety gate failed
> on one misrouted crossing (side 47% vs the 45% bar) and the released union stands, while the
> voided secondary criterion recorded the campaign's first deployment CI excluding zero vs the
> unmonitored planner (+0.226, [+0.004, +0.421]). All three named successor predicates were
> then **refuted offline** on the committed log (no-op; dead trade; non-separable) — the
> routing line closes for per-frame geometric predicates, and the deployment flip now routes
> through **tracking quality**, elevating Line 3 (motivated independently by iteration 14) to
> the front of the GPU queue alongside Line 1's offline stage.
> [`../experiments/iter17_threat_routing/RESULT.md`](../experiments/iter17_threat_routing/RESULT.md).

## Line 2 — threat-class routing (named by iteration 16's null)

**Motivation (measured):** the crawl null proved the stop is a *position guarantee* — but it
bought the campaign's highest safe-progress (2.544) and beat the released union on the deployment
metric with a CI excluding zero. The safety cost was concentrated where geometry says it must be:
the crossing (side) and in-path (stationary) classes. A router that stops for path-crossing and
in-path threats and crawls only where the tracked geometry proves no path overlap keeps the
position guarantee exactly where it is load-bearing.

**Pre-registerable bar:** safety cells within the released-union's (side ≤ 45%, stationary ≤
25%, NCAP within 0.15 of 3.09 — the iteration-16 bars, unchanged) AND safe-progress vs OFF
positive with CI excluding zero (the criterion every configuration so far has failed at
benchmark scope). Falsifier: if the router's "provably no overlap" predicate is wrong even
rarely, side collisions rise — same 45% kill-bar.

**Cost:** one patch, one 120-episode arm (~5 h); the cheapest line and a direct completion of
the deployment story if it lands.

## Line 3 — tracker-quality repair for VAD transfer

**Motivation (measured):** iteration 14 located the union's failed selectivity transfer in
tracking quality — VAD exposes no learned tracker, and nearest-neighbor IDs manufacture closing
speed. A lightweight ID stabilizer (gated Hungarian association with a constant-velocity filter)
between VAD's detections and the monitor would test the sharpest form of the transfer claim:
*monitor portability is a tracker-quality requirement, quantifiable in ID-switch rate*.

**Pre-registerable bar:** VAD+union selectivity restored (clean-scene ego distance within 20% of
VAD-OFF) while keeping the transfer's safety wins (stationary and side at 0% held); report the
tracker's ID-switch rate alongside, giving the field a concrete portability threshold.

**Cost:** moderate — one association module (pure geometry, unit-testable offline against the
committed VAD decision logs before any GPU time), one 120-episode VAD arm.

> **Line 3 outcome (2026-07-06):** run as iteration 20's offline stage only. The committed
> tracker defaults removed **0/47** raw TTC fires, retained only **4/6** side firing episodes
> (bar: 90%), and increased frontal firing frames **79 -> 90**. The pre-registered gate failed;
> no VAD closed-loop run launched. The broad tracking-quality constraint remains, but this
> simple association + smoothing bridge is closed.
> [`../experiments/iter20_vad_tracker_portability/RESULT.md`](../experiments/iter20_vad_tracker_portability/RESULT.md).

## The manuscript

Runs in parallel with whichever line is on the GPU: the campaign is consolidated in
[REPORT.md](REPORT.md) and every number is committed; the manuscript is a writing task, not a
measurement task. It waits only for the power run's final numbers so results are stated once.

## Decision rules

1. **Manuscript drafting starts when the power run's RESULT is committed** — no line blocks it.
2. **Line 2 runs first on the GPU** (cheapest, completes the deployment story the campaign has
   chased since iteration 3; its null is also cheap and informative).
3. **Line 1 starts its offline stage (feature extraction, head training) in parallel with Line
   2's GPU time**; its closed-loop evaluation runs only after its offline bar (escape rate >
   30%) is met — the iteration-12 corpus makes that a no-GPU check.
4. **Line 3 runs when Lines 1–2 conclude**, or earlier if either stalls on engineering.
5. Every line gets a frozen HYPOTHESIS.md with falsifiers before data, per the campaign standard.
