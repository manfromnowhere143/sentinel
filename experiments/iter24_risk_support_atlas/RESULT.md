# Iteration 24 - fresh risk-support atlas availability-null

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested only through the pre-registered
availability and split manifest gate. The manifest generator used official nuScenes train-scene
metadata, the local staged file tree on `sentinel-gpu`, and the committed iter22/iter23 known-data
firewall.

This iteration did not launch a model container, canary extraction, full extraction, probe fitting,
activation direction, intervention replay, iteration-12 scoring, selector evaluation, or closed-loop
run. It stopped at the first gate because the fresh post-firewall train pool had no locally readable
six-camera keyframes under the committed file-existence check.

Harness:

- [`make_availability_manifest.py`](make_availability_manifest.py)

Artifacts:

- [`availability_manifest.json`](availability_manifest.json)
- [`availability_manifest.sha256`](availability_manifest.sha256)
- [`availability_manifest.command.txt`](availability_manifest.command.txt)
- [`availability_manifest.exclusions.txt`](availability_manifest.exclusions.txt)
- [`availability_manifest.runbook.txt`](availability_manifest.runbook.txt)

## Verdict

| gate | result |
|---|---|
| Known-data firewall | **PASS**: 118 known-data scene names collected from committed iter22/iter23 manifests and GT sidecars; 132 total scene names excluded after adding NeuroNCAP / iteration-12 evaluation scenes |
| Availability manifest | **FAIL**: 0 eligible scenes, 0 planned keyframes, and 0 planned heldout keyframes; frozen bars were at least 48 eligible scenes, 1,200 total keyframes, and 300 heldout keyframes |
| Canary extraction | **NOT RUN**: prohibited because availability failed |
| Full extraction / S0 | **NOT RUN**: prohibited because availability failed |
| Label atlas / S1 support counts | **NOT RUN**: no extraction rows exist under the fresh manifest |
| Probe fitting / activation direction / interventions | **NOT RUN** |
| Iteration-12 / selector / closed loop | **NOT RUN** |

**Per the frozen gate rule, iteration 24 publishes an availability-null and stops. No model
extraction, probe fitting, activation direction, intervention replay, iteration-12 scoring,
selector claim, or closed-loop run is authorized from this hypothesis.**

## Availability result

The manifest was generated after the iter24 hypothesis and prerequisite surface were committed. It
used the official 700-scene nuScenes train split and local staged data rooted at
`/datasets/nuscenes` on `sentinel-gpu`.

| quantity | value |
|---|---:|
| official train scenes | 700 |
| scenes in `scene.json` | 850 |
| known-data firewall scene names | 118 |
| excluded scene names total | 132 |
| excluded train-scene names | 118 |
| candidate train scenes after exclusions | 582 |
| eligible scenes | 0 |
| ineligible scenes | 582 |
| total planned keyframes | 0 |
| fit / calibration / heldout scenes | 0 / 0 / 0 |
| heldout keyframes | 0 |

Every post-firewall candidate keyframe was rejected by the local file-existence check. The aggregate
reason counts were identical across all six cameras:

| missing local file reason | count |
|---|---:|
| `missing_file_CAM_FRONT` | 23,435 |
| `missing_file_CAM_FRONT_RIGHT` | 23,435 |
| `missing_file_CAM_FRONT_LEFT` | 23,435 |
| `missing_file_CAM_BACK` | 23,435 |
| `missing_file_CAM_BACK_LEFT` | 23,435 |
| `missing_file_CAM_BACK_RIGHT` | 23,435 |

The manifest SHA256 is:

```text
6c4835d3e69a5dc38a1bfcd7629f2df889004505230f61aa83582be8b502a7b0  availability_manifest.json
```

## What the null establishes

This result establishes that the committed iter24 known-data firewall worked before any model
extraction: iter22 and iter23 scenes were treated as known data, NeuroNCAP / iteration-12 scenes
were excluded, and the remaining fresh train scenes were not allowed to rescue the gate by reusing
earlier rows.

It also establishes that the currently staged `sentinel-gpu` nuScenes file tree cannot support the
registered fresh risk-support atlas. After the firewall, no candidate scene had the 24 locally
readable six-camera keyframes required by the hypothesis, so the availability bar failed before any
canary, extraction, label atlas, or causal-localization work.

## Claim boundary

This result does **not** show that nuScenes lacks low-diversity hazard support. It does **not** show
that the motion/planning bridge lacks a causal signal. It does **not** test strict collapse,
low-diversity labels, probes, interventions, iteration-12 frames, selector compatibility, or closed
loop.

It shows only that, under the committed iter24 firewall, manifest generator, local staged data root,
and file-existence eligibility rule, there were zero fresh eligible scenes available for the
registered atlas. A successor must be a fresh pre-registration, and if it depends on a wider data
tree, that staging/availability change must be named before any extraction.

## Evidence

Pre-run and availability artifacts:

- [`HYPOTHESIS.md`](HYPOTHESIS.md)
- [`make_availability_manifest.py`](make_availability_manifest.py)
- [`availability_manifest.json`](availability_manifest.json)
- [`availability_manifest.sha256`](availability_manifest.sha256)
- [`availability_manifest.command.txt`](availability_manifest.command.txt)
- [`availability_manifest.exclusions.txt`](availability_manifest.exclusions.txt)
- [`availability_manifest.runbook.txt`](availability_manifest.runbook.txt)

The manifest source hashes are recorded in [`availability_manifest.json`](availability_manifest.json)
under `source.table_sha256`; the official train-scene list hash is
`80e7f1b38e4973cc7531ab7df4a37a86b98b5140dcaf1c7600df7db553357314`.

Reproduce the availability gate on a host with the same staged data and committed firewall files:

```bash
cd /tmp/iter24_firewall_root
python3 /tmp/make_availability_manifest_iter24.py \
  --meta /datasets/nuscenes/v1.0-trainval \
  --data-root /datasets/nuscenes \
  --train-scenes /tmp/official_train_scenes_iter24.txt \
  --out-dir /tmp/iter24_manifest
```
