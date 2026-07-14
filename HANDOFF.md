# HANDOFF — dynamic state snapshot

Generated: Tue Jul 14 11:52:44 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
7d8e453 iter131: accept newer handoff freshness
fe3fc2e iter131: publish post iter130 mission audit
4e51b4b iter131: add post iter130 mission audit
49aad02 iter131: preregister post iter130 mission audit
bbc9344 handoff: record iter130 artifact schema state
16aa099 iter130: publish artifact schema preflight
499935f iter130: add artifact schema preflight tooling
07dc9fc iter130: preregister artifact schema preflight
```
Working tree: CLEAN

## Experiments (status inferred from files)

- experiments/full14_benchmark: RESULT PUBLISHED
- experiments/full14_power: RESULT PUBLISHED
- experiments/iter100_hugsim_structural_expansion_support_audit: RESULT PUBLISHED
- experiments/iter101_hugsim_provenance_batch_candidate_design: RESULT PUBLISHED
- experiments/iter102_hugsim_provenance_batch_launch_manifest: RESULT PUBLISHED
- experiments/iter103_hugsim_provenance_batch_execution: RESULT PUBLISHED
- experiments/iter104_hugsim_provenance_batch_actor_match_audit: RESULT PUBLISHED
- experiments/iter105_hugsim_timing_aware_provenance_batch_design: RESULT PUBLISHED
- experiments/iter106_hugsim_timing_aware_launch_manifest: RESULT PUBLISHED
- experiments/iter107_hugsim_timing_aware_batch_execution: RESULT PUBLISHED
- experiments/iter108_hugsim_timing_aware_batch_actor_match_audit: RESULT PUBLISHED
- experiments/iter109_hugsim_timing_aware_support_yield_decomposition: RESULT PUBLISHED
- experiments/iter10_brakevade: RESULT PUBLISHED
- experiments/iter110_hugsim_support_preserving_candidate_design: RESULT PUBLISHED
- experiments/iter111_hugsim_support_core_launch_manifest: RESULT PUBLISHED
- experiments/iter112_hugsim_support_core_batch_execution: RESULT PUBLISHED
- experiments/iter113_hugsim_support_core_actor_match_audit: RESULT PUBLISHED
- experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition: RESULT PUBLISHED
- experiments/iter115_hugsim_support_core_monitor_set_ordering: RESULT PUBLISHED
- experiments/iter116_hugsim_support_core_collision_actor_timeline: RESULT PUBLISHED
- experiments/iter117_hugsim_support_core_event_window_decomposition: RESULT PUBLISHED
- experiments/iter118_hugsim_support_core_object_lifecycle: RESULT PUBLISHED
- experiments/iter119_hugsim_support_core_loss_replacement_audit: RESULT PUBLISHED
- experiments/iter11_early_evade: RESULT PUBLISHED
- experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle: RESULT PUBLISHED
- experiments/iter121_hugsim_support_core_two_track_synthesis: RESULT PUBLISHED
- experiments/iter122_support_core_taxonomy_documentation: RESULT PUBLISHED
- experiments/iter123_mission_evidence_alignment_audit: RESULT PUBLISHED
- experiments/iter124_manuscript_report_freshness: RESULT PUBLISHED
- experiments/iter125_support_core_blind_spot_scenario_design: RESULT PUBLISHED
- experiments/iter126_support_core_candidate_manifest_preflight: RESULT PUBLISHED
- experiments/iter127_post_iter126_mission_alignment_audit: RESULT PUBLISHED
- experiments/iter128_support_core_source_pool_mutation_preflight: RESULT PUBLISHED
- experiments/iter129_support_core_artifact_naming_preflight: RESULT PUBLISHED
- experiments/iter12_plan_selection: RESULT PUBLISHED
- experiments/iter130_support_core_artifact_schema_preflight: RESULT PUBLISHED
- experiments/iter131_post_iter130_mission_alignment_audit: RESULT PUBLISHED
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
- experiments/iter47_map_staging_and_off_completion: RESULT PUBLISHED
- experiments/iter48_hugsim_transfer_gate: RESULT PUBLISHED
- experiments/iter49_hugsim_hard_tier_gate: RESULT PUBLISHED
- experiments/iter4_gated: RESULT PUBLISHED
- experiments/iter50_collision_opportunity_audit: RESULT PUBLISHED
- experiments/iter51_hugsim_failure_taxonomy: RESULT PUBLISHED
- experiments/iter52_hugsim_on_collision_timing_audit: RESULT PUBLISHED
- experiments/iter53_hugsim_first_fire_channel_audit: RESULT PUBLISHED
- experiments/iter54_hugsim_provenance_support_audit: RESULT PUBLISHED
- experiments/iter55_hugsim_collision_instrumentation_source_audit: RESULT PUBLISHED
- experiments/iter56_hugsim_provenance_instrumentation_patch: RESULT PUBLISHED
- experiments/iter57_hugsim_patch_guard_refinement: RESULT PUBLISHED
- experiments/iter58_hugsim_provenance_instrumented_canary: RESULT PUBLISHED
- experiments/iter59_hugsim_actor_match_audit: RESULT PUBLISHED
- experiments/iter5_tracked: RESULT PUBLISHED
- experiments/iter60_actor_bridge_sensitivity: RESULT PUBLISHED
- experiments/iter61_monitor_object_surface_audit: RESULT PUBLISHED
- experiments/iter62_nontrigger_ranking_audit: RESULT PUBLISHED
- experiments/iter63_temporal_emergence_audit: RESULT PUBLISHED
- experiments/iter64_unsupported_temporal_surface_audit: RESULT PUBLISHED
- experiments/iter65_temporal_alignment_audit: RESULT PUBLISHED
- experiments/iter66_matched_object_timeline_audit: RESULT PUBLISHED
- experiments/iter67_trigger_target_bridge_audit: RESULT PUBLISHED
- experiments/iter68_fire_time_bridge_decomposition: RESULT PUBLISHED
- experiments/iter69_hugsim_mechanism_taxonomy: RESULT PUBLISHED
- experiments/iter6_cpa: RESULT PUBLISHED
- experiments/iter70_hugsim_structural_timing_audit: RESULT PUBLISHED
- experiments/iter71_hugsim_surface_silent_margin_audit: RESULT PUBLISHED
- experiments/iter72_hugsim_late_fire_prefire_margin_audit: RESULT PUBLISHED
- experiments/iter73_hugsim_margin_transition_audit: RESULT PUBLISHED
- experiments/iter74_hugsim_late_fire_delay_barrier: RESULT PUBLISHED
- experiments/iter75_hugsim_cross_channel_object_handoff: RESULT PUBLISHED
- experiments/iter76_hugsim_switch_foreground_bridge: RESULT PUBLISHED
- experiments/iter77_hugsim_event_object_set_bridge: RESULT PUBLISHED
- experiments/iter78_hugsim_support_object_ranking: RESULT PUBLISHED
- experiments/iter79_hugsim_selected_surface_decomposition: RESULT PUBLISHED
- experiments/iter7_margin: RESULT PUBLISHED
- experiments/iter80_hugsim_selected_all_provenance_bridge: RESULT PUBLISHED
- experiments/iter81_hugsim_support_object_temporal_surface: RESULT PUBLISHED
- experiments/iter82_hugsim_support_surface_bridge_cooccurrence: RESULT PUBLISHED
- experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition: RESULT PUBLISHED
- experiments/iter84_hugsim_selected_support_arbitration: RESULT PUBLISHED
- experiments/iter85_hugsim_path_horizon_bridge_timing: RESULT PUBLISHED
- experiments/iter86_hugsim_bridge_time_surface_replay: RESULT PUBLISHED
- experiments/iter87_hugsim_interval_bridge_time_surface_replay: RESULT PUBLISHED
- experiments/iter88_hugsim_bridge_surface_margin_residual: RESULT PUBLISHED
- experiments/iter89_hugsim_joint_bridge_surface_candidate_audit: RESULT PUBLISHED
- experiments/iter8_union: RESULT PUBLISHED
- experiments/iter90_hugsim_active_surface_provenance_gap: RESULT PUBLISHED
- experiments/iter91_hugsim_active_gap_geometry_decomposition: RESULT PUBLISHED
- experiments/iter92_hugsim_path_proximity_arbitration: RESULT PUBLISHED
- experiments/iter93_hugsim_surface_winner_alignment: RESULT PUBLISHED
- experiments/iter94_hugsim_active_row_surface_margin_arbitration: RESULT PUBLISHED
- experiments/iter95_hugsim_nonactive_surface_branch_arbitration: RESULT PUBLISHED
- experiments/iter96_hugsim_branch_outcome_bridge: RESULT PUBLISHED
- experiments/iter97_hugsim_surface_silent_outcome_margin_bridge: RESULT PUBLISHED
- experiments/iter98_hugsim_background_only_outcome_bridge: RESULT PUBLISHED
- experiments/iter99_hugsim_structural_bridge_coverage_audit: RESULT PUBLISHED
- experiments/iter9_evade: RESULT PUBLISHED
- experiments/union_validation: RESULT PUBLISHED
- experiments/vad_generalization: RESULT PUBLISHED
- experiments/verification: artifacts only

## GPU box quick-state (live probe)
```
sentinel-gpu
 11:53:53 up 10 days,  1:34,  0 users,  load average: 0.00, 0.00, 0.00
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-iter112-support-core-batch.log
/var/log/sentinel-iter107-timing-aware-batch.log
/dev/root       310G  269G   42G  87% /
Swap:          8.0Gi        75Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest completed experiment: experiments/iter131_post_iter130_mission_alignment_audit/RESULT.md — read it before opening new work.
- Newest pending pre-registration: experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.

