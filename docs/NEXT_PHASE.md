# Next phase — candidate lines after the power run

Written while the 20-run power measurement executes; nothing here presumes its outcome. Each line
is stated with the evidence that motivates it, the mechanism, the pre-registerable bar, and the
cost. Ordering is by expected knowledge-per-GPU-hour; the decision rules at the bottom say what
runs when.

## New frontier packet after these lines closed

After iterations 19–21 closed the tested frozen-planner candidate-head routes, the recommended
next line is causal localization rather than another decoder:
[`research/CAUSAL_PLANNER_INTERPRETABILITY.md`](research/CAUSAL_PLANNER_INTERPRETABILITY.md).
That file is a launch packet only. The official Stage 1 pre-registration lives at
[`../experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md`](../experiments/iter22_causal_planner_interpretability/HYPOTHESIS.md).
Its result is now published:
[`../experiments/iter22_causal_planner_interpretability/RESULT.md`](../experiments/iter22_causal_planner_interpretability/RESULT.md).
Stage 1 stopped at S0: the extraction/GT timestamp join failed on all 1,507 non-reset rows and
the frozen heldout split had 0 GT frames. It authorizes no iteration-12 scoring, probe claim,
intervention claim, or closed-loop evaluation.

The hardened successor was pre-registered as
[`../experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md`](../experiments/iter23_s0_hardened_causal_localization/HYPOTHESIS.md).
Its result is now published:
[`../experiments/iter23_s0_hardened_causal_localization/RESULT.md`](../experiments/iter23_s0_hardened_causal_localization/RESULT.md).

Iteration 23 repaired the iteration-22 artifact failure but did not reach the causal test. The
availability gate passed (66 eligible scenes; 39 fit, 13 calibration, 14 heldout; 554 heldout
keyframes), the two-run canary was deterministic, and full S0 integrity passed with 2,627/2,627
joined non-reset rows and zero error rows. The frozen count-floor gate then failed:
`collapse_positive` was 0 in every split, `eligible_intervention_frame` was 0, and heldout
`danger_positive` was 17 below the 30-frame floor. Iter23 authorizes no probe, activation
direction, iteration-12 scoring, or closed-loop evaluation. Any successor causal-localization
line requires a fresh pre-registration with a revised data-support plan.

The next line is now pre-registered as a fresh data-support prerequisite:
[`../experiments/iter24_risk_support_atlas/HYPOTHESIS.md`](../experiments/iter24_risk_support_atlas/HYPOTHESIS.md).
Iteration 24 is not a causal-intervention run. It freezes a known-data firewall that excludes
iter22/iter23 scenes, then asks whether fresh non-evaluation train scenes contain enough
low-diversity hazard frames and benign controls to justify a later causal-localization
pre-registration. A pass authorizes only that later pre-registration; it does not authorize probe
fitting, activation intervention, iteration-12 scoring, selector evaluation, or closed-loop work.

Its result is now published:
[`../experiments/iter24_risk_support_atlas/RESULT.md`](../experiments/iter24_risk_support_atlas/RESULT.md).
The known-data firewall passed, but the availability bar failed before model extraction:
0 eligible fresh scenes, 0 planned keyframes, and 0 heldout keyframes after 582 post-firewall
candidate scenes all missed the local six-camera file-existence check. Iteration 24 authorizes no
canary extraction, full extraction, label atlas, probe fitting, activation direction, iteration-12
scoring, selector evaluation, or closed-loop evaluation. Any successor needs a fresh
pre-registration and must name its data-staging plan before extraction.

