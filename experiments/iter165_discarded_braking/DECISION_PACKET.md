# Discarded braking continuations

Iter164 removes all 25 producer-clear two-step maximum-braking paths at frame 27.
Its retained beam fails at frame 31. Removal alone establishes neither lost
feasibility nor the cause of that miss. The bottleneck is whether any discarded
state still admits a complete continuation under the original physical contract.

Test all 25 discarded roots and all 24 retained roots. Use unchanged exact/24
search, 60,000 attempted transitions and 1,800 seconds per root. The original
7.75/9.00-second checkpoints and absolute 401-action horizon remain binding.
Interleave ascending IDs. No root selection or tuning after outcomes. Compare
counts descriptively: unequal cohort sizes and shared ancestry preclude an
independent-trials significance claim. This is additional offline work, not an
improvement in the cost of the original planner.

A complete independently checked discarded continuation establishes a feasible
path lost by the original retention decision. It still does not prove that
keeping that root in the original mixed beam would have caused completion.
If all 25 valid bounded runs miss, the claim that this continuation method
completes from at least one discarded root is contradicted; infeasibility remains
unknown. Censored/unstarted and invalid runs stay distinct from misses.

Alternatives: merely widen the beam (already nonmonotonic in Iter161), change the
progress deadline (changes the question), or qualify another search family.
The independent planner will be a separate prospective experiment, using released
OMPL control RRT. Its adapter must pass clock, motion, sweep, budget and exact-goal
checks before source use. Current research on contingency planning motivates
preserving an executable fallback, but does not certify our source geometry.

Resources: local CPU; 1 GiB peak RSS; 1 GiB output; minimum 2 GiB free space;
10,800-second total producer and 3,600-second checker limits, with external process
supervision. If less than 1,860 seconds remain before a root starts, all remaining
roots are explicitly censored. No native driving, GPU, provider or spending.

Acceptance: frozen source and input identities; raw commit before separate scalar
admission; complete historical prefix, every selected state and full background
mask, both original checkpoints for a complete path, exact beam-selection replay,
counts and resource closure. Unselected physical labels remain producer evidence.
