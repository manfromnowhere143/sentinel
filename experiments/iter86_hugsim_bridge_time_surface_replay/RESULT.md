# Iteration 86 - HUGSIM bridge-time support-surface replay: HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED

Status: `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED` (offline bridge-time support-surface replay
over the three fixed iteration-85 support-object bridge timestamps).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-81, iteration-83, and iteration-85 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_bridge_time_surface_replay.py`](analyze_bridge_time_surface_replay.py)
- Tests: [`../../tests/test_iter86_bridge_time_surface_replay.py`](../../tests/test_iter86_bridge_time_surface_replay.py)
- Analyzer command: [`proof-bridge-time/analyze_bridge_time_surface_replay.command.txt`](proof-bridge-time/analyze_bridge_time_surface_replay.command.txt)
- JSON report: [`proof-bridge-time/bridge_time_surface_replay_report.json`](proof-bridge-time/bridge_time_surface_replay_report.json)
- Markdown report: [`proof-bridge-time/bridge_time_surface_replay.md`](proof-bridge-time/bridge_time_surface_replay.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-81 verdict: `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`;
- iteration-83 verdict: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`;
- iteration-85 verdict: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
- exactly the three fixed iteration-85 support-object best provenance bridge rows.

Summary:

- target rows: `3`;
- evaluated rows: `2`;
- row labels:
  - `support_bridge_time_surface_arrival`: `1`;
  - `support_bridge_time_surface_miss`: `1`;
  - `bridge_time_surface_replay_insufficient`: `1`;
- state transitions:
  - `subthreshold->borderline`: `1`;
  - `subthreshold->subthreshold`: `1`;
  - `subthreshold->None`: `1`.

| audit id | event | support object | event ts | bridge ts | event state | bridge state | event CPA | bridge CPA | label | problems |
|---|---|---:|---:|---:|---|---|---:|---:|---|---|
| `both_distinct_extreme` | `pre` | `9` | `5.0` | `5.5` | `subthreshold` | `borderline` | `21.6343 m` | `21.5208 m` | `support_bridge_time_surface_arrival` | `[]` |
| `ttc_medium_a` | `pre` | `10` | `2.5` | `4.0` | `subthreshold` | `subthreshold` | `17.2764 m` | `11.1354 m` | `support_bridge_time_surface_miss` | `[]` |
| `ttc_medium_a` | `active` | `10` | `5.0` | `6.0` | `subthreshold` | `None` | `13.5578 m` | `None` | `bridge_time_surface_replay_insufficient` | `bridge-row-count-0-for-ts-6.0` |

## Interpretation

Iteration 86 blocks under its own registered exact-row rule. The exact `6.0 s` bridge timestamp
from iteration 85 does not have a committed ON decision row, so the fixed three-row bridge-time
replay cannot be completed without a fresh pre-registration that permits nearest-row, interval, or
interpolation logic.

The two classifiable rows remain useful diagnostics but do not form the registered verdict. In
`both_distinct_extreme`, support object `9` moves from event-row subthreshold to bridge-time
TTC-borderline at `5.5 s`. In `ttc_medium_a` pre, support object `10` remains subthreshold at
the `4.0 s` bridge-time row despite a lower CPA than at the event row. The active `ttc_medium_a`
row is blocked at the exact bridge timestamp.

## Claim boundary

Three-row descriptive bridge-time support-surface replay only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
