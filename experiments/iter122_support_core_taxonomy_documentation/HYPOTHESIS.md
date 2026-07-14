# Iteration 122 - support-core two-track taxonomy documentation integration

Frozen after iteration 121 was published and pushed, but before any iteration-122 documentation
edits, verifier, result, handoff update, or claim. This is a documentation-integration iteration
over the committed iteration-121 synthesis and the existing report/manuscript surfaces. It reads no
raw decision logs, launches no GPU work, reruns no actor-match classifier, and changes no code under
test.

## Process disclosure

This is not blind. Iteration 121 closed the support-core line into one report-level taxonomy:
`8/8` rows preserve a two-track split between a support-side object that does not survive as
supported at first fire and a selected fire-side object that is never supported before collision.
The README and NEXT_PHASE already expose the result, but the technical report and manuscript still
predate the HUGSIM support-core mechanism line.

Those are documentation facts only. The bars below freeze the integration scope and claim boundary.

## Documentation question

Can the committed support-core taxonomy be integrated into the durable research narrative without
overstating it as repair, actor-causality, safety, deployment, production, or benchmark evidence?

## Frozen inputs

- Iteration 121 result:
  `experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md`
- Iteration 121 report:
  `experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/support_core_two_track_synthesis_report.json`
- Technical report:
  `docs/REPORT.md`
- Manuscript source of record:
  `docs/paper/MANUSCRIPT.md`

The verifier may read only committed markdown/json files in the repository. It may not read raw
decision logs, raw `eval.json`, live GPU state, raw box paths, uncommitted files, or any
noncommitted simulator artifact.

## Frozen integration rules

1. Create a dedicated mechanism note under `docs/research/` that:
   - names the support-core two-track taxonomy;
   - links iteration 121 and the prerequisite iterations 112-120;
   - states the exact row count (`8/8`) and the two-track split;
   - states the claim boundary.
2. Update `docs/REPORT.md` with a concise HUGSIM external-validity/mechanism paragraph that:
   - distinguishes the HUGSIM transfer null from NeuroNCAP benchmark evidence;
   - summarizes the support-core two-track split;
   - links the dedicated mechanism note and iteration 121;
   - says the taxonomy is descriptive and not repair, actor-causality, safety, deployment, or
     benchmark evidence.
3. Update `docs/paper/MANUSCRIPT.md` with the same bounded claim at manuscript level:
   - no new headline benchmark claim;
   - no safety/deployment claim from HUGSIM;
   - explicit support-core two-track wording and link to the mechanism note.
4. Add a verifier under the iteration-122 experiment directory that checks:
   - the mechanism note exists and links iteration 121 plus iterations 112-120;
   - `docs/REPORT.md` links the mechanism note and iteration 121;
   - `docs/paper/MANUSCRIPT.md` links the mechanism note and iteration 121;
   - all three docs contain the required claim-boundary phrase.

## Frozen bars

- `SUPPORT_CORE_TAXONOMY_DOCUMENTATION_INFRA_NULL`: any required input is missing; the mechanism
  note is missing; either report surface lacks the mechanism-note link or iteration-121 link; any
  required claim-boundary phrase is absent; docs guard fails; or the verifier cannot run.
- `SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE`: infrastructure passes, all required documentation
  surfaces contain the bounded support-core taxonomy integration, and the verifier plus repository
  gates pass.

## Required proof artifacts

- verifier source plus unit tests;
- `proof-docs/support_core_taxonomy_documentation_report.json`;
- `proof-docs/support_core_taxonomy_documentation.md`;
- `proof-docs/verify_support_core_taxonomy_docs.command.txt`;
- dedicated mechanism note under `docs/research/`;
- updates to `docs/REPORT.md` and `docs/paper/MANUSCRIPT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add documentation edits, verifier, and tests; run targeted verifier/tests and
   `python3 scripts/validate_docs.py`.
3. Run the verifier once over the committed documentation surfaces.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness,
benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. The integration is documentation of a
descriptive committed-report taxonomy only.
