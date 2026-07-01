# Iteration 10 — braking evasion into a clear gap: also refuted (the frontal ceiling is real)

Iteration 9 refuted steering-at-speed for the frontal head-on. Its null pointed to a refined evasion:
**shed speed *and* steer** (not steer at speed), steering into the **tracked-clear side** (not a fixed
offset). Iteration 10 implements exactly that — a braking evasion that decelerates hard while ramping a
moderate lateral offset toward whichever side the tracking shows is more open. **It is refuted too, at
essentially the same point as iteration 9: worse than simply stopping.**

## Result (OFF vs union[stop] vs brakevade, same run, 3 scenes × 6 runs)

| scene | OFF | union (committed stop) | brakevade (brake + steer to clear side) |
|---|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% / 32.4 m | 5.00 / 0% / 32.3 m | 5.00 / 0% / 32.3 m |
| frontal/0103 | 0.91 / 83% / 34.6 m | **2.53 / 83%** / 20.8 m | **1.67 / 100%** / 17.6 m |
| side/0103 | 0.64 / 100% | 5.00 / 0% | (stop-routed, as union) |

Actions logged: **10 `brakevade` on frontal, `stop` on side, negligible on clean** — the threat-aware
routing works and selectivity holds (clean 32.3 m = union). The regression is entirely the frontal
evasive *trajectory*.

## The converged finding — the committed stop is the frontal ceiling

Two independent evasion designs now land at the same place versus the stop-based union:

| frontal | union (stop) | iter 9 (steer at speed) | iter 10 (brake + steer to clear gap) |
|---|---|---|---|
| score | **2.53** | 1.66 | 1.67 |
| collision % | **83** | 100 | 100 |

Adding lateral steering to the head-on — whether at speed or while braking — makes it **worse**: more
collisions and higher impact than committing to a straight stop. The reasons hold across both:

- The actor is on an aggressive converging course; a few metres of lateral offset over ~1–1.5 s does
  not leave its swept path before contact, in either design.
- Splitting control effort between braking and steering (nuPlan kinematic-bicycle + LQR) realizes
  *less* deceleration than a pure stop, so the ego strikes harder — exactly what the scores show
  (1.67 < 2.53).
- The committed stop maximally removes the ego's own contribution to the closing speed; any steering
  trades that away for a dodge that does not complete in time.

**Conclusion:** for the frontal head-on in this closed-loop sim, evasive steering does not raise the
ceiling — mitigation via a committed stop is the best available frontal response, and the
iteration-8 **union remains the definitive best configuration of the campaign** (selective,
net-positive, side-solved, frontal mitigated). Frontal head-on *prevention* is now refuted for the two
obvious evasion families and stands as a genuinely hard open problem — likely needing something outside
a single-shot maneuver (e.g. much earlier detection so a *gentle, fully-completed* lane change is
possible, or acting before the ego is committed into the actor's path at all).

## Honesty

Same-run OFF/union baselines identical to iterations 8–9, so the frontal regression (2.53 → 1.67,
83 → 100%) is a clean within-run signal. brakevade side was stop-routed (CPA term) and matches union;
its run completed after this snapshot. 6 runs/scene, 2 public-mini scenes, one L4. This is a **reported
null**, filed with the same weight as the wins.

## Reproduce

`iter10_run.sh` (arms OFF / union / brakevade via `SENTINEL_EVADE` + `SENTINEL_EVADE_DECEL`) +
`server_patch_brakevade.py` (threat-aware: CPA→stop, closing-TTC→brake-and-steer into the clear side).
Full table: [`proof/i10_results.txt`](proof/i10_results.txt).
