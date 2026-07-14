# Iteration 110 - HUGSIM support-preserving candidate design

Frozen after iteration 109 was published and the handoff was refreshed, but before any
iteration-110 analyzer, generated proof artifact, result document, handoff update, or claim. This
is an offline candidate-design audit over committed HUGSIM reports only. It launches no GPU work,
changes no thresholds, changes no planner/action-control code, changes no HUGSIM metrics, and does
not retune Sentinel.

## Context

Iteration 109 explained the iteration-108 support null. The timing-aware batch did not fail for
one reason: `7/13` rows had foreground-absent or empty collision provenance, and `4/13` rows had
observed post-collision monitor fire. The actionable split was channel-level: `2/5` `ttc_only`
slots were foreground-classifiable, while `0/8` `cpa_only` slots were foreground-classifiable in
that batch.

The next design question is therefore not "launch another timing-aware 13-slot batch." The next
question is whether the committed HUGSIM pool can support a future candidate core that preserves
the only observed foreground-classifiable support signal: TTC-channel rows with prior exact or
scenario-level classifiable evidence, excluding exact rows already observed as non-classifiable.

## Research question

Can committed HUGSIM artifacts define a deterministic support-preserving candidate core for a
future run, and do they support a full `13`-slot support-preserving schedule without falling back
to the residual-risk rows that iteration 109 identified?

This iteration may produce a support-preserving core, a fallback-pressure table, and a fresh-pool
scarcity table. It may not select a launch manifest, run a simulator, approve GPU work, retune
thresholds, or claim repair.

## Frozen inputs

The analyzer may read only these committed files:

- Iteration 52 timing report:
  `experiments/iter52_hugsim_on_collision_timing_audit/proof-timing/on_collision_timing_report.json`
- Iteration 54 provenance support report:
  `experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json`
- Iteration 59 actor-match report:
  `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`
- Iteration 104 provenance-batch actor-match report:
  `experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/provenance_batch_actor_match_report.json`
- Iteration 109 timing-aware support-yield decomposition report:
  `experiments/iter109_hugsim_timing_aware_support_yield_decomposition/proof-decomposition/timing_aware_support_yield_decomposition_report.json`

It may not read live GPU state, raw box paths outside committed proof, raw episode directories,
uncommitted artifacts, or launch manifests generated after this pre-registration.

## Frozen source checks

The analyzer must return an infrastructure null unless all checks pass:

1. Iteration 52 verdict is `TIMING_AUDIT_COMPLETE` and exposes exactly `104` `pairs`.
2. Iteration 54 verdict is `PROVENANCE_SUPPORT_NULL`, has no infrastructure problems, and exposes
   exactly `104` `pairs`.
3. Iteration 59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`, has no infrastructure problems, and
   exposes exactly `8` `episodes`.
4. Iteration 104 verdict is `HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_SUPPORT_NULL`, has no
   infrastructure problems, exposes exactly `13` `episodes`, and records the frozen support floor
   `min_classifiable_bar == 4`.
5. Iteration 109 verdict is `HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE`, has no
   infrastructure problems, exposes exactly `13` `slots`, and reports `classifiable_success == 2`.
6. Every timing-eligible iteration-54 row selected or reported by this analyzer must cross-check
   against iteration 52 on `(scenario, run)`, timing bin, `first_on_nc_time`, `first_fire_ts`, and
   `first_fire_lead_time`.

## Frozen candidate universe

A row is timing-eligible only when all conditions hold:

- iteration-54 `on_collision == true`;
- `fire_timing_label` is `long_lead_fire` or `short_lead_fire`;
- `first_fire_lead_time` is finite and `>= 0`;
- `first_fire_channel` is `ttc_only` or `cpa_only`;
- `monitor_provenance_label` is `unique_ttc_object` or `unique_cpa_object`.

For each timing-eligible row, the analyzer builds prior-support evidence from iterations 59, 104,
and 109:

- exact support evidence uses `(scenario, run)` where the source report has a finite run;
- iteration-59 rows are scenario-level evidence because that report does not expose run ids;
- `classifiable_foreground` and iteration-109 `classifiable_success` are positive support
  evidence;
- every other support/residual label is non-classifiable evidence.

## Frozen labels

Each timing-eligible row receives exactly one design label:

- `exact_ttc_classifiable_anchor`: the row is `ttc_only`, the exact `(scenario, run)` has positive
  support evidence, and the exact row has no non-classifiable evidence.
- `ttc_classifiable_scenario_analogue`: the row is `ttc_only`, the scenario has positive support
  evidence, and the exact `(scenario, run)` has no non-classifiable evidence, but the exact row is
  not itself a positive anchor.
- `ttc_residual_risk_probe`: the row is `ttc_only` but does not satisfy either support-preserving
  label above.
- `cpa_residual_risk_fallback`: the row is `cpa_only`.
- `ineligible_or_schema_gap`: any row that cannot be safely labeled under the rules above.

Only the first two labels are support-preserving labels.

## Frozen selection rule

The analyzer must:

1. enumerate all timing-eligible rows and their labels;
2. form `support_preserving_core_rows` from all rows labeled `exact_ttc_classifiable_anchor` or
   `ttc_classifiable_scenario_analogue`;
3. sort core rows by:
   - label priority: exact anchors before scenario analogues;
   - timing priority: `short_lead_fire` before `long_lead_fire`;
   - descending `first_fire_lead_time`;
   - `scenario`;
   - `run`;
4. keep at most two rows per scenario in the core;
5. enumerate, but do not merge into the core, `fallback_pressure_rows` from
   `ttc_residual_risk_probe` followed by `cpa_residual_risk_fallback` under the same deterministic
   ordering;
6. enumerate `fresh_primary_rows` after excluding every scenario that appears in iteration 59,
   iteration 104, or iteration 109 prior-support evidence.

This iteration may report that a full `13`-slot support-preserving schedule is unavailable. That
is a valid result, not a failure of the analyzer.

## Frozen bars

- `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_INFRA_NULL`: any frozen input is missing,
  malformed, has the wrong verdict, has infrastructure problems, fails a required count, fails a
  timing cross-check, or any timing-eligible row receives no label.
- `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_13_SLOT_COMPLETE`: source checks pass and at least
  `13` support-preserving core rows remain after the two-per-scenario cap.
- `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE`: source checks pass and at least `4`
  but fewer than `13` support-preserving core rows remain after the two-per-scenario cap.
- `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_SUPPORT_NULL`: source checks pass but fewer than `4`
  support-preserving core rows remain after the two-per-scenario cap.

The `4`-row core floor is inherited from the actor-match support floor used by iterations 104 and
108. This is still an offline design bar, not an outcome bar.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-design/support_preserving_candidate_design_report.json`;
- `proof-design/support_preserving_candidate_design.md`;
- `proof-design/analyze_support_preserving_candidate_design.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the frozen committed inputs.
4. Publish `RESULT.md`, update README/NEXT_PHASE/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No actor-causality, actor-match support upgrade, repair, threshold-value, transfer, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, retuning, production, commercial,
schedule-selection, launch-manifest, or GPU-approval claim.
