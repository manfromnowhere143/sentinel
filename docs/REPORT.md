# Sentinel: a label-free runtime safety monitor for frozen end-to-end driving planners, evaluated closed-loop

**Technical report — 2026-07-02, updated 2026-07-06.** Every number below regenerates from
evidence committed in this repository; reproduction commands are in the
[README](../README.md#reproduce--repository-map). Scope is stated plainly throughout; the
full-benchmark (14-scene) measurement and its latch-release refinement are reported in §10.

## Abstract

End-to-end driving planners fail catastrophically in safety-critical closed-loop scenarios
(published NeuroNCAP: UniAD scores 1.84/5, colliding in 88–98% of runs), yet the field's dominant
open-loop metrics cannot see it. We build a runtime monitor that reads only a frozen planner's own
outputs — its plan, detected objects, and their tracked motion; no labels, no training, no
privileged simulator state — and intervene with a latched stop. Across 23 documented iterations
and an independent verification pass, we show: (1) a **union of two label-free
geometric detectors** (plan-vs-tracked-path closest approach; observed-closing time-to-collision)
is *selective* (clean-scene behaviour identical to the unmonitored planner), removes most
side-impacts (100% → 30%), halves frontal impact speed (13.9 → 6.7 m/s, median 2.5 s warning),
and is **net-positive on a progress-aware deployment metric with a bootstrap CI excluding zero**
(safe-progress +0.398, 95% CI [+0.133, +0.665], 20 unique episodes/scene); (2) an
**RSS-style formal envelope on identical inputs achieves the best raw safety of the campaign by
near-paralysis** — quantifying, apparently for the first time closed-loop, the over-conservatism
the literature only asserts; (3) three evasive-maneuver designs are **refuted** with a structural
reason — a stop is safe under false alarms, a swerve is not — later completed into a two-sided
result by the softer-than-stop null (a crawl is unsafe under *true* alarms: the stop is a
position guarantee, not merely speed reduction); (4) the planner's own candidate
trajectories **collapse under threat** on two planners (UniAD: 14 m benign diversity → 4 cm in
danger; VAD: partial, below a pre-registered viability bar), and two learned successor heads
under the runtime selector also fail offline (planning-query and BEV conditioning: **0/37**
feasible escapes each) — closing the tested frozen-planner plan-selection path; and (5) the
union's **selectivity does not transfer blind** to a second planner — it is a property of
tracking quality, not the decision rule alone; two subsequent causal-localization Stage 1s stopped
before probes, first because extraction/GT integrity and heldout support failed, then because a
hardened extraction passed S0 but lacked the frozen collapse/intervention count support; and (6)
at full benchmark scale and 20 seed-paired runs per pair (799 episodes) the published UniAD
baseline **independently reproduces** (pooled 2.12 vs 1.84) and the monitor lifts the pooled
score to **2.91 (+0.783, 95% CI [+0.605, +0.928])**, with a threat-cleared latch release
strictly dominating the plain union — while the deployment-metric effect vs the unmonitored
planner resolves to a **tight null** (−0.03, 95% CI [−0.13, +0.07]): the benchmark safety gain
costs approximately nothing on the deployment metric, and softening the stop cannot buy the
residual back (the crawl null).
One headline claim was withdrawn by our own audit and re-established on independent data; the
withdrawal is part of the record.

## 1. Problem and positioning

Open-loop planning metrics are saturated and gameable (an ego-state MLP "wins" nuScenes L2); the
honest axis is closed-loop safety, where the public state of the art is failing. The runtime-
monitor literature on end-to-end planners ([verified sweep](RELATED_WORK.md)) offers learned
collision predictors with braking (RiskMonitor), generative takeover (Argus), and test-time
weight updates (Centaur). Sentinel differs on four verified-unoccupied axes: label-free geometry
instead of a trained monitor head; a deployment metric (progress × safety) with bootstrap CIs;
an empirical measurement of formal-envelope over-conservatism; and threat-conditioned candidate
diversity on frozen planners.

## 2. Apparatus and methodology

Three public containers on one L4 GPU: the NeuroNCAP orchestrator (scenario actor + scoring),
the NeuRAD neural renderer (photoreal multi-camera frames from real nuScenes drives), and the
frozen planner's inference server carrying the Sentinel patch, env-gated per arm. The monitor is
a reviewable ~150-line patch; every arm differs from OFF by one switch.

Methodological spine:

- **Pre-registration.** The campaign win bar was frozen before results
  ([PREREGISTRATION.md](../PREREGISTRATION.md)); later iterations freeze per-experiment
  hypotheses, thresholds, and decision rules before data (iterations 12–14, VAD, the full-14 run).
- **Determinism and seed-pairing.** NeuroNCAP episodes replay deterministically per run index — a
  property we established, which both *invalidated* an early pooled claim (below) and *upgraded*
  every comparison to seed-paired on identical episodes.
- **Evidence discipline.** Per-frame monitor decision logs, per-run trajectories, and run logs are
  committed for every arm ([experiments/verification/](../experiments/verification/README.md));
  when a document disagreed with a log, the log won and the document was corrected in place.
- **Nulls are results.** Three evasion designs, two candidate-collapse verdicts, and a failed
  selectivity transfer are published with the same weight as the wins.

## 3. The monitor and the validated result

The union brakes when **(plan-vs-tracked-path closest approach < 1.5 m) OR (observed
agent-closing TTC < 2.5 s)** — the first term catches the side T-bone (a real path crossing), the
second catches the head-on that the planner's own optimistic plan hides. Object velocity is
observed (ego-motion-compensated tracking by persistent ID), not the planner's forecast — the
forecast is optimistic on exactly the runs that collide (G1 study: the planner's own outputs
predict its collisions at AUROC 0.83, sharpening toward the imminent horizon).

At 20 genuinely-unique episodes per scene (indices 0–7 doubling as an exact apparatus
reproduction — they match the original data to the last digit):

| metric (n=20/scene) | unmonitored UniAD | + union |
|---|---:|---:|
| clean-scene score / collision | 4.51 / 10% | 4.51 / 10% (identical) |
| side-impact collision rate | 100% | **30%** |
| frontal score (0–5) | 0.84 | **2.36** |
| safe-progress (safety × progress) | 1.83 | **2.22** |

**Delta +0.398, 95% CI [+0.133, +0.665]** — excludes zero. In safety-case units: median detection
lead **2.5 s** before counterfactual contact; **11 brake frames per 242 benign meters**; frontal
mean impact speed **13.9 → 6.7 m/s**.

## 4. The formal-envelope baseline

An RSS-style guaranteed-stopping envelope on the *same* observed kinematics and the *same*
actuator — isolating the decision rule — posts the campaign's best raw safety (clean 0%, frontal
30%, side 0%) while driving 3.6–8.2 m where the planner drives 21–32 m: safe-progress **0.879,
below the unmonitored planner's 1.826** (union − RSS = +1.345, CI [+0.944, +1.701]). The
over-conservatism criticism of rule-based fallbacks exists in the literature only as an
unquantified assertion; this measures it. Stopping power is free; **selectivity — knowing the
plan clears the object — is what plan-aware introspection buys.**

