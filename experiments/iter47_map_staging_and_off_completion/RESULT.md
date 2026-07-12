# Iteration 47 - map-expansion staging + HUGSIM OFF-baseline completion: PASS

Status: `OFF_COMPLETION_PASS` (analyzer verdict `PASS_BARS_MET`; carried integrity `104/104` files)

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested exactly as registered: Stage A
staged the official nuScenes Map expansion pack v1.3 under the iteration-28-class provenance
gate (all Stage-A bars passed; receipts committed at
[`proof-staging/staging_receipts.json`](proof-staging/staging_receipts.json)), then the single
registered Stage-B detached run on `sentinel-gpu` re-ran exactly the 14 previously failed
episodes — the seven `load_HD_map: true` `-medium-01` scenarios x 2 back-to-back runs — under
the full re-verified iteration-46 provenance gate
([`proof-completion/receipts.json`](proof-completion/receipts.json): frozen HUGSIM/UniAD_SIM
SHAs, checkpoint SHA `0ad0c2f5…`, shim SHA `5bf69a11…`, image id `f73ef3884063`, all 52
scenario-yaml SHA256s, four map jsons present, carried D0 verdict `stochastic`, `38/38`
carried episodes present). The run launched 05:18:28 UTC and reached
`I47_OFF_COMPLETION_DONE` at 06:29:25 UTC, 2026-07-12, with zero abort markers and no
containers left up. ONE run of the committed analyzer over the committed artifacts then
evaluated the full 52-episode schedule (38 carried + 14 new).

**All registered completion bars passed.**

- **C1 — all 52 episodes complete: PASS.** `52/52` episodes of the frozen stochastic schedule
  (26 scenarios x 2) terminated by the benchmark's own rule with a finite `hdscore`. All 14
  new episodes completed on attempt 1 (`retried_episodes = 0` across the full schedule); new
  episode wall clocks 102-509 s, all far inside the 1200 s bound.
- **C2 — per-step logs for all 52: PASS.** Every episode dir has `output.txt` round-trip
  lines and a positive step count in `episode_meta.json` (new episodes: 9-156 steps); heavy
  per-step records stay on the box behind
  [`proof-completion/heavy_manifest_iter47.txt`](proof-completion/heavy_manifest_iter47.txt).
- **C3 — evidence committed, carried integrity intact: PASS.** Stage-A receipts, launch
  receipts, the full run log, the 14 new episode artifact sets, the heavy manifest, the
  carried-integrity output, and the analyzer report are committed (no file over 90 MB). The
  analyzer verified all `104` carried+new `eval.json`/`episode_meta.json` files byte-identical
  (SHA256) between the committed artifacts and the on-box collection root
  ([`proof-completion/carried_integrity.json`](proof-completion/carried_integrity.json)):
  the 38 iteration-46 episodes were scored exactly as committed, not silently re-scored.
- **Pairing-infeasibility falsifier (re-evaluated over ALL 26 pairs): NOT FIRED.** Median
  within-scenario |dHD| = `0.0251`, far under the frozen `0.15` bar. The heavy tail is real
  and worse than the 19-pair view (see the table), and it binds the Stage-2 design.
- Crash/deadlock loop, VRAM overflow, disk exhaustion: none fired (zero `I47_OFF_ABORT_*`
  markers, no CUDA OOM in the log, disk guard held).

**Re-earned, not repaired (binding framing).** Iteration 46's null stands exactly as
published: its C1 bar failed, its crash-loop falsifier fired, and nothing here changes that
record. Iteration 47 re-earned completion under its own fresh pre-registration and fresh bars;
the mechanism iteration 46 diagnosed (the unstaged map-expansion pack) was confirmed by cure —
after Stage A, all seven formerly dual-failing `load_HD_map: true` scenarios completed both
runs on the first attempt, and no new failure mechanism appeared anywhere in the schedule.

Claim boundary (registered, binding): this is the **OFF arm only**. No transfer, monitor,
OFF-vs-ON, benchmark-ranking, robustness, deployment, or safety claim; no UniAD performance
ranking; the HD-Score numbers below are completion accounting and the registered plausibility
context only. This pass authorizes exactly ONE thing: the iteration-48 Stage-2
OFF-vs-released-union pre-registration. It does not authorize the Stage-2 runs. The
iteration-39 wording rules apply.

Harness:

