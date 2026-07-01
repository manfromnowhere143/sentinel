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

## Implementation (code-grounded — verified against the actual UniAD inference source)

The candidate source is settled: UniAD is **command-conditioned**, so it is the first target (no VAD
runtime fix required to test the core idea). Precise changes:

**A. Candidate generation — `UniAD/inference/runner.py`, in `forward_inference`.** The expensive stages
(`bev_embed`, `outs_track`, `outs_motion`) already run once. Directly after the existing single
`outs_planning = self.model.planning_head.forward(..., command=input.command)` call, loop the *head only*
over the three commands and collect the trajectories — cost is three lightweight head passes, no second
backbone:
```
cand = []
for c in (0, 1, 2):  # right / straight / left  (command is an int into the planning head)
    op = self.model.planning_head.forward(
        bev_embed, occ_mask, outs_motion["bev_pos"],
        outs_motion["sdc_traj_query"], outs_motion["sdc_track_query"],
        command=torch.tensor(c).to(self.device).unsqueeze(0))
    cand.append(_format_trajs(op["sdc_traj"])[0].cpu().numpy())
```
Add `candidate_trajs: Optional[np.ndarray]` (shape `3 x 6 x 2`) to `UniADAuxOutputs` and emit it in
`to_json()` (alongside `objects_in_bev`, `object_scores`, `object_ids`, `future_trajs` at runner.py:76-95).

**B. Transport — `UniAD/inference/server.py`.** Add `candidate_trajs: Optional[list] = None` to the
`InferenceAuxOutputs` pydantic model so the field is not dropped in transit.

**C. Re-ranker — the Sentinel server patch (extends the union's `_sentinel_intervene`).** The tracking,
ego2world, and CPA/closing-TTC risk are already implemented there. For each of the three candidates,
transform to world frame and compute the union risk (min plan-vs-tracked-path CPA and observed-closing
TTC over that candidate). Select `argmin(risk)`; add hysteresis/latch to prevent mode chatter; and — the
safe floor — fall back to the committed stop only if *all three* candidates exceed the risk threshold.
Because every returned trajectory is one UniAD itself produced, the iteration-11 clean-scene crash is
structurally impossible.

**D. First empirical checkpoint (do this before the full sweep).** Log all three candidates' risks on the
frontal scene and confirm the pre-condition of the whole thesis: **does a low-risk command-conditioned
plan exist when the default (straight) plan is high-risk?** If yes, re-ranking can prevent the head-on;
if the three commands are near-identical in the head-on, that is itself the finding (planner mode
diversity is insufficient) and the effort pivots to VAD's native modes or candidate synthesis.

**E. Evaluate.** OFF (planner default command) vs re-ranker vs union-stop, stationary/frontal/side, ≥6
runs → pooled bootstrap CIs; then a published-monitor baseline; then scale (14 scenes, gated data) and
VAD.

## VAD as the second candidate source

`VAD_head.py` exposes `ego_fut_mode=3` and `ego_fut_preds` of shape `[B, 3, fut_ts, 2]`; the VAD runner
currently returns only the selected mode. Exposing all three (plus their mode scores) is the parallel
path once the VAD renderer-to-model runtime bug is fixed (`experiments/vad_generalization/`).

The bar remains unchanged: real numbers, pre-registered, nulls published with the wins, CIs on the
headline, classically professional presentation.
