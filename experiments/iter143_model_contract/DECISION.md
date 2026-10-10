# Decision after Iter143

Iter143 is complete: source-level counterexamples reject the three named common
contract assumptions. The independent checker passed. No new live recovery result
exists; Iter139 and Iter142 remain null on their registered action comparisons.

## Next implementation

Build a separate versioned trajectory adapter whose values carry explicit sample
timestamps, coordinate frame, units and control semantics. Keep legacy source and
results unchanged. The first executable target is to make actor candidate generation,
ego forecasts, cost evaluation and environment consumption agree about time.

Use source-derived fixtures for both spline and low-speed branches, enforce monotone
finite timestamps, compare at common times, and reject out-of-support queries. Require
stored-speed/displacement consistency on exact constant-speed cases, a clear initial
state at reset, and finite replan/pointer behavior. Retain known-bads for a dropped or
shifted time channel, wrong units, unsupported extrapolation, stale plan and reset
advancement. A standalone adapter pass is followed by a bounded integration test;
neither alone qualifies physical fidelity.

A bare dt change is insufficient: the spline and low-speed branches use different
endpoint conventions. Define the shared grid first (for example N=20 timestamps
0,.25,...,4.75), then generate or resample candidates onto those explicit times and
check both branches. This is a proposed new regime, not a repair retroactively
applied to old outcomes. Changing dynamics can change benchmark difficulty, so report
old/new regime identities separately and never attribute that change to information.

For ego control, explicitly align the prediction transition or bound the chosen
approximation, and enforce the declared admissible policy consistently. Do not claim
an approximate multirate model is invalid merely because it differs numerically.
Keep real-time scheduling and behavior on late results as a separate qualification.

## Subsequent driving study

After those executable checks, bind actual scenario/configuration/model assets and
preregister the [finite case-family design](CASE_FAMILY_PROTOCOL.md) with a measured
resource ceiling. The proposed 14 scenarios span 3 historical base scenes, not a fresh
holdout. Detect helpful and harmful interventions across the same frozen population.
Proceed to information ablation only after a reproducible useful action opportunity
is demonstrated; keep independent scene/fault validation separate.

No new pulse/strength/clock search on closed scene 0411, no claim that a finite action
library proves unavoidability, and no escalation from source consistency to physical
safety or state of the art. The next step is authorized engineering work, with its
claims limited by retained measurements.
