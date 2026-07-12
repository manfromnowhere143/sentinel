# Iteration 47 - nuScenes map-expansion staging + HUGSIM OFF-baseline completion pre-registration

Frozen before any iteration-47 tooling, download, byte movement, GPU command, simulator
launch, or claim. Committed alone, before any staging or run script exists. This is the fresh
completion pre-registration named by the iteration-46 successor boundary
(`experiments/iter46_hugsim_off_baseline/RESULT.md`): "(a) stages the official nuScenes map
expansion pack at `/datasets/nuscenes-full/maps/expansion/` with provenance receipts, and
(b) re-runs the failed portion of the frozen schedule ... under freshly frozen completion
bars."

**Honest framing (binding).** Iteration 46's null stands as published: its C1 bar failed, its
crash-loop falsifier fired in dual-failure form, and nothing here repairs that retroactively.
Iteration 47 re-earns completion under this fresh pre-registration with its own frozen bars.
The 38 completed iteration-46 episodes are carried as committed evidence (explicit
justification below), not silently re-scored.

## Research question

After staging the official nuScenes map expansion pack, do the 14 previously failed episodes —
the seven `load_HD_map: true` `-medium-01` scenarios x 2 runs — complete closed-loop
end-to-end, so that the full frozen 52-episode monitor-OFF arm (38 carried + 14 new) satisfies
the completion bars and Stage 2 (OFF vs released union) has a complete, provenance-locked OFF
arm to pair against?

## Stage A — map-expansion staging gate (iteration-28-class)

**Frozen source.** The only allowed dataset asset is the official nuScenes **Map expansion
pack v1.3** (`nuScenes-map-expansion-v1.3.zip`, listed at ~0.38 GB on the official download
page). Source preference order, per the iteration-28 precedent (its committed provenance
records host `motional-nuscenes.s3.amazonaws.com` — the official packages are served from a
public AWS bucket):

1. `public_url`: the public motional-nuscenes AWS bucket
   (`https://motional-nuscenes.s3.amazonaws.com/public/v1.0/nuScenes-map-expansion-v1.3.zip`).
2. `signed_url`: a time-limited official signed URL provided by Daniel (uncommitted file,
   iteration-28 handling: no query strings, cookies, tokens, or credentials committed).

License basis: Daniel's registered nuScenes account covers the dataset's non-commercial terms
of use; the pack is used only under that registration, for this research. The agent handles no
credentials.

**Frozen destination.** Archive at
`/datasets/nuscenes-full/archives/nuScenes-map-expansion-v1.3.zip`; extraction into
`/datasets/nuscenes-full/maps/` only (the zip ships `expansion/`, `basemap/`, and
`prediction/` subtrees; the four pre-existing bitmap PNGs at `maps/` top level are not
modified or deleted). No other root is mutated.

**Stage-A bars (all required):**

| bar | required value |
|---|---|
| archive staged with recorded size + SHA256 | `1` archive, both values in committed receipts |
| archive bytes sanity range | `>= 100,000,000` and `<= 2,000,000,000` |
| committed secret-bearing URL/query material | `0` (redacted provenance: scheme, host, basename, bytes, SHA256 only) |
| unsafe zip members (absolute path or `..` traversal) | `0` accepted |
| extraction root | `/datasets/nuscenes-full/maps/` only |
| four expansion vector maps present | `expansion/singapore-onenorth.json`, `expansion/singapore-hollandvillage.json`, `expansion/singapore-queenstown.json`, `expansion/boston-seaport.json`, each existing with size `>= 1,000,000` bytes |
| destination preflight free space | `>= 20 GiB` on `/datasets/nuscenes-full` |
| Docker/model/simulator runs during Stage A | `0` |

If Stage A fails any bar or the pack is unavailable from both allowed sources, publish the
staging null at full weight and STOP: Stage B does not launch.

## Stage B — completion re-run of the failed portion (frozen schedule)

**Frozen 14-episode schedule.** Exactly the iteration-46 dual-failure set: the seven
`load_HD_map: true` `-medium-01` scenarios, in lexicographic order, x 2 runs each, the two
runs back-to-back per scenario (preserving the within-launch pair structure iteration 46
established):

```
scene-0038-medium-01  r1, r2
scene-0051-medium-01  r1, r2
scene-0062-medium-01  r1, r2
scene-0064-medium-01  r1, r2
scene-0071-medium-01  r1, r2
scene-0138-medium-01  r1, r2
scene-0166-medium-01  r1, r2
```

No other episode is scheduled. The scenario yamls are the same released files frozen in
iteration 46; the launcher re-verifies all 52 per-file SHA256 receipts from the iteration-46
manifest as a hard provenance gate.

