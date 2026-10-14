# Forward-connected RRT completes one of four original cases

**Status: contradicted for all-four qualification.** Independent replay admits
one completion, **chicane_left**, and three bounded misses under the original
seeds, scene inputs, 18,000-transition/120-second/96-action outer limits and
4/8-second checkpoints. This is an improvement from Iter172's 0/4 in this finite
exposed population. **Source comparison remains closed.**

| Original case | Transitions | Directed calls | Accepted edges | Returned model time | Checkpoints passed | Complete |
|---|---:|---:|---:|---:|---:|---|
| bend_left | 17,999 | 19 | 5 | 2.75 s | 0/2 | No |
| bend_right | 17,994 | 19 | 9 | 3.00 s | 0/2 | No |
| chicane_left | 12,285 | 13 | 13 | 8.00 s | 2/2 | Yes |
| chicane_right | 17,996 | 19 | 15 | 4.25 s | 1/2 | No |

![Forward-connected RRT: work and accepted horizons](proof/qualification.png)

Only the connector changes. The released OMPL 2.0.1 RRT, route-index target
sampler, weighted metric, goal bias, linear nearest neighbors, native sequence
transport, full-rollout evaluator and prefix-ranking rules remain unchanged.
The admitted Iter173 generator supplies the same physical seed, fixed phase
patterns and subsequent four-phase Halton proposals. The inner horizon and
transition cap remain eight steps and 1,024. No case identifiers or witness
actions enter the planner; no stop/wait phase is invented. A byte-level contract
check admits exactly this adapter import/call substitution and the unchanged
runtime. [Frozen protocol](PROTOCOL.md) · [contract](contract.py).

All three misses exhaust the allocatable transition budget. Search times are
9.66–12.12 seconds, well below the 120-second cap. A further full requested
rollout cannot use the final 1, 6 or 4 transitions. The complete path reaches
frame 32 and source-model route fraction 1.00735, with both timed checkpoints
checked. Its six accepted connections expand to 32 physical actions. No local
sampled target completes exactly; local target fitting and route completion have
different contracts. Approximate paths do not count as complete.

There are **66,274 attempted transitions**, **70 directed calls** and **42 accepted
connections**. Three final calls do not execute a solve. The furthest accepted
endpoint equals the returned frame in each case: 11, 12, 32 and 17. Iter172's
shooting integration used 71,986 transitions and accepted 24 connections, with
no case completing or reaching checkpoint one. Early stopping on the new
completion changes actual work; this is not an equal-used-work or timing benchmark.
Each case has one unchanged seed, not an estimate of a success probability.

Independent admission checks every attempted motion, physical predicate, absolute
checkpoint, contiguous prefix, native sequence binding and cache/accounting entry.
It separately reconstructs each forward proposal and requires no optimizer
execution. Full scalar masks cover **76 returned states** and **570,636 point-state
classifications**, including all 33 states of the completed path. Unselected
background labels and native tree/RNG remain producer evidence. Passing those
checks establishes the finite model result; it does not establish road safety,
native driving, source recovery, transfer, real-time operation or superiority.

## Post-outcome diagnosis

The retained descriptive audit finds **48/70** target requests outside necessary
endpoint reachability bounds; 47 executed solves on those targets consume 46,658
transitions. These optimistic bounds ignore obstacles and coupled dynamics. An
unreachable target can still guide useful partial motion, so dropping those
requests is not a demonstrated repair. Background collision is the first rejection
in 8,380 of 15,334 evaluated trajectories, using retained producer labels.

Work allocation is a testable remaining limitation. **31/42** eventual selected
edges are already evaluated within 128 transitions; eleven need later proposals.
There are 35,425 transitions after the eventual selected evaluation and 24,297
transitions in requests returning no edge. These are retrospective counts, not
an online stopping oracle or a removable-work guarantee. Two edges on the completed
path are selected only after 256 and 240 transitions; a smaller inner cap could
lose that success and change every later tree request.

The longest reported valid prefixes in all attempted trajectories reach frames
13, 14, 32 and 18. Thus discarded longer prefixes do not already contain the next
missing checkpoint for any failed case. Some are physically longer than the chosen
prefixes; choosing them would create different future trees, whose outcomes remain
unknown. Their unselected background labels have not received full scalar mask
replay. This observation motivates a controlled allocation test before adopting a
new ranking or a larger total budget. [Audit implementation](diagnostics.py) ·
[counts and raw identities](proof/diagnostics.json).

One source freeze, one four-case schedule, fresh processes and no retry or retuning.
Producer/checker times: 50.447/16.962 seconds; supervised wall times including
launch and exit: 50.557/18.573 seconds. All child/stage processes are reaped.
Selected runtime identities pass before and after execution; hermeticity remains
unestablished. No provider use, spending or new driving episode.

Source: `6d973f02c47fd0d2ac979278f2f378ab37c001df`.
Raw committed before admission: `87dc04072801cd78d0ec4dbe1079ef7783f8d24c`.
[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[next decision](DECISION.md).
