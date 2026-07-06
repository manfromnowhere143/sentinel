# Next phase — candidate lines after the power run

Written while the 20-run power measurement executes; nothing here presumes its outcome. Each line
is stated with the evidence that motivates it, the mechanism, the pre-registerable bar, and the
cost. Ordering is by expected knowledge-per-GPU-hour; the decision rules at the bottom say what
runs when.

## New frontier packet after these lines closed

After iterations 19–21 closed the tested frozen-planner candidate-head routes, the recommended
next line is causal localization rather than another decoder:
[`research/CAUSAL_PLANNER_INTERPRETABILITY.md`](research/CAUSAL_PLANNER_INTERPRETABILITY.md).
That file is a launch packet only. The official Stage 1 pre-registration lives at
[`../experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md`](../experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md).
Its result is now published:
[`../experiments/iter22_causal_planner_interpretability/RESULT.md`](../experiments/iter22_causal_planner_interpretability/RESULT.md).
Stage 1 stopped at S0: the extraction/GT timestamp join failed on all 1,507 non-reset rows and
the frozen heldout split had 0 GT frames. It authorizes no iteration-12 scoring, probe claim,
intervention claim, or closed-loop evaluation.

The hardened successor was pre-registered as
[`../experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md`](../experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md).
Its result is now published:
[`../experiments/iter23_s0_hardened_causal_localization/RESULT.md`](../experiments/iter23_s0_hardened_causal_localization/RESULT.md).

Iteration 23 repaired the iteration-22 artifact failure but did not reach the causal test. The
availability gate passed (66 eligible scenes; 39 fit, 13 calibration, 14 heldout; 554 heldout
keyframes), the two-run canary was deterministic, and full S0 integrity passed with 2,627/2,627
joined non-reset rows and zero error rows. The frozen count-floor gate then failed:
`collapse_positive` was 0 in every split, `eligible_intervention_frame` was 0, and heldout
`danger_positive` was 17 below the 30-frame floor. Iter23 authorizes no probe, activation
direction, iteration-12 scoring, or closed-loop evaluation. Any successor causal-localization
line requires a fresh pre-registration with a revised data-support plan.

The next line is now pre-registered as a fresh data-support prerequisite:
[`../experiments/iter24_risk_support_atlas/HYPOTHESIS.md`](../experiments/iter24_risk_support_atlas/HYPOTHESIS.md).
Iteration 24 is not a causal-intervention run. It freezes a known-data firewall that excludes
iter22/iter23 scenes, then asks whether fresh non-evaluation train scenes contain enough
low-diversity hazard frames and benign controls to justify a later causal-localization
pre-registration. A pass authorizes only that later pre-registration; it does not authorize probe
fitting, activation intervention, iteration-12 scoring, selector evaluation, or closed-loop work.

Its result is now published:
[`../experiments/iter24_risk_support_atlas/RESULT.md`](../experiments/iter24_risk_support_atlas/RESULT.md).
The known-data firewall passed, but the availability bar failed before model extraction:
0 eligible fresh scenes, 0 planned keyframes, and 0 heldout keyframes after 582 post-firewall
candidate scenes all missed the local six-camera file-existence check. Iteration 24 authorizes no
canary extraction, full extraction, label atlas, probe fitting, activation direction, iteration-12
scoring, selector evaluation, or closed-loop evaluation. Any successor needs a fresh
pre-registration and must name its data-staging plan before extraction.

The next line was pre-registered as a staged-data provenance gate:
[`../experiments/iter25_staged_data_inventory/HYPOTHESIS.md`](../experiments/iter25_staged_data_inventory/HYPOTHESIS.md).
Iteration 25 may inspect only a frozen list of local nuScenes roots and may produce only
token-free inventory/availability artifacts. It cannot download or copy data, run Docker/model
extraction, compute labels, fit probes, write activation directions, touch iteration-12 outcomes,
score selectors, or run closed loop. A pass authorizes only a separate fresh risk-support-atlas
pre-registration. The committed implementation surface is
[`../experiments/iter25_staged_data_inventory/inventory_roots.py`](../experiments/iter25_staged_data_inventory/inventory_roots.py);
its result is now published:
[`../experiments/iter25_staged_data_inventory/RESULT.md`](../experiments/iter25_staged_data_inventory/RESULT.md).
No root passed: `/datasets/nuscenes` existed but had 0 fresh eligible scenes and 0 keyframes after
the firewall, while the other four frozen roots were missing. It authorizes no data download/copy,
model extraction, label atlas, probe fitting, activation direction, iteration-12 scoring, selector
evaluation, or closed-loop work.

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

> **Line 1 outcome (2026-07-06):** run in two registered offline variants. Iteration 19's
> planning-query head passed benign fidelity but failed at **0/37** feasible escapes, locating
> the collapse in the planner's internal planning representation. Iteration 21 then tested the
> surviving scene-level BEV variant; B0 passed (311/311 exact join, zero plan mismatches), but
> B1 failed at **0/37** feasible escapes, B2 validity was **23.1%**, B3 benign error was
> **1.449 m**, and B4 had no selectable escape. No closed-loop run launched from either
> hypothesis.
> [`../experiments/iter19_diversity_head/RESULT.md`](../experiments/iter19_diversity_head/RESULT.md) ·
> [`../experiments/iter21_bev_diversity_head/RESULT.md`](../experiments/iter21_bev_diversity_head/RESULT.md).

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
2. **Line 2 is closed by iteration 17**; its safety gate failed, and the released union stands.
3. **Line 1 is closed by offline gates**; its closed-loop evaluation never runs because neither
   the planning-query nor the BEV-conditioned variant met the escape/feasibility bars.
4. **Line 3 is closed by iteration 20**; the registered tracker bridge failed before GPU time.
5. Iteration 24 is closed as an availability-null before model extraction.
6. Iteration 22 is closed as an S0 data-null.
7. Iteration 23 is closed as a count-floor data-null after S0 pass. It authorizes no probe,
   activation direction, iteration-12 scoring, or closed-loop run. Any next causal-localization
   line needs a fresh HYPOTHESIS.md before data.
8. Iteration 25 is closed as a staged-data inventory infrastructure-null. No active experiment
   authorizes data download/copy, model extraction, label atlas, probe fitting, activation
   intervention, iteration-12 scoring, selector evaluation, or closed-loop work.
