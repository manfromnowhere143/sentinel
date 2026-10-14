# Released control-RRT adapter

Four cases and four seeds are ordered explicitly in PLAN. Each case runs in a
fresh process, preventing reuse of the OMPL RNG or search tree. No witness controls,
case IDs or prior solutions enter the search API. The known route and current
state are disclosed inputs, as in Iter161.

Upstream control RRT uses exact linear nearest-neighbor queries, goal bias 0.1,
and no intermediate-state insertion. State distance is Euclidean after weights
`[1,1,2,0.5,2,0.01]` on x, y, wrapped heading, speed, steering and absolute frame.
Uniform route-index samples use a uniform lateral offset in [-3,3] m, heading
perturbation [-0.5,0.5] rad, speed [0,6], steering [-pi/3,pi/3] and frame [0,96].
The goal target is the first route index satisfying the existing completion metric,
with local route heading, speed2, steering0 and frame96. These are fixed guidance
choices, not admissibility restrictions or optimality claims.

The directed sampler evaluates the existing discrete and route-guided proposals
from the nearest tree state. Every proposed one-step transition counts, including
invalid proposals. Motion, steering/speed/lateral/yaw limits, foreground endpoint
and eight-subdivision sweep, route distance, absolute-time progress and full
background decision are unchanged. Choose the admissible successor with minimum
target distance, then attempt ID. Partial last batches remain counted. No sampling
or tree termination can bypass the inner attempt/time cap. Physical callback
exceptions invalidate the process; they cannot become a clear edge.

The sampler returns exactly one 0.25-second control. Unexpected native propagation
throws, preventing silent duplicate or unaccounted propagation. The native path
must retain the integer frame progression. Approximate OMPL solutions remain
incomplete even when the library reports a usable path. A completed path needs
progress >=1 and both case checkpoints in the independent scalar checker.

The background producer is the qualified vector implementation; admission uses a
separate scalar implementation. Selected edges must appear among the sampler's
accepted expansions. Unselected hard labels and native tree construction are not
independently replayed; this limitation is explicit. Budgets count initial, search,
returned-path and mask-materialization queries separately. No retuning or retry
follows a valid miss. A scientific miss is not converted into a software failure.
