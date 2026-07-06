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

Only after the remote byte count and SHA256 match may the operator delete the local completed copy
to free Mac space. Do not delete `.crdownload` files that are still active unless the download has
been intentionally cancelled.

## Signed URL staging

Signed URL staging is allowed by the hypothesis but must use an uncommitted manifest, for example:

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
