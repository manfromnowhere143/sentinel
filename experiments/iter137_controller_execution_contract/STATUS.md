# Iteration 137 status — 2026-10-09

**Completed CPU benchmark.** Numerical repeatability is `supported` for the registered corpus
and runtime: 114/114 typed cases, four exact numerical repetitions each. All 912 calls completed
and independently replayed. Deadline misses are retained as observed; real-time feasibility is
not established. See [RESULT.md](RESULT.md), [STATE.json](STATE.json), and
[execution contract](EXECUTION_BINDING.md).

## Provider and validation

Final provider readback: **TERMINATED**. The successful recovery runtime lasted
448.801 seconds, in addition to the approximately 58-minute initial
connection-failure window. One recovery request hit a capacity stockout. No replacement VM.
Postflight matched all 15 deployed source/corpus/license files, found no
active benchmark workers, containers or GPU compute processes, and recorded
110.85 GiB free. The owned shutdown timer was cancelled just before the verified
provider stop. No simulator or GPU computation occurred.

51 focused tests passed locally and from committed source; implementation/test Ruff passed.
The same-runtime source parity fixtures and complete independent replay passed. One local
pytest cache warning and forensic-script Ruff findings are disclosed in RESULT.md. No whole
repository, frozen dependency or hosted CI pass is claimed.

## Recovery and next action

This is the local `research/iter137-controller-execution` candidate. The root WIP checkout and
its unrelated changes remain preserved; canonical master remains F17. The canonical
MISSION_STATE/HANDOFF files retain their historical accepted snapshot. CONTINUITY's active
prelude points here. Iter136 remains closed as REPLAY_DIVERGED; Iter135 remains deferred,
unrun and unchanged.

Next: preregister a fresh live reference pair using an explicitly named numerical controller
mode and actual typed input/iterate/stop-reason logging. Keep deadline evaluation separate.
A passing CPU fixture does not itself pass live replay or authorize an intervention-benefit
claim. No new live comparison was run in this iteration.
