# HANDOFF — dynamic state snapshot

Generated: Sun Jul  5 23:11:51 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
ae13870 continuity: record iter20 VAD tracker null
d5752eb iter20: publish VAD tracker portability null
c345dff iter20: correct VAD replay scene parser
8b6aeac iter20: add VAD tracker replay harness
0c20322 iter20: clarify VAD replay pose evidence
a577386 iter20: pre-register VAD tracker portability gate
727db42 handoff snapshot committed; shift log closed — box idle, no runs in flight, open threads named
9cbac87 paper: iterations 18-19 folded in — the plan-B deficit located in the planning representation joins the abstract and negative-results section; recompiled; arXiv package rebuilt; continuity arc current
```
Working tree: DIRTY — resolve before handoff:
M HANDOFF.md

## Experiments (status inferred from files)

- experiments/full14_benchmark: RESULT PUBLISHED
- experiments/full14_power: RESULT PUBLISHED
- experiments/iter10_brakevade: RESULT PUBLISHED
- experiments/iter11_early_evade: RESULT PUBLISHED
- experiments/iter12_plan_selection: RESULT PUBLISHED
- experiments/iter13_rss_baseline: RESULT PUBLISHED
- experiments/iter15_latch_release: RESULT PUBLISHED
- experiments/iter16_soft_stop: RESULT PUBLISHED
- experiments/iter17_threat_routing: RESULT PUBLISHED
- experiments/iter18_tracker: RESULT PUBLISHED
- experiments/iter19_diversity_head: RESULT PUBLISHED
- experiments/iter1_reproduce: artifacts only
- experiments/iter1b_partial_baseline: artifacts only
- experiments/iter20_vad_tracker_portability: RESULT PUBLISHED
- experiments/iter2_monitor: RESULT PUBLISHED
- experiments/iter3_progress: RESULT PUBLISHED
- experiments/iter4_gated: RESULT PUBLISHED
- experiments/iter5_tracked: RESULT PUBLISHED
- experiments/iter6_cpa: RESULT PUBLISHED
- experiments/iter7_margin: RESULT PUBLISHED
- experiments/iter8_union: RESULT PUBLISHED
- experiments/iter9_evade: RESULT PUBLISHED
- experiments/union_validation: RESULT PUBLISHED
- experiments/vad_generalization: RESULT PUBLISHED
- experiments/verification: artifacts only

## GPU box quick-state (live probe)
Box state: IDLE — no GPU run launched during iteration 20; no run is known to be in flight.

```
sentinel-gpu
 23:12:57 up 1 day, 12:54,  0 users,  load average: 0.00, 0.00, 0.00
/var/log/sentinel-vitals.log
/var/log/sentinel-evalextract.log
/var/log/sentinel-train.log
/dev/root       310G  285G   26G  92% /
Swap:          8.0Gi        61Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter20_vad_tracker_portability/HYPOTHESIS.md — read it in full; its gate governs the next action.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: python3 -m pytest -q && ruff check . && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
