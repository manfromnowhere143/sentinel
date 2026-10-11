# Research branch and handoff review — 11 October 2026

Daniel asked why the completed work remained local and whether the README and handoff were
ready for the next session. The editorial checkpoint was local intentionally: the complete
research line had not been published, and the historical Iter135 publication guard remained
red. Inspection also found a real omission: the root HANDOFF still described the old snapshot.
Current CONTINUITY and the Iter148 decision were insufficient substitutes for that entrypoint.

## Changes

The [current handoff](../../../HANDOFF.md) now states the mission, evidence and limits,
exact next task, completion criteria, closed experiment paths, resource closure, branch identity
and preservation requirements. The next task is deterministic qualification of bounded
observation recovery. Another live scientific comparison requires a fresh prospective protocol.
The interrupted Iter148 study remains closed and inconclusive.

AGENTS routes recovery to that current brief and identifies the old handoff renderer as the
historical Iter135 renderer. Its source and MISSION_STATE are preserved. Both previous handoffs
are archived byte for byte. README, architecture, active continuity and the Iter148 continuation
point to the same state. The full [editorial review](../../editorial/2026-10-11/REVIEW.md) remains
a dated record of the preceding local update; its publication wording describes that checkpoint.

## Publication scope

Destination: [research/iter148-recovery-study](https://github.com/manfromnowhere143/sentinel/tree/research/iter148-recovery-study).
The branch contains the complete retained research lineage and current documentation. Publishing
it makes those materials available for inspection. It does not promote the branch to master or
establish a scientific claim by itself.

The accepted master remains `8c118b74c699bf0f139f9bd659192bad06b895f8`. No history rewrite,
force push, default-branch change or governance change is part of this task. The root checkout
and its unrelated work are preserved; documentation commits use an isolated index and Daniel's
configured identity. Publication verification must compare the remote head and GitHub-served
README/HANDOFF bytes with the exact committed tree. A push response alone is insufficient.

## Remote verification

The first publication completed at `4b600bbd059077a26ac1faad7b3c9a731ef0379a`.
[Remote readback](remote_readback.json) confirmed the branch head and byte-for-byte agreement
for GitHub's README, HANDOFF, AGENTS and architecture. Master remained unchanged. The subsequent
documentation commit retains this checkpoint receipt and the final hosted observation separately.

The [hosted CI observation](hosted_ci_observation.json) records run 38117280514 while both
Python jobs were still checking out the repository. No hosted pass is claimed. Consult that
run and the current branch's later run before interpreting hosted validation or integrating
master; a retained pending observation does not imply that the run is still pending now.

## Checks and limits

- The prior research head, `cc0db9f0fd427f6d70a5bad7ff085481fcc1c264`, descends from master
  by 160 commits. All 160 use Daniel's configured author and committer identity; their messages
  contain no model co-author or generated-by trailers.
- Its 3,067 added blobs total 304,306,057 uncompressed bytes. The largest is 32,162,666 bytes;
  none exceeds GitHub's 100 MB file limit. These are object sizes, not a network transfer estimate.
- Gitleaks 8.30.1 scanned the complete unpublished range and returned 31 findings, exit 1.
  Each was inspected: 25 are SHA-256 source-file inventory values; six are the same Google
  client configuration found in captured public pricing HTML. An anonymous HTTP 200 readback
  of the public pricing page contained that configuration. No unresolved finding remains in
  this scan. This bounded review is not proof that every possible secret is absent.
  [Redacted classifications and public-source fingerprints](secret_classification.json).
- Current links, result coverage, handoff counts, diagram-source equality, preserved scientific
  bytes, root index, README protections and exact documentation scope are checked separately.
  The earlier rendered diagrams remain applicable because their source is unchanged.
- No new driving episode or Google Cloud compute is used for this documentation/publication
  task. Resource states in the handoff are retained observations at the prior closure, not
  a claim of continuous provider monitoring.

### Historical documentation and CI contract

The root documentation guard retains four findings: `current_completed_iteration:134!=148`,
`tooling_publication:pending_f17_origin_not_d16_or_f17`,
`tooling_publication:pending_f17_source_scope`, and
`tooling_publication:pending_f17_worktree_dirty`. These names describe the root checkout at the
dated check. A clean research checkout has a different parent and may produce different
topology findings. The guard requires the exact F17 source child of D16 and an Iter134 maximum
result directory; the later research branch does not satisfy that contract.

A clean detached checkout of `4b600bbd059077a26ac1faad7b3c9a731ef0379a` was also checked.
Its guard reported exactly four findings: iteration mismatch, origin, source-parent and
source-scope. No broken link, diagram-format or missing-result finding was reported. The
[source checkout observation](candidate_docs_guard.json) records the command and full output.
The new handoff commit also passed a separate Gitleaks scan with zero findings.

Those findings are not relabelled green or silently bypassed. The existing hosted workflow is
left intact. Its actual outcome must be reported separately from documentation correctness,
controller qualification and scientific results. This is a research-branch publication, with
master integration unresolved. It is not an accepted Iter135 launch or tooling receipt.

All checks and this review were performed by the repository agent under Daniel's direct
instruction. They are not independent human review or an outside team's endorsement.
