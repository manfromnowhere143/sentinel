# Primary research checked for the next engineering decision

Reviewed 27 October 2026. This is a targeted assessment, not an exhaustive survey.
External results are their authors' reports; none is a matched Sentinel comparison.

| Version and source | Relevant evidence | Design implication — our inference |
|---|---|---|
| Zhang et al., [Guiding End-to-End Driving Models with Endpoint-Constrained Trajectory Optimization, arXiv:2609.31383v1](https://arxiv.org/html/2609.31383v1), 25 September 2026 | ECO repairs intermediate waypoints while preserving the policy endpoint and anchoring to executed history. It reports closed-loop improvements across tested policies. Its limitations explicitly include an incorrect fixed endpoint and absence of reasoning about other agents. | A later Sentinel comparison should include responsive trajectory repair with matched information and actuation. A steering/braking opportunity alone cannot show information value. Preserve actual history and measure execution, including adverse effects. |
| Xiong et al., [TerraTransfer++: Demonstration-Free End-to-End Planner, arXiv:2610.30319v1](https://arxiv.org/html/2610.30319v1), 21 October 2026 | The paper distinguishes a privileged self-play teacher from vision students and separately reports native planned-trajectory and realized-rollout scoring across 436 HUGSim scenarios. It describes severe tier-specific failure modes alongside aggregate results. | Match information access and scoring versions before comparing systems. Keep physical outcomes, useful progress and intervention costs visible. Sentinel's four exposed constructed cases cannot support benchmark parity or population claims. |
| Li, Littlefield and Bekris, [Asymptotically Optimal Sampling-based Kinodynamic Planning, arXiv:1407.2896v5](https://arxiv.org/html/1407.2896v5), 5 February 2016 | SST/SST* couple node selection, propagation and pruning to formal asymptotic results under stated assumptions. Retaining a sparse tree is part of a complete algorithmic argument. | Our one-extra heuristic has no inherited completeness or optimality theorem. Test its finite behavior and losses under unchanged resources. A future SST comparator would need its own explicit interface and qualification. |

These sources do not justify replacing the frozen trial with a fashionable model.
The immediate evidence gap is whether the proposed online retention mechanism
helps inside the original budget. The broader research priority remains useful
action at the actual decision history under measured delay, strong responsive
comparators and newly held-out scenes. External reading informs future protocols;
it does not alter this trial's cases, thresholds or outcome definitions.
