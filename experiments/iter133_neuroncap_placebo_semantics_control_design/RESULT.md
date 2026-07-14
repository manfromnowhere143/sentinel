# Iteration 133 - NeuroNCAP placebo semantics control design: NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE

Status: `NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE` (offline adversarial-control design
preflight for a future NeuroNCAP placebo/sham semantics test).

This iteration used only committed markdown/json result surfaces. It read no raw uncommitted box
state, launched no GPU work, ran no NeuroNCAP or HUGSIM episode, generated no scenarios, created
no generated artifacts, created no reserved future artifact paths, selected no actual execution
slots for a run, changed no thresholds, changed no planner/action-control code, changed no
benchmark metrics, ran no learning/update step, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Generator/verifier:
  [`generate_neuroncap_placebo_semantics_control_design.py`](generate_neuroncap_placebo_semantics_control_design.py)
- Tests:
  [`../../tests/test_iter133_neuroncap_placebo_semantics_control_design.py`](../../tests/test_iter133_neuroncap_placebo_semantics_control_design.py)
- Generator command:
  [`proof-design/generate_neuroncap_placebo_semantics_control_design.command.txt`](proof-design/generate_neuroncap_placebo_semantics_control_design.command.txt)
- JSON report:
  [`proof-design/neuroncap_placebo_semantics_control_design_report.json`](proof-design/neuroncap_placebo_semantics_control_design_report.json)
- Markdown report:
  [`proof-design/neuroncap_placebo_semantics_control_design.md`](proof-design/neuroncap_placebo_semantics_control_design.md)
- Design note:
  [`../../docs/research/NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_2026-07-14.md`](../../docs/research/NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_2026-07-14.md)

## Result

The generator returned `NEURONCAP_PLACEBO_SEMANTICS_CONTROL_DESIGN_COMPLETE` with zero problems:

- primary placebo arms: `1`;
- primary placebo arm: `semantics_scrambled_budget_matched_placebo`;
- future arms: `3` (`off_baseline`, `released_union_semantic_reference`, and the placebo arm);
- future verdict classes: `4`;
- semantic trigger leaks: `0`;
- true authorization flags: `0`;
- GPU authorized: `False`;
- NeuroNCAP execution authorized: `False`;
- HUGSIM execution authorized: `False`;
- source problem count: `0`.

The frozen source anchors are:

- full-power NeuroNCAP result: `799` measured episodes, released-union NCAP delta `+0.783` with
  CI `[+0.605, +0.928]`, and safe-progress delta `-0.032` with CI `[-0.127, +0.065]`;
- iteration-13 RSS-style baseline: same observed kinematics and same latched-stop actuator as the
  union, isolating the decision rule, with union-minus-RSS safe-progress `+1.345` and CI
  `[+0.944, +1.701]`;
- iteration-50 opportunity audit: `A1_CONFIRMED`, Spearman rho `+0.7003`, and the NeuroNCAP
  benefit concentrates where OFF-arm collision opportunity exists.

## Interpretation

Iteration 133 turns the external critique into a falsifiable future-control protocol. The primary
placebo preserves the released union's latched-stop/release actuator family and matches
intervention timing/budget by deterministic donor schedules, while forbidding live Sentinel risk
score use, planner-risk introspection, observed-closing-TTC triggers, plan-vs-path-CPA triggers,
learned prediction, and outcome feedback. Donors must exclude the target scenario pair and target
seed.

The future execution question is now sharp: if the released union beats the placebo under the
frozen NCAP comparison, the semantics claim survives. If the placebo explains the gain, the
headline must be downgraded toward generic braking/timing. If the placebo harms or gives no
benefit, that null is published. No execution is authorized by this design result.

## Claim boundary

Placebo-semantics control design only; no GPU launch, NeuroNCAP execution, HUGSIM execution,
reserved path creation, generated scenario artifact, scenario generation, execution-slot
selection, learning/update step, repair, actor-causality, threshold-value, transfer upgrade,
safety, deployment, robustness, benchmark-ranking, population-rate, HD-Score-invariance,
real-world behavior, first-responder behavior, acquisition-value, retuning, production,
commercial claim, or frontier-stack equivalence claim.
