# Iteration 139 status

Preregistered. Local implementation and validation are complete; bound-host integration passed; live execution is next.
Read [HYPOTHESIS.md](HYPOTHESIS.md) and [DESIGN_REVIEW.md](DESIGN_REVIEW.md).
The existing host is RUNNING after the second registered capacity request, with an owned
shutdown timer. No Iter139 episode or intervention has run. The failed first start and
pre-execution orchestration correction remain retained.

The focused suite passed 174 tests, followed by one additional missing/failed-predecessor
known-bad. Initial lint findings are retained; the formatted implementation/test scope passes
Ruff. Four additional provider-readiness known-bads also pass (179 distinct focused tests total).
Validation includes all six pulse onset/duration combinations through the generated driver,
independent original-source controller replay, independent Decimal endpoint/prefix checks,
overshoot success, false prevention and missing-data cases. Exact committed-source validation and bound-host integration passed. The host fixture verified
12 controller calls, pulse release and raw route-completion overshoot with stub states.
It is not a driving result.

Candidate branch: `research/iter139-finite-pulse`, descending from the closed Iter138 candidate.
Canonical master and unrelated WIP remain unchanged. Full/frozen/hosted CI is not claimed.
