# HANDOFF — dynamic state snapshot

Generated: Wed Jul 15 22:24:53 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
542b432 paper: verify all 14 citations against source
4310960 paper: make the build byte-reproducible
cba0960 paper: untrack latex build intermediates
5d8811a paper: reproducible build, correct four citations
2e4eb7e docs: claim-level audit of the paper before the rewrite
480e745 docs: record the arxiv rejection and its mechanism
0334b80 handoff: refresh baton and log the iter131 idle-box amendment
5796929 iter131: stop requiring an idle box for the audit to pass
```
Working tree: DIRTY — resolve before handoff:
M CONTINUITY.md

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
- experiments/iter134_neuroncap_placebo_semantics_execution: PRE-REGISTERED, result pending
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
 22:26:03 up 11 days, 12:07,  0 users,  load average: 1.26, 1.18, 1.13
GPU_RUN_STATE=IN_FLIGHT_CONTAINERS
agitated_merkle	Up 5 minutes
model	Up 5 minutes
renderer	Up 5 minutes
/var/log/sentinel-vitals.log
/var/log/sentinel-i134.log
/var/log/sentinel-i134-smoke.log
/dev/root       310G  281G   30G  91% /
Swap:          8.0Gi       720Mi       7.3Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest completed experiment: experiments/iter133_neuroncap_placebo_semantics_control_design/RESULT.md — read it before opening new work.
- Newest pending pre-registration: experiments/iter134_neuroncap_placebo_semantics_execution/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.

## OPERATOR STOP — A RUN IS IN FLIGHT (read before touching the box)

**Iteration 134 is executing on `sentinel-gpu`.** Launched 2026-07-14 12:59:10 UTC. `1,200`
episodes, three arms, arm-major. Log `/var/log/sentinel-i134.log`. Done marker
**`I134_PLACEBO_DONE`**. ~115 s/episode.

**DO NOT relaunch while containers are up.** The live probe above reports `GPU_RUN_STATE=`
mechanically; `IN_FLIGHT_CONTAINERS` means a run owns the box. Confirm ownership from the newest
`/var/log/sentinel-*.log` (`sentinel-i134.log`). Episodes are deterministic per run index, so a
crash is RESUMABLE and completed pairs stay valid — do not panic-restart from zero.

### State as of 2026-07-15 22:25 UTC (~1010/1200, ETA ~2026-07-16 03:45 UTC)

- `off` arm: **DONE, 400/400** — and G2-verified exact against the committed power run (see the
  CONTINUITY in-flight-verification entry). Includes `side-0921` at **20/20**; the committed power
  run has `n=19`.
- `union` arm: **DONE, 400/400**.
- `placebo` arm: **RUNNING** (~210/400), verified firing on its frozen donor schedule,
  `schedule_missing 0`, `intervene_err 0`, realized/scheduled budget `0.843`.
- Health: `0` aborts across the whole run; peak memory `28762/32093` (freeze line is `31.6`);
  swap persisted in `/etc/fstab`; disk ~31 G free against ~6 G still needed (a 20 GB docker
  build-cache prune on 2026-07-14 bought the margin; images were NOT pruned and `vad:latest` is
  deliberately kept because the paper reports VAD results).

### On `I134_PLACEBO_DONE`

Follow `CONTINUITY.md` -> "### On I134_PLACEBO_DONE" **verbatim**. The order is load-bearing:
check aborts and that no containers are up -> collect artifacts and **commit proof FIRST** ->
re-verify G0 (patch + analyzer SHA256 still byte-identical to `launch_manifest.json`) -> run the
committed analyzer **ONCE**, no edits -> publish `RESULT.md` at **FULL WEIGHT** in whichever of the
four frozen classes it returns.

`PLACEBO_EXPLAINS_GAIN` takes the `2.12 -> 2.91` headline rather than denting it, and publishes
exactly as readily as `SEMANTIC_VALUE_CONFIRMED`. Do not soften either. Do not read per-episode
outcomes before the analyzer runs.

Commits: `647bab0` pre-reg ALONE, `2b9f560` tooling+manifest, `dc0bb23` disclosed smoke,
`5c30941` launch record + on-done block.

### PAPER — do not touch until 134 lands

arXiv **REJECTED** the submission (2026-07-14); appeal requires a conventional-journal DOI, so the
next submission is to a PEER-REVIEWED VENUE (TMLR / RA-L / IEEE T-ITS), not arXiv. Two CONTINUITY
entries bind the rewrite: the rejection mechanism (**`iter124`'s freshness gate validated
`MANUSCRIPT.md`, which was never submitted, while the shipped `paper.tex` omits HUGSIM entirely —
DO NOT TRUST THAT GATE**) and the claim-level audit (Limitations falsely says "one simulator";
abstract result (5) asserts a universal negative over decoders from two failed probes while the
causal-intervention arc returned only nulls).

Since then: `docs/paper/build.sh` makes source -> PDF -> tarball one **byte-reproducible** act and
fails closed if the tarball's `paper.tex` differs from source; all `14` citations verified against
the actual papers (NeuroNCAP is **ECCV 2024**, not CVPR as `CLAUDE.md` still says; DMAD is
**NeurIPS 2025**; AWTA is **ICRA 2025**; four entries had invented titles and no authors). Requires
BasicTeX (`brew install --cask basictex`).

Frozen critique anchors preserved for Iter133 reproducibility:

- Iterations 125-132 are valuable only as controlled evidence infrastructure.
- They are not new empirical improvement.
- The strongest next test is a placebo/sham intervention with matched timing, actuator budget, and
  opportunity.
