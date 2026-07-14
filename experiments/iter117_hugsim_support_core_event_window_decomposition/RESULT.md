# Iteration 117 - HUGSIM support-core event-window decomposition: HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE` (offline event-window decomposition of the
eight committed support-core mismatch rows).

This iteration used only the committed iteration-112 proof, the committed iteration-115 and
iteration-116 reports, and the frozen iteration-59 bridge logic. It launched no GPU work, reran no
actor-match classifier, changed no thresholds, changed no planner/action-control code, changed no
HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_event_window.py`](analyze_support_core_event_window.py)
- Tests:
  [`../../tests/test_iter117_support_core_event_window.py`](../../tests/test_iter117_support_core_event_window.py)
- Analyzer command:
  [`proof-event-window/analyze_support_core_event_window.command.txt`](proof-event-window/analyze_support_core_event_window.command.txt)
- JSON report:
  [`proof-event-window/support_core_event_window_report.json`](proof-event-window/support_core_event_window_report.json)
- Markdown report:
  [`proof-event-window/support_core_event_window.md`](proof-event-window/support_core_event_window.md)

## Result

Infrastructure passed and all `8` rows received frozen event-window measurements,
support-frame surface counts, identity-persistence fields, and one row label:

- row count: `8`;
- problem row count: `0`;
- row-label counts:
  - `pre_fire_support_surface_far_only`: `5`;
  - `post_fire_support_only`: `2`;
  - `never_supported_before_collision`: `1`;
- first-support surface-state counts:
  - `far`: `7`;
- first-fire surface-state counts:
  - `active`: `8`;
- support-phase counts:
  - `pre_fire`: `13`;
  - `post_fire_pre_collision`: `4`;
- support-surface counts:
  - `far`: `15`;
  - `active`: `2`;
- first-support object present at first fire: `1/7` supported rows;
- first-support object same as first-fire selected object: `0/7` supported rows;
- first-support object same as first-fire nearest object: `1/7` supported rows;
- support-frame count range: `0` to `8`;
- fire-minus-first-support range: `-1.0` to `6.5` s;
- first-fire nearest-object distance range: `7.624207359121617` to `24.812496764606966` m.

Per-row event-window summary:

| slot | scenario | run | label | first support | support surface | fire surface | support at fire | same selected | same nearest |
|---:|---|---:|---|---|---|---|---|---|---|
| 1 | `scene-0411-hard-00` | 2 | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `false` | `false` | `false` |
| 2 | `scene-0411-extreme-00` | 1 | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `true` | `false` | `true` |
| 3 | `scene-0038-hard-00` | 1 | `never_supported_before_collision` | `never_before_collision` | `none` | `active` | `none` | `none` | `none` |
| 4 | `scene-0038-extreme-00` | 1 | `post_fire_support_only` | `post_fire_pre_collision` | `far` | `active` | `false` | `false` | `false` |
| 5 | `scene-0038-extreme-00` | 2 | `post_fire_support_only` | `post_fire_pre_collision` | `far` | `active` | `false` | `false` | `false` |
| 6 | `scene-0383-extreme-00` | 2 | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `false` | `false` | `false` |
| 7 | `scene-0411-hard-00` | 1 | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `false` | `false` | `false` |
| 8 | `scene-0411-extreme-00` | 2 | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `false` | `false` | `false` |

## Interpretation

Iteration 117 explains the event-window separation exposed by iteration 116. In all seven rows
with a close collision-actor candidate before collision, the first support frame is a released
surface `far` frame: no active CPA/TTC crossing and no registered borderline frame-level surface.
By contrast, the first-fire frame is `active` in all eight rows, but it remains outside the frozen
actor-support band from iteration 115.

The object-identity split is also sharp. The first-support object persists to first fire in only
`1/7` supported rows. It is never the first-fire selected object (`0/7`), and it is the first-fire
nearest object in only that one persisting row, where it is still outside support at
`7.624207359121617 m`. Most rows therefore do not look like a close collision-actor candidate that
stays in the first-fire object set and loses a simple final selection tie. They look like a
surface/window mismatch: actor-proximity support appears on surface-far frames, while the released
active fire occurs later on a different object set or after support has moved outside the frozen
band.

This is descriptive only. The per-frame CPA/TTC fields are released monitor surface summaries, not
per-object causal attributions. The next narrower audit should follow the first-support object
through its lifecycle from first support to first fire: last presence, last support, disappearance
or drift outside the support band, and whether any later active support frame is same-object or a
different post-fire object.

## Claim boundary

Descriptive support-core event-window decomposition of eight committed rows only; no repair,
actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
