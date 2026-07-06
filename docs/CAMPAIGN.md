# The campaign, iteration by iteration — the honest arc in full

Moved from the README for weight; every item links to its experiment directory with per-run
numbers and the exact patch. The summary table lives in the README score tracker.


**Iteration 2 won on safety; iteration 3 showed that win is not yet deployable, and corrected an
over-claim.** That arc, in order:

1. **Iter 2 — pre-registered safety win (holds).** On the public-mini NeuroNCAP corpus, a
   Sentinel-monitored **frozen** UniAD beats the same unmonitored planner *on the NeuroNCAP safety
   score*: pooled **1.92 → 4.67**, collision **65% → 13%** (side-impact 100% → 0%), delta **+2.75,
   95% CI [+2.21, +3.22]** (excludes 0). Planner frozen, signal label-free, one L4, public data.
   [`../experiments/iter2_monitor/RESULT.md`](../experiments/iter2_monitor/RESULT.md).
2. **Iter 2 ablation — the introspective signal is essential.** A naive distance brake (no forecast)
   leaves frontal collisions at 83% (≈ the 80% unmonitored); the closing-speed-from-forecast TTC
   trigger is what cuts them to 40% and side to 0%. [`ABLATION.md`](../experiments/iter2_monitor/ABLATION.md).
3. **Iter 3 — the deployment metric (safe-progress) overturns the selectivity story.** Measuring
   *route progress* alongside safety, the TTC monitor **over-brakes**: it freezes even the benign clean
   scene (ego drives **4.9 m vs the unmonitored 32.4 m**), barely better than a trivial always-brake,
   and on safe-progress the **unmonitored planner wins** (OFF 2.08 · TTC 0.58 · always 0.49). The
   iter-2 claim that the monitor was *selectively idle* on the clean scene was an unverified inference
   and is **wrong** — corrected in place. The geometric trigger brakes whenever the ego closes on *any*
   object, not only on real failures. [`../experiments/iter3_progress/RESULT.md`](../experiments/iter3_progress/RESULT.md).
4. **Iter 4 — gate on the agent's closing speed: selectivity solved, net-positive (partial win).**
   Triggering only when an *agent is actively driving at the ego* (not when the ego approaches a passive
   object) **restores the clean scene to normal driving — 32.4 m, identical to OFF, 0 interventions** —
   and the monitor goes **net-positive on the deployment metric: safe-progress 2.80 > OFF 2.08 >
   over-braking 0.64.** Honest split: pre-registered H4 criterion 1 (selectivity) **met**, criterion 2
   (keep danger safety) **failed** — the gate *under*-brakes real threats (side-impact reverts to OFF)
   because it reads agent velocity from the planner's *optimistic* forecast and so filters out the very
   actors it should catch. [`../experiments/iter4_gated/RESULT.md`](../experiments/iter4_gated/RESULT.md).

5. **Iter 5 — observed-velocity gating: selectivity holds, frontal recovers, side resists.** Estimating
   agent velocity from *actual multi-frame tracking* (world-frame, ego-motion-compensated) instead of the
   optimistic forecast keeps the clean scene identical to OFF (0 interventions), stays net-positive
   (safe-progress 2.35 > 2.08), and **recovers frontal safety (collision 83% → 67%)** where the forecast
   gate could not. But **side-impact is still 100%** — its early warning lives in the ego's own
   converging motion, exactly the term the selective gate removes. The arms now bracket the trade
   precisely: total-closing catches every threat but over-brakes; agent-closing is selective but blind to
   the side case. [`../experiments/iter5_tracked/RESULT.md`](../experiments/iter5_tracked/RESULT.md).

6. **Iter 6 — plan-vs-tracked-path CPA solves the side-impact case.** Braking when the ego's *planned*
   path crosses an agent's *tracked* path (closest point of approach, world frame) **drops side-impact
   from 100% to 0% (8/8 avoided)** — the T-bone that resisted iterations 4–5 is caught *geometrically*,
   from the crossing itself. The honest cost: the 2.5 m margin also flags the ego's benign close pass of
   the stationary object, so CPA over-brakes the clean scene (33 → 22 m) and pooled safe-progress dips
   just below OFF (2.17 vs 2.32). The two live approaches are now complementary: iter 5 is selective but
   side-blind; iter 6 catches the side case but over-brakes. [`../experiments/iter6_cpa/RESULT.md`](../experiments/iter6_cpa/RESULT.md).

