# Iteration 134 disclosed smoke

Non-scheduled, disclosed up front, evidence committed. One placebo episode run before the
1,200-episode launch, on `frontal/0923` run 0. Output tag `i134-smoke`, so it writes to its own
root and cannot enter the scheduled run's artifacts. It is not part of any arm and contributes to
no measurement.

## Why it was run

The launch is roughly 30 to 55 GPU-hours. A placebo that silently never fires is
indistinguishable, from the analyzer's point of view, from a placebo that fires and does not help.

## What the first attempt found (the reason to smoke at all)

The first attempt produced `schedule_missing: 17` and **zero brake rows**. The reset row carried
`pair: ""`. Cause: `SENTINEL_PLACEBO_PAIR` is not in the `-e` forwarding list of
`neuro-ncap/scripts/_docker_compose_release.sh`, so it never reached the model container, the
schedule key became `/0`, and every lookup missed.

This is the iteration-2 finding resurfacing: monitor environment reaches the model container only
through explicit `-e` flags on the model block.

Had this shipped, all 400 placebo episodes would have scored as a never-braking arm. The placebo
would have matched OFF, and the analyzer would have returned `PLACEBO_HARM_OR_NULL` with a valid
CI. The iteration would have concluded that the union's risk semantics are load-bearing, at full
pre-registered weight, on the strength of a missing `-e` flag. The failure mode was a false
confirmation of the very headline this iteration exists to attack.

Fix: `-e SENTINEL_PLACEBO_PAIR -e SENTINEL_PLACEBO_SCHEDULE` appended to the MODEL block only
(line 58). The renderer block was not touched. Recorded in `../env_receipts.json` with the
script's SHA256. The added variables are inert for the `off` and `union` arms, which do not read
them; that claim is not assumed, it is tested mechanically by the G2 exact-reproduction gate over
400 committed per-episode scores.

## What the second attempt proved

| check | expected | observed |
|---|---|---|
| reset pair reaches container | `frontal/0923` | `frontal/0923` |
| donor (must exclude target pair and seed) | `frontal/0103/1` | `frontal/0103/1` |
| brake frame indices | `[7, 8, 9, 10, 11, 12, 13, 14]` | `[7, 8, 9, 10, 11, 12, 13, 14]` |
| schedule lookup misses | `0` | `0` |
| intervention errors | `0` | `0` |
| frame rows | episode length | `17` |

The placebo fires on exactly the donor's frame indices and nowhere else, on an episode whose own
world state is irrelevant to its firing. Episode outcome `ncap_score: 5.0, impact_speed: 0.0`,
recorded for completeness and carrying no weight: n=1, non-scheduled, no comparator.

Evidence: [`sentinel_i134_smoke.jsonl`](sentinel_i134_smoke.jsonl).
