# Iteration 68 - fire-time bridge decomposition audit: FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE

Status: `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE` (offline fire-time bridge decomposition
over the two iteration-67 first-fire trigger objects).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59, iteration-61, iteration-64,
iteration-65, iteration-66, and iteration-67 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_fire_time_bridge_decomposition.py`](analyze_fire_time_bridge_decomposition.py)
- Tests: [`../../tests/test_iter68_fire_time_bridge_decomposition.py`](../../tests/test_iter68_fire_time_bridge_decomposition.py)
- Analyzer command: [`proof-fire-time/analyze_fire_time_bridge_decomposition.command.txt`](proof-fire-time/analyze_fire_time_bridge_decomposition.command.txt)
- JSON report: [`proof-fire-time/fire_time_report.json`](proof-fire-time/fire_time_report.json)
- Markdown report: [`proof-fire-time/fire_time.md`](proof-fire-time/fire_time.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-64 verdict: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`;
- iteration-65 verdict: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`;
- iteration-66 verdict: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`;
- iteration-67 verdict: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`;
- exactly the two fixed trigger rows:
  - `ttc_extreme_short` / `scene-0038-extreme-00` / trigger `object_id=2`;
  - `cpa_medium_b` / `scene-0166-medium-00` / trigger `object_id=1`.

It then decomposed each trigger object's first-fire unsupported bridge surface against that same
trigger object's best full-window bridge match.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `fire_gap_best_before_fire`: `1`;
  - `fire_gap_best_after_fire`: `1`;
- before-fire rows: `1`;
- after-fire rows: `1`;
- verdict: `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE`.

| audit id | scenario | trigger | label | first fire | fire distance | best decision | best distance | improvement |
|---|---|---:|---|---:|---:|---:|---:|---:|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `2` | `fire_gap_best_before_fire` | `1.50 s` | `6.9272 m` | `0.25 s` | `1.6718 m` | `5.2554 m` |
| `cpa_medium_b` | `scene-0166-medium-00` | `1` | `fire_gap_best_after_fire` | `0.25 s` | `19.6983 m` | `2.25 s` | `2.8332 m` | `16.8651 m` |

## Interpretation

Iteration 68 shows the fire-time bridge gap is not one timing pattern.

For `ttc_extreme_short`, the first-fire trigger object (`object_id=2`) has its best bridge match
before first fire: `0.25 s`, which is `1.25 s` before the `1.50 s` fire timestamp. At fire time
the same object is already a TTC hazard, but its nearest bridge support is outside the frozen
support band (`6.9272 m`). This is a late-fire / earlier-bridge-support pattern.

For `cpa_medium_b`, the first-fire trigger object (`object_id=1`) has its best bridge match
after first fire: `2.25 s`, which is `2.00 s` after the `0.25 s` CPA fire timestamp. At fire
time the trigger is unsupported by the bridge (`19.6983 m`), while later pre-contact geometry
becomes matchable (`2.8332 m`). This is an early-fire / later-bridge-support pattern.

The mechanism map therefore splits again: the first-fire bridge gap can come from firing after
the best bridge-supported geometry has passed, or firing before bridge-supported geometry
appears. That supports a timing/provenance decomposition, not threshold retuning.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result only classifies two fixed
first-fire trigger bridge decompositions selected by iteration 67.
