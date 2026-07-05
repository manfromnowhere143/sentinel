# A label-free runtime safety monitor for frozen end-to-end driving planners, evaluated closed-loop at benchmark scale

**Working draft — source of record for the manuscript.** Every number cites committed evidence
in this repository; nothing here goes beyond what a result file states. Target venue and
formatting to be decided; this file is the content.

## Abstract

End-to-end driving planners fail catastrophically in safety-critical closed-loop scenarios —
published NeuroNCAP results score UniAD at 1.84/5 with collisions in 88–98% of runs — yet the
field's dominant open-loop metrics cannot see it. We build a runtime monitor that reads only a
frozen planner's own outputs (its plan, detected objects, and their tracked motion; no labels,
no training, no privileged simulator state) and intervenes with a latched, threat-cleared stop.
Across seventeen pre-registered iterations and an independent verification pass we show:
**(1)** the published NeuroNCAP UniAD baseline **independently reproduces** (pooled 2.12 vs
1.84 at 20 seed-paired runs per scenario), to our knowledge a first; **(2)** a union of two
label-free geometric detectors with a threat-cleared release lifts the full-benchmark score to
**2.91 (+0.783, 95% CI [+0.605, +0.928])** while leaving clean-scene behaviour identical to the
unmonitored planner, at a deployment-metric cost that is a **tight null** (safety × progress
delta −0.03, 95% CI [−0.13, +0.07]); **(3)** the committed stop is a **position guarantee**
that no tested softer intervention replaces — three evasive maneuvers, a calibrated crawl, and
a geometric threat-router were all refuted by pre-registered falsifiers, the router while
demonstrating that a deployment-positive monitor is achievable (+0.226 vs the unmonitored
planner, CI [+0.004, +0.421], voided by its safety gate); **(4)** an RSS-style formal envelope
on identical inputs achieves the campaign's best raw safety **by near-paralysis**, quantifying
closed-loop the over-conservatism the literature only asserts; **(5)** the planner's own
candidate trajectories **collapse under threat** on two planners (UniAD: 14 m benign diversity
to 4 cm; VAD: partial, below a pre-registered viability bar) — the first threat-conditioned
diversity measurements on end-to-end planners' own candidates; and **(6)** two independent
failure analyses — cross-planner selectivity transfer and routing safety — converge on a single
binding constraint: **tracking quality**. One headline claim was withdrawn by our own audit and
re-established on independent data; the withdrawal, six published nulls, and the raw per-frame
evidence for every number are part of the record.

## 1. Introduction

Open-loop planning metrics on nuScenes are saturated and gameable: an ego-state MLP with no
perception outperforms published end-to-end planners on displacement error. Closed-loop
evaluation under safety-critical perturbation tells the opposite story — state-of-the-art
planners collide in the vast majority of adversarial episodes. This gap defines the honest
axis for driving-safety research, and it is where runtime assurance belongs: if a frozen
planner's failures are predictable from its own outputs, a small monitor can intervene before
they become collisions, without retraining, fleet data, or privileged state.

This paper reports a complete measurement campaign on that thesis. Its contributions are the
six numbered results in the abstract; its method is as much a contribution as its numbers:
every iteration was pre-registered with falsifiers before data; every comparison is seed-paired
on deterministic episodes; every number regenerates from committed raw evidence; and the
campaign's one statistical over-claim was caught by its own audit, withdrawn in place, and
re-established on fresh data.

## 2. Related work

*(Positioning from a per-claim adversarially verified sweep — 25 claims checked against source
PDFs by three independent verifiers each; docs/RELATED_WORK.md carries the confidence labels.)*

