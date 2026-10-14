# Preserve time before changing the planner

14 October 2026. Fresh primary-source inspection before Iter164 acquisition.
This review informs the implementation; no external planner is benchmarked here.

[OMPL's SpaceTimeStateSpace documentation](https://ompl.kavrakilab.org/classompl_1_1base_1_1SpaceTimeStateSpace.html)
represents spatial state and time separately and exposes explicit time bounds.
Its documented distance need not satisfy the triangle inequality. The pinned
[implementation header](https://github.com/ompl/ompl/blob/5b209a03fe48c41f7a2f364382c2e425bf1c7c1c/src/ompl/base/spaces/SpaceTimeStateSpace.h)
is a concrete reference, not a claim that Sentinel implements that space or inherits
its planners' guarantees. **Inference:** absolute time belongs in our continuation
contract because the retained acceptance conditions depend on it.

[Kino-PAX+ v2](https://arxiv.org/html/2602.02846v2), also inspected in the preceding
[frontier review](../iter162_source_grouping_qualification/RESEARCH_UPDATE.md), motivates
parallel constraint evaluation and alternative exploration/selection methods. Its
reported benchmark and theoretical assumptions do not establish finite-budget
performance under Sentinel's geometry, control and deadline contract. **Decision:**
keep the qualified method fixed for the first actual-history test. A qualified
external comparator remains necessary before any competitive claim.

The local audit provides the decisive implementation fact: resetting the search
clock while retaining the 6.25-second ego state would shift the 7.75/9.00-second
checkpoints to 14.00/15.25 seconds and grant 25 extra actions under a relative
401-action horizon. Iter164 preserves absolute frame numbers and independently
checks the concatenated path. This is a contract correction for a new use case,
not a new planning-theory claim. Downloaded source identities are retained in
[RESEARCH_SOURCES.json](RESEARCH_SOURCES.json).
