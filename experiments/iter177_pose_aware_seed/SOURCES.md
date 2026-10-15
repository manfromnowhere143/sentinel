# Steering context reviewed 15 October 2026

The recent primary-source review in
[Iter176](../iter176_connector_guidance_audit/SOURCES.md) covers Kino-PAX+,
world-model kinodynamic planning and the released OMPL interface. This mechanism
also checks the older foundations below. None is Sentinel outcome evidence.

- [Webb and van den Berg, arXiv:1205.5088v1, 23 May 2012](https://arxiv.org/html/1205.5088v1):
  exact optimal connections concern controllable linear dynamics. Sections VI and
  VII-C/D limit the nonlinear approximation to a local region; the car example
  requires nonzero speed for controllability and reports linearization artifacts.
  Sentinel's proposed seed neither implements that connector nor inherits its
  guarantees. Full nonlinear rollout and hard admission remain necessary.
- [Tedrake, Trajectory Optimization, Underactuated Robotics](https://underactuated.mit.edu/trajopt.html),
  retrieved page carrying 2024 copyright: linearized control depends on the region
  where its model remains accurate. Dynamics, input/state constraints and collision
  constraints are separate parts of trajectory optimization. A two-parameter
  endpoint guess does not solve that complete problem.
- [Perez et al., LQR-RRT*](https://people.csail.mit.edu/gdk/pubs/lqr-rrtstar.pdf):
  the retrieved abstract/introduction derives both distance and extension heuristics
  from local linearization and LQR. Later PDF line requests failed; no detailed
  theorem claim is used. This motivates distinguishing the metric from the proposal.
  Sentinel deliberately preserves its existing metric in this single-mechanism test.

The mathematical derivation is specific to Sentinel's discrete update. It is a
proposal for finite testing, without a novelty, state-of-the-art, optimality,
completeness or cross-system performance claim.
