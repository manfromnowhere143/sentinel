# Iteration 39 - external-validity claim audit pre-registration

Frozen after the iteration-38 opposite-direction S0 canary proof was committed, and before any
iteration-39 claim ledger, analyzer, proof report, documentation narrowing, sensor-degradation
run, adversarial-perturbation run, independent-planner run, gcloud command, Docker command,
iteration-38 calibration replay, heldout replay, selector evaluation, or closed-loop work.

Iteration 39 is a scientific-governance audit, not a new mechanism or benchmark run. The campaign
already has a stable UniAD benchmark result, a VAD split transfer verdict, a full-trainval
diagnostic localization result, and multiple intervention calibration nulls. The next highest-value
question is whether the active paper/repository story states those results at the defensible scope
or quietly implies external validity that has not been tested.

This audit is intentionally hostile. A claim that must be narrowed is a successful outcome if it
prevents a stronger-looking but weaker paper.

## Research question

Using only committed evidence and active story documents, do Sentinel's current claims survive an
external-validity and falsification audit across planner transfer, scenario scope, distribution
shift, sensor/input degradation, adversarial perturbation, calibration stability, intervention
latency/cost, and deployment trade-offs?

Acceptable positive claim if every bar passes:

> The repository's active story is aligned with the evidence: Sentinel is a closed-loop UniAD
> NeuroNCAP benchmark-scale runtime-assurance result with documented limits, including a VAD
> safety-only/selectivity-failed transfer verdict, a full14 deployment-metric tight null, and no
> untested planner-general, sensor-robust, adversarially robust, deployment-ready, or causal
> intervention claim.

Acceptable negative claim if any overclaim bar fails:

> The current story contains one or more unsupported external-validity or deployment implications.
> Those claims must be narrowed in the active docs before any new GPU/model run is launched.

Forbidden claims, even on a pass:

- no claim that Sentinel is planner-agnostic;
- no claim that VAD selectivity transferred;
- no claim that the monitor is robust to sensor degradation, adversarial perturbation, other
  weather/lighting domains, other datasets, or other UniAD checkpoints;
- no claim that any iteration-30 through iteration-38 activation intervention improves
  closed-loop safety;
- no claim that iteration 38 passed calibration or heldout;
- no deployment-readiness, production-safety, certification, or real-vehicle claim;
- no claim that this audit itself creates new empirical external-validity evidence.

## Frozen input artifacts

Iteration 39 may read only committed source, proof, and documentation artifacts:

- `README.md`;
- `docs/REPORT.md`;
- `docs/CAMPAIGN.md`;
- `docs/NEXT_PHASE.md`;
- `docs/paper/MANUSCRIPT.md`;
- `experiments/VERIFICATION.md`;
- `experiments/iter2_monitor/G1_RESULT.md`;
- `experiments/iter2_monitor/RESULT.md`;
- `experiments/iter3_progress/RESULT.md`;
- `experiments/iter8_union/RESULT.md`;
- `experiments/union_validation/RESULT.md`;
- `experiments/iter9_evade/RESULT.md`;
- `experiments/iter10_brakevade/RESULT.md`;
- `experiments/iter11_early_evade/RESULT.md`;
- `experiments/iter12_plan_selection/RESULT.md`;
- `experiments/iter13_rss_baseline/RESULT.md`;
- `experiments/vad_generalization/RESULT.md`;
- `experiments/full14_benchmark/RESULT.md`;
- `experiments/iter15_latch_release/RESULT.md`;
- `experiments/iter16_soft_stop/RESULT.md`;
- `experiments/full14_power/RESULT.md`;
- `experiments/iter17_threat_routing/RESULT.md`;
- `experiments/iter18_tracker/RESULT.md`;
- `experiments/iter19_diversity_head/RESULT.md`;
- `experiments/iter20_vad_tracker_portability/RESULT.md`;
- `experiments/iter21_bev_diversity_head/RESULT.md`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`;
- `experiments/iter31_full_trainval_bridge_intervention/RESULT.md`;
- `experiments/iter32_prefix_replay_baseline_recovery/RESULT.md`;
- `experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md`;
- `experiments/iter34_direction_specificity_audit/RESULT.md`;
- `experiments/iter35_response_heterogeneity_audit/RESULT.md`;
- `experiments/iter36_bridge_site_decomposition/RESULT.md`;
- `experiments/iter37_track_query_site_intervention/RESULT.md`;
- `experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md`;
- `experiments/iter38_track_query_opposite_direction/proof-direction/direction_report.json`;
- `experiments/iter38_track_query_opposite_direction/proof-canary/canary_report.json`.

Iteration 39 must not read uncommitted working-tree content as evidence, remote GPU files,
iteration-12 raw evaluation frames beyond committed published summaries, unpublished
iteration-38 calibration output, external web sources, or any new model output.

## Claim ledger

The audit must create a structured claim ledger before producing a RESULT. Every ledger row must
have:

- `claim_id`;
- `claim_text`;
- `evidence_paths`;
- `scope`;
- `evidence_status`, one of `established`, `split`, `null`, `diagnostic`, `active_gate`,
  `untested`, or `unsupported`;
- `external_validity_status`, one of `within_scope`, `split_limited`, `failed_transfer`,
  `diagnostic_only`, `active_not_result`, or `untested`;
- `permitted_wording`;
- `forbidden_wording`;
- `next_falsifier`.

At minimum, the ledger must cover these claim families:

1. UniAD introspective collision prediction;
2. released-union closed-loop benchmark improvement on the complete official 14-scene set;
3. deployment metric and safe-progress;
4. frontal-head-on mitigation versus prevention;
5. RSS/formal-envelope baseline;
6. VAD independent-planner transfer;
7. planner-native candidate diversity / plan-B availability;
8. full-trainval representation localization;
9. activation-intervention status across iterations 31-38;
10. sensor/input degradation;
11. adversarial perturbation;
12. calibration stability;
13. intervention latency/cost;
14. deployment trade-offs.

## S0 - evidence and status integrity

Before any wording audit:

- every frozen input path above must exist;
- every frozen input path must be committed in `git ls-files`;
- `scripts/validate_docs.py` must pass before audit interpretation;
- iteration 37 must be recorded as a calibration null, not as a pass;
- iteration 38 must be recorded as S0-canary-only, with calibration not launched;
- no Docker, gcloud, GPU, model, heldout, selector, or closed-loop command may run.

If any S0 bar fails, publish an infrastructure/null result and stop before claim interpretation.

## S1 - claim-ledger completeness bars

The ledger passes S1 only if:

- all 14 required claim families appear exactly once or as explicitly numbered subclaims;
- every claim has at least one evidence path, except `untested` claims, which must list the
  evidence gap instead;
- every non-untested evidence path exists and is committed;
- every claim has a permitted-wording boundary and at least one forbidden-wording boundary;
- every claim names a strongest next falsifier;
- no claim uses `established` outside the frozen evidence scope stated in its row.

If S1 fails, publish a claim-ledger-null result. No documentation narrowing or next-experiment
selection is authorized until the ledger is repaired under a fresh commit.

## S2 - hostile external-validity classification bars

S2 passes only if the ledger classifies the strongest skeptical reading correctly:

- independent-planner transfer must be `split` or stricter: VAD safety transfer may be credited,
  but VAD selectivity must be marked `failed_transfer`;
- full14 deployment safe-progress must be marked a tight null or neutral result, not a benchmark
  deployment win;
- mini-scene safe-progress may be marked established only at mini-scene scope;
- full-trainval representation localization must be `diagnostic`, not causal or safety evidence;
- iterations 31, 33, and 37 must be calibration/infrastructure nulls;
- iteration 38 must be `active_gate`, not a result beyond S0 canary;
- sensor/input degradation, adversarial perturbation, calibration stability beyond the frozen
  alpha grids, latency/cost, and deployment trade-offs must be `untested` unless a committed
  result path directly supports the claim.

If any classification is looser than these bars, publish an external-validity overclaim null and
require documentation narrowing before any new GPU work.

## S3 - active-document overclaim bars

The analyzer must inspect only the active story documents:

- `README.md`;
- `docs/REPORT.md`;
- `docs/paper/MANUSCRIPT.md`.

S3 passes only if those documents avoid unsupported broad wording. The audit must flag and fail on
active text that, without a nearby limitation, implies:

- planner-agnostic deployment (`planner-agnostic`, `any planner`, `all planners`, or equivalent);
- plug-in transfer without qualification (`plug-and-play` when not scoped to the tested planner or
  immediately limited by the VAD split verdict);
- deployment-positive benchmark result despite the full14/power tight null;
- production or certification readiness;
- sensor-degradation or adversarial robustness;
- activation-intervention, selector, or closed-loop safety success from iterations 30-38.

If S3 fails, the RESULT must include the exact active-doc locations and the same state change must
narrow those docs before GPU/model work resumes. Historical RESULT files may retain old language
only when a later correction is already on the record; active story documents do not get that
exception.

## S4 - next falsification selector

If S0-S3 pass after any required narrowing, the audit must choose the next primary scientific
objective by expected defensibility, not by expected benchmark gain. The selector may recommend
iteration-38 calibration only if it explicitly states why that mechanism question is more
scientifically valuable than the highest-priority external-validity falsifier.

Default ordering under the current evidence should be:

1. active-doc claim narrowing if S3 fails;
2. an offline latency/intervention-cost audit over committed decision logs;
3. a sensor/input-degradation or scenario-shift stress pre-registration for the released union;
4. an independent-planner transfer successor only if it names a concrete track-quality mechanism
   and passes an offline gate before closed-loop work;
5. iteration-38 calibration only as a narrow causal-handle question, not as the campaign's primary
   scientific direction.

## Named falsifiers

- **Evidence drift.** Required committed evidence or active docs are missing, untracked, or fail
  the docs guard.
- **Ledger incompleteness.** A required claim family or falsifier is absent.
- **Scope inflation.** A claim is marked established beyond the evidence that supports it.
- **Planner-transfer overclaim.** VAD safety transfer is reported without the selectivity failure
  and tracking-quality dependency.
- **Deployment overclaim.** The full14/power deployment metric is reported as a win instead of a
  tight null.
- **Diagnostic-to-causal leap.** Representation localization or S0 canary evidence is treated as
  intervention, selector, closed-loop, deployment, or safety evidence.
- **Untested robustness claim.** Sensor degradation, adversarial perturbation, latency/cost,
  calibration stability, or deployment trade-offs are implied as established.
- **GPU leakage.** Any model/GPU/closed-loop work runs before this offline audit is published.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/claim_ledger.json`;
- `proof-audit/external_validity_report.json`;
- `proof-audit/local_verification.txt`;
- S0/S1/S2/S3/S4 pass/fail tables with every failed bar listed;
- active-doc overclaim findings, including path and line number;
- documentation narrowing diff summary if S3 fails;
- final next-falsification recommendation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing the ledger, analyzer, proof report, or doc
   narrowing.
2. Commit analyzer code and tests before producing the audit report.
3. Run the audit once on committed inputs.
4. Publish `RESULT.md` at full weight whether the audit passes or fails.
5. If active-doc narrowing is required, make it in the same published state before any
   GPU/model/closed-loop work resumes.
6. Iteration-38 calibration remains allowed by its own pre-registration but is deliberately paused
   behind this audit's defensibility decision.
