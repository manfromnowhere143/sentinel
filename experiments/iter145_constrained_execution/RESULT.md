# Iter145 result at the operator stopping point

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

All 14 frozen scenario YAML hashes matched. The 28 unavailable paths are actor model and
dimension paths rejected by the no-follow reader at `postprocess/shadow.pth`.
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
