# Checkpoint preference loses one success and gains none

**Status: contradicted for all-four qualification.** The candidate completes
**2/4**, compared with retained Iter178's **3/4**: zero gains and one lost success,
bend_left. Both chicanes still complete; bend_right still misses. **Source comparison
stays closed.** Preserve this adverse result; it is not a replacement for the
stronger retained baseline or evidence that checkpoint progress is useless.

The only planner change prefers valid prefixes crossing more scheduled checkpoint
times before applying the old target-distance ranking, within and across evaluations.
Full completion retains precedence. Proposal generation, cache, sampler, metric,
motion/scene/progress rules, root tolerance and all budgets remain unchanged.
Each exposed case runs once in a fresh process with its original seed: 18,000
transitions, 120 seconds, 96 actions, 128 transitions/eight steps per connection.
[Protocol](PROTOCOL.md) · [exact preference](MATHEMATICS.md).

| Case | Iter178 | Candidate | Attempts | Calls | Accepted edges | Returned frame | Maximum tree frame |
|---|---|---|---:|---:|---:|---:|---:|
| bend_left | Complete | Miss — lost success | 18,000 | 141 | 92 | 29 | 29 |
| bend_right | Miss | Miss | 17,999 | 142 | 73 | 14 | 31 |
| chicane_left | Complete | Complete | 1,537 | 13 | 13 | 33 | 33 |
| chicane_right | Complete | Complete | 13,191 | 104 | 89 | 35 | 35 |

![Adverse paired qualification](proof/qualification.png)

Total work is **50,727 transitions, 400 directed calls and 267 accepted edges**.
Both misses exhaust their transition/reservation allowance; neither is time-censored.
One remaining transition in bend_right cannot fund the next requested program.
The larger tree clock in bend_right does not establish useful progress: its
frame-31 endpoint has route fraction 0.478469, while the returned best path still
ends at frame 14. Bend_left returns frame 29 at route fraction 0.988836, but cannot
complete under the existing timing rules. Near-completion is not completion.

Independent admission verifies **115 returned-path states / 853,050 point-state
classifications**, complete scalar masks for those paths, every attempted motion,
rejection priority, absolute clocks, proposals, cache/accounting, new selection
arithmetic and native path tokens. Unselected background masks and native tree/RNG
remain producer evidence. A reported accepted endpoint is not an independently
scalar-admitted continuation path unless covered by the returned-path evidence.

On the candidate's own generated records, old-rule and new-rule selection differ
16, 6, 1 and 21 times respectively. The first differences occur at calls 5, 34, 8
and 6. These are fixed-request selection contrasts, not paired later trees.
Bend_left first extends evaluation 6 from frame 14 to frame 16. That original call
5 is absent from Iter178's eventual completed connection chain, so the loss cannot
be attributed merely to truncating a known successful path at that first choice.

Post-admission read-only inspection retains all seven accepted endpoint records at
frame 24 or later in the two missed cases: five left, two right. Four receive no
outgoing request. Bend_left's frame-29 endpoint receives twelve outgoing requests;
all 438 evaluated programs first reject as premature completion. Bend_right's
frame-31 endpoint receives one outgoing request: 125 evaluations first reject on
progress and three on controls. These are observed rejection counts, not proofs
that all continuous controls fail. The other late endpoints need their own
continuation and numerical evidence. [Descriptive records](proof/diagnostic_notes.json).

The trial exposes a limit of the proposed preference: passing one checkpoint can
lead to later states with insufficient progress or an incompatible completion time.
It does not isolate a sole cause of either miss. Selection, later expansion
allocation and bounded local capability remain different mechanisms. No beam swap,
budget increase, retuning or retry follows from this outcome.

One frozen acquisition, raw commit, then separate admission. Producer/checker
supervised walls are **38.332 / 18.763 seconds**; every owned process is reaped.
Runtime identities verify before and after. Fifty-nine new controls and 150
focused checks pass, zero skips; passing software checks do not rehabilitate the
failed qualification. No driving episode, cloud compute, source query or spending.
Useful actual-history intervention, latency, safety, transfer and superiority
remain unestablished.

Frozen source: `129ebac0ad7369b5c8a41e71c8990cfa99d94604`.
Raw committed before admission: `36383c3dd420ab7a8d7efad4c4808c3bae37c09b`.
Admission: `bd59d533032953c83234f95a851fbf7337280868`.
[Independent admission](proof/admission.json) · [execution](proof/search_raw/execution.json) ·
[next decision](DECISION.md).
