# Iteration 50 - collision-opportunity audit pre-registration

Frozen before any iteration-50 analyzer, tooling, report, or claim. Committed alone. This is
an entirely offline audit over COMMITTED evidence only: zero GPU work, zero gcloud commands,
zero box reads. It follows the iteration-40 offline-audit format precedent
(`experiments/iter40_timing_cost_audit/HYPOTHESIS.md`).

## Iteration-49 firewall (binding, stated first because it is time-critical)

Iteration 49's hard/extreme-tier run was IN FLIGHT on the GPU box when this file was frozen.
**No iteration-49 outcome data — episode artifacts, eval.json files, decision rows, logs,
aggregates, or the analyzer verdict — has been read, and none may be read until this file is
committed and pushed. Iteration 49's data is out of bounds for iteration 50 entirely.** The
prediction P1 below is frozen while iteration 49 is unread. One disclosed sliver exists on
the record: the committed HANDOFF launch-verification block records three first-pair HD
values from launch time (scene-0013-extreme-00 OFF r1 `0.0` / ON r1 `0.0082`,
scene-0013-hard-00 OFF r1 `0.0054`), written per iteration 49's own protocol step 3. Those
three markers cannot determine either P1 input (the 52-episode OFF opportunity fraction or
the 52-pair clustered CI) and are disclosed rather than hidden. Any further iteration-49
read before this commit voids the iteration.

## Research question

Does collision OPPORTUNITY explain where the released union's benefit appears? The union
earned +0.783 NCAP on NeuroNCAP's scripted safety-critical scenarios
(`experiments/full14_power/RESULT.md`) and produced `TRANSFER_NULL` on HUGSIM easy+medium
(mean paired HD delta `-0.0166`, CI `[-0.0551, +0.0255]`) while demonstrably operating there
(37/52 ON episodes intervened; `experiments/iter48_hugsim_transfer_gate/RESULT.md`). A brake
monitor can only help where a collision is available to prevent. This audit (A1) tests
whether the NeuroNCAP benefit concentrates where the OFF arm collides, (A2) quantifies how
much collision opportunity the HUGSIM easy+medium OFF arms actually contained and classifies
the iteration-48 null accordingly, and (P1) pre-commits the interpretation of iteration 49's
outcome relative to opportunity, before its data is read.

## Prior published context (on the record before this freeze; not peeking)

The published class-level facts that motivated this audit: full14/power H-P3 (OFF collision
rates stationary 29% / frontal 78% / side 74%; class score deltas +0.48 / +0.54 / +1.33) and
iteration 48's secondaries (mean paired NC delta `-0.0369`, median `0.0000`; the two
scene-0051 over-braking episodes). No iteration-50 statistic — no opportunity count, no
collision fraction, no correlation, no stratified mean — has been computed before this
freeze.

## Pre-registration inspections performed (read-only, disclosed)

To freeze exact field names, the following STRUCTURE-ONLY inspections were performed before
this file, in the iteration-49 read-only-inventory precedent:

- one iteration-48 OFF `eval.json`
  (`proof-stage2/episodes/scene-0013-easy-00__off_r1/eval.json`): top-level numeric fields
  `nc`, `dac`, `ttc`, `c`, `pdms`, `rc`, `hdscore`, plus `details` keyed by simulation time
  with per-key `nc`/`dac`/`ttc`/`c`/`pdms`;
- one full14/power `metrics.json` (`p14-off/stationary-0783/run_4` inside
  `experiments/full14_power/proof/p14-runs.tar.gz`): boolean field `any_collide@0.0s`;
- `experiments/full14_power/analyze_power14.py` episode keying (`##### P14PAIR <arm> <scen>
  <seq>` markers and the `ncap_score: X,  impact_speed: Y` line regex in the merged log);
- directory listings only: iter46 `proof-off/episodes` (52 dirs = 38 completed + 14
  `__failed`), iter47 `proof-completion/episodes` (14 dirs), iter48 `proof-stage2/episodes`
  (104 dirs), each episode dir carrying `eval.json`/`output.txt`/`episode_meta.json`.

No other per-episode values were read; no aggregates were computed.

## Frozen evidence inputs (committed artifacts only)

- `experiments/full14_power/proof/p14-runs.tar.gz` (per-episode `metrics.json`,
  `any_collide@0.0s`);
- `experiments/full14_power/proof/sentinel-power14-merged.log` (per-episode `ncap_score`
  via `P14PAIR` markers, arms `off` and `best`);
