# Iteration 59 - HUGSIM actor-match support audit

Frozen before any iteration-59 launcher, analyzer, GPU command, simulator launch, proof artifact,
result, or claim. This is a bounded support audit only: it is not a transfer rerun, not a metric
retune, not an expanded-N benchmark, and not a safety result.

## Process disclosure

This is not blind. Iterations 48-58 are already published. Before freezing this file, the
iteration-54 provenance-support analyzer, the iteration-58 HUGSIM provenance canary proof, and the
iteration-48/49 scenario SHA manifests were inspected. Those inspections established:

- monitor first-fire object/path argmins are reconstructable from committed ON decision logs;
- committed iteration-48/49 HUGSIM evals did not contain collision actor identity;
- iteration 58 proved the byte-bound HUGSIM patch executes and emits top-level
  `collision_provenance` in real HUGSIM episodes;
- HUGSIM provenance contains collision type, timestamp, trajectory index, obstacle index/name,
  obstacle box, contact distance, nearest foreground, and planned ego pose;
- monitor decision logs and HUGSIM provenance use different coordinate conventions in the
  iteration-58 canary, so this audit must include a frozen frame-support gate before any
  actor-match interpretation.

The selected episodes below are chosen from committed iteration-54 category labels to cover
TTC-only, CPA-only, the one both-distinct case, and no-fire collision controls. The prior labels
are selection context only; the iteration-59 result must classify the newly run episodes from
their own logs and provenance.

## Research question

Given the byte-bound HUGSIM collision-provenance patch, can a bounded set of Sentinel ON collision
episodes support a same-run comparison between:

1. the monitor's first-fire hazard object/path, reconstructed from the released-union decision log;
2. the HUGSIM collision provenance emitted by `eval.json`;

and if support exists, how many classifiable rows are monitor-hazard / collision-actor geometric
matches versus mismatches?

This iteration may answer only support and descriptive match classification inside the registered
eight-episode envelope. It does not claim the distribution of all HUGSIM failures.

## Frozen schedule

Exactly eight ON episodes, in this order, with the released-union monitor patch and the
byte-bound HUGSIM provenance patch:

| audit id | scenario | committed source category used for selection | scenario SHA256 |
|---|---|---|---|
| `ttc_extreme_short` | `scene-0038-extreme-00` | prior unique-TTC short-lead AttackPlanner collision | `ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776` |
| `mixed_extreme` | `scene-0062-extreme-00` | prior TTC and CPA AttackPlanner collision variants | `0a89b5660cf50720263b2379b0c2341c3b8c1a4d2fadb07eff30c7b519e26e2e` |
| `both_distinct_extreme` | `scene-0138-extreme-00` | prior both-distinct post-collision-fire case | `d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9` |
| `nofire_hard_control` | `scene-0041-hard-00` | prior no-fire hard collision control | `ac8c82778713aecf6f9b1af9dbe646f51db5bde7a15b124a24f2f733e11cb1fa` |
| `cpa_medium_a` | `scene-0071-medium-00` | prior unique-CPA long-lead medium collision | `19542bfd37e20b34635f3b8279fa909a1a6dba0774b5c8076100b0969897faa5` |
| `ttc_medium_a` | `scene-0071-medium-01` | prior unique-TTC long-lead medium collision | `1fc17294a29cd90ba424c9d481d7f91f94aa8c5e9649ccf8c79115acc7a8744d` |
| `cpa_medium_b` | `scene-0166-medium-00` | prior unique-CPA long-lead medium collision | `f48075e69aa246bdd26b3fb468814151c412ebd0e94bf4f6c4313d3c6aba9430` |
| `ttc_extreme_b` | `scene-0383-extreme-00` | prior unique-TTC short-lead AttackPlanner collision with distinct CPA/TTC candidates | `f91d42db520f1e4d716fdbd3544fb701d4550062b2f9f933c86f3eb09c958ecf` |

No OFF arm is authorized. No extra scenario, duplicate, tier expansion, or replacement is
authorized except the standard retry-once for infrastructure failure used in the HUGSIM line.

## Frozen environment and patches

Hard launch gates:

- HUGSIM source HEAD must equal `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`.
- UniAD_SIM source HEAD must equal `5fb279e39912a5ac7f58e00d56b065cadcd0a749`.
- HUGSIM provenance patch file must hash to
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd` and either apply cleanly
  or already be applied by reverse-check.
- Released-union monitor patch must hash to
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`.
- Checkpoint, shim, Docker image, map-expansion JSONs, and carried D0 verdict follow the
  iteration-58 launch gates.
