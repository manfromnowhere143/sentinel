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
- Iteration 48 concluded:
  experiments/iter48_hugsim_transfer_gate/RESULT.md, published as `TRANSFER_NULL` at full
  weight — THE transfer verdict of the second-benchmark line. The single registered
  104-episode HUGSIM Stage-2 run (26 scenarios x 2 runs x 2 arms, within-launch back-to-back
  pairing OFF r1 -> ON r1 -> OFF r2 -> ON r2 under the carried stochastic D0 verdict)
  completed 104/104 with 0 retries and 0 dual failures behind the full provenance gate
  (`I48_STAGE2_PROVENANCE_OK` 07:17:49, `I48_STAGE2_DONE` 16:29:13 UTC 2026-07-12; ~9.2
  GPU-h of episode walls, expected 8-16, ceiling 34.7). F1 void check passed FIRST and
  mechanically: monitor_patch_sha byte-identical to the committed
  client_patch_union_iter48.py, the seven NeuroNCAP-frozen parameters echoed in the receipts
  and in every params row of all 52 ON decision logs — zero retuning. Primary: mean paired
  HD-Score delta (ON − OFF) over 52 pairs = `−0.0166`, 95% scenario-clustered bootstrap CI
  `[−0.0551, +0.0255]` (26 clusters, 10k draws, seed 48) — includes zero; median delta
  `+0.0032`, CI `[−0.0467, +0.0178]`, no mean/median CI sign disagreement. The union
  demonstrably OPERATES on HUGSIM: 37/52 ON episodes intervened, 887 fired / 1,392 brake
  frames (26.9% pooled), 134 latch releases. F2 splat-noise mistuning NOT fired either
  direction (iteration 43's prediction lands as broad-but-not-constant firing; 2 episodes
  >80% brake frames — scene-0051-medium-00/01 r1 ran to the 400-step cap with RC roughly
  halved — pooled far under the 80% bar); F3 RC collapse NOT fired (mean paired RC delta
  `−0.0147`, bar `−0.30` — iteration 13's paralysis did not recur); F4 zero dual failures;
  F5 fresh OFF-OFF median |dHD| `0.0307` vs `0.15` bar (heavy tail to 0.4288,
  scene-0071-easy-00). Secondaries (mean paired deltas): NC `−0.0369`, DAC `+0.0069`, TTC
  `−0.0248`, comfort `+0.0652`, RC `−0.0147`. The registered answer: the NeuroNCAP benefit
  does not measurably transfer to HUGSIM easy+medium at this N; the null is the measured
  external-validity boundary of the released union. Forbidden claims held: no
  NeuroNCAP-equivalence, deployment, benchmark-ranking, robustness, or safety claim.
  The named hard-tier extension is iteration 49; any further successor requires a fresh
  pre-registration. Nothing further is authorized by this iteration.
- Iteration 49 concluded:
  experiments/iter49_hugsim_hard_tier_gate/RESULT.md, published as `TRANSFER_NULL` at full
  weight — the hard/extreme-tier collision-regime transfer answer. The single registered
  104-episode HUGSIM run (26 hard/extreme scenarios x 2 runs x 2 arms, within-launch
  back-to-back pairing OFF r1 -> ON r1 -> OFF r2 -> ON r2 under the carried stochastic D0
  verdict) reached `I49_HARD_DONE` at 23:12:34 UTC 2026-07-12 with `104/104` episodes
  complete, `0` retries, `0` failed dirs, no `I49_ABORT_*` markers, and no containers left
  up. Proof was collected from `sentinel-gpu` into `proof-hard/` and committed FIRST
  (`2eb0c81`) before the analyzer ran. F1 void check passed mechanically: receipts'
  `monitor_patch_sha` is byte-identical to the committed iteration-48 patch copy
  (`6b39fd79...`), and all seven NeuroNCAP-frozen parameters match receipts and every ON
  decision-log row. Primary: mean paired HD-Score delta (ON - OFF) over 52 pairs =
  `-0.0089`, 95% scenario-clustered bootstrap CI `[-0.0438, +0.0203]` (26 clusters, 10k
  draws, seed 49) — includes zero; median `+0.0011`, CI `[-0.0077, +0.0105]`; no
  mean/median CI sign disagreement. The union operates on the harder tiers: `40/52` ON
  episodes intervened, `275` fired frames, `526` brake frames (`22.3%` pooled), `58`
  releases, and `0` step-cap episodes. F2 splat-noise mistuning NOT fired, F3 RC collapse
  NOT fired (mean paired RC delta `-0.0403`, bar `-0.30`), F4/F5/F6/F7 not fired, and the
  fresh hard/extreme OFF-OFF median |dHD| was `0.0113` vs the `0.15` bar. Descriptive tier
  split only: hard mean `+0.0011`, extreme mean `-0.0189` — no tier claim. Iteration 50's
  frozen P1 resolves Branch B REFUTED: `51/52` iteration-49 OFF episodes had primary
  collision opportunity (`nc_min < 1.0`), but the transfer CI includes zero, so the transfer
  failure is real, not opportunity-scarce. Forbidden claims held: no NeuroNCAP-equivalence,
  deployment, benchmark-ranking, monitor-robustness, hard-vs-extreme, or safety claim.
  Successors require fresh pre-registration.
- Iteration 50 concluded:
  experiments/iter50_collision_opportunity_audit/RESULT.md, published as
  `OPPORTUNITY_AUDIT_COMPLETE` — an entirely offline collision-opportunity audit over
  committed evidence only (zero GPU, zero gcloud), pre-registered ALONE (fbd1b3d) while
  iteration 49's run was in flight and UNREAD, with the frozen prediction P1 registered
  before any iteration-49 outcome data existed in-repo. Integrity gates all passed (p14 tar
  399 OFF / 400 best metrics over 20 pairs with the side-0921 n=19 exception detected;
  published iteration-48 mean reproduced to 1e-9; 52+52 HUGSIM OFF episodes read with the
  frozen nc fields fully supported). A1 (NeuroNCAP) CONFIRMED: Spearman rho `+0.7003`, 95%
  bootstrap CI `[+0.3909, +0.8762]` (10k draws, seed 50) between per-pair OFF collision rate
  (`any_collide@0.0s`) and per-pair benefit; strata means `+0.989` (12 pairs at rate >= 0.5)
  vs `+0.263` (8 below) — the NeuroNCAP benefit is an opportunity-conversion effect. A2
  (HUGSIM): `40/52` (76.9%) of iteration-48's OFF episodes carry primary collision
  opportunity (frozen definition: eval.json `nc_min < 1.0` over top-level nc and all
  details steps; measured binary 0/1), and the independent iteration-46/47 52-episode
  baseline corroborates at exactly `40/52`; against the frozen 0.25 bar the iteration-48
  `TRANSFER_NULL` is CLASSIFIED `OPPORTUNITY_PRESENT_NULL` — opportunity was abundant and
  the union's interventions converted none of it (descriptive: with-opportunity paired
  deltas mean `+0.0013`, without `−0.0765`). The classification does NOT upgrade the null.
  P1 (binding on whoever publishes iteration 49's RESULT, quoted verbatim there and in the
  RESULT): opportunity fraction >= 13/52 in iter49's OFF arm + positive CI excluding zero =
  CONFIRMED (benefit reappears with opportunity); >= 13/52 + CI including zero or below =
  REFUTED and the transfer failure is REAL, not opportunity-scarce; < 13/52 = NOT TESTABLE
  at the hard tier. No new safety/transfer/deployment claim; classification and prediction
  only; any further opportunity-conditioned analysis needs a fresh pre-registration.
- Iteration 51 concluded:
  experiments/iter51_hugsim_failure_taxonomy/RESULT.md, published as `TAXONOMY_COMPLETE` —
  an entirely offline post-result taxonomy over committed iteration-48/49 HUGSIM proof only
  (zero GPU, zero gcloud, zero box reads), pre-registered ALONE (`778304c`) after the
  transfer nulls were already public. Analyzer/tests were committed separately (`71abe6d`)
  and then run ONCE over the committed artifacts. Infrastructure passed: 104 paired HUGSIM
  transfer episodes classified, both transfer-report point means reproduced exactly, and
  iteration-49 P1 cross-check matched `51` recomputed vs `51` recorded. Combined category
  counts: persistent_collision_late_by_proxy `34`, persistent_collision_early_by_proxy
  `33`, persistent_collision_no_brake `18`, induced_collision `7`,
  clean_no_off_opportunity `6`, converted_collision_no_material_gain `4`, and
  converted_collision_material_gain `2`. The frozen dominance rule returned
  `mixed_taxonomy` (`34/91 = 0.374` of OFF-opportunity pairs, below the 0.40 bar), not a
  single-cause explanation. Main scientific content: only `6/91` OFF-opportunity pairs
  converted from collision to no collision, and only `2` of those cleared the descriptive
  material-gain deadband; `85/104` combined pairs remained collision-persistent. In
  iteration 49 hard/extreme specifically, `51/52` opportunity pairs produced `0/52`
  conversions; AttackPlanner scenes lean late-by-proxy (`15/30`), non-AttackPlanner
  hard/extreme scenes lean early-by-proxy (`10/21`). No new safety/transfer/deployment/
  robustness claim; timing labels are descriptive proxies only because OFF/ON HUGSIM
  trajectories are stochastic. Next mature line is a fresh mechanism-cause audit, not
  retuning or an expanded-N transfer run by default.
- Iteration 52 concluded:
  experiments/iter52_hugsim_on_collision_timing_audit/RESULT.md, published as
  `TIMING_AUDIT_COMPLETE` — an offline post-result timing audit over committed iteration
  48/49 HUGSIM proof only (zero GPU, zero gcloud, zero box reads), with a pre-freeze
  prototype timing probe disclosed in the HYPOTHESIS rather than hidden. Analyzer/tests
  committed separately (`b1721ca`) and run ONCE over committed artifacts. Infrastructure
  passed: 104 pairs read and ON-collision count cross-checked against iteration 51 exactly
  (`92` vs `92`). Combined ON-collision timing bins: post_collision_first_brake `35`,
  long_lead_brake `26`, no_brake_no_surface_proxy `22`, short_lead_brake `9`,
  no_brake_surface_proxy_present `0`, unknown_collision_time `0`. Family split:
  absent_or_post_collision_brake `57/92`, pre_collision_brake `35/92`. Dataset split:
  iter48 ON collisions `40` (absent/post `24`, pre `16`); iter49 ON collisions `52`
  (absent/post `33`, pre `19`). All 22 no-brake ON-collision cases had zero frozen
  TTC/CPA surface-proxy rows (`min_ttc <= 2.5` and `min_cpa <= 1.5` never simultaneous),
  so they are surface misses by this scalar proxy. But `35/92` ON-collision cases braked
  before collision, including `26` long-lead cases, so pure "brake earlier" is insufficient
  as the default repair story. No actor-identity, safety/transfer/deployment/robustness,
  benchmark, real-world, monitor-performance, or retuning claim; the TTC/CPA surface is a
  scalar proxy and not the full firing predicate.
- Iteration 53 concluded:
  experiments/iter53_hugsim_first_fire_channel_audit/RESULT.md, published as
  `FIRST_FIRE_CHANNEL_COMPLETE` — an offline post-result first-fire-channel audit over
  committed iteration 48/49 HUGSIM proof only (zero GPU, zero gcloud, zero box reads), with
  the pre-freeze patch inspection and prototype aggregate disclosed in the HYPOTHESIS rather
  than hidden. Analyzer/tests were committed separately and run ONCE over committed artifacts.
  Infrastructure passed: `104` pairs read, pair count cross-checked against iteration 52
  exactly (`104` vs `104`), timing-bin mismatches `0`, and unreconstructable first-fire
  channels `0`. Combined first-fire channels over all `104` ON-arm pairs: ttc_only `40`,
  cpa_only `36`, no_fire `27`, both `1`. Over the `92` ON-collision episodes: ttc_only `36`,
  cpa_only `33`, no_fire `22`, both `1`. Over the `35` pre-collision-fire ON-collision
  episodes: cpa_only `19`, ttc_only `16`, both/no_fire/unreconstructable `0`. This shows the
  pre-collision-fire persistent family is split across both sides of the released OR predicate,
  not one bad union branch. No actor-identity, safety/transfer/deployment/robustness, benchmark,
  real-world, monitor-performance, HUGSIM-equivalence, or retuning claim; next mature line is
  object/path geometry and provenance under a fresh pre-registration.
