# Iteration 12 — introspective plan selection: pre-registration

Frozen before the candidate data exists. The mechanism and rationale are in
[`../../docs/NEXT_FRONTIER_INTROSPECTIVE_PLAN_SELECTION.md`](../../docs/NEXT_FRONTIER_INTROSPECTIVE_PLAN_SELECTION.md);
the iteration-11 lesson it answers: an *invented* maneuver is unsafe on false alarms, so the only
safe way to do better than a committed stop is to choose among trajectories the planner itself
produced.

## Checkpoint D — the pre-condition (data collection before any re-ranker code)

UniAD's planning head is command-conditioned (0 right, 1 left, 2 straight — the runner's own
docstring). `patch_candidate_logging.py` logs all three candidate plans per frame,
behaviour-preserving, on the deterministic corpus (run indices 0–7: frontal 6/8 collisions,
side 8/8, stationary 0/8).

**Frozen analysis parameters** (`analyze_candidates.py`, chosen from the G1 shadow study before
seeing any candidate data): a frame is *dangerous* when the executed plan's closest predicted
approach to any agent's forecast is < 3.5 m (G1 showed the planner's optimistic forecast reads
3–4 m gaps on runs that actually collide); an *escape* exists when another command's plan has
closest approach > 5.0 m and larger than the executed plan's.

**Decision rule (frozen):**
- If an escape candidate exists in > 30% of dangerous frames → build the re-ranker (H12 below).
- If the three candidates collapse under threat (≤ 30%) → that is the reported finding
  ("command-conditioning does not diversify UniAD's plan under threat") and the effort pivots to
  VAD's native `ego_fut_mode=3` — no re-ranker is built on UniAD.

## H12 (only if the pre-condition holds)

Re-ranking the planner's own three command-conditioned candidates by the union's label-free risk
(world-frame CPA + observed-closing TTC over each candidate), executing the min-risk feasible
candidate, with the committed stop as the floor when *all* candidates are high-risk:

1. **Frontal prevention:** frontal collision rate falls *below* the committed stop's ~83%
   (run indices 0–19; the stop could only soften these).
2. **Selectivity preserved:** clean-scene distance ≈ OFF (re-ranking must not degrade the benign
   scene — structurally expected, since in a benign frame all candidates are low-risk and the
   executed plan is chosen).
3. **Side preserved:** side collisions ≤ the union's rate (the stop floor still fires there if no
   candidate clears the crossing).

Evaluation: OFF vs union-stop vs re-ranker, 3 scenes × 20 unique episodes, seed-paired;
within-scene bootstrap CI on the safe-progress delta.

## Falsifiers, named up front

- Escape candidates exist geometrically but are not *kinematically honored* by the LQR tracker
  (the plan diverges but the executed motion cannot follow it in time) → re-ranker fails to
  prevent; report as "candidate diversity without executable diversity".
- The re-ranker chatters between modes and degrades progress → hysteresis is part of the design;
  if it still chatters, that is a reported failure mode.
- Command-conditioning may diversify *routing* (left/right/straight at intersections) but not
  *hazard response* on a straight road — the checkpoint-D corpus (frontal head-on on a straight
  approach) is exactly the hard case for this concern.
