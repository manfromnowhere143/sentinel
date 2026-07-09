# Iteration 33 - prefix-preserving bridge intervention S0 canary pass

Status: `S0_CANARY_PASS_CALIBRATION_GRID_AUTHORIZED`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed offline
prefix-manifest/direction gate and the pre-registered S0 canary only. The canary fixes the
iteration-31 infrastructure blocker: alpha `0.00` prefix replay exactly reproduces the committed
iteration-29/iteration-32 target outputs while alpha `0.50` deterministically changes the bridge
vector on every target row checked.

Claim boundary: this is **not** a calibration, heldout, iteration-12, selector, closed-loop,
deployment, or safety result. It authorizes only the frozen iteration-33 calibration grid as the
next stage. Heldout replay remains unauthorized until a nonzero calibration alpha passes the
registered bars.

Harnesses:

- [`build_prefix_manifests.py`](build_prefix_manifests.py)
- [`server_patch_intervention.py`](server_patch_intervention.py)
- [`feeder_intervention.py`](feeder_intervention.py)
- [`canary_intervention_run.sh`](canary_intervention_run.sh)
- [`analyze_intervention.py`](analyze_intervention.py)

Primary evidence:

- [`proof-prefix/prefix_manifest_report.json`](proof-prefix/prefix_manifest_report.json)
- [`proof-prefix/prefix_manifest_canary.json`](proof-prefix/prefix_manifest_canary.json)
- [`proof-canary/canary_report.json`](proof-canary/canary_report.json)
- [`proof-canary/sentinel-e33-canary.log`](proof-canary/sentinel-e33-canary.log)
- [`proof-canary/sha256s.txt`](proof-canary/sha256s.txt)
- [`proof-canary/local_verification.txt`](proof-canary/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| Offline prefix manifest | **PASS**: committed canary manifest has `3` scenes, `44` prefix replay rows, `12` target rows, and `32` context-only rows |
| Direction integrity | **PASS**: iteration-31 direction SHA remains `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794` |
| S0 canary execution | **PASS**: two alpha `0.00` repeats and two alpha `0.50` repeats completed on `sentinel-gpu`; every run logged `44` non-reset rows and `12` target rows |
| Alpha-zero model hash | **PASS**: both alpha `0.00` model repeats produced target projection hash `2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e` |
| Alpha-zero GT hash | **PASS**: both alpha `0.00` GT sidecars produced target projection hash `5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7` |
| Alpha-zero reference parity | **PASS**: `96` reference comparisons checked, `0` failures, max absolute coordinate error `0.0` within tolerance `1e-5` |
| Alpha `0.50` repeat hash | **PASS**: both alpha `0.50` model repeats produced target projection hash `30e7e95cc165367697bf72f13b940358ce1c60101d3c3d2abe497f35696fa866` |
| Alpha `0.50` bridge change | **PASS**: `24/24` alpha `0.50` target observations recorded changed bridge-vector SHA256s |
| Context contamination | **PASS**: context-only rows were not intervened on and did not enter target hash/reference checks |
| Calibration, heldout, iteration-12, selector, closed loop | **NOT RUN**: prohibited until this S0 proof is committed; calibration grid is the next authorized stage |

**Iteration 33 S0 passes.** Prefix-preserving intervention replay is now stable enough to run the
pre-registered calibration grid. This does not establish a causal heldout effect or a safety
improvement; it only clears the infrastructure gate that iteration 31 failed.

## S0 Evidence

The canary completed on `sentinel-gpu` with:

```text
E33_CANARY_ALPHA_0p00_a_DONE Thu Jul  9 05:26:55 UTC 2026
E33_CANARY_ALPHA_0p00_b_DONE Thu Jul  9 05:29:28 UTC 2026
E33_CANARY_ALPHA_0p50_a_DONE Thu Jul  9 05:32:09 UTC 2026
E33_CANARY_ALPHA_0p50_b_DONE Thu Jul  9 05:34:49 UTC 2026
E33_CANARY_DONE Thu Jul  9 05:34:49 UTC 2026
```

The proof directory contains:

- [`proof-canary/sentinel_e33_canary_alpha0p00_a.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p00_a.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p00_b.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p00_b.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p50_a.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p50_a.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p50_b.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p50_b.jsonl.gz)
- [`proof-canary/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz`](proof-canary/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz)

The analyzer command was:

```bash
python3 experiments/iter33_prefix_preserving_bridge_intervention/analyze_intervention.py \
  --stage canary \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a.jsonl.gz \
  --log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b.jsonl.gz \
  --gt-log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz \
  --gt-log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz \
  --gt-log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz \
  --gt-log experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz \
  --out experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/canary_report.json
```

## Interpretation

Iteration 31 failed at S0 because sparse alpha-zero replay did not reproduce the committed
iteration-29 target outputs. Iteration 32 showed that prefix-preserving no-op replay restored that
baseline. Iteration 33 combines the same prefix-preserving replay form with the committed
iteration-31 bridge-centroid direction and verifies that the sham condition remains an exact
baseline while the nonzero intervention actually changes the bridge tensor.

That is an infrastructure pass, not a causal pass. The next legal action is the frozen calibration
grid over alphas `{0.00, 0.25, 0.50, 0.75, 1.00}`. If no nonzero alpha passes calibration, the
experiment must publish a calibration null and stop before heldout replay.

## Next Authorized Step

Run exactly one calibration prefix replay for every frozen alpha in the iteration-33 grid, using
the committed calibration manifest. Do not run heldout, iteration-12 scoring, selector evaluation,
or closed-loop work unless the registered calibration-selection gate authorizes it.
