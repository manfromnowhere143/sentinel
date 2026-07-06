# HANDOFF — dynamic state snapshot

Generated: Mon Jul  6 18:50:15 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
1a61c9f tools: add iter25 inventory surface
f15aa6b handoff: refresh after iter25 pre-registration
66e1315 docs: pre-register iter25 staged data inventory
3eaf186 handoff: refresh after iter24 result
80498c8 analysis: publish iter24 availability null
06c1a03 handoff: refresh after iter24 surface
ff98e59 tools: add iter24 risk support surface
c85c817 handoff: refresh after iter24 pre-registration
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
- experiments/iter23_s0_hardened_causal_localization: RESULT PUBLISHED
- experiments/iter24_risk_support_atlas: RESULT PUBLISHED
- experiments/iter25_staged_data_inventory: PRE-REGISTERED, result pending
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
 18:51:23 up 2 days,  8:32,  0 users,  load average: 0.00, 0.00, 0.00
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-e23-extract.log
/var/log/sentinel-e23-canary.log
/dev/root       310G  287G   24G  93% /
Swap:          8.0Gi        60Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter25_staged_data_inventory/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
