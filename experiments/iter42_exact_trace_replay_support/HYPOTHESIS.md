# Iteration 42 - exact trace replay support gate pre-registration

Frozen after iteration 41 was published as `DEGRADATION_GATE_INFRASTRUCTURE_NULL`, and before any
iteration-42 analyzer, trace patch, run script, proof report, documentation claim update, gcloud
command, Docker command, model replay, image perturbation run, iteration-38 calibration replay,
heldout replay, selector evaluation, degradation perturbation, or robustness claim.

Iteration 42 is a replay-support remedy for the iteration-41 infrastructure null. It is not a
sensor-degradation experiment. Its only purpose is to prove whether the released-union monitor can
emit a committed trace that is sufficient to reproduce its own online decisions exactly offline.

The trace-support problem is now the research object. If the trace cannot support exact replay,
stop and publish the null.

## Research question

Can a newly instrumented released-union full14/power best-arm run log the exact monitor inputs,
`ego2world` transforms, and decision state needed for offline replay to reproduce every online
brake/release decision exactly?

Acceptable positive claim if every bar passes:

> The released-union monitor has a committed full14/power exact trace substrate: offline replay
> from logged monitor inputs and logged `ego2world` transforms exactly reproduces the online
> monitor decisions. This authorizes only a future offline object-stream perturbation
> pre-registration over that committed trace.

Acceptable negative claim if any bar fails:

> The released-union monitor still lacks a committed exact replay substrate. Sensor/input
> degradation robustness remains untested, and no degradation, closed-loop robustness, selector,
> deployment, or safety claim is authorized.

Forbidden claims, even on a pass:

- no camera/image degradation claim;
- no object-stream degradation robustness claim;
- no claim that UniAD is robust under degraded sensors;
- no new benchmark, NeuroNCAP, selector, deployment, production, or real-world safety claim;
- no wall-clock latency, comfort, or production-cost claim;
- no claim that iteration 38 passed calibration or heldout;
- no claim that this rerun is an independent safety replication.

## Frozen run set

If S0 authorizes the GPU run, run the released-union best arm only on the same full14/power
scenario/run set:

| order | class | scenario |
|---:|---|---|
| 1 | `stationary` | `0099` |
| 2 | `stationary` | `0101` |
| 3 | `stationary` | `0103` |
| 4 | `stationary` | `0106` |
| 5 | `stationary` | `0108` |
| 6 | `stationary` | `0278` |
| 7 | `stationary` | `0331` |
| 8 | `stationary` | `0783` |
| 9 | `stationary` | `0796` |
| 10 | `stationary` | `0966` |
| 11 | `frontal` | `0103` |
| 12 | `frontal` | `0106` |
| 13 | `frontal` | `0110` |
| 14 | `frontal` | `0346` |
| 15 | `frontal` | `0923` |
| 16 | `side` | `0103` |
| 17 | `side` | `0108` |
| 18 | `side` | `0110` |
| 19 | `side` | `0278` |
| 20 | `side` | `0921` |

Run indices are exactly `0..19` for every pair, for `400` best-arm episodes total. Do not run the
OFF arm. Do not perturb images, object streams, trajectories, model weights, planner state, or
scenario definitions.

## Frozen trace schema

The iteration-42 server patch must derive from
`experiments/iter15_latch_release/server_patch_union_release.py` and preserve the released-union
decision rule:

- `SENTINEL_MIN_SCORE = 0.3`;
- `SENTINEL_MAXGAP = 30.0 m`;
- `SENTINEL_CPA_MARGIN = 1.5 m`;
- `SENTINEL_TTC = 2.5 s`;
- `SENTINEL_MIN_CLOSING = 3.0 m/s`;
- `SENTINEL_RELEASE_K = 4`.

For every inference frame, the trace must log one JSON row carrying:

- `trace_version = "iter42_exact_trace_v1"`;
- `run`;
- `frame_index` within the reset block;
- `ts`;
- `traj`;
- `objs`;
- `scores`;
- `object_ids` if exposed by the model output, otherwise an empty list or absent field;
- `ego2world` as the exact `4x4` matrix used by the online monitor for that frame;
- the six released-union parameter values above;
- pre-decision state: `pre_braking`, `pre_clear`;
- computed decision support: `min_cpa`, `min_ttc`, `fired`;
- post-decision state: `post_braking`, `post_clear`, `brake`, `release`.

The patch may also emit reset rows. It must not log camera images, dataset tokens, secrets,
uncommitted paths, or any perturbation output.

## S0 - static provenance and launch authorization

S0 passes only if:

- this `HYPOTHESIS.md` is committed before iteration-42 tooling or run artifacts;
- the trace patch source, run script, analyzer source, and tests are committed before any GPU
  launch;
