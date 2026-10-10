# Iter143 model contract qualification

Status: preregistered source diagnostic, 2026-10-10. Parent: closed Iter142
`75e0727d564ce19a66199155662d2b5daf4a7fcf`. Commit before implementation and new
fixture calculations. Local CPU only; no provider, host, GPU or live episode access.
This is source qualification and study design, not a recovery or information-value
experiment. Existing outcomes and known source mismatches have already been seen.

## Question and prior exposure

Can the retained controller, environment and actor planner be treated as one
consistent time-and-control contract for a new physically interpreted study?
Prior inspections established controller/environment intervals .5/.25 s, a .1 s
argument to AttackPlanner, differing controller and declared Gym limits, and lack
of Gym clipping in step. This session also inspected upstream spline and forward
sampler bytes that exactly match the Iter142 runtime manifest. Spline sampling
uses tf/(N-1), whereas low-speed resampling uses tf/N. Source inspection suggests
additional integration-order and timing discrepancies; new measurements are pending.
No source inspection is represented as blinded prediction or a driving outcome.

## Inputs and execution

INPUTS binds retained environment, controller, actor source/configuration, the
Iter142 runtime manifest and the two historical scenario hash inventories to parent
Git bytes. Two newly retained upstream source files must match prior runtime hashes.
Reject missing, changed, symlinked, oversized (>16 MiB), duplicate-key or nonfinite
input. Existing scientific source and closed results are immutable. Retain upstream
license and exact source identifiers. No full simulator import, checkpoint load,
pickle deserialization, package installation or source alteration is required.

Use existing local CPU Python/NumPy/Torch/SciPy/pytest and retain versions. These
are diagnostic versions, not the bound Linux simulator environment. Extract named
source AST functions/method segments and report exact selected line ranges. Execute
real tensor arithmetic on CPU. Synthetic actor candidate generation may be injected
only to isolate documented call/sampling/index semantics; record every stub and
never claim full actor-policy, renderer, collision or scene reproduction.

## Frozen qualification fixtures

1. Ego transitions: Cartesian product v in {0,4}, heading in {0,.3}, steering in
   {0,.2}, and (acc,steer_rate) in {(0,0),(2,.2),(-2,-.2),(3,.4)}: 32 states/actions.
   Use initial planar position zero. Compare actual source environment integration
   against source controller dynamics at equal .25 s and at one .5 s controller step
   versus two .25 s environment steps under held controls. Explicit coordinate mapping:
   controller (x,y,heading) corresponds to environment (b,a,theta). Preserve signed
   speed. Controller uses its own clipping and heading wrapping; report boundary
   semantics separately. Do not call a multirate controller inherently erroneous.
2. Limits: read the pinned configuration; exercise declared-bound values and the
   controller-only values ±3 m/s² and ±.4 rad/s. Show whether source step rejects,
   clips or integrates them. Preserve differences as measurements. No silent repair.
3. Actor time coordinates: execute the pinned spline interpolation for straight
   constant speed4 m/s, N20, tf=20*.1=2 s, and constant-headaway fallback. Record all
   generated timestamps, stored speeds, positions and finite-difference speeds when
   indexed every .25 s. Exercise the low-speed tf/N resampling expression with a
   documented linear synthetic sampler whose time channel is exact; do not infer
   which sampler produced any historical live trajectory.
4. Actor dispatch/indexing: execute the retained planner dispatch through its state
   update, excluding renderer/ground placement; run real AttackPlanner.update with
   a single deterministic synthetic candidate generator. Calls at t=0,.25,...,5.0,
   ATTACK_FREQ10. Record passed dt, attacked-state forecast times, candidate horizon,
   reset/pointer advance and replan times. Explicitly include t0 reset behavior.
   Rendering, map queries and historical actor-candidate identity stay unobserved.
5. Independent check: standard-library scalar/Fraction implementation, no NumPy,
   Torch or primary numerical helpers, reconstructs every ego transition and actor
   clock relation from raw fixture rows. Max absolute ego residual <=1e-9 (state
   scalar units), tensor/sampling residual <=1e-6. No tolerance widening after data.

A shared exact-transition claim is contradicted if any registered matched-interval
fixture differs by >1e-9. A same-time actor comparison claim is contradicted if
forecast and candidate sample times differ by >1e-6. A declared-control enforcement
claim is contradicted if any outside-declaration fixture integrates unchanged.
These are counterexamples to named contracts, not error rates over physical driving.

Use invalid / MODEL_CONTRACT_INVALID for changed or malformed inputs, extraction
failure, unexpected execution error or independent disagreement. Use contradicted /
COMMON_MODEL_CONTRACT_REJECTED if the source probes agree with independent arithmetic
and any of the three contract claims is contradicted; otherwise supported /
SOURCE_CONTRACT_FIXTURES_MATCHED for these fixtures only. Broader physical validation
always remains unestablished. No inference about causes of past collision outcomes.

## Known-bads and reporting

Before the real diagnostic, tests must expose an altered time step, old/new velocity
ordering, mismatched actor time channel, altered control, missing/duplicate/nonfinite
rows, changed bound file, symlink input and corrupted report. Use synthetic inputs
for these checks. Retain test streams and failure/correction records. Commit tested
implementation before diagnostic execution; commit raw outputs before interpretation.
Then run the separate validator, retaining both outputs and all fixture rows.

## Finite study design artifact

Construct the union of the two bound historical scenario hash inventories, rejecting
conflicting hashes and malformed names. Preserve all rows, SHA-256s, scene IDs,
tiers and exposure labels. Exclude scene0411 from future action search because its
comparison is closed; keep its rows visible. Assign all other rows to development;
these historically inspected cases cannot be called an untouched holdout. A bounded
pilot proposal selects every row from the first three remaining scene IDs in lexical
order, without consulting outcome values. Keep all other eligible rows in reserve.
Count scenarios and base scenes separately. Asset availability is unobserved locally.

Produce a proposed finite follow-on protocol with complete-route outcomes, live actor
feedback, explicit action and deadline contracts, useful-action witnesses, harmful
intervention checks, missingness, scene clustering and separate genuinely unexposed
validation. A prototype may not claim a finished live protocol while required model
qualification or source/asset bindings remain unresolved. No new live run, selective
case replacement, pulse/strength/clock sweep on the closed case, or publication of a
state-of-the-art/physical safety claim belongs to Iter143.