## Operator continuation appendix

This section was added after the dynamic snapshot so the next session can recover the exact
mission intent without relying on chat history.

### Current state after this shift

- Latest completed experiment: `experiments/iter131_post_iter130_mission_alignment_audit/RESULT.md`.
- Latest verdict: `POST_ITER130_MISSION_ALIGNMENT_AUDIT_COMPLETE`.
- Iteration 131 verifier result: `14/14` checks passed, `0` problems, `5` source anchors.
- Iteration 130 proof remains the latest artifact-preflight substrate:
  `3` schema specs, `30` schema bindings, `10` reservations, `30` reserved paths, `0` true
  authorization flags, `0` existing bound paths, `0` duplicate reserved paths, `0` bad schema
  references, and `0` forbidden keys.
- GPU state at handoff generation: `GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS`.
- Full gates after the final verifier compatibility fix: `ruff check .` passed, `pytest -q`
  passed with `526 passed`, and `python3 scripts/validate_docs.py` passed with all RESULT
  experiments surfaced in README.

### Mission claim hierarchy to preserve

- Proven empirical result: NeuroNCAP released-union monitor improved the frozen UniAD benchmark
  score under the registered full-power run, while deployment metric stayed a null.
- Published nulls: HUGSIM transfer remained null; perturbation and velocity-smoothing work did
  not prove repair.
