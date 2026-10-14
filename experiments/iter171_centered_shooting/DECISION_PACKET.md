# Preserve the physical problem; remove a numerical coordinate dependency

Iter170 fixes derivative perturbations but still completes 10/12. Its two longer
turns terminate after negligible improvement, without exhausting a resource cap.
Pinned SciPy TRF initializes radius from the starting-coordinate norm, with a unit
fallback only at exact zero. An analytic scalar problem reproduces premature
termination near zero and succeeds when expressed as increments from that same
physical point. This is diagnostic evidence, not maneuver qualification.

Alternatives: round tiny controls to zero, disable cost termination, change solver
or enlarge budgets. A coordinate translation keeps the physical seed and feasible
set unchanged and tests a narrower engineering correction. It also alters numerical
probe placement, so any success supports the complete coordinate intervention,
not a claim isolating radius as its sole causal mechanism.

Milestone and falsifier: all twelve unchanged tasks must complete within the same
hard constraints and budget; one miss falsifies qualification. Use the existing
pinned CPU environment with 300 seconds per producer/checker stage. Source freeze,
raw commit and independent replay precede acceptance. The next dependency remains
four-case RRT integration; no additional source comparison is in this study.
