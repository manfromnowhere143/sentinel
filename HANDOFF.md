# HANDOFF — dynamic state snapshot

Generated: Sat Jul 11 08:58:57 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
3d49bac handoff: refresh iter42 second-boundary progress
0e61696 handoff: refresh iter42 pair-boundary progress
d51c036 handoff: refresh after iter42 launch
5523303 research: record iter42 gpu preflight
8601ef0 research: add iter42 exact trace tooling
acb7397 research: preregister iter42 exact trace replay support
a50f165 handoff: refresh after iter41 audit
9059738 research: publish iter41 degradation gate null
```
Working tree: CLEAN

## Experiments (status inferred from files)

- experiments/full14_benchmark: RESULT PUBLISHED
- experiments/full14_power: RESULT PUBLISHED
- experiments/iter10_brakevade: RESULT PUBLISHED
- experiments/iter11_early_evade: RESULT PUBLISHED
- experiments/iter12_plan_selection: RESULT PUBLISHED
- experiments/iter13_rss_baseline: RESULT PUBLISHED
- experiments/iter15_latch_release: RESULT PUBLISHED
- experiments/iter16_soft_stop: RESULT PUBLISHED
- experiments/iter17_threat_routing: RESULT PUBLISHED
- experiments/iter18_tracker: RESULT PUBLISHED
- experiments/iter19_diversity_head: RESULT PUBLISHED
- experiments/iter1_reproduce: artifacts only
- experiments/iter1b_partial_baseline: artifacts only
- experiments/iter20_vad_tracker_portability: RESULT PUBLISHED
- experiments/iter21_bev_diversity_head: RESULT PUBLISHED
- experiments/iter22_causal_planner_interpretability: RESULT PUBLISHED
- experiments/iter23_s0_hardened_causal_localization: RESULT PUBLISHED
- experiments/iter24_risk_support_atlas: RESULT PUBLISHED
- experiments/iter25_staged_data_inventory: RESULT PUBLISHED
- experiments/iter26_data_staging_remedy: RESULT PUBLISHED
- experiments/iter27_storage_provisioning: RESULT PUBLISHED
- experiments/iter28_nuscenes_trainval_staging: RESULT PUBLISHED
- experiments/iter29_trainval_risk_support_atlas: RESULT PUBLISHED
- experiments/iter2_monitor: RESULT PUBLISHED
- experiments/iter30_full_trainval_lowdiv_localization: RESULT PUBLISHED
- experiments/iter31_full_trainval_bridge_intervention: RESULT PUBLISHED
- experiments/iter32_prefix_replay_baseline_recovery: RESULT PUBLISHED
- experiments/iter33_prefix_preserving_bridge_intervention: RESULT PUBLISHED
- experiments/iter34_direction_specificity_audit: RESULT PUBLISHED
- experiments/iter35_response_heterogeneity_audit: RESULT PUBLISHED
- experiments/iter36_bridge_site_decomposition: RESULT PUBLISHED
- experiments/iter37_track_query_site_intervention: RESULT PUBLISHED
- experiments/iter38_track_query_opposite_direction: PRE-REGISTERED, result pending
- experiments/iter39_external_validity_claim_audit: RESULT PUBLISHED
- experiments/iter3_progress: RESULT PUBLISHED
- experiments/iter40_timing_cost_audit: RESULT PUBLISHED
- experiments/iter41_sensor_input_degradation_gate: RESULT PUBLISHED
- experiments/iter42_exact_trace_replay_support: PRE-REGISTERED, result pending
- experiments/iter4_gated: RESULT PUBLISHED
- experiments/iter5_tracked: RESULT PUBLISHED
- experiments/iter6_cpa: RESULT PUBLISHED
- experiments/iter7_margin: RESULT PUBLISHED
- experiments/iter8_union: RESULT PUBLISHED
- experiments/iter9_evade: RESULT PUBLISHED
- experiments/union_validation: RESULT PUBLISHED
- experiments/vad_generalization: RESULT PUBLISHED
- experiments/verification: artifacts only

## GPU box quick-state (live probe)
```
sentinel-gpu
 09:00:04 up 6 days, 22:41,  0 users,  load average: 1.24, 1.09, 1.12
GPU_RUN_STATE=IN_FLIGHT_CONTAINERS
quizzical_wilbur	Up 33 minutes
model	Up 33 minutes
renderer	Up 33 minutes
/var/log/sentinel-iter42-trace.log
/var/log/sentinel-vitals.log
/var/log/sentinel-iter42-preflight.log
/dev/root       310G  287G   24G  93% /
Swap:          8.0Gi       4.0Gi       4.0Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.
Latest Iter42 observation before this handoff: at 2026-07-11T08:59:41Z the trace had reached
`stationary 0108` with 1,796 JSONL rows, 94 reset blocks, 1,702 frame rows, zero parse errors,
and no error markers.
Read-only Iter42 watcher: `/tmp/sentinel_iter42_watch_loop.sh` is running on `sentinel-gpu`
and appends 10-minute summaries to `/var/log/sentinel-iter42-watch.log`. It does not relaunch,
kill, patch, or analyze the run; it exits after `I42_TRACE_ALL_DONE` or if Docker stops before
that marker.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter42_exact_trace_replay_support/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
