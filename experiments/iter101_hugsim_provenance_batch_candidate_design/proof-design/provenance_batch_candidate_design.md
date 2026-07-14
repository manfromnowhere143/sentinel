# Iteration 101 - HUGSIM provenance batch candidate design

Verdict: `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE`

## Summary

- `selected_total_count`: `13`
- `selected_new_count`: `12`
- `carried_singleton_count`: `1`
- `all_strata_covered`: `True`
- `existing_instrumented_scenario_count`: `8`

## Selected Rows

| role | dataset | stratum | scenario | run | tier | timing | first fire | first collision |
|---|---|---|---|---:|---|---|---:|---:|
| `new_candidate` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `1` | `easy` | `no_fire` | `None` | `3.5` |
| `new_candidate` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `2` | `easy` | `no_fire` | `None` | `2.75` |
| `new_candidate` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0038-medium-01` | `1` | `medium` | `long_lead_fire` | `9.75` | `16.0` |
| `new_candidate` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0062-medium-00` | `2` | `medium` | `long_lead_fire` | `12.75` | `18.5` |
| `new_candidate` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `1` | `easy` | `post_collision_fire` | `11.5` | `1.5` |
| `new_candidate` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `2` | `easy` | `post_collision_fire` | `11.5` | `1.75` |
| `new_candidate` | `iter49_hard_extreme` | `no_fire` | `scene-0041-extreme-00` | `2` | `extreme` | `no_fire` | `None` | `3.25` |
| `new_candidate` | `iter49_hard_extreme` | `no_fire` | `scene-0062-hard-00` | `1` | `hard` | `no_fire` | `None` | `16.25` |
| `new_candidate` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `1` | `extreme` | `post_collision_fire` | `2.5` | `0.25` |
| `new_candidate` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `2` | `extreme` | `post_collision_fire` | `2.5` | `0.25` |
| `new_candidate` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `1` | `hard` | `long_lead_fire` | `7.0` | `8.5` |
| `new_candidate` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `2` | `hard` | `post_collision_fire` | `7.0` | `4.75` |
| `carried_existing_singleton` | `iter49_hard_extreme` | `both_distinct_objects` | `scene-0138-extreme-00` | `1` | `extreme` | `post_collision_fire` | `5.25` | `3.5` |

## Boundary

offline candidate-schedule design only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, retuning, GPU approval, or approval-to-run claim
