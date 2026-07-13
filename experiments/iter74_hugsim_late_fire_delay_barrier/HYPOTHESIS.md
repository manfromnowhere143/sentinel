# Iteration 74 - HUGSIM late-fire delay barrier audit

Status: `PRE_REGISTERED`

## Question

Iterations 70, 72, and 73 narrowed the foreground-present late-fire branch:

- both fixed late-fire rows first fire `+1.75 s` after first foreground contact;
- both rows are near a frozen trigger surface before contact;
- neither row crosses an active CPA/TTC surface before contact;
- both rows first cross an active surface only after contact.

This iteration asks the next mechanism question:

For the two late-fire rows, is the post-contact fire a same-channel margin crossing from the
pre-contact near channel, or is it a cross-channel handoff where the channel that was near before
contact is not the channel that first becomes active after contact?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-72 late-fire prefire margin report;
- committed iteration-73 margin-transition report.

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
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
   - iteration 73: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`.
2. Cross-check the fixed row identities against iterations 70, 72, and 73.
3. For each fixed row, load only the committed iteration-59 ON decision log.
4. Read frozen thresholds from logged `params` on each decision row:
   - `ttc_thresh`;
   - `cpa_margin`.
5. Scan pre-foreground frames with `ts < first_foreground_ts` and compute:
   - any pre-foreground active TTC crossing;
   - any pre-foreground active CPA crossing;
   - closest positive TTC margin above `ttc_thresh`;
   - closest positive CPA margin above `cpa_margin`;
   - registered pre-foreground near-channel set using the iteration-72 bands.
6. Scan the full decision log and compute:
   - first active TTC timestamp;
   - first active CPA timestamp;
   - first active timestamp across either channel;
   - first active channel set (`ttc`, `cpa`, or both);
   - first active offset from first foreground contact.
7. Assign one registered row label per fixed row.
8. Emit JSON and Markdown proof with per-row pre-foreground channel facts, first-active facts,
   and the final branch counts.

## Registered margin bands

These bands are descriptive audit bins, not candidate thresholds:

- active TTC crossing: finite `min_ttc <= ttc_thresh`;
- active CPA crossing: `min_cpa <= cpa_margin`;
- near TTC margin: finite `0 < min_ttc - ttc_thresh <= 1.0 s`;
- near CPA margin: `0 < min_cpa - cpa_margin <= 1.5 m`.

## Registered row labels

- `cross_channel_late_activation`: no pre-foreground active crossing, exactly one
  pre-foreground near channel, first active crossing occurs after foreground contact, and the
  first active channel set is disjoint from the pre-foreground near-channel set.
- `same_channel_late_activation`: no pre-foreground active crossing, at least one
  pre-foreground near channel, first active crossing occurs after foreground contact, and the
  first active channel set intersects the pre-foreground near-channel set.
- `dual_near_late_activation`: no pre-foreground active crossing, both channels are near before
  foreground contact, and first active crossing occurs after foreground contact.
- `preforeground_active_inconsistent`: any pre-foreground frame crosses an active CPA/TTC
  surface despite the published late-fire timing.
- `no_preforeground_near_inconsistent`: no pre-foreground active crossing and no pre-foreground
  near channel exists despite the published iteration-72 result.
- `missing_postcontact_active_inconsistent`: no active crossing occurs after foreground contact
  despite the published iteration-73 result.
- `delay_barrier_insufficient`: required row/log/threshold facts are missing or inconsistent.

If both same-channel and dual-near conditions could apply, `dual_near_late_activation` takes
precedence because it is less specific about a single-channel barrier.

## Registered verdicts

- `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`: both fixed rows classify as
  `cross_channel_late_activation`.
- `HUGSIM_LATE_FIRE_DELAY_MIXED_COMPLETE`: both fixed rows are classified with no infrastructure
  problems, but the exact cross-channel split above does not hold.
- `HUGSIM_LATE_FIRE_DELAY_BLOCKED`: source verdicts, row identities, decision logs, or required
  threshold fields fail cross-checks, or any inconsistent label is emitted.

## Claim boundary

This is a two-row descriptive delay-barrier audit only. It cannot claim actor causality, repair,
threshold value, transfer improvement, safety, deployment readiness, robustness, benchmark
ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
