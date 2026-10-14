# Retained primary-source review — 14 October 2026

Read the exact OMPL 2.0.1 RRT implementation retained at
[upstream/RRT.cpp](../iter166_independent_planner/upstream/RRT.cpp.txt), especially
its directed-sampler call and non-intermediate insertion branch. The published
[directed sampler contract](https://ompl.kavrakilab.org/classompl_1_1control_1_1DirectedControlSampler.html)
provides interface context; the retained version controls this experiment.

The returned destination, control and duration become a tree edge when duration
meets the minimum. With intermediate insertion disabled, RRT stores that validated
endpoint instead of repropagating its token as a constant physical control. Iter172's
bridge already implements that transport and fails on unexpected native propagation.
Reusing it keeps the scientific change at the connector. This review does not
establish complete independent reconstruction of native tree or RNG behavior.

The forward family and separate proposal checker are retained unchanged from
Iter173. Its design exposure and limited paired result remain part of interpretation.
New papers, larger budgets or a different search algorithm would not answer this
controlled substitution question. No novelty, latest-version or industry benchmark
claim is made; the next decision depends on the four prospective outcomes.
