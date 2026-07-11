# Box disk cleanup record — 2026-07-12 (pre-HUGSIM transfer lane)

Operator: Claude (Fable 5) via delegated executor. Box: `sentinel-gpu` (idle, no Docker
containers, no run in flight). Purpose: free root disk for the HUGSIM second-benchmark
transfer lane (iteration 45 infra gate) per the verified-cleanup precedent of the
iteration-42 preflight (`experiments/iter42_exact_trace_replay_support/proof-trace/gpu_preflight.txt`):
delete only items whose contents are verified inside committed repository artifacts.

## Verification method (applied before any deletion)

1. **Uncompressed `.jsonl` duplicates** in `/opt/sentinel-stack/UniAD/`: deleted only when
   the file's SHA256 (computed on the box) equals the SHA256 of the decompressed content of
   the committed `.jsonl.gz` (or concatenated `.jsonl.gz.part-*` set) of the same basename in
   this repository.
2. **On-box `.jsonl.gz` copies**: deleted only when byte-identical (SHA256) to the committed
   `.gz` file, or to the concatenation of its committed `.part-*` files.
3. **`outoutput/iter42-trace`** (12 GiB): its per-run JSON outputs (metrics, actors,
   ego_poses, trajectories, reference_trajectory; 400 runs, 2,000 files) were first archived,
   SHA-verified across the transfer, and committed as
   `experiments/iter42_exact_trace_replay_support/proof-runs-cleanup/i42-runs.tar.gz`
   (SHA256 `a1a55d5409511d07ca9db13e787ca3f338718c987935d0338457f0b271e214ff`, commit
   `5af5dc3`, pushed BEFORE deletion). Rendered frames were not preserved, matching the
   campaign convention (f14/p14 run archives keep JSON only; the registered iter42 evidence
   object is the committed exact trace, SHA unchanged).
4. **`/var/log/sentinel-*.log`**: deleted only when byte-identical (SHA256) to a committed
   log in `experiments/*/proof*/` or `experiments/verification/evidence/logs/`.
5. Anything not verifiable was SKIPPED and is listed below with the reason.

Docker images (167.6 GB) were NOT touched: they are the live NeuroNCAP/UniAD/renderer stack.
`/datasets/nuscenes` (22 GiB, root) and `/datasets/nuscenes-full` (1 TB data disk) were NOT
touched.

## Disk receipts (from `/tmp/sentinel-cleanup-20260712.log` on the box)

| | bytes free on `/` | use% |
|---|---|---|
| before (2026-07-11 22:27:32 UTC) | 16,578,969,600 (15.4 GiB) | 96% |
| after (2026-07-11 22:27:34 UTC) | 45,256,380,416 (42.1 GiB) | 87% |

Freed: 28,677,410,816 bytes (~26.7 GiB). Root target for the HUGSIM lane (>= 30 GiB free)
met; HUGSIM assets (~61 GB) go on `/datasets/nuscenes-full` (266 GiB free at record time).

## Deleted: run-output directory (verified inside committed archive)

| path | size | justifying committed artifact |
|---|---|---|
| `/opt/sentinel-stack/NeuroNCAP/outoutput/iter42-trace/` | 12 GiB | `experiments/iter42_exact_trace_replay_support/proof-runs-cleanup/i42-runs.tar.gz` (JSON evidence, 2,000 members) + committed exact trace `proof-trace/sentinel_iter42_trace.jsonl.gz` |

## Deleted: 196 `/opt/sentinel-stack/UniAD/` duplicates (16,025,193,553 bytes, 14.92 GiB)

Each row's on-box SHA256 was verified against the committed artifact as described above
(`decompressed content of` = method 1; `byte-identical to` = method 2).

