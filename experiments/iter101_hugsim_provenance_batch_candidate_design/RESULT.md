# Iteration 101 - HUGSIM provenance batch candidate design: HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE

Status: `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE` (offline candidate-schedule design
for a future collision-provenance-instrumented HUGSIM batch).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, raw `eval.json` files, or raw episode directories, and
did not retune Sentinel. It used only the committed iteration-54, iteration-59, and iteration-100
reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_provenance_batch_design.py`](analyze_provenance_batch_design.py)
- Tests: [`../../tests/test_iter101_provenance_batch_design.py`](../../tests/test_iter101_provenance_batch_design.py)
- Analyzer command:
  [`proof-design/analyze_provenance_batch_design.command.txt`](proof-design/analyze_provenance_batch_design.command.txt)
- JSON report:
  [`proof-design/provenance_batch_candidate_design_report.json`](proof-design/provenance_batch_candidate_design_report.json)
- Markdown report:
  [`proof-design/provenance_batch_candidate_design.md`](proof-design/provenance_batch_candidate_design.md)

## Result

The analyzer cross-checked:

- iteration-54 verdict: `PROVENANCE_SUPPORT_NULL`;
- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-100 verdict: `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL`;
- iteration 54's committed ON-collision rows have the expected monitor-provenance stratum counts;
- iteration 59 provides the existing instrumented scenario set to exclude where possible;
- iteration 100 says a larger structural bridge requires new collision-provenance support;
- no source report has infra problems.

Summary:

- selected total rows: `13`;
- selected new candidate rows: `12`;
- carried singleton reference rows: `1`;
- all seven strata covered: `true`;
- existing instrumented scenario count: `8`.

Selected schedule:

| role | dataset | stratum | scenario | run | tier | timing | first fire | first collision |
|---|---|---|---|---:|---|---|---:|---:|
| `new_candidate` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `1` | `easy` | `no_fire` | none | `3.50 s` |
| `new_candidate` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `2` | `easy` | `no_fire` | none | `2.75 s` |
| `new_candidate` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0038-medium-01` | `1` | `medium` | `long_lead_fire` | `9.75 s` | `16.00 s` |
| `new_candidate` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0062-medium-00` | `2` | `medium` | `long_lead_fire` | `12.75 s` | `18.50 s` |
| `new_candidate` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `1` | `easy` | `post_collision_fire` | `11.50 s` | `1.50 s` |
| `new_candidate` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `2` | `easy` | `post_collision_fire` | `11.50 s` | `1.75 s` |
| `new_candidate` | `iter49_hard_extreme` | `no_fire` | `scene-0041-extreme-00` | `2` | `extreme` | `no_fire` | none | `3.25 s` |
| `new_candidate` | `iter49_hard_extreme` | `no_fire` | `scene-0062-hard-00` | `1` | `hard` | `no_fire` | none | `16.25 s` |
| `new_candidate` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `1` | `extreme` | `post_collision_fire` | `2.50 s` | `0.25 s` |
| `new_candidate` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `2` | `extreme` | `post_collision_fire` | `2.50 s` | `0.25 s` |
| `new_candidate` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `1` | `hard` | `long_lead_fire` | `7.00 s` | `8.50 s` |
| `new_candidate` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `2` | `hard` | `post_collision_fire` | `7.00 s` | `4.75 s` |
| `carried_existing_singleton` | `iter49_hard_extreme` | `both_distinct_objects` | `scene-0138-extreme-00` | `1` | `extreme` | `post_collision_fire` | `5.25 s` | `3.50 s` |

## Interpretation

Iteration 101 freezes a deterministic candidate schedule for a later, separately registered
collision-provenance-instrumented batch. The design covers the six non-singleton
dataset/provenance strata with two new candidates each after excluding iteration-59 scenarios
where possible. The only both-distinct monitor-provenance row is carried as a reference because it
is a singleton in the committed transfer pool and was already instrumented in iteration 59.

This result is a design artifact, not a run authorization.

## Claim boundary

Offline candidate-schedule design only; no actor-causality, repair, threshold-value, transfer,
safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value,
real-world behavior, first-responder behavior, retuning, GPU approval, or approval to run the
proposed batch.
