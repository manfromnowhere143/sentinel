# Causal planner interpretability — launch packet for the next Sentinel line

Status: **research launch packet only.** This is not a pre-registration and it does not
authorize data extraction, probe training, intervention runs, GPU work, or closed-loop
evaluation. The next operator must write and commit an
`experiments/iter22_*/HYPOTHESIS.md` with numeric bars and falsifiers before touching data.

## The question

Sentinel has now measured the plan-B failure four ways:

- UniAD command-conditioned candidates collapse under threat: **0/37** dangerous frames contain
  an escape candidate ([iteration 12](../../experiments/iter12_plan_selection/RESULT.md)).
- VAD native modes retain partial diversity but miss the frozen viability bar: **21%**
  escapes, below 30% ([VAD transfer](../../experiments/vad_generalization/RESULT.md)).
- A planning-query diversity head is faithful on benign frames but yields **0/37** feasible
  escapes ([iteration 19](../../experiments/iter19_diversity_head/RESULT.md)).
- A BEV-conditioned diversity head also yields **0/37** feasible escapes and only **23.1%**
  all-candidate validity ([iteration 21](../../experiments/iter21_bev_diversity_head/RESULT.md)).

The next scientific question is not "can we add another decoder?" The sharper question is:

> **Where, causally, does a frozen end-to-end planner lose its feasible alternatives under
> threat?**

The line succeeds only if it separates diagnostic signals from causal mechanisms. A probe that
predicts danger is not enough. The work must test whether an internal representation can be
patched, ablated, or steered in a way that changes candidate diversity, risk, or feasibility
under the same rulers already used by the campaign.

## Why this is worth doing

This line connects Sentinel's strongest evidence to research themes that serious ML labs are
actively investing in: mechanistic interpretability, causal model understanding, multimodal
agents, empirical safety, and evaluation discipline. Public references worth reading before
drafting the hypothesis:

- OpenAI Research: frontier reasoning, multimodal systems, agents, and safety evaluation
  ([openai.com/research](https://openai.com/research/)).
- Anthropic Research: interpretability, alignment, and safety evaluation
  ([anthropic.com/research](https://www.anthropic.com/research)).
- Anthropic circuit tracing and related interpretability work: useful model for separating
  observed features from causal claims
  ([circuit tracing](https://www.anthropic.com/research/tracing-thoughts-language-model)).
- Thinking Machines: emphasis on understandable, customizable, collaborative, multimodal AI
  systems and strong research infrastructure ([thinkingmachines.ai](https://thinkingmachines.ai/)).
- Thinking Machines Tinker: researcher-controlled fine-tuning and empirical iteration as an
  infrastructure thesis ([thinkingmachines.ai/tinker](https://thinkingmachines.ai/tinker/)).

The Sentinel angle is concrete: we have deterministic closed-loop episodes, committed nulls,
known dangerous frames, exact candidate logs, BEV extraction machinery, and a culture that does
not turn a diagnostic correlation into a causal claim.

## The claim ladder

Keep these claim types separate in every doc and RESULT:

| claim type | acceptable evidence | forbidden shortcut |
|---|---|---|
| Descriptive | activations differ between benign and dangerous frames | calling this "understanding" |
| Predictive | heldout probe predicts a frozen label with a committed split | tuning on eval frames |
| Causal | patching/ablation changes planner internals under a frozen intervention protocol | claiming causality from probe weights |
| Deployable | changed outputs pass feasibility and selector bars | accepting invalid trajectory diversity |

The first pre-registration should probably stop at the causal/offline level. Closed-loop only
enters after an offline gate passes and a second closed-loop pre-registration is committed.

## Candidate first experiment: iter22 causal activation atlas

This is a recommended shape, not a frozen hypothesis.

**Purpose.** Locate whether danger, candidate-collapse, and feasibility-relevant information are
represented in frozen UniAD internals before and after the planning bottleneck, and test whether
those representations causally influence candidate diversity.

**Likely tensors to inspect.** Verify exact names against the committed UniAD source and the
iteration-19/21 extraction patches before writing the hypothesis:

- scene-level BEV features around `bev_embed`;
- motion/planning bridge tensors such as `sdc_traj_query` and `sdc_track_query`;
- planning-query features used by iteration 19;
- candidate/output trajectories and command-conditioned planning-head outputs used by iteration 12.

**Labels and rulers.** Use only committed definitions unless the hypothesis freezes a new one:

- dangerous frame: executed-plan closest approach `< 3.5 m`;
- escape candidate: closest approach `> 5.0 m`;
- feasibility: curvature, acceleration, and first-step continuity from iteration 21;
- candidate collapse: command-candidate endpoint spread and feasible-escape count from iteration
  12, reported as descriptive evidence unless explicitly gated.

**Suggested offline bars to consider.** These numbers must be revisited and frozen in
`HYPOTHESIS.md` before any run:

- A0 extraction integrity: exact join to the committed iteration-12 corpus, **311/311** frames,
  zero executed-plan mismatches.
- A1 heldout danger localization: a linear probe on train/disjoint scenes reaches a fixed AUC
  bar on heldout scenes without using iteration-12 dangerous frames for fitting.
- A2 collapse localization: a low-capacity probe distinguishes high-diversity from collapsed
  candidate states on heldout scenes above a frozen AUC/bar.
- A3 causal patch: pre-specified activation patching changes candidate spread or risk in a
  pre-specified direction on a meaningful fraction of dangerous frames.
- A4 physical validity: any candidate counted as improved must pass the iteration-21
  feasibility limits; invalid diversity is a null.
- A5 benign control: the same intervention must not materially degrade benign frames.

Do not include all of these blindly. A strong first hypothesis is better with fewer bars that
answer one causal question than with a broad dashboard that invites post-hoc interpretation.

## Named falsifiers

The first iter22 pre-registration should name falsifiers in this spirit:

- **No localized signal.** Low-capacity probes fail on heldout scenes. The planner may still
  encode something, but this extraction/probe family did not find a stable representation.
- **Diagnostic but not causal.** Probes succeed, but ablation or patching does not change
  candidate diversity, risk, or planner state under the frozen intervention protocol.
- **Causal but unsafe.** Interventions change outputs but only by creating infeasible
  trajectories, reproducing the iteration-19/21 invalid-divergence failure.
- **Causal but brittle.** Effects appear only on the exact evaluation scenes or vanish on
  heldout scenes.
- **Selector mismatch.** Interventions create feasible alternatives that the released-union
  risk score cannot rank ahead of the executed plan.
- **Storage or determinism failure.** Activations cannot be extracted deterministically and
  committed under the proof rules; publish as an infrastructure null.
- **Protocol breach.** Any training, threshold selection, or architecture choice uses the
  iteration-12 evaluation frames before the gate; void the result.

## Engineering plan for the fresh session

1. Read `CONTINUITY.md`, `HANDOFF.md`, this launch packet, and the RESULT docs for iterations
   12, 19, 20, and 21.
2. Inspect the committed UniAD extraction patches and source paths. Do not assume tensor names.
3. Draft `experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md`.
4. Commit the hypothesis before extraction, probe training, or intervention code is run.
5. Build the smallest extraction patch that answers the hypothesis. Commit it and its run script
   before launch.
6. Use train/disjoint or already-committed non-eval artifacts for fitting. Keep iteration-12
   dangerous frames evaluation-only.
7. Run offline gates once from committed artifacts. Publish pass or fail in `RESULT.md`.
8. Only if all offline bars pass, write a separate closed-loop pre-registration.

## What not to do

- Do not start with sparse autoencoders, natural-language explanations, or a large learned
  intervention. Begin with low-capacity probes and simple causal patches.
- Do not call a probe an explanation.
- Do not tune thresholds on the 37 dangerous frames.
- Do not launch a GPU run because the box is idle.
- Do not pursue a new candidate head under another name unless the hypothesis explains why it is
  not a retread of iterations 19 and 21.
- Do not modify the arXiv manuscript/package as part of this line unless explicitly requested;
  the paper package currently reflects the prior campaign state.

## Presentation standard

The public posture is sober:

- "We are testing where the plan-B collapse becomes causal inside a frozen planner."
- "If the signal is only diagnostic, that is the result."
- "If intervention creates invalid trajectories, that is a null."
- "No closed-loop claim exists until an offline gate passes and a second pre-registration is
  committed."

Avoid claims that sound like capability theater. The maturity of this campaign is the record:
pre-registration, exact joins, committed raw evidence, nulls at full weight, and corrections on
the record.

## Fresh-session prompt

Use this to start the execution session:

```text
Continue the SENTINEL research mission in ~/workspace/sentinel. Read CONTINUITY.md top to bottom,
then run python3 scripts/make_handoff.py. Then read
docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md and the RESULT docs for iterations 12, 19, 20,
and 21. Do not extract data, train probes, patch activations, launch GPU work, or run any gate
until you have written and committed a fresh iter22 HYPOTHESIS.md with numeric bars and named
falsifiers. Keep CI green with: ruff check . && pytest -q && python3 scripts/validate_docs.py.
Commit and push every state change, publish nulls at full weight, and stay handoff-ready.
```
