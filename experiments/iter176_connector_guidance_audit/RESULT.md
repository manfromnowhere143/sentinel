# Coverage differences do not establish a planner repair

**Status: contradicted for the all-request reflection-closure property.**
Of 386 executed retained requests, **327** have reflection-closed nominal control
program sets and **59** do not. One unexecuted request remains excluded. This is
an exploratory audit of exposed Iter175 evidence, with no new integrated search.
**Integrated qualification remains 2/4; source comparison stays closed.**

The audit enumerates unchanged proposals in original and reflected coordinates,
charging each uncached program its full requested horizon. It performs no motion
integration, collision query or goal stopping. Its result concerns nominal program
availability; it does not predict a mirrored solver's stopping or evolving tree.
The independent checker reconstructs parameters, signed-zero cache accounting,
transition budgets and exact physical program sets. [Frozen protocol](PROTOCOL.md).

| Retained case | Requests | Reflection closed | Reflection open |
|---|---:|---:|---:|
| bend_left | 91 | 76 | 15 |
| bend_right | 141 | 116 | 25 |
| chicane_left | 13 | 11 | 2 |
| chicane_right | 141 | 124 | 17 |
| **Total** | **386** | **327** | **59** |

![Admitted coverage and partial paths](proof/audit.png)

**317/324 eight-step requests preserve reflected coverage.** Of the seven open
eight-step requests, five reuse their initial program and two have shortened final
outer-budget allowances. Each differs by one missing and one extra physical program.
Cache hits correctly save work; removing them is not a diagnosed repair. Forty-nine
of the 59 open requests have one- or two-step horizons. No charged physical duplicate
caused by signed zero occurs in this retained nominal population. Constructed controls
show that such duplicates can matter elsewhere. [Descriptive grouping](proof/summary.json)
and [its source](report.py) were produced after admission.

## Four discarded continuations pass full scalar replay

The four fixed chicane_right prefixes from call 84 each form an admissible partial
path from reset, passing both absolute checkpoints through frame 32 / 8 seconds.
They share their ancestor calls and much of their trajectory. **None completes.**

| Evaluation | States | Checkpoints | Final route fraction | Complete |
|---|---:|---:|---:|---|
| 2 | 33 | 2/2 | 0.631215 | No |
| 4 | 33 | 2/2 | 0.639862 | No |
| 11 | 33 | 2/2 | 0.622568 | No |
| 12 | 33 | 2/2 | 0.635538 | No |

Independent replay checks every retained action, foreground sweep, physical and
route constraint, timed checkpoint and full background mask: **132 state records**
and **1,054,152 point-state classifications**, including repeated shared history.
Two ambiguous numeric joins per path resolve to the earliest retained accepted
connection as preregistered. This binds reconstructed retained trajectories; it
does not independently certify native tree ancestry. Four overlapping paths from
one case are not four new cases, recoveries or independent successes.

These results close the previously missing scalar-mask evidence. Their 62–64%
route progress does not justify preferring greater simulated time in prefix
ranking. The overall coverage difference also does not establish directional bias:
the original left/right runs use different seeds and trees, and nominal enumeration
does not reproduce actual stopping. The current initial proposal uses target speed
and steering but not target position or heading; subsequent fixed/Halton programs
are also pose-independent. Pose enters selection. That interface motivates a
distinct, constructed-control test, without proving its effectiveness.

One source freeze, one acquisition and one separate admission; no retry or retuning.
Supervised producer/checker wall times are **8.280 / 17.841 seconds** and both process
groups exited and were reaped. Selected runtime identities verify; no hermeticity
claim. No native OMPL invocation, new motion search, driving episode, source query,
provider use or spending. Source recovery, real-time intervention, safety, transfer
and superiority remain unknown.

Source: `4ddee70c6011b3ad412b3da9d5a4e031cbce88cf`.
Raw committed before admission: `203170305ba731de25bb5153e924366d87ece03b`.
Admission: `d32a249812a23da76a9a5dfe1d904594f49affca`.
[Independent admission](proof/admission.json) · [execution](proof/audit_raw/execution.json) ·
[next decision](DECISION.md).
