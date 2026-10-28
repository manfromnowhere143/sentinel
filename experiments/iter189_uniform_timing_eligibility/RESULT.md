# Iter189 — uniform timing eligibility preserves three of four successes

28 October 2026. **The all-four qualification hypothesis is contradicted.**
Applying the admitted early timing rule before both primary and extra selection
preserves exactly Iter187's three completions. The left bend still exhausts its
transition allowance. Correct local exclusions are insufficient to establish a
successful complete search under the declared budget.

| Case | Iter183 | Iter187 | Iter189 | Attempts / 18,000 | Returned frame |
|---|---|---|---|---:|---:|
| Left bend | complete | miss | miss | 17,999 | 25 |
| Right bend | miss | complete | complete | 11,259 | 33 |
| Left chicane | complete | complete | complete | 4,225 | 38 |
| Right chicane | complete | complete | complete | 12,155 | 32 |

Against Iter187: **zero gains, zero lost successes**. Against Iter183: **one gain,
one lost success**. The original cases, seeds, 18,000-transition / 120-second
ceilings, 128-transition connection allowance and eight-step horizon remain fixed.
The left run stops with one transition unused because its next proposal cannot
fit the remaining allowance. It is an admitted bounded miss, not a timeout,
missing observation or proof of infeasibility. Source comparison stays closed.

![Admitted completion outcomes and attempted work](proof/comparison.png)

[Figure data](proof/figure-data.json) bind all three admissions. Wall times are
observations from different executions; equal ceilings do not establish matched
consumed work or a runtime speedup.

## What changed, and what the evidence establishes

The original late-window eligibility scan runs unchanged. Every prefix it leaves
eligible receives the Iter188 necessary one-step check before either branch can
select it. Unknown stays eligible. The cache binds exact state, absolute frame,
geometry, dynamics and rule version. Bounds, cache work and record production
consume the existing wall allowance; an expired result cannot return a branch.
The eligibility calculation issues no additional collision query.

Independent replay checks **45,638 attempted transitions**, exact native ancestry,
primary and extra selection, and **7,512 distinct uniform timing certificates**.
The uniform rule excludes a prefix in **96 left-bend evaluations**, all before
frame 24. These are evaluations, not 96 distinct states or independent cases.
Every registered branch receives scalar collision-mask replay: **239 primaries,
15 extras, 483 distinct registered states and 3,530,538 point-state classifications**.
The three completed cases retain Iter187's exact attempted-work counts and returned
paths. Their wall times differ and do not measure the isolated cost of the rule.

The left tree advances from maximum registered frame **21 to 26**; its returned
path ends at frame 25, at 0.625 m/s. It remains nearly complete in route progress
but has not satisfied the final frame-32 checkpoint. This improves a descriptive
tree statistic without improving the qualification outcome.

The [post-admission inventory](proof/descriptive.json) covers all four cases.
There are 22 registered nodes at frames 24–31. The left case has four: node 62 at
frame 25 receives three requests / 50 evaluations; its deepest valid evaluated
prefix reaches frame 26. Nodes 76, 85 and 90 at frame 26 receive no outgoing request.
Those three states are at 0.125 m/s. No continuation feasibility is inferred from
low speed, late arrival or absence of requests. The inventory is descriptive,
produced after admission by [a separate reporting script](describe.py); it is not
a preregistered causal test. The next audit must test feasible continuation before
attributing the miss to expansion allocation. [Decision](DECISION.md).

## Qualification, chronology and resources

The source froze **831 source/input bindings** at
`0dc73de3ee97ff30d441e130b6af77c07cc51894` before acquisition. The local
[qualification](QUALIFICATION.md) records **274 focused checks, zero skips**, including
63 new controls and actual native execution. Full-repository Ruff and documentation
checks passed. The frozen qualification replay preserved all **nine successful
paths / 300 transitions** and excluded exactly the two known traps among all
255 retained endpoint paths. Two native constructed controls exercise both selectors,
including 48 early exclusions in the timed corridor.

| Stage | Commit | Elapsed | Peak RSS |
|---|---|---:|---:|
| Qualification raw | `54c2d7d6cae43790de07c6927b4d53bae7f21eab` | 21.418 s | 307,757,056 bytes |
| Qualification admission | `bd48bc478e4f0fd1912029961d5f14917a66a48c` | 23.135 s | bounded below 1 GiB |
| Four-case raw | `4ec7f311a48edceaf766eba4c73d04db7b02605e` | 94.131 s | 359,628,800 bytes |
| Scientific admission | `b182e85e5984ac732bf367e6064b9c0c10009773` | 135.461 s | 329,646,080 bytes |

Raw was committed before each separate replay; qualification admission was committed
before the four-case schedule. The sole acquisition per stage completed within its
registered resources. All children exited and were reaped. One initial invocation
supplied an abbreviated source SHA and was rejected by `source_encoding` before
raw initialization or any observation; using the full identity began the sole
qualification acquisition. [Invocation record](proof/preinitialization-rejection.json).
There was no scientific retry, new simulator driving, provider access, GPU use or spend.

Per-case search walls were 23.191, 14.714, 9.951 and 22.022 seconds in the fixed
case order. Recorded uniform-check intervals sum to 32.654 seconds across cases,
inside these charged runs; this is not a paired estimate of incremental overhead.
The observed runtime remains the bound macOS Python 3.14.2 environment. Hosted
software CI and publication have separate exact-source identities.

This is finite evidence on four repeatedly exposed development cases, one seed
each. It establishes neither population performance nor superiority over another
organization or system. Useful actual-history intervention, measured response
delay, information advantage and transfer remain unestablished.

[Protocol](PROTOCOL.md) · [admission](proof/admission.json) · [state](STATE.json) ·
[primary research](RESEARCH.md) · [implementation](eligibility.py) ·
[separate checker](eligibility_check.py).
