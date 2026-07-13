# Iteration 67 - trigger-target bridge audit: TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE

Status: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE` (offline trigger/target bridge audit over the
two iteration-66 rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59, iteration-61, iteration-64,
iteration-65, and iteration-66 proof.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_trigger_target_bridge.py`](analyze_trigger_target_bridge.py)
- Tests: [`../../tests/test_iter67_trigger_target_bridge.py`](../../tests/test_iter67_trigger_target_bridge.py)
- Analyzer command: [`proof-trigger-target/analyze_trigger_target_bridge.command.txt`](proof-trigger-target/analyze_trigger_target_bridge.command.txt)
- JSON report: [`proof-trigger-target/trigger_target_report.json`](proof-trigger-target/trigger_target_report.json)
- Markdown report: [`proof-trigger-target/trigger_target.md`](proof-trigger-target/trigger_target.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-64 verdict: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`;
- iteration-65 verdict: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`;
- iteration-66 verdict: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`;
- exactly the two fixed iteration-66 rows:
  - `ttc_extreme_short` / `scene-0038-extreme-00` / target `object_id=2`;
  - `cpa_medium_b` / `scene-0166-medium-00` / target `object_id=6`.

It then compared each row's target object and first-fire trigger object to eligible foreground
provenance rows under the same frozen 16-variant bridge grid used by iteration 64.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `same_object_target_trigger_match`: `1`;
  - `split_target_match_trigger_match`: `1`;
- same-object rows: `1`;
- split-object rows: `1`;
- target bridge-match rows: `2`;
- trigger bridge-match rows: `2`;
- verdict: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`.

| audit id | scenario | target | trigger | row label | target best | trigger best | first-fire trigger best |
|---|---|---:|---:|---|---:|---:|---:|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `2` | `2` | `same_object_target_trigger_match` | `1.6718 m` | `1.6718 m` | `6.9272 m` |
| `cpa_medium_b` | `scene-0166-medium-00` | `6` | `1` | `split_target_match_trigger_match` | `0.4325 m` | `2.8332 m` | `19.6983 m` |

## Interpretation

Iteration 67 confirms one same-object row and one split-object row.

In `ttc_extreme_short`, the target and first-fire trigger are the same monitor object
(`object_id=2`). Across the pre-contact window that object has a foreground bridge match
(`1.6718 m`), while at the first-fire timestamp alone its best bridge distance is outside support
(`6.9272 m`). This remains a late-emerging same-object hazard/timing case.

In `cpa_medium_b`, the target and first-fire trigger differ. The foreground-bridged target
(`object_id=6`) has the best support (`0.4325 m`), but the CPA trigger object (`object_id=1`)
also has a full-window bridge match (`2.8332 m`) at a later pre-contact decision timestamp.
However, the trigger object at the actual first-fire timestamp has no bridge support
(`19.6983 m`).

So the split row is not a simple "trigger object has no bridge support anywhere" case. It is a
timing/provenance split: at first fire the trigger object is not bridge-supported, while later
pre-contact geometry can bridge both the target and the trigger object under the frozen grid.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result only classifies two fixed
trigger/target bridge surfaces selected by iteration 66.
