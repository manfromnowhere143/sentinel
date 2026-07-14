# HUGSIM support-core candidate-generation manifest

Status: iteration-126 manifest preflight note. This is a symbolic future-candidate
manifest only; it authorizes no scenario generation, HUGSIM run, GPU launch, retuning,
repair, safety, deployment, benchmark, population-rate, production, or commercial claim.

## Source

- Iteration 125 design proof:
  [`support_core_blind_spot_scenario_design_report.json`](../../experiments/iter125_support_core_blind_spot_scenario_design/proof-design/support_core_blind_spot_scenario_design_report.json)
- Iteration 125 design note:
  [`SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md`](SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md)
- Iteration 126 proof:
  [`support_core_candidate_manifest_report.json`](../../experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json)

## Manifest Rule

Each registered iteration-125 archetype receives exactly two future symbolic candidates:
`branch_stress` and `counterfactual_control`. The first preserves observed branch
pressure; the second freezes the paired future control idea. Both remain inert until a
later pre-registration authorizes generation or execution.

## Candidate Families

### `scbs_001_branch_stress_blindspot_never_supported_selected_nearest`

- archetype: `blindspot_never_supported_selected_nearest`
- role: `branch_stress`
- mutation family: `unsupported_nearest_reference_pressure`
- timing class: `no_pre_fire_support`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest`

- archetype: `blindspot_never_supported_selected_nearest`
- role: `counterfactual_control`
- mutation family: `introduce_pre_fire_support_reference_control`
- timing class: `no_pre_fire_support`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest`

- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `branch_stress`
- mutation family: `post_fire_support_delay_pressure`
- timing class: `post_fire_support`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest`

- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `counterfactual_control`
- mutation family: `shift_post_fire_evidence_to_pre_fire_control`
- timing class: `post_fire_support`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest`

- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_drift_outside_band_sweep`
- timing class: `measured_support_gap`
- selected rank condition: `selected_not_nearest`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest`

- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `support_band_border_continuity_control`
- timing class: `measured_support_gap`
- selected rank condition: `selected_not_nearest`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- timing class: `measured_support_gap`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- timing class: `measured_support_gap`
- selected rank condition: `selected_nearest`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- timing class: `measured_support_gap`
- selected rank condition: `selected_not_nearest`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

### `scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- timing class: `measured_support_gap`
- selected rank condition: `selected_not_nearest`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`

## Future Gates

- freeze candidate source pool and mutation operators before scenario generation
- preserve branch_stress and counterfactual_control pairing by archetype
- define destination paths and duplicate handling by candidate_id and slot_id
- keep thresholds, HUGSIM metrics, planner code, and runtime code unchanged unless a later hypothesis explicitly authorizes a separate intervention
- separate manifest preflight, generation, execution, and analysis into distinct pre-registered iterations

## Claim Boundary

manifest preflight only; no scenario-generation execution, GPU launch, HUGSIM run, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
