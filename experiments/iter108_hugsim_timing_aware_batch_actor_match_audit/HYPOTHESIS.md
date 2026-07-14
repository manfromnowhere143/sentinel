# Iteration 108 - HUGSIM timing-aware batch actor-match support audit

Frozen after iteration 107 was published, but before any iteration-108 analyzer, actor-match
classification, proof artifact, result, handoff update, or claim. This is an offline analyzer
over the committed iteration-107 timing-aware execution proof only. It launches no GPU work and
changes no code under test.

## Process disclosure

This is not blind. Iteration 107 has already published the execution proof:

- `13/13` registered timing-aware slots completed;
- `0` retries;
- `13/13` proof artifact sets complete;
- `13/13` evals expose the top-level `collision_provenance` key;
- `252` total collision-provenance rows;
- `11` unique scenarios and both duplicate scenario groups preserved by `slot_id`.

Those are execution-support facts only. No actor-match classifier has been run over the iteration
107 proof before this file. The bars below freeze how support and match labels will be computed.

## Research question

Using the frozen iteration-59 actor-match support rules, does the timing-aware 13-slot
iteration-107 proof improve support for same-run comparison between:

1. the monitor's first-fire hazard object/path, reconstructed from each slot's released-union
   decision log; and
2. the first foreground HUGSIM collision provenance row in the same slot's `eval.json`;

relative to the iteration-104 support null where only `1/13` slots was
`classifiable_foreground` against the preregistered floor of `4`?

This iteration may answer only support and descriptive match classification inside the registered
13-slot timing-aware proof. It does not claim the distribution of all HUGSIM failures.

## Frozen inputs

- Iteration 106 manifest:
  `experiments/iter106_hugsim_timing_aware_launch_manifest/proof-launch-manifest/timing_aware_launch_manifest.json`
- Iteration 107 execution report:
  `experiments/iter107_hugsim_timing_aware_batch_execution/proof-execution/timing_aware_batch_execution_report.json`
- Iteration 107 proof root:
  `experiments/iter107_hugsim_timing_aware_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot proof artifacts under the
iteration-107 proof root. It may not read live GPU state, raw box paths outside committed proof,
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

- `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_INFRA_NULL`: iteration 107 is not
  `HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE`; the iteration-106 manifest and iteration-107
  slot ids differ; any registered slot proof is missing or malformed; scalar metric schema is
  broken; decision logs cannot be parsed; top-level `collision_provenance` key is absent from any
  registered slot; or the reused iteration-59 support logic fails on any slot.
- `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL`: infrastructure passes, but fewer than
  `4` slots are `classifiable_foreground`.
- `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_AUDIT_COMPLETE`: infrastructure passes and at least
  `4` slots are `classifiable_foreground`. Match/mismatch/ambiguous counts are descriptive
  outputs under this bounded support audit.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-actor-match/timing_aware_batch_actor_match_report.json`;
- `proof-actor-match/timing_aware_batch_actor_match.md`;
- `proof-actor-match/analyze_timing_aware_batch_actor_match.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-107 proof.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim. A match count is not proof that Sentinel prevents collisions; a
mismatch count is not proof of a repair. This iteration may only claim whether the registered
iteration-107 timing-aware slots support same-run monitor-hazard versus HUGSIM collision-actor
comparison and report descriptive labels if support exists.
