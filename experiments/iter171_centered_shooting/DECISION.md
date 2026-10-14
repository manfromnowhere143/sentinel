# Local control passes; qualify the planner integration next

Accept the bounded local qualification: all twelve tasks complete with unchanged
constraints, timing and resource caps. Preserve Iter169 and Iter170's failed
all-task claims and the analytic regressions that explain the numerical repairs.
No broader state-of-the-art or superiority claim follows from these disclosed cases.

The next dependency is an integrated control-RRT qualification on the original
four Iter161 cases. Freeze how RRT requests target state and duration, how explicit
wait/stop requirements are supplied, and how target infeasibility is represented.
Local task targets are currently specified directly; translating sampled RRT
states into those targets is an unresolved integration problem. Do not hand the
planner constructive witness actions or task-specific successful paths.

Preserve the original intermediate constraints, full terminal clock, 4/8-second
checkpoints and per-propagation resource accounting. Charge every local derivative,
line-search and rejected rollout against the planner's original budget; cap internal
horizons without dropping any resulting physical path checks. Define the directed
sampler's partial/failed return semantics before execution. Test known-bad timing,
background, approximate-goal and budget cases, then freeze the integrated source.

Acceptance: all four original cases pass with committed raw evidence and independent
scalar replay. Any miss leaves the integrated planner unqualified. Only after that
milestone is a matched comparison at the unchanged source first-fire state warranted.
The actual-history prefix and source constraints stay fixed. Monitor-time recovery
and an information advantage remain the broader unanswered scientific questions.

No human ceremony or additional provider access is needed for the next local
engineering step. The closed studies must not be enlarged retrospectively.
