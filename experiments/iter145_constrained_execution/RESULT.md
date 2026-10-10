# Iter145: constrained execution and bounded GPU qualification

**2026-10-10 resumed result: supported within the four-case smoke contract.**
The original convergence checks, asset inventory and real simulator smoke now pass.
This is an engineering qualification: no complete-route recovery result or physical
validity claim follows. The proposed 14-scenario / 112-slot study has not started.
Cloud compute was used; the exact owned VM is now **TERMINATED**, its containers were
removed, and the local watchdog exited.

## Resumed measurements

| Check | Result | Evidence |
| --- | --- | --- |
| Asset closure | 5,983 observed file entries; all 14 scenario YAML hashes match | [inventory report](proof/resume_complete_asset_report.json) |
| Original inputs on installed host | 28/28 admitted; 7/28 calls exceeded 50 ms | [host comparison](proof/host_controller_timing_comparison.json) |
| Live GPU smoke | Four fresh nominal cases, 12/12 steps each; one reset each; all stopped at `smoke_step_cap` | [raw batch](proof/gpu_raw/batch.json) |
| Independent execution replay | 48/48 steps supported, including transport bytes, timestamps, controls, actor/render alignment and GEOS foreground overlap | [independent replay](proof/gpu_independent_analysis_v1.json) |
| GPU rendering / actors | 312 camera calls, 48 actor advances, two Attack selections; 48 foreground checks | [aggregate](proof/gpu_aggregate_analysis.json) |
| Maximum live stationarity residual | 9.058617606097497e-7, below unchanged 1e-6 bar | Same aggregate and raw control certificates |
| Complete controller timing | Median 51.305760 ms; maximum 71.016239 ms; **26/48 over 50 ms** | Same aggregate |
| Exchange plus step | Median 2.028208 s; all 48 exceed the .25 s simulation tick | Same aggregate |
| Source/asset preservation | 6,049 original or bound files and 20 actor aliases checked; no changes; owned map-cache copy also unchanged | [postflight](proof/gpu_postflight_integrity_report.json) |
| Focused local tests | 121 passed, 123 warnings | [test log](proof/commands/final_resumed_pytest.stdout) |
| Cleanup | Exact VM observed TERMINATED; watchdog exited | [provider readback](proof/gpu_shutdown_verified.json), [watchdog](proof/gpu_watchdog_exit.json) |

The four cases were `scene-0013-easy-00`, `scene-0038-extreme-00`,
`scene-0013-hard-00` and `scene-0038-medium-01`, in that order. Each ran only
three simulated seconds. The batch took 264.984306 seconds including its file
verification and orchestration. No episode retry or forced-brake outcome occurred.
The fixed seed was 136; the proposed study uses 144 and still needs its own qualification.
No live fresh-process replica comparison was performed in this smoke.

### Timing remains a separate result

Controller convergence passed even when the 50 ms descriptive deadline was missed.
The 28 original inputs had no misses locally and seven on the installed host; the live
48 calls had 26 misses. These are different workloads/environments, not a paired speedup
experiment. Host runtime was Python 3.11.10, NumPy 1.26.4, SciPy 1.17.1,
Torch 2.4.1+cu124, GEOS 3.13.1 and Shapely 2.1.2 as recorded in worker/runtime receipts.
The frozen model container uses its own Torch 1.9.1+cu111 runtime.

Planner exchange alone ranged from 1.502145 to 23.360355 seconds. The four first
exchanges include client readiness; no separate model-startup timer was retained.
After the first exchange in each case, exchange plus step ranged from 1.778705 to
2.653020 seconds (median 2.011067). These sums exclude observation hashing,
serialization and outer-loop overhead, so they are lower bounds on complete loop time.
The synchronous simulator advances by .25 seconds while wall time is longer. Real-time
operation and delay-compensated physical control are unestablished; offline simulated
recoverability can still be studied if this distinction remains explicit.

## Asset and execution corrections

The earlier stopping-point report misclassified 28 unavailable entries. They were
**20 actor files for ten actor IDs plus eight legitimate zero-byte runtime files**.
The [asset amendment](ASSET_CLOSURE_AMENDMENT.md) qualifies the exact historical
`postprocess/shadow.pth -> ..` alias against frozen file hashes, permits only the
registered empty runtime sources, and validates genuinely empty actor populations.
Missing or malformed actor lists remain failures. Full map-loader dependency inventory
added 5,544 files, including nuScenes metadata, vector maps and the complete loader cache.
The runtime writes only to its owned cache copy and outputs.

