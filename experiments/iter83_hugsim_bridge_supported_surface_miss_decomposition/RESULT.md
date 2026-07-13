# Iteration 83 - HUGSIM bridge-supported surface-miss decomposition: HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE

Status: completed offline surface-miss decomposition over the bridge-supported frames of the two
fixed iteration-82 support objects. No GPU work, live box read, HUGSIM run, threshold change,
repair, or retuning was launched.

## Frozen proof

- Pre-registration: `experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/HYPOTHESIS.md`
- Analyzer: `experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/analyze_bridge_supported_surface_miss.py`
- Tests: `tests/test_iter83_bridge_supported_surface_miss.py`
- Proof command: `experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/analyze_bridge_supported_surface_miss.command.txt`
- Machine proof: `experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/surface_miss_report.json`
- Human proof: `experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/surface_miss.md`

## Result

The audit evaluated exactly the two fixed support objects and returned
`HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`.

- `target_objects`: `2`
- `evaluated_objects`: `2`
- `bridge_supported_frames`: `18`
- `active_bridge_supported_frames`: `0`
- `borderline_bridge_supported_frames`: `1`
- `finite_ttc_bridge_supported_frames`: `2`
- `bridge_supported_borderline_ttc_only`: `1`
- `bridge_supported_subthreshold_no_finite_ttc`: `1`

| audit id | support object | label | bridge frames | active | borderline | subthreshold | finite TTC | min active CPA margin | min active TTC margin |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `both_distinct_extreme` | `9` | `bridge_supported_borderline_ttc_only` | `3` | `0` | `1` | `2` | `2` | `+17.6718 m` | `+2.2761 s` |
| `ttc_medium_a` | `10` | `bridge_supported_subthreshold_no_finite_ttc` | `15` | `0` | `0` | `15` | `0` | `+5.7464 m` | `None` |

## Interpretation

Iteration 83 decomposes why foreground bridge support does not become active released-surface
co-occurrence.

`both_distinct_extreme` support object `9` is a TTC-borderline-only miss on its bridge-supported
frames. It has `3` bridge-supported frames, `2` finite-TTC frames, and `1` borderline frame, but
zero active bridge-supported frames. Its closest active TTC margin is still `+2.2761 s`, while
its closest active CPA margin is `+17.6718 m`.

`ttc_medium_a` support object `10` is a no-finite-TTC surface miss. It has bridge support in
`15` frames, but every bridge-supported frame is subthreshold, none has finite TTC, and its
closest active CPA margin is still `+5.7464 m`.

The miss is therefore mixed across the two support objects: one is a TTC-only borderline miss,
the other is a bridge-supported no-closing/no-finite-TTC miss. This does not repair the rule,
prove actor causality, or authorize threshold tuning.

## Claim boundary

Two-object descriptive bridge-supported surface-miss decomposition only; no actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population,
HD-Score-invariance, commercial-value, or retuning claim.
