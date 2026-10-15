# Shorter connections admit two completions; all-four qualification still fails

**Status: contradicted for all-four qualification.** Independent replay admits
**2/4 completions**, compared with the retained Iter174 result of 1/4. `bend_left`
is gained and `chicane_left` is retained; neither right-hand case completes.
**Source comparison remains closed.** No closed reference schedule was rerun.

Only the connection allowance changes, from 1,024 to 128 attempted transitions.
The four original seeds/cases, eight-step horizon, proposal order, native RRT,
sampler, metric, evaluator, prefix ranking, absolute checkpoints and total caps
remain fixed: 18,000 transitions, 120 seconds and 96 actions per case.
[Frozen protocol](PROTOCOL.md) · [contract](contract.py).

| Case | Retained complete | 128-cap complete | Attempts | Calls | Accepted edges | Returned time | Checkpoints |
|---|---|---|---:|---:|---:|---:|---:|
| bend_left | No | Yes | 11,522 | 91 | 56 | 8.50 s | 2/2 |
| bend_right | No | No | 18,000 | 141 | 72 | 3.50 s | 0/2 |
| chicane_left | Yes | Yes | 1,536 | 13 | 13 | 8.00 s | 2/2 |
| chicane_right | No | No | 17,997 | 142 | 100 | 4.50 s | 1/2 |

![Paired allocation results](proof/qualification.png)

One gain, zero losses. Total attempted work falls from 66,274 to **49,055**, directed
calls rise from 70 to **387**, and accepted connections rise from 42 to **241**.
One final call executes no solve because a full requested rollout cannot fit in
the remaining budget. Both misses exhaust allocatable transitions, at 12.00 and
15.22 search seconds, below the 120-second limit. Early completion changes used
work; this is not an equal-used-work or latency benchmark. One seed per exposed
case supports this finite paired result, not a general success probability.

Independent admission checks every attempted motion, physical/checkpoint rule,
prefix choice, forward proposal, cache/accounting entry and native path binding.
Full scalar masks cover **102 returned states** and **741,972 point-state
classifications**. Unselected background labels and native tree/RNG remain producer
evidence. Both complete paths pass their final checkpoint and route condition.
Approximate paths do not count as complete.

The preregistered coverage diagnostic confirms an important limitation: **none of
324 eight-step connection solves reaches the Halton proposal family**. Halton
work occurs only on one- and two-step solves. Thus shortening connections changes
within-connection coverage as well as later tree opportunities. The admitted
case records retain all three proposal-family counts; do not attribute the gain
solely to breadth or extrapolate to other generators.

## Post-outcome diagnosis

Necessary endpoint bounds exclude 219/387 targets; their solves consume 27,839
transitions. An unreachable endpoint may still guide a useful partial extension,
so these counts do not establish a target-sampler repair. Background collision
is the first reported rejection in 6,512/11,686 evaluated trajectories, using
retained producer labels.

The two misses differ. `bend_right` has no reported valid prefix beyond frame 14,
before the first checkpoint at frame 16. `chicane_right` has accepted endpoints
through frame 25, although its returned path ends at frame 18. Four evaluations
in call 84 report valid eight-step prefixes through frame 32, but selection
shortens each to one or two steps. Their route fractions are only 0.623–0.640;
they are not completions, and longer model time alone is not better recovery.
Full scalar background replay has not been performed on those unselected prefixes.
[Reproducible audit](diagnostics.py) · [counts and input hashes](proof/diagnostics.json).

Both successful cases are left-hand fixtures, but each mirror has a different
registered seed and a different evolving tree. This does not establish a directional
bias or a geometry defect. The full fixture reflections were separately admitted
in Iter161. A matched reflection audit must separate proposal order, cache and
selection effects before attributing the asymmetry or introducing a repair.

One source freeze, one four-case schedule, no retry or retuning. Producer and
checker supervised wall times are 44.179 and 19.072 seconds; all scientific jobs
are reaped. Selected runtime identities pass; this is not a hermeticity claim.
No source query, new driving episode, provider use or spending. Source recovery,
real-time intervention, safety, transfer and superiority remain unknown.

Source: `5701fc64b31ec1ad56f088db82e0b1c3f6da1090`.
Raw committed before admission: `19233bf7c5215000e289d49111d10b5ed0c5e537`.
Admission: `104524a4cd014a5ad5e0adab7b7fa1f535dfb1ad`.
[Independent admission](proof/admission.json) · [execution](proof/search_raw/execution.json) ·
[next decision](DECISION.md).
