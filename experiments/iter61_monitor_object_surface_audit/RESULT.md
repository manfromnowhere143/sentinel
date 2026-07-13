# Iteration 61 - monitor object surface audit: OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE

Status: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE` (offline object-surface audit over the three
iteration-59 classifiable foreground rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, and did
not retune Sentinel. It used only the committed iteration-59 proof/report and the committed
iteration-60 sensitivity report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_object_surface.py`](analyze_object_surface.py)
- Tests: [`../../tests/test_iter61_object_surface.py`](../../tests/test_iter61_object_surface.py)
- Analyzer command: [`proof-object-surface/analyze_object_surface.command.txt`](proof-object-surface/analyze_object_surface.command.txt)
- JSON report: [`proof-object-surface/object_surface_report.json`](proof-object-surface/object_surface_report.json)
- Markdown report: [`proof-object-surface/object_surface.md`](proof-object-surface/object_surface.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-60 verdict: `BRIDGE_AMBIGUOUS_NULL`;
- exactly the same three classifiable rows in both reports.

It then evaluated all first-fire monitor objects against all eligible HUGSIM foreground
provenance rows under the frozen bridge grid. Total evaluated variants: `2384`.

Summary:

- `classifiable_rows`: `3`;
- `evaluated_rows`: `3`;
- row label counts:
  - `no_monitor_object_support`: `2`;
  - `nontrigger_object_match`: `1`;
- minimum overall distance: `2.068628866595313 m`;
- verdict: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`.

| audit id | scenario | objects | foreground rows | trigger min | non-trigger min | row label |
|---|---|---:|---:|---:|---:|---|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `4` | `8` | `6.9272` | `11.4262` | `no_monitor_object_support` |
| `cpa_medium_b` | `scene-0166-medium-00` | `6` | `9` | `19.6983` | `8.0969` | `no_monitor_object_support` |
| `ttc_extreme_b` | `scene-0383-extreme-00` | `9` | `7` | `5.6649` | `2.0686` | `nontrigger_object_match` |

For `ttc_extreme_b`, the triggering monitor object remains only ambiguous (`object_id=1`,
`5.6649 m`). A non-triggering first-fire object (`object_id=16`) matches the HUGSIM foreground
surface at the first eligible foreground timestamp (`7.25 s`) with distance `2.0686 m` under
the `first_fire/yx/-1/+1` bridge variant.

## Interpretation

The iteration-60 ambiguity is now more specific. In one classifiable row, the HUGSIM foreground
collision surface is within the registered match threshold of a monitor-visible object at first
fire, but not the object that triggered Sentinel's first fire. That supports a bounded
wrong-object or wrong-hazard-surface diagnosis for that row.

The other two classifiable rows remain harder: neither the triggering object nor any
non-triggering first-fire object comes within `6.0 m` of the eligible HUGSIM foreground surface
under the frozen grid. They still require a different explanation, such as missing actor support,
unrepresented contact geometry, or coordinate/contact structure outside this bounded audit.

## Claim boundary

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. This result says only that among the three
already selected iteration-59 classifiable rows, one row has bounded non-trigger object support
and two rows have no first-fire monitor object support.
