# Iteration 105 - HUGSIM timing-aware provenance batch design

Frozen after iteration 104 was published, but before any iteration-105 analyzer, generated
schedule, result, manifest, launcher, GPU run, proof artifact, or claim. This is an offline
candidate-design step only. It launches no simulator work and changes no code under test.

## Process disclosure

This is not blind. Iteration 104 already published a support null over the iteration-103
instrumented batch:

- `13/13` slots had valid proof artifacts;
- only `1` slot was `classifiable_foreground` against the registered floor of `4`;
- the support split was `6` background-only, `4` post-collision-fire, `2` no-monitor-fire, and
  `1` classifiable foreground `actor_mismatch`.

After that result, a small read-only count probe over the committed iteration-54 timing/support
fields and the iteration-59/104 already-instrumented scenario lists showed that a timing-aware
candidate pool exists after exclusion. Those exploratory counts are disclosed as process context
only. The frozen rules below govern the actual iteration-105 analyzer and report.

## Research question

Can the committed HUGSIM transfer evidence support a deterministic next-run candidate schedule
that is better targeted for actor-match support than iteration 101 by selecting ON-collision rows
where the released union fired at or before the first ON collision time?

This iteration may produce only a future instrumentation schedule. It does not authorize a GPU
launch. A later launch-manifest preflight must bind scenario hashes and slot ids before any run.

## Frozen inputs

- Iteration 54 provenance support report:
  `experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json`
- Iteration 59 actor-match report:
  `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`
- Iteration 104 actor-match support report:
  `experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/provenance_batch_actor_match_report.json`
- Iteration 52 timing report, cross-check only:
  `experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json`

The analyzer may read only these committed reports. It may not read raw episode directories,
live GPU state, scenario YAMLs, uncommitted files, or box paths.

## Frozen eligibility rules

A row is timing-eligible iff all of the following are true in the iteration-54 report:

1. `on_collision` is `true`;
2. `fire_timing_label` is `long_lead_fire` or `short_lead_fire`;
3. `first_fire_lead_time` is numeric and `>= 0.0`;
4. `first_fire_channel` is `cpa_only` or `ttc_only`;
5. `monitor_provenance_label` is `unique_cpa_object` or `unique_ttc_object`.

Rows whose scenario appears in either iteration 59 or iteration 104 are excluded from the primary
candidate pool. Excluded rows may be reported as carried context only; they cannot be selected
unless the primary candidate pool has fewer than `13` eligible rows.

## Frozen deterministic selection policy

The analyzer must build a `13`-slot future schedule from the primary candidate pool if possible.
Selection is deterministic:

1. Start with required coverage buckets:
   - both datasets: `iter48_easy_medium` and `iter49_hard_extreme`;
   - both channels: `cpa_only` and `ttc_only`;
   - all available tiers among `easy`, `medium`, `hard`, and `extreme`;
   - both timing labels if both are available in the primary pool.
2. For each coverage bucket, choose the highest-priority row not yet selected. Priority is:
   higher `first_fire_lead_time`, then higher `brake_frames`, then higher `fired_frames`, then
   lexicographic `scenario`, then lower `run`.
3. Fill remaining slots by the same priority over unselected primary-pool rows.
4. Do not select more than two runs from the same scenario.
5. Preserve duplicates by assigning slot ids, not by scenario.

## Frozen bars

- `HUGSIM_TIMING_AWARE_BATCH_DESIGN_INFRA_NULL`: any frozen input is missing/malformed; iteration
  54/59/104 verdicts do not match the expected committed results; the iteration-52 timing counts
  contradict iteration-54 pre/post/no-fire labels for the selected rows; or selected rows violate
  the deterministic policy.
- `HUGSIM_TIMING_AWARE_BATCH_DESIGN_SUPPORT_NULL`: infrastructure passes but the primary pool
  has fewer than `13` eligible rows, or the selected schedule has fewer than `13` slots, fewer
  than `8` unique scenarios, fewer than `2` datasets, fewer than `2` channels, fewer than `3`
  tiers, or no `short_lead_fire` row when such rows exist in the primary pool.
- `HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE`: infrastructure passes and the selected schedule
  has `13` slots, at least `8` unique scenarios, both datasets, both channels, at least `3`
  tiers, and at least one `short_lead_fire` row if any primary-pool short-lead rows exist.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-design/timing_aware_provenance_batch_design_report.json`;
- `proof-design/timing_aware_provenance_batch_design.md`;
- `proof-design/analyze_timing_aware_provenance_batch_design.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run targeted lint/tests and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed reports.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No GPU approval, launch authorization, actor-causality, actor-match result, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim. This iteration may only claim whether committed evidence
supports a timing-aware future instrumentation schedule under the frozen rules.
