# Iteration 73 - HUGSIM structural margin transition audit

Status: `PRE_REGISTERED`

## Question

Iterations 70-72 split the foreground-present structural HUGSIM rows into two branches:

- surface-silent rows: foreground exists, Sentinel never fires, and iteration 71 found both rows
  far from the frozen CPA/TTC trigger surfaces before foreground contact;
- late-fire rows: foreground exists, Sentinel first fires `1.75 s` after foreground contact, and
  iteration 72 found both rows near but not crossing a frozen trigger surface before contact.

This iteration asks the comparative timeline question:

Across the four foreground-present structural rows, does the committed decision-log timeline
support a branch split between rows that remain far/never-active and rows that become active only
after foreground contact?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-70 structural timing report;
- committed iteration-71 surface-silent margin report;
- committed iteration-72 late-fire prefire margin report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the four iteration-70 foreground-present structural rows:

- `mixed_extreme` / `scene-0062-extreme-00` / `foreground_present_surface_silent`;
- `nofire_hard_control` / `scene-0041-hard-00` / `foreground_present_surface_silent`;
- `both_distinct_extreme` / `scene-0138-extreme-00` / `foreground_present_late_fire`;
- `ttc_medium_a` / `scene-0071-medium-01` / `foreground_present_late_fire`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 70: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
   - iteration 71: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`;
   - iteration 72: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`.
2. Cross-check the fixed row identities and labels against iterations 70-72.
3. For each fixed row, load only the committed iteration-59 ON decision log.
4. Read frozen thresholds from logged `params` and scan the full monitor timeline.
5. Compute:
   - first foreground timestamp;
   - first fire timestamp;
   - first near-margin timestamp for TTC and CPA;
   - first active crossing timestamp for TTC and CPA;
   - first active crossing timestamp across either channel;
   - each timestamp's offset from first foreground;
   - whether active crossing occurs before, at, after, or never relative to first foreground.
6. Assign one registered row label per row.
7. Emit JSON and Markdown proof with per-row timelines and branch counts.

## Registered row labels

- `silent_far_never_active`: surface-silent row, no active crossing anywhere in the decision log.
- `silent_active_after_contact_inconsistent`: surface-silent row with active crossing after
  foreground contact despite no recorded fire.
- `silent_active_before_contact_inconsistent`: surface-silent row with active crossing before or
  at foreground contact despite no recorded fire.
- `late_prefire_near_postcontact_active`: late-fire row with near-margin evidence before
  foreground contact and first active crossing after foreground contact.
- `late_active_before_contact_inconsistent`: late-fire row with active crossing before or at
  foreground contact.
- `late_no_postcontact_active_inconsistent`: late-fire row with no active crossing after
  foreground contact.
- `margin_transition_insufficient`: required row/log/threshold facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`: both surface-silent rows are
  `silent_far_never_active` and both late-fire rows are `late_prefire_near_postcontact_active`.
- `HUGSIM_MARGIN_TRANSITION_MIXED_COMPLETE`: all four rows are classified with no infrastructure
  problems, but the exact split above does not hold.
- `HUGSIM_MARGIN_TRANSITION_BLOCKED`: source verdicts, row identities, decision logs, or required
  threshold fields fail cross-checks.

## Claim boundary

This is a four-row descriptive margin-transition audit only. It cannot claim actor causality,
repair, threshold value, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population rate, retuning value, or commercial value.
