# Test one numerical explanation for the longer-turn failure

Evidence: Iter169 completes 10/12. Both longer turns retain their initial path,
although the optimizer reports successful step-tolerance termination. Their
nonzero initial steering parameters are about 5e-17; multiplying by the explicit
relative derivative step gives about 5e-23. A scalar analytic test distinguishes
a representable control perturbation from a detectable residual perturbation.

Alternatives: change initialization, supply analytic derivatives, increase the
budget, or replace the optimizer. Those alter more mechanisms; neither failed
turn exhausted its budget. First test SciPy's default derivative-step policy,
with the controller implementation and all other scientific parameters fixed.

Recommended milestone: qualify all twelve tasks with independently checked full
horizon steering/speed control. Falsifier: any task miss under the unchanged
contract, or invalid independent admission. Resources: the existing pinned CPU
runtime, at most 300 seconds per stage and the unchanged per-case budgets. No
additional provider resources. The following dependency is four-case integrated
RRT qualification; a local pass does not release source comparison by itself.
