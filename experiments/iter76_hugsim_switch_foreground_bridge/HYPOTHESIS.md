# Iteration 76 - HUGSIM switch foreground bridge audit

Status: `PRE_REGISTERED`

## Question

Iteration 75 showed that both fixed cross-channel late-fire rows are also object switches:

- `both_distinct_extreme`: pre-contact CPA object `5` -> post-contact active TTC object `9`;
- `ttc_medium_a`: pre-contact TTC object `6` -> post-contact active CPA object `24`.

This iteration asks the next foreground-geometry question:

For each cross-channel object switch, does the pre-contact near object or the post-contact active
object have stronger bounded bridge support to the HUGSIM foreground collision provenance?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-72 late-fire prefire margin report;
- committed iteration-73 margin-transition report;
- committed iteration-74 late-fire delay-barrier report;
- committed iteration-75 object-handoff report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the two iteration-75 `object_switch_cross_channel_handoff` rows:

- `both_distinct_extreme` / `scene-0138-extreme-00`;
- `ttc_medium_a` / `scene-0071-medium-01`.

The fixed event objects come from iteration 75:

- pre object: the pre-contact near-channel responsible object id at the iteration-75 `pre_ts`;
- active object: the post-contact first-active responsible object id at the iteration-75
  `active_ts`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
   - iteration 73: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`;
   - iteration 74: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`;
   - iteration 75: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`.
2. Cross-check that the fixed row identities match iteration 75 and classify as
   `object_switch_cross_channel_handoff`.
3. For each fixed row, load only the committed iteration-59 ON decision log and eval artifact.
4. Select the exact decision row at the iteration-75 pre timestamp and the exact decision row at
   the iteration-75 active timestamp.
5. From each selected decision row, select exactly the iteration-75 responsible object id for
   that event. If the object is missing or duplicated in its event row, the row is blocked.
6. Define the HUGSIM foreground surface as every `collision_provenance` row in the committed
   eval artifact where:
   - `collision_type == "foreground"`;
   - `timestamp` is numeric;
   - `obs_box[:2]` are numeric.
7. For each event object and each foreground provenance row, evaluate the same bounded bridge
   family used by iteration 61:
   - temporal source: object position at the event row, and object position propagated to the
     foreground timestamp with `lead_time_s = max(0, foreground_ts - event_ts)`;
   - axis order:
     - `(forward, lateral) = (monitor_local_y, monitor_local_x)`;
     - `(forward, lateral) = (monitor_local_x, monitor_local_y)`;
   - sign flips: `forward_sign in {-1, +1}`, `lateral_sign in {-1, +1}`.
8. Compute the best bridge distance for the pre object and the active object.
9. Assign one registered row label per fixed row.
10. Emit JSON and Markdown proof with event objects, best bridge variants, distances, labels, and
    source cross-checks.

## Registered distance bands

These are the same bounded support bands as iterations 59-61:

- match: best distance `<= 3.0 m`;
- ambiguous: best distance in `(3.0 m, 6.0 m]`;
- no support: best distance `> 6.0 m`.

No fitted translation, scale, rotation, yaw, scenario offset, object offset, or row-conditioned
transform is allowed.

## Registered row labels

- `active_object_foreground_match`: active object has a match and pre object does not.
- `pre_object_foreground_match`: pre object has a match and active object does not.
- `both_objects_foreground_match`: both pre and active objects have a match.
- `active_object_foreground_ambiguous`: no object has a match, active object is ambiguous, and
  pre object is no-support.
- `pre_object_foreground_ambiguous`: no object has a match, pre object is ambiguous, and active
  object is no-support.
- `both_objects_foreground_ambiguous`: no object has a match and both objects are ambiguous.
- `no_foreground_bridge_support`: both objects are no-support.
- `switch_foreground_bridge_insufficient`: required source, log, object, foreground, or bridge
  facts are missing or inconsistent.

If both objects have the same distance band, the row label uses the `both_*` label even if one
distance is numerically smaller. Numeric best-distance deltas are still recorded.

## Registered verdicts

- `HUGSIM_SWITCH_FOREGROUND_ACTIVE_MATCH_COMPLETE`: at least one row is
  `active_object_foreground_match` and no row is blocked.
- `HUGSIM_SWITCH_FOREGROUND_PRE_MATCH_COMPLETE`: at least one row is
  `pre_object_foreground_match` and no row is blocked.
- `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`: both rows are classified with no
  infrastructure problems, but neither active-only nor pre-only match verdict holds.
- `HUGSIM_SWITCH_FOREGROUND_BRIDGE_BLOCKED`: source verdicts, row identities, decision logs,
  eval provenance, object selection, or bridge reconstruction fail cross-checks, or any row is
  `switch_foreground_bridge_insufficient`.

## Claim boundary

This is a two-row descriptive foreground-bridge audit only. It cannot claim actor causality,
repair, threshold value, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
