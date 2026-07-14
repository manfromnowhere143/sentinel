# Iteration 113 - HUGSIM support-core actor-match support audit

Frozen after iteration 112 was published and pushed, but before any iteration-113 analyzer,
actor-match classification, proof artifact, result, handoff update, or claim. This is an offline
analyzer over the committed iteration-112 support-core execution proof only. It launches no GPU
work and changes no code under test.

## Process disclosure

This is not blind. Iteration 112 has already published the execution proof:

- `8/8` registered support-core slots completed;
- `0` retries;
- `8/8` proof artifact sets complete;
- `8/8` evals expose the top-level `collision_provenance` key;
- `44` total collision-provenance rows;
- `5` unique scenarios and all `3` duplicate scenario groups preserved by `slot_id`.

Those are execution-support facts only. No actor-match classifier has been run over the iteration
112 proof before this file. The bars below freeze how support and match labels will be computed.

## Research question

Using the frozen iteration-59 actor-match support rules, does the 8-slot support-core iteration-112
proof reach the minimum support floor for same-run comparison between:

1. the monitor's first-fire hazard object/path, reconstructed from each slot's released-union
   decision log; and
2. the first foreground HUGSIM collision provenance row in the same slot's `eval.json`;

relative to the iteration-108 timing-aware support null where only `2/13` slots were
`classifiable_foreground` against the preregistered floor of `4`?

This iteration may answer only support and descriptive match classification inside the registered
8-slot support-core proof. It does not claim the distribution of all HUGSIM failures.

## Frozen inputs

- Iteration 111 manifest:
  `experiments/iter111_hugsim_support_core_launch_manifest/proof-launch-manifest/support_core_launch_manifest.json`
- Iteration 112 execution report:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution/support_core_batch_execution_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot proof artifacts under the
iteration-112 proof root. It may not read live GPU state, raw box paths outside committed proof,
or uncommitted files.

## Frozen support rules

The per-slot support rules are the iteration-59 rules, reused without threshold changes:

- `no_monitor_fire`: no fired monitor row exists; actor match is not attempted.
- `no_collision_provenance`: no top-level list of collision-provenance rows exists; actor match
  is not attempted.
- `background_collision_only`: all collision provenance rows are background; actor match is not
  attempted.
- `post_collision_fire`: first monitor fire is after the first foreground collision provenance
  timestamp; actor match is not attempted.
- `monitor_argmin_not_unique`, `frame_bridge_failed`, `schema_unsupported`, or
  `argmin_reconstruction_failed`: actor match is not attempted.
- `classifiable_foreground`: first monitor fire is at or before first foreground collision,
  the monitor argmin is unique for the firing channel, and the frozen coordinate bridge yields a
  finite distance.

Frozen coordinate bridge and match thresholds are unchanged from iteration 59:

1. Reconstruct the first-fire monitor argmin object exactly as in iteration 59.
2. Convert the object's logged world `x,y` into monitor ego-local frame using `l2g_r_mat` and
   `l2g_t`.
3. Compare HUGSIM `(forward, lateral)` to `(monitor_local_y, monitor_local_x)`.
4. If foreground collision is later than first fire, propagate the monitor object by logged
   velocity over that lead time before transform.
5. Compute Euclidean center distance in HUGSIM `(forward, lateral)` plane.

Class labels for classifiable foreground rows:

- `actor_match`: distance `<= 3.0 m`;
- `actor_mismatch`: distance `> 6.0 m`;
- `actor_ambiguous`: distance in `(3.0 m, 6.0 m]`.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_INFRA_NULL`: iteration 112 is not
  `HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE`; the iteration-111 manifest and iteration-112
  slot ids differ; any registered slot proof is missing or malformed; scalar metric schema is
  broken; decision logs cannot be parsed; top-level `collision_provenance` key is absent from any
  registered slot; or the reused iteration-59 support logic fails on any slot.
- `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_SUPPORT_NULL`: infrastructure passes, but fewer than `4` slots
  are `classifiable_foreground`.
- `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE`: infrastructure passes and at least `4` slots
  are `classifiable_foreground`. Match/mismatch/ambiguous counts are descriptive outputs under
  this bounded support audit.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-actor-match/support_core_actor_match_report.json`;
- `proof-actor-match/support_core_actor_match.md`;
- `proof-actor-match/analyze_support_core_actor_match.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-112 proof.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim. A match count is not proof that Sentinel prevents collisions; a
mismatch count is not proof of a repair. This iteration may only claim whether the registered
iteration-112 support-core slots support same-run monitor-hazard versus HUGSIM collision-actor
comparison and report descriptive labels if support exists.
