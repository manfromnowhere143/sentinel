# One pose-aware initial proposal — frozen before integrated execution

Replace only the initial control program in the retained Iter175 forward generator.
The new algebraic guess uses target position and heading as well as speed and
steering; its exact equations and approximation limits are in MATHEMATICS.md.
Retained baseline closure: 20130fd53a35040efa2f48e5019349feaa724233 (2/4 complete).
Parent audit closure: da9d78ff48b632d5f71fd8e2b3832b4a5428254d. No baseline rerun.
The source contract permits only the generator's initial call/import (and its
descriptive docstring) and the adapter's generator import to differ. All scientific
PLAN fields stay unchanged.

Keep cases/order/seeds bend_left/20261014, bend_right/20261015,
chicane_left/20261016 and chicane_right/20261017. Each runs once in a fresh process:
18,000 attempted transitions, 120 seconds, 96 actions, 128 transitions per connection
and eight-step maximum connection horizon. Keep OMPL 2.0.1 and the same native binary,
nearest neighbors, sampler, metric, goal bias, sequence transport, exact-vector
cache, prefix ranking, route/foreground/background/physical rules and absolute
4/8-second checkpoints. The original 81 fixed and subsequent Halton programs keep
their exact indices and order. The new initial program replaces the old one; no
extra proposal is added and no witness, case name or direction label enters it.

The seed fits two sequential scalar endpoint approximations with existing metric
weights, then bounds constant acceleration and steering rate. It calls no motion
propagator, scene query or optimizer. Algebraic coefficient computation remains
inside the existing wall clock. Every subsequent nonlinear propagated transition
is charged, including rejected motion. Reserve a full requested horizon before
evaluation; unused remainders remain unused. Actual scene/physical/checkpoint
admission stays unchanged. The 4,096-request guard is an invalid-execution boundary,
not a bounded scientific miss. Exact completion stops immediately.

Constructed pre-execution controls require improved endpoint cost on mirrored pose
targets and one longitudinal pose target, preserve an adverse exact baseline
connection lost by the approximation, and reject treating any approximate endpoint
as exact. Check one-step lateral timing, rigid coordinates, reflected controls,
independent polynomial reconstruction, bounded speed/steering endpoints, prescribed
phase fallback, all later proposals, expired-clock behavior, full work accounting,
absolute clocks, corrupted parameters and forbidden contract changes. These are
design controls, not holdout planner outcomes. They do not require that every
constructed target be reached by the seed or make a general effectiveness claim.

Primary claim: all four original cases complete with independent admission.
Any valid miss contradicts qualification and keeps source comparison closed.
Invalid execution remains invalid. Report gains and losses against the retained
cases, including loss of either current success. Also retain attempted transitions,
calls, accepted edges, returned/max-tree frames, checkpoints and proposal-family
coverage. These diagnostics cannot replace completion. One seed per exposed case
does not identify population success or a causal decomposition through later trees.
Changing the initial program can change cache hits, used work and later requests;
equal maximum budgets are not equal-used-work or real-time evidence.

Source freeze precedes one schedule; all raw is committed before separate admission.
Reuse the scalar motion/checkpoint/prefix/accounting/native-path checks. Reconstruct
the new seed with independent polynomial coefficients (2e-14 parameter tolerance);
later proposals retain their 2e-15 tolerance. No physical, trajectory, goal or
checkpoint tolerance changes. Full scalar masks cover returned paths. Unselected
background labels and native tree/RNG remain producer evidence.

Keep 900 seconds each for producer/checker, 1 GiB peak RSS, 256 MiB raw output,
2 GiB minimum free disk, 180-second child timeout and 910-second stage process-group
supervision. Verify selected runtime identities before/after execution. No retry
or retuning, new driving episode, source query, provider access or spending.

After this single schedule, close the mechanism regardless of outcome. A pass
permits considering a separately frozen source comparison; a miss requires a new
decision grounded in the observed limitation, not a seed-weight or cap sweep.
No optimality, completeness, source recovery, safety, transfer, real-time or
superiority claim follows. The mission remains useful intervention from actual
histories under sensing, computation and actuation delay against a responsive
comparator. Planner qualification is one dependency.