- Single-tenant rule: refuse to start if any Docker container is already running.

The HUGSIM source tree may receive only the byte-bound provenance patch. The UniAD_SIM tree may
receive only the byte-bound released-union monitor patch. No Sentinel thresholds, HUGSIM metric
constants, scenario selection, planner code, action control code, or HD-Score formulas may change.

## Frozen actor-match support rules

The analyzer must classify the newly run episodes only. It may use the iteration-54 reconstruction
logic for monitor first-fire argmins and the iteration-58 `collision_provenance` schema for HUGSIM
collision rows.

Per episode:

- `no_monitor_fire`: no fired monitor row exists; actor match is not attempted.
- `no_collision_provenance`: no top-level `collision_provenance` row exists; actor match is not
  attempted.
- `background_collision_only`: all collision provenance rows are background; actor match is not
  attempted.
- `post_collision_fire`: first monitor fire is after the first foreground collision provenance
  timestamp; actor match is not attempted.
- `classifiable_foreground`: first monitor fire is at or before the first foreground collision
  provenance timestamp, the monitor argmin is unique for the firing channel, and the frozen
  coordinate bridge below yields a finite distance.

Frozen coordinate bridge:

1. Reconstruct the first-fire monitor argmin object exactly as in iteration 54.
2. Convert that object's logged world `x,y` into the monitor ego-local frame using the logged
   `l2g_r_mat` and `l2g_t`.
3. Compare the HUGSIM convention `(forward, lateral)` to `(monitor_local_y, monitor_local_x)`.
4. If the HUGSIM foreground collision timestamp is later than the first-fire timestamp, propagate
   the monitor object by its logged velocity over that lead time before the transform; if not,
   use the first-fire object position directly.
5. Compute Euclidean center distance in the HUGSIM `(forward, lateral)` plane against the
   first foreground `obs_box[:2]`.

Class labels for classifiable foreground rows:

- `actor_match`: distance `<= 3.0 m`;
- `actor_mismatch`: distance `> 6.0 m`;
- `actor_ambiguous`: distance in `(3.0 m, 6.0 m]`.

The `3.0 m` support threshold is deliberately looser than a strict object-center identity claim:
iteration 58 showed a single-object canary can have meter-scale convention/center offsets. The
`6.0 m` mismatch threshold is wider than a passenger-car length and is used only for descriptive
mismatch classification, not a safety claim.

## Frozen bars

- `ACTOR_MATCH_INFRA_NULL`: any hard launch gate fails, any scheduled episode fails both
  attempts, proof collection is incomplete, an ON decision log is missing, scalar metric schema is
  broken, or top-level `collision_provenance` is absent from every completed eval.
- `ACTOR_MATCH_SUPPORT_NULL`: infrastructure passes, but fewer than three episodes are
  `classifiable_foreground`.
- `ACTOR_MATCH_AUDIT_COMPLETE`: infrastructure passes and at least three episodes are
  `classifiable_foreground`. The match/mismatch/ambiguous counts are then descriptive outputs
  under this bounded support audit.

## Forbidden claims

No transfer, benchmark, safety, robustness, deployment, real-world, HD-Score improvement,
HD-Score-invariance, all-HUGSIM distribution, actor-causality, production, acquisition-value, or
retuning claim. A nonzero match count does not prove Sentinel prevents HUGSIM collisions; a
nonzero mismatch count does not prove a repair. This audit may only claim whether the registered
episodes support same-run monitor-hazard versus HUGSIM-collision actor comparison, and report the
descriptive classifications if support exists.

## Required proof artifacts

- launcher and analyzer source plus unit tests;
- `proof-actor-match/receipts.json`;
- `proof-actor-match/i59-actor-match-run.log`;
- per-episode `eval.json`, `output.txt`, `episode_meta.json`, and `sentinel_iter48_decisions.jsonl`;
- `proof-actor-match/actor_match_report.json`;
- `proof-actor-match/actor_match.md`;
- `proof-actor-match/analyze_actor_match.command.txt`;
- `proof-actor-match/heavy_manifest_iter59.txt` if heavy on-box artifacts are not copied.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add launcher/analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Copy the launcher and byte-bound patch artifacts to the GPU box.
4. Launch exactly the registered eight-episode ON audit, detached, only if the box is idle.
5. On done marker: collect proof, commit proof first, run analyzer once, publish `RESULT.md` at
   full weight, update docs/handoff, verify, and push.
