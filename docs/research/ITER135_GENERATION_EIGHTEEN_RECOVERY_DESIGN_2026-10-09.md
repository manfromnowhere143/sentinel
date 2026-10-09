# Generation 18 recovery design after red R17 — 2026-10-09

Status: **proposed design**, not a preregistration, accepted source, receipt, state transition,
launch authorization, or Iteration-135 result. The current canonical tip is F17
`8c118b74c699bf0f139f9bd659192bad06b895f8`. Do not edit or rewrite that published lineage.

## Decision problem

F17 closed its hosted source CI checks on Python 3.10 and 3.11. Generation-17 receipt creation did
not close. The first local generator failed to atomically replace the historical R16 receipt
because its working file had `uchg` and a delete-denying ACL. A separately recorded
metadata-corrected attempt wrote a **red** candidate receipt: focused and full pytest commands
returned `1`, while seven other commands returned `0`. That receipt stored hashes and byte counts
for about 1.19 MB of each pytest stdout stream but discarded their diagnostic contents. Two later
focused-suite diagnostics on clean F17 passed `1615 passed, 2 skipped`, including the exact argv.
Those passes do not explain or erase the red generator results. The failure mechanism of the
pytest commands is **unknown**. The full retained incident is at
`/Users/danielwahnich/sentinel-bootstrap-evidence/f17-20261009-correction-admission/R17B_FAILURE_ANALYSIS.md`.

The central engineering question is: **Can a new source generation produce an auditable local
tooling receipt whose failures remain diagnosable, without selecting around the red Gen17
attempts or changing the scientific Iteration-135 protocol?** The scientific question is separate:
even a green tooling receipt would not show semantic causal value, external transfer, or safety.

## Proposed publication topology

Register a new generation rather than retrying R17 or inserting a commit into its frozen chain.
The candidate topology to freeze before implementation is:

```text
accepted D16 ── accepted F17 ── P18 ── F18 ── R18 ── T18 ── B18
                                  │      │      │      │      └─ continuity + generated handoff
                                  │      │      │      └─ mission state only
                                  │      │      └─ tooling receipt only
                                  │      └─ bounded source/tests/control changes
                                  └─ preregistration only
```

P18 must record the exact changed-path set, parent identities, source/receipt schemas, environment
and retry rules, resource ceiling, hosted event inventory, and falsifiers **before** F18 exists.
The interim P18 and T18 commits should never be pushed as standalone canonical tips. F18, R18,
and B18 need distinct disposable and canonical two-job CI readbacks as frozen by P18. An alternate
topology may be chosen before P18 is frozen, but it must preserve F17 and all red evidence; no
force update, accepted-history rewrite, merge-around, or claim that R17 passed is admissible.

## Source changes that close the observed defects

1. **Destination preflight.** Before expensive tests, bind the existing historical receipt bytes
   and inspect its regular-file status, mode, link count, immutable flags, and delete-denying ACL
   on the canonical host. Record a before/after metadata snapshot and a disposable sibling-path
   replacement probe. If the canonical destination is protected, stop *before* command execution.
   Unsealing must preserve its SHA-256 and be explicit in the retained invocation contract.
2. **Failure streams.** For every nonzero command, retain bounded stdout and stderr bytes in a
   private, no-follow, create-exclusive diagnostic directory outside Git; bind their SHA-256,
   byte count, argv index, and exact truncation status in the red receipt. Design streaming
   capture so output cannot grow without limit in memory or on disk. A proposed limit is 16 MiB
   per stream; a larger stream must produce a distinct `OUTPUT_LIMIT_EXCEEDED` failure and a
   clearly labeled bounded prefix/tail record, never a falsely complete log. No credential or
   private prompt may enter the retained stream. A green receipt still carries command digests
   and independently replayable argv, not a claim of hermeticity.
3. **Known-bads.** Exercise a protected destination, a failed pytest returning a recognizable
   traceback, a diagnostic-output collision, a stream limit, source drift, and duplicate or
   altered receipt fields. The failed-command known-bad must prove the traceback is recoverable
   from retained bytes and the gate reports failure. Test both direct generation and independent
   receipt replay on the exact local toolchain before a hosted push.
4. **One identity, one acceptance attempt.** A failed or incomplete F18 generator or hosted lane
   stops that identity. Diagnostic commands may be used to identify the defect, labeled and
   retained as diagnostics. A correction requires a new source identity and a new pre-execution
   contract; no best-of runs or selected green result.

The precise API, files, path inventory, timeout, stream cap, and tool hashes remain to be frozen
in P18 after a source-scope audit. This design does not silently amend the earlier Generation-17
rules or license an F18 execution.

## Scientific checkpoint before any compute

The [pre-run Iteration-135 review](ITER135_PRE_RUN_SCIENTIFIC_DECISION_REVIEW_2026-10-09.md)
replays the committed Iteration-134 proof and finds low sensitivity near the registered `+0.25`
NCAP and `-0.05` progress margins. Twenty class/pair cells reuse 14 source scenes. A responsive
semantic union versus clock-only schedules at equal assigned class budget estimates that policy
contrast, but cannot separate semantic content from feedback responsiveness. Before any 110-hour
analytic ceiling is spent, state whether a terminal fixed-suite policy/dose-frontier result is
worth that cost, what each registered verdict changes, and what a responsive non-planner-semantic
comparator plus independent held-out scenes would add. Any material protocol correction must be a
visible pre-evidence amendment with synchronized implementation and tests. Do not tune thresholds
after evidence or convert an inconclusive result into a positive claim.

## Current boundary

Iteration 134 remains the last completed scientific experiment. Iteration 135 has no smoke or
analytic episodes, no new outcome data, and no GPU use. Lifecycle is `UNKNOWN`; semantic
attribution is unresolved; HUGSIM transfer is null. F17's green CI is bounded source validation,
not a completed CI-hardening baton or scientific acceptance. This design authorizes no provider,
host, GPU, H/E/P/S descendant, publication of Iteration-135 results, or claim of production
readiness or parity with any industrial autonomy system.
