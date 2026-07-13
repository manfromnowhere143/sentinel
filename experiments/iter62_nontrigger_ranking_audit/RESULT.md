# Iteration 62 - non-trigger ranking audit: MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE

Status: `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE` (offline one-row ranking audit over the
iteration-61 non-trigger object match).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only the committed iteration-59 proof/report and the committed
iteration-61 object-surface report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_nontrigger_ranking.py`](analyze_nontrigger_ranking.py)
- Tests: [`../../tests/test_iter62_nontrigger_ranking.py`](../../tests/test_iter62_nontrigger_ranking.py)
- Analyzer command: [`proof-ranking/analyze_nontrigger_ranking.command.txt`](proof-ranking/analyze_nontrigger_ranking.command.txt)
- JSON report: [`proof-ranking/nontrigger_ranking_report.json`](proof-ranking/nontrigger_ranking_report.json)
- Markdown report: [`proof-ranking/nontrigger_ranking.md`](proof-ranking/nontrigger_ranking.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- exactly one `nontrigger_object_match` row;
- target row: `ttc_extreme_b` / `scene-0383-extreme-00`;
- matched non-trigger object: `object_id=16`.

It then reconstructed all first-fire object CPA/TTC values for that row.

Matched non-trigger object:

- `object_id`: `16`;
- score: `0.7100042700767517`;
- `min_cpa`: `22.764754524017974 m`;
- `cpa_rank`: `9` of `9`;
- `ttc`: `null` because valid closing was absent;
- `ttc_rank`: `null`;
- `cpa_cross`: `false`;
- `ttc_cross`: `false`;
- label: `matched_object_subthreshold`.

Trigger object:

- `object_id`: `1`;
- first-fire channel: `ttc_only`;
- `ttc`: `2.130333589260053 s`;
- `ttc_rank`: `1`;
- `min_cpa`: `15.119705268273568 m`;
- `cpa_rank`: `3`.

The verdict is `MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE`.

## Interpretation

Iteration 61 showed that a non-triggering first-fire object is geometrically close to the HUGSIM
foreground surface under the bounded bridge grid. Iteration 62 shows that this object was not a
near-threshold Sentinel hazard at first fire. It was visible, but it ranked last by CPA and had
no valid TTC crossing; the first fire was instead a TTC-only trigger on `object_id=1`.

So the `ttc_extreme_b` mechanism is not just "the monitor picked the wrong argmin among active
hazards." The collision-near object was outside the frozen first-fire hazard surface. That
points to a sharper surface-alignment problem: HUGSIM foreground collision geometry can be near a
visible object that the released-union rule does not regard as hazardous at first fire.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This is only a one-row selector-surface
fact about an already selected non-trigger match.