**Runtime monitors for end-to-end planners.** CATPlan/RiskMonitor (arXiv 2503.07425) is the
canonical introspection-style monitor: a *learned* transformer decoder trained on the sign of
the planner's collision loss, reading UniAD/VAD internal queries, with a braking policy
(66.5% closed-loop collision-rate reduction on NeuroNCAP). Argus (arXiv 2511.09032, ASE 2025)
attaches a takeover fallback that *generates its own replacement trajectory* in CARLA. Centaur
(arXiv 2503.11650) performs test-time *training* — gradient updates driven by cluster-entropy
uncertainty. Our monitor differs on each axis: label-free geometry over the planner's own
outputs (no trained head), no invented takeover trajectory (the campaign's evasion, crawl, and
routing nulls argue this is not merely simpler but structurally safer), no weight updates — and
it is validated with a progress-aware metric none of the above report.

**Runtime selection among a frozen planner's candidates.** Candidate scoring is an active
paradigm (CLOVER, GTRS, DIVER, DiffusionDrive, TransDiffuser rejection sampling), but in every
verified instance the scorer is co-trained within the planner's pipeline and evaluated on
non-reactive NAVSIM. No verified published work re-ranks a *frozen* planner's native candidates
at runtime with an external safety signal — the mechanism our iteration-12/14 measurements
close for command-indexed candidates (the candidates collapse when needed) and reopen for
diversity-trained heads.

**Mode collapse under threat.** Documented as a training-time phenomenon (WTA instability,
imitation collapse), with explicit metrics only prediction-side (arXiv 2506.23164). Our
threat-*conditioned* diversity measurements on planners' own candidate sets, closed-loop, on
two planners, appear to be the first.

**Deployment-aware statistics.** The verified corpus reports Driving Score and collision-rate
reductions; no confirmed source reports combined progress+safety metrics with bootstrap CIs,
intervention budgets, or detection lead time for a closed-loop runtime monitor. That
evaluation vocabulary — safe-progress with seed-paired CIs, interventions per benign distance,
median lead time from committed decision logs — is a contribution of this work.

**Formal-envelope over-conservatism** exists in the literature as a citable but unquantified
assertion; §8 measures it closed-loop, on inputs and actuator identical to the monitor's.

## 3. Closed-loop apparatus and methodology

The apparatus is three public containers on one L4 GPU: the NeuroNCAP orchestrator drives the
scenario actor and scores episodes; the NeuRAD neural renderer produces photoreal multi-camera
frames from real nuScenes drives; and the frozen planner serves `/infer` carrying the monitor
as a ~150-line patch, env-gated per arm so every experimental condition differs from the
unmonitored baseline by one switch. NeuroNCAP episodes replay deterministically per run index —
a property we established mid-campaign, which first *invalidated* an early pooled claim (§9)
and then *upgraded* every subsequent comparison to seed-paired on identical episodes. The
determinism is verified at scale: the 20-run measurement's first six indices reproduce the
earlier 6-run measurement exactly, on every scenario pair, in both arms, across five
machine-freezing infrastructure incidents, one host migration, and four relaunches.

The methodological spine, held for all seventeen iterations: hypotheses and falsifiers frozen
in writing before data; seed-paired within-pair bootstrap confidence intervals on every delta;
per-frame monitor decision logs, per-run trajectories, and run logs committed for every arm;
nulls published with the same weight as wins; and when a document disagreed with a log, the log
won and the document was corrected in place.

## 4. The monitor

The union brakes when **(plan-vs-tracked-path closest approach < 1.5 m) OR (observed
agent-closing time-to-collision < 2.5 s)**. The two terms correspond to physically distinct
failure modes: the first catches the side crossing (a real path intersection the planner's
plan will meet), the second catches the head-on that the planner's own optimism hides (its
plan claims 3–4 m of clearance on runs that end in collision). Object velocity is *observed* —
ego-motion-compensated tracking by persistent identity across frames — not the planner's
forecast; the forecast is optimistic on exactly the runs that collide. The underlying signal
is real and cheap: the planner's own outputs predict its collisions at AUROC 0.83, sharpening
toward the imminent horizon.

The stop is latched — safe even when the trigger is wrong — and releases after four
consecutive verified-clear frames against the planner's current plan, returning control.
The release strictly dominates the plain latch: identical safety on every cell, +0.246
safe-progress (CI [+0.206, +0.293]).

## 5. The benchmark result (20 runs per pair, 799 episodes)

