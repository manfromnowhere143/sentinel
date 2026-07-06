# HANDOFF — dynamic state snapshot

Generated: Mon Jul  6 12:22:16 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
b2d10c3 tools: add iter23 availability manifest generator
4a7aa9c handoff: refresh after iter23 preregistration
6062f16 docs: pre-register iter23 s0 hardened localization
f9575a2 handoff: refresh after iter22 result
eae9310 docs: publish iter22 stage1 data null
3ec2ddd handoff: refresh after iter22 baseline analysis
8cd3ed4 analysis: report iter22 stage1 integrity null
14ae6d0 handoff: refresh after iter22 extraction proof
```
Working tree: CLEAN

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
- experiments/iter21_bev_diversity_head: RESULT PUBLISHED
- experiments/iter22_causal_planner_interpretability: RESULT PUBLISHED
- experiments/iter23_s0_hardened_causal_localization: PRE-REGISTERED, result pending
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
 12:23:25 up 2 days,  2:04,  0 users,  load average: 0.00, 0.00, 0.00
/var/log/sentinel-vitals.log
/var/log/sentinel-e22-extract.log
/var/log/sentinel-bev-evalextract.log
/dev/root       310G  287G   24G  93% /
Swap:          8.0Gi        60Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
