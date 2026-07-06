# HANDOFF — dynamic state snapshot

Generated: Mon Jul  6 18:09:39 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
ff98e59 tools: add iter24 risk support surface
c85c817 handoff: refresh after iter24 pre-registration
df5b173 docs: pre-register iter24 risk support atlas
8ed5253 handoff: refresh after explicit GPU idle state
152df8a tools: make handoff GPU state explicit
eb22748 handoff: refresh after iter23 result
2f0a115 analysis: publish iter23 count-floor null
8431802 data: add iter23 full extraction proof
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
- experiments/iter24_risk_support_atlas: PRE-REGISTERED, result pending
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
 18:10:47 up 2 days,  7:51,  0 users,  load average: 0.00, 0.00, 0.00
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
- Newest pre-registration: experiments/iter24_risk_support_atlas/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
