# Iter150 result: bounded cloud observation qualification

11 October 2026. **The registered observation and resource-closure checks are supported.**
One actual VM start exercised the native evidence adapter through IAP, temporary observation
loss, completion while disconnected, bounded permanent loss, host-local child expiry and
duplicate-initialization rejection. No driving episode was initialized and no scientific
outcome was added. Iter148 remains 4 admitted / 1 incomplete / 107 uninitialized.

**The live harness returned `failed`.** After the successful postflight response, it tried to
save a report as `postflight.json`, a name already occupied by the command receipt. Exclusive
creation correctly raised `FileExistsError`. The finally path verified the owned VM stopped.
The failure is retained unchanged; qualification is reconstructed from the preceding outputs,
not inferred from a successful exit. Command receipts now have a separate `commands/` directory.
That correction is locally tested; the corrected whole harness has not been rerun in the cloud.

## Observed evidence

| Check | Retained observation |
|---|---|
| Native pair 0 | Injected unavailable read, then genuine IAP reconciliation; 2 reads |
| Native pair 1 | Genuine IAP reconciliation; 1 read |
| Original interrupted pair 2 | Partial evidence; no completion or scientific admission |
| Permanent observer loss | 4 unavailable reads, bounded stop; no launch operation |
| Completion during disconnection | Actual remote synthetic child completed; later IAP reconciliation succeeded |
| Independent child deadline | Remote child killed and reaped at 5.006 s; partial raw preserved |
| Duplicate initialization | Both remote fixture paths rejected a second initialization; retained bytes unchanged |
| Postflight | 2 native pair inventories unchanged, 0 active containers, 0 active GPU processes |
| Resource closure | Exact owned VM/start read back as TERMINATED; local watchdog exit 0 |
| Separate audit | 5 traces replayed, both 16-file native inventories rehashed, 9 corrupted records rejected |

The inventory checks read 10,194,944 and 10,194,998 bytes. Shared plan and manifest files occur
in both inventories; these are 32 entries, not 32 unique files. The adapter stream-hashes bounded
regular files, refuses symlink traversal, detects file changes and sends a small content manifest.
It validates original parent, worker, summary and event bindings. The separate checker also
reconstructs source, plan and initialization identities. Operational completeness never replaces
the scientific dynamics, outcome, prefix, intervention and replica checks.

[Raw run and failure](proof/cloud_001/result.json) ·
[successful postflight response](proof/cloud_001/postflight.stdout) ·
[fixtures](proof/cloud_001/fixtures.json) ·
[separate audit](proof/live_independent_audit_final.json) ·
[resource closure](proof/cloud_001/closure.json).

## Prospective registration, validation and preservation

The [protocol](HYPOTHESIS.md) was committed at `d850d2a` before implementation and live execution.
The live source was frozen at `cb3b7e8`; the [packet receipt](proof/cloud_001/source.json)
binds its files. All 154 live raw files were committed at `7528899` before the independent audit
and still match those Git objects. The later audit and report-path correction do not rewrite them.

The pre-live focused Iter146–150 regression run passed **245 tests**, with 40 retained upstream
warnings. A later startup-reconciliation rejection check increased the adapter count to 30.
After the reporting fix and independent identity checks, **37 adapter tests passed**. This is
not a claim that a fresh 253-test combined suite ran: the broad and final focused receipts are
separate. Nine additional auditor mutations were rejected. Ruff passes on new source and tests;
the unchanged static supply-chain verifier passes. Local tests used ambient macOS Python 3.14.2;
the live packet ran under the existing host Python. No pinned-environment equivalence is claimed.

[Broad regression output](proof/final_local_tests.stdout) ·
[final focused output](proof/final_correction_tests.stdout) ·
[local validation identities](proof/validation.json).

A pre-live audit invocation initially passed a relative native-root path to an older validator
that requires an absolute path. The invocation was corrected, without weakening the validator;
the [failure and correction](proof/prelive_runner_failure.json) are retained. The later report
filename collision is a separate execution defect. Both matter when judging the harness.

The owned checkout recovered about 3 GiB of capacity by replacing duplicate large files with
byte-verified APFS clones. The canonical dirty checkout and its index were not reset or staged.
[Storage receipt](proof/storage.json). Historical scientific evidence, accepted master,
MISSION_STATE and pinned AGENTS bytes are unchanged.

## Resource accounting

VM `sentinel-gpu`, ID `3834622546652649531`, project `sunlit-unison-487018-b0`, zone `us-west1-a`:

- Owned start: `2026-10-10T23:56:43.367-07:00`.
- Verified stop: `2026-10-10T23:59:17.693-07:00`; state `TERMINATED`.
- Full local envelope: 167.878 s, within the registered 900 s.
- Conservative compute estimate: **$0.140**, within $0.75, using $3/hour.

The [fresh pricing binding](proof/price_binding.json) retains the official Oregon g2-standard-8
rate of $0.853624312/hour. The larger planning rate is intentionally conservative. This is an
estimate, not an invoice; persistent storage and taxes are excluded. The attached L4 was billed
with the VM, but no GPU workload ran. No other VM or persistent resource was created.

The independent local watchdog started before VM startup. A 600-second host systemd shutdown
timer was installed and its identity bound before the synthetic workers. The short synthetic
child deadline actually fired. The VM shutdown timer did not need to fire; manual coordinator
closure preceded it. The retained timer observation does not establish successful expiry of
that separate 600-second mechanism.

## Decision and limits

The supported scope is **one VM start, historical native artifacts and constructed CPU-only
faults over real transport**. It does not measure cloud fault probability, real-time driving,
physical safety, generalization or industrial superiority. Source identity and replay do not
eliminate shared implementation errors. Provider stop uses a name-addressed API with pre/post
identity checks under a single lifecycle operator assumption; there is no atomic start-conditional
stop claim. An active scientific worker ownership adapter and new launch/admission integration
remain to be qualified.

Another billed VM start solely to recreate the already-observed postflight response would add
little evidence about the local filename fix. The regression reproduces the collision and
verifies that command metadata and a domain report now coexist; the original failed exit stays
visible. Proceed to the [new-study admission decision](DECISION.md), then spend scientific compute
on the proposed two-case recovery question only after its fresh execution contract is ready.

Reconstruct the audit without contacting a provider:

```bash
python3 -m experiments.iter150_cloud_observation.audit \
  experiments/iter150_cloud_observation/proof/cloud_001 \
  experiments/iter148_recovery_study/proof/study_raw
python3 -m pytest -q tests/test_iter150_cloud_observation.py
```

Do not rerun the live entrypoint or reuse its closed paths as a local reproduction shortcut.
Whole-repository hosted CI is not established; the earlier 688 Ruff findings in 160 pre-task
files remain a separate master-integration issue.

Research publication and root preservation are recorded in the
[remote readback](proof/publication.json) and [preservation receipt](proof/root_preservation.json).
Publication is on the research branch; accepted master remains unchanged.
