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
    negative-of-iteration-37 sign equivalence (`max_abs_direction_sum=0.0`, cosine `-1.0`). S0
    canary passed: alpha-zero parity restored with `0.0` max coordinate error, alpha `0.50`
    changed `track_query` on `24/24` target rows, and `sdc_traj_query_last` stayed unchanged on
    `24/24`. Calibration is authorized but not launched. No calibration result, heldout replay,
    iteration-12 scoring, selector evaluation, closed-loop work, deployment language, or safety
    claim exists yet. Before spending the next GPU window on calibration, compare its value
    against a fresh external-validity falsification pre-registration for the committed
    [`HYPOTHESIS.md`](../experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md).

Strategic rule after iteration 38 S0: if the choice is between a stronger-looking mechanism story
and a more defensible scientific claim, choose the defensible claim. The next fresh
pre-registration should prioritize hostile external-validity pressure unless there is a specific
reason calibration is more informative: independent planner transfer, unseen scenario families,
sensor degradation, adversarial perturbations, calibration stability, intervention latency,
intervention cost, and deployment trade-offs.

22. Iteration 39 is closed as that hostile external-validity gate. It published a claim ledger and
    active-document overclaim audit, passed S0/S1/S2, found three S3 wording problems, and narrowed
    them in the same state. The active docs now pass the same overclaim scanner. The default next
    scientific line is an external-validity falsifier, preferably an offline latency/intervention-
    cost audit over committed decision logs or a sensor/input-degradation stress gate for the
    released union. Iteration-38 calibration remains allowed by its own HYPOTHESIS, but it is not
    the primary direction unless explicitly justified against those falsifiers.
23. Iteration 40 is closed as an offline timing/intervention-cost audit pass. It quantified the
    full14/power simulation intervention envelope (`1,205` brake frames over `10.79 km`,
    `230/400` intervention episodes) and reconstructable lead-time support (`61` measured
    episodes, median `1.30 s`) while preserving the boundaries: no wall-clock latency,
    production-cost, passenger-comfort, deployment-readiness, or new safety claim. This motivated
    the sensor/input-degradation prerequisite in iteration 41; after iteration 41's infrastructure
    null, that line requires replay-support repair before any robustness claim.
24. Iteration 41 is closed as a monitor-input degradation infrastructure null. The frozen paths,
    H-P0 status, iteration-40 verdict, and decision-log counts were intact, but exact timestamp
    lookup into committed `p14-best` ego poses missed `1,388/6,474` timestamped monitor frames
    across `400/400` episodes. The registered world-frame replay was not runnable, so all
    perturbation bars were skipped. No object-stream, camera, degraded-sensor, GPU, closed-loop,
    deployment, or safety robustness claim is authorized.
25. A successor on this line must be a fresh replay-support pre-registration before any result:
    log exact `ego2world` transforms with monitor rows, or pre-register a pose-interpolation/snap
    rule and first prove vanilla replay. Otherwise choose another hostile external-validity
    falsifier such as adversarial perturbations, independent planner transfer, unseen scenario
    families, calibration stability, or deployment trade-offs.
26. Iteration 42 is now pre-registered as that replay-support remedy. It freezes a best-arm-only
    full14/power trace capture with exact `ego2world` per monitor frame and exact offline replay
    identity as the only success condition. It authorizes no perturbation, no robustness claim, no
    selector, no deployment language, and no safety claim.

## 2026-07-13 update after HUGSIM transfer closure

