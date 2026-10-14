# Initial trust-region radius, inspected 2026-10-14

The exact [SciPy 1.17.1 TRF implementation](https://github.com/scipy/scipy/blob/v1.17.1/scipy/optimize/_lsq/trf.py)
is retained in Iter169 and already matches the loaded file. Its bounded solver
initializes the radius from a scaled starting-coordinate norm; only an exact-zero
radius takes the unit fallback. Iter170's approximately 5e-17 starting controls
therefore permit a tiny initial step, followed by relative cost-tolerance stopping.

For the analytic residual f(q)=q-0.5, bounded q in [-1,1], the same configured solver
starting at 5.300924469105862e-17 returns about 1.0601848938211723e-16 after two
function evaluations. With q=q0+delta and delta initially zero, the physical start
and feasible set are unchanged, and the scalar solution is 0.5. Both signs are
regression tests. This does not prove the complete maneuver will qualify.

Translation is mathematically exact before floating-point rounding. It changes
both radius initialization and numerical derivative locations as iterations
proceed. The registered experiment tests that joint coordinate intervention;
a radius-only causal attribution would require another isolation experiment.
No new method, global-optimality or competitive-superiority claim is made.
