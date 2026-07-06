# Iteration 25 - staged-data inventory pre-registration

Frozen before any iter25 inventory script, root scan, manifest generation, data copy, download,
model extraction, canary run, label atlas, probe fitting, activation direction, intervention
replay, iteration-12 contact, selector scoring, or closed-loop evaluation.

Iteration 24 answered the fresh risk-support question only up to the local data-availability gate:
the known-data firewall worked, but after excluding iter22/iter23 and evaluation scenes, the
remaining 582 train-scene candidates had zero locally readable six-camera keyframes under
`/datasets/nuscenes`. That is a staged-data availability null, not evidence about the causal signal
or about the full nuScenes corpus.

Iteration 25 is therefore a provenance and staged-data inventory gate. Its job is to determine,
without model execution, whether any **pre-declared single local data root** contains enough fresh
post-firewall nuScenes train keyframes to justify a later fresh risk-support atlas
pre-registration.

## Research question

Under a frozen root list, frozen known-data firewall, and token-free manifest format, does a single
local staged nuScenes root contain enough fresh six-camera train keyframes for a later
risk-support atlas?

Acceptable positive claim if every bar passes:

> A single pre-declared local nuScenes root contains enough fresh post-firewall train scenes and
> keyframes to justify a separate risk-support-atlas pre-registration.

Acceptable null claim if the availability bars fail:

> No pre-declared local root currently contains enough fresh post-firewall six-camera keyframes for
> the next atlas; the blocker is data staging, not a tested model mechanism.

Forbidden claims from this iteration, even on a pass:

- no claim about low-diversity hazard counts;
- no claim about strict planner collapse;
- no probe, activation direction, causal-localization, selector, or closed-loop claim;
- no claim about iteration-12 dangerous frames;
- no claim that nuScenes globally lacks support if the local staged roots fail;
- no claim that a future model extraction will pass S0 or S1.

## Frozen roots

The inventory may inspect only these local candidate roots on `sentinel-gpu`, in this order:

1. `/datasets/nuscenes`
2. `/datasets/nuscenes-full`
3. `/opt/sentinel-stack/data/nuscenes`
4. `/opt/sentinel-stack/UniAD/data/nuscenes`
5. `/data/nuscenes`

Missing roots must be recorded as missing. The inventory may not run a broad filesystem search,
use shell history, ask the operator for hidden paths, mix files across roots, or create/download
new data. If all pre-declared roots fail, publish an infrastructure-null and stop.

If multiple roots pass, choose exactly one root before any successor work: the root with the most
eligible post-firewall keyframes; ties break lexicographically by root path. A later atlas must use
that root only unless a new pre-registration says otherwise.

## Known-data firewall

The confirmatory universe must exclude:

- every NeuroNCAP official/evaluation scene;
- every iteration-12 evaluation scene identity;
- every scene name in committed iteration-22 manifests or extraction sidecars;
- every scene name in committed iteration-23 manifests or extraction sidecars;
- every scene name in committed iteration-24 manifest artifacts.

Iter24 scene identities are excluded even though iter24 had zero extraction rows, because the
availability result is already known and must not become a tuning surface.

Scene identity may be used only for exclusion and split assignment. Iteration-12 labels, gaps,
escapes, scores, per-frame evidence, and candidate proof artifacts remain prohibited.

## Frozen inventory discipline

The iter25 script must be committed before any inventory run. It may read:

- official nuScenes train-scene names;
- nuScenes metadata tables under each pre-declared root;
- local file existence and file size for keyframe camera files;
- committed known-data firewall artifacts from iterations 22, 23, and 24.

The script may not read image bytes beyond metadata needed by the operating system for existence
and size. It may not import UniAD, start Docker, call `/infer`, run NeuroNCAP, compute planner
labels, inspect iteration-12 outcomes, or fit any model.

Token hygiene is mandatory: committed outputs must not contain nuScenes scene/sample/sample-data
tokens. Use scene names, sample indices, timestamps, counts, relative file paths, file sizes,
root identifiers, and SHA256 digests only.

## Availability bars

Each eligible scene must have at least 24 keyframes where all six camera files are locally present
under the same selected root:

- `CAM_FRONT`
- `CAM_FRONT_RIGHT`
- `CAM_FRONT_LEFT`
- `CAM_BACK`
- `CAM_BACK_LEFT`
- `CAM_BACK_RIGHT`

The primary root-level pass bars are:

| bar | required value |
|---|---:|
| fresh eligible scenes | `>= 48` |
| total eligible keyframes | `>= 1,200` |
| heldout eligible keyframes under frozen split | `>= 300` |
| known-data contamination | `0` scenes |
| mixed-root keyframes | `0` |
| committed token fields | `0` |

The split rule is frozen if a root passes: sort eligible scene names by SHA256 of
`iter25:<root_id>:<scene_name>`, ascending. Assign the first 50% to `fit`, the next 25% to
`calibration`, and the final 25% to `heldout`, rounding down for `fit` and assigning any remainder
to `heldout`.

If no root passes these bars, publish an iter25 infrastructure-null and stop. Do not relax the root
list, move scenes, mix roots, reduce the 24-keyframe scene floor, or reuse iter22/iter23/iter24
known rows to rescue the gate.

## Named falsifiers

- **No staged support.** No pre-declared root has at least 48 fresh eligible scenes, 1,200 total
  eligible keyframes, and 300 heldout keyframes.
- **Known-data contamination.** Any iter22, iter23, iter24, NeuroNCAP, or iteration-12 scene enters
  the fresh eligible manifest.
- **Mixed-root artifact.** A scene or keyframe requires files from more than one root.
- **Hidden root search.** Any root outside the frozen list is inspected for pass/fail evidence.
- **Token leak.** A committed manifest contains nuScenes scene/sample/sample-data tokens.
- **Root mutation ambiguity.** The selected root changes between inventory and any later
  extraction plan without a new pre-registration.
- **Protocol breach.** Any model extraction, label atlas, probe fitting, activation direction,
  iteration-12 contact, selector scoring, closed-loop run, data download, or data copy happens
  before the iter25 inventory result is published.
- **Overclaim attempt.** Any RESULT language treats file availability as evidence for mechanism,
  low-diversity support, or deployability.

## Required proof artifacts

With the iter25 result:

- this `HYPOTHESIS.md`;
- committed inventory script and exact command record;
- root inventory JSON listing every pre-declared root, missing/present status, metadata table
  hashes, camera-file availability counts, and root-level pass/fail;
- token-free selected-root availability/split manifest if any root passes;
- SHA256 sidecars for inventory and manifest artifacts;
- firewall exclusion report listing excluded scene names and source artifacts;
- claim-boundary paragraph in `RESULT.md`;
- explicit statement that no model extraction, Docker container, probe, intervention,
  iteration-12 scoring, selector evaluation, or closed-loop run happened.

## Protocol

1. Commit this hypothesis.
2. Commit the inventory script before any inventory run.
3. Run the inventory once over the frozen root list.
4. Commit the root inventory, command record, exclusion report, SHA256 sidecars, and, if a root
   passes, the selected-root availability/split manifest.
5. Publish the result at full weight whether the bars pass or fail.
6. A pass authorizes only a separate risk-support-atlas pre-registration. It does not authorize
   canary extraction, full extraction, label atlas, probe fitting, activation intervention,
   iteration-12 scoring, selector evaluation, or closed-loop evaluation.
