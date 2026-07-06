# Iteration 28 - official nuScenes trainval staging pre-registration

Frozen before any iter28 source-manifest read, URL fetch, archive copy, archive extraction,
directory mutation under `/datasets/nuscenes-full`, availability inventory rerun, model extraction,
label atlas, probe fitting, activation direction, intervention replay, iteration-12 contact,
selector scoring, or closed-loop evaluation.

Iterations 24 and 25 showed that the current local staged data cannot support a fresh
causal-localization atlas after the known-data firewall. Iteration 26 identified the missing asset
class as the official nuScenes v1.0 trainval sensor file blobs, not metadata. Iteration 27 cleared
the capacity blocker by mounting a 1024 GB persistent disk at `/datasets/nuscenes-full` with
1,026,108,792,832 bytes available.

Iteration 28 is a data-staging gate. Its job is to stage the official trainval sensor blobs into
the frozen destination and then run a bounded availability inventory. It is still not a model
experiment.

## Research question

Can the official nuScenes v1.0 trainval sensor file blobs be staged at the frozen root
`/datasets/nuscenes-full` with auditable provenance and enough post-firewall six-camera keyframes
for a later fresh risk-support atlas?

Acceptable positive claim if every bar passes:

> The frozen data root contains official nuScenes trainval sensor blobs with enough fresh
> post-firewall six-camera keyframes to justify a separate atlas pre-registration.

Acceptable null claim if staging or availability fails:

> The official trainval staging operation did not produce an auditable root with enough fresh
> post-firewall keyframes; no model extraction or causal-localization work is authorized.

Forbidden claims from this iteration, even on a pass:

- no claim about low-diversity hazard counts;
- no claim about strict planner collapse;
- no probe, activation direction, causal-localization, selector, or closed-loop claim;
- no claim about iteration-12 dangerous frames;
- no claim that a future model extraction will pass S0/S1;
- no claim that availability support is mechanism evidence.

## Frozen destination

- instance: `sentinel-gpu`
- destination root: `/datasets/nuscenes-full`
- archive directory: `/datasets/nuscenes-full/archives`
- temporary directory: `/datasets/nuscenes-full/.iter28_tmp`
- metadata directory expected after staging: `/datasets/nuscenes-full/v1.0-trainval`

The destination is the disk mounted by iteration 27. Iteration 28 may not mutate
`/datasets/nuscenes`, `/opt/sentinel-stack/data/nuscenes`,
`/opt/sentinel-stack/UniAD/data/nuscenes`, or `/data/nuscenes`.

## Frozen source handling

The only allowed dataset source is the official nuScenes **Full dataset (v1.0) / Trainval /
File blobs of 85 scenes, parts 1-10** package family. The expected package labels and planning
sizes are inherited from the committed iteration-26 reference:
[`../iter26_data_staging_remedy/official_nuscenes_download_reference.md`](../iter26_data_staging_remedy/official_nuscenes_download_reference.md).

Expected archive basenames:

| part | expected basename | reference size GB |
|---:|---|---:|
| 1 | `v1.0-trainval01_blobs.tgz` | 29.41 |
| 2 | `v1.0-trainval02_blobs.tgz` | 28.06 |
| 3 | `v1.0-trainval03_blobs.tgz` | 27.81 |
| 4 | `v1.0-trainval04_blobs.tgz` | 29.87 |
| 5 | `v1.0-trainval05_blobs.tgz` | 26.25 |
| 6 | `v1.0-trainval06_blobs.tgz` | 25.61 |
| 7 | `v1.0-trainval07_blobs.tgz` | 27.50 |
| 8 | `v1.0-trainval08_blobs.tgz` | 28.19 |
| 9 | `v1.0-trainval09_blobs.tgz` | 31.21 |
| 10 | `v1.0-trainval10_blobs.tgz` | 38.87 |
| total |  | 292.78 |

The source manifest may be supplied only as an uncommitted operator-local file, for example
`/tmp/iter28_nuscenes_sources.json`, because it may contain signed URLs. The committed artifacts
must record redacted source provenance: source kind, host if a URL is used, archive basename,
bytes, and SHA256. They must not commit bearer tokens, cookies, signed query strings, account
secrets, or Daniel's credentials.

Allowed source kinds:

- `local_path`: Daniel has already downloaded the official archive to a local/on-box path.
- `signed_url`: Daniel provides a time-limited signed official nuScenes URL.

If the official nuScenes site requires browser/session authentication, Daniel must perform that
authentication or provide signed URLs. The agent must not handle Daniel's nuScenes or Google
credentials and must not scrape private browser cookies.

## Allowed actions

After this hypothesis and the iter28 staging/inventory scripts are committed, iteration 28 may:

- verify `/datasets/nuscenes-full` is mounted and has at least 900 GB free before staging;
- create the archive and temporary directories under `/datasets/nuscenes-full`;
- copy each official archive from a `local_path` source, or fetch it from a `signed_url` source;
- compute and record SHA256 and byte size for each archive;
- extract the ten trainval blob archives into `/datasets/nuscenes-full`;
- run a bounded, token-free availability inventory for `/datasets/nuscenes-full` only;
- publish pass/fail evidence at full weight.

Forbidden actions:

