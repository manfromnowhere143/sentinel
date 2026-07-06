# Iteration 27 - storage provisioning pass

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested as an infrastructure-only storage
provisioning gate. The run used the committed mount script
([`mount_storage.sh`](mount_storage.sh)) and did not perform any nuScenes download, data copy,
archive extraction, inventory rerun, model extraction, label atlas, probe fitting, activation
direction, intervention replay, iteration-12 contact, selector scoring, or closed-loop work.

Harness:

- [`mount_storage.sh`](mount_storage.sh)

Artifacts:

- [`proof-storage/command_log.txt`](proof-storage/command_log.txt)
- [`proof-storage/disk_describe.json`](proof-storage/disk_describe.json)
- [`proof-storage/instance_disks.json`](proof-storage/instance_disks.json)
- [`proof-storage/mount_evidence.txt`](proof-storage/mount_evidence.txt)
- [`proof-storage/SHA256SUMS.txt`](proof-storage/SHA256SUMS.txt)

## Verdict

| gate | result |
|---|---|
| Disk creation/description | **PASS**: `sentinel-nuscenes-data-1tb` exists in `us-west1-a`, status `READY`, size `1024` GB, type `pd-balanced` |
| Disk attachment | **PASS**: attached to `sentinel-gpu` as non-boot `persistent-disk-1`, source disk `sentinel-nuscenes-data-1tb` |
| Unsafe format ambiguity | **PASS**: the attached device had no filesystem before the committed mount script formatted it as ext4 |
| Mount | **PASS**: `/datasets/nuscenes-full` is mounted from `/dev/nvme0n2` / `/dev/disk/by-id/google-persistent-disk-1` |
| Mounted target free space | **PASS**: `1,026,108,792,832` bytes available, above the `900 GB` decimal bar |
| fstab persistence | **PASS**: UUID entry present for `/datasets/nuscenes-full` |
| Data movement | **PASS**: 0 dataset bytes downloaded, copied, moved, or extracted |
| Model / Docker / NeuroNCAP | **PASS**: no Docker containers were running in the proof check and no model/NeuroNCAP run was launched |
| Existing dataset roots overwritten | **PASS**: `/datasets/nuscenes-full` was missing in iter25 and now contains only ext4 `lost+found` |

**Iteration 27 passes the storage-provisioning gate. `sentinel-gpu` now has a persistent
1024 GB data disk mounted at `/datasets/nuscenes-full`, with enough free space for a later
pre-registered official nuScenes trainval staging operation.**

This pass authorizes only the next pre-registration. It does not authorize downloading,
copying, extracting, inventory rerun, model extraction, label atlas, probe fitting, activation
direction, iteration-12 scoring, selector evaluation, or closed-loop work.

## Evidence

Cloud disk:

| quantity | value |
|---|---|
| disk name | `sentinel-nuscenes-data-1tb` |
| zone | `us-west1-a` |
| status | `READY` |
| sizeGb | `1024` |
| type | `pd-balanced` |
| attached user | `sentinel-gpu` |

Guest mount:

| quantity | value |
|---|---|
| by-id path used | `/dev/disk/by-id/google-persistent-disk-1` |
| backing device | `/dev/nvme0n2` |
| filesystem | `ext4` |
| label | `sentinel-nuscene` |
| UUID | `9a98277e-b21f-4ffc-8f14-3f2235b43103` |
| mount point | `/datasets/nuscenes-full` |
| 1B blocks | `1,081,101,176,832` |
| available bytes | `1,026,108,792,832` |
| human free | `956G` |

Persistence:

```text
UUID=9a98277e-b21f-4ffc-8f14-3f2235b43103 /datasets/nuscenes-full ext4 defaults,nofail 0 2
```

The first mount attempt failed before formatting because the initial script expected
`/dev/disk/by-id/google-sentinel-nuscenes-data-1tb`, while GCE exposed the attached disk by device
name as `/dev/disk/by-id/google-persistent-disk-1`. The read-only diagnosis proved that
`persistent-disk-1` maps to the attached `sentinel-nuscenes-data-1tb` disk. The script was then
corrected and committed before the successful mount run.

## Claim boundary

This result is an infrastructure pass only. It does **not** show that nuScenes trainval sensor
blobs are staged. It does **not** show that a later availability manifest will pass. It does
**not** test labels, low-diversity support, strict collapse, causal localization, interventions,
selector compatibility, or closed-loop behavior.

It establishes only this operational fact: a persistent, auditable, empty-enough data volume now
exists at `/datasets/nuscenes-full` for a later, separately pre-registered official nuScenes
staging operation.

## Next pre-registerable action

Pre-register iteration 28 as a data-staging operation before moving any dataset bytes. The
pre-registration should freeze:

- the official nuScenes v1.0 trainval file-blob archive list, parts 1-10;
- source handling, including the rule that Daniel performs any browser/session authentication or
  provides signed URLs, because the agent must not handle credentials;
- destination root `/datasets/nuscenes-full`;
- expected archive-size budget `292.78 GB`;
- checksum/size recording for every archive;
- extraction or placement layout;
- an explicit 0 model/Docker/NeuroNCAP bar;
- an availability inventory rerun only after staging is complete.
