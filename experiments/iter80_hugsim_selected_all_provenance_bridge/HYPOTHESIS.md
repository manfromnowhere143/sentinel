# Iteration 80 - HUGSIM selected-object all-provenance bridge audit

Status: `PRE_REGISTERED`

## Question

Iteration 79 showed that the selected event objects are active or borderline under the released
CPA/TTC surface, while the foreground-supported full-set objects are subthreshold. Iteration 76
already showed that the selected switched objects do not bridge to foreground provenance.

This iteration asks the narrow follow-up:

Do the selected active/borderline objects from iteration 79 bridge to any logged HUGSIM
collision-provenance row, regardless of collision class, under the same frozen bridge grid?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-77 event object-set foreground-bridge report;
- committed iteration-79 selected-object surface decomposition report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, object selection, bridge variants, and distance-band helpers.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed selected events

The fixed selected events are exactly the three evaluated iteration-79 events:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  selected object `5`, selected state `borderline`, support object `9`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  selected object `6`, selected state `borderline`, support object `10`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  selected object `24`, selected state `active`, support object `10`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 77: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`;
   - iteration 79: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`.
2. Cross-check that iteration 79 contains exactly the fixed selected events above, all with no
   event-level problems and selected states matching the fixed list.
3. For each fixed event, load only the committed iteration-59 ON decision log and `eval.json`.
4. Select the exact decision row at the iteration-79 event timestamp.
5. Select the fixed selected object from that row.
6. Load all eligible `collision_provenance` rows with numeric timestamp and numeric
   `obs_box[:2]`, without filtering by `collision_type`.
7. Record the distinct logged collision classes and row counts used for each fixed event.
8. Run the same frozen bridge-variant grid used by iterations 76 and 77 from the selected object
   to every eligible provenance row.
9. Record best all-provenance bridge variant, best distance, bridge distance band, and collision
   class of the best row.
10. Emit JSON and Markdown proof with source cross-checks, provenance-class inventory, and
   selected-object bridge results.

## Registered bridge bands

These are descriptive support bands, not fitted thresholds:

- `match`: best bridge distance `<= 3.0 m`;
- `ambiguous`: best bridge distance `> 3.0 m` and `<= 6.0 m`;
- `no_support`: best bridge distance `> 6.0 m`;
- `missing`: no eligible provenance or bridge variant.

## Registered event labels

- `selected_all_provenance_match`: selected object reaches `match` against at least one logged
  provenance row of any collision class.
- `selected_all_provenance_ambiguous`: selected object reaches only `ambiguous` against logged
  provenance rows.
- `selected_all_provenance_no_support`: selected object has eligible logged provenance rows but
  reaches no `match` or `ambiguous` support.
- `selected_all_provenance_insufficient`: required source, log, selected object, provenance row,
  bridge, or fixed-event facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SELECTED_ALL_PROVENANCE_MATCH_COMPLETE`: at least one fixed event is
  `selected_all_provenance_match` and no event is blocked.
- `HUGSIM_SELECTED_ALL_PROVENANCE_AMBIGUOUS_COMPLETE`: no fixed event reaches match, at least
  one fixed event is `selected_all_provenance_ambiguous`, and no event is blocked.
- `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`: every fixed event is
  `selected_all_provenance_no_support`.
- `HUGSIM_SELECTED_ALL_PROVENANCE_MIXED_COMPLETE`: all fixed events are classified with no
  infrastructure problems, but none of the verdicts above holds.
- `HUGSIM_SELECTED_ALL_PROVENANCE_BLOCKED`: source verdicts, fixed event identities, decision
  logs, selected objects, provenance rows, bridge variants, or rankings fail cross-checks, or any
  event is `selected_all_provenance_insufficient`.

## Claim boundary

This is a three-event descriptive selected-object all-provenance bridge audit only. It cannot
claim actor causality, repair, threshold value, transfer improvement, safety, deployment
readiness, robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value,
or commercial value.
