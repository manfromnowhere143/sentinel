# HUGSIM support-core two-track taxonomy

This note records the committed support-core mechanism taxonomy after
[iteration 121](../../experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md).
It is documentation integration only. It does not rerun HUGSIM, read raw logs, retune thresholds,
change Sentinel, or upgrade any benchmark claim.

## Evidence chain

- [Iteration 112](../../experiments/iter112_hugsim_support_core_batch_execution/RESULT.md):
  the `8` support-core slots executed with slot-level proof and `44` total
  collision-provenance rows.
- [Iteration 113](../../experiments/iter113_hugsim_support_core_actor_match_audit/RESULT.md):
  all `8` support-core slots were foreground-classifiable and all `8` bridge labels were
  actor mismatches under the frozen bridge.
- [Iteration 114](../../experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition/RESULT.md):
  all `8` mismatch vectors were forward-dominant.
- [Iteration 115](../../experiments/iter115_hugsim_support_core_monitor_set_ordering/RESULT.md):
  all `8` first-fire monitor object sets lacked a close collision-actor candidate.
- [Iteration 116](../../experiments/iter116_hugsim_support_core_collision_actor_timeline/RESULT.md):
  `7/8` rows had pre-collision support frames, but no row was supported at first fire.
- [Iteration 117](../../experiments/iter117_hugsim_support_core_event_window_decomposition/RESULT.md):
  first-support objects persisted to first fire in only `1/7` supported rows and never equaled
  the selected first-fire object.
- [Iteration 118](../../experiments/iter118_hugsim_support_core_object_lifecycle/RESULT.md):
  first-support objects were never still supported at fire.
- [Iteration 119](../../experiments/iter119_hugsim_support_core_loss_replacement_audit/RESULT.md):
  last same-object support ended `1.0-6.0 s` before fire where measurable, and all first-fire
  nearest replacements remained outside support.
- [Iteration 120](../../experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle/RESULT.md):
  all selected first-fire objects were never supported before collision.
- [Iteration 121](../../experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md):
  the committed reports join into one support-core two-track taxonomy.

## Taxonomy

Iteration 121 reports `8/8` rows preserving the two-track split:

- support side: the object that creates earlier support disappears, drifts outside support,
  appears only after fire, or is absent as a reference branch;
- selected-fire side: the object selected at first fire is never supported before collision.

| Branch | Count |
|---|---:|
| pre-support lost absent, selected nearest | `2` |
| pre-support lost absent, selected not nearest | `2` |
| pre-support drifted, selected not nearest | `1` |
| post-fire support, selected nearest | `2` |
| never-supported reference, selected nearest | `1` |

The selected-fire lifecycle count is `8/8`
`selected_never_supported_before_collision`.

## Interpretation

At this evidence level, the support-core mechanism is timing/object-identity separation:
support appears on one object or branch, while first fire selects another object that never entered
the frozen support band before collision. This is a mechanism taxonomy over committed reports, not
a runtime fix.

## Claim Boundary

descriptive support-core taxonomy only; no repair, actor-causality, threshold-value, transfer
upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance,
real-world behavior, first-responder behavior, acquisition-value, retuning, production, or
commercial claim
