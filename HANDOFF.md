# HANDOFF — dynamic state snapshot

Generation-three atomic preflight-baton snapshot, 2026-07-16. Read CONTINUITY.md first.

## Repository state
```
d9e2610 mission: accept iter135 generation-three tooling freeze
755489f iter135: publish generation-three tooling receipt
1820fcf iter135: refreeze generation-three control authority
ee0c0c9 handoff: accept iter135 generation-two tooling freeze
71a137f mission: accept iter135 generation-two tooling freeze
b0eca12 iter135: publish generation-two tooling receipt
90773c3 iter135: refreeze generation-two tooling recovery
c868040 handoff: record iter135 tooling freeze
```
Accepted generation-three source `1820fcfd65483fa9c7429dd54fe65dbf91dc6b35` and receipt
`755489f36ae2b8cefad183341edefd7c30c047e7` are green on `origin/master`. State-only T3
`d9e2610` and this immediately following B3 baton are one local publication unit. T3 is
structurally incomplete by itself and must never be pushed alone. Host preparation remains blocked
until the pushed B3 tip has exactly the two required successful GitHub Actions checks.

## Canonical mission state (`MISSION_STATE.json`)

- Current: iteration 134 / PLACEBO_HARM_OR_NULL / run IDLE / next
  iteration 135 / TOOLING_FROZEN_PREFLIGHT_REQUIRED
- Current result: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md
- Next program: semantics-free placebo dose-response causal closure
- Authorized now:
  - prepare the exact hash-bound sentinel-gpu host contract and atomically commit
    `host_packet_manifest.json` and `host_preparation_receipt.json`
  - capture and commit the read-only iteration-135 environment receipt on sentinel-gpu
  - generate and commit only the hash-addressed incomplete pre-smoke manifest; no analytic episodes
  - run exactly the hash-bound four-run nonanalytic G5 smoke after the incomplete pre-smoke manifest is committed
  - validate, collect, and commit the exact nonanalytic smoke raw evidence, recomputed receipt, and mechanically generated `SMOKE.md`
- Forbidden now:
  - run any iteration-135 analytic episode before smoke evidence and the final launch manifest are committed green
  - remove or bypass the permanent analytic launch lock
  - rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after evidence
  - place any iteration-135 analytic output on the remote root filesystem

The generation-three refreeze adds Python 3.10 CI, a hash-bound one-shot host-preparation
controller, exact GitHub branch/check and committed-artifact authority, environment schema v3 with
physical-interpreter and Docker client/daemon identity, sanitized descriptor-pinned launchers,
source-bound reconstruction of host/smoke/final evidence, deterministic `SMOKE.md`, and a separate
activation receipt. Construction prefixes remain non-authoritative. It does not change the
hypothesis, schedules, estimands, thresholds, retry policy, or analytic payload semantics. No live
evidence was created.

The H authority proof is exactly seven GitHub GETs and zero `/git/blobs/` GETs: branch, checks,
commit, one exact untruncated recursive tree, terminal branch/check replay before mutation, and a
final branch replay. Stable local bytes are bound to that tree with Git's native blob identity
`sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload)` plus exact path, blob type,
integer size, and `100644`/`100755` mode; receipts retain SHA-256, bytes, Git OID, and mode. SHA-1
is trusted here only as Git object identity, never as the sole content digest. The E authority
proof uses eight GETs because two JSON payloads are additionally replayed through the Contents API.
There are no retries. This 7/8-call budget is deliberately below GitHub's documented public,
unauthenticated primary budget, while still failing closed if shared-IP headroom is already gone.
Official references: [Git hash-object](https://git-scm.com/docs/git-hash-object.html),
[GitHub recursive trees](https://docs.github.com/en/rest/git/trees), and
[GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

After those commits exist, a trusted clean SSH/systemd parent must first
`cd /opt/sentinel-stack/iter135`, then invoke each launcher through `/usr/bin/env -i` with only the
required authority variables and `PATH=/usr/bin:/bin:/usr/sbin:/sbin`. The launchers require that
physical working directory, `SHLVL=1`, and the exact startup-variable set. This clean-parent
boundary is mandatory: the launchers reject loader-variable contamination, but source code cannot
undo a native loader hook that ran before Bash read its first byte. Smoke requires both
`SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT=P` and
`SENTINEL_SMOKE_INPUT_MANIFEST_SHA256=<the committed P blob SHA-256>`. Analytic launch requires
`SENTINEL_LAUNCH_MANIFEST_SHA256=<F blob SHA-256>`,
`SENTINEL_LAUNCH_ACTIVATION_COMMIT=B`, and
`SENTINEL_LAUNCH_ACTIVATION_SHA256=<the committed B activation-receipt blob SHA-256>`. A hash or
commit supplied alone is not authority.

The authoritative smoke invocation is:

```bash
cd /opt/sentinel-stack/iter135
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin \
  SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT='<P-commit-sha>' \
  SENTINEL_SMOKE_INPUT_MANIFEST_SHA256='<committed-P-blob-sha256>' \
  /bin/bash -p /opt/sentinel-stack/iter135/run_smoke135.sh
```

The authoritative analytic invocation is:

```bash
cd /opt/sentinel-stack/iter135
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin \
  SENTINEL_LAUNCH_MANIFEST_SHA256='<committed-F-blob-sha256>' \
  SENTINEL_LAUNCH_ACTIVATION_COMMIT='<B-commit-sha>' \
  SENTINEL_LAUNCH_ACTIVATION_SHA256='<committed-B-activation-receipt-blob-sha256>' \
  /bin/bash -p /opt/sentinel-stack/iter135/run_dose135.sh
```

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
- experiments/iter133_neuroncap_placebo_semantics_control_design: RESULT PUBLISHED
- experiments/iter134_neuroncap_placebo_semantics_execution: RESULT PUBLISHED
- experiments/iter135_neuroncap_blind_braking_dose_response: PRE-REGISTERED, result pending
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
GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Canonical completed experiment: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md — read it before opening new work.
- Active pending pre-registration: experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md — read it with MISSION_STATE.json; neither file overrides the other.
- Deprecated pending pre-registration: experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md — historical only; it does not govern the next action.
- Canonical next action: push and remotely validate only this B3 baton tip. Never push the
  intermediate T3 state-only tip. After B3 is exactly green, execute the committed H -> E -> P -> S
  preflight and nonanalytic-smoke sequence without skipping, retrying, or reordering a stage.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
