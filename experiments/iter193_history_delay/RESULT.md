# Preserving history and imposing delay does not yield a full continuation

28 October 2026. **Inconclusive:** none of the six registered source-model
conditions yields a complete returned continuation. Four searches are wall-time
censored. The other two stop at the transition-budget reservation boundary.
This is not proof that the states are unrecoverable and does not retract
[Iter192's admitted 4/4 development result](../iter192_integrated_feedback/RESULT.md).

Both recorded replicas agree through the original first fire at **6.25 seconds**.
The earlier 5.75-second origin is a privileged timing probe, not a validated
trigger. Each imposed delay holds the last applied command; it is a declared
counterfactual, not recorded post-intervention driving. Original deadlines remain
**7.75 and 9.00 seconds**, with the original total **401-action horizon**.

| Origin | Imposed delay | Attempts | Search queries | Search seconds | Full worker seconds | Stop | Returned absolute end | Checkpoints reached |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 5.75 s | 0 ms | 8,089 | 6,040 | 120.008 | 121.874 | time budget | 5.75 s | 0/2 |
| 5.75 s | 250 ms | 9,369 | 6,029 | 120.004 | 121.668 | time budget | 6.00 s | 0/2 |
| 5.75 s | 500 ms | 11,737 | 5,487 | 120.029 | 121.769 | time budget | 6.25 s | 0/2 |
| 6.25 s | 0 ms | 12,544 | 5,935 | 120.014 | 121.677 | time budget | 6.25 s | 0/2 |
| 6.25 s | 250 ms | 17,998 | 2,865 | 59.859 | 61.749 | attempt reservation | 9.75 s | 2/2 |
| 6.25 s | 500 ms | 17,996 | 1,701 | 37.513 | 39.298 | attempt reservation | 7.50 s | 0/2 |

At expiry the frozen planner invalidates its returned path; the first four rows
therefore contain only the preserved/delayed prefix. Their end times are not new
recovery progress. The two uncensored misses leave two/four unused transitions,
insufficient for the next requested connector horizon. A partial path is not a
full-route completion. Zero observed checkpoint checks is not two passed checks.

The first-fire / 250 ms condition returns **13 new controls** after the held tick,
ending at frame 39 / **9.75 s**, with progress **0.31860135**. Separate replay
admits that complete joined history and both original checkpoints. It remains
incomplete. The endpoint speed is 0.11377223 m/s, not an exact stopped state.
This partial result cannot establish that imposed delay helps: changed states,
bounded search and censoring confound such an inference.

## What was independently checked

All six prefixes preserve original controls and states through their origin.
The static-scene clock translation, held commands, local native identities,
proposal schedules, every attempted physical predicate, timing eligibility and
primary/extra selections replay. Full scalar masks are checked on every returned
joined path: **172 states / 47,561,268 point-state classifications**. No prefix is
ineligible. Unselected background labels remain producer evidence, as explicitly
registered; this is narrower than Iter192's all-query scalar replay.

Total search work is **77,733 attempted transitions / 28,057 queries**, plus six
delay-state queries and 172 selected-path materialization queries. All costs are
retained; materialization is outside the search clock and inside full worker cost.
Measured searches take **37.513–120.029 seconds**, workers **39.298–121.874 seconds**.
None meets a 250 ms simulation tick. This is an observed offline timing limit on
the retained runtime, not a prediction about an unimplemented optimized system.
Imposed simulation delay does not include or excuse this computation time.

Protocol commit `29aeffb5` precedes qualified source
`0ada2f6a38563cfff01615c3a594239a2c96195e`. Raw
`a3f66a4424a679772705298ae5aaf2337ab4b037` precedes independent admission
`c5bb87b7e8d966750f875b13e381ac4ab651c16e`. All 30 new qualification checks pass,
including native clock translation, rejected prefixes and known-bad history,
controls, masks, clocks and evidence. [Qualification](QUALIFICATION.json).

Producer **614.312 s / 189,792,256 peak RSS bytes**; largest worker RSS
**481,263,616 bytes**; checker **349.974 s / 380,534,784 bytes**. Raw before final
execution receipt is 71,530,216 bytes. One acquisition, no retry. All processes
exit and are reaped. No new driving, native simulator recovery execution, GPU or
provider spending. [Admission](proof/admission.json) ·
[Resource closure](proof/resource_closure.json).

## Diagnosis and next decision

The [post-admission descriptive audit](proof/descriptive.json) reports all
registered nodes and attempted labels. The no-delay first-fire tree contains a
producer-labeled branch reaching frame 63 and progress 0.63986510; deadline expiry
prevents its return. Feedback is invoked 33 times in that condition. The miss is
therefore not explained by an absent feedback dispatch. Neither these counts nor
the number of unrequested nodes establishes a causal allocation failure.

A [separately frozen exploratory branch audit](FRONTIER_AUDIT.md) checks the
furthest retained no-delay first-fire branch. **Native node 44 independently
qualifies through frame 63 / 15.75 s, with progress 0.63986510 and both original
checkpoints passed.** All 64 states / 17,697,216 point-state classifications replay;
maximum background count is 94 under the frozen threshold. The 25 historical
controls are unchanged; the branch adds 38 controls. It remains incomplete.
This is a model-valid partial continuation, not native simulator recovery.

Selection is post hoc and adds no completion or online credit to the primary
six-row result. No new search runs. Source `e4fc1632b17037c3f146775f79d1e3380df171a3`
precedes diagnostic raw `a3e0c55b0f589175517b4e5b4fea75ab01beedae`, which precedes
[separate scalar admission](proof/frontier_admission.json). Six constructed
selection/ancestry/source-binding checks pass. Materialization takes 15.596 s / 64
queries; checker 122.684 s. These additional offline costs are not charged
retrospectively to, or subtracted from, the expired search budget.

The unseen-case efficacy study remains behind the recovery gate. Do not tune these
six conditions or call finite misses negative viability labels. The next bounded
falsification must compare a competent conventional recovery method under the
same history, constraints, information and measured computation, with explicit
complete witnesses versus unknowns. [Decision](DECISION.md) ·
[Comparison and product gate](../../docs/research/SENTINEL_NEXT_COMPARISON_AND_PRODUCT_GATE_2026-10-28.md).
