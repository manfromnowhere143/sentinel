# Isolate the derivative step before expanding the controller

Keep this failed qualification visible. Freeze one successor using the identical
controller and case population, changing only `optimizer_diff_step` from 1e-6 to
SciPy's default (`None`). The default uses a machine-precision-based step scaled
by `max(1, abs(x))`; the explicit relative step scales by `abs(x)`. This matters
for nonzero control values near zero. Preserve the initialization, all budgets,
tolerances, constraints and stopping rules.

A scalar analytic known-bad must first reproduce the vanished derivative and
show that the default step recovers it. The scientific test remains all twelve
unchanged tasks, frozen before execution. Either longer turn failing falsifies
the new all-task qualification claim. Do not interpret an optimizer success flag
as task success, enlarge the schedule or silently replace this raw run.

Source comparison remains closed. Even twelve local completions would qualify
only this local controller on these exposed constructed tasks. RRT integration
must subsequently pass the four existing Iter161 cases under the original
completion, checkpoint and resource contract before a source comparison.
