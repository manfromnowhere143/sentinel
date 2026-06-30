# Iteration 4 — introspective gating fixes the over-braking, and isolates the next problem

Iteration 3 found the TTC monitor over-brakes: it freezes benign scenes because its trigger fires
whenever the *ego* closes on *any* object. Iteration 4 changes one term — gate on the **agent's own**
closing speed (is something actively driving at us?) instead of the total closing speed — and runs the
same deployment metric. The result is a real step forward with a clean, honest split decision.

## Result — deployment metric (3 scenes × 6 runs, frozen UniAD)

| arm | NCAP safety ↑ | progress ↑ | collision % ↓ | **safe-progress ↑** |
|---|---:|---:|---:|---:|
| OFF (no monitor) | 2.18 | 0.91 | 61 | 2.08 |
| TTC-old (`MIN_CLOSING=0`, iter-2/3) | 4.62 | 0.14 | 17 | 0.64 |
| **gated (`MIN_CLOSING=3 m/s`)** | 3.16 | **0.84** | 50 | **2.80** |

Per scene — safety score / collision % / ego distance driven (m):

| scene | OFF | TTC-old | gated |
|---|---|---|---|
| stationary/0103 (clean) | 5.00 / 0 / **32.4** | 5.00 / 0 / 4.9 | 5.00 / 0 / **32.4** |
| frontal/0103 | 0.91 / 83 / 34.6 | 3.85 / 50 / 3.7 | 2.25 / 83 / 26.8 |
| side/0103 | 0.64 / 100 / 19.9 | 5.00 / 0 / 2.9 | 0.64 / 100 / 19.9 |

## The pre-registered verdict (H4) — split, reported as such

- **Criterion 1 — selectivity restored: MET, cleanly.** On the benign clean scene the gated monitor
  drives **32.4 m, identical to the unmonitored planner, with 0 interventions** (vs TTC-old's 4.9 m
  freeze). The stationary object isn't *actively* closing, so the gate correctly stays silent and lets
  the planner do its job. The over-braking that sank iteration 3 is fixed.
- **Criterion 2 — keep the danger-scene safety: FAILED.** The gate now *under*-brakes real threats:
  side/0103 is **identical to OFF** (0.64 / 100% — the gate never fired), and frontal only mitigates
  impact (2.25 vs OFF 0.91, same 83% collision). Pooled collision 50% (gated) vs 17% (TTC-old).
- **Stretch goal — beat the unmonitored planner's safe-progress (2.08): MET.** gated **2.80 > OFF 2.08
  > TTC-old 0.64.** For the first time the monitor is *net-positive* on the deployment-realistic metric.

So iteration 4 is an honest **partial win**: it solved the iteration-3 problem (selectivity) and made the
monitor net-positive overall — but it bought that by giving back most of the danger-scene safety the
over-braking version had. The safe-progress lead over OFF comes from the clean-scene selectivity plus
not *hurting* danger-scene progress, **not** from strong danger-scene safety.

## Why it under-brakes — the next problem, isolated

The gate decides "is this agent actively closing?" from the agent's velocity, and it reads that velocity
from the **planner's own forecast** (`future_trajs` first-step displacement). But that forecast is
*optimistic* — the same property iteration 1b/G1 documented (the planner under-sees its own collisions).
So a fast actor driving at the ego is forecast as barely moving, its computed closing speed falls below
the `MIN_CLOSING` gate, and the brake stays silent. The gate filters out exactly the threats it should
catch, because its velocity estimate comes from the optimistic source.

This is the clean attribution iteration 4 buys: the remaining failure is **the velocity source, not the
gating idea.** The two arms bracket it — TTC-old (total closing, no gate) over-brakes everything;
gated (agent-closing from the optimistic forecast) under-brakes real threats. The fix is a velocity
estimate that isn't optimistic.

## Next (iteration 5)

Estimate each agent's velocity from its **actual observed motion** — track `object_ids` across
consecutive `/infer` frames and difference the positions — instead of the planner's forecast. A real
fast-approaching actor then has a true high closing speed (gate fires → brake) while the stationary
object stays at ~0 (gate silent → drive). That should keep iteration 4's selectivity *and* recover
TTC-old's danger safety — the first arm that could be both. Bar to beat stays the deployment metric:
clean-scene progress ≈ OFF, danger collisions ≤ TTC-old, safe-progress > 2.80.

## Reproduce

`iter4_run.sh` (arms OFF / ttcold / gated via `SENTINEL_MIN_CLOSING`) + `server_patch_gated.py` →
`analyze.py`. Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md). Full per-run table:
[`proof/i4_results.txt`](proof/i4_results.txt).
