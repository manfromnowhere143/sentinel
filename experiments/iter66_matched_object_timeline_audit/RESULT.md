# Iteration 66 - matched-object hazard timeline audit: MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE

Status: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE` (offline target-object temporal surface audit
over the two iteration-65 matched pre-contact monitor objects).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59, iteration-61, iteration-64, and
iteration-65 proof.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_matched_object_timeline.py`](analyze_matched_object_timeline.py)
- Tests: [`../../tests/test_iter66_matched_object_timeline.py`](../../tests/test_iter66_matched_object_timeline.py)
- Analyzer command: [`proof-timeline/analyze_matched_object_timeline.command.txt`](proof-timeline/analyze_matched_object_timeline.command.txt)
- JSON report: [`proof-timeline/timeline_report.json`](proof-timeline/timeline_report.json)
- Markdown report: [`proof-timeline/timeline.md`](proof-timeline/timeline.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-64 verdict: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`;
- iteration-65 verdict: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`;
- exactly the two fixed iteration-65 targets:
  - `ttc_extreme_short` / `scene-0038-extreme-00` / `object_id=2`;
  - `cpa_medium_b` / `scene-0166-medium-00` / `object_id=6`.

It then reconstructed each target object's released CPA/TTC metrics across all pre-contact
decision frames (`ts < first_foreground_ts`).

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `target_object_ever_active_hazard`: `1`;
  - `target_object_visible_never_active`: `1`;
- total pre-contact frames: `35`;
- total target-present frames: `20`;
- total active hazard frames: `1`;
- total borderline frames: `2`;
- verdict: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`.

| audit id | scenario | object | label | present frames | hazard frames | borderline frames | first hazard | first borderline | min CPA | min TTC | first-fire |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `2` | `target_object_ever_active_hazard` | `7/10` | `1` | `2` | `1.50 s` | `0.25 s` | `12.2164 m` | `2.1893 s` | `ttc_only` on object `2` at `1.50 s` |
| `cpa_medium_b` | `scene-0166-medium-00` | `6` | `target_object_visible_never_active` | `13/25` | `0` | `0` | `null` | `null` | `7.9669 m` | `null` | `cpa_only` on object `1` at `0.25 s` |

## Interpretation

Iteration 66 splits the two formerly unsupported rows into different timing mechanisms.

For `ttc_extreme_short`, the matched object (`object_id=2`) is initially subthreshold at the
iteration-65 matched decision timestamp (`0.25 s`), but it is already TTC-borderline then,
remains TTC-borderline at `0.50 s`, and becomes an active TTC hazard exactly at first fire
(`1.50 s`). That row is a late-emerging target-object hazard, not a permanently unsupported
object.

For `cpa_medium_b`, the matched object (`object_id=6`) is visible in `13` pre-contact frames but
never becomes active or borderline before the first eligible foreground collision timestamp
(`6.25 s`). The first fire in that episode is a CPA-only trigger on a different object
(`object_id=1`) at `0.25 s`.

This narrows the mechanism map without authorizing a repair: one row is timing/late-emergence,
and one row remains visible-never-hazard under the frozen released surface.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result only classifies two fixed
target-object timelines selected by iteration 65.
