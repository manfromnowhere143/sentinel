# Iteration 87 - HUGSIM interval bridge-time support-surface replay: HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE

Status: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE` (offline interval
bridge-time support-surface replay over the three fixed iteration-85 support-object bridge
timestamps).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-85 and iteration-86 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_interval_bridge_time_surface_replay.py`](analyze_interval_bridge_time_surface_replay.py)
- Tests: [`../../tests/test_iter87_interval_bridge_time_surface_replay.py`](../../tests/test_iter87_interval_bridge_time_surface_replay.py)
- Analyzer command: [`proof-interval/analyze_interval_bridge_time_surface_replay.command.txt`](proof-interval/analyze_interval_bridge_time_surface_replay.command.txt)
- JSON report: [`proof-interval/interval_bridge_time_surface_replay_report.json`](proof-interval/interval_bridge_time_surface_replay_report.json)
- Markdown report: [`proof-interval/interval_bridge_time_surface_replay.md`](proof-interval/interval_bridge_time_surface_replay.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-85 verdict: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
- iteration-86 verdict: `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`;
- exactly the three fixed iteration-85 support-object best provenance bridge rows;
- the iteration-86 active `ttc_medium_a` block reason:
  `bridge-row-count-0-for-ts-6.0`.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `interval_support_surface_arrival`: `1`;
  - `interval_support_surface_miss`: `2`;
- state transitions:
  - `subthreshold->borderline`: `1`;
  - `subthreshold->subthreshold`: `2`;
- replay alignments:
  - `exact_bridge_ts`: `2`;
  - `nearest_before_bridge_ts`: `1`.

| audit id | event | support object | event ts | bridge ts | replay ts | alignment | event state | replay state | event CPA | replay CPA | label |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|
| `both_distinct_extreme` | `pre` | `9` | `5.0` | `5.5` | `5.5` | `exact_bridge_ts` | `subthreshold` | `borderline` | `21.6343 m` | `21.5208 m` | `interval_support_surface_arrival` |
| `ttc_medium_a` | `pre` | `10` | `2.5` | `4.0` | `4.0` | `exact_bridge_ts` | `subthreshold` | `subthreshold` | `17.2764 m` | `11.1354 m` | `interval_support_surface_miss` |
| `ttc_medium_a` | `active` | `10` | `5.0` | `6.0` | `5.75` | `nearest_before_bridge_ts` | `subthreshold` | `subthreshold` | `13.5578 m` | `12.1434 m` | `interval_support_surface_miss` |

## Interpretation

Iteration 87 resolves the iteration-86 exact-row block under the registered at-or-before interval
rule. The result is mixed, not a uniform support-surface arrival story. The support object in
`both_distinct_extreme` reaches TTC-borderline at the exact `5.5 s` bridge timestamp, but support
object `10` remains subthreshold at both `ttc_medium_a` replay rows: the exact `4.0 s` pre bridge
row and the nearest-before `5.75 s` active bridge replay row for the `6.0 s` provenance timestamp.

This strengthens the mechanism split without turning it into a repair claim: one provenance-backed
support object arrives only at borderline, while the other provenance-backed support object remains
outside the released surface even when replayed at the registered bridge-time interval row.

## Claim boundary

Three-row descriptive interval bridge-time support-surface replay only; no actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