- [`stage_map_expansion.py`](stage_map_expansion.py) (Stage A),
  [`run_completion.sh`](run_completion.sh) (box-side Stage B),
  [`analyze_completion.py`](analyze_completion.py) (offline, run ONCE; wraps the committed
  iteration-46 analyzer for the full-52 evaluation plus the carried-integrity check)
- [`../../tests/test_iter47_completion.py`](../../tests/test_iter47_completion.py)

Primary evidence:

- [`proof-completion/off_completion_report.json`](proof-completion/off_completion_report.json)
  (the single analyzer run; command receipt in
  [`proof-completion/analyze_completion.command.txt`](proof-completion/analyze_completion.command.txt))
- [`proof-completion/episodes/`](proof-completion/episodes) (the 14 new episodes'
  `eval.json`, `output.txt`, `episode_meta.json`; zero `__failed` dirs this run)
- [`proof-completion/i47-completion-run.log`](proof-completion/i47-completion-run.log) (full
  box-side run log with `I47_OFF_EP_START`/`I47_OFF_EP_RC`/`I47_OFF_EP_DONE` markers and the
  final `I47_OFF_COMPLETION_DONE`)
- [`proof-completion/box_episode_hashes.txt`](proof-completion/box_episode_hashes.txt)
  (on-box SHA256 over `eval.json`/`episode_meta.json` for all 52 episode dirs)
- [`proof-completion/off_completion_episodes.md`](proof-completion/off_completion_episodes.md)
  (per-episode table over all 52)
- Carried arm: the 38 iteration-46 episodes at
  [`../iter46_hugsim_off_baseline/proof-off/episodes/`](../iter46_hugsim_off_baseline/proof-off/episodes)

## Verdict

| gate | result |
|---|---|
| S0 provenance | **PASS**: HYPOTHESIS committed alone (`ced26df`) before tooling (`ab7bf22`); Stage A executed and receipts committed (`dc25fa0`) before Stage B launch; launch provenance gate `I47_OFF_PROVENANCE_OK` (every frozen iteration-46 value re-verified + the four map jsons + carried D0 verdict + 38/38 carried episodes); single-tenant rule held |
| Stage A staging gate | **PASS**: archive `398,535,531` bytes (inside the 0.1-2 GB sanity range), SHA256 recorded, redacted public-bucket provenance (no secret material), `13` zip members `0` unsafe, extraction into `/datasets/nuscenes-full/maps/` only, all four `expansion/*.json` vector maps present (8.2-16.2 MB each), free-space preflight held |
| C1 all 52 episodes complete | **PASS**: `52/52`, `retried_episodes = 0`; the 14 new episodes all completed on attempt 1, wall clock 102-509 s (bound 1200 s) |
| C2 per-step logs captured | **PASS**: `output.txt` round-trip logs + positive step counts for all 52 (new episodes 9-156 steps, median 83); heavy artifacts behind the committed SHA manifest |
| C3 evidence committed + carried integrity | **PASS**: all artifacts committed (largest file well under 90 MB, no split needed); carried-integrity check `104/104` files byte-identical, `0` mismatches |
| Falsifier: pairing infeasibility (26 pairs) | **NOT fired**: median within-scenario \|dHD\| = `0.0251` (bar `0.15`) |
| Falsifier: crash/deadlock loop | not fired (`0` dual failures, `0` consecutive-failure aborts) |
| Falsifier: VRAM overflow | not fired (no CUDA OOM in the run log) |
| Falsifier: disk exhaustion | not fired (guard before every episode; no `I47_OFF_ABORT_DISK`) |
| Budget | Stage B spent ~`1.2` GPU-hours (sum of episode walls 4,229 s + prep), inside the expected 1-2.5 and far under the ~5.1 ceiling |

## The full 52-episode OFF-baseline table (completion accounting + registered plausibility context; NOT a bar)

Aggregate over all 52 episodes: mean HD-Score `0.3607`, median `0.2553`, range
`0.0000-0.9558`; per-tier means: easy `0.4355` (n=18), medium `0.3211` (n=34). As registered,
the published RealADSim closed-loop anchor range (~`0.30-0.42`) is loose context only — scene
sets, tiers, and client stacks differ — and the aggregate falling inside it supports no
performance statement. The per-episode table is committed at
[`proof-completion/off_completion_episodes.md`](proof-completion/off_completion_episodes.md).

