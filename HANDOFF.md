# HANDOFF — dynamic state snapshot

Generation-fifteen control-integrity recovery in source validation, 2026-07-19.
Read CONTINUITY.md first.

## Repository state
```
F15     this exact seventeen-path source recovery (replacement commit assigned after validation;
        unpublished candidate 619083e is red and superseded)
B14     69bd2e2 handoff: accept iter135 generation-fourteen tooling freeze
a084198 mission: accept iter135 generation-fourteen tooling freeze
b260ca5 iter135: publish generation-fourteen tooling receipt
4a62cc4 iter135: refreeze generation-fourteen tooling recovery
4bd0a23 iter135: commit host preparation evidence                (H, attempt 11;
         currently retained on evidence/stage0-h11-b14; briefly pushed to master, then removed)
```
Generation fourteen published green (F14 `4a62cc4` → R14 `b260ca5` → T14 `a084198` → B14
`69bd2e2`). The box was then de-prepared from attempt ten and rebuilt from B14. Host-preparation
attempt eleven returned `I135_HOST_PREPARATION_OK`, `problem_count=0`; its exact manifest SHA-256
is `43fbd96f86bcf59bed6c911a21b43abf9c1a661abef20e7da0cfc8dba6939d15` and its receipt
SHA-256 is `1468761d6763fbd71542609ca884fdaacebe27e09029ad096d7da6f03ff3966d`.
The H commit was pushed to `master` before its checks completed. Exact run 774 failed, after which
`master` was restored to B14 and the commit was retained on
`evidence/stage0-h11-b14`. `scripts/mission_state.py` omitted generation fourteen from the exact
frozen-controller set, so the valid H descendant was misclassified by the generic
descendant-scope path. The brief red-master interval was a publication-discipline failure and is
not stage authority. A second
pre-fire sweep found that all four live GitHub authority readers treated commit-level check rows
as canonical `master` authority. That contract both mixed historical rerun attempts and allowed a
later same-SHA disposable-branch workflow to mask an older red `master` run.

Generation fifteen repairs those control-plane fossils. It admits generations fourteen and
fifteen to the exact frozen validators/controllers. Each live authority reader now selects the
latest exact `.github/workflows/ci.yml` push on `master` by workflow `run_number`, validates only
the selected run's exact `run_attempt` jobs, and replays the workflow row after the job observation
to reject concurrent reruns. Every GitHub request forces cache revalidation, and every numeric
workflow/job identity is required to be a positive exact JSON integer; booleans and numerically
equal floats are rejected. Commit-level check IDs and timestamps are evidence identities, not
branch or chronology authority. The repair does not change the hypothesis, schedules, estimands,
verdict rule, intervention, simulator, or analytic payload. Mission state is rolled back to
`PREREGISTERED_TOOLING_REQUIRED` while F15, R15, the state-only child, and B15 are independently
validated and published. Until B15 is green,
preserve the B14 install and its attempt-eleven evidence exactly; do not mutate the host.

The first unpublished F15 candidate, `619083e`, passed the local suite (`1,402` passed, one
expected skip) but failed disposable-branch Actions run 777 (`29680678241`). Python 3.11 was
green; Python 3.10 reported two exit-128 failures from synthetic Git fixture commands at 92% while
`1,401` tests passed. The fixture helper discarded Git stderr, so the exact operating-system cause
is not recoverable from that run. This repeats generation fourteen's different synthetic Git
exit-128 at the same 92% boundary. The candidate is not rerun or promoted. Its replacement retains
Git stdout/stderr on failure and removes each isolated fixture's `.git` metadata after its test,
bounding resource accumulation without deleting worktree evidence.

## Canonical mission state (`MISSION_STATE.json`)

- Current: iteration 134 / PLACEBO_HARM_OR_NULL / run IDLE / next
  iteration 135 / PREREGISTERED_TOOLING_REQUIRED