A Docker import preflight initially failed because a new mount target could not be
created under a read-only model mount. The prospective correction overlays the existing
container `e2e.py` path read-only. The failed and corrected receipts are retained; the
failure preceded any model process, reset or episode, and the budget was not reset.

Raw traces were committed at `7e5976bb9ee4c54dc5f114ca4392d9f16c202510` before
independent aggregate analysis. Base deployment source was
`fc7abe55d5c08338460129fa013b33b0b16dfe27`, with explicit output-guard and mount patches
from `05a550dcc9a09cb657f34c3d82dc9d8215372c19` and
`1202c067739ede3b301a4fc6d53bf4bdd6bd134f`. This is a file-bound patched deployment,
not a claim that the whole packet equals the final commit tree. The active
[execution manifest](proof/gpu_raw/execution_manifest.json) SHA-256 is
`698be5970fb76171b65ca41583eafd92cc260e43724a7709f84c2be38cd23c32`.

The raw driver summary's `gpu_observed: false` is its generic default. Actual GPU
observation is in each worker receipt, with device, model, synchronized render and GEOS
records. Raw bytes remain unchanged. Client exit 137 follows explicit owned-container
removal after the finite cap. Background collision code executed on CUDA points;
independent point-cloud collision/physical fidelity was not established. The map loader
reported a missing route for the Constant actor in the medium case; that actor does not
consume a route. The IDM case loaded its map and completed.

## Resource evidence and next decision

The resumed inspection and GPU qualification used separate prospective 1,800-second /
$1.50 and 5,400-second / $4.50 incremental compute envelopes at a conservative $3/hour.
Official [price evidence](proof/resume_price_binding.json) and both shutdown readbacks
are retained. These are caps, not billing receipts; persistent storage is excluded.
No disk, bucket or hardware was created. The GPU start/stop timestamps were
04:30:58.026 and 04:45:27.673 on the provider's -07:00 clock. Local/provider wall clocks
differed; duration guards used monotonic clocks.

The smoke produced 233,739,383 bytes. Retained JSON, JSONL, logs and configuration were
downloaded and hash-verified; derived PLY and visualization images remain on the stopped
host with complete [hash/size inventory](proof/gpu_raw/output_inventory.json).
Reproduce the analysis with `python3 -m experiments.iter145_constrained_execution.analyze_gpu`.

The [resource projection](proof/gpu_aggregate_analysis.json) is **proposed**, not admitted:
112 x 401 actions at twice the observed maxima gives about 67.88 hours / $203.63 of
compute when first steps are separated, or 591.67 hours / $1,775.00 if every step uses
the slowest observed first-step time. Neither is a measured upper bound. Separating fixed
PLY from linearly growing outputs still gives about 158.75 GiB under the factor-two
assumption, exceeding observed 108.87 GiB free storage even before a reserve. Short
traces in two scenes do not establish bounds for all scenes, arms or late behavior.
The study needs a bounded output policy, full-route runner and outcome replay, explicit
seed/replica qualification, and committed live resource/protocol bindings.

The candidate is local and unpushed; canonical master remains F17. Iter139 remains
null, 0/6 useful recoveries; Iter142 remains null, 0/2. Iter135 remains deferred.
See [DECISION.md](DECISION.md) and [STATE.json](STATE.json) for the current handoff.

---

# Historical stopping-point result (superseded by the resumed result above)

**2026-10-10: paused at Daniel's request before machine shutdown.** Controller
qualification and simulator CPU wiring are supported within the scopes below.
Asset closure is blocked; full GPU integration and live execution remain unqualified.
Cloud compute was used for inspection. No live smoke or study episode ran.

## Retained measurements

| Check | Result | Evidence |
| --- | --- | --- |
| Original controller inputs | 28/28 admitted; four replica pairs | [independent analysis](proof/optimizer_analysis_v3.json) |
| Maximum stationarity residual | 9.548826324229376e-7, below unchanged 1e-6 bar | [raw controller records](proof/optimizer_raw_v3.json) |
| Constraint violation | 0; maximum complementarity 7.863774333754186e-16 | Same controller analysis |
| From-rest straight / curved iterations | 15 / 34, within the unchanged 100-iteration cap | Same controller analysis |
| Simulator CPU wiring | 96 steps, 384 actor advances, 16 selections, four replica pairs | [independent analysis](proof/integration_analysis.json) |
| Short-horizon maximum stationarity | 9.53344077181395e-7 | Same integration analysis |
| Corrupted full artifacts | 30/30 rejected: 15 controller and 15 integration | [known-bad results](proof/known_bad_validations.json) |
| Focused tests | 71 on isolated committed source; 76 after five brake-pulse tests | [isolated log](proof/commands/committed_simulator_pytest.stdout), [later log](proof/commands/brake_branch_pytest.stdout) |
| Cloud asset inspection | 411/439 file entries observed; 28 unavailable; closure blocked | [host report](proof/asset_inspection_report.json) |
| Cloud shutdown | Exact owned VM observed TERMINATED; local watchdog exited | [provider readback](proof/shutdown_verified.json) |

