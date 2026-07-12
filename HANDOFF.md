# HANDOFF — dynamic state snapshot

Generated: א' יול 12 00:25:30 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
2af43dd iter46: launcher-only amendment after the consecutive-failure abort — fix zip-nesting extraction (7 zips carry a top-level nuscenes/ prefix) and add 3DRealCar postprocess/shadow.pth compatibility symlinks (release layout mismatch, upstream strips the same suffix); resume-skip completed episodes, carry the recorded stochastic D0 verdict, archive prior-launch failure evidence. No frozen bar, scenario yaml, SHA receipt, schedule, or claim boundary changed; abort cause documented in the HYPOTHESIS amendment note and shift log.
e4de492 handoff: refresh — iter46 monitor-OFF baseline run IN FLIGHT (I46_OFF markers, done marker I46_OFF_ALL_DONE); never relaunch while a container is up
fb87da5 iter46: record launch in shift log — OFF baseline IN FLIGHT on sentinel-gpu (log /var/log/sentinel-iter46-off.log, done marker I46_OFF_ALL_DONE) with exact on-done collect/analyze/publish instructions
a03ea18 iter46: tooling — detached run script (provenance gate, D0 probe, branch loop, retry/abort guards, I46_OFF_ALL_DONE marker), on-box D0 comparator, offline completion analyzer, 13 unit tests
077e8d9 iter46: pre-register HUGSIM Stage-1 monitor-OFF baseline — frozen 52-scenario easy+medium nuScenes subset with per-yaml SHAs, D0 determinism probe deciding run multiplicity, provenance gate incl. the carried iter45 CPU-fallback shim (byte copy pinned), completion bars, budget arithmetic, falsifiers
75eaabc handoff: refresh after iter45 HUGSIM infrastructure gate pass; box idle, root 43 GiB free, next step is the Stage-1/2 transfer pre-registration
fd303b0 iter45: publish HUGSIM_INFRA_GATE_PASS — assets/envs/renderer/closed-loop smoke all pass on the frozen checkpoint; record verdict in README header/tracker/status/repo-map and CONTINUITY arc + shift log
baf54ad iter45: env build complete (torch cu124 + gsplat 1.2.0, apex non-blocking), G3 scenario renders, first closed-loop round trips through the pipes; cusolver init failure at step 2 under retry
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
- experiments/iter46_hugsim_off_baseline: PRE-REGISTERED, result pending
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
 00:26:36 up 7 days, 14:07,  0 users,  load average: 2.47, 0.75, 0.41
GPU_RUN_STATE=IN_FLIGHT_CONTAINERS
hugsim_uniad_client	Up About a minute
/var/log/sentinel-iter46-off.log
/var/log/sentinel-vitals.log
/var/log/sentinel-hugsim-smoke.log
/dev/root       310G  270G   41G  88% /
Swap:          8.0Gi        65Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter46_hugsim_off_baseline/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
