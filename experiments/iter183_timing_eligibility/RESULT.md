# Timing eligibility restores 3/4; the right bend still misses

**All-four qualification is contradicted.** The candidate completes the left bend
and both chicanes. It gains one success with no losses against its Iter181 parent,
and ties Iter178's retained 3/4 with no gains or losses. Source comparison stays
closed. This is a repair of the previous regression, not an improved best outcome.

| Case | Iter178 | Iter181 parent | Iter183 | Attempts | Calls | Returned frame / maximum tree frame |
|---|---|---|---|---:|---:|---|
| Bend left | Complete | Miss | Complete | 11,637 | 92 | 32 / 32 |
| Bend right | Miss | Miss | Miss | 17,999 | 142 | 14 / 29 |
| Chicane left | Complete | Complete | Complete | 1,537 | 13 | 33 / 33 |
| Chicane right | Complete | Complete | Complete | 9,083 | 72 | 32 / 35 |

![Timing eligibility qualification](proof/qualification.png)

Total work is 40,256 transitions, 319 calls and 206 accepted edges. The missed
right case exhausts allocatable transitions; its final unused transition cannot
fund another reserved program. No miss is time-censored. Search walls by case are
7.612, 12.512, 1.702 and 9.524 seconds, inside the unchanged 120-second ceilings.
This is offline constructed-case work, not sensing-to-actuation latency.

Independent admission verifies all attempted motion, proposals, eligibility,
selection, cache identity and accounting. Full scalar masks cover all 115 returned
states / 848,694 point-state classifications. Both certificates are independently
checked for 905 distinct case/state/clock entries, with 539 verified cache hits.
The filter finds a first exclusion in 232 evaluated prefixes and carries 33
inherited exclusions forward. Those are decision-record counts, not independent
states or episodes. Unselected background masks and native tree/RNG remain producer
evidence; the bound certificates use geometry and dynamics, not those masks.

The left repair has a directly matched local witness. Parent and candidate call 91
have the same request and the same 16 physical program evaluations. The parent
chooses evaluation 12 / prefix 6 at frame 29, the admitted premature-completion trap.
The candidate instead retains evaluation 1 / prefix 8 at frame 31; its next connection
completes at frame 32. Both original and candidate returned paths have their own
scalar admissions. The matched-program inventory and a changed-state negative
control are retained in [left-choice notes](proof/left_choice_notes.json).
This is one exposed-case mechanism, not a population guarantee.

The right case's maximum retained endpoint progress remains 0.627326. However,
post-admission inventory identifies **15 recorded-valid, eligible prefix records
across three connections** beyond every retained endpoint's nearest-route index.
Their maximum route fraction is 0.707071. None is on its connection's selected
edge. These additional prefix masks have not yet received full scalar replay;
higher progress alone does not establish an extendable path.

| Connection | Maximal recorded candidate: evaluation / prefix | Frame | Route fraction | Attempts remaining after original connection |
|---:|---|---:|---:|---:|
| 83 | 8 / 7 | 24 | 0.701754 | 7,385 |
| 98 | 8 / 6 | 24 | 0.707071 | 5,465 |
| 110 | 2 / 1 | 14 | 0.632642 | 3,929 |

The only two accepted late endpoints are now frames 28 and 29. One receives one
outgoing request; the other receives none. No recorded uninterrupted valid program
reaches frame 32 in the right case. These descriptive records motivate the next
discarded-progress audit; they are not a new planner result.
[Complete inventory and scope](proof/frontier_notes.json).

Before acquisition, 50 new constructed controls / 166 focused checks passed, zero
skips, with the selected native runtime verified. All 72 applicable states on five
retained successes and four checkpoint witnesses remain eligible; the seven old
audit roots reproduce their three exclusions and four nonexclusions. The fixed
256-input cost profile has cold median 2.992 ms / p95 3.123 ms / maximum 3.194 ms;
warm median 2.792 microseconds. These finite constructed costs do not establish
integrated or real-time performance. Initial comparison-fixture mistakes remain
recorded; no scientific retry occurred.

Preregistration `8456b91b752edfc4f736b9926e9f75b2e3ece316`;
final frozen source `cdab7abcdf49c270884380e31f8f643c5cfb375c`;
raw committed before admission `172cf0f5449e4171c3f9a25bc45d6e6cb7f03bd5`;
admission `c53ac67984fde742a6f16a7451451f55a7913e70`.
Producer/checker supervised walls 39.581 / 32.125 seconds; all processes reaped.
No new driving episode, provider use or spending. Historical evidence and the
canonical dirty root remain preserved.

[Protocol](PROTOCOL.md) · [mathematics](MATHEMATICS.md) ·
[qualification](QUALIFICATION.json) · [independent admission](proof/admission.json) ·
[state](STATE.json) · [next decision](DECISION.md).

Useful actual-history intervention, measured end-to-end delay, responsive-baseline
advantage, safety, transfer and generalization remain unestablished. The unchanged
all-four gate continues to prevent source-comparison claims.
