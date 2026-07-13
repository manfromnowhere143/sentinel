# Iteration 61 - monitor object surface audit

Frozen before any iteration-61 analyzer edit, analyzer run, result, or claim. This is an
offline post-result audit over committed iteration-59 and iteration-60 proof only. It launches no
GPU work, reads no live box state, creates no new HUGSIM episodes, and does not retune Sentinel.

## Process disclosure

This audit is not blind. Iteration 59 is already published as `ACTOR_MATCH_AUDIT_COMPLETE`:
eight registered Sentinel-ON episodes completed, exactly three rows were
`classifiable_foreground`, and all three triggering monitor argmins were `actor_mismatch` under
the frozen iteration-59 bridge. Iteration 60 is already published as `BRIDGE_AMBIGUOUS_NULL`:
the same three rows were stress-tested under 48 fixed bridge variants; none became
`bridge_match_possible`, two remained robust mismatches, and `ttc_extreme_b` became
`bridge_ambiguous_possible` at `5.6649 m`.

Iteration 61 therefore cannot produce a surprise transfer or safety result. It asks a narrower
mechanism question: whether the HUGSIM foreground collision surface is near the triggering
monitor object, near some other object visible to the monitor at first fire, or near no
first-fire monitor object under the same bounded bridge family.

## Research question

For the three iteration-59 classifiable foreground rows, does any first-fire monitor object line
up with any HUGSIM foreground collision provenance row under the bounded bridge grid, and if so
is it the triggering argmin object or a non-triggering object?

This matters because iteration 60 showed that the triggering-object bridge can become ambiguous
for one row but never reaches a match. If a non-triggering first-fire object matches the HUGSIM
foreground collision surface, the failure looks like wrong-object or wrong-hazard selection. If
no first-fire monitor object matches, the failure looks deeper: missing actor support,
coordinate/contact ambiguity outside the bounded grid, or collision geometry not represented by
the first-fire monitor object set.

## Frozen inputs

Inputs are exactly:

- [`../iter59_hugsim_actor_match_audit/proof-actor-match/`](../iter59_hugsim_actor_match_audit/proof-actor-match/)
- [`../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`](../iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json)
- [`../iter60_actor_bridge_sensitivity/proof-bridge/bridge_sensitivity_report.json`](../iter60_actor_bridge_sensitivity/proof-bridge/bridge_sensitivity_report.json)

The analyzer must cross-check:

- iteration-59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-60 verdict is `BRIDGE_AMBIGUOUS_NULL`;
- both reports identify exactly the same three classifiable rows:
  - `ttc_extreme_short` / `scene-0038-extreme-00`;
  - `cpa_medium_b` / `scene-0166-medium-00`;
  - `ttc_extreme_b` / `scene-0383-extreme-00`.

The analyzer may analyze only those three rows.

## Frozen object and foreground surface

For each row, reconstruct the iteration-59 first-fire monitor row exactly as the iteration-59
analyzer did. The monitor object set is every object in that first-fire row's `objs` list. The
triggering object is the unique iteration-59 `monitor_object_id`; every other object in the set
is non-triggering.

The HUGSIM foreground surface is every `collision_provenance` row in the episode `eval.json`
where:

- `collision_type == "foreground"`;
- `timestamp` is numeric and `timestamp >= first_fire_ts`;
- `obs_box[:2]` are numeric.

No background rows, post-hoc object identities, fitted transforms, or unlogged actor labels may
be used.

## Frozen bridge family

For each monitor object and each foreground provenance row, evaluate the same fixed bridge family
used in iteration 60:

- temporal source: first-fire object position, propagated object position at the foreground
  provenance timestamp;
- axis order:
  - `(forward, lateral) = (monitor_local_y, monitor_local_x)`;
  - `(forward, lateral) = (monitor_local_x, monitor_local_y)`;
- sign flips: `forward_sign in {-1, +1}`, `lateral_sign in {-1, +1}`.

This yields `16` variants per object/provenance-row pair. The analyzer may compute the minimum
distance for the triggering object, for all non-triggering objects, and for all objects. It may
not fit translation, scale, rotation, yaw, scenario offsets, object offsets, per-row transforms,
or any outcome-conditioned transform outside this fixed grid.

Distance thresholds remain the iteration-59/60 thresholds:

- match: minimum distance `<= 3.0 m`;
- ambiguous: minimum distance in `(3.0 m, 6.0 m]`;
- no support: minimum distance `> 6.0 m`.

## Frozen row labels

Labels are assigned in this order:

1. `trigger_object_match`: the triggering object has any match.
2. `nontrigger_object_match`: no triggering-object match, but at least one non-triggering object
   has a match.
3. `trigger_object_ambiguous`: no object has a match, but the triggering object is ambiguous.
4. `nontrigger_object_ambiguous`: no object has a match and the triggering object is not
   ambiguous, but at least one non-triggering object is ambiguous.
5. `no_monitor_object_support`: every evaluated object/provenance-row/bridge variant is beyond
   `6.0 m`.

## Frozen verdict bars

- `OBJECT_SURFACE_INFRA_NULL`: required proof/report files are missing; report cross-checks fail;
  first-fire reconstruction fails; no foreground rows are eligible; the triggering object is not
  present in the first-fire object set; or any classifiable row cannot be evaluated.
- `OBJECT_SURFACE_TRIGGER_MATCH_COMPLETE`: at least one row is `trigger_object_match`.
- `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`: no row is `trigger_object_match`, but at least one
  row is `nontrigger_object_match`.
- `OBJECT_SURFACE_AMBIGUOUS_NULL`: no row has an object match, but at least one row is
  `trigger_object_ambiguous` or `nontrigger_object_ambiguous`.
- `OBJECT_SURFACE_NO_SUPPORT_COMPLETE`: all three rows are `no_monitor_object_support`.

## Forbidden claims

No transfer, safety, deployment, robustness, benchmark, HD-Score-invariance, actor-causality,
repair, retuning, or population mismatch-rate claim. A match or ambiguity here would be only a
bounded support fact over three already selected rows and committed proof; it would not identify
the true HUGSIM actor beyond the logged provenance geometry.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-object-surface/object_surface_report.json`;
- `proof-object-surface/object_surface.md`;
- `proof-object-surface/analyze_object_surface.command.txt`;
- `RESULT.md`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add analyzer/tests; run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`.
3. Run the analyzer once over committed iteration-59 and iteration-60 proof.
4. Publish `RESULT.md`, update README/NEXT_PHASE/CONTINUITY/HANDOFF, verify, commit, and push.