- Mechanism evidence: HUGSIM support-core iterations 112-121 explain selected-fire-object versus
  support-object separation on committed support-core rows.
- Design/preflight artifacts: iterations 125-130 prepare future support-core generation with
  archetypes, candidate manifest, source pools, mutation operators, reserved paths, and schema
  metadata. They do not create scenarios or prove outcome improvement.

### Hard boundaries

Do not claim generated scenarios, HUGSIM improvement, repair, safety, deployment, production,
commercial value, real-world behavior, first-responder readiness, driver-supervision compliance,
mission feasibility, or parity/superiority to Tesla, Mobileye, SpaceX, Waymo, NVIDIA, or any
frontier autonomy stack. Do not create reserved future artifact paths, run HUGSIM, use GPU, select
execution slots, run learning/update, retune thresholds, change planner/action code, or change
metrics without a fresh committed `HYPOTHESIS.md`.

### Best next move

The highest-accuracy next iteration is likely:

`iter132_support_core_schema_instance_creation_preflight`

Purpose: freeze the exact schema-instance object shape and validator for the three artifact types
before writing any reserved path. It should still create no reserved future files. Suggested bars:

- read Iter130 report/result/schema note;
- verify the Iter130 counts and no-authorization flags;
- define an inert schema-instance template per artifact type;
- define a validator contract for identity, metadata, boundary, payload-section names, forbidden
  fields, and path nonexistence;
- bind templates to all `30` reserved paths without writing those paths;
- output report/note/RESULT and keep the claim boundary unchanged.

Alternative bounded lanes if the operator chooses not to start Iter132:

- one-page external claim ledger;
- explicit mission/rulebook boundary note;
- higher-fidelity perturbation successor;
- separated candidate-generation/execution/analysis/monitor-update plan.

### Autonomous continuation prompt

Use this prompt for the next Codex session if you want the same autonomous behavior inside the
active turn:

```text
Work autonomously in /Users/danielwahnich/workspace/sentinel toward the Sentinel mission goals.
First read CONTINUITY.md, HANDOFF.md, docs/NEXT_PHASE.md, and the newest RESULT.md named in
HANDOFF. Continue from the newest completed experiment, choose the next bounded scientifically
justified step, preregister before data, implement, verify, publish, commit, push, and refresh
HANDOFF. Keep the standards high: frozen bars, explicit falsifiers, nulls published at full
weight, no unearned claims, no GPU/run/creation unless a fresh HYPOTHESIS.md authorizes it. Do not
stop after planning if the next step is discoverable locally; keep going until the next verified,
committed, pushed handoff is ready, or until a real blocker requires user input.
```

There is no durable background daemon that keeps working after the session or tool turn ends. The
autonomous behavior comes from giving the next active session a clear objective plus permission to
continue through implementation, verification, commit, push, and handoff. If the UI exposes a
goal/objective field, use the same text above as the objective.
