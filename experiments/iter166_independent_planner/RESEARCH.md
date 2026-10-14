# Research that changes the decision — 14 October 2026

[SPARQ, arXiv 2409.17630v2, 6 October 2024](https://arxiv.org/html/2409.17630v2)
learns plan evaluation and repair from an offline monitoring/planning pipeline.
Its assumptions include map information and a reliable offline trajectory evaluator;
its conclusion leaves distribution-shift robustness to future work. This is relevant
to Sentinel's eventual online approximation, but only after we can construct and
validate recoveries at the actual intervention state. We have not reproduced its
nuPlan experiment or compared speed, false negatives or recovery outcomes.

[Reachable-set contingency barriers, arXiv 2509.07464v2, 15 April 2026](https://arxiv.org/html/2509.07464v2)
combine learned control-intent sets, reachable occupancies and contingency
optimization. Their receding-horizon argument assumes an invariant terminal set
under a fallback and conditions on the learned uncertainty sets. Our inference:
a low immediate collision count or a braking action is insufficient evidence of
continued recoverability. First test executable continuations; do not import that
paper's safety wording into our fixed-scene model. The linked
[project page](https://pathetiue.github.io/frscp.github.io/) was inspected; no code
link was visible in the retrieved page. This does not establish that code is
unavailable elsewhere, and no implementation reproduction is claimed.

[OMPL 2.0.1 RRT source](https://github.com/ompl/ompl/blob/c509861210a63ec962bbec72c52823abc16b102e/src/ompl/control/planners/rrt/src/RRT.cpp)
calls a directed control sampler and retains accepted nodes without a beam.
It can return an approximate solution. Intermediate-state insertion uses another
propagation path; our adapter disables it and rejects unexpected propagation.
The directed sampler owns complete edge validation, including predecessor-dependent
sweeps. This changes the method choice: qualify RRT before SST so a witness-radius
replacement policy cannot confound the first independent comparison.

The 2026 contingency review was used for discovery, not as empirical evidence
of any method's superiority. Exact retrieved source identities are recorded in
RESEARCH_SOURCES; release implementation excerpts and BSD license are retained in
UPSTREAM. A compatible conda-forge C++ distribution replaces the incompatible
macOS15-only PyPI wheels on this macOS14.4 host. The custom bridge is small and
its binary and shared libraries are content-bound. This is a local qualification
runtime; it does not establish a reproducible binary build across platforms.
