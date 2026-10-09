# Iter141: nominal continuation with the released monitor in shadow

Status: preregistered development canary, 2026-10-09. Freeze this protocol before
implementation, provider start or episode observation. Parent: closed Iter140
`2614f7860283eee3b00bfa39cdfaf428066ec52d`. Daniel directly authorized continuation.

## Question and scope

Does the current nominal planner contain a useful continuation action on
`scene-0411-hard-00` when the released union would replace its plan with zeros?
Iter139 found zero useful recoveries in six finite pulses. Iter140 reconstructed
all contacts and found a reactive actor approaching from behind. Earlier Iter49
OFF runs also failed route progress; this lowers expectations. This canary closes
the current numerical-execution comparison once. It does not establish novelty,
safety, physical inevitability, online action selection or information value.

## Frozen schedule and action

Exactly four fresh-process episodes at most, in this order:
`reference_a`, `reference_b`, `nominal_a`, `nominal_b`.
References deliver the released union proposal. Nominal arms run the same monitor
with SENTINEL_ENABLED=1, including tracking and braking latch, but deliver the
current typed nominal planner array unchanged. Planning keeps responding to new
observations; no prerecorded trajectory playback. Capture nominal, monitor-proposed
and delivered arrays with dtype, shape, bytes and digest before transport. Link the
received array to the controller input and actual environment action. Monitor
errors or missing records invalidate the run rather than permitting a silent fallback.

Freeze HUGSIM `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`, UniAD_SIM
`5fb279e39912a5ac7f58e00d56b065cadcd0a749`, scenario SHA-256
`9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9`, checkpoint
`0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`, image
`sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14`,
seeds 136/0, double reset, and unchanged Iter137 numerical controller source
`7784c0a885bba33414a680d2f943f3a701d7ba38bf29996908c6a7bd4089dc03`.
Use single-thread BLAS/OpenMP and identical available CPU affinity/runtime. Bind the
new client wrapper, generated driver, dependencies and existing runtime before launch.
No package installation, changed weights, simulator repairs or alternate hardware.

## Model and control contract

The pinned controller uses 0.5-second prediction steps, 100 maximum iterations,
1e-6 convergence norm, no numerical-mode wall cutoff, acceleration bounded by
3 m/s², steering angle by pi/3 rad and steering rate by 0.4 rad/s. Its steering
state constraint can recompute the rate; check actual applied rates explicitly.
The simulator integrates at 0.25 seconds and does not enforce its declared Gym
acceleration bound of 2 m/s². Actor candidate timing is 0.1 seconds with trajectory
indices consumed at environment steps. These discrepancies remain part of the named
released-model contract; no physical admissibility or calibrated attack-timing claim.
Before actuation record and enforce finite controls, |acc|<=3+1e-9,
|steer_rate|<=0.4+1e-9 and |current/predicted next ego steering|<=pi/3+1e-9.
Record declared Gym-space violations separately; acceleration beyond 2 up to 3 is
allowed by this research contract. Never clip or replace a failed control. Retain
violations and stop; do not reinterpret them as an observed favorable outcome.

## Admission and failure rules

Both fresh references must match each other: exact observations and discrete fields,
absolute numeric tolerance 1e-6, zero relative tolerance, and exact typed arrays and
complete numerical controller records. Validate both against the retained Iter139
reference trajectory and numerical records, excluding only declared new source identity
and wall timing. Require identical terminal reason/length and actual reference collision.
A divergent reference closes REPLAY_DIVERGED; a matched noncolliding reference closes
NO_RECOVERABILITY_TARGET. No case or seed replacement.

For each continuation, compare the full prefix before the first actually different
monitor-proposed versus nominal array; at that first decision require identical
observation, pre-action state and typed nominal/proposed arrays. After that decision
feedback may differ. If no changed action occurs, report NO_ACTION_CONTRAST. The two
nominal episodes must match traces and numerical records under the same contract.
Independently replay every controller call from original source in the bound runtime.
A separately implemented Decimal checker must recompute prefix/paired equality,
control bounds and recovery outcomes. Reference and nominal replicas are reproducibility
checks, not independent population samples.

Before live work test the complete multi-frame client-capture, monitor, transport,
controller, action and trace path. Retain known-bads for disabled monitor, wrong plan,
dtype loss, missing/reordered records, wrong action/control limit, reference/prefix/
replica divergence, false recovery, censored/missing endpoints and resource/predecessor
gates. Commit exact source and test receipts before deployment. All runtime files must
match the manifest. Retain raw episode files in Git before interpretation or the next
episode. A failure, incomplete log, process timeout, invalid linkage or replay mismatch
stops later execution. No initialized-episode retry or optional stopping after success.
Infrastructure diagnosis before initialization stays within the same resource budget;
source/data/claim changes require a pre-evidence amendment. A correctly recorded
simulator/401-frame truncation is censored and allows the next scheduled replica.

## Outcomes and decision rules

Original horizon: at most 401 actions, 100.25 simulated seconds; preserve earlier
collision, route completion and other environment termination. Raw route completion
range is [0,10/9]; do not clip. Let T be the actual first fresh reference collision
time and R its route completion. Report collision, first collision time, terminal
reason/time, raw final progress, and progress at T (or successful route completion
before T). Missing T remains null; earlier collision is not imputed as zero progress.

Useful recovery requires no actual collision anywhere in the completed branch,
route completion within the original horizon, progress at T >= R-0.05, a reached
actual action contrast and valid execution/prefix. Collision-free-through-T is only
a diagnostic. Report monitor requests and actual changed delivered frames separately.
Both nominal replicas useful and matched: NOMINAL_CONTINUATION_SUPPORTED. Both valid,
matched and not useful, with no censoring: NOMINAL_CONTINUATION_NULL. Censoring without
recovery: NOMINAL_CONTINUATION_INCONCLUSIVE. Replica mismatch or invalid/incomplete
schedule cannot receive supported/null. Do not extend the horizon or tune after data.

If supported, freeze the action opportunity and separately test a strong responsive
action selector plus a specified information ablation, including harmful no-brake
cases. If null, close this case/action comparison and design a finite new case-family
study. Do not begin another strength/clock search here. Privileged geometry remains
diagnostic, not an undeclared deployed monitor input. Iter135 remains deferred;
Iter136–140 remain closed with all failures/nulls preserved.

## Timing, resources and cleanup

Keep fixed simulation and measured wall time separate. Retain stop reasons, solver,
adapter, complete controller-call and client-roundtrip durations, nearest-rank
p50/p95/p99/max and >50 ms counts/denominators. Additional capture is included in
client roundtrip; this is not isolated inference or a vehicle deadline experiment.

Only existing `sentinel-gpu`, ID `3834622546652649531`, project
`sunlit-unison-487018-b0`, zone `us-west1-a`, g2-standard-8/L4. Up to three start
requests within ten minutes for capacity; inspect successful DONE operation and
RUNNING original instance before SSH. Overall **150 minutes from first start request**,
including preparation, four episodes, collection/replay and cleanup; no resetting.
Owned shutdown timer by minute 148. Each episode has 1,200-second wall limit and
requires 1,230 seconds remaining before the timer. Require 15 GiB local collection
space, 100 GiB remote space and 25 GiB reserve after 8 GiB projected episode output.
Exclusive new Iter141 paths, no replacement VM, no automatic budget expansion.
Stop owned compute on completion/failure/budget and retain final provider status.
