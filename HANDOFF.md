# HANDOFF — dynamic state snapshot

Generated: ש' יול 11 23:34:24 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
fd303b0 iter45: publish HUGSIM_INFRA_GATE_PASS — assets/envs/renderer/closed-loop smoke all pass on the frozen checkpoint; record verdict in README header/tracker/status/repo-map and CONTINUITY arc + shift log
baf54ad iter45: env build complete (torch cu124 + gsplat 1.2.0, apex non-blocking), G3 scenario renders, first closed-loop round trips through the pipes; cusolver init failure at step 2 under retry
ea520c3 iter45: fix2 resolved the CUDA-major mismatch (torch cu124); new simple-knn FLT_MAX blocker patched with float.h include, fix3 rebuild in flight
9b2c497 iter45: G2 client half passes — unmodified UniAD_SIM client loads the NeuroNCAP checkpoint in uniad:latest (131,809,024 params); motion-anchor data file staged; smoke script ready pending env build
2cdabd8 iter45: record base-config path edits, docker client wrapper for the unmodified UniAD_SIM client, and host zsh install
1ae096c iter45: commit G1 asset-staging evidence — 306-file SHA256/size manifest of the XDimLab/HUGSIM release on /datasets/nuscenes-full plus staging receipts
123a9e7 iter45: log CUDA falsifier probe (nvcc 12.9 vs torch cu118), failed 11.8-pin fallback, in-flight cu124 fallback, smoke-scene staging (scene-0013-easy-00 by frozen rule), docker client route, exact resume steps
a9de6b1 iter45: record setup progress — repos cloned (62c690d3/5fb279e3), asset staging and pixi env build launched detached, checkpoint SHA receipts, exact resume point
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
- experiments/iter43_object_stream_perturbation_gate: RESULT PUBLISHED
- experiments/iter44_velocity_smoothing_gate: RESULT PUBLISHED
- experiments/iter45_hugsim_infra_gate: RESULT PUBLISHED
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
 23:35:31 up 7 days, 13:16,  0 users,  load average: 0.00, 0.36, 1.30
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-hugsim-smoke.log
/var/log/sentinel-hugsim-importcheck.log
/dev/root       310G  269G   42G  87% /
Swap:          8.0Gi        65Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest completed experiment: experiments/iter45_hugsim_infra_gate/RESULT.md — read it before opening new work.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