7. **Iter 7 — margin sweep: three of four at once, and why the fourth resists.** A tighter CPA margin
   (1.5 m) **restores clean-scene selectivity (32.3 m = OFF) and keeps side-impact at 0%** — but frontal
   reverts to 100%. The reason is fundamental: the head-on actor defeats plan-vs-path CPA at *any* tight
   margin because the planner's **optimistic plan** believes it clears by 3–4 m, so the plan-vs-actor
   closest approach never drops near the margin. Side (paths truly cross to ~0) and frontal (optimistic
   plan) need *different* detectors — no single margin holds all four. [`../experiments/iter7_margin/RESULT.md`](../experiments/iter7_margin/RESULT.md).

8. **Iter 8 — the union: one config, three of four at once.** Braking on **(plan-vs-path CPA < 1.5 m)
   OR (observed agent-closing TTC < 2.5 s)** is the first configuration that is **simultaneously
   selective (clean 30.2 m ≈ OFF), net-positive (safe-progress 2.53 > OFF 2.32), and side-solving
   (100 → 12.5%, 7 of 8 — verification-corrected from the originally-reported 0%)** — with frontal
   impact strongly *mitigated* (score 1.31 → 2.43). The union works exactly
   as reasoned: CPA catches the side crossing, observed-closing catches the frontal the optimistic plan
   hid, and neither fires on the passive object. [`../experiments/iter8_union/RESULT.md`](../experiments/iter8_union/RESULT.md).

9. **Iter 9 — evasive steering for the frontal head-on: refuted.** The state-of-the-art active-safety
   move (AEB **+ AES**) is to steer around a head-on rather than stop in its path. Implemented threat-aware
   (side → stop, head-on → lateral swerve) and tested — and it **makes frontal worse**: evade 1.66/100%
   vs the stop-based union's 2.53/83% (more collisions *and* higher impact). A 4 m swerve while keeping
   speed can't clear the aggressively-converging actor in time, and not shedding speed strikes harder than
   the committed stop. Selectivity and the side solution are preserved; only the evasive *trajectory* is
   inadequate. **Reported as a null — the committed stop (the union) stays the best frontal response.**
   [`../experiments/iter9_evade/RESULT.md`](../experiments/iter9_evade/RESULT.md).

