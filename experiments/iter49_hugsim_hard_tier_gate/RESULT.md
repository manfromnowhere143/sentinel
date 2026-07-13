# Iteration 49 - HUGSIM hard/extreme-tier transfer gate: TRANSFER_NULL

Status: `TRANSFER_NULL` (analyzer verdict; K1/K2 passed, F1 void check passed,
no registered falsifier fired) - published at full weight as the hard/extreme-tier,
collision-regime transfer answer for the released union.

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested exactly as registered:
the single detached 104-episode run (26 hard/extreme scenarios x 2 runs x 2 arms,
within-launch back-to-back pairing `OFF r1 -> ON r1 -> OFF r2 -> ON r2` under
the carried stochastic D0 verdict) launched on `sentinel-gpu` at 17:16:54 UTC
and reached `I49_HARD_DONE` at 23:12:34 UTC on 2026-07-12. There were zero
`I49_ABORT_*` markers, zero failed episode directories, zero retries, and no
Docker containers left up when the run was recovered. Proof was collected and
committed FIRST (`2eb0c81`); ONE run of the committed analyzer over the committed
artifacts then produced the verdict.

## The Verdict

The frozen released union **operates** on the harder tiers: `40/52` ON episodes
received a brake intervention, with `275` fired frames, `526` brake frames
(`22.3%` of `2,354` monitored frames), and `58` latch releases. It still produces
no detectable HD-Score gain:

| primary metric | value |
|---|---:|
| mean paired HD-Score delta, ON - OFF | **-0.0089** |
| 95% scenario-clustered bootstrap CI | **[-0.0438, +0.0203]** |
| clusters / pairs / draws / seed | 26 / 52 / 10,000 / 49 |
| median paired delta | **+0.0011** |
| median 95% CI | **[-0.0077, +0.0105]** |

The registered primary CI includes zero. The collision-dominant hard/extreme
extension therefore does **not** re-establish the NeuroNCAP benefit. This is a
null, not a void and not a completion failure.

## Completion And Evidence

| gate | result |
|---|---|
| S0 provenance | **PASS**: pre-launch asset pre-check passed, `I49_PRECHECK_OK`; full provenance gate passed, `I49_PROVENANCE_OK`; carried D0 verdict `stochastic`; single-tenant rule held |
| F1 retuning void | **NOT fired**: `monitor_patch_sha = 6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`, byte-identical to the committed iteration-48 patch; seven frozen parameters matched receipts and all ON decision rows |
| K1 all 104 complete | **PASS**: `104/104`, `0` retries, `0` dual failures, finite `hdscore` for every episode |
| K2 per-step + decision logs | **PASS**: all 104 `output.txt` step logs; all 52 ON `sentinel_iter48_decisions.jsonl`; `0` trace-error rows |
| K3 evidence committed | **PASS**: receipts, run log, box hashes, all 104 episode artifact sets, all ON decision logs, heavy manifest, single analyzer report; no file over 90 MB |

Harness:

- [`run_hard_tier_gate.sh`](run_hard_tier_gate.sh) - box-side launcher, frozen schedule,
  pre-check/provenance gates, retry/disk/consecutive-failure guards.
- [`analyze_hard_tier.py`](analyze_hard_tier.py) - offline analyzer, run once.
- [`../../tests/test_iter49_hard_tier.py`](../../tests/test_iter49_hard_tier.py)

Primary evidence:

- [`proof-hard/transfer_report.json`](proof-hard/transfer_report.json) - the single
  analyzer run; command receipt in
  [`proof-hard/analyze_hard_tier.command.txt`](proof-hard/analyze_hard_tier.command.txt).
- [`proof-hard/transfer_pairs.md`](proof-hard/transfer_pairs.md) - all 52 paired deltas.
- [`proof-hard/receipts.json`](proof-hard/receipts.json) - launch provenance gate,
  monitor-patch SHA, frozen-param echo, carried D0 verdict.
- [`proof-hard/episodes/`](proof-hard/episodes) - 104 episode dirs: `eval.json`,
  `output.txt`, `episode_meta.json`, ON-arm `sentinel_iter48_decisions.jsonl`.
- [`proof-hard/i49-hard-run.log`](proof-hard/i49-hard-run.log) - full box-side log and
  final `I49_HARD_DONE`.
- [`proof-hard/box_episode_hashes.txt`](proof-hard/box_episode_hashes.txt) - on-box
  SHA256 over `eval.json` / `episode_meta.json` for all 104 dirs.
