# Primary sources informing the question

Reviewed 15 October 2026. These sources motivate the question; none grants Sentinel
a safety certificate, transfer result or state-of-the-art claim.

- Sahin et al., [Context-Conditioned Hamilton–Jacobi Reachability for Adaptive
  Safety Filtering](https://arxiv.org/html/2610.08115v1), v1, 6 October 2026,
  sections II–III. Context determines dynamics, constraints and disturbance
  authority. The authors explicitly treat their learned tube as uncertified and
  report containment empirically. Application here: distinguish present validity
  from continuation feasibility, and state the model and context of any exclusion.
- Feng et al., [Gradient-Free Neural Hamilton-Jacobi Reachability for Scalable
  Safety-Critical Control](https://arxiv.org/html/2609.14087v1), v1,
  12 September 2026, sections 4.1 and 6. The reported RC-car implementation includes
  computation/communication delay. Limitations include integration-step sensitivity
  and suboptimal endpoint-action probing for non-affine dynamics. Sentinel's
  discrete heading update is nonlinear in updated steering; this audit does not
  import endpoint-action completeness or a learned certificate.
- Borquez et al., [On Safety and Liveness Filtering Using Hamilton-Jacobi
  Reachability Analysis](https://arxiv.org/html/2312.15347v2), v2, abstract reviewed.
  The paper characterizes control sets for safety or liveness filtering and studies
  performance, computation and smoothness. Application here: preserve progress as
  well as collision requirements; a collision-free stopped state is insufficient.

The attempted HAL primary copy of Fraichard–Asama's inevitable-collision-state
paper returned an access challenge. No detailed theorem from that unavailable
copy is used. The rational bound here is derived explicitly in MATHEMATICS.md.
