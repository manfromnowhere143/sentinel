# VAD — the union does not transfer blind, and the candidate collapse is a two-planner finding

Both pre-registered questions ([HYPOTHESIS.md](HYPOTHESIS.md)) answered on 20 unique episodes per
scene per arm, after four fork-level runtime fixes (image decode, empty aux, cold-start forecasts,
object-ID association — each committed pre-run with the caveat it introduces).

## H-VAD-1 — transfer: safety yes, selectivity no (pre-registered caveat confirmed)

| arm (n=20/scene) | stationary | frontal | side | pooled safe-progress |
|---|---|---|---|---|
| VAD OFF | 0.88 / **85%** / 12.0 m | 4.32 / **15%** / 49.4 m | 1.87 / **65%** / 20.5 m | 2.297 |
| VAD + union | 5.00 / **0%** / 2.4 m | 4.31 / 30% / 3.7 m | 5.00 / **0%** / 3.8 m | **0.750** |

Union − OFF on safe-progress: **−1.548, 95% CI [−2.057, −1.027]** — decisively negative.

Three findings inside that table, each worth stating precisely:

1. **VAD's failure profile is inverted relative to UniAD's.** Unmonitored VAD crashes the
   *stationary* scene 85% of the time (UniAD: 10%) and side 65% (UniAD: 100%), while frontal is
   its strength (15% at 49 m driven; UniAD: 85%). Failure signatures are planner-specific — which
   alone argues against transplanting a monitor configuration between planners unexamined.
2. **The union's protection transfers where VAD fails.** Stationary 85% → 0% and side 65% → 0% are
   genuine prevention on the scenes where VAD needed a guardian — on VAD, braking near the parked
   car is *correct*, not over-caution.
3. **Its selectivity does not transfer — and the mechanism is identified.** Ego progress collapses
   to 2.4–3.8 m everywhere (frontal degrades outright: 15% → 30% at a standstill in the actor's
   lane). The decision logs attribute the over-braking to the observed-closing **TTC term** (163
   first-fires vs CPA's 62, firing at 6–8 m gaps): on UniAD that term reads velocities from a
   *learned tracker's* stable IDs; on VAD it reads the geometric nearest-neighbor association
   added at the input layer (the fork exposes no IDs), whose frame-to-frame jitter manufactures
   closing speed. **The union's selectivity is a property of its tracking quality, not of the
   decision rule alone** — exactly the suspect the pre-run amendment named.

The honest deployment statement: a monitor validated on one planner is not a plug-in for another —
its input assumptions (track stability) and the target's failure profile must be re-validated.
Tuning a VAD-specific configuration (e.g. velocity smoothing or a CPA-weighted union) is future
work, deliberately not attempted post-hoc on this data.

## H-VAD-2 — native-mode diversity under threat: below the bar (two-planner collapse spectrum)

The frozen analysis (`../iter12_plan_selection/analyze_candidates.py`, thresholds pre-registered)
on the complete candidate log (1,659 frames; all three ego_fut_preds modes logged every frame):

| quantity | UniAD (iter 12) | VAD |
|---|---|---|
| divergence, benign frames (median / max endpoint spread) | 2.58 / 13.94 m | 3.45 / 22.08 m |
| dangerous frames (executed gap < 3.5 m) | 37 | 111 |
| mean gap in danger, per mode | 2.85 / 2.88 / 2.84 m | 2.54 / 3.11 / 2.80 m |
| **escape rate** (bar: > 30%) | **0%** | **21%** (23/111; OFF-only prefix: 24%) |

Per the frozen rule, no re-ranker is built. The two-planner reading: **command-indexed trajectory
alternatives lose most of their diversity precisely under threat** — totally on UniAD (4 cm mode
spread), partially on VAD (0.6 m spread, an escape in one of five dangerous frames — real
diversity, insufficient reliability). To the verified literature
([`../../docs/RELATED_WORK.md`](../../docs/RELATED_WORK.md)), these are the first
threat-conditioned diversity measurements on end-to-end planners' own candidate sets, and they
close the plan-selection line for command-indexed candidate mechanisms: the safe alternative the
re-ranker needs is mostly not there when it matters.

## Evidence

[`proof/`](proof/): run log, per-frame monitor decision logs (both arms), the full candidate log,
per-run trajectories/metrics/actors. Reproduce: `analyze_vad.py` (H-VAD-1),
`../iter12_plan_selection/analyze_candidates.py proof/sentinel_vad_cand.jsonl.gz` (H-VAD-2).
Scope: scene 0103's three scenarios, one L4, VAD-Base checkpoint; the fork-level fixes are
documented patches applied identically to both arms.
