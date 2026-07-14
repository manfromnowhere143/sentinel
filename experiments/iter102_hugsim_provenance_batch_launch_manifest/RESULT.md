# Iteration 102 - HUGSIM provenance batch launch manifest preflight: HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE

Status: `HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE` (offline launch-manifest preflight
for the future collision-provenance-instrumented HUGSIM batch).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, raw `eval.json` files, or raw episode directories, and
did not retune Sentinel. It used only the committed iteration-101 candidate report, iteration-48
and iteration-49 frozen scenario SHA manifests, and iteration-59 frozen stack receipts/launcher.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_provenance_batch_launch_manifest.py`](analyze_provenance_batch_launch_manifest.py)
- Tests:
  [`../../tests/test_iter102_provenance_batch_launch_manifest.py`](../../tests/test_iter102_provenance_batch_launch_manifest.py)
- Analyzer command:
  [`proof-launch-manifest/provenance_batch_launch_manifest.command.txt`](proof-launch-manifest/provenance_batch_launch_manifest.command.txt)
- JSON report:
  [`proof-launch-manifest/provenance_batch_launch_manifest_report.json`](proof-launch-manifest/provenance_batch_launch_manifest_report.json)
- Machine launch manifest:
  [`proof-launch-manifest/provenance_batch_launch_manifest.json`](proof-launch-manifest/provenance_batch_launch_manifest.json)
- Markdown launch manifest:
  [`proof-launch-manifest/provenance_batch_launch_manifest.md`](proof-launch-manifest/provenance_batch_launch_manifest.md)

## Result

The analyzer cross-checked:

- iteration-101 verdict: `HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE`;
- iteration-101 selected counts: `13` total rows, `12` new candidate rows, `1` carried
  singleton row;
- all seven candidate-design strata remain covered;
- every selected row has a scenario SHA in the correct frozen manifest source:
  iteration 48 for `iter48_easy_medium`, iteration 49 for `iter49_hard_extreme`;
- iteration-59 stack receipts match the frozen HUGSIM, UniAD_SIM, checkpoint, shim, Docker image,
  HUGSIM provenance patch, and released-union monitor patch identifiers;
- iteration-59 launcher constants match `EPISODE_TIMEOUT=1200` and `DISK_MIN_GIB=20`;
- slot ids are unique and slot indexes are exactly `1..13`;
- repeated scenarios are preserved as distinct execution slots.

Summary:

- launch slots: `13`;
- new candidate slots: `12`;
- carried singleton slots: `1`;
- scenario SHA-bound slots: `13`;
- unique scenarios: `9`;
- duplicate scenario groups: `4`;
- duplicate slots: `8`.

Duplicate scenario groups:

- `scene-0013-easy-00`: slots `1-2`;
- `scene-0051-easy-00`: slots `5-6`;
- `scene-0013-extreme-00`: slots `9-10`;
- `scene-0038-hard-00`: slots `11-12`.

## Interpretation

Iteration 102 turns the iteration-101 prose schedule into a launch-manifest artifact. The key
engineering point is that a future launcher must key execution, destination paths, retry state,
done markers, and collection checks by `slot_id`, not by `scenario`.

The batch has `13` selected row/run slots but only `9` unique scenario YAML files. That is
intentional. Scenario-level deduplication would silently erase four repeated-scenario pairs and
would invalidate the candidate schedule. The manifest therefore makes `slot_id` the primary
execution key and records `scenario_deduplication_allowed=false`.

This result makes the future run easier to launch correctly. It does not authorize launching it.

## Claim boundary

Offline launch-manifest preflight only; no GPU approval, launch authorization, actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, acquisition-value, or retuning claim.
