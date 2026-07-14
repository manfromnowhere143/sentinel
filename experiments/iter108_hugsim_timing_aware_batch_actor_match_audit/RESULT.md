# Iteration 108 - HUGSIM timing-aware batch actor-match support audit: HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL

Status: `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL` (offline actor-match support audit
over the committed iteration-107 timing-aware 13-slot proof).

This iteration reused the frozen iteration-59 actor-match support rules over the iteration-107
slot proof. It launched no GPU work, changed no thresholds, changed no planner/action-control
code, changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_timing_aware_batch_actor_match.py`](analyze_timing_aware_batch_actor_match.py)
- Tests:
  [`../../tests/test_iter108_timing_aware_batch_actor_match.py`](../../tests/test_iter108_timing_aware_batch_actor_match.py)
- Analyzer command:
  [`proof-actor-match/analyze_timing_aware_batch_actor_match.command.txt`](proof-actor-match/analyze_timing_aware_batch_actor_match.command.txt)
- JSON report:
  [`proof-actor-match/timing_aware_batch_actor_match_report.json`](proof-actor-match/timing_aware_batch_actor_match_report.json)
- Markdown report:
  [`proof-actor-match/timing_aware_batch_actor_match.md`](proof-actor-match/timing_aware_batch_actor_match.md)

## Result

Infrastructure passed, but the registered support floor failed:

- slot count: `13`;
- completed rows: `13`;
- classifiable foreground rows: `2`;
- iteration-104 classifiable baseline: `1`;
- classifiable delta vs iteration 104: `+1`;
- minimum classifiable bar: `4`;
- support counts:
  - `background_collision_only`: `6`;
  - `classifiable_foreground`: `2`;
  - `no_collision_provenance`: `1`;
  - `post_collision_fire`: `4`;
- bridge counts:
  - `actor_mismatch`: `2`;
- actor matches: `0`;
- actor mismatches: `2`;
- actor ambiguous: `0`.

Per-slot support summary:

| slot | scenario | run | timing | channel | support | bridge | distance m | monitor object | foreground |
|---:|---|---:|---|---|---|---|---:|---|---|
| 1 | `scene-0138-medium-01` | 1 | `long_lead_fire` | `ttc_only` | `post_collision_fire` | `None` | `None` | `24` | `car` |
| 2 | `scene-0064-hard-00` | 2 | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `24` | `None` |
| 3 | `scene-0166-easy-00` | 2 | `long_lead_fire` | `cpa_only` | `no_collision_provenance` | `None` | `None` | `1` | `None` |
| 4 | `scene-0138-medium-01` | 2 | `long_lead_fire` | `ttc_only` | `post_collision_fire` | `None` | `None` | `32` | `car` |
| 5 | `scene-0064-easy-00` | 2 | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `84` | `None` |
| 6 | `scene-0166-medium-01` | 2 | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `2` | `None` |
| 7 | `scene-0064-hard-00` | 1 | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `24` | `None` |
| 8 | `scene-0411-extreme-00` | 1 | `long_lead_fire` | `ttc_only` | `classifiable_foreground` | `actor_mismatch` | `33.51390083849024` | `2` | `car` |
| 9 | `scene-0071-easy-00` | 2 | `long_lead_fire` | `ttc_only` | `background_collision_only` | `None` | `None` | `1` | `None` |
| 10 | `scene-0411-hard-00` | 2 | `short_lead_fire` | `ttc_only` | `classifiable_foreground` | `actor_mismatch` | `31.29909111075036` | `6` | `car` |
| 11 | `scene-0138-hard-00` | 1 | `long_lead_fire` | `cpa_only` | `post_collision_fire` | `None` | `None` | `6` | `car` |
| 12 | `scene-0071-extreme-00` | 1 | `long_lead_fire` | `cpa_only` | `post_collision_fire` | `None` | `None` | `2` | `car` |
| 13 | `scene-0064-medium-01` | 1 | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `18` | `None` |

## Interpretation

Iteration 108 answers the immediate post-execution question: the timing-aware batch improved
foreground actor-match support relative to iteration 104, but not enough to pass the registered
support floor. The classifiable count rose from `1/13` to `2/13`, while the required floor was
`4/13`.

Both classifiable foreground rows were `actor_mismatch` by the frozen bridge (`33.51390083849024`
m and `31.29909111075036` m). That is descriptive only. The support floor prevents a stronger
actor-match story, and the mismatch labels do not imply a repair, safety result, or causal claim.

The residual blocker is now explicit: the timing-aware schedule still produced six background-only
rows, four post-collision-fire rows, and one no-collision-provenance row. The next honest
successor should decompose why the timing-aware design did not translate into foreground
classifiable support for those 11 rows before spending another GPU run.

## Claim boundary

Bounded 13-slot timing-aware actor-match support audit only; no repair, threshold-value, transfer,
safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world
behavior, first-responder behavior, acquisition-value, retuning, production, commercial, or
actor-causality claim.
