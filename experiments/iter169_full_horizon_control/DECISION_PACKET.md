# Qualify steering and speed across the complete maneuver

Iter168's two-step connector completes ten of twelve exposed temporal tasks. Its
longer left/right turns remain physically admissible but miss position, speed and
heading targets. The known constructive witnesses pass. Increasing the transition
cap alone would not change that deterministic connector's sequence: no run reached
its cap. These observations do not explain the independent RRT's earlier failures.

Recommended milestone: bounded control-only shooting over each task's full remaining
horizon. Keep the exact discrete dynamics, all twelve cases, target tolerances,
absolute checkpoints and hard physical/background predicates. Compare against the
retained two-step results under the same 8,192-transition and 30-second caps.
No new source comparison, native episode or RRT solve belongs to this milestone.

The candidate is SciPy 1.17.1 bounded trust-region least squares, with terminal
errors normalized by their required tolerances and actuator-violation residuals
for guidance. Hard feasibility is still checked separately. Optimize continuous
controls; this changes both control selection and prediction horizon. A positive
result qualifies this method on exposed cases, not a horizon-only causal claim.

Alternatives: exhaustive longer discrete lookahead grows exponentially; another
short-horizon cost changes guidance without representing the full maneuver;
multiple shooting introduces state variables and continuity equations before
conditioning evidence requires them. A three-frame mechanical preflight exposed
premature SLSQP convergence under two objective scalings. Those development failures
are retained in RESEARCH. No registered twelve-case outcome was inspected before
this method choice or source freeze.

Falsification: any task miss under the frozen envelope, after its constructive
witness qualifies, contradicts the all-twelve claim. A solver success flag, approximate
turn or early position match cannot pass. Keep all failures and optimizer exit
statuses visible. No restart, budget increase or tolerance change within this study.

Resources: local CPU, 1 GiB resident memory, 128 MiB output, 2 GiB minimum free disk;
300 seconds each for producer and checker with 310-second external supervisors.
One task-derived initial guess per case; no witness initialization or seed search.
Every new model transition counts, including numerical derivatives and rejected
rollouts. Exact control-vector cache hits are reported separately. Commit source
before execution and raw before independent admission.

Acceptance: twelve of twelve local tasks with every selected motion, checkpoint,
phase and full point mask independently reconstructed. A pass permits a separate
RRT integration qualification on the four original cases under their original
contract. It does not itself permit source comparison. No human ceremony pending.
