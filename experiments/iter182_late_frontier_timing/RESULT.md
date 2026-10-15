# Four checkpoint continuations; three demonstrated timing constraints

**Supported within the registered seven-endpoint diagnostic.** Four retained left
endpoints admit scalar-verified continuations through checkpoint frame 32. One
left endpoint necessarily completes too early; both right endpoints cannot reach
the required checkpoint progress under the declared numerical model. Zero
unresolved bounded misses, zero censored probes, zero contradictory certificates.

| Case / accepted call | Root frame | Admitted classification | Probe transitions | Original outgoing calls |
|---|---:|---|---:|---|
| Left / 91 | 29 | Premature-completion exclusion | 17 | 12 |
| Left / 104 | 25 | Verified frame-32 continuation | 1,206 | 1 |
| Left / 110 | 26 | Verified frame-32 continuation | 966 | 0 |
| Left / 128 | 24 | Verified frame-32 continuation | 1,499 | 0 |
| Left / 134 | 24 | Verified frame-32 continuation | 1,469 | 0 |
| Right / 102 | 31 | Progress exclusion | 16 | 1 |
| Right / 138 | 30 | Progress exclusion | 240 | 0 |

![Admitted late-frontier timing](proof/timing.png)

The four witnesses have frame-32 route fractions 0.999468, 0.999468, 0.877193 and
0.994152. **None completes the route under the original predicate.** Three feasible
roots received no original outgoing request. All four diagnostic witnesses cost
966–1,499 transitions, exceeding the original 128-transition connection allowance,
and use a different stepwise diagnostic. This establishes available continuations,
not that one additional original connection would have found them, nor that
expansion allocation alone caused the failure.

Left call 91 received 438 original evaluations whose first rejection was premature
completion. The new independent next-position bound establishes a sufficient
continuous-control exclusion within its stated numerical domain. Physical
rejections retain precedence; the certificate is not a relabeling of every sampled
action. Right call 102's premature-completion bound is **inapplicable** because
its next step reaches frame 32; its separate progress exclusion holds. Right call
138 is also progress-excluded. Bounds did not prune any diagnostic probe.

All 3,969 queried states pass complete scalar collision-mask reconstruction:
**25,933,446 point-state classifications**. The checker also reconstructs 196
retained path records, 226 returned probe-path records, and 1,217 prefix records
from all 582 original outgoing evaluations. All new attempted motions, physical
and progress predicates, proposal order, retention, clock, path selection,
numeric joins and accounting replay. Masks and numeric joins remain case-scoped.
Earliest equal-state joins are path witnesses, not proof of native ancestry.

One acquisition used 5,413 transitions. Producer/checker supervised walls were
9.990 / 196.188 seconds, within 900-second stage limits; checker peak RSS was
468,615,168 bytes. Both processes exited and were reaped. No new integrated run,
driving episode, provider access or spending. 57 new constructed controls and
189 focused checks passed before acquisition. The initial fixture rewrite error
and corrected preflight runtime-reader usage are retained in qualification and
external operational records; neither initialized a scientific retry.

Frozen source `b357b7c3dd19eefce3fa394f9859d9cc8b5f9f25`;
raw committed before admission `8a4ccf7c02a4e517ae1834025b871555cce52430`;
admission `84fa02a7b4cf0fc47eb79e5eb337f2f5d4576045`.
[Protocol](PROTOCOL.md) · [mathematical scope](MATHEMATICS.md) ·
[independent admission](proof/admission.json) · [state](STATE.json) ·
[next decision](DECISION.md).

The best retained integrated result remains Iter178's 3/4. Iter181 remains adverse
2/4 with one lost success, and source comparison remains closed. The diagnostic
does not establish full-route feasibility of every witness, useful intervention
from actual decision histories, latency, superiority, physical safety or transfer.
These seven exposed roots do not support population generalization. Constraint
proofs apply to the declared numerical source model, not all hardware or vehicles.
