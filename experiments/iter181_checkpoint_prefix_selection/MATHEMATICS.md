# A checkpoint preference within the existing valid-prefix domain

Let a directed request start at absolute frame b, with sampled target z, and let
F be the set of distinct existing comparator times divided by dt. Require finite,
nonnegative integer checkpoint frames. Here dt = 1/4 second and F = {16, 32};
derive F from geometry, rather than hard-coding these values or a case identity.
The checker independently uses the corresponding distinct time values.

For a prefix ending at frame f, define C(f;b) = |{u in F : b < u <= f}|.
Only the uninterrupted continuously valid prefix is eligible. Physical motion,
foreground/background collision, route distance, progress at each checkpoint and
premature-completion predicates determine that domain exactly as before. Crossing
a checkpoint does not relax any predicate. A later clear row cannot repair an
earlier rejected row. Already-passed checkpoints contribute zero new crossings.

For a non-complete evaluation choose the eligible index k minimizing the tuple

    (-C(frame[k]; b), d(state[k] with frame[k], z), k).

If none is eligible return index zero. Interrupted evaluations always return zero.
A fully valid world-completing evaluation returns its completion prefix. Across
evaluations with an eligible prefix choose the tuple

    (not world_complete, -C(frame[k]; b), d(endpoint, z), evaluation_id, k).

The distance remains the Euclidean norm of coordinate differences weighted by
(1, 1, 2, 1/2, 2, 1/100), with heading difference reduced by remainder modulo 2 pi.
Original floating arithmetic, deterministic index ties and full-completion priority
are preserved. When every candidate has C = 0 this is exactly the old selection
rule. More checkpoints are preferred without estimating a future viability value.

The new preference does not alter proposal order, controls, evaluated trajectories,
cache keys, validity, objective residuals or stopping within a fixed request.
It can alter returned endpoints, hence later native requests, proposal values and
total work in the integrated tree. A valid checkpoint endpoint can still lack a
later admissible continuation. No completeness, optimality or guaranteed gain
follows from the lexicographic preference.

Independent replay reconstructs every eligible domain before applying its own
selection arithmetic. Descriptive old-rule choices use the same candidate-generated
records and do not establish the outcomes of a different tree. Only the admitted
four-case outcome decides qualification. No confidence intervals treat related
requests as independent cases.
