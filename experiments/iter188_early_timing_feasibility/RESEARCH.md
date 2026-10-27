# Primary research informing the audit

Reviewed 27 October 2026. These papers inform the verification design; none is a
matched Sentinel comparator or evidence of Sentinel superiority.

- Gould, Zhang, Tsiotras and Coogan, [Online, Reachability-Aware, Sampling-Based
  Motion Planning, arXiv:2609.09073v1](https://arxiv.org/html/2609.09073v1),
  8 September 2026. The paper uses interval reachability within a sampling controller.
  Its limitations explicitly distinguish failure to find a certifiable sequence
  from absence of a feasible sequence, and acknowledge missing recursive feasibility
  and numerical-integration assumptions. Our inference: retain a one-sided certificate
  and explicit unknowns; a successful short step is not a full continuation guarantee.
- Bartels, Fisikopoulos and Weiser, [Fast Floating-Point Filters for Robust
  Predicates, arXiv:2208.00497v1](https://arxiv.org/html/2208.00497v1), submitted
  31 July 2022; journal reference Bit Numer Math 63, 31 (2023). The work combines
  error-controlled filtering and exact arithmetic for geometric decisions.
  Our inference: an exact affine inequality still needs a numerical argument tying
  it to the source predicate. Freeze operator error bounds and reject uncertain signs.
- Kohlen et al., [A Formally Verified IEEE 754 Floating-Point Implementation of
  Interval Iteration for MDPs, arXiv:2501.10127v3](https://arxiv.org/abs/2501.10127v3),
  6 October 2025. The authors connect abstract semantics to an LLVM implementation
  with machine-checked refinement and directed rounding. Our independent replay is
  a smaller assurance layer and must not be described as that kind of formal verification.
- [Python 3.14 math documentation](https://docs.python.org/3.14/library/math.html#math.hypot)
  documents hypot's maximum error below one ulp since 3.10 and nextafter's neighboring
  representable value. These are explicit numerical assumptions, not evidence of
  physical vehicle fidelity. The observed runtime is recorded separately.

The current task is to establish necessary timing constraints for existing endpoints.
It does not add a controller, disturbances, perception, hardware actuation or a new
benchmark claim. A planner change requires a later frozen all-four comparison.
