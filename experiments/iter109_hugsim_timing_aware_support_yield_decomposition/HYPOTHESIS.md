# Iteration 109 - HUGSIM timing-aware support-yield decomposition

Frozen after iteration 108 was published, but before any iteration-109 analyzer, decomposition
artifact, result, handoff update, or claim. This is an offline decomposition over committed
iteration-105, iteration-106, iteration-107, and iteration-108 artifacts only. It launches no GPU
work and changes no code under test.

## Context

Iteration 108 tested the timing-aware batch with the frozen iteration-59 actor-match support
rules. Infrastructure passed, but support still failed: `2/13` slots were
`classifiable_foreground` against the preregistered floor of `4`. That is an improvement over the
iteration-104 `1/13` support null, but not enough to support a stronger actor-match story.

The residual support labels were:

- `background_collision_only`: `6`;
- `post_collision_fire`: `4`;
- `no_collision_provenance`: `1`;
- `classifiable_foreground`: `2`.

## Research question

Why did the timing-aware design not translate into at least `4` foreground-classifiable rows in
the actual iteration-107 proof?

This iteration decomposes the gap between design-time timing eligibility and observed support
labels by joining each manifest slot to the iteration-108 episode row. It may report whether a
slot became unclassifiable because observed HUGSIM provenance was background-only, empty, or had
foreground contact before observed monitor fire. It may also report descriptive deltas between
manifest timing fields and observed first-fire/foreground timestamps.

This iteration may not select a new schedule, run a simulator, retune thresholds, or claim a
repair.

## Frozen inputs

- Iteration 105 design report:
  `experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/timing_aware_provenance_batch_design_report.json`
- Iteration 106 manifest:
  `experiments/iter106_hugsim_timing_aware_launch_manifest/proof-launch-manifest/timing_aware_launch_manifest.json`
- Iteration 107 execution report:
  `experiments/iter107_hugsim_timing_aware_batch_execution/proof-execution/timing_aware_batch_execution_report.json`
- Iteration 108 actor-match report:
  `experiments/iter108_hugsim_timing_aware_batch_actor_match_audit/proof-actor-match/timing_aware_batch_actor_match_report.json`

The analyzer may read only these committed files. It may not read live GPU state, raw box paths
outside committed proof, raw episode directories, or uncommitted files.

## Frozen residual labels

Each slot receives exactly one residual label:

- `classifiable_success`: iteration 108 labeled the slot `classifiable_foreground`.
- `observed_background_only`: iteration 108 labeled the slot `background_collision_only`.
- `observed_empty_collision_provenance`: iteration 108 labeled the slot
  `no_collision_provenance`.
- `observed_post_collision_fire`: iteration 108 labeled the slot `post_collision_fire`.
- `observed_no_monitor_fire`: iteration 108 labeled the slot `no_monitor_fire`.
- `observed_infra_or_schema_gap`: any other non-classifiable support label, row problem, or
  missing required timing/provenance field.

For every slot, the analyzer may compute:

- manifest `first_fire_ts`, `first_on_nc_time`, and `first_fire_lead_time`;
- observed iteration-108 `first_fire_ts`, `first_foreground_ts`, `foreground_count`,
  `provenance_count`, `support_label`, and `bridge_label`;
- `observed_first_fire_minus_manifest_first_fire_s` when both fire timestamps are finite;
- `observed_first_foreground_minus_manifest_first_on_nc_s` when both foreground timestamps are
  finite;
- `observed_fire_lead_s = observed_first_foreground_ts - observed_first_fire_ts` when both are
  finite.

## Frozen bars

- `HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_INFRA_NULL`: any frozen input is missing or
  malformed; iteration 107 is not `HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE`; iteration 108
  is not `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL` or
  `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_AUDIT_COMPLETE`; manifest, execution report, and
  actor-match report slot ids differ; any slot receives no residual label; or residual counts do
  not sum to `13`.
- `HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE`: all frozen inputs pass, all `13`
  slots are joined in manifest order, each slot receives exactly one residual label, and residual
  counts sum to `13`.

This is a descriptive decomposition. It has no success bar for improving Sentinel.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-decomposition/timing_aware_support_yield_decomposition_report.json`;
- `proof-decomposition/timing_aware_support_yield_decomposition.md`;
- `proof-decomposition/analyze_timing_aware_support_yield_decomposition.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-105/106/107/108 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No actor-causality, actor-match support upgrade, repair, threshold-value, transfer, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, retuning, production, commercial, schedule-selection,
or GPU-approval claim.
