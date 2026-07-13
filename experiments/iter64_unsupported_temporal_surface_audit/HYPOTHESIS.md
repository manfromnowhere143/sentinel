# Iteration 64 - unsupported-row temporal surface audit

Frozen before any iteration-64 analyzer edit, analyzer run, result, or claim. This is an
offline post-result audit over committed iteration-59 and iteration-61 proof only. It launches no
GPU work, reads no live box state, creates no new HUGSIM episodes, and does not retune Sentinel.

## Process disclosure

This audit is not blind. Iteration 61 is already published as
`OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`. In the three iteration-59 classifiable foreground
rows, one row (`ttc_extreme_b`) had a non-triggering first-fire object match, while two rows had
`no_monitor_object_support` at first fire:

- `ttc_extreme_short` / `scene-0038-extreme-00`;
- `cpa_medium_b` / `scene-0166-medium-00`.

Iteration 64 therefore cannot produce a surprise transfer, repair, actor-causality, or safety
claim. It asks whether those two unsupported rows remain unsupported when the monitor-object
surface is expanded from the first-fire frame to all pre-contact monitor frames.

## Research question

For the two iteration-61 rows with no first-fire monitor object support, does any pre-contact
monitor object in any logged decision frame align with any eligible HUGSIM foreground collision
provenance row under the same bounded bridge grid?

This distinguishes:

- first-fire support miss only: no object matched at first fire, but a later pre-contact monitor
  object does align with the HUGSIM foreground surface;
- temporal no-support: no pre-contact monitor object aligns with the HUGSIM foreground surface;
- temporal ambiguity: no match, but at least one pre-contact object/provenance pair falls into
  the ambiguous band.

## Frozen inputs

Inputs are exactly:

- [`../iter59_hugsim_actor_match_audit/proof-actor-match/`](../iter59_hugsim_actor_match_audit/proof-actor-match/)
- [`../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`](../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json)
- [`../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json`](../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json)

The analyzer must cross-check:

- iteration-59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict is `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-61 has exactly two `no_monitor_object_support` rows;
- those rows are exactly:
  - `ttc_extreme_short` / `scene-0038-extreme-00`;
  - `cpa_medium_b` / `scene-0166-medium-00`.

The analyzer may analyze only those two rows.

## Frozen temporal/object surface

For each target row:

1. Load the committed target episode `eval.json` and `sentinel_iter48_decisions.jsonl`.
2. Find the first eligible foreground collision timestamp as the earliest
   `collision_provenance` row with `collision_type == "foreground"`, numeric `timestamp`, and
   numeric `obs_box[:2]`.
3. Use only decision rows with numeric `ts < first_foreground_ts`.
4. For every object in every pre-contact decision row, compare that object to every eligible
   foreground provenance row where `foreground.timestamp >= decision.ts`.
5. Evaluate the same bounded bridge grid used in iterations 60 and 61:
   - temporal source: frame-time object position, object position propagated to the foreground
     provenance timestamp;
   - axis order:
     - `(forward, lateral) = (monitor_local_y, monitor_local_x)`;
     - `(forward, lateral) = (monitor_local_x, monitor_local_y)`;
   - sign flips: `forward_sign in {-1, +1}`, `lateral_sign in {-1, +1}`.

This yields `16` variants per decision-object/foreground-row pair. The analyzer may report the
best variant per row and descriptive best variants by trigger/non-trigger role if the frame is
the first-fire frame, but the primary row label is over all pre-contact objects.

No post-contact frames, background rows, unlogged actor identities, fitted transforms, threshold
changes, object-specific offsets, per-row transforms, or HUGSIM labels outside committed
provenance may be used.

## Frozen thresholds and row labels

Distance thresholds remain:

- match: minimum distance `<= 3.0 m`;
- ambiguous: minimum distance in `(3.0 m, 6.0 m]`;
- no support: minimum distance `> 6.0 m`.

For each target row, labels are assigned in this order:

1. `pre_contact_object_match`: at least one pre-contact object/provenance/bridge variant matches.
2. `pre_contact_object_ambiguous`: no match, but at least one pre-contact
   object/provenance/bridge variant is ambiguous.
3. `temporal_no_object_support`: every evaluated pre-contact variant is beyond `6.0 m`.
4. `insufficient_temporal_surface`: fewer than two pre-contact object rows or no eligible
   foreground rows are evaluable.

## Frozen verdict bars

- `UNSUPPORTED_TEMPORAL_INFRA_NULL`: required proof/report files are missing; report
  cross-checks fail; first foreground timestamp cannot be found for either target row; decision
  log parsing fails; or any target row cannot be evaluated.
- `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`: at least one target row is
  `pre_contact_object_match`.
- `UNSUPPORTED_TEMPORAL_AMBIGUOUS_NULL`: no target row matches, but at least one target row is
  `pre_contact_object_ambiguous`.
- `UNSUPPORTED_TEMPORAL_NO_SUPPORT_COMPLETE`: both target rows are `temporal_no_object_support`.
- `UNSUPPORTED_TEMPORAL_SUPPORT_NULL`: no match or ambiguity, but at least one row is
  `insufficient_temporal_surface`.

## Forbidden claims

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This audit can only classify whether two
already selected rows remain unsupported after expanding from first-fire objects to pre-contact
monitor objects.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-unsupported-temporal/unsupported_temporal_report.json`;
- `proof-unsupported-temporal/unsupported_temporal.md`;
- `proof-unsupported-temporal/analyze_unsupported_temporal.command.txt`;
- `RESULT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add analyzer/tests; run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-59 and iteration-61 proof.
4. Publish `RESULT.md`, update README/NEXT_PHASE/CONTINUITY/HANDOFF, verify, commit, and push.
