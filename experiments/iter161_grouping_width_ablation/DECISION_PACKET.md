# Iter161 decision: measure the two deletion stages separately

The bottleneck is finding a complete model-valid action with a credible search
baseline. Iter159's route/speed-group candidate completed 3/4 constructed controls.
Iter160 found one fixed-suffix terminal change among five pairs, but the failed
route candidate's first replacement still completed. Its later log audit also
showed that cell selection and final beam retention had been conflated in some
descriptions. Neither result identifies the cause of the whole-search miss.

Run one fixed-budget 2×2 comparison: exact versus quantized grouping, widths 24
and 48. Keep route guidance, proposals and constraints fixed. Preserve a complete
account of both deletion stages. This directly answers the operator's next task.
Primary falsifier: any scalar-admitted exact/24 miss on the four frozen controls.
Full details and resource limits are in [PROTOCOL](PROTOCOL.md) and [PLAN](PLAN.json).

Exact grouping removes a particular approximation, not all pruning. Identical
state bits plus absolute frame have the same available future controls and fixed
scene predicates in this implementation. That is a code-level rationale, not a
completeness theorem. Near-duplicate states may crowd out diverse continuations;
wider beams spend more of the cap per depth. Either change can hurt completion.
Fully reflect the foreground as well as the route in a new fixture version;
keep the prior experiment intact.

Alternatives are a width-only sweep, an immediate released-planner adapter, or
more custom guidance. A width-only sweep leaves grouping confounded. Guidance
changes introduce another explanation. The small factorial answers the present
mechanical question before choosing whether further custom work is justified.
If exact/24 fails, do not expand this search by default: qualify a released
adapter against the same model and completion rule first. If it passes, first
test the already exposed source-model opportunity under a fresh frozen envelope;
do not equate these synthetic controls with native recovery.

Primary-source review, 12 October 2026: [SST/SST*](https://arxiv.org/abs/1407.2896v5)
studies sparse kinodynamic planning with different asymptotic guarantees for the
two methods. Those guarantees do not transfer to this finite beam experiment.
The inspected [OMPL SST source](https://raw.githubusercontent.com/ompl/ompl/5b209a03fe48c41f7a2f364382c2e425bf1c7c1c/src/ompl/control/planners/sst/src/SST.cpp)
has separate selection/pruning radii and can return approximate solutions.
The [status interface](https://raw.githubusercontent.com/ompl/ompl/5b209a03fe48c41f7a2f364382c2e425bf1c7c1c/src/ompl/base/PlannerStatus.h)
accepts approximate as well as exact solutions in boolean conversion. A future
adapter must demand exact status and independently verify completion, including
a retained near-goal rejection. No library execution or comparison is claimed.

Acceptance is a full evidence chain and an honest answer, including a failed
candidate. The broader mission remains useful model action, native recovery,
actual decision-time history, equal-cost information ablation and held-out transfer.
