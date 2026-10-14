# Primary-source decision review — 14 October 2026

[OMPL SimpleDirectedControlSampler source](https://ompl.kavrakilab.org/SimpleDirectedControlSampler_8cpp_source.html)
and its [interface](https://ompl.kavrakilab.org/classompl_1_1control_1_1SimpleDirectedControlSampler.html)
were checked for this decision. The exact retained OMPL 2.0.1 implementation in
Iter166 remains the versioned source evidence. It samples controls and durations,
propagates valid motion and selects the closest endpoint among proposals. This
provides a concrete comparator idea without requiring an exact boundary-value solve.

The present forward arm is a Sentinel finite multi-step control family, with an
explicit deterministic phase construction. It is not the released OMPL sampler,
which uses constant controls per sampled duration. The experiment retains full
rollout evaluation to isolate proposal generation; it does not test the upstream
early-rejection efficiency. No asymptotic completeness or optimality theorem is
transferred to this finite implementation. Its selected results need scalar replay.

The shooting method and numerical rationale are the retained SciPy-backed
Iter169–172 implementation. No newer paper or added algorithm is required to test
this bottleneck. The experiment measures exposed finite behavior and cost, not
state-of-the-art status, competitive superiority or source recovery.