Controller complete-call times were 2.374959–25.150209 ms on the original inputs and
1.284666–18.591459 ms in the CPU integration fixtures. These are ambient local
measurements, not a GPU deadline or vehicle timing qualification. Runtime was local
Python 3.14.2, NumPy 2.4.2, SciPy 1.17.1 and CPU Torch 2.10. Ruff passed. The retained
pytest logs include warnings; frozen Linux and hosted CI were not run for this candidate.

## Failures and corrections preserved

The first SLSQP design failed stationarity on 20/28 inputs. A prospective bounded
Gauss-Newton refinement amendment retained the population, thresholds, 100 total
major-iteration cap and eight-refinement limit. A checker incorrectly treated the last
SLSQP callback as the returned solution; the correction retains both values explicitly.
A shorter-horizon fixture then failed at 2.8796812003850647e-6. The diagnostic traced a
zero admissible step to outward roundoff in an active-bound KKT direction. The
[prospective nullspace amendment](NULLSPACE_AMENDMENT.md) changed the equality-constrained
subproblem solve before the final measurements. Failed records remain in proof.
Stationarity is a local necessary condition; global nonlinear optimality is unclaimed.

The [braking correction](ARM_IMPLEMENTATION_CORRECTION.md) restores the registered
one-second signed pulse, caps braking at zero speed, preserves nominal steering and
resumes nominal control. Only nominal CPU traces were measured; no brake-arm episode ran.

## What the integration evidence covers

The fixtures execute retained HUGSIM environment methods, explicit trajectory timing,
reset, control consumption, render transforms and Attack/Constant/IDM/Unicycle updates.
Named substitutions include constructed CPU state, identity CUDA transfer, deterministic
small camera outputs, background collision false, SAT polygon overlap in place of GEOS,
and synthetic nominal delivery. Actual asset construction, CUDA rendering, GEOS and
planner transport require GPU qualification. The bounded driver core exists; standalone
GPU orchestration remains to be completed. Physical fidelity and recovery are unestablished.

## Inspection and shutdown

One g2-standard-8 / L4 VM start was used under the [inspection binding](HOST_INSPECTION_BINDING.md):
1,800 seconds maximum, $1.50 incremental compute cap and zero live episodes. Official
pricing evidence and the conservative $3/hour bound are retained in
[price binding](proof/price_binding.json). This is a prospective budget, not a billing receipt;
existing persistent disk costs are excluded. No new disk or bucket was created.
The host was idle, with about 109.25 GiB free storage. These observations must be refreshed
before another execution; no permanent resource admission follows from this inspection.

All 14 frozen scenario YAML hashes matched. **Correction recorded on resumption:** the
28 unavailable entries were 20 actor model/dimension paths for ten actor IDs plus eight
legitimate empty runtime files. The earlier statement that all 28 were actor paths was
incorrect. The actor entries were rejected at `postprocess/shadow.pth`.
[Iter46's amendment](../iter46_hugsim_off_baseline/HYPOTHESIS.md) documents a historical
compatibility symlink from that path to the flat actor directory. That is a plausible
explanation, not verified current link identity and not proof that the models are missing.
Two scenarios still require HD-map/route-cache inventories. Three easy scenarios have
valid empty actor lists, which the current asset gate incorrectly rejects. These defects
were identified and saved for resumption; no asset gate was waived.

VM `sentinel-gpu`, ID `3834622546652649531`, in `us-west1-a`, project
`sunlit-unison-487018-b0`, was stopped and observed TERMINATED. The local watchdog exited
after verified cleanup. The inspection envelope is closed and must not be reused.

Tested CPU source: `8b8fa4239f95482d8419a0d5afc09b18248feb43`.
Raw committed before analysis: `f0ccefca87981bf4c02acf58e7bd1bc7dada5f60`.
Later brake correction and inspection source: `ae29d5f83f7b021c735bdf0af914bfc4bd132ee6`.
The candidate remains local and unpushed. Canonical master remains F17.
Iter139 remains null, 0/6 useful recoveries; Iter142 remains null, 0/2.
Iter135 stays deferred. The proposed 14-scenario / 112-slot study has not started.

See the [resume handoff](DECISION.md) and [machine-readable state](STATE.json).
