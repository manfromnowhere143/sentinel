# HUGSIM support-core blind-spot scenario design

Status: iteration-125 design note. This is a future candidate-generation design surface
only; it authorizes no scenario generation, HUGSIM run, GPU launch, retuning, repair,
safety, deployment, benchmark, population-rate, production, or commercial claim.

## Source

- Source taxonomy: [`SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md`](SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md)
- Iteration 121 synthesis:
  [`RESULT.md`](../../experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md)
- Iteration 125 proof:
  [`support_core_blind_spot_scenario_design_report.json`](../../experiments/iter125_support_core_blind_spot_scenario_design/proof-design/support_core_blind_spot_scenario_design_report.json)

## Design Principle

The design target is the observed two-track split: support evidence appears on one object
or branch, while first fire selects another object that was never supported before
collision. Future candidate generation should vary this object/timing separation before
any execution batch is proposed.

## Archetypes

### `blindspot_never_supported_selected_nearest`

- observed rows: `1`
- source scenarios: `['scene-0038-hard-00']`
- support branch: `never_supported_reference`
- selected branch: `selected_never_supported_before_collision`
- selected rank condition: `selected_nearest`
- timing-gap class: `no_pre_fire_support`
- knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - no-support reference control: require zero pre-fire support evidence for the reference branch
  - nearest-decoy pressure: make the selected first-fire object nearest while still unsupported
  - nearest unsupported decoy: make the selected object nearest but still unsupported

### `blindspot_post_fire_support_selected_nearest`

- observed rows: `2`
- source scenarios: `['scene-0038-extreme-00']`
- support branch: `post_fire_support_only`
- selected branch: `selected_never_supported_before_collision`
- selected rank condition: `selected_nearest`
- timing-gap class: `post_fire_support`
- knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - post-fire provenance delay: shift support evidence from after fire toward pre-fire
  - different-object versus far-support split: preserve both observed post-fire support subtypes
  - nearest unsupported decoy: make the selected object nearest but still unsupported

### `blindspot_pre_support_drifted_selected_not_nearest`

- observed rows: `1`
- source scenarios: `['scene-0411-extreme-00']`
- support branch: `pre_fire_support_drifted_outside_support`
- selected branch: `selected_never_supported_before_collision`
- selected rank condition: `selected_not_nearest`
- timing-gap class: `measured_support_gap`
- knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object drift vector: sweep lateral/longitudinal drift outside the frozen support band
  - support-band border control: paired variant at the support threshold without changing thresholds
  - rank competition: keep the selected object non-nearest while another object is closer
  - measured support-gap band: preserve the observed last-support-to-fire gap range

### `blindspot_pre_support_lost_absent_selected_nearest`

- observed rows: `2`
- source scenarios: `['scene-0411-extreme-00', 'scene-0411-hard-00']`
- support branch: `pre_fire_support_lost_absent_at_fire`
- selected branch: `selected_never_supported_before_collision`
- selected rank condition: `selected_nearest`
- timing-gap class: `measured_support_gap`
- knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object disappearance timing: sweep last-presence-to-fire and last-support-to-fire gaps
  - same-object continuity control: paired variant where the early support object remains visible
  - nearest unsupported decoy: make the selected object nearest but still unsupported
  - measured support-gap band: preserve the observed last-support-to-fire gap range

### `blindspot_pre_support_lost_absent_selected_not_nearest`

- observed rows: `2`
- source scenarios: `['scene-0383-extreme-00', 'scene-0411-hard-00']`
- support branch: `pre_fire_support_lost_absent_at_fire`
- selected branch: `selected_never_supported_before_collision`
- selected rank condition: `selected_not_nearest`
- timing-gap class: `measured_support_gap`
- knobs:
  - selected-object actor-support distance: keep selected first-fire object outside the frozen support band
  - first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support
  - slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates
  - support-object disappearance timing: sweep last-presence-to-fire and last-support-to-fire gaps
  - same-object continuity control: paired variant where the early support object remains visible
  - rank competition: keep the selected object non-nearest while another object is closer
  - measured support-gap band: preserve the observed last-support-to-fire gap range

## Future Gates

- freeze candidate source pool before any scenario generation
- define mutation operators without changing Sentinel thresholds
- define support/provenance gates before selecting GPU slots
- separate design/preflight, generation, execution, and analysis into distinct hypotheses
- preserve no-repair/no-safety/no-deployment claim boundary until later evidence proves otherwise

## Claim Boundary

design surface only; no scenario-generation execution, GPU launch, HUGSIM run, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
