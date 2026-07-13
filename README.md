# Sentinel

**A runtime introspective safety monitor that watches a frozen self-driving planner, predicts the
collision it is about to cause, and intervenes — measured where it actually matters: in closed
loop, by whether the car crashes *and whether it can still drive*.**

> **Honest status up front (93 registered iterations: 62 completed mechanism iterations + an
> independent verification pass +
> the full official benchmark at power + a completed iteration-37 calibration null + an
> iteration-38 opposite-direction S0 canary pass + completed iteration-39/40/41 defensibility
> audits + a completed iteration-42 exact-trace replay-support pass + a completed iteration-43
> object-stream perturbation gate — a mild-fragile finding: the rule over-fires under 5 cm
> position jitter in replay — + a completed iteration-44 velocity temporal-smoothing repair
> gate — a no-repair null: every frozen smoothed estimator halves the over-firing but erases
> genuine interventions, so the fragility is not repaired by low-pass filtering the velocity —
> + a completed iteration-45 HUGSIM infrastructure gate: the second-benchmark transfer lane is
> open, with assets, environments, and a monitor-OFF closed-loop smoke passing on the same
> frozen checkpoint — + a completed iteration-46 HUGSIM Stage-1 monitor-OFF baseline, a
> completion null: 38 of 52 scheduled episodes completed with per-step logs, the D0 probe
> recorded the loop as stochastic, but the seven `load_HD_map` scenarios all failed on an
> unstaged nuScenes map-expansion pack, so the Stage-2 OFF-vs-union pre-registration is not
> authorized — + a completed iteration-47 map-staging + OFF-completion pass: Stage A staged
> the official nuScenes map-expansion pack v1.3 with provenance receipts, Stage B completed
> all 14 previously failed episodes on the first attempt, and the full 52-episode monitor-OFF
> arm now stands with carried-episode byte integrity and pairing feasible over all 26
> within-scenario pairs (median |dHD| 0.0251) — + a completed iteration-48 HUGSIM Stage-2
> transfer gate, THE transfer verdict of the second-benchmark line, a **transfer null**: all
> 104 OFF-vs-released-union episodes completed under the seven NeuroNCAP-frozen parameters
> with zero retuning, the monitor actively fired and braked (37/52 ON episodes, 26.9% of
> frames braking, 134 latch releases, no RC collapse), and the mean paired HD-Score delta is
> −0.017 with a 95% scenario-clustered CI [−0.055, +0.026] that includes zero — the NeuroNCAP
> benefit does not measurably transfer to HUGSIM easy+medium scenarios at this N, published at
> full weight as the measured external-validity boundary; no NeuroNCAP-equivalence or safety
> claim — + a completed iteration-49 hard/extreme-tier transfer gate, a collision-regime
> **transfer null**: all 104 hard/extreme OFF-vs-released-union episodes completed with zero
> retries and zero retuning, the monitor braked in 40/52 ON episodes (22.3% pooled brake
> frames, 58 releases, no RC collapse), and the mean paired HD-Score delta is −0.0089 with
> CI [−0.0438, +0.0203] that includes zero; 51/52 OFF episodes had collision opportunity,
> so iteration 50's frozen P1 resolves Branch B, REFUTED — the transfer failure is real, not
> opportunity-scarce — + a completed iteration-50 collision-opportunity audit: on NeuroNCAP
> the benefit concentrates
> exactly where the unmonitored planner collides (Spearman rho +0.70, CI [+0.39, +0.88]),
> while 40/52 HUGSIM OFF episodes carried a collision event — the transfer null is classified
> opportunity-present, not opportunity-scarce, and the classification does not upgrade it — +
> a completed iteration-51 HUGSIM transfer-failure taxonomy: across 104 paired HUGSIM transfer
> episodes the frozen rule converted only 6/91 OFF-opportunity pairs, with 85/104 pairs still
> collision-persistent; the combined taxonomy is mixed, not a single-cause failure, so the next
> honest move is mechanism-cause audit rather than retuning — + a completed iteration-52
> ON-collision timing audit: among 92 ON-collision episodes, 57 were absent/post-collision
> braking and 35 had pre-collision braking; all 22 no-brake cases had zero frozen TTC/CPA
> surface-proxy rows, but 26 long-lead brake cases still collided, so a pure brake-earlier
> repair story is insufficient — + a completed iteration-53 first-fire channel audit: across
> the same 92 ON-collision episodes, first-fire channels split as 36 TTC-only, 33 CPA-only,
> 22 no-fire, and 1 both; the 35 pre-collision-fire collisions split 19 CPA-only / 16
> TTC-only, so the HUGSIM failure is not one bad union branch — + a completed iteration-54
> provenance support audit: monitor-side first-fire object/path argmins reconstruct cleanly
> (40 unique TTC objects, 36 unique CPA objects, 1 both-distinct case, 27 no-fire), but HUGSIM
> collision actor identity is not logged in any of the 104 committed evals, so actor-match claims
> require new instrumentation — + a completed iteration-55 HUGSIM source-map audit: the frozen
> HUGSIM checkout at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e` was verified, source-only scan
> mapped instrumentation candidates to `sim/utils/score_calculator.py` and `closed_loop.py`, and
> returned `COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE`; a future no-metric-change
> instrumentation patch is designable, but not implemented or run — + a completed iteration-56
> HUGSIM provenance patch-design null: the first patch draft applied and compiled, but the frozen
> static guard rejected the added `if score_nc == 0.0:` branch as metric/control-sensitive, so no
> instrumentation patch or run is authorized — + a completed iteration-57 guard-refinement pass:
> the byte-identical patch SHA passed a refined static verifier that rejects metric/control
> assignments while allowing read-only score comparisons; still no HUGSIM run or actor-match
> claim — + a completed iteration-58 HUGSIM provenance instrumented canary:
> the byte-bound patch executed on the frozen HUGSIM stack for the registered
> `scene-0013-hard-00` OFF/ON schedule, emitted top-level `collision_provenance` in both
> `eval.json` files (counts 11 and 13) while scalar metrics and scalar-only `details` rows
> stayed intact, and returned `PROVENANCE_CANARY_COMPLETE`; this retires the instrumentation
> execution blocker only, with no actor-match, HD-Score-invariance, safety, transfer,
> deployment, benchmark, or retuning claim — + a completed iteration-59 HUGSIM actor-match
> support audit: exactly eight registered Sentinel-ON HUGSIM episodes completed, same-run
> comparison support existed for three foreground rows, and all three classifiable rows were
> `actor_mismatch` by the frozen bridge (distances 15.43 m, 21.99 m, 37.04 m); the other five
> rows were no-fire, post-collision-fire, or background-only, so this is a bounded mechanism
> audit only, not a population, repair, safety, transfer, deployment, benchmark, or retuning
> claim — + a completed iteration-60 actor-match bridge sensitivity audit: over the three
> iteration-59 classifiable rows, 48 frozen bridge variants produced no
> `bridge_match_possible`, but one row fell into `bridge_ambiguous_possible` at 5.66 m, so
> the verdict is `BRIDGE_AMBIGUOUS_NULL`; no robust all-row mismatch, actor-causality, repair,
> safety, transfer, deployment, benchmark, or retuning
> claim — + a completed iteration-61 monitor object-surface audit: over the same three rows,
> all first-fire monitor objects were compared to all eligible foreground provenance rows under
> the frozen bridge grid; one row (`ttc_extreme_b`) had a non-triggering first-fire object
> (`object_id=16`) match at 2.07 m while the trigger object stayed ambiguous, and the other two
> rows had no first-fire object support; no actor-causality, repair, safety, transfer,
> deployment, benchmark, population, or retuning
> claim — + a completed iteration-62 non-trigger ranking audit: the matched non-trigger object
> in `ttc_extreme_b` was visible but subthreshold at first fire (`min_cpa=22.76 m`, CPA rank
> 9/9, no valid TTC), while the trigger was TTC-only on `object_id=1`; no repair, actor-causality,
> safety, transfer, deployment, benchmark, population, or retuning
> claim — + a completed iteration-63 temporal emergence audit: the same `object_id=16` was
> present in 13 pre-contact monitor frames before the `7.25 s` foreground collision timestamp
> and never crossed even the registered borderline band (minimum CPA 12.17 m, no valid TTC),
> so late hazard emergence is not the explanation for that row; no repair, actor-causality,
> safety, transfer, deployment, benchmark, population, or retuning
> claim — + a completed iteration-64 unsupported-row temporal surface audit: the two rows that
> lacked first-fire object support both gained pre-contact object-surface matches when all
> pre-contact decision objects were considered (`ttc_extreme_short` best 1.67 m, `cpa_medium_b`
> best 0.43 m), so the gap is first-fire/provenance timing rather than total pre-contact object
> absence; no repair, actor-causality, safety, transfer, deployment, benchmark, population, or
> retuning
> claim — + a completed iteration-65 temporal alignment audit: those two matched pre-contact
> objects were present but subthreshold at their matched timestamps (`object_id=2`: min CPA
> 12.72 m, TTC 3.58 s; `object_id=6`: min CPA 9.32 m, no valid TTC), so the gap is not total
> object absence and not an already-active matched hazard; no repair, actor-causality, safety,
> transfer, deployment, benchmark, population, or
> retuning
> claim — + a completed iteration-66 matched-object hazard timeline audit: across the two
> iteration-65 targets, `ttc_extreme_short` `object_id=2` becomes a TTC hazard exactly at first
> fire after two borderline frames, while `cpa_medium_b` `object_id=6` stays visible-never-active
> before foreground collision; no repair, actor-causality, safety, transfer, deployment,
> benchmark, population, or
> retuning
> claim — + a completed iteration-67 trigger-target bridge audit: one row is same-object
> target/trigger, while `cpa_medium_b` is split-object; across the full pre-contact window both
> the target and trigger can bridge to foreground, but the first-fire trigger object has no bridge
> support at the actual first-fire timestamp; no repair, actor-causality, safety, transfer,
> deployment, benchmark, population, or
> retuning
> claim — + a completed iteration-68 fire-time bridge decomposition audit: the fire-time bridge
> gap splits temporally, with `ttc_extreme_short` best trigger support `1.25 s` before first fire
> and `cpa_medium_b` best trigger support `2.00 s` after first fire; no repair, actor-causality,
> safety, transfer, deployment, benchmark, population, or
> retuning
> claim — + a completed iteration-69 HUGSIM mechanism taxonomy synthesis: all eight iteration-59
> rows are classified, with five structural labels preserved and all three classifiable foreground
> rows refined into `nontrigger_visible_never_hazard`,
> `same_object_late_fire_after_best_bridge`, and
> `split_object_visible_never_active_fire_before_best_bridge`; no repair, actor-causality,
> safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-70 HUGSIM structural-row timing audit: the five structural
> rows split into two foreground-present surface-silent rows, two foreground-present late-fire
> rows where first fire occurs `1.75 s` after first foreground contact, and one foreground-absent
> background-only row; no repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, or
> retuning
> claim — + a completed iteration-71 HUGSIM surface-silent margin audit: both foreground-present
> no-fire rows are far from the frozen trigger surfaces before foreground contact (`mixed_extreme`
> closest CPA margin `+2.606 m`; `nofire_hard_control` closest valid TTC margin `+3.456 s` and
> CPA margin `+6.478 m`); no threshold-value, repair, actor-causality, safety, transfer,
> deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-72 HUGSIM late-fire prefire margin audit: both late-fire rows
> are near a frozen trigger surface before foreground contact (`both_distinct_extreme` CPA margin
> `+0.5355 m`; `ttc_medium_a` TTC margin `+0.7742 s`) but first fire still occurs `+1.75 s`
> after first foreground contact; no threshold-value, repair, actor-causality, safety, transfer,
> deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-73 HUGSIM structural margin-transition audit: the four
> foreground-present structural rows split exactly into two silent rows with no active crossing
> anywhere and two late-fire rows that are near before contact but first active only `+1.75 s`
> after contact; no threshold-value, repair, actor-causality, safety, transfer, deployment,
> benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-74 HUGSIM late-fire delay-barrier audit: both late-fire rows
> are cross-channel delay cases — `both_distinct_extreme` is CPA-near before contact but
> TTC-active after contact, while `ttc_medium_a` is TTC-near before contact but CPA-active after
> contact; no threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, or
> retuning
> claim — + a completed iteration-75 HUGSIM cross-channel object-handoff audit: both fixed
> cross-channel late-fire rows are object switches, not same-object channel flips
> (`both_distinct_extreme` object `5` -> `9`; `ttc_medium_a` object `6` -> `24`); no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark, population,
> commercial-value, or
> retuning
> claim — + a completed iteration-76 HUGSIM switch foreground-bridge audit: neither the pre-near
> object nor the post-active object reaches the frozen foreground bridge match or ambiguous band
> in either fixed row (`8.12–13.45 m` best distances); no threshold-value, repair,
> actor-causality, safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-77 HUGSIM event object-set foreground-bridge audit: full
> event-row object sets recover bounded foreground support in mixed form (`both_distinct_extreme`
> pre-set ambiguous via object `9`; `ttc_medium_a` pre/active sets match via object `10`), while
> still not upgrading to actor-causality or repair; no threshold-value, repair, actor-causality,
> safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-78 HUGSIM support-object ranking audit: all three
> foreground-supported full-set objects are nonselected and subthreshold under the logged
> CPA/TTC surface
> (`9` vs selected `5`, `10` vs selected `6`, `10` vs selected `24`; min CPA
> `21.63/17.28/13.56 m`, no finite TTC), so the support-object lead is not an already-active or
> borderline hazard lost at final selection; no threshold-value, repair, actor-causality, safety,
> transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-79 HUGSIM selected-object surface decomposition audit:
> selected objects are not arbitrary far objects in the same rows — two selected objects are
> borderline (`object_id=5` CPA `2.0355 m`; `object_id=6` TTC `3.2742 s`) and one is active
> (`object_id=24` CPA `1.2791 m`), while the foreground-supported objects remain subthreshold;
> no threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, or
> retuning
> claim — + a completed iteration-80 HUGSIM selected-object all-provenance bridge audit:
> all eligible logged provenance rows in the fixed episodes are foreground (`30/30`), and the
> selected active/borderline objects still reach no match or ambiguous bridge support
> (`13.4483/8.1239/8.4408 m` best distances); no threshold-value, repair, actor-causality,
> safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-81 HUGSIM support-object temporal surface audit:
> the two fixed foreground-supported full-set objects split temporally; object `9` in
> `both_distinct_extreme` later becomes borderline at `5.5 s` and active at `7.0 s` after first
> foreground support at `5.25 s`, while object `10` in `ttc_medium_a` stays visible across
> `15` frames and never becomes active or borderline; no threshold-value, repair, actor-causality,
> safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-82 HUGSIM support-object surface/provenance co-occurrence
> audit: both fixed support objects have same-object foreground bridge support, but co-occurrence
> with the released surface is only borderline for object `9` (`5.5 s`, best surface bridge
> `0.9876 m`, zero active+bridge frames), while object `10` has bridge support in all `15`
> present frames and never reaches active or borderline surface; no threshold-value, repair,
> actor-causality, safety, transfer, deployment, benchmark, population, commercial-value, or
> retuning
> claim — + a completed iteration-83 HUGSIM bridge-supported surface-miss decomposition:
> across `18` bridge-supported support-object frames there are zero active frames; object `9`
> is a TTC-borderline-only miss (`1` borderline frame, closest active TTC margin `+2.2761 s`,
> closest active CPA margin `+17.6718 m`), while object `10` has `15` bridge-supported
> subthreshold frames with no finite TTC and closest active CPA margin `+5.7464 m`; no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, or
> retuning
> claim — + a completed iteration-84 HUGSIM selected/support path-arbitration decomposition:
> all three fixed rows classify `selected_surface_support_bridge_split`; the selected object
> has lower CPA and better CPA rank in all three rows, selected bridge support in `0/3` rows,
> while the support object has better foreground/provenance bridge support in `3/3` rows; no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, real-world, first-responder, or
> retuning
> claim — + a completed iteration-90 HUGSIM active-surface provenance gap audit:
> at the fixed replay rows, bridge support lands on `11` non-active objects while the one active
> object has no bridge support, returning `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`; no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, real-world, first-responder, or
> retuning
> claim — + a completed iteration-91 HUGSIM active-gap geometry decomposition:
> the split is path-vs-provenance geometry on the fixed rows: the active object is path-near but
> provenance-far (`10.9518 m`, `no_support`), while bridge-supported objects are non-active; no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark,
> population, commercial-value, real-world, first-responder, or
> retuning
> claim — + a completed iteration-92 HUGSIM path-proximity arbitration audit:
> CPA/path-best and provenance-best objects differ in all three fixed rows (`0/3` same-object
> events); the active row's path/surface-best object is active but no-support while
> provenance-best is subthreshold; no threshold-value, repair, actor-causality, safety, transfer,
> deployment, benchmark, population, commercial-value, real-world, first-responder, or
> retuning
> claim — + a completed iteration-93 HUGSIM surface-winner alignment audit:
> surface-best alignment is mixed (`2/3` path, `1/3` provenance), with the active failure row
> following path and no-support object `24`; no threshold-value, repair, actor-causality, safety,
> transfer, deployment, benchmark, population, commercial-value, real-world, first-responder, or
> retuning
> claim — + a completed iteration-94 HUGSIM active-row surface margin arbitration:
> the active `ttc_medium_a` row has exactly one active/path/surface candidate, object `24`, with
> active CPA margin `-0.4990 m`; all three bridge-supported candidates are subthreshold, TTC-null,
> and CPA-far, with the nearest bridge-supported active CPA margin `+10.6434 m`; no
> threshold-value, repair, actor-causality, safety, transfer, deployment, benchmark, population,
> commercial-value, real-world, first-responder, or
> retuning
> claim):**
> the introspective signal predicts the planner's collisions (AUROC 0.83). On the
> complete 14-scene NeuroNCAP set at **20 seed-paired runs per pair** (799 episodes, the power
> measurement), the unmonitored UniAD baseline **independently reproduces** (pooled 2.12 vs the
> published 1.84 — corroborated by DMAD's independent rerun at 2.11), and the best configuration — the
> **released union** (iteration 8's two-detector union + iteration 15's threat-cleared latch
> release) — lifts the benchmark score to **2.91 (+0.783, 95% CI [+0.605, +0.928])**, with run
> indices 0–5 of every pair reproducing the earlier 6-run measurement exactly. Stated with equal
> weight: on this repository's own deployment metric (safety × progress) the effect vs the
> unmonitored planner is a **tight null (−0.03, 95% CI [−0.13, +0.07])** — the benchmark safety
> gain costs approximately nothing in deployment terms, and iteration 16 showed the residual
> cannot be bought back by softening the stop: a calibrated 2 m/s crawl recovers progress but
> surrenders the stop's **position guarantee** (side collisions past the pre-registered
> falsifier bar) — that null is published and the stop stands. The statistics here earned their precision the hard way: an
> independent verification pass ([`experiments/VERIFICATION.md`](experiments/VERIFICATION.md))
> **withdrew** an earlier headline — the original pooling had counted NeuroNCAP's deterministic
> per-index episodes as independent replications — and the claim was re-established on 20
> genuinely-unique episodes (+0.398, CI [+0.133, +0.665] at mini-scene scope), with run indices
> 0–7 doubling as an exact-reproduction check of the whole apparatus. Three evasive designs to
> *prevent* the head-on were honestly **refuted** — the last showing *why*: a swerve on a false
> alarm crashes. Over-claims here get caught by our own audits and corrected in place — that
> self-correction is the point. Full arc in
> [Status](#status--where-it-really-stands-the-honest-current-truth).

The field's open-loop driving metrics are saturated and gameable (an ego-state MLP "wins" nuScenes
L2). The honest axis is **closed-loop safety**. The end-to-end planner families this campaign
builds on score **1.84 (UniAD) / 2.75 (VAD) out of 5** on NeuroNCAP and collide in 87.8–99.6% of
safety-critical scenarios; retrained planners reach ~3.06 (BridgeAD, CVPR 2025, same protocol) —
every published gain above the baselines changes the planner. Sentinel attacks the unoccupied
slot: a small, plug-and-play monitor on a *frozen* planner — no fleet, no retraining the planner,
single-digit GPUs.

> Built on what we already proved. In a prior study ([PerceptionProof](https://github.com/manfromnowhere143/perceptionproof))
> a cheap label-free signal predicted the **collision gate at AUROC ~0.8**. Sentinel takes that
> introspective signal **closed-loop, with intervention, to prevent the crash** — the natural
> sequel: *we showed cheap signals see failure coming; now we use them to stop it.*

---

## The result

Ninety-three registered iterations — sixty-two completed mechanism iterations, plus the completed defensibility, robustness, and transfer gates of iterations 39-93 — under frozen pre-registrations converge on one closed-loop configuration — the
**released union** (two label-free geometric detectors + a threat-cleared latch release) —
measured on the **complete official 14-scene NeuroNCAP set at 20 seed-paired runs per pair**
(799 episodes; hypotheses frozen before the run; the first 6 indices of every pair reproduce the
earlier 6-run measurement exactly):

| pooled, all 14 official scenes (n=20/pair) | unmonitored UniAD | Sentinel (released union) |
|---|---:|---:|
| **NeuroNCAP score (0–5, the benchmark's metric)** | 2.12 *(published: 1.84 — reproduced)* | **2.91** |
| side-impact collision rate | 74% | **44%** |
| stationary collision rate | 29% | **18%** |
| frontal head-on | 1.24 / 78% | 1.78 / 90% (impact mitigated, not prevented) |
| safe-progress (safety × route progress) | 2.40 | 2.36 (−0.03, CI [−0.13, +0.07]) |

> **Benchmark score +0.783, 95% CI [+0.605, +0.928] — excludes zero at 3.3× the original
> power** — with the release mechanism strictly dominating the plain union (identical safety on
> every cell, safe-progress +0.246, CI [+0.206, +0.293] at n=6). The honest limits, named
> precisely: the frontal head-on is *mitigated*, not *prevented* (three evasive designs to
> prevent it were tested and refuted, §Status; the frontal/0346 regression is confirmed real at
> n=20); and the deployment-metric effect vs the unmonitored planner is a **tight null**
> (−0.03, CI [−0.13, +0.07]) — the safety gain costs approximately nothing on the deployment
> metric, and iteration 16 established the residual is not recoverable by softening the stop.
> The benefit is NeuroNCAP-measured: on a second closed-loop benchmark (HUGSIM, 26 easy+medium
> scenarios, iteration 48) the frozen rule fires and brakes but the paired HD-Score effect is
> a **transfer null** (−0.017, CI [−0.055, +0.026]) — the measured external-validity boundary.

The verification pass's fresh mini-scene measurement stands as measured there: at **20
genuinely-unique episodes per scene** the union is net-positive on safe-progress **+0.398, 95% CI
[+0.133, +0.665]** — a claim that was first **withdrawn** by our own audit (the original pooling
had counted deterministic episode replays as independent —
[`experiments/VERIFICATION.md`](experiments/VERIFICATION.md)) and re-established on fresh data,
with run indices 0–7 doubling as an exact reproduction of the original iteration-8 data.

In the units an AV safety case is written in (derived from the committed per-frame decision logs
and ground-truth timing — [`analyze_safety_case.py`](experiments/verification/analyze_safety_case.py)):
at full14/power scale (iteration 40) the monitor's reconstructable lead time is a median
**1.30 s** (p05/p95 0.40/3.50 s) over 61 measured episodes, at 111.68 brake frames/km across
10.79 km; on the mini-scene verification set it fires a median **2.5 s** before counterfactual
contact and cuts frontal mean impact speed from **13.9 to 6.7 m/s**.

The campaign in one picture — every step measured closed-loop against the same unmonitored planner,
nulls kept, one headline withdrawn by our own audit and re-established on independent data:

```mermaid
flowchart LR
  G1["the signal<br/><b>AUROC 0.83</b>"] --> I2["iter 2 · TTC brake<br/>collision 65 to 13%"]
  I2 --> I3["iter 3<br/><b>over-brakes</b><br/>honest setback"]
  I3 --> I45["iters 4-5<br/>selective gating<br/>side-blind"]
  I45 --> I67["iters 6-7 · CPA<br/>catches the T-bone"]
  I67 --> U["iter 8 · THE UNION<br/><b>selective + side<br/>+ net-positive</b>"]
  U --> E9["iters 9-11<br/>three evasions<br/><b>all refuted</b>"]
  U --> V["verification pass<br/>claim withdrawn, re-measured:<br/><b>+0.398 [+0.133, +0.665]</b>"]
  classDef win fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef bad fill:#fdebec,stroke:#c62828,color:#3b1213;
  classDef audit fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  class G1,I2,U win;
  class I3,I45,I67,E9 bad;
  class V audit;
```

Act two — from a validated method to the benchmark, at power, with the mechanism space mapped:

```mermaid
flowchart LR
  N12["iters 12-14<br/>no plan B, two planners ·<br/>RSS: safety by paralysis ·<br/>selectivity not portable"] --> F14["full benchmark, n=6<br/>baseline reproduced<br/><b>2.15 to 3.09</b>"]
  F14 --> R15["iter 15 · latch release<br/><b>best configuration</b>"]
  R15 --> X16["iter 16 · crawl refuted<br/><b>the stop is a<br/>position guarantee</b>"]
  R15 --> P20["power run · n=20/pair<br/><b>2.12 to 2.91, CI excl. 0</b><br/>deployment: tight null"]
  P20 --> X17["iter 17 · routing refuted —<br/><b>deployment flip proven<br/>achievable</b>"]
  X17 --> X18["iter 18 · tracker offline gate<br/><b>12/13 — GPU stays off</b>"]
  X18 --> H19["iter 19 · diversity head<br/><b>gate refused: 0/37</b> —<br/>collapse is in the<br/>representation"]
  H19 --> H21["iter 21 · BEV head<br/><b>gate refused: 0/37</b><br/>validity 23%"]
  classDef win fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef bad fill:#fdebec,stroke:#c62828,color:#3b1213;
  class F14,R15,P20 win;
  class N12,X16,X17,X18 bad;
  class H19,H21 bad;
```

Act three — causal localization is now gated first on artifact validity:

```mermaid
flowchart LR
  H21["21 BEV null"] --> Q["causal<br/>localization?"]
  Q --> F22["22 join fail"]
  F22 --> S23["23 count null"]
  S23 --> A24["24 0 scenes"]
  A24 --> I25["25 inventory null"]
  I25 --> R26["26 blobs/disk"]
  R26 --> D27["27 1 TB disk"]
  D27 --> S28["28 trainval<br/>532 scenes"]
  S28 --> A29["29 support pass"]
  A29 --> L30["30 localization pass"]
  L30 --> I31["31 S0 fail"]
  I31 --> P32["32 prefix pass"]
  P32 --> C33["33 cal null"]
  C33 --> A34["34 scale null"]
  A34 --> H35["35 no stratum"]
  H35 --> S36["36 <b>track_query</b> site"]
  S36 --> T37["37 track_query<br/>calibration null"]
  T37 --> O38["38 opposite sign<br/>pre-reg only"]
  classDef bad fill:#fee,stroke:#c00,color:#111;
  classDef ask fill:#ffe,stroke:#a70,color:#111;
  classDef data fill:#eef,stroke:#06c,color:#111;
  classDef win fill:#efe,stroke:#080,color:#111;
  class H21,F22,S23,A24,I25,R26,I31,C33,A34,H35,T37 bad;
  class Q,O38 ask;
  class D27,S28 data;
  class A29,L30,P32,S36 win;
```

And the defensibility arc that follows:

```mermaid
flowchart LR
  O38["38"] --> A39["39"]
  A39 --> A40["40"]
  A40 --> A41["41"]
  A41 --> A42["42"]
  A42 --> A43["43"]
  A43 --> A44["44"]
  A44 --> A45["45"]
  A45 --> A46["46"]
  A46 --> A47["47"]
  A47 --> A48["48"]
  A48 --> A49["49"]
  A49 --> A50["50"]
  A50 --> A51["51"]
  A51 --> A52["52"]
  A52 --> A53["53"]
  A53 --> A54["54"]
  A54 --> A55["55"]
  A55 --> A56["56"]
  A56 --> A57["57"]
  A57 --> A58["58"]
  A58 --> A59["59"]
  A59 --> A60["60"]
  A60 --> A61["61"]
  A61 --> A62["62"]
  A62 --> A63["63"]
  A63 --> A64["64"]
  A64 --> A65["65"]
  A65 --> A66["66"]
  A66 --> A67["67"]
  A67 --> A68["68"]
  A68 --> A69["69"]
  A69 --> A70["70"]
  A70 --> A71["71"]
  A71 --> A72["72"]
  A72 --> A73["73"]
  A73 --> A74["74"]
  A74 --> A75["75"]
  A75 --> A76["76"]
  A76 --> A77["77"]
```

The winning monitor is a **union of two individually-selective detectors**, chosen because the two
failure modes are physically distinct — a side T-bone is a real path crossing, while a head-on is
hidden by the planner's own optimism:

The planner's own `/infer` outputs — plan, detected objects, scores, persistent track IDs,
forecasts, ego pose — are the monitor's only inputs; nothing privileged. Object velocity is
*observed* (ego-motion-compensated tracking by ID across frames), not the planner's optimistic
forecast. The stop is latched — safe even when the trigger is wrong — and, since iteration 15,
releases after four consecutive verified-clear frames, returning control to the planner. Every
frame's decision is written to a committed receipt log.

```mermaid
flowchart LR
  P["frozen planner<br/>UniAD, weights locked"] -- "plan + objects +<br/>forecasts + track IDs" --> A
  A["world-frame tracks by ID<br/>= observed velocity"] --> C{"plan vs tracked path<br/>closest approach under 1.5 m?<br/><i>the side T-bone</i>"}
  A --> T{"observed closing TTC<br/>under 2.5 s?<br/><i>the hidden head-on</i>"}
  C -- fires --> B["latched stop<br/>releases when clear"]
  T -- fires --> B
  C -- neither --> E["planner's plan<br/>unchanged"]
  B --> S["NeuroNCAP closed loop"]
  E --> S
  S --> R[/"score 0-5 · collision % ·<br/>impact speed · progress"/]
  classDef mon fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  classDef act fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef base fill:#f6f8fa,stroke:#57606a,color:#1f2328;
  class A,C,T mon;
  class B,E act;
  class P,S,R base;
```

Neither detector fires on a benign passing object, so the union inherits both terms' selectivity; each
term catches the danger case the other is blind to. Full derivation — and the honest nulls along the
way — in the score tracker and [Status](#status--where-it-really-stands-the-honest-current-truth).

---

## The number we are chasing (pre-registered)

Primary benchmark: **NeuroNCAP** (public, NeRF/NeuRAD closed-loop on nuScenes). Metric: NeuroNCAP
**safety score (0–5, ↑)** and **collision rate (%, ↓)**. The win bar is frozen in
[`PREREGISTRATION.md`](PREREGISTRATION.md): a Sentinel-monitored frozen planner must beat **the same
unmonitored planner** (and a RiskMonitor-style baseline) with a bootstrap CI excluding zero.

**Status: the primary bar is met at full scale** — on all 14 official scenes at 20 seed-paired
runs per pair, +0.783 with 95% CI [+0.605, +0.928] against the same unmonitored planner. The
baseline-comparison arm is covered by the ablations (iteration 2: naive proximity and
always-brake controls) and the formal-envelope baseline (iteration 13) on identical inputs.

### Score tracker (honest trajectory — updated every iteration)

Read the empty metric cells literally, not as missing work. In the score and collision columns,
`—` means the pre-registered iteration did not run a closed-loop benchmark arm or that the relevant
metric was not defined for that gate. Signal studies, offline gates, extraction/data gates, and
infrastructure gates report their frozen gate metric in the nearest applicable column instead.
Phrases such as "stopped before probes/interventions" mean the registered gate refused the next
step; they are intentional stops, not hidden probe failures or unreported GPU runs.

| iter | what we changed | NeuroNCAP score ↑ | collision % ↓ | vs baseline | insight |
|---|---|---|---|---|---|
| 0 | published baseline (target) | UniAD 1.84 · VAD 2.75 | 87.8–99.6 | — | the gap we attack |
| 1a | **stack stood up** — full closed loop on 1 L4, frozen UniAD in the loop, real metric out (smoke: scene-0103 stationary, 2 runs → 5.0/5.0, no collision) | — | — | infra gate **cleared** | the binding constraint was the apparatus, not the idea — [8 blockers cleared](experiments/iter1_reproduce/PROOF_smoke_0103.md) |
| 1b | **partial baseline + collision corpus** — every public-mini scene, frozen UniAD, 60 closed-loop episodes (frontal/0103, side/0103, stationary/0103, stationary/0796 × 15) | frontal/0103 **1.07** · side/0103 0.51 · stat/0103 5.00 · stat/0796 1.03 | 80 · 100 · 0 · 80 % | frontal **1.07 vs pub 1.17** (matches) | crashes coincide with the planner's own perception collapsing at 5–15 m — the signal iter 2 monitors. [`PARTIAL_BASELINE.md`](experiments/iter1b_partial_baseline/PARTIAL_BASELINE.md) |
| 2·G1 | **monitor signal validated** — frozen planner's own forecasts foresee its crashes (shadow replay, 40 episodes, 26/14) | — | — | **AUROC 0.83** (label-free) | imminent (≤0.5 s) predicted gap is the signal; sharpens toward imminent (0.67→0.75→0.83 at the cited horizons, one small inversion mid-curve); simplest term wins. [`G1_RESULT.md`](experiments/iter2_monitor/G1_RESULT.md) |
| 2 | **monitor + TTC brake, frozen planner** — A/B on the corpus | **1.92 → 4.67** | **65% → 13%** | **H1 met** (safety), CI [+2.21,+3.22] | TTC trigger + committed stop; side collisions 100%→0% — *but see iter 3*. [`iter2_monitor`](experiments/iter2_monitor/RESULT.md) |
| 2·abl | **ablation** — naive-proximity / always-brake controls | — | prox 83 · always 50 · TTC 40 (frontal) | introspective signal **essential** | naive distance brake ≈ useless on fast approaches; closing-speed-from-forecast does the work. [`ABLATION.md`](experiments/iter2_monitor/ABLATION.md) |
| 3 | **deployment metric (safe-progress)** — does it avoid the crash AND drive? | OFF **2.08** · always 0.49 · TTC 0.58 (safe-prog) | progress: OFF 0.91 · TTC 0.13 | **monitor over-brakes** | honest setback: TTC freezes benign scenes, *not* selective; unmonitored wins safe-progress. Next: introspective gating. [`iter3_progress`](experiments/iter3_progress/RESULT.md) |
| 4 | **gate on the *agent's* closing speed** — brake only on active threats | gated **2.80** · OFF 2.08 · TTC-old 0.64 (safe-prog) | clean-scene progress restored to OFF (0 brakes) | **net-positive vs OFF** (partial) | selectivity SOLVED; but gate under-brakes real threats (optimistic-forecast velocity) → danger safety lost. Next: track true agent velocity. [`iter4_gated`](experiments/iter4_gated/RESULT.md) |
| 5 | **observed-velocity gating** — agent velocity from multi-frame tracking, not the forecast | tracked **2.35** · OFF 2.08 (safe-prog) | clean=OFF (0 brakes); frontal coll 83%→**67%** | net-positive; **frontal recovered** | selectivity holds + observed velocity beats the forecast on frontal — but **side-impact still 100%** (its warning is in the ego's motion the gate filters out). Next: plan-vs-tracked-path collision check. [`iter5_tracked`](experiments/iter5_tracked/RESULT.md) |
| 6 | **plan-vs-tracked-path CPA** — brake if the ego's planned path crosses an agent's tracked path | cpa 2.17 · OFF 2.32 (safe-prog) | **side-impact 100% → 0%** (8/8 avoided) | **side case SOLVED** (but over-brakes) | the T-bone that beat iters 4–5 is caught geometrically; cost = 2.5 m margin also flags benign close passes → clean 33→22 m. Next: tighter margin (~1.2 m) to keep the side win + restore selectivity. [`iter6_cpa`](experiments/iter6_cpa/RESULT.md) |
| 7 | **margin sweep** — CPA at 1.5 m vs 1.0 m vs OFF | cpa@1.5 selective (clean 32.3 = OFF) | side **0%** kept; frontal reverts to **100%** | **3 of 4 at once** | tighter margin restores selectivity + keeps the side win, but frontal defeats plan-CPA at *any* tight margin (optimistic plan clears by 3–4 m). No single margin holds all four → **union two detectors**. [`iter7_margin`](experiments/iter7_margin/RESULT.md) |
| 8 | **the union** — brake if (plan-vs-path CPA < 1.5 m) OR (observed agent-closing TTC < 2.5 s) | union **2.53** · OFF 2.32 (safe-prog) | clean 30.2≈OFF · **side 100→12.5%** (7/8, verification-corrected) · frontal score 1.31→**2.43** | **selective + side-solving + directionally net-positive, at once** | first config to hold 3 of 4 simultaneously; frontal impact strongly *mitigated* (not rate-reduced). Open ceiling: preventing (not softening) frontal head-on — planner optimism + stopping distance. [`iter8_union`](experiments/iter8_union/RESULT.md) |
| 9 | **evasive steering (AES) for frontal** — threat-aware: side→stop, head-on→swerve | — | frontal evade **1.66/100%** vs union stop **2.53/83%** | **refuted (null)** | naive 4 m swerve can't clear the actor and, keeping speed, hits harder than stopping. Selectivity + side preserved. Committed stop stays best; frontal *prevention* remains open. [`iter9_evade`](experiments/iter9_evade/RESULT.md) |
| 10 | **braking evasion into a tracked-clear gap** — shed speed *and* steer to the open side | — | frontal brakevade **1.67/100%** vs union stop **2.53/83%** | **refuted (null)** | second evasion family, same result: steering (even while braking) is worse than the pure stop. Two designs converge → committed stop is the frontal *ceiling*; prevention needs more than a single maneuver. [`iter10_brakevade`](experiments/iter10_brakevade/RESULT.md) |
| ✓ | **statistical validation** — pool the union & OFF arms across iters 8/9/10, bootstrap the safe-progress delta | union 2.60 vs OFF 2.14 (pooled) | side "5%" (pooled) | *claimed* net-positive | **WITHDRAWN by the verification pass**: the three "replications" are deterministic replays of the same episodes (n=20 was really n=8 unique); honest CI [−0.27, +0.78] does not exclude 0. [`union_validation`](experiments/union_validation/RESULT.md) |
| 11 | **early collision-course detection + evasion** — 4 s kinematic closest-approach, then time-gated lane change | — | frontal evade **83%** (= stop 83%); clean **50% crash**; side evade 83% | **refuted (null)** | third evasion refuted, and complete-data audit made it stronger: early detection neither prevents the head-on nor stays selective; evasion on a false alarm *crashes the clean scene 50%* and un-solves the side case (83%). A stop is safe when wrong, a swerve is not. Frontal-prevention line closed. [`iter11_early_evade`](experiments/iter11_early_evade/RESULT.md) |
| ✚ | **independent verification pass** — re-derive every claim from raw evidence; attack the statistics; re-run fresh at 20 unique episodes | union **2.22** vs OFF 1.83 (n=20 unique) | side 100→**30%** · clean identical to OFF | **net-positive RE-ESTABLISHED**: delta **+0.398, 95% CI [+0.133, +0.665]** | determinism found (episodes replay per run index) → pooled claim withdrawn, then re-measured on 20 genuinely-unique episodes: CI excludes zero; runs 0-7 reproduce iteration 8 exactly (apparatus check); iter11 evasion null re-confirms (worse than stop, degrades the clean scene). Raw evidence committed. [`VERIFICATION.md`](experiments/VERIFICATION.md) |
| 12 | **introspective plan selection, checkpoint** — log UniAD's 3 command-conditioned candidate plans per frame; does a safe alternative exist when the executed plan is dangerous? | — | escape candidates **0/37 dangerous frames** (bar: >30%) | **null — pre-condition fails** | the mechanism works (candidates diverge up to 14 m in benign frames) but **collapse under threat** (mean gaps 2.85/2.88/2.84 m): the command is routing, not hazard response. Introspection sees the danger; UniAD holds no safer intention to defer to. Pivot (pre-registered): VAD's native `ego_fut_mode=3`. [`iter12_plan_selection`](experiments/iter12_plan_selection/RESULT.md) |
| 13 | **formal-envelope baseline (RSS-style)** — same tracking, same actuator, physics rule instead of introspection; n=20 unique episodes | RSS **0.88** vs union **2.22** vs OFF 1.83 (safe-prog) | RSS: clean 0% · frontal 30% · side 0% — but ego 3.6–8.2 m (near-freeze) | **H13 confirmed**: union − RSS **+1.345, CI [+0.944, +1.701]** | the envelope posts the campaign's best raw safety *by not driving* — worse than no monitor on the deployment metric. Stopping power is free; **selectivity is what introspection buys** (the plan-aware terms know when the plan clears). [`iter13_rss_baseline`](experiments/iter13_rss_baseline/RESULT.md) |
| 14 | **second frozen planner (VAD)** — union transfer + native-mode diversity, after four fork-level runtime fixes; n=20/scene | VAD-OFF 2.30 vs VAD+union **0.75** (safe-prog, CI [−2.06, −1.03]) | VAD-OFF fails **stationary 85%** / side 65% (inverted profile!); union: both → **0%** but ego 2.4–3.8 m | **transfer: safety yes, selectivity NO** · **H-VAD-2: 21% escapes < 30% bar** | the union protects exactly where VAD fails, but over-brakes everywhere — decision logs attribute it to the TTC term reading jittery geometric-NN IDs (VAD exposes no tracker): **selectivity is a property of tracking quality, not the rule alone**. Candidates: partial diversity under threat (0.6 m spread, 1-in-5 escapes) — a two-planner collapse spectrum; no re-ranker per the frozen rule. [`vad_generalization`](experiments/vad_generalization/RESULT.md) |
| f14 | **the full 14-scene benchmark** — OFF vs union, all official scenes, 240 seed-paired episodes | OFF **2.15** (published: 1.84 — independent reproduction; DMAD's rerun 2.11 corroborates) → union **3.09** | side 73→**37%** · stationary 32→**17%** · frontal 77→87% (mitigation) | **benchmark score +0.934, CI [+0.713, +1.155]** · safe-progress −0.17, CI includes 0 | split verdict, both halves first-class: decisive on the benchmark's metric (side survives its scene-luck falsifier on 3/4 unseen scenes; selectivity holds on clean scenes), and the deployment-metric win does **not** generalize (over-braking on unseen benign-progress scenes; frontal/0346 regression named). Open problem defined: brake-budget calibration. [`full14_benchmark`](experiments/full14_benchmark/RESULT.md) |
| 15 | **threat-cleared latch release** — the stop releases after K=4 clear frames; one new mechanism, thresholds untouched | released **3.09** NCAP = union's · safe-prog 2.45 vs union 2.20 vs OFF 2.37 | safety cells **identical to the union** (44 releases, 0 reopened cases, oscillation 2/120) | **released − union +0.246, CI [+0.206, +0.293]** — strict improvement · vs OFF +0.08, CI includes 0 | **the new best configuration** (dominates the union: same benchmark score, significantly more driving). H15 partial: the deployment gap vs OFF narrows but stays open — a *cost-of-stopping* floor in fixed-horizon episodes, not a triggering flaw. Next mechanisms defined: smaller K under premature-release pressure, or a softer-than-stop intervention. [`iter15_latch_release`](experiments/iter15_latch_release/RESULT.md) |
| 16 | **softer than a stop** — while latched, the planner's own plan re-parameterized to a 2.0 m/s crawl (speed fixed from committed impact evidence); K=4 release unchanged | crawl NCAP **2.64** vs released 3.09 · safe-prog **2.544** (the campaign's highest) | side 37→**57%** — past the pre-registered 45% falsifier bar (0108: 17→100%, impacts 4–5 m/s at zero score) · stationary at its 25% bar (0101 taps at 1.9–3.4 m/s) | crawl − released: NCAP **−0.450** CI [−0.525, −0.371] · safe-prog +0.096 CI [+0.033, +0.167] · vs OFF +0.171, CI includes 0 | **pre-registered null — the full stop stands.** The stop is a *position guarantee*, not just speed reduction: the crawl delivers the ego into the crossing point the stop halts short of. With iter 11 this is two-sided: a swerve is unsafe when the trigger is wrong; a crawl is unsafe when it is right; only the stop is safe in both. [`iter16_soft_stop`](experiments/iter16_soft_stop/RESULT.md) |
| p20 | **the power run** — OFF vs released union at 20 runs/pair, all 14 scenes (799 episodes); H-P0 gate: first-6 of every pair must reproduce the committed 6-run evidence | OFF **2.12** (published 1.84 — reproduction holds) → released **2.91** | side 74→**44%** · stationary 29→**18%** · frontal 1.24→1.78 (78→90%, mitigation) · frontal/0346 regression **confirmed real** | **benchmark +0.783, CI [+0.605, +0.928]** at 3.3× power · safe-progress **−0.03, CI [−0.13, +0.07]** — tight null | **H-P0 PASS (first-6 exact, all pairs, both arms — through 5 machine freezes, 2 hosts, 4 relaunches**; root cause memory exhaustion, found by an on-box vitals watchdog, fixed with swap; off/side-0921 at n=19, its run_19 reproducibly froze the pre-swap host). The n=6 estimate (+0.934) was modestly optimistic; this replaces it as the headline. [`full14_power`](experiments/full14_power/RESULT.md) |
| 17 | **threat-class routing** — stop wherever a tracked object's path overlaps the planned corridor (2.0 m, conservative); crawl only where none does; triggers/crawl/release unchanged | routed NCAP **2.92** vs released 3.09 · safe-prog **2.598** (new campaign high) | side 37→**47%** — past the 45% falsifier bar, carried by ONE pair (0108: 17→67%, a crossing the CV projection misses) · stationary 20% ✓ · frontal **1.97** (best of any arm) | routed − OFF safe-prog **+0.226, CI [+0.004, +0.421] — the campaign's FIRST deployment CI excluding zero vs the unmonitored planner** · routed − released: NCAP −0.170 (beyond the 0.15 tolerance), safe-prog +0.150 | **pre-registered null — the safety gate fails, the released union stands (its fourth surviving challenge).** But the deployment flip is now proven *achievable*. All three named successor predicates were then **refuted offline** on the committed log (a no-op; a dead trade; non-separable) — the routing line closes for per-frame geometric predicates, and the discriminating signal is tracking quality, converging with iteration 14. [`iter17_threat_routing`](experiments/iter17_threat_routing/RESULT.md) |
| 18 | **the tracking layer, offline gate** — association + constant-velocity filter with coasting ([`sentinel/tracker.py`](sentinel/tracker.py), 6 unit tests); pre-registered offline bars on committed logs before any GPU | — (no closed-loop run: that is the point) | O2: **12/13** unsafe crawl frames convert to stops under tracker-based overlap — one miss at 2.2 m vs the frozen 2.0 m margin | **offline gate FAILED by one frame — per the gate rule, the GPU stayed off** | the tracker repairs the measured velocity-flicker class (raw-blind frames at 4.6–6.9 m → tracker sees the actor at 0.5–1.1 m) and retention stays 80%; the tempting margin-widening fix is named as overfitting-until-proven; an initial detection-gap reading was **retracted on the record** (an artifact of a starved diagnostic feed). [`iter18_tracker`](experiments/iter18_tracker/RESULT.md) |
| 19 | **the diversity-trained candidate head** — first *learned* mechanism: K=8 candidates conditioned on the planner's own planning queries, WTA + repulsion, frozen planner untouched; training data provably disjoint from all evaluation scenes | Stage 1: 2,385-frame corpus; 1.2M-param head at **0.52 m** best-of-8 val WTA · D3 benign fidelity **PASS** (0.769 ≤ 0.780) | **D1 FAIL: 0/37 feasible escapes** on iteration 12's eval-only frames (16 diverging candidates appeared — every one kinematically infeasible) · frame join exact: 311/311, zero plan mismatches across runs four days apart | **pre-registered null — the gate refused the closed loop** | the falsifier written before training fired precisely: the *conditioning choice* is refuted, not the mechanism class — **the collapse lives in the planner's internal planning representation itself** (third measurement, third route: commands 0/37 · VAD modes 21% · learned head on planning queries 0/37). The named scene-level (BEV) survivor is tested separately in iteration 21. [`iter19_diversity_head`](experiments/iter19_diversity_head/RESULT.md) |
| 20 | **VAD tracker portability, offline gate** — replay committed VAD-union logs through the iteration-18 tracker defaults before any GPU | — (no closed-loop run) | V1 false-closing reduction **0/47 = 0%** · V2 side retention **4/6 = 66.7%** (bar 90%) · V3 frontal firing frames **79 → 90** | **pre-registered null — the gate refused the closed loop** | the simple association + smoothing tracker is **not** the VAD transfer repair: it removes no raw TTC fires, fails side retention, and increases frontal firing. The broad tracking-quality constraint remains, but this zero-GPU bridge is closed. [`iter20_vad_tracker_portability`](experiments/iter20_vad_tracker_portability/RESULT.md) |
| 21 | **BEV-conditioned diversity head, offline gate** — the scene-level survivor from iteration 19, frozen planner untouched | Stage 1: 2,385-frame BEV corpus; 5.25M-param K=8 head, best val WTA **0.795**; eval extraction exact: 311/311, zero plan mismatches | **B1 FAIL: 0/37 feasible escapes** · B2 validity **574/2488 = 23.1%** · B3 benign error **1.449 m** · B4 **0/0** selectable escapes | **pre-registered null — the gate refused the closed loop** | BEV conditioning did not recover a deployable plan B: it produced invalid would-be escapes and failed benign fidelity as well. Narrow reading: this refutes the registered BEV head, not every possible learned planner; but the frozen-planner candidate-head path is closed for both planning-query and BEV variants tested. [`iter21_bev_diversity_head`](experiments/iter21_bev_diversity_head/RESULT.md) |
| 22 | **causal planner interpretability, Stage 1** — one frozen motion/planning-bridge representation, non-evaluation scenes only, minimum counts, negative controls, and a frozen intervention grid | — (stopped before probes/interventions) | extraction produced 1,507 non-reset rows and 1,507 GT rows, but **1,507 missing-GT joins**; heldout GT rows **0** | **pre-registered data-null — S0 failed; no iter12 or closed loop authorized** | This did not test whether the bridge contains a causal collapse signal. It established that the launched Stage 1 artifact pair cannot support the registered test: timestamp precision mismatch broke the committed join, and the frozen manifest/staged-data combination had no heldout frames. A successor needs a fresh pre-registration. [`iter22_causal_planner_interpretability`](experiments/iter22_causal_planner_interpretability/RESULT.md) |
| 23 | **S0-hardened causal localization** — same narrow motion/planning-bridge question, but artifact validity is the first research object | — (stopped before probes/interventions) | canary deterministic; full S0 **PASS** with **2,627/2,627** joins, zero error rows; count floor **FAIL**: collapse positives **0** in every split, heldout danger **17/30** | **pre-registered data-null — no probe, iter12, or closed loop authorized** | Iter23 repaired the iter22 join failure and proved the extraction/counting surface, then stopped honestly because the frozen non-evaluation corpus did not contain enough collapse-positive or eligible-intervention frames to test the causal mechanism. [`iter23_s0_hardened_causal_localization`](experiments/iter23_s0_hardened_causal_localization/RESULT.md) |
| 24 | **fresh risk-support atlas** — data-support prerequisite before another causal-localization attempt | — (stopped before extraction) | known-data firewall PASS; availability FAIL: **0 eligible scenes**, **0 keyframes**, **0 heldout keyframes** after 582 post-firewall candidates all missed local six-camera files | **pre-registered availability-null — no model extraction, probes, iter12, selector, or closed loop authorized** | The firewall did its job: iter22/iter23 known data could not rescue the gate. The result is a staged-data availability null, not evidence for or against the causal signal. [`iter24_risk_support_atlas`](experiments/iter24_risk_support_atlas/RESULT.md) |
| 25 | **staged-data inventory** — provenance gate before another fresh atlas | — (stopped before extraction) | frozen root inventory FAIL: only `/datasets/nuscenes` exists and it has **0 eligible scenes**, **0 keyframes**, **0 heldout keyframes** after the known-data firewall; four other frozen roots are missing | **pre-registered infrastructure-null — no data download/copy, model extraction, labels, probes, iter12, selector, or closed loop authorized** | The blocker is staged-data availability, not a tested model mechanism. A successor must name a concrete data-staging remedy before any extraction. [`iter25_staged_data_inventory`](experiments/iter25_staged_data_inventory/RESULT.md) |
| 26 | **data-staging remedy** — source/capacity gate before any download or copy | — (stopped before data movement) | official nuScenes v1.0 trainval sensor blobs identified: **292.78 GB** archive budget; capacity FAIL: **365.975 GB** required by margin, **25.125 GB** free observed | **pre-registered capacity-null — storage provisioning required before download/staging** | Yes, the missing data must be staged/downloaded. Do not start on the current disk; next action is a storage/staging pre-registration. [`iter26_data_staging_remedy`](experiments/iter26_data_staging_remedy/RESULT.md) |
| 27 | **storage provisioning** — persistent volume before nuScenes staging | — (infrastructure only) | created/attached/formatted/mounted `sentinel-nuscenes-data-1tb`, 1024 GB `pd-balanced`, at `/datasets/nuscenes-full`; free space **1,026,108,792,832 bytes**; Docker/model runs **0**; dataset bytes moved **0** | **pre-registered storage pass — no data staging/model work authorized** | The capacity blocker is cleared, but only for a later data-staging pre-registration. No download, extraction, inventory rerun, labels, probes, iter12, selector, or closed loop is authorized from this pass. [`iter27_storage_provisioning`](experiments/iter27_storage_provisioning/RESULT.md) |
| 28 | **official nuScenes trainval staging** — stage metadata + sensor blobs before a fresh atlas | — (data gate only) | staged 11 official archives, **314,886,603,672 bytes**, SHA-proved; extracted with **0 unsafe members** across **2,631,374** tar members; six camera channels present with **34,149 files each**; availability PASS: **532** fresh post-firewall train scenes, **21,461** keyframes, **5,360** heldout keyframes | **pre-registered staging/availability pass — not a model result** | `/datasets/nuscenes-full` is now an auditable official trainval root for a fresh pre-registered atlas/research run. No model extraction, labels, probes, iter12, selector, or closed loop authorized by this pass. [`iter28_nuscenes_trainval_staging`](experiments/iter28_nuscenes_trainval_staging/RESULT.md) |
| 29 | **full-trainval risk-support atlas** — first research gate on the staged official trainval root | — (support atlas only) | S0c full extraction PASS: **532** scenes, **21,461/21,461** joined non-reset rows, zero error rows, stable shapes/dtypes; S1 support PASS: `eligible_lowdiv` **127/108/158** and `benign_control` **5,084/2,344/2,245** fit/calibration/heldout; strict optional support FAIL: `eligible_strict` **0/0/1** | **pre-registered support pass — successor pre-registration authorized; strict-collapse language not authorized** | The official trainval root contains enough fresh low-diversity hazard support and benign controls for a later causal-localization or planner-repair hypothesis. No probe, activation direction, intervention, iter12, selector, or closed-loop work is authorized from this pass. [`iter29_trainval_risk_support_atlas`](experiments/iter29_trainval_risk_support_atlas/RESULT.md) |
| 30 | **full-trainval low-diversity localization** — diagnostic probe gate on committed iter29 evidence | — (diagnostic only) | S0/S1/S2 PASS: internal tensor AUROC **0.950**, AP **0.615**, balanced accuracy **0.867**; metadata AUROC **0.596**, ego-plan AUROC **0.674**, shuffled-label internal AUROC **0.531**; scene-bootstrap AUROC p05 **0.922** | **pre-registered localization pass — causal-intervention pre-registration authorized; no causal/safety claim** | The motion/planning bridge carries linearly decodable `eligible_lowdiv` information beyond registered controls on heldout full-trainval scenes. No activation direction, intervention, iter12, selector, GPU, or closed-loop work is authorized from this pass. [`iter30_full_trainval_lowdiv_localization`](experiments/iter30_full_trainval_lowdiv_localization/RESULT.md) |
| 31 | **full-trainval bridge intervention S0 canary** — first causal-intervention harness on the iter30 bridge signal | — (stopped before calibration) | direction artifact PASS; S0 canary repeated hashes PASS for alpha `0.00` and `0.50`; alpha-zero baseline reproduction FAIL: `24` rows checked, `96` comparison failures, max error **30.222 m** vs iteration-29 originals | **pre-registered infrastructure null — calibration, heldout, iter12, selector, and closed loop not authorized** | The intervention harness is deterministic, but the sham run does not reproduce the frozen baseline within the registered `1e-5` tolerance. The experiment stops before any causal/model claim; a successor needs a fresh pre-registration that resolves baseline reproduction. [`iter31_full_trainval_bridge_intervention`](experiments/iter31_full_trainval_bridge_intervention/RESULT.md) |
| 32 | **prefix replay baseline recovery** — no-op replay audit for the iter31 S0 blocker | — (baseline replay only) | offline manifest PASS: `44` replay rows, `12` target rows, `32` context-only rows; S1 prefix replay PASS: two repeats, `44` rows and `12` targets each; model/GT target hashes repeat; max model and GT deltas vs iter29 **0.0** | **pre-registered baseline-recovery pass — fresh prefix-preserving intervention pre-registration authorized only** | Prefix-preserving no-op replay restores iteration-29 baseline parity for the frozen canary targets. This clears only the replay-form blocker; no intervention, calibration, heldout, iter12, selector, closed-loop, or safety claim is authorized. [`iter32_prefix_replay_baseline_recovery`](experiments/iter32_prefix_replay_baseline_recovery/RESULT.md) |
| 33 | **prefix-preserving bridge intervention calibration** — repaired replay form plus committed bridge-centroid direction | — (stopped before heldout) | S0 canary PASS; full calibration grid PASS on row integrity for all alphas (`4293/2452/1841` each); alpha selection NULL: best alpha `1.00` had eligible median spread delta **0.0308 m** vs `>0.25 m` bar and fraction `>0.25 m` **0.1296** vs `>=0.50` bar | **pre-registered calibration null — no usable alpha; heldout/iter12/selector/closed loop not authorized** | Prefix-preserving replay is stable and nonzero alphas perturb the bridge without gross corruption, but the committed centroid direction does not move eligible-lowdiv candidate geometry enough to pass calibration. Iter33 stops before heldout. [`iter33_prefix_preserving_bridge_intervention`](experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md) |
| 34 | **direction-specificity audit** — post-result audit of the failed global bridge-centroid direction | — (offline audit only) | S0 artifact/row integrity PASS; S1 dose-response NULL: only **74/108** eligible rows had nonnegative endpoint-spread slope (`0.685185` vs `0.70` bar), median slope **0.0307 m/alpha** | **post-result audit null — no same-direction scale-only successor authorized** | The same global bridge-centroid direction is closed for scale-only follow-up from these artifacts; a successor must change the intervention family, target site, row conditioning, or claim. [`iter34_direction_specificity_audit`](experiments/iter34_direction_specificity_audit/RESULT.md) |
| 35 | **response-heterogeneity audit** — post-result audit of the failed direction's row-level structure | — (offline audit only) | S0 PASS; S1 heterogeneity PASS (`42/108` rows slope `>=0.05`, `34/108` slope `<0`, IQR **0.1265 m/alpha**); S2 NULL: **0** frozen strata passed actionability bars | **post-result audit null — no row-conditioned successor authorized from these artifacts** | The response is heterogeneous, but not in a simple baseline-geometry stratum with enough target response and benign support. Future work must change intervention family or target site, not merely scale or row-condition the current global direction. [`iter35_response_heterogeneity_audit`](experiments/iter35_response_heterogeneity_audit/RESULT.md) |
| 36 | **bridge-site decomposition audit** — frozen subsite probes over `sdc_traj_query_last` slots and `sdc_track_query` | — (offline audit only) | S0 PASS; S1 full-bridge reproduction PASS; S2 target-site PASS: `traj_slot_0`, `traj_slot_2`, `traj_slot_3`, `traj_slot_4`, and **`track_query`** passed diagnostic + scene-bootstrap bars | **site-specific preregistration authorized — diagnostic only, no intervention/safety claim** | The next intervention should not patch the whole bridge vector. The strongest diagnostic target is `track_query` (AUROC **0.9705**, AP **0.7264**, bootstrap AUROC p05 **0.9506**), but any patch still needs a fresh pre-registration and S0 canary. [`iter36_bridge_site_decomposition`](experiments/iter36_bridge_site_decomposition/RESULT.md) |
| 37 | **track-query site intervention** — prefix-preserving `sdc_track_query`-only causal test | — (stopped before heldout) | S0 canary PASS; full calibration grid PASS on row integrity for all alphas (`4293/2452/1841` each); alpha selection NULL: best alpha `1.00` had eligible median spread delta **−0.0419 m**, fraction `>0.25 m` **0.0741**, and median best-gap delta **−0.001315** | **pre-registered calibration null — no usable alpha; heldout/iter12/selector/closed loop not authorized** | The site-specific track-query harness is stable and wrong-site guarded, but the fit-only centroid direction moves eligible-lowdiv candidate spread in the wrong direction on the median. [`iter37_track_query_site_intervention`](experiments/iter37_track_query_site_intervention/RESULT.md) |
| 38 | **track-query opposite-direction intervention** — exact sign reversal of the iter37 fit-only `sdc_track_query` centroid direction | — (S0 canary only) | Direction artifact PASS: feature count **256**, fit rows **5,211**, direction SHA **251323cf6ba7361da5aa0a084a6ae5ad5083989df75e10d16f352da845e2983d**, exact negative of iter37 (`max_abs_direction_sum=0.0`, cosine **−1.0**); S0 canary PASS: alpha-zero parity restored, `24/24` target rows changed `track_query`, `24/24` preserved `sdc_traj_query_last` | **active pre-registration — calibration authorized but not launched; no calibration result or safety claim yet** | This is the clean post-iter37 successor: test whether the causal handle was real but the centroid repair sign was reversed. It does not rescue iter37. Per the 2026-07-11 intervention-mechanism verdict, the linear-centroid steering line (iterations 31-38) is closed; iter38 calibration stays deprioritized behind iteration 42, the HUGSIM transfer, and the deployment-flip successor. [`iter38_track_query_opposite_direction`](experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md) |
| 39 | **external-validity claim audit** — hostile active-story audit before more GPU/model work | — (offline claim audit only) | S0/S1/S2 PASS; S3 found **3** active-doc scope/ambiguity findings; report/manuscript titles narrowed to frozen UniAD with measured cross-planner limits; post-narrowing scanner PASS with `0` findings | **doc-narrowing result — no new empirical safety claim** | This is the defensibility pivot: VAD remains a split transfer finding, full14 deployment remains a tight null, activation interventions remain null/active, and sensor/adversarial/latency/deployment-trade-off axes remain untested. [`iter39_external_validity_claim_audit`](experiments/iter39_external_validity_claim_audit/RESULT.md) |
| 40 | **timing and intervention-cost audit** — full14/power simulation cost and lead-time envelope | — (offline audit only) | S0/S1/S2/S3 PASS; `400/400` best episodes joined; `1,205` brake frames over `10,789.9 m` (`111.68` frames/km); `230/400` intervention episodes; `61` measured lead-time episodes, median `1.30 s`, p05/p95 `0.40/3.50 s`, negative fraction `0.049` | **simulation-scope timing/cost pass — no real-time or deployment claim** | This upgrades the safety-case budget from mini-scene evidence to full14/power logs while preserving boundaries: simulator timestamp lead time, brake-frame budget, full14 safe-progress tight null, and no production-cost or comfort claim. [`iter40_timing_cost_audit`](experiments/iter40_timing_cost_audit/RESULT.md) |
| 41 | **monitor-input degradation gate** — exact world-frame replay support before perturbation claims | — (offline audit only) | S0 infrastructure NULL: frozen paths, H-P0, Iter40 verdict, and decision-log counts were intact (`8,235` rows, `400` resets, `7,835` non-reset rows, `1,205` brake-key rows), but exact timestamp lookup into committed `p14-best` ego poses missed **1,388/6,474** timestamped monitor frames across **400/400** episodes | **replay-support infrastructure null — perturbations skipped; no sensor/degradation robustness claim** | The current committed full14/power evidence cannot support the registered exact world-frame object-stream replay. No interpolation, nearest-pose snapping, degraded-sensor GPU run, image perturbation, selector, closed-loop, deployment, or safety claim is authorized from this result. [`iter41_sensor_input_degradation_gate`](experiments/iter41_sensor_input_degradation_gate/RESULT.md) |
| 42 | **exact trace replay support** — log `ego2world` and replay online monitor decisions exactly | — (offline replay-identity gate) | S0/S1/S2/S3 PASS: the single authorized best-arm full14/power capture produced `400/400` reset blocks, exactly `6,474` frame rows / `1,205` brake frames / `156` releases / `230` intervention episodes with `0` field failures; offline replay from logged inputs and logged `ego2world` matched every frame's `fired`/`brake`/`release`/latch state (`0` mismatches) | **trace-substrate pass — authorizes only a future offline object-stream perturbation pre-registration; no degradation or safety claim** | The disciplined repair for Iter41 worked without weakening the rule: instead of interpolating poses post hoc, the online monitor logs the exact transform it used, and replay is identical at perturbation strength zero. [`iter42_exact_trace_replay_support`](experiments/iter42_exact_trace_replay_support/RESULT.md) |
| 43 | **object-stream perturbation gate** — frozen 14-cell jitter/dropout/score/churn grid over the committed iter42 exact trace, replayed offline | — (offline replay decision-flip gate) | S0/S1 PASS (zero-strength identity exact, trace SHA unchanged, determinism guard pass); verdict **`OBJECT_PERTURBATION_MILD_FRAGILE`**: jitter `0.05 m` gains **17** new interventions (bar `<=8`) and retains `218/230` (bar `>=219`); jitter `0.10 m` worse (`36` new, `1,445` brake frames); dropout `0.05`, score `0.90`, and churn `0.05` all STABLE | **pre-registered mild-fragile finding — over-firing is the fragile direction; no sensor/closed-loop/safety claim** | The rule derives object velocity from cross-frame positions, so independent per-frame position noise manufactures spurious velocity near the CPA/TTC thresholds; disappearing objects, weakened scores, and broken identities degrade gracefully instead. Closed-loop consequences of flipped decisions are not observable offline. [`iter43_object_stream_perturbation_gate`](experiments/iter43_object_stream_perturbation_gate/RESULT.md) |
| 44 | **velocity temporal-smoothing repair gate** — frozen FD-k / EMA velocity estimators (`k ∈ {2,3}`, `alpha ∈ {0.5,0.3}`) replayed offline over the committed iter42 trace, seed-paired with the iter43 grid | — (offline replay decision-flip gate) | S0/S1/S1b PASS (neutral cells bit-identical to the online stream; iter43 jitter cells reproduced field-for-field); verdict **`VELOCITY_SMOOTHING_NO_REPAIR_NULL`**: every estimator fails V1 fidelity on the clean trace (retention `209–215/230` vs `>= 225`, `5–6` invented interventions vs `<= 4`) and V2 repair (jitter new interventions `11–20` vs `<= 8`, retention below bar) | **pre-registered no-repair null — smoothing halves the over-firing (36 → 18–20 at 0.10 m) but erases 15–21 genuine interventions outright; released union unchanged** | the rule's decision boundary sits on one-frame velocity transients at the 2 Hz cadence: the same spikes that manufacture jitter false-fires also carry a fraction of the true interventions (they vanish under smoothing, not delay — median delay 0), and residual over-firing survives through the CPA term's direct use of the jittered positions; converges with iter18 from the opposite side — no low-pass filter on this estimator is the repair. [`iter44_velocity_smoothing_gate`](experiments/iter44_velocity_smoothing_gate/RESULT.md) |
| 45 | **HUGSIM infrastructure gate** — stand up the second closed-loop benchmark family: XDimLab scene release staged with a per-file SHA256 manifest, HUGSIM pixi environment built, and the unmodified UniAD_SIM client run on the SAME frozen `uniad_base_e2e.pth` inside the existing `uniad:latest` image | — (infrastructure gate; the single-scenario HD-Score `0.1677` is metric-pipeline evidence, not a performance number) | G1–G4 PASS: assets staged with provenance (306 files, ~61 GB, data disk); both environments up (`torch 2.4.1+cu124`, `gsplat 1.2.0`; client `CLIENT_LOAD_OK` on the NeuroNCAP checkpoint); `scene-0013` renders; the monitor-OFF closed-loop smoke completes end-to-end through the named pipes (15 steps, benchmark-rule termination, finite HD-Score, per-step logs); verdict **`HUGSIM_INFRA_GATE_PASS`** | **the transfer lane is open — authorizes ONLY the Stage-1/2 pre-registration (monitor-OFF reproduction subset, then OFF vs released union, seed-paired); no transfer claim** | one real incompatibility found and bounded: CUDA 11.1's cuSOLVER cannot initialize on the L4 (sm_89), so the client's GPU dense linalg is routed through a recorded interpreter-level CPU shim — client and model code untouched; the checkpoint-mismatch, pipe-deadlock, and VRAM-overflow falsifiers did not fire. [`iter45_hugsim_infra_gate`](experiments/iter45_hugsim_infra_gate/RESULT.md) |
| 46 | **HUGSIM Stage-1 monitor-OFF baseline** — frozen 52-scenario easy+medium subset (per-yaml SHA256 provenance gate), D0 determinism probe, then the stochastic branch: the first 26 scenarios x 2 back-to-back runs on the same frozen checkpoint, monitor OFF | — (completion gate; the 38-episode HD aggregate — mean `0.3849`, easy `0.4355` / medium `0.3393` — is the registered plausibility context, not a performance number) | D0 verdict **STOCHASTIC** (16 vs 15 steps, `data.pkl` SHA divergence); C1 **FAIL** `38/52` complete — the seven `load_HD_map: true` `-medium-01` scenarios failed both attempts before the client's first step on a missing `maps/expansion/*.json` (the nuScenes map-expansion pack was never staged; the one `-medium-01` without the flag passed); pairing spread median \|ΔHD\| `0.0245` over 19 pairs (bar `0.15`, not fired); verdict **`HUGSIM_OFF_BASELINE_NULL`** | **pre-registered completion null — the Stage-2 OFF-vs-released-union pre-registration is NOT authorized; a successor needs a fresh pre-registration staging the map-expansion pack** | the registered crash-loop falsifier fired in its dual-failure form, but the mechanism is a staging gap, the third of the iteration's record (zip-nesting and 3DRealCar-suffix defects were fixed by a recorded launcher-only amendment): across both launches no episode that reached client stepping ever failed, and every completed episode finished on attempt 1 inside 114-481 s. [`iter46_hugsim_off_baseline`](experiments/iter46_hugsim_off_baseline/RESULT.md) |
| 47 | **map-expansion staging + OFF-baseline completion** — Stage A stages the official nuScenes map-expansion pack v1.3 (iteration-28-class gate); Stage B re-runs exactly the 14 failed `load_HD_map` `-medium-01` episodes under the carried stochastic D0 verdict, then ONE analyzer run over all 52 (38 carried + 14 new) | — (staging gate + completion re-run; iteration 46's null stands as published) | Stage A **PASS**: archive `398,535,531` bytes with recorded SHA256, redacted public-bucket provenance, `0` unsafe members over `13`, all four `maps/expansion/*.json` vector maps present; Stage B **PASS**: `52/52` episodes complete with finite HD-Score and per-step logs, all 14 new episodes on attempt 1 (wall 102-509 s, bound 1200 s), `retried_episodes = 0`, carried integrity `104/104` files byte-identical, pairing falsifier NOT fired over all 26 pairs (median \|ΔHD\| `0.0251`, bar `0.15`) | **pre-registered PASS — the full 52-episode monitor-OFF arm stands; authorizes ONLY the iteration-48 Stage-2 OFF-vs-released-union pre-registration** | completion re-earned, not retroactively repaired: iteration 46's null stands, the map-staging diagnosis is confirmed by cure (all seven formerly dual-failing scenarios completed first-attempt), and the 26-pair spread is heavy-tailed (22/26 pairs <= `0.09`, max `0.7419` on `scene-0138-medium-01`) — that shape binds the Stage-2 paired design. [`iter47_map_staging_and_off_completion`](experiments/iter47_map_staging_and_off_completion/RESULT.md) |
| 48 | **HUGSIM Stage-2 transfer gate** — THE transfer verdict of the second-benchmark line: monitor-OFF vs the released union under the seven NeuroNCAP-frozen parameters (zero retuning, F1 void discipline), client-side interception in UniAD_SIM's e2e loop, 26 scenarios x 2 runs x 2 arms with within-launch back-to-back pairing under the carried stochastic verdict, ONE analyzer run | mean paired HD-Score delta (ON − OFF) over 52 pairs, 95% scenario-clustered bootstrap CI (26 clusters, 10,000 draws, seed 48); median-delta CI as the registered heavy-tail treatment | `104/104` episodes complete, `0` retries, `0` dual failures; F1 passed (patch SHA byte-identical to the committed copy, frozen params echoed in receipts and all 52 ON decision logs); primary mean delta `−0.0166` CI `[−0.0551, +0.0255]` (includes zero), median `+0.0032` CI `[−0.0467, +0.0178]`; firing: `37/52` ON episodes intervened, `887` fired / `1,392` brake frames (`26.9%` pooled), `134` latch releases; mean paired RC delta `−0.0147` (bar `−0.30`); fresh OFF-OFF median \|ΔHD\| `0.0307` (bar `0.15`) | **pre-registered TRANSFER_NULL — the NeuroNCAP benefit does not measurably transfer to HUGSIM easy+medium at this N; published at full weight as the measured external-validity boundary; no NeuroNCAP-equivalence, deployment, or safety claim** | the frozen rule demonstrably operates on HUGSIM — fires, latches, releases; F2 over-firing NOT fired (iteration 43's splat-noise prediction lands as broad-but-not-constant firing, 2 episodes >80% brake frames, pooled 26.9%), F3 RC collapse NOT fired (iteration 13's paralysis did not recur) — but the interventions buy no measurable HD change against a noise floor where single stochastic pairs swing most of the score range; the named hard-tier successor is iteration 49, and any further successor needs a fresh pre-registration. [`iter48_hugsim_transfer_gate`](experiments/iter48_hugsim_transfer_gate/RESULT.md) |
| 49 | **HUGSIM hard/extreme-tier transfer gate** — the collision-dominant regime test: the byte-identical iteration-48 patch (frozen params, F1 SHA discipline) on the lexicographically first 26 of the 36 harder-tier yamls (13 scenes x {extreme-00, hard-00}; 15 of 26 script an `AttackPlanner`), 104 episodes, within-launch back-to-back pairing, pre-launch asset pre-check gate | mean paired HD-Score delta (ON − OFF) over 52 pairs, 95% scenario-clustered bootstrap CI (26 clusters, 10,000 draws, seed 49); fresh harder-tier OFF-OFF noise floor via F5; iteration-50 P1 opportunity branch | `104/104` episodes complete, `0` retries, `0` failed dirs; F1 passed mechanically (patch SHA byte-identical, seven frozen params echoed); primary mean delta `−0.0089`, CI `[−0.0438, +0.0203]` (includes zero), median `+0.0011`, CI `[−0.0077, +0.0105]`; firing: `40/52` ON episodes intervened, `275` fired frames / `526` brake frames (`22.3%` pooled), `58` releases, no step caps; F2/F3/F5 not fired; P1 opportunity `51/52` | **pre-registered TRANSFER_NULL — the hard/extreme collision-regime extension does not re-establish the NeuroNCAP benefit; P1 Branch B is REFUTED, so the failure is real, not opportunity-scarce** | the frozen rule operates and collision opportunity is nearly universal, but the paired HD outcome remains null; the descriptive tier split is not a claim (hard mean `+0.0011`, extreme `−0.0189`); no NeuroNCAP-equivalence, deployment, benchmark-ranking, robustness, or safety claim. [`iter49_hugsim_hard_tier_gate`](experiments/iter49_hugsim_hard_tier_gate/RESULT.md) |
| 50 | **collision-opportunity audit** — entirely offline over committed evidence (zero GPU/gcloud): does collision opportunity explain where the union's benefit appears? Frozen definitions (HUGSIM OFF `eval.json` `nc_min < 1.0` primary; `any_collide@0.0s` per-pair rate on NeuroNCAP; `0.25` fraction bar), circularity guard (labels from OFF arms only), and the frozen prediction P1 for iteration 49 — committed ALONE while iteration 49's run was in flight and unread | A1: Spearman rho over the 20 full14/power pairs (OFF collision rate vs paired benefit), 10,000-draw pair-resampling bootstrap CI, seed 50, bar `rho >= +0.5` with CI excluding 0; A2: iteration-48 OFF-arm primary-opportunity fraction vs the `0.25` bar | integrity all-pass (tar `399/400` metrics over 20 pairs, `side-0921 n=19` detected, published iteration-48 mean reproduced to `1e-9`); **A1_CONFIRMED**: rho `+0.7003`, CI `[+0.3909, +0.8762]`; strata means `+0.989` (12 pairs at rate `>= 0.5`) vs `+0.263` (8 below); **A2**: `40/52` (`76.9%`) of iteration-48 OFF episodes carry primary opportunity, and the independent iteration-46/47 baseline corroborates at exactly `40/52`; descriptive paired deltas: with-opportunity mean `+0.0013`, without `−0.0765` | **`OPPORTUNITY_AUDIT_COMPLETE` — the iteration-48 `TRANSFER_NULL` is classified `OPPORTUNITY_PRESENT_NULL`: opportunity was abundant and the interventions converted none of it; the classification does NOT upgrade the null** | on NeuroNCAP the benefit is an opportunity-conversion effect (it concentrates where the OFF arm collides); on HUGSIM the same frozen rule fired amid 40 collision-bearing OFF episodes and bought nothing — the transfer boundary is the mechanism's firing not aligning with what causes HUGSIM collisions, not the benchmark lacking safety-critical content; P1 (registered before any iteration-49 read) binds the hard-tier interpretation: opportunity present + positive CI confirms, opportunity present + null makes the transfer failure REAL. [`iter50_collision_opportunity_audit`](experiments/iter50_collision_opportunity_audit/RESULT.md) |
| 51 | **HUGSIM transfer-failure taxonomy** — offline post-result audit over committed iteration-48/49 HUGSIM proof only: classify each paired episode by OFF collision opportunity, ON collision persistence/conversion, ON brake timing proxy, and descriptive HD materiality; zero GPU/gcloud/box reads and no retuning | 104 paired HUGSIM transfer episodes; primary categories frozen before the analyzer ran; `MATERIAL_HD_BAR = 0.03` descriptive only; dominance label requires one category to cover at least 40% of OFF-opportunity pairs | infrastructure all-pass: transfer means reproduced exactly; P1 cross-check matched `51` recomputed vs `51` recorded; combined counts: persistent late-by-proxy `34`, persistent early-by-proxy `33`, persistent no-brake `18`, induced collision `7`, clean no-opportunity `6`, converted no-material-gain `4`, converted material-gain `2`; combined largest category `34/91 = 0.374`, below the dominance bar | **`TAXONOMY_COMPLETE` — mixed taxonomy, not a single-cause failure; only `6/91` OFF-opportunity pairs convert, and only `2` conversions clear the descriptive material-gain deadband** | hard/extreme is the sharpest boundary: `51/52` opportunity pairs, `0/52` conversions, all opportunity pairs persistent; AttackPlanner scenarios lean late-by-proxy (`15/30`), non-AttackPlanner hard/extreme scenarios lean early-by-proxy (`10/21`); no safety/transfer/deployment/robustness claim, and the timing labels are descriptive proxies only. [`iter51_hugsim_failure_taxonomy`](experiments/iter51_hugsim_failure_taxonomy/RESULT.md) |
| 52 | **HUGSIM ON-collision timing audit** — offline post-result audit over committed iteration-48/49 HUGSIM proof only: for ON-collision episodes, compare first ON collision time, first brake time, and frozen TTC/CPA surface-proxy entry; disclosed prototype counts, no inferential surprise claim | 92 ON-collision episodes out of 104 paired transfer episodes; timing bins: unknown, no-brake/no-surface-proxy, no-brake/surface-proxy-present, post-collision first brake, short-lead brake, long-lead brake; surface proxy = `min_ttc <= 2.5` and `min_cpa <= 1.5` | infrastructure all-pass: pair count and ON-collision count cross-checked against iteration 51 (`104`, `92`); combined bins: post-collision first brake `35`, long-lead brake `26`, no-brake/no-surface-proxy `22`, short-lead brake `9`, no-brake/surface-proxy-present `0`, unknown `0`; family split absent/post `57`, pre-collision brake `35` | **`TIMING_AUDIT_COMPLETE` — absent/post-collision braking is larger than pre-collision braking, but 35 pre-collision-brake collisions (26 long-lead) make a pure brake-earlier repair story insufficient** | all 22 no-brake ON-collision cases had zero frozen TTC/CPA surface-proxy rows, so they are surface-miss by this scalar proxy; hard/extreme remains sharp (`52/52` ON collisions, absent/post `33`, pre `19`); no actor-identity, safety, transfer, robustness, deployment, or retuning claim. [`iter52_hugsim_on_collision_timing_audit`](experiments/iter52_hugsim_on_collision_timing_audit/RESULT.md) |
| 53 | **HUGSIM first-fire channel audit** — offline post-result audit over committed iteration-48/49 HUGSIM proof only: reconstruct the released union's first fired row as TTC-only, CPA-only, both, no-fire, or unreconstructable; disclosed pre-freeze patch/prototype inspections, no inferential surprise claim | 104 paired HUGSIM transfer episodes; 92 ON-collision episodes; first-fire channel = actual OR predicate side on the first fired decision row | infrastructure all-pass: pair count matched iteration 52 (`104` vs `104`), timing-bin mismatches `0`, unreconstructable first-fire channels `0`; ON-collision first-fire channels: TTC-only `36`, CPA-only `33`, no-fire `22`, both `1`; pre-collision-fire ON collisions: CPA-only `19`, TTC-only `16`, both/no-fire `0` | **`FIRST_FIRE_CHANNEL_COMPLETE` — the pre-collision-fire persistent cases split across both sides of the union, so the HUGSIM failure is not one bad branch** | the stricter simultaneous TTC/CPA surface proxy from iteration 52 was too strict to describe the actual OR predicate, but reconstructing the OR does not rescue the transfer null; next mature line is object/path geometry and provenance, not threshold retuning. [`iter53_hugsim_first_fire_channel_audit`](experiments/iter53_hugsim_first_fire_channel_audit/RESULT.md) |
| 54 | **HUGSIM provenance support audit** — offline support audit over committed iteration-48/49 HUGSIM proof only: reconstruct first-fire monitor argmin object/path provenance, then check whether HUGSIM eval artifacts log collision actor identity; disclosed schema/patch inspections, no inferential surprise claim | 104 paired HUGSIM ON episodes; 92 ON-collision episodes; iteration-53 report used only for pair/channel/timing cross-checks | infrastructure all-pass: pair count matched iteration 53 (`104` vs `104`), channel mismatches `0`, timing mismatches `0`; monitor-side provenance reconstructs cleanly: unique TTC object `40`, unique CPA object `36`, both-distinct objects `1`, no-fire `27`, reconstruction failures `0`; collision actor support `0/104` | **`PROVENANCE_SUPPORT_NULL` — committed logs support monitor-hazard reconstruction but not actor matching, because HUGSIM collision actor identity is not logged** | the next credible HUGSIM run needs collision actor/contact/proximity instrumentation before any actor-match claim; no safety, transfer, deployment, benchmark, actor-identity, or retuning claim. [`iter54_hugsim_provenance_support_audit`](experiments/iter54_hugsim_provenance_support_audit/RESULT.md) |
| 55 | **HUGSIM collision instrumentation source audit** — source-only audit over the frozen HUGSIM checkout; verify source SHA and map where `eval.json` / `nc` / HD-Score and collision/proximity provenance can be instrumented in a future patch | frozen HUGSIM source at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`; 153 source-like files scanned, 103 candidates found | checkout identity matched the frozen SHA; labels all pass: metric source identified, collision geometry source identified, actor identity available in source, instrumentation point supported, source map not insufficient; top candidates: `sim/utils/score_calculator.py`, `closed_loop.py` | **`COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE` — a future no-metric-change provenance logging patch is designable from source** | no HUGSIM run, no implementation, no actor attribution, no safety/transfer/deployment/benchmark/retuning claim; the next step still needs a fresh instrumentation pre-registration. [`iter55_hugsim_collision_instrumentation_source_audit`](experiments/iter55_hugsim_collision_instrumentation_source_audit/RESULT.md) |
| 56 | **HUGSIM provenance instrumentation patch design** — source-only patch-design gate after iteration 55; draft a no-metric-change `collision_provenance` sidecar patch and statically verify it before any run | frozen HUGSIM source at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`; one patch file against `sim/utils/score_calculator.py`; verifier applies patch to a clean temp clone and compiles changed Python | source SHA matched, patch applied cleanly, changed file allowed, required provenance fields present, Python compile passed; static metric/control guard failed on `if score_nc == 0.0:` because the frozen guard flags changed lines containing `score_nc =` | **`INSTRUMENTATION_PATCH_DESIGN_NULL` — first patch draft rejected by registered static guard** | patch is not authorized for a run; no actor attribution, HD-Score execution, safety/transfer/deployment/benchmark/retuning claim; successor needs fresh guard/patch pre-registration. [`iter56_hugsim_provenance_instrumentation_patch`](experiments/iter56_hugsim_provenance_instrumentation_patch/RESULT.md) |
| 57 | **HUGSIM provenance patch guard refinement** — static verifier refinement over the byte-identical iteration-56 patch; distinguish metric/control assignments from read-only score comparisons | same patch SHA256 `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`; frozen HUGSIM source at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e` | all refined labels pass: patch SHA match, source SHA match, patch applies cleanly, changed file allowed, required provenance fields present, metric-assignment guard pass, control-call guard pass, score-list guard pass, Python compile pass | **`PATCH_GUARD_REFINEMENT_COMPLETE` — byte-identical patch is statically supported as additive provenance instrumentation** | still no HUGSIM run, no HD-Score execution invariance, no actor attribution, no safety/transfer/deployment/benchmark/retuning claim; any run needs a fresh pre-registration. [`iter57_hugsim_patch_guard_refinement`](experiments/iter57_hugsim_patch_guard_refinement/RESULT.md) |
| 58 | **HUGSIM provenance instrumented canary** — first real HUGSIM execution of the byte-bound provenance patch, on a registered two-episode OFF/ON collision canary | `scene-0013-hard-00` OFF r1 then ON r1; HUGSIM patch SHA256 `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`; released-union monitor patch SHA256 `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c` | both episodes completed first-attempt; `nc_min = 0.0` in both; top-level `collision_provenance` emitted with counts `11` OFF and `13` ON; scalar metric keys present; `details` rows scalar-only; ON decision log present | **`PROVENANCE_CANARY_COMPLETE` — byte-identical patch executes and emits top-level collision provenance in the registered canary** | instrumentation-execution blocker retired only; no actor-match, HD-Score-invariance, safety/transfer/deployment/benchmark/retuning claim; successor needs a fresh actor-match pre-registration. [`iter58_hugsim_provenance_instrumented_canary`](experiments/iter58_hugsim_provenance_instrumented_canary/RESULT.md) |
| 59 | **HUGSIM actor-match support audit** — bounded same-run comparison between monitor first-fire hazard provenance and HUGSIM collision provenance | eight registered Sentinel-ON episodes only; frozen bridge compares monitor-local `(forward,lateral)` to HUGSIM foreground `obs_box[:2]`; classifiable support requires first fire before/equal first foreground collision and unique monitor argmin | all 8 completed first-attempt with intact scalar schema, scalar-only `details`, top-level provenance, and ON decision logs; support counts: `classifiable_foreground` 3, `no_monitor_fire` 2, `post_collision_fire` 2, `background_collision_only` 1; bridge counts: `actor_mismatch` 3 | **`ACTOR_MATCH_AUDIT_COMPLETE` — support exists and all three classifiable foreground rows are mismatches by the frozen bridge** | bounded mechanism audit only: distances 15.43 m, 21.99 m, 37.04 m; no population actor-mismatch rate, no repair, no safety/transfer/deployment/benchmark/retuning claim. [`iter59_hugsim_actor_match_audit`](experiments/iter59_hugsim_actor_match_audit/RESULT.md) |
| 60 | **Actor-match bridge sensitivity audit** — offline sensitivity over the three iteration-59 classifiable foreground rows only | committed iteration-59 proof/report; 16 frozen bridge variants per row: first-fire vs propagated position, two axis orders, four sign flips; no fitted transform or retuning | all three rows reconstructed; 48 variants evaluated; counts: `robust_mismatch` 2, `bridge_ambiguous_possible` 1; no `bridge_match_possible`; minimum distance `5.6649 m` | **`BRIDGE_AMBIGUOUS_NULL` — no bounded variant makes a match, but one row becomes ambiguous, so robust all-row mismatch is not supported** | narrows iteration 59 honestly: zero matches, one ambiguous bridge case, two robust mismatches; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/retuning claim. [`iter60_actor_bridge_sensitivity`](experiments/iter60_actor_bridge_sensitivity/RESULT.md) |
| 61 | **Monitor object-surface audit** — compare every first-fire monitor object to every eligible HUGSIM foreground provenance row under the frozen bridge grid | committed iteration-59/60 proof only; three classifiable rows; trigger vs non-trigger object labels; 2,384 object/provenance/bridge variants | rows: `no_monitor_object_support` 2, `nontrigger_object_match` 1; `ttc_extreme_b` non-trigger `object_id=16` matches at `2.0686 m` while trigger `object_id=1` remains ambiguous at `5.6649 m` | **`OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE` — one row supports wrong-object/wrong-hazard selection; two rows still lack first-fire object support** | bounded three-row mechanism audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/retuning claim. [`iter61_monitor_object_surface_audit`](experiments/iter61_monitor_object_surface_audit/RESULT.md) |
| 62 | **Non-trigger ranking audit** — one-row selector audit for the Iter61 matched non-trigger object | committed iteration-59/61 proof only; reconstruct every first-fire object's CPA/TTC values and ranks in `ttc_extreme_b` | matched non-trigger `object_id=16`: `min_cpa=22.7648 m`, CPA rank `9/9`, `ttc=null`, no CPA/TTC crossing; trigger `object_id=1`: TTC-only, `ttc=2.1303 s`, TTC rank `1` | **`MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE` — the matched object was visible but outside the frozen first-fire hazard surface** | one-row selector-surface fact only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/retuning claim. [`iter62_nontrigger_ranking_audit`](experiments/iter62_nontrigger_ranking_audit/RESULT.md) |
| 63 | **Temporal emergence audit** — follow the Iter61/62 matched non-trigger object through pre-contact monitor frames | committed iteration-59/61/62 proof only; target `ttc_extreme_b` `object_id=16`; pre-contact rows are `ts < 7.25 s` | object present in 13 of 29 pre-contact frames; hazard frames `0`; borderline frames `0`; min CPA `12.1690 m`; min TTC `null`; contact-time row also subthreshold | **`TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE` — the collision-near object never becomes a frozen CPA/TTC hazard before contact** | one-object temporal surface audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/retuning claim. [`iter63_temporal_emergence_audit`](experiments/iter63_temporal_emergence_audit/RESULT.md) |
| 64 | **Unsupported-row temporal surface audit** — expand the two no-first-fire-support rows to all pre-contact decision objects | committed iteration-59/61 proof only; targets `ttc_extreme_short` and `cpa_medium_b`; frozen 16-variant bridge grid over every pre-contact object/provenance pair | both rows become `pre_contact_object_match`; best distances `1.6718 m` and `0.4325 m`; `28,016` variants evaluated | **`UNSUPPORTED_TEMPORAL_MATCH_COMPLETE` — first-fire support is absent, but pre-contact object-surface support exists in both rows** | two-row temporal object-surface audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/retuning claim. [`iter64_unsupported_temporal_surface_audit`](experiments/iter64_unsupported_temporal_surface_audit/RESULT.md) |
| 65 | **Matched pre-contact temporal alignment audit** — reconstruct released CPA/TTC metrics for the two Iter64 matched objects at their matched decision timestamps | committed iteration-59/61/64 proof only; targets `ttc_extreme_short` `object_id=2` and `cpa_medium_b` `object_id=6` | both rows classify `matched_object_subthreshold`; `object_id=2` at `0.25 s`: min CPA `12.7240 m`, TTC `3.5763 s`; `object_id=6` at `2.25 s`: min CPA `9.3179 m`, TTC `null`; one matched object later equals first-fire object | **`TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE` — the pre-contact matches are visible geometry, not active released-union hazards at their matched timestamps** | two-row temporal/provenance alignment audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/retuning claim. [`iter65_temporal_alignment_audit`](experiments/iter65_temporal_alignment_audit/RESULT.md) |
| 66 | **Matched-object hazard timeline audit** — follow the two Iter65 target objects across every pre-contact decision frame | committed iteration-59/61/64/65 proof only; targets `ttc_extreme_short` `object_id=2` and `cpa_medium_b` `object_id=6`; released CPA/TTC thresholds unchanged | mixed labels: `object_id=2` becomes active TTC hazard at `1.50 s` after borderline frames at `0.25 s` and `0.50 s`; `object_id=6` is present in `13/25` pre-contact frames with zero active or borderline frames | **`MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE` — one matched object is late-emerging, the other remains visible-never-active** | two-row target-object temporal surface audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/retuning claim. [`iter66_matched_object_timeline_audit`](experiments/iter66_matched_object_timeline_audit/RESULT.md) |
| 67 | **Trigger-target bridge audit** — compare each row's first-fire trigger object against the bridge-matched target object under the frozen bridge grid | committed iteration-59/61/64/65/66 proof only; targets `ttc_extreme_short` and `cpa_medium_b`; compare full pre-contact surface and first-fire trigger surface | one same-object target/trigger row and one split-object row; full-window target matches `1.6718 m` and `0.4325 m`; full-window trigger matches `1.6718 m` and `2.8332 m`; first-fire trigger distances are unsupported (`6.9272 m`, `19.6983 m`) | **`TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE` — the split row is not trigger-unsupported globally, but first-fire trigger support is absent at the fire timestamp** | two-row trigger/target bridge audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/retuning claim. [`iter67_trigger_target_bridge_audit`](experiments/iter67_trigger_target_bridge_audit/RESULT.md) |
| 68 | **Fire-time bridge decomposition audit** — decompose first-fire trigger support gaps against each trigger's best full-window bridge support | committed iteration-59/61/64/65/66/67 reports only; fixed first-fire trigger objects `2` and `1`; no geometry recomputation beyond frozen surfaces | temporal split: `ttc_extreme_short` best support occurs `1.25 s` before first fire (`6.9272 m` -> `1.6718 m`); `cpa_medium_b` best support occurs `2.00 s` after first fire (`19.6983 m` -> `2.8332 m`) | **`FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE` — fire-time support gaps can be pre-fire or post-fire temporal misalignment** | two-row fire-time bridge decomposition only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/retuning claim. [`iter68_fire_time_bridge_decomposition`](experiments/iter68_fire_time_bridge_decomposition/RESULT.md) |
| 69 | **HUGSIM mechanism taxonomy synthesis** — synthesize the eight iteration-59 ON actor-match rows from committed downstream reports only | committed iteration-59/61/63/64/65/66/67/68 reports; no GPU, live box read, new HUGSIM episode, threshold change, or retuning | all eight rows classified; structural rows preserved (`no_monitor_fire` 2, `post_collision_fire` 2, `background_collision_only` 1); all three classifiable foreground rows refined | **`HUGSIM_MECHANISM_TAXONOMY_COMPLETE` — the mechanism map is mixed: non-trigger visible-never-hazard, same-object late fire after best bridge, and split-object visible-never-active fire before best bridge** | eight-row evidence synthesis only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter69_hugsim_mechanism_taxonomy`](experiments/iter69_hugsim_mechanism_taxonomy/RESULT.md) |
| 70 | **HUGSIM structural-row timing audit** — refine the five iteration-69 structural rows using committed iteration-59 proof and decision logs | committed iteration-59 proof/report and iteration-69 taxonomy only; report/log cross-check for monitor frames, fired/brake counts, first-fire timestamp, and channel | all five structural rows classified: surface-silent foreground-present `2`, late-fire foreground-present `2`, foreground-absent/background-only `1`; both late-fire rows fire `+1.75 s` after first foreground timestamp | **`HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE` — the structural side is not one bucket: two no-fire foreground cases, two late-fire foreground cases, and one true background-only case** | five-row structural timing/support audit only; no actor-causality, repair, population mismatch-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter70_hugsim_structural_timing_audit`](experiments/iter70_hugsim_structural_timing_audit/RESULT.md) |
| 71 | **HUGSIM surface-silent margin audit** — test the two foreground-present no-fire rows against frozen CPA/TTC margins before foreground contact | committed iteration-59 proof/report and iteration-70 structural timing report only; descriptive bands, not candidate thresholds | both fixed rows classify `surface_silent_far_margin`; no near-margin rows and no no-object rows; closest margins: `mixed_extreme` CPA `+2.6062 m`, `nofire_hard_control` TTC `+3.4560 s` and CPA `+6.4779 m` | **`HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE` — the no-fire foreground rows are not small threshold misses under the registered bands** | two-row descriptive margin audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter71_hugsim_surface_silent_margin_audit`](experiments/iter71_hugsim_surface_silent_margin_audit/RESULT.md) |
| 72 | **HUGSIM late-fire prefire margin audit** — test the two foreground-present late-fire rows against frozen CPA/TTC margins before foreground contact | committed iteration-59 proof/report and iteration-70 structural timing report only; descriptive bands, not candidate thresholds | both fixed rows classify near-margin before contact: `both_distinct_extreme` near CPA (`+0.5355 m`), `ttc_medium_a` near TTC (`+0.7742 s`); both first fires occur `+1.75 s` after foreground | **`HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE` — late-fire rows are near but not crossing before contact, unlike the far-margin no-fire rows** | two-row descriptive prefire margin audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter72_hugsim_late_fire_prefire_margin_audit`](experiments/iter72_hugsim_late_fire_prefire_margin_audit/RESULT.md) |
| 73 | **HUGSIM structural margin-transition audit** — compare all four foreground-present structural rows on full decision-log margin timelines | committed iteration-59 proof/report plus iteration-70/71/72 reports only; full-log first-near and first-active timestamps relative to foreground contact | exact split: surface-silent rows are `silent_far_never_active` 2/2; late-fire rows are `late_prefire_near_postcontact_active` 2/2; late rows first active at `+1.75 s` | **`HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE` — structural branch contrast is far/never-active vs near-before-contact/postcontact-active** | four-row descriptive margin-transition audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter73_hugsim_margin_transition_audit`](experiments/iter73_hugsim_margin_transition_audit/RESULT.md) |
| 74 | **HUGSIM late-fire delay-barrier audit** — classify whether the two late-fire rows are same-channel or cross-channel post-contact activations | committed iteration-59 proof/report plus iteration-70/72/73 reports only; pre-contact near-channel sets vs first-active channel sets | both fixed rows classify `cross_channel_late_activation`: `both_distinct_extreme` CPA-near -> TTC-active, `ttc_medium_a` TTC-near -> CPA-active; both first active at `+1.75 s` | **`HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE` — the late-fire barrier is cross-channel in both fixed rows, not same-channel drift over threshold** | two-row descriptive delay-barrier audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter74_hugsim_late_fire_delay_barrier`](experiments/iter74_hugsim_late_fire_delay_barrier/RESULT.md) |
| 75 | **HUGSIM cross-channel object-handoff audit** — classify whether the Iter74 cross-channel handoff keeps the same monitor object or switches object id | committed iteration-59 proof/report plus iteration-70/72/73/74 reports only; per-object CPA/TTC reconstruction at pre-near and first-active timestamps | both fixed rows classify `object_switch_cross_channel_handoff`: `both_distinct_extreme` object `5` -> `9`, `ttc_medium_a` object `6` -> `24` | **`HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE` — cross-channel late fire is also cross-object in both fixed rows** | two-row descriptive object-handoff audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter75_hugsim_cross_channel_object_handoff`](experiments/iter75_hugsim_cross_channel_object_handoff/RESULT.md) |
| 76 | **HUGSIM switch foreground-bridge audit** — test whether the pre-near or post-active switched object has bounded foreground collision-provenance support | committed iteration-59 proof/report plus iteration-70/72/73/74/75 reports only; iteration-61 bridge family, 3 m match and 6 m ambiguous bands | both fixed rows classify `no_foreground_bridge_support`; best distances: `13.4483/10.8347 m` for pre/active in `both_distinct_extreme`, `8.1239/8.4408 m` in `ttc_medium_a` | **`HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE` — neither switched object bridges to foreground under the frozen support grid** | two-row descriptive foreground-bridge audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter76_hugsim_switch_foreground_bridge`](experiments/iter76_hugsim_switch_foreground_bridge/RESULT.md) |
| 77 | **HUGSIM event object-set foreground-bridge audit** — test whether any object in the full pre/active event-row object sets bridges to foreground | committed iteration-59 proof/report plus iteration-70/72/73/74/75/76 reports only; all logged objects at the fixed pre and active timestamps, same bridge bands | mixed support: `both_distinct_extreme` pre set ambiguous via object `9` (`3.6899 m`) while active set no-support; `ttc_medium_a` both sets match via object `10` (`1.1245/1.2931 m`) | **`HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE` — foreground support exists in the full object set, but not necessarily on the selected hazard object** | two-row descriptive event-object-set foreground-bridge audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter77_hugsim_event_object_set_bridge`](experiments/iter77_hugsim_event_object_set_bridge/RESULT.md) |
| 78 | **HUGSIM support-object ranking audit** — classify the iteration-77 foreground-supported objects against the logged monitor surface and iteration-75 selected objects | committed iteration-59 proof/report plus iteration-70/72/73/74/75/76/77 reports only; fixed support events: `both_distinct_extreme` pre object `9`, `ttc_medium_a` pre/active object `10` | all three fixed support events classify `support_object_nonselected_subthreshold`; support ids differ from selected ids (`9` vs `5`, `10` vs `6`, `10` vs `24`), CPA ranks are `4/7/2`, min CPA values are `21.6343/17.2764/13.5578 m`, and TTC is non-finite | **`HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE` — foreground-supported full-set objects are neither selected nor near the frozen hazard surface** | three-event descriptive support-object ranking audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter78_hugsim_support_object_ranking`](experiments/iter78_hugsim_support_object_ranking/RESULT.md) |
| 79 | **HUGSIM selected-object surface decomposition** — classify the selected monitor object and foreground-supported object at the same fixed rows | committed iteration-59 proof/report plus iteration-75/77/78 reports only; same three selected-vs-support event pairs | selected objects are active/borderline while support objects remain subthreshold: `both_distinct_extreme` pre selected `5` borderline CPA `2.0355 m` vs support `9` subthreshold; `ttc_medium_a` pre selected `6` borderline TTC `3.2742 s` vs support `10` subthreshold; `ttc_medium_a` active selected `24` active CPA `1.2791 m` vs support `10` subthreshold | **`HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE` — foreground support and released hazard-surface selection split across different objects** | three-event descriptive selected-vs-support surface audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter79_hugsim_selected_surface_decomposition`](experiments/iter79_hugsim_selected_surface_decomposition/RESULT.md) |
| 80 | **HUGSIM selected-object all-provenance bridge audit** — test whether the iteration-79 selected active/borderline objects bridge to any logged collision-provenance row, without filtering by class | committed iteration-59 proof/report plus iteration-77/79 reports only; same three selected event objects | all eligible logged provenance rows are foreground (`30/30`), and all three selected objects classify `selected_all_provenance_no_support`; best distances are `13.4483 m`, `8.1239 m`, and `8.4408 m` | **`HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE` — selected active/borderline objects do not bridge to any logged provenance row in the fixed events** | three-event descriptive selected-object all-provenance bridge audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter80_hugsim_selected_all_provenance_bridge`](experiments/iter80_hugsim_selected_all_provenance_bridge/RESULT.md) |
| 81 | **HUGSIM support-object temporal surface audit** — follow the iteration-78 foreground-supported support objects across every committed ON decision frame | committed iteration-59 proof/report plus iteration-78/79/80 reports only; fixed support objects `9` and `10` | two-object split: `both_distinct_extreme` support object `9` later becomes borderline at `5.5 s` and active at `7.0 s`; `ttc_medium_a` support object `10` is visible in `15` frames with zero active or borderline frames | **`HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE` — one foreground-supported object eventually reaches the released surface, while the other remains visible-never-surface** | two-object descriptive temporal surface audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter81_hugsim_support_object_temporal_surface`](experiments/iter81_hugsim_support_object_temporal_surface/RESULT.md) |
| 82 | **HUGSIM support-object surface/provenance co-occurrence audit** — test whether foreground bridge support and released CPA/TTC surface activation co-occur on the same fixed support objects | committed iteration-59 proof/report plus iteration-81 report only; fixed support objects `9` and `10`; same iteration-76 bridge bands | object `9` has bridge support and surface co-occurrence only at borderline (`1` borderline+bridge frame, zero active+bridge frames; best surface bridge `0.9876 m`); object `10` has bridge support in `15/15` present frames but zero active/borderline frames | **`HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE` — support/provenance alignment exists, but active released-surface co-occurrence does not** | two-object descriptive surface/provenance co-occurrence audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter82_hugsim_support_surface_bridge_cooccurrence`](experiments/iter82_hugsim_support_surface_bridge_cooccurrence/RESULT.md) |
| 83 | **HUGSIM bridge-supported surface-miss decomposition** — decompose released CPA/TTC channels on bridge-supported support-object frames | committed iteration-59 proof/report plus iteration-82 report only; fixed support objects `9` and `10`; same bridge-supported frames recomputed from frozen logs | mixed miss over `18` bridge-supported frames: object `9` is TTC-borderline-only (`3` bridge-supported frames, `1` borderline, zero active; closest active TTC margin `+2.2761 s`), while object `10` has `15` bridge-supported subthreshold frames with zero finite TTC and closest active CPA margin `+5.7464 m` | **`HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE` — active support is blocked by different surface-channel failures in the two support objects** | two-object descriptive bridge-supported surface-miss decomposition only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/retuning claim. [`iter83_hugsim_bridge_supported_surface_miss_decomposition`](experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/RESULT.md) |
| 84 | **HUGSIM selected/support path-arbitration decomposition** — compare released-surface selected objects against provenance-bridged support objects on the same fixed rows | committed iteration-59 proof/report plus iteration-79/80/83 reports only; fixed selected/support rows from iteration 79; all-provenance bridge and CPA/TTC metrics recomputed from frozen logs | all three rows classify `selected_surface_support_bridge_split`: selected objects have lower CPA and better CPA rank in `3/3`, selected bridge support in `0/3`, support bridge support in `3/3`, and one selected object has finite TTC while its support object has no finite TTC | **`HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE` — released hazard-surface selection follows logged path geometry while collision provenance bridges to a different surface-ineligible support object** | three-row descriptive selected/support arbitration decomposition only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter84_hugsim_selected_support_arbitration`](experiments/iter84_hugsim_selected_support_arbitration/RESULT.md) |
| 85 | **HUGSIM path-horizon/provenance-timing decomposition** — make the closest-path horizon and provenance timing explicit for the iteration-84 selected/support split | committed iteration-59 proof/report plus iteration-80/83/84 reports only; same three fixed selected/support rows; CPA horizon and all-provenance bridge recomputed from frozen logs | all three rows classify `path_horizon_support_bridge_timing_split`: selected objects have lower CPA and better CPA rank in `3/3`, selected bridge support in `0/3`, support bridge support in `3/3`, and support best provenance bridge is after the event in `3/3`; selected earlier horizon holds in `1/3` | **`HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE` — released surface selection follows logged path geometry, while provenance aligns with a different support object on a later timing channel** | three-row descriptive path-horizon/provenance-timing decomposition only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter85_hugsim_path_horizon_bridge_timing`](experiments/iter85_hugsim_path_horizon_bridge_timing/RESULT.md) |
| 86 | **HUGSIM bridge-time support-surface replay** — replay support objects at their own best provenance-bridge timestamps from iteration 85 | committed iteration-59 proof/report plus iteration-81/83/85 reports only; exact bridge timestamps from iteration 85, no nearest-row or interpolation fallback | `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`: two rows classified (`support_bridge_time_surface_arrival` for object `9` at `5.5 s`, `support_bridge_time_surface_miss` for object `10` at `4.0 s`), but the active `ttc_medium_a` row has no exact committed decision row at bridge timestamp `6.0 s` | **blocked exact-row replay — useful diagnostics, but no complete three-row bridge-time verdict without a fresh nearest-row/interpolation pre-registration** | three-row descriptive bridge-time support-surface replay only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter86_hugsim_bridge_time_surface_replay`](experiments/iter86_hugsim_bridge_time_surface_replay/RESULT.md) |
| 87 | **HUGSIM interval bridge-time support-surface replay** — resolve iteration-86's missing exact bridge row with a fixed at-or-before logged-row rule | committed iteration-59 proof/report plus iteration-85/86 reports only; exact bridge rows when present, otherwise nearest logged row at-or-before bridge timestamp within `0.5 s`; no future row or interpolation | all three rows classify without blocking: `interval_support_surface_arrival` `1/3` for object `9` at exact `5.5 s`, `interval_support_surface_miss` `2/3` for object `10` at exact `4.0 s` and nearest-before `5.75 s`; replay alignments are exact `2/3`, nearest-before `1/3` | **`HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE` — one support object reaches borderline at bridge time, while the other remains outside the released surface even under interval replay** | three-row descriptive interval bridge-time support-surface replay only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter87_hugsim_interval_bridge_time_surface_replay`](experiments/iter87_hugsim_interval_bridge_time_surface_replay/RESULT.md) |
| 88 | **HUGSIM bridge/surface margin residual decomposition** — pair support-object provenance bridge evidence with iteration-87 replay-row released-surface margins | committed iteration-85/87 reports only; no raw decision logs; fixed support rows from iteration 87 | all three rows classify without blocking: object `9` is `bridge_surface_ttc_borderline_cpa_far` with ambiguous bridge support, replay TTC `4.7761 s`, active TTC margin `+2.2761 s`, and active CPA margin `+20.0208 m`; object `10` is `bridge_surface_no_finite_ttc_cpa_far` in both rows with match bridges, no finite TTC, and active CPA margins `+9.6354/+10.6434 m` | **`HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE` — support-side residuals split into one TTC-borderline/CPA-far case and two no-finite-TTC/CPA-far cases** | three-row descriptive bridge/surface margin residual decomposition only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter88_hugsim_bridge_surface_margin_residual`](experiments/iter88_hugsim_bridge_surface_margin_residual/RESULT.md) |
| 89 | **HUGSIM joint bridge/surface candidate audit** — enumerate every logged object at the iteration-87 replay rows and test for active+bridge candidates | committed iteration-59 proof/report plus iteration-85/87/88 reports only; all logged objects at fixed replay rows; all-provenance bridge and released-surface metrics recomputed from frozen logs | all three rows classify without blocking: active+bridge candidate events `0/3`; bridge-supported objects total `11`; labels split into `no_active_bridge_candidate_support_borderline` `1/3` and `no_active_bridge_candidate_support_subthreshold` `2/3` | **`HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE` — bridge support is common, but no logged object is both active under the released surface and bridge-supported** | three-row descriptive joint bridge/surface candidate audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter89_hugsim_joint_bridge_surface_candidate_audit`](experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/RESULT.md) |
| 90 | **HUGSIM active-surface provenance gap audit** — decompose active released-surface objects against provenance bridge support at the iteration-87 replay rows | committed iteration-59 proof/report plus iteration-87/89 reports only; all logged objects at fixed replay rows; all-provenance bridge and released-surface metrics recomputed from frozen logs | all three rows classify without blocking: `active_surface_absent_bridge_supported_nonactive` `2/3`, `active_surface_present_no_bridge_supported` `1/3`; active object events `1/3`; bridge-supported objects total `11`; active+bridge-supported objects `0`; active/no-bridge objects `1`; bridge-supported non-active objects `11` | **`HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE` — bridge support lands on non-active objects, while the only active object lacks bridge support** | three-row descriptive active-surface/provenance gap audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter90_hugsim_active_surface_provenance_gap`](experiments/iter90_hugsim_active_surface_provenance_gap/RESULT.md) |
| 91 | **HUGSIM active-gap geometry decomposition** — make the path-vs-provenance geometry behind the iteration-90 split explicit | committed iteration-59 proof/report plus iteration-90 report only; all logged objects at fixed replay rows; bridge best-variant geometry and released-surface metrics recomputed from frozen logs | all three rows classify without blocking: `provenance_near_path_inactive` `2/3`, `path_active_provenance_far_with_bridge_nonactive` `1/3`; bridge-supported objects total `11`; active+bridge-supported objects `0`; active-row object `24` is active by path CPA (`min_cpa=1.0010 m`) but bridge `no_support` at `10.9518 m`, while nearest bridge object `10` is subthreshold at `4.2468 m` | **`HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE` — released active surface follows path-near geometry while provenance support points to different non-active objects** | three-row descriptive active-gap geometry decomposition only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter91_hugsim_active_gap_geometry_decomposition`](experiments/iter91_hugsim_active_gap_geometry_decomposition/RESULT.md) |
| 92 | **HUGSIM path-proximity arbitration audit** — compare the CPA/path-best object with the provenance-best bridge-supported object at the fixed replay rows | committed iteration-59 proof/report plus iteration-91 report only; path-best selector is lowest `cpa_rank`; provenance-best selector is lowest bridge distance among supported objects; surface-best recorded for audit | all three rows classify without blocking: path/provenance same-object events `0/3`; labels split across `path_best_no_bridge_provenance_best_nonactive`, `path_best_bridge_supported_nonactive`, and `path_best_active_no_bridge`; active row path/surface-best object `24` is active (`min_cpa=1.0010 m`) but no-support (`10.9518 m`), while provenance-best object `6` is subthreshold at `3.7598 m` | **`HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE` — path proximity and provenance proximity select different logged objects in every fixed row** | three-row descriptive path-proximity/provenance arbitration audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter92_hugsim_path_proximity_arbitration`](experiments/iter92_hugsim_path_proximity_arbitration/RESULT.md) |
| 93 | **HUGSIM surface-winner alignment audit** — classify whether `surface_best` follows `path_best` or `provenance_best` using committed iteration-92 selector proof only | committed iteration-92 report only; no raw decision logs; fixed selector triples from the three replay rows | all three rows classify without blocking: `surface_follows_path_active_no_bridge` `1/3`, `surface_follows_path_nonactive` `1/3`, `surface_follows_provenance_nonactive` `1/3`; surface matches path `2/3`, surface matches provenance `1/3`, path matches provenance `0/3` | **`HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE` — surface winner follows provenance in one row and path in two rows, including the active no-support row** | three-row descriptive selector-alignment audit only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter93_hugsim_surface_winner_alignment`](experiments/iter93_hugsim_surface_winner_alignment/RESULT.md) |
| 94 | **HUGSIM active-row surface margin arbitration** — explain the active `ttc_medium_a` surface/path winner against bridge-supported provenance candidates | committed iteration-91/92/93 reports only; fixed active row at replay `5.75 s`; no raw decision logs and no GPU | one row classifies without blocking as `active_row_cpa_margin_overrides_provenance`: object `24` is the only active/path/surface candidate (`min_cpa=1.0010 m`, `cpa_rank=1`, active CPA margin `-0.4990 m`, bridge `no_support`), while three bridge-supported candidates are subthreshold, TTC-null, and CPA-far; nearest bridge-supported active CPA margin is object `10` at `+10.6434 m` | **`HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE` — in the active row, released surface selection is a CPA/path margin arbitration rather than a near active bridge-provenance tie** | one-row descriptive active-row margin arbitration only; no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/benchmark/HD-Score-invariance/commercial-value/real-world/first-responder/retuning claim. [`iter94_hugsim_active_row_surface_margin_arbitration`](experiments/iter94_hugsim_active_row_surface_margin_arbitration/RESULT.md) |

> **Iteration 1a (2026-06-30):** the NeuroNCAP closed-loop apparatus runs end-to-end on a single GPU
> and produces the genuine per-run metric schema with a *frozen* planner — the engineering risk the
> pre-registration flagged is retired. Proof: [`PROOF_smoke_0103.md`](experiments/iter1_reproduce/PROOF_smoke_0103.md).
>
> **Iteration 1b (2026-06-30):** 60 closed-loop episodes on public-mini scenes. The single clean
> apples-to-apples point — **frontal/0103 = 1.07 vs the published 1.17** — reproduces within
> run-noise; the UniAD failure profile reproduces qualitatively (80–100 % collision in dynamic
> scenarios). Per-scene variance is huge (stationary 5.00 → 1.03), which is exactly why the *averaged*
> baseline needs the gated full trainval set, so no full-baseline claim is drawn here. The real
> payload is a **corpus of 39 frozen-planner collisions** for iteration 2, and a structured
> introspective signal (collisions track `recall@5-15m → 0`). Detail:
> [`PARTIAL_BASELINE.md`](experiments/iter1b_partial_baseline/PARTIAL_BASELINE.md).

---

## How it works — the Sentinel loop

A frozen planner proposes a plan; Sentinel reads the planner's own internal state, scores the risk
that this plan ends in a collision, and — above threshold — triggers a principled intervention
(brake / fallback). All evaluated in a public neural closed-loop simulator.

The apparatus is three public containers on one L4: the NeuroNCAP orchestrator drives the scenario
actor and scores collisions; NeuRAD renders photoreal multi-camera frames from real nuScenes
drives; the frozen UniAD container serves `/infer` with the Sentinel patch env-gated per arm.
Episodes are deterministic per run index (established by the verification pass), so every
comparison is seed-paired. Every run leaves evidence — scores, driven trajectories, per-frame
monitor decisions — which feeds both the research loop and the independent audit:

```mermaid
flowchart TB
  ORCH["NeuroNCAP orchestrator<br/>actor + scoring"] --> REND["NeuRAD renderer<br/>photoreal cameras"]
  REND --> MODEL["frozen UniAD /infer<br/>+ Sentinel patch, env-gated"]
  MODEL -- "trajectory" --> ORCH
  ORCH --> EVID["per-run evidence<br/>scores · trajectories ·<br/>decision logs (committed)"]
  EVID --> H["hypothesize<br/>pre-register the bar"] --> B2["build a patch"] --> R2["run OFF vs arm<br/>seed-paired"] --> M2["measure + ablate<br/>nulls published"] --> H
  EVID --> AUD["independent audit<br/>re-derives every claim;<br/>corrections in place"]
  classDef stack fill:#f3f0fa,stroke:#5e35b1,color:#22163d;
  classDef loop fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef ev fill:#fff8e1,stroke:#b28704,color:#3d2f00;
  classDef audit fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  class ORCH,REND,MODEL stack;
  class H,B2,R2,M2 loop;
  class EVID ev;
  class AUD audit;
```

The monitor is small and the planner is frozen — that is what makes this winnable on single-digit
GPUs and what makes a win *defensible*: any safety gain is attributable to Sentinel, not to a
bigger planner. The label-free trigger reads only what the planner already outputs (its plan, its
detected objects, and their motion) — no ground truth, no privileged sim state. The *risk* term itself
evolved across iterations — from a time-to-collision scalar (iter 2) to a plan-vs-tracked-path
closest-approach test (iter 6); see the score tracker and Status for the honest trajectory.

## The research engine (how we get better every iteration)

Sentinel runs on a disciplined learning loop — hypothesize → build → **measure vs the baseline** →
**attribute (ablate *why*)** → improve — with the win bar frozen up front (`PREREGISTRATION.md`) and
drive-clustered bootstrap CIs on the deltas. The loop is working as intended: iteration 2 produced a
safety win, iteration 2's ablation flagged what the safety metric couldn't separate, and iteration 3
ran that experiment and **overturned an over-claim from iteration 2** — logged and corrected, not
buried. That self-correction is the point. Full design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
(note: the Ed25519-receipt and seed-sweep machinery described there is design intent carried over from
[PerceptionProof](https://github.com/manfromnowhere143/perceptionproof); it is **not yet wired into the
Sentinel runs**, which is stated here rather than implied).

## Status — where it really stands (the honest current truth)

The full iteration-by-iteration arc — including the iteration-3 self-correction, the
selectivity/side-blindness trade of iterations 4–7, and the three refuted evasion designs — is
kept, with every number and link, in [`docs/CAMPAIGN.md`](docs/CAMPAIGN.md). The summary table
above is the same history in one screen.

**Net, stated plainly — 52 completed mechanism iterations plus an independent verification pass,
with iteration 37 closed as a pre-registered calibration null, iteration 38 active at S0
(calibration deprioritized), iterations 39/40/41 completed as defensibility audits (claim
narrowing; timing/cost budget; degradation replay-support null), iteration 42 completed as
the exact-trace replay-support pass — offline replay reproduces every online monitor decision
exactly — iteration 43 completed as the authorized object-stream perturbation gate with a
mild-fragile finding: in replay, 5 cm per-frame position jitter already breaks the frozen
stability bars (mostly by adding false interventions), while detection dropout, score
attenuation, and identity churn stay stable at mild levels — and iteration 44 completed as the
velocity temporal-smoothing repair gate with a no-repair null: all four frozen smoothed
estimators halve the jitter over-firing but erase 15-21 genuine interventions on the clean
trace, so the fragility is not repaired by low-pass filtering the velocity and the released
union stands unchanged — iteration 45 completed as the HUGSIM infrastructure-gate pass that
opens the second-benchmark transfer lane, iteration 46 completed as the HUGSIM Stage-1
monitor-OFF baseline completion null (38 of 52 episodes; the seven `load_HD_map` scenarios
blocked on the unstaged map-expansion pack), iteration 47 completed as the completion
pass: Stage A staged that pack with provenance receipts, Stage B completed all 14 failed
episodes first-attempt, and the full 52-episode monitor-OFF arm now stands — and iteration 48
completed as THE transfer verdict of the second-benchmark line, a **transfer null**: all 104
OFF-vs-released-union HUGSIM episodes completed under the seven NeuroNCAP-frozen parameters
with zero retuning, the monitor fired and braked in 37/52 ON episodes (26.9% pooled brake
frames, 134 latch releases, no RC collapse), and the mean paired HD-Score delta is −0.017
with a 95% scenario-clustered CI [−0.055, +0.026] that includes zero — the NeuroNCAP benefit
does not measurably transfer to HUGSIM easy+medium scenarios at this N, and the null stands
as the measured external-validity boundary of the released union.**
The
**released union (iteration 15) is the best configuration** of the campaign: at the 20-run
power scale it lifts the independently reproduced baseline **2.12 → 2.91 (CI [+0.605, +0.928])**,
keeps clean scenes identical to the unmonitored planner, and strictly dominates the plain union
(identical safety on every cell, safe-progress +0.246, CI [+0.206, +0.293]). Its
deployment-metric effect vs the unmonitored planner is a **tight null** (−0.03, CI [−0.13,
+0.07]) — the safety is bought at approximately zero net deployment cost, and iteration 16
proved the residual is not recoverable by softening the stop. The mini-scene deployment win
stands as measured there (+0.398, [+0.133, +0.665], 20 unique episodes/scene — re-established
after the original pooled version was withdrawn by audit). The frontal head-on *ceiling* is
firmly established — a committed stop is the best frontal response, and **three separate evasion
designs (iters 9, 10, 11) were tested and honestly refuted**, all worse than stopping, the last
one dangerous on false alarms (re-confirmed at n=20: 25% clean-scene collisions vs OFF's 10%).

**Data-scope checkpoint.** Iterations 1-17 and the power run used real NeuroNCAP/NeuRAD closed-loop
evidence on public nuScenes scenes; iterations 19, 21, 22, and 23 used the registered non-evaluation
or evaluation-only extraction surfaces available at the time. They were not mock-data runs. But they
also did **not** use the full official `/datasets/nuscenes-full` trainval root, because that root did
not exist until iteration 28. Iterations 24-27 are the audit trail that proved the blocker and staged
the remedy. Iteration 29 is therefore the first research gate on the newly staged official trainval
root, and iteration 30 is the first diagnostic localization gate on that root's committed research
evidence.

**What's next.** The benchmark campaign is complete and consolidated. Iterations 22, 23, 24, 25,
and 26 are closed as Stage 1 data/availability/infrastructure/capacity nulls; iterations 27 and 28
closed the storage and official trainval staging blockers; iteration 29 passed the first
full-trainval support atlas while failing the optional strict-collapse note; iteration 30 passed
the diagnostic localization gate over committed iter29 evidence; iteration 31 stopped at S0
because alpha `0.00` failed to reproduce the committed iteration-29 baseline; iteration 32 passed
the narrow prefix-replay baseline-recovery audit by restoring exact iteration-29 parity on the
same frozen target rows; iteration 33 repaired the nonzero-intervention S0 canary but then stopped
as a calibration null because no nonzero alpha passed the frozen S1 selection bars; iteration 34
then closed the same global bridge-centroid direction for scale-only successor work with a
post-result dose-response audit null; iteration 35 then showed real row-level heterogeneity but
no actionable frozen baseline-geometry stratum. Iteration 36 then passed a diagnostic bridge-site
decomposition audit: `track_query` and four trajectory-query slots carry enough scene-robust
signal to justify a separate site-specific intervention pre-registration. Iteration 37 ran that
site-specific test through S0 and the full calibration grid, then stopped as a calibration null:
no nonzero alpha passed the frozen positive-movement bars. Iteration 38 is now the fresh
post-result pre-registration for the exact opposite track-query direction; its tooling/tests,
offline direction artifact, and S0 canary proof are committed. Calibration is authorized by the
registered gate but not launched. It is deprioritized: the 2026-07-11 intervention-mechanism
verdict
([docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md](docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md))
closes the linear-centroid family after five consecutive pre-registered nulls. No heldout
intervention replay, iteration-12, selector,
closed-loop work, deployment language, or safety claim is authorized unless its registered gates
advance. Iteration 39 then audited the active paper/repository story against external-validity
pressure, found three active-doc wording problems, and narrowed them in place. Iteration 40 then
quantified full14/power simulation intervention budget and reconstructable lead time: `1,205`
brake frames over `10.79 km`, `230/400` intervention episodes, and `61` measured lead-time
episodes with median `1.30 s`. Iteration 41 then tested the next sensor/input-degradation
prerequisite and stopped at S0: exact timestamp lookup into committed `p14-best` ego poses missed
`1,388/6,474` timestamped monitor frames across all `400` episodes, so the registered
world-frame replay could not be run and perturbations were skipped. Given the current maturity of
the benchmark result, external-validity falsification now has priority when it conflicts with
incremental mechanism search. Iteration 42 completed that replay-support remedy: the new
best-arm trace logs the exact `ego2world` transform with every monitor row, and offline replay
reproduced every online decision exactly (`0` mismatches over `6,474` frames). Iteration 43 then
ran the single authorized successor — the offline object-stream perturbation gate over that
trace — and published `OBJECT_PERTURBATION_MILD_FRAGILE`: position jitter at `0.05`–`0.10 m`
breaks the frozen stability bars, dominated by false interventions (`17` and `36` new
intervention episodes against the `<=8` bar), while dropout, score attenuation, and identity
churn hold at their mild levels. Iteration 44 then tested the natural repair under a fresh
pre-registration — temporally smoothed velocity estimators (two-/three-frame finite difference
and EMA) over the same trace and seed-paired jitter grid — and published
`VELOCITY_SMOOTHING_NO_REPAIR_NULL`: smoothing halves the over-firing but never reaches the
bar, and it erases `15`–`21` of the `230` genuine online interventions outright on the
unperturbed trace, so the temporal-smoothing repair line is closed at these parameters and any
successor needs a fresh pre-registration. Iteration 45 then opened the second closed-loop
benchmark family, passing the HUGSIM infrastructure gate on the same frozen checkpoint.
Iteration 46 ran the frozen Stage-1 monitor-OFF baseline — 52 scheduled episodes (26 scenarios
x 2 back-to-back runs, fixed by the D0 stochasticity verdict) — and published a completion
null at `38/52`: the seven `load_HD_map` scenarios failed on the unstaged nuScenes
map-expansion pack, so the Stage-2 pre-registration was not authorized; the within-scenario
spread (median |ΔHD| `0.0245` over 19 pairs) is committed Stage-2 design evidence. Iteration
47 then completed as the pre-registered completion pass: Stage A staged the official
map-expansion pack v1.3 with redacted provenance receipts and passed all bars; Stage B — the
14-episode completion re-run under the carried stochastic verdict — completed all 14 episodes
on the first attempt, and ONE analyzer run over all 52 passed C1/C2/C3 with carried integrity
`104/104` files and the pairing falsifier not fired over all 26 pairs (median |ΔHD| `0.0251`,
heavy-tailed to `0.7419`). Iteration 48 then ran the authorized Stage-2 transfer gate — the
released union under the seven NeuroNCAP-frozen parameters against the monitor-OFF planner,
104 within-launch back-to-back paired episodes — and published `TRANSFER_NULL` at full
weight: the frozen rule fires, latches, and releases on HUGSIM (37/52 ON episodes, 26.9%
pooled brake frames, no F2 over-firing, no F3 RC collapse), and the mean paired HD-Score
delta is `−0.0166` with 95% scenario-clustered CI `[−0.0551, +0.0255]` — no detectable
outcome change. That null is THE transfer verdict of the second-benchmark line and the
measured external-validity boundary of the released union. Iteration 49 then ran the
registered hard/extreme-tier successor and published the same answer under denser collision
opportunity: all `104` episodes completed, the frozen rule braked in `40/52` ON episodes,
F1/F2/F3/F5 did not fire, and mean paired HD-Score delta was `−0.0089` with CI
`[−0.0438, +0.0203]`. Iteration 50's frozen P1 resolves Branch B on that result:
`51/52` OFF episodes had primary collision opportunity, yet the benefit still did not port,
so the transfer failure is real, not opportunity-scarce. Iteration 51 then decomposed the
published HUGSIM nulls offline: over the combined 104 paired transfer episodes, only `6/91`
OFF-opportunity pairs converted from collision to no collision, `85/104` pairs remained
collision-persistent, and the frozen dominance rule returned `mixed_taxonomy` rather than one
single-cause failure. Iteration 52 then tightened the timing side of that mechanism audit:
among `92` ON-collision episodes, `57` were absent/post-collision braking while `35` had
pre-collision braking, including `26` long-lead cases that still collided; every no-brake
case also had zero frozen TTC/CPA surface-proxy rows. Iteration 53 then reconstructed the
actual first-fire side of the released OR predicate: ON-collision first fires split as
TTC-only `36`, CPA-only `33`, no-fire `22`, both `1`, and the pre-collision-fire subset split
CPA-only `19` / TTC-only `16`, so the failure is not one bad union branch. Iteration 54 then
audited provenance support: monitor-side first-fire argmins reconstruct cleanly (unique TTC
object `40`, unique CPA object `36`, both-distinct `1`, no-fire `27`), but HUGSIM collision
actor identity is not logged in any committed eval (`0/104` supported), so actor matching
requires new instrumentation. Iteration 55 then verified the frozen HUGSIM source checkout and
mapped the source-level instrumentation route to `sim/utils/score_calculator.py` and
`closed_loop.py`; it authorizes only a future no-metric-change instrumentation pre-registration,
not a run or actor attribution. Iteration 56 then drafted that first patch shape, but the
registered static verifier returned `INSTRUMENTATION_PATCH_DESIGN_NULL`: the patch applied and
compiled, yet the guard rejected the added `if score_nc == 0.0:` branch as metric/control
sensitive. Iteration 57 bound the same patch SHA and refined the static guard; the byte-identical
patch now passes as additive by source diff inspection, but no HUGSIM execution or actor-match
claim exists. Iteration 58 then applied that byte-bound patch on the frozen HUGSIM stack for the
registered `scene-0013-hard-00` OFF/ON canary and returned `PROVENANCE_CANARY_COMPLETE`: both
`eval.json` files kept the scalar metric schema and scalar-only `details` rows, and both emitted
top-level `collision_provenance` lists (counts `11` and `13`). This is only an instrumentation
execution pass, not actor matching or HD-Score invariance. Iteration 59 then ran the bounded
actor-match support audit: eight registered ON episodes completed, three rows were classifiable
foreground comparisons, and all three were `actor_mismatch` by the frozen bridge; the other rows
were no-fire, post-fire, or background-only. Iteration 60 stress-tested those three rows under
48 frozen bridge variants. No variant made a match, but one row became ambiguous at `5.6649 m`,
so the correct verdict is `BRIDGE_AMBIGUOUS_NULL`, not robust all-row mismatch. Iteration 61
then compared every first-fire monitor object to every eligible foreground provenance row. One
row (`ttc_extreme_b`) has a non-triggering object match (`object_id=16`, `2.0686 m`) while the
trigger remains ambiguous; the other two rows have no first-fire object support. Iteration 62
then reconstructed the first-fire ranks for that matched object: it was visible but subthreshold
(`min_cpa=22.7648 m`, CPA rank `9/9`, `ttc=null`), while the actual trigger was TTC-only on
`object_id=1`. Iteration 63 then followed that same object through the pre-contact window:
present in 13 frames, zero hazard frames, zero borderline frames, min CPA `12.1690 m`, no valid
TTC. Iteration 64 then expanded the two first-fire-unsupported rows to all pre-contact objects;
both gained object-surface matches (`1.6718 m`, `0.4325 m`). Iteration 65 reconstructed those
matched objects at their matched timestamps and found both subthreshold (`12.7240 m` CPA /
`3.5763 s` TTC, and `9.3179 m` CPA / no TTC). Iteration 66 then followed those target objects:
`object_id=2` becomes a TTC hazard at first fire, while `object_id=6` remains visible-never-active.
Iteration 67 compared first-fire trigger objects to those targets: `cpa_medium_b` is split-object,
but both trigger and target have later full-window bridge support while the trigger lacks bridge
support at the actual first-fire timestamp. Iteration 68 decomposed that fire-time gap into one
before-fire support case and one after-fire support case. Iteration 69 then synthesized all eight
iteration-59 rows into one taxonomy: five structural rows stay structural, while the three
classifiable rows split into non-trigger visible-never-hazard, same-object late-fire, and
split-object visible-never-active mechanisms. Iteration 70 refined those five structural rows:
two foreground-present rows are surface-silent, two foreground-present rows are late-fire
(`+1.75 s` after first foreground contact), and one row is foreground-absent/background-only.
Iteration 71 then audited the two surface-silent rows' frozen trigger margins before foreground
contact; both were far-margin rows, not near misses against the registered CPA/TTC bands.
Iteration 72 then audited the two late-fire rows' pre-foreground margins; both were near a frozen
trigger surface before contact, but not crossing, and first fire still arrived `+1.75 s` after
first foreground contact.
Iteration 73 then put all four foreground-present structural rows on one transition timeline:
the silent rows never become active anywhere in the committed decision logs, while the late-fire
rows are near before contact and first active only `+1.75 s` after contact.
Iteration 74 then classified the two late-fire rows' delay barrier: both are cross-channel cases,
with CPA-near becoming TTC-active in one row and TTC-near becoming CPA-active in the other.
Iteration 75 then resolved that handoff at object level: both rows switch responsible monitor
object across the channel handoff (`5` -> `9`, `6` -> `24`).
Iteration 76 then tested those switched objects against the HUGSIM foreground provenance under
the fixed bridge grid; neither side of either switch reached match or ambiguous support.
Iteration 77 then expanded from selected switched objects to full event-row object sets: foreground
support reappeared in mixed form, showing support can exist in the monitor stream while the
selected hazard object remains wrong or unsupported.
Iteration 78 then ranked the foreground-supported objects themselves against the logged monitor
surface. All three fixed support events are `support_object_nonselected_subthreshold`: the support
objects are not the selected event objects and do not cross the active or borderline CPA/TTC bands.
Iteration 79 then decomposed the selected objects in those same rows: two selected objects are
borderline and one is active, while the foreground-supported objects remain subthreshold.
Iteration 80 then tested the selected active/borderline objects against every logged provenance
row, without filtering by class; all eligible rows were foreground and the selected objects still
reached no match or ambiguous support.
Iteration 81 then followed the foreground-supported support objects through every committed ON
decision frame. The support-object branch is mixed: `both_distinct_extreme` support object `9`
later becomes borderline at `5.5 s` and active at `7.0 s`, while `ttc_medium_a` support object
`10` remains visible-never-surface across `15` frames.
Iteration 82 then tested same-object co-occurrence between foreground bridge support and the
released surface. Both fixed support objects have bridge support, but only object `9` has
surface co-occurrence, and only at the borderline level (`1` borderline+bridge frame, zero
active+bridge frames); object `10` has bridge support in `15/15` present frames and never
reaches active or borderline surface.
Iteration 83 then decomposed the bridge-supported frames by released surface channel: object `9`
is a TTC-borderline-only miss, while object `10` is bridge-supported but has no finite TTC and
stays CPA-far from active.
Iteration 84 then answered the selected/support arbitration question: all three fixed rows have
selected objects with stronger logged path geometry (lower CPA and better CPA rank), zero
selected provenance bridge support, and support objects with better foreground/provenance bridge
support.
Iteration 85 then made the closest-path horizon and provenance timing explicit: all three rows
retain the same selected-path/support-bridge split, support best provenance bridge is after the
event timestamp in `3/3`, and "selected earlier horizon" is only `1/3`, so the robust mechanism
statement is path-geometry selection versus later support-object provenance, not a universal
earlier-horizon rule.
Iteration 86 then attempted an exact bridge-time support-surface replay and correctly blocked:
two rows classified, but the active `ttc_medium_a` bridge timestamp `6.0 s` has no exact
committed ON decision row, so nearest-row or interpolation logic now requires its own fresh
pre-registration.
Iteration 87 then resolved that exact-row block with a registered at-or-before interval replay:
object `9` reaches borderline at exact `5.5 s`, while object `10` remains subthreshold at exact
`4.0 s` and nearest-before `5.75 s`, so support-side provenance timing is mixed rather than a
uniform surface-arrival story.
Iteration 88 then paired that replay result with support bridge evidence and surface margins:
object `9` is TTC-borderline but CPA-far, while object `10` has no finite TTC and remains CPA-far
in both replay rows.
Iteration 89 then enumerated all logged objects at the replay rows: `11` objects are
bridge-supported across the three rows, but zero are both active under the released surface and
bridge-supported.
Iteration 90 then decomposed the active side of that split: two rows have no active object but do
have bridge-supported non-active objects, and the one row with an active object has no bridge
support for that active object while bridge-supported objects remain non-active.
Iteration 91 then made the split geometric: the active row's active object is path-near but
provenance-far, while the bridge-supported objects are provenance-near but path-inactive.
Iteration 92 then made the arbitration object explicit: CPA/path-best and provenance-best differ
in all three fixed replay rows, so path proximity and provenance proximity do not select the same
logged object.
Iteration 93 then showed the surface winner is mixed: it follows provenance in one row and path in
two rows, including the active no-support row.
Iteration 94 then explained that active row's path-following branch: object `24` is the only
active/path/surface candidate, while all three bridge-supported provenance candidates are
subthreshold, TTC-null, and CPA-far.
This is a mechanism-cause audit, not a repair or population-rate claim. Successors now require
fresh pre-registrations. The
published RealADSim closed-loop anchor range remains loose context only —
it supports no performance statement:

- **The manuscript — full draft and compiled PDF committed**
  ([`docs/paper/`](docs/paper/MANUSCRIPT.md)); the arXiv submission package is built and the
  arXiv submission is in moderation/announcement watch.
- **Iteration 22 is completed as an S0 data-null.**
  [`experiments/iter22_causal_planner_interpretability/RESULT.md`](experiments/iter22_causal_planner_interpretability/RESULT.md)
  reports that baseline extraction completed, but the committed timestamp join failed on all
  1,507 non-reset rows and the frozen heldout split had 0 GT frames. Stage 1 stopped before probe
  fitting, activation directions, intervention replay, iteration-12 scoring, or closed-loop work.
  Any successor requires a fresh pre-registration.
- **Iteration 23 is completed as a count-floor data-null.**
  [`experiments/iter23_s0_hardened_causal_localization/RESULT.md`](experiments/iter23_s0_hardened_causal_localization/RESULT.md)
  reports that the hardened S0 surface passed: deterministic canary, 2,627/2,627 full joins, zero
  error rows, and stable primary tensor shapes. The next frozen gate failed before learning:
  collapse-positive frames were 0 in every split, eligible-intervention frames were 0, and heldout
  danger positives were 17 below the 30-frame floor. Stage 1 stopped before probe fitting,
  activation directions, intervention replay, iteration-12 scoring, or closed-loop work.
- **Iteration 24 is completed as a fresh risk-support availability-null.**
  [`experiments/iter24_risk_support_atlas/RESULT.md`](experiments/iter24_risk_support_atlas/RESULT.md)
  reports that the known-data firewall ran first, then the availability manifest found 0 eligible
  fresh scenes, 0 planned keyframes, and 0 heldout keyframes after 582 post-firewall candidates
  all missed local six-camera files. It stopped before canary extraction, full extraction, label
  atlas, probe fitting, activation intervention, iteration-12 scoring, selector evaluation, or
  closed-loop work. A successor needs a fresh pre-registration and an explicit data-staging plan.
- **Iteration 25 is completed as a staged-data inventory infrastructure-null.**
  [`experiments/iter25_staged_data_inventory/RESULT.md`](experiments/iter25_staged_data_inventory/RESULT.md)
  reports that the frozen root inventory inspected only five pre-declared local roots. Only
  `/datasets/nuscenes` exists, and after the known-data firewall it still had 0 eligible fresh
  scenes, 0 planned keyframes, and 0 heldout keyframes; the other four roots were missing. It
  stopped before any data download/copy, model extraction, labels, probes, interventions,
  iteration-12 scoring, selector evaluation, or closed-loop work.
- **Iteration 26 is completed as a data-staging remedy capacity-null.**
  [`experiments/iter26_data_staging_remedy/RESULT.md`](experiments/iter26_data_staging_remedy/RESULT.md)
  answers the operational question: yes, the missing data is the official nuScenes v1.0 trainval
  sensor file blobs; no governed bucket copy currently contains them; and the current GPU disk is
  too small. The next action is storage provisioning plus a later staging pre-registration, not a
  model run.
- **Iteration 27 is completed as a storage-provisioning pass.**
  [`experiments/iter27_storage_provisioning/RESULT.md`](experiments/iter27_storage_provisioning/RESULT.md)
  reports that `sentinel-gpu` now has `sentinel-nuscenes-data-1tb`, a persistent 1024 GB
  `pd-balanced` disk, mounted at `/datasets/nuscenes-full` with `1,026,108,792,832` bytes
  available. It moved 0 dataset bytes and launched 0 Docker/model/NeuroNCAP runs. The next action
  is a fresh data-staging pre-registration, not an unregistered download or model run.
- **Iteration 28 is completed as an official nuScenes trainval staging/availability pass.**
  [`experiments/iter28_nuscenes_trainval_staging/RESULT.md`](experiments/iter28_nuscenes_trainval_staging/RESULT.md)
  reports 11 official archives staged with SHA/byte proofs (`314,886,603,672` bytes total),
  extraction safety PASS (`0` unsafe members across `2,631,374` tar members), six camera channels
  present (`34,149` files each), and availability PASS with `532` fresh post-firewall train scenes,
  `21,461` eligible keyframes, and `5,360` heldout keyframes. This is a data-root pass, not a
  model result; the next action must be a fresh research pre-registration.
- **Iteration 29 is completed as a full-trainval risk-support pass.**
  [`experiments/iter29_trainval_risk_support_atlas/RESULT.md`](experiments/iter29_trainval_risk_support_atlas/RESULT.md)
  reports S0c full extraction integrity PASS (`21,461/21,461` joined non-reset rows, zero error
  row types, stable shapes/dtypes) and S1 support PASS for `low_diversity_1p5` under `danger_4p5`.
  The optional strict-collapse note failed (`eligible_strict` `0/0/1` across
  fit/calibration/heldout), so successor work may use only low-diversity language unless a new
  strict-collapse pre-registration passes. No probe fitting, activation direction, intervention,
  iteration-12 scoring, selector evaluation, or closed-loop work is authorized.
- **Iteration 30 is completed as a full-trainval diagnostic localization pass.**
  [`experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`](experiments/iter30_full_trainval_lowdiv_localization/RESULT.md)
  reports that the committed iter29 hashes/counts reproduced exactly, then the frozen
  motion/planning-bridge tensor probe separated `eligible_lowdiv` from benign controls on heldout
  scenes (AUROC `0.950`, AP `0.615`, balanced accuracy `0.867`) with large margins over metadata
  (AUROC `0.596`) and ego-plan-kinematic controls (AUROC `0.674`). Scene-cluster bootstrap
  robustness passed (AUROC p05 `0.922`). This is diagnostic evidence only: it authorizes only a
  separate causal-intervention pre-registration, not activation patching, iteration-12 scoring,
  selector evaluation, GPU work, or closed-loop work.
- **Iteration 31 is completed as a bridge-intervention S0 infrastructure-null.**
  [`experiments/iter31_full_trainval_bridge_intervention/RESULT.md`](experiments/iter31_full_trainval_bridge_intervention/RESULT.md)
  reports that the fit-only direction artifact was committed and the S0 canary repeated hashes
  were deterministic, but alpha `0.00` failed the frozen baseline reproduction bar against
  iteration-29 originals (`24` rows checked, `96` comparison failures, max coordinate error
  `30.222413063049316` m). Stage 1 stopped before calibration replay, heldout replay,
  iteration-12 scoring, selector evaluation, or closed-loop work.
- **Iteration 32 is completed as a prefix-replay baseline-recovery pass.**
  [`experiments/iter32_prefix_replay_baseline_recovery/RESULT.md`](experiments/iter32_prefix_replay_baseline_recovery/RESULT.md)
  reports that the exact 12 iter31 canary target rows reproduce iteration-29 baseline model and
  GT outputs when each scene is replayed from sample index `0` through the last target index
  (`44` total replay rows). This authorizes only a fresh prefix-preserving intervention
  pre-registration; it does not authorize calibration, heldout, iteration-12, selector, GPU
  closed-loop, or safety claims.
- **Iteration 33 is completed as a prefix-preserving bridge-intervention calibration null.**
  [`experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md`](experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md)
  reports that S0 passed, then the full calibration grid ran all frozen alphas with exact
  `4293/2452/1841` row counts per cell and zero error rows. No nonzero alpha was usable: alpha
  `1.00`, the strongest cell, reached only `0.0308 m` median eligible endpoint-spread delta and
  `0.1296` fraction above `0.25 m`. Heldout, iteration-12, selector, closed loop, and
  safety claims remain unauthorized.
- **Iteration 34 is completed as an offline direction-specificity audit null.**
  [`experiments/iter34_direction_specificity_audit/RESULT.md`](experiments/iter34_direction_specificity_audit/RESULT.md)
  reports S0 artifact/row integrity PASS, then S1 dose-response NULL: only `74/108`
  `eligible_lowdiv` rows had nonnegative endpoint-spread slope (`0.685185` vs the frozen `0.70`
  bar). The same global bridge-centroid direction is closed for scale-only successor work from
  these artifacts; heldout, iteration-12, selector, closed-loop, and safety claims remain
  unauthorized.
- **Iteration 35 is completed as an offline response-heterogeneity audit null.**
  [`experiments/iter35_response_heterogeneity_audit/RESULT.md`](experiments/iter35_response_heterogeneity_audit/RESULT.md)
  reports S1 heterogeneity PASS (`42/108` eligible rows with endpoint-spread slope `>=0.05`,
  `34/108` with slope `<0`, IQR `0.126519 m/alpha`), but S2 found no frozen
  baseline-geometry stratum with enough target response and benign support. Row-conditioned
  successor work from the same global direction is therefore unauthorized.
- **Iteration 36 is completed as a bridge-site decomposition diagnostic pass.**
  [`experiments/iter36_bridge_site_decomposition/RESULT.md`](experiments/iter36_bridge_site_decomposition/RESULT.md)
  reports full-bridge reproduction plus five passing non-global sites. `track_query` is the
  strongest frozen site (AUROC `0.970531`, AP `0.726416`, bootstrap AUROC p05 `0.950589`).
  This authorizes only a fresh site-specific intervention pre-registration, not a causal,
  selector, closed-loop, deployment, or safety claim.
- **Iteration 37 is completed as a track-query site intervention calibration null.**
  [`experiments/iter37_track_query_site_intervention/RESULT.md`](experiments/iter37_track_query_site_intervention/RESULT.md)
  reports S0 canary PASS, exact calibration replay counts for all alphas, zero context
  contamination, and no selected nonzero alpha. The strongest nonzero alpha by dose, `1.00`, had
  eligible median endpoint-spread delta `-0.041940 m`, fraction `>0.25 m` `0.074074`, and median
  best-candidate-gap delta `-0.001315`, below the frozen positive-movement bars. Heldout replay,
  iteration-12 scoring, selector evaluation, closed-loop work, deployment language, and safety
  claims remain unauthorized.
- **Iteration 38 is pre-registered as a track-query opposite-direction gate.**
  [`experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md`](experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md)
  freezes the exact sign-reversed `sdc_track_query` centroid hypothesis. The offline direction
  builder, UniAD patch, feeder, run scripts, analyzer, and tests are now added, and the direction
  artifact is committed with an exact negative-of-iter37 sign-equivalence receipt. S0 canary
  passed: alpha-zero parity restored, alpha `0.50` changed `track_query` on `24/24` target rows,
  and `sdc_traj_query_last` stayed unchanged on `24/24`. Calibration is authorized but not
  launched. It is deprioritized: the 2026-07-11 intervention-mechanism verdict
  ([docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md](docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md))
  closes the linear-centroid family after five consecutive pre-registered nulls.
  It may test only whether the iter37 causal handle was real with the opposite sign; it
  does not rescue iter37 and authorizes no heldout, iteration-12, selector, closed-loop,
  deployment, or safety claim unless calibration and heldout pass.
- **Iteration 39 is completed as an external-validity claim audit and doc-narrowing result.**
  [`experiments/iter39_external_validity_claim_audit/RESULT.md`](experiments/iter39_external_validity_claim_audit/RESULT.md)
  reports S0/S1/S2 PASS, then S3 found three active-doc wording problems. The report and
  manuscript titles were narrowed to frozen UniAD with measured cross-planner limits, and
  ambiguous certification-like wording was removed. The post-narrowing scanner passed with zero
  findings. This creates no new empirical result; it makes the claim boundary harder to dismiss.
- **Iteration 40 is completed as a timing and intervention-cost audit.**
  [`experiments/iter40_timing_cost_audit/RESULT.md`](experiments/iter40_timing_cost_audit/RESULT.md)
  reports full14/power simulation cost coverage: `400/400` best episodes joined, `1,205` brake
  frames over `10,789.9 m`, `111.68` brake frames/km, `230/400` intervention episodes, and `61`
  measured lead-time episodes with median `1.30 s`. It authorizes only scoped simulation timing
  and brake-budget wording, not wall-clock latency, passenger comfort, production cost,
  deployment readiness, or real-world safety language.
- **Iteration 41 is completed as a monitor-input degradation infrastructure null.**
  [`experiments/iter41_sensor_input_degradation_gate/RESULT.md`](experiments/iter41_sensor_input_degradation_gate/RESULT.md)
  reports that the committed full14/power evidence cannot support the registered exact
  world-frame replay: `1,388/6,474` timestamped monitor frames had no exact matching committed
  `p14-best` ego pose, across `400/400` episodes. No perturbation bars were reached, and no
  object-stream, camera, degraded-sensor, closed-loop, deployment, or safety robustness claim is
  authorized.
- **Iteration 42 is completed as the exact trace replay-support pass.**
  [`experiments/iter42_exact_trace_replay_support/RESULT.md`](experiments/iter42_exact_trace_replay_support/RESULT.md)
  commits a best-arm-only full14/power exact trace (`400` episodes, `6,474` frame rows, each
  carrying the exact online `ego2world`) and proves offline replay identity: every online
  fired/brake/release/latch decision reproduced with `0` mismatches. It authorizes only a future
  offline object-stream perturbation pre-registration over that committed trace — no degradation
  perturbation, selector, closed-loop, deployment, or safety claim.
- **Iteration 43 is completed as the object-stream perturbation gate, a mild-fragile finding.**
  [`experiments/iter43_object_stream_perturbation_gate/RESULT.md`](experiments/iter43_object_stream_perturbation_gate/RESULT.md)
  reports zero-strength replay identity through the reused iteration-42 rule, then the frozen
  14-cell grid: position jitter fails the mild bars at `0.05 m` (retention `218/230`, `17` new
  interventions) and `0.10 m`, with a monotonic false-intervention dose-response up to `151`
  new interventions at `1.00 m`; detection dropout, score attenuation, and identity churn pass
  their mild cells. This is replay decision-flip sensitivity of the monitor rule only — not
  sensor degradation, not closed-loop, and not a deployment or safety claim; the offline line
  at this trace is closed.
- **Iteration 44 is completed as the velocity temporal-smoothing repair gate, a no-repair null.**
  [`experiments/iter44_velocity_smoothing_gate/RESULT.md`](experiments/iter44_velocity_smoothing_gate/RESULT.md)
  reports exact neutral-parameter identity and field-for-field seed-paired reproduction of the
  iteration-43 jitter cells, then the frozen verdict grid: all four registered smoothed
  estimators (`fd_k2`, `fd_k3`, `ema_a0p5`, `ema_a0p3`) fail baseline fidelity on the
  unperturbed trace (retention `209-215/230` vs the `>= 225` bar; `5-6` invented interventions)
  and fail jitter repair (`11-20` new interventions vs the `<= 8` bar). Smoothing measurably
  shrinks the over-firing channel but deletes genuine interventions, so the rule's decision
  boundary sits on one-frame velocity transients; the released union is unchanged, and no
  sensor, closed-loop, deployment, or safety claim is made.
- **Iteration 45 is completed as the HUGSIM infrastructure gate, a pass.**
  [`experiments/iter45_hugsim_infra_gate/RESULT.md`](experiments/iter45_hugsim_infra_gate/RESULT.md)
  opens the second closed-loop benchmark family: the XDimLab/HUGSIM scene release is staged on
  the data disk with a per-file SHA256 manifest, the HUGSIM simulator environment and the
  unmodified UniAD_SIM client (running the SAME frozen NeuroNCAP `uniad_base_e2e.pth`) are
  installed, and one monitor-OFF scenario (`scene-0013-easy-00`, chosen by a frozen
  lexicographic rule) runs closed-loop end-to-end through the named-pipe interface, producing
  a finite HD-Score output and per-step logs. This proves only that the pipeline runs: no
  transfer, benchmark, robustness, deployment, or safety claim, and it authorizes only the
  Stage-1/2 pre-registration of the transfer line.
- **Iteration 46 is completed as the HUGSIM Stage-1 monitor-OFF baseline, a completion null.**
  [`experiments/iter46_hugsim_off_baseline/RESULT.md`](experiments/iter46_hugsim_off_baseline/RESULT.md)
  ran the frozen 52-scenario easy+medium subset under a hard provenance gate. The D0 probe
  recorded the HUGSIM closed loop as **stochastic** (no seed surface), fixing the schedule at
  the first 26 scenarios x 2 back-to-back runs. 38 of the 52 episodes completed with finite
  HD-Scores and per-step pairing logs (all on attempt 1); the seven scheduled scenarios whose
  released yamls set `load_HD_map: true` failed both attempts before the client's first step
  on a missing nuScenes **map-expansion** JSON — a staging gap (iteration 28 staged trainval
  metadata and sensor blobs, never the map-expansion pack), cleanly separated from client
  stability by the control case: the one `-medium-01` scenario without the flag passed. The
  registered dual-failure falsifier fired, C1 failed, and the null publishes at full weight:
  the Stage-2 OFF-vs-released-union pre-registration is NOT authorized. The within-scenario
  stochastic spread (median |ΔHD| `0.0245` over 19 pairs, heavy-tailed to `0.31`) is committed
  Stage-2 design evidence for a successor. OFF arm only; no transfer, monitor, benchmark,
  deployment, or safety claim.
- **Iteration 47 completed as the map-expansion staging + OFF-baseline completion PASS.**
  [`experiments/iter47_map_staging_and_off_completion/RESULT.md`](experiments/iter47_map_staging_and_off_completion/RESULT.md).
  Iteration 46's null stands as published; completion was re-earned, not retroactively
  repaired. Stage A **passed**: the official nuScenes map-expansion pack v1.3
  (`398,535,531` bytes, SHA256-receipted, redacted public-bucket provenance, `0` unsafe zip
  members) is staged at `/datasets/nuscenes-full/maps/expansion/` with all four vector-map
  JSONs present
  ([`proof-staging/staging_receipts.json`](experiments/iter47_map_staging_and_off_completion/proof-staging/staging_receipts.json)).
  Stage B **passed**: behind a hard provenance gate re-verifying every frozen iteration-46
  value, all 14 formerly failed `load_HD_map` `-medium-01` episodes completed on the first
  attempt (wall 102-509 s), and ONE analyzer run over all 52 episodes passed C1/C2/C3 with
  carried integrity `104/104` files byte-identical and the pairing falsifier not fired over
  all 26 pairs (median |ΔHD| `0.0251`, heavy-tailed to `0.7419` on `scene-0138-medium-01` —
  that shape binds the Stage-2 paired design). The full 52-episode monitor-OFF arm stands
  (mean HD `0.3607`, median `0.2553`). This pass authorizes ONLY the iteration-48 Stage-2
  OFF-vs-released-union pre-registration — not the Stage-2 runs, and no transfer, monitor,
  benchmark, deployment, or safety claim.
- **Iteration 48 completed as the HUGSIM Stage-2 transfer gate: `TRANSFER_NULL` — THE
  transfer verdict of the second-benchmark line, published at full weight.**
  [`experiments/iter48_hugsim_transfer_gate/RESULT.md`](experiments/iter48_hugsim_transfer_gate/RESULT.md).
  All `104` scheduled episodes (26 scenarios x 2 runs x 2 arms, within-launch back-to-back
  pairing) completed with `0` retries behind the full provenance gate; the F1 void check
  passed mechanically (monitor-patch SHA byte-identical to the committed copy; the seven
  NeuroNCAP-frozen parameters echoed in the receipts and every ON-arm decision log — zero
  retuning). The released union demonstrably operates on HUGSIM: it intervened in `37/52` ON
  episodes (`887` fired frames, `1,392` brake frames = `26.9%` pooled, `134` latch releases),
  F2 splat-noise mistuning did not fire in either direction, and F3 RC collapse did not fire
  (mean paired RC delta `−0.0147`, bar `−0.30` — iteration 13's paralysis did not recur). But
  the interventions buy no measurable outcome change: mean paired HD-Score delta `−0.0166`,
  95% scenario-clustered bootstrap CI `[−0.0551, +0.0255]` (median `+0.0032`, CI
  `[−0.0467, +0.0178]`; fresh OFF-OFF noise floor median \|ΔHD\| `0.0307`). The NeuroNCAP
  benefit does not measurably transfer to HUGSIM easy+medium scenarios at this N; the null is
  the measured external-validity boundary. No NeuroNCAP-equivalence, deployment, benchmark-
  ranking, robustness, or safety claim; successors need fresh pre-registrations.
- **Scientific priority is now defensibility over impressiveness.**
  If the choice is between another stronger-looking benchmark/mechanism result and a narrower
  claim that survives hostile scrutiny, prefer the narrower defensible claim. The next fresh
  pre-registration should prioritize external validity and falsification pressure: independent
  planner transfer, unseen scenario families, sensor degradation, adversarial perturbations,
  calibration stability, intervention latency, intervention cost, and deployment trade-offs.
  Sensor degradation now requires replay-support repair before any robustness claim.

The adopted sequencing (2026-07-11): the iteration-42 trace gate first (done — iterations
42-44), then the second closed-loop benchmark family (HUGSIM transfer of the released union —
launch packet at
[docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md](docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md);
lane opened by iteration 45, Stage-1 OFF-arm completion earned by iteration 47's pass, and
the Stage-2 transfer verdict delivered by iteration 48 as a full-weight transfer null — the
line's registered question is answered and the null folds into the manuscript as the measured
external-validity boundary — with iteration 49 adding the hard/extreme-tier confirmation that
opportunity density does not rescue the frozen released union, and iteration 51 decomposing
that failure as mixed collision persistence rather than a single retunable cause, with
iteration 52 splitting ON-collision persistence into absent/post braking and pre-collision
braking, and iteration 53 showing that pre-collision first fires split across CPA-only and
TTC-only channels, and iteration 54 proving actor-match evidence is not present in committed
HUGSIM evals), then the
deployment-flip successor; these rank ahead of any new intervention iteration, and the
linear-steering mechanism line is closed
([docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md](docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md)).

Closed en route, per the gate discipline: the per-frame routing predicates (iteration 17
addendum — refuted offline), the tracking layer's own offline gate (iteration 18 — failed
by one frame at the frozen margin; the GPU stayed off), the planning-query diversity head
(iteration 19 — 0/37 feasible escapes), the VAD tracker-portability gate (iteration 20 —
0/47 raw TTC fires removed, side retention below bar), and the BEV-conditioned diversity head
(iteration 21 — 0/37 feasible escapes, 23.1% candidate validity), and the first causal-localization
Stage 1 (iteration 22 — S0 integrity/data-support null), the hardened causal-localization
rerun (iteration 23 — count-floor null after S0 pass), the fresh risk-support atlas
(iteration 24 — availability-null before extraction), the staged-data inventory
(iteration 25 — no passing local root), and the data-staging remedy discovery
(iteration 26 — official trainval blobs needed but disk too small). The deployment flip remains proven
achievable and unclaimed.

Completed lines, kept for the record:

- **The power run — done.** The benchmark result confirmed at 20 runs/pair (2.12 → 2.91, CI
  [+0.605, +0.928]); the deployment question resolved into a tight null (−0.03, CI [−0.13,
  +0.07]); the apparatus reproduced the 6-run evidence exactly on every pair.
  [`experiments/full14_power/RESULT.md`](experiments/full14_power/RESULT.md).

- **Iteration 16 — softer than a stop: pre-registered null.** The 2.0 m/s crawl recovers the
  campaign's highest safe-progress but fires the side falsifier (37% → 57%): the crawl delivers
  the ego into the crossing point the stop halts short of. The full stop stands.
  [`experiments/iter16_soft_stop/RESULT.md`](experiments/iter16_soft_stop/RESULT.md).

- **Introspective plan selection — closed for command-indexed candidates, on two planners.** The
  pre-registered checkpoints answered it: UniAD's command-conditioned plans collapse totally under
  threat (0/37 escapes); VAD's native modes retain partial diversity (21% escapes) but stay below
  the frozen 30% viability bar. The safe alternative the re-ranker needs is mostly absent when it
  matters — the first threat-conditioned diversity measurements on E2E planners' own candidates
  ([`iter12`](experiments/iter12_plan_selection/RESULT.md) ·
  [`vad_generalization`](experiments/vad_generalization/RESULT.md)). Two learned successor heads
  under the runtime selector also failed offline: planning-query conditioning and scene-level BEV
  conditioning both produced **0/37** feasible escapes.
  [`iter19`](experiments/iter19_diversity_head/RESULT.md) ·
  [`iter21`](experiments/iter21_bev_diversity_head/RESULT.md).
- **A formal-envelope baseline (RSS-style) — done, H13 confirmed.** The envelope achieves the
  campaign's best raw safety by near-paralysis and lands *below the unmonitored planner* on
  safe-progress; union − RSS = +1.345, CI [+0.944, +1.701]. Stopping power is free; selectivity is
  what plan-aware introspection buys.
  [`experiments/iter13_rss_baseline/RESULT.md`](experiments/iter13_rss_baseline/RESULT.md).
- **A second frozen planner (VAD) — done, and the transfer verdict is a finding.** VAD's failure
  profile is inverted (stationary 85%, side 65%, frontal strong); the union prevents exactly those
  failures (both → 0%) but loses its selectivity — its TTC term needs the stable IDs of a learned
  tracker, which VAD does not expose. Monitor selectivity is a property of tracking quality, not
  the decision rule alone. [`vad_generalization/RESULT.md`](experiments/vad_generalization/RESULT.md).
- **The full 14-scene benchmark — done.** The published baseline independently reproduced (2.15
  vs 1.84), the union's benchmark-score win decisive at full scale (**2.15 → 3.09, CI [+0.713,
  +1.155]**), and the deployment-metric win honestly reported as not generalizing (safe-progress
  CI includes 0 — over-braking on unseen benign-progress scenes). The next mechanism this
  defines: per-scene brake-budget calibration.
  [`experiments/full14_benchmark/RESULT.md`](experiments/full14_benchmark/RESULT.md).

Scope throughout, stated plainly: the method was developed on 2 public-mini scenes at
single-digit-to-20 runs and then measured on the complete official 14-scene set — first at 6
seed-paired runs per pair, then at 20 (the published protocol uses 100; the first-6 indices of
the 20-run measurement reproduce the 6-run measurement exactly); one simulator, one L4, public
data only.

## Reproduce & repository map

**Every headline number regenerates from committed evidence — no GPU, no dataset download:**

```bash
python3 -m pytest -q                                   # monitor geometry unit tests (stdlib + pytest only)

# the G1 signal: AUROC 0.83 from the committed shadow dump
python3 experiments/iter2_monitor/g1_auroc.py \
        experiments/iter2_monitor/proof/risk.jsonl.gz \
        experiments/iter2_monitor/proof/outcomes.tsv

# the verification audit: determinism proof, side-impact recount, honest n=8 CI
python3 experiments/verification/audit_pooling.py

# the safety-engineering view: lead time, intervention budget, severity
python3 experiments/verification/analyze_safety_case.py

# the n=20 measurement (+0.398, CI [+0.133, +0.665]) — committed output
cat experiments/verification/proof_v20.txt             # regenerate: analyze_v20.py (paths in header)
```

The closed-loop stack itself is three public Docker images (NeuRAD renderer · frozen planner ·
NeuroNCAP orchestrator/scorer) on a single L4; the monitor is a self-contained patch injected into
the planner's inference server, gated by environment variables so every arm (OFF / union / RSS /
ablations) is one switch. Each experiment directory is self-describing:

| path | what it holds |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | frozen win bar; research-loop design |
| [`docs/REPORT.md`](docs/REPORT.md) | **the technical report** — the whole campaign in one document, every number wired to committed evidence |
| [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md) | verified field positioning (2023–2026): what is published, what is not, where each claim here stands |
| [`experiments/iter1_reproduce/`](experiments/iter1_reproduce) · [`iter1b_partial_baseline/`](experiments/iter1b_partial_baseline) | stack stood up; baseline reproduced + collision corpus |
| [`experiments/iter2_monitor/`](experiments/iter2_monitor) | the signal (G1, AUROC 0.83), the first A/B, the ablation, and the corrected over-claim |
| [`experiments/iter3_progress/`](experiments/iter3_progress) | the deployment metric (safe-progress) — the honest setback |
| [`experiments/iter4_gated/`](experiments/iter4_gated) · [`iter5_tracked/`](experiments/iter5_tracked) · [`iter6_cpa/`](experiments/iter6_cpa) · [`iter7_margin/`](experiments/iter7_margin) | selectivity → observed velocity → CPA → margin sweep |
| [`experiments/iter8_union/`](experiments/iter8_union) | **the union of two detectors** — the campaign's core monitor |
| [`experiments/iter9_evade/`](experiments/iter9_evade) · [`iter10_brakevade/`](experiments/iter10_brakevade) · [`iter11_early_evade/`](experiments/iter11_early_evade) | three refuted evasion designs for frontal prevention (reported nulls) |
| [`experiments/union_validation/`](experiments/union_validation) | pooled bootstrap CI — **withdrawn** (invalid pooling); corrected in place |
| [`experiments/VERIFICATION.md`](experiments/VERIFICATION.md) · [`verification/`](experiments/verification) | **independent verification pass**: audit, corrections, committed raw evidence, fresh n=20 re-measurement, safety-case analysis |
| [`experiments/iter12_plan_selection/`](experiments/iter12_plan_selection) | introspective plan selection — candidates collapse under threat (reported null) |
| [`experiments/iter13_rss_baseline/`](experiments/iter13_rss_baseline) | RSS-style formal-envelope baseline — best raw safety by near-paralysis (H13 confirmed) |
| [`experiments/vad_generalization/`](experiments/vad_generalization) | second frozen planner (VAD) — safety transfers, selectivity does not |
| [`experiments/full14_benchmark/`](experiments/full14_benchmark) | **the full official 14-scene benchmark** — baseline reproduced; 2.15 → 3.09 |
| [`experiments/iter15_latch_release/`](experiments/iter15_latch_release) | **threat-cleared latch release — the best configuration** |
| [`experiments/iter16_soft_stop/`](experiments/iter16_soft_stop) | softer than a stop — the crawl null; the stop is a position guarantee |
| [`experiments/full14_power/`](experiments/full14_power) | **the power measurement** — the benchmark result at n=20/pair; deployment resolved to a tight null |
| [`experiments/iter17_threat_routing/`](experiments/iter17_threat_routing) | threat-class routing — the gate fails on one crossing; the deployment flip proven achievable; successors refuted offline |
| [`experiments/iter18_tracker/`](experiments/iter18_tracker) | the tracking layer — offline gate failed by one frame; the GPU stayed off |
| [`experiments/iter19_diversity_head/`](experiments/iter19_diversity_head) | **the diversity-trained candidate head** — planning-query variant failed offline; no closed-loop run |
| [`experiments/iter20_vad_tracker_portability/`](experiments/iter20_vad_tracker_portability) | VAD tracker portability — offline gate failed; no closed-loop run |
| [`experiments/iter21_bev_diversity_head/`](experiments/iter21_bev_diversity_head) | BEV-conditioned diversity head — offline gate failed; no closed-loop run |
| [`experiments/iter22_causal_planner_interpretability/`](experiments/iter22_causal_planner_interpretability) | causal planner interpretability Stage 1 — S0 data-null; stopped before probes, interventions, iter12, or closed loop |
| [`experiments/iter23_s0_hardened_causal_localization/`](experiments/iter23_s0_hardened_causal_localization) | S0-hardened causal localization — deterministic canary and full S0 pass, then count-floor data-null; stopped before probes, interventions, iter12, or closed loop |
| [`experiments/iter24_risk_support_atlas/`](experiments/iter24_risk_support_atlas) | fresh risk-support atlas — availability-null after known-data firewall; stopped before canary/full extraction, probes, interventions, iter12, selector, or closed loop |
| [`experiments/iter25_staged_data_inventory/`](experiments/iter25_staged_data_inventory) | staged-data inventory — infrastructure-null; no frozen local root has enough fresh post-firewall keyframes for a future atlas |
| [`experiments/iter26_data_staging_remedy/`](experiments/iter26_data_staging_remedy) | data-staging remedy — capacity-null; official trainval sensor blobs needed, current GPU disk too small |
| [`experiments/iter27_storage_provisioning/`](experiments/iter27_storage_provisioning) | storage provisioning — passed; 1 TB persistent data volume mounted before any nuScenes download |
| [`experiments/iter28_nuscenes_trainval_staging/`](experiments/iter28_nuscenes_trainval_staging) | official nuScenes trainval staging — passed; full trainval root staged, extracted, and post-firewall inventory proved |
| [`experiments/iter29_trainval_risk_support_atlas/`](experiments/iter29_trainval_risk_support_atlas) | full-trainval risk-support atlas — support pass for low-diversity hazard/control counts; optional strict-collapse note failed; no probes, interventions, iter12, selector, or closed loop authorized |
| [`experiments/iter30_full_trainval_lowdiv_localization/`](experiments/iter30_full_trainval_lowdiv_localization) | full-trainval diagnostic localization — pass on committed iter29 proof artifacts; internal bridge tensor signal exceeds metadata and ego-plan controls; no intervention, iter12, selector, GPU, or closed loop authorized |
| [`experiments/iter31_full_trainval_bridge_intervention/`](experiments/iter31_full_trainval_bridge_intervention) | full-trainval bridge intervention — S0 infrastructure-null after alpha-zero baseline reproduction failed; stopped before calibration, heldout, iter12, selector, or closed loop |
| [`experiments/iter32_prefix_replay_baseline_recovery/`](experiments/iter32_prefix_replay_baseline_recovery) | prefix-replay baseline recovery — pass; 12 frozen canary targets reproduce iter29 exactly under 44-row prefix replay; fresh intervention pre-registration required |
| [`experiments/iter33_prefix_preserving_bridge_intervention/`](experiments/iter33_prefix_preserving_bridge_intervention) | prefix-preserving bridge intervention — calibration null; no usable alpha, stopped before heldout, iter12, selector, and closed loop |
| [`experiments/iter34_direction_specificity_audit/`](experiments/iter34_direction_specificity_audit) | direction-specificity audit — post-result null; same global bridge-centroid direction lacks row-level dose-response consistency for scale-only successor work |
| [`experiments/iter35_response_heterogeneity_audit/`](experiments/iter35_response_heterogeneity_audit) | response-heterogeneity audit — post-result null; heterogeneity exists but no frozen baseline-geometry stratum authorizes conditioned successor work |
| [`experiments/iter36_bridge_site_decomposition/`](experiments/iter36_bridge_site_decomposition) | bridge-site decomposition audit — diagnostic pass; `track_query` and four trajectory slots authorize only a future site-specific pre-registration |
| [`experiments/iter37_track_query_site_intervention/`](experiments/iter37_track_query_site_intervention) | track-query site intervention — calibration null; no usable alpha, stopped before heldout, iter12, selector, and closed loop |
| [`experiments/iter38_track_query_opposite_direction/`](experiments/iter38_track_query_opposite_direction) | track-query opposite-direction S0 proof — canary pass; calibration authorized but not launched |
| [`experiments/iter39_external_validity_claim_audit/`](experiments/iter39_external_validity_claim_audit) | external-validity claim audit — doc narrowing published; active story now scoped to evidence |
| [`experiments/iter40_timing_cost_audit/`](experiments/iter40_timing_cost_audit) | timing/intervention-cost audit — full14/power simulation budget and lead-time pass; no real-time/deployment claim |
| [`experiments/iter41_sensor_input_degradation_gate/`](experiments/iter41_sensor_input_degradation_gate) | monitor-input degradation gate — infrastructure null; exact pose timestamp support failed before perturbations |
| [`experiments/iter42_exact_trace_replay_support/`](experiments/iter42_exact_trace_replay_support) | exact trace replay support — replay-identity pass; trace substrate only, authorizes only an offline object-stream perturbation pre-registration |
| [`experiments/iter43_object_stream_perturbation_gate/`](experiments/iter43_object_stream_perturbation_gate) | object-stream perturbation gate — mild-fragile finding; jitter over-fires at 5 cm in replay, dropout/score/churn stable at mild levels; no sensor or closed-loop claim |
| [`experiments/iter44_velocity_smoothing_gate/`](experiments/iter44_velocity_smoothing_gate) | velocity temporal-smoothing repair gate — no-repair null; smoothing halves jitter over-firing but erases genuine interventions; released union unchanged |
| [`experiments/iter45_hugsim_infra_gate/`](experiments/iter45_hugsim_infra_gate) | HUGSIM infrastructure gate — pass; second-benchmark transfer lane open (assets, environments, monitor-OFF closed-loop smoke); authorizes only the Stage-1/2 pre-registration |
| [`experiments/iter46_hugsim_off_baseline/`](experiments/iter46_hugsim_off_baseline) | HUGSIM Stage-1 monitor-OFF baseline — completion null; 38/52 episodes, seven `load_HD_map` scenarios blocked on the unstaged map-expansion pack; Stage-2 pre-registration not authorized |
| [`experiments/iter47_map_staging_and_off_completion/`](experiments/iter47_map_staging_and_off_completion) | map-expansion staging + OFF-baseline completion — PASS; Stage A staged the pack with receipts, Stage B completed all 14 failed episodes first-attempt, full 52-episode OFF arm stands with pairing feasible over 26 pairs; authorizes only the iteration-48 Stage-2 pre-registration |
| [`experiments/iter48_hugsim_transfer_gate/`](experiments/iter48_hugsim_transfer_gate) | HUGSIM Stage-2 transfer gate — TRANSFER_NULL, THE transfer verdict: 104/104 paired episodes under the frozen NeuroNCAP parameters (F1 zero-retuning verified), the union fires/latches/releases on HUGSIM but the mean paired HD delta CI [−0.0551, +0.0255] includes zero; the measured external-validity boundary of the released union |
| [`experiments/iter49_hugsim_hard_tier_gate/`](experiments/iter49_hugsim_hard_tier_gate) | HUGSIM hard/extreme-tier transfer gate — TRANSFER_NULL: 104/104 paired episodes complete, F1 zero-retuning verified, 40/52 ON episodes intervened, mean paired HD delta CI [−0.0438, +0.0203] includes zero; iteration-50 P1 refuted because 51/52 OFF episodes had collision opportunity |
| [`experiments/iter50_collision_opportunity_audit/`](experiments/iter50_collision_opportunity_audit) | collision-opportunity audit — A1_CONFIRMED on NeuroNCAP and OPPORTUNITY_PRESENT_NULL on HUGSIM; P1 pre-committed the iter49 interpretation |
| [`experiments/iter51_hugsim_failure_taxonomy/`](experiments/iter51_hugsim_failure_taxonomy) | HUGSIM transfer-failure taxonomy — TAXONOMY_COMPLETE: 104 committed transfer pairs classified offline; only 6/91 OFF-opportunity pairs converted, 85/104 remained collision-persistent, and the combined taxonomy is mixed rather than a single-cause failure |
| [`experiments/iter52_hugsim_on_collision_timing_audit/`](experiments/iter52_hugsim_on_collision_timing_audit) | HUGSIM ON-collision timing audit — TIMING_AUDIT_COMPLETE: 92 ON-collision episodes decomposed into absent/post braking vs pre-collision braking; no-brake cases all missed the frozen TTC/CPA surface proxy, but 26 long-lead brake cases still collided |
| [`experiments/iter53_hugsim_first_fire_channel_audit/`](experiments/iter53_hugsim_first_fire_channel_audit) | HUGSIM first-fire channel audit — FIRST_FIRE_CHANNEL_COMPLETE: ON-collision first-fire channels split TTC-only 36, CPA-only 33, no-fire 22, both 1; pre-collision-fire persistent cases split CPA-only 19 / TTC-only 16, so no single union branch explains the transfer failure |
| [`experiments/iter54_hugsim_provenance_support_audit/`](experiments/iter54_hugsim_provenance_support_audit) | HUGSIM provenance support audit — PROVENANCE_SUPPORT_NULL: monitor first-fire argmins reconstruct from committed logs, but collision actor identity is not logged in HUGSIM evals, so actor matching requires new instrumentation |
| [`experiments/iter55_hugsim_collision_instrumentation_source_audit/`](experiments/iter55_hugsim_collision_instrumentation_source_audit) | HUGSIM collision instrumentation source audit — COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE: frozen source checkout verified; future provenance instrumentation route mapped to `sim/utils/score_calculator.py` and `closed_loop.py`; no run or actor attribution |
| [`experiments/iter56_hugsim_provenance_instrumentation_patch/`](experiments/iter56_hugsim_provenance_instrumentation_patch) | HUGSIM provenance instrumentation patch design — INSTRUMENTATION_PATCH_DESIGN_NULL: first `collision_provenance` sidecar patch applied and compiled, but the registered static guard rejected the `score_nc` branch; no patch authorized for a run |
| [`experiments/iter57_hugsim_patch_guard_refinement/`](experiments/iter57_hugsim_patch_guard_refinement) | HUGSIM provenance patch guard refinement — PATCH_GUARD_REFINEMENT_COMPLETE: byte-identical Iter56 patch passes refined static guard as additive provenance instrumentation; no HUGSIM run or actor attribution |
| [`experiments/iter58_hugsim_provenance_instrumented_canary/`](experiments/iter58_hugsim_provenance_instrumented_canary) | HUGSIM provenance instrumented canary — PROVENANCE_CANARY_COMPLETE: byte-bound patch executes in two real HUGSIM episodes and emits top-level collision provenance while scalar metrics/details remain intact; no actor-match or HD-Score-invariance claim |
| [`experiments/iter59_hugsim_actor_match_audit/`](experiments/iter59_hugsim_actor_match_audit) | HUGSIM actor-match support audit — ACTOR_MATCH_AUDIT_COMPLETE: eight registered ON episodes completed; three classifiable foreground rows all mismatched by the frozen bridge, with no-fire/post-fire/background-only rows making up the rest; bounded mechanism audit only |
| [`experiments/iter60_actor_bridge_sensitivity/`](experiments/iter60_actor_bridge_sensitivity) | actor-match bridge sensitivity audit — BRIDGE_AMBIGUOUS_NULL: no frozen bridge variant turned the three iteration-59 rows into a match, but one row became ambiguous at 5.6649 m, so robust all-row mismatch is not supported |
| [`experiments/iter61_monitor_object_surface_audit/`](experiments/iter61_monitor_object_surface_audit) | monitor object-surface audit — OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE: one classifiable row has a non-triggering first-fire object match, while two rows have no first-fire object support; bounded mechanism audit only |
| [`experiments/iter62_nontrigger_ranking_audit/`](experiments/iter62_nontrigger_ranking_audit) | non-trigger ranking audit — MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE: the matched non-trigger object in `ttc_extreme_b` was visible but outside the frozen first-fire CPA/TTC hazard surface |
| [`experiments/iter63_temporal_emergence_audit/`](experiments/iter63_temporal_emergence_audit) | temporal emergence audit — TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE: the matched non-trigger object stayed visible but never crossed hazard or borderline before the first foreground collision timestamp |
| [`experiments/iter64_unsupported_temporal_surface_audit/`](experiments/iter64_unsupported_temporal_surface_audit) | unsupported-row temporal surface audit — UNSUPPORTED_TEMPORAL_MATCH_COMPLETE: both first-fire-unsupported rows have pre-contact monitor-object matches under the frozen bridge grid |
| [`experiments/iter65_temporal_alignment_audit/`](experiments/iter65_temporal_alignment_audit) | matched pre-contact temporal alignment audit — TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE: both Iter64 matched objects were present but subthreshold at their matched decision timestamps |
| [`experiments/iter66_matched_object_timeline_audit/`](experiments/iter66_matched_object_timeline_audit) | matched-object hazard timeline audit — MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE: one Iter65 target becomes an active TTC hazard at first fire, while the other remains visible-never-active |
| [`experiments/iter67_trigger_target_bridge_audit/`](experiments/iter67_trigger_target_bridge_audit) | trigger-target bridge audit — TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE: one row is same-object target/trigger, while the split row has full-window support for both objects but no first-fire trigger support at the fire timestamp |
| [`experiments/iter68_fire_time_bridge_decomposition/`](experiments/iter68_fire_time_bridge_decomposition) | fire-time bridge decomposition audit — FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE: one trigger's best bridge support is before first fire, while the other's is after first fire |
| [`experiments/iter69_hugsim_mechanism_taxonomy/`](experiments/iter69_hugsim_mechanism_taxonomy) | HUGSIM mechanism taxonomy synthesis — HUGSIM_MECHANISM_TAXONOMY_COMPLETE: all eight iteration-59 rows classified; five structural labels preserved and all three classifiable foreground rows refined by downstream evidence |
| [`experiments/iter70_hugsim_structural_timing_audit/`](experiments/iter70_hugsim_structural_timing_audit) | HUGSIM structural-row timing audit — HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE: five structural rows split into two foreground-present surface-silent rows, two foreground-present late-fire rows, and one foreground-absent/background-only row |
| [`experiments/iter71_hugsim_surface_silent_margin_audit/`](experiments/iter71_hugsim_surface_silent_margin_audit) | HUGSIM surface-silent margin audit — HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE: both foreground-present no-fire rows are far from the frozen CPA/TTC trigger surfaces before foreground contact |
| [`experiments/iter72_hugsim_late_fire_prefire_margin_audit/`](experiments/iter72_hugsim_late_fire_prefire_margin_audit) | HUGSIM late-fire prefire margin audit — HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE: both foreground-present late-fire rows are near, but not crossing, a frozen trigger surface before foreground contact |
| [`experiments/iter73_hugsim_margin_transition_audit/`](experiments/iter73_hugsim_margin_transition_audit) | HUGSIM structural margin-transition audit — HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE: foreground structural rows split into silent far/never-active versus late near-precontact/postcontact-active timelines |
| [`experiments/iter74_hugsim_late_fire_delay_barrier/`](experiments/iter74_hugsim_late_fire_delay_barrier) | HUGSIM late-fire delay-barrier audit — HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE: both fixed late-fire rows are cross-channel activations from pre-contact near channel to post-contact active channel |
| [`experiments/iter75_hugsim_cross_channel_object_handoff/`](experiments/iter75_hugsim_cross_channel_object_handoff) | HUGSIM cross-channel object-handoff audit — HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE: both fixed cross-channel late-fire rows switch responsible monitor object |
| [`experiments/iter76_hugsim_switch_foreground_bridge/`](experiments/iter76_hugsim_switch_foreground_bridge) | HUGSIM switch foreground-bridge audit — HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE: neither switched event object reaches foreground bridge match or ambiguous support |
| [`experiments/iter77_hugsim_event_object_set_bridge/`](experiments/iter77_hugsim_event_object_set_bridge) | HUGSIM event object-set foreground-bridge audit — HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE: full event-row object sets recover mixed foreground support not carried by selected switched objects |
| [`experiments/iter78_hugsim_support_object_ranking/`](experiments/iter78_hugsim_support_object_ranking) | HUGSIM support-object ranking audit — HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE: all fixed foreground-supported full-set objects are nonselected and subthreshold under the logged monitor surface |
| [`experiments/iter79_hugsim_selected_surface_decomposition/`](experiments/iter79_hugsim_selected_surface_decomposition) | HUGSIM selected-object surface decomposition — HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE: selected objects are active/borderline while the foreground-supported objects remain subthreshold |
| [`experiments/iter80_hugsim_selected_all_provenance_bridge/`](experiments/iter80_hugsim_selected_all_provenance_bridge) | HUGSIM selected-object all-provenance bridge audit — HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE: selected active/borderline objects do not bridge to any logged provenance row |
| [`experiments/iter81_hugsim_support_object_temporal_surface/`](experiments/iter81_hugsim_support_object_temporal_surface) | HUGSIM support-object temporal surface audit — HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE: one foreground-supported object later reaches the released surface, while the other remains visible-never-surface |
| [`experiments/iter82_hugsim_support_surface_bridge_cooccurrence/`](experiments/iter82_hugsim_support_surface_bridge_cooccurrence) | HUGSIM support-object surface/provenance co-occurrence audit — HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE: one support object has borderline+bridge co-occurrence only, while the other has bridge support without surface activation |
| [`experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/`](experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition) | HUGSIM bridge-supported surface-miss decomposition — HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE: bridge-supported support objects split into TTC-borderline-only and no-finite-TTC/CPA-far misses |
| [`experiments/iter84_hugsim_selected_support_arbitration/`](experiments/iter84_hugsim_selected_support_arbitration) | HUGSIM selected/support path-arbitration decomposition — HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE: selected objects have stronger logged path geometry, while support objects have the provenance bridge |
| [`experiments/iter85_hugsim_path_horizon_bridge_timing/`](experiments/iter85_hugsim_path_horizon_bridge_timing) | HUGSIM path-horizon/provenance-timing decomposition — HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE: selected objects retain path-geometry advantage while support-object provenance bridges after the event |
| [`experiments/iter86_hugsim_bridge_time_surface_replay/`](experiments/iter86_hugsim_bridge_time_surface_replay) | HUGSIM bridge-time support-surface replay — HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED: exact bridge-time replay classifies two rows but blocks on missing `6.0 s` decision row |
| [`experiments/iter87_hugsim_interval_bridge_time_surface_replay/`](experiments/iter87_hugsim_interval_bridge_time_surface_replay) | HUGSIM interval bridge-time support-surface replay — HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE: one support object reaches borderline, while the other remains subthreshold under interval replay |
| [`experiments/iter88_hugsim_bridge_surface_margin_residual/`](experiments/iter88_hugsim_bridge_surface_margin_residual) | HUGSIM bridge/surface margin residual decomposition — HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE: support residuals split into TTC-borderline/CPA-far and no-finite-TTC/CPA-far cases |
| [`experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/`](experiments/iter89_hugsim_joint_bridge_surface_candidate_audit) | HUGSIM joint bridge/surface candidate audit — HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE: no logged replay-row object is both active and bridge-supported |
| [`experiments/iter90_hugsim_active_surface_provenance_gap/`](experiments/iter90_hugsim_active_surface_provenance_gap) | HUGSIM active-surface provenance gap audit — HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE: bridge-supported replay-row objects are non-active, while the only active object lacks bridge support |
| [`experiments/iter91_hugsim_active_gap_geometry_decomposition/`](experiments/iter91_hugsim_active_gap_geometry_decomposition) | HUGSIM active-gap geometry decomposition — HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE: path-active geometry and provenance-supported geometry split across different objects |
| [`experiments/iter92_hugsim_path_proximity_arbitration/`](experiments/iter92_hugsim_path_proximity_arbitration) | HUGSIM path-proximity arbitration audit — HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE: CPA/path-best and provenance-best objects differ in all fixed replay rows |
| [`experiments/iter93_hugsim_surface_winner_alignment/`](experiments/iter93_hugsim_surface_winner_alignment) | HUGSIM surface-winner alignment audit — HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE: surface winner follows path in two rows and provenance in one row |
| [`experiments/iter94_hugsim_active_row_surface_margin_arbitration/`](experiments/iter94_hugsim_active_row_surface_margin_arbitration) | HUGSIM active-row surface margin arbitration — HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE: active row surface winner is the only active CPA/path candidate, while bridge-supported candidates are non-active and CPA-far |
| [`docs/NEXT_PHASE.md`](docs/NEXT_PHASE.md) | successor lines with frozen decision rules |
| [`docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md`](docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md) | launch packet that led to iteration 22; not itself a pre-registration |
| [`docs/research/FRONTIER_POSITIONING_2026-07-11.md`](docs/research/FRONTIER_POSITIONING_2026-07-11.md) | source-verified mid-2026 benchmark/monitor/industry positioning; the binding 2.91-is-not-benchmark-SOTA framing rule |
| [`docs/research/FRONTIER_PROBLEM_ALIGNMENT_2026-07-13.md`](docs/research/FRONTIER_PROBLEM_ALIGNMENT_2026-07-13.md) | source-backed Stanford/MIT/Tesla/Mobileye/NHTSA alignment pulse; next local priority is selected-vs-support HUGSIM path/arbitration decomposition, not open-ended research |
| [`docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md`](docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md) | durable memory capsule for future sessions: long-tail, validation, supervision, world-model, operational-semantics, and Sentinel niche lessons from the frontier pass |
| [`docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md`](docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md) | launch packet for the HUGSIM second-benchmark transfer of the released union; not a pre-registration |
| [`docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md`](docs/research/INTERVENTION_MECHANISM_VERDICT_2026-07-11.md) | survey verdict closing the linear-steering line; conditions for any future intervention iteration |
| [`docs/research/BOX_CLEANUP_2026-07-12.md`](docs/research/BOX_CLEANUP_2026-07-12.md) | verified-deletion disk-cleanup record for `sentinel-gpu` before the HUGSIM lane; every deleted item SHA-verified against committed artifacts |
| [`docs/research/ITER22_HYPOTHESIS_DRAFT.md`](docs/research/ITER22_HYPOTHESIS_DRAFT.md) · [`docs/research/ITER22_ADVERSARIAL_REVIEW.md`](docs/research/ITER22_ADVERSARIAL_REVIEW.md) | planning-only iter22 draft and adversarial review; not pre-registrations |
| [`docs/paper/MANUSCRIPT.md`](docs/paper/MANUSCRIPT.md) · [`docs/paper/paper.pdf`](docs/paper/paper.pdf) | the manuscript (full draft; compiled PDF; arXiv package committed) |
| [`scripts/validate_docs.py`](scripts/validate_docs.py) | CI docs guard: diagram budgets, link health, story completeness — enforced on every push |

Every result folder carries a `RESULT.md` with the real per-run numbers, the exact server patch, and the
run script. `sentinel/monitor.py` is the pure-geometry monitor with unit tests (`tests/`); CI runs ruff +
pytest on every push.

## Data & honesty

Public datasets only (nuScenes via NeuroNCAP); no fleet or proprietary data; no frames
redistributed. Reproducing the published baseline ourselves was the starting line — our 2.12
pooled reproduction is corroborated by DMAD's independent 2.11 rerun — and every null is
reported, not buried.
