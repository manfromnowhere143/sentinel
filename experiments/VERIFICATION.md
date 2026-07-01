# Independent verification pass — claim-vs-evidence audit of the full campaign

**What this is.** Before building anything new on top of the iteration-8 union result, an independent
verification pass re-derived every headline claim from raw evidence, attacked the statistics, and
re-ran the key experiments fresh on the GPU. The operator performing this pass had no stake in the
prior results; the brief was to break them and certify only what survives. Everything below is
reproducible from evidence committed in this repository (`verification/evidence/`).

**Bottom line.** The campaign's qualitative claims survive: the monitor is selective, it solves most
side-impact collisions, it mitigates the frontal head-on, the three evasion nulls are real (and get
*stronger* under audit). Two quantitative headline claims did **not** survive as stated and are
corrected in place:

1. **The pooled n=20 statistical validation was invalid.** NeuroNCAP episodes are deterministic per
   run index, so the "three independent replications" pooled in `union_validation/` were the *same
   episodes* re-run — runs 0–5 were counted three times each. The honest unique-episode count is 8
   per scene per arm, and at n=8 the safe-progress CI **does not exclude zero**.
2. **Side-impact is 100% → 12.5% on unique episodes, not 100% → 5%** (and iteration 8's "8/8
   avoided" was wrong — its own log shows a collision at run 6 that the iteration-8 analysis missed
   because it raced the last runs).

A fresh evaluation with 20 *genuinely distinct* episodes per scene per arm (run indices 0–19) was
executed to re-measure the headline honestly — results in §4.

---

## 1. What was audited and how

- **Re-ran every committed analysis script against committed raw data** (locally, no GPU state):
  `iter2_monitor/g1_auroc.py` on `proof/risk.jsonl.gz` + `proof/outcomes.tsv`;
  `union_validation/pooled_union_ci.py` logic re-implemented against the run logs.
- **Pulled the raw evidence off the GPU box** (per-run NCAP scores from the run logs, per-run
  `ego_poses.json` and `metrics.json`, the per-frame monitor decision logs `sentinel_*.jsonl`) and
  committed it under `verification/evidence/` — the box is ephemeral; every number below is now
  derivable from the repo alone.
- **Cross-checked every RESULT.md figure against the raw logs, run by run** (`audit_pooling.py`).
- **Re-ran the key results fresh on the box** with an expanded, honest sample (§4).

## 2. Claims that reproduce exactly

| claim | verification |
|---|---|
| G1: label-free risk separates collisions, AUROC 0.83 at the imminent horizon | re-ran `g1_auroc.py` on committed proof: output byte-identical (AUROC 0.827, 40 runs, 26/14 split) |
| iter2: monitored 1.92→4.67, collision 65%→13%, CI [+2.21, +3.22] | re-derived from committed `ab_outcomes.tsv`/`outcomes.tsv`; single-iteration data, unique runs, no pooling defect |
| iter11: evasion on a false alarm crashes the clean scene (50%) | raw log confirms: early-evade stationary = 3/6 collisions, mean 3.07 — exactly as published |
| iters 9/10: evasive steering worse than the committed stop on frontal | raw logs confirm both, and the audit *strengthens* them (see §3, iter11 correction) |
| selectivity: union clean scene ≈ OFF | confirmed in every log where both arms ran (32–33 m, 0 interventions) |
| apparatus consistency | the same arm re-run across iterations 8/9/10 produces identical per-run scores — the stack is exactly reproducible |

## 3. Corrections (applied in place, with the evidence)

### 3.1 The pooled n=20 validation is statistically invalid (headline correction)

`audit_pooling.py`, section A: per-run scores of iteration 9 and iteration 10 are **identical in
every arm and scene**, and iteration 8's first six runs are identical to iteration 9's six. NeuroNCAP
seeds each episode by its run index (`engine.run(i)`), so `--runs 6` always replays the same six
episodes. The `union_validation` pooling treated these replays as independent replications:
**"n=20 per scene per arm" is really 8 unique episodes**, with runs 0–5 triple-counted.

Honest recompute on the 8 unique episodes (seed-paired bootstrap, same metric, same seed):

| | committed (invalid pooling) | corrected (unique episodes, n=8) |
|---|---|---|
| safe-progress OFF → union | 2.142 → 2.597 | 2.228 → 2.476 |
| delta | +0.455 | +0.247 |
| 95% CI | [+0.083, +0.793] | **[−0.272, +0.782]** |
| excludes zero | yes (claimed) | **no** |

The direction is unchanged, but at 8 unique episodes the pre-registered bar (CI excluding zero) is
**not met**. The claim "net-positive confirmed" is withdrawn and replaced by the honest fresh
measurement in §4. `union_validation/RESULT.md` carries the correction notice.

### 3.2 Side-impact: 100% → 12.5% unique, not 5% (and iteration 8's "8/8" was wrong)

The one union side-impact collision (run 6, impact 8.3 m/s) sits in iteration 8's runs-6/7 tail, so
duplication *diluted* it to "1 of 20" (5%). Unique episodes: **1 of 8 = 12.5%**. Iteration 8's
RESULT.md claimed "8/8 avoided" — its own log shows 7/8; the iteration-8 analysis ran while the last
runs were still finishing and only saw 4 complete run directories. Corrected in
`iter8_union/RESULT.md`. The §4 fresh run gives the definitive rate at n=20.

### 3.3 Iteration 11: the published numbers were a mid-run snapshot; complete data makes the null stronger

The published early-evade frontal cell (2.06 / 80%) was computed on 5 of 6 runs. The complete log
gives **1.71 / 83%**. The evade arm's side-scene runs, which finished after the snapshot, show
**5/6 collisions** — the early-evade design also *breaks the side case that the stop-based union had
solved* (the published table shows "(stop-routed)" for that cell). Both corrections make the
iteration-11 refutation stronger, and the published conclusion (evasion refuted; stop is the safe
response) stands. Corrected in `iter11_early_evade/RESULT.md`.

