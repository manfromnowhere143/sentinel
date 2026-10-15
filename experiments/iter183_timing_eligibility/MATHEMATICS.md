# Eligibility is a necessary condition, not a feasibility classifier

Use the two exact bound constructions and numerical domain in
[Iter182's mathematics](../iter182_late_frontier_timing/MATHEMATICS.md) unchanged.
Its independently admitted three exclusions have strict squared-distance margins
0.013173485369836048, 10.693221727771324 and 3.836371325611026 against the 1e-6 bar.
They describe a numerical source model; no physical-world certificate follows.

Let V be the original uninterrupted valid-prefix length. For k in 1..V, let E(k)
be true only when the registered bound certifies that the state cannot reach the
existing final checkpoint. Unsupported domains give unknown, treated as eligible.
Set K=min({k:E(k)} union {V+1})-1. The candidate ranking runs over 1..K with the
parent's unchanged keys. It does not rescore future progress or maximize a bound.

Exclusion inherits along the same valid program: if a later prefix had an admissible
continuation, composing its intervening valid transitions with that continuation
would contradict the earlier certificate. Continue the producer's physical program
for unchanged transition accounting, but do not select a later prefix behind a
certified exclusion. A fully valid observed crossing of checkpoint32 is itself a
counter-witness to an earlier exclusion; invalidate the record instead of silently
preferring the completion flag.

Cache identities use sha256(canonical geometry/dynamics) and sha256(big-endian
binary64 five-state values followed by signed 64-bit absolute frame). Case caches
are separately instantiated. Negative zero remains distinct in cache identity;
numerical-join conventions in historical audits are unaffected. No cached proof
can transfer across geometry, clock or contract. Cache entries are populated only
when both certificates finish; a partial first certificate remains explicit evidence
of interrupted work and cannot be mistaken for a complete eligible result.

Independent replay validates retained full certificate records using the separate
corner formulations and derives the eligible prefix, all cached flags and rankings
without the producer eligibility implementation. Timing records are bounded
execution evidence, not an independent hardware-clock measurement or real-time
proof. The work's effect on the integrated tree and its successes remains unknown
until the prospective four-case schedule is admitted.
