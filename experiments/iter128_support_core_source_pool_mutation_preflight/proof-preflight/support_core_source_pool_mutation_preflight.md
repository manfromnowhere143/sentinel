# Iteration 128 - support-core source-pool and mutation-operator preflight

Verdict: `SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_COMPLETE`

## Summary

- `candidate_count`: `10`
- `archetype_count`: `5`
- `candidate_role_counts`: `{'branch_stress': 5, 'counterfactual_control': 5}`
- `source_pool_count`: `10`
- `mutation_operator_count`: `8`
- `candidate_operator_binding_count`: `10`
- `unique_mutation_family_count`: `8`
- `candidate_without_source_pool_count`: `0`
- `candidate_without_operator_binding_count`: `0`
- `multi_binding_candidate_count`: `0`
- `source_slot_count`: `8`
- `covered_source_slot_count`: `8`
- `missing_source_slot_count`: `0`
- `mutation_family_counts`: `{'introduce_pre_fire_support_reference_control': 1, 'post_fire_support_delay_pressure': 1, 'same_object_visibility_continuity_control': 2, 'shift_post_fire_evidence_to_pre_fire_control': 1, 'support_band_border_continuity_control': 1, 'support_drift_outside_band_sweep': 1, 'support_loss_gap_sweep': 2, 'unsupported_nearest_reference_pressure': 1}`
- `true_authorization_count`: `0`
- `missing_preflight_content_count`: `0`
- `forbidden_key_count`: `0`

## Source pools

### `scsp_001_scbs_001_branch_stress_blindspot_never_supported_selected_nearest`

- candidate: `scbs_001_branch_stress_blindspot_never_supported_selected_nearest`
- archetype: `blindspot_never_supported_selected_nearest`
- role: `branch_stress`
- mutation family: `unsupported_nearest_reference_pressure`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- source scenarios: `['scene-0038-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_002_scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest`

- candidate: `scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest`
- archetype: `blindspot_never_supported_selected_nearest`
- role: `counterfactual_control`
- mutation family: `introduce_pre_fire_support_reference_control`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- source scenarios: `['scene-0038-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_003_scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest`

- candidate: `scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest`
- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `branch_stress`
- mutation family: `post_fire_support_delay_pressure`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- source scenarios: `['scene-0038-extreme-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_004_scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest`

- candidate: `scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest`
- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `counterfactual_control`
- mutation family: `shift_post_fire_evidence_to_pre_fire_control`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- source scenarios: `['scene-0038-extreme-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_005_scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest`

- candidate: `scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest`
- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_drift_outside_band_sweep`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- source scenarios: `['scene-0411-extreme-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_006_scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest`

- candidate: `scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest`
- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `support_band_border_continuity_control`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- source scenarios: `['scene-0411-extreme-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_007_scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest`

- candidate: `scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest`
- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- source scenarios: `['scene-0411-extreme-00', 'scene-0411-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_008_scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest`

- candidate: `scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest`
- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- source scenarios: `['scene-0411-extreme-00', 'scene-0411-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_009_scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest`

- candidate: `scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest`
- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- source scenarios: `['scene-0383-extreme-00', 'scene-0411-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

### `scsp_010_scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest`

- candidate: `scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest`
- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- source scenarios: `['scene-0383-extreme-00', 'scene-0411-hard-00']`
- scenario generation authorized: `False`
- HUGSIM run authorized: `False`

## Mutation operators

### `scop_introduce_pre_fire_support_reference_control`

- mutation family: `introduce_pre_fire_support_reference_control`
- operator kind: `counterfactual_pre_fire_support_reference`
- allowed controls:
  - symbolically define paired pre-fire support reference control
  - preserve source candidate and scenario identity
  - record future checks for support continuity before first fire
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_post_fire_support_delay_pressure`

- mutation family: `post_fire_support_delay_pressure`
- operator kind: `branch_stress_post_fire_delay`
- allowed controls:
  - symbolically preserve post-fire support timing pressure
  - preserve selected-nearest condition
  - record future checks for support evidence after first fire
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_same_object_visibility_continuity_control`

- mutation family: `same_object_visibility_continuity_control`
- operator kind: `counterfactual_same_object_visibility_control`
- allowed controls:
  - symbolically define paired same-object visibility continuity control
  - preserve active-surface pressure
  - record future checks for same-object support through first fire
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_shift_post_fire_evidence_to_pre_fire_control`

- mutation family: `shift_post_fire_evidence_to_pre_fire_control`
- operator kind: `counterfactual_post_to_pre_fire_shift`
- allowed controls:
  - symbolically define paired pre-fire evidence timing control
  - preserve active-surface pressure
  - record future checks for support evidence before first fire
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_support_band_border_continuity_control`

- mutation family: `support_band_border_continuity_control`
- operator kind: `counterfactual_support_band_border_control`
- allowed controls:
  - symbolically define paired support-band border continuity control
  - preserve source slot identity
  - record future checks for support continuity at the frozen band
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_support_drift_outside_band_sweep`

- mutation family: `support_drift_outside_band_sweep`
- operator kind: `branch_stress_support_drift_sweep`
- allowed controls:
  - symbolically preserve support drift outside the actor-support band
  - preserve selected-not-nearest competition
  - record future checks for support-band distance margin
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_support_loss_gap_sweep`

- mutation family: `support_loss_gap_sweep`
- operator kind: `branch_stress_support_loss_gap_sweep`
- allowed controls:
  - symbolically preserve measured last-support-to-fire gap pressure
  - preserve selected rank condition from source candidate
  - record future checks for last-presence and last-support gaps
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

### `scop_unsupported_nearest_reference_pressure`

- mutation family: `unsupported_nearest_reference_pressure`
- operator kind: `branch_stress_no_support_reference`
- allowed controls:
  - symbolically preserve no-pre-fire-support reference pressure
  - symbolically preserve selected-nearest condition
  - record future checks for selected object outside actor-support band
- invariants:
  - thresholds remain frozen
  - HUGSIM metrics remain frozen
  - planner code remains frozen
  - runtime monitor code remains frozen
  - candidate_id and source_slot_id provenance remain primary keys
  - result remains pre-generation unless a later HYPOTHESIS.md authorizes generation

## Boundary

source-pool and mutation-operator preflight only; no scenario-generation execution, generated scenario artifact, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
