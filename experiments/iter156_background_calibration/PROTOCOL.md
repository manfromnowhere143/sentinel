# Iter156: calibrate the missing background constraint

12 October 2026. Proposed procedure; commit this protocol, the input inventory,
producer, independent checker and qualification evidence before evaluating the
retained development population. This is prospective method registration on
already exposed historical outcomes, not a blind or held-out experiment.

Iter153 selected a maneuver without a background constraint. Iter154 executed
that fixed maneuver twice and both replicas failed at 3.25 s. Iter155 retained
and independently reconstructed the complete source point selection and two
native masks: zero enclosed centers at 3.00 s and 273 at 3.25 s. The source
collision rule remains strictly more than 100. Those results and failures are
unchanged.

The engineering question is narrow: can a bounded vectorized query preserve
that source predicate over the complete retained prefix population at a lower
local query cost than the independent scalar implementation? A positive answer
qualifies an offline feasibility component. It establishes neither a useful
maneuver nor a physical occupancy model.

## Fixed population and evidence layers

Use exactly the ten scene-0013-medium-00 traces in STUDY_PLAN.json: two nominal
runs from Iter151; two each of monitor, brake_t0 and brake_t2_5 from Iter152;
and two selected-maneuver runs from Iter154. Evaluate all 300 after-step bindings,
with exact state deduplication yielding 115 unique states. Preserve first-seen
order. Replicas, overlapping prefixes and repeated states are not independent
samples. The complete selected point population has 276,519 centers. Reconstruct
its filter from all 1,345,702 source centers, semantic features and opacities.
No point subsampling, spatial pruning or evidence-dependent state selection.

The older traces record combined collision, not separate background labels.
The 26 Iter154 bindings carry direct background booleans. The 266 older
collision-free bindings imply a false background predicate under the retained
source statement `collision = background or foreground`. The remaining eight
older collision-positive bindings do not identify the background component;
retain it as null. Never promote those eight to positive or negative background
labels. Direct native full masks remain the two distinct Iter155 poses only.
The independently checked point masks at other poses are scalar-source evidence,
not new native CUDA observations.

## Geometry and computation

Retain the source state order, coordinate mapping, first nearest-ground tie,
ground projection, 1.6 x 1.5 x 3.0 m source box, corner order, binary32 vertices
and strict projection inequalities. The vectorized implementation scans all
centers with explicit three-term binary64 additions. Its immutable, hash-bound
population prevents caller mutation from silently changing the scene. It is
ordinary NumPy vectorization, not a new geometric algorithm.

The separately implemented scalar oracle imports neither the producer nor the
candidate query. It verifies all 115 full masks, counts, certainty diagnostics,
state bindings, source identities, ground heights and box vertices. Ground and
vertex comparison tolerances retain 1e-10 and 1e-6 respectively; full masks and
counts require exact agreement. Both implementations retain the Iter155
64 * 2^-24 magnitude diagnostic band. This band is not a certified error bound.
If certain_inside <= 100 < possible_inside, report numerically_ambiguous rather
than clear. The raw strict predicate and diagnostic decision are separate.

## Admission and adverse outcomes

Commit complete producer outputs before scalar admission. The checker verifies
that exact raw commit and the source/plan identities; mutable working-tree
results are not publication evidence. Retain every comparison and mismatch.
Any full-mask or count discrepancy fails accelerated-query qualification.
An observed or logically implied native-label mismatch makes calibration
contradicted. A threshold-straddling diagnostic without a mismatch makes it
inconclusive. Otherwise support only this finite development qualification,
with the eight unknown labels and two-pose native-mask scope explicit.

No alternate threshold, point filter, candidate state or revised arithmetic may
be substituted after results. Failure requires a retained result and a new
prospective amendment, not an overwritten run. The original selected maneuver
must remain rejected at its observed collision; no new maneuver search belongs
to this protocol.

## Resources and measurements

Local CPU only, one producer and one scalar admission. Producer limit 60 s;
checker limit 900 s; outer wall limit 1,200 s, process memory budget 1 GiB and
output budget 8 MiB. Require 100 MiB free for this small local derivative record;
the earlier 15 GiB host-extraction storage envelope is not this procedure.
No provider, GPU, renderer, simulator constructor/reset/step or new driving
cost. Stop on failure and retain partial outputs. No automatic retry.

Record the exact Python, NumPy, OS and host architecture. Measure each complete
query with a monotonic clock and report medians and ranges for the separate
producer/checker processes. This is exploratory local cost, not a controlled
cross-hardware benchmark, end-to-end planner latency or real-time guarantee.
Query speed is secondary to population and predicate agreement.

## What can follow

Only after this qualification can a new protocol register a finite action
library and competent responsive comparator. Preserve foreground constraints,
actuator limits, progress, road evidence, timing and background evidence as
separate dimensions. Useful full-scene recovery, availability at the actual
monitor trigger, information advantage, held-out transfer and physical fidelity
remain open. No performance superiority, state-of-the-art or safety claim is
permitted by this calibration.
