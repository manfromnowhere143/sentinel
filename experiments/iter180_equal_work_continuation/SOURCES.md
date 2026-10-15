# Source ledger and scope

The immediate evidence is the closed [Iter179 audit](../iter179_frontier_continuation_audit/RESULT.md)
and its [interpretation correction](../iter179_frontier_continuation_audit/CORRECTION.md).
The actual retained [program generator](../iter177_pose_aware_seed/forward.py) and
[corrected evaluator](../iter178_root_domain_consistency/connection.py) are reused;
the [stepwise probe](../iter179_frontier_continuation_audit/probe.py) is reused at
width two. Immutable input hashes and transitive source identities are in PLAN.json.
No third-party implementation is copied into this comparison.

Primary sources reviewed 15 October 2026, before new retained-root acquisition:

- Moncton and Frew, *Achieving Asymptotic Near-Optimality Without Delta-Similarity*,
  [arXiv:2609.04464v1](https://arxiv.org/html/2609.04464v1), 3 September 2026,
  sections II–IV. The paper separates sampling useful segments from retaining
  them in SST and addresses a gap involving local pruning. Inference for Sentinel:
  propagation, retention and future expansion need distinct evidence. This does
  not diagnose SST-style pruning in the present RRT or transfer an asymptotic
  guarantee to its finite, timed-checkpoint model.
- Gao, Lu and Kingston, *Fast Asymptotically Optimal Kinodynamic Planning via
  Vectorization*, [arXiv:2607.03987v2](https://arxiv.org/html/2607.03987v2),
  12 July 2026, sections IV and V-D/Table IV. PAKR distinguishes parent selection
  from multiple candidate propagations; its branching study reports finite-run
  tradeoffs. Inference: count parent opportunities, actual propagation and wall
  time separately. Its GPU timings and algorithms are not Sentinel measurements
  and do not justify unmeasured intervention latency or new GPU execution here.
- Vielmetti, Cherenson and Panagou, *Stochastic Multi-Objective Kinodynamic Planning
  Against Adversaries*, [arXiv:2607.19284v1](https://arxiv.org/html/2607.19284v1),
  21 July 2026, sections IV/VI and Remark 4. The paper searches feedback-policy
  sequences; its pruning discussion explicitly identifies information lost by
  expected-state projection. Inference: do not equate similar progress or pose
  with equivalent future opportunity. No stochastic certificate or completeness
  property is imported, and deterministic witnesses do not replace the eventual
  responsive-comparator intervention test.

Retained primary HTML hashes and review notes are in
~/.codex/reports/sentinel/iter179/next-step-source-review.json. These papers motivate
questions; they are not scientific authority over Sentinel outcomes or permission
to relax this comparison's predicates and budgets.
