# Make the first proposal respond to the requested pose

The 128-transition allocation gains a completion but remains unqualified at 2/4.
Iter176 finds nominal coverage differences without diagnosing a directional or
cache defect. Its four scalar-admitted discarded paths are incomplete at 62–64%
route progress. Neither exact reflection closure nor longer simulated time is an
adequate replacement for completion. Keep those adverse results visible.

The existing first program only fits target speed and steering. Pose affects
selection among candidates, while the short cap rarely explores beyond early
fixed patterns. The next finite hypothesis is that an inexpensive pose-aware
initial guess can supply a useful extension under the same budget. Only that
program changes; all fallback programs and planner/constraint interfaces remain.

Derive the guess from the discrete update, including its use of heading before
the yaw update. Use the existing metric weights rather than tune new ones on
the four original outcomes. Independent polynomial arithmetic and constructed
positive/adverse controls qualify implementation before integration. The adverse
control is material: turning invalidates the longitudinal approximation, so an
exact target reached by the old seed can be lost. Preserving two prior successes
is an outcome to measure, not an assumption.

This is a small engineering mechanism, not a new optimal-control method. Current
planning literature and classical linearized steering identify multiple coupled
choices: metric, local proposal, expansion selection and propagation cost. This
test changes one of them. Its result cannot establish a frontier-system advantage.
All four cases must pass before source comparison. Actual-history action windows,
measured delay and controlled information benefit remain the mission endpoints.
