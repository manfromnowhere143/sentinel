# Iteration 71 - HUGSIM surface-silent margin audit

Status: `PRE_REGISTERED`

## Question

Iteration 70 split the five structural HUGSIM rows into two surface-silent foreground-present
rows, two late-fire foreground-present rows, and one foreground-absent/background-only row.

This iteration asks the next narrow question for the surface-silent branch:

For the two rows where foreground collision provenance exists but Sentinel never fires, were the
pre-foreground decision frames close to the frozen released-union CPA/TTC trigger surfaces, or far
from both trigger surfaces?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the two iteration-70 `foreground_present_surface_silent` rows:

- `mixed_extreme` / `scene-0062-extreme-00`;
- `nofire_hard_control` / `scene-0041-hard-00`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
2. Select exactly the two fixed surface-silent rows from the iteration-70 report.
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
   - whether any pre-foreground frame crosses either active trigger surface.
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

- `surface_silent_near_ttc_margin`: no active crossing, but at least one pre-foreground frame is
  within the registered near-TTC margin band.
- `surface_silent_near_cpa_margin`: no active crossing, but at least one pre-foreground frame is
  within the registered near-CPA margin band.
- `surface_silent_far_margin`: no active crossing and no registered near-margin frame.
- `surface_silent_no_object_rows`: no pre-foreground decision rows contain monitor objects.
- `surface_silent_active_crossing_inconsistent`: a pre-foreground frame crosses the active
  released-union CPA/TTC surface even though the row is registered as no-fire.

If both near-TTC and near-CPA margins occur, the row label is `surface_silent_near_ttc_margin`
and the CPA near flag is still recorded.

## Registered verdicts

- `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`: both fixed rows are classified with no infrastructure
  problems and no `surface_silent_active_crossing_inconsistent` row.
- `HUGSIM_SURFACE_SILENT_ACTIVE_INCONSISTENT_BLOCKED`: at least one fixed row crosses an active
  trigger surface before foreground contact despite being a no-fire row.
- `HUGSIM_SURFACE_SILENT_MARGIN_BLOCKED`: source verdicts, row identities, decision logs, or
  required threshold fields fail cross-checks.

## Claim boundary

This is a two-row descriptive margin audit only. It cannot claim actor causality, repair,
threshold value, transfer improvement, safety, deployment readiness, robustness, benchmark
ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
