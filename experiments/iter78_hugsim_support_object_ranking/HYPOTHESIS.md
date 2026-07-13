# Iteration 78 - HUGSIM support-object ranking audit

Status: `PRE_REGISTERED`

## Question

Iteration 77 showed that full event-row object sets can contain foreground-supported objects even
when the selected switched objects from iteration 75 do not bridge to foreground:

- `both_distinct_extreme`: pre-event object set has ambiguous support via object `9`;
- `ttc_medium_a`: pre-event and active-event object sets have match support via object `10`.

This iteration asks the next monitor-surface question:

At the event rows where foreground-supported objects exist, were those support objects selected
by the monitor surface, already active hazards, borderline hazards, or visible-but-subthreshold /
nonselected objects?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-72 late-fire prefire margin report;
- committed iteration-73 margin-transition report;
- committed iteration-74 late-fire delay-barrier report;
- committed iteration-75 object-handoff report;
- committed iteration-76 switch foreground-bridge report;
- committed iteration-77 event object-set foreground-bridge report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed support events

The fixed support events are exactly the iteration-77 event-set rows with match or ambiguous
foreground support:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event / object `9` /
  `pre_set_foreground_ambiguous`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event / object `10` /
  `both_sets_foreground_match`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event / object `10` /
  `both_sets_foreground_match`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
   - iteration 73: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`;
   - iteration 74: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`;
   - iteration 75: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
   - iteration 76: `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`;
   - iteration 77: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`.
2. Cross-check that the fixed support events above are present in iteration 77 with the expected
   event role, object id, and bridge support band.
3. For each fixed support event, load only the committed iteration-59 ON decision log.
4. Select the exact decision row at the event timestamp from iteration 77.
5. Reconstruct per-object CPA/TTC metrics for every object in that decision row using the
   existing iteration-62 object-metric helper family.
6. For the fixed support object, record:
   - CPA value and rank;
   - TTC value and rank;
   - whether CPA crosses the frozen active surface;
   - whether TTC crosses the frozen active surface;
   - whether either channel is within the registered borderline band;
   - whether it is the selected object for the iteration-75 event.
7. Assign one registered event label per fixed support event.
8. Emit JSON and Markdown proof with per-event metrics, rankings, selected-object comparison, and
   source cross-checks.

## Registered bands

These bands are descriptive audit bins, not candidate thresholds:

- active CPA crossing: per-object `min_cpa <= cpa_margin`;
- active TTC crossing: finite per-object `ttc <= ttc_thresh`;
- borderline CPA: no active CPA crossing and `min_cpa <= 3.0 m`;
- borderline TTC: no active TTC crossing and finite `ttc <= 5.0 s`.

The frozen active thresholds are read from the selected decision row's logged `params`.

## Registered event labels

- `support_object_selected_active`: support object is the iteration-75 selected object for that
  event and crosses at least one active channel.
- `support_object_selected_subthreshold`: support object is the iteration-75 selected object for
  that event and crosses no active channel.
- `support_object_nonselected_active`: support object is not the iteration-75 selected object for
  that event and crosses at least one active channel.
- `support_object_nonselected_borderline`: support object is not the iteration-75 selected object
  for that event, crosses no active channel, and is borderline on at least one channel.
- `support_object_nonselected_subthreshold`: support object is not the iteration-75 selected
  object for that event and is neither active nor borderline.
- `support_object_ranking_insufficient`: required source, log, object, threshold, ranking, or
  support-event facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SUPPORT_OBJECT_NONSELECTED_ACTIVE_COMPLETE`: at least one fixed support event is
  `support_object_nonselected_active` and no event is blocked.
- `HUGSIM_SUPPORT_OBJECT_NONSELECTED_BORDERLINE_COMPLETE`: no support event is nonselected-active,
  at least one fixed support event is `support_object_nonselected_borderline`, and no event is
  blocked.
- `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`: all fixed support events are classified with no
  infrastructure problems, but neither nonselected-active nor nonselected-borderline verdict
  holds.
- `HUGSIM_SUPPORT_OBJECT_RANKING_BLOCKED`: source verdicts, fixed event identities, decision
  logs, per-object metrics, thresholds, or rankings fail cross-checks, or any event is
  `support_object_ranking_insufficient`.

## Claim boundary

This is a three-event descriptive support-object ranking audit only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, or
commercial value.
