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
   "state-of-the-art", "definitive" never appear as self-description). Form: one terse subject
   line (~72 chars, `iterNN: what happened`), no em dashes, never a paragraph-length subject;
   detail belongs in HYPOTHESIS/RESULT/shift-log docs, not the commit message (convention
   drifted 2026-07-12, corrected forward; pushed history stands). CI must be green on
   every push — it runs ruff + pytest + `scripts/validate_docs.py` (diagram budgets, link
   health, README story completeness).
7. **Memory at every state change** (Claude shifts: the aweb-sentinel file under
   `~/.claude/projects/-Users-danielwahnich-workspace-aweb/memory/`; other operators: update
   THIS file's "shift log" section and the dynamic snapshot instead).
8. **Defensibility over impressiveness.** When choosing between a stronger-looking repository
   story and a more defensible scientific claim, choose the defensible claim. A narrower result
   that survives hostile scrutiny is worth more than a larger claim resting on untested
   assumptions. Prefer external-validity falsification, hidden-assumption discovery, and
   reproducibility over incremental benchmark optimization when those goals conflict.

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
- Iteration 39 concluded:
  experiments/iter39_external_validity_claim_audit/RESULT.md. The external-validity claim audit
  passed S0/S1/S2, then S3 found three active-doc wording problems. The same state narrowed the
  report/manuscript titles to frozen UniAD with measured cross-planner limits and removed
  ambiguous certification-like wording; a post-narrowing scanner pass had zero findings. It
  creates no new empirical safety evidence. Default next line: external-validity falsification
  (latency/intervention-cost audit or sensor/input-degradation stress) before incremental
  mechanism search, unless iteration-38 calibration is explicitly justified.
- Iteration 40 concluded:
  experiments/iter40_timing_cost_audit/RESULT.md. The offline timing/intervention-cost audit over
  committed full14/power evidence passed S0/S1/S2/S3: `400/400` best episodes joined, `1,205`
  brake frames over `10,789.9 m`, `230/400` intervention episodes, and `61` measured lead-time
  episodes (median `1.30 s`, p05/p95 `0.40/3.50 s`). It authorizes only simulation timestamp and
  brake-frame budget wording, not wall-clock latency, passenger comfort, production cost,
  deployment readiness, or new safety claims. It motivated the sensor/input-degradation
  prerequisite in iteration 41; after iteration 41's null, that line requires replay-support
  repair before any robustness claim.
- Iteration 41 concluded:
  experiments/iter41_sensor_input_degradation_gate/RESULT.md. The offline monitor-input
  degradation gate stopped at S0 as `DEGRADATION_GATE_INFRASTRUCTURE_NULL`: frozen paths, H-P0,
  the iteration-40 verdict, and best decision-log counts were intact, but exact timestamp lookup
  into committed `p14-best` ego poses missed `1,388/6,474` timestamped monitor frames across
  `400/400` episodes. Perturbation bars were skipped. No object-stream, camera, degraded-sensor,
  GPU, closed-loop, selector, deployment, or safety robustness claim is authorized. A successor on
  this line needs a fresh replay-support pre-registration before any result.
- Iteration 42 concluded:
  experiments/iter42_exact_trace_replay_support/RESULT.md, published as
  `TRACE_REPLAY_SUPPORT_PASS`. The single authorized best-arm full14/power trace-capture run
  logged the exact `ego2world` matrix with every monitor frame and hit the frozen envelope
  exactly: `400/400` reset blocks, `6,474` frame rows, `1,205` brake frames, `156` releases,
  `230` intervention episodes, `0` field failures, `0` trace-error rows. The committed analyzer
  replayed the released-union rule from logged inputs alone and matched every frame's
  fired/brake/release/latch state with `0` mismatches. This is trace-substrate evidence only:
  it authorizes ONLY a future offline object-stream perturbation pre-registration over the
  committed exact trace (proof-trace/sentinel_iter42_trace.jsonl.gz, SHA256
  `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d`); no degradation,
  robustness, selector, deployment, or safety claim.
- Iteration 43 concluded:
  experiments/iter43_object_stream_perturbation_gate/RESULT.md, published as
  `OBJECT_PERTURBATION_MILD_FRAGILE`. The entirely offline perturbation gate over the committed
  iteration-42 exact trace passed S0 provenance and S1 zero-strength identity (0 mismatched
  frames through the reused iteration-42 replay implementation), then ran the frozen 14-cell
  jitter/dropout/score/churn grid once with seed `iter43-object-stream-perturbation-v1`.
  Two of five mild cells failed the frozen bars: position jitter at `0.05 m` (retention
  `218/230` vs `>=219`; `17` new interventions vs `<=8`) and `0.10 m` (`36` new, `1,445` brake
  frames); the false-intervention dose-response is monotonic to `151` new interventions at
  `1.00 m`. Dropout `0.05`, score attenuation `0.90` (decision-identical), and identity churn
  `0.05` were STABLE. Scope is replay decision-flip sensitivity of the monitor rule only —
  not sensor/camera degradation, not closed-loop (consequences of flipped decisions are not
  observable offline), and no benchmark, selector, deployment, or safety claim. Per the
  registered S4 boundary the offline perturbation line at this trace is closed; any successor
  (e.g. correlated-noise or smoothed-input variants, or any closed-loop degradation line)
  requires a fresh pre-registration.
- Iteration 44 concluded:
  experiments/iter44_velocity_smoothing_gate/RESULT.md, published as
  `VELOCITY_SMOOTHING_NO_REPAIR_NULL`. The fresh pre-registration authorized after iteration 43
  tested temporally smoothed velocity estimators (finite difference over `k ∈ {2, 3}` frames;
  EMA at `alpha ∈ {0.5, 0.3}`) as the jitter-fragility repair, entirely offline over the
  committed iteration-42 trace with the seed-paired iteration-43 perturbation layer. S0/S1/S1b
  passed exactly (neutral cells bit-identical to the online stream; iteration-43 jitter cells
  reproduced field-for-field), then every frozen estimator failed both V1 baseline fidelity
  (retention `209-215/230` vs the `>= 225` bar, `5-6` invented interventions vs `<= 4`) and V2
  jitter repair (`11-20` new interventions vs `<= 8`, retention below `219`). Smoothing halves
  the over-firing (`36 -> 18-20` at `0.10 m`) but erases `15-21` genuine online interventions
  outright (median delay `0` — lost interventions vanish, not shift), and residual over-firing
  survives through the CPA term's direct use of jittered positions. Read with iteration 18,
  this bounds the rule from both sides: its decision boundary sits on one-frame velocity
  transients, so no low-pass filter on this estimator is the repair. The released union is
  unchanged; scope is offline decision replay only (changed decisions' vehicle outcomes are not
  observable). The temporal-smoothing repair line is closed at these frozen parameters; any
  successor (estimator-class change such as a measurement-noise-modeling tracking filter, a
  noise-robust rule term, or any closed-loop line) requires a fresh pre-registration.
- Iteration 45 concluded:
  experiments/iter45_hugsim_infra_gate/RESULT.md, published as `HUGSIM_INFRA_GATE_PASS`. The
  Stage-0-only infrastructure gate for the second closed-loop benchmark family passed all four
  completion bars: the XDimLab/HUGSIM release staged at `/datasets/nuscenes-full/hugsim/` with
  a committed 306-file SHA256/size manifest; the HUGSIM pixi environment built (torch
  `2.4.1+cu124`, gsplat `1.2.0`, `simple-knn` +`float.h` build patch; apex fails its strict
  CUDA-minor check but is used only by the reconstruction toolchain — non-blocking, recorded);
  the unmodified UniAD_SIM client (`5fb279e3`) runs inside the existing `uniad:latest` image on
  the SAME `uniad_base_e2e.pth`; and one monitor-OFF scenario (`scene-0013-easy-00`, frozen
  lexicographic rule) ran closed-loop end-to-end through the named pipes (15 steps,
  benchmark-rule termination, `eval.json` HD-Score output, per-step logs). One real
  incompatibility found and bounded: CUDA 11.1 cuSOLVER cannot init on the L4 (sm_89), so the
  client's GPU dense linalg runs through a recorded interpreter-level CPU shim
  (`/opt/sentinel-stack/hugsim-shim/sitecustomize.py`); client/model code untouched. The pass
  authorizes ONLY the Stage-1/2 pre-registration (monitor-OFF reproduction subset, then OFF vs
  released union, seed-paired); no transfer, benchmark, robustness, deployment, or safety
  claim. Box-side surfaces to know: configs edited with `.orig` originals preserved
  (`HUGSIM/configs/sim/nuscenes_base.yaml`, `UniAD_SIM/tools/e2e.sh` docker wrapper,
  `scene-0013/cfg.yaml` model_path), smoke launcher `/tmp/hugsim_smoke.sh`, logs
  `/var/log/sentinel-hugsim-*.log`.
- Iteration 46 concluded:
  experiments/iter46_hugsim_off_baseline/RESULT.md, published as `HUGSIM_OFF_BASELINE_NULL`
  (analyzer verdict `NULL_FALSIFIER_CRASH_LOOP_DUAL_FAILURES`). The Stage-1 monitor-OFF
  baseline over the frozen 52-scenario easy+medium subset ran to `I46_OFF_ALL_DONE` (launch 2,
  after the recorded launcher-only amendment), with the D0 probe recording the loop as
  STOCHASTIC (16 vs 15 steps, `data.pkl` SHA divergence) — schedule = first 26 scenarios x 2
  back-to-back runs. `38/52` episodes completed with finite HD-Scores and per-step logs (all
  attempt 1, 114-481 s each); the seven scheduled `load_HD_map: true` `-medium-01` scenarios
  (scenes 0038/0051/0062/0064/0071/0138/0166) failed both attempts before the client's first
  step on `FileNotFoundError: /datasets/nuscenes-full/maps/expansion/singapore-onenorth.json`
  — the official nuScenes map-expansion pack was never staged (iteration 28 staged metadata +
  sensor blobs only); the one `-medium-01` without the flag (scene-0041) passed. C1 failed and
  the dual-failure falsifier fired; VRAM/disk falsifiers did not; pairing-infeasibility did
  NOT fire (median within-scenario |dHD| `0.0245` over 19 pairs vs the `0.15` bar,
  heavy-tailed: two pairs > `0.29`). Descriptive aggregate (plausibility context only): mean
  HD `0.3849`, easy `0.4355` (n=18) / medium `0.3393` (n=20). The null authorizes NOTHING:
  the Stage-2 OFF-vs-released-union pre-registration is NOT authorized. A successor needs a
  fresh pre-registration that stages `maps/expansion/` with provenance receipts and re-earns
  completion. Evidence committed under proof-off/ (both launch logs, receipts, D0 report,
  per-episode artifacts, prior-launch defect archive, heavy-artifact SHA manifest on the box
  at /datasets/nuscenes-full/hugsim/iter46_runs/).
- Iteration 47 concluded:
  experiments/iter47_map_staging_and_off_completion/RESULT.md, published as
  `OFF_COMPLETION_PASS` (analyzer verdict `PASS_BARS_MET`). Stage A staged the official
  nuScenes map-expansion pack v1.3 under the iteration-28-class gate (398,535,531 bytes,
  SHA-receipted, redacted public-bucket provenance, 0 unsafe members, four expansion jsons
  present). Stage B re-ran exactly the 14 previously failed `load_HD_map: true` `-medium-01`
  episodes under the re-verified iteration-46 provenance gate and the carried STOCHASTIC D0
  verdict; all 14 completed on attempt 1 (102-509 s, steps 9-156, ~1.2 GPU-h), reaching
  `I47_OFF_COMPLETION_DONE` with zero aborts. ONE analyzer run over all 52 (38 carried + 14
  new) passed C1 (52/52 complete, retried_episodes 0), C2 (per-step logs for all 52), and C3
  (evidence committed; carried integrity 104/104 files byte-identical to the committed iter46
  artifacts). Pairing falsifier NOT fired over all 26 within-scenario pairs: median |dHD|
  `0.0251` vs the `0.15` bar, but MORE heavy-tailed than the 19-pair view — 22/26 pairs at or
  under `0.09`, max `0.7419` (scene-0138-medium-01, r1 0.9378 vs r2 0.1959); that shape binds
  the Stage-2 paired design (back-to-back within-launch pairing + scenario-clustered
  uncertainty + stated heavy-tail policy). Descriptive 52-episode aggregate (plausibility
  context only): mean HD `0.3607`, median `0.2553`, easy `0.4355` (n=18) / medium `0.3211`
  (n=34); scene-0062-medium-01 completed both runs at HD exactly 0.0 (valid under C1).
  Iteration 46's null stands as published; the map-staging diagnosis is confirmed by cure.
  The pass authorizes exactly ONE thing: the iteration-48 Stage-2 OFF-vs-released-union
  transfer-gate pre-registration (docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md); it does
  NOT authorize the Stage-2 runs, and no transfer, monitor, OFF-vs-ON, benchmark-ranking,
  robustness, deployment, or safety claim is made.
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
- Iteration 28 concluded:
  experiments/iter28_nuscenes_trainval_staging/RESULT.md. It staged the official nuScenes v1.0
  trainval metadata archive plus ten sensor-blob archives into `/datasets/nuscenes-full`, proved
  archive bytes/SHA values, extracted with 0 unsafe tar members, verified all six camera channels,
  and passed a bounded availability inventory with 532 fresh post-firewall train scenes, 21,461
  eligible keyframes, and 5,360 heldout keyframes. It authorizes no model extraction, label
  atlas, probe fitting, activation direction, iteration-12 scoring, selector evaluation, or
  closed-loop work.
- Iteration 29 concluded:
  experiments/iter29_trainval_risk_support_atlas/RESULT.md. It was the first research gate on the
  staged full trainval root. S0c full extraction passed with 21,461/21,461 joined non-reset rows,
  zero error row types, and stable tensor shapes/dtypes. S1 low-diversity support passed
  (`eligible_lowdiv` 127/108/158 and `benign_control` 5,084/2,344/2,245 across
  fit/calibration/heldout); the optional strict-collapse note failed (`eligible_strict` 0/0/1).
  Iter29 authorizes only a separate successor pre-registration. It authorizes no probe fitting,
  activation direction, intervention replay, iteration-12 scoring, selector evaluation, or
  closed-loop work.
- Iteration 30 concluded:
  experiments/iter30_full_trainval_lowdiv_localization/RESULT.md. It used only committed
  iteration-29 proof artifacts and passed the diagnostic localization gate. S0 reproduced iter29
  hashes/counts exactly; S1 passed with the frozen motion/planning-bridge tensor probe at heldout
  AUROC 0.950, AP 0.615, and balanced accuracy 0.867, above metadata AUROC 0.596, ego-plan
  AUROC 0.674, and shuffled-label internal AUROC 0.531; S2 scene-cluster bootstrap passed with
  AUROC p05 0.922. This is diagnostic only: it authorizes only a separate causal-intervention
  pre-registration, not activation patching, iteration-12 scoring, selector evaluation, GPU work,
  or closed-loop work.
- Iteration 31 concluded:
  experiments/iter31_full_trainval_bridge_intervention/RESULT.md. It derived and committed a
  fit-only bridge-centroid direction, then stopped at S0 as an infrastructure-null: alpha `0.00`
  and `0.50` canary repeat hashes matched, but alpha `0.00` failed the iteration-29 baseline
  reproduction bar (`24` rows checked, `96` comparison failures, max coordinate error
  `30.222413063049316` m). Iter31 authorizes no calibration replay, heldout replay,
  iteration-12 scoring, selector evaluation, closed-loop work, or safety claim.
- Iteration 32 concluded:
  experiments/iter32_prefix_replay_baseline_recovery/RESULT.md. It replayed the exact 12 iter31
  canary target rows with 44 scene-prefix rows and passed the no-op baseline-recovery gate:
  two repeats, 44 non-reset rows and 12 target rows each, matching target canonical hashes, and
  max model/GT deltas of 0.0 versus committed iteration-29 artifacts. It authorizes only a fresh
  prefix-preserving bridge intervention pre-registration; it authorizes no direct intervention,
  calibration, heldout, iteration-12 scoring, selector evaluation, closed-loop work, or safety
  claim.
- Iteration 33 is now pre-registered:
  experiments/iter33_prefix_preserving_bridge_intervention/HYPOTHESIS.md. It is the fresh
  prefix-preserving bridge intervention successor authorized by iteration 32: same committed
  iteration-31 fit-only direction, but canary/calibration/heldout replays must preserve scene
  prefixes, context-only rows are always no-op, and metrics are target-row only. It authorizes no
  tooling, GPU replay, calibration, heldout, iteration-12 scoring, selector evaluation,
  closed-loop work, or safety claim until the required tooling and gates are committed.
- Iter22 planning artifacts now exist under docs/research/: ITER22_HYPOTHESIS_DRAFT.md and
  ITER22_ADVERSARIAL_REVIEW.md. They are planning-only, not pre-registrations. Owner guidance:
  do not promote the broad A0-A8 draft directly; use the adversarial review's tighter Stage
  1-only causal-localization shape before any iteration-12 gate or GPU work.
- Paper: docs/paper/paper.pdf compiled; arXiv account live (Daniel: ezio143); submission
  waits on a cs.RO endorsement (code V76QK4; request sent to William Ljungbergh
  william@recohere.ai on 2026-07-05 — silent through 2026-07-11 per a live mailbox check;
  escalation sent to Holger Caesar H.Caesar@tudelft.nl on 2026-07-11, Gmail message id
  19f51374b4186984, review copy 19f51371eb509367; threaded follow-up to Ljungbergh with the
  DMAD-corroboration update sent 2026-07-11 from daniel@aweblabs.ai, Gmail id 19f51f7617032232;
  remaining fallback: CATPlan authors). After
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
  30/30 joins per run, zero error rows, and stable tensor shapes/dtypes. Full extraction then
  completed cleanly on sentinel-gpu (`FEEDER_DONE mode=full split=all scenes=532 frames=21461`;
  `E29_STAGE1_EXTRACT_DONE Wed Jul  8 14:36:11 UTC 2026`). S0c passed with `21,461/21,461`
  joined non-reset rows, zero error row types, stable primary tensor shapes/dtypes, and split
  counts matching the manifest. S1 low-diversity support passed with no count-floor or
  distribution failures; optional strict-collapse support failed. No probe fitting, activation
  direction, intervention replay, iteration-12 scoring, selector evaluation, or closed-loop work
  is authorized from iter29; a successor requires a fresh pre-registration. GPU box has no iter29
  model container left running after the full extraction script removed it.
- 2026-07-08: Codex — audited the public story while iter29 full extraction remained in flight:
  README, docs/CAMPAIGN.md, docs/NEXT_PHASE.md, and docs/REPORT.md now state the data-scope
  boundary explicitly. Iterations 1-27 used real NeuroNCAP/nuScenes closed-loop or registered
  extraction evidence where applicable, but they did not use the full official
  `/datasets/nuscenes-full` trainval root; iteration 28 is the first full-root staging pass and
  iteration 29 is the first research gate on that root. No scientific result was changed.
- 2026-07-08: Codex — clarified README score-tracker semantics: `—` in metric cells means
  not-applicable for the registered gate type, not missing work, and "stopped before probes" means
  a frozen gate refused the next step rather than an unreported probe/model run.
- 2026-07-08: Codex — pre-registered iteration 30 under
  experiments/iter30_full_trainval_lowdiv_localization/HYPOTHESIS.md. Scope was diagnostic
  localization only on committed iteration-29 proof artifacts: validate hashes/counts, fit one
  low-capacity internal-representation probe against fixed controls if S0 passes, require
  scene-cluster robustness, and stop before any activation direction, intervention, iteration-12
  scoring, selector evaluation, closed-loop work, GPU run, or gcloud command.
- 2026-07-08: Codex — completed and published iteration 30 as a diagnostic localization pass.
  S0/S1/S2 passed: iter29 hashes/counts reproduced exactly; the internal motion/planning-bridge
  tensor probe reached heldout AUROC 0.950, AP 0.615, and balanced accuracy 0.867, exceeding
  metadata and ego-plan controls; scene-cluster bootstrap AUROC p05 was 0.922. No new extraction,
  GPU/gcloud work, activation intervention, iteration-12 scoring, selector evaluation, or
  closed-loop work ran. Successor work requires a fresh causal-intervention pre-registration.
- 2026-07-08: Codex — pre-registered iteration 31 under
  experiments/iter31_full_trainval_bridge_intervention/HYPOTHESIS.md. Scope is Stage-1 causal
  intervention only on the full-trainval bridge representation: derive a fit-only benign-centroid
  direction, select one alpha on calibration rows, then test heldout candidate-geometry movement
  and benign controls once. No direction builder, patch, feeder, analyzer, GPU/gcloud work,
  iteration-12 scoring, selector evaluation, or closed-loop work launched yet.
- 2026-07-08: Codex — added and committed the iteration 31 bridge-intervention tooling surface:
  offline direction/replay-manifest builder, UniAD server patch, row-manifest feeder, canary,
  calibration-grid and heldout run scripts, intervention analyzer, and unit tests. Local
  verification passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`). No
  direction artifact, GPU/gcloud run, calibration replay, heldout replay, iteration-12 scoring,
  selector evaluation, or closed-loop work launched yet.
- 2026-07-08: Codex — ran the iteration 31 offline direction builder only and committed
  `proof-direction/`: fit-only bridge-centroid direction SHA
  `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794`, replay manifests
  canary/calibration/heldout = `12`/`2452`/`2403`, and byte-stability rebuild passed. Local
  verification passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`). No
  GPU/gcloud run, S0 canary replay, calibration replay, heldout replay, iteration-12 scoring,
  selector evaluation, or closed-loop work launched yet.
