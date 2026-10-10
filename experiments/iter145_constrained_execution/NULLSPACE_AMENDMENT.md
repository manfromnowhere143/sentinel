# Prospective refinement linear algebra correction

The new12-control from-rest curved fixture is **failed**: SLSQP reports success,
but independent stationarity is2.8796812003850647e-6 against the unchanged1e-6
gate. Raw controls, callback/returned handoff and two accepted refinement steps are
retained in proof/short_horizon_failure.json. The simulator correctly refuses action.
This does not retract the28-input,19-control qualification or extend its scope.

The retained boundary diagnostic reconstructs the next original KKT least-squares
direction. Roundoff leaves outward motion on an active box whose slack is exactly
zero, making fraction-to-boundary zero. This is an observed linear algebra failure
at a saturated actuator, not a reason to relax feasibility or stationarity.

Before replacement measurements, solve the SAME equality-constrained positive
definite Gauss-Newton subproblem in the active constraint null space. SVD rank
uses eps*max(A.shape)*largest_singular_value; Z is the orthonormal null-space basis.
Compute d=-Z solve(Z' H Z,Z' g). With no active constraints use Z=I. With no free
dimensions stop rejected unless the existing certificate already passes.
Keep NNLS multiplier selection, all linear constraints, fraction-to-boundary,
20 backtracks, at most8 refinements, total100 iterations, objective and every
numeric acceptance threshold unchanged. Retain algorithm name in the record.

Requalify all original28 inputs and all four short-horizon fixtures. Do not select
only successful cases. The GPU, asset and deadline gates remain unobserved.