| pooled, 14 official scenes | unmonitored UniAD | + released union |
|---|---:|---:|
| NCAP score | 2.12 (published 1.84) | **2.91** |
| side collisions | 74% | **44%** |
| stationary collisions | 29% | **18%** |
| frontal | 1.24 / 78% | 1.78 / 90% (mitigation) |
| safe-progress | 2.40 | 2.36 |

Benchmark delta **+0.783, CI [+0.605, +0.928]**; deployment delta **−0.03, CI [−0.13, +0.07]**
— the safety gain costs approximately nothing on the deployment metric. The frontal/0346
regression (the stop converting occasional planner escapes into low-speed collisions) is
confirmed real at n=20 and reported as the stop policy's named cost. In safety-case units
(from committed decision logs): median detection lead **2.5 s** before counterfactual contact;
**11 brake frames per 242 benign meters**; frontal mean impact speed **13.9 → 6.7 m/s**.

## 6. Negative results I: the stop is a position guarantee

Five designs to keep more progress than the stop were pre-registered and refuted, and their
pattern of failure is the finding:

- **Three evasive maneuvers** (steer-at-speed; brake-and-steer-into-gap; early-detection +
  lane change) fail under *false* alarms — the third crashes the benign scene at 25% vs the
  unmonitored 10%.
- **A calibrated 2.0 m/s crawl** fails under *true* alarms — it posts the campaign's
  then-highest safe-progress but delivers the ego into the crossing point the stop halts short
  of (side 37% → 57%, with impacts at near-reference severity).
- **A geometric threat-router** (stop on projected path overlap with the planned corridor;
  crawl otherwise) comes closest: it recovers most of the crawl's safety loss, posts the
  campaign's best frontal score, and records the campaign's first deployment-metric CI
  excluding zero against the unmonitored planner (**+0.226, CI [+0.004, +0.421]**) — and still
  fails its pre-registered gate on a single misrouted crossing (side 47% vs the 45% bar,
  carried entirely by one scene whose crossing geometry the constant-velocity projection
  intermittently misses).

Together: the stop is not merely speed reduction but a **position guarantee** — the only
tested intervention safe in both error directions — and a deployment-positive monitor is
demonstrably achievable, pending a crossing-safe routing signal (§8).

## 7. Negative results II: no plan B, envelope paralysis

**The planner has no plan B.** The natural escape from the stop's ceiling is to execute the
planner's own safer candidate — safe on false alarms by construction. Pre-registered
checkpoints measured whether a low-risk candidate *exists* when the executed plan is
dangerous: UniAD's command-conditioned candidates span 13.9 m in benign frames and collapse to
a 4 cm spread under threat (0/37 escapes); VAD's native modes retain partial diversity (21%
escapes) but stay below the frozen 30% viability bar. Command-indexed alternatives lose their
diversity precisely when it matters; a diversity-trained candidate head is the motivated
successor mechanism.

**Stopping power is free; selectivity is not.** An RSS-style guaranteed-stopping envelope on
identical inputs and actuator posts the campaign's best raw safety (clean 0%, frontal 30%,
side 0%) by driving 3.6–8.2 m where the planner drives 21–32 m — safe-progress 0.88 against
the unmonitored planner's 1.83 (union − RSS = +1.345, CI [+0.944, +1.701]). The
over-conservatism criticism of formal fallbacks, previously an unquantified assertion, is here
a measured closed-loop number.

## 8. The binding constraint is tracking quality

Two failure analyses, from independent directions, converge:

- **Transfer (iteration 14).** On a frozen VAD the union prevents exactly the failures VAD has
  (stationary 85% → 0%, side 65% → 0% — an inverted failure profile) but loses selectivity
  everywhere; decision logs attribute the over-braking to nearest-neighbor identity jitter
  manufacturing closing speed where VAD exposes no learned tracker.
- **Routing (iteration 17).** The router's single misrouted crossing traces to projection
  flicker — velocity dropouts across identity switches. All three named per-frame geometric
  repairs were then refuted *offline* on the committed decision logs (one is a provable no-op;
  one trades away the mechanism; one is statistically non-separable from safe cases), closing
  the routing line for instantaneous geometric predicates.

