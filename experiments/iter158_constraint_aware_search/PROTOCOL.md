# Iter158: constraint-aware actuator search

One exposed scene, reset [0,0,0,1,0], privileged static source model. Freeze this
protocol, PLAN and implementation in Git before initialization. Commit raw before
independent admission. No retry, parameter tuning or scene change within this study.

Every depth advances 0.25 seconds with the retained velocity/steering-first
discrete dynamics. Each beam node proposes 15 combinations of acceleration
{-2,0,2} and steering rate {-pi/12,-pi/24,0,pi/24,pi/12}, plus the three retained
zero-offset tracking commands at target speeds {2,4,6}. Exact duplicate commands
at one node are removed in first-occurrence order. All issued controls are retained.

Reject invalid controls, foreground contact, failed conservative foreground sweep,
distance over 10 m, and either historical progress condition at its exact sample.
Then query all 276,519 selected background centers at the new state. Only an
unambiguous clear decision survives. The reset is also queried. Other component
queries skipped after a rejection remain unobserved. No background broad-phase
approximation or changed threshold is introduced. Background is sampled, not
proved clear between samples. The foreground sweep covers the declared linear
pose interpolation, not an unmodeled continuous physical trajectory.

Guide search ordering with a visibility graph around foreground axis-aligned
bounds inflated by half the ego diagonal plus 0.25 m. Graph nodes are the four
corners per bound and the source completion point. Dijkstra gives distances to
that point. A state's score is its shortest visible connection plus remaining
graph distance, plus 2.7 times absolute wrapped heading error to that connection.
No visible connection receives 1,000,000 plus straight-line goal distance. This is
a heuristic, not an admissible distance bound or a collision/road test; background
and dynamic reachability are omitted from guidance but checked before admission.

Sort survivors by this guide score, descending nearest route index, increasing
route distance, absolute steering, accumulated squared commands, then creation ID. Keep one per
cell (floor(x/2), floor(y/0.5), round(yaw/0.1), round(speed/0.5), round(steer/0.065))
and group these representatives by round(speed). Take the best remaining node
from each speed group in score order, then the next from each, until at most 24
remain. This preserves slower branches needed to steer before accelerating.
Quantization affects pruning only; it never changes a state
or declares collision freedom. Stop at the first depth containing a full completion,
empty beam, 401 actions, 60,000 background queries, 1,800 seconds, or resource failure.
At a successful depth select the first complete survivor in that same order. A
budget limit before finishing a depth cannot admit a completion from that depth.

Retain every attempted transition with its rejection or survival, every beam and
its pruned count, and the best surviving prefix (highest progress, then shortest
prefix, then the same score). Full masks for that prefix are retained by a bounded
second producer pass; reserve 402 queries beyond the 60,000 search limit for it.
The best prefix does not become a complete solution. A no-solution outcome is
inconclusive about feasibility, even when the beam is empty. The 75 old candidates
are context, not an equal-compute performance comparator.

Independent admission reconstructs the selected chain from committed attempts,
recomputes scalar dynamics, limits, foreground geometry, route/progress outcomes,
ground height, all selected-point masks and threshold decisions at every retained
prefix state. The scalar checker imports neither the beam search nor vector query.
It checks raw inventory, input/source identities, resource envelope, chain and
terminal status. Unselected background pruning is producer evidence, not fully
scalar audited. Thus admission never promotes a failed search to an impossibility
claim or a statement that all possible commands were evaluated.

Known-bads include changed state, over-limit actuator, skipped progress, premature
completion, missing/changed mask, and false background clearance; a constructed
clear straight scene supplies a positive completion control before real acquisition.
Numeric ambiguity, missing/invalid data, budget exhaustion and software exceptions
remain explicit. An exception is invalid; a bounded search without an admitted
completion is inconclusive. Road compliance, physical occupancy, native recovery,
actual-trigger recovery, information benefit and transfer remain unknown.
