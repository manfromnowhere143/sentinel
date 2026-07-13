# Iteration 65 - matched pre-contact temporal alignment audit: TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE

Status: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE` (offline temporal/provenance alignment audit
over the two iteration-64 best pre-contact monitor-object matches).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59, iteration-61, and iteration-64 proof.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_temporal_alignment.py`](analyze_temporal_alignment.py)
- Tests: [`../../tests/test_iter65_temporal_alignment.py`](../../tests/test_iter65_temporal_alignment.py)
- Analyzer command: [`proof-alignment/analyze_temporal_alignment.command.txt`](proof-alignment/analyze_temporal_alignment.command.txt)
- JSON report: [`proof-alignment/temporal_alignment_report.json`](proof-alignment/temporal_alignment_report.json)
- Markdown report: [`proof-alignment/temporal_alignment.md`](proof-alignment/temporal_alignment.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- iteration-64 verdict: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`;
- exactly the two iteration-64 matched rows:
  - `ttc_extreme_short` / `scene-0038-extreme-00`;
  - `cpa_medium_b` / `scene-0166-medium-00`.

It then reconstructed the matched monitor object's released CPA/TTC metrics at the exact
iteration-64 matched decision timestamp.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `matched_object_subthreshold`: `2`;
- matched object IDs: `2`, `6`;
- matched objects equal first-fire objects: `1`;
- verdict: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`.

| audit id | scenario | matched object | decision ts | foreground ts | min CPA | CPA rank | TTC | TTC rank | first-fire channel | first-fire object |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `2` | `0.25` | `2.75` | `12.7240` | `2` | `3.5763` | `1` | `ttc_only` at `1.50 s` | `2` |
| `cpa_medium_b` | `scene-0166-medium-00` | `6` | `2.25` | `6.50` | `9.3179` | `2` | `null` | `null` | `cpa_only` at `0.25 s` | `1` |

## Interpretation

Iteration 64 showed that both formerly first-fire-unsupported rows have pre-contact
monitor-object geometry that can be bridged to HUGSIM foreground provenance. Iteration 65 shows
that those matched objects were not released-union hazards at the matched timestamps: both were
present but subthreshold.

For `ttc_extreme_short`, the matched object is also the first-fire object, but the first fire
arrives later (`1.50 s`) than the best geometry match (`0.25 s`). For `cpa_medium_b`, the
matched object is not the first-fire object; the first fire is a CPA-only trigger on `object_id=1`.

This narrows the mechanism question again: the remaining gap is not total object absence and not
an already-active matched hazard at the best bridge timestamp. The next credible line must
explain why the released hazard surface and/or executed plan leaves collision-relevant geometry
subthreshold, late, post-collision, no-fire, or background-only.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result only classifies two already
selected iteration-64 matched objects at their matched decision timestamps.
