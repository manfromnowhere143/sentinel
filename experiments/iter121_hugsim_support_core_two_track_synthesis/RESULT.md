# Iteration 121 - HUGSIM support-core two-track synthesis: HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE` (report-level synthesis over the
committed iteration-118, iteration-119, and iteration-120 reports).

This iteration used only committed reports. It read no raw decision logs, launched no GPU work,
reran no actor-match classifier, changed no thresholds, changed no planner/action-control code,
changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_two_track_synthesis.py`](analyze_support_core_two_track_synthesis.py)
- Tests:
  [`../../tests/test_iter121_support_core_two_track_synthesis.py`](../../tests/test_iter121_support_core_two_track_synthesis.py)
- Analyzer command:
  [`proof-synthesis/analyze_support_core_two_track_synthesis.command.txt`](proof-synthesis/analyze_support_core_two_track_synthesis.command.txt)
- JSON report:
  [`proof-synthesis/support_core_two_track_synthesis_report.json`](proof-synthesis/support_core_two_track_synthesis_report.json)
- Markdown report:
  [`proof-synthesis/support_core_two_track_synthesis.md`](proof-synthesis/support_core_two_track_synthesis.md)

## Result

Infrastructure passed and all `8` rows received frozen two-track synthesis measurements and one
synthesis label:

- row count: `8`;
- problem row count: `0`;
- two-track split count: `8`;
- synthesis-label counts:
  - `two_track_pre_support_lost_absent_selected_not_nearest`: `2`;
  - `two_track_pre_support_lost_absent_selected_nearest`: `2`;
  - `two_track_post_fire_support_selected_nearest`: `2`;
  - `two_track_pre_support_drifted_selected_not_nearest`: `1`;
  - `two_track_never_supported_selected_nearest`: `1`;
- support lifecycle counts:
  - `pre_fire_object_absent_at_fire`: `4`;
  - `pre_fire_object_drifted_outside_support_at_fire`: `1`;
  - `post_fire_support_only_different_object_active_support`: `1`;
  - `post_fire_support_only_far_support`: `1`;
  - `never_supported_reference`: `1`;
- selected lifecycle counts:
  - `selected_never_supported_before_collision`: `8`;
- selected is first-fire nearest: `5/8`;
- selected is not first-fire nearest: `3/8`.

Per-row synthesis summary:

| slot | scenario | run | synthesis | support lifecycle | replacement | selected lifecycle | two-track |
|---:|---|---:|---|---|---|---|---|
| 1 | `scene-0411-hard-00` | 2 | `two_track_pre_support_lost_absent_selected_not_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_not_nearest` | `selected_never_supported_before_collision` | `true` |
| 2 | `scene-0411-extreme-00` | 1 | `two_track_pre_support_drifted_selected_not_nearest` | `pre_fire_object_drifted_outside_support_at_fire` | `pre_fire_drifted_selected_not_nearest` | `selected_never_supported_before_collision` | `true` |
| 3 | `scene-0038-hard-00` | 1 | `two_track_never_supported_selected_nearest` | `never_supported_reference` | `never_supported_reference_selected_nearest` | `selected_never_supported_before_collision` | `true` |
| 4 | `scene-0038-extreme-00` | 1 | `two_track_post_fire_support_selected_nearest` | `post_fire_support_only_different_object_active_support` | `post_fire_support_selected_nearest` | `selected_never_supported_before_collision` | `true` |
| 5 | `scene-0038-extreme-00` | 2 | `two_track_post_fire_support_selected_nearest` | `post_fire_support_only_far_support` | `post_fire_support_selected_nearest` | `selected_never_supported_before_collision` | `true` |
| 6 | `scene-0383-extreme-00` | 2 | `two_track_pre_support_lost_absent_selected_not_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_not_nearest` | `selected_never_supported_before_collision` | `true` |
| 7 | `scene-0411-hard-00` | 1 | `two_track_pre_support_lost_absent_selected_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_nearest` | `selected_never_supported_before_collision` | `true` |
| 8 | `scene-0411-extreme-00` | 2 | `two_track_pre_support_lost_absent_selected_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_nearest` | `selected_never_supported_before_collision` | `true` |

## Interpretation

Iteration 121 consolidates the support-core line into one row-level mechanism map. All eight rows
preserve the two-track split:

- the support-side object either disappears, drifts outside support, appears only after fire, or is
  absent as a reference branch; and
- the selected fire-side object is never supported before collision.

The selected-vs-nearest split remains relevant but secondary. In `5/8` rows the selected object is
the nearest first-fire replacement, and in `3/8` it is not; however, iteration 120 showed all
selected fire-side objects are never supported, and iteration 119 showed all first-fire nearest
replacements remain outside support. The support-core mechanism at this evidence level is therefore
a two-track timing/object identity separation, not a simple final-rank selection error.

This is descriptive only. It does not prove track failure, sensor failure, actor causality, monitor
causality, planner causality, repair feasibility, threshold value, or safety impact. The next
narrower action should be documentation integration: update the technical report/manuscript or a
dedicated mechanism note with this support-core taxonomy and its claim boundary, rather than adding
another raw-log audit to the same eight rows.

## Claim boundary

Descriptive support-core two-track synthesis of committed reports only; no repair, actor-causality,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim.
