# Frozen coordinate-translation qualification

Run the same twelve Iter168 tasks once in their fixed order. Import Iter169's
control parameterization and evaluator unchanged. Relative to Iter170, change only
optimizer coordinates: q = initial + delta, delta starts at zero, and bounds are
[-1 - initial, 1 - initial]. The initial physical rollout, feasible controls,
residual, default derivative policy, TRF method, exact subproblem solve, Jacobian
scaling, numerical tolerances and first hard-admissible completion rule remain
fixed. This coordinate change also changes finite-difference probe placement in
physical coordinates; it is not a radius-only intervention.

Keep 8,192 attempted transitions/30 seconds/16 actions per case; 1 GiB RSS,
128 MiB raw output, 2 GiB minimum disk, 300 seconds per stage. Every derivative
and line-search propagation is counted, exact physical-vector caching remains
visible, and rejected/interrupted evaluations cannot qualify. No witness controls
or case identity enter the search API. All intermediate physical, foreground,
background, route and task predicates and terminal tolerances remain unchanged.

Freeze source before execution; commit raw before independent admission. Replay
all attempted motion, constraints and work accounting with Iter169's independent
checker. Replay full scalar masks for the twelve witnesses, selected new paths,
retained Iter170 paths and Iter168 two-step comparator paths. Unselected background
labels remain producer evidence. Bind the prior source/raw and all reused code.
The observed runtime fingerprints must match; no hermetic-build claim.

Primary claim: complete all twelve full-horizon tasks. Any miss contradicts it;
invalid accounting invalidates admission. No retries or changes after outcomes.
Local qualification does not establish robustness or generalization. Even a pass
leaves source comparison closed pending a separate four-case integrated RRT
qualification. No source replay, RRT solve, native driving or provider use here.
