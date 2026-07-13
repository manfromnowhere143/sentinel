# Iteration 63 - temporal emergence audit

Frozen before any iteration-63 analyzer edit, analyzer run, result, or claim. This is an
offline post-result audit over committed iteration-59, iteration-61, and iteration-62 proof only.
It launches no GPU work, reads no live box state, creates no new HUGSIM episodes, and does not
retune Sentinel.

## Process disclosure

This audit is not blind. Iteration 61 is already published as
`OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`: in `ttc_extreme_b` / `scene-0383-extreme-00`, a
non-triggering first-fire object (`object_id=16`) matched the HUGSIM foreground surface at
`2.0686 m`, while the first-fire trigger object (`object_id=1`) remained ambiguous. Iteration 62
is already published as `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE`: at first fire, `object_id=16`
was visible but outside Sentinel's frozen first-fire hazard surface (`min_cpa=22.7648 m`, CPA
rank `9/9`, no valid TTC), while `object_id=1` was the TTC-only trigger.

Iteration 63 therefore cannot produce a surprise repair, safety, transfer, or actor-causality
claim. It asks whether `object_id=16` ever becomes a frozen Sentinel hazard before the first
HUGSIM foreground collision timestamp, or whether the object remains visible but subthreshold.

## Research question

For the iteration-61 matched non-trigger object (`object_id=16` in `ttc_extreme_b`), does the
object cross the released-union CPA/TTC hazard surface at any logged monitor frame before the
first eligible HUGSIM foreground collision timestamp?

This distinguishes:

- late emergence: the object was subthreshold at first fire but became hazardous before contact;
- visible-never-hazard: the object stayed visible yet never crossed the frozen rule before
  contact;
- tracking-support failure: the object cannot be followed through enough pre-contact frames to
  support either statement.

## Frozen inputs

Inputs are exactly:

- [`../iter59_hugsim_actor_match_audit/proof-actor-match/`](../iter59_hugsim_actor_match_audit/proof-actor-match/)
- [`../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`](../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json)
- [`../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json`](../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json)
- [`../iter62_nontrigger_ranking_audit/proof-ranking/nontrigger_ranking_report.json`](../iter62_nontrigger_ranking_audit/proof-ranking/nontrigger_ranking_report.json)

The analyzer must cross-check:

- iteration-59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict is `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-62 verdict is `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE`;
- target row is `ttc_extreme_b` / `scene-0383-extreme-00`;
- matched object id is `16`;
- triggering object id is `1`;
- iteration-62 matched-object label is `matched_object_subthreshold`.

The analyzer may analyze only that one row and object.

## Frozen temporal window

Use the target episode's committed ON decision log and `eval.json`.

The first eligible foreground collision timestamp is the earliest `collision_provenance` row
where:

- `collision_type == "foreground"`;
- `timestamp` is numeric;
- `obs_box[:2]` are numeric.

The pre-contact window is every decision frame with numeric `ts < first_foreground_ts`.
The contact timestamp frame, if a decision row exists at `ts == first_foreground_ts`, must be
reported separately as contact-time evidence and must not satisfy the pre-contact hazard bar.

## Frozen reconstruction

For each decision row in the pre-contact window:

- find object `id == 16` in that row's `objs`;
- reconstruct that object's CPA and TTC using the same per-row formula as iteration 59/62:
  - CPA: propagate the object over the logged plan horizon and take the minimum distance to the
    logged plan points in world coordinates;
  - TTC: use current ego translation, object world position, object velocity, gap, and closing
    speed with the logged `params.min_closing`;
- classify threshold crossings using the frozen released-union thresholds:
  - CPA cross if `min_cpa < 1.5 m`;
  - TTC cross if `ttc < 2.5 s`;
  - borderline if no cross but `min_cpa < 3.0 m` or `ttc < 5.0 s`.

For every pre-contact decision row, report:

- timestamp;
- object present/absent;
- `min_cpa`, CPA crossing, CPA borderline;
- `ttc`, TTC crossing, TTC borderline;
- score if present;
- whether the monitor fired and braked in that row.

The analyzer may not use later HUGSIM actor labels, post-contact monitor rows for primary
classification, fitted transforms, threshold changes, or any frame not in the committed proof.

## Frozen row labels

Assigned in this order:

1. `pre_contact_hazard_cross`: at least one pre-contact row with object `16` present crosses CPA
   or TTC.
2. `pre_contact_borderline_only`: no pre-contact threshold cross, but at least one pre-contact
   row with object `16` present is borderline.
3. `visible_never_hazard`: object `16` is present in at least two pre-contact rows and every
   present row is outside both hazard and borderline surfaces.
4. `insufficient_temporal_support`: object `16` is present in fewer than two pre-contact rows.

## Frozen verdict bars

- `TEMPORAL_EMERGENCE_INFRA_NULL`: required proof/report files are missing; report cross-checks
  fail; first foreground timestamp cannot be found; decision log cannot be parsed; or per-row
  CPA/TTC reconstruction fails for any row where object `16` is present.
- `TEMPORAL_HAZARD_EMERGED_COMPLETE`: row label is `pre_contact_hazard_cross`.
- `TEMPORAL_BORDERLINE_NULL`: row label is `pre_contact_borderline_only`.
- `TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE`: row label is `visible_never_hazard`.
- `TEMPORAL_SUPPORT_NULL`: row label is `insufficient_temporal_support`.

## Forbidden claims

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This audit can only classify the temporal
hazard-surface behavior of one already selected object in one committed episode.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-temporal/temporal_emergence_report.json`;
- `proof-temporal/temporal_emergence.md`;
- `proof-temporal/analyze_temporal_emergence.command.txt`;
- `RESULT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add analyzer/tests; run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-59, iteration-61, and iteration-62 proof.
4. Publish `RESULT.md`, update README/NEXT_PHASE/CONTINUITY/HANDOFF, verify, commit, and push.
