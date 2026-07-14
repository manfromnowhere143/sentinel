# Iteration 119 - HUGSIM support-core support-loss and replacement audit: HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE` (offline support-loss and first-fire
replacement audit over the eight committed support-core rows).

This iteration used only the committed iteration-112 proof, the committed iteration-117 and
iteration-118 reports, and the frozen iteration-59 bridge logic. It launched no GPU work, reran no
actor-match classifier, changed no thresholds, changed no planner/action-control code, changed no
HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_loss_replacement.py`](analyze_support_core_loss_replacement.py)
- Tests:
  [`../../tests/test_iter119_support_core_loss_replacement.py`](../../tests/test_iter119_support_core_loss_replacement.py)
- Analyzer command:
  [`proof-replacement/analyze_support_core_loss_replacement.command.txt`](proof-replacement/analyze_support_core_loss_replacement.command.txt)
- JSON report:
  [`proof-replacement/support_core_loss_replacement_report.json`](proof-replacement/support_core_loss_replacement_report.json)
- Markdown report:
  [`proof-replacement/support_core_loss_replacement.md`](proof-replacement/support_core_loss_replacement.md)

## Result

Infrastructure passed and all `8` rows received frozen support-loss gaps, first-fire replacement
object measurements, selected-object rank, and one replacement label:

- row count: `8`;
- problem row count: `0`;
- replacement-label counts:
  - `pre_fire_lost_absent_selected_not_nearest`: `2`;
  - `pre_fire_lost_absent_selected_nearest`: `2`;
  - `pre_fire_drifted_selected_not_nearest`: `1`;
  - `post_fire_support_selected_nearest`: `2`;
  - `never_supported_reference_selected_nearest`: `1`;
- selected object is first-fire nearest: `5/8`;
- selected object is not first-fire nearest: `3/8`;
- first-fire nearest object is the first-support object: `1/8`;
- fire-minus-last-support gap range: `1.0` to `6.0` s;
- fire-minus-last-presence gap range: `0.0` to `4.75` s;
- first-fire nearest-object distance range: `7.624207359121617` to `24.812496764606966` m;
- selected-object distance range: `14.472507961609738` to `36.09143899155716` m;
- selected rank by collision-actor distance range: `1` to `8`.

Per-row replacement summary:

| slot | scenario | run | label | support object | last support gap | last presence gap | fire nearest | selected | rank |
|---:|---|---:|---|---:|---:|---:|---|---|---:|
| 1 | `scene-0411-hard-00` | 2 | `pre_fire_lost_absent_selected_not_nearest` | `2` | `4.25` | `1.25` | `10` / `12.724592460878268` | `12` / `23.793069683037515` | `2` |
| 2 | `scene-0411-extreme-00` | 1 | `pre_fire_drifted_selected_not_nearest` | `4` | `1.0` | `0.0` | `4` / `7.624207359121617` | `2` / `24.59033959495813` | `3` |
| 3 | `scene-0038-hard-00` | 1 | `never_supported_reference_selected_nearest` | `none` | `none` | `none` | `25` / `14.472507961609738` | `25` / `14.472507961609738` | `1` |
| 4 | `scene-0038-extreme-00` | 1 | `post_fire_support_selected_nearest` | `8` | `none` | `none` | `2` / `15.460122021736504` | `2` / `15.460122021736504` | `1` |
| 5 | `scene-0038-extreme-00` | 2 | `post_fire_support_selected_nearest` | `14` | `none` | `none` | `2` / `15.541003639773562` | `2` / `15.541003639773562` | `1` |
| 6 | `scene-0383-extreme-00` | 2 | `pre_fire_lost_absent_selected_not_nearest` | `2` | `6.0` | `4.75` | `18` / `23.221048739940226` | `1` / `36.09143899155716` | `8` |
| 7 | `scene-0411-hard-00` | 1 | `pre_fire_lost_absent_selected_nearest` | `2` | `5.0` | `2.25` | `12` / `23.180715225043926` | `12` / `23.180715225043926` | `1` |
| 8 | `scene-0411-extreme-00` | 2 | `pre_fire_lost_absent_selected_nearest` | `4` | `5.0` | `2.5` | `17` / `24.812496764606966` | `17` / `24.812496764606966` | `1` |

## Interpretation

Iteration 119 quantifies the support-loss and replacement structure opened by iteration 118. Where
the first-support object had same-object support before fire, that support ended `1.0-6.0 s`
before first fire. Same-object presence ended `0.0-4.75 s` before first fire; the `0.0 s` case is
the lone drift case where the original object remains present at fire but has moved outside the
frozen `6.0 m` support band.

The first-fire replacement remains outside support in every row. The selected object is nearest in
`5/8` first-fire object sets, but the selected distance is still `14.472507961609738` to
`36.09143899155716 m`. In the three selected-not-nearest rows, the nearest replacement is also
outside support (`7.624207359121617` to `23.221048739940226 m`). The fire-time issue is therefore
not just a selected-vs-nearest tie: even the nearest first-fire replacement is outside the frozen
support band.

This is descriptive only. It does not prove track failure, sensor failure, actor causality, monitor
causality, planner causality, repair feasibility, threshold value, or safety impact. The next
narrower audit should follow the first-fire selected object backward through the committed decision
log: whether it ever enters the frozen support band before fire, when it first appears, whether it
is surface-active before first fire, and whether selected-nearest rows differ from
selected-not-nearest rows.

## Claim boundary

Descriptive support-core support-loss and first-fire replacement audit of eight committed rows
only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness,
benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
