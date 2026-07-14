# Iteration 125 - support-core blind-spot scenario design: SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE

Status: `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE` (offline design surface over the
committed HUGSIM support-core two-track taxonomy).

This iteration used only committed markdown/json result surfaces. It read no raw decision logs,
launched no GPU work, reran no analyzer over raw HUGSIM artifacts, changed no thresholds, changed
no planner/action-control code, changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Generator/verifier:
  [`generate_support_core_blind_spot_design.py`](generate_support_core_blind_spot_design.py)
- Tests:
  [`../../tests/test_iter125_support_core_blind_spot_design.py`](../../tests/test_iter125_support_core_blind_spot_design.py)
- Generator command:
  [`proof-design/generate_support_core_blind_spot_design.command.txt`](proof-design/generate_support_core_blind_spot_design.command.txt)
- JSON report:
  [`proof-design/support_core_blind_spot_scenario_design_report.json`](proof-design/support_core_blind_spot_scenario_design_report.json)
- Markdown report:
  [`proof-design/support_core_blind_spot_scenario_design.md`](proof-design/support_core_blind_spot_scenario_design.md)
- Design note:
  [`../../docs/research/SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md`](../../docs/research/SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md)

## Result

The generator returned `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE` with zero problems:

- source rows: `8`;
- covered rows: `8`;
- archetypes: `5`;
- duplicate covered slots: `0`;
- missing covered slots: `0`;
- synthesis-label coverage:
  - `two_track_never_supported_selected_nearest`: `1`;
  - `two_track_post_fire_support_selected_nearest`: `2`;
  - `two_track_pre_support_drifted_selected_not_nearest`: `1`;
  - `two_track_pre_support_lost_absent_selected_nearest`: `2`;
  - `two_track_pre_support_lost_absent_selected_not_nearest`: `2`;
- selected-rank archetypes:
  - `selected_nearest`: `3`;
  - `selected_not_nearest`: `2`;
- timing-gap archetypes:
  - `measured_support_gap`: `3`;
  - `post_fire_support`: `1`;
  - `no_pre_fire_support`: `1`.

The five design archetypes are:

1. `blindspot_never_supported_selected_nearest`;
2. `blindspot_post_fire_support_selected_nearest`;
3. `blindspot_pre_support_drifted_selected_not_nearest`;
4. `blindspot_pre_support_lost_absent_selected_nearest`;
5. `blindspot_pre_support_lost_absent_selected_not_nearest`.

Each archetype carries source slots, support-side branch, selected-side branch, selected-rank
condition, timing-gap class, candidate-generation knobs, future validation gates, and forbidden
claims.

## Interpretation

Iteration 125 converts the support-core mechanism taxonomy into a future blind-spot/scenario-design
surface. The design target is the observed two-track split: support evidence appears on one object
or branch, while first fire selects another object that was never supported before collision.

This is not scenario generation and not run approval. A later successor would still need a fresh
pre-registration to freeze candidate source pools, mutation operators, support/provenance gates,
slot manifests, execution controls, and analysis bars before any GPU or HUGSIM run.

## Claim boundary

Design surface only; no scenario-generation execution, GPU launch, HUGSIM run, repair,
actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
