# Iteration 85 - HUGSIM path-horizon/provenance-timing decomposition: HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE

Status: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE` (offline path-horizon/provenance-timing
decomposition over the three fixed iteration-84 event rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-80, iteration-83, and iteration-84 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_path_horizon_bridge_timing.py`](analyze_path_horizon_bridge_timing.py)
- Tests: [`../../tests/test_iter85_path_horizon_bridge_timing.py`](../../tests/test_iter85_path_horizon_bridge_timing.py)
- Analyzer command: [`proof-timing/analyze_path_horizon_bridge_timing.command.txt`](proof-timing/analyze_path_horizon_bridge_timing.command.txt)
- JSON report: [`proof-timing/path_horizon_bridge_timing_report.json`](proof-timing/path_horizon_bridge_timing_report.json)
- Markdown report: [`proof-timing/path_horizon_bridge_timing.md`](proof-timing/path_horizon_bridge_timing.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-80 verdict: `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`;
- iteration-83 verdict: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`;
- iteration-84 verdict: `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`;
- exactly the three fixed selected/support event rows.

Summary:

- target events: `3`;
- evaluated events: `3`;
- row labels:
  - `path_horizon_support_bridge_timing_split`: `3`;
- selected bridge-supported events: `0`;
- support bridge-supported events: `3`;
- support bridge timing:
  - `provenance_after_event`: `3`;
- timing comparisons:
  - `selected_lower_cpa`: `3`;
  - `selected_better_cpa_rank`: `3`;
  - `selected_earlier_cpa_horizon`: `1`;
  - `selected_no_support_support_supported`: `3`;
  - `support_better_bridge`: `3`.

| audit id | event | selected object | selected state | selected CPA | selected horizon | selected bridge | support object | support state | support CPA | support horizon | support bridge | support provenance offset |
|---|---|---:|---|---:|---:|---|---:|---|---:|---:|---|---:|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `2.0355 m` | `4` / `2.0 s` | `no_support` | `9` | `subthreshold` | `21.6343 m` | `6` / `3.0 s` | `ambiguous` | `+0.5 s` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `9.2404 m` | `6` / `3.0 s` | `no_support` | `10` | `subthreshold` | `17.2764 m` | `6` / `3.0 s` | `match` | `+1.5 s` |
| `ttc_medium_a` | `active` | `24` | `active` | `1.2791 m` | `6` / `3.0 s` | `no_support` | `10` | `subthreshold` | `13.5578 m` | `6` / `3.0 s` | `match` | `+1.0 s` |

## Interpretation

Iteration 85 sharpens the iteration-84 arbitration split with timing evidence. At the same three
fixed event rows, the selected object again has lower CPA and better CPA rank in all rows, and it
has no provenance bridge support in all rows. The support object again has better bridge support
in all rows, and its best provenance bridge is after the event timestamp in all rows.

The closest-path horizons do not reduce to a single "earlier horizon" rule: selected is earlier in
`1/3` rows and tied with support in `2/3`. The stronger registered decomposition is therefore not
"selected is always earlier"; it is that released surface selection follows logged path geometry,
while logged collision provenance aligns with a different, surface-ineligible support object on a
later provenance timing channel.

## Claim boundary

Three-row descriptive path-horizon/provenance-timing decomposition only; no actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
