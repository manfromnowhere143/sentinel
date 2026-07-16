# Bench2Drive-Robust preflight: from benchmark patch to Deployment Assurance Runtime

**Reconnaissance date:** 2026-07-16
**Decision:** `FEASIBLE_WITH_BLOCKING_GATES`
**Execution authority:** none. This document authorizes no clone, download, environment build,
checkpoint load, CARLA launch, GPU run, benchmark claim, safety claim, or commercial use.

Bench2Drive-Robust is unusually well aligned with Sentinel's next product question: what happens
when a closed-loop driving stack receives stale cameras, biased ego state, or late commands? The
right move is not to turn the released NeuroNCAP patch into another benchmark-specific patch. It
is to extract a benchmark-independent **Sentinel Deployment Assurance Runtime** and use a legally
cleared, pinned Bench2Drive-Robust composition as one external stress laboratory.

That opportunity is real, but the launch is red today. The upstream release is one untagged
commit, is not standalone, contains protocol-to-implementation discrepancies, and carries a
license conflict that blocks both derivative integration and commercial dependency until resolved
in writing. The current one-L4 box is suitable for code-only and narrow smoke work, not a full
robustness campaign.

## 1. Frozen source composition

These are the only upstream identities considered by this preflight. Branch names such as `main`
or `uniad/vad` are discovery labels, not reproducibility pins.

