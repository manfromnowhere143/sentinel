# Iteration 32 - prefix replay baseline-recovery pass

Status: `BASELINE_RECOVERY_PASS_S1_PREFIX_REPLAY`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed offline prefix
manifest/tooling gate and the pre-registered S1 no-op prefix replay. Iteration 32 resolves the
iteration-31 S0 blocker narrowly: replaying each frozen canary scene from sample index `0` through
the last target index restores iteration-29 baseline parity for the exact 12 target rows.

Claim boundary: this is **not** a bridge intervention, calibration, heldout, iteration-12,
selector, closed-loop, deployment, or safety result. It authorizes only a fresh successor
pre-registration for a prefix-preserving bridge intervention.

Harnesses:

- [`build_prefix_manifest.py`](build_prefix_manifest.py)
- [`server_patch_noop.py`](server_patch_noop.py)
- [`feeder_prefix_replay.py`](feeder_prefix_replay.py)
- [`prefix_replay_run.sh`](prefix_replay_run.sh)
- [`analyze_prefix_replay.py`](analyze_prefix_replay.py)

Primary evidence:

- [`proof-prefix/prefix_manifest.json`](proof-prefix/prefix_manifest.json)
- [`proof-prefix/prefix_manifest_report.json`](proof-prefix/prefix_manifest_report.json)
- [`proof-prefix/baseline_recovery_report.json`](proof-prefix/baseline_recovery_report.json)
- [`proof-prefix/sentinel-e32-prefix.log`](proof-prefix/sentinel-e32-prefix.log)
- [`proof-prefix/local_verification.txt`](proof-prefix/local_verification.txt)
- [`proof-prefix/sha256s.txt`](proof-prefix/sha256s.txt)

## Verdict

| gate | result |
|---|---|
| S0 offline manifest/reference gate | **PASS**: prefix manifest has exactly `44` replay rows, `12` target rows, and `32` context-only rows; every frozen target key exists exactly once in committed iteration-29 extraction and GT artifacts |
| S1 prefix replay execution | **PASS**: two no-op prefix repeats completed on `sentinel-gpu`; each run logged `44` non-reset rows and `12` target rows across the same three scenes |
| Model target repeat hash | **PASS**: both repeats produced target canonical hash `2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e` |
| GT target repeat hash | **PASS**: both GT sidecars produced target canonical hash `5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7` |
| Iteration-29 parity | **PASS**: max model absolute delta vs iteration 29 is `0.0` within tolerance `1e-5`; max GT absolute delta vs iteration 29 is `0.0` within tolerance `1e-9` |
| Error, duplicate, missing, unexpected target rows | **PASS**: `failure_count=0`, `error_rows=0`, and all missing/duplicate/unexpected target-key lists are empty |
| Intervention, calibration, heldout, iteration-12, selector, closed loop | **NOT RUN**: prohibited by this baseline-recovery scope |

**Iteration 32 publishes a baseline-recovery pass.** Prefix-preserving no-op replay reproduces the
committed iteration-29 baseline exactly for the frozen iteration-31 canary target rows. This clears
only the baseline reproduction blocker; it does not revive iteration 31 or make any intervention
claim.

## S1 Evidence

The prefix replay completed on `sentinel-gpu` with:

```text
FEEDER_DONE rows=44 target_rows=12 scenes=3
E32_PREFIX_REPLAY_a_DONE Wed Jul  8 21:13:50 UTC 2026
FEEDER_DONE rows=44 target_rows=12 scenes=3
E32_PREFIX_REPLAY_b_DONE Wed Jul  8 21:16:30 UTC 2026
E32_PREFIX_REPLAY_DONE Wed Jul  8 21:16:30 UTC 2026
```

The proof directory contains:

- [`proof-prefix/prefix_replay_run.command.txt`](proof-prefix/prefix_replay_run.command.txt)
- [`proof-prefix/analyze_prefix_replay.command.txt`](proof-prefix/analyze_prefix_replay.command.txt)
- [`proof-prefix/sentinel_e32_prefix_a.jsonl.gz`](proof-prefix/sentinel_e32_prefix_a.jsonl.gz)
- [`proof-prefix/sentinel_e32_prefix_a_gt.jsonl.gz`](proof-prefix/sentinel_e32_prefix_a_gt.jsonl.gz)
- [`proof-prefix/sentinel_e32_prefix_b.jsonl.gz`](proof-prefix/sentinel_e32_prefix_b.jsonl.gz)
- [`proof-prefix/sentinel_e32_prefix_b_gt.jsonl.gz`](proof-prefix/sentinel_e32_prefix_b_gt.jsonl.gz)

The analyzer command was:

```bash
python3 experiments/iter32_prefix_replay_baseline_recovery/analyze_prefix_replay.py \
  --log experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a.jsonl.gz \
  --log experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b.jsonl.gz \
  --gt-log experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a_gt.jsonl.gz \
  --gt-log experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b_gt.jsonl.gz \
  --out experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/baseline_recovery_report.json
```

## Interpretation

Iteration 31 failed because sparse canary replay did not reproduce the committed iteration-29
baseline at alpha `0.00`. Iteration 32 tested the smallest plausible infrastructure correction:
restore scene prefix state before logging the same frozen target rows. The result is exact
baseline parity on both model outputs and GT sidecars.

That finding is useful because it identifies the replay form a future causal test must use. It is
also deliberately limited. No nonzero alpha was applied. No direction was patched into the model.
No calibration alpha was selected. No heldout rows were used. No iteration-12, selector, or
closed-loop behavior was evaluated.

## Next Authorized Step

A successor may be pre-registered for a prefix-preserving bridge intervention that uses this
baseline-recovery lesson. That successor must freeze its own targets, intervention form, S0 bars,
calibration rules, heldout bars, and stop conditions before any run.

Nothing in this result authorizes running calibration, heldout, iteration-12 scoring, selector
evaluation, closed loop, or safety/deployment claims directly from iteration 32.