10. **Iter 10 — braking evasion into a tracked-clear gap: also refuted.** The iter-9 null's refined
    evasion — shed speed *and* steer toward the open side — lands at **1.67/100%**, essentially
    identical to iter 9 and again worse than the pure stop's 2.53/83%. Two independent evasion families
    now converge on the same result: adding lateral steering to the head-on hurts (splitting effort
    between braking and steering realizes less deceleration, and the dodge doesn't complete in time).
    [`../experiments/iter10_brakevade/RESULT.md`](../experiments/iter10_brakevade/RESULT.md).


11. **Iter 11 — early collision-course detection + evasion: the third and decisive refutation.** A
    4 s kinematic closest-approach detector (observed ego and agent velocities) with a time-gated
    lane change neither prevents the head-on (evade 83% = stop 83%) nor stays safe when wrong: the
    evasion **crashes the benign clean scene 50%** (it swerves into the parked car) and un-solves
    the side case. The structural lesson the three nulls prove together: **a committed stop
    degrades gracefully under false alarms; an invented swerve causes the crash it was meant to
    avoid.** Frontal-prevention-by-maneuver is closed.
    [`../experiments/iter11_early_evade/RESULT.md`](../experiments/iter11_early_evade/RESULT.md).

12. **The independent verification pass — a headline withdrawn, then re-established.** Re-deriving
    every claim from raw evidence established that NeuroNCAP episodes **replay deterministically
    per run index**, which invalidated the pooled "n=20" validation (really 8 unique episodes;
    honest CI [−0.27, +0.78] includes zero) — the net-positive headline was **withdrawn in
    place**. A fresh 20-unique-episode measurement then re-established it: safe-progress **+0.398,
    95% CI [+0.133, +0.665]**, side 100% → 30%, clean scene identical to OFF, with run indices
    0–7 reproducing the iteration-8 data exactly (apparatus check). Corrections were applied
    where documents disagreed with logs; all raw evidence committed.
    [`../experiments/VERIFICATION.md`](../experiments/VERIFICATION.md).

13. **Iter 12 — introspective plan selection: the planner has no plan B (pre-registered null).**
    UniAD's three command-conditioned candidate plans diverge up to 14 m in benign frames but
    **collapse to a 4 cm spread under threat** — 0 of 37 dangerous frames hold a viable escape
    (bar: >30%). Introspection sees the danger; the planner holds no safer intention to defer to.
    [`../experiments/iter12_plan_selection/RESULT.md`](../experiments/iter12_plan_selection/RESULT.md).

14. **Iter 13 — the formal-envelope baseline: stopping power is free, selectivity is not.** An
    RSS-style guaranteed-stopping envelope on identical inputs and actuator posts the campaign's
    best raw safety (clean 0%, frontal 30%, side 0%) **by near-paralysis** (ego 3.6–8.2 m vs
    21–32 m) and lands *below the unmonitored planner* on safe-progress (0.88 vs 1.83; union −
    RSS = +1.345, CI [+0.944, +1.701]) — quantifying, apparently for the first time closed-loop,
    the over-conservatism the literature only asserts.
    [`../experiments/iter13_rss_baseline/RESULT.md`](../experiments/iter13_rss_baseline/RESULT.md).

15. **Iter 14 — a second frozen planner (VAD): safety transfers, selectivity does not.** VAD's
    failure profile is inverted (stationary 85%, side 65% collisions); the union prevents exactly
    those failures (both → 0%) but over-brakes everywhere (safe-progress 2.30 → 0.75, CI
    [−2.06, −1.03]) — decision logs attribute it to the TTC term reading jittery
    nearest-neighbor IDs (VAD exposes no tracker). **Selectivity is a property of tracking
    quality, not of the decision rule alone.** VAD's native modes also stay below the escape
    viability bar (21% < 30%): candidate collapse is a two-planner spectrum.
    [`../experiments/vad_generalization/RESULT.md`](../experiments/vad_generalization/RESULT.md).

16. **The full 14-scene benchmark — the baseline reproduces; the win is decisive on the
    benchmark's metric and honest on ours.** Unmonitored UniAD pools to **2.15 vs the published
    1.84** (first independent reproduction); the union lifts it to **3.09 (+0.934, CI [+0.713,
    +1.155])**, driven by side (73% → 37%) and stationary (32% → 17%) — while the mini-scene
    deployment-metric win does **not** generalize (safe-progress −0.17, CI includes 0; the union
    over-brakes unseen benign-progress scenes, and frontal/0346 is named as a real regression).
    [`../experiments/full14_benchmark/RESULT.md`](../experiments/full14_benchmark/RESULT.md).

17. **Iter 15 — threat-cleared latch release: the new best configuration.** Releasing the latch
    after four consecutive verified-clear frames leaves every safety cell **identical to the
    union** (44 releases, 0 reopened cases) and recovers **+0.246 safe-progress over it (CI
    [+0.206, +0.293])** — strict domination. Against the unmonitored planner the deployment gap
    narrows to +0.08 but keeps a CI that includes zero: a *cost-of-stopping* floor in
    fixed-horizon episodes, which iteration 16 (a pre-registered softer-than-stop crawl) attacks.
    [`../experiments/iter15_latch_release/RESULT.md`](../experiments/iter15_latch_release/RESULT.md).

18. **Iter 16 — softer than a stop: the pre-registered null publishes; the stop stands.**
    Replacing the latched stop with the planner's own plan re-parameterized to a 2.0 m/s crawl
    (speed fixed from committed impact evidence before the run) posts the campaign's highest
    safe-progress (2.544; +0.096 over the released union, CI [+0.033, +0.167]) — and **fires the
    pre-registered side falsifier**: side collisions 37% → 57% (bar 45%), benchmark score 3.09 →
    2.64, with side-0108 collapsing 17% → 100% at 4–5 m/s impacts scoring zero. The mechanism:
    the stop is a **position guarantee** — it halts the ego short of the crossing point; the
    crawl delivers it there at contact time. With iteration 11 the result is two-sided: a swerve
    is unsafe when the trigger is wrong, a crawl is unsafe when it is right; only the committed
    stop is safe in both cases. [`../experiments/iter16_soft_stop/RESULT.md`](../experiments/iter16_soft_stop/RESULT.md).

19. **The power run — the benchmark result at 20 runs per pair; the deployment question resolved
    to a tight null.** 799 of 800 planned episodes (off/side-0921 documented at n=19 — its
    run_19 reproducibly froze the pre-swap host, 3/3 attempts on 2 physical hosts). The H-P0
    gate passed in full: run indices 0–5 of every pair in both arms reproduce the committed
    6-run evidence exactly, through five machine-freezing incidents whose root cause (memory
    exhaustion on a swapless image) was isolated by an on-box vitals watchdog and fixed with
    swap. Results: baseline reproduction holds (**2.12** pooled vs published 1.84); the released
    union lifts the benchmark score to **2.91 (+0.783, 95% CI [+0.605, +0.928])** — the n=6
    estimate (+0.934) was modestly optimistic and is replaced; safe-progress resolves to
    **−0.03, CI [−0.13, +0.07]** — the safety gain costs approximately nothing on the deployment
    metric; the frontal/0346 regression is confirmed real. The campaign's measurement phase is
    complete. [`../experiments/full14_power/RESULT.md`](../experiments/full14_power/RESULT.md).

20. **Iter 17 — threat-class routing: the safety gate fails on one misrouted crossing; the
    deployment flip is proven achievable.** A geometric router (stop wherever a tracked object's
    constant-velocity path overlaps the planned corridor at 2.0 m; crawl otherwise) posts a new
    campaign-high safe-progress (2.598) and — as a voided-by-gate observation — the **first
    deployment CI excluding zero vs the unmonitored planner** (+0.226, CI [+0.004, +0.421]).
    But side collisions reach 47% (bar 45%), carried entirely by side-0108, whose crossing
    geometry the projection misses (17% → 67%); the benchmark score gives up 0.170 against a
    0.15 tolerance. **The pre-registered null publishes; the released union survives its fourth
    challenger.** The open problem narrows: a crossing-safe routing predicate (successors named:
    firing-term routing, N-frame no-overlap confirmation, windowed observed-position overlap).
    [`../experiments/iter17_threat_routing/RESULT.md`](../experiments/iter17_threat_routing/RESULT.md).

21. **Iter 19 — the diversity-trained candidate head: the gate refuses the closed loop, and
    the collapse is located.** A 1.2M-parameter K=8 head, trained with an explicit diversity
    objective on the planner's own planning-query embeddings (60 scenes disjoint from all
    evaluation), passes benign fidelity but produces **0/37 feasible escapes** on iteration
    12's dangerous frames — 16 diverging candidates appeared, every one kinematically
    infeasible. The pre-registered falsifier fired exactly: the conditioning choice is
    refuted, not the mechanism class. Third measurement by a third route (commands 0/37; VAD
    modes 21%; learned head 0/37): **the plan-B deficit sits in the planner's internal
    planning representation**, not in any decoder above it.
    [`../experiments/iter19_diversity_head/RESULT.md`](../experiments/iter19_diversity_head/RESULT.md).

