# Iteration 140 contact and actuation diagnostic

Status: preregistered retrospective development analysis, 2026-10-09. Commit this protocol
and input inventory before implementation or calculation of new contact/actor quantities.
Parent: Iter139 `ed23a8c5596c563e6475be2c190856feb481072b`.

## Decision and prior exposure

Determine whether the six failed zero-plan pulses reflect an execution inconsistency or
delivered slowing followed by foreground contact, and whether the encountered actor responds
to the ego trajectory. Finish with one decision memo selecting a justified new action family,
a new case family, or a specific missing measurement. No live episode, expanded pulse grid,
monitor fitting, cloud launch or claims about untested actions belong to this iteration.

This is analysis of known outcomes: all eight Iter139 episodes collided, all pulses slowed
the ego, and one delayed collision by 0.5 seconds. Their outputs were inspected previously.
The diagnostic is not blinded or confirmatory. Source inspection before this registration found
the retained scenario text in Iter136's host_runtime_1.json, hash-matching Iter139's bound
scenario. It specifies one AttackPlanner, ATTACK_FREQ 10, pred_steps 20. The source plans actors
before ego integration and can use ego-state predictions. Neither source capability nor the
policy name establishes observed actor-path divergence or a physical collision mechanism.

## Fixed population and evidence

Analyze exactly reference_a, reference_b, pulse_0_1, pulse_0_2, pulse_2_1, pulse_2_2,
pulse_4_1, pulse_4_2, using all 206 retained action frames and their before/after states.
Bind every raw episode file, the source/configuration evidence and Iter139's runtime manifest
to their parent-commit bytes in INPUTS.json. Check path, byte count and SHA-256 before analysis;
reject symlinks, missing or changed files. No pickle deserialization is needed. Do not modify
Iter136–139 source, raw data, endpoints or results. A missing or invalid input makes this
diagnostic invalid; retain the reason rather than selecting a replacement input.

## Geometry and agreement rules

The source box layout is [x,y,z,width,length,height,yaw]; in-plane x runs along length at yaw
zero. Contact uses the source's closed 2D polygon intersection and ignores height. Extract only
the pinned create_rectangle and fg_collision_det function ASTs and execute them with NumPy and
Shapely in an isolated, version-recorded local environment. Do not import the simulator or GPU
code. For each before and after state record each actor's intersection, polygon distance and
overlap area; report first positive after-state and compare with the actual collision flags.
Also retain the environment's foreground/background log lines. Without static point clouds,
absence of reconstructed foreground contact cannot establish absence of background collision.

Independently implement rectangle separation with analytic projection of centers and half
extents on both boxes' axes using only the standard library; do not import the primary
geometry implementation, NumPy, Shapely or source-generated rectangle vertices. Let g be the
maximum signed separating-axis gap in meters. g>0 means separated; g<0 means strict overlap;
g=0 is closed-boundary contact. Keep |g|<=1e-9 as numerically ambiguous for live interpretation.
Require exact Boolean agreement away from this band. Never widen the band after data.
Tests cover axis-aligned/rotated geometry, touching corners/edges, containment, tiny gaps,
width/length swaps, translations, malformed boxes and disagreements.

At each terminal contact report actor-center longitudinal/lateral offset in the ego heading
frame and wrapped heading difference. A longitudinal offset below -1e-6 m labels the actor
center behind, above +1e-6 ahead, otherwise level. This is center geometry, not identification
of the first contact face. Report finite-difference center velocities over the last 0.25 s,
relative center velocity and distance-closing rate only when correspondence is justified.
They are discrete kinematic diagnostics, not measured impact velocity, severity or fault.
No continuous collision detection or inference about between-sample contacts is licensed.

## Action and state linkage

For every frame independently reconstruct the pinned integration equations: dt=0.25, wheelbase
Lf+Lr=2.7 m; update speed and steering before translation; use the old heading for translation
and the updated steering/speed for heading change. Check delivered acc/steer_rate against the
logged after-state, speed, steering, planar position and heading. Maximum absolute residual
must be <=1e-9 in the respective scalar units. Report each residual; a mismatch is an execution
or reconstruction inconsistency, not evidence about monitor performance. Validate state
continuity and exact 0.25-second intervals. Ground height is outside this planar audit.

Report time series and summaries for before-pulse, during-pulse and resumed segments: speed,
acceleration, steering rate, position, collision and raw progress. Assigned/realized/changed
plan counts remain distinct. No matching, normalization or causal adjustment on post-treatment
speed, realized braking, actor position or monitor firing. Independent arithmetic recomputes
phase boundaries, terminal offsets, kinematic residuals and final interval velocities.

## Actor identity and response

Establish configuration-to-runtime correspondence from the bound scenario and source. When
exactly one configured persistent planner actor and exactly one logged object box exist in
every state, identify the sole actor as source-inferred agent_0, explicitly distinct from a
logged actor ID or any decoded perception track. Otherwise report correspondence unresolved;
do not manufacture persistent identities from list order or nearest position.

At common timestamps compare every post-action actor-box field against reference_a. Report
exact equality and first difference exceeding absolute 1e-6 (zero relative tolerance), maximum
center displacement and wrapped heading difference. Preserve comparisons limited by each
branch's observed horizon. References must match. Prefix and onset semantics remain those of
Iter139. A post-onset actor change demonstrates that the observed actor path is not fixed
across these interventions; it does not by itself identify a controller-internal causal path.
Combine observed evidence with the source's ego-to-actor dependency without claiming inevitability.
Independent replay must recalculate these comparisons from raw JSON, not primary summaries.

## Verdict and next decision

Use invalid / CONTACT_ACTUATION_INVALID for changed/malformed input, an unexplained geometric
disagreement away from the fixed ambiguity band, state-linkage inconsistency or independent
replay disagreement. Retain all diagnostics and choose a specific repair/measurement next.
Use inconclusive / CONTACT_ACTUATION_INCONCLUSIVE for numerical contact ambiguity, unresolved
actor correspondence, or insufficient provenance to interpret terminal foreground contact.
Use supported / CONTACT_ACTUATION_RECONSTRUCTED only if both geometry implementations agree,
all state checks pass, every terminal actual collision has reconstructed foreground overlap
without earlier post-action overlap, and correspondence is supported. This status refers to
the reconstruction only, not recovery, a new theorem or a population claim.

If reconstruction passes, report whether actor paths were equal or differed; do not require
divergence for success. If delivered slowing leaves contact, select the next investment from
contact geometry and reactive dynamics. A richer action is a proposal until a separately frozen
closed-loop experiment evaluates it. A geometric replay against frozen actor positions is not
a reactive counterfactual. If no justified alternative emerges, choose a bounded new case-family
design rather than an open-ended timing/strength search on this case. Stop this diagnostic at
one decision memo; do not reopen the old support-core taxonomy sequence.

## Execution and limits

Local CPU only; no cloud/API/host observation or launch. Allow an isolated local environment
with pinned NumPy 1.26.4, Shapely 2.0.7, pytest 8.3.5 and Matplotlib 3.9.4; retain install and
environment receipts. These are local diagnostic versions, not a claim to the original host's
GEOS runtime. No scientific threshold or population changes after first new analysis. Test and
commit implementation before running the real corpus. Retain initial failures and explicit
corrections if tooling fails. Independently verify the complete report and produce a standalone
contact/trajectory plot from retained coordinates with equal spatial axes.

These eight dependent trajectories concern one disclosed case. No population interval, online
selection, information value, transferable safety, real-time feasibility, blame, human injury
severity or industrial superiority follows. Iter135 stays deferred; Iter139 stays closed.
