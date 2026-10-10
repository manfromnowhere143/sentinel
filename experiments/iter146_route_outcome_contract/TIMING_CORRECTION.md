# Timing scope correction — Iter146

2026-10-10. Status: corrected interpretation of the frozen source measurement.
Deployed source: 9f78e514000f94ab069e846a7b6796009702a223.

The `full_loop_ns` endpoint in runner.py precedes the post-step resource guard,
deadline check and stop dispatch. The raw timing_scope string also omits those
exclusions. Report this field as a **loop-work lower bound**, not an exact complete
loop latency. It includes the initial guard, observation hashing, exchange,
controller and simulator execution, route/outcome calculation and trace flushing.
It excludes the final guard, deadline/stop dispatch and timing-list bookkeeping.
Raw traces, source and earlier pair-analysis field names remain unchanged.

`elapsed_ns` encloses reset, the loops, guards and trace finalization; it excludes
summary serialization and worker cleanup. Its ratio to completed steps bounds the
average loop duration from above, with reset/finalization included. It does not
supply an individual loop latency or replace missing per-loop boundary timestamps.

Any lower bound exceeding 250 ms proves that iteration also missed 250 ms. A
lower bound below 250 ms would not prove that the complete iteration met it.
Controller timing is a separate measured scope; short controller calls do not
establish end-to-end real-time operation. No new runtime behavior is introduced
into the fixed eight-case GPU qualification. A prospective timer boundary fix
needs a delayed-guard known-bad before another source regime claims full-loop timing.
