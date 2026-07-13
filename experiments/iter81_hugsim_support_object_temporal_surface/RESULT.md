# Iteration 81 - HUGSIM support-object temporal surface audit: HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE

Status: completed offline temporal surface audit over the two fixed foreground-supported support
objects from iteration 78. No GPU work, live box read, HUGSIM run, threshold change, repair, or
retuning was launched.

## Frozen proof

- Pre-registration: `experiments/iter81_hugsim_support_object_temporal_surface/HYPOTHESIS.md`
- Analyzer: `experiments/iter81_hugsim_support_object_temporal_surface/analyze_support_object_temporal_surface.py`
- Tests: `tests/test_iter81_support_object_temporal_surface.py`
- Proof command: `experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/analyze_support_object_temporal_surface.command.txt`
- Machine proof: `experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/temporal_report.json`
- Human proof: `experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/temporal.md`

## Result

The audit evaluated exactly the two registered support objects and returned
`HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`.

- `target_objects`: `2`
- `evaluated_objects`: `2`
- `support_object_ever_active`: `1`
- `support_object_visible_never_surface`: `1`
- `support_object_borderline_only`: `0`

| audit id | support object | label | present | active | borderline | first active | first borderline | min cpa | min finite ttc |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `both_distinct_extreme` | `9` | `support_object_ever_active` | `9` | `3` | `2` | `7.0 s` | `5.5 s` | `4.6301 m` | `0.3391 s` |
| `ttc_medium_a` | `10` | `support_object_visible_never_surface` | `15` | `0` | `0` | `None` | `None` | `7.2464 m` | `None` |

## Interpretation

Iteration 81 separates the two foreground-supported full-set objects that iteration 78 found
nonselected and subthreshold at the fixed support events.

`both_distinct_extreme` support object `9` was subthreshold at the fixed pre-event row, but later
became borderline at `5.5 s` and active at `7.0 s`, after first foreground support at `5.25 s`.
That makes this support object a late-emerging hazard-surface object, not a never-surface object.

`ttc_medium_a` support object `10` stayed visible across `15` decision frames and never became
active or borderline, despite being the foreground-support object for both fixed support events in
that row. That keeps the visible-never-surface branch alive for this object.

The mechanism lead is therefore mixed: one support object arrives late to the released surface,
while the other remains outside the active/borderline surface entirely. This does not repair the
released rule, does not establish actor causality, and does not authorize threshold tuning.

## Claim boundary

Two-object descriptive temporal surface audit only; no actor-causality, repair, threshold-value,
transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance,
commercial-value, or retuning claim.
