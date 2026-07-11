# Iteration 42 - exact trace replay support pass

Status: `TRACE_REPLAY_SUPPORT_PASS`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed trace patch, the
committed run script, and one run of the committed analyzer over the collected trace artifacts.
The GPU work was exactly the single authorized best-arm trace-capture run over the frozen
full14/power scenario/run set. No OFF arm, image perturbation, object-stream perturbation,
iteration-38 calibration, heldout replay, selector evaluation, or new benchmark scoring ran.

Claim boundary: this is **trace-support evidence only**. The released-union monitor now has a
committed full14/power exact trace substrate: offline replay from logged monitor inputs and
logged `ego2world` transforms exactly reproduces the online monitor decisions. No perturbation
was tested. This is not sensor degradation, not degradation robustness, not a benchmark or
NeuroNCAP score, and not a selector, deployment, latency, comfort, production-cost, or safety
claim. A pass authorizes only a future offline object-stream perturbation pre-registration over
the committed exact trace.

Harness:

- [`server_patch_union_trace.py`](server_patch_union_trace.py)
- [`iter42_trace_run.sh`](iter42_trace_run.sh)
- [`analyze_trace_replay.py`](analyze_trace_replay.py)
- [`../../tests/test_iter42_trace_replay.py`](../../tests/test_iter42_trace_replay.py)

Primary evidence:

- [`proof-trace/gpu_preflight.txt`](proof-trace/gpu_preflight.txt)
- [`proof-trace/sentinel_iter42_trace.jsonl.gz`](proof-trace/sentinel_iter42_trace.jsonl.gz)
  (SHA256 `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d`, verified identical
  on the box and after copy)
- [`proof-trace/sentinel-iter42-trace.log`](proof-trace/sentinel-iter42-trace.log)
- [`proof-trace/sentinel-iter42-watch.log`](proof-trace/sentinel-iter42-watch.log)
- [`proof-trace/trace_replay_report.json`](proof-trace/trace_replay_report.json)
- [`proof-trace/analyze_trace_replay.command.txt`](proof-trace/analyze_trace_replay.command.txt)
- [`proof-trace/local_verification.txt`](proof-trace/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 static provenance and launch authorization | **PASS**: HYPOTHESIS, trace patch, run script, analyzer, and tests were committed before launch; the patch statically preserves the six released-union thresholds and the latch/release rule; the run script names only the frozen best-arm scenario/run set with no OFF arm and no perturbation mode; the committed preflight showed no running Docker containers, active `8 GiB` swap, and `27 GiB` free root disk (`29,246,566,400` bytes after the recorded `outoutput` cleanup), above the frozen `8 GiB` bar |
| S1 trace capture completeness | **PASS**: `20/20` frozen scenario pairs in the registered order; `400/400` reset blocks with run indices `0..19` per pair; exactly `6,474` timestamped frame rows; exactly `1,205` online brake frames; exactly `156` online release rows; exactly `230` intervention episodes; `0` field failures — every frame row carried finite `traj`/`objs`/`scores`/`min_cpa`/`min_ttc`, a finite `4x4` `ego2world`, and the six frozen parameters; no camera bytes, dataset tokens, or perturbation outputs; `0` trace-error rows |
| S2 exact offline replay identity | **PASS**: the analyzer replayed the released-union rule from logged `traj`/`objs`/`scores`/`object_ids`/`ego2world` alone and matched every frame's `fired`, `brake`, `release`, `post_braking`, and `post_clear` — `0` mismatched frames out of `6,474`; replay totals were exactly `1,205` brake frames, `156` release rows, and `230` intervention episodes; every episode's brake-frame count, first-brake index, and release-frame indices matched |
| S3 claim-boundary audit | **PASS**: this document and the active-doc updates state that this is trace-support evidence, that no perturbation was tested, and that no benchmark, safety, deployment, selector, or robustness claim is made |
| S4 successor authorization | **PASS-scoped**: the only authorized successor is a fresh offline object-stream perturbation pre-registration over the committed iteration-42 exact trace |

The authoritative analyzer report verdict is:

```text
verdict=TRACE_REPLAY_SUPPORT_PASS
s0_pass=true
s1_pass=true
s2_pass=true
s3_pass=true
```

## Trace substrate

The single capture run (`I42_TRACE_ARM_START` 2026-07-11 05:28:55 UTC to `I42_TRACE_ALL_DONE`
2026-07-11 18:27:55 UTC) produced one committed compressed trace:

| quantity | value |
|---|---:|
| total JSON rows | `6,874` |
| reset rows | `400` |
| timestamped frame rows | `6,474` |
| trace-error rows | `0` |
| online brake frames | `1,205` |
| online release rows | `156` |
| intervention episodes | `230` |
| replay-mismatched frames | `0` |

Every count equals the frozen full14/power best-arm envelope registered in the hypothesis, which
is itself the same envelope the iteration-40 audit measured and the iteration-41 null could not
replay. The quantity iteration 41 lacked — the exact `4x4` `ego2world` matrix used online per
monitor frame — is now logged on all `6,474` frame rows.

## Interpretation

Iteration 41 established that the previously committed evidence could not support exact
world-frame replay: `1,388/6,474` monitor frames had no exact committed pose. Iteration 42 is the
narrow repair, and it worked without weakening the rule: instead of interpolating or snapping
poses after the fact, the online monitor now logs the exact transform it used, and the offline
replay reproduces every online decision bit-for-bit — `fired`, `brake`, `release`, and latch
state on all `6,474` frames across all `400` episodes.

What this buys is a substrate, not a result: future object-stream perturbations can now be
evaluated offline against a replay that is proven identical to the online monitor at
perturbation strength zero. What it does not buy: any statement about how the monitor behaves
under degraded inputs. That question remains untested.

## Next Authorized Step

Stop iteration 42. The only authorized successor on this line is a fresh offline object-stream
perturbation pre-registration over the committed iteration-42 exact trace. That pre-registration
must freeze perturbation modes, labels, safety-retention bars, selectivity/cost bars, lead-time
bars, and result boundaries before any analyzer run.

Iteration 42 authorizes no degradation perturbation run, GPU degradation run, image perturbation,
heldout replay, iteration-12 scoring, selector evaluation, closed-loop safety claim, deployment
language, or production claim.