- Iteration 54 concluded:
  experiments/iter54_hugsim_provenance_support_audit/RESULT.md, published as
  `PROVENANCE_SUPPORT_NULL` — an offline support audit over committed iteration 48/49 HUGSIM
  proof only (zero GPU, zero gcloud, zero box reads), with the pre-freeze schema/patch
  inspections disclosed in the HYPOTHESIS rather than hidden. Analyzer/tests were committed
  separately and run ONCE over committed artifacts. Infrastructure passed: `104` pairs read,
  pair count cross-checked against iteration 53 exactly (`104` vs `104`), channel mismatches
  `0`, timing mismatches `0`, and argmin reconstruction failures `0`. Monitor-side first-fire
  provenance is reconstructable from committed logs: unique_ttc_object `40`,
  unique_cpa_object `36`, both_distinct_objects `1`, no_fire `27`; among `92` ON-collision
  episodes: unique_ttc_object `36`, unique_cpa_object `33`, both_distinct_objects `1`,
  no_fire `22`; among `35` pre-collision-fire ON-collision episodes: unique_cpa_object `19`,
  unique_ttc_object `16`. Collision-actor identity is not logged in the committed HUGSIM evals:
  `0/104` actor-supported, `0/92` among ON-collision episodes; eval schemas expose scalar metric
  keys only (`c`, `dac`, `nc`, `pdms`, `ttc`, plus top-level `hdscore`, `rc`, `details`). No
  actor-identity, actor-match, safety/transfer/deployment/robustness, benchmark, real-world,
  monitor-performance, HUGSIM-equivalence, or retuning claim. A later actor-match line needs
  fresh instrumentation.
- Iteration 55 concluded:
  experiments/iter55_hugsim_collision_instrumentation_source_audit/RESULT.md, published as
  `COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE` — a source-only audit over a read-only HUGSIM
  checkout detached at the frozen SHA `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`. No GPU,
  gcloud, simulator launch, HUGSIM episode, source edit, metric edit, or box read occurred.
  The analyzer verified checkout identity, scanned 153 source-like files, found 103 candidates,
  and mapped future instrumentation candidates to `sim/utils/score_calculator.py` and
  `closed_loop.py`. Labels: metric source identified, collision geometry source identified,
  actor identity available in source, instrumentation point supported, source map not
  insufficient. No actor attribution, actor-match, safety/transfer/deployment/robustness,
  benchmark, real-world, HUGSIM-equivalence, or retuning claim. A later actor-match line still
  needs a fresh no-metric-change instrumentation pre-registration and proof that `nc`,
  HD-Score, scenarios, Sentinel thresholds, and planner behavior are unchanged.
- Iteration 56 concluded:
  experiments/iter56_hugsim_provenance_instrumentation_patch/RESULT.md, published as
  `INSTRUMENTATION_PATCH_DESIGN_NULL` — a source-only patch-design gate over the frozen HUGSIM
  checkout. The patch draft added a top-level `collision_provenance` sidecar in
  `sim/utils/score_calculator.py`; the verifier confirmed SHA match, clean patch application,
  allowed changed file, required provenance fields, and Python compile. The static guard failed
  on `if score_nc == 0.0:` because the frozen guard treats changed lines containing `score_nc =`
  as metric/control-sensitive. No patch is authorized for a run. No GPU, gcloud, simulator,
  planner process, actor attribution, actor-match, safety/transfer/deployment/robustness,
  benchmark, real-world, HD-Score-execution, or retuning claim.
- Iteration 57 concluded:
  experiments/iter57_hugsim_patch_guard_refinement/RESULT.md, published as
  `PATCH_GUARD_REFINEMENT_COMPLETE` — a refined static verifier over the byte-identical iteration
  56 patch SHA256 `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`.
  The verifier confirmed patch SHA match, source SHA match, clean patch application, allowed
  changed file, required provenance fields, no metric/control assignment changes, no control-call
  changes, no provenance inside scalar `score_list` rows, and Python compile. No HUGSIM run,
  metric execution, actor attribution, actor-match, safety/transfer/deployment/robustness,
  benchmark, real-world, HD-Score-invariance, or retuning claim. Any run still needs a fresh
  pre-registration.
- Iteration 58 concluded:
  experiments/iter58_hugsim_provenance_instrumented_canary/RESULT.md, published as
  `PROVENANCE_CANARY_COMPLETE` — the first real HUGSIM execution of the byte-bound provenance
  patch. The fresh pre-registration authorized exactly two episodes:
  `scene-0013-hard-00` OFF r1 then ON r1. Both completed on the first attempt, both had
  `nc_min = 0.0`, both emitted top-level `collision_provenance` lists (counts `11` and `13`),
  scalar top-level metrics remained present, `details` rows stayed scalar-only, and the ON
  episode carried the released-union decision log. This retires only the
  instrumentation-execution blocker. No actor-match, HD-Score-invariance,
  safety/transfer/deployment/robustness/benchmark, or retuning claim.
- Iteration 59 concluded:
  experiments/iter59_hugsim_actor_match_audit/RESULT.md, published as
  `ACTOR_MATCH_AUDIT_COMPLETE` — a bounded eight-episode Sentinel-ON actor-match support audit
  using the same byte-bound HUGSIM provenance patch. All eight episodes completed first-attempt
  with intact scalar schemas, scalar-only `details`, top-level `collision_provenance`, and ON
  decision logs. Support labels were `classifiable_foreground` `3`, `no_monitor_fire` `2`,
  `post_collision_fire` `2`, and `background_collision_only` `1`. All three classifiable
  foreground rows were `actor_mismatch` by the frozen bridge, with distances `15.43 m`,
  `21.99 m`, and `37.04 m`. This is a bounded mechanism-cause audit only: no population
  mismatch-rate, repair, safety/transfer/deployment/robustness/benchmark, or retuning claim.
- Iteration 60 concluded:
  experiments/iter60_actor_bridge_sensitivity/RESULT.md, published as
  `BRIDGE_AMBIGUOUS_NULL` — an offline bridge-sensitivity audit over only the three
  iteration-59 classifiable foreground rows. It launched no GPU work and read no live box state.
  The analyzer cross-checked the iteration-59 verdict and exactly three classifiable rows, then
  evaluated `16` frozen bridge variants per row (first-fire vs propagated position, two axis
  orders, four sign combinations). No row became `bridge_match_possible`; two rows remained
  `robust_mismatch`, and `ttc_extreme_b` became `bridge_ambiguous_possible` at `5.6649 m`.
  This narrows iteration 59: no robust all-row mismatch, actor-causality, repair,
  safety/transfer/deployment/robustness/benchmark, population-rate, or retuning claim.
- Iteration 61 concluded:
  experiments/iter61_monitor_object_surface_audit/RESULT.md, published as
  `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE` — an offline object-surface audit over the same
  three iteration-59 classifiable foreground rows. It launched no GPU work and read no live box
  state. The analyzer cross-checked iteration-59 and iteration-60, then evaluated every
  first-fire monitor object against every eligible foreground provenance row under the frozen
  bridge grid (`2,384` variants). Two rows were `no_monitor_object_support`; `ttc_extreme_b`
  had a non-triggering object match (`object_id=16`, `2.0686 m`) while the triggering object
  remained ambiguous (`object_id=1`, `5.6649 m`). No actor-causality, repair, population-rate,
  safety/transfer/deployment/robustness/benchmark, or retuning claim.
- Iteration 62 concluded:
  experiments/iter62_nontrigger_ranking_audit/RESULT.md, published as
  `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE` — a one-row offline selector audit for the iteration-61
  matched non-trigger object. It launched no GPU work and read no live box state. The analyzer
  reconstructed first-fire CPA/TTC metrics for all 9 objects in `ttc_extreme_b`. The matched
  non-trigger object (`object_id=16`) was visible but subthreshold: `min_cpa=22.7648 m`, CPA
  rank `9/9`, no valid TTC. The trigger (`object_id=1`) was TTC-only with `ttc=2.1303 s` and
  TTC rank `1`. No actor-causality, repair, population-rate, safety/transfer/deployment/
  robustness/benchmark, or retuning claim.
- Iteration 63 concluded:
  experiments/iter63_temporal_emergence_audit/RESULT.md, published as
  `TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE` — a one-object temporal audit for the same matched
  non-trigger object. It launched no GPU work and read no live box state. Before the first
  eligible foreground collision timestamp (`7.25 s`), `object_id=16` was present in `13/29`
  pre-contact monitor frames, had zero hazard frames, zero borderline frames, minimum CPA
  `12.1690 m`, and no valid TTC. Contact-time evidence also stayed subthreshold. This closes
  the late-hazard-emergence explanation for that row only. No actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark, or retuning claim.
- Iteration 64 concluded:
  experiments/iter64_unsupported_temporal_surface_audit/RESULT.md, published as
  `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE` — an offline temporal object-surface audit for the two
  iteration-61 rows that had no first-fire object support. It launched no GPU work and read no
  live box state. Expanding to all pre-contact monitor objects yielded matches in both rows:
  `ttc_extreme_short` best distance `1.6718 m` (`object_id=2`, decision `0.25 s`, foreground
  `2.75 s`) and `cpa_medium_b` best distance `0.4325 m` (`object_id=6`, decision `2.25 s`,
  foreground `6.50 s`). This shifts the mechanism question to first-fire/provenance timing, not
  total pre-contact object absence. No actor-causality, repair, population-rate,
  safety/transfer/deployment/robustness/benchmark, or retuning claim.
- Iteration 65 concluded:
  experiments/iter65_temporal_alignment_audit/RESULT.md, published as
  `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE` — an offline temporal/provenance alignment audit
  for the two iteration-64 best pre-contact monitor-object matches. It launched no GPU work and
  read no live box state. Both matched objects were present but subthreshold at their matched
  timestamps: `ttc_extreme_short` `object_id=2` at decision `0.25 s` had min CPA `12.7240 m`
  and TTC `3.5763 s`; `cpa_medium_b` `object_id=6` at decision `2.25 s` had min CPA
  `9.3179 m` and no valid TTC. One matched object later equals the first-fire object; the other
  does not. No actor-causality, repair, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or retuning claim.
- Iteration 66 concluded:
  experiments/iter66_matched_object_timeline_audit/RESULT.md, published as
  `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE` — an offline target-object temporal surface audit for
  the two iteration-65 matched objects. It launched no GPU work and read no live box state.
  `ttc_extreme_short` `object_id=2` was present in `7/10` pre-contact frames, had TTC-borderline
  frames at `0.25 s` and `0.50 s`, and became an active TTC hazard exactly at first fire
  (`1.50 s`). `cpa_medium_b` `object_id=6` was present in `13/25` pre-contact frames with zero
  active or borderline frames, min CPA `7.9669 m`, and no valid TTC. No actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or
  retuning claim.
- Iteration 67 concluded:
  experiments/iter67_trigger_target_bridge_audit/RESULT.md, published as
  `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE` — an offline trigger/target bridge audit for the two
  iteration-66 rows. It launched no GPU work and read no live box state. `ttc_extreme_short` is
  same-object target/trigger (`object_id=2`), with full-window bridge match `1.6718 m` but
  first-fire trigger distance `6.9272 m`. `cpa_medium_b` is split-object: target `object_id=6`
  has bridge match `0.4325 m`, trigger `object_id=1` has later full-window bridge match
  `2.8332 m`, but first-fire trigger distance is unsupported at `19.6983 m`. No
  actor-causality, repair, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or retuning claim.
- Iteration 68 concluded:
  experiments/iter68_fire_time_bridge_decomposition/RESULT.md, published as
  `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE` — an offline fire-time bridge decomposition
  audit for the two iteration-67 first-fire trigger objects. It launched no GPU work and read no
  live box state. `ttc_extreme_short` trigger `object_id=2` has best bridge support before first
  fire (`0.25 s`, `1.25 s` before fire; distance improves `6.9272 m` -> `1.6718 m`).
  `cpa_medium_b` trigger `object_id=1` has best bridge support after first fire (`2.25 s`,
  `2.00 s` after fire; distance improves `19.6983 m` -> `2.8332 m`). No actor-causality,
  repair, population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  or retuning claim.
