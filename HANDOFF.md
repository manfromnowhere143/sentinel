# HANDOFF — dynamic state snapshot

Generated: Mon Jul  6 21:50:46 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
5340e92 tools: harden iter28 archive staging
7f37c84 handoff: refresh during iter28 staging
614ad2e analysis: stage iter28 metadata archive proof
dd62911 tools: add iter28 staging surface
82971d1 docs: correct iter28 package scope
218e4aa docs: pre-register iter28 trainval staging
b5dbd90 handoff: refresh after iter27 result
64cd874 analysis: publish iter27 storage pass
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
- experiments/iter25_staged_data_inventory: RESULT PUBLISHED
- experiments/iter26_data_staging_remedy: RESULT PUBLISHED
- experiments/iter27_storage_provisioning: RESULT PUBLISHED
- experiments/iter28_nuscenes_trainval_staging: PRE-REGISTERED, result pending
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
 21:51:53 up 2 days, 11:32,  0 users,  load average: 0.08, 0.02, 0.01
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-e23-extract.log
/var/log/sentinel-e23-canary.log
/dev/root       310G  297G   14G  96% /
Swap:          8.0Gi        60Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Live iter28 transfer note
- `v1.0-trainval_meta.tgz` is staged and proof is committed in `614ad2e`.
- `v1.0-trainval03_blobs.tgz` upload restarted from local
  `/Users/danielwahnich/Downloads/v1.0-trainval03_blobs.tgz` using committed script `5340e92`.
  Its large temporary remote file now belongs under
  `/datasets/nuscenes-full/.iter28_tmp/iter28-upload-v1.0-trainval03_blobs.tgz`, not `/tmp`.
- Do not delete the local part 3 archive until remote bytes and SHA256 match and its proof JSON
  is committed.
- If Daniel provides real signed official nuScenes URLs, use
  `stage_local_archive.py --signed-url-file <uncommitted-temp-file>`; never scrape browser cookies
  or commit URL query material.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