The next line was pre-registered as a staged-data provenance gate:
[`../experiments/iter25_staged_data_inventory/HYPOTHESIS.md`](../experiments/iter25_staged_data_inventory/HYPOTHESIS.md).
Iteration 25 may inspect only a frozen list of local nuScenes roots and may produce only
token-free inventory/availability artifacts. It cannot download or copy data, run Docker/model
extraction, compute labels, fit probes, write activation directions, touch iteration-12 outcomes,
score selectors, or run closed loop. A pass authorizes only a separate fresh risk-support-atlas
pre-registration. The committed implementation surface is
[`../experiments/iter25_staged_data_inventory/inventory_roots.py`](../experiments/iter25_staged_data_inventory/inventory_roots.py);
its result is now published:
[`../experiments/iter25_staged_data_inventory/RESULT.md`](../experiments/iter25_staged_data_inventory/RESULT.md).
No root passed: `/datasets/nuscenes` existed but had 0 fresh eligible scenes and 0 keyframes after
the firewall, while the other four frozen roots were missing. It authorizes no data download/copy,
model extraction, label atlas, probe fitting, activation direction, iteration-12 scoring, selector
evaluation, or closed-loop work.

The next line was pre-registered as a read-only staging remedy gate:
[`../experiments/iter26_data_staging_remedy/HYPOTHESIS.md`](../experiments/iter26_data_staging_remedy/HYPOTHESIS.md).
Iteration 26 may inspect only source/capacity metadata and must move 0 data bytes. Its job is to
answer whether the missing nuScenes camera files require an official download/staging operation,
and if so to freeze the exact later operator action. It authorizes no download/copy, inventory
rerun, model extraction, label atlas, probe fitting, activation intervention, iteration-12 scoring,
selector evaluation, or closed-loop work. Its result is now published:
[`../experiments/iter26_data_staging_remedy/RESULT.md`](../experiments/iter26_data_staging_remedy/RESULT.md).
The answer is yes: the needed data is the official nuScenes v1.0 trainval sensor file blobs
(292.78 GB archive budget), but the current GPU disk has only 25.125 GB free against a frozen
365.975 GB minimum. Next action is storage provisioning plus a later staging pre-registration.

The storage step is now completed:
[`../experiments/iter27_storage_provisioning/RESULT.md`](../experiments/iter27_storage_provisioning/RESULT.md).
Iteration 27 created/attached/formatted/mounted one 1024 GB persistent disk at
`/datasets/nuscenes-full` and proved `1,026,108,792,832` bytes available. It moved 0 dataset bytes
and launched 0 Docker/model/NeuroNCAP runs. The next permitted action is a fresh data-staging
pre-registration for the official nuScenes v1.0 trainval sensor file blobs; iteration 27 itself
authorizes no download, extraction, inventory rerun, model extraction, label atlas, probe fitting,
activation intervention, iteration-12 scoring, selector evaluation, or closed-loop work.

That data-staging step is now completed:
[`../experiments/iter28_nuscenes_trainval_staging/RESULT.md`](../experiments/iter28_nuscenes_trainval_staging/RESULT.md).
Iteration 28 staged the official nuScenes v1.0 trainval metadata archive plus file-blob archives
parts 1-10 into `/datasets/nuscenes-full`, extracted them with a path-safety gate, and passed the
bounded token-free availability inventory: `532` fresh post-firewall train scenes, `21,461`
eligible keyframes, and `5,360` heldout keyframes. It authorizes no model extraction, label atlas,
probe fitting, activation intervention, iteration-12 scoring, selector evaluation, or closed-loop
work. The next action must be a fresh research pre-registration naming the committed iter28
availability manifest.

That fresh research gate is now pre-registered:
[`../experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md`](../experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md).
Iteration 29 is a full-trainval risk-support atlas, not a causal-intervention run. It may import
only the committed iter28 availability manifest, then proceed through S0a manifest import, S0b
two-run canary, S0c full extraction, and S1 support counts. It authorizes no probe fitting,
activation direction, intervention replay, iteration-12 scoring, selector evaluation, or
closed-loop work.

Its result is now published:
[`../experiments/iter29_trainval_risk_support_atlas/RESULT.md`](../experiments/iter29_trainval_risk_support_atlas/RESULT.md).
S0c full extraction integrity passed on all `21,461` imported keyframes: `21,461/21,461`
non-reset extraction rows joined GT one-to-one, with zero error row types and stable primary
tensor shapes/dtypes. The S1 low-diversity support gate passed with `eligible_lowdiv`
`127/108/158` and `benign_control` `5,084/2,344/2,245` across fit/calibration/heldout, and no
count-floor or distribution failures. The optional strict-collapse note failed
(`eligible_strict` `0/0/1`), so successor work may use only low-diversity language unless a new
strict-collapse pre-registration passes. Iter29 authorizes only a separate successor
pre-registration; it does not authorize probe fitting, activation direction, intervention replay,
iteration-12 scoring, selector evaluation, or closed-loop work.

