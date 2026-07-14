# Iteration 126 - support-core candidate-generation manifest preflight

Verdict: `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE`

## Summary

- `archetype_count`: `5`
- `candidate_count`: `10`
- `candidates_per_archetype`: `{'blindspot_never_supported_selected_nearest': 2, 'blindspot_post_fire_support_selected_nearest': 2, 'blindspot_pre_support_drifted_selected_not_nearest': 2, 'blindspot_pre_support_lost_absent_selected_nearest': 2, 'blindspot_pre_support_lost_absent_selected_not_nearest': 2}`
- `candidate_role_counts`: `{'branch_stress': 5, 'counterfactual_control': 5}`
- `role_pair_complete_count`: `5`
- `source_slot_count`: `8`
- `covered_source_slot_count`: `8`
- `missing_source_slot_count`: `0`
- `mutation_family_counts`: `{'introduce_pre_fire_support_reference_control': 1, 'post_fire_support_delay_pressure': 1, 'same_object_visibility_continuity_control': 2, 'shift_post_fire_evidence_to_pre_fire_control': 1, 'support_band_border_continuity_control': 1, 'support_drift_outside_band_sweep': 1, 'support_loss_gap_sweep': 2, 'unsupported_nearest_reference_pressure': 1}`
- `true_authorization_count`: `0`
- `generated_scenario_path_count`: `0`
- `launch_command_count`: `0`
- `metric_or_threshold_change_instruction_count`: `0`
- `missing_required_content_count`: `0`

## Candidate specs

### `scbs_001_branch_stress_blindspot_never_supported_selected_nearest`

- archetype: `blindspot_never_supported_selected_nearest`
- role: `branch_stress`
- mutation family: `unsupported_nearest_reference_pressure`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- source scenarios: `['scene-0038-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest`

- archetype: `blindspot_never_supported_selected_nearest`
- role: `counterfactual_control`
- mutation family: `introduce_pre_fire_support_reference_control`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- source scenarios: `['scene-0038-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest`

- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `branch_stress`
- mutation family: `post_fire_support_delay_pressure`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- source scenarios: `['scene-0038-extreme-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest`

- archetype: `blindspot_post_fire_support_selected_nearest`
- role: `counterfactual_control`
- mutation family: `shift_post_fire_evidence_to_pre_fire_control`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- source scenarios: `['scene-0038-extreme-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest`

- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_drift_outside_band_sweep`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- source scenarios: `['scene-0411-extreme-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest`

- archetype: `blindspot_pre_support_drifted_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `support_band_border_continuity_control`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- source scenarios: `['scene-0411-extreme-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- source scenarios: `['scene-0411-extreme-00', 'scene-0411-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- source scenarios: `['scene-0411-extreme-00', 'scene-0411-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `branch_stress`
- mutation family: `support_loss_gap_sweep`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- source scenarios: `['scene-0383-extreme-00', 'scene-0411-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

### `scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest`

- archetype: `blindspot_pre_support_lost_absent_selected_not_nearest`
- role: `counterfactual_control`
- mutation family: `same_object_visibility_continuity_control`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- source scenarios: `['scene-0383-extreme-00', 'scene-0411-hard-00']`
- execution authorized: `False`
- GPU authorized: `False`
- HUGSIM run authorized: `False`
- required gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution
  - candidate-manifest gate: this row is a symbolic future candidate spec only
  - fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md
  - authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false
  - no-generated-path gate: candidate records no generated scenario path
  - no-launch-command gate: candidate records no launch command
  - no-threshold-change gate: thresholds and metrics remain frozen
  - paired-role gate: each archetype has one branch_stress and one counterfactual_control spec

## Boundary

manifest preflight only; no scenario-generation execution, GPU launch, HUGSIM run, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
