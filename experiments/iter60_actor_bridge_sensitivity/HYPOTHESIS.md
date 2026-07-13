# Iteration 60 - actor-match bridge sensitivity audit

Frozen before any iteration-60 analyzer edit, analyzer run, result, or claim. This is an offline
post-result sensitivity audit over committed iteration-59 proof only. It launches no GPU work,
reads no box state, creates no new HUGSIM episodes, and does not retune Sentinel.

## Process disclosure

This audit is not blind. Iteration 59 is already published as `ACTOR_MATCH_AUDIT_COMPLETE`.
Before freezing this file, the iteration-59 result and generated report were read. They show:

- eight registered ON episodes completed with intact proof;
- three rows were `classifiable_foreground`;
- all three classifiable rows were `actor_mismatch` under the frozen iteration-59 bridge;
- distances were `15.43 m`, `21.99 m`, and `37.04 m`;
- the other rows were no-fire, post-collision-fire, or background-only.

Iteration 60 is therefore not allowed to produce a surprise actor-match headline. It may only ask
whether the iteration-59 mismatch labels are robust to a bounded, pre-registered set of plausible
coordinate/temporal bridge variants.

## Research question

Do the three iteration-59 classifiable foreground mismatches remain mismatches under a bounded
family of axis-order, sign, and propagation variants, or can any plausible bridge variant turn a
classifiable row into an `actor_match`?

This matters because iteration 58 showed monitor logs and HUGSIM provenance use different
coordinate conventions. Iteration 59 froze one bridge. Iteration 60 stress-tests that bridge
without fitting or learning a transform from outcomes.

## Frozen inputs

Inputs are exactly:

- [`../iter59_hugsim_actor_match_audit/proof-actor-match/`](../iter59_hugsim_actor_match_audit/proof-actor-match/)
- [`../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`](../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json)

The analyzer must cross-check that the iteration-59 report verdict is `ACTOR_MATCH_AUDIT_COMPLETE`
and that exactly three rows have `support_label == classifiable_foreground`. It may analyze only
those three rows for bridge sensitivity.

## Frozen bridge family

For each classifiable row, reconstruct the monitor first-fire object exactly as iteration 59 did.
Then evaluate all variants in this fixed grid:

- temporal source: first-fire object position, propagated object position at the HUGSIM first
  foreground timestamp;
- axis order:
  - `(forward, lateral) = (monitor_local_y, monitor_local_x)`;
  - `(forward, lateral) = (monitor_local_x, monitor_local_y)`;
- sign flips: `forward_sign ∈ {-1, +1}`, `lateral_sign ∈ {-1, +1}`.

This yields `2 * 2 * 2 * 2 = 16` bridge variants per row. The analyzer may compute the minimum
distance over this frozen family. It may not fit translation, scale, rotation, yaw, scenario-level
offsets, object-specific offsets, or choose a variant per outcome after seeing the distances
outside this fixed grid.

Distance labels use the iteration-59 thresholds:

- `bridge_match_possible`: minimum distance `<= 3.0 m`;
- `bridge_ambiguous_possible`: minimum distance in `(3.0 m, 6.0 m]`;
- `robust_mismatch`: minimum distance `> 6.0 m`.

## Frozen bars

- `BRIDGE_SENSITIVITY_INFRA_NULL`: required iteration-59 proof/report files are missing, the
  iteration-59 verdict/cross-check fails, fewer or more than three classifiable rows are found,
  or monitor/HUGSIM reconstruction fails for any classifiable row.
- `BRIDGE_SENSITIVE_NULL`: at least one classifiable row has `bridge_match_possible`.
- `BRIDGE_AMBIGUOUS_NULL`: no row has `bridge_match_possible`, but at least one row has
  `bridge_ambiguous_possible`.
- `BRIDGE_ROBUST_MISMATCH_COMPLETE`: all three classifiable rows are `robust_mismatch`.

## Forbidden claims

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. A robust mismatch result would say only that
the three iteration-59 classifiable mismatch rows do not disappear under this bounded bridge
sensitivity grid.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-bridge/bridge_sensitivity_report.json`;
- `proof-bridge/bridge_sensitivity.md`;
- `proof-bridge/analyze_bridge_sensitivity.command.txt`;
- `RESULT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add analyzer/tests; run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-59 proof.
4. Publish `RESULT.md`, update README/NEXT_PHASE/CONTINUITY/HANDOFF, verify, commit, and push.