- [`proof-hard/heavy_manifest_iter49.txt`](proof-hard/heavy_manifest_iter49.txt) -
  heavy pickles/videos stay on the box.

## Falsifiers

| falsifier | result |
|---|---|
| F1 - retuning void | **NOT fired**: patch SHA and all parameter rows match the frozen iteration-48 copy |
| F2 - splat-noise mistuning | **NOT fired**: brake-frame fraction `22.3%`, under the `80%` over-fire bar; fired frames `275`, so the never-fire direction is also false |
| F3 - RC collapse | **NOT fired**: mean paired RC delta `-0.0403`, far above the `-0.30` bar |
| F4 - crash/deadlock loop | **NOT fired**: `0` dual-failure episodes, no consecutive-failure abort |
| F5 - pairing infeasibility | **NOT fired**: fresh hard/extreme OFF-OFF median \|dHD\| `0.0113`, below the `0.15` bar |
| F6 - VRAM/disk exhaustion | **NOT fired**: no OOM, no disk abort; data disk retained `122G` free at recovery |
| F7 - staging gap | **NOT fired**: pre-launch maps/scenes/assets gate passed; the scheduled new scenes extracted and ran |

No step-cap episode occurred. The localized over-braking watch is still visible: the largest
ON brake fractions were `scene-0071-extreme-00__on_r1` at `70.3%`, then
`scene-0051-hard-00__on_r1` at `58.7%` and `scene-0051-hard-00__on_r2` at `53.8%`.
Unlike iteration 48's `scene-0051` r1 pair, this did not become a step-cap or pooled
RC-collapse result.

## Secondaries (Descriptive, Not Bars)

Mean paired term deltas over 52 pairs:

| term | mean delta, ON - OFF | median delta |
|---|---:|---:|
| NC | +0.0442 | +0.0263 |
| DAC | +0.0108 | 0.0000 |
| TTC | +0.0631 | +0.0576 |
| comfort | +0.1184 | +0.1148 |
| RC | -0.0403 | -0.0172 |

Descriptive tier split, not powered for a tier claim:

| tier | pairs | mean HD delta | median HD delta |
|---|---:|---:|---:|
| hard | 26 | +0.0011 | +0.0029 |
| extreme | 26 | -0.0189 | -0.0012 |

The NC/TTC/comfort components move positive on average, while RC moves mildly negative;
the registered HD-Score primary still resolves to a null. The tier split is context only.

## Iteration 50 P1 Resolution

Iteration 50 froze P1 while this run was in flight and unread. Applying the registered
primary-opportunity definition to iteration 49's OFF arm (`nc_min < 1.0` over top-level
`nc` and all `details.*.nc`) gives:

| P1 field | value |
|---|---:|
| OFF episodes | 52 |
| primary collision-opportunity episodes | **51** |
| opportunity fraction | **0.9808** |
| threshold | 13/52 = 0.25 |
| iter49 transfer verdict | `TRANSFER_NULL` |
| P1 branch | **Branch B - REFUTED** |

The conclusion bound by the frozen P1 text is therefore: opportunity is present, but the
benefit does not port. The transfer failure is real, not opportunity-scarce. The report is
committed in [`proof-hard/p1_opportunity_report.json`](proof-hard/p1_opportunity_report.json)
with the command receipt in
[`proof-hard/p1_opportunity.command.txt`](proof-hard/p1_opportunity.command.txt).

## Scope Boundary

This is a HUGSIM hard/extreme-tier transfer measurement of the frozen-parameter released
union on the same frozen UniAD checkpoint. It makes no NeuroNCAP-equivalence claim:
HD-Score and NeuroNCAP score are different metrics over different scene families. It makes
no deployment, real-world, production, or safety claim; no benchmark-ranking or
UniAD-performance claim; no monitor-robustness claim; no hard-vs-extreme tier claim; and
no generalization beyond the registered 26 scenarios and UniAD-class planner surface. The
iteration-39 wording rules remain binding.

## Successor Boundary

The hard/extreme successor question is answered: even with collision opportunity present
in `51/52` OFF episodes, the released union's NeuroNCAP benefit does not measurably port to
HUGSIM at this N. Any next step requires a fresh pre-registration. Natural successor shapes
are now narrower: mechanism-cause taxonomy for why HUGSIM collisions are not converted,
expanded-N confirmation only if a tighter CI is worth the GPU spend, or a new rule family
that is explicitly not retuning this frozen released union.
