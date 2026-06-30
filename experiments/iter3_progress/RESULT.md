# Iteration 3 — the deployment metric exposes over-braking, and corrects an earlier overclaim

Iteration 2 showed a Sentinel-monitored frozen planner cuts collisions on the NeuroNCAP safety score.
The ablation (`../iter2_monitor/ABLATION.md`) flagged that a collision-only corpus can't tell a
selective monitor from a trivial always-brake, and named the missing experiment: a **progress-aware**
evaluation. This is that experiment. It produced a result we did not want but must report — and it
forces a correction to an earlier claim.

## What we measured

Three arms — **OFF** (no monitor), **always-brake**, **Sentinel-TTC** — each on the clean scene
(stationary/0103, where progress matters) and the two danger scenes (frontal/0103, side/0103), 6 runs
each, **18 episodes per arm**. Beyond the NCAP safety score we measured **progress = ego distance
actually driven** (from `ego_poses.json`), normalized to the OFF arm's normal-driving distance per
scene. A deployable monitor must keep the car safe **and** let it drive; freezing the car is not a
safety success. **safe-progress = safety score × progress.**

## Result (pooled over the three scenes)

| arm | NCAP safety ↑ | progress ↑ | collision % ↓ | **safe-progress ↑** |
|---|---:|---:|---:|---:|
| OFF (no monitor) | 2.18 | **0.91** | 61 | **2.08** |
| always-brake | 4.62 | 0.11 | 17 | 0.49 |
| Sentinel-TTC | 4.42 | 0.13 | 25 | 0.58 |

Clean scene (stationary/0103), ego distance driven: **OFF 32.4 m · always-brake 2.1 m · TTC 4.9 m**.

## The honest findings

1. **The TTC monitor over-brakes. It is not selective.** On the benign stationary scene — which the
   unmonitored planner drives through safely (32.4 m, score 5.0) — **TTC freezes the car to 4.9 m**,
   essentially the same as always-brake (2.1 m). The trigger is pure geometry (time-to-collision with
   any detected object), so it fires whenever the ego *closes on any object*, including a stationary
   one the planner would safely pass. It cannot distinguish a safe close pass from an imminent crash.

2. **On the deployment metric, the unmonitored planner wins.** safe-progress: **OFF 2.08 > TTC 0.58 >
   always-brake 0.49.** The monitors buy collision reduction by trading away ~85% of the car's
   progress. TTC is only marginally better than always-brake (0.58 vs 0.49) — i.e. **the deployment
   metric does *not* establish that the monitor is meaningfully more selective than slamming the
   brakes.**

3. **The iteration-2 safety win still stands — but its framing was wrong.** It remains true and
   pre-registered that the monitored frozen planner beats the *unmonitored* one **on the NeuroNCAP
   safety score** (collisions down, CI excludes 0). What is *not* true is the selectivity gloss I
   wrote into the iter-2 docs.

## Correction (stated plainly, because integrity is the whole point)

The iteration-2 `RESULT.md` and `ABLATION.md` claimed the monitor "fired on 0/10 clean-scene runs" and
left the clean scene "unharmed / selectively idle." **That was an unverified inference, and it is
wrong.** The clean scene held on the *safety score* (the monitor caused no new collisions there), but
the monitor was **not** idle — it over-braked the clean scene, freezing a car that would have driven
through safely. The progress measurement here is the direct evidence. Those docs have been corrected to
say: *safety-score do-no-harm held (no induced collisions), but the monitor over-brakes benign scenes —
it is not selective.* We caught this ourselves, with our own next experiment; we are flagging it rather
than letting it stand.

## Why this is progress, not failure

This is the result that tells us what the actual hard problem is. A geometric time-to-collision brake
is a blunt instrument: near object ⇒ brake. The thing that separates a *safe close pass* from an
*imminent crash* is not geometry — it is **whether the planner itself is failing.** That is exactly the
introspective signal [PerceptionProof](https://github.com/manfromnowhere143/perceptionproof) and our own
G1 gate validated (the planner's own forecast/uncertainty predicts its collisions at AUROC ~0.8–0.83).
The next iteration must **gate the brake on the planner's own distress** — brake only when the
introspective failure signal fires *and* geometry says imminent — so the monitor stays out of the way
when the planner is confidently handling a nearby object, and intervenes only when the planner is
actually about to crash. The deployment metric defined here (safe-progress) is the bar that change must
clear: beat OFF's 2.08, not just always-brake's 0.49.

## Reproduce

`iter3_run.sh` (arms OFF / always / ttc × 3 scenes × 6 runs, output dirs tagged `i3-<arm>`) →
`analyze.py` computes progress from `ego_poses.json` and merges the NCAP scores. Full per-run table:
[`proof/i3_results.txt`](proof/i3_results.txt).
