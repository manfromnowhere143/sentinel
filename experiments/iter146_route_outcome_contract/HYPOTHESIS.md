# Iter146 route outcome contract

2026-10-10. Status: proposed local engineering qualification. Parent is local candidate
dd91e417d43c6a4874d0c7c482f6fade9ea4061d. No new live episode or cloud start is registered.

Implement a separate finite 401-action runner over the unchanged Iter145 controller and
simulator adapter. Retain all four arms, signed one-second brake pulses, seed 144, one
reset, typed deliveries, actor timing, stopping and missingness. Measure complete loop
wall time including observation hashing and event serialization separately from optimizer,
exchange and environment time. Never treat simulator time as wall-clock time.

Qualify with retained-source CPU fixtures with explicit substitutions (constructed assets,
CPU transfer, small deterministic render, synthetic model/monitor and SAT foreground
geometry). Include full 401-action censoring, both pulse boundaries, completion/collision
coincidence, off-route, truncated, invalid source/clock/transport, and wall/resource stops.
An independent standard-library checker must replay controls, transitions, deliveries,
route progress, collision records, terminal precedence and outcomes. Corrupted evidence
must fail; missing data must remain missing. Commit qualification source and raw evidence
before separate aggregate analysis. CPU qualification does not establish GPU or driving results.

## Prospective outcome clarification

The retained HUGSIM source computes rc=(nearest route index+1)/(0.9*N) and terminates
at rc>=1. This is simulator-defined completion at approximately 90% of recorded samples,
not literal traversal of the entire recorded route. It may overwrite a collision reward
with +1000 on a simultaneous completion step. Keep simulator dynamics and stopping unchanged.
Retain rc, nearest index, N, nearest distance, literal final-sample observation, foreground
and background collision, source termination/truncation and reward separately. Success
requires the declared simulator completion criterion, no collision or off-route event
anywhere, and no censoring/invalid execution. Reward never supplies the outcome.

This prospectively narrows the proposed Iter143/144 'full-route' wording to the explicit
simulator criterion; it does not relax a measured outcome after evidence. Future witness
labels must say simulator-defined route completion. Literal route-end recovery remains
unestablished. The 14 scenarios/112 slots/three exposed scenes, no initialized retries,
raw-before-analysis/later-arm order and progress-at-hazard rule remain unchanged. A pair
must agree before any recovery witness; successes remain in the harm denominator.

## Output and execution envelope

Local qualification: at most 401 actions and 120 seconds per CPU fixture, no initialized
retry. Keep all failed traces. Runtime file caps: 256 MiB event stream, 4 MiB per event;
case total guard 512 MiB; host output reserve 25 GiB for future cloud work. These are
finite stops, not successful outcomes. Bound trace parsing and reject symlinks, duplicate
JSON keys, nonfinite values and missing fields.

Prospective live client output policy removes only display-image process creation from
an exactly hashed released source. Retain planner input image hashes, model/monitor
outputs, typed deliveries, controls, actor selections, source geometry, events and timings.
Keep constructor PLY for now. Verify the source delta structurally; do not claim unchanged
runtime timing or GPU behavior before qualifying the generated client on the installed host.
Future live source, budget, host cleanup and finite qualification population require a
new committed binding before starting the already-stopped VM. No study admission follows
from this local preparation alone.
