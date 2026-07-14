# Iteration 125 - support-core blind-spot scenario design

Verdict: `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE`

## Summary

- `row_count`: `8`
- `covered_row_count`: `8`
- `archetype_count`: `5`
- `synthesis_label_counts`: `{'two_track_never_supported_selected_nearest': 1, 'two_track_post_fire_support_selected_nearest': 2, 'two_track_pre_support_drifted_selected_not_nearest': 1, 'two_track_pre_support_lost_absent_selected_nearest': 2, 'two_track_pre_support_lost_absent_selected_not_nearest': 2}`
- `selected_rank_condition_counts`: `{'selected_nearest': 3, 'selected_not_nearest': 2}`
- `timing_gap_class_counts`: `{'measured_support_gap': 3, 'no_pre_fire_support': 1, 'post_fire_support': 1}`
- `duplicate_covered_slot_count`: `0`
- `missing_covered_slot_count`: `0`

## Archetypes

### `blindspot_never_supported_selected_nearest`

- synthesis label: `two_track_never_supported_selected_nearest`
- source rows: `1`
- support side: `never_supported_reference`
- selected side: `selected_never_supported_before_collision`
- selected rank: `selected_nearest`
- timing class: `no_pre_fire_support`
- source slots: `['i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1']`
- candidate-generation knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - no-support reference control: require zero pre-fire support evidence for the reference branch
  - nearest-decoy pressure: make the selected first-fire object nearest while still unsupported
  - nearest unsupported decoy: make the selected object nearest but still unsupported
- future validation gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution

### `blindspot_post_fire_support_selected_nearest`

- synthesis label: `two_track_post_fire_support_selected_nearest`
- source rows: `2`
- support side: `post_fire_support_only`
- selected side: `selected_never_supported_before_collision`
- selected rank: `selected_nearest`
- timing class: `post_fire_support`
- source slots: `['i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1', 'i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2']`
- candidate-generation knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - post-fire provenance delay: shift support evidence from after fire toward pre-fire
  - different-object versus far-support split: preserve both observed post-fire support subtypes
  - nearest unsupported decoy: make the selected object nearest but still unsupported
- future validation gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution

### `blindspot_pre_support_drifted_selected_not_nearest`

- synthesis label: `two_track_pre_support_drifted_selected_not_nearest`
- source rows: `1`
- support side: `pre_fire_support_drifted_outside_support`
- selected side: `selected_never_supported_before_collision`
- selected rank: `selected_not_nearest`
- timing class: `measured_support_gap`
- source slots: `['i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1']`
- candidate-generation knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object drift vector: sweep lateral/longitudinal drift outside the frozen support band
  - support-band border control: paired variant at the support threshold without changing thresholds
  - rank competition: keep the selected object non-nearest while another object is closer
  - measured support-gap band: preserve the observed last-support-to-fire gap range
- future validation gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution

### `blindspot_pre_support_lost_absent_selected_nearest`

- synthesis label: `two_track_pre_support_lost_absent_selected_nearest`
- source rows: `2`
- support side: `pre_fire_support_lost_absent_at_fire`
- selected side: `selected_never_supported_before_collision`
- selected rank: `selected_nearest`
- timing class: `measured_support_gap`
- source slots: `['i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1', 'i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2']`
- candidate-generation knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object disappearance timing: sweep last-presence-to-fire and last-support-to-fire gaps
  - same-object continuity control: paired variant where the early support object remains visible
  - nearest unsupported decoy: make the selected object nearest but still unsupported
  - measured support-gap band: preserve the observed last-support-to-fire gap range
- future validation gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution

### `blindspot_pre_support_lost_absent_selected_not_nearest`

- synthesis label: `two_track_pre_support_lost_absent_selected_not_nearest`
- source rows: `2`
- support side: `pre_fire_support_lost_absent_at_fire`
- selected side: `selected_never_supported_before_collision`
- selected rank: `selected_not_nearest`
- timing class: `measured_support_gap`
- source slots: `['i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2', 'i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2']`
- candidate-generation knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object disappearance timing: sweep last-presence-to-fire and last-support-to-fire gaps
  - same-object continuity control: paired variant where the early support object remains visible
  - rank competition: keep the selected object non-nearest while another object is closer
  - measured support-gap band: preserve the observed last-support-to-fire gap range
- future validation gates:
  - frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool
  - provenance gate: candidate must expose collision_provenance before actor-support classification
  - two-track gate: selected first-fire object remains never-supported before collision
  - branch-reproduction gate: candidate reproduces exactly one registered support-side branch
  - duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario
  - no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged
  - claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution

## Boundary

design surface only; no scenario-generation execution, GPU launch, HUGSIM run, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
