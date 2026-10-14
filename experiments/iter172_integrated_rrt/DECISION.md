# Keep source comparison closed; qualify useful expansion per unit of work

Retain the all-four qualification failure. Local full-horizon control passes its
twelve explicit tasks, but integrated RRT completes none of the original four
cases. No accepted branch reaches the first timed checkpoint. All four runs
exhaust their transition allocation while well below the wall-clock cap.

The immediate bottleneck is useful tree expansion under the fixed work budget.
The post-outcome audit exposes two limitations: many requested endpoints cannot
be reached within the allocated horizon, and most trial trajectories encounter
background rejection. Exact endpoint fitting consumes substantial work without
reaching any sampled target. These are observations, not a causal decomposition.
An unreachable target can still be a useful direction for partial expansion.

Increasing the budget would change the qualification question. Replacing the RRT
would conflate tree search with its connector. Simply discarding unreachable
targets could remove useful partial motions. The recommended next milestone is
a matched-cost connector experiment before another integrated run: compare this
shooting connector with bounded forward-control proposals that generate reachable
endpoints, ranked toward the same requested targets under the same hard checks.

Freeze the parent/target requests from this retained run as an exposed diagnostic
population; include separate constructive turn, stop/wait and obstacle-detour
controls so rejecting every request cannot pass. Preserve absolute time and
every intermediate predicate. Charge proposal generation, derivatives and rejected
rollouts under the same per-request transition/time cap. No witness actions enter
either candidate. Report admissible expansion, target-distance improvement,
checkpoint-reaching opportunities and total work separately; avoid collapsing
them into a post-hoc score. Freeze ranking, acceptance and tie rules before running.

Falsifying result: forward proposals do not improve admissible progress at matched
cost, or fail the constructive controls. In that case, the proposed connector
replacement is unsupported; obstacle guidance, metric and target distribution
remain competing explanations. A positive exposed-request result would only
justify a new, separately frozen four-case integrated qualification. Require all
four original cases to complete with independent scalar admission before any
source comparison. Preserve this failed study unchanged.

Resources: the installed CPU runtime and retained raw evidence; no new provider,
native drive or source-scene query is needed for this milestone. The broader
dependency remains an admissible continuation at the unchanged first-fire state,
followed by native execution and a matched responsive information comparison.
Local or integrated qualification alone cannot establish source recovery.
