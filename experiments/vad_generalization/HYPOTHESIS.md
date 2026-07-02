# VAD run — pre-registration (generalization + the plan-selection checkpoint on native modes)

Frozen before the VAD run executes. Two questions, one 20-episode pass:

## H-VAD-1 — does the union transfer to a second frozen planner?

VAD's inference server exposes the same aux schema (objects, scores, IDs, forecasts), so the union
monitor runs unchanged (only anchors differ). On stationary/frontal/side × 20 unique episodes,
OFF vs union, seed-paired:

- **Transfer confirmed if** the union's three properties hold directionally on VAD: clean-scene
  behaviour ≈ OFF, side-impact collision rate reduced by more than half, frontal impact speed cut.
- **Reported as a boundary if not** — a monitor that works on UniAD only is a finding about
  planner-specific failure signatures, not a failure of honesty.

Note VAD ships its own collision optimizer (`use_col_optim`, occupancy-based trajectory
refinement) — VAD's OFF arm is already a *defended* planner. Beating or matching it is a harder,
more interesting test than UniAD's raw head, and the published VAD NeuroNCAP score (2.75 vs
UniAD's 1.84) says so. Named up front, not discovered after.

## H-VAD-2 — checkpoint D on native modes (the iteration-12 question, second planner)

VAD emits all three ego_fut_preds modes from a single forward pass every frame (free candidates —
no head re-run). The modes are command-indexed, like UniAD's conditioning, but trained as parallel
output heads. `patch_vad_candidates.py` logs all three per frame in the OFF arm
(behaviour-preserving; same record schema as iteration 12, analyzed by the same frozen script and
thresholds: danger < 3.5 m, escape > 5.0 m, decision bar > 30% of dangerous frames).

- **If VAD's modes stay diverse under threat** → the re-ranker (iteration-12 H12 design) is built
  on VAD.
- **If they collapse like UniAD's** → that is a *two-planner* result about end-to-end planner mode
  diversity under threat — a stronger negative than iteration 12 alone, published as such — and
  plan selection on command-indexed heads is closed.

## Protocol

`vad_run.sh`: OFF vs union, 3 scenes × `--runs 20`, smoke-verified config (`VAD_inference.py`,
`VAD_base.pth`), the renderer-tensor decode fix applied after the union patch. Candidate log
analyzed by `../iter12_plan_selection/analyze_candidates.py` unchanged.
