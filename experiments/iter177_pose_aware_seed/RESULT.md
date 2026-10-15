# Pose-aware trial is invalid at an accepted-state boundary

**Status: invalid.** The fourth worker stopped with `reset_bounds`. Preserve the
initialized run and all partial evidence; it was not retried. **No new complete-
case count is admitted.** Retained integrated qualification remains Iter175's
**2/4**, and source comparison stays closed.

The trial changed one initial control program to an analytic pose-aware guess.
Fallback proposals, original cases/seeds, 128-transition inner allowance,
eight-step horizon, 18,000-transition / 120-second / 96-action outer caps, native
binary and every physical/scene/checkpoint rule were fixed. Constructed controls
included both improvements and loss of an exact old curved connection.
[Protocol](PROTOCOL.md) · [derivation and limits](MATHEMATICS.md).

## The retained boundary witness

Chicane_right's first connection selects five steps with acceleration `1.6` from
speed `4`. Its accepted endpoint has speed `6.000000000000002`: two floating-point
steps above `6`, an excess of `1.7763568394002505e-15`.

| Step | Retained speed |
|---:|---:|
| 0 | 4.0 |
| 1 | 4.4 |
| 2 | 4.800000000000001 |
| 3 | 5.200000000000001 |
| 4 | 5.600000000000001 |
| 5 | 6.000000000000002 |

The existing motion predicate allows speed through `6 + 1e-12`. The constructor
for the next connector requires speed at most `6` exactly. Thus this accepted
state cannot satisfy that next-root interface. The worker traceback records
`reset_bounds`; its next callback input was not logged, so no independent native
callback or tree-ancestry replay is claimed.

A separately frozen post-outcome checker binds the original source, all **102 raw
files / 19,832,466 bytes**, initialization, failure and supervisor record. It
independently checks all **125 attempted transitions** and proposals of this first
connection, then the selected **6 state records / 47,916 point-state classifications**
against full scalar background-mask identities. All six states pass the existing
physical/scene checks. Exact scalar speed/steering replay confirms the boundary
excess. The discrepancy is between accepted transition output and next-root input;
this is not evidence that the physical speed limit needs relaxation.
[Failure protocol](FAILURE_PROTOCOL.md) · [checker](failure_check.py).

## Partial outputs remain unadmitted

| Case | Producer-reported completion | Attempts in producer record | Returned frame | Admission |
|---|---|---:|---:|---|
| bend_left | Yes | 4,737 | 32 | Not independently admitted |
| bend_right | No | 18,000 | 14 | Not independently admitted |
| chicane_left | Yes | 1,537 | 33 | Not independently admitted |
| chicane_right | No result file | Unknown final count | Unknown returned path | Worker failed |

The failed worker retains one completed connection record with 125 attempts and
the six-state diagnostic path above. That record does not supply a final case
outcome. Do not turn the absent result into a miss, success or zero work. The three
earlier outputs do not establish a qualified two-of-four result for this trial,
nor may they be pooled with the retained baseline to pass the gate.

Supervised acquisition stopped after **32.261 seconds**; the separate diagnostic
completed in **8.527 seconds**. Both processes were reaped. The serial worker waits
returned; no scientific worker remains running. There was no retry, new driving
episode, provider use, source query or spending. The original 42 constructed
controls and 122 focused/retained checks passed; seven post-outcome failure controls
also pass. Software-test success does not change the scientific `invalid` status.

Frozen trial source: `5762157a1ae612fd6c6c2b1c89bba9701f2150cd`.
Raw committed before diagnosis: `314840a3b996860bf5d5a48b51c09254c359fdf1`.
Frozen diagnostic source: `3f3cd6948b8b6774fc5b69399d97270cb85912a6`.
Failure admission: `91f53c9065e806e297e500030d80313c18e1fdb0`.
[Admission](proof/admission.json) · [producer failure](proof/search_raw/failure.json) ·
[next decision](DECISION.md).