The diagnostic localization gate is now published:
[`../experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`](../experiments/iter30_full_trainval_lowdiv_localization/RESULT.md).
Iteration 30 used only committed iteration-29 proof artifacts. It validated the iter29
hashes/counts, then showed that the concatenated `sdc_traj_query_last || sdc_track_query`
representation carries linearly decodable `eligible_lowdiv` information beyond the registered
metadata and ego-plan-kinematic controls. The primary internal probe passed on heldout scenes
(AUROC `0.950`, AP `0.615`, balanced accuracy `0.867`), while controls remained lower
(metadata AUROC `0.596`, ego-plan-kinematic AUROC `0.674`, shuffled-label internal AUROC
`0.531`), and scene-cluster robustness passed (AUROC p05 `0.922`). This is diagnostic only. It
authorizes only a separate causal-intervention pre-registration, not activation patching,
iteration-12 scoring, selector evaluation, GPU work, or closed-loop work.

That causal-intervention gate is now published:
[`../experiments/iter31_full_trainval_bridge_intervention/RESULT.md`](../experiments/iter31_full_trainval_bridge_intervention/RESULT.md).
Iteration 31 derived and committed a fit-only benign-centroid direction, then ran only the S0
canary. The canary repeated hashes passed for alpha `0.00` and `0.50`, but the alpha-zero baseline
reproduction bar failed against committed iteration-29 originals (`24` rows checked, `96`
comparison failures, max coordinate error `30.222413063049316` m). Iteration 31 is an
infrastructure null. It authorizes no calibration replay, heldout replay, iteration-12 scoring,
selector evaluation, closed-loop work, or safety claim.

The baseline-recovery prerequisite is now published:
[`../experiments/iter32_prefix_replay_baseline_recovery/RESULT.md`](../experiments/iter32_prefix_replay_baseline_recovery/RESULT.md).
Iteration 32 froze the exact 12 iteration-31 canary target rows and replayed each scene from
sample index `0` through its last target index, for `44` total prefix rows. The no-op prefix replay
restored iteration-29 model and GT parity exactly on the frozen target rows (`0.0` max model and
GT delta). This authorizes only a separate prefix-preserving bridge intervention
pre-registration. It does not authorize calibration, heldout, iteration-12 scoring, selector
evaluation, closed-loop work, or safety claims.

## Line 1 — a diversity-trained candidate head under the runtime selector

**Motivation (measured, twice):** iterations 12 and 14 established that frozen planners hold no
plan B precisely when it matters — UniAD's command-conditioned candidates collapse from 14 m of
benign diversity to 4 cm under threat (0/37 escapes); VAD's native modes retain only partial
diversity (21% escapes, below the 30% viability bar). The runtime selector mechanism is sound
(introspection sees the danger); the missing ingredient is a candidate set that stays diverse
under threat. To the verified corpus ([RELATED_WORK.md](RELATED_WORK.md)) no published system
trains a diversity-preserving candidate head for a *frozen* planner and selects among its outputs
with a label-free runtime risk score.

