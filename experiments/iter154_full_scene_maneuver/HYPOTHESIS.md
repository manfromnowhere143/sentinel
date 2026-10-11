# Iter154: validate the fixed maneuver in the full scene

Preregistered 11 October 2026, before new simulator execution. Parent research closure is
b00861cbfcafa5fe977ca7d3f72b8487fdeb0bba. Daniel's continuing mission instruction authorizes
this bounded experiment and its automated operational verification.

## Question and fixed population

Does Iter153's selected maneuver_059 complete scene-0013-medium-00 under the native HUGSIM
renderer, background/foreground collision functions and route termination, while preserving
registered useful progress? The selected packet's 65 actions are immutable. Two fresh replicas,
seed 144, one reset each, same scene/source/assets and the retained timed actor adapter. This is
one exposed development scene, zero holdouts and no population estimate. No alternative candidate,
search extension, initialized retry or success-dependent stopping is allowed.

This is privileged predetermined action delivery. UniAD and the Sentinel perception/monitor
client are bypassed. It tests whether an available maneuver exists in this simulator; it does
not identify information benefit, monitor selection ability, real-time operation or a deployment
policy. Native rendering still runs for every reset and step, including current actor transforms.
No synthetic monitor or client logs may be substituted for absent inference.

## Boundaries and measurements

Use the exact selected packet, source dt=0.25 s, wheelbase=2.7 m, acceleration within ±2 m/s²,
steering rate within ±pi/12 rad/s, steering angle within ±pi/3, speed within [0,6] m/s.
Preserve the Iter153 comfort screens (absolute lateral acceleration <=4.89 m/s², yaw rate <=0.95
rad/s) and progress at 7.75 and 9.0 seconds against the disclosed historical nominal/monitor
collision fractions, each with 0.05 slack. Separate scalar replay checks each applied action,
source transition and expected model state to 1e-9, route sample criterion, foreground geometry,
source collision receipts, actor/render correspondence and the complete trace inventory.

Record the native background-collision call on actual CUDA scene points, including point count,
result, time and bound source/assets. The independent replay can check that receipt and its
outcome consistency; it cannot independently reconstruct the unavailable full point cloud locally.
Do not describe that limit as a second implementation of background collision. Foreground contact
is separately reconstructed from recorded boxes. Road compliance remains unknown: source route
distance is not a drivable-area boundary. Native endpoint collision is not a continuous physical
safety guarantee. Preserve the prior model interpolation result within its original scope only.

Require exactly one native reset, fresh runtime clock, matching original route/reset and current
actor identity. Record every camera render, RGB digest, native action input and post-step state,
separate collision channels and native terminal flags. Unexpected source/reset, missing data,
nonfinite/out-of-bound controls, repeated/out-of-order actions or state disagreement are invalid
execution. A native collision or off-route termination is an observed failure, not invalid data.
All such outcomes and partial records are retained. Actual actor motion may contradict the model's
stationary extension; keep the discrepancy visible rather than modifying actor state.

## Outcome and decision

Supported full-scene maneuver feasibility requires both admitted replicas to reach native route
completion within the exact 65 actions, with no observed collision/off-route, all control/comfort
screens and both progress checks. The native route criterion is near 90% of sampled camera poses;
report the actual final index and whether the literal final sample is reached. Reaching action65
without native completion is censored/inconclusive, never success. Stop on any earlier native
termination, and do not continue actions beyond native termination or the packet horizon.

Both replicas must be attempted unless infrastructure, identity or execution-invalid evidence
requires stopping the pair. One or two observed collision/off-route failures contradict the
proposed useful maneuver in that stated scope; discordance is reported explicitly. Missing,
uninitialized and invalid cases stay distinct. Replica agreement is not environmental independence.
No statistical significance or confidence interval is estimated from two deterministic replicas.
Historical Iter151 nominal and Iter152 monitor results retain their original IDs and bytes and
contribute zero new episodes. Recheck retained trace source/reset compatibility before comparison.

A successful result licenses designing a prospective information-selection test against a
competent responsive baseline. A failure licenses investigating the specific model/scene/interface
mismatch. Neither result automatically licenses trying the other thirteen model candidates.

## Resources, retention and qualification

One existing sentinel-gpu VM, ID3834622546652649531, sunlit-unison-487018-b0/us-west1-a,
g2-standard-8 with one L4. One fresh start, at most3600seconds/$3 conservative incremental compute
at $3/hour; storage/taxes excluded, not an invoice. Child<=1200seconds, pair<=2500seconds.
Independent local watchdog, unique host shutdown timer and pair service retain exact-start ownership.
Require >2800seconds remaining before pair launch. Existing bounded observation recovery cannot
extend any deadline or initialize work again. Local free>=17GiB, remote>=100GiB, reserve25GiB;
collected/extracted block evidence<=2GiB. No infrastructure creation or package installation.

Reuse Iter149–152 lifecycle, process-birth ownership, read-only observation reconciliation,
bounded collection and exact-start shutdown. Adapt only explicit new plan/root/schema/worker
bindings; retain older code and evidence unchanged. Before provider start, test changed packet,
wrong scene/reset/source, action order/bounds, premature terminal, background collision, state
mismatch, missing collision/render observations and false success. Rehearse raw retention and
independent replay with labeled synthetic fixtures; they are not simulator outcomes. Perform
CPU-only Linux ownership/deadline qualification before scientific initialization.

Freeze source and qualification before compute. Commit raw before independent scientific admission.
Retain adverse/partial outcomes, host integrity postflight, resource accounting and verified shutdown.
New research publication does not imply master integration or a whole-repository CI pass.
