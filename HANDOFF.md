# HANDOFF — dynamic state snapshot

Generated: א' יול 12 05:22:19 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
dc25fa0 iter47: Stage A pass, map expansion pack staged with receipts
ab7bf22 iter47: tooling for map staging, completion launcher, analyzer, tests
11aaf0f handoff: codify terse commit-subject convention
ced26df iter47: pre-register map-expansion staging + OFF-baseline completion — Stage A stages the official nuScenes map expansion pack v1.3 into /datasets/nuscenes-full/maps/expansion/ with redacted provenance, SHA/size proofs, zero-unsafe-member extraction, and a four-json existence bar; Stage B re-runs only the 14 failed load_HD_map medium-01 episodes under the carried stochastic D0 verdict with the iteration-46 resume-skip launcher pattern, then re-evaluates C1/C2/C3 over all 52 episodes; falsifiers include pack unavailability, a new post-staging map-loading failure, the crash-loop guard, and pairing infeasibility over all 26 pairs; iteration 46's null stands as published — completion is re-earned, not retroactively repaired; a pass authorizes only the iteration-48 Stage-2 pre-registration
581d180 handoff: refresh — iteration 46 concluded as HUGSIM_OFF_BASELINE_NULL, box IDLE, no runs in flight; next step on the transfer lane is a fresh completion pre-registration staging the nuScenes map-expansion pack
f341fce iter46: record the completion-null verdict in the CONTINUITY arc and shift log — evidence collected and committed, analyzer run once, Stage-2 pre-registration not authorized, box IDLE
497cce1 iter46: publish HUGSIM_OFF_BASELINE_NULL — 38/52 episodes complete, D0 stochastic, the seven load_HD_map medium-01 scenarios failed both attempts on the unstaged nuScenes map-expansion pack (dual-failure falsifier fired, C1 failed); pairing spread median |dHD| 0.0245 over 19 pairs recorded as Stage-2 design evidence; Stage-2 pre-registration NOT authorized; README header/tracker/status/diagram/repo-map updated
d6b4030 iter46: collect OFF-baseline run evidence from sentinel-gpu — 52-episode stochastic schedule (26 scenarios x 2), 38 completed episodes with eval.json/output.txt/episode_meta.json, 14 dual-attempt failures (the seven load_HD_map medium-01 scenarios), D0 stochastic verdict, both launch logs, provenance receipts, heavy-artifact manifest, prior-launch defect archive, and the load_HD_map yaml diagnostic
```
Working tree: DIRTY — resolve before handoff:
M CONTINUITY.md

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
- experiments/iter46_hugsim_off_baseline: RESULT PUBLISHED
- experiments/iter47_map_staging_and_off_completion: PRE-REGISTERED, result pending
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
 05:23:27 up 7 days, 19:04,  0 users,  load average: 5.81, 2.57, 1.03
GPU_RUN_STATE=IN_FLIGHT_CONTAINERS
hugsim_uniad_client	Up 4 minutes
/var/log/sentinel-iter47-completion.log
/var/log/sentinel-vitals.log
/var/log/sentinel-iter46-off.log
/dev/root       310G  271G   40G  88% /
Swap:          8.0Gi        65Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter47_map_staging_and_off_completion/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
