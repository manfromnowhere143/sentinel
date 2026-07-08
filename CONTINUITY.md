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
- Iteration 22 concluded: the non-evaluation causal-localization Stage 1 stopped at S0
  (experiments/iter22_causal_planner_interpretability/RESULT.md). Baseline extraction completed
  with 1,507 non-reset rows and 1,507 GT rows, but all rows failed the committed timestamp join
  (`missing_gt`) and the frozen heldout split had 0 GT frames. No probe fitting, activation
  direction, intervention replay, iteration-12 scoring, or closed-loop work is authorized from
  that hypothesis. Any successor requires a fresh pre-registration.
- Iteration 23 concluded:
  experiments/iter23_s0_hardened_causal_localization/RESULT.md. It repaired iter22's S0 artifact
  failure: availability passed with 66 eligible scenes, the two-run canary was deterministic, and
  full extraction joined 2,627/2,627 non-reset rows with zero error rows and stable tensor shapes.
  The frozen count-floor gate then FAILED before probes: `collapse_positive` was 0 in every split,
  `eligible_intervention_frame` was 0, and heldout `danger_positive` was 17 below the 30-frame
  floor. No probe fitting, activation direction, intervention replay, iteration-12 scoring, or
  closed-loop run is authorized from iter23. Any successor needs a fresh pre-registration.
- Iteration 24 concluded:
  experiments/iter24_risk_support_atlas/RESULT.md. It was a fresh risk-support atlas, not a causal
  intervention. The known-data firewall ran first and excluded iter22/iter23 scenes plus
  NeuroNCAP / iteration-12 evaluation scenes, but the availability bar FAILED before model
  extraction: 0 eligible fresh scenes, 0 planned keyframes, and 0 heldout keyframes after 582
  post-firewall candidate train scenes all missed the local six-camera file-existence check. No
  canary extraction, full extraction, label atlas, probe fitting, activation direction,
  iteration-12 scoring, selector evaluation, or closed-loop run is authorized from iter24. Any
  successor needs a fresh pre-registration and an explicit data-staging plan before extraction.
- Iteration 25 concluded:
  experiments/iter25_staged_data_inventory/RESULT.md. It was a staged-data provenance gate, not a
  model experiment. The frozen root inventory inspected only five pre-declared roots and applied
  the iter22/iter23/iter24/evaluation firewall. No root passed: `/datasets/nuscenes` existed but
  had 0 eligible fresh scenes, 0 planned keyframes, and 0 heldout keyframes after exclusions; the
  other four frozen roots were missing. No data download/copy, model extraction, label atlas,
  probe fitting, activation direction, iteration-12 scoring, selector evaluation, or closed-loop
  run is authorized from iter25. Any successor needs a fresh pre-registration naming a concrete
  data-staging remedy before extraction.
- Iteration 26 concluded:
  experiments/iter26_data_staging_remedy/RESULT.md. It was a read-only data-staging remedy gate.
  It answered the operator question directly: yes, the missing data is the official nuScenes v1.0
  trainval sensor file blobs, not metadata. The governed sentinel bucket contains metadata/map/CAN
  bus artifacts only. The official blobs total 292.78 GB as archives; the frozen capacity bar
  requires 365.975 GB free; the GPU had only 25.125 GB free. No bytes were downloaded or copied,
  and no model work ran. No data download/copy, extraction, root mutation, inventory rerun, model
  extraction, label atlas, probe fitting, activation direction, iteration-12 scoring, selector
  evaluation, or closed-loop run is authorized from iter26. Any successor needs a fresh
  storage/staging pre-registration.
- Iteration 27 concluded:
  experiments/iter27_storage_provisioning/RESULT.md. It was a storage-provisioning pass only:
  `sentinel-nuscenes-data-1tb`, a 1024 GB `pd-balanced` disk, is mounted at
  `/datasets/nuscenes-full` with 1,026,108,792,832 bytes available. It moved 0 dataset bytes and
  launched 0 Docker/model/NeuroNCAP runs. It authorizes only a later data-staging
  pre-registration, not nuScenes download/copy/extraction, inventory rerun, model extraction,
  label atlas, probe fitting, activation direction, iteration-12 scoring, selector evaluation, or
  closed-loop work.
