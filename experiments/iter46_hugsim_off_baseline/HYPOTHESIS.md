# Iteration 46 - HUGSIM Stage-1 monitor-OFF baseline pre-registration

Frozen before any iteration-46 tooling, GPU command, simulator launch, or claim. Committed
alone, before any run script exists. This is the Stage-1 pre-registration authorized by the
iteration-45 pass (`experiments/iter45_hugsim_infra_gate/RESULT.md`, S4 boundary: the pass
authorizes ONLY this pre-registration) and follows the frozen Stage-1 shape in the launch
packet `docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md`: monitor-OFF reproduction on a
frozen scenario subset, scenario list and run-multiplicity frozen here, published closed-loop
anchors used as loose plausibility context only.

## Research question

Does the unmodified UniAD_SIM client, on the exact NeuroNCAP checkpoint, complete a frozen
52-scenario nuScenes-derived HUGSIM subset closed-loop end-to-end — producing an `eval.json`
HD-Score and per-step logs for every scheduled episode — so that a later seed-paired
OFF-vs-released-union comparison (Stage 2) has a complete, provenance-locked OFF arm to pair
against?

## Stage-1-only scope (binding)

This is the monitor-OFF arm ONLY. It contains:

- NO monitor patch, NO sentinel code on the HUGSIM/UniAD_SIM side, NO interception, NO
  OFF-vs-ON comparison, NO threshold work of any kind;
- NO transfer, benchmark-ranking, robustness, deployment, or safety claim;
- NO HD-Score interpretation beyond completion accounting and the loose plausibility note
  defined below (which is context, NOT a bar).

