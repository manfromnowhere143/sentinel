# Sentinel

**A runtime introspective safety monitor that watches a frozen self-driving planner, predicts the
collision it is about to cause, and intervenes — measured where it actually matters: in closed
loop, by whether the car crashes *and whether it can still drive*.**

> **Honest status up front (11 iterations + an independent verification pass):** the introspective
> signal predicts the planner's collisions (AUROC 0.83), and the best configuration — the **union**
> (iter 8) — is **selective** (clean-scene behaviour identical to the unmonitored planner),
> **removes most side-impacts** (100% → 30% at 20 unique episodes), **mitigates** the frontal
> head-on, and is **net-positive on the deployment metric with a bootstrap CI that excludes zero**
> (safe-progress +0.398, 95% CI [+0.133, +0.665], n=20 unique episodes/scene). That last sentence
> earned its precision the hard way: an independent verification pass
> ([`experiments/VERIFICATION.md`](experiments/VERIFICATION.md)) **withdrew** an earlier version of
> it — the original pooling had counted NeuroNCAP's deterministic per-index episodes as independent
> replications — and the claim was then **re-established on 20 genuinely-unique episodes**, with
> run indices 0–7 doubling as an exact-reproduction check of the whole apparatus (they match to
> the last digit). Three evasive designs to *prevent* the head-on were honestly **refuted** — the
> last showing *why*: a swerve on a false alarm crashes, and the fresh n=20 re-check confirms it.
> Over-claims here get caught by our own audits and corrected in place — that self-correction is
> the point. Full arc in [Status](#status--where-it-really-stands-the-honest-current-truth).

The field's open-loop driving metrics are saturated and gameable (an ego-state MLP "wins" nuScenes
L2). The honest axis is **closed-loop safety**, and there the public state of the art is wide open:
the strongest end-to-end planners **collide in 87.8–99.6% of safety-critical scenarios** and score
**1.84 (UniAD) / 2.75 (VAD) out of 5** on NeuroNCAP. Sentinel attacks that gap with a small,
plug-and-play monitor on a *frozen* planner — no fleet, no retraining the planner, single-digit
GPUs.

