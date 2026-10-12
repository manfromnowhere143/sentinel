# Sentinel presentation review — 12 October 2026

Daniel requested a refinement of the existing README in his voice, a current account of the
research, and diagrams that explain the complete system. This is an editorial task. It changes
no experiment, source threshold, historical verdict, raw record or research protocol.

## Why the landing page was stale

GitHub's default branch is `master`. Before this update it pointed to
`8c118b74c699bf0f139f9bd659192bad06b895f8`, whose README opened with a long chronology through
Iter134 and treated Iter135 as the next program. Later research and presentation updates were
published on separate branches. The latest research head was
`4d2998ef8d1c6df8facabb271af49569154259d8`, through Iter155; the protected local README still
stopped at Iter148. Branch publication and the user-facing landing page had drifted apart.

The correction refines the existing research README, synchronizes the local presentation, and
publishes the README and architecture on the default branch as documentation. Later research
links on that branch use exact published commit identities. It does not merge experimental
code, amend MISSION_STATE.json, accept an Iter135 receipt or change the old publication lineage.
The accepted code snapshot remains identifiable by its original commit. A later documentation
commit is not a new scientific acceptance of that snapshot or the research branch.

## Editorial decisions

The complete local and research READMEs were read before editing. Their substantive difference
was the later Iter149–155 work and the resulting next task. The current Reiyah and Nisayon
introductions were inspected as style references only; no sibling content or evidence was
imported and neither repository was changed.

The opening now identifies the project, the implemented capability and the wider scientific
question. The implemented monitor and the criteria for useful intervention precede the findings.
Detailed results, corrections, execution history and the full experiment index remain visible.
Dated repository status follows the explanation and reproduction guidance. This is a refinement
of the existing research narrative, not a shortened replacement or an archive-only account.

The voice is direct about measured results and candid about their scope. Confidence comes from
specific observations and methods. The text does not claim institutional endorsement, novelty,
industrial superiority, physical safety, commercial value or a demonstrated information benefit.
The benchmark gain, increased frontal collisions, progress null, placebo ambiguity, transfer nulls,
interrupted studies and later maneuver failure remain together in the account.

## Corrections and evidence

| Presentation issue | Correction and retained basis |
|---|---|
| Default page stops at Iter134/135; local page at Iter148. | Current presentation covers Iter155 and names the separate historical code/mission snapshot. |
| Opening makes the reader traverse a long research chronology. | Purpose and implemented system come first; all detailed result sections and index rows remain. |
| Research diagram ends at Iter148. | Extend it through the completed pulse comparison, model candidate, native failure and background witness. |
| Iter154 paragraph says background replay has not occurred. | State that this was the limit at Iter154 closure and that Iter155 subsequently replayed the two historical frames. |
| Architecture calls corrected cloud retention unobserved. | Identify the seven new pairs subsequently completed by Iter152. |
| Reproduction guide calls Iter148's decision current. | Point to Iter155's next decision and label the earlier replay qualification historical. |
| Model restoration could be confused with simulator construction. | State that the source model loader ran; driving-environment initialization and stepping did not. |

Headline measurements were checked against the linked retained records:

- [Power run](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/experiments/full14_power/RESULT.md): 799/800 episodes; score difference
  +0.783 [+0.605, +0.928]; safe-progress −0.032 [−0.127, +0.065]; frontal collision increase.
- [Placebo study](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md):
  primary +0.3683 [−0.1901, +0.8866]; 859/1,205 realized placebo brake frames.
- [Iter152](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/experiments/iter152_recovery_continuation/RESULT.md): fourteen new episodes,
  1,420 new actions, neither pulse recovers; benign completion 34.0 s versus monitor 47.0 s.
- [Iter154](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/experiments/iter154_full_scene_maneuver/RESULT.md): both exact-maneuver
  replicas fail on native background collision at 3.25 s, after thirteen actions each.
- [Iter155 admission](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/experiments/iter155_background_witness/proof/admission.json):
  1,345,702 pre-selection points, 276,519 selected points; native/scalar counts 0 and 273;
  zero mask disagreements at both retained poses; physical occupancy and information benefit null.

The measured-results section and all experiment-index rows from the research parent are retained.
No result-bearing experiment is omitted. Historical scope statements in frozen RESULT files
remain historical; this presentation explains later developments rather than altering those records.

## Diagram review

| Diagram | Decision |
|---|---|
| README: released monitor | Preserve the correct component/decision flow; add an accessible description and introduce CPA/TTC in prose. |
| README: research progression | Update the stale Iter148 endpoint through Iter155, with calibration marked proposed. |
| README: next scientific test | Add the decision sequence from calibration to recovery, decision window, information ablation and new scenes; all steps labelled proposed. |
| Architecture: NeuroNCAP | Preserve the correct historical runtime/evaluation flow; add accessibility text. |
| Architecture: HUGSIM monitor/pulse loop | Preserve the implemented flow and identify its Iter152 scope; distinguish it from privileged direct controls. |
| Architecture: execution and admission | Update observation reconciliation, host deadline, raw-before-replay and resource closure through Iter152. |
| Architecture: model/native/witness path | Add the separate Iter153–155 diagnostic path, including native and scalar checks and the failed maneuver. |

The two additional diagrams explain missing relationships; no existing explanatory diagram was
removed. Historical experiment diagrams are preserved as records of their original regimes.
Seven current diagrams are rendered in both light and dark themes, within the existing 1,100
character source budget. Local render and layout records accompany this review. Local visual
inspection checks labels, edges and clipping; it does not certify GitHub's live visual renderer.

## Validation and publication scope

The two advertised CPU examples were rerun successfully. This documentation edit does not rerun
closed experiments, the simulator, provider jobs or the scientific regression suite. Source and
retained evidence preservation, full index coverage, links, anchors and rendered diagrams are
checked separately. Both original presentation versions are retained beside this review.

An interim documentation check encountered the not-yet-created review link. The completed review
resolves it; the intermediate output remains recorded. The existing mission-state and exact
publication-contract findings are retained and reported after the editorial commit. No guard,
workflow, lock, source or historical contract is weakened to produce a green result.

The local README's immutable flag and deny-delete ACL are restored after its authorized update.
The root Git index, branch and unrelated work are preserved. New commits use Daniel's configured
author and committer identity, with complete commit messages inspected. Default-branch publication
is a normal documentation-only successor; remote readback checks the served bytes. Detailed
validation and publication observations are retained separately so that a local check, a push,
scientific acceptance and a hosted CI result remain distinct.

[Content and link checks](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/docs/editorial/2026-10-12/validation.json) · [Local renders](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/docs/editorial/2026-10-12/diagram_render_results.json) ·
[Visual review](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/docs/editorial/2026-10-12/visual_review.json) · [Command observations](https://github.com/manfromnowhere143/sentinel/blob/57d8e42434cd44fb78f91bdace8171614b40d40c/docs/editorial/2026-10-12/command_observations.json).