22. **Iter 20 — VAD tracker portability: the offline gate fails before GPU time.** The
    registered replay of committed VAD-union logs through the iteration-18 tracker defaults
    removes **0/47** raw TTC fires (bar: >=80%), retains only **4/6** side firing episodes
    (bar: >=90%), and increases frontal firing frames **79 -> 90** rather than reducing them.
    The simple association + smoothing tracker is therefore not the VAD transfer repair, and
    no VAD closed-loop run launches from this hypothesis. The broader tracking-quality
    constraint remains, but this zero-GPU bridge is closed.
    [`../experiments/iter20_vad_tracker_portability/RESULT.md`](../experiments/iter20_vad_tracker_portability/RESULT.md).

23. **Iter 21 — BEV-conditioned diversity head: the scene-level survivor also fails the
    offline gate.** The registered BEV extraction and K=8 head training completed on
    train-split scenes disjoint from the evaluation corpus, and B0 passed exactly: 311/311
    iteration-12 frames joined with zero executed-plan mismatches. But the gate failed every
    behavioral bar: **0/37** feasible escapes (bar: >=12/37), all-candidate validity
    **574/2488 = 23.1%** (bar: >=90%), benign best-of-K error **1.449 m** (bar: <=0.780 m),
    and no selector-compatible escape because none existed. The registered BEV head therefore
    does not recover a deployable plan B, and no closed-loop run launches from this hypothesis.
    [`../experiments/iter21_bev_diversity_head/RESULT.md`](../experiments/iter21_bev_diversity_head/RESULT.md).

24. **Iter 22 — causal planner interpretability Stage 1: the S0 gate fails before causal
    testing.** The registered non-evaluation extraction completed with 1,507 non-reset rows and
    a 1,507-row GT sidecar, but every row failed the committed timestamp join (`missing_gt`):
    extracted timestamps were second-level while GT timestamps were microsecond-level. The frozen
    manifest/staged-data combination also produced **0 heldout GT rows**, so the heldout count
    floors could not be evaluated or met. Per the hypothesis, Stage 1 stopped before probe
    fitting, activation-direction writing, calibration-grid replay, iteration-12 scoring, or
    closed-loop work. This is a data-support/integrity null, not evidence for or against the
    causal signal itself. [`../experiments/iter22_causal_planner_interpretability/RESULT.md`](../experiments/iter22_causal_planner_interpretability/RESULT.md).
