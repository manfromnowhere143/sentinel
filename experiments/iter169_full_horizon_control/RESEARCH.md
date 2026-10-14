# Method choice and preflight evidence, 14 October 2026

The [official CasADi shooting description](https://web.casadi.org/docs/#optimal-control-with-casadi)
separates control-only shooting from formulations with intermediate state variables
and continuity constraints. We retain Sentinel's existing discrete map; the example
integrator is not imported. Control-only optimization is the smaller first test for
these short tasks. No CasADi runtime is used or performance claim inferred.

SciPy's [least-squares reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
describes bounded local residual fitting, Jacobian scaling and numerical derivative
work. In particular, max_nfev is separate from evaluations used to approximate the
Jacobian. The controller therefore counts actual transitions behind every callback.
The living documentation is not the runtime identity. Retained 1.17.1 wrapper/TRF
sources match the loaded Python files; the [inventory](UPSTREAM.json), BSD license
and [runtime fingerprint](RUNTIME.json) record that narrower provenance. The native
binary has not been independently rebuilt.

Preflight used a separate three-frame toy, with witness controls
[0.3,0.05], [0.2,-0.04], [0.4,0.02], initial speed 1.3 and coordinate tolerances 1e-4.
SLSQP with the old state-distance weights reported convergence with lateral
error 0.0002673435, outside tolerance. Normalizing the squared objective alone did
not fix its return on that toy: its final selected position error remained about
0.006251. Both pre-source-freeze failures informed the switch to bounded residual
fitting. The toy now passes, and explicit regressions preserve the distinction
between solver success and task completion. This does not establish SciPy solver
superiority; these are development checks, not the twelve-case experiment.

The proposed method expands the control selection beyond a discrete library and
changes its objective and horizon. Any success qualifies the whole method on the
registered exposed tasks. It cannot isolate which change caused an improvement,
explain prior RRT misses or demonstrate source recovery. A new experiment would be
required for those claims. No contemporary paper or software release supplies them.
