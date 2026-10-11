# Iter149 result: local observation recovery qualification

11 October 2026. **Supported within the local engineering scope.** The new observer recovered
from temporary observation loss without relaunching work, rejected mismatched/stale replies,
and required reconciled terminal artifacts before reporting completion. Permanent observation
loss remained bounded. This is not a new driving result or a qualified cloud supervisor.

| Check | Observed result |
|---|---|
| Named deterministic fault cases | 30 passed |
| Bounded sequence exploration | All 1,296 length-four combinations passed in each of Python 3.14.2 and 3.11.15 |
| Separate checker rejection controls | 12 corrupted traces rejected in each interpreter |
| Actual local subprocess cases | Completion, crash and observation-free watchdog expiry passed |
| Duplicate local initialization | Rejected in all three subprocess cases; marker and raw bytes unchanged |
| Regression suite, Iter146–149 | 216 passed, 40 retained upstream warnings, 14.26 s |
| New source Ruff checks | Passed; only new source formatted |
| Existing static supply-chain check | `SUPPLY_CHAIN_VERIFICATION_OK` |

The protocol was committed as `ea38e84` before implementation/qualification. The final source
freeze was `34f494e`; [source identities and environment](proof/validation.json) bind the tested
files. The earlier 47-test development run and review corrections are preserved. Tests ran in
ambient macOS environments; no pinned Linux CI or production-environment equivalence is claimed.

[Deterministic traces](proof/frozen_deterministic/qualification.json),
[Python 3.11 qualification](proof/frozen_py311/qualification.json),
[actual subprocess receipts](proof/frozen_local/qualification.json),
[regression output](proof/final_regression.stdout).
The independent checker imports no production transition or classification implementation.
This is separate implementation, not independent human or institutional review.

## What changed

`recovery.py` attaches to already initialized work and has no launch/restart API. It binds VM
identity/start, source, plan, pair, initialization marker, host boot and host deadline identity.
Fresh request tokens and revision/content checks reject duplicated, stale and conflicting
observations. Fixed limits bound consecutive unavailable reads, total reads, timeouts, backoff
and local elapsed time. A valid read resets only the consecutive failure counter.

Unavailable observation, failed worker, partial evidence and complete worker remain distinct.
Missing terminal artifacts, incorrect inventory or failed return codes cannot establish
completion. The only next action is ownership reconciliation; scientific admission is always
false here. Exact termination readback is required to mark closure verified.

The local host fixture writes an exclusive initialization marker, publishes snapshots atomically
and runs a child under a separate host process deadline. In the disconnected case no observer
ran while the worker was active. The watchdog killed and reaped its owned child at expiry and
retained partial raw data. A second initialization of that path failed without changing evidence.

## Limits and decision

**The live coordinator repair is not yet complete.** The registered local qualification is
complete. The existing GPU worker uses larger artifacts and a different result schema; the
new fixture's bounded small records require an explicit adapter. Cloud/IAP read timeouts,
provider identity transitions, streaming inventory reconciliation and provider shutdown must
be qualified through that adapter in a fresh non-scientific envelope. Do not rerun the closed
Iter148 helpers or infer that a local subprocess receipt establishes VM termination.

No provider was contacted, no GPU was started, and no scientific outcome was added. Local
fixture subprocesses exited. Provider state today was not refreshed; prior Iter148 termination
receipts remain historical observations. Iter148 stays inconclusive with 4 admitted, 1 incomplete
and 107 uninitialized slots. Existing transfer and recoverability nulls are unchanged.

The [assessment](ASSESSMENT.md) supports the recovery-first direction while identifying the
remaining timing, comparator, generalization and integration gaps. The
[new development canary proposal](NEXT_STUDY_PROPOSAL.md) names two disclosed cases and 16 new
slots; it is not launchable and does not fill missing Iter148 slots. Complete bounded cloud
adapter qualification and fresh prospective admission before that canary. No whole-repository
hosted pass, real-time operation, physical safety or state-of-the-art superiority is established.

Reproduce locally into a new output directory:

```bash
python3 -m pytest -q tests/test_iter149_observation_recovery.py
python3 -m experiments.iter149_observation_recovery.qualify /tmp/sentinel149-new-fault-proof
python3 -m experiments.iter149_observation_recovery.qualify_local /tmp/sentinel149-new-process-proof
```

The qualification commands refuse an existing output path. The subprocess fixture uses local
CPU only and creates synthetic artifacts; it cannot launch a driving experiment or a VM.
