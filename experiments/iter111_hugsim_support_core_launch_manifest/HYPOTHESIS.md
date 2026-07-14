# Iteration 111 - HUGSIM support-core launch manifest preflight

Frozen after iteration 110 was published and the handoff was refreshed, but before any
iteration-111 analyzer, generated manifest, result, launcher, GPU command, proof artifact, handoff
update, or claim. This is an offline launch-manifest preflight for the iteration-110
support-preserving core only. It does not authorize a HUGSIM run.

## Context

Iteration 110 found a deterministic `8`-row support-preserving core after the iteration-109
residual split. The core is all `ttc_only`, contains `3` exact TTC classifiable anchors and `5`
TTC scenario-level classifiable analogues, and clears the frozen four-row actor-match support
floor. Iteration 110 also proved that a clean `13`-slot support-preserving schedule is not
available from the committed pool: filling to `13` would require residual-risk TTC rows or CPA
fallback rows.

This iteration tests only whether the `8` support-preserving core rows can be converted into a
byte-bound future-run manifest with the same slot-id discipline used by earlier HUGSIM launch
manifests.

## Research question

Can the iteration-110 support-preserving core be converted into a deterministic future-run
manifest whose `8` execution slots each have:

1. a stable slot id and one-based slot index;
2. the selected dataset, scenario, run index, tier, channel, timing label, lead time, and
   design label;
3. the committed scenario YAML SHA256 from the correct frozen iteration-48 or iteration-49
   scenario manifest;
4. the frozen HUGSIM/UniAD/checkpoint/shim/Docker/patch gate receipts carried from iteration 59;
5. an explicit duplicate-slot policy that preserves repeated scenarios as separate execution
   slots?

## Frozen inputs

The analyzer may read only these committed files:

- Iteration 110 support-preserving candidate design report:
  `experiments/iter110_hugsim_support_preserving_candidate_design/proof-design/support_preserving_candidate_design_report.json`
- Iteration 48 scenario manifest:
  `experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256`
- Iteration 49 scenario manifest:
  `experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256`
- Iteration 59 stack receipts:
  `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json`
- Iteration 59 launcher:
  `experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh`

The analyzer may not read raw episode directories, raw decision logs, new box state, live GPU
state, scenario YAML contents outside the committed manifests, launch artifacts generated after
this pre-registration, or uncommitted files.

## Frozen expected core

The iteration-110 report must have:

- verdict `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE`;
- `support_preserving_core_count == 8`;
- `full_13_support_preserving_available == false`;
- `core_channel_counts == {'ttc_only': 8}`;
- `core_timing_counts == {'long_lead_fire': 3, 'short_lead_fire': 5}`;
- `exact_ttc_classifiable_anchor_count == 3`;
- `ttc_classifiable_scenario_analogue_count == 5`.

The manifest summary must preserve these exact core counts:

- slot count: `8`;
- unique scenario count: `5`;
- duplicate scenario group count: `3`;
- scenario SHA-bound count: `8`;
- dataset counts: `{'iter49_hard_extreme': 8}`;
- channel counts: `{'ttc_only': 8}`;
- tier counts: `{'extreme': 5, 'hard': 3}`;
- timing counts: `{'long_lead_fire': 3, 'short_lead_fire': 5}`;
- design-label counts:
  `{'exact_ttc_classifiable_anchor': 3, 'ttc_classifiable_scenario_analogue': 5}`.

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

- `HUGSIM_SUPPORT_CORE_LAUNCH_MANIFEST_BLOCKED`: any frozen input is missing or malformed;
  iteration 110 is not `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE`; the frozen
  core counts above do not match; any support-core row is missing required fields; any selected
  row is missing a scenario SHA in the correct source manifest; any frozen stack gate receipt or
  launcher constant is missing or mismatched; slot ids are not unique; slot indexes are not
  exactly `1..8`; duplicate scenarios are not explicitly preserved as duplicate execution slots;
  or the manifest includes any row outside the iteration-110 support-preserving core.
- `HUGSIM_SUPPORT_CORE_LAUNCH_MANIFEST_COMPLETE`: all blocked conditions are false, the manifest
  contains exactly `8` execution slots, exactly `5` unique scenarios, exactly `3` duplicate
  scenario groups, `8/8` slots have scenario SHA bindings, every duplicate scenario keeps
  distinct `(scenario, run, slot_id)` tuples, and every slot is traceable to one iteration-110
  support-preserving core row.

## Duplicate-slot policy

Slot id, not scenario id, is the primary execution key for any future launcher. Destination paths,
done markers, retry state, and collection checks must include the slot id. Repeated scenarios are
intentional because iteration 110 selected specific committed scenario/run rows; they must not be
deduplicated.

## Required proof artifacts

- `HYPOTHESIS.md`
- analyzer source plus unit tests
- `proof-launch-manifest/support_core_launch_manifest_report.json`
- `proof-launch-manifest/support_core_launch_manifest.md`
- `proof-launch-manifest/support_core_launch_manifest.json`
- `proof-launch-manifest/analyze_support_core_launch_manifest.command.txt`

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
future `8`-slot support-core manifest is launch-ready as a frozen offline artifact.
