# Iteration 135 - NeuroNCAP blind-braking dose response: pre-registration

Frozen on 2026-07-16 before any iteration-135 extractor, schedule generator, patch, analyzer,
manifest, smoke artifact, or analytic GPU episode exists. This file must be committed alone.

## Pre-data amendment 1 - compose-block execution order

Frozen in a second hypothesis-only commit before any Iteration-135 tooling commit, smoke, or
analytic episode. Inspection of the already committed NeuroNCAP launcher established that one
compose invocation runs all 20 indices for one `(arm, pair)` block. The original per-cell six-arm
rotation would have required `2,400` model/container startups rather than `120`, invalidating the
frozen compute ceiling without improving the inferential pairing.

The execution unit is therefore amended, before data, to a **pair-major 20-run arm block**. For
global pair index `p`, run the cyclic rotation by `p mod 6` of the same six-arm base order. There
are exactly `20 pairs x 6 arm blocks = 120` compose invocations and 20 run indices inside each
block. Every arm still occupies every pair/run cell exactly once and appears in each within-pair
temporal block position three or four times. Scenario-pair inference, common run identities,
scheduled doses, outcomes, margins, estimators, verdicts, resource gates, and episode count do not
change. The superseded per-cell rotation below is replaced in place so the executable contract is
unambiguous; this amendment records why.

## Pre-data amendment 2 - zero-retry block execution

Frozen in a third hypothesis-only commit before any Iteration-135 tooling commit, live smoke, or
analytic episode. Tooling construction exposed that the compose interface has no clean mechanism
to resume only the unfinished run indices inside a 20-run block. Retrying a partially completed
block would therefore duplicate completed cells and make the retained analytic attempt depend on
post-treatment execution state.

The execution policy is amended to **zero retries**. The first failed or timed-out analytic block
aborts the launch, retains its evidence and permanent launch lock, and publishes
`PLACEBO_DOSE_INFRA_NULL`; it is never automatically or manually relaunched as part of this
preregistration. This amendment changes only the infrastructure-failure path. The design,
schedule, estimands, verdicts, complete-run requirements, and total resource ceiling do not
change.

## Pre-data amendment 3 - complete tooling and evidence inventory

Frozen in a fourth hypothesis-only commit before any Iteration-135 tooling commit, live smoke, or
analytic episode. Tooling construction decomposed the originally named monolithic test surface
into independently reviewable schedule, patch, manifest, launcher, smoke, environment, proof,
analyzer, and verifier lanes. The required-artifact inventory below is expanded to name that exact
surface and remove the superseded monolithic test path. This is a provenance correction only; no
design, data, gate, estimator, verdict, or resource rule changes.

Iteration 135 is the terminal causal-diligence experiment on the current NeuroNCAP suite. It asks
one confirmatory question at the originally frozen matched budget and uses three additional doses
only to look for evidence that would weaken that interpretation. It is not a product-readiness or
external-transfer experiment.

## Question and causal object

> At the same ex-ante assigned class-level braking budget, does the released semantic union improve
> NeuroNCAP by a practically meaningful amount over a clock-only braking policy without losing
> more than five percentage points of fixed-horizon progress?

The causal object is the **assigned policy**. Realized brake count, collision, episode duration,
and termination are post-treatment outcomes. They may be reported as mechanisms, but they may not
enter matching, adjustment, arm eligibility, missingness filtering, the primary estimator, or the
verdict.

The confirmatory contrast is fixed now and only now:

```text
released_union_semantic_reference - blind_1_0x
```

The `0.5x`, `1.5x`, and `2.0x` blind policies cannot create an alternative path to semantic-value
confirmation. Their simultaneous intervals may only qualify or downgrade the primary result.

## Known before this pre-registration

### Published evidence

- The released union raised the full14 power result from `2.12` to `2.91`: `+0.783`, CI
  `[+0.605,+0.928]`.