> Built on what we already proved. In a prior study ([PerceptionProof](https://github.com/manfromnowhere143/perceptionproof))
> a cheap label-free signal predicted the **collision gate at AUROC ~0.8**. Sentinel takes that
> introspective signal **closed-loop, with intervention, to prevent the crash** — the natural
> sequel: *we showed cheap signals see failure coming; now we use them to stop it.*

---

## The result

Eleven iterations under a frozen campaign pre-registration converge on one configuration — the
**union** — that, on a frozen UniAD planner, is **selective, side-impact-reducing, and
net-positive over the unmonitored planner** on a progress-aware deployment metric. The numbers
below are the verification pass's definitive fresh measurement: **20 genuinely-unique episodes per
scene per arm**, seed-paired, with run indices 0–7 doubling as an exact reproduction of the
original iteration-8 data (they match to the last digit):

| metric (20 unique episodes/scene) | unmonitored planner | Sentinel (union) |
|---|---:|---:|
| clean-scene score / collision (selectivity) | 4.51 / 10% | **4.51 / 10%** (identical) |
| side-impact collision rate | **100 %** | **30 %** |
| frontal head-on score (0–5) | 0.84 | **2.36** (impact mitigated) |
| **safe-progress** (safety × route progress) | 1.83 | **2.22** |

> **Net-positive, on statistics that survived an adversarial audit:** safe-progress advantage
> **+0.398, 95 % CI [+0.133, +0.665]** — excludes zero at n=20 unique episodes. An earlier version
> of this claim was **withdrawn** by the independent verification pass (it had pooled
> deterministic episode replays as if independent — [`experiments/VERIFICATION.md`](experiments/VERIFICATION.md))
> and re-established on fresh data. The other honest limit, named precisely: the frontal head-on
> is *mitigated*, not *prevented*, and three evasive designs to prevent it were tested and refuted
> (§Status) — the third refutation re-confirmed at n=20.

In the units an AV safety case is written in (derived from the committed per-frame decision logs
and ground-truth timing — [`analyze_safety_case.py`](experiments/verification/analyze_safety_case.py)):
the monitor fires a **median 2.5 s before counterfactual contact** (range 1.0–3.5 s), spends
**11 brake frames per 242 benign meters** driven on the clean scene, and cuts frontal mean impact
speed from **13.9 to 6.7 m/s**.

The campaign in one picture — every step measured closed-loop against the same unmonitored planner,
nulls kept, one headline withdrawn by our own audit and re-established on independent data:

```mermaid
flowchart LR
  G1["G1 · the signal<br/>planner's own outputs<br/>predict its crashes<br/><b>AUROC 0.83</b>"] --> I2["iter 2 · TTC brake<br/>collision 65→13%<br/><b>safety CI met</b>"]
  I2 --> I3["iter 3 · deployment metric<br/><b>over-brakes</b> — honest setback,<br/>corrected an over-claim"]
  I3 --> I45["iters 4–5 · selective gating<br/>clean scene = OFF<br/>but side-blind"]
  I45 --> I67["iters 6–7 · plan-vs-path CPA<br/>catches the T-bone<br/>no single margin holds all"]
  I67 --> U["iter 8 · THE UNION<br/>CPA OR observed-TTC<br/><b>selective + side + net-positive</b>"]
  U --> E9["iters 9–11 · three evasion designs<br/>steer · brake-steer · early-evade<br/><b>all refuted</b> — a stop is safe<br/>when wrong, a swerve is not"]
  U --> V["verification pass<br/>determinism found → pooled claim<br/><b>withdrawn</b> → re-measured fresh:<br/><b>+0.398 [+0.133, +0.665]</b> at n=20"]
  classDef win fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef null fill:#fdebec,stroke:#c62828,color:#3b1213;
  classDef audit fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  class G1,I2,U win;
  class I3,I45,I67,E9 null;
  class V audit;
```

The winning monitor is a **union of two individually-selective detectors**, chosen because the two
failure modes are physically distinct — a side T-bone is a real path crossing, while a head-on is
hidden by the planner's own optimism:

```mermaid
flowchart LR
  subgraph PL["frozen planner (UniAD, weights locked)"]
    direction TB
    BEV["multi-camera BEV encoding"] --> TRK["detection + tracking<br/>(objects, scores, persistent IDs)"]
    TRK --> MOT["motion forecasting<br/>(per-agent future trajectories)"]
    MOT --> PH["planning head<br/>(ego trajectory, command-conditioned)"]
  end
  PL -- "plan · objects · forecasts · track IDs · ego2world<br/>(the planner's own /infer outputs — nothing privileged)" --> M
  subgraph M["Sentinel monitor — label-free geometry, no learned weights"]
    direction TB
    A["world-frame object tracks by ID<br/>(ego-motion-compensated finite difference<br/>= observed velocity, not the planner's optimistic forecast)"]
    C{"plan-vs-tracked-path<br/>closest approach &lt; 1.5 m?<br/><i>catches the side T-bone:<br/>paths truly cross</i>"}
    T{"observed agent-closing<br/>time-to-collision &lt; 2.5 s?<br/><i>catches the head-on the planner's<br/>optimistic plan hides</i>"}
    A --> C
    A --> T
  end
  C -- "either fires" --> B["committed stop<br/>(latched zero-trajectory —<br/>safe even when the trigger is wrong)"]
  T -- "either fires" --> B
  C -- "neither fires" --> E["execute the planner's plan<br/>unchanged"]
  B --> S["NeuroNCAP closed loop"]
  E --> S
  M -. "per-frame decision receipt<br/>(sentinel_*.jsonl, committed)" .-> V[("evidence archive<br/>experiments/verification/")]
  S --> R[/"per-run: NCAP safety 0–5 · collision % · impact speed · ego progress"/]
  R -. "run logs + ego_poses.json (committed)" .-> V
  classDef planner fill:#f3f0fa,stroke:#5e35b1,color:#22163d;
  classDef mon fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  classDef act fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef ev fill:#fff8e1,stroke:#b28704,color:#3d2f00;
  class BEV,TRK,MOT,PH planner;
  class A,C,T mon;
  class B,E act;
  class V,R ev;
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

### Score tracker (honest trajectory — updated every iteration)

| iter | what we changed | NeuroNCAP score ↑ | collision % ↓ | vs baseline | insight |
|---|---|---|---|---|---|
| 0 | published baseline (target) | UniAD 1.84 · VAD 2.75 | 87.8–99.6 | — | the gap we attack |
| 1a | **stack stood up** — full closed loop on 1 L4, frozen UniAD in the loop, real metric out (smoke: scene-0103 stationary, 2 runs → 5.0/5.0, no collision) | — | — | infra gate **cleared** | the binding constraint was the apparatus, not the idea — [8 blockers cleared](experiments/iter1_reproduce/PROOF_smoke_0103.md) |
| 1b | **partial baseline + collision corpus** — every public-mini scene, frozen UniAD, 60 closed-loop episodes (frontal/0103, side/0103, stationary/0103, stationary/0796 × 15) | frontal/0103 **1.07** · side/0103 0.51 · stat/0103 5.00 · stat/0796 1.03 | 80 · 100 · 0 · 80 % | frontal **1.07 vs pub 1.17** (matches) | crashes coincide with the planner's own perception collapsing at 5–15 m — the signal iter 2 monitors |
| 2·G1 | **monitor signal validated** — frozen planner's own forecasts foresee its crashes (shadow replay, 40 episodes, 26/14) | — | — | **AUROC 0.83** (label-free) | imminent (≤0.5 s) predicted gap is the signal; sharpens toward imminent (0.67→0.75→0.83 at the cited horizons, one small inversion mid-curve); simplest term wins |
| 2 | **monitor + TTC brake, frozen planner** — A/B on the corpus | **1.92 → 4.67** | **65% → 13%** | **H1 met** (safety), CI [+2.21,+3.22] | TTC trigger + committed stop; side collisions 100%→0% — *but see iter 3* |
| 2·abl | **ablation** — naive-proximity / always-brake controls | — | prox 83 · always 50 · TTC 40 (frontal) | introspective signal **essential** | naive distance brake ≈ useless on fast approaches; closing-speed-from-forecast does the work |
| 3 | **deployment metric (safe-progress)** — does it avoid the crash AND drive? | OFF **2.08** · always 0.49 · TTC 0.58 (safe-prog) | progress: OFF 0.91 · TTC 0.13 | **monitor over-brakes** | honest setback: TTC freezes benign scenes, *not* selective; unmonitored wins safe-progress. Next: introspective gating |
| 4 | **gate on the *agent's* closing speed** — brake only on active threats | gated **2.80** · OFF 2.08 · TTC-old 0.64 (safe-prog) | clean-scene progress restored to OFF (0 brakes) | **net-positive vs OFF** (partial) | selectivity SOLVED; but gate under-brakes real threats (optimistic-forecast velocity) → danger safety lost. Next: track true agent velocity |
| 5 | **observed-velocity gating** — agent velocity from multi-frame tracking, not the forecast | tracked **2.35** · OFF 2.08 (safe-prog) | clean=OFF (0 brakes); frontal coll 83%→**67%** | net-positive; **frontal recovered** | selectivity holds + observed velocity beats the forecast on frontal — but **side-impact still 100%** (its warning is in the ego's motion the gate filters out). Next: plan-vs-tracked-path collision check |
| 6 | **plan-vs-tracked-path CPA** — brake if the ego's planned path crosses an agent's tracked path | cpa 2.17 · OFF 2.32 (safe-prog) | **side-impact 100% → 0%** (8/8 avoided) | **side case SOLVED** (but over-brakes) | the T-bone that beat iters 4–5 is caught geometrically; cost = 2.5 m margin also flags benign close passes → clean 33→22 m. Next: tighter margin (~1.2 m) to keep the side win + restore selectivity |
| 7 | **margin sweep** — CPA at 1.5 m vs 1.0 m vs OFF | cpa@1.5 selective (clean 32.3 = OFF) | side **0%** kept; frontal reverts to **100%** | **3 of 4 at once** | tighter margin restores selectivity + keeps the side win, but frontal defeats plan-CPA at *any* tight margin (optimistic plan clears by 3–4 m). No single margin holds all four → **union two detectors** |
| 8 | **the union** — brake if (plan-vs-path CPA < 1.5 m) OR (observed agent-closing TTC < 2.5 s) | union **2.53** · OFF 2.32 (safe-prog) | clean 30.2≈OFF · **side 100→12.5%** (7/8, verification-corrected) · frontal score 1.31→**2.43** | **selective + side-solving + directionally net-positive, at once** | first config to hold 3 of 4 simultaneously; frontal impact strongly *mitigated* (not rate-reduced). Open ceiling: preventing (not softening) frontal head-on — planner optimism + stopping distance |
| 9 | **evasive steering (AES) for frontal** — threat-aware: side→stop, head-on→swerve | — | frontal evade **1.66/100%** vs union stop **2.53/83%** | **refuted (null)** | naive 4 m swerve can't clear the actor and, keeping speed, hits harder than stopping. Selectivity + side preserved. Committed stop stays best; frontal *prevention* remains open |
| 10 | **braking evasion into a tracked-clear gap** — shed speed *and* steer to the open side | — | frontal brakevade **1.67/100%** vs union stop **2.53/83%** | **refuted (null)** | second evasion family, same result: steering (even while braking) is worse than the pure stop. Two designs converge → committed stop is the frontal *ceiling*; prevention needs more than a single maneuver |
| ✓ | **statistical validation** — pool the union & OFF arms across iters 8/9/10, bootstrap the safe-progress delta | union 2.60 vs OFF 2.14 (pooled) | side "5%" (pooled) | *claimed* net-positive | **WITHDRAWN by the verification pass**: the three "replications" are deterministic replays of the same episodes (n=20 was really n=8 unique); honest CI [−0.27, +0.78] does not exclude 0. [`union_validation`](experiments/union_validation/RESULT.md) |
| 11 | **early collision-course detection + evasion** — 4 s kinematic closest-approach, then time-gated lane change | — | frontal evade **83%** (= stop 83%); clean **50% crash**; side evade 83% | **refuted (null)** | third evasion refuted, and complete-data audit made it stronger: early detection neither prevents the head-on nor stays selective; evasion on a false alarm *crashes the clean scene 50%* and un-solves the side case (83%). A stop is safe when wrong, a swerve is not. Frontal-prevention line closed. [`iter11_early_evade`](experiments/iter11_early_evade/RESULT.md) |
| ✚ | **independent verification pass** — re-derive every claim from raw evidence; attack the statistics; re-run fresh at 20 unique episodes | union **2.22** vs OFF 1.83 (n=20 unique) | side 100→**30%** · clean identical to OFF | **net-positive RE-ESTABLISHED**: delta **+0.398, 95% CI [+0.133, +0.665]** | determinism found (episodes replay per run index) → pooled claim withdrawn, then re-measured on 20 genuinely-unique episodes: CI excludes zero; runs 0-7 reproduce iteration 8 exactly (apparatus check); iter11 evasion null re-confirms (worse than stop, degrades the clean scene). Raw evidence committed. [`VERIFICATION.md`](experiments/VERIFICATION.md) |

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

```mermaid
flowchart TB
  subgraph STACK["the apparatus — three public containers on one L4 GPU"]
    direction LR
    ORCH["NeuroNCAP orchestrator<br/>scenario actor + scoring<br/><i>episodes are deterministic per run index<br/>(established by the verification pass —<br/>every comparison is therefore seed-paired)</i>"]
    REND["NeuRAD neural renderer<br/>photoreal multi-camera frames<br/>from real nuScenes drives"]
    MODEL["frozen UniAD container<br/>inference server /infer<br/>+ the Sentinel patch (env-gated:<br/>OFF / union / ablation arms)"]
    ORCH -- "ego state, actor state" --> REND
    REND -- "rendered camera set" --> MODEL
    MODEL -- "trajectory (planner's or Sentinel's stop)" --> ORCH
    ORCH -- "nuPlan LQR tracker executes it<br/>collision + scoring vs the actor" --> ORCH
  end
  STACK --> EVID["per-run evidence<br/>scores · ego_poses · metrics ·<br/>per-frame monitor decisions (jsonl)"]
  EVID --> LOOP{"the research loop"}
  LOOP -- "hypothesize (pre-register the bar)" --> BUILD["build: monitor change<br/>as a reviewable server patch"]
  BUILD --> RUN["run: OFF vs arm,<br/>same episodes, seed-paired"]
  RUN --> MEASURE["measure: NCAP score · collision % ·<br/>safe-progress (safety × route progress)"]
  MEASURE --> ATTR["attribute: ablate WHY —<br/>nulls published with the wins"]
  ATTR --> LOOP
  EVID -- "committed raw<br/>(logs, jsonl, run JSONs)" --> AUDIT["independent verification pass<br/>re-derives every claim from the archive;<br/>corrections applied in place<br/>(experiments/VERIFICATION.md)"]
  AUDIT -. "withdrew one headline,<br/>strengthened three nulls" .-> LOOP
  classDef stack fill:#f3f0fa,stroke:#5e35b1,color:#22163d;
  classDef loop fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  classDef ev fill:#fff8e1,stroke:#b28704,color:#3d2f00;
  classDef audit fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  class ORCH,REND,MODEL stack;
  class LOOP,BUILD,RUN,MEASURE,ATTR loop;
  class EVID ev;
  class AUDIT audit;
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

**Iteration 2 won on safety; iteration 3 showed that win is not yet deployable, and corrected an
over-claim.** That arc, in order:

1. **Iter 2 — pre-registered safety win (holds).** On the public-mini NeuroNCAP corpus, a
   Sentinel-monitored **frozen** UniAD beats the same unmonitored planner *on the NeuroNCAP safety
   score*: pooled **1.92 → 4.67**, collision **65% → 13%** (side-impact 100% → 0%), delta **+2.75,
   95% CI [+2.21, +3.22]** (excludes 0). Planner frozen, signal label-free, one L4, public data.
   [`iter2_monitor/RESULT.md`](experiments/iter2_monitor/RESULT.md).
2. **Iter 2 ablation — the introspective signal is essential.** A naive distance brake (no forecast)
   leaves frontal collisions at 83% (≈ the 80% unmonitored); the closing-speed-from-forecast TTC
   trigger is what cuts them to 40% and side to 0%. [`ABLATION.md`](experiments/iter2_monitor/ABLATION.md).
3. **Iter 3 — the deployment metric (safe-progress) overturns the selectivity story.** Measuring
   *route progress* alongside safety, the TTC monitor **over-brakes**: it freezes even the benign clean
   scene (ego drives **4.9 m vs the unmonitored 32.4 m**), barely better than a trivial always-brake,
   and on safe-progress the **unmonitored planner wins** (OFF 2.08 · TTC 0.58 · always 0.49). The
   iter-2 claim that the monitor was *selectively idle* on the clean scene was an unverified inference
   and is **wrong** — corrected in place. The geometric trigger brakes whenever the ego closes on *any*
   object, not only on real failures. [`iter3_progress/RESULT.md`](experiments/iter3_progress/RESULT.md).
4. **Iter 4 — gate on the agent's closing speed: selectivity solved, net-positive (partial win).**
   Triggering only when an *agent is actively driving at the ego* (not when the ego approaches a passive
   object) **restores the clean scene to normal driving — 32.4 m, identical to OFF, 0 interventions** —
   and the monitor goes **net-positive on the deployment metric: safe-progress 2.80 > OFF 2.08 >
   over-braking 0.64.** Honest split: pre-registered H4 criterion 1 (selectivity) **met**, criterion 2
   (keep danger safety) **failed** — the gate *under*-brakes real threats (side-impact reverts to OFF)
   because it reads agent velocity from the planner's *optimistic* forecast and so filters out the very
   actors it should catch. [`iter4_gated/RESULT.md`](experiments/iter4_gated/RESULT.md).

5. **Iter 5 — observed-velocity gating: selectivity holds, frontal recovers, side resists.** Estimating
   agent velocity from *actual multi-frame tracking* (world-frame, ego-motion-compensated) instead of the
   optimistic forecast keeps the clean scene identical to OFF (0 interventions), stays net-positive
   (safe-progress 2.35 > 2.08), and **recovers frontal safety (collision 83% → 67%)** where the forecast
   gate could not. But **side-impact is still 100%** — its early warning lives in the ego's own
   converging motion, exactly the term the selective gate removes. The arms now bracket the trade
   precisely: total-closing catches every threat but over-brakes; agent-closing is selective but blind to
   the side case. [`iter5_tracked/RESULT.md`](experiments/iter5_tracked/RESULT.md).

6. **Iter 6 — plan-vs-tracked-path CPA solves the side-impact case.** Braking when the ego's *planned*
   path crosses an agent's *tracked* path (closest point of approach, world frame) **drops side-impact
   from 100% to 0% (8/8 avoided)** — the T-bone that resisted iterations 4–5 is caught *geometrically*,
   from the crossing itself. The honest cost: the 2.5 m margin also flags the ego's benign close pass of
   the stationary object, so CPA over-brakes the clean scene (33 → 22 m) and pooled safe-progress dips
   just below OFF (2.17 vs 2.32). The two live approaches are now complementary: iter 5 is selective but
   side-blind; iter 6 catches the side case but over-brakes. [`iter6_cpa/RESULT.md`](experiments/iter6_cpa/RESULT.md).

7. **Iter 7 — margin sweep: three of four at once, and why the fourth resists.** A tighter CPA margin
   (1.5 m) **restores clean-scene selectivity (32.3 m = OFF) and keeps side-impact at 0%** — but frontal
   reverts to 100%. The reason is fundamental: the head-on actor defeats plan-vs-path CPA at *any* tight
   margin because the planner's **optimistic plan** believes it clears by 3–4 m, so the plan-vs-actor
   closest approach never drops near the margin. Side (paths truly cross to ~0) and frontal (optimistic
   plan) need *different* detectors — no single margin holds all four. [`iter7_margin/RESULT.md`](experiments/iter7_margin/RESULT.md).

8. **Iter 8 — the union: one config, three of four at once.** Braking on **(plan-vs-path CPA < 1.5 m)
   OR (observed agent-closing TTC < 2.5 s)** is the first configuration that is **simultaneously
   selective (clean 30.2 m ≈ OFF), net-positive (safe-progress 2.53 > OFF 2.32), and side-solving
   (100 → 12.5%, 7 of 8 — verification-corrected from the originally-reported 0%)** — with frontal
   impact strongly *mitigated* (score 1.31 → 2.43). The union works exactly
   as reasoned: CPA catches the side crossing, observed-closing catches the frontal the optimistic plan
   hid, and neither fires on the passive object. [`iter8_union/RESULT.md`](experiments/iter8_union/RESULT.md).

9. **Iter 9 — evasive steering for the frontal head-on: refuted.** The state-of-the-art active-safety
   move (AEB **+ AES**) is to steer around a head-on rather than stop in its path. Implemented threat-aware
   (side → stop, head-on → lateral swerve) and tested — and it **makes frontal worse**: evade 1.66/100%
   vs the stop-based union's 2.53/83% (more collisions *and* higher impact). A 4 m swerve while keeping
   speed can't clear the aggressively-converging actor in time, and not shedding speed strikes harder than
   the committed stop. Selectivity and the side solution are preserved; only the evasive *trajectory* is
   inadequate. **Reported as a null — the committed stop (the union) stays the best frontal response.**
   [`iter9_evade/RESULT.md`](experiments/iter9_evade/RESULT.md).

10. **Iter 10 — braking evasion into a tracked-clear gap: also refuted.** The iter-9 null's refined
    evasion — shed speed *and* steer toward the open side — lands at **1.67/100%**, essentially
    identical to iter 9 and again worse than the pure stop's 2.53/83%. Two independent evasion families
    now converge on the same result: adding lateral steering to the head-on hurts (splitting effort
    between braking and steering realizes less deceleration, and the dodge doesn't complete in time).
    [`iter10_brakevade/RESULT.md`](experiments/iter10_brakevade/RESULT.md).

**Net, stated plainly — eleven iterations plus an independent verification pass.** The **union
(iter 8) is the best monitor** of the campaign: selective (clean-scene behaviour identical to the
unmonitored planner at n=20), side-impact 100% → 30%, frontal *mitigated* (score 0.84 → 2.36), and
**net-positive on safe-progress with a CI that excludes zero** (+0.398, [+0.133, +0.665], 20
unique episodes/scene — re-established after the original pooled version was withdrawn by audit).
The frontal head-on *ceiling* is firmly established — a committed stop is the best frontal
response, and **three separate evasion designs (iters 9, 10, 11) were tested and honestly
refuted**, all worse than stopping, the last one dangerous on false alarms (re-confirmed at n=20:
25% clean-scene collisions vs OFF's 10%). Frontal head-on *prevention* is a genuinely hard open
problem, not a maneuver away — which is exactly what the introspective plan-selection line attacks
next.

**What's next.** With invented maneuvers exhausted for the frontal edge case, three lines remain —
one new mechanism and two scaling milestones:

- **Introspective plan selection (the active line).** Stop overriding the planner; **re-rank the
  frozen planner's own candidate trajectories** by the label-free risk score and execute the safest
  feasible one. Safe on false alarms *by construction* (every candidate is planner-generated and
  in-distribution — the iteration-11 false-alarm crash is structurally impossible), and the first
  mechanism with a credible path to *preventing* the head-on rather than softening it. Plan:
  [`docs/NEXT_FRONTIER_INTROSPECTIVE_PLAN_SELECTION.md`](docs/NEXT_FRONTIER_INTROSPECTIVE_PLAN_SELECTION.md).
- **A second frozen planner (VAD).** Does the union transfer beyond UniAD, or is it UniAD-specific? VAD
  exposes the identical output schema, so the monitor's logic is unchanged — the stack is built and the
  union is patched onto VAD; the one remaining step is generating VAD's NeuroNCAP-specific data-infos.
  Staged to a precise restart point: [`vad_generalization/STATUS.md`](experiments/vad_generalization/STATUS.md).
- **The full 14-scene benchmark.** All results here are on the 2 NeuroNCAP scenes present in public
  `v1.0-mini`; the averaged published number needs the gated ~290 GB trainval set (a free nuScenes
  account). That is the one dependency external to this repo.

Scope throughout, stated plainly: 2 public-mini scenes, single-digit-to-20 runs, one L4 — a
method-development loop on public data, **not** a claim against the full 14-scene published benchmark.

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

# the definitive n=20 measurement (+0.398, CI [+0.133, +0.665]) — committed output
cat experiments/verification/proof_v20.txt             # regenerate: analyze_v20.py (paths in header)
```

The closed-loop stack itself is three public Docker images (NeuRAD renderer · frozen planner ·
NeuroNCAP orchestrator/scorer) on a single L4; the monitor is a self-contained patch injected into
the planner's inference server, gated by environment variables so every arm (OFF / union / RSS /
ablations) is one switch. Each experiment directory is self-describing:

| path | what it holds |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | frozen win bar; research-loop design |
| [`experiments/iter1_reproduce/`](experiments/iter1_reproduce) · [`iter1b_partial_baseline/`](experiments/iter1b_partial_baseline) | stack stood up; baseline reproduced + collision corpus |
| [`experiments/iter2_monitor/`](experiments/iter2_monitor) | the signal (G1, AUROC 0.83), the first A/B, the ablation, and the corrected over-claim |
| [`experiments/iter3_progress/`](experiments/iter3_progress) | the deployment metric (safe-progress) — the honest setback |
| [`experiments/iter4_gated/`](experiments/iter4_gated) … [`iter7_margin/`](experiments/iter7_margin) | selectivity → observed velocity → CPA → margin sweep |
| [`experiments/iter8_union/`](experiments/iter8_union) | **the definitive monitor** (union of two detectors) |
| [`experiments/iter9_evade/`](experiments/iter9_evade) · [`iter10_brakevade/`](experiments/iter10_brakevade) · [`iter11_early_evade/`](experiments/iter11_early_evade) | three refuted evasion designs for frontal prevention (reported nulls) |
| [`experiments/union_validation/`](experiments/union_validation) | pooled bootstrap CI — **withdrawn** (invalid pooling); corrected in place |
| [`experiments/VERIFICATION.md`](experiments/VERIFICATION.md) · [`verification/`](experiments/verification) | **independent verification pass**: audit, corrections, committed raw evidence, fresh n=20 re-measurement, safety-case analysis |
| [`experiments/iter12_plan_selection/`](experiments/iter12_plan_selection) | **introspective plan selection** (active): pre-registered checkpoint + candidate logging |
| [`experiments/iter13_rss_baseline/`](experiments/iter13_rss_baseline) | **RSS-style formal-envelope baseline** (pre-registered, queued) |
| [`experiments/vad_generalization/`](experiments/vad_generalization) | second-planner generalization, staged |

Every result folder carries a `RESULT.md` with the real per-run numbers, the exact server patch, and the
run script. `sentinel/monitor.py` is the pure-geometry monitor with unit tests (`tests/`); CI runs ruff +
pytest on every push.

## Data & honesty

Public datasets only (nuScenes via NeuroNCAP); no fleet or proprietary data; no frames
redistributed. Published baselines are single-preprint and unreproduced — reproducing them is our
true starting line, and every null is reported, not buried.