- Iteration 69 concluded:
  experiments/iter69_hugsim_mechanism_taxonomy/RESULT.md, published as
  `HUGSIM_MECHANISM_TAXONOMY_COMPLETE` — an offline evidence synthesis over the eight
  iteration-59 HUGSIM ON actor-match rows. It launched no GPU work and read no live box state.
  All eight rows were classified: five structural labels were preserved (`no_monitor_fire` 2,
  `post_collision_fire` 2, `background_collision_only` 1), and all three classifiable foreground
  rows were refined as `nontrigger_visible_never_hazard`,
  `same_object_late_fire_after_best_bridge`, and
  `split_object_visible_never_active_fire_before_best_bridge`. No actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- Iteration 70 concluded:
  experiments/iter70_hugsim_structural_timing_audit/RESULT.md, published as
  `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE` — an offline structural timing/support audit over
  the five iteration-69 structural rows. It launched no GPU work and read no live box state. The
  five rows split into two `foreground_present_surface_silent` rows, two
  `foreground_present_late_fire` rows, and one `foreground_absent_background_only` row. Both
  late-fire rows first fire `1.75 s` after first foreground timestamp. No actor-causality,
  repair, population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- Iteration 71 concluded:
  experiments/iter71_hugsim_surface_silent_margin_audit/RESULT.md, published as
  `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE` — an offline descriptive margin audit over the two
  iteration-70 foreground-present surface-silent rows. It launched no GPU work and read no live
  box state. Both rows classify `surface_silent_far_margin`: `mixed_extreme` closest CPA margin
  is `+2.6062 m`; `nofire_hard_control` closest valid TTC margin is `+3.4560 s` and closest CPA
  margin is `+6.4779 m`. No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 72 concluded:
  experiments/iter72_hugsim_late_fire_prefire_margin_audit/RESULT.md, published as
  `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE` — an offline descriptive prefire margin audit over
  the two iteration-70 foreground-present late-fire rows. It launched no GPU work and read no live
  box state. Both rows were near a frozen trigger surface before foreground contact but did not
  cross before contact: `both_distinct_extreme` was near CPA (`+0.5355 m`), and `ttc_medium_a`
  was near TTC (`+0.7742 s`). Both first fires remained `+1.75 s` after first foreground
  timestamp. No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 73 concluded:
  experiments/iter73_hugsim_margin_transition_audit/RESULT.md, published as
  `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE` — an offline four-row margin-transition audit over
  the foreground-present structural HUGSIM rows. It launched no GPU work and read no live box
  state. The two surface-silent rows are `silent_far_never_active`; the two late-fire rows are
  `late_prefire_near_postcontact_active`; both late-fire rows first cross an active surface
  `+1.75 s` after first foreground timestamp. No actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- Iteration 74 concluded:
  experiments/iter74_hugsim_late_fire_delay_barrier/RESULT.md, published as
  `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE` — an offline delay-barrier audit over the two
  iteration-70 foreground-present late-fire rows. It launched no GPU work and read no live box
  state. Both rows classify `cross_channel_late_activation`: `both_distinct_extreme` is CPA-near
  before contact and TTC-active after contact, while `ttc_medium_a` is TTC-near before contact
  and CPA-active after contact. Both first active crossings remain `+1.75 s` after first
  foreground timestamp. No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 75 concluded:
  experiments/iter75_hugsim_cross_channel_object_handoff/RESULT.md, published as
  `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE` — an offline object-handoff audit over the two
  iteration-74 cross-channel late-fire rows. It launched no GPU work and read no live box state.
  Both rows classify `object_switch_cross_channel_handoff`: `both_distinct_extreme` switches
  responsible monitor object `5` -> `9`, and `ttc_medium_a` switches object `6` -> `24`.
  No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 76 concluded:
  experiments/iter76_hugsim_switch_foreground_bridge/RESULT.md, published as
  `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE` — an offline foreground-bridge audit over
  the two iteration-75 object-switch rows. It launched no GPU work and read no live box state.
  Both rows classify `no_foreground_bridge_support`: neither the pre-contact near object nor the
  post-contact active object reaches the frozen `<=3 m` match band or `(3,6] m` ambiguous band
  against HUGSIM foreground collision provenance. Best distances remain `8.1239-13.4483 m`.
  No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 77 concluded:
  experiments/iter77_hugsim_event_object_set_bridge/RESULT.md, published as
  `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE` — an offline foreground-bridge audit over
  the full logged object sets at the iteration-75 pre/active event rows. It launched no GPU work
  and read no live box state. `both_distinct_extreme` has pre-event ambiguous support via object
  `9` at `3.6899 m`, while active-event set remains no-support. `ttc_medium_a` has match support
  in both event-row object sets via object `10` at `1.1245 m` and `1.2931 m`. This is selected
  hazard-object versus object-set support evidence only. No actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- Iteration 78 concluded:
  experiments/iter78_hugsim_support_object_ranking/RESULT.md, published as
  `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE` — an offline ranking audit over the three
  iteration-77 foreground-supported full-object-set events. It launched no GPU work and read no
  live box state. All three fixed support events classify
  `support_object_nonselected_subthreshold`: support objects `9`, `10`, and `10` differ from
  selected event objects `5`, `6`, and `24`, with min CPA values `21.6343 m`, `17.2764 m`, and
  `13.5578 m` and no finite TTC. This is support-object ranking evidence only. No actor-causality,
  repair, threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- Iteration 79 concluded:
  experiments/iter79_hugsim_selected_surface_decomposition/RESULT.md, published as
  `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE` — an offline selected-vs-support surface
  audit over the three iteration-78 fixed events. It launched no GPU work and read no live box
  state. Two selected objects are borderline (`object_id=5` CPA `2.0355 m`, `object_id=6` TTC
  `3.2742 s`) and one selected object is active (`object_id=24` CPA `1.2791 m`), while all
  foreground-supported objects remain subthreshold. This is selected-vs-support surface evidence
  only. No actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- Iteration 80 concluded:
  experiments/iter80_hugsim_selected_all_provenance_bridge/RESULT.md, published as
  `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE` — an offline all-provenance bridge audit
  over the three iteration-79 selected active/borderline objects. It launched no GPU work and
  read no live box state. All eligible logged provenance rows in the fixed episodes are
  foreground (`30/30`), and all three selected objects classify
  `selected_all_provenance_no_support`; best distances are `13.4483 m`, `8.1239 m`, and
  `8.4408 m`. This is selected-object provenance-bridge evidence only. No actor-causality,
  repair, threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- Iteration 81 concluded:
  experiments/iter81_hugsim_support_object_temporal_surface/RESULT.md, published as
  `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE` — an offline temporal surface audit over the two
  iteration-78 foreground-supported support objects. It launched no GPU work and read no live box
  state. `both_distinct_extreme` support object `9` later becomes borderline at `5.5 s` and
  active at `7.0 s` after first foreground support at `5.25 s`; `ttc_medium_a` support object
  `10` remains visible across `15` frames with zero active or borderline frames. This is
  support-object temporal surface evidence only. No actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- Iteration 82 concluded:
  experiments/iter82_hugsim_support_surface_bridge_cooccurrence/RESULT.md, published as
  `HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE` — an offline co-occurrence audit over
  the two iteration-81 support objects. It launched no GPU work and read no live box state. Both
  support objects have foreground bridge support. `both_distinct_extreme` object `9` has
  same-frame bridge+surface co-occurrence only at the borderline level (`1` borderline+bridge
  frame, zero active+bridge frames; best surface bridge `0.9876 m`). `ttc_medium_a` object `10`
  has bridge support in `15/15` present frames and never reaches active or borderline surface.
  This is support-object surface/provenance co-occurrence evidence only. No actor-causality,
  repair, threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- Iteration 83 concluded:
  experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/RESULT.md, published as
  `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE` — an offline channel decomposition over
  bridge-supported support-object frames. It launched no GPU work and read no live box state.
  Across `18` bridge-supported frames there are zero active frames. `both_distinct_extreme`
  object `9` is `bridge_supported_borderline_ttc_only` (`3` bridge-supported frames, `1`
  borderline, closest active TTC margin `+2.2761 s`, closest active CPA margin `+17.6718 m`).
  `ttc_medium_a` object `10` is `bridge_supported_subthreshold_no_finite_ttc` (`15`
  bridge-supported frames, zero finite TTC, closest active CPA margin `+5.7464 m`). This is
  bridge-supported surface-miss decomposition evidence only. No actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- Iteration 84 concluded:
  experiments/iter84_hugsim_selected_support_arbitration/RESULT.md, published as
  `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE` — an offline selected/support
  arbitration decomposition over the three fixed iteration-79 event rows. It launched no GPU work
  and read no live box state. All three rows classify `selected_surface_support_bridge_split`:
  selected objects have lower CPA and better CPA rank in `3/3`, selected bridge support in `0/3`,
  support bridge support in `3/3`, and one selected object has finite TTC while its support object
  has no finite TTC. This is selected/support arbitration evidence only. No actor-causality,
  repair, threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, real-world/first-responder behavior, or retuning claim.
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
  remaining fallback: CATPlan authors). BREAKTHROUGH 2026-07-12 ~19:54 local: Caesar REPLIED
  "Nice work... I am happy to endorse you. Do send me the link" (he noted our mail hit his
  spam folder — root-caused to dev@alfred-ai.app lacking a DKIM record; all sends now go from
  the fully authenticated daniel@aweblabs.ai). Threaded reply with the direct link
  https://arxiv.org/auth/endorse?x=V76QK4 sent the same hour from daniel@aweblabs.ai, Gmail id
  19f574aed0b5f451. AWAITING endorsement confirmation; then Daniel submits at arxiv.org/user;
  package = docs/paper/sentinel-arxiv-submission.tar.gz.

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
- 2026-07-12: Claude (Fable 5) via delegated executor — iteration 48 pre-registered per the
  iteration-47 authorization: experiments/iter48_hugsim_transfer_gate/HYPOTHESIS.md committed
  ALONE (889770c, CI green). Frozen: monitored arm = released union at the client-side
  interception point in UniAD_SIM's e2e loop (plan + tracked boxes/scores from the same
  forward pass, velocities via cross-frame tracking as on NeuroNCAP), monitor params EXACTLY
  the NeuroNCAP-frozen values (cpa 1.5 / ttc 2.5 / min-closing 3.0 / max-gap 30.0 /
  min-score 0.3 / release-K 4 / dt 0.5; any retuning = VOID, falsifier F1); iter45 shim
  carried; same 26 scenarios x N=2 both arms, within-launch back-to-back OFF/ON pairing
  (per-scenario order OFF r1 -> ON r1 -> OFF r2 -> ON r2) per the carried stochastic D0
  verdict with the iter46/47 measured spread as the noise floor; frozen paired analysis =
  scenario-clustered bootstrap (10,000 draws, seed 48) on the 52 paired HD deltas, primary =
  mean-delta CI, median-delta CI reported alongside as the stated heavy-tail treatment;
  secondary = NC/DAC/TTC-COM terms + route completion (over-braking visibility, F3 RC-collapse
  falsifier; F2 splat-tracking-noise over-firing falsifier connects iter43's finding, fires
  constantly >80% brake frames or never 0 fired); budget arithmetic frozen (104 episodes,
  ~35 GPU-h state ceiling, ~8-16 expected); forbidden claims: no NeuroNCAP-equivalence, no
  deployment/safety claim; pass OR null publishes at full weight — THE transfer verdict. NO
  monitor patch built, NO tooling, NO launch under this window; next window starts at
  protocol step 2. BOX IDLE (no Docker containers).
