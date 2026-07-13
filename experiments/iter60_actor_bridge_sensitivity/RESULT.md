# Iteration 60 - actor-match bridge sensitivity: BRIDGE_AMBIGUOUS_NULL

Status: `BRIDGE_AMBIGUOUS_NULL` (offline sensitivity audit over the three iteration-59
classifiable actor-match rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only the committed iteration-59 proof and report, then evaluated the
pre-registered bridge-variant grid.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_bridge_sensitivity.py`](analyze_bridge_sensitivity.py)
- Tests: [`../../tests/test_iter60_bridge_sensitivity.py`](../../tests/test_iter60_bridge_sensitivity.py)
- Analyzer command: [`proof-bridge/analyze_bridge_sensitivity.command.txt`](proof-bridge/analyze_bridge_sensitivity.command.txt)
- JSON report: [`proof-bridge/bridge_sensitivity_report.json`](proof-bridge/bridge_sensitivity_report.json)
- Markdown report: [`proof-bridge/bridge_sensitivity.md`](proof-bridge/bridge_sensitivity.md)

## Result

The analyzer cross-checked the iteration-59 report verdict as `ACTOR_MATCH_AUDIT_COMPLETE` and
found exactly the three registered `classifiable_foreground` rows. It then evaluated exactly
`16` variants per row: first-fire vs foreground-time propagated object position, the two frozen
axis orders, and all four sign combinations.

Summary:

- `iter59_classifiable_rows`: `3`;
- `variant_rows_evaluated`: `3`;
- `variants_per_row`: `16`;
- sensitivity counts:
  - `robust_mismatch`: `2`;
  - `bridge_ambiguous_possible`: `1`;
- minimum distance across the full grid: `5.664876449943843 m`;
- verdict: `BRIDGE_AMBIGUOUS_NULL`.

| audit id | scenario | iteration-59 distance | best grid distance | best label | best variant |
|---|---|---:|---:|---|---|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `15.4330` | `8.6525` | `robust_mismatch` | `first_fire/yx/-1/-1` |
| `cpa_medium_b` | `scene-0166-medium-00` | `21.9863` | `19.6983` | `robust_mismatch` | `first_fire/yx/+1/-1` |
| `ttc_extreme_b` | `scene-0383-extreme-00` | `37.0380` | `5.6649` | `bridge_ambiguous_possible` | `first_fire/yx/-1/+1` |

## Interpretation

The strongest iteration-59 headline is narrowed. None of the 48 pre-registered bridge variants
turned a classifiable row into `bridge_match_possible` (`<= 3.0 m`), so the three actor-mismatch
rows do not disappear under the bounded axis/sign/temporal sensitivity grid.

But one row, `ttc_extreme_b`, becomes `bridge_ambiguous_possible` at `5.6649 m`. Therefore the
registered robust-all-row bar is not met. The correct conclusion is an ambiguity null: the
bounded grid finds no match, but it also does not support claiming that all three classifiable
iteration-59 rows are robust mismatches under every plausible bridge variant.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result says only that the three
iteration-59 classifiable rows were stress-tested under the frozen bridge grid: zero became
matches, one became ambiguous, and two remained robust mismatches.