The discriminating signal in both cases is **velocity continuity through identity switches** —
a property of the tracking layer, not of any decision rule above it. This reframes runtime
monitor portability and monitor softening as one problem: the quality of the track stream the
monitor consumes, quantifiable in identity-switch rate. A lightweight association-and-filter
layer, unit-testable offline against the committed VAD and routing logs before any closed-loop
time, is the motivated next mechanism.

## 9. Verification, reproducibility, and the incident record

An independent verification pass re-derived every claim from raw evidence. It discovered the
episode determinism, found that an early pooled validation had counted deterministic replays
as independent replications, **withdrew the headline**, and re-measured on genuinely unique
episodes where the claim was re-established (mini-scene safe-progress +0.398, CI [+0.133,
+0.665]). Corrections were applied wherever documents disagreed with logs.

The power measurement's incident record is reported as part of the measurement: five
machine-freezing events across two physical hosts, root-caused via an on-box vitals instrument
to memory exhaustion on a swapless image, fixed with swap; one scenario pair reported at n=19
after its final episode reproducibly froze the pre-swap host (three attempts, two hosts). No
completed episode was lost or re-measured differently — the exact-reproduction gate is the
proof. Every number in this paper regenerates from committed raw evidence with the commands in
the repository README.

## 10. Limitations

One simulator (NeuroNCAP/NeuRAD), whose deterministic replay we characterize and exploit; 20
runs per pair against the published 100-run protocol; two planners; the VAD transfer bounded
by an identity-association layer's quality; the RSS baseline is the longitudinal form, not a
full implementation; no fleet data or real-vehicle validation. Frontal head-on prevention (as
opposed to mitigation) remains open and is, on this evidence, not reachable by maneuver
invention from a label-free monitor.

## 11. Conclusion

A label-free monitor on a frozen planner lifts the full official NeuroNCAP benchmark from an
independently reproduced 2.12 to 2.91 with a confidence interval excluding zero, at a
deployment-metric cost statistically indistinguishable from zero. The campaign's negative
results are as load-bearing as its wins: the stop's position guarantee, the planner's missing
plan B, the envelope's paralysis, the achievable-but-not-yet-safe deployment flip, and the
convergence of two independent failure modes on tracking quality — together they map the
mechanism space for runtime driving assurance more sharply than the headline number does, and
they name the next frontier precisely.

## References

*(Verified in docs/RELATED_WORK.md; to be formatted for venue.)*
NeuroNCAP (arXiv 2404.07762) · UniAD (CVPR 2023) · VAD (ICCV 2023) · CATPlan/RiskMonitor
(arXiv 2503.07425) · Argus (arXiv 2511.09032) · Centaur (arXiv 2503.11650) · DIVER (arXiv
2507.04049) · GTRS (arXiv 2506.06664) · CLOVER (arXiv 2605.15120) · DiffusionDrive (arXiv
2411.15139) · aWTA (arXiv 2409.11172) · Mode Collapse Happens (arXiv 2506.23164) · RSS (arXiv
1708.06374) · MuSt/ego-status MLP critique (BEV-Planner, arXiv 2312.03031).

---

### Draft status

- [x] Abstract — final numbers incl. iteration 17 and the convergence finding
- [x] §1 Introduction · §2 Related work (verified-sweep positioning)
- [x] §3 Apparatus · §4 Monitor · §5 Benchmark result — full prose
- [x] §6–§8 Negative results and the tracking-quality convergence — full prose
- [x] §9–§11 Verification, limitations, conclusion
- [x] Reference list (IDs verified; venue formatting pending)
- [x] Figures 1–3 rendered from committed evidence (figures/make_figures.py — validated
      palette, grayscale-safe): per-class benchmark bars; lead-time events; routing audit
- [ ] Figure 0: campaign two-act arc (vector redraw of the README diagrams)
- [ ] LaTeX conversion for arXiv (venue decision: arXiv first, per 2026-07-05)