- local `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py` pass before launch;
- the trace patch statically preserves the released-union thresholds and latch rule above;
- the run script names only the frozen best-arm scenario/run set and does not run OFF;
- the run script has no image/object/trajectory perturbation mode enabled;
- the GPU preflight reports no running Docker containers, active swap, and at least `8 GiB` free
  root disk before launch.

If S0 fails, publish `TRACE_REPLAY_STATIC_OR_PREFLIGHT_NULL` and stop. Do not launch.

## S1 - trace capture completeness

S1 passes only if the single authorized trace-capture run produces committed proof artifacts with:

- `20/20` frozen scenario pairs in the registered order;
- `400/400` reset blocks, with run indices `0..19` for each pair;
- exactly `6,474` timestamped trace frame rows;
- exactly `1,205` online brake frames;
- exactly `156` online release rows;
- exactly `230` intervention episodes;
- every frame row has finite `traj`, `objs`, `scores`, `ego2world`, `min_cpa`, and `min_ttc`
  fields, allowing `1e9` for no finite TTC exactly as the released patch does;
- every frame row has a `4x4` finite `ego2world` matrix;
- no trace row contains camera image bytes, dataset token fields, or perturbation outputs.

If S1 fails, publish `TRACE_REPLAY_CAPTURE_NULL` and stop before replay interpretation.

## S2 - exact offline replay identity

S2 passes only if the committed analyzer replays the released-union decision rule from trace rows
alone, using logged `traj`, `objs`, `scores`, optional `object_ids`, and logged `ego2world`, and
reproduces the online trace exactly:

- every frame's `fired` boolean matches;
- every frame's `brake` boolean matches;
- every frame's `release` boolean matches;
- every frame's `post_braking` and `post_clear` match;
- total brake frames are exactly `1,205`;
- total release rows are exactly `156`;
- intervention episodes are exactly `230`;
- every episode's brake-frame count matches;
- every episode's first-brake frame index matches;
- every episode's release-frame indices match.

The replay must not use logged `fired`, `brake`, `release`, `post_braking`, or `post_clear` fields
as inputs to decide future state. Those fields are comparison targets only.

If S2 fails, publish `TRACE_REPLAY_IDENTITY_NULL`.

## S3 - claim-boundary audit

S3 passes only if the RESULT and active-doc updates state all boundaries:

- this is trace-support evidence, not sensor degradation;
- no perturbation was tested;
- no benchmark score, safety, deployment, selector, or robustness claim is made;
- a pass authorizes only a future offline object-stream perturbation pre-registration over the
  committed exact trace.

If S3 fails, publish `TRACE_REPLAY_OVERCLAIM_NULL` and narrow docs before any new work.

## S4 - successor authorization

If S0-S3 pass, the only authorized successor is a fresh offline object-stream perturbation
pre-registration over the committed iteration-42 exact trace. That future pre-registration must
freeze perturbation modes, labels, safety-retention bars, selectivity/cost bars, lead-time bars,
and result boundaries before any analyzer run.

Iteration 42 itself authorizes no degradation perturbation, GPU degradation run, image
perturbation, heldout replay, iteration-12 scoring, selector evaluation, closed-loop safety claim,
deployment language, or production claim.

## Named falsifiers

- **Patch drift.** The trace patch changes the released-union thresholds, latch rule, object
  filtering, or actuator behavior.
- **Run leakage.** The run script runs OFF, heldout, selector, iteration 38, perturbations, or any
  non-registered scenario/run.
- **Trace incompleteness.** Frame rows are missing `ego2world`, state, or decision-support fields.
- **Trace count drift.** Reset, frame, brake, release, or intervention counts differ from the
  frozen full14/power best-arm counts.
- **Replay mismatch.** Offline replay cannot reproduce online fired/brake/release/state decisions
  exactly.
- **Overclaim.** RESULT language turns trace-support evidence into degradation, robustness,
  deployment, or safety evidence.
- **GPU collision.** Another Docker/model run is in flight or preflight is skipped.

## Required proof artifacts

If run, the RESULT must commit:

- exact command lines;
- trace patch source, run script, analyzer source, and tests;
- GPU preflight transcript;
- trace capture log;
- committed trace artifacts or split artifacts;
- `proof-trace/trace_replay_report.json`;
- `proof-trace/local_verification.txt`;
- S0/S1/S2/S3/S4 pass/fail tables with every failed bar listed;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running iteration-42 tooling.
2. Commit trace patch, run script, analyzer, and tests before GPU launch.
3. Run the GPU preflight once; if it fails, publish the preflight null.
4. Launch at most one trace-capture run for the frozen best-arm set.
5. Collect artifacts, run the analyzer once, and publish `RESULT.md` at full weight whether the
   result is pass or null.
6. Commit and push every state change; refresh `HANDOFF.md` after publication.
