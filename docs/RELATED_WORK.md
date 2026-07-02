# Related work — verified positioning (2023–2026)

Compiled 2026-07-02 from a multi-angle literature sweep with per-claim adversarial verification
(25 claims checked against source PDFs by three independent verifiers each; 22 confirmed, 3
killed — including one intermediate summary that *hallucinated* exactly the mechanism we care
about, caught because verification reads the actual paper). Confidence labels are the sweep's,
not aspirations. The purpose of this document is honesty in both directions: what the field has
already done, and which of this repository's claims survive it.

## 1. Runtime monitors for end-to-end planners, evaluated closed-loop

- **CATPlan / RiskMonitor** (arXiv 2503.07425; v2 Feb 2026) — the canonical introspection-style
  collision monitor for E2E planners: a *learned* transformer decoder trained on the sign of the
  planner's collision loss, reading UniAD/VAD internal queries. Closed-loop on NeuroNCAP: v1
  detection AUROC 70.6% / AP 66.7%; v2 adds a braking policy (66.5% closed-loop collision-rate
  reduction). No mode-diversity analysis, no candidate selection, no progress-aware metric.
  *(high confidence)*
- **Argus** (arXiv 2511.09032, ASE 2025) — monitor + fallback on TCP/UniAD/VAD, closed-loop in
  CARLA (Bench2Drive220, Leaderboard 2.0): up to +150.3% Driving Score. Its fallback **generates
  its own replacement trajectory** (Bézier reference + occupancy rerouting + IDM) and takes over.
  *(high confidence)*
- **Centaur** (arXiv 2503.11650) — test-time *training*: gradient updates to the planner driven by
  a cluster-entropy uncertainty over its multimodal decisions. The candidates feed the signal; the
  action is a weight update, not selection. *(high confidence)*

**Sentinel's position.** The union monitor is *label-free geometry over the planner's own outputs*
— no trained monitor head, no takeover trajectory, no weight updates — evaluated closed-loop on
NeuroNCAP with a deployment-aware metric. Within the verified corpus, the braking-monitor niche is
occupied (RiskMonitor) but the label-free/no-training variant with progress-aware validation is
not.

## 2. Selecting among a frozen planner's own candidates at runtime

Candidate scoring/selection is an active paradigm — CLOVER (arXiv 2605.15120), GTRS (arXiv
2506.06664), DIVER (arXiv 2507.04049), DiffusionDrive (arXiv 2411.15139), TransDiffuser rejection
sampling — but in **every verified instance the scorer is co-trained as part of the planner's own
pipeline**, and evaluation is on non-reactive NAVSIM, not a reactive closed-loop benchmark.
**No verified published work re-ranks or selects among a frozen planner's native candidates at
runtime using an external safety/uncertainty signal.** *(high confidence)*

**Sentinel's position.** That mechanism is exactly iteration 12's design (and the VAD line's H12):
an external, label-free risk signal choosing among the frozen planner's own modes, reactive
closed-loop. Iteration 12 established the *pre-condition result* on UniAD (candidates collapse
under threat — the mechanism is empty there); the VAD test is in flight. Whether the mechanism
ultimately prevents the head-on or not, the runtime-selection-on-frozen-planner slot appears
unoccupied.

## 3. Mode collapse under threat

Mode collapse in trajectory heads is well documented as a **training-time** phenomenon —
imitation from single demonstrations (DIVER), winner-takes-all instability (aWTA, arXiv
2409.11172), diffusion denoising convergence (DiffusionDrive) — with the first explicit
mode-collapse metrics appearing for **joint prediction** on safety-critical interactions
(arXiv 2506.23164, "Mode Collapse Happens", June 2025). **No verified source documents diversity
collapse conditioned specifically on threat in end-to-end planners' candidate sets.**
*(high confidence on the prior art; the absence claim is a search result, not a proof)*

**Sentinel's position.** Iteration 12's finding — UniAD's command-conditioned candidates span
14 m in benign frames and 4 cm under threat (0/37 escapes) — is, to the verified corpus's
knowledge, the first *threat-conditioned* diversity measurement on an E2E planner's own candidate
set, closed-loop. The VAD run extends it to a second planner and a second candidate mechanism.

## 4. Deployment-aware metrics with honest statistics

The verified corpus reports Driving Score, violation counts, and collision-rate reductions —
**no confirmed source reports combined progress+safety metrics with bootstrap confidence
intervals, intervention budgets, or detection lead time for a closed-loop runtime monitor.**
*(medium confidence — absence claims are only as strong as the sweep)*

**Sentinel's position.** Safe-progress with seed-paired bootstrap CIs (withdrawn once, then
re-established at n=20 — [`../experiments/VERIFICATION.md`](../experiments/VERIFICATION.md)),
plus interventions-per-distance and median lead time from committed decision logs, is the
evaluation vocabulary this repo contributes.

## 5. Over-conservatism of formal envelopes

The criticism exists as a **citable but unquantified assertion** (Centaur's abstract: rule-based
fallbacks are "often overly conservative"). **No confirmed source empirically measured RSS-style
progress collapse closed-loop.** *(medium confidence)*

**Sentinel's position.** Iteration 13 measures it: the envelope takes the best raw safety of the
campaign and lands *below the unmonitored planner* on safe-progress (0.879 vs 1.826; union−RSS
= +1.345, CI [+0.944, +1.701]) — turning the folklore into a number, on the same episodes and
actuator as the introspective monitor.

## Standing caveats

"Unoccupied" means unoccupied *in a verified sweep dated 2026-07-02* — the field moves monthly,
and absence-of-evidence claims carry the sweep's coverage, not certainty. Scope differences also
matter when comparing numbers: RiskMonitor evaluates detection quality on balanced sets; Argus
runs CARLA scenarios; Sentinel runs 2 public-mini NeuroNCAP scenes at n=20 with seed-paired
statistics. This document positions mechanisms, not leaderboard numbers.