- Iteration 134 completed `1,200/1,200` fresh episodes. Union minus OFF was `+0.7708`, CI
  `[+0.3315,+1.2151]`; union minus the clock-only placebo was `+0.3683`, CI
  `[-0.1901,+0.8866]`; the placebo realized `859/1205` scheduled brake frames. The published
  verdict was `PLACEBO_HARM_OR_NULL`, and semantic attribution remained unresolved.
- HUGSIM transfer remains null. Nothing in this experiment can change that result.

### A decision-rule defect found in the audit

Iteration 133 froze `minimum_semantic_margin_ncap: 0.25` and required both a point difference of at
least `0.25` and a scenario-clustered interval excluding zero. Iteration 134's HYPOTHESIS and
analyzer silently weakened that rule to any positive point difference with an interval excluding
zero. Iteration 134 stayed null under the weaker rule, so no published verdict was inflated. This
iteration restores the `0.25` practical margin. The historical Iteration-134 result is not edited.

Sources:

- `experiments/iter133_neuroncap_placebo_semantics_control_design/proof-design/neuroncap_placebo_semantics_control_design_report.json`
- `experiments/iter134_neuroncap_placebo_semantics_execution/HYPOTHESIS.md`
- `experiments/iter134_neuroncap_placebo_semantics_execution/analyze_placebo134.py`

### Progress facts found in the audit

Iteration 134's `safe-progress` is NCAP multiplied by a clipped path factor; it is not raw
progress. A read-only, class-stratified reanalysis of the committed Iteration-134 run tar, known
before this file was frozen, found:

| arm | full-path clipped progress | raw mean ego path |
|---|---:|---:|
| OFF | `0.8917` | `33.89 m` |
| union | `0.7535` | `26.97 m` |
| placebo | `0.7535` | `27.82 m` |

Union minus OFF full-path progress was `-0.1382`, CI `[-0.2009,-0.0792]`; union minus placebo was
approximately `0.0000`, CI `[-0.0857,+0.0908]`. Under the fixed first-16-pose definition frozen
below, Iteration 134 was OFF `0.9027`, union `0.7631`, placebo `0.7600`; union minus placebo was
`+0.0031`, CI `[-0.0802,+0.0906]`. These values do not imply OFF was safer: an OFF vehicle can
travel farther into a collision. They do mean that progress must be exposed separately and cannot
be hidden inside the benchmark score.

The `-0.05` progress non-inferiority margin below is deliberately stricter than the lower bound
seen in that audit. It was not chosen to make the known Iteration-134 comparison pass.

Committed source tar and SHA256:

```text
b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315
experiments/iter134_neuroncap_placebo_semantics_execution/proof/i134-runs.tar.gz
```

### Dose and power facts found in the audit

The committed union proof contains `400` episodes, `6,474` frame rows, `1,205` brake rows, `156`
release rows, `265` contiguous braking windows, and `170/400` episodes with no braking window. The
class brake totals are stationary `416`, frontal `475`, and side `314`; mean nonempty window length
is `4.55` frames.

A class-stratified reanalysis of the Iteration-134 union-placebo NCAP contrast had empirical SE
approximately `0.2466`. With only 20 independent scenario-pair clusters, approximate 80% minimum
detectable effect is about `0.61` for one one-sided contrast and about `0.76` across four
multiplicity-controlled contrasts. More run seeds do not create more independent scenes.

Therefore this experiment is not advertised as 80%-powered for the restored `0.25` margin. It can
establish a large fixed-suite effect or expose generic-braking competitiveness; an inconclusive
result is expected to remain possible. `MATCHED_BUDGET_INCONCLUSIVE` closes further NeuroNCAP
threshold/placebo work rather than weakening the margin or adding more seeds.

## Frozen source inputs

- Released behavior:
  `experiments/iter15_latch_release/server_patch_union_release.py`, SHA256
  `d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189`.