| deleted box file | bytes | on-box SHA256 | justifying committed artifact |
|---|---|---|---|
| `/opt/sentinel-stack/UniAD/sentinel_ab.jsonl` | 25,503,672 | `f6ac1219379ba5d02a833b0b461a0ca7008d2a2d90663013d64b464cb91e65f1` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_ab.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_abl_always.jsonl` | 14,848,737 | `4990ac7267ad3d8b121e4489bc93719da910c576828860c94c4814ae8c337f50` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_abl_always.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_abl_proximity.jsonl` | 15,734,172 | `fc775bcae09cc0ac2f5f6dd77a11d544a1a12994c63a549379eef97d967ef12e` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_abl_proximity.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_evalextract.jsonl` | 47,948,846 | `5440856573ae295160395e8058ae4ae73a610efcfd02191619bd303d2d8babad` | decompressed content of `experiments/iter21_bev_diversity_head/proof-gate/sentinel_bev_evalextract.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_evalextract.jsonl.gz` | 16,884,330 | `a7f556007c995b5a21b9b5931893fa629bdfccdbc9a010efb7c079180ee64371` | byte-identical to `experiments/iter21_bev_diversity_head/proof-gate/sentinel_bev_evalextract.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl` | 367,904,851 | `37735e015637306b70a894e339e1aae060affee534cb27079e86a1b9beb74091` | decompressed content of `experiments/iter21_bev_diversity_head/proof-extract/sentinel_bev_extract.jsonl.gz.part-aa (+1 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl.gz` | 129,685,644 | `b5033767423add0eda25c2cac126d7c9f3c19bf65ad7d631efea0a18952277d9` | byte-identical to `experiments/iter21_bev_diversity_head/proof-extract/sentinel_bev_extract.jsonl.gz.part-aa (+1 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl` | 1,035,984 | `1450db6dde55e8d46bf0f0bff683b4ba2641d1f25e4db161ea22c5df35765546` | decompressed content of `experiments/iter21_bev_diversity_head/proof-extract/sentinel_bev_extract_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl.gz` | 365,302 | `6adb2e44e834b9a282f1630cbfbec479bf0779d5836d4237ad410894b07ab58e` | byte-identical to `experiments/iter21_bev_diversity_head/proof-extract/sentinel_bev_extract_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_cand.jsonl` | 21,465,550 | `9bb4a123d947fe0ffa7f6b6b388e58c51d6ad3b55c16d9e0ea0fb8798d7c8781` | decompressed content of `experiments/iter12_plan_selection/proof/sentinel_cand.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e22_stage1.jsonl` | 204,543,636 | `f6cfbb70bc88e0dca0fb457960c4ca70af8863a870ca8a27392759e1f2e8b35d` | decompressed content of `experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e22_stage1.jsonl.gz` | 89,161,655 | `831bf5ccb8f90c23e40e2e6ae32b6d639ec9e8fca2fb74519712c5badb782217` | byte-identical to `experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e22_stage1_gt.jsonl` | 679,949 | `18c86a20f2634703925542303c73e0d1d45ce2bc439d0c1c3d69d5aa05884152` | decompressed content of `experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e22_stage1_gt.jsonl.gz` | 233,757 | `369809a4ac0b4000be18b21290553367d9a428333f5a5406e8ddfa0089f77c52` | byte-identical to `experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_a.jsonl` | 962,981 | `4c27e7b1e1947828b71e96cc3e4a48c91a4030406716a80e45106ae9195c2e85` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_a.jsonl.gz` | 427,427 | `7949e593caa7647a75d43c15b95990f92696a50adaea8ba340890fdced7af1de` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_a_gt.jsonl` | 7,704 | `ea6c5033034299a75b98b5a845f21aad9c6a9478148de0c5c576158a531ad0bf` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_a_gt.jsonl.gz` | 2,887 | `7af8559a2beaf22dcbd4bb0f9aa929356cc94a21353a08cdfbd6c56cc6e803a2` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_b.jsonl` | 962,981 | `4c27e7b1e1947828b71e96cc3e4a48c91a4030406716a80e45106ae9195c2e85` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_b.jsonl.gz` | 427,427 | `d27ec634eb4196a5559973667d816627f9985647d3dbe7ad8f0c0c1d00405714` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_b_gt.jsonl` | 7,704 | `ea6c5033034299a75b98b5a845f21aad9c6a9478148de0c5c576158a531ad0bf` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_canary_b_gt.jsonl.gz` | 2,887 | `effadaccb5188c17808224883d50b23b6b7f5ca29cbdfd5cde33c2b7357f1778` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel_e23_canary_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_stage1.jsonl` | 345,976,334 | `96cbf041b9de42a65aa00a2b437bc676922160a94dcac4a9450c6c9f430e1f92` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-00 (+1 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_stage1.jsonl.gz` | 150,908,411 | `10218c99eb006da4d664c60f28578c34a322582c25242a4223ad7d99b834b2e3` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1.jsonl.gz.part-00 (+1 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_stage1_gt.jsonl` | 1,269,470 | `f39cf753c95c1906826946d1e636c25f62e97329769cd9d5784326397604ef4a` | decompressed content of `experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e23_stage1_gt.jsonl.gz` | 416,833 | `67f3be430757c34332ffb997b51f073fc419c4f378e1fb9494a715af8b957813` | byte-identical to `experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_a.jsonl` | 3,007,052 | `04fdddb8ac576d9de20ce3ae360dab6cf441b3e904f819e772498a8e60f8f1f8` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_a.jsonl.gz` | 1,326,438 | `f8fd25dd7111581479f4266956401868eac78fb5ee5a9e69b13ba5987f41d8f6` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_a_gt.jsonl` | 14,891 | `ed2e1fb740602b755a1af3155bd0a69b4ca96de310936fcbbce866973ce31942` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_a_gt.jsonl.gz` | 5,383 | `8f4a0b55460683694d52c27f1b268161fc4ad973aaeea7dbc787557aa6444d2f` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_b.jsonl` | 3,007,052 | `04fdddb8ac576d9de20ce3ae360dab6cf441b3e904f819e772498a8e60f8f1f8` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_b.jsonl.gz` | 1,326,438 | `7f9ff3a158786d6749932aac2bffe7b20873c68f82f6d1576c1b2d89802e638f` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_b_gt.jsonl` | 14,891 | `ed2e1fb740602b755a1af3155bd0a69b4ca96de310936fcbbce866973ce31942` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_canary_b_gt.jsonl.gz` | 5,383 | `a490059513af04aa12983673ac9885def1d09d7f783436a1429f020831228e2c` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel_e29_canary_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_stage1.jsonl` | 2,840,135,632 | `795b9132e6095c2f876f9942117efc31be82a6f9b1a44a8b2f0bfeeafb7c0d28` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-aa (+14 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_stage1.jsonl.gz` | 1,240,350,622 | `390bee5763d576005f5c49441b2ce7eab208d8396a893e329c6f70d5a0c1d03b` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-aa (+14 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_stage1_gt.jsonl` | 10,507,841 | `e92b38c2a17d12df5c6d9b4c2741b3f8446b3d4b5773fe8794c62e671ddf6f11` | decompressed content of `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e29_stage1_gt.jsonl.gz` | 3,433,613 | `3d2cecd2233cd43cd0ecde0e0bc1d834ad0928a1cbae3cb82756085be8134648` | byte-identical to `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_a.jsonl` | 2,102,595 | `db53f7ba54fa9cc3bda1128fc42aa26d5f77ddd78837e884a8d7a70658903cde` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_a.jsonl.gz` | 911,027 | `fb404aa3f7cac41abb8f0372aad0d128ef9c04f74f9d384796112bdcf77204ce` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_a_gt.jsonl` | 6,747 | `dedc0849256f5eb8b157a8d54579ea632c525fa7ac87170803aae9b605ba968c` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_a_gt.jsonl.gz` | 2,340 | `21b287da8ec00435519ed7c3a825e2e2a0c4688a6d1ea2fb6d87baa0f9c5b373` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_b.jsonl` | 2,102,595 | `db53f7ba54fa9cc3bda1128fc42aa26d5f77ddd78837e884a8d7a70658903cde` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_b.jsonl.gz` | 911,027 | `b274fd1f04c6e47382bb0b4c293fa5d5e33a9a0d455e2aef41b257d435059c79` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_b_gt.jsonl` | 6,747 | `dedc0849256f5eb8b157a8d54579ea632c525fa7ac87170803aae9b605ba968c` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p00_b_gt.jsonl.gz` | 2,340 | `bd4532b2f05d2661577bb676dbf8eea5f7295e6302e56dd0f618dd4e35406d3e` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_a.jsonl` | 2,102,559 | `728e80ee397bdd1a09910944f0882eaa3339fc4038690dce417292321a9234fb` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_a.jsonl.gz` | 911,730 | `ca6a49187d5cc23372bd90ef85e5146a81bcf05ee8c04a72f46a9f450059b6dd` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_a_gt.jsonl` | 6,747 | `0dac8c92266da0dcfc442603d69334b9f94f826c2a18028e703c5a180ed9ace9` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_a_gt.jsonl.gz` | 2,341 | `a558fcce0c3fcdd1b5b85692c803af6d4d8651ba87583f3a8935811b07616a33` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_b.jsonl` | 2,102,559 | `728e80ee397bdd1a09910944f0882eaa3339fc4038690dce417292321a9234fb` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_b.jsonl.gz` | 911,730 | `17aebefb15cda4afe02a9bdc1f6598de8908c78ba132158df5fc8abcb7dc7465` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_b_gt.jsonl` | 6,747 | `0dac8c92266da0dcfc442603d69334b9f94f826c2a18028e703c5a180ed9ace9` | decompressed content of `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha0p50_b_gt.jsonl.gz` | 2,341 | `8b657f2455ae936811b26521c3c8c15eee7155e5d6f5f04b5dd19dff2d6bc0d7` | byte-identical to `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel_e31_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_a.jsonl` | 8,150,339 | `a6eff36d3bf60ed95987081247e24becd6262f632c3a0ceae2950b97bb06cd8b` | decompressed content of `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_a.jsonl.gz` | 3,557,479 | `10dfbb84a51a97ff9b5b84aa603a12f45af416567de4e7153a7b33c6b58334ff` | byte-identical to `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_a_gt.jsonl` | 25,748 | `54a58fd8aa01ce162cd85d432add2783778da4655156c25a625501d4360bcc70` | decompressed content of `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_a_gt.jsonl.gz` | 7,988 | `b81d88059d667dec206ac0f83da6d1effd4dc0f7f050bf3a929ad0be43ef92fe` | byte-identical to `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_b.jsonl` | 8,150,339 | `a6eff36d3bf60ed95987081247e24becd6262f632c3a0ceae2950b97bb06cd8b` | decompressed content of `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_b.jsonl.gz` | 3,557,479 | `54d73c324919b00db3ad5dcf80ab45e38dbb09984e0a1ce98009338946528a39` | byte-identical to `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_b_gt.jsonl` | 25,748 | `54a58fd8aa01ce162cd85d432add2783778da4655156c25a625501d4360bcc70` | decompressed content of `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e32_prefix_b_gt.jsonl.gz` | 7,988 | `82daae57e95be3d9002dbb7f44fde115380258019cb50d790b6ab8bc6ca1c568` | byte-identical to `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel_e32_prefix_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p00.jsonl` | 525,107,028 | `1d568dc8ffd7c26291186f74eaf1ee392a0dc56578ee3f7bb037765ea7e42b7d` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p00.jsonl.gz` | 229,163,755 | `0289bb7872a177a169f224134f4a2af051ee0714694b0ed38b232f0f44b28d05` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p00_gt.jsonl` | 2,888,556 | `d58338d4a1b1828030859be80463e1053311a7ad949387f4bb370fafc75e407a` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p00_gt.jsonl.gz` | 725,717 | `7809ec000f5b991b6d0bd7d0a4b8cbd50b9a57e82b1ea93219aefa737dfae7af` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p25.jsonl` | 525,101,986 | `c9617dcf057d38c90db0fe0533eafbbedcc4bfedb9e00cf2eb0351b96f391eb3` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p25.jsonl.gz` | 229,322,930 | `bb9f7b35df3253bfe8f4fa8da10347ac599cf2bc2ce68f5eac6d6b9266e2eec9` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p25_gt.jsonl` | 2,897,753 | `a8b42036355002fea753163b901f34567cbaa533c36200560795c902e69bb0f1` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p25_gt.jsonl.gz` | 727,140 | `c98e98486d019aabefe00bc67cf39cb9619ab4a9d077594afa4c83167ecc090b` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p25_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p50.jsonl` | 525,073,191 | `0d8c123b67f3109060e55743c58d07847fed64234c2cc1c212ca53839b7ab57a` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p50.jsonl.gz` | 229,286,750 | `f0dd0a91cd382b7bcf44f80166455184bd657b2597772d7744dee61dcb4cdd2b` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p50_gt.jsonl` | 2,888,556 | `952554602d24fe183afa43a7db7e708e94d2c138837f7474f7230b0c7ca31f31` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p50_gt.jsonl.gz` | 727,002 | `9ca8b333e3e160b99258aa997b24a3b34fc13dd85d65b21a478eb19f511a8814` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p50_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p75.jsonl` | 525,061,324 | `be79af9195351ac65fe000f46a47189643d75fa44808fb9c2ed4a42e45904013` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p75.jsonl.gz` | 229,250,840 | `7b9c7ac89b94ee030b8baa426b977cd03824ee60836887a6efb5a6d1a1ab7b21` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p75_gt.jsonl` | 2,897,753 | `e7ff29808271e6a11e805eebbbbca1e3b0a998094ee1485e4ca0468e861925e4` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha0p75_gt.jsonl.gz` | 727,133 | `fae2d05f01db7f8864854b9f7fb1bd4433c14096820454e55abdad1084eeeb71` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha0p75_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha1p00.jsonl` | 525,021,249 | `3eca7fbbc5d9db494ab465c4ebaf5d7eed4421e4260bcbb802c6c956f0a319cf` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha1p00.jsonl.gz` | 229,230,969 | `ea4d3a2644ab2de228ccd9abe2ace15266969d6f54802e1a173442de9bbeae1a` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha1p00_gt.jsonl` | 2,888,556 | `4073504005bff66fbdfdd074c2762dcb781fdc44519acf3660185776cfa4e7cb` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_calibration_alpha1p00_gt.jsonl.gz` | 726,968 | `c72a26d8bfe7d9f09dd98f12feb600508c3b0ec523099c8698055655fa5de255` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel_e33_calibration_alpha1p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_a.jsonl` | 8,187,241 | `687e11dfe899bb2cd455382f3ea2fd4337749674e54674d3c01e840f2ad5c3b4` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_a.jsonl.gz` | 3,570,377 | `5a7745317b9477d3984546aec24c3a165ef91a2e0f255493cec51e84e3c62b90` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_a_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz` | 8,201 | `a8c346842b69233149dc33ca326fa8697c42c57f1590275947bd69c4c6488384` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_b.jsonl` | 8,187,241 | `687e11dfe899bb2cd455382f3ea2fd4337749674e54674d3c01e840f2ad5c3b4` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_b.jsonl.gz` | 3,570,377 | `936e4844491238eb4ab58daed0cb885f701e4f076b06bc1829e84817a230d6e4` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_b_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz` | 8,201 | `24c29e7dce0b15d3a9d906a08097c3dfd414266f0e2596609c983933a60926d9` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_a.jsonl` | 8,187,130 | `5a8167659527768754a8ce16cf3246f777b7ff31b969b9e96e7fbadf05d0e983` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_a.jsonl.gz` | 3,570,997 | `e05ed37bb50b04e227d029c02a7bd6e88e90ea654d8a61f834d22061c09eb69c` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_a_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz` | 8,220 | `061d52d960ecb55149d4a548dfa30f4be7a3479b8afea80cde581894b703a108` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_b.jsonl` | 8,187,130 | `5a8167659527768754a8ce16cf3246f777b7ff31b969b9e96e7fbadf05d0e983` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_b.jsonl.gz` | 3,570,997 | `14e7c996d8fae24c413e8d4ed97d1b264ae308c081c89cbecfc963daa8a257df` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_b_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz` | 8,220 | `d1b1a67e9390c70647c7ca1e3be6106c0c15c701ffdb356aaf0d01d33a1b8c88` | byte-identical to `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel_e33_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p00.jsonl` | 527,446,713 | `6fac80e16290b4d49b47809165c171f05ba74f25354af610c6a8b8c83049627c` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p00.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p00.jsonl.gz` | 229,982,782 | `bb51b4ff831d531c2a497ff75f2ef3ea1c2f8abe219965b6ff9b398f612ec700` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p00.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p00_gt.jsonl` | 2,888,556 | `d58338d4a1b1828030859be80463e1053311a7ad949387f4bb370fafc75e407a` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p00_gt.jsonl.gz` | 725,717 | `0270ee1d586813f7ae7c8ca0a5def9c5e3a280618e5094fe756debd9619a9a6b` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p25.jsonl` | 527,447,646 | `07e84c9985edf0086b4831bdc4fe464830fa1093be1e7d2c82522fad1b4ea590` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p25.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p25.jsonl.gz` | 230,286,733 | `7a88b1dee5bcd7cba463cf53e197899a8a191c4ba39f6d1e75b7af24fd8ecc39` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p25.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p25_gt.jsonl` | 2,897,753 | `a8b42036355002fea753163b901f34567cbaa533c36200560795c902e69bb0f1` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p25_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p25_gt.jsonl.gz` | 727,140 | `0967609779ff9d24310da651168ced7cbbc3cbfc270cd9b399cf9850281d431d` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p25_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p50.jsonl` | 527,435,342 | `6c25856689ed1c80d6e110110141d5c88dce9876bf6f50591c77fe17da0c5adc` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p50.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p50.jsonl.gz` | 230,285,603 | `29302a083be2cab28676d7df6115c12fa32b04c7cbc40441ec0373a1ad08fc74` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p50.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p50_gt.jsonl` | 2,888,556 | `952554602d24fe183afa43a7db7e708e94d2c138837f7474f7230b0c7ca31f31` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p50_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p50_gt.jsonl.gz` | 727,002 | `6f02758ff16be224536c1a386e90acc8238ca4d1f3ed13e52f4143a9ad22739c` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p50_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p75.jsonl` | 527,441,024 | `b35a8ec4af2255da9cac72886969e9ee6c9d43bb045875e4750c8c91c00eee1a` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p75.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p75.jsonl.gz` | 230,282,712 | `3cc9f96097cc9a1a1470d136c182bbbb9f2dd25b73ca4a06aff1367d2887baf6` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p75.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p75_gt.jsonl` | 2,897,753 | `e7ff29808271e6a11e805eebbbbca1e3b0a998094ee1485e4ca0468e861925e4` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p75_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha0p75_gt.jsonl.gz` | 727,133 | `a076e7ae21d48cab2c50d63aaf78b51359b0d5f9f2503c1d57459d52deddeb20` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha0p75_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha1p00.jsonl` | 527,428,995 | `3f35af497600416f693f32d20469f555b6361602b45918c429c59636f7a6ca76` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha1p00.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha1p00.jsonl.gz` | 230,278,722 | `280793b319f9c6f8d67c23a92ac260d83aa7c888b469c9eb1421f0b21d6398a4` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha1p00.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha1p00_gt.jsonl` | 2,888,556 | `4073504005bff66fbdfdd074c2762dcb781fdc44519acf3660185776cfa4e7cb` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha1p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_calibration_alpha1p00_gt.jsonl.gz` | 726,968 | `cdd67dbcb7b15b774b247e40aabaa1eb1e2e56532d133d9b72a87f5b458e6924` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel_e37_calibration_alpha1p00_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_a.jsonl` | 8,211,221 | `ae21163de663e0c9fab29f925e9972504572e87b2a7f3252417c44fb3be7ab6b` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_a.jsonl.gz` | 3,578,806 | `6bce6a58cc8a94efe80d26891c46a0b24dc08f61eee3cad92cf56c77ea495abe` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_a_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_a_gt.jsonl.gz` | 8,201 | `1ae06b5da4b73faa96f02eee16c29701ea47587dd5833b2259aa27973045c9ee` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_b.jsonl` | 8,211,221 | `ae21163de663e0c9fab29f925e9972504572e87b2a7f3252417c44fb3be7ab6b` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_b.jsonl.gz` | 3,578,806 | `15c1efabc70f72b942b056f5e805514ffd0136d710fe00e2bfdb349a3f3e546f` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_b_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p00_b_gt.jsonl.gz` | 8,201 | `ade56598542c7ff92d218726b306cc531db9015c527fd40d7a16377645b184ea` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_a.jsonl` | 8,211,168 | `9447df49e926a2646909d1a872b9fbfb7076967f047cf2fe5cfbfc91162d16ef` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_a.jsonl.gz` | 3,580,375 | `39c66c9e801f41c90643f646a50a6fb8b473d7a1939c02c06130933bc44838e5` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_a_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_a_gt.jsonl.gz` | 8,220 | `53d53ffc927d6817890d71f19a36a41fd8f598943d4a74cefb6a07e71ba7ac19` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_b.jsonl` | 8,211,168 | `9447df49e926a2646909d1a872b9fbfb7076967f047cf2fe5cfbfc91162d16ef` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_b.jsonl.gz` | 3,580,375 | `b3ccc2f99dbc330044be62b439d6bca9c8af642fd66fb7a9db0053207a82d7f9` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_b_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e37_canary_alpha0p50_b_gt.jsonl.gz` | 8,220 | `29dddbcbd51c6d898a96d91d8b9f57338fa4332bfe8a2438f7a0b7bc97cabc40` | byte-identical to `experiments/iter37_track_query_site_intervention/proof-canary/sentinel_e37_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_a.jsonl` | 8,222,485 | `d40e1006dcfea809b3b5e0d470de4d310e73b1f3d880455363649176f1e0a1a2` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_a.jsonl.gz` | 3,587,175 | `62391bcb55b4ef50ceb6fb1ac5aa2c516181844f98e608816bfbd5767b1ecf7f` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_a_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_a_gt.jsonl.gz` | 8,201 | `55b8e944a5e6e5aa0ed3f1446dec69698ea4bf580e7a30004f6183978399627c` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_b.jsonl` | 8,222,485 | `d40e1006dcfea809b3b5e0d470de4d310e73b1f3d880455363649176f1e0a1a2` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_b.jsonl.gz` | 3,587,175 | `5ee2eae0e37020b2daed66cd21150cec14cf45db515358a59e8e8eaf06dd3560` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_b_gt.jsonl` | 29,934 | `0404d4654fa7223bc0e8f700d3575975e98cd6cb74d91fb150c079a31f40893d` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p00_b_gt.jsonl.gz` | 8,201 | `7d779a08a99026581e9bc938c9f94fe91c0a639f905f21b3b83f367892aa9607` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p00_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_a.jsonl` | 8,222,434 | `791ebb1e0fbea448da4938386c10b44723984747b1a3e50b7840fa6fb369760e` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_a.jsonl.gz` | 3,588,607 | `960db908c25b039fdf26e961043caa22cd9a368d89cbdd9b8fd0ec0bb4046a56` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_a.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_a_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_a_gt.jsonl.gz` | 8,220 | `b4f86086e24434052582e0e53f3166983e9bd6286ad5e10867a38948dbad82f6` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_a_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_b.jsonl` | 8,222,434 | `791ebb1e0fbea448da4938386c10b44723984747b1a3e50b7840fa6fb369760e` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_b.jsonl.gz` | 3,588,607 | `98b687c9127d1031cbc1a08b06efd776595d9b615790a2489dbaf14d74e22486` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_b.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_b_gt.jsonl` | 29,934 | `4114c94c2a216986542152f8806849eaf143b69166a243e7b9082a47391c1864` | decompressed content of `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_e38_canary_alpha0p50_b_gt.jsonl.gz` | 8,220 | `bf72fad94707f0fa6f806b65f27b57b8388577831ba9d9dfe638c7e236d4041d` | byte-identical to `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel_e38_canary_alpha0p50_b_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_evalextract.jsonl` | 31,582,342 | `b2991c701c2f198d221766655be901ab6cbfbb157a10323102e5391f3778425f` | decompressed content of `experiments/iter19_diversity_head/proof-gate/sentinel_evalextract.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_evalextract.jsonl.gz` | 14,018,860 | `087146cb0b219cc64b1c5c58be35d372098a32e11aa399c8cafd80a6c13bba1f` | byte-identical to `experiments/iter19_diversity_head/proof-gate/sentinel_evalextract.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_extract.jsonl` | 242,441,033 | `978105d25e655c8bf6a86114ca11bf6d905af30f889dc75dc78c4e480ffac581` | decompressed content of `experiments/iter19_diversity_head/proof-extract/sentinel_extract.jsonl.gz.part-aa (+1 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_extract.jsonl.gz` | 107,494,025 | `4574079d6a7ade79e0e42fab6600b8f45a0086dd5cf5c806b91b649ae6d72d68` | byte-identical to `experiments/iter19_diversity_head/proof-extract/sentinel_extract.jsonl.gz.part-aa (+1 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_extract_gt.jsonl` | 1,035,984 | `1450db6dde55e8d46bf0f0bff683b4ba2641d1f25e4db161ea22c5df35765546` | decompressed content of `experiments/iter19_diversity_head/proof-extract/sentinel_extract_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_extract_gt.jsonl.gz` | 365,298 | `e04852522d8b67f09fafd6c6e13bcee6f8ad961fe710baba3a604606954540e7` | byte-identical to `experiments/iter19_diversity_head/proof-extract/sentinel_extract_gt.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_f14_off.jsonl` | 105,264,078 | `12d2009dfc0006760045c1a4ca94bbcec2c3959442630d1cd621ce5ce5cc5a53` | decompressed content of `experiments/full14_benchmark/proof/sentinel_f14_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_f14_union.jsonl` | 123,697,648 | `8db2c37287ee6c458de18bb3fde2dda46bb0cd23d70188fdbae4cb315f7a501b` | decompressed content of `experiments/full14_benchmark/proof/sentinel_f14_union.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i10_brakevade.jsonl` | 653,725 | `6c5aaa4449b1f31aa17ed08c5698fc5e8ad1a39540752832ccc74d24a81444bd` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i10_brakevade.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i10_off.jsonl` | 640,124 | `8bd5050b6aab3cf52123c677a9ee89f1df4bd8dd4ee09c2d5fd092a7f45b94c4` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i10_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i10_union.jsonl` | 666,847 | `fbcec5f7c8196da15ca66b98b7015d8f7ac7f02e6754904f7af115b1d29b05d1` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i10_union.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i11_evade.jsonl` | 533,716 | `05c5039cd1de0f35f7edac8975436c55394fbd16a6325adead44c00fb9dd3083` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i11_evade.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i11_off.jsonl` | 640,124 | `8bd5050b6aab3cf52123c677a9ee89f1df4bd8dd4ee09c2d5fd092a7f45b94c4` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i11_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i11_stop.jsonl` | 636,607 | `80d850f6a02b6d6713f2757960632a2935a0ae3f8707619276f78bee91930299` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i11_stop.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i15_released.jsonl` | 122,396,306 | `7c663d1054e9a0f525c597bcf196b77f68f94c4cf9e1692c1f0d3bf7a2868ffb` | decompressed content of `experiments/iter15_latch_release/proof/sentinel_i15_released.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i16_crawl.jsonl` | 113,379,562 | `000f754eab34ca39170ec402abc8eac49b4a68764988e1887640b2491d83af55` | decompressed content of `experiments/iter16_soft_stop/proof/sentinel_i16_crawl.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i16_crawl.jsonl.gz` | 48,522,219 | `e4b26c3bc4103a9126d9ea3849d71000364c8513d069bb0765061ece8f024785` | byte-identical to `experiments/iter16_soft_stop/proof/sentinel_i16_crawl.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i17_routed.jsonl` | 119,370,721 | `445dce39849740348540f3033856b3be485898aae8479227107def904880bd6a` | decompressed content of `experiments/iter17_threat_routing/proof/sentinel_i17_routed.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i17_routed.jsonl.gz` | 51,048,792 | `760e3c6d0f167a6454c0508138392451f1a07492cec934e6b8e10d2b709f5f57` | byte-identical to `experiments/iter17_threat_routing/proof/sentinel_i17_routed.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i3_always.jsonl` | 13,833,155 | `bdd2fd8f12837bf12d8983a1455ce9a8651c19dc22b04f33d9f01a4994cf3eda` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i3_always.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i3_off.jsonl` | 15,646,684 | `dfc0a30eb077642ab2116bcc7911c4615de4785942cc7b42dc87e91aa0786529` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i3_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i3_ttc.jsonl` | 14,303,746 | `327b0d69305e74f97e5c02776a091157be463fe11bf0db66d68eb1feeca98402` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i3_ttc.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i4_gated.jsonl` | 15,148,338 | `40cbb8bb1e8d0bfdd8ab2fa7d2658f4de23d861a641df28d077c84831fdf09ec` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i4_gated.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i4_off.jsonl` | 15,646,684 | `dfc0a30eb077642ab2116bcc7911c4615de4785942cc7b42dc87e91aa0786529` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i4_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i4_ttcold.jsonl` | 14,303,746 | `327b0d69305e74f97e5c02776a091157be463fe11bf0db66d68eb1feeca98402` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i4_ttcold.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i5_off.jsonl` | 15,646,684 | `dfc0a30eb077642ab2116bcc7911c4615de4785942cc7b42dc87e91aa0786529` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i5_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i5_tracked.jsonl` | 15,444,967 | `75852bf64fae720279aaf3a5a42f42b347ede28a20e10b6d2b538db7c9e29c38` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i5_tracked.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i6_cpa.jsonl` | 20,850,157 | `66d5c56579b40e9fb56768c5e735e2ea39b16ca77f19e12f2ebfedd342184420` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i6_cpa.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i6_off.jsonl` | 21,304,240 | `575b5b715a9d6d2678f3463a1b5803a01d05c77eec1c1193f63cc45740ff593e` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i6_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i7_cpa10.jsonl` | 2,811,614 | `e364db39baa7f14a0ae99ba0aaaeddc13915ac89cea633d397a117f7290af0c4` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i7_cpa10.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i7_cpa15.jsonl` | 16,129,101 | `b46fbc251f4012f0029802b2a2c2ee1b919416e644e54dc4bbe7643e08fbc6fa` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i7_cpa15.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i8_off.jsonl` | 21,304,240 | `575b5b715a9d6d2678f3463a1b5803a01d05c77eec1c1193f63cc45740ff593e` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i8_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i8_union.jsonl` | 21,007,950 | `b286b35e789508829cb4a80980a329508670c7e765a6a9a491fd8a1531d241dd` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i8_union.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i9_evade.jsonl` | 647,341 | `dfbb60b5d076156bca088acac8ef12fda088885aca33178ed05b9552a4926e9c` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i9_evade.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i9_off.jsonl` | 640,124 | `8bd5050b6aab3cf52123c677a9ee89f1df4bd8dd4ee09c2d5fd092a7f45b94c4` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i9_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_i9_union.jsonl` | 665,515 | `097d0865ac9b475fbb089a3f8fee1d5680bc26a55934f13821116b29fb3c0058` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_i9_union.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl` | 21,406,979 | `194abf54e70b56672d36c044376dc9ebc11a6a01c186d527aec2436be287ea46` | decompressed content of `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl.gz` | 7,938,947 | `8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d` | byte-identical to `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_p14_best.jsonl` | 407,410,302 | `25b15807a6ec3bf36b31567a81e9366f23a530cbc0abd9cfa4d9cca2ac17fe48` | decompressed content of `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa (+1 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_p14_best.jsonl.gz` | 174,081,388 | `c36eafd82796a8a09ccca721d5cc8daabb07eeb9c296b2038b29007e086cb2c6` | byte-identical to `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa (+1 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_p14_off.jsonl` | 446,282,620 | `1a3343930f5c994d2fd81666b4adf64e8b8b6cc0d2db980096de64c70dcdf322` | decompressed content of `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-aa (+2 parts)` |
| `/opt/sentinel-stack/UniAD/sentinel_p14_off.jsonl.gz` | 190,993,659 | `9c7ca88f47c4ed43f91cf3937c7baab08001fa67d3a8d9e984260157fa5ac175` | byte-identical to `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-aa (+2 parts, concatenated)` |
| `/opt/sentinel-stack/UniAD/sentinel_rss.jsonl` | 49,794,456 | `bedfa210828ca7be8e4da1219428c908ed779ae9a1986bf3546ca1f068b00d4c` | decompressed content of `experiments/iter13_rss_baseline/proof/sentinel_rss.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_v20_evade.jsonl` | 1,491,323 | `37da85d0755515eb5b2f26073e94c11d161d9dbc7b3164450147970eb8fac4a6` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_v20_evade.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_v20_off.jsonl` | 50,735,817 | `c356546c3cabc12633060758d64eb9b769610e9378793e52d14875414613445a` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_v20_off.jsonl.gz` |
| `/opt/sentinel-stack/UniAD/sentinel_v20_union.jsonl` | 51,235,790 | `8b2b74d5bdc88e43f393a70580966d84abdb4086db501106d49791ae2af01fa9` | decompressed content of `experiments/verification/evidence/jsonl/sentinel_v20_union.jsonl.gz` |

## Deleted: 42 `/var/log/sentinel-*.log` files (byte-identical committed copies)

| deleted box log | byte-identical committed copy |
|---|---|
| `/var/log/sentinel-ab.log` | `experiments/verification/evidence/logs/sentinel-ab.log` |
| `/var/log/sentinel-abl.log` | `experiments/verification/evidence/logs/sentinel-abl.log` |
| `/var/log/sentinel-bev-evalextract.log` | `experiments/iter21_bev_diversity_head/proof-gate/sentinel-bev-evalextract.log` |
| `/var/log/sentinel-bev-extract.log` | `experiments/iter21_bev_diversity_head/proof-extract/sentinel-bev-extract.log` |
| `/var/log/sentinel-bev-train.log` | `experiments/iter21_bev_diversity_head/proof-train/sentinel-bev-train.log` |
| `/var/log/sentinel-cand.log` | `experiments/iter12_plan_selection/proof/sentinel-cand.log` |
| `/var/log/sentinel-e22-extract.log` | `experiments/iter22_causal_planner_interpretability/proof-extract/sentinel-e22-extract.log` |
| `/var/log/sentinel-e23-canary.log` | `experiments/iter23_s0_hardened_causal_localization/proof-canary/sentinel-e23-canary.log` |
| `/var/log/sentinel-e23-extract.log` | `experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel-e23-extract.log` |
| `/var/log/sentinel-e29-canary.log` | `experiments/iter29_trainval_risk_support_atlas/proof-canary/sentinel-e29-canary.log` |
| `/var/log/sentinel-e29-extract.log` | `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel-e29-extract.log` |
| `/var/log/sentinel-e31-canary.log` | `experiments/iter31_full_trainval_bridge_intervention/proof-canary/sentinel-e31-canary.log` |
| `/var/log/sentinel-e32-prefix.log` | `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/sentinel-e32-prefix.log` |
| `/var/log/sentinel-e33-calibration.log` | `experiments/iter33_prefix_preserving_bridge_intervention/proof-calibration/sentinel-e33-calibration.log` |
| `/var/log/sentinel-e33-canary.log` | `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/sentinel-e33-canary.log` |
| `/var/log/sentinel-e37-calibration.log` | `experiments/iter37_track_query_site_intervention/proof-calibration/sentinel-e37-calibration.log` |
| `/var/log/sentinel-e38-canary.log` | `experiments/iter38_track_query_opposite_direction/proof-canary/sentinel-e38-canary.log` |
| `/var/log/sentinel-evalextract.log` | `experiments/iter19_diversity_head/proof-gate/sentinel-evalextract.log` |
| `/var/log/sentinel-extract.log` | `experiments/iter19_diversity_head/proof-extract/sentinel-extract.log` |
| `/var/log/sentinel-full14.log` | `experiments/full14_benchmark/proof/sentinel-full14.log` |
| `/var/log/sentinel-i10.log` | `experiments/verification/evidence/logs/sentinel-i10.log` |
| `/var/log/sentinel-i11.log` | `experiments/verification/evidence/logs/sentinel-i11.log` |
| `/var/log/sentinel-i3.log` | `experiments/verification/evidence/logs/sentinel-i3.log` |
| `/var/log/sentinel-i4.log` | `experiments/verification/evidence/logs/sentinel-i4.log` |
| `/var/log/sentinel-i5.log` | `experiments/verification/evidence/logs/sentinel-i5.log` |
| `/var/log/sentinel-i6.log` | `experiments/verification/evidence/logs/sentinel-i6.log` |
| `/var/log/sentinel-i7.log` | `experiments/verification/evidence/logs/sentinel-i7.log` |
| `/var/log/sentinel-i8.log` | `experiments/verification/evidence/logs/sentinel-i8.log` |
| `/var/log/sentinel-i9.log` | `experiments/verification/evidence/logs/sentinel-i9.log` |
| `/var/log/sentinel-iter15.log` | `experiments/iter15_latch_release/proof/sentinel-iter15.log` |
| `/var/log/sentinel-iter16.log` | `experiments/iter16_soft_stop/proof/sentinel-iter16.log` |
| `/var/log/sentinel-iter17.log` | `experiments/iter17_threat_routing/proof/sentinel-iter17.log` |
| `/var/log/sentinel-iter1b.log` | `experiments/verification/evidence/logs/sentinel-iter1b.log` |
| `/var/log/sentinel-iter42-trace.log` | `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel-iter42-trace.log` |
| `/var/log/sentinel-iter42-watch.log` | `experiments/iter42_exact_trace_replay_support/proof-trace/sentinel-iter42-watch.log` |
| `/var/log/sentinel-power14.log` | `experiments/full14_power/proof/sentinel-power14.log` |
| `/var/log/sentinel-power14b.log` | `experiments/full14_power/proof/sentinel-power14b-attempt3.log` |
| `/var/log/sentinel-power14c.log` | `experiments/full14_power/proof/sentinel-power14c.log` |
| `/var/log/sentinel-rss.log` | `experiments/iter13_rss_baseline/proof/sentinel-rss.log` |
| `/var/log/sentinel-train.log` | `experiments/iter19_diversity_head/proof-extract/sentinel-train.log` |
| `/var/log/sentinel-v20.log` | `experiments/verification/evidence/logs/sentinel-v20.log` |
| `/var/log/sentinel-vad20.log` | `experiments/vad_generalization/proof/sentinel-vad20.log` |

## Skipped (verification uncertain — left on the box)

| path | bytes | reason |
|---|---|---|
| `/opt/sentinel-stack/UniAD/sentinel_i7_off.jsonl` | 15,646,684 | no committed artifact with this basename |
| `/opt/sentinel-stack/UniAD/sentinel_risk.jsonl` | 32,864,030 | no committed artifact with this basename |
| `/var/log/sentinel-abllaunch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-brakefix.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-build.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-e37-canary.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i10launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i11launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i3launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i4launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i5launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i6launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i7launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i8launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-i9launch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-iter42-preflight.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-latch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-nuscenes-fetch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-recover.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-setup.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-shadow.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-smoke.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-trainfetch.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-ttc.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-vad20-attempt1.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-vad20-attempt2.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |
| `/var/log/sentinel-vitals.log` | — | no byte-identical committed copy (working/vitals/launch/fetch logs, or logs that diverged from the committed excerpt) |

Also intentionally untouched: `/opt/sentinel-stack/UniAD/sentinel_e*_context.json` (7 tiny
context files), all checkpoints, `neurad-studio`, `/tmp` (wiped on reboot anyway), Docker
images and build cache, and both dataset roots.

## Execution

Deletions ran once via `/tmp/cleanup_20260712.sh` on the box (generated from the verified
plan; `set -euo pipefail`, full `set -x` receipt at `/tmp/sentinel-cleanup-20260712.log`,
end marker `CLEANUP_20260712_DONE`). Box remained idle throughout; no Docker, model, or
GPU command ran.
