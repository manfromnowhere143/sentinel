# Iteration 72 - HUGSIM late-fire prefire margin audit

Status: `PRE_REGISTERED`

## Question

Iteration 70 split two structural rows into `foreground_present_late_fire`: foreground collision
provenance exists, but Sentinel first fires after the first foreground timestamp. Iteration 71
closed the near-margin explanation for the surface-silent branch.

This iteration asks the parallel late-fire question:

For the two rows where Sentinel fires after first foreground contact, were the pre-foreground
decision frames already near or crossing the frozen released-union CPA/TTC trigger surfaces, or
were they also far from the trigger surfaces before contact?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the two iteration-70 `foreground_present_late_fire` rows:

- `both_distinct_extreme` / `scene-0138-extreme-00`;
- `ttc_medium_a` / `scene-0071-medium-01`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
2. Select exactly the two fixed late-fire rows from the iteration-70 report.
3. For each row, load only the committed iteration-59 ON decision log and scan frames with
   `ts < first_foreground_ts`.
4. Read the frozen released-union thresholds from each decision row's logged `params`:
   - `ttc_thresh`;
   - `cpa_margin`.
5. Compute:
   - pre-foreground monitor-frame count;
   - pre-foreground object-row count;
   - finite minimum TTC and its margin above `ttc_thresh`;
   - minimum CPA and its margin above `cpa_margin`;
   - whether any pre-foreground frame crosses either active trigger surface;
   - the already-published fire delay from iteration 70.
6. Assign one registered row label per row.
7. Emit JSON and Markdown proof with counts and per-row margins.

## Registered margin bands

These bands are descriptive audit bins, not candidate thresholds:

- active TTC crossing: finite `min_ttc <= ttc_thresh`;
- active CPA crossing: `min_cpa <= cpa_margin`;
- near TTC margin: finite `0 < min_ttc - ttc_thresh <= 1.0 s`;
- near CPA margin: `0 < min_cpa - cpa_margin <= 1.5 m`;
- far margin: no active crossing and no near TTC/CPA margin.

## Registered row labels

- `late_fire_prefire_near_ttc_margin`: no pre-foreground active crossing, but at least one
  pre-foreground frame is within the registered near-TTC margin band.
- `late_fire_prefire_near_cpa_margin`: no pre-foreground active crossing, but at least one
  pre-foreground frame is within the registered near-CPA margin band.
- `late_fire_prefire_far_margin`: no pre-foreground active crossing and no registered near-margin
  frame.
- `late_fire_prefire_no_object_rows`: no pre-foreground decision rows contain monitor objects.
- `late_fire_prefire_active_crossing_inconsistent`: a pre-foreground frame crosses the active
  released-union CPA/TTC surface even though first fire is after foreground contact.

If both near-TTC and near-CPA margins occur, the row label is
`late_fire_prefire_near_ttc_margin` and the CPA near flag is still recorded.

## Registered verdicts

- `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`: both fixed rows are classified with no
  infrastructure problems and no `late_fire_prefire_active_crossing_inconsistent` row.
- `HUGSIM_LATE_FIRE_PREFIRE_ACTIVE_INCONSISTENT_BLOCKED`: at least one fixed row crosses an
  active trigger surface before foreground contact despite first fire occurring later.
- `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_BLOCKED`: source verdicts, row identities, decision logs, or
  required threshold fields fail cross-checks.

## Claim boundary

This is a two-row descriptive prefire margin audit only. It cannot claim actor causality, repair,
threshold value, transfer improvement, safety, deployment readiness, robustness, benchmark
ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
