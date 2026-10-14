# Qualify the connector before another source comparison

Iter167's released control-RRT adapter misses all four exposed feasible cases. That
result does not identify a cause. A subsequent five-speed arithmetic diagnostic
found a narrower omission: the proposal library lacks the legal immediate stop at
several fractional speeds below 0.5 m/s. Longer sequences can still reach zero;
the omission does not establish general inability to stop or explain the RRT misses.

This milestone separates control coverage from short-sequence selection. Retain
the historical modules. Add bounded state-conditioned braking in a successor and
compare one-step with two-step receding lookahead on twelve constructed tasks.
Use the same controls, distance metric, geometry, constraints and transition cap.
No witness actions enter either connector. End states and task schedules are
explicit inputs; this is exposed development qualification, not generalization.

The alternatives are to rerun the same RRT, increase its budget, change its metric,
or add longer control rollouts. None identifies this local prerequisite as directly.
We choose the smallest rollout extension and charge every computed transition,
including rejected and ultimately discarded alternatives. Prefix reuse within a
call is counted once; propagating it again in a later call is charged again.

Falsifying experiment: a qualified constructive witness completes each task, but
the two-step connector fails any one under the frozen envelope. Such a result
contradicts the all-task claim and blocks promotion. A larger pass count alone does
not qualify the connector, establish statistical superiority, or explain Iter167.

Resources: local CPU, 8,192 transitions and 30 seconds per arm/case, sixteen-action
maximum, 300 seconds each for producer and checker, 1 GiB resident memory,
64 MiB output, 2 GiB minimum free disk. No providers, native driving or source scene.
All raw outcomes are committed before independent scalar admission. No initialized
retry, seed search, post-result tolerance adjustment or budget extension.

The source-comparison dependency remains stronger: after connector qualification,
a separately frozen integration must still pass all four Iter161 cases with their
original 18,000-transition, 120-second, 96-action and checkpoint contract. This
study never sets source-comparison qualification true.