| Component | Frozen identity | What the pin establishes |
|---|---|---|
| Bench2Drive-Robust | [`ae1b5867324710bf0574cba797062280d9d97105`](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/tree/ae1b5867324710bf0574cba797062280d9d97105) | Entire public history at recon time: one untagged commit dated 2026-05-20; perturbation patch, scripts, and documentation |
| Bench2Drive base | [`2645714eb1f3a100217928dd113093cae0779f36`](https://github.com/Thinklab-SJTU/Bench2Drive/tree/2645714eb1f3a100217928dd113093cae0779f36) | Base evaluator, routes/protocol surface, and CARLA integration that the Robust repository expects but does not contain in full |
| Bench2DriveZoo | [`498c1f799dd90faf840dedb3f0d3234ec2e567db`](https://github.com/Thinklab-SJTU/Bench2DriveZoo/tree/498c1f799dd90faf840dedb3f0d3234ec2e567db) | UniAD/VAD wrappers and model-side integration seams |
| Model repository | [`rethinklab/Bench2DriveZoo@140aea58c02185e787c3df39d7ad79e910967b8b`](https://huggingface.co/rethinklab/Bench2DriveZoo/tree/140aea58c02185e787c3df39d7ad79e910967b8b) | Exact checkpoint-repository revision; the card labels the repository Apache-2.0, which conflicts with the GitHub license files discussed below |
| Simulator | [CARLA 0.9.15](https://github.com/carla-simulator/carla/releases/tag/0.9.15) | Version named by the Robust setup and inherited Bench2Drive protocol |

The checkpoint metadata observed without downloading payloads is:

| Artifact | Exact byte size | Repository object ID |
|---|---:|---|
| `uniad_base_b2d.pth` | 996,840,308 | `af6b9e647912c184728a4f0d1b95a9d235cd708f` |
| `vad_b2d_base.pth` | 699,792,372 | `4f1b3f9a81495ad1713109c12d2f2bbc454e9df0` |
| `resnet50-19c8e357.pth` | 102,502,400 | `f32b13a276cc06b272093e2fd3c89381b6c54e2c` |

Those 40-character values are repository object identifiers from remote metadata, not independently
computed payload digests. A future acquisition manifest must record the remote ID, byte size, and a
locally computed SHA-256 after an authorized download; it must not relabel these IDs as verified
content hashes.

Remote `HEAD` metadata for the two CARLA objects was:

| Artifact | Compressed size | ETag |
|---|---:|---|
| [`CARLA_0.9.15.tar.gz`](https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/CARLA_0.9.15.tar.gz) | 7.81 GiB | `e7e759a251bbd7c62bcd38b789ad8499-84` |
| [`AdditionalMaps_0.9.15.tar.gz`](https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/AdditionalMaps_0.9.15.tar.gz) | 6.87 GiB | `25fb0bda594ad2fef5431a056c9ee990-880` |

The hyphenated multipart ETags are transport metadata, not SHA-256 content proofs. An authorized
acquisition must compute local hashes and preserve both the original archive and extraction
manifest. No training dataset is needed for the proposed first feasibility lane: it uses frozen
pretrained checkpoints and closed-loop evaluation assets only.

### Composition rule

The Robust snapshot is a patch surface, not a complete runnable bill of materials. It omits the
route XML corpus and the UniAD/VAD team agents, and its README instructs users to replace four
files in a Bench2Drive installation. A reproducible environment therefore needs one immutable
composition manifest containing all three Git commits, the Hugging Face revision and artifact
digests, CARLA archive digests, Python/CUDA/container identities, route-list digest, checkpoint
configuration digest, and every local compatibility patch. “Robust HEAD + latest base” is not an
acceptable experiment identity.

## 2. License and commercial-use stop gate

The following pinned GitHub license files say that all assets and code are licensed under
CC-BY-NC-ND 4.0:

- [Bench2Drive-Robust license](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/blob/ae1b5867324710bf0574cba797062280d9d97105/LICENSE)
- [Bench2Drive license](https://github.com/Thinklab-SJTU/Bench2Drive/blob/2645714eb1f3a100217928dd113093cae0779f36/LICENSE)
- [Bench2DriveZoo license](https://github.com/Thinklab-SJTU/Bench2DriveZoo/blob/498c1f799dd90faf840dedb3f0d3234ec2e567db/LICENSE)

That conflicts with Apache-2.0 language in the original
[Bench2Drive paper/release record](https://arxiv.org/abs/2406.03877) and the
[Hugging Face checkpoint card](https://huggingface.co/rethinklab/Bench2DriveZoo). The conflict is
material: `NC` is incompatible with the intended commercial path, and `ND` can prohibit the
modified/combined use that the Robust README itself instructs. This preflight is not legal advice;
it is a fail-closed engineering gate.

Before any integration, modification, publication, customer demonstration, or commercial reliance,
one of these routes must close:

1. Obtain written permission from the relevant rightsholders covering the exact code, routes,
   assets, checkpoints, derivative/combined execution, publication, and commercial use, then pass
   counsel review; or
2. Keep the upstream stack entirely external and noncommercial under counsel-approved terms, while
   implementing an independently authored, clean-room MIT-licensed CARLA fault harness from public
   behavioral specifications. Preserve provenance showing that no CC-BY-NC-ND implementation was
   copied or adapted.

Until then, Sentinel must not vendor the three repositories, copy their perturbation code, ship
their checkpoints/assets, or make any commercial feature depend on them. The product is Sentinel's
owned assurance runtime; Bench2Drive-Robust is at most an external research evaluation surface.

## 3. Protocol audit: upstream claims are hypotheses until tested

The public release is valuable reconnaissance, but it is not a drop-in ground-truth protocol. A
read-only source audit found the following defects or ambiguities at the frozen pin.

| Finding | Why it changes the experiment | Required closure |
|---|---|---|
| Burst duration is sampled from `2..BURST_MAX_TICKS`, rather than held at the advertised fixed 20- or 60-tick exposure. | “Burst 20” and “Burst 60” do not mean every event lasts 20 or 60 ticks; dose varies within condition. | Define and test fixed-duration and randomized-duration protocols separately; log realized stale-frame age every tick. |
| Occlusion multiplies both mask height and width by the configured ratio. | Ratios `0.5` and `0.8` cover 25% and 64% of image area, respectively, not 50% and 80%. | Name the parameter `side_ratio`, report realized area fraction, or construct a mask with the requested area fraction. |
| Stochastic processors are not seeded from a stable route-derived identity. | A global/config seed does not guarantee identical faults for a route across process scheduling, restarts, models, or arms. | Derive independent RNG streams from a canonical route ID, condition, severity, replicate, and sensor; commit the derivation and fixtures. |
| Multiplicative speed noise is not clipped to a physically valid domain. | Gaussian draws can produce a negative reported speed, creating an unbounded/unphysical fault class rather than the named under-estimation condition. | Freeze the physical domain and clipping/censoring rule; report clipped-draw rate. |
| The latency path coasts during warm-up and reduces policy update cadence; it is not a transparent FIFO of every generated command with measured command age. | It confounds action age with missing inference updates and a special zero-control startup policy. The README's FIFO description is therefore insufficient. | Use a timestamped command ledger and true FIFO; log observation time, inference start/end, command-ready time, apply time, age, queue depth, and fallback reason. |
| The four-file replacement instructions omit the evaluator-side `SIM_RATE` difference. | A nominally identical setup can convert milliseconds to ticks differently and silently change the fault dose. | Include evaluator/runtime-rate code in the composition manifest and assert the observed simulator/control cadence before every route. |
| The subset merge utility retains a denominator of 220 routes. | Dev10/subset scores are numerically diluted and cannot be reported as official Bench2Drive metrics. | Use route-level records and a subset-aware analyzer; label all Dev10 results `NONOFFICIAL_FEASIBILITY`. |
| Robust omits route XML and UniAD/VAD team agents. | The single Robust Git SHA cannot reconstruct an evaluation. | Freeze the tri-repo composition, route list, and checkpoint config as one signed manifest. |
| No perturbation unit/integration tests ship. | Syntax validity says nothing about realized fault dose, arm equivalence, seeding, or queue semantics. | Add deterministic fixtures for every perturbation and paired replay tests before CARLA. |

The relevant primary source surfaces are the pinned
[Robust README](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/blob/ae1b5867324710bf0574cba797062280d9d97105/README.md),
[sensor perturbation package](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/tree/ae1b5867324710bf0574cba797062280d9d97105/leaderboard/leaderboard/envs/sensor_interface_with_perturbations),
[action-latency wrapper](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/blob/ae1b5867324710bf0574cba797062280d9d97105/leaderboard/leaderboard/autoagents/agent_wrapper.py),
[merge utility](https://github.com/Thinklab-SJTU/Bench2Drive-Robust/blob/ae1b5867324710bf0574cba797062280d9d97105/tools/merge_route_json.py),
and the authors' [paper](https://arxiv.org/abs/2605.18059). The paper describes 220 routes, fixed
severity labels, deterministic route-level occlusions, and FIFO latency; those are protocol goals,
not evidence that this one-commit implementation realizes them.

A non-executing syntax pass succeeded for the 12 Python and 3 shell files examined. That is only a
parser check. No behavioral test, CARLA smoke, checkpoint load, or metric reproduction was run, so
this document makes no upstream-reproduction claim.

## 4. Compute and storage feasibility

Appendix Table 5 of the original
[Bench2Drive paper](https://arxiv.org/abs/2406.03877) reports one 220-route UniAD-Base evaluation as
8 H800 GPUs for 2 days:

`8 GPUs × 48 hours = 384 H800-hours per clean 220-route pass`.

Bench2Drive-Robust's published matrix has 12 passes per planner: 1 clean, 2 GPS, 3 latency,
2 burst, 2 partial-observation, and 2 speed conditions. The exact first-order arithmetic is:

| Scope | Passes | H800-hours |
|---|---:|---:|
| One planner, published 12-condition matrix | 12 | 4,608 |
| One planner, OFF and Sentinel-ACTIVE arms | 24 | 9,216 |
| UniAD and VAD, both arms | 48 | 18,432 |
| Two planners, both arms, 3 paired seeds | 144 | 55,296 |

This is why “just run the full benchmark” is not a credible one-L4 plan. These are H800-equivalent
budget numbers from the paper's cost report, not predictions of L4 wall time; no conversion factor
is asserted.

The authors also identify the 10-route Dev10 development subset. Linear route-count arithmetic,
used only for budgeting, gives:

`384 × 10 / 220 = 17.4545 H800-hours per Dev10 condition/arm`.

Therefore:

| Dev10 feasibility scope | Condition/arm passes | H800-hours |
|---|---:|---:|
| Clean + latency 200 ms + GPS 15 m + burst 60, OFF/ACTIVE | 8 | 139.6 |
| All 12 conditions, OFF/ACTIVE | 24 | 418.9 |

The route-count scaling assumption may be wrong because difficult routes, simulator restarts, and
timeouts are not uniform. It is a capacity estimate, never a result or launch promise.

### Current box snapshot

The observed remote box has one L4 with 23,034 MiB VRAM, 8 vCPUs, and 31 GiB RAM. Free space was
26 GiB on root and 113 GiB on the data volume. Docker reported 167.6 GB total with 152.8 GB
reclaimable and no containers. Large retained surfaces included approximately 342 GB of sweeps,
294 GB of archives, 128 GB of HUGSIM material, 53 GB of samples, and a 26 GB HUGSIM environment.

Reclaimable accounting can overlap layers and directories, so those numbers must not be summed into
a fictional capacity guarantee. Cleanup remains proof-first: hash/retain committed evidence,
identify reproducible duplicates, delete only verified disposable material, then remeasure. A B2D
campaign needs a dedicated 250-500 GB working volume; the full run also needs appropriately scaled
H800-class compute or an experimentally measured alternative. Root-space improvisation is a stop,
not an invitation to skip acquisition or provenance gates.

## 5. Planner seams and the extraction debt

### UniAD: first active candidate

The pinned Zoo wrapper exposes the least-bad initial seam in
[`team_code/uniad_b2d_agent.py` around line 375](https://github.com/Thinklab-SJTU/Bench2DriveZoo/blob/498c1f799dd90faf840dedb3f0d3234ec2e567db/team_code/uniad_b2d_agent.py#L375):
after the model forward pass has produced a planned SDC trajectory and perception outputs, before
the PID converts the trajectory into vehicle control. The available output surface includes boxes,
scores, and stable track identifiers in addition to the plan.

That is an architectural seam, not yet a valid adapter. Before shadow evaluation, golden fixtures
must verify coordinate axes and handedness, ego/world frame transforms, timestamps and cadence,
track-ID continuity, plan horizon/sample interval, confidence meaning, and the exact transport of a
zero/stop plan through the PID. Any uncertainty fails closed to `SHADOW_ONLY`; it does not license a
control override.

### VAD: shadow only

The corresponding VAD seam is visible in
[`team_code/vad_b2d_agent.py` lines 392-396](https://github.com/Thinklab-SJTU/Bench2DriveZoo/blob/498c1f799dd90faf840dedb3f0d3234ec2e567db/team_code/vad_b2d_agent.py#L392),
between trajectory extraction and PID, but it does not provide the same stable-ID surface. Sentinel
already has a directly relevant portability falsifier: iteration 20's simple VAD association and
smoothing repair removed `0/47` false-closing TTC fires and failed its side-retention gate. That
result is recorded in
[`experiments/iter20_vad_tracker_portability/RESULT.md`](../../experiments/iter20_vad_tracker_portability/RESULT.md).
VAD therefore remains shadow-only until a separately pre-registered association contract passes;
UniAD success must not be generalized to VAD.

### Sentinel's own runtime debt

The released behavior is still embodied in the benchmark-specific
[`server_patch_union_release.py`](../../experiments/iter15_latch_release/server_patch_union_release.py),
while [`sentinel/monitor.py`](../../sentinel/monitor.py) represents an earlier mechanism. Shipping
either file as “the product” would preserve experiment coupling and create two competing truths.

The next engineering object is a benchmark-independent package with typed input/output contracts,
no NeuroNCAP/HUGSIM/Bench2Drive imports, deterministic state serialization, bounded numerical
behavior, explicit fault receipts, and golden replay against committed iteration-15 evidence. The
old patch stays immutable as evidence. Active B2D control is forbidden until the extracted runtime
matches the released decisions on the frozen golden corpus and divergence tests prove that any
mismatch is observable.

## 6. Product transition: Sentinel Deployment Assurance Runtime

The acquisition-worthy object is not a better emergency-brake script. It is an assurance layer
between an arbitrary planner and actuation with auditable timing, uncertainty, and bounded response.

The runtime contract should own:

- **Time:** source timestamp, receipt timestamp, inference interval, command-ready timestamp,
  application timestamp, actual command age, queue depth, and deadline state.
- **State quality:** coordinate-frame identity, covariance/quality for ego pose and speed, sensor
  freshness, camera-frame age, track continuity, and plan horizon validity.
- **Decision modes:** `ALLOW`, `DEGRADE`, `FALLBACK`, and `STOP`, each with a machine-readable reason,
  evidence inputs, latching/release state, and an explicit maximum authority.
- **Bounded fallback:** a planner-independent response whose horizon, steering envelope,
  acceleration/deceleration, jerk, timeout, and release behavior are declared and tested. “All-zero
  trajectory” is not an acceptable universal fallback assumption.
- **Latency receipts:** a per-command chain proving what observation produced which plan, when it
  became ready, which command actually reached actuation, and why any fallback replaced it.
- **Evidence:** route-paired OFF/SHADOW/ACTIVE records, deterministic fault IDs, realized dose, raw
  completion/progress, official metrics where valid, and arm-by-arm failure accounting.

This changes Sentinel's question from “did our patch raise a score?” to “can an independent runtime
detect an invalid deployment envelope, choose a bounded response, and prove exactly what happened?”
That is the systems problem relevant to high-pressure automotive engineering. Bench2Drive-Robust
supplies candidate stressors; it does not define the product architecture or truth standard.

## 7. Fail-closed gate ladder

No later gate may begin before every earlier gate is committed and green.

| Gate | Authorized work | Pass condition | Failure action |
|---|---|---|---|
| **L0 — rights** | Read-only metadata and counsel/rightsholder contact | Written permission plus legal review, or approved external-noncommercial/clean-room boundary | Stop all acquisition, copying, adaptation, publication, and commercial dependency |
| **L1 — code-only contract** | Sentinel-owned interfaces, manifests, deterministic fault fixtures, extracted runtime, shadow receipts; no upstream payloads | Golden iteration-15 replay; deterministic serialization; hostile timestamp/frame/NaN/ID tests; provenance manifest complete | Publish an engineering null; remain code-only |
| **L2 — storage and acquisition** | Authorized pinned archives/checkpoints only | Dedicated 250-500 GB volume; local SHA-256/size verification; malware/pickle handling; immutable acquisition manifest | Delete only verified disposable copies; do not launch |
| **L3 — clean repeatability** | UniAD, route 3514, Sentinel OFF twice | Exact composition and fault manifests; both clean runs complete; route-level outputs and timing receipts agree within pre-registered tolerances | Infrastructure/reproducibility null |
| **L4 — stale-frame canary** | One route, burst fault, `SHADOW_ONLY` | Realized 60-tick stale age is logged deterministically; Sentinel flags the stale stream; no control override occurs | Adapter/fault-harness null |
| **L5 — active canary** | One route only, after L1 golden equivalence | OFF/SHADOW/ACTIVE all complete; bounded override reaches the intended PID/control path; command-age ledger is internally consistent | Control-path null; revert to shadow |
| **L6 — Dev10 feasibility** | UniAD; clean, latency 200 ms, GPS 15 m, burst 60; paired OFF/ACTIVE | Pre-registered seeds and route list; subset-aware analysis; raw route outcomes, progress, realized dose, and uncertainty published | Publish full-weight feasibility null; no retuning on Dev10 |
| **L7 — full UniAD matrix** | Full 220 routes and/or 12 conditions | L0 rights, dedicated storage, measured capacity, independent analyzer, and exact route denominator all green | Stop at Dev10; no extrapolated benchmark claim |
| **L8 — VAD portability** | Shadow only at first | Separate stable-association contract passes its own pre-registration and replay falsifiers | VAD remains unsupported; do not borrow UniAD evidence |

L6 is explicitly `NONOFFICIAL_FEASIBILITY`. It must not be displayed as an official 220-route
Bench2Drive score, compared directly with the published table, or used to claim deployment safety.
L7 requires new authorization and a separate pre-registration; this document does not grant it.

## 8. Binding claim and dependency boundary

Until a future result closes the relevant gates, Sentinel may say only:

> We completed a pinned, read-only feasibility and source audit of Bench2Drive-Robust and designed
> a fail-closed path for evaluating an independently owned deployment-assurance runtime.

It must not say or imply that:

- Sentinel reproduces, improves, solves, or is state of the art on Bench2Drive-Robust;
- the upstream perturbation labels have been behaviorally validated;
- Dev10 is an official Bench2Drive score or predicts the 220-route result;
- the released NeuroNCAP union transfers to CARLA, UniAD, VAD, Tesla, Mobileye, or a real vehicle;
- any monitor intervention is safe, production-ready, or superior to a planner's native behavior;
- CC-BY-NC-ND code, routes, assets, or checkpoints are part of Sentinel's commercial product; or
- parser success, one-route smoke success, or a favorable simulator metric is a safety case.

The commercial architecture must remain usable, testable, and licensable with every
Bench2Drive-family artifact absent. External benchmarks can challenge Sentinel's evidence; they
cannot own its runtime, interfaces, or route to market.

## 9. Preflight verdict

**Proceed now:** extract and golden-test the Sentinel Deployment Assurance Runtime; define typed
time/state/decision receipts; build deterministic clean-room fault fixtures; prepare a signed
composition manifest; and open the license clarification path.

**Do not proceed now:** download upstream payloads, patch the Robust code into a base checkout,
launch CARLA, run a GPU, activate control, publish a benchmark number, or build a commercial feature
on the upstream stack.

The near-term benchmark target is UniAD Dev10 in four conditions only after the rights, storage,
golden-replay, repeatability, and stale-frame canary gates pass. VAD stays shadow-only. Full 220-route
or 12-condition work is a later capital decision, not the default next command.
