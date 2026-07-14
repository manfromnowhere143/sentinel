# Iteration 100 - HUGSIM structural expansion support audit

## Research question

Can the completed five-row structural bridge map from iteration 99 be expanded to a larger
committed HUGSIM row set using existing evidence, or do the committed transfer artifacts still
lack collision-actor support and therefore require a fresh instrumented run before any larger-row
structural bridge claim?

## Scope

This is an offline report-level support-boundary audit. It may read only these committed reports:

- `experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json`
- `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`
- `experiments/iter99_hugsim_structural_bridge_coverage_audit/proof-coverage/structural_bridge_coverage_report.json`

It must not read raw decision logs, raw `eval.json` files, raw episode directories, launch Docker,
touch the GPU box, run HUGSIM, modify thresholds, tune parameters, or infer counterfactual vehicle
outcomes.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 54 verdict is `PROVENANCE_SUPPORT_NULL`.
2. Iteration 59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`.
3. Iteration 99 verdict is `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE`.
4. Iteration 54 combined summary has:
   - `pairs == 104`;
   - `on_collision_pairs == 92`;
   - `collision_actor_support_counts.collision_actor_supported == 0`;
   - `collision_actor_support_counts.collision_actor_not_logged == 104`;
   - `collision_actor_support_on_collision_counts.collision_actor_supported == 0`;
   - `collision_actor_support_on_collision_counts.collision_actor_not_logged == 92`;
   - `monitor_provenance_counts.unique_ttc_object == 40`;
   - `monitor_provenance_counts.unique_cpa_object == 36`;
   - `monitor_provenance_counts.both_distinct_objects == 1`;
   - `monitor_provenance_counts.no_fire == 27`;
   - `monitor_provenance_counts.argmin_reconstruction_failed == 0`;
   - `monitor_provenance_counts.schema_unsupported == 0`;
   - `collision_actor_identity_fields == []`.
5. Iteration 59 summary has:
   - `completed_rows == 8`;
   - `support_counts.classifiable_foreground == 3`;
   - `support_counts.no_monitor_fire == 2`;
   - `support_counts.post_collision_fire == 2`;
   - `support_counts.background_collision_only == 1`.
6. Iteration 99 summary has:
   - `target_rows == 5`;
   - `covered_rows == 5`;
   - `compatible_rows == 5`;
   - `uncovered_rows == 0`;
   - `duplicate_or_incompatible_rows == 0`.
7. No source report has infra problems.

## Fixed measurements

Compute:

- broad committed transfer pool size from iteration 54;
- broad ON-collision count from iteration 54;
- monitor-side provenance support count from iteration 54;
- collision-actor-supported count from iteration 54;
- collision-actor-not-logged count from iteration 54;
- provenance-instrumented actor-match audit size from iteration 59;
- structural row count from iteration 59 support labels;
- completed structural-bridge coverage count from iteration 99;
- whether any larger committed row set can support structural bridge expansion without new
  collision-provenance instrumentation.

## Completion labels

- `expansion_boundary_no_collision_actor_support`: iteration 54 has a larger committed HUGSIM
  transfer pool with monitor-side provenance support but zero collision-actor support, while
  iteration 59/99 fully cover only the smaller provenance-instrumented structural subset.
- `expansion_candidate_committed_actor_support_present`: iteration 54 has nonzero collision-actor
  support beyond the iteration-59/99 subset.
- `expansion_support_mixed`: source checks pass, but the larger-row support pattern does not match
  either label above.
- `expansion_support_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL`: the audit classifies as
  `expansion_boundary_no_collision_actor_support`; the existing committed transfer pool is larger
  (`104` ON rows) but has zero collision-actor support, so the structural bridge map cannot be
  expanded from committed reports alone.
- `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_CANDIDATE_PRESENT`: the audit classifies as
  `expansion_candidate_committed_actor_support_present`.
- `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_MIXED_COMPLETE`: source checks pass but the support pattern
  is mixed.
- `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BLOCKED`: source checks fail or measurements are
  insufficient.

## Claim boundary

Report-level expansion-support boundary only. This does not claim actor causality, repair,
threshold value, transfer, safety, deployment, robustness, benchmark performance, population rate,
HD-Score invariance, commercial value, real-world behavior, first-responder behavior, retuning, or
approval to run a new HUGSIM job.
