# Iteration 58 - HUGSIM provenance instrumented canary

Frozen before any iteration-58 launcher, analyzer, GPU command, simulator launch, proof artifact,
result, or claim. This is a two-episode instrumentation canary only: not a transfer rerun, not a
metric retune, not an expanded-N experiment, and not an actor-match result.

## Process disclosure

This is not blind. Iterations 48-57 are already published. Before freezing this file, the
iteration-48/49 launch scripts, iteration-49 hard-tier opportunity report, iteration-57 result,
and current handoff were inspected. Those inspections confirmed:

- the GPU box was last recorded idle with no Docker containers;
- the frozen HUGSIM source SHA is `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- the released-union monitor patch SHA is
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`;
- the byte-bound HUGSIM provenance patch SHA is
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`;
- `scene-0013-hard-00__off_r1` had committed iteration-49 primary collision opportunity
  (`nc_min = 0.0`);
- iteration 57 statically verified the byte-identical provenance patch as additive by source
  diff inspection, but did not run HUGSIM.

These inspections are disclosed and allowed as context. This iteration makes no surprise or
performance claim.

## Research question

Can the byte-bound HUGSIM provenance patch be applied on the frozen HUGSIM stack and produce a
top-level `collision_provenance` sidecar in real HUGSIM `eval.json` outputs on a tiny collision
canary, while preserving the scalar metric schema shape?

The purpose is to retire the instrumentation-execution blocker before any future actor-match
audit. This iteration does not answer whether Sentinel hit the right or wrong actor.

## Frozen schedule

Exactly two episodes, in this order, on the existing HUGSIM GPU stack:

1. `scene-0013-hard-00`, monitor OFF, run label `off_r1`;
2. `scene-0013-hard-00`, monitor ON with the released-union patch, run label `on_r1`.

The selected scenario is allowed because committed iteration-49 proof showed its OFF r1 episode had
primary collision opportunity. No other scenario, tier, run index, or retry expansion is authorized
except the standard per-episode retry-once used in iterations 48/49 for infrastructure failure.

## Frozen environment and patches

Hard launch gates:

- HUGSIM source HEAD must equal `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`.
- UniAD_SIM source HEAD must equal `5fb279e39912a5ac7f58e00d56b065cadcd0a749`.
- HUGSIM provenance patch file must hash to
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd` and apply cleanly.
- Released-union monitor patch must hash to
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`.
- Checkpoint, shim, Docker image, scenario YAML SHA, map-expansion JSONs, and carried D0 verdict
  follow the iteration-49 launch gates.
- Single-tenant rule: refuse to start if any Docker container is already running.

The HUGSIM source tree may receive only the byte-bound provenance patch. The UniAD_SIM tree may
receive only the byte-bound released-union monitor patch. No Sentinel thresholds, HUGSIM metric
constants, scenario selection, planner code, action control code, or HD-Score formulas may change.

## Frozen bars

- `CANARY_INFRA_NULL`: any hard launch gate fails, patch application fails, a scheduled episode
  fails both attempts, or proof collection is incomplete.
- `PROVENANCE_CANARY_NULL`: both episodes complete, but neither `eval.json` contains a top-level
  `collision_provenance` list with at least one entry when `nc_min < 1.0`, or provenance is written
  inside scalar `details` rows.
- `PROVENANCE_CANARY_COMPLETE`: both episodes complete; at least one completed `eval.json` has
  `nc_min < 1.0` and a non-empty top-level `collision_provenance` list; scalar top-level metric
  keys remain present (`nc`, `dac`, `ttc`, `c`, `pdms`, `rc`, `hdscore`), `details` rows remain
  scalar-metric-only, and the ON episode carries Sentinel decision logs.

## Forbidden claims

No transfer, benchmark, safety, robustness, deployment, real-world, HD-Score improvement,
HD-Score-invariance, actor-match, collision-cause, production, acquisition-value, or retuning claim.
This canary may only claim whether the byte-bound patch executed and emitted provenance under the
registered two-episode envelope.

## Required proof artifacts

- launcher and analyzer source plus unit tests;
- `proof-canary/receipts.json`;
- `proof-canary/i58-canary-run.log`;
- `proof-canary/episodes/scene-0013-hard-00__off_r1/{eval.json,output.txt,episode_meta.json}`;
- `proof-canary/episodes/scene-0013-hard-00__on_r1/{eval.json,output.txt,episode_meta.json,sentinel_iter48_decisions.jsonl}`;
- `proof-canary/provenance_canary_report.json`;
- `proof-canary/provenance_canary.md`;
- `proof-canary/analyze_provenance_canary.command.txt`;
- `proof-canary/heavy_manifest_iter58.txt` if heavy on-box artifacts are not copied.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add launcher/analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Copy the launcher and byte-bound patch artifacts to the GPU box.
4. Launch exactly the registered two-episode canary, detached, only if the box is idle.
5. Record in HANDOFF/CONTINUITY whether the run is in flight.
6. On done marker: collect proof, commit proof first, run analyzer once, publish `RESULT.md` at
   full weight, update docs/handoff, verify, and push.
