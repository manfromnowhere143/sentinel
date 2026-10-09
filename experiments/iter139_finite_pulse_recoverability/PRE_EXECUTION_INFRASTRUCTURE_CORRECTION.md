# Pre execution infrastructure correction

Recorded before any successful host connection or initialized Iter139 episode, 2026-10-09.
The first completed provider start operation reported zone stockout. The local shell command
did not stop after that failure: it invoked deployment and then integration SSH commands.
Both failed at IAP connection establishment with exit 255 and no successful port-22 connection.
Their commands and failures are retained as `proof/deployment.*` and `proof/runtime_integration.*`.
The provider readback before the second start still reported TERMINATED.

This was an orchestration error. The requirement for a successful completed start before SSH
was not enforced in that outer shell. Subsequent dependent operations run separately, and every
SSH call now checks a retained successful start operation and RUNNING original-instance readback
through [provider_gate.py](provider_gate.py). Known-bads reject a pending operation, completed
stockout, wrong instance identity and stopped instance. Missing readiness records fail before
invoking the connection tool. Historical failure logs will not be overwritten by recovery.

This agent-authored pre-execution correction adds that operational guard. The frozen scene,
seeds, controller, arms, outcomes, equality rules, timeout and overall budget remain unchanged.
The second start is within the preregistered three-request/ten-minute capacity allowance; the
overall time budget continues from the first request. No measured episode is retried. Fresh
exclusive remote paths and all bound prior files must still be checked before any episode.