- Current result: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md
- Next program: semantics-free placebo dose-response causal closure
- Authorized now:
  - build and validate only the tooling and tests frozen by the active iteration-135 hypothesis
  - inventory storage and provenance before any safe cleanup or live smoke
  - publish a read-only external-benchmark commercial, license, compute, and integration preflight
- Forbidden now:
  - GPU launch before the iteration-135 hypothesis, analyzer, manifest, provenance, storage, and smoke gates are frozen
  - rerun iteration 134
  - adopt run-index resampling as the iteration-135 primary after observing iteration-134 results

Generation four changes no scientific or execution payload. It makes structural Git reads resolve
and attest only Git instead of unnecessarily requiring the current `pytest`, Ruff, shell, and
Python launchers to live under the macOS-oriented trusted roots. The recovery adds hostile hosted-
toolcache coverage and retains every generation-one through generation-three commit as disclosed
history. Host preparation, Docker, GPU, smoke, and analytic execution remain forbidden.

The generation-three refreeze adds Python 3.10 CI, a hash-bound one-shot host-preparation
controller, exact GitHub branch/check and committed-artifact authority, environment schema v3 with
physical-interpreter and Docker client/daemon identity, sanitized descriptor-pinned launchers,
source-bound reconstruction of host/smoke/final evidence, deterministic `SMOKE.md`, and a separate
activation receipt. Construction prefixes remain non-authoritative. It does not change the
hypothesis, schedules, estimands, thresholds, retry policy, or analytic payload semantics. No live
evidence was created.

The green H authority proof is exactly sixteen GitHub GETs and zero `/git/blobs/` GETs. Its
initial six-call proof binds branch, canonical workflow run, commit, exact-attempt jobs, workflow
replay, and one exact untruncated recursive tree. A five-call branch/workflow/jobs/workflow/branch
observation is required immediately before the first mutation, and the same five-call observation
is repeated after packet installation before a green receipt may be emitted. Stable local bytes
are bound to the tree with Git's native blob identity
`sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload)` plus exact path, blob type,
integer size, and `100644`/`100755` mode; receipts retain SHA-256, bytes, Git OID, and mode. SHA-1
is trusted here only as Git object identity, never as the sole content digest. The green E
authority proof uses thirteen GETs: one topology observation, the initial workflow/tree proof,
two committed-payload reads, and the terminal five-call authority observation. There are no
retries. Both readers remain below GitHub's documented public unauthenticated primary budget while
failing closed if shared-IP headroom is already gone. Remote authority is established at the last
successful observation; it is not represented as a perpetual lease.
The live adversarial audit exhausted the shared unauthenticated window on 2026-07-19. Do not
invoke any real one-shot H/E/S authority gate until the rate window has reset and sufficient
headroom has been checked out of band.
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
GPU_RUN_STATE=IDLE_LAST_PROBED_2026-07-19
HOST_INSTALL=B14_ATTEMPT_11_GREEN_PRESERVE_UNTIL_B15
CONTAINERS=NONE
SMOKE_OR_ANALYTIC_LOCKS=NONE
ANALYTIC_ROOT=EXISTS_EMPTY
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Canonical completed experiment: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md — read it before opening new work.
- Active pending pre-registration: experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md — read it with MISSION_STATE.json; neither file overrides the other.
- Deprecated pending pre-registration: experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md — historical only; it does not govern the next action.
- Canonical next action: validate and publish F15, generate and publish R15 from the exact clean
  source commit, then publish its state-only child and B15 baton. Only after B15 and its required
  checks are green: archive the B14 attempt-eleven install and receipts, invert the compose patch
  only from exact SHA `a5ed766…` to preimage `9f8804b5…`/3380, remove the analytic root only if it
  remains the exact empty physical directory, rebuild from B15, fire host-preparation attempt
  twelve, commit H, re-fire and commit E, commit P, then fire S from
  `/opt/sentinel-stack/iter135` with no wrapping shell (`SHLVL=1`) and both
  `SENTINEL_SMOKE_INPUT_MANIFEST_SHA256` and `SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT` set.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
