# Iteration 28 source manifest runbook

This file documents the uncommitted operator-local source manifest used by
[`stage_local_archive.py`](stage_local_archive.py). The manifest or command arguments may include
local paths or signed URLs and must not be committed.

## Canonical package set

Iteration 28 expects exactly these official nuScenes Full dataset v1.0 / Trainval packages before
it can publish a staging pass:

- `v1.0-trainval_meta.tgz`
- `v1.0-trainval01_blobs.tgz`
- `v1.0-trainval02_blobs.tgz`
- `v1.0-trainval03_blobs.tgz`
- `v1.0-trainval04_blobs.tgz`
- `v1.0-trainval05_blobs.tgz`
- `v1.0-trainval06_blobs.tgz`
- `v1.0-trainval07_blobs.tgz`
- `v1.0-trainval08_blobs.tgz`
- `v1.0-trainval09_blobs.tgz`
- `v1.0-trainval10_blobs.tgz`

## Incremental local staging

When the Mac has limited free space, stage one completed archive at a time:

```bash
python3 experiments/iter28_nuscenes_trainval_staging/stage_local_archive.py \
  --package 3 \
  --local-path /Users/danielwahnich/Downloads/v1.0-trainval03_blobs.tgz
```

The script computes a local SHA256, uploads the archive to
`/datasets/nuscenes-full/archives/<canonical-name>` on `sentinel-gpu`, computes the remote SHA256,
and writes a token-free proof JSON under `proof-staging/uploads/`.

Local-path staging uses rsync by default so interrupted uploads can resume from
`/datasets/nuscenes-full/.iter28_tmp/iter28-upload-<canonical-name>`. Use `--transfer-method scp`
only for a deliberate non-resumable fallback.

If the IAP tunnel is too slow, a temporary direct SSH path may be used only when the VM has a
source-IP-restricted firewall rule and a temporary target tag. Example after confirming the
operator's current public IP and creating the restricted rule:

```bash
python3 experiments/iter28_nuscenes_trainval_staging/stage_local_archive.py \
  --package 4 \
  --local-path /Users/danielwahnich/Downloads/v1.0-trainval04_blobs.tgz \
  --rsync-transport direct \
  --direct-host 35.227.136.146
```

Record the temporary firewall rule in `HANDOFF.md` while it exists, and remove the rule/tag after
staging. Never leave a broad SSH rule open.

If a single direct `rsync` stream is still throughput-limited, use the bounded parallel direct
transport. It splits the local archive into fixed chunks, uploads those chunks through multiple
direct SSH streams into `/datasets/nuscenes-full/.iter28_tmp`, reassembles the archive on the VM,
and then runs the same byte/SHA proof gate:

```bash
python3 experiments/iter28_nuscenes_trainval_staging/stage_local_archive.py \
  --package 4 \
  --local-path /Users/danielwahnich/Downloads/v1.0-trainval04_blobs.tgz \
  --rsync-transport direct \
  --direct-host 35.227.136.146 \
  --transfer-method parallel-direct \
  --parallel-workers 4
```

Use this only for completed local archives, not `.crdownload` files. If it is interrupted, rerun
the same command; the script recreates its per-archive chunk directory and verifies the final
archive before writing proof.

Only after the remote byte count and SHA256 match may the operator delete the local completed copy
to free Mac space. Do not delete `.crdownload` files that are still active unless the download has
been intentionally cancelled.

## Signed URL staging

Signed URL staging is allowed by the hypothesis but must use an uncommitted file or manifest.
For one archive, put exactly one official signed URL in a temporary file:

```bash
printf '%s\n' '<signed official URL>' > /tmp/iter28-part04.url

python3 experiments/iter28_nuscenes_trainval_staging/stage_local_archive.py \
  --package 4 \
  --signed-url-file /tmp/iter28-part04.url
```

The script copies only that temporary URL file to `/datasets/nuscenes-full/.iter28_tmp`, downloads
the archive on `sentinel-gpu`, deletes the remote URL file, records only redacted source
provenance, and commits no URL/query material.

For a batch operator manifest, use the same fields:

```json
{
  "entries": [
    {
      "package": "metadata",
      "source_kind": "signed_url",
      "url": "https://..."
    },
    {
      "package": 1,
      "source_kind": "signed_url",
      "url": "https://..."
    }
  ]
}
```

Do not commit signed URLs, cookies, bearer tokens, query strings, or browser-exported credentials.
If official nuScenes requires browser/session authentication, Daniel performs it or provides
time-limited signed URLs.