- `experiments/full14_power/proof/analysis_output.txt` (H-P0 PASS integrity check only);
- `experiments/iter46_hugsim_off_baseline/proof-off/episodes/` (the 38 completed
  non-`__failed` episode dirs, `eval.json` each);
- `experiments/iter47_map_staging_and_off_completion/proof-completion/episodes/` (14
  episode dirs, `eval.json` each);
- `experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes/` (the 52 `__off_r*` OFF
  episode dirs for opportunity; the 52 pairs' `eval.json` `hdscore` values ONLY as the
  outcome variable in the descriptive stratification below);
- `experiments/iter48_hugsim_transfer_gate/proof-stage2/transfer_report.json` (integrity
  cross-check of the published mean delta only).

Nothing on the GPU box, nothing under `experiments/iter49_hugsim_hard_tier_gate/` beyond its
committed `HYPOTHESIS.md`, no uncommitted file, no external source.

## Frozen opportunity definitions (exact fields; no post-hoc changes)

**HUGSIM, per OFF episode (PRIMARY — the only definition any bar or P1 uses):** an episode
has collision opportunity iff `nc_min < 1.0`, where `nc_min = min(` top-level `nc`, minimum
over all `details.<t>.nc` values `)` from that OFF episode's `eval.json`.

**HUGSIM, per OFF episode (SECONDARY near-miss proxy — descriptive only, never substitutes
into any bar or into P1):** an episode is a near-miss iff it lacks primary opportunity AND
`ttc_min < 1.0`, computed identically over the `ttc` field.

**NeuroNCAP, per scenario pair:** OFF collision rate = fraction of that pair's completed
OFF episodes whose `metrics.json` has `any_collide@0.0s == true`. Known carried exception
(iteration-40 frozen facts): 400 best / 399 OFF metrics files over 20 pairs; `side-0921` OFF
n=19.

**Circularity guard (binding):** every opportunity label is computed from OFF-arm artifacts
ONLY. ON-arm data may appear only as the outcome variable (paired deltas / published
benefit), never in any opportunity label. The analyzer must not open ON-arm `eval.json` or
decision logs for opportunity computation.

**Frozen fraction bar, used by both A2 and P1:** `OPPORTUNITY_FRACTION_BAR = 0.25` — at
least 13 of 52 OFF episodes with primary opportunity counts as "opportunity present" at the
set level.

## A1 - NeuroNCAP: does the benefit concentrate where the OFF arm collides? (frozen method + bars)

Unit: the 20 full14/power scenario pairs. Per pair: `x` = OFF collision rate (above);
`y` = benefit = mean best-arm `ncap_score` minus mean OFF `ncap_score` over that pair's
completed episodes (merged log, `P14PAIR` markers, n=20/20 except OFF `side-0921` n=19).

- **Primary statistic:** Spearman rank correlation `rho` (average ranks for ties) between
  `x` and `y` over the 20 pairs, with a 95% percentile bootstrap CI: resample the 20
  `(x, y)` pairs with replacement, `10,000` draws, Python `random` seeded `50`; a draw with
  zero variance in either ranked vector contributes `rho = 0`.
- **Bars:** `A1_CONFIRMED` iff `rho >= +0.5` AND the CI excludes zero from below.
  `A1_INVERTED` iff the CI excludes zero from above. Otherwise `A1_ABSENT`.
- **Stratified means (support, no bar):** pairs with OFF collision rate `>= 0.5` vs
  `< 0.5`: per-stratum count, mean benefit, and the difference of means.

## A2 - HUGSIM easy+medium: how much opportunity did the OFF arms contain? (frozen bar)

Two OFF sets, both n=52:

- **H48-OFF (the classifying set):** iteration 48's 52 OFF episodes — the exact baseline
  the `TRANSFER_NULL` was paired against.
- **HBASE (corroboration):** the iteration-46/47 52-episode OFF baseline (38 iter46
  completed + 14 iter47).

Report per set: primary-opportunity count and fraction, secondary near-miss count, per-tier
(easy/medium) split, and a per-episode table.

**Frozen classification bar:** if the H48-OFF primary-opportunity fraction is `< 0.25`
(12 or fewer of 52), the iteration-48 `TRANSFER_NULL` is CLASSIFIED
**`OPPORTUNITY_SCARCE`** — the easy+medium tier gave the monitor almost nothing to prevent.
If `>= 0.25` (13 or more), it is CLASSIFIED **`OPPORTUNITY_PRESENT_NULL`** — opportunity
existed and the interventions still bought no measurable HD change. **Stated plainly: this
classification is an explanation of the null's domain, not an excuse, and it does NOT
upgrade, soften, or reopen the null. Iteration 48's `TRANSFER_NULL` stands as published
under either classification.**

