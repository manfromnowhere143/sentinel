# Iteration 36 - bridge-site decomposition audit pass

Status: `BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed offline analyzer.
The audit used only committed iteration-29 extraction artifacts plus committed iteration-30 and
iteration-35 proof reports. It did not run gcloud, Docker, a GPU, UniAD, NeuroNCAP, heldout
intervention replay, iteration-12 scoring, selector evaluation, or closed-loop work.

Claim boundary: this is a **diagnostic target-site audit pass**. It does not choose an activation
direction, alpha, intervention family, heldout intervention arm, selector, closed-loop run,
deployment claim, or safety claim. A pass authorizes only a separate future pre-registration.

Harness:

- [`analyze_bridge_sites.py`](analyze_bridge_sites.py)

Primary evidence:

- [`proof-audit/bridge_site_decomposition_report.json`](proof-audit/bridge_site_decomposition_report.json)
- [`proof-audit/analyze_bridge_sites.command.txt`](proof-audit/analyze_bridge_sites.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 artifact and count integrity | **PASS**: iteration-29 extraction and GT hashes matched; primary counts reproduced exactly (`eligible_lowdiv` `127/108/158`, `benign_control` `5084/2344/2245`); iteration 30 verdict was `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`; iteration 35 verdict was `HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM`; bridge tensor lengths matched the frozen `1536 + 256` partition |
| S1 full-bridge reproduction | **PASS**: `all_bridge` reproduced the diagnostic surface above the frozen bars with AUROC `0.950224`, AP `0.614943`, balanced accuracy `0.867444`, recall `0.873418`, specificity `0.861470` |
| S2 non-global target-site audit | **PASS**: five frozen non-global sites passed all diagnostic and scene-bootstrap bars: `traj_slot_0`, `traj_slot_2`, `traj_slot_3`, `traj_slot_4`, and `track_query` |
| Heldout intervention, iteration-12, selector, closed loop | **NOT RUN**: prohibited by this audit |

## Site Results

| site | pass | AUROC | AP | balanced accuracy | recall | specificity | bootstrap AUROC p05 | bootstrap BA p05 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `all_bridge` | reference | `0.950224` | `0.614943` | `0.867444` | `0.873418` | `0.861470` | — | — |
| `track_query` | **PASS** | `0.970531` | `0.726416` | `0.892026` | `0.854430` | `0.929621` | `0.950589` | `0.827686` |
| `traj_slot_0` | **PASS** | `0.911683` | `0.466271` | `0.814909` | `0.816456` | `0.813363` | `0.872878` | `0.759474` |
| `traj_slot_2` | **PASS** | `0.897494` | `0.360284` | `0.812646` | `0.841772` | `0.783519` | `0.851646` | `0.747160` |
| `traj_slot_3` | **PASS** | `0.915049` | `0.422081` | `0.854443` | `0.892405` | `0.816481` | `0.875374` | `0.807795` |
| `traj_slot_4` | **PASS** | `0.908689` | `0.453451` | `0.834212` | `0.867089` | `0.801336` | `0.869575` | `0.790082` |
| `traj_slot_1` | null | `0.916095` | `0.389736` | `0.847967` | `0.981013` | `0.714922` | not run | not run |
| `traj_slot_5` | null | `0.924767` | `0.425507` | `0.821993` | `0.962025` | `0.681960` | not run | not run |

`traj_slot_1` and `traj_slot_5` failed the frozen specificity bar (`< 0.75`), so their
scene-bootstrap audits were not run.

## Interpretation

Iteration 36 changes the path after the iteration-33 through iteration-35 intervention nulls.
The global bridge-centroid direction is still closed for scale-only work, and simple
baseline-geometry row conditioning is still closed. But the diagnostic signal is not only a
diffuse full-bridge artifact: several smaller, pre-declared bridge sites carry strong heldout
signal, and `track_query` is the strongest site under these frozen diagnostics.

This is not evidence that patching `track_query` or any trajectory slot will improve candidate
geometry. It is evidence that a future intervention should stop treating the whole bridge as one
undifferentiated vector and should pre-register a site-specific target, with `track_query` as the
highest-priority diagnostic candidate.

## Next Authorized Step

Stop iteration 36. No heldout intervention replay, iteration-12 scoring, selector evaluation,
closed-loop work, deployment language, or safety claim is authorized. The only authorized next
research move is a fresh pre-registration for a site-specific intervention family, likely starting
with `track_query`, with S0 canary and calibration gates at least as strict as iterations 31-33.
