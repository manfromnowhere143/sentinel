# Iteration 95 - HUGSIM non-active surface branch arbitration: HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE

Status: `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE` (offline branch
arbitration over the two fixed non-active iteration-93 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, and did not retune Sentinel. It used only the committed
iteration-92, iteration-93, and iteration-94 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_nonactive_surface_branch_arbitration.py`](analyze_nonactive_surface_branch_arbitration.py)
- Tests:
  [`../../tests/test_iter95_nonactive_surface_branch_arbitration.py`](../../tests/test_iter95_nonactive_surface_branch_arbitration.py)
- Analyzer command:
  [`proof-branch/analyze_nonactive_surface_branch_arbitration.command.txt`](proof-branch/analyze_nonactive_surface_branch_arbitration.command.txt)
- JSON report:
  [`proof-branch/nonactive_surface_branch_arbitration_report.json`](proof-branch/nonactive_surface_branch_arbitration_report.json)
- Markdown report:
  [`proof-branch/nonactive_surface_branch_arbitration.md`](proof-branch/nonactive_surface_branch_arbitration.md)

## Result

The analyzer cross-checked:

- iteration-92 verdict: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`;
- iteration-93 verdict: `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`;
- iteration-94 verdict: `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`;
- both fixed non-active rows exist exactly once in iteration 92 and iteration 93;
- the registered iteration-92 and iteration-93 row labels match both rows;
- no source row has row-level problems.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `nonactive_surface_provenance_ttc_borderline_over_path_cpa`: `1`;
  - `nonactive_surface_path_cpa_over_provenance_bridge`: `1`;
- surface matches path events: `1`;
- surface matches provenance events: `1`;
- provenance finite-TTC events: `1`;
- path better-CPA-rank events: `2`;
- provenance closer-bridge events: `2`.

| audit id | event | surface object | branch | path object | path CPA/rank | provenance object | provenance TTC | provenance bridge |
|---|---|---:|---|---:|---|---:|---|---|
| `both_distinct_extreme` | `pre` | `9` | `provenance_ttc_borderline` | `5` | `6.4909 / 1` | `9` | `4.7761` | `match`, `0.9876 m` |
| `ttc_medium_a` | `pre` | `19` | `path_cpa_over_bridge` | `19` | `6.3299 / 1` | `3` | `null` | `match`, `0.7077 m` |

## Interpretation

Iteration 95 closes the two non-active surface-winner branches from the fixed replay rows.
`both_distinct_extreme` follows provenance: object `9` is the surface/provenance winner, is
bridge-matched, and has finite TTC at `4.7761 s`, even though path object `5` has better CPA and
rank. The `ttc_medium_a` pre row follows path: both path object `19` and provenance object `3`
are subthreshold and TTC-null, so the surface follows the lower-CPA/better-rank path object
despite the provenance object having closer bridge support.

This narrows the fixed-row mechanism into two non-active branches: a TTC-borderline provenance
branch and a CPA/rank path branch. Read with iteration 94, all three fixed iteration-93 surface
winner rows now have a local branch explanation from committed reports only.

## Claim boundary

Two-row descriptive non-active surface branch arbitration only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
