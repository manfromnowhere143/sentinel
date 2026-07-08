# Iteration 31 - bridge intervention S0 canary infrastructure null

Status: `INFRASTRUCTURE_NULL_S0_CANARY_ALPHA_ZERO_REPRODUCTION_FAIL`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed offline
direction artifact and the pre-registered S0 canary only. The canary repeated hashes were stable,
but the frozen alpha-zero reproduction bar failed against the committed iteration-29 originals.
Per the pre-registration, iteration 31 stops before calibration-grid replay, heldout replay,
iteration-12 scoring, selector evaluation, or closed-loop work.

Harnesses:

- [`build_direction.py`](build_direction.py)
- [`server_patch_intervention.py`](server_patch_intervention.py)
- [`feeder_intervention.py`](feeder_intervention.py)
- [`canary_intervention_run.sh`](canary_intervention_run.sh)
- [`analyze_intervention.py`](analyze_intervention.py)

Primary evidence:

- [`proof-direction/direction.json`](proof-direction/direction.json)
- [`proof-direction/replay_manifest_canary.json`](proof-direction/replay_manifest_canary.json)
- [`proof-canary/canary_report.json`](proof-canary/canary_report.json)
- [`proof-canary/sha256s.txt`](proof-canary/sha256s.txt)
- [`proof-canary/sentinel-e31-canary.log`](proof-canary/sentinel-e31-canary.log)

## Verdict

| gate | result |
|---|---|
| Direction artifact | **PASS**: fit-only bridge-centroid direction committed before GPU replay; direction SHA `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794`; canary/calibration/heldout manifests `12`/`2452`/`2403` rows |
| S0 canary execution | **PASS**: two alpha `0.00` repeats and two alpha `0.50` repeats completed; each model log had `15` canonical rows; GT feeder logs were copied as proof |
| Repeat counts | **PASS**: `repeat_count_failures=[]` |
| Repeat hashes | **PASS**: `repeat_hash_failures=[]`; alpha `0.00` canonical hash repeated as `227df05968f037634961e94a5de02d8329ea3867be46704f77b70c7a5d119203`; alpha `0.50` repeated as `f2cd126fcd966311bed5908873dfd4d551f3b3d696c18cbb7c58bea7dd68ac96` |
| Alpha-zero reproduction | **FAIL**: `alpha_zero_reference_pass=false`; `24` alpha-zero rows checked; `96` field comparisons failed; max absolute coordinate error `30.222413063049316` m against iteration-29 originals |
| Calibration grid | **NOT RUN**: S0 failed |
| Heldout replay | **NOT RUN**: S0 failed |
| Iteration-12, selector, closed loop | **NOT RUN**: prohibited by the failed S0 gate |

**Iteration 31 publishes an infrastructure null.** The intervention harness is deterministic at the
canary level, but the sham alpha-zero run does not reproduce the committed iteration-29
trajectories/candidates within the registered `1e-5` tolerance. That fires the named
`Patch nondeterminism` falsifier and stops the experiment before any calibration or heldout claim.

## S0 Evidence

The canary completed on `sentinel-gpu` with:

```text
E31_CANARY_ALPHA_0p00_a_DONE Wed Jul  8 20:29:19 UTC 2026
E31_CANARY_ALPHA_0p00_b_DONE Wed Jul  8 20:30:53 UTC 2026
E31_CANARY_ALPHA_0p50_a_DONE Wed Jul  8 20:32:32 UTC 2026
E31_CANARY_ALPHA_0p50_b_DONE Wed Jul  8 20:34:05 UTC 2026
E31_CANARY_DONE Wed Jul  8 20:34:05 UTC 2026
```

The proof directory contains:

- [`proof-canary/sentinel_e31_canary_alpha0p00_a.jsonl.gz`](proof-canary/sentinel_e31_canary_alpha0p00_a.jsonl.gz)
- [`proof-canary/sentinel_e31_canary_alpha0p00_b.jsonl.gz`](proof-canary/sentinel_e31_canary_alpha0p00_b.jsonl.gz)
- [`proof-canary/sentinel_e31_canary_alpha0p50_a.jsonl.gz`](proof-canary/sentinel_e31_canary_alpha0p50_a.jsonl.gz)
- [`proof-canary/sentinel_e31_canary_alpha0p50_b.jsonl.gz`](proof-canary/sentinel_e31_canary_alpha0p50_b.jsonl.gz)
- matching `_gt.jsonl.gz` feeder proof logs for all four runs.

The analyzer command was:

```bash
python3 experiments/iter31_full_trainval_bridge_intervention/analyze_intervention.py \
  --stage canary \
  --log experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_a.jsonl.gz \
  --log experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_b.jsonl.gz \
  --log experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_a.jsonl.gz \
  --log experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_b.jsonl.gz \
  --out experiments/iter31_full_trainval_bridge_intervention/proof-canary/canary_report.json
```

During analysis, the reference loader was hardened to stream committed iteration-29
`*.jsonl.gz.part-*` shards as a single split gzip stream; the regression test covers compressed
bytes split across shard boundaries.

## Failure Detail

The alpha-zero rows were internally stable: `intervention_applied` was `false`, and the original and
intervened outputs matched inside each sham run. They did not match the committed iteration-29
baseline for the same `(scene, sample_index, timestamp_us)` keys.

One audited key from the failed report:

```text
key: scene-0252, sample_index=1, timestamp_us=1534867433448600
alpha-zero original/intervened last trajectory point: [8.578692436218262, -0.23365989327430725]
iteration-29 original last trajectory point: [30.044660568237305, 0.20119568705558777]
max trajectory delta: 21.465968132019043 m
```

The report records the first `50` failures; the total failure count is `96`.

## Claim Boundary

This result does **not** show that the bridge-centroid intervention cannot change planner geometry.
It does **not** evaluate any calibration alpha, heldout row, iteration-12 frame, selector outcome,
or closed-loop behavior. It establishes only that the registered S0 canary did not reproduce the
iteration-29 baseline at alpha `0.00`, so the causal intervention test is not legally runnable under
this pre-registration.

Any successor must be a fresh pre-registration. It must explicitly resolve the baseline
reproduction issue before authorizing calibration replay, heldout replay, iteration-12 scoring,
selector evaluation, or closed-loop work.