- Byte-identical Iteration-134 copy:
  `experiments/iter134_neuroncap_placebo_semantics_execution/server_patch_union_release.py`.
- Union decision proof:
  - `proof/sentinel_i134_union.jsonl.gz.part-aa`, SHA256
    `4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85`
  - `proof/sentinel_i134_union.jsonl.gz.part-ab`, SHA256
    `93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97`
  under `experiments/iter134_neuroncap_placebo_semantics_execution/`.
- Iteration-134 environment, launcher, manifest, proof, and result in that same directory.
- The exact Iteration-134 OFF and union episodes are the drift oracle and pilot only. No
  Iteration-134 placebo outcome enters the Iteration-135 estimator.

## Frozen scenario population and independent unit

Canonical class/pair order:

- `stationary`: `0099 0101 0103 0106 0108 0278 0331 0783 0796 0966`
- `frontal`: `0103 0106 0110 0346 0923`
- `side`: `0103 0108 0110 0278 0921`

Each arm runs indices `0..19` for every pair. The population-inference unit is the scenario pair,
not the episode: `10/5/5` independent clusters by class, 20 total. Within a pair, the 20 run
indices are repeated common-seed measurements and are averaged before population inference. All
arms use the same pair/run identities and benchmark randomness.

The fixed-suite estimand covers exactly these 20 pairs and 20 run indices. Population language
beyond this public suite is forbidden.

## Arms and execution order

Six fresh arms, `20 pairs x 20 runs = 400` episodes per arm:

1. `off_baseline`
2. `released_union_semantic_reference`
3. `blind_0_5x`
4. `blind_1_0x`
5. `blind_1_5x`
6. `blind_2_0x`

Total: `2,400` analytic episodes. No prior episode substitutes for a fresh cell.

Execution is pair-major in 20-run arm blocks. For canonical global pair index `p`, run the cyclic
rotation by `p mod 6` of:

```text
[off_baseline, released_union_semantic_reference, blind_0_5x,
 blind_1_0x, blind_1_5x, blind_2_0x]
```

Each block runs indices `0..19` before the next arm block. Every arm therefore occurs once per
pair/run cell and occupies each within-pair temporal block position three or four times. The
manifest must materialize all `120` blocks, all `2,400` cells, and their exact order before launch.

OFF and union use the same byte-identical released-union patch; only `SENTINEL_ENABLED` differs.
Union parameters remain:

```text
SENTINEL_MIN_SCORE=0.3
SENTINEL_MAXGAP=30
SENTINEL_CPA_MARGIN=1.5
SENTINEL_TTC=2.5
SENTINEL_MIN_CLOSING=3
SENTINEL_RELEASE_K=4
```

Any change voids the experiment.

## Blind schedule family

### Donor mapping

Parse the committed Iteration-134 union proof in canonical block order. For target class `C`, pair
index `p` within `C`, and run `i`:

```text
donor pair q = (p + 2) mod len(C)
donor run  j = (i + 7) mod 20
```

This is a bijection within each class and excludes the target pair and run. It differs from the
known Iteration-134 `+1/+1` mapping.

Frame `k` is the zero-based `k`-th frame row after a donor reset. A donor brake at `k` is a brake
row between frame rows `k` and `k+1`. The donor horizon is the donor's committed frame count.

### Deterministic supported allocation

For every target schedule, construct one ordered list of unique candidate frames inside its donor
horizon:

1. Anchor: if the donor has brake frames, choose the brake frame nearest the median brake frame;
   ties use the SHA-256 rule below. If it has no brake frames, choose the SHA-256-minimum horizon
   frame.
2. Remaining donor brake frames, ordered by distance to the median of their contiguous donor
   braking window, then SHA-256.
3. Remaining non-brake frames, ordered by minimum distance to a donor brake frame, then SHA-256.
4. For a zero-brake donor, all remaining horizon frames are ordered by SHA-256.

Every tie hash is the lowercase hexadecimal SHA-256 of:

```text
iter135.blind_dose.v1|class|target_pair|target_run|donor_pair|donor_run|frame
```

Merge candidate lists within each class by candidate ordinal first and tie hash second. This
round-robin ordering prevents the class budget from concentrating in a few schedules. The first
`B(C,d)` unique candidates form policy `P_d`. Because the same master order is prefix-selected:

```text
P_0.5 subset P_1.0 subset P_1.5 subset P_2.0
```

The `0.5x` class budgets exceed the number of schedules in every class, so every one of the 400
target schedules receives at least one ex-ante assigned brake frame at every dose. This repairs the
zero-support defect without conditioning on a target outcome. It does not guarantee realized dose:
closed-loop termination remains an outcome.

Exact class-global scheduled budgets, using round-half-up:

| dose | stationary | frontal | side | total |
|---|---:|---:|---:|---:|
| `0.5x` | `208` | `238` | `157` | `603` |
| `1.0x` | `416` | `475` | `314` | `1,205` |
| `1.5x` | `624` | `713` | `471` | `1,808` |
| `2.0x` | `832` | `950` | `628` | `2,410` |

Available donor horizons are stationary `3,624`, frontal `1,347`, and side `1,503`; every budget
is feasible.

### Runtime information boundary

The blind patch may read only:

- the base trajectory, solely to return it unchanged on nonscheduled frames;
- frozen `(class, pair, run, frame)` identity;
- frozen dose ID and schedule membership.

It returns the exact released actuator
`[[0.0, 0.0] for _ in range(len(base))]` on scheduled frames. It may not read or name scene state,
timestamps, ego pose, auxiliary planner outputs, detections, scores, tracks, futures, risk terms,
collisions, metrics, episode length, realized-budget feedback, CPA, TTC, closing speed, latch state,
or release state. It has no learned component and no outcome feedback.

## Outcomes

### NCAP

For each arm and pair, average the 20 per-episode NCAP scores. The arm aggregate is the equal mean
of the stationary, frontal, and side class means.

### Fixed-horizon progress `Q16`

For each episode, sort ego poses by key and use at most the first 16 pose samples. Sum Euclidean
ego translation over those samples. If the episode terminates before sample 16, the last pose is
absorbing and adds zero further distance; collision and normal benchmark completion are both
terminal outcomes, not censored observations.

For pair `p`, let `L_off,p` be the fresh OFF mean fixed-horizon distance across its 20 runs. The
episode factor is:

```text
min(1, episode_fixed_horizon_distance / L_off,p)
```

Average within pair, then take the equal mean of the three class means. The OFF denominator is
recomputed from fresh Iteration-135 data inside every integrity calculation; it is never imported
from a previous run.

### Mandatory separate reporting

Report all of these even when they do not change the verdict:

- NCAP score and impact speed;
- `Q16`, full raw path length, and the legacy safe-progress composite as separate columns;
- collision rate and terminal reason;
- scheduled and realized brake frames and windows by dose, class, pair, and run;
- realization fraction, intervention-free realized-episode fraction, and episode frame count;
- per-class point estimates and pair-level values.

No collision-free subset, realized-dose match, survivor analysis, regression adjustment, or
missingness-filtered estimate may be called causal.

## Confirmatory estimator and inference

For the `1.0x` policy only:

```text
delta_N = NCAP_union - NCAP_blind_1.0x
delta_Q = Q16_union - Q16_blind_1.0x
```

Use a paired, class-stratified scenario-pair bootstrap:

- average 20 runs within each arm/pair first;
- resample `10/5/5` pairs with replacement inside stationary/frontal/side;
- carry all arms for a sampled pair together;
- `100,000` draws, PRNG seed `135`;
- one-sided 95% lower bound is sorted draw index `4,999` (zero-based);
- one-sided 95% upper bound is sorted draw index `94,999`;
- ordinary two-sided 95% interval uses indices `2,499` and `97,499`.

