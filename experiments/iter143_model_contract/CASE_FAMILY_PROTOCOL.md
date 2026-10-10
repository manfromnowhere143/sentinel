# Proposed finite case-family study

Status: **proposed; live execution not preregistered**. Current cloud budget: 0.
This design follows the Iter143 source-contract diagnostic. Its inventory is frozen;
new model source, assets, timing contract and a bounded host budget still need binding
before a live protocol can be registered. The agent can do that work autonomously
under Daniel's mission instruction; no human acceptance ceremony is required.

## Purpose and population

Test whether a finite admissible action set contains a repeatable complete-route
recovery that strong responsive comparators fail to achieve, while measuring harmful
interventions on the same inventory. Establish that constructive action opportunity
before asking whether added information can identify it in time.

The retained inventory is 88 scenarios / 18 base scenes. Exclude all 5 scene 0411 rows
from new search, retaining their hashes and exclusion reason. The proposed pilot
has 14 scenarios from the first three eligible scene IDs, independent of outcome
values; the 69 other eligible rows remain development reserve. All are historically
exposed. No member may be labelled an untouched holdout or substituted after seeing
its outcome. Availability, case-family composition and qualification failures are
reported for every row; unavailable assets remain unavailable.

| Scene | Proposed pilot scenarios |
| --- | --- |
| 0013 | scene-0013-easy-00, scene-0013-extreme-00, scene-0013-hard-00, scene-0013-medium-00 |
| 0038 | scene-0038-easy-00, scene-0038-extreme-00, scene-0038-hard-00, scene-0038-medium-00, scene-0038-medium-01 |
| 0041 | scene-0041-easy-00, scene-0041-extreme-00, scene-0041-hard-00, scene-0041-medium-00, scene-0041-medium-01 |

Tier names are source labels, not verified physical difficulty or preassigned
braking-helpful/harmful classes. Measure those classes from paired outcomes and
retain their denominators; do not select the reported sample using them.

## Required model contract before launch

Use a new, named regime; keep the legacy regime and all its evidence immutable.
Specify timestamps for nominal-plan knots, controller prediction, actor generation,
actor costs, simulator application, observation and reset. Compare trajectories at
common times by a declared interpolation rule and forbid unsupported extrapolation.
Verify sampler timestamp monotonicity, spacing and duration; do not discard the time
channel. A dt-argument replacement alone does not reconcile tf/(N-1) with tf/N.

Specify controls, units, steering-angle/rate interpretation, signed-speed semantics
and the intersection of controller and simulator admissible bounds. Any clipping is
part of the named policy and logged before/after; undeclared clipping is invalid.
Either use the tested simulator transition for prediction or predeclare a model
approximation and an error budget with counterexamples. A qualification fixture
must demonstrate stored-speed/displacement consistency and reset without an
unlogged future advance. Physical scope remains separate from software consistency.

## Candidate arms and finite schedule

Subject to that source qualification, freeze these four policies with one fixed
planner/model and two fresh numerical replicas each:

- Responsive nominal planner/controller under the new regime.
- The released monitor with the same responsive planner/controller and new regime.
- Responsive nominal planning with one 1.0-second longitudinal braking action starting
  at simulated time 0.0 s, then return to current nominal planning.
- The same action starting at 2.5 s, then return to current nominal planning.

The proposed braking law is acceleration -min(2,max(v,0)/dt) for nonnegative forward
speed, while using the current nominal steering command within qualified bounds.
Reverse-state behavior must be resolved by the new model contract before this law
can become executable protocol. These two fixed times/actions are development probes,
not learned policies or claims that arbitrary evasive actions have been exhausted.

This is at most 14 × 4 × 2 =112 fresh episodes, with 401 actions per episode maximum.
Group by lexical scenario, nominal pair, monitor pair, early-brake pair, late-brake
pair. No initialized retry, seed search, replacement case or success stopping. Freeze
seeds and double-reset policy explicitly after the reset contract is qualified;
legacy seed 136/0 and double-reset behavior cannot be imported silently. Every raw
packet enters Git before analysis or later-arm admission. An invalid replay stops
later work; unobserved arms remain missing. A completed baseline must not remove its
scenario from the intervention schedule, because that would hide potential harm.

## Outcomes and inference

Record collision, off-route termination, full-route completion, first failure time,
raw progress, censoring, actual controls and monitor proposals for every arm. Useful
recovery requires no collision anywhere, full route completion within 401 actions,
valid action contrast and prefix, and progress at each failing comparator's hazard
time at least its raw progress minus .05. A missing hazard observation remains null
unless successful earlier full-route completion satisfies the declared rule.
A comparator that completes collision-free supplies no recovery opportunity against
it; the same row remains eligible for detecting intervention harm.

For a given scenario, label a constructive recovery witness only when both replicas
of the fixed intervention qualify and both replicas of each failing comparator match.
Report witnesses separately against nominal and monitor, plus their intersection;
never silently select the weaker comparator. Any collision or lost full completion
under intervention when the nominal pair completed safely is observed harm. Report
progress differences and runtime as separate outcomes. Disagreeing replicas invalidate
the paired claim. Horizon/time/resource cutoffs are censored, not successes or zeroes.

This is development enumeration, not a powered population comparison. Report all 14
scenario rows, base-scene counts and invalid/missing/censored counts. Repetitions and
tier variants do not expand the independent-scene denominator. Do not issue a population
p-value or confidence interval from three base scenes. Any later effect estimate
requires a prospectively justified scene-level design, multiplicity rule and enough
independent scenes. Preserve no-witness results; finite-library failure is not physical
unavoidability. A successful simulator action is not automatically implementable by
an observation-limited selector.

## Information and deadline successor

Freeze any selector and exact signal access only after a useful action witness exists.
Compare available-observation signals with specified additions, logging when each
became available and whether the controller could act before opportunity closed.
Privileged actor geometry may diagnose opportunities but cannot be an undeclared
online input. Include the harmful-braking rows and the full original selection ledger.
Reserve genuinely unexposed base scenes/fault families separately; the retained 88-row
pool supplies none. Replicate outside the development family before transfer claims.

Measure solver, adapter, complete call, perception/transport and action application
separately. Numerical-mode replay does not qualify end-to-end latency. Freeze a late
result policy and its deadline experiment before interpreting wall-time behavior as
vehicle operation; no timeout silently selects a favorable command.

## Resource and stopping requirements

No cloud launch is part of this draft. Before registration, an agent must bind source,
assets and hardware, estimate runtime from a separately bounded qualification smoke,
and record total host seconds/cost ceiling, per-episode timeout, storage reserve,
capacity attempts and an owned shutdown timer. If the 112-episode envelope does not
fit that ceiling, revise the whole pilot prospectively and retain this proposal.
Do not start with an unaffordable schedule and then select favorable completed cases.
A resource stop preserves the incomplete schedule and all missingness. Publication
requires retained evidence and applicable validation, not a human ceremony file.
