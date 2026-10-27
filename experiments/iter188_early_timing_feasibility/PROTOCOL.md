# Iter188 — prospective early-endpoint timing-feasibility audit

27 October 2026. Parent 0490e766a2833ad8d59ee85f4d07335a4fee7146.
This is a diagnostic audit of already exposed development evidence. It adds no
independent scenes, integrated search, simulator driving or planner change.

## Population and hypothesis

Freeze POPULATION.json before computing any new bound. Include every Iter187
native root and every registered primary/extra endpoint across bend_left,
bend_right, chicane_left and chicane_right, without frame or outcome filtering.
Retain exact native node, parent and sequence-token identities. Separately include
every nonterminal state of every admitted completed Iter178, Iter183 and Iter187
path as a false-exclusion control. Preserve duplicate states as distinct records;
do not count them as independent observations. Failed paths are not successful
controls, and their absence from that control group is not a favorable outcome.

The registered scientific question is whether at least one registered endpoint
before frame 24 is necessarily unable to continue through the final checkpoint:
every physically permitted next action already completes the route too early.
Supported requires at least one such exclusion, complete independent admission
and zero excluded successful-transition controls. No exclusions gives null evidence
for this sufficient certificate, not a feasibility or impossibility conclusion.
Missing, ambiguous or unsupported inputs never become an exclusion. Checker
inconsistency, a valid contradictory scalar control or a false exclusion invalidates
the audit. Report all cases, origins, frames, exclusions and unknowns, including the
lost left path's returned endpoint; never attribute the whole search loss causally.

## Necessary certificate and scope

Use the exact source update order: accelerated speed, then position along the old
heading, then heading from updated steering. Enclose every allowed acceleration
and resulting speed with outward binary64 intervals, including source control
tolerances. Capture the actual computed libm cosine/sine coefficients. Bound every
possible next position by a rectangle. A completing route vertex must be strictly
nearer than every noncompleting vertex everywhere in that rectangle, after a
derived numerical comparison margin. Exact rational affine minimization produces
the gap; a separately implemented checker reconstructs the arithmetic enclosure
and evaluates squared-distance differences at all four rectangle corners.

Apply this one-step exclusion only when frame+1 precedes the unchanged last
checkpoint. A bound that does not exclude remains unknown. Ignoring joint steering,
yaw, lateral, collision and road constraints enlarges the reachable set; exclusion
over that superset is necessary. An overlap does not prove a feasible joint control.
Scalar probes must check steering rate/angle, speed, yaw and lateral constraints.
Captured coefficients describe the source program, not ideal sine/cosine or a
physical vehicle. The machine-arithmetic assumptions and error derivation are
frozen in MATHEMATICS.md before acquisition; no formal compiler/libm proof is claimed.

Retained complete-path suffixes provide positive model witnesses only when case,
absolute frame and all state coordinates match exactly. Their prior collision
admission is reused and explicitly identified; this audit makes no new point-cloud
query or collision-certification claim.

## Scalar counterchecks

For each endpoint, probe the Cartesian product of these unique binary64 actions:
acceleration [-A,-2,-1,0,1,2,A,clip(-4*v),clip(4*(6-v))], A=2+1e-12;
steering rate [-R,-pi/24,0,pi/24,R,clip(-4*steering)], R=pi/12+1e-12.
Clips use the corresponding signed action bound. Preserve every probe and its
outcome. This fixed finite probe grid can defeat an exclusion; it cannot prove
infeasibility, collision freedom, a full continuation or controller performance.
Also check every retained successful transition with its actual action. No new
trajectory optimization, sampled search, retry or endpoint-specific tuning.

## Execution and admission

Qualify synthetic controls before freezing the scientific source: positive forced
completion, negative heading, turning, stopped/waiting states, action/speed limits,
joint-control rejection, nearest-site ties, numerical ambiguity, final-checkpoint
boundary, malformed/missing input, altered parent/token/population, altered box,
coefficient, rational gap, comparison margin and false exclusion. Every new gate
must have a known-bad. These controls are independent of the real endpoint bounds.

Freeze implementation, input identities, population, numeric contract and budgets
in PLAN.json/source commit. One exclusive producer acquisition, commit raw before
independent admission, then commit admission and close STATE/RESULT. No raw overwrite
or silent rerun. Producer 300 s; checker 300 s; each process 1 GiB RSS; raw 64 MiB;
minimum 1 GiB free disk. The fixed source envelope may be executed once per stage.
If stopped or invalid, retain the cause and incomplete evidence. Future amendment
must precede any new acquisition and preserve this evidence. No cloud/GPU spending.

## Decision

A supported exclusion may justify a separately frozen planner amendment applying
the necessary rule consistently to primary and extra endpoints, with preserved
witnesses and a fresh unchanged-budget all-four comparison. This audit itself
changes no planner and earns no new integrated qualification credit. Current best
remains 3/4; source comparison stays closed. Unknown states need additional evidence.