The primary is an intersection-union gate. Semantic budget efficiency requires both conditions, so
no multiplicity correction is taken between them:

1. NCAP superiority with restored practical size:
   `delta_N >= 0.25` and one-sided `LCB_N > 0`.
2. Progress non-inferiority:
   one-sided `LCB_Q > -0.05`.

The original unstratified 20-pair bootstrap, 14-source-scene clustering, and run-index resampling
are sensitivity analyses only. They cannot change the verdict. Their disagreement must be printed.

## Secondary dose frontier and multiplicity

For all four blind doses, estimate union-minus-blind NCAP and `Q16`: eight contrasts. Construct one
simultaneous two-sided 95% max-|T| confidence family across all eight pair-clustered contrasts,
using the same `100,000` paired class-stratified draws and seed. For contrast `j`, `SE_j` is the
sample standard deviation (`ddof=1`) of its bootstrap draws and
`T_bj = (delta_bj - delta_j) / SE_j`. Let `M_b = max_j(abs(T_bj))`; the critical value is sorted
`M` index `94,999`. The simultaneous interval is `delta_j +/- critical * SE_j`. A zero-SE
contrast receives the exact interval `[delta_j,delta_j]` and is omitted from the maximum. These
rules and hostile zero-variance tests must be frozen before launch.

The dose curve is the four arm means joined by straight line segments in ascending assigned dose.
No polynomial, optimum dose, isotonic repair, selected-dose contrast, class-specific significance
claim, or post-run curve form is allowed. Class differences are descriptive unless a frozen
interaction contrast in the simultaneous family is added before launch; they may not be inferred
from separate uncorrected intervals.

For a blind dose `d`, with simultaneous interval `[L_Nd,U_Nd]` and `[L_Qd,U_Qd]`:

- blind dose is **competitive** only if `U_Nd < +0.25` and `U_Qd < +0.05`;
- blind dose **Pareto-dominates** only if it is competitive and either:
  - point `delta_Nd <= -0.25` with `U_Nd < 0`, or
  - point `delta_Qd <= -0.05` with `U_Qd < 0`.

These doses may downgrade a semantic interpretation. They cannot create one.

## Verdict and mandatory qualifier

Evaluate in this order:

1. `PLACEBO_DOSE_INFRA_NULL`
   - any validity gate or falsifier fails.
2. `GENERIC_BRAKING_DOMINATES`
   - the `1.0x` primary satisfies the reverse dominance rule using its primary one-sided bounds,
     or any blind dose satisfies the simultaneous secondary Pareto-dominance rule.
3. `SEMANTIC_MATCHED_BUDGET_CONFIRMED`
   - the `1.0x` confirmatory NCAP and `Q16` gates both pass.
4. `BLIND_MATCHED_BUDGET_COMPETITIVE`
   - primary one-sided `UCB_N < +0.25` and `UCB_Q < +0.05`, without dominance.
5. `MATCHED_BUDGET_INCONCLUSIVE`
   - infrastructure is valid and none of the above fires.

The reverse `1.0x` dominance rule is: blind is competitive by the preceding primary upper bounds,
and either point `delta_N <= -0.25` with `UCB_N < 0`, or point `delta_Q <= -0.05` with
`UCB_Q < 0`.

Every non-infrastructure verdict also carries exactly one simultaneous-frontier qualifier:

- `BLIND_FRONTIER_DOMINATES`
- `BLIND_FRONTIER_COMPETITIVE`
- `NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED`

Choose `BLIND_FRONTIER_DOMINATES` first if any dose meets dominance; otherwise choose
`BLIND_FRONTIER_COMPETITIVE` if any dose meets competitiveness; otherwise choose the third label.

The verdict and qualifier must both appear in the result headline. A primary semantic confirmation
with a competitive higher or lower blind dose must be stated as such, never shortened to a pure
semantic win.

