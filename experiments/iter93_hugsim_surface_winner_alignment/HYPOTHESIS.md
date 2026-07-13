# Iteration 93 - HUGSIM surface-winner alignment audit

Status: `PRE_REGISTERED`

## Question

Iteration 92 showed that CPA/path-best and provenance-best objects differ in all three fixed replay
rows. This iteration asks the immediate selector-alignment question:

When the released `surface_best` object is recorded beside `path_best` and `provenance_best`, does
`surface_best` align with path proximity, provenance proximity, or a mixed pattern across the fixed
rows?

This is not a repair, threshold search, actor-causality test, interpolation, retuning step, or new
simulator run. It only audits selector alignment already emitted in the committed iteration-92
proof.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-92 path-proximity arbitration report.

It must not read raw HUGSIM decision logs, `eval.json`, live box state, or GPU state; launch GPU
work; create HUGSIM episodes; modify simulator code; approve a patch; change thresholds; fit a
transform; retune Sentinel; interpolate metrics; or reinterpret simulation artifacts as live
system state.

## Fixed replay rows

The fixed replay rows are exactly the three iteration-92 evaluated rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  replay timestamp `5.5 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  replay timestamp `4.0 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  replay timestamp `5.75 s`, alignment `nearest_before_bridge_ts`.

## Registered procedure

1. Cross-check source verdict before analysis:
   - iteration 92: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`.
2. Cross-check that iteration 92 contains exactly the fixed replay rows above with no row
   problems, zero path/provenance same-object events, and the registered row-label split:
   - `path_best_no_bridge_provenance_best_nonactive`;
   - `path_best_bridge_supported_nonactive`;
   - `path_best_active_no_bridge`.
3. For each fixed row, read only the committed `path_best`, `provenance_best`, and `surface_best`
   compact candidate objects from the iteration-92 report.
4. Record whether `surface_best` matches `path_best`, `provenance_best`, both, or neither.
5. Record each selector object's state and bridge band.
6. Assign one registered row label per fixed replay row.
7. Emit JSON and Markdown proof with compact per-row selector alignment evidence.

## Registered labels

- `surface_follows_path_active_no_bridge`: `surface_best` matches `path_best`, the object is
  active, and it is not bridge-supported.
- `surface_follows_path_nonactive`: `surface_best` matches `path_best`, the object is non-active,
  and it does not also match `provenance_best`.
- `surface_follows_provenance_nonactive`: `surface_best` matches `provenance_best`, the object is
  non-active, and it does not also match `path_best`.
- `surface_path_provenance_same_nonactive`: all three selectors match the same non-active object.
- `surface_path_provenance_same_active`: all three selectors match the same active object.
- `surface_winner_alignment_insufficient`: required source, selector, row identity, compact
  candidate, or label fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`: every fixed row is classified without
  blocking, at least one row follows path, at least one row follows provenance, and no row is
  `surface_path_provenance_same_active`.
- `HUGSIM_SURFACE_WINNER_ALIGNMENT_PATH_ONLY_COMPLETE`: every fixed row follows path and no row is
  blocked.
- `HUGSIM_SURFACE_WINNER_ALIGNMENT_PROVENANCE_ONLY_COMPLETE`: every fixed row follows provenance
  and no row is blocked.
- `HUGSIM_SURFACE_WINNER_ALIGNMENT_ACTIVE_COINCIDENT_COMPLETE`: at least one row is
  `surface_path_provenance_same_active`, and no row is blocked.
- `HUGSIM_SURFACE_WINNER_ALIGNMENT_BLOCKED`: source verdicts, fixed row identities, selector
  fields, compact candidates, or labels fail cross-checks, or any row is
  `surface_winner_alignment_insufficient`.

## Claim boundary

This is a three-row descriptive selector-alignment audit only. It cannot claim actor causality,
repair, threshold value, transfer improvement, safety, deployment readiness, robustness, benchmark
ranking, HD-Score-invariance, population rate, retuning value, commercial value, or real-world/
first-responder behavior.
