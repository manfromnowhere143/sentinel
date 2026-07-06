# Iteration 26 - data-staging remedy pre-registration

Frozen before any iter26 source discovery, bucket/listing query, data download, data copy, archive
extraction, root mutation, inventory rerun, model extraction, label atlas, probe fitting,
activation direction, intervention replay, iteration-12 contact, selector scoring, or closed-loop
evaluation.

Iterations 24 and 25 stopped for the right reason: the fresh post-firewall nuScenes train scenes
available to the causal-localization line have metadata but no locally readable six-camera files
under the frozen roots. This is a data-staging/provenance blocker, not a model result.

Iteration 26 is a remedy-design gate. Its job is to determine, without mutating the dataset, whether
there is an auditable source and sufficient local capacity to stage the missing nuScenes camera data
for a later atlas. If the remedy is a download or copy, the result must say so explicitly and freeze
the exact operator action for a later pre-registration.

## Research question

Can we identify one auditable, reproducible data-staging remedy that would provide enough fresh
post-firewall nuScenes train camera files for a later risk-support atlas, without moving data or
running the model in this iteration?

Acceptable positive claim if every bar passes:

> A specific data-staging remedy is available, capacity-checked, and precise enough to
> pre-register a later staging run.

Acceptable null claim if any bar fails:

> No sufficiently auditable staging remedy is currently identified; the blocker remains data
> provenance/staging rather than a tested model mechanism.

Forbidden claims from this iteration, even on a pass:

- no claim that data has been staged;
- no claim that a future availability manifest will pass;
- no label, low-diversity, strict-collapse, probe, activation, selector, or closed-loop claim;
- no use of iteration-12 outcomes;
- no silent data download, file copy, extraction, root mutation, or broad filesystem search.

## Frozen allowed discovery surfaces

The only allowed discovery actions are read-only metadata/listing commands:

- inspect disk capacity on `sentinel-gpu` with `df -h` for the frozen candidate destinations;
- inspect the current frozen roots from iteration 25;
- list local directory names directly under the frozen roots, without walking image files beyond
  metadata already captured by iter25;
- query configured Google Cloud project and storage bucket listings only if authenticated access
  already works;
- inspect public nuScenes download documentation only for package names and expected archive
  sizes;
- inspect committed repository artifacts from iterations 24 and 25.

The iteration may not:

- download files;
- copy files into a nuScenes root;
- extract archives;
- create or delete dataset files;
- change symlinks under data roots;
- run `find /` or a broad hidden-path search;
- launch Docker/model/NeuroNCAP;
- compute labels or fit any model.

If authentication fails, stop and ask Daniel to run `gcloud auth login`; do not touch credentials.

## Candidate remedies

The result may name at most one primary remedy, selected by the first passing option in this order:

1. **Existing local full-data root.** A pre-declared root exists or can be proven by direct parent
   listing to contain the missing six-camera train files without moving data.
2. **Google Cloud Storage staging.** An accessible governed bucket/object prefix contains the
   required nuScenes camera archives or extracted `samples/CAM_*` files, with object counts and
   byte totals available from metadata listing.
3. **Official nuScenes download.** The only viable source is official nuScenes trainval camera
   archive download, requiring Daniel/operator credentials and a later staging pre-registration.

If none can be evidenced, publish a remedy-null and stop.

## Numeric bars

A remedy candidate may pass only if all applicable bars are met before any data movement:

| bar | required value |
|---|---:|
| expected fresh eligible scenes after firewall | `>= 48` |
| expected eligible keyframes after firewall | `>= 1,200` |
| expected heldout keyframes after frozen split | `>= 300` |
| source provenance artifacts | `>= 1` command output or official reference |
| destination free space margin | `>= 1.25x` expected staged bytes |
| data movement performed in iter26 | `0` bytes |
| model / Docker / NeuroNCAP runs | `0` |

If archive size is unknown, the remedy cannot pass. If destination free space is below the margin,
the remedy cannot pass unless the result names a later operator cleanup/resize step without
performing it.

## Named falsifiers

- **No source.** No existing local root, governed bucket, or official package source can be named
  with enough provenance to pre-register a staging operation.
- **Capacity insufficient.** No allowed destination has at least 1.25x the expected staged bytes.
- **Ambiguous remedy.** More than one source/path is blended or the result cannot name the exact
  source and destination.
- **Unauthorized mutation.** Any data download, copy, extraction, deletion, symlink mutation, or
  root mutation occurs in iter26.
- **Hidden search.** Broad filesystem search or unregistered paths are used to rescue the result.
- **Credential breach.** Daniel's credentials are handled by the agent instead of asking Daniel to
  authenticate.
- **Overclaim attempt.** The result treats a remedy plan as staged data, model evidence, or causal
  evidence.

## Required proof artifacts

With the iter26 result:

- this `HYPOTHESIS.md`;
- exact read-only command records;
- disk capacity report;
- source listing/provenance report, if any source is found;
- expected byte budget and 1.25x margin calculation;
- explicit selected remedy or remedy-null;
- claim-boundary paragraph;
- explicit statement that no data bytes were moved and no model/Docker/NeuroNCAP run happened.

## Protocol

1. Commit this hypothesis.
2. Commit any discovery script before running it.
3. Run only the read-only discovery commands listed above.
4. Publish the result at full weight.
5. A pass authorizes only a later data-staging pre-registration. It does not authorize the staging
   itself, inventory rerun, model extraction, label atlas, probe fitting, activation intervention,
   iteration-12 scoring, selector evaluation, or closed-loop evaluation.
