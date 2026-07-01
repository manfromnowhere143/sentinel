# Next frontier — introspective plan selection on a frozen planner

This is the launch plan for the next research phase. It follows from a settled negative finding: across
iterations 9–11, three ways of *overriding* the planner with an invented maneuver (steer, brake+steer,
early-detect+evade) were refuted, and iteration 11 showed *why* — a swerve on a false alarm crashes, so
any invented out-of-distribution maneuver is unsafe under the false positives a real monitor produces.
The committed stop (the iteration-8 union) is the best *and* safe response, but it only *mitigates* the
head-on. Prevention needs a different mechanism.

## The thesis

Do not override the planner — **select among the planner's own candidates.** Modern end-to-end planners
(VAD, VADv2) emit a *multimodal distribution* of ego trajectories and commit to one — frequently the
optimistic mode that drives into the actor. Replace "brake when risky" with:

> **Re-rank the frozen planner's own multimodal ego trajectories by a label-free introspective
> collision-risk score, and execute the safest *feasible* mode.**

The monitor never invents a trajectory; it only ever chooses among trajectories the planner already
produced.

## Why it can succeed where intervention failed

- **Safe on false alarms.** The candidates are planner-generated, in-distribution, kinematically feasible
  and smooth. The iteration-11 failure mode — swerving into a benign parked car — is structurally
  impossible, because every option is a trajectory the planner itself judged drivable. This directly
  answers the false-positive-asymmetry lesson (a stop is safe when wrong; an invented swerve is not; but
  *choosing the planner's own alternative* is always at least as safe as the planner).
- **Can prevent, not just mitigate.** The head-on defeated the stop (ego stays in the actor's lane) and
  the swerve (out-of-distribution, crashed). A *planner-generated* mode that eases aside or slows is both
  feasible and safe; selecting it prevents the collision the default mode causes.
- **Distinct from prior runtime monitors.** The runtime-monitoring literature almost exclusively *brakes
  or flags*. Re-ranking a frozen planner's own multimodal output via a label-free introspective signal,
  evaluated closed-loop on NeuroNCAP, is a different mechanism. It also closes the arc from
  [PerceptionProof](https://github.com/manfromnowhere143/perceptionproof): *there*, introspective signals
  were shown to predict failure (AUROC ~0.8); *here*, they are used to make the planner choose its own
  safer intention. Framing: **the planner is overconfident in one mode; introspection detects it and
  defers.**

## Plan

1. **Fix the VAD runtime path.** VAD is the natural first target (native multimodal planning head). The
   iteration-10 VAD smoke revealed a runtime bug (JSON/image decode between renderer and VAD, only 1/3
   runs completed). Debug the renderer↔VAD I/O first. (Infra already built: image, checkpoint, mini-scene
   infos, union patch — see `experiments/vad_generalization/`.)
2. **Expose the multimodal candidates.** Modify VAD's inference server to return *all* ego trajectory
   modes (not just the argmax), plus their planner scores. For UniAD (single-mode), obtain candidates via
   command-conditioning (left/straight/right) or the planning query — a secondary, harder target.
3. **The re-ranker.** For each candidate, compute the union's collision-risk (plan-vs-tracked-path CPA and
   observed-closing TTC over the candidate). Select the min-risk feasible mode; keep a hysteresis/latch to
   avoid mode chatter; fall back to the committed stop only if *all* modes are high-risk (the safe floor).
4. **Evaluate honestly.** OFF (planner default) vs re-ranker vs the union stop, on stationary/frontal/side,
   ≥6 runs, then pooled bootstrap CIs. Success = frontal collision falls *below* the stop's ~83% (genuine
   prevention) with clean ≈ OFF (the re-ranker must not degrade the benign scene — and structurally it
   should not).
5. **Baseline vs published runtime monitors** (RiskMonitor / CATPlan-style) on the same metric, so the
   contribution is measured against the field, not only against OFF.
6. **Scale + generalize.** Full 14-scene NeuroNCAP benchmark — confirmed (probe on scene 0099) to require
   the gated nuScenes trainval sensor blobs for the 12 non-mini scenes, so it needs the account download —
   and both planners.

## Honest risks

- VAD's multimodal head may not expose cleanly separable, high-quality alternative modes at inference; if
  the alternatives are all minor variations of the argmax, re-ranking cannot prevent a committed head-on.
  That would itself be a reportable finding about planner mode diversity.
- If the safe alternative does not exist among the planner's modes for the hardest head-on, the result
  degrades gracefully to the union stop (no regression, no unsafe behavior) — the floor is safe by design.

The bar remains unchanged: real numbers, pre-registered, nulls published with the wins, CIs on the
headline, classically professional presentation.
