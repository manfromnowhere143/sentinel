# Iteration 126 - support-core candidate-generation manifest preflight: SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE

Status: `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE` (offline manifest
preflight over the committed iteration-125 blind-spot design surface).

This iteration used only committed markdown/json result surfaces. It read no raw decision logs,
launched no GPU work, generated no scenarios, selected no execution slots, changed no thresholds,
changed no planner/action-control code, changed no HUGSIM metrics, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Generator/verifier:
  [`generate_support_core_candidate_manifest.py`](generate_support_core_candidate_manifest.py)
- Tests:
  [`../../tests/test_iter126_support_core_candidate_manifest.py`](../../tests/test_iter126_support_core_candidate_manifest.py)
- Generator command:
  [`proof-manifest/generate_support_core_candidate_manifest.command.txt`](proof-manifest/generate_support_core_candidate_manifest.command.txt)
- JSON report:
  [`proof-manifest/support_core_candidate_manifest_report.json`](proof-manifest/support_core_candidate_manifest_report.json)
- Markdown report:
  [`proof-manifest/support_core_candidate_manifest.md`](proof-manifest/support_core_candidate_manifest.md)
- Manifest note:
  [`../../docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md`](../../docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md)

## Result

The generator returned `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE` with zero problems:

- archetypes: `5`;
- candidate specs: `10`;
- candidates per archetype: `2` for every archetype;
- role pairs complete: `5/5`;
- role counts:
  - `branch_stress`: `5`;
  - `counterfactual_control`: `5`;
- source slots: `8`;
- covered source slots: `8`;
- missing source slots: `0`;
- true authorization flags: `0`;
- generated scenario paths: `0`;
- launch commands: `0`;
- metric or threshold change instructions: `0`;
- missing required content rows: `0`.

The manifest freezes eight mutation-family labels across the ten symbolic candidates:

- `unsupported_nearest_reference_pressure`;
- `introduce_pre_fire_support_reference_control`;
- `post_fire_support_delay_pressure`;
- `shift_post_fire_evidence_to_pre_fire_control`;
- `support_drift_outside_band_sweep`;
- `support_band_border_continuity_control`;
- `support_loss_gap_sweep`;
- `same_object_visibility_continuity_control`.

## Interpretation

Iteration 126 turns the iteration-125 design surface into a future candidate-generation manifest
without crossing into generation or execution. Each registered blind-spot archetype now has a
paired symbolic `branch_stress` and `counterfactual_control` candidate. The pairing gives a later
successor a concrete source-archetype and mutation-family map, while preserving the evidence
boundary: all candidates carry `execution_authorized=false`, `gpu_authorized=false`, and
`hugsim_run_authorized=false`.

A later successor that generates scenarios, chooses execution slots, launches HUGSIM, changes
thresholds or metrics, or claims repair/improvement still requires a fresh `HYPOTHESIS.md`.

## Claim boundary

Manifest preflight only; no scenario-generation execution, GPU launch, HUGSIM run, repair,
actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
