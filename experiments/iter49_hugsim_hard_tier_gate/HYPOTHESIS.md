# Iteration 49 - HUGSIM hard/extreme-tier transfer gate: monitor-OFF vs released union

Frozen before any iteration-49 tooling, launcher, byte movement, GPU command, simulator
launch, or claim. Committed alone. This is the named hard-tier successor to iteration 48's
`TRANSFER_NULL` (`experiments/iter48_hugsim_transfer_gate/RESULT.md`, successor boundary
item (c)): the collision-dominant regime test. It authorizes the Stage-2-style runs it
describes and nothing else. A pass OR a null publishes at full weight — it is the
collision-regime transfer answer for the released union.

## Research question

Iteration 48 measured that the released union's NeuroNCAP benefit does not transfer to
HUGSIM easy+medium scenarios (mean paired HD delta `−0.0166`, CI `[−0.0551, +0.0255]`),
while the mechanism (fire, latch, release) demonstrably operates there. NeuroNCAP's benefit
was earned on scripted safety-critical collisions. Does the benefit reappear on HUGSIM's
hard/extreme tiers, where aggressive and adversarial actors dominate and the NC term
carries more of the score?

**H (directional, honest):** on the frozen hard/extreme-tier subset, the paired HD-Score
delta (ON − OFF) is positive with the 95% scenario-clustered CI excluding zero. The stated
mechanism: 15 of the 26 scheduled scenarios script an `AttackPlanner` adversarial actor
(all 13 extreme plus `scene-0041-hard-00` and `scene-0411-hard-00`), so collisions the
monitor can prevent should dominate outcomes. The honest alternatives, all publishable at
full weight: a null (the benefit does not reappear even where collisions dominate — a
stronger external-validity boundary than iteration 48's), a negative (over-braking costs
exceed collision savings — the iteration-48 `scene-0051` localized over-braking pattern
generalizing), or a boundary null via F2.

## Read-only inventory (performed 2026-07-12 before this pre-registration; no bytes moved)

The staged XDimLab/HUGSIM release at `/datasets/nuscenes-full/hugsim/` ships exactly two
harder tiers for nuScenes: `hard-00` and `extreme-00`, one each for all 18 released scenes
(36 yamls total at `extracted/scenarios/nuscenes/`; 88 yamls across all tiers). All 44
distinct 3DRealCar actor assets referenced by the 36 harder-tier yamls are present with
`gs.pth`. Exactly two harder-tier yamls set `load_HD_map: true`: `scene-0013-hard-00` and
`scene-0920-hard-00`; the four `maps/expansion/*.json` vector maps are staged (iteration-47
Stage A). Actor counts are 0-2 per yaml; every extreme yaml carries at least one
`AttackPlanner` (18/18), and three hard yamls do (`scene-0041`, `scene-0411`,
`scene-0930`). The scenarios use the same yaml schema the UniAD_SIM client already drives
(iterations 45-48); no other planner types or asset classes appear.

## Frozen monitored arm (binding; any deviation = VOID, falsifier F1 — identical to iteration 48)

The committed iteration-48 client patch is used UNCHANGED, as a byte copy:
`experiments/iter48_hugsim_transfer_gate/client_patch_union_iter48.py`, SHA256
`6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`. The launcher refuses to
start unless the staged patch file hashes to exactly this value, and the receipts record it.
The patch's baked-in frozen parameters are EXACTLY the NeuroNCAP-frozen values
(`cpa_margin = 1.5` m, `ttc_thresh = 2.5` s, `min_closing = 3.0` m/s, `max_gap = 30.0` m,
`min_score = 0.3`, `release_k = 4`, `dt = 0.5` s); only `SENTINEL_ENABLED` is forwarded
into the container. **Any retuning, rescaling, or "adaptation" of any of these values for
the harder tiers — before, during, or after the run — voids the iteration (F1).** The
patch's load marker, per-frame `SENTINEL_I48_DECISION` lines, and
`sentinel_iter48_decisions.jsonl` full-input rows keep their iteration-48 names because the
byte copy is the point; the analyzer greps those exact strings.

