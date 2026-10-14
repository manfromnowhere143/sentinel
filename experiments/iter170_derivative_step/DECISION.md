# Keep physical initialization; change the solver coordinates

The derivative policy correction is insufficient. Preserve the failed all-task
claim. Next freeze a coordinate translation: optimize increments from zero around
the original task-derived control vector, translating bounds by the same vector.
This keeps the initial physical rollout and feasible controls unchanged, while
removing the near-zero starting-coordinate radius. Keep the default derivative
policy and all other settings, budgets and constraints fixed. Do not round away
initial controls, inject witness actions, enlarge tolerances or increase the budget.

First retain an analytic scalar known-bad and test physical mapping/bounds plus
independent work accounting. Then run the unchanged twelve-task schedule once,
with source frozen and raw bytes committed before independent admission. Any miss
still contradicts qualification. Source comparison remains closed; a local pass
still requires subsequent four-case integrated RRT qualification.
