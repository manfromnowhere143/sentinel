# Iteration 133 - NeuroNCAP placebo semantics control design

Frozen after iteration 132 and its handoff were published. Frozen before any iteration-133
generator/verifier, placebo-control design report, proof artifact, result, README update, or
handoff refresh.

This is an offline adversarial-control design preflight over committed NeuroNCAP and audit
surfaces. It may create proof artifacts that define a future placebo/sham control protocol,
matching rules, falsifiers, verdict classes, and launch-manifest requirements. It must not launch
GPU work, run NeuroNCAP, run HUGSIM, create generated scenario artifacts, create reserved future
artifact paths, select actual execution slots for a run, inspect raw uncommitted box state, change
Sentinel thresholds, change planner/action code, change benchmark metrics, run learning/update
steps, repair Sentinel, retune Sentinel, or upgrade any empirical claim.

## Frozen question

Can the committed evidence be converted into a deterministic future-run protocol that matches the
released union's actuation opportunity and intervention budget while removing load-bearing
introspective risk semantics, so a later separately approved NeuroNCAP experiment can distinguish
semantic monitoring value from generic braking/timing artifacts?

## Frozen inputs

- Full-power NeuroNCAP result:
  `experiments/full14_power/RESULT.md`
- Full-power NeuroNCAP hypothesis:
  `experiments/full14_power/HYPOTHESIS.md`
- Full-power analyzer:
  `experiments/full14_power/analyze_power14.py`
- Iteration 13 RSS-style baseline result:
  `experiments/iter13_rss_baseline/RESULT.md`
- Iteration 50 collision-opportunity audit result:
  `experiments/iter50_collision_opportunity_audit/RESULT.md`
- Iteration 50 collision-opportunity report:
  `experiments/iter50_collision_opportunity_audit/proof-audit/opportunity_report.json`
- Iteration 132 result and current handoff:
  `experiments/iter132_support_core_schema_instance_creation_preflight/RESULT.md`,
  `HANDOFF.md`

## Success bars

S0 source-integrity pass:

- the full-power result states `799` measured episodes, `20` seed-paired runs per pair except the
  recorded `off/side-0921` `n=19` exception, H-P0 pass, NCAP `+0.783` with CI `[+0.605, +0.928]`,
  and safe-progress `-0.032` with CI `[-0.127, +0.065]`;
- the iteration-13 result states that the RSS-style envelope used the same observed kinematics and
  same latched-stop actuator while isolating the decision rule, and that union minus RSS
  safe-progress was `+1.345` with CI `[+0.944, +1.701]`;
- the iteration-50 result/report state `A1_CONFIRMED`, NeuroNCAP Spearman rho `+0.7003`, and that
  NeuroNCAP benefit concentrates where OFF-arm collision opportunity exists;
- the iteration-132 result and handoff state that iterations 125-132 are evidence infrastructure
  only and do not upgrade the empirical claim.

S1 placebo-control protocol pass:

- exactly one primary future placebo arm is defined: `semantics_scrambled_budget_matched_placebo`;
- the placebo arm uses no live Sentinel risk score, no planner-risk introspection, no observed
  closing-TTC trigger, no plan-vs-path CPA trigger, no learned predictor, and no outcome feedback;
- the placebo arm preserves the future actuator family as the released union's threat-cleared
  latched stop/release actuator;
- the placebo arm matches intervention budget by scenario class and run index using only a
  deterministic donor schedule from committed released-union logs or a future launch manifest;
- donor selection must exclude the target scenario pair and target seed, and must be deterministic
  from committed identifiers;
- intervention windows must be replayed as timing/budget windows only, not as risk decisions.

S2 matching and leakage controls pass:

- the protocol freezes seed-pairing, scene-pair identity, class-level matching, donor exclusion,
  actuator budget matching, no-hidden-tuning, and one-pass analyzer reuse;
- the future run must include OFF, released union, and placebo arms under the same frozen planner,
  benchmark stack, route/scenario list, and run-index discipline;
- any future launch manifest must hash-bind scenario ids, run indices, donor schedule ids, actuator
  budget summaries, patch files, analyzer files, and environment receipts before execution;
- the placebo schedule must not be selected using ON-arm outcome, future placebo outcome, or
  post-run metric feedback.

S3 verdict-class pass:

- the design freezes at least four future verdict classes:
  `SEMANTIC_VALUE_CONFIRMED`, `PLACEBO_EXPLAINS_GAIN`, `PLACEBO_HARM_OR_NULL`, and
  `PLACEBO_CONTROL_INFRA_NULL`;
- the primary future comparison is released-union NCAP minus placebo NCAP under the same
  scenario-clustered bootstrap discipline used by the full-power analyzer;
- safe-progress remains a first-class secondary/deployment metric and cannot be hidden by a
  benchmark-score win;
- nulls must be published at full weight.

S4 run-boundary pass:

- the verifier verdict is exactly `NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE`;
- the generated report states that Iter133 authorizes no GPU launch, NeuroNCAP run, HUGSIM run,
  scenario generation, reserved artifact creation, metric change, threshold change, learning/update
  step, repair claim, safety claim, deployment claim, production claim, commercial claim, or claim
  that Sentinel matches or exceeds any frontier autonomy stack;
- a later execution step still requires a fresh `HYPOTHESIS.md`, explicit operator approval for GPU
  use, and a launch manifest that passes the frozen design checks.

## Falsifiers

Return `NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_INFRA_NULL` if any frozen input is missing or
malformed; any required source fact is absent; the primary placebo arm is missing or more than one
primary placebo arm is declared; any placebo trigger uses live Sentinel risk semantics, TTC, CPA,
planner-risk introspection, learned prediction, or outcome feedback; donor exclusion is missing;
budget matching is not deterministic; future verdict classes are incomplete; the safe-progress
secondary metric is absent; any text authorizes GPU launch, NeuroNCAP execution, HUGSIM execution,
generated artifact creation, reserved path creation, threshold/metric/planner-code changes,
learning/update, repair, safety, deployment, benchmark-ranking, real-world, production,
commercial, acquisition-value, or frontier-stack equivalence claims.

## Required proof artifacts

- generator/verifier source plus unit tests;
- `proof-design/neuroncap_placebo_semantics_control_design_report.json`;
- `proof-design/neuroncap_placebo_semantics_control_design.md`;
- `proof-design/generate_neuroncap_placebo_semantics_control_design.command.txt`;
- placebo-control design note under `docs/research/`;
- published `RESULT.md`;
- README, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, and `HANDOFF.md` updates after success.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and note writer; run focused ruff/tests and docs guard.
3. Run the generator/verifier once.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Claim boundary

Placebo-semantics control design only; no GPU launch, NeuroNCAP execution, HUGSIM execution,
reserved path creation, generated scenario artifact, scenario generation, execution-slot
selection, learning/update step, repair, actor-causality, threshold-value, transfer upgrade,
safety, deployment, robustness, benchmark-ranking, population-rate, HD-Score-invariance,
real-world behavior, first-responder behavior, acquisition-value, retuning, production,
commercial claim, or frontier-stack equivalence claim.