- use any source outside the ten official trainval blob packages;
- stage mini, test, lidarseg, panoptic, map, CAN bus, or unrelated archives in this iteration;
- mutate any pre-existing dataset root other than `/datasets/nuscenes-full`;
- run a broad filesystem search;
- inspect image pixels for research labels;
- launch Docker/model/NeuroNCAP or call `/infer`;
- fit probes, write activation directions, run interventions, touch iteration-12 outcomes, score
  selectors, or run closed loop;
- delete source data outside `/datasets/nuscenes-full/.iter28_tmp` and failed partial files created
  by the iter28 script.

## Numeric bars

Source/provenance bars:

| bar | required value |
|---|---:|
| source manifest entries | `10` |
| expected part numbers present | `1..10 exactly once` |
| unexpected package basenames | `0` |
| committed secret-bearing URL/query strings | `0` |
| per-archive SHA256 values recorded | `10` |
| total archive bytes | `>= 250,000,000,000` and `<= 330,000,000,000` |

Storage/staging bars:

| bar | required value |
|---|---:|
| destination preflight free space | `>= 900,000,000,000` bytes |
| extracted root | `/datasets/nuscenes-full` only |
| extraction path traversal attempts accepted | `0` |
| required camera channel directories present | `6/6` |
| dataset bytes moved outside destination root | `0` |
| model / Docker / NeuroNCAP runs | `0` |

Availability bars, copied from the staged-data discipline:

| bar | required value |
|---|---:|
| fresh eligible scenes | `>= 48` |
| total eligible keyframes | `>= 1,200` |
| heldout eligible keyframes under frozen split | `>= 300` |
| known-data contamination | `0` scenes |
| mixed-root keyframes | `0` |
| committed token fields | `0` |

If staging passes but availability fails, publish a data-support null and stop. Do not relax the
known-data firewall, search hidden roots, move scenes across splits, or run model extraction.

## Known-data firewall

The post-staging availability inventory must exclude:

- every NeuroNCAP official/evaluation scene;
- every iteration-12 evaluation scene identity;
- every scene name in committed iteration-22 manifests or extraction sidecars;
- every scene name in committed iteration-23 manifests or extraction sidecars;
- every scene name in committed iteration-24 manifest artifacts.

Scene identity may be used only for exclusion and split assignment. Iteration-12 labels, gaps,
escapes, scores, per-frame evidence, and candidate proof artifacts remain prohibited.

## Split rule after availability pass

If `/datasets/nuscenes-full` passes availability, sort eligible scene names by SHA256 of
`iter28:/datasets/nuscenes-full:<scene_name>`, ascending. Assign the first 50% to `fit`, the next
25% to `calibration`, and the final 25% to `heldout`, rounding down for `fit` and assigning any
remainder to `heldout`. No scene may move between splits after the manifest is committed.

## Named falsifiers

- **Source absent.** The operator-local source manifest is missing, malformed, or does not list
  exactly the ten official trainval blob packages.
- **Source ambiguity.** Any source cannot be tied to the expected official trainval package
  basename and part number.
- **Credential leak.** Any committed artifact contains cookies, bearer tokens, signed query
  strings, or other secret-bearing URL material.
- **Archive integrity failure.** Any archive cannot be copied/fetched, hashed, or size-checked; or
  total archive bytes fall outside the frozen range.
- **Extraction unsafe.** Any archive member attempts path traversal or extraction outside
  `/datasets/nuscenes-full`.
- **Capacity regression.** The mounted root has less than 900,000,000,000 bytes free before
  staging.
- **No staged support.** After extraction, `/datasets/nuscenes-full` has fewer than 48 fresh
  eligible scenes, fewer than 1,200 total eligible keyframes, or fewer than 300 heldout keyframes.
- **Known-data contamination.** Any iter22, iter23, iter24, NeuroNCAP, or iteration-12 scene enters
  the fresh eligible manifest.
- **Protocol breach.** Any model extraction, label atlas, probe fitting, activation direction,
  iteration-12 contact, selector scoring, closed-loop run, hidden root search, or unregistered data
  source happens before the iter28 result is published.
- **Overclaim attempt.** Any RESULT language treats staging or file availability as causal,
  mechanistic, selector, or deployment evidence.

## Required proof artifacts

Before any data movement:

- this `HYPOTHESIS.md`;
- committed staging script;
- committed bounded availability inventory script;
- committed source-manifest schema or runbook that describes the uncommitted source file format.

With the result:

- redacted source-manifest proof;
- exact command log for every staging and inventory command;
- per-archive byte counts and SHA256 values;
- extraction safety report;
- post-extraction directory summary for the six camera channel directories;
- availability inventory JSON for `/datasets/nuscenes-full`;
- token-free selected availability/split manifest if availability passes;
- SHA256 sidecars for all committed evidence;
- claim-boundary paragraph;
- explicit statement that no Docker/model/NeuroNCAP/probe/intervention/iteration-12/selector or
  closed-loop work happened.

## Protocol

1. Commit this hypothesis.
2. Commit the staging and bounded inventory scripts before reading any source manifest or moving
   any dataset bytes.
3. Verify `/datasets/nuscenes-full` mount/capacity.
4. Stage the ten official trainval blob archives from the operator-provided source manifest.
5. Extract into `/datasets/nuscenes-full` only.
6. Run the bounded post-staging availability inventory for `/datasets/nuscenes-full`.
7. Publish the result at full weight whether staging or availability passes or fails.
8. A pass authorizes only a separate risk-support-atlas pre-registration. It does not authorize
   model extraction, label atlas, probe fitting, activation intervention, iteration-12 scoring,
   selector evaluation, or closed-loop evaluation.
