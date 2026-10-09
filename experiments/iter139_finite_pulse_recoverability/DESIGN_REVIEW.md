# Challenge to the finite pulse design

The Iter138 arithmetic recount again matched all retained timing quantiles, counts, numerical
records and trace equality. See [the independent recount](proof/iter138_arithmetic_recount.json).
The decision to continue rests on repeatable development evidence, with collision and latency
failures preserved. It does not rest on being certain that this is the best possible research path.

The source review identified two distinctions that matter before collecting new outcomes.
HUGSIM's raw route completion can exceed one: its numerator is a discrete nearest-camera index
and its denominator is 90% of the recorded camera count. The previous validator's [0,1]
restriction could reject a successful route. The new schema accepts the source's [0,10/9]
range without clipping, and tests successful overshoot and invalid excess. This does not change
Iter138's reported 0.11557062998555366 outcome or revise its closed evidence.

The evaluator's `nc` field scores planned trajectories and can be fractional. It is not the
probability that the executed episode avoided collision. Iter139 takes actual collision flags
from `env.step` for its endpoint and preserves the evaluator output as a separate artifact.
The retained source is [hug_sim.py](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt)
and [the original driver](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/closed_loop.py.txt).
The [bound evaluator source](proof/score_calculator.py.txt), retained during execution without
changing it, confirms the per-plan collision checks and frame averaging. Its reported `rc` is
the clipped maximum over frames; Iter139 instead retains raw progress at the specified time
and at termination. Those quantities need not coincide.

The experiment keeps three different quantities visible: assigned override frames, frames
where the override changes the incoming plan, and the released monitor's brake requests. A
zero incoming plan can make a scheduled override have no immediate plan effect. It must not
be reported as additional braking dose. Actual controls and state changes remain measured.

Successful recovery requires resumed planning, full route completion without actual collision,
and progress at the reference hazard time within the fixed five-percentage-point allowance.
Collision-free observation at the reference time alone is a bounded diagnostic. This avoids
mistaking delayed collision, an episode cap, a stationary vehicle or an incomplete run for
useful recovery. Tests include those failure modes and incomplete-grid false promotion.

The six development cells can establish only whether this action library contains a useful
response on this case. Even a positive outcome would leave online action selection, incremental
information value, independent-scene performance and physical timing unresolved. A null could
motivate a different action family in a new protocol; it cannot prove inevitable collision.
