# Integrated RRT qualification, frozen before four-case execution

Population/order/seeds are exactly Iter167: bend_left/20261014,
bend_right/20261015, chicane_left/20261016, chicane_right/20261017. Cases are read
from the immutable Iter161 CASES.json; no case IDs, witness actions or retained
solutions enter the planner or connector. Preserve 18,000 attempted transitions,
120 seconds and 96 physical actions per case; 1 GiB RSS, 256 MiB total raw output,
2 GiB minimum free disk and 900 seconds per producer/checker stage. The four runs
use separate subprocesses, isolated native RNG/tree lifetimes and reaped exits.

Keep the released OMPL 2.0.1 control-RRT algorithm, linear nearest neighbors, 0.1
goal bias, disabled intermediate-node insertion, weighted six-coordinate distance,
route-index target sampler and frame-96 route-completion target exactly as Iter167.
The bridge changes its control payload to an integer sequence token. The callback
returns its physical step count in [1,8], endpoint and token. The native path's
token, parent, endpoint and duration must resolve to the recorded physical sequence.
No repeated constant acceleration is inferred. Unexpected native propagation fails.

For a nearest node at integer absolute frame f and sampled target t, request
H=min(8,96-f,max(1,ceil(t.frame-f))) steps. A frame-96 node returns no connection.
The local target is the sampled five-coordinate state, without reachability
clamping or invented witness-derived target. Retain Iter171's physical control
initialization, centered increment coordinates, residual, default two-point
Jacobian, exact TRF subproblem, Jacobian scaling, linear loss, max_nfev=100 and
1e-12 tolerances. Local target tolerances remain [.02,.02,.002,.01,.002]. These
are guidance; route/checkpoint completion retains its original independent rule.
The four planner cases prescribe no explicit stop/wait phase. Therefore neither
is imposed: both controls remain free, with original physical bounds. Local
qualification with explicit phases is not evidence that RRT will discover them.

The inner cap is min(1,024,remaining outer transitions). Every new rollout reserves
H steps before evaluation and charges each actually computed transition, including
invalid trials, finite differences and line-search calls. Exact physical-parameter
cache hits have no duplicate propagation; requests and cache identities remain
visible. The absolute outer deadline is checked before every rollout and every
step. All initial, connection-root, search, returned-path and mask-materialization
queries are accounted separately. An inability to reserve the next H steps ends
search at the attempt cap with fewer than H unused transitions.

Each trial predicts the full local horizon, including motion beyond a rejected
state for numerical guidance. Only the initial contiguous clear prefix can become
an edge. Rank its prefixes by original RRT target distance then earliest prefix;
rank across evaluations by global completion first, target distance, evaluation ID
and prefix. Interrupted evaluations yield no edge. A physically valid prefix
reaching route completion at or after the final checkpoint stops the rollout and
solve immediately; earlier completion is rejected. Full local target attainment
also stops the solve. A target miss can still return an admissible prefix; no valid
prefix returns zero duration. Exact/partial/failed connections are distinct from
planner completion. An optimizer convergence flag never establishes either.

Motion, actuator bounds, foreground endpoint and swept checks, background decisions,
route distance and absolute-time progress checkpoints remain unchanged. All
intermediate states are checked even though only edge endpoints enter the tree.
The independent checker reconstructs every attempted motion/physical predicate,
prefix choice, parameter/request/cache accounting and native path-token binding.
Full scalar background masks cover selected returned paths; unselected labels and
the native tree/RNG are retained producer evidence, not independently reconstructed.

Source and selected runtime identities freeze before execution. Commit raw before
separate scalar admission. All four exact completions plus valid replay support
this finite integration claim; any valid miss contradicts it. No retuning, retry,
new seed or source execution follows a miss within this study. The all-four pass
can qualify a future separately frozen source comparison; source recovery remains
unknown regardless of this study's outcome.
