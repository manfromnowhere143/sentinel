# Proposed finite intervention experiment

**Status: proposed, 2026-10-09. Not a preregistration or an observed intervention result.**
Iteration 138 now supplies a repeatable collision case under its declared numerical controller
and runtime. The next question is: **does a finite, admissible intervention improve collision
and progress outcomes beyond the released responsive baseline on this case?** Establish that
opportunity before spending on new information signals or large scene suites.

## Correct the action and outcome mismatch

Iteration 136 proposed a zero-plan override held from a fixed onset through episode end.
Its [comparator](../iter136_hugsim_recoverability_canary/replay_trace.py) requires a
`route_complete` terminal reason for prevention, as well as the progress bar. A permanent
stop can frustrate that terminal criterion even when temporary braking would help. A failed
permanent-stop grid could therefore reflect a restrictive action library rather than the
absence of a useful recovery opportunity. This is a design limitation, not a theorem that
the controller must stop perfectly or that every such branch must fail.

No Iter136 intervention ran, and its closed protocol is unchanged. The successor should use
finite zero-plan pulses followed by resumption of the same released planner/monitor. This
preserves the actuator family while allowing progress after the hazard. Resumption and the
actor response become measured parts of the intervention.

## Freeze a small development experiment before execution

An initial candidate grid is onset **0, 2 or 4 simulated seconds**, crossed with pulse duration
**1 or 2 seconds**: six cells, all reported. These values are proposed after inspecting this
development case; they cannot support confirmatory generalization. Before any run, freeze the
grid, exact frame-boundary semantics, full episode horizon, progress and intervention-cost
criteria, validation, missingness, stopping rules and resource budget in a new hypothesis.

Require a fresh reference check under the new source contract and exact correspondence of
each intervention branch's entire pre-action prefix, including the first intervention
observation, planner input and controller state. After onset, actor reactions may differ;
that is part of the simulated treatment response. Log both incoming and executed plans,
actual override frames, returned controls, solver receipts and release time. Add known-bads
for off-by-one onset/release, leaked intervention state, premature release, divergence before
onset, missing outcomes and false progress/prevention labels.

Separate three outcome questions explicitly:

1. Was a collision observed through the reference hazard time? A bounded collision-free
   observation is a diagnostic, with its actual horizon reported.
2. Did the complete episode achieve the registered joint collision and useful-progress
   criterion? Report route completion, terminal reason and intervention cost together.
3. Was the branch censored, truncated, off-route, timed out or otherwise invalid? Those
   states cannot become successful prevention. An unreached onset remains unobserved.

Do not relax the full-episode criterion because a pulse fails. Report every cell and distinguish
failure within this finite library from physical inevitability. A positive cell establishes
only an available action in this disclosed case. It does not show that a monitor could select
that action online or that an extra signal has value.

## Keep the ambitious question testable

If a useful intervention exists, compare a frozen additional-information policy with a strong
responsive policy using the same admissible actions, observation timing and resource constraints.
Avoid an information comparison against a clock-only policy that also removes feedback.
Freeze development choices before evaluation on independent scenes, and report joint collision,
progress, intervention burden, missed opportunities and worst-group outcomes.

In parallel with that research sequence, define an actual end-to-end latency requirement and
late-result policy before claiming deployment relevance. Current client roundtrip is much
larger than the controller duration, and simulator time masks both. Optimization must preserve
the chosen numerical/decision contract or explicitly register its change; removing diagnostics
alone cannot erase the observed full-solver overrun. Delay injection and stale-action tests
belong in a separate registered evaluation.

This sequence aims to identify an actionable information deficit with reproducible evidence.
An engineering replay result is a prerequisite for that contribution, and the present result
has not established the contribution itself.
