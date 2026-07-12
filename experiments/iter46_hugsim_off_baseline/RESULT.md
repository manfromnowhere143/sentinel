# Iteration 46 - HUGSIM Stage-1 monitor-OFF baseline: completion null

Status: `HUGSIM_OFF_BASELINE_NULL` (analyzer verdict `NULL_FALSIFIER_CRASH_LOOP_DUAL_FAILURES`)

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested by the single registered detached
run on `sentinel-gpu` (two launches: the first aborted by the consecutive-failure guard on two
run-script/staging defects and was fixed by the recorded launcher-only amendment; the second
resumed under the carried D0 verdict and ran to `I46_OFF_ALL_DONE` at 03:43:53 UTC,
2026-07-12), followed by ONE run of the committed analyzer over the collected, committed
artifacts. The provenance gate passed at both launches (frozen HUGSIM/UniAD_SIM SHAs,
checkpoint SHA `0ad0c2f5…`, shim SHA `5bf69a11…`, image id `f73ef3884063`, all 52 scenario-yaml
SHA256s verified; [`proof-off/receipts.json`](proof-off/receipts.json)). The D0 determinism
probe returned **STOCHASTIC** (16 vs 15 client steps, structural `eval.json` mismatch,
`data.pkl` SHA divergence; [`proof-off/d0_comparison.json`](proof-off/d0_comparison.json)), so
the frozen schedule was the stochastic branch: the lexicographically first 26 scenarios x 2
back-to-back runs = 52 episodes.

**The registered completion gate failed.** 38 of 52 scheduled episodes completed; 14 episodes —
exactly the seven `-medium-01` scenarios in the subset that carry `load_HD_map: true` — failed
both scripted attempts, firing the registered crash/deadlock-loop falsifier in its dual-failure
form. Per the pre-registration this publishes as a null at full weight, and it authorizes
nothing: the Stage-2 OFF-vs-released-union pre-registration is NOT authorized (a pass was its
only trigger). The 38 completed episodes and the D0 verdict are committed evidence that a
successor completion pre-registration may cite.

Claim boundary (registered, binding): this is the **OFF arm only**. No transfer, monitor,
OFF-vs-ON, benchmark-ranking, robustness, deployment, or safety claim; no UniAD performance
ranking; HD-Score numbers below are completion accounting and the registered plausibility
context only. The iteration-39 wording rules apply.

Harness:

- [`run_off_baseline.sh`](run_off_baseline.sh) (box-side, amended per the HYPOTHESIS.md
  amendment note), [`d0_compare.py`](d0_compare.py),
  [`analyze_off_baseline.py`](analyze_off_baseline.py)
- [`../../tests/test_iter46_off_baseline.py`](../../tests/test_iter46_off_baseline.py)

Primary evidence:

- [`proof-off/off_baseline_report.json`](proof-off/off_baseline_report.json) (the analyzer
  report; command receipt in
  [`proof-off/analyze_off_baseline.command.txt`](proof-off/analyze_off_baseline.command.txt))
- [`proof-off/episodes/`](proof-off/episodes) (per-episode `eval.json`, `output.txt`,
  `episode_meta.json` for the 38 completed episodes; `episode_meta.json` plus the preserved
  client log for the 14 `__failed` dirs)
- [`proof-off/i46-off-run.log`](proof-off/i46-off-run.log) (launch 2, the completing run) and
  [`proof-off/i46-off-run-launch1.log`](proof-off/i46-off-run-launch1.log) (launch 1, aborted;
  its defect evidence archived under [`proof-off/prior_launches/`](proof-off/prior_launches))
- [`proof-off/heavy_manifest.txt`](proof-off/heavy_manifest.txt) (SHA256 manifest of the heavy
  per-episode artifacts — `data.pkl`, `infos.pkl`, `video.mp4`, ply — retained on the box at
  `/datasets/nuscenes-full/hugsim/iter46_runs/`)
- [`proof-off/load_hd_map_flags.txt`](proof-off/load_hd_map_flags.txt) (diagnostic: the exact
  set of released scenario yamls carrying `load_HD_map: true`)

## Verdict

