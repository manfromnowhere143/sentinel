# Integrated RRT fails all four original qualification cases

**Status: contradicted.** The integrated released control-RRT completes **0/4**
original cases under the unchanged seeds, 18,000-transition/120-second/96-action
caps and 4/8-second progress checkpoints. Independent admission accepts the four
bounded misses. The planner remains unqualified; no source comparison ran.

| Case | Attempted transitions | Directed calls | Accepted connections | Returned path, seconds | Complete |
|---|---:|---:|---:|---:|---|
| bend_left | 17,999 | 20 | 5 | 2.25 | No |
| bend_right | 17,993 | 20 | 2 | 2.00 | No |
| chicane_left | 17,995 | 22 | 8 | 2.25 | No |
| chicane_right | 17,999 | 22 | 9 | 2.00 | No |

![Attempt budgets and accepted versus returned path horizons](proof/qualification.png)

The native bridge now carries varying physical controls as a recorded sequence
token. Its endpoint, parent and duration expand back into the checked physical
path. The released OMPL 2.0.1 RRT, target sampler, metric, goal bias and nearest
neighbors remain unchanged. Centered shooting supplies at most eight steps per
connection, with at most 1,024 transitions charged inside the outer budget. Only
an initial contiguous admissible prefix can enter the tree. The four cases have
no prescribed stop/wait phases; those controls remain free. The prior explicit
local tasks therefore do not establish that the planner discovers those phases.

There are **71,986 attempted transitions**, **84 directed calls** and **24 accepted
partial connections**. Four final calls cannot reserve their requested horizon;
the 14 unused transitions do not finance another full requested rollout. All four
runs stop on this attempt limit, after 8.54–15.65 seconds of search each. The
120-second limit is not the binding constraint. No accepted connection reaches
the first checkpoint at frame 16; the furthest tree endpoints are frames 9, 8,
15 and 8. The returned approximate paths reach route fractions 0.2711, 0.2392,
0.2205 and 0.2983. Neither approximate status nor a partial path is completion.

Independent replay checks every attempted motion, physical predicate, absolute
checkpoint, prefix choice, request/cache count and native path-token binding.
It reconstructs **38 selected states and full background masks**, with **275,880
scalar point-state classifications**. Unselected background labels and the native
tree/RNG remain producer evidence; no complete independent tree reconstruction
is claimed. Passing replay validates this finite result, not planner competence.

A separately labelled **post-outcome descriptive audit** finds that **62/84**
requests violate at least one necessary endpoint bound; 58 of the 80 executed
solves target such states and consume **50,202 transitions**. Bounds use the same
quarter-second motion, acceleration, speed, steering-rate and yaw-rate limits,
allowing the frozen terminal tolerances. For example, displacement cannot exceed
the sum of maximum admissible next-step speeds times the step duration. These
optimistic bounds ignore obstacles and coupled constraints: passing them is not
proof of reachability. A target outside them can still yield a useful partial
extension, so these counts do not show that skipping such requests would help.

No exact local target completes. Of 9,884 trial trajectories, 8,223 have background
collision as their first rejection in the retained producer labels. The optimizer
fits terminal state and actuator slacks; obstacle clearance is a hard acceptance
check, not a smooth guidance term. These observations motivate testing the expansion
policy and its work allocation. They do not identify a sole cause or prove a repair.
[Reproducible diagnostic](diagnostics.py) · [counts and raw-file identities](proof/diagnostics.json).

One frozen execution per seed, in fresh reaped processes, with no retry or retuning.
The producer stage takes 62.410 seconds; independent admission takes 16.450 seconds.
Supervised wall times including launch/exit are 62.520 and 18.187 seconds. Selected
runtime identities pass before and after execution; hermeticity is not established.
No native driving episode, provider use or spending. Source recovery, transfer,
real-time operation, road safety and competitive superiority remain unknown.

Iter171's 12/12 local qualification remains valid in its narrower scope. This
result does not erase it, and it does not extend it to the integrated planner.
Finite search failure also does not establish physical impossibility.

Source: `f348b1ff6f07dc3eac1e766c44a42cace6b9b1c6`.
Raw committed before admission: `1ffcb7baf12ede9c96c47500f2f7ad10782f7a3f`.
[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[frozen protocol](PROTOCOL.md) · [next decision](DECISION.md).
