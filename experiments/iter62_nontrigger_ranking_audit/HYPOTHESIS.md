# Iteration 62 - non-trigger ranking audit

Frozen before any iteration-62 analyzer edit, analyzer run, result, or claim. This is an
offline post-result audit over committed iteration-59 and iteration-61 proof only. It launches no
GPU work, reads no live box state, creates no new HUGSIM episodes, and does not retune Sentinel.

## Process disclosure

This audit is not blind. Iteration 61 is already published as
`OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`. It found that among the three iteration-59
classifiable foreground rows, `ttc_extreme_b` / `scene-0383-extreme-00` had a non-triggering
first-fire monitor object (`object_id=16`) matching the HUGSIM foreground surface at `2.0686 m`,
while the triggering object (`object_id=1`) remained ambiguous at `5.6649 m`. The other two rows
had no first-fire monitor object support.

Iteration 62 therefore cannot produce a surprise actor-causality, repair, transfer, or safety
claim. It asks why the matched non-triggering object was not the first-fire provenance object.

## Research question

For the single iteration-61 `nontrigger_object_match` row, was the matched non-trigger object
already a threshold-crossing Sentinel hazard at first fire, or was it visible but subthreshold
under the frozen released-union TTC/CPA rule?

This distinguishes two mechanism readings:

- If the matched object crossed a frozen TTC or CPA threshold, the monitor surface contained the
  collision-near object but the provenance argmin selected a different object.
- If the matched object was subthreshold, the monitor surface did not regard the collision-near
  object as hazardous at first fire; the non-trigger match is then evidence of hazard-surface
  misalignment rather than just provenance tie-breaking.

## Frozen inputs

Inputs are exactly:

- [`../iter59_hugsim_actor_match_audit/proof-actor-match/`](../iter59_hugsim_actor_match_audit/proof-actor-match/)
- [`../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`](../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json)
- [`../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json`](../iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json)

The analyzer must cross-check:

- iteration-59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict is `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-61 has exactly one `nontrigger_object_match` row;
- that row is `ttc_extreme_b` / `scene-0383-extreme-00`;
- its `best_nontrigger_variant.object_id` is `16`.

The analyzer may analyze only that one row and object.

## Frozen reconstruction

Reconstruct the first-fire row exactly as the iteration-59 analyzer did:

- first fired decision row;
- `l2g_r_mat`, `l2g_t`, `params.dt`, `params.min_closing`, `traj`, and `objs`;
- per-object CPA by propagating each object over the logged plan horizon;
- per-object TTC by the same closing-speed calculation used by iteration 59.

The analyzer must report for every first-fire object:

- object id and score if present;
- minimum CPA and CPA rank;
- TTC, gap, closing, and TTC rank when closing is valid;
- whether the object crosses `cpa_margin = 1.5 m`;
- whether the object crosses `ttc_thresh = 2.5 s`;
- whether it is the triggering object;
- whether it is the matched non-trigger object.

The analyzer may not use later frames, fitted transforms, HUGSIM labels beyond the iteration-61
matched object id, or any threshold other than the frozen released-union thresholds plus the
borderline bands below.

## Frozen labels

For the matched non-trigger object (`object_id=16`):

- `matched_object_hazard_present`: `min_cpa < 1.5` or `ttc < 2.5` at first fire.
- `matched_object_borderline`: not hazard-present, but `min_cpa < 3.0` or `ttc < 5.0`.
- `matched_object_subthreshold`: neither hazard-present nor borderline.

Ranking facts are descriptive but frozen:

- CPA rank is one-based rank by ascending minimum CPA across all first-fire objects.
- TTC rank is one-based rank by ascending TTC among valid-closing objects only.
- Missing TTC because closing is invalid must be reported as `null`, not imputed.

## Frozen verdict bars

- `NONTRIGGER_RANKING_INFRA_NULL`: required proof/report files are missing; report cross-checks
  fail; first-fire reconstruction fails; the matched object is absent from the first-fire object
  set; or the matched object's CPA/TTC cannot be evaluated.
- `MATCHED_OBJECT_HAZARD_PRESENT_COMPLETE`: matched object label is
  `matched_object_hazard_present`.
- `MATCHED_OBJECT_BORDERLINE_NULL`: matched object label is `matched_object_borderline`.
- `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE`: matched object label is
  `matched_object_subthreshold`.

## Forbidden claims

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. A result here is only a one-row
selector-surface fact about an already selected non-trigger match.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-ranking/nontrigger_ranking_report.json`;
- `proof-ranking/nontrigger_ranking.md`;
- `proof-ranking/analyze_nontrigger_ranking.command.txt`;
- `RESULT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add analyzer/tests; run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-59 and iteration-61 proof.
4. Publish `RESULT.md`, update README/NEXT_PHASE/CONTINUITY/HANDOFF, verify, commit, and push.
