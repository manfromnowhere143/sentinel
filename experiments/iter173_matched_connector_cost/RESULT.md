# Forward proposals pass the finite connector comparison

**Status: supported, within the frozen scope.** Forward proposals complete all
14 constructed tasks and improve target distance on 16 of 80 retained requests;
centered shooting completes 12 tasks and improves 15 requests. Both return
admissible motion on the same 24 requests. Neither crosses a timed checkpoint.
This meets the preregistered criterion for a subsequent integrated trial.
**Source comparison remains closed.** The original integrated RRT still has a
retained 0/4 result; this study does not execute a new RRT or qualify those cases.

| Outcome | Centered shooting | Bounded forward proposals |
|---|---:|---:|
| Constructed tasks completed | 12/14 | 14/14 |
| Requests returning admissible motion | 24/80 | 24/80 |
| Requests improving target distance | 15/80 | 16/80 |
| Timed checkpoint crossings | 0 | 0 |
| Request transitions | 71,986 | 79,435 |
| Constructive-task transitions | 18,507 | 845 |
| Total transitions | 90,493 | 80,280 |
| Summed request-call time, seconds | 49.335 | 49.633 |
| Summed constructive-call time, seconds | 4.558 | 0.235 |

![Matched connector outcomes and actual work](proof/comparison.png)

The available budgets match within every pair; actual work does not. Retained
requests preserve their original allocations up to 1,024 transitions and eight
physical steps. Constructive tasks allow 8,192 transitions. Both arms have a new
30-second per-call cap. All 80 forward request runs reach their attempt cap;
shooting reaches it on 70 and returns from optimization on ten. The request-level
improvement therefore is not an equal-used-transition or speedup result. Timings
are one local CPU schedule, not repeated performance measurements or real-time
bounds. Total work combines two populations and must not conceal their difference.

The paired improvement counts are 15 improved by both, one improved only by
forward, and 64 improved by neither. The same 56 requests return no admissible
edge; their distance and route gains remain null. Of the 24 common admissible
returns, forward reduces target distance more on 23, shooting on one. These are
descriptive paired counts, not an inferential test or a population superiority
claim. Distance is the frozen six-state metric, not meters alone; route gain is
the change in route fraction. Negative distance gains remain visible below.

| Available transitions, clipped to original request cap | Shooting admissible / improving | Forward admissible / improving |
|---|---:|---:|
| 128 | 24 / 15 | 24 / 16 |
| 256 | 24 / 15 | 24 / 16 |
| 512 | 24 / 15 | 24 / 16 |
| 1,024 | 24 / 15 | 24 / 16 |

These prespecified checkpoints count only fully evaluated trajectories within the
budget. Equal binary counts do not mean that selected endpoints or gain magnitudes
stop changing. No adaptive stopping rule or reduced-budget integrated policy has
been tested here.

The twelve previous stop, wait, restart and turn tasks pass in both arms. On each
new 16-step detour, shooting exhausts 8,192 transitions without completion; forward
completes the left and right cases in 288 and 272 transitions. Both constructive
witnesses pass full scalar replay; both straight negative controls encounter the
background collision predicate. The new detours use a four-quarter steering
pattern represented by the forward proposal family. This is a disclosed capability
control, not an unbiased effectiveness test. The 80 requests are exposed outputs
of the earlier shooting-driven tree, not independent scenes or a holdout.

Forward evaluates the unchanged physical seed, then a bounded deterministic
family of constant and reversing phase controls, followed by four-phase Halton
proposals. Shooting retains its centered numerical coordinates, derivatives,
residuals and tolerances. Both use the same evaluator, exact physical-vector
cache, hard intermediate checks and return ranking. All predicted transitions
count, including derivative calls and motion after rejection. No witness controls
enter either candidate. Early rejection savings are not tested by this isolation.
[Design and limits](PROTOCOL.md) · [primary-source comparison](RESEARCH.md).