A pass authorizes ONLY the writing of the Stage-2 pre-registration (OFF vs released union,
seed-paired, scene-clustered bootstrap CIs, the launch packet's falsifiers). It does not
authorize the Stage-2 runs themselves. A blocked or failed gate publishes a null at full
weight (`HUGSIM_OFF_BASELINE_NULL` naming the failed bar/falsifier).

## Frozen scenario subset (deterministic rule, exact list)

**Rule:** every scenario yaml in the released `XDimLab/HUGSIM` `scenarios.zip` nuScenes
export (staged and manifested in iteration 45 at
`/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/`) whose difficulty tier is
`easy` or `medium` — filename matching `scene-*-easy-*.yaml` or `scene-*-medium-*.yaml` —
taken in lexicographic filename order. No other selection input exists. This resolves to
**52 scenarios across 18 scenes** (18 easy + 34 medium; `scene-0010` ships scene assets but
no scenario yaml and is therefore excluded by the rule itself). Hard/extreme tiers are
deliberately out of Stage-1 scope: the reproduction question is "does the pipeline hold at
subset scale", not "how does UniAD fare under adversarial actors" — that comparison belongs
to Stage 2 design.

Frozen per-file SHA256 receipts of the 52 scenario yamls, read from the staged export before
this pre-registration was committed (verification at launch is a hard provenance gate):

```
22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735  scene-0013-easy-00.yaml
162bd65e0fa40d6f46a992063da665f858ccf78b00879b0a34fdfc76103a2401  scene-0013-medium-00.yaml
275066a06afb7a909748739e28de0eabc3d8c711d8c73f8769225a959ac5c3d5  scene-0038-easy-00.yaml
fb18b473300b9373e089fb0656caf533e6920de3314df4e6703b04cdb30d08c4  scene-0038-medium-00.yaml
cbc56796e802e964bca700662f34c77fb2500ee8ee32225820276521d4a230e2  scene-0038-medium-01.yaml
0d6f403dacf5f9f5b069f4fa9009e60dc0a8d76bb52d0843e18de63926d57756  scene-0041-easy-00.yaml
276024f3a668b64262829eecff89f27b9b318e32d71a85fdf5ccfbfa4f58d564  scene-0041-medium-00.yaml
3f082023ffc6d117897cb342c8e0b09d638579c84389e8beb30f9e224d2c5f93  scene-0041-medium-01.yaml
48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1  scene-0051-easy-00.yaml
bcdee66520d70d3666e51b00ed155e494f7f06772c9e50cfd2c4d5f678906016  scene-0051-medium-00.yaml
d239eabe85a5d6e518c86263d293d45bde2b50b4bf0c984268c78e5ee2db8b16  scene-0051-medium-01.yaml
5d49e3535d6b61eca97fe350baa000c35db9c7f75c4dd01f09712a64ec5e4429  scene-0062-easy-00.yaml
8ab4eaa941cf292710701f1a8e0d791ee81fede1874c985d0bf126951018e2ae  scene-0062-medium-00.yaml
299c8ed35a83d5bdfa4f2c9aaf42911d83a334f072adac457a4dbf348d7b5bd5  scene-0062-medium-01.yaml
b7665e1495ffe4fa045af495a44defe247e5497cb8d79330e5f054de86898392  scene-0064-easy-00.yaml
aef45943c6675c79872f305403632e72c47c4cf1ea7fc312a438a47009503b75  scene-0064-medium-00.yaml
e8a5c2d53b016257f7c1e0758137395c72ff7d36de368af8937ff7d2249efd98  scene-0064-medium-01.yaml
f04f159365d966c3bacf326375eb67463cf2614b85b9343eff2adec84d640750  scene-0071-easy-00.yaml
19542bfd37e20b34635f3b8279fa909a1a6dba0774b5c8076100b0969897faa5  scene-0071-medium-00.yaml
1fc17294a29cd90ba424c9d481d7f91f94aa8c5e9649ccf8c79115acc7a8744d  scene-0071-medium-01.yaml
8e4dd7879dc5571396f2cbc332175e869f9a806932e33665a79b34976abb9669  scene-0138-easy-00.yaml
a789c2df8e5a128e618b84a0e84197f6130c2de5b61cd5893bae1ec91817be98  scene-0138-medium-00.yaml
69e97a6c983982365b4336e95d2b48570729ab92984ebaa63b5e644118505f9a  scene-0138-medium-01.yaml
c83e3968a727d199c91dfda0987431fc943e47ca238d2a47f91ef7fc903bfb39  scene-0166-easy-00.yaml
f48075e69aa246bdd26b3fb468814151c412ebd0e94bf4f6c4313d3c6aba9430  scene-0166-medium-00.yaml
fa7d9c8912cf4ea62aa9c2498de516f048742cb93e903b59f0f7d6580138d30b  scene-0166-medium-01.yaml
3b4881b920dca9b410cd8112a329c331e5900642967e44ecb4da590235ee0060  scene-0167-easy-00.yaml
992431bd838b3ffd232c9f3ba052fc24553c5478e3fffed580ff1e6ba70341de  scene-0167-medium-00.yaml
9f230954ce903fe6587edc044a069559e6121dcbd7b77b6b83dc255df5fe084c  scene-0167-medium-01.yaml
70ffeb11cb5178d6244caef9f243f2fa3ee0ac864aebf6694626f4162508d496  scene-0254-easy-00.yaml
efca4498f7b08e25767a04ae8007f164c1a837c3f7ceb88e9c5a76525dfbb045  scene-0254-medium-00.yaml
9ec53138759dac721d6abbe939647574a8f1025ecfaad3e24c955fc0099c9ea9  scene-0254-medium-01.yaml
b0264012e4abdfacd69c24d66d584c5cc3bd403719d4337f635b861327382efb  scene-0383-easy-00.yaml
845eb2efdf4ea5e71fd38f3bd3a22798f8bc733a1547b569a080e57a10885671  scene-0383-medium-00.yaml
5db6b1fa03fa5125c5705ba7b0decdfe876075737ac7c5e0a23023a9b8f34bc3  scene-0383-medium-01.yaml
b240cd999d2965a3065c8bed180963f6ea2b142a71c0e9db060c131667424f4f  scene-0411-easy-00.yaml
e523239202841b593337756c8574066ec4ebf78c8e21327dc4d8fe0e6df48d5a  scene-0411-medium-00.yaml
6be5e30531971509201d03e7a562a3979932dcc4969a8d9f001379f9be903475  scene-0411-medium-01.yaml
43835067f13a42bc2b2ba5e1f6194c53e3ccf66f4ec97158f058cbacd11039e3  scene-0418-easy-00.yaml
7352e0f2274b5995cd2f7e4b25a40e33065a0ef360ddc100648ca37a2838e596  scene-0418-medium-00.yaml
8486d3105f9a3e9957bb8618009d105a57493d3818eba479cc7896153a95ae43  scene-0418-medium-01.yaml
b86f4ecdac8da1ccf5f63b47f8393977dacbcd60b2110046b93c30c80f09fdb6  scene-0528-easy-00.yaml
1601f6abb8c0f17f0582a51fa74f9d543928c1ff8c417588624e9727bfdc0fda  scene-0528-medium-00.yaml
496332fae21957d585067260f36f87d7ee83544edfe252ef22bc203273ca5311  scene-0528-medium-01.yaml
9505645725545ae4c28fd9ea909fbcc665631434af59527af8802322553540f5  scene-0661-easy-00.yaml
79201b40fba2e32e5194236a080629b51c89308cc3ff38d097e744294f5fb9bf  scene-0661-medium-00.yaml
8ab2194ea48cf5b0c5e1640fc421926956d49049b6049c182923cd03ce577504  scene-0661-medium-01.yaml
f28ceeb17036d5671943fae8428ef3c00c0bd52383c347fd7c3a3268e139e8c9  scene-0920-easy-00.yaml
8edbdea084cca4ad9b6e5548bab49b1edcc66309a54fbe163c8c5f3b7518512b  scene-0920-medium-00.yaml
27fbcc2c4639d010601169139e90e51647dfaf8f239df9cb1c9c83c314d34179  scene-0930-easy-00.yaml
ff5b7b16146780663da0a28be5f9b477fc223517bbf5111463243e72bb83b614  scene-0930-medium-00.yaml
e60488e152656de157742141c1cf68d834059c9645507edafb3764f2d6ad10d5  scene-0930-medium-01.yaml
```

## Frozen determinism probe and run multiplicity (D0)

The HUGSIM closed-loop entry point exposes no seed parameter (`grep -rn seed closed_loop.py
sim/` on the cloned `62c690d3` tree finds only the gymnasium `reset(seed=None)` signature,
never called with a seed by `closed_loop.py`), so determinism must be established
empirically, first, before the subset run's multiplicity is known:

- **D0 probe:** the lexicographically first scenario (`scene-0013-easy-00`) is run TWICE,
  back to back, before any other episode. The two runs are compared on: (a) client step
  count (pipe round-trip `sent` lines in `output.txt`) exactly equal; (b) every numeric
  field of `eval.json` exactly equal; (c) the per-step episode record `data.pkl` —
  byte-identical SHA256, or, if bytes differ, a recursive numeric comparison of all array/
  scalar leaves with max abs delta exactly `0.0`.
- **All three hold → DETERMINISTIC branch:** N=1 run per scenario; all 52 scenarios are
  scheduled once (D0 run 1 counts as `scene-0013-easy-00`'s episode; D0 run 2 is committed
  as determinism evidence). Stage-2 pairing note: deterministic OFF episodes pair 1:1
  against future ON episodes by scenario identity.
- **Any fails → STOCHASTIC branch:** N=2 runs per scenario on the lexicographically first
  26 scenarios of the frozen list (the two D0 runs are `scene-0013-easy-00`'s two runs).
  Episode count stays 52; the within-scenario repeat pairs measure run-to-run spread, which
  Stage-2 pairing design then has to carry. The branch decision is made once, by the D0
  comparison, and is logged with marker `I46_OFF_D0_VERDICT=` before episode 3 starts.

Total scheduled runs: 53 in the deterministic branch (52 episodes + the D0 repeat), 52 in
the stochastic branch. The branch is an observable-keyed pre-declared fork, not a
post-hoc choice.

## Frozen environment and provenance (verified as a hard gate at launch)

All values were read from the box before this file was committed; the run script re-verifies
each and refuses to start on any mismatch (`I46_OFF_PROVENANCE_FAIL`):

- HUGSIM repo `/opt/sentinel-stack/HUGSIM` @ `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
  UniAD_SIM repo `/opt/sentinel-stack/UniAD_SIM` @
  `5fb279e39912a5ac7f58e00d56b065cadcd0a749` (client code unmodified; the docker wrapper
  `tools/e2e.sh` and base-config path edits are the iteration-45-recorded config surface,
  originals preserved as `.orig`).
- Docker image `uniad:latest`, image id `f73ef3884063` (the NeuroNCAP image).
- Planner checkpoint `uniad_base_e2e.pth` SHA256
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990` (the exact NeuroNCAP
  checkpoint — the same-checkpoint premise of the transfer line); motion anchor file SHA256
  `45761de4a965c590318987f43af7e7f50b8e043f9a2832a91246f4fd39bb57bb`.
- **The iteration-45 CPU-fallback shim is carried explicitly** (the S4 boundary requires
  it): `/opt/sentinel-stack/hugsim-shim/sitecustomize.py`, SHA256
  `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c`, mounted read-only into
  the client container via `PYTHONPATH` by the wrapper. It routes the cuSOLVER-backed dense
  linalg ops (`inverse`/`linalg.inv`/`cholesky`/`svd`/`eigh`/`symeig`) through CPU because
  CUDA 11.1 cuSOLVER cannot initialize on the L4 (sm_89); same math, different execution
  provider; client/model code untouched. A byte copy is committed in this directory
  (`shim/sitecustomize.py`) and the launch gate requires the box copy to match it.
- HUGSIM pixi environment as frozen by iteration 45: torch `2.4.1+cu124`, gsplat `1.2.0`
  (`experiments/iter45_hugsim_infra_gate/proof-infra/hugsim_pip_freeze.txt`).
- Per-scene prep (the iteration-45-recorded edit class, applied by script): each scene zip
  is extracted once to `/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/` and the
  extracted `cfg.yaml`'s author-absolute `model_path` is rewritten to the staged path, with
  the original preserved as `cfg.yaml.orig`. The zips in the committed iteration-45 manifest
  are never modified.

## Completion bars (all required for a pass)

- **C1 — all scheduled episodes complete.** Every scheduled episode (52 per the D0 branch)
  terminates by the benchmark's own rule within the per-episode wall-clock bound and
  produces an `eval.json` whose `hdscore` is a finite number, after at most ONE scripted
  retry per episode. A single episode failing both attempts fails C1.
- **C2 — per-step logs captured for later monitor-ON pairing.** Every completed episode's
  collection directory contains the client per-step log (`output.txt` with the
  `received`/`sent` round-trip lines; step count recorded in `episode_meta.json`) and the
  per-step episode records (`data.pkl`, `infos.pkl`) with SHA256 receipts. These are the
  pairing substrate for the future Stage-2 ON arm.
- **C3 — evidence committed and sized for git.** Per-episode `eval.json` + `output.txt` +
  `episode_meta.json` and the run-level receipts (provenance gate output, D0 comparison
  report, full run log) are committed under `proof-off/` (files >90 MB split into
  `.part-*`); heavy artifacts (`data.pkl`, `infos.pkl`, `video.mp4`, ply files) are
  retained on the data disk under the run collection root with a committed SHA256 manifest.

D0's verdict itself is not a bar — either branch can pass; the verdict is a recorded fact
that constrains Stage-2 design.

## Plausibility note (context, NOT a bar)

The subset mean and per-tier mean HD-Scores are reported next to the published RealADSim
closed-loop anchor range (~0.30-0.42 HD-Score) as a LOOSE plausibility cross-check only:
scene sets, tiers, and client stacks differ, and the iteration-45 single-scenario smoke
value (0.1677) supports no expectation in either direction. No numeric HD-Score level passes
or fails this iteration; a wildly implausible aggregate (e.g. all-zero or all-1.0) triggers
investigation and honest reporting, not silent acceptance — but the registered verdict rides
on C1-C3 and the falsifiers alone.

## Budget (frozen, with the arithmetic)

- Evidence base: the iteration-45 smoke completed `scene-0013-easy-00` end-to-end in ~2
  minutes wall (15 steps, simulator + client both on the L4).
- Per-episode ceiling: `timeout 1200` s (20 min) on the closed-loop process, plus ~2 min
  amortized scene-prep/collection overhead. Medium-tier scenarios add actors and some scenes
  are larger, hence the 10x headroom over the observed smoke.
- Worst case: 53 runs x ~22 min = **~19.4 GPU-hours**, inside the 20 GPU-hour cap this
  pre-registration adopts from the launch packet. Expected, from the smoke evidence: 53 runs
  x 3-7 min = **~2.5-6 GPU-hours**.
- Hard stop: the abort guards below ensure a pathological run cannot burn the box for days.

## Named falsifiers

- **Client crash/deadlock loop at scale.** Any episode failing twice (initial + retry)
  fails C1; THREE CONSECUTIVE episodes failing both attempts aborts the run early
  (`I46_OFF_ABORT_CONSECUTIVE_FAILURES`) — publish the null with the failure evidence
  rather than burning the remaining budget.
- **VRAM overflow at subset scale.** CUDA out-of-memory in simulator or client on scenes
  heavier than the smoke scene — the L4's 24 GB may not hold both halves everywhere.
  Reported per-episode; if systematic (the consecutive-failure guard fires on OOM), it is
  the falsifier form of the null.
- **Non-determinism breaking seed-pairing.** In the STOCHASTIC branch only: if the median
  within-scenario |ΔHD-Score| across the 26 repeat pairs exceeds `0.15`, run-to-run spread
  is large enough to make naive per-scenario pairing meaningless; publish as a
  pairing-infeasibility finding — Stage-2 design must change (repeats per arm), and that is
  the honest outcome, not a defect.
- **Disk exhaustion.** The run script checks free space on `/datasets/nuscenes-full` before
  every episode and aborts below 20 GiB (`I46_OFF_ABORT_DISK`). An abort here is an
  interrupted run with a resume point, not a null, unless space cannot be recovered.

## Forbidden claims (binding)

No transfer claim, no monitor claim, no OFF-vs-ON statement, no safety/robustness/deployment
claim, no UniAD performance ranking, and no HD-Score interpretation beyond the completion
bars and the plausibility note. This is the OFF arm only. A pass authorizes exactly one
thing: the Stage-2 OFF-vs-released-union pre-registration. The iteration-39 wording rules
apply to every doc this iteration touches.

## Required proof artifacts

- `proof-off/receipts.json`: provenance-gate output (all frozen SHAs re-verified at launch);
- `proof-off/d0_comparison.json`: the D0 determinism report and branch verdict;
- `proof-off/episodes/<scenario>__r<run>/`: per-episode `eval.json`, `output.txt`,
  `episode_meta.json`;
- `proof-off/heavy_manifest.txt`: SHA256/size of the heavy on-box artifacts per episode;
- `proof-off/i46-off-run.log`: the full box-side run log
  (`/var/log/sentinel-iter46-off.log`), with `I46_OFF_EP_START`/`I46_OFF_EP_DONE` pair
  markers per episode and the final `I46_OFF_ALL_DONE` marker.

## Protocol

1. Commit this `HYPOTHESIS.md` alone (with the in-repo shim byte copy named above), CI
   green, before any tooling exists.
2. Commit tooling: detached run script (box playbook: `setsid nohup`, `set -x`, log
   `/var/log/sentinel-iter46-off.log`, per-episode pair markers, done marker
   `I46_OFF_ALL_DONE`), the on-box D0 comparison helper, the offline analyzer skeleton, and
   unit tests; ruff + pytest + validate_docs green.
3. Launch the run detached on `sentinel-gpu`; verify the first scenario is producing steps
   before leaving; record IN FLIGHT state in CONTINUITY/HANDOFF. Never alongside another
   GPU job.
4. On `I46_OFF_ALL_DONE`: collect evidence, run the committed analyzer ONCE from collected
   artifacts, publish `RESULT.md` at full weight (pass or null), update README/CONTINUITY/
   HANDOFF. No Stage-2 run happens under this pre-registration.