## Frozen schedule and pairing (binding)

- **Scenario universe:** all 36 harder-tier yamls, with the per-file SHA256 manifest below
  re-verified at launch as a hard provenance gate.
- **Scheduled subset:** the lexicographically first 26 of the 36 (the iteration-46
  selection rule) — 13 scenes x {extreme-00, hard-00}:
  scenes `0013, 0038, 0041, 0051, 0062, 0064, 0071, 0138, 0166, 0167, 0254, 0383, 0411`.
  This is 13 extreme + 13 hard, includes iteration 48's over-braking scene (`scene-0051`)
  in both tiers, and adds four scenes never driven by this pipeline
  (`0167, 0254, 0383, 0411` — extraction from their staged zips is part of the launch, per
  the iteration-46 idempotent temp-dir pattern).
- **Arms and N:** N=2 per scenario per arm → `26 x 2 x 2 = 104` episodes.
- **Pairing (carried stochastic D0 verdict, decided once in iteration 46 — no re-probe):**
  WITHIN-LAUNCH, BACK-TO-BACK. Per scenario, in lexicographic order:
  `OFF r1 -> ON r1 -> OFF r2 -> ON r2`, all inside a single launch. Paired unit =
  (ON rN − OFF rN) per scenario per N → `52` paired HD deltas in `26` scenario clusters.
- **Noise floor (stated honestly):** the measured OFF-OFF spreads (iterations 46/47/48:
  medians `0.0245-0.0307`, heavy tails to `0.74`) are easy+medium measurements; the
  harder-tier OFF-OFF noise is UNKNOWN before this run. F5 measures it fresh from this
  run's own 26 OFF-OFF pairs, same `0.15` bar. No per-pair delta is interpretable alone.

### Frozen 26-scenario schedule with per-yaml SHA256 (inventoried read-only)

| scenario | sha256 |
|---|---|
| scene-0013-extreme-00 | 7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442 |
| scene-0013-hard-00 | 6947a5381c09485f20d5fed55eef2406d868ce047bdd44864aad81902f54e48e |
| scene-0038-extreme-00 | ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776 |
| scene-0038-hard-00 | 5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d |
| scene-0041-extreme-00 | 7d186ac9491de1cc3aab58a3a636ab0eb00088179f68d8a563214aaada3aa8af |
| scene-0041-hard-00 | ac8c82778713aecf6f9b1af9dbe646f51db5bde7a15b124a24f2f733e11cb1fa |
| scene-0051-extreme-00 | 0bde23ad758f52aa74946c9db7b68888537308f020315476de7bcbb43b39a09d |
| scene-0051-hard-00 | 10d048c8d76c06a72696e9fe519cb2361b5b54854eea4acaccedf8fdd14a9d39 |
| scene-0062-extreme-00 | 0a89b5660cf50720263b2379b0c2341c3b8c1a4d2fadb07eff30c7b519e26e2e |
| scene-0062-hard-00 | a318c5a49a43fc50e66b6b1b73bd53df165cca3c49e409e7b22f65276361e90e |
| scene-0064-extreme-00 | b223ef214c1ea8961b5103e34650b5e664f40797721aa18aa35ca50f2b70f4c0 |
| scene-0064-hard-00 | 2acfe05ed22c4c287daf74dabbbb6ef61d130bd9351088fb1be40b9270d6516e |
| scene-0071-extreme-00 | 97b55b931c7ac5bf5991b1b0ba46907468dc4c6c8a3108df5b2dddbcf43ab0ed |
| scene-0071-hard-00 | 1fd0c4b87d3b1fb28ecf0672b0779150fb0b866e93e168bd4a8f0babee3d6ee7 |
| scene-0138-extreme-00 | d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9 |
| scene-0138-hard-00 | 8d0e3ec0d0068ae51047c0f3d2d63995d3a9dfeb60dc4071d7ec017d869fed2e |
| scene-0166-extreme-00 | c1ee5627487ece22e88937a43f82901fff1a823ab7447e45cac51fa2d922099f |
| scene-0166-hard-00 | 33c2d545537a213510383e33bc406b4f4131bead5c3278d7a91d3375976a612a |
| scene-0167-extreme-00 | bd247f7111566c7ae2c232b1ce06d7e1e6173f1f4616a84131db413213af8065 |
| scene-0167-hard-00 | ba58cafd0a571c4701ddba37aace7a3f4618d206796e749e1fb67b21edee8ff7 |
| scene-0254-extreme-00 | 40c32535a7ac7d0bff923374591d64ddeca89922182e391ba5b407718b46e08c |
| scene-0254-hard-00 | 506229ef5fe677ffe2fee91b940a9d1b633a5d4177fbcd33b2fb0b4e7e2eb937 |
| scene-0383-extreme-00 | f91d42db520f1e4d716fdbd3544fb701d4550062b2f9f933c86f3eb09c958ecf |
| scene-0383-hard-00 | 82b36b555747ab3934085ba170799cbe957c7d2bcc64b3cb8495dc64111bc92a |
| scene-0411-extreme-00 | cd9c86bd4dbad2e6ff74f275f9fe43ad60aa0d9bf314971473ae2ddb01b703fb |
| scene-0411-hard-00 | 9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9 |

