# Iteration 48 pre-launch ON-arm smoke — NOT a scheduled episode

This directory holds the evidence of the single pre-launch tooling sanity check run by
[`smoke_on_arm.sh`](../smoke_on_arm.sh) on 2026-07-12 (box log
[`i48-smoke-run.log`](i48-smoke-run.log), evidence dir on the box:
`/datasets/nuscenes-full/hugsim/iter48_smoke/scene-0013-easy-00__on_smoke_20260712T071450Z`).

Binding scope: the pre-registration (`HYPOTHESIS.md`) has no smoke provision, so this run
is disclosed here as a non-scheduled sanity check. It is EXCLUDED from the analyzer, from
every completion bar, and from every claim; its output lives outside the registered
`iter48_runs` collection root; nothing was tuned (the monitor parameters are the patch's
baked-in frozen defaults, echoed in every decision row below).

What it verified, on `scene-0013-easy-00` with `SENTINEL_ENABLED=1`:

- `SENTINEL_I48_UNION_PATCH_LOADED enabled=1` printed to the episode log
  ([`output.txt`](output.txt)) with the frozen parameter block echoed.
- 15 per-frame `SENTINEL_I48_DECISION` lines in the episode log and 15 full-input rows in
  [`sentinel_iter48_decisions.jsonl`](sentinel_iter48_decisions.jsonl) (plan, tracked
  boxes/scores/ids, l2g pose, params echo, fired/brake/release/latch state) — the monitor
  consumed real tracked objects from the client's own forward pass (e.g. frame 1: one
  tracked object, score 0.534, at ~28.8 m; `min_cpa 30.15`).
- Zero-fire logged cleanly: `fired=0` on all 15 frames (no object inside the frozen CPA
  margin or TTC threshold on this easy scene), the pre-registered clean alternative to an
  observed brake override; the override write path itself is exercised by construction
  (`brake -> np.zeros_like(plan_traj)` into the plan pipe) and is validated per-episode by
  the launcher's decision-line checks during the registered run.
- The episode completed end-to-end under the patch: `I48_SMOKE_RC=0`, finite HD-Score in
  [`eval.json`](eval.json), no containers left running.
