# Test whether forward proposals produce more useful expansion at matched cost

Evidence: Iter172 completes 0/4 integrated cases, consumes 71,986 transitions and
accepts 24 partial edges. Many endpoints fail necessary reachability bounds and
most trial paths encounter background rejection. This does not isolate a cause.
Iter171's explicit local tasks pass, so replacing the whole planner or enlarging
budgets would obscure the narrower connector question.

Alternatives are new target projection, obstacle-gradient guidance, a larger
budget, or bounded multi-step forward proposals. Choose the last as a controlled
comparison: preserve evaluator, physical constraints and target ranking, change
how candidate control sequences are produced. Preserve the earlier failed
single-step adapter; this candidate covers multi-step reversals and fixed four-phase
samples, rather than relabelling that adapter. Explicitly retain its exposure to
the existing constructive tasks. No novelty or industry-superiority inference.

Milestone: a prospective paired comparison on 80 retained requests plus 14
constructive controls. Same per-request transition allocation and 30-second cap;
same 8,192-transition cap on the constructive tasks. Keep counts, work, timed
checkpoint opportunities and actual elapsed time distinct. Required evidence:
all-control forward qualification and strictly more improved request returns,
without fewer admissible returns or checkpoint crossings. Anything less leaves
the proposed replacement unsupported under this criterion.

Falsification: forward fails a constructive case or the separate request criteria.
This would leave metric, target distribution, obstacle guidance and work allocation
as competing explanations, not prove RRT or the scene impossible. A pass justifies
one new original-four-case integrated qualification; it cannot justify source
comparison or recovery claims. Required resources are retained evidence, installed
CPU SciPy/NumPy, 900 seconds per execution/admission stage and bounded local storage.
No provider or human acceptance ceremony is needed.