- Iteration 28 is now pre-registered:
  experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md. It authorizes only official
  nuScenes v1.0 trainval staging into `/datasets/nuscenes-full`: the metadata archive plus ten
  file-blob archives, redacted source provenance, archive byte/SHA evidence, extraction safety
  proof, then a bounded availability inventory for that root. Daniel must perform any
  browser/session authentication or provide signed URLs; the agent must not handle credentials.
  It authorizes no model extraction, label atlas, probe fitting, activation direction,
  iteration-12 scoring, selector evaluation, or closed-loop work.
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
- 2026-07-06: Codex — pre-registered iteration 22 Stage 1 under
  experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md. Scope is non-evaluation
  causal localization at the motion/planning bridge with minimum counts, negative controls, a
  frozen activation-direction grid, and a hard stop before iteration-12 or closed-loop work.
  No data extraction, GPU work, probe fitting, or activation patching launched.
- 2026-07-06: Codex — created the iteration 22 Stage 1 split manifest from the official
  `nuscenes.utils.splits.train` scene list and local nuScenes scene metadata. Committed source
  list, generator, manifest, command record, exclusion report, and SHA256 sidecar under
  experiments/iter22_causal_planner_interpretability/. No extraction, probe fitting, activation
  patching, model container run, or NeuroNCAP run launched.
- 2026-07-06: Codex — aligned README with the active iter22 Stage 1 story and added the committed
  extraction/intervention run surfaces for iter22 (server patch, manifest-driven feeder,
  baseline extraction script, calibration-grid script, heldout-selected-alpha script). This
  authorizes only the next committed extraction step under the iter22 HYPOTHESIS; no extraction,
  probe fitting, activation patching, intervention replay, iteration-12 scoring, or closed-loop
  run launched yet.
- 2026-07-06: Codex — launched iteration 22 Stage 1 baseline extraction on sentinel-gpu from the
  committed non-evaluation split manifest. Run is IN FLIGHT if `/var/log/sentinel-e22-extract.log`
  lacks `E22_STAGE1_EXTRACT_DONE`; patch marker `E22_STAGE1_PATCHED` printed, server became
  alive, feeder matched 90/90 manifest scenes, and the first JSONL rows were writing. Do not
  relaunch while the `model` container is up. No probe fitting, activation intervention replay,
  iteration-12 scoring, or closed-loop run launched.
- 2026-07-06: Codex — investigated GitGuardian's commit `b98cbb5` high-entropy alert. Findings:
  no credentials; alerts came from public nuScenes scene-token metadata in `split_manifest.json`
  plus required SHA evidence strings. Removed unnecessary scene tokens from the generator and
  regenerated the manifest; retained SHA256 evidence sidecars required by protocol. Current
  in-flight extraction is unaffected because the feeder uses scene names only.
- 2026-07-06: Codex — iteration 22 Stage 1 extraction completed cleanly on sentinel-gpu
  (`FEEDER_DONE split=all scenes=90 frames=1507`, `E22_STAGE1_EXTRACT_DONE`); proof copied under
  experiments/iter22_causal_planner_interpretability/proof-extract. The GPU box is IDLE.
- 2026-07-06: Codex — iteration 22 Stage 1 analysis stopped at S0 and published a data-null:
  1,507/1,507 non-reset rows failed the committed timestamp join (`missing_gt`) and heldout GT
  rows were 0. No probes, activation directions, intervention grid, iteration-12 scoring, or
  closed-loop work ran; any successor causal-localization line requires a fresh HYPOTHESIS.md.
- 2026-07-06: Codex — pre-registered iteration 23 under
  experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md. Scope is S0-hardened
  causal localization: availability manifest first, frozen `(scene, sample_index, timestamp_us)`
  join, two-run canary determinism, then full extraction only if canary passes. No manifest,
  extraction code, GPU work, probe fitting, activation direction, iteration-12 scoring, or
  closed-loop work launched yet.
- 2026-07-06: Codex — committed the iter23 availability manifest generator and generated the
  manifest read-only on sentinel-gpu against `/datasets/nuscenes`. Availability gate PASS:
  66 eligible scenes, 39 fit / 13 calibration / 14 heldout, 554 heldout keyframes, no token
  fields in the manifest. No model container, extraction, probe fitting, activation direction,
  iteration-12 scoring, or closed-loop work launched.
