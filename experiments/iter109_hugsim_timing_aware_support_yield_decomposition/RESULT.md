# Iteration 109 - HUGSIM timing-aware support-yield decomposition: HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE

Status: `HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE` (offline decomposition of the
iteration-108 support null).

This iteration joined the committed iteration-105 design rows, iteration-106 manifest,
iteration-107 execution report, and iteration-108 actor-match support report. It launched no GPU
work, changed no thresholds, changed no planner/action-control code, changed no HUGSIM metrics,
and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_timing_aware_support_yield_decomposition.py`](analyze_timing_aware_support_yield_decomposition.py)
- Tests:
  [`../../tests/test_iter109_timing_aware_support_yield_decomposition.py`](../../tests/test_iter109_timing_aware_support_yield_decomposition.py)
- Analyzer command:
  [`proof-decomposition/analyze_timing_aware_support_yield_decomposition.command.txt`](proof-decomposition/analyze_timing_aware_support_yield_decomposition.command.txt)
- JSON report:
  [`proof-decomposition/timing_aware_support_yield_decomposition_report.json`](proof-decomposition/timing_aware_support_yield_decomposition_report.json)
- Markdown report:
  [`proof-decomposition/timing_aware_support_yield_decomposition.md`](proof-decomposition/timing_aware_support_yield_decomposition.md)

## Result

The decomposition completed with no infrastructure problems:

- slot count: `13`;
- residual counts:
  - `classifiable_success`: `2`;
  - `observed_background_only`: `6`;
  - `observed_empty_collision_provenance`: `1`;
  - `observed_post_collision_fire`: `4`;
- unclassifiable rows: `11`;
- foreground-absent or empty-provenance rows: `7`;
- observed post-collision-fire rows: `4`;
- timing-inversion rows: `4`;
- observed fire-lead range: `-6.75 s` to `+3.0 s`.

Residuals by design timing:

- `long_lead_fire`: `1` classifiable success, `6` background-only, `1` empty provenance, and
  `4` post-collision-fire rows;
- `short_lead_fire`: `1` classifiable success.

Residuals by channel:

- `cpa_only`: `0` classifiable successes, `5` background-only, `1` empty provenance, and `2`
  post-collision-fire rows;
- `ttc_only`: `2` classifiable successes, `1` background-only, and `2` post-collision-fire rows.

Per-slot decomposition:

| slot | scenario | run | design lead s | observed lead s | support | residual |
|---:|---|---:|---:|---:|---|---|
| 1 | `scene-0138-medium-01` | 1 | `27.0` | `-2.5` | `post_collision_fire` | `observed_post_collision_fire` |
| 2 | `scene-0064-hard-00` | 2 | `5.5` | `None` | `background_collision_only` | `observed_background_only` |
| 3 | `scene-0166-easy-00` | 2 | `14.5` | `None` | `no_collision_provenance` | `observed_empty_collision_provenance` |
| 4 | `scene-0138-medium-01` | 2 | `18.0` | `-6.75` | `post_collision_fire` | `observed_post_collision_fire` |
| 5 | `scene-0064-easy-00` | 2 | `9.75` | `None` | `background_collision_only` | `observed_background_only` |
| 6 | `scene-0166-medium-01` | 2 | `13.0` | `None` | `background_collision_only` | `observed_background_only` |
| 7 | `scene-0064-hard-00` | 1 | `5.25` | `None` | `background_collision_only` | `observed_background_only` |
| 8 | `scene-0411-extreme-00` | 1 | `4.5` | `3.0` | `classifiable_foreground` | `classifiable_success` |
| 9 | `scene-0071-easy-00` | 2 | `5.5` | `None` | `background_collision_only` | `observed_background_only` |
| 10 | `scene-0411-hard-00` | 2 | `0.25` | `0.25` | `classifiable_foreground` | `classifiable_success` |
| 11 | `scene-0138-hard-00` | 1 | `4.25` | `-0.75` | `post_collision_fire` | `observed_post_collision_fire` |
| 12 | `scene-0071-extreme-00` | 1 | `4.0` | `-0.25` | `post_collision_fire` | `observed_post_collision_fire` |
| 13 | `scene-0064-medium-01` | 1 | `3.0` | `None` | `background_collision_only` | `observed_background_only` |

## Interpretation

Iteration 109 shows that the iteration-105 timing-aware design did not fail for one reason. It
split into two residual blockers:

1. foreground support did not appear in the instrumented proof for `7/13` rows (`6`
   background-only plus `1` empty-provenance row);
2. foreground support existed but arrived before observed monitor fire for `4/13` rows.

The channel split is the sharpest actionable signal: all `2/13` classifiable successes were
`ttc_only`, while `0/8` `cpa_only` slots were classifiable in this batch. The only short-lead
slot was also classifiable, while long-lead rows supplied only `1/12` classifiable success.

The next honest successor is an offline support-preserving candidate design that uses these
residual labels to avoid the failed assumptions before any new GPU schedule is proposed. This
result itself does not select that schedule.

## Claim boundary

Offline timing-aware support-yield decomposition only; no actor-causality, actor-match support
upgrade, repair, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial, schedule-selection, or GPU-approval claim.
