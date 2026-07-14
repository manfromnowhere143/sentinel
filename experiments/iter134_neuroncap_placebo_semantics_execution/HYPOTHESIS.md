# Iteration 134 - NeuroNCAP placebo semantics execution: pre-registration

Frozen before any tooling, donor extraction, manifest, or GPU work. This is the execution of the
control frozen by iteration 133. It is the first iteration since 49 that asks the benchmark a
question instead of asking the repository a question.

## The question

The released union lifts NeuroNCAP from `2.12` to `2.91` (`+0.783`, CI `[+0.605, +0.928]`, 799
episodes). That gain is attributed to the union's risk semantics: closing-TTC and plan-vs-path CPA
computed from the frozen planner's own outputs.

Nothing in the campaign has yet tested whether the semantics are load-bearing. Iteration 13
compared the union against an RSS-style envelope, which is a different decision rule, not an
absence of one. Iteration 50 showed the benefit concentrates where collision opportunity exists
(Spearman rho `+0.7003`), which is consistent with real skill and also consistent with "braking
helps wherever a scripted actor is aimed at the ego".

> Does the released union's NeuroNCAP gain require its risk semantics, or does a semantics-free
> braking schedule, matched on actuator, scenario class, and intervention budget, reproduce it?

If a placebo that cannot see the world reproduces the gain, then on this benchmark the union's
score is not evidence about its risk estimate.

## Frozen inputs

- Iteration 133 design contract: `iter133.neuroncap_placebo_semantics_control_design.v1`
  (`experiments/iter133_neuroncap_placebo_semantics_control_design/proof-design/neuroncap_placebo_semantics_control_design_report.json`)
- Released-union patch: `experiments/iter15_latch_release/server_patch_union_release.py`
- Power-run launcher (pair order and env discipline):
  `experiments/full14_power/power14_run.sh`
- Committed union decision log: `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-a*`
- Committed OFF decision log: `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-a*`
- Committed per-episode scores: `experiments/full14_power/proof/sentinel-power14-merged.log`
- Power-run analyzer (reused, not rewritten): `experiments/full14_power/analyze_power14.py`

Established by reading those inputs before this pre-registration was written, and recorded here so
the record shows what was known in advance:

- the released union is iteration 15's latched zero-trajectory stop, not iteration 16's crawl.
  Three independent confirmations: the launch marker
  `patch=/tmp/server_patch_union_release.py extra=SENTINEL_RELEASE_K=4`; `RESULT.md` stating the
  decision rule fired for the released union because the crawl failed its safety gate; and the
  decision log containing `1,205` `brake` rows and `0` `crawl` rows;
- the union log contains exactly `400` reset blocks, `6,474` frame rows, `1,205` brake rows, and
  `156` release rows, matching iteration 42's committed trace counts;
- the run index cycles `0..19` per pair, so decision-log block `b` maps to pair `PAIRS[b // 20]`
  and run `b % 20` in canonical launcher order.

## Frozen scenario list and pair order

Canonical launcher order, 20 pairs:

- `stationary`: `0099 0101 0103 0106 0108 0278 0331 0783 0796 0966`
- `frontal`: `0103 0106 0110 0346 0923`
- `side`: `0103 0108 0110 0278 0921`

## Arms

Three arms, exactly as the iteration 133 contract requires, one launch, arm-major order, same
frozen planner, same benchmark stack, same scenario list, same run-index discipline, 20 runs per
pair:

1. `off_baseline`: `SENTINEL_ENABLED=0`.
2. `released_union_semantic_reference`: `server_patch_union_release.py`, frozen parameters
   `SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 SENTINEL_TTC=2.5
   SENTINEL_MIN_CLOSING=3 SENTINEL_RELEASE_K=4`. Any change to any of these voids the iteration.
3. `semantics_scrambled_budget_matched_placebo`: the placebo defined below.

Total: `20` pairs x `20` runs x `3` arms = `1,200` episodes.

## The placebo, frozen

The placebo inherits the released union's actuator byte-for-byte and receives its firing from a
donor schedule instead of from the world.

- Actuator: while scheduled, return `[[0.0, 0.0] for _ in range(len(base))]`, the identical zero
  trajectory of `server_patch_union_release.py`. Otherwise return the planner's plan unchanged.
- The placebo does not read `out.aux_outputs`, `objects_in_bev`, `object_scores`, `future_trajs`,
  `object_ids`, `data.ego2world`, or `data.timestamp` for any decision. It reads only a per-run
  frame counter. It computes no CPA, no TTC, no closing speed, no score gate, no latch, no
  release. It has no access to outcomes.
- Firing rule: at frame `k` of the target episode, return the zero trajectory if and only if
  `k` is in the donor schedule set.

Donor selection, deterministic from committed identifiers alone:

- For target (class `C`, pair at index `p` within `C`, run `i`):
  - donor pair index `q = (p + 1) mod len(C)`
  - donor run `j = (i + 1) mod 20`
  - donor schedule = the set of frame indices at which the committed union episode
    (`C`, `PAIRS_C[q]`, run `j`) emitted a `brake` row.
- `q != p` and `j != i` hold by construction, satisfying donor exclusion of the target pair and
  the target seed.
- The map is a bijection on (pair, run) within each class, so the placebo's scheduled brake budget
  equals the union's brake budget exactly at class level and in total.

Frame indexing, frozen: frame `k` is the `k`-th frame row (`ts` key) after a `reset` row within a
donor block, zero-based. Frame `k` is a brake frame if and only if a `brake` row occurs between
frame row `k` and frame row `k + 1`.

Disclosed in advance, not a falsifier: episode length is an outcome, so a target episode may end
before the donor's last scheduled brake frame, or outlast it. Scheduled budget is matched exactly;
realized budget is measured and reported per arm and per class. Any realized-budget gap is stated
in the result, never corrected post hoc.

