# Iteration 116 - HUGSIM support-core collision-actor timeline audit: HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE` (offline timeline audit of the
eight committed support-core mismatch rows).

This iteration used only the committed iteration-112 proof, the committed iteration-115 report,
and the frozen iteration-59 bridge logic. It launched no GPU work, reran no actor-match classifier,
changed no thresholds, changed no planner/action-control code, changed no HUGSIM metrics, and did
not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_core_collision_actor_timeline.py`](analyze_support_core_collision_actor_timeline.py)
- Tests:
  [`../../tests/test_iter116_support_core_collision_actor_timeline.py`](../../tests/test_iter116_support_core_collision_actor_timeline.py)
- Analyzer command:
  [`proof-timeline/analyze_support_core_collision_actor_timeline.command.txt`](proof-timeline/analyze_support_core_collision_actor_timeline.command.txt)
- JSON report:
  [`proof-timeline/support_core_collision_actor_timeline_report.json`](proof-timeline/support_core_collision_actor_timeline_report.json)
- Markdown report:
  [`proof-timeline/support_core_collision_actor_timeline.md`](proof-timeline/support_core_collision_actor_timeline.md)

## Result

Infrastructure passed and all `8` rows received frozen first-support phase, best-distance phase,
support-frame counts, and distance summaries:

- row count: `8`;
- problem row count: `0`;
- rows with any support frame before collision: `7`;
- first-support phase counts:
  - `pre_fire`: `5`;
  - `post_fire_pre_collision`: `2`;
  - `never_before_collision`: `1`;
- best-distance phase counts:
  - `pre_fire`: `5`;
  - `post_fire_pre_collision`: `3`;
- support-frame count range: `0` to `8`;
- considered-frame count range: `11` to `30`;
- best nearest-object distance to the collision actor before collision: `1.5056697220919042` to
  `10.051852932919369` m;
- at-fire nearest-object distance range: `7.624207359121617` to `24.812496764606966` m.

Per-row timeline summary:

| slot | scenario | run | first support | support frames | best phase | best m | best id | frames |
|---:|---|---:|---|---:|---|---:|---|---:|
| 1 | `scene-0411-hard-00` | 2 | `pre_fire` | `1` | `pre_fire` | `2.889279073064421` | `2` | `22` |
| 2 | `scene-0411-extreme-00` | 1 | `pre_fire` | `1` | `pre_fire` | `4.259200249926439` | `4` | `20` |
| 3 | `scene-0038-hard-00` | 1 | `never_before_collision` | `0` | `post_fire_pre_collision` | `10.051852932919369` | `25` | `30` |
| 4 | `scene-0038-extreme-00` | 1 | `post_fire_pre_collision` | `2` | `post_fire_pre_collision` | `5.638200876604923` | `13` | `11` |
| 5 | `scene-0038-extreme-00` | 2 | `post_fire_pre_collision` | `1` | `post_fire_pre_collision` | `5.647095932359166` | `14` | `11` |
| 6 | `scene-0383-extreme-00` | 2 | `pre_fire` | `8` | `pre_fire` | `1.651081390885113` | `3` | `30` |
| 7 | `scene-0411-hard-00` | 1 | `pre_fire` | `2` | `pre_fire` | `1.5056697220919042` | `3` | `25` |
| 8 | `scene-0411-extreme-00` | 2 | `pre_fire` | `2` | `pre_fire` | `3.95802218200769` | `4` | `25` |

## Interpretation

Iteration 116 answers the timeline question exposed by iteration 115. At the first monitor-fire
frame, all eight rows remained outside the frozen `6.0 m` actor-support band, as iteration 115
already showed. Across the full committed decision timeline before the first foreground collision,
however, `7/8` rows have at least one logged monitor object within that frozen band.

The split is temporal. In `5/8` rows the first close collision-actor candidate appears before the
first fire; in `2/8` rows it appears only after first fire but before collision; and in `1/8` row
it never appears before collision. The closest before-collision distances are often much smaller
than the at-fire distances, so the next question is not whether a close candidate ever exists in
most rows. The next narrower audit should decompose why close-candidate frames and first-fire
frames do not coincide: persistence, selected-object identity, and released CPA/TTC surface state
around the first-support and first-fire windows.

This is descriptive only. It does not prove sensor failure, actor causality, monitor causality,
planner causality, repair feasibility, threshold value, or safety impact.

## Claim boundary

Descriptive collision-actor monitor-set timeline audit of eight committed support-core rows only;
no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim.
