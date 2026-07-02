# Iteration 12 — checkpoint D: UniAD's command-conditioned candidates collapse under threat (null)

The plan-selection thesis ([HYPOTHESIS.md](HYPOTHESIS.md), frozen before the data) required one
pre-condition: when the executed plan is dangerous, some *other* command-conditioned plan must be
clear. The data answers **no**, decisively, so per the frozen decision rule the UniAD re-ranker is
**not built** and the effort pivots to VAD's native multimodal head.

## The measurement

`patch_candidate_logging.py` logged all three command-conditioned plans (0 right, 1 left,
2 straight) per frame, behaviour-preserving, over the deterministic corpus (frontal / side /
stationary × run indices 0–7): **311 frames**, zero logging errors. Analysis
(`analyze_candidates.py`, thresholds frozen in the hypothesis):

| quantity | value |
|---|---|
| candidate divergence, all frames (max endpoint spread) | median 2.58 m · max 13.94 m |
| dangerous frames (executed plan's closest predicted gap < 3.5 m) | 37 |
| mean closest gap in danger — command 0 / 1 / 2 | **2.85 / 2.88 / 2.84 m** |
| escape candidates (alt gap > 5.0 m and better than executed) | **0 / 37 = 0%** (bar: > 30%) |

## What it means

- **The mechanism works; the planner lacks the diversity.** In benign frames the three commands do
  produce genuinely different trajectories (endpoint spreads up to 14 m — routing diversity). In
  the 37 dangerous frames they collapse to nearly the *same* trajectory: the three mean gaps span
  4 cm. UniAD's planning head treats the command as a routing hint, not a hazard-response degree
  of freedom.
- **Introspection sees the danger; UniAD holds no safer intention to defer to.** The pre-condition
  of plan selection fails at the planner, not at the monitor — a statement about end-to-end
  planner *mode diversity under threat*, which the hypothesis named in advance as the reportable
  alternative outcome.
- **The frontal ceiling stands, for a deeper reason.** After three refuted evasion designs
  (iterations 9–11) showed *invented* maneuvers are unsafe, this shows the safe alternative —
  choosing among the planner's own intentions — is empty on UniAD when it matters.

## Pivot (pre-registered)

VAD emits `ego_fut_mode = 3` native trajectory modes with scores — plan diversity that exists by
construction rather than via command conditioning. The plan-selection mechanism is tested there
next; the blocking VAD runtime work is staged in
[`../vad_generalization/STATUS.md`](../vad_generalization/STATUS.md).

## Evidence

Per-frame candidate log (all three plans + detected objects + forecasts per frame):
[`proof/sentinel_cand.jsonl.gz`](proof/sentinel_cand.jsonl.gz); run log
[`proof/sentinel-cand.log`](proof/sentinel-cand.log). Reproduce the table:
`python3 analyze_candidates.py proof/sentinel_cand.jsonl.gz` (reads gzip directly; thresholds
default to the frozen values).