The 10 unscheduled harder-tier yamls (scenes `0418, 0528, 0661, 0920, 0930`) are part of
the 36-yaml launch manifest for provenance but are NOT run; expanding to them requires a
fresh pre-registration.

## Pre-launch asset pre-check gate (the iterations-46/47 lesson, pre-declared)

Iteration 46 lost 14 episodes to an unstaged map pack discovered only at episode time;
iteration 47 fixed it by staging with receipts. This iteration checks assets BEFORE launch,
as a hard gate (`I49_PRECHECK_OK` / `I49_PRECHECK_FAIL`, refuse to run on failure):

1. **Maps:** all four `maps/expansion/*.json` present and non-empty (`scene-0013-hard-00`
   in the schedule sets `load_HD_map: true`).
2. **Scenes:** for each of the 13 scheduled scenes, either the extracted
   `scenes/nuscenes/<scene>/cfg.yaml` exists or the staged zip
   `scenes/nuscenes/<scene>.zip` exists and lists a `cfg.yaml` member (read-only zip
   listing; extraction itself happens at episode time per the idempotent iteration-46
   pattern).
3. **Actor assets:** every 3DRealCar id referenced by the 26 scheduled yamls has its
   directory with `gs.pth`; the iteration-46 amendment-b compatibility symlinks are applied
   idempotently after the check.

If the pre-check fails and the missing asset is not something already covered by a
committed staging pass, the iteration publishes a scoping/staging null and stops — no
partial launch.

## Frozen paired-analysis design (binding)

ONE run of a committed analyzer over committed artifacts, identical in form to iteration 48
with the seed advanced:

- **Primary bar (the collision-regime transfer verdict):** the 95% scenario-clustered
  bootstrap CI (resample the 26 scenario clusters with replacement, `10,000` draws, seed
  `49`) on the MEAN paired HD-Score delta (ON − OFF) over the 52 pairs.
  - `PASS_TRANSFER_POSITIVE` if the CI excludes zero from below.
  - `TRANSFER_NEGATIVE` if the CI excludes zero from above — full weight.
  - `TRANSFER_NULL` if the CI includes zero — full weight, noise floor stated.
- **Heavy-tail treatment (stated up front):** the MEDIAN paired delta with the same
  bootstrap draws and the full per-pair table are reported alongside; on mean/median CI
  sign disagreement the verdict follows the pre-registered primary (mean) and the
  disagreement is a reported caveat. Bars never move after data.
- **Secondaries (descriptive, NOT bars):** paired deltas of NC, DAC, the weighted TTC/COM
  terms, and RC; ON-arm firing statistics (fired/brake frames, releases, intervention
  episodes); per-episode brake-frame fractions and step-cap episodes, explicitly to make an
  iteration-48 `scene-0051`-pattern recurrence (localized over-braking) visible on the
  record. A per-tier (hard vs extreme) descriptive split of the paired deltas is reported
  for context only — 13 pairs per tier is not powered for a tier claim and none is made.
