# Iteration 13 — the formal envelope: maximum stopping power, minimum driving (H13 confirmed)

The pre-registered comparison ([HYPOTHESIS.md](HYPOTHESIS.md)): the union vs an RSS-style
guaranteed-stopping-distance envelope on the *same* observed kinematics and the *same* latched-stop
actuator — isolating one variable, the decision rule. Same 20 unique episodes per scene,
seed-paired against the verification pass's OFF and union arms.

## Result (n=20/scene; OFF and union from the committed v20 measurement)

| arm | stationary (clean) | frontal | side | pooled safe-progress |
|---|---|---|---|---|
| OFF | 4.51 / 10% / 31.9 m | 0.84 / 85% / 31.7 m | 0.52 / 100% / 21.3 m | 1.826 |
| union | 4.51 / 10% / 28.6 m | 2.36 / 90% / 21.7 m | 3.56 / 30% / 12.4 m | **2.224** |
| RSS envelope | 5.00 / **0%** / **8.2 m** | 4.31 / **30%** / **3.7 m** | 5.00 / **0%** / **3.6 m** | **0.879** |

**Union − RSS on safe-progress: +1.345, 95% CI [+0.944, +1.701]** (within-scene bootstrap) —
excludes zero decisively. Every pre-registered prediction held; the falsifier (envelope matches the
union's selectivity) did not fire.

## Reading it honestly — both directions

- **The envelope posts the best raw safety numbers of the entire campaign.** Side and clean at 0%,
  and frontal at 30% — a collision rate no selective monitor achieved. If the only metric is
  collision rate, a formal physics rule wins.
- **It wins by not driving.** Ego progress collapses to 3.6–8.2 m per episode (the planner's
  normal is 21–32 m): at ~8 m/s the guaranteed-stopping envelope is ~12 m, so the rule fires on
  essentially any object in the scene — including the parked car the plan safely steers around.
  On the deployment metric it is *worse than no monitor at all* (0.879 vs OFF's 1.826). This is
  the iteration-3 lesson, now measured at the baseline level: safety-only metrics reward paralysis.
- **What the comparison isolates:** stopping power is free — any envelope has it. *Selectivity* —
  knowing the plan clears the object, so the car keeps driving — is the hard part, and it is
  exactly what the union's plan-aware terms (plan-vs-tracked-path CPA, observed-closing TTC) buy.
  A formal envelope has no concept of the plan; introspection is the difference.

## Scope

The envelope is the longitudinal, closing-speed form (disclosed in the patch header) — a
full RSS implementation with lane-based decomposition would fire less on lateral-offset objects;
on a straight-lane corpus like this one the difference is second-order, but the label "RSS-style",
not "RSS", is deliberate. 2 public-mini scenes, one L4, same scope as the whole campaign.

## Reproduce

[`server_patch_rss.py`](server_patch_rss.py) (same tracking, same actuator as the union;
only the rule differs) · [`rss_run.sh`](rss_run.sh) · analysis
[`analyze_rss.py`](analyze_rss.py) on the committed logs. Evidence: [`proof/`](proof/).
