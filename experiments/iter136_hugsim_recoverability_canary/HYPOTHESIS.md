# Iteration 136 HUGSIM recoverability canary

Status: preregistration for a bounded development canary, 2026-10-09. Commit this file alone
before executing the new probes or simulation episodes. Source inspection and historical outcomes
informed this design and are disclosed below. This is not a confirmatory generalization test.

## Operator decision and lineage

Daniel explicitly instructed continuation of the information and recoverability direction after
the 2026-10-09 strategic assessment. This file records the agent's implementation of that order:
defer Iteration 135 without changing its arms, outcomes or historical artifacts; begin this
separate development experiment. Iteration 134 remains the last completed driving result.
Generation-17's failed R17 path remains failed. This successor does not claim its acceptance or
retry it. Commit on a dedicated research branch descending from accepted F17
`8c118b74c699bf0f139f9bd659192bad06b895f8`; do not rewrite or merge around accepted history.

## Question and disclosed development case

Can fresh-process, seeded HUGSIM executions reproduce the same closed-loop trace closely enough
to compare a fixed set of timed stop interventions on one previously inspected failure case?

Case: `scene-0411-hard-00`, scenario SHA-256
`9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9`.
It is slot 1 of the committed iteration-111 support-core manifest. Historical run labels do not
establish simulator RNG seeds. New runs receive new identities; reproducing each other does not
establish exact reproduction of the historical run.

Pinned upstream source: HUGSIM `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`, UniAD_SIM
`5fb279e39912a5ac7f58e00d56b065cadcd0a749`. Retain source URLs and content hashes. The source
inspection before this registration found that HUGSIM reset does not restore steering or actor
controller state, accepts a seed without using it, and calls a state-advancing actor planner.
The historical driver calls reset twice. UniAD retains temporal BEV and tracking state. These
observations motivate fresh processes and trace comparisons rather than an assumed reset API.

## Stage zero source and environment feasibility

Execute the exact pinned reset method in a lightweight fixture with rendering and actor planning
replaced by explicit stubs. Test repeated reset, changed steering/control history, seed forwarding,
and actor-state advancement. Publish observed behavior, source identity, fixture limitations and
known-bad checks. This tests source semantics only, not CUDA rendering or actual actor dynamics.

Read the provider and, when available, the existing Sentinel host to identify source revisions,
scene and checkpoint availability, environments, free storage and competing processes. Starting
the previously stopped existing host for bounded inspection is in scope; no replacement instance,
new accelerator, disk resize, or asset reconstruction is included. Stop it after this task's work
if it was initially stopped and no unrelated workload has appeared. Provider failures and missing
assets are retained as operational evidence, not zero outcomes or a scientific null.

## Stage one paired reference runs

Only after source, assets, process ownership, storage and instrumentation tests pass, execute two
fresh-process references on the one case. Simulator Python/NumPy/Torch seed is `136`; preserve and
record the client's existing seed `0`. Use the frozen released-union monitor, parameters and
all-zero trajectory actuator. Preserve the historical double-reset startup sequence in both arms
and document it. No warm reuse of the model, simulator or monitor state is allowed.

Instrumentation records pre-action time, ego and actor state, incoming and executed trajectory,
controller command, post-action state, terminal flags, collision and progress, plus observation
hashes and process/source/seed identities. All values must be finite and records complete.
Require equal episode lengths and terminal reasons, exact observation hashes and discrete flags,
and absolute tolerance `1e-6` with zero relative tolerance on numeric trace fields. Compare all
frames, not only final score. Any mismatch closes Stage one as `REPLAY_DIVERGED`, with the first
divergence retained; it does not authorize seed or tolerance tuning.

If both references agree but have no collision, record `NO_RECOVERABILITY_TARGET` and do not
select another case in this canary. Otherwise Stage two may proceed.

## Stage two fixed intervention grid

Run exactly three fresh-process branches with stop onset at simulator timestamps `0.0`, `2.0`,
and `4.0` seconds. Before onset, execute the same released-union policy; from onset onward,
replace the outgoing plan with the same all-zero trajectory on every frame. Do not add a new
actuator or alter the low-level controller. References and branches share initial seeds and
configuration; actor reactions after intervention are allowed to differ.

Validate the entire pre-intervention prefix against the reference, including the observation and
incoming plan at the first intervention decision. A branch whose prefix diverges is `invalid`.
An onset never reached is `unobserved`, not an unsuccessful intervention. There is no assumption
that earlier braking is always better or that stopping is intrinsically safe.

For valid branches report collision and its type, time to termination, route completion, realized
stop frames, and severity if the simulator actually provides it. Avoidance over the observed
horizon with route completion at least reference minus `0.05` is the explicit useful-outcome bar.
Report collision-free branches below that bar separately as a progress tradeoff. Early off-route
termination, missing outcomes, truncation or a timeout cannot count as prevention. A valid
comparison requires observation through the reference collision time unless route completion
has already reached the benchmark's successful terminal condition.

No successful branch means no successful intervention in this finite grid and policy library.
It is not a proof of physical inevitability or an estimate of real-world safety.

## Budget and stopping

At most five simulation episodes: two references and three conditional branches. Each has a
1,200-second wall timeout; at most 120 minutes of instance runtime for this session including
inspection and setup. A failed or invalid episode is not retried. Infrastructure failure before
an episode starts may be diagnosed within the same bound, without changing this protocol.
No automatic expansion of cases, seeds, grid, thresholds, tolerance or compute.

Require at least 15 GiB local free space before proof collection, 100 GiB remote free before GPU
episodes, and projected remaining remote reserve at least 25 GiB. Only hash-verified duplicate
checkouts or reproducible caches may be removed. Retain the evidence required to regenerate each
reported value. Runtime output goes to a new iteration-136 directory; never overwrite earlier
proof or execute the old iteration-112 launcher's cleanup/retry behavior.

## Validation and reporting

Before live episodes, retained known-bads must reject altered observations, reordered/missing
frames, nonfinite fields, changed source/seed identity, differing terminal states, late-only
comparisons and prefix divergence. Use a separately implemented comparison check on retained
traces where feasible. Unit/fixture success is tooling evidence; it cannot substitute for a live
reference pair. Commit raw proof before interpreting new episode outcomes. Publish failures and
resource blocks at full weight. Update continuity with the actual stage reached and explicit
next command; do not imply that an unrun stage completed.
