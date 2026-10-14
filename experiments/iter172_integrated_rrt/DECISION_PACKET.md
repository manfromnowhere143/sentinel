# Qualify the integrated planner under the original four-case contract

Evidence: Iter171 admits 12/12 local tasks, but the old released-RRT bridge returns
only one constant-control step. The original corrected adapter completed 0/4 cases
in Iter167. Neither fact establishes the integrated planner or source recovery.
The integration must represent varying controls, absolute time, failed targets and
all optimizer work explicitly before it can be evaluated.

Alternatives: execute only the first optimized action; encode a validated sequence
as one RRT edge; or replace the released planner. First-action receding control
throws away the qualified maneuver; replacing the planner obscures the immediate
integration question. Choose a sequence edge while retaining released OMPL 2.0.1
RRT, its sampler, metric, goal bias and nearest-neighbor implementation.

The custom directed sampler returns a contiguous admissible prefix, represented
by a recorded sequence token and exact duration. This is a specialized bridge,
not a generally interoperable constant-control OMPL dynamics implementation.
Unexpected native propagation still throws. All selected sequences expand into
physical controls and independently checked states before scientific admission.

Freeze four original cases and seeds; 18,000 transitions, 120 seconds and 96
physical actions per case; original 4/8-second checkpoints and every scene/physical
constraint. Inner solves use at most eight predicted steps and 1,024 transitions,
counted within the outer cap. Eight is the longest locally qualified maneuver;
1,024 covers the observed 960-transition turns while reserving work for multiple
tree expansions. This allocation is prospective, not demonstrated optimal.

Acceptance: all four cases complete and independent scalar admission passes. Any
valid miss contradicts integrated qualification. Invalid accounting invalidates
admission. One seeded run per case, each in a fresh process; no outcome-dependent
retry, retuning or source comparison. Resources are the already installed CPU
OMPL/SciPy runtimes, bounded output and 900 seconds per producer/checker stage.
A pass would permit a separately frozen source comparison; it would not demonstrate
recovery, transfer, real-time operation, safety or superiority.
