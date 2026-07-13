# Iteration 52 - HUGSIM ON-collision timing audit

Frozen before any iteration-52 analyzer, proof artifact, result, or claim. Committed alone.
This is an offline post-result audit over committed HUGSIM proof only: zero GPU work, zero
gcloud commands, zero box reads, zero simulator launches, zero monitor retuning, and zero
external data.

## Process disclosure

This is not blind. Iterations 48-51 are already published, and before this file was frozen a
small prototype timing probe was run over committed iteration-48/49 artifacts to check whether
the ON-arm `eval.json` and decision logs can support the proposed timing bins. The probe counted:

- iteration 48 ON collisions: `40` total; no-brake `10`, post-ON-collision first brake `14`,
  short-lead brake `1`, long-lead brake `15`;
- iteration 49 ON collisions: `52` total; no-brake `12`, post-ON-collision first brake `21`,
  short-lead brake `8`, long-lead brake `11`.

Those counts are disclosed rather than hidden. This audit therefore makes no inferential
surprise claim and uses no statistical pass/fail bar. It freezes the exact official analyzer,
proof tables, grouping, and forbidden claims before any iteration-52 result file exists.

## Research question

Iteration 51 showed that the HUGSIM transfer failure is mostly collision persistence, not lack
of collision opportunity: only `6/91` OFF-opportunity pairs converted and `85/104` combined
pairs remained collision-persistent. The next narrower question is:

**When ON still collides, did the released union brake too late for the ON trajectory, fail to
enter the frozen TTC/CPA monitor surface at all, or brake before the ON collision and still fail
to change the outcome?**

This is a mechanism-cause audit of the published nulls. It does not test a new monitor, does
not retune thresholds, and cannot establish true actor identity or real-world causality.

## Frozen evidence inputs

Committed artifacts only:

- `experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes/`
- `experiments/iter49_hugsim_hard_tier_gate/proof-hard/episodes/`
- `experiments/iter51_hugsim_failure_taxonomy/proof-taxonomy/failure_taxonomy_report.json`
  for pair-count/category-count cross-checks only.

The analyzer must not read the GPU box, staged scenario YAMLs, uncommitted files, external
sources, or future experiment directories.

## Frozen unit and fields

Unit: one ON-arm HUGSIM paired episode, `(dataset, scenario, run)`.

Fields:

- `on_collision`: ON `nc_min < 1.0`, where `nc_min` is the minimum of top-level `nc` and all
  numeric `details.<t>.nc`, exactly matching iterations 50-51.
- `first_on_nc_time`: earliest `details.<t>.nc < 1.0`; if only the top-level value is below
  `1.0`, timing is `unknown_top_level_only`.
- `first_brake_ts`: first ON decision row with `brake == true`.
- `brake_frames`, `fired_frames`, `monitor_frames`.
- `surface_proxy_rows`: decision rows with `min_ttc <= 2.5` and `min_cpa <= 1.5`, the frozen
  NeuroNCAP TTC/CPA thresholds. This is a **proxy for entering the monitor's geometric timing
  surface**, not the full firing predicate, because score/closing/latch details are not fully
  reconstructable from the scalar minima alone.
- `first_surface_proxy_ts`: first row satisfying the proxy.
- `lead_time = first_on_nc_time - first_brake_ts` for ON-collision episodes with known timing
  and at least one brake frame.

## Frozen ON-collision timing bins

The primary table includes only ON-collision episodes. Non-ON-collision pairs are counted as
`excluded_no_on_collision` and not assigned a timing bin.

Bins are mutually exclusive and assigned in this order:

1. `unknown_collision_time`: ON collides but `first_on_nc_time` is unavailable because the
   collision is visible only in the top-level metric.
2. `no_brake_no_surface_proxy`: ON collides, `brake_frames == 0`, and `surface_proxy_rows == 0`.
3. `no_brake_surface_proxy_present`: ON collides, `brake_frames == 0`, and
   `surface_proxy_rows > 0`.
4. `post_collision_first_brake`: ON collides, has brake frames, and `first_brake_ts` is
   greater than `first_on_nc_time`.
5. `short_lead_brake`: ON collides, has brake frames, and `0 <= lead_time <= 1.0` seconds.
6. `long_lead_brake`: ON collides, has brake frames, and `lead_time > 1.0` seconds.

If any required `eval.json` or ON decision log is missing or lacks numeric fields needed for
these bins, publish `TIMING_AUDIT_INFRASTRUCTURE_NULL` and stop before interpretation.

## Frozen summaries

Report counts for:

- combined iteration 48+49 ON-collision episodes;
- iteration 48 easy+medium ON-collision episodes;
- iteration 49 hard/extreme ON-collision episodes;
- iteration 49 AttackPlanner vs non-AttackPlanner scenarios, using the same schedule facts
  frozen in iteration 49 and reused in iteration 51;
- material HD gain/loss per bin using the iteration-51 descriptive deadband `0.03`.

Also report two descriptive families:

- `absent_or_post_collision_brake_family` =
  `no_brake_no_surface_proxy + no_brake_surface_proxy_present + post_collision_first_brake`;
- `pre_collision_brake_family` = `short_lead_brake + long_lead_brake`.

No dominance threshold is used because the pre-freeze prototype counts are disclosed. The
result may say "larger" or "smaller" by exact count, but not "confirmed", "significant", or
"dominant" as an inferential finding.

## Forbidden claims

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world,
monitor-performance, HUGSIM-equivalence, or retuning claim. The audit may only decompose the
already-published HUGSIM nulls under the frozen timing bins. It cannot say which actor caused
a collision, cannot claim braking causally failed, and cannot select a new rule family without
a later fresh pre-registration.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-timing/on_collision_timing_report.json`;
- `proof-timing/on_collision_timing_pairs.md`;
- `proof-timing/analyze_on_collision_timing.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer ONCE over committed inputs.
4. Publish `RESULT.md` at full weight: either `TIMING_AUDIT_COMPLETE` or
   `TIMING_AUDIT_INFRASTRUCTURE_NULL`.
5. Update README, CONTINUITY, HANDOFF, and push.
