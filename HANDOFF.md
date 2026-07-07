# HANDOFF — dynamic state snapshot

Generated: Tue Jul  7 07:46:36 UTC 2026 by scripts/make_handoff.py. Read CONTINUITY.md first.

## Repository state
```
67f051b tools: add direct iter28 rsync transport
83ede98 tools: enable faster iter28 IAP uploads
948b2d0 tools: add resumable iter28 archive upload
e7439e8 handoff: refresh iter28 staging transfer
5340e92 tools: harden iter28 archive staging
7f37c84 handoff: refresh during iter28 staging
614ad2e analysis: stage iter28 metadata archive proof
dd62911 tools: add iter28 staging surface
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
 07:47:42 up 2 days, 21:28,  0 users,  load average: 0.01, 0.02, 0.00
GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS
/var/log/sentinel-vitals.log
/var/log/sentinel-e23-extract.log
/var/log/sentinel-e23-canary.log
/dev/root       310G  287G   24G  93% /
Swap:          8.0Gi        60Mi       7.9Gi
```
If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run
is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.

## Live iter28 transfer note
- `v1.0-trainval_meta.tgz` is staged and proof is committed in `614ad2e`.
- `v1.0-trainval03_blobs.tgz` upload is in progress from local
  `/Users/danielwahnich/Downloads/v1.0-trainval03_blobs.tgz` to
  `/datasets/nuscenes-full/.iter28_tmp/iter28-upload-v1.0-trainval03_blobs.tgz`, then
  `/datasets/nuscenes-full/archives/v1.0-trainval03_blobs.tgz`.
- Do not delete the local part 3 archive until remote bytes and SHA256 match and its proof JSON
  is committed.
- Temporary direct SSH path is open for faster remaining local uploads:
  firewall rule `sentinel-direct-ssh-20260707`, source `176.229.61.140/32`, target tag
  `sentinel-direct-ssh`, VM external IP `35.227.136.146`. Remove this firewall rule and VM tag
  after iter28 staging or if Daniel's public IP changes.
- Use committed direct transport for subsequent local archives, e.g.
  `stage_local_archive.py --package 4 --local-path ... --rsync-transport direct --direct-host
  35.227.136.146`.

## Open threads (from the newest experiment docs)
- Newest pre-registration: experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md — read it in full; its gate governs the next action.
- Next research launch packet: docs/research/CAUSAL_PLANNER_INTERPRETABILITY.md — not a pre-registration; it authorizes no run.
- docs/NEXT_PHASE.md: check its status ledger/decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger/decision rules.

## Verification before you act
- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py
- All three must pass before and after your changes; CI enforces the same on push.
