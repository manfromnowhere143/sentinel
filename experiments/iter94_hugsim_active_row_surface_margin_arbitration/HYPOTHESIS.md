# Iteration 94 - HUGSIM active-row surface margin arbitration

## Research question

In the fixed `ttc_medium_a` active replay row, does the released surface choose object `24`
because it is the only active CPA/path candidate, while all provenance/bridge-supported
candidates are non-active, CPA-far, and have no finite TTC?

## Scope

This is an offline report-level audit. It may read only these committed reports:

- `experiments/iter91_hugsim_active_gap_geometry_decomposition/proof-geometry/active_gap_geometry_report.json`
- `experiments/iter92_hugsim_path_proximity_arbitration/proof-arbitration/path_proximity_arbitration_report.json`
- `experiments/iter93_hugsim_surface_winner_alignment/proof-alignment/surface_winner_alignment_report.json`

It must not read raw decision logs, launch Docker, touch the GPU box, run HUGSIM, modify
thresholds, tune parameters, or infer vehicle outcomes.

## Frozen row

- audit id: `ttc_medium_a`
- scenario: `scene-0071-medium-01`
- event role: `active`
- replay alignment: `nearest_before_bridge_ts`
- replay timestamp: `5.75`

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 91 verdict is `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`.
2. Iteration 92 verdict is `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`.
3. Iteration 93 verdict is `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`.
4. The frozen row exists exactly once in all three reports.
5. Iteration 91 row label is `path_active_provenance_far_with_bridge_nonactive`.
6. Iteration 92 row label is `path_best_active_no_bridge`.
7. Iteration 93 row label is `surface_follows_path_active_no_bridge`.
8. Iteration 93 has `surface_matches_path == true` and `surface_matches_provenance == false`.
9. Iteration 92 path-best, iteration 93 surface-best, and iteration 91 active candidate identify
   the same object.

## Fixed measurements

For the frozen row, compute:

- number of active candidates in iteration 91;
- number of bridge-supported candidates in iteration 91;
- active candidate object id, state, bridge band, `min_cpa`, `cpa_rank`, `ttc`, and
  `active_cpa_margin_m`;
- bridge-supported candidate object ids, states, bridge bands, `min_cpa`, `cpa_rank`, `ttc`, and
  `active_cpa_margin_m`;
- minimum bridge-supported active CPA margin and its object id;
- whether any bridge-supported candidate is active or borderline;
- whether any bridge-supported candidate has finite TTC;
- whether the active candidate has lower CPA and better CPA rank than every bridge-supported
  candidate.

## Completion labels

- `active_row_cpa_margin_overrides_provenance`: exactly one active candidate exists; it is the
  same object as the iteration-92 path-best and iteration-93 surface-best object; it has
  `state == active`, bridge band `no_support`, and negative `active_cpa_margin_m`; every
  bridge-supported candidate is non-active, has positive `active_cpa_margin_m`, has no finite
  TTC, and has worse CPA/rank than the active candidate.
- `active_row_bridge_candidate_surface_near`: at least one bridge-supported candidate is active
  or borderline, has non-positive `active_cpa_margin_m`, or has finite TTC.
- `active_row_surface_margin_mixed`: source checks pass, but neither of the above labels fully
  holds.
- `active_row_surface_margin_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`: the row receives
  `active_row_cpa_margin_overrides_provenance`.
- `HUGSIM_ACTIVE_ROW_BRIDGE_CANDIDATE_SURFACE_NEAR_COMPLETE`: the row receives
  `active_row_bridge_candidate_surface_near`.
- `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_MIXED_COMPLETE`: the row receives
  `active_row_surface_margin_mixed`.
- `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_BLOCKED`: source checks fail or the row receives
  `active_row_surface_margin_insufficient`.

## Claim boundary

One-row descriptive active-row margin arbitration only. This does not claim actor causality,
repair, threshold value, transfer, safety, deployment, robustness, benchmark performance,
population rate, HD-Score invariance, commercial value, real-world behavior, first-responder
behavior, or retuning.
