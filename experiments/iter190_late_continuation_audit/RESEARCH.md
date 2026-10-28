# Feasibility, finite search and observed expansion

Primary sources checked 28 October 2026. This note interprets the frozen audit;
it does not amend its population, programs, limits or stopping rule.

Gould et al., [Online, Reachability-Aware, Sampling-Based Motion Planning,
arXiv:2609.09073v1](https://arxiv.org/html/2609.09073v1), 8 September 2026,
Section III-D, identify three distinct limitations: finite sampling can miss an
existing admissible control sequence, finite-horizon feasibility need not survive
later evolution, and numerical trajectory checks can miss violations. Our design
inference is to keep necessary exclusions, checkpoint witnesses and complete
continuations separate, and to replay the complete retained query population.
Sentinel's source-model checks do not acquire that paper's disturbance guarantees
or establish physical safety between background-query samples.

Li, Littlefield and Bekris, [Asymptotically Optimal Sampling-based Kinodynamic
Planning, arXiv:1407.2896v5](https://arxiv.org/abs/1407.2896v5), 5 February 2016,
establish asymptotic properties for SST and SST*. Our inference is narrower:
finite-budget expansion must be evaluated using the actual transitions and
stopping rules. A small tree, retained branch or unexpanded node alone is not
evidence of those properties in Sentinel.

The [official OMPL control-RRT interface](https://ompl.kavrakilab.org/classompl_1_1control_1_1RRT.html)
separates the nearest-neighbor structure, directed-control sampler, intermediate
state insertion and termination condition. This motivates inspecting the observed
expansion stages separately. The bound historical binary and native event records,
not current online documentation, define the audited execution.

## The question as a conditional witness

For each retained node, the audit joins its original path to a proposed suffix
at the exact state and absolute frame. A completion requires every joined
transition to satisfy the frozen dynamics, controls, foreground and background
checks, progress schedule and final route rule. A checkpoint is only one of these
requirements. A rejected attempted transition still consumes computational work.

For each arm, admitted conditional work must fit both inequalities:

```text
original attempts through registration + every attempted probe transition <= 18,000
entire original case search wall + charged conditional arm wall < 120 seconds
```

The additional caps are 2,048 attempts and 20 seconds per arm. Shared-root records
use the smallest remaining allowance in their group; original histories stay
distinct. Full original wall is a conservative debit. These are separate
conditional alternatives, not a claim that the integrated planner performed all
42 arms inside one 18,000-transition run. Replay is offline evidence work.

A successful joined path establishes existence under this model and schedule.
Failure of either finite program family leaves other actions unresolved unless
a separately checked necessary bound excludes them. An original node receiving
no request establishes lack of observed expansion, but establishes a missed
feasible opportunity only when that same node has an admitted full continuation.
Even then, selecting the node online and preserving other successes requires a
new integrated trial. It does not identify the isolated cause of a prior miss.

No comparator implementation was run here. Organization-level superiority,
actual-history recovery, information advantage and sensing-to-actuation delay
remain outside this result.
