# Iteration 59 - HUGSIM actor-match support audit: ACTOR_MATCH_AUDIT_COMPLETE

Status: `ACTOR_MATCH_AUDIT_COMPLETE` (bounded eight-episode ON-only actor-match support audit).

This iteration ran exactly the pre-registered eight Sentinel-ON HUGSIM episodes with the
released-union monitor patch and the byte-bound HUGSIM collision-provenance patch. It did not run
an OFF arm, did not retune Sentinel, did not expand the HUGSIM transfer benchmark, and did not
claim safety, transfer, deployment, HD-Score invariance, or repair.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Launcher: [`run_actor_match_audit.sh`](run_actor_match_audit.sh)
- Analyzer: [`analyze_actor_match.py`](analyze_actor_match.py)
- Tests: [`../../tests/test_iter59_actor_match.py`](../../tests/test_iter59_actor_match.py)
- Raw proof: [`proof-actor-match/`](proof-actor-match/)
- Analyzer command: [`proof-actor-match/analyze_actor_match.command.txt`](proof-actor-match/analyze_actor_match.command.txt)
- JSON report: [`proof-actor-match/actor_match_report.json`](proof-actor-match/actor_match_report.json)
- Markdown report: [`proof-actor-match/actor_match.md`](proof-actor-match/actor_match.md)

## Result

The analyzer returned:

- `completed_rows`: `8`;
- `classifiable_foreground`: `3`;
- support counts:
  - `classifiable_foreground`: `3`;
  - `no_monitor_fire`: `2`;
  - `post_collision_fire`: `2`;
  - `background_collision_only`: `1`;
- bridge counts among the three classifiable foreground rows:
  - `actor_mismatch`: `3`;
- verdict: `ACTOR_MATCH_AUDIT_COMPLETE`.

All eight scheduled episodes completed on the first attempt and all had intact scalar metric
schema, scalar-only `details` rows, top-level `collision_provenance`, and ON decision logs.

| audit id | scenario | support label | bridge label | distance |
|---|---|---|---|---:|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `classifiable_foreground` | `actor_mismatch` | `15.4330` |
| `mixed_extreme` | `scene-0062-extreme-00` | `no_monitor_fire` | - | - |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `post_collision_fire` | - | - |
| `nofire_hard_control` | `scene-0041-hard-00` | `no_monitor_fire` | - | - |
| `cpa_medium_a` | `scene-0071-medium-00` | `background_collision_only` | - | - |
| `ttc_medium_a` | `scene-0071-medium-01` | `post_collision_fire` | - | - |
| `cpa_medium_b` | `scene-0166-medium-00` | `classifiable_foreground` | `actor_mismatch` | `21.9863` |
| `ttc_extreme_b` | `scene-0383-extreme-00` | `classifiable_foreground` | `actor_mismatch` | `37.0380` |

## Interpretation

The registered support bar was met: at least three newly run episodes supported same-run
monitor-hazard versus HUGSIM foreground-collision comparison under the frozen coordinate bridge.
The descriptive result inside that bounded support set is stark: all three classifiable rows are
`actor_mismatch`, with distances far beyond the frozen `6.0 m` mismatch threshold.

The other five rows are also mechanism-informative but not actor-match rows: two did not fire the
monitor before collision, two first fired after the first foreground collision provenance row, and
one emitted only background collision provenance. This is consistent with the prior HUGSIM failure
taxonomy: the transfer failure is not one threshold branch, and a pure brake-earlier repair story
is insufficient.

## Claim boundary

This audit does not prove a population-wide HUGSIM actor-mismatch rate. It does not prove a
repair, does not downgrade the NeuroNCAP result, and does not claim safety, transfer,
deployment, robustness, HD-Score invariance, real-world behavior, or retuning. The only positive
claim is that the registered eight-episode audit produced enough support to classify three
same-run foreground actor-match rows, and all three were mismatches by the frozen bridge.
