# Iteration 96 - HUGSIM branch taxonomy outcome bridge: HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE

Status: `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE` (offline bridge audit from
the fixed branch taxonomy to the iteration-70 late-fire structural outcomes).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, and did not retune Sentinel. It used only the committed
iteration-70, iteration-94, and iteration-95 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_branch_outcome_bridge.py`](analyze_branch_outcome_bridge.py)
- Tests: [`../../tests/test_iter96_branch_outcome_bridge.py`](../../tests/test_iter96_branch_outcome_bridge.py)
- Analyzer command: [`proof-outcome/analyze_branch_outcome_bridge.command.txt`](proof-outcome/analyze_branch_outcome_bridge.command.txt)
- JSON report: [`proof-outcome/branch_outcome_bridge_report.json`](proof-outcome/branch_outcome_bridge_report.json)
- Markdown report: [`proof-outcome/branch_outcome_bridge.md`](proof-outcome/branch_outcome_bridge.md)

## Result

The analyzer cross-checked:

- iteration-70 verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
- iteration-94 verdict: `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`;
- iteration-95 verdict: `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE`;
- both frozen rows exist exactly once in iteration 70;
- both rows are `foreground_present_late_fire`;
- both rows have `iter59_support_label == post_collision_fire`;
- both rows have `pre_or_at_foreground_fire == false`;
- both rows have `fire_minus_foreground_s == 1.75`;
- the expected iteration-94 and iteration-95 branch labels join exactly.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `late_fire_with_provenance_ttc_branch`: `1`;
  - `late_fire_with_path_cpa_branch`: `1`;
- late-fire rows: `2`;
- no-pre-foreground-fire rows: `2`;
- provenance/TTC branch rows: `1`;
- path/CPA branch rows: `1`;
- active CPA branch rows: `1`.

| audit id | first foreground | first fire | delta | channel | branch labels | outcome label |
|---|---:|---:|---:|---|---|---|
| `both_distinct_extreme` | `5.25` | `7.00` | `1.75` | `ttc_only` | `nonactive_surface_provenance_ttc_borderline_over_path_cpa` | `late_fire_with_provenance_ttc_branch` |
| `ttc_medium_a` | `3.25` | `5.00` | `1.75` | `cpa_only` | `nonactive_surface_path_cpa_over_provenance_bridge`; `active_row_cpa_margin_overrides_provenance` | `late_fire_with_path_cpa_branch` |

## Interpretation

Iteration 96 connects the fixed branch taxonomy back to the committed late-fire outcome boundary.
The two post-collision-fire structural rows have different surface branch explanations:
`both_distinct_extreme` joins to the provenance/TTC-borderline branch, while `ttc_medium_a` joins
to the path/CPA branch plus the active CPA/path branch. Even with those different branches, both
rows share the same structural outcome: first fire occurs `+1.75 s` after foreground contact, and
there are zero pre-or-at foreground fire frames.

This means the fixed-row branch split is not, by itself, an outcome separator between the two
late-fire rows. It is a mechanism bridge: different surface branches can sit inside the same
post-collision-fire timing class. That statement is descriptive and bounded to the two committed
rows.

## Claim boundary

Two-row descriptive branch-taxonomy/outcome bridge only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
