# Stopping and waiting pass; longer turning remains unqualified

**Status: contradicted** for the preregistered claim that the two-step connector
completes all twelve tasks. Independent admission succeeds. All twelve constructive
witnesses pass. The one-step connector completes **8/12** tasks; two-step lookahead
completes **10/12**. Both miss the eight-frame left and right turns. No source
comparison was run, and the independent RRT remains unqualified.

| Task family | Cases | One step | Two steps |
|---|---:|---:|---:|
| Stop, then hold | 4 | 4 | 4 |
| Sustained wait | 2 | 2 | 2 |
| Wait, then restart | 2 | 2 | 2 |
| Two-frame turn | 2 | 0 | 2 |
| Eight-frame turn | 2 | 0 | 0 |
| Total | 12 | 8 | 10 |

The new proposal library preserves the old controls and adds bounded braking to
zero. Independent arithmetic checks all fourteen frozen speeds; six expose an
immediate exact stop missing from the legacy choices. This repairs a local control
omission. It does not establish that the legacy library could never stop through
a longer sequence, explain the previous RRT failures, or establish source recovery.

The comparison changes only lookahead, under the same 8,192-transition/30-second
cap per case. Every run reaches its terminal frame; none exhausts a resource cap.
One step uses **908 transitions**, two steps **6,899**. The extra two completions
therefore require substantially more work in this schedule. Equal caps are not
equal realized cost, and these exposed deterministic cases establish no statistical
or general performance superiority.

The two-step eight-frame misses overshoot forward position by **0.757461 m**, end
**1 m/s below target speed**, and miss heading by **0.030521 rad** in magnitude.
The frozen tolerances are 0.02 m, 0.01 m/s and 0.002 rad respectively. Their paths remain
physically admissible under the model; they fail the terminal task. Neither an
early position match nor partial turning is accepted as completion.

Independent admission reconstructs **213 states and full masks** across witnesses
and selected paths: **206,184 scalar point-state classifications**. It also checks
motion, physical/task constraints, temporal parentage, selected-leaf ranking and
accounting across all **7,807 attempted transitions**. Unselected background labels
remain producer evidence; they are not included in the scalar-mask claim.
The fixed cloud has 968 constructed points. These are model qualification cases,
not measured road evidence or a real-vehicle safety result.

The producer takes 5.050 seconds; admission takes 6.605 seconds. External supervisors
confirm successful exits and reaping. One initialized execution, no retries, no
native driving, no provider use or spending. Preflight: 74 passed, 2 optional native
bridge tests skipped in the ambient environment. Full publication checks are
observed separately after the closure commit.

Source: `b7e0e2a7bcbac0042873449adad7e6312100f70f`.
Raw committed before admission: `84cda131b58d2dd9ac40225a6cbf9cf204551551`.
[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[protocol](PROTOCOL.md) · [decision](DECISION.md).