**Mechanism:** a small trajectory head (MLP/GRU over the frozen planner's BEV features, weights
of the planner untouched) trained on nuScenes train split with an explicit diversity objective
(winner-takes-all regression plus an inter-mode repulsion term), producing K candidates per
frame. At runtime, the union's risk score ranks the candidates; the committed-stop floor remains
(a candidate is executed only if its risk clears the plan's; otherwise the released stop fires).
Safe on false alarms by construction — the iteration-11 asymmetry is respected because every
candidate is trained on in-distribution driving.

**Pre-registerable bar (frozen before any training):** under-threat escape rate > 30% on the
iteration-12 frame corpus (the exact bar the planner's own candidates failed); then closed-loop:
frontal collision rate below the released-union's at equal selectivity (clean-scene cells within
noise of OFF), benchmark score not below the released-union's.

**Cost:** the first line requiring training — feature-extraction pipeline plus a small head;
single-L4 feasible; the largest engineering lift of the three.

> **Line 1 outcome (2026-07-06):** run in two registered offline variants. Iteration 19's
> planning-query head passed benign fidelity but failed at **0/37** feasible escapes, locating
> the collapse in the planner's internal planning representation. Iteration 21 then tested the
> surviving scene-level BEV variant; B0 passed (311/311 exact join, zero plan mismatches), but
> B1 failed at **0/37** feasible escapes, B2 validity was **23.1%**, B3 benign error was
> **1.449 m**, and B4 had no selectable escape. No closed-loop run launched from either
> hypothesis.
> [`../experiments/iter19_diversity_head/RESULT.md`](../experiments/iter19_diversity_head/RESULT.md) ·
> [`../experiments/iter21_bev_diversity_head/RESULT.md`](../experiments/iter21_bev_diversity_head/RESULT.md).

> **Line 2 outcome (2026-07-05):** run as iteration 17 — the pre-registered safety gate failed
> on one misrouted crossing (side 47% vs the 45% bar) and the released union stands, while the
> voided secondary criterion recorded the campaign's first deployment CI excluding zero vs the
> unmonitored planner (+0.226, [+0.004, +0.421]). All three named successor predicates were
> then **refuted offline** on the committed log (no-op; dead trade; non-separable) — the
> routing line closes for per-frame geometric predicates, and the deployment flip now routes
> through **tracking quality**, elevating Line 3 (motivated independently by iteration 14) to
> the front of the GPU queue alongside Line 1's offline stage.
> [`../experiments/iter17_threat_routing/RESULT.md`](../experiments/iter17_threat_routing/RESULT.md).

## Line 2 — threat-class routing (named by iteration 16's null)

**Motivation (measured):** the crawl null proved the stop is a *position guarantee* — but it
bought the campaign's highest safe-progress (2.544) and beat the released union on the deployment
metric with a CI excluding zero. The safety cost was concentrated where geometry says it must be:
the crossing (side) and in-path (stationary) classes. A router that stops for path-crossing and
in-path threats and crawls only where the tracked geometry proves no path overlap keeps the
position guarantee exactly where it is load-bearing.

**Pre-registerable bar:** safety cells within the released-union's (side ≤ 45%, stationary ≤
25%, NCAP within 0.15 of 3.09 — the iteration-16 bars, unchanged) AND safe-progress vs OFF
positive with CI excluding zero (the criterion every configuration so far has failed at
benchmark scope). Falsifier: if the router's "provably no overlap" predicate is wrong even
rarely, side collisions rise — same 45% kill-bar.

**Cost:** one patch, one 120-episode arm (~5 h); the cheapest line and a direct completion of
the deployment story if it lands.

## Line 3 — tracker-quality repair for VAD transfer

**Motivation (measured):** iteration 14 located the union's failed selectivity transfer in
tracking quality — VAD exposes no learned tracker, and nearest-neighbor IDs manufacture closing
speed. A lightweight ID stabilizer (gated Hungarian association with a constant-velocity filter)
between VAD's detections and the monitor would test the sharpest form of the transfer claim:
*monitor portability is a tracker-quality requirement, quantifiable in ID-switch rate*.

**Pre-registerable bar:** VAD+union selectivity restored (clean-scene ego distance within 20% of
VAD-OFF) while keeping the transfer's safety wins (stationary and side at 0% held); report the
tracker's ID-switch rate alongside, giving the field a concrete portability threshold.

**Cost:** moderate — one association module (pure geometry, unit-testable offline against the
committed VAD decision logs before any GPU time), one 120-episode VAD arm.