Independent admission checks every attempted motion, physical predicate, absolute
checkpoint, prefix selection and request/cache count, and separately reconstructs
the forward parameter sequence. Full scalar masks cover **668 states** across
selected returns, constructive witnesses and straight negatives: **2,710,158
point-state classifications**. Unselected background labels remain producer
evidence. No native tree or random sequence is replayed because no RRT runs here.

One frozen schedule contains 188 fresh-process executions, alternating arm order
by population index; all children are reaped. Four final Iter172 calls did not
execute a solve and remain explicitly excluded. Producer stage: 175.845 seconds;
scalar admission: 56.476 seconds. Supervised wall times including launch and exit:
176.002 and 58.759 seconds. Runtime selected-file identities pass; hermeticity is
not established. No provider use, spending or new driving episode.

The bounded result justifies testing this candidate inside the original planner.
It does not establish successful integrated expansion, source recovery, transfer,
road safety, a new planning method or superiority over another system.

Source: `d39ab973ec2d97e6fa160fedd2873a53d2ecca00`.
Raw committed before admission: `5886892a76bd7943ca51b495465309e2b7c2f103`.
[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[frozen protocol](PROTOCOL.md) · [next decision](DECISION.md).

## Paired admitted returns

All 24 common admissible requests appear here; the other 56 have null gains in
[the admission record](proof/admission.json). Values are rounded only for display.

| Request | Shooting distance gain | Forward distance gain | Shooting route gain | Forward route gain |
|---|---:|---:|---:|---:|
| bend_left_001 | 1.885910 | 1.913123 | 0.159490 | 0.148857 |
| bend_left_002 | 1.997097 | 6.747302 | 0.106326 | 0.435938 |
| bend_left_012 | -0.203564 | -0.168324 | 0.037214 | 0.037214 |
| bend_left_015 | 0.180057 | 0.223778 | 0.031898 | 0.037214 |
| bend_left_017 | -0.539377 | -0.446855 | 0.031898 | 0.026582 |
| bend_right_001 | 3.540687 | 7.735182 | 0.233918 | 0.377459 |
| bend_right_012 | 0.641863 | 0.710221 | 0.069112 | 0.063796 |
| chicane_left_001 | 3.472210 | 8.699782 | 0.095115 | 0.341548 |
| chicane_left_002 | 3.632175 | 3.631955 | 0.112408 | 0.112408 |
| chicane_left_005 | 1.734114 | 1.845584 | 0.116732 | 0.116732 |
| chicane_left_006 | 0.033329 | 0.073876 | 0.004323 | 0.004323 |
| chicane_left_007 | -0.146804 | -0.131378 | 0.030264 | 0.030264 |
| chicane_left_008 | 2.126559 | 2.191776 | 0.069174 | 0.069174 |
| chicane_left_009 | -0.752678 | -0.752578 | 0.030264 | 0.030264 |
| chicane_left_014 | 0.103494 | 0.197983 | 0.000000 | 0.004323 |
| chicane_right_001 | 5.227531 | 5.645628 | 0.185906 | 0.194553 |
| chicane_right_002 | 2.826995 | 3.691923 | 0.108085 | 0.129702 |
| chicane_right_005 | 0.550024 | 0.584617 | 0.064851 | 0.064851 |
| chicane_right_008 | -1.007833 | -0.989355 | 0.038911 | 0.038911 |
| chicane_right_009 | -0.170008 | -0.165556 | 0.025940 | 0.025940 |
| chicane_right_010 | -0.589393 | -0.564559 | 0.038911 | 0.038911 |
| chicane_right_014 | -0.020245 | 0.021558 | 0.025940 | 0.025940 |
| chicane_right_016 | 0.726355 | 0.774866 | 0.047557 | 0.051881 |
| chicane_right_020 | -0.051905 | -0.035773 | 0.034587 | 0.030264 |
