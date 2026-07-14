# Iteration 118 - HUGSIM support-core support-object lifecycle audit: HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE` (offline support-object lifecycle audit
over the eight committed support-core rows).

This iteration used only the committed iteration-112 proof, the committed iteration-117 report,
and the frozen iteration-59 bridge logic. It launched no GPU work, reran no actor-match classifier,
changed no thresholds, changed no planner/action-control code, changed no HUGSIM metrics, and did
not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_object_lifecycle.py`](analyze_support_core_object_lifecycle.py)
- Tests:
  [`../../tests/test_iter118_support_core_object_lifecycle.py`](../../tests/test_iter118_support_core_object_lifecycle.py)
- Analyzer command:
  [`proof-lifecycle/analyze_support_core_object_lifecycle.command.txt`](proof-lifecycle/analyze_support_core_object_lifecycle.command.txt)
- JSON report:
  [`proof-lifecycle/support_core_object_lifecycle_report.json`](proof-lifecycle/support_core_object_lifecycle_report.json)
- Markdown report:
  [`proof-lifecycle/support_core_object_lifecycle.md`](proof-lifecycle/support_core_object_lifecycle.md)

## Result

Infrastructure passed and all `8` rows received frozen lifecycle measurements and one lifecycle
label:

- row count: `8`;
- problem row count: `0`;
- lifecycle-label counts:
  - `pre_fire_object_absent_at_fire`: `4`;
  - `pre_fire_object_drifted_outside_support_at_fire`: `1`;
  - `post_fire_support_only_different_object_active_support`: `1`;
  - `post_fire_support_only_far_support`: `1`;
  - `never_supported_reference`: `1`;
- supported rows: `7`;
- first-support object present at first fire: `1`;
- first-support object supported at first fire: `0`;
- active-surface support on the same first-support object: `0`;
- active-surface support on a different object: `2`;
- first-support object presence-frame count range: `1` to `12`;
- first-support object support-frame count range: `1` to `3`;
- first-support object support-before-or-at-fire count range: `0` to `3`;
- first-fire distance for the lone present first-support object: `7.624207359121617` m.

Per-row lifecycle summary:

| slot | scenario | run | label | object | present at fire | support at fire | same active | diff active | last support <= fire |
|---:|---|---:|---|---:|---|---|---:|---:|---:|
| 1 | `scene-0411-hard-00` | 2 | `pre_fire_object_absent_at_fire` | `2` | `false` | `false` | `0` | `0` | `0.75` |
| 2 | `scene-0411-extreme-00` | 1 | `pre_fire_object_drifted_outside_support_at_fire` | `4` | `true` | `false` | `0` | `0` | `0.75` |
| 3 | `scene-0038-hard-00` | 1 | `never_supported_reference` | `none` | `none` | `none` | `0` | `0` | `none` |
| 4 | `scene-0038-extreme-00` | 1 | `post_fire_support_only_different_object_active_support` | `8` | `false` | `false` | `0` | `1` | `none` |
| 5 | `scene-0038-extreme-00` | 2 | `post_fire_support_only_far_support` | `14` | `false` | `false` | `0` | `0` | `none` |
| 6 | `scene-0383-extreme-00` | 2 | `pre_fire_object_absent_at_fire` | `2` | `false` | `false` | `0` | `0` | `0.75` |
| 7 | `scene-0411-hard-00` | 1 | `pre_fire_object_absent_at_fire` | `2` | `false` | `false` | `0` | `0` | `0.75` |
| 8 | `scene-0411-extreme-00` | 2 | `pre_fire_object_absent_at_fire` | `4` | `false` | `false` | `0` | `1` | `0.75` |

## Interpretation

Iteration 118 resolves the first-support-object lifecycle question opened by iteration 117. The
first-support object is never still supported at first fire (`0/7` supported rows). Among the five
pre-fire support rows, four first-support objects are absent from the first-fire object set, and
the only persisting object has already drifted outside the frozen `6.0 m` support band by first
fire (`7.624207359121617 m`).

The later active support cases do not rescue same-object continuity. There are `2` active-surface
support frames in the committed logs, but both are on different nearest support objects, not the
original first-support object. This turns the event-window split into a lifecycle split: early
actor-proximity support is short-lived or gone by fire, and later active support, when present, is
not same-object continuity.

This is descriptive only. It does not prove track failure, sensor failure, actor causality, monitor
causality, planner causality, repair feasibility, threshold value, or safety impact. The next
narrower audit should quantify the support-loss gap and first-fire replacement: time from last
same-object support to first fire, time from last same-object presence to first fire, and the
identity/distance/surface state of the first-fire replacement object.

## Claim boundary

Descriptive support-core support-object lifecycle audit of eight committed rows only; no repair,
actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
