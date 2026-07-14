# Iteration 101 - HUGSIM provenance batch candidate design

## Research question

Given iteration 100's support boundary, can we freeze a small, deterministic candidate schedule
for a future collision-provenance-instrumented HUGSIM batch from the committed 104-row transfer
pool, while avoiding already instrumented iteration-59 scenarios where possible and preserving the
rare both-distinct monitor-provenance singleton as a carried reference?

## Scope

This is an offline report-level batch-design audit. It may read only these committed reports:

- `experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json`
- `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`
- `experiments/iter100_hugsim_structural_expansion_support_audit/proof-expansion/structural_expansion_support_report.json`

It must not read raw decision logs, raw `eval.json` files, raw episode directories, launch Docker,
touch the GPU box, run HUGSIM, modify thresholds, tune parameters, or infer counterfactual vehicle
outcomes. It creates only a candidate schedule for a later separately pre-registered run; it does
not authorize that run.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 54 verdict is `PROVENANCE_SUPPORT_NULL`.
2. Iteration 59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`.
3. Iteration 100 verdict is `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL`.
4. Iteration 54 combined summary has the same support boundary used by iteration 100:
   - `pairs == 104`;
   - `on_collision_pairs == 92`;
   - `monitor_provenance_counts.unique_ttc_object == 40`;
   - `monitor_provenance_counts.unique_cpa_object == 36`;
   - `monitor_provenance_counts.both_distinct_objects == 1`;
   - `monitor_provenance_counts.no_fire == 27`;
   - `collision_actor_support_counts.collision_actor_supported == 0`.
5. Iteration 59 has exactly eight completed rows and an existing instrumented scenario set derived
   from its `episodes[*].scenario` fields.
6. Iteration 100 summary has:
   - `larger_committed_pool_exists == true`;
   - `can_expand_from_committed_reports == false`;
   - `new_instrumentation_required_for_larger_structural_bridge == true`.
7. No source report has infra problems.

## Fixed selection rule

The analyzer must use only iteration-54 `pairs` where `on_collision == true`. It partitions rows by
`(dataset, monitor_provenance_label)` and freezes these seven strata:

1. `iter48_easy_medium` / `no_fire`;
2. `iter48_easy_medium` / `unique_cpa_object`;
3. `iter48_easy_medium` / `unique_ttc_object`;
4. `iter49_hard_extreme` / `no_fire`;
5. `iter49_hard_extreme` / `unique_cpa_object`;
6. `iter49_hard_extreme` / `unique_ttc_object`;
7. `iter49_hard_extreme` / `both_distinct_objects`.

For the first six strata, select exactly two candidate rows per stratum after excluding any row
whose `scenario` is already present in the iteration-59 instrumented scenario set. Sort eligible
rows by `(scenario, run)` before taking the first two. For the seventh stratum, select the single
row even if its scenario is already in iteration 59, and label it `carried_existing_singleton`
rather than `new_candidate`, because iteration 54 has only one both-distinct row.

## Fixed measurements

Compute:

- iteration-54 on-collision stratum counts;
- iteration-59 existing instrumented scenario set;
- eligible-after-exclusion counts for each of the first six strata;
- selected new-candidate rows per stratum;
- carried singleton rows;
- selected total row count;
- selected new-candidate count;
- selected carried-reference count;
- whether the design covers all seven strata.

## Completion labels

- `provenance_batch_design_balanced_with_carried_singleton`: all six non-singleton strata select
  exactly two new candidate rows after excluding iteration-59 scenarios, and the both-distinct
  singleton is selected as a carried existing reference.
- `provenance_batch_design_partial`: source checks pass, but at least one non-singleton stratum
  has fewer than two eligible rows after exclusion or the singleton is missing.
- `provenance_batch_design_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE`: the audit classifies as
  `provenance_batch_design_balanced_with_carried_singleton`, yielding `12` new candidate rows and
  `1` carried singleton reference row.
- `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_PARTIAL_COMPLETE`: the audit classifies as
  `provenance_batch_design_partial`.
- `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_BLOCKED`: source checks fail or measurements are
  insufficient.

## Claim boundary

Offline candidate-schedule design only. This does not claim actor causality, repair, threshold
value, transfer, safety, deployment, robustness, benchmark performance, population rate,
HD-Score invariance, commercial value, real-world behavior, first-responder behavior, retuning, GPU
approval, or approval to run the proposed batch.