## 5. Negative results I: evasion, and the false-positive asymmetry

Three designs to *prevent* (not soften) the frontal head-on were pre-registered, run, and
refuted: steer-at-speed (worse than stopping), brake-and-steer-into-a-tracked-gap (equally
worse), early-detection + time-gated lane change (no prevention, and **50% collisions on the
benign scene** — re-confirmed at n=20: 25% vs OFF's 10%). The structural lesson the third null
proves: **a committed stop degrades gracefully under the false positives every real monitor
produces; an invented swerve causes the crash it was meant to avoid.** Evasion demands a
precision that label-free monitoring does not have.

## 6. Negative results II: the planner has no plan B

The natural escape from the stop's ceiling is to execute the planner's own safer candidate —
safe on false alarms by construction. Pre-registered checkpoints measured whether a low-risk
candidate *exists* when the executed plan is dangerous:

| | UniAD (command-conditioned head re-runs) | VAD (native ego_fut_preds, one pass) |
|---|---|---|
| benign diversity (median/max endpoint spread) | 2.6 / 13.9 m | 3.5 / 22.1 m |
| mode spread under threat | **4 cm** | 0.6 m |
| escape rate (bar: >30%) | **0%** (0/37) | **21%** (23/111) |

Command-indexed trajectory alternatives lose most of their diversity precisely when it matters —
totally on UniAD, partially on VAD; neither clears the pre-registered viability bar, so no
re-ranker was built. To the verified corpus, these are the first threat-conditioned diversity
measurements on end-to-end planners' own candidates; the nearest published evidence is
prediction-side (arXiv 2506.23164).

Two learned successor heads then tested whether a small auxiliary decoder could supply the
missing candidate while leaving the planner frozen. The planning-query head passed benign
fidelity but failed at **0/37** feasible escapes; the BEV-conditioned survivor also failed at
**0/37**, with only **23.1%** all-candidate validity and benign error **1.449 m**. The narrow
claim is the important one: these registered heads do not recover a deployable plan B for the
label-free selector. They do not prove that no richer learned planner or representation could
encode alternatives.

A later causal-localization Stage 1 was pre-registered to ask a narrower representation question
at UniAD's motion/planning bridge. It stopped before probes or interventions: extraction produced
1,507 non-reset rows, but the committed timestamp join failed on all rows and the frozen heldout
split had 0 GT frames. That result is a data-support/integrity null, not evidence for or against
the causal signal itself.

The hardened successor repaired the artifact failure but still stopped before the causal test:
availability and canary gates passed, full extraction joined **2,627/2,627** non-reset rows with
zero error rows and stable tensor shapes, then the frozen count-floor gate failed
(`collapse_positive` 0 in every split, `eligible_intervention_frame` 0, heldout
`danger_positive` 17 below the 30-frame floor). That second null is narrower: it validates the
non-evaluation extraction/counting surface, but says this exact manifest and label definition do
not contain enough support to fit the registered probe or choose an activation direction.

The follow-up risk-support atlas put data availability ahead of extraction and kept the iter22/23
rows behind a known-data firewall. That firewall passed, but the fresh staged-data pool failed:
after 582 post-firewall train-scene candidates, the local file-existence check found **0 eligible
scenes**, **0 planned keyframes**, and **0 heldout keyframes**. This third null says only that the
current staged data tree cannot support the registered fresh atlas; it is not evidence that
nuScenes lacks such frames or that the causal signal is absent.

## 7. Transfer: the monitor is not planner-agnostic, and the reason is precise

On a frozen VAD (after four documented fork-level runtime fixes), the union prevents exactly the
failures VAD actually has — **stationary 85% → 0%, side 65% → 0%** (VAD's failure profile is
inverted relative to UniAD's) — but loses its selectivity everywhere (safe-progress 2.30 → 0.75,
CI [−2.06, −1.03]). Decision logs attribute the over-braking to the observed-closing TTC term
reading geometric nearest-neighbor IDs (VAD exposes no tracker), whose jitter manufactures
closing speed. **Selectivity is a property of tracking quality, not of the decision rule alone**
— named as the prime suspect in a pre-run amendment, confirmed by the data. A monitor validated
on one planner is not a plug-in for another.

## 8. The verification pass

An independent audit re-derived every claim from raw committed evidence. It found the original
"n=20 pooled" statistical validation invalid — deterministic episode replays had been pooled as
independent replications — **withdrew the headline**, and re-measured on 20 genuinely-unique
episodes, where the claim was re-established (§3). It also corrected a side-impact rate (5% →
30% at honest n), completed two mid-run snapshot tables (both strengthening the nulls), and
certified what reproduces exactly (the signal study byte-identical; the iteration-2 safety win;
the apparatus). Full report: [experiments/VERIFICATION.md](../experiments/VERIFICATION.md).

## 9. Limitations and scope

Two nuScenes sequences carried all sub-benchmark results (the 14-scene run extends this — 
pre-registered, in progress); one simulator (NeuroNCAP/NeuRAD), whose deterministic episode
replay we characterize and exploit rather than hide; n=20 per cell; the VAD stack required an
ID-association layer whose quality bounds the transfer conclusion; the RSS baseline is the
longitudinal closing-speed form, not a full RSS implementation (disclosed in the patch). No
fleet data, no retraining, single-digit GPU-hours per experiment — deliberately: every gain is
attributable to the monitor, and everything is reproducible from this repository.

## 10. The full-benchmark measurement

All 240 episodes (40 scene-scenario pairs × 6 seed-paired runs × 2 arms) completed with zero
failures; hypotheses were frozen before the run.

- **H14-1 — the published baseline reproduces.** Unmonitored UniAD pools to **2.15** vs the
  published **1.84** (pre-registered tolerance ±0.4) with the published failure structure — to the
  verified literature, the first independent reproduction of the NeuroNCAP UniAD number.
- **H14-2 — a split verdict, both halves first-class.** On the benchmark's own metric the union
  lifts the pooled score **2.15 → 3.09 (+0.934, 95% CI [+0.713, +1.155])** — a 43% relative
  improvement at full scale, driven by side (collisions 73% → 37%) and stationary (32% → 17%).
  On this repository's own deployment metric the mini-scene net-positive **does not generalize**:
  safe-progress delta −0.170, CI [−0.401, +0.032] — the union over-spends progress on several
  unseen benign-progress scenes. Benchmark-positive, deployment-neutral: the exact distinction
  iteration 3 introduced, now measured at scale on our own headline configuration.
- **H14-3 — structure holds, with one named regression.** Side survives its scene-luck falsifier
  (improves on 3 of 4 unseen side scenes); selectivity holds on the already-clean stationary
  scenes; frontal remains mitigation-not-prevention; frontal/0346 got *worse* under the union
  (3.13/50% → 2.28/100%) — logged, not hidden.
- **Validity:** the 0103 pairs reproduce the committed v20 values across metadata versions; no
  exclusions.

The open problem the split verdict defines — brake-budget calibration — was attacked immediately
(iteration 15): releasing the latch after four verified-clear frames **strictly dominates the
union** (identical safety on every cell, 44 releases with zero reopened cases, safe-progress
+0.246 over the union with CI [+0.206, +0.293]) and becomes the campaign's best configuration —
while the deployment gap against the unmonitored planner narrows to +0.08 but keeps a CI that
includes zero. The residual is a *cost-of-stopping* floor in fixed-horizon episodes, not a
triggering flaw.

Iteration 16 then tested the named softer-than-stop mechanism — the planner's own plan
re-parameterized to a 2.0 m/s crawl while latched, the speed fixed from committed impact
evidence before the run — and the **pre-registered null published**: the crawl posts the
campaign's highest safe-progress (2.544; +0.096 over the released union, CI [+0.033, +0.167])
but drops the benchmark score 3.09 → 2.64 and fires the side falsifier (collisions 37% → 57%,
bar 45%), with 0108's impacts landing at 4–5 m/s and zero score. The mechanism is precise: the
stop is a **position guarantee**, not merely speed reduction — the crawl delivers the ego into
the crossing point the stop halts short of. Together with iteration 11 the result is two-sided:
a swerve is unsafe when the trigger is wrong; a crawl is unsafe when it is right; the committed
stop is the only intervention tested that is safe in both cases, and the released union is its
calibrated form — the campaign's best configuration.

Iteration 17 completed the intervention-softness line with threat-class routing — stop wherever
a tracked object's projected path overlaps the planned corridor, crawl where none does. Its
pre-registered safety gate failed on a single misrouted crossing (side 47% vs the 45% bar,
carried by one scene whose crossing geometry the constant-velocity projection misses; benchmark
−0.170 vs a 0.15 tolerance), so the released union stands, its fourth surviving challenge —
while the voided secondary criterion recorded the campaign's first deployment CI excluding zero
against the unmonitored planner (+0.226, [+0.004, +0.421]): the deployment flip is achievable,
pending a crossing-safe predicate. Full tables and evidence:
[experiments/full14_benchmark/RESULT.md](../experiments/full14_benchmark/RESULT.md) ·
[experiments/iter15_latch_release/RESULT.md](../experiments/iter15_latch_release/RESULT.md) ·
[experiments/iter16_soft_stop/RESULT.md](../experiments/iter16_soft_stop/RESULT.md) ·
[experiments/iter17_threat_routing/RESULT.md](../experiments/iter17_threat_routing/RESULT.md).