| gate | result |
|---|---|
| S0 provenance | **PASS**: HYPOTHESIS committed alone (`077e8d9`) before tooling; tooling committed (`a03ea18`) before launch; launcher-only amendment (`2af43dd`) recorded in HYPOTHESIS.md before relaunch with no frozen bar/scenario/SHA/schedule change; both launches passed the hard provenance gate; single-tenant rule held (no other containers) |
| D0 determinism probe | **STOCHASTIC** (recorded fact, not a bar): steps 16 vs 15, `eval.json` structural mismatch, `data.pkl` SHA differs → branch = first 26 scenarios x 2 runs; verdict made once (launch 1) and carried, per the pre-registration |
| C1 all scheduled episodes complete | **FAIL**: `38/52` complete. The 14 failures are the seven `load_HD_map: true` `-medium-01` scenarios (scenes 0038/0051/0062/0064/0071/0138/0166), each failing both attempts with rc=0, no `eval.json`, 0 client steps. Every completed episode finished on attempt 1 (`retried_episodes = 0`, inside the <=1-retry clause); episode wall clock 114-481 s, all inside the 1200 s bound |
| C2 per-step logs captured | **FAIL (via C1, as registered)**: all 38 completed episodes have `output.txt` round-trip logs and positive step counts (15-150 steps, median 51); the bar requires this for every *scheduled* episode, so it falls with C1 |
| C3 evidence committed | **PASS as a fact**: run-level receipts, D0 report, both launch logs, per-episode artifacts, prior-launch defect archive, and the heavy-artifact SHA manifest committed under `proof-off/` (no file over 90 MB; no split needed) |
| Falsifier: crash/deadlock loop | **FIRED** (dual-attempt failures on 14 episodes) — the registered falsifier form of the null. Mechanism diagnosed below: a staging gap, not a client crash after stepping, not a pipe deadlock |
| Falsifier: VRAM overflow | not fired (no CUDA OOM anywhere in either launch log) |
| Falsifier: pairing infeasibility | **NOT fired**: median within-scenario \|ΔHD\| = `0.0245` over the 19 complete pairs, well under the frozen `0.15` bar |
| Falsifier: disk exhaustion | not fired (guard checked before every episode) |

## The failure, diagnosed (on the record)

Every failed episode dies before the client's first step with the same simulator-side
exception, preserved in the committed run log:

```text
FileNotFoundError: [Errno 2] No such file or directory:
  '/datasets/nuscenes-full/maps/expansion/singapore-onenorth.json'
```

The seven failing scenarios are exactly the scheduled yamls carrying `load_HD_map: true`
([`proof-off/load_hd_map_flags.txt`](proof-off/load_hd_map_flags.txt)). That flag makes
HUGSIM's `hug_sim.py` construct a trajdata `UnifiedMap`, which requires the official nuScenes
**map expansion pack** (per-location JSON vector maps under `maps/expansion/`). Iteration 28
staged the trainval metadata + sensor blobs; the map expansion pack was never part of that
staging, and `/datasets/nuscenes-full/maps/` holds only the four bitmap PNGs. The control case
confirms the diagnosis: `scene-0041-medium-01` — the one scheduled `-medium-01` yaml WITHOUT
`load_HD_map: true` — completed both runs cleanly, and no `load_HD_map: false` scenario failed
anywhere in the schedule.

So the registered falsifier fired in its formal (dual-failure) form, but the mechanism is the
third staging-layout defect of this iteration's record (after launch 1's zip-nesting and
3DRealCar-suffix defects), not planner/client instability at subset scale: across both
launches, no episode that actually reached client stepping ever failed. The honest verdict is
still the null — the bars are completion bars, the run is complete, and the bars never move
after data. A successor needs a fresh pre-registration whose staging plan names the nuScenes
map expansion pack for `/datasets/nuscenes-full/maps/expansion/` (an official-download staging
step of the iteration-28 class).

## Descriptive OFF-baseline table (completion accounting + registered plausibility context; NOT a bar)

Aggregate over the 38 completed episodes: mean HD-Score `0.3849`, median `0.2457`, range
`0.0985-0.9558`; per-tier means: easy `0.4355` (n=18), medium `0.3393` (n=20). As registered,
the published RealADSim closed-loop anchor range (~`0.30-0.42`) is loose context only — scene
sets, tiers, and client stacks differ — and the aggregate falling inside it supports no
performance statement. The per-episode table is committed at
[`proof-off/off_baseline_episodes.md`](proof-off/off_baseline_episodes.md).

