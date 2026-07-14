# HUGSIM support-core source-pool and mutation-operator preflight

Status: iteration-128 pre-generation note. This freezes source pools and mutation
operators only; it authorizes no scenario generation, generated artifacts, execution
slot selection, HUGSIM run, GPU launch, learning/update step, retuning, repair, safety,
deployment, production, or commercial claim.

## Source

- Iteration 126 candidate manifest:
  [`support_core_candidate_manifest_report.json`](../../experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json)
- Iteration 127 alignment audit:
  [`SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md`](SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md)
- Iteration 128 proof:
  [`support_core_source_pool_mutation_preflight_report.json`](../../experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight/support_core_source_pool_mutation_preflight_report.json)

## Freeze Rule

Each iteration-126 symbolic candidate receives exactly one source pool and exactly one
candidate-to-operator binding. Each unique mutation family receives exactly one frozen
operator. These artifacts remain symbolic until a later pre-registration authorizes
scenario generation.

## Operator Library

### `scop_introduce_pre_fire_support_reference_control`

- mutation family: `introduce_pre_fire_support_reference_control`
- operator kind: `counterfactual_pre_fire_support_reference`
- allowed controls:
  - symbolically define paired pre-fire support reference control
  - preserve source candidate and scenario identity
  - record future checks for support continuity before first fire

### `scop_post_fire_support_delay_pressure`

- mutation family: `post_fire_support_delay_pressure`
- operator kind: `branch_stress_post_fire_delay`
- allowed controls:
  - symbolically preserve post-fire support timing pressure
  - preserve selected-nearest condition
  - record future checks for support evidence after first fire

### `scop_same_object_visibility_continuity_control`

- mutation family: `same_object_visibility_continuity_control`
- operator kind: `counterfactual_same_object_visibility_control`
- allowed controls:
  - symbolically define paired same-object visibility continuity control
  - preserve active-surface pressure
  - record future checks for same-object support through first fire

### `scop_shift_post_fire_evidence_to_pre_fire_control`

- mutation family: `shift_post_fire_evidence_to_pre_fire_control`
- operator kind: `counterfactual_post_to_pre_fire_shift`
- allowed controls:
  - symbolically define paired pre-fire evidence timing control
  - preserve active-surface pressure
  - record future checks for support evidence before first fire

### `scop_support_band_border_continuity_control`

- mutation family: `support_band_border_continuity_control`
- operator kind: `counterfactual_support_band_border_control`
- allowed controls:
  - symbolically define paired support-band border continuity control
  - preserve source slot identity
  - record future checks for support continuity at the frozen band

### `scop_support_drift_outside_band_sweep`

- mutation family: `support_drift_outside_band_sweep`
- operator kind: `branch_stress_support_drift_sweep`
- allowed controls:
  - symbolically preserve support drift outside the actor-support band
  - preserve selected-not-nearest competition
  - record future checks for support-band distance margin

### `scop_support_loss_gap_sweep`

- mutation family: `support_loss_gap_sweep`
- operator kind: `branch_stress_support_loss_gap_sweep`
- allowed controls:
  - symbolically preserve measured last-support-to-fire gap pressure
  - preserve selected rank condition from source candidate
  - record future checks for last-presence and last-support gaps

### `scop_unsupported_nearest_reference_pressure`

- mutation family: `unsupported_nearest_reference_pressure`
- operator kind: `branch_stress_no_support_reference`
- allowed controls:
  - symbolically preserve no-pre-fire-support reference pressure
  - symbolically preserve selected-nearest condition
  - record future checks for selected object outside actor-support band

## Source Pools

- `scsp_001_scbs_001_branch_stress_blindspot_never_supported_selected_nearest` -> `scbs_001_branch_stress_blindspot_never_supported_selected_nearest` using `unsupported_nearest_reference_pressure`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_002_scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest` -> `scbs_002_counterfactual_control_blindspot_never_supported_selected_nearest` using `introduce_pre_fire_support_reference_control`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_003_scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest` -> `scbs_003_branch_stress_blindspot_post_fire_support_selected_nearest` using `post_fire_support_delay_pressure`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_004_scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest` -> `scbs_004_counterfactual_control_blindspot_post_fire_support_selected_nearest` using `shift_post_fire_evidence_to_pre_fire_control`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_005_scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest` -> `scbs_005_branch_stress_blindspot_pre_support_drifted_selected_not_nearest` using `support_drift_outside_band_sweep`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_006_scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest` -> `scbs_006_counterfactual_control_blindspot_pre_support_drifted_selected_not_nearest` using `support_band_border_continuity_control`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_007_scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest` -> `scbs_007_branch_stress_blindspot_pre_support_lost_absent_selected_nearest` using `support_loss_gap_sweep`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_008_scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest` -> `scbs_008_counterfactual_control_blindspot_pre_support_lost_absent_selected_nearest` using `same_object_visibility_continuity_control`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_009_scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest` -> `scbs_009_branch_stress_blindspot_pre_support_lost_absent_selected_not_nearest` using `support_loss_gap_sweep`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.
- `scsp_010_scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest` -> `scbs_010_counterfactual_control_blindspot_pre_support_lost_absent_selected_not_nearest` using `same_object_visibility_continuity_control`; `scenario_generation=false`, `gpu=false`, `hugsim_run=false`.

## Future Gates

- freeze generated artifact naming before any scenario file is created
- freeze destination directories and duplicate handling before any generation run
- carry candidate_id, source_pool_id, source_slot_id, and operator_id into all outputs
- separate scenario generation, execution, analysis, and learning/update into distinct hypotheses
- preserve no-repair/no-safety/no-deployment claim boundary until later evidence proves otherwise

## Claim Boundary

source-pool and mutation-operator preflight only; no scenario-generation execution, generated scenario artifact, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
