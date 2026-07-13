# Iteration 79 - HUGSIM selected-object surface decomposition

Status: `PRE_REGISTERED`

## Question

Iteration 78 showed that the three foreground-supported full-set objects from iteration 77 are
not the selected event objects and are subthreshold under the logged CPA/TTC surface.

This iteration asks the paired question:

At those same event rows, what did the selected monitor object look like under the logged surface,
and how does it compare to the foreground-supported but nonselected object?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-75 object-handoff report;
- committed iteration-77 event object-set foreground-bridge report;
- committed iteration-78 support-object ranking report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, and per-object CPA/TTC metric reconstruction.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed comparison events

The fixed comparison events are exactly the three evaluated iteration-78 events:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  selected object `5`, foreground-supported object `9`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  selected object `6`, foreground-supported object `10`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  selected object `24`, foreground-supported object `10`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 75: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
   - iteration 77: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`;
   - iteration 78: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`.
2. Cross-check that iteration 78 contains exactly the fixed comparison events above, all with
   `support_object_nonselected_subthreshold` and no event-level problems.
3. Cross-check that iteration 75 provides the same selected object id for each fixed event role.
4. Load only the committed iteration-59 ON decision log for each event row.
5. Select the exact decision row at the iteration-78 event timestamp.
6. Reconstruct per-object CPA/TTC metrics for every object in that decision row using the
   existing iteration-62 object-metric helper family.
7. For both the selected object and the foreground-supported object, record:
   - CPA value and rank;
   - TTC value and rank;
   - detector score if present;
   - whether CPA crosses the frozen active surface;
   - whether TTC crosses the frozen active surface;
   - whether either channel is within the registered borderline band.
8. Assign one registered event label per fixed comparison event.
9. Emit JSON and Markdown proof with selected-vs-support metrics, rankings, threshold-state
   comparison, and source cross-checks.

## Registered bands

These bands are descriptive audit bins, not candidate thresholds:

- active CPA crossing: per-object `min_cpa <= cpa_margin`;
- active TTC crossing: finite per-object `ttc <= ttc_thresh`;
- borderline CPA: no active CPA crossing and `min_cpa <= 3.0 m`;
- borderline TTC: no active TTC crossing and finite `ttc <= 5.0 s`.

The frozen active thresholds are read from the selected decision row's logged `params`.

## Registered event labels

- `selected_active_support_subthreshold`: selected object crosses at least one active channel,
  while the foreground-supported object remains nonselected and subthreshold.
- `selected_borderline_support_subthreshold`: selected object crosses no active channel but is
  borderline on at least one channel, while the foreground-supported object remains nonselected
  and subthreshold.
- `selected_subthreshold_support_subthreshold`: both selected and foreground-supported objects
  are subthreshold under the registered bands.
- `selected_support_surface_mixed`: selected-vs-support comparison is complete with no problems,
  but none of the labels above covers every event uniformly.
- `selected_surface_decomposition_insufficient`: required source, log, object, threshold,
  ranking, or comparison facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`: at least one fixed event is
  `selected_active_support_subthreshold` and no event is blocked.
- `HUGSIM_SELECTED_BORDERLINE_SUPPORT_SUBTHRESHOLD_COMPLETE`: no selected-active event exists,
  at least one fixed event is `selected_borderline_support_subthreshold`, and no event is
  blocked.
- `HUGSIM_SELECTED_AND_SUPPORT_SUBTHRESHOLD_COMPLETE`: every fixed event is
  `selected_subthreshold_support_subthreshold`.
- `HUGSIM_SELECTED_SURFACE_DECOMPOSITION_MIXED_COMPLETE`: all fixed events are classified with
  no infrastructure problems, but none of the verdicts above holds.
- `HUGSIM_SELECTED_SURFACE_DECOMPOSITION_BLOCKED`: source verdicts, fixed event identities,
  decision logs, per-object metrics, thresholds, or rankings fail cross-checks, or any event is
  `selected_surface_decomposition_insufficient`.

## Claim boundary

This is a three-event descriptive selected-vs-support surface audit only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, or
commercial value.
