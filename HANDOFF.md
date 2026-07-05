# HANDOFF — dynamic state snapshot

Generated: Sun Jul  5 23:26:34 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
411f3b8 iter21: add BEV extraction patch
93d6840 iter21: pre-register BEV diversity head gate
5964cbb handoff: snapshot after iter20 tracker null
ae13870 continuity: record iter20 VAD tracker null
d5752eb iter20: publish VAD tracker portability null
c345dff iter20: correct VAD replay scene parser
8b6aeac iter20: add VAD tracker replay harness
0c20322 iter20: clarify VAD replay pose evidence
```
Working tree: DIRTY — resolve before handoff:
M CONTINUITY.md
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
- experiments/iter21_bev_diversity_head: PRE-REGISTERED, result pending
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
Run state: IN FLIGHT — iteration 21 Stage-1 BEV train extraction. Log:
`/var/log/sentinel-bev-extract.log`. Done marker: `BEV_EXTRACT_DONE`. Expected artifacts:
`/opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl(.gz)` and
`/opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl(.gz)`. Do not relaunch while the
`model` container is running or the done marker is absent.

```
sentinel-gpu
 23:27:40 up 1 day, 13:08,  0 users,  load average: 1.02, 0.52, 0.21
/var/log/sentinel-bev-extract.log
/var/log/sentinel-vitals.log
/var/log/sentinel-evalextract.log
/dev/root       310G  285G   26G  92% /
Swap:          8.0Gi        60Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter21_bev_diversity_head/HYPOTHESIS.md — read it in full; its gate governs the next action.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: python3 -m pytest -q && ruff check . && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
