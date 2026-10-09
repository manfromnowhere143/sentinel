# Iteration 139 status

Preregistered. Local implementation and validation are complete; live execution is unobserved.
Read [HYPOTHESIS.md](HYPOTHESIS.md) and [DESIGN_REVIEW.md](DESIGN_REVIEW.md).
The existing host remains stopped as last observed in Iter138; a current provider observation
is required before execution. No Iter139 episode or intervention has run.

The focused suite passed 174 tests, followed by one additional missing/failed-predecessor
known-bad. Initial lint findings are retained; the formatted implementation/test scope passes
Ruff. Validation includes all six pulse onset/duration combinations through the generated driver,
independent original-source controller replay, independent Decimal endpoint/prefix checks,
overshoot success, false prevention and missing-data cases. Exact committed-source validation
and bound-host integration are required before live work.

Candidate branch: `research/iter139-finite-pulse`, descending from the closed Iter138 candidate.
Canonical master and unrelated WIP remain unchanged. Full/frozen/hosted CI is not claimed.
