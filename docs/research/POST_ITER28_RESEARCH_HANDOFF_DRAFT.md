# Post-iter28 research handoff draft

Status: planning-only draft. This is not a pre-registration and authorizes no extraction, model
run, probe fitting, activation patching, selector scoring, closed-loop evaluation, GPU run, or
claim beyond the committed iter28 result.

## Purpose

After iteration 28 completes, the next research session should inherit a complete, audited account
of the official nuScenes trainval staging state and convert it into a fresh pre-registration for
the next real-data Sentinel experiment. The next session must not treat data availability as a
research result. It must first prove that the staged root passes the bounded inventory gate, then
freeze the exact research question, splits, bars, falsifiers, and proof artifacts before running
any model-side work.

The audience assumption is severe external technical scrutiny. The handoff must read like a
professional research-control document: concise, reproducible, falsifiable, and free of hidden
tuning paths or victory language.

## Non-negotiable standard

- Read `CONTINUITY.md` first, then run `python3 scripts/make_handoff.py`.
- Use only committed evidence and redacted proofs. Never depend on memory, chat claims, or
  uncommitted source material.
- Keep CI green before and after changes: `ruff check .`, `pytest -q`, and
  `python3 scripts/validate_docs.py`.
- Commit every state change with a narrow message: tooling, proof, docs, and handoff updates stay
  separate when they represent different evidence states.
- Publish nulls at full weight. A failed data gate, count floor, join, probe, intervention, or
  safety bar is a result, not a delay.
- No closed-loop run, selector claim, causal claim, or deployment language may appear until a
  fresh pre-registration authorizes that exact surface.
- Do not handle or print private credentials, cookies, bearer tokens, or signed query material.
  Official download URLs may be used through uncommitted temp files only, and committed artifacts
  must be redacted.

## Iter28 completion requirements

Before any successor research is launched, the repo must show:

- proof JSON for `v1.0-trainval_meta.tgz`;
- proof JSON for every blob part `01` through `10`;
- all proof files committed and pushed;
- local completed archives deleted only after their remote proof commits are pushed;
- official archives extracted only into `/datasets/nuscenes-full`;
- bounded availability inventory run for `/datasets/nuscenes-full` only;
- iter28 `RESULT.md` published with pass/null language exactly bounded by the hypothesis;
- `HANDOFF.md`, `README.md`, and any status ledgers updated without overclaiming.

## Successor launch packet

If and only if iter28 passes its availability bars, the next session should prepare a fresh
pre-registration for the next real-data experiment. The launch packet should include:

- research question: the single claim being tested, not a bundle of adjacent claims;
- data source: `/datasets/nuscenes-full` only, with the committed iter28 inventory artifact named;
- split discipline: frozen scene manifest, known-data firewall, deterministic split rule, and
  no iteration-12 tuning surface;
- minimum positive-count rules before any model/probe/intervention scoring;
- numeric offline bars with named falsifiers;
- proof artifact plan: exact commands, hashes, row counts, join counts, negative controls, and
  failed-grid evidence where applicable;
- stop condition: what failure ends the run before GPU escalation or closed-loop evaluation;
- claim boundary: exact language allowed on pass and exact null language required on fail.

## Candidate next research shape

The most mature next step is not a broad “run everything” pass. It is a narrow, staged real-data
gate that uses the newly staged trainval support to rebuild the fresh risk-support atlas under a
frozen split, then decides whether a causal-localization or planner-repair experiment is justified.

Recommended first successor shape:

- Stage A: inventory-derived fresh atlas manifest over `/datasets/nuscenes-full`.
- Stage B: count-floor and join-validity gate before any representation or intervention work.
- Stage C: only if A/B pass, pre-register a narrow model-side test with one claim, one tensor
  family, low-capacity controls, and a frozen intervention grid.
- Stage D: only if the offline gate passes, consider a separate closed-loop pre-registration.

## Handoff tone

The next handoff should be confident because the evidence chain is real, but disciplined because
confidence without falsifiers is not research. It should show human-in-the-loop maturity by naming
operator corrections, process improvements, and blocked paths factually, without sarcasm or blame.