**Carried episodes (justification, binding).** The 38 completed iteration-46 episodes are
carried, not re-run, because: (1) each is committed evidence behind the iteration-46 proof
(`experiments/iter46_hugsim_off_baseline/proof-off/episodes/`) and the committed heavy-artifact
SHA manifest for the on-box collection root; (2) the environment is provenance-locked — the
launcher refuses to start unless every frozen iteration-46 value (repo SHAs, checkpoint SHA,
shim SHA, image id, all 52 yaml SHAs) still holds, so the carried and new episodes run under
byte-identical code, checkpoint, and configs; (3) within-scenario stochastic pairs are intact
per launch — all 19 carried pairs were produced back-to-back within a single launch, and the 7
new pairs will be produced back-to-back within this launch. The analyzer additionally verifies
the carried episodes byte-match the committed iteration-46 artifacts before scoring them.

**Frozen environment and provenance (hard gate at launch, `I47_OFF_PROVENANCE_FAIL` on any
mismatch).** All values identical to iteration 46:

- HUGSIM `/opt/sentinel-stack/HUGSIM` @ `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
  UniAD_SIM `/opt/sentinel-stack/UniAD_SIM` @ `5fb279e39912a5ac7f58e00d56b065cadcd0a749`.
- Docker image `uniad:latest` id `f73ef3884063`; checkpoint `uniad_base_e2e.pth` SHA256
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`.
- Iteration-45 CPU-fallback shim `/opt/sentinel-stack/hugsim-shim/sitecustomize.py` SHA256
  `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c` (byte copy committed at
  `../iter46_hugsim_off_baseline/shim/sitecustomize.py`).
- All 52 scenario-yaml SHA256s from the iteration-46 manifest verify (`sha256sum -c`).
- Single-tenant rule: refuse to start if any Docker container is up.
- Additionally (iteration-47 gates): the four Stage-A map jsons exist; the carried D0 verdict
  file reads `stochastic` (the branch decision was made once, in iteration 46, and is carried —
  no re-probe); all 38 carried completed episode dirs are present in the collection root with
  non-failed `episode_meta.json`.

**Collection root.** The iteration-46 root `/datasets/nuscenes-full/hugsim/iter46_runs/` is
reused so the launcher's resume-skip carries the 38 completed episodes in place
(`I47_OFF_EP_SKIP_DONE` markers). Stale `__failed` dirs are archived under
`prior_launches/<utc>/` on the box as defect evidence (their contents are already committed in
the iteration-46 proof). The iteration-46 `heavy_manifest.txt` box file is left untouched;
iteration 47 writes `heavy_manifest_iter47.txt` covering all 52 episodes. The launcher keeps
the iteration-46 per-scene prep surface (idempotent temp-dir zip extraction keyed on
`cfg.yaml`; idempotent 3DRealCar `postprocess/shadow.pth -> ..` compatibility symlinks;
`cfg.yaml` `model_path` rewrite with `.orig` preserved), retry-once-per-episode, the
consecutive-failure and disk guards, per-episode pair markers, log
`/var/log/sentinel-iter47-completion.log`, and done marker **`I47_OFF_COMPLETION_DONE`**.

**Completion bars (all required for a pass), evaluated over ALL 52 episodes (38 carried + 14
new) by ONE run of the committed analyzer:**

- **C1 — all 52 episodes complete.** Every episode of the frozen stochastic schedule (26
  scenarios x 2) terminates by the benchmark's own rule within the 1200 s per-episode bound
  and has an `eval.json` with a finite `hdscore`, after at most ONE scripted retry per
  episode. A single episode failing both attempts fails C1.
- **C2 — per-step logs for all 52.** Every episode's collection dir has `output.txt` with
  round-trip lines and a positive step count in `episode_meta.json`; heavy per-step records
  (`data.pkl`, `infos.pkl`) stay on the box behind the committed SHA manifest.
- **C3 — evidence committed.** Stage-A receipts, launch receipts, the run log, the 14 new
  episode dirs' `eval.json`/`output.txt`/`episode_meta.json`, `heavy_manifest_iter47.txt`, the
  carried-integrity check output, and the analyzer report committed under this experiment
  (files >90 MB split into `.part-*`). Carried-episode integrity: the analyzer verifies each
  of the 38 carried episodes' `eval.json` + `episode_meta.json` are byte-identical to the
  committed iteration-46 copies before scoring; any mismatch fails C3.

The pairing-infeasibility falsifier is re-evaluated over the full 26 within-scenario pairs
(median |dHD| > `0.15` fires it), because the OFF arm is only Stage-2-usable if pairing holds
over the complete set. The plausibility note from iteration 46 applies unchanged (context, NOT
a bar).

