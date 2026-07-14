# Iteration 114 - HUGSIM support-core mismatch-geometry decomposition: HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE` (offline geometry decomposition of the
eight committed iteration-113 support-core mismatch vectors).

This iteration used only the committed iteration-113 actor-match report. It launched no GPU work,
reran no actor-match classifier, changed no thresholds, changed no planner/action-control code,
changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_mismatch_geometry.py`](analyze_support_core_mismatch_geometry.py)
- Tests:
  [`../../tests/test_iter114_support_core_mismatch_geometry.py`](../../tests/test_iter114_support_core_mismatch_geometry.py)
- Analyzer command:
  [`proof-geometry/analyze_support_core_mismatch_geometry.command.txt`](proof-geometry/analyze_support_core_mismatch_geometry.command.txt)
- JSON report:
  [`proof-geometry/support_core_mismatch_geometry_report.json`](proof-geometry/support_core_mismatch_geometry_report.json)
- Markdown report:
  [`proof-geometry/support_core_mismatch_geometry.md`](proof-geometry/support_core_mismatch_geometry.md)

## Result

Infrastructure passed and all `8` mismatch rows received frozen geometry labels:

- row count: `8`;
- problem row count: `0`;
- geometry-label counts:
  - `far_behind_lateral_near`: `5`;
  - `far_behind_lateral_far`: `2`;
  - `far_ahead_lateral_far`: `1`;
- forward-relation counts:
  - `monitor_far_behind`: `7`;
  - `monitor_far_ahead`: `1`;
- lateral-relation counts:
  - `monitor_lateral_near`: `5`;
  - `monitor_far_right`: `3`;
- dominant-component counts:
  - `forward_dominant`: `8`;
- bridge-distance range: `14.472507961609738` to `36.09143899155716` m;
- absolute forward-delta range: `12.638445243704446` to `36.05451869836678` m;
- absolute lateral-delta range: `1.6320692112815172` to `16.504205595491126` m.

Per-row geometry summary:

| slot | scenario | run | geometry | forward | lateral | dominant | delta forward | delta lateral | distance |
|---:|---|---:|---|---|---|---|---:|---:|---:|
| 1 | `scene-0411-hard-00` | 2 | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-23.506868694236438` | `3.6793055233027125` | `23.793069683037515` |
| 2 | `scene-0411-extreme-00` | 1 | `far_ahead_lateral_far` | `monitor_far_ahead` | `monitor_far_right` | `forward_dominant` | `18.22898787802343` | `-16.504205595491126` | `24.59033959495813` |
| 3 | `scene-0038-hard-00` | 1 | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-13.335525415682211` | `-5.622921712646466` | `14.472507961609738` |
| 4 | `scene-0038-extreme-00` | 1 | `far_behind_lateral_far` | `monitor_far_behind` | `monitor_far_right` | `forward_dominant` | `-12.638445243704446` | `-8.904216683620547` | `15.460122021736504` |
| 5 | `scene-0038-extreme-00` | 2 | `far_behind_lateral_far` | `monitor_far_behind` | `monitor_far_right` | `forward_dominant` | `-12.684481107615593` | `-8.979239007955975` | `15.541003639773562` |
| 6 | `scene-0383-extreme-00` | 2 | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-36.05451869836678` | `-1.6320692112815172` | `36.09143899155716` |
| 7 | `scene-0411-hard-00` | 1 | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-22.669632478607582` | `4.840797623268669` | `23.180715225043926` |
| 8 | `scene-0411-extreme-00` | 2 | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-24.74298187779935` | `1.8560289568118495` | `24.812496764606966` |

## Interpretation

Iteration 114 decomposes the eight already-supported actor mismatches from iteration 113. The
dominant component is longitudinal in every row (`8/8` `forward_dominant`). In `7/8` rows, the
monitor object's propagated position is far behind the first foreground collision actor under the
frozen bridge. The remaining row is far ahead and laterally far.

This is a descriptive geometry result only. It does not prove why the planner crashed, why the
monitor fired, whether the monitor selected the wrong object, or whether a repair exists. It does
make the next audit sharper: inspect monitor-object and collision-actor temporal/object-set
ordering in these same eight rows, rather than launching another GPU batch.

## Claim boundary

Descriptive geometry decomposition of eight committed support-core mismatch vectors only; no
repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
