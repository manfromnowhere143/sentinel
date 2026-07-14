# HANDOFF — dynamic state snapshot

Generated: Tue Jul 14 12:06:58 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
e8d4931 iter132: publish schema instance preflight
ffd113f iter132: add schema instance preflight tooling
5faa681 iter132: preregister schema instance preflight
143b863 handoff: record iter131 mission audit state
7d8e453 iter131: accept newer handoff freshness
fe3fc2e iter131: publish post iter130 mission audit
4e51b4b iter131: add post iter130 mission audit
49aad02 iter131: preregister post iter130 mission audit
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
- experiments/iter132_support_core_schema_instance_creation_preflight: RESULT PUBLISHED
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
 12:08:08 up 10 days,  1:49,  0 users,  load average: 0.00, 0.00, 0.00
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
- Newest completed experiment: experiments/iter132_support_core_schema_instance_creation_preflight/RESULT.md — read it before opening new work.
- Newest pending pre-registration: experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.

## Operator continuation appendix — current through Iter132

This appendix was added after the generated handoff so the next Codex/Claude session does not
restart from vibes or from the project narrative.

### Active goal to continue

Current active goal in the Codex goal tool:

> Continue the Sentinel mission actively from Iter101 without stopping at status: choose and execute
> the next scientifically justified iteration with preregistration, gates, publication, and handoff.

Do not mark this goal complete. The mission is ongoing. A new session should be told:

```text
Create/continue the active goal: Continue the Sentinel mission actively from Iter101 without
stopping at status. Choose and execute the next scientifically justified iteration with
pre-registration, gates, publication, and handoff. Do not declare the goal complete unless the
mission objective itself is genuinely complete; keep state changes committed, pushed, and handed
off.
```

### Iter132 final state

- Latest result: `experiments/iter132_support_core_schema_instance_creation_preflight/RESULT.md`.
- Latest verdict: `SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_COMPLETE`.
- Commits:
  - `5faa681` — pre-registered Iter132 alone.
  - `ffd113f` — added Iter132 generator/verifier and tests.
  - `e8d4931` — published Iter132 proof, result, note, README/NEXT_PHASE/CONTINUITY updates.
- Proof counts: `3` inert schema-instance templates, `1` validator contract, `30`
  reserved-path-to-template instance bindings, `10` reservations, `30` reserved relative paths.
- Negative checks: `0` true authorization flags, `0` missing schema/template/validator/binding
  content rows, `0` existing reserved or instance-bound paths, `0` duplicate paths, `0` bad
  references, `0` forbidden keys.
- Boundary: no `future_artifacts/` directory exists; no reserved path was created; no generated
  artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run, learning/update,
  repair, threshold, metric, deployment, safety, benchmark, production, commercial, acquisition,
  or frontier-equivalence claim was made.
- Gates run after publication:
  - `ruff check .` — passed.
  - `pytest -q` — `532 passed in 31.96s`.
  - `python3 scripts/validate_docs.py` — `389 markdown files clean; all RESULT experiments surfaced
    in README`.

### Direct answer to the incoming audit/critique

I broadly agree with the critique and it should govern the next fork:

- The core publishable science is still the frozen NeuroNCAP result arc, the independent
  verification discipline, the honest HUGSIM transfer nulls, and the mechanism forensics through
  the support-core/two-track analysis.
- Iterations 125-132 are valuable only as controlled evidence infrastructure for future generated
  support-core artifacts. They are not new empirical improvement, not a repair, not a deployment
  claim, and not a reason to say Tesla/Mobileye would be behind today.
- The project must not keep extending a self-grading preflight chain just because each preflight
  can pass its own bars. The next high-value move should put pressure back on empirical
  falsification or an externally legible claim boundary.
- Strongest next scientific fork: pre-register an adversarial empirical test that asks whether the
  NeuroNCAP gain depends on Sentinel's introspective risk semantics or can be reproduced by a
  placebo/sham intervention with matched timing, actuator budget, and opportunity. Keep this as a
  proper experiment with frozen controls, no hidden tuning, and full null publication.
- Conservative alternate fork if generation must continue first: a reserved-file/stub creation gate
  that writes only validator-checked placeholder JSON for the already reserved paths. It must be
  freshly pre-registered and must not run generation, HUGSIM, GPU, learning, repair, or claim
  upgrade. This is lower scientific value than the adversarial empirical fork.

### Recommended next move

Prefer Iter133 as an adversarial placebo/control design, not another inert preflight:

`experiments/iter133_neuronncap_placebo_semantics_control_design/`

Frozen question:

> Can we design a seed-paired, no-hidden-tuning NeuroNCAP control that matches Sentinel's actuation
> opportunity and intervention budget while removing the load-bearing introspective risk semantics,
> so the next empirical run can distinguish semantic monitoring value from generic braking or timing
> artifacts?

Minimum bars before any run:

- use only committed NeuroNCAP result/control surfaces until a fresh `HYPOTHESIS.md` is committed;
- freeze the placebo/sham rule, matching policy, opportunity definition, seed pairing, actuator
  budget, and null verdicts before execution;
- require independent verification and full null publication;
- no GPU launch until the design/preflight result says the launch manifest is ready and the operator
  explicitly approves the run;
- no Tesla/Mobileye/frontier/commercial/deployment claim.

If the new session decides this is too broad for one iteration, first do a bounded design/preflight
that outputs the frozen placebo-control protocol and exact launch-manifest requirements, then stop
only after committing/pushing the result and refreshing this handoff.
