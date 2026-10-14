# Directed-control interface review — 14 October 2026

Primary sources: [OMPL directed control sampler contract](https://ompl.kavrakilab.org/classompl_1_1control_1_1DirectedControlSampler.html)
and [control-RRT interface](https://ompl.kavrakilab.org/classompl_1_1control_1_1RRT.html).
The retained exact OMPL 2.0.1 RRT.cpp from Iter166 is the implementation evidence;
online reference pages are not a replacement for that pinned source.

The sampler supplies a validated motion, updates the destination and reports a
control duration. With intermediate insertion disabled, released RRT stores the
returned endpoint/control/duration and later constructs PathControl from them.
This supports a specialized sequence-token adapter without changing tree search.
The token has meaning only in the recorded run; it must expand to the complete
varying physical control sequence. Generic native propagation is deliberately
unsupported and fails, preserving accounted producer propagation.

The optimizer and centered-coordinate implementation remain grounded in Iter169–171's
pinned SciPy evidence. This integration adds absolute scene time, prefix selection
and sequence transport; the earlier 12/12 result cannot qualify those additions.
No alternative planner, paper benchmark or current-industry comparison changes
this immediate interface test. This is an engineering qualification, not a claim
that RRT, TRF or this allocation is the newest or best planning method.
