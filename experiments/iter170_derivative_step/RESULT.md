# Correcting the derivative step alone is insufficient

**Status: contradicted.** The independently admitted successor completes **10/12**
unchanged tasks using **747 transitions**, compared with Iter169's 10/12 and 731.
Both eight-frame turns still fail. Only the derivative-step policy changed; all
scientific parameters, physical initialization and constraints remained fixed.

Each longer turn uses 272 transitions, then returns successful `ftol` termination
after two function evaluations and two Jacobian evaluations. The full accounting
includes numerical-derivative probes: 134 trajectory evaluations across all tasks,
seven exact cache hits. An optimizer's function counter is not a work budget.

Inspection of the pinned TRF source identifies a second numerical dependency:
its initial trust-region radius depends on the norm of the starting coordinates.
Near-zero nonzero controls give a near-zero radius; the special unit-radius branch
applies only at exact zero. A separate analytic scalar problem reproduces a tiny
step followed by cost-tolerance termination. Expressing increments relative to
the same starting control solves that scalar problem. Maneuver qualification under
that coordinate change remains a separate experiment, not a result of this one.

Independent admission reconstructs all 747 attempted transitions and **284 states
with full masks**, spanning witnesses, selected paths and both retained comparator
sets: **274,912 scalar point-state classifications**. Unselected background labels
remain producer evidence. All twelve witnesses pass. No source comparison, RRT
solve, native driving or provider use. No superiority or road-safety claim.

An initial invocation supplied an abbreviated source hash and was rejected by the
identity gate before an output directory or scientific execution was initialized.
The corrected invocation used the full frozen hash. There was one initialized
scientific schedule; both its producer and checker exited successfully and were
reaped. The rejected invocation is preserved separately.

Source: `a875efd1beb4a3c25979397f1efc4d34f5b68a57`.
Raw committed before admission: `f4fe6a42627e7813718a765d94941a4b7de91529`.
[Independent admission](proof/admission.json) · [protocol](PROTOCOL.md) · [decision](DECISION.md).
