# NeuroNCAP placebo semantics control design

Status: iteration-133 adversarial-control design note. This freezes a future placebo/sham
control protocol only; it authorizes no GPU launch, NeuroNCAP execution, HUGSIM execution,
scenario generation, reserved artifact creation, repair, deployment, production, commercial,
or frontier-equivalence claim.

## Source Anchors

- full-power NCAP delta: `0.783`
- full-power NCAP CI95: `[0.605, 0.928]`
- full-power safe-progress delta: `-0.032`
- RSS-style union-minus-RSS safe-progress: `1.345`
- opportunity-audit rho: `0.7003`

## Primary Placebo

`semantics_scrambled_budget_matched_placebo` preserves the released union's latched-stop/release actuator family but
removes live Sentinel risk semantics. It replays deterministic timing/budget windows from
donor schedules selected by committed identifiers while excluding the target scenario pair
and target seed.

## Future Run Contract

- OFF, released union, and placebo arms must run under the same frozen planner and benchmark stack.
- The future launch manifest must bind scenario ids, run indices, donor ids, actuator budgets, patch hashes, analyzer hashes, and environment receipts.
- The analyzer must report NCAP and safe-progress; safe-progress cannot be hidden by a benchmark-score win.
- Nulls publish at full weight.

## Verdict Classes

- `SEMANTIC_VALUE_CONFIRMED`
- `PLACEBO_EXPLAINS_GAIN`
- `PLACEBO_HARM_OR_NULL`
- `PLACEBO_CONTROL_INFRA_NULL`

## Claim Boundary

placebo-semantics control design only; no GPU launch, NeuroNCAP execution, HUGSIM execution, reserved path creation, generated scenario artifact, scenario generation, execution-slot selection, learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark-ranking, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
