# Derivative scale, inspected 2026-10-14

Primary sources: [SciPy 1.17.0 least-squares reference](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html)
and the exact [SciPy 1.17.1 numerical-difference implementation](https://github.com/scipy/scipy/blob/v1.17.1/scipy/optimize/_numdiff.py).
The retained 1.17.1 file matches the loaded implementation byte for byte; versions
are intentionally explicit. No claim that this is the newest solver is needed.

For two-point differences the default step scales with machine precision and
`max(1, abs(x))`. An explicit relative step scales with `abs(x)`; fallback occurs
when adding that step leaves x unchanged. That guard does not ensure the function
value changes. For x=5.300924469105862e-17 and f(x)=1+x, the 1e-6 relative step
returns numerical derivative zero; the default returns one, agreeing with the
analytic derivative. Test both signs and an exact-zero control to expose the
boundary. This scalar diagnostic is not a maneuver qualification result.

Inference: the explicit step can suppress steering sensitivity for the retained
long-turn initialization. The frozen successor tests whether removing that
choice is sufficient for qualification. It does not establish global optimality,
robust control, generalization or the cause of earlier RRT/source failures.
