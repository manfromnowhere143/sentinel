# Research context reviewed 15 October 2026

These primary sources motivate distinctions and alternatives; they are not
Sentinel outcome evidence or a cross-system superiority benchmark.

- [OMPL directed-control interface](https://ompl.kavrakilab.org/classompl_1_1control_1_1DirectedControlSampler.html)
  returns the reached valid state and duration for a desired direction.
  [SimpleDirectedControlSampler](https://ompl.kavrakilab.org/namespaceompl_1_1control.html)
  samples candidates and chooses the endpoint closest to target. Target-independent
  candidates plus target-distance selection are a documented baseline, not inherently
  an implementation error.
- [Kino-PAX+, arXiv:2602.02846v2, 9 September 2026](https://arxiv.org/html/2602.02846v2)
  combines regional cost-based selection and sparse trees with parallel propagation.
  Its asymptotic claims require stated dynamics/accessibility and cost assumptions;
  its GPU results do not establish outcomes under Sentinel's CPU/checkpoint contract.
  This suggests examining selection and computational organization as separate choices.
- [Sampling-based Kinodynamic Planning with World Models, arXiv:2610.12910v1,
  9 October 2026](https://arxiv.org/html/2610.12910v1) compares nearest-neighbor and
  projection-guided exploration, batches expensive propagation and identifies goal
  metric limitations. This motivates auditing selection; it does not demonstrate
  that adding a learned propagator solves Sentinel's current failures.

The [official OMPL page](https://ompl.kavrakilab.org/) lists 2.0.2 released on
14 August 2026. Iter175 intentionally retains 2.0.1 and its original binary to
isolate allocation. This audit invokes neither version's native planner. No claim
of using the newest release is made. Unread search results are not evidence.
