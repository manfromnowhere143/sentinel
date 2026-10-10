# Prospective constrained optimizer refinement

2026-10-10, after raw commit 48e8058493aa3f774d4641d90f0098478689cd95.
The original SLSQP design is **failed / CONSTRAINED_CONTROLLER_REJECTED**:
8/28 outputs passed the fixed certificate; 20/28 failed stationarity. Independent
replay passed. All four from-rest outputs passed, but accepting only those would
hide failures elsewhere. Retain optimizer_raw.json and optimizer_analysis.json.

Baseline from-rest iLQR objective increased 24 times per invocation; this is an
observed failure of monotone improvement, not proof of its unique causal mechanism.
The first SLSQP candidate has feasible controls and lower from-rest cost, yet its
maximum stationarity residual is 1.8495587566370875e-5 against the fixed 1e-6 gate.
The library objective tolerance is not a stationarity certificate.

Before measuring a revised candidate, add at most eight feasible Gauss-Newton
refinement iterations, within the SAME total 100 major-iteration cap. Use the
positive-definite least-squares Hessian 2 J'QJ + 2R, a KKT linear solve over currently
active constraints with positive fitted multipliers, and a fraction-to-boundary step
respecting every linear constraint. Backtrack with at most20 steps alpha=2^-j,
Armijo coefficient1e-4. Allow only machine-scale objective slack2e-14*max(1,abs(J))
to account for floating-point rounding near stationarity; report every accepted
step and residual. A non-descent direction or exhausted refinement stops rejected.

Preserve dynamics, constraints, objective, initial warm start, input population,
feasibility1e-9, stationarity1e-6, complementarity1e-7, replica tolerance1e-9 and100
major iterations. This is an explicit new algorithm stage, not relaxed convergence.
A refinement result must pass the same independent scalar replay and certificate.
No extra fixture/seed search or live execution is admitted by this amendment.
