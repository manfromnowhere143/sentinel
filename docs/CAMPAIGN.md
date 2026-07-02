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

