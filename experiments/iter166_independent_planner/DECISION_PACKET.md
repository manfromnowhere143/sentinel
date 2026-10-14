# Qualify an independent search family

The source model is traversable from reset, but exact/24 has a bounded miss from
the actual first-fire history. Retention diagnostics do not distinguish loss of
useful braking states from poor downstream control exploration. Iter165 tests the
first explanation. This experiment tests whether a released tree planner can be
qualified without silently changing the physical question.

Use OMPL 2.0.1 control RRT, release commit
`c509861210a63ec962bbec72c52823abc16b102e`. The tree and nearest-neighbor selection
are upstream; Sentinel supplies dynamics, edge validation, route sampling and a
directed sampler that evaluates its existing control proposals. This is an
independent search algorithm with a custom adapter, not an independent physical
model or an unmodified out-of-box driving planner. No performance theorem is claimed.

A tree retaining accepted nodes avoids another witness-radius or beam-width
pruning rule. SST is an alternative but introduces cost-based witness replacement.
A trajectory optimizer could offer stronger local refinement, but requires a
separate differentiable collision contract and nonconvex initialization study.
Neither method name nor publication recency establishes suitability here.

Before source comparison, run one frozen seed on each of the four fully reflected,
known-feasible Iter161 controls. Preserve the same 18,000 attempted transitions,
120-second search cap and 96-action horizon. Sentinel exact/24 completed 4/4 in
that disclosed experiment; these exposed controls are qualification, not held-out
competition. All four independent RRT paths must complete and pass scalar replay
for source admission. A valid bounded miss contradicts this adapter's qualification
claim; it does not discredit RRT generally or establish Sentinel superiority.

Resources: local CPU; four isolated native processes; 900-second producer and
900-second independent checker; 1 GiB RSS per process; 256 MiB retained output.
No GPU, source-scene search, provider use or spending. Every process is reaped.
Local binary/package hashes and the exact release source excerpts are retained.
The binary is a conda-forge artifact, not a claimed hermetic source build.

Acceptance: clock, stop/restart dynamics, sweep, ambiguity and attempt-cap known-bads;
real native bridge smoke and distance agreement; frozen source/runtime; raw commit
before scalar admission; every selected full mask and required checkpoint checked;
exact rather than approximate goal status. Failed fixtures are retained and are
not tuned away within this study. Source comparison is the next dependency only
if this qualification passes.