Per-scenario HD with within-scenario stochastic spread — all 26 pairs, every pair produced
back-to-back within a single launch (19 carried from iteration 46, 7 new from this run). This
is the Stage-2 pairing evidence:

| scenario | r1 HD | r2 HD | \|dHD\| |
|---|---:|---:|---:|
| scene-0013-easy-00 | 0.1677 | 0.1026 | 0.0651 |
| scene-0013-medium-00 | 0.1757 | 0.1757 | 0.0000 |
| scene-0038-easy-00 | 0.3393 | 0.6382 | 0.2988 |
| scene-0038-medium-00 | 0.2237 | 0.2937 | 0.0700 |
| scene-0038-medium-01 * | 0.3610 | 0.4946 | 0.1336 |
| scene-0041-easy-00 | 0.2695 | 0.2511 | 0.0184 |
| scene-0041-medium-00 | 0.2357 | 0.2345 | 0.0013 |
| scene-0041-medium-01 | 0.2548 | 0.2390 | 0.0158 |
| scene-0051-easy-00 | 0.2389 | 0.2267 | 0.0122 |
| scene-0051-medium-00 | 0.2403 | 0.1637 | 0.0766 |
| scene-0051-medium-01 * | 0.2558 | 0.2940 | 0.0382 |
| scene-0062-easy-00 | 0.4925 | 0.1869 | 0.3056 |
| scene-0062-medium-00 | 0.4743 | 0.4487 | 0.0256 |
| scene-0062-medium-01 * | 0.0000 | 0.0000 | 0.0000 |
| scene-0064-easy-00 | 0.7276 | 0.6809 | 0.0466 |
| scene-0064-medium-00 | 0.2404 | 0.2360 | 0.0043 |
| scene-0064-medium-01 * | 0.3876 | 0.3435 | 0.0442 |
| scene-0071-easy-00 | 0.0985 | 0.1228 | 0.0243 |
| scene-0071-medium-00 | 0.4922 | 0.5410 | 0.0488 |
| scene-0071-medium-01 * | 0.0402 | 0.0302 | 0.0100 |
| scene-0138-easy-00 | 0.7554 | 0.7308 | 0.0245 |
| scene-0138-medium-00 | 0.9558 | 0.8662 | 0.0896 |
| scene-0138-medium-01 * | 0.9378 | 0.1959 | 0.7419 |
| scene-0166-easy-00 | 0.8978 | 0.9118 | 0.0140 |
| scene-0166-medium-00 | 0.1459 | 0.1486 | 0.0027 |
| scene-0166-medium-01 * | 0.4037 | 0.3865 | 0.0171 |

`*` = the 7 new pairs from this iteration's Stage-B run.

Median |dHD| `0.0251`, mean `0.0819`, max `0.7419` over the 26 pairs. The registered
pairing-infeasibility bar (median > `0.15`) did NOT fire, but the full-set spread is MORE
heavy-tailed than the 19-pair view iteration 46 measured: 22/26 pairs sit at or under `0.09`,
while four pairs — `scene-0038-easy-00` (`0.2988`), `scene-0062-easy-00` (`0.3056`),
`scene-0038-medium-01` (`0.1336`), and above all `scene-0138-medium-01` (`0.7419`, r1 `0.9378`
vs r2 `0.1959`) — show that a single stochastic replay pair can swing by most of the score
range. Two descriptive observations for the record (context, not bars):
`scene-0062-medium-01` completed both runs by the benchmark's own rule at 9 steps with
HD-Score exactly `0.0000` both times — a valid, finite, completed episode under C1; and the
`scene-0138-medium-01` pair is the new spread maximum. Any Stage-2 paired design must carry
this shape explicitly: back-to-back within-launch pairing, a scenario-clustered uncertainty
treatment over paired deltas, and a stated heavy-tail policy. That requirement is written into
the iteration-48 pre-registration this pass authorizes.

## Successor boundary (registered)

Per the pre-registration, this pass authorizes exactly ONE next step: the iteration-48 Stage-2
OFF-vs-released-union transfer-gate pre-registration
(per [`docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md`](../../docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md)),
committed alone before any Stage-2 tooling or run. The complete, provenance-locked 52-episode
OFF arm, the stochastic D0 verdict, and the 26-pair spread table above are the evidence base
that pre-registration builds on. No Stage-2 run happens under iteration 47.
