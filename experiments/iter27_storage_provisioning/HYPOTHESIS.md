# Iteration 27 - storage provisioning pre-registration

Frozen before any disk creation, disk attachment, formatting, mount, fstab change, data download,
data copy, archive extraction, inventory rerun, model extraction, label atlas, probe fitting,
activation direction, intervention replay, iteration-12 contact, selector scoring, or closed-loop
evaluation.

Iteration 26 identified the data-staging blocker precisely: the causal-localization line needs the
official nuScenes v1.0 trainval sensor file blobs, but the current `sentinel-gpu` root disk has
only 25.125 GB free, while the frozen archive-size capacity bar is 365.975 GB. A storage
provisioning step is required before any responsible download/staging operation can exist.

Iteration 27 is an infrastructure provisioning gate. Its job is to create a clean, auditable data
volume for nuScenes staging and prove capacity, without downloading or copying dataset bytes.

## Research question

Can we provision a persistent `sentinel-gpu` data volume with enough free capacity for the official
nuScenes trainval sensor blobs and expose it at one frozen dataset root for a later staging
pre-registration?

Acceptable positive claim if every bar passes:

> `sentinel-gpu` has a mounted persistent data volume at the frozen destination with enough free
> space for a later official nuScenes trainval staging operation.

Acceptable null claim if any bar fails:

> Storage provisioning did not produce an auditable destination with enough free capacity; no
> download or staging operation is authorized.

Forbidden claims from this iteration, even on a pass:

- no claim that nuScenes data has been staged;
- no claim that a later availability manifest will pass;
- no label, low-diversity, strict-collapse, probe, activation, selector, or closed-loop claim;
- no data download, dataset copy, archive extraction, inventory rerun, or model run.

## Frozen target

Target instance:

- project: `sunlit-unison-487018-b0`
- zone: `us-west1-a`
- instance: `sentinel-gpu`

Target disk and mount:

- disk name: `sentinel-nuscenes-data-1tb`
- disk type: `pd-balanced`
- disk size: `1024 GB`
- mount point: `/datasets/nuscenes-full`
- filesystem: `ext4`

This path is chosen because iteration 25 already treated `/datasets/nuscenes-full` as a frozen
candidate root and found it missing. Mounting a new disk there does not hide an existing staged
dataset.

## Allowed actions

The only allowed mutating actions are:

- create the named persistent disk if it does not already exist;
- attach it to `sentinel-gpu` if not already attached;
- format it as `ext4` only if it has no filesystem;
- create the mount point if absent;
- mount the disk at `/datasets/nuscenes-full`;
- add a persistent `/etc/fstab` entry by UUID only after the mount is verified.

Allowed read-only checks:

- `gcloud compute disks describe`;
- `gcloud compute instances describe`;
- `lsblk -f`;
- `blkid`;
- `df -h`;
- direct mount-point listing.

Forbidden actions:

- download, copy, extract, delete, or move nuScenes files;
- mutate `/datasets/nuscenes`;
- run broad filesystem search;
- launch Docker/model/NeuroNCAP;
- rerun iter25 inventory;
- inspect iteration-12 outcomes;
- handle Daniel's credentials.

## Numeric bars

| bar | required value |
|---|---:|
| mounted target free space | `>= 900 GB` decimal |
| disk size | `>= 1024 GB` |
| data movement performed | `0` bytes |
| model / Docker / NeuroNCAP runs | `0` |
| existing dataset roots overwritten | `0` |

The 900 GB free-space floor is deliberately above the iter26 365.975 GB minimum. It leaves working
room for archives plus extracted sensor blobs and avoids running another marginal capacity gate.

## Named falsifiers

- **Disk creation failed.** The named disk cannot be created or described.
- **Attach failed.** The disk cannot be attached to `sentinel-gpu`.
- **Unsafe format ambiguity.** The disk appears to contain an existing filesystem or data and the
  operator cannot prove it is the intended empty staging disk.
- **Mount failed.** `/datasets/nuscenes-full` is not mounted from the named disk.
- **Capacity insufficient.** Mounted free space is below 900 GB decimal.
- **Unauthorized data movement.** Any nuScenes data download/copy/extraction occurs in iter27.
- **Root overwrite.** An existing dataset root is hidden or overwritten.
- **Protocol breach.** Any inventory rerun, model extraction, label atlas, probe fitting,
  activation direction, iteration-12 scoring, selector evaluation, or closed-loop run happens.

## Required proof artifacts

With the iter27 result:

- this `HYPOTHESIS.md`;
- exact command log for disk create/attach/format/mount checks;
- `gcloud compute disks describe` output for the named disk;
- `gcloud compute instances describe` attachment summary;
- `lsblk -f`, `blkid`, and `df -h` evidence;
- explicit fstab/mount evidence if persistence is configured;
- claim-boundary paragraph;
- explicit statement that 0 dataset bytes were moved and no model/Docker/NeuroNCAP run happened.

## Protocol

1. Commit this hypothesis.
2. Run the allowed storage provisioning commands exactly under this target.
3. Commit the proof artifacts and `RESULT.md`.
4. A pass authorizes only a later data-staging pre-registration. It does not authorize the
   nuScenes download itself, inventory rerun, model extraction, label atlas, probe fitting,
   activation intervention, iteration-12 scoring, selector evaluation, or closed-loop evaluation.
