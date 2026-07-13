# Iteration 64 - unsupported-row temporal surface audit: UNSUPPORTED_TEMPORAL_MATCH_COMPLETE

Status: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE` (offline temporal object-surface audit over the
two iteration-61 rows with no first-fire object support).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only committed iteration-59 and iteration-61 proof.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_unsupported_temporal.py`](analyze_unsupported_temporal.py)
- Tests: [`../../tests/test_iter64_unsupported_temporal.py`](../../tests/test_iter64_unsupported_temporal.py)
- Analyzer command: [`proof-unsupported-temporal/analyze_unsupported_temporal.command.txt`](proof-unsupported-temporal/analyze_unsupported_temporal.command.txt)
- JSON report: [`proof-unsupported-temporal/unsupported_temporal_report.json`](proof-unsupported-temporal/unsupported_temporal_report.json)
- Markdown report: [`proof-unsupported-temporal/unsupported_temporal.md`](proof-unsupported-temporal/unsupported_temporal.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-61 verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
- exactly two `no_monitor_object_support` rows:
  - `ttc_extreme_short` / `scene-0038-extreme-00`;
  - `cpa_medium_b` / `scene-0166-medium-00`.

It then expanded from first-fire objects to every pre-contact decision object, comparing each
object to eligible foreground provenance rows under the frozen 16-variant bridge grid.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `pre_contact_object_match`: `2`;
- total variants evaluated: `28016`;
- minimum distance: `0.4325280723170322 m`;
- verdict: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`.

| audit id | scenario | pre-contact frames | object rows | variants | best distance | best object | decision ts | foreground ts |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `10` | `40` | `5120` | `1.6718` | `2` | `0.25` | `2.75` |
| `cpa_medium_b` | `scene-0166-medium-00` | `25` | `159` | `22896` | `0.4325` | `6` | `2.25` | `6.50` |

## Interpretation

Iteration 61 found no first-fire monitor-object support for these two rows. Iteration 64 shows
that this is a first-fire-surface limitation, not a whole pre-contact object-surface absence:
both rows have at least one pre-contact monitor object that matches the HUGSIM foreground
surface under the frozen bridge grid.

The result does not say Sentinel should have fired on those objects and does not identify a true
HUGSIM actor. It says the needed monitor-visible geometry exists somewhere in the pre-contact
sequence, while the iteration-59 first-fire provenance did not land on it. The next mechanism
question is temporal/provenance alignment: whether those matched objects were hazardous under
the released-union rule at their matched decision times, and why the first-fire event selected a
different surface.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result only classifies two already
selected unsupported rows after expanding from first-fire objects to pre-contact monitor objects.
