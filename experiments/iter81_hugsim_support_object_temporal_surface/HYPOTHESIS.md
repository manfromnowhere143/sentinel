# Iteration 81 - HUGSIM support-object temporal surface audit

Status: `PRE_REGISTERED`

## Question

Iteration 78 showed that foreground-supported full-set objects are nonselected and subthreshold
at the fixed event rows. Iteration 79 showed that the selected objects in those rows are active
or borderline surface candidates. Iteration 80 showed that those selected objects do not bridge
to any logged provenance row in the fixed episodes.

This iteration asks the paired temporal question:

Do the foreground-supported objects from iteration 78 ever become active or borderline under the
released CPA/TTC surface anywhere in the committed ON decision logs?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-78 support-object ranking report;
- committed iteration-79 selected-object surface decomposition report;
- committed iteration-80 selected-object all-provenance bridge report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, per-object CPA/TTC metric reconstruction, threshold-state
classification, and first-foreground timestamp extraction.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed support objects

The fixed support objects are the unique foreground-supported objects from iteration 78:

- `both_distinct_extreme` / `scene-0138-extreme-00` / support object `9`;
  fixed support event: pre event at `5.0 s`, support band `ambiguous`;
- `ttc_medium_a` / `scene-0071-medium-01` / support object `10`;
  fixed support events: pre event at `2.5 s` and active event at `5.0 s`, support band `match`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 78: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`;
   - iteration 79: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`;
   - iteration 80: `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`.
2. Cross-check that iteration 78 contains exactly the fixed support events above, all with
   `support_object_nonselected_subthreshold` and no event-level problems.
3. Cross-check that iteration 79 and iteration 80 preserve the same selected/support object split
   for those fixed events with no event-level problems.
4. For each fixed support object, load only the committed iteration-59 ON decision log and
   `eval.json`.
5. Extract the first eligible foreground timestamp from `eval.json` for timing context.
6. Scan every non-error decision row in the committed ON decision log.
7. Whenever the fixed support object is present, reconstruct per-object CPA/TTC metrics using the
   existing iteration-62 object-metric helper family and the row's logged thresholds.
8. For each fixed support object, record:
   - present frame count and absent frame count;
   - first and last present timestamps;
   - active frame count;
   - borderline-only frame count;
   - first active timestamp, if any;
   - first borderline timestamp, if any;
   - minimum CPA and minimum finite TTC over the full log;
   - the fixed support event states inherited from iteration 78;
   - timing of first active/borderline relative to each fixed support event and first foreground.
9. Assign one registered object label per fixed support object.
10. Emit JSON and Markdown proof with per-object temporal metrics, event-relative timing, and
    source cross-checks.

## Registered bands

These bands are descriptive audit bins, not candidate thresholds:

- active CPA crossing: per-object `min_cpa <= cpa_margin`;
- active TTC crossing: finite per-object `ttc <= ttc_thresh`;
- borderline CPA: no active CPA crossing and `min_cpa <= 3.0 m`;
- borderline TTC: no active TTC crossing and finite `ttc <= 5.0 s`.

The frozen active thresholds are read from each decision row's logged `params`.

## Registered object labels

- `support_object_ever_active`: fixed support object is present in at least one decision row and
  crosses at least one active CPA/TTC channel anywhere in the committed ON decision log.
- `support_object_borderline_only`: fixed support object never crosses an active channel but is
  borderline in at least one decision row.
- `support_object_visible_never_surface`: fixed support object is present in at least one
  decision row and never crosses active or borderline bands.
- `support_object_temporal_insufficient`: required source, log, object, threshold, metric,
  foreground timestamp, or fixed-event facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`: at least one fixed support object is
  `support_object_ever_active` and no object is blocked.
- `HUGSIM_SUPPORT_OBJECT_BORDERLINE_ONLY_COMPLETE`: no fixed support object is ever active, at
  least one fixed support object is `support_object_borderline_only`, and no object is blocked.
- `HUGSIM_SUPPORT_OBJECT_VISIBLE_NEVER_SURFACE_COMPLETE`: every fixed support object is
  `support_object_visible_never_surface`.
- `HUGSIM_SUPPORT_OBJECT_TEMPORAL_MIXED_COMPLETE`: all fixed support objects are classified with
  no infrastructure problems, but none of the verdicts above holds.
- `HUGSIM_SUPPORT_OBJECT_TEMPORAL_BLOCKED`: source verdicts, fixed event identities, decision
  logs, object metrics, thresholds, foreground timestamps, or timing facts fail cross-checks, or
  any object is `support_object_temporal_insufficient`.

## Claim boundary

This is a two-object descriptive temporal surface audit only. It cannot claim actor causality,
repair, threshold value, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
