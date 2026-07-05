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
unmonitored planner, and its deployment-metric cost is a **tight null** (safety × progress
delta −0.03, 95% CI [−0.13, +0.07]); **(3)** the committed stop is a **position guarantee**
that no tested softer intervention can replace — three evasive-maneuver designs and a
calibrated crawl were all refuted by pre-registered falsifiers, giving a two-sided structural
result (a swerve is unsafe when the trigger is wrong; a crawl is unsafe when it is right);
**(4)** an RSS-style formal envelope on identical inputs achieves the campaign's best raw
safety **by near-paralysis**, quantifying closed-loop the over-conservatism the literature only
asserts; **(5)** the planner's own candidate trajectories **collapse under threat** on two
planners (UniAD: 14 m benign diversity to 4 cm; VAD: partial, below a pre-registered viability
bar) — the first threat-conditioned diversity measurements on end-to-end planners' own
candidates; and **(6)** monitor selectivity does **not transfer blind** to a second planner —
it is a property of tracking quality, not the decision rule alone. One headline claim was
withdrawn by our own audit and re-established on independent data; the withdrawal, five
published nulls, and the raw per-frame evidence for every number are part of the record.

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

*(Sections below are drafted from the evidence-wired technical report; numbers final as of the
20-run power measurement.)*

## 2. Related work

Position against (verified sweep, docs/RELATED_WORK.md): learned collision-prediction monitors
with braking (RiskMonitor/CATPlan); generative takeover (Argus); test-time adaptation
(Centaur); formal runtime assurance (RSS and derivatives); THG/candidate-diversity literature
(prediction-side only). Four axes verified unoccupied: label-free geometric monitoring on a
frozen planner; progress-aware deployment metric with CIs; closed-loop quantification of
formal-envelope over-conservatism; threat-conditioned candidate diversity on planners' own
candidates.

## 3. Closed-loop apparatus and methodology

Three public containers on one L4 GPU (NeuroNCAP orchestrator/scorer; NeuRAD neural renderer;
frozen planner serving `/infer` with the monitor patch env-gated per arm). Deterministic
episode replay per run index — established during the campaign, exploited for seed-pairing,
and verified at scale: the 20-run measurement's first-6 indices reproduce the earlier 6-run
measurement exactly on every scenario pair in both arms. Methodological spine:
pre-registration with falsifiers; seed-paired bootstrap CIs; committed per-frame decision
logs; nulls published with the same weight as wins.

## 4. The monitor

Union of two label-free geometric detectors over the planner's own outputs — plan-vs-tracked-
path closest approach (< 1.5 m) catching the crossing threat, and observed-closing
time-to-collision (< 2.5 s) catching the head-on the planner's optimistic plan hides — with a
latched stop that releases after four consecutive verified-clear frames. Object velocity is
observed (ego-motion-compensated tracking by persistent ID), not the planner's forecast; the
forecast is optimistic on exactly the runs that collide (the planner's own outputs predict its
collisions at AUROC 0.83, sharpening toward the imminent horizon).

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
regression (stop converting occasional planner escapes into low-speed collisions) is confirmed
real at n=20 and reported as the stop policy's named cost. In safety-case units (from committed
decision logs): median detection lead 2.5 s; 11 brake frames per 242 benign meters; frontal
mean impact speed 13.9 → 6.7 m/s.

## 6. Negative results I: the stop is a position guarantee

Three evasive designs (steer-at-speed; brake-and-steer-into-gap; early-detection + lane
change) and a calibrated 2.0 m/s crawl were pre-registered and refuted. The evasions fail
under false alarms (the third crashes the benign scene at 25% vs OFF's 10%); the crawl fails
under true alarms (side 37% → 57%: it delivers the ego into the crossing point the stop halts
short of, at near-reference impact severity) while posting the campaign's highest
safe-progress. Together: the stop is not merely speed reduction but a position guarantee, and
it is the only tested intervention safe in both error directions.

## 7. Negative results II: no plan B, and a failed transfer with a precise reason

Candidate collapse under threat on two planners (UniAD 0/37 escapes; VAD 21% < 30% bar) closes
runtime plan-selection for command-indexed candidates and motivates a diversity-trained head.
The union transfers its safety to VAD (stationary 85% → 0%, side 65% → 0% — an inverted
failure profile) but loses selectivity entirely; decision logs attribute this to
nearest-neighbor ID jitter manufacturing closing speed. Selectivity is a property of tracking
quality.

## 8. The formal-envelope baseline

RSS-style guaranteed-stopping envelope on identical inputs and actuator: best raw safety of
the campaign (clean 0%, frontal 30%, side 0%) by driving 3.6–8.2 m where the planner drives
21–32 m — safe-progress 0.88 vs the unmonitored 1.83 (union − RSS = +1.345, CI [+0.944,
+1.701]). Stopping power is free; selectivity is what plan-aware introspection buys.

## 9. Verification, reproducibility, and the incident record

The independent verification pass: determinism discovery, withdrawal and re-establishment of
the headline, corrections applied where documents disagreed with logs. The power measurement's
incident record: five machine-freezing events across two physical hosts, root-caused (via an
on-box vitals instrument) to memory exhaustion on a swapless image, fixed with swap; one
scenario pair reported at n=19 after its final episode reproducibly froze the pre-swap host
(3/3 attempts, 2 hosts); no completed episode lost or re-measured differently — the exact-
reproduction gate is the proof. Every number regenerates from committed raw evidence with the
commands in the repository README.

## 10. Limitations

One simulator (NeuroNCAP/NeuRAD) whose deterministic replay we characterize and exploit; 20
runs per pair against the published 100-run protocol; two planners; the VAD transfer bounded
by an ID-association layer's quality; the RSS baseline is the longitudinal form, not a full
implementation; no fleet data or real-vehicle validation. Frontal head-on prevention (as
opposed to mitigation) remains open and is, on this evidence, not reachable by maneuver
invention from a label-free monitor.

## 11. Conclusion

A label-free monitor on a frozen planner lifts the full official NeuroNCAP benchmark from an
independently reproduced 2.12 to 2.91 with a CI excluding zero, at a deployment-metric cost
statistically indistinguishable from zero — and the campaign's negative results are as
load-bearing as its wins: the stop's position guarantee, the planner's missing plan B, the
envelope's paralysis, and the non-portability of selectivity define the mechanism space for
runtime driving assurance more sharply than the headline number does.

---

### Draft status

- [x] Abstract — final numbers
- [x] §1 Introduction — first pass
- [ ] §2 Related work — expand from docs/RELATED_WORK.md with citations
- [ ] §3–§8 — tighten from docs/REPORT.md; add figures (campaign arc; per-class bars; lead-time histogram)
- [x] §9–§11 — first pass
- [ ] Iteration-17 (threat-class routing) result — folds into §5/§6 when its verdict lands
- [ ] Figures, references, venue formatting