- **F1 additionally checks the patch byte-identity mechanically:** the receipts'
  `monitor_patch_sha` must equal the frozen value above, and every decision-log params row
  must equal the seven frozen values, else `VOID_RETUNED`.

## Frozen environment and provenance (hard gate at launch, `I49_PROVENANCE_FAIL` on any mismatch)

Identical to iteration 48 except where named:

- HUGSIM `/opt/sentinel-stack/HUGSIM` @ `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
  UniAD_SIM `/opt/sentinel-stack/UniAD_SIM` @ `5fb279e39912a5ac7f58e00d56b065cadcd0a749`
  (plus the byte-identical iteration-48 monitor patch applied at launch — the ONLY
  permitted delta, SHA re-verified as above).
- Docker image `uniad:latest` id `f73ef3884063`; checkpoint `uniad_base_e2e.pth` SHA256
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`; iteration-45 shim
  `/opt/sentinel-stack/hugsim-shim/sitecustomize.py` SHA256
  `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c`.
- All 36 harder-tier scenario-yaml SHA256s verify; the asset pre-check gate passes; the
  carried D0 verdict file reads `stochastic` (no re-probe).
- Single-tenant rule: refuse to start if any Docker container is up.
- Launcher discipline carried: per-episode retry-once, 3-consecutive-dual-failure abort
  (`I49_ABORT_CONSECUTIVE_FAILURES`), 20 GiB disk guard (`I49_ABORT_DISK`), per-episode
  arm-labelled markers (`I49_EP_START`/`I49_EP_RC`/`I49_EP_DONE`), fresh collection root
  `/datasets/nuscenes-full/hugsim/iter49_runs/`, log `/var/log/sentinel-iter49-hard.log`,
  done marker **`I49_HARD_DONE`**.

## Completion bars (all required before the transfer verdict is read)

- **K1 — all 104 episodes complete:** benchmark-rule termination within the 1200 s
  per-episode bound, finite `hdscore` in `eval.json`, at most ONE scripted retry each. Any
  episode failing both attempts → completion null, NOT a transfer verdict.
- **K2 — per-step and decision logs for all 104:** `output.txt` round-trip lines, positive
  step count, the patch load marker on every episode; ON episodes additionally carry the
  per-frame decision lines and the full-input JSONL. Heavy artifacts stay on the box behind
  a committed SHA manifest.
- **K3 — evidence committed:** launch receipts (patch SHA, param echo, carried D0), the run
  log, all 104 episodes' `eval.json`/`output.txt`/`episode_meta.json` (+ ON decision
  JSONLs), the heavy manifest, and the single analyzer report; files >90 MB split into
  `.part-*`.

## Budget (frozen, with the arithmetic)

- `104` episodes x `1200` s single-attempt ceiling = `124,800` s = **34.7 GPU-hours
  absolute ceiling** (<= 35); the retry-once clause is bounded by the consecutive-failure
  abort, so the practical state ceiling stays ~35 GPU-h and an early abort costs less.
- Expected: iteration 48 measured `9.17` GPU-h of episode walls on this exact 104-episode
  schedule shape at easy+medium; harder tiers plausibly brake more and hit more step caps
  (iteration 48's two cap-bound episodes ran ~1,170-1,190 s each), so **~9-18 GPU-hours
  expected**, one detached run, box otherwise idle.

## Named falsifiers

- **F1 — retuning void.** Any launched monitor parameter differing from the seven frozen
  values, any patch byte differing from the committed iteration-48 copy, or any change
  between launch and analysis → `VOID_RETUNED`, no transfer verdict, no partial claim.
  Mechanical: patch SHA in receipts + params echo in every decision row.
- **F2 — trigger mistuned for splat tracking noise (either direction, bars identical to
  iteration 48).** Pooled over all 52 ON episodes: brake frames > `80%` of monitored frames
  (fires constantly) OR `0` fired frames (fires never) → transfer-boundary null naming the
  mechanism; NO retuning on these scenes. Iteration 48 measured `26.9%` pooled on
  easy+medium; denser threats should raise this legitimately — the bar is unchanged and
  pre-registered.
- **F3 — over-braking (RC collapse), the scene-0051 recurrence watch.** Mean paired RC
  delta (ON − OFF) < `−0.30` → named in the published verdict regardless of the primary HD
  outcome. The per-episode brake-fraction and step-cap tables (secondaries) put any
  localized recurrence on the record even below the bar.
- **F4 — crash/deadlock loop.** Any episode failing both attempts fails K1; three
  consecutive dual failures abort early → completion null rather than burning budget. The
  four never-driven scenes (`0167, 0254, 0383, 0411`) are the highest-risk surface; their
  zips and actor assets are pre-checked, but a scene that cannot complete either arm is
  exactly this falsifier's territory (the iteration-46 lesson: publish the completion null,
  do not improvise).
