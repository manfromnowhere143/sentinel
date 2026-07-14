# Iteration 120 - HUGSIM support-core selected fire-object backward lifecycle audit: HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE` (offline selected fire-object backward
lifecycle audit over the eight committed support-core rows).

This iteration used only the committed iteration-112 proof, the committed iteration-119 report, and
the frozen iteration-59 bridge logic. It launched no GPU work, reran no actor-match classifier,
changed no thresholds, changed no planner/action-control code, changed no HUGSIM metrics, and did
not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_selected_fire_object_lifecycle.py`](analyze_selected_fire_object_lifecycle.py)
- Tests:
  [`../../tests/test_iter120_selected_fire_object_lifecycle.py`](../../tests/test_iter120_selected_fire_object_lifecycle.py)
- Analyzer command:
  [`proof-selected/analyze_selected_fire_object_lifecycle.command.txt`](proof-selected/analyze_selected_fire_object_lifecycle.command.txt)
- JSON report:
  [`proof-selected/selected_fire_object_lifecycle_report.json`](proof-selected/selected_fire_object_lifecycle_report.json)
- Markdown report:
  [`proof-selected/selected_fire_object_lifecycle.md`](proof-selected/selected_fire_object_lifecycle.md)

## Result

Infrastructure passed and all `8` rows received frozen selected-object lifecycle measurements and
one lifecycle label:

- row count: `8`;
- problem row count: `0`;
- selected lifecycle-label counts:
  - `selected_never_supported_before_collision`: `8`;
- selected support phase counts: none;
- selected supported before fire: `0/8`;
- selected supported at fire: `0/8`;
- selected supported after fire before collision: `0/8`;
- selected-object presence-frame count range: `3` to `30`;
- selected-object support-frame count range: `0` to `0`;
- selected-object closest pre-fire distance range: `9.814849860027191` to
  `26.576615026308698` m;
- selected-object distance at fire range: `14.472507961609738` to `36.09143899155716` m;
- selected-object closest before-collision distance range: `9.814849860027191` to
  `23.793069683037515` m;
- pre-fire selected-object-containing active-frame count range: `0` to `0`;
- pre-fire selected-object-containing borderline-frame count range: `0` to `9`;
- pre-fire selected-object-containing far-frame count range: `0` to `18`.

Per-row selected-object summary:

| slot | scenario | run | label | selected | rank | pre best | fire m | global best | support phases |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `scene-0411-hard-00` | 2 | `selected_never_supported_before_collision` | `12` | `2` | `26.576615026308698` | `23.793069683037515` | `23.793069683037515` | `{}` |
| 2 | `scene-0411-extreme-00` | 1 | `selected_never_supported_before_collision` | `2` | `3` | `12.192824650458231` | `24.59033959495813` | `12.192824650458231` | `{}` |
| 3 | `scene-0038-hard-00` | 1 | `selected_never_supported_before_collision` | `25` | `1` | `12.714470083636659` | `14.472507961609738` | `10.051852932919369` | `{}` |
| 4 | `scene-0038-extreme-00` | 1 | `selected_never_supported_before_collision` | `2` | `1` | `9.814849860027191` | `15.460122021736504` | `9.814849860027191` | `{}` |
| 5 | `scene-0038-extreme-00` | 2 | `selected_never_supported_before_collision` | `2` | `1` | `9.846701909939755` | `15.541003639773562` | `9.846701909939755` | `{}` |
| 6 | `scene-0383-extreme-00` | 2 | `selected_never_supported_before_collision` | `1` | `8` | `17.82467248647331` | `36.09143899155716` | `17.82467248647331` | `{}` |
| 7 | `scene-0411-hard-00` | 1 | `selected_never_supported_before_collision` | `12` | `1` | `22.74246925010588` | `23.180715225043926` | `22.74246925010588` | `{}` |
| 8 | `scene-0411-extreme-00` | 2 | `selected_never_supported_before_collision` | `17` | `1` | `21.056817761623456` | `24.812496764606966` | `21.056817761623456` | `{}` |

## Interpretation

Iteration 120 closes the selected fire-object backward lifecycle question opened by iteration 119.
Every selected first-fire object is visible in the committed decision log, but none enters the
frozen `6.0 m` actor-support band before fire, at fire, or after fire before the first foreground
collision. This holds for both selected-nearest and selected-not-nearest rows.

The result separates two object tracks. Earlier iterations found that close collision-actor support
can exist before collision, but iteration 118 showed those first-support objects are absent or
outside support by fire. Iteration 120 shows the selected first-fire objects are not a delayed
same-support continuation either: they never become actor-supported anywhere before the first
foreground collision. Pre-fire frames containing the selected objects can be frame-level
`borderline` under released CPA/TTC summaries, but the selected objects themselves remain outside
the frozen actor-support band.

This is descriptive only. It does not prove track failure, sensor failure, actor causality, monitor
causality, planner causality, repair feasibility, threshold value, or safety impact. The next
narrower audit should synthesize the support-core line into a two-track row taxonomy: first-support
object lifecycle plus selected-fire-object lifecycle plus first-fire replacement rank, without
rerunning raw reconstruction or launching GPU.

## Claim boundary

Descriptive support-core selected fire-object backward lifecycle audit of eight committed rows
only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness,
benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
