# Pre-evidence amendment: historical input reader

16 October 2026. Original source `cc4e3c29c30878ba452467e173da43a9506c2a08`
stopped during initialization when the new strict JSON reader rejected the
historical Iter153 plan's formatting. The input bytes and hash were correct.
The source calls this reader before constructing the query or collecting masks.
The failed output contains only initialization and failure records; no new path,
mask query, certificate, continuation or original-case outcome was acquired.
The process exited and was reaped. [Retained failure boundary](proof/initialization_failure.json).

This amendment supersedes the original no-retry clause **once, for this pre-query
mechanical failure only**. Preserve `proof/audit_raw` unchanged. The amended source
uses a fresh exclusive `proof/audit_retry_raw`, with the same 300-second acquisition
and 900-second admission ceilings. The historical plan remains bound by its exact
SHA256 and parent-commit bytes and is parsed without requiring canonical re-encoding.
All newly produced JSON remains canonical. No historical file is rewritten.

No population, prefix, root, seed, procedure, timing certificate, action horizon,
transition cap, wall cap, classification or claim changes. The full three-root
schedule remains unacquired and unchanged. Retain the original source, failure and
corrected source separately. Any further failure stops this amended acquisition;
no automatic additional retry or favorable fallback. Full prefix admission still
precedes any conditional continuation search.

Two added constructed controls reproduce the formatting mismatch and ensure that
noncanonical new records are still rejected. The unchanged native/source controls
must pass again before the amended source is frozen.
