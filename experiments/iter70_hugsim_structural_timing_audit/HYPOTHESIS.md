# Iteration 70 - HUGSIM structural-row timing audit

Status: `PRE_REGISTERED`

## Question

Iteration 69 synthesized the eight iteration-59 HUGSIM ON actor-match rows into a mechanism
taxonomy. The three classifiable foreground rows are now refined, but the five structural rows
remain coarse:

- `no_monitor_fire`: `2`;
- `post_collision_fire`: `2`;
- `background_collision_only`: `1`.

This iteration asks the next narrow structural question:

Can the five structural rows be separated into foreground-present surface-silent rows,
foreground-present late-fire rows, and foreground-absent/background-only rows using only the
committed iteration-59 proof and the committed iteration-69 taxonomy?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts;
- committed iteration-69 mechanism-taxonomy report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed rows

The fixed rows are exactly the five iteration-69 structural rows, in iteration-59 schedule order:

- `mixed_extreme` / `scene-0062-extreme-00` / `no_monitor_fire`;
- `both_distinct_extreme` / `scene-0138-extreme-00` / `post_collision_fire`;
- `nofire_hard_control` / `scene-0041-hard-00` / `no_monitor_fire`;
- `cpa_medium_a` / `scene-0071-medium-00` / `background_collision_only`;
- `ttc_medium_a` / `scene-0071-medium-01` / `post_collision_fire`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 69: `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`.
2. Select exactly the five fixed structural rows from the iteration-69 taxonomy, preserving
   iteration-59 schedule order.
3. For each row, cross-check the matching iteration-59 report row:
   - support label;
   - first-fire timestamp;
   - first-fire channel;
   - fired frames;
   - brake frames;
   - first foreground timestamp;
   - foreground count;
   - monitor frame count.
4. Load the row's committed iteration-59 ON decision log only to independently summarize:
   - monitor frames;
   - fired frames;
   - brake frames;
   - first fired timestamp and channel;
   - whether any fire occurred before or at first foreground timestamp when foreground exists.
5. Assign one registered structural label per row.
6. Emit a JSON report and Markdown table with counts, per-row timing deltas, source fields, and
   any row-level inconsistencies.

## Registered structural labels

- `foreground_present_surface_silent`: foreground provenance exists, but the monitor never fires.
- `foreground_present_late_fire`: foreground provenance exists, and first monitor fire occurs
  strictly after first foreground timestamp.
- `foreground_absent_background_only`: no foreground provenance exists for the collision row,
  leaving the row background-only under iteration 59.
- `structural_timing_inconsistent`: committed report and decision-log facts disagree, or a row
  cannot satisfy any registered structural label.

## Registered verdicts

- `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`: all five fixed rows are classified with no
  infrastructure problems and the labels include at least one
  `foreground_present_surface_silent`, one `foreground_present_late_fire`, and one
  `foreground_absent_background_only`.
- `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_PARTIAL`: all five fixed rows are classified with no
  infrastructure problems, but fewer than all three expected structural labels appear.
- `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED`: source verdicts, row identities, decision logs,
  or report/log cross-checks fail, preventing the five-row audit from being produced.

## Claim boundary

This is a five-row structural timing/support audit only. It cannot claim actor causality, repair,
transfer improvement, safety, deployment readiness, robustness, benchmark ranking,
HD-Score-invariance, population mismatch rate, retuning value, or commercial value. It may only
state the registered structural labels for the fixed five rows.
