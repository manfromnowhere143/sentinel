# Iteration 82 - HUGSIM support-object surface/provenance co-occurrence audit: HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE

Status: completed offline co-occurrence audit over the two fixed iteration-81 support objects.
No GPU work, live box read, HUGSIM run, threshold change, repair, or retuning was launched.

## Frozen proof

- Pre-registration: `experiments/iter82_hugsim_support_surface_bridge_cooccurrence/HYPOTHESIS.md`
- Analyzer: `experiments/iter82_hugsim_support_surface_bridge_cooccurrence/analyze_support_surface_bridge_cooccurrence.py`
- Tests: `tests/test_iter82_support_surface_bridge_cooccurrence.py`
- Proof command: `experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/analyze_support_surface_bridge_cooccurrence.command.txt`
- Machine proof: `experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/cooccurrence_report.json`
- Human proof: `experiments/iter82_hugsim_support_surface_bridge_cooccurrence/proof-cooccurrence/cooccurrence.md`

## Result

The audit evaluated exactly the two registered support objects and returned
`HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE`.

- `target_objects`: `2`
- `evaluated_objects`: `2`
- `objects_with_bridge_support`: `2`
- `objects_with_surface_bridge_cooccurrence`: `1`
- `support_surface_bridge_borderline_only`: `1`
- `support_bridge_never_surface`: `1`

| audit id | support object | label | present | bridge-supported | active+bridge | borderline+bridge | first bridge | first surface+bridge | best bridge | best surface bridge |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `both_distinct_extreme` | `9` | `support_surface_bridge_borderline_only` | `9` | `3` | `0` | `1` | `5.0 s` | `5.5 s` | `0.6565 m` | `0.9876 m` |
| `ttc_medium_a` | `10` | `support_bridge_never_surface` | `15` | `15` | `0` | `0` | `2.25 s` | `None` | `0.0863 m` | `None` |

## Interpretation

Iteration 82 tests whether the foreground-supported support objects ever align with the released
CPA/TTC surface on the same frame.

`both_distinct_extreme` object `9` has same-frame foreground bridge support and surface
co-occurrence, but only at the registered borderline level: one borderline+bridge frame at
`5.5 s`, best surface bridge distance `0.9876 m`, and zero active+bridge frames. Its later active
frames from iteration 81 do not carry bridge support under this audit's frozen bands.

`ttc_medium_a` object `10` is the opposite failure mode: it has bridge support in all `15` present
frames, including a best distance of `0.0863 m`, but has zero active or borderline frames.

The support-object side is therefore not missing bridge support. The remaining split is sharper:
one support object has only borderline co-occurrence, and the other has persistent bridge support
that never enters the released surface. This does not repair the rule, prove actor causality, or
authorize threshold tuning.

## Claim boundary

Two-object descriptive surface/provenance co-occurrence audit only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population,
HD-Score-invariance, commercial-value, or retuning claim.
