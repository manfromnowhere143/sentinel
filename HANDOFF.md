# HANDOFF — dynamic state snapshot

Generated: א' יול  5 22:41:01 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
9cbac87 paper: iterations 18-19 folded in — the plan-B deficit located in the planning representation joins the abstract and negative-results section; recompiled; arXiv package rebuilt; continuity arc current
8147007 continuity: the baton is permanent and bidirectional — every operator stays handoff-ready at all times; shift-log convention
8d26692 readme: iteration count current at nineteen
d5fcb9d iter19 gate verdict: D1 fails at 0/37 feasible escapes with D3 passing — the pre-registered null; the collapse is located in the planning representation itself (third measurement, third route)
5c8a9d8 iter19: the offline gate harness — iteration-12 rulers reused verbatim, deterministic frame join with executed-plan cross-check, D1 counts feasible escapes only, binomial CI reported
4368ec8 paper: commit the arXiv submission package referenced by the continuity doc
ad0b759 operator continuity system: CONTINUITY.md (invariants, baton protocol, box playbooks) + make_handoff.py (one-command dynamic state snapshot) — campaign portable across operators
274fbda readme through iterations 18-19 with the two-act arc extended; docs integrity guard added to CI (diagram budgets, link health, story completeness — it immediately caught three unlinked experiment directories)
```
Working tree: DIRTY — resolve before handoff:
?? HANDOFF.md

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
```
sentinel-gpu
 22:42:08 up 1 day, 12:23,  0 users,  load average: 0.00, 0.00, 0.11
/var/log/sentinel-vitals.log
/var/log/sentinel-evalextract.log
/var/log/sentinel-train.log
/dev/root       310G  285G   26G  92% /
Swap:          8.0Gi        61Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter19_diversity_head/HYPOTHESIS.md — read it in full; its gate governs the next action.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: python3 -m pytest -q && ruff check . && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