## Budget (frozen, with the arithmetic)

- Stage A: one ~0.38 GB download + extraction; no GPU time.
- Stage B worst case: 14 episodes x 2 attempts x 20-min timeout cannot all be spent
  (retry-once + 3-consecutive-dual-failure abort); ceiling 14 x ~22 min = **~5.1 GPU-hours**.
  Expected from the 38 completed iteration-46 episodes (114-481 s each) plus first-time
  vector-map construction overhead: **~1-2.5 GPU-hours**.

## Named falsifiers

- **Map pack unavailable.** The pack cannot be fetched from the public bucket and Daniel does
  not provide a signed official URL, or any Stage-A bar fails → publish the staging null
  (`MAP_STAGING_NULL`) at full weight; Stage B never launches.
- **Map-loading path fails for a NEW reason after staging.** Any scheduled episode still dies
  before the client's first step (map construction, trajdata, or a further staging-layout
  defect) → C1 fails; publish the null naming the new mechanism with the preserved log
  evidence.
- **Client crash/deadlock loop.** Any episode failing both attempts fails C1; THREE
  CONSECUTIVE dual-failure episodes abort early (`I47_OFF_ABORT_CONSECUTIVE_FAILURES`) —
  publish the null rather than burning the budget.
- **VRAM overflow.** CUDA OOM reported per-episode; systematic OOM (the consecutive guard
  firing on it) is the falsifier form of the null.
- **Pairing infeasibility.** Median within-scenario |dHD| over the full 26 pairs > `0.15` →
  publish as a pairing-infeasibility finding; Stage-2 design must change.
- **Disk exhaustion.** Guard before every episode; abort below 20 GiB free
  (`I47_OFF_ABORT_DISK`) — an interrupted run with a resume point, not a null, unless space
  cannot be recovered.

## Forbidden claims (binding)

This is the **OFF arm only**. No transfer, monitor, OFF-vs-ON, benchmark-ranking, robustness,
deployment, or safety claim; no UniAD performance ranking; no HD-Score interpretation beyond
completion accounting and the registered plausibility context. A pass authorizes exactly ONE
thing: the Stage-2 OFF-vs-released-union pre-registration (iteration 48). It does not
authorize the Stage-2 runs. The iteration-39 wording rules apply to every doc this iteration
touches.

## Required proof artifacts

- `proof-staging/`: redacted source provenance + archive SHA256/bytes receipts, zip-safety
  report, four-json existence/size check, SHA256 sidecar.
- `proof-completion/receipts.json`: launch provenance-gate output (all frozen values
  re-verified, map jsons present, carried verdict + carried-episode gate).
- `proof-completion/episodes/<scenario>__r<n>/`: the 14 new episodes' `eval.json`,
  `output.txt`, `episode_meta.json`.
- `proof-completion/i47-completion-run.log`: the full box-side run log
  (`/var/log/sentinel-iter47-completion.log`) with `I47_OFF_EP_START`/`I47_OFF_EP_RC`/
  `I47_OFF_EP_DONE` pair markers and the final `I47_OFF_COMPLETION_DONE` marker.
- `proof-completion/heavy_manifest_iter47.txt`: SHA256 manifest of heavy on-box artifacts for
  all 52 episodes.
- `proof-completion/carried_integrity.json`: byte-identity check of the 38 carried episodes
  against the committed iteration-46 artifacts.
- `proof-completion/off_completion_report.json`: the single analyzer run over all 52.

## Protocol

1. Commit this `HYPOTHESIS.md` alone, CI green, before any tooling exists.
2. Commit tooling: Stage-A staging script (download, hash, safe-extract, four-json check,
   redacted receipts), the Stage-B launcher (the iteration-46 launcher adapted to the frozen
   14-episode schedule with the added iteration-47 gates), the analyzer (reusing the committed
   iteration-46 analyzer for the 52-episode evaluation plus the carried-integrity check), and
   unit tests; ruff + pytest + validate_docs green.
3. Execute Stage A; commit receipts. On unavailability or any Stage-A bar failure, publish the
   staging null and STOP.
4. Launch Stage B detached per the box playbook; verify the first formerly-failing episode
   (`scene-0038-medium-01` r1) gets PAST map loading to client stepping before leaving; record
   IN FLIGHT state in CONTINUITY/HANDOFF. Never alongside another GPU job.
5. On `I47_OFF_COMPLETION_DONE`: collect the 14 episodes + receipts + log, run the committed
   analyzer ONCE over all 52, publish `RESULT.md` at full weight (pass or null), update
   README/CONTINUITY/HANDOFF. A pass authorizes ONLY the iteration-48 Stage-2
   pre-registration; no Stage-2 run happens under this pre-registration.
