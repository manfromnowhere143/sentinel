# Iter145 current decision and continuation handoff

## Completed after Daniel resumed, 2026-10-10

Asset closure and the four-case GPU smoke are supported in the scope stated in
[RESULT.md](RESULT.md). All 48 control/step records pass independent replay; 26/48
controller calls missed 50 ms. No full-route recovery or real-time result follows.
The cloud VM is verified **TERMINATED**, the watchdog exited, and no owned job remains
active. The study has zero episodes and is not admitted. This is a completed engineering
milestone, not a new operator-requested pause. No automatic restart is scheduled.

## Next concrete work

1. Read current root identity/instructions, active CONTINUITY, this handoff and STATE.
   Keep the dirty root on `wip-gen17-ci-hardening`. Use the candidate through Git or an
   isolated same-repository source packet; preserve unrelated WIP and the immutable README.
2. Implement the full-route 401-action runner and separately implemented outcome checker.
   Keep the Iter145 12-step smoke contract intact. Bind single reset, exact terminal reasons,
   final actor/ego state, collision source, route progress and all missingness explicitly.
   A useful recovery must finish the route collision-free; delay alone does not count.
3. Implement and qualify all four scheduled deliveries: nominal, released monitor,
   one-second brake at t=0 and at t=2.5, preserving signed braking and nominal steering.
   Retain full action/prefix checks and tests that reject mismatched comparisons. Source:
   [case-family protocol](../iter143_model_contract/CASE_FAMILY_PROTOCOL.md),
   [proposed schedule](../iter144_timed_trajectory/study.py),
   [braking correction](ARM_IMPLEMENTATION_CORRECTION.md).
4. Resolve output/storage policy before live execution. The retained projection including
   fixed PLY still exceeds observed free storage; it is not an admitted bound. Qualify any
   prospective visualization/output change without altering evidence needed for replay.
   Measure full-loop time explicitly, including serialization, and keep numerical admission,
   descriptive controller deadlines, simulator time and wall time as separate fields.
5. Bind seed 144, fresh-process replicas, all 14 fixed scenarios / 112 slots, exact source,
   runtime, assets, qualification and a finite total resource envelope. The current four-case
   seed-136 nominal smoke supplies bounded integration evidence, not full study admission.
   Requalify the actual study source and arms under its own finite prospective binding.
6. Then execute the fixed lexical scenario/arm/replica schedule, committing raw before
   analysis and before later arms. Preserve no initialized retry/replacement/seed search,
   stops on invalid replay, successful-comparator cases, missingness and witness criteria.
   Three historically exposed scenes provide development evidence; no untouched holdout
   or population-generalization claim exists. Finite action-library failure is not proof
   that physical recovery is impossible. No independent-human ceremony is required.

## Recovery anchors

- Candidate: `research/iter145-constrained-execution`, local/unpushed. Raw GPU commit:
  `7e5976bb9ee4c54dc5f114ca4392d9f16c202510`. Read current tip with `git rev-parse`.
- Deployed base/patched source identities and manifest are listed in RESULT. All measured
  failures and amendments are retained. Do not rewrite accepted or raw historical bytes.
- Host: `sentinel-gpu`, ID `3834622546652649531`, project `sunlit-unison-487018-b0`,
  zone `us-west1-a`; [latest terminal readback](proof/gpu_shutdown_verified.json).
- Host control/output: `/datasets/nuscenes-full/hugsim/iter145_gpu_20261010/`.
  Raw receipts and JSON/JSONL/log/config files are local in `proof/gpu_raw/`; derived PLY
  and visualization files are retained on host with hashes. All start budgets are closed.
- Resumed inspection cache/source evidence: `proof/resume_*`; GPU evidence: `proof/gpu_*`.
  Reproduce aggregate locally with `python3 -m experiments.iter145_constrained_execution.analyze_gpu`.
- External packet/receipts: `/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-gpu-20261010/`
  and `iter145-resume-20261010/`. Exact session tools are retained under `proof/session_tools/`.
- 121 focused local tests passed with 123 warnings. Prior isolated CPU test receipts remain;
  hosted/frozen Linux CI was not run for this unpushed candidate. No blanket CI-green claim.
- Portable memory: `/Users/danielwahnich/.codex/memories/sentinel-latest.md`.
  Root HANDOFF/MISSION_STATE remain their historical publication snapshot.

---

# Historical pause handoff (tasks below superseded by the current handoff)

## Stopped at Daniel's request, 2026-10-10

