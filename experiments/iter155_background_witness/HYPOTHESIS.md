# Iter155: background collision witness and independent replay

11 October 2026. Prospective diagnostic following the exposed Iter154 failure. Test whether the
unchanged source predicate, restored selected scene population and reconstructed boxes reproduce
the historical last-clear (frame12,3.00s) and first-collision (frame13,3.25s) observations.
Four historical replica/frame records bind two unique poses. They are not new driving episodes,
independent scenes, holdouts, or a physical-occupancy validation. No other frames, maneuver search,
policy actions, simulator constructor, rendering, inference client or threshold tuning.

Retain the native pre-filter xyz, semantic feature vectors and opacities; independently recover
argmax/opacity selection and verify every selected point and its order. Retain complete selected
points, two native CUDA masks/counts, float32 boxes and source-returned booleans. No local spatial
pruning. Store arrays in bounded little-endian gzip chunks and a complete hash inventory. Retain
source/asset identities, actual model-loader source and dense ground poses. Check source assets
before and after read-only extraction. Reconstruct boxes with the bound source methods using
historical states, without calling reset or step; check independent yaw geometry and ground-plane
projection against recorded pose/height. Model loading is source-bound, not a separately reproduced
checkpoint-deserializer or reconstruction validation.

Primary checks: full selected population equals276519; source booleans match both historical
replicas; count exceeds100 only at frame13. Independent binary64 scalar projections use strict
open boundaries on retained float32 inputs. Report exact masks/counts and disagreements. Also
report a conservative diagnostic ambiguity band of64*2^-24 times the maximum of1 and the sum
of absolute point/endpoint projection terms per edge (float32-rounded edges). This band is a
numerical sensitivity diagnostic, not a certified forward-error theorem. Retain native TF32 and
matmul settings; report them rather than forcing a different kernel. Exact source/independent
mask agreement supports this finite witness. Disagreements confined to the ambiguity band are
inconclusive for exact arithmetic equivalence; material disagreements contradict the replay
hypothesis. Do not convert invalid, missing, partial, or unobserved evidence into empty counts.
Physical geometry, drivable boundaries, live recovery and information value remain unknown.

Qualify100/101/0/empty counts, strict faces/edges, rotated boxes, ties, opacity boundary, NaN/Inf,
malformed/degenerate boxes, wrong height/filter, point deletion, reordered/missing arrays, corrupt
chunks, extra files and wrong historical bindings. Use the retained source function on CPU as
one fixture and a separately implemented scalar checker; CPU fixtures do not prove CUDA behavior.
Freeze producer/checker and all input identities before provider access. Commit raw before replay.

One original1800s/$1.50 conservative compute envelope at$3/hour on the existing bound L4 VM.
Maximum two start requests: a second only after explicit capacity refusal, two unchanged prior-start
TERMINATED observations, no extraction initialization, and120s delay. The inclusive original
budget includes both requests and the delay. No retry after extraction starts. Use a fresh exclusive
root, local watchdog and host shutdown deadline,420s worker timeout,384MiB collection ceiling,
8MiB raw chunks, existing packages only, no new infrastructure. Stop exact owned start, retain
failures and partial evidence, preserve old roots. One source worker invocation; no recovered
transport reply authorizes a second invocation. Daniel's continuing mission instruction is the
operational authority; no human ceremony is pending.

If supported, the next study adds this missing constraint to a separately registered model and
calibrates against retained native prefixes before a new search. If contradicted/inconclusive,
resolve the measurement discrepancy first. Do not expand this experiment after observing counts.