- 2026-07-12: Claude (Fable 5) via delegated executor — iteration 48 protocol steps 2-3
  executed on the committed pre-registration (889770c). (1) Tooling committed (ff3772c, CI
  green): client-side monitor patch `client_patch_union_iter48.py` — the released union
  ported EXACTLY at the pre-registered UniAD_SIM interception point
  (`tools/closeloop/e2e.py`, after the model forward, before the plan-pipe write; plan +
  tracked `boxes_3d`/`scores_3d`/`track_ids` from the SAME forward pass; velocities by
  cross-frame world-position differencing keyed on track id via the client's own l2g
  transform; HUGSIM timestamps are seconds and are used unit-correctly; latched all-zeros
  committed-stop override; threat-cleared release K=4; the seven frozen params are baked in
  as defaults and `tools/e2e.sh` forwards ONLY `SENTINEL_ENABLED` into the container, so no
  parameter override can reach the monitor — F1 discipline); env-gated `SENTINEL_ENABLED`
  so the OFF arm runs the identical patched binary path unpatched-in-behavior; per-frame
  decision logging (`SENTINEL_I48_DECISION` lines in output.txt + full-input JSONL per ON
  episode; no printed token contains the substring 'sent' — the step counter greps for it);
  104-episode launcher `run_transfer_gate.sh` (per-scenario within-launch order
  OFF r1 -> ON r1 -> OFF r2 -> ON r2, resume-skip, retry-once,
  3-consecutive-dual-failure abort, 20 GiB disk guard, provenance gate incl. patch SHA +
  shim + 52-yaml manifest + map jsons + carried stochastic D0, fresh collection root
  `iter48_runs`, per-episode arm-labelled markers); offline paired analyzer
  `analyze_transfer.py` (F1 void check FIRST, K1/K2 bars, scenario-clustered bootstrap
  10,000 draws seed 48, mean-delta CI primary + median-delta CI heavy-tail treatment,
  NC/DAC/TTC/comfort + RC secondaries, F2/F3/F4/F5) + 14 unit tests (178 total green).
  (2) Pre-launch ON-arm SMOKE (disclosed, non-scheduled, excluded from all analysis; the
  pre-registration has no smoke provision — see smoke-evidence/SMOKE_NOTE.md):
  scene-0013-easy-00 with SENTINEL_ENABLED=1 into the separate `iter48_smoke` root — load
  marker `enabled=1` printed, 15 decision lines + 15 full-input JSONL rows with the frozen
  params echoed, zero-fire logged cleanly (no object inside the frozen margins on this easy
  scene), RC=0, finite HD; evidence committed (bddb6f1); nothing tuned. (3) LAUNCHED the
  single registered 104-episode run detached on sentinel-gpu at 07:17:38 UTC:
  `I48_STAGE2_PROVENANCE_OK` 07:17:49 (receipts.json records monitor_patch_sha
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c` — byte-identical to the
  committed patch — e2e_py_patched_sha `23cce8a2…`, e2e_sh_patched_sha `8b404adc…`, frozen
  param echo, carried stochastic D0); first pair verified before departure — OFF r1
  hd=0.1677 steps=16 (114 s, attempt 1, marker `enabled=0`) and ON r1 hd=0.1056 steps=15
  (113 s, attempt 1, marker `enabled=1`, 15 decision lines/JSONL rows, 0 brake frames on
  this scene; per-pair deltas are NOT interpretable alone per the registered noise floor).
  RUN IN FLIGHT — log `/var/log/sentinel-iter48-stage2.log`, done marker `I48_STAGE2_DONE`;
  ETA: at the iteration-46/47 median ~250 s/episode the remaining 102 episodes are ~7.1 h
  (done ~14:30-15:30 UTC 2026-07-12); observed first-pair pace ~114 s/episode would finish
  ~10:33 UTC; registered ceiling 104 x 1200 s = 34.7 GPU-h. Do NOT relaunch while any
  Docker container is up.

  ### On I48_STAGE2_DONE (iteration 48 completion instructions — execute in this order)

  1. Check the log tail for `I48_ABORT_*` (disk aborts are interrupted runs with a resume
     point, not nulls; the consecutive-failure abort is falsifier F4's completion-null
     form) and confirm no Docker containers remain (`sudo docker ps`).
  2. Collect from `/datasets/nuscenes-full/hugsim/iter48_runs/` into
     `experiments/iter48_hugsim_transfer_gate/proof-stage2/`: `receipts.json`,
     `d0_verdict_carried.txt`, `frozen_scenarios.sha256`, `heavy_manifest_iter48.txt`,
     every episode dir's `eval.json`/`output.txt`/`episode_meta.json` plus each ON dir's
     `sentinel_iter48_decisions.jsonl` (under `proof-stage2/episodes/`, any `__failed`
     dirs included), and `/var/log/sentinel-iter48-stage2.log` as
     `proof-stage2/i48-stage2-run.log`; also produce `proof-stage2/box_episode_hashes.txt`
     on the box first: `cd /datasets/nuscenes-full/hugsim/iter48_runs && sha256sum
     */eval.json */episode_meta.json`. Split any file >90 MB into `.part-*`. Heavy
     pickles/videos STAY on the box behind `heavy_manifest_iter48.txt`. Commit proof
     FIRST.
  3. Run the committed analyzer ONCE from the committed artifacts:
     `python3 experiments/iter48_hugsim_transfer_gate/analyze_transfer.py
     --episodes .../proof-stage2/episodes --receipts .../proof-stage2/receipts.json
     --out .../proof-stage2/transfer_report.json
     --markdown-out .../proof-stage2/transfer_pairs.md`
  4. Publish RESULT.md at FULL WEIGHT per the registered verdict classes
     (PASS_TRANSFER_POSITIVE / TRANSFER_NEGATIVE / TRANSFER_NULL /
     TRANSFER_BOUNDARY_NULL_F2_* / VOID_RETUNED / completion null) — pass OR null is THE
     transfer verdict; state the carried noise floor; report the median CI + heavy-tail
     caveat; name F3 on the record if fired; the forbidden-claims list is binding (no
     NeuroNCAP-equivalence, no deployment/real-world/safety, no benchmark-ranking, no
     monitor-robustness claim). Update README (row 48 + header/status/repo-map/
     defensibility arc), CONTINUITY arc + shift log, regenerate HANDOFF.md; ruff + pytest
     + validate_docs green on every push. Record box state (iter48_runs stays on the data
     disk behind the heavy manifest).
- 2026-07-12: Claude (Fable 5) via delegated executor — executed the committed iteration 48
  on-done flow after `I48_STAGE2_DONE` (16:29:13 UTC; zero `I48_ABORT_*` markers; no
  containers). Collected the full evidence set from the box into
  experiments/iter48_hugsim_transfer_gate/proof-stage2/ (receipts, carried D0 verdict file,
  frozen-scenarios manifest, heavy manifest, all 104 episode artifact sets — zero __failed
  dirs — all 52 ON-arm decision JSONLs, the full run log, on-box SHA256 hashes; 208/208
  collected files verified byte-identical to the box; monitor_patch_sha verified
  byte-identical to the committed patch copy BEFORE commit; no file needed a .part split),
  committed proof FIRST, ran the committed analyzer ONCE from committed artifacts, and
  published `TRANSFER_NULL` at full weight — THE transfer verdict (see the arc bullet above
  for the numbers: mean paired HD delta −0.0166 CI [−0.0551, +0.0255]; median +0.0032 CI
  [−0.0467, +0.0178]; 37/52 ON episodes intervened, 26.9% pooled brake frames, 134 releases;
  no falsifier fired; F1 void check passed mechanically). README row 48 + header blockquote +
  "The result" boundary line + net-summary + status bullet + sequencing paragraph + repo map
  + defensibility-arc node A48 (verdict class null) updated; CONTINUITY arc bullet added;
  HANDOFF regenerated; ruff + pytest (178) + validate_docs green. BOX IDLE at exit (no Docker
  containers; iter48_runs stays on the data disk behind heavy_manifest_iter48.txt). Nothing
  further is authorized under this iteration; successors need fresh pre-registrations.
- 2026-07-12: Claude (Fable 5) via delegated executor — iteration 49 (the named hard-tier
  successor to iteration 48's TRANSFER_NULL, successor item (c)) pre-registered, tooled, and
  LAUNCHED. (1) Read-only box inventory FIRST: the staged HUGSIM release ships exactly two
  harder nuScenes tiers — hard-00 and extreme-00, one per scene x 18 scenes = 36 yamls (88
  total across tiers); every extreme yaml carries an AttackPlanner adversarial actor (18/18),
  three hard yamls do (0041/0411/0930); only scene-0013-hard-00 and scene-0920-hard-00 set
  load_HD_map: true (maps staged, iter47); all 44 referenced 3DRealCar assets present with
  gs.pth; scene zips present for all 18 scenes; 9 scenes already extracted, 4 scheduled
  scenes new to the pipeline (0167/0254/0383/0411). (2) Pre-registered
  experiments/iter49_hugsim_hard_tier_gate/HYPOTHESIS.md committed ALONE (ddd9130, CI
  green): frozen schedule = lexicographically first 26 of the 36 (13 scenes x both tiers,
  15/26 AttackPlanner-bearing, includes scene-0051 both tiers) with per-yaml SHA256s; the
  iter48 client patch UNCHANGED as a byte copy (SHA 6b39fd79… gated at launch AND in the
  analyzer F1), seven NeuroNCAP-frozen params, F1 void identical; 26 x 2 arms x N=2 = 104
  episodes, within-launch back-to-back OFF r1 -> ON r1 -> OFF r2 -> ON r2 under the carried
  stochastic D0; scenario-clustered bootstrap 10k seed 49, primary mean-delta CI + median
  heavy-tail; secondaries NC/DAC/TTC-COM/RC + per-episode brake fractions + step-cap list
  (scene-0051 recurrence watch) + descriptive tier split (no tier claim); falsifiers F1-F7
  incl. the pre-declared asset pre-check gate (iters 46/47 staging lesson); budget ceiling
  104 x 1200 s = 34.7 GPU-h (<= 35), expected ~9-18; forbidden claims carried; pass OR null
  = the collision-regime transfer answer at full weight. (3) Tooling committed (755e179, CI
  green): run_hard_tier_gate.sh (iter48 launcher pattern + I49 markers + pre-check gate +
  patch-SHA gate; only SENTINEL_ENABLED reaches the container), analyze_hard_tier.py (seed
  49, patch-SHA F1, per-episode over-braking visibility), 19 unit tests (197 total green).
  (4) LAUNCHED detached at 17:16:54 UTC: I49_PRECHECK_OK 17:16:55, I49_PROVENANCE_OK
  17:17:06 (receipts monitor_patch_sha byte-identical to the committed iter48 patch);
  first pair verified — OFF r1 hd=0.0 steps=12 (~109 s, attempt 1) and ON r1 hd=0.0082
  steps=12 (12 decision lines + JSONL, attempt 1) on scene-0013-extreme-00; the map-loading
  episode scene-0013-hard-00 off r1 also completed (hd=0.0054, steps=13) — past the
  iteration-46 historical failure point. RUN IN FLIGHT — log
  /var/log/sentinel-iter49-hard.log, done marker I49_HARD_DONE; observed pace ~108
  s/episode would finish ~20:30 UTC 2026-07-12; braking/extraction-heavy episodes may
  extend this; registered ceiling 34.7 GPU-h. Do NOT relaunch while any Docker container
  is up.

  ### On I49_HARD_DONE (iteration 49 completion instructions — execute in this order)

  1. Check the log tail for `I49_ABORT_*` (disk aborts are interrupted runs with a resume
     point, not nulls; the consecutive-failure abort is falsifier F4's completion-null
     form) and confirm no Docker containers remain (`sudo docker ps`).
  2. Collect from `/datasets/nuscenes-full/hugsim/iter49_runs/` into
     `experiments/iter49_hugsim_hard_tier_gate/proof-hard/`: `receipts.json`,
     `d0_verdict_carried.txt`, `frozen_scenarios_hard.sha256`, `schedule_26.txt`,
     `heavy_manifest_iter49.txt`, every episode dir's
     `eval.json`/`output.txt`/`episode_meta.json` plus each ON dir's
     `sentinel_iter48_decisions.jsonl` (under `proof-hard/episodes/`, any `__failed` dirs
     included), and `/var/log/sentinel-iter49-hard.log` as `proof-hard/i49-hard-run.log`;
     also produce `proof-hard/box_episode_hashes.txt` on the box first:
     `cd /datasets/nuscenes-full/hugsim/iter49_runs && sha256sum */eval.json
     */episode_meta.json`. Split any file >90 MB into `.part-*`. Heavy pickles/videos STAY
     on the box behind `heavy_manifest_iter49.txt`. Verify the collected receipts'
     monitor_patch_sha is byte-identical to the committed
     experiments/iter48_hugsim_transfer_gate/client_patch_union_iter48.py BEFORE commit.
     Commit proof FIRST.
  3. Run the committed analyzer ONCE from the committed artifacts:
     `python3 experiments/iter49_hugsim_hard_tier_gate/analyze_hard_tier.py
     --episodes .../proof-hard/episodes --receipts .../proof-hard/receipts.json
     --out .../proof-hard/transfer_report.json
     --markdown-out .../proof-hard/transfer_pairs.md`
  4. Publish RESULT.md at FULL WEIGHT per the registered verdict classes
     (PASS_TRANSFER_POSITIVE / TRANSFER_NEGATIVE / TRANSFER_NULL /
     TRANSFER_BOUNDARY_NULL_F2_* / VOID_RETUNED / completion null) — pass OR null is the
     collision-regime transfer answer; state that the harder-tier OFF-OFF noise floor is
     measured fresh by F5 inside this run; report the median CI + heavy-tail caveat; name
     F3 and any scene-0051-pattern localized over-braking on the record; the tier split is
     descriptive only (no tier claim); the forbidden-claims list is binding (no
     NeuroNCAP-equivalence, no deployment/real-world/safety, no benchmark-ranking, no
     monitor-robustness claim). Update README (row 49 + header/status/repo-map/
     defensibility arc), CONTINUITY arc + shift log, regenerate HANDOFF.md; ruff + pytest
     + validate_docs green on every push. Record box state (iter49_runs stays on the data
     disk behind the heavy manifest).
- 2026-07-12: Claude (Fable 5) via delegated executor: accessibility revision of paper.tex per
  Holger Caesar's nine-point feedback (language only, zero number or claim changes); pdf and
  arXiv package rebuilt (1807981, 7372eae, CI green). Caesar replied happy-to-endorse; direct
  link sent (Gmail 19f574aed0b5f451) plus an honest Maestro disclosure (19f5752e5c2369f1);
  awaiting his endorsement confirmation. Iter49 hard-tier gate in its launch window in
  parallel.
- 2026-07-12 (eve consolidation): Claude (Fable 5) — Caesar thread complete for the night: four
  messages sent same-evening (endorse link 19f574aed0b5f451; style ownership 19f57523339cc24e;
  honest Maestro disclosure 19f5752e5c2369f1; revision-is-live closing note 19f5763d5703fb3d),
  all threaded, all from the authenticated daniel@aweblabs.ai; awaiting endorsement
  confirmation, then Daniel uploads docs/paper/sentinel-arxiv-submission.tar.gz (REVISED
  package, rebuilt 7372eae) at arxiv.org/user. RUNS: iter49 hard-tier gate IN FLIGHT
  (pre-reg ddd9130; 26 hard/extreme scenarios, 15 with AttackPlanner adversaries; log
  /var/log/sentinel-iter49-hard.log, done marker I49_HARD_DONE, on-done block committed
  73add7c; early OFF-arm zero-score episodes confirm the collision-dominant regime). iter50
  collision-opportunity audit dispatched OFFLINE in parallel: its HYPOTHESIS must be committed
  BEFORE any iter49 outcome data is read, freezing the opportunity-scarcity explanation of the
  iter48 null and prediction P1 for iter49; both branches falsifiable. Standards unchanged and
  binding: pre-register before data, nulls at full weight, terse commit subjects, evidence or
  it did not happen, defensibility over impressiveness.
- 2026-07-12/13: Claude (Fable 5) — iteration 50 executed and published. Pre-registration
  committed ALONE and pushed (fbd1b3d) with iteration 49 unread (firewall stated in the doc;
  the three HANDOFF launch-marker HDs disclosed as the only pre-existing sliver); analyzer +
  18 unit tests (ee41aa6, 215 total green); ONE analyzer run over committed artifacts; proof
  committed first (d76c6ba), then RESULT at full weight: `OPPORTUNITY_AUDIT_COMPLETE` with
  A1_CONFIRMED (NeuroNCAP benefit concentrates where OFF collides, rho +0.7003 CI
  [+0.3909, +0.8762]) and the iter48 TRANSFER_NULL classified `OPPORTUNITY_PRESENT_NULL`
  (40/52 = 76.9% of iter48 OFF episodes collision-bearing; HBASE corroborates 40/52; the
  classification does not upgrade the null). P1 stands frozen for iteration 49's publisher:
  opportunity >= 13/52 + positive CI = confirmed; opportunity >= 13/52 + null/negative CI =
  transfer failure REAL, not opportunity-scarce; < 13/52 = not testable. NO iteration-49
  outcome data was read this shift; the iter49 run/collection remains governed solely by its
  own on-done block above. README row 49 (in-flight) + row 50 added; ruff/pytest/
  validate_docs green on every push.
- 2026-07-12 ~23:15 local: MILESTONE — the paper is SUBMITTED to arXiv (submit/7790500,
  cs.RO, status submitted; endorsed by Holger Caesar the same evening after his nine-point
  review was folded in). Awaiting moderation + announcement for the abs/ link. On
  announcement: thank-you reply to Caesar with the link, William courtesy note follow-up if
  natural, LinkedIn publication entry + follow-up post, profile README + portfolio research
  links upgraded from repo-PDF to arXiv link (post-publication task list in campaign memory).
- 2026-07-12 night consolidation: Claude (Fable 5) — ARXIV SUBMITTED (submit/7790500, cs.RO,
  metadata verified clean pre-submit); Caesar endorsement acknowledged with a two-line
  threaded thank-you (Gmail 19f57fc0b1f194cd); announcement watch armed (on abs/ link: Caesar
  link reply, LinkedIn publication + post, profile/site link upgrades per campaign memory).
  Public surfaces shipped tonight, outside this repo: GitHub profile README
  (manfromnowhere143 root repo; profile-overview render pending GitHub indexing; Daniel set
  pins sentinel/telos/perceptionproof), danielwahnich.dev/work Sentinel+Telos entries with
  hand-drawn marks (portfolio repo 26d7fdc, no Aweb attribution). Iteration 49 hard-tier run
  IN FLIGHT (~52/104 at 20:15 UTC, zero aborts, marker I49_HARD_DONE, on-done block in this
  file); iteration 50's frozen prediction P1 governs its interpretation. Hourly heartbeat
  carries: iter49 completion, arXiv announcement email, Caesar inbox, gcloud auth.
- 2026-07-13: Codex — recovered after auth refresh, followed the committed I49 on-done block,
  and completed iteration 49. Live probe found `I49_HARD_DONE` at 23:12:34 UTC 2026-07-12,
  no Docker containers, `104` completed episode dirs, `0` failed dirs, root disk 87%, data
  disk 88% with 122G free, swap healthy. Exported the registered proof set from
  `/datasets/nuscenes-full/hugsim/iter49_runs/` plus `/var/log/sentinel-iter49-hard.log`;
  box proof tar SHA256 `7b7573616691475baab9622100ebc08b5d54c1b73ec24d4019a75c1121976f3a`.
  Local substrate check before commit: 104 evals/output/meta, 52 ON decision JSONLs, 0 large
  files, receipts monitor_patch_sha byte-identical to the committed iter48 patch. Proof
  committed FIRST as `2eb0c81` (`iter49: commit hard-tier proof artifacts`). Then ran the
  committed analyzer ONCE from committed artifacts: verdict `TRANSFER_NULL`, mean paired HD
  delta `-0.0089` CI `[-0.0438, +0.0203]`, median `+0.0011` CI `[-0.0077, +0.0105]`,
  40/52 ON intervention episodes, 22.3% pooled brake frames, 58 releases, no falsifier fired.
  Resolved iteration 50 P1 from iter49 OFF evals: 51/52 primary opportunity, Branch B
  REFUTED. Published RESULT.md; updated README row 49/header/status/repo-map and this
  continuity arc. Heavy artifacts remain on the box behind `heavy_manifest_iter49.txt`.
- 2026-07-13: Codex — opened and completed iteration 51 as the next autonomous offline move
  after the HUGSIM transfer null. Pre-registered the HUGSIM transfer-failure taxonomy ALONE
  (`778304c`), then added analyzer/tests (`71abe6d`, 231 tests green before analysis), then
  ran the analyzer ONCE over committed iteration-48/49/50 proof. Result:
  `TAXONOMY_COMPLETE`; infrastructure all-pass; combined HUGSIM taxonomy is mixed
  (`34/91 = 0.374`, below 0.40 dominance bar), with only 6/91 OFF-opportunity pairs
  converted and 85/104 pairs collision-persistent. Published RESULT.md and proof-taxonomy
  artifacts, updated README and this continuity record. No GPU/gcloud/box read and no new
  safety, transfer, deployment, robustness, or benchmark claim.
- 2026-07-13: Codex — opened and completed iteration 52 as the next mechanism-cause audit.
  Disclosed the pre-freeze prototype timing probe in the HYPOTHESIS (`48a37e1`), added
  analyzer/tests (`b1721ca`, 244 tests green before analysis), then ran the analyzer ONCE
  over committed iteration-48/49/51 proof. Result: `TIMING_AUDIT_COMPLETE`; 92 ON-collision
  episodes cross-checked exactly against iter51; bins = post-collision first brake 35,
  long-lead brake 26, no-brake/no-surface-proxy 22, short-lead brake 9, no-brake/surface
  present 0. Published RESULT.md and proof-timing artifacts, updated README/NEXT_PHASE/
  CONTINUITY. No GPU/gcloud/box read and no actor-identity, safety, transfer, deployment,
  robustness, benchmark, or retuning claim.
- 2026-07-13: Codex — opened and completed iteration 53 as the next HUGSIM mechanism-cause
  audit. Disclosed the pre-freeze patch/prototype inspection in the HYPOTHESIS (`b5758f3`),
  added analyzer/tests (`92c8cdd`), then ran the analyzer ONCE over committed iteration-48/49
  HUGSIM proof plus the iteration-52 timing report for cross-checks. Result:
  `FIRST_FIRE_CHANNEL_COMPLETE`; pair count matched iteration 52 `104` vs `104`, timing-bin
  mismatches `0`, unreconstructable channels `0`; ON-collision first-fire channels =
  ttc_only `36`, cpa_only `33`, no_fire `22`, both `1`; pre-collision-fire channels =
  cpa_only `19`, ttc_only `16`. Published RESULT.md and proof-channel artifacts, updated
  README/NEXT_PHASE/CONTINUITY. No GPU/gcloud/box read and no actor-identity, safety,
  transfer, deployment, robustness, benchmark, or retuning claim.
- 2026-07-13: Codex — opened and completed iteration 54 as the provenance support audit after
  iteration 53. Disclosed pre-freeze schema/patch inspections in the HYPOTHESIS (`1ba7663`),
  added analyzer/tests (`7c5a3fd`, 266 tests green before analysis), then ran the analyzer
  ONCE over committed iteration-48/49 HUGSIM proof plus the iteration-53 report for
  cross-checks. Result: `PROVENANCE_SUPPORT_NULL`; pair count matched iteration 53 `104` vs
  `104`, channel mismatches `0`, timing mismatches `0`; monitor-side first-fire argmins
  reconstruct cleanly (unique TTC object `40`, unique CPA object `36`, both-distinct `1`,
  no-fire `27`), but collision actor identity is not logged in any committed HUGSIM eval
  (`0/104` supported, `0/92` among ON-collision episodes). Published RESULT.md and
  proof-provenance artifacts, updated README/NEXT_PHASE/CONTINUITY. No GPU/gcloud/box read and
  no actor-identity, actor-match, safety, transfer, deployment, robustness, benchmark, or
  retuning claim.
- 2026-07-13: Codex — opened and completed iteration 55 as the HUGSIM collision instrumentation
  source-map audit. Pre-registered source-only scope ALONE (`b9254fb`), added analyzer/tests
  (`6695f2e`, 271 tests green before analysis), cloned HUGSIM outside the repo and detached at
  the frozen SHA `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`, then ran the analyzer ONCE.
  Result: `COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE`; checkout identity matched, 153
  source-like files scanned, 103 candidates found, and instrumentation candidates mapped to
  `sim/utils/score_calculator.py` and `closed_loop.py`. Published RESULT.md and proof-source
  artifacts, updated README/NEXT_PHASE/CONTINUITY. No GPU/gcloud/simulator/box read, no source
  edit, no actor attribution, no safety/transfer/deployment/robustness/benchmark, and no
  retuning claim.
- 2026-07-13: Codex — continued into iteration 56 as the source-only HUGSIM provenance
  instrumentation patch-design gate. Pre-registered ALONE (`a6429b6`), drafted a
  `collision_provenance` sidecar patch against a temporary frozen HUGSIM checkout, added verifier
  and tests (`87536ff`, 275 tests green before proof), then ran the verifier ONCE. Result:
  `INSTRUMENTATION_PATCH_DESIGN_NULL`; the patch applied cleanly and
  `sim/utils/score_calculator.py` compiled, but the registered static guard failed on the added
  `if score_nc == 0.0:` branch. Published RESULT.md and proof-patch artifacts, updated
  README/NEXT_PHASE/CONTINUITY. No GPU/gcloud/simulator/box read, no HUGSIM run, no patch
  authorization, no actor attribution, no safety/transfer/deployment/robustness/benchmark, and
  no retuning claim.
- 2026-07-13: Codex — continued into iteration 57 as the patch guard-refinement successor to the
  iteration-56 null. Pre-registered ALONE (`ce852b3`) with the Iter56 patch SHA bound, added the
  refined verifier/tests (`e2bc0c0`, 279 tests green before proof), then ran the verifier ONCE.
  Result: `PATCH_GUARD_REFINEMENT_COMPLETE`; byte-identical patch SHA matched, source SHA matched,
  patch applied cleanly, `sim/utils/score_calculator.py` compiled, and refined guards passed for
  metric assignments, control calls, and scalar `score_list` isolation. Published RESULT.md and
  proof-refined artifacts, updated README/NEXT_PHASE/CONTINUITY. No GPU/gcloud/simulator/box read,
  no HUGSIM run, no actor attribution, no safety/transfer/deployment/robustness/benchmark, and no
  retuning claim.
- 2026-07-13: Codex — continued into iteration 58 as the HUGSIM provenance execution canary
  authorized by iteration 57. Pre-registered ALONE (`70c9d63`), added launcher/analyzer/tests
  (`94756b9`, 282 tests green before launch), pushed the pre-run state, copied only byte-bound
  artifacts to `sentinel-gpu`, verified source/patch/checkpoint/shim/image/scenario/map/D0 and
  single-tenant gates, then launched exactly `scene-0013-hard-00` OFF r1 then ON r1. The run
  reached `I58_CANARY_DONE`; raw proof was collected without heavy artifacts and committed FIRST
  (`0405e28`). Analyzer verdict: `PROVENANCE_CANARY_COMPLETE`; both episodes completed
  first-attempt with `nc_min = 0.0`, top-level `collision_provenance` counts `11` and `13`,
  scalar metrics present, scalar-only `details`, and ON decision log present. No actor-match,
  HD-Score-invariance, safety/transfer/deployment/robustness/benchmark, or retuning claim.
- 2026-07-13: Codex — continued into iteration 59 as the bounded actor-match support audit after
  iteration 58 retired the instrumentation-execution blocker. Pre-registered ALONE (`c9f50c5`),
  added launcher/analyzer/tests (`e2c98a6`, 285 tests green before launch), pushed pre-run state,
  copied only byte-bound artifacts to `sentinel-gpu`, verified hashes/source/checkpoint/shim/
  image/scenario/map/D0/single-tenant gates, then launched exactly eight Sentinel-ON episodes.
  The run reached `I59_ACTOR_MATCH_DONE`; all eight episodes completed first-attempt. Raw proof
  was collected without heavy artifacts and committed FIRST (`ec5750f`). Analyzer verdict:
  `ACTOR_MATCH_AUDIT_COMPLETE`; support labels = 3 classifiable foreground, 2 no-fire, 2
  post-collision-fire, 1 background-only; all three classifiable foreground rows were
  `actor_mismatch` by the frozen bridge (15.43 m, 21.99 m, 37.04 m). No population
  actor-mismatch rate, repair, safety/transfer/deployment/robustness/benchmark, or retuning claim.
- 2026-07-13: Codex — continued into iteration 60 as the offline actor-match bridge sensitivity
  audit after iteration 59. Pre-registered ALONE (`ea8f42b`), added analyzer/tests (`5f4dd9b`,
  290 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  and report. Result: `BRIDGE_AMBIGUOUS_NULL`; exactly three classifiable rows cross-checked,
  48 frozen bridge variants evaluated, no `bridge_match_possible`, two `robust_mismatch`, and
  one `bridge_ambiguous_possible` at `5.6649 m`. No GPU/gcloud/box read, no robust all-row
  mismatch, actor-causality, repair, population-rate, safety/transfer/deployment/robustness/
  benchmark, or retuning claim.
- 2026-07-13: Codex — continued into iteration 61 as the monitor object-surface audit after the
  iteration-60 ambiguity. Pre-registered ALONE (`7688075`), added analyzer/tests (`2598b79`,
  295 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 and
  iteration-60 proof. Result: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`; three rows evaluated,
  `2,384` variants, row labels = two `no_monitor_object_support` and one
  `nontrigger_object_match`. The matching row is `ttc_extreme_b`: non-triggering `object_id=16`
  at `2.0686 m`, while trigger `object_id=1` remains ambiguous at `5.6649 m`. No GPU/gcloud/box
  read, no actor-causality, repair, population-rate, safety/transfer/deployment/robustness/
  benchmark, or retuning claim.
- 2026-07-13: Codex — continued into iteration 62 as the one-row ranking audit for the iteration
  61 matched non-trigger object. Pre-registered ALONE (`e27e587`), added analyzer/tests
  (`32d2b5f`, 299 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 and iteration-61 proof. Result: `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE`; matched
  non-trigger `object_id=16` had `min_cpa=22.7648 m`, CPA rank `9/9`, no valid TTC, while
  trigger `object_id=1` had `ttc=2.1303 s` and TTC rank `1`. No GPU/gcloud/box read, no
  actor-causality, repair, population-rate, safety/transfer/deployment/robustness/benchmark,
  or retuning claim.
- 2026-07-13: Codex — continued into iteration 63 as the temporal emergence audit for the
  iteration-61/62 matched non-trigger object. Pre-registered ALONE (`538e8d4`), added
  analyzer/tests (`dd46041`, 304 tests green before analysis), then ran the analyzer ONCE over
  committed iteration-59/61/62 proof. Result: `TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE`;
  `object_id=16` was present in 13 pre-contact frames before `7.25 s`, with hazard frames `0`,
  borderline frames `0`, min CPA `12.1690 m`, and min TTC `null`. No GPU/gcloud/box read, no
  actor-causality, repair, population-rate, safety/transfer/deployment/robustness/benchmark,
  or retuning claim.
- 2026-07-13: Codex — continued into iteration 64 as the unsupported-row temporal surface audit.
  Pre-registered ALONE (`ebdd344`), added analyzer/tests (`6807221`, 309 tests green before
  analysis), then ran the analyzer ONCE over committed iteration-59/61 proof. Result:
  `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`; both first-fire-unsupported rows have pre-contact
  monitor-object matches (`ttc_extreme_short` best `1.6718 m`; `cpa_medium_b` best `0.4325 m`),
  with `28,016` frozen bridge variants evaluated. No GPU/gcloud/box read, no actor-causality,
  repair, population-rate, safety/transfer/deployment/robustness/benchmark, or retuning claim.
- 2026-07-13: Codex — continued into iteration 65 as the matched pre-contact temporal alignment
  audit after iteration 64. Pre-registered ALONE (`2ae2c07`), added analyzer/tests (`cf516a9`,
  313 tests green before analysis), then ran the analyzer ONCE over committed iteration-59/61/64
  proof. Result: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`; both Iter64 matched objects were
  present but subthreshold at their matched timestamps (`object_id=2`: min CPA `12.7240 m`, TTC
  `3.5763 s`; `object_id=6`: min CPA `9.3179 m`, TTC `null`). One matched object later equals
  the first-fire object; the other does not. No GPU/gcloud/box read, no actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 66 as the matched-object hazard timeline audit
  after iteration 65. Pre-registered ALONE (`f56c92e`), added analyzer/tests (`151b018`, 317
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59/61/64/65
  proof. Result: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`; `ttc_extreme_short` `object_id=2`
  becomes an active TTC hazard at first fire after two borderline frames, while `cpa_medium_b`
  `object_id=6` remains visible-never-active across `13/25` pre-contact frames. No GPU/gcloud/
  box read, no actor-causality, repair, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or retuning claim.
- 2026-07-13: Codex — continued into iteration 67 as the trigger-target bridge audit after
  iteration 66. Pre-registered ALONE (`4ee7f95`), added analyzer/tests (`3ccaaa7`, 320 tests
  green before analysis), then ran the analyzer ONCE over committed iteration-59/61/64/65/66
  proof. Result: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`; one row is same-object target/trigger
  and one row is split-object. Both targets and both triggers have full-window bridge matches,
  but the first-fire trigger object has no bridge support at the fire timestamp in both rows
  (`6.9272 m`, `19.6983 m`). No GPU/gcloud/box read, no actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 68 as the fire-time bridge decomposition audit
  after iteration 67. Pre-registered ALONE (`1dc576a`), added analyzer/tests (`de567b4`, 324
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59/61/64/65/
  66/67 reports. Result: `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE`; one trigger's best
  bridge support is before first fire (`ttc_extreme_short`, `-1.25 s`) and one is after first
  fire (`cpa_medium_b`, `+2.00 s`). No GPU/gcloud/box read, no actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 69 as the HUGSIM mechanism taxonomy synthesis
  after iteration 68. Pre-registered ALONE (`ee4f60b`), added analyzer/tests (`4ec0278`, 327
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59/61/63/64/
  65/66/67/68 reports. Result: `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`; all eight iteration-59
  rows classified, with five structural rows preserved and all three classifiable foreground
  rows refined by downstream evidence. No GPU/gcloud/box read, no actor-causality, repair,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 70 as the HUGSIM structural-row timing audit
  after iteration 69. Pre-registered ALONE (`b7cb588`), added analyzer/tests (`4ceb190`, 330
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof and
  iteration-69 taxonomy. Result: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`; two structural
  rows are foreground-present surface-silent, two are foreground-present late-fire (`+1.75 s`),
  and one is foreground-absent/background-only. No GPU/gcloud/box read, no actor-causality,
  repair, population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 71 as the HUGSIM surface-silent margin audit
  after iteration 70. Pre-registered ALONE (`8c263bb`), added analyzer/tests (`fe10de8`, 333
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof and
  iteration-70 report. Result: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`; both fixed no-fire
  foreground rows are far from the frozen trigger surfaces under registered descriptive bands.
  No GPU/gcloud/box read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 72 as the HUGSIM late-fire prefire margin audit
  after iteration 71. Pre-registered ALONE (`165d99f`), added analyzer/tests (`2f08900`, 336
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof and
  iteration-70 report. Result: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`; both late-fire rows
  were near but not crossing a frozen trigger surface before contact, and both fired `+1.75 s`
  after first foreground timestamp. No GPU/gcloud/box read, no actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 73 as the HUGSIM structural margin-transition
  audit after iteration 72. Pre-registered ALONE (`6fc6c5d`), added analyzer/tests (`b73361e`,
  339 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-70/71/72 reports. Result: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`; the two
  surface-silent rows are silent/far/never-active, while the two late-fire rows are near before
  contact and first active only `+1.75 s` after first foreground timestamp. No GPU/gcloud/box
  read, no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 74 as the HUGSIM late-fire delay-barrier audit
  after iteration 73. Pre-registered ALONE (`667f45f`), added analyzer/tests (`91fb28f`, 343
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof plus
  iteration-70/72/73 reports. Result: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`; both
  late-fire rows are cross-channel delay cases: CPA-near to TTC-active for
  `both_distinct_extreme`, and TTC-near to CPA-active for `ttc_medium_a`. No GPU/gcloud/box read,
  no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 75 as the HUGSIM cross-channel object-handoff
  audit after iteration 74. Pre-registered ALONE (`a9f1750`), added analyzer/tests (`03f805c`,
  346 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-70/72/73/74 reports. Result: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
  both fixed late-fire cross-channel cases switch responsible monitor object (`5` -> `9` and
  `6` -> `24`). No GPU/gcloud/box read, no actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 76 as the HUGSIM switch foreground-bridge audit
  after iteration 75. Pre-registered ALONE (`f873c8c`), added analyzer/tests (`6f5d267`, 349
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof plus
  iteration-70/72/73/74/75 reports. Result:
  `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`; both fixed rows are
  `no_foreground_bridge_support`, so neither side of the object switch reaches the frozen match
  or ambiguous foreground bridge band. No GPU/gcloud/box read, no actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 77 as the HUGSIM event object-set foreground
  bridge audit after iteration 76. Pre-registered ALONE (`91bc32f`), added analyzer/tests
  (`9a5d20e`, 351 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-70/72/73/74/75/76 reports. Result:
  `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`; full event-row object sets recover
  mixed foreground support (`both_distinct_extreme` pre-set ambiguous via object `9`,
  `ttc_medium_a` both sets match via object `10`) even though selected switched objects remained
  unsupported in iteration 76. No GPU/gcloud/box read, no actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 78 as the HUGSIM support-object ranking audit
  after iteration 77. Pre-registered ALONE (`b7d90d6`), added analyzer/tests (`eea3883`, 353
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof plus
  iteration-70/72/73/74/75/76/77 reports. Result:
  `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`; all three foreground-supported full-set
  objects are nonselected and subthreshold under the logged CPA/TTC surface. No GPU/gcloud/box
  read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 79 as the HUGSIM selected-object surface
  decomposition after iteration 78. Pre-registered ALONE (`c5f95df`), added analyzer/tests
  (`d858f11`, 355 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-75/77/78 reports. Result:
  `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`; selected objects are active/borderline
  while foreground-supported objects remain subthreshold. No GPU/gcloud/box read, no
  actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 80 as the HUGSIM selected-object all-provenance
  bridge audit after iteration 79. Pre-registered ALONE (`833053a`), added analyzer/tests
  (`76affe1`, 357 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-77/79 reports. Result:
  `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`; all eligible logged provenance rows are
  foreground, and the selected active/borderline objects do not bridge to any logged provenance
  row. No GPU/gcloud/box read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 81 as the HUGSIM support-object temporal surface
  audit after iteration 80. Pre-registered ALONE (`9047f8c`), added analyzer/tests (`5dec78a`,
  359 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-78/79/80 reports. Result: `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`;
  `both_distinct_extreme` support object `9` later becomes borderline at `5.5 s` and active at
  `7.0 s`, while `ttc_medium_a` support object `10` remains visible-never-surface across
  `15` frames. No GPU/gcloud/box read, no actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- 2026-07-13: Codex — continued into iteration 82 as the HUGSIM support-object
  surface/provenance co-occurrence audit after iteration 81. Pre-registered ALONE (`6257a65`),
  added analyzer/tests (`9abd95e`, 361 tests green before analysis), then ran the analyzer ONCE
  over committed iteration-59 proof plus iteration-81 report. Result:
  `HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE`; both support objects have foreground
  bridge support, but object `9` has only borderline+bridge co-occurrence and object `10` has
  bridge support in every present frame without surface activation. No GPU/gcloud/box read, no
  actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value, or
  retuning claim.
- 2026-07-13: Codex — continued into iteration 83 as the HUGSIM bridge-supported surface-miss
  decomposition after iteration 82. Pre-registered ALONE (`3d6593d`), added analyzer/tests
  (`92b8f74`, 363 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-82 report. Result:
  `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`; object `9` is TTC-borderline-only on
  bridge-supported frames, while object `10` is bridge-supported with no finite TTC and
  CPA-far active margins. No GPU/gcloud/box read, no actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, or retuning claim.
- 2026-07-13: Codex — added `docs/research/FRONTIER_PROBLEM_ALIGNMENT_2026-07-13.md`, a
  source-backed alignment pulse after the operator requested a deeper Stanford/MIT/Tesla/Mobileye
  read. It records that Sentinel is aligned only as a runtime monitor/failure-localization/
  safety-evidence system for opaque planners, not as a full autonomy stack, world model,
  robotaxi product, deployment-ready safety case, or first-responder/real-world claim. The
  immediate next research action remains a fresh HUGSIM pre-registration, with selected-vs-support
  path/arbitration decomposition named as the highest-value local successor to iterations 79-83.
  The memo authorizes no GPU work, HUGSIM run, threshold change, repair, retuning, safety,
  benchmark, deployment, commercial-value, or real-world claim.
- 2026-07-13: Codex — continued into iteration 84 as the HUGSIM selected/support
  path-arbitration decomposition after the frontier-alignment pulse and iteration 83.
  Pre-registered ALONE (`c24b227`), added analyzer/tests (`ff87574`, 365 tests green before
  analysis), then ran the analyzer ONCE over committed iteration-59 proof plus iteration-79/80/83
  reports. Result: `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`; all three fixed rows
  have selected objects with lower CPA and better CPA rank, zero selected bridge support, and
  support objects with better foreground/provenance bridge support. No GPU/gcloud/box read, no
  actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, real-world/first-responder behavior,
  or retuning claim.
- 2026-07-13: Codex — added `docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md` as a
  durable compressed memory capsule of the wide frontier pass. It records the reusable lessons:
  long-tail failure discovery, validation/falsification/safety cases, supervised-autonomy claim
  discipline, world-model simulation as later infrastructure, first-responder operational
  semantics as uncovered scope, and Sentinel's defensible niche as runtime monitor/failure
  localization/evidence ledger. It authorizes no run or claim; it is recall infrastructure for
  future sessions.
- 2026-07-13: Codex — continued into iteration 85 as the HUGSIM path-horizon/provenance-timing
  decomposition after iteration 84. Pre-registered ALONE (`91900b5`), added analyzer/tests
  (`2f43d57`, 367 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-80/83/84 reports. Result:
  `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`; all three fixed rows retain selected lower
  CPA and better CPA rank, selected bridge support is `0/3`, support bridge support is `3/3`,
  support best provenance bridge is after the event timestamp in `3/3`, and selected earlier CPA
  horizon is only `1/3`. No GPU/gcloud/box read, no actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 86 as the HUGSIM bridge-time support-surface
  replay after iteration 85. Pre-registered ALONE (`832ffe5`), added analyzer/tests (`f3866ba`,
  369 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-81/83/85 reports. Result: `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`; two rows
  classified (`both_distinct_extreme` object `9` moves subthreshold -> borderline at `5.5 s`,
  `ttc_medium_a` pre object `10` remains subthreshold at `4.0 s`), but the active
  `ttc_medium_a` row has no exact committed ON decision row at the iteration-85 bridge timestamp
  `6.0 s`. No GPU/gcloud/box read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 87 as the HUGSIM interval bridge-time
  support-surface replay after iteration 86. Pre-registered ALONE (`d7aeb22`), added
  analyzer/tests (`37e21d1`, 371 tests green before analysis), then ran the analyzer ONCE over
  committed iteration-59 proof plus iteration-85/86 reports. Result:
  `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`; two rows use exact bridge
  timestamps and one row uses the registered nearest-before replay row (`5.75 s` for bridge
  timestamp `6.0 s`). Object `9` moves subthreshold -> borderline at exact `5.5 s`, while object
  `10` remains subthreshold at exact `4.0 s` and nearest-before `5.75 s`. No GPU/gcloud/box read,
  no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, real-world/first-responder
  behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 88 as the HUGSIM bridge/surface margin residual
  decomposition after iteration 87. Pre-registered ALONE (`ff61fee`), added analyzer/tests
  (`dfa85ba`, 373 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-85/87 reports. Result: `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE`; object
  `9` is TTC-borderline/CPA-far at replay (`ttc=4.7761 s`, active TTC margin `+2.2761 s`,
  active CPA margin `+20.0208 m`), while object `10` is no-finite-TTC/CPA-far in both replay rows
  (active CPA margins `+9.6354 m` and `+10.6434 m`). No GPU/gcloud/box read, no raw decision-log
  read, no actor-causality, repair, threshold-value, population-rate, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, real-world/first-responder
  behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 89 as the HUGSIM joint bridge/surface candidate
  audit after iteration 88. Pre-registered ALONE (`762d58d`), added analyzer/tests (`6ba45c9`,
  375 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-85/87/88 reports. Result:
  `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE`; across the three replay rows,
  `11` logged objects are bridge-supported, but active+bridge-supported candidate events are
  `0/3`. Object `9` is bridge-supported only at borderline, and object `10` is bridge-supported
  but subthreshold in both rows. No GPU/gcloud/box read, no actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 90 as the HUGSIM active-surface provenance gap
  audit after iteration 89. Pre-registered ALONE (`1caef74`), added analyzer/tests (`5f174e8`,
  377 tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof
  plus iteration-87/89 reports. Result: `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`; across
  the three replay rows, bridge-supported objects total `11`, all `11` are non-active,
  active+bridge-supported objects are `0`, and the only active object is active/no-bridge. No
  GPU/gcloud/box read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 91 as the HUGSIM active-gap geometry
  decomposition after iteration 90. Pre-registered ALONE (`4397619`), added analyzer/tests
  (`db6b1cb`, 379 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-59 proof plus iteration-90 report. Result:
  `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`; two rows are
  provenance-near/path-inactive, and the active `ttc_medium_a` row is
  path-active/provenance-far: object `24` is active by CPA (`min_cpa=1.0010 m`) but bridge
  `no_support` at `10.9518 m`, while nearest bridge-supported object `10` is subthreshold at
  `4.2468 m`. No GPU/gcloud/box read, no actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 92 as the HUGSIM path-proximity arbitration audit
  after iteration 91. Pre-registered ALONE (`cf329be`), added analyzer/tests (`342b97d`, 381
  tests green before analysis), then ran the analyzer ONCE over committed iteration-59 proof plus
  iteration-91 report. Result: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`; CPA/path-best
  and provenance-best objects differ in all three fixed replay rows (`0/3` same-object events).
  The active row's path/surface-best object `24` is active but bridge `no_support`
  (`10.9518 m`), while provenance-best object `6` is subthreshold at `3.7598 m`. No
  GPU/gcloud/box read, no actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 93 as the HUGSIM surface-winner alignment audit
  after iteration 92. Pre-registered ALONE (`193274f`), added analyzer/tests (`126aa4a`, 383
  tests green before analysis), then ran the analyzer ONCE over the committed iteration-92 report
  only. Result: `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`; surface follows path in two
  rows and provenance in one row, with zero path/provenance same-object rows. The active
  `ttc_medium_a` row follows path object `24`, which is active but bridge `no_support`. No
  raw-log read, GPU/gcloud/box read, actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 94 as the HUGSIM active-row surface margin
  arbitration after iteration 93. Pre-registered ALONE (`16449c2`), added analyzer/tests
  (`fab51e0`, 386 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-91/92/93 reports. Result:
  `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`; in the active `ttc_medium_a` row,
  object `24` is the only active CPA/path/surface candidate (`active_cpa_margin_m=-0.4990`,
  `cpa_rank=1`, bridge `no_support`), while all three bridge-supported candidates are
  subthreshold, TTC-null, and CPA-far; the nearest bridge-supported active CPA margin is object
  `10` at `+10.6434 m`. No raw-log read, GPU/gcloud/box read, actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-13: Codex — continued into iteration 95 as the HUGSIM non-active surface branch
  arbitration after iteration 94. Pre-registered ALONE (`f964d9e`), added analyzer/tests
  (`2453187`, 389 tests green before analysis), then ran the analyzer ONCE over committed
  iteration-92/93/94 reports. Result:
  `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE`; `both_distinct_extreme` pre
  follows provenance object `9`, which is bridge-matched and TTC-borderline (`ttc=4.7761 s`),
  despite path object `5` having better CPA/rank, while `ttc_medium_a` pre follows path object
  `19` because both candidates are subthreshold/TTC-null and path wins CPA/rank despite
  provenance object `3` having closer bridge support. No raw-log read, GPU/gcloud/box read,
  actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-14: Codex — continued into iteration 96 as the HUGSIM branch taxonomy outcome bridge
  after iteration 95. Pre-registered ALONE (`91ddad5`), added analyzer/tests (`8a16f79`, 392
  tests green before analysis), then ran the analyzer ONCE over committed iteration-70/94/95
  reports. Result: `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE`; the two
  post-collision-fire structural rows have different branch explanations
  (`both_distinct_extreme` provenance/TTC-borderline, `ttc_medium_a` path/CPA plus active CPA),
  but both are `foreground_present_late_fire`, both fire `+1.75 s` after foreground contact, and
  both have zero pre-or-at foreground fire frames. No raw-log read, GPU/gcloud/box read,
  actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-14: Codex — continued into iteration 97 as the HUGSIM surface-silent outcome margin
  bridge after iteration 96. Pre-registered ALONE (`d8610f3`), added analyzer/tests (`8f79976`,
  395 tests green before analysis), then ran the analyzer ONCE over committed iteration-70/71/73
  reports. Result: `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE`; both
  foreground-present no-fire rows are far-margin, never-active, zero-fire rows with zero
  pre-foreground-near flags and only post-foreground near approaches (`+0.25 s` and `+3.50 s`).
  No raw-log read, GPU/gcloud/box read, actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-14: Codex — continued into iteration 98 as the HUGSIM background-only outcome bridge
  after iteration 97. Pre-registered ALONE (`49454a6`), added analyzer/tests (`b6b8240`, focused
  tests and ruff green before analysis), then ran the analyzer ONCE over committed
  iteration-59/69/70 reports. Result: `HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE`; the lone
  `cpa_medium_a` background-only row has zero foreground support, no first foreground timestamp,
  first fire at `3.5 s`, `ttc_only` first-fire channel, `4` fired frames, `11` brake frames, and
  preserved monitor object `11` with `unique_ttc_object` provenance. No raw-log/raw-eval read,
  GPU/gcloud/box read, actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, or retuning claim.
- 2026-07-14: Codex — continued into iteration 99 as the HUGSIM structural bridge coverage audit
  after iteration 98. Pre-registered ALONE (`5a5564c`), added analyzer/tests (`7cd825a`, focused
  tests and ruff green before analysis), then ran the analyzer ONCE over committed
  iteration-70/96/97/98 reports. Result: `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE`; all five
  fixed iteration-70 structural rows are covered exactly once by compatible bridge sources:
  late-fire rows by iteration 96 (`2`), surface-silent rows by iteration 97 (`2`), and the
  background-only row by iteration 98 (`1`), with `0` uncovered and `0` duplicate/incompatible
  rows. No raw-log/raw-eval read, GPU/gcloud/box read, actor-causality, repair, threshold-value,
  population-rate, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, or retuning claim.
- 2026-07-14: Codex — continued into iteration 100 as the HUGSIM structural expansion support
  audit after iteration 99. Pre-registered ALONE (`ed539e6`), added analyzer/tests (`ac20787`,
  focused tests and ruff green before analysis), then ran the analyzer ONCE over committed
  iteration-54/59/99 reports. Result: `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL`; the
  broad committed transfer pool has `104` ON rows and `77` monitor-side provenance-supported rows,
  but `0/104` collision-actor-supported rows, so the five-row structural bridge map cannot expand
  from existing committed reports alone. New collision-provenance instrumentation or another
  evidence source is required before any larger structural bridge claim. No raw-log/raw-eval/raw
  episode read, GPU/gcloud/box read, actor-causality, repair, threshold-value, population-rate,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, or approval-to-run claim.
- 2026-07-14: Codex — continued into iteration 101 as the HUGSIM provenance batch candidate
  design after iteration 100. Pre-registered ALONE (`498d0a5`), added analyzer/tests (`6886108`,
  focused tests and ruff green before analysis), then ran the analyzer ONCE over committed
  iteration-54/59/100 reports. Result: `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE`; the
  future instrumented-batch candidate schedule now has `12` new rows across the six
  non-singleton dataset/provenance strata plus `1` carried existing both-distinct singleton
  reference (`scene-0138-extreme-00` run 1). This is a schedule only and authorizes no run. No
  raw-log/raw-eval/raw episode read, GPU/gcloud/box read, actor-causality, repair,
  threshold-value, population-rate, safety/transfer/deployment/robustness/benchmark,
  HD-Score-invariance, commercial-value, real-world/first-responder behavior, retuning, GPU
  approval, or approval-to-run claim.
- 2026-07-14: Codex — completed iteration 112 as the HUGSIM support-core batch execution after
  the iteration-111 launch manifest. Pre-registered ALONE (`9ffc507`), added launcher/analyzer/tests
  (`f5aa89c`), collected and pushed raw GPU proof before analysis (`bced67b`), then ran the
  analyzer ONCE over the committed proof. Result:
  `HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE`; all `8/8` manifest slots completed on first
  attempt, `8/8` proof artifact sets are complete, `8/8` evals expose top-level
  `collision_provenance`, total collision-provenance rows are `44`, and all `3` duplicate scenario
  groups were preserved by `slot_id`. The next honest step is a separately pre-registered
  actor-match support audit over the committed iteration-112 proof. No actor-causality,
  actor-match interpretation, repair, threshold-value, safety/transfer/deployment/robustness/
  benchmark/HD-Score-invariance, commercial-value, real-world/first-responder behavior, retuning,
  production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 113 as the HUGSIM support-core actor-match support
  audit after iteration 112. Pre-registered ALONE (`3bc6027`), added analyzer/tests (`a3d7439`,
  targeted ruff/tests/docs green), then ran the analyzer ONCE over committed iteration-111/112
  artifacts. Result: `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE`; `8/8` slots are
  `classifiable_foreground` against the frozen floor of `4`, all `3` exact anchors and all `5`
  scenario analogues remained classifiable, and all `8` bridge labels are `actor_mismatch` with
  `0` matches and `0` ambiguous rows. This solves the registered support floor for these rows but
  does not prove repair, safety, or causal effect. Next honest step: offline mismatch-geometry
  decomposition over the committed support-core report/proof. No actor-causality, repair,
  threshold-value, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, retuning, production, or commercial
  claim.
- 2026-07-14: Codex — continued into iteration 114 as the HUGSIM support-core mismatch-geometry
  decomposition after iteration 113. Pre-registered ALONE (`b08709e`), added analyzer/tests
  (`e7bfc37`, targeted ruff/tests/docs green), then ran the analyzer ONCE over the committed
  iteration-113 report only. Result: `HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE`; all `8`
  mismatch vectors classified with `0` problem rows, `8/8` are `forward_dominant`, `7/8` place
  the monitor object far behind the first foreground collision actor, and the geometry split is
  `5` far-behind/lateral-near, `2` far-behind/lateral-far, `1` far-ahead/lateral-far. Next honest
  step: offline monitor-object/collision-actor temporal and object-set ordering over the same
  committed rows. No actor-causality, repair, threshold-value, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, real-world/first-responder
  behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 115 as the HUGSIM support-core monitor-set ordering
  audit after iteration 114. Pre-registered ALONE (`dad164a`), added analyzer/tests (`cf871f6`,
  targeted ruff/tests/docs green), then ran the analyzer ONCE over committed iteration-112/113/114
  artifacts. Result: `HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE`; all `8/8` first-fire
  monitor object sets classify as `nearest_actor_mismatch`, nearest object distance is
  `7.624207359121617-24.812496764606966 m`, selected object is nearest in `5/8` rows and not
  nearest in `3/8`, but every row remains a whole-set mismatch. Next honest step: offline timeline
  audit asking whether a close collision-actor candidate appears before fire, after fire, or never
  appears under the frozen bridge. No actor-causality, repair, threshold-value,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 116 as the HUGSIM support-core collision-actor
  timeline audit after iteration 115. Pre-registered ALONE (`05f90d0`), added analyzer/tests
  (`e9688e5`, targeted ruff/tests/docs green), then ran the analyzer ONCE over committed
  iteration-112/115 artifacts. Result: `HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE`;
  all `8` rows classified with `0` problem rows, `7/8` rows have at least one support frame before
  collision, first support appears `pre_fire` in `5/8`, `post_fire_pre_collision` in `2/8`, and
  `never_before_collision` in `1/8`, while at-fire nearest distances remain
  `7.624207359121617-24.812496764606966 m`. Next honest step: offline event-window decomposition
  of persistence, selected-object identity, and released CPA/TTC surface state around first-support
  and first-fire frames. No actor-causality, repair, threshold-value, safety/transfer/deployment/
  robustness/benchmark/HD-Score-invariance, commercial-value, real-world/first-responder behavior,
  retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 117 as the HUGSIM support-core event-window
  decomposition after iteration 116. Pre-registered ALONE (`c42b195`), added analyzer/tests
  (`525a3bd`, targeted ruff/tests/docs green), then ran the analyzer ONCE over committed
  iteration-112/115/116 artifacts. Result: `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE`; all `8`
  rows classified with `0` problem rows, first-support surface state is `far` in all `7`
  supported rows, first-fire surface state is `active` in all `8`, first-support objects persist
  to first fire in only `1/7`, and first-support objects equal the selected first-fire object in
  `0/7`. Next honest step: offline support-object lifecycle audit from first support to fire
  (last presence, last support, disappearance or drift outside the support band, and same-object
  vs different-object later active support). No actor-causality, repair, threshold-value,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 118 as the HUGSIM support-core support-object
  lifecycle audit after iteration 117. Pre-registered ALONE (`f5f01ea`), added analyzer/tests
  (`a336d29`, targeted ruff/tests/docs green), then ran the analyzer ONCE over committed
  iteration-112/117 artifacts. Result: `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE`; all `8`
  rows classified with `0` problem rows, first-support objects are absent at fire in `4` pre-fire
  rows, drifted outside support in `1`, never still supported at fire (`0/7`), and later
  active-surface support is different-object only (`2` frames, `0` same-object). Next honest step:
  offline support-loss/replacement audit quantifying last-support-to-fire and
  last-presence-to-fire gaps plus first-fire replacement identity/distance. No actor-causality,
  repair, threshold-value, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, retuning, production, or commercial
  claim.
- 2026-07-14: Codex — continued into iteration 119 as the HUGSIM support-core support-loss and
  replacement audit after iteration 118. Pre-registered ALONE (`eddb0e6`), added analyzer/tests
  (`43dee63`, targeted ruff/tests/docs green), then ran the analyzer ONCE over committed
  iteration-112/117/118 artifacts. Result: `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE`; all
  `8` rows classified with `0` problem rows, last same-object support ends `1.0-6.0 s` before
  first fire where measurable, selected is first-fire nearest in `5/8` and not nearest in `3/8`,
  first-fire nearest is the first-support object in only `1/8`, and all first-fire nearest
  distances remain outside support (`7.624207359121617-24.812496764606966 m`). Next honest step:
  offline selected-fire-object backward lifecycle audit. No actor-causality, repair,
  threshold-value, safety/transfer/deployment/robustness/benchmark/HD-Score-invariance,
  commercial-value, real-world/first-responder behavior, retuning, production, or commercial
  claim.
- 2026-07-14: Codex — continued into iteration 120 as the HUGSIM support-core selected fire-object
  backward lifecycle audit after iteration 119. Pre-registered ALONE (`77a3e3b`), added
  analyzer/tests (`508f576`, targeted ruff/tests/docs green), then ran the analyzer ONCE over
  committed iteration-112/119 artifacts. Result:
  `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE`; all `8` selected first-fire objects are
  `selected_never_supported_before_collision`, selected support-frame count is `0` in every row,
  selected closest pre-fire distance is `9.814849860027191-26.576615026308698 m`, and selected
  at-fire distance is `14.472507961609738-36.09143899155716 m`. Next honest step: report-level
  two-track support-core synthesis joining first-support object lifecycle, selected fire-object
  lifecycle, and first-fire replacement rank. No actor-causality, repair, threshold-value,
  safety/transfer/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 121 as the HUGSIM support-core two-track synthesis
  after iteration 120. Pre-registered ALONE (`f5cbd1e`), added analyzer/tests (`6a921ab`,
  targeted ruff/tests/docs green), then ran the analyzer ONCE over committed iteration-118/119/120
  reports only. Result: `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE`; all `8/8` rows
  preserve the two-track split, selected lifecycle is `selected_never_supported_before_collision`
  in all rows, and support-side branches split across absent, drifted, post-fire, and
  never-supported reference cases. Next honest step: documentation integration of the support-core
  taxonomy and claim boundary into the technical report/manuscript or a dedicated mechanism note.
  No actor-causality, repair, threshold-value, safety/transfer/deployment/robustness/benchmark/
  HD-Score-invariance, commercial-value, real-world/first-responder behavior, retuning,
  production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 122 as the HUGSIM support-core taxonomy
  documentation integration after iteration 121. Pre-registered ALONE (`1fa33f2`), added the
  bounded mechanism note plus technical-report/manuscript integration and verifier/tests
  (`32d2978`, targeted ruff/tests/docs green), then ran the verifier ONCE over committed
  markdown/json surfaces. Result: `SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE`; the mechanism
  note, technical report, and manuscript link iteration 121, preserve the `8/8` two-track split
  and `8/8` selected-never-supported counts, and carry the exact claim boundary. This closes the
  documentation gap only; it adds no HUGSIM evidence and does not upgrade the transfer null. Next
  operator-requested action: mission-level evidence/alignment audit across Sentinel's results,
  claims, docs, and next-step framing. No actor-causality, repair, threshold-value, transfer
  upgrade, safety/deployment/robustness/benchmark/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 123 as the operator-requested mission evidence and
  frontier-alignment audit after iteration 122. Pre-registered ALONE (`fa3359c`), added the
  source-backed audit note, verifier/tests, and surgical README/frontier-memory freshness fixes
  (`51e09d2`, targeted ruff/tests/docs green), then ran the verifier ONCE. Result:
  `MISSION_EVIDENCE_ALIGNMENT_AUDIT_COMPLETE`; all `7` checks passed with `0` problems and `7`
  source anchors. The audit fixed two concrete freshness issues: README no longer says the current
  campaign is only "Ninety-three registered iterations", and the July 13 frontier memory now marks
  iteration 84 as historical and points to the iteration-122 support-core taxonomy note. Next
  bounded options: manuscript/report freshness pass, blind-spot/scenario-generation design,
  higher-fidelity perturbation successor, explicit mission/rulebook boundary, or one-page external
  claim ledger. No actor-causality, repair, threshold-value, transfer upgrade, safety/deployment/
  robustness/benchmark/population-rate/HD-Score-invariance, commercial-value, real-world/
  first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 124 as the manuscript/report freshness pass after
  iteration 123. Pre-registered ALONE (`39e3ad5`), added bounded report/manuscript edits plus
  verifier/tests (`509fa79`, targeted ruff/tests/docs green), then ran the verifier ONCE. Result:
  `MANUSCRIPT_REPORT_FRESHNESS_COMPLETE`; all `6` checks passed with `0` problems. The technical
  report now says refreshed 2026-07-14 after iterations 122-123, the manuscript no longer says
  "all nineteen iterations", and both durable paper surfaces explicitly name the HUGSIM transfer
  null, link the support-core taxonomy and mission-audit notes, and carry the bounded claim
  boundary. No actor-causality, repair, threshold-value, transfer upgrade, safety/deployment/
  robustness/benchmark/population-rate/HD-Score-invariance, commercial-value, real-world/
  first-responder behavior, retuning, production, or commercial claim.
- 2026-07-14: Codex — continued into iteration 125 as the support-core blind-spot/scenario design
  lane after iteration 124. Pre-registered ALONE (`882ee5f`), added the generator/tests
  (`5e6249e`, targeted ruff/tests/docs green), then ran the generator ONCE over committed
  iteration-121/122/123/124 surfaces. Result:
  `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE`; five archetypes cover all `8` support-core
  rows exactly once, with `0` duplicate and `0` missing slots. Archetypes split into `3`
  selected-nearest and `2` selected-not-nearest classes, and timing-gap classes split into `3`
  measured support-gap, `1` post-fire support, and `1` no-pre-fire-support archetype. This is a
  design surface only; no scenario generation, GPU launch, HUGSIM run, repair, threshold-value,
  safety/deployment/robustness/benchmark/population-rate/HD-Score-invariance, commercial-value,
  real-world/first-responder behavior, retuning, production, or commercial claim.
