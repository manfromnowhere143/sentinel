# Iter191 — mathematical and interface rationale

28 October 2026. The question is whether a feedback proposal fits the existing
connector contract and recovers missed finite-budget opportunities. This is
qualification on exposed inputs; it cannot establish unseen-case performance.

For the frozen discrete speed update, `v_next = v + dt * a`, choosing
`a = clip(-v/dt, -a_max, a_max)` gives `max(0, v - dt*a_max)` for legal
nonnegative speed in exact arithmetic. Unlike a fixed acceleration grid, this
includes the state-dependent final braking increment. Constructed tests check
the floating-point boundary, tolerated near-zero roots, zero-speed pose holding,
and subsequent release. They do not establish continuous-time physical safety.

The intervention is a single ordered feedback program within the existing
128-attempt connector. Every action uses the preceding evaluated state. Every
transition, rejected alternative and background query remains charged and
replayed. The target may shorten the horizon. Stopping through the final scheduled
checkpoint does not itself imply feasibility: geometry, collision, dynamic limits,
checkpoint eligibility and full completion remain separately checked. Displacing
old proposals can lose opportunities; all paired gains and losses are reported.

The native callback must transport the returned duration and evaluated state
correctly. OMPL's official [DirectedControlSampler contract](https://ompl.kavrakilab.org/classompl_1_1control_1_1DirectedControlSampler.html)
describes this interface; Sentinel's exact retained native binary and separately
replayed registration events determine the implementation being tested. The
constructed native runs specifically test that the inherited callback dispatch
actually reaches the new evaluator. A Python-only success would be insufficient.

Gould et al., [Online Reachability-Aware Sampling-Based Motion Planning,
arXiv:2609.09073v1, 8 September 2026](https://arxiv.org/html/2609.09073v1), section
III-D, distinguishes finite sampling outcomes from existence guarantees and
finite-horizon checks from recursive feasibility. Here a successful suffix is a
conditional witness from an exposed retained state. A failed bounded search is
not an infeasibility certificate. Neither this paper nor this qualification
provides Sentinel a safety, recursive-feasibility or competitor-superiority claim.

The next integrated experiment, if qualification is supported, must freeze the
all-four population and unchanged budgets before execution. This qualification
does not change sampling, metric, expansion allocation or integrated credit.
