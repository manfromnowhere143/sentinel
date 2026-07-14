# Iteration 113 - HUGSIM support-core actor-match support audit: HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE` (offline actor-match support audit over
the committed iteration-112 support-core 8-slot proof).

This iteration reused the frozen iteration-59 actor-match support rules over the iteration-112
slot proof. It launched no GPU work, changed no thresholds, changed no planner/action-control
code, changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_actor_match.py`](analyze_support_core_actor_match.py)
- Tests:
  [`../../tests/test_iter113_support_core_actor_match.py`](../../tests/test_iter113_support_core_actor_match.py)
- Analyzer command:
  [`proof-actor-match/analyze_support_core_actor_match.command.txt`](proof-actor-match/analyze_support_core_actor_match.command.txt)
- JSON report:
  [`proof-actor-match/support_core_actor_match_report.json`](proof-actor-match/support_core_actor_match_report.json)
- Markdown report:
  [`proof-actor-match/support_core_actor_match.md`](proof-actor-match/support_core_actor_match.md)

## Result

Infrastructure passed and the registered support floor passed:

- slot count: `8`;
- completed rows: `8`;
- classifiable foreground rows: `8`;
- minimum classifiable bar: `4`;
- iteration-108 classifiable baseline: `2`;
- classifiable delta vs iteration 108: `+6`;
- support counts:
  - `classifiable_foreground`: `8`;
- design counts:
  - `exact_ttc_classifiable_anchor`: `3`;
  - `ttc_classifiable_scenario_analogue`: `5`;
- design classifiable counts:
  - `exact_ttc_classifiable_anchor`: `3`;
  - `ttc_classifiable_scenario_analogue`: `5`;
- bridge counts:
  - `actor_mismatch`: `8`;
- actor matches: `0`;
- actor mismatches: `8`;
- actor ambiguous: `0`.

Per-slot support summary:

| slot | scenario | run | design | timing | support | bridge | distance m | monitor object | foreground |
|---:|---|---:|---|---|---|---|---:|---|---|
| 1 | `scene-0411-hard-00` | 2 | `exact_ttc_classifiable_anchor` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `23.793069683037515` | `12` | `car` |
| 2 | `scene-0411-extreme-00` | 1 | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `24.59033959495813` | `2` | `car` |
| 3 | `scene-0038-hard-00` | 1 | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `14.472507961609738` | `25` | `car` |
| 4 | `scene-0038-extreme-00` | 1 | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `15.460122021736504` | `2` | `car` |
| 5 | `scene-0038-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `15.541003639773562` | `2` | `car` |
| 6 | `scene-0383-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `36.09143899155716` | `1` | `car` |
| 7 | `scene-0411-hard-00` | 1 | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `23.180715225043926` | `12` | `car` |
| 8 | `scene-0411-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `24.812496764606966` | `17` | `car` |

## Interpretation

Iteration 113 answers the immediate post-execution support question: the support-core selection
preserved foreground-classifiable actor-match support on all registered rerun slots. The
classifiable count is `8/8`, above the frozen floor of `4/8` and above the iteration-108
timing-aware support count of `2/13`.

Every classifiable row is an `actor_mismatch` by the frozen iteration-59 bridge. That is a
descriptive actor-comparison label only. It does not imply a repair, a causal intervention, a
safety result, or a deployment result.

The next honest successor is an offline mismatch-geometry decomposition over these eight
classifiable rows: why the monitor's first-fire object is consistently far from the first
foreground collision actor under the frozen bridge.

## Claim boundary

Bounded 8-slot support-core actor-match support audit only; no repair, threshold-value, transfer,
safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world
behavior, first-responder behavior, acquisition-value, retuning, production, commercial, or
actor-causality claim.