> **Line 3 outcome (2026-07-06):** run as iteration 20's offline stage only. The committed
> tracker defaults removed **0/47** raw TTC fires, retained only **4/6** side firing episodes
> (bar: 90%), and increased frontal firing frames **79 -> 90**. The pre-registered gate failed;
> no VAD closed-loop run launched. The broad tracking-quality constraint remains, but this
> simple association + smoothing bridge is closed.
> [`../experiments/iter20_vad_tracker_portability/RESULT.md`](../experiments/iter20_vad_tracker_portability/RESULT.md).

## The manuscript

Runs in parallel with whichever line is on the GPU: the campaign is consolidated in
[REPORT.md](REPORT.md) and every number is committed; the manuscript is a writing task, not a
measurement task. It waits only for the power run's final numbers so results are stated once.

## Decision rules

1. **Manuscript drafting starts when the power run's RESULT is committed** — no line blocks it.
2. **Line 2 is closed by iteration 17**; its safety gate failed, and the released union stands.
3. **Line 1 is closed by offline gates**; its closed-loop evaluation never runs because neither
   the planning-query nor the BEV-conditioned variant met the escape/feasibility bars.
4. **Line 3 is closed by iteration 20**; the registered tracker bridge failed before GPU time.
5. Iteration 24 is closed as an availability-null before model extraction.
6. Iteration 22 is closed as an S0 data-null.
7. Iteration 23 is closed as a count-floor data-null after S0 pass. It authorizes no probe,
   activation direction, iteration-12 scoring, or closed-loop run. Any next causal-localization
   line needs a fresh HYPOTHESIS.md before data.
8. Iteration 25 is closed as a staged-data inventory infrastructure-null.
9. Iteration 26 is closed as a data-staging capacity-null.
10. Iteration 27 is closed as a storage-provisioning pass. The 1 TB persistent disk is mounted at
    `/datasets/nuscenes-full` with `1,026,108,792,832` bytes available, and 0 dataset bytes moved.
11. Iteration 28 is closed as a staging/availability pass. It staged and extracted the official
    nuScenes trainval metadata plus ten sensor-blob archives into `/datasets/nuscenes-full`, then
    passed the bounded availability inventory with `532` fresh post-firewall scenes and `21,461`
    eligible keyframes. It does not authorize model extraction, label atlas, probe fitting,
    activation intervention, iteration-12 scoring, selector evaluation, or closed-loop work.
    The next action must be a fresh research pre-registration naming the committed iter28
    availability manifest.
12. Iteration 29 is closed as a full-trainval low-diversity support pass. S0c full extraction
    passed with `21,461/21,461` joined non-reset rows and zero error row types; S1 passed all
    low-diversity hazard/control count and distribution bars. The optional strict-collapse note
    failed, so no successor may call this support strict collapse without a new pre-registration.
    Iter29 authorizes only a separate successor pre-registration, not probe fitting, activation
    intervention, iteration-12 scoring, selector evaluation, or closed-loop work.
13. Iteration 30 is closed as a diagnostic localization pass on committed iter29 proof artifacts
    only. S0/S1/S2 passed: iter29 hashes/counts reproduced, the internal bridge tensor probe
    exceeded the frozen bars and controls, and scene-cluster bootstrap robustness passed. This
    authorizes only a separate causal-intervention pre-registration; it does not authorize
    activation patching, iteration-12 scoring, selector evaluation, GPU work, or closed-loop work.
14. Iteration 31 is closed as an S0 infrastructure-null. Alpha-zero baseline reproduction failed
    against iteration-29 originals, so calibration, heldout, iteration-12 scoring, selector
    evaluation, closed-loop work, and safety claims are not authorized.
15. Iteration 32 is closed as a prefix-replay baseline-recovery pass. The no-op replay restored
    exact iteration-29 parity for the frozen 12 iter31 canary target rows under a 44-row
    scene-prefix replay. It authorizes only a fresh prefix-preserving bridge intervention
    pre-registration; it authorizes no direct intervention, calibration, heldout, iteration-12,
    selector, closed-loop, or safety claim.
