# CONTINUITY — operator handoff (any agent: Claude, Codex, human)

**Purpose.** This campaign is operator-portable by design. Everything an incoming operator
needs is in this repository plus the two live surfaces below. Read this file top to bottom
before touching anything. Generate the *dynamic* state snapshot with
`python3 scripts/make_handoff.py` — it assembles current git/experiment/box state
automatically; this file carries the invariants that do not change per shift.

## The standard (non-negotiable, verbatim from 19 iterations of practice)

1. **Pre-register before data.** Every experiment gets a HYPOTHESIS.md with numeric bars and
   named falsifiers, committed BEFORE any run. Bars never move after data.
2. **Nulls publish at full weight.** A failed gate or fired falsifier gets the same RESULT.md
   quality as a win. Six of this campaign's strongest findings are nulls.
3. **Gates are real.** Offline gates decide whether GPU/closed-loop runs happen. Iteration 18
   refused the GPU over one frame at 0.2 m. That refusal is the culture.
4. **Evidence or it didn't happen.** Every result commits raw evidence under proof*/ (logs,
   per-frame decision dumps, run trajectories) sized for git (split >90 MB files into
   `.part-*`). Every number in any doc must regenerate from committed evidence.
5. **Corrections on the record.** If your earlier statement was wrong, retract it explicitly
   in the published doc (see iteration 18's addendum for the pattern).
6. **Commits:** plain factual messages, no trailers, no self-praise ("brilliant",
   "state-of-the-art", "definitive" never appear as self-description). CI must be green on
   every push — it runs ruff + pytest + `scripts/validate_docs.py` (diagram budgets, link
   health, README story completeness).
7. **Memory at every state change** (Claude shifts: the aweb-sentinel file under
   `~/.claude/projects/-Users-danielwahnich-workspace-aweb/memory/`; other operators: update
   THIS file's "shift log" section and the dynamic snapshot instead).

## The baton protocol (one operator at a time — hard rule; PERMANENT, BIDIRECTIONAL)

**Standing rule for every operator (Claude, Codex, or human): stay handoff-ready at all
times.** Commit and push at every state change; keep the shift log below current; never leave
uncommitted state at the end of a work window. Then any interruption — a usage limit, a crash,
a sleep — is automatically a clean handoff in EITHER direction: the incoming operator (whoever
it is) reads this file, runs `python3 scripts/make_handoff.py`, and continues. Handoffs are not
events to prepare; they are a property the repository always has.

- Outgoing: commit and push everything; run `python3 scripts/make_handoff.py > HANDOFF.md`,
  commit it; state in HANDOFF.md whether the GPU box is IDLE or a run is IN FLIGHT (name the
  log + done-marker).
- Incoming: read CONTINUITY.md, then HANDOFF.md, then the newest experiments/*/HYPOTHESIS.md
  and RESULT.md. Never relaunch a running job; never run two GPU jobs (single-tenant box,
  shared container names renderer/model/ncap).

## Operating surfaces

- **Repo:** github.com/manfromnowhere143/sentinel (master). Docs spine: README.md (the story),
  docs/REPORT.md (technical report), docs/CAMPAIGN.md (iteration log), docs/NEXT_PHASE.md
  (decision rules), docs/paper/ (manuscript + compiled PDF + arXiv package).
- **GPU box:** `gcloud compute ssh sentinel-gpu --zone us-west1-a --tunnel-through-iap --quiet
  --command "..."`. Auth tokens lapse ~12 h — ask Daniel to run `gcloud auth login`; NEVER
  handle his credentials. Box is single-tenant; leave it up between runs.
- **Box playbooks (hard-won):** detached runs via
  `sudo bash -c 'setsid nohup bash /tmp/<script>.sh </dev/null >/dev/null 2>&1 &'`, logs to
  `/var/log/sentinel-*.log` with `set -x` + pair markers; verify the patch marker prints and
  the first pair starts before leaving. Reboot WIPES /tmp (re-scp scripts) and drops swapon
  (`swapon /swapfile` — the memory-exhaustion fix; without swap the box HARD-FREEZES on heavy
  pairs: flat CPU + zero disk writes + dead ssh = wedge → check hypervisor metrics via the
  Cloud Monitoring API, then `gcloud compute instances reset`, disk is safe). The compose
  script forwards a fixed `-e` list — new env vars need the sed-variant pattern
  (see experiments/iter19_diversity_head/eval_extract_run.sh).
- **Determinism:** NeuroNCAP episodes replay exactly per run index. Every comparison is
  seed-paired; never pool replays as independent samples (that error was made once, caught by
  audit, and is part of the record).

## Current campaign arc (static facts; dynamic state comes from make_handoff.py)

- Benchmark result (definitive, n=20/pair, 799 episodes): OFF 2.12 (published 1.84 reproduced)
  → released union 2.91, +0.783 CI [+0.605, +0.928]; deployment delta −0.03 CI [−0.13, +0.07].
- Best configuration: the released union (iteration 15). Four challengers refuted (evasions,
  crawl, router, tracker-gate); deployment flip proven achievable (+0.226 CI excl. 0) but
  unclaimed — safety gate failed on one crossing.
- Iteration 19 concluded: the diversity head's offline gate FAILED D1 at 0/37 feasible
  escapes (D3 passed) — the pre-registered falsifier fired; the collapse is located in the
  planner's internal planning representation (experiments/iter19_diversity_head/RESULT.md).
  Surviving variant if pursued: scene-level (BEV) conditioning — new pre-registration
  required. Data discipline unchanged: eval frames are EVAL-ONLY; violation voids results.
- Iteration 20 concluded: the VAD tracker-portability offline gate FAILED before GPU time
  (0/47 raw TTC fires removed, side retention 4/6 below the 90% bar, frontal firing frames
  79 -> 90). The simple association + smoothing tracker is not the VAD transfer repair;
  no VAD closed-loop run is authorized from that hypothesis
  (experiments/iter20_vad_tracker_portability/RESULT.md).
- Iteration 21 concluded: the BEV-conditioned diversity head offline gate FAILED after exact
  evaluation extraction (B0 pass: 311/311 frames, zero plan mismatches). B1 failed at 0/37
  feasible escapes, B2 candidate validity was 574/2488 = 23.1%, B3 benign error was 1.449 m,
  and B4 had no selectable escape. No closed-loop run is authorized from that hypothesis
  (experiments/iter21_bev_diversity_head/RESULT.md).
- Next research packet prepared: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md. It is a
  launch packet only, not a pre-registration; it authorizes no extraction, probe training,
  intervention, GPU run, or closed-loop work. The next operator must write and commit a fresh
  iter22 HYPOTHESIS.md with numeric bars and named falsifiers before data.
- Iter22 planning artifacts now exist under docs/research/: ITER22_HYPOTHESIS_DRAFT.md and
  ITER22_ADVERSARIAL_REVIEW.md. They are planning-only, not pre-registrations. Owner guidance:
  do not promote the broad A0-A8 draft directly; use the adversarial review's tighter Stage
  1-only causal-localization shape before any iteration-12 gate or GPU work.
- Paper: docs/paper/paper.pdf compiled; arXiv account live (Daniel: ezio143); submission
  waits on a cs.RO endorsement (code V76QK4; request sent to William Ljungbergh
  william@recohere.ai on 2026-07-05; fallbacks: Holger Caesar, CATPlan authors). After
  endorsement Daniel resumes at arxiv.org/user; package = docs/paper/sentinel-arxiv-submission.tar.gz.

## Shift log

- 2026-06-30 → 2026-07-06: Claude (Fable 5) — iterations 1–19 (incl. the iter-19 gate null:
  collapse located in the planning representation), verification pass, benchmark + power runs,
  paper draft + figures + arXiv package, this continuity system.
- 2026-07-06 (shift end): Claude (Fable 5) — paper folded through iter 19; HANDOFF.md
  committed; BOX IDLE, no runs in flight; open threads: arXiv endorsement (V76QK4, Ljungbergh
  asked 07-05, escalate to Holger Caesar if silent by 07-07 eve), optional next lines per
  NEXT_PHASE (BEV-conditioning pre-reg; VAD tracker portability).
- 2026-07-06: Codex — iteration 20 VAD tracker-portability line pre-registered and run
  offline only; gate failed (V1 0/47, V2 side 4/6, V3 79 -> 90 frontal frames), null
  published; no GPU run launched; BOX not touched because no open gate authorized it.
- 2026-07-06: Codex — iteration 21 BEV-conditioned diversity head pre-registered and Stage-1
  BEV train extraction launched on sentinel-gpu; run IN FLIGHT if `/var/log/sentinel-bev-extract.log`
  lacks `BEV_EXTRACT_DONE`; expected artifacts under `/opt/sentinel-stack/UniAD/sentinel_bev_extract*`.
- 2026-07-06: Codex — gcloud auth lapsed while iter21 extraction was near the final stretch;
  last verified healthy at 2200 frames with no error markers. Ask Daniel to run `gcloud auth login`,
  then check the log/done marker before any train/eval step; do not relaunch blindly.
- 2026-07-06: Codex — iteration 21 Stage-1 BEV train extraction completed cleanly
  (`FEEDER_DONE frames=2385`, `BEV_EXTRACT_DONE`); proof copied under
  experiments/iter21_bev_diversity_head/proof-extract with the 124 MB BEV gzip split into
  80 MB parts. Next permitted step: train the committed BEV head; no eval/gate run before
  training artifact is committed.
- 2026-07-06: Codex — iteration 21 BEV head training completed cleanly (`BEV_TRAIN_DONE`);
  checkpoint committed under proof-train, K=8/H=6, 5.25M params, best validation WTA 0.795.
  Next permitted step: evaluation-only BEV extraction, then committed gate run.
- 2026-07-06: Codex — iteration 21 evaluation-only BEV extraction launched on sentinel-gpu;
  run IN FLIGHT if `/var/log/sentinel-bev-evalextract.log` lacks
  `E21_BEV_EVAL_EXTRACT_DONE`; patch marker verified and first frontal pair started. Expected
  artifacts under `/opt/sentinel-stack/UniAD/sentinel_bev_evalextract*`; do not relaunch while
  renderer/model/ncap containers are up.
- 2026-07-06: Codex — iteration 21 evaluation-only BEV extraction completed
  (`E21_BEV_EVAL_EXTRACT_DONE`); proof copied under
  experiments/iter21_bev_diversity_head/proof-gate (335 JSONL rows: 24 resets + 311 BEV
  frames; 24 NCAP scores). Optional shadow log was absent and gzip warned on that path; the
  required BEV gzip validated. Next permitted step: commit proof, then run the offline gate
  once from committed artifacts.
- 2026-07-06: Codex — iteration 21 offline gate run once from committed artifacts and FAILED
  (B0 pass; B1 0/37, B2 23.1%, B3 1.449 m, B4 0/0). Null published; no closed-loop run
  authorized from the BEV-conditioned head.
- 2026-07-06: Codex — prepared the causal planner interpretability launch packet under
  docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md for the next session. No data or GPU work
  launched; fresh iter22 pre-registration remains required before any run.
- 2026-07-06: bounded helper session drafted ITER22_HYPOTHESIS_DRAFT.md and
  ITER22_ADVERSARIAL_REVIEW.md under docs/research only; Codex owner review accepted them as
  planning artifacts and recorded that official iter22 should be tightened to Stage 1 before
  promotion. No experiment directory, data extraction, GPU work, commit, or push was done by
  the helper.
- (append one line per shift: dates, operator, what changed, box state at exit)
