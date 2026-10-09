# Iteration 135 pre-run scientific decision review — 2026-10-09

Status: proposed strategic review. This is neither an amendment to the preregistration nor an
Iteration-135 result. The current mission state remains `CI_HARDENING_REQUIRED / UNKNOWN`.

## Decision

Iteration 135 is a disciplined terminal test of one **assigned-policy contrast** on the frozen
NeuroNCAP suite. It is worth preserving as that test. It is not, on its own, a decisive test of
whether planner-risk semantics cause the benefit, whether the monitor transfers, or whether a
deployable safety system exists. The offline diagnostic below finds low sensitivity near the
registered practical margins. Before spending the registered ceiling of 110 L4 GPU-hours, the
inferential target and claim wording need an explicit pre-evidence decision. Any protocol change
must be a visible pre-evidence amendment, never a post-result repair.

## Evidence that controls this review

- [Iteration 134](../../experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md)
  reproduced union-minus-OFF but returned `PLACEBO_HARM_OR_NULL`. Union-minus-placebo was
  `+0.3683`, 95% pair-clustered CI `[-0.1901,+0.8866]`; the placebo realized only `859/1205`
  scheduled brake frames. Semantic attribution remains unresolved.
- [Iteration 135's frozen hypothesis](../../experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md)
  fixes 20 class/pair cells, 20 repeated runs per cell, six arms, 2,400 analytic episodes, a
  practical NCAP margin of `0.25`, and a `Q16` progress non-inferiority bound of `-0.05`. Its own
  audit estimates an approximately `0.61` 80%-power detectable effect for a single contrast at
  this scene count. It explicitly permits an inconclusive result.
- [The mission state](../../MISSION_STATE.json) records HUGSIM transfer as `TRANSFER_NULL` and
  production readiness as `NOT_ESTABLISHED`. The [research audit](SENTINEL_POST_ITER130_MISSION_ALIGNMENT_AUDIT_2026-07-14.md)
  distinguishes empirical findings from the support-core design/preflight chain.

## Completed offline diagnostic from Iteration 134 proof

Run [the audit script](../../scripts/audit_iter135_prerun.py) with
`python3 scripts/audit_iter135_prerun.py` from the repository root. The script reads only the
committed Iteration-134 run archive at SHA-256
`b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315`, rejects a
different archive or incomplete episode inventory, and parses all `1,200` episodes. It applies
Iteration 135's equal-class aggregation and `Q16` definition to the old three-arm pilot. Its
`100,000` class-stratified pair bootstrap draws and `100,000` valid shared-source-scene draws use
seed `135`. This is a **retrospective design diagnostic**, not an Iteration-135 analysis or a
substitute for the frozen analyzer. The Iteration-134 placebo's realized-dose defect remains.

| Old union minus placebo | Point | Class-stratified pair 95% interval | Shared-source-scene 95% interval |
|---|---:|---:|---:|
| NCAP | `+0.3683` | `[-0.1304,+0.8510]` | `[-0.2279,+0.9884]` |
| `Q16` | `+0.0031` | `[-0.0800,+0.0901]` | `[-0.0885,+0.1019]` |

The arm NCAP means reproduce the published rounded values: OFF `2.135`, union `2.906`, placebo
`2.538`. The `Q16` means reproduce the preregistration's pilot audit: OFF `0.9027`, union
`0.7631`, placebo `0.7600`. Source-scene resampling widens both intervals and leaves zero inside
them. The pilot `Q16` lower bound is below the registered `-0.05` non-inferiority margin under
both resampling methods.

For a transparent scale calculation only, plug the pair-bootstrap standard errors (`0.2496`
NCAP; `0.0435` `Q16`) into a normal approximation to the one-sided registered gates. A point
NCAP difference would need to exceed about `0.4106` to pass the one-sided zero bound; a point
`Q16` difference would need to exceed about `+0.0216` to pass the `-0.05` bound. If a future
comparison truly had NCAP advantage `+0.25` and the same variability, the NCAP gate alone would
fire in about `26%` of repeated samples. If its true `Q16` difference were zero, the progress
gate alone would fire in about `31%`. The joint confirmation probability cannot exceed the
smaller of those two probabilities. These are **illustrative plug-in sensitivities**, not
predictions for the different Iteration-135 blind schedule; the actual registered bootstrap need
not have normal coverage, and the two gates are correlated.

There is a sharper design limit: the NCAP rule requires the *observed point estimate* to be at
least `+0.25` as well as a lower bound above zero. Under an unbiased, approximately symmetric
estimator with a true effect exactly `+0.25`, the point-threshold part has at most about `50%`
rejection probability, even as independent sample size grows; the lower-bound part only reduces
it. Thus the registered decision rule cannot have 80% confirmation probability at its own
practical boundary. For scale only, holding the old pair variance fixed, achieving 80% power for
the NCAP *lower-bound part alone* at a true `+0.25` would take about `123` independent
pair-equivalents, and for the `Q16` lower-bound part at a true difference of zero about `94`,
versus the current `20` pair cells and only `14` source scenes. These are normal-approximation
diagnostics, not a proposed sample size, because the actual blind comparator and source-scene
covariance may differ. More repeated seeds on the same scenes cannot supply those independent
units.

**Decision consequence:** do not justify the 110-hour run as likely to *confirm semantic
attribution*. It may still have value as a terminal fixed-suite policy/dose-frontier test or as
an honest null. The scientific case for that expenditure must name those outcomes and the
clock-only comparator limitation before launch. A stronger next causal test needs a responsive,
non-planner-semantic control and independent scenes.

## Questions that matter before the next expensive run

| Question | Current answer | Required interpretation or next evidence |
|---|---|---|
| Does the union add useful information beyond generic braking? | Iteration 134 did not resolve it. Iteration 135 compares the live responsive union with clock-only schedules at equal **assigned class budgets**. | A win identifies this policy contrast. Clock-only control also removes feedback, so it cannot isolate the value of semantic content from the value of state-responsive timing. A later fair test needs a competent, state-aware, non-planner-semantic comparator with frozen information access, actuator, calibration, and intervention-cost rules. |
| What is the unit of inference? | There are 20 class/pair cells but only 14 distinct source-scene IDs; several IDs occur in more than one class. The protocol treats 20 pairs as primary clusters and 14 source scenes as a sensitivity analysis. | Report both. Explain the sampling model behind any confidence interval: the complete fixed 20-pair/20-run mean is an observed suite quantity, while pair resampling describes variation under an assumed population of pairs. Repeated runs do not create new independent scenes. A claim that depends on the 20-pair interval but fails the 14-scene sensitivity is fragile. |
| Is the registered compute likely to change the decision? | The `0.25` practical margin is much smaller than the hypothesis's approximate `0.61` 80%-power detectable effect; `Q16` adds a second necessary gate. The ceiling is 110 GPU-hours. | Use committed Iteration-134 pair-level data for a transparent pre-run power/sensitivity and cost audit, without treating it as Iteration-135 outcome data. State the probability of a decisive verdict under plausible effects and the decision that each verdict triggers. Do not buy apparent precision with more repeated seeds on the same scenes. |
| Does any benefit survive system stress? | HUGSIM transfer is null, and the released rule has a documented 5 cm position-jitter over-firing problem. | The next decisive empirical lane after this terminal fixed-suite test is held-out closed-loop transfer and deployment-fault testing, with collision severity, progress, intervention burden, latency, and missingness reported together. It needs independent scenes and a strong comparator. |

## Work sequence

1. Resolve the inference-target and claim-wording issues above before any Iteration-135 smoke or
   analytic launch. If a material defect requires correction, publish a lawful pre-evidence
   amendment with all code, manifests, and tests synchronized before new evidence exists.
2. Close the present CI/supply-chain blocker with bounded, automated provenance and known-bad
   checks. A green workflow establishes those tested properties, not scientific validity.
3. If the protocol proceeds, execute and report the exact registered trial once. Preserve
   infrastructure nulls, scientific nulls, collision/progress tradeoffs, and disagreement among
   sensitivity analyses. Do not reframe a favorable clock-control contrast as uniquely proven
   semantic causation.
4. Move the main research effort to an external, held-out failure test with a state-aware
   comparator. Freeze failure families, scene independence, information budgets, thresholds,
   resource cost, and stop rules before looking at outcomes. If transfer fails, investigate the
   failure mechanism instead of tuning the NeuroNCAP suite again.

The public methods described by [Mobileye's long-tail program](https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/),
[Waymo's collision-avoidance testing](https://waymo.com/research/collision-avoidance-testing-of-the-waymo-automated/),
and the [Bench2Drive-Robust benchmark](https://arxiv.org/abs/2605.18059) motivate failure-led,
scenario-based, perturbation-aware evaluation. They do not establish what a private team would do
with Sentinel or show that Sentinel equals or exceeds any deployed stack.

The scientifically defensible aim is a narrow, independently reproducible contribution: identify
when an introspective monitor adds value to a frozen planner, when it fails, and how much
intervention and progress that value costs. Broader safety and state-of-the-art claims require
separate comparative evidence.