**Descriptive stratification (no bar):** iteration 48's 52 committed paired HD deltas split
by whether the pair's OFF episode has primary opportunity (OFF-only label; ON data enters
only as the delta's outcome side); per-stratum count, mean, and median delta.

## P1 - THE FROZEN PREDICTION for iteration 49 (registered before its data is read)

The following text is the registered prediction, frozen verbatim while iteration 49's run
is unread; the operator who publishes iteration 49's RESULT must quote it and state which
branch obtained:

> **P1.** Compute the primary-opportunity fraction over iteration 49's 52 OFF episodes
> (`proof-hard/episodes/*__off_r*/eval.json`, frozen primary definition: `nc_min < 1.0`).
>
> **Branch A (opportunity present, benefit ports):** if at least 13/52 (`>= 0.25`) of the
> iteration-49 OFF episodes show primary collision opportunity AND iteration 49's own
> registered analyzer reports a mean paired HD delta (ON - OFF) whose 95%
> scenario-clustered CI excludes zero from below, P1 is **CONFIRMED**: the union's benefit
> reappears where collision opportunity is present, and iteration 48's null is explained
> as an opportunity-scarce transfer domain.
>
> **Branch B (opportunity present, benefit does not port):** if at least 13/52 show primary
> opportunity AND the CI includes zero or excludes it from above, P1 is **REFUTED**, and
> the conclusion is binding: the transfer failure is REAL, not opportunity-scarce — the
> monitor's mechanism does not port to HUGSIM even where collisions are available to
> prevent.
>
> **Branch C (opportunity absent at the harder tier):** if fewer than 13/52 show primary
> opportunity, P1 is **NOT TESTABLE** at the hard/extreme tier; that scarcity is itself a
> finding and is NOT a confirmation of anything.
>
> Iteration 49's analyzer remains its own registered gate with its own verdict classes;
> P1 pre-commits only the INTERPRETATION of that outcome relative to collision
> opportunity. Whichever branch obtains publishes on the record.

## Named falsifiers

- **Definition ambiguity (infrastructure null).** Any required OFF `eval.json` is missing
  or lacks a numeric `nc` (top-level or in `details`); the tar does not match the
  iteration-40 frozen facts (20 pairs, 400 best / 399 OFF metrics files, `side-0921` OFF
  n=19); or `P14PAIR` parsing yields an episode count other than 20 per arm per pair
  (except the recorded n=19) -> publish `OPPORTUNITY_AUDIT_INFRASTRUCTURE_NULL` and stop
  before any A1/A2 interpretation. If the primary NC definition cannot be supported by the
  committed fields, the infrastructure null publishes; the secondary proxy does NOT
  substitute into any bar.
- **Circularity.** Any opportunity label computed from ON-arm data -> void.
- **No post-hoc definition changes.** The definitions, the `0.25` bar, the A1 bars, and
  the P1 text above never move after data.
- **Iteration-49 leakage.** Any iteration-49 outcome data read before this file is
  committed and pushed -> void.
- **GPU/gcloud leakage.** Any GPU, Docker, gcloud, or box command run as part of this
  audit -> void.

## Forbidden claims (binding)

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world, or
monitor-performance claim. This audit only CLASSIFIES published results and REGISTERS a
prediction. It does not change iteration 48's verdict, does not pre-authorize or constrain
iteration 49's own registered verdict, and authorizes no run of any kind. The iteration-39
wording rules apply to every doc this iteration touches.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-audit/opportunity_report.json` (A1 + A2 numbers, falsifier evaluations);
- `proof-audit/opportunity_episodes.md` (per-episode HUGSIM opportunity table, both sets);
- `proof-audit/neuroncap_pairs.md` (per-pair A1 table: collision rate, benefit, ranks);
- `proof-audit/analyze_opportunity.command.txt` (exact command receipt).

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE, CI green, before any iteration-50 tooling exists and
   before any iteration-49 outcome data is read.
2. Commit the analyzer and tests; ruff + pytest + validate_docs green.
3. Run the analyzer ONCE over the committed artifacts listed above.
4. Publish `RESULT.md` at full weight (audit-complete with A1/A2 sub-verdicts, or the
   infrastructure null), quoting the P1 text verbatim.
5. Update README row 50 (row 49 stays in-flight), CONTINUITY arc + shift log, HANDOFF, and
   the operator memory file.
6. P1 resolution is executed later by whichever operator publishes iteration 49's RESULT,
   quoting the registered text verbatim and naming the branch.
