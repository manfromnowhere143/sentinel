# Iteration 102 - HUGSIM provenance batch launch manifest preflight

Frozen before any iteration-102 analyzer, generated manifest, result, handoff update, GPU launch,
or claim. This is an offline launch-manifest preflight only. It does not authorize a HUGSIM run.

## Context

Iteration 100 found that the existing committed reports cannot expand the structural bridge beyond
the five actor-match rows without new collision-provenance instrumentation. Iteration 101 then
froze a 13-row candidate schedule for that future instrumented batch: 12 new candidate rows plus
the one carried both-distinct singleton reference row.

This iteration tests whether that schedule can be made launch-ready from committed artifacts alone.
The specific risk is slot collapse: the schedule has 13 row/run slots but only 9 unique scenarios.
A future launcher that keys completion or destination directories only by scenario would silently
erase repeated run slots. The manifest must therefore preserve slot identity as the primary unit of
execution.

## Research question

Can the iteration-101 candidate schedule be converted into a deterministic, byte-bound future-run
manifest whose 13 execution slots each have:

1. a stable slot id and one-based slot index;
2. the selected dataset, scenario, run index, tier, stratum, timing label, and selection role;
3. the committed scenario YAML SHA256 from the correct frozen iteration-48 or iteration-49
   scenario manifest;
4. the frozen HUGSIM/UniAD/checkpoint/shim/Docker/patch gate receipts carried from iteration 59;
5. an explicit duplicate-slot policy that preserves repeated scenarios as separate execution slots?

## Frozen inputs

- Iteration 101 candidate report:
  `experiments/iter101_hugsim_provenance_batch_candidate_design/proof-design/provenance_batch_candidate_design_report.json`
- Iteration 48 scenario manifest:
  `experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256`
- Iteration 49 scenario manifest:
  `experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256`
- Iteration 59 stack receipts:
  `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json`
- Iteration 59 launcher:
  `experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh`

The analyzer may read these files only. It may not read raw episode directories, raw decision logs,
new box state, live GPU state, or uncommitted files.

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

- `HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED`: any frozen input is missing or malformed;
  iteration 101 is not `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE`; selected total/new/
  carried counts differ from `13/12/1`; not all seven strata are covered; any selected row is
  missing a scenario SHA in the correct source manifest; any frozen stack gate receipt or launcher
  constant is missing or mismatched; slot ids are not unique; slot indexes are not exactly
  `1..13`; or duplicate scenarios are not explicitly preserved as duplicate execution slots.
- `HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE`: all blocked conditions are false, the
  manifest contains exactly 13 execution slots, exactly 9 unique scenarios, exactly 4 scenarios
  with duplicate slots, and every duplicate scenario keeps distinct `(scenario, run, slot_id)`
  tuples.

## Duplicate-slot policy

Slot id, not scenario id, is the primary execution key for any future launcher. Destination paths,
done markers, retry state, and collection checks must include the slot id. Repeated scenarios are
intentional because iteration 101 selected specific committed scenario/run rows; they must not be
deduplicated.

## Required proof artifacts

- `HYPOTHESIS.md`
- analyzer source plus unit tests
- `proof-launch-manifest/provenance_batch_launch_manifest_report.json`
- `proof-launch-manifest/provenance_batch_launch_manifest.md`
- `proof-launch-manifest/provenance_batch_launch_manifest.json`
- `proof-launch-manifest/provenance_batch_launch_manifest.command.txt`

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer and tests.
3. Run `ruff check .`, targeted tests, and the analyzer once.
4. Publish `RESULT.md`, update docs and handoff only after the manifest result exists.
5. Run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py` before the final
   state commit.

## Forbidden claims

No GPU approval, no launch authorization, no actor-causality, no repair, no threshold-value,
no transfer, no safety, no deployment, no robustness, no benchmark, no population-rate,
no HD-Score-invariance, no real-world behavior, no acquisition-value, and no retuning claim.
This iteration may claim only whether the future-run manifest is launch-ready as a frozen offline
artifact.
