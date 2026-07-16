# Iteration 134 - NeuroNCAP placebo semantics execution: PLACEBO_HARM_OR_NULL

Status: `PLACEBO_HARM_OR_NULL` (analyzer verdict, one pass over committed proof; G2 passed, zero
drift; no falsifier fired). Published at full weight as the pre-registered outcome.

**The headline: this iteration does NOT resolve whether the released union's NeuroNCAP gain needs
its risk semantics.** The primary comparison is null under the pre-registered method AND is
confounded by a realized-dose gap that the pre-registration named in advance and that fired. The
union's `2.12 -> 2.91` benefit reproduced exactly. The semantics question remains open and needs a
dose-matched successor.

## Frozen proof

- Pre-registration (committed ALONE, before any tooling): [`HYPOTHESIS.md`](HYPOTHESIS.md), `647bab0`
- Design contract honored: `iter133.neuroncap_placebo_semantics_control_design.v1`
- Tooling + hash-bound manifest: [`launch_manifest.json`](launch_manifest.json), `2b9f560`
- Disclosed smoke: [`smoke-evidence/SMOKE.md`](smoke-evidence/SMOKE.md), `dc0bb23`
- Launch record + verbatim on-done block: `5c30941`
- **Run proof, committed BEFORE the analyzer ran: `b1a6714`** — [`proof/`](proof), 336 MB,
  [`proof/SHA256SUMS.txt`](proof/SHA256SUMS.txt)
- Analyzer (frozen at launch, sha `50992ba52f006fd0`, run ONCE, unedited):
  [`analyze_placebo134.py`](analyze_placebo134.py)
- Report: [`proof/placebo134_report.json`](proof/placebo134_report.json)

## The run

Launched 2026-07-14 12:59:10 UTC, `I134_PLACEBO_DONE` 2026-07-16 02:44:27 UTC. `1,200/1,200`
episodes, `0` `I134_ABORT` markers, `0` `__failed` dirs, `0` containers up at completion, ~37.75 h
wall at ~115 s/episode (inside the pre-registered 30-55 GPU-h; ceiling 80). G0 provenance passed at
launch and again at collection: all six hash-bound files byte-identical to the manifest, on the box
and in the repository.

## G2: the box did not drift, so the comparison is interpretable

`0` mismatches. All `400` `off` and `400` `union` episodes reproduce the committed `full14_power`
per-episode `ncap_score` **exactly**, despite the box since having staged and stripped ~61 GB of
HUGSIM assets, undergone the iteration-45 cleanup, gained a persisted swapfile, lost 20 GB of
docker build cache, and had two environment variables appended to the model container's `-e` list.

Two further reproductions, unplanned and worth recording:

- the fresh `union` arm emitted **`1,205` brake frames and `156` releases** — exactly the counts
  iteration 42 committed and proved by offline replay;
- `off/side-0921` completed **`20/20`**, where the committed power run carries `n=19` because
  run_19 reproducibly froze the pre-swap host across 3 attempts and 2 physical hosts. The
  persisted swapfile recovered the episode the power run permanently lost. The fresh OFF arm is
  more complete than the evidence it reproduces.

This also tests, rather than asserts, that the compose-script change (`-e SENTINEL_PLACEBO_PAIR
-e SENTINEL_PLACEBO_SCHEDULE`, model block only) is inert for the carried arms: 800 shared
episodes, zero divergence.

## Results

| arm | episodes | NCAP | safe-progress | collision rate |
|---|---:|---:|---:|---:|
| `off_baseline` | 400 | 2.135 | 2.395 | 52% |
| `released_union_semantic_reference` | 400 | **2.906** | 2.362 | 43% |
| `semantics_scrambled_budget_matched_placebo` | 400 | 2.538 | 2.085 | 50% |

Primary and secondaries, pre-registered method (20-pair-clustered bootstrap, 10,000 draws, seed
134):

| comparison | NCAP delta | 95% CI | excludes 0 |
|---|---:|---|---|
| **union − placebo (PRIMARY)** | **+0.3683** | **[−0.1901, +0.8866]** | **no** |
| placebo − off | +0.4026 | [−0.0038, +0.8947] | no |
| union − off | +0.7708 | [+0.3315, +1.2151] | yes |

Safe-progress (first-class, per the standing defensibility rule; a benchmark win may not hide a
progress regression): union − placebo `+0.2774` CI `[−0.1506, +0.7090]`; **placebo − off `−0.3099`
CI `[−0.7256, +0.0985]`**; union − off `−0.0325` CI `[−0.4717, +0.3643]`.

**The union's benefit reproduced.** union − off `+0.7708` against the committed `+0.783`; under the
power run's own method the CI is `[+0.6087, +0.9226]` against the committed `[+0.605, +0.928]`. The
`2.91` is real and re-established on an independent run.

## Why the verdict is `PLACEBO_HARM_OR_NULL`

By the four classes frozen in iteration 133 and restated in `HYPOTHESIS.md`, evaluated in order:

- not `SEMANTIC_VALUE_CONFIRMED`: union − placebo is positive but its CI includes zero;
- not `PLACEBO_EXPLAINS_GAIN`: placebo − off is positive but its CI includes zero (lower bound
  `−0.0038`, a hair from exclusion);
