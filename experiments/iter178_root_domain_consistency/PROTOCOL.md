# Correct next-root numerical acceptance before a fresh qualification

Iter177 is invalid and must not be retried. Its first chicane_right connection
produced an admissible state at speed 6.000000000000002, within the existing motion
tolerance but outside the next constructor's strict domain. Retain the invalid
admission and all partial evidence at parent 802c6779ae50b94251870288cf76752438ed53fd.
The valid comparison remains Iter175's 2/4 result; none of Iter177's three earlier
producer outputs is an admitted case result.

Change exactly the Controls constructor's numerical speed and steering acceptance
to match the already-existing motion predicate: speed in `[-1e-12,6+1e-12]` and
absolute steering at most `pi/3+1e-12`. Preserve the original state object and all
values. No clipping, snapping or modification of stored or propagated states.
The remaining constructor/method bytes are copied exactly, and source contracts
allow only its import into the evaluator and that evaluator's adapter import.
Every physical/scene/checkpoint predicate and tolerance remains unchanged.

Retain the Iter177 pose-aware seed and its fallback generator byte-for-byte. Keep
OMPL 2.0.1/native binary, sampler, metric, goal bias, nearest neighbors, sequence
transport, prefix selection, exact-vector cache, goal and absolute clock rules.
Cases/order/seeds remain bend_left/20261014, bend_right/20261015,
chicane_left/20261016, chicane_right/20261017. Each runs once in a fresh process:
18,000 attempted transitions, 120 seconds, 96 actions, 128 transitions per connection
and eight-step maximum horizon. Every nonlinear transition, including rejected
motion, counts. Full requested rollouts must fit; remainders remain unused.
Proposal arithmetic remains inside the original wall clock. No hidden optimizer,
witness actions, source queries or extra work allowance.

Constructed controls must compose the retained five-step boundary sequence with
the next constructor, preserving the exact out-of-strict-bound value. Cover both
speed endpoints and both steering endpoints at the existing tolerance, plus the
next representable value outside each boundary. Real excess must still fail.
Check original interior controls, absolute clocks, full accounting and independent
scalar replay of a subsequent toy connection, and preserve scene rejection after
domain acceptance. Each new source/identity gate has a known-bad. These tests are
mechanical development controls, not independent scene evidence.

Primary claim: the corrected candidate completes all four original cases with
independent admission. A valid miss contradicts qualification; invalid execution
remains invalid. Require all four before any source comparison. Preserve gains
and losses versus retained Iter175, plus attempts, calls, edges, returned/max-tree
frames, checkpoints and proposal-family coverage. This compares the corrected
pose-aware candidate as a whole; it does not isolate a pure seed effect from the
numerical interface correction. The cases and earlier partial outputs are exposed;
this is development qualification, not a fresh holdout or population comparison.

Freeze source before one new schedule, commit raw before separate admission, and
preserve the invalid predecessor. No retry or retuning under this identity. Reuse
independent scalar motion/checkpoint/prefix/accounting/native-path checks and the
separately implemented seed/fallback parameter reconstruction. Full scalar masks
cover returned paths; unselected background labels and native tree/RNG remain
producer evidence. No changes to physical, goal or replay tolerances.

Keep 900 seconds each for producer and checker, 1 GiB RSS, 256 MiB raw output,
2 GiB minimum free disk, 180-second child timeout and 910-second stage supervision.
Verify selected runtime identities before/after. No new driving episode, cloud
compute or spending. After the one schedule, close this correction regardless of
outcome and judge completed cases. A numerical repair alone does not establish
source recovery, safety, real-time operation, information benefit or superiority.
