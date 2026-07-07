# Iteration 28 - official nuScenes trainval staging pass

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested as a data-staging and availability
gate. It staged the official nuScenes v1.0 trainval metadata archive and the ten official trainval
sensor-blob archives into `/datasets/nuscenes-full`, extracted them with a path-safety gate, and
ran the bounded post-firewall availability inventory.

This iteration did not run Docker, NeuroNCAP, UniAD/VAD inference, label extraction, probe fitting,
activation directions, interventions, selector scoring, iteration-12 evaluation, or closed-loop
evaluation.

Harness:

- [`stage_local_archive.py`](stage_local_archive.py)
- [`extract_archives.py`](extract_archives.py)
- [`bounded_inventory.py`](bounded_inventory.py)
- [`run_remote_inventory.py`](run_remote_inventory.py)

Artifacts:

- [`proof-staging/uploads/`](proof-staging/uploads/)
- [`proof-extract/extraction_safety_report.json`](proof-extract/extraction_safety_report.json)
- [`proof-extract/extraction_safety_report.sha256`](proof-extract/extraction_safety_report.sha256)
- [`proof-inventory/availability_inventory.json`](proof-inventory/availability_inventory.json)
- [`proof-inventory/availability_inventory.sha256`](proof-inventory/availability_inventory.sha256)
- [`proof-inventory/selected_availability_manifest.json`](proof-inventory/selected_availability_manifest.json)
- [`proof-inventory/selected_availability_manifest.sha256`](proof-inventory/selected_availability_manifest.sha256)
- [`proof-inventory/remote_inventory_controller.json`](proof-inventory/remote_inventory_controller.json)

## Verdict

| gate | result |
|---|---|
| Source package set | **PASS**: exactly the official trainval metadata archive plus blob parts `1..10` were staged |
| Source provenance redaction | **PASS**: committed proofs record source kind, host, basename, bytes, and SHA256; no URL query strings, cookies, bearer tokens, or credentials are committed |
| Per-archive integrity | **PASS**: 11/11 archives have committed remote byte counts and SHA256 values |
| Total archive bytes | **PASS**: `314,886,603,672` bytes, within the frozen `250,000,000,000..331,000,000,000` bar |
| Extraction root | **PASS**: extracted only into `/datasets/nuscenes-full` |
| Extraction path safety | **PASS**: `0` unsafe members and `0` path traversal attempts accepted across `2,631,374` tar members |
| Metadata directory | **PASS**: `/datasets/nuscenes-full/v1.0-trainval` present |
| Camera channel directories | **PASS**: 6/6 present, each with `34,149` files |
| Availability support | **PASS**: `532` eligible post-firewall train scenes and `21,461` eligible keyframes |
| Heldout support | **PASS**: heldout split has `133` scenes and `5,360` keyframes |
| Known-data contamination | **PASS**: `0` |
| Mixed-root keyframes | **PASS**: `0` |
| Token fields in committed inventory | **PASS**: `0` |
| Model / Docker / NeuroNCAP | **PASS**: no model, Docker, NeuroNCAP, probe, intervention, selector, iteration-12, or closed-loop run was launched |

**Iteration 28 passes the official trainval staging and availability gate.**
`/datasets/nuscenes-full` now contains the official nuScenes trainval metadata and sensor blobs
with enough fresh post-firewall six-camera keyframes to justify a separate atlas/research
pre-registration.

This pass authorizes only the next pre-registration. It does not authorize model extraction,
label atlas generation, probe fitting, activation intervention, iteration-12 scoring, selector
evaluation, or closed-loop work.

## Staging Evidence

