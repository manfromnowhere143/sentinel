# Iteration 20 — VAD tracker portability: pre-registration (offline stage first)

Frozen before any new replay, analysis, patch, or GPU run for this iteration.

## Why this line, and what is not being reopened

Two committed results define the remaining question:

- **VAD transfer failed on selectivity** ([iteration 14](../vad_generalization/RESULT.md)):
  the union prevented VAD's actual failures (stationary 85% -> 0%, side 65% -> 0%) but collapsed
  progress everywhere (safe-progress 2.297 -> 0.750). The decision logs named the mechanism:
  VAD exposes no learned tracker, so geometric nearest-neighbor IDs manufacture closing speed.
- **The first tracker gate refused the GPU** ([iteration 18](../iter18_tracker/RESULT.md)):
  the library tracker repaired 12/13 unsafe routed crawl frames, but the frozen bar was every
  frame. That null stands. This iteration does **not** tune the routing margin, revive the
  UniAD routed arm, or claim deployment progress from the failed O2 evidence.

The open, narrower claim is the VAD portability claim from
[`docs/NEXT_PHASE.md`](../../docs/NEXT_PHASE.md): monitor portability should be quantifiable as
track-stream quality. This iteration tests that claim on the already committed VAD logs before
any new closed-loop time.

## Mechanism

Use the existing pure-geometry tracker (`../../sentinel/tracker.py`) as a replacement for VAD's
input-layer nearest-neighbor IDs when recomputing the union's observed-closing TTC term:

- detections are transformed to world frame exactly as in the VAD union patch;
- the tracker emits smoothed position, velocity, and stable IDs;
- the CPA and TTC thresholds stay unchanged (`CPA < 1.5 m`, `TTC < 2.5 s`,
  `closing > 3.0 m/s`, score >= 0.3, range <= 30 m);
- no VAD weights, planner outputs, monitor thresholds, or intervention semantics change.

The output of the offline stage is a replay report only: raw-ID union triggers versus tracker
union triggers on the committed VAD-union decision stream, with the same episode reset
boundaries.

## Offline gate — bars frozen now

The replay uses only committed iteration-14 VAD evidence:
`../vad_generalization/proof/sentinel_vad20_union.jsonl.gz`.

- **V1 — false-closing reduction:** frames where raw-ID finite differencing fires the TTC term
  while the tracker stream does not fire either union term fall by **>= 80%** across the three
  VAD scenes. This is the direct test of the named failure mode: ID jitter manufacturing
  closing speed.
- **V2 — safety-scene retention:** on stationary-0103 and side-0103, tracker replay retains
  **>= 90%** of raw union firing episodes. The tracker may remove false closing, but it must
  not erase the alarms that produced the committed 0% collision results on VAD's failure
  scenes.
- **V3 — frontal selectivity:** on frontal-0103, tracker replay reduces union firing frames by
  **>= 50%** and first-fire episodes by **>= 50%** versus the raw-ID union log. This is the
  scene where VAD-OFF was already strong and the union's over-braking was most visibly a
  selectivity failure.
- **V4 — no threshold fit:** the replay uses the tracker defaults already committed in
  iteration 18 (`gate=3.0`, `alpha=0.5`, `max_missed=3`). No sweep is allowed in this
  iteration; if the defaults fail, the null publishes.

**Gate rule:** V1 through V4 must all pass before any VAD closed-loop run is pre-registered.
If any bar fails, the result is a full-weight null and no GPU launches from this hypothesis.

## Closed-loop stage (held until a passing offline RESULT exists)

If, and only if, the offline gate passes, a separate committed follow-up document will freeze
the closed-loop arms, bars, and falsifiers before launch. The expected arm is VAD + union on
tracker output, seed-paired against the committed VAD OFF/union evidence or a newly
pre-registered VAD rerun if determinism cannot be proven.

Minimum bars for that later document, not executable here:

- clean/frontal ego distance within 20% of VAD-OFF;
- stationary and side remain at 0% collisions, matching the committed VAD-union safety wins;
- safe-progress improves over committed VAD-union with a confidence interval excluding zero;
- tracker ID-switch and first-fire lead-time summaries are reported either way.

## Falsifiers, named up front

- **The tracker is only a UniAD-routing repair.** If V1 fails, VAD's over-braking is not mainly
  raw-ID false closing; the portability claim is refuted for this mechanism.
- **Safety was a jitter artifact too.** If V2 fails, the raw VAD union's safety wins depended
  on the same noisy closing signal; no closed-loop selectivity repair is allowed.
- **Frontal is not separable offline.** If V3 fails, the tracker does not isolate the VAD
  clean/frontal over-braking mode well enough to spend GPU time.
- **Wrong association.** If replay traces show the tracker smoothing velocity across the wrong
  object, the null reports association error rather than tuning gates after the fact.

## Protocol

1. Commit this `HYPOTHESIS.md`.
2. Add a replay harness in this directory that recomputes raw-ID and tracker union terms from
   the committed VAD-union decision log.
3. Commit the harness before running it.
4. Run the harness once; commit its stdout under `proof/` and publish `RESULT.md`, whether pass
   or fail.
5. Run `ruff check . && pytest -q && python3 scripts/validate_docs.py` before handoff.
