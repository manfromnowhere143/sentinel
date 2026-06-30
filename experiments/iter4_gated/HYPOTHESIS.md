# Iteration 4 — introspective gating: brake only on *active* threats (pre-registered before the run)

Iteration 3's verdict: the TTC monitor over-brakes because its trigger fires whenever the **ego closes
on any object** — including a stationary one the planner would safely pass. The fix is to make the
trigger ask a sharper question: *is an agent actively driving toward the ego (a threat the planner is
failing), or is this a passive obstacle the planner already handles?*

## The change (one term)

The iter-2/3 trigger used the **total** closing speed (ego approach + agent approach):
`closing = -((agent_vel − ego_vel) · r̂)`. The gated trigger uses **only the agent's own** approach:
`closing = -(agent_vel · r̂)`, and brakes only if that exceeds `SENTINEL_MIN_CLOSING` (the agent is
actively coming at us). Velocities come from the planner's *own* forecast displacement — still
label-free, still a frozen planner.

- A **stationary / passive** object (the clean scene) has `agent_vel ≈ 0` ⇒ agent-closing ≈ 0 ⇒ **no
  brake** ⇒ the ego drives normally, the planner handles the obstacle.
- A **frontal / side actor** driving at the ego has high agent-closing ⇒ **brake** ⇒ collision removed.

This delegates passive-obstacle handling to the planner (which the iter-1b data shows it does well on
the clean scene: 5.0, no collision) and reserves Sentinel for the adversarial active-threat collisions
the planner fails.

## Pre-registered success criterion (H4)

Run the iteration-3 deployment metric (3 scenes × 6 runs) on three arms — **OFF**, **TTC-old**
(`MIN_CLOSING=0`, the over-braking iter-2/3 trigger), **gated** (`MIN_CLOSING≈3 m/s`). H4 holds iff:

1. **Selectivity restored:** on the benign clean scene (stationary/0103) the gated arm's ego distance
   driven is within ~20% of OFF (≈ 32 m), i.e. it **stops over-braking** the passive object — vs
   TTC-old's ~5 m freeze.
2. **Danger safety kept:** on the danger scenes (frontal/side), the gated arm's collision rate is no
   worse than TTC-old's (it still brakes for active actors).

Reported as a 2-axis result (safety × progress) per scene; the headline number is benign-scene
progress restored **and** danger-scene collisions still removed. The bar set in iteration 3 — beat the
unmonitored planner's pooled safe-progress of **2.08** — is the stretch goal; the primary claim is
selectivity (benign untouched, danger protected), which is what the iter-3 correction said was missing.

## Falsifiers (stated up front)

- If the gated arm still freezes the clean scene (benign progress stays low), the agent-closing gate
  does not fix the over-braking — reported as another null.
- If gating out passive objects lets a collision through on a scene where stopping was actually needed,
  the delegation-to-planner assumption is wrong — reported.
- Single-scene-per-type, 6 runs, thresholds fixed before the run; no tuning on the reported scenes.
