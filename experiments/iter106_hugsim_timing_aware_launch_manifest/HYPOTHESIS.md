# Iteration 106 - HUGSIM timing-aware launch manifest preflight

Frozen after iteration 105 was published, but before any iteration-106 analyzer, generated
manifest, result, launcher, GPU command, proof artifact, handoff update, or claim. This is an
offline launch-manifest preflight only. It does not authorize a HUGSIM run.

## Context

Iteration 104 proved that the first 13-slot provenance batch was valid instrumentation/execution
proof but weak actor-match support: only `1/13` slots was foreground-classifiable. Iteration 105
then redesigned the future batch around timing-aware support yield, selecting `13` rows where the
released union fired at or before first ON collision time. The selected schedule has `11` unique
scenarios and two intentional duplicate scenario groups:

- `scene-0138-medium-01` runs `1` and `2`;
- `scene-0064-hard-00` runs `2` and `1`.

This iteration tests whether that timing-aware schedule can be made launch-ready from committed
artifacts alone. As in iteration 102, the key failure mode is slot collapse: repeated scenarios
must remain distinct execution slots keyed by `slot_id`, not by scenario.

## Research question

Can the iteration-105 timing-aware candidate schedule be converted into a deterministic,
byte-bound future-run manifest whose `13` execution slots each have:

1. a stable slot id and one-based slot index;
2. the selected dataset, scenario, run index, tier, channel, timing label, lead time, and
   selection reason;
3. the committed scenario YAML SHA256 from the correct frozen iteration-48 or iteration-49
   scenario manifest;
4. the frozen HUGSIM/UniAD/checkpoint/shim/Docker/patch gate receipts carried from iteration 59;
5. an explicit duplicate-slot policy that preserves repeated scenarios as separate execution
   slots?

## Frozen inputs

- Iteration 105 timing-aware design report:
  `experiments/iter105_hugsim_timing_aware_provenance_batch_design/proof-design/timing_aware_provenance_batch_design_report.json`
- Iteration 48 scenario manifest:
  `experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256`
- Iteration 49 scenario manifest:
  `experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256`
- Iteration 59 stack receipts:
  `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json`
- Iteration 59 launcher:
  `experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh`

The analyzer may read these files only. It may not read raw episode directories, raw decision
logs, new box state, live GPU state, scenario YAML contents outside the committed manifests, or
uncommitted files.

## Frozen expected stack gates

- HUGSIM source SHA:
  `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`
- UniAD_SIM source SHA:
  `5fb279e39912a5ac7f58e00d56b065cadcd0a749`
- checkpoint SHA:
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`
- shim SHA:
  `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c`
- Docker image id:
  `f73ef3884063`
- HUGSIM provenance patch SHA:
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`
- released-union monitor patch SHA:
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`
- episode timeout from the iteration-59 launcher: `1200`
- minimum disk guard from the iteration-59 launcher: `20` GiB

## Frozen bars

- `HUGSIM_TIMING_AWARE_LAUNCH_MANIFEST_BLOCKED`: any frozen input is missing or malformed;
  iteration 105 is not `HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE`; selected slot count is not
  `13`; selected unique scenario count is not `11`; selected timing/channel/dataset/tier counts
  do not match the iteration-105 summary; any selected row is missing a scenario SHA in the
  correct source manifest; any frozen stack gate receipt or launcher constant is missing or
  mismatched; slot ids are not unique; slot indexes are not exactly `1..13`; or duplicate
  scenarios are not explicitly preserved as duplicate execution slots.
- `HUGSIM_TIMING_AWARE_LAUNCH_MANIFEST_COMPLETE`: all blocked conditions are false, the manifest
  contains exactly `13` execution slots, exactly `11` unique scenarios, exactly `2` duplicate
  scenario groups, `13/13` slots have scenario SHA bindings, and every duplicate scenario keeps
  distinct `(scenario, run, slot_id)` tuples.

## Duplicate-slot policy

Slot id, not scenario id, is the primary execution key for any future launcher. Destination paths,
done markers, retry state, and collection checks must include the slot id. Repeated scenarios are
intentional because iteration 105 selected specific committed scenario/run rows; they must not be
deduplicated.

## Required proof artifacts

- `HYPOTHESIS.md`
- analyzer source plus unit tests
- `proof-launch-manifest/timing_aware_launch_manifest_report.json`
- `proof-launch-manifest/timing_aware_launch_manifest.md`
- `proof-launch-manifest/timing_aware_launch_manifest.json`
- `proof-launch-manifest/analyze_timing_aware_launch_manifest.command.txt`

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer and tests.
3. Run targeted lint/tests and `python3 scripts/validate_docs.py`.
4. Run the analyzer once over committed inputs.
5. Publish `RESULT.md`, update docs and handoff only after the manifest result exists.
6. Run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py` before the final
   state commit.

## Forbidden claims

No GPU approval, no launch authorization, no actor-causality, no actor-match result, no repair,
no threshold-value, no transfer, no safety, no deployment, no robustness, no benchmark,
no population-rate, no HD-Score-invariance, no real-world behavior, no acquisition-value,
no retuning, no production, and no commercial claim. This iteration may claim only whether the
future timing-aware run manifest is launch-ready as a frozen offline artifact.
