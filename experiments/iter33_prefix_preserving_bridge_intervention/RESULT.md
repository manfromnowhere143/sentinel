# Iteration 33 - prefix-preserving bridge intervention calibration null

Status: `CALIBRATION_NULL_NO_USABLE_ALPHA`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed offline
prefix-manifest/direction gate, the pre-registered S0 canary, and the full S1 calibration grid.
S0 passed, but calibration did not select any nonzero global alpha. The experiment therefore stops
before heldout replay.

Claim boundary: this is **not** a heldout causal-geometry result, iteration-12 result, selector
score, closed-loop result, deployment result, or safety result. It is a calibration null: the
registered intervention produced valid logs and benign controls remained stable, but the
eligible-lowdiv target movement was far below the frozen calibration bars.

Harnesses:

- [`build_prefix_manifests.py`](build_prefix_manifests.py)
- [`server_patch_intervention.py`](server_patch_intervention.py)
- [`feeder_intervention.py`](feeder_intervention.py)
- [`canary_intervention_run.sh`](canary_intervention_run.sh)
- [`calibration_grid_run.sh`](calibration_grid_run.sh)
- [`analyze_intervention.py`](analyze_intervention.py)

Primary evidence:

- [`proof-prefix/prefix_manifest_report.json`](proof-prefix/prefix_manifest_report.json)
- [`proof-canary/canary_report.json`](proof-canary/canary_report.json)
- [`proof-calibration/calibration_report.json`](proof-calibration/calibration_report.json)
- [`proof-calibration/sentinel-e33-calibration.log`](proof-calibration/sentinel-e33-calibration.log)
- [`proof-calibration/unsplit_sha256s.txt`](proof-calibration/unsplit_sha256s.txt)
- [`proof-calibration/sha256s.txt`](proof-calibration/sha256s.txt)
- [`proof-calibration/local_verification.txt`](proof-calibration/local_verification.txt)

The large model JSONL gzip logs are committed as `*.jsonl.gz.part-*` shards under the registered
`>90 MB` proof-artifact rule. Reconstruct and re-run the analyzer with
[`proof-calibration/artifact_reconstruction.command.txt`](proof-calibration/artifact_reconstruction.command.txt).

## Verdict

| gate | result |
|---|---|
| Offline prefix manifest | **PASS**: canary/calibration/heldout manifests match the frozen prefix/target/context counts |
| Direction integrity | **PASS**: iteration-31 direction SHA remains `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794` |
| S0 canary | **PASS**: alpha `0.00` reproduced the iteration-32 model/GT target hashes exactly; alpha `0.50` repeated deterministically and changed bridge SHA on `24/24` nonzero target observations |
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

The strongest nonzero cell by registered positive movement was alpha `1.00`, but it still missed
the eligible-lowdiv bars by a wide margin:

| alpha | eligible median spread delta | eligible fraction > 0.25 m | eligible median best-gap delta | eligible rows | benign rows |
|---:|---:|---:|---:|---:|---:|
| `0.25` | `0.004535` | `0.009259` | `-0.000086` | `108` | `2344` |
| `0.50` | `0.009948` | `0.083333` | `-0.000027` | `108` | `2344` |
| `0.75` | `0.019271` | `0.111111` | `-0.000018` | `108` | `2344` |
| `1.00` | `0.030803` | `0.129630` | `-0.000055` | `108` | `2344` |

The frozen eligibility bars required median eligible endpoint-spread delta `> 0.25 m`, at least
`50%` of eligible rows with endpoint-spread delta `> 0.25 m`, and median best-candidate-gap delta
`>= 0.0 m`. No nonzero alpha satisfied those bars.

Benign-control motion stayed within the registered harm bars. For alpha `1.00`, benign median
executed endpoint displacement was `0.106039 m`, p95 displacement was `0.466095 m`, danger-cross
fraction was `0.0`, low-diversity-collapse fraction was `0.0`, and benign median endpoint-spread
delta was `0.054514 m`. That does not rescue the result because the positive eligible-lowdiv
movement criterion failed first.

## Calibration Evidence

The calibration grid completed on `sentinel-gpu`:

```text
E33_CALIBRATION_ALPHA_0p00_DONE Thu Jul  9 08:14:04 UTC 2026
E33_CALIBRATION_ALPHA_0p25_DONE Thu Jul  9 10:50:54 UTC 2026
E33_CALIBRATION_ALPHA_0p50_DONE Thu Jul  9 13:27:10 UTC 2026
E33_CALIBRATION_ALPHA_0p75_DONE Thu Jul  9 16:02:31 UTC 2026
E33_CALIBRATION_ALPHA_1p00_DONE Thu Jul  9 18:39:08 UTC 2026
E33_CALIBRATION_DONE Thu Jul  9 18:39:08 UTC 2026
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
python3 experiments/iter33_prefix_preserving_bridge_intervention/analyze_intervention.py \
  --stage calibration \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00.jsonl.gz \
  --out experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/calibration_report.json
```

The committed proof directory contains the analyzer report, command receipts, the calibration run
log, GT sidecars, split model logs, unsplit SHA256 receipts, final SHA256 receipts, and local
verification output.

## Interpretation

Iteration 33 repaired the replay-form blocker that stopped iteration 31: prefix-preserving replay
is stable, alpha-zero reproduces the baseline, and nonzero alphas change the bridge tensor without
gross corruption. The calibration null says something narrower and important: the committed
iteration-31 bridge-centroid direction is not a strong enough single global intervention to move
calibration eligible-lowdiv command-candidate geometry by the registered amount.

This does not erase iteration 30's localization result. The bridge representation can still carry
diagnostic low-diversity information. What failed here is the stronger causal repair step: adding
that centroid direction globally did not produce enough registered downstream candidate-diversity
movement while preserving the frozen gate logic.

## Next Authorized Step

Publish this calibration null and stop iteration 33. Heldout replay, iteration-12 scoring, selector
evaluation, closed-loop work, deployment language, and safety claims are not authorized from this
result. A successor would need a fresh pre-registration with a different intervention hypothesis
or a deliberately narrower claim.