- not `PLACEBO_CONTROL_INFRA_NULL`: no gate failed;
- therefore `PLACEBO_HARM_OR_NULL`: the placebo does not beat OFF at this N, and it costs
  safe-progress (`2.085` vs OFF's `2.395`).

## THE CONFOUND FIRED. The primary comparison is not clean.

The pre-registration stated, before any episode ran:

> "episode length is an outcome, so a target episode may end before the donor's last scheduled
> brake frame... Scheduled budget is matched exactly; realized budget is measured and reported...
> It is also directionally conservative: if the placebo brakes slightly less than the union and
> still matches its score, the placebo's case is if anything understated. **If it brakes less and
> scores worse, that's a confound I'd have to state plainly rather than claim a semantic win.**"

It braked less and scored worse.

| | brake frames |
|---|---:|
| union (realized) | `1,205` |
| placebo (scheduled) | `1,205` |
| **placebo (realized)** | **`859`** (`0.713`) |

`union − placebo = +0.368` is therefore consistent with the risk semantics, with the `40%` larger
brake dose, or with both. **This design cannot separate them, and no semantic claim is made from
it in either direction.**

The mechanism is worse than simple truncation, and it is the iteration's most useful finding: the
placebo braking at borrowed times **caused collisions** (`50%` vs the union's `43%`), collisions
**ended episodes early**, and early endings **prevented the remaining scheduled brakes**. The
control could not spend its budget precisely because its timing was wrong. Budget matching is an
open-loop concept; in a closed loop the intervention determines how much of its own budget it can
spend. Scheduled-budget equality (exact, `1205 = 1205`, by bijection) does not survive contact with
the loop. Mid-run realization was `0.843` at 208 episodes and fell to `0.713` by 400 — the gap
widened as the arm entered the collision-dense frontal and side classes, exactly where dose matters
most.

## Method disagreement, disclosed rather than exploited

| union − placebo | delta | 95% CI | excludes 0 |
|---|---:|---|---|
| 20-pair-clustered (PRE-REGISTERED PRIMARY) | +0.3683 | [−0.1901, +0.8866] | no |
| run-index resampling (the method behind the committed `+0.783`) | +0.3683 | [+0.1464, +0.5723] | **yes** |

The two methods disagree on the primary question. The run-index method would license
`SEMANTIC_VALUE_CONFIRMED`. **It is not adopted.** `HYPOTHESIS.md` named the pair-clustered
bootstrap as primary before the run; selecting the other method after seeing which one flatters the
hypothesis is precisely the failure this apparatus exists to prevent. The run-index figures are
reported as registered comparability only, and they do not change the verdict.

Note the pair-clustered method is the more conservative and is consistent with iterations 48/49's
scenario-clustered standard: it widens every interval, including union − off (`[+0.332, +1.215]`
vs the run-index `[+0.609, +0.923]`). With 20 clusters the primary is underpowered.

## Honest reading

The placebo captured `+0.403` of the union's `+0.771` (a point estimate of ~52%) while realizing
`71%` of the dose, and it harmed driving progress. None of that is CI-confirmed at this N. The
suggestive shape — that some of the benchmark gain survives without any risk semantics, while the
semantics may be what buys braking without wrecking progress — is a hypothesis this iteration
generates, not a result it establishes.

## Analyzer defect, disclosed

`placebo_realized_frames` reports `0`. The placebo's frame rows carry `run` and `k` but no `pair`
key, and `realized_brakes()` skips rows lacking `pair`. Only the frame counter is affected; the
brake counter is unaffected and correct (`859`, independently confirmed by grep against the
committed log). No reported number depends on the frame count. The analyzer was NOT edited to fix
this: it is hash-bound and was run once, as registered. A successor may correct it under a fresh
pre-registration.

## Claim boundary

Measures whether the released union's NeuroNCAP gain survives a semantics-free, budget-matched
placebo on the NeuroNCAP 14-scene public set at n=20 per pair. It authorizes **no** claim that the
risk semantics are load-bearing, and **no** claim that they are not. It authorizes no HUGSIM or
transfer claim, does not rescue the iteration 48/49 transfer nulls, and will not be reported as
doing so. No repair, retuning, threshold change, benchmark ranking, deployment, safety, production,
commercial, acquisition-value, real-world, or frontier-stack equivalence claim.

The `union − off` reproduction is confirmatory of committed evidence, not a new benchmark claim.

## Successors (each needs a fresh pre-registration)

The confound is specific and fixable. Defensibility order:

1. **Dose-response placebo** — the placebo at several budget multiples. If the union outperforms
   *every* dose of semantics-free braking, the semantics are load-bearing regardless of the
   matching problem. Rigorous; the most expensive.
2. **Closed-loop budget controller** — a placebo that brakes until its budget is spent rather than
   at fixed frame indices, targeting ~100% realization. Changes the timing distribution; that
   change must be registered and measured, not assumed benign.
3. **Union truncated to the placebo's realized dose** — cheapest, and must be frozen before any
   outcome is read.
4. **Expanded N** — the pair-clustered primary is underpowered at 20 clusters; ~4x pairs to halve
   the CI is not available on this benchmark (14 scenes is the whole official set), so power must
   come from design, not scale.