16. Iteration 33 is closed as a prefix-preserving bridge-intervention calibration null. S0 passed
    and the full calibration grid completed exact row counts for every frozen alpha, but no
    nonzero alpha passed S1. The strongest cell, alpha `1.00`, reached only `0.0308 m` eligible
    median endpoint-spread delta and `0.1296` fraction above `0.25 m`, far below the frozen bars.
    Iter33 authorizes no heldout replay, iteration-12 scoring, selector evaluation, closed-loop
    work, deployment language, or safety claim. Any successor needs a fresh pre-registration with
    a different intervention hypothesis or a narrower post-result audit claim.
17. Iteration 34 is closed as a post-result direction-specificity audit null. S0 artifact and row
    integrity passed, but S1 failed: only `74/108` eligible rows had nonnegative endpoint-spread
    slope across the frozen alpha grid (`0.685185` vs the `0.70` bar). S2 was not evaluated. The
    same global bridge-centroid direction is not authorized for scale-only successor work from
    these artifacts. Any successor needs a fresh pre-registration that changes the intervention
    family, target site, row conditioning, or claim.
18. Iteration 35 is closed as a post-result response-heterogeneity audit null. S0 passed and S1
    showed measurable heterogeneity (`42/108` eligible rows with slope `>=0.05 m/alpha`, `34/108`
    with slope `<0`, IQR `0.126519 m/alpha`), but S2 failed because no frozen baseline-geometry
    stratum passed all actionability bars. It authorizes no GPU/gcloud work, heldout replay,
    iteration-12 scoring, selector evaluation, closed-loop work, deployment language, safety
    claim, same-direction scale-only successor, or row-conditioned successor from these artifacts.
19. Iteration 36 is closed as an offline bridge-site decomposition diagnostic pass. S0 artifact
    and count integrity passed; S1 reproduced the full-bridge diagnostic signal (`all_bridge`
    AUROC `0.950224`, AP `0.614943`, balanced accuracy `0.867444`); S2 passed for five frozen
    non-global sites: `traj_slot_0`, `traj_slot_2`, `traj_slot_3`, `traj_slot_4`, and
    `track_query`. The strongest site was `track_query` (AUROC `0.970531`, AP `0.726416`,
    bootstrap AUROC p05 `0.950589`). This authorizes only a separate site-specific intervention
    pre-registration. It authorizes no GPU/gcloud work, heldout intervention replay,
    iteration-12 scoring, selector evaluation, closed-loop work, deployment language, safety
    claim, direction, or alpha.
20. Iteration 37 is closed as a prefix-preserving `track_query`-only site intervention
    calibration null. Its fit-only `sdc_track_query` direction, replay tooling, analyzer, and S0
    canary proof were committed; S0 passed with alpha-zero parity restored, `24/24` nonzero target
    observations changing `track_query`, and `24/24` preserving `sdc_traj_query_last`. The full
    calibration grid then passed row integrity for every frozen alpha, but no nonzero alpha was
    selectable. Alpha `1.00` had eligible median endpoint-spread delta `-0.041940 m`, fraction
    `>0.25 m` `0.074074`, and median best-candidate-gap delta `-0.001315`, below the frozen bars.
    Iter37 authorizes no heldout replay, iteration-12 scoring, selector evaluation, closed-loop
    work, deployment language, or safety claim.
21. Iteration 38 is pre-registered as a post-iteration-37 opposite-direction `track_query` gate.
    It may test only the exact sign reversal of the iter37 fit-only `sdc_track_query` centroid
    direction, with the same prefix counts and S0/S1/S2/S3 bars. Its offline direction builder,
    UniAD patch, feeder, run scripts, analyzer, tests, and proof-direction artifact are committed.
    The direction has `256` features, `5,211` fit rows, direction SHA
    `251323cf6ba7361da5aa0a084a6ae5ad5083989df75e10d16f352da845e2983d`, and exact
    negative-of-iteration-37 sign equivalence (`max_abs_direction_sum=0.0`, cosine `-1.0`). No
    GPU/gcloud command, model replay, calibration result, heldout replay, iteration-12 scoring,
    selector evaluation, closed-loop work, deployment language, or safety claim exists yet. The
    next authorized action is S0 canary replay for the committed
    [`HYPOTHESIS.md`](../experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md).
