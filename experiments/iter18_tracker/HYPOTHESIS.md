# Iteration 18 — the tracking layer: pre-registration (offline stage first)

Frozen before any new measurement. Two independent failure analyses converge on one constraint:

- **Iteration 14 (transfer):** the union's selectivity does not survive VAD's geometric
  nearest-neighbor IDs — identity jitter manufactures closing speed, and the monitor over-brakes
  everywhere (safe-progress 2.30 → 0.75).
- **Iteration 17 (routing):** the router's single misrouted crossing traces to velocity dropout
  across identity switches — the overlap projection flickers, and each dropout unlocks a crawl
  into the crossing. All three per-frame geometric repairs were refuted offline
  ([`../iter17_threat_routing/RESULT.md`](../iter17_threat_routing/RESULT.md), addendum).

The mechanism this prescribes is not a new decision rule but a better **track stream**: a
lightweight association-and-filter layer between the planner's raw detections and the monitor.

## The mechanism (pure geometry, no learning)

`sentinel/tracker.py`: gated nearest-neighbor association with a constant-velocity filter —

- **Association:** greedy matching of current detections to live tracks within a gate radius,
  in world frame (ego-motion compensated), robust to the raw IDs (used as a hint, not truth).
- **Filter:** per-track constant-velocity state with exponential smoothing; velocity persists
  through short occlusion/dropout (up to M missed frames) instead of resetting to zero.
- **Output:** the same (position, velocity, id) interface the monitor already consumes — the
  union, release, and router logic are untouched.

## Offline stage (no GPU) — bars frozen now

Replaying the committed per-frame logs through the tracker (VAD decision logs from iteration
14; the iteration-17 routed log), measured by the committed analyzers:

- **O1 — VAD jitter kill:** on the committed VAD-union logs, the rate of *false closing*
  events (frames where raw-ID finite differencing yields closing > 3 m/s against an object
  whose smoothed track shows < 1 m/s) drops by **≥ 80%**.
- **O2 — 0108 flicker repair:** on the committed iteration-17 log, the crossing actor in
  side-0108's misrouted frames holds a continuous track with non-zero velocity through the
  frames where the raw projection flickered — i.e. the overlap predicate, recomputed on
  tracker output, mandates the stop in **every** frame the router crawled unsafely.
- **O3 — no benign regression:** on clean-scene logs, smoothed velocities do not create new
  union firings (recomputed trigger rate within 10% of the raw-ID rate).

**Gate:** all three offline bars must pass before any closed-loop run is pre-registered. If O1
or O2 fails, the tracker hypothesis is refuted at zero GPU cost and published as such.

## Closed-loop stage (pre-registered now, run only after the offline gate)

Two arms, RUNS=6, seed-paired against committed evidence:

- **A1 — VAD selectivity repair:** VAD + union-on-tracker. Bar: clean-scene ego distance
  within 20% of VAD-OFF while stationary and side stay at 0% (the iteration-14 safety wins
  held). This turns the transfer failure into a quantified portability fix.
- **A2 — routing on tracker (UniAD):** the iteration-17 router consuming tracker output. Bars:
  the iteration-17 gate, unchanged (side ≤ 45%, stationary ≤ 25%, NCAP within 0.15 of the
  released union) AND routed − OFF safe-progress CI > 0 — the deployment flip, claimed only if
  safety holds this time.

## Falsifiers, named up front

- The tracker's own failure mode is **wrong association** (identity theft between crossing
  objects), which would *smooth in* a wrong velocity — visible in O3 as new false firings or
  in A1/A2 as new collision modes; any of these publishes the null.
- If O2 passes but A2 still breaches the side bar, the flicker was not the whole story —
  reported with the decision-log diff.
- Latency: the filter must not delay first detection (the union's 2.5 s median lead is a
  budget, not a given); first-fire lead time is reported in both arms.

## Protocol

Offline: `sentinel/tracker.py` with unit tests (pure stdlib, CI-covered) + replay harnesses
committed under this directory with their outputs. Closed-loop: patches extend the committed
iteration-15/17 patterns with the tracker inlined; evidence per campaign standard.
