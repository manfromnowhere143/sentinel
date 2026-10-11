# README and architecture review — 11 October 2026

This editorial update follows closure of the first Iter148 block and precedes any next
experiment, as Daniel requested. It introduces no experiment, threshold change or new scientific
verdict. The scientific closure and preservation receipt are retained at candidate commit
`3e79f028abd63c365e0b23e3f9a388c238c8498f`.

## What changed

- Replaced the repeated opening chronology with the research question, measured results,
  limitations, implemented monitor, development history, current study and proposed next work.
- Kept a direct index of all result-bearing experiments and the unrun Iter135 protocol.
- Preserved the previous README and original architecture text byte for byte as historical
  snapshots. Original results, protocols, evidence and accepted history are unchanged.
- Rebuilt the current diagrams to describe actual interfaces and distinguish the old
  NeuroNCAP/HUGSIM evaluations from the new execution regime.
- Corrected the verification README's blanket offline-reproduction claim and the v20 script's
  argument requirements. Added a dated current-status pointer to the research direction note.
- Updated the current operational handoff and research-memory pointers after scientific closure.

## Claim review

| Claim in the current README | Source and reading |
|---|---|
| NeuroNCAP score +0.783, interval [+0.605, +0.928] | [Power result](../../../experiments/full14_power/RESULT.md); registered run-index bootstrap, 799/800 episodes. |
| Safe-progress −0.032, interval [−0.127, +0.065] | Same result; neither equivalence nor a progress gain is established. |
| Frontal collision increase and the 0346 regression | Same result; retained alongside the favorable composite score. |
| Release effect +0.246, interval [+0.206, +0.293] | [Iter15](../../../experiments/iter15_latch_release/RESULT.md); earlier six-run comparison against the latched union. |
| Placebo primary +0.3683, interval [−0.1901, +0.8866] | [Iter134](../../../experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md); pair-clustered primary, 859/1,205 realized placebo brake frames. |
| HUGSIM transfer nulls | Iter48 and Iter49 results linked in the README; unchanged parameters, scenario-clustered intervals. |
| Four admitted episodes and 368 verified actions | [Iter148 metrics](../../../experiments/iter148_recovery_study/proof/block_000_attempt_002/metrics.json); incomplete pulse excluded. |
| One incomplete and 107 uninitialized slots; no full comparison | [Aggregate](../../../experiments/iter148_recovery_study/proof/block_000_attempt_002/study_aggregate.json) and [result](../../../experiments/iter148_recovery_study/RESULT.md). |
| Six controller deadline exceedances; all loops over 250 ms | Scoped metrics and retained arm admissions; numerical convergence is separate. |
| Current system uses decoded objects and geometric conditions | Released source and separately implemented monitor replay, linked in the architecture. |

## Wording corrected

The previous README called the monitor introspective without consistently specifying the
interface, described a stop as safe when wrong, elevated candidate-head failures to a
representation limitation, and described a non-significant progress effect as costing
approximately nothing. The current text states the measured interface and narrows those
conclusions. It also names the bootstrap unit rather than treating all confidence intervals
as interchangeable. Extra episodes are not described as a proportional increase in statistical
power, and repeated seeds are not counted as new scenes.

The old architecture described a generic benchmark engine, Maestro orchestration and signed
receipts as though they were implemented. The replacement describes the actual simulator,
controller, worker, observation and evidence paths. Proposed extensions remain labelled proposed.

## Validation and preservation

The [content and preservation audit](validation.json) passed: all 148 result files are linked,
the current relative links and anchors resolve, and all five Mermaid diagrams fit the existing
size limit. Ten local PNGs cover light and dark themes; visual inspection found readable labels
and intact paths. Rendering used Mermaid CLI 11.4.2 with the existing Chrome executable after
the CLI's default bundled browser was unavailable. Hosted GitHub rendering was not observed.
The [command observations](command_observations.json) record successful signal and pooling
reproduction, and the remaining repository guard findings. These checks were performed by the
repository agent under Daniel's instruction; they are not an external scientific review.

The repository-wide documentation guard was already
red before editing: four mission/publication-state findings and thirteen missing README result
links. This edit repairs the missing links. It does not rewrite the canonical mission snapshot,
accepted publication topology or unrelated CI work to make the other findings disappear.

The root README's original immutable flag and deny-delete ACL are preserved after the authorized
write. The root Git index and branch are not changed. Candidate commits use an isolated index
and Daniel's configured identity; the candidate remains local and unpushed. Diagram rendering
and command checks are local; no cloud compute is used for this editorial update.

Historical experiment diagrams and paper figures remain dated evidence of their original
regimes. They are not silently redrawn to suggest that later controller changes existed then.
The five diagrams in the current README and architecture describe the current presentation.

[Previous README](../../history/README_through_iter134.snapshot.txt) ·
[Original architecture](../../history/ARCHITECTURE_original_design.snapshot.txt).
