# Iteration 26 - data-staging remedy capacity-null

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested through read-only source/capacity
discovery. The run used the committed discovery script
([`discover_staging_remedy.py`](discover_staging_remedy.py)), the official nuScenes download-size
reference ([`official_nuscenes_download_reference.md`](official_nuscenes_download_reference.md)),
and bounded GCS listings.

This iteration did not download data, copy data into a root, extract archives, mutate symlinks,
launch Docker, start a model container, call `/infer`, run NeuroNCAP, compute labels, fit probes,
write activation directions, touch iteration-12 outcomes, score selectors, or run closed loop.

Harness:

- [`discover_staging_remedy.py`](discover_staging_remedy.py)

Artifacts:

- [`staging_remedy_discovery.json`](staging_remedy_discovery.json)
- [`staging_remedy_discovery.sha256`](staging_remedy_discovery.sha256)
- [`staging_remedy_discovery.command.txt`](staging_remedy_discovery.command.txt)
- [`official_nuscenes_download_reference.md`](official_nuscenes_download_reference.md)
- [`gcloud_storage_probe.txt`](gcloud_storage_probe.txt)

## Verdict

| gate | result |
|---|---|
| Existing local full-data root | **FAIL**: only `/datasets/nuscenes` exists; it has metadata and `samples/` but lacks the needed trainval camera blobs |
| Governed GCS source | **FAIL**: `gs://sunlit-unison-487018-b0-sentinel/nuscenes/` contains metadata/map/CAN bus artifacts only, 1.53 GiB total; no trainval sensor blobs |
| Official nuScenes source | **SOURCE IDENTIFIED**: v1.0 trainval sensor file blobs parts 1-10, 292.78 GB archive-size budget |
| Destination capacity | **FAIL**: frozen 1.25x margin requires 365.975 GB free; best observed free space on `sentinel-gpu` was 25.125 GB |
| Data movement | **PASS**: 0 bytes downloaded/copied/extracted |
| Model / Docker / NeuroNCAP | **PASS**: 0 runs |

**Iteration 26 identifies the correct remedy class but fails the capacity gate. The next required
operator action is storage provisioning, not a model run. No data download/copy, extraction,
inventory rerun, model extraction, label atlas, probe fitting, activation direction, intervention
replay, iteration-12 scoring, selector claim, or closed-loop run is authorized from this
hypothesis.**

## Direct answer

Yes, we need to stage/download missing nuScenes data before the causal-localization line can
continue.

The needed data is the official **nuScenes full dataset v1.0 / Trainval / File blobs of 85 scenes,
parts 1-10**. Metadata alone is not enough; the missing files are the sensor file blobs, especially
the camera files under `samples/CAM_*`.

Do **not** start the download on the current GPU disk. It has about 25.125 GB free. The official
trainval file-blob archives total 292.78 GB, and the frozen safety margin requires at least
365.975 GB free before staging. A practical next pre-registration should provision a new or resized
data volume, preferably 750 GB to 1 TB, then stage the ten official trainval file-blob archives and
rerun the availability inventory.

## Evidence

Capacity and local roots:

| quantity | value |
|---|---:|
| official trainval file-blob archive budget | 292.78 GB |
| frozen capacity margin | 1.25x |
| required free capacity | 365.975 GB |
| best observed free capacity on frozen destinations | 25.125 GB |
| capacity pass | false |

The frozen local roots from iter25 remained unchanged:

| root | status |
|---|---|
| `/datasets/nuscenes` | exists; metadata and `samples/` dir present |
| `/datasets/nuscenes-full` | missing |
| `/opt/sentinel-stack/data/nuscenes` | missing |
| `/opt/sentinel-stack/UniAD/data/nuscenes` | missing |
| `/data/nuscenes` | missing |

GCS probe:

| object | bytes |
|---|---:|
| `gs://sunlit-unison-487018-b0-sentinel/nuscenes/can_bus.zip` | 780,974,697 |
| `gs://sunlit-unison-487018-b0-sentinel/nuscenes/nuScenes-map-expansion-v1.3.zip` | 398,535,531 |
| `gs://sunlit-unison-487018-b0-sentinel/nuscenes/v1.0-trainval_meta.tgz` | 461,678,030 |

The governed bucket therefore does not contain the missing trainval sensor blobs.

## Claim boundary

This result does **not** stage data. It does **not** show that a later availability manifest will
pass. It does **not** test labels, low-diversity support, strict collapse, causal localization,
interventions, selector compatibility, or closed-loop behavior.

It establishes only this operational fact: the Sentinel causal-localization path needs the official
nuScenes trainval sensor file blobs, and the current GPU disk is too small to stage them under the
frozen capacity rule.

## Next pre-registerable action

Pre-register a storage/staging iteration that does exactly one of:

- attach or resize a data disk so a destination has at least 365.975 GB free, preferably 750 GB to
  1 TB for archive plus extracted-data working room; then
- stage the official nuScenes v1.0 trainval file-blob archives parts 1-10 from the signed-in
  nuScenes download source; then
- extract or place them under one declared destination root; then
- rerun the iter25-style availability inventory before any model extraction.

If the official download requires browser/session credentials, Daniel must perform that
authentication or provide signed download URLs. The agent must not handle Daniel's nuScenes or
Google credentials.
