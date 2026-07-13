# Iteration 82 - HUGSIM support-object surface/provenance co-occurrence audit

Status: `PRE_REGISTERED`

## Question

Iteration 77 showed that full event-row object sets can contain foreground-supported objects.
Iteration 78 showed that those foreground-supported support objects were nonselected and
subthreshold at the fixed support events. Iteration 79 showed that the selected objects at the
same events were active or borderline. Iteration 80 showed that selected active/borderline objects
do not bridge to any logged provenance row. Iteration 81 showed that the support-object temporal
surface is mixed: one support object later becomes active, while the other remains
visible-never-surface.

This iteration asks the next paired question:

Do foreground bridge support and released CPA/TTC surface activation ever co-occur on the same
fixed support object in the committed ON decision logs?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-81 support-object temporal surface report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, and compact proof
formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed support objects

The fixed support objects are exactly the two iteration-81 objects:

- `both_distinct_extreme` / `scene-0138-extreme-00` / support object `9`;
  iteration-81 label `support_object_ever_active`;
- `ttc_medium_a` / `scene-0071-medium-01` / support object `10`;
  iteration-81 label `support_object_visible_never_surface`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 81: `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`.
2. Cross-check that iteration 81 contains exactly the two fixed support objects above with no
   object-level problems and with the registered labels above.
3. For each fixed support object, load only the committed iteration-59 ON decision log and
   `eval.json` from the episode directory recorded in the iteration-59 report.
4. Load only eligible foreground collision-provenance rows from `eval.json`; non-foreground rows
   are excluded for this audit.
5. Scan every non-error decision row in the committed ON decision log.
6. Whenever the fixed support object is present:
   - reconstruct its released CPA/TTC surface state using the row's logged thresholds;
   - bridge that same object at that same decision timestamp to every eligible foreground
     provenance row using the already-committed iteration-76 16-variant bridge family;
   - assign the best bridge distance and bridge band for that frame.
7. Bridge bands are frozen from iteration 76:
   - `match`: best distance `<= 3.0 m`;
   - `ambiguous`: best distance `> 3.0 m` and `<= 6.0 m`;
   - `no_support`: best distance `> 6.0 m`;
   - `missing`: no bridge variants can be evaluated.
8. Surface bands are frozen from iteration 81:
   - `active`: per-object active CPA or TTC crossing under the logged thresholds;
   - `borderline`: no active crossing, but within the registered borderline CPA/TTC band;
   - `subthreshold`: present but outside active and borderline bands.
9. For each fixed support object, record:
   - present frame count;
   - bridge-supported frame count (`match` or `ambiguous`);
   - active bridge-supported frame count;
   - borderline bridge-supported frame count;
   - first bridge-supported timestamp, if any;
   - first active/borderline bridge-supported timestamp, if any;
   - best overall bridge distance and frame;
   - best active/borderline bridge distance and frame, if any;
   - minimum CPA and minimum finite TTC inherited from frame metrics;
   - the strongest registered object label.
10. Emit JSON and Markdown proof with per-object co-occurrence metrics, frame-level best examples,
    and source cross-checks.

## Registered object labels

Labels are assigned in this order:

- `support_surface_bridge_active_match`: at least one active frame has bridge band `match`.
- `support_surface_bridge_active_ambiguous`: no active frame has bridge band `match`, but at least
  one active frame has bridge band `ambiguous`.
- `support_surface_bridge_borderline_only`: no active frame has bridge support, but at least one
  borderline frame has bridge band `match` or `ambiguous`.
- `support_bridge_surface_temporally_split`: the object has at least one bridge-supported frame
  and at least one active or borderline surface frame, but no active/borderline frame is
  bridge-supported.
- `support_bridge_never_surface`: the object has at least one bridge-supported frame and no active
  or borderline surface frame.
- `support_surface_never_bridge`: the object has at least one active or borderline surface frame
  and no bridge-supported frame.
- `support_no_bridge_no_surface`: the object is present but has neither bridge-supported frames
  nor active/borderline surface frames.
- `support_surface_bridge_cooccurrence_insufficient`: required source, log, object, foreground,
  threshold, metric, or bridge facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SUPPORT_SURFACE_BRIDGE_ACTIVE_MATCH_COMPLETE`: at least one fixed support object is
  `support_surface_bridge_active_match` and no object is blocked.
- `HUGSIM_SUPPORT_SURFACE_BRIDGE_ACTIVE_AMBIGUOUS_COMPLETE`: no object has active match
  co-occurrence, at least one fixed support object is
  `support_surface_bridge_active_ambiguous`, and no object is blocked.
- `HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE`: no object has active bridge
  co-occurrence, at least one fixed support object is
  `support_surface_bridge_borderline_only`, and no object is blocked.
- `HUGSIM_SUPPORT_SURFACE_BRIDGE_TEMPORAL_SPLIT_COMPLETE`: every fixed support object is
  classified without infrastructure problems, but no fixed support object has active or
  borderline bridge co-occurrence.
- `HUGSIM_SUPPORT_SURFACE_BRIDGE_MIXED_COMPLETE`: all fixed support objects are classified with
  no infrastructure problems, but none of the verdicts above holds.
- `HUGSIM_SUPPORT_SURFACE_BRIDGE_BLOCKED`: source verdicts, fixed object identities, decision
  logs, object metrics, thresholds, foreground provenance, or bridge facts fail cross-checks, or
  any object is `support_surface_bridge_cooccurrence_insufficient`.

## Claim boundary

This is a two-object descriptive surface/provenance co-occurrence audit only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, or commercial
value.
