# Frozen derivative-step correction

One schedule of the twelve unchanged Iter168 cases, in their original order.
The Iter169 controller implementation is imported unchanged. The sole scientific
parameter change is `optimizer_diff_step: null`, replacing 1e-6. Retain the same
initial guess, terminal residuals, normalized controls, explicit stop/wait phases,
TRF method, Jacobian scaling, exact trust-region solve, numerical tolerances,
maximum evaluations and first hard-admissible completion rule. No witness actions
or case identity enter the controller API.

Retain 8,192 attempted transitions, 30 seconds and at most 16 actions per case;
1 GiB RSS, 128 MiB raw output, 2 GiB minimum disk and 300 seconds per producer or
checker stage. Every derivative/line-search propagation is charged. A complete
horizon is reserved before each new evaluation; exact-byte caching and all calls
remain recorded. No retry or outcome-dependent modification of this study.

Both source manifests and previous admission are bound before execution. Enforce
identical non-metadata plan fields except the derivative step. Freeze this source,
run once, commit raw bytes, then independently reconstruct every attempted motion,
constraint and work count with the Iter169 scalar checker. Replay full masks for
all twelve witnesses, new selected paths, retained Iter169 selected paths and
retained Iter168 depth-two paths. Unselected background labels remain producer
evidence. Selected runtime fingerprints must match Iter169's observed environment;
this is not a hermetic-build assertion.

Primary claim: all twelve full-horizon tasks complete under their unchanged
intermediate and terminal constraints. A single miss contradicts that claim;
invalid accounting or evidence invalidates admission. Optimizer termination flags
alone never establish completion. A 12/12 result qualifies this local controller
only on these exposed deterministic cases. RRT/source comparison stays closed
pending separate integrated qualification on the original four cases. No native
driving, provider use or source replay is part of this study.