The machine is about to be closed for approximately one hour. Work is paused; no automatic
restart is scheduled. Cloud VM `sentinel-gpu` (ID `3834622546652649531`, project
`sunlit-unison-487018-b0`, zone `us-west1-a`) is **TERMINATED** according to the
[retained readback](proof/shutdown_verified.json). The owned local watchdog exited.
No owned job remains active. Cloud compute was used for asset inspection; zero live
smoke/study episodes ran. Read [RESULT.md](RESULT.md) and [STATE.json](STATE.json).

## First actions when Daniel resumes

1. Verify Sentinel cwd/root/remote and read AGENTS.md, the active CONTINUITY block,
   this handoff and STATE.json. Inspect `research/iter145-constrained-execution` through
   Git without checking out over the dirty WIP root. No human acceptance ceremony is needed.
2. Correct and qualify asset inventory locally. Preserve all scenario YAML bytes.
   Iter46 HYPOTHESIS.md (historical section around lines 262–294) records the approved
   `<car>/postprocess/shadow.pth -> ..` compatibility alias over flat released
   `<car>/{gs.pth,wlh.json}`. Inspect that exact historical evidence and the Iter45
   `proof-infra/hugsim_asset_manifest.txt`. Implement an explicit, bounded logical-to-physical
   mapping; verify actual link text, target ownership and canonical regular-file hashes.
   Do not generally relax no-follow reads or substitute actor assets. Current link identity
   was not read back in this inspection. Retain known-bads for escape, wrong alias and hashes.
3. Accept a validated empty `plan_list` for the three easy scenarios, with a known-bad for
   missing/malformed lists. Complete HD-map and route-cache dependency discovery for
   `scene-0013-hard-00.yaml` and `scene-0038-medium-01.yaml`. Base config uses
   `/datasets/nuscenes-full`, `nusc_trainval`; inspect actual loader dependencies.
4. Prepare and commit a fresh finite inspection/qualification binding before any new VM
   start. The previous single-start, 1,800-second inspection envelope is closed. Refresh
   cloud identity, credentials, price bound, disk/RAM/GPU headroom, idle state and clock
   basis; stale receipts do not admit execution. Arm cleanup and retain terminal evidence.
   Authentication recovered this session and is not currently a known blocker.
5. Finish source-bound GPU assembly around the bounded driver and planner pipe. Qualify
   actual asset construction, rendering, CUDA, GEOS, transport, actor/ego consumption,
   resets, stop reasons, wall-clock limits and cleanup with a finite preregistered smoke.
   Record complete-call deadlines separately from numerical convergence. No smoke was
   authorized by the now-closed inspection binding, and no smoke was run.
6. Only after those checks, finalize live bindings for the proposed 14-scenario / 112-slot
   study. Preserve frozen populations, schedules, outcomes, missingness, retries and stops.
   These are historically exposed development scenarios across three scenes, not an
   independent generalization population. Do not relabel collision delay as useful recovery.

## Evidence and preservation

- CPU: original 28/28 inputs pass unchanged constrained checks; 96 CPU integration steps,
  384 actor advances; independent replay and 30 corrupted-artifact rejections retained.
- 71 focused tests passed on the isolated 56-file source packet; 76 passed locally after
  five brake-branch tests. Real GPU/GEOS/model transport and physical validity remain open.
- Source `8b8fa4239f95482d8419a0d5afc09b18248feb43`; raw-before-analysis
  `f0ccefca87981bf4c02acf58e7bd1bc7dada5f60`; brake/inspection correction
  `ae29d5f83f7b021c735bdf0af914bfc4bd132ee6`. No brake-arm outcome measured.
- All failed optimizer, replay and development attempts remain retained. Inspect amendments
  before interpreting results. Never use callback values as a substitute for SLSQP result.x.
- Host packet/output remains at `/datasets/nuscenes-full/hugsim/iter145_control_20261010/`;
  all relevant inspection output is also in local `proof/`. No remote process remains running.
- External evidence: `/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/`.
  Frozen source packet is `simulator_source_v4/`. Retained tooling is `proof/session_tools/`.
- Root stays `wip-gen17-ci-hardening`. Preserve unrelated WIP, staged state, immutable README,
  canonical HANDOFF.md and MISSION_STATE.json. The active blocks in CONTINUITY/NEXT_PHASE
  carry the current candidate state. Candidate README was updated through an alternate index;
  root README was not edited. No checkout, stash, master move, push or publication was used.
- Latest portable memory is `/Users/danielwahnich/.codex/memories/sentinel-latest.md`.
  The previous snapshot is `sentinel-through-iter144-closure-2026-10-10.md`.
