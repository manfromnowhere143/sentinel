# Pre-measurement capacity clarification — 2026-10-09

The asynchronous recovery start returned an operation, but that operation ended in
`ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS`. The instance stayed TERMINATED; both SSH
preflights failed to connect. No guest timer was armed and no controller code was deployed.
Keep these failed commands. An accepted asynchronous request is not a running host.

Before any benchmark measurement, allow at most two additional start RPCs for the same
instance within the already opened second recovery window (local deadline 1791554138.290096,
2026-10-09T13:55:38.290096+00:00). Do not reset that deadline, add an instance, alter its
hardware, or change any numerical or timing rule. Only one actual additional runtime window
is permitted. Inspect each operation's completed result before SSH; stop retrying after a
successful start. If all three recovery RPCs fail, close the hosted benchmark as unobserved.

This is an infrastructure-only pre-evidence amendment, not a measured block retry or an
expansion of the 912-call schedule. The original failed connection consumed a separate,
reported approximately 58-minute instance window.