### 3.4 Framing corrections

- **"Ten pre-registered iterations"** (README): the campaign-level win bar is pre-registered
  (`PREREGISTRATION.md`, frozen before results), but per-iteration hypothesis documents exist for
  iterations 2, 4, and 11 only. Rephrased.
- **"The pre-registered bar" for safe-progress** (`union_validation/RESULT.md`): the frozen
  pre-registration's bar is the NCAP score / collision rate with a CI excluding zero (met by
  iteration 2). The safe-progress *metric* was introduced in iteration 3 and adopted as the bar in
  iteration 4's hypothesis — before iterations 8–10 ran, but not in the original freeze. Rephrased
  to say exactly that.
- **G1 "sharpens monotonically toward imminent"**: the three cited horizons (0.67 → 0.75 → 0.83) are
  monotone; the full five-point curve has one small inversion (h=4: 0.695 → h=3: 0.684). Noted.
- **`pooled_union_ci.py` read box-local paths** — the headline was not reproducible from the repo.
  The raw inputs are now committed (`verification/evidence/`) and `audit_pooling.py` reproduces every
  number in this document from them.

## 4. Fresh reproduction with honest statistics (n=20 unique episodes)

Executed on the GPU box during this pass: OFF vs union (exact iteration-8 configuration, the
committed `server_patch_union.py`, pristine planner repo) on stationary/frontal/side with
`--runs 20` — run indices 0–19, i.e. the 8 episodes every prior iteration used **plus 12 never-seen
episodes** — followed by the iteration-11 early-evade arm on the same 20 indices (null re-check).
Determinism makes indices 0–7 an exact-reproduction check; indices 8–19 are the honest expansion.

**RESULTS PENDING — run in flight at the time of this commit; this section is finalized in the
follow-up commit with the raw logs committed alongside.**

## 4b. The safety-engineering view (derived from committed decision logs)

AV safety cases are argued in interventions-per-distance, detection lead time, and severity — not
benchmark scores. `verification/analyze_safety_case.py` derives them from the committed evidence
(episodes are deterministic until intervention, so the OFF arm's ground-truth contact moment is the
counterfactual impact time for the union arm's first brake on the same run index; simulator actor
trajectories are used only for this offline timing, never by the monitor):

| quantity | value (iteration-8 union, unique episodes) |
|---|---|
| detection lead time before counterfactual contact | **median 2.5 s** (n=6 reconstructable, range 1.0–3.5 s) |
| benign-scene intervention budget | 11 brake frames over 242 m driven (2 of 8 episodes touched) |
| frontal severity | mean impact 13.9 → **6.7 m/s** (rate unchanged) |
| side outcome | 8/8 collisions → **1/8** |

## 5. Attacks attempted and their outcomes

| attack | outcome |
|---|---|
| "Is the baseline a weakened planner?" | No. OFF is the same frozen checkpoint, same episodes (determinism makes every comparison seed-paired); confirmed per-run in the logs. |
| "Is safe-progress gameable by freezing?" | No. Progress term multiplies the safety score; always-brake scores 0.49–0.64 in iters 3/4 — the metric punishes freezing. Capped ratio (min(1, ego/OFF-mean)) prevents overshoot credit. |
| "Is the side-impact win an artifact?" | The effect is real but the published rate was wrong: 7/8 + 6/6 + 6/6 identical replays → honest 12.5% at n=8; re-measured at n=20 in §4. |
| "Are the frontal nulls misinterpreted — is the stop really the ceiling?" | The three nulls reproduce from raw logs and get stronger with complete data (§3.3). Within the tested design space (invented maneuvers) the stop is the ceiling; the untested space (planner-native alternatives) is exactly the next phase. |
| "Is the iter11 'evasion crashes on false alarms' conclusion supported?" | Yes — raw decision logs + scores confirm 3/6 clean-scene collisions under evade, 0/6 under stop, on identical episodes. |
| "Do the iteration-to-iteration comparisons hold given determinism?" | Yes — determinism *strengthens* them: every arm faced exactly the same episodes, so per-iteration comparisons are paired, not sampled. What it breaks is only the *pooling across re-runs* (§3.1). |

## 6. Evidence completeness

Committed under `verification/evidence/`: the raw run logs for iterations 8–11 (`logs/`), the
per-frame monitor decision logs for every arm of iterations 8–11 (`jsonl/`, gzipped), and per-run
`ego_poses.json` + `metrics.json` archives (`runs/`). Earlier iterations' committed proofs
(`iter*/proof/`) were audited against these logs where they overlap. The v20 fresh-run evidence is
committed with the follow-up.

## 7. Certification

- **Certified (reproduces from committed evidence):** G1 signal (AUROC 0.83); iteration-2 safety win
  and its CI; selectivity of the union; the three evasion nulls (strengthened); apparatus
  reproducibility.
- **Corrected in place:** pooled n=20 validation (invalid → withdrawn; honest n=8 CI does not
  exclude zero); side-impact rate (5% → 12.5% unique at n=8); iteration-8 "8/8 avoided" (7/8);
  iteration-11 snapshot numbers (complete-data numbers published); framing items in §3.4.
- **Superseded by §4 (n=20 fresh measurement):** the definitive net-positive test and side/frontal
  rates.

The campaign's honest core — a selective, label-free monitor on a frozen planner that solves most of
the side-impact failure and mitigates the frontal one, with prevention refuted for invented
maneuvers — stands. Its statistical headline is re-established at n=20 in §4 or not at all.