- 2026-07-06: Codex — added the iter23 S0 canary/full extraction surface: server patch with
  explicit context endpoint for `(scene, sample_index, timestamp_us)`, manifest-driven feeder,
  two-run canary script, full-extraction script, canonical JSONL hash utility, and S0 analyzer.
  No canary/model run, full extraction, probe fitting, activation direction, iteration-12
  scoring, or closed-loop work launched.
- 2026-07-06: Codex — iteration 23 canary and full extraction completed cleanly, S0 passed, and
  the label/count gate then published a data-null: 2,627/2,627 full joins, zero error rows, stable
  tensor shapes, but collapse positives 0 in all splits, eligible intervention frames 0, and
  heldout danger positives 17/30 below the frozen floor. No probe fitting, activation direction,
  iteration-12 scoring, or closed-loop run is authorized from iter23; BOX IDLE.
- 2026-07-06: Codex — pre-registered iteration 24 under
  experiments/iter24_risk_support_atlas/HYPOTHESIS.md. Scope is a fresh risk-support atlas with a
  known-data firewall excluding iter22/iter23 scenes; a pass would authorize only a later
  pre-registration. No manifest generation, extraction surface, GPU work, probe fitting,
  activation direction, iteration-12 scoring, selector evaluation, or closed-loop run launched.
- 2026-07-06: Codex — added the committed iteration 24 prerequisite surface: manifest generator
  with iter22/iter23 known-data firewall, namespaced server patch, feeder, canary/full extraction
  scripts, S0 analyzer with dtype/candidate/alpha checks, label-atlas analyzer, and canonical
  hashing routine. No manifest generation, model extraction, GPU container, probe fitting,
  activation direction, iteration-12 scoring, selector evaluation, or closed-loop run launched.
- 2026-07-06: Codex — generated the iteration 24 availability manifest on sentinel-gpu as
  metadata/file-existence work only, with committed iter22/iter23 firewall inputs staged under
  `/tmp/iter24_firewall_root`. Availability FAILED before any model extraction: 0 eligible scenes,
  0 planned keyframes, and 0 heldout keyframes after 582 post-firewall candidate train scenes all
  missed local six-camera files. Null published; no canary/full extraction, probe fitting,
  activation direction, iteration-12 scoring, selector evaluation, or closed-loop run authorized.
- 2026-07-06: Codex — pre-registered iteration 25 under
  experiments/iter25_staged_data_inventory/HYPOTHESIS.md. Scope is read-only staged-data inventory
  over a frozen local root list after iter24's availability-null. No inventory script/run, data
  download/copy, model extraction, label atlas, probe fitting, activation direction, iteration-12
  scoring, selector evaluation, or closed-loop work launched yet.
- 2026-07-06: Codex — added the committed iteration 25 inventory surface:
  experiments/iter25_staged_data_inventory/inventory_roots.py plus pure gate tests. The script is
  metadata/file-existence only, token-field guarded, and bounded to the frozen root list. No
  inventory run, data download/copy, model extraction, label atlas, probe fitting, activation
  direction, iteration-12 scoring, selector evaluation, or closed-loop work launched yet.
- 2026-07-06: Codex — ran the single frozen iteration 25 staged-data inventory on sentinel-gpu.
  No Docker containers were running; the inventory inspected only pre-declared roots and returned
  infrastructure-null: `/datasets/nuscenes` existed but had 0 eligible fresh scenes / 0 keyframes
  after the known-data firewall; `/datasets/nuscenes-full`,
  `/opt/sentinel-stack/data/nuscenes`, `/opt/sentinel-stack/UniAD/data/nuscenes`, and
  `/data/nuscenes` were missing. Null published; no data download/copy, model extraction, label
  atlas, probe fitting, activation direction, iteration-12 scoring, selector evaluation, or
  closed-loop run authorized.
- 2026-07-06: Codex — pre-registered iteration 26 under
  experiments/iter26_data_staging_remedy/HYPOTHESIS.md. Scope is read-only source/capacity
  discovery after iter25's inventory-null, to determine whether the correct next action is an
  official nuScenes download/staging operation. No discovery script/run, data download/copy,
  extraction, root mutation, inventory rerun, model extraction, label atlas, probe fitting,
  activation direction, iteration-12 scoring, selector evaluation, or closed-loop work launched.