| package | bytes | SHA256 |
|---|---:|---|
| `v1.0-trainval_meta.tgz` | `461,678,030` | `db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b` |
| `v1.0-trainval01_blobs.tgz` | `31,579,122,687` | `fee4316c55f0780532819ea1b01f347b2ad964303c93477cc815f8191b126171` |
| `v1.0-trainval02_blobs.tgz` | `30,134,721,083` | `292301394af9d4a8eb62cee41b3b3031c6cad78e2b39bf63a91bd6d3b7592373` |
| `v1.0-trainval03_blobs.tgz` | `29,872,679,856` | `9e6e7c949fbea971321112757dfcff757add646078393c191981a0a49d5f483c` |
| `v1.0-trainval04_blobs.tgz` | `32,075,538,096` | `6927f765f8555ce6f901ed2763569bd860b33ad5e076709bbc6c4cc8a51ffc76` |
| `v1.0-trainval05_blobs.tgz` | `28,191,611,840` | `ea8d886bc79be30d02e9552d229aaa0843ecffccaaff6606644540b4183f605f` |
| `v1.0-trainval06_blobs.tgz` | `27,516,468,993` | `26e3dfff85d8ef6354d4b9dc0a9d8b3f0ebd8719b6d84eac5841fa31b97b8deb` |
| `v1.0-trainval07_blobs.tgz` | `29,534,216,608` | `70287e2d65386bce2d67001ef56f5c0abdd3dd95d1ec404c3e00a39208fa60b7` |
| `v1.0-trainval08_blobs.tgz` | `30,275,496,199` | `744080381fcfbca3e3ee8d20c5340dce4b5b7fae8020a7e90338ec98b20802c1` |
| `v1.0-trainval09_blobs.tgz` | `33,517,622,306` | `ca3aba09dc63cd22fdc455959f3aea99e0f6ed4de822c8c3f5f96f0efa372ec5` |
| `v1.0-trainval10_blobs.tgz` | `41,727,447,974` | `046aa7c5ff2cab63a25eaa6210e00bd8197f835e5324457d305a2a16a262f57a` |

The direct URL staging path was used for the final archives after proving that browser-local
downloads were not the right source of truth for a large staged root. Committed artifacts preserve
only redacted provenance and remote hashes.

## Extraction Evidence

The committed extraction report scanned every tar member before extraction:

| quantity | value |
|---|---:|
| archives scanned | `11` |
| tar members scanned | `2,631,374` |
| unsafe members | `0` |
| path traversal attempts accepted | `0` |
| metadata directory present | `true` |
| post-extraction available bytes | `280,398,983,168` |

Six-camera file counts after extraction:

| channel | files |
|---|---:|
| `CAM_FRONT` | `34,149` |
| `CAM_FRONT_LEFT` | `34,149` |
| `CAM_FRONT_RIGHT` | `34,149` |
| `CAM_BACK` | `34,149` |
| `CAM_BACK_LEFT` | `34,149` |
| `CAM_BACK_RIGHT` | `34,149` |

## Availability Evidence

The bounded inventory was run on `sentinel-gpu` against `/datasets/nuscenes-full` by
[`run_remote_inventory.py`](run_remote_inventory.py). A controller-side inventory attempt was not
used because the dataset root exists on the VM, not on the Mac controller. The committed inventory
proof is the VM-produced result.

| quantity | value |
|---|---:|
| official train scenes | `700` |
| scene rows in metadata | `850` |
| known-data/firewall excluded scene names | `182` |
| candidate scenes after exclusions | `532` |
| eligible scenes | `532` |
| ineligible scenes | `0` |
| total eligible keyframes | `21,461` |
| heldout keyframes | `5,360` |
| known-data contamination | `0` |
| mixed-root keyframes | `0` |
| metadata identifier fields | `0` |

Frozen split summary:

| split | scenes | keyframes |
|---|---:|---:|
| fit | `266` | `10,726` |
| calibration | `133` | `5,375` |
| heldout | `133` | `5,360` |

The selected manifest is token-free and joins future work by scene name, sample index, timestamp,
and committed relative camera file paths only.

## Claim Boundary

This result establishes an auditable data root and a fresh post-firewall availability manifest.
It does **not** establish low-diversity hazard counts, strict planner collapse support, causal
localization, probe evidence, activation directions, selector compatibility, or closed-loop safety.

The next scientifically valid action is a new pre-registration that names this committed
availability manifest, freezes labels/count bars before model extraction, and stops on any S0/data
support failure. Iteration 28 itself grants no permission to run models or tune research choices.
