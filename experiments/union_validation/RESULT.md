# Union — statistical validation: net-positive confirmed at n=20 (bootstrap CI excludes 0)

The campaign's headline is the iteration-8 union: a label-free monitor on a frozen planner that is
selective, side-solving, and **net-positive over the unmonitored planner on the progress-aware
deployment metric**. That last claim was asserted at single-digit run counts. Here it is put on a
statistical footing, using the pre-registration's own bar: a **drive-clustered bootstrap CI on the
safe-progress advantage that excludes zero**.

## Method — pool the independent replications

The union and OFF arms were run together (same seeds) **three separate times** — iterations 8, 9, and
10 — with identical configuration for the union and OFF arms. Pooling those replications gives
**20 independent-seed runs per scene per arm**. Progress is normalized to the pooled-OFF mean ego
distance per scene; safe-progress = NCAP score × progress; the pooled metric averages the three scenes.
The CI is a 5000-sample bootstrap resampling runs **within each scene** (drive-clustered), fixed seed.
Reproduce: `pooled_union_ci.py`.

## Result

| scene (pooled n=20) | OFF score / collision % | union score / collision % |
|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% | 5.00 / 0% |
| frontal/0103 | 1.07 / 80% | 2.49 / 85% |
| side/0103 | 0.64 / **100%** | 4.75 / **5%** |

**Pooled safe-progress: OFF 2.142 → union 2.597. Delta = +0.455, 95% CI [+0.083, +0.793].**

> **The CI excludes 0 — the union is net-positive over the unmonitored planner at a 95% confidence
> level, on 20 independent-seed runs per scene.** The pre-registered deployment-metric bar is met.

## Reading it honestly

- **The win is real but modest.** The advantage is +0.46 safe-progress with a lower CI bound of +0.08 —
  positive and significant, not large. The campaign never claimed more; this pins the size.
- **The advantage is carried by the side case.** Side-impact goes 100% → **5%** at n=20 (near-complete
  prevention; the residual 5% is 1 of 20 runs). That is the structural source of the net gain, on top
  of an unchanged clean scene and a mitigated (not prevented) frontal.
- **Frontal remains mitigated, not prevented** — 80% → 85% collision (within noise), score 1.07 → 2.49
  (impact cut). Consistent with the iteration 9/10 finding that the frontal ceiling is a committed
  stop; two evasion families were refuted trying to beat it.

## What this establishes

The union is not a lucky single-run result: across 60 pooled runs it beats the unmonitored planner on
the deployment-realistic metric with a bootstrap CI that excludes zero, while remaining selective and
solving side-impact. That is the campaign's defensible, statistically-validated headline — label-free,
frozen planner, one L4, public data. Scope is unchanged: 3 scenes of 2 public-mini sequences; the full
14-scene published benchmark (gated trainval) is the next validation at scale.