- **F5 — pairing infeasibility (fresh, harder-tier).** Median |dHD| over this run's 26
  fresh OFF-OFF pairs > `0.15` → the pairing design is invalidated at this tier; publish as
  a pairing finding; the transfer CI is still reported but flagged noise-dominated.
- **F6 — VRAM overflow / disk exhaustion.** As iterations 46-48: systematic OOM via the
  consecutive guard is the falsifier form of the null; disk aborts are interrupted runs
  with a resume point, not nulls.
- **F7 — staging gap (pre-launch).** The asset pre-check gate fails → scoping/staging null,
  no launch, no partial run.

## Forbidden claims (binding)

No NeuroNCAP-equivalence claim (HD-Score on scripted harder tiers is still not NeuroNCAP's
metric or scene family). No deployment, real-world, production, or safety claim. No
benchmark-ranking or UniAD-performance claim. No monitor-robustness claim (iteration 43's
mild-fragile finding stands). No hard-vs-extreme tier claim (descriptive split only, not
powered). No generalization beyond UniAD-class planners on these 26 scenarios. The
iteration-39 wording rules apply to every doc this iteration touches. A pass authorizes
successor pre-registrations only; it does not itself authorize any run beyond the single
registered launch here.

## Required proof artifacts

- `proof-hard/receipts.json`: provenance-gate output (frozen SHAs, monitor-patch SHA,
  echoed parameter block, carried D0 verdict, pre-check summary).
- `proof-hard/episodes/<scenario>__<arm>_r<n>/`: all 104 episodes' `eval.json`,
  `output.txt`, `episode_meta.json` (+ ON `sentinel_iter48_decisions.jsonl`; any `__failed`
  dirs included).
- `proof-hard/i49-hard-run.log`: the full box-side log with arm-labelled markers and the
  final `I49_HARD_DONE`.
- `proof-hard/frozen_scenarios_hard.sha256`, `proof-hard/heavy_manifest_iter49.txt`.
- `proof-hard/transfer_report.json` (+ per-pair markdown table): the single analyzer run.

## Protocol

1. Commit this `HYPOTHESIS.md` alone, CI green, before any iteration-49 tooling exists.
2. Commit tooling: the launcher (iteration-48 pattern + the pre-check gate + I49 markers),
   the analyzer (seed 49, scenario list above, patch-SHA F1 check), and unit tests;
   ruff + pytest + validate_docs green.
3. Launch the single registered detached run per the box playbook; verify the pre-check,
   provenance gate, and the first OFF and first ON episodes complete before leaving; record
   IN FLIGHT + the on-done block in CONTINUITY; regenerate HANDOFF; push; stop.
4. On `I49_HARD_DONE`: collect and commit proof FIRST, run the committed analyzer ONCE,
   publish `RESULT.md` at full weight per the registered verdict classes
   (`PASS_TRANSFER_POSITIVE` / `TRANSFER_NEGATIVE` / `TRANSFER_NULL` /
   `TRANSFER_BOUNDARY_NULL_F2_*` / `VOID_RETUNED` / completion null / staging null), update
   README/CONTINUITY/HANDOFF.