- 2026-07-08: Codex — hardened the iteration 31 canary analyzer before GPU replay so S0 now
  checks the frozen `alpha=0.00` baseline reproduction bar against committed iteration-29
  trajectories/candidates within `1e-5`, in addition to repeat hashes and repeat counts. Local
  verification passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`). No
  GPU/gcloud run, S0 canary replay, calibration replay, heldout replay, iteration-12 scoring,
  selector evaluation, or closed-loop work launched yet.
- 2026-07-08: Codex — ran and published the iteration 31 S0 canary as an infrastructure-null:
  alpha `0.00` and `0.50` repeat hashes matched, but alpha `0.00` failed the registered
  iteration-29 baseline reproduction bar (`24` rows checked, `96` comparison failures, max
  coordinate error `30.222413063049316` m). `RESULT.md` and `proof-canary/` are committed.
  Calibration replay, heldout replay, iteration-12 scoring, selector evaluation, and closed-loop
  work remain unauthorized.
- 2026-07-08: Codex — pre-registered iteration 32 under
  experiments/iter32_prefix_replay_baseline_recovery/HYPOTHESIS.md. Scope is a no-op
  prefix-replay baseline recovery audit for the iter31 alpha-zero reproduction failure: exact 12
  target rows, 44 prefix replay rows, frozen parity bars against committed iteration-29 artifacts.
  No prefix manifest builder, no-op patch, feeder, analyzer, GPU/gcloud replay, intervention,
  calibration, heldout, iteration-12 scoring, selector evaluation, or closed-loop work launched
  yet.
- 2026-07-08: Codex — added and committed the iteration 32 prefix-replay tooling surface
  (prefix manifest builder, no-op server patch, prefix feeder, analyzer, two-run script, and
  tests), then ran the offline manifest/reference gate only. `proof-prefix/` passed with
  `44` prefix rows, `12` target rows, `32` context-only rows, and exact committed iteration-29
  extraction/GT target-key coverage. Local verification passed (`ruff check .`, `pytest -q`,
  `python3 scripts/validate_docs.py`). No GPU/gcloud replay, intervention, calibration, heldout,
  iteration-12 scoring, selector evaluation, or closed-loop work launched yet.
- 2026-07-08: Codex — ran and published the iteration 32 no-op prefix replay on `sentinel-gpu`.
  Two repeats completed with `44` non-reset rows and `12` target rows each; model and GT target
  canonical hashes matched across repeats; max model and GT deltas versus committed iteration-29
  artifacts were both `0.0`. Local verification passed (`ruff check .`, `pytest -q`,
  `python3 scripts/validate_docs.py`). This is a baseline-recovery pass only; no intervention,
  calibration, heldout, iteration-12 scoring, selector evaluation, closed-loop work, or safety
  claim launched.
- 2026-07-09: Codex — pre-registered iteration 33 under
  experiments/iter33_prefix_preserving_bridge_intervention/HYPOTHESIS.md. Scope is a fresh
  prefix-preserving bridge intervention using the committed iteration-31 direction and the
  iteration-32 replay lesson. No iteration-33 tooling, GPU/gcloud replay, calibration, heldout,
  iteration-12 scoring, selector evaluation, closed-loop work, or safety claim launched yet.
- 2026-07-09: Codex — added and committed the iteration 33 prefix-preserving intervention
  tooling surface, then published the offline prefix-manifest/direction-receipt proof. The S0
  offline gate passed with canary `44/12/32`, calibration `4293/2452/1841`, heldout
  `4283/2403/1880` prefix/target/context counts, direction SHA
  `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794`, and local verification
  passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`). No GPU/gcloud
  canary replay, calibration replay, heldout replay, iteration-12 scoring, selector evaluation,
  closed-loop work, or safety claim launched yet.
