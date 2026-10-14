# Full-horizon local control qualifies on all twelve constructed tasks

**Status: supported** for the preregistered twelve-task claim. Independent admission
accepts **12/12 completions**, including both eight-frame turns. Every selected
path satisfies the same intermediate physical/task constraints and terminal
clock, position, heading, speed and steering tolerances. All twelve constructive
witnesses pass. No source comparison or RRT solve was run.

| Frozen method | Completed tasks | Attempted transitions |
|---|---:|---:|
| Iter168 two-step connector | 10/12 | 6,899 |
| Iter169 full-horizon shooting | 10/12 | 731 |
| Iter170 default derivative step | 10/12 | 747 |
| Iter171 centered solver coordinates | 12/12 | 2,123 |

![Qualification, terminal errors and full-horizon speed and steering](proof/full_horizon_qualification.png)

The same 8,192-transition/30-second cap applies per case. Each longer turn now
uses **960 transitions**, versus 272 in the preceding unsuccessful run. Across
all cases, 306 full trajectory evaluations and five exact cache hits are retained.
Every numerical-derivative and line-search propagation is charged. Passing takes
more work than the failed shooting variants; the lower total than the two-step
connector is restricted to this exposed deterministic schedule.

The longer-turn terminal errors remain inside the frozen tolerances:

| Absolute error | Left | Right | Allowed |
|---|---:|---:|---:|
| Forward position, m | 0.01090605 | 0.01090612 | 0.02 |
| Lateral position, m | 0.00832671 | 0.00832696 | 0.02 |
| Heading, rad | 0.00158172 | 0.00158170 | 0.002 |
| Speed, m/s | 0.00066132 | 0.00066132 | 0.01 |
| Steering, rad | 0.00165841 | 0.00165841 | 0.002 |

These margins are measured outcomes, not uncertainty or robustness bounds.
The controller receives task targets and geometry, never witness actions. A
hard-admissible trajectory stops the solve immediately; no optimizer convergence
claim is made for those interrupted calls.

The engineering correction is numerical. Iter169's explicit relative derivative
step loses sensitivity near tiny nonzero controls. Iter170's default step alone
does not qualify the turns: its initial trust-region radius remains tiny. Iter171
optimizes increments around the identical physical seed and translates bounds
accordingly. This changes radius initialization and subsequent derivative probe
placement. The result supports that complete coordinate intervention; it does
not isolate the radius as the sole cause of the maneuver improvement.

Independent admission checks all **2,123 attempted transitions** for motion,
physical/task constraints and accounting. It reconstructs **284 states and full
masks** across witnesses, new paths, Iter170 paths and Iter168 two-step paths:
**274,912 scalar point-state classifications**. Unselected background labels remain
producer evidence. Prior Iter169 evidence remains separately admitted and retained.

The producer takes 3.994 seconds; admission takes 7.172 seconds in the recorded
CPU environment. Both supervised processes exit successfully and are reaped.
One initialized schedule, no retries, no native driving, no provider use or spending.
Pinned selected files/versions are checked; a hermetic runtime is not established.

This qualifies local control on twelve exposed constructed cases only. It does
not qualify the integrated RRT, demonstrate source recovery, transfer, road safety,
real-time response or competitive superiority. Source comparison remains closed
until the separate original four-case integration qualification passes.

Source: `035cb62cb86443f5f74631e228ea216b8d4e28a5`.
Raw committed before admission: `04dad93b0509d7b3bdc06a2354e6ddcb237f4678`.
[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[protocol](PROTOCOL.md) · [decision](DECISION.md).