## Primary and secondary measures

- Primary: mean per-pair NCAP score difference `released_union - placebo`, 20-pair-clustered
  bootstrap, `10,000` draws, seed `134`, 95 percent CI.
- Secondary 1: `placebo - off_baseline`, same treatment. This is the measure that distinguishes a
  placebo that does nothing from a placebo that does the union's work.
- Secondary 2: safe-progress for all three arms, first-class. A benchmark-score result that hides
  a safe-progress regression is not a win, per the standing defensibility rule.
- Reported descriptively, never as a claim: per-class breakdown, collision rate per arm, realized
  vs scheduled brake budget, episode-length distribution per arm.

## Verdict classes, frozen by iteration 133

- `SEMANTIC_VALUE_CONFIRMED`: `union - placebo > 0` with CI excluding zero. The semantics are
  load-bearing and the headline survives its harshest control.
- `PLACEBO_EXPLAINS_GAIN`: `placebo - off > 0` with CI excluding zero, and `union - placebo` CI
  including zero. The headline must be downgraded toward generic braking and timing.
- `PLACEBO_HARM_OR_NULL`: the placebo does not beat OFF. Published at full weight.
- `PLACEBO_CONTROL_INFRA_NULL`: any validity gate below fails. No semantic claim either way.

The verdict is whatever the analyzer returns on its single pass. All four classes publish at full
weight.

## Validity gates

- G0 provenance: the placebo patch file SHA256 and the analyzer file SHA256 recorded in the launch
  manifest must be byte-identical to the committed copies, verified on the box before the first
  episode and again at collection. Mismatch voids.
- G1 semantic-leak guard, mechanical: the committed placebo patch source must contain none of
  `aux_outputs`, `objects_in_bev`, `object_scores`, `future_trajs`, `object_ids`, `ego2world`,
  `cpa`, `ttc`, `closing`, `min_score`, `SENTINEL_TTC`, `SENTINEL_CPA_MARGIN`,
  `SENTINEL_MIN_CLOSING`, `SENTINEL_MAXGAP`, `SENTINEL_MIN_SCORE`, or `SENTINEL_RELEASE_K`. A hit
  voids the iteration. A placebo that can name a risk term is not a placebo.
- G2 exact-reproduction integrity (the drift gate): every `off_baseline` and
  `released_union_semantic_reference` episode must reproduce the committed `full14_power`
  per-episode `ncap_score` exactly at the same (arm, class, pair, run index). This box has since
  staged and removed HUGSIM assets, been cleaned, and gained swap. If the two carried arms do not
  reproduce, the environment drifted and the placebo comparison is not interpretable:
  `PLACEBO_CONTROL_INFRA_NULL`. Known and accepted exception: committed `off/side-0921` is at
  `n=19`; its run 19 is compared only if it completes here, and its absence is not a mismatch.
- G3 schedule integrity: the donor schedule set for every one of the 400 placebo episodes must be
  derived only from committed union log blocks, must exclude the target pair and target seed, and
  must be frozen in the launch manifest with a SHA256 before the first episode.
- G4 completion: `1,200` planned episodes; any episode that fails is retried once, and every
  incomplete episode is reported. Below `95` percent completion in any arm:
  `PLACEBO_CONTROL_INFRA_NULL`.

## Falsifiers

- The placebo patch fires on anything derived from the observed world: void.
- Any frozen union parameter changes: void, per the standing F1 discipline.
- The donor schedule is regenerated, reselected, or filtered after any episode runs:
  `post_run_schedule_selection_forbidden` is breached, void.
- The analyzer is modified after the first episode runs: void. One pass, from committed artifacts.
- G2 fails: `PLACEBO_CONTROL_INFRA_NULL`, environment drift documented.

## Compute

Expected `30` to `55` GPU-hours on the single L4, ceiling `80` GPU-hours. Swap is persisted in
`/etc/fstab` as of 2026-07-14, which is the recorded fix for the memory-exhaustion freezes that
cost the power run five host freezes and forced `off/side-0921` to `n=19`. Operator approval for
GPU use is recorded for this iteration.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Build the donor extractor, placebo patch, launch manifest generator, launcher, analyzer, and
   tests. Run focused lint, tests, and the docs guard.
3. Generate and commit the launch manifest, hash-binding scenario pair ids, scenario classes, run
   indices, arm ids, donor schedule ids, donor-exclusion receipts, actuator budget summaries,
   patch SHA256, analyzer SHA256, and environment receipts. Nothing runs before this is committed.
4. Launch once, detached, done marker `I134_PLACEBO_DONE`.
5. On done: collect artifacts and commit proof FIRST. Then run the analyzer ONCE over the
   committed artifacts. Then publish `RESULT.md` at full weight in whichever verdict class fires.
6. Update README row 134, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, regenerate `HANDOFF.md`, run full
   gates, push.

Never relaunch while containers are up.

## Claim boundary

This iteration measures whether the released union's NeuroNCAP gain survives a semantics-free,
budget-matched placebo on the NeuroNCAP easy public-scene family at `n=20` per pair. It authorizes
no HUGSIM claim, no transfer claim, no repair, no retuning, no threshold change, no benchmark
ranking, no deployment, safety, production, commercial, acquisition-value, real-world, or
frontier-stack equivalence claim.

It does not rescue the iteration 48 and 49 transfer nulls and will not be reported as doing so.

A `PLACEBO_EXPLAINS_GAIN` verdict is a statement about what the NeuroNCAP score can and cannot
distinguish under this control, on these scenes, at this N. It is not a claim that any other
published NeuroNCAP result is wrong. Any such implication requires its own pre-registration and
its own evidence.
