# Iteration 20, offline gate — the committed tracker is not a VAD portability fix

The VAD tracker-portability hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested only on
committed iteration-14 VAD evidence, before any new closed-loop work. Harness:
[`replay_vad_tracker.py`](replay_vad_tracker.py). Output:
[`proof/replay_output.txt`](proof/replay_output.txt).

## Verdict

| bar | result |
|---|---|
| **V1** false-closing reduction >= 80% | **0/47 = 0% — FAIL** |
| **V2** safety-scene firing-episode retention >= 90% | side **4/6 = 66.7% — FAIL**; stationary 2/2 pass |
| **V3** frontal selectivity >= 50% frame and episode reduction | frames **79 -> 90** (-13.9% reduction) and episodes **20 -> 20** — **FAIL** |
| **V4** no threshold fit | PASS: committed defaults (`gate=3.0`, `alpha=0.5`, `max_missed=3`) used with no sweep |

**Per the gate rule, no VAD closed-loop run launches from this iteration.**

## What the null establishes

The simple tracker that repaired most of the UniAD routing flicker in iteration 18 does not
repair VAD transfer selectivity under the frozen offline test. It removes **zero** raw-ID TTC
fires, fails the side-scene retention bar, and creates more frontal firing frames than the raw
nearest-neighbor stream. This refutes the mechanism as registered: the committed association
and constant-velocity smoothing layer is not a VAD portability fix.

The broader tracking-quality constraint is not erased by this null. Iteration 14 still shows
that VAD transfer depends on the track stream the monitor consumes, and iteration 17 still
shows routing safety depends on velocity continuity. What closes here is the default
lightweight tracker as the immediate zero-GPU bridge from those diagnoses to a VAD closed-loop
arm.

## Correction on the record

The first replay attempt was invalid because the pair parser matched both shell `set -x` echo
lines and the actual `##### VAD20PAIR ... #####` run markers, duplicating the scene order and
mis-joining the side episodes. That stdout is preserved in
[`proof/replay_attempt1_invalid.txt`](proof/replay_attempt1_invalid.txt). The committed fix
requires the actual marker at line start, and the valid output above is from the corrected
harness.

## Evidence

The corrected replay joined 759 frames to committed ego poses and excluded 181 frames without a
matching pose timestamp. All reported counts are over the joined frames. Reproduce:

```bash
python3 -B experiments/iter20_vad_tracker_portability/replay_vad_tracker.py \
  experiments/vad_generalization/proof/sentinel-vad20.log \
  experiments/vad_generalization/proof/sentinel_vad20_union.jsonl.gz \
  experiments/vad_generalization/proof/vad20-runs.tar.gz
```