`MATCHED_BUDGET_INCONCLUSIVE` is terminal for further NeuroNCAP threshold, seed-count, placebo,
or dose searches. The next evidence lane is an external deployment-fault benchmark or a
Sentinel-owned fault harness under a fresh pre-registration.

## Validity gates

- **G0 preregistration:** this `HYPOTHESIS.md` is the only file in its commit and predates every
  iteration-135 tool and analytic artifact.
- **G1 provenance:** manifest-bind the source union logs and their hashes; schedule generator;
  generated schedule; union and blind patches; analyzer; launcher; compose script; checkpoint;
  container image IDs/digests; shim; pair/run/arm order; environment receipts; and smoke receipts.
  Box and repository copies must match before launch and collection.
- **G2 released behavior:** the Iteration-135 union patch is byte-identical to Iteration 15 and
  Iteration 134 at the frozen SHA256. OFF differs only by `SENTINEL_ENABLED=0`.
- **G3 schedule integrity:** donor exclusion, bijection, frame parsing, exact class totals,
  per-schedule support, uniqueness, horizon bounds, nesting, master-order determinism, and all 400
  schedules per dose pass mechanical tests.
- **G4 semantic leak:** the static guard must detect risk terms in the union patch and detect none
  in the blind patch. A guard that is empty on both patches is invalid, not green.
- **G5 live smoke:** nonanalytic smoke proves every dose fires at exactly its frozen scheduled
  frames, passes through the base trajectory otherwise, emits `(class,pair,run,frame,dose)`, fixes
  Iteration 134's missing-pair counter defect, and receives every required environment variable
  inside the model container. Smoke episodes never enter analysis.
- **G6 drift:** all 400 fresh OFF and 400 fresh union episodes reproduce Iteration 134 per-episode
  NCAP and impact speed exactly. Canonical fixed-horizon path lengths must agree within `1e-6` m.
  Fresh union emits exactly `1,205` brake rows and `156` release rows. Any mismatch is infra-null.
- **G7 completion:** every arm completes `400/400` analytic cells with zero retries. The first
  failed or timed-out block aborts the launch, retains its evidence and permanent launch lock, and
  yields infra-null. Any automatic or manual analytic relaunch under this preregistration is a
  protocol violation and also yields infra-null.
- **G8 storage:** before launch, the remote execution/evidence filesystem has at least `100 GiB`
  free and projected output plus `25 GiB` reserve; before collection, local disk has at least
  `15 GiB` free. Cleanup may remove only hash-verified duplicates, reproducible renders, and caches.
  Current proof, required image digests, checkpoints, logs without committed equivalents, and
  secrets are never deleted.
- **G9 resource ceiling:** no launch above the committed resource budget below. Ceiling breach
  stops the run and publishes infra-null; it does not license silent continuation.

## Falsifiers and forbidden adaptations

Any of these makes the result `PLACEBO_DOSE_INFRA_NULL`:

- schedule regeneration, re-ranking, dose change, arm deletion, run-index substitution, or pair
  change after launch;
- analyzer, metric, margin, bootstrap, verdict-order, or qualifier change after launch;
- any runtime access by the blind patch beyond its frozen information boundary;
- realized-dose matching, collision/survival filtering, regression adjustment, missingness
  filtering, selected-dose inference, or post-run power-based rule change;
- launch-manifest hash mismatch, undisclosed environment drift, unbalanced/misordered cells,
  failed leak discrimination, failed smoke, failed reproduction, or incomplete proof;
- analyzer execution before the raw proof is committed.

Nulls and infra-nulls publish at full weight.

## Compute, storage, and retry budget

Iteration 134 averaged approximately 115 seconds per episode. `2,400` episodes project to `76.7`
single-L4 GPU-hours before smoke and aborted-partial-work overhead. Frozen budget:

- expected analytic window: `65-90` GPU-hours;
- absolute total ceiling including smoke and any aborted partial work: `110` GPU-hours;
- one L4 only; no parallel-host mixture;
- zero analytic retries; abort and retain evidence on the first failed or timed-out block;
- remote free-space gate `100 GiB` plus projected-output reserve;
- local collection gate `15 GiB`.

The operator's 2026-07-16 instruction authorizes continued mission work and safe cleanup. It does
not override any gate above. GPU launch remains separately locked until all tooling, provenance,
storage, smoke, and live-idle checks are committed and green.

## Protocol

1. Commit this file alone. In an immediately following state-only commit, classify it as the active
   hypothesis and advance the phase; push both commits before any iteration-135 tooling commit.
2. Build extractor, supported nested schedule generator, two patches, analyzer, manifest generator,
   pair-major launcher, tests, and a read-only strategic preflight note.
3. Generate schedule and manifest; bind every code/data/environment/input digest. Update
   `MISSION_STATE.json` to the exact phase. Run full lint, unit, historical, documentation, and
   hostile mutation tests.
4. Inventory storage and required image/checkpoint digests. Perform only verified safe cleanup.
5. Run nonanalytic live smoke. Commit smoke evidence and a launch-readiness receipt. Re-run every
   gate. Regenerate the handoff from a clean tree.
6. Only if state says `LAUNCH_AUTHORIZED`, the box is idle, remote and local storage gates pass,
   and hashes match, launch once detached with done marker `I135_DOSE_DONE`.
7. On completion, collect and hash proof, verify completeness, and commit raw proof **before** the
   analyzer runs.
8. Run the frozen analyzer once over committed proof. Publish the exact verdict and frontier
   qualifier, update current surfaces, run all gates, regenerate handoff, commit, and push.

Never relaunch while any renderer, model, NeuroNCAP, or unknown evaluation container is running.

## Required artifacts after tooling is authorized

```text
experiments/iter135_neuroncap_blind_braking_dose_response/
  HYPOTHESIS.md
  extract_union_windows.py
  generate_nested_dose_schedules.py
  dose_schedules.json
  server_patch_union_release.py
  server_patch_blind_dose.py
  patch_compose_dose_env.py
  analyze_dose135.py
  collect_proof135.py
  capture_environment135.py
  make_launch_manifest.py
  launch_manifest.json
  env_receipts.json
  run_dose135.sh
  run_smoke135.sh
  validate_smoke135.py
  verify_tooling135.py
  tooling_verification_receipt.json
  smoke-evidence/SMOKE.md
  smoke-evidence/*
  proof/SHA256SUMS.txt
  proof/sentinel-i135.log.gz
  proof/sentinel_i135_*.jsonl.gz
  proof/i135-runs.tar.gz
  proof/dose135_report.json
  RESULT.md

tests/test_iter135_analyzer.py
tests/test_iter135_environment_capture.py
tests/test_iter135_harness_patches.py
tests/test_iter135_launch_manifest.py
tests/test_iter135_launcher.py
tests/test_iter135_proof_collector.py
tests/test_iter135_runtime_patches.py
tests/test_iter135_schedule_tools.py
tests/test_iter135_smoke_pipeline.py
tests/test_iter135_tooling_verifier.py
```

## Claim boundary

This iteration can establish only a fixed-suite, matched-assigned-budget difference between the
released union and frozen clock-only policies on the 20-pair NeuroNCAP public set. Even
`SEMANTIC_MATCHED_BUDGET_CONFIRMED` is not evidence of real-world safety, production readiness,
fault tolerance, transfer, planner-agnostic portability, a complete blind-policy frontier, or a
commercial safety case.

It cannot rescue the HUGSIM null, repair the known 5 cm jitter fragility, validate VAD, authorize a
Bench2Drive claim, compare Sentinel with Tesla/Mobileye systems, establish benchmark SOTA, or
support an acquisition-value statement. Product/runtime extraction and external fault validation
require independent gates and evidence.
