# Iteration 93 - HUGSIM surface-winner alignment audit: HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE

Status: `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE` (offline selector-alignment audit over
the three fixed iteration-92 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, and did not retune Sentinel. It used only the committed
iteration-92 report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_surface_winner_alignment.py`](analyze_surface_winner_alignment.py)
- Tests: [`../../tests/test_iter93_surface_winner_alignment.py`](../../tests/test_iter93_surface_winner_alignment.py)
- Analyzer command: [`proof-alignment/analyze_surface_winner_alignment.command.txt`](proof-alignment/analyze_surface_winner_alignment.command.txt)
- JSON report: [`proof-alignment/surface_winner_alignment_report.json`](proof-alignment/surface_winner_alignment_report.json)
- Markdown report: [`proof-alignment/surface_winner_alignment.md`](proof-alignment/surface_winner_alignment.md)

## Result

The analyzer cross-checked:

- iteration-92 verdict: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`;
- exactly the three fixed iteration-92 replay rows;
- zero path/provenance same-object events in iteration 92;
- the registered iteration-92 row-label split.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `surface_follows_path_active_no_bridge`: `1`;
  - `surface_follows_path_nonactive`: `1`;
  - `surface_follows_provenance_nonactive`: `1`;
- surface matches path events: `2`;
- surface matches provenance events: `1`;
- path matches provenance events: `0`.

| audit id | event | surface best | surface state | surface bridge | matches path | matches provenance | label |
|---|---|---:|---|---|---|---|---|
| `both_distinct_extreme` | `pre` | `9` | `borderline` | `match` | `False` | `True` | `surface_follows_provenance_nonactive` |
| `ttc_medium_a` | `pre` | `19` | `subthreshold` | `ambiguous` | `True` | `False` | `surface_follows_path_nonactive` |
| `ttc_medium_a` | `active` | `24` | `active` | `no_support` | `True` | `False` | `surface_follows_path_active_no_bridge` |

## Interpretation

Iteration 93 shows that the released surface winner is mixed across the fixed rows. In
`both_distinct_extreme`, `surface_best` follows provenance: object `9` is both surface-best and
provenance-best, bridge-matched and borderline, while path-best is a different no-support
subthreshold object. In `ttc_medium_a`, `surface_best` follows path in both rows. The pre row's
surface/path object `19` is still subthreshold and bridge-ambiguous; the active row's surface/path
object `24` is active but bridge `no_support`.

This means the failure mechanism is not simply "surface always follows path" or "surface always
follows provenance." The fixed rows show a mixed selector alignment, with the active failure row
specifically following path rather than provenance.

## Claim boundary

Three-row descriptive selector-alignment audit only; no actor-causality, repair, threshold-value,
transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance,
commercial-value, real-world behavior, first-responder behavior, or retuning claim.
