# Iteration 19 — the diversity-trained candidate head: pre-registration (offline stage first)

Frozen before any training run. This is the campaign's deepest swing, and its motivation is
entirely measured:

- **The planner has no plan B** (iterations 12 and 14): UniAD's command-conditioned candidates
  collapse from 13.9 m of benign diversity to a 4 cm spread under threat (0/37 escapes); VAD's
  native modes reach only 21% against the frozen 30% viability bar. The runtime selector
  mechanism is sound; the candidate set is what's missing.
- **Every intervention that is not a planner-shaped trajectory has been refuted** (evasions ×3,
  crawl, router): invented maneuvers are unsafe when wrong, softness is unsafe when right, and
  the stop — safe in both directions — cannot prevent the frontal head-on or win deployment.
  A *trained, in-distribution, diverse* candidate set is the remaining mechanism class.
- To the verified corpus ([RELATED_WORK.md](../../docs/RELATED_WORK.md) §2–3), no published
  work trains a diversity-preserving candidate head for a **frozen** planner with an external
  runtime safety selector. The slot is open.

## The mechanism

A small trajectory head (**frozen planner untouched**) producing K=8 candidate trajectories per
frame, conditioned on cheap planner-internal state, selected at runtime by the union's
label-free risk score with the released stop as the floor (a candidate is executed only if its
risk clears both the planner's plan and the stop's; otherwise iteration-15 behaviour is
unchanged). Safe on false alarms by construction: every candidate is trained on real driving.

- **Conditioning signal:** the planner's internal planning-query embedding plus ego kinematic
  state — kilobytes per frame, not the full BEV tensor (the extraction hook and exact tensor
  names are documented in the extraction patch when built; the *choice* — planning-query-level
  conditioning, not raw BEV — is frozen here for storage and simplicity).
- **Architecture:** an MLP/GRU head, ≤5M parameters, emitting K trajectories over the planner's
  12-step horizon.
- **Training objective:** winner-takes-all imitation (best-of-K regression to the logged future)
  plus an inter-candidate repulsion term — the standard remedy for WTA collapse, applied here
  for the first time *outside* the planner it serves.
- **Data discipline (frozen):** training data only from nuScenes **train-split** scenes disjoint
  from every NeuroNCAP evaluation scene. The iteration-12 dangerous-frame corpus (37 frames) is
  **evaluation-only** — it never touches training. Any violation voids the result.

## Offline gate (no closed-loop time) — bars frozen now

Evaluated on the committed iteration-12 corpus with iteration-12's frozen definitions
(dangerous: executed-plan closest approach < 3.5 m; escape: a candidate with closest approach
> 5.0 m):

- **D1 — escape rate:** in > 30% of the 37 dangerous frames, the head offers an escape
  candidate — the exact bar the planner's own candidates failed at 0%.
- **D2 — feasibility:** every escape candidate respects kinematic limits (|curvature| ≤ 0.2
  1/m, |accel| ≤ 4 m/s², frame-to-frame continuity with the ego state) — diversity bought with
  infeasible trajectories is a null.
- **D3 — benign fidelity:** on benign frames of the same corpus, the best-of-K displacement
  error to the executed plan is within 1.5× the planner's own (the head must not be a wild
  generator that happens to score well on D1).

**Gate rule:** all three bars or no closed-loop pre-registration; a failed gate publishes as a
null with the measured mechanism, per the iteration-18 precedent.

## Falsifiers, named up front

- **Small-corpus overfitting:** 37 evaluation frames is few. Guard: the head never sees them in
  training (disjoint-split rule above), D1 is reported with a binomial CI, and the closed-loop
  stage (if reached) is the real test — its scenes are unseen by construction.
- **Diverse-but-doomed:** candidates diverge yet all still intersect the actor (escape by the
  3.5/5.0 m definitions but not in outcome) — surfaced in closed loop; reported.
- **Selector mismatch:** the union's risk score may rank a colliding candidate lowest (the
  score is geometric, not oracle). The committed-stop floor bounds the harm; the rate is
  reported from decision logs.
- If extraction shows the planning-query signal carries too little scene information for
  diverse-but-relevant candidates (D3 fails with D1 passing, or vice versa), the conditioning
  choice — not the mechanism class — is refuted; reported as such.

## Protocol

Stage 1 (GPU, ~hours): extraction patch dumps per-frame conditioning features + logged futures
on the training scenes; committed as a documented patch like every server patch before it.
Stage 2 (GPU, ~hours): train the head; training curves and config committed.
Stage 3 (no GPU): the offline gate above, from committed artifacts, harness + output committed.
Stage 4 (only through the gate): closed-loop pre-registration in a separate frozen document —
arms, bars, and falsifiers set there, comparators the committed OFF/released evidence.