Within-scenario stochastic spread (the Stage-2 pairing-feasibility measurement, from the 19
complete run pairs):

| scenario | r1 HD | r2 HD | \|ΔHD\| |
|---|---:|---:|---:|
| scene-0013-easy-00 | 0.1677 | 0.1026 | 0.0651 |
| scene-0013-medium-00 | 0.1757 | 0.1757 | 0.0000 |
| scene-0038-easy-00 | 0.3393 | 0.6382 | 0.2988 |
| scene-0038-medium-00 | 0.2237 | 0.2937 | 0.0700 |
| scene-0041-easy-00 | 0.2695 | 0.2511 | 0.0184 |
| scene-0041-medium-00 | 0.2357 | 0.2345 | 0.0013 |
| scene-0041-medium-01 | 0.2548 | 0.2390 | 0.0158 |
| scene-0051-easy-00 | 0.2389 | 0.2267 | 0.0122 |
| scene-0051-medium-00 | 0.2403 | 0.1637 | 0.0766 |
| scene-0062-easy-00 | 0.4925 | 0.1869 | 0.3056 |
| scene-0062-medium-00 | 0.4743 | 0.4487 | 0.0256 |
| scene-0064-easy-00 | 0.7276 | 0.6809 | 0.0466 |
| scene-0064-medium-00 | 0.2404 | 0.2360 | 0.0043 |
| scene-0071-easy-00 | 0.0985 | 0.1228 | 0.0243 |
| scene-0071-medium-00 | 0.4922 | 0.5410 | 0.0488 |
| scene-0138-easy-00 | 0.7554 | 0.7308 | 0.0245 |
| scene-0138-medium-00 | 0.9558 | 0.8662 | 0.0896 |
| scene-0166-easy-00 | 0.8978 | 0.9118 | 0.0140 |
| scene-0166-medium-00 | 0.1459 | 0.1486 | 0.0027 |

Median \|ΔHD\| `0.0245`, mean `0.0602`, max `0.3056`. The registered pairing-infeasibility bar
(median > `0.15`) did NOT fire, but the spread is heavy-tailed: 17/19 pairs sit at or under
`0.09` while two (`scene-0038-easy-00`, `scene-0062-easy-00`) exceed `0.29`. Any future
Stage-2 design has to carry this shape honestly (back-to-back within-launch pairing plus a
scenario-clustered uncertainty treatment, or repeats per arm), and — because this iteration is
a null — that design question belongs to the successor pre-registrations, not to this one.

## Launch-1 defects and the amendment (on the record)

Launch 1 (23:54-23:58 UTC, 2026-07-11) aborted via `I46_OFF_ABORT_CONSECUTIVE_FAILURES` on two
run-script/staging defects, both diagnosed from box evidence and fixed by the recorded
launcher-only amendment (HYPOTHESIS.md amendment note; commit `2af43dd`): (1) 7 of the 19
release scene zips nest under a top-level `nuscenes/` prefix, so extraction landed scene dirs
at the wrong path; (2) the released scenario yamls reference actor assets as
`<car>/postprocess/shadow.pth` while the released 3DRealCar export is flat — upstream strips
the same suffix. No frozen bar, scenario SHA, schedule, or claim boundary changed; the D0
verdict was carried; launch-1 defect evidence is archived under
[`proof-off/prior_launches/`](proof-off/prior_launches). The map-expansion gap above is a
third, distinct staging defect that only manifests at the first `load_HD_map: true` scenario —
position 5 in the schedule — and therefore survived both the iteration-45 smoke and launch 1.

## Successor boundary (registered)

Per the pre-registration, this null authorizes NO Stage-2 pre-registration, no monitor work,
no OFF-vs-ON work, and no transfer claim. The next step on this line requires a fresh
pre-registration that (a) stages the official nuScenes map expansion pack at
`/datasets/nuscenes-full/maps/expansion/` with provenance receipts, and (b) re-runs the failed
portion of the frozen schedule (or the full schedule) under freshly frozen completion bars.
The 38 committed episodes, the stochastic D0 verdict, and the spread table above are evidence
a successor may cite, not results it may skip re-earning where its own bars require more.
