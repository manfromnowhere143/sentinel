# Iteration 75 - HUGSIM cross-channel object handoff audit

Status: `PRE_REGISTERED`

## Question

Iteration 74 showed that both foreground-present late-fire rows are cross-channel delay cases:

- `both_distinct_extreme`: CPA-near before contact, then TTC-active after contact;
- `ttc_medium_a`: TTC-near before contact, then CPA-active after contact.

This iteration asks the next object-level mechanism question:

At the cross-channel handoff, is the responsible monitor object the same tracked object before
and after contact, or does responsibility switch to a different object?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-72 late-fire prefire margin report;
- committed iteration-73 margin-transition report;
- committed iteration-74 late-fire delay-barrier report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the two iteration-74 `cross_channel_late_activation` rows:

- `both_distinct_extreme` / `scene-0138-extreme-00`;
- `ttc_medium_a` / `scene-0071-medium-01`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
   - iteration 73: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`;
   - iteration 74: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`.
2. Cross-check that the fixed row identities match iteration 74 and classify as
   `cross_channel_late_activation`.
3. For each fixed row, load only the committed iteration-59 ON decision log.
4. Reconstruct per-object CPA/TTC metrics with the same object-metric helper family used by
   iteration 62, reading only the logged decision row fields and frozen logged parameters.
5. For the pre-contact near event named by iteration 74:
   - use the closest pre-contact near timestamp for the pre-contact near channel;
   - identify the responsible object-id set for that channel as the object(s) attaining the
     logged aggregate near-channel minimum within numeric tolerance.
6. For the post-contact first-active event named by iteration 74:
   - use the first active timestamp and first active channel set;
   - identify the responsible object-id set for each first-active channel as the object(s)
     attaining the active-channel minimum within numeric tolerance.
7. Compare pre-contact responsible object ids to post-contact responsible object ids.
8. Emit JSON and Markdown proof with per-row timestamps, channels, object-id sets, and labels.

## Registered object labels

- `same_object_cross_channel_handoff`: both responsible object-id sets are singleton and equal.
- `object_switch_cross_channel_handoff`: both responsible object-id sets are singleton and
  disjoint.
- `multiobject_cross_channel_handoff`: either responsible object-id set has multiple ids, or the
  first-active channel set has multiple channels.
- `cross_channel_object_handoff_insufficient`: required row/log/channel/object facts are missing
  or inconsistent.
- `cross_channel_source_inconsistent`: source reports do not support the fixed cross-channel
  late-activation premise.

If a row has both a multi-object condition and an intersecting object id, the registered label is
`multiobject_cross_channel_handoff`; it is less specific and avoids claiming a clean same-object
handoff under ties.

## Registered verdicts

- `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`: both fixed rows classify as
  `object_switch_cross_channel_handoff`.
- `HUGSIM_CROSS_CHANNEL_SAME_OBJECT_COMPLETE`: both fixed rows classify as
  `same_object_cross_channel_handoff`.
- `HUGSIM_CROSS_CHANNEL_OBJECT_HANDOFF_MIXED_COMPLETE`: both fixed rows are classified with no
  infrastructure problems, but neither all-switch nor all-same holds.
- `HUGSIM_CROSS_CHANNEL_OBJECT_HANDOFF_BLOCKED`: source verdicts, row identities, decision logs,
  per-object metric reconstruction, or required timestamp/channel facts fail cross-checks, or any
  insufficient/source-inconsistent label is emitted.

## Claim boundary

This is a two-row descriptive object-handoff audit only. It cannot claim actor causality, repair,
threshold value, transfer improvement, safety, deployment readiness, robustness, benchmark
ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
