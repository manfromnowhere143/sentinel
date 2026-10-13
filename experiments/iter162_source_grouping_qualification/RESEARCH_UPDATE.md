# What current planning research changes for Sentinel

13 October 2026. Primary-source inspection during the frozen source comparison,
after the quantized producer reported completion and before independent admission.
No outcome, candidate or protocol was changed. This review is a decision input;
none of these external methods was installed or benchmarked in Sentinel.

[Kino-PAX+ v2, 9 September 2026](https://arxiv.org/html/2602.02846v2)
combines parallel expansion with regional cost selection and node reactivation.
Its CUDA benchmarks use an RTX 4090 and an embedded Jetson; the serial SST baseline
uses an i9 CPU. The formal assumptions include Lipschitz dynamics and local
accessibility. **Inference for Sentinel:** a useful future comparison must count
hardware and collision work, preserve absolute-time constraints and qualify the
rejection policy. Its regional pruning is not evidence that our quantized cells
preserve every finite-budget continuation. We have not established a release
artifact for this version from this inspection.

[FLASK v4, 17 September 2026](https://arxiv.org/html/2603.16059v4)
combines flat-output boundary-value solutions with SIMD collision checking. Its
low-dimensional benchmarks model robots and obstacles with spheres; continuous
collision checking remains future work. The [authors' project page](https://kavrakilab.org/flask/)
says code will be released with OMPL; that statement is not an installed comparator.
**Inference:** its reported timings cannot be compared directly with our five-state
discrete bicycle contract and full selected-point box predicate. A flatness-based
adapter needs an explicit contract reconciliation, especially near zero speed,
steering-rate limits and timed progress requirements.

[Sampling-based Kinodynamic Planning with World Models v1, 9 October 2026](https://arxiv.org/html/2610.12910v1)
uses batched RRT/KPIECE expansion with a learned propagator. Its authors identify
the goal metric as a weak link and predictor evaluation as the dominant expansion
cost. **Inference:** the separation between exploration, propagation and goal
measurement is useful here, but replacing the retained dynamics with a learned
world model would introduce a new calibration problem before solving our current
one. This under-review paper does not establish autonomous-driving transfer.

## Engineering decision

Complete the frozen comparison and independent replay first. Preserve its explicit
native, information-value and transfer unknowns. If the exact candidate misses,
follow the registered released-adapter qualification route. A qualified, complete
source action can support a separately bounded native replay; it cannot establish
monitor responsiveness from the reset state.

The common opportunity in these papers is better use of expensive constraint
queries. A future exact spatial broad phase or batched evaluator could benefit
multiple planners, but only after full-mask equivalence, boundary/ambiguity controls,
preprocessing cost, memory and a fixed query population are measured. This is a
proposed engineering experiment, not an implemented acceleration or novelty claim.
No added learned model, GPU backend or planner complexity is justified solely by
publication date or a reported speedup on a different contract.

The pinned OMPL source inspection adds a concrete adapter requirement:
[propagateWhileValid](https://github.com/ompl/ompl/blob/5b209a03fe48c41f7a2f364382c2e425bf1c7c1c/src/ompl/control/src/SpaceInformation.cpp)
checks propagated endpoints. Sentinel's predecessor-dependent sweep and control
limits must be enforced explicitly during propagation, with intermediate timed
checks retained. [PlannerStatus](https://github.com/ompl/ompl/blob/5b209a03fe48c41f7a2f364382c2e425bf1c7c1c/src/ompl/base/PlannerStatus.h)
boolean success includes approximate solutions. Require exact goal status and
separate scalar admission; retain an approximate-result known-bad. This establishes
adapter work, not an OMPL defect or a transferred SST guarantee.
