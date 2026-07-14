# Iteration 114 - HUGSIM support-core mismatch-geometry decomposition

Verdict: `HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `geometry_label_counts`: `{'far_ahead_lateral_far': 1, 'far_behind_lateral_far': 2, 'far_behind_lateral_near': 5}`
- `forward_relation_counts`: `{'monitor_far_ahead': 1, 'monitor_far_behind': 7}`
- `lateral_relation_counts`: `{'monitor_far_right': 3, 'monitor_lateral_near': 5}`
- `dominant_component_counts`: `{'forward_dominant': 8}`
- `bridge_distance_m`: `{'min': 14.472507961609738, 'max': 36.09143899155716}`
- `abs_forward_delta_m`: `{'min': 12.638445243704446, 'max': 36.05451869836678}`
- `abs_lateral_delta_m`: `{'min': 1.6320692112815172, 'max': 16.504205595491126}`

## Rows

| slot | scenario | run | geometry | forward | lateral | dominant | d_forward | d_lateral | distance |
|---:|---|---:|---|---|---|---|---:|---:|---:|
| `1` | `scene-0411-hard-00` | `2` | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-23.506868694236438` | `3.6793055233027125` | `23.793069683037515` |
| `2` | `scene-0411-extreme-00` | `1` | `far_ahead_lateral_far` | `monitor_far_ahead` | `monitor_far_right` | `forward_dominant` | `18.22898787802343` | `-16.504205595491126` | `24.59033959495813` |
| `3` | `scene-0038-hard-00` | `1` | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-13.335525415682211` | `-5.622921712646466` | `14.472507961609738` |
| `4` | `scene-0038-extreme-00` | `1` | `far_behind_lateral_far` | `monitor_far_behind` | `monitor_far_right` | `forward_dominant` | `-12.638445243704446` | `-8.904216683620547` | `15.460122021736504` |
| `5` | `scene-0038-extreme-00` | `2` | `far_behind_lateral_far` | `monitor_far_behind` | `monitor_far_right` | `forward_dominant` | `-12.684481107615593` | `-8.979239007955975` | `15.541003639773562` |
| `6` | `scene-0383-extreme-00` | `2` | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-36.05451869836678` | `-1.6320692112815172` | `36.09143899155716` |
| `7` | `scene-0411-hard-00` | `1` | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-22.669632478607582` | `4.840797623268669` | `23.180715225043926` |
| `8` | `scene-0411-extreme-00` | `2` | `far_behind_lateral_near` | `monitor_far_behind` | `monitor_lateral_near` | `forward_dominant` | `-24.74298187779935` | `1.8560289568118495` | `24.812496764606966` |

## Boundary

descriptive geometry decomposition of eight committed support-core mismatch vectors only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
