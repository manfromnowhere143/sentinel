# Iteration 115 - HUGSIM support-core monitor-set ordering audit: HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE` (offline first-fire monitor-set
ordering audit over the eight committed support-core mismatch rows).

This iteration used only the committed iteration-112 proof plus the committed iteration-113 and
iteration-114 reports. It launched no GPU work, reran no actor-match classifier, changed no
thresholds, changed no planner/action-control code, changed no HUGSIM metrics, and did not retune
Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_monitor_set_ordering.py`](analyze_support_core_monitor_set_ordering.py)
- Tests:
  [`../../tests/test_iter115_support_core_monitor_set_ordering.py`](../../tests/test_iter115_support_core_monitor_set_ordering.py)
- Analyzer command:
  [`proof-ordering/analyze_support_core_monitor_set_ordering.command.txt`](proof-ordering/analyze_support_core_monitor_set_ordering.command.txt)
- JSON report:
  [`proof-ordering/support_core_monitor_set_ordering_report.json`](proof-ordering/support_core_monitor_set_ordering_report.json)
- Markdown report:
  [`proof-ordering/support_core_monitor_set_ordering.md`](proof-ordering/support_core_monitor_set_ordering.md)

## Result

Infrastructure passed and all `8` rows received frozen temporal, object-set, selection, and
combined labels:

- row count: `8`;
- problem row count: `0`;
- temporal-label counts:
  - `short_lead`: `4`;
  - `medium_lead`: `2`;
  - `long_lead`: `2`;
- object-set label counts:
  - `nearest_actor_mismatch`: `8`;
- selection-label counts:
  - `selected_is_nearest`: `5`;
  - `selected_not_nearest`: `3`;
- combined-label counts:
  - `whole_set_mismatch_selected_nearest`: `5`;
  - `whole_set_mismatch_selected_not_nearest`: `3`;
- lead-time range: `0.25` to `3.25` s;
- nearest first-fire monitor-object distance to the collision actor: `7.624207359121617` to
  `24.812496764606966` m;
- selected-object distance to the collision actor: `14.472507961609738` to
  `36.09143899155716` m;
- first-fire object-count range: `1` to `10`.

Per-row ordering summary:

| slot | scenario | run | lead | object-set | selection | combined | nearest id | nearest m | selected rank | objects |
|---:|---|---:|---|---|---|---|---|---:|---:|---:|
| 1 | `scene-0411-hard-00` | 2 | `short_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `10` | `12.724592460878268` | `2` | `3` |
| 2 | `scene-0411-extreme-00` | 1 | `long_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `4` | `7.624207359121617` | `3` | `3` |
| 3 | `scene-0038-hard-00` | 1 | `long_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `25` | `14.472507961609738` | `1` | `5` |
| 4 | `scene-0038-extreme-00` | 1 | `medium_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `2` | `15.460122021736504` | `1` | `5` |
| 5 | `scene-0038-extreme-00` | 2 | `medium_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `2` | `15.541003639773562` | `1` | `4` |
| 6 | `scene-0383-extreme-00` | 2 | `short_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `18` | `23.221048739940226` | `8` | `10` |
| 7 | `scene-0411-hard-00` | 1 | `short_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `12` | `23.180715225043926` | `1` | `1` |
| 8 | `scene-0411-extreme-00` | 2 | `short_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `17` | `24.812496764606966` | `1` | `1` |

## Interpretation

Iteration 115 answers the first-fire object-set question exposed by iterations 113 and 114. In all
eight rows, the nearest logged monitor object at first fire remains outside the frozen `6.0 m`
actor-support band after propagation to the first foreground collision timestamp. That makes the
eight mismatches a whole-first-fire-object-set mismatch under the frozen bridge, not merely a case
where a close collision-actor candidate was present but the first-fire selector chose the wrong
object.

The selected object is nearest in `5/8` rows and not nearest in `3/8` rows, but even the nearest
available object is still an actor mismatch in every row. Lead times span short, medium, and long
buckets, so the absence of a close first-fire object-set candidate is not confined to one lead
bucket in this eight-row proof.

This is descriptive only. It does not prove sensor failure, actor causality, monitor causality,
planner causality, repair feasibility, or safety impact. The next honest successor is an offline
timeline audit of whether a close collision-actor candidate appears before or after first fire in
the committed decision logs, using the same frozen bridge and no new GPU run.

## Claim boundary

Descriptive monitor-set ordering audit of eight committed support-core mismatch rows only; no
repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
