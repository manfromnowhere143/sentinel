# Iteration 21, offline gate — BEV conditioning does not recover a deployable plan B

The BEV-conditioned diversity head hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested
exactly as registered: train-split BEV extraction and head training first, then one offline
gate on the committed iteration-12 evaluation corpus. Harness:
[`analyze_bev_gate.py`](analyze_bev_gate.py). Output:
[`proof-gate/gate_output.txt`](proof-gate/gate_output.txt).

## Verdict

| bar | result |
|---|---|
| **B0** extraction integrity | **PASS**: 311/311 frames joined, zero executed-plan mismatches |
| **B1** feasible escape rate >= 12/37 | **0/37 = 0.0% — FAIL**; exact two-sided 95% binomial CI [0.0%, 9.5%] |
| **B2** candidate feasibility | **574/2488 = 23.1% — FAIL** (bar: >=90%); 102 infeasible would-be escapes |
| **B3** benign fidelity | **1.449 m — FAIL** (bar: <=0.780 m) |
| **B4** selector compatibility | **0/0 = 0.0% — FAIL**; no feasible escapes existed for the selector to choose |

**Per the frozen gate rule, no closed-loop run is allowed from this hypothesis.**

## What the null establishes

Iteration 19 left one named survivor: maybe the missing feasible alternative existed earlier in
the frozen planner's scene-level BEV representation, before the planning-query bottleneck. This
test gave that survivor the registered training/extraction path and the same evaluation-only
dangerous-frame ruler. The answer for this mechanism is negative.

B0 matters: the gate did not fail because the extraction drifted. The frame join was exact
against iteration 12, and the executed plans matched. The failure is in the candidate source:
the K=8 BEV head produced **zero feasible escapes** on the 37 dangerous frames. It also bought
invalid divergence: 102 would-be escapes violated the pre-registered feasibility limits, and
only 23.1% of all emitted candidates were valid. Unlike iteration 19, benign fidelity did not
hold either (1.449 m vs the 0.780 m bar), so this head is neither a faithful ordinary-driving
decoder nor a threat-useful alternative source.

The conservative reading is narrow and important: this result refutes the registered
BEV-conditioned head, not every possible learned planner or every possible use of scene-level
features. But the tested route from a frozen planner to a label-free runtime selector is closed
again. Four measurements now agree at the plan-B boundary: UniAD command candidates **0/37**,
VAD native modes **21%** below bar, the planning-query diversity head **0/37**, and this
BEV-conditioned head **0/37** with poor feasibility.

## Evidence

Training extraction proof: [`proof-extract/`](proof-extract/). Training proof and checkpoint:
[`proof-train/`](proof-train/). Evaluation extraction proof:
[`proof-gate/sentinel-bev-evalextract.log`](proof-gate/sentinel-bev-evalextract.log) and
[`proof-gate/sentinel_bev_evalextract.jsonl.gz`](proof-gate/sentinel_bev_evalextract.jsonl.gz).
The required BEV gzip validates and contains 335 JSONL records: 24 reset markers and 311 BEV
frame rows. The optional shadow log was absent on the GPU run; the log preserves the gzip
warning, and the gate does not depend on that file.

Reproduce the gate:

```bash
python3 experiments/iter21_bev_diversity_head/analyze_bev_gate.py \
  experiments/iter12_plan_selection/proof/sentinel_cand.jsonl.gz \
  experiments/iter21_bev_diversity_head/proof-gate/sentinel_bev_evalextract.jsonl.gz \
  experiments/iter21_bev_diversity_head/proof-train/bev_diversity_head.pt
```