Iterations 48 and 49 closed the HUGSIM transfer question for the released union. The answer is
`TRANSFER_NULL` in both the easy+medium and hard/extreme regimes. Iteration 50 ruled out the
simple opportunity-scarcity explanation: NeuroNCAP benefit concentrates where the OFF arm
collides, but HUGSIM had abundant opportunity and the benefit did not port. Iteration 51 then
classified the committed HUGSIM transfer pairs offline and found a mixed taxonomy: only `6/91`
OFF-opportunity pairs converted from collision to no collision, `85/104` pairs remained
collision-persistent, and no combined category crossed the frozen 40% dominance bar.
Iteration 52 then tightened the timing side of that mechanism story: among `92` ON-collision
episodes, `57` were absent/post-collision braking and `35` had pre-collision braking; all `22`
no-brake ON-collision cases had zero frozen TTC/CPA surface-proxy rows, but `26` long-lead
brake cases still collided. Iteration 53 then reconstructed the actual first-fire side of the
released OR predicate. Among the same `92` ON-collision episodes, first-fire channels split
TTC-only `36`, CPA-only `33`, no-fire `22`, and both `1`; among the `35` pre-collision-fire
ON-collision episodes the split was CPA-only `19` / TTC-only `16`. The stricter simultaneous
TTC+CPA proxy from iteration 52 was too strict to describe the actual OR predicate, but
reconstructing the OR showed that the persistent failures are not one bad union branch.
Iteration 54 then audited provenance support. The monitor side is reconstructable from committed
decision logs: first-fire argmins resolve to unique TTC objects `40` times, unique CPA objects
`36` times, one both-distinct case, and `27` no-fire episodes, with zero reconstruction failures.
But HUGSIM collision actor identity is not logged in any of the `104` committed eval artifacts
(`0/104` actor-supported; top-level eval keys are scalar metrics plus `details`, and detail keys
are `c`, `dac`, `nc`, `pdms`, `ttc`). The result is `PROVENANCE_SUPPORT_NULL`.
Iteration 55 then performed the missing source-map prerequisite without running HUGSIM: the
frozen HUGSIM checkout at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e` matched exactly, a
source-only scanner covered 153 source-like files, and the result was
`COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE`. The source-level candidates are
`sim/utils/score_calculator.py` and `closed_loop.py`; this makes a future no-metric-change
provenance logging patch designable, but not yet implemented or run.
Iteration 56 then attempted that first patch-design gate. The draft patch applied to a clean
temporary frozen checkout and `sim/utils/score_calculator.py` compiled, but the pre-registered
static guard rejected the added `if score_nc == 0.0:` branch as metric/control-sensitive. The
result is `INSTRUMENTATION_PATCH_DESIGN_NULL`. The draft patch is not authorized for a run.
Iteration 57 then bound the same patch by SHA256
`49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd` and refined the guard to
reject metric/control assignments while permitting read-only score comparisons. The result is
`PATCH_GUARD_REFINEMENT_COMPLETE`: the byte-identical patch applies, compiles, stays within the
allowed changed file, keeps provenance out of scalar `score_list` rows, and is statically
supported as additive by source diff inspection.
Iteration 58 then performed the required execution canary under a fresh pre-registration: the
byte-bound patch was applied to the frozen HUGSIM stack and exactly two episodes were run
(`scene-0013-hard-00` OFF r1 then ON r1). The result is `PROVENANCE_CANARY_COMPLETE`: both
episodes completed, both had `nc_min = 0.0`, both emitted top-level `collision_provenance`
lists (counts `11` and `13`), scalar top-level metrics remained present, `details` rows stayed
scalar-only, and the ON episode carried the released-union decision log.
Iteration 59 then used that instrumentation in a bounded eight-episode ON-only actor-match
support audit. The result is `ACTOR_MATCH_AUDIT_COMPLETE`: all eight episodes completed, three
same-run foreground comparisons were classifiable, and all three were `actor_mismatch` by the
frozen bridge (`15.43 m`, `21.99 m`, `37.04 m`). The other five rows were two no-fire collision
rows, two post-collision-fire rows, and one background-only collision row.
Iteration 60 then stress-tested only those three classifiable rows under the frozen bridge
sensitivity grid: first-fire vs propagated position, two axis orders, and four sign combinations
per row. The result is `BRIDGE_AMBIGUOUS_NULL`: no row became `bridge_match_possible`, but
`ttc_extreme_b` became `bridge_ambiguous_possible` at `5.6649 m`, while the other two rows
remained robust mismatches.

The default next scientific line is therefore not an expanded-N transfer run and not retuning the
released union. After iteration 60, the actor-match audit points to a hazard-surface
misalignment or coordinate/contact ambiguity in the classifiable rows and to
no-fire/post-fire/background-only failure modes in the rest. Any successor should be a fresh
mechanism-cause pre-registration that explains those categories, not threshold tuning. A strong
successor should distinguish among:

1. hazard surface: whether the monitor is braking for the wrong detected object or wrong path
   crossing geometry;
2. planner/path geometry: whether HUGSIM collisions arise from executed-plan modes the stop rule
   cannot change;
3. metric composition: whether HD-Score changes are dominated by non-collision terms even when a
   collision is converted;
4. AttackPlanner structure: why hard/extreme adversarial scenes have many absent/post cases
   while a substantial pre-collision-brake subset still persists.

Pure "brake earlier" is no longer the default next hypothesis because iteration 52 found
`35/92` ON-collision cases with pre-collision braking, including `26` long-lead cases. Any timing
successor must specifically explain why those pre-collision-brake cases still collide, not merely
move the first brake earlier. Pure "fix the TTC branch" or "fix the CPA branch" is also no longer
the default next hypothesis because iteration 53 found the pre-collision-fire failures split
across both channels. A pure offline "which actor did we hit?" audit is also not authorized from
the current proof, because iteration 54 found that collision actor identity is not present in the
committed eval artifacts. Iteration 55 removes the source-location blocker only; it does not
retroactively add actor identity to any committed HUGSIM result. Iteration 56 did not remove the
patch-authorization blocker because the static guard returned null. Iteration 57 removed only that
static guard blocker. Iteration 58 removed only the execution blocker for a tiny canary; it does
not prove actor match, HD-Score invariance, or transfer value. Iteration 59 supplies a bounded
actor-match mechanism result only; it does not prove a population mismatch rate, repair, or
deployment/safety claim. Iteration 60 narrows that result: no bounded bridge variant produces a
match, but one classifiable row is ambiguous, so robust all-row mismatch is also not authorized.

Any such line requires a fresh `HYPOTHESIS.md`. Until then, no new HUGSIM transfer, safety,
robustness, deployment, benchmark-ranking, or retuning claim is authorized.
