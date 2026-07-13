# Iteration 53 - HUGSIM first-fire channel audit

Frozen before any iteration-53 analyzer, proof artifact, result, or claim. Committed alone.
This is an offline post-result audit over committed HUGSIM proof only: zero GPU work, zero
gcloud commands, zero box reads, zero simulator launches, zero monitor retuning, and zero
external data.

## Process disclosure

This is not blind. Iterations 48-52 are already published. Before freezing this file, two
pre-registration inspections were performed:

1. The committed iteration-48 HUGSIM patch was read. It confirmed the released union fires on
   `min_cpa < 1.5 OR min_ttc < 2.5`, not on the stricter simultaneous TTC+CPA proxy used in
   iteration 52 as a conservative surface proxy.
2. A small aggregate probe over the already-published iteration-52 report found `35`
   pre-collision-brake ON-collision cases; `26/35` had zero simultaneous TTC+CPA surface-proxy
   rows and `9/35` had at least one. The probe also printed one example where the monitor braked
   before collision via low CPA with TTC effectively infinite, and two example decision rows
   showing TTC-only first fires.

Those inspections are disclosed rather than hidden. This audit therefore makes no inferential
surprise claim and uses no statistical pass/fail bar. It freezes only the exact official channel
classification, proof tables, grouping, and forbidden claims.

## Research question

Iteration 52 split ON-collision persistence into absent/post-collision braking (`57/92`) and
pre-collision braking (`35/92`). The pre-collision family, especially the `26` long-lead cases,
is the key reason "just brake earlier" is insufficient.

This audit asks the next narrower question:

**When the released union fired on HUGSIM, which side of the union fired first — TTC-only,
CPA-only, or both — and how does that channel distribute across post-collision and pre-collision
ON-collision cases?**

This is a mechanism-cause audit. It does not identify the true colliding actor and does not
test a new rule.

## Frozen evidence inputs

Committed artifacts only:

- `experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes/`
- `experiments/iter49_hugsim_hard_tier_gate/proof-hard/episodes/`
- `experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json`
  for pair-count/timing-bin cross-checks only.

The analyzer must not read the GPU box, staged scenario YAMLs, uncommitted files, external
sources, or future experiment directories.

## Frozen unit and fields

Unit: one ON-arm HUGSIM paired episode, `(dataset, scenario, run)`.

Fields:

- ON collision timing exactly as iteration 52: `nc_min < 1.0` over top-level `nc` and
  `details.<t>.nc`, with earliest details timestamp as `first_on_nc_time`.
- Decision log rows from `sentinel_iter48_decisions.jsonl`.
- `first_fire_ts`: first row with `fired == true`.
- `first_brake_ts`: first row with `brake == true`.
- First-fire channel from the first fired row:
  - `ttc_only`: `min_ttc < 2.5` and `min_cpa >= 1.5`;
  - `cpa_only`: `min_cpa < 1.5` and `min_ttc >= 2.5`;
  - `both`: both thresholds crossed;
  - `no_fire`: no fired row;
  - `fired_channel_unreconstructable`: fired row exists but scalar minima do not reconstruct
    either side of the OR predicate.
- First-fire lead relative to ON collision:
  - `no_on_collision`: ON `nc_min >= 1.0`;
  - `unknown_collision_time`: ON collides but no details timestamp supports first time;
  - `no_fire`;
  - `post_collision_fire`: first fire after first ON collision;
  - `short_lead_fire`: first fire `0 <= lead <= 1.0` s before first ON collision;
  - `long_lead_fire`: first fire more than `1.0` s before first ON collision.

If any required `eval.json` or ON decision log is missing or lacks numeric fields needed for
these labels, publish `FIRST_FIRE_CHANNEL_INFRASTRUCTURE_NULL` and stop before interpretation.

## Frozen summaries

Report counts for:

- all 104 ON-arm paired episodes;
- the 92 ON-collision episodes;
- iteration 48 and iteration 49 separately;
- iteration 49 AttackPlanner vs non-AttackPlanner scenarios;
- iteration-52 timing bins crossed with first-fire channel;
- pre-collision-fire ON collisions (`short_lead_fire + long_lead_fire`) crossed with channel.

Also report descriptive HD materiality per first-fire channel using the iteration-51 deadband
`0.03`.

No dominance threshold is used because the pre-freeze inspections are disclosed. The result may
state exact counts and proportions, but not statistical significance or a confirmed repair.

## Forbidden claims

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world,
monitor-performance, HUGSIM-equivalence, actor-identity, or retuning claim. The audit may only
decompose the already-published HUGSIM nulls under the frozen first-fire-channel labels. It
cannot say which object caused a collision and cannot select a new rule family without a later
fresh pre-registration.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-channel/first_fire_channel_report.json`;
- `proof-channel/first_fire_channel_pairs.md`;
- `proof-channel/analyze_first_fire_channel.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer ONCE over committed inputs.
4. Publish `RESULT.md` at full weight: either `FIRST_FIRE_CHANNEL_COMPLETE` or
   `FIRST_FIRE_CHANNEL_INFRASTRUCTURE_NULL`.
5. Update README, CONTINUITY, HANDOFF, and push.
