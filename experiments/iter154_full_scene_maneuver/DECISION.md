# Next decision: make the missing background constraint replayable

11 October 2026. The selected model maneuver is contradicted as a useful full-scene maneuver:
both admitted replicas terminate on native background collision at 3.25 seconds. Applied controls
and the executed prefix match the fixed model to 4.44e-16; foreground contact and off-route are
false. This is evidence that the reduced model omitted a decisive constraint, not evidence that
no recovery is possible or that the underlying scene point cloud is physically correct.

Do not try the remaining thirteen candidates automatically, fit a new information model, or
adjust the collision threshold to rehabilitate this trajectory. The fixed Iter153 search and
Iter154 experiment remain closed with their original results and exact source identities.

The next bounded task is **background-collision witness extraction and independent replay**,
before another maneuver search. Register it prospectively. Reuse the same bound scene assets,
source and ground geometry, with read-only asset access and no driving-policy trial. Retain the
selected Gaussian-point population, source semantic/opacity filters, ego 3D vertices at the
last non-collision and first collision frames, coordinate/height conventions and exact input
identities. Export only the bounded data needed to reproduce the predicate, with an inventory
showing how that subset was selected; do not silently prune away colliding points.

The source predicate in score_calculator.py returns true for more than 100 selected point centers
inside the ego box. Current receipts retain its boolean, source identity, total point count and
time; they do not retain the actual mask, enclosed count or selected points. A separate scalar
implementation should check the source function on retained inputs, including 100 versus 101 points,
boundary points, rotated boxes, empty/invalid populations and changed filter/height conventions.
Distinguish float precision and boundary disagreements from geometry disagreements. A replayed
source collision does not itself validate the reconstruction against physical occupancy.

If the witness is consistent, add the missing background feasibility constraint to a separately
registered diagnostic model, then compare its predictions with retained successful and failing
native prefixes before spending on a new search. If it is inconsistent, preserve the discrepancy
and fix the measurement contract before interpreting another driving outcome. Drivable-road
boundaries remain a distinct unknown in either case.

Only after a full-scene useful maneuver exists should the research move to information selection.
A maneuver from time zero would still not establish recovery after the monitor's actual decision
time. A later experiment must preserve the nominal prefix, qualify a compatible continuation,
and measure the decision window before attributing gains to another signal. Strong responsive
control and trajectory-repair baselines belong in that design; they must use the same available
information and actuator budget. New scenes and population claims require a separate held-out design.

This next task does not authorize another automatic launch from either closed Iter154 attempt.
A new protocol and resource record can be created under Daniel's continuing mission instruction;
no human ceremony is pending. Read the current state and resource closure before provider access.
