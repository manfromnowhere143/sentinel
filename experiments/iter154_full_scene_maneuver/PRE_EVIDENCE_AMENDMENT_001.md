# Pre-evidence amendment 001 — capacity refusal and no-start reconciliation

11 October 2026. The first start request returned ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS:
g2-standard-8 with one L4 was unavailable in us-west1-a. Both replicas remain uninitialized;
no host SSH, packet deployment, renderer or scientific worker ran. Repeated provider observations
show the original VM TERMINATED with unchanged lastStartTimestamp. The changed stop timestamp is
retained literally; it is not treated as an owned new start. Original failed supervisor records
remain unchanged under proof/block_000. The qualified no-start closure allowed its watchdog to
exit; later process inspection observed it absent, without observing its exit code.

The existing supervisor correctly refused to invent an owned start but could not classify a
known capacity denial. Its termination-unverified result is superseded only by the separately
retained no-start closure, not rewritten. A new helper accepts this classification only for an
explicit nonzero capacity rejection plus at least two same-identity TERMINATED observations at
the prior start. Success replies, other errors, changed start, running state or changed hardware
remain unresolved. Eight local known-bad/positive checks passed before recording this closure.

Authorize exactly one further start request on the same VM and hardware after at least120seconds
from the first request, using a new exclusive local proof/block_000_attempt_001 directory.
This is a capacity retry before any scientific initialization, not a retry of an experiment.
The original remote root was never created by the first request; its exclusive creation remains
mandatory. Do not reuse either local proof directory or retry an initialized replica. A second
capacity refusal closes Iter154 without scientific outcomes; no third request or infrastructure
substitution is authorized by this amendment.

Keep the exact scientific plan, packet, scenarios, seeds, actions, outcome rules and test order.
Preserve source ad063849c502d21967d3bc6b8590057f797e1a13 as the first attempt's identity.
Freeze a new execution source after tests, changing only startup/attempt bookkeeping, related
qualification tests and manifest bindings. The total execution-envelope allowance remains
3600seconds/$3: deduct the first supervisor's23.950629seconds from the second envelope.
The long interval spent on local analysis is not VM runtime; no new started VM was observed.
Storage/taxes remain excluded. A prior denial and its closure must be committed before retry.
Qualified rejected-start closure now runs inside the supervisor and joins its own watchdog.
Unknown or possibly successful starts retain the original ownership-checked reconciliation.
