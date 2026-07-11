# HANDOFF — dynamic state snapshot

Generated: ש' יול 11 19:02:13 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
bd6e6c4 docs: record iter42 trace replay-support pass in README status/tracker/diagram and CONTINUITY arc + shift log
d1a83aa iter42: publish TRACE_REPLAY_SUPPORT_PASS — exact counts (400/6474/1205/156/230) and 0-mismatch offline replay identity
3ffde8f iter42: collect trace capture proof from sentinel-gpu (trace sha256 8c43726c, run + watch logs)
f19fb4b handoff: record threaded ljungbergh follow-up
a614535 docs: readme alignment pass — corroborated-reproduction framing, iter40 power-scale safety case, iters 39-42 arc, steering-line closure, early-row evidence links
1e4c3be research: record intervention-mechanism survey verdict (asymmetry replicated; LAE-style learned edit = only credible successor)
541cdbc handoff: record positioning and hugsim launch-packet shift work
eee4bf9 research: add HUGSIM second-benchmark transfer launch packet from recon
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
- experiments/iter42_exact_trace_replay_support: RESULT PUBLISHED
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
 19:03:21 up 7 days,  8:44,  0 users,  load average: 0.00, 0.00, 0.08
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-iter42-watch.log
/var/log/sentinel-iter42-trace.log
/dev/root       310G  295G   16G  96% /
Swap:          8.0Gi        67Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest completed experiment: experiments/iter42_exact_trace_replay_support/RESULT.md — read it before opening new work.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