- 2026-07-06: Codex — ran iteration 26 read-only staging discovery. It identified the required
  source as official nuScenes v1.0 trainval sensor file blobs parts 1-10 (292.78 GB archive
  budget) and rejected current capacity: 365.975 GB required by the 1.25x margin, 25.125 GB free
  observed. The governed sentinel bucket has only metadata/map/CAN bus artifacts. Null published;
  next action is storage/staging pre-registration, not model work.
- 2026-07-06: Codex — pre-registered iteration 27 under
  experiments/iter27_storage_provisioning/HYPOTHESIS.md. Scope is storage provisioning only: one
  1024 GB persistent disk at `/datasets/nuscenes-full`; no data download/copy/extraction,
  inventory rerun, model extraction, label atlas, probe fitting, activation direction,
  iteration-12 scoring, selector evaluation, or closed-loop work launched yet.
- 2026-07-06: Codex — ran iteration 27 storage provisioning. Created/attached/formatted/mounted
  `sentinel-nuscenes-data-1tb` at `/datasets/nuscenes-full`; free space is 1,026,108,792,832
  bytes, above the 900 GB bar. No dataset bytes moved and no Docker/model/NeuroNCAP run launched.
  Result published as a storage-only pass; next step requires a fresh data-staging
  pre-registration before any nuScenes download/copy/extraction or inventory rerun.
- 2026-07-06: Codex — pre-registered iteration 28 under
  experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md. Scope is official nuScenes trainval
  staging only: the metadata archive plus ten v1.0 trainval sensor-blob archives into
  `/datasets/nuscenes-full`, redacted source provenance, archive hashes, extraction safety, and
  bounded availability inventory. No source manifest read, download/copy/extraction, inventory run,
  model extraction, label atlas, probe fitting, activation direction, iteration-12 scoring,
  selector evaluation, or closed-loop work launched yet.
- 2026-07-07: Codex — completed iteration 28 as an official nuScenes trainval staging and
  availability PASS. Staged all 11 official archives into `/datasets/nuscenes-full`
  (`314,886,603,672` bytes total) with redacted source provenance and SHA proofs; extracted with
  `0` unsafe members across `2,631,374` tar members; verified all six camera channels have
  `34,149` files; remote bounded inventory passed with `532` fresh post-firewall train scenes,
  `21,461` eligible keyframes, and `5,360` heldout keyframes. No Docker/model/NeuroNCAP,
  label atlas, probe fitting, activation direction, iteration-12 scoring, selector evaluation, or
  closed-loop work launched. Next action requires a fresh research pre-registration naming the
  committed iter28 availability manifest.
- 2026-07-07: Codex — cleaned up the temporary iter28 direct-SSH staging surface after the result
  commit was pushed: deleted firewall rule `sentinel-direct-ssh-20260707`, removed VM tag
  `sentinel-direct-ssh`, and deleted only obsolete `.iter28_tmp` upload/inventory scratch files.
  Verified the official archive directory and extracted `/datasets/nuscenes-full/v1.0-trainval`
  root still exist; GPU box remains IDLE.
- 2026-07-07: Codex — pre-registered iteration 29 under
  experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md. Scope is the first research gate
  on the completed `/datasets/nuscenes-full` root: import the committed iter28 availability
  manifest, pass a two-run canary, run full extraction only after canary pass, then compute frozen
  low-diversity hazard and benign-control support counts. No tooling, manifest import, GPU work,
  probe fitting, activation direction, intervention, iteration-12 scoring, selector evaluation, or
  closed-loop work launched yet.
- 2026-07-08: Codex — iteration 29 S0a/S0b passed and proof was committed: manifest import matched
  the iter28 digest/counts exactly, and the two-run canary had deterministic canonical hashes,
  30/30 joins per run, zero error rows, and stable tensor shapes/dtypes. Full extraction is now
  IN FLIGHT on sentinel-gpu if `/var/log/sentinel-e29-extract.log` lacks
  `E29_STAGE1_EXTRACT_DONE`; model container `model` is expected while in flight. At launch,
  532 manifest scenes matched and the first fit scene completed (`SCENE_DONE fit scene-0852
  frames=41`). Do not relaunch while the container/log indicate progress.
- (append one line per shift: dates, operator, what changed, box state at exit)
