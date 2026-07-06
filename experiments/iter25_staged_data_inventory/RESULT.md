# Iteration 25 - staged-data inventory infrastructure-null

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through the committed read-only root
inventory script ([`inventory_roots.py`](inventory_roots.py)). The run inspected only the frozen
local root list, applied the iter22/iter23/iter24/evaluation known-data firewall, and wrote
token-free inventory artifacts.

This iteration did not download or copy nuScenes data, launch Docker, start a model container,
call `/infer`, compute labels, fit probes, write activation directions, touch iteration-12
outcomes, score selectors, or run closed loop. Immediately before the inventory command,
`sudo docker ps --format '{{.Names}}'` returned no running containers.

Harness:

- [`inventory_roots.py`](inventory_roots.py)

Artifacts:

- [`root_inventory.json`](root_inventory.json)
- [`root_inventory.sha256`](root_inventory.sha256)
- [`root_inventory.command.txt`](root_inventory.command.txt)
- [`root_inventory.exclusions.txt`](root_inventory.exclusions.txt)
- [`root_inventory.runbook.txt`](root_inventory.runbook.txt)

## Verdict

| gate | result |
|---|---|
| Frozen root discipline | **PASS**: only the five pre-declared roots were inspected |
| Known-data firewall | **PASS**: 182 scene names excluded from committed iter22/iter23/iter24/evaluation artifacts; 168 of those were official train scenes |
| Token hygiene | **PASS**: committed JSON artifacts contain no `token` or `*_token` fields |
| Root availability | **FAIL**: no pre-declared root met the frozen bars |
| Selected-root manifest | **NOT WRITTEN**: no root passed |
| Model extraction / labels / probes / interventions | **NOT RUN** |
| Iteration-12 / selector / closed loop | **NOT RUN** |

**Per the frozen gate rule, iteration 25 publishes an infrastructure-null and stops. No data
download/copy, model extraction, label atlas, probe fitting, activation direction, intervention
replay, iteration-12 scoring, selector claim, or closed-loop run is authorized from this
hypothesis.**

## Inventory result

The frozen root list was:

1. `/datasets/nuscenes`
2. `/datasets/nuscenes-full`
3. `/opt/sentinel-stack/data/nuscenes`
4. `/opt/sentinel-stack/UniAD/data/nuscenes`
5. `/data/nuscenes`

Root-level outcome:

| root | status | eligible scenes | total keyframes | heldout keyframes | pass |
|---|---|---:|---:|---:|---|
| `/datasets/nuscenes` | `insufficient_availability` | 0 | 0 | 0 | false |
| `/datasets/nuscenes-full` | `missing_root` | 0 | 0 | 0 | false |
| `/opt/sentinel-stack/data/nuscenes` | `missing_root` | 0 | 0 | 0 | false |
| `/opt/sentinel-stack/UniAD/data/nuscenes` | `missing_root` | 0 | 0 | 0 | false |
| `/data/nuscenes` | `missing_root` | 0 | 0 | 0 | false |

The only present root, `/datasets/nuscenes`, had metadata for 850 scenes and 532 official train
candidate scenes after exclusions, but zero eligible six-camera keyframes. Its aggregate missing
file counts were identical across all six cameras:

| missing local file reason | count |
|---|---:|
| `missing_file_CAM_FRONT` | 21,461 |
| `missing_file_CAM_FRONT_RIGHT` | 21,461 |
| `missing_file_CAM_FRONT_LEFT` | 21,461 |
| `missing_file_CAM_BACK` | 21,461 |
| `missing_file_CAM_BACK_LEFT` | 21,461 |
| `missing_file_CAM_BACK_RIGHT` | 21,461 |

No root satisfied the frozen bars of at least 48 fresh eligible scenes, 1,200 total eligible
keyframes, and 300 heldout eligible keyframes. Therefore `selected_root` is `null` and
`selected_availability_manifest.json` was not created.

The inventory SHA256 is:

```text
584e33b433a7be1773d09fdb15b6114550dc23f02834a3d32a7ae583a24617ba  root_inventory.json
```

## What the null establishes

This result establishes that the currently pre-declared local roots on `sentinel-gpu` do not
contain enough fresh post-firewall six-camera nuScenes train keyframes for another atlas. The
blocker remains data staging/provenance, not model behavior.

The result also establishes that the inventory gate is now auditable: the root list, known-data
firewall, token hygiene, pass/fail bars, and selected-root tie-break are frozen in committed code
and tests.

## Claim boundary

This result does **not** show that the full nuScenes train split lacks low-diversity hazard frames.
It does **not** test strict collapse, low diversity, causal localization, interventions, selector
compatibility, or closed-loop behavior. It shows only that none of the five pre-declared local
roots currently contains enough fresh six-camera keyframes, after the committed firewall, to
justify another atlas run.

A successor should not launch model extraction until a fresh pre-registration names a concrete
data-staging remedy and proves availability before extraction.

## Evidence

Pre-run artifacts:

- [`HYPOTHESIS.md`](HYPOTHESIS.md)
- [`inventory_roots.py`](inventory_roots.py)
- [`../../tests/test_iter25_inventory.py`](../../tests/test_iter25_inventory.py)

Inventory proof:

- [`root_inventory.json`](root_inventory.json)
- [`root_inventory.sha256`](root_inventory.sha256)
- [`root_inventory.command.txt`](root_inventory.command.txt)
- [`root_inventory.exclusions.txt`](root_inventory.exclusions.txt)
- [`root_inventory.runbook.txt`](root_inventory.runbook.txt)

Reproduce the inventory on a host with the same frozen roots and staged firewall inputs:

```bash
cd /tmp/iter25_firewall_root_20260706_1852z
python3 -B /tmp/inventory_roots_iter25.py \
  --train-scenes /tmp/official_train_scenes_iter25.txt \
  --out-dir /tmp/iter25_inventory_20260706_1852z
```
