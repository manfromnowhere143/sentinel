# Research and comparison requirements — 28 October 2026

The [Iter188 numerical derivation](../iter188_early_timing_feasibility/MATHEMATICS.md)
remains the mathematical contract. No new theorem or state-of-the-art claim follows
from connecting it to a planner.

1. Gould et al., [Online, Reachability-Aware, Sampling-Based Motion Planning,
   arXiv:2609.09073v1](https://arxiv.org/html/2609.09073v1), 8 September 2026.
   Section III-D distinguishes a finite sampling failure from absence of a valid
   sequence, and states the recursive-feasibility and numerical limitations.
   Design inference: retain one-sided exclusions and unknowns, then test the complete
   budgeted system. This paper's vehicle experiments are not a matched Sentinel result.
2. Li, Littlefield and Bekris, [Asymptotically Optimal Sampling-based Kinodynamic
   Planning, arXiv:1407.2896v5](https://arxiv.org/abs/1407.2896v5), 5 February 2016.
   SST and SST* address sparse kinodynamic exploration with asymptotic guarantees.
   Design inference: finite retention changes need explicit budget and outcome tests;
   a sparse-looking tree or local witness supplies no asymptotic guarantee here.
3. [OMPL control-RRT documentation](https://ompl.kavrakilab.org/classompl_1_1control_1_1RRT.html),
   accessed 28 October 2026. The interface distinguishes nearest-neighbor state,
   intermediate-state insertion, repeated solve and termination. We preserve the
   already qualified modified Iter186 binary; current web documentation is context,
   not a replacement for its frozen headers, runtime and source identities.

The mission needs several distinct demonstrations. Necessary feasibility asks what
can be ruled out. Search competence asks what the available budget can find.
Recoverability asks what remains possible from the actual observed history.
Information value asks whether a signal changes useful decisions against a strong
responsive baseline with equal access and action limits. Competitive advantage
requires a named versioned comparator, held-out cases, resource accounting and
uncertainty across gains and harms. The present exposed four-case test addresses
only finite search competence under one necessary eligibility amendment.
