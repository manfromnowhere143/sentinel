# Iteration 77 - HUGSIM event object-set foreground bridge audit

Status: `PRE_REGISTERED`

## Question

Iteration 76 showed that the two specific switched objects from iteration 75 do not bridge to
the HUGSIM foreground collision provenance under the fixed support grid.

This iteration asks the next bounded support question:

At the same pre-contact and post-contact event rows, does any monitor object in the full logged
object set bridge to the HUGSIM foreground collision provenance, or is foreground support absent
from the entire event-row object set?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-72 late-fire prefire margin report;
- committed iteration-73 margin-transition report;
- committed iteration-74 late-fire delay-barrier report;
- committed iteration-75 object-handoff report;
- committed iteration-76 switch foreground-bridge report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the two iteration-76 `no_foreground_bridge_support` rows:

- `both_distinct_extreme` / `scene-0138-extreme-00`;
- `ttc_medium_a` / `scene-0071-medium-01`.

The fixed event timestamps come from iteration 75:

- pre event timestamp: iteration-75 `pre_ts`;
- active event timestamp: iteration-75 `active_ts`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
   - iteration 73: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`;
   - iteration 74: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`;
   - iteration 75: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
   - iteration 76: `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`.
2. Cross-check that the fixed row identities match iteration 76 and classify as
   `no_foreground_bridge_support`.
3. For each fixed row, load only the committed iteration-59 ON decision log and eval artifact.
4. Select the exact decision row at the iteration-75 pre timestamp and the exact decision row at
   the iteration-75 active timestamp.
5. Use every object in each selected decision row's `objs` list. Do not filter by score, channel,
   selected argmin object, foreground distance, object id, or post-hoc outcome.
6. Define the HUGSIM foreground surface as every `collision_provenance` row in the committed
   eval artifact where:
   - `collision_type == "foreground"`;
   - `timestamp` is numeric;
   - `obs_box[:2]` are numeric.
7. For every event-row object and every foreground provenance row, evaluate the same bounded
   bridge family used by iterations 61 and 76:
   - temporal source: object position at the event row, and object position propagated to the
     foreground timestamp with `lead_time_s = max(0, foreground_ts - event_ts)`;
   - axis order:
     - `(forward, lateral) = (monitor_local_y, monitor_local_x)`;
     - `(forward, lateral) = (monitor_local_x, monitor_local_y)`;
   - sign flips: `forward_sign in {-1, +1}`, `lateral_sign in {-1, +1}`.
8. Compute best bridge distance for the pre-event object set and active-event object set.
9. Assign one registered row label per fixed row.
10. Emit JSON and Markdown proof with object counts, best variants, distances, labels, and source
    cross-checks.

## Registered distance bands

These are the same bounded support bands as iterations 59-61 and 76:

- match: best distance `<= 3.0 m`;
- ambiguous: best distance in `(3.0 m, 6.0 m]`;
- no support: best distance `> 6.0 m`.

No fitted translation, scale, rotation, yaw, scenario offset, object offset, score threshold,
object filter, or row-conditioned transform is allowed.

## Registered row labels

- `active_set_foreground_match`: active-event object set has a match and pre-event object set
  does not.
- `pre_set_foreground_match`: pre-event object set has a match and active-event object set does
  not.
- `both_sets_foreground_match`: both event-row object sets have at least one match.
- `active_set_foreground_ambiguous`: no set has a match, active-event set is ambiguous, and
  pre-event set is no-support.
- `pre_set_foreground_ambiguous`: no set has a match, pre-event set is ambiguous, and active
  event set is no-support.
- `both_sets_foreground_ambiguous`: no set has a match and both sets are ambiguous.
- `event_object_sets_no_foreground_support`: both event-row object sets are no-support.
- `event_object_set_bridge_insufficient`: required source, log, object, foreground, or bridge
  facts are missing or inconsistent.

If both event sets have the same distance band, the row label uses the `both_*` label even if one
distance is numerically smaller. Numeric best-distance deltas are still recorded.

## Registered verdicts

- `HUGSIM_EVENT_SET_FOREGROUND_ACTIVE_MATCH_COMPLETE`: at least one row is
  `active_set_foreground_match` and no row is blocked.
- `HUGSIM_EVENT_SET_FOREGROUND_PRE_MATCH_COMPLETE`: at least one row is
  `pre_set_foreground_match` and no row is blocked.
- `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`: both rows are classified with no
  infrastructure problems, but neither active-only nor pre-only match verdict holds.
- `HUGSIM_EVENT_SET_FOREGROUND_BRIDGE_BLOCKED`: source verdicts, row identities, decision logs,
  eval provenance, object-set selection, or bridge reconstruction fail cross-checks, or any row
  is `event_object_set_bridge_insufficient`.

## Claim boundary

This is a two-row descriptive event-object-set foreground-bridge audit only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, or
commercial value.
