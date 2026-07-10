# Iteration 37 - track-query site intervention calibration null

Status: `CALIBRATION_NULL_NO_USABLE_ALPHA`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed fit-only
track-query direction, the pre-registered S0 canary, and the full S1 calibration grid. S0 passed,
but calibration selected no nonzero global alpha. The experiment therefore stops before heldout
replay.

Claim boundary: this is **not** a heldout causal-geometry result, iteration-12 result, selector
score, NeuroNCAP result, closed-loop result, deployment result, or safety result. It is a
calibration null: the registered track-query-only intervention produced valid logs and preserved
the benign-control bars, but it did not increase calibration eligible-lowdiv command-candidate
diversity under the frozen alpha-selection rules.

Harnesses:

- [`build_track_direction.py`](build_track_direction.py)
- [`server_patch_intervention.py`](server_patch_intervention.py)
- [`feeder_intervention.py`](feeder_intervention.py)
- [`canary_intervention_run.sh`](canary_intervention_run.sh)
- [`calibration_grid_run.sh`](calibration_grid_run.sh)
- [`analyze_intervention.py`](analyze_intervention.py)

Primary evidence:

- [`proof-direction/track_query_direction.json`](proof-direction/track_query_direction.json)
- [`proof-canary/canary_report.json`](proof-canary/canary_report.json)
- [`proof-calibration/calibration_report.json`](proof-calibration/calibration_report.json)
- [`proof-calibration/sentinel-e37-calibration.log`](proof-calibration/sentinel-e37-calibration.log)
- [`proof-calibration/unsplit_sha256s.txt`](proof-calibration/unsplit_sha256s.txt)
- [`proof-calibration/sha256s.txt`](proof-calibration/sha256s.txt)
- [`proof-calibration/local_verification.txt`](proof-calibration/local_verification.txt)

The large model JSONL gzip logs are committed as `*.jsonl.gz.part-*` shards under the registered
`>90 MB` proof-artifact rule. Reconstruct and re-run the analyzer with
[`proof-calibration/artifact_reconstruction.command.txt`](proof-calibration/artifact_reconstruction.command.txt).

## Verdict

| gate | result |
|---|---|
| Direction artifact | **PASS**: fit-only `sdc_track_query` direction committed before GPU replay; feature count `256`, fit rows `5,211`, direction SHA `56c70104230f2eacd328c884197c93bd120076fbed775e21c8dc219f6392230f` |
| S0 canary | **PASS**: alpha-zero parity restored; alpha `0.50` changed `track_query` SHA on `24/24` nonzero target observations and preserved `sdc_traj_query_last` SHA on `24/24` |
| S1 calibration replay | **PASS**: alphas `0.00`, `0.25`, `0.50`, `0.75`, and `1.00` each logged `4293` non-reset rows, `2452` target rows, and `1841` context-only rows |
| Context contamination | **PASS**: all calibration cells reported zero context-contamination failures |
| Error/gross validity | **PASS**: all calibration cells reported `0` error rows and `0` gross-validity failures |
| Alpha selection | **FAIL/NULL**: no nonzero alpha was calibration-eligible |
| Heldout, iteration-12, selector, closed loop | **NOT RUN**: prohibited because calibration selected no usable alpha |

## Calibration Result

The calibration report selected no alpha:

```text
verdict=CALIBRATION_NULL_NO_USABLE_ALPHA
selected=false
selected_alpha=null
prefix_replay_integrity_pass=true
```

All five alpha cells completed the frozen target-label counts:

```text
eligible_lowdiv rows per alpha = 108
benign_control rows per alpha = 2344
```

The nonzero cells failed the eligible-lowdiv movement bars. Rather than increasing median
endpoint spread, the registered direction moved the eligible median in the wrong direction:

| alpha | eligible median spread delta | eligible fraction > 0.25 m | eligible median best-gap delta | eligible rows | benign rows |
|---:|---:|---:|---:|---:|---:|
| `0.25` | `-0.009995` | `0.000000` | `-0.000322` | `108` | `2344` |
| `0.50` | `-0.020936` | `0.000000` | `-0.000619` | `108` | `2344` |
| `0.75` | `-0.031567` | `0.009259` | `-0.000930` | `108` | `2344` |
| `1.00` | `-0.041940` | `0.074074` | `-0.001315` | `108` | `2344` |

The frozen eligibility bars required median eligible endpoint-spread delta `> 0.25 m`, at least
`50%` of eligible rows with endpoint-spread delta `> 0.25 m`, and median best-candidate-gap delta
`>= 0.0 m`. No nonzero alpha satisfied those bars.

Benign-control motion stayed within the registered harm bars. For alpha `1.00`, benign median
executed endpoint displacement was `0.061037 m`, p95 displacement was `0.203339 m`, danger-cross
fraction was `0.0`, low-diversity-collapse fraction was `0.0`, and benign median endpoint-spread
delta was `-0.102558 m`. That does not rescue the result because the positive eligible-lowdiv
movement criterion failed first.

## Calibration Evidence

The calibration grid completed on `sentinel-gpu`:

```text
E37_CALIBRATION_ALPHA_0p00_DONE Fri Jul 10 06:22:02 UTC 2026
E37_CALIBRATION_ALPHA_0p25_DONE Fri Jul 10 08:57:27 UTC 2026
E37_CALIBRATION_ALPHA_0p50_DONE Fri Jul 10 11:32:15 UTC 2026
E37_CALIBRATION_ALPHA_0p75_DONE Fri Jul 10 14:07:37 UTC 2026
E37_CALIBRATION_ALPHA_1p00_DONE Fri Jul 10 16:41:58 UTC 2026
E37_CALIBRATION_DONE Fri Jul 10 16:41:58 UTC 2026
```

Every alpha cell logged the frozen row counts:

```text
FEEDER_DONE run_alpha=0.0 rows=4293 target_rows=2452 context_only_rows=1841 scenes=121
FEEDER_DONE run_alpha=0.25 rows=4293 target_rows=2452 context_only_rows=1841 scenes=121
FEEDER_DONE run_alpha=0.5 rows=4293 target_rows=2452 context_only_rows=1841 scenes=121
FEEDER_DONE run_alpha=0.75 rows=4293 target_rows=2452 context_only_rows=1841 scenes=121
FEEDER_DONE run_alpha=1.0 rows=4293 target_rows=2452 context_only_rows=1841 scenes=121
```

The analyzer command was:

```bash
python3 experiments/iter37_track_query_site_intervention/analyze_intervention.py \
  --stage calibration \
  --log experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p00.jsonl.gz \
  --log experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p25.jsonl.gz \
  --log experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p50.jsonl.gz \
  --log experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p75.jsonl.gz \
  --log experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha1p00.jsonl.gz \
  --out experiments/iter37_track_query_site_intervention/proof-calibration/calibration_report.json
```

The committed proof directory contains the analyzer report, command receipts, the calibration run
log, GT sidecars, split model logs, unsplit SHA256 receipts, final SHA256 receipts, and local
verification output.

## Interpretation

Iteration 37 tested the site-specific successor authorized by iteration 36. The S0 result matters:
the harness can mutate `sdc_track_query` alone while preserving the wrong-site guard on
`sdc_traj_query_last`, and prefix-preserving replay remains stable. The calibration null says the
stronger causal-repair claim fails: adding the fit-only track-query centroid direction does not
increase calibration eligible-lowdiv candidate diversity by the registered amount.

This does not erase iteration 36's diagnostic site-localization result. `track_query` can still
carry strong diagnostic low-diversity information. What failed here is the registered global
track-query-only intervention direction as a causal movement mechanism.

## Next Authorized Step

Publish this calibration null and stop iteration 37. Heldout replay, iteration-12 scoring,
selector evaluation, closed-loop work, deployment language, and safety claims are not authorized
from this result. A successor would need a fresh pre-registration with a different intervention
hypothesis, target transformation, or deliberately narrower post-result audit claim.
