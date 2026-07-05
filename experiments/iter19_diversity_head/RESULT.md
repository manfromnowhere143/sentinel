# Iteration 19, offline gate — D1 fails at 0/37: the collapse lives in the representation

Stage 1 completed in full (2,385-frame conditioning corpus from 60 disjoint train scenes; a
1.2M-parameter K=8 head trained to 0.52 m best-of-8 validation error with an active repulsion
term). The frozen offline gate ([HYPOTHESIS.md](HYPOTHESIS.md)) was then scored on iteration
12's 37 evaluation-only dangerous frames, with iteration 12's danger/escape rulers reused
verbatim and the frame join proven exact (311/311 frames, zero executed-plan mismatches
between runs four days apart — the determinism, again). Harness:
[`analyze_gate.py`](analyze_gate.py); output committed in
[`proof-gate/gate_output.txt`](proof-gate/gate_output.txt).

## The verdict

| bar | result |
|---|---|
| **D1** escape rate > 30% (feasible escapes) | **0/37 = 0% — FAIL** (binomial CI [0%, 0%]) |
| D2 kinematic feasibility | folded into D1: **16 would-be escapes rejected** (curvature/accel violations); raw counts reported |
| D3 benign fidelity ≤ 0.780 m | 0.769 m — PASS |

**Per the gate rule, no closed-loop run happens; the null publishes.**

## What the null establishes (the pre-registration's own reading)

The falsifier written before any training fired exactly: *D1 failing with D3 passing refutes
the conditioning choice, not the mechanism class.* The head is a faithful trajectory generator
(benign fidelity within its bar) and its repulsion term does force divergence under threat —
16 diverging candidates appeared on the dangerous frames — but **every diverging candidate was
kinematically infeasible**. Conditioned on the planner's own planning-query embeddings, the
head can only re-express what the representation contains, and under threat that
representation has already committed: iteration 12 measured the collapse in the planner's
*outputs* (14 m of benign diversity to 4 cm); this iteration shows the collapse is present in
the planner's *internal planning state* itself — feasible alternatives cannot be decoded from
a representation that no longer holds them.

Three measurements now frame the finding, each by a different route: UniAD's
command-conditioned candidates (0/37), VAD's native modes (21%, below the bar), and a
diversity-trained head on UniAD's planning queries (0/37 feasible). The plan-B deficit of
end-to-end planners is not a decoder artifact — it sits in the planning representation.

## What remains open (named, not built)

Richer conditioning — scene-level features (BEV) rather than the committed planning queries —
is the surviving variant of this mechanism class, at meaningfully higher storage and training
cost, and it now carries a sharpened burden: it must demonstrate that feasible-alternative
information exists *anywhere* in the frozen planner under threat. The deployment flip
(+0.226 vs OFF, CI excluding zero — iteration 17) remains proven achievable and unclaimed.

## Evidence

[`proof-extract/`](proof-extract/) (training corpus, GT sidecar, head checkpoint, training
log) · [`proof-gate/`](proof-gate/) (evaluation extraction, run log, gate output). Reproduce:
`analyze_gate.py <iter12 cand jsonl.gz> <evalextract jsonl.gz> <diversity_head.pt>`.
