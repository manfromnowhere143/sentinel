# Iteration 13 — formal-envelope baseline (RSS-style): pre-registration

Frozen before the arm runs. The runtime-monitor literature's strongest non-learned comparator is a
formal guaranteed-stopping envelope in the spirit of Responsibility-Sensitive Safety's longitudinal
minimum-distance rule. If Sentinel's introspective union cannot beat a physics rule that needs no
planner internals at all, that must be reported; if it can, the comparison states *why* plan-aware
introspection earns its complexity.

## The arm

`server_patch_rss.py` — identical inputs (the same multi-frame world-frame observed tracking) and
identical actuator (latched committed stop) as the union; the only changed variable is the decision
rule: brake when the observed gap to any tracked object falls inside

    d_safe = v_c·ρ + ½·a_acc·ρ² + (v_c + ρ·a_acc)²/(2·a_brake) + margin

(v_c = observed closing speed; ρ = 0.5 s, a_acc = 2 m/s², a_brake = 6 m/s², margin = 1 m,
contact radius 2 m). Scope disclosed in the patch header: longitudinal rule only, closing-speed
form — RSS-inspired, not a full RSS implementation.

## H13 (pre-registered predictions)

1. **Danger scenes:** the envelope catches both the frontal approach and the side crossing (both
   produce real closing speed) — collision outcomes comparable to the union's.
2. **Benign scene:** the envelope **over-brakes**. At ego speed ~8 m/s the safe distance is ~12 m,
   and the formal rule has no concept of the *plan* steering around the parked object — it sees
   only closing kinematics. Expected: clean-scene progress collapses toward the iteration-3
   over-braking arm (ego ≪ 32 m), so pooled safe-progress falls below both OFF and the union.
3. **Therefore:** the union > envelope on safe-progress, with the envelope ≈ union on raw safety —
   i.e. the introspective, plan-aware terms are what buy *selectivity*, not raw stopping power.

## Falsifier

If the envelope matches the union's selectivity on the benign scene (progress ≈ OFF) while
matching its danger-scene safety, the introspective monitor's added complexity is unjustified on
this corpus and that conclusion is published with the same weight.

## Protocol

RSS arm only (OFF and union already measured at n=20 unique episodes in the verification §4 run),
`--runs 20`, all three scenes, seed-paired against those arms. Metrics: per-scene score /
collision% / ego progress; pooled safe-progress; within-scene bootstrap CI for union − RSS.
