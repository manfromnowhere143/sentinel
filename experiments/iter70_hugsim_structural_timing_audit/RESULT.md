# Iteration 70 - HUGSIM structural-row timing audit: HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE

Status: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE` (offline structural timing/support audit
over the five iteration-69 structural rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59 proof/report artifacts and the committed
iteration-69 taxonomy report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_structural_timing.py`](analyze_structural_timing.py)
- Tests: [`../../tests/test_iter70_structural_timing.py`](../../tests/test_iter70_structural_timing.py)
- Analyzer command: [`proof-structural/analyze_structural_timing.command.txt`](proof-structural/analyze_structural_timing.command.txt)
- JSON report: [`proof-structural/structural_report.json`](proof-structural/structural_report.json)
- Markdown report: [`proof-structural/structural.md`](proof-structural/structural.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-69 verdict: `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`;
- exactly the five fixed structural rows from iteration 69;
- report/log agreement for monitor frame counts, fired frame counts, brake frame counts, first
  fire timestamp, and first-fire channel.

Summary:

- target rows: `5`;
- evaluated rows: `5`;
- structural labels:
  - `foreground_present_surface_silent`: `2`;
  - `foreground_present_late_fire`: `2`;
  - `foreground_absent_background_only`: `1`;
- verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.

| audit id | scenario | iteration-59 support | structural label | first foreground | first fire | delta |
|---|---|---|---|---:|---:|---:|
| `mixed_extreme` | `scene-0062-extreme-00` | `no_monitor_fire` | `foreground_present_surface_silent` | `4.75 s` | none | none |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `post_collision_fire` | `foreground_present_late_fire` | `5.25 s` | `7.00 s` | `+1.75 s` |
| `nofire_hard_control` | `scene-0041-hard-00` | `no_monitor_fire` | `foreground_present_surface_silent` | `2.50 s` | none | none |
| `cpa_medium_a` | `scene-0071-medium-00` | `background_collision_only` | `foreground_absent_background_only` | none | `3.50 s` | none |
| `ttc_medium_a` | `scene-0071-medium-01` | `post_collision_fire` | `foreground_present_late_fire` | `3.25 s` | `5.00 s` | `+1.75 s` |

## Interpretation

Iteration 70 refines the structural side of the HUGSIM mechanism map.

The two `no_monitor_fire` rows are not background-only rows: both have foreground provenance, but
Sentinel never fires. The two `post_collision_fire` rows also have foreground provenance, but
Sentinel first fires `1.75 s` after the first foreground collision timestamp in both cases. The
remaining structural row is the true background-only case: the collision provenance has no
foreground actor support under iteration 59.

Read with iteration 69, the eight-row taxonomy is now fully split into six mechanism labels: three
classifiable foreground mechanisms plus three structural timing/support mechanisms. This remains
a mechanism audit, not a repair or retuning result.

## Claim boundary

No actor-causality, repair, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population mismatch-rate, retuning value, or commercial
value claim. This result only classifies the fixed five structural rows using committed
iteration-59 and iteration-69 evidence.