- 2026-07-09: Codex — hardened the iteration 33 S0 canary harness before GPU replay: run
  scripts now pass a server-patch SHA256 and UniAD source commit into logged rows, and alpha
  `0.00` target rows avoid extra original-output pre-planning calls so the baseline cell stays
  closest to the iteration-32 no-op replay form. Local verification passed (`ruff check .`,
  `pytest -q`, `python3 scripts/validate_docs.py`) and GitHub CI passed. A direct GPU probe
  still failed with non-interactive gcloud reauthentication; ask Daniel to run `gcloud auth
  login` before S0 canary replay. No GPU canary replay, calibration replay, heldout replay,
  iteration-12 scoring, selector evaluation, closed-loop work, or safety claim launched yet.
- 2026-07-09: Codex — ran and published the iteration 33 prefix-preserving S0 canary on
  `sentinel-gpu` after Daniel refreshed gcloud auth. Two alpha `0.00` repeats and two alpha
  `0.50` repeats completed with `44` non-reset rows and `12` target rows each. Alpha `0.00`
  reproduced the iteration-32 model/GT target hashes exactly, alpha `0.50` repeated
  deterministically, bridge SHA256 changed on `24/24` nonzero target observations, and local
  verification passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`).
  Calibration grid replay is authorized next; heldout replay, iteration-12 scoring, selector
  evaluation, closed-loop work, and safety claims remain unauthorized.
- 2026-07-09: Codex — refreshed the baton while the authorized iteration 33 calibration grid was
  in flight on `sentinel-gpu` (`/var/log/sentinel-e33-calibration.log`). Alpha `0.00`, `0.25`,
  and `0.50` had completed with exact `4293/2452/1841` prefix/target/context counts; alpha
  `0.75` was still running without error markers, and alpha `1.00` had not started yet. No
  calibration analyzer, heldout replay, iteration-12 scoring, selector evaluation, closed-loop
  work, or safety claim was launched.
- 2026-07-09: Codex — monitored the same authorized iteration 33 calibration grid through alpha
  `0.75` completion. Alpha `0.75` also completed with exact `4293/2452/1841`
  prefix/target/context counts, and alpha `1.00` had started on `sentinel-gpu`. No calibration
  analyzer, heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, or safety
  claim was launched.
- 2026-07-09: Codex — completed and analyzed the iteration 33 calibration grid. All five alphas
  completed exact `4293/2452/1841` prefix/target/context counts with zero error rows and no context
  contamination, but no nonzero alpha passed S1: best alpha `1.00` reached only `0.0308 m`
  eligible median endpoint-spread delta and `0.1296` fraction above `0.25 m`. Published as
  `CALIBRATION_NULL_NO_USABLE_ALPHA`; heldout replay, iteration-12 scoring, selector evaluation,
  closed-loop work, and safety claims remain unauthorized.
- 2026-07-09: Codex — pre-registered iteration 34 under
  experiments/iter34_direction_specificity_audit/HYPOTHESIS.md. Scope is a post-result offline
  audit of committed iteration-33 calibration artifacts to decide whether the same global
  bridge-centroid direction warrants any future scale-only successor. No analyzer, proof report,
  GPU/gcloud replay, heldout replay, iteration-12 scoring, selector evaluation, closed-loop work,
  or safety claim launched yet.
- 2026-07-09: Codex — ran and published the iteration 34 offline direction-specificity audit.
  S0 artifact/row integrity passed, but S1 dose-response coupling failed: only `74/108`
  eligible rows had nonnegative endpoint-spread slope (`0.685185` vs the frozen `0.70` bar).
  Published as `DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE`; S2 was not evaluated, and heldout replay,
  iteration-12 scoring, selector evaluation, closed-loop work, and safety claims remain
  unauthorized.
- 2026-07-10: Codex — pre-registered iteration 35 under
  experiments/iter35_response_heterogeneity_audit/HYPOTHESIS.md. Scope is an offline
  response-heterogeneity audit over committed iteration-33/34 artifacts only, with frozen
  baseline-geometry strata and support/benign-harm bars. No analyzer, proof report, GPU/gcloud
  replay, heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, or safety
  claim launched yet.
- 2026-07-10: Codex — ran and published the iteration 35 offline response-heterogeneity audit.
  S0 passed and S1 showed real row-level heterogeneity (`42/108` eligible rows with slope
  `>=0.05 m/alpha`, `34/108` with slope `<0`, IQR `0.126519 m/alpha`), but S2 failed because
  no frozen baseline-geometry stratum passed the actionability bars. Published as
  `HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM`; heldout replay, iteration-12 scoring, selector
  evaluation, closed-loop work, row-conditioned successor work, and safety claims remain
  unauthorized.
- 2026-07-10: Codex — pre-registered iteration 36 under
  experiments/iter36_bridge_site_decomposition/HYPOTHESIS.md. Scope is an offline bridge-site
  decomposition audit over committed iteration-29/30/35 artifacts only, with frozen target-site
  slices (`traj_slot_0` through `traj_slot_5`, `track_query`) and scene-robustness bars. No
  analyzer, proof report, GPU/gcloud replay, heldout replay, iteration-12 scoring, selector
  evaluation, closed-loop work, intervention direction, or safety claim launched yet.
- 2026-07-10: Codex — ran and published the iteration 36 offline bridge-site decomposition audit.
  S0 passed, S1 reproduced the full-bridge diagnostic signal, and S2 passed for `traj_slot_0`,
  `traj_slot_2`, `traj_slot_3`, `traj_slot_4`, and `track_query`; `track_query` was strongest
  (AUROC `0.970531`, AP `0.726416`, bootstrap AUROC p05 `0.950589`). Published as
  `BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED`; only a separate future site-specific
  intervention pre-registration is authorized. No GPU/gcloud replay, heldout intervention replay,
  iteration-12 scoring, selector evaluation, closed-loop work, direction, alpha, deployment
  language, or safety claim launched.
- 2026-07-10: Codex — pre-registered iteration 37 under
  experiments/iter37_track_query_site_intervention/HYPOTHESIS.md. Scope is a
  prefix-preserving `track_query`-only site intervention with a fit-only centroid direction,
  frozen alpha grid, S0 canary, calibration, and heldout gates. No tooling, direction artifact,
  proof report, GPU/gcloud replay, heldout replay, iteration-12 scoring, selector evaluation,
  closed-loop work, deployment language, or safety claim launched yet.
- 2026-07-10: Codex — added and committed the iteration 37 offline track-query direction builder
  and unit tests, then built and committed the reproduced `proof-direction` artifact. Direction
  has feature count `256`, fit rows `5211` (`127` eligible lowdiv, `5084` benign control), zero
  dropped dimensions, direction stats SHA `d46179b6f6152e9ede19c2ddf05eb4ce53cb72a229705fea88c337feb5905cd5`,
  and file SHA `56c70104230f2eacd328c884197c93bd120076fbed775e21c8dc219f6392230f`. Local
  verification passed (`ruff check .`, `pytest -q`, `python3 scripts/validate_docs.py`). GPU
  box was reachable and idle in refreshed `HANDOFF.md`; no S0 canary, calibration, heldout
  replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or
  safety claim launched.
- 2026-07-10: Codex — added and committed iteration 37 replay tooling: track-query-only UniAD
  server patch, prefix-preserving feeder, canary/calibration/heldout run scripts, analyzer, and
  unit tests. The patch mutates only `sdc_track_query`, logs track-query and full-bridge SHA
  changes, and treats any `sdc_traj_query_last` SHA change as S0 wrong-site failure. Local
  verification passed (`ruff check .`, `pytest -q` with `89` tests, `python3 scripts/validate_docs.py`).
  GPU box was reachable and idle in refreshed `HANDOFF.md`; no S0 canary, calibration, heldout
  replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or
  safety claim launched.
- 2026-07-10: Codex — ran and committed iteration 37 S0 canary proof. S0 passed with alpha-zero
  target model hash `2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e`,
  alpha-zero GT hash `5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7`,
  zero alpha-zero coordinate error, alpha-0.50 repeat hash
  `bb7983cfba0c8c132b09474c61fae202ac8514e1e552a44c951070c84dc25e54`, `24/24`
  changed track-query SHA rows, and `24/24` unchanged `sdc_traj_query_last` SHA rows. GPU
  box was idle after collection in refreshed `HANDOFF.md`; calibration grid is now authorized,
  but heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment
  language, and safety claims remain unauthorized.
- 2026-07-10: Codex — launched the authorized iteration 37 calibration grid as a detached GPU
  job using `/tmp/calibration_grid_run_iter37.sh`, with output log
  `/var/log/sentinel-e37-calibration.log`. The laptop-local monitor was stopped, but the remote
  `model` container remained in flight. Latest recovery snapshot before baton commit: alpha
  `0.00` completed and compressed (`sentinel_e37_calibration_alpha0p00.jsonl.gz` `4414`
  lines; GT `4293` lines) with `E37_CALIBRATION_ALPHA_0p00_DONE`; alpha `0.25` was running
  (`713` model lines, `693` GT lines). Do not relaunch calibration while any Docker container
  is up. When `E37_CALIBRATION_DONE` appears, collect all five alpha logs, analyze calibration,
  publish the grid proof or calibration null, and keep heldout, iteration-12 scoring, selector
  evaluation, closed-loop work, deployment language, and safety claims unauthorized until the
  registered bars allow them.
- 2026-07-10: Codex — recovered the interrupted iteration 37 calibration/watch session and aligned
  README plus docs/NEXT_PHASE with the committed direction/tooling/S0 facts while keeping
  calibration explicitly in flight. Verification passed locally (`ruff check .`, `pytest -q`,
  `python3 scripts/validate_docs.py`). Latest pre-handoff remote snapshot at
  `2026-07-10T13:00:10Z`: alpha `0.00`, `0.25`, and `0.50` completed with exact
  `4293/2452/1841` feeder counts; alpha `0.75` is running on `sentinel-gpu` with `2479` model
  rows and `2409` GT rows written, and the `model` container is up. Do not relaunch. If the laptop sleeps, resume by
  probing `/var/log/sentinel-e37-calibration.log`; after `E37_CALIBRATION_DONE` and empty Docker,
  collect all five alpha logs, analyze calibration, and keep heldout/iteration-12/selector/
  closed-loop/deployment/safety claims unauthorized unless the registered bars advance.
- 2026-07-10: Codex — collected and analyzed the completed iteration 37 calibration grid.
  All five alphas completed exact `4293/2452/1841` row counts with zero context-contamination
  failures, zero error rows, and zero gross-validity failures, but no nonzero alpha was selectable.
  Alpha `1.00` had eligible median endpoint-spread delta `-0.041940 m`, fraction `>0.25 m`
  `0.074074`, and median best-candidate-gap delta `-0.001315`. Published as
  `CALIBRATION_NULL_NO_USABLE_ALPHA`; heldout replay, iteration-12 scoring, selector evaluation,
  closed-loop work, deployment language, and safety claims remain unauthorized.
- 2026-07-10: Codex — pre-registered iteration 38 under
  `experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md`. Scope is the exact
  sign-reversed `sdc_track_query` centroid direction (`mu_pos - mu_benign`), required to be the
  negative of the committed iteration 37 raw direction. No iteration 38 tooling, direction
  artifact, GPU/gcloud command, model replay, calibration result, heldout replay, iteration-12
  scoring, selector evaluation, closed-loop work, deployment language, or safety claim exists yet.
  Next authorized work is tooling/tests for the committed pre-registration.
- 2026-07-10: Codex — added iteration 38 tooling/tests for the committed opposite-direction
  pre-registration: offline direction builder with iteration-37 sign-equivalence check, UniAD
  server patch, prefix-preserving feeder, canary/calibration/heldout run scripts, analyzer, and
  unit tests. No iteration 38 direction artifact, GPU/gcloud command, model replay, calibration
  result, heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment
  language, or safety claim exists yet. Next authorized work is the offline direction build.
- 2026-07-10: Codex — ran the iteration 38 offline direction builder only and committed
  `proof-direction/`: feature count `256`, fit rows `5211`, direction stats SHA
  `251323cf6ba7361da5aa0a084a6ae5ad5083989df75e10d16f352da845e2983d`, file SHA
  `ca256dc8a402c9bc6b12df800f9ae62052f95ab78aef78ceb253a44a9fc41743`, and exact
  negative-of-iteration-37 sign equivalence (`max_abs_direction_sum=0.0`, cosine `-1.0`).
  Local verification passed (`ruff check .`, `pytest -q` with `100` tests,
  `python3 scripts/validate_docs.py`). No GPU/gcloud command, S0 canary replay, calibration,
  heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment
  language, or safety claim exists yet. Next authorized work is S0 canary replay.
- 2026-07-10: Codex — ran and collected iteration 38 S0 canary proof. S0 passed with exact
  alpha-zero parity (`0.0` max coordinate error), model alpha-zero target hash
  `2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e`, GT alpha-zero target
  hash `5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7`, stable alpha-0.50
  repeat hash `af113a25e8eccb092a7e863f6f13892871d6b78a766d68267773e3e8972a28a7`, `24/24`
  changed track-query SHA rows, and `24/24` unchanged `sdc_traj_query_last` SHA rows.
  Calibration is authorized by the registered gate but not launched. Under the defensibility
  rule, compare the value of Iter38 calibration against a fresh external-validity falsification
  pre-registration before spending the next GPU window.
- 2026-07-11: Claude (Fable 5) — took the baton mid-iter42 (run IN FLIGHT under the read-only
  watcher; not touched). Verified the Ljungbergh endorsement request was silent for 6 days in
  the live mailbox and sent the pre-authorized escalation to Holger Caesar (H.Caesar@tudelft.nl,
  Gmail id 19f51374b4186984; review copy to Daniel first). Launched an external frontier survey
  (NeuroNCAP SOTA 2026, monitor/interpretability literature, industry landscape) to position the
  campaign; key facts so far: RiskMonitor (arXiv 2503.07425v2, 2026-02) is the closest prior —
  frozen UniAD/VAD + risk head + max-brake on NeuroNCAP, collision-rate-only, no CIs, no
  deployment-cost measurement; retrained planners now post 3.06 (BridgeAD, CVPR 2025) and 3.49
  (ImagiDrive, ICRA 2026, no-post-processing family) on NeuroNCAP, so 2.91 must be framed as a
  training-free plug-in on a frozen planner, not absolute benchmark SOTA; no published work
  probes or steers UniAD/VAD-class planner internals (iters 29-38 line appears first-of-kind);
  "detection-without-correction" asymmetry now documented in LLMs (arXiv 2604.13068) — our
  steering nulls are independent cross-domain evidence. Full positioning report to Daniel in
  the session; related-work refresh of the manuscript is a named next action.
- 2026-07-11: Claude (Fable 5) — manuscript related-work refresh DONE with source-verified
  numbers only: added a "Retrained planners on the same benchmark" paragraph (BridgeAD CVPR 2025
  2.98--3.06 with post-processing / UniAD 1.84 same table, verified from arXiv 2503.14182 HTML;
  ImagiDrive ICRA 2026 3.49 in the no-post-processing family, verified from arXiv 2508.11428;
  DMAD UniAD rerun 2.11 corroborating our 2.12 reproduction, verified from the DMAD README) plus
  three bibitems; paper.pdf recompiled (tectonic) and sentinel-arxiv-submission.tar.gz rebuilt
  with identical member list. Scope note: the compiled paper covers through iteration 19; the
  iters 29-38 probe/steering line and its cross-domain "detection-without-correction" framing
  (arXiv 2604.13068) are deliberately NOT folded in — that is a future revision, not this
  submission.
- 2026-07-11: Claude (Fable 5) — while iter42 remained in flight (protected, watcher + external
  read-only poll), committed two planning-only research docs: FRONTIER_POSITIONING_2026-07-11.md
  (source-verified benchmark table + consequences: linear-steering line closed, headline framing
  rule binding) and SECOND_BENCHMARK_TRANSFER_HUGSIM.md (launch packet: HUGSIM primary — same
  uniad_base_e2e.pth checkpoint via hyzhou404/UniAD_SIM pipe client, ~61 GB prebuilt scenes,
  10-20 GPU-h per sweep on the L4, no prior monitor work there; Bench2Drive = labeled-subset
  stretch only, Argus ASE 2025 occupies that slot and a full pass costs weeks on one L4).
  Neither authorizes a run; the HUGSIM line needs its own HYPOTHESIS.md and launches only after
  iter42 completes and its analyzer publishes.
- 2026-07-11: Claude (Fable 5) — collected the completed iteration 42 trace-capture run from
  sentinel-gpu (`I42_TRACE_ALL_DONE` at 18:27:55 UTC; trace SHA256 `8c43726c…` verified identical
  after copy; run + watch logs committed under proof-trace/), ran the committed analyzer once
  from the committed artifacts, and published `TRACE_REPLAY_SUPPORT_PASS`: S0/S1/S2/S3 all
  passed, exact frozen counts (`400` resets, `6,474` frames, `1,205` brake frames, `156`
  releases, `230` intervention episodes), and exact offline replay identity (`0` mismatched
  frames). README row 42, header status, defensibility diagram, and net-summary updated to the
  verdict. Only a future offline object-stream perturbation pre-registration is authorized;
  heldout, iteration-12 scoring, selector, closed-loop, deployment, and safety claims remain
  unauthorized. BOX IDLE at exit (no containers; root disk 96% used, 16 GiB free — nothing
  deleted).
- 2026-07-11: Claude (Fable 5) via delegated executor — executed iteration 43 end-to-end,
  entirely offline (no gcloud, Docker, or GPU command; BOX UNTOUCHED, still IDLE).
  Pre-registered the object-stream perturbation gate over the committed iter42 exact trace
  (frozen 14-cell jitter/dropout/score/churn grid, seed `iter43-object-stream-perturbation-v1`,
  mild-set stability bars) BEFORE any analysis code existed; committed analyzer (reusing the
  iter42 replay implementation via import) + 9 unit tests; ran the analyzer exactly once from
  committed artifacts and published `OBJECT_PERTURBATION_MILD_FRAGILE` at full weight: jitter
  fragile at `0.05`/`0.10 m` (over-firing dominant — `17`/`36` new interventions vs the `<=8`
  bar), dropout/score/churn stable at mild levels; zero-strength identity exact, determinism
  guard pass, trace SHA unchanged. README row 43, header clause, net-summary, defensibility
  diagram (A43), status bullet, and repo map updated; ruff + pytest (131) +
  validate_docs green. The offline perturbation line at this trace is closed; successors need
  a fresh pre-registration.
- 2026-07-11: Claude (Fable 5) via delegated executor — executed iteration 44 end-to-end,
  entirely offline (no gcloud, Docker, or GPU command; BOX UNTOUCHED). Pre-registered the
  velocity temporal-smoothing repair gate (frozen estimators `fd_k2`/`fd_k3`/`ema_a0p5`/
  `ema_a0p3`, frozen V1 fidelity + V2 jitter-repair + V3 no-new-fragility bars, iteration-43
  seed reused verbatim for seed-paired perturbation draws, fresh run id
  `iter44-velocity-smoothing-v1`) and committed it ALONE before any analysis code; committed
  the analyzer (importing the iter42 replay and iter43 perturbation modules) + 10 unit tests;
  ran once from committed artifacts and published `VELOCITY_SMOOTHING_NO_REPAIR_NULL` at full
  weight: S1/S1b exact (0 mismatches; iter43 jitter cells reproduced field-for-field), then all
  four estimators failed V1 (retention 209-215/230 vs >=225) and V2 (new interventions 11-20 vs
  <=8); smoothing halves over-firing but erases 15-21 genuine interventions — no low-pass
  filter on this estimator is the repair. README row 44, header clause, net-summary,
  defensibility diagram (A44), status bullet, what's-next, and repo map updated; ruff + pytest
  (140) + validate_docs green. HANDOFF.md regenerated via scripts/make_handoff.py after the
  docs commit; its read-only probe (run after the result was published, outside the iteration's
  evidence chain) confirmed sentinel-gpu IDLE with no Docker containers — the box was not
  otherwise touched.
- 2026-07-12 (box-clock 2026-07-11 22:12-23:35 UTC): Claude (Fable 5) via delegated executor —
  opened the HUGSIM transfer lane in three stages. (1) Verified disk cleanup per
  docs/research/BOX_CLEANUP_2026-07-12.md: 26.7 GiB freed (root 16 -> 43 GiB free at 87%);
  outoutput/iter42-trace archived FIRST into the committed
  experiments/iter42_exact_trace_replay_support/proof-runs-cleanup/i42-runs.tar.gz then
  deleted; 196 UniAD jsonl/gz duplicates deleted only after SHA256 match against committed
  artifacts; 42 logs deleted only when byte-identical to committed copies; 2 files + 25 logs
  SKIPPED as unverifiable; Docker images and both dataset roots untouched. (2) Pre-registered
  iteration 45 (experiments/iter45_hugsim_infra_gate/HYPOTHESIS.md, committed ALONE, CI green)
  per the launch packet's frozen Stage-0 shape. (3) Executed the gate to completion in the same
  window: assets (306-file SHA manifest), environments (3 recorded pixi attempts to torch
  cu124; falsifier probes fired exactly as pre-declared and were bounded), unmodified client on
  the frozen checkpoint, and the single monitor-OFF smoke (scene-0013-easy-00, 15 steps,
  HD-Score produced). Published HUGSIM_INFRA_GATE_PASS at full weight; README row 45 + header +
  status bullet + repo map updated; ruff + pytest (140) + validate_docs green on every push.
  BOX state at exit: IDLE, no Docker containers, root 43 GiB free, data disk 184 GiB free;
  detached jobs all terminated (check /var/log/sentinel-hugsim-*.log markers). Exact resume
  point: write the Stage-1/2 HUGSIM pre-registration (monitor-OFF reproduction subset first)
  per the S4 boundary in iter45 RESULT.md; the smoke launcher and shim on the box are reusable
  surfaces for it.
- 2026-07-11 23:37-00:15 UTC (box clock): Claude (Fable 5) via delegated executor — iteration
  46 opened on the iter45 resume point. (1) Pre-registered the HUGSIM Stage-1 monitor-OFF
  baseline (experiments/iter46_hugsim_off_baseline/HYPOTHESIS.md, commit `077e8d9`, committed
  alone with the pinned iter45 shim byte copy, CI green): frozen 52-scenario easy+medium
  nuScenes subset (deterministic rule + per-yaml SHA256s), D0 determinism probe deciding run
  multiplicity (deterministic -> N=1 x 52; stochastic -> N=2 x lexicographic first 26),
  completion bars C1-C3, budget ceiling ~19.4 GPU-h (53 runs x 20-min timeout) vs expected
  2.5-6 h, falsifiers (crash loop, VRAM overflow, pairing-infeasibility median |dHD|>0.15,
  disk guard 20 GiB). (2) Committed tooling (`a03ea18`): detached run script with a hard
  provenance gate (repo SHAs, checkpoint/shim SHAs, image id, 52-yaml sha256sum -c), on-box
  D0 comparator, offline completion analyzer, 13 unit tests; ruff + pytest (153) +
  validate_docs green. (3) LAUNCHED the OFF baseline detached on sentinel-gpu
  (`sudo setsid nohup bash /tmp/iter46_run_off_baseline.sh`, log
  `/var/log/sentinel-iter46-off.log`): `I46_OFF_PROVENANCE_OK` at 23:54:11 UTC, first episode
  `scene-0013-easy-00 r1` started, client container up and stepping. RUN IN FLIGHT — done
  marker `I46_OFF_ALL_DONE`; do NOT relaunch while any Docker container is up.

  ### On I46_OFF_ALL_DONE (iteration 46 completion instructions — execute in this order)

  1. Check the log tail for `I46_OFF_ABORT_*` (disk / consecutive-failure aborts are
     interrupted runs with a resume point, not nulls) and confirm no Docker containers
     remain (`docker ps`); read `I46_OFF_D0_VERDICT=` from the log.
  2. Collect: `/datasets/nuscenes-full/hugsim/iter46_runs/` — copy `receipts.json`,
     `d0_comparison.json`, `d0_verdict.txt`, `frozen_scenarios.sha256`, `heavy_manifest.txt`,
     each `episodes <scenario>__r<n>/{eval.json,output.txt,episode_meta.json}` (and any
     `__failed` dirs), plus `/var/log/sentinel-iter46-off.log`, into
     `experiments/iter46_hugsim_off_baseline/proof-off/` (episodes under `proof-off/episodes/`;
     split any file >90 MB into `.part-*`). Heavy pickles/videos STAY on the box behind
     `heavy_manifest.txt`.
  3. Run the committed analyzer ONCE from the collected artifacts:
     `python3 experiments/iter46_hugsim_off_baseline/analyze_off_baseline.py
     --runs-root experiments/iter46_hugsim_off_baseline/proof-off/episodes-root
     --out .../proof-off/off_baseline_report.json` (point --runs-root at the directory that
     directly contains the `<scenario>__r<n>` dirs plus `d0_comparison.json`).
  4. Publish RESULT.md at full weight (pass or null per the analyzer's registered bars;
     plausibility note is context, NOT a bar; forbidden claims list is binding — OFF arm
     only), update README (row 46 + header/status/repo-map), CONTINUITY arc + shift log,
     regenerate HANDOFF.md; ruff + pytest + validate_docs green on every push. A pass
     authorizes ONLY the Stage-2 OFF-vs-released-union pre-registration.

- 2026-07-12: Claude (Fable 5) via delegated executor — diagnosed the iteration 46 first-launch
  abort and relaunched after a launcher-only amendment. The run stopped at 23:58:52 UTC via
  `I46_OFF_ABORT_CONSECUTIVE_FAILURES` (episodes 3-5 failed both attempts), but box evidence
  showed both causes were run-script/staging defects, not the registered crash/VRAM
  falsifier conditions: (1) 7 of 19 release scene zips nest under a top-level `nuscenes/`
  prefix, so `prep_scene` extracted scene-0038 (and would have extracted 0041/0051/0254/
  0418/0920/0930) to the wrong path — `cfg.yaml` never found; (2) the released scenario
  yamls reference actor assets as `<car>/postprocess/shadow.pth` while the staged 3DRealCar
  export is flat — HUGSIM's plan.py failed on `.../shadow.pth/wlh.json` for every
  actor-bearing (medium) scenario; upstream's own export_multiple_scenes.py strips exactly
  this suffix. No episode reached client stepping; no OOM. D0 completed before the abort:
  verdict STOCHASTIC (hd 0.1677/16 steps vs 0.1026/15 steps), so the branch is 26 scenarios
  x 2 runs. Amended run_off_baseline.sh only (temp-dir extraction keyed on cfg.yaml,
  idempotent `postprocess/shadow.pth -> ..` symlinks under 3DRealCar, resume-skip of
  completed episodes, carried D0 verdict, prior-launch evidence archival) and recorded the
  amendment in HYPOTHESIS.md — no frozen bar/scenario/provenance value changed; the two
  completed scene-0013-easy-00 episodes remain valid. Launch-1 log preserved into the
  collection root. RELAUNCHED detached on sentinel-gpu (same log
  /var/log/sentinel-iter46-off.log, done marker I46_OFF_ALL_DONE); the on-done completion
  instructions above apply unchanged, plus: commit BOTH launch logs under proof-off/ and
  the archived prior_launches/ defect evidence.
- 2026-07-12: Claude (Fable 5) via delegated executor — executed the committed iteration 46
  on-done flow after `I46_OFF_ALL_DONE` (03:43:53 UTC; no containers; no abort markers in
  launch 2). Collected the full evidence set from the box into
  experiments/iter46_hugsim_off_baseline/proof-off/ (52 episode dirs — 38 complete + 14
  __failed — both launch logs, receipts, D0 report, frozen-scenario manifest verified
  byte-identical to HYPOTHESIS.md, prior_launches defect archive, heavy manifest; transfer
  tar SHA-verified; no file needed a .part split), committed proof FIRST (d6b4030), ran the
  committed analyzer ONCE, and published the honest null `HUGSIM_OFF_BASELINE_NULL` at full
  weight (497cce1): C1 38/52, dual-failure falsifier fired on the seven load_HD_map
  medium-01 scenarios — diagnosed on the record as the unstaged nuScenes map-expansion pack
  (maps/expansion/*.json), NOT client instability (control: the flagless scene-0041-medium-01
  passed; zero failures after first client step across both launches). Pairing spread
  recorded for Stage-2 design: median |dHD| 0.0245 (19 pairs), heavy tail to 0.3056. README
  row 46 + header + status bullet + repo map + defensibility-arc nodes A45/A46 updated; ruff
  + pytest (153) + validate_docs green. Per the registered boundary the Stage-2
  pre-registration is NOT authorized — iteration 47 was NOT pre-registered; next step on this
  lane is a fresh completion pre-registration staging maps/expansion/ (iteration-28-class
  official download, ~last staging gap: zips nest, 3DRealCar flat, map expansion absent). BOX
  IDLE at exit (no Docker containers; iter46_runs kept on the data disk behind the committed
  heavy manifest).
- 2026-07-12: Claude (Fable 5) via delegated executor — iteration 47 opened as the named
  iteration-46 successor. (1) Pre-registered
  experiments/iter47_map_staging_and_off_completion/HYPOTHESIS.md (commit `ced26df`, committed
  ALONE, CI green): Stage A = official nuScenes map-expansion pack v1.3 staged
  iteration-28-class (redacted provenance, SHA/size proofs, 0 unsafe members, four-json bar);
  Stage B = ONLY the 14 failed load_HD_map -medium-01 episodes re-run under the carried
  stochastic D0 verdict with the iteration-46 resume-skip launcher, then C1/C2/C3 re-evaluated
  over all 52 (38 carried + 14 new, carried-integrity byte check against the committed iter46
  proof); iteration 46's null stands as published — completion is re-earned, not repaired.
  (2) Tooling committed (`ab7bf22`, CI green): staging script, 14-episode completion launcher,
  analyzer reusing the committed iter46 analyzer, new tests (164 total). (3) Stage A
  EXECUTED and PASSED on the first source (public bucket
  motional-nuscenes.s3.amazonaws.com): archive 398,535,531 bytes, SHA256
  `9dbc80a095b6b28d9b79fc9a43471a750dc92ca78c6d0db288fd92b34be5a144`, 13 members 0 unsafe,
  all four expansion jsons staged (8.2-16.2 MB each); receipts committed (`dc25fa0`).
  (4) Stage B LAUNCHED detached on sentinel-gpu at 05:18 UTC (log
  /var/log/sentinel-iter47-completion.log, done marker I47_OFF_COMPLETION_DONE):
  I47_OFF_PROVENANCE_OK (all frozen iter46 SHAs + map jsons + carried verdict + 38/38 carried
  episodes verified; 14 stale __failed dirs archived under prior_launches/20260712T051822Z);
  first formerly-failing episode scene-0038-medium-01 r1 verified PAST map loading (no
  FileNotFoundError) and INTO client stepping (hugsim_uniad_client up, 2 round-trip sent
  lines) before departure. RUN IN FLIGHT — do NOT relaunch while any Docker container is up.

  ### On I47_OFF_COMPLETION_DONE (iteration 47 completion instructions — execute in this order)

  1. Check the log tail for `I47_OFF_ABORT_*` (disk aborts are interrupted runs with a resume
     point, not nulls) and confirm no Docker containers remain (`sudo docker ps`).
  2. Collect from `/datasets/nuscenes-full/hugsim/iter46_runs/` into
     `experiments/iter47_map_staging_and_off_completion/proof-completion/`: the 14 new
     episode dirs' `eval.json`/`output.txt`/`episode_meta.json` (under
     `proof-completion/episodes/`, any `__failed` dirs included), `receipts_iter47.json` (as
     `proof-completion/receipts.json`), `heavy_manifest_iter47.txt`, and
     `/var/log/sentinel-iter47-completion.log` (as `proof-completion/i47-completion-run.log`);
     also produce `proof-completion/box_episode_hashes.txt` on the box first:
     `cd /datasets/nuscenes-full/hugsim/iter46_runs && sha256sum */eval.json */episode_meta.json`
     (all 52 dirs). Split any file >90 MB into `.part-*`. Commit proof FIRST.
  3. Run the committed analyzer ONCE from the committed artifacts:
     `python3 experiments/iter47_map_staging_and_off_completion/analyze_completion.py
     --new-episodes .../proof-completion/episodes --box-hashes
     .../proof-completion/box_episode_hashes.txt --out
     .../proof-completion/off_completion_report.json --markdown-out
     .../proof-completion/off_completion_episodes.md` (it assembles all 52 = 38 carried from
     the committed iter46 proof + 14 new, checks carried integrity, and applies the frozen
     bars + falsifiers including pairing over all 26 pairs).
  4. Publish RESULT.md at full weight (pass or null per the registered bars; forbidden-claims
     list is binding — OFF arm only), update README (row 47 + header/status/repo-map),
     CONTINUITY arc + shift log, regenerate HANDOFF.md; ruff + pytest + validate_docs green
     on every push. A pass authorizes ONLY the iteration-48 Stage-2 OFF-vs-released-union
     pre-registration; no Stage-2 run happens under iteration 47.
- 2026-07-12: Claude (Fable 5) via delegated executor — executed the committed iteration 47
  on-done flow after `I47_OFF_COMPLETION_DONE` (06:29:25 UTC; zero `I47_OFF_ABORT_*` markers;
  no containers). Collected the evidence set from the box into
  experiments/iter47_map_staging_and_off_completion/proof-completion/ (14 new episode
  artifact sets — zero __failed dirs — receipts, full run log, heavy_manifest_iter47,
  on-box SHA256 hashes over all 52 episode dirs; no file needed a .part split), committed
  proof FIRST (673bc0c), ran the committed analyzer ONCE from committed artifacts, and
  published `OFF_COMPLETION_PASS` at full weight: C1 52/52 (all 14 new episodes attempt 1,
  102-509 s), C2 pass, C3 pass with carried integrity 104/104 byte-identical, pairing
  falsifier not fired over all 26 pairs (median |dHD| 0.0251, heavy tail to 0.7419 on
  scene-0138-medium-01). Iteration 46's null stands; completion re-earned under the fresh
  bars, map-staging diagnosis confirmed by cure. README row 47 + header + net-summary +
  status bullet + repo map + arc node A47 (verdict class win) updated; CONTINUITY arc bullet
  added; ruff + pytest + validate_docs green. Per the registered boundary the pass
  authorizes ONLY the iteration-48 Stage-2 OFF-vs-released-union pre-registration. BOX IDLE
  at exit (no Docker containers; iter46_runs kept on the data disk behind
  heavy_manifest_iter47.txt).
