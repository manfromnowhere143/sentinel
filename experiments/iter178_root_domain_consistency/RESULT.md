# Three completions admitted; all-four qualification still fails

**Status: contradicted for all-four qualification.** Independent replay admits
**3/4 completions**, up from retained Iter175's 2/4. Chicane_right is gained;
bend_left and chicane_left remain complete. Bend_right exhausts its work budget
without completing. **Source comparison stays closed.** Iter177 remains invalid
and was not retried or pooled into this corrected trial.

The correction makes next-root acceptance use the already-existing motion
tolerance. Stored state values and all physical/scene/checkpoint predicates remain
unchanged. Keep the pose-aware seed from Iter177, all fallback programs, original
cases/seeds, native binary, sampler, metric and prefix ranking. Caps remain 128
transitions per connection, eight-step maximum horizon, 18,000 transitions,
120 seconds and 96 actions per case. [Frozen protocol](PROTOCOL.md).

| Case | Retained complete | Corrected complete | Attempts | Calls | Accepted edges | Returned time | Checkpoints |
|---|---|---|---:|---:|---:|---:|---:|
| bend_left | Yes | Yes | 4,737 | 38 | 27 | 8.00 s | 2/2 |
| bend_right | No | No | 18,000 | 141 | 71 | 3.50 s | 0/2 |
| chicane_left | Yes | Yes | 1,537 | 13 | 13 | 8.25 s | 2/2 |
| chicane_right | No | Yes | 13,192 | 104 | 92 | 8.75 s | 2/2 |

![Paired corrected qualification](proof/qualification.png)

One gain and zero losses. Total work is **37,466 attempted transitions**, compared
with 49,055 in Iter175; calls/accepted edges are **296/203**. Early completion
changes used work. This is one exposed seed per case, with unchanged maximum
budgets; it is not a general efficiency, equal-used-work or latency estimate.
The candidate combines pose-aware proposals and numerical interface correction,
so this comparison does not isolate a pure seed effect. No reference was rerun.

Independent admission checks every attempted motion, physical/checkpoint rule,
prefix choice, seed/fallback proposal, cache/accounting entry and native-path
binding. Full scalar masks cover **118 returned states** and **872,652 point-state
classifications**. All three complete paths pass both timed checkpoints and their
terminal route condition. Unselected background labels and native tree/RNG remain
producer evidence. Approximate paths never count as complete.

The remaining bend_right path ends at frame 14 with route fraction 0.627326;
accepted tree endpoints reach frame 15. It has no admitted continuation through
the first checkpoint at frame 16. The returned path's existing progress alone
does not explain the miss: the first checkpoint requires 0.345561 with the frozen
0.05 margin. Other retained branches have different positions, speeds and progress.
Inspect their continuation constraints before attributing the failure to a single
metric, target, control proposal or checkpoint. Longer tree time is not completion.

One source freeze, one fresh corrected schedule and one independent admission.
Producer/checker supervised wall times are **36.388 / 18.838 seconds**; both process
groups exited and were reaped. Selected runtime identities verify. The correction
does not project states or alter physical tolerances. Twenty-eight new controls
and 119 focused/retained checks pass with the native runtime and no skips.
No new driving episode, source query, provider use or spending. Actual-history
recovery, measured intervention latency, safety, information benefit, transfer
and superiority remain unestablished.

Frozen source: `3d5b35c1659375b3722f8a8661fe5974aeb496f9`.
Raw committed before admission: `1ba6a4e90db895fe2991eeb2df26fc3b48ccdeba`.
Admission: `c62f7aaafb6703827a57ef2da1fe989457b672fb`.
[Independent admission](proof/admission.json) · [execution](proof/search_raw/execution.json) ·
[next decision](DECISION.md).
